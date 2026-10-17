"""Small provenance-bound historical cases; never current native permission."""

from __future__ import annotations

HOLY_SITE_ADOPTION_HISTORICAL_CASES = [{'case_id': 'faith-e01-r5-nadjaf-20261017',
  'kind': 'historical_native_observation',
  'game_build': '1.20.0.4',
  'machine_id': '4-8e1c2f1861',
  'run_id': '4-8e1c2f1861--faith-and-power--R0005',
  'observed_until_utc': '2026-10-17T12:04:35.487269+00:00',
  'record_path': 'docs/ck3-native-ai/evidence/faith-and-power-episode01-r0005/adoption-case.json',
  'record_sha256': '8ca7a9425b0e7530702996012194d34df0f160453eb6b9194c126c1f991547c7',
  'scope': {'pid': 12556,
            'connection_generation': 1,
            'actor_id': 15893,
            'rite_id': 15,
            'faith_id': 50,
            'faith_main_rite_id': 13,
            'date_raw': 51394920},
  'observed': {'membership_added': True,
               'new_faith50_level': 'regular',
               'same_full_id_type_barony': True,
               'faith51_association_retained': True,
               'faith51_after_level': 'eminent',
               'inventory_before_after_empty': True,
               'actual_piety_paid': 1000,
               'cached_active_after': False,
               'evaluated_active_after': False,
               'post_confirm_detail_unavailable': True,
               'post_adoption_checkpoint_saved': True,
               'checkpoint_sha256': '0f1774d0be0f7652ce8dda22ce76a1eceeb36b6f9d42ae15422eae5bfd4cd18f'},
  'unknown_or_not_verified': ['faith51 prior same-run grade and unchanged-grade claim',
                              'nonempty artifact retention',
                              'post-action cooldown/free-action count/used kingdoms',
                              'world effects applied and actual beneficiaries',
                              'C cold restore, complete Driver binding and normal close',
                              'media clean spans and human review'],
  'planning_lessons': ['Current native terms must be re-read; this historical permission and price '
                       'cannot authorize another action.',
                       'This case added a regular association to the same existing site; no '
                       'universal default-grade invariant is claimed.',
                       'Actual membership and piety debit are independent of the confirmation ACK.',
                       'The already-empty inventory stayed empty; nonempty artifact retention was '
                       'not tested.',
                       'This successful adoption did not activate the empty site in cache or '
                       'current native evaluation; actual benefits remain unobserved.',
                       'Post-Confirm detail became unavailable while adoption succeeded; do not '
                       'retry or interpret missing cooldown as absent.',
                       'Faith51 remained associated; its prior same-run eminent flag was not '
                       'captured, so unchanged grade is not claimed.'],
  'generalization': 'single prepared vanilla case only; re-read current native terms; no '
                    'engine-wide default, price or Active invariant'}]
