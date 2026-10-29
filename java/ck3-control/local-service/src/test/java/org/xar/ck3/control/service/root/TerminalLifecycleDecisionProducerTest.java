package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual command producer -> sole codec -> typed terminal consumer. These fixtures mint no Root live lease or action outcome. */
final class TerminalLifecycleDecisionProducerTest {
    @TempDir Path temporary;
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private ExactRef file(String name)throws Exception {byte[] bytes=("actual test original "+name).getBytes(StandardCharsets.UTF_8);Path path=temporary.resolve(name);Files.write(path,bytes);return new ExactRef(path.toString(),bytes.length,ActionCodec.sha256(bytes));}
    private record Fixture(LifecycleIdentity identity,G2Source source) { }
    private Fixture fixture(LifecycleIdentity.CurrentPlayer player,LifecycleIdentity.TerminalReason reason)throws Exception {
        var source=new G2Source("decision-fixture",AT.toString(),"decision-test-source",file("source-"+reason+"-"+player.getClass().getSimpleName()));
        var identity=new LifecycleIdentity("decision-fixture",GAME,"decision-session",BigInteger.valueOf(5),
                new LifecycleIdentity.Subject(BigInteger.valueOf(73),"original-episode",9,81),
                new LifecycleIdentity.Frame("original-native",BigInteger.valueOf(123),BigInteger.valueOf(7),BigInteger.valueOf(1000),true,true),player,reason,
                new LifecycleIdentity.Evidence(file("native-"+reason+"-"+player.getClass().getSimpleName()),file("hello-"+reason+"-"+player.getClass().getSimpleName()),
                        file("manifest-"+reason+"-"+player.getClass().getSimpleName()),file("driver-"+reason+"-"+player.getClass().getSimpleName()),file("qualification-"+reason+"-"+player.getClass().getSimpleName())),AT);
        return new Fixture(identity,source);
    }
    @Test void canonicalThreeCommandProducerRoundTripsIntoTerminalConsumerWithZeroOrdinaryCredit()throws Exception {
        for(var operation:List.of(LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL,LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,
                LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR)) {
            boolean natural=operation==LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR;
            var f=fixture(new LifecycleIdentity.Character(BigInteger.valueOf(natural?74:73),natural),natural?LifecycleIdentity.TerminalReason.CHANGED:LifecycleIdentity.TerminalReason.DEAD);
            var produced=TerminalLifecycleDecisionProducer.command(f.identity,f.source,operation,AT.plusSeconds(30));
            var decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(produced));
            assertEquals(produced,decoded);assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(123)),decoded.arguments().get("expected_revision"));
            assertEquals(new BigInteger("9007199254740993"),decoded.lifecycleBefore().game().creationFiletime().value());
            assertTrue(decoded.claims().characterIds().isEmpty());assertTrue(decoded.claims().armyIds().isEmpty());
            assertEquals(3,decoded.lifecycleExpected().values().size());assertTrue(decoded.lifecycleExpected().values().stream().allMatch(value->value instanceof ExpectedBoolean bool&&!bool.value()));
            var consumer=new SessionPorts.TerminalReady(f.identity,new SessionPorts.TerminalAction(decoded));assertSame(decoded,((SessionPorts.TerminalAction)consumer.decision()).command());
            assertThrows(IllegalStateException.class,decoded::before);assertThrows(IllegalStateException.class,decoded::expected);
        }
    }
    @Test void missingAndExplicitNullStayDistinctThroughActualCommandCodec()throws Exception {
        var missing=fixture(new LifecycleIdentity.Missing(),LifecycleIdentity.TerminalReason.MISSING);
        var explicit=fixture(new LifecycleIdentity.Null(),LifecycleIdentity.TerminalReason.MISSING);
        var first=TerminalLifecycleDecisionProducer.command(missing.identity,missing.source,LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL,AT.plusSeconds(1));
        var second=TerminalLifecycleDecisionProducer.command(explicit.identity,explicit.source,LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL,AT.plusSeconds(1));
        assertInstanceOf(LifecycleIdentity.Missing.class,ActionCodec.decodeCommand(ActionCodec.encodeCommand(first)).lifecycleBefore().currentPlayer());
        assertInstanceOf(LifecycleIdentity.Null.class,ActionCodec.decodeCommand(ActionCodec.encodeCommand(second)).lifecycleBefore().currentPlayer());
        assertNotEquals(first.actionId(),second.actionId());assertThrows(IllegalArgumentException.class,()->new SessionPorts.TerminalReady(missing.identity,new SessionPorts.TerminalAction(second)));
    }
    @Test void actualCanonicalUnknownOrderingPrecedesAnyFreshTerminalActionAndKeepsOrdinaryReceipt()throws Exception {
        var f=fixture(new LifecycleIdentity.Character(BigInteger.valueOf(74),true),LifecycleIdentity.TerminalReason.CHANGED);
        var terminal=TerminalLifecycleDecisionProducer.command(f.identity,f.source,LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR,AT.plusSeconds(1));
        var ordinaryBefore=new ObservationIdentity(f.identity.machineId(),GAME,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.valueOf(6),BigInteger.valueOf(999)),"pre-death",BigInteger.valueOf(6),"original-episode"),1);
        var expected=new ExpectedPostcondition(1,ordinaryBefore,f.source,"original-clock-result/v1",List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false)));
        var ordinary=new ActionCommand("original-clock",ordinaryBefore,f.source,f.identity.sessionId(),new OperationKey("resume-map"),new OpportunityJson.Obj(Map.of()),expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),AT.plusSeconds(1));
        var a=new ActionReceipt(1,12,terminal,ActionCodec.bodySha256(terminal),new ActionState.IntentDurable());
        var b=new ActionReceipt(1,8,ordinary,ActionCodec.bodySha256(ordinary),new ActionState.IntentDurable());
        var owner=new SessionPorts.SessionIdentity(f.identity.machineId(),GAME,f.identity.sessionId());
        assertSame(b,TerminalLifecycleDecisionProducer.firstUnresolved(List.of(a,b),owner,Optional.of(f.source)).orElseThrow());
        assertTrue(TerminalLifecycleDecisionProducer.firstUnresolved(List.of(a,b),new SessionPorts.SessionIdentity(f.identity.machineId(),new GameGeneration(43,GAME.creationFiletime()),f.identity.sessionId()),Optional.of(f.source)).isEmpty());
        assertFalse(b.settled());assertFalse(b.visibleGameplay());assertFalse(b.eligibleAdvance());
        assertEquals(73,b.command().before().frame().identity().player().intValueExact());
    }
}
