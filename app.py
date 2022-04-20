from tkinter import *
from main import Main, BACKGROUND_COLOR


window = Tk()

main_frame = Main(window)
window.config(padx=50, pady=50, bg=BACKGROUND_COLOR)

window.mainloop()
