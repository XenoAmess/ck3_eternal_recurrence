import collections
import hashlib
import json
import re
from pathlib import Path

ROOT=Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-008')
OUT=Path(__file__).parent
HEADER=re.compile(rb'^\[(\d\d:\d\d:\d\d)\]\[([A-Z])\]\[([^\]]+)\]: ?(.*)$')
TOKENS=re.compile(rb'\b(?:lyd|xar|ervc|zhongguo)[A-Za-z0-9_.]*')
result={}
for name in ['error.log','debug.log','game.log']:
    path=ROOT/'userdir/logs'/name
    groups={}
    digest=hashlib.sha256()
    namespace_counts=collections.Counter()
    project_e_digest=hashlib.sha256()
    project_e_count=0
    record=[]
    start=1
    offset=0
    byte_offset=0
    product_times=collections.Counter()
    detail=[]
    def consume(lines,start,offset):
        global project_e_count
        if not lines:return
        raw=b''.join(lines)
        hdr=HEADER.match(lines[0].rstrip(b'\r\n'))
        if not hdr:return
        time=hdr[1].decode();severity=hdr[2].decode();origin=hdr[3].decode()
        tokens=sorted(set(TOKENS.findall(raw)))
        sig=re.sub(rb'^\[\d\d:\d\d:\d\d\]',b'[TIME]',raw)
        sigsha=hashlib.sha256(sig).hexdigest()
        is_script=origin=='jomini_script_system.cpp:304'
        families=set()
        for t in tokens:
            token=t.decode()
            if token.startswith('lyd_im'):family='fixture_matrix_lyd_im'
            elif token.startswith('lyd_cp'):family='fixture_charter_lyd_cp'
            elif token.startswith('lyd_r3'):family='fixture_entry_lyd_r3'
            elif token.startswith('lyd_r4'):family='fixture_observer_lyd_r4'
            elif token.startswith('lyd_c2'):family='product_c2'
            elif token.startswith('lyd_c3'):family='product_c3'
            elif token.startswith('lyd_i3b'):family='product_i3b'
            elif token.startswith('lyd_np'):family='prototype_unmounted_lyd_np'
            elif token.startswith('lyd'):family='product_lyd_other'
            else:family='other_project_'+token.split('_',1)[0]
            families.add(family)
        for family in families:namespace_counts[(severity,family)]+=1
        if severity=='E' and is_script:
            project_e_digest.update(raw)
            project_e_count+=1
            product_times[time]+=1
        if severity in ('E','W'):
            g=groups.setdefault(sigsha,{'first_time':time,'last_time':time,'first_line':start,'last_line':start,'first_byte_offset':offset,'count':0,'severity':severity,'origin':origin,'families':sorted(families),'tooltip':'while building tooltip/description' in raw.decode('utf-8',errors='replace'),'text':raw.decode('utf-8',errors='replace')[:20000]})
            g['count']+=1;g['last_time']=time;g['last_line']=start
    with path.open('rb') as f:
        for lineno,raw in enumerate(f,1):
            digest.update(raw)
            if HEADER.match(raw.rstrip(b'\r\n')):
                consume(record,start,offset)
                record=[];start=lineno;offset=byte_offset
            record.append(raw);byte_offset+=len(raw)
    consume(record,start,offset)
    result[name]={'sha256':digest.hexdigest(),'bytes':byte_offset,'script_e_count':project_e_count,'script_e_sequence_sha256':project_e_digest.hexdigest(),'namespace_severity_records': [{'severity':s,'namespace_family':n,'record_count':c} for (s,n),c in namespace_counts.most_common()], 'script_e_records_by_log_clock':dict(sorted(product_times.items())),'error_warning_signature_groups':groups}
    print(name,'runtime',project_e_count,'sequence',project_e_digest.hexdigest(),'tooltip',sum(g['count'] for g in groups.values() if g['tooltip']),'non-tooltip',sum(g['count'] for g in groups.values() if g['origin']=='jomini_script_system.cpp:304' and not g['tooltip']))
(OUT/'DEEP-SCAN.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print('WARNINGS')
for name in ['game.log','debug.log']:
    for g in result[name]['error_warning_signature_groups'].values():
        if g['severity']=='W':print(name,g['count'],g['text'][:1500])
print('ERROR TIME RANGES')
for g in result['error.log']['error_warning_signature_groups'].values():
    if g['origin']=='jomini_script_system.cpp:304':
        print(g['count'],g['first_time'],g['last_time'],g['tooltip'],re.findall(r'lyd_c2_[a-z_]+|line: \d+',g['text']))
srcs={'common/scripted_effects/lyd_c2_vote_effects.txt':[(1,103)],'common/scripted_effects/lyd_c2_snapshot_effects.txt':[(1,45),(204,290),(305,349),(389,408)],'common/scripted_effects/lyd_c2_setup_effects.txt':[(1,32),(113,144),(188,218)],'events/lyd_c2_consent_events.txt':[(1,70)],'common/decisions/lyd_c2_consent_decisions.txt':[(1,45)]}
proof={}
for rel,ranges in srcs.items():
    path=ROOT/'content/production'/rel
    raw=path.read_bytes();lines=raw.decode('utf-8-sig').splitlines()
    proof[rel]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'ranges':[{'start':a,'end':b,'lines':[{'line':i,'text':lines[i-1]} for i in range(a,min(b,len(lines))+1)]} for a,b in ranges]}
(OUT/'COLD-PRODUCT-ERROR-SOURCE-PROOF.json').write_bytes((json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode())
print('SOURCE SHAS',json.dumps({k:v['sha256'] for k,v in proof.items()}))
