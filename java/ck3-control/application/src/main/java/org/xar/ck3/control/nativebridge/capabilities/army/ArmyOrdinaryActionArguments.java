package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy.Variant;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Durable custody of one public selection and the actual archived preflight receipts.
 * This application-layer contract has no Native submission or public route authority.
 */
public record ArmyOrdinaryActionArguments(Kind kind, RawJson publicArguments, List<ExactRef> preflightReads, ExecutionProfile executionProfile, Optional<Variant> automaticSurrender, Optional<TerminalSelection> terminalSelection) {
    public static final String SCHEMA = "xar.ck3.army-ordinary-action-arguments/v1";
    public static final String PROFILE_SCHEMA = "xar.ck3.army-ordinary-action-arguments/v2";
    public static final String TERMINAL_SCHEMA = "xar.ck3.army-ordinary-action-arguments/v3";
    public ArmyOrdinaryActionArguments(Kind kind, RawJson publicArguments, List<ExactRef> preflightReads,
            ExecutionProfile executionProfile, Optional<Variant> automaticSurrender) {
        this(kind, publicArguments, preflightReads, executionProfile, automaticSurrender, Optional.empty());
    }
    public enum TerminalOutcome {
        PLAYER_VICTORY("player_victory", Kind.ENFORCE_DEMANDS), SURRENDER("surrender", Kind.SURRENDER_WAR),
        WHITE_PEACE("white_peace", Kind.OFFER_WHITE_PEACE);
        private final String wire; private final Kind kind;
        TerminalOutcome(String wire, Kind kind) { this.wire = wire; this.kind = kind; }
        public String wire() { return wire; }
        public Kind kind() { return kind; }
        public static TerminalOutcome exact(String value) {
            for (TerminalOutcome route : values()) if (route.wire.equals(value)) return route;
            throw new IllegalArgumentException("unknown terminal selection outcome");
        }
    }
    /** Original planner DATA only. The optional plan is an explicit null inside a present selection. */
    public record TerminalSelection(java.math.BigInteger warId, TerminalOutcome outcome, Optional<RawJson> postconditionPlan) {
        public TerminalSelection {
            Objects.requireNonNull(warId); Objects.requireNonNull(outcome); Objects.requireNonNull(postconditionPlan);
            StrictJson.require(warId.signum() >= 0 && warId.compareTo(new java.math.BigInteger("9007199254740991")) <= 0
                    && (outcome == TerminalOutcome.PLAYER_VICTORY || warId.signum() > 0), "terminal selection WarID is outside its original route domain");
            postconditionPlan = postconditionPlan.map(raw -> {
                var plan = StrictJson.object(StrictJson.parse(raw.bytes(), 65536),
                        Set.of("schema_version", "route", "requirements", "expectations", "verified", "gen034_completion_eligible"));
                StrictJson.require(outcome != TerminalOutcome.PLAYER_VICTORY
                        && StrictJson.integer(plan.get("schema_version"), 1, 1) == 1
                        && StrictJson.text(plan.get("route")).equals(outcome.wire())
                        && plan.get("verified").isBoolean() && !plan.get("verified").booleanValue()
                        && plan.get("gen034_completion_eligible").isBoolean() && plan.get("gen034_completion_eligible").booleanValue(),
                        "frozen terminal plan changed its route, version or unverified state");
                StrictJson.require(plan.get("requirements").isArray(), "frozen terminal requirements must be an explicit array");
                List<String> requirements = new ArrayList<>();
                plan.get("requirements").forEach(value -> requirements.add(StrictJson.text(value)));
                StrictJson.require(requirements.equals(org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.TERMINATE),
                        "frozen terminal requirements changed");
                var expected = plan.get("expectations");
                StrictJson.require(expected != null && expected.isObject()
                        && StrictJson.integer(expected.get("war_id"), java.math.BigInteger.ONE, StrictJson.UINT64_MAX).equals(warId),
                        "frozen terminal plan changed its complete WarID");
                return new RawJson(StrictJson.canonical(plan, 65536));
            });
        }
        public OpportunityJson.Obj encode() {
            return new OpportunityJson.Obj(java.util.Map.of("war_id", new OpportunityJson.IntegerValue(warId),
                    "requested_outcome", new OpportunityJson.Text(outcome.wire()), "postcondition_plan",
                    postconditionPlan.<OpportunityJson.Value>map(raw -> DriverJson.object(raw.bytes(), 65536)).orElse(OpportunityJson.Nil.INSTANCE)));
        }
        public static TerminalSelection decode(OpportunityJson.Obj value) {
            var n = StrictJson.object(OpportunityJson.toNode(value), Set.of("war_id", "requested_outcome", "postcondition_plan"));
            var plan = n.get("postcondition_plan");
            StrictJson.require(plan.isNull() || plan.isObject(), "terminal plan must retain explicit object/null JSON domain");
            return new TerminalSelection(StrictJson.integer(n.get("war_id"), java.math.BigInteger.ZERO, StrictJson.UINT64_MAX),
                    TerminalOutcome.exact(StrictJson.text(n.get("requested_outcome"))),
                    plan.isNull() ? Optional.empty() : Optional.of(new RawJson(StrictJson.canonical(plan, 65536))));
        }
        public void requirePublic(Kind kind, RawJson publicArguments) {
            var publicValue = DriverJson.toNode(DriverJson.object(publicArguments.bytes(), 65536));
            StrictJson.require(outcome.kind() == kind
                    && StrictJson.integer(publicValue.get("war_id"), java.math.BigInteger.ZERO, StrictJson.UINT64_MAX).equals(warId),
                    "terminal origin differs from the actual public kind/full WarID");
        }
    }
    public ArmyOrdinaryActionArguments withTerminalSelection(Optional<TerminalSelection> selected) {
        return new ArmyOrdinaryActionArguments(kind, publicArguments, preflightReads, executionProfile, automaticSurrender, selected);
    }
    public ArmyOrdinaryActionArguments(Kind kind, RawJson publicArguments, List<ExactRef> preflightReads) {
        this(kind, publicArguments, preflightReads, ExecutionProfile.SDK_ORDINARY, Optional.empty());
    }
    public enum ExecutionProfile {
        SDK_ORDINARY("sdk_ordinary"), GENERIC_AUTOMATIC_SURRENDER("generic_automatic_surrender"), DIRECT_FIXED_WINDOW("direct_fixed_window");
        private final String wire; ExecutionProfile(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static ExecutionProfile exact(String value) {
            for (ExecutionProfile profile : values()) if (profile.wire.equals(value)) return profile;
            throw new IllegalArgumentException("unknown Army execution profile");
        }
    }
    public enum Kind {
        SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1, SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1,
        CLOSE_WAR_DECLARED_OVERVIEW_V1, CLOSE_WAR_RESULTS_WINDOW_V1,
        DECLARE_WAR, RAISE_TROOPS_DEFAULT, MOVE_ARMY, START_ASSAULT, STOP_ASSAULT,
        DISBAND_ARMY, ENFORCE_DEMANDS, SURRENDER_WAR, OFFER_WHITE_PEACE,
        HIRE_MERCENARY_V1, HIRE_HOLY_ORDER_V1, ASSIGN_ARMY_COMMANDER_V1,
        SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
        public static Kind exact(String value) {
            for (Kind kind : values()) if (kind.wire().equals(value)) return kind;
            throw new IllegalArgumentException("unknown Army ordinary action kind");
        }
    }
    public ArmyOrdinaryActionArguments {
        Objects.requireNonNull(kind); Objects.requireNonNull(publicArguments); Objects.requireNonNull(automaticSurrender); Objects.requireNonNull(executionProfile); Objects.requireNonNull(terminalSelection);
        StrictJson.require((executionProfile == ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER) == automaticSurrender.isPresent(),
                "automatic surrender profile requires its exact variant and other profiles forbid it");
        StrictJson.require(automaticSurrender.isEmpty() || kind == Kind.SURRENDER_WAR, "automatic surrender variant is invalid for another Army kind");
        if (executionProfile == ExecutionProfile.DIRECT_FIXED_WINDOW)
            StrictJson.require((kind == Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1 || kind == Kind.CLOSE_WAR_RESULTS_WINDOW_V1) && preflightReads.isEmpty(),
                    "direct fixed-window profile belongs only to the two original no-query close commands");
        publicArguments = new RawJson(DriverJson.encode(DriverJson.object(publicArguments.bytes(), 65536)));
        if (terminalSelection.isPresent()) terminalSelection.orElseThrow().requirePublic(kind, publicArguments);
        preflightReads = List.copyOf(preflightReads);
        StrictJson.require(executionProfile != ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER || preflightReads.size() == 1,
                "automatic surrender must retain its one original options receipt");
        StrictJson.require(preflightReads.size() <= 16 && preflightReads.stream().distinct().count() == preflightReads.size(),
                "bounded distinct original preflight receipt references required");
        for (ExactRef ref : preflightReads) StrictJson.require(ref.bytes() > 0, "empty preflight receipt is not evidence");
    }
    public OpportunityJson.Obj encode() {
        var refs = preflightReads.stream().<OpportunityJson.Value>map(ref ->
                DriverJson.object(StrictJson.canonical(ref.toJson()), 65536)).toList();
        java.util.Map<String,OpportunityJson.Value> fields = new java.util.LinkedHashMap<>();
        fields.put("schema", new OpportunityJson.Text(terminalSelection.isPresent() ? TERMINAL_SCHEMA : executionProfile == ExecutionProfile.SDK_ORDINARY ? SCHEMA : PROFILE_SCHEMA)); fields.put("kind", new OpportunityJson.Text(kind.wire()));
        fields.put("public_arguments", DriverJson.object(publicArguments.bytes(), 65536)); fields.put("preflight_reads", new OpportunityJson.Arr(refs));
        if (terminalSelection.isPresent() || executionProfile != ExecutionProfile.SDK_ORDINARY) {
            fields.put("execution_profile", new OpportunityJson.Text(executionProfile.wire()));
            fields.put("generic_automatic_surrender_variant", automaticSurrender.<OpportunityJson.Value>map(variant -> new OpportunityJson.Text(variant.wire())).orElse(OpportunityJson.Nil.INSTANCE));
        }
        terminalSelection.ifPresent(selected -> fields.put("terminal_selection", selected.encode()));
        var value = new OpportunityJson.Obj(fields);
        return DriverJson.object(DriverJson.encode(value), ActionCommand.MAX_ARGUMENT_BYTES);
    }
    public RawJson raw() { return new RawJson(DriverJson.encode(encode())); }
    public static ArmyOrdinaryActionArguments decode(OpportunityJson.Obj arguments) {
        String schema = OpportunityJson.text(arguments.get("schema"), "Army durable schema");
        boolean terminal = schema.equals(TERMINAL_SCHEMA), automatic = schema.equals(PROFILE_SCHEMA) || terminal;
        StrictJson.require(automatic || schema.equals(SCHEMA), "wrong Army ordinary action schema");
        var fields = terminal ? Set.of("schema", "kind", "public_arguments", "preflight_reads", "execution_profile", "generic_automatic_surrender_variant", "terminal_selection")
                : automatic ? Set.of("schema", "kind", "public_arguments", "preflight_reads", "execution_profile", "generic_automatic_surrender_variant")
                : Set.of("schema", "kind", "public_arguments", "preflight_reads");
        var n = StrictJson.object(OpportunityJson.toNode(arguments), fields);
        ExecutionProfile profile = automatic ? ExecutionProfile.exact(StrictJson.text(n.get("execution_profile"))) : ExecutionProfile.SDK_ORDINARY;
        StrictJson.require(terminal || !automatic || profile != ExecutionProfile.SDK_ORDINARY, "SDK ordinary must retain its original v1 schema");
        Optional<TerminalSelection> selected = terminal
                ? Optional.of(TerminalSelection.decode(OpportunityJson.object(arguments.get("terminal_selection"), "original terminal selection"))) : Optional.empty();
        Optional<Variant> variant = automatic && !n.get("generic_automatic_surrender_variant").isNull()
                ? Optional.of(Variant.exact(StrictJson.text(n.get("generic_automatic_surrender_variant")))) : Optional.empty();
        StrictJson.require(n.get("public_arguments").isObject(), "public arguments must retain their original object domain");
        var refs = n.get("preflight_reads"); StrictJson.require(refs.isArray(), "preflight_reads must be an explicit array");
        List<ExactRef> originals = new ArrayList<>(); refs.forEach(value -> originals.add(ExactRef.fromJson(value)));
        return new ArmyOrdinaryActionArguments(Kind.exact(StrictJson.text(n.get("kind"))),
                new RawJson(DriverJson.encode(OpportunityJson.object(arguments.get("public_arguments"), "original public arguments"))), originals, profile, variant, selected);
    }
    public static ArmyOrdinaryActionArguments decode(RawJson arguments) {
        return decode(DriverJson.object(arguments.bytes(), ActionCommand.MAX_ARGUMENT_BYTES));
    }
}
