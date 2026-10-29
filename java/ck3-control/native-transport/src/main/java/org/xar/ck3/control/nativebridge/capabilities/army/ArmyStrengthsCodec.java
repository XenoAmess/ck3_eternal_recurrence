package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.xar.ck3.control.contracts.NativeCharacterId;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.IdentityHashMap;
import java.util.EnumMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;

/** Exact existing Army producer boundary; malformed rich fields cannot be passed through as validated values. */
public final class ArmyStrengthsCodec {
    private static final Set<String> CORE = ArmyStrengthsReadValue.CORE_FIELDS;
    private static final Set<String> GATHERING = Set.of("gathering_days_left", "gathering_days_status", "gathering_days_ready");
    private static final String SHARED_KEY = "army_manager_inputs_shared_v1";
    private ArmyStrengthsCodec() { }
    public static Snapshot snapshot(Context context, RawJson actual) {
        Objects.requireNonNull(context); ObjectNode root = parse(actual.bytes());
        yes(get(root, "paused")); yes(get(root, "map_ready")); ObjectNode player = object(get(root, "played_character")); yes(get(player, "alive"));
        int actor = NativeCharacterId.fromJson(get(player, "character_id")).value();
        ObjectNode diagnostics = object(get(root, "diagnostics")); BigInteger generation = positive(get(diagnostics, "connection_generation")).value();
        String snapshotId = nonempty(get(root, "snapshot_id")); BigInteger revision = integer(get(root, "revision"));
        BigInteger nativeRevision = integer(get(root, "native_revision")); BigInteger date = integer(get(root, "date_raw"));
        require(revision.signum() >= 0 && nativeRevision.signum() >= 0, "published revisions must be nonnegative exact integers");
        Optional<String> episode = !root.has("episode_run_id") || root.get("episode_run_id").isNull() ? Optional.empty() : Optional.of(nonempty(root.get("episode_run_id")));
        var before = context.before(); var frame = before.frame();
        require(frame.snapshotId().equals(snapshotId) && frame.revision().equals(revision)
                && frame.identity().nativeRevision().equals(nativeRevision) && frame.identity().dateRaw().equals(date)
                && frame.identity().player().equals(BigInteger.valueOf(actor)) && Objects.equals(frame.episodeRunId(), episode.orElse(null)),
                "Army snapshot does not bind the actual selected Driver frame");
        return new Snapshot(context, new Binding(before.machineId(), before.game(), context.sessionId(), generation,
                snapshotId, revision, nativeRevision, date, episode, actor), scope(root), actual);
    }
    public static List<ScopeArmy> scope(ObjectNode snapshot) {
        return ArmyStrengthsReadValue.scope(snapshot).stream().map(row->
                new ScopeArmy(row.army(),Role.valueOf(row.role().name()),row.wars())).toList();
    }
    public static List<ScopeArmy> selectedScope(Snapshot snapshot, Query query, boolean scopedExport) {
        if (!(query.requestedArmies() instanceof Present<List<PublicUnitId>> requested)) return snapshot.scope();
        List<ScopeArmy> selected = new ArrayList<>();
        for (PublicUnitId id : requested.value()) selected.add(snapshot.scope().stream().filter(row -> row.army().equals(id)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("requested Army lies outside actual published scope")));
        return scopedExport ? List.copyOf(selected) : snapshot.scope();
    }
    public static Read decode(Snapshot snapshot, Query query, boolean scopedExport, PlanningReadReceipt receipt,
            ArmyStrengthsFamilies.Registry families) {
        require(receipt.request().before().equals(snapshot.context().before()) && receipt.request().sessionId().equals(snapshot.context().sessionId())
                && receipt.request().operation().value().equals(STEP), "Army receipt crossed its actual selected source");
        ObjectNode result = parse(receipt.original().originalResultToken().orElseThrow().bytes());
        Set<String> required = Set.of("step", "accepted", "status", "query_sequence", "army_strengths", "backend_id", "army_strengths_profile", "army_observed_phase_coverage");
        Set<String> allowed = new HashSet<>(required); allowed.add(SHARED_KEY); allowed.add("army_native_timing_v1");
        if (query.mode() == Mode.EXPLICIT_RICH) allowed.add("observed_army_stage_inputs_12004");
        boolean subset = scopedExport && query.requestedArmies() instanceof Present<?>;
        if (subset) allowed.add("army_strengths_query_scope");
        require(names(result).containsAll(required) && allowed.containsAll(names(result)), "Army native result exact required/optional fields differ");
        if (result.has("observed_army_stage_inputs_12004")) require(result.get("observed_army_stage_inputs_12004").isNull()
                || result.get("observed_army_stage_inputs_12004").isArray(), "explicit observed stages must be an actual retained array or null");
        equal(get(result, "step"), STEP); yes(get(result, "accepted"));
        Status resultStatus = aggregateStatus(get(result, "status")); BigInteger sequence = positive(get(result, "query_sequence")).value();
        String backend = nonempty(get(result, "backend_id"));
        String expectedWire = query.mode() == Mode.PRIVATE_AUTO_SCALAR ? "private_auto_scalar_v1" : query.profile().wire();
        equal(get(result, "army_strengths_profile"), expectedWire); equal(get(result, "army_observed_phase_coverage"), query.profile().coverage());
        if (query.mode() == Mode.PRIVATE_AUTO_SCALAR) require(!result.has(SHARED_KEY), "private scalar profile cannot carry shared manager inputs");
        List<ObjectNode> expanded = expandShared(result);
        for (ObjectNode row : expanded) for (ArmyStrengthsFamilies.Key key : ArmyStrengthsFamilies.Key.values()) if (key.retainedPhase())
            require(query.profile() == Profile.OBSERVED_HISTORY_FULL_V1 ? row.has(key.wire()) : !row.has(key.wire()), "Army profile retained-journal coverage mismatch");
        if (query.mode() == Mode.EXPLICIT_RICH) families.requireCompleteRich();
        IdentityHashMap<JsonNode,EnumMap<ArmyStrengthsFamilies.Key,FamilyValue<?>>> sharedValidation = new IdentityHashMap<>();
        List<Row> rows = expanded.stream().map(row -> row(row, query.mode(), families, sharedValidation)).toList();
        List<ScopeArmy> actualScope = rows.stream().map(row -> row.core().scope()).toList();
        require(actualScope.stream().map(ScopeArmy::army).distinct().count() == actualScope.size(), "duplicate Army IDs in native rows");
        require(actualScope.equals(selectedScope(snapshot, query, scopedExport)), "native rows differ from exact ordered published scope");
        require(status(rows) == resultStatus, "Army aggregate status disagrees with atomic rows");
        Field<Status> published = new Missing<>();
        if (subset) {
            ObjectNode echo = closed(get(result, "army_strengths_query_scope"), "army_ids", "published_scope_status");
            List<PublicUnitId> echoed = units(get(echo, "army_ids"));
            require(query.requestedArmies() instanceof Present<List<PublicUnitId>> requested && echoed.equals(requested.value()), "scoped Army query echo is not the actual ordered requested subset");
            published = new Present<>(aggregateStatus(get(echo, "published_scope_status")));
        }
        Field<NativeTiming> timing = field(result, "army_native_timing_v1", raw -> {
            ObjectNode n = closed(raw, "read_total_ns", "owner_query_ns", "baseline_read_ns", "rich_attach_ns", "serialize_ns");
            return new NativeTiming(integer(get(n, "read_total_ns")), integer(get(n, "owner_query_ns")), integer(get(n, "baseline_read_ns")), integer(get(n, "rich_attach_ns")), integer(get(n, "serialize_ns")));
        });
        return new Read(query.profile(), resultStatus, sequence, backend, rows, timing, published, receipt);
    }
    /** Expansion validates the entire shared bundle and preserves each missing/null/empty distinction. */
    static List<ObjectNode> expandShared(ObjectNode result) {
        ObjectNode expanded = org.xar.ck3.control.wave2.military.sharedwire.ArmyManagerSharedWire.expand(result, false);
        return array(get(expanded, "army_strengths"), ArmyJson::object);
    }
    public static Row row(ObjectNode raw, Mode mode, ArmyStrengthsFamilies.Registry families) {
        return row(raw, mode, families, new IdentityHashMap<>());
    }
    private static Row row(ObjectNode raw, Mode mode, ArmyStrengthsFamilies.Registry families,
            IdentityHashMap<JsonNode,EnumMap<ArmyStrengthsFamilies.Key,FamilyValue<?>>> sharedValidation) {
        Set<String> allowed = new HashSet<>(CORE); allowed.addAll(GATHERING); allowed.addAll(ArmyStrengthsFamilies.allowedFieldNames());
        for (SupplyKey key : SupplyKey.values()) { allowed.add(key.rawKey()); allowed.add(key.scaleKey()); }
        require(names(raw).containsAll(CORE) && allowed.containsAll(names(raw)), "Army row exact required/optional field schema differs");
        Core core = core(raw); List<Supply> supply = new ArrayList<>();
        for (SupplyKey key : SupplyKey.values()) {
            require(raw.has(key.rawKey()) == raw.has(key.scaleKey()), "Army supply scalar requires its matching scale");
            if (!raw.has(key.rawKey())) continue; scale(get(raw, key.scaleKey()));
            Field<Long> value = nullable(raw, key.rawKey(), ArmyJson::i64);
            require(core.status() == Status.AVAILABLE || value instanceof NullValue<?>, "unavailable Army supply scalar must be null");
            if (key == SupplyKey.MERGE_SUPPLY_DESTINATION_WEIGHT && value instanceof Present<Long> p) require(p.value() >= 0, "merge supply destination weight must be nonnegative");
            if (mode == Mode.EXPLICIT_RICH || key == SupplyKey.CURRENT_SUPPLY || key == SupplyKey.CURRENT_ATTRITION_FRACTION) supply.add(new Supply(key, value));
        }
        if (mode != Mode.EXPLICIT_RICH) return new Row(core, supply, new Missing<>(), new Missing<>(), List.of());
        Field<Gathering> gathering = new Missing<>();
        if (GATHERING.stream().anyMatch(raw::has)) {
            require(names(raw).containsAll(GATHERING), "gathering fields are an atomic group");
            gathering = new Present<>(new Gathering(nullable(raw, "gathering_days_left", ArmyJson::nonnegative), enumText(get(raw, "gathering_days_status"), GatheringStatus.class), bool(get(raw, "gathering_days_ready"))));
        }
        Field<List<Regiment>> regiments = new Missing<>();
        if (raw.has("regiment_strengths")) {
            require(core.status() == Status.AVAILABLE, "unavailable Army cannot publish regiment strengths");
            List<Regiment> values = array(raw.get("regiment_strengths"), ArmyStrengthsCodec::regiment);
            int count = present(core.regimentCount()), current = present(core.currentSoldiers()), maximum = present(core.maximumSoldiers());
            require(values.size() == count && values.stream().map(value -> BigInteger.valueOf(value.currentSoldiers())).reduce(BigInteger.ZERO, BigInteger::add).equals(BigInteger.valueOf(current))
                    && values.stream().map(value -> BigInteger.valueOf(value.maximumSoldiers())).reduce(BigInteger.ZERO, BigInteger::add).equals(BigInteger.valueOf(maximum)), "regiment rows do not cover same-frame strength aggregates");
            regiments = new Present<>(values);
        }
        List<FamilyValue<?>> normalized = new ArrayList<>();
        RowContext context = new RowContext(core, regiments);
        for (ArmyStrengthsFamilies.Key key : ArmyStrengthsFamilies.Key.values()) {
            if (key == ArmyStrengthsFamilies.Key.REGIMENT_STRENGTHS || !raw.has(key.wire()) && !key.defaultNullWhenMissing()) continue;
            if (key == ArmyStrengthsFamilies.Key.CURRENT_DISEMBARK_PENALTY_V1 || key == ArmyStrengthsFamilies.Key.COUNTY_ENTRY_INPUTS_V1 || key == ArmyStrengthsFamilies.Key.REGIMENT_REPLENISHMENT)
                require(core.status() == Status.AVAILABLE, "unavailable Army cannot publish this available-only family");
            boolean sharedManager = java.util.Arrays.stream(org.xar.ck3.control.wave2.military.sharedwire.ArmyManagerSharedWire.Family.values())
                    .anyMatch(family -> family.wireName().equals(key.wire()));
            JsonNode original = raw.get(key.wire());
            if (sharedManager && original != null && original.isObject()) {
                EnumMap<ArmyStrengthsFamilies.Key,FamilyValue<?>> previous = sharedValidation.computeIfAbsent(original, ignored -> new EnumMap<>(ArmyStrengthsFamilies.Key.class));
                FamilyValue<?> value = previous.get(key);
                if (value == null) { value = families.normalize(key, field(raw, key.wire(), node -> new RawJson(bytes(node))), context); previous.put(key, value); }
                normalized.add(value);
            } else normalized.add(families.normalize(key, field(raw, key.wire(), node -> new RawJson(bytes(node))), context));
        }
        return new Row(core, supply, gathering, regiments, normalized);
    }
    static Core core(ObjectNode raw) {
        Status status = enumText(get(raw, "status"), Status.class); scale(get(raw, "ai_base_power_scale"));
        return new Core(status, unit(get(raw, "army_id")), nullable(raw, "native_carmy_id", ArmyJson::full), enumText(get(raw, "scope_role"), Role.class),
                distinct(array(get(raw, "war_ids"), ArmyJson::id), 0, 65536, "strength war IDs"), nullable(raw, "regiment_count", ArmyJson::nonnegative), nullable(raw, "current_soldiers", ArmyJson::nonnegative),
                nullable(raw, "maximum_soldiers", ArmyJson::nonnegative), nullable(raw, "ai_base_power_raw", ArmyJson::i64), nullable(raw, "unavailable_reason", ArmyJson::nonempty));
    }
    static Regiment regiment(JsonNode raw) {
        ObjectNode row = object(raw); Set<String> base = Set.of("army_regiment_id", "current_soldiers", "maximum_soldiers", "scale");
        Set<String> composition = Set.of("maa_type_status", "maa_type_key", "siege_tier_observable", "siege_tier", "composition_unavailable_reason");
        Set<String> eligibility = Set.of("native_supply_loss_eligible", "supply_loss_eligibility_unavailable_reason");
        Set<String> allowed = new HashSet<>(base); allowed.addAll(composition); allowed.addAll(eligibility);
        require(names(row).containsAll(base) && allowed.containsAll(names(row)), "regiment strength schema differs"); equal(get(row, "scale"), BigInteger.ONE);
        Field<Composition> composed = new Missing<>();
        if (composition.stream().anyMatch(row::has)) {
            require(names(row).containsAll(composition), "regiment composition fields are an atomic group");
            composed = new Present<>(new Composition(enumText(get(row, "maa_type_status"), MaaStatus.class), nullable(row, "maa_type_key", ArmyJson::nonempty),
                    nullable(row, "siege_tier", ArmyJson::i32), bool(get(row, "siege_tier_observable")), nullable(row, "composition_unavailable_reason", ArmyJson::nonempty)));
        }
        Field<SupplyEligibility> eligible = new Missing<>();
        if (eligibility.stream().anyMatch(row::has)) {
            require(names(row).containsAll(eligibility), "regiment supply eligibility fields are an atomic group");
            eligible = new Present<>(new SupplyEligibility(nullable(row, "native_supply_loss_eligible", ArmyJson::bool), nullable(row, "supply_loss_eligibility_unavailable_reason", ArmyJson::nonempty)));
        }
        return new Regiment(nonnegative(get(row, "army_regiment_id")), nonnegative(get(row, "current_soldiers")), nonnegative(get(row, "maximum_soldiers")), composed, eligible);
    }
    public static ObjectNode coreJson(Core core) {
        ObjectNode row = empty().put("status", wire(core.status())).put("army_id", core.army().value()).put("scope_role", wire(core.role())).put("ai_base_power_scale", SCALE);
        put(row, "native_carmy_id", core.nativeArmy(), value -> empty().numberNode(value.value()));
        var wars = row.putArray("war_ids"); core.wars().forEach(id -> wars.add(id.value()));
        put(row, "regiment_count", core.regimentCount(), value -> empty().numberNode(value)); put(row, "current_soldiers", core.currentSoldiers(), value -> empty().numberNode(value));
        put(row, "maximum_soldiers", core.maximumSoldiers(), value -> empty().numberNode(value)); put(row, "ai_base_power_raw", core.aiBasePowerRaw(), value -> empty().numberNode(value));
        put(row, "unavailable_reason", core.unavailableReason(), value -> empty().textNode(value)); return row;
    }
    public static ObjectNode rowJson(Row value) {
        ObjectNode row = coreJson(value.core());
        value.supply().forEach(supply -> { put(row, supply.key().rawKey(), supply.raw(), n -> empty().numberNode(n)); row.put(supply.key().scaleKey(), SCALE); });
        if (value.gathering() instanceof Present<Gathering> p) { Gathering g = p.value(); put(row, "gathering_days_left", g.daysLeft(), n -> empty().numberNode(n)); row.put("gathering_days_status", wire(g.status())).put("gathering_days_ready", g.ready()); }
        if (value.regiments() instanceof Present<List<Regiment>> p) {
            var target = row.putArray("regiment_strengths");
            p.value().forEach(regiment -> target.add(regimentJson(regiment)));
        }
        value.families().forEach(family -> row.set(family.key().wire(), parseValue(family.normalizedJson()))); return row;
    }
    /** Sole complete regiment encoder, shared by full rows and conditional refill consumers. */
    public static ObjectNode regimentJson(Regiment regiment) {
        Objects.requireNonNull(regiment);
        ObjectNode node = empty().put("army_regiment_id", regiment.armyRegimentId()).put("current_soldiers", regiment.currentSoldiers()).put("maximum_soldiers", regiment.maximumSoldiers()).put("scale", 1);
        if (regiment.composition() instanceof Present<Composition> p) {
            Composition value = p.value(); node.put("maa_type_status", wire(value.status())).put("siege_tier_observable", value.siegeTierObservable());
            put(node, "maa_type_key", value.key(), v -> empty().textNode(v)); put(node, "siege_tier", value.siegeTier(), v -> empty().numberNode(v)); put(node, "composition_unavailable_reason", value.reason(), v -> empty().textNode(v));
        }
        if (regiment.supplyEligibility() instanceof Present<SupplyEligibility> p) {
            SupplyEligibility value = p.value(); put(node, "native_supply_loss_eligible", value.eligible(), v -> empty().booleanNode(v)); put(node, "supply_loss_eligibility_unavailable_reason", value.reason(), v -> empty().textNode(v));
        }
        return node;
    }
    static JsonNode parseValue(RawJson raw) { return ArmyJson.parseValue(Objects.requireNonNull(raw).bytes(), RawJson.MAXIMUM_BYTES); }
    public static ObjectNode rowPublicV2Json(Row value) {
        ObjectNode row = rowJson(value);
        value.families().forEach(family -> row.set(family.key().wire(), parseValue(family.publicV2Json())));
        List<ArmyStrengthsPublicNumbers.Rule> rules = new ArrayList<>();
        rules.add(new ArmyStrengthsPublicNumbers.Rule("/ai_base_power_raw", ArmyStrengthsPublicNumbers.Domain.SIGNED_64));
        value.supply().forEach(supply -> rules.add(new ArmyStrengthsPublicNumbers.Rule("/" + supply.key().rawKey(), ArmyStrengthsPublicNumbers.Domain.SIGNED_64)));
        return parse(ArmyStrengthsPublicNumbers.encode(new RawJson(bytes(row)), rules).bytes());
    }
    static <T> void put(ObjectNode row, String name, Field<T> field, java.util.function.Function<T,JsonNode> encoder) { if (field instanceof NullValue<?>) row.putNull(name); else if (field instanceof Present<T> p) row.set(name, encoder.apply(p.value())); }
    static <E extends Enum<E>> E enumText(JsonNode raw, Class<E> type) { String value = text(raw); E result = Enum.valueOf(type, value.toUpperCase(Locale.ROOT)); require(wire(result).equals(value), "exact Army enum spelling required"); return result; }
    static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    static Status aggregateStatus(JsonNode raw) { Status status = enumText(raw, Status.class); require(status != Status.UNAVAILABLE, "query status must be available or partial"); return status; }
    static void scale(JsonNode raw) { equal(raw, BigInteger.valueOf(SCALE)); }
    static <T> T present(Field<T> value) { if (value instanceof Present<T> p) return p.value(); throw new IllegalArgumentException("observed value required"); }
}
