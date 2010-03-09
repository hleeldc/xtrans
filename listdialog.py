from PyQt4 import QtGui
from PyQt4 import QtCore

__all__ = ["ListDialog"]

class ListDialog(QtGui.QDialog):
    def __init__(self, lst, parent=None, name=None,
                 wflag=QtCore.Qt.Dialog,
                 caption=None,
                 description=None,
                 buttonLabel=None,
                 multiChoice=True,
                 defaultChoices=[]):
        QtGui.QDialog.__init__(self, parent, wflag)

        if caption:
            self.setWindowTitle(caption)

        l = QtGui.QListWidget(self)
        if multiChoice:
            l.setSelectionMode(l.MultiSelection)
        for i,item in enumerate(lst):
            if item is None:
                l.addItem("- None -")
            else:
                l.addItem(item)
                if item in defaultChoices:
                    l.setCurrentRow(i)
                    
        btnOk = QtGui.QPushButton("OK", self)
        btnCancel = QtGui.QPushButton("Cancel", self)

        g = None
        if description is not None:
            g = QtGui.QGroupBox(self)
            gl = QtGui.QVBoxLayout(g)
            gl.addWidget(QtGui.QLabel(description,g))

        layout = QtGui.QVBoxLayout(self)
        if g: layout.addWidget(g)
        layout.addWidget(l)
        buttons = QtGui.QHBoxLayout()
        layout.addLayout(buttons)
        buttons.addWidget(btnOk)
        buttons.addWidget(btnCancel)
        
        buttons.setSpacing(10)
        buttons.setMargin(10)

        btnOk.clicked.connect(self._ok)
        btnCancel.clicked.connect(self._cancel)
        self.listbox = l

    def getSelectedItems(self):
        r = []
        for item in self.listbox.selectedItems():
            v = unicode(item.text())
            if v == '- None -': v=None
            r.append(v)
        return r
    
    def _ok(self):
        self.done(self.Accepted)
        
    def _cancel(self):
        self.listbox.clearSelection()
        self.done(self.Rejected)
