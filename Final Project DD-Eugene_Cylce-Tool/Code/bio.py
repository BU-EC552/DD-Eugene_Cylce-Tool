import pandas as pd
import tkinter as tk
from tkinter import *
from scipy import stats
from tkinter import filedialog
from tkintertable import TableCanvas, TableModel
import time
import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common import action_chains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
import os, sys

#handler code for running local instance of javascript code
#https://stackoverflow.com/questions/10123929/fetch-a-file-from-a-local-url-with-python-requests
if sys.version_info.major < 3:
    from urllib import url2pathname
else:
    from urllib.request import url2pathname

class LocalFileAdapter(requests.adapters.BaseAdapter):
    """Protocol Adapter to allow Requests to GET file:// URLs
    @todo: Properly handle non-empty hostname portions.
    """

    @staticmethod
    def _chkpath(method, path):
        """Return an HTTP status for the given filesystem path."""
        if method.lower() in ('put', 'delete'):
            return 501, "Not Implemented"  # TODO
        elif method.lower() not in ('get', 'head'):
            return 405, "Method Not Allowed"
        elif os.path.isdir(path):
            return 400, "Path Not A File"
        elif not os.path.isfile(path):
            return 404, "File Not Found"
        elif not os.access(path, os.R_OK):
            return 403, "Access Denied"
        else:
            return 200, "OK"

    def send(self, req, **kwargs):  # pylint: disable=unused-argument
        """Return the file specified by the given request
        @type req: C{PreparedRequest}
        @todo: Should I bother filling `response.headers` and processing
               If-Modified-Since and friends using `os.stat`?
        """
        path = os.path.normcase(os.path.normpath(url2pathname(req.path_url)))
        response = requests.Response()

        response.status_code, response.reason = self._chkpath(req.method, path)
        if response.status_code == 200 and req.method.lower() != 'head':
            try:
                response.raw = open(path, 'rb')
            except (OSError, IOError) as err:
                response.status_code = 500
                response.reason = str(err)

        if isinstance(req.url, bytes):
            response.url = req.url.decode('utf-8')
        else:
            response.url = req.url

        response.request = req
        response.connection = self

        return response

    def close(self):
        pass
##

'''MAIN GUI CLASS'''
class BIO:
    '''INSTANTIATION'''
    def __init__(self, root):
        # initialize the application
        self.root = root
        self.root.title("Pipeline Tool")
        self.root.geometry("1050x700")
        
        # global variables (make sure to change paths as necessary)
        
        #path to chrome driver
        self.chrome_driver_path = r"/Users/brianhjung/Desktop/Big_SynBio_Project/chromedriver"
        #path to local install of DD
        self.DD_path ='file:///Users/brianhjung/Desktop/Big_SynBio_Project/doubledutch-master/app/pathwayDesigner/pathwayDesigner.html'
        #path to miniEugene Website (shouldnt be changed)
        self.miniEugene_path = 'https://minieugene.eugenecad.org/'
        
        self.output_loc = ''
        self.input_loc = ''
        self.window = 1

        '''LABELS'''
        # labels for the program title
        self.title_label = Label(root, text="DD - Eugene Cycle Tool", font=("Helvetica", 20))
        self.title_label.grid(row=0, column=3, padx=10,pady=15, sticky=W)
        self.coders_label = Label(root, text="By, Coders Brian.M and Brian.H", font=("Arial", 14))
        self.coders_label.grid(row=1, column=3, padx=10,sticky=W)


        # label for error message
        self.error_label = Label(root, text="", fg='red',font=("Arial", 15))
        self.error_label.grid(row=2, column=3,padx=10,pady=240,sticky=S+W)

        #label to get miniEugene Code
        self.eugene_label = Label(root, text="Eugene Code: ",font=("Arial", 14))
        self.eugene_label.grid(row=2, column=3, padx=0, pady=60, sticky=W+N)
        
        #label for output text
        self.output_label = Label(root, text="Output: ",font=("Arial", 14))
        self.output_label.grid(row=2, column=3, padx=0, pady=250, sticky=W+N)
        
        #label for level per factor
        self.level_label = Label(root, text="Level per Factor",font=("Arial", 12))
        self.level_label.grid(row=2, column=0, padx=20, pady=300,sticky=S+W)
        
        #label for number of trials
        self.level_label = Label(root, text="# of Trials",font=("Arial", 12))
        self.level_label.grid(row=2, column=0, padx=20, pady=250,sticky=S+W)
        
        #label for Factorial Design
        self.level_label = Label(root, text="Factorial Design",font=("Arial", 12))
        self.level_label.grid(row=2, column=0, padx=20, pady=200,sticky=S+W)
        
        '''BUTTONS'''
        # button to get the path of the data csv file
        self.file_btn = Button(root, text="Find CSV File", command= self.find_file, borderwidth=2, relief="raised")
        self.file_btn.grid(row=0,column=0, padx=20, pady=20, sticky=W)

        # create label for getting output path
        self.out_btn = Button(root, text="Select Output Location", command= self.select_output, borderwidth=2, relief="raised")
        self.out_btn.grid(row=2, column=0, padx=20, pady=350,sticky=S+W)

        # create button to call miniEugene
        self.eugene_btn = Button(root, text="Solve", command= self.solve, font=("Arial", 10),borderwidth=1.4, relief="solid", width=10, height=3)
        self.eugene_btn.grid(row=2, column=3, padx=300, pady=0, sticky=N+W)
        
        self.eugene_btn = Button(root, text="miniEugene", command= self.open_eugene, font=("Arial", 10),borderwidth=1.4, relief="solid", width=10, height=3)
        self.eugene_btn.grid(row=2, column=3, padx=200, pady=0, sticky=N+W)
        
        # create button to call DubleDutch
        self.DD_btn = Button(root, text="Double Dutch", command= self.open_double_dutch, font=("Arial", 10),borderwidth=1.4, relief="solid", width=10, height=3)
        self.DD_btn.grid(row=2, column=3, padx=100, pady=0, sticky=N+W)
        
        # create button to compare
        self.comp_btn = Button(root, text="Load", command= self.load, font=("Arial", 10),borderwidth=1.4, relief="solid", width=10, height=3)
        self.comp_btn.grid(row=2, column=3, padx=0, pady=0, sticky=N+W)

        '''Text Field'''
        #entry field for miniEugene code
        self.eugene_entry = Text(root, width=35, height=10)
        self.eugene_entry.grid(row=2, column=3, padx=150, pady=65, sticky=N+W)
        
        # Create text widget and specify size.
        self.output_text = Text(root, width=35, height=10)
        self.output_text.grid(row=2, column=3, padx=150, pady=250, sticky=N+W)
  
        # Create label
        l = Label(root, text = "Fact of the Day")
        l.config(font =("Courier", 14))
        
        '''ENTRY FIELDS'''
        # entry field to display path for data csv file
        self.file_entry = Entry(root, width=55)
        self.file_entry.grid(row=0, column=1, columnspan=2, padx=2, sticky=W)

        # entry field for the output path
        self.out_entry = Entry(root, width=55)
        self.out_entry.grid(row=2, column=1, columnspan=2, padx=5,pady=350, sticky=S+W)
        
        # entry field for level per factor
        self.level_entry = Entry(root, width=10)
        self.level_entry.grid(row=2, column=0, columnspan=2, padx=150, pady=300,sticky=S+W)
        
        # entry field for number of Trials
        self.trials_entry = Entry(root, width=10)
        self.trials_entry.grid(row=2, column=0,columnspan=2, padx=150, pady=250,sticky=S+W)
        
        
        '''FRAME'''
        # create frame for the table
        self.tframe = Frame(root)
        self.tframe.grid(row=2, column=0, columnspan=3, padx=10, pady=20, sticky=N+W)
        
        
        '''Drop Down Menu'''
        self.drop_down = StringVar(root)
        # Dictionary with options
        choices = {'Box Behnken (2<N<13x3, N/=8)','Fractional Factorial (Nx2) III','Fractional Factorial (Nx2) IV',
        'Fractional Factorial (Nx2) V','Full Factorial (Any Size)','Plackett Burman (N<24x2)'}
        self.drop_down.set('Select Design') # set the default option
        popupMenu = OptionMenu(root, self.drop_down, *choices)
        popupMenu.grid(row=2, column=0,columnspan=2, padx=150, pady=200,sticky=S+W)
        
    '''Button Functions'''
    # function to get csv file path
    def find_file(self):
        # clear the entry field
        self.file_entry.delete(0, END)
        # clear errors
        self.error_label.config(text="")
        # get the path for the csv file
        self.root.filename = filedialog.askopenfilename(initialdir=".", title="Select A CSV File", 
                                                       filetypes=(("CSV Files", "*.csv"),("All Files", "*.*")))
        self.input_loc =  self.root.filename
        # insert the path to the entry field
        self.file_entry.insert(0, root.filename)

    def select_output(self):
        # clear  entry fields
        self.out_entry.delete(0, END)
        # clear errors
        self.error_label.config(text="")
        # use filedialog to select output location
        self.out_dir = filedialog.askdirectory(initialdir=".",title="Select A Folder To Store Output")
        # insert to entry field
        self.out_entry.insert(0, self.out_dir)
        # store in location
        self.output_loc = self.out_dir
        
    def open_eugene(self):
        #clear driver an instantiate the website for eugine
        driver = None
        driver = webdriver.Chrome(self.chrome_driver_path)
        driver.get(self.miniEugene_path)
        
    def open_double_dutch(self):
        #clear driver instantiate the local code for DD
        op = webdriver.ChromeOptions()
        op.add_argument('headless')
        requests_session = requests.session()
        requests_session.mount('file://', LocalFileAdapter())
        r = requests_session.get(self.DD_path)
        driver = None
        driver = webdriver.Chrome(self.chrome_driver_path,options=op)
        driver.get(self.DD_path)
        uploadElement = driver.find_element_by_xpath('html/body/div/div[1]/div[1]/input[3]')
        uploadElement.send_keys(self.input_loc)
        uploadElementbutton = driver.find_element_by_xpath('/html/body/div/div[1]/div[1]/button[1]')
        uploadElementbutton.click()
        time.sleep(6)
        moveAll = driver.find_element_by_xpath('/html/body/div/div[3]/div[1]/div[1]/button[2]')
        moveAll.click()
        time.sleep(2)
        lvlfac = driver.find_element_by_xpath('/html/body/div/div[3]/div[2]/div[1]/input')
        lvlfac.clear()
        lvlfac.send_keys(self.factorLevls)
        time.sleep(1)
        editbutton = driver.find_element_by_xpath('/html/body/div/div[3]/div[2]/div[1]/button[2]')
        editbutton.click()
        modtrials = driver.find_element_by_xpath('/html/body/div[3]/div/div/div[2]/div/div[1]/div[2]/input[1]')
        modtrials.clear()
        modtrials.send_keys(self.trialNums)
        time.sleep(1)
        donebutton = driver.find_element_by_xpath('/html/body/div[3]/div/div/div[3]/button[2]')
        donebutton.click()
        time.sleep(1)
        selecting = driver.find_element_by_xpath('/html/body/div/div[1]/div[2]/select')
        selecting = Select(selecting)
        selecting.select_by_visible_text(self.factorialDesign)
        time.sleep(1)
        assignIt = driver.find_element_by_xpath('/html/body/div/div[3]/div[2]/div[1]/button[1]')
        assignIt.click()
        outputText = driver.find_element_by_xpath('/html/body/div/div[3]/div[1]/div[2]/p')
        librarydownload = driver.find_element_by_xpath('/html/body/div/div[3]/div[2]/div[1]/div/button[2]').click()
        assignmentdownload = driver.find_element_by_xpath('/html/body/div/div[3]/div[2]/div[1]/div/button[1]').click()
        self.output_text.insert(tk.END,outputText.text)

        
        
    def load(self):
        class Pair:
          def __init__(self, part1, part2):
            self.part1 = part1
            self.part2 = part2

        #add input path as a var
        input = self.input_loc
        #create table
        self.table = TableCanvas(self.tframe)
        self.table.thefont = ('Arial',10)
        
        #edit csv and save
        df = pd.read_csv(input)
        #create list of factors
        self.inputEugeneText = self.eugene_entry.get("1.0",'end-1c')
        factors = list()
        pairings = list()

        for myline in self.inputEugeneText.splitlines():
            tempWord = myline.split()
            if (len(tempWord)>1):
                if tempWord[0] == "CONTAINS" or tempWord[0] == "contains":
                    factors.append(tempWord[1])
                if (tempWord[1] == "MORETHAN" or tempWord[1] == "EXACTLY" or tempWord[1] == "SAME_COUNT" or
                tempWord[1] == "morethan" or tempWord[1] == "exactly" or tempWord[1] == "same_count"):
                    factors.append(tempWord[0])
                if (tempWord[1] == "REPRESSES" or tempWord[1] == "INDUCES" or tempWord[1] == "DRIVES" or tempWord[1] == "WITH" or 
                tempWord[1] == "THEN" or tempWord[1] == "represses" or tempWord[1] == "induces" or tempWord[1] == "drives" or 
                tempWord[1] == "with" or tempWord[1] == "then"):
                    if(tempWord[0][0]=="C" or tempWord[0][0]=="c" or tempWord[2][0]=="C" or tempWord[2][0]=="C"):
                        pairings.append(Pair(tempWord[0],tempWord[2]))
        
        #add list to dataframe
        col_one = df['Constraints'].tolist()
        c_factor = col_one + factors
        df2 = pd.DataFrame(c_factor, index=None)
        df = pd.concat([df2,df], axis=1)
        df = df.drop(columns=['Constraints'])
        #df.apply(lambda col: col.drop_duplicates().reset_index(drop=True))
        
        index = input.find('.csv')
        input_edit = input[:index] + '_edited' + input[index:]
        df.to_csv(input_edit,index=False)
        #import edited excel file
        self.table.importCSV(input_edit)
        self.table.show()
        
        '''Load function also set up varaibles of trails, level per factor, and factorial design'''
        self.trialNums = int(self.trials_entry.get())
        self.factorLevls = int(self.level_entry.get())
        self.factorialDesign = self.drop_down.get()

        '''Code to output text, get entry data, and drop down menu'''
        #text output to show it wworked
        self.output_text.insert(tk.END,"Good job!")

        
        
    def solve(self):
        pass
    
    '''Non Button Functions'''
    # load sorted data as pandas dataframe
    def load_sorted(self,name):
        # file location for the csv file
        file = name
        # return pandas dataframe of the csv file
        df = pd.read_csv(file)
        # remove all NaN entries
        df.drop(df.filter(regex="Unname"),axis=1, inplace=True)
        return df
    
   
# run the program
root = Tk()
gui = BIO(root)
root.mainloop()