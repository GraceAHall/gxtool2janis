



from typing import Optional


class TagFormatter:
    def __init__(self):
        self.prohibited_key_counts = {
            "identifier": 0,
            "tool": 0,
            "scatter": 0,
            "ignore_missing": 0,
            "output": 0,
            "input": 0,
            "inputs": 0
        }

    def format(self, the_string: str, datatype: Optional[str]=None) -> str:
        the_string = the_string.lower()
        the_string = self.replace_non_alphanumeric(the_string)
        the_string = self.handle_prohibited_key(the_string)
        the_string = self.handle_short_tag(the_string, datatype)
        the_string = self.encode(the_string)
        return the_string

    def replace_non_alphanumeric(self, the_string: str) -> str:
        """
        to satisfy janis tag requirements
        to avoid janis reserved keywords
        """
        the_string = the_string.strip('\\/-$')
        the_string = the_string.replace('-', '_')
        the_string = the_string.replace('/', '_')
        the_string = the_string.replace('\\', '_')
        the_string = the_string.replace('"', '')
        the_string = the_string.replace("'", '')
        return the_string

    def handle_prohibited_key(self, the_string: str) -> str:
        if the_string in self.prohibited_key_counts:
            self.prohibited_key_counts[the_string] += 1
            int_suffix = self.prohibited_key_counts[the_string]
            the_string = f'the_string{int_suffix}'
        return the_string

    def handle_short_tag(self, the_string: str, datatype: Optional[str]) -> str:
        if len(the_string) == 1 and datatype:
            if the_string[0].isnumeric():
                the_string = f'{datatype.lower()}_{the_string}'
            else:
                the_string = f'{the_string}_{datatype.lower()}'
        return the_string

    def encode(self, the_string: str) -> str:
        return fr'{the_string}'
    



        