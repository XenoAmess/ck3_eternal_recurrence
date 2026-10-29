package org.xar.ck3.control.planning.warquerycadence;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeInteractionRoles;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.CasusBelli;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.HistoryRecord;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.NativeOptions;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.NegativeSignature;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.OptionSignature;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.OptionsSignature;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.PolicyDefer;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.QueryContext;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.QueryResult;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.RecipientResponse;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.Request;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.ScoreBreakdown;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.Side;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.Snapshot;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.StableWar;
import org.xar.ck3.control.planning.warquerycadence.WarQueryCadence.War;

/** Strict JSON projection boundary; native evidence is never reissued by this codec. */
public final class WarQueryCadenceCodec {
    public static final String SCHEMA = "xar.ck3.war-query-cadence-input/v1";
    private static final int MAX_RECORDS = 256;
    private static final int MAX_WARS = 64;
    private static final BigInteger INT32_MIN = BigInteger.valueOf(Integer.MIN_VALUE);
    private static final BigInteger INT32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final BigInteger MAX_INTEGER = StrictJson.UINT64_MAX;
    private static final Set<String> SIGNATURE_FIELDS = Set.of("war_id", "player_side", "player_is_primary_war_leader",
            "player_relative_war_score", "absolute_war_scores_observable", "attacker_war_score", "defender_war_score",
            "war_score_breakdown", "active_casus_belli_present", "active_casus_belli_identity", "cb_allows_white_peace", "options");

    private WarQueryCadenceCodec() { }

    public static Request decode(byte[] bytes) {
        ObjectNode root = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "snapshot", "active_wars", "war", "recent_records"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "unsupported cadence schema");
        ObjectNode frame = object(root.get("snapshot")); ObjectNode actor = object(required(frame, "played_character"));
        ObjectNode diagnostics = object(required(frame, "diagnostics"));
        JsonNode terminal = required(frame, "one_life_terminal_reason");
        StrictJson.require(terminal.isNull() || terminal.isTextual(), "terminal reason must be null or text");
        Snapshot snapshot = new Snapshot(bool(required(frame, "paused")), bool(required(frame, "map_ready")), !terminal.isNull(),
                objectMarker(required(frame, "active_event")), objectMarker(required(frame, "pending_character_interaction")),
                modalPresent(frame.get("top_exclusive_modal_choice_hint")),
                positive(required(actor, "character_id")), bool(required(actor, "alive")), positive(required(frame, "date_raw")),
                StrictJson.text(required(frame, "episode_run_id")), positive(required(diagnostics, "connection_generation")));
        List<War> wars = wars(required(root, "active_wars")); War war = war(required(root, "war"));
        List<HistoryRecord> records = new ArrayList<>(); JsonNode history = required(root, "recent_records");
        StrictJson.require(history.isArray() && history.size() <= MAX_RECORDS, "bounded history array required");
        for (JsonNode value : history) { records.add(history(value, war.warId())); }
        return new Request(snapshot, wars, war, records);
    }

    /** Encodes the semantic policy projection, not a replacement for original native records. */
    public static byte[] encodeRequest(Request request) {
        ObjectNode root = StrictJson.object(); root.put("schema", SCHEMA);
        Snapshot snapshot = request.snapshot(); ObjectNode frame = root.putObject("snapshot");
        frame.put("paused", snapshot.paused()); frame.put("map_ready", snapshot.mapReady());
        if (snapshot.terminalReasonPresent()) { frame.put("one_life_terminal_reason", "present"); }
        else { frame.putNull("one_life_terminal_reason"); }
        marker(frame, "active_event", snapshot.activeEventPresent()); marker(frame, "pending_character_interaction", snapshot.interactionPresent());
        if (snapshot.exclusiveModalPresent()) { frame.putObject("top_exclusive_modal_choice_hint").put("status", "present"); }
        else { frame.putNull("top_exclusive_modal_choice_hint"); }
        frame.put("date_raw", snapshot.dateRaw()); frame.put("episode_run_id", snapshot.episodeRunId());
        ObjectNode actor = frame.putObject("played_character"); actor.put("character_id", snapshot.actorId()); actor.put("alive", snapshot.actorAlive());
        frame.putObject("diagnostics").put("connection_generation", snapshot.connectionGeneration());
        ArrayNode wars = root.putArray("active_wars"); request.activeWars().forEach(w -> wars.add(encodeWar(w)));
        root.set("war", encodeWar(request.war())); ArrayNode records = root.putArray("recent_records");
        for (HistoryRecord record : request.recentRecords()) {
            ObjectNode node = records.addObject(); nullable(node, "step", record.step()); nullable(node, "ok", record.ok());
            ObjectNode result = node.putObject("result"); if (record.warActionPresent()) { result.putObject("war_action"); }
            if (record.query() != null) {
                QueryResult query = record.query(); result.put("step", query.step()); nullable(result, "accepted", query.accepted());
                result.put("status", query.status()); result.put("query_sequence", query.querySequence());
                result.set("termination_query_context", encodeContext(query.context()));
                ObjectNode options = encodeSignature(query.options().signature()); nullable(options, "war_duration_days", query.options().durationDays());
                ObjectNode peace = object(options.get("options").get("white_peace"));
                nullable(peace, "auto_accept_observable", query.options().whitePeaceAutoAcceptObservable());
                nullable(peace, "auto_accept", query.options().whitePeaceAutoAccept());
                result.set("war_termination_options", options);
            }
        }
        return StrictJson.canonical(root);
    }

    /** The exact legacy consumer fields; authority-denying fields are constants. */
    public static byte[] encodeDefer(Optional<PolicyDefer> defer) {
        if (defer.isEmpty()) { return StrictJson.canonical(NullNode.getInstance()); }
        PolicyDefer value = defer.orElseThrow(); ObjectNode node = StrictJson.object();
        node.put("status", "policy_deferred_after_two_no_action_queries"); node.put("war_id", value.warId());
        node.put("latest_queried_date_raw", value.latestQueriedDateRaw()); node.put("previous_queried_date_raw", value.previousQueriedDateRaw());
        node.put("latest_query_sequence", value.latestQuerySequence()); node.put("expires_date_raw", value.expiresDateRaw());
        node.put("fresh_native_result", false); node.putNull("native_legality"); node.put("business_action_credit", 0);
        node.set("last_observed_cb_identity", encodeCb(value.lastObservedCasusBelli()));
        node.put("current_cb_identity_status", "unknown_without_fresh_native_query"); node.put("source", "history_policy_only");
        return StrictJson.canonical(node);
    }

    private static HistoryRecord history(JsonNode value, BigInteger selectedWar) {
        ObjectNode node = object(value); JsonNode rawStep = required(node, "step");
        StrictJson.require(rawStep.isNull() || rawStep.isTextual(), "history step must be string or null");
        String step = rawStep.isNull() ? null : rawStep.textValue();
        if (step != null && !step.isEmpty()) { StrictJson.text(step); }
        Boolean ok = nullableBool(required(node, "ok"));
        JsonNode result = node.get("result"); boolean warAction = result != null && result.isObject()
                && result.get("war_action") != null && result.get("war_action").isObject();
        QueryResult query = null;
        if (selectedWar.equals(WarQueryCadence.parseQueryWarId(step)) && result != null && result.isObject()
                && result.has("termination_query_context") && result.get("termination_query_context").isObject()
                && result.has("war_termination_options") && result.get("war_termination_options").isObject()) {
            ObjectNode options = object(result.get("war_termination_options"));
            NativeOptions nativeOptions = new NativeOptions(signature(options, false), nullableNonnegative(required(options, "war_duration_days")),
                    nullableBool(required(object(required(options, "options")).get("white_peace"), "auto_accept_observable")),
                    nullableBool(required(object(required(options, "options")).get("white_peace"), "auto_accept")));
            query = new QueryResult(StrictJson.text(required(result, "step")), nullableBool(required(result, "accepted")),
                    StrictJson.text(required(result, "status")), context(result.get("termination_query_context")), nativeOptions,
                    positive(required(result, "query_sequence")));
        }
        return new HistoryRecord(step, ok, warAction, query);
    }

    private static QueryContext context(JsonNode value) {
        ObjectNode node = StrictJson.object(value, Set.of("schema_version", "active_war_signature", "queried_episode_run_id",
                "queried_connection_generation", "queried_character_id", "negative_decision_signature", "queried_war_duration_days", "queried_date_raw"));
        List<StableWar> stable = wars(required(node, "active_war_signature")).stream().map(War::stable).toList();
        return new QueryContext(nonnegative(required(node, "schema_version")), stable, StrictJson.text(required(node, "queried_episode_run_id")),
                positive(required(node, "queried_connection_generation")), positive(required(node, "queried_character_id")),
                signature(required(node, "negative_decision_signature"), true), nullableNonnegative(required(node, "queried_war_duration_days")),
                positive(required(node, "queried_date_raw")));
    }

    private static NegativeSignature signature(JsonNode value, boolean exact) {
        ObjectNode node = exact ? StrictJson.object(value, SIGNATURE_FIELDS) : object(value);
        ObjectNode options = StrictJson.object(required(node, "options"), Set.of("surrender", "white_peace", "victory"));
        return new NegativeSignature(positive(required(node, "war_id")), side(required(node, "player_side")),
                nullableBool(required(node, "player_is_primary_war_leader")), signed(required(node, "player_relative_war_score")),
                nullableBool(required(node, "absolute_war_scores_observable")), nullableSigned(required(node, "attacker_war_score")),
                nullableSigned(required(node, "defender_war_score")), breakdown(required(node, "war_score_breakdown")),
                nullableBool(required(node, "active_casus_belli_present")), cb(required(node, "active_casus_belli_identity")),
                nullableBool(required(node, "cb_allows_white_peace")), new OptionsSignature(option(options.get("surrender"), exact),
                option(options.get("white_peace"), exact), option(options.get("victory"), exact)));
    }

    private static OptionSignature option(JsonNode value, boolean exact) {
        ObjectNode node = object(value);
        if (exact) {
            StrictJson.object(node, node.has(NativeInteractionRoles.FIELD)
                    ? Set.of("outcome", "hostage_variant", "context_constructed", "native_validator_passed", "available",
                            "recipient_response", NativeInteractionRoles.FIELD)
                    : Set.of("outcome", "hostage_variant", "context_constructed", "native_validator_passed", "available",
                            "recipient_response"));
        }
        ObjectNode response = StrictJson.object(required(node, "recipient_response"), Set.of("status", "decision_status_raw", "would_accept_now"));
        return new OptionSignature(StrictJson.text(required(node, "outcome")), StrictJson.text(required(node, "hostage_variant")),
                nullableBool(required(node, "context_constructed")), nullableBool(required(node, "native_validator_passed")),
                nullableBool(required(node, "available")), new RecipientResponse(StrictJson.text(required(response, "status")),
                nullableSigned(required(response, "decision_status_raw")), nullableBool(required(response, "would_accept_now"))),
                NativeInteractionRoles.fromOption(node));
    }

    private static List<War> wars(JsonNode value) {
        StrictJson.require(value != null && value.isArray() && value.size() <= MAX_WARS, "bounded wars array required");
        List<War> result = new ArrayList<>(); for (JsonNode node : value) { result.add(war(node)); } return List.copyOf(result);
    }

    private static War war(JsonNode value) {
        ObjectNode node = object(value); JsonNode titles = required(node, "targeted_title_ids");
        StrictJson.require(titles.isArray() && titles.size() <= 1024, "bounded targeted titles array required");
        List<BigInteger> ids = new ArrayList<>(); for (JsonNode id : titles) { ids.add(nonnegative(id)); }
        JsonNode cb = node.get("active_casus_belli_identity");
        return new War(positive(required(node, "war_id")), side(required(node, "player_side")),
                nullableBool(required(node, "player_is_primary_war_leader")), nullableNonnegative(required(node, "primary_opponent_character_id")),
                signed(required(node, "player_relative_war_score")), ids, cb == null ? null : cb(cb));
    }

    private static CasusBelli cb(JsonNode value) {
        if (value.isNull()) { return null; }
        ObjectNode node = StrictJson.object(value, Set.of("database_index", "canonical_key"));
        return new CasusBelli(StrictJson.integer(node.get("database_index"), BigInteger.ZERO, INT32_MAX), StrictJson.text(node.get("canonical_key")));
    }

    private static ScoreBreakdown breakdown(JsonNode value) {
        if (value.isNull()) { return null; }
        ObjectNode node = StrictJson.object(value, Set.of("imprisonment", "battles", "occupation", "ticking"));
        return new ScoreBreakdown(signed(node.get("imprisonment")), signed(node.get("battles")), signed(node.get("occupation")), signed(node.get("ticking")));
    }

    private static Side side(JsonNode value) {
        String text = StrictJson.text(value); StrictJson.require(Set.of("attacker", "defender").contains(text), "known side required");
        return "attacker".equals(text) ? Side.ATTACKER : Side.DEFENDER;
    }

    private static ObjectNode encodeWar(War value) {
        ObjectNode node = encodeStable(value.stable()); node.put("player_relative_war_score", value.score());
        if (value.currentCasusBelli() != null) { node.set("active_casus_belli_identity", encodeCb(value.currentCasusBelli())); }
        return node;
    }

    private static ObjectNode encodeStable(StableWar value) {
        ObjectNode node = StrictJson.object(); node.put("war_id", value.warId()); node.put("player_side", sideText(value.side()));
        nullable(node, "player_is_primary_war_leader", value.primaryLeader()); nullable(node, "primary_opponent_character_id", value.opponentId());
        ArrayNode titles = node.putArray("targeted_title_ids"); value.targetedTitleIds().forEach(titles::add); return node;
    }

    private static ObjectNode encodeContext(QueryContext value) {
        ObjectNode node = StrictJson.object(); node.put("schema_version", value.schemaVersion());
        ArrayNode wars = node.putArray("active_war_signature");
        for (StableWar war : value.activeWars()) { ObjectNode item = encodeStable(war); item.put("player_relative_war_score", 0); wars.add(item); }
        node.put("queried_episode_run_id", value.episodeRunId()); node.put("queried_connection_generation", value.connectionGeneration());
        node.put("queried_character_id", value.actorId()); node.set("negative_decision_signature", encodeSignature(value.negativeSignature()));
        nullable(node, "queried_war_duration_days", value.durationDays()); node.put("queried_date_raw", value.queriedDateRaw()); return node;
    }

    private static ObjectNode encodeSignature(NegativeSignature value) {
        ObjectNode node = StrictJson.object(); node.put("war_id", value.warId()); node.put("player_side", sideText(value.playerSide()));
        nullable(node, "player_is_primary_war_leader", value.primaryLeader()); node.put("player_relative_war_score", value.score());
        nullable(node, "absolute_war_scores_observable", value.absoluteScoresObservable()); nullable(node, "attacker_war_score", value.attackerScore());
        nullable(node, "defender_war_score", value.defenderScore());
        if (value.scoreBreakdown() == null) { node.putNull("war_score_breakdown"); }
        else {
            ObjectNode score = node.putObject("war_score_breakdown"); score.put("imprisonment", value.scoreBreakdown().imprisonment());
            score.put("battles", value.scoreBreakdown().battles()); score.put("occupation", value.scoreBreakdown().occupation()); score.put("ticking", value.scoreBreakdown().ticking());
        }
        nullable(node, "active_casus_belli_present", value.activeCasusBelliPresent()); node.set("active_casus_belli_identity", encodeCb(value.activeCasusBelli()));
        nullable(node, "cb_allows_white_peace", value.allowsWhitePeace()); ObjectNode options = node.putObject("options");
        options.set("surrender", encodeOption(value.options().surrender())); options.set("white_peace", encodeOption(value.options().whitePeace()));
        options.set("victory", encodeOption(value.options().victory())); return node;
    }

    private static ObjectNode encodeOption(OptionSignature value) {
        ObjectNode node = StrictJson.object(); node.put("outcome", value.outcome()); node.put("hostage_variant", value.hostageVariant());
        nullable(node, "context_constructed", value.contextConstructed()); nullable(node, "native_validator_passed", value.nativeValidatorPassed());
        nullable(node, "available", value.available()); ObjectNode response = node.putObject("recipient_response"); response.put("status", value.recipientResponse().status());
        nullable(response, "decision_status_raw", value.recipientResponse().decisionStatusRaw()); nullable(response, "would_accept_now", value.recipientResponse().wouldAcceptNow());
        NativeInteractionRoles.putOption(node, value.recipientContext()); return node;
    }

    private static JsonNode encodeCb(CasusBelli value) {
        if (value == null) { return NullNode.getInstance(); }
        ObjectNode node = StrictJson.object(); node.put("database_index", value.databaseIndex()); node.put("canonical_key", value.canonicalKey()); return node;
    }

    private static ObjectNode object(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "JSON object required"); return (ObjectNode) node;
    }
    private static JsonNode required(JsonNode node, String name) {
        StrictJson.require(node != null && node.isObject() && node.has(name), "missing required field: " + name); return node.get(name);
    }
    private static boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "exact JSON boolean required"); return node.booleanValue();
    }
    private static Boolean nullableBool(JsonNode node) { return node.isNull() ? null : bool(node); }
    private static BigInteger positive(JsonNode node) { return StrictJson.integer(node, BigInteger.ONE, MAX_INTEGER); }
    private static BigInteger nonnegative(JsonNode node) { return StrictJson.integer(node, BigInteger.ZERO, MAX_INTEGER); }
    private static BigInteger signed(JsonNode node) { return StrictJson.integer(node, INT32_MIN, INT32_MAX); }
    private static BigInteger nullableSigned(JsonNode node) { return node.isNull() ? null : signed(node); }
    private static BigInteger nullableNonnegative(JsonNode node) { return node.isNull() ? null : nonnegative(node); }
    private static boolean objectMarker(JsonNode node) {
        StrictJson.require(node.isNull() || node.isObject(), "object or null marker required"); return node.isObject();
    }
    private static boolean modalPresent(JsonNode node) {
        if (node == null || node.isNull()) { return false; }
        ObjectNode modal = object(node); return modal.has("status") && "present".equals(StrictJson.text(modal.get("status")));
    }
    private static String sideText(Side side) { return side == Side.ATTACKER ? "attacker" : "defender"; }
    private static void marker(ObjectNode node, String key, boolean present) { if (present) { node.putObject(key); } else { node.putNull(key); } }
    private static void nullable(ObjectNode node, String key, Boolean value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void nullable(ObjectNode node, String key, String value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void nullable(ObjectNode node, String key, BigInteger value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
}
