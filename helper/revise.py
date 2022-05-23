from main import Main
from helper.functions import *
from helper.tags import Graph
from tkinter.simpledialog import askstring


def close(old_window, new_window):
    old_window.destroy()
    new_window.focus_set()


class Revise:

    def __init__(self, parent: Main):
        # Initialize MongoDB
        self.words = parent.data.get_revised_list()

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
        place_window(self.parent.window, 1400, 600)

    def new_window(self, text):
        new_window = Toplevel(self.frame)
        new_window.config(padx=25, pady=50, bg=BACKGROUND_COLOR)
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

        get_button(new_window, "Statistics", NEXT_COLOR, lambda: self.statistics(new_window), 2, 0, 2, (50, 0))
        get_button(new_window, "Close", NEXT_COLOR, lambda: close(new_window, self.parent.window), 2, 2, 2, (50, 0))

        def set_value():
            value: str = box.get()
            if value == "All":
                query = len(self.words)
            elif value == "Marked":
                query = self.parent.data.get_count("marked", True)
            else:
                param = int(askstring("Query", f"{value}: "))
                query = self.parent.data.get_count(value.lower(), param)
            textbox.delete("1.0", "end-1c")
            textbox.insert("end", query, "centered")

        box.bind("<<ComboboxSelected>>", lambda event: set_value())
        set_value()
        place_window(new_window, 525, 300)

    def statistics(self, old_window):
        new_window = self.new_window(("Word Statistics", "Counts"))

        def get_table(col):
            frame = Frame(new_window, bg=BACKGROUND_COLOR)
            frame.grid(row=1, column=col[0])
            tree, style = get_tree(frame, (150, 150), (col[1].title(), "Counts"), None)
            counts = self.parent.data.get_counts(col[1])
            for itr, count in enumerate(counts):
                tree.insert("", 'end', text=itr, values=count)
            alternate(tree)
            tree.configure(height=5)

        [get_table((i, col)) for i, col in enumerate(["level", "test"])]
        get_button(new_window, "Close", NEXT_COLOR, lambda: close(new_window, old_window), 2, 0, 4, (50, 0))

        place_window(new_window, 650, 450)

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
        word, prompt, score, test, marked, level, tag = self.words[itr]
        final_score = "Not done" if test == 0 else f"{round(score / test * 100, 2)}%"
        return word, prompt, final_score, test, "❌" if marked else "", level, tag

    def get_word(self):
        if len(self.tree.selection()) == 0:
            return
        ReviseTab(self)


class ReviseTab:

    def __init__(self, parent: Revise):
        self.tree_item = parent.tree.selection()[0]
        parent.tree.selection_remove(self.tree_item)
        self.item = parent.tree.item(self.tree_item, "text")
        word, prompt, score, test, marked, level, tag = parent.get_values(self.item)
        self.word_index = parent.parent.data.get_index(word)
        word_data = parent.parent.data[self.word_index]
        self.new_window = parent.new_window(("Word Revision", f"Word: {word}"))
        self.parent = parent

        # Labels and Boxes
        select_boxes = [get_widgets(1, i, SELECT_COLOR, self.new_window, 2) for i in range(4)]
        for i, (select_widget, col) in enumerate(zip(select_boxes, COLUMNS)):
            select_widget.delete("1.0", "end-1c")
            select_widget.insert("end", word_data[col])
            select_widget.configure(state="disabled")

        # Frame
        self.frame = Frame(self.new_window, bg=BACKGROUND_COLOR)
        self.frame.grid(row=3, column=0, columnspan=4)

        self.entries = [("Prompt", prompt, 1), ("Level", level, 5), ("Tag", tag, 6)]
        self.guis, self.texts = [self.get_input_gui(i) for i in range(3)], [prompt, str(level), str(tag)]
        self.is_any_changed = False
        if prompt == "":
            self.guis[0].focus_set()
        self.graph = Graph(parent.new_window, word, self.guis[2], lambda: self.detect_change(2, "Tab"),
                           parent.parent.data, parent.parent.window, self.new_window)
        self.guis[2].configure(state="disabled")
        self.guis[2].bind("<Button-1>", lambda event: self.graph())

        # Buttons
        button_frame = Frame(self.frame, bg=BACKGROUND_COLOR)
        button_frame.grid(row=4, column=0, columnspan=4)
        get_button(button_frame, "Close", "#4FA9EB", lambda: close(self.new_window, self.parent.parent.window),
                   0, 1, 1, (25, 0))
        self.next_button = get_button(button_frame, "Next", "#BA5CF3", self.next_window, 0, 2, 1, (25, 0))
        place_window(self.new_window, 1500, 560)

    def detect_change(self, itr, event):
        if event != "Tab":
            self.texts[itr] = self.guis[itr].get("1.0", "end-1c")
            self.guis[itr].tag_add("centered", 1.0, "end")
        elif itr != 2:
            self.guis[itr].delete("1.0", "end-1c")
            self.guis[itr].insert("end", self.texts[itr], "centered")
        else:
            self.texts[itr] = self.guis[itr].get("1.0", "end-1c")
        self.is_any_changed = sum([self.texts[i].strip() != str(self.entries[i][1]) for i in range(3)]) > 0
        if self.is_any_changed:
            self.next_button.configure(text="Save and Next")
        else:
            self.next_button.configure(text="Next")
        if event == "Tab":
            if itr == 0:
                self.guis[1].focus_set()
            elif itr == 1:
                self.graph()
            else:
                if self.is_any_changed:
                    self.next_button.focus_set()

    def get_input_gui(self, row: int):
        gui_frame = Frame(self.frame, bg=BACKGROUND_COLOR)
        gui_frame.grid(row=row, column=0, columnspan=4, pady=(0, 10))
        label = Label(gui_frame, text=self.entries[row][0], bg=SELECT_COLOR, fg="black", font=("Ariel", 20), width=10)
        label.grid(row=0, column=0, padx=100)
        box = ScrolledText(gui_frame, height=1, width=60, font=("Ariel", 14), bg="white",
                           fg="black", wrap=WORD, insertbackground="black")
        box.grid(row=0, column=1, columnspan=2, padx=(0, 50))
        box.tag_configure("centered", justify="center")
        box.delete("1.0", "end-1c")
        box.insert("end", self.entries[row][1], "centered")
        box.bind("<KeyRelease>", lambda event: self.detect_change(row, event.keysym))
        return box

    def next_window(self):
        for i, entry in enumerate(self.entries):
            new_change = self.guis[i].get("1.0", "end-1c").strip()
            if new_change != self.entries[i][1]:
                key = entry[0].lower()
                self.guis[i].delete("1.0", "end-1c")
                self.guis[i].insert("end", new_change, "centered")
                self.parent.words[self.item][entry[-1]] = new_change
                self.parent.parent.data[self.word_index, key] = new_change if key != "level" else int(new_change)
                self.parent.tree.item(self.tree_item, text=self.item, values=self.parent.get_values(self.item))
                if i == 2:
                    self.parent.parent.data.tag_change = True
        close(self.new_window, self.parent.parent.window)
        next_item = self.parent.tree.next(self.tree_item)
        if next_item != "":
            self.parent.tree.selection_set(next_item)
            self.parent.get_word()
