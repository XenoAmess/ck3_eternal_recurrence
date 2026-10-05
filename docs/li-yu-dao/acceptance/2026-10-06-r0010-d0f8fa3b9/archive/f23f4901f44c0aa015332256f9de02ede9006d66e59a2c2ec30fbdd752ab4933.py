"""Exact typed/stored bodies from the sealed R6 helper; no main-tree import."""
from decimal import Decimal
import json
from bounded_save_parser import one

def unquote(value):
    return json.loads(value) if isinstance(value, str) and value.startswith(chr(34)) else value

def typed(data):
    if not isinstance(data, list):
        return {"type": None, "identity": None, "entries": data}
    kind, identity = one(data, "type"), one(data, "identity")
    result = {"type": kind, "identity": identity, "entries": data}
    if kind == "value" and isinstance(identity, str):
        # R2 actual three-round saves bind the persistent script value encoding.
        result["number"] = str(Decimal(identity) / Decimal(100000))
        result["scale"] = 100000
    elif kind == "boolean":
        result["boolean"] = {"0": False, "1": True}.get(identity)
    return result

def stored(entries):
    owner = one(entries, "variables")
    if owner is None:
        return {}, {}, None
    data, lists = one(owner, "data") or [], one(owner, "list") or []
    variables, collections = {}, {}
    for row in data:
        fields = row["value"]
        if not isinstance(fields, list):
            raise ValueError("Unexpected saved variable row")
        name = unquote(one(fields, "flag"))
        if isinstance(name, str) and name.startswith("lyd_"):
            if name in variables:
                raise ValueError("Duplicate saved variable: " + name)
            variables[name] = {"present": True, "tick": one(fields, "tick"),
                               **typed(one(fields, "data")), "row_entries": fields}
    for row in lists:
        fields = row["value"]
        if not isinstance(fields, list):
            raise ValueError("Unexpected named list row")
        name = unquote(one(fields, "name"))
        if isinstance(name, str) and name.startswith("lyd_"):
            if name in collections:
                raise ValueError("Duplicate saved list: " + name)
            collections[name] = {"present": True, "items": [typed(item["value"]) for item in fields if item["key"] == "item"],
                                 "duration_entries": one(fields, "duration"), "row_entries": fields}
    return variables, collections, owner
