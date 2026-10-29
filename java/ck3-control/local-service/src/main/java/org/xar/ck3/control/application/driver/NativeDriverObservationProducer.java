package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.service.root.RootFrozenRunProfile;
import org.xar.ck3.control.service.root.RootLegacyResumeRuntime;
import org.xar.ck3.control.service.root.RootRestoreMaterials;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.PublicRevision;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnosticsCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Concrete facts producer on the same held Native session and actual imported/versioned Driver owner. */
public final class NativeDriverObservationProducer implements DriverObservationFacts.Reader {
    /** Current transport-owned values never inherit an older Driver auxiliary diagnostic. */
    private static final java.util.Set<String> LIVE_DIAGNOSTICS=java.util.Set.of("pipe_name","connected","bridge_pid","connection_generation","hello",
            "last_heartbeat","last_pong","last_error","last_snapshot_publish_diagnostic");
    @FunctionalInterface public interface SemanticEvidencePort { ExactRef preserve(byte[] actualFacts); }
    private final DriverFactsRepository repository;
    private NativeGameTransport transport;
    private G2Source source;
    private SemanticEvidencePort archive;
    private NativeObservationPort.TransportSession acceptedSession;
    private NativeRequestChronology.Event lastProjectedReceipt;
    private BigInteger transportRevisionOffset=BigInteger.ZERO;
    private BigInteger publicRevision=BigInteger.ZERO;
    private boolean cleanNativeCampaign;
    private String archivedDriverSha256;
    private ExactRef archivedDriver;
    private String nextEpisodeEvent;
    private NativeCampaignFixture nativeCampaignFixture;
    private SavedNativeCampaign savedNativeCampaign;
    private RestoredNativeCampaign restoredNativeCampaign;
    private record NativeCampaignFixture(InitialDriverBootstrap.Staged stage,ManagedGameSession game,
            G2Source source,org.xar.ck3.control.continuity.writer.NativeOutcomeArchive archive,
            InitialEpisodePolicy policy,PreparedFixture prepared) {
        void requireCurrent(NativeDriverObservationProducer owner)throws IOException {
            var same=archive.writer().borrowedSession();
            stage.requireNativeCampaignObservationOwner(same,game,source);
            policy.requireFixtureProjection(prepared);
            StrictJson.require(stage.policy()==policy&&stage.repository()==owner.repository
                    &&game.nativeTransport()==owner.transport&&source.equals(owner.source),
                    "native campaign facts crossed its actual private Stage/Driver/transport/source");
        }
    }
    private record SavedNativeCampaign(RootFrozenRunProfile.FrozenRunProfile frozen,ManagedGameSession game,
            G2Source source,NativeOutcomeArchive archive,long committedSequence,String committedDigest) {
        void requireCurrent(NativeDriverObservationProducer owner)throws IOException {
            var same=archive.writer().borrowedSession();archive.writer().requireSession(same);
            same.requireHistoricalHead(committedSequence,committedDigest);
            game.verify();frozen.requireCurrent(game.launchPlan(),java.time.Clock.systemUTC());
            for(Class<?> actual:List.of(NativeDriverObservationProducer.class,NativeCampaignProjection.class,
                    DriverObservationAssembler.class,org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier.class,
                    DriverBootstrap.class,RootLegacyResumeRuntime.class,RootFrozenRunProfile.class,InitialEpisodePolicy.class))
                game.launchPlan().sources().requireLoadedClass(actual);
            frozen.requireExplicitNativeCampaign();frozen.initialPolicy().requireSavedProjection(game.launchPlan());
            StrictJson.require(game.nativeTransport()==owner.transport&&source.equals(owner.source)
                    &&frozen.fixture().isEmpty()&&frozen.lifecycleBinding().isEmpty(),
                    "saved native campaign facts crossed the genuine committed Game/source/plan");
        }
    }
    /**
     * Only Bootstrap's verified private original migration may select the Saved projection.
     * Public null lifecycle, a JSON marker or an arbitrary Frozen DATA value cannot bind this producer.
     */
    synchronized void bindNativeCampaignSaved(RootLegacyResumeRuntime.Prepared actual,WriterContracts.Receipt committed,
            ContinuityStorePort.Session same,ActionPorts.OutcomeArchive sameArchive)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(committed);Objects.requireNonNull(same);Objects.requireNonNull(sameArchive);
        StrictJson.require(nativeCampaignFixture==null&&savedNativeCampaign==null&&restoredNativeCampaign==null&&acceptedSession==null,
                "saved projection must bind once before the sole public revision producer observes");
        StrictJson.require(sameArchive instanceof NativeOutcomeArchive,"saved projection requires the actual long-lived Native archive");
        var archive=(NativeOutcomeArchive)sameArchive;archive.writer().requireSession(same);
        actual.requireOwner(same,transport,source,sameArchive);actual.requireCommitted(same,committed);
        var frozen=actual.requireSavedNativeProjection(same,committed);
        var game=actual.requireSavedNativeGame(same,committed);
        frozen.requireExplicitNativeCampaign();frozen.initialPolicy().requireSavedProjection(game.launchPlan());
        StrictJson.require(game.nativeTransport()==transport&&frozen.fixture().isEmpty()&&frozen.lifecycleBinding().isEmpty(),
                "saved projection requires the genuine same Game and explicit Saved null provenance");
        var seed=actual.seed(same,committed);var original=actual.originalNative();
        StrictJson.require(seed.expectedSession().equals(original.session())&&game.generation().equals(original.session().game())
                &&source.machineId().equals(original.session().machineId())
                &&transport.diagnostics().session().filter(original.session()::equals).isPresent(),
                "saved projection crossed the verified canonical migration's actual Native session");
        repository.locked(state->{
            StrictJson.require(state instanceof DriverSnapshotFacts.Known,"actual migrated full Driver unavailable");
            var known=(DriverSnapshotFacts.Known)state;
            StrictJson.require(known.driver().successionLifecycle() instanceof org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue
                    &&known.stamp().driverSha256().equals(seed.fullDriver().sha256())
                    &&known.originalHistoryBasis().equals(seed.originalHistoryBasis())
                    &&known.stamp().driverVersion()==seed.driverVersion()&&known.stamp().episodeEpoch()==seed.episodeEpoch()
                    &&known.stamp().game().equals(game.generation()),"saved projection must retain its actual canonical migrated Driver/history/version");
            return null;
        });
        savedNativeCampaign=new SavedNativeCampaign(frozen,game,source,archive,committed.head().sequence(),
                ContinuityJson.digest(committed.head().toJson()));
        savedNativeCampaign.requireCurrent(this);
    }
    private static final class RestoredNativeCampaign {
        final RootRestoreMaterials.ColdAdoption original;
        final DriverBootstrap.Seed originalSeed;
        final RootFrozenRunProfile.FrozenRunProfile originalFrozen;
        final ManagedGameSession replacement;
        final G2Source source;
        final NativeOutcomeArchive archive;
        WriterContracts.Receipt committed;
        DriverBootstrap.Seed publishedSeed;
        RestoredNativeCampaign(RootRestoreMaterials.ColdAdoption original,DriverBootstrap.Seed originalSeed,
                RootFrozenRunProfile.FrozenRunProfile originalFrozen,ManagedGameSession replacement,
                G2Source source,NativeOutcomeArchive archive) {
            this.original=original;this.originalSeed=originalSeed;this.originalFrozen=originalFrozen;
            this.replacement=replacement;this.source=source;this.archive=archive;
        }
        void requireCurrent(NativeDriverObservationProducer owner)throws IOException {
            var same=archive.writer().borrowedSession();archive.writer().requireSession(same);
            replacement.verify();originalFrozen.requireExplicitNativeCampaign();
            // The Frozen belongs to the original run. A replacement Saved plan is a different private object.
            StrictJson.require(replacement.nativeTransport()==owner.transport&&source.equals(owner.source),
                    "restored native campaign observation crossed its actual replacement Game/source");
            for(Class<?> actual:List.of(NativeDriverObservationProducer.class,NativeCampaignProjection.class,
                    DriverObservationAssembler.class,org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier.class,
                    DriverBootstrap.class,RootRestoreMaterials.class,RootFrozenRunProfile.class,InitialEpisodePolicy.class,
                    org.xar.ck3.control.service.root.RootRestoreAdapters.class,org.xar.ck3.control.service.root.RootRestoreMaterialFactory.class))
                replacement.launchPlan().sources().requireLoadedClass(actual);
            if(committed==null)original.requireCurrent(same,originalSeed,owner.transport);
            else same.requireHistoricalHead(committed.head().sequence(),ContinuityJson.digest(committed.head().toJson()));
        }
    }
    /**
     * Historical projection provenance only. This compares the identical original private policy/Frozen
     * with this producer's real binding; the old Game may already have been retired by the real restore.
     */
    public synchronized void requireNativeCampaignProjectionOrigin(RootFrozenRunProfile.FrozenRunProfile original)throws IOException {
        Objects.requireNonNull(original);original.requireExplicitNativeCampaign();
        boolean same=nativeCampaignFixture!=null&&nativeCampaignFixture.policy()==original.initialPolicy()
                &&original.fixture().filter(value->value==nativeCampaignFixture.prepared()).isPresent()
                ||savedNativeCampaign!=null&&savedNativeCampaign.frozen()==original
                ||restoredNativeCampaign!=null&&restoredNativeCampaign.originalFrozen==original;
        StrictJson.require(same,"native campaign origin must be this producer's identical actual private projection source");
    }
    /** Warm physical replacement uses its actual captured restore source, never a cold legacy Prepared. */
    synchronized void bindNativeCampaignRestored(RootRestoreMaterials.ColdAdoption actual,DriverBootstrap.Seed exact,
            ContinuityStorePort.Session same,ActionPorts.OutcomeArchive sameArchive)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(exact);Objects.requireNonNull(same);Objects.requireNonNull(sameArchive);
        StrictJson.require(nativeCampaignFixture==null&&savedNativeCampaign==null&&restoredNativeCampaign==null&&acceptedSession==null,
                "restored projection must bind once before its sole public revision producer observes");
        StrictJson.require(sameArchive instanceof NativeOutcomeArchive,"restored projection requires the actual long-lived Native archive");
        var archive=(NativeOutcomeArchive)sameArchive;archive.writer().requireSession(same);
        actual.requireCurrent(same,exact,transport);
        var frozen=actual.requireNativeCampaignProjection(same,exact,transport);
        var game=actual.requireNativeCampaignGame(same,exact,transport);
        frozen.requireExplicitNativeCampaign();
        StrictJson.require(game.nativeTransport()==transport&&game.generation().equals(exact.expectedSession().game())
                &&source.machineId().equals(exact.expectedSession().machineId())
                &&transport.diagnostics().session().filter(exact.expectedSession()::equals).isPresent(),
                "restored projection crossed its actual private captured Game/transport/source");
        repository.locked(state->{
            StrictJson.require(state instanceof DriverSnapshotFacts.Known,"actual provisional restored Driver unavailable");
            var known=(DriverSnapshotFacts.Known)state;
            StrictJson.require(known.driver().successionLifecycle() instanceof org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue
                    &&known.stamp().driverSha256().equals(exact.fullDriver().sha256())
                    &&known.originalHistoryBasis().equals(exact.originalHistoryBasis())
                    &&known.stamp().driverVersion()==exact.driverVersion()&&known.stamp().episodeEpoch()==exact.episodeEpoch()
                    &&known.stamp().game().equals(game.generation()),"restored projection crossed its actual captured complete Driver/history/version");
            return null;
        });
        restoredNativeCampaign=new RestoredNativeCampaign(actual,exact,frozen,game,source,archive);
        restoredNativeCampaign.requireCurrent(this);
    }
    /** Only Bootstrap's actual committed/CAS-published private Stage can cross the precommit source boundary. */
    synchronized void promoteNativeCampaignRestored(DriverBootstrap.Staged actual,DriverBootstrap.Seed finalSeed,
            WriterContracts.Prepared prepared,WriterContracts.Receipt receipt,ContinuityStorePort.Session same)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(finalSeed);Objects.requireNonNull(prepared);
        Objects.requireNonNull(receipt);Objects.requireNonNull(same);
        var retained=Objects.requireNonNull(restoredNativeCampaign,"actual restored native campaign binding unavailable");
        retained.archive.writer().requireSession(same);
        actual.requireNativeCampaignProjectionPublished(this,retained.original,same,finalSeed,prepared,receipt);
        same.requireCommitted(prepared,receipt);
        repository.locked(state->{
            StrictJson.require(state instanceof DriverSnapshotFacts.Known,"actual published restored Driver unavailable");
            var known=(DriverSnapshotFacts.Known)state;
            StrictJson.require(known.stamp().driverSha256().equals(finalSeed.fullDriver().sha256())
                    &&known.stamp().driverVersion()==finalSeed.driverVersion()&&known.stamp().episodeEpoch()==finalSeed.episodeEpoch()
                    &&known.originalHistoryBasis().equals(finalSeed.originalHistoryBasis())
                    &&known.driver().successionLifecycle() instanceof org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue,
                    "restored projection promotion requires the actual complete published Driver");
            return null;
        });
        if(retained.committed!=null)StrictJson.require(retained.committed==receipt&&retained.publishedSeed.equals(finalSeed),
                "restored projection cannot replace its original committed publication");
        else {retained.committed=receipt;retained.publishedSeed=finalSeed;}
        retained.requireCurrent(this);
    }
    /** Actual late ReboundOrigin may prove historical provenance; it grants no current Native or Ready permission. */
    public synchronized void requireNativeCampaignRestoredProjection(ContinuityStorePort.Session same,
            RestoreCheckpointService.ReboundOrigin actual)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(actual);
        var retained=Objects.requireNonNull(restoredNativeCampaign,"actual restored native campaign binding unavailable");
        retained.archive.writer().requireSession(same);
        actual.requireOriginal(same);var evidence=actual.evidence();
        StrictJson.require(retained.committed!=null&&evidence.attachmentSequence()==retained.committed.head().sequence()
                &&evidence.attachmentHeadDigest().equals(ContinuityJson.digest(retained.committed.head().toJson()))
                &&evidence.attachmentEventIdentity().equals(retained.committed.eventIdentity())
                &&evidence.restoredOwner().game().equals(retained.replacement.generation())
                &&evidence.restoredOwner().sessionId().equals(retained.publishedSeed.expectedSession().sessionId())
                &&evidence.restoredConnectionGeneration().equals(retained.publishedSeed.expectedSession().connectionGeneration().toString())
                &&evidence.source().equals(retained.source)
                &&evidence.originalRestoredSemantic().frame().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                &&evidence.originalRestoredSemantic().originalDriver().sha256().equals(retained.publishedSeed.fullDriver().sha256())
                &&evidence.originalHistoryBasis().equals(retained.publishedSeed.originalHistoryBasis()),
                "restored native campaign provenance crossed its actual committed binding/Game/source/Driver");
        retained.requireCurrent(this);actual.requireOriginal(same);
    }

    /** Explicit first-map fixture binding. The public profile number or a JSON marker cannot create this custody. */
    public synchronized void bindNativeCampaignFixture(InitialDriverBootstrap.Staged stage,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ManagedGameSession sameGame,G2Source sameSource,
            org.xar.ck3.control.continuity.writer.NativeOutcomeArchive sameArchive,InitialEpisodePolicy samePolicy,
            NativeFreshSnapshotPort.Received firstRead)throws IOException {
        Objects.requireNonNull(stage);Objects.requireNonNull(same);Objects.requireNonNull(sameGame);
        Objects.requireNonNull(sameSource);Objects.requireNonNull(sameArchive);Objects.requireNonNull(samePolicy);Objects.requireNonNull(firstRead);
        StrictJson.require(nativeCampaignFixture==null&&savedNativeCampaign==null&&restoredNativeCampaign==null&&acceptedSession==null,"fixture projection must bind once before the sole public revision producer observes");
        sameArchive.writer().requireSession(same);stage.requireFixtureProjectionOwner(same,sameGame,sameSource);
        var prepared=samePolicy.explicitFixture().orElseThrow();samePolicy.requireFixtureProjection(prepared);
        StrictJson.require(stage.policy()==samePolicy&&stage.repository()==repository&&sameGame.nativeTransport()==transport
                &&sameSource.equals(source)&&stage.latestFixtureRead()==firstRead,"first fixture projection crossed its actual private owner or original READ");
        NativeFreshSnapshotPort.verifyOriginal(firstRead.acknowledgement(),firstRead.originalFrame(),firstRead.snapshotReceived());
        StrictJson.require(firstRead.originalFrame().session().game().equals(sameGame.generation())
                &&transport.diagnostics().session().filter(firstRead.originalFrame().session()::equals).isPresent(),"fixture projection READ has another actual held Game/session");
        nativeCampaignFixture=new NativeCampaignFixture(stage,sameGame,sameSource,sameArchive,samePolicy,prepared);
        nativeCampaignFixture.requireCurrent(this);
    }

    public static final long OBSERVATION_CONTRACT_VERSION=DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION;
    public NativeDriverObservationProducer(DriverFactsRepository sameRepository,NativeGameTransport sameHeldTransport,
            G2Source actualSource,SemanticEvidencePort actualArchive) {
        repository=Objects.requireNonNull(sameRepository);transport=Objects.requireNonNull(sameHeldTransport);
        source=Objects.requireNonNull(actualSource);archive=Objects.requireNonNull(actualArchive);
    }
    /** Restores only durable revision/projection metadata; all received chronology and frames come from the new transport. */
    synchronized void bindInitialRecovery(FreshGameplayEntryAuthority.RecoveryAdmission actual,
            ContinuityStorePort.Session same)throws IOException {
        Objects.requireNonNull(actual);actual.requireCurrent(same);
        StrictJson.require(acceptedSession==null&&lastProjectedReceipt==null&&publicRevision.signum()==0&&transportRevisionOffset.signum()==0,
                "initial recovery revision baseline binds once before the new producer's first observation");
        repository.locked(state->{
            StrictJson.require(state instanceof DriverSnapshotFacts.Known known&&known.stamp().equals(actual.facts().stamp())
                    &&java.util.Arrays.equals(known.driver().encode(),actual.facts().driver().encode())
                    &&source.machineId().equals(actual.entry().machineId()),"initial recovery producer crossed its actual full Driver");return true;
        });
        var captured=actual.initialNoDispatchRecovery().flatMap(value->value.capturedManifest());
        if(captured.isPresent()) {
            var manifest=captured.orElseThrow();new PublicRevision(manifest.publicRevision());
            publicRevision=manifest.publicRevision();transportRevisionOffset=publicRevision;
            cleanNativeCampaign=manifest.observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION;
            return;
        }
        var old=actual.facts().observation().orElseThrow(()->new IOException("actual initial observation DATA unavailable"));
        new PublicRevision(old.publicRevision());publicRevision=old.publicRevision();transportRevisionOffset=publicRevision;
        cleanNativeCampaign=old.observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION;
    }

    synchronized void bindCleanRestart(org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartAdmission actual,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException {
        Objects.requireNonNull(actual);actual.requireCurrent(same);
        StrictJson.require(acceptedSession==null&&lastProjectedReceipt==null&&publicRevision.signum()==0&&transportRevisionOffset.signum()==0,
                "clean revision baseline is installed once before the new producer receives a current frame");
        repository.locked(state->{
            StrictJson.require(state instanceof DriverSnapshotFacts.Known&&((DriverSnapshotFacts.Known)state).stamp().equals(actual.facts().stamp())
                    &&source.machineId().equals(actual.controller().owner().machineId()),"clean producer crossed its canonical complete Driver");return true;
        });
        new PublicRevision(actual.manifest().publicRevision());
        publicRevision=actual.manifest().publicRevision();transportRevisionOffset=publicRevision;
        cleanNativeCampaign=actual.manifest().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION;
    }
    /** Verifies object custody for another consumer of this one public revision owner. No I/O or authority is minted. */
    public synchronized void requireSameTransport(NativeGameTransport expected,G2Source expectedSource) {
        StrictJson.require(transport==Objects.requireNonNull(expected) && source.equals(Objects.requireNonNull(expectedSource)),
                "semantic facts must share the exact held transport object and original source DATA");
    }
    /** Actual Bootstrap completion only: original accepted raw/source/session custody, never a readiness grant. */
    synchronized void recordAdoptionObserved(NativeObservationPort.TransportSession expected,G2Source expectedSource)throws IOException {
        StrictJson.require(Objects.requireNonNull(expected).equals(acceptedSession)&&source.equals(Objects.requireNonNull(expectedSource))
                &&transport.diagnostics().session().filter(expected::equals).isPresent(),"successful adoption crossed its actual accepted native/source owner");
        transport.recordAdoptionObserved();
    }
    /** Package-private: only the Bootstrap consumes the original issuer's committed replacement, under its writer. */
    void transferNextEpisode(LifecycleComposites.NextEpisodeAdoption actual,ContinuityStorePort.Session same,
            NativeGameTransport replacement,G2Source replacementSource,NativeObservationPort.TransportSession nextSession,
            DriverCapabilityRuntime candidate,DriverStateAssembler authority,SemanticEvidencePort replacementArchive) throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(same);Objects.requireNonNull(replacement);
        Objects.requireNonNull(replacementSource);Objects.requireNonNull(nextSession);Objects.requireNonNull(replacementArchive);
        Objects.requireNonNull(candidate).requireNextCandidate(same,actual,Objects.requireNonNull(authority));
        var started=actual.replacement();String event=actual.commit().receipt().eventIdentity();
        repository.locked(state -> {
            synchronized(this) {
                StrictJson.require(state instanceof DriverSnapshotFacts.Known,"actual next episode Driver owner unavailable");
                var current=(DriverSnapshotFacts.Known)state;var published=actual.published();
                StrictJson.require(current.stamp().equals(published.stamp())
                        && Arrays.equals(current.driver().encode(),published.driver().encode()),"next episode complete published owner changed");
                StrictJson.require(nextSession.game().equals(started.newGame()) && nextSession.sessionId().equals(started.sessionId())
                        && nextSession.machineId().equals(replacementSource.machineId())
                        && replacement.pipeName().equals(started.pipeName())
                        && replacement.diagnostics().session().filter(nextSession::equals).isPresent(),"replacement held Native session differs from private lifecycle custody");
                if(event.equals(nextEpisodeEvent)) {
                    StrictJson.require(transport==replacement && source.equals(replacementSource)
                            && (acceptedSession==null || acceptedSession.equals(nextSession)),"same committed transfer cannot change its original transport/source");
                    return null;
                }
                StrictJson.require(acceptedSession!=null && acceptedSession.game().equals(started.oldGame())
                        && !acceptedSession.game().equals(nextSession.game()),"actual old producer and distinct next Game required");
                // Retain the old receiver's actual final state, including its observed non-packet disconnect.
                // The existing lifecycle already stopped/closed/cleaned up this Game before launching the replacement.
                // Reading retained DATA cannot close it again or infer a revision from a lifecycle ACK.
                var retired=transport.latestStateRevision().orElseThrow(
                        ()->new IllegalArgumentException("actual retired native state revision unavailable"));
                StrictJson.require(retired.session().equals(acceptedSession)
                        &&retired.kind()==NativeGameTransport.StateRevisionKind.DISCONNECTED
                        &&retired.disconnection().isPresent(),
                        "NEXT requires the actual old session's observed disconnected final revision");
                BigInteger retiredRevision=transportRevisionOffset.add(retired.publicRevision());
                new PublicRevision(retiredRevision);
                StrictJson.require(retiredRevision.compareTo(publicRevision)>=0,"actual retired receive revision regressed");
                publicRevision=retiredRevision;transportRevisionOffset=retiredRevision;
                transport=replacement;source=replacementSource;archive=replacementArchive;acceptedSession=null;lastProjectedReceipt=null;
                archivedDriverSha256=null;archivedDriver=null;nextEpisodeEvent=event;
                // The replacement transport's actual hello/ingest revisions add to this immutable old-session offset.
                return null;
            }
        });
        candidate.requireNextCandidate(same,actual,authority);
    }
    @Override public DriverObservationFacts.Result read(NativeObservationPort.ObservedFrame actual) {
        Objects.requireNonNull(actual);
        return repository.locked(state -> {
            if(state instanceof DriverSnapshotFacts.Unavailable missing)return new DriverObservationFacts.Unavailable(missing.reasons());
            synchronized(this) { return produce(actual,(DriverSnapshotFacts.Known)state); }
        });
    }
    private DriverObservationFacts.Result produce(NativeObservationPort.ObservedFrame actual,DriverSnapshotFacts.Known known) {
        try {
            if(nativeCampaignFixture!=null)nativeCampaignFixture.requireCurrent(this);
            if(savedNativeCampaign!=null)savedNativeCampaign.requireCurrent(this);
            if(restoredNativeCampaign!=null)restoredNativeCampaign.requireCurrent(this);
            boolean explicitNativeCampaign=nativeCampaignFixture!=null||savedNativeCampaign!=null||restoredNativeCampaign!=null||cleanNativeCampaign;
            long observationVersion=explicitNativeCampaign?DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION:OBSERVATION_CONTRACT_VERSION;
            var diagnostics=transport.diagnostics();
            StrictJson.require(diagnostics.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED
                    && diagnostics.session().filter(actual.session()::equals).isPresent(),"actual held hello/session unavailable or terminal");
            var hello=diagnostics.originalHello().orElseThrow(() -> new IllegalArgumentException("actual native hello missing")).original();
            StrictJson.require(hello.pid()==known.stamp().game().pid() && known.stamp().game().equals(actual.session().game())
                    && hello.connectionGeneration().equals(actual.session().connectionGeneration())
                    && source.machineId().equals(actual.session().machineId())
                    && known.driver().session().pipeName().equals(transport.pipeName()),"native/Driver Game/source/session/pipe differs");
            StrictJson.require(hello.capabilities().contains("game.state.snapshot"),"actual native snapshot capability missing");
            OpportunityJson.Obj raw=DriverObservationAssembler.originalNativeState(actual);
            var accepted=transport.acceptedSnapshotRevision(actual);
            accepted.requireOriginal(actual);
            StrictJson.require(accepted.session().equals(actual.session()),"actual accepted snapshot revision crossed its received session");
            StrictJson.require(acceptedSession==null||acceptedSession.equals(actual.session()),
                    "new native session requires a new protocol producer; no silent reconnect revision reset");
            // Only actual receive chronology can distinguish repeated A/B/A packets, even at the same UTC time.
            // A historical original remains replayable through its manifest but cannot replace current Driver facts.
            StrictJson.require(lastProjectedReceipt==null||accepted.received().order().compareTo(lastProjectedReceipt.order())>=0,
                    "older actual Native frame cannot replace the current semantic publication; replay its original manifest");
            BigInteger receivedRevision=transportRevisionOffset.add(accepted.publicRevision());
            new PublicRevision(receivedRevision);
            StrictJson.require(receivedRevision.compareTo(publicRevision)>=0,"actual accepted public revision regressed");
            acceptedSession=actual.session();lastProjectedReceipt=accepted.received();publicRevision=receivedRevision;
            Map<String,OpportunityJson.Value> extra=new LinkedHashMap<>((explicitNativeCampaign
                    ?NativeCampaignProjection.withoutDriverEpisodeOverlay(known.auxiliary()):known.auxiliary()).members());
            if(explicitNativeCampaign)extra.put("episode_projection",new OpportunityJson.Text(NativeCampaignProjection.WIRE_MODE));
            for(var field:raw.members().entrySet()) {
                if("diagnostics".equals(field.getKey()) || explicitNativeCampaign&&"episode_projection".equals(field.getKey()))continue;
                if(extra.containsKey(field.getKey()))StrictJson.require(extra.get(field.getKey()).equals(field.getValue()),"retained Driver auxiliary crossed native field: "+field.getKey());
            }
            extra.put("backend_id",new OpportunityJson.Text("native-headless"));
            extra.put("source",new OpportunityJson.Text("injected-dll-named-pipe"));
            var diagnosticFields=raw.get("diagnostics") instanceof OpportunityJson.Obj nativeDiagnostics
                    ? new LinkedHashMap<>(nativeDiagnostics.members()) : new LinkedHashMap<String,OpportunityJson.Value>();
            if(extra.get("diagnostics") instanceof OpportunityJson.Obj originalDiagnostics)
                originalDiagnostics.members().forEach((key,value) -> {
                    if(!LIVE_DIAGNOSTICS.contains(key)&&!BridgeDiagnosticsCodec.nativeOwnedFields().contains(key))retainDiagnostic(diagnosticFields,key,value);
                });
            retainDiagnostic(diagnosticFields,"pipe_name",new OpportunityJson.Text(known.driver().session().pipeName()));
            retainDiagnostic(diagnosticFields,"connected",new OpportunityJson.Bool(true));
            retainDiagnostic(diagnosticFields,"bridge_pid",new OpportunityJson.IntegerValue(BigInteger.valueOf(actual.session().game().pid())));
            retainDiagnostic(diagnosticFields,"connection_generation",new OpportunityJson.IntegerValue(actual.session().connectionGeneration()));
            retainDiagnostic(diagnosticFields,"hello",packet(hello.packet().value()));
            diagnostics.latestHeartbeat().ifPresent(received -> retainDiagnostic(diagnosticFields,"last_heartbeat",packet(received.original().packet().value())));
            diagnostics.latestPong().ifPresent(received -> retainDiagnostic(diagnosticFields,"last_pong",packet(received.original().packet().value())));
            diagnostics.latestError().ifPresent(received -> retainDiagnostic(diagnosticFields,"last_error",packet(received.original().packet().value())));
            diagnostics.latestSnapshotDiagnostic().ifPresent(received -> retainDiagnostic(diagnosticFields,"last_snapshot_publish_diagnostic",packet(received.original().packet().value())));
            diagnostics.production().ifPresent(production -> {
                StrictJson.require(production.session().equals(diagnostics.session()),"actual native diagnostic counters crossed their original transport session");
                BridgeDiagnosticsCodec.nativeProductionFields(production).members().forEach((key,value) -> retainDiagnostic(diagnosticFields,key,value));
            });
            extra.put("diagnostics",new OpportunityJson.Obj(diagnosticFields));
            String nativeSha=DriverJson.sha256(actual.state().bytes());
            if(!known.stamp().driverSha256().equals(archivedDriverSha256)) {
                byte[] wire=known.driver().encode();
                StrictJson.require(wire.length<=RawJson.MAXIMUM_BYTES,"complete Driver exceeds qualified semantic archive lane; no truncated history");
                ExactRef saved=archive.preserve(wire);
                StrictJson.require(saved.bytes()==wire.length && saved.sha256().equals(DriverJson.sha256(wire)),"complete current Driver archive differs");
                archivedDriver=saved;archivedDriverSha256=known.stamp().driverSha256();
            }
            byte[] original=DriverObservationEvidenceReader.encode(known,actual,publicRevision,observationVersion,
                    source,new OpportunityJson.Obj(extra),archivedDriver).bytes();
            ExactRef ref=archive.preserve(original.clone());
            StrictJson.require(ref.bytes()==original.length && ref.sha256().equals(DriverJson.sha256(original)),"actual semantic facts archive differs");
            return new DriverObservationFacts.Known(new DriverObservationFacts(known.driver(),known.stamp().driverVersion(),known.stamp().episodeEpoch(),
                    actual.session(),actual.snapshotId(),actual.nativeRevision(),nativeSha,publicRevision,observationVersion,source,new OpportunityJson.Obj(extra),ref));
        } catch(IOException | IllegalArgumentException | ArithmeticException failure) {
            return new DriverObservationFacts.Unavailable(List.of("actual_native_driver_facts: "+failure.getMessage()));
        }
    }
    private static OpportunityJson.Obj packet(byte[] framed) {
        StrictJson.require(framed.length>=5,"actual framed native diagnostic required");
        int size=ByteBuffer.wrap(framed,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        StrictJson.require(size>0 && size<=DriverJson.MAX_NATIVE_BYTES && framed.length==size+4,"original diagnostic packet length differs");
        return DriverJson.object(Arrays.copyOfRange(framed,4,framed.length),DriverJson.MAX_NATIVE_BYTES);
    }
    private static void retainDiagnostic(Map<String,OpportunityJson.Value> fields,String key,OpportunityJson.Value value) {
        var old=fields.putIfAbsent(key,value);StrictJson.require(old==null || old.equals(value),"actual native diagnostic differs: "+key);
    }
}
