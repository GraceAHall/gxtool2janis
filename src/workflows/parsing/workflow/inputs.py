

import json
from typing import Any
from workflows.entities.workflow.input import WorkflowInput

# INPUT STEP
def parse_input_step(step: dict[str, Any]) -> WorkflowInput:
    return WorkflowInput(
        name=format_input_step_name(step),
        step_id=step['id'],
        step_tag=None,
        is_array=format_input_step_array(step),
        is_galaxy_input_step=True,
        gx_datatypes=format_input_step_datatypes(step),
    )

def format_input_step_name(step: dict[str, Any]) -> str:
    if step['label'] and step['label'] != '':
        return step['label']
    elif step['inputs']:
        return step['inputs'][0]['name']
    else:
        raise RuntimeError()
    
def format_input_step_array(step: dict[str, Any]) -> bool:
    if step['type'] and step['type'] == 'data_collection_input':
        return True
    return False

def format_input_step_datatypes(step: dict[str, Any]) -> list[str]:
    tool_state = json.loads(step['tool_state'])
    if 'format' in tool_state:
        return tool_state['format']
    return []
    # TODO no idea if this needs recursive tool_state expansion

