import re
from uuid import UUID
import json
import logging


def to_snake_case(string):
    """
    Convert a string from camelCase or PascalCase to snake_case.

    This function takes a string in camelCase or PascalCase format and converts it to snake_case.
    It handles the following cases:
    - camelCase -> camel_case
    - PascalCase -> pascal_case
    - ABC -> abc (consecutive uppercase letters are treated as one word)
    - alreadySnakeCase -> already_snake_case
    - ThisIsATest -> this_is_a_test

    Args:
        string (str): The input string to convert.

    Returns:
        str: The input string converted to snake_case.

    Example:
        >>> to_snake_case('camelCase')
        'camel_case'
        >>> to_snake_case('PascalCase')
        'pascal_case'
        >>> to_snake_case('ABC')
        'abc'
        >>> to_snake_case('XMLHttpRequest')
        'xml_http_request'
        >>> to_snake_case('ThisIsATest')
        'this_is_a_test'
    """
    if not string:
        return string

    result = [string[0].lower()]

    # Look at triplets: previous, current, and next character
    for i in range(1, len(string)):
        curr = string[i]
        prev = string[i - 1]
        next_char = string[i + 1] if i < len(string) - 1 else None

        # Add underscore if:
        # 1. Current char is uppercase and previous char is lowercase
        # 2. Current char is uppercase and next char is lowercase (for cases like 'ThisIsATest')
        # 3. Previous char is not underscore and not uppercase
        if curr.isupper() and (
            (prev.isalnum() and not prev.isupper())
            or (next_char and next_char.islower())
        ):
            if result[-1] != '_':
                result.append('_')

        result.append(curr.lower())

    return ''.join(result)


def convert_dict_keys_to_snake_case(data):
    """
    Recursively converts all dictionary keys to snake_case.

    This function takes a dictionary and converts all of its keys to snake_case format.
    If the value of a key is also a dictionary, it recursively applies the same conversion.
    For non-dictionary values, it returns them unchanged.

    Args:
        data (dict): The input dictionary to convert.

    Returns:
        dict: A new dictionary with all keys converted to snake_case.
              If the input is not a dictionary, it returns the input unchanged.

    Example:
        >>> convert_dict_keys_to_snake_case({'firstName': 'John', 'lastName': 'Doe'})
        {'first_name': 'John', 'last_name': 'Doe'}
    """
    if not isinstance(data, dict):
        return data

    return {
        to_snake_case(key): convert_dict_keys_to_snake_case(value)
        for key, value in data.items()
    }


# These are the list id uuid that are supported by the module
SUPPORTED_UUID_VERSIONS = (1, 3, 4, 5)


# TODO: check UUID version 1, 2, 4, 7. True when atleast on passes
def get_uuid_version(id: str) -> int | None:
    # 1 ... 8 | None
    for version in SUPPORTED_UUID_VERSIONS:
        try:
            uuid_obj = UUID(id, version=version)
        except ValueError:
            continue

        if str(uuid_obj) == id:
            return version

    return None


def is_valid_uuid(uuid_to_test, version: int | None = None):
    """
    Check if uuid_to_test is a valid UUID.

     Parameters
    ----------
    uuid_to_test : str
    version : {1, 3, 4, 5}

     Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

     Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """
    if not uuid_to_test:  # Handle None and empty string
        return False

    if version is None:
        return get_uuid_version(uuid_to_test) is not None

    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def safe_json_dumps(data, default=None):
    """
    Safely convert data to JSON string.

    Args:
    data: The data to convert to JSON.
    default: The default value to return if conversion fails (default is '{}').

    Returns:
    str: JSON string representation of the data, or the default value if conversion fails.
    """
    if default is None:
        default = '{}'

    output = default
    try:
        output = json.dumps(data)
    except (TypeError, ValueError, OverflowError) as e:
        logging.warning(f'Failed to serialize to JSON. Using default value.')

    return output

def safe_json_loads(data, default=None, attempt_double_decode=False):
    """
    Safely convert JSON string to Python object.

    Args:
        data: The JSON string or object to convert/validate
        default: The default value to return if conversion fails (default is None)
        attempt_double_decode: If True, attempts to decode twice in case of double-encoded JSON

    Returns:
        object: Python object representation of the JSON string, or the default value if conversion fails.
        If input is already a dict/list, returns it as is.
    """
    # If data is None, return default
    if data is None:
        return default
        
    # If data is already a dict or list, return as is
    if isinstance(data, (dict, list)):
        return data

    try:
        if not isinstance(data, str):
            return default
            
        result = json.loads(data)
        
        # Attempt second decode if the result is a string and looks like JSON
        if attempt_double_decode and isinstance(result, str):
            try:
                if result.startswith('{') or result.startswith('['):
                    second_result = json.loads(result)
                    return second_result
            except (TypeError, ValueError, json.JSONDecodeError):
                # If second decode fails, return result from first decode
                pass
                
        return result
    except (TypeError, ValueError, json.JSONDecodeError) as e:
        logging.warning(f'Failed to deserialize JSON: {str(e)}. Input was: {str(data)[:100]}')
        return default


def convert_operator(operator: str, case_insensitive: bool = True) -> str:
    """
    Convert frontend operator to SQL operator.

    Args:
        operator (str): The frontend operator to convert.
        case_insensitive (bool): Whether to use case-insensitive operators where applicable. Defaults to True.

    Returns:
        str: The corresponding SQL operator.
    """
    operator_map = {
        'contains': 'ILIKE' if case_insensitive else 'LIKE',
        'does not contain': 'NOT ILIKE' if case_insensitive else 'NOT LIKE',
        'is empty': 'IS NULL',
        'is not empty': 'IS NOT NULL',
        # TODO: figure out how to do this well with varying data types
        # '=': 'ILIKE' if case_insensitive else '=',
        '=': '=',
        # '!=': 'NOT ILIKE' if case_insensitive else '!=',
        '!=': '!=',
        '<': '<',
        '>': '>',
        '<=': '<=',
        '>=': '>=',
    }
    return operator_map.get(operator, 'ILIKE' if case_insensitive else '=')
