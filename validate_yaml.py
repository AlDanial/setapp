#!/usr/bin/env python3
import sys
import yaml
import pprint

F = 'Setapp_inputs.yaml'
pp = pprint.PrettyPrinter(indent=2)

try:
    D = yaml.safe_load(open(F))
except yaml.constructor.ConstructorError as e:
    print(f'Load error: {e}')
    sys.exit(1)
except yaml.parser.ParserError as e:
    print(f'Parse error: {e}')
    sys.exit(1)

pp.pprint(D)
print('Format OK')
