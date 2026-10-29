package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m6.M6TerminalSourceComposition.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Validate the actual dynamic parent/end relationship independently of material and terminal status. */
final class M6CausalSources {
    private M6CausalSources() { }
    private record DynamicKey(BigInteger session, long thread, BigInteger toast, BigInteger branch) { }
    private static final Set<String> COMPLETE_INVOCATION = Set.of("observer_session_identity", "owner_thread_id", "toast_invocation_id", "branch_source_sequence", "copied_scopes");
    private static final Set<String> END_INVOCATION = Set.of("observer_session_identity", "owner_thread_id", "original_invocation_id", "original_rva",
            "incoming_return_address_observed", "caller_return_rva", "original_forwarded_once", "original_returned", "pre_frame_observed", "pre_date_raw", "post_frame_observed", "post_date_raw");
    private static final Set<String> RELATION = Set.of("source_contract", "source_contract_version", "relationship_observed", "observer_session_identity",
            "owner_thread_id", "branch_source_sequence", "parent_toast_invocation_id", "end_original_invocation_id", "end_original_rva",
            "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation", "native_returns_observed", "native_returns_truncated", "native_return_rvas");

    static JsonNode consume(JsonNode execution, JsonNode termination) {
        if (!bool(execution, "available") || !bool(termination, "available") || bool(execution, "retention_gap") || bool(termination, "retention_gap")) return null;
        actual4(execution); actual4(termination);
        if (!same(execution, termination)) return null;
        Map<DynamicKey, JsonNode> sources = new HashMap<>();
        for (JsonNode row : execution.get("records")) {
            if (!COMPLETE.equals(text(row, "source_branch"))) continue;
            require(same(row, execution), "authored completion record differs from query identity");
            require(row.has("stock_event") && row.get("stock_event").isNull() && row.has("phase_result") && row.get("phase_result").isNull()
                    && bool(row, "executing_input_observed") && bool(row, "exact_scope_join_ready")
                    && !bool(row, "message_enqueue_observed") && !bool(row, "material_effect_observed") && !bool(row, "native_terminal_state_observed"), "authored completion source malformed");
            JsonNode invocation = completeInvocation(row.get("native_invocation"), row);
            require(sources.putIfAbsent(key(invocation, "toast_invocation_id"), row) == null, "duplicate completion dynamic identity");
        }
        JsonNode records = termination.get("records");
        for (int index = records.size() - 1; index >= 0; index--) {
            JsonNode row = records.get(index); if (!row.has("native_invocation")) continue;
            require(same(row, termination), "retained end record differs from query identity");
            JsonNode invocation = endInvocation(row.get("native_invocation"), row), relation = relation(row.get("cause_relation"), row, invocation);
            if (relation == null) continue;
            JsonNode parent = sources.get(key(relation, "parent_toast_invocation_id"));
            if (parent == null || !same(parent, row) || !terminalTransition(row, row) || !bool(invocation, "post_frame_observed")
                    || !exactIntegerEquals(invocation.get("pre_date_raw"), parent.get("date_raw"))
                    || !exactIntegerEquals(invocation.get("post_date_raw"), invocation.get("pre_date_raw"))) continue;
            ObjectNode result = StrictJson.object(); result.put("schema", "xar.ck3.sway-end-causal-observation.12004.v1");
            for (String field : IDS) result.set(field, row.get(field));
            result.put("cause_key", COMPLETE); result.put("terminal_cause_observed", true); result.put("native_status_key", "terminated_attributed");
            result.put("native_status_raw", 1); result.put("native_terminal_transition_observed", true); result.put("material_effect_observed", false);
            for (String field : List.of("observer_session_identity", "owner_thread_id", "branch_source_sequence", "parent_toast_invocation_id", "end_original_invocation_id")) result.set(field, relation.get(field));
            result.set("execution_record", parent); result.set("termination_record", row); return result;
        }
        return null;
    }

    static JsonNode completeInvocation(JsonNode invocation, JsonNode record) {
        StrictJson.object(invocation, COMPLETE_INVOCATION); u64(invocation, "observer_session_identity", 1); integer(invocation, "owner_thread_id", 1, 0xffff_ffffL);
        u64(invocation, "toast_invocation_id", 1); u64(invocation, "branch_source_sequence", 1);
        require(exactIntegerEquals(invocation.get("branch_source_sequence"), record.get("sequence")), "authored branch sequence differs");
        JsonNode scopes = invocation.get("copied_scopes"); StrictJson.object(scopes, Set.of("root", "owner", "target", "scheme"));
        for (String name : List.of("root", "owner", "target", "scheme")) {
            JsonNode token = scopes.get(name); StrictJson.object(token, Set.of("type", "subtype", "reserved", "payload"));
            integer(token, "subtype", 0, 65535); integer(token, "reserved", 0, 0xffff_ffffL);
            long expected = integer(record, name.equals("target") ? "target_character_id" : name.equals("scheme") ? "scheme_instance_id" : "actor_character_id", 0, 0xffff_ffffL);
            require(integer(token, "type", 0, 65535) == (name.equals("scheme") ? 9 : 4)
                    && u64(token, "payload", 0).and(BigInteger.valueOf(0xffff_ffffL)).longValueExact() == expected, "copied source scope differs from full identity");
        }
        return invocation;
    }

    static JsonNode endInvocation(JsonNode invocation, JsonNode record) {
        StrictJson.object(invocation, END_INVOCATION); u64(invocation, "observer_session_identity", 1); integer(invocation, "owner_thread_id", 1, 0xffff_ffffL);
        u64(invocation, "original_invocation_id", 1);
        long expected = switch (text(record, "source_class")) {
            case "end_scheme_command_execute" -> 0x299c320L;
            case "authored_end_scheme_false_execute" -> 0x2d11b30L;
            case "authored_end_scheme_true_execute" -> 0x2d11ad0L;
            default -> -1L;
        };
        require(expected >= 0 && u64(invocation, "original_rva", 0).equals(BigInteger.valueOf(expected)), "native original end source differs");
        BigInteger caller = u64(invocation, "caller_return_rva", 0);
        for (String flag : List.of("incoming_return_address_observed", "original_forwarded_once", "original_returned", "pre_frame_observed", "post_frame_observed")) bool(invocation, flag);
        require(bool(invocation, "original_forwarded_once") && bool(invocation, "original_returned") && bool(invocation, "pre_frame_observed")
                && exactIntegerEquals(invocation.get("pre_date_raw"), record.get("date_raw"))
                && (bool(invocation, "incoming_return_address_observed") || caller.signum() == 0), "native original return contract differs");
        for (String prefix : List.of("pre", "post")) {
            if (bool(invocation, prefix + "_frame_observed")) signed(invocation, prefix + "_date_raw");
            else require(invocation.get(prefix + "_date_raw").isNull(), "unobserved end date was filled");
        }
        return invocation;
    }

    static JsonNode relation(JsonNode relation, JsonNode record, JsonNode invocation) {
        if (relation == null || relation.isNull()) return null;
        StrictJson.object(relation, RELATION); textEquals(relation, "source_contract", "sway_child_end_causal_path_12004_v1");
        require(integer(relation, "source_contract_version", 1, 1) == 1 && bool(relation, "relationship_observed") && bool(relation, "native_returns_observed")
                && !bool(relation, "native_returns_truncated"), "causal relationship contract differs");
        u64(relation, "branch_source_sequence", 1); u64(relation, "parent_toast_invocation_id", 1);
        require(same(relation, record), "causal relationship full identity differs");
        for (String field : List.of("observer_session_identity", "owner_thread_id")) require(exactIntegerEquals(relation.get(field), invocation.get(field)), "causal dynamic session/thread differs");
        require(exactIntegerEquals(relation.get("end_original_invocation_id"), invocation.get("original_invocation_id"))
                && exactIntegerEquals(relation.get("end_original_rva"), invocation.get("original_rva")), "causal original invocation differs");
        require(Set.of("authored_end_scheme_false_execute", "authored_end_scheme_true_execute").contains(text(record, "source_class"))
                && integer(record, "input_root_scope_kind", 0, 65535) == 9 && bool(invocation, "incoming_return_address_observed")
                && u64(invocation, "caller_return_rva", 0).equals(BigInteger.valueOf(0x2d67c04)), "causal native input/caller edge differs");
        JsonNode returns = relation.get("native_return_rvas"); array(returns); require(returns.size() >= 3 && returns.size() <= 32, "bounded causal native return chain required");
        int nearestToast = -1, dispatcher = -1;
        for (int index = 0; index < returns.size(); index++) {
            BigInteger rva = StrictJson.integer(returns.get(index), BigInteger.ZERO, StrictJson.UINT64_MAX);
            if (index == 0) require(rva.equals(BigInteger.valueOf(0x2d67c04)), "causal first edge differs");
            if (nearestToast < 0 && rva.equals(BigInteger.valueOf(0x2cc93cc))) nearestToast = index;
            if (dispatcher < 0 && rva.equals(BigInteger.valueOf(0x3766146))) dispatcher = index;
        }
        require(dispatcher > 0 && nearestToast > dispatcher, "causal relationship crosses nearest Toast barrier"); return relation;
    }

    static boolean terminalTransition(JsonNode row, JsonNode original) {
        if (!exactIntegerEquals(row.get("pre_status"), StrictJson.object().numberNode(0))
                || !exactIntegerEquals(row.get("post_status"), StrictJson.object().numberNode(1))
                || !exactIntegerEquals(row.get("pre_owner"), original.get("actor_character_id"))) return false;
        JsonNode owner = row.get("post_owner");
        if (owner == null || !owner.isIntegralNumber() || (!exactIntegerEquals(owner, original.get("actor_character_id"))
                && !owner.bigIntegerValue().equals(BigInteger.valueOf(0xffff_ffffL)))) return false;
        for (String field : List.of("executing_source_observed", "post_read_succeeded", "post_instance_present", "post_exact_instance_join_ready",
                "post_status_observed", "native_terminal_state_observed", "native_terminal_transition_observed")) if (!bool(row, field)) return false;
        return !bool(row, "post_storage_slot_reused");
    }
    private static DynamicKey key(JsonNode value, String toast) {
        return new DynamicKey(u64(value, "observer_session_identity", 1), integer(value, "owner_thread_id", 1, 0xffff_ffffL), u64(value, toast, 1), u64(value, "branch_source_sequence", 1));
    }
}
