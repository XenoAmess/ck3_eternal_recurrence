package org.xar.ck3.control.wave2.governance.marriagehandoff;

import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import java.util.Objects;
import static org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffModel.*;

/** Narrow integration projections; deliberately owns no file, native connection, admission flag or writer. */
public final class MarriageHandoffConsumerPort {
    private MarriageHandoffConsumerPort() { }

    /** For the original driver only, under its existing lock after its ordinary M3 reconciliation checks. */
    public static Reduction prepareOriginalWriterUpdate(byte[] strictRequest) {
        return MarriageEpisodeHandoff.reduce(MarriageHandoffCodec.decodeRequest(strictRequest));
    }

    /** Original writer must reread under its lock: a stale proposal cannot erase a later pending record. */
    public static Ledger revalidateOriginalWriterUpdate(Archived proposal, byte[] currentLedger) {
        Objects.requireNonNull(proposal);
        Ledger current = MarriageHandoffCodec.decodeLedger(currentLedger);
        if (!current.equals(proposal.before())) { throw new ProjectionDomainRejection("family ledger changed before original writer commit"); }
        Reduction refreshed = MarriageEpisodeHandoff.reduce(new Request(true, proposal.receipt().handoff(), current));
        if (!(refreshed instanceof Archived archived) || !archived.after().equals(proposal.after())) {
            throw new ProjectionDomainRejection("family handoff reducer no longer matches its proposed update");
        }
        return archived.after();
    }

    /** Every existing ledger consumer receives the identical schema and preserved SDK extension fields. */
    public static byte[] ledgerForExistingConsumers(Ledger ledger) { return MarriageHandoffCodec.encodeLedger(Objects.requireNonNull(ledger)); }
    public static byte[] receiptForOriginalDriver(Receipt receipt) { return MarriageHandoffCodec.encodeReceipt(Objects.requireNonNull(receipt)); }
}
