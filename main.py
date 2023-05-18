"""
    @File: PIILinker.py
    @Author: Archer Simmons, UGTA
    @Contact: Archer.Simmons@tamu.edu 
    
        Personal:
            832 <dash> 433 <dash> 2245
            Archer1799@gmail.com
    
    This program renames submission folders 
    from GradeScope such that they contain 
    names in preparation for Compare50 scan. 
    
    * Compare 50:
        > RUN:  compare50 */*.cpp -d 0_STARTER.cpp -p structure text exact misspellings -n 750
        > DOC:  https://cs50.readthedocs.io/projects/compare50/en/latest/index.html
        > REPO: https://github.com/cs50/compare50
    
    
    #! TODO (maybe): ADD DEPENDANCY MANAGER
    
"""

from os import listdir, chdir, getcwd, path, mkdir, system, name as OS
from tkinter import filedialog, ttk
from datetime import datetime as dt
import tkinter as tk
import threading
import time
import sys

## ____________________ Progress-Bar Class ____________________ ##
class ProgBar:
    instance = 0
    def __init__(self, total, title=''):
        self.ID = ProgBar.instance
        ProgBar.instance += 1
        self.total = total
        self.progress = 0
        self.start_time = time.time()
        self.title = title
        self.chars = '█▉▊▋▌▍▎▏░'
        self.animation_chars = '🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛'
        self.animation_index = 0

    def increment(self):
        self.progress += 1
        self.animation_index = (self.animation_index + 1) % len(self.animation_chars)

    def __str__(self):
        total_chars = 24 
        completed_chars = int((self.progress / self.total) * total_chars * len(self.chars))
        full_blocks = completed_chars // len(self.chars)
        remainder = completed_chars % len(self.chars)
        percentage = (self.progress / self.total) * 100
        elapsed_time = time.time() - self.start_time
        finished_indicator = ' ✅' if self.progress == self.total else ' ' + self.animation_chars[self.animation_index]
        return '{} [{}{}{}] {:.2f}% ({:.1f}s) {}'.format(
            self.title,
            self.chars[0] * full_blocks, 
            self.chars[-remainder] if remainder else '',
            self.chars[-1] * (total_chars - full_blocks - bool(remainder)),
            percentage,
            elapsed_time,
            finished_indicator
        )



## ____________________ PII-Linker Classes ____________________ ##

ERROR        = lambda x, y: print(f"[ERROR {x}]: {y}")
WARNING      = lambda x, y: print(f"[WARNING {x}]: {y}")
UNKNOWNERROR = lambda x, y: print(f"[ERROR {x}] UNHANDLED EXCEPTION:\n\t{y}")

class EmptyDatabase(Exception): pass
class EmptyStarterDirectory(Exception): pass


#* Student Dataclass
class Student():
        
    def __init__(self, first_=None, last_=None, SID_=None, uin_=None, email_=None, section_=None) -> None:
        self.NAME:    str = first_ + " " + last_
        self.SID:     int = int(SID_)
        self.CODE:    str = ""
        self.UIN:     str = uin_
        self.EMAIL:   str = email_
        self.SECTION: str = section_
    
    
    def __repr__(self) -> str:
        return f"{self.NAME} | UIN{self.UIN} | {self.EMAIL} | {self.SECTION if self.SECTION else 'N/A'} | Submission ID: {self.SID}"



#* Submission ID & PII Handler
class PIILinker():
    
    def __init__(self) -> None:
        self.ROOTDIR: str = getcwd()
        self.ARCHIVE: str = "NONE"
        self.SID_CSV: str = "NONE"
        self.STARTER: str = "" #? Holds combined starter code
        self.OUTPUT:  str = getcwd()
        
        self.CHECK: list[str] = [] #? Contains Filenames of files to extract from student code
        
        self.DATABASE: dict[int, Student] = {}
        
        
    def __getitem__(self, SID: int) -> Student | None:
        """ Returns student given submissionID """
        return self.DATABASE.get(SID)


    @staticmethod
    def clearTerminal() -> None:
        """ [UNUSED]: Erases All Terminal Text """
        system('cls' if OS == 'nt' else 'clear')
 


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

        #* Selected Paths
        self.csvPath         = tk.StringVar()
        self.submissionPath  = tk.StringVar()
        self.starterCodePath = tk.StringVar()
        self.outputPath      = tk.StringVar()
        self.outputPath.set(getcwd())

        self.create_widgets()
        
        #* STDIO Redirection
        #!sys.stdout = TextRedirector(self.output)
        #!sys.stderr = TextRedirector(self.output)
        
        #* PII-Linker 
        self.mgr = PIILinker()
        
        #* ProgBar
        self.progBars: list[ProgBar] = []
        self.stop = threading.Event()
        

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
        self.output = tk.Text(
            self, 
            wrap                = 'word', 
            bg                  = 'grey16', 
            fg                  = 'white', 
            highlightbackground = 'grey18',
            highlightthickness  = 1,
            relief              = 'flat',
            state               = 'normal'
        )
        self.output.pack(
            padx = 10, 
            pady = 1, 
            expand = True, 
            fill = 'both'
        )
        
        #* Unicode Progress Bar
        self.active_progress_area = tk.Text(
            self, 
            wrap                = 'word', 
            bg                  = 'grey16', 
            fg                  = 'white', 
            highlightbackground = 'grey18',
            highlightthickness  = 1,
            relief              = 'flat', 
            height              = 1,
            state               = 'normal'
        )
        self.active_progress_area.pack(
            padx = 10, 
            pady = 1, 
            expand = True, 
            fill='x'
        )

        #* Progress Bar
        self.mainProgressBar = ttk.Progressbar(self, mode = 'determinate', length = 500)
        self.mainProgressBar.pack(pady = 10)
        


    #> -------------------- Load Directories -------------------- <# 
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
            
            

    #> -------------------- Progress Bar -------------------- <#            
    def updateProg(self):
        while not self.stop:
            self.active_progress_area.delete('1.0', tk.END)
            self.active_progress_area.insert(tk.END, str(self.progBars[-1]))
            
        self.progBars[-1].progress = self.progBars[-1].total
        print(self.progBars[-1])


    #> -------------------- PIILinker -------------------- <#
    def setup(self) -> None:
        """ Grabs starter-code data """
        self.stop.clear()
        self.mgr.CHECK = [file for file in listdir(self.mgr.STARTER) if file.endswith(".cpp") or file.endswith(".h")]
        
        if not len(self.mgr.CHECK): 
            raise EmptyStarterDirectory
        
        
        #* Init main progress bar
        self.numSubmissions = len(listdir(self.mgr.ARCHIVE))
        self.mainProgressBar["value"] = 0
        self.mainProgressBar["maximum"] = self.operationsRemaining * 2 + 2
        
        self.progBars += [ProgBar(1, "Initialzing")]
        self.threadS = threading.Thread(daemon = True, target = self.updateProg)
        self.threadS.start()

        chdir(self.mgr.STARTER) #> Change dir to starter-code folder
        NL2 = "\n\n"
        #* Concatenate combined starter code file for FileWrangler::generate()
        for i, sFile in enumerate(self.mgr.CHECK, 0):
            with open(sFile, 'r') as rFile:
                self.mgr.STARTER += f"{(NL2 if i else '')}/* ----- {sFile} | STARTER CODE ----- */\n\n{rFile.read()}"    
        chdir(self.mgr.ROOTDIR) #> Restoring root directory
        
        self.progBars[0].increment()
        self.stop.set()
        self.mainProgressBar["value"] += 1
         
    
    def build(self) -> None:
        """ Builds student database using exported submission CSV """
        self.stop.clear()
        self.progBars += [ProgBar(1, "Building")]
        self.threadB = threading.Thread(daemon = True, target = self.updateProg)
        self.threadB.start()
        
        #* Building Student Database
        with open(self.mgr.SID_CSV, 'r') as csvFile:
            csvFile.readline()
            self.mgr.DATABASE = {
                int(sid) : Student(first, last, sid, uin, email, section) for sid, first, last, uin, email, section
                    in [[line.split(",")[8]] + line.split(",")[:5] for line in csvFile.read().split('\n') if "Graded" in line]
            } 

        self.progBars[1].increment()
        self.mainProgressBar["value"] += 1
        
        
        if not len(self.mgr.DATABASE) or all(student == None for student in self.mgr.DATABASE.values()):
            raise EmptyDatabase("Build Failed. Check all Files for Validity")
            
        print("Database Sucessfully Built...")
        self.stop.set()
           
    def extract(self) -> None:
        """ Extracts code from submissions to later write to PII-linked files """
        self.stop.clear()
        self.progBars += [ProgBar(self.numSubmissions, "Extracting")]
        self.threadE = threading.Thread(daemon = True, target = self.updateProg)
        self.threadE.start()
        
        chdir(self.mgr.ARCHIVE) #> Open archive directory
            
        #* Iterate over each submission
        for folderName in listdir(): 
            chdir(path.join(self.mgr.ARCHIVE, folderName)) #> Open individual folder

            #* Iterate over files listed in CHECK
            for file in self.mgr.CHECK:
                try:
                    with open(file, 'r') as fileCode:
                        #* Store unified code from submitted code file(s) 
                        (stu := self.mgr[int(subID := folderName.strip().split('_')[-1])]).CODE \
                            += f"/* ----- {file} | {repr(stu)} ----- */\n\n{fileCode.read()}"
                
                except FileNotFoundError: WARNING("E1", f"Missing {file} for:\n\t{self[int(subID)]}")            
                except KeyError: WARNING("E2", f"Missing Key for:\n\t{self[int(subID)]}")
                
            self.progBars[2].increment()
            self.mainProgressBar["value"] += 1
        
            chdir(self.mgr.ARCHIVE) #> Restore Archive Directory
            
        self.stop.set()
        chdir(self.mgr.ROOTDIR) #> Restore Root Directory
        print("Code Extracted & Linked...")
        
        
    def generate(self) -> None:
        """ Generates folder of single files which contain PII-linked code """
        self.stop.clear()
        self.progBars += [ProgBar(self.numSubmissions, "Generating")]
        self.threadG = threading.Thread(daemon = True, target = self.updateProg)
        self.threadG.start()
            
        #* Create & open unique folder using date & time; created in ROOTDIR
        while True:
            try:
                #* Try to create folder; if exists, create folder with suffix "(n)"
                T, n  = dt.now(), 0
                fileID = f"{T.month}-{T.year}" + (f"({n})" if n else "")
                mkdir(EXPDIR := path.join(self.mgr.OUTPUT, f"PIILinked_{fileID}")) 
    
            except FileExistsError: n += 1
            else: break
            
        chdir(EXPDIR) #> Open created folder

        #* Write all files; starter & Student
        #? Write combined starter to directory
        with open("0_STARTER.cpp", 'w') as wFile: 
            wFile.write(self.mgr.STARTER)
                    
        #* Create Unique folder for each student
        for subID, student in self.mgr.DATABASE.items():
            n = 0
            while True:
                try: mkdir(STUDIR := path.join(EXPDIR, '_'.join(student.NAME.split()) + (f"({n})" if n else "")))
                except FileExistsError: n += 1
                else: break
                    
            chdir(STUDIR) #> Open Individual student directory to write
                    
            #* Write student code to single file
            with open('_'.join(student.NAME.split()) + '_' + str(subID) + ".cpp", 'w') as wFile: 
                wFile.write(student.CODE)
                        
            chdir(EXPDIR) #> Restore Export Directory
                
            self.progBars[3].increment()
            self.mainProgressBar["value"] += 1
            
        self.stop.set()
        chdir(self.mgr.ROOTDIR) #> Restore root directory
        print("Folder Generation Complete...")


        
    #> -------------------- Run PII Linker -------------------- <#
    def run_program(self):
        """ Starts main program """
        print("Running")
        if not all([self.csvPath.get(), self.submissionPath.get(), self.starterCodePath.get()]):
            print('[ERROR] Please select all files & directories before running\n')
            return
            
        try: self.setup()
        except EmptyStarterDirectory: ERROR("S1", "Selected Starter Code Directory Contains 0 .h/.cpp Files")
        except Exception as e:        UNKNOWNERROR("S2", e); return
        self.threadS.join()
        
        try: self.build()    #> Build Student Database
        except EmptyDatabase as e: ERROR("B1", e)
        except Exception as e:     UNKNOWNERROR("B2", e); return
        self.threadB.join()
        
        try: self.extract()  #> Extract Student Code
        except Exception as e: UNKNOWNERROR("E", e); return
        self.threadE.join()
        
        try: self.generate() #> Generate PII-Linked Folder of Student Code
        except Exception as e: UNKNOWNERROR("G", e); return
        self.threadG.join()
        
        print(f"\nSummary:\n\t{len(listdir(self.mgr.ARCHIVE))} PII-Linked Files Generated")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
