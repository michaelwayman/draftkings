"""
Data structure helper methods.
"""


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]


def guard(fn, ex):
    try:
        return fn()
    except ex:
        return None
