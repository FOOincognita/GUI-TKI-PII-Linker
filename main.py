"""
    @File: PIILinker.py
    @Author: Archer Simmons, UGTA
    @Contact: Archer.Simmons@tamu.edu 
    
        Personal:
            832 <dash> 433 <dash> 2245
            Archer1799@gmail.com
    
    * Compare 50:
        > RUN:  compare50 */*.cpp -d 0_STARTER.cpp -p structure text exact misspellings -n 750
        > DOC:  https://cs50.readthedocs.io/projects/compare50/en/latest/index.html
        > REPO: https://github.com/cs50/compare50
"""

from os import listdir, chdir, getcwd, path, mkdir
from tkinter import filedialog, ttk
from datetime import datetime as dt
import tkinter as tk
import threading
import queue
import time


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
ERROR        = lambda x, y: print(f"[ERROR {x}]: {y}")
WARNING      = lambda x, y: print(f"[WARNING {x}]: {y}")
UNKNOWNERROR = lambda x, y: print(f"[ERROR {x}] UNHANDLED EXCEPTION:\n\t{y}")

class EmptyDatabase(Exception): pass
class EmptyStarterDirectory(Exception): pass


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
class Application(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        #* Global Settings
        self.geometry('640x650')
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
        
        #* PII-Linker 
        self.mgr = PIILinker()
        self.numSubmissions = 0
        
        #* ProgBar
        self.procQueue = queue.Queue()
        self.running = False
        self.FUNCS = {
            "setup":    ["Initializing...", self.setup],
            "build":    ["Building...",     self.build],
            "extract":  ["Extracting...",   self.extract],
            "generate": ["Generating...",   self.generate]
        }
        
        self.create_widgets()


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
        print("Runner called")
        if not self.procQueue.empty():
            print("procQ isn't empty")
            next_op = self.procQueue.get()
            next_op() 


    #> -------------------- PIILinker Main -------------------- <#
    def setup(self, PB: ProgBar) -> None:
        """ Grabs Starter-Code """
        self.mgr.CHECK = [
            file for file in listdir(self.mgr.STARTER) 
                if file.endswith(".cpp") or file.endswith(".h")
        ]
        
        if not len(self.mgr.CHECK): raise EmptyStarterDirectory
        
        self.numSubmissions = len(listdir(self.mgr.ARCHIVE))
        self.mainProgressBar["value"] = 0
        self.mainProgressBar["maximum"] = self.numSubmissions * 2 + 2
        chdir(self.mgr.STARTER)
        NL2 = "\n\n"
        
        for i, sFile in enumerate(self.mgr.CHECK, 0):
            with open(sFile, 'r') as rFile:
                self.mgr.STARTER += f"{(NL2 if i else '')}/* ----- {sFile} | STARTER CODE ----- */\n\n{rFile.read()}"    
                
        chdir(self.mgr.ROOTDIR)
        self.mainProgressBar["value"] += 1
        PB.increment()
        app.after(0, self.updateProg, PB)
        app.after(0, self.complete, PB)
        self.procQueue.put((lambda: self._call__("build")))
         
         
    def build(self, PB: ProgBar) -> None:
        """ Builds student database using exported submission CSV """
        with open(self.mgr.SID_CSV, 'r') as csvFile:
            csvFile.readline()
            self.mgr.DATABASE = {
                int(sid) : Student(first, last, sid, uin, email, section) 
                    for sid, first, last, uin, email, section in [
                        [line.split(",")[8]] + line.split(",")[:5] 
                            for line in csvFile.read().split('\n') 
                                if "Graded" in line
                    ]
            } 
        #!!!! [TODO]: ADD EXCEPTION HANDLING
        if not len(self.mgr.DATABASE) or all(student == None for student in self.mgr.DATABASE.values()): 
            raise EmptyDatabase("Build Failed. Check all Files for Validity")
        
        self.mainProgressBar["value"] += 1
        PB.increment()
        app.after(0, self.updateProg, PB)
        app.after(0, self.complete, PB)
        self.procQueue.put((lambda: self._call__("extract")))

           
    def extract(self, PB: ProgBar) -> None:
        """ Extracts code from submissions to later write to PII-linked files """
        chdir(self.mgr.ARCHIVE) 
   
        for folderName in listdir(): 
            chdir(path.join(self.mgr.ARCHIVE, folderName)) 
            for file in self.mgr.CHECK:
                try:
                    with open(file, 'r') as fileCode:
                        (stu := self.mgr[int(subID := folderName.strip().split('_')[-1])]).CODE \
                            += f"/* ----- {file} | {repr(stu)} ----- */\n\n{fileCode.read()}"
                            
                #!!!! [TODO]: ADD EXCEPTION HANDLING
                except FileNotFoundError: WARNING("E1", f"Missing {file} for:\n\t{self[int(subID)]}")            
                except KeyError: WARNING("E2", f"Missing Key for:\n\t{self[int(subID)]}")
                
            self.mainProgressBar["value"] += 1
            PB.increment()
            app.after(0, self.updateProg, PB)
            chdir(self.mgr.ARCHIVE) 
            
        chdir(self.mgr.ROOTDIR) 
        app.after(0, self.complete, PB)
        self.procQueue.put((lambda: self._call__("generate")))
        
    
    def generate(self, PB: ProgBar) -> None:
        """ Generates folder of single files which contain PII-linked code """
        fileID = f"{(T := dt.now()).month}-{T.year}_{T.second}"
        mkdir(EXPDIR := path.join(self.mgr.OUTPUT, f"PIILinked_{fileID}")) 
        chdir(EXPDIR) 

        with open("0_STARTER.cpp", 'w') as wFile: wFile.write(self.mgr.STARTER)
                    
        for subID, student in self.mgr.DATABASE.items():
            mkdir(STUDIR := path.join(EXPDIR, '_'.join(student.NAME.split())))     
            chdir(STUDIR) 
    
            with open('_'.join(student.NAME.split()) + '_' + str(subID) + ".cpp", 'w') as wFile: 
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
        """ Start runner loop. """
        self._runNext__()
        if self.running: 
            self.after(50, self.start_runner)    
            
    
    def run_program(self):
        """ Starts Main Program """
        if not all([self.csvPath.get(), self.submissionPath.get(), self.starterCodePath.get()]):
            self.output.insert(tk.END, '[ERROR] Please select all files & directories before running\n')
            return    
        
        if not self.running:
            self.running = True
            self._call__("setup")
            self.start_runner()
            
        self.active_progress_area.delete('1.0', tk.END)


if __name__ == "__main__":
    app = Application()
    app.mainloop()
