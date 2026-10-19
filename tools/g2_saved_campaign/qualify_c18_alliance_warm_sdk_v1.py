"""Compile/import the exact single-leaf composition; reuse M5 business proof.

No business test matrix is repeated. No Driver state, ledger or Game is opened.
All unchanged production imports come from actual source14, and only the pinned
family module is supplied from the proposed bytes in memory.
"""
import importlib.util
import json
from pathlib import Path
import sys
import types

import prepare_c18_alliance_warm_sdk_v1 as producer


def qualify():
    producer.exact.require(sys.dont_write_bytecode,'run -B')
    producer.exact.require(not any(n=='xar_autoplayer' or n.startswith('xar_autoplayer.')
                                  for n in sys.modules),'fresh source-only qualifier required')
    changed,rows,plan=producer.compose()
    sys.path.insert(0,str(producer.BASE_ROOT))
    import xar_autoplayer
    name='xar_autoplayer.family_marriage_formal_consumer'
    raw=changed[producer.LEAF]
    module=types.ModuleType(name)
    module.__file__=str(producer.BASE_ROOT/producer.LEAF)
    module.__package__='xar_autoplayer'
    module.__spec__=importlib.util.spec_from_loader(name,loader=None,origin=module.__file__)
    sys.modules[name]=module
    try:
        exec(compile(raw,'<C18-alliance-inmemory-family>','exec',dont_inherit=True),module.__dict__)
        from xar_autoplayer.bridge.service import GameplayBridgeService
        producer.exact.require(callable(GameplayBridgeService),'actual original Service import failed')
        producer.exact.require(module._plan_existing_resolution.__code__.co_filename=='<C18-alliance-inmemory-family>',
                               'family import did not use composed bytes')
        loaded=[]
        for imported,value in list(sys.modules.items()):
            if imported=='xar_autoplayer' or imported.startswith('xar_autoplayer.'):
                path=getattr(value,'__file__',None)
                if path:
                    producer.exact.require(Path(path).resolve().is_relative_to(producer.BASE_ROOT.resolve()),
                                           'unchanged dependency escaped actual source14: '+imported)
                    loaded.append(imported)
        business=producer.REPO/'docs/ck3-native-ai/evidence/alliance9421-self-recipient-source-2026-10-19.json'
        source=business.read_bytes()
        producer.exact.check_bytes(source,(6458,'fdbc6eafc2ef4cfc9719ce8a867a4269c2f4015d3e0220cac570a681f33e6879'),
                                   'existing exact M5 business proof')
        plan['qualification']={'kind':'Full actual1445 content/blob verification, exact reversible four hunks, two-method AST/import guard, compile and actual source14 dependency import',
            'status':'PASS','business_matrix_repeated':False,'new_business_tests':0,
            'existing_M5_proof':{'path':str(business),**producer.exact.pin(source)},
            'existing_M5_results':'13 focused PASS; actual source14 Service5b49 in-memory production path1 PASS',
            'loaded_production_module_count':len(loaded),'unchanged_production_imports_only_actual_source14':True,
            'new_children':0,'Task_Game_RPC_calls':0,'Driver_SAVE_ledger_body_reads':0,
            'D_Git_output_writes':0,'retained_test_scratch_files':0,'real_alliance_or_marriage_credit':0}
        plan['status']='SOURCE_COMPOSITION_QUALIFIED_NOT_ADOPTED'
        return plan
    finally:
        sys.modules.pop(name,None)


if __name__=='__main__':
    proof=qualify()
    if len(sys.argv)==2:
        path=Path(sys.argv[1]).resolve()
        producer.exact.require(path.is_relative_to(producer.REPO.resolve()),'small source proof outside workspace')
        raw=(json.dumps(proof,indent=2,ensure_ascii=False)+'\n').encode()
        producer.exact.require(len(raw)<=16*1024,'small source proof cap')
        with path.open('xb') as stream:stream.write(raw)
        print(json.dumps({'proof':{'path':str(path),**producer.exact.pin(raw)}}))
    else:print(json.dumps(proof,indent=2,ensure_ascii=False))
