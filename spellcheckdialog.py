from config import *
import aspell
import codecs
import os
from PyQt4 import QtGui
from PyQt4 import QtCore
import sip

__all__ = ["SpellChecker"]

class MyASpell:
    def __init__(self, *args):
        aspell_conf_str = os.getenv('ASPELL_CONF')
        if aspell_conf_str is not None:
            aspell_conf = tuple(tuple(x.split()) for x in aspell_conf_str.split(';'))
        else:
            aspell_conf = ()
        new_args = args + (('encoding','UTF-8'),) + aspell_conf
        new_args = tuple(dict(new_args).items())
        self.aspell = apply(aspell.Speller, new_args)
        self.ignoreList = {}
        
    def check(self, word):
        """
        @param word: unicode encoded word
        """
        if word in self.ignoreList:
            return True
        else:
            return self.aspell.check(word.encode('utf-8'))
    
    def suggest(self, word):
        return self.aspell.suggest(word.encode('utf-8'))

    def addtoSession(self, word):
        try:
            self.aspell.addtoSession(word.encode('utf-8'))
        except aspell.AspellSpellerError:
            self.ignoreList[word] = 1
    
class PwlEditor(QtGui.QDialog):
    def __init__(self, word, pwl, dic):
        QtGui.QDialog.__init__(self)

        self.setWindowTitle("Personal Word List Editor")

        l1 = QtGui.QLabel("New word:", self)
        l2 = QtGui.QLabel("Word in dictionary:", self)

        b1 = QtGui.QPushButton("Add", self)
        b2 = QtGui.QPushButton("Remove", self)
        b3 = QtGui.QPushButton("Close", self)

        le = QtGui.QLineEdit(word, self)
        lbox = QtGui.QListWidget(self)

        layout = QtGui.QGridLayout(self)
        layout.setMargin(10)
        layout.setSpacing(5)
        lbox.setFixedHeight(160)
        lbox.setFixedWidth(160)
        
        layout.addWidget(l1, 0, 0, 1, 2)

        layout.addWidget(le, 1, 0)
        layout.addWidget(b1, 1, 1)

        layout.addWidget(l2, 2, 0, 1, 2)

        layout.addWidget(lbox, 3, 0, 3, 1)
        layout.addWidget(b2, 3, 1)
        layout.addWidget(b3, 5, 1)


        self.dic = dic
        self.pwl = pwl
        self.entry = le
        self.lbox = lbox
        
        self._fillWordList()

        self.connect(b1, QtCore.SIGNAL("clicked()"), self.addWord)
        self.connect(b2, QtCore.SIGNAL("clicked()"), self.removeWord)
        self.connect(b3, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        
    def addWord(self):
        word = unicode(self.entry.text())
        if word not in self.pwl and not self.dic.check(word):
            self.pwl[word] = 1
            self._fillWordList()
        self.entry.setText("")

    def removeWord(self):
        item = self.lbox.currentItem()
        if item:
            word = unicode(item.text())
            self.lbox.removeItemWidget(item)
            sip.delete(item)
            del self.pwl[word]
            
        
    def _fillWordList(self):
        self.lbox.clear()
        words = self.pwl.keys()
        words.sort()
        for w in words:
            self.lbox.addItem(w)

class SpellChecker(QtGui.QDialog):
    MSG_COMPLETE = "Completed spell checking."
    
    def __init__(self, data, te):
        QtGui.QDialog.__init__(self)

        self.setWindowTitle("Spell Checker")

        l1 = QtGui.QLabel("Misspelled word:", self)
        l2 = QtGui.QLabel(self)
        l3 = QtGui.QLabel("Replace with:", self)
        l4 = QtGui.QLabel("Suggestions:", self)
        l5 = QtGui.QLabel("Personal Dictionary:", self)
        l6 = QtGui.QLabel("Language:", self)
        
        le = QtGui.QLineEdit(self)
        
        b1 = QtGui.QPushButton("Recheck Page", self)
        b2 = QtGui.QPushButton("Check Word", self)
        b3 = QtGui.QPushButton("Replace", self)
        b4 = QtGui.QPushButton("Ignore", self)
        b5 = QtGui.QPushButton("Replace All", self)
        b6 = QtGui.QPushButton("Ignore All", self)
        b7 = QtGui.QPushButton("Add Word", self)
        b8 = QtGui.QPushButton("Edit", self)
        b9 = QtGui.QPushButton("Close", self)

        lbox = QtGui.QListWidget(self)
        cbox = QtGui.QComboBox(self)

        f = l2.font()
        f.setWeight(QtGui.QFont.Bold)
        l2.setFont(f)
        layout = QtGui.QGridLayout(self)
        layout.setMargin(10)
        layout.setSpacing(5)
        lbox.setFixedWidth(200)
        lbox.setFixedHeight(120)

        layout.addWidget(l1, 0, 0)
        layout.addWidget(l2, 0, 1, 1, 2)
        layout.addWidget(b1, 0, 3)

        layout.addWidget(l3, 1, 0)
        layout.addWidget(le, 1, 1, 1, 2)
        layout.addWidget(b2, 1, 3)

        layout.addWidget(l4, 2, 0, 1, 3)

        layout.addWidget(lbox, 3, 0, 5, 2)
        layout.addWidget(b3, 3, 2)
        layout.addWidget(b4, 3, 3)
        layout.addWidget(b5, 4, 2)
        layout.addWidget(b6, 4, 3)
        layout.addWidget(l5, 6, 2, 1, 2)
        layout.addWidget(b7, 7, 2)
        layout.addWidget(b8, 7, 3)

        layout.addWidget(l6, 8, 0, 1, 3)

        layout.addWidget(cbox, 9, 0, 1, 2)
        layout.addWidget(b9, 9, 3)

        languages = []
        for tup in aspell.list_dicts():
            if tup[1] not in languages:
                languages.append(tup[1])

        for i,lang in enumerate(languages):
            cbox.insertItem(i,lang)
        try:
            activeLangIdx = languages.index(config["targetLang"])
            cbox.setCurrentIndex(activeLangIdx)
        except ValueError:
            activeLangIdx = 0

        self.connect(cbox, QtCore.SIGNAL("activated(const QString&)"),
                     self.changeDict)
        self.connect(lbox, QtCore.SIGNAL("highlighted(const QString&)"),
                     le, QtCore.SLOT("setText(const QString&)"))
        self.connect(le, QtCore.SIGNAL("textChanged(const QString&)"),
                     self.checkUserWord)
        self.connect(b1, QtCore.SIGNAL("clicked()"), self.recheckPage)
        self.connect(b2, QtCore.SIGNAL("clicked()"), self.checkWord)
        self.connect(b3, QtCore.SIGNAL("clicked()"), self.replace)
        self.connect(b4, QtCore.SIGNAL("clicked()"), self.ignore)
        self.connect(b5, QtCore.SIGNAL("clicked()"), self.replaceAll)
        self.connect(b6, QtCore.SIGNAL("clicked()"), self.ignoreAll)
        self.connect(b7, QtCore.SIGNAL("clicked()"), self.addToPwl)
        self.connect(b8, QtCore.SIGNAL("clicked()"), self.editPwl)
        self.connect(b9, QtCore.SIGNAL("clicked()"), self.closeDialog)
        
        self.data = data
        self.te = te
        self.cbox = cbox
        self.lbox = lbox
        self.languages = languages
        self.activeLangIdx = activeLangIdx
        #self.dic = aspell.Speller(('lang',config["targetLang"]),('encoding','UTF-8'))
        self.dic = MyASpell(('lang',config["targetLang"]))
        self.pwl = {}
        self.iwl = {}
        self.tokenize = lambda x:[]
        self.lblMisspelled = l2
        self.entReplace = le
        self.b2 = b2
        self.b3 = b3
        self.b4 = b4
        self.b5 = b5
        self.b6 = b6
        self.b7 = b7

        self._readPwl()
        self.recheckPage()
        

    def changeDict(self, lang):
        self._writePwl()
        
        if type(lang) != str:
            lang = lang.ascii()
        try:
            #self.dic = aspell.Speller(('lang',lang),('encoding','UTF-8'))
            self.dic = MyASpell(('lang',lang))
        except aspell.AspellSpellerError, e:
            self.cbox.setCurrentItem(self.activeLangIdx)
            QtGui.QMessageBox.critical(
                self,
                "Dictionary Not Found",
                str(e),
                "OK")
            return

        try:
            self.importTokenizer(lang)
        except ImportError:
            self.cbox.setCurrentItem(self.activeLangIdx)
            QtGui.QMessageBox.critical(
                self,
                "Not Supported Language",
                "Annotation guildelines, code-named '%s', doesn not support\n"
                "language '%s' yet." % (config["guidelines"], lang),
                "OK")
            return
            
        self.activeLangIdx = self.languages.index(lang)

        self._readPwl()
        
    def checkUserWord(self, word):
        if unicode(word) == "" or word == self.lblMisspelled.text():
            self.b3.setEnabled(False)
            self.b5.setEnabled(False)
        else:
            self.b3.setEnabled(True)
            self.b5.setEnabled(True)
            
    def importTokenizer(self, lang):
        modnam = "tokenizer.%s.%s" % (lang,config["guidelines"])
        mod = __import__(modnam)
        components = modnam.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        #return mod
        self.tokenize = mod.tokenize

    def checkWord(self):
        word = unicode(self.entReplace.text())
        if self.dic.check(word):
            self.lbox.clear()
            self.lbox.addItem("(correct spelling)")
            self.disconnect(
                self.lbox, QtCore.SIGNAL("highlighted(const QString&)"),
                self.entReplace, QtCore.SLOT("setText(const QString&)"))
        else:
            self._fillSuggestionBox(self.dic.suggest(word))
            
    def recheckPage(self):
        self._enableWidgets()
        #self.iwl = {}
        #self.changeDict(self.languages[self.activeLangIdx])
        self._clearSession()
        self.rowIdx = -1
        self.wordIdx = 0
        self.wordList = []
        self.nextWord()

    def ignore(self):
        self.nextWord()

    def ignoreAll(self):
        _,_,h,k,_,_ = self.wordList[self.wordIdx]
        word = self.line[h:k]
        if word not in self.pwl:
            self.iwl[word] = 1
            self.dic.addtoSession(word)
        self.nextWord()

    def replace(self):
        _,_,h,k,_,_ = self.wordList[self.wordIdx]
        word = self.line[h:k]
        word2 = unicode(self.entReplace.text())
        self.line = self.line[:h] + word2 + self.line[k:]
        self.seg['transcript'] = self.line
        self.wordList = self.tokenize(self.line)

        self.nextWord()
        
    def replaceAll(self):
        _,_,h,k,_,_ = self.wordList[self.wordIdx]
        word = self.line[h:k]
        word2 = unicode(self.entReplace.text())
        self.line = self.line[:h] + word2 + self.line[k:]
        self.seg['transcript'] = self.line

        delta = delta0 = len(word2) - len(word)
        for i in range(self.wordIdx+1,len(self.wordList)):
            _,_,h,k,tag,_ = self.wordList[i]
            h += delta
            k += delta
            word1 = self.line[h:k]
            if word1 == word:
                self.line = self.line[:h] + word2 + self.line[k:]
                self.seg['transcript'] = self.line
                delta += delta0
        self.wordList = self.tokenize(self.line)

        for i in range(self.rowIdx+1,len(self.data)):
            seg = self.data[i]
            line = seg['transcript']
            wordList = self.tokenize(line)
            delta = 0
            for _,_,h,k,tag,_ in wordList:
                h += delta
                k += delta
                word1 = line[h:k]
                if word1 == word:
                    line = line[:h] + word2 + line[k:]
                    seg['transcript'] = line
                    delta += delta0

        self.nextWord()

    def addToPwl(self):
        word = unicode(self.lblMisspelled.text())
        if word not in self.pwl:
            self.pwl[word] = 1
            self.dic.addtoSession(word)
        self.nextWord()

    def editPwl(self):
        word = self.lblMisspelled.text()
        if word == self.MSG_COMPLETE:
            word = ''
        d = PwlEditor(word, self.pwl, self.dic)
        d.exec_()
        del d
        del self.dic
        self.changeDict(self.languages[self.activeLangIdx])
        for w in self.iwl:
            self.dic.addtoSession(w)

    def closeEvent(self, e):
        self.closeDialog()
        
    def closeDialog(self):
        self._writePwl()
        extra = QtGui.QTextEdit.ExtraSelection()
        extra.cursor= self.te.textCursor()
        extra.cursor.clearSelection()
        self.te.setExtraSelections([extra])
        self.accept()
        
    def nextWord(self):
        checked = True
        while checked:
            self.wordIdx += 1
            if self.wordIdx >= len(self.wordList):
                if self.rowIdx >= len(self.data):
                    self.finish()
                    return
                else:
                    for self.rowIdx in range(self.rowIdx+1,len(self.data)):
                        self.seg = self.data[self.rowIdx]
                        self.line = self.seg['transcript']
                        self.wordList = self.tokenize(self.line)
                        if self.wordList:
                            self.wordIdx = 0
                            break
                    else:
                        self.finish()
                        return

            i,j,h,k,tag,desc = self.wordList[self.wordIdx]
            if tag == "":
                word = self.line[h:k]
                checked = self.dic.check(word)
            
        self.lblMisspelled.setText(word)
        self._fillSuggestionBox(self.dic.suggest(word))

        p = self.te.getParagraphIndex(self.seg.num)
        if p is not None:
            extra = QtGui.QTextEdit.ExtraSelection()
            extra.format.setForeground(QtCore.Qt.red)
            extra.cursor= self.te.textCursor()
            pos = extra.cursor.document().findBlockByNumber(p).position()
            beg_pos = pos + h
            end_pos = pos + k
            extra.cursor.setPosition(beg_pos)
            extra.cursor.setPosition(end_pos, QtGui.QTextCursor.KeepAnchor)
            self.te.setExtraSelections([extra])
            cur = self.te.textCursor()
            cur.setPosition(end_pos)
            self.te.setTextCursor(cur)

    def finish(self):
        self._disableWidgets()
        self.lbox.clear()
        self.entReplace.setText("")
        self.lblMisspelled.setText(self.MSG_COMPLETE)

    def _disableWidgets(self):
        self.b2.setEnabled(False)
        self.b3.setEnabled(False)
        self.b4.setEnabled(False)
        self.b5.setEnabled(False)
        self.b6.setEnabled(False)
        self.b7.setEnabled(False)
        self.entReplace.setReadOnly(True)

    def _enableWidgets(self):
        self.b2.setEnabled(True)
        self.b3.setEnabled(True)
        self.b4.setEnabled(True)
        self.b5.setEnabled(True)
        self.b6.setEnabled(True)
        self.b7.setEnabled(True)
        self.entReplace.setReadOnly(False)

    def _fillSuggestionBox(self, suggs):
        self.lbox.clear()
        self.disconnect(
            self.lbox, QtCore.SIGNAL("highlighted(const QString&)"),
            self.entReplace, QtCore.SLOT("setText(const QString&)"))
        if len(suggs) == 0:
            self.lbox.insertItem("(no suggested words)")
            self.entReplace.clear()
        else:
            suggs = [w.decode('utf-8') for w in suggs]
            for w in suggs:
                self.lbox.addItem(w)
            self.entReplace.setText(suggs[0])
            self.connect(
                self.lbox, QtCore.SIGNAL("highlighted(const QString&)"),
                self.entReplace, QtCore.SLOT("setText(const QString&)"))

    def _clearSession(self):
        del self.dic
        self.iwl = {}
        self.changeDict(self.languages[self.activeLangIdx])

    def _readPwl(self):
        lang = self.languages[self.activeLangIdx]
        pwl = config['xtransdir'] + "/pwl.%s" % lang
        if not os.path.exists(pwl): return
        f = codecs.getreader("utf-8")(file(pwl,"r"))
        self.pwl = {}
        for w in f:
            w = w.strip()
            if w not in self.pwl:
                self.pwl[w] = 1
                self.dic.addtoSession(w)

    def _writePwl(self):
        lang = self.languages[self.activeLangIdx]
        pwl = config['xtransdir'] + "/pwl.%s" % lang
        f = codecs.getwriter("utf-8")(file(pwl,"w"))
        words = self.pwl.keys()
        words.sort()
        for w in words:
            f.write(w + '\n')

if __name__ == "__main__":
    import at4

    app = QApplication([])
    w = PwlEditor()
    app.setMainWidget(w)
    w.show()
    app.exec_loop()
