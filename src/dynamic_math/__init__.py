from .dynamath import *
from aqt import gui_hooks


class CustomDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super(CustomDialog, self).__init__(*args, **kwargs)

        self.dyna_math = DynaMathManager(self)

        self.setWindowTitle("DynaMath Addon")
        self.setMinimumSize(500, 400)
        self.setMaximumSize(500, 400)

        self.text_editor = QTextEdit()
        self.output_text = QTextEdit()
        self.info_text = QLineEdit()
        self.toolbar_bottom = QToolBar()
        self.editCardWidgets = [self.text_editor, self.output_text, self.toolbar_bottom]
        self.chooseDeckWidgets = []
        self.chooseCardWidgets = []
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.topHoriBtns = []
        self.topVertBtns = []

        self.action_addNote = None  # may need different solution, see setupEditCardGUI()

        self.saved_texts = ['', '', '', '']
        self.menu_triggered = 1
        self.windowOpen = ''

        self.deck = None
        self.note = None

        # menu_triggered | 0 = graphic text ; 1 = question text ; 2 = answer text ; 3 = algorithm text

        # TOP TOOLBAR
        self.topBtnLayout = self.createTopBtnLayout()

        self.home = True

        self.topContainer = QWidget()
        self.topContainer.setLayout(self.topBtnLayout)
        # Top Toolbar
        self.mainLayout.addWidget(self.topContainer)
        self.setLayout(self.mainLayout)
        # Text Edit GUI
        self.setupEditCardGUI()
        self.setupChooseDeckGUI()
        self.setupChooseCardGUI()
        self.setupHomeGUI()

        self.installEventFilter(self)
        self.show()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.WindowActivate:  # Gained Focus
            if self.dyna_math.previewer is not None:
                self.dyna_math.previewer.close()
        elif event.type() == QEvent.WindowDeactivate:  # Lost Focus
            self.print("Lost focus")
        return False

    #
    # Execute
    #
    def showPreview(self, add_note=False):
        self.saved_texts[self.menu_triggered] = self.text_editor.toPlainText()

        question = self.saved_texts[1]
        answer = self.saved_texts[2]
        algorithm = self.saved_texts[3]
        if self.note is None:  # creating a new note
            self.dyna_math.showPreview(question, answer, algorithm, self.deck['name'], add_note)
        else:  # TODO: editing an existing note - broken
            self.note.fields[0] = question
            self.note.fields[1] = answer
            self.note.fields[2] = algorithm
            mw.col.save(self.note)
            mw.col.reset()
            mw.reset()
            showInfo("Note has been saved.")

    #
    # OUTPUT "CONSOLE" HELPER FUNCTIONS
    #
    def setOutput(self, text):
        self.output_text.setText(text)

    def print(self, text):
        prevText = self.output_text.toPlainText()
        self.output_text.setText(prevText + text + "\n")

    def printArr(self, arr):
        for i in arr:
            self.print(str(i))

    #
    # MAIN GUI FUNCTIONS
    #
    def setupHomeGUI(self):
        self.hideEditCardGUI()
        self.hideChooseDeckGUI()
        self.hideChooseCardGUI()
        self.showTopVertBtns()

    def setupChooseDeckGUI(self):
        # Currently does not support addition of decks while this QDialog is open.
        self.hideEditCardGUI()
        label = QLabel("Please choose a deck:")
        self.chooseDeckWidgets.append(label)
        self.mainLayout.addWidget(label)
        scrollArea = QScrollArea()
        container = QWidget()
        vLayout = QVBoxLayout(container)

        allDecks = mw.col.decks.all()
        for deck in allDecks:
            button = QPushButton(self)
            deck_name = deck['name']
            button.setText(deck_name)

            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            button.clicked.connect(lambda checked, name=deck_name: self.setSelectedDeck(name))

            hLayout = QHBoxLayout()
            hLayout.addWidget(button, 1)
            vLayout.addLayout(hLayout)
            # verticalSpacer = QSpacerItem(0, 10, QSizePolicy.Maximum, QSizePolicy.Maximum)
            # vLayout.addItem(verticalSpacer)

        scrollArea.setWidget(container)
        scrollArea.setWidgetResizable(True)
        self.mainLayout.addWidget(scrollArea)
        self.chooseDeckWidgets.append(scrollArea)  # for easy visible/invisible

    def setupEditCardGUI(self):
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color:#3B434C")
        palette = QPalette()
        palette.setColor(QPalette.Text, Qt.lightGray)
        self.output_text.setPalette(palette)

        # BOTTOM TOOLBAR
        action_editQuestionText = QAction("Edit Question Text", self)
        action_editQuestionText.triggered.connect(lambda checked: self.switchMenu(1))

        action_editAnswerText = QAction("Edit Answer Text", self)
        action_editAnswerText.triggered.connect(lambda checked: self.switchMenu(2))

        action_editAlgorithm = QAction("Edit Algorithm", self)
        action_editAlgorithm.triggered.connect(lambda checked: self.switchMenu(3))

        action_showPreview = QAction("Show Preview", self)
        action_showPreview.triggered.connect(self.showPreview)

        # is self to edit its text when editing existing or creating new note
        self.action_addNote = QAction("Add Note", self)
        self.action_addNote.triggered.connect(lambda checked: self.showPreview(True))

        self.toolbar_bottom.addAction(action_editQuestionText)
        self.toolbar_bottom.addAction(action_editAnswerText)
        self.toolbar_bottom.addAction(action_editAlgorithm)
        self.toolbar_bottom.addAction(action_showPreview)
        self.toolbar_bottom.addAction(self.action_addNote)

        bottom1 = self.toolbar_bottom.findChildren(QToolButton)
        i = 0
        # first QToolButton is irrelevant
        for child in bottom1:
            child.setObjectName("btn" + str(i))
            i += 1

        # Single Line Info
        self.info_text.setReadOnly(True)
        self.info_text.setStyleSheet("background-color:#3B434C")
        self.info_text.setPalette(palette)
        self.mainLayout.addWidget(self.info_text)
        self.editCardWidgets.append(self.info_text)

        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        # Text Editor
        container = QWidget()
        self.editCardWidgets.append(container)
        hLayout = QHBoxLayout(container)
        label = QLabel("Text Editor", self)
        label.setFont(font)
        hLayout.addWidget(label)
        container.setStyleSheet("background-color:#C6E2FF")
        self.mainLayout.addWidget(container)
        self.mainLayout.addWidget(self.text_editor)

        # Console
        container = QWidget()
        self.editCardWidgets.append(container)
        hLayout = QHBoxLayout(container)
        label = QLabel("Console", self)
        label.setFont(font)
        hLayout.addWidget(label)
        container.setStyleSheet("background-color:#C6E2FF")
        self.mainLayout.addWidget(container)
        self.mainLayout.addWidget(self.output_text)

        # Bottom Toolbar
        self.mainLayout.addWidget(self.toolbar_bottom)

        self.switchMenu(1, True)

    def setupChooseCardGUI(self):
        label = QLabel("DynaMath Cards found:")
        self.chooseCardWidgets.append(label)
        self.mainLayout.addWidget(label)

        allModelNames = mw.col.models.allNames()
        decks = {}
        for name in allModelNames:
            if len(name) > 9 and name[:9] == "DynaMath-":
                model = mw.col.models.byName(name)
                deck = mw.col.decks.get(model['did'])

                decks[deck['name']] = mw.col.models.nids(model)

        for key, val in decks.items():
            dropdown = QComboBox()
            dropdown.addItem(key)
            for nid in val:
                note = mw.col.getNote(nid)
                dropdown.addItem(note.fields[0])
            dropdown.currentIndexChanged.connect(lambda index, nids=val: self.openNote(index, nids))
            self.mainLayout.addWidget(dropdown)
            self.chooseCardWidgets.append(dropdown)

    def openNote(self, index, nids):
        if index == 0:
            return
        note = mw.col.getNote(nids[index - 1])
        self.saved_texts = ['', note.fields[0], note.fields[1], note.fields[2]]
        self.showEditCardGUI()
        self.text_editor.setText(self.saved_texts[1])
        self.menu_triggered = 1

        self.deck = mw.col.decks.get(mw.col.models.get(note.mid)['did'])
        self.note = note

        self.info_text.setText("Selected Deck: " + self.deck['name'] + " [editing existing note]")

        self.action_addNote.setText("Save Note")

    #
    # HELPER GUI FUNCTIONS
    #
    # menu_triggered | 0 = graphic text ; 1 = question text ; 2 = answer text ; 3 = algorithm text
    def createTopBtnLayout(self):
        # My workaround for changing from a Vertical Layout for Home to a Horizontal Layout for everything else
        # Needs to change if there is another way
        layout = QVBoxLayout()
        hLayout = QHBoxLayout()
        vLayout = QVBoxLayout()

        btn1 = QPushButton("Create DynaMath Card")
        btn1.clicked.connect(self.showChooseDeckGUI)
        btn2 = QPushButton("Edit DynaMath Card")
        btn2.clicked.connect(self.showChooseCardGUI)
        btn3 = QPushButton("Help")
        btn3.clicked.connect(self.setupHomeGUI)
        hLayout.addWidget(btn1)
        hLayout.addWidget(btn2)
        hLayout.addWidget(btn3)
        self.topHoriBtns = [btn1, btn2, btn3]
        btn1_ = QPushButton("Create DynaMath Card")
        btn1_.clicked.connect(self.showChooseDeckGUI)
        btn2_ = QPushButton("Edit DynaMath Card")
        btn2_.clicked.connect(self.showChooseCardGUI)
        btn3_ = QPushButton("Help")
        btn3_.clicked.connect(self.setupHomeGUI)
        vLayout.addWidget(btn1_)
        vLayout.addWidget(btn2_)
        vLayout.addWidget(btn3_)
        self.topVertBtns = [btn1_, btn2_, btn3_]

        layout.addLayout(hLayout)
        layout.addLayout(vLayout)

        return layout

    def showTopHoriBtns(self):
        for btn in self.topVertBtns:
            btn.setVisible(False)
        for btn in self.topHoriBtns:
            btn.setVisible(True)

    def showTopVertBtns(self):
        for btn in self.topHoriBtns:
            btn.setVisible(False)
        for btn in self.topVertBtns:
            btn.setVisible(True)

    def switchMenu(self, menu_num, first=False):
        if self.menu_triggered != menu_num or first:
            # STYLE
            old_btn = self.toolbar_bottom.findChild(QToolButton, "btn" + str(self.menu_triggered))
            old_btn.setStyleSheet("QToolButton{background:none}")
            btn = self.toolbar_bottom.findChild(QToolButton, "btn" + str(menu_num))
            btn.setStyleSheet("QToolButton{background:#B0B0B0}")

            # DATA/LOGIC
            # saves current text in the correct location
            currentMenu = self.menu_triggered
            self.saved_texts[currentMenu] = self.text_editor.toPlainText()
            # sets text box to desired cached text
            self.text_editor.setText(self.saved_texts[menu_num])
            self.menu_triggered = menu_num

    def showEditCardGUI(self):
        self.hideChooseDeckGUI()
        self.hideChooseCardGUI()
        self.showTopHoriBtns()
        for widget in self.editCardWidgets:
            widget.setVisible(True)

    def showChooseDeckGUI(self):
        self.hideEditCardGUI()
        self.hideChooseCardGUI()
        self.showTopHoriBtns()
        for widget in self.chooseDeckWidgets:
            widget.setVisible(True)

    def showChooseCardGUI(self):
        self.hideEditCardGUI()
        self.hideChooseDeckGUI()
        self.showTopHoriBtns()

        for widget in self.chooseCardWidgets:
            widget.setVisible(True)
            if isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)

    def hideEditCardGUI(self):
        for widget in self.editCardWidgets:
            widget.setVisible(False)

    def hideChooseDeckGUI(self):
        for widget in self.chooseDeckWidgets:
            widget.setVisible(False)

    def hideChooseCardGUI(self):
        for widget in self.chooseCardWidgets:
            widget.setVisible(False)

    def setSelectedDeck(self, name):
        self.deck = mw.col.decks.byName(name)
        self.note = None
        self.info_text.setText("Selected Deck: " + self.deck['name'] + " [editing new note]")

        self.action_addNote.setText("Add Note")

        self.showEditCardGUI()

    # function that's called when closed by dialog manager (found in qt/aqt/__init__.py) (REQUIRED BY ANKI)
    def closeWithCallback(self, *args):
        dialogs.markClosed("testD")


# About QDialog | https://doc.qt.io/qtforpython/PySide2/QtWidgets/QDialog.html#more
def main_func():
    name = "testD"
    dialogs.register_dialog(name, CustomDialog)
    dialogs.open(name, mw)


question = ''
answer = ''


def will_show_question(q, card, state):
    global answer, question
    # TODO: broken: Latex, Previewer - show both sides
    note = card.note()
    model = mw.col.models.get(note.mid)
    # see if model name starts with "DynaMath-"
    new_output = ''
    if len(model['name']) > 9 and model['name'][:9] == "DynaMath-":  # is a dynamath note
        if state == "reviewQuestion" or state == "previewQuestion":
            new_output = card.css()
            # field[0] will have question format. field[1] answer format. field[2] algorithm
            dyna_math = DynaMathManager()
            new_output += dyna_math.generateQuestion(note.fields[0])
            question = new_output
            answer = dyna_math.generateAnswer(note.fields[1], note.fields[2])
        elif state == "reviewAnswer" or state == "previewAnswer":
            new_output = card.css() + answer
        if len(new_output) != 0:
            return new_output
    # Normal Card
    return q


# create a new menu item, "test"
action = QAction("DynaMath", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(main_func)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
gui_hooks.card_will_show.append(will_show_question)
