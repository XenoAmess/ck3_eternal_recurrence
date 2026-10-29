package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Complete original occupation/siege normalizer. Shared application boundary for live and archived reads. */
public final class ArmyWarOccupationCodec {
    private ArmyWarOccupationCodec() { }
    public enum Territory { ATTACKER, DEFENDER }
    public enum Occupier { ATTACKER, DEFENDER, OUTSIDE_WAR, NONE, UNAVAILABLE }
    public record SideCount(Territory side, int eligible, int occupied, int nativeCandidates, boolean complete) { }
    public record Fixed(long raw, int scale) { }
    public record Assault(int breach, boolean inProgress, boolean canStart, boolean canStop, Fixed dailyProgress, int dailyCasualties) { }
    /** Zero is a valid observed SiegeID. Empty means an observed absence only when Holding.siegeObservable is true. */
    public record Siege(int id, Field<PublicUnitId> besiegingArmy, boolean playerBesieging,
            Fixed progress, Fixed current, Fixed total, Optional<Assault> assault, Obj normalized) {
        public Siege { Objects.requireNonNull(besiegingArmy); Objects.requireNonNull(assault); Objects.requireNonNull(normalized); }
        public boolean assaultObservable() { return assault.isPresent(); }
    }
    public record Holding(int title, int province, int holder, Territory territory, boolean occupationObservable,
            Field<Boolean> occupied, Field<Integer> occupier, Occupier occupierSide, Field<Boolean> opposingOccupation,
            boolean siegeObservable, Optional<Siege> siege, Obj normalized) {
        public Holding { Objects.requireNonNull(occupied); Objects.requireNonNull(occupier); Objects.requireNonNull(opposingOccupation); Objects.requireNonNull(siege); Objects.requireNonNull(normalized); }
    }
    public record Occupation(UInt64 nativeRevision, long dateRaw, int requestedWar, boolean available,
            boolean collectionComplete, Field<String> unavailableReason, List<SideCount> sideCounts,
            List<Holding> holdings, Obj normalized) {
        public Occupation { sideCounts = List.copyOf(sideCounts); holdings = List.copyOf(holdings); Objects.requireNonNull(normalized); }
    }
    /** Domain decoder expects the caller's same-frame original receipt guard before this method. */
    public static Occupation decode(byte[] originalResult, Context source, int warId, Side playerSide) {
        ObjectNode n = parse(originalResult);
        equal(get(n, "step"), "query-war-occupation-targets-v1-" + warId); yes(get(n, "accepted"));
        positive(get(n, "query_sequence"));
        Occupation value = normalize(get(n, "war_occupation_targets_v1"), source, warId, playerSide);
        require(text(get(n, "status")).equals(value.available() ? "available" : "unavailable"), "occupation outer status differs");
        if (n.has("snapshot_revision")) equal(n.get("snapshot_revision"), source.nativeRevision());
        return value;
    }
    public static Occupation normalize(JsonNode raw, Context source, int warId, Side playerSide) {
        Objects.requireNonNull(source); Objects.requireNonNull(playerSide); require(warId >= 0, "original occupation requires nonnegative full WarID");
        ObjectNode n = object(raw).deepCopy(); equal(get(n, "schema"), "xar.ck3.war-occupation-targets.v1");
        require(i32(get(n, "schema_version")) == 1, "occupation schema version");
        boolean available = bool(get(n, "available")), complete = bool(get(n, "collection_complete"));
        equal(get(n, "status"), available ? "available" : "unavailable");
        equal(get(n, "snapshot_revision"), source.nativeRevision()); equal(get(n, "date_raw"), source.dateRaw());
        Field<String> reason = nullable(n, "unavailable_reason", ArmyJson::nonempty);
        if (available) {
            require(complete && reason instanceof NullValue<?>, "complete occupation must retain null failure");
            require(nonnegative(get(n, "war_id")) == warId, "occupation selected war differs");
            equal(get(n, "actor_character_id"), source.playerId());
            nonnegative(get(n, "primary_attacker_character_id")); nonnegative(get(n, "primary_defender_character_id"));
            require(territory(get(n, "player_side")).name().equals(playerSide.name()), "occupation participant side differs");
        } else require(!complete && reason instanceof Present<?>, "unavailable occupation requires explicit failure");
        text(get(n, "game_version")); String digest = text(get(n, "executable_sha256")); // Native exact-build adapter supplies support, not this shape.
        List<SideCount> counts = array(get(n, "side_counts"), row -> {
            ObjectNode r = object(row); Territory side = territory(get(r, "territory_side"));
            int eligible = nonnegative(get(r, "eligible")), occupied = nonnegative(get(r, "occupied")), candidates = nonnegative(get(r, "native_candidate_count"));
            boolean sideComplete = bool(get(r, "collection_complete"));
            require(occupied <= eligible && (!available || sideComplete), "occupation side counter inconsistent");
            return new SideCount(side, eligible, occupied, candidates, sideComplete);
        });
        if (available) require(counts.size() == 2 && counts.stream().map(SideCount::side).collect(java.util.stream.Collectors.toSet()).equals(Set.of(Territory.ATTACKER, Territory.DEFENDER)), "occupation requires both complete side counts");
        JsonNode rows = get(n, "rows"); require(rows.isArray(), "occupation rows array required");
        List<Holding> holdings = new ArrayList<>();
        for (JsonNode row : rows) holdings.add(holding(object(row), available));
        n.put("executable_sha256", digest.toLowerCase(Locale.ROOT));
        return new Occupation(positive(n.get("snapshot_revision")), i64(n.get("date_raw")), warId, available, complete, reason, counts, holdings, immutable(n));
    }
    public static RawJson encode(Occupation value) { return new RawJson(OpportunityJson.encode(value.normalized())); }
    public static ObjectNode normalizedNode(Occupation value) { return parse(encode(value).bytes()); }
    private static Holding holding(ObjectNode n, boolean complete) {
        int title = nonnegative(get(n, "holding_title_id")), province = nonnegative(get(n, "province_id")), holder = nonnegative(get(n, "legal_holder_character_id"));
        Territory territory = territory(get(n, "territory_side")); boolean observable = bool(get(n, "occupation_observable"));
        Occupier side = switch (text(get(n, "occupier_side"))) {
            case "attacker" -> Occupier.ATTACKER; case "defender" -> Occupier.DEFENDER; case "outside_war" -> Occupier.OUTSIDE_WAR;
            case "none" -> Occupier.NONE; case "unavailable" -> Occupier.UNAVAILABLE; default -> throw new IllegalArgumentException("occupation side unknown");
        };
        Field<Boolean> occupied = nullable(n, "is_occupied", ArmyJson::bool), opposing = nullable(n, "counted_occupied_by_opposing_side", ArmyJson::bool);
        Field<Integer> occupier = nullable(n, "occupying_character_id", ArmyJson::nonnegative);
        if (observable) {
            require(occupied instanceof Present<Boolean> && opposing instanceof Present<Boolean>, "observable occupation booleans required");
            if (((Present<Boolean>) occupied).value()) require(occupier instanceof Present<?> && Set.of(Occupier.ATTACKER, Occupier.DEFENDER, Occupier.OUTSIDE_WAR).contains(side), "occupied target lacks occupier");
            else require(occupier instanceof NullValue<?> && side == Occupier.NONE, "unoccupied target must retain absence");
        } else require(occupied instanceof NullValue<?> && occupier instanceof NullValue<?> && opposing instanceof NullValue<?> && side == Occupier.UNAVAILABLE, "unknown occupation cannot substitute zero");
        require(!complete || observable, "complete occupation has an unobservable holding");
        for (String name : List.of("county_title_id", "fort_level", "garrison_size", "besieging_strength")) putOptionalCount(n, name);
        boolean siegeObservable = n.has("siege_observable") && bool(n.get("siege_observable")); n.put("siege_observable", siegeObservable);
        if (n.has("current_besieging_army_selection")) n.set("current_besieging_army_selection", selection(n.get("current_besieging_army_selection")));
        JsonNode rawSiege = n.get("active_siege");
        require(siegeObservable || rawSiege == null || rawSiege.isNull(), "unobservable siege cannot publish an active one");
        Optional<Siege> siege = rawSiege == null || rawSiege.isNull() ? Optional.empty() : Optional.of(siege(rawSiege));
        if (siege.isPresent()) n.set("active_siege", OpportunityJson.toNode(siege.orElseThrow().normalized())); else n.putNull("active_siege");
        return new Holding(title, province, holder, territory, observable, occupied, occupier, side, opposing, siegeObservable, siege, immutable(n));
    }
    /** Same full siege normalization as war_contract._normalize_active_siege; ordered occurrences remain ordered. */
    public static Siege siege(JsonNode raw) {
        ObjectNode value = object(raw), n = empty();
        int id = nonnegative(get(value, "siege_id")); n.put("siege_id", id);
        copyNullable(value, n, "besieging_army_id", ArmyJson::unit); Field<PublicUnitId> army = nullable(n, "besieging_army_id", ArmyJson::unit);
        boolean player = bool(get(value, "player_army_besieging")); n.put("player_army_besieging", player);
        Fixed progress = fixed(get(value, "progress_fraction"), true), current = fixed(get(value, "current_work"), false), total = fixed(get(value, "total_work"), false);
        putFixed(n, "progress_fraction", progress); putFixed(n, "current_work", current); putFixed(n, "total_work", total);
        putFixed(n, "remaining_work", new Fixed(Math.max(total.raw() - current.raw(), 0), 100000));
        copyNullable(value, n, "days_left", ArmyJson::nonnegative);
        for (String name : List.of("ordinary_daily_progress", "current_phase_length", "prepared_phase_length")) nullableFixed(value, n, name);
        copyNullable(value, n, "phase_counter", ArmyJson::nonnegative); copyNullable(value, n, "can_advance", ArmyJson::bool);
        JsonNode phase = value.get("phase_event_state");
        if (phase == null || phase.isNull()) n.putNull("phase_event_state");
        else {
            ObjectNode from = object(phase), to = n.putObject("phase_event_state");
            for (String name : List.of("breach_level", "starvation_level", "disease_level", "desertion_count", "stalemate_count")) copyNullable(from, to, name, ArmyJson::nonnegative);
        }
        copyNullable(value, n, "prepared_selected_phase_event_enum", node -> { int event = nonnegative(node); require(event <= 5, "siege event enum outside 0..5"); return event; });
        boolean observable = value.has("assault_observable") && bool(value.get("assault_observable")); n.put("assault_observable", observable);
        Optional<Assault> assault;
        List<String> assaultFields = List.of("breach_level", "assault_in_progress", "can_start_assault", "can_stop_assault", "assault_daily_progress", "assault_daily_casualties");
        if (!observable) {
            for (String name : assaultFields) { require(!value.has(name) || value.get(name).isNull(), "unknown assault cannot publish values"); n.putNull(name); }
            n.putNull("walls_breached"); assault = Optional.empty();
        } else {
            int breach = nonnegative(get(value, "breach_level")); require(breach <= 2, "siege breach outside 0..2");
            boolean inProgress = bool(get(value, "assault_in_progress")), start = bool(get(value, "can_start_assault")), stop = bool(get(value, "can_stop_assault"));
            Fixed daily = fixed(get(value, "assault_daily_progress"), false); int casualties = nonnegative(get(value, "assault_daily_casualties"));
            n.put("breach_level", breach).put("walls_breached", breach > 0).put("assault_in_progress", inProgress).put("can_start_assault", start).put("can_stop_assault", stop).put("assault_daily_casualties", casualties);
            putFixed(n, "assault_daily_progress", daily); assault = Optional.of(new Assault(breach, inProgress, start, stop, daily, casualties));
        }
        if (value.has("eligible_regiment_siege_work")) nullableFixed(value, n, "eligible_regiment_siege_work");
        if (value.has("highest_eligible_siege_tier")) copyNullable(value, n, "highest_eligible_siege_tier", ArmyJson::nonnegative);
        if (value.has("province_unit_occurrences")) n.set("province_unit_occurrences", occurrences(value.get("province_unit_occurrences")));
        return new Siege(id, army, player, progress, current, total, assault, immutable(n));
    }
    private static JsonNode selection(JsonNode raw) {
        if (raw == null || raw.isNull()) return com.fasterxml.jackson.databind.node.NullNode.instance;
        ObjectNode from = object(raw), to = empty();
        copyNullable(from, to, "native_carmy_id", ArmyJson::nonnegative); copyNullable(from, to, "public_unit_id", ArmyJson::unit); copyNullable(from, to, "controllable", ArmyJson::bool); return to;
    }
    private static JsonNode occurrences(JsonNode raw) {
        if (raw == null || raw.isNull()) return com.fasterxml.jackson.databind.node.NullNode.instance;
        require(raw.isArray(), "native Province occurrence array required"); var out = empty().putArray("items"); int index = 0;
        for (JsonNode item : raw) {
            ObjectNode from = object(item), to = empty();
            require(nonnegative(get(from, "occurrence_index")) == index, "native occurrence order differs"); to.put("occurrence_index", index++);
            copyNullable(from, to, "public_unit_id", ArmyJson::unit); copyNullable(from, to, "native_carmy_id", ArmyJson::nonnegative); copyNullable(from, to, "eligible", ArmyJson::bool);
            JsonNode regiments = from.get("qualified_regiment_ids");
            if (regiments == null || regiments.isNull()) to.putNull("qualified_regiment_ids");
            else { List<Integer> ids = array(regiments, ArmyJson::nonnegative); var values = to.putArray("qualified_regiment_ids"); ids.forEach(values::add); }
            JsonNode eligible = to.get("eligible");
            if (eligible.isBoolean() && eligible.booleanValue()) require(!to.get("public_unit_id").isNull() && !to.get("native_carmy_id").isNull(), "eligible occurrence lacks resolved IDs");
            else if (eligible.isBoolean()) require(to.get("qualified_regiment_ids").isArray() && to.get("qualified_regiment_ids").isEmpty(), "excluded occurrence consumed regiments");
            else require(to.get("qualified_regiment_ids").isNull(), "unresolved occurrence cannot publish regiments");
            out.add(to);
        }
        return out;
    }
    private static Fixed fixed(JsonNode raw, boolean fraction) {
        ObjectNode n = closed(raw, "raw", "scale"); long value = range(n.get("raw"), BigInteger.ZERO, BigInteger.valueOf(Long.MAX_VALUE)).longValueExact();
        require(integer(n.get("scale")).equals(BigInteger.valueOf(100000)) && (!fraction || value <= 100000), "native siege fixed point differs"); return new Fixed(value, 100000);
    }
    private static void putFixed(ObjectNode n, String name, Fixed value) { n.putObject(name).put("raw", value.raw()).put("scale", value.scale()); }
    private static void nullableFixed(ObjectNode from, ObjectNode to, String name) { JsonNode value = from.get(name); if (value == null || value.isNull()) to.putNull(name); else putFixed(to, name, fixed(value, false)); }
    private static <T> void copyNullable(ObjectNode from, ObjectNode to, String name, java.util.function.Function<JsonNode,T> decode) {
        JsonNode value = from.get(name); if (value == null || value.isNull()) to.putNull(name); else { decode.apply(value); to.set(name, value.deepCopy()); }
    }
    private static void putOptionalCount(ObjectNode n, String name) { JsonNode value = n.get(name); if (value == null || value.isNull()) n.putNull(name); else nonnegative(value); }
    private static Territory territory(JsonNode raw) { return switch (text(raw)) { case "attacker" -> Territory.ATTACKER; case "defender" -> Territory.DEFENDER; default -> throw new IllegalArgumentException("native territory side unknown"); }; }
    private static Obj immutable(ObjectNode n) { return DriverJson.object(bytes(n), DriverJson.MAX_NATIVE_BYTES); }
}

