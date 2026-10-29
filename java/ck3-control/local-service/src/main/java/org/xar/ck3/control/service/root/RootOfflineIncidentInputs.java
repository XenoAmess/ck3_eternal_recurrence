package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal.Binding;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.BatchReviewCompletionPort;

/** Same borrowed writer session, actual incident originals, and source-bound empty scan evidence. */
public final class RootOfflineIncidentInputs implements RootPlanningInputsFactory.OfflineInputs, ActionPorts.IntentPreparationPort {
    private final RootRuntimeContext context;
    private final EpisodeIncidentJournal journal;
    public RootOfflineIncidentInputs(RootRuntimeContext actualContext, EpisodeIncidentJournal actualJournal) {
        context = Objects.requireNonNull(actualContext); journal = Objects.requireNonNull(actualJournal);
    }
    public EpisodeIncidentJournal journal() { return journal; }
    public BatchReviewCompletionPort reviewCompletion() { return journal::acknowledge; }
    @Override public void prepare(Session original, ActionCommand command) {
        if (!journal.handles(command)) return;
        try {
            context.writer().requireSession(original); context.requireCurrent(command.deadline());
            StrictJson.require(context.borrowedSession() == original && command.before().game().equals(context.game().generation())
                    && command.source().equals(context.source()) && command.sessionId().equals(context.game().sessionId()), "Incident preparation crossed its original writer or physical Game");
            String head = original.head().digest(); journal.before(command).orElseThrow(() -> new IOException("Original fallback did not produce its mandatory incident"));
            StrictJson.require(head.equals(original.head().digest()), "Incident capture changed the authoritative ledger head");
        } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    @Override public RootPlanningInputsFactory.OfflineObservation collect(RootPlanningInputsFactory.Capture actual, PlanningRequest complete) throws IOException {
        StrictJson.require(actual.context() == context && actual.session() == context.borrowedSession()
                && complete.before().equals(actual.frame().identity()) && complete.source().equals(actual.frame().source())
                && complete.sessionId().equals(actual.frame().sessionId()), "Actual incident scan crossed the complete request or borrowed session");
        context.writer().requireSession(actual.session()); context.requireCurrent(actual.deadline()); String head = actual.session().head().digest();
        EpisodeIncidentJournal.Scan scan = journal.scan(new Binding(complete.before(), complete.source(), complete.sessionId()));
        StrictJson.require(head.equals(actual.session().head().digest()), "Incident scan changed the authoritative ledger head");
        var source = new RootPlanningInputsFactory.FieldSource(complete.before(), complete.source(), complete.sessionId(), scan.evidence());
        return new RootPlanningInputsFactory.OfflineObservation(source, scan.batch());
    }
}
