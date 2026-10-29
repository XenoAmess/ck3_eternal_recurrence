package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/** Pure original restore-history projection. Its result is a candidate for the sole assembler/writer, never authority. */
public final class DriverHistoryProjection {
    private static final String COLD = "native-session-cold-start";
    private static final String MANAGED = "native-session-lifecycle-queue";
    private static final Set<String> ANCHORS = Set.of("save-checkpoint", "restore-phase2-span-source-checkpoint-v1");
    private DriverHistoryProjection() { }
    public record CheckpointIdentity(String sha256, BigInteger size, BigInteger dateRaw) {
        public CheckpointIdentity {
            StrictJson.require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "canonical checkpoint SHA required");
            Objects.requireNonNull(size); Objects.requireNonNull(dateRaw); StrictJson.require(size.signum() > 0, "positive exact checkpoint size required");
        }
    }
    public record ProcessReplacement(BigInteger previousPid, BigInteger pid) {
        public ProcessReplacement {
            Objects.requireNonNull(previousPid); Objects.requireNonNull(pid);
            StrictJson.require(previousPid.signum() > 0 && pid.signum() > 0, "positive exact process identity required");
        }
    }
    public sealed interface Projection permits Available, Unavailable { }
    public record Available(List<Obj> rows, int checkpointHistoryIndex, int retainedPhysicalRestarts) implements Projection {
        public Available { rows = List.copyOf(rows); StrictJson.require(checkpointHistoryIndex >= 1 && retainedPhysicalRestarts >= 0, "actual checkpoint prefix required"); }
    }
    public record Unavailable(String reason) implements Projection { public Unavailable { StrictJson.text(reason); } }

    public static Optional<CheckpointIdentity> checkpointIdentity(Value value) {
        if (!(value instanceof Obj row)) return Optional.empty();
        if (!(row.get("sha256") instanceof OpportunityJson.Text digest) || !digest.value().matches("[0-9a-f]{64}")
                || !(row.get("size") instanceof OpportunityJson.IntegerValue size) || size.value().signum() <= 0
                || !(row.get("date_raw") instanceof OpportunityJson.IntegerValue date)) return Optional.empty();
        return Optional.of(new CheckpointIdentity(digest.value(), size.value(), date.value()));
    }
    public static Optional<ProcessReplacement> processReplacement(Value value) {
        if (!(value instanceof Obj row) || !(row.get("previous_pid") instanceof OpportunityJson.IntegerValue previous)
                || !(row.get("pid") instanceof OpportunityJson.IntegerValue current) || previous.value().signum() <= 0 || current.value().signum() <= 0) return Optional.empty();
        return Optional.of(new ProcessReplacement(previous.value(), current.value()));
    }
    public static OptionalInt checkpointHistoryIndex(Obj checkpoint, List<Obj> history) {
        Objects.requireNonNull(checkpoint); List<Obj> rows = checkedHistory(history);
        Optional<CheckpointIdentity> identity = checkpointIdentity(checkpoint);
        if (identity.isEmpty() || !(checkpoint.get("history_index") instanceof OpportunityJson.IntegerValue index)
                || index.value().compareTo(BigInteger.ONE) < 0 || index.value().compareTo(BigInteger.valueOf(rows.size())) > 0) return OptionalInt.empty();
        int count = index.value().intValueExact(); Obj anchor = rows.get(count - 1);
        if (!(anchor.get("index") instanceof OpportunityJson.IntegerValue ordinal) || !ordinal.value().equals(index.value())
                || !(anchor.get("command") instanceof OpportunityJson.Text command) || !ANCHORS.contains(command.value())
                || !(anchor.get("ok") instanceof OpportunityJson.Bool ok) || !ok.value() || !(anchor.get("result") instanceof Obj result)
                || !checkpointIdentity(result.get("checkpoint")).equals(identity)) return OptionalInt.empty();
        return OptionalInt.of(count);
    }
    /** Exact original hot-resume lookup. This DATA index is not checkpoint/cold authority. */
    public static OptionalInt matchingCheckpointHistoryIndex(Obj checkpoint,List<Obj> history) {
        Objects.requireNonNull(checkpoint);List<Obj> rows=checkedHistory(history);var identity=checkpointIdentity(checkpoint);
        if(identity.isEmpty())return OptionalInt.empty();
        for(int index=rows.size()-1;index>=0;index--) {
            Obj row=rows.get(index);
            if(row.get("command") instanceof OpportunityJson.Text command&&ANCHORS.contains(command.value())&&yes(row.get("ok"))
                    &&row.get("result") instanceof Obj result&&checkpointIdentity(result.get("checkpoint")).equals(identity))
                return OptionalInt.of(((OpportunityJson.IntegerValue)row.get("index")).value().intValueExact());
        }
        return OptionalInt.empty();
    }
    /** Exact original upgrade order: an already in-range index is retained even if a later cold check rejects its anchor. */
    public static Obj upgradeCheckpointAnchor(Obj checkpoint,List<Obj> history,BigInteger episodeCharacterId,String episodeRunId) {
        Objects.requireNonNull(checkpoint);Objects.requireNonNull(episodeCharacterId);StrictJson.text(episodeRunId);
        List<Obj> rows=checkedHistory(history);Value ordinal=checkpoint.get("history_index");
        boolean valid=ordinal instanceof OpportunityJson.IntegerValue index&&index.value().signum()>0
                &&index.value().compareTo(BigInteger.valueOf(rows.size()))<=0;
        Obj upgraded=checkpoint;
        if(!valid) {
            OptionalInt matching=matchingCheckpointHistoryIndex(checkpoint,rows);
            if(matching.isEmpty())return checkpoint;
            upgraded=checkpoint.with("history_index",new OpportunityJson.IntegerValue(BigInteger.valueOf(matching.getAsInt())));
        }
        return upgraded.with("episode_character_id",new OpportunityJson.IntegerValue(episodeCharacterId))
                .with("episode_run_id",new OpportunityJson.Text(episodeRunId));
    }
    public static boolean provenRestore(Obj row, Obj checkpoint) {
        Optional<CheckpointIdentity> identity = checkpointIdentity(checkpoint);
        if (identity.isEmpty() || !text(row.get("command"), DriverSurvivingHistory.RESTORE) || !yes(row.get("ok"))
                || !(row.get("result") instanceof Obj result) || !text(result.get("step"), DriverSurvivingHistory.RESTORE)
                || !yes(result.get("accepted")) || !text(result.get("status"), "restored") || !text(result.get("backend_id"), "native-headless")
                || !(text(result.get("source"), COLD) || text(result.get("source"), MANAGED))
                || !(result.get("restored_date_raw") instanceof OpportunityJson.IntegerValue date) || !date.value().equals(identity.orElseThrow().dateRaw())
                || !yes(result.get("map_ready")) || !checkpointIdentity(result.get("checkpoint")).equals(identity)) return false;
        Optional<ProcessReplacement> process = processReplacement(result.get("lifecycle"));
        return process.isPresent() && !process.orElseThrow().previousPid().equals(process.orElseThrow().pid());
    }
    /** Exact NativeDriver._checkpoint_history_with_restore_lineage: gameplay after the anchor is discarded; proven restarts survive. */
    public static Projection retain(Obj checkpoint, List<Obj> originalHistory) {
        List<Obj> history = List.copyOf(originalHistory); OptionalInt index = checkpointHistoryIndex(checkpoint, history);
        if (index.isEmpty()) return new Unavailable("checkpoint_history_anchor_not_proven");
        List<Obj> retained = new ArrayList<>(history.subList(0, index.getAsInt())); int restarts = 0;
        for (Obj row : history.subList(index.getAsInt(), history.size())) {
            if (!provenRestore(row, checkpoint)) continue;
            retained.add(withIndex(row, retained.size() + 1L)); restarts++;
        }
        return new Available(retained, index.getAsInt(), restarts);
    }
    /** Original completed managed request replaces only its matching final provisional cold row; older physical restarts remain. */
    public static Projection completedRestore(Obj checkpoint, List<Obj> history, Obj actualCompletedRow) {
        Objects.requireNonNull(actualCompletedRow);
        DriverSurvivingHistory.row(actualCompletedRow);
        if (!provenRestore(actualCompletedRow, checkpoint)) return new Unavailable("completed_restore_actual_receipt_not_proven");
        Projection projection = retain(checkpoint, history); if (!(projection instanceof Available available)) return projection;
        List<Obj> retained = new ArrayList<>(available.rows()); int restarts = available.retainedPhysicalRestarts();
        Obj actualResult = OpportunityJson.object(actualCompletedRow.get("result"), "actual completed restore result");
        if (!retained.isEmpty() && text(actualResult.get("source"), MANAGED)) {
            Obj last = retained.getLast();
            if (last.get("result") instanceof Obj previous && text(previous.get("source"), COLD)
                    && processReplacement(previous.get("lifecycle")).isPresent()
                    && processReplacement(previous.get("lifecycle")).equals(processReplacement(actualResult.get("lifecycle")))) {
                retained.removeLast(); restarts--;
            }
        }
        retained.add(withIndex(actualCompletedRow, retained.size() + 1L));
        return new Available(retained, available.checkpointHistoryIndex(), restarts + 1);
    }
    /** Only a pure reindex; all original result/error/extension fields remain verbatim in the typed JSON domain. */
    private static Obj withIndex(Obj row, long index) {
        var fields = new LinkedHashMap<String, Value>(row.members()); fields.put("index", new OpportunityJson.IntegerValue(BigInteger.valueOf(index))); return new Obj(fields);
    }
    private static List<Obj> checkedHistory(List<Obj> history) {
        List<Obj> rows = List.copyOf(history);
        DriverSurvivingHistory.completeBranch(rows.stream().map(DriverSurvivingHistory::row).toList());
        return rows;
    }
    private static boolean yes(Value value) { return value instanceof OpportunityJson.Bool flag && flag.value(); }
    private static boolean text(Value value, String expected) { return value instanceof OpportunityJson.Text text && text.value().equals(expected); }
}
