"""File-only DES load bootstrap regression; AST simulation is not engine scheduling proof."""
from __future__ import annotations
import copy
from dataclasses import dataclass, field
import io
import os
from pathlib import Path
import re
import sys
import unittest

REPO=Path(os.environ.get('DES_REPO','D:/workspace/ck3_eternal_recurrence'))
SOURCE=Path(os.environ.get('DES_BOOTSTRAP_SOURCE',str(REPO)))
sys.path.insert(0,str(REPO/'ck3_autonomous_player/src'))
sys.path.insert(0,str(REPO/'tools/lyd_i3b_checkpoint_readback/reader/dependencies'))
from xar_autoplayer.campaign_score_save_reader import melt_tokens
from bounded_save_parser import parse_block, one
sys.path.append(str(REPO/'tools'))
from extract_auto_upgrade_buildings import parse_clausewitz, Block

MOD='mod_dynastic_esotericism/'
SGUI=MOD+'common/scripted_guis/des_saved_game_initialization.txt'
WINDOW=MOD+'gui/des_saved_game_initialization.gui'
WIDGET=MOD+'gui/scripted_widgets/des_saved_game_initialization.txt'
EFFECTS=MOD+'common/scripted_effects/des_initialization_effects.txt'

def text(relative,original=False):
    path=(REPO if original else SOURCE)/relative
    if not original and not path.exists():path=REPO/relative
    return path.read_text(encoding='utf-8-sig')

def parsed(relative,original=False):
    # Reuse the shared script parser so >= is retained, not flattened by the Save parser.
    def project(block):
        result=[]
        for entry in block.entries:
            row={'key':entry.key if entry.operator is not None else None,
                 'value':project(entry.value) if isinstance(entry.value,Block)
                         else entry.value if entry.operator is not None else entry.key}
            if entry.operator not in (None,'='):row['operator']=entry.operator
            result.append(row)
        return result
    return project(parse_clausewitz(text(relative,original)))

def entries(body,key):
    return [row['value'] for row in body if row['key']==key]

def exact(body,key):
    value=entries(body,key)
    if len(value)!=1:raise ValueError('Expected exact single script field: '+key)
    return value[0]

@dataclass(eq=False)
class Scope:
    kind:str
    name:str
    human:bool=False
    alive:bool=True
    playable:bool=True
    tenets:set[str]=field(default_factory=set)
    doctrines:set[str]=field(default_factory=set)
    known:set[str]=field(default_factory=set)
    variables:dict=field(default_factory=dict)
    faiths:list=field(default_factory=list)
    rites:list=field(default_factory=list)
    characters:list=field(default_factory=list)

@dataclass
class World:
    named_rites:dict=field(default_factory=dict)
    globals:dict=field(default_factory=dict)
    lists:dict=field(default_factory=dict)
    religions:list=field(default_factory=list)
    game_rules:dict=field(default_factory=dict)
    protected:dict=field(default_factory=lambda:{'faith':'original_faith','title':'original_title',
        'house':'original_house','dynasty':'original_dynasty','role':'original_role','gold':141})
    scheduled:list=field(default_factory=list)
    observed_calls:list=field(default_factory=list)

class SourceEffects:
    """Execute actual small initialization AST. Unchanged discovery/maintenance are recorded boundaries.

    This checks the new entry and preexisting defaults/knowledge/queue contract,
    not Native operations, all binding internals or the game's GUI scheduler.
    """
    def __init__(self,world):
        self.world=world
        self.definitions={row['key']:row['value'] for row in parsed(EFFECTS)}
    def condition(self,body,scope):
        results=[]
        for row in body:
            key,value=row['key'],row['value']
            if key in ('AND','OR','NOR','NOT'):
                inside=[self.condition([x],scope) for x in value]
                result=all(inside) if key=='AND' else any(inside) if key=='OR' else not any(inside)
            elif key=='is_ai':result=(not scope.human)==(value=='yes')
            elif key=='is_alive':result=scope.alive==(value=='yes')
            elif key=='is_playable_character':result=scope.playable==(value=='yes')
            elif key=='has_global_variable':result=value in self.world.globals
            elif key=='rite_has_doctrine':result=value in scope.doctrines
            elif key=='rite_has_tenet':result=value in scope.tenets
            elif key=='any_rite_tenet':
                if value!=[{'key':'count','value':'4','operator':'>='}]:raise AssertionError('Unexpected tenet count guard')
                result=len(scope.tenets)>=4
            elif key=='exists' and value.startswith('rite:'):result=value.removeprefix('rite:') in self.world.named_rites
            elif key=='knows_doctrine':result=value.removeprefix('doctrine:') in scope.known
            elif key=='is_target_in_global_variable_list':
                target=exact(value,'target');target=scope if target=='this' else target
                result=target in self.world.lists.get(exact(value,'name'),[])
            else:raise AssertionError('Unexpected initialization condition: '+str(key))
            results.append(result)
        return all(results)
    def effect(self,name,scope):
        self.world.observed_calls.append(name)
        if name in ('des_discover_rites_effect','des_maintenance_effect'):return
        self.run(self.definitions[name],scope)
    def run(self,body,scope):
        limits=entries(body,'limit')
        if limits and not self.condition(limits[0],scope):return
        for row in body:
            key,value=row['key'],row['value']
            if key=='limit':continue
            if key=='if':self.run(value,scope)
            elif key=='set_global_variable':self.world.globals[exact(value,'name')]=exact(value,'value')
            elif key=='set_variable':scope.variables[exact(value,'name')]=exact(value,'value')
            elif key=='add_to_global_variable_list':
                target=exact(value,'target');target=scope if target=='this' else target
                self.world.lists.setdefault(exact(value,'name'),[]).append(target)
            elif key=='add_rite_doctrine':scope.doctrines.add(value)
            elif key=='remove_rite_tenet':scope.tenets.discard(value)
            elif key=='add_rite_tenet':scope.tenets.add(value)
            elif key=='change_rite_doctrine':
                scope.doctrines.difference_update({'doctrine_funeral_sky_burial','doctrine_funeral_mummification','doctrine_funeral_burial'})
                scope.doctrines.add(value)
            elif isinstance(key,str) and key.startswith('rite:'):
                named=self.world.named_rites.get(key.removeprefix('rite:'))
                if named is not None:self.run(value,named)
            elif key=='add_known_doctrine':scope.known.add(value)
            elif key=='every_religion_global':
                for religion in list(self.world.religions):self.run(value,religion)
            elif key=='every_faith':
                for faith in list(scope.faiths):self.run(value,faith)
            elif key=='every_faith_rite':
                for rite in list(scope.rites):self.run(value,rite)
            elif key=='every_faith_character':
                for character in list(scope.characters):self.run(value,character)
            elif key=='trigger_event':self.world.scheduled.append((scope.kind,scope.name,copy.deepcopy(value)))
            elif key in self.definitions or key in ('des_discover_rites_effect','des_maintenance_effect'):self.effect(key,scope)
            else:raise AssertionError('Unexpected initialization write: '+str(key))

def old_world():
    actor=Scope('character','loaded-human',human=True)
    ai=Scope('character','living-AI')
    dead=Scope('character','dead',alive=False)
    unplayable=Scope('character','unplayable',playable=False)
    rites=[Scope('rite','vanilla'),Scope('rite','existing-none',doctrines={'des_doctrine_none'}),
        Scope('rite','existing-dynastic',doctrines={'des_doctrine_dynastic'}),
        Scope('rite','both-preserved',doctrines={'des_doctrine_none','des_doctrine_dynastic'})]
    faith=Scope('faith','original-faith',rites=rites,characters=[actor,ai,dead,unplayable])
    religions=[Scope('religion','first',faiths=[faith]),Scope('religion','second')]
    named=Scope('rite','des_procreation_rite',tenets={'tenet_carnal_exaltation','tenet_ancestor_worship','tenet_pursuit_of_power'},doctrines={'doctrine_funeral_mummification'})
    return World(religions=religions,named_rites={'des_procreation_rite':named}),actor,faith

class SavedBootstrapTest(unittest.TestCase):
    def bootstrap(self,world,actor):SourceEffects(world).effect('des_initialize_loaded_game_effect',actor)
    def test_real_runtime_widget_links_actual_owned_player_and_guarded_scripted_gui(self):
        widget=text(WIDGET).strip()
        self.assertEqual('gui/des_saved_game_initialization.gui = des_saved_game_initialization_window',widget)
        window=exact(parsed(WINDOW),'window')
        self.assertEqual('"des_saved_game_initialization_window"',exact(window,'name'))
        self.assertEqual('yes',exact(window,'alwaystransparent'))
        self.assertEqual('"[GetPlayer.IsValid]"',exact(window,'visible'))
        state=exact(window,'state')
        self.assertIn("GetScriptedGui('des_saved_game_initialize_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )",exact(state,'trigger_when'))
        self.assertIn("GetScriptedGui('des_saved_game_initialize_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )",exact(state,'on_start'))
        sgui=exact(parsed(SGUI),'des_saved_game_initialize_gui')
        self.assertEqual('character',exact(sgui,'scope'))
        world,actor,_=old_world();self.assertTrue(SourceEffects(world).condition(exact(sgui,'is_shown'),actor))
        self.assertEqual([{'key':'des_initialize_loaded_game_effect','value':'yes'}],exact(sgui,'effect'))
    def test_old_world_with_no_product_rules_gets_real_defaults_knowledge_and_queue(self):
        world,actor,faith=old_world();self.assertEqual({},world.game_rules)
        self.bootstrap(world,actor)
        self.assertEqual('yes',world.globals['des_initialized'])
        self.assertEqual({'des_doctrine_none'},faith.rites[0].doctrines)
        self.assertEqual({'des_doctrine_none','des_doctrine_dynastic'},actor.known)
        self.assertEqual({'des_doctrine_none','des_doctrine_dynastic'},faith.characters[1].known)
        self.assertEqual(set(),faith.characters[2].known);self.assertEqual(set(),faith.characters[3].known)
        self.assertEqual(['doctrine:des_doctrine_none'],world.lists['xar_rite_creation_optional_default_doctrines'])
        self.assertEqual(1,len(world.scheduled));self.assertEqual(('religion','first'),world.scheduled[0][:2])
        self.assertEqual('des_monthly_maintenance',exact(world.scheduled[0][2],'on_action'))
        self.assertEqual('30',exact(world.scheduled[0][2],'days'))
        self.assertIn('des_maintenance_effect',world.observed_calls)
    def test_defaulting_never_overwrites_existing_none_or_dynastic_choice(self):
        world,actor,faith=old_world();self.bootstrap(world,actor)
        self.assertEqual({'des_doctrine_none'},faith.rites[1].doctrines)
        self.assertEqual({'des_doctrine_dynastic'},faith.rites[2].doctrines)
        self.assertEqual({'des_doctrine_none','des_doctrine_dynastic'},faith.rites[3].doctrines)
        self.assertNotIn('des_ordinary_binding_ready',faith.rites[0].variables)
        self.assertEqual('yes',faith.rites[2].variables['des_ordinary_binding_ready'])
    def test_repeated_window_frames_do_not_reinitialize_or_repeat_maintenance(self):
        world,actor,faith=old_world();self.bootstrap(world,actor)
        snapshot=copy.deepcopy((world.globals,world.scheduled,actor.known,[x.doctrines for x in faith.rites]))
        for _ in range(5):self.bootstrap(world,actor)
        self.assertEqual(snapshot,(world.globals,world.scheduled,actor.known,[x.doctrines for x in faith.rites]))
        self.assertEqual(1,world.observed_calls.count('des_initialize_world_effect'))
        self.assertEqual(1,world.observed_calls.count('des_maintenance_effect'))
        shown=exact(exact(parsed(SGUI),'des_saved_game_initialize_gui'),'is_shown')
        self.assertFalse(SourceEffects(world).condition(shown,actor))
    def test_existing_initialized_product_state_is_completely_outside_automatic_effect(self):
        world,actor,faith=old_world()
        world.globals.update(des_initialized='yes',des_new_game_preset_clergy_pending='yes',des_procreation_preset_023_checked='yes')
        world.lists['xar_rite_creation_optional_default_doctrines']=['doctrine:external_provider']
        faith.rites[2].variables.update(des_bound_dynasty='original-dynasty',des_join_house='original-house',des_native_head_claim_pending='original-token')
        before=copy.deepcopy((world.globals,world.lists,world.protected,actor.known,[x.variables for x in faith.rites]))
        self.bootstrap(world,actor)
        self.assertEqual(before,(world.globals,world.lists,world.protected,actor.known,[x.variables for x in faith.rites]))
        self.assertEqual(['des_initialize_loaded_game_effect'],world.observed_calls);self.assertEqual([],world.scheduled)
    def test_existing_optional_provider_registry_is_preserved_and_none_is_added_once(self):
        world,actor,_=old_world();world.lists['xar_rite_creation_optional_default_doctrines']=['doctrine:external_provider']
        self.bootstrap(world,actor)
        effects=SourceEffects(world);effects.effect('des_initialize_world_effect',actor)
        self.assertEqual(['doctrine:external_provider','doctrine:des_doctrine_none'],world.lists['xar_rite_creation_optional_default_doctrines'])
        self.assertEqual(1,len(world.scheduled))
    def test_execute_time_guard_rejects_ai_dead_and_stale_preinitialize_gui_snapshot(self):
        for human,alive in [(False,True),(True,False)]:
            world,actor,_=old_world();actor.human=human;actor.alive=alive
            self.bootstrap(world,actor);self.assertNotIn('des_initialized',world.globals)
            self.assertEqual([],world.scheduled)
        world,actor,_=old_world();world.globals.update(des_initialized='yes',des_procreation_preset_023_checked='yes')
        self.bootstrap(world,actor);self.assertEqual(['des_initialize_loaded_game_effect'],world.observed_calls)
    def test_loaded_entry_never_gets_new_game_preset_token_or_rewrites_player_rules(self):
        body=exact(parsed(EFFECTS),'des_initialize_loaded_game_effect')
        self.assertEqual({'if'},set(x['key'] for x in body))
        branch=exact(body,'if')
        self.assertEqual({'limit','if','des_reconcile_procreation_preset_023_effect'},set(x['key'] for x in branch))
        world,actor,_=old_world();protected=copy.deepcopy(world.protected);self.bootstrap(world,actor)
        self.assertEqual({},world.game_rules);self.assertEqual(protected,world.protected)
        self.assertNotIn('des_new_game_preset_clergy_pending',world.globals)
        self.assertNotIn('des_reconcile_new_game_preset_clergy_effect',world.observed_calls)
        for row in parsed(EFFECTS,True):
            if row['key'] not in ('des_initialize_world_effect','des_initialize_loaded_game_effect'):
                self.assertEqual(row['value'],exact(parsed(EFFECTS),row['key']),row['key'])
    def test_formal_builder_explicitly_contains_all_three_product_runtime_leaves(self):
        product=text(MOD+'tools/src/main/java/org/xar/ck3/dynastic/release/ReleaseProduct.java')
        for relative in (SGUI,WINDOW,WIDGET):
            self.assertEqual(1,product.count('"'+relative.removeprefix(MOD)+'"'),relative)
            self.assertNotIn('/acceptance-fixture/',relative)
        descriptor=text(MOD+'descriptor.mod')
        self.assertIn('version="0.2.3"',descriptor)
        for name in (SGUI,WINDOW,WIDGET):self.assertNotIn('on_game_load',text(name))
    def test_manual_fallback_and_new_game_only_preset_entry_remain_unchanged(self):
        actions=parsed(MOD+'common/on_action/des_on_actions.txt')
        init=exact(exact(actions,'des_new_game_initialize'),'effect')
        self.assertIn({'key':'set_global_variable','value':[{'key':'name','value':'des_new_game_preset_clergy_pending'},{'key':'value','value':'yes'}]},init)
        decision=exact(parsed(MOD+'common/decisions/des_initialization_decisions.txt'),'des_initialize_decision')
        self.assertEqual('yes',exact(exact(decision,'effect'),'hidden_effect')[0]['value'])
        self.assertEqual(exact(parsed(MOD+'common/decisions/des_initialization_decisions.txt',True),'des_initialize_decision'),decision)

if __name__=='__main__':unittest.main()
