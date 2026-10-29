package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.holycost.HolyCostJsonAdapter;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Complete original optional defender-set sibling. An observed set is neither a join score nor execution permission. */
public final class HolyWarDefenderJoinCodec {
    public static final String DOMAIN = "player_holy_war_defender_join_inputs";
    private static final BigInteger UINT32 = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    private static final Set<String> FIELDS = Set.of("schema", "read_only", "available", "unavailable_reason", "capture_epoch",
            "native_revision", "public_revision", "date_raw", "played_character_id", "declaration_id", "selected_declaration",
            "primary_attacker_character_id", "primary_defender_character_id", "primary_defender_faith_available",
            "primary_defender_faith_unavailable_reason", "primary_defender_rite_id", "primary_defender_faith_id", "cb_flags_raw",
            "defender_faith_can_join", "native_joiner_set_observed", "joiner_count", "joiners", "raw_scale", "unit", "is_final_join_score");
    private static final Set<String> ROW = Set.of("character_id", "row_faith_available", "row_fervor_available", "unavailable_reason",
            "rite_id", "faith_id", "faith_fervor_raw", "matches_primary_defender_faith");
    private HolyWarDefenderJoinCodec() { }
    public record Faith(boolean available, Optional<String> unavailableReason, Optional<Long> riteId, Optional<Long> faithId) {
        public Faith { Objects.requireNonNull(unavailableReason); Objects.requireNonNull(riteId); Objects.requireNonNull(faithId); }
    }
    public record Joiner(long characterId, Faith faith, boolean fervorAvailable, Optional<Long> fervorRaw,
            Optional<Boolean> matchesPrimaryDefenderFaith) {
        public Joiner { Objects.requireNonNull(faith); Objects.requireNonNull(fervorRaw); Objects.requireNonNull(matchesPrimaryDefenderFaith); }
    }
    public record Observation(HolyCostObservation owner, boolean available, Optional<String> unavailableReason,
            Optional<Long> primaryAttacker, Optional<Long> primaryDefender, Faith primaryDefenderFaith,
            Optional<Long> cbFlags, Optional<Boolean> defenderFaithCanJoin, boolean nativeSetObserved,
            List<Joiner> joiners, OpportunityJson.Obj normalized) {
        public Observation {
            Objects.requireNonNull(owner); Objects.requireNonNull(unavailableReason); Objects.requireNonNull(primaryAttacker);
            Objects.requireNonNull(primaryDefender); Objects.requireNonNull(primaryDefenderFaith); Objects.requireNonNull(cbFlags);
            Objects.requireNonNull(defenderFaithCanJoin); joiners = List.copyOf(joiners); Objects.requireNonNull(normalized);
        }
    }
    public static Observation normalize(JsonNode raw, HolyCostObservation owner, JsonNode actualSnapshot) {
        Objects.requireNonNull(owner); ObjectNode n = StrictJson.object(raw, FIELDS), snapshot = object(actualSnapshot);
        String schema = owner.build() == HolyCostObservation.Build.CK3_12004 ? "ck3_12004_holy_war_defender_join_inputs_v1" : "ck3_12003_holy_war_defender_join_inputs_v1";
        equal(n.get("schema"), schema); yes(n.get("read_only")); equal(n.get("raw_scale"), BigInteger.valueOf(100000)); equal(n.get("unit"), "fervor_points"); no(n.get("is_final_join_score"));
        ObjectNode hello = object(get(object(get(snapshot, "diagnostics")), "hello"));
        equal(get(hello, "expected_ck3_version"), owner.build().gameVersion()); equal(get(hello, "expected_ck3_sha256"), owner.build().executableSha256());
        require(owner.originalExecutableSha256().equals(owner.build().executableSha256()), "join owner must retain the exact original uppercase build source");
        equalPositive(n.get("capture_epoch"), owner.captureEpoch()); equalPositive(n.get("native_revision"), owner.nativeRevision()); equalPositive(n.get("public_revision"), owner.publicRevision());
        equalPositive(get(snapshot, "native_revision"), owner.nativeRevision()); equalPositive(get(snapshot, "revision"), owner.publicRevision());
        require(i32(n.get("date_raw")) == owner.dateRaw() && i32(get(snapshot, "date_raw")) == owner.dateRaw(), "defender join date crossed owner/source");
        require(i32(n.get("played_character_id")) == owner.playedCharacterId()
                && i32(get(object(get(snapshot, "played_character")), "character_id")) == owner.playedCharacterId(), "defender join player crossed owner/source");
        equal(n.get("declaration_id"), owner.declarationId());
        ObjectNode selected = StrictJson.object(n.get("selected_declaration"), Set.of("target_character_id", "casus_belli_index", "casus_belli_key", "configuration_index", "claimant_character_id", "target_title_ids"));
        for (String key : List.of("target_character_id", "casus_belli_index")) StrictJson.integer(selected.get(key), 0, Integer.MAX_VALUE);
        for (String key : List.of("configuration_index", "claimant_character_id")) StrictJson.integer(selected.get(key), -1, Integer.MAX_VALUE);
        require(HolyCostJsonAdapter.ORDINARY_HOLY_WAR_KEYS.contains(text(selected.get("casus_belli_key"))), "join selected CB is not ordinary holy war");
        array(selected.get("target_title_ids"), value -> StrictJson.integer(value, 0, Integer.MAX_VALUE));
        require(selected.equals(HolyCostJsonAdapter.selectedJson(owner.selectedDeclaration())), "defender join selected tuple differs from actual owner");
        boolean available = bool(n.get("available")), observed = bool(n.get("native_joiner_set_observed"));
        require(available == observed, "join availability differs from complete native set observation");
        Optional<String> reason = reason(n.get("unavailable_reason"), available);
        Optional<Long> attacker = u32null(n.get("primary_attacker_character_id")), defender = u32null(n.get("primary_defender_character_id"));
        checkRole(attacker, owner.roles().additionalRoleCharacterId()); checkRole(defender, owner.roles().recipientCharacterId());
        boolean rolesComplete = attacker.isPresent() && defender.isPresent() && Boolean.FALSE.equals(owner.roles().additionalRoleUsesNativeFallback())
                && Boolean.FALSE.equals(owner.roles().recipientUsesNativeFallback());
        require(!observed || rolesComplete, "observed native set requires both actual non-fallback receivers");
        require(!Boolean.TRUE.equals(owner.roles().additionalRoleUsesNativeFallback()) && !Boolean.TRUE.equals(owner.roles().recipientUsesNativeFallback()) || !observed,
                "native role fallback cannot grant an observed set");
        boolean primaryReady = bool(n.get("primary_defender_faith_available"));
        Faith primary = new Faith(primaryReady, reason(n.get("primary_defender_faith_unavailable_reason"), primaryReady),
                u32null(n.get("primary_defender_rite_id")), u32null(n.get("primary_defender_faith_id")));
        require(!primaryReady || primary.riteId().isPresent() && primary.faithId().isPresent(), "available primary faith requires both observed IDs");
        Optional<Long> flags = u32null(n.get("cb_flags_raw")); Optional<Boolean> canJoin = nullable(n.get("defender_faith_can_join"), ArmyJson::bool);
        require(flags.isPresent() ? canJoin.equals(Optional.of((flags.orElseThrow() & (1L << 15)) != 0)) : canJoin.isEmpty(), "CB flag branch differs from actual flag bit15");
        require(!observed || flags.isPresent(), "observed native set requires actual CB flags");
        long count = u32(n.get("joiner_count")); List<JsonNode> rows = array(n.get("joiners"), value -> value);
        require(count == rows.size() && (observed || rows.isEmpty()) && (!canJoin.equals(Optional.of(false)) || rows.isEmpty()), "join ordered rows differ from complete native branch/count");
        List<Joiner> joiners = new ArrayList<>();
        for (JsonNode row : rows) {
            ObjectNode r = StrictJson.object(row, ROW); long id = u32(r.get("character_id"));
            boolean faithReady = bool(r.get("row_faith_available")), fervorReady = bool(r.get("row_fervor_available"));
            Optional<Long> rite = u32null(r.get("rite_id")), faith = u32null(r.get("faith_id"));
            Optional<Long> fervor = nullable(r.get("faith_fervor_raw"), value -> StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE));
            require(!faithReady || rite.isPresent() && faith.isPresent(), "available row faith requires actual IDs");
            require(fervorReady ? faithReady && fervor.isPresent() : fervor.isEmpty(), "fervor availability differs from observed row faith/raw value");
            Optional<String> rowReason = reason(r.get("unavailable_reason"), faithReady && fervorReady);
            Optional<Boolean> matches = nullable(r.get("matches_primary_defender_faith"), ArmyJson::bool);
            require(faithReady && primaryReady ? matches.equals(Optional.of(faith.equals(primary.faithId()))) : matches.isEmpty(), "faith comparison must bind observed FaithIDs");
            joiners.add(new Joiner(id, new Faith(faithReady, rowReason, rite, faith), fervorReady, fervor, matches));
        }
        return new Observation(owner, available, reason, attacker, defender, primary, flags, canJoin, observed, joiners,
                DriverJson.object(bytes(n), DriverJson.MAX_NATIVE_BYTES));
    }
    public static ObjectNode encode(Observation observation) { return object(OpportunityJson.toNode(observation.normalized())).deepCopy(); }
    private static void equalPositive(JsonNode n, BigInteger expected) { require(positive(n).value().equals(expected), "defender join owner revision/epoch differs"); }
    private static void checkRole(Optional<Long> child, Integer owner) {
        require(child.isEmpty() || owner != null && child.orElseThrow() == Integer.toUnsignedLong(owner), "defender join receiver bits differ from actual owning role");
    }
    private static long u32(JsonNode n) { return StrictJson.integer(n, BigInteger.ZERO, UINT32).longValueExact(); }
    private static Optional<Long> u32null(JsonNode n) { return nullable(n, HolyWarDefenderJoinCodec::u32); }
    private static Optional<String> reason(JsonNode n, boolean ready) {
        require(n != null, "required reason slot missing"); if (ready) { require(n.isNull(), "ready reason must be null"); return Optional.empty(); }
        String value = nonempty(n); require(!value.isBlank(), "unavailable stage reason required"); return Optional.of(value);
    }
    private static <T> Optional<T> nullable(JsonNode n, java.util.function.Function<JsonNode,T> decoder) {
        require(n != null, "required nullable slot missing"); return n.isNull() ? Optional.empty() : Optional.of(decoder.apply(n));
    }
}
