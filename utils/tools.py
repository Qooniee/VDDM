from time import perf_counter
def wait_process(wait_sec):
    """
    Pauses the execution of the program for the specified number of seconds.

    This function uses a busy-wait loop to delay execution, effectively blocking 
    the program for the duration of the specified wait time.

    Args:
        wait_sec (float): The amount of time, in seconds, to wait before continuing.
    """
    until = perf_counter() + wait_sec
    while perf_counter() < until:
        pass
    return