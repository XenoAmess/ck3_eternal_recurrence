package org.xar.ck3.control.wave3.military.landcontext;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.wave2.military.landstock.LandStockModel;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteCodec;

/** One strict native boundary for all Land context families and their complete nested DATA dependency. */
public final class LandContextCodec {
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(32).maxNumberLength(24).build()).build());
    private static final Set<String> RATE = keys("source status unavailable_reason current_observation_ready scale province_id subject_army_id subject_carmy_id owner_character_id commander_raw_full_id commander_resolved_full_id commander_used_native_fallback native_land_branch_applicable native_province_component_applicable province_component_raw commander_modifier_1a9_raw loaded_excess_slope_raw loaded_min_loss_raw loaded_max_loss_raw loaded_divisor_floor_raw");
    private static final Set<String> RESUPPLY = keys("source status unavailable_reason current_observation_ready province_id owner_character_id native_land_branch_applicable native_resupply_eligible loaded_gain_raw scale");
    private static final Set<String> PROVINCE = keys("source status unavailable_reason current_usage_ready contributors_ready province_id subject_army_id subject_carmy_id owner_character_id native_province_unit_count native_supply_limit_soldiers native_supply_usage_soldiers soldiers_scale occurrences");
    private static final Set<String> OCCURRENCE = keys("stored_index army_id status unavailable_reason owner_character_id included inclusion_basis native_carmy_id native_eligible_current_soldiers regiments");
    private static final Set<String> REGIMENT = keys("stored_index army_regiment_id status unavailable_reason current_soldiers maximum_soldiers native_supply_loss_eligible replenishment_records_v1");
    private static final Set<String> DATA = keys("army_regiment_id source status ready native_data_record_count unavailable_reason records");
    private static final Set<String> DATA_RECORD = keys("status unavailable_reason record_index persistent_regiment_id chunk_index current_soldiers maximum_soldiers effective_current_soldiers state_raw native_can_replenish native_chunk_can_replenish persistent_monthly_replenishment_fraction_raw persistent_prepared_replenishment_fraction_raw persistent_monthly_replenishment_fraction_scale persistent_prepared_replenishment_fraction_scale");
    private static final Set<String> ROLE = keys("source status army_regiment_id native_carmy_id arrg_army_id_140 character_raw_id_148 resolved_character_id extension_army_id_f4 extension_arrg_id_f8 character_magic_1c resolution_used_fallback native_character_predicate character_extension_present same_ArRg_instance_after unavailable_reason");
    private LandContextCodec() {}

    public static LandContextRow decodeRow(byte[] bytes) { return decodeRow(parse(bytes)); }
    public static FullLandStockInput decodeStockInput(byte[] bytes) { return decodeStockInput(parse(bytes)); }
    public static FullLandStockInput decodeStockInput(JsonNode node) {
        return new FullLandStockInput(decodeRow(node), UpdaterWriteCodec.decode(node), FleetSupplyCodec.decodeRow(node),
                i64(node, "current_supply_raw"), i64(node, "current_supply_capacity_raw"));
    }
    public static LandContextRow decodeRow(JsonNode node) {
        require(node != null && node.isObject(), "strength row must be object");
        // The SDK row is extensible; all three owned families are closed contracts and validated even for unavailable rows.
        return new LandContextRow("available".equals(optionalText(node, "status")), i32(node, "army_id"),
                i32(node, "native_carmy_id"), i64(node, "current_supply_change_monthly_raw"),
                decodeRate(node.get("current_land_supply_rate_inputs_v1")), decodeResupply(node.get("current_land_resupply_v1")),
                decodeProvince(node.get("current_province_supply_contributors_v1")));
    }
    public static LandRateInputs decodeRate(JsonNode node) {
        if (absent(node)) return null;
        exact(node, RATE); source(node, "native_current_province_land_supply_rate_inputs"); scale(node, "scale", 100_000);
        return new LandRateInputs(landStatus(node), reason(node), requiredBool(node, "current_observation_ready"),
                i32(node, "province_id"), i32(node, "subject_army_id"), i32(node, "subject_carmy_id"), i32(node, "owner_character_id"),
                i32(node, "commander_raw_full_id"), i32(node, "commander_resolved_full_id"), bool(node, "commander_used_native_fallback"),
                bool(node, "native_land_branch_applicable"), bool(node, "native_province_component_applicable"),
                i64(node, "province_component_raw"), i64(node, "commander_modifier_1a9_raw"), i64(node, "loaded_excess_slope_raw"),
                i64(node, "loaded_min_loss_raw"), i64(node, "loaded_max_loss_raw"), i64(node, "loaded_divisor_floor_raw"));
    }
    public static LandResupply decodeResupply(JsonNode node) {
        if (absent(node)) return null;
        exact(node, RESUPPLY); source(node, "native_current_province_land_resupply"); scale(node, "scale", 100_000);
        return new LandResupply(landStatus(node), reason(node), requiredBool(node, "current_observation_ready"),
                i32(node, "province_id"), i32(node, "owner_character_id"), bool(node, "native_land_branch_applicable"),
                bool(node, "native_resupply_eligible"), i64(node, "loaded_gain_raw"));
    }
    public static ProvinceContributors decodeProvince(JsonNode node) {
        if (absent(node)) return null;
        exact(node, PROVINCE); source(node, "native_current_province_mode0"); scale(node, "soldiers_scale", 1);
        List<ProvinceContributors.Occurrence> occurrences = new ArrayList<>();
        for (JsonNode item : array(node, "occurrences")) {
            exact(item, OCCURRENCE);
            List<ProvinceContributors.Regiment> regiments = new ArrayList<>();
            for (JsonNode regiment : array(item, "regiments")) {
                exact(regiment, REGIMENT);
                regiments.add(new ProvinceContributors.Regiment(requiredI32(regiment, "stored_index"), requiredI32(regiment, "army_regiment_id"),
                        recordStatus(regiment), reason(regiment), i32(regiment, "current_soldiers"), i32(regiment, "maximum_soldiers"),
                        bool(regiment, "native_supply_loss_eligible"), decodeData(regiment.get("replenishment_records_v1"))));
            }
            String basis = optionalText(item, "inclusion_basis");
            ProvinceContributors.InclusionBasis inclusion = basis == null ? null : switch (basis) {
                case "same_owner" -> ProvinceContributors.InclusionBasis.SAME_OWNER;
                case "native_common_war_side" -> ProvinceContributors.InclusionBasis.NATIVE_COMMON_WAR_SIDE;
                case "native_not_common_war_side" -> ProvinceContributors.InclusionBasis.NATIVE_NOT_COMMON_WAR_SIDE;
                default -> throw invalid("unknown Province inclusion basis");
            };
            occurrences.add(new ProvinceContributors.Occurrence(requiredI32(item, "stored_index"), requiredI32(item, "army_id"),
                    recordStatus(item), reason(item), i32(item, "owner_character_id"), bool(item, "included"), inclusion,
                    i32(item, "native_carmy_id"), i32(item, "native_eligible_current_soldiers"), regiments));
        }
        return new ProvinceContributors(coverage(node), reason(node), requiredBool(node, "current_usage_ready"),
                requiredBool(node, "contributors_ready"), i32(node, "province_id"), i32(node, "subject_army_id"),
                i32(node, "subject_carmy_id"), i32(node, "owner_character_id"), i32(node, "native_province_unit_count"),
                i32(node, "native_supply_limit_soldiers"), i32(node, "native_supply_usage_soldiers"), occurrences);
    }
    public static FullDataModel.Snapshot decodeData(JsonNode node) {
        if (absent(node)) return null;
        Set<String> accepted = new HashSet<>(DATA);
        if (node.has("native_loss_writer_skipped") || node.has("loss_writer_admission_unavailable_reason")) {
            accepted.add("native_loss_writer_skipped"); accepted.add("loss_writer_admission_unavailable_reason");
        }
        if (node.has("native_character_role_v1")) accepted.add("native_character_role_v1");
        exact(node, accepted); source(node, "native_all_data_records");
        FullDataModel.Coverage status = coverage(node);
        require(requiredBool(node, "ready") == (status == FullDataModel.Coverage.AVAILABLE), "native DATA readiness differs");
        List<FullDataModel.DataRecord> records = new ArrayList<>();
        for (JsonNode item : array(node, "records")) {
            Set<String> fields = new HashSet<>(DATA_RECORD);
            if (item.has("chunk_army_regiment_id")) fields.add("chunk_army_regiment_id");
            exact(item, fields); scale(item, "persistent_monthly_replenishment_fraction_scale", 100_000);
            scale(item, "persistent_prepared_replenishment_fraction_scale", 100_000);
            records.add(new FullDataModel.DataRecord(recordStatus(item), reason(item), requiredI32(item, "record_index"),
                    requiredI32(item, "persistent_regiment_id"), requiredI32(item, "chunk_index"), i32(item, "current_soldiers"),
                    i32(item, "maximum_soldiers"), i32(item, "effective_current_soldiers"), i32(item, "state_raw"),
                    bool(item, "native_can_replenish"), bool(item, "native_chunk_can_replenish"),
                    i64(item, "persistent_monthly_replenishment_fraction_raw"), i64(item, "persistent_prepared_replenishment_fraction_raw"),
                    100_000, 100_000, i32(item, "chunk_army_regiment_id")));
        }
        int parent = requiredI32(node, "army_regiment_id");
        FullDataModel.CharacterRole role = node.has("native_character_role_v1") ? decodeRole(node.get("native_character_role_v1")) : null;
        return new FullDataModel.Snapshot(parent, status, i32(node, "native_data_record_count"), reason(node), records,
                bool(node, "native_loss_writer_skipped"), optionalText(node, "loss_writer_admission_unavailable_reason"), role);
    }
    public static FullDataModel.CharacterRole decodeRole(JsonNode node) {
        exact(node, ROLE); source(node, "native_selected_ArRg_character_role_raw");
        Long magic = i64(node, "character_magic_1c");
        return new FullDataModel.CharacterRole(coverage(node), requiredI32(node, "army_regiment_id"), requiredI32(node, "native_carmy_id"),
                i32(node, "arrg_army_id_140"), i32(node, "character_raw_id_148"), i32(node, "resolved_character_id"),
                i32(node, "extension_army_id_f4"), i32(node, "extension_arrg_id_f8"), magic,
                bool(node, "resolution_used_fallback"), bool(node, "native_character_predicate"), bool(node, "character_extension_present"),
                requiredBool(node, "same_ArRg_instance_after"), reason(node));
    }

    public static JsonNode encodeRate(LandRateInputs value) {
        if (value == null) return NullNode.getInstance();
        ObjectNode node = base("native_current_province_land_supply_rate_inputs", value.status(), value.unavailableReason());
        node.put("current_observation_ready", value.currentObservationReady()); node.put("scale", 100_000);
        put(node, "province_id", value.provinceId()); put(node, "subject_army_id", value.subjectArmyId()); put(node, "subject_carmy_id", value.subjectCarmyId());
        put(node, "owner_character_id", value.ownerCharacterId()); put(node, "commander_raw_full_id", value.commanderRawFullId());
        put(node, "commander_resolved_full_id", value.commanderResolvedFullId()); putBool(node, "commander_used_native_fallback", value.commanderUsedNativeFallback());
        putBool(node, "native_land_branch_applicable", value.nativeLandBranchApplicable()); putBool(node, "native_province_component_applicable", value.nativeProvinceComponentApplicable());
        put(node, "province_component_raw", value.provinceComponentRaw()); put(node, "commander_modifier_1a9_raw", value.commanderModifier1a9Raw());
        put(node, "loaded_excess_slope_raw", value.loadedExcessSlopeRaw()); put(node, "loaded_min_loss_raw", value.loadedMinLossRaw());
        put(node, "loaded_max_loss_raw", value.loadedMaxLossRaw()); put(node, "loaded_divisor_floor_raw", value.loadedDivisorFloorRaw());
        return node;
    }
    public static JsonNode encodeResupply(LandResupply value) {
        if (value == null) return NullNode.getInstance();
        ObjectNode node = base("native_current_province_land_resupply", value.status(), value.unavailableReason());
        node.put("current_observation_ready", value.currentObservationReady()); node.put("scale", 100_000);
        put(node, "province_id", value.provinceId()); put(node, "owner_character_id", value.ownerCharacterId());
        putBool(node, "native_land_branch_applicable", value.nativeLandBranchApplicable()); putBool(node, "native_resupply_eligible", value.nativeResupplyEligible());
        put(node, "loaded_gain_raw", value.loadedGainRaw()); return node;
    }
    public static JsonNode encodeProvince(ProvinceContributors value) {
        if (value == null) return NullNode.getInstance();
        ObjectNode node = base("native_current_province_mode0", value.status(), value.unavailableReason());
        node.put("current_usage_ready", value.currentUsageReady()); node.put("contributors_ready", value.contributorsReady()); node.put("soldiers_scale", 1);
        put(node, "province_id", value.provinceId()); put(node, "subject_army_id", value.subjectArmyId()); put(node, "subject_carmy_id", value.subjectCarmyId());
        put(node, "owner_character_id", value.ownerCharacterId()); put(node, "native_province_unit_count", value.nativeProvinceUnitCount());
        put(node, "native_supply_limit_soldiers", value.nativeSupplyLimitSoldiers()); put(node, "native_supply_usage_soldiers", value.nativeSupplyUsageSoldiers());
        ArrayNode occurrences = node.putArray("occurrences");
        for (var occurrence : value.occurrences()) {
            ObjectNode item = JSON.createObjectNode(); item.put("stored_index", occurrence.storedIndex()); item.put("army_id", occurrence.armyId());
            item.put("status", wire(occurrence.status())); item.put("unavailable_reason", occurrence.unavailableReason());
            put(item, "owner_character_id", occurrence.ownerCharacterId()); putBool(item, "included", occurrence.included());
            item.put("inclusion_basis", occurrence.inclusionBasis() == null ? null : wire(occurrence.inclusionBasis()));
            put(item, "native_carmy_id", occurrence.nativeCarmyId()); put(item, "native_eligible_current_soldiers", occurrence.nativeEligibleCurrentSoldiers());
            ArrayNode regiments = item.putArray("regiments");
            for (var regiment : occurrence.regiments()) {
                ObjectNode row = JSON.createObjectNode(); row.put("stored_index", regiment.storedIndex()); row.put("army_regiment_id", regiment.armyRegimentId());
                row.put("status", wire(regiment.status())); row.put("unavailable_reason", regiment.unavailableReason());
                put(row, "current_soldiers", regiment.currentSoldiers()); put(row, "maximum_soldiers", regiment.maximumSoldiers());
                putBool(row, "native_supply_loss_eligible", regiment.nativeSupplyLossEligible()); row.set("replenishment_records_v1", encodeData(regiment.replenishmentRecords()));
                regiments.add(row);
            }
            occurrences.add(item);
        }
        return node;
    }
    public static JsonNode encodeData(FullDataModel.Snapshot value) {
        if (value == null) return NullNode.getInstance();
        ObjectNode node = base("native_all_data_records", value.status(), value.unavailableReason());
        node.put("army_regiment_id", value.armyRegimentId()); node.put("ready", value.status() == FullDataModel.Coverage.AVAILABLE);
        put(node, "native_data_record_count", value.nativeDataRecordCount()); putBool(node, "native_loss_writer_skipped", value.nativeLossWriterSkipped());
        node.put("loss_writer_admission_unavailable_reason", value.lossWriterAdmissionUnavailableReason());
        if (value.characterRole() != null) node.set("native_character_role_v1", encodeRole(value.characterRole()));
        ArrayNode records = node.putArray("records");
        for (var valueRow : value.records()) {
            ObjectNode row = JSON.createObjectNode(); row.put("status", wire(valueRow.status())); row.put("unavailable_reason", valueRow.unavailableReason());
            row.put("record_index", valueRow.recordIndex()); row.put("persistent_regiment_id", valueRow.persistentRegimentId()); row.put("chunk_index", valueRow.chunkIndex());
            put(row, "current_soldiers", valueRow.currentSoldiers()); put(row, "maximum_soldiers", valueRow.maximumSoldiers());
            put(row, "effective_current_soldiers", valueRow.effectiveCurrentSoldiers()); put(row, "state_raw", valueRow.stateRaw());
            putBool(row, "native_can_replenish", valueRow.nativeCanReplenish()); putBool(row, "native_chunk_can_replenish", valueRow.nativeChunkCanReplenish());
            put(row, "persistent_monthly_replenishment_fraction_raw", valueRow.monthlyFractionRaw());
            put(row, "persistent_prepared_replenishment_fraction_raw", valueRow.preparedFractionRaw());
            row.put("persistent_monthly_replenishment_fraction_scale", valueRow.monthlyFractionScale());
            row.put("persistent_prepared_replenishment_fraction_scale", valueRow.preparedFractionScale());
            put(row, "chunk_army_regiment_id", valueRow.chunkArmyRegimentId()); records.add(row);
        }
        return node;
    }
    public static JsonNode encodeRole(FullDataModel.CharacterRole value) {
        ObjectNode node = base("native_selected_ArRg_character_role_raw", value.status(), value.unavailableReason());
        node.put("army_regiment_id", value.armyRegimentId()); node.put("native_carmy_id", value.nativeCarmyId());
        put(node, "arrg_army_id_140", value.arrgArmyId140()); put(node, "character_raw_id_148", value.characterRawId148());
        put(node, "resolved_character_id", value.resolvedCharacterId()); put(node, "extension_army_id_f4", value.extensionArmyIdF4());
        put(node, "extension_arrg_id_f8", value.extensionArrgIdF8()); put(node, "character_magic_1c", value.characterMagic1c());
        putBool(node, "resolution_used_fallback", value.resolutionUsedFallback()); putBool(node, "native_character_predicate", value.nativeCharacterPredicate());
        putBool(node, "character_extension_present", value.characterExtensionPresent()); node.put("same_ArRg_instance_after", value.sameArrgInstanceAfter()); return node;
    }
    public static ObjectNode encodeProjection(FullLandRateProjection value) {
        ObjectNode node = JSON.createObjectNode(); node.put("source", "conditional_same_context_full_land_supply_rate");
        node.put("status", value.ready() ? "available" : "unavailable"); node.put("full_land_rate_ready", value.ready());
        node.put("selected_refill_usage_soldiers", value.selectedRefillUsageSoldiers());
        put(node, "current_observed_total_rate_raw", value.currentObservedTotalRateRaw());
        for (String key : List.of("native_limit_soldiers", "conditional_full_land_rate_raw", "province_component_raw", "excess_loss_raw",
                "gain_component_raw", "local_component_before_adjustment_raw", "local_component_after_adjustment_raw", "commander_divisor_raw", "division_path")) node.putNull(key);
        node.put("scale", 100_000); node.put("actual_after", false); node.put("actual_post_stage_observed", false);
        node.put("full_monthly_supply_change_ready", false); ArrayNode missing = node.putArray("missing_inputs"); value.missingInputs().forEach(missing::add);
        LandStockModel.RateResult result = value.numericResult();
        if (result == null) return node;
        put(node, "native_limit_soldiers", result.limit());
        LandStockModel.Components components = switch (result) {
            case LandStockModel.UnavailableRate ignored -> null;
            case LandStockModel.ComponentsUnavailableRate partial -> partial.components();
            case LandStockModel.AvailableRate available -> available.components();
        };
        if (components != null) {
            node.put("province_component_raw", components.provinceComponent()); node.put("excess_loss_raw", components.excessLoss());
            node.put("gain_component_raw", components.gainComponent()); node.put("local_component_before_adjustment_raw", components.localBeforeAdjustment());
        }
        if (result instanceof LandStockModel.AvailableRate available) {
            node.put("conditional_full_land_rate_raw", available.conditionalRate()); node.put("local_component_after_adjustment_raw", available.localAfterAdjustment());
            put(node, "commander_divisor_raw", available.commanderDivisor()); node.put("division_path", wire(available.divisionPath()));
        }
        return node;
    }

    public static ObjectNode encodeStockProjection(FullLandStockProjection value) {
        ObjectNode node = JSON.createObjectNode();
        node.put("schema_version", 1); node.put("source", "same_input_conditional_source_derived_next_land_stock_supply_budget");
        node.put("status", wire(value.status())); node.put("ready", value.ready());
        ArrayNode missing = node.putArray("missing_inputs"); value.missingInputs().forEach(missing::add);
        put(node, "army_id", value.input().land().armyId()); put(node, "native_carmy_id", value.input().land().nativeCarmyId());
        node.put("condition", "one source-ordered LAND supply callback for this CURRENT captured receiver at "
                + "source-derived next passedDate and the same next GLOBAL GameState low32 date, "
                + "with current Province/owner/commander, native usage/limit, captured capacity "
                + "and all non-date rate/budget inputs unchanged after earlier Unit stages");
        node.put("callback_entry_is_conditional", true);
        put(node, "observed_current_stock_raw", value.input().capturedStockRaw());
        put(node, "observed_current_rate_raw", value.input().land().currentObservedTotalRateRaw());
        put(node, "observed_current_capacity_raw", value.input().capturedCapacityRaw());
        putBool(node, "observed_current_native_fleet_supply_loss_suppressed", value.input().fleet().observedSuppressed());
        put(node, "observed_current_budget_soldiers", value.input().fleet().observedBudget());
        node.set("source_next_date", SourceNextFrameCodec.encode(value.updater().sourceNextDate()));
        node.set("next_admission", UpdaterWriteCodec.encodeAdmission(value.updater().nextAdmission()));
        node.set("conditional_pre_rate_writes", UpdaterWriteCodec.encode(value.updater()).get("conditional_writes"));
        node.put("ordered_pre_rate_writes_ready", value.updater().ready());
        FullLandStockProjection.RateStage rate = value.rate();
        ObjectNode rateNode = node.putObject("conditional_rate"); putBool(rateNode, "would_evaluate", rate.wouldEvaluate());
        rateNode.put("ready", rate.ready()); put(rateNode, "raw", rate.raw());
        rateNode.put("basis", rate.basis() == null ? null : wire(rate.basis()));
        rateNode.put("usage_basis", "captured_current_native_usage_unchanged");
        put(rateNode, "native_usage_soldiers", rate.nativeUsageSoldiers()); put(rateNode, "native_limit_soldiers", rate.nativeLimitSoldiers());
        rateNode.put("conditional_refill_usage_used", false); rateNode.put("captured_target_context_used", false); rateNode.put("native_day_index_used", false);
        rateNode.set("full_land_rate_projection", rate.fullLandRateProjection() == null ? NullNode.getInstance() : encodeProjection(rate.fullLandRateProjection()));
        ArrayNode rateMissing = rateNode.putArray("missing_inputs"); rate.missingInputs().forEach(rateMissing::add);
        FullLandStockProjection.StockStage stock = value.stock();
        ObjectNode stockNode = node.putObject("conditional_post_updater_stock"); stockNode.put("ready", stock.ready());
        put(stockNode, "raw", stock.raw()); put(stockNode, "signed64_add_raw", stock.signed64Add());
        stockNode.put("clamp_branch", stock.clampBranch() == null ? null : wire(stock.clampBranch()));
        stockNode.put("capacity_basis", "captured_current_capacity_unchanged"); stockNode.put("actual_future_capacity_observed", false);
        ArrayNode stockMissing = stockNode.putArray("missing_inputs"); stock.missingInputs().forEach(stockMissing::add);
        FullLandStockProjection.BudgetStage budget = value.budget();
        ObjectNode budgetNode = node.putObject("conditional_budget_getter"); putBool(budgetNode, "would_call", budget.wouldCall());
        budgetNode.put("call_predicate_ready", budget.callPredicateReady()); put(budgetNode, "global_date_raw_i32", budget.globalDateRawI32());
        budgetNode.put("fleet_date_predicate_ready", budget.fleetDatePredicateReady()); putBool(budgetNode, "suppression", budget.suppression());
        budgetNode.put("stock_basis", wire(budget.stockBasis())); put(budgetNode, "stock_raw", budget.stockRaw());
        put(budgetNode, "state_index", budget.stateIndex()); put(budgetNode, "base_fraction_raw", budget.baseFractionRaw());
        put(budgetNode, "effective_fraction_raw", budget.effectiveFractionRaw()); budgetNode.put("ready", budget.ready()); put(budgetNode, "soldiers", budget.soldiers());
        ArrayNode budgetMissing = budgetNode.putArray("missing_inputs"); budget.missingInputs().forEach(budgetMissing::add);
        for (String key : List.of("earlier_stage_effects_reconstructed", "actual_future_date_stage_observed", "actual_future_callback_observed",
                "actual_future_rate_getter_observed", "actual_future_stock_observed", "actual_future_supply_budget_observed", "actual_physical_loss_observed",
                "future_stock_or_strength_ready", "full_daily_supply_transition_ready", "full_monthly_ready")) node.put(key, false);
        return node;
    }

    public static JsonNode parse(byte[] bytes) {
        require(bytes != null && bytes.length > 0 && bytes.length <= 524_288, "Land projection byte budget exceeded or empty");
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
            try (JsonParser parser = JSON.createParser(bytes)) {
                JsonNode node = JSON.readTree(parser); require(node != null && parser.nextToken() == null, "exactly one JSON value required"); return node;
            }
        } catch (IOException failure) { throw new IllegalArgumentException("invalid strict UTF-8/JSON Land projection", failure); }
    }
    private static Set<String> keys(String fields) { return Set.of(fields.split(" ")); }
    private static void exact(JsonNode node, Set<String> expected) {
        Set<String> actual = new HashSet<>();
        if (node != null && node.isObject()) for (var property : node.properties()) actual.add(property.getKey());
        require(node != null && node.isObject() && actual.equals(expected), "native Land family field contract differs");
    }
    private static boolean absent(JsonNode node) { return node == null || node.isNull() || node.isMissingNode(); }
    private static void source(JsonNode node, String expected) { require(expected.equals(optionalText(node, "source")), "native Land source differs"); }
    private static String reason(JsonNode node) { return optionalText(node, "unavailable_reason"); }
    private static String optionalText(JsonNode node, String field) {
        JsonNode value = node.get(field); if (absent(value)) return null;
        require(value.isTextual() && !value.textValue().isEmpty(), field + " must be nonempty string/null"); return value.textValue();
    }
    private static Long i64(JsonNode node, String field) {
        JsonNode value = node.get(field); if (absent(value)) return null;
        require(value.isIntegralNumber() && value.bigIntegerValue().bitLength() <= 63, field + " must be signed64 integer token/null"); return value.longValue();
    }
    private static Integer i32(JsonNode node, String field) {
        Long value = i64(node, field); if (value == null) return null;
        require(value >= Integer.MIN_VALUE && value <= Integer.MAX_VALUE, field + " must be signed32 integer token/null"); return value.intValue();
    }
    private static int requiredI32(JsonNode node, String field) { Integer value = i32(node, field); require(value != null, field + " is required"); return value; }
    private static Boolean bool(JsonNode node, String field) {
        JsonNode value = node.get(field); if (absent(value)) return null;
        require(value.isBoolean(), field + " must be bool/null"); return value.booleanValue();
    }
    private static boolean requiredBool(JsonNode node, String field) { Boolean value = bool(node, field); require(value != null, field + " is required"); return value; }
    private static void scale(JsonNode node, String field, int expected) { require(Integer.valueOf(expected).equals(i32(node, field)), field + " integer scale differs"); }
    private static ArrayNode array(JsonNode node, String field) {
        JsonNode value = node.get(field); require(value != null && value.isArray() && value.size() <= 4096, field + " must be array within 4096 items"); return (ArrayNode) value;
    }
    private static FullDataModel.Coverage coverage(JsonNode node) {
        String value = optionalText(node, "status");
        if ("available".equals(value)) return FullDataModel.Coverage.AVAILABLE;
        if ("partial".equals(value)) return FullDataModel.Coverage.PARTIAL;
        if ("unavailable".equals(value)) return FullDataModel.Coverage.UNAVAILABLE;
        throw invalid("unknown native coverage status");
    }
    private static FullDataModel.RecordStatus recordStatus(JsonNode node) {
        return switch (coverage(node)) {
            case AVAILABLE -> FullDataModel.RecordStatus.AVAILABLE;
            case UNAVAILABLE -> FullDataModel.RecordStatus.UNAVAILABLE;
            case PARTIAL -> throw invalid("partial record is not allowed");
        };
    }
    private static LandRateInputs.Status landStatus(JsonNode node) {
        String value = optionalText(node, "status");
        if ("available".equals(value)) return LandRateInputs.Status.AVAILABLE;
        if ("not_land".equals(value)) return LandRateInputs.Status.NOT_LAND;
        if ("unavailable".equals(value)) return LandRateInputs.Status.UNAVAILABLE;
        throw invalid("unknown native Land status");
    }
    private static ObjectNode base(String source, Enum<?> status, String reason) {
        ObjectNode node = JSON.createObjectNode(); node.put("source", source); node.put("status", wire(status)); node.put("unavailable_reason", reason); return node;
    }
    private static void put(ObjectNode node, String field, Number value) { if (value == null) node.putNull(field); else node.put(field, value.longValue()); }
    private static void putBool(ObjectNode node, String field, Boolean value) { if (value == null) node.putNull(field); else node.put(field, value); }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static void require(boolean condition, String message) { if (!condition) throw invalid(message); }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
