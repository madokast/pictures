import os
import time
import json
import logging
import serializable
from collections import defaultdict
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)
Path = str

class Picture(serializable.Json):
    def __init__(self, path:Path = "") -> None:
        self.path = path # "202411201620-aaibs.webp"
        self.name:str = "untitled" # 
        self.dir:List[str] = ['uncategorized']
        self.tags:List[str] = []

class Pictures:
    def __init__(self, root_dir:str = 'pic', database_file:str = 'db.json', json_indent=2) -> None:
        self.path_pictures:Dict[Path, Picture] = dict()
        self.root_dir = root_dir
        self.database_file = os.path.join(root_dir, database_file)
        self.json_indent = json_indent

        if os.path.exists(self.database_file):
            with open(file=self.database_file, mode='r', encoding='utf-8') as f:
                items:List[Dict] = json.load(f)
                for item in items:
                    p = Picture()
                    p.populate_dict(item)
                    self.path_pictures[p.path] = p
        
        for _, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if not filename.endswith('.json') and filename not in self.path_pictures:
                    self.add_new_pictures(filename)
        
        self.persistence()
        logger.info('finish loading pictures')
    
    def add_new_pictures(self, path:Path) -> None:
        logger.info('new add pictures %s', path)
        if path in self.path_pictures:
            raise RuntimeError(f"duplicated name {path}")
        self.path_pictures[path] = Picture(path=path)
    
    def persistence(self) -> None:
        with open(file=self.database_file, mode='w', encoding='utf-8') as f:
            pictures = [p.to_dict() for p in self.path_pictures.values()]
            json.dump(pictures, f, ensure_ascii=False, indent=self.json_indent)

class PictureServer:
    def __init__(self, root_dir:str = 'pic', database_file:str = 'db.json', json_indent = 2) -> None:
        self.pictures = Pictures(root_dir=root_dir, database_file=database_file, json_indent=json_indent)


