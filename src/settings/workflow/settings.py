


workflow_path: str 
dev_test_cmdstrs: bool
dev_partial_eval: bool


def set_workflow(value: str) -> None:
    global workflow_path
    workflow_path = value

def set_dev_test_cmdstrs(value: bool) -> None:
    global dev_test_cmdstrs
    dev_test_cmdstrs = value

def set_dev_partial_eval(value: bool) -> None:
    global dev_partial_eval
    dev_partial_eval = value

