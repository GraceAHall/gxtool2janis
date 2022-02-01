




from typing import Union
from datetime import date


from tool.tool_definition import GalaxyToolDefinition
from command.CommandComponents import Output
from classes.janis.DatatypeExtractor import DatatypeExtractor

from logger.Logger import Logger
from command.Command import Flag, Option, Positional, TokenType
from janis_core.utils.metadata import ToolMetadata

from utils.galaxy_utils import is_tool_parameter, is_tool_output

CommandComponent = Union[Positional, Flag, Option]


class JanisFormatter:
    def __init__(self, tool: Tool, janis_out_path: str, logger: Logger) -> None:
        self.tool = tool
        self.janis_out_path = janis_out_path
        self.logger = logger
        self.dtype_extractor = DatatypeExtractor(tool.param_register, tool.out_register, logger)

        # janis attributes to create
        self.commandtool: str = ''
        self.inputs: list[str] = []
        self.outputs: list[str] = []
        self.metadata: list[str] = []
        self.datatype_imports: set[str] = set()   
        self.default_imports: dict[str, set[str]] = {
            'janis_core': {
                'CommandToolBuilder', 
                'ToolInput', 
                'ToolOutput',
                'InputSelector',
                'WildcardSelector',
                'Array',
                'Optional',
                'UnionType',
                'Stdout'
            }
        }
        self.extra_prohibited_keys = {
            "identifier",
            "tool",
            "scatter",
            "ignore_missing",
            "output",
            "input",
            "inputs"
        }


    def format(self) -> None:
        self.commandtool = self.gen_commandtool()
        self.inputs = self.gen_inputs()
        self.outputs = self.gen_outputs()
        self.imports = self.gen_imports()
        self.main_call = self.gen_main_call()
        

    def gen_commandtool(self) -> str:
        """
        each str elem in out list is tool output
        - contributors
        - dateCreated
        - dateUpdated
        """
        #metadata = self.get_tool_metadata()

        base_command = self.infer_base_command()
        toolname = self.tool.id.replace('-', '_').lower()
        version = self.tool.version
        container = self.tool.container
        
        citation = "NOT NOW ILL DO IT LATER"
        # citaiton = self.tool.get_main_citation()
        
        out_str = f'\n{toolname} = CommandToolBuilder(\n'
        out_str += f'\ttool="{toolname}",\n'
        out_str += f'\tbase_command={base_command},\n'
        out_str += f'\tinputs=inputs,\n'
        out_str += f'\toutputs=outputs,\n'

        if self.container_version_mismatch():
            out_str += (f'\t# WARN contaniner version mismatch\n\t# tool requirement version was {self.tool.main_requirement["version"]}\n\t# container version is {container["version"]}\n')

        out_str += f'\tcontainer="{container["url"]}",\n'
        out_str += f'\tversion="{version}",\n'
        #out_str += f'\tfriendly_name="{friendly_name}",\n'
        #out_str += f'\targuments="{arguments}",\n'
        #out_str += f'\tenv_vars="{env_vars}",\n'
        #out_str += f'\ttool_module="{tool_module}",\n'
        out_str += f'\ttool_provider="{citation}",\n'
        #out_str += f'\tmetadata="{metadata}",\n'
        #out_str += f'\tcpus="{cpus}",\n'
        #out_str += f'\tmemory="{memory}",\n'
        #out_str += f'\ttime="{time}",\n'
        #out_str += f'\tdisk="{disk}",\n'
        #out_str += f'\tdirectories_to_create="{directories_to_create}",\n'
        #out_str += f'\tfiles_to_create="{files_to_create}",\n'
        out_str += f'\tdoc="""{self.tool.help}""",\n'
        out_str += ')\n'

        return out_str


    def get_tool_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            contributors=["janis"],
            dateCreated=date.today(),
            dateUpdated=date.today(),
            institution="<who produces the tool>",
            keywords=["list", "of", "keywords"],
            documentationUrl="<url to original documentation>",
            short_documentation="Short subtitle of tool",
            documentation="""Extensive tool documentation here """.strip(),
            doi=None,
            citation=None,
    )


    def infer_base_command(self) -> str:
        """
        base command is all positionals before options begin, where all sources are RAW_STRING types and only 1 value was witnessed.    
        """
        # get positionals before opts
        positionals = self.tool.command.get_positionals()
        positionals = [p for p in positionals if not p.is_after_options]

        # get positionals which are part of base command
        base_positionals = []
        for p in positionals:
            p_types = p.get_token_types()
            if TokenType.RAW_STRING in p_types and len(p_types) == 1 and p.has_unique_value():
                base_positionals.append(p)

        # remove these Positional CommandComponents as they are now considered 
        # base command, not positionals
        for p in base_positionals:
            self.tool.command.remove_positional(p.pos)

        # format to string
        base_command = [p.get_token_values(as_list=True)[0] for p in base_positionals]
        base_command = ['"' + cmd + '"' for cmd in base_command]
        base_command = ', '.join(base_command)
        base_command = '[' + base_command + ']'
        return base_command


    def container_version_mismatch(self) -> bool:
        target_version = self.tool.main_requirement['version']
        acquired_version = self.tool.container['version']
        if target_version != acquired_version:
            return True
        return False


    def gen_inputs(self) -> list[str]:
        """
        inputs are any positional, flag or option except the following:
            - positional is part of the base_command (will have been removed)
            - positional with TokenType = GX_OUT
            - option with only 1 source token and the TokenType is GX_OUT
        """
        inputs = []

        command = self.tool.command

        inputs.append('\n\t# positionals\n')
        for posit in command.get_positionals():
            new_input = self.gen_positional_toolinput(posit)
            inputs.append(new_input)

        inputs.append('\n\t# flags\n')
        for flag in command.get_flags():
            new_input = self.gen_flag_toolinput(flag)
            inputs.append(new_input)

        inputs.append('\n\t# options\n')
        for opt in command.get_options():
            new_input = self.gen_option_toolinput(opt)
            inputs.append(new_input)

        return inputs
        

    def gen_positional_toolinput(self, positional: Positional) -> str:
        """
        creates a janis ToolInput string from a Positional. 
        """
        c_data = self.extract_janis_positional(positional)

        if not self.is_valid_positional(c_data):
            raise Exception('invalid positional')

        self.update_datatype_imports(c_data['datatypes'])
        positional_str = self.format_positional_to_string(c_data)
        return positional_str


    def extract_janis_positional(self, posit: Positional) -> dict[str, str]:       
        c_data = {}

        if posit.galaxy_object is not None:
            tag = posit.galaxy_object.name
        else:
            tag = '_'.join(posit.get_token_values(as_list=True))
        
        c_data['tag'] = self.validate_tag(tag)
        c_data['pos'] = posit.pos
        docstring = self.get_docstring(posit)
        c_data['docstring'] = self.validate_docstring(docstring)
        
        c_data['default'] = posit.get_default_value()
        # if not c_data['default'] or c_data['default'] == '':
        #     ext = c_data['datatypes'][0].split(',')[0]
        #     c_data['default'] = c_data['tag'] + '.' + ext

        c_data['datatypes'] = self.dtype_extractor.extract(posit)    
        c_data['is_array'] = posit.is_array()
        c_data['is_optional'] = posit.is_optional() 
        c_data['typestring'] = self.format_typestring(c_data['datatypes'], c_data['is_array'], c_data['is_optional']) 

        return c_data


    def validate_tag(self, tag: str) -> str:
        """
        to satisfy janis tag requirements
        to avoid janis reserved keywords
        """
        tag = tag.strip('\\/')
        tag = tag.replace('-', '_')
        tag = tag.replace('/', '_')
        tag = tag.replace('\\', '_')
        if tag in self.extra_prohibited_keys or len(tag) == 1:
            tag += '_janis'

        return tag


    def get_docstring(self, component: CommandComponent) -> str:
        gxobj = component.galaxy_object
        if gxobj:
            if is_tool_parameter(gxobj):
                docstring = gxobj.label + ' ' + gxobj.help
            elif is_tool_output(gxobj):
                docstring = gxobj.label
                docstring = docstring.replace('${tool.name} on ${on_string}', '').strip(': ')
        
        elif type(component) in [Positional, Option]:
            values = component.get_token_values(as_list=True)
            docstring = f'possible values: {", ".join(values[:5])}'
        
        else:
            docstring = ''

        return docstring
    
    
    def validate_docstring(self, docstring: str) -> str:
        """
        to avoid janis reserved keywords

        """
        docstring = docstring.replace('"', '\\"')

        return docstring

    
    def format_typestring(self, datatypes: list[dict], is_array, is_optional) -> str:
        """
        turns a component and datatype dict into a formatted string for janis definition.
        the component is used to help detect array / optionality. 
            String
            String(optional=True)
            Array(String(), optional=True)
            etc
        """
        
        # just work with the classname for now
        datatypes = [d['classname'] for d in datatypes]
        
        # handle union type
        if len(datatypes) > 1:
            dtype = ', '.join(datatypes)
            dtype = "UnionType(" + dtype + ")"
        else:
            dtype = datatypes[0]
        
        # not array not optional
        if not is_optional and not is_array:
            out_str = f'{dtype}'

        # array and not optional
        elif not is_optional and is_array:
            out_str = f'Array({dtype})'
        
        # not array and optional
        elif is_optional and not is_array:
            out_str = f'{dtype}(optional=True)'
        
        # array and optional
        elif is_optional and is_array:
            out_str = f'Array({dtype}(), optional=True)'

        return out_str


    def is_valid_positional(self, c_data: dict[str, str]) -> bool:
        # needs default if not optional
        if not c_data['is_optional']:
            if not c_data['default'] or c_data['default'] == '':
                return False

        # at least 1 datatype needs to be supplied 
        elif len(c_data['datatypes']) == 0:
            return False

        return True
 
    
    def update_datatype_imports(self, datatypes: list[dict[str, str]]) -> None:
        """
        update the import list for the datatypes it needs.
        """
        for dtype in datatypes:
            import_str = f'from {dtype["import_path"]} import {dtype["classname"]}'
            self.datatype_imports.add(import_str)


    def format_positional_to_string(self, c_data: dict[str, str]) -> str:
        out_str = '\tToolInput(\n'
        out_str += f'\t\t"{c_data["tag"]}",\n'
        out_str += f'\t\t{c_data["typestring"]},\n'
        out_str += f'\t\tposition={c_data["pos"]},\n'

        # pure jank
        if c_data['default']:
            if len(c_data['datatypes']) == 1 and c_data['datatypes'][0]['classname'] in ['Float', 'Integer']:
                out_str += f'\t\tdefault={c_data["default"]},\n'
            else:
                out_str += f'\t\tdefault="{c_data["default"]}",\n'
        
        out_str += f'\t\tdoc="{c_data["docstring"]}"\n'
        out_str += '\t),\n'

        return out_str


    # def get_gx_obj(self, query_ref: str):
    #     varname, obj = self.tool.param_register.get(query_ref)
    #     if obj is None:
    #         varname, obj = self.tool.out_register.get(query_ref) 
    #     return varname, obj


    def gen_flag_toolinput(self, flag: Flag) -> str:
        """
        creates a janis ToolInput string from a Flag. 
        """
        c_data = self.extract_janis_flag(flag)

        if not self.is_valid_flag(c_data):
            raise Exception('invalid flag')

        flag_str = self.format_flag_to_string(c_data)
        return flag_str

    
    def extract_janis_flag(self, flag: Flag) -> dict[str, str]:
        c_data = {}

        tag = flag.prefix.lstrip('-')
        c_data['tag'] = self.validate_tag(tag)
        c_data['prefix'] = flag.prefix
        c_data['pos'] = flag.pos

        default = flag.get_default_value()
        if not default or default == '':
            c_data['default'] = False
        else:
            c_data['default'] = True
            
        docstring = self.get_docstring(flag) 
        c_data['docstring'] = self.validate_docstring(docstring)
        c_data['is_optional'] = flag.is_optional()

        typestring = 'Boolean'
        if c_data['is_optional']:
            typestring += "(optional=True)"
        c_data['typestring'] = typestring

        return c_data


    def is_valid_flag(self, c_data: dict[str, str]) -> bool:
        return True


    def format_flag_to_string(self, c_data: dict[str, str]) -> str:
        """
        flag example
            'cs_string',
            Boolean(optional=True/False),
            prefix="--cs_string",
            doc=""
        """
        out_str = '\tToolInput(\n'
        out_str += f'\t\t"{c_data["tag"]}",\n'
        out_str += f'\t\t{c_data["typestring"]},\n'
        out_str += f'\t\tprefix="{c_data["prefix"]}",\n'
        out_str += f'\t\tposition={c_data["pos"]},\n'
        out_str += f'\t\tdefault={c_data["default"]},\n'
        out_str += f'\t\tdoc="{c_data["docstring"]}"\n'
        out_str += '\t),\n'

        return out_str
        

    def gen_option_toolinput(self, opt: Option) -> str:
        """
        creates a janis ToolInput string from an Option. 
        """
        c_data = self.extract_janis_option(opt)
        if not self.is_valid_option(c_data):
            raise Exception('invalid option')

        self.update_datatype_imports(c_data['datatypes'])
        option_str = self.format_option_to_string(c_data)
        return option_str


    def extract_janis_option(self, opt: Option) -> dict[str, str]:
        c_data = {}

        tag = opt.prefix.lstrip('-')
        c_data['tag'] = self.validate_tag(tag)
        c_data['prefix'] = opt.prefix
        c_data['pos'] = opt.pos
        c_data['default'] = opt.get_default_value()
        c_data['delim'] = opt.delim
        
        c_data['datatypes'] = self.dtype_extractor.extract(opt)    
        c_data['is_array'] = opt.is_array()
        c_data['is_optional'] = opt.is_optional() 
        c_data['typestring'] = self.format_typestring(c_data['datatypes'], c_data['is_array'], c_data['is_optional']) 
        
        docstring = self.get_docstring(opt)
        c_data['docstring'] = self.validate_docstring(docstring)

        return c_data


    def is_valid_option(self, c_data: dict[str, str]) -> bool:
        return True
    

    def format_option_to_string(self, c_data: dict[str, str]) -> str:
        """
        option example
            'max_len',
            Int(optional=True/False),
            prefix='--max_len1',
            doc="[Optional] Max read length",
        """
        out_str = '\tToolInput(\n'
        out_str += f'\t\t"{c_data["tag"]}",\n'
        out_str += f'\t\t{c_data["typestring"]},\n'

        if c_data['delim'] != ' ':
            out_str += f'\t\tprefix="{c_data["prefix"] + c_data["delim"]}",\n'
            out_str += f'\t\tseparate_value_from_prefix=False,\n'
        else:
            out_str += f'\t\tprefix="{c_data["prefix"]}",\n'

        out_str += f'\t\tposition={c_data["pos"]},\n'
        
        if c_data["default"]:
            if all(dtype['classname'] in ['Float', 'Int'] for dtype in c_data["datatypes"]):
                out_str += f'\t\tdefault={c_data["default"]},\n'
            else:
                out_str += f'\t\tdefault="{c_data["default"]}",\n'
        
        out_str += f'\t\tdoc="{c_data["docstring"]}"\n'
        out_str += '\t),\n'

        return out_str


    def gen_outputs(self) -> list[str]:
        """
        each str elem in 'outputs' is tool output
        """
        outputs = []

        # galaxy output objects
        command = self.tool.command
        for output in command.outputs:           
            output_string = self.gen_janis_output(output) 
            outputs.append(output_string)
        
        return outputs

        
    def gen_janis_output(self, output: Output) -> str:
        """
        creates a janis ToolInput string from an Option. 
        """
        c_data = self.extract_janis_output(output)
        if not self.is_valid_output(c_data):
            raise Exception('invalid option')

        if c_data['selector']:
            self.default_imports['janis_core'].add(c_data['selector'])
        
        self.update_datatype_imports(c_data['datatypes'])
        output_str = self.format_output_to_string(c_data)
        return output_str


    def extract_janis_output(self, output: Output) -> dict[str, str]:
        c_data = {}

        c_data['tag'] = self.validate_tag(output.get_name())
        c_data['is_stdout'] = output.is_stdout
        
        # datatype
        c_data['datatypes'] = self.dtype_extractor.extract(output)
        c_data['is_array'] = output.is_array()
        c_data['is_optional'] = output.is_optional()
        c_data['typestring'] = self.format_typestring(c_data['datatypes'], c_data['is_array'], c_data['is_optional'])

        c_data['selector'] = None
        c_data['selector_contents'] = None

        if not c_data['is_stdout']:
            c_data['selector'] = output.get_selector()
            c_data['selector_contents'] = output.get_selector_contents(self.tool.command)

            # if selector is InputSelector, its referencing an input
            # that input tag will have been converted to a janis-friendly tag
            # same must be done to the selector contents, hence the next 2 lines:
            if c_data['selector'] == 'InputSelector':
                c_data['selector_contents'] = self.validate_tag(c_data['selector_contents'])  
        
        # docstring
        docstring = self.get_docstring(output)
        c_data['docstring'] = self.validate_docstring(docstring)

        return c_data


    def is_valid_output(self, c_data: dict[str, str]) -> bool:
        return True


    def format_output_to_string(self, c_data: dict[str, str]) -> str:
        # string formatting
        out_str = '\tToolOutput(\n'
        out_str += f'\t\t"{c_data["tag"]}",\n'

        if c_data['is_stdout']:
            out_str += f'\t\tStdout({c_data["typestring"]}),\n'
        else:
            out_str += f'\t\t{c_data["typestring"]},\n'
            out_str += f'\t\tselector={c_data["selector"]}("{c_data["selector_contents"]}"),\n'
        
        out_str += f'\t\tdoc="{c_data["docstring"]}"\n'
        out_str += '\t),\n'

        return out_str


    def gen_imports(self) -> list[str]:
        out_str = ''
        out_str += 'import sys\n'
        out_str += 'import os\n'
        out_str += 'sys.path.append(os.getcwd() + "\\src")\n'
        
        # default imports from janis core
        if len(self.default_imports['janis_core']) > 0:
            modules = ', '.join(self.default_imports['janis_core'])
            out_str += f'\nfrom janis_core import {modules}\n'

        # at least 1 boolean flag present
        if len(self.tool.command.get_flags()) > 0:
            import_str = 'from janis_core.types.common_data_types import Boolean'
            out_str += f'{import_str}\n'

        # all the other datatypes we found
        for import_str in list(self.datatype_imports):
            out_str += f'{import_str}\n'

        return out_str

    
    def gen_main_call(self) -> str:
        """
        generates the __main__ call to translate to wdl on program exec
        """
        toolname = self.tool.id.replace('-', '_')

        out_str = '\n'
        out_str += 'if __name__ == "__main__":\n'
        out_str += f'\t{toolname}().translate(\n'
        out_str += '\t\t"wdl", to_console=True\n'
        out_str += '\t)'
        return out_str
        

    def write(self) -> None:
        """
        writes the text to tool def fil

        """

        with open(self.janis_out_path, 'w', encoding="utf-8") as fp:
            fp.write(self.imports + '\n\n')

            fp.write('inputs = [')
            for inp in self.inputs:
                fp.write(inp)
            fp.write(']\n\n')

            fp.write('outputs = [\n')
            for out in self.outputs:
                fp.write(out)
            fp.write(']\n\n')

            fp.write(self.commandtool + '\n')
            fp.write(self.main_call + '\n')



