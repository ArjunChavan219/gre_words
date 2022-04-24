from main import Main
from helper.functions import *
from helper.tags import Graph
from tkinter.simpledialog import askstring


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

    def statistics(self):
        new_window = self.new_window(("Word Statistics", "Counts"))

        def get_table(col):
            frame = Frame(new_window, bg=BACKGROUND_COLOR)
            frame.grid(row=1, column=col[0])
            tree, style = get_tree(frame, (150, 150), (col[1].title(), "Counts"), None)
            counts = self.parent.data.get_counts(col[1])
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
        word, prompt, score, test, marked, level, tag = self.words[itr]
        final_score = "Not done" if test == 0 else f"{round(score / test * 100, 2)}%"
        return word, prompt, final_score, test, "❌" if marked else "", level, tag

    def get_word(self):
        if len(self.tree.selection()) == 0:
            return
        tree_item = self.tree.selection()[0]
        self.tree.selection_remove(tree_item)
        item = self.tree.item(tree_item, "text")
        word, prompt, score, test, marked, level, tag = self.get_values(item)
        word_index = self.parent.data.get_index(word)
        word_data = self.parent.data[word_index]
        new_window = self.new_window(("Word Revision", f"Word: {word}"))

        # Labels and Boxes
        select_boxes = [get_widgets(1, i, SELECT_COLOR, new_window, 2) for i in range(4)]
        for i, (select_widget, col) in enumerate(zip(select_boxes, COLUMNS)):
            select_widget.delete("1.0", "end-1c")
            select_widget.insert("end", word_data[col])
            select_widget.configure(state="disabled")

        # Frame
        frame = Frame(new_window, bg=BACKGROUND_COLOR)
        frame.grid(row=3, column=0, columnspan=4)

        def detect_change(gui, data):
            new_change = gui[0].get("1.0", "end-1c")
            gui[0].tag_add("centered", 1.0, "end")
            if new_change == data:
                gui[1].grid_forget()
            else:
                gui[1].grid(row=0, column=3, columnspan=1)

        def save_change(gui, itr, key):
            new_change = gui[0].get("1.0", "end-1c")
            self.words[item][itr] = new_change
            self.parent.data[word_index, key] = new_change if key != "level" else int(new_change)
            self.tree.item(tree_item, text=item, values=self.get_values(item))

        def get_input_gui(row: int, label_text: str, box_text: str, index: int):
            gui_frame = Frame(frame, bg=BACKGROUND_COLOR)
            gui_frame.grid(row=row, column=0, columnspan=4, pady=(0, 10))
            label = Label(gui_frame, text=label_text, bg=SELECT_COLOR, fg="black", font=("Ariel", 20), width=10)
            label.grid(row=0, column=0, padx=100)
            box = ScrolledText(gui_frame, height=1, width=60, font=("Ariel", 14), bg="white",
                               fg="black", wrap=WORD, insertbackground="black")
            box.grid(row=0, column=1, columnspan=2, padx=(0, 50))
            box.tag_configure("centered", justify="center")
            box.delete("1.0", "end-1c")
            box.insert("end", box_text, "centered")
            button = get_button(gui_frame, f"Save {label_text}", "#BA5CF3", self.query, 0, 3, 1, (0, 10))
            box.bind("<KeyRelease>", lambda event: detect_change((box, button), box_text))
            button.configure(width=200, padx=50, font=("Ariel", 22),
                             command=lambda: save_change((box, button), index, label_text.lower()))
            button.grid_forget()
            return box, button

        def close_window():
            new_window.destroy()
            self.parent.window.focus_set()

        def next_window():
            new_window.destroy()
            next_item = self.tree.next(tree_item)
            if next_item != "":
                self.tree.selection_set(next_item)
                self.get_word()
            else:
                self.parent.window.focus_set()

        entries = [("Prompt", prompt, 1), ("Level", level, 5), ("Tag", tag, 6)]
        prompt_gui, level_gui, tag_gui = [get_input_gui(i, *entry) for i, entry in enumerate(entries)]
        graph = Graph(self.new_window, word, tag_gui, detect_change, self.parent.data.tags)
        tag_gui[0].configure(state="disabled")
        tag_gui[0].bind("<Double-1>",
                        lambda event: graph())

        # Buttons
        button_frame = Frame(frame, bg=BACKGROUND_COLOR)
        button_frame.grid(row=4, column=0, columnspan=4)
        get_button(button_frame, "Close", "#4FA9EB", close_window, 0, 1, 1, (25, 0))
        get_button(button_frame, "Next", NEXT_COLOR, next_window, 0, 2, 1, (25, 0))
