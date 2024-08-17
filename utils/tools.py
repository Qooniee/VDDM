from time import perf_counter
def wait_process(wait_sec):
    until = perf_counter() + wait_sec
    while perf_counter() < until:
        pass
    return
