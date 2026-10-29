package org.xar.ck3.control.wave2.finance.giftpendingframe;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingStatus;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy.Frame;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy.Proof;

/** Actual proof producer/consumer v1 wire contract; snapshot input is an SDK projection. */
public final class GiftPendingFrameCodec {
    private static final Set<String> FRAME_FIELDS = Set.of("public_revision", "native_revision", "date_raw", "episode_run_id", "actor_character_id",
            "actor_alive", "paused", "map_ready", "active_event_absent", "pending_interaction_absent", "bridge_pid", "connection_generation");
    private static final Set<String> PROOF_FIELDS = Set.of("schema", "phase", "pending_request_id", "pending_status", "source_bridge_pid",
            "source_bridge_creation_date", "pre_native_revision", "source_frame", "fresh_frame", "business_submission_attempted", "receipt_query_attempted", "gift_submission_replayed");
    private GiftPendingFrameCodec() { }
    public static Frame decodeSnapshot(byte[] bytes) {
        JsonNode node = object(StrictJson.parse(bytes)); JsonNode actor = object(node.get("played_character")); JsonNode diagnostics = object(node.get("diagnostics"));
        return new Frame(integer(node, "revision"), integer(node, "native_revision"), integer(node, "date_raw"), text(node, "episode_run_id"),
                integer(actor, "character_id"), bool(actor, "alive"), bool(node, "paused"), bool(node, "map_ready"),
                absent(node, "active_event"), absent(node, "pending_character_interaction"), integer(diagnostics, "bridge_pid"), integer(diagnostics, "connection_generation"));
    }
    public static Proof decodeProof(byte[] bytes) {
        JsonNode node = StrictJson.object(StrictJson.parse(bytes), PROOF_FIELDS);
        StrictJson.require("xar.faction-gift-pending-frame-ready/v1".equals(text(node, "schema"))
                && "planning_before_dispatch".equals(text(node, "phase")), "pending frame proof schema/phase required");
        for (String field : Set.of("business_submission_attempted", "receipt_query_attempted", "gift_submission_replayed")) {
            StrictJson.require(!bool(node, field), "read-only proof action flag must be false");
        }
        PendingStatus status = null; String wire = text(node, "pending_status");
        for (PendingStatus candidate : PendingStatus.values()) { if (candidate.wire().equals(wire)) { status = candidate; } }
        StrictJson.require(status != null, "pending frame status required");
        return new Proof(text(node, "pending_request_id"), status,
                new ProcessIdentity(integer(node, "source_bridge_pid"), text(node, "source_bridge_creation_date")),
                integer(node, "pre_native_revision"), frame(node.get("source_frame")), frame(node.get("fresh_frame")));
    }
    public static byte[] encodeProof(Proof proof) {
        ObjectNode node = StrictJson.object(); node.put("schema", "xar.faction-gift-pending-frame-ready/v1"); node.put("phase", "planning_before_dispatch");
        node.put("pending_request_id", proof.pendingRequestId()); node.put("pending_status", proof.pendingStatus().wire());
        node.put("source_bridge_pid", proof.sourceProcess().pid()); node.put("source_bridge_creation_date", proof.sourceProcess().creationDate());
        node.put("pre_native_revision", proof.preNativeRevision()); node.set("source_frame", frameNode(proof.sourceFrame())); node.set("fresh_frame", frameNode(proof.freshFrame()));
        node.put("business_submission_attempted", false); node.put("receipt_query_attempted", false); node.put("gift_submission_replayed", false);
        return StrictJson.canonical(node);
    }
    /** Actual _faction_pending_frame_ready consumer projection, granting only its existing read-only retry class. */
    public static byte[] classifyProof(Proof proof) {
        ObjectNode node = StrictJson.object(); node.put("class", "faction_pending_receipt_paused_frame_ready"); node.put("business_submission", false);
        node.put("pending_request_id", proof.pendingRequestId()); node.put("source_bridge_pid", proof.sourceProcess().pid());
        node.put("pre_native_revision", proof.preNativeRevision()); node.put("source_public_revision", proof.sourceFrame().publicRevision());
        node.put("fresh_public_revision", proof.freshFrame().publicRevision()); node.put("fresh_native_revision", proof.freshFrame().nativeRevision());
        node.put("receipt_query_sent", false); node.put("gift_submission_replayed", false); return StrictJson.canonical(node);
    }
    private static Frame frame(JsonNode value) {
        JsonNode node = StrictJson.object(value, FRAME_FIELDS);
        return new Frame(integer(node, "public_revision"), integer(node, "native_revision"), integer(node, "date_raw"), text(node, "episode_run_id"),
                integer(node, "actor_character_id"), bool(node, "actor_alive"), bool(node, "paused"), bool(node, "map_ready"),
                bool(node, "active_event_absent"), bool(node, "pending_interaction_absent"), integer(node, "bridge_pid"), integer(node, "connection_generation"));
    }
    private static ObjectNode frameNode(Frame frame) {
        ObjectNode node = StrictJson.object(); node.put("public_revision", frame.publicRevision()); node.put("native_revision", frame.nativeRevision());
        node.put("date_raw", frame.dateRaw()); node.put("episode_run_id", frame.episodeRunId()); node.put("actor_character_id", frame.actorCharacterId());
        node.put("actor_alive", frame.actorAlive()); node.put("paused", frame.paused()); node.put("map_ready", frame.mapReady());
        node.put("active_event_absent", frame.activeEventAbsent()); node.put("pending_interaction_absent", frame.pendingInteractionAbsent());
        node.put("bridge_pid", frame.bridgePid()); node.put("connection_generation", frame.connectionGeneration()); return node;
    }
    private static JsonNode object(JsonNode node) { StrictJson.require(node != null && node.isObject(), "SDK object projection required"); return node; }
    private static String text(JsonNode node, String field) { return StrictJson.text(node.get(field)); }
    private static BigInteger integer(JsonNode node, String field) {
        JsonNode value = node.get(field); StrictJson.require(value != null && value.isIntegralNumber(), "exact integer token required: " + field); return value.bigIntegerValue();
    }
    private static boolean bool(JsonNode node, String field) {
        JsonNode value = node.get(field); StrictJson.require(value != null && value.isBoolean(), "boolean token required: " + field); return value.booleanValue();
    }
    private static boolean absent(JsonNode node, String field) { return !node.has(field) || node.get(field).isNull(); }
}
