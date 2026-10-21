"""Small typed collection readers shared by this synthetic runner only."""
from typing import cast
from postload_models import JsonObject,object_value

def text(value: object,name: str) -> str:
    if type(value) is not str:
        raise ValueError(name+' must be text')
    return cast(str,value)

def objects(value: object,name: str) -> list[JsonObject]:
    if type(value) is not list:
        raise ValueError(name+' must be list')
    return [object_value(item,name) for item in value]

def strings(value: object,name: str) -> list[str]:
    if type(value) is not list:
        raise ValueError(name+' must be list')
    return [text(item,name) for item in value]
