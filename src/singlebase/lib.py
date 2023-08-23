#-----------------------------
# -- Singlebase --
#-----------------------------

import re
import json
import uuid
import time
import arrow
import cuid2
import secrets
import hashlib
import datetime
from functools import reduce
from operator import itemgetter
from typing import Iterator, Any

# Date format
FORMAT_ISO_DATE = "YYYY-MM-DD"
FORMAT_ISO_TIME = "HH:mm:ss"
FORMAT_ISO_DATETIME = "YYYY-MM-DD HH:mm:ss"

DATES_FORMAT = {
    "ISO_DATE": FORMAT_ISO_DATE,
    "ISO_TIME": FORMAT_ISO_TIME,
    "ISO_DATETIME": FORMAT_ISO_DATETIME
}


def keyname_valid(name:str) -> bool:
    """
    Test if a key name is valid. 

    For example, it can test if a key in a dict is valid

    pattern: start with letters or underscrore. Contains alphanum + underscore + hyphen + $

    Params:
        name:str
    Returns:
        bool
    """
    if not name or not isinstance(name, str):
        return False
    pattern = re.compile(r"^[a-zA-Z\_\$][a-zA-Z0-9\_\-\$]*$")
    return bool(pattern.match(name)) 


def gen_xid() -> str:
    """
    XID - To generate a random unique ID. 
    Return CUID2. 16 chars
    """
    l = 16
    return cuid2.Cuid(length=l).generate()
    
def gen_uuid() -> str:
    """
    To be used as UUID
    Return a UUID4 key. 32 chars
    """
    return str(uuid.uuid4()).replace("-", "")


# === DATE + TIME 
def get_datetime() -> arrow.Arrow:
    """
    Generates the current UTC timestamp with Arrow date

    ISO FORMAT
    Date    2022-08-13
    Date and time in UTC : 2022-08-13T22:45:03+00:00

    Returns:
      Arrow UTC Now
    """
    return arrow.utcnow()


def get_timestamp() -> int:
    """
    Generates the current UTC timestamp with datetime
    Returns:
      int
    """
    return round(datetime.datetime.utcnow().timestamp())


# ----------------------
# json_ext

class json_ext:
    """ 
    JSON Extension class to loads and dumps json
    """

    @classmethod
    def dumps(cls, data: dict) -> str:
        """ Serialize dict to a JSON formatted """
        return json.dumps(data, default=cls._serialize)

    @classmethod
    def loads(cls, data: str) -> dict:
        """ Deserialize a JSON string to dict """
        if not data:
            return None
        if isinstance(data, list):
            return [json.loads(v) if v else None for v in data]
        return json.loads(data, object_hook=cls._deserialize)

    @classmethod
    def _serialize(cls, o):
        return cls._timestamp_to_str(o)

    @classmethod
    def _deserialize(cls, json_dict):
        for k, v in json_dict.items():
            if isinstance(v, str) and cls._timestamp_valid(v):
                json_dict[k] = arrow.get(v)
        return json_dict

    @staticmethod
    def _timestamp_valid(dt_str) -> bool:
        try:
            datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return False
        return True

    @staticmethod
    def _timestamp_to_str(dt) -> str:
        if isinstance(dt, arrow.Arrow):
            return dt.for_json()
        elif isinstance(dt, (datetime.date, datetime.datetime)):
            return dt.isoformat()
        return dt

# alias 
json_dumps = json_ext.dumps
json_loads = json_ext.loads



# === DICT extensions

def flatten_dict(_dict: dict, _str: str = '', reducer=None) -> dict:
    """
    To flatten a dict. Nested node will be separated by dot or separator
    It takes in consideration dict in list and flat them.
    Non dict stay as is

    Args:
        ddict:
        prefix:
    Returns:
        dict

    """
    sep = "."
    ret_dict = {}
    for k, v in _dict.items():
        if isinstance(v, dict):
            ret_dict.update(flatten_dict(v, _str=sep.join([_str, k]).strip(sep)))
        elif isinstance(v, list):
            _k =  ("%s.%s" % (_str, k)).strip(sep)
            ret_dict[_k] = [flatten_dict(item) if isinstance(item, dict) else item for item in v]
        else:
            ret_dict[sep.join([_str, k]).strip(sep)] = v
    return ret_dict


def unflatten_dict(flatten_dict: dict) -> dict:
    """
    To un-flatten a flatten dict

    Args:
      flatten_dict: A flatten dict
    Returns:
      an unflatten dictionnary
    """
    output = {}
    for k, v in flatten_dict.items():
        path = k.split(".")
        if isinstance(v, list):
            v = [unflatten_dict(i2) if isinstance(i2, dict) else i2 for i2 in v]
        _set_nested(output, path, v, k)
    return output


def _get_nested_default(d, path):
    return reduce(lambda d, k: d.setdefault(k, {}), path, d)


def _set_nested(d, path, value, full_path=None):
    try:
        _get_nested_default(d, path[:-1])[path[-1]] = value
    except (AttributeError, TypeError) as e:
        err = "DataTypeAttributeError: %s at '%s'" % (e, full_path)
        raise AttributeError(err)

def dict_pick(ddict: dict, keys: list, check_keys=False) -> dict:
    """
    To pick and return specific keys from a flatten dict.

    Args:
      ddict: dict
      keys: A list of dot notation path to keep
      check_keys: bool - check if all keys exist

    Returns:
      a dict with the picked value

    Example
      keys: ["name", "location.city"]
      flatten_dict: { "name": "MM", "location.city": "Charlotte",
          "location.state": "NC", "age": 100}
      returns: {
        "name": "MM",
        "location": {
          "city": "Charlotte"
        }
      }
    """
    fd = flatten_dict(ddict)

    # check that all keys exist
    if check_keys:
        for k in keys:
            assert k in fd, "missing key '%s'" % k

    ufd = _dict_pick_merge_l2d([_dict_pick_lookup_dict(fd, k) for k in keys])
    return unflatten_dict(ufd)


def _dict_pick_merge_l2d(iter: list):
    """
    Flatten a looked up list of tuples into dict
    Returns dict
    """
    df = {}
    for u in iter:
        if isinstance(u, list):
            for u2 in u:
                df[u2[0]] = u2[1]
    return df


def _dict_pick_lookup_dict(fd, k):
    """
    To lookup a key in a flatten dict 
    If the key is not found directly, it will start from the parent dot

    Returns list of tuples
    """
    if k in fd:
        return [(k, fd[k])]
    p = []
    for dk, dv in fd.items():
        if dk.startswith("%s." % k):
            p.append((dk, dv))
    return p


def dict_find_replace(ddict: dict, kv_repl: dict, is_flatten=False):
    """
    Find/Replace a KV dict in a dict

    Args:
      - ddict
      - kv_repl
      - is_flatten

    Returns
      dict
    """

    fd = ddict
    for k, v in fd.items():
        if isinstance(v, str) and v in kv_repl:
            fd[k] = kv_repl[v]
        elif isinstance(v, list):
            for l, e in enumerate(v):
                if isinstance(fd[k][l], str) and fd[k][l] in kv_repl:
                    fd[k][l] = kv_repl[fd[k][l]]
                elif isinstance(fd[k][l], dict):
                    fd[k][l] = dict_find_replace(fd[k][l], kv_repl)
        elif isinstance(v, dict):
            fd[k] = dict_find_replace(v, kv_repl)
    return fd


def dict_set(my_dict, key_string, value):
    """
    dict_set
    Mutable
    """
    here = my_dict
    keys = key_string.split(".")
    for key in keys[:-1]:
        here = here.setdefault(key, {})
    here[keys[-1]] = value


def dict_get(obj, path, default=None):
    """
    Get a value via dot notaion

    Args:
        @obj: Dict
        @attr: String - dot notation path
            object-path: key.value.path
            object-with-array-index: key.0.path.value
    Returns:
        mixed
    """
    def _getattr(obj, path):
        try:
            if isinstance(obj, list) and path.isdigit():
                return obj[int(path)]
            return obj.get(path, default)
        except:
            return default
    return reduce(_getattr, [obj] + path.split('.'))

def dict_pop(obj:dict, path:str) -> Any:
    """
    * Mutates #obj

    To pop a property from a dict dotnotation

    Args:
        obj:dict - This object will be mutated
        path:str - the dot notation path to update
        value:Any - value to update with

    Returns:
        Any - The value that was removed
    """

    here = obj 
    keys = path.split(".")

    for key in keys[:-1]:
        here = here.setdefault(key, {})
    if isinstance(here, dict):
        return here.pop(keys[-1])
    else:
        val = here[keys[-1]]
        del here[keys[-1]]
        return val

def dict_merge(*dicts) -> dict:                                                            
    """         
    Deeply merge an arbitrary number of dicts                                                                    
    Args:
        *dicts
    Return:
        dict

    Example
        dict_merge(dict1, dict2, dict3, dictN)
    """                                                                             
    updated = {}                                                                    
    # grab all keys                                                                 
    keys = set()                                                                    
    for d in dicts:                                                                 
        keys = keys.union(set(d))                                                   

    for key in keys:                                                                
        values = [d[key] for d in dicts if key in d]                                                                
        maps = [value for value in values if isinstance(value, dict)]            
        if maps:                                                                    
            updated[key] = dict_merge(*maps)                                       
        else:                                                                                                      
            updated[key] = values[-1]                                               
    return updated 

def chunk_list (lst:list, n:int):
    """
    Yield successive n-sized chunks from lst.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def dict_upper_keys(obj) -> dict:
    """
    Change all the keys to uppercase in dict
    Args:
        obj: dict
    Returns
        dict

    """
    return { k.upper(): v for k, v in obj }

def list_sorted_dict(l:list, key:str) -> list:
    """
    To order a list of dict, by the value in the dict

    list_sorted_dict(list, "name")
    """
    return sorted(l, key=itemgetter(key))

def dict_inspect_valid_keyname(obj:dict) -> bool:
    """
    Inspect a dict valid keys
    It goes recursively. 
    Will raise errors if a key is invalid
    """
    for k, v in obj.items():
        if isinstance(v, dict):
            dict_inspect_valid_keyname(v)
        elif isinstance(v, list):
            for l in v:
                if isinstance(l, dict):
                    dict_inspect_valid_keyname(l)

        if keyname_valid(k) is False:
            raise NameError("INVALID_DATA_KEY_ERROR:%s" % k)
    return True
        
#===

def hash_string(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

