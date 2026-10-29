package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

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
import org.xar.ck3.control.application.advance.GenericPublicPauseRecovery;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Software contract DATA. These cases never construct an Installed, Managed or native source authority. */
final class RootPublicPauseArchiveClassifierTest {
    private static final Instant T=Instant.parse("2026-10-24T19:00:00Z");
    private static final String SESSION="software-classifier-session";
    private static ExactRef ref(String text){
        byte[] bytes=text.getBytes(StandardCharsets.UTF_8);
        return new ExactRef("software/classifier/"+text,bytes.length,ActionCodec.sha256(bytes));
    }
    private static ObservationIdentity identity(long revision){
        return new ObservationIdentity("software-public-pause-classifier",
                new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                        BigInteger.valueOf(revision),BigInteger.valueOf(1000)),"software-native-"+revision,
                        BigInteger.valueOf(revision),"software-episode"),1);
    }
    private static G2Source source(){return new G2Source(identity(1).machineId(),T.toString(),"1.20.0.4",ref("source"));}
    private static JointBudgetSelector.Claims noClaims(){return new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of());}
    private static ActionCommand parent(){
        return new ActionCommand("software-classifier-parent",identity(1),source(),SESSION,
                GenericPublicPauseRecovery.OPERATION,new OpportunityJson.Obj(Map.of()),
                GenericPublicPauseRecovery.expected(identity(1),source()),noClaims(),T.plusSeconds(30));
    }
    private static ActionCommand changed(ActionCommand parent,OperationKey operation,OpportunityJson.Obj arguments,
            ExpectedPostcondition expected,JointBudgetSelector.Claims claims){
        return new ActionCommand(parent.actionId(),parent.origin(),parent.source(),parent.sessionId(),operation,
                arguments,new CommandExpectation.Gameplay(expected),claims,parent.deadline());
    }
    private static void requireParent(ActionCommand parent){
        RootPublicPauseArchiveClassifier.requireParentContract(parent,identity(1).game(),SESSION,source());
    }
    private static CompositeExecution execution(String handler,List<CompositeExecution.Child> children){
        var command=parent();
        var guard=new GuardEvidence(command.before(),command.source(),SESSION,BigInteger.ONE,command.operation(),
                ref("native"),ref("hello"),"software-DATA-no-qualification",T,T.plusSeconds(30));
        return new CompositeExecution(handler,T,guard,children);
    }
    private static List<CompositeExecution.Child> children(){
        return List.of(new CompositeExecution.Child("software-classifier-child","a".repeat(64)));
    }
    private static ActionReceipt receipt(ActionCommand command,CompositeExecution execution,ActionState.Settlement settlement){
        return new ActionReceipt(1,3,command,ActionCodec.bodySha256(command),new ActionState.CompositeSettled(execution,settlement));
    }
    private static ControlSequenceObservation completed(){
        return new ControlSequenceObservation(parent(),ControlSequenceObservation.Mode.DIRECT_PAUSE,identity(2),ref("report"),
                List.of(new ControlSequenceObservation.Child(children().getFirst().actionId(),children().getFirst().bodySha256(),ref("canonical-child"))),
                List.of(ref("report")));
    }

    @Test void actualCommandCodecPreservesFullSourceAndWideGameIdentity(){
        var original=parent();byte[] bytes=ActionCodec.encodeCommand(original);
        var decoded=ActionCodec.decodeCommand(bytes);assertEquals(original,decoded);assertArrayEquals(bytes,ActionCodec.encodeCommand(decoded));
        requireParent(decoded);
        assertEquals(new BigInteger("133700000000000001"),decoded.before().game().creationFiletime().value());
    }
    @Test void gameSessionAndSourceAreSeparateMandatoryScopes(){
        var command=parent();
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.requireParentContract(command,
                new GameGeneration(124,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),SESSION,source()));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.requireParentContract(command,
                identity(1).game(),"foreign-session",source()));
        var foreign=new G2Source(source().machineId(),T.plusSeconds(1).toString(),"1.20.0.4",ref("different-source"));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.requireParentContract(command,
                identity(1).game(),SESSION,foreign));
    }
    @Test void primitiveArgumentsObserverAndBusinessClaimsCannotBorrowParentClassification(){
        var command=parent();
        assertThrows(IllegalArgumentException.class,()->requireParent(changed(command,new OperationKey("pause-map"),
                command.arguments(),command.expected(),command.claims())));
        assertThrows(IllegalArgumentException.class,()->requireParent(changed(command,command.operation(),
                new OpportunityJson.Obj(Map.of("unexpected",new OpportunityJson.Bool(true))),command.expected(),command.claims())));
        var observer=new ExpectedPostcondition(1,command.before(),command.source(),"foreign-observer",command.expected().values());
        assertThrows(IllegalArgumentException.class,()->requireParent(changed(command,command.operation(),command.arguments(),observer,command.claims())));
        var claims=new JointBudgetSelector.Claims(Set.of(BigInteger.ONE),Set.of(),Set.of(),Set.of());
        assertThrows(IllegalArgumentException.class,()->requireParent(changed(command,command.operation(),command.arguments(),command.expected(),claims)));
    }
    @Test void actualCommandReaderRejectsMissingNullUnknownAndNonIntegerVersions(){
        byte[] bytes=ActionCodec.encodeCommand(parent());
        var missing=(ObjectNode)StrictJson.parse(bytes);missing.remove("source");
        assertThrows(IllegalArgumentException.class,()->ActionCodec.decodeCommand(StrictJson.canonical(missing)));
        var nullSource=(ObjectNode)StrictJson.parse(bytes);nullSource.putNull("source");
        assertThrows(IllegalArgumentException.class,()->ActionCodec.decodeCommand(StrictJson.canonical(nullSource)));
        var unknown=(ObjectNode)StrictJson.parse(bytes);unknown.put("source_alias","forbidden");
        assertThrows(IllegalArgumentException.class,()->ActionCodec.decodeCommand(StrictJson.canonical(unknown)));
        var boolVersion=(ObjectNode)StrictJson.parse(bytes);((ObjectNode)boolVersion.get("expected")).put("version",true);
        assertThrows(IllegalArgumentException.class,()->ActionCodec.decodeCommand(StrictJson.canonical(boolVersion)));
        var floatVersion=(ObjectNode)StrictJson.parse(bytes);((ObjectNode)floatVersion.get("expected")).put("version",new java.math.BigDecimal("1.0"));
        assertThrows(IllegalArgumentException.class,()->ActionCodec.decodeCommand(StrictJson.canonical(floatVersion)));
    }
    @Test void originalControlCodecFeedsStrictTerminalContractWithoutGameplayOrSaveCredit(){
        var original=completed();byte[] bytes=original.encode();var decoded=ControlSequenceObservation.decode(bytes);
        assertEquals(original,decoded);assertArrayEquals(bytes,decoded.encode());
        var receipt=receipt(parent(),execution(RootPublicPauseRuntime.HANDLER,children()),new ActionState.ControlSequenceCompleted(decoded));
        RootPublicPauseArchiveClassifier.requireSettledReceipt(receipt);
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,receipt.outcome());
        assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
        var rejected=receipt(parent(),execution(RootPublicPauseRuntime.HANDLER,children()),
                new ActionState.CompositeRejected("original known native rejection",children(),List.of(ref("negative-report"))));
        RootPublicPauseArchiveClassifier.requireSettledReceipt(rejected);
        assertFalse(rejected.visibleGameplay());assertFalse(rejected.eligibleAdvance());
    }
    @Test void unknownAndRunningParentsRemainBlockingWithTheirExactOriginalState(){
        var execution=execution(RootPublicPauseRuntime.HANDLER,children());var command=parent();
        for(ActionState state:List.of(new ActionState.IntentDurable(),new ActionState.CompositeRunning(execution),
                new ActionState.CompositeUnknown(execution,"original dispatch result unknown",List.of(ref("unknown-original"))))) {
            var original=new ActionReceipt(1,3,command,ActionCodec.bodySha256(command),state);
            assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.requireSettledReceipt(original));
            assertSame(state,original.state());assertEquals(ActionReceipt.Outcome.UNRESOLVED,original.outcome());
        }
    }
    @Test void anotherHandlerSettlementOrChildRosterCannotBorrowTerminalControl(){
        var completed=new ActionState.ControlSequenceCompleted(completed());
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.requireSettledReceipt(
                receipt(parent(),execution("foreign-handler",children()),completed)));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.requireSettledReceipt(
                receipt(parent(),execution(RootPublicPauseRuntime.HANDLER,children()),new ActionState.Rejected("foreign-native","foreign settlement",ref("foreign")))));
        var otherChildren=List.of(new CompositeExecution.Child("foreign-child","b".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.requireSettledReceipt(
                receipt(parent(),execution(RootPublicPauseRuntime.HANDLER,otherChildren),completed)));
        var changed=(ObjectNode)StrictJson.parse(completed().encode());changed.put("mode",true);var boolMode=changed;
        assertThrows(IllegalArgumentException.class,()->ControlSequenceObservation.decode(StrictJson.canonical(boolMode)));
        changed=(ObjectNode)StrictJson.parse(completed().encode());changed.remove("proof");var missing=changed;
        assertThrows(IllegalArgumentException.class,()->ControlSequenceObservation.decode(StrictJson.canonical(missing)));
    }
}
