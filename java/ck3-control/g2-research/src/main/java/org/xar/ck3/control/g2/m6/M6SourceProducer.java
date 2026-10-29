package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m6.G2M6Contracts.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Offline source projection. This producer reads supplied bytes and has no action or ledger writer. */
public final class M6SourceProducer {
    public static final int MAX_BYTES = 524_288;
    public static final String PACKET_SCHEMA = "xar.g2.m6.evidence-packet/v1";
    public static final String BUILD = "1.20.0.4";
    public static final String EXE = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String ORDINARY = "ordinary-sway-opportunity-v1";
    private static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");
    private M6SourceProducer() { }

    public enum OriginalVersion {
        CK3_12003("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
        CK3_12004(BUILD, EXE);
        private final String build;
        private final String digest;
        OriginalVersion(String build, String digest) { this.build = build; this.digest = digest; }
    }
    public enum NativeState { UNOBSERVED, CONTINUE, TERMINATED_UNATTRIBUTED }
    public record OrdinaryStartBinding(long actorCharacterId, String episodeRunId, long gamePid) {
        public OrdinaryStartBinding {
            NativeCharacterId.of(actorCharacterId);
            require(gamePid > 0, "positive admitted Game PID required");
            StrictJson.text(episodeRunId);
        }
    }
    public record RawCompletionObservation(Identity identity, Stamp source, NativeState nativeState,
            boolean canContinueObserved, Optional<Boolean> canContinue, ProjectionJson raw) {
        public RawCompletionObservation {
            java.util.Objects.requireNonNull(identity); java.util.Objects.requireNonNull(source);
            java.util.Objects.requireNonNull(nativeState); java.util.Objects.requireNonNull(canContinue);
            java.util.Objects.requireNonNull(raw);
            require(canContinueObserved == canContinue.isPresent(), "CanContinue observation/value mismatch");
        }
    }

    /** Exact original ledger bytes are retained, including absent/null fields and uint64 numeric tokens. */
    public static CampaignEvidence fromClosedLedger(byte[] raw, G2Source source) {
        verify(raw, source.sourceRef());
        require(BUILD.equals(source.exactBuild()), "M6 source build differs from the qualified source boundary");
        JsonNode root = StrictJson.parse(raw, MAX_BYTES);
        StrictJson.object(root, Set.of("schema", "pending", "resolved"));
        equalText(root, "schema", "xar.ck3.active-scheme-sway-formal-private.v1");
        require(root.get("pending").isNull(), "unresolved pending material cannot grant a resolved episode");
        List<Episode> episodes = new ArrayList<>();
        Set<String> actions = new HashSet<>();
        if (!root.get("resolved").isNull()) flatten(root.get("resolved"), episodes, actions, 0);
        return new CampaignEvidence(source, episodes, ProjectionJson.object(raw, MAX_BYTES));
    }

    /** Packet source binds the entire packet; nested pins bind decoded original bytes, never re-encoding. */
    public static CampaignEvidence fromEvidencePacket(byte[] packet, G2Source packetSource) {
        verify(packet, packetSource.sourceRef());
        JsonNode root = StrictJson.parse(packet, MAX_BYTES);
        StrictJson.object(root, Set.of("schema", "ledger", "ordinary_start_sources"));
        equalText(root, "schema", PACKET_SCHEMA);
        JsonNode ledger = StrictJson.object(root.get("ledger"), Set.of("source_ref", "original_bytes_base64"));
        ExactRef ledgerRef = ExactRef.fromJson(ledger.get("source_ref"));
        byte[] rawLedger = decodeOriginal(ledger, ledgerRef);
        G2Source ledgerSource = new G2Source(packetSource.machineId(), packetSource.observedAtUtc(),
                packetSource.exactBuild(), ledgerRef);
        CampaignEvidence campaign = fromClosedLedger(rawLedger, ledgerSource);
        JsonNode sources = root.get("ordinary_start_sources");
        require(sources.isArray() && sources.size() <= 64, "finite ordinary source array required");
        List<Episode> episodes = new ArrayList<>(campaign.episodes());
        Set<String> witnessed = new HashSet<>();
        for (JsonNode item : sources) {
            StrictJson.object(item, Set.of("source_ref", "original_bytes_base64", "admitted_binding"));
            ExactRef ref = ExactRef.fromJson(item.get("source_ref"));
            byte[] raw = decodeOriginal(item, ref);
            JsonNode admitted = StrictJson.object(item.get("admitted_binding"),
                    Set.of("actor_character_id", "episode_run_id", "game_pid"));
            OrdinaryStartBinding binding = new OrdinaryStartBinding(id(admitted, "actor_character_id"),
                    text(admitted, "episode_run_id"), integer(admitted, "game_pid", 1, 0xffff_ffffL));
            Episode originalStart = ordinaryStart(raw, binding);
            require(witnessed.add(originalStart.identity().actionId()), "duplicate ordinary Start source");
            int found = -1;
            for (int index = 0; index < episodes.size(); index++) {
                if (episodes.get(index).identity().equals(originalStart.identity())) {
                    require(found < 0, "ordinary source identifies duplicate retained episodes"); found = index;
                }
            }
            require(found >= 0, "ordinary Start does not belong to this retained campaign");
            Episode retained = episodes.get(found);
            StartEvidence witnessedStart = originalStart.start().orElseThrow();
            StartEvidence old = retained.start().orElseThrow(() -> new IllegalArgumentException("retained independent Start missing"));
            require(old.applied().equals(witnessedStart.applied())
                    && old.independentActive().equals(witnessedStart.independentActive()),
                    "ordinary Start stamps differ from retained episode");
            episodes.set(found, new Episode(retained.identity(), Optional.of(new StartEvidence(old.applied(),
                    old.independentActive(), old.postconditionVerified(), StartOrigin.ORDINARY_FULL_PLANNER,
                    old.consumption())), retained.firstNamedGain(), retained.terminal(), retained.originalResolved()));
        }
        return new CampaignEvidence(packetSource, episodes, campaign.originalLedger());
    }

    /** Explicit role codec: base64 may exceed StrictJson's small business-text limit, while original bytes remain exact. */
    public static byte[] encodeEvidencePacket(byte[] ledger, ExactRef ledgerRef, byte[] ordinaryAuto,
            ExactRef ordinaryRef, OrdinaryStartBinding binding) {
        verify(ledger, ledgerRef); verify(ordinaryAuto, ordinaryRef); java.util.Objects.requireNonNull(binding);
        ObjectNode packet = StrictJson.object(); packet.put("schema", PACKET_SCHEMA);
        ObjectNode old = packet.putObject("ledger"); old.set("source_ref", ledgerRef.toJson());
        old.put("original_bytes_base64", Base64.getEncoder().encodeToString(ledger));
        ObjectNode source = packet.putArray("ordinary_start_sources").addObject(); source.set("source_ref", ordinaryRef.toJson());
        source.put("original_bytes_base64", Base64.getEncoder().encodeToString(ordinaryAuto));
        ObjectNode admitted = source.putObject("admitted_binding"); admitted.put("actor_character_id", binding.actorCharacterId());
        admitted.put("episode_run_id", binding.episodeRunId()); admitted.put("game_pid", binding.gamePid());
        byte[] raw = packet.toString().getBytes(StandardCharsets.UTF_8);
        return ProjectionJson.object(raw, MAX_BYTES).bytes();
    }

    /** Same diagnostic plane as the old source composer. Neither opinion nor CanContinue supplies termination. */
    public static RawCompletionObservation fromRawCompletion(byte[] raw, Identity expected) {
        JsonNode read = StrictJson.parse(raw, MAX_BYTES);
        object(read); equalText(read, "schema", "xar.ck3.sway_completion.v1"); actual4Completion(read);
        require(identity(read, expected.actionId()).equals(expected), "completion full instance differs");
        Stamp stamp = stamp(read, "snapshot_revision", "date_raw");
        NativeState state = NativeState.UNOBSERVED;
        boolean available = bool(read, "available");
        boolean present = bool(read, "instance_present");
        boolean sourceObserved = bool(read, "instance_source_observed");
        boolean reused = bool(read, "storage_slot_reused");
        boolean exact = bool(read, "exact_instance_join_ready");
        boolean statusObserved = bool(read, "native_status_observed");
        boolean terminal = bool(read, "native_terminal_state_observed");
        Optional<Long> status = nullableInteger(read, "native_status_raw", Integer.MIN_VALUE, Integer.MAX_VALUE);
        Optional<Long> owner = nullableInteger(read, "native_owner_raw", 0, 0xffff_ffffL);
        if (available && sourceObserved && present && exact && !reused && statusObserved && status.isPresent()) {
            long value = status.orElseThrow();
            boolean ownerMatches = owner.isPresent() && (owner.orElseThrow() == expected.actorCharacterId()
                    || value == 1 && owner.orElseThrow() == 0xffff_ffffL);
            if ((value == 0 || value == 1) && ownerMatches) {
                require(terminal == (value == 1), "native status and terminal bit disagree");
                state = value == 0 ? NativeState.CONTINUE : NativeState.TERMINATED_UNATTRIBUTED;
            }
        }
        boolean canObserved = read.has("native_can_continue_observed") && bool(read, "native_can_continue_observed");
        Optional<Boolean> can = Optional.empty();
        if (read.has("native_can_continue") && !read.get("native_can_continue").isNull()) {
            can = Optional.of(bool(read, "native_can_continue"));
        }
        return new RawCompletionObservation(expected, stamp, state, canObserved, can, ProjectionJson.object(raw, MAX_BYTES));
    }

    /** Differential plane matches original compose_sway_terminal_sources_12004 current_instance_observation. */
    public static ProjectionJson composeCurrentObservation(byte[] raw, Identity expected) {
        RawCompletionObservation observation = fromRawCompletion(raw, expected);
        if (observation.nativeState() == NativeState.UNOBSERVED) return ProjectionJson.value(new byte[]{'n','u','l','l'}, 4);
        ObjectNode result = StrictJson.object();
        boolean terminal = observation.nativeState() == NativeState.TERMINATED_UNATTRIBUTED;
        result.put("native_status_raw", terminal ? 1 : 0);
        result.put("native_status_key", terminal ? "terminated_unattributed" : "continue");
        result.put("native_terminal_state_observed", terminal); result.put("terminal_cause_observed", false);
        result.put("source_snapshot_revision", observation.source().nativeRevision());
        result.put("source_date_raw", observation.source().dateRaw());
        result.set("copied_completion_read", StrictJson.parse(raw, MAX_BYTES));
        return ProjectionJson.object(StrictJson.canonical(result, MAX_BYTES), MAX_BYTES);
    }

    private static void flatten(JsonNode resolved, List<Episode> out, Set<String> actions, int depth) {
        require(depth < 64 && out.size() < 64, "finite retained episode tree required");
        Episode episode = episode(resolved);
        require(actions.add(episode.identity().actionId()), "repeated retained action identity");
        out.add(episode);
        if (resolved.has("previous_interventions")) {
            JsonNode previous = resolved.get("previous_interventions");
            require(previous.isArray(), "previous_interventions must be an array, not null");
            for (JsonNode old : previous) flatten(old, out, actions, depth + 1);
        }
    }

    private static Episode episode(JsonNode resolved) {
        object(resolved); equalText(resolved, "status", "applied");
        require(bool(resolved, "postcondition_verified"), "resolved instance is not independently applied");
        String action = text(resolved, "action_id");
        JsonNode receipt = resolved.get("native_receipt");
        boolean recovered = receipt == null || receipt.isNull();
        JsonNode applied = resolved.get(recovered ? "recovered_instance_observation" : "applied_instance_observation");
        JsonNode identitySource = recovered ? applied : receipt;
        object(identitySource);
        Identity identity = new Identity(action, id(resolved, "actor_character_id"), id(resolved, "target_character_id"),
                integer(identitySource, "scheme_instance_id", 0, 0xffff_fffeL), (int) integer(identitySource, "scheme_instance_generation", 0, 255));
        require(identity.schemeInstanceGeneration() == identity.schemeInstanceId() >>> 24, "full instance generation mismatch");
        if (!recovered) {
            equalText(receipt, "schema", "active-scheme-sway-formal-private-v1"); equalText(receipt, "stage", "applied");
            equalText(receipt, "action_id", action); require(bool(receipt, "postcondition_verified"), "unverified native receipt");
            originalNormalizedIdentity(receipt);
            for (String field : List.of("actor_character_id", "target_character_id")) {
                if (receipt.has(field)) require(id(receipt, field) == id(resolved, field),
                        "optional receipt identity drift");
            }
        }
        Optional<StartEvidence> start = Optional.empty();
        if (applied != null && !applied.isNull()) {
            equalText(applied, "schema", recovered ? "xar.ck3.sway-recovered-instance-observation.v1"
                    : "xar.ck3.sway-applied-instance-observation.v1");
            require(identity(applied, action).equals(identity), "independent active identity differs");
            equalText(applied, "action_id", action);
            equalText(applied, "source_kind", recovered ? "matching_active_readback_recovery" : "independent_active_read_after_native_receipt");
            if (recovered) require(!bool(applied, "submission_receipt_available"), "identity-only recovery cannot invent a submission receipt");
            JsonNode row = applied.get("active_instance"); object(row);
            require(integer(row, "scheme_instance_id", 0, 0xffff_fffeL) == identity.schemeInstanceId()
                    && integer(row, "scheme_instance_generation", 0, 255) == identity.schemeInstanceGeneration()
                    && id(row, "target_character_id") == identity.targetCharacterId(), "independent active row differs");
            long progress = integer(row, "progress", 0, Integer.MAX_VALUE);
            require(integer(row, "progress_goal", 1, Integer.MAX_VALUE) >= progress, "independent progress invalid");
            bool(row, "is_exposed"); bool(row, "is_frozen");
            JsonNode read = applied.get("source_read"); object(read); originalNormalizedIdentity(read);
            equalText(read, "schema", "active-scheme-sway-private-read-v1");
            Optional<Stamp> appliedStamp = optionalStamp(resolved, "post_native_revision", "post_date_raw");
            Stamp activeStamp = stamp(read, "snapshot_revision", "date_raw");
            if (recovered) {
                uint64(read, "queried_revision"); uint64(read, "capture_epoch"); uint64(read, "container_generation");
                require(uint64(read, "queried_native_revision").equals(activeStamp.nativeRevision()), "recovered active read revision differs");
                equalText(read, "queried_snapshot_id", "native:" + activeStamp.nativeRevision());
                equalText(read, "post_snapshot_id", text(read, "queried_snapshot_id"));
            }
            if (appliedStamp.isPresent()) start = Optional.of(new StartEvidence(appliedStamp.orElseThrow(), activeStamp,
                    true, recovered ? StartOrigin.RECOVERED_IDENTITY_ONLY : StartOrigin.UNKNOWN, consumption(resolved)));
        }
        Optional<NamedGainEvidence> gain = Optional.empty();
        JsonNode first = resolved.get("first_named_gain_intervention");
        if (first != null && !first.isNull()) {
            equalText(first, "action_id", action);
            require(identity(first, action).equals(identity), "first named gain belongs to another action"); actual4Normalized(first);
            gain = Optional.of(new NamedGainEvidence(stamp(first, "baseline_source_native_revision", "baseline_source_date_raw"),
                    named(first.get("previous_scheme_sway_opinion")), stamp(first, "source_native_revision", "source_date_raw"),
                    named(first.get("scheme_sway_opinion")), bool(first, "incremental_named_gain_observed"),
                    bool(first, "tracked_instance_active"), consumption(first)));
        }
        Optional<TerminalEvidence> terminal = Optional.empty();
        JsonNode item = resolved.get("terminal_intervention");
        if (item != null && !item.isNull()) {
            equalText(item, "action_id", action);
            require(identity(item, action).equals(identity), "retained terminal belongs to another action"); actual4Normalized(item);
            boolean observed = bool(item, "instance_terminal_outcome_observed");
            boolean attributed = bool(item, "terminal_cause_observed");
            String key = text(item, "native_status_key");
            require(Set.of("unobserved", "continue", "terminated_unattributed").contains(key), "unqualified terminal status key");
            TerminalCause cause = key.equals("terminated_unattributed") ? TerminalCause.TERMINATED_UNATTRIBUTED : TerminalCause.UNKNOWN;
            // Derived labels alone are not the existing qualified execute/end causal validator.
            require(!attributed, "attributed source needs the qualified causal input path, not a derived ledger label");
            equalText(item, "terminal_cause", "unknown");
            Stamp observedStamp = stamp(item, "source_native_revision", "source_date_raw");
            boolean independentNatural = false;
            JsonNode copied = item.get("native_observation");
            if (copied != null && !copied.isNull()) {
                RawCompletionObservation raw = fromRawCompletion(StrictJson.canonical(copied, MAX_BYTES), identity);
                require(raw.source().equals(observedStamp), "copied terminal frame differs from retained source stamp");
                if (observed) require(raw.nativeState() == NativeState.TERMINATED_UNATTRIBUTED
                        && key.equals("terminated_unattributed"), "terminal label differs from independent copied native status");
                boolean stopped = resolved.has("stop_intervention") && !resolved.get("stop_intervention").isNull();
                // P55 permits a neutral, independent original-instance terminal with no typed Stop.
                // This does not name the cause or turn its unknown cause into success.
                independentNatural = observed && raw.nativeState() == NativeState.TERMINATED_UNATTRIBUTED && !stopped;
            }
            terminal = Optional.of(new TerminalEvidence(observedStamp,
                    independentNatural, observed, cause, false, consumption(item)));
        }
        return new Episode(identity, start, gain, terminal,
                ProjectionJson.object(StrictJson.canonical(resolved, MAX_BYTES), MAX_BYTES));
    }

    /** Java translation of the actual strict public ordinary Start classifier, not a source tag. */
    private static Episode ordinaryStart(byte[] raw, OrdinaryStartBinding admitted) {
        JsonNode outer = StrictJson.parse(raw, MAX_BYTES);
        JsonNode body = outer.at("/result/structured_content"); object(body);
        equalText(body, "status", "executed"); equalText(body, "selected_step", ORDINARY);
        JsonNode plan = body.get("plan"); object(plan); equalText(plan, "selected_step", ORDINARY);
        JsonNode result = body.get("result"); Episode episode = episode(result); Identity identity = episode.identity();
        require(identity.actionId().matches("sway-[0-9a-f]{32}"), "ordinary original action syntax differs");
        require(!bool(result, "next_turn_consumed"), "ordinary source is not the new Start result");
        JsonNode job = plan.get("ordinary_sway_job_v1"); object(job); equalText(job, "job", "query_selected_target");
        require(!bool(job, "submit_allowed") && id(job, "target_character_id") == identity.targetCharacterId()
                && id(job.get("state"), "actor_character_id") == identity.actorCharacterId(), "ordinary nomination differs");
        JsonNode frame = body.get("planning_source_frame"); object(frame);
        equalText(frame, "schema", "xar.ck3.planning-source-frame/v1"); equalText(frame, "status", "complete");
        BigInteger publicRevision = uint64(frame, "revision"); BigInteger nativeRevision = uint64(frame, "native_revision");
        int date = (int) integer(frame, "date_raw", 1, Integer.MAX_VALUE);
        require(id(frame, "actor_character_id") == identity.actorCharacterId()
                && id(frame, "actor_character_id") == admitted.actorCharacterId()
                && integer(frame, "bridge_pid", 1, 0xffff_ffffL) == admitted.gamePid()
                && text(frame, "episode_run_id").equals(admitted.episodeRunId()), "admitted player/episode/process differs");
        uint64(frame, "connection_generation"); equalText(frame, "snapshot_id", "native:" + nativeRevision);
        JsonNode receipt = result.get("native_receipt"); object(receipt);
        actual4Normalized(receipt);
        BigInteger before = uint64(result, "pre_capture_epoch"); BigInteger after = uint64(result, "post_capture_epoch");
        BigInteger receiptEpoch = uint64(receipt, "post_capture_epoch");
        BigInteger container = uint64(receipt, "post_container_generation");
        Stamp post = stamp(result, "post_native_revision", "post_date_raw");
        require(before.compareTo(receiptEpoch) < 0 && receiptEpoch.compareTo(after) < 0
                && integer(receipt, "post_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == date
                && post.dateRaw() == date && post.nativeRevision().compareTo(nativeRevision) >= 0,
                "ordinary submit/receipt/independent frame ordering differs");
        JsonNode read = result.path("applied_instance_observation").path("source_read"); object(read);
        actual4Normalized(read);
        require(uint64(read, "queried_revision").compareTo(publicRevision) >= 0
                && uint64(read, "queried_native_revision").equals(post.nativeRevision())
                && uint64(read, "snapshot_revision").equals(post.nativeRevision())
                && integer(read, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == date
                && uint64(read, "capture_epoch").equals(after)
                && uint64(read, "container_generation").equals(container), "independent readback provenance differs");
        equalText(read, "queried_snapshot_id", "native:" + post.nativeRevision());
        equalText(read, "post_snapshot_id", text(read, "queried_snapshot_id"));
        JsonNode optional = body.get("ordinary_sway_optional"); object(optional);
        equalText(optional, "job", "query_selected_target"); equalText(optional, "outcome", "applied");
        require(id(optional, "target_character_id") == identity.targetCharacterId()
                && optional.get("result").equals(result), "ordinary completion differs from original result");
        JsonNode cadence = optional.get("scheduler_state"); object(cadence);
        require(id(cadence, "actor_character_id") == identity.actorCharacterId()
                && id(cadence, "last_target_character_id") == identity.targetCharacterId()
                && integer(cadence, "no_operation_count", 0, Integer.MAX_VALUE) == 0
                && integer(cadence, "last_check_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == date
                && integer(cadence, "next_check_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == (long) date + 720,
                "ordinary completed cadence differs");
        equalText(cadence, "last_job_kind", "query_selected_target");
        return episode;
    }

    private static Identity identity(JsonNode value, String action) {
        object(value);
        if (value.has("action_id")) equalText(value, "action_id", action);
        return new Identity(action, id(value, "actor_character_id"), id(value, "target_character_id"),
                integer(value, "scheme_instance_id", 0, 0xffff_fffeL), (int) integer(value, "scheme_instance_generation", 0, 255));
    }
    private static NamedValue named(JsonNode node) {
        StrictJson.object(node, Set.of("observed", "present", "value"));
        boolean observed = bool(node, "observed"), present = bool(node, "present");
        Optional<BigInteger> value = node.get("value").isNull() ? Optional.empty()
                : Optional.of(StrictJson.integer(node.get("value"), BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)));
        require(present == value.isPresent() && (!present || observed), "named modifier observation/presence/value mismatch");
        return new NamedValue(observed, present, value);
    }
    private static Consumption consumption(JsonNode node) {
        boolean consumed = node.has("next_turn_consumed") && bool(node, "next_turn_consumed");
        return new Consumption(consumed, optionalStamp(node, "following_native_revision", "following_date_raw"));
    }
    private static Optional<Stamp> optionalStamp(JsonNode value, String revision, String date) {
        if (!value.has(revision) && !value.has(date)) return Optional.empty();
        return Optional.of(stamp(value, revision, date));
    }
    private static Stamp stamp(JsonNode value, String revision, String date) {
        return new Stamp(uint64(value, revision), (int) integer(value, date, Integer.MIN_VALUE, Integer.MAX_VALUE));
    }
    private static BigInteger uint64(JsonNode value, String field) {
        object(value); return StrictJson.integer(value.get(field), BigInteger.ONE, UINT64_MAX);
    }
    private static long id(JsonNode node, String field) {
        object(node); return NativeCharacterId.fromJson(node.get(field)).value();
    }
    private static long integer(JsonNode node, String field, long minimum, long maximum) {
        object(node); return StrictJson.integer(node.get(field), minimum, maximum);
    }
    private static Optional<Long> nullableInteger(JsonNode node, String field, long minimum, long maximum) {
        require(node.has(field), "required nullable integer missing: " + field);
        return node.get(field).isNull() ? Optional.empty() : Optional.of(integer(node, field, minimum, maximum));
    }
    private static boolean bool(JsonNode node, String field) {
        object(node); JsonNode value = node.get(field); require(value != null && value.isBoolean(), "exact boolean required: " + field);
        return value.booleanValue();
    }
    private static String text(JsonNode node, String field) { object(node); return StrictJson.text(node.get(field)); }
    private static void equalText(JsonNode node, String field, String expected) { require(text(node, field).equals(expected), field + " differs"); }
    private static void object(JsonNode value) { require(value != null && value.isObject(), "JSON object required"); }
    /** Native completion wire fields are mandatory. A normalized copy may additionally retain its own pair. */
    private static void actual4Completion(JsonNode value) {
        equalText(value, "build_version", BUILD);
        require(text(value, "executable_sha256").equalsIgnoreCase(EXE), "native completion digest differs");
        if (value.has("exact_ck3_build") || value.has("exe_sha256")) actual4Normalized(value);
    }
    /** Formal ledger and active-read normalization have their own mandatory field contract, with no fallback. */
    private static void actual4Normalized(JsonNode value) {
        equalText(value, "exact_ck3_build", BUILD);
        require(text(value, "exe_sha256").equalsIgnoreCase(EXE), "normalized exact source digest differs");
        if (value.has("build_version") || value.has("executable_sha256")) {
            equalText(value, "build_version", BUILD);
            require(text(value, "executable_sha256").equalsIgnoreCase(EXE), "copied native digest differs from normalized contract");
        }
    }
    private static void originalNormalizedIdentity(JsonNode value) {
        String build = text(value, "exact_ck3_build"); String digest = text(value, "exe_sha256");
        OriginalVersion selected = null;
        for (OriginalVersion version : OriginalVersion.values()) if (version.build.equals(build)) selected = version;
        require(selected != null && selected.digest.equalsIgnoreCase(digest), "unqualified original identity version/digest pair");
        if (value.has("build_version") || value.has("executable_sha256")) {
            equalText(value, "build_version", build);
            require(text(value, "executable_sha256").equalsIgnoreCase(digest), "original copied native version differs");
        }
    }
    private static byte[] decodeOriginal(JsonNode node, ExactRef ref) {
        JsonNode encoded = node.get("original_bytes_base64");
        require(encoded != null && encoded.isTextual() && encoded.textValue().length() <= MAX_BYTES,
                "finite base64 original required");
        byte[] raw;
        try { raw = Base64.getDecoder().decode(encoded.textValue()); }
        catch (IllegalArgumentException error) { throw new IllegalArgumentException("malformed original base64", error); }
        require(Base64.getEncoder().encodeToString(raw).equals(encoded.textValue()), "canonical base64 required");
        verify(raw, ref); return raw;
    }
    private static void verify(byte[] raw, ExactRef ref) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES && ref.bytes() == raw.length,
                "actual source bytes differ from finite source pin");
        try { require(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(ref.sha256()), "source digest differs"); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
