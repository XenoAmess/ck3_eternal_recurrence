package org.xar.ck3.control.continuity.writer;

import java.io.IOException;

/** A commit phase failed. Re-read the same immutable identity; never replay a Game action. */
public final class CommitUncertainException extends IOException {
    private final String eventIdentity;
    private final long proposedSequence;
    public CommitUncertainException(String eventIdentity, long proposedSequence, Throwable cause) {
        super("continuity persistence outcome requires same-identity recovery; no Game replay", cause);
        this.eventIdentity = eventIdentity; this.proposedSequence = proposedSequence;
    }
    public String eventIdentity() { return eventIdentity; }
    public long proposedSequence() { return proposedSequence; }
}
