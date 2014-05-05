from PyQt4 import QtCore
from PyQt4 import QtGui
import re

__all__ = ["KeySeqInputDialog", "str2qkeyseq", "str2objname"]


#
#  user input:   ctrl key + shift key + comma key
#
#  qt repr.:     Qt.CTRL | Qt.SHIFT | Qt.Key_Less
#
#  xtrans repr.: Ctrl+Shift+,
#
KEYS = {}       # Qt code -> name, e.g. Qt.Key_Comma -> 'Comma'
KEYS_R = {}     # name -> Qt code, e.g. 'Comma' -> Qt.Key_Comma

EX = ['Key_Alt','Key_Control','Key_Shift','Key_Meta','Key_unknown']
for v in dir(QtCore.Qt):
    if v.startswith('Key_') and v not in EX:
        key = v.split('_')[1]
        KEYS[eval("QtCore.Qt."+v)] = key
for k,v in KEYS.items():
    KEYS_R[v] = k

# shifted-up name --> shifted-down name, e.g.  Dollar -> $
SHIFT_DOWN = {
    'Backtab':'Tab',
    'AsciiTilde':'QuoteLeft',
    'Exclam':'1',
    'At':'2',
    'NumberSign':'3',
    'Dollar':'4',
    'Percent':'5',
    'AsciiCircum':'6',
    'Ampersand':'7',
    'Asterisk':'8',
    'ParenLeft':'9',
    'ParenRight':'0',
    'Underscore':'Minus',
    'Plus':'Equal',
    'BraceLeft':'BracketLeft',
    'BraceRight':'BracketRight',
    'Bar':'Backslash',
    'Colon':'Semicolon',
    'QuoteDbl':'Apostrophe',
    'Less':'Comma',
    'Greater':'Period',
    'Question':'Slash',
    }

# shifted-down name --> shifted-up name, e.g.  $ -> Dollar
SHIFT_UP = {
    'Tab':'Backtab',
    'QuoteLeft':'AsciiTilde',
    '1':'Exclam',
    '2':'At',
    '3':'NumberSign',
    '4':'Dollar',
    '5':'Percent',
    '6':'AsciiCircum',
    '7':'Ampersand',
    '8':'Asterisk',
    '9':'ParenLeft',
    '0':'ParenRight',
    'Minus':'Underscore',
    'Equal':'Plus',
    'BracketLeft':'BraceLeft',
    'BracketRight':'BraceRight',
    'Backslash':'Bar',
    'Semicolon':'Colon',
    'Apostrophe':'QuoteDbl',
    'Comma':'Less',
    'Period':'Greater',
    'Slash':'Question',
    }

# key name --> acsii character
NAME_ENC = {
    'QuoteLeft':'`',
    'AsciiTilde':'~',
    'Exclam':'!',
    'At':'@',
    'NumberSign':'#',
    'Dollar':'$',
    'Percent':'%',
    'AsciiCircum':'^',
    'Ampersand':'&',
    'Asterisk':'*',
    'ParenLeft':'(',
    'ParenRight':')',
    'Minus':'-',
    'Underscore':'_',
    'Equal':'=',
    #'Plus':'+',     # plus is reserved for a joiner
    'BracketLeft':'[',
    'BracketRight':']',
    'BraceLeft':'{',
    'BraceRight':'}',
    'Backslash':'\\',
    'Bar':'|',
    'Semicolon':';',
    'Colon':':',
    'Apostrophe':"'",
    'QuoteDbl':'"',
    #'Comma':',',   # comma is reserved for a separator
    'Less':'<',
    'Period':'.',
    'Greater':'>',
    'Slash':'/',
    'Question':'?',
    }

# ascii character --> key name
NAME_DEC = {
    '`':'QuoteLeft',
    '~':'AsciiTilde',
    '!':'Exclam',
    '@':'At',
    '#':'NumberSign',
    '$':'Dollar',
    '%':'Percent',
    '^':'AsciiCircum',
    '&':'Ampersand',
    '*':'Asterisk',
    '(':'ParenLeft',
    ')':'ParenRight',
    '-':'Minus',
    '_':'Underscore',
    '=':'Equal',
    #'+':'Plus',     # plus is reserved for a joiner
    '[':'BracketLeft',
    ']':'BracketRight',
    '{':'BraceLeft',
    '}':'BraceRight',
    '\\':'Backslash',
    '|':'Bar',
    ';':'Semicolon',
    ':':'Colon',
    "'":'Apostrophe',
    '"':'QuoteDbl',
    #',':'Comma',   # comma is reserved for a separator
    '<':'Less',
    '.':'Period',
    '>':'Greater',
    '/':'Slash',
    '?':'Question',
    }


## KEYS[Qt.Key_Backtab] = 'Tab'
## KEYS[Qt.Key_AsciiTilde] = 'QuoteLeft'
## KEYS[Qt.Key_Exclam] = '1'
## KEYS[Qt.Key_At] = '2'
## KEYS[Qt.Key_NumberSign] = '3'
## KEYS[Qt.Key_Dollar] = '4'
## KEYS[Qt.Key_Percent] = '5'
## KEYS[Qt.Key_AsciiCircum] = '6'
## KEYS[Qt.Key_Ampersand] = '7'
## KEYS[Qt.Key_Asterisk] = '8'
## KEYS[Qt.Key_ParenLeft] = '9'
## KEYS[Qt.Key_ParenRight] = '0'
## KEYS[Qt.Key_Underscore] = 'Minus'
## KEYS[Qt.Key_Plus] = 'Equal'
## KEYS[Qt.Key_BraceLeft] = 'BracketLeft'
## KEYS[Qt.Key_BraceRight] = 'BracketRight'
## KEYS[Qt.Key_Bar] = 'Backslash'
## KEYS[Qt.Key_Colon] = 'Semicolon'
## KEYS[Qt.Key_QuoteDbl] = 'Apostrophe'
## KEYS[Qt.Key_Less] = 'Comma'
## KEYS[Qt.Key_Greater] = 'Period'
## KEYS[Qt.Key_Question] = 'Slash'

## KEYS_R['Backtab'] = Qt.Key_Tab
## KEYS_R['AsciiTilde'] = Qt.Key_QuoteLeft
## KEYS_R['Exclam'] = Qt.Key_1
## KEYS_R['At'] = Qt.Key_2
## KEYS_R['NumberSign'] = Qt.Key_3
## KEYS_R['Dollar'] = Qt.Key_4
## KEYS_R['Percent'] = Qt.Key_5
## KEYS_R['AsciiCircum'] = Qt.Key_6
## KEYS_R['Ampersand'] = Qt.Key_7
## KEYS_R['Asterisk'] = Qt.Key_8
## KEYS_R['ParenLeft'] = Qt.Key_9
## KEYS_R['ParenRight'] = Qt.Key_0
## KEYS_R['Underscore'] = Qt.Key_Minus
## KEYS_R['Plus'] = Qt.Key_Equal
## KEYS_R['BraceLeft'] = Qt.Key_BracketLeft
## KEYS_R['BraceRight'] = Qt.Key_BracketRight
## KEYS_R['Bar'] = Qt.Key_Backslash
## KEYS_R['Colon'] = Qt.Key_Semicolon
## KEYS_R['QuoteDbl'] = Qt.Key_Apostrophe
## KEYS_R['Less'] = Qt.Key_Comma
## KEYS_R['Greater'] = Qt.Key_Period
## KEYS_R['Question'] = Qt.Key_Slash

class KeySeqInputDialog(QtGui.QDialog):
    def __init__(self, stoplist=[], default="", parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.stoplist = stoplist
        
        self.setWindowTitle("Key Sequence Input")

        self.b1 = QtGui.QCheckBox("Ctrl",self)
        self.b2 = QtGui.QCheckBox("Alt",self)
        self.b3 = QtGui.QCheckBox("Shift",self)
        self.label = QtGui.QLineEdit(self)

        self.labels = []
        for i in range(4):
            label2 = QtGui.QLineEdit(self)
            self.labels.append(label2)

        self.btnReset = QtGui.QPushButton("Reset", self)
        self.btnDone = QtGui.QPushButton("Done", self)
        self.btnCancel = QtGui.QPushButton("Cancel", self)

        layout = QtGui.QVBoxLayout(self)
        upper = QtGui.QVBoxLayout()
        buttons = QtGui.QHBoxLayout()
        labelwrap = QtGui.QHBoxLayout()
        buttons2 = QtGui.QHBoxLayout()
        
        layout.addLayout(upper)
        upper.addLayout(buttons)
        upper.addLayout(labelwrap)
        layout.addLayout(buttons2)
        
        buttons.addStretch()
        buttons.addWidget(self.b1)
        buttons.addWidget(self.b2)
        buttons.addWidget(self.b3)
        buttons.addStretch()

        labelwrap.addStretch()
        labelwrap.addWidget(self.label)
        labelwrap.addStretch()
        
        layout.addWidget(self.labels[0])
        layout.addWidget(self.labels[1])
        layout.addWidget(self.labels[2])
        layout.addWidget(self.labels[3])
        
        buttons2.addWidget(self.btnReset)
        buttons2.addWidget(self.btnDone)
        buttons2.addWidget(self.btnCancel)
        
        self.b1.setTristate(True)
        self.b2.setTristate(True)
        self.b3.setTristate(True)
        self.b1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.b2.setFocusPolicy(QtCore.Qt.NoFocus)
        self.b3.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btnReset.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btnDone.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btnCancel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.label.setFocusPolicy(QtCore.Qt.NoFocus)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        self.label.setFixedWidth(160)
        f = self.label.font()
        f.setPointSize(24)
        self.label.setFont(f)
        
        f.setPointSize(16)
        for label in self.labels:
            label.setFont(f)
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setFocusPolicy(QtCore.Qt.NoFocus)
        
        layout.setSpacing(3)
        layout.setMargin(3)
        upper.setMargin(10)
        buttons2.setMargin(10)
        buttons2.setSpacing(10)
        
        self.stack = []
        self.keyseq = []    # stores key sequence entered by user
                            # 

        for i,s in enumerate(default.split(',')):
            if i >= 4: break
            self.labels[i].setText(s)
            
        self.connect(self.btnReset, QtCore.SIGNAL("clicked()"), self._init)
        self.connect(self.btnDone, QtCore.SIGNAL("clicked()"), self._done)
        self.connect(self.btnCancel, QtCore.SIGNAL("clicked()"), self._cancel)


    def _init(self):
        self.stack = []
        self.keyseq = []
        self.b1.setChecked(False)
        self.b2.setChecked(False)
        self.b3.setChecked(False)
        self.label.clear()
        for l in self.labels:
            l.clear()

    def _done(self):
        self.done(self.Accepted)
        
    def _cancel(self):
        self.done(self.Rejected)

    def _init(self):
        self.keyseq = []
        self.stack = []
        for l in self.labels:
            l.clear()
            palette = l.palette()
            palette.setColor(palette.Text, QtCore.Qt.black)
            l.setPalette(palette)
        self.btnDone.setEnabled(True)
        self.b1.setChecked(False)
        self.b2.setChecked(False)
        self.b3.setChecked(False)

        
    def keyPressEvent(self, e):
        # initialize data structures if the key stack is empty
        # key stack is empty when no key is held down by the user
        if not self.stack: self._init()
            
        # set modifier checkboxes
        s = e.modifiers()
        self.b1.setChecked(False)
        self.b2.setChecked(False)
        self.b3.setChecked(False)
        if s & QtCore.Qt.AltModifier:
            self.b2.setChecked(True)
        if s & QtCore.Qt.ControlModifier:
            self.b1.setChecked(True)
        if s & QtCore.Qt.ShiftModifier:
            self.b3.setChecked(True)
            
        k = e.key()     # 
        self.stack.append(k)
        #print "press %d %x" % (k,k)

        self.label.clear()
        if k in (QtCore.Qt.Key_Alt,QtCore.Qt.Key_Meta):
            self.b2.setChecked(True)
        elif k == QtCore.Qt.Key_Control:
            self.b1.setChecked(True)
        elif k == QtCore.Qt.Key_Shift:
            self.b3.setChecked(True)
        elif k == 4185:
            # press Shift -> press Ctrl -> release Shift or Ctrl
            # press Ctrl -> press Shift -> release Shift or Ctrl
            self.stack.pop()
            self.stack.pop()
            self.b1.setNoChange()
            self.b3.setNoChange()
        elif len(self.keyseq) < 4:
            ch = e.text().at(0).unicode()
            if (ch >= 0 and ch <= 32) or ch == 127:
                try:
                    label = KEYS[k]
                except KeyError:
                    QtGui.QMessageBox.warning(
                        self, "Error",
                        "That combination of keys is not recognized.\n"
                        "Check your keyboard configuration.",
                        "&OK")
                    self._init()
                    return
                code = k
            else:
                label = unichr(ch)
                code = ch
                
            self.keyseq.append(self.modifiers()+[code])
            self.label.setText(label)
            self.labels[len(self.keyseq)-1].setText(self.asString().split(',')[-1])
            
##             if k < 256:
##                 v = k
##             else:
##                 v = e.text().at(0).unicode()
##             if k in KEYS:
##                 label = KEYS[k]
##                 code = k
##             elif v != 0:
##                 label = unichr(v)
##                 code = e.text().at(0).unicode()
##             else:
##                 label = None
##                 code = None
##             if label is not None and len(self.keyseq) < 4:
##                 if label in NAME_ENC:
##                     self.label.setText(NAME_ENC[label])
##                 else:
##                     self.label.setText(label)
##                 self.keyseq.append(self.modifiers()+[code])
##                 self.labels[len(self.keyseq)-1].setText(self.asString().split(',')[-1])

    def keyReleaseEvent(self, e):
        try:
            self.stack.pop()
        except IndexError:
            pass
        if not self.stack:
            self.b1.setChecked(False)
            self.b2.setChecked(False)
            self.b3.setChecked(False)
            self.label.clear()
            if self.asString() in self.stoplist:
                self.btnDone.setEnabled(False)
                for label in self.labels:
                    palette = label.palette()
                    palette.setColor(QtGui.QPalette.Text, QtCore.Qt.red)
                    label.setPalette(palette)
        else:
            k = e.key()
            if self.stack[-1] != k:
                if k in (QtCore.Qt.Key_Alt,QtCore.Qt.Key_Meta):
                    self.b2.setChecked(False)
                elif k == QtCore.Qt.Key_Control:
                    self.b1.setChecked(False)
                elif k == QtCore.Qt.Key_Shift:
                    self.b3.setChecked(False)

    def asString(self):
        """
        """
        l = []
        for seq in self.keyseq:
            seq = seq[:]
            code = seq[-1]
            if code in KEYS:
                label = KEYS[code]
                #if 'Shift' in seq and label in SHIFT_DOWN:
                #    label = SHIFT_DOWN[label]
                if label in NAME_ENC:
                    label = NAME_ENC[label]
                if re.match("^[A-Z]$", label):
                    if 'Shift' not in seq:
                        label = label.lower()
            else:
                label = unichr(code)
            try:
                seq.remove('Shift')
            except ValueError:
                pass
            l.append('+'.join(seq[:-1]+[label]))
        return ','.join(l)

    def modifiers(self):
        """
        """
        seq = []
        if self.b1.isChecked():
            seq.append('Ctrl')
        if self.b2.isChecked():
            seq.append('Alt')
        if self.b3.isChecked():
            seq.append('Shift')
        return seq


def str2qkeyseq(s):
    """
    String -> Qt key code
    """
    mods = {'Ctrl':QtCore.Qt.CTRL,'Shift':QtCore.Qt.SHIFT,'Alt':QtCore.Qt.ALT}
    codes = []
    for seq in s.split(','):
        code = QtCore.Qt.UNICODE_ACCEL

        # obtain key sequence (xtrans repr.)
        a = seq.split('+')
        shift = False   # tell if there is a shift modifier in the seq

        # convert modifiers to Qt repr.
        for m in a[:-1]:
            code |= mods[m]

        try:
            key = NAME_DEC[a[-1]]
        except KeyError:
            key = a[-1]

        m = re.match("^[A-Z]$", key)
        if key in KEYS_R and not m:
            code |= KEYS_R[key]
        else:
            if m:
                code |= QtCore.Qt.SHIFT
            elif re.match("^[a-z]$", key):
                key = key.upper()
            code |= ord(key)

        codes.append(code)


    return apply(QtGui.QKeySequence,codes)


def str2objname(s):
    a = s.split('+')
    if a[-1] in NAME_DEC:
        a[-1] = NAME_DEC[a[-1]]
    return "_".join(a)

    
