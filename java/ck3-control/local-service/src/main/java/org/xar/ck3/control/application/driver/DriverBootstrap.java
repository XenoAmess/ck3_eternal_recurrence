package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.CommandExpectation;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionReceiptCodec;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer;
import org.xar.ck3.control.application.history.LegacyResumeMigration;
import org.xar.ck3.control.nativebridge.NativeTransportDiagnostics.AdoptionRefusalReason;
import org.xar.ck3.control.service.root.RootOriginalDriverJournal;
import org.xar.ck3.control.service.root.RootRestoreMaterials;
import org.xar.ck3.control.service.root.RootLegacyResumeRuntime;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;

/** Concrete local-service assembly. Source imports and hello/frame ACKs grant no action or readiness authority. */
public final class DriverBootstrap {
    private DriverBootstrap() { }
    /** Exact original first-connection refusal. Generic IO, custody and source failures never use this type. */
    public static final class OriginalAdoptionRefused extends IOException {
        private static final long serialVersionUID=1L;
        private final AdoptionRefusalReason reason;
        private OriginalAdoptionRefused(AdoptionRefusalReason actualReason,String actualMessage) {
            super(actualMessage);reason=Objects.requireNonNull(actualReason);
        }
        public AdoptionRefusalReason reason(){return reason;}
    }

    /**
     * Reads the actual original Python Driver/WAL through its private physical issuer and sole complete
     * resume normalizer. Success is only these four first-connection guards; it is not a Seed, episode,
     * cold restore, fresh-start or action admission. An already-adopted Java checkpoint has a separate
     * real material/restore protocol and is never represented by a fabricated Python journal load.
     * The caller has already received the actual HELLO and sends the single PING only after success.
     */
    public static void requireOriginalAdoption(ContinuityStorePort.Session same,NativeGameTransport actual,
            RootOriginalDriverJournal.OriginalJournalLoad original)throws IOException {
        checkedOriginalAdoption(same,actual,original);
    }
    private static Optional<LegacyResumeNormalizer.Loaded> checkedOriginalAdoption(ContinuityStorePort.Session same,NativeGameTransport actual,
            RootOriginalDriverJournal.OriginalJournalLoad original)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(actual);Objects.requireNonNull(original);
        original.requireRetained(same);
        var hello=original.requireActualHello(same,actual);
        if(original.status()==RootOriginalDriverJournal.Status.JOURNAL_INVALID) {
            refuseOriginal(same,actual,original,AdoptionRefusalReason.INVALID_DRIVER_JOURNAL,
                    original.journalError().orElseThrow(()->new IOException("actual invalid journal lacks its original diagnostic")));
        }
        if(original.status()==RootOriginalDriverJournal.Status.MISSING) {original.requireRetained(same);return Optional.empty();}
        final LegacyResumeNormalizer.Result result;
        try {
            result=original.normalizeForFrozen(same);
        }catch(IllegalArgumentException | ArithmeticException invalidCanonical) {
            original.requireRetained(same);
            if(original.canonicalFailureIsJournalInvalid()) {
                refuseOriginal(same,actual,original,AdoptionRefusalReason.INVALID_DRIVER_JOURNAL,
                        "journaled Driver state failed canonical resume normalization: "+invalidCanonical.getMessage());
            }
            // The original base-only loader ignores a rejected state. This is not permission to create
            // an empty episode: the actual entry producer separately requires physically MISSING.
            return Optional.empty();
        }
        original.requireRetained(same);
        if(!(result instanceof LegacyResumeNormalizer.Loaded loaded)) {
            if(original.canonicalFailureIsJournalInvalid()) {
                String detail=result instanceof LegacyResumeNormalizer.Rejected rejected?rejected.driverError():
                        "canonical original state ignored: "+((LegacyResumeNormalizer.Ignored)result).reason();
                refuseOriginal(same,actual,original,AdoptionRefusalReason.INVALID_DRIVER_JOURNAL,
                        "journaled Driver state failed canonical resume normalization: "+detail);
            }
            return Optional.empty();
        }
        var persistedLifecycle=original.persistedLifecycleData();
        if(loaded.lifecycleMigrationRequired()!=original.lifecycleFieldWasMissing()
                ||loaded.lifecycleMigrationRequired()!=(persistedLifecycle instanceof RootOriginalDriverJournal.MissingLegacyLifecycle))
            throw new IOException("canonical original lifecycle presence differs from its retained raw payload");
        if(persistedLifecycle instanceof RootOriginalDriverJournal.ExplicitNullLifecycle
                &&loaded.normalizedLifecycle()!=OpportunityJson.Nil.INSTANCE)
            throw new IOException("canonical original native_campaign null differs from its retained raw payload");
        if(persistedLifecycle instanceof RootOriginalDriverJournal.BoundPersistedLifecycle bound
                &&!LegacyResumeMigration.lifecycleData(new LegacyResumeMigration.BoundLifecycle(bound.binding())).equals(loaded.normalizedLifecycle()))
            throw new IOException("canonical original bound lifecycle differs from its retained raw payload");
        if(original.status()==RootOriginalDriverJournal.Status.REPLAYED
                && !loaded.persistedBridgePid().equals(java.math.BigInteger.valueOf(hello.game().pid())))
            refuseOriginal(same,actual,original,AdoptionRefusalReason.ACTIVE_DRIVER_JOURNAL_REQUIRES_CONSOLIDATION,
                    "journaled Driver state needs a verified full-state barrier before cross-PID adoption");
        var reason=lifecycleRefusal(loaded,original.frozenLifecycleProjection());
        if(reason.isPresent())refuseOriginal(same,actual,original,reason.orElseThrow(),
                reason.orElseThrow()==AdoptionRefusalReason.LEGACY_LIFECYCLE_INCOMPATIBLE
                        ?"legacy driver state is only compatible with the frozen rogue xar_on profile"
                        :"persisted succession lifecycle differs from the frozen run profile");
        original.requireActualHello(same,actual);original.requireRetained(same);return Optional.of(loaded);
    }
    /** Pure classification DATA used by the real held-HELLO consumer above; grants no acceptance token. */
    static Optional<AdoptionRefusalReason> lifecycleRefusal(LegacyResumeNormalizer.Loaded loaded,
            LegacyResumeMigration.FrozenLifecycle frozen) {
        Objects.requireNonNull(loaded);Objects.requireNonNull(frozen);
        if(loaded.lifecycleMigrationRequired()) {
            return frozen instanceof LegacyResumeMigration.BoundLifecycle bound
                    &&bound.binding().profile()==SuccessionLifecycleBinding.Profile.ROGUE_ONE_LIFE?Optional.empty()
                    :Optional.of(AdoptionRefusalReason.LEGACY_LIFECYCLE_INCOMPATIBLE);
        }
        return LegacyResumeMigration.lifecycleData(frozen).equals(loaded.normalizedLifecycle())?Optional.empty()
                :Optional.of(AdoptionRefusalReason.PERSISTED_LIFECYCLE_MISMATCH);
    }
    private static void refuseOriginal(ContinuityStorePort.Session same,NativeGameTransport actual,
            RootOriginalDriverJournal.OriginalJournalLoad original,AdoptionRefusalReason reason,String message)throws IOException {
        original.requireActualHello(same,actual);original.requireRetained(same);
        var refusal=new OriginalAdoptionRefused(reason,message);
        actual.recordAdoptionRefused(reason,refusal.getClass().getName(),refusal.getMessage());
        throw refusal;
    }

    public record Seed(ExactRef fullDriver,ExactRef originalHistoryBasis,long driverVersion,long episodeEpoch,
            NativeObservationPort.TransportSession expectedSession,OpportunityJson.Obj auxiliary,Optional<DriverSnapshotFacts.LoopWitness> loop) {
        public Seed {
            Objects.requireNonNull(fullDriver);Objects.requireNonNull(originalHistoryBasis);Objects.requireNonNull(expectedSession);
            Objects.requireNonNull(auxiliary);Objects.requireNonNull(loop);StrictJson.safe(driverVersion,0);StrictJson.safe(episodeEpoch,0);
            StrictJson.require(fullDriver.bytes()>0 && fullDriver.bytes()<=DriverCheckpointStore.MAX_DRIVER_BYTES
                    && originalHistoryBasis.bytes()>0 && originalHistoryBasis.bytes()<=DriverCheckpointStore.MAX_DRIVER_BYTES,"bounded complete seed and original history artifacts required");
        }
    }
    @FunctionalInterface public interface ExactArtifactReader {
        byte[] read(ExactRef expected,int maximumBytes) throws IOException;
    }
    @FunctionalInterface public interface BorrowedSessionReader {
        ContinuityStorePort.Session current() throws IOException;
    }
    private static ActionPorts.OutcomeArchive borrowedArchive(ActionPorts.OutcomeArchive longLived,BorrowedSessionReader actualCurrent) {
        try { return longLived.withSession(Objects.requireNonNull(actualCurrent.current(),"currently held original writer required")); }
        catch(IOException failure) { throw new UncheckedIOException(failure); }
    }
    /** A real history producer's immutable index, never a caller's empty coverage list. */
    @FunctionalInterface public interface HistoryCoverageReader {
        Optional<? extends ArchivedActionCoverage> originalFor(ActionReceipt actualCanonicalReceipt) throws IOException;
        /** Finite original operator rejection verification. A generic reader has no installed private zero-dispatch authority. */
        default void requireOperatorNonRebind(ContinuityStorePort.Session same,ActionReceipt actual,
                ActionPorts.OutcomeArchive archive)throws IOException {
            DriverOperatorNonRebindOriginals.requireCanonical(same,actual,archive);
        }
    }
    public sealed interface ArchivedActionCoverage permits ArchivedHistoryRow,ArchivedCanonicalOnly { ExactRef receipt(); }
    public record ArchivedHistoryRow(ExactRef receipt,long historyIndex,ExactRef originalRow) implements ArchivedActionCoverage {
        public ArchivedHistoryRow {
            Objects.requireNonNull(receipt);Objects.requireNonNull(originalRow);StrictJson.safe(historyIndex,1);
            StrictJson.require(receipt.bytes()>0 && originalRow.bytes()>0,"actual archived receipt and full compatible history row required");
        }
    }
    public record ArchivedCanonicalOnly(ExactRef receipt,ExactRef originalSource) implements ArchivedActionCoverage {
        public ArchivedCanonicalOnly {Objects.requireNonNull(receipt);Objects.requireNonNull(originalSource);StrictJson.require(receipt.bytes()>0&&originalSource.bytes()>0,"actual canonical action source and receipt required");}
    }
    public enum AdoptionStatus { FRESH_OBSERVED, QUALIFICATION_REQUIRED, READ_ONLY_UNRESOLVED, READ_ONLY_INCOMPLETE_HISTORY, READ_ONLY_UNCLASSIFIED }
    private enum AdoptionKind { UNCLASSIFIED, PYTHON_ORIGINAL, JAVA_COLD, JAVA_HOT }

    /**
     * Replacement observations before canonical attachment. This object grants no restored session
     * admission. The exact same repository, held transport and public revision producer survive adoption.
     */
    public static final class Staged {
        private final Adopted provisional;
        private final DriverSnapshotFacts.Stamp predecessor;
        private final ActionSnapshotReader actions;
        private final ActionPorts.OutcomeArchive archive;
        private final NativeGameTransport transport;
        private final long originalLedgerSequence;
        private final String originalHeadSha256;
        private final Optional<RootRestoreMaterials.ColdAdoption> nativeCampaignOriginal;
        private Seed appliedSeed;
        private String appliedEventIdentity;
        private DriverSnapshotFacts.Stamp appliedStamp;
        private Staged(Adopted provisional,DriverSnapshotFacts.Stamp predecessor,ActionSnapshotReader actions,
                ActionPorts.OutcomeArchive archive,NativeGameTransport transport,long sequence,String digest,
                Optional<RootRestoreMaterials.ColdAdoption> nativeCampaignOriginal) {
            this.provisional=provisional;this.predecessor=predecessor;this.actions=actions;this.archive=archive;
            this.transport=transport;originalLedgerSequence=sequence;originalHeadSha256=digest;
            this.nativeCampaignOriginal=Objects.requireNonNull(nativeCampaignOriginal);
        }
        public DriverObservationAssembler.Complete first() { return provisional.first(); }
        public HeldDriverObservationPort observations() { return provisional.observations(); }
        public DriverStateAssembler authority() { return provisional.authority(); }
        public NativeDriverObservationProducer producer() { return provisional.producer(); }
        public G2Source source() { return provisional.source(); }
        public NativeObservationPort.TransportSession session() { return provisional.session(); }
        public DriverSnapshotFacts.Stamp expectedPredecessor() { return predecessor; }
        public long originalLedgerSequence() { return originalLedgerSequence; }
        public String originalHeadSha256() { return originalHeadSha256; }
        /** Only this private Stage, after its actual commit and CAS, can promote its original projection. */
        synchronized void requireNativeCampaignProjectionPublished(NativeDriverObservationProducer sameProducer,
                RootRestoreMaterials.ColdAdoption sameOriginal,ContinuityStorePort.Session same,Seed finalSeed,
                WriterContracts.Prepared originalPrepared,WriterContracts.Receipt receipt)throws IOException {
            StrictJson.require(producer()==Objects.requireNonNull(sameProducer)
                    &&nativeCampaignOriginal.filter(value->value==sameOriginal).isPresent(),
                    "restored projection promotion requires this Stage's identical producer and private capture");
            Objects.requireNonNull(same).requireCommitted(originalPrepared,receipt);
            requireRestoreCommitFields(this,finalSeed,originalPrepared,receipt);
            StrictJson.require(appliedSeed!=null&&appliedSeed.equals(finalSeed)
                    &&receipt.eventIdentity().equals(appliedEventIdentity)&&appliedStamp!=null
                    &&appliedStamp.driverVersion()==finalSeed.driverVersion()
                    &&appliedStamp.episodeEpoch()==finalSeed.episodeEpoch()
                    &&appliedStamp.game().equals(session().game())
                    &&appliedStamp.driverSha256().equals(finalSeed.fullDriver().sha256()),
                    "restored projection must follow the actual recorded canonical CAS publication");
            provisional.repository().locked(state->{
                StrictJson.require(state instanceof DriverSnapshotFacts.Known known
                        &&known.stamp().equals(appliedStamp)
                        &&known.originalHistoryBasis().equals(finalSeed.originalHistoryBasis()),
                        "published restored projection lost its actual repository stamp/history");return null;
            });
        }
    }

    /**
     * Captures the real original writer head and replacement facts together. Source artifacts remain
     * provenance DATA; the Root's current runtime/source verifier and full readiness still apply.
     */
    public static Staged stageRestored(Seed provisional,DriverSnapshotFacts.Stamp expectedPredecessor,
            ContinuityStorePort.Session borrowed,ActionSnapshotReader actions,NativeGameTransport transport,
            G2Source source,ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,
            HistoryCoverageReader coverage,int retainedFrames,Instant deadline,RootRestoreMaterials.ColdAdoption actualCold) throws IOException,InterruptedException {
        Objects.requireNonNull(provisional);Objects.requireNonNull(expectedPredecessor);
        Objects.requireNonNull(actualCold,"actual private cold material admission required").requireCurrent(borrowed,provisional,transport);
        StrictJson.require(provisional.driverVersion()==expectedPredecessor.driverVersion()
                && !provisional.expectedSession().game().equals(expectedPredecessor.game()),
                "restore staging requires the actual predecessor version and a distinct replacement Game");
        StrictJson.require(provisional.episodeEpoch()==expectedPredecessor.episodeEpoch()
                || provisional.episodeEpoch()==Math.addExact(expectedPredecessor.episodeEpoch(),1),
                "provisional restore epoch must remain or advance exactly once");
        try {
            return actions.withFrozen(borrowed,lease -> {
                try {
                    lease.assertCurrent();long sequence=lease.snapshot().ledgerSequence();String head=lease.snapshot().headSha256();
                    Optional<RootRestoreMaterials.ColdAdoption> nativeCampaign=actualCold.hasNativeCampaignProjection(borrowed,provisional,transport)
                            ?Optional.of(actualCold):Optional.empty();
                    Adopted staged=adoptInternal(provisional,borrowed,actions,transport,source,archive,originals,coverage,retainedFrames,deadline,
                            AdoptionKind.JAVA_COLD,Optional.empty(),Optional.empty(),nativeCampaign);
                    StrictJson.require(staged.first().identity().frame().episodeRunId().equals(expectedPredecessor.episodeRunId()),
                            "physical restore cannot silently create another episode");
                    actualCold.requireCurrent(borrowed,provisional,transport);
                    lease.assertCurrent();return new Staged(staged,expectedPredecessor,actions,archive,transport,sequence,head,nativeCampaign);
                } catch(IOException failure) { throw new UncheckedIOException(failure); }
                catch(InterruptedException interrupted) { throw new InterruptedBootstrap(interrupted); }
            });
        } catch(UncheckedIOException failure) { throw failure.getCause(); }
        catch(InterruptedBootstrap interrupted) { throw interrupted.interruption; }
    }

    /**
     * Publishes an already committed full replacement into the staged owner. No writer operation is
     * submitted here. A failed observation can be retried only against the same immutable commit;
     * the CAS and the session's public revision producer are never replayed or recreated.
     */
    public static Adopted adoptRestored(Staged stage,Seed finalSeed,WriterContracts.Prepared originalPrepared,
            WriterContracts.Receipt actualReceipt,ContinuityStorePort.Session borrowed,ExactArtifactReader originals,
            HistoryCoverageReader coverage,Instant deadline) throws IOException,InterruptedException {
        Objects.requireNonNull(stage);Objects.requireNonNull(finalSeed);Objects.requireNonNull(originalPrepared);
        Objects.requireNonNull(actualReceipt);Objects.requireNonNull(borrowed);Objects.requireNonNull(originals);
        Objects.requireNonNull(coverage);Objects.requireNonNull(deadline);
        synchronized(stage) {
            try {
                return stage.actions.withFrozen(borrowed,lease -> {
                    try {
                        lease.assertCurrent();StrictJson.require(Instant.now().isBefore(deadline),"restored adoption deadline expired");
                        requireRestoreCommit(stage,finalSeed,originalPrepared,actualReceipt,lease);
                        readExact(originals,stage.source().sourceRef(),DriverJson.MAX_NATIVE_BYTES);
                        StrictJson.require(stage.transport.awaitHello(deadline).equals(stage.session()),"staged held Native session changed before final adoption");
                        var driver=DriverStateSnapshot.decodeComplete(readExact(originals,finalSeed.fullDriver(),DriverCheckpointStore.MAX_DRIVER_BYTES));
                        StrictJson.require(driver.encode().length==finalSeed.fullDriver().bytes()
                                && DriverJson.sha256(driver.encode()).equals(finalSeed.fullDriver().sha256()),
                                "committed restored Driver reference must bind its complete canonical wire");
                        StrictJson.require(driver.session().bridgePid()==stage.session().game().pid()
                                && driver.session().pipeName().equals(stage.transport.pipeName())
                                && driver.session().episodeRunId().equals(stage.predecessor.episodeRunId())
                                && driver.session().actorId().equals(stage.provisional.first().identity().frame().identity().player()),
                                "final restored full Driver crossed staged Game/pipe/episode/actor");
                        readExact(originals,finalSeed.originalHistoryBasis(),DriverCheckpointStore.MAX_DRIVER_BYTES);
                        finalSeed.loop().ifPresent(loop -> {
                            try { readExact(originals,loop.originalFacts(),DriverJson.MAX_NATIVE_BYTES); }
                            catch(IOException failure) { throw new UncheckedIOException(failure); }
                        });
                        List<DriverSnapshotFacts.ActionRow> rows=new ArrayList<>();List<String> gaps=new ArrayList<>();boolean unresolved=false;
                        for(var actual:lease.snapshot().actions()) {
                            if(!actual.settled()) { unresolved=true;gaps.add("unreconciled_action:"+actual.command().actionId());continue; }
                            if(actual.command().expectation() instanceof CommandExpectation.OperatorRebind operator) {
                                if(actual.command().origin().game().equals(stage.session().game())
                                        &&actual.command().sessionId().equals(stage.session().sessionId())
                                        &&operator.expected().episodeRunId().equals(driver.session().episodeRunId())
                                        &&operator.expected().episodeEpoch()==finalSeed.episodeEpoch()) {
                                    if(DriverOperatorNonRebindOriginals.isRecordedNonRebound(actual))
                                        coverage.requireOperatorNonRebind(borrowed,actual,stage.archive);
                                    else DriverOperatorRebindOriginals.requireCoveredBy(borrowed,actual,stage.archive,driver,
                                            finalSeed.driverVersion(),finalSeed.episodeEpoch(),stage.session().game(),stage.session().sessionId());
                                }
                                continue; // Identity-only settlement has its own real canonical originals, no legacy row/CAS/event.
                            }
                            if(!(actual.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay))continue;
                            if(!actual.command().before().game().equals(stage.session().game())
                                    || !actual.command().before().frame().episodeRunId().equals(driver.session().episodeRunId()))continue;
                            Optional<? extends ArchivedActionCoverage> original=coverage.originalFor(actual);
                            if(original.isEmpty()) { gaps.add("original_history_row_unavailable:"+actual.command().actionId());continue; }
                            rows.add(validateCoverage(borrowed,actual,original.orElseThrow(),driver,stage.archive));
                        }
                        var stamp=new DriverSnapshotFacts.Stamp(finalSeed.driverVersion(),finalSeed.episodeEpoch(),stage.session().game(),
                                driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
                        var replacement=new DriverSnapshotFacts.Known(driver,stamp,finalSeed.originalHistoryBasis(),rows,finalSeed.auxiliary(),finalSeed.loop(),Optional.empty());
                        if(stage.appliedSeed==null) {
                            stage.provisional.repository().locked(state -> {
                                StrictJson.require(state instanceof DriverSnapshotFacts.Known,"staged full Driver owner unavailable");
                                var before=(DriverSnapshotFacts.Known)state;
                                StrictJson.require(before.stamp().driverVersion()==stage.predecessor.driverVersion()
                                        && before.stamp().game().equals(stage.session().game()),"staged Driver owner changed before its committed adoption");
                                stage.provisional.repository().compareAndSet(before.stamp(),replacement);return null;
                            });
                            // Record immediately after the only CAS, before any observation/archive can fail.
                            stage.appliedSeed=finalSeed;stage.appliedEventIdentity=actualReceipt.eventIdentity();stage.appliedStamp=stamp;
                        } else {
                            StrictJson.require(stage.appliedSeed.equals(finalSeed) && stage.appliedEventIdentity.equals(actualReceipt.eventIdentity())
                                    && stage.appliedStamp.equals(stamp),"a staged adoption cannot change its original committed replacement");
                            stage.provisional.repository().locked(state -> {
                                StrictJson.require(state instanceof DriverSnapshotFacts.Known known && known.stamp().equals(stamp),
                                        "previously adopted Driver changed; use current Root authority");return null;
                            });
                        }
                        if(stage.nativeCampaignOriginal.isPresent())
                            stage.provisional.producer().promoteNativeCampaignRestored(stage,finalSeed,originalPrepared,actualReceipt,borrowed);
                        DriverStateSnapshot projected=DriverStateAssembler.project(replacement,lease.snapshot(),Optional.empty());
                        if(projected instanceof DriverStateSnapshot.Incomplete missing)
                            for(String reason:missing.missingOrUnreconciledFields())if(!gaps.contains(reason))gaps.add(reason);
                        var first=stage.provisional.observations().observe(deadline);
                        StrictJson.require(first.identity().game().equals(stage.session().game()) && first.sessionId().equals(stage.session().sessionId())
                                && first.source().equals(stage.source()) && first.identity().frame().episodeRunId().equals(driver.session().episodeRunId())
                                && first.identity().frame().identity().player().equals(driver.session().actorId()),"final same-producer observation crossed committed restore");
                        ExactRef current=stage.archive.materialReferenceOf(RawJson.fullMaterial(driver.encode()));
                        StrictJson.require(current.bytes()==driver.encode().length && current.sha256().equals(stamp.driverSha256()),
                                "final complete Driver was not archived by the same real semantic producer");
                        lease.assertCurrent();AdoptionStatus status=unresolved ? AdoptionStatus.READ_ONLY_UNRESOLVED
                                : gaps.isEmpty() ? AdoptionStatus.QUALIFICATION_REQUIRED : AdoptionStatus.READ_ONLY_INCOMPLETE_HISTORY;
                        stage.provisional.producer().recordAdoptionObserved(stage.session(),stage.source());
                        return new Adopted(finalSeed,stage.source(),current,stage.provisional.repository(),stage.provisional.authority(),
                                stage.provisional.producer(),stage.provisional.observations(),first,status,gaps);
                    } catch(IOException failure) { throw new UncheckedIOException(failure); }
                    catch(InterruptedException interrupted) { throw new InterruptedBootstrap(interrupted); }
                });
            } catch(UncheckedIOException failure) { throw failure.getCause(); }
            catch(InterruptedBootstrap interrupted) { throw interrupted.interruption; }
        }
    }

    /**
     * Transfers one already committed NEXT_EPISODE into the existing repository/authority/revision producer.
     * This performs no writer mutation, Game launch, native execute, restore alias or readiness admission.
     */
    public static Adopted adoptNextEpisode(Adopted previous,LifecycleComposites.NextEpisodeAdoption actual,
            ContinuityStorePort.Session same,NativeGameTransport replacement,G2Source source,
            DriverCapabilityRuntime candidate,ActionPorts.OutcomeArchive longLivedArchive,
            BorrowedSessionReader currentSession,ExactArtifactReader originals,int retainedFrames,Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(previous);Objects.requireNonNull(actual);Objects.requireNonNull(same);
        Objects.requireNonNull(replacement);Objects.requireNonNull(source);Objects.requireNonNull(longLivedArchive);
        Objects.requireNonNull(candidate);Objects.requireNonNull(currentSession);Objects.requireNonNull(originals);Objects.requireNonNull(deadline);
        StrictJson.require(retainedFrames>=1 && retainedFrames<=4096,"explicit bounded retained observation count required");
        synchronized(previous) {
            return adoptNextEpisodeLocked(previous,actual,same,replacement,source,candidate,longLivedArchive,currentSession,
                    originals,retainedFrames,deadline);
        }
    }
    private static Adopted adoptNextEpisodeLocked(Adopted previous,LifecycleComposites.NextEpisodeAdoption actual,
            ContinuityStorePort.Session same,NativeGameTransport replacement,G2Source source,
            DriverCapabilityRuntime candidate,ActionPorts.OutcomeArchive longLivedArchive,
            BorrowedSessionReader currentSession,ExactArtifactReader originals,int retainedFrames,Instant deadline)
            throws IOException,InterruptedException {
        StrictJson.require(Instant.now().isBefore(deadline),"next episode adoption deadline expired");
        StrictJson.require(currentSession.current()==same,"NEXT must borrow the exact currently held original writer Session");
        candidate.requireNextCandidate(same,actual,previous.authority());
        var started=actual.replacement();var published=actual.published();
        NextTransfer retained=previous.nextTransfer;
        if(retained!=null) {
            retained.requireSame(actual,replacement,source,candidate,longLivedArchive,retainedFrames);
        } else {
            actual.requireCurrent(same);
        }
        StrictJson.require(previous.session().game().equals(started.oldGame())
                && !previous.session().game().equals(started.newGame())
                && previous.session().machineId().equals(source.machineId()),"original owner and private replacement Game differ");
        readExact(originals,source.sourceRef(),DriverJson.MAX_NATIVE_BYTES);
        byte[] full=readExact(originals,actual.driverReference(),DriverCheckpointStore.MAX_DRIVER_BYTES);
        StrictJson.require(Arrays.equals(full,published.driver().encode()),"next episode actual complete Driver original differs");
        readExact(originals,published.originalHistoryBasis(),DriverCheckpointStore.MAX_DRIVER_BYTES);
        for(ExactRef ref:List.of(started.launchEvidence(),started.helloEvidence(),started.lifecycleEvidence()))
            readExact(originals,ref,DriverJson.MAX_NATIVE_BYTES);
        var session=replacement.awaitHello(deadline);
        StrictJson.require(session.game().equals(started.newGame()) && session.sessionId().equals(started.sessionId())
                && session.machineId().equals(source.machineId()) && replacement.pipeName().equals(started.pipeName())
                && published.stamp().game().equals(session.game())
                && published.driver().session().bridgePid()==session.game().pid()
                && published.driver().session().pipeName().equals(started.pipeName()),"actual replacement Native/Driver/pipe/session differs");
        replacement.startHandshake(deadline);
        var loaded=actual.loadedObservation();
        StrictJson.require(Instant.now().isBefore(deadline) && loaded.session().equals(session)
                && !loaded.observedAt().isAfter(deadline),"retained next episode packet crossed replacement session or deadline");
        if(retained==null) {
            retained=new NextTransfer(actual,replacement,source,candidate,longLivedArchive,retainedFrames,
                    loaded);
            // Bind only validated physical/source inputs, before any mutable handover/publication.
            previous.nextTransfer=retained;
        }
        var transfer=retained;
        requireSameNextRaw(transfer.firstRaw,loaded);
        if(transfer.adopted!=null) {
            candidate.requireNextCandidate(same,actual,previous.authority());
            return transfer.adopted;
        }
        previous.authority().withFrozenFacts(same,frozen -> {
            requireNextPublished(frozen,published);
            candidate.requireNextCandidate(same,actual,previous.authority());
            previous.producer().transferNextEpisode(actual,same,replacement,source,session,candidate,previous.authority(),
                    wire -> borrowedArchive(longLivedArchive,currentSession).preserveMaterial(RawJson.fullMaterial(wire)));
            requireNextPublished(frozen,published);return null;
        });
        // This is the issuer's exact awaitSeedMap packet, including original observation time.
        // A later transport packet cannot replace it and retry never performs another native query.
        var nativeRaw=transfer.firstRaw;
        candidate.prepareNextObservation(same,nativeRaw);
        candidate.requireNextCandidate(same,actual,previous.authority());
        var assembler=new DriverObservationAssembler();
        var held=new HeldDriverObservationPort(replacement,previous.authority(),
                original -> borrowedArchive(longLivedArchive,currentSession).preserveNativeFrame(original),assembler,retainedFrames);
        List<String> gaps=new ArrayList<>();
        DriverObservationAssembler.Complete first=previous.authority().withFrozenRawObservation(nativeRaw,same,frozen -> {
            StrictJson.require(frozen.state().stamp().equals(published.stamp())
                    && Arrays.equals(frozen.state().driver().encode(),published.driver().encode()),"next episode first original Driver changed");
            requireNextPublished(frozen.driver(),published);
            if(frozen.projection() instanceof DriverStateSnapshot.Incomplete missing)gaps.addAll(missing.missingOrUnreconciledFields());
            ExactRef original=longLivedArchive.withSession(same).preserveNativeFrame(nativeRaw);
            var fullSnapshot=assembler.projectFull(nativeRaw,frozen.facts(),original);
            var result=assembler.assemble(nativeRaw,frozen.facts(),original);
            StrictJson.require(result instanceof DriverObservationAssembler.Complete,"actual next episode has no complete living native/Driver observation");
            var complete=(DriverObservationAssembler.Complete)result;
            StrictJson.require(complete.source().equals(source) && complete.sessionId().equals(session.sessionId())
                    && complete.identity().game().equals(session.game())
                    && complete.identity().frame().episodeRunId().equals(published.stamp().episodeRunId())
                    && complete.identity().frame().identity().player().equals(published.driver().session().actorId()),"next episode first complete observation crossed committed replacement");
            held.retainVerified(fullSnapshot,complete);
            candidate.requireNextCandidate(same,actual,previous.authority());return complete;
        });
        ExactRef archived=longLivedArchive.withSession(same).materialReferenceOf(RawJson.fullMaterial(published.driver().encode()));
        StrictJson.require(archived.bytes()==published.driver().encode().length
                && archived.sha256().equals(published.stamp().driverSha256()),"actual next episode full Driver was not archived by the same producer");
        var currentAuxiliary=previous.authority().withFrozenFacts(same,frozen -> {
            requireNextPublished(frozen,published);
            return ((DriverSnapshotFacts.Known)frozen.state()).auxiliary();
        });
        var seed=new Seed(actual.driverReference(),published.originalHistoryBasis(),published.stamp().driverVersion(),
                published.stamp().episodeEpoch(),session,currentAuxiliary,published.loop());
        candidate.requireNextCandidate(same,actual,previous.authority());
        previous.producer().recordAdoptionObserved(session,source);
        transfer.adopted=new Adopted(seed,source,archived,previous.repository(),previous.authority(),previous.producer(),held,first,
                gaps.isEmpty()?AdoptionStatus.QUALIFICATION_REQUIRED:AdoptionStatus.READ_ONLY_INCOMPLETE_HISTORY,gaps);
        return transfer.adopted;
    }
    private static void requireNextPublished(DriverStateAssembler.Frozen frozen,DriverSnapshotFacts.Known expected) {
        // The sole candidate proof separately checks every tracked auxiliary publication.
        StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"complete current next episode owner required");
        var current=(DriverSnapshotFacts.Known)frozen.state();
        StrictJson.require(current.stamp().equals(expected.stamp()) && Arrays.equals(current.driver().encode(),expected.driver().encode())
                && current.originalHistoryBasis().equals(expected.originalHistoryBasis())
                && current.actionRows().equals(expected.actionRows())
                && current.loop().equals(expected.loop()),"next episode canonical complete Driver publication changed");
    }

    /** Packet identity DATA only. It grants no lifecycle, writer, capability or readiness authority. */
    static void requireSameNextRaw(NativeObservationPort.ObservedFrame retained,NativeObservationPort.ObservedFrame actual) {
        Objects.requireNonNull(retained);Objects.requireNonNull(actual);
        StrictJson.require(retained.session().equals(actual.session()) && retained.snapshotId().equals(actual.snapshotId())
                && retained.nativeRevision().equals(actual.nativeRevision()) && retained.observedAt().equals(actual.observedAt())
                && Arrays.equals(retained.state().bytes(),actual.state().bytes())
                && Arrays.equals(retained.originalPacket(),actual.originalPacket()),
                "NEXT must retain the issuer's original first packet, source session, state and observation time");
    }
    private static final class NextTransfer {
        private final LifecycleComposites.NextEpisodeAdoption actual;
        private final NativeGameTransport transport;
        private final G2Source source;
        private final DriverCapabilityRuntime candidate;
        private final ActionPorts.OutcomeArchive archive;
        private final int retainedFrames;
        private final NativeObservationPort.ObservedFrame firstRaw;
        private Adopted adopted;
        private NextTransfer(LifecycleComposites.NextEpisodeAdoption actual,NativeGameTransport transport,G2Source source,
                DriverCapabilityRuntime candidate,ActionPorts.OutcomeArchive archive,int retainedFrames,
                NativeObservationPort.ObservedFrame firstRaw) {
            this.actual=actual;this.transport=transport;this.source=source;this.candidate=candidate;this.archive=archive;
            this.retainedFrames=retainedFrames;this.firstRaw=Objects.requireNonNull(firstRaw);
        }
        private void requireSame(LifecycleComposites.NextEpisodeAdoption requested,NativeGameTransport transport,G2Source source,
                DriverCapabilityRuntime candidate,ActionPorts.OutcomeArchive archive,int retainedFrames) {
            StrictJson.require(actual==requested && this.transport==transport && this.source.equals(source)
                    && this.candidate==candidate && this.archive==archive && this.retainedFrames==retainedFrames,
                    "a retained NEXT cannot replace its private adoption, transport, source, candidate, archive or retention contract");
        }
    }

    private static void requireRestoreCommit(Staged stage,Seed seed,WriterContracts.Prepared prepared,
            WriterContracts.Receipt receipt,ActionSnapshotReader.Lease lease) {
        requireRestoreCommitFields(stage,seed,prepared,receipt);
        StrictJson.require(receipt.head().sequence()==lease.snapshot().ledgerSequence()
                &&ContinuityJson.digest(receipt.head().toJson()).equals(lease.snapshot().headSha256()),
                "restore adoption requires the actual complete commit at the current original writer head");
        StrictJson.require(lease.snapshot().originalHistory() instanceof ActionJournal.BoundHistoryBasis bound
                &&bound.originalDriverHistory().equals(seed.originalHistoryBasis()),
                "restore changed its canonical full history basis");
    }
    private static void requireRestoreCommitFields(Staged stage,Seed seed,WriterContracts.Prepared prepared,
            WriterContracts.Receipt receipt) {
        StrictJson.require(prepared.predecessor().state().sequence()==stage.originalLedgerSequence
                && prepared.predecessor().digest().equals(stage.originalHeadSha256),"restore prepared another original writer head");
        StrictJson.require(SavedAttachmentAuthority.kinds().contains(prepared.request().kind()),"only an original ordinary or BASELINE-first canonical saved attachment commit can adopt a staged restore");
        var committed=prepared.reduced().toJson();committed.put("sequence",Math.addExact(stage.originalLedgerSequence,1));
        committed.put("last_event_identity",prepared.request().identity());
        StrictJson.require(receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE && receipt.eventIdentity().equals(prepared.request().identity())
                && ContinuityJson.same(receipt.head().toJson(),committed),
                "restore adoption requires the actual complete commit at the current original writer head");
        StrictJson.require(seed.expectedSession().equals(stage.session())
                && seed.originalHistoryBasis().equals(stage.provisional.seed().originalHistoryBasis()),
                "restore changed its held session or canonical full history basis");
        var details=DriverJson.object(prepared.request().details(),DriverJson.MAX_NATIVE_BYTES);
        var delta=OpportunityJson.object(details.get("driver_snapshot"),"driver_snapshot");
        long epoch=OpportunityJson.integer(delta.get("next_epoch"),"next_epoch").longValueExact();
        StrictJson.require(OpportunityJson.integer(delta.get("expected_version"),"expected_version").longValueExact()==stage.predecessor.driverVersion()
                && OpportunityJson.integer(delta.get("expected_epoch"),"expected_epoch").longValueExact()==stage.predecessor.episodeEpoch()
                && stage.predecessor.driverSha256().equals(OpportunityJson.text(delta.get("before_sha256"),"before_sha256"))
                && seed.fullDriver().sha256().equals(OpportunityJson.text(delta.get("after_sha256"),"after_sha256"))
                && seed.driverVersion()==Math.addExact(stage.predecessor.driverVersion(),1)
                && seed.episodeEpoch()==epoch && (epoch==stage.predecessor.episodeEpoch() || epoch==Math.addExact(stage.predecessor.episodeEpoch(),1)),
                "restored full Driver differs from the original committed version/epoch/hash delta");
        var generation=OpportunityJson.object(details.get("driver_after_game"),"driver_after_game");
        var birth=new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(OpportunityJson.text(generation.get("creation_filetime"),"creation_filetime"));
        StrictJson.require(OpportunityJson.integer(generation.get("pid"),"pid").longValueExact()==stage.session().game().pid()
                && new java.math.BigInteger(birth.decimal()).equals(stage.session().game().creationFiletime().value()),
                "committed restored Game identity differs from the exact held replacement");
    }

    /** Only adopt can mint this binding. Readiness and completed-cycle proofs remain separate authorities. */
    public static final class Adopted {
        private final Seed seed;
        private final G2Source source;
        private final NativeObservationPort.TransportSession session;
        private final ExactRef currentDriverEvidence;
        private final DriverFactsRepository repository;
        private final DriverStateAssembler authority;
        private final NativeDriverObservationProducer producer;
        private final HeldDriverObservationPort observations;
        private final DriverObservationAssembler.Complete first;
        private final AdoptionStatus status;
        private final List<String> incompleteReasons;
        private NextTransfer nextTransfer;
        private org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartAdmission cleanRestart;
        private FreshGameplayEntryAuthority.RecoveryAdmission initialRecovery;
        private org.xar.ck3.control.application.session.ContinuityBatchJournal.SettledSameGameData settledSameGame;
        public void requireSettledSameGame(org.xar.ck3.control.application.session.ContinuityBatchJournal.SettledSameGameData actual) {
            StrictJson.require(settledSameGame==Objects.requireNonNull(actual),
                    "Driver was not reconstructed from this actual settled same-Game history");
        }
        public void requireInitialNoDispatchRecovery(org.xar.ck3.control.application.session.ContinuityBatchJournal.InitialNoDispatchRecovery actual){
            Objects.requireNonNull(actual);
            StrictJson.require(initialRecovery!=null&&initialRecovery.initialNoDispatchRecovery().filter(value->value==actual).isPresent(),
                    "Driver was not created by this actual journal-issued initial interruption recovery");
        }


        public void requireInitialRecovery(FreshGameplayEntryAuthority.RecoveryAdmission actual){
            StrictJson.require(initialRecovery==Objects.requireNonNull(actual),"Driver was not created by this actual initial recovery admission");
        }
        public void requireCleanRestart(org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartAdmission actual){
            StrictJson.require(cleanRestart==Objects.requireNonNull(actual),"Driver was not created by this actual clean restart admission");
        }
        private Adopted(Seed seed,G2Source source,ExactRef currentDriverEvidence,DriverFactsRepository repository,
                DriverStateAssembler authority,NativeDriverObservationProducer producer,HeldDriverObservationPort observations,
                DriverObservationAssembler.Complete first,AdoptionStatus status,List<String> reasons) {
            this.seed=seed;this.source=source;session=seed.expectedSession();this.currentDriverEvidence=currentDriverEvidence;
            this.repository=repository;this.authority=authority;this.producer=producer;this.observations=observations;
            this.first=first;this.status=status;incompleteReasons=List.copyOf(reasons);
        }
        public Seed seed() { return seed; }
        public G2Source source() { return source; }
        public NativeObservationPort.TransportSession session() { return session; }
        public ExactRef currentDriverEvidence() { return currentDriverEvidence; }
        public DriverFactsRepository repository() { return repository; }
        public DriverStateAssembler authority() { return authority; }
        public NativeDriverObservationProducer producer() { return producer; }
        public HeldDriverObservationPort observations() { return observations; }
        public DriverObservationAssembler.Complete first() { return first; }
        public AdoptionStatus status() { return status; }
        public List<String> incompleteReasons() { return incompleteReasons; }
    }

    /** Observation-only raw Seed inspection. No private entry source, success diagnostic, handshake or readiness is granted. */
    public static Adopted adopt(Seed seed,ContinuityStorePort.Session borrowed,ActionSnapshotReader actions,
            NativeGameTransport transport,G2Source source,ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,
            HistoryCoverageReader coverage,int retainedFrames,Instant deadline) throws IOException,InterruptedException {
        return adoptInternal(seed,borrowed,actions,transport,source,archive,originals,coverage,retainedFrames,deadline,AdoptionKind.UNCLASSIFIED);
    }
    /** Same living Game, clean canonical batch boundary, new actual HELLO and independently requested full read. */
    public static Adopted adoptCleanRestart(org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartAdmission actual,
            ContinuityStorePort.Session same,ActionSnapshotReader actions,NativeGameTransport transport,G2Source source,
            ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,int retainedFrames,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(actual);actual.requireCurrent(same);
        StrictJson.require(source.equals(actual.manifest().source()),"same-Game restart retains its logical source DATA without a new startup audit");
        var old=actual.manifest().previousTransport();var current=transport.awaitHello(deadline);
        StrictJson.require(current.machineId().equals(old.machineId())&&current.game().equals(old.game())&&current.sessionId().equals(old.sessionId())
                &&current.connectionGeneration().compareTo(old.connectionGeneration())>0,"clean restart requires the same Game PID/birth and a new actual HELLO generation");
        var facts=actual.facts();
        var seed=new Seed(actual.manifest().fullDriver(),facts.originalHistoryBasis(),facts.stamp().driverVersion(),facts.stamp().episodeEpoch(),current,facts.auxiliary(),facts.loop());
        java.util.Map<String,DriverSnapshotFacts.ActionRow> rows=new java.util.HashMap<>();facts.actionRows().forEach(row->rows.put(row.actionId(),row));
        HistoryCoverageReader coverage=receipt->{
            var row=rows.get(receipt.command().actionId());if(row==null)return Optional.empty();
            StrictJson.require(row.bodySha256().equals(receipt.bodySha256())&&row.durableSequence()==receipt.sequence(),"restart action coverage crossed its actual canonical receipt");
            ExactRef ref=archive.receiptReferenceOf(receipt);
            if(row.coverageSource() instanceof DriverSnapshotFacts.LegacyHistoryRow legacy)return Optional.of(new ArchivedHistoryRow(ref,legacy.historyIndex(),legacy.originalRow()));
            return Optional.of(new ArchivedCanonicalOnly(ref,((DriverSnapshotFacts.CanonicalOnly)row.coverageSource()).originalSource()));
        };
        transport.startHandshake(deadline);
        var result=adoptInternal(seed,same,actions,transport,source,archive,originals,coverage,retainedFrames,deadline,AdoptionKind.JAVA_HOT,
                Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(actual));
        StrictJson.require(result.status()==AdoptionStatus.QUALIFICATION_REQUIRED
                &&result.first().identity().frame().identity().dateRaw().longValueExact()==actual.manifest().dateRaw(),
                "clean restart cannot discard unresolved history or a changed game date");
        actual.requireCurrent(same);result.cleanRestart=actual;return result;
    }
    /** Pure routing DATA, derived only from the sole canonical resume result. An empty set grants no admission. */
    public enum OriginalResumeNeed { MODERN_SESSION_BINDING, FULL_HISTORY_MATERIALIZATION, LIFECYCLE_MIGRATION, ROLLBACK_MIGRATION, MANAGED_RESTORE_RESOLUTION }
    public static java.util.Set<OriginalResumeNeed> originalResumeNeeds(LegacyResumeNormalizer.Loaded canonical) {
        Objects.requireNonNull(canonical);var needs=java.util.EnumSet.noneOf(OriginalResumeNeed.class);
        boolean modern=canonical.formatVersion()==2 && canonical.episode().isPresent()
                && isSignedInt32Actor(canonical.episode().orElseThrow().characterId())
                && canonical.persistedBridgePid().compareTo(new java.math.BigInteger("4294967295"))<=0;
        if(!modern)needs.add(OriginalResumeNeed.MODERN_SESSION_BINDING);
        if(!(canonical.normalizedPayload().get("command_history") instanceof OpportunityJson.Arr))needs.add(OriginalResumeNeed.FULL_HISTORY_MATERIALIZATION);
        if(canonical.lifecycleMigrationRequired())needs.add(OriginalResumeNeed.LIFECYCLE_MIGRATION);
        if(canonical.rollbackMigrationRequired())needs.add(OriginalResumeNeed.ROLLBACK_MIGRATION);
        if(canonical.normalizedPayload().get("managed_restore_transaction")!=OpportunityJson.Nil.INSTANCE)
            needs.add(OriginalResumeNeed.MANAGED_RESTORE_RESOLUTION);
        return java.util.Set.copyOf(needs);
    }

    private static boolean isSignedInt32Actor(java.math.BigInteger value) {
        try {
            org.xar.ck3.control.contracts.NativeCharacterId.of(value);
            return true;
        } catch (IllegalArgumentException invalid) {
            return false;
        }
    }

    /** Actual first Python connection: physical load, canonical complete resume and frozen profile are mandatory. */
    public static Adopted adoptOriginal(Seed seed,ContinuityStorePort.Session borrowed,ActionSnapshotReader actions,
            NativeGameTransport transport,G2Source source,ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,
            HistoryCoverageReader coverage,int retainedFrames,Instant deadline,RootOriginalDriverJournal.OriginalJournalLoad actualOriginal)
            throws IOException,InterruptedException {
        Objects.requireNonNull(seed);Objects.requireNonNull(actualOriginal);Objects.requireNonNull(transport);transport.awaitHello(deadline);
        var loaded=checkedOriginalAdoption(borrowed,transport,actualOriginal)
                .orElseThrow(()->new IOException("missing or rejected original Driver cannot become a modern seeded episode"));
        var required=originalResumeNeeds(loaded);
        if(!required.isEmpty())throw new IOException("canonical original state requires its actual binding/migration/transaction producer before modern hot adoption: "+required);
        var actual=DriverJson.object(readExact(originals,seed.fullDriver(),DriverCheckpointStore.MAX_DRIVER_BYTES),DriverCheckpointStore.MAX_DRIVER_BYTES);
        var basis=DriverJson.object(readExact(originals,seed.originalHistoryBasis(),DriverCheckpointStore.MAX_DRIVER_BYTES),DriverCheckpointStore.MAX_DRIVER_BYTES);
        var canonical=loaded.normalizedPayload();
        // The complete Driver envelope has no legacy migration flags. All actual business/history fields
        // must be the sole canonical producer's exact result; no reconstructed empty seed is accepted.
        for(var entry:canonical.members().entrySet()) {
            if(entry.getKey().equals("succession_lifecycle_migration_required") || entry.getKey().equals("rollback_war_failures_migration_required"))continue;
            StrictJson.require(entry.getValue().equals(actual.get(entry.getKey())),"complete seed differs from canonical original Driver: "+entry.getKey());
        }
        StrictJson.require(new OpportunityJson.Text(actualOriginal.pipeName()).equals(actual.get("pipe_name"))
                && Objects.equals(actual.get("command_history"),basis.get("command_history")),"original canonical full history/pipe differs from seed basis");
        actualOriginal.requireActualHello(borrowed,transport);actualOriginal.requireRetained(borrowed);
        var result=adoptInternal(seed,borrowed,actions,transport,source,archive,originals,coverage,retainedFrames,deadline,AdoptionKind.PYTHON_ORIGINAL);
        actualOriginal.requireRetained(borrowed);return result;
    }
    /** Sole actual legacy migration producer plus its real committed original writer transition. */
    public static Adopted adoptResolvedOriginal(RootLegacyResumeRuntime.Prepared actual,WriterContracts.Receipt committed,
            ContinuityStorePort.Session same,ActionSnapshotReader actions,NativeGameTransport transport,G2Source source,
            ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,HistoryCoverageReader coverage,int retainedFrames,Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(actual);actual.requireOwner(same,transport,source,archive);actual.requireCommitted(same,committed);
        Seed seed=actual.seed(same,committed);
        Optional<SavedNativeBootstrap> savedNative=actual.hasSavedNativeProjection(same,committed)
                ?Optional.of(new SavedNativeBootstrap(actual,committed)):Optional.empty();
        Adopted result=adoptInternal(seed,same,actions,transport,source,archive,originals,coverage,retainedFrames,deadline,
                AdoptionKind.PYTHON_ORIGINAL,Optional.of(actual.originalNative()),savedNative);
        actual.requireCommitted(same,committed);return result;
    }
    private static Adopted adoptInternal(Seed seed,ContinuityStorePort.Session borrowed,ActionSnapshotReader actions,
            NativeGameTransport transport,G2Source source,ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,
            HistoryCoverageReader coverage,int retainedFrames,Instant deadline,AdoptionKind kind)throws IOException,InterruptedException {
        return adoptInternal(seed,borrowed,actions,transport,source,archive,originals,coverage,retainedFrames,deadline,kind,Optional.empty());
    }
    private static Adopted adoptInternal(Seed seed,ContinuityStorePort.Session borrowed,ActionSnapshotReader actions,
            NativeGameTransport transport,G2Source source,ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,
            HistoryCoverageReader coverage,int retainedFrames,Instant deadline,AdoptionKind kind,Optional<NativeObservationPort.ObservedFrame> resolvedRaw)throws IOException,InterruptedException {
        return adoptInternal(seed,borrowed,actions,transport,source,archive,originals,coverage,retainedFrames,deadline,
                kind,resolvedRaw,Optional.empty());
    }
    /** Private carrier of the actual already-committed Saved preparation, never a decoded source token. */
    private record SavedNativeBootstrap(RootLegacyResumeRuntime.Prepared original,WriterContracts.Receipt committed) {
        private SavedNativeBootstrap {Objects.requireNonNull(original);Objects.requireNonNull(committed);}
    }
    private static Adopted adoptInternal(Seed seed,ContinuityStorePort.Session borrowed,ActionSnapshotReader actions,
            NativeGameTransport transport,G2Source source,ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,
            HistoryCoverageReader coverage,int retainedFrames,Instant deadline,AdoptionKind kind,
            Optional<NativeObservationPort.ObservedFrame> resolvedRaw,Optional<SavedNativeBootstrap> savedNative)throws IOException,InterruptedException {
        return adoptInternal(seed,borrowed,actions,transport,source,archive,originals,coverage,retainedFrames,deadline,
                kind,resolvedRaw,savedNative,Optional.empty());
    }
    private static Adopted adoptInternal(Seed seed,ContinuityStorePort.Session borrowed,ActionSnapshotReader actions,
            NativeGameTransport transport,G2Source source,ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,
            HistoryCoverageReader coverage,int retainedFrames,Instant deadline,AdoptionKind kind,
            Optional<NativeObservationPort.ObservedFrame> resolvedRaw,Optional<SavedNativeBootstrap> savedNative,
            Optional<RootRestoreMaterials.ColdAdoption> restoredNative)throws IOException,InterruptedException {
        return adoptInternal(seed,borrowed,actions,transport,source,archive,originals,coverage,retainedFrames,deadline,kind,resolvedRaw,savedNative,restoredNative,Optional.empty());
    }
    private static Adopted adoptInternal(Seed seed,ContinuityStorePort.Session borrowed,ActionSnapshotReader actions,
            NativeGameTransport transport,G2Source source,ActionPorts.OutcomeArchive archive,ExactArtifactReader originals,
            HistoryCoverageReader coverage,int retainedFrames,Instant deadline,AdoptionKind kind,
            Optional<NativeObservationPort.ObservedFrame> resolvedRaw,Optional<SavedNativeBootstrap> savedNative,
            Optional<RootRestoreMaterials.ColdAdoption> restoredNative,
            Optional<org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartAdmission> cleanRestart)throws IOException,InterruptedException {
        Objects.requireNonNull(seed);Objects.requireNonNull(borrowed);Objects.requireNonNull(actions);Objects.requireNonNull(transport);
        Objects.requireNonNull(source);Objects.requireNonNull(archive);Objects.requireNonNull(originals);Objects.requireNonNull(coverage);Objects.requireNonNull(deadline);
        Objects.requireNonNull(resolvedRaw);Objects.requireNonNull(savedNative);Objects.requireNonNull(restoredNative);
        StrictJson.require(savedNative.isEmpty()||restoredNative.isEmpty(),"one actual private projection source required");
        StrictJson.require(Instant.now().isBefore(deadline),"Driver adoption deadline expired");
        StrictJson.require(source.machineId().equals(seed.expectedSession().machineId()),"seed/source machine differs");
        try {
            return actions.withFrozen(borrowed,lease -> {
                try {
                    lease.assertCurrent();
                    StrictJson.require(lease.activeActionId().isEmpty(),"Driver adoption cannot replace an active coordinator action scope");
                    StrictJson.require(lease.snapshot().originalHistory() instanceof ActionJournal.BoundHistoryBasis bound
                            && bound.originalDriverHistory().equals(seed.originalHistoryBasis()),"canonical writer does not bind this exact original full history basis");
                    byte[] full=readExact(originals,seed.fullDriver(),DriverCheckpointStore.MAX_DRIVER_BYTES);
                    byte[] baseline=seed.fullDriver().equals(seed.originalHistoryBasis()) ? full
                            : readExact(originals,seed.originalHistoryBasis(),DriverCheckpointStore.MAX_DRIVER_BYTES);
                    // A digest or a WAL tail alone cannot stand in for the full original history body.
                    DriverStateSnapshot.decodeComplete(baseline);
                    var driver=DriverStateSnapshot.decodeComplete(full);
                    StrictJson.require(driver.session().bridgePid()==seed.expectedSession().game().pid()
                            && driver.session().pipeName().equals(transport.pipeName()),"complete seed belongs to another actual Game process/pipe");
                    if(kind!=AdoptionKind.JAVA_HOT)readExact(originals,source.sourceRef(),DriverJson.MAX_NATIVE_BYTES);
                    seed.loop().ifPresent(loop -> {
                        try { readExact(originals,loop.originalFacts(),DriverJson.MAX_NATIVE_BYTES); }
                        catch(IOException failure) { throw new UncheckedIOException(failure); }
                    });
                    var stamp=new DriverSnapshotFacts.Stamp(seed.driverVersion(),seed.episodeEpoch(),seed.expectedSession().game(),
                            driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
                    List<DriverSnapshotFacts.ActionRow> rows=new ArrayList<>();List<String> gaps=new ArrayList<>();boolean unresolved=false;
                    for(var actual:lease.snapshot().actions()) {
                        if(!actual.settled()) { unresolved=true;gaps.add("unreconciled_action:"+actual.command().actionId());continue; }
                        if(actual.command().expectation() instanceof CommandExpectation.OperatorRebind operator) {
                            if(actual.command().origin().game().equals(stamp.game())
                                    &&actual.command().sessionId().equals(seed.expectedSession().sessionId())
                                    &&operator.expected().episodeRunId().equals(stamp.episodeRunId())
                                    &&operator.expected().episodeEpoch()==stamp.episodeEpoch()) {
                                if(DriverOperatorNonRebindOriginals.isRecordedNonRebound(actual))
                                    coverage.requireOperatorNonRebind(borrowed,actual,archive);
                                else DriverOperatorRebindOriginals.requireCoveredBy(borrowed,actual,archive,driver,
                                        stamp.driverVersion(),stamp.episodeEpoch(),stamp.game(),seed.expectedSession().sessionId());
                            }
                            continue; // Operator is not an ordinary ACTION-history recording interface.
                        }
                        if(!(actual.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay))continue;
                        if(!actual.command().before().game().equals(stamp.game())
                                || !actual.command().before().frame().episodeRunId().equals(stamp.episodeRunId())) continue;
                        Optional<? extends ArchivedActionCoverage> original=coverage.originalFor(actual);
                        if(original.isEmpty()) { gaps.add("original_history_row_unavailable:"+actual.command().actionId());continue; }
                        rows.add(validateCoverage(borrowed,actual,original.orElseThrow(),driver,archive));
                    }
                    var known=new DriverSnapshotFacts.Known(driver,stamp,seed.originalHistoryBasis(),rows,seed.auxiliary(),seed.loop(),Optional.empty());
                    DriverStateSnapshot projected=DriverStateAssembler.project(known,lease.snapshot(),Optional.empty());
                    if(projected instanceof DriverStateSnapshot.Incomplete incomplete)
                        for(String reason:incomplete.missingOrUnreconciledFields()) if(!gaps.contains(reason))gaps.add(reason);
                    StrictJson.require(transport.awaitHello(deadline).equals(seed.expectedSession()),"actual held Native hello differs from immutable seed session");
                    var repository=new DriverFactsRepository(known);
                    var producer=new NativeDriverObservationProducer(repository,transport,source,wire -> archive.preserveMaterial(RawJson.fullMaterial(wire)));
                    if(cleanRestart.isPresent())producer.bindCleanRestart(cleanRestart.orElseThrow(),borrowed);
                    if(savedNative.isPresent()) {
                        var retained=savedNative.orElseThrow();
                        retained.original().requireOwner(borrowed,transport,source,archive);
                        retained.original().requireCommitted(borrowed,retained.committed());
                        producer.bindNativeCampaignSaved(retained.original(),retained.committed(),borrowed,archive);
                        retained.original().requireCommitted(borrowed,retained.committed());
                    }
                    if(restoredNative.isPresent())
                        producer.bindNativeCampaignRestored(restoredNative.orElseThrow(),seed,borrowed,archive);
                    var authority=new DriverStateAssembler(actions,repository,producer);
                    var held=new HeldDriverObservationPort(transport,authority,archive::preserveNativeFrame,new DriverObservationAssembler(),retainedFrames);
                    if(kind!=AdoptionKind.UNCLASSIFIED)transport.startHandshake(deadline);
                    Optional<NativeObservationPort.ObservedFrame> firstRaw=resolvedRaw;
                    if(cleanRestart.isPresent()) {
                        var read=transport.readFreshFullState(deadline);
                        if(!(read instanceof org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received received))throw new IOException("clean restart independent native full-state read is unavailable");
                        firstRaw=Optional.of(received.originalFrame());
                    }
                    DriverObservationAssembler.Complete first;
                    if(firstRaw.isPresent()) {
                        var raw=firstRaw.orElseThrow();
                        first=authority.withFrozenRawObservation(raw,borrowed,frozen->{
                            ExactRef original=archive.preserveNativeFrame(raw);var assembler=new DriverObservationAssembler();
                            var fullSnapshot=assembler.projectFull(raw,frozen.facts(),original);
                            var assembled=assembler.assemble(raw,frozen.facts(),original);
                            StrictJson.require(assembled instanceof DriverObservationAssembler.Complete,"actual resolved original observation is incomplete");
                            var complete=(DriverObservationAssembler.Complete)assembled;held.retainVerified(fullSnapshot,complete);return complete;
                        });
                    }else first=held.observe(deadline);
                    StrictJson.require(first.identity().game().equals(stamp.game()) && first.identity().frame().episodeRunId().equals(stamp.episodeRunId())
                            && first.identity().frame().identity().player().equals(driver.session().actorId())
                            && first.source().equals(source) && first.sessionId().equals(seed.expectedSession().sessionId()),"actual first frame crossed adopted seed authority");
                    ExactRef current=archive.materialReferenceOf(RawJson.fullMaterial(driver.encode()));
                    StrictJson.require(current.bytes()==driver.encode().length && current.sha256().equals(stamp.driverSha256()),"current complete Driver was not archived by the real semantic producer");
                    lease.assertCurrent();
                    if(kind==AdoptionKind.UNCLASSIFIED)gaps.add("entry_source_unclassified_no_private_original_or_java_cold_admission");
                    AdoptionStatus status=kind==AdoptionKind.UNCLASSIFIED ? AdoptionStatus.READ_ONLY_UNCLASSIFIED : unresolved ? AdoptionStatus.READ_ONLY_UNRESOLVED
                            : gaps.isEmpty() ? AdoptionStatus.QUALIFICATION_REQUIRED : AdoptionStatus.READ_ONLY_INCOMPLETE_HISTORY;
                    if(kind!=AdoptionKind.UNCLASSIFIED)producer.recordAdoptionObserved(seed.expectedSession(),source);
                    return new Adopted(seed,source,current,repository,authority,producer,held,first,status,gaps);
                } catch(IOException failure) { throw new UncheckedIOException(failure); }
                catch(InterruptedException interrupted) { throw new InterruptedBootstrap(interrupted); }
            });
        } catch(UncheckedIOException failure) { throw failure.getCause(); }
        catch(InterruptedBootstrap interrupted) { throw interrupted.interruption; }
    }

    /**
     * Reconstructs an UNKNOWN same-Game state from captured restart DATA and retained Driver facts.
     * This is observation-only: it does not grant gameplay status, submit actions, or create admissions.
     */
    public static Adopted adoptUnresolvedSameGame(org.xar.ck3.control.application.session.CleanBatchRestart captured,
            DriverSnapshotFacts.Known retained, ExactRef retainedFullDriver, ContinuityStorePort.Session same,
            ActionSnapshotReader actions, NativeGameTransport transport, ActionPorts.OutcomeArchive archive,
            int retainedFrames, Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(captured); Objects.requireNonNull(retained); Objects.requireNonNull(retainedFullDriver);
        Objects.requireNonNull(same); Objects.requireNonNull(actions); Objects.requireNonNull(transport);
        Objects.requireNonNull(archive); Objects.requireNonNull(deadline);
        StrictJson.require(Instant.now().isBefore(deadline), "unresolved same-Game reconstruction deadline expired");
        
        // Authenticate retained Driver bytes via archive
        byte[] driverBytes = archive.withSession(same).loadFullMaterial(retainedFullDriver).bytes();
        StrictJson.require(Arrays.equals(driverBytes, retained.driver().encode()), "retained Driver bytes mismatch");
        StrictJson.require(retainedFullDriver.sha256().equals(DriverJson.sha256(driverBytes)), "retained Driver SHA mismatch");

        List<ActionReceipt> recoveringActions = actions.withFrozen(same, lease -> {
            lease.assertCurrent();
            StrictJson.require(lease.snapshot().originalHistory() instanceof ActionJournal.BoundHistoryBasis basis
                    && basis.originalDriverHistory().equals(retained.originalHistoryBasis()),
                    "unresolved recovery changed the canonical original history basis");
            var pending = lease.snapshot().actions().stream().filter(action -> !action.settled()).toList();
            var recovering = pending.isEmpty() ? lease.snapshot().actions().stream()
                    .filter(action -> action.command().operation().value().equals("private-select-player-lifestyle-stock-focus-v1")
                            && action.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                            && retained.actionRows().stream().anyMatch(row -> row.actionId().equals(action.command().actionId())
                                    && row.durableSequence() == action.sequence()))
                    .toList() : pending;
            StrictJson.require(recovering.size()==1,
                    "same-Game recovery requires one canonical original action, pending or applied before cycle closure");
            for (var action : recovering) {
                StrictJson.require(action.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                        && org.xar.ck3.control.application.action.ActionTransitions.attempt(action.state()).isPresent()
                        && org.xar.ck3.control.application.action.ActionTransitions.composite(action.state()).isEmpty()
                        && action.command().origin().machineId().equals(captured.previousTransport().machineId())
                        && action.command().origin().game().equals(retained.stamp().game())
                        && action.command().sessionId().equals(captured.previousTransport().sessionId())
                        && action.command().source().equals(captured.source()),
                        "unresolved recovery crossed its actual original primitive owner/source");
            }
            lease.assertCurrent();
            return List.copyOf(recovering);
        });

        // Await real new HELLO with same machine/Game PID-birth/session and greater generation
        var current = transport.awaitHello(deadline);
        StrictJson.require(current.machineId().equals(captured.previousTransport().machineId())
                && current.game().equals(captured.previousTransport().game())
                && current.sessionId().equals(captured.previousTransport().sessionId())
                && current.connectionGeneration().compareTo(captured.previousTransport().connectionGeneration()) > 0,
                "unresolved same-Game requires same Game identity and new HELLO generation");
        StrictJson.require(retained.stamp().game().equals(current.game())
                &&retained.driver().session().bridgePid()==current.game().pid()
                &&retained.driver().session().pipeName().equals(transport.pipeName()),
                "unresolved retained Driver belongs to another physical Game or pipe");

        // Rebuild repository, producer, assembler, held observation
        var repository = new DriverFactsRepository(retained);
        var producer = new NativeDriverObservationProducer(repository, transport, captured.source(),
                wire -> archive.preserveMaterial(RawJson.fullMaterial(wire)));
        
        // Bind read-only recovery baseline using captured manifest and retained stamp
        producer.bindReadOnlyRecovery(captured, retained.stamp(), same);
        
        var authority = new DriverStateAssembler(actions, repository, producer);
        var held = new HeldDriverObservationPort(transport, authority, archive::preserveNativeFrame, new DriverObservationAssembler(), retainedFrames);

        // Obtain independent full state on existing transport using fresh operation deadline and only read paths
        transport.startHandshake(deadline);
        var result = transport.readFreshFullState(deadline);
        if (!(result instanceof org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received received)) {
            throw new IOException("unresolved same-Game independent native full-state read unavailable");
        }
        var raw = received.originalFrame();
        StrictJson.require(raw.session().equals(current), "unresolved same-Game received another current connection");

        // Reuse adoptInitialRecovery's real raw observation assembly
        var first = authority.withFrozenRawObservation(raw, same, frozen -> {
            ExactRef nativeOriginal = archive.withSession(same).preserveNativeFrame(raw);
            var assembler = new DriverObservationAssembler();
            var fullSnapshot = assembler.projectFull(raw, frozen.facts(), nativeOriginal);
            var assembled = assembler.assemble(raw, frozen.facts(), nativeOriginal);
            StrictJson.require(assembled instanceof DriverObservationAssembler.Complete, "unresolved same-Game actual resolved original observation is incomplete");
            var complete = (DriverObservationAssembler.Complete) assembled;
            held.retainVerified(fullSnapshot, complete);
            return complete;
        });

        // Verify first frame identity matches retained Driver session
        StrictJson.require(first.identity().game().equals(retained.stamp().game())
                && first.identity().frame().episodeRunId().equals(retained.stamp().episodeRunId())
                && first.identity().frame().identity().player().equals(retained.driver().session().actorId())
                && first.source().equals(captured.source())
                && first.sessionId().equals(current.sessionId()),
                "unresolved same-Game actual first frame crossed adopted seed authority");

        // Preserve Native public revision offset and NATIVE_CAMPAIGN observationVersion
        // (handled by bindReadOnlyRecovery)

        // Keep read-only recovery until the interrupted original batch has closed.
        List<String> reasons = recoveringActions.stream().map(a -> "unfinished_cycle_action:" + a.command().actionId()).toList();
        
        var seed = new Seed(retainedFullDriver, retained.originalHistoryBasis(), retained.stamp().driverVersion(),
                retained.stamp().episodeEpoch(), current, retained.auxiliary(), retained.loop());
        
        var adopted = new Adopted(seed, captured.source(), retainedFullDriver, repository, authority, producer, held, first,
                AdoptionStatus.READ_ONLY_UNRESOLVED, reasons);
        
        return adopted;
    }

    /** Same retained cancellation DATA role as the Journal producer; this grants no Ready or Native submission. */
    private static Optional<ActionReceipt> pendingCancelledLifeCycle(List<ActionReceipt> actions,
            com.fasterxml.jackson.databind.JsonNode pending,ActionPorts.OutcomeArchive originals) {
        if(pending==null||pending.isNull()||actions.isEmpty()||actions.stream().anyMatch(action->!action.settled()))return Optional.empty();
        var actual=originals.loadReceipt(ExactRef.fromJson(pending));
        if(!actions.contains(actual)||actual.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED
                ||actual.visibleGameplay()||actual.eligibleAdvance()
                ||!(actual.state() instanceof org.xar.ck3.control.application.action.ActionState.CompositeSettled settled)
                ||!(settled.settlement() instanceof org.xar.ck3.control.application.action.ActionState.CompositeControlApplied control)
                ||!org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(actual.command().operation().value())
                ||!settled.execution().handlerId().equals(org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER)
                ||!control.observation().semantic().actual().contains(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(
                        new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("progress_status"),"initialization_cancelled")))return Optional.empty();
        var children=settled.execution().children().stream().map(bound->actions.stream()
                .filter(child->child.command().actionId().equals(bound.actionId())&&child.bodySha256().equals(bound.bodySha256()))
                .findFirst().orElseThrow()).toList();
        org.xar.ck3.control.application.advance.LifeAdvanceComposite.requireCancelledInitialization(
                actual.command(),settled.execution(),control.observation(),children);
        return Optional.of(actual);
    }

    /** Reattaches a settled dirty Driver using its new HELLO and independent physical read. */
    public static Adopted adoptSettledSameGame(
            org.xar.ck3.control.application.session.ContinuityBatchJournal.SettledSameGameData data,
            ContinuityStorePort.Session same,ActionSnapshotReader actions,NativeGameTransport transport,
            ActionPorts.OutcomeArchive archive,BorrowedSessionReader currentSession,int retainedFrames,Instant deadline)
            throws IOException,InterruptedException {
        return adoptSameGameHistory(data,same,actions,transport,archive,currentSession,retainedFrames,deadline,false);
    }

    /** Reattaches retained Life action or pending-cycle recovery with its latest Driver, without granting Ready. */
    public static Adopted adoptUnresolvedSameGame(
            org.xar.ck3.control.application.session.ContinuityBatchJournal.UnresolvedSameGameData data,
            ContinuityStorePort.Session same,ActionSnapshotReader actions,NativeGameTransport transport,
            ActionPorts.OutcomeArchive archive,BorrowedSessionReader currentSession,int retainedFrames,Instant deadline)
            throws IOException,InterruptedException {
        if (data.retainedHistory().isPresent())
            return adoptSameGameHistory(data.retainedHistory().orElseThrow(),same,actions,transport,archive,currentSession,retainedFrames,deadline,true);
        return adoptUnresolvedSameGame(data.capturedManifest(),data.retainedFacts(),data.retainedFullDriver(),
                same,actions,transport,archive,retainedFrames,deadline);
    }

    private static Adopted adoptSameGameHistory(
            org.xar.ck3.control.application.session.ContinuityBatchJournal.SettledSameGameData data,
            ContinuityStorePort.Session same,ActionSnapshotReader actions,NativeGameTransport transport,
            ActionPorts.OutcomeArchive archive,BorrowedSessionReader currentSession,int retainedFrames,Instant deadline,
            boolean isolatedLife) throws IOException,InterruptedException {
        Objects.requireNonNull(data);Objects.requireNonNull(same);Objects.requireNonNull(actions);
        Objects.requireNonNull(transport);Objects.requireNonNull(archive);Objects.requireNonNull(currentSession);
        Objects.requireNonNull(deadline);
        var retained=data.retainedFacts();var old=data.previousTransport();
        var current=transport.awaitHello(deadline);
        StrictJson.require(current.machineId().equals(old.machineId())&&current.game().equals(old.game())
                &&current.sessionId().equals(old.sessionId())
                &&current.connectionGeneration().compareTo(old.connectionGeneration())>0,
                "settled continuation requires the same Game PID/birth and a new actual HELLO generation");
        StrictJson.require(retained.stamp().game().equals(current.game())
                &&retained.driver().session().bridgePid()==current.game().pid()
                &&retained.driver().session().pipeName().equals(transport.pipeName()),
                "settled retained Driver belongs to another physical Game or pipe");
        var finalizationHead = same.head().state();
        var pendingLifeCycle=isolatedLife?same.head().state().toJson()
                .path(WriterContracts.ORDINARY_CYCLE_FIELD).get("pending_receipt"):null;
        actions.withFrozen(same,lease->{
            StrictJson.require(lease.snapshot().originalHistory() instanceof ActionJournal.BoundHistoryBasis basis
                    &&basis.originalDriverHistory().equals(retained.originalHistoryBasis()),
                    "same-Game continuation cannot replace its actual original history");
            if (isolatedLife) {
                StrictJson.require(new java.util.HashSet<>(lease.snapshot().actions()).equals(new java.util.HashSet<>(data.settledActions()))
                        && (org.xar.ck3.control.application.session.ContinuityBatchJournal
                                .readOnlyLifeRecoveryRoot(lease.snapshot().actions()).isPresent()
                            || org.xar.ck3.control.application.session.ContinuityBatchJournal
                                .readOnlySaveRecoveryRoot(lease.snapshot().actions()).isPresent()
                            || pendingCancelledLifeCycle(lease.snapshot().actions(),pendingLifeCycle,archive.withSession(same)).isPresent()
                            || org.xar.ck3.control.application.session.ContinuityBatchJournal
                                .readOnlySaveFinalizationRoot(finalizationHead,new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(old.machineId(),old.game(),old.sessionId()),lease.snapshot().actions(),archive.withSession(same)).isPresent()),
                        "read-only Life/SAVE adoption retains the complete canonical action set and exact pending recovery role");
            } else {
                StrictJson.require(lease.snapshot().actions().stream().allMatch(ActionReceipt::settled),
                        "settled continuation cannot replay an unresolved original action");
            }
            lease.assertCurrent();return null;
        });
        var repository=new DriverFactsRepository(retained);
        var producer=new NativeDriverObservationProducer(repository,transport,data.source(),
                wire->borrowedArchive(archive,currentSession).preserveMaterial(RawJson.fullMaterial(wire)));
        producer.bindSettledSameGame(data,same);
        var authority=new DriverStateAssembler(actions,repository,producer);
        var held=new HeldDriverObservationPort(transport,authority,
                frame->borrowedArchive(archive,currentSession).preserveNativeFrame(frame),
                new DriverObservationAssembler(),retainedFrames);
        transport.startHandshake(deadline);
        var result=transport.readFreshFullState(deadline);
        if(!(result instanceof org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received received))
            throw new IOException("settled continuation independent native full-state read unavailable");
        var raw=received.originalFrame();
        StrictJson.require(raw.session().equals(current),"settled continuation received another current connection");
        var first=authority.withFrozenRawObservation(raw,same,frozen->{
            ExactRef nativeOriginal=archive.withSession(same).preserveNativeFrame(raw);
            var assembler=new DriverObservationAssembler();
            var full=assembler.projectFull(raw,frozen.facts(),nativeOriginal);
            var projected=assembler.assemble(raw,frozen.facts(),nativeOriginal);
            StrictJson.require(projected instanceof DriverObservationAssembler.Complete,
                    "settled continuation actual physical Driver projection is incomplete");
            var complete=(DriverObservationAssembler.Complete)projected;
            held.retainVerified(full,complete);return complete;
        });
        StrictJson.require(first.identity().game().equals(retained.stamp().game())
                &&first.identity().frame().episodeRunId().equals(retained.stamp().episodeRunId())
                &&first.identity().frame().identity().player().equals(retained.driver().session().actorId())
                &&first.identity().observationVersion()==data.latestObservedFrame().observationVersion()
                &&first.identity().frame().identity().dateRaw().compareTo(data.latestObservedFrame().frame().identity().dateRaw())>=0
                &&first.identity().frame().identity().nativeRevision().compareTo(data.latestObservedFrame().frame().identity().nativeRevision())>=0
                &&first.identity().frame().revision().compareTo(data.latestObservedFrame().frame().revision())>=0
                &&first.source().equals(data.source())&&first.sessionId().equals(current.sessionId()),
                "settled continuation physical read crossed the retained Game/episode/actor or regressed its latest observation");
        var seed=new Seed(data.retainedFullDriver(),retained.originalHistoryBasis(),retained.stamp().driverVersion(),
                retained.stamp().episodeEpoch(),current,retained.auxiliary(),retained.loop());
        var adopted=new Adopted(seed,data.source(),data.retainedFullDriver(),repository,authority,producer,held,first,
                isolatedLife ? AdoptionStatus.READ_ONLY_UNRESOLVED : AdoptionStatus.QUALIFICATION_REQUIRED,
                isolatedLife ? List.of("retained_life_requires_read_only_action_or_cycle_recovery") : List.of());
        if (!isolatedLife) {
            adopted.settledSameGame=data;
            producer.recordAdoptionObserved(current,data.source());
        }
        return adopted;
    }

    /** Resumes only the canonical first entry on this living Game; it neither starts nor initializes a campaign. */
    public static Adopted adoptInitialRecovery(FreshGameplayEntryAuthority.RecoveryAdmission actual,
            ContinuityStorePort.Session same,ActionSnapshotReader actions,NativeGameTransport transport,G2Source source,
            ActionPorts.OutcomeArchive archive,int retainedFrames,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(deadline);
        return adoptInitialRecovery(actual,same,actions,transport,source,archive,retainedFrames,()->deadline);
    }

    public static Adopted adoptInitialRecovery(FreshGameplayEntryAuthority.RecoveryAdmission actual,
            ContinuityStorePort.Session same,ActionSnapshotReader actions,NativeGameTransport transport,G2Source source,
            ActionPorts.OutcomeArchive archive,int retainedFrames,java.util.function.Supplier<Instant> deadlineSupplier)throws IOException,InterruptedException {
        Objects.requireNonNull(actual);Objects.requireNonNull(source);actual.requireCurrent(same);actual.requireArchive(archive);
        var deadline = Objects.requireNonNull(Objects.requireNonNull(deadlineSupplier).get());
        StrictJson.require(Instant.now().isBefore(deadline),"initial recovery deadline expired");
        var entry=actual.entry();var original=actual.facts();var current=transport.awaitHello(deadline);
        var captured=actual.initialNoDispatchRecovery().flatMap(value->value.capturedManifest());
        var fullDriver=actual.initialNoDispatchRecovery().flatMap(value->value.retainedFullDriver())
                .orElseGet(()->captured.map(value->value.fullDriver()).orElse(entry.fullDriver()));
        var previousConnection=captured.map(value->value.previousTransport().connectionGeneration()).orElse(entry.connectionGeneration());
        var minimumNative=captured.map(value->value.nativeRevision()).orElse(entry.nativeRevision());
        StrictJson.require(current.machineId().equals(entry.machineId())&&current.game().equals(entry.game())
                &&current.sessionId().equals(entry.sessionId())&&source.machineId().equals(current.machineId())
                &&current.connectionGeneration().compareTo(previousConnection)>0,
                "initial recovery requires the same Game and a new actual HELLO generation");
        var bound=archive.withSession(same);
        StrictJson.require(Arrays.equals(bound.loadFullMaterial(fullDriver).bytes(),original.driver().encode())
                &&original.driver().session().pipeName().equals(transport.pipeName()),
                "initial recovery changed the complete original Driver or held pipe");
        var known=new DriverSnapshotFacts.Known(original.driver(),original.stamp(),original.originalHistoryBasis(),
                original.actionRows(),original.auxiliary(),original.loop(),Optional.empty());
        var repository=new DriverFactsRepository(known);
        var producer=new NativeDriverObservationProducer(repository,transport,source,
                wire->borrowedArchive(archive,actual::activeSession).preserveMaterial(RawJson.fullMaterial(wire)));
        producer.bindInitialRecovery(actual,same);
        var authority=new DriverStateAssembler(actions,repository,producer);
        var held=new HeldDriverObservationPort(transport,authority,
                frame->borrowedArchive(archive,actual::activeSession).preserveNativeFrame(frame),
                new DriverObservationAssembler(),retainedFrames);
        var result=transport.readFreshFullState(deadline);
        if(!(result instanceof org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received received))
            throw new IOException("initial recovery independent native full-state read unavailable");
        var raw=received.originalFrame();
        StrictJson.require(raw.session().equals(current),"initial recovery received another current connection");
        var first=authority.withFrozenRawObservation(raw,same,frozen->{
            ExactRef nativeOriginal=archive.withSession(same).preserveNativeFrame(raw);var assembler=new DriverObservationAssembler();
            var full=assembler.projectFull(raw,frozen.facts(),nativeOriginal);var projected=assembler.assemble(raw,frozen.facts(),nativeOriginal);
            StrictJson.require(projected instanceof DriverObservationAssembler.Complete,"initial recovery actual full projection incomplete");
            var complete=(DriverObservationAssembler.Complete)projected;held.retainVerified(full,complete);return complete;
        });
        var frame=first.identity().frame();var nativeState=DriverObservationAssembler.originalNativeState(raw);
        var expectedActor=captured.isPresent()?original.driver().session().actorId():java.math.BigInteger.valueOf(entry.actorId());
        var expectedEpisode=captured.isPresent()?original.driver().session().episodeRunId():entry.episodeId();
        var expectedDate=java.math.BigInteger.valueOf(captured.map(m->m.dateRaw()).orElse(entry.dateRaw()));
        StrictJson.require(frame.identity().player().equals(expectedActor)
                &&frame.episodeRunId().equals(expectedEpisode)
                &&(captured.isPresent()?frame.identity().dateRaw().compareTo(expectedDate)>=0:frame.identity().dateRaw().equals(expectedDate))
                &&frame.identity().nativeRevision().compareTo(minimumNative)>=0
                &&OpportunityJson.bool(nativeState.get("paused"),"paused")&&OpportunityJson.bool(nativeState.get("map_ready"),"map_ready"),
                "initial recovery changed actor/date, regressed native revision, or moving map");
        actual.requireCurrent(same);producer.recordAdoptionObserved(current,source);
        var seed=new Seed(fullDriver,original.originalHistoryBasis(),original.stamp().driverVersion(),
                original.stamp().episodeEpoch(),current,original.auxiliary(),original.loop());
        var adopted=new Adopted(seed,source,fullDriver,repository,authority,producer,held,first,AdoptionStatus.QUALIFICATION_REQUIRED,List.of());
        adopted.initialRecovery=actual;return adopted;
    }

    /** Joins the actual first-map packet to the original Java Driver owners; no legacy entry receipt is required. */
    public static Adopted fresh(org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received received,
            InitialDriverState.Produced initial,org.xar.ck3.control.platform.ManagedGameSession game,
            org.xar.ck3.control.continuity.writer.ContinuityWriter writer,
            org.xar.ck3.control.continuity.writer.NativeOutcomeArchive archive,ActionSnapshotReader actions,
            G2Source source,int retainedFrames,Instant deadline)throws IOException {
        Objects.requireNonNull(received);Objects.requireNonNull(initial);Objects.requireNonNull(game);
        Objects.requireNonNull(writer);Objects.requireNonNull(archive);Objects.requireNonNull(actions);Objects.requireNonNull(source);
        var actual=received.originalFrame();var transport=game.nativeTransport();
        StrictJson.require(archive.writer()==writer&&actual.session().game().equals(game.generation())
                &&actual.session().sessionId().equals(game.sessionId())
                &&transport.diagnostics().session().filter(actual.session()::equals).isPresent(),
                "fresh Driver must retain its actual Game, held connection and writer");
        return writer.locked(same->{
            byte[] bytes=initial.driver().encode();
            ExactRef full=archive.preserveArtifact(same,bytes,Math.min(DriverCheckpointStore.MAX_DRIVER_BYTES,WriterContracts.MAX_PIN_BYTES));
            var stamp=new DriverSnapshotFacts.Stamp(0,0,game.generation(),initial.driver().session().episodeRunId(),DriverJson.sha256(bytes));
            var known=new DriverSnapshotFacts.Known(initial.driver(),stamp,full,List.of(),initial.auxiliary(),Optional.empty(),Optional.empty());
            var repository=new DriverFactsRepository(known);
            var producer=new NativeDriverObservationProducer(repository,transport,source,wire->{
                try{return archive.preserveArtifact(writer.borrowedSession(),wire,Math.min(DriverCheckpointStore.MAX_DRIVER_BYTES,WriterContracts.MAX_PIN_BYTES));}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            var authority=new DriverStateAssembler(actions,repository,producer);
            var observations=new HeldDriverObservationPort(transport,authority,frame->{
                try{return archive.withSession(writer.borrowedSession()).preserveNativeFrame(frame);}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            },new DriverObservationAssembler(),retainedFrames);
            var first=authority.withFrozenRawObservation(actual,same,frozen->{
                ExactRef original=archive.withSession(same).preserveNativeFrame(actual);
                var assembler=new DriverObservationAssembler();
                var fullSnapshot=assembler.projectFull(actual,frozen.facts(),original);
                var assembled=assembler.assemble(actual,frozen.facts(),original);
                StrictJson.require(assembled instanceof DriverObservationAssembler.Complete,"actual first-map observation is incomplete");
                var complete=(DriverObservationAssembler.Complete)assembled;
                observations.retainVerified(fullSnapshot,complete);return complete;
            });
            producer.recordAdoptionObserved(actual.session(),source);
            var seed=new Seed(full,full,0,0,actual.session(),initial.auxiliary(),Optional.empty());
            return new Adopted(seed,source,full,repository,authority,producer,observations,first,AdoptionStatus.FRESH_OBSERVED,List.of());
        });
    }

    /** The original new-game bridge retains its already committed provisional owner; it does not mint entry authority. */
    static Adopted initial(InitialDriverBootstrap.Staged staged,ContinuityStorePort.Session borrowed,
            WriterContracts.Prepared prepared,WriterContracts.Receipt receipt)throws IOException {
        Objects.requireNonNull(staged);staged.requireCommitted(borrowed,prepared,receipt);
        Seed seed=staged.seed();
        StrictJson.require(seed.fullDriver().equals(seed.originalHistoryBasis()),"initial complete Driver is its actual canonical history basis");
        staged.producer().recordAdoptionObserved(seed.expectedSession(),staged.source());
        return new Adopted(seed,staged.source(),seed.fullDriver(),staged.repository(),staged.authority(),
                staged.producer(),staged.observations(),staged.frame(),AdoptionStatus.QUALIFICATION_REQUIRED,List.of());
    }

    private static DriverSnapshotFacts.ActionRow validateCoverage(ContinuityStorePort.Session same,ActionReceipt actual,ArchivedActionCoverage proof,
            DriverStateSnapshot.Complete driver,ActionPorts.OutcomeArchive archive)throws IOException {
        var receipt=archive.loadReceipt(proof.receipt());
        StrictJson.require(archive.receiptReferenceOf(receipt).equals(proof.receipt())
                && Arrays.equals(ActionReceiptCodec.encodeReceipt(receipt,archive),ActionReceiptCodec.encodeReceipt(actual,archive)),
                "coverage does not reference this actual canonical settled receipt");
        if(proof instanceof ArchivedCanonicalOnly canonical) {
            DriverActionHistoryCodec.verifyCanonicalOnly(same,actual,canonical.originalSource(),archive);
            return new DriverSnapshotFacts.ActionRow(actual.command().actionId(),actual.bodySha256(),actual.sequence(),
                    new DriverSnapshotFacts.CanonicalOnly(canonical.originalSource()));
        }
        var legacy=(ArchivedHistoryRow)proof;
        StrictJson.require(legacy.historyIndex()<=driver.commandHistory().size(),"legacy coverage ordinal exceeds complete original branch");
        byte[] original=archive.loadFullMaterial(legacy.originalRow()).bytes();
        StrictJson.require(legacy.originalRow().bytes()==original.length&&legacy.originalRow().sha256().equals(DriverJson.sha256(original)),"archived original history row differs");
        var expected=DriverJson.object(driver.commandHistory().get(Math.toIntExact(legacy.historyIndex()-1)).originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
        var archived=DriverJson.object(original,DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(expected.equals(archived)&&OpportunityJson.text(archived.get("command"),"command").equals(actual.command().operation().value())
                &&archived.get("ok") instanceof OpportunityJson.Bool,"complete original history row does not project the actual original command");
        if(archived.members().containsKey(DriverActionHistoryCodec.SOURCE_FIELD))DriverActionHistoryCodec.verifyLegacy(same,actual,archived,archive);
        // Historical specialized SAVE/DEATH rows retain their original producer's boolean.
        // Python normal return (including proposal_submitted) is not globally equivalent to APPLIED_CONFIRMED.
        return new DriverSnapshotFacts.ActionRow(actual.command().actionId(),actual.bodySha256(),actual.sequence(),legacy.historyIndex(),legacy.originalRow());
    }
    private static byte[] readExact(ExactArtifactReader reader,ExactRef expected,int maximum) throws IOException {
        StrictJson.require(expected.bytes()>0 && expected.bytes()<=maximum,"original artifact exceeds qualified read bound");
        byte[] actual=reader.read(expected,maximum);
        StrictJson.require(actual!=null && actual.length==expected.bytes() && expected.sha256().equals(DriverJson.sha256(actual)),"immutable original artifact bytes/SHA differ");
        return actual;
    }
    private static final class InterruptedBootstrap extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final InterruptedException interruption;
        InterruptedBootstrap(InterruptedException interrupted) { super(interrupted);interruption=interrupted; }
    }
}
