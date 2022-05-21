

from tool.Tool import Tool

from workflows.workflow.Workflow import Workflow
from workflows.io.WorkflowInput import WorkflowInput
from workflows.step.WorkflowStep import WorkflowStep

from workflows.step.values.InputValue import (
    InputValue, 
    InputValueType, 
    DefaultInputValue, 
    RuntimeInputValue, 
    StaticInputValue
)
import workflows.step.values.create_value as value_utils


class ValueMigrator:
    """
    migrates InputValues to other InputValue types
    some assigned tool input values need to be migrated to other values.
    for example: a non-optional File input which was assigned 'None' would need
    to be migrated to a WorkflowInput (WorkflowInputInputValue) because this
    is something the user will need to supply at runtime (non-optional File). 
    """
    def __init__(self, step: WorkflowStep, workflow: Workflow):
        self.step = step
        self.tool: Tool = step.tool # type: ignore
        self.workflow = workflow

    def migrate(self) -> None:
        self.migrate_default_to_runtime()
        #self.migrate_connection_to_workflowinput()
        self.migrate_runtime_to_workflowinput()
        self.migrate_static_to_default()

    def migrate_default_to_runtime(self) -> None:
        """
        swap DefaultInputValue for RuntimeInputValue for InputValues
        where the default doens't look right. ie environment variables
        forces the user to supply a value for this input. 
        """
        register = self.step.tool_values
        for uuid, value in register.linked:
            if self.should_migrate_default_to_runtime(value):
                component = self.tool.get_input(uuid)
                input_value = value_utils.create_runtime(component)
                register.update_linked(uuid, input_value)
    
    def should_migrate_default_to_runtime(self, value: InputValue) -> bool:
        if isinstance(value, DefaultInputValue):
            if value.valtype == InputValueType.ENV_VAR:
                return True
        return False

    def migrate_static_to_default(self) -> None:
        """
        this marks whether the value supplied should be considered the default
        for the tool input. can be due to value being same as tool input default,
        or when the input value is None
        """
        register = self.step.tool_values
        for uuid, value in register.linked:
            if self.should_migrate_static_to_default(uuid, value):
                component = self.tool.get_input(uuid)
                input_value = value_utils.create_default(component)
                register.update_linked(uuid, input_value)

    def should_migrate_static_to_default(self, uuid: str, value: InputValue) -> bool:
        if isinstance(value, StaticInputValue):
            component = self.tool.get_input(uuid)
            if str(component.get_default_value()) == value.value:
                return True
        return False

    def migrate_runtime_to_workflowinput(self) -> None:
        """
        each tool input which is a RuntimeInputValue at this stage should be converted
        to a WorkflowInputInputValue. A RuntimeInputValue here means that we couldn't link
        a StepInput to any known ToolInputs (not direcly linkable), or that the StepInput
        is genuinely specified as a runtimevalue in the workflow. 
        A WorkflowInput will be created, and the user will have to supply a value for this 
        input when running the workflow. 
        """
        register = self.step.tool_values
        for uuid, value in register.linked:
            if self.should_migrate_runtime_to_workflowinput(value):
                component = self.tool.get_input(uuid)
                workflow_input = self.create_workflow_input(uuid)
                self.workflow.add_input(workflow_input)
                input_value = value_utils.create_workflow_input(component, workflow_input)
                input_value.is_runtime = True
                register.update_linked(uuid, input_value)

    def should_migrate_runtime_to_workflowinput(self, value: InputValue) -> bool:
        if isinstance(value, RuntimeInputValue):
            return True
        return False

    def create_workflow_input(self, comp_uuid: str) -> WorkflowInput:
        """creates a workflow input for the tool input component"""
        component = self.tool.get_input(comp_uuid)
        component_tag = self.tool.tag_manager.get(comp_uuid)
        step_id = self.step.metadata.step_id
        step_tag = self.workflow.get_step_tag_by_step_id(step_id)
        return WorkflowInput(
            name=component_tag,
            step_id=step_id,
            step_tag=step_tag,
            janis_datatypes=component.janis_datatypes,
            is_galaxy_input_step=False
        )




    # def migrate_connection_to_workflowinput(self) -> None:
    #     self.migrate_conn_to_winp_linked()
    #     self.migrate_conn_to_winp_unlinked()

    # def migrate_conn_to_winp_linked(self) -> None:
    #     for comp_uuid, value in self.valregister.list_values():
    #         if self.should_migrate_connection_to_workflowinput(value):
    #             assert(isinstance(value, ConnectionInputValue))
    #             component = self.tool.get_input(comp_uuid)
    #             workflow_input = self.workflow.get_input(step_id=value.step_id)
    #             assert(workflow_input)
    #             input_value = value_utils.create_workflow_input(component, workflow_input)
    #             self.valregister.update(comp_uuid, input_value)
    
    # def migrate_conn_to_winp_unlinked(self) -> None:
    #     unlinked: list[InputValue] = []
    #     for value in self.valregister.list_unlinked():
    #         if self.should_migrate_connection_to_workflowinput(value):
    #             assert(isinstance(value, ConnectionInputValue))
    #             workflow_input = self.workflow.get_input(step_id=value.step_id)
    #             assert(workflow_input)
    #             value = value_utils.cast_connection_to_workflowinput(value, workflow_input)
    #         unlinked.append(value)
    #     self.valregister.unlinked = unlinked

    # def should_migrate_connection_to_workflowinput(self, value: InputValue) -> bool:
    #     if isinstance(value, ConnectionInputValue):
    #         step = self.workflow.steps[value.step_id]
    #         if isinstance(step, InputDataStep):
    #             return True
    #     return False