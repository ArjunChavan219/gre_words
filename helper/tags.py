class Tags:

    def __init__(self, value, children, level):
        self.value = value
        self.children = []
        self.level = level
        if children is not None:
            for child in children:
                self.children.append(Tags(child, children[child], level+1))

    def __str__(self):
        return self.value+"\n"+"".join(map(lambda a: self.level*"\t"+str(a), self.children))
