package org.xar.ck3.control.application.session;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Explicit DATA/flow tests only. No private Root issuer, canonical native receipt or Managed qualification is manufactured. */
public final class OperatorRebindConsumerTest {
    private static final Instant TIME=Instant.parse("2026-10-23T15:00:00Z");
    private static final SessionIdentity OWNER=new SessionIdentity("fixture-machine-1",new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001"))),"session-1");
    record Data(ActionReceipt actual,SemanticEvidence semantic) { }
    private static ExactRef ref(String role){return new ExactRef("D:/fixture/operator-data-"+role+".json",1,ActionCodec.sha256(role.getBytes(java.nio.charset.StandardCharsets.UTF_8)));}
    private static ObservationIdentity frame(long actor,long revision,String snapshot){return new ObservationIdentity(OWNER.machineId(),OWNER.game(),
            new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(revision),BigInteger.valueOf(24000)),snapshot,BigInteger.valueOf(revision),"episode-1"),1);}
    static Data data(){
        var before=frame(29829,1,"operator-data-before");var after=frame(123,2,"operator-data-rebound");
        var source=new G2Source(OWNER.machineId(),TIME.toString(),"fixture-build",ref("source"));
        var request=new OperatorPlayerSwitch.Request(123,BigInteger.ONE);var origin=new CommandOrigin.Gameplay(before);
        var refs=new OperatorPlayerSwitch.Artifacts(ref("hello"),ref("before-native"),ref("ack"),ref("after-native"),ref("before-driver"),ref("after-driver"),
                ref("before-aux"),ref("after-aux"),ref("canonical"),ref("private-proof-data-only"),ref("rebound-full-sem"));
        var expected=new OperatorRebindExpectation(origin,source,request,"episode-1",1,refs.beforeDriver());
        var command=new ActionCommand("operator-data",origin,source,OWNER.sessionId(),new OperationKey(request.step()),new OpportunityJson.Obj(Map.of()),
                new CommandExpectation.OperatorRebind(expected),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),TIME.plusSeconds(10));
        String nativeId=RequestIds.forCommand(command);RawJson token=new RawJson("{\"status\":\"switched\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var guard=new GuardEvidence(before,source,OWNER.sessionId(),BigInteger.ONE,command.operation(),ref("manifest"),ref("binding"),"fixture",TIME,TIME.plusSeconds(10));
        var attempt=new ActionState.Attempt(nativeId,TIME,guard,new NativeRequest(request.step(),Optional.of(OperatorPlayerSwitch.CAPABILITY),new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        var dispatch=new NativeActionPort.AckReceived(nativeId,true,Optional.of(token),token,token.bytes());
        var completion=new OperatorPlayerSwitch.Completion(request,command.actionId(),ActionCodec.bodySha256(command),nativeId,source,
                new NativeObservationPort.TransportSession(OWNER.machineId(),OWNER.game(),BigInteger.ONE,OWNER.sessionId()),"episode-1",1,29829,1,2,
                OperatorPlayerSwitch.NativeStatus.SWITCHED,BigInteger.TWO,BigInteger.TWO,24000,refs);
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,dispatch,new ActionState.OperatorRebound(completion)));
        return new Data(receipt,new SemanticEvidence(after,refs.reboundNative(),ref("rebound-raw-native"),ref("driver-stamp"),refs.afterDriver(),TIME.plusSeconds(2)));
    }
    @Test void originalTypedCompletionRoundTripPreservesDistinctFullSemAndNativeRolesWithoutGrantingAuthority()throws Exception {
        Data data=data();var original=((ActionState.OperatorRebound)((ActionState.Settled)data.actual().state()).settlement()).observation();
        assertEquals(original,OperatorPlayerSwitch.decodeCompletion(original.encode()));
        assertEquals(original,requireOperatorEvidence(OWNER,data.actual(),data.semantic()));
        assertNotEquals(data.semantic().semantic(),data.semantic().originalNativePacket());
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,data.actual().outcome());assertFalse(data.actual().visibleGameplay());assertFalse(data.actual().eligibleAdvance());
        ObservationPort source=(owner,deadline)->{throw new AssertionError("operator must not enter ordinary observation");};
        assertThrows(IOException.class,()->source.requireOperatorRebound(OWNER,data.actual(),TIME.plusSeconds(10)));
        BatchJournal journal=input->{throw new AssertionError("operator must not create a SAVE or batch boundary");};
        assertThrows(IOException.class,()->journal.acceptOperatorRebound(OWNER,data.actual(),data.semantic()));
    }
    @Test void wrongSubjectRevisionAndSemanticRoleCannotBePresentedAsTheOriginalOperatorFullSemantic(){
        Data data=data();for(SemanticEvidence wrong:List.of(
                new SemanticEvidence(frame(29829,2,"wrong-player"),data.semantic().semantic(),data.semantic().originalNativePacket(),data.semantic().driverStamp(),data.semantic().originalDriver(),data.semantic().observedAt()),
                new SemanticEvidence(frame(123,3,"wrong-revision"),data.semantic().semantic(),data.semantic().originalNativePacket(),data.semantic().driverStamp(),data.semantic().originalDriver(),data.semantic().observedAt()),
                new SemanticEvidence(data.semantic().frame(),ref("other-sem"),data.semantic().originalNativePacket(),data.semantic().driverStamp(),data.semantic().originalDriver(),data.semantic().observedAt())))
            assertThrows(IllegalArgumentException.class,()->requireOperatorEvidence(OWNER,data.actual(),wrong));
        ObjectNode json=(ObjectNode)StrictJson.parse(((ActionState.OperatorRebound)((ActionState.Settled)data.actual().state()).settlement()).observation().encode());
        for(String invalid:List.of("01","-0","18446744073709551616")){ObjectNode copy=json.deepCopy();copy.put("after_revision",invalid);
            assertThrows(IllegalArgumentException.class,()->OperatorPlayerSwitch.decodeCompletion(StrictJson.canonical(copy)));}
        ObjectNode copy=json.deepCopy();copy.put("after_driver_version",true);assertThrows(IllegalArgumentException.class,()->OperatorPlayerSwitch.decodeCompletion(StrictJson.canonical(copy)));
    }
    /** External actual-Root fixture input only; this helper never constructs a Root source, canonical operator or private admission. */
    public static void assertActualRootAdmission(SessionController original,ContinuityBatchJournal sameJournal,ActionReceipt actual,SemanticEvidence rebound,Instant deadline)throws Exception {
        var pair=original.savedPair();var historical=original.lastReport();var completion=requireOperatorEvidence(original.identity(),actual,rebound);
        assertTrue(completion.rebindPerformed());assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,actual.outcome());
        original.acceptOperatorRebound(actual,deadline);
        assertFalse(original.isQuarantined());assertFalse(original.isRunning());assertFalse(original.isRetired());
        assertEquals(pair,original.savedPair());assertEquals(historical,original.lastReport());
        var current=sameJournal.cycleProof(original.identity(),rebound).orElseThrow();assertEquals(rebound,current.semantic());
        assertFalse(actual.visibleGameplay());assertFalse(actual.eligibleAdvance());
    }
}
