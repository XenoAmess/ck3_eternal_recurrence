package org.xar.ck3.control.service.root;

import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.contracts.ExactRef;
import static org.junit.jupiter.api.Assertions.*;

/** Actual pure classification only: no private restoration proof, packet or SavedOrigin is fabricated. */
final class RestoredFeastOriginalTest {
    private static final ExactRef REF=new ExactRef("synthetic-restored-feast",1,"a".repeat(64));
    private static FeastDomainRuntime.Resolved activity() {
        return new FeastDomainRuntime.Resolved(REF,REF,ActionReceipt.Outcome.APPLIED_CONFIRMED,
                Optional.of(new FeastDomainRuntime.ActivityOrigin(REF,Optional.empty())));
    }
    @Test void actualKnownNoActivityDoesNotMakeAllFirstRestoresFail() {
        var known=new FeastDomainRuntime.Ledger(Optional.empty(),Optional.empty());
        assertEquals(RestoredFeastOriginal.Disposition.NONE,RestoredFeastOriginal.classify(known,SavedCheckpointMaterial.Kind.FIRST_BASELINE));
        assertEquals(RestoredFeastOriginal.Disposition.NONE,RestoredFeastOriginal.classify(known,SavedCheckpointMaterial.Kind.ORDINARY));
    }
    @Test void pendingUnknownWinsOverAnyRetainedResolvedOriginAndIsNotClassifiedAbsent() {
        var unknown=new FeastDomainRuntime.Ledger(Optional.of(new FeastDomainRuntime.Pending("synthetic-old-episode",REF,"b".repeat(64))),Optional.of(activity()));
        byte[] before=FeastDomainRuntime.encode(unknown);
        for(var kind:SavedCheckpointMaterial.Kind.values())assertEquals(RestoredFeastOriginal.Disposition.PENDING,RestoredFeastOriginal.classify(unknown,kind));
        assertArrayEquals(before,FeastDomainRuntime.encode(unknown));
    }
    @Test void firstActivityCannotBorrowTheOrdinaryHistoricalGuardOrNativeAdoption() {
        var actual=new FeastDomainRuntime.Ledger(Optional.empty(),Optional.of(activity()));
        assertEquals(RestoredFeastOriginal.Disposition.FIRST_ACTIVITY,RestoredFeastOriginal.classify(actual,SavedCheckpointMaterial.Kind.FIRST_BASELINE));
        assertEquals(RestoredFeastOriginal.Disposition.ORDINARY_ACTIVITY,RestoredFeastOriginal.classify(actual,SavedCheckpointMaterial.Kind.ORDINARY));
    }
}
