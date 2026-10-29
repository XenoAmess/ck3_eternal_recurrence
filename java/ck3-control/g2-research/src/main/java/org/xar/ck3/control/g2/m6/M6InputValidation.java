package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m6.M6TerminalSourceComposition.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Runtime record validation shared by the real native codecs and lifecycle reducer. */
final class M6InputValidation {
    private M6InputValidation() { }
    private static final Set<String> EXEC = Set.of("sequence", "date_raw", "actor_character_id", "target_character_id",
            "scheme_instance_id", "scheme_instance_generation", "source_branch", "stock_event", "executing_input_observed",
            "exact_scope_join_ready", "phase_result", "message_enqueue_observed", "material_effect_observed", "native_terminal_state_observed");
    private static final Set<String> END = Set.of("sequence", "source_class", "date_raw", "actor_character_id", "target_character_id",
            "scheme_instance_id", "scheme_instance_generation", "input_root_scope_kind", "executing_source_observed", "pre_status",
            "pre_owner", "post_read_succeeded", "post_instance_present", "post_storage_slot_reused", "post_exact_instance_join_ready",
            "post_status_observed", "post_status", "post_owner", "native_terminal_state_observed", "native_terminal_transition_observed",
            "material_effect_observed", "specific_invalidation_reason");
    static void validate(Inputs inputs, Identity identity, ObservationIdentity queried) {
        require(queried.frame().identity().player().equals(BigInteger.valueOf(identity.actorCharacterId())), "Sway query player differs");
        inputs.completion().ifPresent(raw -> {
            JsonNode read = parse(raw); exactIdentity(read, identity, true); queryStamp(read, queried);
            M6SourceProducer.fromRawCompletion(raw.bytes(), identity);
        });
        inputs.execution().ifPresent(raw -> queryStamp(parse(journal(raw, identity.nativeSubject(), true)), queried));
        inputs.termination().ifPresent(raw -> queryStamp(parse(journal(raw, identity.nativeSubject(), false)), queried));
        inputs.opinion().ifPresent(raw -> {
            JsonNode read = parse(raw); actual4(read); textEquals(read, "schema", "xar.ck3.sway-outcome-opinion-v1");
            exactIdentity(read, identity, false); queryStamp(read, queried); bool(read, "available");
            named(read.get("scheme_sway_opinion")); named(read.get("sway_blocker_opinion"));
            if (read.get("target_opinion_of_actor") != null && !read.get("target_opinion_of_actor").isNull()) signed(read, "target_opinion_of_actor");
        });
    }
    static ProjectionJson journal(ProjectionJson raw, NativeSubject identity, boolean execution) {
        JsonNode read = M6TerminalSourceComposition.journal(parse(raw), execution);
        exactIdentity(read, identity, true);
        if (read.has("read_only")) require(bool(read, "read_only"), "Sway journal is read-only");
        if (read.has("material_effect_observed")) require(!bool(read, "material_effect_observed"), "execution journal supplies no material");
        if (execution && read.has("native_terminal_state_observed")) require(!bool(read, "native_terminal_state_observed"), "execution journal supplies no terminal");
        BigInteger previous = BigInteger.ZERO;
        BigInteger earliest = read.has("earliest_sequence") ? u64(read, "earliest_sequence", 0) : BigInteger.ZERO;
        BigInteger latest = read.has("latest_sequence") ? u64(read, "latest_sequence", 0) : StrictJson.UINT64_MAX;
        if (read.has("earliest_sequence") && read.has("latest_sequence")) require((earliest.signum() == 0) == (latest.signum() == 0) && earliest.compareTo(latest) <= 0, "Sway journal bounds differ");
        require(bool(read, "available") || read.get("records").isEmpty(), "unavailable journal has no copied rows");
        for (JsonNode row : read.get("records")) {
            BigInteger sequence = u64(row, "sequence", 1);
            require(sequence.compareTo(previous) > 0 && sequence.compareTo(earliest) >= 0 && sequence.compareTo(latest) <= 0, "Sway journal row order differs");
            exactIdentity(row, identity, true); signed(row, "date_raw");
            if (execution) execution(row); else termination(row);
            previous = sequence;
        }
        if (!execution && read.has("common_native_end")) M6CommonEndSources.normalize(read.get("common_native_end"), read);
        return json(read);
    }
    private static void execution(JsonNode row) {
        String branch = text(row, "source_branch");
        boolean authored = branch.equals(COMPLETE) || branch.equals("authored_sway_invalidated_title_source");
        StrictJson.object(row, authored ? plus(EXEC, "native_invocation") : EXEC);
        require(bool(row, "executing_input_observed") && bool(row, "exact_scope_join_ready")
                && !bool(row, "message_enqueue_observed") && !bool(row, "material_effect_observed")
                && !bool(row, "native_terminal_state_observed"), "Sway executing input flags differ");
        if (authored) {
            require(row.get("stock_event").isNull() && row.get("phase_result").isNull(), "authored toast is not a phase event");
            M6CausalSources.completeInvocation(row.get("native_invocation"), row);
        } else {
            boolean success = branch.equals("hidden_phase_success_source");
            require(success || branch.equals("hidden_phase_failure_source"), "unknown Sway execution source");
            textEquals(row, "stock_event", success ? "sway_outcome.0001" : "sway_outcome.0002");
            textEquals(row, "phase_result", success ? "success" : "failure");
        }
    }
    private static void termination(JsonNode row) {
        boolean invocation = row.has("native_invocation");
        StrictJson.object(row, invocation ? plus(END, "native_invocation", "cause_relation") : END);
        require(Set.of("end_scheme_command_execute", "authored_end_scheme_false_execute", "authored_end_scheme_true_execute").contains(text(row, "source_class")), "unknown native end source");
        for (String field : List.of("executing_source_observed", "post_read_succeeded", "post_instance_present", "post_storage_slot_reused",
                "post_exact_instance_join_ready", "post_status_observed", "native_terminal_state_observed", "native_terminal_transition_observed", "material_effect_observed")) bool(row, field);
        require(bool(row, "executing_source_observed") && !bool(row, "material_effect_observed") && row.get("specific_invalidation_reason").isNull(), "native end reason or material was invented");
        integer(row, "input_root_scope_kind", 0, 65535); signed(row, "pre_status"); integer(row, "pre_owner", 0, 0xffff_ffffL);
        for (String field : List.of("post_status", "post_owner")) {
            if (bool(row, "post_status_observed")) integer(row, field, field.equals("post_status") ? Integer.MIN_VALUE : 0,
                    field.equals("post_status") ? Integer.MAX_VALUE : 0xffff_ffffL);
            else require(row.get(field).isNull(), "unread native end value was filled");
        }
        if (invocation) {
            JsonNode original = M6CausalSources.endInvocation(row.get("native_invocation"), row);
            M6CausalSources.relation(row.get("cause_relation"), row, original);
        }
    }
    static void queryStamp(JsonNode read, ObservationIdentity queried) {
        String revision = read.has("source_snapshot_revision") ? "source_snapshot_revision" : "snapshot_revision";
        String date = read.has("source_date_raw") ? "source_date_raw" : "date_raw";
        require(u64(read, revision, 1).equals(queried.frame().identity().nativeRevision())
                && BigInteger.valueOf(signed(read, date)).equals(queried.frame().identity().dateRaw()), "Sway read crossed its actual query frame");
    }
    static void exactIdentity(JsonNode read, Identity identity, boolean instance) {
        exactIdentity(read, identity.nativeSubject(), instance);
    }
    static void exactIdentity(JsonNode read, NativeSubject identity, boolean instance) {
        require(integer(read, "actor_character_id", 0, 0xffff_fffeL) == identity.actorCharacterId()
                && integer(read, "target_character_id", 0, 0xffff_fffeL) == identity.targetCharacterId(), "Sway actor or target differs");
        if (instance) require(integer(read, "scheme_instance_id", 0, 0xffff_fffeL) == identity.schemeInstanceId()
                && integer(read, "scheme_instance_generation", 0, 255) == identity.schemeInstanceGeneration(), "Sway full instance or generation differs");
    }
    private static Set<String> plus(Set<String> fields, String... extra) {
        Set<String> result = new HashSet<>(fields); result.addAll(List.of(extra)); return Set.copyOf(result);
    }
}

