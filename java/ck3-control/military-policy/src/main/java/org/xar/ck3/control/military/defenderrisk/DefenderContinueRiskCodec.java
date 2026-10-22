package org.xar.ck3.control.military.defenderrisk;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.Blocker;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.Contact;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.ContactStatus;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.ConflictEvidence;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.Envelope;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.Frame;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.ObservedContact;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.ObservedSiege;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.OffsiteArrival;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.Request;
import org.xar.ck3.control.military.defenderrisk.DefenderContinueRisk.Siege;

/** The sole dynamic JSON boundary for this leaf; no object-to-domain coercion. */
public final class DefenderContinueRiskCodec {
    private static final ObjectMapper OPAQUE_JSON = new ObjectMapper();
    private static final Set<String> FRAME_FIELDS = Set.of("snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "connection_generation", "played_character_id", "war_id", "player_relative_war_score");
    private static final Set<String> CONTACT_FIELDS = Set.of("source_frame", "source_sha256", "subject_army_id",
            "target_province_id", "horizon_start_date_raw", "horizon_end_date_raw", "one_day_contact_free", "conflicts",
            "first_waypoint_arrival_date_raw", "subject_target_arrival_date_raw", "offsite_target_arrivals");
    private static final Set<String> SIEGE_FIELDS = Set.of("source_frame", "source_sha256", "province_id",
            "besieging_army_ids", "remaining_days_estimate");
    private static final Set<String> OFFSITE_FIELDS = Set.of("army_id", "arrival_date_raw");

    private DefenderContinueRiskCodec() { }

    /** Adapter envelope always contains all three keys; JSON null represents an absent optional observation. */
    public static Request decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("frame", "contact", "siege"));
        Frame frame = frame(root.get("frame"));
        return new Request(frame, root.get("contact").isNull() ? null : contact(root.get("contact")),
                root.get("siege").isNull() ? null : siege(root.get("siege")));
    }

    public static byte[] evaluate(byte[] raw) {
        return encode(DefenderContinueRisk.observe(decode(raw)));
    }

    /** Round-trip the adapter domain, retaining explicit nulls and opaque conflict evidence. */
    public static byte[] encodeRequest(Request request) {
        require(request != null, "risk request required");
        ObjectNode root = StrictJson.object();
        root.set("frame", frameNode(request.frame()));
        root.set("contact", request.contact() == null ? NullNode.instance : contactNode(request.contact()));
        root.set("siege", request.siege() == null ? NullNode.instance : siegeNode(request.siege()));
        // Conflicts can contain arbitrary JSON numbers in the original producer. They are never interpreted.
        return opaqueBytes(root);
    }

    public static byte[] encode(Envelope envelope) {
        require(envelope != null, "risk envelope required");
        ObjectNode root = StrictJson.object();
        root.put("policy", DefenderContinueRisk.POLICY);
        root.put("status", "partial_bounded_observation_no_exit_comparison");
        root.put("read_only", true);
        root.set("frame", frameNode(envelope.frame()));
        ObjectNode score = root.putObject("current_score");
        score.put("status", "observed_current_only");
        score.put("player_relative_war_score", envelope.frame().playerRelativeWarScore());
        score.putNull("future_score_bound");
        score.put("trend_inferred", false);
        ObjectNode contact = root.putObject("contact");
        contact.put("current_orders_only", true);
        contact.put("offsite_roster_complete_proven", false);
        if (envelope.contact() instanceof ObservedContact observed) {
            contact.put("status", observed.status().wire());
            if (observed.status() == ContactStatus.BOUNDED_CURRENT_ORDERS_ONE_DAY_ONLY) {
                contact.putNull("reason");
            } else { contact.put("reason", "no_verified_contact_free_game_day"); }
            putNullable(contact, "contact_free_through_raw", observed.contactFreeThroughRaw());
            if (observed.firstWaypointOutsideProvenWindow() == null) {
                contact.putNull("first_waypoint_outside_proven_window");
            } else { contact.put("first_waypoint_outside_proven_window", observed.firstWaypointOutsideProvenWindow()); }
            contact.put("offsite_target_arrival_order", observed.arrivalOrder().wire());
            putNullable(contact, "target_arrival_date_raw", observed.targetArrivalDateRaw());
            contact.put("source_sha256", observed.sourceSha256());
        } else {
            contact.put("status", "typed_unavailable");
            contact.put("reason", "same_frame_route_contact_required");
            contact.putNull("contact_free_through_raw");
            contact.putNull("first_waypoint_outside_proven_window");
            contact.put("offsite_target_arrival_order", "unavailable");
            contact.putNull("target_arrival_date_raw");
        }
        ObjectNode siege = root.putObject("siege");
        siege.put("completion_upper_bound_proven", false);
        if (envelope.siege() instanceof ObservedSiege observed) {
            siege.put("status", "current_timer_estimate_only");
            siege.putNull("reason");
            siege.put("province_id", observed.provinceId());
            ArrayNode armies = siege.putArray("besieging_army_ids");
            observed.besiegingArmyIds().forEach(armies::add);
            siege.put("remaining_days_estimate", observed.remainingDaysEstimate());
            siege.put("completion_estimate_raw", observed.completionEstimateRaw());
            siege.put("source_sha256", observed.sourceSha256());
        } else {
            siege.put("status", "typed_unavailable");
            siege.put("reason", "same_frame_siege_clock_required");
            siege.putNull("completion_estimate_raw");
        }
        ObjectNode assets = root.putObject("asset_exposure");
        assets.put("status", "typed_unavailable");
        assets.put("reason", "current_material_effects_and_asset_valuation_required");
        assets.putNull("tail_loss_upper_raw");
        root.putNull("continuation_loss_upper_raw");
        root.putNull("continuation_win_probability");
        root.putNull("surrender_vs_continue_utility_interval");
        root.put("material_comparison_ready", false);
        root.putNull("recommended_outcome");
        root.putNull("action_literal");
        ArrayNode blockers = root.putArray("blockers");
        envelope.blockers().stream().map(Blocker::wire).sorted().distinct().forEach(blockers::add);
        return StrictJson.canonical(root);
    }

    static String normalizeConflictJson(String json) {
        JsonNode node = StrictJson.parse(json.getBytes(StandardCharsets.UTF_8));
        return new String(opaqueBytes(node), StandardCharsets.UTF_8);
    }

    private static byte[] opaqueBytes(JsonNode node) {
        try {
            byte[] raw = OPAQUE_JSON.writeValueAsBytes(node);
            require(raw.length <= StrictJson.INPUT_MAX_BYTES, "risk adapter payload exceeds byte budget");
            return raw;
        } catch (JsonProcessingException error) {
            throw new ContractViolationException("risk adapter JSON serialization failed", error);
        }
    }

    private static Frame frame(JsonNode value) {
        ObjectNode row = StrictJson.object(value, FRAME_FIELDS);
        return new Frame(StrictJson.text(row.get("snapshot_id")), integer(row.get("revision")),
                integer(row.get("native_revision")), integer(row.get("date_raw")),
                StrictJson.text(row.get("episode_run_id")), integer(row.get("connection_generation")),
                integer(row.get("played_character_id")), integer(row.get("war_id")),
                integer(row.get("player_relative_war_score")));
    }

    private static Contact contact(JsonNode value) {
        ObjectNode row = StrictJson.object(value, CONTACT_FIELDS);
        require(row.get("one_day_contact_free").isBoolean(), "one_day_contact_free must be boolean");
        require(row.get("conflicts").isArray(), "conflicts must be a list");
        List<ConflictEvidence> conflicts = new ArrayList<>();
        for (JsonNode conflict : row.get("conflicts")) {
            conflicts.add(new ConflictEvidence(new String(opaqueBytes(conflict), StandardCharsets.UTF_8)));
        }
        require(row.get("offsite_target_arrivals").isArray(), "offsite arrivals must be a list");
        List<OffsiteArrival> arrivals = new ArrayList<>();
        for (JsonNode valueRow : row.get("offsite_target_arrivals")) {
            ObjectNode arrival = StrictJson.object(valueRow, OFFSITE_FIELDS);
            arrivals.add(new OffsiteArrival(integer(arrival.get("army_id")), integer(arrival.get("arrival_date_raw"))));
        }
        return new Contact(frame(row.get("source_frame")), StrictJson.text(row.get("source_sha256")),
                integer(row.get("subject_army_id")), integer(row.get("target_province_id")),
                integer(row.get("horizon_start_date_raw")), integer(row.get("horizon_end_date_raw")),
                row.get("one_day_contact_free").booleanValue(), conflicts,
                nullableInteger(row.get("first_waypoint_arrival_date_raw")),
                nullableInteger(row.get("subject_target_arrival_date_raw")), arrivals);
    }

    private static Siege siege(JsonNode value) {
        ObjectNode row = StrictJson.object(value, SIEGE_FIELDS);
        require(row.get("besieging_army_ids").isArray(), "siege besieger list invalid");
        List<BigInteger> armies = new ArrayList<>();
        row.get("besieging_army_ids").forEach(army -> armies.add(integer(army)));
        return new Siege(frame(row.get("source_frame")), StrictJson.text(row.get("source_sha256")),
                integer(row.get("province_id")), armies, integer(row.get("remaining_days_estimate")));
    }

    private static BigInteger integer(JsonNode node) {
        require(node != null && node.isIntegralNumber(), "exact JSON integer required; no boolean, float or string");
        return node.bigIntegerValue();
    }
    private static BigInteger nullableInteger(JsonNode node) {
        require(node != null, "required nullable integer field missing");
        return node.isNull() ? null : integer(node);
    }
    private static ObjectNode frameNode(Frame frame) {
        ObjectNode row = StrictJson.object();
        row.put("snapshot_id", frame.snapshotId());
        row.put("revision", frame.revision());
        row.put("native_revision", frame.nativeRevision());
        row.put("date_raw", frame.dateRaw());
        row.put("episode_run_id", frame.episodeRunId());
        row.put("connection_generation", frame.connectionGeneration());
        row.put("played_character_id", frame.playedCharacterId());
        row.put("war_id", frame.warId());
        row.put("player_relative_war_score", frame.playerRelativeWarScore());
        return row;
    }
    private static ObjectNode contactNode(Contact contact) {
        ObjectNode row = StrictJson.object();
        row.set("source_frame", frameNode(contact.sourceFrame()));
        row.put("source_sha256", contact.sourceSha256());
        row.put("subject_army_id", contact.subjectArmyId());
        row.put("target_province_id", contact.targetProvinceId());
        row.put("horizon_start_date_raw", contact.horizonStartDateRaw());
        row.put("horizon_end_date_raw", contact.horizonEndDateRaw());
        row.put("one_day_contact_free", contact.oneDayContactFree());
        ArrayNode conflicts = row.putArray("conflicts");
        contact.conflicts().forEach(conflict -> conflicts.add(StrictJson.parse(conflict.json().getBytes(StandardCharsets.UTF_8))));
        putNullable(row, "first_waypoint_arrival_date_raw", contact.firstWaypointArrivalDateRaw());
        putNullable(row, "subject_target_arrival_date_raw", contact.subjectTargetArrivalDateRaw());
        ArrayNode arrivals = row.putArray("offsite_target_arrivals");
        for (OffsiteArrival arrival : contact.offsiteTargetArrivals()) {
            ObjectNode entry = StrictJson.object();
            entry.put("army_id", arrival.armyId());
            entry.put("arrival_date_raw", arrival.arrivalDateRaw());
            arrivals.add(entry);
        }
        return row;
    }
    private static ObjectNode siegeNode(Siege siege) {
        ObjectNode row = StrictJson.object();
        row.set("source_frame", frameNode(siege.sourceFrame()));
        row.put("source_sha256", siege.sourceSha256());
        row.put("province_id", siege.provinceId());
        ArrayNode armies = row.putArray("besieging_army_ids");
        siege.besiegingArmyIds().forEach(armies::add);
        row.put("remaining_days_estimate", siege.remainingDaysEstimate());
        return row;
    }
    private static void putNullable(ObjectNode node, String name, BigInteger value) {
        if (value == null) { node.putNull(name); } else { node.put(name, value); }
    }
}
