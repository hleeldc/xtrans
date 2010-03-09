from PyQt4 import QtGui
from at4 import *
from keyseqinputdialog import *
from config import config_default

__all__ = ["KeyBindingDialog", "FreeStringKeyBindingDialog"]


class KeyBindingDialog(QtGui.QDialog):
    def __init__(self, config, config_description, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.config = config
        self.config_description = config_description
        
        self.setWindowTitle("Key Binding Editor")
        
        L = [[("binding",unicode),("key",unicode),("description",unicode)]]
        bindings = filter(lambda x:x[0][:3]=='KB_', config.items())
        bindings.sort()
        for k,v in bindings:
            L.append([k,v,config_description[k]])
        tab = TableModel.importList(L)
        te = TableEdit(self)
        te.setData(tab)
        
        #te.setColumnReadOnly(0,True)
        #te.setColumnReadOnly(1,True)
        #te.setColumnReadOnly(2,True)
        #te.setColumnStretchable(0,True)
        #te.setColumnStretchable(1,True)
        #te.setColumnStretchable(2,True)
        
        btnEdit = QtGui.QPushButton("&Edit", self)
        btnReset = QtGui.QPushButton("&Reset", self)
        btnResetAll = QtGui.QPushButton("Re&set all", self)
        btnDefault = QtGui.QPushButton("&Default", self)
        btnDefaultAll = QtGui.QPushButton("De&fault all", self)
        btnOkay = QtGui.QPushButton("&OK", self)
        btnCancel = QtGui.QPushButton("&Cancel", self)

        vbox = QtGui.QVBoxLayout(self)
        buttons = QtGui.QHBoxLayout()
        buttons2 = QtGui.QHBoxLayout()
        vbox.addWidget(te)
        vbox.addLayout(buttons)
        vbox.addLayout(buttons2)
        buttons.addWidget(btnEdit)
        buttons.addWidget(btnReset)
        buttons.addWidget(btnResetAll)
        buttons.addWidget(btnDefault)
        buttons.addWidget(btnDefaultAll)
        buttons2.addStretch()
        buttons2.addWidget(btnOkay)
        buttons2.addWidget(btnCancel)
        buttons2.addStretch()
        
        buttons.setSpacing(2)
        buttons.setMargin(2)
        buttons2.setSpacing(20)
        buttons2.setMargin(10)

        self.connect(te, QtCore.SIGNAL("clicked(int,int,int,const QPoint&)"),
                     self._edit)
        self.connect(btnEdit, QtCore.SIGNAL("clicked()"), self._edit)
        self.connect(btnReset, QtCore.SIGNAL("clicked()"), self._reset)
        self.connect(btnResetAll, QtCore.SIGNAL("clicked()"), self._resetAll)
        self.connect(btnDefault, QtCore.SIGNAL("clicked()"), self._default)
        self.connect(btnDefaultAll, QtCore.SIGNAL("clicked()"), self._defaultAll)
        self.connect(btnOkay, QtCore.SIGNAL("clicked()"), self._okay)
        self.connect(btnCancel, QtCore.SIGNAL("clicked()"), self._cancel)
        
        self.changes = {}
        self.data = tab
        self.backup = tab.toList()
        self.table = te

    def _edit(self, *args):
        if args:
            # invoked by clicking on a cell
            row, col, btn, point = args
        else:
            row = self.table.currentRow()
            col = self.table.currentColumn()
        h = self.config.copy()
        h.update(self.changes)
        d = KeySeqInputDialog(h.values(), self.data[row][1], self)
        if d.exec_():
            seq = d.asString()
            if seq:
                self.changes[self.data[row][0]] = seq
                self.backup[row][1] = seq
                self.data[row][1] = seq        
        
    def _reset(self):
        i = self.table.currentRow()
        if i is not None:
            row = self.data[i]
            k = row[0]
            v = self.config.rawValue(k)
            row[1] = v
            self.backup[i][1] = v
            if k in self.changes:
                del self.changes[k]
            
    def _resetAll(self):
        for row in self.data:
            row[1] = self.config.rawValue(row[0])
        self.changes = {}
        self.backup = self.data.toList()
        
    def _default(self):
        i = self.table.currentRow()
        if i is not None:
            row = self.data[i]
            k = row[0]
            v = config_default.rawValue(k)
            row[1] = v
            self.backup[i][1] = v
            if self.config[k] != config_default[k]:
                self.changes[k] = v
            elif k in self.changes:
                del self.changes[k]
                
    def _defaultAll(self):
        for row in self.data:
            k = row[0]
            v = config_default.rawValue(k)
            row[1] = v
            if self.config[k] != config_default[k]:
                self.changes[k] = v
            elif k in self.changes:
                del self.changes[k]
        self.backup = self.data.toList()

    def _okay(self):
        for k,v in self.changes.items():
            self.config[k] = v
        self.done(self.Accepted)

    def _cancel(self):
        self.done(self.Rejected)
        


class FreeStringKeyBindingDialog(QtGui.QDialog):
    def __init__(self, config, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.config = config
        
        self.setWindowTitle("Key Binding Editor")
        
        L = [[("key",unicode),("string",unicode)]]
        bindings = filter(lambda x:x[0].startswith('FSKB_'), config.items())
        self.orgConfig = {}
        for name,rawval in bindings:
            try:
                seq, s = eval(rawval)
            except Exception, e:
                print "WARNING: can't read configuration:", name
                print "WARNING:", e
                continue
            self.orgConfig[name] = rawval
            del self.config[name]
            self.config[self._configName(seq)] = rawval
            L.append([seq,s])

        tab = TableModel.importList(L)
        te = TableEdit(self)
        te.setData(tab)
        #te.setColumnReadOnly(0,True)
        #te.setColumnStretchable(1,True)
        #te.setColumnWidth(0, 120)
        #te.setColumnWidth(1, 240)
        
        btnAdd = QtGui.QPushButton("&Add", self)
        btnEdit = QtGui.QPushButton("&Edit", self)
        btnRemove = QtGui.QPushButton("&Remove", self)
        btnOkay = QtGui.QPushButton("&OK", self)
        btnCancel = QtGui.QPushButton("&Cancel", self)

        vbox = QtGui.QVBoxLayout(self)
        buttons = QtGui.QHBoxLayout()
        buttons2 = QtGui.QHBoxLayout()
        vbox.addWidget(te)
        vbox.addLayout(buttons)
        vbox.addLayout(buttons2)
        buttons.addWidget(btnAdd)
        buttons.addWidget(btnEdit)
        buttons.addWidget(btnRemove)
        buttons2.addStretch()
        buttons2.addWidget(btnOkay)
        buttons2.addWidget(btnCancel)
        buttons2.addStretch()
        
        buttons.setSpacing(2)
        buttons.setMargin(2)
        buttons2.setSpacing(20)
        buttons2.setMargin(10)

        self.connect(tab.emitter, QtCore.SIGNAL("cellChanged"), self._cellChanged)
        self.connect(te, QtCore.SIGNAL("clicked(int,int,int,const QPoint&)"),
                     self._edit)
        self.connect(btnAdd, QtCore.SIGNAL("clicked()"), self._add)
        self.connect(btnRemove, QtCore.SIGNAL("clicked()"), self._remove)
        self.connect(btnEdit, QtCore.SIGNAL("clicked()"), self._edit)
        self.connect(btnOkay, QtCore.SIGNAL("clicked()"), self._okay)
        self.connect(btnCancel, QtCore.SIGNAL("clicked()"), self._cancel)
        
        self.data = tab
        self.table = te

    def keyBindings(self):
        h = {}
        for r in self.data:
            h[r[0]] = r[1]
        return h

    def _configName(self, seq):
        return "FSKB_" + str2objname(seq)
    
    def _cellChanged(self, i, c, v, w):
        seq = self.data[i][0]
        self.config[self._configName(seq)] = str((seq,v))

    def _add(self, *args):
        d = KeySeqInputDialog(self._stoplist(), parent=self)
        if d.exec_():
            seq = d.asString()
            if seq:
                row = self.table.currentRow()
                row += 1
                self.data.insertRow(row, [seq,"<string>"])
                self.config[self._configName(seq)] = str((seq,"<string>"))
    
    def _remove(self, *args):
        row = self.table.currentRow()
        row = self.data.takeRow(row)
        del self.config[self._configName(row[0])]
        
    def _edit(self, *args):
        if args:
            # invoked by clicking on a cell
            row, col, btn, point = args
        else:
            row = self.table.currentRow()
            col = self.table.currentColumn()
        if col != 0: return
        d = KeySeqInputDialog(self._stoplist(), self.data[row][col], self)
        if d.exec_():
            seq = d.asString()
            if seq:
                r = self.data[row]
                cfgnam = self._configName(r[0])
                del self.config[cfgnam]
                r[0] = seq
                self.config[self._configName(seq)] = str(tuple(r))
                
    def _okay(self):
        self.done(self.Accepted)

    def _cancel(self):
        bindings = filter(lambda x:x[0].startswith('FSKB_'), self.config.items())
        for name,rawval in bindings:
            del self.config[name]
        for name,rawval in self.orgConfig.items():
            self.config[name] = rawval
        self.done(self.Rejected)
        
    def _stoplist(self):
        return self.config.values() + [x[0] for x in self.data]
