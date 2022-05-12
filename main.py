from helper.functions import *
from helper.data import MongoDb


class Main:

    def __init__(self, window: Tk):
        #
        self.data = MongoDb()

        # TK Constants:
        from helper.classes import CLASSES
        self.button_data: list[tuple[classmethod, str]] = list(zip(CLASSES, CLASS_COLORS))

        # Initialize TK Widgets
        self.window = window
        self.frame, canvas = self.init_frames(("Words", "Welcome to the Learning Platform"), None)
        canvas[0].configure(width=750)
        canvas[0].grid(row=0, column=0, columnspan=4, pady=(0, 30))
        canvas[0].move(canvas[1], 125, 0)
        self.init_window()

        # Button
        self.practice_button, self.revise_button, self.test_button, self.quick_test_button = [
            get_button(self.frame, self.button_data[itr][0].__name__, self.button_data[itr][1],
                       lambda itr_=itr: self.button_data[itr_][0](self), 1, itr, 1, (0, 0)) for itr in range(4)]

    def init_window(self):
        self.window.title("GRE Words")
        self.refresh_child(self.frame)
        place_window(self.window, 800, 200)

    def init_frames(self, titles, *args):
        self.window.title(f"GRE {titles[0]} Card")
        # Frame
        frame = Frame(self.window, bg=BACKGROUND_COLOR)
        frame.grid(row=0, column=0)

        # Word Header
        canvas = Canvas(frame, width=500, height=50, bg=BACKGROUND_COLOR, highlightthickness=0)
        canvas_title = canvas.create_text(250, 25, text=titles[1], fill="black", font=CANVAS_FONT)
        canvas.grid(row=0, column=0, columnspan=4, pady=(0, 30))

        # Home Button
        if args[0] is not None:
            get_button(frame, "Home", HOME_COLOR, lambda: self.go_home(frame), args[0], args[1], args[2], args[3])

        return frame, (canvas, canvas_title)

    def go_home(self, frame):
        frame.destroy()
        self.init_window()

    def refresh_child(self, frame):
        self.frame.grid_forget()
        frame.grid_forget()
        frame.grid(row=0, column=0)
