#!/usr/bin/env python
import sys
import os
import os.path
import argparse
import yaml
import pathlib

from rich import print
import pprint ; pp = pprint.PrettyPrinter(indent=2)

SETAPP_CONFIG_FILE = '/home/al/apps/setapp/new_setapp_inputs.yaml'
OS_alias = { '3.13.0-37-generic' : 'Ubuntu_16.04' } # updated in load_app_file()
This_OS  = None

def die(msg):                                               # {{{
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(msg)
    print("died")
    sys.exit(1)
# }}}
def parse_args():                                           # {{{
    global This_OS

    parser = argparse.ArgumentParser(description=
    """Add, modify, show, remove environment variables,
    aliases, and shell functions associated with applications.
    """)

    parser.add_argument('applications', metavar='APP', type=str, nargs='*',
        help='Application to configure.')

    parser.add_argument('--by-cat', metavar='CAT',
        dest='apps_by_cat', action='store', type=str, default=None,
        help='List applications grouped by category. [NOT IMPLEMENTED]')

    parser.add_argument('-d', '--debug', dest='debug',
        action='store_true', default=False,
        help='Print some internal variables.')

    parser.add_argument('--dump-env', dest='dump_env',
        action='store_true', default=False,
        help='Print a sorted list of environment variables with separate '
             'with colon separated values on separate lines.')

    parser.add_argument('-g', '--getapp', dest='getapp',
        action='store_true', default=False,
        help='Print currently configured applications.')

    parser.add_argument('-e', '--explain', metavar='APP',
        dest='explain', action='store', type=str, default=None,
        help='Print changes that would be made to the environment '
             'when adding or removing the given application.')

    parser.add_argument('-i', '--infile', dest='infile',
        action='store', type=str, default=None,
        help='Read application definitions from the given file '
             'instead of searching paths.')

    parser.add_argument('-r', '--remove',
        dest='remove', action='store_true', default=None,
        help='Remove entries for the given application from '
             'the environment.  Version specifiers are ignored. '
             'A value of "all" removes every '
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
        help='Show executables provided by the given application. [NOT IMPLEMENTED]')

    parser.add_argument('--show-man', dest='show_man', metavar='APP',
        action='store', type=str, default=None,
        help='Show man page entries provided by the given application. [NOT IMPLEMENTED]')

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

    app_data = load_app_data(verbose=args.verbose)

    release = os.uname().release
    if release not in OS_alias:
        print(f'This OS, uname -r = {release}, is unrecognized')
        sys.exit(0)
    This_OS = OS_alias[release]

    # quick exit options
    if args.dump_env:
        dump_env()
        sys.exit(0)

    return args, app_data
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
def env_var_action(varname):                                # {{{
    """
    varname is an environment variable name with two optional
    modifiers, "!" and "+", and so takes one of three forms:
        "XX"    ->  verb = 'append to'
        "XX!"   ->  verb = 'overwrite'
        "XX+"   ->  verb = 'prefix'
    Returns the verb, varname without "!" or "+", and
    a following string used for printing an explanation.
    """
    if   varname.endswith('!'):
        clean = varname[:-1]
        return "overwrite", clean, "with"
    elif varname.endswith('+'):
        clean = varname[:-1]
        return "prefix", clean, "with"
    else:
        return "append to", varname, ":"
# }}}
def app_exists(data, app_ver):                              # {{{
    """
    app_ver -> "matlab", or "matlab/2022a"
    Return an error string if the requested app/version
    isn't defined.  Ignore leading '+' if it exists.
    """
    err = ""

    if app_ver.startswith('+'):
        app_ver = app_ver[1:]

    if '/' in app_ver:
        app, ver = app_ver.split('/')
    else:
        app, ver = app_ver, data[app_ver]['default']

    if  app not in data:
        err = f'{app} is not defined'
    elif ver not in data[app]['ver']:
        err = f'{app}/{ver} is not defined'
    elif This_OS not in data[app]['ver'][ver]:
        err = f'{app}/{ver} is not available for {This_OS}'

    return app, ver, err
# }}}
def explain(data, app_ver,                                  # {{{
            verbose=0):
    """
    app_ver -> "matlab", or "matlab/2022a"
    """

    app, ver, err = app_exists(data, app_ver)
    if err:
        print(err)
        return
    print(f'{app}/{ver}')
    entry = data[app]['ver'][ver][This_OS]
    print(f"  defined in {entry['from']}")
    for var_setting in entry['env']:  # list of dicts
        for var in var_setting:
            verb, clean_var, preposition = env_var_action(var)
            print(f"  -> {verb} {clean_var} {preposition} {var_setting[var]}")

# }}}
def add_app(data, app_ver_list, Old_Env,                    # {{{
            verbose=0):
    """
    app_ver is a list of application names with an optional version
    number:  "matlab" or "matlab/2022a"

    Return an updated Env dictionary of lists that contain
    the environment delta needed to include app_ver.
    """

    New_Env = { 'SETAPP_TOOLS' : [] }
    have_it = {}
    action = {
        'append to' : [],
        'prefix'    : [],
        'overwrite' : [],
    }

    for app_ver in app_ver_list:
        if app_ver.startswith('+'):
            front = True
        else:
            front = False

        app, ver, err = app_exists(data, app_ver)
        clean_app_ver = f'{app}/{ver}'
        if err:
            print(err)
            return

        if clean_app_ver in have_it:
            continue

        entry = data[app]['ver'][ver][This_OS]
        for var_setting in entry['env']:  # list of dicts
            for var in var_setting:
                value = var_setting[var]
                verb, clean_var, _ = env_var_action(var)
                if verb == 'append to' and front:
                    verb = 'prefix'
                action[verb].append( (clean_var, value)  )
                if clean_var in Old_Env:
                    New_Env[clean_var] = [ f'${{{clean_var}}}' ]
                else:
                    New_Env[clean_var] = []

        # add this app/ver to the registry variable
        New_Env['SETAPP_TOOLS'].append( clean_app_ver )
        have_it[clean_app_ver] = True

        assignments = []
        for env_var, value in action['append to']:
            New_Env[env_var].append(value)
        for env_var, value in action['prefix']:
            New_Env[env_var].insert(0, value)
        for env_var, value in action['overwrite']:
            New_Env[env_var] = [ value ]

    return New_Env
# }}}
def print_joined_values(color, separator, values,           # {{{
                        color_set):
    sep = separator
    for value in values:
        if value in color_set:
            print(f"{sep}[{color}]{value}", end="")
        else:
            print(f"{sep}{value}", end="")
        sep = ":"
    print()
# }}}
def rm_app( data, app_ver_list, Old_Env,                    # {{{
            verbose=0):
    """
    Modify Old_Env by removing the applications in app_ver_list.
    Retain any environment variables needed by other applications
    in case there are overlaps.
    Return dict of affected env variables.
    """

    if 'SETAPP_TOOLS' not in Old_Env:
        print("no applications definied, nothing removed")
        return

    tools_to_rm = []
    for app_ver in app_ver_list:
        if app_ver == 'all':
            tools_to_rm = ['all']
            break
        app, ver, err = app_exists(data, app_ver)
        if err:
            print(err)
            continue
        tools_to_rm.append(app)
    rm_app_set = set(tools_to_rm)

    # make a set from basenames of existing apps
    configured_apps = {}  # configured_apps['matlab'] = '2022a'
    for app_ver in Old_Env['SETAPP_TOOLS'][0].split(':'):
        app, ver, err = app_exists(data, app_ver)
        if err:
            print(err)
            continue
        configured_apps[app] = ver
    existing_set = set(configured_apps.keys())
    if 'all' in rm_app_set:
        rm_app_set  = existing_set
    else:
        rm_app_set &= existing_set # intersection

    tools_to_keep = existing_set - rm_app_set

    # preserve environment variable settings needed by retained tools
    keep_vars = {} # keep_vars['PATH'] = [list of directories]
    for app in tools_to_keep:
        ver = configured_apps[app]
        for entry in data[app]['ver'][ver][This_OS]['env']:
            # entry: eg { 'PATH!' : '/usr/local/bin' }
            for envname in entry:
                k = envname
                if k.endswith('!') or k.endswith('+'):
                    k = k[:-1]
                if k in keep_vars:
                    keep_vars[k].append( entry[envname] )
                else:
                    keep_vars[k] =     [ entry[envname] ]

#   print('rm_app_set   =', rm_app_set  )
#   print('tools_to_keep=', tools_to_keep)
#   print('keep_vars    =', keep_vars    )

    delete_from = {} # delete_from['PATH'] = [list of directories]
    for app in rm_app_set:
        ver = configured_apps[app]
        for entry in data[app]['ver'][ver][This_OS]['env']:
            for envname in entry:
                k = envname
                if k.endswith('!') or k.endswith('+'):
                    k = k[:-1]
#               print('entry=', entry)
#               print(f'cleaning up {k}')
                values_to_keep = set()
                if k not in keep_vars:
                    if k not in Old_Env:
                        continue
                else:
                    values_to_keep = set(keep_vars[k])
                for value in Old_Env[k]:
#                   print(f'examining {value}')
                    if (entry[envname] == value) and \
                       (value not in values_to_keep):
                        if verbose:
                            print(f'DELETING {value} from {k}')
                        if k in delete_from:
                            delete_from[k].append(value)
                        else:
                            delete_from[k] =    [ value ]

    New_Env = {}
    Unset   = {}
    for k in delete_from:
        delete_from[k] = set( delete_from[k] )
        for value in Old_Env[k]:
            if value in delete_from[k]:
                continue
            if k in New_Env:
                New_Env[k].append(value)
            else:
                New_Env[k] =    [ value ]
        print(f"Before {k}=", end="")
        print_joined_values("red", ":", Old_Env[k], delete_from[k])
        if k in New_Env:
            print(f"After  {k}={':'.join(New_Env[k])}\n")
        else:
            New_Env[k] = [ ]
            print(f"After  {k}=null\n")

#   pp.pprint(New_Env)
    return New_Env
# }}}
def clean_env_var(value):                                   # {{{
    """
    Cleans up PATH-like environment variable by removing
    duplicate entries, consecutive colons, leading and
    trailing colons.
    """
    seen_it = {}
    unique = []
    for entry in value.split(':'):
        if not entry or entry in seen_it:
            continue
        seen_it[entry] = True
        unique.append(entry)

    return unique
# }}}
def getapp(data):                                           # {{{
    if 'SETAPP_TOOLS' not in os.environ:
        print('no tools configured')
        return
    for app_ver in os.environ['SETAPP_TOOLS'].split(':'):
        app, ver, err = app_exists(data, app_ver)
        if err:
            print(f'unrecognized tool "{app_ver}", {err}')
            continue
        print(f"{app:16s} {ver:14s} {data[app]['name']}")
# }}}
def get_current_env():                                      # {{{
    Env = {}
    for var in os.environ:
        value = os.environ[var]
        if var.endswith('PATH') or 'LICENSE_FILE' in var:
            Env[var] = clean_env_var(value)
        else:
            Env[var] = [ value ]

    return Env
# }}}
def write_dotfile(Env, shell):                              # {{{
    if not Env:
        print('null environment change, nothing written')
        return
    lines = []
    for var in Env:
        lines.append('export %s="%s"' % (var, ':'.join(Env[var])))
    P = pathlib.Path('/home/al/.my_env')
    P.write_text('\n'.join(lines) + '\n')
# }}}
def main():                                                 # {{{
    args, app_data = parse_args()
    if args.show:
        print_app(app_data, args.show, verbose=args.verbose)
    elif args.getapp:
        getapp(app_data)
    elif args.remove:
        Old_Env = get_current_env()
        rm_app(app_data, args.applications, Old_Env,
               verbose=args.verbose)
    elif args.explain:
        explain(app_data, args.explain)
    elif args.shell and args.applications:
        Old_Env = get_current_env()
#       pp.pprint(Old_Env)
        rm_app(app_data, args.applications, Old_Env,
               verbose=args.verbose)
        delta_Env = add_app(app_data, args.applications, Old_Env,
                            verbose=args.verbose)
        pp.pprint(delta_Env)
        write_dotfile(delta_Env, args.shell)

# }}}
if __name__ == "__main__": main()
