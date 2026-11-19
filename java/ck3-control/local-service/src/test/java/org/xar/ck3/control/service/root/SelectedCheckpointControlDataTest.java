package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.io.CleanupMode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Pure control/receipt DATA only. No Root context, managed Game or Native write is created. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.selected.checkpoint.inputs",matches=".+")
final class SelectedCheckpointControlDataTest {
    @TempDir(cleanup=CleanupMode.NEVER) Path directory;
    private static ExactRef ref(Path path)throws Exception {
        byte[] b=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().toString(),b.length,ActionCodec.sha256(b));
    }
    private static byte[] exact(com.fasterxml.jackson.databind.JsonNode r)throws Exception {
        byte[] b=Files.readAllBytes(Path.of(r.path("path").textValue()));assertEquals(r.path("bytes").longValue(),b.length);
        assertEquals(r.path("sha256").textValue(),ActionCodec.sha256(b));return b;
    }
    private ObjectNode inputs()throws Exception{return (ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.selected.checkpoint.inputs"))));}
    private ActionCommand original()throws Exception{return ActionCodec.decodeCommand(exact(inputs().path("command25")));}
    private ExactRef write(String name,ObjectNode value)throws Exception {
        Path p=directory.resolve(name);Files.write(p,StrictJson.canonical(value));return ref(p);
    }
    private RootSelectedCheckpointControl.Declaration declaration(Path published)throws Exception {
        var command=original();return new RootSelectedCheckpointControl.Declaration(command.source().machineId(),command.sessionId(),
                StrictJson.canonical(command.origin().game().toJson()),published,directory.resolve("result.json"),Instant.now().plusSeconds(90),Duration.ofSeconds(60));
    }
    @Test void legacySixArgumentsStaySeparateFromExplicitBoundedExactThree()throws Exception {
        assertTrue(RootLoadedSavedResumeMain250.checkpointControlReference(new String[6]).isEmpty());
        var source=write("declared.json",StrictJson.object().put("software_data",true));
        String[] args=new String[9];args[6]=source.path();args[7]=Long.toString(source.bytes());args[8]=source.sha256();
        assertEquals(Optional.of(source),RootLoadedSavedResumeMain250.checkpointControlReference(args));
        assertThrows(Exception.class,()->RootLoadedSavedResumeMain250.checkpointControlReference(new String[7]));
        args[7]="not-a-number";assertThrows(Exception.class,()->RootLoadedSavedResumeMain250.checkpointControlReference(args));
    }
    @Test void declarationUsesTheOriginalFiniteSourceStopAndBoundedNewSaveDeadline()throws Exception {
        var command=original();Instant now=Instant.now();Clock clock=Clock.fixed(now,ZoneOffset.UTC);
        var value=StrictJson.object().put("schema","xar.java-single-selected-checkpoint-control/v1")
                .put("machine_id",command.source().machineId()).put("session_id",command.sessionId())
                .put("response_published_path",directory.resolve("respond.json").toString()).put("result_path",directory.resolve("result.json").toString())
                .put("stop_before_utc",now.plusSeconds(90).toString()).put("checkpoint_timeout_ms",60000);
        value.set("game",command.origin().game().toJson());
        var result=RootSelectedCheckpointControl.read(write("control.json",value),clock);
        assertEquals(now.plusSeconds(90),result.stopBefore());assertEquals(Duration.ofSeconds(60),result.checkpointTimeout());
        var over=value.deepCopy().put("checkpoint_timeout_ms",120001);
        assertThrows(RuntimeException.class,()->RootSelectedCheckpointControl.read(write("too-long.json",over),clock));
        var expired=value.deepCopy().put("stop_before_utc",now.minusNanos(1).toString());
        assertThrows(RuntimeException.class,()->RootSelectedCheckpointControl.read(write("expired.json",expired),clock));
        var unknown=value.deepCopy().put("implicit_select_all",true);
        assertThrows(RuntimeException.class,()->RootSelectedCheckpointControl.read(write("unknown.json",unknown),clock));
    }
    private RootSelectedCheckpointControl.Selected selected(String choice,String tag,boolean wrongBody)throws Exception {
        var input=inputs();var request=(ObjectNode)StrictJson.parse(exact(input.path("request25")));
        var response=(ObjectNode)StrictJson.parse(exact(input.path("response25")));
        Path root=Files.createDirectory(directory.resolve(tag));Path responsePath=root.resolve("response.json");
        request.put("response_file",responsePath.toString());byte[] requestRaw=StrictJson.canonical(request);Files.write(root.resolve("request.json"),requestRaw);
        ((ObjectNode)response.get("selection")).put("decision",choice);
        if(wrongBody)((ObjectNode)response.get("selection")).put("body_sha256","0".repeat(64));
        response.put("request_sha256",ActionCodec.sha256(requestRaw));Files.write(responsePath,StrictJson.canonical(response));
        var published=StrictJson.object().put("provider","codex-session").put("schema","xar.ordinary-codex-session-response-published/v1");
        published.set("response",ref(responsePath).toJson());Path publisher=root.resolve("published.json");Files.write(publisher,StrictJson.canonical(published));
        return RootSelectedCheckpointControl.selected(declaration(publisher));
    }
    @Test void publishedOriginalSelectionBindsItsExactCommandBodyAndDoesNotRenewTheDecision()throws Exception {
        var current=selected("SELECT_PROPOSAL","selected",false);var old=original();
        assertEquals(old.actionId(),current.actionId());assertEquals(ActionCodec.bodySha256(old),current.bodySha256());assertEquals(old,current.original());
        assertEquals(old.deadline(),current.original().deadline(),"historical DATA must keep its expired original deadline");
        assertEquals("WAIT",selected("WAIT","wait",false).decision());
        assertThrows(RuntimeException.class,()->selected("SELECT_PROPOSAL","wrong-body",true));
    }
    private ActionReceipt receipt(boolean settled,boolean advances)throws Exception {
        var command=original();var before=command.before();
        Path evidence=directory.resolve("software-evidence-"+settled+"-"+advances+".json");
        Files.writeString(evidence,"software classified receipt DATA only; not native observation or Root authority");var data=ref(evidence);
        var guard=new GuardEvidence(before,command.source(),command.sessionId(),BigInteger.ONE,command.operation(),data,data,"software-no-live-authority",
                command.deadline().minusSeconds(10),command.deadline());
        var request=new NativeRequest("software-life-sequence","software.capability",new RawJson(new byte[]{123,125}));
        var attempt=new ActionState.Attempt("software-attempt",command.deadline().minusSeconds(5),guard,request);
        if(!settled)return new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Submitting(attempt));
        var f=before.frame();var identity=f.identity();
        var after=new ObservationIdentity(before.machineId(),before.game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(identity.player(),identity.nativeRevision().add(BigInteger.ONE),identity.dateRaw().add(advances?BigInteger.valueOf(168):BigInteger.ZERO)),
                "software-post",f.revision().add(BigInteger.ONE),f.episodeRunId()),before.observationVersion());
        List<ExpectedValue> values=List.of(new ExpectedBoolean(new FieldKey("timeline.advance_verified"),true),
                new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),true),new ExpectedText(new FieldKey("progress_status"),"postcondition"));
        var observed=new ActionState.EffectObservation(after,command.source(),command.sessionId(),"software-postcondition/v1",values,
                "software-post-read",command.deadline().minusSeconds(1),data);
        var nativeData=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","software-attempt").put("ok",true);
        nativeData.putObject("result").put("software_fixture",true);
        var ack=new NativeActionPort.AckReceived("software-attempt",true,Optional.of(new RawJson(StrictJson.canonical(nativeData.get("result")))),
                new RawJson(StrictJson.canonical(nativeData)),org.xar.ck3.control.nativebridge.NativeWire.packet(StrictJson.canonical(nativeData)));
        return new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,new ActionState.Applied(observed)));
    }
    private BatchReport report(ActionReceipt receipt,BatchReport.Terminal terminal)throws Exception {
        var before=receipt.command().before();var data=ref(directory.resolve("software-evidence-"+receipt.settled()+"-"+receipt.eligibleAdvance()+".json"));
        var plan=new org.xar.ck3.control.application.planning.PlanTrace(before,List.of(),Optional.empty());
        var facts=new TurnFacts(receipt.visibleGameplay(),receipt.eligibleAdvance(),List.of(data));
        return new BatchReport(new SessionIdentity(before.machineId(),before.game(),receipt.command().sessionId()),"software-batch-1",terminal,"pure DATA",
                new SessionClock.Tick(1,receipt.command().deadline().minusSeconds(2)),new SessionClock.Tick(2,receipt.command().deadline().minusSeconds(1)),
                List.of(),List.of(new BatchReport.Turn(1,before,plan,receipt,facts)),List.of(),List.of(),List.of(),List.of(),Optional.of(plan),Optional.empty(),Optional.empty(),
                Optional.empty(),Optional.of(data),0,receipt.eligibleAdvance()?1:0,receipt.eligibleAdvance(),List.of(),List.of(),List.of());
    }
    @Test void onlyTheMatchedSettledAppliedAdvanceAtTheCompletedTurnBoundaryIsEligible()throws Exception {
        var selected=selected("SELECT_PROPOSAL","eligible",false);
        var applied=receipt(true,true);assertTrue(applied.eligibleAdvance());
        assertTrue(RootSelectedCheckpointControl.eligible(report(applied,BatchReport.Terminal.TURN_BOUND),selected));
        assertFalse(RootSelectedCheckpointControl.eligible(report(applied,BatchReport.Terminal.WALL_TIMEOUT),selected));
        var wrong=new RootSelectedCheckpointControl.Selected(selected.actionId(),"0".repeat(64),selected.original(),"SELECT_PROPOSAL");
        assertFalse(RootSelectedCheckpointControl.eligible(report(applied,BatchReport.Terminal.TURN_BOUND),wrong));
        var wait=new RootSelectedCheckpointControl.Selected(selected.actionId(),selected.bodySha256(),selected.original(),"WAIT");
        assertFalse(RootSelectedCheckpointControl.eligible(report(applied,BatchReport.Terminal.TURN_BOUND),wait));
        var unresolved=receipt(false,false);assertFalse(RootSelectedCheckpointControl.eligible(report(unresolved,BatchReport.Terminal.TURN_BOUND),selected));
        var noDay=receipt(true,false);assertFalse(RootSelectedCheckpointControl.eligible(report(noDay,BatchReport.Terminal.TURN_BOUND),selected));
    }
}
