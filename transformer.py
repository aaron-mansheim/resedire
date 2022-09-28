#!python
# A study. Process a self-describing JSON file.
# Aaron Mansheim <aaron@mansheim.com>
# 2022-09-27

import datetime
import json
import re
import sys

DEBUG = False

DEMO_JSON_FILENAME='JSON file'

DEMO_JSON=(''
'{"number_1":{"N":"1.50"},"string_1":{"S":"784498 "},'
'"string_2":{"S":"2014-07-16T20:55:46Z"},'
'"map_1":{"M":{"bool_1":{"BOOL":"truthy"},"null_1":{"NULL ":"true"},'
'"list_1":{"L":[{"S":""},{"N":"011"},{"N":"5215s"},{"BOOL":"f"},{"NULL":"0"}]}}},'
'"list_2":{"L":"noop"},"list_3":{"L":["noop"]},"":{"S":"noop"}}')

def as_invalid(debug_string):
    return debug_string if DEBUG else ''

def as_bool(data):
    if not isinstance(data, str):
        return as_invalid(f"bool: no way, {type(data)}.")
    data = data.strip()
    if data in ("1", "t", "T", "TRUE", "true", "True"):
        return True
    if data in ("0", "f", "F", "FALSE", "false", "False"):
        return False
    return as_invalid(f"bool: no, {data}.")

def as_null(data):
    data = as_bool(data)
    if data is True:
        return None
    return as_invalid(f"null: no, {data}.")

def as_number(data):
    """
    Accept strings of JSON number literals, with any number of zeros prepended.
    """
    if not isinstance(data, str):
        return as_invalid(f"number: no way, {type(data)}.")
    data = data.strip()
    data = data.lstrip('0')
    result = re.fullmatch("-?(\\d|[1-9]\\d+)(\\.\\d+)?([Ee][+-]?\\d+)?", data)
    if result:
        if result.group(2):
            return float(data)
        return int(data)
    return as_invalid("number: no, {data}.")

def as_string(data):
    if not isinstance(data, str):
        return as_invalid(f"string: no way, {type(data)}.")
    data = data.strip()
    if data and data[-1].lower() == 'z':
        data = data[0:-1] + '+00:00'
    result = re.match(r'^\d{4}-\d{2}-\d{2}[tT]\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2})$', data)
    if result:
        return int(datetime.datetime.fromisoformat(data).timestamp())
    return data

def as_scalar(data):
    if not isinstance(data, dict):
        return as_invalid(f"scalar: no way, {type(data)}.")
    for key, value in data.items():
        key = key.strip()
        if key == "S":
            return as_string(value)
        if key == "N":
            return as_number(value)
        if key == "BOOL":
            return as_bool(value)
        return as_invalid(f"scalar: nope, {key}.")

def as_value(data):
    if not isinstance(data, dict):
        return as_invalid(f"value: no way, {type(data)}.")
    for key, value in data.items():
        key = key.strip()
        return (as_null(value) if key == "NULL" else
                as_list(value) if key == "L" else
                as_map(value) if key == "M" else
                as_scalar(data))

def as_list(data):
    if not isinstance(data, list):
        return as_invalid(f"list: no way, {type(data)}.")
    result = []
    for value in data:
        result += [as_scalar(value)]
    result = [value for value in result if value != ""]
    return result

def as_map(data):
    if not isinstance(data, dict):
        return as_invalid(f"map: no way, {type(data)}.")
    result = {}
    for key, value in data.items():
        key = key.strip()
        if key == '':
            continue
        value = as_value(value)
        if value not in ('', {}, []):
            result[key] = value
    rebuild = {}
    for key in sorted(result):
        rebuild[key] = result[key]
    return rebuild

def transforms(data):
    return json.dumps([as_map(data)], indent=2)

def transform(filename):
    with open(filename, encoding='utf8') as jsonfile:
        data = json.load(jsonfile)
    return transforms(data)

def tool():
    if len(sys.argv) < 2:
        print('Input filename is a required command-line argument.', file=sys.stderr)
        sys.exit(1)
    print(transform(sys.argv[1]))

def demo_json():
    data = json.loads(DEMO_JSON)
    indented = json.dumps(data, indent=2)
    return indented

def transform_demo_json():
    retry_delay = 1
    while retry_delay < 30:
        try:
            return transform(DEMO_JSON_FILENAME)
        except FileNotFoundError:
            print(f'File {DEMO_JSON_FILENAME}: Not found.', file=sys.stderr)
            print(f'\tWill write the file, wait {retry_delay}s, and retry.', file=sys.stderr)
            data = demo_json()
            with open(DEMO_JSON_FILENAME, 'w', encoding='utf8') as jsonfile:
                print(data, file=jsonfile)
            retry_delay *= 2
    print('Too many attempts to read the file.', file=sys.stderr)
    print('\tWill transform demo JSON from memory.', file=sys.stderr)
    return transforms(demo_json())

def demo():
    print(transform_demo_json())

if __name__ == '__main__':
    # tool()
    demo()
