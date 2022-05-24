import pymongo
import numpy as np
import pandas as pd
from helper.constants import COLUMNS


class MongoDb:

    def __init__(self):
        """
        Class init
        """
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["gre_"]
        self.col = db["words_last_new"]
        self.data_col = db["words_first"]
        self.data: pd.DataFrame = self.get_database()

        self.tree = {}
        self.tag_change = False
        self.get_tag_tree({"Tags": db["words_tags"].find({}, {"_id": 0})[0]}, "Tags", "Tags")

    def get_database(self) -> pd.DataFrame:
        df = pd.DataFrame(self.col.find({}, {"_id": 0}))
        df.definitions = df.definitions.str.join("\n")
        df.examples = df.examples.str.join("\n")
        df.syns = df.syns.str.join(", ")
        df.ants = df.ants.str.join(", ")
        return df.astype(object)

    def __call__(self) -> list[dict]:
        return self.data.to_dict("records")

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, item):
        if type(item) == tuple:
            return self.data.loc[item[0]][item[1]]
        else:
            return dict(self.data.loc[item])

    def __setitem__(self, item, value):
        self.data.at[item] = value
        self.col.update_one({"word": self.data["word"][item[0]]}, {"$set": {item[1]: value}})

    def get_counts(self, item) -> list:
        return list(self.data[item].value_counts().sort_index().items())

    def get_count(self, item, value):
        return len(self.data[self.data[item] == value])

    def get_level_indices(self, level):
        return self.data[self.data.level == level].index.to_numpy()

    def get_remaining_count(self):
        return self.data_col.count_documents({"learnt": False})

    def get_revised_list(self):
        return self.data[["word", "prompt", "score", "test", "marked", "level", "tag"]].sort_values("word").to_numpy()

    def get_word_tab(self, word):
        return self.data[self.data.word == word][["prompt", "level", "tag"]].to_numpy()[0]

    def get_word_data(self, *args):
        if len(args) == 0:
            return self.data_col.find({"learnt": False}, {"_id": 0, "word": 1, "data": 1})
        else:
            data = self.data[self.data.word == args[0]]
            return data.index[0].item(), data.to_dict("records")[0]

    def insert_one(self, data):
        extra_data = {
            "prompt": "",
            "score": 0,
            "test": 0,
            "marked": False,
            "level": 3,
            "tag": ""
        }
        self.data.loc[len(self.data)] = [*data.values(), *extra_data.values()]
        for i, col in enumerate(COLUMNS):
            data[col] = data[col].split(", " if 0 < i < 3 else "\n")
        self.col.insert_one(data | extra_data)
        self.data_col.update_one(
            {"word": data["word"]},
            {"$set": {"learnt": True}}
        )

    def get_tag(self, word):
        # get tag for the respective word
        return self.data[self.data.word == word].tag.values[0]

    def get_tag_tree(self, tags, header, root):
        children = tags[root]
        if children is None:
            self.tree[header] = []
        else:
            self.tree[header] = [header + "." + key for key in children]
            for child in children:
                self.get_tag_tree(children, header + "." + child, child)

    def get_tag_children(self, parent):
        # children of that particular tag
        return [child.split(".")[-1] for child in self.tree[parent]]

    def get_tag_words(self, tag):
        # list of all words with that tag
        return ", ".join(np.sort(self.data[self.data.tag == tag].word.values))

    def get_tag_words_data(self, tag):
        # list of all words and definitions with that tag
        return self.data[self.data.tag == tag][["word", "definitions"]].sort_values("word").to_numpy()

    def save_tags(self):
        with open("Words.md") as file:
            lines = [line for line in file.readlines() if line.startswith("#")]

        words_entry = ""
        stack = []

        for line in lines:
            level = line.index(" ")
            if level <= len(stack):
                tag_df = self.data[self.data.tag == ".".join(stack)][["word", "definitions"]].sort_values("word")
                words_entry += "\n".join(tag_df.word + " -> " + tag_df.definitions.str.replace("\n", "; ")) + "\n\n"
            while level <= len(stack):
                stack.pop()
            stack.append(line[level + 1:-1])
            words_entry += line

        tag_df = self.data[self.data.tag == ".".join(stack)][["word", "definitions"]].sort_values("word")
        words_entry += "\n".join(tag_df.word + " -> " + tag_df.definitions.str.replace("\n", "; ")) + "\n\n"

        with open("Words_2.md", "w") as file:
            file.write(words_entry)
