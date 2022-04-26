from tkinter import *
from main import Main, BACKGROUND_COLOR


window = Tk()

main_frame = Main(window)
window.config(padx=25, pady=50, bg=BACKGROUND_COLOR)

window.mainloop()
