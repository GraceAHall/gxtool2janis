

from __future__ import annotations

from command.components.CommandComponent import BaseCommandComponent
from command.text.tokens.Tokens import Token
from typing import Any, Optional, Tuple
from xmltool.param.OutputParam import DataOutputParam, CollectionOutputParam
from command.components.ValueRecord import PositionalValueRecord
from command.components.linux import Stream
from datatypes import format_janis_str

class RedirectOutput(BaseCommandComponent):
    def __init__(self, tokens: Tuple[Token, Token]):
        super().__init__()
        self.redirect_token = tokens[0]
        self.file_token = tokens[1]
        self.stream: Stream = self.extract_stream()

        self.gxparam = self.file_token.gxparam
        self.value_record: PositionalValueRecord = PositionalValueRecord()
        self.value_record.add(self.file_token.text)

    @property
    def name(self) -> str:
        # get name from galaxy param if available
        if self.gxparam:
            return self.gxparam.name
        # otherwise, most commonly witnessed option value as name
        pseudo_name = self.value_record.get_most_common_value()
        if pseudo_name:
            return pseudo_name.split('.', 1)[0].split(' ', 1)[0]
        return self.file_token.text.split('.', 1)[0]
    
    @property
    def text(self) -> str:
        return self.redirect_token.text + ' ' + self.file_token.text

    @property
    def default_value(self) -> Any:
        raise NotImplementedError()

    @property
    def optional(self) -> bool:
        # NOTE - janis does not allow optional outputs
        return False

    @property
    def array(self) -> bool:
        match self.gxparam:
            case CollectionOutputParam() | DataOutputParam():
                return self.gxparam.array
            case _:
                pass
        return False

    @property
    def docstring(self) -> Optional[str]:
        if self.gxparam:
            return self.gxparam.docstring
        return ''
        #return f'examples: {", ".join(self.value_record.get_unique_values()[:5])}'
    
    def get_janis_datatype_str(self) -> str:
        """gets the janis datatypes then formats into a string for writing definitions"""
        datatype_str = format_janis_str(
            datatypes=self.janis_datatypes,
            is_optional=self.optional,
            is_array=self.array
        )
        return f'Stdout({datatype_str})'
    
    def is_append(self) -> bool:
        if self.redirect_token.text == '>>':
            return True
        return False

    def update(self, incoming: Any):
        # transfer galaxy param reference
        if not self.gxparam and incoming.gxparam:
            self.gxparam = incoming.gxparam
        # add values
        self.value_record.record += incoming.value_record.record

    def extract_stream(self) -> Stream:
        match self.redirect_token.text[0]:
            case '2':
                return Stream.STDERR
            case _:
                return Stream.STDOUT

    # def get_selector_str(self) -> str:
    #     if self.extract_stream() == Stream.STDOUT:
    #         return 'Stdout()'
    #     else:
    #         return 'Stderr()'

