import os
import tempfile

def is_filesystem_case_sensitive(dir_:str='.') -> bool:
    """Check whether <dir_> is part of a case sensitive filesystem

    Requires write access to <dir_>

    https://stackoverflow.com/a/36580834/10630957

    Imports:
        os
        tempfile

    Args:
        dir_ (str): directory that is being tested for case sensitivity

    Returns:
        bool: True if filesystem for <dir_> is case sensitive
    """

    try:
        return is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_]
    except AttributeError:
        setattr(is_filesystem_case_sensitive, 'case_sensitive_dir_dict', {})
    finally:
        with tempfile.NamedTemporaryFile(prefix='TmP', dir=dir_) as tmp_file:
            is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_] = not os.path.exists(tmp_file.name.lower())
            return is_filesystem_case_sensitive.case_sensitive_dir_dict[dir_]
