package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

/** Original exact-build capture/current/cleanup contracts. The historical source origin is never promoted to another EXE. */
public final class RaiktorWarBoundEvidenceCodec {
    public static final String CAPTURE_EXE = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final String ARM_SHA = "B7DC28B0B9EDB0F8A03E5DB2F03AD6CA1E3B649648BAE161B6A487063735B9B8";
    private static final String GENERIC_BACKEND = "ck3-1.19.0.6-native-raiktor-war-bound-regiment-v1";
    private static final String GENERIC_STATUS = "generic_war_bound_visible_source_unattributed";
    public record Frame(int warId, int attacker, int defender, BigInteger publicRevision, BigInteger nativeRevision, int dateRaw) {
        public Frame {
            require(warId != -1 && attacker != -1 && defender != -1, "full generations excluding none required");
            require(publicRevision != null && publicRevision.signum() > 0 && publicRevision.compareTo(StrictJson.UINT64_MAX) <= 0
                    && nativeRevision != null && nativeRevision.signum() > 0 && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 frame revisions required");
        }
        Frame nativeStamped() { return new Frame(warId, attacker, defender, nativeRevision, nativeRevision, dateRaw); }
    }
    record Identity(int war, List<Integer> persistent, List<Integer> current, List<Integer> armies) {
        Identity { persistent = List.copyOf(persistent); current = List.copyOf(current); armies = List.copyOf(armies); }
        boolean sameRegiments(Identity other) { return war == other.war && persistent.equals(other.persistent) && current.equals(other.current); }
    }
    private RaiktorWarBoundEvidenceCodec() { }
    public static ObjectNode normalizeGeneric(JsonNode value, Frame expected) {
        ObjectNode root = exact(value, Set.of("schema_version", "backend_id", "status", "failure", "active_frame", "postwar_frame",
                "owner_character_id", "war_id", "source_attribution", "soldiers", "cleanup", "regiments", "readiness"), "war-bound regiment root");
        number(root.get("schema_version"), 1, 1, "generic version");
        require(text(root.get("backend_id"), "generic backend").equals(GENERIC_BACKEND) && text(root.get("status"), "generic status").equals(GENERIC_STATUS)
                && root.get("failure").isNull(), "generic war-bound observation unavailable");
        int war = fullId(root.get("war_id"), "generic war"), owner = fullId(root.get("owner_character_id"), "owner");
        require(war == expected.warId() && owner == expected.attacker(), "generic selected binding differs");
        ObjectNode active = exact(root.get("active_frame"), Set.of("snapshot_revision", "native_revision", "date_raw", "paused", "war_id",
                "active_casus_belli_database_index", "active_casus_belli_key", "primary_attacker_character_id", "primary_defender_character_id"), "generic active frame");
        require(bool(active.get("paused"), "active paused") && fullId(active.get("war_id"), "active war") == war
                && text(active.get("active_casus_belli_key"), "active CB").equals("raiktor_claim_cb")
                && fullId(active.get("primary_attacker_character_id"), "attacker") == expected.attacker()
                && fullId(active.get("primary_defender_character_id"), "defender") == expected.defender()
                && uint64(active.get("snapshot_revision")).equals(expected.publicRevision()) && uint64(active.get("native_revision")).equals(expected.nativeRevision())
                && i32(active.get("date_raw"), "active date") == expected.dateRaw(), "generic active frame differs");
        number(active.get("active_casus_belli_database_index"), 0, Integer.MAX_VALUE, "CB database index");
        ObjectNode source = exact(root.get("source_attribution"), Set.of("mode", "authored_candidate_name", "authored_spawn_army_count", "authored_soldiers_per_army", "authored_total_soldiers"), "source attribution");
        require(text(source.get("mode"), "source mode").equals("authored_candidate_only") && text(source.get("authored_candidate_name"), "candidate").equals("norman_highwaymen"), "authored boundary differs");
        number(source.get("authored_spawn_army_count"), 6, 6, "authored count"); number(source.get("authored_soldiers_per_army"), 500, 500, "authored per army"); number(source.get("authored_total_soldiers"), 3000, 3000, "authored total");
        ObjectNode soldiers = exact(root.get("soldiers"), Set.of("current_soldiers_observable", "observed_current_soldiers", "pre_soldiers_observable", "observed_pre_soldiers", "proven_soldier_loss_observable", "proven_soldiers_lost"), "generic soldiers");
        long current = nonnegative(soldiers.get("observed_current_soldiers"), "current total");
        require(bool(soldiers.get("current_soldiers_observable"), "current observable") && !bool(soldiers.get("pre_soldiers_observable"), "pre observable")
                && soldiers.get("observed_pre_soldiers").isNull() && !bool(soldiers.get("proven_soldier_loss_observable"), "loss observable")
                && soldiers.get("proven_soldiers_lost").isNull(), "generic soldier evidence overclaim");
        ObjectNode cleanup = exact(root.get("cleanup"), Set.of("observable", "status"), "cleanup");
        boolean observed = bool(cleanup.get("observable"), "cleanup observable");
        if (observed) {
            state(cleanup.get("status"), "cleanup status");
            ObjectNode post = exact(root.get("postwar_frame"), Set.of("snapshot_revision", "native_revision", "date_raw", "paused", "frozen_war_id", "frozen_war_absent_from_active_wars"), "cleanup post frame");
            require(bool(post.get("paused"), "post paused") && bool(post.get("frozen_war_absent_from_active_wars"), "old war absent")
                    && fullId(post.get("frozen_war_id"), "frozen war") == war, "cleanup post frame differs");
            uint64(post.get("snapshot_revision")); uint64(post.get("native_revision")); i32(post.get("date_raw"), "post date");
        } else require(root.get("postwar_frame").isNull() && cleanup.get("status").isNull(), "unobserved cleanup cannot publish frame");
        var regiments = array(root.get("regiments"), "generic regiments"); require(!regiments.isEmpty(), "generic regiments empty");
        Set<Integer> persistent = new HashSet<>(), currents = new HashSet<>(); BigInteger total = BigInteger.ZERO; boolean anyAlive = false;
        for (JsonNode raw : regiments) {
            ObjectNode regiment = exact(raw, Set.of("persistent_regiment_id", "bound_war_id", "war_keep_on_attacker_victory", "current_soldiers", "postwar_persistent_state", "composition_rows"), "generic regiment");
            require(persistent.add(fullId(regiment.get("persistent_regiment_id"), "persistent regiment")) && fullId(regiment.get("bound_war_id"), "bound war") == war
                    && !bool(regiment.get("war_keep_on_attacker_victory"), "keep after victory"), "generic regiment selector differs");
            long regimentTotal = nonnegative(regiment.get("current_soldiers"), "regiment total"); BigInteger sum = BigInteger.ZERO;
            if (observed) anyAlive |= state(regiment.get("postwar_persistent_state"), "persistent state").equals("still_alive");
            else require(regiment.get("postwar_persistent_state").isNull(), "active regiment invented post state");
            var rows = array(regiment.get("composition_rows"), "composition rows"); require(rows.size() == 7, "exact seven composition rows required");
            for (int index = 0; index < rows.size(); index++) {
                ObjectNode row = exact(rows.get(index), Set.of("composition_ordinal", "current_army_regiment_id", "raised_carmy_id", "current_soldiers", "current_army_regiment_state", "raised_carmy_state", "frozen_carmy_roster_evidence"), "composition row");
                number(row.get("composition_ordinal"), index, index, "composition ordinal");
                if (row.get("current_army_regiment_id").isNull()) {
                    require(row.get("raised_carmy_id").isNull() && row.get("current_soldiers").isNull(), "absent current row differs");
                    for (String key : List.of("current_army_regiment_state", "raised_carmy_state", "frozen_carmy_roster_evidence"))
                        require(observed ? text(row.get(key), key).equals("not_present") : row.get(key).isNull(), "absent cleanup row differs");
                    continue;
                }
                require(currents.add(fullId(row.get("current_army_regiment_id"), "current regiment")), "duplicate current regiment");
                fullId(row.get("raised_carmy_id"), "raised CArmy");
                sum = sum.add(BigInteger.valueOf(number(row.get("current_soldiers"), 0, Integer.MAX_VALUE, "row soldiers")));
                if (observed) {
                    String currentState = state(row.get("current_army_regiment_state"), "current state"), armyState = state(row.get("raised_carmy_state"), "army state"), roster = text(row.get("frozen_carmy_roster_evidence"), "roster");
                    require(armyState.equals("destroyed") ? roster.equals("frozen_army_destroyed") : Set.of("detached", "still_attached").contains(roster), "cleanup roster differs");
                    require(!currentState.equals("destroyed") || !roster.equals("still_attached"), "destroyed regiment remains attached");
                    anyAlive |= currentState.equals("still_alive");
                } else for (String key : List.of("current_army_regiment_state", "raised_carmy_state", "frozen_carmy_roster_evidence")) require(row.get(key).isNull(), "active row invented cleanup");
            }
            require(sum.equals(BigInteger.valueOf(regimentTotal)), "regiment soldier sum differs"); total = total.add(sum);
        }
        require(total.equals(BigInteger.valueOf(current)), "generic total soldier sum differs");
        if (observed) require(text(cleanup.get("status"), "cleanup").equals("still_alive") == anyAlive, "aggregate cleanup differs");
        ObjectNode readiness = exact(root.get("readiness"), Set.of("exact_raiktor_war_context_ready", "generic_war_bound_identity_ready", "current_soldiers_ready", "postwar_cleanup_ready", "source_specific_attribution_ready", "pre_soldiers_ready", "proven_soldier_loss_ready", "independently_visible_value_ready", "raiktor_source_specific_domain_ready"), "generic readiness");
        for (String key : List.of("exact_raiktor_war_context_ready", "generic_war_bound_identity_ready", "current_soldiers_ready", "independently_visible_value_ready")) require(bool(readiness.get(key), key), "generic visible readiness differs");
        require(bool(readiness.get("postwar_cleanup_ready"), "cleanup ready") == observed, "cleanup readiness differs");
        for (String key : List.of("source_specific_attribution_ready", "pre_soldiers_ready", "proven_soldier_loss_ready", "raiktor_source_specific_domain_ready")) require(!bool(readiness.get(key), key), "generic source attribution overclaim");
        return root.deepCopy();
    }
    public static ObjectNode normalizeCleanup(JsonNode raw, Frame active, BigInteger postPublic, BigInteger postNative, int postDate) {
        ObjectNode wire = exact(raw, Set.of("step", "accepted", "query_sequence", "snapshot_revision", "raiktor_war_bound_loss_cleanup", "backend_id"), "cleanup wire");
        require(text(wire.get("step"), "cleanup step").equals("query-raiktor-war-bound-loss-cleanup-v1-" + active.warId())
                && bool(wire.get("accepted"), "cleanup accepted") && text(wire.get("backend_id"), "cleanup backend").equals("native-headless"), "cleanup wire identity differs");
        positiveUnbounded(wire.get("query_sequence"), "cleanup sequence"); require(integer(wire.get("snapshot_revision"), "cleanup revision").equals(postNative), "cleanup native revision differs");
        ObjectNode normalized = normalizeGeneric(wire.get("raiktor_war_bound_loss_cleanup"), active.nativeStamped());
        ObjectNode post = object(normalized.get("postwar_frame"), "cleanup native post");
        require(uint64(post.get("snapshot_revision")).equals(postNative) && uint64(post.get("native_revision")).equals(postNative)
                && i32(post.get("date_raw"), "cleanup native date") == postDate && bool(post.get("paused"), "cleanup paused")
                && fullId(post.get("frozen_war_id"), "cleanup frozen war") == active.warId() && bool(post.get("frozen_war_absent_from_active_wars"), "cleanup old war absent"), "cleanup native post frame differs");
        object(normalized.get("active_frame"), "rebound active").put("snapshot_revision", active.publicRevision()); post.put("snapshot_revision", postPublic);
        normalized = normalizeGeneric(normalized, active);
        ObjectNode result = StrictJson.object(); result.set("query_sequence", wire.get("query_sequence")); result.set("snapshot_revision", wire.get("snapshot_revision")); result.set("observation", normalized); return result;
    }
    public static ObjectNode normalizeCapture(JsonNode raw, String captureSha256) {
        require(captureSha256 != null && captureSha256.matches("[0-9A-F]{64}"), "capture SHA must remain uppercase");
        ObjectNode capture = object(raw, "source capture");
        require(text(capture.get("schema"), "capture schema").equals("raiktor-war-bound-private-capture-v1") && text(capture.get("status"), "capture status").equals("private_test_only")
                && text(capture.get("result"), "capture result").equals("GREEN") && text(capture.get("reason"), "capture reason").equals("six-action-bound-source-executions-captured")
                && text(capture.get("exe_sha256"), "capture EXE").equals(CAPTURE_EXE) && text(capture.get("arm_proof_sha256"), "capture ARM").equals(ARM_SHA)
                && hex(capture.get("observation_stop_rva")).equals("0x2e7f951") && hex(capture.get("observation_window_end_rva_exclusive")).equals("0x2e7f9a6")
                && text(capture.get("event_definition_key"), "source event").equals("bookmark.1071") && text(capture.get("option_key"), "source option").equals("bookmark.1071.a"), "historical source capture boundary differs");
        for (String key : List.of("read_only", "breakpoint_installed", "original_breakpoint_byte_restored", "attach_mode", "debugger_detached")) require(bool(capture.get(key), key), "source capture actual flag differs");
        for (String key : List.of("public_bridge_abi_changed", "production_detour_installed", "readiness_promotion", "process_terminated")) require(!bool(capture.get(key), key), "source capture boundary promoted");
        number(capture.get("option_index"), 0, 0, "source option"); number(capture.get("source_execution_count"), 6, 6, "source execution count");
        BigInteger pid = positiveUnbounded(capture.get("pid"), "capture PID"); String image = hex(capture.get("image_base")); int war = nonnegativeId(capture.get("exact_raiktor_war_id"), "source war");
        var rows = array(capture.get("executions"), "source executions"); require(rows.size() == 6, "six source rows required");
        Set<String> nodes = new HashSet<>(); TreeSet<Integer> armies = new TreeSet<>(), current = new TreeSet<>(), persistent = new TreeSet<>();
        ObjectNode sourceSet = StrictJson.object().put("war_id", war); var executions = sourceSet.putArray("executions"); BigInteger measured = BigInteger.ZERO; String name = null;
        for (int index = 0; index < rows.size(); index++) {
            ObjectNode row = object(rows.get(index), "source execution"); number(row.get("sequence"), index + 1, index + 1, "source sequence");
            String loaded = hex(row.get("loaded_node")), created = hex(row.get("created_army")), evaluated = text(row.get("evaluated_name"), "source evaluated name");
            int army = nonnegativeId(row.get("army_generation_id"), "source army");
            require(nonnegativeId(row.get("war_id"), "row source war") == war && nodes.add(loaded) && armies.add(army) && (name == null || name.equals(evaluated)), "source execution identities differ"); name = evaluated;
            ObjectNode out = StrictJson.object().put("sequence", index + 1).put("thread_id", positiveUnbounded(row.get("thread_id"), "source thread")).put("loaded_node", loaded).put("created_army", created).put("army_generation_id", army).put("war_id", war).put("evaluated_name", evaluated);
            Set<Integer> executionCurrent = new HashSet<>(), mapped = new HashSet<>(); BigInteger executionSoldiers = BigInteger.ZERO;
            var currentRows = array(row.get("current_regiments"), "created current regiments");
            var persistentRows = array(row.get("persistent_regiments"), "created persistent regiments");
            require(!currentRows.isEmpty() && !persistentRows.isEmpty(), "source generation rows empty"); var currentsOut = out.putArray("current_regiments");
            for (JsonNode item : currentRows) {
                ObjectNode regiment = object(item, "source current regiment"); int id = nonnegativeId(regiment.get("generation_id"), "created current generation"); BigInteger soldiers = nonnegativeUnbounded(regiment.get("current_soldiers"), "created soldiers");
                require(current.add(id), "source current generation duplicated"); executionCurrent.add(id); executionSoldiers = executionSoldiers.add(soldiers);
                currentsOut.addObject().put("generation_id", id).put("current_soldiers", soldiers);
            }
            BigInteger initial = nonnegativeUnbounded(row.get("initial_soldiers"), "initial soldiers"); require(initial.equals(executionSoldiers), "source execution soldier sum differs");
            out.put("initial_soldiers", initial); var persistentOut = out.putArray("persistent_regiments");
            for (JsonNode item : persistentRows) {
                ObjectNode regiment = object(item, "source persistent regiment"); int id = nonnegativeId(regiment.get("generation_id"), "created persistent generation");
                require(persistent.add(id) && nonnegativeId(regiment.get("war_id"), "persistent source war") == war, "persistent source identity differs");
                var mapping = array(regiment.get("current_regiment_ids"), "persistent current mapping"); require(!mapping.isEmpty(), "source mapping empty");
                Set<Integer> local = new HashSet<>(); ObjectNode target = persistentOut.addObject().put("generation_id", id).put("war_id", war); var ids = target.putArray("current_regiment_ids");
                for (JsonNode value : mapping) { int currentId = nonnegativeId(value, "mapped current"); require(local.add(currentId) && mapped.add(currentId), "duplicate source mapping"); ids.add(currentId); }
            }
            require(mapped.equals(executionCurrent), "persistent/current source mapping differs"); measured = measured.add(initial); executions.add(out);
        }
        var persistentsOut = sourceSet.putArray("persistent_generation_ids"); persistent.forEach(persistentsOut::add);
        var currentsOut = sourceSet.putArray("current_generation_ids"); current.forEach(currentsOut::add);
        var armiesOut = sourceSet.putArray("army_generation_ids"); armies.forEach(armiesOut::add); sourceSet.put("measured_initial_soldiers", measured);
        ObjectNode result = StrictJson.object().put("schema_version", 1).put("contract", "raiktor-source-specific-war-loss-attribution-provider-v1").put("status", "normalized_private_capture")
                .put("capture_sha256", captureSha256).put("exact_build_sha256", CAPTURE_EXE).put("capture_pid", pid).put("image_base", image).put("source_set_sha256", hash(sourceSet));
        result.set("source_set", sourceSet); ObjectNode ready = result.putObject("readiness");
        for (String key : List.of("exact_callsite_shape_ready", "action_arm_bound", "six_source_executions_ready", "source_origin_shape_ready", "measured_initial_soldiers_ready")) ready.put(key, true);
        for (String key : List.of("private_live_evidence_classified", "action_bound_current_ready", "postwar_cleanup_ready", "source_specific_loss_ready", "comparison_input_ready")) ready.put(key, false);
        ObjectNode boundary = result.putObject("boundaries");
        for (String key : List.of("evaluated_name_is_standalone_selector", "authored_3000_used", "generic_r3_rows_retroactively_attributed", "public_readiness_promoted", "action_readiness_promoted", "decision_ready", "automatic_surrender_ready", "gen034_closed")) boundary.put(key, false);
        return result;
    }
    static Identity sourceIdentity(ObjectNode source) {
        ObjectNode set = object(source.get("source_set"), "normalized source set");
        return new Identity(i32(set.get("war_id"), "source war"), ids(set.get("persistent_generation_ids")), ids(set.get("current_generation_ids")), ids(set.get("army_generation_ids")));
    }
    static Identity observationIdentity(ObjectNode observation) {
        TreeSet<Integer> persistent = new TreeSet<>(), current = new TreeSet<>(), armies = new TreeSet<>();
        for (JsonNode value : array(observation.get("regiments"), "normalized regiments")) {
            ObjectNode regiment = object(value, "normalized regiment"); persistent.add(i32(regiment.get("persistent_regiment_id"), "persistent ID"));
            for (JsonNode row : array(regiment.get("composition_rows"), "normalized composition")) if (!row.get("current_army_regiment_id").isNull()) {
                current.add(i32(row.get("current_army_regiment_id"), "current ID")); armies.add(i32(row.get("raised_carmy_id"), "army ID"));
            }
        }
        return new Identity(i32(observation.get("war_id"), "war"), List.copyOf(persistent), List.copyOf(current), List.copyOf(armies));
    }
    private static List<Integer> ids(JsonNode raw) { return java.util.stream.StreamSupport.stream(array(raw, "generation IDs").spliterator(), false).map(n -> i32(n, "generation ID")).toList(); }
    private static BigInteger uint64(JsonNode value) { return StrictJson.integer(value, BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static BigInteger positiveUnbounded(JsonNode value, String name) { BigInteger n = integer(value, name); require(n.signum() > 0, name + " must be positive"); return n; }
    private static BigInteger nonnegativeUnbounded(JsonNode value, String name) { BigInteger n = integer(value, name); require(n.signum() >= 0, name + " must be nonnegative"); return n; }
    private static int nonnegativeId(JsonNode value, String name) { return Math.toIntExact(number(value, 0, Integer.MAX_VALUE, name)); }
    private static String state(JsonNode value, String name) { String n = text(value, name); require(Set.of("destroyed", "still_alive").contains(n), name + " unknown"); return n; }
    private static String hex(JsonNode value) {
        String text = text(value, "hex address"); require(text.matches("0x[0-9A-Fa-f]+"), "hex address shape");
        BigInteger n = new BigInteger(text.substring(2), 16); require(n.signum() > 0 && n.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 hex address"); return "0x" + n.toString(16);
    }
}

