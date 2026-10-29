package org.xar.ck3.control.wave2.military.armyinventory;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Read-only physical inventory validation. Shape validity never authorizes an action or date. */
public final class ArmyInventoryValidation {
    private static final String SOURCE_BUILD = "CK3 1.19.0.6";
    private static final String H3937_EPISODE = "native-29829-2bc2d599f7f9";
    private static final BigInteger H3937_ACTOR = BigInteger.valueOf(29_829);
    private static final BigInteger H3937_WAR = BigInteger.valueOf(16_777_231);
    private static final BigInteger H3937_SUBJECT = BigInteger.valueOf(83_886_367);
    private static final Set<String> MAILBOX_KEYS = Set.of("source_build", "status", "date_raw", "war_id",
            "subject_army_id", "native_revision", "query_sequence", "mailbox_pump_epoch", "mailbox_thread_id",
            "mailbox_date_raw", "mailbox_paused", "same_source_across_route", "storage_capacity", "slots_scanned",
            "empty_slots", "canonical_units", "invalid_id_slots", "noncanonical_slots", "unresolved_slots",
            "player_army_ids", "allied_army_ids", "hostile_army_ids", "contact_hostile_army_ids",
            "retreating_hostile_army_ids", "units");
    private static final Set<String> UNIT_KEYS = Set.of("army_id", "owner_character_id", "current_province_id",
            "route_province_ids", "route_read_status", "route_source_count", "army_state_code", "in_combat",
            "retreating", "controllable", "war_side");
    private static final List<String> IDENTITY_KEYS = List.of("snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "played_character", "active_wars", "player_armies", "map_ready", "paused",
            "episode_character_id", "active_event", "pending_character_interaction", "route_contact_horizon_supported");
    private static final List<String> COUNT_KEYS = List.of("storage_capacity", "slots_scanned", "empty_slots",
            "canonical_units", "invalid_id_slots", "noncanonical_slots", "unresolved_slots");
    private static final Set<String> EXPECTED_KEYS = Set.of("date_raw", "war_id", "subject_army_id", "snapshot_id",
            "revision", "native_revision", "episode_run_id", "connection_generation", "published_player_ids",
            "published_allied_ids", "published_enemy_ids", "contact_request_ids", "contact_result_ids");

    private ArmyInventoryValidation() { }

    public enum Reason {
        INVENTORY_UNAVAILABLE_OR_PARTIAL, SOURCE_BUILD_MISMATCH, DATE_RAW_MISMATCH, WAR_ID_MISMATCH,
        SUBJECT_ARMY_ID_MISMATCH, SNAPSHOT_ID_MISMATCH, REVISION_MISMATCH, NATIVE_REVISION_MISMATCH,
        EPISODE_RUN_ID_MISMATCH, CONNECTION_GENERATION_MISMATCH, SCAN_COUNTS_INVALID,
        SCAN_INCOMPLETE_OR_UNRESOLVED, UNIT_ROWS_INCOMPLETE, UNIT_ROW_INVALID, UNIT_ID_INVALID_OR_DUPLICATE,
        WAR_SIDE_UNCLASSIFIED, OWNER_OR_PROVINCE_UNRESOLVED, RETREAT_STATE_UNRESOLVED,
        CONTROL_STATE_UNRESOLVED, ARMY_STATE_UNRESOLVED, COMBAT_STATE_UNRESOLVED, ARMY_STATE_RISK_UNPROVEN,
        HOSTILE_ROUTE_INCOMPLETE, SUBJECT_UNRESOLVED, FRIENDLY_SET_NONCANONICAL, PLAYER_ARMY_SET_MISMATCH,
        ALLIED_ARMY_SET_MISMATCH, HOSTILE_SET_NONCANONICAL, PHYSICAL_PUBLISHED_SET_MISMATCH, HOSTILE_SET_EMPTY,
        RETREATING_HOSTILE_RISK_UNPROVEN, CONTACT_SET_MISMATCH, SHAPE_VALID_ONLY,
        MAILBOX_RECEIPT_MISSING_OR_EXTRA_FIELDS, MAILBOX_UNIT_ROWS_MALFORMED, MAILBOX_SOURCE_OR_FRAME_MISMATCH,
        PUBLIC_FRAME_CHANGED, CAPABILITY_FRAME_CHANGED, PLAYED_CHARACTER_MISSING, H3937_ACTOR_BINDING_MISMATCH,
        EPISODE_ACTOR_BINDING_MISMATCH, PLAYED_CHARACTER_SUBJECT_MISMATCH, CONNECTION_GENERATION_MISSING,
        PUBLIC_FRAME_TOKEN_MISSING, H3937_EPISODE_OR_SUBJECT_MISMATCH, WAR_SCOPE_AMBIGUOUS, WAR_ID_MISSING,
        H3937_WAR_MISMATCH, PUBLISHED_ARMY_ROSTER_MALFORMED, ROUTE_CONTACT_RESULT_MISSING;

        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }

    public record Check(boolean valid, Reason reason, List<BigInteger> hostileArmyIds,
                        List<BigInteger> contactHostileArmyIds) {
        public Check {
            Objects.requireNonNull(reason, "reason");
            hostileArmyIds = List.copyOf(hostileArmyIds); contactHostileArmyIds = List.copyOf(contactHostileArmyIds);
            StrictJson.require(valid == (reason == Reason.SHAPE_VALID_ONLY), "shape result and reason disagree");
            StrictJson.require(valid || hostileArmyIds.isEmpty() && contactHostileArmyIds.isEmpty(),
                    "rejected evidence cannot carry validated armies");
            if (valid) {
                requireCanonical(hostileArmyIds); requireCanonical(contactHostileArmyIds);
                StrictJson.require(!hostileArmyIds.isEmpty() && hostileArmyIds.equals(contactHostileArmyIds),
                        "successful inventory must retain every physical hostile in contact scope");
            }
        }
        public boolean dateOrActionAuthorized() { return false; }
    }

    private record Ids(boolean canonical, List<BigInteger> values) {
        private Ids { values = List.copyOf(values); }
    }

    /** Expected arguments are a new exact wire contract; old receipt containers remain projections. */
    private sealed interface Input permits ShapeInput, MailboxInput { Check evaluate(); }
    private record ShapeInput(JsonNode receipt, ObjectNode expected) implements Input {
        @Override public Check evaluate() { return shape(receipt, expected); }
    }
    private record MailboxInput(JsonNode receipt, JsonNode starting, JsonNode current, JsonNode horizon,
                                BigInteger sequence, BigInteger subject, JsonNode requested) implements Input {
        @Override public Check evaluate() { return mailbox(receipt, starting, current, horizon, sequence, subject, requested); }
    }

    /** Input contract only; Check result invariants and encoding remain outside decode. */
    public static void validateRequest(byte[] input) { decodeInput(input); }

    public static byte[] validate(byte[] input) { return encode(decodeInput(input).evaluate()); }

    private static Input decodeInput(byte[] input) {
        JsonNode root = StrictJson.parse(input);
        String mode = StrictJson.text(root.get("mode"));
        if (mode.equals("shape")) {
            StrictJson.object(root, Set.of("mode", "receipt", "expected"));
            ObjectNode expected = StrictJson.object(root.get("expected"), EXPECTED_KEYS);
            validateExpected(expected);
            return new ShapeInput(root.get("receipt"), expected);
        } else if (mode.equals("mailbox")) {
            StrictJson.object(root, Set.of("mode", "native_receipt", "starting", "current", "horizon",
                    "query_sequence", "subject_army_id", "requested_hostiles"));
            BigInteger sequence = requiredInteger(root.get("query_sequence"), false);
            BigInteger subject = requiredInteger(root.get("subject_army_id"), false);
            JsonNode requested = root.get("requested_hostiles");
            StrictJson.require(requested != null && requested.isArray(), "requested_hostiles array required");
            return new MailboxInput(root.get("native_receipt"), root.get("starting"), root.get("current"),
                    root.get("horizon"), sequence, subject, requested);
        } else { throw new ContractViolationException("unknown inventory validation mode"); }
    }

    public static byte[] encode(Check check) {
        ObjectNode result = StrictJson.object(); result.put("valid", check.valid()); result.put("reason", check.reason().wire());
        var hostile = result.putArray("hostile_army_ids"); check.hostileArmyIds().forEach(hostile::add);
        var contact = result.putArray("contact_hostile_army_ids"); check.contactHostileArmyIds().forEach(contact::add);
        result.put("date_or_action_authorized", false); return StrictJson.canonical(result);
    }

    private static void validateExpected(ObjectNode expected) {
        for (String key : List.of("date_raw", "war_id", "subject_army_id", "revision", "native_revision", "connection_generation")) {
            requiredInteger(expected.get(key), false);
        }
        StrictJson.require(expected.get("snapshot_id").isTextual() && expected.get("episode_run_id").isTextual(),
                "expected identity strings required");
        // Published arrays are validated in the original friendly/hostile reason order below.
    }

    private static Check shape(JsonNode receipt, JsonNode expected) {
        if (!object(receipt) || !textEquals(receipt.get("status"), "complete")) {
            return red(Reason.INVENTORY_UNAVAILABLE_OR_PARTIAL);
        }
        if (!textEquals(receipt.get("source_build"), SOURCE_BUILD)) { return red(Reason.SOURCE_BUILD_MISMATCH); }
        for (String key : List.of("date_raw", "war_id", "subject_army_id", "snapshot_id", "revision", "native_revision",
                "episode_run_id", "connection_generation")) {
            if (!sameTyped(receipt.get(key), expected.get(key))) { return red(identityReason(key)); }
        }
        for (String key : COUNT_KEYS) { if (!nonnegative(receipt.get(key))) { return red(Reason.SCAN_COUNTS_INVALID); } }
        BigInteger capacity = integer(receipt, "storage_capacity");
        if (capacity.signum() <= 0 || capacity.compareTo(BigInteger.valueOf(1_000_000)) > 0
                || !integer(receipt, "slots_scanned").equals(capacity)
                || !integer(receipt, "empty_slots").add(integer(receipt, "canonical_units"))
                    .add(integer(receipt, "invalid_id_slots")).add(integer(receipt, "noncanonical_slots")).equals(capacity)
                || integer(receipt, "invalid_id_slots").signum() != 0
                || integer(receipt, "noncanonical_slots").signum() != 0
                || integer(receipt, "unresolved_slots").signum() != 0) { return red(Reason.SCAN_INCOMPLETE_OR_UNRESOLVED); }
        JsonNode rows = receipt.get("units");
        if (rows == null || !rows.isArray() || !BigInteger.valueOf(rows.size()).equals(integer(receipt, "canonical_units"))) {
            return red(Reason.UNIT_ROWS_INCOMPLETE);
        }
        Set<BigInteger> seen = new HashSet<>(); List<BigInteger> players = new ArrayList<>();
        List<BigInteger> allies = new ArrayList<>(); List<BigInteger> physical = new ArrayList<>();
        List<BigInteger> contact = new ArrayList<>(); List<BigInteger> retreating = new ArrayList<>();
        boolean subjectFound = false;
        for (JsonNode row : rows) {
            if (!object(row)) { return red(Reason.UNIT_ROW_INVALID); }
            if (!positive(row.get("army_id")) || !seen.add(integer(row, "army_id"))) {
                return red(Reason.UNIT_ID_INVALID_OR_DUPLICATE);
            }
            BigInteger army = integer(row, "army_id"); JsonNode side = row.get("war_side");
            if (side == null || !side.isTextual() || !Set.of("allied", "hostile", "neutral").contains(side.textValue())) {
                return red(Reason.WAR_SIDE_UNCLASSIFIED);
            }
            if (!positive(row.get("owner_character_id")) || !positive(row.get("current_province_id"))) {
                return red(Reason.OWNER_OR_PROVINCE_UNRESOLVED);
            }
            if (!bool(row.get("retreating"))) { return red(Reason.RETREAT_STATE_UNRESOLVED); }
            if (!bool(row.get("controllable"))) { return red(Reason.CONTROL_STATE_UNRESOLVED); }
            if (!positive(row.get("army_state_code")) || integer(row, "army_state_code").compareTo(BigInteger.valueOf(9)) > 0) {
                return red(Reason.ARMY_STATE_UNRESOLVED);
            }
            if (!bool(row.get("in_combat"))) { return red(Reason.COMBAT_STATE_UNRESOLVED); }
            boolean isRetreating = row.get("retreating").booleanValue();
            boolean controlled = row.get("controllable").booleanValue(); String allegiance = side.textValue();
            if (!allegiance.equals("neutral") && (row.get("in_combat").booleanValue()
                    || integer(row, "army_state_code").equals(BigInteger.valueOf(6)) && !isRetreating)) {
                return red(Reason.ARMY_STATE_RISK_UNPROVEN);
            }
            if (army.equals(integer(expected, "subject_army_id"))) {
                subjectFound = allegiance.equals("allied") && completeRoute(row) && controlled;
            }
            if (controlled) { players.add(army); }
            if (allegiance.equals("allied")) { allies.add(army); }
            if (allegiance.equals("hostile")) {
                physical.add(army); if (!completeRoute(row)) { return red(Reason.HOSTILE_ROUTE_INCOMPLETE); }
                if (isRetreating) { retreating.add(army); } else { contact.add(army); }
            }
        }
        if (!subjectFound) { return red(Reason.SUBJECT_UNRESOLVED); }
        Ids observedPlayers = canonical(receipt.get("player_army_ids"));
        Ids observedAllies = canonical(receipt.get("allied_army_ids"));
        Ids publishedPlayers = canonical(expected.get("published_player_ids"));
        Ids publishedAllies = canonical(expected.get("published_allied_ids"));
        if (!observedPlayers.canonical() || !observedAllies.canonical() || !publishedPlayers.canonical()
                || !publishedAllies.canonical()) { return red(Reason.FRIENDLY_SET_NONCANONICAL); }
        if (!observedPlayers.values().equals(sorted(players)) || !observedPlayers.equals(publishedPlayers)) {
            return red(Reason.PLAYER_ARMY_SET_MISMATCH);
        }
        if (!observedAllies.values().equals(sorted(allies)) || !observedAllies.equals(publishedAllies)) {
            return red(Reason.ALLIED_ARMY_SET_MISMATCH);
        }
        Ids hostile = canonical(receipt.get("hostile_army_ids"));
        Ids requested = canonical(receipt.get("contact_hostile_army_ids"));
        Ids excluded = canonical(receipt.get("retreating_hostile_army_ids"));
        Ids published = canonical(expected.get("published_enemy_ids"));
        Ids contactRequest = canonical(expected.get("contact_request_ids"));
        Ids contactResult = canonical(expected.get("contact_result_ids"));
        if (!hostile.canonical() || !requested.canonical() || !excluded.canonical() || !published.canonical()
                || !contactRequest.canonical() || !contactResult.canonical()) { return red(Reason.HOSTILE_SET_NONCANONICAL); }
        if (!hostile.values().equals(sorted(physical)) || !hostile.equals(published)) {
            return red(Reason.PHYSICAL_PUBLISHED_SET_MISMATCH);
        }
        if (hostile.values().isEmpty()) { return red(Reason.HOSTILE_SET_EMPTY); }
        if (!excluded.values().equals(sorted(retreating)) || !excluded.values().isEmpty()) {
            return red(Reason.RETREATING_HOSTILE_RISK_UNPROVEN);
        }
        if (!requested.values().equals(sorted(contact)) || !requested.equals(contactRequest) || !requested.equals(contactResult)) {
            return red(Reason.CONTACT_SET_MISMATCH);
        }
        return new Check(true, Reason.SHAPE_VALID_ONLY, hostile.values(), requested.values());
    }

    private static Check mailbox(JsonNode receipt, JsonNode starting, JsonNode current, JsonNode horizon,
                                 BigInteger querySequence, BigInteger subject, JsonNode requestedHostiles) {
        if (!exactKeys(receipt, MAILBOX_KEYS)) { return red(Reason.MAILBOX_RECEIPT_MISSING_OR_EXTRA_FIELDS); }
        JsonNode rows = receipt.get("units");
        if (rows == null || !rows.isArray()) { return red(Reason.MAILBOX_UNIT_ROWS_MALFORMED); }
        for (JsonNode row : rows) { if (!exactKeys(row, UNIT_KEYS)) { return red(Reason.MAILBOX_UNIT_ROWS_MALFORMED); } }
        if (!object(starting) || !object(current) || !trueValue(starting.get("map_ready"))
                || !trueValue(current.get("map_ready")) || !trueValue(starting.get("paused"))
                || !trueValue(current.get("paused")) || !positive(receipt.get("mailbox_pump_epoch"))
                || !positive(receipt.get("mailbox_thread_id")) || !trueValue(receipt.get("mailbox_paused"))
                || !trueValue(receipt.get("same_source_across_route")) || !integral(receipt.get("mailbox_date_raw"))
                || !sameTyped(receipt.get("mailbox_date_raw"), starting.get("date_raw"))
                || !integral(receipt.get("query_sequence")) || !integer(receipt, "query_sequence").equals(querySequence)
                || !integral(receipt.get("native_revision"))
                || !sameTyped(receipt.get("native_revision"), starting.get("native_revision"))) {
            return red(Reason.MAILBOX_SOURCE_OR_FRAME_MISMATCH);
        }
        for (String key : IDENTITY_KEYS) {
            if (!sameTyped(starting.get(key), current.get(key))) { return red(Reason.PUBLIC_FRAME_CHANGED); }
        }
        Set<String> capabilities = new HashSet<>();
        starting.fieldNames().forEachRemaining(key -> { if (key.endsWith("_supported") || key.equals("capabilities")) { capabilities.add(key); } });
        current.fieldNames().forEachRemaining(key -> { if (key.endsWith("_supported") || key.equals("capabilities")) { capabilities.add(key); } });
        for (String key : capabilities) {
            if (!sameTyped(starting.get(key), current.get(key))) { return red(Reason.CAPABILITY_FRAME_CHANGED); }
        }
        JsonNode actorRow = starting.get("played_character");
        if (!object(actorRow) || !positive(actorRow.get("character_id"))) { return red(Reason.PLAYED_CHARACTER_MISSING); }
        BigInteger actor = integer(actorRow, "character_id");
        if (textEquals(starting.get("episode_run_id"), H3937_EPISODE) && !actor.equals(H3937_ACTOR)) {
            return red(Reason.H3937_ACTOR_BINDING_MISMATCH);
        }
        if (!integral(starting.get("episode_character_id")) || !integer(starting, "episode_character_id").equals(actor)) {
            return red(Reason.EPISODE_ACTOR_BINDING_MISMATCH);
        }
        JsonNode playerRows = starting.get("player_armies"); List<JsonNode> subjects = new ArrayList<>();
        if (playerRows != null && playerRows.isArray()) {
            for (JsonNode row : playerRows) {
                if (object(row) && integral(row.get("army_id")) && integer(row, "army_id").equals(subject)) { subjects.add(row); }
            }
        }
        if (subjects.size() != 1 || !positive(subjects.getFirst().get("owner_character_id"))
                || !integer(subjects.getFirst(), "owner_character_id").equals(actor)
                || !trueValue(subjects.getFirst().get("controllable"))) { return red(Reason.PLAYED_CHARACTER_SUBJECT_MISMATCH); }
        JsonNode startDiag = starting.get("diagnostics"); JsonNode currentDiag = current.get("diagnostics");
        if (!object(startDiag) || !object(currentDiag)) { return red(Reason.CONNECTION_GENERATION_MISSING); }
        if (!positive(startDiag.get("connection_generation"))
                || !sameTyped(startDiag.get("connection_generation"), currentDiag.get("connection_generation"))) {
            return red(Reason.CONNECTION_GENERATION_MISMATCH);
        }
        if (!nonemptyText(starting.get("snapshot_id")) || !nonemptyText(starting.get("episode_run_id"))
                || !positive(starting.get("revision")) || !positive(starting.get("native_revision"))) {
            return red(Reason.PUBLIC_FRAME_TOKEN_MISSING);
        }
        if (!textEquals(starting.get("episode_run_id"), H3937_EPISODE) || !subject.equals(H3937_SUBJECT)) {
            return red(Reason.H3937_EPISODE_OR_SUBJECT_MISMATCH);
        }
        JsonNode wars = starting.get("active_wars");
        if (wars == null || !wars.isArray() || wars.size() != 1 || !object(wars.get(0))) { return red(Reason.WAR_SCOPE_AMBIGUOUS); }
        JsonNode war = wars.get(0);
        if (!positive(war.get("war_id"))) { return red(Reason.WAR_ID_MISSING); }
        if (!integer(war, "war_id").equals(H3937_WAR)) { return red(Reason.H3937_WAR_MISMATCH); }
        Ids players = roster(playerRows); Ids allies = roster(war.get("allied_armies")); Ids enemies = roster(war.get("enemy_armies"));
        if (!players.canonical() || !allies.canonical() || !enemies.canonical()) { return red(Reason.PUBLISHED_ARMY_ROSTER_MALFORMED); }
        JsonNode resultIds = object(horizon) ? horizon.get("hostile_army_ids") : null;
        if (resultIds == null || !resultIds.isArray()) { return red(Reason.ROUTE_CONTACT_RESULT_MISSING); }
        ObjectNode expected = StrictJson.object();
        for (String key : List.of("date_raw", "snapshot_id", "revision", "native_revision", "episode_run_id")) {
            expected.set(key, starting.get(key));
        }
        expected.put("war_id", H3937_WAR); expected.put("subject_army_id", subject);
        expected.set("connection_generation", startDiag.get("connection_generation"));
        putIds(expected, "published_player_ids", players.values()); putIds(expected, "published_allied_ids", allies.values());
        putIds(expected, "published_enemy_ids", enemies.values());
        expected.set("contact_request_ids", requestedHostiles); expected.set("contact_result_ids", resultIds);
        ObjectNode enriched = ((ObjectNode) receipt).deepCopy();
        for (String key : List.of("snapshot_id", "revision", "episode_run_id", "connection_generation")) {
            enriched.set(key, expected.get(key));
        }
        return shape(enriched, expected);
    }

    private static boolean completeRoute(JsonNode row) {
        JsonNode status = row.get("route_read_status"); JsonNode count = row.get("route_source_count");
        JsonNode provinces = row.get("route_province_ids");
        if ((!textEquals(status, "complete_empty") && !textEquals(status, "complete_nonempty")) || !nonnegative(count)
                || provinces == null || !provinces.isArray() || !BigInteger.valueOf(provinces.size()).equals(count.bigIntegerValue())) { return false; }
        for (JsonNode province : provinces) { if (!positive(province)) { return false; } }
        return textEquals(status, "complete_empty") ? count.bigIntegerValue().signum() == 0 : count.bigIntegerValue().signum() > 0;
    }
    private static Ids canonical(JsonNode value) {
        if (value == null || !value.isArray()) { return new Ids(false, List.of()); }
        List<BigInteger> values = new ArrayList<>(); BigInteger prior = BigInteger.ZERO;
        for (JsonNode node : value) {
            if (!positive(node) || node.bigIntegerValue().compareTo(prior) <= 0) { return new Ids(false, List.of()); }
            values.add(node.bigIntegerValue()); prior = node.bigIntegerValue();
        }
        return new Ids(true, values);
    }
    private static Ids roster(JsonNode rows) {
        if (rows == null || !rows.isArray()) { return new Ids(false, List.of()); }
        List<BigInteger> result = new ArrayList<>(); Set<BigInteger> seen = new HashSet<>();
        for (JsonNode row : rows) {
            if (!object(row) || !positive(row.get("army_id")) || !seen.add(integer(row, "army_id"))) { return new Ids(false, List.of()); }
            result.add(integer(row, "army_id"));
        }
        return new Ids(true, sorted(result));
    }
    private static List<BigInteger> sorted(List<BigInteger> value) { return value.stream().sorted().toList(); }
    private static BigInteger requiredInteger(JsonNode value, boolean positive) {
        StrictJson.require(integral(value) && (!positive || value.bigIntegerValue().signum() > 0), "exact integer required");
        return value.bigIntegerValue();
    }
    private static BigInteger integer(JsonNode value, String field) { return value.get(field).bigIntegerValue(); }
    private static boolean integral(JsonNode value) { return value != null && value.isIntegralNumber(); }
    private static boolean nonnegative(JsonNode value) { return integral(value) && value.bigIntegerValue().signum() >= 0; }
    private static boolean positive(JsonNode value) { return integral(value) && value.bigIntegerValue().signum() > 0; }
    private static boolean bool(JsonNode value) { return value != null && value.isBoolean(); }
    private static boolean trueValue(JsonNode value) { return bool(value) && value.booleanValue(); }
    private static boolean object(JsonNode value) { return value != null && value.isObject(); }
    private static boolean nonemptyText(JsonNode value) { return value != null && value.isTextual() && !value.textValue().isEmpty(); }
    private static boolean textEquals(JsonNode value, String text) { return value != null && value.isTextual() && value.textValue().equals(text); }
    private static boolean sameTyped(JsonNode left, JsonNode right) { return left != null && right != null && left.equals(right); }
    private static boolean exactKeys(JsonNode value, Set<String> expected) {
        if (!object(value)) { return false; } Set<String> actual = new HashSet<>(); value.fieldNames().forEachRemaining(actual::add);
        return actual.equals(expected);
    }
    private static Check red(Reason reason) { return new Check(false, reason, List.of(), List.of()); }
    private static Reason identityReason(String key) {
        return switch (key) {
            case "date_raw" -> Reason.DATE_RAW_MISMATCH; case "war_id" -> Reason.WAR_ID_MISMATCH;
            case "subject_army_id" -> Reason.SUBJECT_ARMY_ID_MISMATCH; case "snapshot_id" -> Reason.SNAPSHOT_ID_MISMATCH;
            case "revision" -> Reason.REVISION_MISMATCH; case "native_revision" -> Reason.NATIVE_REVISION_MISMATCH;
            case "episode_run_id" -> Reason.EPISODE_RUN_ID_MISMATCH;
            case "connection_generation" -> Reason.CONNECTION_GENERATION_MISMATCH;
            default -> throw new IllegalArgumentException("not an identity field");
        };
    }
    private static void putIds(ObjectNode target, String field, List<BigInteger> values) {
        var array = target.putArray(field); values.forEach(array::add);
    }
    private static void requireCanonical(List<BigInteger> values) {
        BigInteger prior = BigInteger.ZERO;
        for (BigInteger value : values) {
            StrictJson.require(value.compareTo(prior) > 0, "validated identities must be strictly increasing positive integers");
            prior = value;
        }
    }
}
