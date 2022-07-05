

from typing import Tuple
from entities.tool.Tool import Tool

from fileio.text.tool.ToolInputSectionRender import ToolInputSectionRender
from fileio.text.tool.ToolOutputSectionRender import ToolOutputSectionRender

from runtime.dates import JANIS_DATE_FMT
from fileio.text.TextRender import TextRender
from datetime import datetime

import tags
import textwrap

from dataclasses import dataclass
from fileio.text.TextRender import TextRender

from .. import ordering
from .. import formatting

def note_snippet(tool: Tool) -> str:
    tool_name = tool.metadata.id
    tool_version = tool.metadata.version
    return f"""\
# NOTE
# This is an automated translation of the '{tool_name}' version '{tool_version}' tool from a Galaxy XML tool wrapper.  
# Translation was performed by the gxtool2janis program (in-development)
"""

def syspath_snippet() -> str:
    return """\
import sys
sys.path.append('/home/grace/work/pp/gxtool2janis')
"""

def metadata_snippet(tool: Tool) -> str:
    return f"""\
metadata = ToolMetadata(
    short_documentation="{tool.metadata.description}",
    keywords=[],
    contributors={get_contributors(tool)},
    dateCreated="{datetime.today().strftime(JANIS_DATE_FMT)}",
    dateUpdated="{datetime.today().strftime(JANIS_DATE_FMT)}",
    version="{tool.metadata.version}",
    doi="{tool.metadata.get_doi_citation()}",
    citation="{tool.metadata.get_main_citation()}",
    documentationUrl=None,
    documentation=\"\"\"{str(tool.metadata.help)}\"\"\"
)
"""

def get_contributors(tool: Tool) -> list[str]:
    contributors: list[str] = ['gxtool2janis']
    if tool.metadata.owner:
        contributors += [f'Wrapper owner: galaxy toolshed user {tool.metadata.owner}']
    if tool.metadata.creator:
        contributors += [f'Wrapper creator: {tool.metadata.creator}']
    return contributors

def builder_snipper(tool: Tool) -> str:
    container = f'"{tool.container}"' if tool.container else None
    return f"""\
{tags.tool.get(tool.uuid)} = CommandToolBuilder(
    tool="{tags.tool.get(tool.uuid)}",
    version="{tool.metadata.version}",
    metadata=metadata,
    container={container},
    base_command={tool.base_command},
    inputs=inputs,
    outputs=outputs
)
"""
    
def translate_snippet(tool: Tool) -> str:
    tool_name = tool.metadata.id
    return textwrap.dedent(f"""\
    if __name__ == "__main__":
        {tool_name}().translate(
            "wdl", to_console=True
        )\n
    """
    )


tool_class_imports = [
    ("janis_core", "CommandToolBuilder"),
    ("janis_core", "ToolMetadata"),
    ("janis_core", "ToolInput"),
    ("janis_core", "ToolOutput"),
]


@dataclass
class ToolRender(TextRender):
    def __init__(self, entity: Tool, render_imports: bool=False):
        super().__init__(render_imports)
        self.entity = entity

    @property
    def imports(self) -> list[Tuple[str, str]]:
        inputs = self.entity.list_inputs()
        outputs = self.entity.list_outputs()
        imports: list[Tuple[str, str]] = []
        imports += tool_class_imports
        imports += ToolInputSectionRender(inputs).imports
        imports += ToolOutputSectionRender(outputs).imports
        imports = list(set(imports))
        return ordering.order_imports(imports)

    def render(self) -> str:
        inputs = self.entity.list_inputs()
        outputs = self.entity.list_outputs()
        out_str: str = ''
        out_str += f'{note_snippet(self.entity)}\n'
        out_str += f'{syspath_snippet()}\n'
        if self.render_imports:
            out_str += f'{formatting.format_imports(self.imports)}\n'
        out_str += f'\n{metadata_snippet(self.entity)}\n'
        out_str += f'{ToolInputSectionRender(inputs).render()}\n'
        out_str += f'{ToolOutputSectionRender(outputs).render()}\n'
        out_str += f'{builder_snipper(self.entity)}\n'
        out_str += f'\n{translate_snippet(self.entity)}\n'
        return out_str