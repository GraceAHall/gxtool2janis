

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from classes.tool.Param import Param 

# TODO i dont have a very good solution for the get() method.
# chose ABC but could use protocol instead

class SearchStrategy(ABC):    
    @abstractmethod
    def search(self, query: str, params: dict[str, Param]) -> Optional[Param]:
        """searches for a param using some concrete strategy"""
        ...

class DefaultSearchStrategy(SearchStrategy):
    def search(self, query: str, params: dict[str, Param]) -> Optional[Param]:
        """searches for a param using param name"""
        try:
            return params[query]
        except KeyError:
            return None

@dataclass
class LCAParam:
    split_name: list[str]
    param: Param

class LCASearchStrategy(SearchStrategy):
    def search(self, query: str, params: dict[str, Param]) -> Optional[Param]:
        """searches for a param using LCA"""
        split_query = query.split('.')
        remaining_params = self.init_datastructure(params)

        for i in range(1, len(split_query) + 1):
            remaining_params = [p for p in remaining_params if p.split_name[-i] == split_query[-i]]

        if len(remaining_params) > 0:
            return remaining_params[0].param

    def init_datastructure(self, params: dict[str, Param]):
        out: list[LCAParam] = []
        for param in params.values():
            out.append(LCAParam(param.name.split('.'), param))
        return out
        

class FilepathSearchStrategy(SearchStrategy):
    def search(self, query: str, params: dict[str, Param]) -> Optional[Param]:
        """
        searches for a param by matching the specified 
        from_work_dir path to a given filepath
        """
        for param in params.values():
            if hasattr(param, 'from_work_dir') and param.from_work_dir == query:
                return param



class ParamRegister(ABC):
    params: dict[str, Param] = dict()

    @abstractmethod
    def list(self) -> list[Param]:
        ...
    
    @abstractmethod
    def add(self, param: Param) -> None:
        ...
    
    @abstractmethod
    def get(self, strategy: str, query: str) -> Optional[Param]:
        ...
    
