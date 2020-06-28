import json
import os

from server.app.utils import obj_to_json


class DataBase:

    def __init__(self, url):
        self.url = url
        if not os.path.exists(url):
            os.mkdir(url)

    def drop_table(self, db_name, tab_name, default=None):
        try:
            db_path = os.path.join(self.url, db_name)
            os.remove(os.path.join(db_path, tab_name))
        except:
            return default

    def save_to_db(self, db_name, tab_name, bean):
        db_path = os.path.join(self.url, db_name)
        if not os.path.exists(db_path):
            os.mkdir(db_path)
        with open(os.path.join(db_path, tab_name), "w") as f:
            f.write(obj_to_json(bean))
            f.close()

    def append(self, db_name, tab_name, line):
        db_path = os.path.join(self.url, db_name)
        if not os.path.exists(db_path):
            os.mkdir(db_path)
        with open(os.path.join(db_path, tab_name), "a") as f:
            f.writelines(line)
            f.close()

    def find_from_db_and_cover_json(self, db_name, tab_name, default=None):
        try:
            db_path = os.path.join(self.url, db_name)
            with open(os.path.join(db_path, tab_name), "r") as f:
                data = json.load(f)
                return data
        except:
            return default

    def find(self, db_name, tab_name, default=None):
        try:
            db_path = os.path.join(self.url, db_name)
            with open(os.path.join(db_path, tab_name), "r") as f:
                return f.read()
        except:
            return default

   