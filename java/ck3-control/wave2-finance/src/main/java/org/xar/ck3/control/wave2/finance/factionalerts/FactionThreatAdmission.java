package org.xar.ck3.control.wave2.finance.factionalerts;

import java.util.Objects;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel.*;

/** Current native danger/member admission for the ordinary FACTION_GIFT consumer.
 * The owning public read receipt and spending admission remain separate authorities.
 */
public final class FactionThreatAdmission {
    private FactionThreatAdmission() { }

    public record Request(ExpectedFrame expected, int actorCharacterId,
                          int factionId, int recipientCharacterId) {
        public Request {
            Objects.requireNonNull(expected, "expected native query frame");
            StrictJson.require(expected.connectedBuild().orElse(null) == Build.CK3_12004,
                    "exact current CK3 1.20.0.4 source required");
            NativeCharacterId.of(actorCharacterId);
            NativeCharacterId.of(recipientCharacterId);
            StrictJson.require(factionId > 0, "positive int32 faction identity required");
            StrictJson.require(actorCharacterId != recipientCharacterId, "gift cannot target its actor");
        }
    }

    public enum MissingReason {
        QUERY_UNAVAILABLE, TARGETING_ROWS_UNAVAILABLE, STOCK_DANGER_UNAVAILABLE,
        SAME_FRAME_UNAVAILABLE, SELECTED_FACTION_ABSENT, EXISTING_FACTION_WAR,
        NOT_CURRENTLY_DANGEROUS, RECIPIENT_NOT_LEADER_OR_MEMBER
    }
    public enum StrengthCoverage { FINAL_NATIVE_POWER_ONLY_COMPONENT_CACHES_NOT_OBSERVED }
    public enum ClockCoverage { MONTHS_TO_MAX_DISCONTENT_ONLY_EXACT_DEMAND_CLOCK_UNPUBLISHED }
    public sealed interface Result permits Admitted, Missing { }
    public record Missing(MissingReason reason) implements Result {
        public Missing { Objects.requireNonNull(reason); }
    }

    /** Only the validated original producer path can construct this current observation.
     * Public danger/member observations do not grant private gift-preview or submission eligibility.
     */
    public static final class Admitted implements Result {
        private final Request request;
        private final TargetingFaction faction;
        private final FactionAlertsBoundary.Projection source;
        private Admitted(Request request, TargetingFaction faction, FactionAlertsBoundary.Projection source) {
            this.request = request; this.faction = faction; this.source = source;
        }
        public Request request() { return request; }
        public TargetingFaction faction() { return faction; }
        public Frame nativeFrame() { return source.frame(); }
        public String originalDriverResultSha256() { return source.originalSha256(); }
        public byte[] normalizedAlertJson() { return source.normalizedAlertJson(); }
        public StrengthCoverage strengthCoverage() {
            return StrengthCoverage.FINAL_NATIVE_POWER_ONLY_COMPONENT_CACHES_NOT_OBSERVED;
        }
        public ClockCoverage clockCoverage() {
            return ClockCoverage.MONTHS_TO_MAX_DISCONTENT_ONLY_EXACT_DEMAND_CLOCK_UNPUBLISHED;
        }
    }

    /**
     * Validates the existing original packet and same-frame active wars once.
     * Malformed packets/frame or source drift throw; valid missing facts remain typed Missing.
     * Native final power and stock dangerous are consumed without reconstructing troop strength.
     */
    public static Result fromExistingDriverResult(byte[] originalDriverResult, Request request,
                                                 byte[] sameFrameActiveWars) {
        Objects.requireNonNull(request, "faction admission request");
        var projection = FactionAlertsBoundary.normalizeCurrentNativeResult(
                originalDriverResult, request.expected(), sameFrameActiveWars).projection();
        if (!(projection.frame() instanceof Available available)) return missing(MissingReason.QUERY_UNAVAILABLE);
        StrictJson.require(available.playerCharacterId() == request.actorCharacterId(), "native faction actor drift");
        if (!available.readiness().targetingRowsReady()) return missing(MissingReason.TARGETING_ROWS_UNAVAILABLE);
        if (!available.readiness().stockDangerousReady()) return missing(MissingReason.STOCK_DANGER_UNAVAILABLE);
        if (!available.readiness().sameFrameReady()) return missing(MissingReason.SAME_FRAME_UNAVAILABLE);
        TargetingFaction selected = null;
        for (TargetingFaction row : available.targetingFactions())
            if (row.factionId() == request.factionId()) selected = row;
        if (selected == null) return missing(MissingReason.SELECTED_FACTION_ABSENT);
        StrictJson.require(selected.targetCharacterId() == request.actorCharacterId(), "selected faction targets another actor");
        if (selected.factionAtWar()) return missing(MissingReason.EXISTING_FACTION_WAR);
        if (!selected.dangerous()) return missing(MissingReason.NOT_CURRENTLY_DANGEROUS);
        boolean recipientPresent = selected.leaderCharacterId()
                .filter(id -> id == request.recipientCharacterId()).isPresent()
                || selected.characterMemberIds().contains(request.recipientCharacterId());
        if (!recipientPresent) return missing(MissingReason.RECIPIENT_NOT_LEADER_OR_MEMBER);
        return new Admitted(request, selected, projection);
    }

    private static Missing missing(MissingReason reason) { return new Missing(reason); }
}
