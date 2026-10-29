package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.RouteContext;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovementCodec;
import org.xar.ck3.control.wave2.military.prestore.PrestoreCodec;
import org.xar.ck3.control.wave2.military.prestore.PrestoreDisembark;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrame;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;
import org.xar.ck3.control.wave3.military.landcontext.LandContextCodec;
import org.xar.ck3.control.wave3.military.landcontext.ProvinceContributors;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPublicNumbers.Domain;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPublicNumbers.Rule;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline.Stage;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Query-start movement observations and six conditional projections; none executes or observes a callback. */
public final class ArmyStrengthsMovement {
    private ArmyStrengthsMovement() { }
    private static final String BOUNDARY = "current_query_before_unit_new_date_stage";
    private static final String TARGET_SOURCE = "native_current_first_route_target_supply_contributors_12004";
    private static final String TARGET_BASIS = "captured_committed_first_route_target";
    private static final long PROVINCE = 0x50726f76L;
    private static final List<String> CLOCK = List.of("source_derived_full_cdate64_ready", "source_derived_next_date_raw_i32",
            "source_derived_next_native_day_index_raw_i32", "source_derived_next_date_storage_raw64",
            "source_derived_next_calendar_day_u8", "source_derived_next_calendar_month_u8");
    private static final List<String> SCHEDULE_FALSE = List.of("actual_unit_new_date_callback_observed", "actual_movement_or_arrival_observed",
            "earlier_stage_outputs_reconstructed", "full_daily_supply_transition_ready", "full_monthly_ready");
    public enum Availability { AVAILABLE, UNAVAILABLE }
    public enum TargetStatus { AVAILABLE, NO_COMMITTED_TARGET, PARTIAL, UNAVAILABLE }
    public record Schedule(Availability status, String reason, Long army, Long carmy, Integer vectorCount, Boolean dataPresent,
            List<Integer> positions, Integer occurrences) {
        public Schedule { Objects.requireNonNull(status); if (positions != null) positions = List.copyOf(positions); }
        public boolean ready() { return status == Availability.AVAILABLE; }
    }
    public record Entry(Availability status, String reason, Long army, Long carmy, Integer routeCount) {
        public Entry { Objects.requireNonNull(status); }
        public boolean ready() { return status == Availability.AVAILABLE; }
    }
    public record TargetInput(TargetStatus status, String reason, boolean ready, Integer army, Integer carmy, Integer current,
            Integer target, Integer routeCount, ProvinceContributors contributors, List<Integer> matching, Integer includedCount) {
        public TargetInput { Objects.requireNonNull(status); matching = List.copyOf(matching); }
    }
    public record Provenance(String snapshotId, BigInteger revision, BigInteger nativeRevision) {
        public Provenance { Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision); }
    }
    public record Joined<T>(int army, Provenance provenance, T projection) {
        public Joined { require(army >= 0, "public Unit subject must be nonnegative int32"); Objects.requireNonNull(provenance); Objects.requireNonNull(projection); }
    }
    public record Contexts(List<RouteContext> allFirst, List<RouteContext> playersLast) {
        public Contexts { allFirst = List.copyOf(allFirst); playersLast = List.copyOf(playersLast); }
        public RouteContext target(int id) { return allFirst.stream().filter(c -> c.armyId() == id).findFirst().orElse(null); }
        public RouteContext player(int id) { RouteContext found = null; for (RouteContext c : playersLast) if (c.armyId() == id) found = c; return found; }
    }
    public record TargetProjection(TargetInput input, RouteContext context) { }
    public record EntryProjection(Entry entry, Schedule schedule, SourceNextFrame clock, Integer rawState,
            Boolean scheduled, Integer resultingState, Boolean wouldWrite, String reason) {
        public boolean ready() { return reason == null; }
    }
    public record Prefix(EntryProjection entry, Optional<CurrentMovement> movement, Integer rawReference,
            String gate, Boolean addSelected, Boolean admissionRequired, boolean currentRateDemanded,
            Long rate, String rateSource, Long resultingWeight, String reason) {
        public Prefix { Objects.requireNonNull(entry); Objects.requireNonNull(movement); }
        public boolean ready() { return reason == null; }
    }
    public record Edge(Prefix prefix, Long cost, Integer provider, Boolean selected, Boolean providerDemanded,
            String bypass, String reason) {
        public Edge { Objects.requireNonNull(prefix); }
        public boolean ready() { return reason == null; }
    }
    public record Arrival(Edge edge, RouteContext context, Long targetType, Boolean tagDemanded,
            Long residual, Integer consumed, List<Integer> remaining, Integer remainingCount,
            Boolean write, Integer nextProvince, String reason) {
        public Arrival { Objects.requireNonNull(edge); if (remaining != null) remaining = List.copyOf(remaining); }
        public boolean ready() { return reason == null; }
    }
    public record TargetBatch(List<Joined<TargetProjection>> rows) { public TargetBatch { rows = List.copyOf(rows); } }
    public record EntryBatch(List<Joined<EntryProjection>> rows) { public EntryBatch { rows = List.copyOf(rows); } }
    public record PrefixBatch(List<Joined<Prefix>> rows) { public PrefixBatch { rows = List.copyOf(rows); } }
    public record EdgeBatch(List<Joined<Edge>> rows) { public EdgeBatch { rows = List.copyOf(rows); } }
    public record ArrivalBatch(List<Joined<Arrival>> rows) { public ArrivalBatch { rows = List.copyOf(rows); } }
    public record PrestoreBatch(List<Joined<PrestoreDisembark.Result>> rows) { public PrestoreBatch { rows = List.copyOf(rows); } }

    /** Root calls once before registry/pipeline freeze, with the actual immutable bundle source. */
    public static void install(ArmyStrengthsFamilies.Registry registry, ArmyStrengthsPipeline pipeline, ExactRef actualJavaBundleSource) {
        Objects.requireNonNull(registry); Objects.requireNonNull(pipeline); Objects.requireNonNull(actualJavaBundleSource);
        registry.register(Key.CURRENT_FIRST_ROUTE_TARGET_SUPPLY_CONTRIBUTORS_V1, TargetInput.class,
                (raw, row) -> normalized(raw, n -> target(n, row.core().army().value(), nativeId(row.core()), null)),
                value -> raw(fieldNode(value, ArmyStrengthsMovement::targetNode)),
                value -> ArmyStrengthsPublicNumbers.encode(raw(fieldNode(value, ArmyStrengthsMovement::targetNode)), targetRules("/target_contributors_v1")), actualJavaBundleSource);
        registry.register(Key.CURRENT_UNIT_NEW_DATE_SCHEDULE_INPUTS_V1, Schedule.class,
                (raw, row) -> normalized(raw, n -> schedule(n, row.core().army().value(), nativeId(row.core()))),
                value -> raw(fieldNode(value, ArmyStrengthsMovement::scheduleNode)), actualJavaBundleSource);
        registry.register(Key.CURRENT_UNIT_NEW_DATE_CALLBACK_ENTRY_INPUTS_V1, Entry.class,
                (raw, row) -> normalized(raw, n -> entry(n, row.core().army().value(), nativeId(row.core()))),
                value -> raw(fieldNode(value, ArmyStrengthsMovement::entryNode)), actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_FIRST_ROUTE_TARGET_SUPPLY_CONTRIBUTORS_V1, TargetBatch.class, List.of(), (input, earlier) -> {
            Contexts contexts = contexts(input); List<Joined<TargetProjection>> rows = new ArrayList<>();
            for (ArmyStrengths.Row row : input.selected()) { JsonNode strength = ArmyStrengthsCodec.rowJson(row); RouteContext context = contexts.target(row.core().army().value());
                rows.add(join(input, row, new TargetProjection(target(strength.get(Key.CURRENT_FIRST_ROUTE_TARGET_SUPPLY_CONTRIBUTORS_V1.wire()), row.core().army().value(), nativeId(row.core()), context), context))); }
            return new TargetBatch(rows);
        }, value -> rows(value.rows(), ArmyStrengthsMovement::targetProjectionNode, false),
           value -> ArmyStrengthsPublicNumbers.encode(rows(value.rows(), ArmyStrengthsMovement::targetProjectionNode, false), targetRules("/*/projection/observed_inputs/target_contributors_v1")), actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_UNIT_NEW_DATE_ENTRY_NORMALIZATION_V1, EntryBatch.class, List.of(), (input, earlier) -> {
            List<Joined<EntryProjection>> rows = new ArrayList<>(); for (ArmyStrengths.Row row : input.selected()) rows.add(join(input, row, entryProjection(ArmyStrengthsCodec.rowJson(row)))); return new EntryBatch(rows);
        }, value -> rows(value.rows(), ArmyStrengthsMovement::entryProjectionNode, true),
           value -> publicRows(rows(value.rows(), ArmyStrengthsMovement::entryProjectionNode, true), "source_derived_next_date_storage_raw64"), actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_UNIT_NEXT_MOVEMENT_PREFIX_V1, PrefixBatch.class, List.of(Stage.CURRENT_UNIT_NEW_DATE_ENTRY_NORMALIZATION_V1), (input, earlier) -> {
            var entries = earlier.required(Stage.CURRENT_UNIT_NEW_DATE_ENTRY_NORMALIZATION_V1, EntryBatch.class); List<Joined<Prefix>> rows = new ArrayList<>();
            for (ArmyStrengths.Row row : input.selected()) rows.add(join(input, row, prefix(ArmyStrengthsCodec.rowJson(row), find(entries.rows(), row.core().army().value())))); return new PrefixBatch(rows);
        }, value -> rows(value.rows(), ArmyStrengthsMovement::prefixNode, true),
           value -> publicRows(rows(value.rows(), ArmyStrengthsMovement::prefixNode, true), "source_derived_next_date_storage_raw64 accumulated_movement_weight_raw cached_edge_speed_raw current_edge_movement_rate_raw selected_movement_rate_raw conditional_unit_168_raw_after_next_new_date_movement_prefix"), actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_UNIT_NEXT_FIRST_EDGE_SELECTION_V1, EdgeBatch.class, List.of(Stage.CURRENT_UNIT_NEXT_MOVEMENT_PREFIX_V1), (input, earlier) -> {
            var prefixes = earlier.required(Stage.CURRENT_UNIT_NEXT_MOVEMENT_PREFIX_V1, PrefixBatch.class); List<Joined<Edge>> rows = new ArrayList<>();
            for (ArmyStrengths.Row row : input.selected()) rows.add(join(input, row, edge(find(prefixes.rows(), row.core().army().value())))); return new EdgeBatch(rows);
        }, value -> rows(value.rows(), ArmyStrengthsMovement::edgeNode, true),
           value -> publicRows(rows(value.rows(), ArmyStrengthsMovement::edgeNode, true), "conditional_post_add_unit_168_raw first_route_edge_weight_cost_raw current_remaining_duration_days_existing/raw"), actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_UNIT_NEXT_ARRIVAL_TRANSITION_V1, ArrivalBatch.class, List.of(Stage.CURRENT_UNIT_NEXT_FIRST_EDGE_SELECTION_V1), (input, earlier) -> {
            var edges = earlier.required(Stage.CURRENT_UNIT_NEXT_FIRST_EDGE_SELECTION_V1, EdgeBatch.class); Contexts contexts = contexts(input); List<Joined<Arrival>> rows = new ArrayList<>();
            for (ArmyStrengths.Row row : input.selected()) { int id = row.core().army().value(); rows.add(join(input, row, arrival(id, find(edges.rows(), id), contexts.player(id)))); } return new ArrivalBatch(rows);
        }, value -> rows(value.rows(), ArmyStrengthsMovement::arrivalNode, true),
           value -> publicRows(rows(value.rows(), ArmyStrengthsMovement::arrivalNode, true), "conditional_post_add_unit_168_raw first_route_edge_weight_cost_raw conditional_unit_168_raw_after_arrival_subtraction current_remaining_duration_days_existing/raw current_committed_route_timeline_existing/native_full_route_remaining_days_q100000 current_committed_route_timeline_existing/native_route_prefix_remaining_days_q100000/*"), actualJavaBundleSource);
        pipeline.register(Stage.CURRENT_UNIT_ARRIVAL_PRESTORE_DISEMBARK_WRITE_V1, PrestoreBatch.class, List.of(Stage.CURRENT_UNIT_NEXT_ARRIVAL_TRANSITION_V1), (input, earlier) -> {
            var arrivals = earlier.required(Stage.CURRENT_UNIT_NEXT_ARRIVAL_TRANSITION_V1, ArrivalBatch.class); List<Joined<PrestoreDisembark.Result>> rows = new ArrayList<>();
            for (ArmyStrengths.Row row : input.selected()) { Arrival arrival = find(arrivals.rows(), row.core().army().value());
                rows.add(join(input, row, prestore(ArmyStrengthsCodec.rowJson(row), arrival))); } return new PrestoreBatch(rows);
        }, value -> rows(value.rows(), PrestoreCodec::node, true),
           value -> publicRows(rows(value.rows(), PrestoreCodec::node, true), "current_remaining_duration_days_existing/raw county_entry_risk_v1/observed_current_native_budget/effective_fraction_raw county_entry_risk_v1/observed_current_native_budget/minimum_multiplier_raw county_entry_risk_v1/observed_loaded_multiplier_floors/base_floor_raw county_entry_risk_v1/observed_loaded_multiplier_floors/army_1d4_nonzero_floor_raw county_entry_risk_v1/multiplier_branch_explanation/inferred_ordinary_army_property_1a7_raw"), actualJavaBundleSource);
    }

    public static Schedule schedule(JsonNode node, Integer expectedArmy, Integer expectedCarmy) {
        if (absent(node)) return null;
        exact(node, "schema_version source capture_boundary status ready unavailable_reason subject_army_id_u32 subject_carmy_id_u32 vector_header_count_i32 subject_stored_id_occurrence_count_i32 vector_data_present subject_stored_id_positions actual_unit_new_date_callback_observed actual_movement_or_arrival_observed earlier_stage_outputs_reconstructed full_daily_supply_transition_ready full_monthly_ready");
        identity(node, "native_current_unit_new_date_schedule_inputs_12004"); SCHEDULE_FALSE.forEach(key -> no(node.get(key)));
        Availability status = availability(node); Long army = u32(node.get("subject_army_id_u32")), carmy = u32(node.get("subject_carmy_id_u32"));
        expected(army, expectedArmy); expected(carmy, expectedCarmy); Integer count = i32(node.get("vector_header_count_i32"));
        Boolean data = nullableBool(node.get("vector_data_present")); List<Integer> positions = integers(node.get("subject_stored_id_positions"));
        Integer occurrences = i32(node.get("subject_stored_id_occurrence_count_i32")); int last = -1;
        if (positions != null) for (int index : positions) { require(index > last, "stored positions must be nonnegative, distinct and ordered"); last = index; }
        require(occurrences == null || occurrences >= 0, "stored occurrence count cannot be negative");
        if (status == Availability.AVAILABLE) {
            require(army != null && carmy != null && count != null && data != null && count >= 0 && (count == 0 || data), "ready schedule needs complete subject/header/data");
            require(positions != null && Objects.equals(occurrences, positions.size()), "schedule occurrence count differs from stored positions");
            for (int index : positions) require(index < count, "stored position exceeds current vector count");
        } else require(positions == null && occurrences == null, "unavailable schedule cannot claim stored positions/count");
        return new Schedule(status, text(node.get("unavailable_reason")), army, carmy, count, data, positions, occurrences);
    }
    public static Entry entry(JsonNode node, Integer expectedArmy, Integer expectedCarmy) {
        if (absent(node)) return null;
        exact(node, "schema_version source capture_boundary status ready unavailable_reason subject_army_id_u32 subject_carmy_id_u32 unit_route_count_i32");
        identity(node, "native_current_unit_new_date_callback_entry_inputs_12004"); Availability status = availability(node);
        Long army = u32(node.get("subject_army_id_u32")), carmy = u32(node.get("subject_carmy_id_u32")); expected(army, expectedArmy); expected(carmy, expectedCarmy);
        Integer count = i32(node.get("unit_route_count_i32")); require(status != Availability.AVAILABLE || army != null && count != null, "ready callback entry needs subject and signed route count");
        return new Entry(status, text(node.get("unavailable_reason")), army, carmy, count);
    }
    public static TargetInput target(JsonNode node, Integer expectedArmy, Integer expectedCarmy, RouteContext context) {
        if (absent(node)) return null;
        exact(node, "source status unavailable_reason current_target_inputs_ready subject_army_id subject_carmy_id current_province_id first_route_target_province_id route_source_count target_contributors_v1 subject_matching_occurrence_indices subject_included_occurrence_count input_basis actual_arrival_observed actual_after_arrival_usage_observed full_arrival_supply_transition_ready");
        eq(node.get("source"), TARGET_SOURCE); eq(node.get("input_basis"), TARGET_BASIS);
        no(node.get("actual_arrival_observed")); no(node.get("actual_after_arrival_usage_observed")); no(node.get("full_arrival_supply_transition_ready"));
        String wire = StrictJson.text(node.get("status")); TargetStatus status;
        try { status = TargetStatus.valueOf(wire.toUpperCase(java.util.Locale.ROOT)); } catch (IllegalArgumentException invalid) { throw new IllegalArgumentException("unknown target contributor status", invalid); }
        require(wire.equals(status.name().toLowerCase(java.util.Locale.ROOT)), "exact target status spelling");
        String reason = text(node.get("unavailable_reason")); boolean ready = bool(node.get("current_target_inputs_ready"));
        require(status == TargetStatus.AVAILABLE || status == TargetStatus.NO_COMMITTED_TARGET ? reason == null : reason != null, "target reason differs from status");
        Integer army = i32(node.get("subject_army_id")), carmy = i32(node.get("subject_carmy_id")), current = i32(node.get("current_province_id"));
        Integer target = i32(node.get("first_route_target_province_id")), count = i32(node.get("route_source_count")), included = i32(node.get("subject_included_occurrence_count"));
        require(expectedArmy == null || Objects.equals(army, expectedArmy), "target public Army differs from same-query row");
        require(expectedCarmy == null || Objects.equals(carmy, expectedCarmy), "target private CArmy differs from same-query row");
        List<Integer> matching = integers(node.get("subject_matching_occurrence_indices")); require(matching != null, "target matching positions array required"); int last = -1;
        for (int index : matching) { require(index > last, "target matching positions must preserve ordered native occurrences"); last = index; }
        ProvinceContributors nested = LandContextCodec.decodeProvince(node.get("target_contributors_v1"));
        if (nested == null) require(matching.isEmpty() && included == null, "missing target roster cannot supply occurrence witnesses");
        else {
            require(Objects.equals(nested.provinceId(), target) && Objects.equals(nested.subjectArmyId(), army) && Objects.equals(nested.subjectCarmyId(), carmy), "nested target contributor context differs");
            for (int index : matching) { require(index < nested.occurrences().size(), "target subject index exceeds captured roster"); var occurrence = nested.occurrences().get(index);
                require(Objects.equals(occurrence.armyId(), army) && (occurrence.nativeCarmyId() == null || Objects.equals(occurrence.nativeCarmyId(), carmy)), "target matching position is another receiver"); }
            if (nested.contributorsReady()) { List<Integer> actual = new ArrayList<>(); int includedActual = 0;
                for (int index = 0; index < nested.occurrences().size(); index++) { var occurrence = nested.occurrences().get(index);
                    if (Objects.equals(occurrence.armyId(), army) && Objects.equals(occurrence.nativeCarmyId(), carmy)) { actual.add(index); if (Boolean.TRUE.equals(occurrence.included())) includedActual++; } }
                require(actual.equals(matching) && Objects.equals(included, includedActual), "complete target subject roster/count differs");
            } else require(included == null, "partial target roster cannot claim complete subject count");
        }
        if (status == TargetStatus.AVAILABLE) require(ready && nested != null && nested.status() == org.xar.ck3.control.wave3.military.landcontext.FullDataModel.Coverage.AVAILABLE
                && nested.contributorsReady() && nested.currentUsageReady() && army != null && carmy != null && target != null && count != null && count > 0, "available target needs complete current committed-target inputs");
        else require(!ready, "incomplete/no-target observation cannot be ready");
        if (status == TargetStatus.NO_COMMITTED_TARGET) require(Objects.equals(count, 0) && target == null && nested == null && matching.isEmpty() && included == null, "no target must preserve empty route/absent target");
        if (context != null) {
            require(Objects.equals(context.armyId(), army), "target context subject differs");
            require(context.currentProvinceId() == null || current == null || context.currentProvinceId().equals(current), "target current Province differs from query-start context");
            if (context.routeProvinceIds() != null) {
                if (target != null) require(!context.routeProvinceIds().isEmpty() && context.routeProvinceIds().getFirst().equals(target), "target differs from query-start first route entry");
                else if (status == TargetStatus.NO_COMMITTED_TARGET) require(context.routeProvinceIds().isEmpty(), "no target disagrees with query-start route");
            }
            require(context.routeSourceCount() == null || count == null || context.routeSourceCount().equals(count), "target route count differs from query-start context");
        }
        return new TargetInput(status, reason, ready, army, carmy, current, target, count, nested, matching, included);
    }

    public static EntryProjection entryProjection(JsonNode strength) {
        int army = requiredId(strength, "army_id"); Integer carmy = i32(strength.get("native_carmy_id"));
        Entry entry = entry(strength.get(Key.CURRENT_UNIT_NEW_DATE_CALLBACK_ENTRY_INPUTS_V1.wire()), army, carmy);
        Schedule schedule = schedule(strength.get(Key.CURRENT_UNIT_NEW_DATE_SCHEDULE_INPUTS_V1.wire()), army, carmy);
        var budget = MonthlyLossCodec.decodeFamilyNullable(strength.get("monthly_loss_budget_inputs_v1"));
        SourceNextFrame clock = SourceNextFrameCodec.decode(strength.get("source_derived_next_daily_supply_frame_inputs_v1"), army, carmy);
        Integer state = budget == null ? null : budget.admission().unitNative170Raw();
        String reason = entry == null ? "current_unit_new_date_callback_entry_inputs_absent" : !entry.ready() ? entry.reason()
                : schedule == null ? "current_unit_new_date_schedule_inputs_absent" : !schedule.ready() ? schedule.reason()
                : state == null ? "current_unit_native_170_raw_unavailable" : null;
        Boolean scheduled = schedule == null || !schedule.ready() ? null : !schedule.positions().isEmpty();
        Boolean write = reason == null ? Boolean.TRUE.equals(scheduled) && Integer.toUnsignedLong(state - 2) <= 1 && entry.routeCount() == 0 : null;
        Integer output = reason == null ? Boolean.TRUE.equals(write) ? 0 : state : null;
        return new EntryProjection(entry, schedule, clock, state, scheduled, output, write, reason);
    }
    public static Prefix prefix(JsonNode strength, EntryProjection entry) {
        Optional<CurrentMovement> movement = CurrentMovementCodec.normalize(strength.get("current_movement_progress")); CurrentMovement m = movement.orElse(null);
        JsonNode rawResolution = strength.get("native_army_resolution_v1");
        var resolution = absent(rawResolution) ? null : ArmyStrengthsNativeFields.resolution(ArmyJson.object(rawResolution));
        Integer reference = resolution == null || !(resolution.rawReference() instanceof Present<Integer> p) ? null : p.value();
        Long weight = m == null ? null : m.accumulatedWeight(), cached = m == null ? null : m.cachedEdgeSpeed(), currentRate = m == null ? null : m.currentEdgeRate().value();
        Boolean admission = m == null ? null : m.nativeArmyAdmission().value(); Integer count = entry.entry() == null ? null : entry.entry().routeCount(), state = entry.resultingState();
        String reason = null, gate = null, rateSource = null; Long output = null, rate = null; Boolean add = null, required = null; boolean demanded = false;
        if (entry.scheduled() == null) reason = "current_unit_new_date_schedule_inputs_unavailable";
        else if (weight == null) reason = "current_unit_accumulated_movement_weight_unavailable";
        else if (!entry.scheduled()) { gate = "not_scheduled"; add = false; rateSource = "not_demanded"; output = weight; required = false; }
        else if (entry.entry() == null || !entry.entry().ready()) reason = entry.entry() == null ? "current_unit_new_date_callback_entry_inputs_absent" : entry.entry().reason();
        else if (count == 0) { gate = "route_zero"; add = false; rateSource = "not_demanded"; output = weight; required = false; }
        else {
            if (Objects.equals(reference, -1)) { gate = "direct_raw_unit178_absent"; add = true; required = false; }
            else if (Objects.equals(state, 1)) { gate = "direct_raw_unit170_1"; add = true; required = false; }
            else if (reference == null || state == null) { gate = "native_army_predicate_unresolved"; reason = "unit_new_date_native_army_movement_admission_predicate_unavailable"; }
            else { required = true;
                if (Boolean.TRUE.equals(admission)) { gate = "native_army_predicate_true"; add = true; }
                else if (Boolean.FALSE.equals(admission)) { gate = "native_army_predicate_false"; add = false; rateSource = "not_demanded"; output = weight; }
                else { gate = "native_army_predicate_unresolved"; reason = "unit_new_date_native_army_movement_admission_predicate_unavailable"; }
            }
            if (Boolean.TRUE.equals(add)) {
                if (cached == null) reason = "current_unit_cached_edge_speed_unavailable";
                else if (cached > 0) { rate = cached; rateSource = "cached_unit_190"; }
                else { demanded = true; rate = currentRate; rateSource = "current_edge_getter"; if (rate == null) reason = "current_edge_movement_rate_unavailable"; }
                if (reason == null) output = weight + rate;
            }
        }
        return new Prefix(entry, movement, reference, gate, add, required, demanded, rate, rateSource, output, reason);
    }
    public static Edge edge(Prefix prefix) {
        CurrentMovement m = prefix.movement().orElse(null); Long cost = m == null ? null : m.firstEdgeCost().value(); Integer provider = m == null ? null : m.arrivalProviderByte().value();
        Boolean selected = null, demanded = null; String bypass = null, reason = null;
        if (!prefix.ready()) reason = fallback(prefix.reason(), "conditional_movement_prefix_unavailable");
        else if (Boolean.FALSE.equals(prefix.entry().scheduled())) { selected = false; demanded = false; bypass = "not_scheduled_by_observed_stored_ids"; }
        else if ("route_zero".equals(prefix.gate())) { selected = false; demanded = false; bypass = "route_zero_under_inputs_held_at_movement_gate"; }
        else if (prefix.resultingWeight() == null) reason = "conditional_post_add_unit_168_unavailable";
        else if (cost == null) reason = "first_route_edge_weight_cost_unavailable";
        else if (prefix.resultingWeight() > cost) { selected = true; demanded = false; }
        else { demanded = true; if (provider == null) reason = "first_edge_arrival_provider_byte_e_unavailable"; else selected = provider != 0; }
        return new Edge(prefix, cost, provider, selected, demanded, bypass, reason);
    }
    public static Arrival arrival(int army, Edge edge, RouteContext context) {
        CurrentMovement m = edge.prefix().movement().orElse(null); Long tag = m == null ? null : m.targetProvinceType().value();
        Integer current = context == null ? null : context.currentProvinceId(), count = context == null ? null : context.routeSourceCount();
        List<Integer> route = context == null ? null : context.routeProvinceIds(); boolean complete = context != null && ("complete_empty".equals(context.routeReadStatus()) || "complete_nonempty".equals(context.routeReadStatus()));
        String reason = null; Integer consumed = null, remainingCount = null, next = null; Long residual = null; List<Integer> remaining = null; Boolean write = null, demanded = null;
        if (!edge.ready()) reason = fallback(edge.reason(), "conditional_first_edge_selection_unavailable");
        else if (Boolean.FALSE.equals(edge.selected())) { demanded = false; write = false; residual = edge.prefix().resultingWeight(); next = current;
            if (complete) { remaining = route; remainingCount = count; } }
        else if (Boolean.TRUE.equals(edge.selected())) {
            demanded = true;
            if (edge.prefix().resultingWeight() != null && edge.cost() != null) residual = edge.prefix().resultingWeight() - edge.cost();
            else reason = "conditional_arrival_subtraction_inputs_unavailable";
            if (complete && count != null && count > 0 && route != null && route.size() == count) { consumed = route.getFirst(); remaining = route.subList(1, route.size()); remainingCount = count - 1; }
            else reason = fallback(reason, "complete_current_route_unavailable");
            if (tag == null) reason = fallback(reason, "first_route_target_province_type_tag_unavailable");
            else if (current != null && consumed != null) { write = tag == PROVINCE && !consumed.equals(current); next = write ? consumed : current; }
        } else reason = "conditional_first_edge_selection_unavailable";
        if (context == null || context.armyId() != army) { reason = "query_start_army_context_unavailable"; write = Boolean.FALSE.equals(edge.selected()) ? false : null; next = null; }
        else if (current == null) { reason = fallback(reason, "current_province_id_unavailable"); next = null; }
        return new Arrival(edge, context, tag, demanded, residual, consumed, remaining, remainingCount, write, next, reason);
    }
    public static PrestoreDisembark.Result prestore(JsonNode strength, Arrival arrival) {
        return PrestoreDisembark.project(PrestoreCodec.decode(strength, arrivalNode(arrival), arrival.context(), prefixNode(arrival.edge().prefix())));
    }

    public static ObjectNode scheduleNode(Schedule value) {
        ObjectNode n = inputNode("native_current_unit_new_date_schedule_inputs_12004", value.status(), value.reason()); subject(n, value.army(), value.carmy());
        put(n, "vector_header_count_i32", value.vectorCount()); put(n, "subject_stored_id_occurrence_count_i32", value.occurrences());
        put(n, "vector_data_present", value.dataPresent()); put(n, "subject_stored_id_positions", value.positions()); SCHEDULE_FALSE.forEach(key -> n.put(key, false)); return n;
    }
    public static ObjectNode entryNode(Entry value) {
        ObjectNode n = inputNode("native_current_unit_new_date_callback_entry_inputs_12004", value.status(), value.reason()); subject(n, value.army(), value.carmy()); put(n, "unit_route_count_i32", value.routeCount()); return n;
    }
    public static ObjectNode targetNode(TargetInput value) {
        ObjectNode n = ArmyJson.empty().put("source", TARGET_SOURCE).put("input_basis", TARGET_BASIS).put("status", value.status().name().toLowerCase(java.util.Locale.ROOT));
        put(n, "unavailable_reason", value.reason()); n.put("current_target_inputs_ready", value.ready()); put(n, "subject_army_id", value.army()); put(n, "subject_carmy_id", value.carmy());
        put(n, "current_province_id", value.current()); put(n, "first_route_target_province_id", value.target()); put(n, "route_source_count", value.routeCount());
        n.set("target_contributors_v1", LandContextCodec.encodeProvince(value.contributors())); put(n, "subject_matching_occurrence_indices", value.matching()); put(n, "subject_included_occurrence_count", value.includedCount());
        falses(n, "actual_arrival_observed actual_after_arrival_usage_observed full_arrival_supply_transition_ready"); return n;
    }
    public static ObjectNode targetProjectionNode(TargetProjection value) {
        TargetInput input = value.input(); RouteContext context = value.context(); ProvinceContributors nested = input == null ? null : input.contributors();
        boolean ready = input != null && input.ready(), witness = nested != null && nested.contributorsReady();
        boolean contextReady = input != null && context != null && Objects.equals(context.currentProvinceId(), input.current()) && context.routeProvinceIds() != null
                && (input.target() != null ? !context.routeProvinceIds().isEmpty() : input.status() == TargetStatus.NO_COMMITTED_TARGET);
        ObjectNode n = ArmyJson.empty().put("schema_version", 1).put("source", "current_first_route_target_supply_contributors_observation").put("input_basis", TARGET_BASIS)
                .put("status", input == null ? "unavailable" : input.status().name().toLowerCase(java.util.Locale.ROOT)).put("ready", ready).put("current_target_inputs_ready", ready)
                .put("same_frame_army_context_ready", contextReady).put("only_current_target_inputs", true);
        var missing = n.putArray("missing_inputs"); if (!(ready || input != null && input.status() == TargetStatus.NO_COMMITTED_TARGET)) missing.add(input == null ? Key.CURRENT_FIRST_ROUTE_TARGET_SUPPLY_CONTRIBUTORS_V1.wire() : input.reason());
        n.set("observed_inputs", input == null ? NullNode.getInstance() : targetNode(input)); n.put("target_current_usage_ready", nested != null && nested.currentUsageReady());
        put(n, "target_native_supply_limit_soldiers", nested == null ? null : nested.nativeSupplyLimitSoldiers()); put(n, "target_native_supply_usage_soldiers", nested == null ? null : nested.nativeSupplyUsageSoldiers());
        n.put("subject_presence_witness_ready", witness).put("subject_presence_witness", !witness ? "unavailable" : input.includedCount() != null && input.includedCount() > 0 ? "observed_present" : "observed_absent");
        falses(n, "actual_arrival_observed actual_after_arrival_usage_observed full_arrival_supply_transition_ready"); return n;
    }
    public static ObjectNode entryProjectionNode(EntryProjection value) {
        ObjectNode n = projection("source_conditional_unit_new_date_entry_normalization_12004", "first_selected_unit_new_date_entry_prefix",
                "observed_schedule_receiver_state_and_route_count_held_at_first_selected_entry", "prefix_input_ready", value.ready(), value.reason());
        subject(n, value.entry() == null ? null : value.entry().army(), value.entry() == null ? null : value.entry().carmy());
        put(n, "unit_native_170_raw", value.rawState()); put(n, "unit_route_count_i32", value.entry() == null ? null : value.entry().routeCount());
        put(n, "subject_stored_id_positions", value.schedule() == null ? null : value.schedule().positions()); put(n, "scheduled_by_observed_stored_ids", value.scheduled());
        put(n, "conditional_unit_170_raw_after_next_new_date_entry_prefix", value.resultingState()); put(n, "conditional_first_entry_prefix_would_write", value.wouldWrite()); clock(n, value.clock());
        falses(n, "actual_unit_new_date_callback_observed actual_movement_or_arrival_observed actual_future_frame_observed earlier_stage_outputs_reconstructed repeated_full_callback_effects_reconstructed full_daily_supply_transition_ready full_monthly_ready"); return n;
    }
    public static ObjectNode prefixNode(Prefix value) {
        ObjectNode n = projection("source_conditional_unit_next_movement_prefix_12004", "first_selected_unit_new_date_after_add168_before_edge_cost",
                "observed_schedule_receiver_and_post_entry_state_reference_route_weight_and_rate_held_at_movement_gate", "movement_prefix_input_ready", value.ready(), value.reason());
        ObjectNode entry = entryProjectionNode(value.entry()); copy(n, entry, "subject_army_id_u32 subject_carmy_id_u32 subject_stored_id_positions scheduled_by_observed_stored_ids unit_route_count_i32 conditional_unit_170_raw_after_next_new_date_entry_prefix");
        put(n, "unit_native_178_raw_reference", value.rawReference()); CurrentMovement m = value.movement().orElse(null);
        put(n, "accumulated_movement_weight_raw", m == null ? null : m.accumulatedWeight()); put(n, "cached_edge_speed_raw", m == null ? null : m.cachedEdgeSpeed());
        put(n, "current_edge_movement_rate_raw", m == null ? null : m.currentEdgeRate().value()); put(n, "native_army_movement_admission", m == null ? null : m.nativeArmyAdmission().value());
        put(n, "native_army_admission_required_by_conditional_prefix", value.admissionRequired()); n.put("native_army_admission_condition", "same_resolved_carmy_and_admission_operands_held_at_movement_gate_when_required");
        put(n, "movement_gate", value.gate()); put(n, "movement_add_selected", value.addSelected()); n.put("current_edge_rate_demanded_by_conditional_prefix", value.currentRateDemanded());
        put(n, "selected_movement_rate_raw", value.rate()); put(n, "movement_rate_source", value.rateSource()); put(n, "conditional_unit_168_raw_after_next_new_date_movement_prefix", value.resultingWeight());
        for (String key : CLOCK) n.set(key, entry.get(key));
        falses(n, "actual_unit_new_date_callback_observed actual_movement_or_arrival_observed actual_future_frame_observed earlier_stage_outputs_reconstructed intervening_empty_route_handler_reconstructed route_consumption_or_arrival_reconstructed repeated_full_callback_effects_reconstructed full_daily_supply_transition_ready full_monthly_ready"); return n;
    }
    public static ObjectNode edgeNode(Edge value) {
        ObjectNode n = projection("source_conditional_unit_next_first_edge_selection_12004", "first_selected_unit_new_date_after_add168_before_arrival_subtraction",
                "observed_schedule_receiver_route_and_post_entry_movement_operands_cost_context_provider_held_at_first_edge_selection", "first_edge_selection_input_ready", value.ready(), value.reason());
        copy(n, prefixNode(value.prefix()), "subject_army_id_u32 subject_carmy_id_u32 subject_stored_id_positions scheduled_by_observed_stored_ids unit_route_count_i32 movement_add_selected");
        put(n, "selection_bypass", value.bypass()); put(n, "conditional_post_add_unit_168_raw", value.prefix().resultingWeight()); put(n, "first_route_edge_weight_cost_raw", value.cost());
        put(n, "first_edge_arrival_provider_byte_e_u8", value.provider()); put(n, "provider_byte_demanded_by_conditional_first_edge_selection", value.providerDemanded()); put(n, "conditional_first_edge_arrival_branch_selected", value.selected());
        CurrentMovement m = value.prefix().movement().orElse(null); n.set("current_remaining_duration_days_existing", CurrentMovementCodec.fixedNode(m == null ? null : m.remainingDuration()));
        falses(n, "actual_future_frame_observed actual_first_edge_selection_observed actual_first_edge_arrival_observed post_selection_subtraction_reconstructed route_consumption_reconstructed clamp_reconstructed repeated_callback_effects_reconstructed full_unit_new_date_callback_ready native_action_executed earlier_stage_outputs_reconstructed intervening_empty_route_handler_reconstructed full_daily_supply_transition_ready full_monthly_ready"); return n;
    }
    public static ObjectNode arrivalNode(Arrival value) {
        ObjectNode n = projection("source_conditional_unit_next_arrival_transition_12004", "first_selected_unit_new_date_route_pop_and_first_unit20_assignment_24aec82",
                "observed_schedule_receiver_post_entry_operands_original_route_current_and_target_province_type_held_with_normal_prestore_callback_returns", "arrival_transition_input_ready", value.ready(), value.reason());
        copy(n, prefixNode(value.edge().prefix()), "subject_army_id_u32 subject_carmy_id_u32 subject_stored_id_positions scheduled_by_observed_stored_ids");
        copy(n, edgeNode(value.edge()), "conditional_first_edge_arrival_branch_selected selection_bypass conditional_post_add_unit_168_raw first_route_edge_weight_cost_raw current_remaining_duration_days_existing");
        RouteContext context = value.context(); put(n, "current_province_id_existing", context == null ? null : context.currentProvinceId()); put(n, "current_route_province_ids_existing", context == null ? null : context.routeProvinceIds());
        put(n, "current_route_read_status_existing", context == null ? null : context.routeReadStatus()); put(n, "current_route_source_count_existing", context == null ? null : context.routeSourceCount());
        put(n, "first_route_target_province_type_tag_u32", value.targetType()); put(n, "target_type_tag_demanded_by_conditional_arrival", value.tagDemanded()); put(n, "conditional_route_pop_selected", value.edge().selected());
        put(n, "conditional_unit_168_raw_after_arrival_subtraction", value.residual()); put(n, "conditional_consumed_first_route_province_id", value.consumed()); put(n, "conditional_route_province_ids_after_first_pop", value.remaining());
        put(n, "conditional_unit_route_count_i32_after_first_pop", value.remainingCount()); put(n, "conditional_first_province_assignment_selected", value.write()); put(n, "conditional_current_province_id_after_first_assignment", value.nextProvince());
        n.put("prestore_callback_normal_returns_condition", "reached_24e23e0_c46100_2479780_return_normally"); CurrentMovement m = value.edge().prefix().movement().orElse(null);
        JsonNode timeline = m == null ? null : CurrentMovementCodec.node(m).get("committed_route_timeline"); n.set("current_committed_route_timeline_existing", timeline == null ? NullNode.getInstance() : timeline);
        falses(n, "actual_future_frame_observed actual_arrival_transition_observed final_helper_current_province_reconstructed unit30_or_unit160_reconstructed post_helper_state_or_progress_reconstructed clamp_reconstructed repeated_callback_effects_reconstructed full_unit_new_date_callback_ready native_action_executed earlier_stage_outputs_reconstructed intervening_empty_route_handler_reconstructed battle_contact_siege_effects_reconstructed full_daily_supply_transition_ready full_monthly_ready"); return n;
    }

    /** Uses the saved query-start Snapshot only; no refreshed/post-mutation frame can fill old operands. */
    public static Contexts contexts(ArmyStrengthsPipeline.Input input) {
        ObjectNode snapshot = ArmyJson.parse(input.snapshot().original().bytes());
        boolean same = input.original().original().request().before().equals(input.snapshot().context().before())
                && input.original().original().request().sessionId().equals(input.snapshot().context().sessionId());
        return contexts(snapshot, same);
    }
    public static Contexts contexts(JsonNode snapshot, boolean sameQueryIdentity) {
        require(snapshot != null && snapshot.isObject(), "original query-start snapshot object required"); List<RouteContext> all = new ArrayList<>(), players = new ArrayList<>();
        for (JsonNode n : requiredArray(snapshot.get("player_armies"))) { RouteContext c = context(n); all.add(c); if (sameQueryIdentity) players.add(c); }
        for (JsonNode war : requiredArray(snapshot.get("active_wars"))) for (String key : List.of("allied_armies", "enemy_armies"))
            for (JsonNode n : requiredArray(war.get(key))) all.add(context(n));
        return new Contexts(all, players);
    }
    public static RouteContext context(JsonNode node) {
        require(node != null && node.isObject(), "Army context object required"); return new RouteContext(requiredId(node, "army_id"), i32(node.get("current_province_id")), text(node.get("route_read_status")), i32(node.get("route_source_count")), integers(node.get("route_province_ids")));
    }
    private static <T> Joined<T> join(ArmyStrengthsPipeline.Input input, ArmyStrengths.Row row, T value) {
        var frame = input.original().original().request().before().frame();
        return new Joined<>(row.core().army().value(), new Provenance(frame.snapshotId(), frame.revision(), frame.identity().nativeRevision()), value);
    }
    private static <T> T find(List<Joined<T>> rows, int id) {
        List<Joined<T>> matches = rows.stream().filter(r -> r.army() == id).toList(); require(matches.size() == 1, "earlier projection must bind exactly one selected public Army"); return matches.getFirst().projection();
    }
    private static <T> RawJson rows(List<Joined<T>> values, Function<T,ObjectNode> encoder, boolean provenance) {
        ArrayNode array = ArmyJson.empty().arrayNode(); for (Joined<T> value : values) { ObjectNode row = array.addObject().put("army_id", value.army());
            if (provenance) row.putObject("source_provenance").put("snapshot_id", value.provenance().snapshotId()).put("revision", value.provenance().revision()).put("native_revision", value.provenance().nativeRevision());
            row.set("projection", encoder.apply(value.projection())); } return raw(array);
    }
    private static Integer nativeId(ArmyStrengths.Core row) { return row.nativeArmy() instanceof Present<FullId> p ? p.value().value() : null; }
    private static List<Rule> targetRules(String prefix) { return ArmyStrengthsSupply.provinceRules().stream().map(rule -> new Rule(prefix + rule.exactPath(), rule.domain())).toList(); }
    private static RawJson publicRows(RawJson nativeRows, String signedFields) {
        List<Rule> rules = new ArrayList<>(); rules.add(new Rule("/*/source_provenance/revision", Domain.UNSIGNED_64)); rules.add(new Rule("/*/source_provenance/native_revision", Domain.UNSIGNED_64));
        for (String field : signedFields.split(" ")) rules.add(new Rule("/*/projection/" + field, Domain.SIGNED_64)); return ArmyStrengthsPublicNumbers.encode(nativeRows, rules);
    }
    private static <T> ArmyTypes.Field<T> normalized(ArmyTypes.Field<RawJson> input, Function<JsonNode,T> decoder) {
        T value = decoder.apply(input instanceof Present<RawJson> p ? ArmyStrengthsCodec.parseValue(p.value()) : NullNode.getInstance()); return value == null ? new NullValue<>() : new Present<>(value);
    }
    private static <T> JsonNode fieldNode(ArmyTypes.Field<T> value, Function<T,ObjectNode> encoder) { return value instanceof Present<T> p ? encoder.apply(p.value()) : NullNode.getInstance(); }
    private static RawJson raw(JsonNode n) { return new RawJson(ArmyJson.bytes(n)); }
    private static ObjectNode inputNode(String source, Availability status, String reason) {
        ObjectNode n = ArmyJson.empty().put("schema_version", 1).put("source", source).put("capture_boundary", BOUNDARY).put("status", status.name().toLowerCase(java.util.Locale.ROOT)).put("ready", status == Availability.AVAILABLE); put(n, "unavailable_reason", reason); return n;
    }
    private static ObjectNode projection(String source, String boundary, String condition, String readyKey, boolean ready, String reason) {
        ObjectNode n = ArmyJson.empty().put("schema_version", 1).put("source", source).put("projection_boundary", boundary).put("condition", condition).put(readyKey, ready); put(n, "unavailable_reason", reason); return n;
    }
    private static void clock(ObjectNode n, SourceNextFrame clock) {
        n.put("source_derived_full_cdate64_ready", clock != null && clock.fullCdate64Ready()); put(n, CLOCK.get(1), clock == null ? null : clock.nextDateRawI32());
        put(n, CLOCK.get(2), clock == null ? null : clock.values().nextNativeDayIndexRawI32()); put(n, CLOCK.get(3), clock == null ? null : clock.nextDateStorageRaw64());
        put(n, CLOCK.get(4), clock instanceof SourceNextFrame.Extended23 c ? c.nextCalendarDayU8() : null); put(n, CLOCK.get(5), clock instanceof SourceNextFrame.Extended23 c ? c.nextCalendarMonthU8() : null);
    }
    private static void identity(JsonNode n, String source) { require(Integer.valueOf(1).equals(i32(n.get("schema_version"))), "exact integer schema version 1 required"); eq(n.get("source"), source); eq(n.get("capture_boundary"), BOUNDARY); }
    private static Availability availability(JsonNode node) {
        String status = StrictJson.text(node.get("status")); boolean ready = bool(node.get("ready")); String reason = text(node.get("unavailable_reason"));
        require((status.equals("available") || status.equals("unavailable")) && ready == status.equals("available") && (ready ? reason == null : reason != null), "native input status/readiness/reason differs"); return ready ? Availability.AVAILABLE : Availability.UNAVAILABLE;
    }
    private static void subject(ObjectNode n, Long army, Long carmy) { put(n, "subject_army_id_u32", army); put(n, "subject_carmy_id_u32", carmy); }
    private static void expected(Long value, Integer expected) { require(expected == null || value == null || value == Integer.toUnsignedLong(expected), "raw DWORD subject differs from same-query row"); }
    private static void exact(JsonNode node, String keys) { StrictJson.object(node, Set.of(keys.split(" "))); }
    private static void eq(JsonNode node, String expected) { require(expected.equals(StrictJson.text(node)), "native input source/basis differs"); }
    private static void no(JsonNode node) { require(node != null && node.isBoolean() && !node.booleanValue(), "current observations cannot claim future/callback effects"); }
    private static boolean absent(JsonNode node) { return node == null || node.isNull(); }
    private static Integer i32(JsonNode n) { return absent(n) ? null : (int) StrictJson.integer(n, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static int requiredId(JsonNode n, String key) { return (int) StrictJson.integer(n.get(key), 0, Integer.MAX_VALUE); }
    private static Long u32(JsonNode n) { return absent(n) ? null : StrictJson.integer(n, 0, 0xffff_ffffL); }
    private static String text(JsonNode n) { if (absent(n)) return null; String value = StrictJson.text(n); require(!value.isEmpty(), "nonempty text or null required"); return value; }
    private static boolean bool(JsonNode n) { require(n != null && n.isBoolean(), "exact boolean required"); return n.booleanValue(); }
    private static Boolean nullableBool(JsonNode n) { return absent(n) ? null : bool(n); }
    private static List<Integer> integers(JsonNode n) { if (absent(n)) return null; List<Integer> result = new ArrayList<>(); for (JsonNode item : requiredArray(n)) result.add((int) StrictJson.integer(item, Integer.MIN_VALUE, Integer.MAX_VALUE)); return List.copyOf(result); }
    private static ArrayNode requiredArray(JsonNode n) { require(n != null && n.isArray(), "native ordered array required"); return (ArrayNode) n; }
    private static String fallback(String value, String other) { return value == null || value.isEmpty() ? other : value; }
    private static void copy(ObjectNode target, ObjectNode source, String names) { for (String key : names.split(" ")) target.set(key, source.get(key)); }
    private static void falses(ObjectNode n, String fields) { for (String key : fields.split(" ")) n.put(key, false); }
    private static void put(ObjectNode n, String key, Integer value) { if (value == null) n.putNull(key); else n.put(key, value); }
    private static void put(ObjectNode n, String key, Long value) { if (value == null) n.putNull(key); else n.put(key, value); }
    private static void put(ObjectNode n, String key, Boolean value) { if (value == null) n.putNull(key); else n.put(key, value); }
    private static void put(ObjectNode n, String key, String value) { if (value == null) n.putNull(key); else n.put(key, value); }
    private static void put(ObjectNode n, String key, List<Integer> value) { if (value == null) n.putNull(key); else { var array = n.putArray(key); value.forEach(array::add); } }
}
