package org.xar.ck3.control.wave2.military.losssequence;

import static org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorCodec;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.Coverage;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.DataRecord;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.DataSnapshot;
import org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh.PhysicalChunk;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.LossSequenceSeed;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossPolicy;

/** Strict declared SDK projection and original loss-sequence wire format. */
public final class LossSequenceCodec {
    public static final int MAX_BYTES = 65_536;
    public enum InputBasis { EXPLICIT_READONLY_BUDGETS, DERIVED_BUDGET_AND_LOSS_SUBSYSTEM }
    private LossSequenceCodec() {}

    public static Input decode(byte[] raw) { return decodeArmyProjection(StrictJson.parse(raw, MAX_BYTES)); }
    public static Input decodeArmyProjection(JsonNode node) { return decodeArmyProjection(node, false, 0); }

    /** Replaces only supply, preserving missing/nullable original siege and raid instead of inventing zeroes. */
    public static Input decodeArmyProjectionWithSupplyBudget(JsonNode node, int supplyBudget) {
        object(node, "army row"); object(node.get("loss_application_inputs_v1"), "loss application inputs");
        return decodeArmyProjection(node, true, supplyBudget);
    }

    private static Input decodeArmyProjection(JsonNode node, boolean replaceSupply, int supplyBudget) {
        object(node, "army row");
        JsonNode losses = optionalObject(node.get("loss_application_inputs_v1"), "loss application inputs");
        Integer supply = replaceSupply ? Integer.valueOf(supplyBudget) : integer32(losses, "current_supply_loss_budget");
        Integer siege = integer32(losses, "siege_loss_budget"), raid = integer32(losses, "raid_loss_budget");
        LossSequenceSeed budgets = supply == null || siege == null || raid == null ? null : new LossSequenceSeed(supply, siege, raid);
        JsonNode rawRegiments = node.get("regiment_strengths");
        List<Regiment> regiments = null;
        if (rawRegiments != null && !rawRegiments.isNull()) {
            array(rawRegiments, "regiment strengths"); regiments = new ArrayList<>();
            for (JsonNode row : rawRegiments) {
                object(row, "regiment strength");
                regiments.add(new Regiment(required32(row.get("army_regiment_id")), integer32(row, "current_soldiers"), integer32(row, "maximum_soldiers"),
                        predicate(row, "siege_tier_observable"), integer32(row, "siege_tier"), predicate(row, "native_supply_loss_eligible")));
            }
        }
        List<DataRow> data = new ArrayList<>();
        JsonNode dataRows = node.get("regiment_replenishment_records_v1");
        if (dataRows != null && !dataRows.isNull()) {
            array(dataRows, "DATA snapshots");
            for (JsonNode row : dataRows) data.add(decodeDataProjection(row));
        }
        return new Input(available(node), available(losses), budgets, regiments, data);
    }

    public static DataRow decodeDataProjection(JsonNode row) {
        object(row, "DATA snapshot");
        int regiment = required32(row.get("army_regiment_id"));
        List<DataRecord> records = null; List<RecordMetadata> metadata = null;
        JsonNode raw = row.get("records");
        if (raw != null && !raw.isNull()) {
            array(raw, "DATA records"); records = new ArrayList<>(); metadata = new ArrayList<>();
            for (JsonNode record : raw) {
                object(record, "DATA record");
                records.add(new DataRecord(required32(record.get("record_index")), required32(record.get("persistent_regiment_id")),
                        required32(record.get("chunk_index")), integer32(record, "state_raw"), integer32(record, "current_soldiers"), integer32(record, "maximum_soldiers")));
                metadata.add(new RecordMetadata(available(record), integer32(record, "chunk_army_regiment_id")));
            }
        }
        return new DataRow(new DataSnapshot(regiment, coverage(row), predicate(row, "native_loss_writer_skipped"), records), metadata);
    }

    public static WriterRequest decodeWriterRequest(JsonNode node) {
        object(node, "writer request");
        return new WriterRequest(required32(node.get("army_regiment_id")),
                StrictJson.integer(node.get("writer_quantity_raw"), Long.MIN_VALUE, Long.MAX_VALUE),
                (int) StrictJson.integer(node.get("writer_quantity_scale"), 100_000, 100_000));
    }

    public static ObjectNode writerNode(WriterResult value) {
        ObjectNode node = StrictJson.object();
        if (value.status() == WriterStatus.ARITHMETIC_ERROR) {
            node.put("chunk_writeback_ready", false); strings(node, "missing_inputs", value.missingInputs());
            node.put("native_arithmetic_error", value.arithmeticError()); return node;
        }
        node.put("projection_kind", "conditional_associated_chunk_writeback"); node.put("source_contract_game_version", "1.20.0.3");
        node.put("army_regiment_id", value.regimentId()); node.put("input_basis", "same_frame_native_DATA_and_explicit_writer_request");
        node.put("status", value.ready() ? "available" : "unavailable"); node.put("chunk_writeback_ready", value.ready());
        node.put("actual_loss", false); node.putNull("raised_regiment_current_after"); node.putNull("conditional_raised_regiment_refresh");
        strings(node, "missing_inputs", value.missingInputs()); ArrayNode writes = node.putArray("writes");
        for (Write write : value.writes()) {
            ObjectNode item = writes.addObject(); item.put("pass", write.pass()); item.put("record_index", write.recordIndex());
            item.put("persistent_regiment_id", write.persistentId()); item.put("chunk_index", write.chunkIndex());
            item.put("current_before", write.currentBefore()); item.put("effective_current", write.effectiveCurrent());
            item.put("selected_quantity_raw", write.selectedQuantityRaw()); item.put("current_after", write.currentAfter());
        }
        physical(node.putArray("physical_chunks_after"), value.physicalChunksAfter());
        if (value.ready()) {
            boolean skipped = Boolean.TRUE.equals(value.skipped()); node.put("writer_skipped", skipped); node.put("refresh_requested", !skipped);
            nullable(node, "remaining_writer_quantity_raw", value.remainingQuantityRaw()); nullable(node, "physical_current_delta", value.physicalCurrentDelta());
            if (skipped) {
                ObjectNode refresh = node.putObject("conditional_raised_regiment_refresh");
                refresh.put("projection_kind", "conditional_raised_regiment_refresh"); refresh.put("status", "not_called");
                refresh.put("current_maximum_ready", false); refresh.put("actual_refresh", false); refresh.putArray("missing_inputs");
                refresh.put("reason", "2634880_true_writer_exits_before_refresh");
            } else node.set("conditional_raised_regiment_refresh", ArmySelectorCodec.refreshNode(value.refresh()));
        }
        return node;
    }

    public static ObjectNode sequenceNode(Result value) { return sequenceNode(value, InputBasis.EXPLICIT_READONLY_BUDGETS); }
    public static ObjectNode sequenceNode(Result value, InputBasis basis) {
        ObjectNode node = StrictJson.object();
        node.put("projection_kind", "conditional_four_pass_loss_subsystem"); node.put("source_contract_game_version", "1.20.0.3");
        node.put("status", wire(value.status())); node.put("conditional_sequence_ready", value.ready()); node.put("actual_loss", false);
        node.putNull("actual_post_stage_current"); node.put("input_basis", basis == InputBasis.DERIVED_BUDGET_AND_LOSS_SUBSYSTEM
                ? "derived_budget_and_loss_subsystem" : "one_query_DATA_order_predicates_and_explicit_readonly_budgets");
        node.put("intermediate_state_basis", "derived_writer_and_current_maximum_refresh");
        ArrayNode passes = node.putArray("passes");
        for (Pass pass : value.passes()) {
            ObjectNode item = passes.addObject(); item.put("phase", pass.phase()); item.put("request_budget_soldiers", pass.requestBudget());
            item.put("input_basis", pass.initialStage() ? "observed_initial_stage" : "derived_conditional_stage");
            item.put("native_filter_flags", pass.filterFlags()); ArrayNode requests = item.putArray("requests");
            for (AllocationRequest request : pass.requests()) {
                ObjectNode entry = requests.addObject(); entry.put("army_regiment_id", request.regimentId());
                entry.put("current_soldiers_read", request.currentRead()); entry.put("remaining_budget_before", request.remainingBudgetBefore());
                entry.put("remaining_eligible_before", request.remainingEligibleBefore()); entry.put("multiply_signed32", request.multiplySigned32());
                entry.put("requested_soldiers", request.requestedSoldiers()); entry.put("writer_quantity_raw", request.requestedSoldiers() * AssociatedChunkWriter.SCALE);
                entry.put("writer_quantity_scale", AssociatedChunkWriter.SCALE); entry.set("conditional_chunk_writeback", writerNode(request.writer()));
            }
            item.put("status", wire(pass.status())); nullable(item, "native_eligible_total_soldiers", pass.eligibleTotal());
            item.put("capped_request_budget_soldiers", pass.cappedBudget()); item.put("caller_overflow_residual_soldiers", pass.callerOverflow());
            if (pass.status() != PassStatus.NOT_CALLED) item.put("unallocated_residual_overflow_soldiers", pass.unallocatedOverflow());
            item.put("remaining_request_budget_soldiers", pass.remainingBudget()); nullable(item, "remaining_eligible_soldiers", pass.remainingEligible());
        }
        ArrayNode missing = node.putArray("missing_inputs");
        for (MissingInput input : value.missingInputs()) {
            switch (input) {
                case MissingField field -> missing.add(field.input());
                case MissingStage stage -> {
                    ObjectNode item = missing.addObject(); item.put("phase", stage.phase()); item.put("army_regiment_id", stage.regimentId());
                    strings(item, "inputs", stage.inputs());
                }
            }
        }
        node.putNull("conditional_final_regiment_strengths");
        if (value.finalRegiments() != null) {
            ArrayNode finalRows = node.putArray("conditional_final_regiment_strengths");
            for (FinalRegiment row : value.finalRegiments()) {
                ObjectNode item = finalRows.addObject(); item.put("army_regiment_id", row.regimentId());
                item.put("current_soldiers", row.current()); item.put("maximum_soldiers", row.maximum()); item.put("scale", 1);
            }
        }
        nullable(node, "conditional_final_current_soldiers", value.finalCurrentSoldiers()); node.putNull("conditional_physical_chunks_after");
        if (value.physicalChunksAfter() != null) physical(node.putArray("conditional_physical_chunks_after"), value.physicalChunksAfter());
        node.put("conditional_physical_chunks_ready", value.physicalChunksReady()); nullable(node, "conditional_physical_current_delta", value.physicalCurrentDelta());
        if (value.budgets() != null) {
            LossSequenceSeed budgets = value.budgets(); node.put("supply_budget_soldiers", budgets.currentSupplyLossBudget());
            node.put("siege_budget_soldiers", budgets.siegeLossBudget()); node.put("raid_budget_soldiers", budgets.raidLossBudget());
            node.put("combined_siege_raid_budget_soldiers", budgets.siegeLossBudget() + budgets.raidLossBudget());
        }
        return node;
    }
    public static byte[] project(byte[] raw) { return StrictJson.canonical(sequenceNode(LossSequencePolicy.project(decode(raw))), MAX_BYTES); }

    /** Complete original monthly producer route: real budget kernel feeds the real conditional writer/refresh core. */
    public static ObjectNode monthlyBudgetsNode(JsonNode row) { return monthlyBudgetsNode(row, false); }
    public static ObjectNode monthlyBudgetsNodeForHost(JsonNode row) { return monthlyBudgetsNode(row, true); }
    private static ObjectNode monthlyBudgetsNode(JsonNode row, boolean host) {
        var budgets = MonthlyLossPolicy.constructConditionalMonthlyLossBudgets(input(host, () -> MonthlyLossCodec.decodeArmyProjection(row)));
        ObjectNode result = MonthlyLossCodec.kernelNode(budgets); result.putNull("same_input_conditional_loss_sequence_v1");
        if (budgets.lossSequenceSeed() != null) {
            Result sequence = LossSequencePolicy.projectWithDerivedBudgets(input(host, () -> decodeArmyProjection(row)), budgets.lossSequenceSeed());
            result.set("same_input_conditional_loss_sequence_v1", sequenceNode(sequence, InputBasis.DERIVED_BUDGET_AND_LOSS_SUBSYSTEM));
        }
        return result;
    }
    public static byte[] projectMonthlyBudgets(byte[] raw) {
        return StrictJson.canonical(monthlyBudgetsNode(StrictJson.parse(raw, MAX_BYTES)), MAX_BYTES);
    }


    private static <T> T input(boolean host, java.util.function.Supplier<T> validator) {
        try { return validator.get(); }
        catch (IllegalArgumentException rejected) {
            if (!host || rejected instanceof org.xar.ck3.control.contracts.projection.ProjectionDomainRejection) throw rejected;
            throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection(rejected.getMessage());
        }
    }

    private static void physical(ArrayNode node, List<PhysicalChunk> chunks) {
        for (PhysicalChunk chunk : chunks) {
            ObjectNode item = node.addObject(); item.put("persistent_regiment_id", chunk.persistentId()); item.put("chunk_index", chunk.chunkIndex());
            nullable(item, "current_soldiers", chunk.current()); nullable(item, "maximum_soldiers", chunk.maximum());
        }
    }
    private static boolean available(JsonNode node) {
        if (node == null) return false; JsonNode value = node.get("status");
        if (value == null || value.isNull()) return false;
        StrictJson.require(value.isTextual(), "status must be text"); return value.textValue().equals("available");
    }
    private static Coverage coverage(JsonNode node) {
        JsonNode status = node.get("status");
        if (status == null || status.isNull()) return Coverage.UNAVAILABLE;
        return switch (StrictJson.text(status)) {
            case "available" -> Coverage.AVAILABLE;
            case "partial" -> Coverage.PARTIAL;
            case "unavailable" -> Coverage.UNAVAILABLE;
            default -> throw new IllegalArgumentException("DATA coverage status differs");
        };
    }
    private static JsonNode object(JsonNode node, String name) { StrictJson.require(node != null && node.isObject(), name + " must be object"); return node; }
    private static JsonNode optionalObject(JsonNode node, String name) { return node == null || node.isNull() ? null : object(node, name); }
    private static void array(JsonNode node, String name) { StrictJson.require(node.isArray(), name + " must be ordered array"); }
    private static int required32(JsonNode node) { return (int) StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static Integer integer32(JsonNode node, String key) {
        JsonNode value = node == null ? null : node.get(key); return value == null || value.isNull() ? null : required32(value);
    }
    private static Boolean predicate(JsonNode node, String key) {
        JsonNode value = node == null ? null : node.get(key); if (value == null || value.isNull()) return null;
        StrictJson.require(value.isBoolean(), key + " must be bool or null"); return value.booleanValue();
    }
    private static void strings(ObjectNode node, String key, List<String> values) { ArrayNode array = node.putArray(key); values.forEach(array::add); }
    private static void nullable(ObjectNode node, String key, Integer value) { if (value == null) node.putNull(key); else node.put(key, value.intValue()); }
    private static void nullable(ObjectNode node, String key, Long value) { if (value == null) node.putNull(key); else node.put(key, value.longValue()); }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
}
