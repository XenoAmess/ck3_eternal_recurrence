package org.xar.ck3.control.wave2.planning.jointintake;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Typed, immutable scope for collecting already observed domain proposals. */
public final class IntakeModel {
    private IntakeModel() { }
    public enum Domain { war, council, building, marriage, diplomacy, lifestyle }
    public record Frame(BigInteger playedCharacterId, BigInteger nativeRevision, BigInteger dateRaw,
                        String snapshotId, BigInteger revision, String episodeRunId) {
        public Frame {
            positive(playedCharacterId); positive(nativeRevision); positive(revision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(snapshotId); Objects.requireNonNull(episodeRunId);
            if (dateRaw.signum() < 0 || snapshotId.isEmpty() || episodeRunId.isEmpty()) throw new IllegalArgumentException("incomplete observed frame");
        }
    }
    public record Identity(Domain domain, String candidateId) {
        public Identity { Objects.requireNonNull(domain); Objects.requireNonNull(candidateId);
            if (candidateId.isEmpty()) throw new IllegalArgumentException("empty proposal identity"); }
    }
    public record Budget(BigInteger goldReserveRaw, BigInteger maxActiveWars) {
        public Budget { nonnegative(goldReserveRaw); nonnegative(maxActiveWars); }
    }
    public record Collection(Frame frame, List<Identity> candidates, Budget budget) {
        public Collection { Objects.requireNonNull(frame); candidates = List.copyOf(candidates); Objects.requireNonNull(budget); }
        public List<String> domains() { return candidates.stream().map(row -> row.domain().name()).distinct().toList(); }
        public List<String> candidateIds() { return candidates.stream().map(Identity::candidateId).toList(); }
    }
    private static void positive(BigInteger value) { if (value == null || value.signum() <= 0) throw new IllegalArgumentException("positive identity required"); }
    private static void nonnegative(BigInteger value) { if (value == null || value.signum() < 0) throw new IllegalArgumentException("nonnegative budget required"); }
}
