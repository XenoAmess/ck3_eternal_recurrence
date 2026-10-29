package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import static org.xar.ck3.control.service.root.CashObservationPublicCodec.*;
import static org.junit.jupiter.api.Assertions.*;

/** Actual retained original native serializer rows -> original Python producer -> sole installed family/decoder/public serde. No Game authority. */
final class CashObservationReadParityTest {
    private static final Instant TIME=Instant.parse("2026-10-24T00:00:00Z"),DEADLINE=TIME.plusSeconds(60);
    private static final ExactRef SOURCE=new ExactRef("controlled-cash-no-native-authority",1,"a".repeat(64));
    @TempDir Path temporary;
    @Test void originalPythonCashFeesAndDurableMaterialCompositionReachTheSamePublicConsumer()throws Exception {
        ObjectNode data=originals();int accepted=0,rejected=0;
        for(JsonNode row:data.path("rows")){
            var snapshot=(ObjectNode)row.path("snapshot");var request=request(row);var complete=frame(snapshot);
            Optional<RawJson> material=request instanceof Construction?Optional.of(PublicDataJson.encode(row.path("material"))):Optional.empty();
            var selected=new CashObservationReads.Selection(complete,request,material,DEADLINE);var reads=new CashObservationReads(new CashObservationReads.Sources(SOURCE,SOURCE));
            var catalog=new RootReadContractCatalog(List.of(),reads.families());var contract=reads.contract(catalog,selected);
            assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,contract.guardMode());assertEquals(ReadContract.WireProfile.G2_PRIVATE_QUERY,contract.wireProfile());
            assertTrue(contract.requiredCapability().isEmpty());assertEquals(CashObservationReads.PERMISSION,contract.permissionKey());
            assertEquals(selected.operation().value(),contract.prepare(selected.request(),"original-cash").step());
            assertTrue(contract.prepare(selected.request(),"original-cash").additionalFields().objectFieldNames().isEmpty(),"cash policy/material must not leak into native fields");
            var receipt=receipt(selected,row.path("frame"),contract.contractId());
            if(!row.path("accepted").booleanValue()){assertThrows(IllegalArgumentException.class,()->contract.decode(receipt),row.path("name").textValue());rejected++;continue;}
            var observed=contract.decode(receipt);same(row.path("expected"),PublicDataJson.object(observed.originalNormalized()));
            assertEquals(observed,contract.replay(receipt));RawJson publicWire=CashObservationPublicCodec.encode(observed);
            assertEquals(observed.originalNormalized(),CashObservationCodec.nativeWire(publicWire));
            assertEquals(publicWire,CashObservationCodec.publicWire(CashObservationCodec.nativeWire(publicWire)));
            var crossed=selected.request();var wrong=new PlanningReadRequest(crossed.before(),crossed.source(),"wrong-physical-session",crossed.operation(),crossed.arguments(),crossed.deadline());
            assertThrows(IllegalArgumentException.class,()->contract.prepare(wrong,"forbidden"));
            assertThrows(IllegalArgumentException.class,()->reads.contract(new RootReadContractCatalog(List.of(),List.of()),selected));
            accepted++;
        }
        assertTrue(accepted>=8);assertTrue(rejected>=2);
    }
    @Test void actualParameterizedFamilyRetainsSamplingAndRejectsLegacyBeforeDispatch()throws Exception {
        var data=originals();ObjectNode exact4=null,legacy=null;
        for(JsonNode row:data.path("rows")){if(row.path("kind").asText().equals("construction"))exact4=(ObjectNode)row.path("snapshot");else if(legacy==null)legacy=(ObjectNode)row.path("snapshot");}
        assertNotNull(exact4);assertNotNull(legacy);
        var input=CashObservationPublicCodec.current(PublicBindings.present(new RawJson(("{\"expected_revision\":"+exact4.path("revision")+",\"payment_sampling\":\"enable\",\"payment_window_contract\":\"same_owned_process_no_load_v1\"}").getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        var reads=new CashObservationReads(new CashObservationReads.Sources(SOURCE,SOURCE));var catalog=new RootReadContractCatalog(List.of(),reads.families());
        var selected=new CashObservationReads.Selection(frame(exact4),input,Optional.empty(),DEADLINE);var contract=reads.contract(catalog,selected);
        var fields=PublicDataJson.object(contract.prepare(selected.request(),"exact-parameterized-cash").additionalFields());
        assertEquals(3,fields.size());assertEquals("enable",fields.path("war_payment_sampling").asText());assertEquals("controlled-cash-fixture",fields.path("war_payment_machine_id").asText());assertEquals("same_owned_process_no_load_v1",fields.path("war_payment_window_contract").asText());
        var old=frame(legacy);var legacyInput=new Current(old.identity().frame().revision(),input.sampling(),input.window());
        assertThrows(IllegalArgumentException.class,()->new CashObservationReads.Selection(old,legacyInput,Optional.empty(),DEADLINE));
    }
    private static Request request(JsonNode row){var args=PublicBindings.present(PublicDataJson.encode(row.path("args")));return switch(row.path("kind").textValue()){
        case "current"->CashObservationPublicCodec.current(args);case "construction"->CashObservationPublicCodec.construction(args);default->CashObservationPublicCodec.termination(args);};}
    private static PlanningReadReceipt receipt(CashObservationReads.Selection s,JsonNode frame,String contractId)throws Exception {
        RawJson raw=PublicDataJson.encode(frame);String id=frame.path("request_id").textValue();var original=new NativeActionPort.AckReceived(id,true,Optional.of(PublicDataJson.encode(frame.path("result"))),raw,NativeWire.packet(raw.bytes()));
        var request=s.request();var guard=new PlanningReadGuard(new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,request.operation(),SOURCE,SOURCE,"controlled-cash",TIME,DEADLINE),true,true,true,"b".repeat(64));
        return new PlanningReadReceipt(request,contractId,id,guard,guard,original);
    }
    private static DriverObservationAssembler.Complete frame(ObjectNode snapshot){var nativeRevision=snapshot.path("native_revision").bigIntegerValue();var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(snapshot.path("played_character").path("character_id").bigIntegerValue(),nativeRevision,snapshot.path("date_raw").bigIntegerValue()),snapshot.path("snapshot_id").textValue(),snapshot.path("revision").bigIntegerValue(),"cash-fixture");
        var source=new G2Source("controlled-cash-fixture",TIME.toString(),snapshot.path("diagnostics").path("hello").path("expected_ck3_version").textValue(),SOURCE);var identity=new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        return new DriverObservationAssembler.Complete(identity,source,"cash-session",BigInteger.ONE,DriverJson.object(PublicDataJson.encode(snapshot).bytes(),DriverJson.MAX_NATIVE_BYTES),SOURCE,TIME,"b".repeat(64));}
    private static void same(JsonNode a,JsonNode b){assertEquals(new String(StrictJson.canonical(a),java.nio.charset.StandardCharsets.UTF_8),new String(StrictJson.canonical(b),java.nio.charset.StandardCharsets.UTF_8));}
    private ObjectNode originals()throws Exception {return originals(temporary);}
    static ObjectNode originals(Path temporary)throws Exception {
        String python=required("xar.native.producer.python"),source=required("xar.native.producer.source");Path output=temporary.resolve("cash.json"),errors=temporary.resolve("cash.stderr");
        var child=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL,source).redirectOutput(output.toFile()).redirectError(errors.toFile()).start();
        if(!child.waitFor(30,TimeUnit.SECONDS)){child.destroyForcibly();throw new java.io.IOException("actual cash producer process timeout");}
        if(child.exitValue()!=0)throw new java.io.IOException("original cash process failed: "+Files.readString(errors));
        return PublicDataJson.object(new RawJson(Files.readAllBytes(output)));
    }
    private static String required(String property){String s=System.getProperty(property);if(s==null||s.isBlank()||!Path.of(s).isAbsolute())throw new IllegalStateException("actual absolute original producer configuration required: "+property);return s;}
    private static final String ORIGINAL="""
        import copy,hashlib,json,runpy,sys
        from pathlib import Path
        from unittest.mock import patch
        source=Path(sys.argv[1]);base=source.resolve().parents[3]
        pins={
          source:'eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603',
          base/'src/xar_autoplayer/bridge/g2_private_query_transport.py':'02db15ca2b070f814df06cad10da2bb9b4c8e2e1aec621f9228a5ab12f971315',
          base/'tests/unit/test_construction_economic_outcome_v1.py':'f418549b473b3e4bc30114cd41bd7bacac6768c80ac225727de497c9e59542cd',
          base/'native_bridge/research/fixtures/ck3_12002_war_cash_python_provenance.json':'7cf26525828df5e5628f0be1c427eb03a470dcd941de2145916a8f5fa5b4f177',
          base/'src/xar_autoplayer/bridge/war_cash_private_transport_v1.py':'81ba0ca4c99b4f607f649712d996a63c0c044bff56a8e2fc4456f937c47f24c6',
          base/'src/xar_autoplayer/construction_economic_outcome_v1.py':'393bb0b905cf91be265fa9f3af32dbea07c73f27e35f5fa841fa5b9e8763a699',
          base/'src/xar_autoplayer/bridge/construction_monthly_budget_v1.py':'8bc0573083d6ab1e69bb6a04e30ad84e5f2c394742213d5ec263f37b9b357753',
          base/'tests/unit/test_construction_monthly_budget_v1.py':'bdd2ca9a328a6b534ede68e5de773cf73e0d6764bc2a7fa217d8746b93182933'}
        def verify():
            for path,sha in pins.items():
                raw=path.read_bytes()
                assert len(raw)<=2*1024*1024 and hashlib.sha256(raw).hexdigest()==sha
                assert path.read_bytes()==raw
        verify()
        manifest=base/'native_bridge/research/fixtures/ck3_12002_war_cash_python_provenance.json'
        for row in json.loads(manifest.read_bytes())['fixtures']:
            pins[manifest.parent/row['file']]=row['sha256']
        verify();sys.path.insert(0,str(base/'src'))
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.version_identity import require_exact_native_build
        cash_factory=runpy.run_path(str(base/'tests/unit/test_construction_monthly_budget_v1.py'))['cash_fixture']
        completed_factory=runpy.run_path(str(base/'tests/unit/test_construction_economic_outcome_v1.py'))['completed_receipt']
        class Driver:
            allow_private_war_cash_query=True;command_timeout_seconds=1.0
            query_war_cash_current_resources_private_v1=NativeHeadlessGameplayDriver.query_war_cash_current_resources_private_v1
            query_war_cash_termination_send_costs_private_v1=NativeHeadlessGameplayDriver.query_war_cash_termination_send_costs_private_v1
            query_construction_cash_outcome_private_v1=NativeHeadlessGameplayDriver.query_construction_cash_outcome_private_v1
            def __init__(self,value):
                self.value=copy.deepcopy(value);self.requests=[];self.endpoint=self.state=self;self.state_dir=base;self.frame=None
                self.snapshot=dict(paused=True,map_ready=True,revision=value['snapshot_revision']+1,native_revision=value['snapshot_revision'],snapshot_id=value.get('queried_snapshot_id','native:'+str(value['snapshot_revision'])),date_raw=value['date_raw'],episode_run_id='cash-fixture',episode_character_id=value['played_character_id'],played_character=dict(character_id=value['played_character_id'],alive=True),diagnostics=dict(bridge_pid=42,connection_generation=1,hello=dict(expected_ck3_version=value['game_version'],expected_ck3_sha256=value['executable_sha256'])))
            def take_snapshot(self):return copy.deepcopy(self.snapshot)
            def send(self,request):self.requests.append(copy.deepcopy(request))
            def wait_for_command_result(self,id,timeout):
                request=self.requests[-1];key='war_cash_current_resources' if request['step']=='query-war-cash-current-resources-v1' else 'war_cash_termination_send_costs'
                self.frame=dict(type='command_result',protocol_version=1,request_id=id,ok=True,result=dict(step=request['step'],accepted=True,status=self.value['status'],private_build=True,read_only=True,advertised=False,**{key:copy.deepcopy(self.value)}))
                return copy.deepcopy(self.frame)
        rows=[]
        def add(name,kind,value,material=None):
            driver=Driver(value);args=dict(expected_revision=driver.snapshot['revision']);row=dict(name=name,kind=kind,snapshot=driver.snapshot)
            if kind=='termination':args.update(war_id=value['war_id'],outcome=value['outcome'])
            if kind=='construction':args.update(reserve_gold_raw=3000000,existing_commitment_gold_raw=2000000,horizon_months=4);row['material']=material
            try:
                with patch('xar_autoplayer.construction_formal_consumer.read_construction_ledger',return_value={'applied':material} if material else {}):
                    row['expected']=getattr(driver,'query_'+('war_cash_current_resources_private_v1' if kind=='current' else 'war_cash_termination_send_costs_private_v1' if kind=='termination' else 'construction_cash_outcome_private_v1'))(**args)
                row['accepted']=True
            except Exception:row['accepted']=False
            row.update(args=args,frame=driver.frame);assert len(driver.requests)==1 and driver.frame is not None
            rows.append(row)
        fixture=base/'native_bridge/research/fixtures'
        for name in ('current-resources-normal','current-zero-normal','partial-resources-normal','drift-unavailable-normal'):
            add(name,'current',json.loads((fixture/('ck3_12002_war_cash_'+name+'.json')).read_text()))
        for name in ('termination-send-zero-normal','termination-send-unavailable-normal'):
            add(name,'termination',json.loads((fixture/('ck3_12002_war_cash_'+name+'.json')).read_text()))
        for material in ({},completed_factory()):add('durable-applied' if material else 'known-no-applied','construction',cash_factory(),material)
        bad=cash_factory();bad['player_monthly_net_income']['raw']=True;add('bool-net','current',bad)
        bad=cash_factory();bad['military_expenses']['current']['gold_raw']+=1;add('vector-mismatch','current',bad)
        verify();print(json.dumps(dict(rows=rows),allow_nan=False,separators=(',',':')))
        """;
}
