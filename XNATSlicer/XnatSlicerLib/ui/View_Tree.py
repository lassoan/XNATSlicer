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

# application
from __main__ import qt, slicer

# external
from Xnat import *
from MokaUtils import *

# module
from View import *
from Timer import *
from XnatSlicerUtils import *
from XnatSlicerGlobals import *




class View_Tree(View, qt.QTreeWidget):
    """ 
    View_Tree is a subclass of both the View class and the
    qt.QTreeWidget class.  It presents XNAT file system accessed
    in a tree-node hierarchy, with customized columns masks to avoid 
    visual clutter and maximize interactibility.
    
    The view classes (and subclasses) ultimately communicate
    with the load and save workflows.   

    
    """  

    DEFAULT_FONT_SIZE = 10
    
    def setup(self):
        """ 
        Setup function for View_Tree.
        """
        
        #----------------------
        # View_Tree
        #----------------------
        qt.QTreeWidget.__init__(self)
        self.setAnimated(True)
        self.setHeaderHidden(False)       
        #treeWidgetSize = qt.QSize(100, 200)
        #self.setBaseSize(treeWidgetSize)

        
        
        #----------------------
        # View_Tree Columns
        #----------------------
        self.initColumns()

        

        #----------------------
        # Fonts
        #----------------------
        self.currentFontSize = XnatSlicerGlobals.FONT_SIZE
        self.itemFonts = {}
        self.itemFonts['folders'] = qt.QFont("Arial", 
                                self.currentFontSize, 25, False)
        self.itemFonts['file'] = qt.QFont("Arial", 
                                    self.currentFontSize, 75, False)
        self.itemFonts['category'] = qt.QFont("Arial", 
                                        self.currentFontSize, 25, True)
        self.itemFonts['searchHighlight'] = qt.QFont("Arial", 
                                            self.currentFontSize, 25, False)

        
        
        #----------------------
        # Tree-related globals
        #----------------------
        self.dirText = None           


        
        #----------------------
        # Scene globals
        #----------------------
        self.lastButtonClicked = None 



        
        #----------------------
        # Folder masks
        #----------------------
        self.applySlicerFolderMask = True
        self.hideSlicerHelperFolders = True


        
        #----------------------
        # Delete dialog
        #----------------------
        self.deleteDialog = qt.QMessageBox()   


        
        #--------------------
        # NOTE: fixes a scaling error that occurs with the scroll 
        # bar.  Have yet to pinpoint why this happens.
        #--------------------
        self.verticalScrollBar().setStyleSheet('width: 15px')
        self.updateFromSettings()




    def updateFontFromSettings(self):
        """
        """
        if not self.Setting.currXnatHost:
            return
            
        storedFontSetting = self.Setting.getStoredFont(
                           self.Setting.LABEL_FONT_SIZE)
        storedFont = int(storedFontSetting[0]) if \
                     len(storedFontSetting) > 0 else \
                     XnatSlicerGlobals.FONT_SIZE
        self.changeFontSize(storedFont)




    def updateFromSettings(self):
        """
        """
        # 
        # NOTE: since 'changeFontSize' runs a 'refreshColumns'
        # it will automatically update the Info column metdata as well.
        #
        self.updateFontFromSettings()
                                            


    def changeFontSize(self, size):
        """
        """
        self.currentFontSize = size
        for key, font in self.itemFonts.items():
            font.setPointSize(self.currentFontSize)
        self.refreshColumns()

        
        

    def initColumns(self):
        """ 
        Intializes the columns of the qView_TreeWidget
        tailoring XNAT metadata to columns.  There are merged 
        columns that blend two or more columns together
        and there are single columns associated with single
        XNAT metadata values.
        """
        self.columns = {}
        for key, level in Xnat.metadata.DEFAULT_TAGS.items():
            for metadata in level:
                if not metadata in self.columns:
                    self.columns[metadata] = {}


            
        #-----------------------
        # Apply metadata key to the columns.  Manuplulate
        # the string values of the tags to make them more
        # human-readable.
        #----------------------
        for key in self.columns:
            strVal = key.replace('_',' ').title()
            strVal = strVal.replace('Pi', 'PI')
            strVal = strVal.replace('Uri', 'URI')
            strVal = strVal.replace(' 497', '')
            strVal = strVal.replace('Id', 'ID')
            self.columns[key]['displayname'] = strVal


            
        #----------------------
        # MERGED_LABEL, and XNAT_LEVEL columns are not 
        # part of the metadata set so we're adding them. 
        #---------------------- 
        self.columns['MERGED_LABEL'] = {}  
        self.columns['MERGED_LABEL']['displayname'] = 'Name/ID/Label'   
        self.columns['XNAT_LEVEL'] = {}  
        self.columns['XNAT_LEVEL']['displayname'] = 'Level'      
        self.columns['MERGED_INFO'] = {}  
        self.columns['MERGED_INFO']['displayname'] = 'Info' 


        
        #----------------------
        # Define column keys based on XNAT_LEVEL.  
        # More columns can be added by uncommenting.
        #---------------------- 
        self.columnKeyOrder = {}
        self.columnKeyOrder['ALL'] = [
            'MERGED_LABEL',
            'XNAT_LEVEL',
            'MERGED_INFO'
        ]



        #----------------------
        # Set the preliminary 'visibleColumnKeys' for 
        # just the ones in self.columnKeyOrder['ALL']
        #----------------------       
        self.visibleColumnKeys = self.columnKeyOrder['ALL']


        
        #---------------------- 
        # Merge 'self.columnKeyOrder' with
        # the XnatIo.DEFAULT_METADATA
        #---------------------- 
        self.columnKeyOrder = {**self.columnKeyOrder, **Xnat.metadata.DEFAULT_TAGS}
        


        #---------------------- 
        # Create a union of all the self.columnKeyOrder 
        # arrays (i.e. 'allHeaders')
        #---------------------- 
        allHeaders = MokaUtils.list.uniqify(self.columnKeyOrder['ALL'] + 
            # NOTE: Leaving this out as it will 
            # become part of MERGED_LABELS
            # via self.getMergedLabelByLevel, which 
            # determines the relevant
            # metadata tag for the given XNAT level.
            # self.columnKeyOrder['LABELS'] + 
            self.columnKeyOrder['projects'] + 
            self.columnKeyOrder['subjects'] + 
            self.columnKeyOrder['experiments'] + 
            self.columnKeyOrder['resources'] + 
            self.columnKeyOrder['scans'] + 
            self.columnKeyOrder['files'] + 
            self.columnKeyOrder['slicer'])


        
        #---------------------- 
        # Create columns based on 'allHeaders'
        #----------------------         
        self.setColumnCount(len(allHeaders))
        headerLabels = []
        for header in allHeaders:
            try:
                #
                # Set other column key/values.
                #
                self.columns[header]['location'] = len(headerLabels)
                #
                # Set the headerLabels.
                #
                headerLabels.append( self.columns[header]['displayname'])
            except Exception as e:
                ##print e, "column init stuff"
                continue
        self.setHeaderLabels(headerLabels)


        
        #---------------------- 
        # Allow columns to be clicked and sorted.
        #----------------------  
        self.columnSorts = [None for i in range(0, len(self.columns))]
        def onHeaderClicked(index):
            if self.columnSorts[index] == None:
                self.columnSorts[index] = 0
            elif self.columnSorts[index] == 0:
                self.columnSorts[index] = 1
            else:
                self.columnSorts[index] = 0
                
            self.sortItems(index, self.columnSorts[index])
            
        header = self.header()
        header.setSectionsClickable(True)
        header.connect('sectionClicked(int)', onHeaderClicked)
                



        
    def getMergedLabelTagByLevel(self, level):
        """ 
        Points the MERGED_LABEL column tag to the relevant
        XNAT metadata tag.  This is for the Name/ID/Label column.
        """ 
        level = level.lower()
        if level == 'projects': 
            #
            # NOTE: this would be in all caps if there were no query arguments.
            # since we only query projects that the user has access to, 
            # we have to use a lowercase 'id'.
            #
            return 'id'
        elif level == 'scans':
            return 'ID'
        elif level == 'subjects' or level == 'experiments':
            return 'label'
        elif level == 'files' or level == 'slicer':
            return 'Name'           



        
    def populateColumns(self, widgetItem = None, xnatMetadata = None):
        """ Fills the row values for a given set of columns for
            a tree node.  The columns correspond to the keys of
            the 'xnatMetadata' argument.
        """

        #------------------
        # POPULATE ALL COLUMNS EXCEPT MERGED_INFO
        #
        # Populate all of the columns if the 'xnatMetadata'
        # argument is provided.
        #
        # If it isn't, we assume that the colummns
        # have already been populated.
        #------------------
        if xnatMetadata != None:
            
            for key in xnatMetadata:

                
                #
                # Leave out metadata without a 
                # corresponding column.
                #
                if not key in self.columns:
                    continue

                
                #
                # Filtered projects return a lowercase 'id'
                # need to convert this back to uppercase.
                #
                columnKey = key
                if key == 'id':
                    columnKey = 'ID'


                #
                # Set the column text, if the coulumn
                # has a location.
                #
                value = xnatMetadata[key]
                self.columns[columnKey]['value'] = value
                if 'location' in self.columns[columnKey]:
                    widgetItem.setText(self.columns[columnKey]['location'],\
                                       value)
        

            #
            # Nodes below the 'project' level will not have
            # the 'MERGED_LABEL' key in xnatMetadata.  We need to construct it.
            #
            if not 'MERGED_LABEL' in xnatMetadata:
                xnatLevel = self.columns['XNAT_LEVEL']['value']
                labelTag = self.getMergedLabelTagByLevel(xnatLevel)
                widgetItem.setText(self.columns['MERGED_LABEL']['location'], \
                                   xnatMetadata[labelTag])



                
        
        #------------------
        # Construct MERGED_INFO
        #------------------
        mergedInfoColumnNumber = self.columns['MERGED_INFO']['location']
        xnatLevelColumnNumber = self.columns['XNAT_LEVEL']['location']

        storedMetadata = self.Setting.getStoredMetadata( \
                                      self.Setting.LABEL_METADATA, 
                                      widgetItem.text(xnatLevelColumnNumber),
                                      True)


        #MokaUtils.debug.lf("Info metadata: ", storedMetadata)


        ##print "MERGED INFO TEXT:", widgetItem.text(mergedInfoColumnNumber)
        #
        # Clear the text
        #
        widgetItem.setText(mergedInfoColumnNumber, '')

        def debugPrint():
            printStr = ''
            for i in range(0, 40):
                printStr += '\n\t' + self.headerItem().text(i) + ": " +  \
                widgetItem.text(i)
            #MokaUtils.debug.lf(printStr)

        debugPrint()

        
        #
        # Aggregate the text as we cycle through
        # the storedMetadata
        #
        ##print "INFO METADATA", storedMetadata
        for key in storedMetadata:
            
            try:
                ##print "COLUMN: ", self.columns
                ##print "KEY: ", self.columns[key]
                value = widgetItem.text(self.columns[key]['location'])
                ##print "VALUE: ", value
            except Exception as e:
                value = '(Empty)'
                xnatLevel = self.columns['XNAT_LEVEL']['value']
                key2 = str(e)
                MokaUtils.debug.lf("\n\nProperty '%s' does not exist in provided XNAT metadata at the '%s' level.  "%(key2, xnatLevel) +  
                                   "If this is a custom tag, you need to modify your XNAT server to provide it.  " +
                                   "\nTo remove this tag, open the 'XNAT Metadata' tab of the settigs window," + 
                                   "and remove '%s' property from the 'CUSTOM' section of the '%s' collapsible."%(key2, xnatLevel))

            #
            # Only allow metadata with a corresponding column.
            #
            if key in self.columns:
                ##print "WIDGET", widgetItem.text(0), key, self.columns[key]

                #
                # Convert date tags to human readable
                #
                if key in Xnat.metadata.DEFAULT_DATE_TAGS:
                    value = XnatSlicerUtils.makeDateReadable(value)
                widgetItem.setText(mergedInfoColumnNumber, 
                                   widgetItem.text(mergedInfoColumnNumber) + 
                                   self.columns[key]['displayname'] + ': ' + 
                                   value + ' ')
                widgetItem.setFont(mergedInfoColumnNumber, 
                                   self.itemFonts['folders'])  

        
        
        #-------------------
        # Set aesthetics.
        #-------------------
        #
        # De-bold font.
        #
        widgetItem.setFont(self.columns['MERGED_LABEL']['location'], 
                           self.itemFonts['folders']) 
        widgetItem.setFont(self.columns['XNAT_LEVEL']['location'], 
                           self.itemFonts['category']) 
        self.changeFontColor(widgetItem, False, "black", 
                             self.columns['MERGED_LABEL']['location'])
        self.changeFontColor(widgetItem, False, "grey", 
                             self.columns['XNAT_LEVEL']['location'])


        #
        # Set the font color to green if slicer exists
        #
        if widgetItem.text(\
                        self.columns['XNAT_LEVEL']['location']) == 'Slicer' or \
           widgetItem.text(self.columns['XNAT_LEVEL']['location']) == 'files':
            self.changeFontColor(widgetItem, False, "green", 
                                 self.columns['MERGED_LABEL']['location'])



            
            
        #-------------------
        # Hide columns that aren't part of the 'visibleColumnKeys' 
        # group.
        #-------------------
        visibleHeaders = [self.columns[key]['displayname'] \
                          for key in self.visibleColumnKeys] 
        headerItem = self.headerItem()
        for i in range(0, self.columnCount):
            setHidden = not headerItem.text(i) in visibleHeaders
            self.setColumnHidden(i, setHidden)

                

                
        return widgetItem


    
        
    def getColumn(self, metadataKey):
        """ 
        Returns a column location within the qTreeWidget based on it's 
        metadata key.
        @return: The column number.
        @rtype: int
        """
        return self.columns[metadataKey]['location']



    
    def getItemName(self, item = None):
        """ 
        Returns the 'MERGED_LABEL' value of the item.
        @return: The 'MERGED_LABEL' value of the item.
        @rtype: str
        """
        if not item: 
            item = self.currentItem()
        return item.text(self.columns['MERGED_LABEL']['location'])
        



    def getItemLevel(self, item = None):
        """ 
        Returns the 'XNAT_LEVEL' value of the item.
        @return: The 'XNAT_LEVEL' value of the item.
        @rtype: str
        """
        if not item: 
            item = self.currentItem()
        return item.text(self.MODULE.View.columns['XNAT_LEVEL']['location'])


    
    def removeCurrItem(self):
        """ 
        Returns the currentItem
        """
        try:
            self.currentItem().parent().removeChild(self.currentItem())
        except Exception as e:
            #print "Deleting top level (%s"%(str(e))
            self.removeItemWidget(self.currentItem(), 0)
            
    

    
    def resizeColumns(self):
        """ 
        As stated.  Resizes the columns according to the content
        by calling on the qt.QTreeWidget 'resizeColumnToContents' function.
        
        NOTE: Suspending for now as it creates awkward UX.
        """
        return
        for key in self.columns:
            if 'location' in self.columns[key]:
                self.resizeColumnToContents(self.columns[key]['location'])





                
                
    def sort_accessed(self):
        """
        """
        self.sortItems(self.columns['last_accessed_497']['location'], 1)

        


        
            
    def filter_accessed(self):
        """
        """
        self.sortItems(self.columns['last_accessed_497']['location'], 1)
        def hideEmpty(child):
            accessedText = child.text(self.columns['last_accessed_497']\
                                      ['location'])
            if accessedText == '': 
                child.setHidden(True)  
        self.loopProjectNodes(hideEmpty)


        

    def filter_all(self):
        """
        """
        self.sortItems(self.columns['MERGED_LABEL']['location'], 0)
        def showChild(child):
            child.setHidden(False)
        self.loopProjectNodes(showChild)   



        
    def loadProjects(self, filters = None, projectContents = None):
        """ Specific method for loading projects.  'Project'-level
            nodes necessiate for special handling in terms of assigning
            parents and filtering.
        """

    
        #----------------------
        # Add projects only if they are specified 
        # in the arguments.
        #----------------------
        if projectContents:
            #
            # Make tree Items from projects.
            #               
            projectContents['XNAT_LEVEL'] = ['projects' for p \
                                             in projectContents['id']]
            projectContents['MERGED_LABEL'] = [p for p in projectContents['id']]
            self.makeTreeItems(parentItem = self, 
                               children = projectContents['MERGED_LABEL'], 
                               metadata = projectContents, 
                               expandible = [0] * \
                               len(projectContents['MERGED_LABEL']))

            self.connect("itemExpanded(QTreeWidgetItem *)", \
                         self.onTreeItemExpanded)
            self.connect("currentItemChanged(QTreeWidgetItem *, " + 
                         "QTreeWidgetItem *)", self.manageTreeNode)

        
            
        #----------------------
        # If no 'filters'...
        #----------------------
        defaultFilterButton = None 
        self.defaultFilterFunction = self.sort_accessed
        if not filters or len(filters) == 0:
            #
            # Run the default filter function
            #
            self.defaultFilterFunction()
            #
            # Count and compare hidden nodes with all nodes
            #
            self.nodeCount = 0
            self.hiddenNodeCount = 0
            def checkEmpty(child):
                if child.isHidden():
                    self.hiddenNodeCount += 1
                self.nodeCount += 1
            self.loopProjectNodes(checkEmpty) 
            #
            # If there are no visible nodes, uncheck the default filter button,
            # so the filter reverts to 'all'.
            #
            if self.nodeCount > 0 and \
               self.nodeCount == self.hiddenNodeCount and defaultFilterButton:
                defaultFilterButton.click()


            self.topLevelItem(0).setSelected(True)
            self.setCurrentItem(self.topLevelItem(0))
            return True




        
        #----------------------
        # If filter is 'accessed' (i.e. 'Last Accessed')
        #----------------------        
        elif filters[0] == 'accessed':
            self.filter_accessed()
            self.topLevelItem(0).setSelected(True)
            self.setCurrentItem(self.topLevelItem(0))
            return True


        
        #----------------------
        # If filter is 'all'
        #----------------------        
        elif filters[0] == 'all':
            self.filter_all()
            self.topLevelItem(0).setSelected(True)
            self.setCurrentItem(self.topLevelItem(0))
            return True

        

        return True




    def getParentItemByXnatLevel(self, item, xnatLevel):
        """
        """
        parentItem = item
        while parentItem:
            if parentItem.text(\
                    self.columns['XNAT_LEVEL']['location']) == xnatLevel:
                return parentItem
            parentItem = parentItem.parent()
        
    

    def loopProjectNodes(self, callback):
        """ 
        Loops through all of the top level
        treeItems (i.e. 'projects') and allows the user
        to run a callback.
        """
        ind = 0
        currChild = self.topLevelItem(ind)
        while currChild:
            callback(currChild)
            ind += 1
            currChild = self.topLevelItem(ind)




    def expandItem(self, item = None):
        """
        As sated.
        """
        if not item and self.currentItem():
            item = self.currentItem()
        self.onTreeItemExpanded(item)
        



    def projectExists(self, projectName):
        """
        Determines if a project of a given name exists.
        @param projectName: The project name.
        @type projectName: str
        @return: Whether the project exists.
        @rtype: bool
        """
        self.__projExists = False
        def findProj(item):
            if projectName.lower() == self.getItemName(item).lower():
                self.__projExists = True
        self.loopProjectNodes(findProj)
        return self.__projExists




    def loopSiblingNodes(self, callback, item = None):
        """
        Loops the nodes at the sibling level.

        @param callback: The callback function.
        @type callback: function

        @param item: The item provided, defaults to current.
        @type item: qt.QTreeWidgetItem
        """
        if not self.currentItem() or self.getItemLevel() == 'projects':
            self.loopProjectNodes(callback)
        else:
            self.loopChildren(self.currentItem().parent(), callback)



    def loopChildren(self, item, callback):
        """
        @param callback: The callback function.
        @type callback: function

        @param item: The item provided, defaults to current.
        @type item: qt.QTreeWidgetItem
        """
        for i in range(0, item.childCount()):            
            currChild = item.child(i)
            callback(currChild)
            


    def traverseTree(self, item, callback):
        """
        """
        
        for i in range(0, item.childCount()): 
            currChild = item.child(i)
            callback(currChild)
            self.traverseTree(currChild, callback)
            
                

                
                
    def loopVisible(self, callback):
        """ Loops through all of the top level
            treeItems (i.e. 'projects') and allows the user
            to run a callback.
        """
        def looper(projNode):
            callback(projNode)
            self.traverseTree(projNode, callback)
        self.loopProjectNodes(looper)

            

            

    def makeRequiredSlicerFolders(self, path = None):  
        """ Puts the required 'Slicer' folders in the reuqired location
            of the current XNAT host.
        """     
        if self.sessionManager.sessionArgs:
            self.MODULE.XnatIo.putFolder(os.path.dirname(\
                                        self.sessionManager.\
                                                sessionArgs['saveUri']))





    
    def getXnatUri(self, parents = None):
        """ Constructs a directory structure based on the default Xnat 
            organizational scheme, utilizing the tree hierarchy. Critical to 
            communication with Xnat. Ex. parents = [exampleProject, testSubj, 
            testExpt, scan1, images], then returns: 
            'projects/exampleProject/subjects/testSubj/experiments/' +
            'testExpt/scans/scan1/resources/images'  
        """  
        isResource = False
        isSlicerFile = False
        dirStr = "/"        


        
        #------------------------
        # Make the parents if they're not
        # provided.
        #------------------------
        if not parents:
            parents = self.getParents(self.currentItem())


            
        #------------------------
        # Construct preliminary URI based on the 'parents' array.
        #------------------------
        XnatDepth = 0        
        for item in parents:     
             
            # For resource folders
            if 'resources' in item.text(self.columns['XNAT_LEVEL']\
                                        ['location']).strip(" "): 
                isResource = True    
                
            # For masked slicer folders
            elif 'slicer' in item.text(self.columns['XNAT_LEVEL']\
                                       ['location']).lower() and \
                self.applySlicerFolderMask: 
                isSlicerFile = True

            # Construct directory string
            dirStr += "%s/%s/"%(item.text(self.columns['XNAT_LEVEL']\
                                          ['location']).strip(" "), 
                                item.text(self.columns['MERGED_LABEL']\
                                          ['location']))
            XnatDepth+=1


            
        #------------------------
        # Modify if URI has 'resources' in it.
        #------------------------
        if isResource:    

            # Append "files" if resources folder          
            if 'resources' in parents[-1].text(self.columns['XNAT_LEVEL']\
                                               ['location']).strip(" "):
                dirStr += "files" 

            # Cleanup if at files level 
            elif 'files'  in parents[-1].text(self.columns['XNAT_LEVEL']\
                                              ['location']).strip(" "):
                dirStr = dirStr[:-1]  

            # If on a files         
            else:
                dirStr =  "%s/files/%s"%(os.path.dirname(dirStr), 
                                         os.path.basename(dirStr))  

                
        #------------------------
        # Modify URI for Slicer files.
        #------------------------
        if isSlicerFile:
            dirStr = ("%s/resources/%s/files/%s"%(os.path.dirname(\
                                    os.path.dirname(os.path.dirname(dirStr))),
                                    XnatSlicerGlobals.SLICER_FOLDER_NAME,
                                    os.path.basename(\
                                                os.path.dirname(dirStr))))   

            
        #------------------------
        # For all other URIs.
        #------------------------
        elif XnatDepth < 4: 
            dirStr += Xnat.path.DEFAULT_LEVELS[XnatDepth] 

            
        return dirStr



    
    def getParents(self, item):
        """ Returns the parents of a specific treeNode 
            all the way to the "project" level
        """
        parents = []
        while(item):
          parents.insert(0, item)
          item = item.parent()
        return parents




    
    def determineExpanded(self, item):
        """Determines if the current treeItem is expanded.
        """      
        if item.childIndicatorPolicy() == 0:
            self.getChildren(item, expanded = True) 



            
    def onTreeItemExpanded(self, item):
        """ When the user interacts with the treeView, 
            this is a hook method that gets the branches 
            of a treeItem and expands them.
        """ 
        self.manageTreeNode(item, 0)
        self.setCurrentItem(item)

        if not 'files' in item.text(self.columns['XNAT_LEVEL']['location']) \
           and \
          not 'Slicer' in item.text(self.columns['XNAT_LEVEL']['location']):
            self.getChildren(item, expanded = True) 
        self.resizeColumns()


            
            
    def getChildrenNotExpanded(self, item):
        """ When the user interacts with the treeView, this 
            is a hook method that gets the branches of a treeItem 
            and does not expand them 
        """ 
        self.manageTreeNode(item, 0)
        self.setCurrentItem(item)

        if not 'files' in item.text(self.columns['XNAT_LEVEL']['location']):
            self.getChildren(item, expanded = False)



            
    def manageTreeNode(self, item, col = 0):
        """ Broad-scoped function. Conducts the necessary filtering, 
            column visibility, buttonEnabling, nodeMasking and 'loadable' 
            analysis. 
            
            NOTE: Consider refactoring into specific methods.
        """

        if not item:
            return

        #------------------------
        # Get the item level
        #------------------------
        xnatLevelColumnNumber = self.columns['XNAT_LEVEL']['location']
        itemLevel = item.text(xnatLevelColumnNumber).strip(" ")


        #------------------------
        # Set the value of 'item'
        #------------------------        
        if item == None and self.currentItem() != None:
            item = self.currentItem()
        elif item == None and self.currentItem() == None:
            return


            
        #------------------------
        # Enable load/save at the default save level
        #------------------------
        if 'experiments' in itemLevel or 'scans' in itemLevel or 'files' \
           in itemLevel or 'slicer' in itemLevel.lower():
            self.MODULE.Buttons.setEnabled('save', True)
            self.MODULE.Buttons.setEnabled('load', True)
        else:
            self.MODULE.Buttons.setEnabled('save', False)
            self.MODULE.Buttons.setEnabled('load', False)
           

        #------------------------
        # Since we can't really delete projects
        # we disable the delete button at the project level.
        #------------------------            
        if 'projects' in itemLevel:
            self.MODULE.Buttons.setEnabled('delete', False)
        else:
            self.MODULE.Buttons.setEnabled('delete', True)

        self.MODULE.Buttons.setEnabled('addFolder', True)            



        
        #------------------------
        # Resize columns.
        #------------------------
        self.resizeColumns()


        
        #------------------------
        # Selectively pull the relevant columns, based on
        # the node level to construct the dictionary that
        # feeds the 'Details' GroupBox.
        #------------------------
        detailsDict = self.getRowValues(item)  
        detailsDict['XNAT_LEVEL'] = itemLevel


        #------------------------
        # Callback
        #------------------------
        self.Events.runEventCallbacks('nodeChanged', detailsDict)

        

        
    def getXnatUriObject(self, item):    
        """ Helper function that constructs a number of useful
            key-value pairs related to a given qTreeItem, for 
            communicating with XNAT and the qTreeWidget.
        """
        pathObj = {}

        
        #-------------------------
        # Construct various URIs (current, and children)
        # based on the locaiton of the treeNode.
        #-------------------------
        pathObj['parents'] = self.getParents(item)


        
        #-------------------------
        # Get the workable xnatUri from the parents
        #-------------------------      
        xnatUri = self.getXnatUri(pathObj['parents'])
        if '/scans/' in xnatUri and '/files/' in xnatUri and xnatUri.endswith('/'):
            if not xnatUri.endswith('files/'):
                xnatUri = xnatUri[:-1]

                

        #-------------------------
        # Get the workable xnatUri from the parents
        #------------------------- 
        #print "\n\nXNAT URI", xnatUri
        pathObj['childQueryUris'] = [xnatUri + "files" if '/scans/' in xnatUri and not '/files/' in xnatUri else xnatUri]
            

        
        #-------------------------
        # Curr Uri
        #-------------------------         
        pathObj['currUri'] = os.path.dirname(pathObj['childQueryUris'][0])  
        pathObj['currLevel'] = xnatUri.split('/')[-1] if not '/scans/' \
                               in xnatUri else 'files'


        
        #------------------------
        # Construct URI dictionary by splitting the currUri from slashes.
        #------------------------
        pathObj['pathDict'] = XnatSlicerUtils.getXnatPathDict(pathObj\
                                                              ['currUri'])

            

        #-------------------------
        # Construct child Xnat level.
        #-------------------------          
        pathObj['childXnatLevel'] = os.path.basename(pathObj\
                                                     ['childQueryUris'][0])

        
        
        #-----------------------------
        # Specific key-value pairs for Slicer files...
        #-------------------------------
        if pathObj['childQueryUris'][0].endswith('/scans'):
            pathObj['slicerQueryUris'] = []
            pathObj['slicerQueryUris'].append(pathObj['currUri'] + 
                                              '/resources/Slicer/files')
            pathObj['slicerMetadataTag'] = 'Name'


        return pathObj


        
            
    def isDICOMFolder(self, item):  
        """ Probes the children of a tree item to determine if the folder
            is a DICOM folder.
        """     
        
        dicomCount = 0
        for x in range(0, item.childCount()):          
            try:
                child = item.child(x)
                if XnatSlicerUtils.isDICOM(child.text(self.columns\
                                                      ['MERGED_LABEL']\
                                                      ['location'])):
                    #print "found dicom"
                    dicomCount +=1
            except Exception as e:
                #print str(e)
                pass        
        if dicomCount == item.childCount():
                return True
        return False



    
    def setCurrItemToChild(self, item = None, childFileName = None):
        """ Scans the children a given tree item for those that have 
            'childFileName' and sets the selected qView_TreeWidget item
            to that child.  Does nothing if a child with 'childFileName' 
            is not found.
        """
        #----------------------
        # Set self.currentItem() to the item provided in the 
        # argument.
        #----------------------
        if not item:
            item = self.currentItem()    

        #----------------------
        # Expand self.currentItem()
        #----------------------
        self.onTreeItemExpanded(item)


        #----------------------
        # Search children only if 'childFileName' is not None.
        #----------------------
        if childFileName:
            for x in range(0, item.childCount()):
                child = item.child(x)
                if child.text(self.columns['MERGED_LABEL']\
                              ['location']) == childFileName:
                    self.setCurrentItem(child)
                    return   



                
    def changeFontColor(self, item, bold = True, color = "black", column = 0):
        """ As stated.
        """
        b = qt.QBrush()
        c = qt.QColor(color)
        b.setColor(c)
        item.setForeground(column, b)



        
    def startNewSession(self, sessionArgs, method="currItem"):
        """ Starts a new session based on XNAT interaction.  
        """
        if method=="currItem":            

                
            # Derive parameters based on currItem
            self.sessionManager.startNewSession(sessionArgs)




            
    def findChild(self, item, childName, expanded=True):
        """ Loops through the children of a given node
            to see if there is a string match for the childName
            argument based on the 'MERGED_LABEL' column.
        """

        ##print "childName:", childName
        if isinstance(childName, list) and len(childName) == 1:
            childName = childName[0]
        elif isinstance(childName, list) and len(childName) > 1:
            errorString = "Error: invalid 'childName' argument.  "  
            errorString +="It should be an array of length 1 or a string."
            raise Exception(MokaUtils.debug.lf() + errorString)
            ##print childName

        
        for i in range(0, item.childCount()):
            if str(childName) == item.child(i).text(\
                                    self.columns['MERGED_LABEL']['location']):
                if expanded:
                    self.onTreeItemExpanded(item.child(i))
                return item.child(i)



            
    def selectItem_byUri(self, pathStr):
        """  
        Selects a qTreeWidgetItem based on the URI.  Breaks
        down the URI and traverses the tree for th relevant strings.
        """
             
        #------------------------
        # Break apart pathStr to its Xnat categories
        #------------------------
        pathDict = XnatSlicerUtils.getXnatPathDict(pathStr)
        
        
        #------------------------
        # Reload projects if it can't find the project initially
        #------------------------
        foundProjects = self.findItems(pathDict['projects'], 1)
        

        # For Debugging...
        #MokaUtils.debug.lf("FOUND PROJECTS", foundProjects)
        #MokaUtils.debug.lf("PATH DICT1", pathStr, pathDict)
        #def _print(item):
        #    MokaUtils.debug.lf("ITEM TEXT", item.text(0))
        #self.loopProjectNodes(_print)

        if len(foundProjects) == 0: 
            #MokaUtils.debug.lf()
            self.MODULE.XnatIo.projectCache = None
            self.begin(skipAnim = True, hardReset = True)
            slicer.app.processEvents()
            foundProjects = self.findItems(pathDict['projects'], 1)
            #MokaUtils.debug.lf("FOUND PROJECTS2", foundProjects)

            
        #------------------------
        # Start by setting the current item at the project level, 
        # get its children
        #------------------------
        self.setCurrentItem(foundProjects[0])


        #------------------------
        # Proceed accordingly to its lower levels
        #------------------------
        if pathDict['subjects']:
            self.setCurrentItem(self.findChild(self.currentItem(), \
                                               pathDict['subjects']))

            #
            # If the subject isn't there or the tree isn't 
            # expanded, we recurse.
            #
            if self.currentItem() == None:
                self.setCurrentItem(foundProjects[0])
                self.onTreeItemExpanded(self.currentItem())
                self.selectItem_byUri(pathStr)
                return
                
            if pathDict['experiments']:
                self.setCurrentItem(self.findChild(self.currentItem(), \
                                                   pathDict['experiments']))
                if pathDict['scans']:
                    self.setCurrentItem(self.findChild(self.currentItem(), \
                                                       pathDict['scans']))

                    
        if pathDict['resources']:
            if pathDict['resources'] == 'Slicer':
                 self.setCurrentItem(self.findChild(self.currentItem(), \
                                                    pathDict['files']))
            else:
                self.setCurrentItem(self.findChild(self.currentItem(), \
                                                   pathDict['resources']))
                if (pathDict['files']):
                    self.setCurrentItem(self.findChild(self.currentItem(), \
                                                       pathDict['files']))





    
        
    def getChildren(self, item, expanded, setCurrItem = True):
        """ Gets the branches of a particular treeItem 
            via an XnatIo.   
        """       

        #--------------------
        # Selected Item management
        #--------------------  
        if not item: 
            return
        self.setCurrentItem(item)              


        
        #--------------------
        # Remove existing children for reload
        #--------------------
        item.takeChildren()

        
            
        #--------------------
        # Get path 
        #--------------------           
        pathObj = self.getXnatUriObject(item)
        currXnatLevel = pathObj['currLevel']

        
            
        #--------------------
        # SPECIAL CASE: this filters out image
        # folders with no images in them.
        #-------------------- 
        queryArguments = None
        if currXnatLevel == 'experiments':
            queryArguments = ['imagesonly']


                
        #--------------------
        # Get folder contents via metadata.  
        # Set nodeNames from metadata.
        #-------------------- 
        metadata = self.MODULE.XnatIo.getFolder(pathObj['childQueryUris'], 
                                                Xnat.metadata.\
                                                getTagsByLevel(currXnatLevel), \
                                                queryArguments)



        #--------------------
        # Return out of the childkeys dont exist.
        # (Means that there are no children to the 
        # node).
        #--------------------        
        xnatLabel = self.getMergedLabelTagByLevel(currXnatLevel)
        if not xnatLabel in metadata:
            ##print "NO XNAT LABEL"
            return


        
        #--------------------
        # Set the child names based on the level, metadata key
        #--------------------
        childNames = metadata[xnatLabel]

        
        
        #--------------------
        # Set the categories of the children.
        #--------------------
        metadata['XNAT_LEVEL'] = [pathObj['childXnatLevel'] \
                                  for x in range(len(childNames))]


        
        #--------------------
        # Special case for children with Slicer URIs
        #--------------------
        if 'slicerQueryUris' in pathObj:
            slicerMetadata = self.MODULE.XnatIo.\
                             getFolder(pathObj['slicerQueryUris'], \
                                       Xnat.metadata.getTagsByLevel('files'))
            #print "SLICER METADATA", slicerMetadata
            #
            # Proceed only if the relevant metadata to retrieve Slicer
            # files exists 
            #
            if self.getMergedLabelTagByLevel('files') in slicerMetadata:
                slicerChildNames = slicerMetadata[\
                                    self.getMergedLabelTagByLevel('files')]
                prevLen = len(childNames)
                childNames = childNames + slicerChildNames 
                #
                # Merge slicerMetadata with metadata
                #
                for key in slicerMetadata:
                    if not key in metadata:
                        #
                        # Set empty strings for keys that aren't shared.  
                        # For instance, Scans do not share the 'Name' key, 
                        # even though they are displayed at the same depth in 
                        # the tree hierarchy.
                        #
                        metadata[key] = [''] * prevLen
                        metadata[key] += slicerMetadata[key]

                        if (key == 'Size'):
                            for i in range(0, len(metadata[key])):
                                if metadata[key][i]:
                                    metadata[key][i] = '%i MB'%(int(round(\
                                                       MokaUtils.convert.\
                                                        bytesToMB(metadata[key]\
                                                                [i]))))
                metadata['XNAT_LEVEL'] = metadata['XNAT_LEVEL'] + \
                            ['Slicer' for x in range(len(slicerChildNames))]  
                

            
        #--------------------
        # Determine expandibility of the child node.
        #--------------------    
        expandible = []
        for i in range(0, len(metadata['XNAT_LEVEL'])):
            level = metadata['XNAT_LEVEL'][i]
            #
            # 'files' and 'Slicer' category are
            # immediately ruled as unexpandable (1).
            #
            if (level == 'files' or level == 'Slicer') :
                expandible.append(1)
            else:
                expandible.append(0)


                
        #--------------------
        # Make the treeItems
        #-------------------- 
        self.makeTreeItems(parentItem = item, children = childNames, \
                           metadata = metadata, expandible = expandible)
        item.setExpanded(True)
        self.setCurrentItem(item) 
            

        
            
    def condenseDicomsToOneName(self, names):
        """ Takes a list of DICOM files and condenses 
            them into one name.

            NOTE: Consider moving this to XnatSlicerUtils.py.
        """
        ##print("CONDENSE DICOMS")
        returnName = None
        index = 0
        for name in names:
            ##print name, XnatSlicerUtils.isDICOM(name)
            if XnatSlicerUtils.isDICOM(name) or XnatSlicerUtils.isAnalyze(name):
                returnName = name
                break
            index += 1

            ##print "RETURN", returnName, [returnName.rsplit('.',1)[0]]
        return [returnName.rsplit('.',1)[0]], index




    def getRowValues(self, item = None):
        """
        """
        if not item:
            item = self.currentItem()

        rowValues = None
        if item:
            rowValues = {}
            for tag in self.columns:
                if 'location' in self.columns[tag]:
                    rowValues[tag] = item.text(self.columns[tag]['location']).\
                                     strip(' ')


        return rowValues



    
    def refreshColumns(self):
        """
        """

        ##print MokaUtils.debug.lf(), "REFRESH COLUMNS"
        #--------------------
        # Reset the the 'currentItem' so that
        # the appropriate events can get called.
        #--------------------
        currItem = self.currentItem()
        self.clearSelection()
        self.setCurrentItem(None)
        self.setCurrentItem(currItem)

        rowVals = self.getRowValues()
        if rowVals:
            self.Events.runEventCallbacks('nodeChanged', rowVals)

        

        #--------------------
        # Refresh all of the column values in the 
        # visible nodes.
        #--------------------
        self.loopVisible(self.populateColumns)




    def setDefaultFonts(self):
        """ 
        Restores the default fonts described
        in the 'populateColumns' method by calling
        on 'populateColumns.'  This method is called on 
        after the user clears the search field and the highlighted
        tree nodes that meet the serach criteria need to be
        unhighlighted.
        """
        ##print self.browser.utils.lf(), "Begin"
        root = self.invisibleRootItem()
        childCount = root.childCount()
        for i in range(childCount):
            item = root.child(i)
            ##print '\n\n\n', item.text()
            self.populateColumns(item)
            self.Events.runEventCallbacks('nodeChanged', self.getRowValues())

            
    
    
    def makeTreeItems(self, parentItem = None, children = [],  metadata = {}, 
                      expandible = None):
        """
        Creates a set of items to be put into the 
        QTreeWidget based upon its parents, its children 
        and the metadata provide.
        """

        
        
        #----------------
        # Do nothing if no children.
        #----------------
        if len(children) == 0: return


        
        #----------------
        # Convert string children to arrays
        #----------------       
        if isinstance(children, str):
            children = [children]


            
        #----------------
        # convert string expandible to array
        #----------------
        if isinstance(expandible, int):
            expandible = [expandible]

            
            
        #----------------
        # Get the DICOM count if at 'scans' level
        #----------------
        condensed = False
        childIndex = -1
        if (metadata['XNAT_LEVEL'][0] == 'files'):
            pathObj = self.getXnatUriObject(parentItem.parent())
            parentXnatLevel = pathObj['currLevel']
            if parentXnatLevel == 'scans':
                if self.isDICOMFolder(parentItem):                
                    children, childIndex = \
                                self.condenseDicomsToOneName(children)
                    ##print "CHILDREN", children
                    condensed = True
                    
        
        
        #------------------------
        # Add children to parentItem
        #------------------------
        treeItems = []
        for i in range(0, len(children)):
            ##print "\n\nCHILDREN: ", children[i]

            
            treeNode = qt.QTreeWidgetItem(parentItem)
            #
            # Set expanded (0 = expandable, 1 = not)
            #
            expandPolicy = 0
            if metadata['XNAT_LEVEL'][i] == 'files' \
               or metadata['XNAT_LEVEL'][i] == 'Slicer':
                expandPolicy = 1
            treeNode.setChildIndicatorPolicy(expandPolicy)   
            #
            # Set other metadata
            #
            treeNodeMetadata = {}
            for key in metadata:
                #MokaUtils.debug.lf('\n\n', key, i, len(metadata[key]), 
                #             metadata, len(children), children)
                if i < len(metadata[key]):
                    treeNodeMetadata[key] = metadata[key][i]
                if childIndex > -1:
                    treeNodeMetadata[key] = metadata[key][childIndex]
                    #MokaUtils.debug.lf("\n\nTREE NODE METADATA", \
                    # treeNodeMetadata)

            #
            # Register the condensed tree node name, if it's there.
            #
            #MokaUtils.debug.lf("\n\nTREE NODE METADATA2", treeNodeMetadata,\
            # condensed)
                
            treeNode = self.populateColumns(treeNode, treeNodeMetadata)
            #
            # Add the items array
            #
            if treeNode:
                treeNode.setFlags(1 | 4 | 8 | 32)
                treeItems.append(treeNode) 


                
        #------------------------    
        # SPECIAL CASE: If at project level, set parents accordingly.
        #------------------------
        if str(parentItem.__class__) == "<class 'View_Tree.View_Tree'>":
            parentItem.addTopLevelItems(treeItems)
            return
        

        
        #------------------------    
        # Items array gets added to parentItem.
        #------------------------
        parentItem.addChildren(treeItems)





            
        
    def searchEntered(self):
        """
            
        Qt::MatchExactly	0	Performs QVariant-based matching.

        Qt::MatchFixedString	8	Performs string-based matching. 
                                        String-based comparisons are 
                                        case-insensitive unless the 
                                        MatchCaseSensitive flag is also 
                                        specified.

        Qt::MatchContains	1	The search term is contained in the 
                                        item.

        Qt::MatchStartsWith	2	The search term matches the start of 
                                        the item.

        Qt::MatchEndsWith	3	The search term matches the end of the 
                                        item.

        Qt::MatchCaseSensitive	16	The search is case sensitive.

        Qt::MatchRegExp	        4	Performs string-based matching using a 
                                        regular expression as the search term.

        Qt::MatchWildcard	5	Performs string-based matching using a 
                                        string with wildcards as the search 
                                        term.

        Qt::MatchWrap	        32	Perform a search that wraps around, 
                                        so that when the search reaches the 
                                        last item in the model, it begins again
                                        at the first item and continues until 
                                        all items have been examined.

        Qt::MatchRecursive	64	Searches the entire hierarchy.
        """

        ##print MokaUtils.debug.lf(), "Disconnecting item expanded."
        self.disconnect("itemExpanded(QTreeWidgetItem *)", \
                        self.onTreeItemExpanded)
        #SEARCH_TIMER = Timer(self.MODULE)


        
        #------------------------
        # Deslect any selected items.
        #------------------------  
        for selectedItem in self.selectedItems():
            selectedItem.setSelected(False)


            
        #------------------------
        # Get searchString from MODULE.  Remove starting 
        # and ending white spaces via '.strip()'
        #------------------------
        searchString = self.MODULE.SearchBar.getText()


        
        #------------------------
        # Return out if searchString is all
        # white spaces. 
        # NOTE: .strip() is called on it above.
        #------------------------
        if len(searchString) == 0:
            return


        
        #------------------------
        # Set all visible if searchString == ''
        # and return out.
        #------------------------
        if len(searchString) == 0:
            def showAll(child):
                child.setHidden(False)
            self.loopProjectNodes(showAll)  
            return          
            
        
        
        #------------------------
        # Search existing tree items
        #------------------------
        #SEARCH_TIMER.start("Search existing", "search exist")
        self.searchTreeItems = self.searchAndShowExisting(searchString)
        #SEARCH_TIMER.stop()


        
        
        #------------------------
        # First pass: Hide all items that don't
        # fit the search criteria.
        #------------------------
        def hideEqual(child):
            if child in self.searchTreeItems:
                child.setHidden(False)
            else:
                child.setHidden(True)
        self.loopProjectNodes(hideEqual)

        

        #------------------------
        # Second pass: Re-show any ancestor nodes of the 
        # search nodes.
        #------------------------
        #SEARCH_TIMER.start("Reshow ancestors")
        for searchTreeItem in self.searchTreeItems:
            #
            # Get parent
            #
            parent = searchTreeItem.parent()
            while parent:
                #
                # Show parent
                #
                parent.setHidden(False)
                #
                # Expand the ancestor
                #
                parent.setExpanded(True)
                parent = parent.parent()

                #SEARCH_TIMER.stop()
                





        #**************************************************************
        #
        #              CONDUCT SEARCH ON SERVER
        #
        #**************************************************************


        
        #------------------------
        # Run the search method in the
        # XnatIo.
        #------------------------
        #SEARCH_TIMER.start("Server search")
        serverQueryResults = self.MODULE.XnatIo.search(searchString)
        #SEARCH_TIMER.stop()

        

        #------------------------
        # Establish searchable levels: 
        # projects, subjects and experiments
        #------------------------
        levels = ['projects', 'subjects', 'experiments']



        #------------------------
        # Cycle through search query results by level
        #------------------------       
        for level in levels:
            for serverQueryResult in serverQueryResults[level]:

                
                #-------------------
                # Create the item in the tree (i.e. the 
                # user hasn't browsed there yet).  This node will never
                # be a project, because projects that have met the search
                # criteria are shown above.
                #-------------------
                if level != 'projects':
                    
                    #
                    # Get the 'project' of the node and make sure it's visible.
                    # The project folder of every subject and experiment are
                    # provided in the metadata json from REST get calls.
                    #
                    #SEARCH_TIMER.start("Getting projects after server query.")
                    project = self.findItems(serverQueryResult['project'], \
                                        1 , self.columns['ID']['location'])[0]
                    #
                    # Show the ancestor 'project'.
                    #
                    project.setHidden(False)
                    #
                    # Expand the ancestor 'project' (events are disabled, so
                    # there's no querying happening).
                    #
                    project.setExpanded(True)
                    #SEARCH_TIMER.stop()
                    
                    #
                    # Get MERGED_LABEL tag.
                    # 
                    mergedLabel = self.getMergedLabelTagByLevel(level)
                    
                    #
                    # Construct metadata dictionary.
                    #
                    metadata = {}
                    for key in serverQueryResult:
                        metadata[key] = [serverQueryResult[key]]  

                        
                    #
                    # Construct the custom/merged columns.
                    #
                    metadata['XNAT_LEVEL'] = [level]
                    metadata['MERGED_LABEL'] = [serverQueryResult[mergedLabel]]
                    metadata['MERGED_INFO'] = [mergedLabel]


                    
                    #--------------------
                    # Make 'subject' items that match the search 
                    # criteria. 
                    #--------------------
                    if level == 'subjects':
                        #
                        # Make the child items of the project, which 
                        # will be the subject nodes.
                        #
                        self.makeTreeItems(parentItem = project, \
                                    children = serverQueryResult[mergedLabel],\
                                    metadata = metadata, expandible = [0])
                        #
                        # Find the child nodes in the tree.
                        #
                        project.setExpanded(True)


                        
                    #--------------------
                    # Make 'experiment' items that match the search 
                    # criteria. 
                    #--------------------
                    elif level == 'experiments':
                        
                        #
                        # Construct necessary metadata dictionary
                        # for the parent 'subject'.
                        #
                        experimentName = metadata['MERGED_LABEL']
                        subjectLabel = metadata['subject_label']
                        subjectMetadata = {}
                        subjectMetadata['XNAT_LEVEL'] = ['subjects']
                        subjectMetadata['MERGED_LABEL'] = subjectLabel
                        subjectMetadata['MERGED_INFO'] = ['Info']
                        subjectMetadata['ID'] = metadata['subject_ID']
                        subjectMetadata['label'] = subjectLabel
                        
                        #
                        # Check if the 'subject' is already a child
                        # of the 'project'.  This happens as a result of 
                        # the 'makeTreeItems'
                        # line below being called, and subsequent experiments 
                        # being created.
                        #
                        subject = self.findItems(\
                                    serverQueryResult['subject_ID'], \
                                    1 | 64 , self.columns['ID']['location'])
                        if len(subject) > 0:
                            subject = subject[0]
                            
                        #
                        # If the parent 'subject' doesn't exist, make the parent
                        # 'subject' a child of the 'project'.
                        #
                        if not subject:
                            self.makeTreeItems(parentItem = project, \
                                               children = [subjectLabel], \
                                               metadata = subjectMetadata, \
                                               expandible = [0])
                            subject = self.findItems(\
                                        serverQueryResult['subject_label'], \
                                        1 | 64 , self.columns['MERGED_LABEL']\
                                                     ['location'])[0]
                            subject.setHidden(False)
                            
                        #
                        # Make 'experiment' as child of parent 'subject' 
                        # if it doesn't exist.
                        #
                        item = self.findChild(subject, experimentName)
                        #MokaUtils.debug.lf("\t\t*************FIND CHILD: ", \
                        #subject.text(0), experimentName, item)
                        if not item:
                            self.makeTreeItems(parentItem = subject, 
                                               children = experimentName, 
                                               metadata = metadata, 
                                               expandible = [0]) 
                        
                        #
                        # Expand the parent 'subject'.
                        # 
                        subject.setExpanded(True)   
                        

        #
        # Highlight all nodes that meet the search
        # criteria.
        #
        items = self.searchAndShowExisting(searchString)



        #
        # For no results found...
        #       
        if len(items) == 0:
            self.MODULE.Viewer.noSearchResultsFound.setText(\
                                    "No results for '%s'."%(searchString))
            self.MODULE.Viewer.setNoResultsWidgetVisible(True)
        else:
            self.MODULE.Viewer.setNoResultsWidgetVisible(False)


            
        #
        # Reconnect the event listeners for expandning
        # the QTreeWidgetItems.
        #
        ##print MokaUtils.debug.lf(), "Re-connecting item expanded."
        self.connect("itemExpanded(QTreeWidgetItem *)", self.onTreeItemExpanded)
        self.resizeColumns()

    
        

    def searchAndShowExisting(self, searchString):
        """ Searches through all columns using 'Qt::MatchContains'
            for a match.  Highlights and selects treeItems that
            match.
        """

        #--------------------
        # Get the items that match the string
        # by looking through every column and
        # every node. columns * O(n) at least.
        #--------------------
        items = []
        for columnNumber in range(0, self.columnCount):
            results = self.findItems(searchString, 1 | 64 , columnNumber)
            if results:
                #
                # 'results' is returned as a tuple, so
                # we cannot simply add the array.
                #
                for result in results:
                    items.append(result)



        #--------------------
        # If the items are found
        #--------------------
        if len(items) > 0:
            for item in items:
                #
                # Make the tree node bold.
                #                     
                item.setFont(0, self.itemFonts['searchHighlight'])
                self.changeFontColor(item, False, 'blue', 0)
                #
                # If the node his hidden...
                #
                if item.isHidden():
                    #
                    # Show the item
                    #
                    item.setHidden(False)

                #
                # Show the parents if it's not a 'project'
                #
                parent = item.parent()
                while parent:
                    parent.setHidden(False)
                    parent.setExpanded(True)
                    parent = parent.parent()

            
        self.resizeColumns()
        return items
        

    

