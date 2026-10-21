"""Consume the independent parent-entry format offline; never query native state."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,sys
from parent_pointer_read_contract import normalize_rows,need
from pointer_read_models import JsonObject,object_value,expected_value
def main() -> int:
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--raw",type=Path,required=True);p.add_argument("--binding",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
 a=p.parse_args();need(a.raw.stat().st_size<=1024*1024 and a.binding.stat().st_size<=65536,"input stat caps")
 raw=a.raw.read_bytes();binding_bytes=a.binding.read_bytes()
 need(len(raw)<=1024*1024 and len(binding_bytes)<=65536,"input caps")
 binding=object_value(json.loads(binding_bytes),"binding");expected=binding.get("expected",binding)
 result: JsonObject=dict(normalize_rows([json.loads(x) for x in raw.splitlines() if x.strip()],expected))
 result.update(schema="xar.maintenance.parent_pointer_read.result.v1",machine_id=expected_value(expected)["machine_id"],observed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 raw_pin=dict(path=str(a.raw),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),binding_pin=dict(path=str(a.binding),bytes=len(binding_bytes),sha256=hashlib.sha256(binding_bytes).hexdigest()))
 payload=(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n").encode();need(len(payload)<=65536,"output cap")
 with a.output.open("xb") as f:f.write(payload)
 return 0
if __name__=="__main__":
 try:raise SystemExit(main())
 except (ValueError,KeyError,TypeError,OSError) as e:print(str(e),file=sys.stderr);raise SystemExit(2)
