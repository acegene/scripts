def progressbar(it, prefix='', size=60, file=sys.stderr):
    #### https://stackoverflow.com/questions/3160699/python-progress-bar
    count = len(it)
    def show(j):
        x = int(size*j/count)
        file.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), j, count))
        file.flush()
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i+1)
    file.write("\n")
    file.flush()

def safe_execute(default, exception, func, *args):
    try:
        return function(*args)
    except exception:
        return default

def except_if_not(exception:Exception, expression:bool, string_if_except:str=None) -> None:
    """Throw exception if expression is False"""
    if not expression:
        if string_if_except != None:
            print(string_if_except)
        raise exception