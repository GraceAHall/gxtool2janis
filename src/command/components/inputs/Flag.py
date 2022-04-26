
from __future__ import annotations
from typing import Any, Optional
from xmltool.param.InputParam import BoolParam

from command.components.CommandComponent import BaseCommandComponent


class Flag(BaseCommandComponent):
    def __init__(self, prefix: str, name: Optional[str]=None) -> None:
        super().__init__()
        self.prefix = prefix

    def get_name(self) -> str:
        return self.prefix.strip('--')

    def get_default_value(self) -> bool:
        if self.gxparam:
            return self.get_default_from_gxparam()
        else:
            return self.get_default_from_presence()
    
    def get_default_from_gxparam(self) -> bool:
        if isinstance(self.gxparam, BoolParam):
            if self.gxparam.checked and self.gxparam.truevalue == self.prefix:
                return True
            elif self.gxparam.checked and self.gxparam.truevalue == "":
                return False
            elif not self.gxparam.checked and self.gxparam.falsevalue == self.prefix:
                return True
            elif not self.gxparam.checked and self.gxparam.falsevalue == "":
                return False
        return False
    
    def get_default_from_presence(self) -> bool:
        if all([self.presence_array]):
            return True
        return False
   
    def is_optional(self) -> bool:
        return True

    def is_array(self) -> bool:
        return False

    def get_docstring(self) -> Optional[str]:
        if self.gxparam:
            return self.gxparam.get_docstring()
        return None

    def update(self, incoming: Any):
        assert(isinstance(incoming, Flag))
        # gxparam transfer
        if not self.gxparam and incoming.gxparam:
            self.gxparam = incoming.gxparam
        # presence
        cmdstr_index = len(incoming.presence_array) - 1
        self.update_presence_array(cmdstr_index)
        
    def __str__(self) -> str:
        return f'{str(self.get_default_value()):20}{str(self.is_optional()):>10}'
