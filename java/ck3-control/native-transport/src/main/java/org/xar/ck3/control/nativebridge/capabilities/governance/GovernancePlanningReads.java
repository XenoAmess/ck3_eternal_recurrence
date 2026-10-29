package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksCodec;
import org.xar.ck3.control.governance.lifestylesource.LifestyleSourceFacts;
import org.xar.ck3.control.governance.lifestylesource.LifestylePredicateSourceCodec;
import org.xar.ck3.control.governance.lifestylesource.LifestyleTriggerFrontierCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real LIFE/Crown native encoders and frame projection. Public publication IDs never enter native wire fields. */
public final class GovernancePlanningReads {
    public static final String FORMAL = "private-query-player-lifestyle-formal-v1";
    public static final String STATE = "private-query-player-lifestyle-current-state-v1";
    public static final String WEALTH = "private-query-player-lifestyle-stock-focus-v1";
    public static final String MARTIAL = "private-query-player-lifestyle-martial-authority-v1";
    public static final String CROWN = "query-realm-law-crown-action-v1-private";
    public record Sources(ExactRef lifestyle, ExactRef crown) { }
    private final ReadContract<OpportunityJson.Obj> formal, state, wealth, martial, crown;
    public GovernancePlanningReads(Sources sources, String version, String sha256) {
        CouncilCodec.requireBuild(version, sha256);
        formal = contract(FORMAL, sources.lifestyle(), version, sha256); state = contract(STATE, sources.lifestyle(), version, sha256);
        wealth = contract(WEALTH, sources.lifestyle(), version, sha256); martial = contract(MARTIAL, sources.lifestyle(), version, sha256);
        crown = contract(CROWN, sources.crown(), version, sha256);
    }
    public ReadContract<OpportunityJson.Obj> formal() { return formal; }
    public ReadContract<OpportunityJson.Obj> state() { return state; }
    public ReadContract<OpportunityJson.Obj> focus(String target) {
        return switch (target) { case "stewardship_wealth_focus" -> wealth; case "martial_authority_focus" -> martial;
            default -> throw new IllegalArgumentException("focus outside original native coverage"); };
    }
    public ReadContract<OpportunityJson.Obj> crown() { return crown; }
    public List<ReadContract<?>> all() { return List.of(formal, state, wealth, martial, crown); }
    private static ReadContract<OpportunityJson.Obj> contract(String step, ExactRef source, String version, String sha256) {
        return new ReadContract<>("governance.planning." + step, new OperationKey(step), Optional.empty(), step,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, source,
                request -> {
                    StrictJson.require(request.arguments().members().isEmpty(), "native governance read takes no caller wire arguments");
                    var frame = request.before().frame(); var id = frame.identity();
                    ObjectNode fields = StrictJson.object().put("expected_date_raw", id.dateRaw()).put("expected_player_character_id", id.player());
                    if (!step.equals(CROWN)) fields.put("expected_snapshot_id", "native:" + id.nativeRevision()).put("episode_run_id", frame.episodeRunId());
                    return new NativeRequest(step, Optional.empty(), new RawJson(StrictJson.canonical(fields)));
                }, receipt -> {
                    ObjectNode result = original(receipt);
                    ObjectNode normalized = step.equals(CROWN) ? crown(result, receipt.request(), version, sha256)
                            : step.equals(FORMAL) || step.equals(STATE) ? life(result, receipt.request(), step) : focus(result, receipt.request(), step);
                    return (OpportunityJson.Obj) OpportunityJson.parse(StrictJson.canonical(normalized));
                });
    }
    private static ObjectNode original(PlanningReadReceipt receipt) {
        var full = StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
        StrictJson.require(StrictJson.text(full.get("type")).equals("command_result") && StrictJson.integer(full.get("protocol_version"), 1, 1) == 1
                && StrictJson.text(full.get("request_id")).equals(receipt.requestId()) && receipt.original().nativeOk(), "native governance query original correlation drift");
        StrictJson.trueValue(full.get("ok"));
        JsonNode token = StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes());
        StrictJson.require(token.equals(full.get("result")), "native governance full original/token mismatch");
        return CouncilCodec.object(token);
    }
    public static ObjectNode crown(ObjectNode result, PlanningReadRequest request, String version, String sha256) {
        StrictJson.object(result, Set.of("step", "accepted", "private_build", "advertised", "backend_id", "game_version", "executable_sha256", "read_only", "status", "observation", "ack", "receipt"));
        equal(result, "step", CROWN); equal(result, "backend_id", "native-headless"); equal(result, "game_version", version); equal(result, "executable_sha256", sha256);
        CouncilCodec.requireBuild(version, sha256); StrictJson.trueValue(result.get("accepted")); StrictJson.trueValue(result.get("private_build")); StrictJson.trueValue(result.get("read_only"));
        StrictJson.require(!CouncilCodec.bool(result.get("advertised")) && result.get("ack").isNull() && result.get("receipt").isNull(), "Crown read carried mutation/receipt material");
        equal(result, "status", "available"); ObjectNode observed = StrictJson.object(result.get("observation"), Set.of("available", "paused", "snapshot_revision", "native_snapshot_revision", "proof_epoch", "date_raw", "player_character_id", "group_key", "active_law_key", "candidates", "resources", "title_successors"));
        var frame = request.before().frame(); var id = frame.identity();
        StrictJson.trueValue(observed.get("available")); StrictJson.trueValue(observed.get("paused")); equal(observed, "group_key", "crown_authority");
        number(observed, "snapshot_revision", id.nativeRevision()); number(observed, "date_raw", id.dateRaw()); number(observed, "player_character_id", id.player());
        CouncilCodec.u64(observed.get("native_snapshot_revision"), true); CouncilCodec.u64(observed.get("proof_epoch"), true);
        ObjectNode normalized = observed.deepCopy().put("schema", CrownAuthorityPolicy.READ_SCHEMA)
                .put("exact_ck3_build", version).put("exe_sha256", sha256).put("read_only", true).put("advertised", false)
                .put("queried_snapshot_id", frame.snapshotId()).put("queried_revision", frame.revision()).put("queried_native_revision", id.nativeRevision());
        // The sole shared typed consumer validates all currency, title, candidate, signed amount and final-gate fields.
        var decoded = CrownAuthorityCodec.decodeReadback(StrictJson.canonical(normalized));
        StrictJson.require(decoded.resources().size() == 5 && decoded.candidates().size() >= 1 && decoded.candidates().size() <= 24, "complete bounded Crown source required");
        var keys = new HashSet<CrownAuthorityPolicy.Currency>();
        for (var balance : decoded.resources()) { StrictJson.require(keys.add(balance.currency()), "duplicate Crown wallet"); signed(balance.amountRaw()); }
        var laws = new HashSet<String>(); int active = 0;
        for (var candidate : decoded.candidates()) {
            StrictJson.require(laws.add(candidate.lawKey()) && candidate.lawKey().startsWith("crown_authority_") && candidate.costs().size() <= 6, "duplicate/invalid Crown candidate");
            if (candidate.active()) { active++; StrictJson.require(candidate.lawKey().equals(decoded.activeLawKey()), "Crown active candidate differs"); }
            var currencies = new HashSet<CrownAuthorityPolicy.Currency>();
            for (var cost : candidate.costs()) { StrictJson.require(currencies.add(cost.currency()) && cost.costRaw().signum() >= 0, "duplicate/negative Crown quote"); signed(cost.costRaw()); }
        }
        StrictJson.require(active == 1, "one independently observed active Crown law required");
        org.xar.ck3.control.application.effects.NativeGovernanceEffects.validateTitles(observed.get("title_successors"));
        return normalized;
    }
    public static ObjectNode life(ObjectNode result, PlanningReadRequest request, String step) {
        equal(result, "step", step); StrictJson.trueValue(result.get("private_build")); StrictJson.require(!CouncilCodec.bool(result.get("advertised")), "LIFE private envelope changed");
        equal(result, "status", "available"); var frame = request.before().frame(); var id = frame.identity(); equal(result, "episode_run_id", frame.episodeRunId());
        ObjectNode snapshot = CouncilCodec.object(result.get("snapshot")); equal(snapshot, "status", "available"); nativeBinding(snapshot, request, true); validateLifeSnapshot(snapshot);
        ObjectNode projected = snapshot.deepCopy().put("snapshot_id", frame.snapshotId()).put("public_revision", frame.revision()).put("episode_run_id", frame.episodeRunId());
        ObjectNode normalized = StrictJson.object().put("status", "available").put("step", step).put("episode_run_id", frame.episodeRunId());
        if (step.equals(FORMAL)) {
            normalized.set("formal_precondition_status", result.get("formal_precondition_status")); StrictJson.text(result.get("formal_precondition_status"));
            if (result.hasNonNull("all_lifestyle_progress_v3")) {
                var progress = CouncilCodec.object(result.get("all_lifestyle_progress_v3")); nativeBinding(progress, request, false); equal(progress, "episode_run_id", frame.episodeRunId());
                projected.set("all_lifestyle_progress_v3", progress.deepCopy().put("snapshot_id", frame.snapshotId()));
                ObjectNode wrapper = StrictJson.object().put("schema", LifestylePerksCodec.INPUT_SCHEMA); wrapper.set("snapshot", projected); wrapper.set("owned", projected.get("owned_perk_keys"));
                ObjectNode binding = wrapper.putObject("binding");
                for (String key : List.of("snapshot_id", "episode_run_id", "public_revision", "native_revision", "proof_epoch", "date_raw", "player_character_id")) binding.set("expected_" + key, projected.get(key));
                LifestylePerksCodec.decode(StrictJson.canonical(wrapper));
            }
        } else normalized.put("formal_precondition_status", "state_only");
        normalized.set("snapshot", projected); normalized.set("source_frame", source(request));
        normalized.set("native_source_frame", StrictJson.object().put("snapshot_id", "native:" + id.nativeRevision()).put("public_revision", id.nativeRevision()).put("native_revision", id.nativeRevision()));
        appendSourceFacts(normalized,result,request);
        return normalized;
    }
    /** Actual response -> unique shared source decoders -> typed fact JSON; raw input tokens remain separate. */
    public static void appendSourceFacts(ObjectNode normalized,ObjectNode original,PlanningReadRequest request) {
        var id=request.before().frame().identity();
        var binding=LifestyleSourceFacts.Binding.exact("native:"+id.nativeRevision(),id.nativeRevision(),id.dateRaw().intValueExact(),id.player(),Optional.empty());
        for(String key:List.of(LifestylePredicateSourceCodec.WIRE_KEY,LifestyleTriggerFrontierCodec.WIRE_KEY))if(original.has(key))normalized.set(key,original.get(key).deepCopy());
        StrictJson.require(!original.has(LifestylePredicateSourceCodec.FACTS_KEY)&&!original.has(LifestyleTriggerFrontierCodec.FACTS_KEY),"native input cannot supply an already decoded facts sibling");
        if(original.hasNonNull(LifestylePredicateSourceCodec.WIRE_KEY))normalized.set(LifestylePredicateSourceCodec.FACTS_KEY,
                LifestylePredicateSourceCodec.factsNode(LifestylePredicateSourceCodec.decode(original.get(LifestylePredicateSourceCodec.WIRE_KEY),binding)));
        if(original.hasNonNull(LifestyleTriggerFrontierCodec.WIRE_KEY))normalized.set(LifestyleTriggerFrontierCodec.FACTS_KEY,
                LifestyleTriggerFrontierCodec.factsNode(LifestyleTriggerFrontierCodec.decode(original.get(LifestyleTriggerFrontierCodec.WIRE_KEY),binding)));
    }
    public static ObjectNode focus(ObjectNode result, PlanningReadRequest request, String step) {
        equal(result, "step", step); StrictJson.trueValue(result.get("private_build")); StrictJson.trueValue(result.get("read_only")); StrictJson.trueValue(result.get("policy_scoped"));
        StrictJson.require(!CouncilCodec.bool(result.get("advertised")), "focus advertised private source");
        var frame = request.before().frame(); equal(result, "snapshot_id", "native:" + frame.identity().nativeRevision()); equal(result, "episode_run_id", frame.episodeRunId());
        String target = step.equals(WEALTH) ? "stewardship_wealth_focus" : "martial_authority_focus", lifestyle = step.equals(WEALTH) ? "stewardship_lifestyle" : "martial_lifestyle";
        equal(result, "target_key", target); equal(result, "target_lifestyle_key", lifestyle);
        String status = CouncilCodec.text(result, "status"); StrictJson.require(Set.of("observed_native_legal", "observed_native_illegal").contains(status)
                && CouncilCodec.bool(result.get("native_legal")) == status.equals("observed_native_legal"), "focus final legality missing or inconsistent");
        CouncilCodec.u64(result.get("scanned_database_rows"), true);
        ObjectNode progress = StrictJson.object(result.get("target_lifestyle_progress"), Set.of("presence", "source", "xp_total_raw", "xp_within_level_raw", "xp_per_level", "unspent_perk_points", "used_perk_points"));
        equal(progress, "presence", "present"); equal(progress, "source", "exact_native_getters");
        for (String key : List.of("xp_total_raw", "xp_within_level_raw", "unspent_perk_points", "used_perk_points")) StrictJson.integer(progress.get(key), BigInteger.ZERO, BigInteger.valueOf(Long.MAX_VALUE));
        BigInteger perLevel = StrictJson.integer(progress.get("xp_per_level"), BigInteger.ONE, BigInteger.valueOf(Long.MAX_VALUE));
        StrictJson.require(progress.get("xp_within_level_raw").bigIntegerValue().compareTo(perLevel.multiply(BigInteger.valueOf(100000))) < 0, "focus within-level XP outside native fixed scale");
        ObjectNode projected = result.deepCopy().put("status", "observed"); projected.set("source_frame", source(request));
        return projected;
    }
    public static ObjectNode combine(ObjectNode state, ObjectNode focus) {
        equal(state, "status", "available"); equal(focus, "status", "observed");
        boolean nativeLegal = CouncilCodec.bool(focus.get("native_legal"));
        StrictJson.require(state.get("source_frame").equals(focus.get("source_frame")) && state.get("episode_run_id").equals(focus.get("episode_run_id")), "LIFE state/focus lost their exact shared frame");
        if (!nativeLegal) {
            ObjectNode unavailable = StrictJson.object().put("status", "stock_focus_readback_red");
            unavailable.set("state", state.deepCopy()); unavailable.set("focus", focus.deepCopy()); return unavailable;
        }
        ObjectNode snapshot = CouncilCodec.object(state.get("snapshot")).deepCopy();
        ObjectNode ready = CouncilCodec.object(snapshot.get("readiness")).deepCopy().put("legal_focus_candidates_ready", true); snapshot.set("readiness", ready);
        ObjectNode collection = StrictJson.object().put("status", "available").put("policy_scoped", true);
        collection.putArray("items").addObject().put("key", CouncilCodec.text(focus, "target_key")).put("lifestyle_key", CouncilCodec.text(focus, "target_lifestyle_key"));
        snapshot.set("legal_focus_candidates", collection); snapshot.set("target_lifestyle_progress", CouncilCodec.object(focus.get("target_lifestyle_progress")).deepCopy().put("lifestyle_key", CouncilCodec.text(focus, "target_lifestyle_key")));
        ObjectNode result = state.deepCopy().put("status", "stock_focus_available").put("step", CouncilCodec.text(focus, "step")).put("formal_precondition_status", "stock_focus_ready");
        result.set("snapshot", snapshot); result.set("focus_query", focus); return result;
    }
    private static ObjectNode source(PlanningReadRequest request) { var frame = request.before().frame(); var id = frame.identity(); return StrictJson.object().put("snapshot_id", frame.snapshotId())
            .put("revision", frame.revision()).put("native_revision", id.nativeRevision()).put("date_raw", id.dateRaw()).put("player_character_id", id.player()); }
    private static void nativeBinding(ObjectNode value, PlanningReadRequest request, boolean snapshot) {
        var id = request.before().frame().identity(); equal(value, "snapshot_id", "native:" + id.nativeRevision()); number(value, "native_revision", id.nativeRevision());
        number(value, "date_raw", id.dateRaw()); number(value, "player_character_id", id.player());
        if (snapshot) { number(value, "public_revision", id.nativeRevision()); number(value, "proof_epoch", id.nativeRevision()); }
    }
    private static void validateLifeSnapshot(ObjectNode snapshot) {
        StrictJson.object(snapshot, Set.of("private_build", "advertised", "status", "snapshot_id", "public_revision", "native_revision", "proof_epoch", "date_raw", "player_character_id", "current_focus", "current_lifestyle_progress", "owned_perk_keys", "actor_traits", "legal_focus_candidates", "legal_perk_candidates", "readiness"));
        StrictJson.trueValue(snapshot.get("private_build")); StrictJson.require(!CouncilCodec.bool(snapshot.get("advertised")), "LIFE snapshot private provenance changed");
        ObjectNode focus = CouncilCodec.object(snapshot.get("current_focus")); String presence = CouncilCodec.text(focus, "presence");
        StrictJson.object(focus, presence.equals("present") ? Set.of("presence", "key", "lifestyle_key") : Set.of("presence"));
        StrictJson.require(Set.of("present", "absent").contains(presence), "LIFE focus presence is unavailable, not absent");
        if (presence.equals("present")) { StrictJson.text(focus.get("key")); StrictJson.text(focus.get("lifestyle_key")); }
        ObjectNode progress = CouncilCodec.object(snapshot.get("current_lifestyle_progress")); String progressPresence = CouncilCodec.text(progress, "presence");
        StrictJson.require(Set.of("present", "absent").contains(progressPresence), "LIFE progress presence invalid");
        StrictJson.object(progress, progressPresence.equals("present") ? Set.of("presence", "lifestyle_key", "xp_total_raw", "xp_within_level_raw", "xp_per_level", "unspent_perk_points", "used_perk_points") : Set.of("presence"));
        if (progressPresence.equals("present")) {
            StrictJson.text(progress.get("lifestyle_key"));
            for (String key : List.of("xp_total_raw", "xp_within_level_raw", "unspent_perk_points", "used_perk_points")) StrictJson.integer(progress.get(key), BigInteger.ZERO, BigInteger.valueOf(Long.MAX_VALUE));
            BigInteger per = StrictJson.integer(progress.get("xp_per_level"), BigInteger.ONE, BigInteger.valueOf(Long.MAX_VALUE));
            StrictJson.require(progress.get("xp_within_level_raw").bigIntegerValue().compareTo(per.multiply(BigInteger.valueOf(100000))) < 0, "LIFE XP scale invalid");
        }
        strings(snapshot.get("owned_perk_keys"), 2048);
        ObjectNode traits = CouncilCodec.object(snapshot.get("actor_traits")); String status = CouncilCodec.text(traits, "status");
        StrictJson.require(Set.of("available", "unavailable").contains(status), "LIFE trait status invalid");
        StrictJson.object(traits, status.equals("available") ? Set.of("status", "observed_keys") : Set.of("status")); if (status.equals("available")) strings(traits.get("observed_keys"), 1024);
        ObjectNode readiness = StrictJson.object(snapshot.get("readiness"), Set.of("current_focus_ready", "lifestyle_progress_ready", "owned_perks_ready", "legal_focus_candidates_ready", "legal_perk_candidates_ready", "same_frame_ready"));
        readiness.forEach(CouncilCodec::bool);
        for (String key : List.of("legal_focus_candidates", "legal_perk_candidates")) {
            ObjectNode collection = CouncilCodec.object(snapshot.get(key)); String collectionStatus = CouncilCodec.text(collection, "status");
            StrictJson.require(Set.of("available", "unavailable").contains(collectionStatus), "LIFE candidate availability invalid");
            var fields = new HashSet<>(Set.of("status", "items")); if (collectionStatus.equals("unavailable")) fields.add("reason"); if (collection.has("scope")) { fields.add("scope"); equal(collection, "scope", "policy_target"); }
            StrictJson.object(collection, fields); if (collectionStatus.equals("unavailable")) StrictJson.text(collection.get("reason"));
            JsonNode items = collection.get("items"); StrictJson.require(items.isArray() && items.size() <= 2048 && (!collectionStatus.equals("unavailable") || items.isEmpty()), "LIFE candidate collection incomplete");
            var unique = new HashSet<String>(); for (JsonNode item : items) { ObjectNode candidate = StrictJson.object(item, Set.of("key", "lifestyle_key")); StrictJson.text(candidate.get("lifestyle_key")); StrictJson.require(unique.add(CouncilCodec.text(candidate, "key")), "duplicate LIFE candidate"); }
        }
    }
    private static void strings(JsonNode value, int maximum) { StrictJson.require(value != null && value.isArray() && value.size() <= maximum, "bounded exact string array required"); var unique = new HashSet<String>(); value.forEach(item -> StrictJson.require(unique.add(StrictJson.text(item)), "duplicate native key")); }
    private static void equal(ObjectNode value, String key, String expected) { StrictJson.require(CouncilCodec.text(value, key).equals(expected), "native governance field drift: " + key); }
    private static void number(ObjectNode value, String key, BigInteger expected) { StrictJson.require(value.has(key) && value.get(key).isIntegralNumber() && value.get(key).bigIntegerValue().equals(expected), "native governance integer/frame drift: " + key); }
    private static void signed(BigInteger value) { StrictJson.require(value.compareTo(BigInteger.valueOf(Long.MIN_VALUE)) >= 0 && value.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "native amount exceeds signed int64"); }
}
