


import runtime.logging.logging as logging
import re
from command.text.regex.utils import find_unquoted
import command.text.regex.scanners as scanners
import command.text.simplification.utils as utils

def replace_function_calls(cmdstr: str) -> str:
    cmdlines = utils.split_lines(cmdstr)
    out: list[str] = []
    for line in cmdlines:
        matches = scanners.get_function_calls(line)
        for match in matches:
            logging.has_cheetah_function()
            old_section = match[0]
            new_section = '__FUNCTION_CALL__'
            line = line.replace(old_section, new_section)
        out.append(line)
    return utils.join_lines(out)

def replace_backticks(cmdstr: str) -> str:
    matches = scanners.get_backtick_sections(cmdstr)
    for match in matches:
        logging.has_backtick_statement()
        old_section = match[0]
        new_section = '__BACKTICK_SHELL_STATEMENT__'
        cmdstr = cmdstr.replace(old_section, new_section)
    return cmdstr

def interpret_raw(cmdstr: str) -> str:
    return cmdstr.replace('\\', '')

def flatten_multiline_strings(cmdstr: str) -> str:
    matches = scanners.get_quoted_sections(cmdstr)
    for match in matches:
        if '\n' in match[0]:
            logging.has_multiline_str()
            old_section = match[0]
            new_section = match[0].replace('\n', ' ')
            cmdstr = cmdstr.replace(old_section, new_section)
    return cmdstr

def translate_variable_markers(cmdstr: str) -> str:
    return cmdstr.replace("gxparam_", "$")

def standardise_variable_format(cmdstr: str) -> str:
    """standardises different forms of a galaxy variable ${var}, $var etc"""
    cmdlines: list[str] = utils.split_lines(cmdstr)
    outlines: list[str] = [remove_var_braces(line) for line in cmdlines]
    return utils.join_lines(outlines)

def remove_var_braces(text: str) -> str:
    """
    modifies cmd word to ensure the $var format is present, rather than ${var}
    takes a safe approach using regex and resolving all vars one by one
    """
    return text
    # if text == '':
    #     return text
    # matches = scanners.get_variables_fmt2(text)
    # if len(matches) > 0:
    #     m = matches[0]
    #     # this is cursed but trust me it removes the curly braces for the match span
    #     old_segment = text[m.start(): m.end()]
    #     new_segment = old_segment[0] + old_segment[2: -1]
    #     new_segment = new_segment.replace(' ', '')
    #     text = text.replace(old_segment, new_segment)
    #     text = remove_var_braces(text)
    # return text  

def remove_empty_quotes(cmdstr: str) -> str:
    cmdstr = cmdstr.replace('""', '')
    cmdstr = cmdstr.replace("''", '')
    return cmdstr

def simplify_sh_constructs(cmdstr: str) -> str:
    """
    this function standardises the different equivalent 
    forms of linux operations into a single common form
    """
    cmdstr = cmdstr.replace("&amp;", "&")
    cmdstr = cmdstr.replace("&lt;", "<")
    cmdstr = cmdstr.replace("&gt;", ">")
    cmdstr = cmdstr.replace("|&", "2>&1 |")
    cmdstr = cmdstr.replace("| tee", "|tee")
    cmdstr = cmdstr.replace("1>", ">")
    return cmdstr 

def simplify_galaxy_static_vars(cmdstr: str) -> str:
    """
    modifies galaxy reserved words to relevant format. only $__tool_directory__ for now. 
    There is a scanner for this, but the actual substitutions might be different. 
    """
    cmdstr = re.sub(r"\$__tool_directory__/", "", cmdstr)
    return cmdstr

def simplify_galaxy_dynamic_vars(cmdstr: str) -> str:
    """  ${GALAXY_SLOTS:-2} -> 2   etc """
    matches = scanners.get_dynamic_keywords(cmdstr)
    for match in matches:
        cmdstr = cmdstr.replace(match[0], match.group(1)) 
    return cmdstr

def remove_cheetah_comments(cmdstr: str) -> str:
    """
    removes cheetah comments from command lines
    comments can be whole line, or part way through
    """
    cmdlines: list[str] = utils.split_lines(cmdstr)
    outlines: list[str] = []

    for line in cmdlines:
        comment_start, _ = find_unquoted(line, '##')
        if comment_start != -1:
            # override line with comment removed
            line = line[:comment_start].strip()
        # make sure we didnt trim a full line comment and now its an empty string
        if line != '':
            outlines.append(line)
    return utils.join_lines(outlines)


