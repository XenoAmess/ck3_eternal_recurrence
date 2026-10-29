package org.xar.ck3.control.application.planning;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Predicate;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;

/** Actual strategy.py history expansion/effective-command/index helpers. No result is promoted to success. */
public final class OrdinaryHistory {
    private final List<Obj> rows;
    private OrdinaryHistory(List<Obj> rows) { this.rows = List.copyOf(rows); }

    public static OrdinaryHistory collect(List<Obj> commands) {
        Objects.requireNonNull(commands); List<Obj> expanded = new ArrayList<>();
        for (Obj row : commands) {
            Objects.requireNonNull(row);
            String command = textOrNull(row.get("command"));
            boolean autoRun = "auto-run".equals(command)
                    || command != null && command.startsWith("auto-run ") && digitSuffix(command.substring(9));
            if (autoRun && row.get("result") instanceof Obj result && result.get("turns") instanceof Arr turns) {
                for (var turn : turns.items()) if (turn instanceof Obj object) append(expanded, object);
                continue;
            }
            append(expanded, row);
        }
        return new OrdinaryHistory(expanded);
    }

    private static void append(List<Obj> rows, Obj row) {
        // The original producer replaces outer/inner indices after expansion.
        rows.add(row.with("index", new IntegerValue(BigInteger.valueOf(rows.size() + 1L))));
    }

    private static boolean digitSuffix(String value) {
        if (value.isEmpty()) return false;
        return value.codePoints().allMatch(OrdinaryHistory::digit);
    }

    private static boolean digit(int value) {
        if (Character.isDigit(value)) return true;
        int number = Character.getNumericValue(value);
        if (number < 0 || number > 9 || Character.getType(value) != Character.OTHER_NUMBER) return false;
        String name = Character.getName(value);
        return name != null && (name.contains("DIGIT") || name.startsWith("SUPERSCRIPT ") || name.startsWith("SUBSCRIPT "));
    }

    public List<Obj> rows() { return rows; }
    public Optional<Obj> last() { return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getLast()); }

    public static Optional<String> effectiveCommand(Obj row) {
        String command = textOrNull(row.get("command"));
        if (!"auto-turn".equals(command)) return Optional.ofNullable(command);
        if (!(row.get("result") instanceof Obj result) || !(result.get("auto_turn") instanceof Obj autoTurn)) return Optional.empty();
        return Optional.ofNullable(textOrNull(autoTurn.get("selected_step")));
    }

    public int latest(String command) { return latest(command, true); }
    public int latest(String command, boolean successfulOnly) { return latestMatching(value -> value.equals(command), successfulOnly); }
    public int latestPrefix(String prefix) { return latestPrefix(prefix, true); }
    public int latestPrefix(String prefix, boolean successfulOnly) { return latestMatching(value -> value.startsWith(prefix), successfulOnly); }
    public int latestMatching(Predicate<String> predicate, boolean successfulOnly) {
        Objects.requireNonNull(predicate);
        for (int index = rows.size() - 1; index >= 0; index--) {
            Obj row = rows.get(index);
            if (successfulOnly && !successful(row)) continue;
            if (effectiveCommand(row).filter(predicate).isPresent()) return index + 1;
        }
        return 0;
    }

    public Optional<Obj> latestEffectiveResult(String command) {
        for (int index = rows.size() - 1; index >= 0; index--) {
            Obj row = rows.get(index);
            if (effectiveCommand(row).filter(command::equals).isEmpty() || !successful(row)) continue;
            if (row.get("result") instanceof Obj result) return Optional.of(result);
        }
        return Optional.empty();
    }

    /** Preserve the original root postcondition preference; a nested plan never overrides factual output. */
    public static Optional<Obj> effectiveCommandResult(Obj row) {
        if (!(row.get("result") instanceof Obj result)) return Optional.empty();
        if (!"auto-turn".equals(textOrNull(row.get("command")))) return Optional.of(result);
        for (String key : List.of("assault_action", "route_preview", "war_action", "war_progress_before", "war_progress_after"))
            if (result.get(key) instanceof Obj) return Optional.of(result);
        if (result.get("auto_turn") instanceof Obj auto && auto.get("result") instanceof Obj nested) return Optional.of(nested);
        return Optional.of(result);
    }

    public long countSuccessfulAfter(int afterIndex, Predicate<String> predicate) {
        StrictJson.require(afterIndex >= 0, "nonnegative history boundary required");
        long count = 0;
        for (int index = afterIndex; index < rows.size(); index++) {
            Obj row = rows.get(index);
            if (successful(row) && effectiveCommand(row).filter(predicate).isPresent()) count++;
        }
        return count;
    }
    public static boolean successful(Obj row) { return row.get("ok") instanceof Bool value && value.value(); }
    private static String textOrNull(OpportunityJson.Value value) { return value instanceof Text text ? text.value() : null; }
}
