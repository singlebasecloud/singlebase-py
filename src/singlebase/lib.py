#-----------------------------
# -- Singlebase --
#-----------------------------

import re
import json
import uuid
import arrow
import cuid2
import datetime

# Date format
FORMAT_ISO_DATE = "YYYY-MM-DD"
FORMAT_ISO_TIME = "HH:mm:ss"
FORMAT_ISO_DATETIME = "YYYY-MM-DD HH:mm:ss"

DATES_FORMAT = {
    "ISO_DATE": FORMAT_ISO_DATE,
    "ISO_TIME": FORMAT_ISO_TIME,
    "ISO_DATETIME": FORMAT_ISO_DATETIME
}

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
