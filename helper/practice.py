import os
from main import Main
from helper.functions import *
from tkinter import messagebox


class Practice:

    def __init__(self, parent: Main):
        # Initialize MongoDB
        self.words = parent.data.get_word_data()
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
        count = self.parent.data.get_remaining_count()
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
            self.current_word[col] = data.strip()

        self.parent.data.insert_one(self.current_word)

        self.current_word = {}
        self.get_word()
