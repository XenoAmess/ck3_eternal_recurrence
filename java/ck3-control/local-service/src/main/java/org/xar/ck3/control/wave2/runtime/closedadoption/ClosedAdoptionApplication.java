package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedCheckpointMeasurementCoordinator;

/** Shared original-writer and cold-consumer execution; production entry requires the retained explicit Root review. */
public final class ClosedAdoptionApplication {
    private ClosedAdoptionApplication() { }
    public record Completed(OriginalWriterTransaction.Committed writer, RecoveryEvidence basis,
            RecoveryEvidence qualification, OriginalColdConsumerSession.Consumed consumer,
            List<WindowsJobProcess.CommandResult> actualJobs) {
        public Completed { actualJobs = List.copyOf(actualJobs); }
        public boolean grantsWarmAttachment() { return false; }
    }
    public static Completed runTemporary(ClosedAdoptionRequest request, SavedCheckpointMeasurementCoordinator measured,
            WindowsFileWriterSession.Settings processSettings) throws IOException, InterruptedException {
        return runTemporary(new ClosedAdoptionSourceLoader(request,measured),processSettings);
    }
    public static Completed runTemporary(ClosedAdoptionSourceLoader source,
            WindowsFileWriterSession.Settings processSettings) throws IOException, InterruptedException {
        ClosedAdoptionRequest request = source.request();
        var root = processSettings.outputRoot().toRealPath();
        StrictJson.require(request.canonicalPath().toRealPath().startsWith(root)
                && request.metadataRoot().toRealPath().startsWith(root), "temporary canonical and publications stay within the explicit Root fixture root");
        source.preflightSources();
        return runOriginal(source.target(),source,source,source::currentCanonicalReceipt,
                source::publishBasis,source::publishQualification,processSettings,committed -> { });
    }
    @FunctionalInterface interface CommitObserver {
        void committed(OriginalWriterTransaction.Committed committed) throws IOException;
    }
    @FunctionalInterface interface EvidencePublisher {
        RecoveryEvidence publish(byte[] raw) throws IOException;
    }
    /** Only the retained Root review session calls this after independent explicit approval. */
    static Completed runProduction(ClosedAdoptionSourceLoader source, OriginalWriterTransaction.Target target,
            ClosedAdoptionMaterial.CurrentSource lockedCurrent, WindowsFileWriterSession.Settings processSettings,
            CommitObserver observer) throws IOException, InterruptedException {
        var root = processSettings.outputRoot().toRealPath();
        StrictJson.require(!target.canonicalPath().toRealPath().startsWith(root)
                && target.originalWriter().equals(source.request().writerSource()), "Root-approved actual production target and original writer");
        source.preflightProductionPublications();
        source.preflightSources();
        return runOriginal(target,lockedCurrent,source,source::currentCanonicalReceipt,
                source::publishProductionBasis,source::publishProductionQualification,processSettings,observer);
    }
    /** Constructed only after the actual original writer and original cold-consumer Jobs both succeeded. */
    static final class RetainedCompletion {
        private final Completed completed;
        private final OriginalWriterTransaction.RetainedSession writerSession;
        private RetainedCompletion(Completed completed, OriginalWriterTransaction.RetainedSession writerSession) {
            this.completed = completed; this.writerSession = writerSession;
        }
        Completed completed() { return completed; }
        OriginalWriterTransaction.RetainedSession writerSession() { return writerSession; }
    }
    static RetainedCompletion runProductionRetained(ClosedAdoptionSourceLoader source, OriginalWriterTransaction.Target target,
            ClosedAdoptionMaterial.CurrentSource lockedCurrent, ClosedAdoptionMaterial.CurrentSource handoffCurrent,
            Runnable rootScope, org.xar.ck3.control.wave2.runtime.savedproof.SavedProofReadTicket ticket,
            WindowsFileWriterSession.Settings settings, CommitObserver observer) throws IOException, InterruptedException {
        var root = settings.outputRoot().toRealPath();
        StrictJson.require(!target.canonicalPath().toRealPath().startsWith(root)
                && target.originalWriter().equals(source.request().writerSource()), "Root-approved actual production target and original writer");
        source.preflightProductionPublications(); source.preflightSources();
        List<WindowsFileWriterSession> sessions = new ArrayList<>(); Throwable failure = null;
        try {
            var actual = OriginalWriterTransaction.executeRetained(target,lockedCurrent,handoffCurrent,rootScope,ticket,settings);
            sessions.add(actual.process()); observer.committed(actual.committed());
            Completed completed = finishOriginal(actual.committed(),source,source::currentCanonicalReceipt,
                    source::publishProductionBasis,source::publishProductionQualification,settings,sessions);
            return new RetainedCompletion(completed,actual.session());
        } catch (IOException | InterruptedException | RuntimeException | Error error) {
            failure = error; throw error;
        } finally {
            if (failure != null) {
                for (var session : sessions) {
                    if (session.actualCommandResult().isEmpty()) { OriginalProcessCleanup.suppressing(session,failure); }
                }
            }
        }
    }
    /** One shared execution path; tests use the existing explicitly synthetic SDK seam with real original processes. */
    static Completed runOriginal(OriginalWriterTransaction.Target target, ClosedAdoptionMaterial.CurrentSource writerCurrent,
            ClosedAdoptionMaterial.CurrentSource current, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            EvidencePublisher basisPublisher, EvidencePublisher qualificationPublisher,
            WindowsFileWriterSession.Settings processSettings, CommitObserver observer) throws IOException, InterruptedException {
        List<WindowsFileWriterSession> sessions = new ArrayList<>();
        Throwable failure = null;
        try {
            var committed = OriginalWriterTransaction.execute(target,writerCurrent,selected -> {
                var session = WindowsFileWriterSession.start(processSettings,WindowsFileWriterSession.Mode.WRITER); sessions.add(session); return session;
            });
            observer.committed(committed);
            return finishOriginal(committed,current,canonical,basisPublisher,qualificationPublisher,processSettings,sessions);
        } catch (IOException | InterruptedException | RuntimeException | Error error) {
            failure = error;
            throw error;
        } finally {
            if (failure != null) {
                for (WindowsFileWriterSession session : sessions) {
                    if (session.actualCommandResult().isEmpty()) { OriginalProcessCleanup.suppressing(session,failure); }
                }
            }
        }
    }
    private static Completed finishOriginal(OriginalWriterTransaction.Committed committed,
            ClosedAdoptionMaterial.CurrentSource current, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            EvidencePublisher basisPublisher, EvidencePublisher qualificationPublisher,
            WindowsFileWriterSession.Settings settings, List<WindowsFileWriterSession> sessions)
            throws IOException, InterruptedException {
        var prepared = ClosedColdInputsConsumer.prepare(current,committed,canonical);
        RecoveryEvidence basis = basisPublisher.publish(prepared.basisBytes());
        RecoveryEvidence qualification = qualificationPublisher.publish(prepared.qualificationBytes(basis.reference()));
        var consumed = OriginalColdConsumerSession.run(current,committed,canonical,basis,qualification,() -> {
            var session = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.COLD_CONSUMER); sessions.add(session); return session;
        });
        List<WindowsJobProcess.CommandResult> jobs = sessions.stream().map(session -> session.actualCommandResult().orElseThrow()).toList();
        StrictJson.require(jobs.size() == 2 && jobs.stream().allMatch(WindowsJobProcess.CommandResult::passed),
                "both actual native Jobs complete with zero active processes");
        return new Completed(committed,basis,qualification,consumed,jobs);
    }
}
