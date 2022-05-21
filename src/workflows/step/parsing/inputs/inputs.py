
from typing import Any
from runtime.ExeSettings import ToolExeSettings
from workflows.io.WorkflowInput import WorkflowInput

from workflows.step.inputs.StepInputRegister import StepInputRegister
from workflows.workflow.Workflow import Workflow
from workflows.step.inputs.StepInput import (
    StepInput, 
    init_connection_step_input, 
    init_static_step_input, 
    init_runtime_step_input, 
    init_workflow_input_step_input
)
from .standardisation import standardise_tool_state
from .flatten import get_flattened_tool_state
from .resolve import resolve_values


def parse_step_inputs(gxstep: dict[str, Any], workflow: Workflow, esettings: ToolExeSettings) -> StepInputRegister:
    gxstep['tool_state'] = get_flattened_tool_state(gxstep)
    gxstep['tool_state'] = resolve_values(esettings, gxstep)
    gxstep['tool_state'] = standardise_tool_state(gxstep)
    parser = ToolStepInputParser(gxstep, workflow)
    inputs = parser.parse()
    return StepInputRegister(inputs)


class InputDataStepParser:
    def parse(self, step: dict[str, Any])  -> WorkflowInput:
        return WorkflowInput(
            name=step['inputs'][0]['name'],
            step_id=step['id'],
            step_tag=None,
            gx_datatypes=step['tool_state']['format'] if 'format' in step['tool_state'] else [],
            is_galaxy_input_step=True
        )


class ToolStepInputParser:
    def __init__(self, gxstep: dict[str, Any], workflow: Workflow):
        self.gxstep = gxstep
        self.workflow = workflow
        self.inputs: dict[str, StepInput] = {}

    def parse(self) -> list[StepInput]:
        self.parse_connection_inputs()
        self.parse_static_inputs()
        self.parse_user_defined_inputs()
        return list(self.inputs.values())

    def parse_connection_inputs(self) -> None:
        for name, details in self.gxstep['input_connections'].items(): #type: ignore
            step_id = details['id']
            if self.workflow.get_input(step_id=step_id):
                self.inputs[name] = init_workflow_input_step_input(name, details)
            else:
                self.inputs[name] = init_connection_step_input(name, details)

    def parse_static_inputs(self) -> None:
        for name, value in self.gxstep['tool_state'].items(): #type: ignore
            if name not in self.inputs:
                if not name.endswith('__') and value != 'RuntimeValue':
                    self.inputs[name] = init_static_step_input(name, value)

    def parse_user_defined_inputs(self) -> None:
        for name, value in self.gxstep['tool_state'].items(): #type: ignore
            if name not in self.inputs:
                if value == 'RuntimeValue':
                    self.inputs[name] = init_runtime_step_input(name)
