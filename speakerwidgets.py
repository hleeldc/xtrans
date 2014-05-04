from PyQt4 import QtCore
from PyQt4 import QtGui
from config import config
import re
import sip

__all__ = ["SpeakerInfoDialog", "SpeakerSelectionPanel"]

class SpeakerInfoDialog(QtGui.QDialog):
    def __init__(self, data, spkrs, parent=None):
        """
        @param data: Transcript
        """
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Speaker Info Editor")

        # compute the next anonymous speaker id
        if spkrs:
            l = []
            for spkr in spkrs:
                if spkr is not None:
                    m = re.match("^speaker([0-9]+)$", spkr)
                    if m:
                        l.append(int(m.group(1)))
            if l:
                l.sort()
                if l[0] != 1:
                    a = 1
                else:
                    a = 1
                    for b in l:
                        if b > a:
                            break
                        else:
                            a = b+1
            else:
                a = 1
        else:
            a = 1
        self.anonSpkrId = a
        
        lblSpkrId = QtGui.QLabel("Speaker ID", self)
        ledSpkrId = QtGui.QLineEdit("speaker%d"%self.anonSpkrId, self)
        btnAnon = QtGui.QPushButton("&New", self)
        lblSpkrType = QtGui.QLabel("Speaker Type", self)
        cmbSpkrType = QtGui.QComboBox(self)
        lblSpkrDialect = QtGui.QLabel("Speaker Dialect", self)
        cmbSpkrDialect = QtGui.QComboBox(self)

        btnOk = QtGui.QPushButton("&OK", self)
        btnCancel = QtGui.QPushButton("&Cancel", self)

        layout = QtGui.QVBoxLayout(self)
        grid = QtGui.QGridLayout()
        hbox = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()
        layout.addLayout(grid)
        layout.addLayout(hbox2)
        grid.addWidget(lblSpkrId, 0, 0)
        grid.addLayout(hbox, 0, 1)
        hbox.addWidget(ledSpkrId)
        hbox.addWidget(btnAnon)
        grid.addWidget(lblSpkrType, 1, 0)
        grid.addWidget(cmbSpkrType, 1, 1)
        grid.addWidget(lblSpkrDialect, 2, 0)
        grid.addWidget(cmbSpkrDialect, 2, 1)
        hbox2.addWidget(btnOk)
        hbox2.addWidget(btnCancel)

        layout.setSpacing(10)
        #layout.setMargin(10)
        grid.setSpacing(5)
        grid.setMargin(10)
        hbox2.setSpacing(15)
        hbox2.setMargin(10)
        ledSpkrId.setMinimumWidth(150)

        cmbSpkrType.addItems(["unknown","child","female","male"])
        cmbSpkrDialect.addItems(["native","other"])

        btnOk.clicked.connect(self._ok)
        btnCancel.clicked.connect(self._cancel)
        btnAnon.clicked.connect(self._setAnonSpkrId)
        ledSpkrId.textChanged.connect(self._textChanged)

        self._accepted = False
        self.ledSpkrId = ledSpkrId
        self.cmbSpkrType = cmbSpkrType
        self.cmbSpkrDialect = cmbSpkrDialect
        self.data = data
        self.orgSpkr = None
        self.spkrIsNone = False

        #self.connect(ledSpkrId, SIGNAL("textChanged(const QString&)"),
        #             self._textChanged)

        btnOk.setFocus()
        
    def _ok(self):
        spkr = self.ledSpkrId.text()
        if len(spkr) == 0:
            QtGui.QMessageBox.critical(
                self, "Speaker ID Error",
                "Speaker ID shouldn't be an empty string.",
                "OK")
            return
        elif spkr != self.orgSpkr:
            for row in self.data:
                if row['speaker'] == spkr:
                    QtGui.QMessageBox.critical(
                        self, "Speaker ID Error",
                        "Speaker ID is not unique.",
                        "OK")
                    return
        self._accepted = True
        self.accept()

    def _cancel(self):
        self._accepted = False
        self.reject()

    def _setAnonSpkrId(self):
        self.ledSpkrId.setText("speaker%d" % self.anonSpkrId)
        
    def _textChanged(self, s):
        if self.spkrIsNone:
            self.spkrIsNone = False

    def setSpeakerTypeComboDisabled(self,v):
        self.cmbSpkrType.setDisabled(v)

    def setSpeakerDialectComboDisabled(self,v):
        self.cmbSpkrDialect.setDisabled(v)
    
    def setInfo(self, spkr, typ, dialect):
        self.orgSpkr = spkr
        if spkr is None:
            spkr='None'
            self.spkrIsNone = True
        self.ledSpkrId.setText(spkr)
        for i in range(self.cmbSpkrType.count()):
            if self.cmbSpkrType.itemText(i) == typ:
                self.cmbSpkrType.setCurrentIndex(i)
                break
        else:
            # FIXME: new speaker type found. what are you gonna do?
            self.cmbSpkrType.setCurrentIndex(0)
        
        for i in range(self.cmbSpkrDialect.count()):
            if self.cmbSpkrDialect.itemText(i) == dialect:
                self.cmbSpkrDialect.setCurrentIndex(i)
                break
        else:
            # FIXME: new speaker type found. what are you gonna do?
            self.cmbSpkrDialect.setCurrentIndex(1)
            
    def getValues(self):
        if self._accepted:
            if self.spkrIsNone:
                spkr = None
            else:
                spkr = unicode(self.ledSpkrId.text())
            return (spkr,
                    unicode(self.cmbSpkrType.currentText()),
                    unicode(self.cmbSpkrDialect.currentText()))
        else:
            return None

class SpeakerSelectionPanel(QtGui.QScrollArea):
    def __init__(self, colorMap=lambda x:Qt.white, parent=None):
        """
        """
        QtGui.QScrollArea.__init__(self, parent)
        #self.setResizePolicy(self.AutoOneFit)
        self.colorMap = colorMap
        self.bgpSpkrs = QtGui.QButtonGroup(self)
        self.data = None
        self.btn2spkr = {}
        self.spkr2btn = {}
        self.spkrs = {} # spkr_id:[spkr_id, start_time, count, segment_sample]
        self.selectedSpeaker = None
        self.sortBySpeaker = False
        self.setWidgetResizable(True)
        self.setWidget(QtGui.QWidget(self))
        self.hbox = QtGui.QVBoxLayout(self.widget())

    def toggleSorting(self):
        self.sortBySpeaker = not self.sortBySpeaker
        self._display()
        
    def setData(self, data, filter=lambda x:True):
        """
        Scan transcript to obtain a list of speakers and information
        about them.
        
        @param data: Transcript object.
        @param filter: Callable returning a boolean for a segment. Only the
        segments that result a True value are considered. Segment is a row in
        a Transcript object. 
        """
        h = {}
        for row in data:
            if not filter(row): continue 
            spkr = row['speaker']
            if spkr in h:
                h[spkr][2] += 1
                continue
            h[spkr] = [spkr,row['start'],1,row]
        try:
            del h[config['sectionSpeakerId']]
        except KeyError:
            pass
        self.spkrs = h
        
        self.selectedSpeaker = None
        self._display()

        if data != self.data:
            self.connect(data.emitter,QtCore.SIGNAL("takeRow"),self._takeRow)
            self.connect(data.emitter,QtCore.SIGNAL("insertRow"),self._insertRow)
            self.connect(data.emitter,QtCore.SIGNAL("cellChanged"),self._cellChanged)
            self.data = data

    def getSpeakers(self):
        """
        @return: A list of speaker IDs.
        """
        return self.spkrs.keys()
    
    def _getSpeakerList(self):
        """
        @return: A sorted list of speaker IDs.
        """
        spkrs = self.spkrs.values()
        if self.sortBySpeaker:
            spkrs.sort(lambda a,b:cmp(a[0],b[0]))
        else: # sort by start time
            spkrs.sort(lambda a,b:cmp(a[1],b[1]))
        return [a[0] for a in spkrs]
            
    def _display(self):
        """
        Rebuild the speaker panel from scratch. Existing buttons and stuff
        will be destroyed before new ones are created.
        """

        self.btn2spkr = {}
        self.spkr2btn = {}
        sip.delete(self.widget())
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        buttonGroup = QtGui.QButtonGroup(widget)
        buttonGroup.buttonClicked.connect(self._setSelectedSpeaker)
        for spkr in self._getSpeakerList():
            if spkr is None:
                label = 'None'
            else:
                label = self._speakerInfoString(spkr)
            button = QtGui.QRadioButton(label, widget)
            if self.selectedSpeaker == spkr: button.setChecked(True)
            buttonGroup.addButton(button)
            self.btn2spkr[button] = self.spkrs[spkr][-1]
            self.spkr2btn[spkr] = button
            color = self.colorMap(spkr)
            palette = button.palette()
            palette.setColor(QtGui.QPalette.Button, QtGui.QColor(color))
            button.setPalette(palette)
            button.setAutoFillBackground(True)
            layout.addWidget(button)
        self.bgpSpkrs = buttonGroup
        layout.setMargin(1)
        layout.setSpacing(1)
        layout.addStretch()
        self.setWidget(widget)

    def _setSelectedSpeaker(self, button):
        self.selectedSpeaker = self.btn2spkr[button]['speaker']
        
    def _speakerInfoString(self, spkr):
        sex = self.spkrs[spkr][3]['speakerType']
        if sex is None or sex == '': sex = '?'
        s = "%s (%s)" % (spkr, sex[0].upper())
        return s
            
    def getSelectedSpeaker(self):
        """
        @return: A tuple.  First value tells whether there is a selected
        speaker.  The second value is the speaker id.
        @type: Tuple
        """
        try:
            row = self.btn2spkr[self.bgpSpkrs.checkedButton()]
            return row['speaker'],row['speakerType'],row['speakerDialect']
        except KeyError:
            return None

    def setCurrentSpeaker(self, spkr):
        if spkr not in self.spkr2btn: return
        self.spkr2btn[spkr].setChecked(True)
        
    def clearSelection(self):
        if self.bgpSpkrs:
            b = self.bgpSpkrs.checkedButton()
            if b:
                # Because he button group wants one of the buttons to be
                # checked always, setChecked(False) is ineffective as long as
                # the button is inside the button group.  
                self.bgpSpkrs.removeButton(b)
                b.setChecked(False)
                self.bgpSpkrs.addButton(b)

    # model-to-self
    def _insertRow(self, i, r):
        spkr = r['speaker']
        if spkr in self.spkrs:
            self.spkrs[spkr][2] += 1
        else:
            self.spkrs[spkr] = [spkr,r['start'],1,r]
            self._display()
            
    def _takeRow(self, i, r):
        spkr = r['speaker']
        self.spkrs[spkr][2] -= 1
        if self.spkrs[spkr][2] == 0:
            del self.spkrs[spkr]
            self._display()

    def _cellChanged(self, i, c, v, w):
        h = self.data.getColumnName(c)
        if h == 'speaker' and v != w:
            self.spkrs[w][2] -= 1
            flag = False
            if self.spkrs[w][2] == 0:
                del self.spkrs[w]
                flag = True
            else:
                for row in self.data:
                    if row['speaker'] == w:
                        self.spkrs[w][1] = row['start']
                        self.spkrs[w][3] = row
                        break
            if v in self.spkrs:
                self.spkrs[v][2] += 1
            else:
                row = self.data[i]
                self.spkrs[v] = [v,row['start'],1,row]
                flag = True
            if flag:
                self._display()
        elif h == 'speakerType':
            spkr = self.data[i]['speaker']
            s = self._speakerInfoString(spkr)
            b = self.spkr2btn[spkr]
            b.setText(s)
            
        
if __name__ == "__main__":
    import sys
    import at4

    d = at4.Transcript.importTrs('xtrans/x.trs')
    app = QApplication([])

    w = SpeakerSelectionPanel(d)
    app.setMainWidget(w)
    w.show()

    app.exec_loop()

