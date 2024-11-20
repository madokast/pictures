import json
from io import BufferedReader
from typing import Dict, Union, Any

SupportsRead = Any

class Json:
    def to_dict(self) -> Dict[str, Any]:
        obj = dict()
        for name in dir(self):
            if name[1] == '_':
                continue
            if not callable(getattr(self, name)):
                value = getattr(self, name)
                if isinstance(value, Json):
                    value = value.to_dict()
                obj[name] = value
        return obj

    def populate_dict(self, obj:Dict[str, Any]) -> None:
        for k, v in obj.items():
            if isinstance(v, dict):
                old_value = getattr(self, k)
                if isinstance(old_value, Json):
                    old_value.populate_dict(v)
            else:
                setattr(self, k, v)
    
    def populate_json(self, json_source:Union[str, bytes, bytearray, SupportsRead]) -> None:
        if isinstance(json_source, str) or isinstance(json_source, bytes):
            obj = json.loads(json_source)
        else:
            obj = json.load(json_source)
        self.populate_dict(obj)

    def to_json(self, ensure_ascii = False, indent = None) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=indent)

    def __str__(self) -> str:
        return self.to_json()
    
    def __repr__(self) -> str:
        return str(self)

    
