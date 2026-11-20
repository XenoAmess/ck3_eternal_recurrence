package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Input/DATA regressions do not manufacture a current Core, Root, Native receipt or completed-cycle issuer. */
final class RootTwoCycleCheckpointControlTest {
    @TempDir Path directory;
    private static final Instant NOW=Instant.parse("2026-11-20T00:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private static final String MACHINE="software-fixture-machine",SESSION="software-fixture-session";
    private static final GameGeneration GAME=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private ExactRef write(String name,ObjectNode value)throws Exception {
        Path path=directory.resolve(name);byte[] raw=StrictJson.canonical(value);Files.write(path,raw);
        return new ExactRef(path.toString(),raw.length,ActionCodec.sha256(raw));
    }
    private ExactRef data(String name)throws Exception {return write(name,StrictJson.object().put("software_DATA_only",true));}
    private record Inputs(ExactRef declaration,ObjectNode body,ExactRef owner,ExactRef configuration,ExactRef top) { }
    private Inputs inputs(String tag,int maximum)throws Exception {
        Path output=Files.createDirectory(directory.resolve("review-"+tag));
        Path queue=directory.resolve("queue-"+tag),materials=directory.resolve("materials-"+tag);
        var main=StrictJson.object().put("schema","xar.java-ordinary-runtime-configuration/v1").put("machine_id",MACHINE);
        main.putObject("decision_provider").put("endpoint",queue.toUri().toString()).put("model","codex-session")
                .put("timeout_ms",120000).put("maximum_attempts",1).put("retry_backoff_ms",0);
        var cfg=write("main-"+tag+".json",main);
        var owner=StrictJson.object().put("schema","xar.java-game-supervisor-owner/v1").put("machine_id",MACHINE).put("session_id",SESSION);
        ObjectNode ownerGame=GAME.toJson();ownerGame.put("executable","software-fixture-NO-Game");owner.set("game",ownerGame);
        var plan=owner.putObject("configuration").put("session_id",SESSION).put("deadline",NOW.plusSeconds(180).toString());
        plan.putObject("review").put("machine_id",MACHINE).put("expires_at",NOW.plusSeconds(180).toString());
        var ownerRef=write("owner-"+tag+".json",owner);var prefix=data("prefix-"+tag+".json");
        var watch=StrictJson.object().put("schema","ck3.multi-original-review-watch/v2")
                .put("queue_root",queue.toString()).put("material_root",materials.toString()).put("output_root",output.toString())
                .put("main_begin",directory.resolve("BEGIN-"+tag).toString()).put("main_end",directory.resolve("END-"+tag).toString())
                .put("own_stop",directory.resolve("STOP-"+tag).toString()).put("source_started_at_utc",NOW.minusSeconds(1).toString())
                .put("stop_before_utc",NOW.plusSeconds(170).toString()).put("source_expires_at_utc",NOW.plusSeconds(180).toString())
                .put("maximum_requests",maximum);
        watch.set("prefix",prefix.toJson());watch.set("actual_configuration",cfg.toJson());watch.set("owner_descriptor",ownerRef.toJson());
        var watchRef=write("watch-"+tag+".json",watch);
        // Explicit software metadata projection. This is never an observed preMain PID or qualified Game owner.
        var top=StrictJson.object().put("schema","ck3.multi-original-review-watcher-running/v2").put("at_utc",NOW.toString())
                .put("pid",456).put("creation_filetime","134000000000000002").put("script_sha256","a".repeat(64))
                .put("machine_id",MACHINE).put("session_id",SESSION).put("actually_running_before_Main",true)
                .put("maximum_requests",maximum).put("source_started_at_utc",NOW.minusSeconds(1).toString())
                .put("stop_before_utc",NOW.plusSeconds(170).toString()).put("source_expires_at_utc",NOW.plusSeconds(180).toString())
                .put("automatic_decision",false).put("zero_request_retries",true).put("no_Game_pipe_HTTP_writer_API",true);
        top.set("game",GAME.toJson());top.set("config",watchRef.toJson());top.set("prefix",prefix.toJson());
        top.set("actual_configuration",cfg.toJson());top.set("owner_descriptor",ownerRef.toJson());
        byte[] raw=StrictJson.canonical(top);Path topPath=output.resolve("WATCHER.READY.json");Files.write(topPath,raw);
        var topRef=new ExactRef(topPath.toString(),raw.length,ActionCodec.sha256(raw));
        var body=StrictJson.object().put("schema",RootTwoCycleCheckpointControl.SCHEMA).put("machine_id",MACHINE).put("session_id",SESSION)
                .put("result_path",directory.resolve("result-"+tag+".json").toString()).put("stop_before_utc",NOW.plusSeconds(160).toString())
                .put("checkpoint_timeout_ms",120000);
        body.set("game",GAME.toJson());body.set("watcher_ready",topRef.toJson());
        return new Inputs(write("declaration-"+tag+".json",body),body,ownerRef,cfg,topRef);
    }
    @Test void sixArgumentsAndLegacySingleControlRemainExplicitAndSeparate()throws Exception {
        assertTrue(RootLoadedSavedResumeMain250.checkpointControlReference(new String[6]).isEmpty());
        var legacy=write("legacy.json",StrictJson.object().put("schema","xar.java-single-selected-checkpoint-control/v1"));
        assertFalse(RootTwoCycleCheckpointControl.accepts(legacy));
        var input=inputs("args",3);String[] args=new String[9];args[6]=input.declaration().path();args[7]=Long.toString(input.declaration().bytes());args[8]=input.declaration().sha256();
        assertEquals(Optional.of(input.declaration()),RootLoadedSavedResumeMain250.checkpointControlReference(args));
        assertTrue(RootTwoCycleCheckpointControl.accepts(input.declaration()));
        assertThrows(Exception.class,()->RootLoadedSavedResumeMain250.checkpointControlReference(new String[7]));
    }
    @Test void independentMainAndOwnerRefsAndOneTurnAreMandatory()throws Exception {
        var input=inputs("bound",3);var declaration=RootTwoCycleCheckpointControl.read(input.declaration(),CLOCK);
        RootTwoCycleCheckpointControl.requireMainInputs(declaration,input.owner(),input.configuration(),1);
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.requireMainInputs(declaration,data("foreign-owner.json"),input.configuration(),1));
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.requireMainInputs(declaration,input.owner(),data("foreign-main.json"),1));
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.requireMainInputs(declaration,input.owner(),input.configuration(),2));
    }
    @Test void watcherCapacityTwoCannotEndTheStreamBeforeTheSecondBusinessPost()throws Exception {
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.read(inputs("capacity2",2).declaration(),CLOCK));
        var accepted=RootTwoCycleCheckpointControl.read(inputs("capacity3",3).declaration(),CLOCK);
        assertEquals(3,accepted.watcher().maximumRequests());
        assertEquals(NOW.plusSeconds(160),accepted.stop());
    }
    @Test void closedFieldsAndOriginalSourceStopCannotBeExtended()throws Exception {
        var input=inputs("closed",3);
        var extra=input.body().deepCopy().put("automatic_select",true);
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.read(write("extra.json",extra),CLOCK));
        var later=input.body().deepCopy().put("stop_before_utc",NOW.plusSeconds(171).toString());
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.read(write("later.json",later),CLOCK));
        var expired=input.body().deepCopy().put("stop_before_utc",NOW.minusNanos(1).toString());
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.read(write("expired.json",expired),CLOCK));
        var bool=input.body().deepCopy().put("checkpoint_timeout_ms",true);
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.read(write("bool.json",bool),CLOCK));
    }
    @Test void birthRemainsAnExactDecimalStringAndPidIsNeverBoolean()throws Exception {
        var input=inputs("identity",3);
        var numeric=input.body().deepCopy();((ObjectNode)numeric.get("game")).put("creation_filetime",134000000000000001L);
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.read(write("birth-int.json",numeric),CLOCK));
        var bool=input.body().deepCopy();((ObjectNode)bool.get("game")).put("pid",true);
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.read(write("pid-bool.json",bool),CLOCK));
    }
    private record CycleData(ActionReceipt receipt,SessionIdentity owner,CompletedCycleProof proof,ExactRef receiptRef,ObjectNode record) { }
    private CycleData cycle()throws Exception {
        var evidence=data("cycle-evidence.json");var source=new G2Source(MACHINE,NOW.toString(),"software-DATA-only",evidence);
        var before=new ObservationIdentity(MACHINE,GAME,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(24000)),
                "software-before",BigInteger.ONE,"software-episode"),1);
        var operation=new OperationKey("life-advance");
        List<ExpectedValue> expected=List.of(new ExpectedBoolean(new FieldKey("timeline.advance_verified"),true),
                new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),true),new ExpectedText(new FieldKey("progress_status"),"postcondition"));
        var command=new ActionCommand("software-original-1",before,source,SESSION,operation,new OpportunityJson.Obj(java.util.Map.of()),
                new ExpectedPostcondition(1,before,source,"software-post/v1",expected),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(120));
        var guard=new GuardEvidence(before,source,SESSION,BigInteger.ONE,operation,evidence,evidence,"software-no-live-authority",NOW,command.deadline());
        var attempt=new ActionState.Attempt("software-attempt",NOW.plusSeconds(1),guard,new NativeRequest("software", "software.capability",new RawJson(new byte[]{123,125})));
        var post=new ObservationIdentity(MACHINE,GAME,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.TWO,BigInteger.valueOf(24024)),
                "software-post",BigInteger.TWO,"software-episode"),1);
        var observed=new ActionState.EffectObservation(post,source,SESSION,"software-post/v1",expected,"software-post-read",NOW.plusSeconds(2),evidence);
        var raw=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","software-attempt").put("ok",true);
        raw.putObject("result").put("software_DATA_only",true);
        var ack=new NativeActionPort.AckReceived("software-attempt",true,Optional.of(new RawJson(StrictJson.canonical(raw.get("result")))),
                new RawJson(StrictJson.canonical(raw)),NativeWire.packet(StrictJson.canonical(raw)));
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,new ActionState.Applied(observed)));
        var frame=new ObservationIdentity(MACHINE,GAME,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(3),BigInteger.valueOf(24024)),
                "software-after-sem",BigInteger.valueOf(3),"software-episode"),1);
        // Separate synthetic reference roles; none is represented as a real semantic export, Native packet or full Driver.
        var semanticExport=write("semantic-export-DATA.json",StrictJson.object().put("synthetic_DATA_role","semantic-export-not-qualified"));
        var rawPacket=write("native-packet-DATA.json",StrictJson.object().put("synthetic_DATA_role","native-packet-not-qualified"));
        var driverStamp=write("driver-stamp-DATA.json",StrictJson.object().put("synthetic_DATA_role","driver-stamp-not-qualified"));
        var originalDriver=write("driver-original-DATA.json",StrictJson.object().put("synthetic_DATA_role","driver-original-not-qualified"));
        var semantic=new SemanticEvidence(frame,semanticExport,rawPacket,driverStamp,originalDriver,NOW.plusSeconds(3));
        var proof=new CompletedCycleProof(11,semantic,"c".repeat(64));var owner=new SessionIdentity(MACHINE,GAME,SESSION);
        var receiptRef=data("canonical-receipt-DATA.json");
        var record=StrictJson.object().put("schema","xar.java-ordinary-cycle-record/v1").put("completed_cycles",11).put("classification","ELIGIBLE_ADVANCE");
        record.set("session",OrdinaryCycleTransitions.sessionToJson(owner));record.set("receipt_ref",receiptRef.toJson());
        record.set("semantic",OrdinaryCycleTransitions.semanticToJson(semantic));record.putNull("previous");
        return new CycleData(receipt,owner,proof,receiptRef,record);
    }
    private BatchReport report(CycleData data,BatchReport.Terminal terminal) {
        var receipt=data.receipt();var plan=new PlanTrace(receipt.command().before(),List.of(),Optional.empty());
        var tick=new SessionClock.Tick(1,NOW.plusSeconds(4));
        var turn=new BatchReport.Turn(1,receipt.command().before(),plan,receipt,new TurnFacts(true,true,List.of(data.receiptRef())));
        return new BatchReport(data.owner(),"software-batch-1",terminal,"DATA only",tick,tick,List.of(),List.of(turn),List.of(),List.of(),List.of(),List.of(),
                Optional.of(plan),Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(data.receiptRef()),0,1,true,List.of(),List.of(),List.of());
    }
    @Test void publicationOrAnotherBodyIsNotTheAppliedCompletedTurn()throws Exception {
        var data=cycle();var receipt=data.receipt();var selected=new RootSelectedCheckpointControl.Selected(receipt.command().actionId(),receipt.bodySha256(),receipt.command(),"SELECT_PROPOSAL");
        assertSame(receipt,RootTwoCycleCheckpointControl.matched(report(data,BatchReport.Terminal.TURN_BOUND),selected));
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.matched(report(data,BatchReport.Terminal.WALL_TIMEOUT),selected));
        var wait=new RootSelectedCheckpointControl.Selected(selected.actionId(),selected.bodySha256(),selected.original(),"WAIT");
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.matched(report(data,BatchReport.Terminal.TURN_BOUND),wait));
        var wrong=new RootSelectedCheckpointControl.Selected(selected.actionId(),"0".repeat(64),selected.original(),"SELECT_PROPOSAL");
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.matched(report(data,BatchReport.Terminal.TURN_BOUND),wrong));
    }
    @Test void retainedProofMustBeExactlyThisReceiptAndBaselinePlusOne()throws Exception {
        var data=cycle();RootTwoCycleCheckpointControl.requireCompletedData(data.receipt(),data.owner(),data.proof(),11,data.receiptRef(),data.record());
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.requireCompletedData(data.receipt(),data.owner(),data.proof(),12,data.receiptRef(),data.record()));
        var other=data("other-receipt.json");
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.requireCompletedData(data.receipt(),data.owner(),data.proof(),11,other,data.record()));
        var control=data.record().deepCopy().put("classification","CONTROL_ONLY");
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.requireCompletedData(data.receipt(),data.owner(),data.proof(),11,data.receiptRef(),control));
    }
    @Test void afterSemCannotBeReplacedByThePostItselfOrAnOlderNativeRevision()throws Exception {
        var data=cycle();var old=data.proof().semantic();var post=data.receipt().applied().orElseThrow().observation();
        var sameTime=new SemanticEvidence(old.frame(),old.semantic(),old.originalNativePacket(),old.driverStamp(),old.originalDriver(),post.observedAt());
        var proof=new CompletedCycleProof(11,sameTime,data.proof().cycleStateDigest());var record=data.record().deepCopy();record.set("semantic",OrdinaryCycleTransitions.semanticToJson(sameTime));
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.requireCompletedData(data.receipt(),data.owner(),proof,11,data.receiptRef(),record));
        var frame=data.receipt().command().before();var stale=new SemanticEvidence(frame,old.semantic(),old.originalNativePacket(),old.driverStamp(),old.originalDriver(),NOW.plusSeconds(3));
        var older=new CompletedCycleProof(11,stale,data.proof().cycleStateDigest());var olderRecord=data.record().deepCopy();olderRecord.set("semantic",OrdinaryCycleTransitions.semanticToJson(stale));
        assertThrows(RuntimeException.class,()->RootTwoCycleCheckpointControl.requireCompletedData(data.receipt(),data.owner(),older,11,data.receiptRef(),olderRecord));
    }

    /** Separate qualification entry, NOT an automatic test/provider or fake Root.
     * Invoke only with the real production startup issuer and two separately reviewed original requests.
     * No actual input is available in this source-only package, so this entry is NOT_RUN.
     */
    static void assertActualTwoCyclesThenOneCheckpoint(RootStartupInputsProducer.Actual input,
            RootTwoCycleCheckpointControl.Declaration declaration)throws Exception {
        var root=input.original();var access=input.core().sessionAccess();assertSame(root,access.current());
        var control=new RootTwoCycleCheckpointControl(declaration,access,Clock.systemUTC());int[] batches={0};
        var loop=new RootOrdinaryWorkerLoop(new RootOrdinaryWorkerLoop.Configuration("two-cycle-actual",1,Duration.ofMinutes(10),
                Duration.ofMinutes(1),Duration.ofMillis(20),1),new RootOrdinaryWorkerLoop.Control(){
            @Override public boolean stopRequested(){return control.stopRequested();}
            @Override public void onBatchCompleted(BatchReport report,long next)throws IOException,InterruptedException {
                assertSame(root,access.current());assertSame(report,root.controllerForPublication().lastReport().orElseThrow());
                assertTrue(root.batchJournal().retainedCycleProof(root.identity()).isPresent());
                assertTrue(++batches[0]<=2,"the third batch must never be entered");control.afterBatch(report);
                if(batches[0]==1){assertFalse(control.finished());assertFalse(Files.exists(declaration.result()),"no checkpoint marker at SELECT/first cycle");}
                else assertTrue(control.finished(),"only the second complete post/cycle may finish its terminal checkpoint");
            }
        });
        var ended=loop.run(access,0);assertEquals(2,batches[0]);assertEquals(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,ended.stopReason());
        var result=StrictJson.parse(Files.readAllBytes(declaration.result()),1<<20);
        assertEquals("TWO_CYCLES_CANONICAL_TERMINAL_CHECKPOINT_CONFIRMED",result.path("status").asText());
        assertTrue(result.path("physical_save_confirmed").booleanValue());assertEquals(2,result.path("completed_cycles_in_this_control").intValue());
        assertTrue(result.has("canonical_save_receipt"));assertTrue(result.has("checkpoint_pair"));
    }
}
