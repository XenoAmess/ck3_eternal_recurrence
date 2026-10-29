package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.checkpoint.CheckpointCommitVerifier;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.planning.campaign.M7CheckpointInputs;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SessionAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** One Core factory retains each actual per-Game store triplet; capture still resolves the exact current physical owner. */
public final class RootM7CheckpointCaptureFactory implements RootCheckpointVerifier.SavedCaptureFactory {
    private record Created(CheckpointCommitVerifier pairs, DriverCheckpointStore drivers, SavedAttachmentSourceStore sources,
            M7CheckpointInputs inputs, RootM7CheckpointCapture capture) { }
    private final ContinuityStorePort writer;
    private final SessionAuthority sessions;
    private final ActionJournal actions;
    private final ActionPorts.OutcomeArchive archive;
    private final RootM7CheckpointCapture.RuntimeAuthority runtimes;
    private final List<Created> created = new ArrayList<>();

    public RootM7CheckpointCaptureFactory(ContinuityStorePort soleWriter, SessionAuthority actualWriterAuthority,
            ActionJournal actualActions, ActionPorts.OutcomeArchive originalArchive,
            RootM7CheckpointCapture.RuntimeAuthority actualRuntimes) {
        writer = Objects.requireNonNull(soleWriter); sessions = Objects.requireNonNull(actualWriterAuthority);
        actions = Objects.requireNonNull(actualActions); archive = Objects.requireNonNull(originalArchive);
        runtimes = Objects.requireNonNull(actualRuntimes);
    }

    @Override public synchronized RootM7CheckpointCapture create(CheckpointCommitVerifier actualPairs,
            DriverCheckpointStore actualDrivers, SavedAttachmentSourceStore actualSources) throws IOException {
        Objects.requireNonNull(actualPairs); Objects.requireNonNull(actualDrivers); Objects.requireNonNull(actualSources);
        for (Created original : created) {
            if (same(original, actualPairs, actualDrivers, actualSources)) return original.capture();
            StrictJson.require(original.pairs() != actualPairs && original.drivers() != actualDrivers && original.sources() != actualSources,
                    "a new physical store triplet cannot mix an original verifier, Driver store or saved-source authority");
        }
        M7CheckpointInputs inputs = new M7CheckpointInputs(writer, sessions, actualPairs, actualDrivers, owner -> {
            RootRuntimeContext current = Objects.requireNonNull(runtimes.require(owner));
            StrictJson.require(current.writer() == writer && current.game().machineId().equals(owner.machineId())
                    && current.game().generation().equals(owner.game()) && current.game().sessionId().equals(owner.sessionId()),
                    "actual checkpoint Driver resolver crossed the original writer or physical session");
            return current.adopted().authority();
        }, archive);
        RootM7HistoricalCheckpointInputs historical = new RootM7HistoricalCheckpointInputs(writer, sessions, actions, archive,
                actualSources, inputs);
        RootM7CheckpointCapture capture = new RootM7CheckpointCapture(inputs, runtimes, historical);
        created.add(new Created(actualPairs, actualDrivers, actualSources, inputs, capture));
        return capture;
    }

    /** Lookup uses the original three producer objects, never the most recent Game or a PID/path guess. */
    public synchronized M7CheckpointInputs requireInputs(CheckpointCommitVerifier actualPairs,
            DriverCheckpointStore actualDrivers, SavedAttachmentSourceStore actualSources) throws IOException {
        return requireCreated(actualPairs, actualDrivers, actualSources).inputs();
    }
    public synchronized RootM7CheckpointCapture requireCapture(CheckpointCommitVerifier actualPairs,
            DriverCheckpointStore actualDrivers, SavedAttachmentSourceStore actualSources) throws IOException {
        return requireCreated(actualPairs, actualDrivers, actualSources).capture();
    }
    private Created requireCreated(CheckpointCommitVerifier actualPairs, DriverCheckpointStore actualDrivers,
            SavedAttachmentSourceStore actualSources) throws IOException {
        Objects.requireNonNull(actualPairs); Objects.requireNonNull(actualDrivers); Objects.requireNonNull(actualSources);
        for (Created original : created) if (same(original, actualPairs, actualDrivers, actualSources)) return original;
        throw new IOException("the exact original Root verifier/Driver/source triplet has not created its M7 consumers");
    }
    private static boolean same(Created original, CheckpointCommitVerifier actualPairs,
            DriverCheckpointStore actualDrivers, SavedAttachmentSourceStore actualSources) {
        return original.pairs() == actualPairs && original.drivers() == actualDrivers && original.sources() == actualSources;
    }
}
