"""Current Character/commander/knight roles remain separate from physical DATA.

Source candidate for a same-query strengths leaf, not a historical birth probe.
Callers retain and bind each query's own frame/lifecycle before joining inputs.
"""
from __future__ import annotations

from collections.abc import Mapping


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


_IDS = ('army_regiment_id', 'native_carmy_id', 'arrg_army_id_140',
        'character_raw_id_148', 'resolved_character_id',
        'extension_army_id_f4', 'extension_arrg_id_f8')
_BOOLS = ('resolution_used_fallback', 'native_character_predicate',
          'character_extension_present')
_FIELDS = {'source', 'status', *_IDS, 'character_magic_1c', *_BOOLS,
           'same_ArRg_instance_after', 'unavailable_reason'}


def normalize_regiment_character_role_v1(value: object, *, army_regiment_id: int,
                                        loss_writer_skipped: bool | None) -> dict[str, object]:
    """Validate the literal native strengths leaf, preserving partial/null fields."""
    _need(isinstance(value, dict) and set(value) == _FIELDS, 'Character role schema differs')
    row = dict(value)
    _need(row['source'] == 'native_selected_ArRg_character_role_raw', 'Character role source differs')
    _need(row['status'] in ('available', 'partial', 'unavailable'), 'Character role status invalid')
    for name in _IDS:
        item = row[name]
        _need(item is None or type(item) is int and -(2**31) <= item < 2**31,
              'Character role identity must be int32/null')
    _need(row['army_regiment_id'] == army_regiment_id and army_regiment_id != -1
          and type(row['native_carmy_id']) is int and row['native_carmy_id'] != -1,
          'Character role parent identity differs')
    magic = row['character_magic_1c']
    _need(magic is None or type(magic) is int and 0 <= magic < 2**32, 'Character magic invalid')
    for name in _BOOLS:
        _need(row[name] is None or type(row[name]) is bool, 'Character role predicate must remain bool/null')
    _need(type(row['same_ArRg_instance_after']) is bool, 'Character role readback must be bool')
    predicate = row['native_character_predicate']
    if predicate is not None and loss_writer_skipped is not None:
        _need(predicate == loss_writer_skipped, 'same-query Character predicates disagree')
    if predicate is True:
        _need(magic == 0x43686172 and row['resolved_character_id'] not in (None, -1)
              and type(row['resolution_used_fallback']) is bool,
              'true Character predicate lacks resolved native identity')
    if row['resolution_used_fallback'] is False:
        _need(row['resolved_character_id'] == row['character_raw_id_148'],
              'direct Character generation differs')
    if row['character_extension_present'] is False:
        _need(row['extension_army_id_f4'] is None and row['extension_arrg_id_f8'] is None,
              'absent Character extension has values')
    if row['character_raw_id_148'] == -1:
        _need(predicate is False and row['resolved_character_id'] is None,
              'absent Character association invented a role')
    reason = row['unavailable_reason']
    if row['status'] == 'available':
        _need(reason is None and row['same_ArRg_instance_after'] is True
              and row['arrg_army_id_140'] == row['native_carmy_id']
              and row['character_raw_id_148'] is not None and type(predicate) is bool,
              'available Character role is incomplete')
        if predicate:
            _need(type(row['character_extension_present']) is bool,
                  'available Character extension presence unknown')
            if row['character_extension_present']:
                _need(row['extension_army_id_f4'] is not None and row['extension_arrg_id_f8'] is not None,
                      'available Character extension is incomplete')
    else:
        _need(isinstance(reason, str) and bool(reason), 'unavailable Character role requires reason')
    return row


def classify_current_regiment_character_role_12004(
    strength: Mapping[str, object], data: Mapping[str, object],
    link: Mapping[str, object], *, native_carmy_id: int,
    current_commander: Mapping[str, object],
    knights: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Consume already normalized same-frame observations without filling gaps.

    The raw native provider is army_regiment_character_role_12004.hpp. A complete
    combat Knights DTO supplies knight membership independently; a current ArRg
    F8 backlink alone supplies only an observed Character association.
    """
    identity = strength.get('army_regiment_id')
    _need(type(identity) is int and identity != -1, 'complete ArRg identity required')
    _need(strength.get('scale') == 1, 'ArRg scale must be 1')
    _need(data.get('army_regiment_id') == identity
          and link.get('army_regiment_id') == identity
          and link.get('native_carmy_id') == native_carmy_id,
          'Character/DATA/Army full-generation identities differ')
    _need(link.get('source') == 'native_selected_ArRg_character_role_raw',
          'current Character link source differs')
    _need(link.get('status') in ('available', 'partial', 'unavailable'), 'link status invalid')
    predicate = link.get('native_character_predicate')
    _need(predicate is None or type(predicate) is bool, 'Character predicate must remain bool/null')
    published = data.get('native_loss_writer_skipped')
    _need(published is None or type(published) is bool, 'DATA predicate must remain bool/null')
    if predicate is not None and published is not None:
        _need(predicate == published, 'independent same-query Character predicates disagree')
    linked_id = link.get('resolved_character_id') if predicate is True else None
    if predicate is True:
        _need(type(linked_id) is int and linked_id != -1, 'true Character predicate lacks its actual Character')
    if link.get('status') == 'available':
        _need(link.get('same_ArRg_instance_after') is True
              and link.get('arrg_army_id_140') == native_carmy_id,
              'available current link lost its full-generation Army association')
    commander_status = current_commander.get('status')
    _need(commander_status in ('available', 'absent', 'unavailable'), 'commander status invalid')
    commander_observable = commander_status in ('available', 'absent')
    commander_id = current_commander.get('character_id')
    if commander_status == 'available':
        _need(type(commander_id) is int and commander_id != -1, 'actual commander ID absent')
    elif commander_status == 'absent':
        _need(commander_id is None, 'absent commander has an invented ID')
    is_commander = (linked_id == commander_id if linked_id is not None and commander_observable else None)
    knight_member = None
    if knights is not None and knights.get('available') is True and linked_id is not None:
        members = knights.get('members')
        _need(isinstance(members, list), 'available Knight membership lacks its complete list')
        selected = [row for row in members if row.get('source_regiment_id') == identity]
        _need(len(selected) <= 1, 'duplicate native Knight ArRg membership')
        knight_member = False
        if selected:
            row = selected[0]
            _need(row.get('army_id') == native_carmy_id and row.get('character_id') == linked_id
                  and row.get('eligible') is True and row.get('participant_army_membership_verified') is True,
                  'native Knight member belongs to another Character or CArmy')
            knight_member = True
    return {'army_regiment_id': identity, 'linked_character_id': linked_id,
            'native_character_predicate': predicate,
            'current_commander_role_observable': commander_observable,
            'is_current_commander': is_commander,
            'native_knight_member': knight_member,
            'extension_commander_army_id_f4': link.get('extension_army_id_f4'),
            'extension_arrg_id_f8': link.get('extension_arrg_id_f8'),
            'observed_ArRg_backlink_matches': (link.get('extension_arrg_id_f8') == identity
                                              if link.get('extension_arrg_id_f8') is not None else None),
            'DATA_record_count': data.get('native_data_record_count'),
            'physical_refill_applied': None, 'birth_producer_observed': False,
            'current_input_status': link['status']}
