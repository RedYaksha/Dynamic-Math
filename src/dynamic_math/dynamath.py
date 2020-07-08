from aqt import *
from anki.notes import *
import json
import pathlib
import time
from .mathdef import *
from aqt.previewer import Previewer
from aqt.previewer import SingleCardPreviewer as PreviewerDialog
from anki.cards import Card
from aqt.utils import showInfo


class DynaMathManager:

    def __init__(self, custom_dialog=None):
        self.dialog = custom_dialog
        self.previewer = None
        self.card = None
        self.note = None
        self.prev_bool = False

        self.variables = []  # TODO change into map?
        self.temp_variables = {}
        self.supportedOperations = ['+', '-', '*', '/', '(', ')', '^']
        self.supportedFunctions = ["der", "int"]

        self.text_handler = TextHandler(self)
        self.algo_handler = AlgorithmHandler(self)

    def card(self):
        return self.card
    #
    # ADDING ANKI NOTES
    #
    def addMathNote(self, front, back, algo, deck_name, add_note):
        # did = deck id, mid = model id, ... etc.
        model_name = "DynaMath-" + deck_name

        deck_id = mw.col.decks.id(deck_name)

        models = mw.col.models  # Collection's Model Manager

        cur_model = models.byName(model_name)

        if cur_model is None:  # model not found? Then create it
            cur_model = createTestModel(deck_name, model_name)

        note = Note(mw.col, cur_model)  # returns Note using the currently selected model

        note.fields[0] = front
        note.fields[1] = back
        note.fields[2] = algo

        mw.col.decks.select(deck_id)  # selecting "testDeck"
        card_num = mw.col.addNote(note)  # mw.col adds note to currently selected deck

        self.print("Add Note Returned: " + str(card_num))

        mw.col.reset()  # reset DB for GUI to show
        mw.reset()

        if not add_note:
            self.card = note.cards()[0]
            self.note = note

    #
    # GENERATING FRONT/BACK PREVIEW & EXECUTING ALGORITHM
    #
    def showPreview(self, question_text, answer_text, algo_text, deck_name, add_note=False,):
        if not add_note and self.previewer is not None:  # Previewer not closed
            self.previewer.close()

        self.variables = []
        self.text_handler.updateVariables()
        self.algo_handler.updateVariables()

        question_text = "What! is [$]{Var(x,Integer,1,10)} + {Var(y,Integer,11,100)} - 2*{Var(x)}[/$]"
        answer_text = "The answer is {Var(output)}"
        algo_text = " output = x + y - 2*x \n"

        question_text = self.text_handler.parseRawText(question_text)
        self.algo_handler.parseAlgorithm(algo_text)
        answer_text = self.text_handler.parseRawText(answer_text)

        self.addMathNote(question_text, answer_text, algo_text, deck_name, add_note)

        # Set console cursor to end
        if self.dialog is not None:
            cursor = self.dialog.output_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.dialog.output_text.setTextCursor(cursor)

        # Preview
        if not add_note:
            self.previewer = PreviewerDialog(self.card, self, mw, self._on_preview_closed)
            self.previewer.open()

    def _on_preview_closed(self):
        self.previewer = None
        mw.col.remNotes([self.note.id])  # TODO: not removing, correct nid?
        mw.col.save()
        self.note = None
        self.card = None
        mw.col.reset()  # reset DB for GUI to show
        mw.reset()
    #
    # GENERATE FRONT/BACK FOR REVIEW
    #
    def generateQuestion(self, text):
        return self.text_handler.parseRawText(text, True, True)

    def generateAnswer(self, text, algo_text):
        self.algo_handler.parseAlgorithm(algo_text)
        return self.text_handler.parseRawText(text, True, False)
    #
    # HELPERS
    #
    def findVariable(self, x):
        for obj in self.variables:
            if obj.name == x:
                return obj
        return None

    #
    # DEBUG/ERROR OUTPUT
    #
    def print(self, text):
        if self.dialog is not None:
            self.dialog.print(text)


def createTestModel(deck_name, model_name):
        models = mw.col.models  # Collection's Model Manager
        deck_id = mw.col.decks.id(deck_name)
        deck1 = mw.col.decks.get(deck_id)

        cur_model = models.new(model_name)

        # adding fields
        models.addField(cur_model, models.newField("question"))
        models.addField(cur_model, models.newField("answer"))
        models.addField(cur_model, models.newField("algorithm"))

        # add template (NEEDED FOR CARD CREATION) P.S needs to go after the fields are created
        t = models.newTemplate("Normal")
        t['qfmt'] = "<p>{{question}}</p>"  # cannot be empty
        t['afmt'] = "<p>{{answer}}</p>"  # cannot be empty
        models.addTemplate(cur_model, t)  # adds template to cur_model

        models.add(cur_model)
        mw.col.models.save(cur_model)

        mw.col.decks.select(deck_id)
        mw.col.decks.current()['mid'] = cur_model['id']  # deck's model id is cur_model's id
        mw.col.decks.save(deck1)  # commit in the DB

        mw.col.models.setCurrent(cur_model)  # current model = cur_model
        models.current()['did'] = mw.col.decks.current()['id']  # cur_model's deck id is the deck's id
        mw.col.models.save(cur_model)  # commit in the DB
        return cur_model


class TextHandler:

    def __init__(self, dyna_manager: DynaMathManager):
        self.dyna_math = dyna_manager
        self.variables = self.dyna_math.variables
        self.temp_variables = self.dyna_math.temp_variables

    def parseRawText(self, text, execute=False, question=False):
        # parses raw text and saves any variables that are explicitly written along with what type of number it is.
        # converts raw text into text for a front of a card (without the values of the variables written)
        # variables are then used by the algorithm written by the user
        # possible notation to use: { Var(x,Integer,1,50) }
        i = 0
        special_data = []  # list of tuples that are used to replace {Var(x,params)} to just x
        while i < len(text):
            if text[i] == '{':
                # find where the ending } is.
                for j in range(i, len(text)):
                    if text[j] == '}':
                        var_str = text[i:j + 1]
                        params = self.parseVarStr(var_str)
                        special_data.append((var_str, params[0]))
                        if len(params) == 1:  # then it may be an existing variable
                            if self.findVariable(params[0]) is not None:
                                i = j
                                break
                            elif params[0] in self.temp_variables:
                                i = j
                                break
                            else:
                                if not execute:
                                    self.print("ERROR: Variable does not exist: " + params[0])
                                special_data.pop()
                                raise Exception
                        self.variables.append(Variable(params[0], params[1], params[2:]))
                        i = j
                        break
            i += 1

        final_str = text

        if execute:
            for var in special_data:  # var[0] = the whole { ...} | var[1] = variable name
                variable = self.findVariable(var[1])
                if variable is None:  # Then check temp variables
                    # (temp/existing values should have final values at this point)
                    value = self.temp_variables[var[1]]
                    final_str = final_str.replace(var[0], str(value))
                    return final_str
                if question and variable.value == 0:
                    variable.generateRandomValue()
                    # showInfo("Question " + str(var[1]) + " " + str(variable.value))
                final_str = final_str.replace(var[0], str(variable.value))
                # showInfo(str(self.findVariable('x').value))

        return final_str

    #
    # HELPERS
    #
    def parseVarStr(self, str):
        params = []

        start = str.find('(')
        end = str.find(')')

        if str[1:start] == "Var":
            tmp_str = str[start + 1:end]
            comma_ind = tmp_str.find(',')
            while comma_ind != -1:
                params.append(tmp_str[:comma_ind])
                tmp_str = tmp_str[comma_ind + 1:]
                comma_ind = tmp_str.find(',')
            # account for the last arg
            params.append(tmp_str)
        else:
            self.print("another type")
        return params

    def findVariable(self, x):
        return self.dyna_math.findVariable(x)

    def updateVariables(self):
        self.variables = self.dyna_math.variables

    #
    # FOR DEBUG/ERROR
    #
    def print(self, text):
        self.dyna_math.print(text)


class AlgorithmHandler:

    def __init__(self, dyna_manager: DynaMathManager):
        self.dyna_math = dyna_manager
        self.temp_variables = self.dyna_math.temp_variables
        self.variables = self.dyna_math.variables
        self.supportedOperations = self.dyna_math.supportedOperations
        self.supportedFunctions = self.dyna_math.supportedFunctions

    def parseAlgorithm(self, text):
        # generates random numbers for each variable that was created in parseRawText()
        # goes through the written function and generates an output.
        # types of input/output are: integer, double, integral, complex number, function, etc.

        # TODO: each line goes through lexer (in C) -> parser (in C) -> sends back output value and is assigned
        # TODO: in either variables or temp variables

        lines = text.splitlines()

        # Restricted to lines of the form: "var_name = <logic here>"
        for line in lines:
            processed_tokens = self.tokenizeAlgorithm(line)

            if processed_tokens[0][1] != "str":
                self.print("LHS not valid.")
                raise Exception
            elif processed_tokens[1][0] != '=':
                self.print("'=' is missing")
                raise Exception

            var_name = processed_tokens[0][0]  # TODO: check if these are indeed var =
            logic = processed_tokens[2:]
            self.print(str(var_name))
            var = self.findVariable(var_name)
            self.print(str(var))
            if var is None:
                self.print("Temp Variable")
                self.temp_variables[var_name] = self.processLogic(logic)
            else:
                self.print("Existing Variable")
                var.value = self.processLogic(logic)
                # need to check if output is of correct type

        self.print("Temporary Variables: ")
        for key, val in self.temp_variables.items():
            self.print(key + ":" + str(val))
        self.print("Existing Variables: ")
        for var in self.variables:
            self.print(var.name + ":" + str(var.value))
        # output is in the form of temp_variables and variables

    # LEXER
    def tokenizeAlgorithm(self, text):
        # types: char, num, operator
        tokens = []
        operators = [40, 41, 42, 43, 44, 45, 47, 61, 94]
        # classify each non whitespace character
        for char in text:
            ascii = ord(char)
            if 65 <= ascii <= 90 or 97 <= ascii <= 122:
                # letter
                tokens.append((char, "char"))
            elif 48 <= ascii <= 57:
                # number
                tokens.append((char, "num"))
            elif ascii in operators:
                # operator
                tokens.append((char, "op"))

        # self.print("Tokens: " + str(tokens))

        word = False
        number = False
        double = False
        func = False
        buffer = ""
        tokens_adv = []
        func_form = []
        param_num = 0
        # adding more context to the tokens.
        for token in tokens:
            if sum([word, number, double, func]) > 1:
                self.print("Multiple TRUE. Booleans = " + str([word, number, double, func]))
                raise Exception

            if token[1] == "char":
                if number is True:  # "Word" started with number -> INVALID
                    self.print("INVALID NAME - CAN'T START WITH A NUMBER")
                    raise Exception
                if func is True:  # Constructing Function Param
                    buffer += token[0]
                else:  # Start of a word
                    word = True
                    buffer += token[0]

            elif token[1] == "num":
                if word is True:  # Word + Num // part of a variable
                    buffer += token[0]
                elif double is True:  # Double + Num // adding to the double
                    buffer += token[0]
                elif number is True:  # Already Construct Num // adding to num
                    buffer += token[0]
                elif func is True:
                    buffer += token[0]
                else:  # Start to a number
                    number = True
                    buffer += token[0]

            elif token[1] == "op":
                # Special Cases
                if func is True and token[0] == ',':
                    func_form.append(buffer)
                    buffer = ''
                    param_num += 1
                elif func is True and token[0] == ')':  # Func -> ')' // end of function
                    func_form.append(buffer)  # last param
                    func_form.append(param_num + 1)  # last entry = num of arg
                    tokens_adv.append((str(func_form), "func"))
                    func_form.clear()
                    param_num = 0
                    buffer = ''
                    func = False
                elif number and token[1] == '.':  # Number -> '.' // double
                    double = True
                    number = False
                # Normal Cases
                elif word is True:
                    if token[0] == '(':  # Word -> '(' // start to a function
                        func_form.append(buffer)  # func_form[0] = function name
                        buffer = ''
                        func = True
                        word = False
                    else:  # Word -> Operator
                        tokens_adv.append((buffer, "str"))
                        tokens_adv.append((token[0], "op"))
                        buffer = ''
                        word = False
                elif number is True:  # Number -> Operator
                    tokens_adv.append((buffer, "num"))
                    tokens_adv.append((token[0], "op"))
                    buffer = ''
                    number = False
                elif double is True:  # Double -> Operator
                    tokens_adv.append((buffer, "double"))
                    tokens_adv.append((token[0], "op"))
                    buffer = ''
                    double = False
                else:
                    tokens_adv.append((token[0], "op"))
        # handle extra
        if len(buffer) != 0:
            if word:
                tokens_adv.append((buffer, "str"))
            elif number:
                tokens_adv.append((buffer, "num"))
            elif double:
                tokens_adv.append((buffer, "double"))
            elif func:
                tokens_adv.append((buffer, "func"))
            else:
                self.print("handle extra type error. Buffer = " + buffer)
                raise Exception
        self.print(str(tokens_adv))
        return tokens_adv

    def processLogic(self, logic_tokens):
        # Stacks (as lists) for evaluating the POST-FIX notation
        operators = []
        values = []

        for item in logic_tokens:
            # Remember the tokens are tuples : (value,type)
            value = item[0]  # value is either an operation, value, or function

            if value in self.supportedOperations:  # OPERATION

                if len(operators) != 0 and value != '(':
                    op = operators[-1]  # top of operators

                    if value == ')' and op == '(':  # handles ( x )
                        operators.pop()  # popped '('
                    elif prec(op) >= prec(value) and op != '(' or value == ')':
                        val1 = values.pop()
                        val2 = values.pop()
                        handleOperation(values, val2, val1, op)
                        operators.pop()

                        if value == ')':
                            self.print("Should be '(': " + str(operators.pop()))  # should be opening parenthesis
                if value != ')':
                    operators.append(value)

            else:  # VALUE OR FUNCTION
                if item[1] == 'func':
                    # Remember, item[0] is a string rep of list with entries as [name, <params> , param_num]
                    ftn = self.unpackFunctionList(item[0])
                    ftn_name = ftn[0]
                    self.print(ftn_name)
                    value = self.runFunctionInLogic(ftn_name, ftn[1:len(ftn)-1])

                var = self.findVariable(value)
                if var is not None:  # is the value an existing variable?
                    new_value = var.value
                elif self.temp_variables.get(value) is not None:  # is the value a temporary variable?
                    new_value = self.temp_variables[value]
                else:  # value must be a number or it's undefined
                    if item[1] == 'str':
                        self.print("ERROR: " + str(value) + " is undefined.")
                        raise Exception
                    new_value = float(value)

                values.append(new_value)

        # Handle the remaining operations
        while len(operators) > 0:
            op = operators[-1]
            val1 = values.pop()  # get values to do operation on
            val2 = values.pop()
            handleOperation(values, val2, val1, op)

            operators.pop()  # operation is done

        if len(values) != 1 or len(operators) != 0:
            self.print("Error: len(values) = " + str(len(values)) + " OR len(operators) = " + str(len(operators)))
            raise Exception

        return values[0]

    #
    # HELPERS
    #
    def runFunctionInLogic(self, name, params):
        if not name in self.supportedFunctions:
            self.print(name + " is not supported (yet).")
            raise Exception
        elif name == "der":
            return Der(*params)
        elif name == "int":
            return

    def unpackFunctionList(self, text):
        toBeRemoved = ['[', ']', "'", '"', ' ']
        params = text.split(',')
        self.print("Params (before): " + str(params))
        new_params = []
        for p in params:
            new_param = ''
            for char in p:
                if char in toBeRemoved:
                    p = p.replace(char, '')
            new_param = p
            new_params.append(new_param)

        self.print("Params (after): " + str(new_params))
        return new_params

    def findVariable(self, x):
        return self.dyna_math.findVariable(x)

    def updateVariables(self):
        self.variables = self.dyna_math.variables

    #
    # FOR DEBUG/ERROR
    #
    def print(self, text):
        self.dyna_math.print(text)

#
# STATIC HELPERS
#

def prec(c):
    if c == '+' or c == '-':
        return 1
    elif c == '*' or c == '/':
        return 2
    elif c == '^':
        return 3
    elif c == '(' or c == ')':
        return 4
    return -1


def handleOperation(values, val2, val1, c):
    if c == '+':
        values.append(val2 + val1)
    elif c == '-':
        values.append(val2 - val1)
    elif c == '*':
        values.append(val2 * val1)
    elif c == '/':
        values.append(val2 / val1)
    elif c == '^':
        values.append(val2 ** val1)
