package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure ordinary-selection boundary. It grants no quote, lease, family or dispatch authority. */
public final class ArmyOrdinaryPlannerSelection {
    private ArmyOrdinaryPlannerSelection() { }
    public record Selection(ArmyOrdinaryActionArguments.Kind kind, RawJson publicArguments,
            Optional<ArmyOrdinaryActionArguments.TerminalSelection> terminalSelection) {
        public Selection(ArmyOrdinaryActionArguments.Kind kind, RawJson publicArguments) { this(kind, publicArguments, Optional.empty()); }
        public Selection {
            Objects.requireNonNull(kind); Objects.requireNonNull(publicArguments); Objects.requireNonNull(terminalSelection);
            terminalSelection.ifPresent(selected -> selected.requirePublic(kind, publicArguments));
        }
    }
    private static final String ID = "(0|[1-9][0-9]*)";
    private static final Pattern MOVE = Pattern.compile("move-army-" + ID + "-to-" + ID);
    private static final Pattern ONE = Pattern.compile("(disband-army|start-assault|stop-assault|enforce-demands|surrender-war|offer-white-peace)-" + ID);
    private static final Pattern DECLARE = Pattern.compile("declare-war-((?:0|[1-9][0-9]*)-(?:0|[1-9][0-9]*)-(?:-1|0|[1-9][0-9]*))");
    private static final Set<String> FRAMES = Set.of("raise-troops-default", "close-war-declared-overview-v1", "close-war-results-window-v1");
    private static final Set<String> TERMINAL_FIELDS = Set.of("war_id", "requested_outcome", "postcondition_plan");

    /** Strict canonical route and ID membership. Actual selected arguments still require decode. */
    public static boolean supports(OperationKey operation) {
        String step = Objects.requireNonNull(operation).value();
        if (!(FRAMES.contains(step) || MOVE.matcher(step).matches() || ONE.matcher(step).matches() || DECLARE.matcher(step).matches())) return false;
        try { decode(operation, new Obj(java.util.Map.of()), BigInteger.ONE); return true; }
        catch (IllegalArgumentException invalidId) { return false; }
    }

    /** Decode the actual planner's empty selection args or LegacyWarExitPolicy's exact terminal args.
     * The caller retains the original Select/detail and action ID and must pass this Call through
     * the actual Army producer under the original writer. Public call validation remains with
     * the installed native adapter; this method cannot turn a planner detail into Native data.
     */
    public static Selection decode(OperationKey operation, Obj selectedArguments, BigInteger actualRevision) {
        Objects.requireNonNull(operation); Objects.requireNonNull(selectedArguments);
        StrictJson.require(actualRevision != null && actualRevision.signum() > 0 && actualRevision.bitLength() <= 64,
                "ordinary Army selection requires its actual positive uint64 public revision");
        String step = operation.value(); ObjectNode args = StrictJson.object().put("expected_revision", actualRevision.toString());
        ArmyOrdinaryActionArguments.Kind method;
        Optional<ArmyOrdinaryActionArguments.TerminalSelection> terminalSelection = Optional.empty();
        Matcher move = MOVE.matcher(step), one = ONE.matcher(step), declaration = DECLARE.matcher(step);
        if (FRAMES.contains(step)) {
            empty(selectedArguments);
            method = switch (step) {
                case "raise-troops-default" -> ArmyOrdinaryActionArguments.Kind.RAISE_TROOPS_DEFAULT;
                case "close-war-declared-overview-v1" -> ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1;
                case "close-war-results-window-v1" -> ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_RESULTS_WINDOW_V1;
                default -> throw new IllegalStateException("closed frame inventory changed");
            };
        } else if (move.matches()) {
            empty(selectedArguments); method = ArmyOrdinaryActionArguments.Kind.MOVE_ARMY;
            bounded(integer(move.group(1)), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE));
            bounded(integer(move.group(2)), BigInteger.ONE, BigInteger.valueOf(Integer.MAX_VALUE));
            args.put("army_id", integer(move.group(1))).put("target_province_id", integer(move.group(2)));
        } else if (declaration.matches()) {
            empty(selectedArguments); method = ArmyOrdinaryActionArguments.Kind.DECLARE_WAR; args.put("declaration_id", declaration.group(1));
        } else if (one.matches()) {
            BigInteger id = integer(one.group(2));
            method = switch (one.group(1)) {
                case "disband-army" -> ArmyOrdinaryActionArguments.Kind.DISBAND_ARMY;
                case "start-assault" -> ArmyOrdinaryActionArguments.Kind.START_ASSAULT;
                case "stop-assault" -> ArmyOrdinaryActionArguments.Kind.STOP_ASSAULT;
                case "enforce-demands" -> ArmyOrdinaryActionArguments.Kind.ENFORCE_DEMANDS;
                case "surrender-war" -> ArmyOrdinaryActionArguments.Kind.SURRENDER_WAR;
                case "offer-white-peace" -> ArmyOrdinaryActionArguments.Kind.OFFER_WHITE_PEACE;
                default -> throw new IllegalStateException("closed single-ID inventory changed");
            };
            String key = switch (method) {
                case DISBAND_ARMY -> "army_id"; case START_ASSAULT, STOP_ASSAULT -> "siege_id"; default -> "war_id";
            };
            BigInteger minimum = method == ArmyOrdinaryActionArguments.Kind.DISBAND_ARMY || method == ArmyOrdinaryActionArguments.Kind.ENFORCE_DEMANDS ? BigInteger.ZERO : BigInteger.ONE;
            BigInteger maximum = method == ArmyOrdinaryActionArguments.Kind.ENFORCE_DEMANDS ? new BigInteger("9007199254740991") : BigInteger.valueOf(Integer.MAX_VALUE);
            bounded(id, minimum, maximum);
            if (key.equals("war_id")) {
                terminal(selectedArguments, id, method);
                if (!selectedArguments.members().isEmpty())
                    terminalSelection = Optional.of(ArmyOrdinaryActionArguments.TerminalSelection.decode(selectedArguments));
            }
            else if (method == ArmyOrdinaryActionArguments.Kind.DISBAND_ARMY) disband(selectedArguments, id);
            else empty(selectedArguments);
            args.put(key, id);
        } else throw new IllegalArgumentException("ordinary Army planner selection has no canonical installed route: " + step);
        return new Selection(method, new RawJson(StrictJson.canonical(args)), terminalSelection);
    }

    /** Custody only: preserve the unique planner-to-public projection inside the actual prepared envelope. */
    public static void requirePrepared(OperationKey operation, Obj selectedArguments, BigInteger revision, ArmyOrdinaryActionArguments actual) {
        Selection selected = decode(operation, selectedArguments, revision); Objects.requireNonNull(actual);
        StrictJson.require(actual.kind() == selected.kind()
                && DriverJson.object(actual.publicArguments().bytes(), 65536).equals(DriverJson.object(selected.publicArguments().bytes(), 65536))
                && actual.terminalSelection().equals(selected.terminalSelection()),
                "Army preparation changed the original planner selection or its actual revision");
    }

    private static void terminal(Obj selected, BigInteger id, ArmyOrdinaryActionArguments.Kind method) {
        if (selected.members().isEmpty()) return;
        StrictJson.require(selected.members().keySet().equals(TERMINAL_FIELDS), "ordinary terminal selection has wrong, missing or extra arguments");
        StrictJson.require(selected.get("war_id") instanceof IntegerValue integer && integer.value().equals(id),
                "ordinary terminal arguments changed the complete step WarID or integer JSON domain");
        String outcome = switch (method) {
            case ENFORCE_DEMANDS -> "player_victory"; case SURRENDER_WAR -> "surrender"; case OFFER_WHITE_PEACE -> "white_peace";
            default -> throw new IllegalArgumentException("unrelated terminal Army method");
        };
        StrictJson.require(new Text(outcome).equals(selected.get("requested_outcome")), "ordinary terminal arguments changed their selected outcome");
        Value plan = selected.get("postcondition_plan");
        StrictJson.require(plan == Nil.INSTANCE || plan instanceof Obj, "ordinary terminal plan must retain its explicit object/null JSON domain");
    }
    private static void empty(Obj selected) {
        StrictJson.require(selected.members().isEmpty(), "this ordinary Army step requires the planner's exact empty arguments");
    }
    /** OrdinaryCorePolicy.select's postwar producer carries this exact integer payload; other military leaves carry empty args. */
    private static void disband(Obj selected, BigInteger stepArmy) {
        if (selected.members().isEmpty()) return;
        StrictJson.require(selected.members().keySet().equals(Set.of("army_id"))
                && selected.get("army_id") instanceof IntegerValue army && army.value().equals(stepArmy),
                "ordinary postwar disband payload changed its exact step ArmyID or integer JSON domain");
    }
    private static BigInteger integer(String exact) { return new BigInteger(exact); }
    private static void bounded(BigInteger value, BigInteger minimum, BigInteger maximum) {
        StrictJson.require(value.compareTo(minimum) >= 0 && value.compareTo(maximum) <= 0, "ordinary planner ID is outside its exact public input domain");
    }
}
