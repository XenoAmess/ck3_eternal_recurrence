"""Local IndexTTS-2.5 entry point for the verified Windows installation.

This wrapper preserves each request, generated WAV and measurement receipt.
The upstream model/inference files are not modified. See LOCAL_INSTALL.md.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, sys, time, wave, traceback

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
os.environ.setdefault('HF_HOME',str(ROOT/'.cache/huggingface'))
os.environ.setdefault('TORCH_HOME',str(ROOT/'.cache/torch'))
os.environ.setdefault('NLTK_DATA',str(ROOT/'.cache/nltk_data'))
os.environ.setdefault('PYTHONIOENCODING','utf-8')
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write_json(path, value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)

def progress(event, **fields):
    print(json.dumps({'event':event,**fields},ensure_ascii=False),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument('--text-file',type=Path,help='UTF-8 Chinese/English/etc script; read in full.')
    source.add_argument('--batch-file',type=Path,help='JSON array [{id,text,output}]; one model load, ordered synthesis, stops on first failure. Relative outputs resolve beside this JSON.')
    p.add_argument('--reference',type=Path,required=True,help='Voice reference WAV. Official examples are installation-test material only.')
    p.add_argument('--output',type=Path,help='New WAV path for --text-file; existing outputs/receipts are refused.')
    p.add_argument('--device',choices=['cuda','cpu'],default='cuda')
    p.add_argument('--lang',choices=['ZH','EN','JA','ES','AR'],default='ZH')
    p.add_argument('--duration-factor',type=float,default=1.0)
    p.add_argument('--seed',type=int,default=20260922)
    p.add_argument('--max-text-tokens',type=int,default=80,help='Upper chunk token budget, conservative on 6GB VRAM.')
    p.add_argument('--cpu-threads',type=int,default=8)
    args=p.parse_args()
    args.reference=args.reference.resolve()
    if not 0.5<=args.duration_factor<=2.0:p.error('duration-factor must be between 0.5 and 2.0')
    if args.cpu_threads<1 or args.max_text_tokens<1:p.error('thread count and token budget must be positive')
    if args.batch_file:
        if args.output:p.error('--output is only valid with --text-file')
        source_path=args.batch_file.resolve()
        jobs=json.loads(source_path.read_text(encoding='utf-8-sig'))
        if not isinstance(jobs,list) or not jobs:p.error('batch file must be a nonempty JSON array')
        ids=set()
        for job in jobs:
            if not isinstance(job,dict) or set(job)!={'id','text','output'}:p.error('each batch entry must have exactly id, text, output')
            if not isinstance(job['id'],str) or not job['id'].strip() or job['id'] in ids:p.error('batch ids must be unique nonempty strings')
            ids.add(job['id'])
            if not isinstance(job['output'],str) or not job['output'].strip():p.error('batch output must be a nonempty path string')
            job['output']=(source_path.parent/Path(job['output'])).resolve()
    else:
        if args.output is None:p.error('--text-file requires --output')
        source_path=args.text_file.resolve()
        jobs=[{'id':'single','text':source_path.read_text(encoding='utf-8-sig').strip(),'output':args.output.resolve()}]
    outputs=set()
    for job in jobs:
        if not isinstance(job['text'],str) or not job['text'].strip():p.error('each text must be a nonempty string')
        output=job['output']
        if output.suffix.lower()!='.wav':p.error('each output must end in .wav')
        if output in outputs:p.error('duplicate output path in batch')
        outputs.add(output)
        if not output.parent.is_dir():p.error('each output parent directory must exist')
        if any(Path(str(output)+suffix).exists() for suffix in ['', '.request.json','.receipt.json','.failure.json']):p.error(f'output or sidecar exists; choose a new attempt filename: {output}')
    request_base={
        'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_file':str(source_path),'source_file_sha256':sha(source_path),
        'reference':str(args.reference),'reference_sha256':sha(args.reference),
        'device_requested':args.device,'lang':args.lang,
        'duration_factor':args.duration_factor,'seed':args.seed,'max_text_tokens':args.max_text_tokens,
        'wrapper_sha256':sha(__file__),'upstream_infer_sha256':sha(ROOT/'indextts/infer_v2_5.py'),
        'config_sha256':sha(ROOT/'checkpoints/config.yaml'),
        'use_deepspeed':False,'use_cuda_kernel':False,'use_accel':False,'use_torch_compile':False,'use_qwen_emo':False,
    }
    for job in jobs:write_json(Path(str(job['output'])+'.request.json'),{**request_base,**job,'output':str(job['output'])})
    os.chdir(ROOT)
    started=time.perf_counter()
    import torch, numpy as np, random
    torch.set_num_threads(args.cpu_threads)
    random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed)
    if args.device=='cuda':
        if not torch.cuda.is_available():raise RuntimeError('CUDA requested but unavailable; CPU must be explicitly selected')
        torch.cuda.manual_seed_all(args.seed);torch.cuda.reset_peak_memory_stats()
    from indextts.infer_v2_5 import IndexTTS2
    loading_started=time.perf_counter()
    tts=IndexTTS2(cfg_path=str(ROOT/'checkpoints/config.yaml'),model_dir=str(ROOT/'checkpoints'),
        device='cuda:0' if args.device=='cuda' else 'cpu',use_bf16=args.device=='cuda',
        use_cuda_kernel=False,use_deepspeed=False,use_accel=False,use_torch_compile=False,use_qwen_emo=False)
    if args.device=='cuda':torch.cuda.synchronize()
    loaded=time.perf_counter()
    progress('model_ready',model_load_seconds=loaded-loading_started,device=str(tts.device),jobs=len(jobs))
    for index,job in enumerate(jobs):
        output=job['output'];item_started=time.perf_counter()
        progress('item_started',index=index,id=job['id'],output=str(output))
        try:
            if output.exists():raise FileExistsError('output appeared after preflight; refused overwrite')
            random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed)
            tts.infer(spk_audio_prompt=str(args.reference),text=job['text'],lang=args.lang,output_path=str(output),
                duration_factor=args.duration_factor,verbose=True,max_text_tokens_per_segment=args.max_text_tokens)
            if args.device=='cuda':torch.cuda.synchronize()
            ended=time.perf_counter()
            with wave.open(str(output),'rb') as f:
                info={'sample_rate':f.getframerate(),'channels':f.getnchannels(),'sample_width_bytes':f.getsampwidth(),
                      'frames':f.getnframes(),'duration_seconds':f.getnframes()/f.getframerate()}
                pcm=f.readframes(f.getnframes())
            if info['sample_width_bytes']!=2:raise ValueError('expected PCM16 WAV')
            samples=np.frombuffer(pcm,dtype='<i2').astype(np.float64)
            if not samples.size or not np.any(samples):raise ValueError('generated WAV is empty or silent')
            receipt={**info,'id':job['id'],'output':str(output),'wav_sha256':sha(output),'wav_bytes':output.stat().st_size,
                'request_sha256':sha(Path(str(output)+'.request.json')),
                'peak_abs':float(np.max(np.abs(samples)))/32768.0,'rms':float(np.sqrt(np.mean((samples/32768.0)**2))),
                'clip_fraction':float(np.mean(np.abs(samples)>=32767)),
                'torch_version':torch.__version__,'cuda_runtime':torch.version.cuda,'device':str(tts.device),
                'model_load_seconds':loaded-loading_started,'inference_seconds':ended-item_started,
                'process_elapsed_seconds':ended-started,'inference_rtf':(ended-item_started)/info['duration_seconds'],
                'peak_cuda_allocated_bytes':torch.cuda.max_memory_allocated() if args.device=='cuda' else None,
                'peak_cuda_reserved_bytes':torch.cuda.max_memory_reserved() if args.device=='cuda' else None,
                'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'verification':'real synthesis plus waveform probe; listening/transcription is separate'}
            write_json(Path(str(output)+'.receipt.json'),receipt)
            progress('item_completed',**receipt)
        except Exception as error:
            failure={'id':job['id'],'output':str(output),'error':repr(error),'traceback':traceback.format_exc(),
                     'elapsed_seconds':time.perf_counter()-item_started,'completed_items':index,
                     'partial_output_preserved':output.exists()}
            write_json(Path(str(output)+'.failure.json'),failure)
            progress('item_failed',**failure)
            raise
    progress('batch_completed',items=len(jobs),model_instances=1,total_seconds=time.perf_counter()-started)

if __name__=='__main__':main()
