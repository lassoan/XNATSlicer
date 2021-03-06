__author__ = "Sunil Kumar (kumar.sunil.p@gmail.com)"
__copyright__ = "Copyright 2014, Washington University in St. Louis"
__credits__ = ["Sunil Kumar", "Steve Pieper", "Dan Marcus"]
__license__ = "XNAT Software License Agreement " + \
              "(see: http://xnat.org/about/license.php)"
__version__ = "2.1.1"
__maintainer__ = "Rick Herrick"
__email__ = "herrickr@mir.wustl.edu"
__status__ = "Production"


# python
import os
import sys
import shutil

# application
from __main__ import qt, slicer

# external
from MokaUtils import *

# module
from XnatSlicerGlobals import *
from FileInfo import *
from XnatSlicerUtils import *
from ScenePackager import *
from SessionManager import *
from Timer import *




class SaveDialog(object):
    """
    SaveDialog is a parent class that manages various 
    dialogs related to saving Xnat files.  Dialogs occur
    in a sequence, hence there are multiple dialogs to 
    be managed.  This class handles the generic functions
    related to their management: setting the number of dialogs,
    closing the dialogs, etc. The contents of the dialogs 
    are specified in the 
    
    The classes that inherit from it are:
        1. XnatSaveUnlinkedDialog: For saving a scene that doesn't 
           originate from an XNAT host.
        2. XnatFileSaveDialog: Where user enters filename of the scene to save.
    """
    
    def __init__(self, MODULE, saveWorkflow):
        """ 
        Init function.

        @param MODULE: 
        @type MODULE: XnatSlicerWidget
        @param saveWorkflow:
        @type saveWorkflow: Workflow_Save
        """

        self.MODULE = MODULE
        self.dialogs = []               
        self.saveWorkflow = saveWorkflow;



    
        
    def show(self):
        """ Shows the first dialog in a dialog sequence,
            and adjusts its position.
        """

        #--------------------
        # Show first window in the dialog sequence.
        #--------------------
        self.dialogs[0].show()
        

        
        #--------------------
        # Adjust position of first window.
        #--------------------
        mainWindow = slicer.util.mainWindow()
        screenMainPos = mainWindow.pos
        x = screenMainPos.x() + 400
        y = screenMainPos.y() + 400
        self.dialogs[0].move(qt.QPoint(x,y))     


        
        
    def okClicked(self):
        """ To be inherited by sub-class.
        """
        pass



    
    def yesClicked(self):
        """ To be inherited by sub-class.
        """
        pass



    
    def noClicked(self):
        """ To be inherited by sub-class.
        """
        pass



    
    def cancelClicked(self):
        """ Hides all dialogs.
        """
        for dialog in self.dialogs: dialog.hide()
        return



    
    def setNumDialogs(self, numDialogs = 1, dialogType = None):
        """ User can set the amount of dialogs in the
            dialog sequence.
        """
        for x in range(0, numDialogs):
            try:
                #
                # Set dialog based on the 'dialogType' argument.
                #
                self.dialogs.append(dialogType[str(x)])      
            except Exception as e:
                #
                # Set default based on the default 'dialogType' argument.
                #
                dialog = qt.QMessageBox()
                self.dialogs.append(dialog)   
                self.dialogs[x].connect('buttonClicked(QAbstractButton*)', self.onButtonClicked)
                self.dialogs[x].setTextFormat(1)
                #
                # NOTE: Need to keep the window modality
                # always in front.  Blocking out 
                # all other interactions.
                #
                self.dialogs[x].setWindowModality(1) 



                
    def onButtonClicked(self):
        pass


    
    def setup(self):     
        """ Descriptor
        """      
        pass



class XnatSaveUnlinkedDialog(SaveDialog):
     """ Dialog sequence for saving Slicer scenes
         to an XNAT host where the scene content is 
         detateched from the XNAT location.  The use-case
         driving this is when a user desires to upload
         a local scene to a given XNAT host.
     """

     def __init__(self, MODULE, saveWorkflow):
        """ Init function.
        """

        #--------------------
        # Call parent class.
        #--------------------
        super(saveUnlinkedDialog, self).__init__(MODULE, saveWorkflow)
        self.setup()


        
       
     def setup(self):
         """ Sets the number of dialogs and their
             contents.
         """

         #--------------------
         # Dialog setup
         #--------------------
         self.setNumDialogs(1)
         msg = """the scene doesn't appear to be associated with a specific xnat location.  Would you like to save it within this xnat """
         msg = "%s %s (%s)?" %(msg, XnatSlicerGlobals.DEFAULT_XNAT_SAVE_LEVEL[:-1], os.path.basename(self.MODULE.View.sessionManager.sessionArgs['savelevel']))
         msg.replace('location', XnatSlicerGlobals.DEFAULT_XNAT_SAVE_LEVEL[:-1])
         self.dialogs[0].setText(msg)      
         


         #--------------------
         # Button setup
         #--------------------
         self.dialogs[0].addButton(qt.QMessageBox.yes)
         self.dialogs[0].addButton(qt.QMessageBox.cancel)
         self.MODULE.XNAView.selectItem_byPath((self.MODULE.View.sessionManager.sessionArgs['savelevel']))



         
     def buttonclicked(self,button):
        """ When a button on the dialog is clicked.  
            Creates a XnatFileSaveDialog once the user gives
            the OK to save the scene to the XNAT host.  The
            user is prompted for this because XNATSlicer could
            not determine the origin XNAT host/location of the scene.
        """

        #--------------------
        # If ok button clicked.
        #--------------------
        if button.text.lower().find('yes') > -1: 
            #
            # Call FileSave with updated sessionArgs.
            #
            XnatFileSaveDialog(self.MODULE, self.MODULE.View.sessionManager.sessionArgs)


            


            
class XnatFileSaveDialog(SaveDialog):  
    """ Dialog sequence that allows the user
        to specify the filename to be written to 
        a given XNAT host.
    """

    
    
    def __init__(self, MODULE, saveWorkflow):
        """ Init function.
        """

        
        #--------------------
        # Call parent.
        #--------------------
        super(XnatFileSaveDialog, self).__init__(MODULE, saveWorkflow)

        self.MODULE = MODULE
        
        
        #--------------------
        # Determine filename.
        #--------------------
        self.fileName = None


        #--------------------
        # Dialog setup.
        #--------------------
        self.inputIndex = 0  
        self.noticeLabel = qt.QLabel("")

  

        #--------------------
        # Window setup.   
        #--------------------
        self.setNumDialogs(1, {'0':qt.QDialog(slicer.util.mainWindow())}) 
        self.dialogs[0].setFixedWidth(600)
        self.dialogs[0].setWindowModality(1)


        
        #--------------------
        # Label button and fileLine.
        #--------------------
        self.saveButtonStr = "Save"
        fileLineLabel = qt.QLabel("File Name: ")

        

        #--------------------
        # Set fileline text (where user enters the file
        # name) 
        #--------------------
        self.fileLine = qt.QLineEdit(self.MODULE.View.sessionManager.sessionArgs['fileName'].split(XnatSlicerGlobals.DEFAULT_SLICER_EXTENSION)[0])

        

        #--------------------
        # Create file name input layout.
        #--------------------
        fileInputLayout = qt.QHBoxLayout()
        fileInputLayout.addWidget(fileLineLabel)
        fileInputLayout.addWidget(self.fileLine)
        dialogLayout = qt.QVBoxLayout()
     

        
        #--------------------
        # Create the buttons.
        #--------------------
        saveButton = qt.QPushButton()
        saveButton.setText(self.saveButtonStr)
        cancelButton = qt.QPushButton()
        cancelButton.setText("Cancel")
        buttonRow = qt.QDialogButtonBox()
        buttonRow.addButton(saveButton, 0)
        buttonRow.addButton(cancelButton, 2)               
        

        
        #--------------------
        # Put buttons in the bottom row.
        #--------------------
        bottomRow = qt.QHBoxLayout()
        bottomRow.addWidget(buttonRow)

        

        #--------------------
        # Add the layouts to the dialog.
        #--------------------
        dialogLayout.addLayout(fileInputLayout)
        dialogLayout.addWidget(self.noticeLabel)
        dialogLayout.addLayout(bottomRow)
        self.dialogs[0].setLayout(dialogLayout)


        
        #--------------------
        # Set onClick connections.
        #--------------------  
        buttonRow.connect('clicked(QAbstractButton*)', self.onButtonClicked)
        #self.MODULE.View.selectItem_byUri(self.MODULE.View.sessionManager.sessionArgs['saveLevel'])



        ##print("%s"%(MokaUtils.debug.lf()))



            
    def onButtonClicked(self, button):
        """ onClick method for when a dialog button
            is clicked.  If the button clicked is 'yes' or 'ok',
            calls the appropriate upload methods.
        """

        #--------------------
        # Hide the dialog
        #--------------------
        slicer.app.processEvents()
        self.dialogs[0].hide()         


        
        #--------------------
        # Get filename from the text input line.
        #--------------------
        self.MODULE.View.sessionManager.sessionArgs['fileName'] = MokaUtils.string.replaceForbidden(self.fileLine.text.split(".")[0], "_")
        if len(self.MODULE.View.sessionManager.sessionArgs['fileName']) == 0:
            import datetime
            self.MODULE.View.sessionManager.sessionArgs['fileName'] = datetime.datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
            
        self.MODULE.View.sessionManager.sessionArgs['fileName'] += XnatSlicerGlobals.DEFAULT_SLICER_EXTENSION


        
        #--------------------
        # If 'yes' or 'ok' button is clicked, then save...
        #--------------------
        if self.saveButtonStr.lower() in button.text.lower():                             
            #
            # Pre-save.  Start an new session and make the necessary
            # slicerSave folders in the XNAT host.
            #
            self.MODULE.View.startNewSession(self.MODULE.View.sessionManager.sessionArgs)
            self.MODULE.View.makeRequiredSlicerFolders() 
            #
            # Save scene to XNAT host.    
            #     
            self.saveWorkflow.saveScene()   
            #
            # UI config
            #
            self.MODULE.View.setEnabled(True)


            
        #--------------------    
        # Otherwise reenable everything.
        #--------------------
        else:
            self.MODULE.View.setEnabled(True)
            
