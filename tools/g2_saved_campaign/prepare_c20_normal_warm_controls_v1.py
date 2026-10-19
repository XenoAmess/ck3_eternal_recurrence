"""Exact C18 -> C20 normal warm controls; pure bytes and source checks only."""
import ast
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
PORT = REPO/'_runtime/compose_C18_warm_controls93.py'
PORT_SHA = '2bbdee3dc30521aca2b4f774d75b8f1df9e73b5816be3d3d6d880dac20e63fa6'
BUSINESS_COMMIT = 'f19864de1cc073eed62617faad2307c57ad45a97'
ROWS_SHA = '7b62abe6c91e382af449b1c7057bf304d729db310ad88deea4861218c8379935'
DOCS = REPO/'docs/ck3-native-ai/evidence'
PLAN = DOCS/'source20-minimal-warm-sdk-source-plan-2026-10-20.json'
ANCHOR = DOCS/'source20-root-git-actual-2026-10-20.json'
CLASSIFIER = T/'root_p37c11_prisoner_epoch_classifier.py'
CLASSIFIER_SHA = '0bff8fae24c072d5f05285ba62c503dfed408f8095690fb8dffec16fe72ec28b'
PAIRS = (('P37C18','P37C20'),('p37c18','p37c20'),('-C18','-C20'),('SDKC18','SDKC20'),
    ('p51_resident_successor_adoption_c18','p51_resident_successor_adoption_c20'))
BASE = {
 'root_p37c18_sdk_queue.py':(267957,'f4adb613364e56413b5244e13122f2530a897a5e42d76c1fa9897e2c7bfcd694'),
 'root_p37c18_mcp_entry.py':(12630,'3c249181f4991331eb569956777a9f20a3edc48e154eb85453047b104e4f237c'),
 'root_native_build_binding_p37c18.py':(4090,'1d5f41c5645fc9256a4b3346a6a3c8aa3b3324c7331aa47b044fb2cca0ce8aaa'),
 'root_p37c18_automatic_natural_succession_handoff.py':(38624,'c70043630269cb676d6491d6ea534771f292b9cd8aef82a92965e58e346c4c0a'),
 'p51_resident_successor_adoption_c18.py':(24607,'a3cc6fec9a98eefe76bee916771d196ce77cd25af0cad8f6ff6be7c93ccbf6a2'),
 'launch_sdk_p37c18_owner.py':(5462,'9c1efcd7fb39d787cbd4c3088366ea269bafff46b94947889b33bfe5a8226bee'),
 'root_p37c18_warm_resume.py':(14752,'56659907137b021f812382d718a9294faa5ad2ca7bf34818ad16c454f5c6c1ca')}
EXPECTED = (
 'ed5f8b77b5fbb69b27be204d36f28e1a2e45acd572ff7fae2658444f07f9a09d',
 'a00aa55f62ec6184a31f4a6f4f9957ed95dfaceb55094352adc70af89bb68a6f',
 '93468a9628b2b3f7a24c5dbd7013ceb6eb1d3f6bbb32a8adb4240e0a4b30b50f',
 'dca34aee98f396da3a8593c10df8618643e16022a294e3b956585266adf2ca85',
 'af99ff1943c46cf053ac19e9244152251f541973c2ee9a6c0f86b6c3a7b357a4',
 'e6063206ff45cf7d5f7da42e0534bc058adc51798bcf7cc19e8f0d3370272630',
 'b4abc2203eaeaef17f1b058cdaf416c39b31262654a90450e31f2e583d0894c7')


def require(ok, message):
    if not ok:
        raise ValueError('C20 normal controls denied: '+message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, size, digest):
    raw = path.read_bytes()
    require(len(raw) == size and sha(raw) == digest, 'frozen input changed: '+str(path))
    return raw


def source_binding():
    plan = json.loads(checked(PLAN,10765,'fe1e72416971ca15617d48ec79415f6b841eb776a8dc7718502783926df2d41f'))
    record = json.loads(checked(ANCHOR,4622,'8836237f119acb3e7d59d8a179bd954711f46397d8f9097b14ad2ec92264649d'))
    require(plan['machine_id'] == record['machine_id'] == MACHINE
        and plan['schema'] == 'xar.source20.minimal-warm-sdk-frozen-source-plan/v1'
        and record['schema'] == 'xar.root.Source20-Git-anchor-actual/v1', 'business provenance differs')
    output, actual = plan['output'], record['actual']
    require(output['changed_existing_leaves'] == 4 and output['new_leaves'] == 2
        and output['unchanged_original_leaves'] == 1441
        and actual['commit'] == BUSINESS_COMMIT and actual['parent'] == plan['base']['business_commit']
        == '0e8a190bf3e5ec187e7bc30d76310585922a0b50'
        and actual['tree'] == 'c868c9aa96fc012cd34f05e3fad6ebf7b8f3d8b8'
        and actual['ref'] == 'refs/heads/campaign/robert-v20261019-c20-campaign-root-retry-warm-01',
        'six-leaf actual business anchor differs')
    for manifest in (output['complete_manifest'],actual['complete_manifest']):
        require(manifest['file_count'] == 1447 and manifest['source_bytes'] == 59065188
            and manifest['canonical_rows_JSON']['sha256'] == ROWS_SHA, 'complete Source20 manifest differs')
    require(plan['family_fix_preserved']['sha256'] == 'd8bbaa3c469f10f974b43335f8505913ae292c4f9b487dddf3e8da1a3c93deaf',
        'family correction lost')
    checked(CLASSIFIER,260570,CLASSIFIER_SHA)
    return {'plan':str(PLAN), 'actual_anchor':str(ANCHOR), 'business_commit':BUSINESS_COMMIT,
        'full_files':1447, 'rows_sha256':ROWS_SHA, 'changed_existing':4, 'new_leaves':2}


def compose():
    binding = source_binding()
    raw = checked(PORT,6120,PORT_SHA)
    text = raw.decode().replace('P37C18oldReadyQueue','P37C20oldReadyQueue').replace('P37C17oldReadyQueue','P37C18oldReadyQueue')
    scope = {'__name__':'C20_source_port_only', '__file__':str(PORT)}
    exec(compile(text,str(PORT),'exec'),scope)
    scope['PAIRS'] = PAIRS
    graph = {}; protected = 0
    for (name,(size,digest)), candidate_sha in zip(BASE.items(), EXPECTED):
        original = checked(T/name,size,digest)
        candidate = scope['port'](original.decode()).encode()
        require(sha(candidate) == candidate_sha, 'earlier RAM candidate drifted: '+name)
        new_name = scope['mapped'](name); compile(candidate,new_name,'exec')
        graph[new_name] = candidate
        old = [node.value for node in ast.walk(ast.parse(original)) if isinstance(node,ast.Constant) and isinstance(node.value,str)]
        new = [node.value for node in ast.walk(ast.parse(candidate)) if isinstance(node,ast.Constant) and isinstance(node.value,str)]
        for value in old:
            if value == MACHINE or value.startswith('native-') or (len(value)==64 and all(c in '0123456789abcdef' for c in value)) or 'C16' in value or 'c16' in value:
                require(new.count(value) == old.count(value), 'protected constant changed'); protected += 1
    require(protected == 45 and sum(map(len,graph.values())) == 368122, 'seven-source shape differs')
    return graph, binding
