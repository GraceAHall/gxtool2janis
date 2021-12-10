


from collections import Counter
from typing import Union

from classes.templating.MockClasses import MockApp, ComputeEnvironment
from galaxy.tools import Tool as GalaxyTool
from galaxy.tools.evaluation import ToolEvaluator
from galaxy.model import (
    Job,
    Dataset,
    HistoryDatasetAssociation,
    JobToInputDatasetAssociation,
    JobToOutputDatasetAssociation,
)

## galaxy engine - tool evaluation 

def generate_dataset(app: MockApp, varname: str, iotype: str) -> Union[JobToInputDatasetAssociation, JobToOutputDatasetAssociation]:
    """
    creates a dataset association. 
    this process creates a dataset and updates the sql database model.
    """
    i = app.dataset_counter
    path = varname
    varrep = '__gxvar_' + varname
    app.dataset_counter += 1

    if iotype == 'input':
        return JobToInputDatasetAssociation(name=varname, dataset=generate_hda(app, i, path, varrep))
    elif iotype == 'output':
        return JobToOutputDatasetAssociation(name=varname, dataset=generate_hda(app, i, path, varrep))


def generate_hda(app: MockApp, id: int, name: str, path: str) -> HistoryDatasetAssociation:
    hda = HistoryDatasetAssociation(name=name, metadata=dict())
    hda.dataset = Dataset(id=id, external_filename=path)
    hda.dataset.metadata = dict()
    hda.children = []
    app.model.context.add(hda)
    app.model.context.flush()
    return hda


def setup_evaluator(app: MockApp, gxtool: GalaxyTool, job: Job, test_directory: str) -> ToolEvaluator:
    evaluator = ToolEvaluator(app, gxtool, job, test_directory)
    kwds = {}
    kwds["working_directory"] = test_directory
    kwds["new_file_path"] = app.config.new_file_path
    evaluator.set_compute_environment(ComputeEnvironment(**kwds))
    return evaluator



# ---- consolidating types ---- #

# TODO write tests for all these
type_consolidator = {
    'fastqsanger': 'fastq',
    'fastqsanger.gz': 'fastq.gz',
    'tabular': 'tsv',
}

def consolidate_types(types: str) -> str:
    # standardises types. ie fastq,fastqsanger -> fastq
    out_types: set[str] = set()

    type_list = types.split(',')
    for old_type in type_list:
        old_type = old_type.replace('\n', '').strip(' ')
        try:
            new_type = type_consolidator[old_type]
            out_types.add(new_type)
        except KeyError:
            out_types.add(old_type)
    
    out_types = list(out_types)
    out_types.sort(key=lambda x: len(x))
    return ','.join(out_types)


# ---- list operations ---- #

def get_common_extension(the_list: list[str]) -> str: 
    """
    identifies whether a list of items has a common extension. 
    all items must share the same extension. 
    will return the extension if true, else will return ""
    """
    
    try:
        ext_list = [item.rsplit('.', 1)[1] for item in the_list]
    except IndexError:
        return ''  # at least one item has no extension

    ext_counter = Counter(ext_list)
        
    if len(ext_counter) == 1:  
        ext, count = ext_counter.popitem() 
        if count == len(the_list):  # does every item have the extension?
            return ext 

    return ""


def is_string_list(the_list: list[str]) -> bool:
    """
    string list is list of values which do not look like prefixes ('-' at start)
    TODO awful. refactor.
    """
    for item in the_list:
        val = item['value']
        if val == '' or val[0] == '-':
            return False
    if len(the_list) == 2:
        if the_list[0]['value'] in ['true', 'false'] and the_list[1]['value'] in ['true', 'false']:
            return False
    return True


def is_flag_list(options: list[str]) -> bool:
    outcome = True

    # check all the options start with '-'
    for opt in options:
        if not opt['value'].startswith('-'):
            outcome = False
            break

    # ensure its just not because negative numbers
    try: 
        [float(opt['value']) for opt in options] 
        outcome = False  # if reaches this point, all opts are float castable
    except ValueError:
        pass

    return outcome


def cast_list(the_list: list[str]) -> str:
    """
    identifies whether all list items can be cast to a common datatype.
    currently just float and int
    """
    castable_types = []

    if can_cast_to_float(the_list):
        castable_types.append('Float')
    elif can_cast_to_int(the_list):
        castable_types.append('Integer')

    if 'Float' in castable_types:
        if 'Integer' in castable_types:
            return 'Integer'
        else:
            return 'Float'

    return ''


# write test
def can_cast_to_float(the_list: list[str]) -> bool:
    # each item is empty
    if all([elem == '' for elem in the_list]):
        return False

    # check if any can't be cast to float    
    for item in the_list:
        try:
            float(item)
        except ValueError:
            return False
    return True 


def can_cast_to_int(the_list: list[str]) -> bool:
    # empty list
    if len(the_list) == 0:
        return False

    for item in the_list:
        # empty string
        if len(item) > 0:
            if item[0] in ('-', '+'):
                item = item[1:]

        if not item.isdigit():
            return False

    return True 








