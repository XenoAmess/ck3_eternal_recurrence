package org.xar.ck3.control.wave2.military.prewaradmission;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Detached projected boundary. No field in this model certifies native provenance by itself. */
public record PrewarAdmissionInput(Field<Snapshot> snapshot, Declaration declaration) {
    public PrewarAdmissionInput {
        Objects.requireNonNull(snapshot, "snapshot");
        Objects.requireNonNull(declaration, "declaration");
        if (snapshot.presence() == Presence.MISSING) { throw new IllegalArgumentException("snapshot required"); }
    }

    public enum Presence { MISSING, NULL, VALUE }

    public record Field<T>(Presence presence, T value) {
        public Field {
            Objects.requireNonNull(presence, "presence");
            if ((presence == Presence.VALUE) != (value != null)) {
                throw new IllegalArgumentException("only present values carry a non-null value");
            }
        }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nullValue() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
        public boolean hasValue() { return presence == Presence.VALUE; }
        public boolean isPresent() { return presence != Presence.MISSING; }
    }

    public record PlayedCharacter(Field<Boolean> alive, Field<BigInteger> characterId) {
        public PlayedCharacter { Objects.requireNonNull(alive); Objects.requireNonNull(characterId); }
    }

    public record Hello(Field<String> bridgeVersion, Field<String> expectedCk3Version, Field<String> expectedCk3Sha256) {
        public Hello {
            Objects.requireNonNull(bridgeVersion); Objects.requireNonNull(expectedCk3Version);
            Objects.requireNonNull(expectedCk3Sha256);
        }
    }

    public record Diagnostics(Field<Hello> hello, Field<BigInteger> connectionGeneration) {
        public Diagnostics { Objects.requireNonNull(hello); Objects.requireNonNull(connectionGeneration); }
    }

    public record Declaration(Field<String> declarationId, Field<BigInteger> targetCharacterId,
            Field<BigInteger> casusBelliIndex, Field<String> casusBelliKey, Field<BigInteger> configurationIndex,
            Field<BigInteger> claimantCharacterId, Field<List<BigInteger>> targetTitleIds) {
        public Declaration {
            Objects.requireNonNull(declarationId); Objects.requireNonNull(targetCharacterId);
            Objects.requireNonNull(casusBelliIndex); Objects.requireNonNull(casusBelliKey);
            Objects.requireNonNull(configurationIndex); Objects.requireNonNull(claimantCharacterId);
            Objects.requireNonNull(targetTitleIds);
            if (targetTitleIds.hasValue()) { targetTitleIds = Field.of(List.copyOf(targetTitleIds.value())); }
        }
    }

    /** Dynamic JSON is confined to the two bare native boundary objects owned by coalition validation. */
    public static final class DetachedObject {
        private final ObjectNode value;
        public DetachedObject(ObjectNode value) { this.value = Objects.requireNonNull(value).deepCopy(); }
        public ObjectNode copy() { return value.deepCopy(); }
        @Override public boolean equals(Object other) {
            return other instanceof DetachedObject detached && value.equals(detached.value);
        }
        @Override public int hashCode() { return value.hashCode(); }
    }

    public record QueryEnvelope(Field<String> queriedSnapshotId, Field<BigInteger> queriedRevision,
            Field<BigInteger> queriedNativeRevision, Field<BigInteger> queriedDateRaw,
            Field<BigInteger> queriedActorCharacterId, Field<BigInteger> queriedConnectionGeneration,
            Field<String> queriedEpisodeRunId, Field<Boolean> accepted, Field<String> status,
            Field<DetachedObject> executionReceipt, Field<String> nativeRequestId,
            Field<DetachedObject> coverage) {
        public QueryEnvelope {
            Objects.requireNonNull(queriedSnapshotId); Objects.requireNonNull(queriedRevision);
            Objects.requireNonNull(queriedNativeRevision); Objects.requireNonNull(queriedDateRaw);
            Objects.requireNonNull(queriedActorCharacterId); Objects.requireNonNull(queriedConnectionGeneration);
            Objects.requireNonNull(queriedEpisodeRunId); Objects.requireNonNull(accepted); Objects.requireNonNull(status);
            Objects.requireNonNull(executionReceipt); Objects.requireNonNull(nativeRequestId); Objects.requireNonNull(coverage);
        }
    }

    public record Snapshot(Field<Boolean> paused, Field<Boolean> mapReady, Field<PlayedCharacter> playedCharacter,
            Field<Diagnostics> diagnostics, Field<String> snapshotId, Field<BigInteger> revision,
            Field<BigInteger> nativeRevision, Field<BigInteger> dateRaw, Field<String> episodeRunId,
            Field<BigInteger> captureEpoch, Field<List<Declaration>> declarableWars, Field<QueryEnvelope> query) {
        public Snapshot {
            Objects.requireNonNull(paused); Objects.requireNonNull(mapReady); Objects.requireNonNull(playedCharacter);
            Objects.requireNonNull(diagnostics); Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision);
            Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(episodeRunId);
            Objects.requireNonNull(captureEpoch); Objects.requireNonNull(declarableWars); Objects.requireNonNull(query);
            if (declarableWars.hasValue()) { declarableWars = Field.of(List.copyOf(declarableWars.value())); }
        }
    }
}
