

# classes
from startup.ExeSettings import WorkflowExeSettings
from workflows.io.WorkflowOutput import WorkflowOutput
from workflows.workflow.WorkflowFactory import WorkflowFactory
from workflows.workflow.Workflow import Workflow

# modules
from workflows.step.values.InputValueLinker import link_step_input_values
from workflows.step.outputs.OutputLinker import link_step_outputs_tool_outputs
from workflows.step.tools.assign import set_tools, set_tool_paths



"""
file ingests a galaxy workflow, then downloads and translates each tool
to a janis definition
"""

def parse_workflow(wsettings: WorkflowExeSettings) -> Workflow:
    workflow = init_workflow(wsettings)
    set_tools(wsettings, workflow)
    link_step_input_values(workflow)
    link_step_outputs_tool_outputs(workflow)
    set_outputs(workflow)
    set_tool_paths(wsettings, workflow)
    return workflow

def init_workflow(wsettings: WorkflowExeSettings) -> Workflow:
    # basic parsing workflow into internal representaiton
    galaxy_workflow_path = wsettings.get_galaxy_workflow_path()
    factory = WorkflowFactory()
    workflow = factory.create(galaxy_workflow_path)
    return workflow

def set_outputs(workflow: Workflow) -> None:
    for step in workflow.list_steps():
        for stepout in step.list_outputs():
            if stepout.is_wflow_out:
                toolout = stepout.tool_output
                assert(step.tool)
                assert(toolout)
                step_tag = workflow.tag_manager.get(step.get_uuid())
                toolout_tag = step.tool.tag_manager.get(toolout.get_uuid())
                workflow_output = WorkflowOutput(
                    step_tag=step_tag,
                    toolout_tag=toolout_tag,
                    janis_datatypes=stepout.janis_datatypes
                )
                workflow.add_output(workflow_output)









