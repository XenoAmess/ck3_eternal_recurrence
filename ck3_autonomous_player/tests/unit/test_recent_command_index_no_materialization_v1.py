"""Nearest command lookup preserves indices without prewalking owned history."""
import copy

import pytest

from xar_autoplayer import strategy


def _row(command, *, ok=True, index=None, indexed=False, decorated=False):
    value = {'command': command, 'ok': ok}
    if indexed:
        value['index'] = index
    if decorated:
        value.update(command='auto-turn', result={'auto_turn': {'selected_step': command}})
    return value


@pytest.mark.parametrize('lookup', ['exact', 'life'])
@pytest.mark.parametrize('rows,success_only,expected', [
    ([], True, 0),
    ([_row('other'), _row('life-advance')], True, 2),
    ([_row('life-advance'), _row('other')], True, 1),
    ([_row('life-advance'), _row('life-advance', ok=False)], True, 1),
    ([_row('life-advance'), _row('life-advance', ok=False)], False, 2),
    ([_row('life-advance', index=79, indexed=True)], True, 79),
    ([_row('life-advance', index='79', indexed=True)], True, 1),
    ([_row('life-advance', index=True, indexed=True)], True, True),
    ([_row('life-advance', decorated=True)], True, 1),
    ([_row('other', decorated=True)], True, 0),
])
def test_recent_indices_keep_success_filter_decorated_steps_and_original_fallback(
    lookup, rows, success_only, expected,
):
    original = copy.deepcopy(rows)
    if lookup == 'exact':
        actual = strategy._latest_index(rows, 'life-advance', successful_only=success_only)
    else:
        actual = strategy._latest_life_advance_index(rows, successful_only=success_only)
    assert type(actual) is type(expected)
    assert actual == expected
    assert rows == original


class _OwnedHistory(list):
    def __init__(self, rows):
        super().__init__(rows)
        self.visited = []

    def __iter__(self):
        pytest.fail('Lookup prewalked/materialized the whole history')

    def __getitem__(self, position):
        self.visited.append(position)
        return super().__getitem__(position)


@pytest.mark.parametrize('lookup', ['exact', 'life'])
def test_tail_match_reads_only_the_last_owned_row(lookup):
    rows = _OwnedHistory([_row('other') for _ in range(12)] + [_row('life-advance')])
    if lookup == 'exact':
        result = strategy._latest_index(rows, 'life-advance')
    else:
        result = strategy._latest_life_advance_index(rows)
    assert result == 13
    assert rows.visited == [12]


def test_life_lookup_preserves_different_life_step_matching_and_absent_result():
    rows = [_row('life-advance'), _row('life-advance-one-day', decorated=True)]
    assert strategy._latest_life_advance_index(rows) == 2
    assert strategy._latest_index(rows, 'life-advance') == 1
    assert strategy._latest_index(rows, 'missing') == 0
