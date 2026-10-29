package org.xar.ck3.control.wave2.military.exitresult;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** Observation DTOs only: requested outcome, command ACK, war absence and result identity stay separate. */
public final class OrdinaryWarExitObservation {
    public static final String SCHEMA = "xar.ck3.ordinary-war-exit-observation.v1";
    public static final String EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public static final int MAXIMUM_OBSERVED_TITLES = 32;
    private OrdinaryWarExitObservation() { }

    public enum RequestedOutcome {
        PLAYER_VICTORY("player_victory"), WHITE_PEACE("white_peace"), PLAYER_DEFEAT("player_defeat");
        private final String wire;
        RequestedOutcome(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum PlayerSide {
        ATTACKER("attacker"), DEFENDER("defender");
        private final String wire;
        PlayerSide(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum NativeOutcome {
        ATTACKER_VICTORY("attacker_victory"), WHITE_PEACE("white_peace"), ATTACKER_DEFEAT("attacker_defeat");
        private final String wire;
        NativeOutcome(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Availability {
        AVAILABLE("available"), UNAVAILABLE("unavailable");
        private final String wire;
        Availability(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Resource {
        GOLD("gold"), PRESTIGE("prestige"), PIETY("piety");
        private final String wire;
        Resource(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum ClaimState {
        ABSENT("absent"), STRONG_IMPLICIT("strong_implicit"), STRONG_EXPLICIT("strong_explicit"),
        WEAK_IMPLICIT("weak_implicit"), WEAK_EXPLICIT("weak_explicit");
        private final String wire;
        ClaimState(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision, int dateRaw,
                        String episodeRunId, int actorCharacterId, int bridgePid, int connectionGeneration) {
        public Frame {
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            uint64Positive(revision); uint64Positive(nativeRevision);
            require(actorCharacterId >= 0 && bridgePid > 0 && connectionGeneration > 0, "full integer identity unavailable");
        }
    }
    public record Action(long warId, RequestedOutcome requestedOutcome, boolean acknowledged) {
        public Action {
            require(requestedOutcome != null && (requestedOutcome == RequestedOutcome.PLAYER_VICTORY
                    ? warId >= 0 && warId <= 9007199254740991L : warId > 0 && warId <= Integer.MAX_VALUE),
                    "outcome-specific original public war identity required");
        }
    }
    public record Bound(Frame before, Frame post, boolean warAbsent, PlayerSide side, int opponentCharacterId,
                        List<Integer> renderedTitleIds, int targetTitleCount) {
        public Bound {
            require(before != null && post != null && side != null && opponentCharacterId >= 0,
                    "bound action identity required");
            require(before.episodeRunId().equals(post.episodeRunId()) && before.actorCharacterId() == post.actorCharacterId()
                    && before.bridgePid() == post.bridgePid() && before.connectionGeneration() == post.connectionGeneration()
                    && post.dateRaw() >= before.dateRaw() && post.revision().compareTo(before.revision()) >= 0
                    && post.nativeRevision().compareTo(before.nativeRevision()) >= 0, "post frame crossed action identity");
            require(renderedTitleIds != null && renderedTitleIds.size() <= MAXIMUM_OBSERVED_TITLES
                    && targetTitleCount >= renderedTitleIds.size() && targetTitleCount <= 4096,
                    "bounded frozen targets required");
            renderedTitleIds = List.copyOf(renderedTitleIds);
            require(new HashSet<>(renderedTitleIds).size() == renderedTitleIds.size()
                    && renderedTitleIds.stream().allMatch(value -> value >= 0), "unique nonnegative TitleIDs required");
        }
        public NativeOutcome nativeOutcome(RequestedOutcome requested) {
            if (requested == RequestedOutcome.WHITE_PEACE) { return NativeOutcome.WHITE_PEACE; }
            boolean physicalVictory = (requested == RequestedOutcome.PLAYER_VICTORY) == (side == PlayerSide.ATTACKER);
            return physicalVictory ? NativeOutcome.ATTACKER_VICTORY : NativeOutcome.ATTACKER_DEFEAT;
        }
    }
    public record FixedValue(BigInteger raw) {
        public FixedValue {
            require(raw != null && raw.compareTo(BigInteger.valueOf(Long.MIN_VALUE)) >= 0
                    && raw.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "signed int64 fixed value required");
        }
    }
    public record ResourceObservation(Resource resource, FixedValue before, FixedValue after, boolean sameDate) {
        public ResourceObservation { require(resource != null, "typed resource required"); }
        public BigInteger deltaRaw() { return before == null || after == null ? null : after.raw().subtract(before.raw()); }
    }
    public record ClaimRow(int titleId, boolean present, ClaimState state, Boolean strong, Boolean implicit) {
        public ClaimRow {
            require(titleId >= 0 && state != null, "typed claim identity required");
            if (!present) { require(state == ClaimState.ABSENT && strong == null && implicit == null, "absent claim flags required"); }
            else {
                require(strong != null && implicit != null, "present claim flags required");
                ClaimState expected = strong ? (implicit ? ClaimState.STRONG_IMPLICIT : ClaimState.STRONG_EXPLICIT)
                        : (implicit ? ClaimState.WEAK_IMPLICIT : ClaimState.WEAK_EXPLICIT);
                require(state == expected, "claim state disagrees with native flags");
            }
        }
    }
    public sealed interface Claims permits ClaimsNotObserved, ClaimsUnavailable, NativeClaims { }
    public record ClaimsNotObserved() implements Claims { }
    public record ClaimsUnavailable() implements Claims { }
    public record NativeClaims(Availability availability, List<ClaimRow> rows, BigInteger querySequence,
                               String unavailableReason) implements Claims {
        public NativeClaims {
            require(availability != null, "claims availability required");
            uint64Positive(querySequence);
            if (availability == Availability.AVAILABLE) {
                require(rows != null && unavailableReason == null, "available claim rows required");
                rows = List.copyOf(rows);
            } else { require(rows == null && unavailableReason != null && !unavailableReason.isEmpty(), "unknown claim rows required"); }
        }
    }
    public record TitleRow(int titleId, Availability availability, Integer holderCharacterId,
                            Integer immediateLiegeCharacterId, Integer topLiegeCharacterId,
                            Boolean holderInPlayerRealm, String unavailableReason) {
        public TitleRow {
            require(titleId >= 0 && availability != null, "typed title observation required");
            require(holderCharacterId == null || holderCharacterId >= 0, "holder ID required");
            require(immediateLiegeCharacterId == null || immediateLiegeCharacterId >= 0, "immediate liege ID required");
            require(topLiegeCharacterId == null || topLiegeCharacterId >= 0, "top liege ID required");
            if (availability == Availability.UNAVAILABLE) {
                require(holderCharacterId == null && immediateLiegeCharacterId == null && topLiegeCharacterId == null
                        && holderInPlayerRealm == null && unavailableReason != null && !unavailableReason.isEmpty(),
                        "unknown title observation required");
            } else { require(holderInPlayerRealm != null && unavailableReason == null, "available title observation required"); }
        }
    }
    public sealed interface Titles permits TitlesNotObserved, TitlesUnavailable, NativeTitles { }
    public record TitlesNotObserved() implements Titles { }
    public record TitlesUnavailable() implements Titles { }
    public record NativeTitles(List<TitleRow> rows, int totalFrozenTargets) implements Titles {
        public NativeTitles {
            require(rows != null && rows.size() <= MAXIMUM_OBSERVED_TITLES && totalFrozenTargets >= rows.size()
                    && totalFrozenTargets <= 4096, "bounded native title observations required");
            rows = List.copyOf(rows);
        }
        public boolean allFrozenTargetsObserved() {
            return rows.size() == totalFrozenTargets && rows.stream().allMatch(row -> row.availability() == Availability.AVAILABLE);
        }
    }
    public sealed interface Truce permits TruceNotObserved, TruceUnavailable, NativeTruce { }
    public record TruceNotObserved() implements Truce { }
    public record TruceUnavailable() implements Truce { }
    public enum TruceStatus {
        AVAILABLE("available"), NO_TRUCE("no_truce");
        private final String wire;
        TruceStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record NativeTruce(TruceStatus status, int ownerCharacterId, int towardCharacterId,
                              Integer expiryDateRaw, String unavailableReason, BigInteger querySequence) implements Truce {
        public NativeTruce {
            require(status != null && ownerCharacterId >= 0 && towardCharacterId > 0, "directed truce identity required");
            uint64Positive(querySequence);
            require(status == TruceStatus.AVAILABLE ? expiryDateRaw != null && unavailableReason == null
                    : expiryDateRaw == null && "native_has_truce_false".equals(unavailableReason), "typed truce absence required");
        }
    }
    public record Receipt(Action action, Bound bound, List<ResourceObservation> resources, Claims claims,
                           Titles titles, Truce truce, List<String> issues) {
        public Receipt {
            require(action != null && resources != null && claims != null && titles != null && truce != null && issues != null,
                    "complete observation receipt required");
            resources = List.copyOf(resources); issues = List.copyOf(issues);
            require(bound != null && bound.warAbsent() || resources.isEmpty(), "resources require observed war absence");
            if (bound != null && bound.warAbsent()) {
                require(resources.size() == Resource.values().length, "complete three-resource observation required");
                for (int index = 0; index < Resource.values().length; index++) {
                    require(resources.get(index).resource() == Resource.values()[index]
                            && resources.get(index).sameDate() == (bound.before().dateRaw() == bound.post().dateRaw()),
                            "bound resource observation required");
                }
                if (claims instanceof NativeClaims nativeClaims && nativeClaims.rows() != null) {
                    require(nativeClaims.rows().stream().map(ClaimRow::titleId).toList().equals(bound.renderedTitleIds()),
                            "claim rows must retain frozen ordered targets");
                }
                if (titles instanceof NativeTitles nativeTitles) {
                    List<Integer> ids = nativeTitles.rows().stream().map(TitleRow::titleId).toList();
                    require(nativeTitles.totalFrozenTargets() == bound.targetTitleCount() && new HashSet<>(ids).size() == ids.size()
                            && bound.renderedTitleIds().containsAll(ids), "title rows must retain frozen targets");
                }
                if (truce instanceof NativeTruce nativeTruce) {
                    require(nativeTruce.ownerCharacterId() == bound.post().actorCharacterId()
                            && nativeTruce.towardCharacterId() == bound.opponentCharacterId()
                            && (nativeTruce.expiryDateRaw() == null || nativeTruce.expiryDateRaw() > bound.post().dateRaw()),
                            "truce observation crossed action identity");
                }
            } else {
                require(claims instanceof ClaimsNotObserved && titles instanceof TitlesNotObserved && truce instanceof TruceNotObserved,
                        "postwar materials require observed war absence");
            }
        }
    }
    private static void uint64Positive(BigInteger value) {
        require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0,
                "positive uint64 required");
    }
}

