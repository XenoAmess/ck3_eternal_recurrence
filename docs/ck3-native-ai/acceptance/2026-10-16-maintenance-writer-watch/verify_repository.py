from pathlib import Path
import argparse,hashlib,json,re,urllib.parse,zipfile
def require(ok,message):
    if not ok:raise RuntimeError(message)
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path);p.add_argument('--overlay',type=Path);p.add_argument('--extract-originals',type=Path);a=p.parse_args()
root=(a.repo or Path(__file__).resolve().parents[4]).resolve();overlay=a.overlay.resolve() if a.overlay else None
def resolve(rel):
    path=Path(rel);require(not path.is_absolute() and '..' not in path.parts,'Unsafe relative repository path')
    return overlay/path if overlay is not None and (overlay/path).is_file() else root/path
base='docs/ck3-native-ai/acceptance/2026-10-16-maintenance-writer-watch/'
manifest=json.loads(resolve(base+'FILE-MANIFEST.json').read_bytes())
for item in manifest['files']:
    raw=resolve(item['path']).read_bytes();require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'Exact candidate file differs '+item['path'])
index=json.loads(resolve(base+'ARCHIVE-INDEX.json').read_bytes());archive=resolve(index['archive']['path'])
with zipfile.ZipFile(archive) as z:
    require(set(z.namelist())=={i['member'] for i in index['members']},'Archive member set differs')
    for item in index['members']:
        raw=z.read(item['member']);require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'Raw historical member differs')
    if a.extract_originals:
        target=a.extract_originals.resolve();require(not target.exists(),'New extraction directory required');target.mkdir(parents=True)
        for item in index['members']:
            relative=Path(item['member']);require(not relative.is_absolute() and '..' not in relative.parts,'Unsafe original member path');out=target/relative;out.parent.mkdir(parents=True,exist_ok=True)
            with out.open('xb') as f:f.write(z.read(item['member']))
doc='docs/ck3-native-ai/war-payment-four-term-writer-watch-12004.md'
for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',resolve(doc).read_text(encoding='utf-8')):
    if '://' in link:continue
    target=link.split('#',1)[0]
    if target:
        # Normalize only internal authored links; enforce staying inside the repository.
        absolute=(root/Path(doc).parent/urllib.parse.unquote(target)).resolve();require(root in absolute.parents,'Link leaves repository');relative=absolute.relative_to(root);require(resolve(relative).is_file(),'Document target missing '+str(relative))
report=json.loads(resolve(base+'TARGETED-QUALIFICATION.final-a01.actual.json').read_bytes())
require(report['status']=='PASS_WITH_EXPLICIT_OCCUPIED_RAW_VECTOR_LIMIT' and report['occupied_before_attach']['raw_all6_equal'] is False and report['known_producer'] is False and report['maintenance_attribution']=='unclosed','Raw qualification boundary changed')
print(json.dumps(dict(status='PASS',files=len(manifest['files']),archive_members=len(index['members']),all_document_links_held=True,CK3_observed=False,known_producer=False,military_attribution='unclosed')))
