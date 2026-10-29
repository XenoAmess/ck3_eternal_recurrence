package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.advance.GenericPublicPauseRecovery.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure software receipt/SEM DATA. These cases never construct a private Root/Managed/once qualification. */
final class GenericPublicPauseRecoveryTest {
    private static final Instant T=Instant.parse("2026-10-24T12:00:00Z");
    private static final String MACHINE="public-pause-policy-software";
    private static final ExactRef SOURCE=ref("policy-source");
    private static final G2Source G2=new G2Source(MACHINE,T.toString(),"1.20.0.4",SOURCE);
    private static RawJson raw(String s){return new RawJson(s.getBytes(StandardCharsets.UTF_8));}
    private static ExactRef ref(String s){byte[] b=s.getBytes(StandardCharsets.UTF_8);return new ExactRef("software/"+s,b.length,ActionCodec.sha256(b));}
    private static ObservationIdentity identity(long revision){
        return new ObservationIdentity(MACHINE,new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(revision),BigInteger.valueOf(1000)),
                        "native-"+revision,BigInteger.valueOf(revision),"episode-software"),1);
    }
    private static ActionCommand command(String id,long revision,boolean parent){
        var before=identity(revision);var operation=parent?OPERATION:new OperationKey(PUBLIC_STEP);
        return new ActionCommand(id,before,G2,"session-software",operation,new Obj(Map.of()),
                parent?expected(before,G2):new ExpectedPostcondition(1,before,G2,PauseConfirmation.OBSERVER,PauseConfirmation.expectedValues()),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),T.plusSeconds(30));
    }
    private static ObjectNode sem(long revision,boolean paused){
        var row=StrictJson.object().put("snapshot_id","native-"+revision).put("revision",revision).put("native_revision",revision)
                .put("date_raw",1000).put("paused",paused).put("map_ready",true).put("episode_run_id","episode-software")
                .put("episode_character_id",29829).put("local_player_id",0).put("speed",3);
        row.putNull("one_life_terminal_reason");row.putNull("active_event");row.putNull("pending_character_interaction");
        row.putObject("played_character").put("character_id",29829).put("alive",true).put("source","native");
        var d=row.putObject("diagnostics").put("connected",true).put("bridge_pid",123).put("connection_generation",1);
        d.putObject("hello").put("ck3_build_match",true).put("expected_ck3_version",ExactCk3Build.CK3_12004.version())
                .put("expected_ck3_sha256",ExactCk3Build.CK3_12004.executableSha256()).put("game_adapter_id","ck3-1.20.0.4-msvc-x64")
                .put("pid",123).put("connection_generation",1);
        return row;
    }
    private static Snapshot snapshot(ObjectNode v){
        byte[] b=DriverJson.encodeNode(v);return GenericPublicPauseRecovery.snapshot(DriverJson.object(b,RawJson.MAXIMUM_BYTES),new ExactRef("software/sem-"+ActionCodec.sha256(b),b.length,ActionCodec.sha256(b)));
    }
    private static ActionReceipt rejected(String error){
        var c=command("actual-software-first",1,false);String id="software-request-1";
        var guard=new GuardEvidence(c.before(),G2,c.sessionId(),BigInteger.ONE,c.operation(),ref("native"),ref("hello"),"DATA-only",T,T.plusSeconds(30));
        var attempt=new ActionState.Attempt(id,T,guard,new NativeRequest(PUBLIC_STEP,Optional.empty(),raw("{}")));
        RawJson frame=raw("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+id+"\",\"ok\":false,\"error\":\""+error+"\"}");
        byte[] original=frame.bytes();
        var ack=new NativeActionPort.AckReceived(id,false,Optional.empty(),frame,original,
                Optional.of(new NativeActionPort.OutboundPacket(id,raw("{\"type\":\"execute_step\",\"request_id\":\""+id+"\",\"step\":\"pause-map\"}").bytes())));
        return new ActionReceipt(1,1,c,ActionCodec.bodySha256(c),new ActionState.Settled(attempt,ack,new ActionState.Rejected(id,error,ref("rejection"))));
    }
    private static AwaitFresh waiting(){
        return assertInstanceOf(AwaitFresh.class,afterFirst(snapshot(sem(1,false)),rejected(ControlSequenceObservation.MAP_UNAVAILABLE),T.plusSeconds(30),T));
    }
    @Test void realNegativeAckDataDrivesFreshAlreadyPausedBranchAndReplayReport()throws Exception{
        AwaitFresh first=waiting();Snapshot fresh=snapshot(sem(2,true));
        Completed done=assertInstanceOf(Completed.class,afterRefresh(first,fresh,T.plusSeconds(1)));
        assertEquals(ControlSequenceObservation.Mode.ALREADY_PAUSED_AFTER_REJECTION,done.mode());
        assertEquals(1,done.partial().attempts().size());assertEquals(done,replay(done));
        var receipt=done.partial().attempts().getFirst().receipt().orElseThrow();ExactRef canonical=ref("canonical-first");
        byte[] encoded=encode(done,x->{assertEquals(receipt,x);return canonical;});
        var loaded=decode(encoded,new ReplayReader(){
            public Snapshot snapshot(ExactRef ref){return ref.equals(fresh.originalSemantic())?fresh:first.partial().starting();}
            public ActionReceipt receipt(ExactRef ref){assertEquals(canonical,ref);return receipt;}
        });
        assertEquals(done,loaded);
        var result=StrictJson.parse(result(done,List.of(Optional.empty())).bytes());
        assertTrue(result.get("accepted").booleanValue());assertEquals("already_paused",result.get("status").textValue());
        assertTrue(result.get("map_control_recovery").get("postcondition_verified").booleanValue());
        var tampered=(ObjectNode)StrictJson.parse(encoded);tampered.put("mode","RETRIED_PAUSE");
        assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(tampered),new ReplayReader(){
            public Snapshot snapshot(ExactRef ref){return ref.equals(fresh.originalSemantic())?fresh:first.partial().starting();}
            public ActionReceipt receipt(ExactRef ref){return receipt;}
        }));
    }
    @Test void exactErrorFreshnessOwnerAndDeadlineAreRequiredBeforeOneRetry(){
        assertInstanceOf(Original.class,afterFirst(snapshot(sem(1,false)),rejected("other native rejection"),T.plusSeconds(30),T));
        var first=waiting();
        assertInstanceOf(AwaitFresh.class,afterRefresh(first,snapshot(sem(1,false)),T.plusSeconds(1)));
        var noNative=sem(2,false);noNative.put("native_revision",1);
        assertEquals(FailureReason.NO_FRESH_SEMANTIC_FRAME,assertInstanceOf(Failed.class,afterRefresh(first,snapshot(noNative),T.plusSeconds(1))).reason());
        var changed=sem(2,false);changed.put("active_event","different actual event");
        assertEquals(FailureReason.OWNER_CHANGED_BEFORE_RETRY,assertInstanceOf(Failed.class,afterRefresh(first,snapshot(changed),T.plusSeconds(1))).reason());
        Retry retry=assertInstanceOf(Retry.class,afterRefresh(first,snapshot(sem(2,false)),T.plusSeconds(1)));
        assertEquals(BigInteger.TWO,retry.expectedNativeRevision());assertTrue(retry.callerPublicRevision().isEmpty());
        Failed unresolved=afterRetryFailure(retry,"original-request-two","actual transport unknown",T.plusSeconds(2));
        assertTrue(unresolved.partial().needsOriginalReconciliation());assertEquals(2,unresolved.partial().attempts().size());
        assertEquals(unresolved,replay(unresolved));
        assertEquals(FailureReason.DEADLINE_BEFORE_RETRY,assertInstanceOf(Failed.class,afterRefresh(first,snapshot(sem(2,false)),T.plusSeconds(30))).reason());
    }
    @Test void unknownAndMissingOrWrongIntegerTypesNeverTurnIntoRetry(){
        var c=command("unknown-software-child",1,false);
        var unknown=new ActionReceipt(1,1,c,ActionCodec.bodySha256(c),new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual unknown",List.of()));
        assertInstanceOf(Original.class,afterFirst(snapshot(sem(1,false)),unknown,T.plusSeconds(30),T));
        var invalid=sem(1,false);invalid.put("episode_character_id",true);
        assertTrue(snapshot(invalid).owner().isEmpty());
        invalid=sem(1,false);invalid.put("date_raw",new java.math.BigDecimal("1000.0"));assertTrue(snapshot(invalid).owner().isEmpty());
        var missing=sem(1,false);missing.remove("episode_character_id");assertTrue(snapshot(missing).owner().isEmpty());
        var explicitNull=sem(1,false);explicitNull.putNull("episode_character_id");assertTrue(snapshot(explicitNull).owner().isEmpty());
    }
    @Test void nativeCampaignOwnerDoesNotRequireOrdinaryEpisodeCharacter(){
        var managed=sem(1,false);managed.put("episode_projection","native_campaign").put("format_version",1)
                .put("backend_id","native-headless").put("source","injected-dll-named-pipe");managed.putNull("episode_run_id");managed.remove("episode_character_id");
        managed.putObject("managed_campaign_run_binding").put("run_id","actual-run").put("state_dir","D:/software-campaign")
                .put("bridge_pipe","actual-pipe").put("host_path","D:/software-host").put("frozen_argv_sha256","a".repeat(64));
        ((ObjectNode)managed.get("diagnostics")).put("pipe_name","actual-pipe");
        assertInstanceOf(ManagedCampaignOwner.class,snapshot(managed).owner().orElseThrow());
        var later=managed.deepCopy();later.put("revision",2).put("native_revision",2).put("date_raw",1001);
        assertTrue(sameOwner(snapshot(managed),snapshot(later)));
        later.put("speed",4);assertFalse(sameOwner(snapshot(managed),snapshot(later)));
    }
    @Test void parentProofRoundTripPreservesOriginalCallerAndNamedSemanticDriverRole(){
        ActionCommand parent=command("software-parent",1,true);ExactRef nativeRef=ref("before-native"),driverFacts=ref("driver-facts"),runtime=ref("runtime"),product=ref("product"),proofRef=ref("parent-proof");
        var proof=new ParentProof(parent,raw("{\"step\":\"pause-map\",\"arguments\":{},\"extension\":null}"),nativeRef,driverFacts,runtime,product,List.of(runtime,product),9007199254740993L,"b".repeat(64));
        byte[] bytes=proof.encode();assertEquals("9007199254740993",StrictJson.parse(bytes).get("writer_sequence").textValue());
        var decoded=ParentProof.decode(bytes);assertArrayEquals(bytes,decoded.encode());assertArrayEquals(proof.originalCaller().bytes(),decoded.originalCaller().bytes());
        var guard=new GuardEvidence(parent.before(),G2,parent.sessionId(),BigInteger.ONE,OPERATION,nativeRef,ref("capability"),"not-a-proof-locator",T,T.plusSeconds(30),List.of(proofRef));
        assertTrue(decoded.matchesGuard(guard,driverFacts,proofRef));assertFalse(decoded.matchesGuard(guard,ref("full-driver-not-manifest"),proofRef));
        var row=(ObjectNode)StrictJson.parse(bytes);row.put("writer_sequence",9007199254740993L);
        ObjectNode wrongNumber=row;assertThrows(IllegalArgumentException.class,()->ParentProof.decode(StrictJson.canonical(wrongNumber)));
        row=(ObjectNode)StrictJson.parse(bytes);row.put("catalog_handler","status");
        ObjectNode wrong=row;assertThrows(IllegalArgumentException.class,()->ParentProof.decode(StrictJson.canonical(wrong)));
    }
    @Test void validLargeOriginalCallerUsesTheDeclaredParentProofBudget(){
        var caller=StrictJson.object().put("step","pause-map").put("extension","x".repeat(62000));
        var proof=new ParentProof(command("large-software-parent",1,true),new RawJson(StrictJson.canonical(caller)),
                ref("large-native"),ref("large-driver-facts"),ref("large-runtime"),ref("large-product"),
                List.of(ref("large-runtime"),ref("large-product")),1,"c".repeat(64));
        byte[] encoded=proof.encode();assertTrue(encoded.length>StrictJson.INPUT_MAX_BYTES);
        assertArrayEquals(encoded,ParentProof.decode(encoded).encode());
        assertTrue(encoded.length<=256*1024);
    }
    private static ActionReceipt pausedSecondData(){
        var c=command("actual-software-second",2,false);String id="software-request-2";
        var guard=new GuardEvidence(c.before(),G2,c.sessionId(),BigInteger.ONE,c.operation(),ref("second-native"),ref("hello"),"DATA-only",T.plusSeconds(1),T.plusSeconds(30));
        var attempt=new ActionState.Attempt(id,T.plusSeconds(1),guard,new NativeRequest(PUBLIC_STEP,Optional.empty(),raw("{}")));
        RawJson frame=raw("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+id+"\",\"ok\":true,\"result\":{\"paused\":true}}");
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(raw("{\"paused\":true}")),frame,frame.bytes(),
                Optional.of(new NativeActionPort.OutboundPacket(id,raw("{\"step\":\"pause-map\"}").bytes())));
        ExactRef push=ref("software-push-3");var after=identity(3);
        var observation=new ActionState.EffectObservation(after,G2,c.sessionId(),PauseConfirmation.OBSERVER,PauseConfirmation.actualValues(),
                new ObservationProvenance.Push(after.frame().snapshotId(),after.frame().identity().nativeRevision(),push),T.plusSeconds(2),push,List.of(ref("software-control-basis")));
        return new ActionReceipt(1,2,c,ActionCodec.bodySha256(c),new ActionState.Settled(attempt,ack,new ActionState.PauseConfirmed(observation)));
    }
    private static Decision roundTrip(Decision data)throws Exception{
        var p=data.partial();var slots=new java.util.HashMap<ExactRef,Snapshot>();slots.put(p.starting().originalSemantic(),p.starting());
        p.refreshed().ifPresent(x->slots.put(x.originalSemantic(),x));p.ending().ifPresent(x->slots.put(x.originalSemantic(),x));
        var receipts=new java.util.HashMap<ExactRef,ActionReceipt>();
        byte[] encoded=encode(data,r->{ExactRef key=ref("canonical-"+r.command().actionId());receipts.put(key,r);return key;});
        return decode(encoded,new ReplayReader(){public Snapshot snapshot(ExactRef key){return java.util.Objects.requireNonNull(slots.get(key));}
            public ActionReceipt receipt(ExactRef key){return java.util.Objects.requireNonNull(receipts.get(key));}});
    }
    @Test void unavailableFreshReadRecordsFailureTimeWithoutInventingARefOrUnknown()throws Exception{
        AwaitFresh wait=waiting();Failed failed=afterRefreshUnavailable(wait,T.plusSeconds(2));
        assertEquals(FailureReason.NO_FRESH_SEMANTIC_FRAME,failed.reason());
        assertSame(wait.partial().starting(),failed.partial().starting());assertTrue(failed.partial().refreshed().isEmpty());
        assertTrue(failed.partial().ending().isEmpty());assertEquals(wait.partial().attempts(),failed.partial().attempts());
        assertFalse(failed.partial().needsOriginalReconciliation(),"the known original negative ACK is not relabeled UNKNOWN");
        assertEquals(Optional.of(T.plusSeconds(2)),failed.partial().times().unavailableAt());assertEquals(failed,replay(failed));assertEquals(failed,roundTrip(failed));
        assertThrows(IllegalArgumentException.class,()->new AwaitFresh(failed.partial()));
        var numeric=StrictJson.parse(result(failed,List.of(Optional.empty())).bytes());
        assertFalse(numeric.get("accepted").booleanValue());assertEquals("no fresh semantic frame after rejected pause",numeric.get("map_control_recovery").get("failure").textValue());
    }
    @Test void unavailableEndingReadRetainsSecondReceiptAndCannotAskForAnotherRetry()throws Exception{
        Retry retry=assertInstanceOf(Retry.class,afterRefresh(waiting(),snapshot(sem(2,false)),T.plusSeconds(1)));
        ActionReceipt second=pausedSecondData();AwaitEnding wait=assertInstanceOf(AwaitEnding.class,afterRetry(retry,second,Optional.empty(),T.plusSeconds(2)));
        Failed failed=afterEndingUnavailable(wait,T.plusSeconds(3));
        assertEquals(FailureReason.ENDING_NOT_PAUSED,failed.reason());assertEquals(2,failed.partial().attempts().size());
        assertSame(second,failed.partial().attempts().getLast().receipt().orElseThrow());assertTrue(failed.partial().ending().isEmpty());
        assertEquals(Optional.of(T.plusSeconds(3)),failed.partial().times().unavailableAt());assertEquals(failed,replay(failed));assertEquals(failed,roundTrip(failed));
        assertThrows(IllegalArgumentException.class,()->new AwaitEnding(failed.partial()));
        var partial=failed.partial();
        assertThrows(IllegalArgumentException.class,()->new Times(partial.times().first(),partial.times().refresh(),
                partial.times().retry(),partial.times().ending(),Optional.of(T)));
    }
}
