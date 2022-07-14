


from typing import Any
from gx.gxtool.load import load_xmltool
from .simplification.aliases import resolve_aliases
from .cheetah.evaluation import sectional_evaluate
from .simplification.simplify import simplify_cmd


def load_command() -> str:
    xmltool = load_xmltool()
    text = simplify_cmd(xmltool.raw_command, 'xml')
    text = resolve_aliases(text)
    return text

def load_partial_cheetah_command(inputs_dict: dict[str, Any]) -> str:
    xmltool = load_xmltool()
    text = xmltool.raw_command
    text = simplify_cmd(text, 'cheetah')
    text = sectional_evaluate(text, inputs=inputs_dict)
    text = resolve_aliases(text)
    return text
