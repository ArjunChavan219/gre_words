import textwrap
from helper.constants import *
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkmacosx import Button


def place_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 4
    window.geometry(f"{min(screen_width, width)}x{min(screen_height, height)}+{max(0, x)}+{max(0, y)}")


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


def get_tree(frame, widths, texts, function, tid, values):
    style = ttk.Style(frame)
    style.theme_use("aqua")
    style.configure(f"Custom{tid}.Treeview", background="white", foreground="black", font=("Ariel", 16), rowheight=30)
    style.configure(f"Custom{tid}.Treeview.Heading", foreground="white", font=("Ariel", 20), rowheight=60)
    tree = ttk.Treeview(frame, selectmode='browse', style=f"Custom{tid}.Treeview")
    tree.grid(row=1, column=0, columnspan=4, sticky="news")
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    vsb.grid(row=1, column=3, sticky="nse")

    tree.configure(yscrollcommand=vsb.set)

    tree["columns"] = [str(i+1) for i in range(len(widths))]
    tree['show'] = 'headings'
    for itr, width, text in zip(tree["columns"], widths, texts):
        tree.column(itr, width=width, anchor='c')
        tree.heading(itr, text=text, command=lambda itr_=itr: function(itr_, True))
    for itr, value in enumerate(values):
        tree.insert("", 'end', text=itr, values=value, tag=("blue" if itr % 2 != 0 else ""))

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
