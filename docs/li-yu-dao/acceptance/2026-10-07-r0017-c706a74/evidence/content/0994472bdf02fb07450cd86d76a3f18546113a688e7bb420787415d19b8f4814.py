"""ROOT-only verify/freeze actual consumer bindings and one explicit serve CLI."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,sys
from consumer_binding import load_binding,reference,EXTERNAL_BASE
from persistent_native_mcp_queue_28 import TOOLS
from runtime_bindings import ref,write,need

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--request-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    path,raw=reference({'path':a.request.resolve().as_posix(),'sha256':a.request_sha256});request=json.loads(raw)
    binding=load_binding(path,a.request_sha256,profile=request['profile']['path'],queue=request['queue_directory'],output=request['client_output_directory'],tools=TOOLS)
    output=a.output.resolve();run=Path(binding['run_root']).resolve()
    need(EXTERNAL_BASE in output.parents and run in output.parents,'New explicit builder output must belong to actual run')
    output.mkdir(parents=True,exist_ok=False);target=output/'ROOT-BINDING.json'
    with target.open('xb') as stream:stream.write(raw)
    helper=Path(__file__).with_name('persistent_native_mcp_queue_28.py')
    argv=[sys.executable,'-B','-X','utf8',str(helper),'serve','--profile',binding['profile']['path'],'--queue',binding['queue_directory'],'--output',binding['client_output_directory'],'--binding',str(target),'--binding-sha256',ref(target)['sha256']]
    write(output/'serve-cli.json',{'argv':argv,'helper':ref(helper),'actual_binding':ref(target),'automatic_attach':False,'automatic_retry':False})
    receipt={'schema':'ck3.root.consumer24-binding-preparation.v1','utc':datetime.now(timezone.utc).isoformat(),'request':ref(path),'binding':ref(target),'serve_cli':ref(output/'serve-cli.json'),'attempt_id':binding['attempt_id'],'epoch_id':binding['epoch_id'],'source_revision':binding['source_revision'],'target':binding['target'],'read_only_file_verification':True,'Client_started':False,'native_attached':False,'game_acceptance':'NOT_RUN'}
    write(output/'PREPARATION.json',receipt);print(json.dumps(receipt,ensure_ascii=False));return 0

if __name__=='__main__':raise SystemExit(main())
