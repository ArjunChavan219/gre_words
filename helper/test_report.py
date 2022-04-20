from helper.functions import *
from helper.test import Test


class TestReport:

    def __init__(self, parent: Test):
        # Initialize MongoDB
        self.col = parent.parent.db["words_last_new"]

        # Initialize TK Widgets
        self.parent = parent
        self.frame = self.parent.parent.init_frames(("Test Report", "Report"), 2, 0, 4, (50, 0))[0]

        # TreeView
        sizes = (600, 60, 200, 200, 150) if self.parent.test_type else (150, 60, 600, 600, 150)
        self.tree, style = get_tree(self.frame, sizes, ("Word", "Score", "Your Answer",
                                                        "Correct Answer", "Marked"), self.sort)
        style.configure("Treeview", rowheight=60)
        self.set_report()

        self.parent.parent.refresh_child(self.frame)

    def sort(self, col, reverse):
        def get_children(parent):
            value = self.tree.set(parent, col)
            if col == "2" or col == "5":
                value = 1 if value != "❌" else -1
                if reverse:
                    value *= -1
            return value, self.tree.set(parent, "4"), parent
        children = [get_children(k) for k in self.tree.get_children('')]
        children.sort(reverse=(reverse if col == "1" or (col != "1" and not reverse) else (not reverse)))
        for index, (val1, val2, k) in enumerate(children):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda itr_=col: self.sort(itr_, not reverse))
        alternate(self.tree)

    def set_report(self):
        for itr, (word, options, report) in enumerate(zip(self.parent.words, self.parent.options, self.parent.report)):
            check = "✅" if report == 0 else "❌"
            mark = "❌" if self.parent.marked[itr] else ""
            values = (wrap_text(word["definitions" if self.parent.test_type else "word"], 75),
                      check, wrap_text(options[report], 75), wrap_text(options[0], 75), mark)
            self.tree.insert("", 'end', values=values, tag=("blue" if itr % 2 != 0 else ""))
            self.col.update_one({"word": word["word"]}, {"$inc": {"score": 1 if report == 0 else 0, "test": 1},
                                                         "$set": {"marked": self.parent.marked[itr]}})