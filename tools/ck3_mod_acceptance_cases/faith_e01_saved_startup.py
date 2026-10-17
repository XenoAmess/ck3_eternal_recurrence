"""Pure proof for the approved F save's pending preparation event.

The shared host binds this process's actual event instance before calling us.
No native query, option selection, preparation or game mutation is performed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

EVENT_KEY='xar_faith_h01_prepare.1'
SOURCE_FILES={
    'descriptor.mod':'74047ddd40b7b4293b136a2da4d8a9aa589ba575d47615063e70d29cd97a37bd',
    'events/xar_faith_h01_prepare_events.txt':'b60af0ae7bd2e1904eae86bc5cd7e3a525ec7ca9ce2487e89eae3cfa5278f872',
    'localization/english/xar_faith_h01_l_english.yml':'eb2cae39babefb6d1ea681dcb64910f5078fc0b851647265b477f4fce5c333f7',
    'localization/simp_chinese/xar_faith_h01_l_simp_chinese.yml':'f76bbf33d928f7ba95868140d836f2ee8c8ecf97617acdcf12ed1a59b1802a68',
}


def qualify_prepare_event_from_save(context,snapshot,event_packet):
    expected=context['expected']
    native=event_packet.get('current_event_window_context',{})
    actual=snapshot.get('active_event') or {}
    actor=(snapshot.get('played_character') or {}).get('character_id')
    identity=(native.get('root_scope') or {}).get('typed_identity') or {}
    if (expected['event_definition_key']!=EVENT_KEY or expected['date_raw']!=51394920
            or expected['native_option_indices']!=[0,1]
            or type(expected['event_instance_id']) is not int or expected['event_instance_id']<1
            or actor!=expected['actor_character_id'] or identity.get('character_id')!=expected['root_character_id']
            or native.get('event_definition_key')!=EVENT_KEY
            or native.get('current_event_instance_id')!=expected['event_instance_id']
            or actual.get('instance_id')!=expected['event_instance_id']
            or snapshot.get('date_raw')!=expected['date_raw']):
        raise ValueError('saved F preparation proof crossed its actual bound event/player/date')
    product=Path(context['state_dir'])/'profile/mod-content/product'
    observed={path.relative_to(product).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
        for path in product.rglob('*') if path.is_file()}
    if observed!=SOURCE_FILES:
        raise ValueError('saved F requires exactly the original four event-only source files; no startup registrar')
    return {**expected,'proof':{'source_files_sha256':dict(SOURCE_FILES),
        'event_only_projection':True,'cold_start_registrar_mounted':False,
        'preparation_or_selection_performed':False,'runtime_event_instance_bound_by_shared_host':True,
        'history_id_is_not_a_runtime_fullref':True},'business_pass':False}
