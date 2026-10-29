package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/**
 * The complete staged Driver to completed-history producer used by restore publication.
 * Its output is an immutable candidate, never lifecycle, writer, readiness or adoption authority.
 * The caller supplies the actual source-bound lifecycle row and the cold reducer's full staged
 * Driver; this class neither invents a successful row nor recomputes rollback/goal state.
 */
public final class DriverRestoreHistoryProducer {
    private static final String MANAGED = "native-session-lifecycle-queue";
    private DriverRestoreHistoryProducer() { }

    public record Binding(String requestId, GameGeneration previousGame, GameGeneration replacementGame,
            DriverStateSnapshot.Session replacementSession, BigInteger restoredDateRaw) {
        public Binding {
            StrictJson.text(requestId); Objects.requireNonNull(previousGame); Objects.requireNonNull(replacementGame);
            Objects.requireNonNull(replacementSession); Objects.requireNonNull(restoredDateRaw);
            StrictJson.require(!previousGame.equals(replacementGame) && previousGame.pid() != replacementGame.pid()
                    && replacementSession.bridgePid() == replacementGame.pid(), "actual physical replacement and its complete Driver session required");
        }
    }

    /** Private construction binds a full archive reread to this exact staged Driver and original completion. */
    public static final class Candidate {
        private final DriverStateSnapshot.Complete driver;
        private final ExactRef driverEvidence;
        private final ExactRef stagedDriverEvidence;
        private final ExactRef completedRowEvidence;
        private final Binding binding;
        private Candidate(DriverStateSnapshot.Complete driver, ExactRef driverEvidence,
                ExactRef stagedDriverEvidence, ExactRef completedRowEvidence, Binding binding) {
            this.driver = driver; this.driverEvidence = driverEvidence; this.stagedDriverEvidence = stagedDriverEvidence;
            this.completedRowEvidence = completedRowEvidence; this.binding = binding;
        }
        public DriverStateSnapshot.Complete driver() { return driver; }
        public ExactRef driverEvidence() { return driverEvidence; }
        public ExactRef stagedDriverEvidence() { return stagedDriverEvidence; }
        public ExactRef completedRowEvidence() { return completedRowEvidence; }
        public Binding binding() { return binding; }
    }

    /**
     * Root calls under the existing canonical archive/writer scope. Both source artifacts must
     * already exist; failed lookup never archives caller bytes or creates an empty history.
     * The exact committed writer delta and same-session staged-producer transfer are checked by
     * the formal publication/adoption consumer after this candidate is prepared.
     */
    public static Candidate prepare(ActionPorts.OutcomeArchive archive, DriverStateSnapshot.Complete originalSavedDriver,
            ExactRef stagedDriverEvidence, ExactRef actualCompletedRowEvidence, Binding actual) {
        Objects.requireNonNull(archive); Objects.requireNonNull(originalSavedDriver); Objects.requireNonNull(actual);
        byte[] stagedWire = material(archive, stagedDriverEvidence);
        var staged = DriverStateSnapshot.decodeComplete(stagedWire);
        Obj completed = DriverJson.object(material(archive, actualCompletedRowEvidence), DriverJson.MAX_NATIVE_BYTES);
        DriverSurvivingHistory.row(completed);
        StrictJson.require(staged.session().equals(actual.replacementSession()), "staged complete Driver is not the actual replacement session");
        StrictJson.require(originalSavedDriver.session().actorId().equals(staged.session().actorId())
                && originalSavedDriver.session().episodeRunId().equals(staged.session().episodeRunId()), "restore may not invent an actor or a new episode");
        StrictJson.require(originalSavedDriver.lastCheckpoint() instanceof DriverStateSnapshot.Value
                && sameSlot(originalSavedDriver.lastCheckpoint(), staged.lastCheckpoint()), "original saved checkpoint must survive the staged cold reducer");
        Obj checkpoint = DriverJson.object(((DriverStateSnapshot.Value) originalSavedDriver.lastCheckpoint()).json(), DriverJson.MAX_NATIVE_BYTES);
        var identity = DriverHistoryProjection.checkpointIdentity(checkpoint).orElseThrow(() -> new IllegalArgumentException("complete saved checkpoint identity unavailable"));
        StrictJson.require(identity.dateRaw().equals(actual.restoredDateRaw()), "restored native date differs from the physical saved checkpoint");
        requireCheckpointEpisode(checkpoint, staged.session());
        List<Obj> saved = DriverSurvivingHistory.rows(originalSavedDriver);
        List<Obj> history = DriverSurvivingHistory.rows(staged);
        var savedAnchor = DriverHistoryProjection.checkpointHistoryIndex(checkpoint, saved);
        StrictJson.require(savedAnchor.isPresent() && savedAnchor.getAsInt() == saved.size()
                && history.size() >= saved.size(), "full saved Driver must end at its exact checkpoint anchor");
        for (int index = 0; index < saved.size(); index++)
            StrictJson.require(saved.get(index).equals(history.get(index)), "restore changed the saved surviving history prefix");
        StrictJson.require(sameSlot(originalSavedDriver.campaignGoal(), staged.campaignGoal())
                && sameSlot(originalSavedDriver.successionLifecycle(), staged.successionLifecycle()), "cold restore changed the original goal or lifecycle presence/value");
        StrictJson.require(staged.successionExpectation() instanceof DriverStateSnapshot.NullValue,
                "physical restore must invalidate the original frame-bound succession expectation");
        requireCompletion(completed, checkpoint, actual);

        var retained = DriverHistoryProjection.retain(checkpoint, history);
        StrictJson.require(retained instanceof DriverHistoryProjection.Available, "complete staged restore lineage unavailable");
        List<Obj> retainedRows = ((DriverHistoryProjection.Available) retained).rows();
        boolean alreadyCompleted = false;
        var replacement = DriverHistoryProjection.processReplacement(OpportunityJson.object(completed.get("result"), "completion result").get("lifecycle")).orElseThrow();
        for (int index = saved.size(); index < retainedRows.size(); index++) {
            Obj row = retainedRows.get(index);
            Obj result = OpportunityJson.object(row.get("result"), "retained restore result");
            if (!text(result.get("source"), MANAGED)) continue;
            Obj lifecycle = OpportunityJson.object(result.get("lifecycle"), "retained restore lifecycle");
            boolean sameRequest = text(lifecycle.get("request_id"), actual.requestId());
            boolean samePhysical = DriverHistoryProjection.processReplacement(lifecycle).filter(replacement::equals).isPresent();
            if (!sameRequest && !samePhysical) continue;
            StrictJson.require(sameRequest && samePhysical && index == retainedRows.size() - 1
                    && withoutIndex(row).equals(withoutIndex(completed)), "conflicting or nonfinal managed completion cannot authorize another physical restore");
            alreadyCompleted = true;
        }
        List<Obj> finalRows;
        if (alreadyCompleted) finalRows = retainedRows;
        else {
            var projection = DriverHistoryProjection.completedRestore(checkpoint, history, completed);
            StrictJson.require(projection instanceof DriverHistoryProjection.Available, "actual managed restore completion unavailable");
            finalRows = ((DriverHistoryProjection.Available) projection).rows();
        }
        var entries = new ArrayList<DriverStateSnapshot.HistoryEntry>(finalRows.size());
        for (Obj row : finalRows) entries.add(new DriverStateSnapshot.HistoryEntry(
                OpportunityJson.integer(row.get("index"), "restore history index").longValueExact(), new DriverStateSnapshot.Value(OpportunityJson.encode(row))));
        // NativeDriver._record_command only clears the managed marker at managed completion.
        // Every other business slot is the exact cold reducer output, including missing/null/empty.
        var driver = new DriverStateSnapshot.Complete(staged.session(), entries, staged.lastCheckpoint(), staged.rollbackWarFailure(),
                new DriverStateSnapshot.NullValue(), staged.successionExpectation(), staged.successionLifecycle(), staged.campaignGoal(), staged.rollbackWarFailures());
        byte[] finalWire = driver.encode();
        StrictJson.require(finalWire.length <= RawJson.MAXIMUM_BYTES, "complete restored Driver exceeds qualified archive lane; no truncation");
        ExactRef finalEvidence = archive.preserveMaterial(new RawJson(finalWire));
        StrictJson.require(java.util.Arrays.equals(finalWire, material(archive, finalEvidence)), "complete restored Driver differs from its immutable archive reread");
        return new Candidate(driver, finalEvidence, stagedDriverEvidence, actualCompletedRowEvidence, actual);
    }

    private static void requireCompletion(Obj completed, Obj checkpoint, Binding actual) {
        StrictJson.require(DriverHistoryProjection.provenRestore(completed, checkpoint), "actual completed restore receipt is not proven");
        Obj result = OpportunityJson.object(completed.get("result"), "completed restore result");
        Obj lifecycle = OpportunityJson.object(result.get("lifecycle"), "completed restore lifecycle");
        var replacement = DriverHistoryProjection.processReplacement(lifecycle).orElseThrow();
        StrictJson.require(text(result.get("source"), MANAGED) && text(lifecycle.get("request_id"), actual.requestId())
                && result.get("paused") instanceof OpportunityJson.Bool paused && paused.value()
                && checkpoint.equals(OpportunityJson.object(result.get("checkpoint"), "actual completed checkpoint"))
                && replacement.previousPid().longValueExact() == actual.previousGame().pid()
                && replacement.pid().longValueExact() == actual.replacementGame().pid(), "completed original row differs from this actual managed replacement request");
    }
    private static void requireCheckpointEpisode(Obj checkpoint, DriverStateSnapshot.Session session) {
        StrictJson.require(OpportunityJson.integer(checkpoint.get("episode_character_id"), "saved checkpoint actor").equals(session.actorId())
                && text(checkpoint.get("episode_run_id"), session.episodeRunId()), "saved checkpoint actor/episode differs from the actual replacement");
    }
    private static byte[] material(ActionPorts.OutcomeArchive archive, ExactRef ref) {
        Objects.requireNonNull(ref);
        StrictJson.require(ref.bytes() > 0 && ref.bytes() <= RawJson.MAXIMUM_BYTES, "bounded existing complete restore artifact required");
        byte[] wire = archive.loadMaterial(ref).bytes();
        StrictJson.require(wire.length == ref.bytes() && DriverJson.sha256(wire).equals(ref.sha256()), "original restore artifact content/source drift");
        return wire;
    }
    private static Obj withoutIndex(Obj row) {
        var fields = new LinkedHashMap<>(row.members()); fields.remove("index"); return new Obj(fields);
    }
    private static boolean sameSlot(DriverStateSnapshot.Slot first, DriverStateSnapshot.Slot second) {
        if (first instanceof DriverStateSnapshot.Value left && second instanceof DriverStateSnapshot.Value right)
            return OpportunityJson.parse(left.json()).equals(OpportunityJson.parse(right.json()));
        return first.equals(second);
    }
    private static boolean text(OpportunityJson.Value value, String expected) {
        return value instanceof OpportunityJson.Text word && word.value().equals(expected);
    }
}
