package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts;
import org.xar.ck3.control.g2.m6.SwayLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.vanilla.schemesway.SwayScheduleWire;

/** One strict persisted Java body and one explicit legacy-consumer projection. No absent-to-empty fallback. */
public final class SwayFormalCodec {
    public static final int MAX = 1_048_576;
    private SwayFormalCodec() { }
    public static byte[] encode(Ledger state) {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA); row.put("machine_id", state.machineId()); row.put("episode_run_id", state.episodeRunId());
        nullable(row, "pending", state.pending().map(SwayFormalCodec::pending)); nullable(row, "resolved", state.resolved().map(SwayFormalCodec::episode));
        var previous = row.putArray("previous"); state.previous().forEach(value -> previous.add(episode(value)));
        nullable(row, "scheduler", state.schedule().map(value -> StrictJson.parse(SwayScheduleWire.encodeState(value))));
        row.set("original_migration_input", state.originalMigrationInput().toJson()); nullable(row, "imported_legacy", state.imported().map(SwayFormalCodec::imported)); nullable(row, "active_stage", state.activeStage().map(ExactRef::toJson)); return StrictJson.canonical(row, MAX);
    }
    public static Ledger decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, MAX), Set.of("schema", "machine_id", "episode_run_id", "pending", "resolved", "previous", "scheduler", "original_migration_input", "imported_legacy", "active_stage"));
        SwayNativeWire.equals(row, "schema", SCHEMA); JsonNode previous = row.get("previous"); require(previous.isArray() && previous.size() <= 4096, "Sway history array required");
        List<Episode> history = new ArrayList<>(); previous.forEach(value -> history.add(episode(value)));
        return new Ledger(SwayNativeWire.string(row, "machine_id"), SwayNativeWire.string(row, "episode_run_id"), optional(row.get("pending")).map(SwayFormalCodec::pending),
                optional(row.get("resolved")).map(SwayFormalCodec::episode), history, optional(row.get("scheduler")).map(value -> SwayScheduleWire.decodeState(StrictJson.canonical(value))), ExactRef.fromJson(row.get("original_migration_input")), optional(row.get("imported_legacy")).map(SwayFormalCodec::imported), optional(row.get("active_stage")).map(ExactRef::fromJson));
    }

    public static ObjectNode target(SwayNativeWire.TargetRead value) {
        ObjectNode row = StrictJson.object(); row.set("binding", SwayNativeWire.bindingJson(value.binding())); row.set("native_body", StrictJson.parse(value.body().bytes(), MAX)); return row;
    }
    public static SwayNativeWire.TargetRead target(JsonNode value) {
        StrictJson.object(value, Set.of("binding", "native_body")); SwayNativeWire.Binding binding = SwayNativeWire.binding(value.get("binding"));
        JsonNode body = value.get("native_body"); long target = SwayNativeWire.actionCharacter(body, "target_character_id");
        return SwayNativeWire.target(payload(SwayNativeWire.TARGET + target, "available", "active_scheme_sway", body, true, false), "persisted-payload", binding, target);
    }
    public static ObjectNode receipt(SwayNativeWire.AppliedReceipt value) {
        ObjectNode row = StrictJson.object(); row.set("binding", SwayNativeWire.bindingJson(value.binding())); row.set("native_body", StrictJson.parse(value.body().bytes(), MAX)); return row;
    }
    public static SwayNativeWire.AppliedReceipt receipt(JsonNode value, long target) {
        StrictJson.object(value, Set.of("binding", "native_body")); var binding = SwayNativeWire.binding(value.get("binding")); JsonNode body = value.get("native_body");
        return SwayNativeWire.receipt(payload(SwayNativeWire.RECEIPT + target, "applied", "active_scheme_sway_formal", body, false, false), "persisted-payload", binding, SwayNativeWire.string(body, "action_id"), target, BigInteger.ZERO);
    }
    static ObjectNode pending(Pending value) {
        ObjectNode row = StrictJson.object(); row.put("action_id", value.actionId()); row.set("original_target_read", target(value.original())); row.put("stage", value.stage().name());
        nullable(row, "acknowledgement", value.acknowledgement().map(ack -> StrictJson.parse(ack.body().bytes(), MAX))); nullable(row, "receipt", value.receipt().map(SwayFormalCodec::receipt)); return row;
    }
    static Pending pending(JsonNode row) {
        StrictJson.object(row, Set.of("action_id", "original_target_read", "stage", "acknowledgement", "receipt"));
        var original = target(row.get("original_target_read")); String actionId = SwayNativeWire.string(row, "action_id");
        Optional<SwayNativeWire.StartAck> ack = optional(row.get("acknowledgement")).map(body -> SwayNativeWire.startAck(payload(SwayNativeWire.START + original.target(), "submitted_verification_pending", "active_scheme_sway_formal", body, false, false), "persisted-payload", actionId, original));
        return new Pending(actionId, original, PendingStage.valueOf(SwayNativeWire.string(row, "stage")), ack, optional(row.get("receipt")).map(value -> receipt(value, original.target())));
    }
    static ObjectNode episode(Episode value) {
        ObjectNode row = StrictJson.object(); row.set("identity", identity(value.identity())); nullable(row, "original_target_read", value.originalIntent().map(SwayFormalCodec::target)); row.set("independent_active", target(value.independentActive()));
        nullable(row, "imported_intent", value.importedIntent().map(SwayFormalCodec::intent));
        var scopes = row.putArray("retained_scopes"); value.retainedScopes().forEach(old -> scopes.add(chunks(SwayLifecycle.encode(old))));
        nullable(row, "native_receipt", value.nativeReceipt().map(SwayFormalCodec::receipt)); nullable(row, "retained_receipt", value.retainedReceipt().map(SwayFormalCodec::receipt));
        row.set("lifecycle", chunks(SwayLifecycle.encode(value.lifecycle()))); nullable(row, "start_following", value.startFollowing().map(ProposalLifecycleCodec::observation));
        nullable(row, "stop", value.stop().map(SwayFormalCodec::stop)); return row;
    }
    static Episode episode(JsonNode row) {
        StrictJson.object(row, Set.of("identity", "original_target_read", "independent_active", "native_receipt", "retained_receipt", "lifecycle", "start_following", "stop", "imported_intent", "retained_scopes"));
        G2M6Contracts.Identity id = identity(row.get("identity"));
        JsonNode scopes = row.get("retained_scopes"); require(scopes.isArray() && scopes.size() <= 64, "retained Sway source scopes required"); List<SwayLifecycle.State> oldScopes = new ArrayList<>(); scopes.forEach(value -> oldScopes.add(SwayLifecycle.decode(bytes(value))));
        return new Episode(id, optional(row.get("original_target_read")).map(SwayFormalCodec::target), target(row.get("independent_active")), optional(row.get("native_receipt")).map(value -> receipt(value, id.targetCharacterId())),
                optional(row.get("retained_receipt")).map(value -> receipt(value, id.targetCharacterId())), SwayLifecycle.decode(bytes(row.get("lifecycle"))),
                optional(row.get("start_following")).map(ProposalLifecycleCodec::decodeObservation), optional(row.get("stop")).map(value -> stop(value, id)), optional(row.get("imported_intent")).map(SwayFormalCodec::intent), oldScopes);
    }
    static ObjectNode stop(Stop value) {
        ObjectNode row = StrictJson.object(); row.put("action_id", value.actionId()); row.set("submitted_from", SwayNativeWire.bindingJson(value.submittedFrom())); row.put("stage", value.stage().name());
        nullable(row, "acknowledgement", value.acknowledgement().map(ack -> StrictJson.parse(ack.body().bytes(), MAX))); nullable(row, "terminal_observed", value.terminalObserved().map(ProposalLifecycleCodec::observation));
        nullable(row, "following", value.following().map(ProposalLifecycleCodec::observation)); return row;
    }
    static Stop stop(JsonNode row, G2M6Contracts.Identity id) {
        StrictJson.object(row, Set.of("action_id", "submitted_from", "stage", "acknowledgement", "terminal_observed", "following"));
        String actionId = SwayNativeWire.string(row, "action_id"); var binding = SwayNativeWire.binding(row.get("submitted_from"));
        Optional<SwayNativeWire.StopAck> ack = optional(row.get("acknowledgement")).map(body -> SwayNativeWire.stopAck(payload(SwayNativeWire.STOP, "submitted_verification_pending", "sway_stop", body, false, true), "persisted-payload", binding, actionId, id.targetCharacterId(), id.schemeInstanceId(), id.schemeInstanceGeneration()));
        return new Stop(actionId, binding, StopStage.valueOf(SwayNativeWire.string(row, "stage")), ack, optional(row.get("terminal_observed")).map(ProposalLifecycleCodec::decodeObservation), optional(row.get("following")).map(ProposalLifecycleCodec::decodeObservation));
    }

    /** Current original full episode, consumed by the one M6 composition. Preserved receipts keep their original provenance. */
    public static G2M6Contracts.Episode m6Episode(Episode value) {
        ProjectionJson legacy = SwayNativeWire.json(originalResolved(value));
        return new G2M6Contracts.Episode(value.identity(), Optional.empty(), Optional.empty(), Optional.empty(), legacy);
    }
    public static ObjectNode originalResolved(Episode value) {
        ObjectNode row = identity(value.identity()); row.remove("scheme_instance_id"); row.remove("scheme_instance_generation"); row.put("status", "applied"); row.put("postcondition_verified", true);
        value.originalIntent().ifPresent(original -> row.put("pre_capture_epoch", original.captureEpoch()));
        value.importedIntent().ifPresent(original -> { JsonNode historical = StrictJson.parse(original.original().bytes(), MAX); if (historical.has("pre_capture_epoch")) row.set("pre_capture_epoch", historical.get("pre_capture_epoch")); });
        row.put("post_capture_epoch", value.independentActive().captureEpoch());
        row.put("post_native_revision", value.independentActive().binding().revision()); row.put("post_date_raw", value.independentActive().binding().date()); row.put("next_turn_consumed", value.importedIntent().isPresent() || value.startFollowing().isPresent());
        if (value.nativeReceipt().isPresent()) row.set("native_receipt", receiptWithProvenance(value.nativeReceipt().orElseThrow())); else row.putNull("native_receipt");
        value.retainedReceipt().ifPresent(receipt -> row.set("retained_native_applied_receipt", receiptWithProvenance(receipt)));
        SwayNativeWire.Instance active = value.independentActive().instances().stream().filter(instance -> instance.fullId() == value.identity().schemeInstanceId()).findFirst().orElseThrow();
        ObjectNode observation = identity(value.identity()); boolean recovered = value.nativeReceipt().isEmpty();
        observation.put("schema", recovered ? "xar.ck3.sway-recovered-instance-observation.v1" : "xar.ck3.sway-applied-instance-observation.v1");
        observation.put("source_kind", recovered ? "matching_active_readback_recovery" : "independent_active_read_after_native_receipt");
        if (recovered) observation.put("submission_receipt_available", false);
        ObjectNode activeRow = observation.putObject("active_instance"); activeRow.put("scheme_instance_id", active.fullId()); activeRow.put("scheme_instance_generation", active.generation()); activeRow.put("target_character_id", active.target());
        activeRow.put("progress", active.progress()); activeRow.put("progress_goal", active.progressGoal()); activeRow.put("is_exposed", active.exposed()); activeRow.put("is_frozen", active.frozen());
        ObjectNode source = (ObjectNode) StrictJson.parse(value.independentActive().body().bytes(), MAX); source.remove("active_sway_instances");
        source.put("exact_ck3_build", value.independentActive().binding().exactBuild()); source.put("exe_sha256", value.independentActive().binding().exeSha256());
        source.put("queried_snapshot_id", value.independentActive().binding().before().frame().snapshotId()); source.put("queried_revision", value.independentActive().binding().before().frame().revision());
        source.put("queried_native_revision", value.independentActive().binding().revision()); source.put("post_snapshot_id", value.independentActive().binding().before().frame().snapshotId());
        observation.set("source_read", source); row.set(recovered ? "recovered_instance_observation" : "applied_instance_observation", observation);
        ObjectNode interventions = (ObjectNode) StrictJson.parse(SwayLifecycle.interventions(value.lifecycle()).bytes(), MAX);
        // A consumed historical first gain cannot become a second first-gain credit after source reattachment.
        value.importedIntent().filter(original -> original.historicalConsumed(org.xar.ck3.control.g2.m6.SwayHistoricalImport.Plane.FIRST_GAIN)).ifPresent(original -> interventions.remove("first_named_gain_intervention"));
        if (value.retainedScopes().stream().anyMatch(old -> old.firstGain().isPresent())) interventions.remove("first_named_gain_intervention");
        interventions.properties().forEach(entry -> { require(!row.has(entry.getKey()), "M6 intervention cannot overwrite original Start core"); row.set(entry.getKey(), entry.getValue()); });
        value.startFollowing().ifPresent(after -> { row.put("following_native_revision", after.frame().identity().nativeRevision()); row.put("following_date_raw", after.frame().identity().dateRaw()); });
        value.stop().ifPresent(stop -> {
            ObjectNode projection = identity(value.identity()); projection.put("original_action_id", value.identity().actionId()); projection.put("action_id", stop.actionId());
            projection.put("status", stop.stage() == StopStage.TERMINAL_OBSERVED ? "terminal_observed_after_stop_request" : stop.stage() == StopStage.POSTCONDITION_PENDING ? "stop_postcondition_pending" : "stop_submission_unresolved");
            projection.put("postcondition_verified", stop.terminalObserved().isPresent()); projection.put("next_turn_consumed", stop.following().isPresent());
            stop.terminalObserved().ifPresent(observed -> { projection.put("source_native_revision", observed.frame().identity().nativeRevision()); projection.put("source_date_raw", observed.frame().identity().dateRaw()); });
            stop.following().ifPresent(after -> { projection.put("following_native_revision", after.frame().identity().nativeRevision()); projection.put("following_date_raw", after.frame().identity().dateRaw()); });
            stop.acknowledgement().ifPresent(ack -> projection.set("ack", StrictJson.parse(ack.body().bytes(), MAX))); row.set("stop_intervention", projection);
        });
        return row;
    }
    static ObjectNode receiptWithProvenance(SwayNativeWire.AppliedReceipt value) {
        ObjectNode row = (ObjectNode) StrictJson.parse(value.body().bytes(), MAX); row.put("exact_ck3_build", value.binding().exactBuild()); row.put("exe_sha256", value.binding().exeSha256()); return row;
    }
    static ObjectNode imported(SwayLegacyImport.Imported value) {
        ObjectNode row = StrictJson.object(); row.set("archived_original", value.archivedOriginal().toJson()); row.set("original_bytes_base64", chunks(value.original().bytes())); return row;
    }
    static SwayLegacyImport.Imported imported(JsonNode row) {
        StrictJson.object(row, Set.of("archived_original", "original_bytes_base64"));
        return SwayLegacyImport.parse(ExactRef.fromJson(row.get("archived_original")), bytes(row.get("original_bytes_base64")));
    }
    static ObjectNode intent(SwayLegacyImport.OriginalIntent value) {
        ObjectNode row = StrictJson.object(); row.put("kind", value.kind().name()); row.set("original_bytes_base64", chunks(value.original().bytes())); return row;
    }
    static SwayLegacyImport.OriginalIntent intent(JsonNode row) {
        StrictJson.object(row, Set.of("kind", "original_bytes_base64")); return new SwayLegacyImport.OriginalIntent(SwayLegacyImport.Kind.valueOf(SwayNativeWire.string(row, "kind")), ProjectionJson.object(bytes(row.get("original_bytes_base64")), MAX));
    }
    static JsonNode chunks(byte[] bytes) {
        require(bytes.length <= MAX, "bounded exact stored bytes required"); String encoded = java.util.Base64.getEncoder().encodeToString(bytes); var rows = StrictJson.object().putArray("chunks");
        for (int offset = 0; offset < encoded.length(); offset += 2048) rows.add(encoded.substring(offset, Math.min(offset + 2048, encoded.length()))); return rows;
    }
    static byte[] bytes(JsonNode value) {
        require(value != null && value.isArray() && value.size() <= 684, "bounded stored-byte chunks required"); StringBuilder encoded = new StringBuilder();
        for (int index = 0; index < value.size(); index++) { JsonNode chunk = value.get(index); require(chunk.isTextual() && !chunk.textValue().isEmpty() && chunk.textValue().length() <= 2048 && (index == value.size() - 1 || chunk.textValue().length() == 2048), "canonical base64 chunk required"); encoded.append(chunk.textValue()); }
        byte[] bytes = java.util.Base64.getDecoder().decode(encoded.toString()); require(bytes.length <= MAX && java.util.Base64.getEncoder().encodeToString(bytes).equals(encoded.toString()), "canonical original bytes base64 required"); return bytes;
    }
    static ObjectNode identity(G2M6Contracts.Identity value) {
        ObjectNode row = StrictJson.object(); row.put("action_id", value.actionId()); row.put("actor_character_id", value.actorCharacterId()); row.put("target_character_id", value.targetCharacterId()); row.put("scheme_instance_id", value.schemeInstanceId()); row.put("scheme_instance_generation", value.schemeInstanceGeneration()); return row;
    }
    static G2M6Contracts.Identity identity(JsonNode row) {
        StrictJson.object(row, Set.of("action_id", "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation"));
        return new G2M6Contracts.Identity(SwayNativeWire.string(row, "action_id"), SwayNativeWire.actionCharacter(row, "actor_character_id"), SwayNativeWire.actionCharacter(row, "target_character_id"), SwayNativeWire.integer(row, "scheme_instance_id", 0, 0xffff_fffeL), Math.toIntExact(SwayNativeWire.integer(row, "scheme_instance_generation", 0, 255)));
    }
    /** Pure stored-body decoding reuses the same strict payload parser. This frame is never archived as a native original. */
    static byte[] payload(String step, String status, String key, JsonNode body, boolean readOnly, boolean stop) {
        ObjectNode frame = StrictJson.object(); frame.put("type", "command_result"); frame.put("protocol_version", 1); frame.put("request_id", "persisted-payload"); frame.put("ok", true); if (stop) frame.put("error", "");
        ObjectNode result = frame.putObject("result"); result.put("step", step); result.put("accepted", true); result.put("status", status); result.put("private_build", true); result.put("advertised", false); result.put("backend_id", "native-headless");
        if (readOnly || stop) result.put("read_only", readOnly); result.set(key, body); return StrictJson.canonical(frame, MAX);
    }
    static Optional<JsonNode> optional(JsonNode value) { require(value != null, "required nullable Sway field is missing"); return value.isNull() ? Optional.empty() : Optional.of(value); }
    static void nullable(ObjectNode row, String name, Optional<? extends JsonNode> value) { if (value.isPresent()) row.set(name, value.orElseThrow()); else row.putNull(name); }
}
