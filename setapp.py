#!/usr/bin/env python
import sys
import os
import os.path
import argparse
import yaml

SETAPP_CONFIG_FILE = '/home/al/apps/setapp/new_setapp_inputs.yaml'
OS_alias = { '3.13.0-37-generic' : 'Ubuntu_16.04' }

def die(msg):                                               # {{{
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(msg)
    print("died")
    sys.exit(1)
# }}}
def parse_args():                                           # {{{
    parser = argparse.ArgumentParser(description=
    """Add, modify, show, remove environment variables,
    aliases, and shell functions associated with applications.
    """)

    parser.add_argument('application', metavar='APP', type=str, nargs='?',
        help='Application to configure.')

    parser.add_argument('--by-cat', metavar='CAT',
        dest='apps_by_cat', action='store', type=str, default=None,
        help='List applications grouped by category.')

    parser.add_argument('-d', '--debug', dest='debug',
        action='store_true', default=False,
        help='Print some internal variables.')

    parser.add_argument('--dump-env', dest='dump_env',
        action='store_true', default=False,
        help='Print a sorted list of environment variables with separate '
             'with colon separated values on separate lines.')

    parser.add_argument('-e', '--explain', metavar='APP',
        dest='explain', action='store', type=str, default=None,
        help='Print changes that would be made to the environment '
             'when adding or removing the given application.')

    parser.add_argument('-i', '--infile', dest='infile',
        action='store', type=str, default=None,
        help='Read application definitions from the given file '
             'instead of searching paths.')

    parser.add_argument('-r', '--remove', metavar='APP',
        dest='remove', action='store', type=str, default=None,
        help='Remove entries for the given application from '
             'the environment.  A value of "all" removes every '
             'configured application.  See also --explain.')

    parser.add_argument('-s', '--shell', dest='shell', action='store',
        choices=['bash', 'csh'], type=str, default='bash',
        help='Write changes for the given shell.  Use "bash" for '
             'sh/ksh/bash/zsh and "csh" for csh/tcsh [default "bash"].')

    parser.add_argument('--show', dest='show', metavar='APP',
        action='store', type=str, default=None,
        help='Show information about the given application.  "all" '
             'prints information about every application.')

    parser.add_argument('--show-bin', dest='show_bin', metavar='APP',
        action='store', type=str, default=None,
        help='Show executables provided by the given application.')

    parser.add_argument('--show-man', dest='show_man', metavar='APP',
        action='store', type=str, default=None,
        help='Show man page entries provided by the given application.')

    parser.add_argument('--validate', dest='validate', metavar='FILE',
        action='store', type=str, default=None,
                        help='Validate the correctness of the YAML '
                        'data in the given file then exit.')

    parser.add_argument('-v', '--verbose', dest='verbose',
        action='count', default=0,
        help='Verbose mode (may be specified '
             'multiple times for more output).')

#   # an integer
#   parser.add_argument('--num-cases', dest='n_cases',
#                       action='store', type=int, default=10,
#                       help='Number of data lines to create '
#                       '[10].')

    if len(sys.argv) == 1:
        # No arguments; echo the help information and exit.
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # quick exit options
    if args.dump_env:
        dump_env()
        sys.exit(0)

    return args
# }}}
def dump_env():                                             # {{{
    for var in sorted(os.environ):
        if ':' in os.environ[var]:
            print(f'{var}')
            for i,item in enumerate(os.environ[var].split(':')):
                print(f'  {i+1:3d}.  {item}')
        else:
            print(f'{var:30s} {os.environ[var]}')
# }}}
def load_app_file(File, verbose=0):                         # {{{
    global OS_alias
    y_data = None
    try:
        with open(File) as fh:
            y_data = yaml.safe_load(fh)
    except FileNotFoundError as e:
        print(f'setapp.load_app_file({File}) {e}')
    except yaml.scanner.ScannerError as e:
        print(f'setapp.load_app_file({File}) {e}')

    if verbose:
        print(f'loaded {File}')
    # validate the entries
    is_bad = False
    if 'OS_aliases' in y_data:
        OS_alias = {**OS_alias, **y_data['OS_aliases']} # dict merge
        del y_data['OS_aliases']

    recognized_k2_keys = {'env', 'alias_sh', 'alias_csh', 'function_def',
                          'doc', 'from'}

    for app in y_data:
        app_data = y_data[app]
        for required_k1 in ['name', 'default', 'ver']:
            if required_k1 not in app_data:
                print(f'key "{required_k1}" missing for {app}')
                is_bad = True
                continue
            if not isinstance(app_data['ver'], dict):
                print(f'key "ver" for {app} must define a dictionary')
                is_bad = True
                continue
            for version in app_data['ver']:
                if not isinstance(app_data['ver'][version], dict):
                    print(f'{app}/ver/{version} must define a dictionary')
                    is_bad = True
                    continue
                for OS in app_data['ver'][version]:
                    if OS not in OS_alias.values():
                        print(f'{app}/ver/{version} : OS "{OS}" is not defined '
                              f'in the OS_aliases map')
                        is_bad = True
                        continue
                    if not isinstance(app_data['ver'][version][OS], dict):
                        print(f'{app}/ver/{version}/{OS} must define a dictionary')
                        is_bad = True
                        continue
                    for k in app_data['ver'][version][OS]:
                        if k not in recognized_k2_keys:
                            print(f'{app}/ver/{version}/{OS} : unrecognized key "{k}"')
                            print(f'Allowed are :{recognized_k2_keys}')
                            is_bad = True
                    for k in ['env', 'alias_sh', 'alias_csh', 'function_def']:
                        entry = app_data['ver'][version][OS]
                        if k not in entry: continue
                        if not isinstance(entry[k], list):
                            print(f'{app}/ver/{version}/{OS}/{k} must define a list')
                            is_bad = True
                        for name_val in entry[k]:
                            if len(name_val) != 1 or \
                               not isinstance(name_val, dict):
                                print(f'{app}/ver/{version}/{OS}/{k} all entries '
                                      f'must be key : value pairs, failed with')
                                print(name_val)
                                is_bad = True
                    app_data['ver'][version][OS]['from'] = File
    if is_bad:
        print(f'setapp.load_app_file({File}) failure')
        sys.exit(1)

    return y_data
# }}}
def load_app_data(verbose=0):                               # {{{
    app_data = load_app_file(SETAPP_CONFIG_FILE, verbose=verbose)
    # look for optional files
    if 'HOME' in os.environ:
        user_yaml = f"{os.environ['HOME']}/.config/setapp/inputs.yaml"
        if os.path.exists(user_yaml):
            user_data = load_app_file(user_yaml, verbose=verbose)
        app_data = {**app_data, **user_data}
    return app_data
# }}}
def print_app(data, app,                                    # {{{
              verbose=0):

    def print_one(app):
        if app in data:
            print(f'{app:14s} ', end='')
            if 'name' in data[app]:
                print(f"{data[app]['name']:14s} ", end='')
            print()
        for ver in data[app]['ver']:
            s = '*' if ver == data[app]['default'] else ' '
            print(f'  {s}  {ver} : ', end='')
            if not verbose:
                print(', '.join(data[app]['ver'][ver].keys()))
            else:
                print()
                for OS in data[app]['ver'][ver]:
                    print(f"{' ' * 7}{OS} ({data[app]['ver'][ver][OS]['from']})")
                    for var in data[app]['ver'][ver][OS]['env']:
                        # eg var = { 'PATH+' : '/usr/local/matlab/2020b/bin' }
                        name = list(var)[0]
                        value = var[name]
                        print(f'{" " * 9}{name} {value}')

    if app == 'all':
        for A in sorted(data):
            print_one(A)
    else:
        print_one(app)
# }}}
def main():                                                 # {{{
    args = parse_args()
    app_data = load_app_data(verbose=args.verbose)
    if args.show:
        print_app(app_data, args.show, verbose=args.verbose)
        sys.exit(0)
# }}}
if __name__ == "__main__": main()
