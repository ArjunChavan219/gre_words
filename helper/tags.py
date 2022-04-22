class Tree:

    def __init__(self, value, children, level):
        self.value = value
        self.children = []
        self.level = level
        if children is not None:
            for child in children:
                self.children.append(Tree(child, children[child], level+1))

    def __str__(self):
        return self.value+"\n"+"".join([self.level*"\t"+str(child) for child in self.children])

    def get_leaves(self, leaves, header):
        if len(self.children) == 0:
            return [*leaves, header+self.value]
        header += self.value+"."
        for child in self.children:
            leaves = child.get_leaves(leaves, header)
        return leaves


class Tags:

    def __init__(self, data, words):
        self.tree = Tree("Tags", data, 0)
        self.words = words

    def get_leaves(self):
        return self.tree.get_leaves([], "")

    def graph(self, window_function, word, gui, change_function):
        window = window_function(("Word Tags", f"Word: {word}"))
        tag = self.words[word]
        path = ["Tags"]
        selected = None
        if tag != "":
            tags = tag.split(".")
            path.extend(tags[:-1])
            selected = tags[-1]
        print(path, selected)
        # gui[0].configure(state='normal')
        # gui[0].delete("1.0", "end-1c")
        # gui[0].insert("end", "tmp_tag", "centered")
        # gui[0].configure(state='disabled')

        def close_window():
            change_function(gui, tag)
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", close_window)
