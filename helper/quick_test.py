import numpy as np
from main import Main
from helper.functions import *
from tkinter import messagebox
from tkinter.simpledialog import askstring


class QuickTest:

    def __init__(self, parent: Main):
        parent.init_window()
        self.ranged = messagebox.askyesno("Test Type", "Words should be ranged?")
        try:
            if self.ranged:
                start, end = askstring("Test Specs", "Enter range of words:").split(":")
                start, end = int(start), int(end)
                if start < end:
                    parent.frame.grid_forget()
                    self.level = 3
                    self.range = np.arange(start, end)
                else:
                    messagebox.showerror("Error", "Invalid range.")
                    return
            else:
                self.level = int(askstring("Test Specs", "Enter level of words:"))
                if 0 < self.level < 6:
                    parent.frame.grid_forget()
                else:
                    messagebox.showerror("Error", "Enter number in the range 1-5.")
                    return
        except (TypeError, ValueError):
            messagebox.showerror("Error", "Enter a valid number.")
            return
        except AttributeError:
            messagebox.showerror("Error", "Enter a valid range.")
            return

        self.num_options = 4
        self.test_type = False
        if self.level > 1:
            self.test_type = messagebox.askyesno("Test Type", "Questions should be definitions?")
            self.num_options = 1

        # Initialize MongoDB
        # self.col = parent.db["words_last_new"]
        self.parent = parent
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
        for i in range(self.num_options):
            self.radio_buttons[i].grid(row=(i % 2) + 1, column=(i // 2) + 1, sticky="e")

        # Buttons
        self.show_button = get_button(self.frame, "Show", NEXT_COLOR, self.show, 3, 1, 1, (30, 0))

        self.button_frame = Frame(self.frame, bg=BACKGROUND_COLOR)
        self.dec_button = get_button(self.button_frame, "Decrement", "#ffa500", lambda: self.next(-1), 0, 0, 1, (0, 0))
        self.keep_button = get_button(self.button_frame, "Keep", NEXT_COLOR, lambda: self.next(0), 0, 1, 1, (0, 0))
        self.inc_button = get_button(self.button_frame, "Increment", "#ffa500", lambda: self.next(1), 0, 2, 1, (0, 0))
        if self.ranged:
            self.dec_button.grid_forget()
            self.inc_button.grid_forget()
            self.keep_button.configure(text="Next")
        elif self.level == 1:
            self.dec_button.grid_forget()
        elif self.level == 5:
            self.inc_button.grid_forget()

        # Grids
        self.column_span = 3 if 1 < self.level < 5 else 4
        self.canvas.grid(row=0, column=0, columnspan=self.column_span, pady=(0, 30))
        self.label.grid(row=1, column=0, columnspan=self.column_span, pady=(0, 30))
        self.show_button.grid(row=3, column=0, columnspan=self.column_span, pady=(30, 0))
        self.option_frame.grid(row=2, column=0, columnspan=self.column_span, pady=(30, 0))
        self.button_frame.grid(row=4, column=0, columnspan=self.column_span, pady=(30, 0))

        self.frame.bind_all("<KeyRelease>", self.key_press)
        # Init functions
        self.get_word()
        self.parent.refresh_child(self.frame)
        self.parent.window.focus_set()

    def get_radio_buttons(self, i):
        radio_button = Radiobutton(self.option_frame, text="", variable=self.option_choice, value=i, width=50, height=3,
                                   bg=BACKGROUND_COLOR, fg="black", font=("Ariel", 20))
        return radio_button

    def formulate(self):
        length = len(self.parent.data)
        indexes = np.arange(length).reshape(length, 1)
        self.word_indices = self.range if self.ranged else self.parent.data.get_level_indices(self.level)
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
        self.option_frame.grid_forget()
        self.button_frame.grid_forget()
        self.check_hide = True
        self.check_next = True
        if self.test_type:
            place_window(self.parent.window, 800, 340)
        else:
            place_window(self.parent.window, 550, 365)

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
            self.option_frame.grid(row=2, column=0, columnspan=self.column_span, pady=(30, 0))
            self.button_frame.grid(row=4, column=0, columnspan=self.column_span, pady=(30, 0))
            self.check_hide = False
            if self.test_type:
                place_window(self.parent.window, 800, 520)
            else:
                place_window(self.parent.window, 1365, 555)
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
