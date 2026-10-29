package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityPayload;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure production reducer failures. No Core-private NEXT proof or native packet issuer is fabricated. */
final class GovernanceNextInitializationTest {
    private static final ExactRef REF=new ExactRef("synthetic-next-original",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("governance-next-fixture","2026-10-24T00:00:00Z","1.20.0.4",REF);
    private static ObservationIdentity frame(String episode,long player,long pid) {
        return new ObservationIdentity(SOURCE.machineId(),new GameGeneration(pid,new PythonOnlyUInt64(new BigInteger("133700000000000001").add(BigInteger.valueOf(pid)))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(player),BigInteger.TEN,BigInteger.valueOf(1000)),"synthetic-"+episode,BigInteger.TEN,episode),1);
    }
    @Test void nextOpeningUsesTheActualNewPlayerEpisodeAndKeepsTheOriginalEvidence() {
        var before=frame("old-episode",29829,123);var after=frame("new-episode",30000,124);
        var old=new GovernanceOpeningDocument.Document(before,SOURCE,"old-session",OpeningStage.AWAIT_SUBMIT,Optional.empty(),Optional.empty(),List.of(REF));
        var next=GovernanceOpeningDocument.decode(GovernanceNextInitialization.nextOpening(GovernanceOpeningDocument.encode(old),after,SOURCE,"new-session",List.of(REF)));
        assertEquals(after,next.observed());assertEquals("new-session",next.sessionId());assertEquals(OpeningStage.AWAIT_SUBMIT,next.stage());
        assertEquals(List.of(REF),next.originals());assertTrue(next.actionReceipt().isEmpty());assertTrue(next.checkpoint().isEmpty());
        assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.nextOpening(GovernanceOpeningDocument.encode(old),before,SOURCE,"new-session",List.of(REF)));
    }
    @Test void priorPreparedUnknownOpeningIsNotClearedForAnotherPlayer() {
        var old=new GovernanceOpeningDocument.Document(frame("old-episode",29829,123),SOURCE,"old-session",OpeningStage.AWAIT_RECEIPT,
                Optional.empty(),Optional.empty(),List.of(REF),Optional.of(REF),Optional.empty());byte[] original=GovernanceOpeningDocument.encode(old);
        assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.nextOpening(original,frame("new-episode",30000,124),SOURCE,"new-session",List.of(REF)));
        assertArrayEquals(original,GovernanceOpeningDocument.encode(old));
    }
    @Test void oldFeastPendingAndUnfinishedOriginStayUnresolved() {
        var pending=new FeastDomainRuntime.Ledger(Optional.of(new FeastDomainRuntime.Pending("old-episode",REF,"b".repeat(64))),Optional.empty());
        byte[] original=FeastDomainRuntime.encode(pending);assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.requireOldFeastSettled(pending));
        assertArrayEquals(original,FeastDomainRuntime.encode(pending));
        var unfinished=new FeastDomainRuntime.Ledger(Optional.empty(),Optional.of(new FeastDomainRuntime.Resolved(REF,REF,ActionReceipt.Outcome.APPLIED_CONFIRMED,
                Optional.of(new FeastDomainRuntime.ActivityOrigin(REF,Optional.empty())))));
        assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.requireOldFeastSettled(unfinished));
    }
    private static ActivityPayload.Hosted hosted(ActivityPayload.HostedActivity row) {
        return new ActivityPayload.Hosted(List.of(),List.of(row),Optional.empty(),Optional.empty(),Optional.empty(),new OpportunityJson.Obj(java.util.Map.of()));
    }
    @Test void newNativeHostUnknownOrOngoingNeverGrantsClearOrAdoptsAnOldIdentity() {
        var unknown=new ActivityPayload.HostedActivity(0x01000042L,30000,"activity_feast",Optional.empty(),Optional.empty(),Optional.of(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.requireNewFeastClear(hosted(unknown),30000));
        var ongoing=new ActivityPayload.HostedActivity(0x01000042L,30000,"activity_feast",Optional.of(false),Optional.of(false),Optional.of(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.requireNewFeastClear(hosted(ongoing),30000));
        var oldHost=new ActivityPayload.HostedActivity(0x01000042L,29829,"activity_feast",Optional.of(true),Optional.of(false),Optional.empty());
        assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.requireNewFeastClear(hosted(oldHost),30000));
        // Pure reducer acceptance is not packet qualification. The caller still requires the actual native decoder and archive.
        GovernanceNextInitialization.requireNewFeastClear(new ActivityPayload.Hosted(List.of(),List.of(),Optional.empty(),Optional.empty(),Optional.empty(),new OpportunityJson.Obj(java.util.Map.of())),30000);
    }
}
