

from typing import Optional
from xmltool.load import XMLToolDefinition
from command.Command import Command
from containers import Container
from tool.Tool import Tool
from tool.ToolFactory import ToolFactory


def gen_tool(xmltool: XMLToolDefinition, command: Command, container: Optional[Container]) -> Tool:
    factory = ToolFactory(xmltool, command, container)
    tool = factory.create()
    return tool

