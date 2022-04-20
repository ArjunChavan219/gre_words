import numpy as np
from main import Main
from helper.functions import *
from tkinter import messagebox
from tkinter.simpledialog import askstring


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
        self.words_num = words_num
        self.words = []
        self.word_indices = []
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
        length = len(self.parent.data)
        indexes = np.arange(length).reshape(length, 1)
        test_arr = (self.parent.data.test*2 - self.parent.data.marked).to_numpy().reshape(length, 1)
        cat_arr = np.concatenate((indexes, test_arr), axis=1)
        srt_arr = np.sort(cat_arr.view('i8,i8'), order=['f1', 'f0'], axis=0).view(int)
        uv, ind = np.unique(srt_arr[:, 1], return_index=True)
        spt_arr = np.split(srt_arr[:, 0], ind[1:])
        self.word_indices = np.concatenate([np.random.permutation(seq) for seq in spt_arr])[:self.words_num]

        for index in self.word_indices:
            word_data = self.parent.data[index]
            self.words.append(word_data)
            options = [word_data["word" if self.test_type else "definitions"]]
            others = np.random.choice(np.delete(indexes, index), size=3, replace=False)
            options.extend([self.parent.data[idx, ("word" if self.test_type else "definitions")] for idx in others])
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
            from helper.test_report import TestReport
            TestReport(self)
        else:
            self.get_word()
