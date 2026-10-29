package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneCodec;

/** Exact archived Batch25 originals, used offline. No native call, Game action, Known LIFE reply or writer qualification. */
final class GovernanceCollectorOriginalSceneBoundTest {
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186";
    private static final String SNAPSHOT="c57ed74f981164eef3056ad6d040cad6b834501f8ad3fb78f5dcf5cf445e1984";
    private static final String DISPATCH="278b0b04d4f4c967078630f7868cb619dbb8fe4c33c35d974f63412a171769da";
    private static final String RESPONSE="4dab7ecb0ca6a8ae01dc5f30398d708351a794379ce06c95e1337c0a5a8541f7";
    private static final String RESOURCE_ROOT="/governance-scene-bound01/";
    private record Input(PlanningRequest request,Obj root,ExactRef rootOriginal,byte[] scene){}
    private static byte[] original(String sha)throws Exception{
        String configured=System.getProperty("xar.governance.scene.originals");
        if(configured!=null)return Files.readAllBytes(Path.of(configured).resolve(sha+".bin"));
        try(InputStream stream=GovernanceCollectorOriginalSceneBoundTest.class.getResourceAsStream(RESOURCE_ROOT+sha+".bin")){
            assertNotNull(stream,"retained Batch25 classpath original is absent: "+sha);
            return stream.readAllBytes();
        }
    }
    private static String originalPath(String sha){
        String configured=System.getProperty("xar.governance.scene.originals");
        return configured==null?"classpath:"+RESOURCE_ROOT+sha+".bin":Path.of(configured).resolve(sha+".bin").toString();
    }
    private static Input input()throws Exception{
        byte[] snapshotRaw=original(SNAPSHOT);
        assertEquals(70468,snapshotRaw.length);assertEquals(SNAPSHOT,ActionCodec.sha256(snapshotRaw));
        Obj snapshot=DriverJson.object(snapshotRaw,DriverJson.MAX_NATIVE_BYTES);
        byte[] dispatchRaw=original(DISPATCH);assertEquals(DISPATCH,ActionCodec.sha256(dispatchRaw));
        var dispatch=StrictJson.parse(dispatchRaw);var session=dispatch.get("custody").get("session");
        assertEquals(MACHINE,StrictJson.text(session.get("machine_id")));assertEquals("64",StrictJson.text(session.get("connection_generation")));
        byte[] packet=original(RESPONSE);assertEquals(13061,packet.length);assertEquals(RESPONSE,ActionCodec.sha256(packet));
        assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        var response=StrictJson.parse(java.util.Arrays.copyOfRange(packet,4,packet.length));
        assertEquals(StrictJson.text(dispatch.get("request_id")),StrictJson.text(response.get("request_id")));StrictJson.trueValue(response.get("ok"));
        var nativeRevision=integer(snapshot.get("native_revision"),"actual native revision");var date=integer(snapshot.get("date_raw"),"actual date");
        Obj nativeResult=DriverJson.object(StrictJson.canonical(response.get("result")),DriverJson.MAX_NATIVE_BYTES);
        Obj originalRoot=CampaignRootContextJson.normalizeNativeResult(nativeResult,date,nativeRevision);
        var observed=object(originalRoot.get("campaign_root_context"),"whole ROOT");
        var actor=integer(object(snapshot.get("played_character"),"played character").get("character_id"),"actor");
        assertEquals(BigInteger.valueOf(209),nativeRevision);assertEquals(nativeRevision,integer(observed.get("snapshot_revision"),"ROOT revision"));
        assertEquals(date,integer(observed.get("date_raw"),"ROOT date"));assertEquals(actor,integer(observed.get("player_character_id"),"ROOT actor"));
        assertEquals(nativeResult.members().keySet(),originalRoot.members().keySet());
        List<Obj> history=array(snapshot.get("native_command_history"),"complete original Driver history").stream().map(row->object(row,"original history row")).toList();
        assertEquals(2,history.size());var originalRef=new ExactRef(originalPath(SNAPSHOT),snapshotRaw.length,SNAPSHOT);
        var source=new G2Source(MACHINE,StrictJson.text(dispatch.get("custody").get("response_received").get("observed_at")),"retained Batch25 offline scene",originalRef);
        var id=new ObservationIdentity(MACHINE,GameGeneration.fromJson(session.get("game")),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(actor,nativeRevision,date),text(snapshot.get("snapshot_id"),"snapshot id"),integer(snapshot.get("revision"),"public revision"),text(snapshot.get("episode_run_id"),"logical episode")),1);
        var observation=new PlanningObservation(snapshot,history,Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),true);
        var request=new PlanningRequest(id,source,StrictJson.text(session.get("session_id")),Instant.parse(StrictJson.text(dispatch.get("custody").get("response_received").get("observed_at"))).plusSeconds(30),observation);
        List<Value> rows=new ArrayList<>(history);rows.add(new Obj(Map.of("command",new Text("query-campaign-root-context-v1"),"ok",new Bool(true),"result",originalRoot)));
        Obj scene=new Obj(Map.of("schema",new Text(ConstructionSceneCodec.SCENE_SCHEMA),"snapshot",snapshot,"history",new Arr(rows)));
        byte[] sceneRaw=DriverJson.encode(scene);assertTrue(sceneRaw.length>ConstructionSceneCodec.MAX_BYTES);
        return new Input(request,originalRoot,new ExactRef(originalPath(RESPONSE),packet.length,RESPONSE),sceneRaw);
    }
    @Test void archivedFullSnapshotAndHistoryReachTheActualFormalPortAfterRootSceneAdmission()throws Exception{
        var input=input();var formalCalls=new AtomicInteger();var rootCalls=new AtomicInteger();
        var request=input.request();byte[] before=DriverJson.encode(request.observations().snapshot());var history=List.copyOf(request.observations().history());
        var session=forbiddenSession();var borrowed=new GovernanceBorrowedSession(session,Path.of("D:/test-memory/unopened-governance-writer.lock"),same->{throw new AssertionError("scene DATA must not qualify a writer");});
        var reads=new GovernanceCollector.Reads(Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
        var collector=new GovernanceCollector(new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest current){throw new AssertionError("no Native query in an offline scene case");}},
                new ForbiddenArchive(),current->{throw new AssertionError("scene collection cannot read durable state");},reads,borrowed,
                new GovernanceCollector.LifestyleReadPort(){
                    @Override public GovernanceObservationSupplier.Read<Obj> formal(PlanningRequest current){
                        assertSame(request,current);assertEquals(history,current.observations().history());assertArrayEquals(before,DriverJson.encode(current.observations().snapshot()));
                        formalCalls.incrementAndGet();return new GovernanceObservationSupplier.Unavailable<>("controlled formal port reached; no LIFE Native result requested");
                    }
                    @Override public GovernanceObservationSupplier.Read<Obj> stockFocus(PlanningRequest current,String target){throw new AssertionError("no formal Known or focus/action was produced");}
                },current->{assertSame(request,current);rootCalls.incrementAndGet();return new GovernanceObservationSupplier.Known<>(input.root(),List.of(input.rootOriginal()));});
        var actual=collector.lifestyle(request,"martial_authority_focus",true);
        var unavailable=assertInstanceOf(GovernanceObservationSupplier.Unavailable.class,actual);
        assertEquals("controlled formal port reached; no LIFE Native result requested",unavailable.reason());
        assertEquals(1,rootCalls.get());assertEquals(1,formalCalls.get());assertEquals(history,request.observations().history());
        assertArrayEquals(before,DriverJson.encode(request.observations().snapshot()));
    }
    @Test void theExternalByteEntryRetainsItsExisting64KiBBound()throws Exception{
        var input=input();var rejected=assertThrows(IllegalArgumentException.class,()->ConstructionSceneCodec.decodeScene(input.scene()));
        assertEquals("bounded nonempty UTF-8 JSON required",rejected.getMessage());
        assertEquals(65536,ConstructionSceneCodec.MAX_BYTES);
    }
    private static ContinuityStorePort.Session forbiddenSession(){return new ContinuityStorePort.Session(){
        @Override public WriterContracts.Head head(){throw new AssertionError("no writer head read");}
        @Override public void requireWriter(Path lock){throw new AssertionError("no physical writer qualification");}
        @Override public WriterContracts.Pin capturePin(ExactRef ref,int maximum){throw new AssertionError("no pin capture");}
        @Override public void verifyPin(WriterContracts.Pin pin){throw new AssertionError("no pin verification");}
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("no ledger preview");}
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("no ledger commit");}
        @Override public ExactRef persistedHead(){throw new AssertionError("no persisted head");}
    };}
    private static final class ForbiddenArchive implements ActionPorts.OutcomeArchive{
        private AssertionError unused(){return new AssertionError("offline scene cannot access archive or Native runtime");}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw unused();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){throw unused();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw unused();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw unused();}
        @Override public NativeRequest loadRequest(ExactRef ref){throw unused();}
        @Override public ExactRef requestReferenceOf(NativeRequest value){throw unused();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw unused();}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){throw unused();}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){throw unused();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw unused();}
        @Override public ActionRecord loadRecord(ExactRef ref){throw unused();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw unused();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw unused();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){throw unused();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw unused();}
        @Override public ExactRef preserveMaterial(RawJson value){throw unused();}
        @Override public RawJson loadMaterial(ExactRef ref){throw unused();}
        @Override public ExactRef materialReferenceOf(RawJson value){throw unused();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unused();}
        @Override public byte[] loadNativeFrame(ExactRef ref){throw unused();}
    }
}
