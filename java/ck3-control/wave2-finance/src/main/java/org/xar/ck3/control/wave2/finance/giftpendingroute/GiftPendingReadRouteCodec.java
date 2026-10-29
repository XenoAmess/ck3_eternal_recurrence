package org.xar.ck3.control.wave2.finance.giftpendingroute;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.Checkpoint;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Recovery;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecoveryCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.AppliedReceipt;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ObjectEvidence;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.ColdResult;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.Command;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.Frame;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.ReceiptResult;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Read;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransportCodec;

/** Bounded existing wire projections. No arbitrary step string or submit encoder is exposed. */
public final class GiftPendingReadRouteCodec {
    private GiftPendingReadRouteCodec() { }
    public static Frame decodeFrame(byte[] raw) {
        JsonNode node = object(StrictJson.parse(raw)); JsonNode episode = node.get("episode_run_id");
        Read<String> value = episode == null ? Read.missing() : episode.isNull() ? Read.nil() : Read.of(StrictJson.text(episode));
        return new Frame(GiftReadTransportCodec.decodeSnapshot(raw), value);
    }
    public static byte[] encodeCommand(Command command) {
        ObjectNode node = StrictJson.object(); node.put("type", "execute_step"); node.put("protocol_version", 1);
        node.put("request_id", command.requestId().value()); node.put("step", command.step().wire());
        node.put("expected_revision", command.expectedRevision()); node.put("expected_date_raw", command.expectedDateRaw());
        node.put("expected_player_character_id", command.expectedPlayerCharacterId());
        command.sourceFactionId().ifPresent(value -> node.put("source_faction_id", value));
        command.recipientCharacterId().ifPresent(value -> node.put("recipient_character_id", value));
        return StrictJson.canonical(node);
    }
    static AppliedReceipt materialReceipt(ObjectEvidence result) {
        JsonNode node = evidence(result); JsonNode receipt = node.get("receipt");
        if (!"applied".equals(textOrNull(node.get("status"))) || receipt == null || !receipt.isObject()) {
            throw new GiftPendingReadRoute.RouteFailure("private faction receipt did not prove material application");
        }
        return GiftPendingCodec.decodeReceipt(GiftPendingCodec.encodeObjectProjection(receipt));
    }
    static Recovery recovery(ObjectEvidence result, Frame before, PendingAction pending, ProcessIdentity current,
            Read<String> roundId, Optional<Checkpoint> checkpoint) {
        JsonNode node = evidence(result); JsonNode nativeResult = part(node, "native"); JsonNode post = part(nativeResult, "observation");
        ObjectNode wrapper = StrictJson.object(); wrapper.put("schema_version", 1); copyGet(wrapper, node, "status");
        copyGet(wrapper, node, "private_build"); copyGet(wrapper, node, "advertised"); wrapper.put("new_process_confirmed", true);
        shared(wrapper, "new_round_id", roundId, value -> StrictJson.object().textNode(value));
        wrapper.put("new_bridge_pid", current.pid()); wrapper.put("new_bridge_creation_date", current.creationDate());
        shared(wrapper, "episode_run_id", before.episodeRunId(), value -> StrictJson.object().textNode(value));
        shared(wrapper, "paused", before.snapshot().binding().paused(), value -> StrictJson.object().booleanNode(value));
        shared(wrapper, "map_ready", before.snapshot().binding().mapReady(), value -> StrictJson.object().booleanNode(value));
        boolean zeroFlags = nativeResult != null && nativeResult.has("failure_flags") && !nativeResult.get("failure_flags").isNull()
                && exactInteger(nativeResult.get("failure_flags")).signum() == 0;
        wrapper.put("independent_faction_storage_lookup_complete", zeroFlags && actualTrue(post, "source_faction_requery_complete"));
        wrapper.put("independent_recipient_lookup_complete", actualTrue(post, "recipient_identity_resolved") && actualTrue(post, "recipient_opinion_query_complete"));
        wrapper.put("selected_from_current_targeting_vector", false);
        wrapper.put("save_is_pre_action_checkpoint", checkpoint.filter(value -> value.sha256().equals(pending.checkpointSha256BeforeSubmit())).isPresent());
        if (checkpoint.isPresent()) { wrapper.put("selected_save_sha256", checkpoint.orElseThrow().sha256()); } else { wrapper.putNull("selected_save_sha256"); }
        if (post == null) { wrapper.putNull("post_observation"); } else { wrapper.set("post_observation", post); }
        return GiftColdRecoveryCodec.decodeRecovery(GiftPendingCodec.encodeObjectProjection(wrapper));
    }
    public static ObjectEvidence receiptEvidence(ReceiptResult result) {
        ObjectNode node = evidence(result.originalResult()).deepCopy(); node.set("pending_ledger", StrictJson.parse(GiftPendingCodec.encodeLedger(result.pendingLedger())));
        return wrap(node);
    }
    public static ObjectEvidence coldEvidence(ColdResult result) {
        ObjectNode node = evidence(result.originalResult()).deepCopy(); node.set("cold_recovery", recoveryNode(result.recovery()));
        node.set("cold_recovery_classification", StrictJson.parse(GiftColdRecoveryCodec.encodeResolution(
                new GiftColdRecovery.Resolution(result.classification(), result.ledger())))); return wrap(node);
    }
    static String encodeRecoveryJson(Recovery value) {
        return new String(GiftPendingCodec.encodeObjectProjection(recoveryNode(value)), StandardCharsets.UTF_8);
    }
    private static ObjectNode recoveryNode(Recovery value) {
        ObjectNode node = StrictJson.object(); cold(node, "schema_version", value.schemaVersion(), number -> StrictJson.object().numberNode(number));
        cold(node, "status", value.status(), text -> StrictJson.object().textNode(text));
        cold(node, "private_build", value.privateBuild(), bool -> StrictJson.object().booleanNode(bool));
        cold(node, "advertised", value.advertised(), bool -> StrictJson.object().booleanNode(bool));
        cold(node, "new_process_confirmed", value.newProcessConfirmed(), bool -> StrictJson.object().booleanNode(bool));
        cold(node, "new_round_id", value.newRoundId(), text -> StrictJson.object().textNode(text));
        cold(node, "new_bridge_pid", value.newBridgePid(), number -> StrictJson.object().numberNode(number));
        cold(node, "new_bridge_creation_date", value.newBridgeCreationDate(), text -> StrictJson.object().textNode(text));
        cold(node, "episode_run_id", value.episodeRunId(), text -> StrictJson.object().textNode(text));
        cold(node, "paused", value.paused(), bool -> StrictJson.object().booleanNode(bool)); cold(node, "map_ready", value.mapReady(), bool -> StrictJson.object().booleanNode(bool));
        cold(node, "independent_faction_storage_lookup_complete", value.independentFactionStorageLookupComplete(), bool -> StrictJson.object().booleanNode(bool));
        cold(node, "independent_recipient_lookup_complete", value.independentRecipientLookupComplete(), bool -> StrictJson.object().booleanNode(bool));
        cold(node, "selected_from_current_targeting_vector", value.selectedFromCurrentTargetingVector(), bool -> StrictJson.object().booleanNode(bool));
        cold(node, "save_is_pre_action_checkpoint", value.saveIsPreActionCheckpoint(), bool -> StrictJson.object().booleanNode(bool));
        cold(node, "selected_save_sha256", value.selectedSaveSha256(), text -> StrictJson.object().textNode(text));
        cold(node, "post_observation", value.postObservation(), post -> evidence(post.evidence())); return node;
    }
    private static ObjectEvidence wrap(ObjectNode value) { return new ObjectEvidence(new String(GiftPendingCodec.encodeObjectProjection(value), StandardCharsets.UTF_8)); }
    private static ObjectNode evidence(ObjectEvidence value) { return (ObjectNode) object(StrictJson.parse(value.json().getBytes(StandardCharsets.UTF_8))); }
    private static JsonNode object(JsonNode node) { StrictJson.require(node != null && node.isObject(), "existing object projection required"); return node; }
    private static JsonNode part(JsonNode node, String name) { JsonNode value = node == null ? null : node.get(name); return value != null && value.isObject() ? value : null; }
    private static String textOrNull(JsonNode node) {
        if (node == null || node.isNull()) { return null; } return StrictJson.text(node);
    }
    private static BigInteger exactInteger(JsonNode node) {
        StrictJson.require(node.isIntegralNumber(), "native integer token required; no bool/float/string"); return node.bigIntegerValue();
    }
    private static boolean actualTrue(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        if (value == null || value.isNull()) { return false; }
        StrictJson.require(value.isBoolean(), "native boolean token required: " + field); return value.booleanValue();
    }
    private static void copyGet(ObjectNode target, JsonNode source, String field) {
        JsonNode value = source.get(field); if (value == null) { target.putNull(field); } else { target.set(field, value); }
    }
    private static <T> void shared(ObjectNode target, String field, Read<T> value, Function<T, JsonNode> encode) {
        if (value.known()) { target.set(field, encode.apply(value.value())); } else { target.putNull(field); }
    }
    private static <T> void cold(ObjectNode target, String field, GiftColdRecovery.Read<T> value, Function<T, JsonNode> encode) {
        if (value.known()) { target.set(field, encode.apply(value.value())); }
        else if (value.presence() == GiftColdRecovery.Presence.NULL) { target.putNull(field); }
    }
}
