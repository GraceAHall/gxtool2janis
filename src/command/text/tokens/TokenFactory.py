

from abc import ABC, abstractmethod
from typing import Optional

from command.text.tokens.Tokens import Token, TokenType
from command.text.regex import scanners as scanners
from command.text.regex.utils import get_base_variable
from xmltool.XMLToolDefinition import XMLToolDefinition
import command.text.tokens.utils as token_utils

class TokenOrderingStrategy(ABC):
    @abstractmethod
    def order(self, token_list: list[Token]) -> list[Token]:
        """selects a token in the list according to some prioritisation"""
        ...


class FirstTokenOrderingStrategy(TokenOrderingStrategy):
    def order(self, token_list: list[Token]) -> list[Token]:
        """selects a token in the list according to some prioritisation"""
        token_list.sort(key=lambda x: x.start)
        return token_list


class LongestTokenOrderingStrategy(TokenOrderingStrategy):
    def order(self, token_list: list[Token]) -> list[Token]:
        """selects a token in the list according to some prioritisation"""
        token_list.sort(key=lambda x: x.end - x.start)
        return token_list


class PriorityTokenOrderingStrategy(TokenOrderingStrategy):
    def order(self, token_list: list[Token]) -> list[Token]:
        priorities: dict[TokenType, int] = {
            TokenType.FUNCTION_CALL: 0,
            TokenType.BACKTICK_SHELL_STATEMENT: 0,
            TokenType.GX_KW_DYNAMIC: 1,
            TokenType.GX_KW_STATIC: 2,
            TokenType.KV_PAIR: 3,
            TokenType.KV_LINKER: 3,
            TokenType.GX_INPUT: 4,
            TokenType.GX_OUTPUT: 4,
            TokenType.ENV_VAR: 5,
            TokenType.QUOTED_NUM: 6,
            TokenType.QUOTED_STRING: 7,
            TokenType.RAW_STRING: 8,
            TokenType.RAW_NUM: 9,
            TokenType.LINUX_TEE: 10,
            TokenType.LINUX_REDIRECT: 10,
            TokenType.LINUX_STREAM_MERGE: 10,
            TokenType.EMPTY_STRING: 11,
            TokenType.UNKNOWN: 999,
        }
        token_list.sort(key=lambda x: priorities[x.type])
        return token_list


class TokenFactory:
    def __init__(self, xmltool: Optional[XMLToolDefinition]=None):
        self.xmltool = xmltool
        self.generic_scanners = [
            #(scanners.get_keyval_pairs, TokenType.KV_PAIR),
            (scanners.get_quoted_numbers, TokenType.QUOTED_NUM),
            (scanners.get_quoted_strings, TokenType.QUOTED_STRING),
            (scanners.get_raw_numbers, TokenType.RAW_NUM),
            (scanners.get_raw_strings, TokenType.RAW_STRING),
            (scanners.get_redirects, TokenType.LINUX_REDIRECT),
            (scanners.get_tees, TokenType.LINUX_TEE),
            (scanners.get_stream_merges, TokenType.LINUX_STREAM_MERGE),
            (scanners.get_dynamic_keywords, TokenType.GX_KW_DYNAMIC),
            (scanners.get_static_keywords, TokenType.GX_KW_STATIC),
            (scanners.get_empty_strings, TokenType.EMPTY_STRING),
            (scanners.get_all, TokenType.UNKNOWN)
        ]
        self.ordering_strategies: dict[str, TokenOrderingStrategy] = {
            'first':  FirstTokenOrderingStrategy(),
            'priority':  PriorityTokenOrderingStrategy(),
            'longest':  LongestTokenOrderingStrategy()
        }

    def create(self, word: str, prioritisation: str='priority') -> list[Token]:
        kv_split_tokens = self.create_kv_tokens(word, prioritisation)
        if kv_split_tokens:
            return kv_split_tokens
        else:
            token = self.create_single(word, prioritisation)
            return [token]

    def create_kv_tokens(self, word: str, prioritisation: str='priority') -> list[Token]:
        left_token_allowed_types = [
            TokenType.RAW_STRING,
            TokenType.RAW_NUM,
        ]
        right_token_allowed_types = [
            TokenType.RAW_STRING,
            TokenType.RAW_NUM,
            TokenType.QUOTED_STRING,
            TokenType.QUOTED_NUM,
            TokenType.GX_INPUT,
            TokenType.GX_OUTPUT,
            TokenType.GX_KW_DYNAMIC,
            TokenType.GX_KW_STATIC,
            TokenType.ENV_VAR
        ]
        delims = ['=', ':']
        for delim in delims:
            if delim in word:
                left, right = word.split(delim, 1)
                left_token = self.create_single(left, prioritisation)
                right_token = self.create_single(right, prioritisation)
                if left_token.type in left_token_allowed_types:
                    if right_token.type in right_token_allowed_types:
                        return [left_token, token_utils.spawn_kv_linker(delim), right_token]
        return []

    def create_single(self, word: str, prioritisation: str='priority') -> Token:
        """
        extracts the best token from a word.
        where multiple token types are possible, selection can be made 
        """
        token_list = self.get_all_tokens(word)
        token_list = self.perform_default_ordering(token_list)
        final_ordering = self.perform_final_ordering(token_list, prioritisation)
        final_token = self.select_final_token(final_ordering)
        return final_token

    def select_final_token(self, ordered_token_list: list[Token]) -> Token:
        # a few overrides to ensure things make sense 
        
        # full length string (helps for )
        # if self.has_full_length_quoted_token(ordered_token_list):
        #     if not self.has_semi_full_length_var_match(ordered_token_list):
       
        # normal approach (priority based)
        final_token = ordered_token_list[0]
        return final_token

    def perform_default_ordering(self, token_list: list[Token]) -> list[Token]:
        #default orderings (low to high priority) first, longest, priority
        for strategy in self.ordering_strategies.values():
            token_list = strategy.order(token_list)
        return token_list
        
    def perform_final_ordering(self, token_list: list[Token],  prioritisation: str) -> list[Token]:
        # overriding final prioritisation
        return self.ordering_strategies[prioritisation].order(token_list)

    def get_all_tokens(self, the_string: str) -> list[Token]:
        """gets all the possible token interpretations of the_string"""  
        tokens: list[Token] = []
        tokens += self.get_dunder_token(the_string)
        tokens += self.get_generic_tokens(the_string)
        tokens += self.get_variable_tokens(the_string)
        return tokens

    def get_dunder_token(self, the_string: str) -> list[Token]:
        if the_string == '__FUNCTION_CALL__':
            return [token_utils.spawn_function_call()]
        if the_string == '__BACKTICK_SHELL_STATEMENT__':
            return [token_utils.spawn_backtick_section()]
        return []

    def get_generic_tokens(self, the_string: str) -> list[Token]:
        """gets all tokens except galaxy/env variables"""
        tokens: list[Token] = []
        for scanner_func, ttype in self.generic_scanners:
            matches = scanner_func(the_string)
            tokens += [Token(m, ttype) for m in matches]
        return tokens

    def get_variable_tokens(self, the_string: str) -> list[Token]:
        """gets tokens for galaxy/env variables"""
        tokens: list[Token] = []
        matches = scanners.get_variables_fmt1(the_string)
        matches += scanners.get_variables_fmt2(the_string)
        base_vars = [get_base_variable(m) for m in matches]
        
        for m, varname in zip(matches, base_vars):
            if varname and self.xmltool:
                if self.xmltool.get_input(varname):
                    tokens.append(Token(m, TokenType.GX_INPUT, gxparam=self.xmltool.get_input(varname)))
                elif self.xmltool.get_output(varname):
                    tokens.append(Token(m, TokenType.GX_OUTPUT, gxparam=self.xmltool.get_output(varname)))
                else:
                    tokens.append(Token(m, TokenType.ENV_VAR))
        return tokens
    
    