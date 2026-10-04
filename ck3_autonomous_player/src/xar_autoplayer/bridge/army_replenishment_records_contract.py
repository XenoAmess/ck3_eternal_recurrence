"""Complete stored persistent-regiment DATA observations; no future fill forecast."""
from __future__ import annotations

_ROW={"army_regiment_id","source","status","ready","native_data_record_count","unavailable_reason","records"}
_I32=("record_index","persistent_regiment_id","chunk_index","current_soldiers","maximum_soldiers","effective_current_soldiers","state_raw")
_BOOL=("native_can_replenish","native_chunk_can_replenish")
_I64=("persistent_monthly_replenishment_fraction_raw","persistent_prepared_replenishment_fraction_raw")
_SCALE=("persistent_monthly_replenishment_fraction_scale","persistent_prepared_replenishment_fraction_scale")
_RECORD={"status","unavailable_reason",*_I32,*_BOOL,*_I64,*_SCALE}

def integer(value, bits, name, nullable=True):
    if value is None and nullable:
        return None
    if type(value) is not int or not -(2**(bits-1)) <= value < 2**(bits-1):
        raise ValueError(f"native full DATA {name} must be signed int{bits}" + (" or null" if nullable else ""))
    return value

def normalize_regiment_replenishment_records_v1(value: object) -> list[dict[str,object]]:
    if not isinstance(value,list):
        raise ValueError("native full DATA must be an array")
    result=[]
    for row in value:
        if not isinstance(row,dict) or set(row) != _ROW or row["source"] != "native_all_data_records":
            raise ValueError("native full DATA regiment schema is malformed")
        integer(row["army_regiment_id"],32,"army_regiment_id",False)
        status=row["status"]
        if status not in {"available","partial","unavailable"} or type(row["ready"]) is not bool or row["ready"] != (status=="available"):
            raise ValueError("native full DATA regiment readiness is malformed")
        count=integer(row["native_data_record_count"],32,"native_data_record_count")
        if count is not None and count < 0:
            raise ValueError("native full DATA count cannot be negative")
        records=row["records"]
        if not isinstance(records,list):
            raise ValueError("native full DATA records must be an array")
        if status in {"available","partial"} and (count is None or len(records)!=count):
            raise ValueError("native full DATA stored count/order is incomplete")
        reason=row["unavailable_reason"]
        if (status=="available" and reason is not None) or (reason is not None and (not isinstance(reason,str) or not reason)):
            raise ValueError("native full DATA regiment reason is malformed")
        for index,record in enumerate(records):
            if not isinstance(record,dict) or set(record)!=_RECORD or record["status"] not in {"available","unavailable"}:
                raise ValueError("native full DATA record schema is malformed")
            for field in _I32:
                integer(record[field],32,field,field not in {"record_index","persistent_regiment_id","chunk_index"})
            for field in _I64:
                integer(record[field],64,field)
            for field in _BOOL:
                if record[field] is not None and type(record[field]) is not bool:
                    raise ValueError("native full DATA predicate must be bool or null")
            if record["record_index"]!=index or any(record[field]!=100000 for field in _SCALE):
                raise ValueError("native full DATA record order/scale is malformed")
            available=record["status"]=="available"
            reason=record["unavailable_reason"]
            if available and (reason is not None or any(record[field] is None for field in (*_I32,*_I64,*_BOOL))):
                raise ValueError("native available full DATA record is incomplete")
            if not available and (not isinstance(reason,str) or not reason):
                raise ValueError("native unavailable full DATA record requires its reason")
        if status=="available" and any(record["status"]!="available" for record in records):
            raise ValueError("native complete full DATA contains an unavailable record")
        result.append({**row,"records":[dict(record) for record in records]})
    return result
