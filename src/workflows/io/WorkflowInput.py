

from dataclasses import dataclass, field
from typing import Optional
from datatypes.JanisDatatype import JanisDatatype
from datatypes.formatting import format_janis_str
from uuid import uuid4


"""
JANIS
Workflow.input(
    identifier: str, 
    datatype: DataType, 
    default: any = None, 
    doc: str = None
)
eg w.input("sample_name", String)
"""


@dataclass
class WorkflowInput:
    name: str
    step_id: int
    step_tag: Optional[str]
    is_galaxy_input_step: bool = False
    gx_datatypes: list[str] = field(default_factory=list)
    janis_datatypes: list[JanisDatatype] = field(default_factory=list)

    def __post_init__(self):
        self.uuid: str = str(uuid4())

    def get_uuid(self) -> str:
        return self.uuid

    def get_docstring(self) -> Optional[str]:
        return 'None yet!'
        raise NotImplementedError()
        
    def get_janis_datatype_str(self) -> str:
        return format_janis_str(
            datatypes=self.janis_datatypes,
            is_optional=False,
            is_array=False
        )


