


import yaml
from typing import Optional

from .JanisDatatype import JanisDatatype

DATATYPES_PATH = './galaxy2janis/datatypes/galaxy_janis_types.yaml'

class DatatypeRegister:
    def __init__(self):
        self.dtype_map: dict[str, JanisDatatype] = self._load()

    def get(self, datatype: str) -> Optional[JanisDatatype]:
        if datatype in self.dtype_map:
            return self.dtype_map[datatype]

    def _load(self) -> dict[str, JanisDatatype]:
        """
        func loads the combined datatype yaml then converts it to dict with format as keys
        provides structue where we can search all the galaxy and janis types given what we see
        in galaxy 'format' attributes.
        """
        out: dict[str, JanisDatatype] = {}
        with open(DATATYPES_PATH, 'r') as fp:
            datatypes = yaml.safe_load(fp)
        for type_data in datatypes['types']:
            janistype = self._init_type(type_data)
            # multiple keys per datatype
            out[type_data['format']] = janistype
            out[type_data['classname']] = janistype 
            if type_data['extensions']:
                for ext in type_data['extensions']:
                    out[ext] = janistype 
        return out

    def _init_type(self, dtype: dict[str, str]) -> JanisDatatype:
        return JanisDatatype(
            format=dtype['format'],
            source=dtype['source'],
            classname=dtype['classname'],
            extensions=dtype['extensions'],
            import_path=dtype['import_path']
        )


# SINGLETON
register = DatatypeRegister()
