package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.function.BiFunction;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave3.military.landcontext.FullLandStockPolicy;
import org.xar.ck3.control.wave3.military.landcontext.FullLandStockProjection;
import org.xar.ck3.control.wave3.military.landcontext.LandContextCodec;
import org.xar.ck3.control.wave3.military.landcontext.LandResupply;
import org.xar.ck3.control.wave3.military.landcontext.ProvinceContributors;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline.*;

/** Same-query LAND operands and retained actual callback observations. No result grants future execution qualification. */
public final class ArmyStrengthsSupply {
    private ArmyStrengthsSupply() { }
    private static final Set<String> FAMILY = keys("status source identity_basis observer_installed oldest_available_sequence latest_sequence overwritten_events unattributed_capture_failures event_count events");
    private static final Set<String> EVENT = keys("sequence army_id native_carmy_id passed_date_raw64 caller_return_rva before after same_instance_after capture_failure_flags");
    private static final Set<String> VALUES = keys("supply_raw last_supply_update_date_raw64 supply_updated_byte_raw");
    private static final Set<String> PARENT = keys("invocation_token native_thread_id nesting_depth parent_invocation_token callback_caller_return_rva callback_entry_rva receiver_basis");
    private static final BigInteger CALLBACK_RVA = BigInteger.valueOf(0x24E3410);

    /** Full unsigned native domains remain BigInteger; optional fields retain missing versus explicit null. */
    public record SupplyParentInvocation(BigInteger invocationToken, BigInteger nativeThreadId, BigInteger nestingDepth,
            BigInteger parentInvocationToken, BigInteger callbackCallerReturnRva) {
        public SupplyParentInvocation {
            unsigned(invocationToken, 64); unsigned(nativeThreadId, 32); unsigned(nestingDepth, 32);
            optionalUnsigned(parentInvocationToken, 64); optionalUnsigned(callbackCallerReturnRva, 64);
            require(invocationToken.signum() > 0 && nativeThreadId.signum() > 0 && nestingDepth.signum() > 0
                    && (parentInvocationToken == null || parentInvocationToken.signum() > 0)
                    && nestingDepth.equals(BigInteger.ONE) == (parentInvocationToken == null)
                    && !invocationToken.equals(parentInvocationToken), "invalid supply callback parent identity/depth");
        }
    }
    public record Values(Long supplyRaw, BigInteger lastSupplyUpdateDateRaw64, Integer supplyUpdatedByteRaw,
            Field<Integer> provinceId) {
        public Values {
            optionalUnsigned(lastSupplyUpdateDateRaw64, 64); Objects.requireNonNull(provinceId);
            require(supplyUpdatedByteRaw == null || supplyUpdatedByteRaw >= 0 && supplyUpdatedByteRaw <= 255, "callback byte must be uint8/null");
        }
    }
    public record CallbackEvent(BigInteger sequence, int armyId, int nativeCarmyId, BigInteger passedDateRaw64,
            BigInteger callerReturnRva, Values before, Values after, boolean sameInstanceAfter,
            BigInteger captureFailureFlags, Field<SupplyParentInvocation> parentInvocation) {
        public CallbackEvent {
            unsigned(sequence, 64); optionalUnsigned(passedDateRaw64, 64); optionalUnsigned(callerReturnRva, 64);
            unsigned(captureFailureFlags, 32); Objects.requireNonNull(before); Objects.requireNonNull(after);
            Objects.requireNonNull(parentInvocation); require(!(parentInvocation instanceof NullValue<?>), "published parent invocation cannot be null");
        }
    }
    public record CallbackFamily(boolean observerInstalled, BigInteger oldestAvailableSequence, BigInteger latestSequence,
            BigInteger overwrittenEvents, BigInteger unattributedCaptureFailures, List<CallbackEvent> events) {
        public CallbackFamily {
            for (BigInteger value : List.of(oldestAvailableSequence, latestSequence, overwrittenEvents, unattributedCaptureFailures)) unsigned(value, 64);
            events = List.copyOf(events);
        }
    }
    public record EventSummary(CallbackEvent event, boolean stockChangeObserved, BigInteger supplyDeltaRaw,
            BigInteger supplyDrainRaw) {
        public EventSummary {
            Objects.requireNonNull(event);
            require(stockChangeObserved == (event.sameInstanceAfter() && event.before().supplyRaw() != null && event.after().supplyRaw() != null), "callback summary measurement witness differs");
            BigInteger expected = stockChangeObserved ? BigInteger.valueOf(event.after().supplyRaw()).subtract(BigInteger.valueOf(event.before().supplyRaw())) : null;
            require(Objects.equals(expected, supplyDeltaRaw) && Objects.equals(expected == null ? null : expected.negate().max(BigInteger.ZERO), supplyDrainRaw), "callback summary delta/drain differs");
        }
    }
    public record Summary(CallbackFamily family, BigInteger afterSequence, List<EventSummary> events) {
        public Summary {
            require(afterSequence != null && afterSequence.signum() >= 0, "after_sequence must be a nonnegative integer fence"); events = List.copyOf(events);
            List<CallbackEvent> selected = family == null ? List.of() : family.events().stream().filter(event -> event.sequence().compareTo(afterSequence) > 0).toList();
            require(selected.equals(events.stream().map(EventSummary::event).toList()), "summary selection loses callback order or fence");
        }
    }
    public record LandStocks(List<PerArmy<FullLandStockProjection>> values) { public LandStocks { values = List.copyOf(values); } }
    public record Observations(List<PerArmy<Summary>> values) { public Observations { values = List.copyOf(values); } }
    public record GainComponent(int usageSoldiers, int limitSoldiers, boolean ready, Long gainComponentRaw) {
        public GainComponent { require(ready == (gainComponentRaw != null), "land gain readiness differs"); }
    }

    public static void install(ArmyStrengthsFamilies.Registry registry, ArmyStrengthsPipeline pipeline, ExactRef actualJavaBundleSource) {
        add(registry, ArmyStrengthsFamilies.Key.CURRENT_PROVINCE_SUPPLY_CONTRIBUTORS_V1, ProvinceContributors.class,
                (node, context) -> LandContextCodec.decodeProvince(node), LandContextCodec::encodeProvince, provinceRules(), actualJavaBundleSource);
        add(registry, ArmyStrengthsFamilies.Key.CURRENT_LAND_RESUPPLY_V1, LandResupply.class,
                (node, context) -> LandContextCodec.decodeResupply(node), LandContextCodec::encodeResupply, rules(ArmyStrengthsPublicNumbers.Domain.SIGNED_64, "loaded_gain_raw"), actualJavaBundleSource);
        add(registry, ArmyStrengthsFamilies.Key.ACTUAL_SUPPLY_CALLBACK_OBSERVATIONS_V1, CallbackFamily.class,
                (node, context) -> decodeCallbacks(node, context.core().army().value(), context.core().nativeArmy() instanceof Present<FullId> present ? present.value().value() : null),
                ArmyStrengthsSupply::encodeCallbacks, callbackRules(), actualJavaBundleSource);
        pipeline.register(Stage.SOURCE_DERIVED_NEXT_LAND_STOCK_SUPPLY_BUDGET_V1, LandStocks.class, List.of(),
                (input, earlier) -> new LandStocks(input.selected().stream().map(row -> new PerArmy<>(row.core().army(), projectLandStock(earlier.rowJson(row)))).toList()),
                value -> perArmy(value.values(), LandContextCodec::encodeStockProjection, "projection"),
                value -> ArmyStrengthsPublicNumbers.encode(perArmy(value.values(), LandContextCodec::encodeStockProjection, "projection"), prefixed("*/projection/", landStockRules())), actualJavaBundleSource);
        pipeline.register(Stage.ACTUAL_SUPPLY_CALLBACK_OBSERVATION_SUMMARY_V1, Observations.class, List.of(),
                (input, earlier) -> new Observations(input.selected().stream().map(row -> new PerArmy<>(row.core().army(), summarizeRow(earlier.rowJson(row), BigInteger.ZERO))).toList()),
                value -> perArmy(value.values(), ArmyStrengthsSupply::encodeSummary, "observation"),
                value -> ArmyStrengthsPublicNumbers.encode(perArmy(value.values(), ArmyStrengthsSupply::encodeSummary, "observation"), prefixed("*/observation/", summaryRules())), actualJavaBundleSource);
    }
    /** Existing strict native contract and sole LAND/updater/Fleet numeric producer, without a second model. */
    public static FullLandStockProjection projectLandStock(JsonNode sameQueryRow) {
        return FullLandStockPolicy.project(LandContextCodec.decodeStockInput(sameQueryRow));
    }
    /** Original conditional gain component is independent of the complete monthly rate. */
    public static GainComponent projectGain(LandResupply observation, int usageSoldiers, int limitSoldiers) {
        boolean ready = observation != null && observation.currentObservationReady();
        return new GainComponent(usageSoldiers, limitSoldiers, ready,
                ready ? usageSoldiers <= limitSoldiers && Boolean.TRUE.equals(observation.nativeResupplyEligible()) ? observation.loadedGainRaw() : 0L : null);
    }
    public static ObjectNode encodeGain(GainComponent value) {
        var result = ArmyJson.empty().put("source", "conditional_same_context_land_gain_component").put("gain_component_ready", value.ready())
                .put("usage_soldiers", value.usageSoldiers()).put("limit_soldiers", value.limitSoldiers()).put("under_limit", value.usageSoldiers() <= value.limitSoldiers());
        put(result, "gain_component_raw", value.gainComponentRaw());
        return result.put("scale", 100000).put("full_monthly_supply_change_ready", false).put("actual_post_stage_observed", false);
    }
    public static SupplyParentInvocation decodeParentInvocation(JsonNode raw) {
        exact(raw, PARENT); require(integer(get(raw, "callback_entry_rva"), 64, true, false).equals(CALLBACK_RVA)
                && text(get(raw, "receiver_basis")).equals("actual_24E3410_rcx_carmy"), "supply parent invocation source differs");
        return new SupplyParentInvocation(integer(get(raw, "invocation_token"), 64, true, false), integer(get(raw, "native_thread_id"), 32, true, false),
                integer(get(raw, "nesting_depth"), 32, true, false), integer(get(raw, "parent_invocation_token"), 64, true, true),
                integer(get(raw, "callback_caller_return_rva"), 64, true, true));
    }
    public static CallbackFamily decodeCallbacks(JsonNode raw, int currentArmyId, Integer currentNativeCarmyId) {
        if (raw == null || raw.isNull()) return null;
        exact(raw, FAMILY); require(text(get(raw, "status")).equals("available")
                && text(get(raw, "source")).equals("native_natural_supply_callback_entry_return")
                && text(get(raw, "identity_basis")).equals("public_unit_and_native_carmy_full_ids_at_invocation"), "callback provenance differs");
        List<CallbackEvent> events = new ArrayList<>();
        for (JsonNode event : array(get(raw, "events"))) {
            exactOptional(event, EVENT, "supply_parent_invocation_v1");
            int army = i32(get(event, "army_id")), nativeArmy = i32(get(event, "native_carmy_id"));
            require(army == currentArmyId && Integer.valueOf(nativeArmy).equals(currentNativeCarmyId), "callback event differs from both current full Army identities");
            events.add(new CallbackEvent(integer(get(event, "sequence"), 64, true, false), army, nativeArmy,
                    integer(get(event, "passed_date_raw64"), 64, true, true), integer(get(event, "caller_return_rva"), 64, true, true),
                    decodeValues(get(event, "before")), decodeValues(get(event, "after")), bool(get(event, "same_instance_after")),
                    integer(get(event, "capture_failure_flags"), 32, true, false), event.has("supply_parent_invocation_v1")
                            ? new Present<>(decodeParentInvocation(get(event, "supply_parent_invocation_v1"))) : new Missing<>()));
        }
        require(integer(get(raw, "event_count"), 64, true, false).equals(BigInteger.valueOf(events.size())), "callback event_count differs");
        return new CallbackFamily(bool(get(raw, "observer_installed")), integer(get(raw, "oldest_available_sequence"), 64, true, false),
                integer(get(raw, "latest_sequence"), 64, true, false), integer(get(raw, "overwritten_events"), 64, true, false),
                integer(get(raw, "unattributed_capture_failures"), 64, true, false), events);
    }
    private static Values decodeValues(JsonNode raw) {
        exactOptional(raw, VALUES, "province_id");
        Field<Integer> province = !raw.has("province_id") ? new Missing<>() : get(raw, "province_id").isNull() ? new NullValue<>() : new Present<>(i32(get(raw, "province_id")));
        BigInteger supply = integer(get(raw, "supply_raw"), 64, false, true), updated = integer(get(raw, "supply_updated_byte_raw"), 8, true, true);
        return new Values(supply == null ? null : supply.longValueExact(), integer(get(raw, "last_supply_update_date_raw64"), 64, true, true), updated == null ? null : updated.intValueExact(), province);
    }
    public static Summary summarizeRow(JsonNode normalizedArmy, BigInteger afterSequence) {
        require(normalizedArmy != null && normalizedArmy.isObject(), "normalized callback Army must be object");
        JsonNode family = normalizedArmy.get("actual_supply_callback_observations_v1");
        Integer nativeArmy = normalizedArmy.hasNonNull("native_carmy_id") ? i32(get(normalizedArmy, "native_carmy_id")) : null;
        return summarize(decodeCallbacks(family, i32(get(normalizedArmy, "army_id")), nativeArmy), afterSequence);
    }
    public static Summary summarize(CallbackFamily family, BigInteger afterSequence) {
        require(afterSequence != null && afterSequence.signum() >= 0, "after_sequence must be a nonnegative integer fence");
        List<EventSummary> events = new ArrayList<>();
        if (family != null) for (CallbackEvent event : family.events()) if (event.sequence().compareTo(afterSequence) > 0) {
            boolean measured = event.sameInstanceAfter() && event.before().supplyRaw() != null && event.after().supplyRaw() != null;
            BigInteger delta = measured ? BigInteger.valueOf(event.after().supplyRaw()).subtract(BigInteger.valueOf(event.before().supplyRaw())) : null;
            events.add(new EventSummary(event, measured, delta, delta == null ? null : delta.negate().max(BigInteger.ZERO)));
        }
        return new Summary(family, afterSequence, events);
    }
    public static ObjectNode encodeParentInvocation(SupplyParentInvocation value) {
        var result = ArmyJson.empty(); put(result, "invocation_token", value.invocationToken()); put(result, "native_thread_id", value.nativeThreadId());
        put(result, "nesting_depth", value.nestingDepth()); put(result, "parent_invocation_token", value.parentInvocationToken());
        put(result, "callback_caller_return_rva", value.callbackCallerReturnRva()); put(result, "callback_entry_rva", CALLBACK_RVA);
        return result.put("receiver_basis", "actual_24E3410_rcx_carmy");
    }
    public static JsonNode encodeCallbacks(CallbackFamily value) {
        if (value == null) return NullNode.getInstance();
        var result = ArmyJson.empty().put("status", "available").put("source", "native_natural_supply_callback_entry_return")
                .put("identity_basis", "public_unit_and_native_carmy_full_ids_at_invocation"); metadata(result, value); result.put("event_count", value.events().size());
        var events = result.putArray("events");
        for (CallbackEvent valueEvent : value.events()) {
            var event = eventIdentity(valueEvent); event.set("before", encodeValues(valueEvent.before())); event.set("after", encodeValues(valueEvent.after()));
            event.put("same_instance_after", valueEvent.sameInstanceAfter()); put(event, "capture_failure_flags", valueEvent.captureFailureFlags());
            if (valueEvent.parentInvocation() instanceof Present<SupplyParentInvocation> parent) event.set("supply_parent_invocation_v1", encodeParentInvocation(parent.value()));
            events.add(event);
        }
        return result;
    }
    private static ObjectNode encodeValues(Values value) {
        var result = ArmyJson.empty(); put(result, "supply_raw", value.supplyRaw()); put(result, "last_supply_update_date_raw64", value.lastSupplyUpdateDateRaw64());
        put(result, "supply_updated_byte_raw", value.supplyUpdatedByteRaw()); putProvince(result, "province_id", value.provinceId()); return result;
    }
    public static ObjectNode encodeSummary(Summary value) {
        var result = ArmyJson.empty().put("source", "retained_actual_natural_supply_callback_snapshots"); put(result, "after_sequence", value.afterSequence());
        result.put("supply_scale", 100000).put("actual_physical_soldier_loss_observed", false).put("updater_admission_observed", false)
                .put("future_supply_projected", false).put("full_monthly_execution_observed", false);
        result.put("status", value.family() == null ? "unavailable" : "available");
        if (value.family() == null) result.put("reason", "observer_leaf_absent"); else metadata(result, value.family());
        result.put("actual_callback_observed", !value.events().isEmpty()).put("matching_event_count", value.events().size());
        int complete = 0; BigInteger delta = BigInteger.ZERO, drain = BigInteger.ZERO; var events = result.putArray("events");
        for (EventSummary summary : value.events()) {
            CallbackEvent source = summary.event(); var event = eventIdentity(source);
            put(event, "supply_before_raw", source.before().supplyRaw()); put(event, "supply_after_raw", source.after().supplyRaw());
            putProvince(event, "province_before_id", source.before().provinceId()); putProvince(event, "province_after_id", source.after().provinceId());
            put(event, "supply_delta_raw", summary.supplyDeltaRaw()); put(event, "supply_drain_raw", summary.supplyDrainRaw());
            put(event, "last_supply_update_date_before_raw64", source.before().lastSupplyUpdateDateRaw64());
            put(event, "last_supply_update_date_after_raw64", source.after().lastSupplyUpdateDateRaw64());
            put(event, "supply_updated_byte_before_raw", source.before().supplyUpdatedByteRaw()); put(event, "supply_updated_byte_after_raw", source.after().supplyUpdatedByteRaw());
            event.put("same_instance_after", source.sameInstanceAfter()); put(event, "capture_failure_flags", source.captureFailureFlags()); event.put("stock_change_observed", summary.stockChangeObserved());
            events.add(event); if (summary.stockChangeObserved()) { complete++; delta = delta.add(summary.supplyDeltaRaw()); drain = drain.add(summary.supplyDrainRaw()); }
        }
        result.put("complete_supply_event_count", complete).put("partial_supply_event_count", value.events().size() - complete);
        put(result, "sum_observed_supply_delta_raw", complete == 0 ? null : delta); put(result, "sum_observed_supply_drain_raw", complete == 0 ? null : drain);
        result.set("latest_event", events.isEmpty() ? NullNode.getInstance() : events.get(events.size() - 1).deepCopy()); return result;
    }
    private static ObjectNode eventIdentity(CallbackEvent value) {
        var result = ArmyJson.empty(); put(result, "sequence", value.sequence()); result.put("army_id", value.armyId()).put("native_carmy_id", value.nativeCarmyId());
        put(result, "passed_date_raw64", value.passedDateRaw64()); put(result, "caller_return_rva", value.callerReturnRva()); return result;
    }
    private static void metadata(ObjectNode result, CallbackFamily value) {
        result.put("observer_installed", value.observerInstalled()); put(result, "oldest_available_sequence", value.oldestAvailableSequence());
        put(result, "latest_sequence", value.latestSequence()); put(result, "overwritten_events", value.overwrittenEvents()); put(result, "unattributed_capture_failures", value.unattributedCaptureFailures());
    }
    private static <T> void add(ArmyStrengthsFamilies.Registry registry, ArmyStrengthsFamilies.Key key, Class<T> type,
            BiFunction<JsonNode,ArmyStrengths.RowContext,T> decoder, Function<T,JsonNode> encoder, List<ArmyStrengthsPublicNumbers.Rule> publicRules, ExactRef source) {
        registry.register(key, type, (input, context) -> input instanceof Missing<?> ? new Missing<>() : input instanceof NullValue<?> ? new NullValue<>()
                : new Present<>(Objects.requireNonNull(decoder.apply(ArmyStrengthsCodec.parseValue(((Present<RawJson>) input).value()), context))),
                field -> encoded(field, encoder), field -> ArmyStrengthsPublicNumbers.encode(encoded(field, encoder), publicRules), source);
    }
    private static <T> RawJson encoded(Field<T> field, Function<T,JsonNode> encoder) {
        return new RawJson(ArmyJson.bytes(field instanceof Present<T> present ? encoder.apply(present.value()) : NullNode.getInstance()));
    }
    /** Exact native numerical paths for the public decimal64 representation; no guessing from names or magnitude. */
    public static List<ArmyStrengthsPublicNumbers.Rule> provinceRules() {
        return rules(ArmyStrengthsPublicNumbers.Domain.SIGNED_64,
                "occurrences/*/regiments/*/replenishment_records_v1/records/*/persistent_monthly_replenishment_fraction_raw",
                "occurrences/*/regiments/*/replenishment_records_v1/records/*/persistent_prepared_replenishment_fraction_raw");
    }
    public static List<ArmyStrengthsPublicNumbers.Rule> parentInvocationRules() {
        return rules(ArmyStrengthsPublicNumbers.Domain.UNSIGNED_64, "invocation_token", "parent_invocation_token", "callback_caller_return_rva", "callback_entry_rva");
    }
    public static List<ArmyStrengthsPublicNumbers.Rule> callbackRules() {
        var result = new ArrayList<>(rules(ArmyStrengthsPublicNumbers.Domain.UNSIGNED_64, "oldest_available_sequence", "latest_sequence", "overwritten_events", "unattributed_capture_failures", "event_count",
                "events/*/sequence", "events/*/passed_date_raw64", "events/*/caller_return_rva", "events/*/before/last_supply_update_date_raw64", "events/*/after/last_supply_update_date_raw64"));
        result.addAll(rules(ArmyStrengthsPublicNumbers.Domain.SIGNED_64, "events/*/before/supply_raw", "events/*/after/supply_raw"));
        result.addAll(prefixed("events/*/supply_parent_invocation_v1/", parentInvocationRules())); return List.copyOf(result);
    }
    public static List<ArmyStrengthsPublicNumbers.Rule> summaryRules() {
        var result = new ArrayList<>(rules(ArmyStrengthsPublicNumbers.Domain.UNSIGNED_64, "oldest_available_sequence", "latest_sequence", "overwritten_events", "unattributed_capture_failures"));
        result.addAll(rules(ArmyStrengthsPublicNumbers.Domain.INTEGER, "after_sequence", "sum_observed_supply_delta_raw", "sum_observed_supply_drain_raw"));
        for (String prefix : List.of("events/*/", "latest_event/")) {
            result.addAll(prefixed(prefix, rules(ArmyStrengthsPublicNumbers.Domain.UNSIGNED_64, "sequence", "passed_date_raw64", "caller_return_rva", "last_supply_update_date_before_raw64", "last_supply_update_date_after_raw64")));
            result.addAll(prefixed(prefix, rules(ArmyStrengthsPublicNumbers.Domain.SIGNED_64, "supply_before_raw", "supply_after_raw")));
            result.addAll(prefixed(prefix, rules(ArmyStrengthsPublicNumbers.Domain.INTEGER, "supply_delta_raw", "supply_drain_raw")));
        }
        return List.copyOf(result);
    }
    public static List<ArmyStrengthsPublicNumbers.Rule> landStockRules() {
        var result = new ArrayList<>(rules(ArmyStrengthsPublicNumbers.Domain.SIGNED_64, "observed_current_stock_raw", "observed_current_rate_raw", "observed_current_capacity_raw",
                "source_next_date/current_date_storage_raw64", "source_next_date/source_derived_next_date_storage_raw64",
                "conditional_pre_rate_writes/0/observed_value", "conditional_pre_rate_writes/1/observed_value", "conditional_pre_rate_writes/1/conditional_value",
                "conditional_rate/raw", "conditional_post_updater_stock/raw", "conditional_post_updater_stock/signed64_add_raw",
                "conditional_budget_getter/stock_raw", "conditional_budget_getter/base_fraction_raw", "conditional_budget_getter/effective_fraction_raw"));
        result.addAll(prefixed("conditional_rate/full_land_rate_projection/", rules(ArmyStrengthsPublicNumbers.Domain.SIGNED_64,
                "current_observed_total_rate_raw", "conditional_full_land_rate_raw", "province_component_raw", "excess_loss_raw", "gain_component_raw", "local_component_before_adjustment_raw", "commander_divisor_raw")));
        result.addAll(rules(ArmyStrengthsPublicNumbers.Domain.INTEGER, "conditional_rate/full_land_rate_projection/local_component_after_adjustment_raw")); return List.copyOf(result);
    }
    private static List<ArmyStrengthsPublicNumbers.Rule> rules(ArmyStrengthsPublicNumbers.Domain domain, String... paths) {
        return java.util.Arrays.stream(paths).map(path -> new ArmyStrengthsPublicNumbers.Rule("/" + path, domain)).toList();
    }
    private static List<ArmyStrengthsPublicNumbers.Rule> prefixed(String prefix, List<ArmyStrengthsPublicNumbers.Rule> rules) {
        return rules.stream().map(rule -> new ArmyStrengthsPublicNumbers.Rule("/" + prefix + rule.exactPath().substring(1), rule.domain())).toList();
    }
    private static <T> RawJson perArmy(List<PerArmy<T>> values, Function<T,JsonNode> encoder, String field) {
        var result = ArmyJson.empty().arrayNode(); for (PerArmy<T> value : values) result.addObject().put("army_id", value.army().value()).set(field, encoder.apply(value.projection()));
        return new RawJson(ArmyJson.bytes(result));
    }
    private static void putProvince(ObjectNode result, String field, Field<Integer> value) {
        if (value instanceof Present<Integer> present) result.put(field, present.value().intValue()); else if (value instanceof NullValue<?>) result.putNull(field);
    }
    private static void put(ObjectNode result, String field, Number value) {
        if (value == null) result.putNull(field); else if (value instanceof BigInteger integer) result.put(field, integer); else result.put(field, value.longValue());
    }
    private static JsonNode get(JsonNode value, String field) { JsonNode node = value.get(field); require(node != null, "missing supply field: " + field); return node; }
    private static Set<String> keys(String text) { return Set.of(text.split(" ")); }
    private static void exact(JsonNode raw, Set<String> expected) {
        require(raw != null && raw.isObject(), "supply object required"); var actual = new java.util.HashSet<String>(); raw.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(expected), "supply closed field contract differs");
    }
    private static void exactOptional(JsonNode raw, Set<String> base, String optional) {
        var expected = new java.util.HashSet<>(base); if (raw != null && raw.has(optional)) expected.add(optional); exact(raw, expected);
    }
    private static ArrayNode array(JsonNode raw) { require(raw.isArray(), "supply array required"); return (ArrayNode) raw; }
    private static String text(JsonNode raw) { require(raw.isTextual(), "supply text required"); return raw.textValue(); }
    private static boolean bool(JsonNode raw) { require(raw.isBoolean(), "supply bool required"); return raw.booleanValue(); }
    private static int i32(JsonNode raw) { return integer(raw, 32, false, false).intValueExact(); }
    private static BigInteger integer(JsonNode raw, int bits, boolean unsigned, boolean nullable) {
        if (nullable && raw.isNull()) return null; require(raw.isIntegralNumber(), "supply integer token required"); BigInteger value = raw.bigIntegerValue();
        require(value.compareTo(unsigned ? BigInteger.ZERO : BigInteger.ONE.shiftLeft(bits - 1).negate()) >= 0
                && value.compareTo(BigInteger.ONE.shiftLeft(unsigned ? bits : bits - 1)) < 0, "supply integer width differs"); return value;
    }
    private static void optionalUnsigned(BigInteger value, int bits) { if (value != null) unsigned(value, bits); }
    private static void unsigned(BigInteger value, int bits) { require(value != null && value.signum() >= 0 && value.bitLength() <= bits, "supply uint" + bits + " required"); }
    private static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}
