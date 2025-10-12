import json

def pretty_print_json(data):
    """
    Takes a JSON string or Python dict/list and prints it in a pretty format.
    """
    # If it's a string, parse it into a Python object
    if not isinstance(data, object):
        data = json.loads(data)

    # Pretty print with indentation
    print(json.dumps(data, indent=4, sort_keys=True, default=str))
