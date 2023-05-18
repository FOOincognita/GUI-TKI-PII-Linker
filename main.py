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
from contextlib import redirect_stdout
from tkinter import filedialog, ttk
from datetime import datetime as dt
import tkinter as tk
import sys
import io

import tkinter.scrolledtext as st
import threading
import time

## ____________________ Progress-Bar Class ____________________ ##
class ProgressBar:
    def __init__(self, total, title=''):
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

UnknownErr = lambda x, y: print(f"[ERROR {x}]: Unknown Exception:\n\t{y}")

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
        
        self.CHECK: list[str] = [] #? Contains Filenames of files to extract from student code
        
        self.DATABASE: dict[int, Student] = {}
        
        
    def __getitem__(self, SID: int) -> Student | None:
        """ Returns student given submissionID """
        return self.DATABASE.get(SID)
    
    
    def setup(self) -> None:
        """ Grabs starter-code data """
        try: 
            chdir(self.STARTER) #> Change dir to starter-code folder
            NL2 = "\n\n"
            #* Concatenate combined starter code file for FileWrangler::generate()
            for i, sFile in enumerate(self.CHECK, 0):
                with open(sFile, 'r') as rFile:
                    self.STARTER += f"{(NL2 if i else '')}/* ----- {sFile} | STARTER CODE ----- */\n\n{rFile.read()}"
                            
            chdir(self.ROOTDIR) #> Restoring root directory
            
        except Exception as e: UnknownErr("S1", e)
        
    
    def build(self) -> None:
        """ Builds student database using exported submission CSV """
        print("Building Student Database...")
        
        #* Building Student Database
        try:
            with open(self.SID_CSV, 'r') as csvFile:
                csvFile.readline() #? Omit Header
                self.DATABASE = {
                    int(sid) : Student(first, last, sid, uin, email, section) for sid, first, last, uin, email, section
                        in [[line.split(",")[8]] + line.split(",")[:5] for line in csvFile.read().split('\n') if "Graded" in line]
                } 
                    
        except FileNotFoundError: print(f"[ERROR B1]: {self.SID_CSV} is not in root directory\n\t{self.ROOTDIR}")
        except KeyboardInterrupt: exit()
        except Exception as e: print(f"[ERROR B2]: Unknown Exception:\n\t{e}")
            
        #! Check if Database is empty
        if not len(self.DATABASE) or all(student == None for student in self.DATABASE.values()):
            print("[ERROR B3]: Database Empty\nEXITING...")
            exit()
            
        print("Database Sucessfully Built...")
       
           
    def extract(self) -> None:
        """ Extracts code from submissions to later write to PII-linked files """
        print("Extracting Student Code...")
        chdir(self.ARCHIVE) #> Open archive directory
            
        #* Iterate over each submission
        for folderName in listdir(): 
            chdir(path.join(self.ARCHIVE, folderName)) #> Open individual folder

            #* Iterate over files listed in CHECK
            for file in self.CHECK:
                try:
                    with open(file, 'r') as fileCode:
                        #* Store unified code from submitted code file(s) 
                        (stu := self[int(subID := folderName.strip().split('_')[-1])]).CODE \
                            += f"/* ----- {file} | {repr(stu)} ----- */\n\n{fileCode.read()}"
                            
                except FileNotFoundError: print(f"[WARNING E1]: Missing {file} for:\n\t{self[int(subID)]}")
                except KeyError: print(f"[ERROR E1]: Missing Key for:\n\t{self[int(subID)]}")
                except KeyboardInterrupt: exit()
                except Exception as e: print(f"[ERROR E2]: Unknown Exception:\n\t{e}")
                
            chdir(self.ARCHIVE) #> Restore Archive Directory
        chdir(self.ROOTDIR) #> Restore Root Directory
        print("Code Extracted & Linked...")
        
        
    def generate(self) -> None:
        """ Generates folder of single files which contain PII-linked code """
        print("Generating PII-Linked Folder...")
            
        #* Create & open unique folder using date & time; created in ROOTDIR
        while True:
            try:
                #* Try to create folder; if exists, create folder with suffix "(n)"
                T, n  = dt.now(), 0
                fileID = f"{T.month}-{T.year}" + (f"({n})" if n else "")
                mkdir(EXPDIR := path.join(self.ROOTDIR, f"PIILinked_{fileID}")) 
                    
            except KeyboardInterrupt: exit()
            except FileExistsError: 
                n += 1
                continue
            except Exception as e: 
                print(f"[ERROR G1]: Unknown Exception 1:\n\t{e}\nEXITING...")
                exit()
            else:
                break
            
        chdir(EXPDIR) #> Open created folder

        #* Write all files; starter & Student
        try:
            with open("0_STARTER.cpp", 'w') as wFile: #? Write combined starter to directory
                wFile.write(self.STARTER)
                    
            for subID, student in self.DATABASE.items():
                #* Create Unique folder for each student
                n = 0
                while True:
                    try: mkdir(STUDIR := path.join(getcwd(), '_'.join(student.NAME.split()) + (f"({n})" if n else "")))
                    except KeyboardInterrupt: exit()
                    except FileExistsError: n += 1
                    else: break
                    
                chdir(STUDIR) #> Open Individual student directory to write
                    
                #* Write student code to single file
                with open('_'.join(student.NAME.split()) + '_' + str(subID) + ".cpp", 'w') as wFile: 
                    wFile.write(student.CODE)
                        
                chdir(EXPDIR) #> Restore Export Directory
                        
        except KeyboardInterrupt: exit()
        except Exception as e: print(f"[ERROR G2]: Unknown Exception 2:\n\t{e}\nFor: {student.NAME}")
            
        chdir(self.ROOTDIR) #> Restore root directory
        print("Folder Generation Complete...")


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
        self.geometry('640x800')
        self.title("PII-Linker")
        self.configure(bg = 'grey15')
        self.style = ttk.Style()
        self.style.theme_use('alt')
        
        #* Button Style
        self.style.configure("TButton",
                             background  = 'grey10',
                             foreground  = 'white',
                             bordercolor = 'grey16',
                             relief      = 'flat'
                            )
        
        self.style.map('TButton', background=[('active', 'grey14')])

        #* Progress Bar Style
        self.style.configure("TProgressbar",
                             background = 'SlateBlue1',
                             relief     = 'flat'
                            )

        #* Label Style
        self.style.configure("TLabel",
                             background  = 'grey16',
                             foreground  = 'white',
                             relief      = 'flat',
                             width       = 620,
                             borderwidth = 2
                            )
        
        #* Frame Style
        self.style.configure("TFrame",
                             background = 'grey16',
                             relief     = 'flat'
                            )

        #* Selected Paths
        self.csvPath         = tk.StringVar()
        self.submissionPath  = tk.StringVar()
        self.starterCodePath = tk.StringVar()

        self.create_widgets()
        
        #* STDIO Redirection
        sys.stdout = TextRedirector(self.output)
        sys.stderr = TextRedirector(self.output)
        
        #* PII-Linker 
        self.mgr = PIILinker()

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

        #* Start Program Button
        self.btn_run = ttk.Button(self, text = "LINK PII", command = self.run_program)
        self.btn_run.pack(pady = 10)
  
        #* Text Box
        self.output = tk.Text(self, 
                              wrap                = 'word', 
                              bg                  = 'grey16', 
                              fg                  = 'white', 
                              highlightbackground = 'grey18',
                              highlightthickness  = 1,
                              relief              = 'flat', 
                              state               = 'disabled'
                             )
        self.output.pack(padx = 10, pady = 10, expand = True, fill = 'both')

        #* Progress Bar
        self.progress_bar = ttk.Progressbar(self, mode = 'determinate', length = 500)
        self.progress_bar.pack(pady = 10)

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

    def run_program(self):
        """ Starts main program """
        #!if not all([self.student_data.get(), self.submission_dir.get(), self.starter_code_dir.get()]):
          #!  print('Please select all files and directories before running the program.\n')
            #!return
        
        #self.output.configure(state = 'normal')
        print('Program is running...\n')
        #self.progress_bar["value"] = 0
        #self.progress_bar["maximum"] = 100
        #self.progress_bar["value"] += 1

        print('Program finished.\n')
        #self.output.configure(state = 'disabled')

if __name__ == "__main__":
    app = Application()
    app.mainloop()
