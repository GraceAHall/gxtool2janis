




import runtime.logging.logging as logging
import datatypes
from typing import Optional
from tool.Tool import Tool
from xmltool.load import XMLToolDefinition
from command.Command import Command
from containers import Container
from .outputs import extract_outputs

class ToolFactory:
    def __init__(self, xmltool: XMLToolDefinition, command: Command, container: Optional[Container]) -> None:
        self.xmltool = xmltool
        self.command = command
        self.container = container

    def create(self) -> Tool:
        tool = Tool(
            metadata=self.xmltool.metadata,
            container=self.container,
            base_command=self.get_base_command(),
            gxparam_register=self.xmltool.inputs
        )
        self.supply_inputs(tool)
        self.supply_outputs(tool)
        return tool

    def supply_inputs(self, tool: Tool) -> None:
        self.command.set_cmd_positions()
        inputs = self.command.list_inputs(include_base_cmd=False)
        if not inputs:
            logging.no_inputs()
        for inp in inputs:
            datatypes.annotate(inp)
            tool.add_input(inp)

    def supply_outputs(self, tool: Tool) -> None:
        outputs = extract_outputs(self.xmltool, self.command)
        if not outputs:
            logging.no_outputs()
        for out in outputs:
            datatypes.annotate(out)
            tool.add_output(out)

    def get_base_command(self) -> list[str]:
        positionals = self.command.get_base_positionals()
        if not positionals:
            logging.no_base_cmd()
        return [p.default_value for p in positionals]
    