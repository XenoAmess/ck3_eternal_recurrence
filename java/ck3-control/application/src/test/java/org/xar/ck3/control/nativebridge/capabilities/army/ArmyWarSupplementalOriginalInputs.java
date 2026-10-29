package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.action.RawJson;

/** Mandatory original Python compatibility oracle, invoked only by actual CI. No production Python module. */
public final class ArmyWarSupplementalOriginalInputs {
    private ArmyWarSupplementalOriginalInputs(){ }
    public static ObjectNode capture(Path temporary)throws Exception{
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        if(repository==null||repository.isBlank()||python==null||python.isBlank())throw new IllegalStateException("NOT_RUN: mandatory xar.repository.root and xar.python original producers required");
        Path root=Path.of(repository).resolve("ck3_autonomous_player"),out=temporary.resolve("supplemental-original.json"),error=temporary.resolve("supplemental-original.stderr");
        Process process=new ProcessBuilder(python,"-B","-X","utf8","-c",PROGRAM,root.toString()).redirectOutput(out.toFile()).redirectError(error.toFile()).start();
        try{if(!process.waitFor(45,TimeUnit.SECONDS))throw new java.io.IOException("original supplemental producer timeout");
            if(process.exitValue()!=0)throw new java.io.IOException("original supplemental producer failed: "+Files.readString(error));
            return ArmyWarSupplementalReadCodec.object(new RawJson(Files.readAllBytes(out)));
        }finally{if(process.isAlive())process.destroyForcibly();}
    }
    public static final String PROGRAM="""
        import ast,copy,hashlib,json,sys
        from pathlib import Path
        root=Path(sys.argv[1]);sys.path[:0]=[str(root/'src'),str(root/'tests/unit')]
        pins={
          'src/xar_autoplayer/bridge/native_driver.py':'eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603',
          'src/xar_autoplayer/bridge/war_contract.py':'b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937',
          'src/xar_autoplayer/bridge/defender_dejure_exit_terms_v1.py':'fdb5155ed55d5c1c700cdeb4fe8235f9e6317515d70341fe58a6860f5ec6dc0a',
          'tests/unit/test_province_local_siege_contract.py':'1543d4b0c2b8b613ad13a20a441b66b5674985d61b6e3b44152a040ab6bc2224',
          'tests/unit/test_siege_membership_contract.py':'adbc9669d860cc3cb38ddfee514a47dee01c78875423f0136666b7d430dee931',
          'tests/unit/test_defender_dejure_exit_terms_v1.py':'503873e9d6f6d677398f2e5739b98eb06696a0c877ea1e71a491d78c01435df4',
          'src/xar_autoplayer/bridge/siege_membership_contract.py':'501c9a24331a1a4121ea3bf0cd74ac63c954ca565ea5e5fb2e0a5b42a5ff23bf',
          'src/xar_autoplayer/bridge/province_besieging_army_selection_contract.py':'0bf1ebd7ac1f77e607e0654b430e865546c04d72a3caa143541f799dc619f354',
          'src/xar_autoplayer/bridge/public_unit_contract.py':'0de76f3bf10ae24d3202177bb527bcb3ec903432a38af64f55e08c95698cab4e',
          'src/xar_autoplayer/bridge/driver.py':'eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6',
          'src/xar_autoplayer/h2743_stock_predicate_admission.py':'de9816f26acdc5e76899fa87bdaefb4d5c7c16b49e626bf1daeecf531f7b3bb8'}
        for name,sha in pins.items():
          if hashlib.sha256((root/name).read_bytes()).hexdigest()!=sha:raise RuntimeError('original producer drift: '+name)
        import test_province_local_siege_contract as local
        import test_siege_membership_contract as members
        import test_defender_dejure_exit_terms_v1 as defender
        from xar_autoplayer.bridge.war_contract import normalize_province_local_siege_result
        from xar_autoplayer.bridge.defender_dejure_exit_terms_v1 import normalize_defender_dejure_exit_terms_v1
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        # Execute the unchanged original method and its exact helper bodies, without importing
        # the Native runtime or constructing a Game. AST extraction changes no method branch.
        tree=ast.parse((root/'src/xar_autoplayer/bridge/native_driver.py').read_text(encoding='utf-8'))
        selected=[]
        for node in tree.body:
          if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in ('_war_by_id','_same_paused_native_frame'):selected.append(copy.deepcopy(node))
          if isinstance(node,ast.ClassDef) and node.name=='NativeHeadlessGameplayDriver':
            selected.extend(copy.deepcopy(method) for method in node.body if isinstance(method,ast.FunctionDef) and method.name=='_execute_defender_dejure_exit_terms_v1_query')
        if len(selected)!=3:raise RuntimeError('exact original driver method/helper inventory changed')
        namespace=dict(BridgeUnavailableError=BridgeUnavailableError,normalize_defender_dejure_exit_terms_v1=normalize_defender_dejure_exit_terms_v1,QUERY_DEFENDER_DEJURE_EXIT_TERMS_V1_CAPABILITY='game.command.query-defender-de-jure-exit-terms-v1-N')
        exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+selected,type_ignores=[])),'<exact-original-native-driver-method>','exec'),namespace)
        actual_driver=namespace['_execute_defender_dejure_exit_terms_v1_query']
        class SoftwareOriginal:
          def __init__(self,raw,after):self.raw=raw;self.after=after;self.sends=0
          def _execute_primitive_step(self,step,**kwargs):
            self.sends+=1
            if step!=self.raw['step'] or kwargs.get('required_capability')!='game.command.query-defender-de-jure-exit-terms-v1-N' or kwargs.get('internal_semantic_snapshot') is not True:raise RuntimeError('original primitive selection changed')
            return copy.deepcopy(self.raw)
          def take_internal_semantic_snapshot(self):return copy.deepcopy(self.after)
        def frame(native,date,actor=29829,war=16777231):
          return dict(snapshot_id='software:'+str(native),revision=7,native_revision=native,date_raw=date,episode_run_id='software-supplemental',paused=True,map_ready=True,played_character=dict(character_id=actor,alive=True),diagnostics=dict(connection_generation=1),active_wars=[dict(war_id=war,player_side='defender',player_is_primary_war_leader=True,primary_opponent_character_id=30097,targeted_title_ids=[2128])])
        rows=[]
        def add_local(name,raw):
          before=frame(raw['snapshot_revision'],raw['date_raw']);expected=normalize_province_local_siege_result(copy.deepcopy(raw),expected_step=raw['step'],expected_province_id=raw['province_state']['province_id'],expected_snapshot_revision=raw['snapshot_revision'],expected_date_raw=raw['date_raw'])
          rows.append(dict(name=name,kind='local',raw=raw,before=before,after=copy.deepcopy(before),expected=expected))
        add_local('original-available',local._result())
        partial=local._result();partial['status']='partial';partial['province_state']['siege_observable']=False;add_local('original-partial',partial)
        raw=local._result();raw['province_state']=members.objective();raw['step']='query-province-local-siege-v1-3711';add_local('original-membership-repetitions-zero',raw)
        for name,value in [('missing','MISSING'),('null',None),('zero',dict(raw=0,scale=100000))]:
          row=copy.deepcopy(raw);siege=row['province_state']['active_siege']
          if name=='missing':siege.pop('eligible_regiment_siege_work')
          else:siege['eligible_regiment_siege_work']=value
          add_local('software-optional-work-'+name,row)
        wide=copy.deepcopy(raw);wide['snapshot_revision']=2**64-1;wide['query_sequence']=2**64-1;wide['province_state']['active_siege']['current_work']['raw']=2**63-1;add_local('software-wide-raw-and-native-revision',wide)
        assault=copy.deepcopy(raw);assault['province_state']['active_siege'].update(assault_observable=True,breach_level=2,assault_in_progress=False,can_start_assault=True,can_stop_assault=False,assault_daily_progress=dict(raw=1,scale=100000),assault_daily_casualties=0);add_local('software-assault-observed',assault)
        for name in ('baseline','truce','storage','signed-resource-boundary'):
          candidate=defender._candidate()
          if name in ('truce','storage'):candidate['truce_inputs_v1']=defender._truce_inputs()
          if name=='storage':candidate['border_raid_storage_candidate_v1']=dict(schema='xar.ck3.h2743-border-raid-storage-candidate.v1',status='structural_candidate_only',candidate=False,storage_capacity=17,active_war_count=2,matching_war_count=0,unavailable_reason=None,native_condition_observed=False)
          if name=='signed-resource-boundary':candidate['primary_resource_balances'][0]['value']['raw']=-2**63;candidate['primary_monthly_gold_income'][0]['value']['raw']=2**63-1
          raw=dict(step='query-defender-de-jure-exit-terms-v1-16777231',accepted=True,status='baseline_only',query_sequence=2**64-1,defender_de_jure_exit_terms_v1=candidate,backend_id='native-headless')
          before=frame(3,53217264);after=copy.deepcopy(before);stub=SoftwareOriginal(raw,after)
          expected=actual_driver(stub,raw['step'],starting=copy.deepcopy(before),selected_revision=7,war_id=16777231)
          if stub.sends!=1:raise RuntimeError('original driver dispatched more than once')
          rows.append(dict(name='original-driver-'+name,kind='baseline',raw=raw,before=before,after=after,expected=expected))
        sys.stdout.write(json.dumps(dict(cases=rows,source_pins=pins),ensure_ascii=False,separators=(',',':')))
        """;
}
