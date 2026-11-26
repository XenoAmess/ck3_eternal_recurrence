package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeGovernanceEffects;
import org.xar.ck3.control.contracts.ExactCk3Build;
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
    private final ReadContract<OpportunityJson.Obj> formal, state, wealth, martial, crown, focusStateReconciliation;
    public GovernancePlanningReads(Sources sources, String version, String sha256) {
        CouncilCodec.requireBuild(version, sha256);
        formal = contract(FORMAL, sources.lifestyle(), version, sha256); state = contract(STATE, sources.lifestyle(), version, sha256);
        wealth = contract(WEALTH, sources.lifestyle(), version, sha256); martial = contract(MARTIAL, sources.lifestyle(), version, sha256);
        crown = contract(CROWN, sources.crown(), version, sha256);
        focusStateReconciliation = contract(STATE,sources.lifestyle(),version,sha256,ReadContract.GuardMode.RECONCILIATION_OBSERVATION);
    }
    public ReadContract<OpportunityJson.Obj> formal() { return formal; }
    public ReadContract<OpportunityJson.Obj> state() { return state; }
    public ReadContract<OpportunityJson.Obj> focusStateReconciliation() { return focusStateReconciliation; }
    public ReadContract<OpportunityJson.Obj> focus(String target) {
        return switch (target) { case "stewardship_wealth_focus" -> wealth; case "martial_authority_focus" -> martial;
            default -> throw new IllegalArgumentException("focus outside original native coverage"); };
    }
    public ReadContract<OpportunityJson.Obj> crown() { return crown; }
    public List<ReadContract<?>> all() { return List.of(formal, state, wealth, martial, crown, focusStateReconciliation); }
    private static ReadContract<OpportunityJson.Obj> contract(String step, ExactRef source, String version, String sha256) {
        return contract(step,source,version,sha256,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
    }
    private static ReadContract<OpportunityJson.Obj> contract(String step, ExactRef source, String version, String sha256,ReadContract.GuardMode guardMode) {
        StrictJson.require(guardMode==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP||guardMode==ReadContract.GuardMode.RECONCILIATION_OBSERVATION&&step.equals(STATE),
                "only original FOCUS current-state may use reconciliation governance profile");
        Function<PlanningReadReceipt, OpportunityJson.Obj> decoder = receipt -> {
            ObjectNode result = original(receipt);
            ObjectNode normalized = step.equals(CROWN) ? crown(result, receipt.request(), version, sha256)
                    : step.equals(FORMAL) || step.equals(STATE) ? life(result, receipt.request(), step) : focus(result, receipt.request(), step);
            return (OpportunityJson.Obj) OpportunityJson.parse(StrictJson.canonical(normalized));
        };
        String contractId=guardMode==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                ?NativeGovernanceEffects.FOCUS_STATE_CONTRACT:"governance.planning."+step;
        return new ReadContract<>(contractId, new OperationKey(step), Optional.empty(), step,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, guardMode, source,
                (request, requestId) -> {
                    StrictJson.require(request.arguments().members().isEmpty(), "native governance read takes no caller wire arguments");
                    var frame = readFrame(request).frame(); var id = frame.identity();
                    ObjectNode fields = StrictJson.object().put("expected_date_raw", id.dateRaw()).put("expected_player_character_id", id.player());
                    if (!step.equals(CROWN)) fields.put("expected_snapshot_id", "native:" + id.nativeRevision()).put("episode_run_id", NativeGovernanceEffects.lifestyleWireEpisode(readFrame(request)));
                    return new NativeRequest(step, Optional.empty(), new RawJson(StrictJson.canonical(fields)));
                },
                decoder,
                decoder);
    }
    private static org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity readFrame(PlanningReadRequest request) {
        if(request.origin() instanceof CommandOrigin.Reconciliation) {
            StrictJson.require(request.operation().value().equals(STATE),"only original FOCUS STATE may borrow reconciliation factual frame");
            return request.reconciliationBefore();
        }
        return request.before();
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
        var frame = readFrame(request).frame(); var id = frame.identity();
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
        equal(result, "status", "available"); var frame = readFrame(request).frame(); var id = frame.identity(); equal(result, "episode_run_id", NativeGovernanceEffects.lifestyleWireEpisode(readFrame(request)));
        ObjectNode snapshot = CouncilCodec.object(result.get("snapshot")); equal(snapshot, "status", "available"); nativeBinding(snapshot, request, true); validateLifeSnapshot(snapshot);
        ObjectNode projected = snapshot.deepCopy().put("snapshot_id", frame.snapshotId()).put("public_revision", frame.revision()).put("episode_run_id", frame.episodeRunId());
        ObjectNode normalized = StrictJson.object().put("status", "available").put("step", step).put("episode_run_id", frame.episodeRunId());
        if (step.equals(FORMAL)) {
            normalized.set("formal_precondition_status", result.get("formal_precondition_status")); StrictJson.text(result.get("formal_precondition_status"));
            if (result.hasNonNull("all_lifestyle_progress_v3")) {
                var progress = CouncilCodec.object(result.get("all_lifestyle_progress_v3")); nativeBinding(progress, request, false); equal(progress, "episode_run_id", NativeGovernanceEffects.lifestyleWireEpisode(readFrame(request)));
                projected.set("all_lifestyle_progress_v3", progress.deepCopy().put("snapshot_id", frame.snapshotId()).put("episode_run_id", frame.episodeRunId()));
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
        var id=readFrame(request).frame().identity();
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
        var frame = readFrame(request).frame(); equal(result, "snapshot_id", "native:" + frame.identity().nativeRevision()); equal(result, "episode_run_id", NativeGovernanceEffects.lifestyleWireEpisode(readFrame(request)));
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
        ObjectNode projected = result.deepCopy().put("status", "observed").put("episode_run_id", frame.episodeRunId()); projected.set("source_frame", source(request));
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
    private static ObjectNode source(PlanningReadRequest request) { var frame = readFrame(request).frame(); var id = frame.identity(); return StrictJson.object().put("snapshot_id", frame.snapshotId())
            .put("revision", frame.revision()).put("native_revision", id.nativeRevision()).put("date_raw", id.dateRaw()).put("player_character_id", id.player()); }
    private static void nativeBinding(ObjectNode value, PlanningReadRequest request, boolean snapshot) {
        var id = readFrame(request).frame().identity(); equal(value, "snapshot_id", "native:" + id.nativeRevision()); number(value, "native_revision", id.nativeRevision());
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
    /** Exact hotfix read-only DATA. This profile grants no legacy ROOT, governance or action authority. */
    public static final class OpeningReadProfile {
        public static final String ADAPTER="ck3-1.21.0-26757580-msvc-x64";
        public static final String VERSION="1.21.0";
        public static final String EXECUTABLE="BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79";
        private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
        private static final BigInteger U32=BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
        private static final BigInteger I32_MIN=BigInteger.valueOf(Integer.MIN_VALUE),I32_MAX=BigInteger.valueOf(Integer.MAX_VALUE);
        private static final Set<String> COMMON=Set.of("schema","status","unavailable_reason","read_only","full_governance_ready","action_ready",
                "native_revision","snapshot_id","date_raw","player_character_id","readiness","origin","provenance");
        public enum Kind {
            SCOPE("scope", "scope"), CURRENT("state", "current");
            private final String nativeName, dataName;
            Kind(String nativeName, String dataName) { this.nativeName = nativeName; this.dataName = dataName; }
            private String step(String build) { return "query-current-lifestyle-" + nativeName + "-" + build + "-v1"; }
            private String capability(String build) { return "game.query.current-lifestyle-" + nativeName + "." + build + ".v1"; }
            private String schema(String build) { return "xar.ck3.lifestyle-" + dataName + "." + build + ".v1"; }
            private String profile(String build) { return "ck3-" + build + "-lifestyle-" + dataName + "-v1"; }
            // Archived BB3 callers still name the original wire values.
            public String step() { return step(Protocol.BB3.number); }
            public String capability() { return capability(Protocol.BB3.number); }
            public String schema() { return schema(Protocol.BB3.number); }
            public String profile() { return profile(Protocol.BB3.number); }
        }
        private enum Protocol {
            BB3("26757580", ExactCk3Build.CK3_1210_STEAM_26757580),
            FULL111("26785313", ExactCk3Build.CK3_121003_STEAM_26785313_FULL111);
            private final String number;
            private final ExactCk3Build build;
            Protocol(String number, ExactCk3Build build) { this.number = number; this.build = build; }
        }
        private record DllIdentity(long bytes, String sha256) {
            private boolean matches(ExactRef actual) { return bytes == actual.bytes() && sha256.equals(actual.sha256()); }
        }
        // Add only a reviewed Full111 bridge that actually contains both Opening producers and the pinned reader/ABI.
        private static final List<DllIdentity> FULL111_PRODUCERS = List.of(
                new DllIdentity(21_515_776L, "f33eb6d59068ebd21ba78ef43d933222e15427352d2bb206bb60990152963c52"),
                new DllIdentity(21_523_968L, "db2a814aaa702b322a53e76512b8c80d71fc3249c71c9d31a674a436effaee86"));
        private static final SourcePins FULL111_PINS = new SourcePins(
                "d31b5b369f4e121009cdb3b941fc362992e8155782ac5a894daafd48c6f87cc9",
                "6db7725c631d02cbed843b7c0ebf085ac120448cb1719a5b46f9df0831f0f2b8");
        /** Exact separately frozen reader/ABI identity; syntactic pins alone never install a live producer. */
        public record SourcePins(String readerSourceSha256,String abiManifestSha256) {
            public SourcePins {
                StrictJson.require(readerSourceSha256!=null&&readerSourceSha256.matches("[0-9a-f]{64}")
                        &&abiManifestSha256!=null&&abiManifestSha256.matches("[0-9a-f]{64}"),"two exact lowercase source/ABI SHA256 pins required");
            }
        }
        public record Frame(BigInteger nativeRevision,BigInteger dateRaw,BigInteger playerCharacterId) {
            public Frame {
                range(nativeRevision,BigInteger.ONE,U64,"expected native revision");range(dateRaw,I32_MIN,I32_MAX,"expected native date");
                range(playerCharacterId,I32_MIN,I32_MAX,"expected complete character ID");
                StrictJson.require(!playerCharacterId.equals(BigInteger.valueOf(-1)),"absent character sentinel is not a complete actor");
            }
            public String snapshotId(){return "native:"+nativeRevision;}
        }
        public enum SourceKind { APPLICATION_MAIN_TICKET, OFFLINE_FIXTURE, UNAVAILABLE }
        public record Origin(SourceKind kind,Optional<BigInteger> ticketSequence,Optional<BigInteger> pumpEpoch,
                Optional<BigInteger> threadId,boolean mainOwnerObserved) {
            public Origin {
                java.util.Objects.requireNonNull(kind);ticketSequence=java.util.Objects.requireNonNull(ticketSequence);
                pumpEpoch=java.util.Objects.requireNonNull(pumpEpoch);threadId=java.util.Objects.requireNonNull(threadId);
                ticketSequence.ifPresent(v->range(v,BigInteger.ZERO,U64,"ticket sequence"));pumpEpoch.ifPresent(v->range(v,BigInteger.ZERO,U64,"pump epoch"));
                threadId.ifPresent(v->range(v,BigInteger.ZERO,U32,"thread ID"));
                if(kind==SourceKind.APPLICATION_MAIN_TICKET) {
                    StrictJson.require(mainOwnerObserved&&ticketSequence.filter(v->v.signum()>0).isPresent()
                            &&pumpEpoch.filter(v->v.signum()>0).isPresent()&&threadId.filter(v->v.signum()>0).isPresent(),
                            "application-main origin requires its actual positive ticket/pump/thread observations");
                } else StrictJson.require(!mainOwnerObserved,"offline or unavailable origin cannot claim a main owner");
            }
        }
        public record Government(String key,List<String> flags) {
            public Government {key=nonempty(key,"government key");flags=List.copyOf(flags);StrictJson.require(flags.size()<=4096,"bounded complete flag span required");
                flags.forEach(v->nonempty(v,"government flag"));}
        }
        public record FocusProgress(boolean present,Optional<String> focusKey,Optional<String> lifestyleKey,
                Optional<BigInteger> xpTotalRaw,Optional<BigInteger> xpWithinLevelRaw,Optional<BigInteger> xpPerLevel,
                Optional<BigInteger> unspentPerkPoints,Optional<BigInteger> usedPerkPoints) {
            public FocusProgress {
                java.util.Objects.requireNonNull(focusKey);java.util.Objects.requireNonNull(lifestyleKey);java.util.Objects.requireNonNull(xpTotalRaw);
                java.util.Objects.requireNonNull(xpWithinLevelRaw);java.util.Objects.requireNonNull(xpPerLevel);
                java.util.Objects.requireNonNull(unspentPerkPoints);java.util.Objects.requireNonNull(usedPerkPoints);
                if(present) {
                    nonempty(focusKey.orElseThrow(),"focus key");nonempty(lifestyleKey.orElseThrow(),"lifestyle key");
                    range(xpTotalRaw.orElseThrow(),BigInteger.ZERO,BigInteger.valueOf(Long.MAX_VALUE),"native total XP raw");
                    range(xpWithinLevelRaw.orElseThrow(),BigInteger.ZERO,BigInteger.valueOf(Long.MAX_VALUE),"native within-level XP raw");
                    range(xpPerLevel.orElseThrow(),BigInteger.ONE,I32_MAX,"observed native XP threshold");
                    StrictJson.require(xpWithinLevelRaw.orElseThrow().compareTo(xpPerLevel.orElseThrow().multiply(BigInteger.valueOf(100000)))<0,"observed within-level XP exceeds native fixed-scale remainder domain");
                    range(unspentPerkPoints.orElseThrow(),BigInteger.ZERO,I32_MAX,"observed native perk points");
                    range(usedPerkPoints.orElseThrow(),BigInteger.ZERO,I32_MAX,"observed native used perk points");
                } else StrictJson.require(focusKey.isEmpty()&&lifestyleKey.isEmpty()&&xpTotalRaw.isEmpty()&&xpWithinLevelRaw.isEmpty()
                        &&xpPerLevel.isEmpty()&&unspentPerkPoints.isEmpty()&&usedPerkPoints.isEmpty(),"known absence cannot carry invented focus/progress values");
            }
        }
        /** The parser is the sole constructor; original native bytes are retained separately from projections. */
        public static final class Data {
            private final Kind kind;private final boolean available;private final Optional<String> unavailableReason;
            private final Optional<Frame> frame;private final Optional<Government> government;private final Optional<FocusProgress> progress;
            private final Origin origin;private final RawJson original;
            private Data(Kind kind,boolean available,Optional<String> reason,Optional<Frame> frame,Optional<Government> government,
                    Optional<FocusProgress> progress,Origin origin,RawJson original) {
                this.kind=kind;this.available=available;this.unavailableReason=reason;this.frame=frame;this.government=government;
                this.progress=progress;this.origin=origin;this.original=original;
            }
            public Kind kind(){return kind;}public boolean available(){return available;}public Optional<String> unavailableReason(){return unavailableReason;}
            public Optional<Frame> frame(){return frame;}public Optional<Government> government(){return government;}
            public Optional<FocusProgress> progress(){return progress;}public Origin origin(){return origin;}public RawJson original(){return original;}
            /** Additional live receipt/owner/frame/deadline/catalog checks remain mandatory at the actual read binding. */
            public void requireApplicationMainOrigin(){StrictJson.require(origin.kind()==SourceKind.APPLICATION_MAIN_TICKET,"offline DATA cannot install a live opening read");}
        }
        /** Exact readonly producer combinations; each still needs real catalog/HELLO/owner/read guards. */
        public static Optional<OpeningReadProfile> selectQualified(String version,String executableSha256,ExactRef selectedDll) {
            if (selectedDll == null || !java.nio.file.Path.of(selectedDll.path()).isAbsolute()) return Optional.empty();
            if (Protocol.FULL111.build.matches(version, executableSha256))
                return FULL111_PRODUCERS.stream().filter(producer -> producer.matches(selectedDll)).findFirst()
                        .map(producer -> full111DataProfile());
            if (!Protocol.BB3.build.matches(version, executableSha256)) return Optional.empty();
            boolean opening56=selectedDll.bytes()==13443584L&&selectedDll.sha256().equals("6d6eddb24b6d84a4066606b262329d52ec5acf061ae8edae804dcab1d7c7b5f3");
            // SAVE61 reuses the exact56 Opening reader/frame/serializer/Actor objects and source/ABI pair.
            boolean mappedSave61=selectedDll.bytes()==13451776L&&selectedDll.sha256().equals("4376f38077794ba100349da7a8cc26f45fcab33d0ad525da9ea1836ca26747d6");
            //81 preserves56 reader/ABI and readonly source; Actor/frame/serializer were rebuilt for Full4.
            boolean diagnostic81=selectedDll.bytes()==13752832L&&selectedDll.sha256().equals("75dc138eecec0719f6b7648a4dca3fa83332138c08a61c07403378ba17b54fd9");
            //92 preserves the original56 reader/ABI and exact81 Opening object closure.
            boolean observer92=selectedDll.bytes()==13761536L&&selectedDll.sha256().equals("d9cb12a0e634e517ce6f72d9698e4ea9ab72fc3df606e8fcf34d3fee58c6805f");
            if(!opening56&&!mappedSave61&&!diagnostic81&&!observer92)return Optional.empty();
            return Optional.of(new OpeningReadProfile(new SourcePins("856a95114bd5e70ab50bef77d26a27035552b77df1c3bf79467d1c5b50839102",
                    "31fe8e38eaa822edb8cb63606ee9c1c630657af8f41cd25f7ccb6319e65901f8")));
        }
        private final Protocol protocol;
        private final SourcePins pins;
        public OpeningReadProfile(SourcePins actualFrozenPins) { this(Protocol.BB3, actualFrozenPins); }
        private OpeningReadProfile(Protocol protocol, SourcePins pins) {
            this.protocol = protocol;
            this.pins = java.util.Objects.requireNonNull(pins);
        }
        static OpeningReadProfile full111DataProfile() { return new OpeningReadProfile(Protocol.FULL111, FULL111_PINS); }
        public SourcePins pins() { return pins; }
        public String profileId(Kind kind) { return kind.profile(protocol.number); }
        private String step(Kind kind) { return kind.step(protocol.number); }
        private String capability(Kind kind) { return kind.capability(protocol.number); }
        private String schema(Kind kind) { return kind.schema(protocol.number); }
        public static boolean isCurrentOperation(OperationKey operation) {
            return java.util.Arrays.stream(Protocol.values()).anyMatch(value -> Kind.CURRENT.step(value.number).equals(operation.value()));
        }
        /** DATA decoding only. A matching provenance string does not itself prove Native execution or owner authority. */
        public Data decodeData(Kind kind,RawJson original,Frame expected) {
            java.util.Objects.requireNonNull(kind);java.util.Objects.requireNonNull(original);java.util.Objects.requireNonNull(expected);
            var fields=new HashSet<>(COMMON);if(kind==Kind.SCOPE)fields.add("government");else fields.addAll(Set.of("current_focus","current_lifestyle_progress"));
            ObjectNode row=StrictJson.object(StrictJson.parse(original.bytes(),65536),fields);
            equal(row,"schema",schema(kind));String status=StrictJson.text(row.get("status"));
            StrictJson.require(status.equals("available")||status.equals("unavailable"),"exact opening DATA status required");boolean available=status.equals("available");
            StrictJson.require(CouncilCodec.bool(row.get("read_only"))&&!CouncilCodec.bool(row.get("full_governance_ready"))
                    &&!CouncilCodec.bool(row.get("action_ready")),"opening DATA cannot claim full governance or action readiness");
            ObjectNode provenance=StrictJson.object(row.get("provenance"),Set.of("profile_id","adapter_id","game_version","executable_sha256","reader_source_sha256","abi_manifest_sha256"));
            equal(provenance,"profile_id",profileId(kind));equal(provenance,"adapter_id",protocol.build.coreFullAdapterId());
            equal(provenance,"game_version",protocol.build.version());
            equal(provenance,"executable_sha256",protocol.build.executableSha256().toUpperCase(java.util.Locale.ROOT));
            equal(provenance,"reader_source_sha256",pins.readerSourceSha256());equal(provenance,"abi_manifest_sha256",pins.abiManifestSha256());
            Origin origin=origin(row.get("origin"));Optional<String> reason;
            Optional<Frame> frame;
            if(available) {
                nil(row.get("unavailable_reason"),"available reason");reason=Optional.empty();
                Frame actual=new Frame(integer(row.get("native_revision"),"native revision"),integer(row.get("date_raw"),"native date"),integer(row.get("player_character_id"),"complete actor"));
                StrictJson.require(actual.equals(expected),"opening DATA crossed its independently bound Full actor/revision/date");equal(row,"snapshot_id",actual.snapshotId());
                StrictJson.require(origin.kind()!=SourceKind.UNAVAILABLE,"available DATA requires its actual source kind");frame=Optional.of(actual);
            } else {
                reason=Optional.of(nonempty(StrictJson.text(row.get("unavailable_reason")),"unavailable reason"));frame=Optional.empty();
                for(String key:List.of("native_revision","snapshot_id","date_raw","player_character_id"))nil(row.get(key),"unavailable "+key);
            }
            Set<String> readyFields=kind==Kind.SCOPE?Set.of("same_frame_ready","government_key_ready","government_flags_ready")
                    :Set.of("same_frame_ready","current_focus_ready","lifestyle_progress_ready");
            ObjectNode readiness=StrictJson.object(row.get("readiness"),readyFields);
            for(String key:readyFields)StrictJson.require(CouncilCodec.bool(readiness.get(key))==available,"opening readiness disagrees with its observed status");
            Optional<Government> government=Optional.empty();Optional<FocusProgress> progress=Optional.empty();
            if(kind==Kind.SCOPE) {
                if(!available)nil(row.get("government"),"unavailable government");else {
                    ObjectNode value=StrictJson.object(row.get("government"),Set.of("key","native_flag_count","flags"));
                    int count=StrictJson.integer(value.get("native_flag_count"),BigInteger.ZERO,BigInteger.valueOf(4096)).intValueExact();
                    JsonNode rawFlags=value.get("flags");StrictJson.require(rawFlags.isArray()&&rawFlags.size()==count,"complete government flag span/count changed");
                    java.util.ArrayList<String> flags=new java.util.ArrayList<>();rawFlags.forEach(v->flags.add(nonempty(StrictJson.text(v),"government flag")));
                    government=Optional.of(new Government(StrictJson.text(value.get("key")),flags));
                }
            } else if(!available) {nil(row.get("current_focus"),"unavailable current focus");nil(row.get("current_lifestyle_progress"),"unavailable current progress");}
            else progress=Optional.of(progress(row.get("current_focus"),row.get("current_lifestyle_progress")));
            return new Data(kind,available,reason,frame,government,progress,origin,new RawJson(original.bytes()));
        }
        private static FocusProgress progress(JsonNode focusNode,JsonNode progressNode) {
            ObjectNode focus=StrictJson.object(focusNode,Set.of("presence","key","lifestyle_key"));
            ObjectNode progress=StrictJson.object(progressNode,Set.of("presence","lifestyle_key","xp_total_raw","xp_within_level_raw","xp_per_level","unspent_perk_points","used_perk_points"));
            String presence=StrictJson.text(focus.get("presence"));
            StrictJson.require(presence.equals("present"),"this exact profile has no proven focus/progress absence producer");
            equal(progress,"presence",presence);
            String key=nonempty(StrictJson.text(focus.get("key")),"focus key"),style=nonempty(StrictJson.text(focus.get("lifestyle_key")),"lifestyle key");equal(progress,"lifestyle_key",style);
            return new FocusProgress(true,Optional.of(key),Optional.of(style),Optional.of(integer(progress.get("xp_total_raw"),"total XP raw")),
                    Optional.of(integer(progress.get("xp_within_level_raw"),"within-level XP raw")),Optional.of(integer(progress.get("xp_per_level"),"XP threshold")),
                    Optional.of(integer(progress.get("unspent_perk_points"),"unspent perk points")),Optional.of(integer(progress.get("used_perk_points"),"used perk points")));
        }
        private static Origin origin(JsonNode value) {
            ObjectNode row=StrictJson.object(value,Set.of("source_kind","ticket_sequence","pump_epoch","thread_id","main_owner_observed"));
            SourceKind kind=switch(StrictJson.text(row.get("source_kind"))){case "application_main_ticket"->SourceKind.APPLICATION_MAIN_TICKET;
                case "offline_fixture"->SourceKind.OFFLINE_FIXTURE;case "unavailable"->SourceKind.UNAVAILABLE;default->throw new IllegalArgumentException("unknown opening source kind");};
            return new Origin(kind,optionalInteger(row.get("ticket_sequence"),"ticket sequence"),optionalInteger(row.get("pump_epoch"),"pump epoch"),
                    optionalInteger(row.get("thread_id"),"thread ID"),CouncilCodec.bool(row.get("main_owner_observed")));
        }
        private static Optional<BigInteger> optionalInteger(JsonNode value,String name){java.util.Objects.requireNonNull(value,name);return value.isNull()?Optional.empty():Optional.of(integer(value,name));}
        private static BigInteger integer(JsonNode value,String name){StrictJson.require(value!=null&&value.isIntegralNumber(),"exact JSON integer required: "+name);return value.bigIntegerValue();}
        private static void range(BigInteger value,BigInteger min,BigInteger max,String name){StrictJson.require(value!=null&&value.compareTo(min)>=0&&value.compareTo(max)<=0,"integer outside native domain: "+name);}
        private static String nonempty(String value,String name){StrictJson.require(value!=null&&!value.isEmpty(),"observed nonempty "+name+" required");return value;}
        private static void nil(JsonNode value,String name){StrictJson.require(value!=null&&value.isNull(),"explicit null required for "+name);}
        /** Only these two advertised reads exist in this profile; no legacy read/action contract is constructed. */
        public static final class Bindings {
            private final OpeningReadProfile profile;
            private final ReadContract<Data> scope,current;
            public Bindings(OpeningReadProfile profile,ExactRef nativeSource) {
                this.profile=java.util.Objects.requireNonNull(profile);java.util.Objects.requireNonNull(nativeSource);
                StrictJson.require(nativeSource.bytes()>0&&java.nio.file.Path.of(nativeSource.path()).isAbsolute(),"actual selected native read producer required");
                scope=contract(Kind.SCOPE,nativeSource);current=contract(Kind.CURRENT,nativeSource);
            }
            public OpeningReadProfile profile() { return profile; }
            public List<ReadContract<?>> all(){return List.of(scope,current);}
            public ReadContract<Data> scope(){return scope;}public ReadContract<Data> current(){return current;}
            private ReadContract<Data> contract(Kind kind,ExactRef source) {
                var step = profile.step(kind);
                var capability = profile.capability(kind);
                java.util.function.Function<PlanningReadReceipt,Data> decoder=receipt->{
                    requireReceipt(receipt,step);
                    original(receipt);
                    Data data=profile.decodeData(kind,receipt.original().originalResultToken().orElseThrow(),frame(receipt.request()));
                    if(data.available())data.requireApplicationMainOrigin();
                    return data;
                };
                return new ReadContract<>("governance.opening-readonly."+profile.profileId(kind),new OperationKey(step),Optional.of(capability),
                        capability,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                        ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(request,id)->{
                            StrictJson.require(request.arguments().members().isEmpty(),"Opening read takes no caller selector or extra wire fields");
                            frame(request);
                            return new NativeRequest(step,Optional.of(capability),new RawJson(StrictJson.canonical(StrictJson.object())));
                        },decoder,decoder);
            }
            private static Frame frame(PlanningReadRequest request) {
                StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay,"Opening read requires its actual gameplay frame");
                var id=request.before().frame().identity();return new Frame(id.nativeRevision(),id.dateRaw(),id.player());
            }
            private static void requireReceipt(PlanningReadReceipt receipt,String step) {
                var request=receipt.request();frame(request);
                StrictJson.require(request.operation().value().equals(step)&&request.arguments().members().isEmpty()
                        &&receipt.adoption().isEmpty()&&receipt.archiveVersion()==PlanningReadReceipt.ArchiveVersion.CURRENT_V2,
                        "Opening read cannot adopt another operation or historical/canonical receipt");
                for(var guard:List.of(receipt.before(),receipt.after())) {
                    StrictJson.require(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                            &&guard.binding().observed().equals(request.before())&&guard.paused()&&guard.mapReady()&&guard.playerAlive()
                            &&!guard.binding().observedAt().isAfter(request.deadline()),"Opening read crossed its live paused Full frame or deadline");
                }
                StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                        &&!receipt.after().binding().observedAt().isBefore(receipt.before().binding().observedAt()),
                        "Opening read changed its complete bound owner/source or time order");
                var chronology=GovernanceReadChronology.requireAck(receipt.original(),receipt.before().binding());chronology.verify(receipt);
                StrictJson.require(!chronology.responseReceived().observedAt().isAfter(request.deadline()),"Opening original arrived after its actual deadline");
            }
        }
        @FunctionalInterface public interface CurrentGuard {void requireCurrent(java.time.Instant deadline)throws java.io.IOException;}
        /** Reuses the sole installed coordinator and the currently borrowed writer Session. */
        public static org.xar.ck3.control.application.planning.governance.GovernanceCollector.LifestyleReadPort readPort(
                Bindings definitions,PlanningReadPort port,ActionPorts.OutcomeArchive archive,
                org.xar.ck3.control.application.planning.governance.GovernanceBorrowedSession borrowed,
                java.time.Clock clock,CurrentGuard currentGuard) {
            java.util.Objects.requireNonNull(definitions);java.util.Objects.requireNonNull(port);java.util.Objects.requireNonNull(archive);
            java.util.Objects.requireNonNull(borrowed);java.util.Objects.requireNonNull(clock);java.util.Objects.requireNonNull(currentGuard);
            return new org.xar.ck3.control.application.planning.governance.GovernanceCollector.LifestyleReadPort() {
                @Override public org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.Read<OpportunityJson.Obj> formal(
                        org.xar.ck3.control.application.planning.PlanningRequest request) {
                    return new org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.Unavailable<>("readonly Opening profile does not qualify legacy LIFE formal reads");
                }
                @Override public org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.Read<OpportunityJson.Obj> stockFocus(
                        org.xar.ck3.control.application.planning.PlanningRequest request,String target) {
                    return new org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.Unavailable<>("independent final-focus legality/action producer is not qualified");
                }
                @Override public Optional<org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.Read<org.xar.ck3.control.application.planning.governance.GovernanceCollector.ReadOnlyOpening>> openingReadOnly(
                        org.xar.ck3.control.application.planning.PlanningRequest request) {
                    try {
                        currentGuard.requireCurrent(request.deadline());StrictJson.require(clock.instant().isBefore(request.deadline()),"Opening planning deadline elapsed");
                        if (definitions.profile.protocol == Protocol.FULL111) {
                            var advertised = request.observations().bridgeCapabilities();
                            StrictJson.require(advertised.contains(definitions.profile.capability(Kind.SCOPE))
                                    && advertised.contains(definitions.profile.capability(Kind.CURRENT)),
                                    "Full111 Opening needs both read-only capabilities on the held connection");
                        }
                        var value=borrowed.use(request,same->archive.inSession(same,bound->{
                            var originals=new java.util.ArrayList<PlanningReadReceipt>();var refs=new java.util.ArrayList<ExactRef>();
                            java.util.function.Function<ReadContract<Data>,Data> read=contract->{
                                var actualRequest=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),contract.operation(),new OpportunityJson.Obj(java.util.Map.of()),request.deadline());
                                var result=port.read(same,contract,actualRequest);
                                if(result instanceof PlanningReadResult.Unavailable<Data> unavailable) {
                                    unavailable.original().ifPresent(bound::preserve);throw new IllegalStateException(unavailable.reason());
                                }
                                var actual=(PlanningReadResult.Known<Data>)result;var receipt=actual.receipt();
                                StrictJson.require(receipt.request().equals(actualRequest)&&actual.originalReceipt().equals(bound.readReferenceOf(receipt)),"Opening coordinator receipt belongs to another request/archive");
                                org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(receipt,bound);
                                StrictJson.require(contract.decode(receipt).original().equals(actual.value().original()),"Opening typed DATA differs from its original native receipt");
                                if(!originals.isEmpty()) {
                                    var previous=originals.getLast().after().binding();var next=receipt.before().binding();
                                    StrictJson.require(previous.connectionGeneration().equals(next.connectionGeneration())&&previous.authorityId().equals(next.authorityId())
                                            &&previous.nativeEvidence().equals(next.nativeEvidence())&&previous.capabilityEvidence().equals(next.capabilityEvidence()),
                                            "Opening scope/current reads crossed their held connection, owner, Full or HELLO originals");
                                }
                                originals.add(receipt);GovernanceReadChronology.requireOrderedReads(originals);
                                refs.add(actual.originalReceipt());refs.add(bound.referenceOf(receipt.original()));refs.add(contract.sourceRef());
                                Data data=actual.value();if(!data.available())throw new IllegalStateException(data.unavailableReason().orElseThrow());
                                data.requireApplicationMainOrigin();return data;
                            };
                            Data scopeData=read.apply(definitions.scope());Government government=scopeData.government().orElseThrow();
                            boolean admitted=government.key().equals("feudal_government")&&government.flags().contains("government_is_feudal");
                            ObjectNode scope=StrictJson.object().put("status",admitted?"admitted":"outside_scene")
                                    .put("at_peace",!request.observations().warInProgress()).put("government_key",government.key())
                                    .put("snapshot_revision",scopeData.frame().orElseThrow().nativeRevision()).put("player_character_id",scopeData.frame().orElseThrow().playerCharacterId());
                            ObjectNode query=StrictJson.object().put("status","not_requested_outside_current_admitted_scope");
                            if(admitted)query=definitions.profile.projectCurrent(request,read.apply(definitions.current()));
                            query.set("opening_native_scope",StrictJson.parse(scopeData.original().bytes()));
                            var result=new org.xar.ck3.control.application.planning.governance.GovernanceCollector.ReadOnlyOpening(
                                    (OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(scope)),(OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(query)));
                            return new org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.Known<>(result,refs.stream().distinct().toList());
                        }));
                        currentGuard.requireCurrent(request.deadline());StrictJson.require(clock.instant().isBefore(request.deadline()),"Opening completed after its planning deadline");
                        return Optional.of(value);
                    }catch(java.io.IOException|IllegalStateException|IllegalArgumentException failure) {
                        return Optional.of(new org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.Unavailable<>("actual readonly Opening read unavailable: "+failure.getMessage()));
                    }
                }
            };
        }
        private ObjectNode projectCurrent(org.xar.ck3.control.application.planning.PlanningRequest request,Data data) {
            StrictJson.require(data.kind()==Kind.CURRENT&&data.available()&&data.progress().orElseThrow().present(),"actual present current focus/progress required");
            data.requireApplicationMainOrigin();var frame=request.before().frame();var id=frame.identity();var p=data.progress().orElseThrow();
            StrictJson.require(data.frame().orElseThrow().equals(new Frame(id.nativeRevision(),id.dateRaw(),id.player())),"Opening projection crossed its Full frame");
            ObjectNode query=StrictJson.object().put("status","available").put("opening_read_profile",profileId(Kind.CURRENT));
            query.set("source_frame",StrictJson.object().put("snapshot_id",frame.snapshotId()).put("revision",frame.revision()).put("native_revision",id.nativeRevision()).put("date_raw",id.dateRaw()));
            ObjectNode snapshot=query.putObject("snapshot").put("status","available").put("snapshot_id",frame.snapshotId()).put("episode_run_id",frame.episodeRunId())
                    .put("public_revision",frame.revision()).put("native_revision",id.nativeRevision()).put("date_raw",id.dateRaw()).put("player_character_id",id.player());
            snapshot.putObject("current_focus").put("presence","present").put("key",p.focusKey().orElseThrow()).put("lifestyle_key",p.lifestyleKey().orElseThrow());
            snapshot.putObject("current_lifestyle_progress").put("presence","present").put("lifestyle_key",p.lifestyleKey().orElseThrow())
                    .put("xp_total_raw",p.xpTotalRaw().orElseThrow()).put("xp_within_level_raw",p.xpWithinLevelRaw().orElseThrow()).put("xp_per_level",p.xpPerLevel().orElseThrow())
                    .put("unspent_perk_points",p.unspentPerkPoints().orElseThrow()).put("used_perk_points",p.usedPerkPoints().orElseThrow());
            snapshot.putObject("readiness").put("current_focus_ready",true).put("lifestyle_progress_ready",true).put("same_frame_ready",true);
            query.set("opening_native_current",StrictJson.parse(data.original().bytes()));
            return query;
        }
    }
}
