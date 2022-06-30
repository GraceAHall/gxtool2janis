


# top note
# messages
# imports?
# inputs
# preprocessing?
# tool
# postprocessing?




from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Tuple
from shellparser.components.CommandComponent import CommandComponent

from entities.workflow import WorkflowStep
from entities.workflow import InputValue
from entities.workflow import Workflow

from formats.imports.Import import Import
from formats.imports.WorkflowImportCollector import WorkflowImportCollector

import formats.workflow_definition.snippets as snippets
import formats.workflow_definition.formatting as formatting
from formats.workflow_definition.ToolInputLine import LinkedInputLine, ToolInputLine, UnlinkedInputLine
from formats.workflow_definition.ordering import order



class TextEntity(ABC):  # prev: Snippet
    """Smallest unit of text. Eg: Import statement, Input, Output etc"""

    def __init__(self, entity: Any):
        self.entity = entity

    @abstractmethod
    def render(self) -> str:
        """renders text sections using content and ordering strategy"""
        ...


class OrderingStrategy(ABC):

    @abstractmethod
    def order(self) -> list[TextSection]:
        """orders TextSection"""
        ...


class TextSection(ABC):
    """combines """
    def __init__(self, content: list[TextSection], ordering: OrderingStrategy):
        self.content = content
        self.ordering = ordering

    @abstractmethod
    def render(self) -> str:
        """renders text sections using content and ordering strategy"""
        ...



class NoteTextSection(TextSection):
    pass

class MessageTextSection(TextSection):
    pass

class ImportTextSection(TextSection):
    pass

class InputTextSection(TextSection):
    pass

class ToolTextSection(TextSection):
    class ValuesTextSection(TextSection):
        pass

class PreProcessingTextSection(TextSection):
    pass

class PostProcessingTextSection(TextSection):
    pass


class StepTextDefinition:
    def __init__(self, sections: list[TextSection]):
        self.sections = sections
        self.ordering: list[TextSection] = [
            NoteTextSection,
            MessageTextSection,
            ImportTextSection,
            InputTextSection, 
            PreProcessingTextSection,
            ToolTextSection,
            PostProcessingTextSection
        ]
    
    def text(self) -> str:
        out: str = '\n'
        for section_type in self.ordering:
            for section in self.sections:
                if isinstance(section, section_type):
                    out += section
            out += '\n'
        return out






@dataclass
class StepText:
    """
    represents a step definition as it appears to the user.
    in future will include features such as providing documentation,
    line references to xml text to aid user etc. 
    """
    step_count: int
    step: WorkflowStep
    workflow: Workflow

    def format_page(self) -> str:
        """
        produces the string representation of this step.
        each segment is separated by a blank line.
        includes all StepTextDefinition properties
        """
        out: str = '\n'
        out += self.title + '\n'
        out += self.foreword + '\n'
        out += self.text_imports + '\n'
        out += self.pre_task + '\n'
        out += '# RUNTIME VALUES\n'
        out += self.runtime_inputs + '\n'
        out += '# TOOL EXECUTION\n'
        out += self.step_call + '\n'
        out += self.post_task + '\n'
        return out
    
    def format_main(self) -> str:
        """
        produces the string representation of this step.
        each segment is separated by a blank line.
        includes a subset of StepTextDefinition properties
        """
        out: str = ''
        out += self.title + '\n'
        out += self.runtime_inputs
        out += self.step_call
        return out

    @property
    def imports(self) -> list[Import]:
        collector = WorkflowImportCollector()
        collector.collect_step_imports(self.step, self.workflow)
        return collector.list_imports()
    
    @property
    def text_imports(self) -> str:
        return formatting.format_imports(self.imports)

    @property
    def title(self) -> str:
        return snippets.step_title_snippet(self.step_count, self.get_tool_tag())
    
    @property
    def foreword(self) -> str:
        return snippets.step_foreward_snippet()
    
    @property
    def pre_task(self) -> str:
        # TODO 
        return snippets.pre_task_snippet()

    @property
    def runtime_inputs(self) -> str:
        # following few lines could be workflow method? 
        runtime_inputs = self.step.tool_values.runtime
        workflow_inputs = [ self.workflow.get_input(input_uuid=value.input_uuid) 
                            for value in runtime_inputs]
        workflow_inputs = [x for x in workflow_inputs if x is not None]
        out_str: str = ''
        for wflow_inp in workflow_inputs:
            input_tag = self.workflow.tag_manager.get(wflow_inp.uuid)
            dtype_string = wflow_inp.get_janis_datatype_str()
            out_str += snippets.workflow_input_snippet(input_tag, dtype_string)
        return out_str

    @property
    def step_call(self) -> str:
        out: str = ''
        out += 'w.step(\n'
        out += f'\t"{self.get_step_tag()}",\n'
        #out += f'\tscatter="{scatter}",\n' if scatter else ''
        out += f'\t{self.get_tool_tag()}(\n'
        out += self.format_unlinked_inputs()
        out += self.format_linked_nondefault_inputs()
        out += self.format_linked_default_inputs()
        out += '\t)\n'
        out += ')\n'
        return out
    
    @property
    def post_task(self) -> str:
        # TODO 
        return snippets.post_task_snippet()
    
    def get_step_tag(self) -> str:
        return self.workflow.tag_manager.get(self.step.uuid)
    
    def get_tool_tag(self) -> str:
        tool = self.step.tool
        return tool.tag_manager.get(tool.uuid)

    def format_unlinked_inputs(self) -> str:
        lines: list[ToolInputLine] = []
        for inp in self.step.tool_values.unlinked:
            lines.append(UnlinkedInputLine(inp, self.step, self.workflow))
        return self.format_input_section(lines)

    def format_linked_nondefault_inputs(self) -> str:
        lines: list[ToolInputLine] = []
        for component, invalue in self.get_nondefault_input_values():
            lines.append(LinkedInputLine(invalue, component, self.step, self.workflow))
        return self.format_input_section(lines)

    def format_linked_default_inputs(self) -> str:
        lines: list[ToolInputLine] = []
        for component, invalue in self.get_default_input_values():
            lines.append(LinkedInputLine(invalue, component, self.step, self.workflow))
        return self.format_input_section(lines)

    def get_nondefault_input_values(self) -> list[Tuple[CommandComponent, InputValue]]:
        out: list[Tuple[CommandComponent, InputValue]] = []
        for comp_uuid, invalue in self.step.tool_values.linked:
            if not isinstance(invalue, DefaultInputValue):
                component = self.step.tool.get_input(comp_uuid)
                assert(component)
                out.append((component, invalue))
        return out
    
    def get_default_input_values(self) -> list[Tuple[CommandComponent, InputValue]]:
        out: list[Tuple[CommandComponent, InputValue]] = []
        for comp_uuid, invalue in self.step.tool_values.linked:
            if isinstance(invalue, DefaultInputValue):
                component = self.step.tool.get_input(comp_uuid)
                assert(component)
                out.append((component, invalue))
        return out
        
    def format_input_section(self, lines: list[ToolInputLine]) -> str:
        out: str = ''
        if len(lines) > 0:
            lines = order(lines)
            line_len = self.calculate_line_len(lines)
            for line in lines:
                out += snippets.step_input_value_snippet(
                    line_len=line_len,
                    line=line
                )
        return out
        
    def calculate_line_len(self, lines: list[ToolInputLine]) -> int:
        return max(len(line.tag_and_value) for line in lines)

    




