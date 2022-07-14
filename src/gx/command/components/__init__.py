

# components
from .CommandComponent import CommandComponent
from .inputs.InputComponent import InputComponent
from .inputs.Flag import Flag
from .inputs.Option import Option
from .inputs.Positional import Positional

from .linux.Tee import Tee
from .linux.streams import StreamMerge

from .outputs.InputOutput import InputOutput
from .outputs.OutputComponent import OutputComponent
from .outputs.RedirectOutput import RedirectOutput
from .outputs.UncertainOutput import UncertainOutput
from .outputs.WildcardOutput import WildcardOutput


from .outputs.factory import create_output
from .inputs.factory import spawn_component