#!/usr/bin/env python
import sys
import os
import pathlib
import argparse
def parse_args(desc):                                       # {{{

    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-v','--version',
        dest='version', action='store_true', default=False,
        help='Print version information.')

    if len(sys.argv) == 1:
        # No arguments; echo the help information and exit.
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    return args
# }}}
def missing_env_vars(vars):                                 # {{{
    for v in vars:
        if v not in os.environ:
            return v
    return None
# }}}
def missing_exe(exes):                                      # {{{
    """
    Search $PATH for the given application.
    """
    if 'PATH' not in os.environ:
        return "PATH not set"
    files = []
    for D in os.environ['PATH'].split(':'):
        P = pathlib.Path(D)
        if not P.is_dir():
            continue
        for F in P.iterdir():
            if not F.is_file():
                continue
            files.append(F.name)

    files   = set(files)
    exe_set = set(exes)
    if not exe_set.issubset(files):
        return list(exe_set - files)
    else:
        return None
# }}}
