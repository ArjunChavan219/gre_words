import numpy as np
from helper.functions import *
from tkinter import messagebox


class Tags:

    def __init__(self, data, words_data, leaves_data):
        self.tree = {}
        self.get_tree({"Tags": data}, "Tags", "Tags")
        self.words = words_data
        self.leaves = leaves_data

    def get_children(self, parent):
        return [child.split(".")[-1] for child in self.tree[parent]]

    def get_words(self, leaf):
        return self.leaves[leaf]

    def get_tree(self, tags, header, root):
        children = tags[root]
        if children is None:
            self.tree[header] = []
        else:
            self.tree[header] = [header + "." + key for key in children]
            for child in children:
                self.get_tree(children, header + "." + child, child)


class Graph:

    def __init__(self, window_function, word, gui, change_function, tags: Tags, main_window, parent_window):
        self.main_window = main_window
        self.parent_window = parent_window
        self.w_factor, self.h_factor = 65, 65
        self.x_pad, self.y_pad = 15, 5

        self.h_nodes, self.width, self.height = None, None, None
        self.stack, self.children = None, None
        self.selected_gui = (-1, -1)
        self.spaces = []

        self.word = word
        self.window_function = window_function
        self.change_function = change_function
        self.tags = tags
        self.gui = gui
        self.current_tag = self.tags.words[word]
        self.selected = "Tags." + self.current_tag

    def __call__(self):
        self.window = self.window_function(("Word Tags", f"Word: {self.word}"))
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.canvas = Canvas(self.window, background="#8CF3D4")
        self.canvas.grid(row=2, column=0, columnspan=4)

        button_frame = Frame(self.window, bg=BACKGROUND_COLOR)
        button_frame.grid(row=4, column=0, columnspan=4)
        get_button(button_frame, "Close", NEXT_COLOR, self.close_window, 0, 0, 1, (25, 0))
        self.save_button = get_button(button_frame, "Save n Close", "#4FA9EB", self.save, 0, 1, 1, (25, 0))
        self.save_button.grid_forget()

        self.update(self.selected)

    def save(self):
        self.gui[0].configure(state='normal')
        self.gui[0].delete("1.0", "end-1c")
        self.gui[0].insert("end", self.selected[5:], "centered")
        self.gui[0].configure(state='disabled')
        self.close_window()

    def close_window(self):
        self.change_function(self.gui, self.current_tag, "Tab")
        self.window.destroy()

    def update(self, tag):
        self.stack = ["Tags"]
        if tag != "" and tag != "Tags":
            self.stack = tag.split(".")[:-1]
        self.children = sorted(self.tags.get_children(".".join(self.stack)), key=lambda a: (-len(a), a))

        self.canvas.delete("all")
        self.h_nodes = len(self.stack) + 1.5 + (1 if len(self.children) >= 2 else 0)
        self.spaces = np.cumsum(np.char.str_len(self.children) * 12 + 3)
        self.width = self.spaces[-1] + self.w_factor + 2*self.x_pad
        self.spaces[1:] = self.spaces[:-1]
        self.spaces[0] = 0
        self.spaces += self.w_factor
        self.height = self.h_factor * self.h_nodes
        self.canvas.configure(width=self.width, height=self.height)

        self.display()

    def hover(self, gui, enter):
        if enter:
            color = ("white", "red")
        elif gui == self.selected_gui:
            color = ("white", "#8800C7")
        else:
            color = ("black", "#FFED31")
        self.canvas.itemconfigure(gui[0], fill=color[0])
        self.canvas.itemconfigure(gui[1], fill=color[1])

    def click(self, gui, identifier):
        if identifier[1] != "parent":
            tag = ".".join(self.stack) + "." + self.children[identifier[0]]
            children = self.tags.get_children(tag)
            if len(children) == 0:
                words = self.tags.get_words(tag[5:])
                confirm = messagebox.askyesno("Confirm", f"It has the following words:\n{wrap_text(words, 60)}")
                self.main_window.focus_set()
                self.parent_window.focus_set()
                self.window.focus_set()
                if confirm:
                    self.selected = tag
                    old_gui = self.selected_gui
                    self.selected_gui = gui
                    self.hover(old_gui, False)
                    self.hover(self.selected_gui, False)
                    if self.selected[5:] != self.current_tag:
                        self.save_button.grid(row=0, column=1, pady=(25, 0))
                        self.save_button.focus_set()
                    else:
                        self.save_button.grid_forget()
                return
            tag += ".*"
        else:
            tag = ".".join(self.stack[:identifier[0] + 1]) + ".*"
        self.update(tag)

    def draw_text(self, x, y, label, anchor, identifier):
        text = self.canvas.create_text(x, y, font="Courier 20", text=label, fill="black", anchor=anchor)
        x1, y1, x2, y2 = self.canvas.bbox(text)
        new_box = (x1 - self.x_pad, y1 - self.y_pad, x2 + self.x_pad, y2 + self.y_pad)
        border = self.canvas.create_rectangle(new_box, outline="black", fill="#FFED31")
        self.canvas.tag_raise(text, border)

        self.canvas.tag_bind(text, "<Enter>", func=lambda e: self.hover((text, border), True))
        self.canvas.tag_bind(border, "<Enter>", func=lambda e: self.hover((text, border), True))
        self.canvas.tag_bind(text, "<Leave>", func=lambda e: self.hover((text, border), False))
        self.canvas.tag_bind(border, "<Leave>", func=lambda e: self.hover((text, border), False))

        self.canvas.tag_bind(text, "<Button-1>", func=lambda e: self.click((text, border), identifier))
        self.canvas.tag_bind(border, "<Button-1>", func=lambda e: self.click((text, border), identifier))

        return new_box, (text, border)

    def draw_line(self, x1, y1, x2, y2, arrow):
        self.canvas.create_line(x1, y1, x2, y2, arrow=arrow, fill="black", width=2)

    def display(self):
        x_cord = self.width / 2
        y_cord1 = self.height-self.h_factor*1.75
        parents_cords = [self.draw_text(x_cord, self.h_factor * (i + 0.5), parent, "center", (i, "parent"))
                         for i, parent in enumerate(self.stack)]
        y_cord2 = self.h_factor*(self.h_nodes-0.75)
        children_cords = [self.draw_text(self.spaces[i], y_cord1 if i % 2 == 0 else y_cord2, child, "w", (i, "child"))
                          for i, child in enumerate(self.children)]

        for itr in range(len(parents_cords) - 1):
            self.draw_line(x_cord, parents_cords[itr][0][3], x_cord, parents_cords[itr + 1][0][1], "last")

        y_cord3 = (children_cords[0][0][1] + parents_cords[-1][0][3]) // 2
        self.draw_line(x_cord, parents_cords[-1][0][3], x_cord, y_cord3, "none")
        c_cords = [(c[0][0]+c[0][2])//2 for c in children_cords]
        self.draw_line(c_cords[0], y_cord3, c_cords[-1], y_cord3, "none")
        for i, child in enumerate(c_cords):
            self.draw_line(child, y_cord3, child, children_cords[i][0][1], "last")

        selected_index = np.where(self.selected == np.char.add(".".join(self.stack)+".", np.array(self.children)))[0]
        if selected_index.shape[0] != 0:
            self.selected_gui = children_cords[selected_index[0]][1]
            self.hover(self.selected_gui, False)
        else:
            self.selected_gui = (-1, -1)
