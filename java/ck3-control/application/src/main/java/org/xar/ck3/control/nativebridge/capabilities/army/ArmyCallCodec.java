package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.Frame;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** One closed public JSON boundary for all 47 Army Service methods, including local/composite methods. */
public final class ArmyCallCodec {
    private ArmyCallCodec() { }
    public static Call decode(PublicMethod method, RawJson arguments) {
        need(method != null && method.group() == PublicMethod.Group.ARMY, "not an Army Service method");
        ObjectNode n = parse(arguments.bytes());
        return switch (method) {
            case WAR_STATE -> { shape(n, "", ""); yield new Empty(); }
            case QUERY_WAR_DECLARED_OVERVIEW_V1, CLOSE_WAR_DECLARED_OVERVIEW_V1,
                    QUERY_WAR_RESULTS_WINDOW_V1, CLOSE_WAR_RESULTS_WINDOW_V1,
                    QUERY_PLAYER_MERCENARY_CONTEXT_V1, QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> {
                shape(n, "expected_revision", ""); yield new Frame(method, revision(n, true)); }
            case QUERY_DECLARABLE_WARS, RAISE_TROOPS_DEFAULT, QUERY_PLAYER_DEFAULT_RAISE_V1 -> {
                shape(n, "", "expected_revision"); yield new Frame(method, revision(n, false)); }
            case ENFORCE_DEMANDS, QUERY_WAR_OCCUPATION_TARGETS_V1, QUERY_WAR_TERMINATION_OPTIONS,
                    QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS, QUERY_WAR_TERMINATION_TERMS,
                    QUERY_WAR_TERMINATION_EXIT_TERMS, SURRENDER_WAR, OFFER_WHITE_PEACE -> {
                shape(n, "war_id", "expected_revision"); yield new War(method, revision(n, false), safe(get(n, "war_id"))); }
            case DISBAND_ARMY -> { shape(n, "army_id", "expected_revision"); yield new Unit(method, revision(n, false), unit(n.get("army_id"))); }
            case QUERY_BATTLE_CONTROL_SNAPSHOT_V1 -> { shape(n, "subject_public_cunit_id expected_revision", ""); yield new Unit(method, revision(n, true), unit(n.get("subject_public_cunit_id"))); }
            case QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1 -> { shape(n, "selected_public_cunit_id expected_revision", ""); yield new Unit(method, revision(n, true), unit(n.get("selected_public_cunit_id"))); }
            case START_ASSAULT, STOP_ASSAULT -> { shape(n, "siege_id", "expected_revision"); yield new Siege(method, revision(n, false), id(n.get("siege_id"))); }
            case DECLARE_WAR -> { shape(n, "declaration_id", "expected_revision"); yield new Declaration(method, revision(n, false), text(n.get("declaration_id"))); }
            case QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1,
                    QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2 -> {
                shape(n, "declaration_id expected_revision", ""); yield new Declaration(method, revision(n, true), text(n.get("declaration_id"))); }
            case QUERY_PLAYER_TRUCE_EXPIRY_V1 -> { shape(n, "toward_character_id expected_revision", ""); yield new Truce(revision(n, true), id(n.get("toward_character_id"))); }
            case COLLECT_DECLARABLE_WARS_RESULT_V1 -> { shape(n, "request_id expected_revision", ""); yield new Collect(revision(n, true), text(n.get("request_id"))); }
            case SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1 -> { shape(n, "war_id recipient_character_id expected_revision", ""); yield new CallAlly(revision(n, true), full(n.get("war_id")), full(n.get("recipient_character_id"))); }
            case SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1 -> {
                shape(n, "type_index action_id expected_revision", "timeout_seconds"); Revision r = revision(n, true); positiveRevision(r);
                yield new CreateMaa(r, nonnegative(n.get("type_index")), text(n.get("action_id")), field(n, "timeout_seconds", ArmyCallCodec::decimal)); }
            case MOVE_ARMY -> { shape(n, "army_id target_province_id", "expected_revision"); yield new Move(revision(n, false), unit(n.get("army_id")), id(n.get("target_province_id"))); }
            case HIRE_MERCENARY_V1, HIRE_HOLY_ORDER_V1 -> { String key = method == PublicMethod.HIRE_MERCENARY_V1 ? "company_id" : "holy_order_id";
                shape(n, key + " expected_revision", ""); yield new Hire(method, revision(n, true), hire(n.get(key))); }
            case QUERY_ARMY_COMMANDER_CANDIDATES_V1 -> { shape(n, "army_id", "expected_revision target_province_id");
                yield new Commander(revision(n, false), unit(n.get("army_id")), field(n, "target_province_id", ArmyJson::id)); }
            case ASSIGN_ARMY_COMMANDER_V1 -> { shape(n, "army_id commander_character_id expected_revision", "");
                yield new AssignCommander(revision(n, true), unit(n.get("army_id")), unit(n.get("commander_character_id"))); }
            case SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> { shape(n, "enabled expected_revision", ""); yield new Sampling(revision(n, true), bool(n.get("enabled"))); }
            case QUERY_ARMY_STRENGTHS -> { shape(n, "army_ids", "expected_revision profile ordered_refill_entry_mode ordered_besieging_entry_mode");
                yield new Strengths(revision(n, false), array(n.get("army_ids"), ArmyJson::unit),
                        field(n, "profile", v -> choice(v, StrengthProfile.class)), field(n, "ordered_refill_entry_mode", v -> choice(v, EntryMode.class)),
                        field(n, "ordered_besieging_entry_mode", v -> choice(v, EntryMode.class))); }
            case QUERY_BATTLE_TRANSITION_V1, QUERY_COMBAT_PHASE_EVENT_TRACE_V1 -> { shape(n, "combat_id" + (method == PublicMethod.QUERY_BATTLE_TRANSITION_V1 ? " expected_revision" : ""),
                        method == PublicMethod.QUERY_BATTLE_TRANSITION_V1 ? "" : "expected_revision");
                yield new CombatId(method, revision(n, method == PublicMethod.QUERY_BATTLE_TRANSITION_V1), full(n.get("combat_id"))); }
            case QUERY_BATTLE_TERMINAL_TRANSITION_V1 -> { shape(n, "prior_combat_id subject_public_cunit_id expected_revision", "after_terminal_sequence character_ids");
                yield new Terminal(revision(n, true), field(n, "prior_combat_id", ArmyJson::full), field(n, "subject_public_cunit_id", ArmyJson::unit),
                        field(n, "after_terminal_sequence", v -> UInt64.positive(publicU64(v))), field(n, "character_ids", v -> array(v, ArmyJson::id))); }
            case PREVIEW_ACTIVE_COMBAT_RETREAT_V1 -> { shape(n, "selected_public_cunit_id target_province_id expected_revision", "");
                yield new RetreatPreview(revision(n, true), unit(n.get("selected_public_cunit_id")), id(n.get("target_province_id"))); }
            case ORDER_ACTIVE_COMBAT_RETREAT_V1 -> { shape(n, "selected_public_cunit_id expected_revision expected_combat_id expected_side_index expected_scope target_province_id candidate_token", "");
                yield new RetreatOrder(revision(n, true), unit(n.get("selected_public_cunit_id")), full(n.get("expected_combat_id")),
                        i32(n.get("expected_side_index")), choice(n.get("expected_scope"), Scope.class), id(n.get("target_province_id")), text(n.get("candidate_token"))); }
            case QUERY_COMBAT_SIMULATION_INPUTS, QUERY_COMBAT_SIMULATION_INPUTS_V3 -> { shape(n, "target_province_id attacker_entry_province_id attacker_army_ids defender_army_ids", "expected_revision constructor_adjacency_kind_raw");
                Field<Integer> ctor = field(n, "constructor_adjacency_kind_raw", ArmyJson::i32);
                yield new Combat(method, revision(n, false), CombatRequest.decode(n.get("target_province_id"), n.get("attacker_entry_province_id"),
                        n.get("attacker_army_ids"), n.get("defender_army_ids"), n.get("constructor_adjacency_kind_raw")), ctor); }
            case QUERY_WAR_ENTRY_ASSESSMENTS -> { shape(n, "target_character_ids", "expected_revision"); yield new WarEntry(revision(n, false), array(n.get("target_character_ids"), ArmyJson::id)); }
            case QUERY_CURRENT_BATTLE_KNIGHT_V1 -> {
                shape(n, "subject_public_cunit_id character_id regiment_id expected_played_character_id expected_war_id expected_native_carmy_id expected_combat_id expected_province_id expected_date_raw expected_revision expected_native_revision expected_snapshot_id", "");
                Revision r = revision(n, true); positiveRevision(r);
                long date = range(n.get("expected_date_raw"), BigInteger.ZERO, JS_SAFE).longValueExact();
                yield new Knight(r, new ArmyRequests.Knight(unit(n.get("subject_public_cunit_id")), id(n.get("character_id")), id(n.get("regiment_id")),
                        id(n.get("expected_played_character_id")), nonnegative(n.get("expected_war_id")), id(n.get("expected_native_carmy_id")),
                        id(n.get("expected_combat_id")), id(n.get("expected_province_id")), date, UInt64.positive(publicU64(n.get("expected_native_revision"))), text(n.get("expected_snapshot_id")))); }
            default -> throw new IllegalArgumentException("outside the exclusive 47-method Army partition");
        };
    }
    /** Persisted input round trips retain absent/null/explicit default separately. */
    public static RawJson encode(Call call) {
        ObjectNode n = empty(); put(n, "expected_revision", call.revision().value(), v -> string(v.toString()));
        switch (call) {
            case Empty ignored -> { }
            case Frame ignored -> { }
            case War c -> n.put("war_id", c.warId());
            case Unit c -> n.put(c.method() == PublicMethod.DISBAND_ARMY ? "army_id" : c.method() == PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1 ? "subject_public_cunit_id" : "selected_public_cunit_id", c.army().value());
            case Siege c -> n.put("siege_id", c.siege().value());
            case Declaration c -> n.put("declaration_id", c.declarationId());
            case Truce c -> n.put("toward_character_id", c.toward().value());
            case Collect c -> n.put("request_id", c.requestId());
            case CallAlly c -> n.put("war_id", c.war().value()).put("recipient_character_id", c.recipient().value());
            case CreateMaa c -> { n.put("type_index", c.typeIndex()).put("action_id", c.actionId()); put(n, "timeout_seconds", c.timeoutSeconds(), v -> com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.numberNode(v)); }
            case Move c -> n.put("army_id", c.army().value()).put("target_province_id", c.target().value());
            case Hire c -> n.put(c.method() == PublicMethod.HIRE_MERCENARY_V1 ? "company_id" : "holy_order_id", c.id().value());
            case Commander c -> { n.put("army_id", c.army().value()); put(n, "target_province_id", c.target(), v -> number(BigInteger.valueOf(v.value()))); }
            case AssignCommander c -> n.put("army_id", c.army().value()).put("commander_character_id", c.character().value());
            case Sampling c -> n.put("enabled", c.enabled());
            case Strengths c -> { ids(n, "army_ids", c.armies().stream().map(PublicUnitId::value).toList());
                put(n, "profile", c.profile(), v -> string(v.wire())); put(n, "ordered_refill_entry_mode", c.refillMode(), v -> string(v.wire())); put(n, "ordered_besieging_entry_mode", c.besiegingMode(), v -> string(v.wire())); }
            case Terminal c -> { put(n, "prior_combat_id", c.combat(), v -> number(BigInteger.valueOf(v.value()))); put(n, "subject_public_cunit_id", c.subject(), v -> number(BigInteger.valueOf(v.value())));
                put(n, "after_terminal_sequence", c.afterSequence(), v -> string(v.decimal())); put(n, "character_ids", c.characters(), v -> intArray(v.stream().map(PositiveId::value).toList())); }
            case RetreatPreview c -> n.put("selected_public_cunit_id", c.selected().value()).put("target_province_id", c.target().value());
            case RetreatOrder c -> n.put("selected_public_cunit_id", c.selected().value()).put("expected_combat_id", c.combat().value()).put("expected_side_index", c.sideIndex()).put("expected_scope", c.scope().name().toLowerCase(java.util.Locale.ROOT)).put("target_province_id", c.target().value()).put("candidate_token", c.token());
            case Combat c -> { CombatRequest q = c.selection(); n.put("target_province_id", q.targetProvinceId()); if (q.attackerEntryProvinceId() == null) n.putNull("attacker_entry_province_id"); else n.put("attacker_entry_province_id", q.attackerEntryProvinceId());
                ids(n, "attacker_army_ids", q.attackerArmyIds()); ids(n, "defender_army_ids", q.defenderArmyIds()); put(n, "constructor_adjacency_kind_raw", c.constructorKind(), v -> number(BigInteger.valueOf(v))); }
            case CombatId c -> n.put("combat_id", c.combat().value());
            case WarEntry c -> ids(n, "target_character_ids", c.targets().stream().map(PositiveId::value).toList());
            case Knight c -> { ArmyRequests.Knight q = c.selection(); n.put("subject_public_cunit_id", q.subject().value()).put("character_id", q.character().value()).put("regiment_id", q.regiment().value()).put("expected_played_character_id", q.player().value()).put("expected_war_id", q.war()).put("expected_native_carmy_id", q.nativeArmy().value()).put("expected_combat_id", q.combat().value()).put("expected_province_id", q.province().value()).put("expected_date_raw", q.dateRaw()).put("expected_native_revision", q.nativeRevision().decimal()).put("expected_snapshot_id", q.snapshotId()); }
        }
        return new RawJson(bytes(n));
    }
    private static Revision revision(ObjectNode n, boolean required) {
        Field<BigInteger> value = field(n, "expected_revision", ArmyCallCodec::publicU64);
        if (required) need(value instanceof Present<?>, "expected_revision is required and cannot be null");
        return new Revision(value);
    }
    private static void positiveRevision(Revision r) { need(r.value() instanceof Present<BigInteger> p && p.value().signum() > 0, "positive public revision required"); }
    private static BigInteger safe(JsonNode n) { return range(n, BigInteger.ZERO, JS_SAFE); }
    /** Canonical decimal text covers uint64; a numeric interface is restricted to exact JavaScript-safe integers. */
    private static BigInteger publicU64(JsonNode n) {
        if (!n.isTextual()) return safe(n); String value = text(n); need(value.matches("0|[1-9][0-9]*"), "canonical unsigned decimal public revision/sequence required"); return new UInt64(new BigInteger(value)).value();
    }
    private static BigDecimal decimal(JsonNode n) { need(n != null && n.isNumber(), "finite numeric timeout required; bool is not a number"); return n.decimalValue(); }
    private static <E extends Enum<E>> E choice(JsonNode n, Class<E> type) { String value = text(n); for (E e : type.getEnumConstants()) if (e.name().toLowerCase(java.util.Locale.ROOT).equals(value)) return e; throw new IllegalArgumentException("unknown typed enum token: " + value); }
    private static void shape(ObjectNode n, String required, String optional) {
        Set<String> r = words(required), allowed = new HashSet<>(r); allowed.addAll(words(optional));
        need(names(n).containsAll(r) && allowed.containsAll(names(n)), "wrong, missing or extra Army public arguments");
    }
    private static Set<String> words(String text) { return text.isEmpty() ? Set.of() : Set.of(text.split(" ")); }
    private static JsonNode number(BigInteger n) { return com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.numberNode(n); }
    private static JsonNode string(String s) { return com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.textNode(s); }
    private static JsonNode intArray(List<Integer> values) { var a = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode(); values.forEach(a::add); return a; }
    private static void ids(ObjectNode n, String key, List<Integer> values) { n.set(key, intArray(values)); }
    private static <T> void put(ObjectNode n, String key, Field<T> field, Function<T, JsonNode> encode) {
        if (field instanceof Present<T> p) n.set(key, encode.apply(p.value())); else if (field instanceof NullValue<?>) n.putNull(key);
    }
}
