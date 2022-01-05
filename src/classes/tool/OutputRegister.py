

from typing import Optional

from classes.param.ToolParam import ToolParam
from .ParamRegister import (
    ParamRegister,
    DefaultSearchStrategy,
    LCASearchStrategy,
    FilepathSearchStrategy
)


# TODO i dont have a very good solution for the get() method.



class OutputRegister(ParamRegister):

    def list(self) -> list[ToolParam]:
        return list(self.params.values())
    
    def add(self, param: ToolParam) -> None:
        """adds a param to register. enforces unique param var names"""
        if param.name not in self.params:
            self.params[param.name] = param            

    def get(self, strategy: str, query: str) -> Optional[ToolParam]:
        """performs search using the specified search strategy"""
        strategy_map = {
            'default': DefaultSearchStrategy(),
            'lca': LCASearchStrategy(),
            'filepath': FilepathSearchStrategy(),
        }

        search_strategy = strategy_map[strategy]
        return search_strategy.search(query, self.params)

    # def create_output_from_text(self, text: str) -> None:
    #     """
    #     creates a new output using a dummy et.Element
    #     the new et.Element node is populated with some default details
    #     then is parsed as normal created the new output. 
    #     the output is added to our collection of outputs. 
    #     """
    #     # TODO 
    #     raise Exception('TODO: make galaxy ToolOutput not old Output')
    #     # create dummy node
    #     name = text.split('.', 1)[0]
    #     dummy_node = et.Element('data', attrib={'name': name, 'format': 'file', 'from_work_dir': text})
        
    #     # create and parse output
    #     new_output = ToolOutput(dummy_node)
    #     new_output.parse()

    #     # add to collection
    #     self.add([new_output])



