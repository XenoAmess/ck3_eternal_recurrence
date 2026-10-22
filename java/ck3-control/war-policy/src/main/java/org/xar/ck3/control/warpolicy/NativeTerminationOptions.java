package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Optional;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete exact-.4 normalized query/cache contract; no material preview is inferred. */
public record NativeTerminationOptions(int warId, WarSide side, boolean primary,
        int relativeScore, Truth activeCasusBelli, Optional<CasusBelli> casusBelli,
        QueryBinding binding) {
    public NativeTerminationOptions {
        require(warId > 0, "positive query WarID required");
        Objects.requireNonNull(side, "query side"); Objects.requireNonNull(binding, "query binding");
        Objects.requireNonNull(activeCasusBelli, "active CB availability");
        Objects.requireNonNull(casusBelli, "explicit CB observation");
        require(activeCasusBelli == Truth.TRUE || casusBelli.isEmpty(), "CB identity without observed active CB");
    }
    public enum Truth { TRUE, FALSE, UNKNOWN }

    public record CasusBelli(int databaseIndex, String canonicalKey) {
        public CasusBelli {
            require(databaseIndex >= 0, "nonnegative CB database index");
            StrictJson.text(canonicalKey);
        }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("database_index", databaseIndex);
            row.put("canonical_key", canonicalKey); return row;
        }
    }

    public record QueryBinding(BigInteger sequence, String snapshotId, BigInteger revision,
            BigInteger nativeRevision, String episodeRunId, BigInteger connectionGeneration) {
        public QueryBinding {
            for (BigInteger value : new BigInteger[] {sequence, revision, nativeRevision, connectionGeneration}) {
                require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0,
                    "query binding integer outside positive uint64");
            }
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            // A stale binding is valid input; the projector returns unknown on mismatch.
        }
        public boolean matches(WarObservationFrame frame) {
            return snapshotId.equals(frame.snapshotId()) && revision.equals(frame.revision())
                && nativeRevision.equals(frame.nativeRevision()) && episodeRunId.equals(frame.episodeRunId())
                && connectionGeneration.equals(frame.connectionGeneration());
        }
    }

    private static final Set<String> FIELDS = Set.of("war_id", "player_side",
        "player_is_primary_war_leader", "player_relative_war_score", "war_duration_days",
        "absolute_war_scores_observable", "attacker_war_score", "defender_war_score",
        "war_score_breakdown", "active_casus_belli_present", "active_casus_belli_identity",
        "cb_allows_white_peace", "options", "query_sequence", "queried_snapshot_id",
        "queried_revision", "queried_native_revision", "episode_run_id", "queried_connection_generation");
    private static final Set<String> OPTION_FIELDS = Set.of("outcome", "hostage_variant",
        "context_constructed", "native_validator_passed", "available", "terms_observable", "terms",
        "ai_acceptance_observable", "ai_acceptance", "auto_accept_observable", "auto_accept", "recipient_response");

    public static NativeTerminationOptions fromCache(JsonNode value, int expectedWarId) {
        ObjectNode raw = WarJson.record(value, "native termination cache row");
        Set<String> fields = new HashSet<>(FIELDS);
        if (raw.has("source")) { fields.add("source"); }
        ObjectNode row = StrictJson.object(raw, fields);
        if (row.has("source")) { require(WarJson.textEquals(row.get("source"), "native"), "native query source required"); }
        int warId = WarJson.positive32(row.get("war_id"));
        require(warId == expectedWarId, "query WarID mismatch");
        QueryBinding binding = new QueryBinding(WarJson.positive64(row.get("query_sequence")),
            StrictJson.text(row.get("queried_snapshot_id")), WarJson.positive64(row.get("queried_revision")),
            WarJson.positive64(row.get("queried_native_revision")), StrictJson.text(row.get("episode_run_id")),
            WarJson.positive64(row.get("queried_connection_generation")));
        WarSide side = WarSide.fromJson(row.get("player_side"));
        boolean primary = WarJson.bool(row.get("player_is_primary_war_leader"));
        int score = WarJson.signed32(row.get("player_relative_war_score"));
        nullableNonnegative32(row.get("war_duration_days"));
        Truth active = nullableBool(row.get("active_casus_belli_present"));
        Truth whiteAllowed = nullableBool(row.get("cb_allows_white_peace"));
        require(whiteAllowed == Truth.UNKNOWN || active == Truth.TRUE,
            "white peace permission requires an observed active CB");
        Optional<CasusBelli> cb = Optional.empty();
        if (!row.get("active_casus_belli_identity").isNull()) {
            require(active == Truth.TRUE, "CB identity requires active CB");
            ObjectNode identity = StrictJson.object(row.get("active_casus_belli_identity"), Set.of("database_index", "canonical_key"));
            cb = Optional.of(new CasusBelli(WarJson.nonnegative32(identity.get("database_index")),
                StrictJson.text(identity.get("canonical_key"))));
        }
        boolean absolute = WarJson.bool(row.get("absolute_war_scores_observable"));
        Integer attacker = nullableSigned32(row.get("attacker_war_score"));
        Integer defender = nullableSigned32(row.get("defender_war_score"));
        if (absolute) {
            require(attacker != null && defender != null, "observable absolute scores require both values");
            // Compare in long: -Integer.MIN_VALUE must not overflow.
            require((long) defender == -(long) attacker, "absolute score pair differs");
            require(score == (side == WarSide.ATTACKER ? attacker : defender), "relative score differs");
        } else {
            require(attacker == null && defender == null, "unobservable absolute scores require nulls");
        }
        JsonNode breakdown = row.get("war_score_breakdown");
        if (!breakdown.isNull()) {
            ObjectNode parts = StrictJson.object(breakdown, Set.of("imprisonment", "battles", "occupation", "ticking"));
            parts.elements().forEachRemaining(WarJson::signed32);
        }
        ObjectNode options = StrictJson.object(row.get("options"), Set.of("surrender", "white_peace", "victory"));
        boolean surrender = option(options.get("surrender"), side == WarSide.ATTACKER ? "attacker_defeat" : "attacker_victory");
        boolean whitePeace = option(options.get("white_peace"), "white_peace");
        boolean victory = option(options.get("victory"), side == WarSide.ATTACKER ? "attacker_victory" : "attacker_defeat");
        require(primary || !(surrender || whitePeace || victory), "nonprimary participant cannot construct exit contexts");
        require(whiteAllowed == Truth.TRUE || !whitePeace, "forbidden white peace context");
        return new NativeTerminationOptions(warId, side, primary, score, active, cb, binding);
    }

    private static boolean option(JsonNode value, String outcome) {
        ObjectNode row = StrictJson.object(value, OPTION_FIELDS);
        require(WarJson.textEquals(row.get("outcome"), outcome), "outcome differs from player side");
        require(WarJson.textEquals(row.get("hostage_variant"), "none"), "only no-hostage option supported");
        boolean constructed = WarJson.bool(row.get("context_constructed"));
        Truth validator = nullableBool(row.get("native_validator_passed"));
        require(constructed || validator == Truth.UNKNOWN, "validator without constructed context");
        require(WarJson.bool(row.get("available")) == (constructed && validator == Truth.TRUE), "available/context/validator mismatch");
        require(!WarJson.bool(row.get("terms_observable")), "material terms must remain unobservable");
        ObjectNode terms = StrictJson.object(row.get("terms"), Set.of("status", "reason"));
        require(WarJson.textEquals(terms.get("status"), "unavailable")
            && WarJson.textEquals(terms.get("reason"), "cb_specific_terms_not_observable"), "material terms differ");
        boolean ai = WarJson.bool(row.get("ai_acceptance_observable"));
        if (ai) {
            ObjectNode fixed = StrictJson.object(row.get("ai_acceptance"), Set.of("raw", "scale"));
            StrictJson.integer(fixed.get("raw"), BigInteger.valueOf(Long.MIN_VALUE), BigInteger.valueOf(Long.MAX_VALUE));
            StrictJson.integer(fixed.get("scale"), 100_000, 100_000);
        } else { require(row.get("ai_acceptance").isNull(), "unobservable AI acceptance requires null"); }
        boolean automatic = WarJson.bool(row.get("auto_accept_observable"));
        if (automatic) { WarJson.bool(row.get("auto_accept")); }
        else { require(row.get("auto_accept").isNull(), "unobservable auto-accept requires null"); }
        require(constructed || !(ai || automatic), "acceptance without constructed context");
        recipient(row.get("recipient_response"), constructed, validator);
        return constructed;
    }

    private static void recipient(JsonNode value, boolean constructed, Truth validator) {
        ObjectNode row = StrictJson.object(value, Set.of("status", "decision_status_raw", "would_accept_now"));
        if (WarJson.textEquals(row.get("status"), "unavailable")) {
            require(row.get("decision_status_raw").isNull() && row.get("would_accept_now").isNull(),
                "unavailable recipient response requires nulls");
            return;
        }
        require(WarJson.textEquals(row.get("status"), "available") && constructed && validator == Truth.TRUE,
            "available recipient response requires validated context");
        int status = (int) StrictJson.integer(row.get("decision_status_raw"), 0, 2);
        require(WarJson.bool(row.get("would_accept_now")) == (status != 2), "recipient answer/status mismatch");
    }

    private static Truth nullableBool(JsonNode value) {
        if (value.isNull()) { return Truth.UNKNOWN; }
        return WarJson.bool(value) ? Truth.TRUE : Truth.FALSE;
    }
    private static Integer nullableSigned32(JsonNode value) {
        return value.isNull() ? null : WarJson.signed32(value);
    }
    private static void nullableNonnegative32(JsonNode value) {
        if (!value.isNull()) { WarJson.nonnegative32(value); }
    }
}
