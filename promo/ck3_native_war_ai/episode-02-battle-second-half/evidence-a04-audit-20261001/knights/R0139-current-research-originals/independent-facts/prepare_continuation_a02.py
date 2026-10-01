from pathlib import Path
import hashlib,json
p=Path(__file__).parent
old=p/'verify_originals.py';b=old.read_bytes();s=b.decode('utf-8')
s=s.replace("OUT=Path(__file__).resolve().parent","OUT=Path(__file__).resolve().parent/'continuation-a02'\nOUT.mkdir(exist_ok=False)")
s=s.replace("bound(pair['save']);save=read(savepath)","bound(pair['save']['response']);save=read(savepath)")
s=s.replace("read(bound(pair['snapshot']))['body']['revision']","read(bound(pair['snapshot']['response']))['body']['revision']")
new=p/'verify_originals_a02.py'
with new.open('x',encoding='utf-8',newline='\n')as f:f.write(s)
with (p/'continuation-source-identity-a02.json').open('x',encoding='utf-8')as f:json.dump({'a01_original':{'path':str(old),'sha256':hashlib.sha256(b).hexdigest().upper()},'a02_created':{'path':str(new),'sha256':hashlib.sha256(new.read_bytes()).hexdigest().upper()},'a01_result':'Packaging KeyError path occurred at pair.save wrapper, after 19 checks; not game RED and no melt yet. Original file and result retained.'},f,indent=2)
