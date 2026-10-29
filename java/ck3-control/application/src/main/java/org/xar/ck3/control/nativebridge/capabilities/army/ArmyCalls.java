package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod.*;

/** Public Service selections. These values carry no Native dispatch or source qualification authority. */
public final class ArmyCalls {
    private ArmyCalls() { }
    public static final BigInteger JS_SAFE = new BigInteger("9007199254740991");
    public record Revision(Field<BigInteger> value) {
        public Revision { Objects.requireNonNull(value); if (value instanceof Present<BigInteger> p) new UInt64(p.value()); }
        public BigInteger requireCurrent(BigInteger actual) {
            if (value instanceof Present<BigInteger> p) need(p.value().equals(actual), "public revision differs from the observed frame");
            return Objects.requireNonNull(actual);
        }
    }
    public sealed interface Call permits Empty, Frame, War, Unit, Siege, Declaration, Truce, Collect,
            CallAlly, CreateMaa, Move, Hire, Commander, AssignCommander, Sampling, Strengths, Terminal,
            RetreatPreview, RetreatOrder, Combat, CombatId, WarEntry, Knight {
        PublicMethod method();
        Revision revision();
    }
    public record Empty() implements Call {
        public PublicMethod method() { return WAR_STATE; }
        public Revision revision() { return new Revision(new Missing<>()); }
    }
    public record Frame(PublicMethod method, Revision revision) implements Call {
        public Frame { allow(method, QUERY_WAR_DECLARED_OVERVIEW_V1, CLOSE_WAR_DECLARED_OVERVIEW_V1,
                QUERY_WAR_RESULTS_WINDOW_V1, CLOSE_WAR_RESULTS_WINDOW_V1, QUERY_DECLARABLE_WARS,
                RAISE_TROOPS_DEFAULT, QUERY_PLAYER_DEFAULT_RAISE_V1, QUERY_PLAYER_MERCENARY_CONTEXT_V1,
                QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1); Objects.requireNonNull(revision); }
    }
    public record War(PublicMethod method, Revision revision, BigInteger warId) implements Call {
        public War { allow(method, ENFORCE_DEMANDS, QUERY_WAR_OCCUPATION_TARGETS_V1, QUERY_WAR_TERMINATION_OPTIONS,
                QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS, QUERY_WAR_TERMINATION_TERMS,
                QUERY_WAR_TERMINATION_EXIT_TERMS, SURRENDER_WAR, OFFER_WHITE_PEACE);
            Objects.requireNonNull(revision); range(warId, method == ENFORCE_DEMANDS || method == QUERY_WAR_OCCUPATION_TARGETS_V1 ? BigInteger.ZERO : BigInteger.ONE,
                    method == ENFORCE_DEMANDS ? JS_SAFE : BigInteger.valueOf(Integer.MAX_VALUE)); }
    }
    public record Unit(PublicMethod method, Revision revision, PublicUnitId army) implements Call {
        public Unit { allow(method, DISBAND_ARMY, QUERY_BATTLE_CONTROL_SNAPSHOT_V1, QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1);
            Objects.requireNonNull(revision); Objects.requireNonNull(army); }
    }
    public record Siege(PublicMethod method, Revision revision, PositiveId siege) implements Call {
        public Siege { allow(method, START_ASSAULT, STOP_ASSAULT); Objects.requireNonNull(revision); Objects.requireNonNull(siege); }
    }
    public record Declaration(PublicMethod method, Revision revision, String declarationId) implements Call {
        public Declaration { allow(method, DECLARE_WAR, QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1,
                QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2);
            Objects.requireNonNull(revision); need(declarationId != null && declarationId.matches("[0-9]+-[0-9]+-(?:-1|[0-9]+)"), "original declaration tuple required"); }
    }
    public record Truce(Revision revision, PositiveId toward) implements Call {
        public Truce { Objects.requireNonNull(revision); Objects.requireNonNull(toward); }
        public PublicMethod method() { return QUERY_PLAYER_TRUCE_EXPIRY_V1; }
    }
    public record Collect(Revision revision, String requestId) implements Call {
        public Collect { Objects.requireNonNull(revision); text(requestId); }
        public PublicMethod method() { return COLLECT_DECLARABLE_WARS_RESULT_V1; }
    }
    public record CallAlly(Revision revision, FullId war, FullId recipient) implements Call {
        public CallAlly { Objects.requireNonNull(revision); Objects.requireNonNull(war); Objects.requireNonNull(recipient); }
        public PublicMethod method() { return SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1; }
    }
    public record CreateMaa(Revision revision, int typeIndex, String actionId, Field<BigDecimal> timeoutSeconds) implements Call {
        public CreateMaa { Objects.requireNonNull(revision); need(typeIndex >= 0, "observed MAA registry index required");
            need(actionId != null && !actionId.isEmpty() && actionId.getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 63, "MAA action ID needs 1..63 UTF-8 bytes");
            Objects.requireNonNull(timeoutSeconds); need(!(timeoutSeconds instanceof NullValue<?>), "timeout cannot be null");
            if (timeoutSeconds instanceof Present<BigDecimal> p) need(p.value().signum() > 0, "positive timeout required"); }
        public PublicMethod method() { return SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1; }
    }
    public record Move(Revision revision, PublicUnitId army, PositiveId target) implements Call {
        public Move { Objects.requireNonNull(revision); Objects.requireNonNull(army); Objects.requireNonNull(target); }
        public PublicMethod method() { return MOVE_ARMY; }
    }
    public record Hire(PublicMethod method, Revision revision, HireId id) implements Call {
        public Hire { allow(method, HIRE_MERCENARY_V1, HIRE_HOLY_ORDER_V1); Objects.requireNonNull(revision); Objects.requireNonNull(id); }
    }
    public record Commander(Revision revision, PublicUnitId army, Field<PositiveId> target) implements Call {
        public Commander { Objects.requireNonNull(revision); Objects.requireNonNull(army); Objects.requireNonNull(target); }
        public PublicMethod method() { return QUERY_ARMY_COMMANDER_CANDIDATES_V1; }
    }
    public record AssignCommander(Revision revision, PublicUnitId army, PublicUnitId character) implements Call {
        public AssignCommander { Objects.requireNonNull(revision); Objects.requireNonNull(army); Objects.requireNonNull(character); }
        public PublicMethod method() { return ASSIGN_ARMY_COMMANDER_V1; }
    }
    public record Sampling(Revision revision, boolean enabled) implements Call {
        public Sampling { Objects.requireNonNull(revision); }
        public PublicMethod method() { return SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1; }
    }
    public enum StrengthProfile { ORDINARY_CORE_V1, OBSERVED_HISTORY_FULL_V1;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public enum EntryMode { OBSERVED_PREPARED, FIXED_CHUNK0_PREPARE;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public record Strengths(Revision revision, List<PublicUnitId> armies, Field<StrengthProfile> profile,
            Field<EntryMode> refillMode, Field<EntryMode> besiegingMode) implements Call {
        public Strengths { Objects.requireNonNull(revision); armies = distinct(armies, 1, 64, "explicit Army subset");
            Objects.requireNonNull(profile); Objects.requireNonNull(refillMode); Objects.requireNonNull(besiegingMode);
            need(!(profile instanceof NullValue<?>) && !(refillMode instanceof NullValue<?>) && !(besiegingMode instanceof NullValue<?>), "explicit profile/modes cannot be null"); }
        public PublicMethod method() { return QUERY_ARMY_STRENGTHS; }
        public StrengthProfile effectiveProfile() { return profile instanceof Present<StrengthProfile> p ? p.value() : StrengthProfile.ORDINARY_CORE_V1; }
        public EntryMode effectiveRefill() { return refillMode instanceof Present<EntryMode> p ? p.value() : EntryMode.OBSERVED_PREPARED; }
        public EntryMode effectiveBesieging() { return besiegingMode instanceof Present<EntryMode> p ? p.value() : EntryMode.OBSERVED_PREPARED; }
    }
    public record Terminal(Revision revision, Field<FullId> combat, Field<PublicUnitId> subject,
            Field<UInt64> afterSequence, Field<List<PositiveId>> characters) implements Call {
        public Terminal { Objects.requireNonNull(revision); Objects.requireNonNull(combat); Objects.requireNonNull(subject); Objects.requireNonNull(afterSequence); Objects.requireNonNull(characters);
            need(!(combat instanceof Missing<?>) && !(subject instanceof Missing<?>), "prior combat and subject are required, nullable arguments");
            need((combat instanceof Present<?>) == (subject instanceof Present<?>), "terminal battle context must be paired");
            if (afterSequence instanceof Present<UInt64> p) need(p.value().value().signum() > 0, "terminal cursor must be positive");
            if (characters instanceof Present<List<PositiveId>> p) characters = new Present<>(List.copyOf(p.value()));
            if (!(combat instanceof Present<?>)) need(characters instanceof Present<List<PositiveId>> p && !p.value().isEmpty()
                    && !(afterSequence instanceof Present<?>), "character-only terminal needs characters and no cursor"); }
        public PublicMethod method() { return QUERY_BATTLE_TERMINAL_TRANSITION_V1; }
        public List<PositiveId> effectiveCharacters() { return characters instanceof Present<List<PositiveId>> p ? p.value().stream().distinct().toList() : List.of(); }
    }
    public record RetreatPreview(Revision revision, PublicUnitId selected, PositiveId target) implements Call {
        public RetreatPreview { Objects.requireNonNull(revision); Objects.requireNonNull(selected); Objects.requireNonNull(target); }
        public PublicMethod method() { return PREVIEW_ACTIVE_COMBAT_RETREAT_V1; }
    }
    public record RetreatOrder(Revision revision, PublicUnitId selected, FullId combat, int sideIndex, Scope scope,
            PositiveId target, String token) implements Call {
        public RetreatOrder { Objects.requireNonNull(revision); Objects.requireNonNull(selected); Objects.requireNonNull(combat); Objects.requireNonNull(scope); Objects.requireNonNull(target);
            need(sideIndex == 0 || sideIndex == 1, "native side index must be 0 or 1"); need(token != null && token.matches("[A-Za-z0-9_-]{32,128}"), "original candidate token required"); }
        public PublicMethod method() { return ORDER_ACTIVE_COMBAT_RETREAT_V1; }
    }
    public record Combat(PublicMethod method, Revision revision, CombatRequest selection, Field<Integer> constructorKind) implements Call {
        public Combat { allow(method, QUERY_COMBAT_SIMULATION_INPUTS, QUERY_COMBAT_SIMULATION_INPUTS_V3); Objects.requireNonNull(revision); Objects.requireNonNull(selection); Objects.requireNonNull(constructorKind);
            need(Objects.equals(constructorKind instanceof Present<Integer> p ? p.value() : null, selection.constructorAdjacencyKindRaw()), "constructor presence differs from the shared combat request"); }
    }
    public record CombatId(PublicMethod method, Revision revision, FullId combat) implements Call {
        public CombatId { allow(method, QUERY_BATTLE_TRANSITION_V1, QUERY_COMBAT_PHASE_EVENT_TRACE_V1); Objects.requireNonNull(revision); Objects.requireNonNull(combat);
            need(method != QUERY_COMBAT_PHASE_EVENT_TRACE_V1 || combat.value() > 0, "phase-event evaluator requires a positive CombatID"); }
    }
    public record WarEntry(Revision revision, List<PositiveId> targets) implements Call {
        public WarEntry { Objects.requireNonNull(revision); targets = distinct(targets, 1, 1, "production war-entry targets"); }
        public PublicMethod method() { return QUERY_WAR_ENTRY_ASSESSMENTS; }
    }
    public record Knight(Revision revision, ArmyRequests.Knight selection) implements Call {
        public Knight { Objects.requireNonNull(revision); Objects.requireNonNull(selection); need(revision.value() instanceof Present<?>, "current knight needs explicit public revision"); }
        public PublicMethod method() { return QUERY_CURRENT_BATTLE_KNIGHT_V1; }
    }
    public static void need(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
    static void range(BigInteger value, BigInteger min, BigInteger max) { need(value != null && value.compareTo(min) >= 0 && value.compareTo(max) <= 0, "integer outside exact request domain"); }
    static void text(String value) { need(value != null && !value.isEmpty(), "nonempty original identity required"); }
    static void allow(PublicMethod actual, PublicMethod... allowed) { need(actual != null && java.util.Arrays.asList(allowed).contains(actual), "request shape does not belong to this Army method"); }
}
