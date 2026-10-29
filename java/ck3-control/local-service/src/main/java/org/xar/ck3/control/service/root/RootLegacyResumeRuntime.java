package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import org.xar.ck3.control.contracts.NativeCharacterId;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.history.*;
import org.xar.ck3.control.application.history.LegacyResumeMigration.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.OriginalLegacyResume.Route;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** The actual original importer -> native packet -> migration -> sole continuity writer producer.
 * It submits no gameplay action, consolidates no Python WAL and creates no replacement Game.
 * A private Prepared is scoped to its concrete Root context and currently held writer Session. */
public final class RootLegacyResumeRuntime {
    public sealed interface Result permits Awaiting,Prepared { }
    public record Awaiting(String reason,List<ExactRef> originalReferences) implements Result {
        public Awaiting {StrictJson.text(reason);originalReferences=List.copyOf(originalReferences);}
    }
    public enum ColdRejection { NO_COMPLETE_CHECKPOINT_ANCHOR,PLAYED_CHARACTER_MISMATCH,CHECKPOINT_DATE_MISMATCH,
        CHECKPOINT_PATH_UNAVAILABLE,CHECKPOINT_SIZE_MISMATCH,CHECKPOINT_SHA256_MISMATCH }
    /** The closed rejection is derived solely from a legitimate parsed candidate and actual observations. */
    public static final class RejectedCold {
        private final RootLegacyResumeRuntime issuer;private final Attempt attempt;private final ColdRejection reason;
        private final Optional<SaveObservation> save;private final ExactRef evidence;
        private RejectedCold(RootLegacyResumeRuntime issuer,Attempt attempt,ColdRejection reason,Optional<SaveObservation> save,ExactRef evidence) {
            this.issuer=issuer;this.attempt=attempt;this.reason=reason;this.save=save;this.evidence=evidence;
        }
        public ColdRejection reason(){return reason;}
        public ExactRef evidence(){return evidence;}
        public ExactRef originalDriver(){return attempt.originalDriver;}
    }
    private record SaveObservation(Path path,Optional<SharedSourceFiles.Witness> original,Optional<FileWitness> witness) { }
    private static final class Attempt {
        private final ContinuityStorePort.Session same;private final WriterContracts.Head before;
        private final RootOriginalDriverJournal.OriginalJournalLoad load;private final LegacyResumeNormalizer.Loaded canonical;
        private final NativeObservationPort.ObservedFrame nativeRaw;private final NativeOccurrence nativeOccurrence;private final Obj nativeState;
        private final ExactRef originalDriver,canonicalOriginal,originalHello,originalNative,canonicalNative;
        private final NativeReadinessCollector.SourceQualification source;private final Optional<String> sourceEpoch;
        private final List<WriterContracts.Pin> pins=new ArrayList<>();
        private RootOriginalDriverJournal.ManagedQueueObservation queue;private ExactRef queueEvidence;
        private BindingIdentity binding;private RejectedCold rejected;private RootColdCheckpointValidator.Verified cold;
        private SaveObservation save;private Prepared prepared;
        private Attempt(ContinuityStorePort.Session same,WriterContracts.Head before,RootOriginalDriverJournal.OriginalJournalLoad load,
                LegacyResumeNormalizer.Loaded canonical,NativeObservationPort.ObservedFrame nativeRaw,NativeOccurrence nativeOccurrence,Obj nativeState,
                ExactRef originalDriver,ExactRef canonicalOriginal,ExactRef originalHello,ExactRef originalNative,ExactRef canonicalNative,
                NativeReadinessCollector.SourceQualification source,Optional<String> sourceEpoch) {
            this.same=same;this.before=before;this.load=load;this.canonical=canonical;this.nativeRaw=nativeRaw;this.nativeOccurrence=nativeOccurrence;this.nativeState=nativeState;
            this.originalDriver=originalDriver;this.canonicalOriginal=canonicalOriginal;this.originalHello=originalHello;
            this.originalNative=originalNative;this.canonicalNative=canonicalNative;this.source=source;this.sourceEpoch=sourceEpoch;
        }
    }
    public static final class Prepared implements Result {
        private final RootLegacyResumeRuntime issuer;private final Attempt attempt;private final OriginalLegacyResume.Delta delta;
        private final DriverStateSnapshot.Complete driver;private final Obj auxiliary;private final Optional<RejectedCold> rejection;
        private WriterContracts.Prepared transition;private WriterContracts.Receipt committed;
        private boolean recoveredCommitted;
        private RootCanonicalDriverCoverage historyCoverage;
        private Prepared(RootLegacyResumeRuntime issuer,Attempt attempt,OriginalLegacyResume.Delta delta,
                DriverStateSnapshot.Complete driver,Obj auxiliary,Optional<RejectedCold> rejection) {
            this.issuer=issuer;this.attempt=attempt;this.delta=delta;this.driver=driver;this.auxiliary=auxiliary;this.rejection=rejection;
        }
        public WriterContracts.Request request(){return delta.request();}
        public OriginalLegacyResume.Delta delta(){return delta;}
        public Optional<RejectedCold> rejectedCold(){return rejection;}
        public NativeObservationPort.ObservedFrame originalNative(){return attempt.nativeRaw;}
        /** First binder only: actual committed private profile selects Saved native, never nullable public DATA. */
        public boolean hasSavedNativeProjection(ContinuityStorePort.Session same,WriterContracts.Receipt actual)throws IOException {
            requireCommitted(same,actual);
            var frozen=attempt.load.frozenProfile();var game=issuer.context.game();
            frozen.requireCurrent(game.launchPlan(),issuer.context.clock());
            boolean selected=frozen.initialPolicy().kind()==InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED;
            if(selected){frozen.requireExplicitNativeCampaign();frozen.initialPolicy().requireSavedProjection(game.launchPlan());}
            return selected;
        }
        /** Returns the identical privately retained Frozen after this exact canonical commit, not decoded provenance. */
        public RootFrozenRunProfile.FrozenRunProfile requireSavedNativeProjection(ContinuityStorePort.Session same,
                WriterContracts.Receipt actual)throws IOException {
            if(!hasSavedNativeProjection(same,actual))throw new IOException("actual committed original is not the Saved native_campaign private projection");
            return attempt.load.frozenProfile();
        }
        /** First binder retains this actual creator Game; later reads must verify its canonical historical prefix. */
        public org.xar.ck3.control.platform.ManagedGameSession requireSavedNativeGame(ContinuityStorePort.Session same,
                WriterContracts.Receipt actual)throws IOException {
            requireSavedNativeProjection(same,actual);return issuer.context.game();
        }
        /** Actual private cold validator output, bound to both original files before any commit. */
        public void requireColdBootstrapPair(ContinuityStorePort.Session same,
                org.xar.ck3.control.application.checkpoint.CheckpointPair pair)throws IOException {
            requireCurrent(same);Objects.requireNonNull(pair);
            require(delta.route()==Route.COLD_CHECKPOINT&&rejection.isEmpty()&&attempt.cold!=null
                    &&attempt.save!=null&&attempt.save.witness().isPresent(),"original private cold SAVE validator did not accept this attempt");
            new org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles().verify(pair);
            require(attempt.save.witness().orElseThrow().equals(pair.save()),"cold bootstrap SAVE is not the private validator's exact FileID/source");
            require(attempt.load.originalBase().isPresent()&&attempt.load.originalBase().orElseThrow().equals(pair.driver()),
                    "cold bootstrap Driver is not the actual original imported base FileID/source");
            require(pair.driver().reference().bytes()==attempt.originalDriver.bytes()
                    &&pair.driver().reference().sha256().equals(attempt.originalDriver.sha256()),
                    "cold bootstrap requires the exact complete original checkpoint Driver; changed WAL content cannot be ignored");
            require(new Bool(true).equals(attempt.nativeState.get("map_ready"))&&new Bool(true).equals(attempt.nativeState.get("paused"))
                    &&attempt.nativeState.get("played_character") instanceof Obj played&&new Bool(true).equals(played.get("alive"))
                    &&actor(attempt.nativeState).orElseThrow(()->new IOException("cold bootstrap native actor absent")).equals(pair.frame().frame().identity().player())
                    &&integer(attempt.nativeState.get("date_raw"),"actual cold date").equals(pair.frame().frame().identity().dateRaw()),
                    "actual private cold native paused map/date/living actor differs from the physical SAVE pair");
            physicalCurrent(same);
        }
        private void physicalCurrent(ContinuityStorePort.Session same)throws IOException {
            issuer.physical.requireCurrentLegacy(same,attempt.cold);issuer.requireSave(attempt.save);requireCurrent(same);
        }
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {issuer.requireCurrent(same,this);}
        /** Preview and commit both borrow the already held original Session; retry queries this exact transition. */
        public synchronized WriterContracts.Receipt commit(ContinuityStorePort.Session same)throws IOException {
            issuer.context.writer().requireSession(same);requireIdentity(same);
            if(committed!=null){requireCommitted(same,committed);return committed;}
            if(transition==null){requireCurrent(same);transition=same.preview(request());}
            var prior=same.queryCommitted(transition);
            if(prior.isPresent())committed=prior.orElseThrow();
            else committed=same.commit(transition);
            requireCommitted(same,committed);return committed;
        }
        public synchronized void requireCommitted(ContinuityStorePort.Session same,WriterContracts.Receipt actual)throws IOException {
            requireIdentity(same);issuer.context.writer().requireSession(same);
            if(transition==null||committed==null||actual!=committed)throw new IOException("original resume lacks this private producer's actual committed transition");
            same.requireCommitted(transition,actual);OriginalLegacyResume.requireReduction(attempt.before.state(),actual.head(),request(),true);
            require(same.head().digest().equals(ContinuityJson.digest(actual.head().toJson())),"another transition followed original resume before its private adoption");
            if(recoveredCommitted) {
                attempt.load.requireRetained(same);
                if(attempt.queue!=null)attempt.queue.requireCurrent(same,attempt.load);
                for(var pin:transition.sources())same.verifyPin(pin);for(var pin:transition.evidence())same.verifyPin(pin);
            }else {
                attempt.load.requireCommittedInputs(same,transition,actual);
                if(attempt.queue!=null)attempt.queue.requireCommittedInputs(same,attempt.load,transition,actual);
            }
            issuer.requireNative(attempt);attempt.source.assertCurrent(same);issuer.verifyPins(same,attempt);
            if(attempt.save!=null)issuer.requireSave(attempt.save);
            require(Arrays.equals(driver.encode(),issuer.context.archive().readArtifact(same,delta.fullDriver(),DriverCheckpointStore.MAX_DRIVER_BYTES)),"committed full migrated Driver changed");
        }
        public DriverBootstrap.Seed seed(ContinuityStorePort.Session same,WriterContracts.Receipt actual)throws IOException {
            requireCommitted(same,actual);
            return new DriverBootstrap.Seed(delta.fullDriver(),delta.fullDriver(),delta.driverVersion(),delta.episodeEpoch(),
                    attempt.nativeRaw.session(),auxiliary,Optional.empty());
        }
        public synchronized DriverBootstrap.HistoryCoverageReader coverage(ContinuityStorePort.Session same,WriterContracts.Receipt actual)throws IOException {
            requireCommitted(same,actual);
            if(historyCoverage==null)historyCoverage=RootCanonicalDriverCoverage.resolved(issuer.context,this,actual);
            return historyCoverage;
        }
        public void requireOwner(ContinuityStorePort.Session same,NativeGameTransport actual,org.xar.ck3.control.g2.common.G2Source source,
                ActionPorts.OutcomeArchive archive)throws IOException {
            requireIdentity(same);require(actual==issuer.context.transport()&&source.equals(issuer.context.source()),"resolved original crossed its actual Root transport/source");
            require(archive==issuer.context.archive(),"resolved original must retain this Core's identical long-lived writer archive");
        }
        private void requireIdentity(ContinuityStorePort.Session same)throws IOException {
            if(issuer.active!=attempt||attempt.prepared!=this||attempt.same!=same)throw new IOException("private original resume belongs to another producer or escaped writer Session");
        }
    }
    private final RootRuntimeContext context;private final RootOriginalDriverJournal.Prepared originals;
    private final ExactRef implementation;private final RootColdCheckpointValidator physical;
    private final RootOriginalDriverAdoptionBundleProducer.Collector adoptionObservations;
    private Attempt active;
    private final WriterContracts.TransitionAuthority authority=new WriterContracts.TransitionAuthority() {
        @Override public String revalidate(ContinuityState ignored,WriterContracts.Request request)throws IOException {
            throw new IOException("original resume requires the same original Head and borrowed Session");
        }
        @Override public String revalidate(WriterContracts.Head before,WriterContracts.Request request)throws IOException {
            var same=context.writer().borrowedSession();context.writer().requireSession(same);
            Prepared actual=active==null?null:active.prepared;
            if(actual==null||!Arrays.equals(actual.request().details(),request.details())||!actual.request().evidence().equals(request.evidence()))
                throw new IOException("no actual private original migration producer owns this request");
            require(before.digest().equals(same.head().digest()),"legacy resume authority crossed the current writer Head");
            actual.requireCurrent(same);OriginalLegacyResume.checked(before.state(),request);
            var proof=StrictJson.object();proof.put("head",before.digest());proof.put("request",request.identity());
            proof.set("migration",actual.delta.migrationPlan().toJson());return ContinuityJson.digest(proof);
        }
        @Override public ContinuityState reduce(ContinuityState before,WriterContracts.Request request){return OriginalLegacyResume.reduce(before,request);}
    };
    public RootLegacyResumeRuntime(RootRuntimeContext actual,RootOriginalDriverJournal.Prepared originalImporter,ExactRef actualImplementation)throws IOException {
        context=Objects.requireNonNull(actual);originals=Objects.requireNonNull(originalImporter);implementation=Objects.requireNonNull(actualImplementation);
        require(implementation.bytes()>0&&context.archive().writer()==context.writer(),"actual original writer/archive and implementation required");
        context.game().verify();originals.frozenProfile().requireCurrent(context.game().launchPlan(),context.clock());
        physical=new RootColdCheckpointValidator(context.writer());
        adoptionObservations=new RootOriginalDriverAdoptionBundleProducer.Collector(context);
    }
    public List<RootOriginalDriverAdoptionBundleProducer.Captured> adoptionCaptures(){return adoptionObservations.captured();}
    public WriterContracts.TransitionAuthority authority(){return authority;}
    public void requireOwner(RootApplicationAssembly.Core actual)throws IOException {
        if(context.core()!=actual||context.writer()!=actual.writer()||context.archive()!=actual.archive())throw new IOException("legacy resume runtime belongs to another actual Core");
    }
    public void requireOwner(RootApplicationAssembly.Core actual,org.xar.ck3.control.platform.ManagedGameSession game,
            org.xar.ck3.control.g2.common.G2Source source)throws IOException {
        requireOwner(actual);if(context.game()!=game||!context.source().equals(source))throw new IOException("legacy resume runtime belongs to another actual physical Game/source");
    }
    public synchronized Result prepare(ContinuityStorePort.Session same,Instant deadline)throws IOException,InterruptedException {
        context.writer().requireSession(same);context.requireCurrent(deadline);
        Attempt earlier=null;
        if(active!=null&&active.same!=same) {
            if(active.prepared!=null) {
                Prepared retained=active.prepared;
                if(retained.transition!=null) {
                    var actual=same.queryCommitted(retained.transition);
                    if(actual.isPresent())return recoverCommitted(same,retained,actual.orElseThrow(),deadline);
                    return awaiting(active,"original commit has no known canonical result; it is not replayed");
                }
                // No commit was entered; only read-only preparation is replaced by a freshly qualified scope.
            }
            // Pending read-only work receives a fresh private load/source qualification; old scoped authority is never reused.
            earlier=active;requireNative(earlier);active=null;
        }
        if(active!=null){
            if(active.prepared!=null){
                if(active.prepared.committed!=null)active.prepared.requireCommitted(same,active.prepared.committed);
                else active.prepared.requireCurrent(same);
                return active.prepared;
            }
            requireAttempt(same,active);
            if(mapReady(active.nativeState))return finish(same,active,deadline);
            // A genuinely later packet may finish an unplayable initial observation. PING is cached, never resent.
            active=null;
        }
        var load=originals.load(context.writer(),same,context.game().launchPlan());
        if(earlier!=null)require(load.status()==earlier.load.status()&&load.originalBase().equals(earlier.load.originalBase())
                &&load.originalJournal().equals(earlier.load.originalJournal())&&load.originalReferences().equals(earlier.load.originalReferences()),
                "pending original input changed while its read-only scope was released");
        NativeGameTransport transport=context.transport();transport.awaitHello(deadline);
        adoptionObservations.classify(same,load,RootOriginalDriverAdoptionBundleProducer.caseName(context.game().launchPlan())).requireAccepted();
        if(load.status()==RootOriginalDriverJournal.Status.MISSING)return new Awaiting("actual original Driver is absent; this is not the private fresh-bookmark route",load.originalReferences());
        var normalized=load.normalizeForFrozen(same);
        if(!(normalized instanceof LegacyResumeNormalizer.Loaded canonical))return new Awaiting("actual existing base Driver was rejected; no empty episode fallback",load.originalReferences());
        for(ActionReceipt action:ContinuityActionJournal.receipts(same.head().state(),context.archive().withSession(same)))
            require(action.settled(),"unresolved canonical action cannot be reclassified or replayed by legacy migration");
        transport.startHandshake(deadline);
        var raw=earlier!=null&&mapReady(earlier.nativeState)?earlier.nativeRaw:transport.observe(deadline);
        require(raw.session().equals(load.requireActualHello(same,transport))&&raw.session().game().equals(context.game().generation()),"actual original native observation crossed managed HELLO/full Game birth");
        NativeOccurrence occurrence=NativeOccurrence.capture(transport,raw);
        Obj state=DriverObservationAssembler.canonicalNativeState(raw).semantic();
        var archive=context.archive();ExactRef originalDriver=archive.preserveArtifact(same,load.fullBytes(),DriverCheckpointStore.MAX_DRIVER_BYTES);
        ExactRef canonicalOriginal=archive.preserveArtifact(same,canonical.encode(),DriverCheckpointStore.MAX_DRIVER_BYTES);
        ExactRef hello=archive.preserveArtifact(same,transport.originalHello().packet().value(),DriverJson.MAX_NATIVE_BYTES+4);
        ExactRef nativePacket=archive.withSession(same).preserveNativeFrame(raw);
        ExactRef semantic=archive.preserveArtifact(same,DriverJson.encode(state),DriverJson.MAX_NATIVE_BYTES);
        var qualification=context.sources().verifyPhysicalOrigin(same,raw.session(),context.source(),nativePacket,transport.diagnostics(),deadline);
        var epochOpt=context.sources().optionalMetadata(same,qualification).map(m->m.ownerSourceEpoch());
        active=new Attempt(same,same.head(),load,canonical,raw,occurrence,state,originalDriver,canonicalOriginal,hello,nativePacket,semantic,qualification,epochOpt);
        for(ExactRef ref:load.originalReferences())pin(same,active,ref);
        for(ExactRef ref:List.of(implementation,originalDriver,canonicalOriginal,hello,nativePacket,semantic))pin(same,active,ref);
        if(qualification.proof().isPresent())pin(same,active,qualification.proof().orElseThrow());
        return finish(same,active,deadline);
    }
    /** A known committed event is inspected and adopted; this path never invokes commit or native observe. */
    private Prepared recoverCommitted(ContinuityStorePort.Session same,Prepared retained,WriterContracts.Receipt committed,Instant deadline)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);same.requireCommitted(retained.transition,committed);
        require(same.head().digest().equals(ContinuityJson.digest(committed.head().toJson())),"original commit was followed by another transition before recovery");
        OriginalLegacyResume.requireReduction(retained.attempt.before.state(),committed.head(),retained.request(),true);
        for(var pin:retained.transition.sources())same.verifyPin(pin);for(var pin:retained.transition.evidence())same.verifyPin(pin);
        Attempt old=retained.attempt;requireNative(old);
        var load=originals.load(context.writer(),same,context.game().launchPlan());
        DriverBootstrap.requireOriginalAdoption(same,context.transport(),load);
        require(load.originalReferences().equals(old.load.originalReferences())&&load.originalBase().equals(old.load.originalBase())
                &&load.originalJournal().equals(old.load.originalJournal())&&OriginalDriverJournal.sha256(load.fullBytes()).equals(old.originalDriver.sha256()),
                "actual original inputs changed after the canonical resume commit");
        var normalized=load.normalizeForFrozen(same);
        require(normalized instanceof LegacyResumeNormalizer.Loaded,"actual committed original no longer has its canonical full payload");
        var canonical=(LegacyResumeNormalizer.Loaded)normalized;
        require(DriverJson.sha256(canonical.encode()).equals(old.canonicalOriginal.sha256()),"actual original canonical payload changed after commit");
        var source=context.sources().verifyPhysicalOrigin(same,old.nativeRaw.session(),context.source(),old.originalNative,context.transport().diagnostics(),deadline);
        var epochOpt=context.sources().optionalMetadata(same,source).map(m->m.ownerSourceEpoch());
        if(old.sourceEpoch.isPresent()&&epochOpt.isPresent())require(old.sourceEpoch.equals(epochOpt),"actual native/Java source epoch changed after original commit");
        Attempt fresh=new Attempt(same,old.before,load,canonical,old.nativeRaw,old.nativeOccurrence,old.nativeState,old.originalDriver,old.canonicalOriginal,
                old.originalHello,old.originalNative,old.canonicalNative,source,epochOpt);
        fresh.binding=old.binding;fresh.save=old.save;fresh.queueEvidence=old.queueEvidence;
        if(old.queue!=null) {
            fresh.queue=RootOriginalDriverJournal.probeManagedQueue(same,load,old.queue.requestId());fresh.queue.requireCurrent(same,load);
            require(fresh.queue.identityDigest().equals(old.queue.identityDigest()),"actual queue identity/presence/content changed after original commit");
        }
        Optional<RejectedCold> rejection=Optional.empty();
        if(retained.rejection.isPresent()) {
            var prior=retained.rejection.orElseThrow();var current=new RejectedCold(this,fresh,prior.reason,prior.save,prior.evidence);
            fresh.rejected=current;rejection=Optional.of(current);
        }
        Prepared result=new Prepared(this,fresh,retained.delta,retained.driver,retained.auxiliary,rejection);
        result.transition=retained.transition;result.committed=committed;result.recoveredCommitted=true;fresh.prepared=result;active=fresh;
        for(ExactRef ref:retained.delta.evidence())pin(same,fresh,ref);result.requireCommitted(same,committed);return result;
    }
    private Result finish(ContinuityStorePort.Session same,Attempt attempt,Instant deadline)throws IOException {
        requireAttempt(same,attempt);
        if(!mapReady(attempt.nativeState))return awaiting(attempt,"actual native map is not yet playable");
        var request=new Request(attempt.canonical,BigInteger.valueOf(attempt.nativeRaw.session().game().pid()),
                frozenLifecycle(attempt),SaveDirectoryState.CONFIGURED,Optional.of(attempt.nativeState),Optional.empty());
        Plan plan=LegacyResumeMigration.resolve(request);
        if(plan instanceof NeedsManagedQueue waiting) {
            attempt.queue=RootOriginalDriverJournal.probeManagedQueue(same,attempt.load,waiting.requestId());
            attempt.queue.requireCurrent(same,attempt.load);
            plan=LegacyResumeMigration.withManagedQueue(waiting,new ManagedQueueData(attempt.queue.requestId(),QueueStatus.valueOf(attempt.queue.status().name())));
            var queue=StrictJson.object();queue.put("schema","xar.java-original-managed-queue-observation/v1");
            queue.put("request_id",attempt.queue.requestId());queue.put("status",attempt.queue.status().name());
            if(attempt.queue.readIssue().isPresent())queue.put("read_issue",attempt.queue.readIssue().orElseThrow().name());else queue.putNull("read_issue");
            if(attempt.queue.readErrorType().isPresent())queue.put("read_error_type",attempt.queue.readErrorType().orElseThrow());else queue.putNull("read_error_type");
            var refs=queue.putArray("original_references");attempt.queue.originalReferences().forEach(ref->refs.add(ref.toJson()));
            attempt.queueEvidence=context.archive().preserveArtifact(same,ContinuityJson.canonical(queue),1<<20);
        }
        if(plan instanceof RequiredBinding binding) {
            if(attempt.binding==null)attempt.binding=mint(attempt,binding.actualCharacterId());
            plan=LegacyResumeMigration.bind(binding,attempt.binding);
        }
        if(plan instanceof Rejected rejected)throw new IOException("actual canonical legacy migration failed: "+rejected.reason()+": "+rejected.diagnostic());
        if(plan instanceof NeedsManagedQueue)return awaiting(attempt,"the actual managed restore request remains unresolved");
        Obj payload;Route route;Optional<RejectedCold> rejected=Optional.empty();
        if(plan instanceof SamePidData hot) {
            if(!hot.pending().isEmpty())return awaiting(attempt,"actual same-PID migration remains pending: "+hot.pending());
            payload=hot.modernDriverPayload();route=attempt.binding==null?Route.SAME_PID:Route.BIND_UNBOUND;
        }else if(plan instanceof PendingColdData cold) {
            ColdResult result=resolveCold(same,attempt,cold);
            payload=result.payload();rejected=result.rejection();route=rejected.isPresent()?Route.COLD_REJECTED_NEW_EPISODE:Route.COLD_CHECKPOINT;
        }else throw new IOException("actual legacy reducer produced an unsupported pending branch");
        DriverStateSnapshot.Complete driver=DriverStateSnapshot.decodeComplete(DriverJson.encode(payload));
        BigInteger actualActor=actor(attempt.nativeState).orElseThrow(()->new IOException("actual playable native character is absent"));
        if(!driver.session().actorId().equals(actualActor))return awaiting(attempt,"actual bound character changed and requires the real lifecycle reducer");
        require(driver.session().bridgePid()==attempt.nativeRaw.session().game().pid()&&driver.session().pipeName().equals(attempt.load.pipeName()),"migration crossed actual HELLO PID/pipe");
        var decision=StrictJson.object();decision.put("schema","xar.java-original-legacy-migration-decision/v1");decision.put("route",route.name());
        decision.set("original_driver",attempt.originalDriver.toJson());decision.set("canonical_original",attempt.canonicalOriginal.toJson());
        decision.set("original_native",attempt.originalNative.toJson());decision.set("canonical_native",attempt.canonicalNative.toJson());
        decision.put("complete_history_rows",driver.commandHistory().size());decision.put("full_driver_sha256",DriverJson.sha256(driver.encode()));
        decision.put("original_lifecycle_migration_required",attempt.canonical.lifecycleMigrationRequired());
        decision.put("original_rollback_migration_required",attempt.canonical.rollbackMigrationRequired());
        if(rejected.isPresent())decision.set("cold_rejection",rejected.orElseThrow().evidence().toJson());else decision.putNull("cold_rejection");
        if(attempt.queueEvidence!=null)decision.set("managed_queue",attempt.queueEvidence.toJson());else decision.putNull("managed_queue");
        if(attempt.cold!=null){decision.set("physical_driver",file(attempt.cold.driverWitness()));decision.set("physical_save",file(attempt.cold.saveWitness()));}
        else {decision.putNull("physical_driver");decision.putNull("physical_save");}
        ExactRef migration=context.archive().preserveArtifact(same,ContinuityJson.canonical(decision),1<<20);
        ExactRef full=context.archive().preserveArtifact(same,driver.encode(),DriverCheckpointStore.MAX_DRIVER_BYTES);
        OriginalLegacyResume.BeforeHistory prior;
        var before=attempt.before.state().toJson();
        if(before.has(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD)) {
            require(!before.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD).isNull(),"null original history basis is not an absent baseline");
            prior=new OriginalLegacyResume.BoundHistory(ExactRef.fromJson(before.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD)));
        }else prior=new OriginalLegacyResume.MissingHistory();
        var inputs=new LinkedHashSet<ExactRef>(attempt.load.originalReferences());if(attempt.source.proof().isPresent())inputs.add(attempt.source.proof().orElseThrow());
        if(attempt.queue!=null)inputs.addAll(attempt.queue.originalReferences());rejected.ifPresent(value->inputs.add(value.evidence()));
        if(attempt.cold!=null){
            var physicalProof=StrictJson.object();physicalProof.put("schema","xar.java-original-legacy-physical-checkpoint/v1");
            physicalProof.set("driver",file(attempt.cold.driverWitness()));physicalProof.set("save",file(attempt.cold.saveWitness()));
            inputs.add(context.archive().preserveArtifact(same,ContinuityJson.canonical(physicalProof),1<<20));
        }
        var delta=new OriginalLegacyResume.Delta(implementation,attempt.nativeRaw.session().machineId(),attempt.before.digest(),prior,route,
                attempt.nativeRaw.session().sessionId(),driver.session().pipeName(),
                new OriginalLegacyResume.Game(attempt.nativeRaw.session().game().pid(),attempt.nativeRaw.session().game().creationFiletime().value().toString()),
                driver.session().actorId().longValueExact(),driver.session().episodeRunId(),0,0,attempt.originalDriver,attempt.canonicalOriginal,full,
                attempt.originalHello,attempt.originalNative,attempt.canonicalNative,migration,Optional.ofNullable(attempt.queueEvidence),List.copyOf(inputs));
        Obj auxiliary=new Obj(java.util.Map.of("java_legacy_resume_source",DriverJson.fromNormalizedNode(migration.toJson())));
        Prepared prepared=new Prepared(this,attempt,delta,driver,auxiliary,rejected);attempt.prepared=prepared;
        for(ExactRef ref:delta.evidence())pin(same,attempt,ref);
        requireCurrent(same,prepared);return prepared;
    }
    private record ColdResult(Obj payload,Optional<RejectedCold> rejection) { }
    private ColdResult resolveCold(ContinuityStorePort.Session same,Attempt attempt,PendingColdData cold)throws IOException {
        Obj candidate=cold.candidate();ColdRejection rejection=null;
        if(!cold.anchorReady())rejection=ColdRejection.NO_COMPLETE_CHECKPOINT_ANCHOR;
        BigInteger actualActor=actor(attempt.nativeState).orElseThrow(()->new IOException("actual cold map has no current character"));
        Obj checkpoint=candidate.get("last_checkpoint") instanceof Obj value?value:null;
        if(rejection==null&&!new IntegerValue(actualActor).equals(candidate.get("episode_character_id")))rejection=ColdRejection.PLAYED_CHARACTER_MISMATCH;
        if(rejection==null&&!attempt.nativeState.get("date_raw").equals(checkpoint.get("date_raw")))rejection=ColdRejection.CHECKPOINT_DATE_MISMATCH;
        if(rejection==null) {
            Path profile=attempt.load.profileDirectory();attempt.load.requireActualProfile(same,profile);
            attempt.save=observeSave(profile.resolve("save games").resolve(RootColdCheckpointValidator.CHECKPOINT_FILENAME));
            if(attempt.save.witness().isEmpty())rejection=ColdRejection.CHECKPOINT_SIZE_MISMATCH;
            else if(!BigInteger.valueOf(attempt.save.witness().orElseThrow().reference().bytes()).equals(integer(checkpoint.get("size"),"actual checkpoint size")))rejection=ColdRejection.CHECKPOINT_SIZE_MISMATCH;
            else if(!new Text(attempt.save.witness().orElseThrow().reference().sha256()).equals(checkpoint.get("sha256")))rejection=ColdRejection.CHECKPOINT_SHA256_MISMATCH;
            if(rejection==null) {
                FileWitness originalComplete=physicalWitness(attempt.originalDriver);
                var expected=physical.expectedLegacy(same,attempt.load,originalComplete,attempt.save.witness().orElseThrow(),profile);
                attempt.cold=physical.verifyLegacy(same,expected);physical.requireCurrentLegacy(same,attempt.cold);
            }
        }
        if(rejection!=null) {
            RejectedCold actual=rejectCold(same,attempt,rejection);attempt.rejected=actual;
            // Original Python's explicit rejected-cold transition. The old full branch remains immutable evidence.
            if(attempt.binding==null)attempt.binding=mint(attempt,actualActor);
            Obj payload=attempt.canonical.normalizedPayload().with("format_version",number(2)).with("pipe_name",new Text(attempt.load.pipeName()))
                    .with("bridge_pid",number(attempt.nativeRaw.session().game().pid())).with("episode_character_id",new IntegerValue(actualActor))
                    .with("episode_run_id",new Text(attempt.binding.runId())).with("command_history",new Arr(List.of())).with("last_checkpoint",Nil.INSTANCE)
                    .with("campaign_goal",Nil.INSTANCE).with("rollback_war_failure",Nil.INSTANCE).with("rollback_war_failures",new Arr(List.of()))
                    .with("managed_restore_transaction",Nil.INSTANCE).with("succession_expectation",Nil.INSTANCE)
                    .with("succession_lifecycle",lifecycle(attempt));
            return new ColdResult(withoutMigrationFlags(payload),Optional.of(actual));
        }
        require(attempt.cold!=null,"actual physical checkpoint qualification is absent");
        List<Obj> original=attempt.canonical.commandHistory();String run=text(candidate.get("episode_run_id"),"original cold episode run");
        var retained=DriverHistoryProjection.retain(checkpoint,original);
        require(retained instanceof DriverHistoryProjection.Available,"actual original checkpoint lineage is unavailable");
        var rows=new ArrayList<>(((DriverHistoryProjection.Available)retained).rows());
        Obj result=new Obj(java.util.Map.of("step",new Text(DriverSurvivingHistory.RESTORE),"accepted",new Bool(true),"status",new Text("restored"),
                "backend_id",new Text("native-headless"),"source",new Text("native-session-cold-start"),"checkpoint",checkpoint,
                "restored_date_raw",attempt.nativeState.get("date_raw"),"map_ready",new Bool(true),
                "lifecycle",new Obj(java.util.Map.of("previous_pid",candidate.get("bridge_pid"),"pid",number(attempt.nativeRaw.session().game().pid())))));
        Obj completion=new Obj(java.util.Map.of("index",number(rows.size()+1L),"command",new Text(DriverSurvivingHistory.RESTORE),"ok",new Bool(true),"result",result));
        // A same-PID managed crossed transaction is not falsely promoted to an unequal physical restart.
        DriverSurvivingHistory.row(completion);rows.add(completion);
        List<Obj> current=RollbackWarFailures.deriveCurrentLegacyDriverFailure(original,checkpoint,attempt.nativeState,run,Optional.empty(),0).map(List::of).orElseGet(List::of);
        List<Obj> completed=attempt.canonical.rollbackMigrationRequired()?RollbackWarFailures.deriveCompletedLegacyDriverFailures(original,checkpoint,attempt.nativeState,run,2):List.of();
        List<Obj> existing=objects(new Arr(array(candidate.get("rollback_war_failures"),"original rollback failures")));
        List<Obj> merged=RollbackWarFailures.boundedLegacyDriverFailures(current,existing,completed);
        Obj payload=candidate.with("format_version",number(2)).with("pipe_name",new Text(attempt.load.pipeName())).with("bridge_pid",number(attempt.nativeRaw.session().game().pid()))
                .with("command_history",new Arr(new ArrayList<Value>(rows))).with("rollback_war_failures",new Arr(new ArrayList<Value>(merged)))
                .with("rollback_war_failure",merged.isEmpty()?Nil.INSTANCE:merged.getFirst()).with("managed_restore_transaction",Nil.INSTANCE)
                .with("succession_expectation",Nil.INSTANCE).with("succession_lifecycle",lifecycle(attempt));
        return new ColdResult(withoutMigrationFlags(payload),Optional.empty());
    }
    private RejectedCold rejectCold(ContinuityStorePort.Session same,Attempt attempt,ColdRejection reason)throws IOException {
        requireAttempt(same,attempt);if(attempt.save!=null)requireSave(attempt.save);
        var record=StrictJson.object();record.put("schema","xar.java-original-cold-rejection/v1");record.put("reason",reason.name());
        record.set("original_driver",attempt.originalDriver.toJson());record.set("canonical_original",attempt.canonicalOriginal.toJson());
        record.set("actual_native",attempt.originalNative.toJson());record.set("canonical_native",attempt.canonicalNative.toJson());
        record.set("source_qualification",ExactRef.optionalToJson(attempt.source.proof()));
        if(attempt.save!=null&&attempt.save.witness().isPresent())record.set("observed_save",file(attempt.save.witness().orElseThrow()));else record.putNull("observed_save");
        record.put("source_binding","actual parsed original candidate; no rejected base or missing Driver fallback");
        ExactRef evidence=context.archive().preserveArtifact(same,ContinuityJson.canonical(record),1<<20);
        return new RejectedCold(this,attempt,reason,Optional.ofNullable(attempt.save),evidence);
    }
    private void requireCurrent(ContinuityStorePort.Session same,Prepared prepared)throws IOException {
        prepared.requireIdentity(same);requireAttempt(same,prepared.attempt);
        require(same.head().digest().equals(prepared.delta.expectedHeadSha256()),"legacy resume original Head changed before commit");
        if(prepared.attempt.queue!=null)prepared.attempt.queue.requireCurrent(same,prepared.attempt.load);
        if(prepared.attempt.save!=null)requireSave(prepared.attempt.save);
        if(prepared.attempt.cold!=null)physical.requireCurrentLegacy(same,prepared.attempt.cold);
        OriginalLegacyResume.checked(same.head().state(),prepared.request());
        require(Arrays.equals(prepared.driver.encode(),context.archive().readArtifact(same,prepared.delta.fullDriver(),DriverCheckpointStore.MAX_DRIVER_BYTES)),"full migrated Driver changed before its only commit");
        if(prepared.rejection.isPresent()) {
            RejectedCold rejected=prepared.rejection.orElseThrow();
            require(rejected.issuer==this&&rejected.attempt==prepared.attempt&&prepared.delta.route()==Route.COLD_REJECTED_NEW_EPISODE,
                    "cold rejection did not originate at this exact physical/native producer");
            require(prepared.driver.commandHistory().isEmpty()&&prepared.driver.lastCheckpoint() instanceof DriverStateSnapshot.NullValue,
                    "explicit rejected-cold new branch must follow its original reset semantics");
        }
    }
    private void requireAttempt(ContinuityStorePort.Session same,Attempt attempt)throws IOException {
        context.writer().requireSession(same);
        if(active!=attempt||attempt.same!=same||!attempt.before.digest().equals(same.head().digest()))throw new IOException("original migration attempt escaped its actual writer Head or Session");
        attempt.load.requireRetained(same);requireNative(attempt);attempt.source.assertCurrent(same);verifyPins(same,attempt);
    }
    /** Receiver-issued identity remains private runtime state; persisted equal DATA cannot recreate it. */
    static final class NativeOccurrence {
        private final NativeGameTransport transport;
        private final NativeObservationPort.ObservedFrame original;
        private final NativeGameTransport.AcceptedSnapshotRevision revision;
        private NativeOccurrence(NativeGameTransport transport,NativeObservationPort.ObservedFrame original,
                NativeGameTransport.AcceptedSnapshotRevision revision) {
            this.transport=transport;this.original=original;this.revision=revision;
        }
        static NativeOccurrence capture(NativeGameTransport transport,NativeObservationPort.ObservedFrame original)throws IOException {
            Objects.requireNonNull(transport);Objects.requireNonNull(original);
            synchronized(transport) {
                var actual=new NativeOccurrence(transport,original,transport.acceptedSnapshotRevision(original));
                actual.requireCurrent(transport);return actual;
            }
        }
        void requireCurrent(NativeGameTransport actual)throws IOException {
            if(actual!=transport)throw new IOException("original migration occurrence belongs to another actual Native receiver");
            synchronized(transport) {
                var current=transport.latestObservedSnapshot().orElseThrow(()->new IOException("actual original native packet no longer held"));
                revision.requireOriginal(original);revision.requireOriginal(current);
                var state=transport.latestStateRevision().orElseThrow(()->new IOException("actual original native current state revision unavailable"));
                require(state.kind()==NativeGameTransport.StateRevisionKind.SNAPSHOT&&state.disconnection().isEmpty()
                        &&state.session().equals(revision.session())&&state.received().equals(revision.received())
                        &&state.publicRevision().equals(revision.publicRevision()),
                        "original migration requires its actual current connected received snapshot occurrence");
                require(current.session().equals(original.session())&&current.snapshotId().equals(original.snapshotId())
                        &&current.nativeRevision().equals(original.nativeRevision())&&current.observedAt().equals(original.observedAt())
                        &&Arrays.equals(current.originalPacket(),original.originalPacket())&&Arrays.equals(current.state().bytes(),original.state().bytes()),
                        "another native packet cannot replace this original migration observation");
            }
        }
    }
    private void requireNative(Attempt attempt)throws IOException {
        context.game().verify();attempt.nativeOccurrence.requireCurrent(context.transport());
        require(attempt.nativeRaw.session().game().equals(context.game().generation())
                &&attempt.nativeRaw.session().sessionId().equals(context.game().sessionId()),"actual managed migration Game/session changed");
    }
    private void pin(ContinuityStorePort.Session same,Attempt attempt,ExactRef ref)throws IOException {
        if(attempt.pins.stream().anyMatch(pin->pin.reference().equals(ref)))return;
        var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);attempt.pins.add(pin);
    }
    private void verifyPins(ContinuityStorePort.Session same,Attempt attempt)throws IOException {for(var pin:attempt.pins)same.verifyPin(pin);}
    private SaveObservation observeSave(Path path)throws IOException {
        SharedSourceFiles.plainAncestors(path);
        try {
            var witness=SharedSourceFiles.observe(path);var ref=witness.source();
            FileWitness physical=physicalWitness(new ExactRef(ref.path(),ref.bytes(),ref.sha256()));
            SharedSourceFiles.assertUnchanged(witness);return new SaveObservation(path,Optional.of(witness),Optional.of(physical));
        }catch(NoSuchFileException absent) {
            if(java.nio.file.Files.exists(path,java.nio.file.LinkOption.NOFOLLOW_LINKS))throw absent;
            return new SaveObservation(path,Optional.empty(),Optional.empty());
        }
    }
    private void requireSave(SaveObservation source)throws IOException {
        if(source.original().isPresent()) {
            SharedSourceFiles.assertUnchanged(source.original().orElseThrow());
            require(physicalWitness(source.witness().orElseThrow().reference()).equals(source.witness().orElseThrow()),"actual cold SAVE FileID/size identity changed");
        }else {
            SharedSourceFiles.plainAncestors(source.path());
            require(!java.nio.file.Files.exists(source.path(),java.nio.file.LinkOption.NOFOLLOW_LINKS),"missing actual checkpoint became present before rejected-cold publication");
        }
    }
    private static FileWitness physicalWitness(ExactRef actual)throws IOException {
        var identity=new WindowsSavedProofIdentityReader().stat(Path.of(actual.path()));
        require(identity.bytes().equals(BigInteger.valueOf(actual.bytes())),"actual complete source size differs from its physical identity");return new FileWitness(actual,identity);
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode file(FileWitness actual) {
        return org.xar.ck3.control.application.checkpoint.CheckpointPairCodec.fileWitnessToJson(actual);
    }
    private BindingIdentity mint(Attempt attempt,BigInteger actualActor) {
        if(attempt.binding!=null){require(attempt.binding.characterId().equals(actualActor),"one original attempt cannot mint another character binding");return attempt.binding;}
        var basis=StrictJson.object();basis.put("request_id",attempt.load.frozenProfile().request().requestId());basis.put("head",attempt.before.digest());
        basis.set("original_driver",attempt.originalDriver.toJson());basis.set("original_native",attempt.originalNative.toJson());basis.put("actor",actualActor);
        return new BindingIdentity(actualActor,"native-"+actualActor+"-"+ContinuityJson.digest(basis).substring(0,12));
    }
    private FrozenLifecycle frozenLifecycle(Attempt attempt)throws IOException {
        return attempt.load.frozenLifecycleProjection();
    }
    private Value lifecycle(Attempt attempt)throws IOException {return LegacyResumeMigration.lifecycleData(frozenLifecycle(attempt));}
    private static Obj withoutMigrationFlags(Obj payload) {
        var fields=new LinkedHashMap<>(payload.members());fields.remove("succession_lifecycle_migration_required");fields.remove("rollback_war_failures_migration_required");return new Obj(fields);
    }
    private static boolean mapReady(Obj nativeState){return new Bool(true).equals(nativeState.get("map_ready"));}
    private static Optional<BigInteger> actor(Obj nativeState) {
        if(!(nativeState.get("played_character") instanceof Obj played)||!(played.get("character_id") instanceof IntegerValue id))return Optional.empty();
        return Optional.of(NativeCharacterId.of(id.value()).asBigInteger());
    }
    private static List<Obj> objects(Arr rows){var result=new ArrayList<Obj>();for(Value value:rows.items())result.add(object(value,"complete legacy row"));return List.copyOf(result);}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Awaiting awaiting(Attempt attempt,String reason){return new Awaiting(reason,List.of(attempt.originalDriver,attempt.canonicalOriginal,attempt.originalNative,attempt.canonicalNative));}
    private static void require(boolean condition,String diagnostic){StrictJson.require(condition,diagnostic);}
}
