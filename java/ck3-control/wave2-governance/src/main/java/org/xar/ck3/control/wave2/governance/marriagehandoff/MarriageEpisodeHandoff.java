package org.xar.ck3.control.wave2.governance.marriagehandoff;

import java.util.Objects;
import static org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffModel.*;

/** Pure counterpart of archive_predecessor_family_marriage_v1; original driver retains admission and its writer lock. */
public final class MarriageEpisodeHandoff {
    private MarriageEpisodeHandoff() { }

    public static Reduction reduce(Request request) {
        Objects.requireNonNull(request);
        if (!request.stateDirectoryPresent()) { return new Unchanged(null); }
        Ledger ledger = request.ledger(); Handoff handoff = request.handoff();
        boolean pending = ledger.pending() != null && ledger.pending().episode().matches(handoff.sourceEpisodeRunId());
        boolean resolved = ledger.resolved() != null && ledger.resolved().episode().matches(handoff.sourceEpisodeRunId());
        if (!pending && !resolved) { return new Unchanged(ledger); }
        Ledger after = MarriageHandoffCodec.archive(ledger, handoff, pending, resolved);
        return new Archived(ledger, after, new Receipt(handoff, pending, resolved));
    }
}
