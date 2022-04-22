import pymongo
import pandas as pd
from helper.constants import COLUMNS
from helper.tags import Tags


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

        self.tags: Tags = Tags(
            db["words_tags"].find({}, {"_id": 0})[0],
            self.data[["word", "tag"]].set_index("word").to_dict()["tag"]
        )

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

    def get_index(self, word):
        return self.data[self.data.word == word].index[0].item()

    def get_level_indices(self, level):
        return self.data[self.data.level == level].index.to_numpy()

    def get_remaining_count(self):
        return self.data_col.count_documents({"learnt": False})

    def get_revised_list(self):
        return self.data[["word", "prompt", "score", "test", "marked", "level", "tag"]].sort_values("word").to_numpy()

    def get_word_data(self):
        return self.data_col.find({"learnt": False}, {"_id": 0, "word": 1, "data": 1})

    def insert_one(self, data):
        extra_data = {
            "prompt": "",
            "score": 0,
            "test": 0,
            "marked": False,
            "level": 2,
            "tags": ""
        }
        self.data.loc[len(self.data)] = [*data.values(), *extra_data.values()]
        for i, col in enumerate(COLUMNS):
            data[col] = data[col].split(", " if 0 < i < 3 else "\n")
        self.col.insert_one(data | extra_data)
        self.data_col.update_one(
            {"word": data["word"]},
            {"$set": {"learnt": True}}
        )
