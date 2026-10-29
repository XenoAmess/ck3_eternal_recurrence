package org.xar.ck3.control.wave2.finance.giftpending;

import java.math.BigInteger;
import java.util.Optional;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;

/** Validated projection required by existing budget, proposal and private planning readers. */
public final class GiftPendingConsumerAdapter {
    private GiftPendingConsumerAdapter() { }
    public record PendingRecovery(String requestId, BigInteger sourceFactionId, BigInteger recipientCharacterId) { }
    public record View(Ledger ledger, Optional<PendingRecovery> recovery) {
        public boolean spendingBlocked() { return ledger.blocksNewSubmission(); }
        public boolean giftSubmissionEnabled() { return false; }
        public boolean publicCapabilityAdvertised() { return false; }
        public boolean sameLedgerAs(Ledger reobserved) { return ledger.equals(reobserved); }
    }
    public static View read(byte[] originalLedger) {
        Ledger ledger = GiftPendingCodec.decodeLedger(originalLedger);
        return new View(ledger, ledger.pending().map(value -> new PendingRecovery(value.requestId(),
                value.baseline().sourceFactionId(), value.baseline().recipientCharacterId())));
    }
}
