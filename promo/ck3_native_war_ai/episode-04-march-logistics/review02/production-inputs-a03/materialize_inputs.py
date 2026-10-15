"""Materialize exact metadata members into one NEW explicit directory."""
from pathlib import Path
import argparse,hashlib,json,zipfile
def need(ok,why):
    if not ok:raise ValueError(why)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();base=Path(__file__).resolve().parent
    index=json.loads((base/'bundle-index.json').read_bytes());archive=base/index['archive']['path']
    raw=archive.read_bytes()
    need(len(raw)==index['archive']['bytes'] and hashlib.sha256(raw).hexdigest()==index['archive']['sha256'],'archive changed')
    need(not args.output.exists(),'output already exists')
    payload=[]
    with zipfile.ZipFile(archive) as z:
        need(z.namelist()==[row['path'] for row in index['members']],'archive member list differs')
        for row in index['members']:
            rel=Path(row['path']);need(not rel.is_absolute() and '..' not in rel.parts,'nonportable member')
            data=z.read(row['path']);need(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'member changed')
            payload.append((rel,data))
    args.output.mkdir(parents=True,exist_ok=False)
    for rel,data in payload:
        path=args.output/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as out:out.write(data)
    cues=json.loads((args.output/'inputs/narration.cues.bilingual.json').read_bytes())['cues']
    need(len(cues)==69 and len({row['id'] for row in cues})==69,'expected69 original cues')
    for language in ['zh','en']:
        with (args.output/('narration.'+language+'.txt')).open('x',encoding='utf-8',newline='\n') as out:
            out.write('\n\n'.join('['+row['id']+']\n'+row[language] for row in cues)+'\n')
    print(json.dumps({'state':'MATERIALIZED_EXACT_METADATA','output':str(args.output),'members':len(payload),'provider_calls':0}))
if __name__=='__main__':main()
