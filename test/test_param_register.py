

import unittest

from classes.tool.OutputRegister import OutputRegister
from classes.param.InputParam import (
    BoolToolParam,
    IntegerToolParam, 
    TextToolParam, 
    FloatToolParam,
    DataToolParam
)


class TestRegister(unittest.TestCase):
    """
    tests the ParamRegister code
    this is kinda bad because it mutates register then asserts register length
    """
    def setUp(self) -> None:
        self.register = OutputRegister()
        self.register.add(TextToolParam('param1'))
        self.register.add(IntegerToolParam('param2'))
        self.register.add(FloatToolParam('param3.has.extra.path'))
        self.register.add(BoolToolParam('param4'))
        self.register.add(DataToolParam('param5', 'fasta'))

    def test_list(self) -> None:
        self.assertEquals(len(self.register.list()), 6)

    def test_add_param(self) -> None:
        self.register.add(TextToolParam('param6'))
        param_list = self.register.list()
        self.assertEquals(len(param_list), 6)
    
    def test_add_existing_param(self) -> None:
        self.register.add(TextToolParam('param1'))
        param_list = self.register.list()
        self.assertEquals(len(param_list), 5)

    def test_get_basic(self) -> None:
        param = self.register.get('default', 'param2')
        self.assertEquals(param.name, 'param2')
    
    def test_get_lca(self) -> None:
        param = self.register.get('lca', 'extra.path')
        self.assertEquals(param.name, 'param3.has.extra.path')
    
    def test_get_lca_fullpath(self) -> None:
        param = self.register.get('lca', 'param3.has.extra.path')
        self.assertEquals(param.name, 'param3.has.extra.path')
        


