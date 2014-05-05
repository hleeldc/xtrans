from qt import *

class SpeakerDialog(QWidget):
    def __init__(self, data, wave=None, parent=None):
        """
        @param data: Transcript
        @type data: Transcript
        @param wave: TranscriptWaveform
        @type wave: TranscriptWaveform
        """
        QDialog.__init__(self, parent)

        self.data = data
        self.wave = wave
        
        self._buildWidget()
        self._displaySpeakers()
        
        self.gbxNewSpkr.hide()
        self.btnDelete.hide()
        self.connect(self.btnAdvanced, SIGNAL("clicked()"), self._toggleAdvancedMode)
        self.connect(self.btnSelect, SIGNAL("clicked()"), self._accept)
        self.connect(self.btnCancel, SIGNAL("clicked()"), self._reject)

    def _buildWidget(self):
        vbxLeft = QVBox(self)
        lvwSpeakers = QListView(vbxLeft)
        btnDelete = QPushButton("Delete speaker", vbxLeft)
        vbxRight = QVBox(self)
        gbxAudit = QGroupBox(1, Qt.Horizontal, "Audit Selected Speaker", vbxRight)
        btnRandom = QPushButton("Listen random sample", gbxAudit)
        btnAll = QPushButton("Listen all", gbxAudit)
        gbxNewSpkr = QGroupBox(1, Qt.Vertical, "Add New Speaker", vbxRight)
        hbxNewSpkr = QHBox(gbxNewSpkr)
        grdSpkrInfo = QGrid(2, hbxNewSpkr)
        lblSpkrId = QLabel("ID", grdSpkrInfo)
        ledSpkrId = QLineEdit(grdSpkrInfo)
        lblSpkrType = QLabel("Type", grdSpkrInfo)
        cmbSpkrType = QComboBox(grdSpkrInfo)
        lblSpkrDialect = QLabel("Dialect", grdSpkrInfo)
        cmbSpkrDialect = QComboBox(grdSpkrInfo)
        btnCreate = QPushButton("Create", hbxNewSpkr)
        QWidget(vbxRight)   # spacer
        hbxButtons = QHBox(vbxRight)
        btnSelect = QPushButton("Select", hbxButtons)
        btnCancel = QPushButton("Cancel", hbxButtons)
        btnAdvanced = QPushButton("Advanced mode", vbxRight)

        layout = QHBoxLayout(self)
        layout.addWidget(vbxLeft)
        layout.addWidget(vbxRight)

        layout.setSpacing(10)
        layout.setMargin(10)
        vbxLeft.setMinimumWidth(150)
        vbxRight.setSpacing(10)
        vbxRight.setMargin(5)
        vbxRight.setFixedWidth(250)
        grdSpkrInfo.setSpacing(3)
        hbxNewSpkr.setSpacing(15)
        hbxButtons.setSpacing(10)
        #hbxButtons.setMargin(5)
        lblSpkrId.setAlignment(Qt.AlignRight)
        lblSpkrType.setAlignment(Qt.AlignRight)
        lblSpkrDialect.setAlignment(Qt.AlignRight)
        btnCreate.setFixedWidth(65)
        btnCreate.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        gbxAudit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        gbxNewSpkr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        hbxButtons.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        btnAdvanced.setFixedHeight(15)
        lvwSpeakers.addColumn("ID")
        lvwSpeakers.addColumn("Type")
        lvwSpeakers.addColumn("Dialect")

        self.lvwSpeakers = lvwSpeakers
        self.gbxNewSpkr = gbxNewSpkr
        self.btnAdvanced = btnAdvanced
        self.btnDelete = btnDelete
        self.btnSelect = btnSelect
        self.btnCancel = btnCancel

    def _displaySpeakers(self):
        """
        fill lvwSpeakers
        """
        self.lvwSpeakers.clear()
        h = {}
        for row in self.data:
            h[(row['speaker'],
               row['speakerType'],
               row['speakerDialect'])] = 1
        a = h.keys()
        a.sort()
        for id,typ,dialect in a:
            QListViewItem(self.lvwSpeakers,id,typ,dialect)

    # self-to-self slots
    def _toggleAdvancedMode(self):
        if self.gbxNewSpkr.isHidden():
            self.gbxNewSpkr.show()
            self.btnDelete.show()
            self.btnAdvanced.setText("Simple mode")
        else:
            self.gbxNewSpkr.hide()
            self.btnDelete.hide()
            self.btnAdvanced.setText("Advanced mode")

    def _accept(self):
        self.accept()

    def _reject(self):
        self.reject()
        
if __name__ == "__main__":
    import sys
    import at
    app = QApplication([])

    data = at.Transcript.importTrs(sys.argv[1])
    w = SpeakerDialog(data)
    app.setMainWidget(w)
    w.show()
    app.exec_loop()
