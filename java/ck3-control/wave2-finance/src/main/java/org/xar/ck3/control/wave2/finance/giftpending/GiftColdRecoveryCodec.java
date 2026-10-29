package org.xar.ck3.control.wave2.finance.giftpending;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Applied;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.PostObservation;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Read;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Recovery;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Resolution;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Result;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Unchanged;

/** Declared projection of the existing private recovery producer, including missing/null states. */
public final class GiftColdRecoveryCodec {
    private GiftColdRecoveryCodec() { }
    public static Recovery decodeRecovery(byte[] raw) { return recovery(GiftPendingCodec.object(StrictJson.parse(raw))); }
    static Recovery recovery(JsonNode node) {
        return new Recovery(read(node, "schema_version", GiftPendingCodec::integer), read(node, "status", StrictJson::text),
                bool(node, "private_build"), bool(node, "advertised"), bool(node, "new_process_confirmed"),
                read(node, "new_round_id", StrictJson::text), read(node, "new_bridge_pid", GiftPendingCodec::integer),
                read(node, "new_bridge_creation_date", StrictJson::text), read(node, "episode_run_id", StrictJson::text),
                bool(node, "paused"), bool(node, "map_ready"), bool(node, "independent_faction_storage_lookup_complete"),
                bool(node, "independent_recipient_lookup_complete"), bool(node, "selected_from_current_targeting_vector"),
                bool(node, "save_is_pre_action_checkpoint"), read(node, "selected_save_sha256", StrictJson::text),
                read(node, "post_observation", GiftColdRecoveryCodec::post));
    }
    private static PostObservation post(JsonNode raw) {
        JsonNode node = GiftPendingCodec.object(raw);
        return new PostObservation(read(node, "snapshot_revision", GiftPendingCodec::integer),
                read(node, "native_snapshot_revision", GiftPendingCodec::integer), read(node, "observed_date_raw", GiftPendingCodec::integer),
                read(node, "player_character_id", GiftPendingCodec::integer), bool(node, "player_resources_query_complete"),
                read(node, "player_gold_raw", GiftPendingCodec::integer), bool(node, "recipient_identity_resolved"),
                read(node, "recipient_character_id", GiftPendingCodec::integer), bool(node, "recipient_alive"),
                bool(node, "recipient_opinion_query_complete"), read(node, "recipient_opinion_of_player", GiftPendingCodec::integer),
                bool(node, "gift_opinion_present"), read(node, "gift_opinion_modifier_value", GiftPendingCodec::integer),
                bool(node, "source_faction_requery_complete"), read(node, "queried_source_faction_id", GiftPendingCodec::integer),
                bool(node, "source_faction_present"), bool(node, "source_faction_metrics_available"), bool(node, "source_faction_targeting_player"),
                read(node, "source_faction_power_raw", GiftPendingCodec::integer), read(node, "source_faction_discontent_raw", GiftPendingCodec::integer),
                read(node, "source_faction_member_character_ids", GiftPendingCodec::integers), GiftPendingCodec.evidence(node));
    }
    public static byte[] encodeResult(Result result) { return GiftPendingCodec.json(resultNode(result)); }
    public static byte[] encodeResolution(Resolution resolution) {
        ObjectNode node = resultNode(resolution.result());
        if (!(resolution.result() instanceof GiftColdRecovery.Unresolved)) {
            node.set("ledger", GiftPendingCodec.encodeLedgerNode(resolution.ledger()));
        }
        return GiftPendingCodec.json(node);
    }
    private static ObjectNode resultNode(Result result) {
        ObjectNode node = StrictJson.object();
        node.put("reason", result.reason().wire()); node.put("action_retry_allowed", result.actionRetryAllowed());
        node.put("public_capability_advertised", false);
        switch (result) {
            case Applied applied -> {
                node.put("status", "applied"); node.put("request_id", applied.requestId()); node.put("new_round_id", applied.newRoundId());
                node.put("new_bridge_pid", applied.newBridgePid()); node.put("new_bridge_creation_date", applied.newBridgeCreationDate());
                node.set("post_observation", StrictJson.parse(applied.postObservation().evidence().json().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                if (applied.threatResolved().known()) { node.put("threat_resolved", applied.threatResolved().value()); }
                else { node.putNull("threat_resolved"); }
            }
            case Unchanged unchanged -> {
                node.put("status", "unchanged"); node.put("request_id", unchanged.requestId()); node.put("new_round_id", unchanged.newRoundId());
                node.put("new_bridge_pid", unchanged.newBridgePid());
            }
            case GiftColdRecovery.Unresolved ignored -> node.put("status", "unresolved");
        }
        return node;
    }
    private static Read<Boolean> bool(JsonNode node, String field) {
        return read(node, field, value -> {
            StrictJson.require(value.isBoolean(), "actual JSON boolean required: " + field); return value.booleanValue();
        });
    }
    private static <T> Read<T> read(JsonNode node, String field, Function<JsonNode, T> parser) {
        JsonNode value = node.get(field); return value == null ? Read.missing() : value.isNull() ? Read.nil() : Read.of(parser.apply(value));
    }
}
