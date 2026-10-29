package org.xar.ck3.control.wave2.governance.marriagehandoff;

import java.util.Objects;

/** Immutable local bookkeeping contracts. None of these values authorizes succession or replay. */
public final class MarriageHandoffModel {
    public static final String LEDGER_SCHEMA = "xar.ck3.first-heir-marriage-formal.v1";
    public static final String REQUEST_SCHEMA = "xar.java-family-marriage-episode-handoff/v1";
    private MarriageHandoffModel() { }

    /** Native CharacterID, rather than a JavaScript floating point identity. */
    public record CharacterId(long value) {
        public CharacterId {
            if (value <= 0 || value > 0xffff_ffffL) { throw new IllegalArgumentException("positive uint32 CharacterID required"); }
        }
    }

    public record Handoff(String sourceEpisodeRunId, String successorEpisodeRunId,
                          CharacterId predecessorCharacterId, CharacterId successorCharacterId) {
        public Handoff {
            episode(sourceEpisodeRunId); episode(successorEpisodeRunId);
            Objects.requireNonNull(predecessorCharacterId); Objects.requireNonNull(successorCharacterId);
            if (sourceEpisodeRunId.equals(successorEpisodeRunId)) { throw new IllegalArgumentException("natural successor needs a new episode"); }
            if (predecessorCharacterId.equals(successorCharacterId)) { throw new IllegalArgumentException("natural successor needs a different played character"); }
        }
    }

    public enum Presence { MISSING, NULL, VALUE }
    public record EpisodeField(Presence presence, String value) {
        public EpisodeField {
            Objects.requireNonNull(presence);
            if (presence == Presence.VALUE) { episode(value); }
            else if (value != null) { throw new IllegalArgumentException("absent episode cannot carry a value"); }
        }
        public boolean matches(String expected) { return presence == Presence.VALUE && value.equals(expected); }
    }

    /** Validated JSON extension container, kept intact rather than interpreted as a result verdict. */
    public static final class PreservedObject {
        private final String json;
        PreservedObject(String json) { this.json = Objects.requireNonNull(json); }
        String json() { return json; }
        @Override public boolean equals(Object other) { return other instanceof PreservedObject object && MarriageHandoffCodec.sameJson(json, object.json); }
        @Override public int hashCode() { return MarriageHandoffCodec.jsonHash(json); }
    }

    public record FamilyRecord(PreservedObject source, EpisodeField episode) {
        public FamilyRecord {
            Objects.requireNonNull(source); Objects.requireNonNull(episode);
            MarriageHandoffCodec.requireRecordProjection(source, episode);
        }
    }

    /** Missing history differs from an empty history; source retains every undeclared SDK field. */
    public record Ledger(PreservedObject source, FamilyRecord pending, FamilyRecord resolved,
                         boolean historyPresent) {
        public Ledger {
            Objects.requireNonNull(source);
            MarriageHandoffCodec.requireLedgerProjection(source, pending, resolved, historyPresent);
        }
    }

    public record Request(boolean stateDirectoryPresent, Handoff handoff, Ledger ledger) {
        public Request {
            Objects.requireNonNull(handoff);
            if (stateDirectoryPresent != (ledger != null)) { throw new IllegalArgumentException("ledger exists exactly when the state directory is supplied"); }
        }
    }

    public record Receipt(Handoff handoff, boolean pendingArchived, boolean resolvedArchived) {
        public Receipt {
            Objects.requireNonNull(handoff);
            if (!pendingArchived && !resolvedArchived) { throw new IllegalArgumentException("archive receipt requires an archived record"); }
        }
        public boolean ck3CommandSubmitted() { return false; }
    }

    /** Proposed original-writer update, never a persisted or native-completed acknowledgement. */
    public sealed interface Reduction permits Unchanged, Archived { }
    public record Unchanged(Ledger ledger) implements Reduction { }
    public record Archived(Ledger before, Ledger after, Receipt receipt) implements Reduction {
        public Archived { Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(receipt); }
    }

    private static void episode(String value) {
        if (value == null || value.isEmpty() || value.codePointCount(0, value.length()) > 32_768) {
            throw new IllegalArgumentException("bounded nonempty episode identity required");
        }
        org.xar.ck3.control.contracts.StrictJson.text(value);
    }
}
