


from command.components.inputs import Flag, Option
from command.tokens.Tokens import Token, TokenType
from xmltool.param.InputParam import BoolParam, SelectParam
import command.regex.scanners as scanners

NON_VALUE_TOKENTYPES = set([
    TokenType.FUNCTION_CALL, 
    TokenType.BACKTICK_SHELL_STATEMENT, 
    TokenType.LINUX_TEE, 
    TokenType.LINUX_REDIRECT,
    TokenType.LINUX_STREAM_MERGE,
    TokenType.END_STATEMENT,
    TokenType.EXCISION,
])

def is_bool_select(token: Token) -> bool:
    if token.type == TokenType.GX_INPUT:
        match token.gxparam:
            case BoolParam():
                return True
            case SelectParam():
                if len(token.gxparam.options) > 0:
                    return True
            case _:
                pass
    return False


# FLAG STUFF

def boolparam_then_gxparam(ctoken: Token, ntoken: Token) -> bool:
    # for when boolparam followed by a different gxparam
    if looks_like_a_flag(ctoken):
        if isinstance(ctoken.gxparam, BoolParam):
            if ctoken.gxparam and ntoken.gxparam:  # curr and next both have gxparams
                if ctoken.gxparam.name != ntoken.gxparam.name:  # ensure not same gxparam
                    return True
    return False

def flag_then_flag(ctoken: Token, ntoken: Token) -> bool:
    if looks_like_a_flag(ctoken) and looks_like_a_flag(ntoken):
        return True
    return False

def flag_then_null(ctoken: Token, ntoken: Token) -> bool:
    if looks_like_a_flag(ctoken) and ntoken.type in NON_VALUE_TOKENTYPES:
        return True
    return False

def looks_like_a_flag(token: Token) -> bool:
    allowed_prefix_types = [TokenType.RAW_STRING, TokenType.RAW_NUM]
    if token.type == TokenType.FORCED_PREFIX:
        return True
    if token.type in allowed_prefix_types and token.text.startswith('-'):
        return True
    return False

flag_conditions = [
    boolparam_then_gxparam,
    flag_then_flag,
    flag_then_null,
]

def is_flag(ctoken: Token, ntoken: Token) -> bool:
    for condition in flag_conditions:
        if condition(ctoken, ntoken):
            return True
    return False


# OPTION STUFF 


def kvlinker(ctoken: Token, ntoken: Token) -> bool:
    if ntoken.type == TokenType.KV_LINKER:
        return True 
    return False

def compound_option(ctoken: Token, ntoken: Token) -> bool:
    if looks_like_a_flag(ctoken):
        if has_compound_structure(ctoken) and not is_positional(ntoken):
            return True
    return False

def has_compound_structure(token: Token) -> bool:
    compound_opts = scanners.get_compound_opt(token.text)
    if compound_opts:
        match = compound_opts[0]
        value = match.group(2)
        if int(value) > 3:
            return True
    return False

def prefix_then_value(ctoken: Token, ntoken: Token) -> bool:
    if not is_flag(ctoken, ntoken):
        if looks_like_a_flag(ctoken) and is_positional(ntoken):
            return True
    return False

option_conditions = [
    kvlinker,
    compound_option,
    prefix_then_value
]

def is_option(ctoken: Token, ntoken: Token) -> bool:
    """
    happens 2nd after 'is_flag()'
    already know that its not a flag, so if the current token
    looks like a flag/option, it has to be an option. 
    """
    for condition in option_conditions:
        if condition(ctoken, ntoken):
            return True
    return False


# POSITIONAL STUFF

def is_positional(token: Token) -> bool:
    if not looks_like_a_flag(token):
        if token.type not in NON_VALUE_TOKENTYPES:
            return True
    return False

def cast_opt_to_flag(option: Option) -> Flag:
    return Flag(
        prefix=option.prefix,
        gxparam=option.gxparam,
        presence_array=option.presence_array
    )
