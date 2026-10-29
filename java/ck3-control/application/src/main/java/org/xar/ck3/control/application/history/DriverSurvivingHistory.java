package org.xar.ck3.control.application.history;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceStep;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** The complete surviving Driver branch. This reader never appends, submits, retries, or opens a file. */
public final class DriverSurvivingHistory {
    public static final String RESTORE = "restore-checkpoint";
    private static final Set<String> OUTER_RESULT_FIELDS = Set.of("route_preview", "war_action", "assault_action",
            "war_progress_before", "war_progress_after", "player_armies");
    private DriverSurvivingHistory() { }

    public record Effective(Optional<String> command, Optional<Obj> result) {
        public Effective { Objects.requireNonNull(command); Objects.requireNonNull(result); }
    }
    public record Row(long index, String command, boolean ok, Obj original, Effective effective) {
        public Row {
            StrictJson.safe(index, 1); StrictJson.text(command); Objects.requireNonNull(original); Objects.requireNonNull(effective);
            StrictJson.require(OpportunityJson.integer(original.get("index"), "index").longValueExact() == index
                    && OpportunityJson.text(original.get("command"), "command").equals(command)
                    && OpportunityJson.bool(original.get("ok"), "ok") == ok, "actual original history row differs");
            StrictJson.require(effective.equals(DriverSurvivingHistory.effective(original)), "effective history view differs from its original row");
        }
    }

    /** Every original field survives, including missing/null results, failed reads, errors and physical restore rows. */
    public static List<Obj> rows(DriverStateSnapshot.Complete driver) {
        return entries(driver).stream().map(Row::original).toList();
    }
    public static List<Row> entries(DriverStateSnapshot.Complete driver) {
        Objects.requireNonNull(driver); List<Row> rows = new ArrayList<>();
        for (DriverStateSnapshot.HistoryEntry entry : driver.commandHistory()) {
            Obj original = DriverJson.object(entry.originalRow().json(), DriverJson.MAX_NATIVE_BYTES);
            rows.add(row(original));
        }
        return completeBranch(rows);
    }
    /** Complete branch validation is separate from a fresh query slice whose first original index may exceed one. */
    public static List<Row> completeBranch(List<Row> branch) {
        List<Row> rows = orderedSlice(branch);
        if (!rows.isEmpty()) StrictJson.require(rows.getFirst().index() == 1, "complete surviving history must begin at one");
        return rows;
    }
    public static List<Row> orderedSlice(List<Row> slice) {
        List<Row> rows = List.copyOf(slice);
        for (int index = 1; index < rows.size(); index++) StrictJson.require(rows.get(index).index() == Math.addExact(rows.get(index - 1).index(), 1),
                "surviving history order/index gap differs from actual Driver branch");
        return rows;
    }
    public static Row row(Obj original) {
        Objects.requireNonNull(original);
        return new Row(OpportunityJson.integer(original.get("index"), "index").longValueExact(),
                OpportunityJson.text(original.get("command"), "command"), OpportunityJson.bool(original.get("ok"), "ok"),
                original, effective(original));
    }
    /** NativeDriver._effective_native_history_entry; field presence, including explicit null, selects the outer result. */
    public static Effective effective(Obj original) {
        Optional<String> command = original.get("command") instanceof OpportunityJson.Text value
                ? Optional.of(value.value()) : Optional.empty();
        Optional<Obj> result = original.get("result") instanceof Obj value ? Optional.of(value) : Optional.empty();
        if (command.equals(Optional.of("auto-turn")) && result.isPresent()) {
            Obj outer = result.orElseThrow(); Optional<Obj> auto = object(outer.get("auto_turn"));
            command = auto.flatMap(value -> value.get("selected_step") instanceof OpportunityJson.Text selected
                    ? Optional.of(selected.value()) : Optional.empty());
            if (OUTER_RESULT_FIELDS.stream().noneMatch(outer.members()::containsKey)) {
                Optional<Obj> nested = auto.flatMap(value -> object(value.get("result")));
                if (nested.isPresent()) result = nested;
            }
        }
        return new Effective(command, result);
    }
    /** Query freshness view only. Timeline endpoint/exhaustion consumers must use entries(), never this slice. */
    public static List<Row> afterLatestRestore(List<Row> completeSurvivingBranch) {
        List<Row> rows = completeBranch(completeSurvivingBranch);
        for (int index = rows.size() - 1; index >= 0; index--) {
            Row row = rows.get(index);
            if (row.command().equals(RESTORE) && row.ok()) return List.copyOf(rows.subList(index + 1, rows.size()));
        }
        return rows;
    }
    /** One exact predicate shared by clocks and history. Existing command parsers remain the canonical token validators. */
    public static boolean isLifeAdvanceStep(String step) {
        if (step == null) return false;
        if (LifeAdvanceComposite.accepts(step)) return true;
        if (BattleAdvanceStep.parse(step).isPresent()) return true;
        try { RouteContactSteps.parse(step); return true; }
        catch (IllegalArgumentException unsupported) { return false; }
    }
    private static Optional<Obj> object(OpportunityJson.Value value) {
        return value instanceof Obj object ? Optional.of(object) : Optional.empty();
    }
}
