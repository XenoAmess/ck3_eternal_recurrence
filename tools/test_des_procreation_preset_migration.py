"""Run the actual candidate Clausewitz AST; no Game/render/Save qualification."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

helper = Path(__file__).with_name('test_des_saved_game_bootstrap.py')
spec = importlib.util.spec_from_file_location('des_bootstrap_candidate', helper)
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)

MARKER = 'des_procreation_preset_023_checked'
MIGRATION = 'des_reconcile_procreation_preset_023_effect'
OLD = {'tenet_be_fruitful_and_multiply', 'tenet_carnal_exaltation', 'tenet_sacred_childbirth'}
NEW = {'tenet_carnal_exaltation', 'tenet_ancestor_worship', 'tenet_pursuit_of_power'}
SKY = 'doctrine_funeral_sky_burial'
MUMMY = 'doctrine_funeral_mummification'


def world(initialized=True):
    w, actor, faith = b.old_world()
    if initialized:
        w.globals['des_initialized'] = 'yes'
    rite = w.named_rites['des_procreation_rite']
    rite.tenets = set(OLD)
    rite.doctrines = {SKY, 'des_doctrine_dynastic', 'doctrine_gender_equal'}
    rite.variables = {'des_bound_dynasty': 'same-dynasty', 'custom-edit-variable': 42}
    return w, actor, faith, rite


def bootstrap(w, actor):
    b.SourceEffects(w).effect('des_initialize_loaded_game_effect', actor)


class ProcreationMigrationTest(unittest.TestCase):
    def test_initial_named_rite_uses_requested_ids_and_vivhite_is_byte_exact(self):
        relative = b.MOD + 'common/religion/rite_types/des_rites.txt'
        rites = b.parsed(relative)
        procreation = b.exact(rites, 'des_procreation_rite')
        actual_tenets = [row['value'] for row in b.exact(procreation, 'tenets')]
        self.assertEqual(['tenet_carnal_exaltation', 'tenet_ancestor_worship', 'tenet_pursuit_of_power'], actual_tenets)
        doctrines = [row['value'] for row in b.exact(procreation, 'doctrines')]
        self.assertEqual(1, doctrines.count(MUMMY))
        self.assertNotIn(SKY, doctrines)
        self.assertEqual(b.text(relative, True).split('des_vivhite_rite = {', 1)[1], b.text(relative).split('des_vivhite_rite = {', 1)[1])
        self.assertEqual(b.parsed(b.MOD + 'common/religion/faith_types/des_faiths.txt', True), b.parsed(b.MOD + 'common/religion/faith_types/des_faiths.txt'))

    def test_initialized_legacy_world_migrates_without_reinitializing_or_maintenance(self):
        w, actor, faith, rite = world()
        before = copy.deepcopy((w.protected, w.lists, actor.known, rite.variables))
        bootstrap(w, actor)
        self.assertEqual(NEW, rite.tenets)
        self.assertEqual({MUMMY, 'des_doctrine_dynastic', 'doctrine_gender_equal'}, rite.doctrines)
        self.assertEqual('yes', w.globals[MARKER])
        self.assertEqual(before, (w.protected, w.lists, actor.known, rite.variables))
        self.assertNotIn('des_initialize_world_effect', w.observed_calls)
        self.assertNotIn('des_maintenance_effect', w.observed_calls)
        self.assertEqual([], w.scheduled)

    def test_uninitialized_old_world_keeps_original_bootstrap_and_runs_migration(self):
        w, actor, faith, rite = world(False)
        w.lists['xar_rite_creation_optional_default_doctrines'] = ['doctrine:other-provider']
        bootstrap(w, actor)
        self.assertEqual(NEW, rite.tenets)
        self.assertIn(MUMMY, rite.doctrines)
        self.assertEqual('yes', w.globals['des_initialized'])
        self.assertEqual(['doctrine:other-provider', 'doctrine:des_doctrine_none'], w.lists['xar_rite_creation_optional_default_doctrines'])
        self.assertEqual({'des_doctrine_none', 'des_doctrine_dynastic'}, actor.known)
        self.assertEqual(1, len(w.scheduled))
        self.assertEqual(1, w.observed_calls.count('des_initialize_world_effect'))
        self.assertEqual(1, w.observed_calls.count('des_maintenance_effect'))

    def test_any_edited_core_tenet_is_preserved_and_reverted_old_bundle_is_not_revisited(self):
        for removed in OLD:
            with self.subTest(removed=removed):
                w, actor, faith, rite = world()
                rite.tenets.remove(removed)
                rite.tenets.add('tenet_custom_player_choice')
                before = copy.deepcopy((rite.tenets, rite.doctrines))
                bootstrap(w, actor)
                self.assertEqual(before, (rite.tenets, rite.doctrines))
                self.assertEqual('yes', w.globals[MARKER])
                rite.tenets = set(OLD)
                bootstrap(w, actor)
                self.assertEqual(OLD, rite.tenets)
                self.assertIn(SKY, rite.doctrines)

    def test_edited_funeral_or_mixed_new_bundle_is_preserved_as_one_bundle(self):
        for tenets, funeral in [(OLD, 'doctrine_funeral_burial'), (NEW, SKY), (NEW, MUMMY)]:
            with self.subTest(tenets=tenets, funeral=funeral):
                w, actor, faith, rite = world()
                rite.tenets = set(tenets)
                rite.doctrines = {funeral, 'des_doctrine_dynastic'}
                before = copy.deepcopy((rite.tenets, rite.doctrines))
                bootstrap(w, actor)
                self.assertEqual(before, (rite.tenets, rite.doctrines))
                self.assertEqual('yes', w.globals[MARKER])

    def test_four_tenet_superset_is_not_mistaken_for_legacy_three(self):
        w, actor, faith, rite = world()
        rite.tenets.add('tenet_modded_fourth_choice')
        before = copy.deepcopy((rite.tenets, rite.doctrines))
        bootstrap(w, actor)
        self.assertEqual(before, (rite.tenets, rite.doctrines))
        self.assertEqual('yes', w.globals[MARKER])

    def test_vivhite_and_dynamic_rites_are_never_migration_targets(self):
        w, actor, faith, rite = world()
        other = b.Scope('rite', 'des_vivhite_rite', tenets=set(OLD), doctrines={SKY})
        dynamic = b.Scope('rite', 'dynamic-player-rite', tenets=set(OLD), doctrines={SKY})
        w.named_rites.update(des_vivhite_rite=other, dynamic_player_rite=dynamic)
        before = copy.deepcopy([(x.tenets, x.doctrines, x.variables) for x in (other, dynamic)])
        bootstrap(w, actor)
        self.assertEqual(before, [(x.tenets, x.doctrines, x.variables) for x in (other, dynamic)])

    def test_repeat_load_and_later_player_edit_never_reapply_the_migration(self):
        w, actor, faith, rite = world()
        bootstrap(w, actor)
        rite.tenets = set(OLD)
        rite.doctrines = {SKY}
        snapshot = copy.deepcopy((w.globals, rite.tenets, rite.doctrines))
        for _ in range(5):
            bootstrap(w, actor)
        self.assertEqual(snapshot, (w.globals, rite.tenets, rite.doctrines))
        shown = b.exact(b.exact(b.parsed(b.SGUI), 'des_saved_game_initialize_gui'), 'is_shown')
        self.assertFalse(b.SourceEffects(w).condition(shown, actor))

    def test_missing_fixed_rite_never_consumes_migration_and_ai_or_dead_cannot_run(self):
        w, actor, faith, rite = world()
        del w.named_rites['des_procreation_rite']
        bootstrap(w, actor)
        self.assertNotIn(MARKER, w.globals)
        self.assertEqual([], w.scheduled)
        for human, alive in [(False, True), (True, False)]:
            w, actor, faith, rite = world()
            actor.human, actor.alive = human, alive
            bootstrap(w, actor)
            self.assertNotIn(MARKER, w.globals)
            self.assertEqual(OLD, rite.tenets)

    def test_new_world_definitions_only_consume_once_and_stock_picker_rules_are_not_replaced(self):
        w, actor, faith = b.old_world()
        rite = w.named_rites['des_procreation_rite']
        before = copy.deepcopy((rite.tenets, rite.doctrines))
        bootstrap(w, actor)
        self.assertEqual(before, (rite.tenets, rite.doctrines))
        self.assertEqual('yes', w.globals[MARKER])
        candidate = Path(__file__).parents[1]
        self.assertFalse((candidate / b.MOD / 'common/religion/tenet_types').exists())
        self.assertFalse((candidate / b.MOD / 'common/religion/doctrine_types/20_doctrines.txt').exists())


if __name__ == '__main__':
    unittest.main()
