package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

/** Original pure three-way verifier. A submitted command cannot satisfy frozen loss, truce or cold-restore checks. */
public final class RaiktorExitPostcondition {
    public static final String CONTRACT = "raiktor-three-way-exit-postcondition-v1";
    public static final String SCHEMA = "xar.ck3.raiktor_three_way_exit_postcondition.v1";
    public static final String PROVIDER = "raiktor-three-way-exit-postcondition-provider-v1";
    public static final String POSTWAR_SCHEMA = "xar.ck3.raiktor_three_way_exit_postwar_evidence.v1";
    public static final List<String> CONTINUE = List.of("same_full_generation_war_id_remains_active",
            "same_played_character_and_episode_remain_bound", "map_resume_is_observed_on_a_successor_revision");
    public static final List<String> TERMINATE = List.of("old_full_generation_war_id_absent", "gold_matches_frozen_terms",
            "attacker_prestige_matches_frozen_terms", "directional_truce_days_and_expiry_observed",
            "source_specific_war_bound_regiments_absent", "postwar_checkpoint_cold_restore_rebinds_identity");
    private static final String GATE_SCHEMA = "xar.ck3.raiktor_three_way_exit_action_gate.v1";
    private static final String GATE_PROVIDER = "raiktor-three-way-exit-action-gate-provider-v1";
    private static final String GATE_CONTRACT = "raiktor-three-way-exit-action-gate-v1";
    private RaiktorExitPostcondition() { }
    public static ObjectNode provide(JsonNode gate, JsonNode actionResult, JsonNode postSnapshot,
            JsonNode postwarEvidence, JsonNode checkpointRestore) {
        if (absent(gate)) return result(List.of("action_authorization_unavailable"), null, null, Map.of(), false, false, false, false, StrictJson.object());
        ObjectNode authorization = normalizeAuthorization(gate), action = object(authorization.get("action"), "authorization action");
        ObjectNode plan = object(authorization.get("postcondition_plan"), "authorization postcondition plan");
        String route = text(action.get("semantic_action"), "semantic route");
        List<String> expected = route.equals("continue") ? CONTINUE : Set.of("white_peace", "surrender").contains(route) ? TERMINATE : null;
        require(expected != null && strings(plan.get("requirements"), "postconditions").equals(expected), "authorization postcondition route or requirements drifted");
        ObjectNode expectations = object(plan.get("expectations"), "postcondition expectations");
        List<String> missing = new ArrayList<>();
        if (absent(actionResult)) missing.add("action_result_unavailable"); if (absent(postSnapshot)) missing.add("post_snapshot_unavailable");
        if (!route.equals("continue")) {
            if (absent(postwarEvidence)) missing.add("postwar_evidence_unavailable");
            if (absent(checkpointRestore)) missing.add("checkpoint_restore_evidence_unavailable");
        }
        if (!missing.isEmpty()) return result(missing, route, authorization, Map.of(), false, false, false, false, StrictJson.object());
        ObjectNode submitted = object(actionResult, "action result"), post = snapshot(postSnapshot, "post snapshot");
        Map<String,Boolean> checks;
        ObjectNode evidence = StrictJson.object();
        if (route.equals("continue")) {
            checks = continueChecks(authorization, expectations, submitted, post);
        } else {
            ObjectNode postwar = exact(postwarEvidence, Set.of("schema", "authorization_sha256", "war_id", "post_snapshot_id", "source_specific_loss", "truce"), "postwar evidence");
            require(isText(postwar.get("schema"), POSTWAR_SCHEMA) && isSha(postwar.get("authorization_sha256")), "postwar evidence schema/hash drifted");
            ObjectNode checkpoint = exact(checkpointRestore, Set.of("save_result", "restore_result", "restored_snapshot"), "checkpoint restore evidence");
            checks = terminationChecks(authorization, expectations, submitted, post, postwar, checkpoint);
            evidence.set("post_snapshot_id", post.get("snapshot_id")); evidence.put("postwar_evidence_sha256", hash(postwar));
            evidence.set("checkpoint_sha256", object(object(checkpoint.get("save_result"), "save result").get("checkpoint"), "saved checkpoint").get("sha256"));
        }
        List<String> failed = checks.entrySet().stream().filter(e -> !e.getValue()).map(e -> "postcondition_failed:" + e.getKey()).toList();
        boolean verified = failed.isEmpty(), cold = checks.getOrDefault("postwar_checkpoint_cold_restore_rebinds_identity", false);
        return result(failed, route, authorization, checks, submissionMatches(submitted, authorization, post), verified, cold, !route.equals("continue") && verified, evidence);
    }

    public static final String SUBMISSION_CONTRACT = "raiktor-three-way-exit-postcondition-v2";
    public static final String SUBMISSION_SCHEMA = "xar.ck3.raiktor_three_way_exit_postcondition.v2";
    public static final String SUBMISSION_PROVIDER = "raiktor-three-way-exit-postcondition-provider-v2";

    /**
     * Current projection retains a separately bound submission fact when full postwar evidence is missing.
     * The original v1 provider stays byte compatible for strict replay of retained receipts.
     */
    public static ObjectNode provideSubmissionFacts(JsonNode gate, JsonNode actionResult, JsonNode postSnapshot,
            JsonNode postwarEvidence, JsonNode checkpointRestore) {
        ObjectNode value = provide(gate, actionResult, postSnapshot, postwarEvidence, checkpointRestore);
        boolean submitted = yes(value.get("action_submitted"));
        if (!absent(gate) && !absent(actionResult) && !absent(postSnapshot)
                && isText(value.get("status"), "evidence_required")) {
            ObjectNode authorization = normalizeAuthorization(gate);
            submitted = submissionMatches(object(actionResult, "action result"), authorization,
                    snapshot(postSnapshot, "post snapshot"));
        }
        ObjectNode receipt = object(value.get("postcondition_receipt"), "postcondition receipt");
        receipt.put("schema_version", 2).put("contract", SUBMISSION_CONTRACT).put("action_submitted", submitted);
        receipt.remove("receipt_sha256");
        receipt.put("receipt_sha256", hash(receipt));
        value.put("schema", SUBMISSION_SCHEMA).put("provider", SUBMISSION_PROVIDER).put("action_submitted", submitted);
        return value;
    }

    public static final String NATIVE_SUBMISSION_CONTRACT = "raiktor-three-way-exit-postcondition-v3";
    public static final String NATIVE_SUBMISSION_SCHEMA = "xar.ck3.raiktor_three_way_exit_postcondition.v3";
    public static final String NATIVE_SUBMISSION_PROVIDER = "raiktor-three-way-exit-postcondition-provider-v3";
    /** DATA supplied only after the caller verifies the retained native request/response and endpoint custody. */
    public enum NativeSubmissionOrigin { VERIFIED_CUSTODY, UNAVAILABLE }

    /**
     * Explicit native-custody submission projection. No full postwar or cold-restore evidence is accepted here.
     * The original v1/v2 entry points retain their backend-field semantics for archived replay.
     */
    public static ObjectNode provideNativeSubmissionFacts(JsonNode gate, JsonNode actionResult, JsonNode postSnapshot,
            NativeSubmissionOrigin origin) {
        require(origin != null, "explicit native submission origin required");
        if (!absent(gate)) {
            ObjectNode authorization = normalizeAuthorization(gate);
            require(oneOf(object(authorization.get("action"), "action").get("semantic_action"), "white_peace", "surrender"),
                    "native submission projection requires a termination route");
        }
        ObjectNode value = provide(gate, actionResult, postSnapshot, null, null);
        boolean submitted = false;
        if (!absent(gate) && !absent(actionResult) && !absent(postSnapshot)) {
            ObjectNode authorization = normalizeAuthorization(gate);
            ObjectNode action = object(actionResult, "action result"), post = snapshot(postSnapshot, "post snapshot");
            submitted = submissionMatchesNative(action, authorization, post,
                    origin == NativeSubmissionOrigin.VERIFIED_CUSTODY);
        }
        ObjectNode receipt = object(value.get("postcondition_receipt"), "postcondition receipt");
        receipt.put("schema_version", 3).put("contract", NATIVE_SUBMISSION_CONTRACT).put("action_submitted", submitted);
        receipt.remove("receipt_sha256"); receipt.put("receipt_sha256", hash(receipt));
        value.put("schema", NATIVE_SUBMISSION_SCHEMA).put("provider", NATIVE_SUBMISSION_PROVIDER).put("action_submitted", submitted);
        return value;
    }

    public static ObjectNode normalizeAuthorization(JsonNode rawGate) {
        ObjectNode gate = object(rawGate, "action gate");
        require(isText(gate.get("schema"), GATE_SCHEMA) && isText(gate.get("provider"), GATE_PROVIDER)
                && isText(gate.get("status"), "authorized") && yes(gate.get("action_ready"))
                && array(gate.get("blockers"), "action gate blockers").isEmpty(), "action gate is not authorized");
        ObjectNode authorization = object(gate.get("authorization"), "authorization");
        require(number(authorization.get("schema_version"), 1, 1, "authorization version") == 1
                && isText(authorization.get("contract"), GATE_CONTRACT) && isText(authorization.get("status"), "authorized"), "authorization identity drifted");
        ObjectNode unhashed = authorization.deepCopy(); unhashed.remove("authorization_sha256");
        require(isSha(authorization.get("authorization_sha256")) && isText(authorization.get("authorization_sha256"), hash(unhashed)), "authorization hash drifted");
        ObjectNode action = object(authorization.get("action"), "authorization action"), frame = object(authorization.get("frame"), "authorization frame");
        positive32(frame.get("war_id"), "authorization WarID");
        StrictJson.integer(frame.get("snapshot_revision"), BigInteger.ONE, StrictJson.UINT64_MAX);
        StrictJson.integer(frame.get("native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX);
        i32(frame.get("date_raw"), "authorization date"); positive32(frame.get("ck3_pid"), "authorization PID");
        positive32(frame.get("primary_attacker_character_id"), "authorization attacker");
        text(frame.get("snapshot_id"), "authorization snapshot"); text(frame.get("episode_id"), "authorization episode");
        text(action.get("literal"), "authorization literal"); text(action.get("semantic_action"), "authorization semantic action");
        require(yes(action.get("single_action_only")) && same(action.get("war_id"), frame.get("war_id"))
                && same(action.get("expected_revision"), frame.get("snapshot_revision")), "authorization action binding drifted");
        return authorization.deepCopy();
    }
    /** Frozen source projection for the actual sole-writer ActionCommand consumer; this function never grants a submission permit. */
    public static ObjectNode bindFrozenPlan(JsonNode frameValue, JsonNode planValue, String literal, String semanticAction) {
        ObjectNode frame = object(frameValue, "actual pre-action frame"), plan = object(planValue, "actual frozen postcondition plan");
        number(plan.get("schema_version"), 1, 1, "frozen postcondition plan version");
        require(Set.of("continue", "white_peace", "surrender").contains(semanticAction), "three-way semantic route required");
        require(isText(plan.get("route"), semanticAction) && !bool(plan.get("verified"), "frozen verified"), "frozen plan route or verified state differs");
        require(strings(plan.get("requirements"), "frozen requirements").equals(semanticAction.equals("continue") ? CONTINUE : TERMINATE), "frozen postcondition requirements differ");
        int war = positive32(frame.get("war_id"), "frozen WarID");
        require(literal != null && literal.equals(semanticAction.equals("continue") ? "resume-map"
                : (semanticAction.equals("white_peace") ? "offer-white-peace-" : "surrender-war-") + war), "frozen literal differs from semantic route and full WarID");
        ObjectNode expected = object(plan.get("expectations"), "frozen expectations");
        require(same(expected.get("war_id"), frame.get("war_id")) && same(expected.get("played_character_id"), frame.get("primary_attacker_character_id")),
                "frozen expected war or played character differs from source frame");
        if (!semanticAction.equals("continue")) require(same(expected.get("opponent_character_id"), frame.get("primary_defender_character_id")), "frozen opponent differs from source frame");
        ObjectNode action = StrictJson.object().put("semantic_action", semanticAction).put("literal", literal).put("single_action_only", true);
        action.set("war_id", frame.get("war_id")); action.set("expected_revision", frame.get("snapshot_revision"));
        ObjectNode authorization = StrictJson.object().put("schema_version", 1).put("contract", GATE_CONTRACT).put("status", "authorized");
        authorization.set("frame", frame.deepCopy()); authorization.set("action", action); authorization.set("postcondition_plan", plan.deepCopy());
        authorization.put("authorization_sha256", hash(authorization));
        ObjectNode gate = StrictJson.object().put("schema", GATE_SCHEMA).put("provider", GATE_PROVIDER).put("status", "authorized").put("action_ready", true);
        gate.putArray("blockers"); gate.set("authorization", authorization); normalizeAuthorization(gate); return gate;
    }
    private static boolean submissionMatches(ObjectNode result, ObjectNode authorization, ObjectNode post) {
        ObjectNode action = object(authorization.get("action"), "action"), frame = object(authorization.get("frame"), "frame");
        if (!(same(result.get("step"), action.get("literal")) && yes(result.get("accepted"))
                && oneOf(result.get("status"), "submitted", "applied") && isText(result.get("backend_id"), "native-headless"))) return false;
        JsonNode termination = result.get("war_termination_result"); if (absent(termination)) return true;
        ObjectNode value = object(termination, "war termination result");
        String route = text(action.get("semantic_action"), "semantic action");
        boolean observationBound = isText(value.get("status"), "applied") ? same(value.get("observed_snapshot_id"), post.get("snapshot_id"))
                : isText(value.get("status"), "submitted_pending") && nonempty(value.get("observed_snapshot_id")) && no(value.get("war_id_absent_after_ack"));
        return oneOf(value.get("status"), "applied", "submitted_pending") && same(value.get("war_id"), action.get("war_id"))
                && isText(value.get("outcome"), route.equals("surrender") ? "attacker_defeat" : route)
                && same(value.get("episode_run_id"), frame.get("episode_id")) && same(value.get("starting_snapshot_id"), frame.get("snapshot_id"))
                && observationBound && yes(value.get("command_acknowledged"));
    }
    private static boolean submissionMatchesNative(ObjectNode result, ObjectNode authorization, ObjectNode post, boolean nativeOriginVerified) {
        if (!nativeOriginVerified) return false;
        ObjectNode action = object(authorization.get("action"), "action"), frame = object(authorization.get("frame"), "frame");
        if (!(same(result.get("step"), action.get("literal")) && yes(result.get("accepted"))
                && oneOf(result.get("status"), "submitted", "applied"))) return false;
        JsonNode backend = result.get("backend_id");
        if (result.has("backend_id") && !isText(backend, "native-headless")) return false;
        JsonNode termination = result.get("war_termination_result"); if (absent(termination)) return true;
        ObjectNode value = object(termination, "war termination result");
        String route = text(action.get("semantic_action"), "semantic action");
        boolean observationBound = isText(value.get("status"), "applied") ? same(value.get("observed_snapshot_id"), post.get("snapshot_id"))
                : isText(value.get("status"), "submitted_pending") && nonempty(value.get("observed_snapshot_id")) && no(value.get("war_id_absent_after_ack"));
        return oneOf(value.get("status"), "applied", "submitted_pending") && same(value.get("war_id"), action.get("war_id"))
                && isText(value.get("outcome"), route.equals("surrender") ? "attacker_defeat" : route)
                && same(value.get("episode_run_id"), frame.get("episode_id")) && same(value.get("starting_snapshot_id"), frame.get("snapshot_id"))
                && observationBound && yes(value.get("command_acknowledged"));
    }
    private static Map<String,Boolean> continueChecks(ObjectNode authorization, ObjectNode expected, ObjectNode action, ObjectNode post) {
        ObjectNode frame = object(authorization.get("frame"), "frame"), diagnostics = object(post.get("diagnostics"), "diagnostics"), played = object(post.get("played_character"), "played");
        Map<String,Boolean> checks = new LinkedHashMap<>();
        checks.put("authorized_action_submitted", submissionMatches(action, authorization, post));
        checks.put(CONTINUE.get(0), warPresent(post, expected.get("war_id")));
        checks.put(CONTINUE.get(1), same(played.get("character_id"), expected.get("played_character_id"))
                && same(post.get("episode_run_id"), expected.get("episode_id")) && same(diagnostics.get("bridge_pid"), frame.get("ck3_pid"))
                && connection(diagnostics.get("connection_generation"), frame.get("connection_id")));
        checks.put(CONTINUE.get(2), greater(post.get("revision"), frame.get("snapshot_revision")) && greater(post.get("native_revision"), frame.get("native_revision"))
                && greater(post.get("date_raw"), frame.get("date_raw")) && absent(post.get("active_event")));
        return checks;
    }
    private static Map<String,Boolean> terminationChecks(ObjectNode authorization, ObjectNode expected, ObjectNode action, ObjectNode post, ObjectNode postwar, ObjectNode checkpoint) {
        ObjectNode frame = object(authorization.get("frame"), "frame"), resources = object(expected.get("resources"), "resources");
        ObjectNode gold = object(resources.get("gold"), "gold"), prestige = object(resources.get("prestige"), "prestige"), truceExpected = object(expected.get("truce"), "truce expectation");
        ObjectNode lossExpected = object(expected.get("source_specific_loss"), "loss expectation"), truce = object(postwar.get("truce"), "postwar truce"), loss = object(postwar.get("source_specific_loss"), "postwar loss");
        boolean successor = greater(post.get("revision"), frame.get("snapshot_revision")) && greater(post.get("native_revision"), frame.get("native_revision"))
                && atLeast(post.get("date_raw"), frame.get("date_raw")) && yes(post.get("paused")) && absent(post.get("active_event"));
        boolean bound = same(postwar.get("authorization_sha256"), authorization.get("authorization_sha256")) && same(postwar.get("post_snapshot_id"), post.get("snapshot_id"))
                && same(postwar.get("war_id"), expected.get("war_id"));
        JsonNode queried = truce.get("queried_at_date_raw"), days = truce.get("evaluated_days"), expiry = truce.get("expiry_date_raw");
        boolean exactExpiry = integral(queried) && integral(days) && integral(expiry) && expiry.bigIntegerValue().equals(queried.bigIntegerValue().add(days.bigIntegerValue().multiply(BigInteger.valueOf(24))));
        Map<String,Boolean> checks = new LinkedHashMap<>();
        checks.put("authorized_action_submitted", submissionMatches(action, authorization, post));
        checks.put(TERMINATE.get(0), sameHot(post, frame) && successor && !warPresent(post, expected.get("war_id")));
        checks.put(TERMINATE.get(1), bound && fixedMatches(post.get("played_character_gold"), gold.get("post_raw"), resources.get("scale")));
        checks.put(TERMINATE.get(2), bound && fixedMatches(post.get("played_character_prestige"), prestige.get("post_raw"), resources.get("scale")));
        checks.put(TERMINATE.get(3), bound && isText(truce.get("source"), "persisted_native_truce_row") && no(truce.get("formula_derived"))
                && same(truce.get("from_character_id"), truceExpected.get("owner_character_id")) && same(truce.get("to_character_id"), truceExpected.get("toward_character_id"))
                && same(days, truceExpected.get("evaluated_days")) && same(queried, post.get("date_raw")) && exactExpiry && isSha(truce.get("evidence_sha256")));
        checks.put(TERMINATE.get(4), bound && same(loss.get("war_id"), lossExpected.get("war_id")) && same(loss.get("status"), lossExpected.get("required_cleanup_status"))
                && yes(loss.get("source_specific_attribution_ready")) && positive(loss.get("frozen_generation_count")) && zero(loss.get("post_termination_soldiers"))
                && isSha(loss.get("source_set_sha256")) && isSha(loss.get("evidence_sha256")));
        checks.put(TERMINATE.get(5), bound && checkpointMatches(checkpoint, post, expected));
        return checks;
    }
    private static boolean checkpointMatches(ObjectNode value, ObjectNode post, ObjectNode expected) {
        ObjectNode save = object(value.get("save_result"), "save result"), restore = object(value.get("restore_result"), "restore result");
        ObjectNode restored = snapshot(value.get("restored_snapshot"), "restored snapshot"), saved = object(save.get("checkpoint"), "saved checkpoint"), checkpoint = object(restore.get("checkpoint"), "restored checkpoint");
        ObjectNode lifecycle = object(restore.get("lifecycle"), "restore lifecycle"), diagnostics = object(restored.get("diagnostics"), "restored diagnostics");
        ObjectNode player = object(restored.get("played_character"), "restored player"), postDiagnostics = object(post.get("diagnostics"), "post diagnostics");
        ObjectNode resources = object(expected.get("resources"), "resources"), gold = object(resources.get("gold"), "gold"), prestige = object(resources.get("prestige"), "prestige");
        JsonNode digest = saved.get("sha256"), materialization = save.get("materialization");
        return isText(save.get("step"), "save-checkpoint") && yes(save.get("accepted")) && isText(save.get("status"), "submitted") && isText(save.get("backend_id"), "native-headless")
                && isText(saved.get("status"), "saved") && isSha(digest) && same(saved.get("date_raw"), post.get("date_raw")) && same(saved.get("episode_run_id"), post.get("episode_run_id"))
                && same(saved.get("episode_character_id"), expected.get("played_character_id")) && materialization instanceof ObjectNode && yes(materialization.get("available"))
                && isText(restore.get("step"), "restore-checkpoint") && yes(restore.get("accepted")) && isText(restore.get("status"), "restored") && isText(restore.get("backend_id"), "native-headless")
                && isText(restore.get("source"), "native-session-lifecycle-queue") && yes(restore.get("map_ready"))
                && isText(checkpoint.get("status"), "restored") && same(checkpoint.get("sha256"), digest) && same(checkpoint.get("saved_date_raw"), post.get("date_raw"))
                && same(checkpoint.get("date_raw"), post.get("date_raw")) && same(restore.get("restored_date_raw"), post.get("date_raw")) && yes(restore.get("paused"))
                && same(restore.get("snapshot_id"), restored.get("snapshot_id")) && same(restore.get("revision"), restored.get("revision"))
                && same(lifecycle.get("previous_pid"), postDiagnostics.get("bridge_pid")) && positive(lifecycle.get("pid")) && !same(lifecycle.get("pid"), postDiagnostics.get("bridge_pid"))
                && same(lifecycle.get("previous_connection_generation"), postDiagnostics.get("connection_generation")) && same(lifecycle.get("connection_generation"), diagnostics.get("connection_generation"))
                && same(diagnostics.get("bridge_pid"), lifecycle.get("pid")) && yes(restored.get("paused")) && absent(restored.get("active_event"))
                && same(restored.get("date_raw"), post.get("date_raw")) && same(restored.get("episode_run_id"), post.get("episode_run_id"))
                && same(player.get("character_id"), expected.get("played_character_id")) && !warPresent(restored, expected.get("war_id"))
                && fixedMatches(restored.get("played_character_gold"), gold.get("post_raw"), resources.get("scale"))
                && fixedMatches(restored.get("played_character_prestige"), prestige.get("post_raw"), resources.get("scale"));
    }
    private static ObjectNode result(List<String> blockers, String route, ObjectNode authorization, Map<String,Boolean> checks,
            boolean submitted, boolean verified, boolean cold, boolean closed, ObjectNode evidence) {
        ObjectNode receipt = StrictJson.object().put("schema_version", 1).put("contract", CONTRACT).put("status", verified ? "green" : "red").put("route", route);
        if (authorization == null) receipt.putNull("authorization_sha256"); else receipt.set("authorization_sha256", authorization.get("authorization_sha256"));
        ObjectNode checkJson = receipt.putObject("checks"); checks.forEach(checkJson::put); receipt.set("evidence", evidence.deepCopy());
        receipt.put("action_submitted", submitted).put("postcondition_verified", verified).put("checkpoint_cold_restore_verified", cold).put("gen034_closed", closed);
        receipt.put("receipt_sha256", hash(receipt));
        ObjectNode result = StrictJson.object().put("schema", SCHEMA).put("provider", PROVIDER)
                .put("status", verified ? "verified" : blockers.stream().anyMatch(s -> s.endsWith("_unavailable")) ? "evidence_required" : "red").put("route", route)
                .put("action_submitted", submitted).put("postcondition_verified", verified).put("checkpoint_cold_restore_verified", cold).put("gen034_closed", closed);
        strings(result, "blockers", blockers); result.set("postcondition_receipt", receipt);
        strings(result, "boundaries", List.of("command_acknowledgement_is_submission_only", "termination_requires_all_six_frozen_observations",
                "continue_postcondition_does_not_close_gen034", "this_provider_performs_no_ck3_or_filesystem_operation")); return result;
    }
    static ObjectNode snapshot(JsonNode value, String name) {
        ObjectNode n = object(value, name); for (String field : List.of("revision", "native_revision", "date_raw")) integer(n.get(field), name + " " + field);
        text(n.get("snapshot_id"), name + " snapshot identity"); array(n.get("active_wars"), name + " active wars"); return n;
    }
    static boolean warPresent(ObjectNode snapshot, JsonNode war) { for (JsonNode value : array(snapshot.get("active_wars"), "active wars")) if (value.isObject() && same(value.get("war_id"), war)) return true; return false; }
    static boolean sameHot(ObjectNode snapshot, ObjectNode frame) {
        if (!(snapshot.get("diagnostics") instanceof ObjectNode diagnostics) || !(snapshot.get("played_character") instanceof ObjectNode player)) return false;
        return same(diagnostics.get("bridge_pid"), frame.get("ck3_pid")) && connection(diagnostics.get("connection_generation"), frame.get("connection_id"))
                && same(snapshot.get("episode_run_id"), frame.get("episode_id")) && same(player.get("character_id"), frame.get("primary_attacker_character_id"));
    }
    private static boolean fixedMatches(JsonNode value, JsonNode raw, JsonNode scale) {
        return value instanceof ObjectNode n && integral(n.get("raw")) && integral(n.get("scale")) && integral(raw) && integral(scale) && same(n.get("raw"), raw) && same(n.get("scale"), scale);
    }
    private static boolean connection(JsonNode generation, JsonNode connection) {
        if (!integral(generation) || connection == null || !connection.isTextual()) return false;
        String value = connection.textValue(), prefix = "connection-generation:"; if (!value.startsWith(prefix)) return false;
        String digits = value.substring(prefix.length()); return digits.matches("[0-9]+") && generation.bigIntegerValue().equals(new BigInteger(digits));
    }
    private static boolean greater(JsonNode a, JsonNode b) { return integral(a) && integral(b) && a.bigIntegerValue().compareTo(b.bigIntegerValue()) > 0; }
    private static boolean atLeast(JsonNode a, JsonNode b) { return integral(a) && integral(b) && a.bigIntegerValue().compareTo(b.bigIntegerValue()) >= 0; }
    static boolean absent(JsonNode n) { return n == null || n.isNull(); }
    private static boolean integral(JsonNode n) { return n != null && n.isIntegralNumber(); }
    private static boolean positive(JsonNode n) { return integral(n) && n.bigIntegerValue().signum() > 0; }
    private static boolean zero(JsonNode n) { return integral(n) && n.bigIntegerValue().signum() == 0; }
    private static boolean nonempty(JsonNode n) { return n != null && n.isTextual() && !n.textValue().isEmpty(); }
    private static boolean isText(JsonNode n, String value) { return n != null && n.isTextual() && n.textValue().equals(value); }
    private static boolean oneOf(JsonNode n, String... values) { return n != null && n.isTextual() && Set.of(values).contains(n.textValue()); }
    private static boolean yes(JsonNode n) { return n != null && n.isBoolean() && n.booleanValue(); }
    private static boolean no(JsonNode n) { return n != null && n.isBoolean() && !n.booleanValue(); }
    private static boolean isSha(JsonNode n) { return n != null && n.isTextual() && n.textValue().matches("[0-9a-fA-F]{64}"); }
}

