package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public typed DATA and a pure wire encoder do not acquire the actual Root/writer/modal permission. */
final class RootNaturalOriginalAuthorityTest {
    private static ExactRef ref(String name,char hash) {return new ExactRef("D:/natural-authority-fixture/"+name,11,String.valueOf(hash).repeat(64));}
    private static RootNaturalSuccessionOriginals unbound() {return new RootNaturalSuccessionOriginals(List.of(ref("producer.java",'a')),ref("timeline.cpp",'b'),ref("close.cpp",'c'),(config,hello,guard,request)->{throw new IOException("fixture has no native source authority");});}
    private static ActionCommand close() { return close(30000); }
    private static ActionCommand close(int actor) {
        Instant now=Instant.parse("2026-10-24T00:00:00Z");var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var identity=new LifecycleIdentity("natural-authority-fixture",game,"session",BigInteger.ONE,new LifecycleIdentity.Subject(BigInteger.valueOf(29829),"old-episode",1,2),new LifecycleIdentity.Frame("native:2",BigInteger.valueOf(5),BigInteger.valueOf(2),BigInteger.valueOf(100),true,true),new LifecycleIdentity.Character(BigInteger.valueOf(actor),true),LifecycleIdentity.TerminalReason.CHANGED,new LifecycleIdentity.Evidence(ref("packet",'d'),ref("hello",'e'),ref("manifest",'f'),ref("driver",'1'),ref("source-proof",'2')),now);
        var source=new G2Source(identity.machineId(),now.toString(),"1.20.0.4",ref("native-source",'3'));
        List<ExpectedValue> values=List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false),new ExpectedBoolean(new FieldKey("lifecycle.death_modal_cleared"),true));
        return new ActionCommand("actual-close",new CommandOrigin.LifecycleTerminal(identity),source,identity.sessionId(),LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL.key(),new OpportunityJson.Obj(Map.of("expected_date_raw",new OpportunityJson.IntegerValue(BigInteger.valueOf(100)),"expected_played_character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(actor)))),new CommandExpectation.LifecycleTerminal(new LifecycleExpectedPostcondition(identity,source,RootNaturalTimeline.OBSERVER,LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL,values)),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),now.plusSeconds(30));
    }
    @Test void onePrivateReadAndCloseBindingKeepTerminalOriginAndNoFabricatedHelloCapability() {
        var producer=unbound();var prepared=new RootNaturalSuccessionOriginals.Prepared(List.of(ref("producer.java",'a')),ref("timeline.cpp",'b'),ref("close.cpp",'c'));assertEquals(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS,prepared.registration().slot());assertThrows(IllegalArgumentException.class,producer::registration);var timeline=producer.timeline();
        assertSame(prepared.registration(),prepared.registration(),"Root catalog requires the identical Core registration, not a reconstructed equivalent record");
        assertSame(timeline.actionBinding(),timeline.actionBinding());assertSame(timeline.replayBinding(),timeline.replayBinding());assertSame(timeline.privatePermission(),timeline.privatePermission());
        assertEquals(ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,timeline.contract().guardMode());assertEquals(ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,timeline.contract().permissionMode());assertTrue(timeline.contract().requiredCapability().isEmpty());
        assertEquals(ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,timeline.actionBinding().guardMode());assertTrue(timeline.actionBinding().requiredCapability().isEmpty());assertEquals("allow_private_death_succession_modal_continue",timeline.privatePermission().permissionKey());
    }
    @Test void preparedRetainsOneImmutableFiniteUniqueProducerClosure() {
        ExactRef source=ref("producer.java",'a');var input=new java.util.ArrayList<>(List.of(source));
        var prepared=new RootNaturalSuccessionOriginals.Prepared(input,ref("timeline.cpp",'b'),ref("close.cpp",'c'));
        var registration=prepared.registration();input.clear();
        assertSame(registration,prepared.registration());
        assertEquals(List.of(source),registration.producerSources());
        assertThrows(IllegalArgumentException.class,()->new RootNaturalSuccessionOriginals.Prepared(List.of(source,source),ref("timeline.cpp",'b'),ref("close.cpp",'c')));
        assertThrows(IllegalArgumentException.class,()->new RootNaturalSuccessionOriginals.Prepared(List.of(),ref("timeline.cpp",'b'),ref("close.cpp",'c')));
    }
    @Test void perGameTimelineRetainsTheOriginalPrelaunchClosePermission() {
        var original=unbound();var permission=original.timeline().privatePermission();
        var actual=new RootNaturalSuccessionOriginals(List.of(ref("producer.java",'a')),ref("timeline.cpp",'b'),ref("close.cpp",'c'),
                (config,hello,guard,request)->{throw new IOException("fixture has no native source authority");},java.util.Optional.of(permission));
        assertSame(permission,actual.timeline().privatePermission());
        assertNotSame(original.timeline().actionBinding(),actual.timeline().actionBinding(),"a per-Game native observer cannot be reused from the unbound prelaunch permission producer");
        assertThrows(IllegalArgumentException.class,()->new RootNaturalSuccessionOriginals(List.of(ref("producer.java",'a')),ref("timeline.cpp",'b'),ref("changed-close.cpp",'d'),
                (config,hello,guard,request)->{throw new IOException("fixture has no native source authority");},java.util.Optional.of(permission)));
    }
    @Test void closeWireContainsOnlyTheTwoActualNativeFieldsAndDeclinesDaySaveGameplayCredit() {
        var producer=unbound();var command=close();var wire=RootNaturalTimeline.terminalCloseWire(command);assertTrue(wire.requiredCapability().isEmpty());
        var json=StrictJson.object(StrictJson.parse(wire.additionalFields().bytes()),Set.of("expected_date_raw","expected_played_character_id"));assertEquals(30000,json.get("expected_played_character_id").intValue());assertFalse(json.has("lifecycle.death_modal_cleared"));
        assertThrows(IllegalStateException.class,command::before);assertThrows(IllegalStateException.class,()->producer.inspectCandidate(null));
        assertThrows(IllegalStateException.class,()->producer.openQualified(command,null,null));
        assertThrows(IllegalStateException.class,()->producer.timeline().prepare(command),"pure wire encoding grants no Root owner");
    }
    @Test void terminalCloseWireValidatesSignedInt32Boundaries() {
        var command=close();
        var wire=RootNaturalTimeline.terminalCloseWire(command);
        var json=StrictJson.object(StrictJson.parse(wire.additionalFields().bytes()),Set.of("expected_date_raw","expected_played_character_id"));
        assertEquals(30000,json.get("expected_played_character_id").intValue());
        
        for(int id:new int[]{Integer.MIN_VALUE, Integer.MIN_VALUE+2, 0, Integer.MAX_VALUE}) {
            var cmd=close(id);
            var w=RootNaturalTimeline.terminalCloseWire(cmd);
            var j=StrictJson.object(StrictJson.parse(w.additionalFields().bytes()),Set.of("expected_date_raw","expected_played_character_id"));
            assertEquals(id,j.get("expected_played_character_id").intValue());
        }
        
        // Reject -1
        assertThrows(IllegalArgumentException.class,()->RootNaturalTimeline.terminalCloseWire(close(-1)));
    }
    @Test void terminalCloseWireRejectsMismatchedDateActorAndIncorrectJsonTypes() {
        var original=close(Integer.MIN_VALUE+2);
        for(String token:List.of("true","1.0","\"-2147483646\"","null","-1","-2147483649","2147483648","7")) {
            var changed=original.arguments().with("expected_played_character_id",
                    OpportunityJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->RootNaturalTimeline.terminalCloseWire(
                    withArguments(original,changed)),token);
        }
        var date=original.arguments().with("expected_date_raw",new OpportunityJson.IntegerValue(BigInteger.valueOf(101)));
        assertThrows(IllegalArgumentException.class,()->RootNaturalTimeline.terminalCloseWire(withArguments(original,date)));
    }
    private static ActionCommand withArguments(ActionCommand original,OpportunityJson.Obj arguments) {
        return new ActionCommand(original.actionId(),original.origin(),original.source(),original.sessionId(),
                original.operation(),arguments,original.expectation(),original.claims(),original.deadline());
    }
    @Test void anEvidenceOrAliasFieldCannotBeSmuggledOntoTheNativeCloseWire() {
        var original=close();var fields=new java.util.LinkedHashMap<>(original.arguments().members());fields.put("material_result_verified",new OpportunityJson.Bool(true));
        var changed=new ActionCommand(original.actionId(),original.origin(),original.source(),original.sessionId(),original.operation(),new OpportunityJson.Obj(fields),original.expectation(),original.claims(),original.deadline());assertThrows(IllegalArgumentException.class,()->RootNaturalTimeline.terminalCloseWire(changed));
        fields.remove("material_result_verified");fields.put("expected_played_character_id",new OpportunityJson.DecimalValue("30000.0"));
        var floating=new ActionCommand(original.actionId(),original.origin(),original.source(),original.sessionId(),original.operation(),new OpportunityJson.Obj(fields),original.expectation(),original.claims(),original.deadline());assertThrows(IllegalArgumentException.class,()->RootNaturalTimeline.terminalCloseWire(floating));
    }
}
