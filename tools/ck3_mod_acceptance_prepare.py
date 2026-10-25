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
from datetime import datetime
from dataclasses import dataclass
from typing import Literal, TypedDict

from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field

CONFIG_NAMES = ('pdx_settings.txt','tutorial.txt','presets.txt','player/game_rules/presets.txt')


@dataclass(frozen=True)
class CompatibilityMod:
    """One independent, source-manifest-bound formal mod above the product."""
    key: str
    directory: Path
    source_manifest: FilePin
    files: dict[str, FilePin]

    @property
    def mount_name(self) -> str:
        return 'compat_' + self.key


def _compatibility_checked_pin(value: object) -> FilePin:
    row = json_object(value)
    if set(row) != {'path', 'bytes', 'sha256'}:
        raise ValueError('Compatibility mod requires exact FilePin fields')
    expected = file_pin(row)
    path = Path(expected['path'])
    if (not path.is_absolute() or str(path.resolve()) != expected['path']
            or path.is_symlink() or path.is_junction() or not path.is_file()):
        raise ValueError('Compatibility file must be an absolute canonical ordinary file')
    if pin(path) != expected:
        raise ValueError('Compatibility frozen file changed: ' + expected['path'])
    return expected


def compatibility_mods(case_inputs: object) -> tuple[CompatibilityMod, ...]:
    """Validate the single optional JSON contract before prepare AND allocation.

    Missing means the historic product/fixture pair; null is never an empty list.
    Release manifests may spell their integral length ``bytes`` or ``size``;
    their exact file list must equal every separately pinned source payload.
    """
    inputs = json_object(case_inputs)
    if 'compatibility_mods' not in inputs:
        return ()
    values = inputs['compatibility_mods']
    if not isinstance(values, list) or len(values) > 16:
        raise ValueError('compatibility_mods must be an explicit bounded array, not null')
    result: list[CompatibilityMod] = []
    keys: set[str] = set()
    manifests: set[str] = set()
    roots: list[Path] = []
    for value in values:
        row = json_object(value)
        if set(row) != {'key', 'directory', 'source_manifest', 'files'}:
            raise ValueError('Compatibility mod fields differ')
        key = text_field(row, 'key')
        if (re.fullmatch('[a-z][a-z0-9_]{0,47}', key) is None
                or key in {'product', 'fixture'} or key in keys):
            raise ValueError('Compatibility mod key must be safe, canonical and unique')
        keys.add(key)
        directory = text_field(row, 'directory')
        root = Path(directory)
        if (not root.is_absolute() or str(root.resolve()) != directory
                or not root.is_dir() or root.is_symlink() or root.is_junction()
                or any(root.is_relative_to(other) or other.is_relative_to(root) for other in roots)):
            raise ValueError('Compatibility mod requires disjoint canonical ordinary directories')
        roots.append(root)
        if file_pin(row['source_manifest'])['bytes'] > 2 * 1024 * 1024:
            raise ValueError('Compatibility source manifest exceeds its bounded size')
        source_manifest = _compatibility_checked_pin(row['source_manifest'])
        if source_manifest['path'] in manifests:
            raise ValueError('Compatibility source manifest paths repeat')
        manifests.add(source_manifest['path'])
        if source_manifest['bytes'] > 2 * 1024 * 1024 or Path(source_manifest['path']).is_relative_to(root):
            raise ValueError('Compatibility source manifest must be bounded and outside payload')
        manifest = json_object(json.loads(Path(source_manifest['path']).read_text(encoding='utf-8-sig')))
        declared_values = manifest.get('files')
        if not isinstance(declared_values, list) or not 1 <= len(declared_values) <= 4096:
            raise ValueError('Compatibility source manifest requires its exact bounded files array')
        manifest_files: dict[str, FilePin] = {}
        for declared_value in declared_values:
            declared = json_object(declared_value)
            if set(declared) not in ({'path', 'bytes', 'sha256'}, {'path', 'size', 'sha256'}):
                raise ValueError('Compatibility release manifest file fields differ')
            relative = text_field(declared, 'path')
            path = root / _prebuilt_relative_path(relative)
            if relative.casefold() in {name.casefold() for name in manifest_files}:
                raise ValueError('Compatibility release manifest paths repeat')
            manifest_files[relative] = file_pin({'path': str(path),
                'bytes': declared['bytes'] if 'bytes' in declared else declared['size'], 'sha256': declared['sha256']})
        file_values = object_field(row, 'files')
        if set(file_values) != set(manifest_files) or 'descriptor.mod' not in file_values:
            raise ValueError('Compatibility source manifest and payload closure differ')
        files: dict[str, FilePin] = {}
        for relative, file_value in file_values.items():
            _prebuilt_relative_path(relative)
            expected = _compatibility_checked_pin(file_value)
            if expected != manifest_files[relative]:
                raise ValueError('Compatibility file pin differs from its release manifest')
            files[relative] = expected
        actual: set[str] = set()
        for path in root.rglob('*'):
            if path.is_symlink() or path.is_junction():
                raise ValueError('Compatibility mod cannot follow filesystem links')
            if path.is_file():
                actual.add(path.relative_to(root).as_posix())
        if actual != set(files):
            raise ValueError('Compatibility actual payload closure differs')
        result.append(CompatibilityMod(key, root, source_manifest, files))
    return tuple(result)


def compatibility_mod_source_pins(case_inputs: object) -> list[FilePin]:
    """Original provenance and payload pins consumed by public preflight freeze."""
    references: list[FilePin] = []
    for mod in compatibility_mods(case_inputs):
        references.append(mod.source_manifest)
        references.extend(mod.files.values())
    if len({row['path'] for row in references}) != len(references):
        raise ValueError('Compatibility source pin paths repeat across mods')
    return references


def compatibility_mods_json(mods: tuple[CompatibilityMod, ...]) -> list[JsonObject]:
    return [json_object({'key': mod.key, 'directory': str(mod.directory),
                        'source_manifest': mod.source_manifest, 'files': mod.files}) for mod in mods]


def fixture_enabled_mods(profile: Path) -> list[str]:
    """Read only the exact independent mounts, never a directory wildcard."""
    row = json_object(json.loads((profile / 'dlc_load.json').read_text(encoding='utf-8-sig')))
    values = row.get('enabled_mods')
    if not isinstance(values, list) or not values or len(values) > 18:
        raise ValueError('Explicit bounded fixture enabled_mods required')
    enabled: list[str] = []
    for value in values:
        if (not isinstance(value, str) or value in enabled
                or re.fullmatch(r'mod/(?:product|fixture|compat_[a-z][a-z0-9_]{0,47})\.mod', value) is None):
            raise ValueError('Fixture enabled descriptor is unsafe or repeated')
        enabled.append(value)
    if enabled[-1] != 'mod/fixture.mod' or ('mod/product.mod' in enabled and enabled[-2:] != ['mod/product.mod', 'mod/fixture.mod']):
        raise ValueError('Independent compatibility mods must precede product and fixture')
    if len(enabled) > 1 and 'mod/product.mod' not in enabled:
        raise ValueError('Compatibility mods require an actual formal product')
    return enabled


class PrebuiltFixtureReceipt(TypedDict):
    required_markers: list[str]
    required_product_markers_minimum: dict[str, int]
    fixture_contains_business_effects: bool


class PrebuiltFixtureMaterialization(TypedDict):
    manifest: FilePin
    producer_source_pins: list[FilePin]
    machine_id: str
    observed_at_utc: str
    game_started: Literal[False]
    business_acceptance: Literal['NOT_ASSESSED']


def _prebuilt_checked_pin(value: object) -> FilePin:
    row = json_object(value)
    if set(row) != {'path', 'bytes', 'sha256'}:
        raise ValueError('Prebuilt fixture file pin fields differ')
    expected = file_pin(row)
    actual = pin(expected['path'])
    if actual != expected:
        raise ValueError('Prebuilt fixture frozen file changed: ' + expected['path'])
    return expected


def _prebuilt_relative_path(value: str) -> Path:
    if (not value or '\\' in value or ':' in value or value.startswith('/')
            or any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError('Prebuilt fixture requires a canonical relative file path')
    return Path(*value.split('/'))


def materialize_prebuilt_fixture(
    context: JsonObject, manifest_value: object, destination: Path,
) -> tuple[Path, PrebuiltFixtureReceipt, PrebuiltFixtureMaterialization]:
    """Import an exact pre-generated fixture without running another interpreter.

    The producer may be Java or another existing non-Python build tool. Its
    immutable manifest, complete file closure and source pins are validated
    before copying; the ordinary shared profile builder remains authoritative.
    """
    manifest_pin = _prebuilt_checked_pin(manifest_value)
    row = json_object(json.loads(Path(manifest_pin['path']).read_text(encoding='utf-8-sig')))
    fields = {'schema', 'product', 'case_id', 'machine_id', 'observed_at_utc',
              'fixture_root', 'producer_source_pins', 'files', 'receipt'}
    if (set(row) != fields or row.get('schema') != 'ck3-mod-acceptance-prebuilt-fixture-v1'
            or row.get('product') != context.get('product') or row.get('case_id') != context.get('case')):
        raise ValueError('Prebuilt fixture crossed product/case/schema')
    shared_pin = _prebuilt_checked_pin(context.get('runtime_manifest'))
    shared = json_object(json.loads(Path(shared_pin['path']).read_text(encoding='utf-8-sig')))
    machine = text_field(row, 'machine_id')
    if machine != shared.get('machine_id'):
        raise ValueError('Prebuilt fixture belongs to another execution machine')
    stamp = text_field(row, 'observed_at_utc')
    if datetime.fromisoformat(stamp.replace('Z', '+00:00')).utcoffset() is None:
        raise ValueError('Prebuilt fixture timestamp needs an explicit timezone')
    source_values = row.get('producer_source_pins')
    if not isinstance(source_values, list) or not 1 <= len(source_values) <= 64:
        raise ValueError('Prebuilt fixture producer source pins required')
    source_pins = [_prebuilt_checked_pin(value) for value in source_values]
    if len({value['path'] for value in source_pins}) != len(source_pins):
        raise ValueError('Prebuilt fixture producer source pins repeat')
    repo = Path(text_field(context, 'repo_root')).resolve()
    if any(not Path(value['path']).resolve().is_relative_to(repo) for value in source_pins):
        raise ValueError('Prebuilt fixture producer is outside the selected repository')
    root_value = text_field(row, 'fixture_root')
    if not Path(root_value).is_absolute():
        raise ValueError('Prebuilt fixture root must be absolute')
    source_root = Path(root_value)
    root = source_root.resolve()
    if not root.is_dir() or source_root.is_symlink() or source_root.is_junction():
        raise ValueError('Prebuilt fixture requires an ordinary directory')
    files = object_field(row, 'files')
    if not files or len(files) > 1024 or 'descriptor.mod' not in files:
        raise ValueError('Prebuilt fixture needs its complete bounded file closure')
    declared: dict[str, FilePin] = {}
    for relative, value in files.items():
        path = root / _prebuilt_relative_path(relative)
        expected = json_object(value)
        if set(expected) != {'bytes', 'sha256'}:
            raise ValueError('Prebuilt fixture inventory fields differ')
        declared[relative] = file_pin({'path': str(path), **expected})
    actual_paths: set[str] = set()
    for path in root.rglob('*'):
        if path.is_symlink() or path.is_junction():
            raise ValueError('Prebuilt fixture cannot follow filesystem links')
        if path.is_file():
            actual_paths.add(path.relative_to(root).as_posix())
    if actual_paths != set(declared):
        raise ValueError('Prebuilt fixture inventory differs from actual files')
    for expected_pin in declared.values():
        _prebuilt_checked_pin(expected_pin)
    receipt_row = object_field(row, 'receipt')
    if set(receipt_row) != {'required_markers', 'required_product_markers_minimum', 'fixture_contains_business_effects'}:
        raise ValueError('Prebuilt fixture receipt fields differ')
    marker_values = receipt_row.get('required_markers')
    if (not isinstance(marker_values, list) or not marker_values
            or any(not isinstance(value, str) or not value for value in marker_values)):
        raise ValueError('Prebuilt fixture requires actual assertion marker names')
    markers = [value for value in marker_values if isinstance(value, str)]
    if len(set(markers)) != len(markers):
        raise ValueError('Prebuilt fixture assertion markers repeat')
    minima: dict[str, int] = {}
    for key, value in object_field(receipt_row, 'required_product_markers_minimum').items():
        if type(value) is not int or not isinstance(value, int) or value <= 0:
            raise ValueError('Prebuilt fixture marker minima must be positive integers')
        minima[key] = value
    business_effects = receipt_row.get('fixture_contains_business_effects')
    if type(business_effects) is not bool or not isinstance(business_effects, bool):
        raise ValueError('Prebuilt fixture business-effect flag must be Boolean')
    receipt = PrebuiltFixtureReceipt(required_markers=markers,
        required_product_markers_minimum=minima, fixture_contains_business_effects=business_effects)
    if destination.exists() or destination.is_symlink() or destination.is_junction():
        raise ValueError('Unused prebuilt fixture destination required')
    destination.mkdir(parents=True)
    for relative, expected_pin in declared.items():
        target = destination / _prebuilt_relative_path(relative)
        copied = checked_copy(expected_pin, target)
        if copied['bytes'] != expected_pin['bytes'] or copied['sha256'] != expected_pin['sha256']:
            raise ValueError('Prebuilt fixture copy differs from its frozen inventory')
    materialized = PrebuiltFixtureMaterialization(manifest=manifest_pin,
        producer_source_pins=source_pins, machine_id=machine, observed_at_utc=stamp,
        game_started=False, business_acceptance='NOT_ASSESSED')
    return destination, receipt, materialized


def require(value: object, message: str) -> None:
    if not value: raise ValueError(message)


def pin(path: str | Path) -> FilePin:
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')


def checked_copy(row: FilePin, target: str | Path) -> FilePin:
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
    scenario=contract.get('frontend_scenario')
    if scenario is not None:
        require(isinstance(scenario,dict) and set(scenario)=={
            'profile_id','frontend_target','startup_event_admission'},
            'Explicit fixture scenario requires its exact declared target and startup event admission')
        policy.update(schema='ck3-frontend-fixture-start-policy-v2',schema_version=2,**scenario)
    policy_path=Path(context['output'])/'frontend-fixture-start-policy.json'
    write_json(policy_path,policy)
    return {'state_dir':str(profile.parent),'profile':str(profile),'preparation':pin(preparation),
            'fixture_start_policy':pin(policy_path),'files':rows,'runtime_status':'NOT_RUN'}


def materialize_fixture_profile(context: JsonObject, fixture_dir: str | Path,
                                product_dir: str | Path | None, plain_configuration: object, *,
                                compatibility: tuple[CompatibilityMod, ...] = ()) -> JsonObject:
    state=Path(text_field(context, 'state_dir')).resolve();profile=state/'profile'
    require(not profile.exists(),'New unused fixture profile required')
    plain = json_object(plain_configuration)
    require(set(plain)==set(CONFIG_NAMES),'Exactly four original plain configuration files required')
    require(not compatibility or product_dir is not None, 'Compatibility fixtures require the actual product')
    # Re-enter the same validated contract immediately before filesystem writes.
    compatibility = compatibility_mods({'compatibility_mods': compatibility_mods_json(compatibility)})
    if product_dir is not None:
        product_root = Path(product_dir).resolve()
        fixture_root = Path(fixture_dir).resolve()
        require(all(not (mod.directory.is_relative_to(root) or root.is_relative_to(mod.directory))
                    for mod in compatibility for root in (product_root, fixture_root)),
                'Compatibility roots must remain independent of product and fixture')
    profile.mkdir(parents=True)
    for relative,row in plain.items():checked_copy(file_pin(row),profile/relative)
    directories=[('fixture',Path(fixture_dir))]
    if product_dir is not None:
        directories.append(('product',Path(product_dir)))
    for name,directory in directories:
        require((directory/'descriptor.mod').is_file(),'Original '+name+' descriptor is missing')
        target=profile/'mod-content'/name
        shutil.copytree(directory,target)
        outer=profile/'mod'/ (name+'.mod');outer.parent.mkdir(exist_ok=True)
        with outer.open('x',encoding='utf-8',newline='\n') as stream:stream.write(_outer_from_inner(target/'descriptor.mod',target))
    for mod in compatibility:
        target = profile / 'mod-content' / mod.mount_name
        for relative, expected in mod.files.items():
            copied = checked_copy(expected, target / _prebuilt_relative_path(relative))
            require(copied['bytes'] == expected['bytes'] and copied['sha256'] == expected['sha256'],
                    'Compatibility copied payload differs')
        outer = profile / 'mod' / (mod.mount_name + '.mod')
        with outer.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(_outer_from_inner(target / 'descriptor.mod', target))
    enabled_mods = ['mod/' + mod.mount_name + '.mod' for mod in compatibility]
    enabled_mods += (['mod/product.mod','mod/fixture.mod'] if product_dir is not None else ['mod/fixture.mod'])
    write_json(profile/'dlc_load.json',{'enabled_mods':enabled_mods,'disabled_dlcs':[]})
    provenance: JsonObject = ({'kind':'case-emitter-and-exact-formal-staging','fixture':str(fixture_dir),'product':str(product_dir)}
                if product_dir is not None else {'kind':'standalone-mechanism-fixture','fixture':str(fixture_dir),'product':None})
    if compatibility:
        provenance = json_object({**provenance, 'compatibility_mods': compatibility_mods_json(compatibility)})
    return json_object({**_finish(context,profile,provenance), 'enabled_mods': enabled_mods})


def restore_prepared_profile(context: JsonObject, beforelaunch_inventory: str | Path) -> JsonObject:
    inventory=json_object(json.loads(Path(beforelaunch_inventory).read_text(encoding='utf-8-sig')))
    require(inventory.get('snapshot_kind')=='before-launch','Only a frozen before-launch profile may seed a retry')
    root=Path(text_field(inventory, 'snapshot_root')).resolve();rows=object_field(inventory, 'files')
    require('dlc_load.json' in rows, 'Frozen enabled_mods inventory is missing')
    frozen_load = file_pin({'path': str(root / 'dlc_load.json'), **json_object(rows['dlc_load.json'])})
    require(pin(root / 'dlc_load.json') == frozen_load, 'Frozen enabled_mods changed')
    enabled = fixture_enabled_mods(root)
    require({relative for relative in rows if relative.startswith('mod/')} == set(enabled),
            'Only declared outer descriptor files may be restored')
    for outer in enabled:
        require('mod-content/' + Path(outer).stem + '/descriptor.mod' in rows,
                'Declared independent mod content descriptor is missing')
    state=Path(text_field(context, 'state_dir')).resolve();profile=state/'profile'
    require(not profile.exists(),'New unused profile required; played state cannot be reused')
    profile.mkdir(parents=True)
    changed=[]
    for relative,row in rows.items():
        _prebuilt_relative_path(relative)
        row = json_object(row)
        source=(root/relative).resolve();require(source.is_relative_to(root),'Snapshot path escaped')
        checked_copy(file_pin({'path':str(source),'bytes':row['bytes'],'sha256':row['sha256']}),profile/relative)
        if relative in enabled:
            target=profile/'mod-content'/Path(relative).stem
            old=(profile/relative).read_bytes()
            pattern=rb'^path\s*=.*$'
            matches=list(re.finditer(pattern,old,flags=re.MULTILINE))
            require(len(matches)==1,'Original outer descriptor must have one path')
            ending=b'\r' if matches[0].group().endswith(b'\r') else b''
            replacement=b'path="'+target.as_posix().encode('utf-8')+b'"'+ending
            new=old[:matches[0].start()]+replacement+old[matches[0].end():]
            (profile/relative).write_bytes(new);changed.append(relative)
    require(set(changed) == set(enabled), 'Only explicitly declared outer paths may change')
    return json_object(_finish(context,profile,{'kind':'before-launch-exact-restore','inventory':pin(beforelaunch_inventory),
                                    'source_run_id':inventory['source_run_id'],'file_count':len(rows),
                                    'byte_exact_count':len(rows)-len(enabled),'changed_outer_paths':changed}))


def materialize_product_profile(context,product_dir,plain_configuration,*,workshop_cache_files=None):
    state=Path(context['state_dir']).resolve();profile=state/'profile'
    require(not profile.exists(),'New product-only profile required')
    require(set(plain_configuration)==set(CONFIG_NAMES),'Exactly four plain configurations required')
    profile.mkdir(parents=True)
    for relative,row in plain_configuration.items():checked_copy(row,profile/relative)
    if product_dir is None:
        require(workshop_cache_files is None,'A vanilla saved campaign cannot declare Workshop product files')
        write_json(profile/'dlc_load.json',{'enabled_mods':[],'disabled_dlcs':[]})
        inventory=json_object({'schema':'ck3-saved-campaign-vanilla-profile-v1','profile_path':str(profile.resolve()),
                   'enabled_mods':[],'product_files':[]})
        path=Path(context['output'])/'saved-product-inventory.json';write_json(path,inventory)
        rows={p.relative_to(profile).as_posix():pin(p) for p in sorted(profile.rglob('*')) if p.is_file()}
        return {'state_dir':str(state),'profile':str(profile),'product_inventory':pin(path),'files':rows,
                'product_file_count':0,'runtime_status':'NOT_RUN','fixture_mounted':False,'vanilla_profile':True}
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
    inventory=json_object({'schema':('ck3-workshop-cache-product-only-profile-v1' if workshop_cache_files is not None else
                         'ck3-saved-campaign-product-only-profile-v1'),'profile_path':str(profile.resolve()),
               'enabled_mods':['mod/product.mod'],'product_files':products})
    path=Path(context['output'])/'saved-product-inventory.json';write_json(path,inventory)
    rows={p.relative_to(profile).as_posix():pin(p) for p in sorted(profile.rglob('*')) if p.is_file()}
    return {'state_dir':str(state),'profile':str(profile),'product_inventory':pin(path),'files':rows,
            'product_file_count':len(products),'runtime_status':'NOT_RUN','fixture_mounted':False}


def finish_product_profile(context,profile,*,provenance=None):
    """Bind an actual product-only profile to the selected engine and startup.

    Call after materialize_product_profile and product-specific byte checks.
    This emits no fixture policy, save, game process or launch authority.
    """
    state=Path(context['state_dir']).resolve();userdir=state/'profile'
    require(Path(profile['state_dir']).resolve()==state and
            Path(profile['profile']).resolve()==userdir and profile.get('fixture_mounted') is False,
            'Product preparation must identify the actual product-only profile')
    _,identity=_engine(context)
    rows={p.relative_to(userdir).as_posix():pin(p) for p in sorted(userdir.rglob('*')) if p.is_file()}
    require(rows and rows==profile['files'],'Materialized product profile files changed before preparation')
    inventory=profile['product_inventory'];actual_inventory=pin(inventory['path'])
    require(all(actual_inventory[k]==inventory[k] for k in ('bytes','sha256')),
            'Product inventory changed before preparation')
    preparation=Path(context['output'])/'profile-preparation.json'
    receipt={'schema':'ck3-mod-acceptance-prepared-product-v1','runtime_status':'NOT_RUN',
             'state_dir':str(state),'profile_dir':str(userdir),**identity,
             'files':rows,'product_inventory':actual_inventory,'fixture_mounted':False,
             'provenance':provenance or {},'business_acceptance':'NOT_ASSESSED'}
    write_json(preparation,receipt)
    write_json(state/'preparation.json',{'schema':'ck3-mod-acceptance-profile-startup-evidence-v1',
        'profile_dir':str(userdir),'profile_files':list(rows),
        'profile_input_sha256':{relative:row['sha256'] for relative,row in rows.items()},
        'preparation':pin(preparation),'runtime_status':'NOT_RUN'})
    return {**profile,'preparation':pin(preparation)}
