"""
@author: `@parkin`_
"""
import os.path

from PySide import QtGui


class FileListItem(QtGui.QListWidgetItem):
    """
    Subclass of QListWidgetItem to handle file names with long file paths.
    """
    
    def __init__(self, filename):
        words = os.path.split(filename)
        self.simple_name = words[1]
        super(FileListItem, self).__init__(self.simple_name)
        self.file_name = filename
        self.directory = words[0]
        
    def get_file_name(self):
        """
        :returns: StringType -- the file names with the file path included.
                    ex /home/user/.../filename
        """
        return self.file_name
    
    def get_simple_name(self):
        """
        :returns: StringType -- the file name without the file path included.
        """
        return self.simple_name
    
    def get_directory(self):
        """
        :returns: StringType -- the directory containing the file.
        """
        return self.directory

    
class DataFileListItem(FileListItem):
    """
    Is a FileListItem with a parameter.
    """
    
    def __init__(self, filename, params):
        FileListItem.__init__(self, filename)
        self.params = params
        
    def get_params(self):
        """
        :returns: DictType -- Dictionary of the item's parameters.
        """
        return dict(self.params)
    
    def get_param(self, param):
        """
        :param param: Key in the parameter dictionary, whose value should be returned.
        :returns: Parameter value specified by the key 'param'.
        """
        if param in self.params:
            return self.params[param]
        else:
            return None


class FilterListItem(QtGui.QListWidgetItem):
    """
    Subclass of QListWidgetItem to handle filter list items.
    
    self.params contain the filter parameters specified by the user.
    """
    def __init__(self, file_names, **params):
        """
        :param ListType<String> file_names: File names that define this FilterListItem.
        :param params: A dictionary of the parameters for this FilterListItem.
        """
        self.file_names = file_names
        self.simple_names = []
        item_text = 'item'
        if len(file_names) > 0:
            item_text = ''
        index = 0
        for filename in file_names:
            words = os.path.split(filename)
            simple_name = words[1]
            item_text += simple_name
            self.simple_names.append(simple_name)
            index += 1
            # don't append ', ' to last item
            if index < len(file_names):
                item_text += ', '
        super(FilterListItem, self).__init__(item_text)
        self.params = params
        if not 'color' in params:
            # give the item a default color
            self.params['color'] = QtGui.QColor.fromRgbF(0., 0., 1.)
        # set the icon color
#         self.setForeground(params['color'])
        pix_map = QtGui.QPixmap(20, 20)
        pix_map.fill(self.params['color'])
        self.setIcon(QtGui.QIcon(pix_map))
        
    def get_params(self):
        """
        :returns: Dict -- dictionary of the parameters of this Item.
        """
        return dict(self.params)
    
    def get_file_names(self):
        """
        :returns: List -- list of the full file names of the files that make up this Item.
        """
        return list(self.file_names)
    
    def get_file_name_at(self, index):
        """
        :param IntType index: Position of the item.
        :returns: String -- Full filename (including path) of the file at index.
        """
        if 0 <= index < len(self.file_names):
            return self.file_names[index]
        else:
            return None
    
    def get_simple_names(self):
        """
        :returns: List -- list of the simple names (no path/directory) of the files that make up this Item.
        """
        return list(self.simple_names)
    
    def get_simple_name_at(self, index):
        """
        :param IntType index: Index of the list item to get the simple name of.
        :returns: String -- Simple name (i.e. no path/directory) of the file at index.
        """
        if 0 <= index < len(self.file_names):
            return self.simple_names[index]
        else:
            return None
