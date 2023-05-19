"""
    @File: PIILinker.py
    @Author: Archer Simmons, UGTA
    @Contact: Archer.Simmons@tamu.edu 
    
    Mobile: 832 <dash> 433 <dash> 2245
    
    # Compare 50:
        > RUN:  compare50 */*.cpp -d 0_STARTER.cpp -p structure text exact misspellings -n 750
        > DOC:  https://cs50.readthedocs.io/projects/compare50/en/latest/index.html
        > REPO: https://github.com/cs50/compare50
        
    
    # Generate Windows exe:
        * Convert main.py to .exe:
            > pyinstaller --onefile --windowed --icon=C:\path\to\icon.ico code.py
        
        * Create Self-Sign Certificate:
            > $cert = New-SelfSignedCertificate -DNSName "Texas A&M University Departement of Computer Science and Engineering" -CertStoreLocation Cert:\CurrentUser\My -Type CodeSigningCert -Subject “Code Signing”

        * Export SSC:
            1. Press Win+R, type certmgr.msc, and press Enter to open the Certificate Manager.
            2. Navigate to Personal -> Certificates.
            3. Move Code Signing cert to Trusted Root CA folder
            4. Right-click on your certificate, select All Tasks, then Export.
            5. In the wizard, select Yes, export the private key.
            6. Select Personal Information Exchange - PKCS #12 (.PFX), & check:
                i. Include all certificates in the certification path if possible  
                ii. Export all extended properties.
            7. Set a password for the .pfx file.
            8. Select SHA256 Encryption
            9. Choose a location to save the .pfx file, then click Finish.
                
        * Link SSC to exe:
            > Install Windiows SDK; Open PowerShell as Administrator
            > cd "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\"
            > .\signtool sign /f C:\path\to\Cert.pfx /fd SHA256 /p <certificate-password> C:\path\to\program.exe
        
"""

from os import listdir, chdir, getcwd, path, mkdir
from tkinter import filedialog, ttk
from datetime import datetime as dt
import tkinter as tk
import threading
import queue
import time
import sys


## ____________________ Progress-Bar ____________________ ##
class ProgBar:
    
    def __init__(self, tot_: int, title_: str = '') -> None:
        self.total = tot_                           #? Required Progress
        self.progress = 0                           #? Current Progress
        self.Ti = time.time()                       #? Start Time
        self.title = title_                         #? Bar Prefix
        self.BARS = '█▉▊▋▌▍▎▏░'                     #? Bars for Progress Animation
        self.CLOCKS = '🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛' #? Clocks for Progress Animation
        self.clock = 0                              #? Clock Frame
        self.LEN = 24                               #? Fixed-Size of Bar


    def increment(self):
        """ Increments Progress by 1"""
        self.progress += 1
        self.clock = (self.clock+1)%len(self.CLOCKS)


    def __str__(self): 
        """ Generates Printable Bar + Data str for Updates """
        progChrs = int((self.progress/self.total)*self.LEN*(nChrs := len(self.BARS)))
        nBars = progChrs//nChrs
        rem = progChrs%nChrs
        done = ' ✅' if self.progress == self.total else ' ' + self.CLOCKS[self.clock]
        return f"{self.title}" \
                + f"[{self.BARS[0]*nBars}{self.BARS[-rem] if rem else ''}{self.BARS[-1]*(self.LEN-nBars-bool(rem))}]" \
                + f" {((self.progress/self.total)*100):.2f}% ({(time.time()-self.Ti):.1f}s) {done}"



## ____________________ PII-Linker ____________________ ##

#* Student Dataclass
class Student:
        
    def __init__(self, first_=None, last_=None, SID_=None, uin_=None, email_=None, section_=None) -> None:
        self.NAME:    str = first_ + " " + last_ #? Full-Name
        self.SID:     int = int(SID_)            #? Submission ID
        self.CODE:    str = ""                   #? Submitted Code
        self.UIN:     str = uin_                 #? UIN
        self.EMAIL:   str = email_               #? Email
        self.SECTION: str = section_             #? Section
    
    
    def __repr__(self) -> str:
        """ Creates Printable str to Add to Concat Submissions """
        return f"{self.NAME} | UIN{self.UIN} | {self.EMAIL} | {self.SECTION if self.SECTION else 'N/A'} | Submission ID: {self.SID}"



#* Submission ID & PII Handler
class PIILinker:
    
    def __init__(self) -> None:
        self.ROOTDIR: str = getcwd()           #? Directory of Main Execution
        self.ARCHIVE: str = ""                 #? Submissions Directory
        self.SID_CSV: str = ""                 #? CSV Directory
        self.STARTER: str = ""                 #? Holds combined starter code
        self.OUTPUT:  str = getcwd()           #? Output Directory
        self.CHECK: list[str] = []             #? List of .cpp/.h File Names in Starter Directory
        self.DATABASE: dict[int, Student] = {} #? Database of Students (SID Keys)
        
    def __getitem__(self, SID: int) -> Student | None:
        """ Returns student given submissionID """
        return self.DATABASE.get(SID)
 


## ____________________ GUI Classes ____________________ ##

class TextRedirector(object):
    """ Redirects STDIO to Text Box """
    def __init__(self, widget):
        self.widget = widget

    def write(self, str):
        """ Writes STDIO to window """
        self.widget.insert(tk.END, str)
        self.widget.see(tk.END)
    
    def flush(self): pass

class Application(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        #* Global Settings
        self.geometry('880x630')
        self.title("PII-Linker")
        self.configure(bg = 'grey15')
        self.style = ttk.Style()
        self.style.theme_use('alt')
        
        #* Button Style
        self.style.configure(
            "TButton",
            background  = 'grey10',
            foreground  = 'white',
            bordercolor = 'grey16',
            relief      = 'flat'
        )
        self.style.map(
            'TButton', 
            background = [('active', 'grey14')]
        )

        #* Progress Bar Style
        self.style.configure(
            "TProgressbar",
            background = 'SlateBlue1',
            relief     = 'flat'
        )

        #* Label Style
        self.style.configure(
            "TLabel",
            background  = 'grey16',
            foreground  = 'white',
            relief      = 'flat',
            width       = 620,
            borderwidth = 2
        )
        
        #* Frame Style
        self.style.configure(
            "TFrame",
            background = 'grey16',
            relief     = 'flat'
        )

        #* Labels Vars
        self.csvPath         = tk.StringVar()
        self.submissionPath  = tk.StringVar()
        self.starterCodePath = tk.StringVar()
        self.outputPath      = tk.StringVar()
        self.outputPath.set(getcwd())
        
        self.create_widgets()
        
        #* PII-Linker 
        self.mgr = PIILinker()
        self.numSubmissions = 0
        
        #* ProgBar
        self.procQueue = queue.Queue()
        self.running = False
        self.FUNCS = {
            "setup":    ["Initializing... ", self.setup   ],
            "build":    ["Building... ",     self.build   ],
            "extract":  ["Extracting... ",   self.extract ],
            "generate": ["Generating... ",   self.generate]
        }
        
        #* STDIO Redirection
        sys.stderr = TextRedirector(self.output)


    def create_widgets(self):
        #* CSV Selection Field
        row = ttk.Frame(self)
        self.btn_student_data = ttk.Button(row, text = "Select Submission IDs CSV", command = self.loadCSVDir)
        self.btn_student_data.pack(side = 'left')
        ttk.Label(row, textvariable = self.csvPath).pack(side = 'left')
        row.pack(fill = 'x', padx = 10, pady = 5)

        #* Submission Dir Selection Field
        row = ttk.Frame(self)
        self.btn_submissions_dir = ttk.Button(row, text = "Select Submissions Directory", command = self.loadSubmissionsDir)
        self.btn_submissions_dir.pack(side='left')
        ttk.Label(row, textvariable=self.submissionPath).pack(side='left')
        row.pack(fill='x', padx=10, pady=5)

        #* Starter Code Dir Selection Field
        row = ttk.Frame(self)
        self.btn_starter_code_dir = ttk.Button(row, text = "Select Starter-Code Directory", command = self.loadStarterCodeDir)
        self.btn_starter_code_dir.pack(side = 'left')
        ttk.Label(row, textvariable = self.starterCodePath).pack(side = 'left')
        row.pack(fill = 'x', padx = 10, pady = 5)
        
        #* Output File Dir Selection Field
        row = ttk.Frame(self)
        self.btn_output_dir = ttk.Button(row, text = "Select Output Directory", command = self.loadOutputDir)
        self.btn_output_dir.pack(side = 'left')
        ttk.Label(row, textvariable = self.outputPath).pack(side = 'left')
        row.pack(fill = 'x', padx = 10, pady = 5)

        #* Start Program Button
        self.btn_run = ttk.Button(self, text = "LINK PII", command = self.run_program)
        self.btn_run.pack(pady = 10)
  
        #* Text Box
        self.output = tk.Text(self, 
            wrap   = 'word', 
            bg     = 'grey16', 
            fg     = 'white', 
            relief = 'flat',
            state  = 'normal'
        )
        self.output.pack(
            padx   = 10, 
            pady   = 1, 
            expand = True, 
            fill   = 'both'
        )
        
        #* Unicode Progress Bar
        self.active_progress_area = tk.Text(self, 
            wrap   = 'word', 
            bg     = 'grey16', 
            fg     = 'white', 
            relief = 'flat',
            state  = 'normal',
            height = 1
        )
        self.active_progress_area.pack(padx = 10, pady = 1, fill = 'x')

        #* Main Progress Bar
        self.mainProgressBar = ttk.Progressbar(self, mode = 'determinate', length = 500)
        self.mainProgressBar.pack(pady = 10)
        
        
    #> -------------------- Directory/File Selection -------------------- <# 
    def loadCSVDir(self):
        """ Asks user to select local CSV file """
        if filename := filedialog.askopenfilename(filetypes = (("CSV files","*.csv"),("all files","*.*"))): 
            self.csvPath.set(f"  {filename}")
            self.mgr.SID_CSV = filename
            
            
    def loadSubmissionsDir(self):
        """ Asks user to select local submissions directory """
        if directory := filedialog.askdirectory(): 
            self.submissionPath.set(f"  {directory}")
            self.mgr.ARCHIVE = directory
            
            
    def loadStarterCodeDir(self):
        """ Asks user to select local starter code directory """
        if directory := filedialog.askdirectory():
            self.starterCodePath.set(f"  {directory}")
            self.mgr.STARTER = directory
            
            
    def loadOutputDir(self):
        """ Asks user to select local starter code directory """
        if directory := filedialog.askdirectory():
            self.outputPath.set(f"  {directory}")
            self.mgr.OUTPUT = directory
            
            
    #> -------------------- Progress Bar Threads -------------------- <#            
    def _call__(self, func: str):
        """ Handles Step-Selection & Threads"""
        print(func)
        PB = ProgBar(
            (1 if func in ["setup", "build"] else self.numSubmissions), 
            (F := self.FUNCS.get(func))[0]
        )
        threading.Thread(target = F[1], args = (PB,)).start()
 
 
    def updateProg(self, PB):
        """ Updates Progress Bar in active tk.Text widget """
        self.active_progress_area.delete('1.0', tk.END)
        self.active_progress_area.insert('1.0', str(PB))


    def complete(self, PB):
        """ Moves Completed Progress Bar to output (tk.Text) """
        self.output.insert('end', str(PB) + '\n')
        self.active_progress_area.delete('1.0', tk.END)


    def _runNext__(self):
        """ Loops to Consume & Execute Queue Requests """
        if not self.procQueue.empty():
            next_op = self.procQueue.get()
            next_op() 


    #> -------------------- PIILinker Main -------------------- <#
    def setup(self, PB: ProgBar) -> None:
        """ Grabs Starter-Code """
        self.mgr.CHECK = [
            file for file in listdir(self.mgr.STARTER) 
                if file.endswith(".cpp") or file.endswith(".h")
        ]
        
        if not len(self.mgr.CHECK): 
            print("[ERROR] Starter-Code Directory Contains 0 .h/.cpp File(s)", file=sys.stderr)
            self.running = False
            return
        
        self.numSubmissions = len(listdir(self.mgr.ARCHIVE))
        self.mainProgressBar["value"] = 0
        self.mainProgressBar["maximum"] = self.numSubmissions * 2 + 2
        chdir(self.mgr.STARTER)
        NL2 = "\n\n"
        
        for i, sFile in enumerate(self.mgr.CHECK, 0):
            with open(sFile, mode='r', encoding='utf-8', errors='ignore') as rFile:
                self.mgr.STARTER += f"{(NL2 if i else '')}/* ----- {sFile} | STARTER CODE ----- */\n\n{rFile.read()}"    
                
        chdir(self.mgr.ROOTDIR)
        self.mainProgressBar["value"] += 1
        PB.increment()
        app.after(0, self.updateProg, PB)
        app.after(0, self.complete, PB)
        self.procQueue.put((lambda: self._call__("build")))
         
         
    def build(self, PB: ProgBar) -> None:
        """ Builds student database using exported submission CSV """
        with open(self.mgr.SID_CSV, mode='r', encoding='utf-8', errors='ignore') as csvFile:
            csvFile.readline()
            self.mgr.DATABASE = {
                int(sid) : Student(first, last, sid, uin, email, section) 
                    for sid, first, last, uin, email, section in [
                        [line.split(",")[8]] + line.split(",")[:5] 
                            for line in csvFile.read().split('\n') 
                                if "Graded" in line
                    ]
            } 
            
        if not len(self.mgr.DATABASE) or all(student == None for student in self.mgr.DATABASE.values()): 
            print("[ERROR] Database Build Failed\n\tCheck all Files for Validity", file=sys.stderr)
            self.running = False
            return
        
        self.mainProgressBar["value"] += 1
        PB.increment()
        app.after(0, self.updateProg, PB)
        app.after(0, self.complete, PB)
        self.procQueue.put((lambda: self._call__("extract")))

           
    def extract(self, PB: ProgBar) -> None:
        """ Extracts Submissions for PII-linking """
        chdir(self.mgr.ARCHIVE) 
   
        for folderName in listdir(): 
            chdir(path.join(self.mgr.ARCHIVE, folderName)) 
            FILES_ = listdir()
            for file in self.mgr.CHECK:       
                if file not in FILES_: 
                    print(f"[WARNING] Missing {file} for:\n\t{(self.mgr[int(subID)])}", file=sys.stderr) 
                    continue
                
                with open(file, mode='r', encoding='utf-8', errors='ignore') as fileCode:
                    (stu := self.mgr[int(subID := folderName.strip().split('_')[-1])]).CODE \
                        += f"/* ----- {file} | {repr(stu)} ----- */\n\n{fileCode.read()}"
                
            self.mainProgressBar["value"] += 1
            PB.increment()
            app.after(0, self.updateProg, PB)
            chdir(self.mgr.ARCHIVE) 
            
        chdir(self.mgr.ROOTDIR) 
        app.after(0, self.complete, PB)
        self.procQueue.put((lambda: self._call__("generate")))
        
    
    def generate(self, PB: ProgBar) -> None:
        """ Generates Folder PII-linked Code """
        fileID = f"{(T := dt.now()).month}-{T.year}_{T.second}"
        mkdir(EXPDIR := path.join(self.mgr.OUTPUT, f"PIILinked_{fileID}")) 
        chdir(EXPDIR) 

        with open(file="0_STARTER.cpp", mode='w', encoding='utf-8', errors="ignore") as wFile: 
            wFile.write(self.mgr.STARTER)
                    
        for subID, student in self.mgr.DATABASE.items():
            if not path.exists(STUDIR := path.join(EXPDIR, '_'.join(student.NAME.split()))):
                mkdir(STUDIR)     
            chdir(STUDIR) 
    
            with open(file=f"{'_'.join(student.NAME.split())}_{subID}.cpp", mode='w', encoding='utf-8', errors="ignore") as wFile: 
                wFile.write(student.CODE)
                        
            chdir(EXPDIR) 
            self.mainProgressBar["value"] += 1
            PB.increment()
            app.after(5, self.updateProg, PB)
            
        chdir(self.mgr.ROOTDIR) 
        app.after(0, self.complete, PB)
        self.running = False
        

    #> -------------------- Run PII Linker -------------------- <#
    def start_runner(self):
        """ Start Runner Loop. """
        self._runNext__()
        if self.running: self.after(50, self.start_runner)    
        else: self.active_progress_area.delete('1.0', tk.END)
            
    
    def run_program(self):
        """ Starts Main Program """
        if not all([self.csvPath.get(), self.submissionPath.get(), self.starterCodePath.get()]):
            self.output.insert(tk.END, '[ERROR] Missing Files/Directories Selections \n')
            return    
        
        if not self.running:
            self.running = True
            self._call__("setup")
            self.start_runner()



if __name__ == "__main__":
    app = Application()
    app.mainloop()


