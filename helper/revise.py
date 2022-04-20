from main import Main, Data
from helper.functions import *
from tkinter.simpledialog import askstring


class Revise:

    def __init__(self, parent: Main):
        # Initialize MongoDB
        self.col = parent.db["words_last_new"]
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