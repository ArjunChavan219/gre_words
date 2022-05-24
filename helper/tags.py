import numpy as np
import pandas as pd
from helper.functions import *
from tkinter import messagebox


class Graph:

    def __init__(self, add, tags, window_function, parent_window, *args):

        self.add = add
        self.tags = tags
        self.window_function = window_function
        self.parent_window = parent_window

        self.w_factor, self.h_factor = 65, 65
        self.x_pad, self.y_pad = 15, 5

        self.h_nodes, self.width, self.height = None, None, None
        self.stack, self.children, self.shortcuts = None, None, None
        self.selected_gui, self.highlighted_gui, self.guis = (-1, -1), (-1, -1), {}
        self.spaces = []

        if self.add:
            self.word = args[0]
            self.gui = args[1]
            self.change_function = args[2]
            self.main_window = args[3]
            self.current_tag = self.tags.get_tag(args[0])
            self.selected = "Tags." + self.current_tag
        else:
            self.selected = ""
            self.get_word = args[0]

    def __call__(self):
        text = f"Word: {self.word}" if self.add else "Tags Revision"
        self.window: Toplevel = self.window_function(("Word Tags", text))[0]
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.canvas = Canvas(self.window, background="#8CF3D4")
        self.canvas.grid(row=2, column=0, columnspan=4)
        self.window.bind_all("<Key>", lambda event: self.handle_key(event.keysym))

        button_frame = Frame(self.window, bg=BACKGROUND_COLOR)
        button_frame.grid(row=4, column=0, columnspan=4)
        get_button(button_frame, "Close", NEXT_COLOR, self.close_window, 0, 0, 1, (25, 0))
        self.save_button = get_button(button_frame, "Save n Close", "#4FA9EB", self.save, 0, 1, 1, (25, 0))
        self.save_button.grid_forget()

        self.update(self.selected)

    def save(self):
        self.gui.configure(state='normal')
        self.gui.delete("1.0", "end-1c")
        self.gui.insert("end", self.selected[5:], "centered")
        self.gui.configure(state='disabled')
        self.close_window()

    def close_window(self):
        self.window.unbind_all("<Key>")
        if self.add:
            self.change_function()
        self.window.destroy()

    def get_tag_shortcuts(self):
        identifier, letter = [], []
        for i, parent in enumerate(self.stack):
            identifier.append(self.guis[(i, "parent")])
            letter.append(parent[0].lower())
        for i, child in enumerate(self.children):
            identifier.append(self.guis[(i, "child")])
            letter.append(child[0].lower())

        return pd.DataFrame({"identifier": identifier, "letter": letter}).groupby("letter").agg(
            {"identifier": lambda a: list(a)}).to_dict()["identifier"]

    def update(self, tag):
        self.stack = ["Tags"]
        if tag != "" and tag != "Tags":
            self.stack = tag.split(".")[:-1]
        self.children = sorted(self.tags.get_tag_children(".".join(self.stack)), key=lambda a: (-len(a), a))
        self.guis = {}

        self.canvas.delete("all")
        self.h_nodes = len(self.stack) + 1.5 + (1 if len(self.children) >= 2 else 0)
        self.spaces = np.cumsum(np.char.str_len(self.children) * 12 + 3)
        self.width = self.spaces[-1] + self.w_factor + 2*self.x_pad
        self.spaces[1:] = self.spaces[:-1]
        self.spaces[0] = 0
        self.spaces += self.w_factor
        self.height = int(self.h_factor * self.h_nodes)
        self.canvas.configure(width=self.width, height=self.height)
        place_window(self.window, max(550, 56+self.width), self.height+249)

        self.display()

    def handle_key(self, key: str):
        if key == "space":
            if self.highlighted_gui == (-1, -1):
                return
            if str(self.canvas.focus_get()).split(".!")[-1] != "button":
                identifier = list(self.guis.keys())[list(self.guis.values()).index(self.highlighted_gui)]
                self.click(self.highlighted_gui, identifier)
            return
        if len(key) == 1 and key.isalpha() and key in self.shortcuts:
            guis: list = self.shortcuts[key]
            if self.highlighted_gui == (-1, -1) or self.highlighted_gui not in guis:
                index = 0
            else:
                index = (guis.index(self.highlighted_gui) + 1) % len(guis)
            self.hover(guis[index], True)

    def hover(self, gui, enter):
        h_gui = self.highlighted_gui
        self.highlighted_gui = (-1, -1)
        if h_gui != (-1, -1):
            self.hover(h_gui, False)
        if enter:
            color = ("white", "red")
            self.highlighted_gui = gui
        elif gui == self.selected_gui:
            color = ("white", "#8800C7")
        else:
            color = ("black", "#FFED31")
        self.canvas.itemconfigure(gui[0], fill=color[0])
        self.canvas.itemconfigure(gui[1], fill=color[1])

    def click(self, gui, identifier):
        if identifier[1] != "parent":
            tag = ".".join(self.stack) + "." + self.children[identifier[0]]
            children = self.tags.get_tag_children(tag)

            if len(children) == 0:
                if self.add:
                    words = wrap_text(self.tags.get_tag_words(tag[5:]), 60)
                    confirm = messagebox.askyesno("Confirm", f"It has the following words:\n{words}")
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
                else:
                    print(tag)
                    self.display_tag_words(tag)
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

        self.guis[identifier] = (text, border)
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
        self.shortcuts = self.get_tag_shortcuts()

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

    def display_tag_words(self, tag):
        new_window, _ = self.window_function(("Word Tags", "Tag:"))
        _.grid(row=0, column=0, columnspan=4, pady=(0, 0))
        height = 320

        canvas = Canvas(new_window, width=500, height=50, bg=BACKGROUND_COLOR, highlightthickness=0)
        canvas.create_text(250, 25, text=tag, fill="black", font=("Ariel", 20, "italic"))
        canvas.grid(row=1, column=0, columnspan=4, pady=(0, 30))

        frame = Frame(new_window, bg=BACKGROUND_COLOR)
        frame.grid(row=2, column=0)
        tree, style = get_tree(frame, (150, 750), ("Word", "Prompt"), None, 3)
        values = self.tags.get_tag_words_data(tag[5:])
        style.configure("Custom3.Treeview", rowheight=60)
        length = len(values)
        if length < 10:
            tree.configure(height=length)
            height += length*60
        else:
            height += 600

        def get_values(val):
            return values[val][0], wrap_text(values[val][1].replace("\n", "; "), 75)

        for itr in range(len(values)):
            tree.insert("", 'end', text=itr, values=get_values(itr))
        alternate(tree)
        tree.bind("<Double-1>", lambda event: self.get_word(tree, get_values))

        get_button(new_window, "Close", NEXT_COLOR, lambda: new_window.destroy(), 3, 0, 4, (25, 0))

        place_window(new_window, 950, height)
