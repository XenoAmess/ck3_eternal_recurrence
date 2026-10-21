"""Offline new-schema normalization; never launch, query, re-arm or grant payment."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from postload_admission import read,pin,need,obj
from postload_models import expected_value
from postload_wire import wire_json
from parent_postload_contract import normalize_rows,MODE

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('raw','binding','output'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    need(0<args.raw.stat().st_size<=1048576,'bounded complete native stream')
    raw=args.raw.read_bytes();need(raw.endswith(b'\n'),'complete newline-terminated stream')
    lines=raw.splitlines();need(2<=len(lines)<=4096,'bounded native events')
    rows: list[object]=[json.loads(line) for line in lines]
    binding=read(pin(args.binding))
    need(binding.get('schema')=='xar.maintenance.parent_postload.binding.v1'
        and binding.get('prepared_only') is True,'new prepared role')
    expected=expected_value(binding['expected'])
    normalized=normalize_rows(rows,binding['expected'])
    result: dict[str,object]={'schema':'xar.maintenance.parent_postload.result.v1',
        'mode':MODE,'machine_id':expected['machine_id'],**normalized,
        'raw_pin':pin(args.raw),'binding_pin':pin(args.binding)}
    payload=(json.dumps(wire_json(result),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    need(len(payload)<=65536 and not args.output.exists(),'bounded new derived result')
    with args.output.open('xb') as stream:stream.write(payload)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,KeyError,TypeError,OSError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(2)
