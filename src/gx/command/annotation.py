

import logs.logging as logging

from gx.gxtool.XMLToolDefinition import XMLToolDefinition
from gx.gxtool.param.Param import Param
from gx.gxtool.param.InputParam import BoolParam, SelectParam
from gx.gxtool.param import utils

from .parser.epath.ExecutionPath import ExecutionPath
from .parser.epath.ExecutionPathAnnotator import GreedyExecutionPathAnnotator
from .parser.regex import scanners

from .Command import Command 
from .cmdstr.CommandString import CommandString
from .components.inputs.Flag import Flag
from .components.inputs.Option import Option
from .components.inputs.factory import spawn_component 



# Utility functions to check aspects of a gxparam argument attribute

def argument_exists(gxparam: Param, xmltool: XMLToolDefinition, command: Command) -> bool:
    if hasattr(gxparam, 'argument') and gxparam.argument is not None:  #type: ignore
        return True
    return False

def argument_format(gxparam: Param, xmltool: XMLToolDefinition, command: Command) -> bool:
    banned_argument_chars = [' ', '/', '\\']
    if any([char in gxparam.argument for char in banned_argument_chars]):  #type: ignore
        return False
    return True

def argument_component_not_exists(gxparam: Param, xmltool: XMLToolDefinition, command: Command) -> bool:
    # check whether the argument is already known as a prefix 
    prefix_components: list[Flag | Option] = []
    prefix_components += command.get_flags()
    prefix_components += command.get_options()
    for component in prefix_components:
        if gxparam.argument == component.prefix: # type: ignore
            return False
    return True

def argument_has_command_presence(gxparam: Param, xmltool: XMLToolDefinition, command: Command) -> bool:
    # check the prefix appears in the cmd text
    # TODO improve. this is very limited.
    argument: str = gxparam.argument # type: ignore
    variable_fmt1: str = f'${gxparam.name}'
    variable_fmt2: str = f'${{{gxparam.name}}}'
    if argument is not None:
        # options
        if argument in xmltool.raw_command:
            return True
        # flags
        if variable_fmt1 in xmltool.raw_command or variable_fmt2 in xmltool.raw_command:
            return True
    return False


# Annotator classes

class ArgumentCommandAnnotator:
    def __init__(self, command: Command, xmltool: XMLToolDefinition):
        self.command = command
        self.xmltool = xmltool

    def annotate(self) -> None:
        # add any gxparams which hint they are components (or update the component)
        for gxparam in self.xmltool.list_inputs():
            if self.should_update_command_components(gxparam):
                gxparam = self.refine_argument(gxparam)
                self.update_command_components(gxparam)
    
    def should_update_command_components(self, gxparam: Param) -> bool:
        checks = [
            argument_exists,
            argument_format,
            argument_component_not_exists,
            argument_has_command_presence,
        ]
        for check in checks:
            if not check(gxparam, self.xmltool, self.command):
                return False
        return True

    def refine_argument(self, gxparam: Param) -> Param:
        """
        'argument' attribute of gxparam not always written with 
        correct number of preceeding dashes. this aims to discover
        the correct amount by looking in the <command> section for the
        argument
        """
        old_argument: str = gxparam.argument # type: ignore
        matches = scanners.get_preceeding_dashes(
            search_term=old_argument,
            text=self.xmltool.raw_command
        )
        if matches:
            num_dashes = max(len(dashes) for dashes in matches) 
            gxparam.argument = '-' * num_dashes + old_argument # type: ignore
        return gxparam

    def update_command_components(self, gxparam: Param) -> None:
        """
        gxparam definitely has 'argument' field
        the below are assumptions - galaxy XML can be written any way you want. 
        will need finer tuning / more disgression for use cases later?
        """
        assert(gxparam.argument) # type: ignore
        match gxparam:
            case BoolParam():
                self.handle_bool_param(gxparam)
            case SelectParam():
                self.handle_select_param(gxparam)
            case _:
                self.handle_generic_param(gxparam)

    def handle_bool_param(self, gxparam: BoolParam) -> None:
        assert(gxparam.argument)
        component = spawn_component('flag', ctext=gxparam.argument, ntexts=[])
        component.gxparam = gxparam
        self.command.update(component)

    def handle_select_param(self, gxparam: SelectParam) -> None:
        assert(gxparam.argument)
        if utils.select_is_bool(gxparam):
            component = spawn_component('flag', ctext=gxparam.argument, ntexts=[])
            self.command.update(component)
        else:
            for opt in gxparam.options:
                component = spawn_component('option', ctext=gxparam.argument, ntexts=[opt.value])
                component.gxparam = gxparam
                self.command.update(component)

    def handle_generic_param(self, gxparam: Param) -> None:
        component = spawn_component('option', ctext=gxparam.argument, ntexts=[])
        component.gxparam = gxparam
        self.command.update(component)    



class CmdstrCommandAnnotator:

    def __init__(self, command: Command, xmltool: XMLToolDefinition, cmdstrs: list[CommandString]):
        self.command = command
        self.xmltool = xmltool
        self.cmdstrs = cmdstrs
        self.epath_count: int = 0

    def annotate(self) -> None:
        for cmdstr in self.cmdstrs:
            for epath in cmdstr.main.get_execution_paths():
                logging.runtime_data(str(epath))
                self.extract_components(epath)

    def extract_components(self, epath: ExecutionPath) -> None:
        epath.id = self.epath_count
        epath = self.assign_epath_components(epath)
        self.update_command(epath)
        self.epath_count += 1
    
    def assign_epath_components(self, epath: ExecutionPath) -> ExecutionPath:
        annotator = GreedyExecutionPathAnnotator(epath, self.xmltool, self.command)
        return annotator.annotate()

    def update_command(self, epath: ExecutionPath) -> None:
        for component in epath.get_components():
            self.command.update(component)