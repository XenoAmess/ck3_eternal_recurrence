package org.xar.ck3.control.wave3.governance.crownfinalterms;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown.RawObservation;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown.TurnTick;

/** Immutable full-cost law read contracts. This port has no native or action I/O. */
public final class CrownFinalTerms {
    public static final String SCHEMA = "realm-law-final-terms-private-read-v1";
    public static final String STEP = "query-realm-law-final-terms-v1-private";
    public static final List<String> SLOTS = List.of("gold", "prestige", "piety", "renown", "influence", "herd",
            "treasury", "treasury_or_gold", "merit", "barter_goods");
    private CrownFinalTerms() { }

    public enum Build {
        LEGACY_11906("1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),
        CK3_12002("1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"),
        CK3_12003("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
        CK3_12004("1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        private final String version;
        private final String sha256;
        Build(String version, String sha256) { this.version = version; this.sha256 = sha256; }
        public String version() { return version; }
        public String sha256() { return sha256; }
        public boolean profileRows() { return this == CK3_12003 || this == CK3_12004; }
    }

    public enum GroupKey { CROWN_AUTHORITY, SUCCESSION_ORDER_LAWS }
    public enum FinalStatus { CANDIDATE_KIND_REJECTED, ALREADY_ACTIVE, ENGINE_BLOCKED, CAN_ENACT }
    public enum ProfileStatus { AVAILABLE, ABSENT, UNAVAILABLE }
    public enum Order { INHERITANCE, ELECTION, APPOINTMENT, THEOCRATIC, COMPANY, GENERATE, GENERATE_FROM_TEMPLATE, PLAYER_HEIR, NOBLE_FAMILY }
    public enum Traversal { CHILDREN, DYNASTY_HOUSE, DYNASTY }
    public enum Rank { OLDEST, YOUNGEST }
    public enum Division { SINGLE_HEIR, PARTITION }

    public record SuccessionProfile(Order order, Traversal traversal, Rank rank, Division division,
            long primaryHeirMinimumShareRaw, boolean createPrimaryTierTitles) { }
    public record Candidate(String lawKey, boolean active, FinalStatus finalStatus, boolean finalCanEnact,
            String nativeReason, List<Long> costRaw, ProfileStatus profileStatus, SuccessionProfile profile) {
        public Candidate { Objects.requireNonNull(lawKey); Objects.requireNonNull(finalStatus); Objects.requireNonNull(nativeReason); costRaw = List.copyOf(costRaw); }
    }
    public record Group(GroupKey key, String activeLawKey, List<Candidate> candidates) {
        public Group { Objects.requireNonNull(key); candidates = List.copyOf(candidates); }
    }
    public record Payload(BigInteger snapshotRevision, BigInteger dateRaw, BigInteger actorCharacterId,
            List<Group> groups, RawObservation cooldown, TurnTick turnTick) {
        public Payload { Objects.requireNonNull(snapshotRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(actorCharacterId); groups = List.copyOf(groups); }
    }
    public record SourceFrame(BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw,
            BigInteger actorCharacterId, boolean paused, boolean mapReady, boolean alive,
            String snapshotId, Build build) { }
    public record NativeRequest(String requestId, BigInteger expectedNativeRevision) {
        public NativeRequest {
            Objects.requireNonNull(requestId); Objects.requireNonNull(expectedNativeRevision);
            require(!requestId.isEmpty() && requestId.length() <= 128 && expectedNativeRevision.signum() > 0,
                    "bounded request identity and positive native revision required");
        }
    }
    public record Readback(Payload payload, Build build, String queriedSnapshotId, BigInteger queriedRevision,
            BigInteger queriedNativeRevision, String postSnapshotId) { }

    public static NativeRequest prepare(boolean enabled, BigInteger expectedRevision, String requestId, SourceFrame before) {
        require(enabled, "private realm-law query is disabled");
        require(expectedRevision != null && expectedRevision.signum() > 0, "expected_revision must be positive");
        require(Objects.equals(before.revision(), expectedRevision) && before.paused() && before.mapReady() && before.alive()
                && before.actorCharacterId() != null && before.actorCharacterId().signum() > 0
                && before.nativeRevision() != null && before.nativeRevision().signum() > 0 && before.dateRaw() != null,
                "private realm-law query requires a living paused actor");
        Objects.requireNonNull(before.build());
        return new NativeRequest(requestId, before.nativeRevision());
    }

    static void require(boolean condition, String reason) { if (!condition) { throw new ProjectionDomainRejection(reason); } }
}
