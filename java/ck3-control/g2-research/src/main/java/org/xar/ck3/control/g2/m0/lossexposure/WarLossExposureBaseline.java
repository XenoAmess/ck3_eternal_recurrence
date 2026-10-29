package org.xar.ck3.control.g2.m0.lossexposure;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Current holders of declared targets. This is not a resolved settlement or a loss forecast. */
public final class WarLossExposureBaseline {
    public static final String SCHEMA = "xar.ck3.war-loss-exposure-baseline.v1";
    public static final String BACKEND = "ck3-1.20.0.4-native-war-loss-exposure-baseline-v1";
    public static final String GAME_VERSION = "1.20.0.4";
    public static final String EXECUTABLE_SHA256 =
            "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public static final String SETTLEMENT_REASON = "resolved_title_and_vassal_effects_not_observed";
    private static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");

    private WarLossExposureBaseline() { }

    public enum Side { ATTACKER, DEFENDER }

    public enum UnavailableReason {
        NOT_READ, UNSUPPORTED_BUILD, MAIN_THREAD_UNAVAILABLE, FRAME_UNAVAILABLE,
        REVISION_MISMATCH, PAUSED_PLAYER_SCOPE_UNAVAILABLE, WAR_NOT_FOUND,
        PLAYER_NOT_PARTICIPANT, PARTICIPANT_SIDES_CONFLICT, WAR_SOURCE_UNAVAILABLE,
        TARGET_TITLE_LIST_INVALID, TARGET_HOLDER_UNAVAILABLE, SOURCE_CHANGED, READER_EXCEPTION
    }

    /** Native producer revision; the application observation revision must be joined separately. */
    public record SourceFrame(BigInteger snapshotRevision, int dateRaw, int actorCharacterId) {
        public SourceFrame {
            Objects.requireNonNull(snapshotRevision, "snapshot revision");
            require(snapshotRevision.signum() > 0 && snapshotRevision.compareTo(UINT64_MAX) <= 0,
                    "positive native uint64 revision required");
            fullId(actorCharacterId);
        }
    }

    public record Target(int titleId, int titleTierRaw, String titleTierKey,
                         Optional<Integer> holderCharacterId, boolean holderIsPlayer,
                         boolean holderInPlayerRealm, Optional<Integer> holderImmediateLiegeCharacterId,
                         Optional<Integer> holderTopLiegeCharacterId) {
        public Target {
            require(titleId >= 0, "native target title ID must be nonnegative");
            require(titleTierRaw >= 1 && titleTierRaw <= 6, "supported native title tier required");
            require(tierKey(titleTierRaw).equals(titleTierKey), "title tier key differs from raw tier");
            Objects.requireNonNull(holderCharacterId, "holder presence");
            Objects.requireNonNull(holderImmediateLiegeCharacterId, "immediate liege presence");
            Objects.requireNonNull(holderTopLiegeCharacterId, "top liege presence");
            holderCharacterId.ifPresent(WarLossExposureBaseline::fullId);
            holderImmediateLiegeCharacterId.ifPresent(WarLossExposureBaseline::fullId);
            holderTopLiegeCharacterId.ifPresent(WarLossExposureBaseline::fullId);
            if (holderCharacterId.isEmpty()) {
                require(!holderIsPlayer && !holderInPlayerRealm && holderImmediateLiegeCharacterId.isEmpty()
                        && holderTopLiegeCharacterId.isEmpty(), "unheld title cannot have holder membership or lieges");
            } else {
                require(holderTopLiegeCharacterId.isPresent(), "held title requires observed top liege");
                require(!holderIsPlayer || holderInPlayerRealm, "player holder must belong to player realm");
                require(holderImmediateLiegeCharacterId.isEmpty()
                        || !holderImmediateLiegeCharacterId.equals(holderCharacterId), "holder cannot be own immediate liege");
                if (holderImmediateLiegeCharacterId.isEmpty()) {
                    require(holderTopLiegeCharacterId.equals(holderCharacterId),
                            "independent holder must be own top liege");
                }
            }
        }
    }

    public sealed interface Observation permits Available, Unavailable { }

    public record Available(SourceFrame sourceFrame, int warId, Side playerSide,
                            boolean playerIsPrimaryWarLeader, List<Integer> targetedTitleIds,
                            List<Target> targets) implements Observation {
        public Available {
            Objects.requireNonNull(sourceFrame, "source frame");
            Objects.requireNonNull(playerSide, "player side");
            fullId(warId);
            targetedTitleIds = List.copyOf(targetedTitleIds);
            targets = List.copyOf(targets);
            require(targetedTitleIds.size() <= 4096 && targetedTitleIds.size() == targets.size(),
                    "bounded complete ordered target material required");
            require(new HashSet<>(targetedTitleIds).size() == targetedTitleIds.size(), "duplicate target ID");
            for (int i = 0; i < targets.size(); i++) {
                Target target = targets.get(i);
                require(targetedTitleIds.get(i) >= 0 && targetedTitleIds.get(i) == target.titleId(),
                        "target row differs from ordered native target IDs");
                require(target.holderIsPlayer() == target.holderCharacterId()
                        .map(id -> id == sourceFrame.actorCharacterId()).orElse(false),
                        "holder_is_player differs from observed actor identity");
            }
        }
    }

    /** Verified request/frame identity may survive; material is wholly unavailable. */
    public record Unavailable(UnavailableReason reason, Optional<SourceFrame> sourceFrame,
                              Optional<Integer> warId) implements Observation {
        public Unavailable {
            Objects.requireNonNull(reason, "unavailable reason");
            Objects.requireNonNull(sourceFrame, "frame presence");
            Objects.requireNonNull(warId, "war ID presence");
            warId.ifPresent(WarLossExposureBaseline::fullId);
        }
    }

    private static void fullId(int id) { require(id != -1, "native invalid full ID sentinel"); }

    private static String tierKey(int raw) {
        return switch (raw) {
            case 1 -> "barony";
            case 2 -> "county";
            case 3 -> "duchy";
            case 4 -> "kingdom";
            case 5 -> "empire";
            case 6 -> "hegemony";
            default -> throw new IllegalArgumentException("unsupported native title tier");
        };
    }
}
