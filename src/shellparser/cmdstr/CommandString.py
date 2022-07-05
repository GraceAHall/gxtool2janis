


from dataclasses import dataclass

from shellparser.cmdstr.DynamicCommandStatement import DynamicCommandStatement
from shellparser.text.tokens.Tokens import Token


@dataclass
class CommandString:
    main: DynamicCommandStatement
    preprocessing: list[DynamicCommandStatement]
    postprocessing: list[DynamicCommandStatement]

    def get_original_tokens(self) -> list[Token]:
        """gets the original tokenized form of the command string"""
        out: list[Token] = []
        for statement in self.preprocessing:
            out += statement.get_tokens()
        out += self.main.get_tokens()
        for statement in self.postprocessing:
            out += statement.get_tokens()
        return out




