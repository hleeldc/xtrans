from PyQt4 import QtGui

class SmallButton(QtGui.QPushButton):
    def __init__(self, label, parent=None):
        QtGui.QPushButton.__init__(self, label, parent)
        f = self.font()
        f.setPointSize(10)
        self.setFont(f)
        self.setFixedHeight(20)
        self.setFixedWidth(40)
