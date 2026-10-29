package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.history.DriverHistoryProjection;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePlayerEventTraitMembership;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One replacement, raw map proof, original-lock attachment, full Driver publication, then admission. */
public final class RestoreCheckpointService {
    private static final int MAX_NATIVE_BYTES = DriverJson.MAX_NATIVE_BYTES;
    public record Request(String requestId, CheckpointPair pair, CheckpointRequest.Readiness current,
            String expectedHeadDigest, Instant deadline,SavedCheckpointMaterial savedMaterial) {
        public Request {
            StrictJson.text(requestId); Objects.requireNonNull(pair); Objects.requireNonNull(current); Objects.requireNonNull(deadline);Objects.requireNonNull(savedMaterial);
            StrictJson.require(pair.equals(savedMaterial.pair()),"restore must carry its original private typed saved material");
            StrictJson.require(expectedHeadDigest != null && expectedHeadDigest.matches("[0-9a-f]{64}"), "exact original ledger head");
            StrictJson.require(pair.frame().machineId().equals(current.observed().machineId()) && pair.lineageId().equals(current.lineageId())
                    && pair.frame().frame().episodeRunId().equals(current.observed().frame().episodeRunId()), "restore remains in the original machine/lineage/episode");
        }
    }
    public sealed interface LaunchResult permits ReplacementAck, LaunchRejected, LaunchUnknown { }
    public record ReplacementAck(String requestId, GameGeneration previous, GameGeneration replacement,
            ExactRef loadedSave, ExactRef lifecycleEvidence) implements LaunchResult {
        public ReplacementAck {
            StrictJson.text(requestId); Objects.requireNonNull(previous); Objects.requireNonNull(replacement);
            Objects.requireNonNull(loadedSave); Objects.requireNonNull(lifecycleEvidence);
            StrictJson.require(!previous.equals(replacement) && lifecycleEvidence.bytes() > 0, "actual replacement generation and evidence");
        }
    }
    public record LaunchRejected(String reason) implements LaunchResult { public LaunchRejected { StrictJson.text(reason); } }
    public record LaunchUnknown(String reason) implements LaunchResult { public LaunchUnknown { StrictJson.text(reason); } }
    public interface LifecyclePort {
        LaunchResult replaceOnce(Request request) throws IOException, InterruptedException;
        LaunchResult query(String requestId, Instant deadline) throws IOException, InterruptedException;
    }
    /** Raw facts from the replacement's own transport. This value grants no planning or session authority. */
    public record NativeCandidate(NativeObservationPort.ObservedFrame actual, G2Source source,
            String lineageId, ExactRef originalNativePacket) {
        public NativeCandidate {
            Objects.requireNonNull(actual); Objects.requireNonNull(source); StrictJson.text(lineageId); Objects.requireNonNull(originalNativePacket);
        }
    }
    @FunctionalInterface public interface RestoreNativePort {
        NativeCandidate observe(ReplacementAck replacement, ReadWindow reads) throws IOException, InterruptedException;
        /** Only the actual receiver may qualify the two original independent READs. */
        default IndependentReadPair requireIndependentPair(ReplacementAck replacement,NativeCandidate first,NativeCandidate second)throws IOException {
            throw new IOException("actual independent restore READ custody unavailable");
        }
        /** Historical archive verification only; it must not observe or dispatch. */
        default void requireHistoricalPair(ContinuityStorePort.Session same,ReplacementAck replacement,IndependentReadPair original)throws IOException {
            throw new IOException("original independent restore READ custody unavailable");
        }
    }
    /** Archive DATA only. Constructing these locators cannot create receiver or restoration authority. */
    public record IndependentReadPair(ExactRef manifest,ExactRef firstAck,ExactRef firstNative,ExactRef secondAck,ExactRef secondNative) {
        public IndependentReadPair {
            for(ExactRef ref:java.util.List.of(manifest,firstAck,firstNative,secondAck,secondNative))
                StrictJson.require(ref.bytes()>0&&ref.bytes()<=WriterContracts.MAX_PIN_BYTES,"bounded nonempty original restore READ artifact required");
            StrictJson.require(manifest.bytes()<=65536&&!firstAck.equals(secondAck)&&!firstNative.equals(secondNative),
                    "two independent original READ ACKs and native packets required");
            StrictJson.require(java.util.Set.of(manifest,firstAck,firstNative,secondAck,secondNative).size()==5,"restore READ archive roles must be distinct");
        }
        public java.util.List<ExactRef> references(){return java.util.List.of(manifest,firstAck,firstNative,secondAck,secondNative);}
    }
    public record Attachment(WriterContracts.Request request, SavedContinuityAttachment.Input input,SavedCheckpointMaterial material) {
        public Attachment { Objects.requireNonNull(request); Objects.requireNonNull(input);Objects.requireNonNull(material); }
    }
    /** Prepares the canonical source-bound attachment and full after-Driver delta from actual raw facts. */
    @FunctionalInterface public interface AttachmentPort {
        Attachment prepare(Request request, NativeCandidate restored, DriverStateSnapshot.Complete originalSavedDriver, ReadWindow reads) throws IOException;
    }
    public record PublishedDriver(DriverStateSnapshot.Complete driver, long episodeEpoch, ExactRef originalHistoryBasis,
            CheckpointRequest.Readiness readiness, SemanticEvidence semantic) {
        public PublishedDriver {
            Objects.requireNonNull(driver); StrictJson.safe(episodeEpoch, 0); Objects.requireNonNull(originalHistoryBasis);
            Objects.requireNonNull(readiness); Objects.requireNonNull(semantic);
            StrictJson.require(originalHistoryBasis.bytes() > 0, "actual complete surviving history basis required");
        }
    }
    /** Adopts a new Driver authority only from the actual same-writer commit, then runs its full collector. */
    public interface PublicationPort {
        PublishedDriver publish(Request request, NativeCandidate restored, DriverStateSnapshot.Complete originalSavedDriver,
                WriterContracts.Prepared prepared, WriterContracts.Receipt committed, ReadWindow reads) throws IOException;
        void requireCurrent(PublishedDriver published, NativeCandidate restored, WriterContracts.Receipt committed, ReadWindow reads) throws IOException;
    }
    /** Only this service can mint admission. A record constructor, ACK, or seed copy cannot mint it. */
    public static final class RestoreBinding {
        private final RestoreCheckpointService issuer;
        private final Request request;
        private final ReplacementAck replacement;
        private final PublishedDriver published;
        private final WriterContracts.Receipt attachment;
        private final WriterContracts.Prepared originalPrepared;
        private final NativeCandidate originalNative;
        private final NativeCandidate publicationNative;
        private final IndependentReadPair originalReadPair;
        private final SessionIdentity session;
        private final long committedSavedDays;
        private ReboundOrigin reboundOrigin;
        private RestoreBinding(RestoreCheckpointService issuer, Request request, ReplacementAck replacement,
                PublishedDriver published, WriterContracts.Receipt attachment, WriterContracts.Prepared originalPrepared, NativeCandidate originalNative,NativeCandidate publicationNative,IndependentReadPair originalReadPair) {
            this.issuer = issuer; this.request = request; this.replacement = replacement;
            this.published = published; this.attachment = attachment;
            this.originalPrepared=Objects.requireNonNull(originalPrepared);this.originalNative=Objects.requireNonNull(originalNative);
            this.publicationNative=Objects.requireNonNull(publicationNative);
            this.originalReadPair=Objects.requireNonNull(originalReadPair);
            var ready = published.readiness(); session = new SessionIdentity(ready.observed().machineId(), ready.observed().game(), ready.sessionId());
            long delta = Math.subtractExact(attachment.head().settledDateRaw(), attachment.head().origin().startDateRaw());
            StrictJson.require(delta >= 0 && delta % 24 == 0, "existing committed saved frontier must contain whole forward days");
            committedSavedDays = delta / 24;
        }
        /** A private query/read window of this original attempt; this does not renew the lifecycle action. */
        public ReadWindow readWindow() throws IOException { return issuer.currentReadWindow(this); }
        public SavedCheckpointMaterial savedMaterial(){return request.savedMaterial();}
        public SessionIdentity session() { return session; }
        public DriverStateSnapshot.Complete driver() { return published.driver(); }
        public CheckpointPair pair() { return request.pair(); }
        public long episodeEpoch() { return published.episodeEpoch(); }
        public String episodeRunId() { return published.driver().session().episodeRunId(); }
        public G2Source source() { return published.readiness().source(); }
        public SemanticEvidence semantic() { return published.semantic(); }
        public ExactRef originalHistoryBasis() { return published.originalHistoryBasis(); }
        public WriterContracts.Receipt attachment() { return attachment; }
        /** Read-only original transaction custody; this value cannot admit another restoration. */
        public WriterContracts.Prepared originalAttachment() { return originalPrepared; }
        public IndependentReadPair originalReadPair(){return originalReadPair;}
        public long committedSavedDays() { return committedSavedDays; }
        public long newSavedDayCredit() { return 0; }
        /** Original private actual SAVE-to-LOAD custody, not a current physical or Native qualification. */
        public ReboundOrigin requireReboundOrigin(ContinuityStorePort.Session same)throws IOException {
            return issuer.requireReboundOrigin(same,this);
        }
    }
    /** Private actual-restoration origin. Serialized DATA cannot construct or recover this object. */
    public static final class ReboundOrigin {
        private final RestoreCheckpointService issuer;
        private final RestoreBinding binding;
        private final RestoredEpisodeOriginData evidence;
        private ReboundOrigin(RestoreCheckpointService issuer,RestoreBinding binding,RestoredEpisodeOriginData evidence) {
            this.issuer=issuer;this.binding=binding;this.evidence=evidence;
        }
        public RestoredEpisodeOriginData evidence(){return evidence;}
        public void requireOriginal(ContinuityStorePort.Session same)throws IOException {
            StrictJson.require(issuer.requireReboundOrigin(same,binding)==this,"restoration origin lost its actual private issuer/binding");
        }
        public long newSavedDayCredit(){return 0;}
        public long newCycleCredit(){return 0;}
    }
    public sealed interface Result permits Restored, Rejected, Unknown { }
    public record Restored(CheckpointPair pair, CheckpointRequest.Readiness nativePoststate,
            ReplacementAck lifecycleAck, WriterContracts.Receipt attachment, RestoreBinding binding) implements Result {
        public Restored {
            Objects.requireNonNull(pair); Objects.requireNonNull(nativePoststate); Objects.requireNonNull(lifecycleAck);
            Objects.requireNonNull(attachment); Objects.requireNonNull(binding);
            StrictJson.require(binding.pair().equals(pair) && binding.attachment().equals(attachment)
                    && binding.published.readiness().equals(nativePoststate) && binding.replacement.equals(lifecycleAck), "restored result binds its privately admitted source");
        }
    }
    public record Rejected(String reason) implements Result { public Rejected { StrictJson.text(reason); } }
    public record Unknown(String requestId, String reason) implements Result { public Unknown { StrictJson.text(requestId); StrictJson.text(reason); } }
    private static final class Attempt {
        private final Request request;
        private volatile boolean launched;
        private boolean entered;
        private volatile ReadWindow reads;
        private ReplacementAck replacement;
        private NativeCandidate candidate;
        private IndependentReadPair originalReadPair;
        private WriterContracts.Prepared prepared;
        private WriterContracts.Receipt committed;
        private RestoreBinding binding;
        private Attempt(Request request) { this.request = request; }
    }
    /** Private issuer-bound read scope. The original lifecycle Request is never replaced or extended. */
    public static final class ReadWindow {
        private final RestoreCheckpointService issuer;
        private final Attempt attempt;
        private final Instant deadline;
        private final boolean queryOnly;
        private ReadWindow(RestoreCheckpointService issuer,Attempt attempt,Instant deadline,boolean queryOnly) {
            this.issuer=issuer;this.attempt=attempt;this.deadline=deadline;this.queryOnly=queryOnly;
        }
        public Request original(){return attempt.request;}
        public Instant deadline(){return deadline;}
        public boolean queryOnly(){return queryOnly;}
        /** Exact private lifecycle result of this attempt, never an ACK reconstructed from DATA. */
        public void requireReplacement(ReplacementAck actual)throws IOException {
            requireOriginal(attempt.request);
            if(actual!=attempt.replacement)throw new IOException("restore READ requires the exact original private replacement ACK");
            requireAck(attempt.request,actual);
        }
        /** This proves only the current finite read scope of the actual original private attempt. */
        public void requireOriginal(Request exact)throws IOException {
            if(exact!=attempt.request||issuer.attempts.get(exact.requestId())!=attempt||attempt.reads!=this
                    ||!issuer.clock.instant().isBefore(deadline)||(queryOnly&&!attempt.launched))
                throw new IOException("original restore read window is stale, foreign, expired or has no entered lifecycle");
        }
    }
    private ReadWindow openReadWindow(Attempt actual,Instant deadline,boolean queryOnly)throws IOException {
        Objects.requireNonNull(deadline);
        Instant now=clock.instant();
        if(!now.isBefore(deadline)||Duration.between(now,deadline).compareTo(Duration.ofMinutes(30))>0)
            throw new IOException("fresh finite restore read deadline required");
        if(attempts.get(actual.request.requestId())!=actual||(queryOnly&&!actual.launched))
            throw new IOException("query requires this service's actual already-entered original lifecycle attempt");
        ReadWindow reads=new ReadWindow(this,actual,deadline,queryOnly);actual.reads=reads;return reads;
    }
    private ReadWindow currentReadWindow(RestoreBinding binding)throws IOException {
        Attempt actual=issuedAttempt(binding);
        ReadWindow reads=actual.reads;
        if(reads==null)throw new IOException("original restoration has no retained read scope");
        reads.requireOriginal(binding.request);return reads;
    }
    private Attempt issuedAttempt(RestoreBinding binding)throws IOException {
        Objects.requireNonNull(binding);
        Attempt actual=attempts.get(binding.request.requestId());
        if(binding.issuer!=this||actual==null||actual.binding!=binding)
            throw new IOException("foreign or unretained restoration binding");
        return actual;
    }
    private final CheckpointFiles files;
    private final DriverCheckpointStore drivers;
    private final LifecyclePort lifecycle;
    private final RestoreNativePort nativeFrames;
    private final ContinuityStorePort writer;
    private final SavedCheckpointMaterialStore materials;
    private final AttachmentPort attachments;
    private final PublicationPort publications;
    private final Clock clock;
    private final ConcurrentHashMap<String, Attempt> attempts = new ConcurrentHashMap<>();
    public RestoreCheckpointService(CheckpointFiles files, DriverCheckpointStore drivers, LifecyclePort lifecycle,
            RestoreNativePort nativeFrames, ContinuityStorePort writer, SavedCheckpointMaterialStore materials, AttachmentPort attachments,PublicationPort publications, Clock clock) {
        this.files = Objects.requireNonNull(files); this.drivers = Objects.requireNonNull(drivers); this.lifecycle = Objects.requireNonNull(lifecycle);
        this.nativeFrames = Objects.requireNonNull(nativeFrames); this.writer = Objects.requireNonNull(writer); this.materials = Objects.requireNonNull(materials);
        this.attachments=Objects.requireNonNull(attachments);this.publications = Objects.requireNonNull(publications); this.clock = Objects.requireNonNull(clock);
        StrictJson.require(attachments==publications,"actual restore preparation and publication must retain the same private stage owner");
    }
    public Result restore(Request request) throws InterruptedException {
        Objects.requireNonNull(request);
        Attempt actual=attempts.computeIfAbsent(request.requestId(),ignored->new Attempt(request));
        synchronized(actual){
            try{
                StrictJson.require(actual.request.equals(request),"same restore request ID changed its exact body");
                if(actual.entered&&!actual.launched)
                    return new Unknown(request.requestId(),"original pre-dispatch source failure retained; no new lifecycle call");
                actual.entered=true;
                return executeOriginal(actual,openReadWindow(actual,request.deadline(),false));
            }catch(IOException|IllegalArgumentException|ArithmeticException failure){return new Unknown(request.requestId(),failure.toString());}
        }
    }
    /** Reads/resolves only an existing entered lifecycle. It cannot create a Request or call replaceOnce. */
    public Result queryOriginal(String requestId,Instant readDeadline)throws InterruptedException {
        StrictJson.text(requestId);Objects.requireNonNull(readDeadline);
        Attempt actual=attempts.get(requestId);
        if(actual==null)return new Unknown(requestId,"no original private restore attempt is retained; zero dispatch");
        synchronized(actual){
            try{return executeOriginal(actual,openReadWindow(actual,readDeadline,true));}
            catch(IOException|IllegalArgumentException|ArithmeticException failure){return new Unknown(requestId,failure.toString());}
        }
    }
    private Result executeOriginal(Attempt stage,ReadWindow reads)throws InterruptedException {
        Request request=stage.request;
        try {
                reads.requireOriginal(request);
                materials.requireOwn(request.savedMaterial());
                DriverStateSnapshot.Complete saved = request.savedMaterial().savedDriver();
                StrictJson.require(Arrays.equals(saved.encode(),drivers.readVerifiedOriginal(request.pair(),saved.session()).encode()),"original complete saved Driver changed");
                if (stage.binding != null) {
                    requireRetainedQuery(stage.binding,reads);return result(stage.binding);
                }
                if (stage.replacement == null) {
                    writer.locked(session -> { StrictJson.require(session.head().digest().equals(request.expectedHeadDigest()), "original restore head drift before lifecycle");
                        materials.requireRestorePredecessor(session,request.savedMaterial());
                        return null; });
                    boolean alreadyLaunched = stage.launched;
                    // Record before the call: an exception after native dispatch can only lead to query.
                    reads.requireOriginal(request);
                    if(reads.queryOnly()&&!alreadyLaunched)throw new IOException("query scope cannot issue a lifecycle replacement");
                    stage.launched = true;
                    LaunchResult launch = alreadyLaunched ? lifecycle.query(request.requestId(), reads.deadline()) : lifecycle.replaceOnce(request);
                    if (launch instanceof LaunchRejected rejection) return new Rejected(rejection.reason());
                    if (!(launch instanceof ReplacementAck actual)) return new Unknown(request.requestId(), "lifecycle unresolved; query only, never relaunch");
                    requireAck(request, actual); stage.replacement = actual;
                }
                NativeCandidate first = nativeFrames.observe(stage.replacement, reads);
                NativeCandidate current = nativeFrames.observe(stage.replacement, reads);
                requireNative(request, stage.replacement, first); requireNative(request, stage.replacement, current);
                StrictJson.require(sameRawIdentity(first, current), "replacement paused map changed between independent raw observations");
                IndependentReadPair actualPair=nativeFrames.requireIndependentPair(stage.replacement,first,current);
                requireStableReadProgression(first.actual(),current.actual());
                if (stage.candidate != null) {
                    StrictJson.require(sameRawIdentity(stage.candidate, current), "restore source changed after original prepare");
                    requireStableReadProgression(stage.candidate.actual(),current.actual());
                } else {
                    // Keep the first qualified opening even if the attachment producer succeeds but preview later fails.
                    stage.candidate=current;stage.originalReadPair=actualPair;
                }
                if (stage.prepared == null) {
                    writer.locked(session -> {
                        StrictJson.require(session.head().digest().equals(request.expectedHeadDigest()), "original restore head changed before prepare");
                        // SourceStore borrows this exact existing session to reread the original SAVE/SEM material.
                        // Preparing outside it would either lose source custody or acquire a second writer lock.
                        materials.requireOwn(request.savedMaterial());request.savedMaterial().requirePhysical(session);
                        reads.requireOriginal(request);
                        nativeFrames.requireHistoricalPair(session,stage.replacement,stage.originalReadPair);
                        Attachment source = attachments.prepare(request, stage.candidate, saved,reads);
                        StrictJson.require(SavedAttachmentAuthority.kinds().contains(source.request().kind())
                                &&source.material().kind()==request.savedMaterial().kind()&&source.material().witness().equals(request.savedMaterial().witness())
                                && SavedAttachmentAuthority.pairFromDetails(source.request()).equals(request.pair()), "original attachment kind and exact physical pair required");
                        var reduced = SavedContinuityAttachment.reduce(source.input());
                        StrictJson.require(ContinuityJson.digest(source.input().predecessor().toJson()).equals(request.expectedHeadDigest()), "original restore predecessor");
                        // Preserve the actual lifecycle artifact identity in the one original canonical attachment.
                        // Details/identity and the sole reducer are unchanged; old hash-only origins cannot gain this pin later.
                        var evidence=new java.util.LinkedHashSet<ExactRef>(source.request().evidence());
                        evidence.add(stage.replacement.lifecycleEvidence());
                        evidence.addAll(stage.originalReadPair.references());
                        var pinnedRequest=new WriterContracts.Request(source.request().kind(),source.request().details(),java.util.List.copyOf(evidence));
                        reads.requireOriginal(request);var prepared = session.preview(pinnedRequest);
                        StrictJson.require(ContinuityJson.same(prepared.reduced().toJson(), reduced.toJson()), "real original reducer and same-lock writer preview disagree");
                        stage.prepared = prepared; return null;
                    });
                }
                if (stage.committed == null) {
                    // The writer's event identity makes recovery idempotent even if commit returned no receipt.
                    stage.committed = writer.locked(session -> {reads.requireOriginal(request);
                        nativeFrames.requireHistoricalPair(session,stage.replacement,stage.originalReadPair);return session.commit(stage.prepared);});
                }
                StrictJson.require(stage.committed.disposition() != WriterContracts.Disposition.NO_CHANGE
                        && stage.committed.eventIdentity().equals(stage.prepared.request().identity()), "actual original attachment event commit required");
                PublishedDriver published = publications.publish(request, current, saved, stage.prepared, stage.committed,reads);
                requirePublished(request, stage.replacement, current, published);
                RestoreBinding binding = new RestoreBinding(this, request, stage.replacement, published, stage.committed, stage.prepared, stage.candidate,current,stage.originalReadPair);
                requireCurrentWithWindow(binding,reads);stage.binding = binding; return result(binding);

        }catch(IOException|IllegalArgumentException|ArithmeticException failure){
            return new Unknown(request.requestId(),failure.toString());
        }
    }
    /** Root calls this again immediately before replacing its controller; stale bindings cannot admit a session. */
    public void requireCurrent(RestoreBinding binding, Instant deadline) throws IOException, InterruptedException {
        Attempt actual=issuedAttempt(binding);
        synchronized(actual){requireCurrentWithWindow(binding,openReadWindow(actual,deadline,true));}
    }
    private void requireCurrentWithWindow(RestoreBinding binding,ReadWindow reads)throws IOException,InterruptedException {
        reads.requireOriginal(binding.request);
        StrictJson.require(binding.issuer==this,"original service admission required");
        drivers.verifyOriginal(binding.pair(),binding.savedMaterial().savedDriver().session());
        NativeCandidate actual=nativeFrames.observe(binding.replacement,reads);
        requireNative(binding.request,binding.replacement,actual);
        // The historical publication remains self-consistent; a later READ is a different publication occurrence.
        requirePublished(binding.request,binding.replacement,binding.publicationNative,binding.published);
        StrictJson.require(sameRawIdentity(binding.publicationNative,actual),"restored raw state changed after actual publication");
        requireStableReadProgression(binding.publicationNative.actual(),actual.actual());
        writer.locked(session->{
            reads.requireOriginal(binding.request);
            StrictJson.require(session.head().digest().equals(ContinuityJson.digest(binding.attachment.head().toJson())),
                    "same canonical writer head drifted after restore publication");
            publications.requireCurrent(binding.published,actual,binding.attachment,reads);
            materials.requireOwn(binding.savedMaterial());binding.savedMaterial().requirePhysical(session);
            drivers.verifyOriginal(binding.pair(),binding.savedMaterial().savedDriver().session());return null;
        });
    }
    /** A retained result after actual domain imports is an original fact, not renewed current admission. */
    private void requireRetainedQuery(RestoreBinding binding,ReadWindow reads)throws IOException,InterruptedException {
        reads.requireOriginal(binding.request);issuedAttempt(binding);
        writer.locked(same->{
            requireRetainedOriginal(same,binding);
            materials.requireOwn(binding.savedMaterial());binding.savedMaterial().requirePhysical(same);return null;
        });
        NativeCandidate actual=nativeFrames.observe(binding.replacement,reads);
        requireNative(binding.request,binding.replacement,actual);
        reads.requireOriginal(binding.request);
    }
    /**
     * Historical custody of an already admitted private restoration, under the caller's real writer.
     * Normal later domain writes and a later physical SAVE do not erase this original fact.
     * This method grants no current Game/readiness, physical reload, replay or new episode authority.
     */
    public void requireRetainedOriginal(ContinuityStorePort.Session borrowed, RestoreBinding binding) throws IOException {
        Objects.requireNonNull(binding);writer.requireSession(borrowed);
        StrictJson.require(binding.issuer==this,"foreign restoration source cannot acquire retained provenance");
        Attempt original=attempts.get(binding.request.requestId());
        StrictJson.require(original!=null&&original.binding==binding&&original.prepared==binding.originalPrepared
                &&original.committed==binding.attachment&&original.replacement==binding.replacement,
                "the original private admitted restoration custody is unavailable");
        materials.requireOwn(binding.savedMaterial());binding.savedMaterial().requireRetained(borrowed);
        String before=borrowed.head().digest();var prepared=binding.originalPrepared;var committed=binding.attachment;
        StrictJson.require(committed.disposition()!=WriterContracts.Disposition.NO_CHANGE
                &&committed.eventIdentity().equals(prepared.request().identity())
                &&SavedAttachmentAuthority.kinds().contains(prepared.request().kind())
                &&SavedAttachmentAuthority.pairFromDetails(prepared.request()).equals(binding.pair()),
                "retained restoration differs from its actual original attachment transaction");
        borrowed.requireHistoricalState(prepared.predecessor().state().sequence(),prepared.predecessor().digest());
        borrowed.requireHistoricalState(committed.head().sequence(),ContinuityJson.digest(committed.head().toJson()));
        StrictJson.require(original.originalReadPair==binding.originalReadPair,"original private restore READ pair changed");
        for(ExactRef ref:binding.originalReadPair.references())readOriginalAttachment(borrowed,prepared,ref,MAX_NATIVE_BYTES+4);
        nativeFrames.requireHistoricalPair(borrowed,binding.replacement,binding.originalReadPair);
        StrictJson.require(committed.head().sequence()==Math.addExact(prepared.predecessor().state().sequence(),1),
                "retained restoration must be the actual immediate original attachment successor");
        readExact(binding.replacement.lifecycleEvidence(),MAX_NATIVE_BYTES+4);
        StrictJson.require(Arrays.equals(readExact(binding.originalNative.originalNativePacket(),MAX_NATIVE_BYTES+4),
                binding.originalNative.actual().originalPacket()),"retained restored native packet changed");
        StrictJson.require(Arrays.equals(readExact(binding.publicationNative.originalNativePacket(),MAX_NATIVE_BYTES+4),
                binding.publicationNative.actual().originalPacket()),"retained restore publication packet changed");
        for(ExactRef ref:binding.semantic().references())readExact(ref,DriverCheckpointStore.MAX_DRIVER_BYTES);
        readExact(binding.originalHistoryBasis(),DriverCheckpointStore.MAX_DRIVER_BYTES);
        var originalDriver=DriverStateSnapshot.decodeComplete(readExact(binding.semantic().originalDriver(),DriverCheckpointStore.MAX_DRIVER_BYTES));
        StrictJson.require(Arrays.equals(originalDriver.encode(),binding.driver().encode())
                &&binding.semantic().frame().game().equals(binding.replacement.replacement())
                &&binding.semantic().frame().machineId().equals(binding.session().machineId())
                &&binding.driver().session().bridgePid()==binding.session().game().pid()
                &&binding.driver().session().episodeRunId().equals(binding.pair().frame().frame().episodeRunId())
                &&binding.driver().session().actorId().equals(binding.pair().frame().frame().identity().player()),
                "retained restoration lost its originally published complete Driver/session/episode sources");
        StrictJson.require(before.equals(borrowed.head().digest()),"retained restoration verification mutated canonical head");
        writer.requireSession(borrowed);
    }
    /** Lookup cannot submit, reconstruct or issue an origin for an UNKNOWN or missing actual restoration. */
    public java.util.Optional<ReboundOrigin> originalReboundOrigin(ContinuityStorePort.Session same,String requestId)throws IOException {
        writer.requireSession(same);StrictJson.text(requestId);var actual=attempts.get(requestId);
        if(actual==null)return java.util.Optional.empty();
        synchronized(actual) {
            return actual.binding==null?java.util.Optional.empty():java.util.Optional.of(requireReboundOrigin(same,actual.binding));
        }
    }
    public ReboundOrigin requireReboundOrigin(ContinuityStorePort.Session same,RestoreBinding binding)throws IOException {
        writer.requireSession(same);Attempt actual=issuedAttempt(binding);
        synchronized(actual) {
            String head=same.head().digest();requireRetainedOriginal(same,binding);
            var prepared=binding.originalPrepared;var source=SavedAttachmentSourceStore.Sources.decode(
                    prepared.request().detailsObject().get(SavedAttachmentSourceStore.SOURCES_DETAIL));
            StrictJson.require(source.kind()==binding.savedMaterial().kind()&&source.material().equals(binding.savedMaterial().witness())
                    &&SavedAttachmentAuthority.pairFromDetails(prepared.request()).equals(binding.pair()),
                    "restoration origin requires the identical original typed SAVE material and physical pair");
            var reduced=SavedContinuityAttachment.reduce(new SavedContinuityAttachment.Input(prepared.predecessor().state(),prepared.request().details(),
                    readOriginalAttachment(same,prepared,source.basis(),1024*1024),readOriginalAttachment(same,prepared,source.game(),1024*1024),
                    readOriginalAttachment(same,prepared,source.opening(),1024*1024),readOriginalAttachment(same,prepared,source.progress(),1024*1024))).toJson();
            reduced.put("sequence",binding.attachment.head().sequence());reduced.put("last_event_identity",prepared.request().identity());
            StrictJson.require(ContinuityJson.same(reduced,binding.attachment.head().toJson()),
                    "sole restore reducer must reproduce the actual original canonical restored successor");
            var lifecyclePin=originalAttachmentPin(prepared,binding.replacement.lifecycleEvidence());
            var nativePin=originalAttachmentPin(prepared,binding.originalNative.originalNativePacket());
            readOriginalAttachment(same,prepared,lifecyclePin.reference(),MAX_NATIVE_BYTES+4);
            readOriginalAttachment(same,prepared,nativePin.reference(),MAX_NATIVE_BYTES+4);
            var previous=new SessionIdentity(binding.request.current().observed().machineId(),binding.request.current().observed().game(),binding.request.current().sessionId());
            var evidence=new RestoredEpisodeOriginData(binding.request.requestId(),binding.savedMaterial().session(),previous,binding.session(),
                    binding.originalNative.actual().session().connectionGeneration().toString(),binding.source(),binding.pair(),binding.savedMaterial().witness(),
                    binding.savedMaterial().originalHeadDigest(),binding.attachment.head().sequence(),ContinuityJson.digest(binding.attachment.head().toJson()),
                    binding.attachment.eventIdentity(),lifecyclePin,nativePin,binding.semantic(),binding.originalHistoryBasis());
            StrictJson.require(java.util.Arrays.equals(evidence.encode(),RestoredEpisodeOriginData.decode(evidence.encode()).encode()),
                    "actual restoration original DATA must round trip without changing identity or JSON types");
            if(binding.reboundOrigin==null)binding.reboundOrigin=new ReboundOrigin(this,binding,evidence);
            else StrictJson.require(binding.reboundOrigin.evidence.equals(evidence),"actual retained restoration original changed");
            StrictJson.require(head.equals(same.head().digest()),"restoration origin verification changed the canonical writer head");
            writer.requireSession(same);return binding.reboundOrigin;
        }
    }
    private static WriterContracts.Pin originalAttachmentPin(WriterContracts.Prepared actual,ExactRef reference)throws IOException {
        return java.util.stream.Stream.concat(actual.sources().stream(),actual.evidence().stream())
                .filter(pin->pin.reference().equals(reference)).findFirst()
                .orElseThrow(()->new IOException("actual original restore artifact FileID was not captured by its canonical attachment: "+reference.path()));
    }
    private static byte[] readOriginalAttachment(ContinuityStorePort.Session same,WriterContracts.Prepared actual,
            ExactRef reference,int maximum)throws IOException {
        StrictJson.require(reference.bytes()>0&&reference.bytes()<=maximum,"bounded actual restore artifact required");
        var pin=originalAttachmentPin(actual,reference);byte[] bytes=same.readPinned(pin,Math.toIntExact(reference.bytes()));same.verifyPin(pin);return bytes;
    }
    /** Explicit same-writer source custody for a genuinely admitted FIRST replacement. No new restore or SAVE is submitted. */
    public SavedFirstCheckpointMaterialStore.BaselinedMaterial reopenFirstMaterial(ContinuityStorePort.Session same,
            RestoreBinding binding,SavedCheckpointMaterialStore target,SessionIdentity actualReplacement,
            SemanticEvidence actualReplacementSemantic)throws IOException {
        Objects.requireNonNull(target);Objects.requireNonNull(actualReplacement);Objects.requireNonNull(actualReplacementSemantic);
        requireRetainedOriginal(same,binding);
        StrictJson.require(target!=materials&&binding.session().equals(actualReplacement)
                &&binding.semantic().equals(actualReplacementSemantic),
                "FIRST custody must enter a distinct actually bound replacement aggregate with its real restored session/SEM");
        if(!(binding.savedMaterial() instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial original))
            throw new IOException("ordinary material cannot enter the FIRST restored-custody branch");
        firstBaselinePredecessor(same,original);original.requirePhysical(same);
        same.requireDomainImportContinuation(binding.attachment().head().sequence(),ContinuityJson.digest(binding.attachment().head().toJson()));
        var actual=materials.loadHistoricalOriginal(same,binding.originalPrepared,original);
        StrictJson.require(actual.material().kind()==SavedCheckpointMaterial.Kind.FIRST_BASELINE
                &&actual.material().witness().equals(original.witness())&&actual.pair().equals(original.pair()),
                "actual FIRST original reducer sources changed before custody transfer");
        var replayed=SavedContinuityAttachment.reduce(actual.input()).toJson();
        replayed.put("sequence",binding.attachment().head().sequence());
        replayed.put("last_event_identity",binding.originalPrepared.request().identity());
        StrictJson.require(ContinuityJson.same(replayed,binding.attachment().head().toJson()),
                "actual original FIRST reducer no longer produces its canonical restored successor");
        var custody=new FirstReopenCustody(this,binding,target,original);
        var reopened=target.reopenFirstOriginal(same,custody);
        target.requireOwn(reopened);reopened.requirePhysical(same);return reopened;
    }
    /** Same-writer custody import of an actual admitted ordinary restoration. No SAVE or lifecycle action is sent. */
    public SavedAttachmentSourceStore.SavedMaterial reopenOrdinaryMaterial(ContinuityStorePort.Session same,
            RestoreBinding binding,SavedCheckpointMaterialStore target,SessionIdentity actualReplacement,
            SemanticEvidence actualReplacementSemantic)throws IOException {
        Objects.requireNonNull(target);Objects.requireNonNull(actualReplacement);Objects.requireNonNull(actualReplacementSemantic);
        requireRetainedOriginal(same,binding);
        StrictJson.require(target!=materials&&binding.session().equals(actualReplacement)
                &&binding.semantic().equals(actualReplacementSemantic),
                "ordinary custody requires a distinct actually bound replacement aggregate and real restored session/SEM");
        if(!(binding.savedMaterial() instanceof SavedAttachmentSourceStore.SavedMaterial original))
            throw new IOException("FIRST material cannot enter ordinary restored custody");
        original.requirePhysical(same);
        same.requireDomainImportContinuation(binding.attachment().head().sequence(),ContinuityJson.digest(binding.attachment().head().toJson()));
        var actual=materials.loadHistoricalOriginal(same,binding.originalPrepared,original);
        StrictJson.require(actual.material().kind()==SavedCheckpointMaterial.Kind.ORDINARY
                &&actual.material().witness().equals(original.witness())&&actual.pair().equals(original.pair()),
                "ordinary original reducer sources changed before custody transfer");
        var replayed=SavedContinuityAttachment.reduce(actual.input()).toJson();
        replayed.put("sequence",binding.attachment().head().sequence());
        replayed.put("last_event_identity",binding.originalPrepared.request().identity());
        StrictJson.require(ContinuityJson.same(replayed,binding.attachment().head().toJson()),
                "original ordinary reducer no longer produces its canonical restored successor");
        var custody=new OrdinaryReopenCustody(this,binding,target,original);
        var reopened=target.reopenOrdinaryOriginal(same,custody);
        target.requireOwn(reopened);reopened.requirePhysical(same);return reopened;
    }
    /** Only this genuine admitted service can mint ordinary custody. A reference or foreign material is insufficient. */
    static final class OrdinaryReopenCustody {
        private final RestoreCheckpointService issuer;private final RestoreBinding binding;
        private final SavedCheckpointMaterialStore target;private final SavedAttachmentSourceStore.SavedMaterial original;
        private OrdinaryReopenCustody(RestoreCheckpointService issuer,RestoreBinding binding,SavedCheckpointMaterialStore target,
                SavedAttachmentSourceStore.SavedMaterial original){
            this.issuer=issuer;this.binding=binding;this.target=target;this.original=original;
        }
        SavedAttachmentSourceStore.SavedMaterial original(){return original;}
        boolean sameOriginal(OrdinaryReopenCustody other){return issuer==other.issuer&&binding==other.binding&&target==other.target&&original==other.original;}
        void require(ContinuityStorePort.Session same,SavedAttachmentSourceStore actualTarget,boolean physical)throws IOException {
            StrictJson.require(target.ordinaryStore()==actualTarget,"ordinary custody cannot move to another aggregate");
            issuer.requireRetainedOriginal(same,binding);
            StrictJson.require(binding.savedMaterial()==original&&binding.pair().equals(original.pair()),
                    "ordinary private custody lost its actual originally saved material");
            if(physical)original.requirePhysical(same);
        }
    }
    /** Private producer token. It preserves original issuer/file custody and grants no new Game/readiness/restore permission. */
    static final class FirstReopenCustody {
        private final RestoreCheckpointService issuer;private final RestoreBinding binding;
        private final SavedCheckpointMaterialStore target;private final SavedFirstCheckpointMaterialStore.BaselinedMaterial original;
        private FirstReopenCustody(RestoreCheckpointService issuer,RestoreBinding binding,SavedCheckpointMaterialStore target,
                SavedFirstCheckpointMaterialStore.BaselinedMaterial original) {
            this.issuer=issuer;this.binding=binding;this.target=target;this.original=original;
        }
        SavedFirstCheckpointMaterialStore.BaselinedMaterial original(){return original;}
        boolean sameOriginal(FirstReopenCustody other){return issuer==other.issuer&&binding==other.binding&&target==other.target&&original==other.original;}
        void require(ContinuityStorePort.Session same,SavedFirstCheckpointMaterialStore actualTarget,boolean physical)throws IOException {
            StrictJson.require(target.firstStore()==actualTarget,"FIRST original custody cannot move to another aggregate");
            issuer.requireRetainedOriginal(same,binding);
            StrictJson.require(binding.savedMaterial()==original&&binding.pair().equals(original.pair()),
                    "private FIRST custody lost its original saved material");
            same.requireHistoricalEpisodeWindowBaseline(original.baseline());
            if(physical)original.requirePhysical(same);
        }
    }

    public SavedCheckpointMaterial loadRetainedMaterialOriginal(ContinuityStorePort.Session same,SavedCheckpointMaterial.Kind kind,
            CheckpointPair.FileWitness original,CheckpointPair pair)throws IOException {
        writer.requireSession(same);return materials.loadRetainedOriginal(same,kind,original,pair);
    }
    private static void firstBaselinePredecessor(ContinuityStorePort.Session same,SavedFirstCheckpointMaterialStore.BaselinedMaterial first)throws IOException {
        same.requireHistoricalEpisodeWindowBaseline(first.baseline());
        StrictJson.require(same.head().state().origin().equals(first.originalHead().origin())
                &&same.head().state().settledCycles()==0
                &&same.head().state().settledDateRaw()==first.pair().frame().frame().identity().dateRaw().longValueExact(),
                "FIRST physical restore cannot roll back a later ordinary frontier; dedicated rollback required");
    }
    private static Restored result(RestoreBinding binding) {
        return new Restored(binding.pair(), binding.published.readiness(), binding.replacement, binding.attachment, binding);
    }
    private static void requireAck(Request request, ReplacementAck ack) {
        StrictJson.require(ack.requestId().equals(request.requestId()) && ack.previous().equals(request.current().observed().game())
                && ack.loadedSave().equals(request.pair().save().reference()), "lifecycle ACK must bind exact old Game and SAVE source");
    }
    private void requireNative(Request request, ReplacementAck ack, NativeCandidate candidate) throws IOException {
        var actual = candidate.actual(); var transport = actual.session();
        StrictJson.require(ack.replacement().equals(transport.game()) && !transport.game().equals(request.current().observed().game())
                && !transport.sessionId().equals(request.current().sessionId()) && transport.machineId().equals(request.pair().frame().machineId())
                && candidate.lineageId().equals(request.pair().lineageId()) && candidate.source().machineId().equals(transport.machineId())
                && candidate.source().exactBuild().equals(request.current().source().exactBuild()), "raw restored Game/session/machine/source/lineage binding");
        byte[] retained = readExact(candidate.originalNativePacket(), MAX_NATIVE_BYTES + 4);
        StrictJson.require(Arrays.equals(retained, actual.originalPacket()) && retained.length >= 5, "original replacement native packet differs from archived bytes");
        int length = ByteBuffer.wrap(retained, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        StrictJson.require(length > 0 && length <= MAX_NATIVE_BYTES && length + 4 == retained.length, "exact original native LE frame required");
        ObjectNode envelope = object(FullJsonTree.parse(Arrays.copyOfRange(retained, 4, retained.length),MAX_NATIVE_BYTES));
        StrictJson.require("state_snapshot".equals(StrictJson.text(envelope.get("type")))
                && StrictJson.integer(envelope.get("protocol_version"), 1, 1) == 1
                && StrictJson.text(envelope.get("snapshot_id")).equals(actual.snapshotId())
                && SavedAttachmentSourceStore.nativeRevision(envelope.get("revision")).equals(actual.nativeRevision()), "raw native envelope differs from observed frame");
        ObjectNode state = object(FullJsonTree.parse(actual.state().bytes(),MAX_NATIVE_BYTES));
        StrictJson.require(state.equals(envelope.get("state")), "native payload differs from the original transport packet");
        ObjectNode player = object(state.get("played_character"));
        StrictJson.require(isTrue(state.get("map_ready")) && isTrue(state.get("paused")) && isTrue(player.get("alive"))
                && StrictJson.integer(state.get("date_raw"), 0, StrictJson.MAX_SAFE_INTEGER) == request.pair().frame().frame().identity().dateRaw().longValueExact()
                && NativeCharacterId.fromJson(player.get("character_id")).asBigInteger().equals(request.pair().frame().frame().identity().player()), "raw restored paused map/date/living actor differs from physical SAVE");
    }
    private void requirePublished(Request request, ReplacementAck ack, NativeCandidate candidate, PublishedDriver published) throws IOException {
        var ready = published.readiness(); var frame = ready.observed(); var driver = published.driver(); var session = driver.session();
        StrictJson.require(ready.mapReady() && ready.paused() && ready.saveEligible()
                && ack.replacement().equals(frame.game()) && candidate.actual().session().game().equals(frame.game())
                && candidate.actual().session().sessionId().equals(ready.sessionId()) && frame.machineId().equals(candidate.actual().session().machineId())
                && candidate.source().equals(ready.source()) && ready.lineageId().equals(request.pair().lineageId())
                && request.pair().frame().frame().episodeRunId().equals(frame.frame().episodeRunId())
                && request.pair().frame().frame().identity().player().equals(frame.frame().identity().player())
                && request.pair().frame().frame().identity().dateRaw().equals(frame.frame().identity().dateRaw())
                && candidate.actual().nativeRevision().equals(frame.frame().identity().nativeRevision())
                && session.bridgePid() == frame.game().pid() && session.actorId().equals(frame.frame().identity().player())
                && session.episodeRunId().equals(frame.frame().episodeRunId()) && published.semantic().frame().equals(frame), "full adopted Driver, fresh readiness and original raw restore facts disagree");
        for (ExactRef ref : published.semantic().references()) readExact(ref, DriverCheckpointStore.MAX_DRIVER_BYTES);
        readExact(published.originalHistoryBasis(), DriverCheckpointStore.MAX_DRIVER_BYTES);
        DriverStateSnapshot.Complete originalDriver = DriverStateSnapshot.decodeComplete(readExact(published.semantic().originalDriver(), DriverCheckpointStore.MAX_DRIVER_BYTES));
        StrictJson.require(Arrays.equals(originalDriver.encode(), driver.encode()), "published full Driver differs from its archived semantic source");
        requireSurvivingHistory(request, ack, driver);
    }
    private void requireSurvivingHistory(Request request, ReplacementAck ack, DriverStateSnapshot.Complete after) throws IOException {
        DriverStateSnapshot.Complete saved = request.savedMaterial().savedDriver();
        StrictJson.require(after.commandHistory().size() > saved.commandHistory().size(), "full restored Driver must retain the saved prefix and actual physical restart");
        for (int index = 0; index < saved.commandHistory().size(); index++)
            StrictJson.require(Arrays.equals(saved.commandHistory().get(index).originalRow().json(), after.commandHistory().get(index).originalRow().json()), "restore changed original saved history, including unknown rows");
        StrictJson.require(saved.campaignGoal().getClass().equals(after.campaignGoal().getClass()), "restore changed campaign goal presence/null semantics");
        if (saved.campaignGoal() instanceof DriverStateSnapshot.Value oldGoal && after.campaignGoal() instanceof DriverStateSnapshot.Value newGoal)
            StrictJson.require(FullJsonTree.parse(oldGoal.json(),DriverCheckpointStore.MAX_DRIVER_BYTES).equals(FullJsonTree.parse(newGoal.json(),DriverCheckpointStore.MAX_DRIVER_BYTES)), "restore changed the saved goal/calendar");
        StrictJson.require(after.lastCheckpoint() instanceof DriverStateSnapshot.Value, "actual restored checkpoint anchor required");
        var checkpoint = DriverJson.object(((DriverStateSnapshot.Value) after.lastCheckpoint()).json(), DriverJson.MAX_NATIVE_BYTES);
        var rows = after.commandHistory().stream().map(row -> DriverJson.object(row.originalRow().json(), DriverJson.MAX_NATIVE_BYTES)).toList();
        var anchor = DriverHistoryProjection.checkpointHistoryIndex(checkpoint, rows);
        StrictJson.require(anchor.isPresent() && anchor.getAsInt() == request.pair().historyIndex()
                && DriverHistoryProjection.provenRestore(rows.getLast(), checkpoint), "original shared history projection must prove saved anchor and latest actual restore");
        var result = OpportunityJson.object(rows.getLast().get("result"), "actual restore result");
        var replacement = DriverHistoryProjection.processReplacement(result.get("lifecycle")).orElseThrow(() -> new IllegalArgumentException("actual restore process pair missing"));
        StrictJson.require(replacement.previousPid().longValueExact() == ack.previous().pid()
                && replacement.pid().longValueExact() == ack.replacement().pid(), "actual surviving restart row belongs to another process replacement");
    }
    private byte[] readExact(ExactRef ref, int limit) throws IOException {
        var observed = files.observe(Path.of(ref.path())).orElseThrow(() -> new IOException("original restore evidence missing"));
        StrictJson.require(observed.reference().equals(ref), "original restore evidence identity/content drift");
        return files.read(observed, limit);
    }
    private static boolean sameRawIdentity(NativeCandidate first, NativeCandidate second) {
        return first.actual().session().equals(second.actual().session())
                && sameStableReadState(first.actual(),second.actual())
                && first.source().equals(second.source()) && first.lineageId().equals(second.lineageId());
    }
    /** DATA coherence only. The original receiver must separately prove independent request/ACK chronology. */
    public static void requireStableReadProgression(NativeObservationPort.ObservedFrame first,NativeObservationPort.ObservedFrame second) {
        Objects.requireNonNull(first);Objects.requireNonNull(second);
        StrictJson.require(first.session().equals(second.session())
                &&second.nativeRevision().compareTo(first.nativeRevision())>0
                &&!first.snapshotId().equals(second.snapshotId())
                &&!second.observedAt().isBefore(first.observedAt())
                &&sameStableReadState(first,second),
                "independent restore READs require later publication, same owner and identical raw state");
    }
    /** Compare the full JSON type/token domain after validating the sole nested publication-binding leaf. */
    public static boolean sameStableReadState(NativeObservationPort.ObservedFrame first,NativeObservationPort.ObservedFrame second) {
        return stableReadState(Objects.requireNonNull(first)).equals(stableReadState(Objects.requireNonNull(second)));
    }
    private static ObjectNode stableReadState(NativeObservationPort.ObservedFrame original) {
        ObjectNode state=object(FullJsonTree.parse(original.state().bytes(),MAX_NATIVE_BYTES));
        var player=state.get("played_character");
        if(player instanceof ObjectNode character&&character.has("event_trait_membership")) {
            var membership=NativePlayerEventTraitMembership.normalize(character.get("event_trait_membership"),
                    NativeCharacterId.fromJson(character.get("character_id")).asBigInteger(),original.nativeRevision(),state.get("date_raw"));
            // Validation above binds the original leaf to this exact packet; only its publication role is compared alike.
            membership.put("snapshot_revision",0);character.set("event_trait_membership",membership);
        }
        return state;
    }
    private static ObjectNode object(com.fasterxml.jackson.databind.JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "original restore object required"); return (ObjectNode) node;
    }
    private static boolean isTrue(com.fasterxml.jackson.databind.JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
}
