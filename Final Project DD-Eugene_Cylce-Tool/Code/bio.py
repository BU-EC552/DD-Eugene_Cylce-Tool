import pandas as pd
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
import os, sys

#handler code for running local instance of javascript code
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
        self.root.geometry("1050x550")
        
        # global variables
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
        self.eugene_label = Label(root, text="Eugine Code: ",font=("Arial", 14))
        self.eugene_label.grid(row=2, column=3, padx=0, pady=60, sticky=W+N)

        '''BUTTONS'''
        # button to get the path of the data csv file
        self.file_btn = Button(root, text="Find CSV File", command= self.find_file, borderwidth=2, relief="raised")
        self.file_btn.grid(row=0,column=0, padx=20, pady=20, sticky=W)

        # create label for getting output path
        self.out_btn = Button(root, text="Select Output Location", command= self.select_output, borderwidth=2, relief="raised")
        self.out_btn.grid(row=2, column=0, padx=20, pady=350,sticky=S+W)

        
        # create button to call miniEugene
        self.eugene_btn = Button(root, text="miniEugene", command= self.open_eugene, font=("Arial", 10),borderwidth=1.4, relief="solid", width=10, height=3)
        self.eugene_btn.grid(row=2, column=3, padx=200, pady=0, sticky=N+W)
        
        # create button to call DubleDutch
        self.DD_btn = Button(root, text="Double Dutch", command= self.open_double_dutch, font=("Arial", 10),borderwidth=1.4, relief="solid", width=10, height=3)
        self.DD_btn.grid(row=2, column=3, padx=100, pady=0, sticky=N+W)
        
        # create button to compare
        self.comp_btn = Button(root, text="Compare", command= self.compare, font=("Arial", 10),borderwidth=1.4, relief="solid", width=10, height=3)
        self.comp_btn.grid(row=2, column=3, padx=0, pady=0, sticky=N+W)

        '''Text Field'''
        #entry field for miniEugene code
        self.eds_entry = Text(root, width=35, height=20)
        self.eds_entry.grid(row=2, column=3, padx=150, pady=65, sticky=N+W)
        
        '''ENTRY FIELDS'''
        # entry field to display path for data csv file
        self.file_entry = Entry(root, width=55)
        self.file_entry.grid(row=0, column=1, columnspan=2, padx=2, sticky=W)

        # entry field for the output path
        self.out_entry = Entry(root, width=55)
        self.out_entry.grid(row=2, column=1, columnspan=2, padx=5,pady=350, sticky=S+W)
        
        '''FRAME'''
        # create frame for the table
        self.tframe = Frame(root)
        self.tframe.grid(row=2, column=0, columnspan=3, padx=10, pady=20, sticky=N)


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
        driver = webdriver.Chrome(r"C:\Users\bmahabir\Desktop\chromedriver_win32\chromedriver.exe")
        driver.get('https://minieugene.eugenecad.org/')
        
    def open_double_dutch(self):
        #clear driver instantiate the local code for DD
        requests_session = requests.session()
        requests_session.mount('file://', LocalFileAdapter())
        r = requests_session.get('file:///C:/Users/bmahabir/Desktop/doubledutch/app/pathwayDesigner/pathwayDesigner.html#/')
        driver = None
        driver = webdriver.Chrome(r"C:\Users\bmahabir\Desktop\chromedriver_win32\chromedriver.exe")
        driver.get('file:///C:/Users/bmahabir/Desktop/doubledutch/app/pathwayDesigner/pathwayDesigner.html#/')
        
        
    def compare(self):
        self.table = TableCanvas(self.tframe)
        self.table.thefont = ('Arial',10)
        input = self.input_loc
        self.table.importCSV(input)
        self.table.show()
    
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