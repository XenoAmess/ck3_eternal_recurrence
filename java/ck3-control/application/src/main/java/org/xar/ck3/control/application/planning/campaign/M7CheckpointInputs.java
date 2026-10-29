package org.xar.ck3.control.application.planning.campaign;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.checkpoint.CheckpointCommitVerifier;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.FirstCheckpointVerifier;
import org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SessionAuthority;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity;
import org.xar.ck3.control.g2.m7.CheckpointContinuity;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.KernelCheckpointContinuity;
import org.xar.ck3.control.g2.m7.NativeCalendarObservation;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext;

/**
 * Actual paired-SAVE and admitted-restore inputs for the M7 comparison consumer.
 * The original checkpoint, restore and cycle services retain every authority and all credit.
 */
public final class M7CheckpointInputs {
    private final ContinuityStorePort writer;
    private final SessionAuthority writerAuthority;
    private final CheckpointCommitVerifier checkpoints;
    private final DriverCheckpointStore checkpointDrivers;
    private final DriverAuthority drivers;
    private final ActionPorts.OutcomeArchive archive;

    /** The original global checkpoint verifier resolves the actual physical Game on every call. */
    @FunctionalInterface public interface DriverAuthority {
        DriverStateAssembler require(org.xar.ck3.control.application.session.SessionPorts.SessionIdentity actualOwner) throws IOException;
    }

    public M7CheckpointInputs(ContinuityStorePort soleWriter, SessionAuthority actualWriterAuthority, CheckpointCommitVerifier originalVerifier,
            DriverCheckpointStore actualCheckpointDrivers, DriverAuthority actualDrivers,
            ActionPorts.OutcomeArchive originalArchive) {
        writer = Objects.requireNonNull(soleWriter); writerAuthority = Objects.requireNonNull(actualWriterAuthority); checkpoints = Objects.requireNonNull(originalVerifier);
        checkpointDrivers = Objects.requireNonNull(actualCheckpointDrivers); drivers = Objects.requireNonNull(actualDrivers);
        archive = Objects.requireNonNull(originalArchive);
    }

    /** Invoke from the actual checkpoint-verifier callback before its SAVE boundary writer commit. */
    public Saved saved(ContinuityStorePort.Session borrowed, CheckpointCommitVerifier.VerifiedCheckpoint verified,
            FileWitness originalMaterial, G2Source source, String sourceEpoch, ExactRef executable,
            Optional<GovernmentContext.Context> government) throws IOException {
        return saved(borrowed, verified, originalMaterial, source, Optional.of(sourceEpoch), Optional.of(executable), government);
    }

    /** Invoke from the actual checkpoint-verifier callback before its SAVE boundary writer commit. */
    public Saved saved(ContinuityStorePort.Session borrowed, CheckpointCommitVerifier.VerifiedCheckpoint verified,
            FileWitness originalMaterial, G2Source source, Optional<String> sourceEpoch, Optional<ExactRef> executable,
            Optional<GovernmentContext.Context> government) throws IOException {
        Objects.requireNonNull(verified); writerAuthority.require(borrowed);
        checkpoints.requireIssued(borrowed, verified);
        org.xar.ck3.control.application.session.OrdinaryCycleTransitions.requireSameIdentity(
                verified.pair().frame(), verified.proof().semantic().frame());
        String head = borrowed.head().digest();
        DriverStateSnapshot.Complete saved = checkpointDrivers.readVerified(verified.pair());
        Optional<KernelCheckpointContinuity.Observation> observation = projectArchived(borrowed,
                verified.proof().semantic().frame(), source, saved, verified.proof().semantic(), sourceEpoch, executable, government);
        checkpoints.requireIssued(borrowed, verified);
        StrictJson.require(head.equals(borrowed.head().digest()), "writer changed during paired-SAVE kernel input capture");
        return new Saved(this, verified.pair(), Objects.requireNonNull(originalMaterial), CheckpointKind.ORDINARY,
                verified.originalHeadDigest(), source, observation);
    }

    /** Original saved material is replayed by its actual historical verifier; this grants no live or restore authority. */
    public Saved recovered(ContinuityStorePort.Session borrowed, SavedAttachmentSourceStore actualSources,
            CheckpointPair pair, FileWitness originalMaterial, G2Source originalSource, String originalSourceEpoch, ExactRef originalExecutable,
            Optional<GovernmentContext.Context> originalGovernment) throws IOException {
        return recovered(borrowed, actualSources, pair, originalMaterial, originalSource, Optional.of(originalSourceEpoch), Optional.of(originalExecutable), originalGovernment);
    }

    /** Original saved material is replayed by its actual historical verifier; this grants no live or restore authority. */
    public Saved recovered(ContinuityStorePort.Session borrowed, SavedAttachmentSourceStore actualSources,
            CheckpointPair pair, FileWitness originalMaterial, G2Source originalSource, Optional<String> originalSourceEpoch, Optional<ExactRef> originalExecutable,
            Optional<GovernmentContext.Context> originalGovernment) throws IOException {
        Objects.requireNonNull(actualSources); Objects.requireNonNull(pair); writerAuthority.require(borrowed);
        String head = borrowed.head().digest();
        var material = actualSources.loadRetainedOriginal(borrowed, originalMaterial, pair);
        borrowed.requireHistoricalState(material.originalHeadSequence(), material.originalHeadDigest());
        org.xar.ck3.control.application.session.OrdinaryCycleTransitions.requireSameIdentity(pair.frame(), material.proof().semantic().frame());
        DriverStateSnapshot.Complete saved = actualSources.readRetainedDriver(borrowed, material);
        Optional<KernelCheckpointContinuity.Observation> observation = projectArchived(borrowed,
                material.proof().semantic().frame(), originalSource, saved, material.proof().semantic(),
                originalSourceEpoch, originalExecutable, originalGovernment);
        var retained = actualSources.loadRetainedOriginal(borrowed, originalMaterial, pair);
        StrictJson.require(material.witness().equals(retained.witness()) && material.session().equals(retained.session())
                && material.checkpointDigest().equals(retained.checkpointDigest())
                && material.originalHeadDigest().equals(retained.originalHeadDigest()) && head.equals(borrowed.head().digest()),
                "original historical checkpoint material changed during kernel input reconstruction");
        writerAuthority.require(borrowed);
        return new Saved(this, pair, originalMaterial, CheckpointKind.ORDINARY, material.originalHeadDigest(), originalSource, observation);
    }

    /** Explicit first-SAVE data projection. It never fabricates an ordinary CompletedCycleProof. */
    public Saved savedFirst(ContinuityStorePort.Session borrowed, FirstCheckpointVerifier firstSaves,
            FirstCheckpointVerifier.VerifiedFirstCheckpoint verified, FileWitness originalMaterial,
            G2Source source, String sourceEpoch, ExactRef executable,
            Optional<GovernmentContext.Context> government) throws IOException {
        return savedFirst(borrowed, firstSaves, verified, originalMaterial, source, Optional.of(sourceEpoch), Optional.of(executable), government);
    }

    /** Explicit first-SAVE data projection. It never fabricates an ordinary CompletedCycleProof. */
    public Saved savedFirst(ContinuityStorePort.Session borrowed, FirstCheckpointVerifier firstSaves,
            FirstCheckpointVerifier.VerifiedFirstCheckpoint verified, FileWitness originalMaterial,
            G2Source source, Optional<String> sourceEpoch, Optional<ExactRef> executable,
            Optional<GovernmentContext.Context> government) throws IOException {
        writerAuthority.require(borrowed); Objects.requireNonNull(firstSaves); Objects.requireNonNull(verified);
        String head = borrowed.head().digest(); firstSaves.requireIssued(borrowed, verified);
        var observation = projectArchived(borrowed, verified.semantic().frame(), source, verified.savedDriver(),
                verified.semantic(), sourceEpoch, executable, government);
        firstSaves.requireIssued(borrowed, verified);
        StrictJson.require(head.equals(borrowed.head().digest()), "first SAVE kernel data capture changed canonical head");
        return new Saved(this, verified.pair(), Objects.requireNonNull(originalMaterial), CheckpointKind.FIRST,
                verified.originalHeadDigest(), source, observation);
    }

    /** Archived first-SAVE originals remain a separate typed branch after later SAVE/NEXT. No live permit is returned. */
    public Saved recoveredFirst(ContinuityStorePort.Session borrowed, SavedFirstCheckpointMaterialStore actualSources,
            CheckpointPair pair, FileWitness originalMaterial, G2Source originalSource, String originalSourceEpoch,
            ExactRef originalExecutable, Optional<GovernmentContext.Context> originalGovernment) throws IOException {
        return recoveredFirst(borrowed, actualSources, pair, originalMaterial, originalSource, Optional.of(originalSourceEpoch), Optional.of(originalExecutable), originalGovernment);
    }

    /** Archived first-SAVE originals remain a separate typed branch after later SAVE/NEXT. No live permit is returned. */
    public Saved recoveredFirst(ContinuityStorePort.Session borrowed, SavedFirstCheckpointMaterialStore actualSources,
            CheckpointPair pair, FileWitness originalMaterial, G2Source originalSource, Optional<String> originalSourceEpoch,
            Optional<ExactRef> originalExecutable, Optional<GovernmentContext.Context> originalGovernment) throws IOException {
        writerAuthority.require(borrowed); Objects.requireNonNull(actualSources);
        String head = borrowed.head().digest();
        var material = actualSources.loadRetainedOriginal(borrowed, originalMaterial, pair);
        var retained = material.checkpoint();
        var observation = projectArchived(borrowed, retained.semantic().frame(), originalSource, retained.savedDriver(),
                retained.semantic(), originalSourceEpoch, originalExecutable, originalGovernment);
        actualSources.requireRetained(borrowed, material);
        StrictJson.require(head.equals(borrowed.head().digest()), "retained first SAVE kernel projection changed canonical head");
        return new Saved(this, pair, originalMaterial, CheckpointKind.FIRST, retained.originalHeadDigest(), originalSource, observation);
    }

    /**
     * Root uses this in place of its one existing restore requireCurrent call, before cycle rebind/adopt.
     * It must be called outside a held writer Session because the original restore service acquires it.
     * The private restore proof is revalidated once; the following capture joins that exact attachment head.
     */
    public Restored restored(Saved saved, RestoreCheckpointService actualOriginalRestores, RestoreCheckpointService.RestoreBinding binding,
            String sourceEpoch, ExactRef executable, Optional<GovernmentContext.Context> government,
            Instant deadline) throws IOException, InterruptedException {
        return restored(saved, actualOriginalRestores, binding, Optional.of(sourceEpoch), Optional.of(executable), government, deadline);
    }

    public Restored restored(Saved saved, RestoreCheckpointService actualOriginalRestores, RestoreCheckpointService.RestoreBinding binding,
            Optional<String> sourceEpoch, Optional<ExactRef> executable, Optional<GovernmentContext.Context> government,
            Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(saved); Objects.requireNonNull(binding);
        StrictJson.require(saved.issuer == this && saved.pair.equals(binding.pair()),
                "restore kernel input must use this producer's exact verified physical SAVE pair");
        Objects.requireNonNull(actualOriginalRestores).requireCurrent(binding, deadline);
        return writer.locked(borrowed -> {
            writerAuthority.require(borrowed);
            StrictJson.require(borrowed.head().digest().equals(ContinuityJson.digest(binding.attachment().head().toJson())),
                    "restore attachment head changed before kernel comparison input capture");
            drivers.require(binding.session()).withFrozenFacts(borrowed, frozen -> {
                StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,
                        "actual complete admitted restore Driver is unavailable");
                DriverSnapshotFacts.Known known = (DriverSnapshotFacts.Known) frozen.state();
                StrictJson.require(known.stamp().game().equals(binding.session().game())
                        && known.stamp().episodeEpoch() == binding.episodeEpoch()
                        && known.stamp().episodeRunId().equals(binding.episodeRunId())
                        && Arrays.equals(known.driver().encode(), binding.driver().encode())
                        && frozen.actions().headSha256().equals(borrowed.head().digest()),
                        "restore kernel input crossed the actual published full Driver or canonical writer");
                return null;
            });
            StrictJson.require(saved.source.exactBuild().equals(binding.source().exactBuild()),
                    "restore kernel comparison crossed its qualified original build");
            Optional<KernelCheckpointContinuity.Observation> after = projectArchived(borrowed,
                    binding.semantic().frame(), binding.source(), binding.driver(), binding.semantic(), sourceEpoch,
                    executable, government);
            Optional<CheckpointContinuity.Comparison> compared = saved.observation.flatMap(before ->
                    after.map(current -> KernelCheckpointContinuity.compare(before, current)));
            StrictJson.require(saved.observation.isPresent() == after.isPresent(),
                    "restore changed presence of the original complete campaign goal");
            compared.ifPresent(value -> StrictJson.require(value.sameGoal() && value.sameCampaignOrigin()
                    && value.sameRulerEpisode() && value.sameMachine() && !value.sameGameIdentity()
                    && value.replacementBirthKnown(),
                    "actual restored kernel facts do not preserve the original goal/ruler on a distinct Game birth"));
            StrictJson.require(borrowed.head().digest().equals(ContinuityJson.digest(binding.attachment().head().toJson())),
                    "writer changed during actual restore kernel comparison");
            return new Restored(binding, saved.observation, after, compared);
        });
    }

    private Optional<KernelCheckpointContinuity.Observation> projectArchived(ContinuityStorePort.Session borrowed,
            ObservationIdentity frame, G2Source source, DriverStateSnapshot.Complete driver,
            SemanticEvidence semantic, Optional<String> sourceEpoch, Optional<ExactRef> executable,
            Optional<GovernmentContext.Context> government) throws IOException {
        Objects.requireNonNull(source); Objects.requireNonNull(sourceEpoch); Objects.requireNonNull(executable); Objects.requireNonNull(government);
        if (sourceEpoch.isPresent()) {
            String epoch = sourceEpoch.get();
            StrictJson.require(epoch.matches("[0-9a-f]{64}"), "supplied source epoch must be exact hex");
        }
        if (executable.isPresent()) {
            ExactRef exe = executable.get();
            StrictJson.require(exe.bytes() > 0, "supplied executable reference must be nonempty");
        }
        StrictJson.require(frame.equals(semantic.frame()) && driver.session().bridgePid() == frame.game().pid()
                && driver.session().episodeRunId().equals(frame.frame().episodeRunId())
                && driver.session().actorId().equals(frame.frame().identity().player()),
                "paired kernel input crossed actual Driver, Game birth, actor or episode");
        try { return archive.inSession(borrowed, bound -> {
            OpportunityJson.Obj snapshot = OpportunityJson.object(
                    OpportunityJson.parse(bound.loadMaterial(semantic.semantic()).bytes()), "original full saved/restored SEM");
            NativeCalendarObservation.project(frame, source, snapshot);
            OpportunityJson.Value semanticGoal = snapshot.get("campaign_goal");
            switch (driver.campaignGoal()) {
                case DriverStateSnapshot.Missing ignored -> {
                    StrictJson.require(semanticGoal == null, "missing saved goal became a synthetic goal");
                    return Optional.empty();
                }
                case DriverStateSnapshot.NullValue ignored -> {
                    StrictJson.require(semanticGoal == OpportunityJson.Nil.INSTANCE, "explicit null saved goal changed at kernel boundary");
                    return Optional.empty();
                }
                case DriverStateSnapshot.Value retained -> {
                    StrictJson.require(semanticGoal != null && OpportunityJson.parse(retained.json()).equals(semanticGoal),
                            "full saved Driver goal differs from the original SEM goal");
                    var goal = GoalCodec.parseGoal(OpportunityJson.toNode(semanticGoal));
                    var nativeFrame = frame.frame();
                    return Optional.of(new KernelCheckpointContinuity.Observation(frame.machineId(), sourceEpoch,
                            new GameIdentity(frame.game().pid(), frame.game().creationFiletime().value().toString()),
                            executable, nativeFrame.snapshotId(), nativeFrame.revision(),
                            nativeFrame.identity().nativeRevision(), nativeFrame.episodeRunId(),
                            nativeFrame.identity().player().longValueExact(), nativeFrame.identity().dateRaw().longValueExact(),
                            goal, government.map(GovernmentContext.Context::governmentKey).orElse(null),
                            government.map(GovernmentContext.Context::adapterFamily).orElse(null)));
                }
            }
        }); } catch (UncheckedIOException failure) { throw failure.getCause(); }
    }

    public enum CheckpointKind { ORDINARY, FIRST }

    /** Original verified paired-SAVE facts, not an extra checkpoint or a saved-day counter. */
    public static final class Saved {
        private final M7CheckpointInputs issuer;
        private final CheckpointPair pair;
        private final FileWitness materialWitness;
        private final CheckpointKind kind;
        private final String originalHeadDigest;
        private final G2Source source;
        private final Optional<KernelCheckpointContinuity.Observation> observation;
        private Saved(M7CheckpointInputs issuer, CheckpointPair pair, FileWitness materialWitness, CheckpointKind kind,
                String originalHeadDigest, G2Source source,
                Optional<KernelCheckpointContinuity.Observation> observation) {
            this.issuer = issuer; this.pair = pair; this.materialWitness = materialWitness; this.kind = kind;
            this.originalHeadDigest = originalHeadDigest; this.source = source; this.observation = observation;
        }
        public CheckpointPair pair() { return pair; }
        public FileWitness materialWitness() { return materialWitness; }
        public CheckpointKind kind() { return kind; }
        public Optional<KernelCheckpointContinuity.Observation> observation() { return observation; }
        public String originalHeadDigest() { return originalHeadDigest; }
        public long savedDayCredit() { return 0; }
    }
    public record Restored(RestoreCheckpointService.RestoreBinding binding,
            Optional<KernelCheckpointContinuity.Observation> before, Optional<KernelCheckpointContinuity.Observation> after,
            Optional<CheckpointContinuity.Comparison> comparison) {
        public Restored {
            Objects.requireNonNull(binding); Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(comparison);
        }
        public boolean grantsColdAuthority() { return false; }
        public boolean actionReplayAuthorized() { return false; }
        public long savedDayCredit() { return 0; }
    }
}
