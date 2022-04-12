

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from command.components.CommandComponent import CommandComponent
from workflows.io.WorkflowInput import WorkflowInput
from workflows.workflow.Workflow import Workflow
from workflows.step.values.InputValue import (
    InputValue, 
    ConnectionInputValue, 
    RuntimeInputValue, 
    StaticInputValue, 
    DefaultInputValue,
    InputValueType,
    WorkflowInputInputValue
)
from workflows.step.values.utils import select_input_value_type
from workflows.step.inputs.StepInput import (
    ConnectionStepInput,
    StaticStepInput
)
from xmltool.param.Param import Param


@dataclass
class InputValueFactory(ABC):
    component: CommandComponent

    @abstractmethod
    def create(self) -> InputValue:
        ...
        
    def get_comptype(self) -> str:
        return type(self.component).__name__.lower() 


@dataclass
class ConnectionInputValueFactory(InputValueFactory):
    step_input: ConnectionStepInput
    workflow: Workflow

    def create(self) -> ConnectionInputValue:
        return ConnectionInputValue(
            step_id=self.step_input.step_id,
            step_output=self.step_input.output_name,
            comptype=self.get_comptype(),
            gxparam=self.step_input.gxparam
        )
    

@dataclass
class RuntimeInputValueFactory(InputValueFactory):

    def create(self) -> RuntimeInputValue:
        return RuntimeInputValue(
            comptype=self.get_comptype(),
            gxparam=self.component.gxparam
        )
    

@dataclass
class StaticInputValueFactory(InputValueFactory):
    step_input: StaticStepInput
    value_translations = {
        'false': False,
        'False': False,
        'true': True,
        'True': True,
        'null': None,
        'none': None,
        'None': None,
        '': None
    }

    def create(self) -> StaticInputValue:
        return StaticInputValue(
            value=self.get_value(),
            valtype=self.get_valtype(),
            comptype=self.get_comptype(),
            gxparam=self.step_input.gxparam
        )

    def get_value(self) -> Any:
        gx_value = self.step_input.value
        value = self.standardise_value(gx_value)
        return value

    def standardise_value(self, value: Any) -> Any:
        if value in self.value_translations:
            return self.value_translations[value]
        return value
    
    def get_valtype(self) -> InputValueType:
        value = self.get_value()
        return select_input_value_type(self.component, value)


@dataclass
class DefaultInputValueFactory(InputValueFactory):
    
    def create(self) -> DefaultInputValue:
        value = DefaultInputValue(
            value=self.get_value(),
            valtype=self.get_valtype(),
            comptype=self.get_comptype(),
            gxparam=self.component.gxparam
        )
        value.is_default_value = True
        return value

    def get_value(self) -> Any:
        return self.component.get_default_value()
    
    def get_valtype(self) -> InputValueType:
        return select_input_value_type(self.component, self.get_value())

    def get_gxparam(self) -> Optional[Param]:
        return self.component.gxparam

@dataclass
class WorkflowInputInputValueFactory(InputValueFactory):
    workflow_input: WorkflowInput
    
    def create(self) -> WorkflowInputInputValue:
        return WorkflowInputInputValue(
            input_uuid=self.workflow_input.get_uuid(),
            comptype=self.get_comptype(),
            gxparam=self.component.gxparam
        )