package org.xar.ck3.control.service;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/** The actual HTTP encoder consumes the same typed terminal report; no ordinary frame is fabricated. */
final class OrdinarySessionResourceLifecycleTest {
    @Test void terminalUnknownSerializationPreservesNullPlayerExactBirthAndZeroOrdinaryCredit() {
        Instant now=Instant.parse("2026-10-24T00:00:00Z");
        var ref=new ExactRef("D:/fixture/native",1,"a".repeat(64));
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var owner=new SessionPorts.SessionIdentity("fixture-machine-1",game,"terminal-session");
        var identity=new LifecycleIdentity(owner.machineId(),game,owner.sessionId(),new BigInteger("18446744073709551615"),
                new LifecycleIdentity.Subject(BigInteger.valueOf(29829),"old-episode",2,7),
                new LifecycleIdentity.Frame("terminal-native",BigInteger.TWO,BigInteger.TWO,BigInteger.valueOf(24024),true,false),
                new LifecycleIdentity.Null(),LifecycleIdentity.TerminalReason.MISSING,
                new LifecycleIdentity.Evidence(ref,new ExactRef("D:/fixture/hello",1,"b".repeat(64)),new ExactRef("D:/fixture/manifest",1,"c".repeat(64)),
                        new ExactRef("D:/fixture/driver",1,"d".repeat(64)),new ExactRef("D:/fixture/source",1,"e".repeat(64))),now);
        var source=new G2Source(owner.machineId(),now.toString(),"fixture-build",ref);
        var op=LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL;
        var values=List.<ExpectedValue>of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false));
        var command=new ActionCommand("original-terminal",new CommandOrigin.LifecycleTerminal(identity),source,owner.sessionId(),op.key(),new OpportunityJson.Obj(Map.of()),
                new CommandExpectation.LifecycleTerminal(new LifecycleExpectedPostcondition(identity,source,"fixture/v1",op,values)),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),now.plusSeconds(1));
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual completion unknown",List.of(ref)));
        var report=new BatchReport(owner,"terminal-wire",BatchReport.Terminal.ACTION_UNKNOWN,"original terminal unknown",new SessionClock.Tick(0,now),new SessionClock.Tick(1,now.plusNanos(1)),
                List.of(),List.of(),List.of(),List.of(new BatchReport.LifecycleTurn(1,identity,receipt,false)),List.of(),List.of(),Optional.empty(),Optional.of(new SessionPorts.TerminalReady(identity,new SessionPorts.TerminalBlocked("private completion unavailable",List.of(ref)))),Optional.empty(),Optional.empty(),Optional.empty(),0,0,false,List.of(),List.of(),List.of());
        var row=OrdinarySessionResource.report(report);
        assertEquals(1,row.get("attempted_turns").intValue());assertEquals(0,row.get("applied_turns").intValue());assertEquals(0,row.get("committed_saved_days").intValue());
        assertEquals("134000000000000001",row.get("game_creation_filetime").textValue());
        var actual=row.get("last_lifecycle_turns").get(0);assertEquals("UNRESOLVED",actual.get("outcome").textValue());
        assertFalse(actual.get("visible_gameplay").booleanValue());assertFalse(actual.get("eligible_advance").booleanValue());
        assertEquals(identity,LifecycleIdentityCodec.decode(actual.get("current_lifecycle_identity")));
        assertTrue(row.get("last_plan").isNull());
        assertTrue(row.get("last_actions").isEmpty());assertFalse(actual.has("before"));
        assertEquals(identity,LifecycleIdentityCodec.decode(row.get("last_terminal_observation").get("identity")));
        assertEquals("BLOCKED",row.get("last_terminal_observation").get("decision").textValue());
        assertEquals(ref,ExactRef.fromJson(row.get("last_terminal_observation").get("evidence").get(0)));
    }
    @Test void ordinaryWaitReportRetainsExistingTraceReasonsAndExactObservationIdentity() {
        Instant now=Instant.parse("2026-10-24T00:00:00Z");
        var ref=new ExactRef("D:/fixture/policy",1,"a".repeat(64));
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var owner=new SessionPorts.SessionIdentity("fixture-machine-1",game,"ordinary-session");
        var frame=new ObservationIdentity(owner.machineId(),game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(31254),BigInteger.valueOf(102),BigInteger.valueOf(53144328)),
                        "native:102",BigInteger.valueOf(7),"episode-1"),1);
        var detail=new OpportunityJson.Obj(Map.of("explicit_null",OpportunityJson.Nil.INSTANCE,"available",new OpportunityJson.Bool(false)));
        var draft=new org.xar.ck3.control.application.planning.OrdinaryPolicy.Draft("actual-policy","current","actual input unavailable; retained wait",
                org.xar.ck3.control.application.planning.OrdinaryPolicy.Kind.ORDINARY,Optional.empty(),
                org.xar.ck3.control.application.planning.OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),detail);
        var trace=new org.xar.ck3.control.application.planning.PlanTrace(frame,List.of(
                new org.xar.ck3.control.application.planning.PlanTrace.StageVisit(
                        org.xar.ck3.control.application.planning.PlanningStage.ORDINARY_CORE,
                        org.xar.ck3.control.application.planning.PlanTrace.Outcome.DEFERRED_INPUT,
                        "actual current capability unavailable",Optional.of(ref),Optional.of(detail))),Optional.of(draft));
        var report=new BatchReport(owner,"ordinary-wait",BatchReport.Terminal.WALL_TIMEOUT,"actual finite batch ended",
                new SessionClock.Tick(0,now),new SessionClock.Tick(1,now.plusNanos(1)),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                Optional.of(trace),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),0,0,false,List.of(),List.of(),List.of());
        var row=OrdinarySessionResource.report(report);var encoded=row.get("last_plan");
        assertEquals("actual input unavailable; retained wait",encoded.get("final_plan").get("reason").textValue());
        assertTrue(encoded.get("final_plan").get("command").isNull());
        assertEquals("DEFERRED_INPUT",encoded.get("visits").get(0).get("outcome").textValue());
        assertEquals("actual current capability unavailable",encoded.get("visits").get(0).get("reason").textValue());
        assertEquals(ref,ExactRef.fromJson(encoded.get("visits").get(0).get("source")));
        assertEquals("134000000000000001",encoded.get("before").get("game").get("creation_filetime").textValue());
        assertTrue(encoded.get("visits").get(0).get("evidence").get("explicit_null").isNull());
        assertFalse(encoded.get("visits").get(0).get("evidence").has("missing"));
        assertEquals(0,row.get("attempted_turns").intValue());assertEquals(0,row.get("committed_saved_days").intValue());
    }

}
