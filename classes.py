import textwrap
import pymongo
import os
import numpy as np
import pandas as pd
from tkinter import *
from tkinter import messagebox
from tkmacosx import Button
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter.simpledialog import askstring


COLUMNS = ["definitions", "syns", "ants", "examples"]
LABELS = [("Definitions", (10, 60)), ("Synonyms", (10, 15)), ("Antonyms", (10, 15)), ("Examples", (10, 60))]
BACKGROUND_COLOR = "#8CF3D4"
HOME_COLOR = "#03fc62"
SELECT_COLOR = "#4FA9EB"
NEXT_COLOR = "#E46060"
ENTER_COLOR = "#BA5CF3"
BUTTON_FONT = ("Ariel", 24, "bold")
CANVAS_FONT = ("Ariel", 40, "italic")

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["gre_"]


def get_widgets(row, col, color, parent, scale):
    text, box_type = LABELS[col]
    label = Label(parent, text=text, bg=color, fg="black", font=("Ariel", 20), width=10)
    label.grid(row=row, column=col, padx=15)
    box = ScrolledText(parent, height=box_type[0]/scale, width=box_type[1], font=("Ariel", 14),
                       bg="white", fg="black", wrap=WORD, insertbackground="black")
    box.grid(row=row + 1, column=col, pady=(20, 60))
    return box


def get_button(frame, text, color, function, row, col, span, pad):
    button = Button(frame, text=text, bg=color, fg="black", font=BUTTON_FONT, borderless=1, command=function)
    button.grid(row=row, column=col, columnspan=span, pady=pad)
    return button


def get_tree(frame, widths, texts, function):
    style = ttk.Style(frame)
    style.theme_use("aqua")
    style.configure("Treeview", background="white", foreground="black", font=("Ariel", 16), rowheight=30)
    style.configure("Treeview.Heading", foreground="white", font=("Ariel", 20), rowheight=60)
    tree = ttk.Treeview(frame, selectmode='browse')
    tree.grid(row=1, column=0, columnspan=4, sticky="news")
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    vsb.grid(row=1, column=3, sticky="nse")

    tree.configure(yscrollcommand=vsb.set)

    tree["columns"] = [str(i+1) for i in range(len(widths))]
    tree['show'] = 'headings'
    for itr, width, text in zip(tree["columns"], widths, texts):
        tree.column(itr, width=width, anchor='c')
        tree.heading(itr, text=text, command=lambda itr_=itr: function(itr_, True))
    tree.tag_configure("blue", background='#b8f7fc')

    return tree, style


def alternate(tree):
    for itr, k in enumerate(tree.get_children('')):
        tree.item(k, tag=("blue" if itr % 2 != 0 else ""))


def wrap_text(array, length):
    if type(array) == str:
        return "\n".join(textwrap.wrap(array, length))
    else:
        return "\n".join(textwrap.wrap("; ".join(array), length))


class Data:

    def __init__(self):
        """
        Class init
        """
        # client = pymongo.MongoClient("mongodb://localhost:27017/")
        # db = client["gre_"]
        self.col = db["words_last_new"]
        self.data = self.get_database()

    def get_database(self):
        df = pd.DataFrame(self.col.find({}, {"_id": 0}))
        df.definitions = df.definitions.str.join("\n")
        df.examples = df.examples.str.join("\n")
        df.syns = df.syns.str.join(", ")
        df.ants = df.ants.str.join(", ")
        return df.astype(object)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        if type(item) == tuple:
            return self.data.loc[item[0]][item[1]]
        else:
            return dict(self.data.loc[item])

    def __setitem__(self, item, value):
        self.data.at[item] = value
        self.col.update_one({"word": self.data["word"][item[0]]}, {"$set": {item[1]: value}})

    def get_counts(self, item):
        return list(self.data[item].value_counts().sort_index().items())

    def get_level_indices(self, level):
        return self.data[self.data.level == level].index.to_numpy()


class Main:

    def __init__(self, window: Tk):
        #
        self.data = Data()

        # TK Constants:
        self.button_data = [[Practice, "#4FA9EB"], [Revise, "#BA5CF3"], [Test, "#E46060"], [QuickTest, "#FFE800"]]

        # Initialize TK Widgets
        self.window = window
        self.frame, canvas = self.init_frames(("Words", "Welcome to the Learning Platform"), None)
        canvas[0].configure(width=750)
        canvas[0].grid(row=0, column=0, columnspan=4, pady=(0, 30))
        canvas[0].move(canvas[1], 125, 0)
        self.init_window()

        # Button
        self.practice_button, self.revise_button, self.test_button, self.quick_test_button = [
            get_button(self.frame, self.button_data[itr][0].__name__, self.button_data[itr][1],
                       lambda itr_=itr: self.button_data[itr_][0](self), 1, itr, 1, (0, 0)) for itr in range(4)]

    def init_window(self):
        self.window.title("GRE Words")
        self.refresh_child(self.frame)

    def init_frames(self, titles, *args):
        self.window.title(f"GRE {titles[0]} Card")
        # Frame
        frame = Frame(self.window, bg=BACKGROUND_COLOR)
        frame.grid(row=0, column=0)

        # Word Header
        canvas = Canvas(frame, width=500, height=50, bg=BACKGROUND_COLOR, highlightthickness=0)
        canvas_title = canvas.create_text(250, 25, text=titles[1], fill="black", font=CANVAS_FONT)
        canvas.grid(row=0, column=0, columnspan=4, pady=(0, 30))

        # Home Button
        if args[0] is not None:
            get_button(frame, "Home", HOME_COLOR, lambda: self.go_home(frame), args[0], args[1], args[2], args[3])

        return frame, (canvas, canvas_title)

    def go_home(self, frame):
        frame.destroy()
        self.init_window()

    def refresh_child(self, frame):
        self.frame.grid_forget()
        frame.grid_forget()
        frame.grid(row=0, column=0)


class Practice:

    def __init__(self, parent: Main):
        # Initialize MongoDB
        self.old_col = db["words_first"]
        self.new_col = db["words_last_new"]
        self.words = self.old_col.find(
            {"learnt": False},
            {"_id": 0, "word": 1, "data": 1})
        self.current_word = {}

        # Initialize TK Widgets
        self.parent = parent
        self.frame, canvas = self.parent.init_frames(("Practice", ""), 5, 0, 2, (0, 0))
        self.canvas, self.canvas_title = canvas

        # Labels and Boxes
        self.select_boxes = [get_widgets(1, i, SELECT_COLOR, self.frame, 1) for i in range(4)]
        self.enter_boxes = [get_widgets(3, i, ENTER_COLOR, self.frame, 1) for i in range(4)]

        # Home and Next Buttons
        self.next_button = get_button(self.frame, "Next", NEXT_COLOR, self.save_word, 5, 2, 2, (0, 0))

        self.get_word()

    def get_word(self):

        word = self.words[0]["word"]
        word_data = self.words[0]["data"]
        self.current_word = {
            "word": word,
            "definitions": "",
            "syns": "",
            "ants": "",
            "examples": "",
            "prompt": "",
            "score": 0,
            "test": 0,
            "marked": False,
            "level": 2
        }

        self.canvas.itemconfig(self.canvas_title, text=f"Word: {word}")
        count = self.old_col.count_documents({"learnt": False})
        self.next_button.configure(text=f"Next ({count})")

        for i, (select_widget, enter_widget, col) in enumerate(zip(self.select_boxes, self.enter_boxes, COLUMNS)):
            select_widget.configure(state="normal")
            select_widget.delete("1.0", "end-1c")
            enter_widget.delete("1.0", "end-1c")
            data = (", " if 0 < i < 3 else "\n").join(word_data[col])
            select_widget.insert("end", data)
            select_widget.configure(state="disabled")
            if data == "":
                if col == "examples":
                    os.system(f"open \"\"https://www.merriam-webster.com/dictionary/{word}#examples")
                elif col == "syns":
                    os.system(f"open \"\"https://www.thesaurus.com/browse/{word}")
                    os.system(f"open \"\"https://www.merriam-webster.com/dictionary/{word}#synonyms")
                elif col == "ants":
                    os.system(f"open \"\"https://www.thesaurus.com/browse/{word}")
        self.parent.refresh_child(self.frame)

    def save_word(self):
        for i, (enter_widget, col) in enumerate(zip(self.enter_boxes, COLUMNS)):
            data = enter_widget.get("1.0", "end-1c")
            if data == "":
                messagebox.showerror("Error", "Enter data in all columns before saving.")
                return
            self.current_word[col] = data.strip().split(", " if 0 < i < 3 else "\n")

        self.old_col.update_one(
            {"word": self.current_word["word"]},
            {"$set": {"learnt": True}}
        )
        self.new_col.insert_one(self.current_word)
        self.current_word = {}
        self.get_word()


class Revise:

    def __init__(self, parent: Main):
        # Initialize MongoDB
        self.col = db["words_last_new"]
        self.words = []
        for data in self.col.find({}, {"_id": 0, "word": 1, "prompt": 1, "score": 1,
                                       "test": 1, "marked": 1, "level": 1}).sort("word", 1):
            self.words.append(list(data.values()))

        # Initialize TK Widgets
        self.parent = parent
        self.frame = self.parent.init_frames(("Revision", "Revision Table"), 2, 2, 1, (50, 0))[0]

        # TreeView
        self.tree, self.style = get_tree(self.frame, (150, 600, 150, 150, 150, 150),
                                         ("Word", "Prompt", "Score", "Tests", "Marked", "Level"), self.sort)
        for itr in range(len(self.words)):
            self.tree.insert("", 'end', text=itr, values=(self.get_values(itr)))
        alternate(self.tree)
        self.tree.bind("<Double-1>", lambda event: self.get_word())

        # Query Button
        get_button(self.frame, "Query", NEXT_COLOR, self.query, 2, 1, 1, (50, 0))

        self.parent.refresh_child(self.frame)

    def new_window(self, text):
        new_window = Toplevel(self.frame)
        new_window.config(padx=50, pady=50, bg=BACKGROUND_COLOR)
        new_window.title(text[0])

        # Word Header
        canvas = Canvas(new_window, width=500, height=50, bg=BACKGROUND_COLOR, highlightthickness=0)
        canvas.create_text(250, 25, text=text[1], fill="black", font=("Ariel", 40, "italic"))
        canvas.grid(row=0, column=0, columnspan=4, pady=(0, 30))

        return new_window

    def query(self):
        new_window = self.new_window(("Word Queries", "Enter Query"))
        self.style.configure("TCombobox", selectbackground='gray')
        box = ttk.Combobox(new_window, font=("Ariel", 16))
        box.grid(row=1, column=0, columnspan=2)
        box["state"] = "readonly"
        box["values"] = ["All", "Score", "Test", "Marked", "Level"]
        box.current(0)
        textbox = ScrolledText(new_window, height=1, width=8, font=("Ariel", 20))
        textbox.grid(row=1, column=2, columnspan=2)
        textbox.tag_configure("centered", justify="center")

        get_button(new_window, "Statistics", NEXT_COLOR, self.statistics, 2, 0, 4, (50, 0))

        def set_value():
            value: str = box.get()
            if value == "All":
                textbox.delete("1.0", "end-1c")
                textbox.insert("end", len(self.words), "centered")
            elif value == "Marked":
                textbox.delete("1.0", "end-1c")
                query = self.col.count_documents({"marked": True})
                textbox.insert("end", query, "centered")
            else:
                textbox.delete("1.0", "end-1c")
                param = int(askstring("Query", f"{value}: "))
                query = self.col.count_documents({value.lower(): param})
                textbox.insert("end", query, "centered")
        box.bind("<<ComboboxSelected>>", lambda event: set_value())
        set_value()

    def statistics(self):
        data = Data()
        new_window = self.new_window(("Word Statistics", "Counts"))

        def get_table(col):
            frame = Frame(new_window, bg=BACKGROUND_COLOR)
            frame.grid(row=1, column=col[0])
            tree, style = get_tree(frame, (150, 150), (col[1].title(), "Counts"), None)
            counts = data.get_counts(col[1])
            for itr, count in enumerate(counts):
                tree.insert("", 'end', text=itr, values=count)
            alternate(tree)

        [get_table((i, col)) for i, col in enumerate(["level", "test"])]

    def sort(self, col, reverse):
        def get_children(parent):
            value = self.tree.set(parent, col)
            if col == "3":
                value = -1 if value == "Not done" else float(value[:-1])
            elif col == "2":
                value = -1 if value == "" else 1
            elif col == "5":
                value = -1 if value == "❌" else 1
            elif col == "4" or col == "6":
                value = int(value)
            if col != "1" and not reverse:
                value *= -1
            return value, self.tree.set(parent, "1"), parent
        children = [get_children(k) for k in self.tree.get_children('')]
        children.sort(reverse=(reverse if col == "1" or (col != "1" and not reverse) else (not reverse)))
        for index, (val1, val2, k) in enumerate(children):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda itr_=col: self.sort(itr_, not reverse))
        alternate(self.tree)

    def get_values(self, itr):
        word, prompt, score, test, marked, level = self.words[itr]
        final_score = "Not done" if test == 0 else f"{round(score / test * 100, 2)}%"
        return word, prompt, final_score, test, "❌" if marked else "", level

    def get_word(self):
        tree_item = self.tree.selection()[0]
        item = self.tree.item(tree_item, "text")
        word, prompt, score, test, marked, level = self.get_values(item)
        word_data = self.col.find_one({"word": word}, {"_id": 0, "definitions": 1, "syns": 1, "ants": 1, "examples": 1})
        new_window = self.new_window(("Word Revision", f"Word: {word}"))

        # Labels and Boxes
        select_boxes = [get_widgets(1, i, SELECT_COLOR, new_window, 2) for i in range(4)]
        for i, (select_widget, col) in enumerate(zip(select_boxes, COLUMNS)):
            select_widget.delete("1.0", "end-1c")
            data = (", " if 0 < i < 3 else "\n").join(word_data[col])
            select_widget.insert("end", data)
            select_widget.configure(state="disabled")

        # Frame
        frame = Frame(new_window, bg=BACKGROUND_COLOR)
        frame.grid(row=3, column=0, columnspan=4)

        def get_input_gui(row, label_text, box_text):
            label = Label(frame, text=label_text, bg=SELECT_COLOR, fg="black", font=("Ariel", 20), width=10)
            label.grid(row=row, column=0, padx=100)
            box = ScrolledText(frame, height=1, width=60, font=("Ariel", 14), bg="white",
                               fg="black", wrap=WORD, insertbackground="black")
            box.grid(row=row, column=1, columnspan=2)
            box.tag_configure("centered", justify="center")
            box.delete("1.0", "end-1c")
            box.insert("end", box_text, "centered")
            return box

        prompt_box, level_box = get_input_gui(0, "Prompt", prompt), get_input_gui(1, "Level", level)

        # Save Button
        save_button = get_button(frame, "Close", NEXT_COLOR, self.query, 0, 3, 1, (0, 0))
        save_button.configure(width=200, padx=100)

        def detect_change():
            new_prompt, new_level = prompt_box.get("1.0", "end-1c"), level_box.get("1.0", "end-1c")
            prompt_box.tag_add("centered", 1.0, "end")
            level_box.tag_add("centered", 1.0, "end")
            if new_prompt == prompt and new_level == level:
                save_button.configure(text="Close", width=100)
            else:
                save_button.configure(text="Save n Close", width=200)
            pass

        def save_prompt():
            if save_button['text'] != "Close":
                new_prompt, new_level = prompt_box.get("1.0", "end-1c"), level_box.get("1.0", "end-1c")
                self.words[item][1] = new_prompt
                self.words[item][5] = new_level
                self.col.update_one({"word": word}, {"$set": {"prompt": new_prompt, "level": int(new_level)}})
                self.tree.item(tree_item, text=item, values=(word, new_prompt, score, test, marked, new_level))
            new_window.destroy()
            self.parent.window.focus_set()

        prompt_box.bind("<KeyRelease>", lambda event: detect_change())
        level_box.bind("<KeyRelease>", lambda event: detect_change())
        save_button.configure(command=save_prompt)


class Test:

    def __init__(self, parent: Main):
        parent.init_window()
        self.test_type = messagebox.askyesno("Test Type", "Questions should be definitions?")
        self.hide = messagebox.askyesno("Test Type", "Options should be hidden?")
        self.check_hide = False
        try:
            words_num = int(askstring("Test Specs", "Enter no. of questions you wish to answer:"))
            if words_num > 0:
                parent.frame.grid_forget()
            else:
                messagebox.showerror("Error", "Enter number greater than 0.")
                return
        except (TypeError, ValueError):
            messagebox.showerror("Error", "Enter a valid number.")
            return

        # Initialize MongoDB
        self.col = db["words_last_new"]
        self.words_num = words_num
        self.words = []
        self.options = []
        self.options_order = []
        self.report = []
        self.marked = []
        self.itr = 0
        self.formulate()

        # Initialize TK Widgets
        self.parent = parent
        self.frame, canvas = self.parent.init_frames(("Test", ""), 3, 0, 2, (30, 0))
        self.canvas, self.canvas_title = canvas
        if self.test_type:
            self.canvas.configure(width=750, height=90)
            self.canvas.itemconfig(self.canvas_title, font=("Ariel", 24, "bold"))
            self.canvas.move(self.canvas_title, 125, 20)

        # Labels and Boxes
        self.option_choice = IntVar()
        self.radio_buttons = [self.get_radio_buttons(itr) for itr in range(4)]

        # Next Buttons
        self.check_button = get_button(self.frame, "Show", NEXT_COLOR, self.check, 3, 2, 2, (30, 0))
        if self.hide:
            self.mark_button = get_button(self.frame, "?", "#ffa500", self.mark, 3, 1, 2, (30, 0))
            self.mark_button.configure(width=30)
            self.check_hide = True
        else:
            self.show()

        self.get_word()
        self.parent.refresh_child(self.frame)

    def show(self):
        for i in range(4):
            self.radio_buttons[i].grid(row=(i % 2) + 1, column=(i // 2) + 1, sticky="e")
        self.check_hide = False
        self.check_button.configure(text="Check")

    def get_radio_buttons(self, i):
        radio_button = Radiobutton(self.frame, text="", variable=self.option_choice, value=i, width=50, height=3,
                                   bg=BACKGROUND_COLOR, fg="black", font=("Ariel", 20))
        return radio_button

    def formulate(self):
        all_words: list[dict] = list(self.col.find({}, {"_id": 0, "word": 1, "definitions": 1,
                                                        "score": 1, "test": 1, "marked": 1}))
        length = len(all_words)
        indexes = np.arange(length).reshape(length, 1)
        test_arr = np.array([data["test"]*2-int(data["marked"]) for data in all_words]).reshape(length, 1)
        cat_arr = np.concatenate((indexes, test_arr), axis=1)
        srt_arr = np.sort(cat_arr.view('i8,i8'), order=['f1', 'f0'], axis=0).view(int)
        uv, ind = np.unique(srt_arr[:, 1], return_index=True)
        spt_arr = np.split(srt_arr[:, 0], ind[1:])
        order = np.concatenate([np.random.permutation(seq) for seq in spt_arr])[:self.words_num]

        for index in order:
            word_data = all_words[index]
            self.words.append(word_data)
            options = [word_data["word" if self.test_type else "definitions"]]
            others = np.random.choice(np.delete(indexes, index), size=3, replace=False)
            options.extend([all_words[idx]["word" if self.test_type else "definitions"] for idx in others])
            self.marked.append(False)
            self.options.append(options)

    def mark(self):
        self.marked[self.itr] = True
        if self.check_hide:
            self.show()
        else:
            self.check()

    def get_word(self):
        current_word_data = self.words[self.itr]
        question = current_word_data["definitions" if self.test_type else "word"]
        self.canvas.itemconfig(self.canvas_title, text=f"Question {self.itr+1}: {wrap_text(question, 50)}")
        self.options_order = np.arange(4)
        np.random.shuffle(self.options_order)
        for itr, option_itr in enumerate(self.options_order):
            self.radio_buttons[itr].configure(text=wrap_text(self.options[self.itr][option_itr], 75))
            if self.hide:
                self.radio_buttons[itr].grid_forget()
                self.check_hide = True
                self.check_button.configure(text="Check")

    def check(self):
        if self.check_hide:
            self.show()
            return
        self.report.append(self.options_order[self.option_choice.get()])
        self.itr += 1
        if self.itr == self.words_num:
            self.frame.destroy()
            TestReport(self)
        else:
            self.get_word()


class TestReport:

    def __init__(self, parent: Test):
        # Initialize MongoDB
        self.col = db["words_last_new"]

        # Initialize TK Widgets
        self.parent = parent
        self.frame = self.parent.parent.init_frames(("Test Report", "Report"), 2, 0, 4, (50, 0))[0]

        # TreeView
        sizes = (600, 60, 200, 200, 150) if self.parent.test_type else (150, 60, 600, 600, 150)
        self.tree, style = get_tree(self.frame, sizes, ("Word", "Score", "Your Answer",
                                                        "Correct Answer", "Marked"), self.sort)
        style.configure("Treeview", rowheight=60)
        self.set_report()

        self.parent.parent.refresh_child(self.frame)

    def sort(self, col, reverse):
        def get_children(parent):
            value = self.tree.set(parent, col)
            if col == "2" or col == "5":
                value = 1 if value != "❌" else -1
                if reverse:
                    value *= -1
            return value, self.tree.set(parent, "4"), parent
        children = [get_children(k) for k in self.tree.get_children('')]
        children.sort(reverse=(reverse if col == "1" or (col != "1" and not reverse) else (not reverse)))
        for index, (val1, val2, k) in enumerate(children):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda itr_=col: self.sort(itr_, not reverse))
        alternate(self.tree)

    def set_report(self):
        for itr, (word, options, report) in enumerate(zip(self.parent.words, self.parent.options, self.parent.report)):
            check = "✅" if report == 0 else "❌"
            mark = "❌" if self.parent.marked[itr] else ""
            values = (wrap_text(word["definitions" if self.parent.test_type else "word"], 75),
                      check, wrap_text(options[report], 75), wrap_text(options[0], 75), mark)
            self.tree.insert("", 'end', values=values, tag=("blue" if itr % 2 != 0 else ""))
            self.col.update_one({"word": word["word"]}, {"$inc": {"score": 1 if report == 0 else 0, "test": 1},
                                                         "$set": {"marked": self.parent.marked[itr]}})


class QuickTest:

    def __init__(self, parent: Main):
        parent.init_window()
        try:
            level = int(askstring("Test Specs", "Enter level of words:"))
            if 0 < level < 6:
                parent.frame.grid_forget()
            else:
                messagebox.showerror("Error", "Enter number in the range 1-5.")
                return
        except (TypeError, ValueError):
            messagebox.showerror("Error", "Enter a valid number.")
            return

        self.num_options = 4
        self.test_type = False
        if level > 2:
            self.test_type = messagebox.askyesno("Test Type", "Questions should be definitions?")
            self.num_options = 1
        elif level == 3:
            self.test_type = True

        # Initialize MongoDB
        self.col = db["words_last_new"]
        self.parent = parent
        self.level = level
        self.words = []
        self.word_indices = []
        self.options = []
        self.itr = 0
        self.total = 0
        self.check_hide = True
        self.check_next = True
        self.formulate()
        if self.total == 0:
            messagebox.showerror("Error", "No words with that level.")
            parent.init_window()
            return

        # Initialize TK Widgets
        self.frame, canvas = self.parent.init_frames(("Test", ""), None)
        self.canvas, self.canvas_title = canvas
        if self.test_type:
            self.canvas.configure(width=750, height=90)
            self.canvas.itemconfig(self.canvas_title, font=("Ariel", 24, "bold"))
            self.canvas.move(self.canvas_title, 125, 20)

        # Label
        self.label = Label(self.frame, text="Remaining words: ", bg=BACKGROUND_COLOR, fg="black", font=("Ariel", 16))

        # Options
        self.option_frame = Frame(self.frame, bg=BACKGROUND_COLOR)
        self.option_choice = IntVar()
        self.options_order = np.array([])
        self.radio_buttons = [self.get_radio_buttons(itr) for itr in range(self.num_options)]

        # Buttons
        self.show_button = get_button(self.frame, "Show", NEXT_COLOR, self.show, 3, 1, 1, (30, 0))

        self.button_frame = Frame(self.frame, bg=BACKGROUND_COLOR)
        self.dec_button = get_button(self.button_frame, "Decrement", "#ffa500", lambda: self.next(-1), 0, 0, 1, (0, 0))
        self.keep_button = get_button(self.button_frame, "Keep", NEXT_COLOR, lambda: self.next(0), 0, 1, 1, (0, 0))
        self.inc_button = get_button(self.button_frame, "Increment", "#ffa500", lambda: self.next(1), 0, 2, 1, (0, 0))

        # Grids
        if 2 < self.level < 5:
            column_span = 3
        else:
            column_span = 4

        self.canvas.grid(row=0, column=0, columnspan=column_span, pady=(0, 30))
        self.label.grid(row=1, column=0, columnspan=column_span, pady=(0, 30))
        self.option_frame.grid(row=2, column=0, columnspan=column_span, pady=(30, 0))
        self.show_button.grid(row=3, column=0, columnspan=column_span, pady=(30, 0))
        self.button_frame.grid(row=4, column=0, columnspan=column_span, pady=(30, 0))

        self.frame.bind_all("<KeyRelease>", self.key_press)
        # Init functions
        self.get_word()
        self.parent.refresh_child(self.frame)

    def get_radio_buttons(self, i):
        radio_button = Radiobutton(self.option_frame, text="", variable=self.option_choice, value=i, width=50, height=3,
                                   bg=BACKGROUND_COLOR, fg="black", font=("Ariel", 20))
        return radio_button

    def formulate(self):
        self.parent.data = Data()
        length = len(self.parent.data)
        indexes = np.arange(length).reshape(length, 1)
        self.word_indices = self.parent.data.get_level_indices(self.level)
        self.total = len(self.word_indices)
        np.random.shuffle(self.word_indices)
        for index in self.word_indices:
            word_data = self.parent.data[index]
            self.words.append(word_data)
            options = [word_data["word" if self.test_type else "definitions"]]
            if self.level < 3:
                others = np.random.choice(np.delete(indexes, index), size=3, replace=False)
                options.extend([self.parent.data[idx, ("word" if self.test_type else "definitions")] for idx in others])
            self.options.append(options)

    def hide(self):
        self.dec_button.grid_forget()
        self.keep_button.grid_forget()
        self.inc_button.grid_forget()
        for itr in range(self.num_options):
            self.radio_buttons[itr].grid_forget()
        self.check_hide = True
        self.check_next = True

    def get_word(self):
        self.hide()
        self.label.configure(text=f"Remaining words: {self.total-self.itr-1}")
        current_word_data = self.words[self.itr]
        question = current_word_data["definitions" if self.test_type else "word"]
        self.canvas.itemconfig(self.canvas_title, text=f"Question {self.itr+1}: {wrap_text(question, 50)}")
        self.options_order = np.arange(self.num_options)
        np.random.shuffle(self.options_order)
        for itr, option_itr in enumerate(self.options_order):
            self.radio_buttons[itr].configure(text=wrap_text(self.options[self.itr][option_itr], 75))

    def show(self):
        if self.check_hide:
            for i in range(self.num_options):
                self.radio_buttons[i].grid(row=(i % 2) + 1, column=(i // 2) + 1, sticky="e")
            self.dec_button.grid(row=0, column=0)
            self.keep_button.grid(row=0, column=1)
            if self.level != 5:
                self.inc_button.grid(row=0, column=2)
            self.check_hide = False
        elif self.check_next:
            self.toggle_option(True)
            self.check_next = False
        else:
            self.next(0)

    def toggle_option(self, highlight):
        itr = np.where(self.options_order == 0)[0][0]
        if highlight:
            self.radio_buttons[itr].configure(bg="white")
        else:
            self.radio_buttons[itr].configure(bg=BACKGROUND_COLOR)

    def next(self, change):
        self.toggle_option(False)
        if change != 0:
            self.parent.data[self.word_indices[self.itr], "level"] += change
        self.itr += 1
        if self.itr == self.total:
            self.frame.unbind_all("<KeyRelease>")
            self.parent.go_home(self.frame)
        else:
            self.get_word()

    def key_press(self, event):
        if event.char != "" and event.char in "awd":
            if self.check_hide:
                self.show()
            elif event.char == "w":
                self.next(0)
            elif event.char == "d":
                self.next(1)
            else:
                self.next(-1)
