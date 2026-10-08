"""Prepare ordinary fixture inputs using the selected shared source primitives."""
from __future__ import annotations
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import sys

CONFIG_NAMES = ('pdx_settings.txt','tutorial.txt','presets.txt','player/game_rules/presets.txt')


def require(value, message):
    if not value: raise ValueError(message)


def pin(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')


def checked_copy(row,target):
    source=Path(row['path']).resolve()
    actual=pin(source)
    require(actual['bytes']==row['bytes'] and actual['sha256']==row['sha256'].lower(), 'Frozen input changed: '+str(source))
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    require(not target.exists(),'Input destination already exists')
    shutil.copyfile(source,target)
    return pin(target)


def _engine(context):
    if '_selected_engine' in context:return context['_selected_engine']
    path=Path(context['shared_source_root'])/'tools/fixture_engine_prepare.py'
    spec=importlib.util.spec_from_file_location('_selected_fixture_engine_prepare',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    identity=module.engine_identity(Path(context['shared_source_root']),game_dir=Path(context['game_dir']),
                                   steam_manifest=Path(context['case_inputs']['steam_manifest']) if context['case_inputs'].get('steam_manifest') else None)
    game=context['shared_game']
    require(identity['game_version']==game['version'] and identity['exe_sha256'].lower()==game['exe_sha256'].lower(),
            'Preparation game differs from the one selected shared runtime')
    # Existing emitters keep their repo/output API; the only identity provider is
    # this selected common module, not their legacy script-directory allowlist.
    module.engine_identity=lambda repo, **kwargs:dict(identity)
    context['_selected_engine']=(module,identity)
    return module,identity


def invoke_fixture_prepare(context,script,arguments):
    module,identity=_engine(context)
    previous=sys.modules.get('fixture_engine_prepare')
    original_argv=sys.argv
    sys.modules['fixture_engine_prepare']=module
    sys.argv=[str(script),*map(str,arguments)]
    output=Path(context['output']);output.mkdir(parents=True,exist_ok=True)
    try:
        with (output/'fixture-emitter.stdout.log').open('x',encoding='utf-8') as stdout, (output/'fixture-emitter.stderr.log').open('x',encoding='utf-8') as stderr:
            with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
                try:runpy.run_path(str(script),run_name='__main__')
                except SystemExit as error:
                    require(error.code in (None,0),'Original fixture emitter failed; no replay')
    finally:
        sys.argv=original_argv
        if previous is None:sys.modules.pop('fixture_engine_prepare',None)
        else:sys.modules['fixture_engine_prepare']=previous
    return {'engine_identity':identity,'emitter':pin(script),'arguments':list(map(str,arguments)),
            'game_started':False,'business_acceptance':'NOT_ASSESSED'}


def _outer_from_inner(inner,target):
    text=Path(inner).read_text(encoding='utf-8-sig')
    text=re.sub(r'^\s*(?:path|remote_file_id)\s*=.*\n?', '', text, flags=re.MULTILINE)
    return text.rstrip()+'\npath="'+Path(target).as_posix()+'"\n'


def _finish(context,profile,provenance):
    _,identity=_engine(context)
    rows={p.relative_to(profile).as_posix():pin(p) for p in sorted(profile.rglob('*')) if p.is_file()}
    preparation=Path(context['output'])/'profile-preparation.json'
    receipt={'schema':'ck3-mod-acceptance-prepared-fixture-v1','runtime_status':'NOT_RUN',
             'state_dir':str(profile.parent),'profile_dir':str(profile),**identity,
             'files':rows,'provenance':provenance,'business_acceptance':'NOT_ASSESSED'}
    write_json(preparation,receipt)
    write_json(profile.parent/'preparation.json',{'schema':'ck3-mod-acceptance-profile-startup-evidence-v1',
        'profile_dir':str(profile.resolve()),'profile_files':list(rows),
        'profile_input_sha256':{relative:row['sha256'] for relative,row in rows.items()},
        'preparation':pin(preparation),'runtime_status':'NOT_RUN'})
    contract=context['case_contract']
    policy={'schema':'ck3-frontend-fixture-start-policy-v1','schema_version':1,
            'preparation':{'path':str(preparation.resolve()),'sha256':pin(preparation)['sha256']},
            'profile_input_sha256':{relative:row['sha256'] for relative,row in rows.items()},
            'post_start':contract['post_start'],
            'required_log_markers':contract['required_startup'],
            'forbidden_log_markers':contract['forbidden_startup']}
    policy_path=Path(context['output'])/'frontend-fixture-start-policy.json'
    write_json(policy_path,policy)
    return {'state_dir':str(profile.parent),'profile':str(profile),'preparation':pin(preparation),
            'fixture_start_policy':pin(policy_path),'files':rows,'runtime_status':'NOT_RUN'}


def materialize_fixture_profile(context,fixture_dir,product_dir,plain_configuration):
    state=Path(context['state_dir']).resolve();profile=state/'profile'
    require(not profile.exists(),'New unused fixture profile required')
    require(set(plain_configuration)==set(CONFIG_NAMES),'Exactly four original plain configuration files required')
    profile.mkdir(parents=True)
    for relative,row in plain_configuration.items():checked_copy(row,profile/relative)
    for name,directory in (('fixture',Path(fixture_dir)),('product',Path(product_dir))):
        require((directory/'descriptor.mod').is_file(),'Original '+name+' descriptor is missing')
        target=profile/'mod-content'/name
        shutil.copytree(directory,target)
        outer=profile/'mod'/ (name+'.mod');outer.parent.mkdir(exist_ok=True)
        with outer.open('x',encoding='utf-8',newline='\n') as stream:stream.write(_outer_from_inner(target/'descriptor.mod',target))
    write_json(profile/'dlc_load.json',{'enabled_mods':['mod/product.mod','mod/fixture.mod'],'disabled_dlcs':[]})
    return _finish(context,profile,{'kind':'case-emitter-and-exact-formal-staging','fixture':str(fixture_dir),'product':str(product_dir)})


def restore_prepared_profile(context,beforelaunch_inventory):
    inventory=json.loads(Path(beforelaunch_inventory).read_text(encoding='utf-8-sig'))
    require(inventory.get('snapshot_kind')=='before-launch','Only a frozen before-launch profile may seed a retry')
    root=Path(inventory['snapshot_root']).resolve();rows=inventory['files']
    state=Path(context['state_dir']).resolve();profile=state/'profile'
    require(not profile.exists(),'New unused profile required; played state cannot be reused')
    profile.mkdir(parents=True)
    changed=[]
    for relative,row in rows.items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,'Input path must remain below profile')
        source=(root/relative).resolve();require(source.is_relative_to(root),'Snapshot path escaped')
        checked_copy({'path':str(source),**{key:row[key] for key in ('bytes','sha256')}},profile/relative)
        if relative in ('mod/fixture.mod','mod/product.mod'):
            target=profile/'mod-content'/Path(relative).stem
            old=(profile/relative).read_bytes()
            pattern=rb'^path\s*=.*$'
            matches=list(re.finditer(pattern,old,flags=re.MULTILINE))
            require(len(matches)==1,'Original outer descriptor must have one path')
            ending=b'\r' if matches[0].group().endswith(b'\r') else b''
            replacement=b'path="'+target.as_posix().encode('utf-8')+b'"'+ending
            new=old[:matches[0].start()]+replacement+old[matches[0].end():]
            (profile/relative).write_bytes(new);changed.append(relative)
    require(changed==['mod/fixture.mod','mod/product.mod'] or set(changed)=={'mod/fixture.mod','mod/product.mod'},'Only two outer paths may change')
    return _finish(context,profile,{'kind':'before-launch-exact-restore','inventory':pin(beforelaunch_inventory),
                                    'source_run_id':inventory['source_run_id'],'file_count':len(rows),
                                    'byte_exact_count':len(rows)-2,'changed_outer_paths':changed})


def materialize_product_profile(context,product_dir,plain_configuration,*,workshop_cache_files=None):
    state=Path(context['state_dir']).resolve();profile=state/'profile'
    require(not profile.exists(),'New product-only profile required')
    require(set(plain_configuration)==set(CONFIG_NAMES),'Exactly four plain configurations required')
    profile.mkdir(parents=True)
    for relative,row in plain_configuration.items():checked_copy(row,profile/relative)
    product_dir=Path(product_dir).resolve();target=profile/'mod-content/product'
    require((product_dir/'descriptor.mod').is_file(),'Exact formal product descriptor required')
    if workshop_cache_files is None:
        shutil.copytree(product_dir,target)
    else:
        require(workshop_cache_files,'Exact external Workshop cache inventory required')
        target=product_dir
    outer=profile/'mod/product.mod';outer.parent.mkdir()
    text=_outer_from_inner(target/'descriptor.mod',target)
    if workshop_cache_files is not None:
        item=context['workshop_cache_item_id']
        require(re.fullmatch(r'[1-9][0-9]*',item),'Canonical cache item ID required')
        text+='remote_file_id="'+item+'"\n'
    with outer.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
    write_json(profile/'dlc_load.json',{'enabled_mods':['mod/product.mod'],'disabled_dlcs':[]})
    products=([pin(outer),*workshop_cache_files] if workshop_cache_files is not None else
              [pin(p) for p in [outer,*sorted(p for p in target.rglob('*') if p.is_file())]])
    inventory={'schema':('ck3-workshop-cache-product-only-profile-v1' if workshop_cache_files is not None else
                         'ck3-saved-campaign-product-only-profile-v1'),'profile_path':str(profile.resolve()),
               'enabled_mods':['mod/product.mod'],'product_files':products}
    path=Path(context['output'])/'saved-product-inventory.json';write_json(path,inventory)
    rows={p.relative_to(profile).as_posix():pin(p) for p in sorted(profile.rglob('*')) if p.is_file()}
    return {'state_dir':str(state),'profile':str(profile),'product_inventory':pin(path),'files':rows,
            'product_file_count':len(products),'runtime_status':'NOT_RUN','fixture_mounted':False}
