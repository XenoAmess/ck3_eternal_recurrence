"""ROOT-owned explicit queue operations using this new run's actual paths."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,subprocess,sys,time,uuid
from runtime_bindings import load,need,ref,write

def compact(v):
    omitted={'diagnostics','observation','observation_before','observation_after','native_clock_before','native_clock_after','native_command_history','connection_status','later_decisions_tree','later_actual_observation','widgets','native_ack','native_command_history_export'}
    if isinstance(v,dict):return {k:compact(x) for k,x in v.items() if k not in omitted}
    if isinstance(v,list):return [compact(x) for x in v]
    return v

def result(b,request_id,show_compact=False):
    client=Path(b['client_dir']);matches=list(client.glob('*-'+request_id+'.response.json'))
    if len(matches)!=1:
        print(json.dumps({'request_id':request_id,'response_count':len(matches),'status':'PENDING_OR_UNAVAILABLE_NO_RETRY'}));return
    response=json.loads(matches[0].read_bytes());print(json.dumps(response,ensure_ascii=False))
    if 'sdk_result' in response:
        p=client/response['sdk_result'];payload=json.loads(p.read_bytes());body=payload.get('structuredContent',payload)
        print(json.dumps(compact(body) if show_compact else body,ensure_ascii=False))
        print(json.dumps({'full_sdk_result':ref(p)}))

def parser():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bindings',required=True,type=Path);p.add_argument('--compact',action='store_true')
    sub=p.add_subparsers(dest='mode',required=True)
    send=sub.add_parser('send');send.add_argument('name');send.add_argument('--arguments-file',type=Path);send.add_argument('--wait-seconds',type=float,default=50)
    r=sub.add_parser('result');r.add_argument('request_id')
    sub.add_parser('client-status');sub.add_parser('start-client');sub.add_parser('check-bindings')
    schemas=sub.add_parser('schemas');schemas.add_argument('names',nargs='+')
    return p

def main():
    args=parser().parse_args();b=load(args.bindings)
    if args.mode=='check-bindings':print(json.dumps({'status':'ACTUAL_QUEUE_INPUTS_BOUND','binding':b['_binding_ref'],'runtime_credit':None}));return 0
    if args.mode=='result':result(b,args.request_id,args.compact);return 0
    if args.mode=='client-status':
        for name in ['ready.json','session-terminated.json','session-closed.json']:
            p=Path(b['client_dir'])/name
            if p.exists():print(json.dumps({name:json.loads(p.read_bytes())},ensure_ascii=False))
        return 0
    if args.mode=='schemas':
        need(b.get('metadata_path') is not None,'actual metadata_path required')
        rows=json.loads(Path(b['metadata_path']).read_bytes())
        if isinstance(rows,dict):rows=rows['tools']
        for row in rows:
            if row['name'] in args.names:print(json.dumps({'name':row['name'],'inputSchema':row['inputSchema']},ensure_ascii=False))
        return 0
    out=Path(b['dispatch_output']);out.mkdir(parents=True,exist_ok=True)
    if args.mode=='start-client':
        need(b.get('serve_cli') is not None,'new actual serve_cli required')
        cli=Path(b['serve_cli']);argv=json.loads(cli.read_bytes())['argv'];need(isinstance(argv,list) and argv,'actual argv required')
        with (out/'client.stdout').open('xb') as stdout,(out/'client.stderr').open('xb') as stderr:
            proc=subprocess.Popen(argv,cwd=b['repo_root'],stdout=stdout,stderr=stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        write(out/'CLIENT-START.actual.json',{'utc':datetime.now(timezone.utc).isoformat(),'argv':argv,'pid':proc.pid,'serve_cli':ref(cli),'bindings':b['_binding_ref'],'automatic_attach':False})
        print(json.dumps({'PID':proc.pid,'ready_path':(Path(b['client_dir'])/'ready.json').as_posix()}));return 0
    need(0<=args.wait_seconds<=50,'wait must remain within 0..50 seconds')
    arguments={} if args.arguments_file is None else json.loads(args.arguments_file.read_bytes());need(isinstance(arguments,dict),'argument object required')
    request_id='explicit-'+uuid.uuid4().hex
    packet={'schema':'ck3.lyd.mcp-request.v1','request_id':request_id,'operation':args.name if args.name in ['list_tools','close'] else 'call_tool'}
    if packet['operation']=='call_tool':packet.update(name=args.name,arguments=arguments)
    else:need(not arguments,'list_tools/close has no arguments')
    source=out/(request_id+'.json');write(source,packet)
    argv=[sys.executable,'-B','-X','utf8',b['queue_helper'],'enqueue','--queue',b['queue_dir'],'--request',str(source)]
    called=subprocess.run(argv,cwd=b['repo_root'],capture_output=True)
    write(out/(request_id+'-enqueue.json'),{'argv':argv,'bindings':b['_binding_ref'],'exit_code':called.returncode,'stdout':called.stdout.decode('utf-8','replace'),'stderr':called.stderr.decode('utf-8','replace'),'automatic_retry':False})
    need(called.returncode==0,'queue enqueue failed; no retry: '+called.stderr.decode('utf-8','replace'))
    print(json.dumps({'request_id':request_id,'packet':ref(source),'queued':True}),flush=True)
    until=time.monotonic()+args.wait_seconds
    while time.monotonic()<until:
        if list(Path(b['client_dir']).glob('*-'+request_id+'.response.json')):break
        time.sleep(.25)
    result(b,request_id,args.compact);return 0

if __name__=='__main__':raise SystemExit(main())
