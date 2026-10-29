package org.xar.ck3.control.application.planning.warexit;

import static org.xar.ck3.control.application.planning.warexit.WarExitEvidence.*;
import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeInteractionRoles;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.g2.m0.RaiktorExitObservationCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadenceCodec;

/** Original seven-day negative reuse, same-day explicit rejection defer, then the existing 30-day Java policy. */
final class WarExitQueryCadence {
    private static final List<String> SIGNATURE_FIELDS = List.of("war_id", "player_side", "player_is_primary_war_leader",
            "player_relative_war_score", "absolute_war_scores_observable", "attacker_war_score", "defender_war_score",
            "war_score_breakdown", "active_casus_belli_present", "active_casus_belli_identity", "cb_allows_white_peace");
    private static final List<String> WAR_FIELDS = List.of("war_id", "player_side", "player_is_primary_war_leader",
            "primary_opponent_character_id", "player_relative_war_score", "targeted_title_ids");
    private static final String OPTIONAL_ERROR = "war-termination completion snapshot read failed";
    private WarExitQueryCadence() { }

    static Optional<OpportunityJson.Obj> defer(PlanningRequest request, WarExitEvidence.War war, List<ObjectNode> oldestFirst) {
        ObjectNode snapshot = WarExitEvidence.snapshot(request);
        List<ObjectNode> newestFirst = new ArrayList<>(oldestFirst); java.util.Collections.reverse(newestFirst);
        Optional<ObjectNode> negative = negativeReuse(snapshot, war, newestFirst);
        if (negative.isPresent()) return Optional.of(WarExitPolicies.immutable(negative.orElseThrow()));
        Optional<ObjectNode> rejected = optionalFailure(snapshot, war.warId(), newestFirst);
        if (rejected.isPresent()) return Optional.of(WarExitPolicies.immutable(rejected.orElseThrow()));
        return policyDefer(snapshot, war, newestFirst).map(WarExitPolicies::immutable);
    }

    private static Optional<ObjectNode> negativeReuse(ObjectNode snapshot, WarExitEvidence.War war, List<ObjectNode> rows) {
        try {
            if (!trueValue(snapshot.get("paused")) || present(snapshot.get("one_life_terminal_reason"))
                    || snapshot.get("active_event") instanceof ObjectNode || snapshot.get("pending_character_interaction") instanceof ObjectNode
                    || !trueValue(object(snapshot.get("played_character"), "actor").get("alive"))) return Optional.empty();
            ObjectNode actor = object(snapshot.get("played_character"), "actor"); ObjectNode diagnostics = object(snapshot.get("diagnostics"), "diagnostics");
            ArrayNode active = warSignature(snapshot.get("active_wars"), false);
            for (ObjectNode row : rows) {
                JsonNode stepValue = row.get("command"); String step = stepValue != null && stepValue.isTextual() ? stepValue.textValue() : null;
                if (negativeBarrier(step)) return Optional.empty();
                if (!textIs(stepValue, "query-war-termination-options-" + war.warId())) continue;
                if (!trueValue(row.get("ok"))) return Optional.empty();
                ObjectNode result = object(row.get("result"), "negative query result");
                ObjectNode context = object(result.get("termination_query_context"), "negative query context");
                ObjectNode rawOptions = object(result.get("war_termination_options"), "historical native options");
                if (!textIs(result.get("step"), step) || !trueValue(result.get("accepted")) || !textIs(result.get("status"), "available")
                        || !integerIs(context.get("schema_version"), 1) || !equal(context.get("active_war_signature"), active)
                        || !equal(context.get("queried_episode_run_id"), snapshot.get("episode_run_id"))
                        || !equal(context.get("queried_connection_generation"), diagnostics.get("connection_generation"))
                        || !equal(context.get("queried_character_id"), actor.get("character_id"))) return Optional.empty();
                var historical = WarExitEvidence.historicalOptions(rawOptions, war.warId());
                if (!NativeTerminationOptions.normalizeNativePacket(rawOptions, war.warId()).recipientContexts()
                        .reusableForNegativeAssessment()) return Optional.empty();
                ObjectNode signature = negativeSignature(rawOptions);
                if (!equal(context.get("negative_decision_signature"), signature)
                        || !integerIs(signature.get("war_id"), war.warId())
                        || !equal(context.get("queried_war_duration_days"), rawOptions.get("war_duration_days"))) return Optional.empty();
                long date = int32(snapshot.get("date_raw")); long queried = int32(context.get("queried_date_raw")); long elapsed = date - queried;
                long lease = 7L * 24;
                if (war.playerSide() == WarExitEvidence.Side.ATTACKER && war.primaryLeader()
                        && historical.playerSide() == WarExitEvidence.Side.ATTACKER && historical.primaryLeader()
                        && war.score().filter(score -> score == historical.score() && score >= 0 && score < 100).isPresent()
                        && historical.durationDays().filter(days -> days >= 0 && days < 365).isPresent() && historical.cbPresent()
                        && historical.cbKey().filter("claim_cb"::equals).isPresent() && historical.allowsWhitePeace())
                    lease = Math.min(lease, Math.max(1, 365 - historical.durationDays().orElseThrow()) * 24L);
                if (elapsed < 0 || elapsed >= lease || OrdinaryWhitePeacePolicy.historicalOptionsRequireRefresh(
                        WarExitPolicies.immutable(war.original()), WarExitPolicies.immutable(rawOptions))
                        || LegacyWarExitPolicy.deJureSurrender(war, historical))
                    return Optional.empty();
                ObjectNode output = StrictJson.object().put("status", "negative_assessment_reused").put("war_id", war.warId())
                        .put("queried_date_raw", queried).put("age_raw", elapsed).put("age_game_days", elapsed / 24)
                        .put("expires_date_raw", queried + lease);
                output.set("query_sequence", result.get("query_sequence")); return Optional.of(output);
            }
        } catch (IllegalArgumentException malformed) { return Optional.empty(); }
        return Optional.empty();
    }

    private static ObjectNode negativeSignature(ObjectNode options) {
        ObjectNode result = StrictJson.object(); for (String key : SIGNATURE_FIELDS) { require(options.has(key), "signature field missing"); result.set(key, options.get(key)); }
        ObjectNode choices = object(options.get("options"), "historical choices"); ObjectNode projected = result.putObject("options");
        for (String name : List.of("surrender", "white_peace", "victory")) {
            ObjectNode source = object(choices.get(name), "historical option"); ObjectNode target = projected.putObject(name);
            for (String field : List.of("outcome", "hostage_variant", "context_constructed", "native_validator_passed", "available", "recipient_response")) {
                require(source.has(field), "negative option field missing"); target.set(field, source.get(field));
            }
            NativeInteractionRoles.putOption(target, NativeInteractionRoles.fromOption(source));
        }
        return result;
    }

    private static Optional<ObjectNode> policyDefer(ObjectNode snapshot, WarExitEvidence.War selected, List<ObjectNode> rows) {
        try {
            ObjectNode root = StrictJson.object().put("schema", WarQueryCadenceCodec.SCHEMA);
            ObjectNode projected = StrictJson.object();
            for (String field : List.of("paused", "map_ready", "one_life_terminal_reason", "played_character", "date_raw", "episode_run_id", "diagnostics")) {
                require(snapshot.has(field), "cadence source field missing"); projected.set(field, snapshot.get(field));
            }
            for (String field : List.of("active_event", "pending_character_interaction")) {
                JsonNode value = snapshot.get(field); require(value != null, "cadence modal source missing");
                if (value instanceof ObjectNode) projected.putObject(field); else projected.set(field, value);
            }
            if (snapshot.has("top_exclusive_modal_choice_hint")) projected.set("top_exclusive_modal_choice_hint", snapshot.get("top_exclusive_modal_choice_hint"));
            root.set("snapshot", projected); root.set("active_wars", snapshot.get("active_wars")); root.set("war", selected.original());
            List<WarQueryCadence.HistoryRecord> complete = new ArrayList<>(); WarQueryCadence.Request parsed = null;
            // The existing codec's per-message bound remains 256. Small batches preserve complete original history.
            int count = Math.max(1, rows.size());
            for (int offset = 0; offset < count; offset += 4) {
                ArrayNode records = root.putArray("recent_records");
                for (int i = offset; i < Math.min(rows.size(), offset + 4); i++) {
                    ObjectNode row = rows.get(i); ObjectNode record = records.addObject();
                    record.set("step", row.has("command") ? row.get("command") : com.fasterxml.jackson.databind.node.NullNode.instance);
                    record.set("ok", row.has("ok") ? row.get("ok") : com.fasterxml.jackson.databind.node.NullNode.instance);
                    if (row.has("result")) record.set("result", row.get("result"));
                }
                parsed = WarQueryCadenceCodec.decode(RaiktorExitObservationCodec.encodeWire(root)); complete.addAll(parsed.recentRecords());
            }
            require(parsed != null, "cadence projection required");
            var policy = WarQueryCadence.evaluate(new WarQueryCadence.Request(parsed.snapshot(), parsed.activeWars(), parsed.war(), complete));
            if (policy.isEmpty()) return Optional.empty(); var result = policy.orElseThrow();
            ObjectNode output = StrictJson.object().put("schema", "xar.war-termination-query-policy-defer/v1")
                    .put("war_id", result.warId()).put("latest_queried_date_raw", result.latestQueriedDateRaw())
                    .put("previous_queried_date_raw", result.previousQueriedDateRaw()).put("latest_query_sequence", result.latestQuerySequence())
                    .put("expires_date_raw", result.expiresDateRaw());
            output.putObject("last_observed_casus_belli").put("database_index", result.lastObservedCasusBelli().databaseIndex())
                    .put("canonical_key", result.lastObservedCasusBelli().canonicalKey()); return Optional.of(output);
        } catch (IllegalArgumentException unsupportedProjection) { return Optional.empty(); }
    }

    private static Optional<ObjectNode> optionalFailure(ObjectNode snapshot, int id, List<ObjectNode> rows) {
        try {
            ObjectNode current = optionalFrame(snapshot); String expected = "query-war-termination-options-" + id;
            for (int i = 0; i < rows.size(); i++) {
                if (i >= 512) return Optional.empty(); ObjectNode row = rows.get(i); String step = boundedText(row.get("command"));
                if (step.equals(expected)) {
                    if (!falseValue(row.get("ok"))) return Optional.empty();
                    ObjectNode old = storedOptionalFailure(row.get("result"));
                    if (!sameDayOptionalScope(current, object(old.get("source_frame"), "old source frame"))) return Optional.empty();
                    ObjectNode output = StrictJson.object().put("schema", "xar.war-termination-optional-query-defer/v1")
                            .put("war_id", id).put("reason", "same_day_optional_material_unavailable")
                            .put("native_negative_assessment", false).put("business_submission", false).put("replay_allowed", false);
                    output.set("date_raw", current.get("date_raw")); output.putNull("war_termination_options");
                    output.set("source_request_id", old.get("native_rejection").get("request").get("request_id")); return Optional.of(output);
                }
                if (List.of("restore-", "load-", "surrender-", "white-peace-", "offer-white-peace-", "war-enforce-demands", "enforce-")
                        .stream().anyMatch(step::startsWith)) return Optional.empty();
                if (falseValue(row.get("ok"))) {
                    ObjectNode other = storedOptionalFailure(row.get("result"));
                    if (!textIs(other.get("step"), step) || !sameDayOptionalScope(current, object(other.get("source_frame"), "other source frame"))) return Optional.empty();
                } else if (!trueValue(row.get("ok"))) return Optional.empty();
            }
        } catch (IllegalArgumentException malformed) { return Optional.empty(); }
        return Optional.empty();
    }

    private static ObjectNode storedOptionalFailure(JsonNode value) {
        ObjectNode row = object(value, "stored explicit optional rejection"); ObjectNode source = object(row.get("source_frame"), "stored source frame");
        ObjectNode recreated = StrictJson.object();
        for (String field : List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")) recreated.set(field, source.get(field));
        recreated.put("paused", true).put("map_ready", true);
        recreated.putObject("played_character").set("character_id", source.get("actor_character_id"));
        ((ObjectNode) recreated.get("played_character")).put("alive", true);
        ObjectNode diagnostics = recreated.putObject("diagnostics"); diagnostics.set("bridge_pid", source.get("bridge_pid")); diagnostics.set("connection_generation", source.get("connection_generation"));
        recreated.set("active_wars", source.get("active_war_signature")); ObjectNode frame = optionalFrame(recreated);
        require(equal(source, frame), "stored optional source frame differs");
        ObjectNode evidence = object(row.get("native_rejection"), "original rejection evidence");
        require(textIs(evidence.get("response_result_presence"), "absent"), "original rejection result must be absent");
        ObjectNode request = StrictJson.object(evidence.get("request"), Set.of("type", "protocol_version", "request_id", "step", "expected_revision"));
        String step = boundedText(row.get("step")); require(step.matches("query-war-termination-options-[1-9][0-9]*"), "canonical optional step required");
        int id = Integer.parseInt(step.substring("query-war-termination-options-".length())); require(id > 0, "positive optional WarID");
        boolean active = false; for (JsonNode war : frame.get("active_war_signature")) if (integerIs(war.get("war_id"), id)) active = true;
        require(active, "optional queried war must remain active"); String requestId = boundedText(request.get("request_id"));
        require(requestId.matches("step-[1-9][0-9]*-[0-9a-f]{12}"), "original canonical native request ID required");
        BigInteger number = new BigInteger(requestId.split("-")[1]); require(number.signum() > 0 && number.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)) <= 0, "original request number range");
        require(textIs(request.get("type"), "execute_step") && integerIs(request.get("protocol_version"), 1)
                && textIs(request.get("step"), step) && equal(request.get("expected_revision"), frame.get("native_revision"))
                && textIs(evidence.get("response_error"), OPTIONAL_ERROR) && textIs(evidence.get("response_request_id"), requestId)
                && integerIs(evidence.get("response_protocol_version"), 1) && falseValue(evidence.get("response_ok")), "original optional rejection binding differs");
        ObjectNode expected = StrictJson.object().put("schema", "xar.war-termination-readonly-unavailable/v1").put("step", step)
                .put("accepted", false).put("available", false).put("status", "unavailable").put("read_only", true)
                .put("business_submission", false).put("replay_allowed", false).put("replan_required", true).put("war_id", id)
                .putNull("war_termination_options").put("unavailable_reason", "native_termination_completion_snapshot_read_failed")
                .put("semantic_publication_rechecked", true).put("fresh_native_completion_proved", false);
        expected.set("source_frame", frame); ObjectNode rejected = expected.putObject("native_rejection"); rejected.set("request", request);
        rejected.put("response_error", OPTIONAL_ERROR).put("response_request_id", requestId).put("response_protocol_version", 1)
                .put("response_ok", false).put("response_result_presence", "absent");
        require(equal(expected, row), "stored optional unavailable DTO differs from original exact contract"); return expected;
    }

    private static ObjectNode optionalFrame(ObjectNode snapshot) {
        require(trueValue(snapshot.get("paused")) && trueValue(snapshot.get("map_ready")), "optional query requires paused map");
        ObjectNode actor = object(snapshot.get("played_character"), "actor"); require(trueValue(actor.get("alive")), "living optional query actor required");
        ObjectNode diagnostics = object(snapshot.get("diagnostics"), "diagnostics"); ObjectNode result = StrictJson.object();
        String id = boundedText(snapshot.get("snapshot_id")); BigInteger nativeRevision = positiveSafe(snapshot.get("native_revision"), StrictJson.MAX_SAFE_INTEGER);
        require(id.equals("native:" + nativeRevision), "optional snapshot/native revision binding differs"); result.put("snapshot_id", id);
        result.put("revision", positiveSafe(snapshot.get("revision"), StrictJson.MAX_SAFE_INTEGER)); result.put("native_revision", nativeRevision);
        result.put("date_raw", positiveSafe(snapshot.get("date_raw"), StrictJson.MAX_SAFE_INTEGER));
        result.put("actor_character_id", positiveSafe(actor.get("character_id"), 0xffff_ffffL));
        result.put("episode_run_id", boundedText(snapshot.get("episode_run_id")));
        result.put("bridge_pid", positiveSafe(diagnostics.get("bridge_pid"), 0xffff_ffffL));
        result.put("connection_generation", positiveSafe(diagnostics.get("connection_generation"), StrictJson.MAX_SAFE_INTEGER));
        result.set("active_war_signature", warSignature(snapshot.get("active_wars"), true)); return result;
    }

    private static ArrayNode warSignature(JsonNode value, boolean optional) {
        require(value != null && value.isArray() && (!optional || !value.isEmpty()), "actual active-war signature required");
        List<ObjectNode> wars = new ArrayList<>(); Set<BigInteger> ids = new java.util.HashSet<>();
        for (JsonNode raw : value) {
            ObjectNode row = object(raw, "signature war"); ObjectNode projected = StrictJson.object();
            for (String field : WAR_FIELDS) { require(row.has(field), "all nullable signature fields required"); projected.set(field, row.get(field)); }
            BigInteger id = StrictJson.integer(row.get("war_id"), BigInteger.ONE, optional ? BigInteger.valueOf(0xffff_ffffL) : BigInteger.valueOf(Integer.MAX_VALUE));
            require(ids.add(id), "duplicate signature WarID"); require(textIs(row.get("player_side"), "attacker") || textIs(row.get("player_side"), "defender"), "signature side");
            JsonNode primary = row.get("player_is_primary_war_leader"); require(primary.isNull() || primary.isBoolean(), "signature primary flag");
            JsonNode opponent = row.get("primary_opponent_character_id"); if (!opponent.isNull()) {
                StrictJson.integer(opponent, optional ? 1 : 0, optional ? 0xffff_ffffL : Integer.MAX_VALUE);
            }
            StrictJson.integer(row.get("player_relative_war_score"), -StrictJson.MAX_SAFE_INTEGER, StrictJson.MAX_SAFE_INTEGER);
            JsonNode targets = row.get("targeted_title_ids"); require(targets.isArray(), "signature targets"); Set<BigInteger> targetIds = new java.util.HashSet<>();
            for (JsonNode target : targets) {
                BigInteger title = StrictJson.integer(target, BigInteger.valueOf(optional ? 1 : 0), BigInteger.valueOf(optional ? 0xffff_ffffL : Integer.MAX_VALUE));
                require(!optional || targetIds.add(title), "duplicate optional signature TitleID");
            }
            wars.add(projected);
        }
        wars.sort(Comparator.comparing(row -> row.get("war_id").bigIntegerValue())); ArrayNode output = StrictJson.object().putArray("wars"); wars.forEach(output::add); return output;
    }

    private static boolean sameDayOptionalScope(ObjectNode current, ObjectNode previous) {
        return List.of("date_raw", "actor_character_id", "episode_run_id", "bridge_pid", "connection_generation", "active_war_signature")
                .stream().allMatch(field -> equal(current.get(field), previous.get(field)));
    }
    private static BigInteger positiveSafe(JsonNode value, long maximum) { return StrictJson.integer(value, BigInteger.ONE, BigInteger.valueOf(maximum)); }
    private static String boundedText(JsonNode value) { String text = StrictJson.text(value); require(text.length() <= 256, "bounded original optional text"); return text; }
    private static boolean present(JsonNode value) { return value != null && !value.isNull(); }
    private static boolean equal(JsonNode a, JsonNode b) { return a != null && b != null && Arrays.equals(StrictJson.canonical(a), StrictJson.canonical(b)); }
    private static boolean negativeBarrier(String step) {
        if (step == null) return false;
        return step.startsWith("select-event-option-") || Set.of("resolve-current-event", "query-current-event-window-context-v1",
                "query-pending-character-interaction-context-v1", "acknowledge-pending-character-interaction",
                "accept-pending-character-interaction", "reject-pending-character-interaction", "block-pending-character-interaction",
                "death-terminal", "start-next-episode").contains(step);
    }
}

