package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Read adapter borrowing the existing complete Driver owner and its actual canonical writer lease. */
public final class DriverHistoryAccess {
    /** Resolves Root's genuinely adopted owner at use time. The port cannot fabricate facts, history or a writer lease. */
    @FunctionalInterface public interface ActualAuthority { DriverStateAssembler current(); }
    public record View(DriverSnapshotFacts.Stamp stamp, ExactRef originalHistoryBasis,
            ExactRef currentDriverEvidence, List<DriverSurvivingHistory.Row> rows) {
        public View {
            Objects.requireNonNull(stamp); Objects.requireNonNull(originalHistoryBasis); Objects.requireNonNull(currentDriverEvidence);
            StrictJson.require(currentDriverEvidence.bytes() > 0 && currentDriverEvidence.sha256().equals(stamp.driverSha256()),
                    "current complete Driver evidence must bind this exact owner version");
            rows = DriverSurvivingHistory.completeBranch(rows);
        }
        public List<Obj> completeOriginalRows() { return rows.stream().map(DriverSurvivingHistory.Row::original).toList(); }
        public List<DriverSurvivingHistory.Row> freshQueryRows() { return DriverSurvivingHistory.afterLatestRestore(rows); }
    }
    private final ActualAuthority actualAuthority;
    private final ActionPorts.OutcomeArchive archive;
    public DriverHistoryAccess(DriverStateAssembler assembler, ActionPorts.OutcomeArchive canonicalArchive) {
        this(fixed(assembler),canonicalArchive);
    }
    /** Construction is valid before Root adoption; no authority is resolved until an actual history read begins. */
    public DriverHistoryAccess(ActualAuthority actualAuthority,ActionPorts.OutcomeArchive canonicalArchive) {
        this.actualAuthority=Objects.requireNonNull(actualAuthority);archive=Objects.requireNonNull(canonicalArchive);
    }
    private static ActualAuthority fixed(DriverStateAssembler assembler) { Objects.requireNonNull(assembler);return ()->assembler; }

    public View read(ActionCommand parent) {
        return withView(parent, Function.identity());
    }
    /** Work executes while the original writer/facts lease remains held; returning View alone does not retain that lease. */
    public <T> T withView(ActionCommand parent, Function<View, T> work) {
        Objects.requireNonNull(parent); Objects.requireNonNull(work);
        // Resolve exactly once. The entire callback retains this concrete owner's real original writer/facts lease.
        DriverStateAssembler assembler=Objects.requireNonNull(actualAuthority.current(),"actual adopted Driver authority unavailable");
        try {
            return assembler.withFrozenFacts(frozen -> {
                StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known, "complete original Driver history unavailable");
                DriverSnapshotFacts.Known known = (DriverSnapshotFacts.Known) frozen.state();
                StrictJson.require(DriverStateAssembler.projectHistory(known, frozen.actions(), frozen.activeActionId(), parent)
                        instanceof DriverStateSnapshot.Complete, "current surviving history lacks original durable action coverage");
                StrictJson.require(frozen.actions().originalHistory() instanceof ActionJournal.BoundHistoryBasis bound
                        && bound.originalDriverHistory().equals(known.originalHistoryBasis()), "canonical writer does not bind this full Driver history baseline");
                StrictJson.require(known.stamp().game().equals(parent.before().game())
                        && known.driver().session().bridgePid() == parent.before().game().pid()
                        && known.stamp().episodeRunId().equals(parent.before().frame().episodeRunId())
                        && known.driver().session().actorId().equals(parent.before().frame().identity().player()), "history read crossed the actual Game/episode/actor");
                StrictJson.require(frozen.activeActionId().isEmpty() || frozen.activeActionId().equals(java.util.Optional.of(parent.actionId())),
                        "another action owns the Driver history lease");
                for (var action : frozen.actions().actions()) {
                    if (!action.settled()) StrictJson.require(action.command().equals(parent),
                            "another unresolved action prevents route-history admission; UNKNOWN is never replay permission");
                }
                ExactRef current = DriverStateAssembler.currentEvidence(frozen, known.stamp(), archive);
                return work.apply(new View(known.stamp(), known.originalHistoryBasis(), current,
                        DriverSurvivingHistory.entries(known.driver())));
            });
        } catch (IOException failure) { throw new UncheckedIOException("actual frozen Driver history read failed", failure); }
    }
}
