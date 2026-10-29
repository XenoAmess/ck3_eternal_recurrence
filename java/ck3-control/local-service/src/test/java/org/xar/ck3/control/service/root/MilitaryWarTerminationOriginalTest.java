package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Real retained original Driver producer -> registered Army decoder -> ordinary dispatcher -> actual history and cold replay.
 * In-memory transport and archive are software fixtures; they grant no physical Root, native effect or Game qualification. */
final class MilitaryWarTerminationOriginalTest {
    private static final ExactRef SOURCE=new ExactRef("synthetic-war-exit-source",1,"a".repeat(64));
    @Test void actualOriginalOptionsAndUnsupportedTermsReachOrdinaryHistoryWithoutANewReadModel()throws Exception {
        JsonNode captured=corpus();int good=0,bad=0;
        for(JsonNode row:captured.path("cases")) {
            var input=new Held(row);var wars=new ArmyWarReads(SOURCE,SOURCE,input);
            var catalog=new RootReadContractCatalog(List.of(),wars.families());
            var parsed=MilitaryNativeReadDispatcher.termination(input.operation(),input.revision()).orElseThrow();
            assertEquals(77,parsed.warId().intValueExact());
            var selected=new ArmyWarReads.Selection(parsed,input.frame,Optional.empty());
            if(!row.path("expected").path("accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class,()->MilitaryNativeReadDispatcher.termination(wars,input,input.session,catalog,selected),row.path("name").textValue());
                assertEquals(1,input.nativeCalls);bad++;continue;
            }
            var returned=MilitaryNativeReadDispatcher.termination(wars,input,input.session,catalog,selected);
            if(!(returned instanceof PlanningReadResult.Known<Obj> actual))throw new AssertionError("actual original exit read unavailable: "+returned);
            Obj normalized=actual.value();
            assertEquals(canonical(row.path("expected").path("result")),canonical(OpportunityJson.toNode(normalized)));
            var contract=wars.contract(catalog,selected);var receipt=actual.receipt();
            var typed=new PlanningReadResult.Known<>(contract.replay(receipt),receipt,actual.originalReceipt());
            assertEquals(normalized,typed.value().normalizedResult());
            var candidate=DriverReadHistoryRowProducer.prepare(input.archive,catalog,contract,typed,1);
            assertEquals(normalized,candidate.row().result());
            assertEquals(candidate.row(),DriverReadHistoryRowProducer.decode(candidate.row().encode()));
            assertEquals(typed,DriverReadHistoryRowProducer.replayCanonical(input.archive,catalog,contract,candidate.row()));
            assertEquals(typed.originalReceipt(),DriverReadHistoryRowProducer.replay(input.archive,catalog,contract,typed,candidate).readReference());
            assertEquals(1,input.nativeCalls,"pure history replay must not submit another native read");
            assertEquals(row.path("kind").textValue().equals("options")?DriverReadHistoryRowProducer.Kind.TERMINATION_OPTIONS:DriverReadHistoryRowProducer.Kind.TERMINATION_TERMS,candidate.provenance().kind());
            if(row.path("kind").textValue().equals("terms"))assertEquals(new OpportunityJson.Text("unsupported"),normalized.get("status"));
            Obj corrupted=candidate.row().toJson().with("result",normalized.with("query_sequence",new OpportunityJson.Bool(true)));
            assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(OpportunityJson.encode(corrupted)));
            var wrong=new ArmyWarReads.Selection(new ArmyCalls.War(parsed.method(),input.revision(),BigInteger.valueOf(3)),input.frame,Optional.empty());
            assertThrows(IllegalArgumentException.class,()->MilitaryNativeReadDispatcher.termination(wars,input,input.session,catalog,wrong));
            good++;
        }
        assertEquals(2,good);assertEquals(10,bad);verifySources();
    }
    @Test void canonicalSelectionRefusesAliasesOverflowAndOtherNativeFamilies() {
        var revision=new ArmyCalls.Revision(new Present<>(BigInteger.TWO));
        assertEquals(PublicMethod.QUERY_WAR_TERMINATION_OPTIONS,MilitaryNativeReadDispatcher.termination("query-war-termination-options-2147483647",revision).orElseThrow().method());
        assertEquals(PublicMethod.QUERY_WAR_TERMINATION_TERMS,MilitaryNativeReadDispatcher.termination("query-war-termination-terms-v1-1",revision).orElseThrow().method());
        for(String bad:List.of("query-war-termination-options-0","query-war-termination-options-01","query-war-termination-options-2147483648","query-war-termination-options--1","query-war-termination-options-1.0","query-war-termination-options-1-extra","query-war-termination-terms-v1-true","query-war-termination-terms-v1-1 ","query-declarable-wars","query-war-termination-options-"+"9".repeat(50000)))
            assertTrue(MilitaryNativeReadDispatcher.termination(bad,revision).isEmpty());
    }
    private static final class Held implements PlanningReadPort {
        final ArmyRetreatFrames.Current frame;final ContinuityStorePort.Session session;final ActionPorts.OutcomeArchive archive;
        final Obj original;final Map<ExactRef,RawJson> materials=new HashMap<>();final Map<ExactRef,PlanningReadReceipt> receipts=new HashMap<>();int nativeCalls;
        Held(JsonNode row) {
            Obj snapshot=DriverJson.object(StrictJson.canonical(row.path("snapshot")),DriverJson.MAX_NATIVE_BYTES);
            original=DriverJson.object(StrictJson.canonical(row.path("native")),DriverJson.MAX_NATIVE_BYTES);
            var source=new G2Source("synthetic-test-no-game","2026-10-24T00:00:00Z","1.20.0.4",SOURCE);
            var proposal=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(3),BigInteger.valueOf(77)),"native:3",BigInteger.TWO,"termination-fixture");
            var before=new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),proposal,1);
            frame=new ArmyRetreatFrames.Current(new Complete(before,source,"termination-fixture-session",BigInteger.ONE,snapshot,SOURCE,Instant.parse("2026-10-24T00:00:00Z"),"b".repeat(64)),Instant.parse("2026-10-24T00:01:00Z"));
            session=(ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.Session.class},(p,m,a)->{throw new AssertionError("decoder cannot mutate writer: "+m.getName());});
            archive=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(p,m,a)->switch(m.getName()) {
                case "withSession"->p;
                case "loadRead"->receipts.get(a[0]);
                case "readReferenceOf"->receipts.entrySet().stream().filter(e->e.getValue().equals(a[0])).map(Map.Entry::getKey).findFirst().orElseThrow();
                case "preserveMaterial"->{RawJson raw=(RawJson)a[0];ExactRef ref=materialReference(raw);materials.put(ref,raw);yield ref;}
                case "materialReferenceOf"->materialReference((RawJson)a[0]);
                case "loadMaterial"->materials.get(a[0]);
                default->throw new AssertionError("unexpected archive operation: "+m.getName());
            });
        }
        String operation(){return OpportunityJson.text(original.get("step"),"native original step");}
        ArmyCalls.Revision revision(){return new ArmyCalls.Revision(new Present<>(BigInteger.TWO));}
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){return read(session,contract,request);}
        @Override public <T>PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request) {
            assertSame(session,same);String id="original-exit-"+(++nativeCalls);contract.prepare(request,id);
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);envelope.set("result",OpportunityJson.toNode(original));
            var raw=new RawJson(StrictJson.canonical(envelope));
            final byte[] packet;
            try {packet=NativeWire.packet(raw.bytes());}
            catch(java.io.IOException failure){throw new AssertionError("synthetic native packet encoding failed",failure);}
            var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(OpportunityJson.encode(original))),raw,packet);
            var context=frame.context();var guard=new PlanningReadGuard(new GuardEvidence(context.before(),context.source(),context.sessionId(),BigInteger.ONE,request.operation(),SOURCE,SOURCE,"synthetic-read-authority",frame.actual().observedAt(),request.deadline()),true,true,true,"b".repeat(64));
            var receipt=new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
            ExactRef ref=new ExactRef("synthetic-original-read-"+id,raw.bytes().length,DriverJson.sha256(raw.bytes()));receipts.put(ref,receipt);
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,ref);
        }
        static ExactRef materialReference(RawJson raw){return new ExactRef("synthetic-material-"+DriverJson.sha256(raw.bytes()),raw.bytes().length,DriverJson.sha256(raw.bytes()));}
    }
    private static String canonical(JsonNode node){return new String(StrictJson.canonical(node),StandardCharsets.UTF_8);}
    private static JsonNode corpus()throws Exception {
        verifySources();String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");assertNotNull(repository);assertNotNull(python,"actual original oracle executable required");
        String program="""
                import copy,json,runpy,threading,sys
                from pathlib import Path
                repo=Path(sys.argv[1]);sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
                import xar_autoplayer.bridge.native_driver as original
                from xar_autoplayer.bridge.version_identity import CK3_12004
                make_options=runpy.run_path(str(repo/'ck3_autonomous_player/tests/unit/test_war_termination_contract.py'))['_termination_options']
                war=dict(war_id=77,player_side='attacker',player_is_primary_war_leader=True,primary_opponent_character_id=202,targeted_title_ids=[8,3],player_relative_war_score=41)
                other=dict(war_id=3,player_side='defender',player_is_primary_war_leader=None,primary_opponent_character_id=None,targeted_title_ids=[],player_relative_war_score=-7)
                snapshot=dict(snapshot_id='native:3',revision=2,native_revision=3,date_raw=77,paused=True,map_ready=True,episode_run_id='termination-fixture',episode_character_id=101,played_character=dict(character_id=101,alive=True),active_wars=[war,other],diagnostics=dict(connection_generation=1,bridge_pid=42,hello=dict(expected_ck3_version=CK3_12004.game_version,expected_ck3_sha256=CK3_12004.executable_sha256)))
                terms=dict(schema_version=1,status='unsupported',war_id=77,casus_belli=dict(database_index=91,canonical_key='raiktor_claim_cb'),supported_slice='claim_cb_claim_disposition',reason='casus_belli_not_claim_cb',readiness=dict(ready=False),provenance=dict(game_version=CK3_12004.game_version,executable_sha256=CK3_12004.executable_sha256,native_reader='CWar+0x270/+0x290;0x2B9ECB0',present_claim_lifecycle='present_only_vtable_slot_0_delete_flags_0',claim_script_sha256='887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4'))
                class Source:
                    def __init__(self,result,frame):self.result=result;self.frame=frame;self._driver_state_lock=threading.Lock();self._war_termination_options={};self._war_termination_terms={}
                    def _execute_primitive_step(self,*args,**kwargs):return copy.deepcopy(self.result)
                    def take_internal_semantic_snapshot(self):return copy.deepcopy(self.frame)
                rows=[]
                def add(kind,name,edit=None):
                    frame=copy.deepcopy(snapshot)
                    result=dict(step='query-war-termination-options-77' if kind=='options' else 'query-war-termination-terms-v1-77',accepted=True,status='available' if kind=='options' else 'unsupported',query_sequence=13,backend_id='native-headless')
                    result['war_termination_options' if kind=='options' else 'war_termination_terms']=make_options(war_id=77) if kind=='options' else copy.deepcopy(terms)
                    if edit:edit(result,frame)
                    producer=Source(result,frame)
                    try:
                        if kind=='options':value=original.NativeHeadlessGameplayDriver._execute_war_termination_step(producer,result['step'],starting=frame,selected_revision=2,query_war_id=77,surrender_war_id=None,white_peace_war_id=None)
                        else:value=original.NativeHeadlessGameplayDriver._execute_war_termination_terms_query(producer,result['step'],starting=frame,selected_revision=2,war_id=77)
                        expected=dict(accepted=True,result=value)
                    except Exception:expected=dict(accepted=False)
                    native=copy.deepcopy(result);native.pop('backend_id')
                    rows.append(dict(name=name,kind=kind,snapshot=frame,native=native,expected=expected))
                add('options','complete-original-options-query-context')
                add('terms','actual4-unsupported-original-session-is-unavailable')
                add('options','missing-query-sequence',lambda r,s:r.pop('query_sequence'))
                add('options','bool-query-sequence',lambda r,s:r.__setitem__('query_sequence',True))
                add('options','wrong-outer-status',lambda r,s:r.__setitem__('status','unsupported'))
                add('options','wrong-active-war-side',lambda r,s:s['active_wars'][0].__setitem__('player_side','defender'))
                add('options','wrong-active-war-score',lambda r,s:s['active_wars'][0].__setitem__('player_relative_war_score',40))
                add('options','war-ended-before-read',lambda r,s:s.__setitem__('active_wars',[]))
                add('terms','unsupported-outer-union-disagrees',lambda r,s:r.__setitem__('status','available'))
                add('terms','missing-query-sequence',lambda r,s:r.pop('query_sequence'))
                add('terms','wrong-exact-build',lambda r,s:r['war_termination_terms']['provenance'].__setitem__('executable_sha256','A'*64))
                add('terms','war-ended-before-read',lambda r,s:s.__setitem__('active_wars',[]))
                print(json.dumps({'cases':rows},allow_nan=False))
                """;
        var builder=new ProcessBuilder(python,"-B","-X","utf8","-c",program,repository).directory(Path.of(repository).toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");var process=builder.start();
        try(var readers=java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
            var out=readers.submit(()->process.getInputStream().readNBytes(1048577));var err=readers.submit(()->process.getErrorStream().readNBytes(1048577));
            try{process.getOutputStream().close();assertTrue(process.waitFor(45,java.util.concurrent.TimeUnit.SECONDS),"original producer timeout is RED");var bytes=out.get(5,java.util.concurrent.TimeUnit.SECONDS);var error=err.get(5,java.util.concurrent.TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(error,StandardCharsets.UTF_8));assertTrue(bytes.length<=1048576);return StrictJson.parse(bytes,1048576);}
            finally{if(process.isAlive())process.destroyForcibly();}
        }
    }
    private static void verifySources()throws Exception {
        String configured=System.getProperty("xar.repository.root");assertNotNull(configured,"actual original source root required");Path root=Path.of(configured).toRealPath();
        for(String[] pin:new String[][]{{"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},{"ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py","b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937"},{"ck3_autonomous_player/tests/unit/test_war_termination_contract.py","be4d7dbad8499632d433b43d6edbba901fba71ec848a3a6735911db07a8d5fc0"}}) {
            Path file=root.resolve(pin[0]).toRealPath();assertTrue(file.startsWith(root));assertEquals(pin[1],HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))),"actual original producer source drift");
        }
    }
}
