package org.xar.ck3.control.events.interactionfallback;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.events.interactionfallback.InteractionFallback.*;

/** Explicit projection boundary; never treats the unvalidated legacy context as an internal model. */
public final class InteractionFallbackCodec {
    public static final int MAX_BYTES = 16_384;
    private InteractionFallbackCodec() { }

    public static Request parseRequest(byte[] raw) {
        StrictJson.require(raw != null && raw.length <= MAX_BYTES, "bounded interaction request required");
        ObjectNode root = object(StrictJson.parse(raw), "schema", "binding", "pending", "context", "original_plan", "action_steps");
        StrictJson.require(REQUEST_SCHEMA.equals(text(root, "schema")), "unsupported interaction request schema");
        ObjectNode p = object(root.get("pending"), "instance_id", "sender_character_id", "auto_accept_notification");
        Pending pending = new Pending(id(p, "instance_id"), positiveId(p, "sender_character_id"), nullableBoolean(p.get("auto_accept_notification")));
        ObjectNode c = object(root.get("context"), "status", "snapshot_revision", "date_raw", "pending_interaction_id", "definition", "legality");
        ObjectNode d = object(c.get("definition"), "canonical_key", "deterministic_key_hash");
        Context context = new Context(status(c.get("status")), unsigned(c, "snapshot_revision"), unsigned(c, "date_raw"),
                id(c, "pending_interaction_id"), new Definition(text(d, "canonical_key"), StrictJson.integer(d.get("deterministic_key_hash"), 0, 0xffff_ffffL)),
                legality(c.get("legality")));
        ObjectNode plan = object(root.get("original_plan"), "phase", "selected_step", "blocked_marriage_reply", "existing_interaction_fallback");
        OriginalPlan original = new OriginalPlan(text(plan, "phase"), nullableText(plan.get("selected_step")),
                bool(plan.get("blocked_marriage_reply")), bool(plan.get("existing_interaction_fallback")));
        JsonNode actions = root.get("action_steps");
        StrictJson.require(actions.isArray() && actions.size() <= 512, "bounded action array required");
        Set<String> steps = new LinkedHashSet<>();
        actions.forEach(row -> { String step = StrictJson.text(row); stable(step); steps.add(step); });
        return new Request(binding(root.get("binding")), pending, context, original, steps);
    }

    public static byte[] encodeRequest(Request value) {
        java.util.Objects.requireNonNull(value);
        ObjectNode root = StrictJson.object(); root.put("schema", REQUEST_SCHEMA); root.set("binding", binding(value.binding()));
        root.set("pending", pending(value.pending()));
        Context context = value.context();
        ObjectNode c = StrictJson.object(); c.put("status", lower(context.status())); c.put("snapshot_revision", context.snapshotRevision());
        c.put("date_raw", context.dateRaw()); c.put("pending_interaction_id", context.pendingInteractionId());
        ObjectNode d = StrictJson.object(); d.put("canonical_key", context.definition().canonicalKey());
        d.put("deterministic_key_hash", context.definition().deterministicKeyHash()); c.set("definition", d);
        c.set("legality", legality(context.legality())); root.set("context", c);
        OriginalPlan original = value.originalPlan();
        ObjectNode p = StrictJson.object(); p.put("phase", original.phase()); nullableText(p, "selected_step", original.selectedStep());
        p.put("blocked_marriage_reply", original.blockedMarriageReply()); p.put("existing_interaction_fallback", original.existingInteractionFallback());
        root.set("original_plan", p); var actions = root.putArray("action_steps"); value.actionSteps().stream().sorted().forEach(actions::add);
        return StrictJson.canonical(root, MAX_BYTES);
    }

    /** New candidate projection, not a legacy evidence ticket or an authorization to execute. */
    public static byte[] encodeResult(Result result) {
        java.util.Objects.requireNonNull(result);
        ObjectNode root = StrictJson.object(); root.put("schema", RESULT_SCHEMA); root.put("disposition", lower(result.disposition()));
        if (result.candidate() == null) { root.putNull("candidate"); return StrictJson.canonical(root, MAX_BYTES); }
        Candidate value = result.candidate();
        ObjectNode row = StrictJson.object(); row.put("phase", value.phase().wire()); nullableText(row, "selected_step", value.selectedStep());
        row.put("reason", value.reason()); row.put("pending_interaction_id", value.pending().instanceId());
        row.put("interaction_definition_key", value.definition().canonicalKey()); row.set("binding", binding(value.binding()));
        row.set("gui_binding", guiBinding());
        ObjectNode selected = guiRow(value.selection().action(), value.selection().position(), value.selection().renderedIndex(), value.selection().button());
        selected.put("native_legal", value.selection().nativeLegal()); selected.put("action_reachable", value.selection().actionReachable()); row.set("selection", selected);
        var options = row.putArray("reply_options");
        for (ReplyOption option : value.replyOptions()) {
            ObjectNode rendered = guiRow(option.action(), option.position(), option.renderedIndex(), option.button());
            rendered.set("native_legality", legalityValue(option.nativeLegality())); options.add(rendered);
        }
        row.put("registry_known", value.registryKnown()); row.put("offline_followup_required", value.offlineFollowupRequired());
        if (value.reviewedRule() == null) { row.putNull("reviewed_rule"); } else {
            ReviewedRule known = value.reviewedRule(); ObjectNode rule = StrictJson.object(); rule.put("classification", known.classification());
            rule.put("preferred_action", known.preferredAction()); rule.put("deterministic_key_hash", known.deterministicKeyHash());
            rule.put("source", known.source()); rule.put("source_sha256", known.sourceSha256()); rule.put("source_lines", known.sourceLines());
            rule.put("reason", known.reason()); row.set("reviewed_rule", rule);
        }
        ObjectNode decision = StrictJson.object(); decision.put("classification", value.classification()); decision.put("registry_known", value.registryKnown());
        nullableText(decision, "selected_action", value.selection().proposed() ? value.selection().action().wire() : null);
        nullableText(decision, "selected_step", value.selectedStep()); decision.put("display_position", value.selection().position());
        decision.put("semantic_optimal", false); row.set("decision", decision);
        row.put("semantic_optimal", false); row.put("native_ai_equivalent", false);
        root.set("candidate", row); return StrictJson.canonical(root, MAX_BYTES);
    }

    public static ObjectNode guiBinding() {
        ObjectNode gui = StrictJson.object(); gui.put("game_version", "1.20.0.4"); gui.put("source", GUI_SOURCE); gui.put("sha256", GUI_SHA256); gui.put("lines", "58-76");
        var normal = gui.putArray("normal_channel");
        normal.add(guiRow(Action.REJECT, "left", 0, "reject_button")); normal.add(guiRow(Action.ACCEPT, "right", 1, "accept_button"));
        gui.set("auto_accept_channel", guiRow(Action.ACKNOWLEDGE, "only", 0, "acknowledge_button"));
        ObjectNode variants = StrictJson.object();
        variants.put("gui/interaction_marriage_notification_window.gui", "cb31a53b90b4cfd68145068a0d43780d9287249a6dbe20566c2459610cd07398");
        variants.put("gui/interaction_call_ally_notification_window.gui", "79986b774e6ca8957353da4973b0e329ab3424ae8eee0952c9d3b652eaa591bb");
        variants.put("gui/interaction_interfere_in_war_notification.gui", "e71c670b16639236349cae33ef92805829eb623f77854fe434a3774e1782729e");
        gui.set("same_order_stock_variants", variants); return gui;
    }

    private static ObjectNode guiRow(Action action, String position, int renderedIndex, String button) {
        ObjectNode row = StrictJson.object(); row.put("position", position); row.put("rendered_index", renderedIndex);
        row.put("button", button); row.put("action", action.wire()); row.put("step", action.step());
        if (action == Action.REJECT || action == Action.ACCEPT) {
            row.put("onclick", "CharacterInteractionNotificationWindow." + (action == Action.REJECT ? "Reject" : "Accept"));
            row.put("enabled", "CharacterInteractionNotificationWindow." + (action == Action.REJECT ? "CanReject" : "CanAccept"));
        }
        return row;
    }
    private static Binding binding(JsonNode raw) {
        ObjectNode row = object(raw, "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "paused", "map_ready", "actor_character_id", "connection_generation", "bridge_pid");
        return new Binding(text(row, "snapshot_id"), unsigned(row, "revision"), unsigned(row, "native_revision"), unsigned(row, "date_raw"),
                text(row, "episode_run_id"), bool(row.get("paused")), bool(row.get("map_ready")), positiveId(row, "actor_character_id"),
                unsigned(row, "connection_generation"), StrictJson.integer(row.get("bridge_pid"), 1, 0xffff_ffffL));
    }
    private static ObjectNode binding(Binding value) {
        ObjectNode row = StrictJson.object(); row.put("snapshot_id", value.snapshotId()); row.put("revision", value.revision());
        row.put("native_revision", value.nativeRevision()); row.put("date_raw", value.dateRaw()); row.put("episode_run_id", value.episodeRunId());
        row.put("paused", value.paused()); row.put("map_ready", value.mapReady()); row.put("actor_character_id", value.actorCharacterId());
        row.put("connection_generation", value.connectionGeneration()); row.put("bridge_pid", value.bridgePid()); return row;
    }
    private static ObjectNode pending(Pending value) {
        ObjectNode row = StrictJson.object(); row.put("instance_id", value.instanceId()); row.put("sender_character_id", value.senderCharacterId());
        nullableBoolean(row, "auto_accept_notification", value.autoAcceptNotification()); return row;
    }
    private static ReplyLegality legality(JsonNode raw) {
        StrictJson.require(raw != null && raw.isObject(), "legality object required");
        raw.fieldNames().forEachRemaining(key -> StrictJson.require(Set.of("accept", "reject", "block", "acknowledge").contains(key), "unknown legality key"));
        return new ReplyLegality(legalityValue(raw.get("accept")), legalityValue(raw.get("reject")), legalityValue(raw.get("block")), legalityValue(raw.get("acknowledge")));
    }
    private static ObjectNode legality(ReplyLegality value) {
        ObjectNode row = StrictJson.object();
        for (Action action : Action.values()) {
            Legality item = value.forAction(action);
            if (item.presence() != Presence.MISSING) { row.set(action.wire(), legalityValue(item)); }
        }
        return row;
    }
    private static Legality legalityValue(JsonNode raw) {
        if (raw == null) { return new Legality(Presence.MISSING, null, null, null); }
        if (raw.isNull()) { return new Legality(Presence.NULL, null, null, null); }
        ObjectNode row = object(raw, "status", "allowed", "reason");
        return new Legality(Presence.VALUE, status(row.get("status")), nullableBoolean(row.get("allowed")), nullableText(row.get("reason")));
    }
    private static JsonNode legalityValue(Legality value) {
        if (value.presence() != Presence.VALUE) { return com.fasterxml.jackson.databind.node.NullNode.instance; }
        ObjectNode row = StrictJson.object(); row.put("status", lower(value.status())); nullableBoolean(row, "allowed", value.allowed());
        nullableText(row, "reason", value.reason()); return row;
    }
    private static ObjectNode object(JsonNode node, String... fields) { return StrictJson.object(node, Set.of(fields)); }
    private static String text(ObjectNode row, String key) { String value = StrictJson.text(row.get(key)); stable(value); return value; }
    private static String nullableText(JsonNode node) { StrictJson.require(node != null, "required nullable text missing"); if (node.isNull()) { return null; } String value = StrictJson.text(node); stable(value); return value; }
    private static void nullableText(ObjectNode row, String key, String value) { if (value == null) { row.putNull(key); } else { row.put(key, value); } }
    private static void nullableBoolean(ObjectNode row, String key, Boolean value) { if (value == null) { row.putNull(key); } else { row.put(key, value); } }
    private static boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "exact boolean required"); return node.booleanValue(); }
    private static Boolean nullableBoolean(JsonNode node) { StrictJson.require(node != null, "required nullable boolean missing"); return node.isNull() ? null : bool(node); }
    private static int id(ObjectNode row, String key) { int value = (int) StrictJson.integer(row.get(key), Integer.MIN_VALUE, Integer.MAX_VALUE); pendingId(value); return value; }
    private static int positiveId(ObjectNode row, String key) { return (int) StrictJson.integer(row.get(key), 1, Integer.MAX_VALUE); }
    private static BigInteger unsigned(ObjectNode row, String key) { return StrictJson.integer(row.get(key), BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static Status status(JsonNode node) {
        return switch (StrictJson.text(node)) {
            case "available" -> Status.AVAILABLE; case "unavailable" -> Status.UNAVAILABLE; case "invalid" -> Status.INVALID;
            default -> throw new ContractViolationException("unsupported native status");
        };
    }
    private static String lower(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
}
