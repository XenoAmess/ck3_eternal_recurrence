package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.FirstCheckpointVerifier;
import org.xar.ck3.control.application.checkpoint.FirstCheckpointVerifier.VerifiedFirstCheckpoint;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.EpisodeWindowAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** The Core's one private NEXT window producer. It never submits SAVE, activates callbacks or installs a host. */
public final class RootNextEpisodeWindowRuntime implements EpisodeWindowAuthority.Verifier {
    private final RootApplicationAssembly.Core core;
    private final EpisodeWindowAuthority authority;
    private BeginAttempt pending;

    public RootNextEpisodeWindowRuntime(RootApplicationAssembly.Core actual) {
        core=Objects.requireNonNull(actual);authority=new EpisodeWindowAuthority(this);
    }
    public EpisodeWindowAuthority authority(){return authority;}

    public static final class Begun {
        private final RootNextEpisodeWindowRuntime issuer;
        private final BeginAttempt original;
        private final EpisodeWindow.CommittedBegin committed;
        private Begun(RootNextEpisodeWindowRuntime issuer,BeginAttempt original,EpisodeWindow.CommittedBegin committed){
            this.issuer=issuer;this.original=original;this.committed=committed;
        }
        public RootApplicationAssembly.NextEpisodeStage stage(){return original.stage;}
        public LifecycleEpisodeInputs inputs(){return original.inputs;}
        public LifecycleEpisodeInputs.Binding openingBinding(){return original.binding;}
        public EpisodeWindow.CommittedBegin committedBegin(){return committed;}
        public SemanticEvidence opening(){return original.opening;}
    }
    public static final class Baselined {
        private final RootNextEpisodeWindowRuntime issuer;
        private final Begun begun;
        private final FirstCheckpointVerifier firstVerifier;
        private final VerifiedFirstCheckpoint first;
        private final EpisodeWindow.CommittedBaseline committed;
        private Baselined(RootNextEpisodeWindowRuntime issuer,Begun begun,FirstCheckpointVerifier firstVerifier,
                VerifiedFirstCheckpoint first,EpisodeWindow.CommittedBaseline committed){
            this.issuer=issuer;this.begun=begun;this.firstVerifier=firstVerifier;this.first=first;this.committed=committed;
        }
        public Begun begun(){return begun;}
        public FirstCheckpointVerifier firstVerifier(){return firstVerifier;}
        public VerifiedFirstCheckpoint firstCheckpoint(){return first;}
        public EpisodeWindow.CommittedBaseline committedBaseline(){return committed;}
    }
    private static final class BeginAttempt {
        private final RootApplicationAssembly.NextEpisodeStage stage;
        private final LifecycleEpisodeInputs inputs;
        private final LifecycleEpisodeInputs.Binding binding;
        private final SemanticEvidence opening;
        private final WriterContracts.Head before;
        private final EpisodeWindow.Begin descriptor;
        private WriterContracts.Prepared prepared;
        private boolean submitted;
        private Begun begun;
        private BaselineAttempt baseline;
        private BeginAttempt(RootApplicationAssembly.NextEpisodeStage stage,LifecycleEpisodeInputs inputs,
                LifecycleEpisodeInputs.Binding binding,SemanticEvidence opening,WriterContracts.Head before,EpisodeWindow.Begin descriptor){
            this.stage=stage;this.inputs=inputs;this.binding=binding;this.opening=opening;this.before=before;this.descriptor=descriptor;
        }
    }
    private static final class BaselineAttempt {
        private final Begun begun;
        private final FirstCheckpointVerifier verifier;
        private final VerifiedFirstCheckpoint first;
        private final WriterContracts.Head before;
        private final EpisodeWindow.Baseline descriptor;
        private WriterContracts.Prepared prepared;
        private boolean submitted;
        private Baselined result;
        private BaselineAttempt(Begun begun,FirstCheckpointVerifier verifier,VerifiedFirstCheckpoint first,WriterContracts.Head before){
            this.begun=begun;this.verifier=verifier;this.first=first;this.before=before;descriptor=first.baseline();
        }
    }

    /** Root supplies a real later candidate SEM under its existing writer; this method issues no native query. */
    public synchronized Begun begin(ContinuityStorePort.Session same,RootApplicationAssembly.NextEpisodeStage stage,
            LifecycleEpisodeInputs actualInputs,SemanticEvidence opening)throws IOException {
        requireSession(same);Objects.requireNonNull(stage);Objects.requireNonNull(actualInputs);Objects.requireNonNull(opening);
        BeginAttempt actual=pending;
        if(actual!=null&&actual.stage==stage){
            StrictJson.require(actual.inputs==actualInputs&&actual.opening.equals(opening),"NEXT BEGIN retry changed its original input producer or opening SEM");
        }else{
            if(actual!=null){
                StrictJson.require(actual.baseline!=null&&actual.baseline.result!=null,"an unresolved BEGIN/first SAVE cannot be replaced by another NEXT");
                same.requireEpisodeWindowActive(actual.baseline.result.committedBaseline());
            }
            stage.requireCurrent(same);
            WriterContracts.Head before=same.head();
            var after=new SessionIdentity(stage.source().machineId(),stage.replacement().generation(),stage.replacement().sessionId());
            var binding=actualInputs.bind(same,stage.previous().identity(),after,stage.original().parent(),opening);
            requireBinding(stage,binding);
            requireHead(before,same.head());
            EpisodeWindow.Begin descriptor=describe(stage,binding,before,same);
            actual=new BeginAttempt(stage,actualInputs,binding,opening,before,descriptor);
            // Register only fully validated inputs before the sole authority participates in preview/commit.
            pending=actual;
        }
        if(actual.begun!=null){requireBegun(same,actual.begun);return actual.begun;}
        if(!actual.submitted){
            stage.requireCurrent(same);actual.inputs.requireCurrent(same,actual.binding);requireHead(actual.before,same.head());
            actual.prepared=same.preview(actual.descriptor.request());
            actual.submitted=true;
            EpisodeWindow.CommittedBegin committed=same.beginEpisodeWindow(actual.descriptor);
            actual.begun=new Begun(this,actual,committed);
        }else{
            var receipt=queryOriginal(same,actual.prepared,"BEGIN");
            WriterContracts.Pin event=committedEvent(same,actual.prepared,receipt);
            actual.begun=new Begun(this,actual,new EpisodeWindow.CommittedBegin(actual.descriptor,
                    receipt.head().sequence(),receipt.eventIdentity(),ContinuityJson.digest(receipt.head().toJson()),event));
        }
        requireBegun(same,actual.begun);return actual.begun;
    }

    /** Consumes the actual already confirmed first pair. It never authorizes or repeats the physical SAVE. */
    public synchronized Baselined baseline(ContinuityStorePort.Session same,Begun begun,
            FirstCheckpointVerifier verifier,VerifiedFirstCheckpoint first)throws IOException {
        requireBegun(same,begun);Objects.requireNonNull(verifier);Objects.requireNonNull(first);
        BeginAttempt owner=begun.original;BaselineAttempt actual=owner.baseline;
        if(actual==null){
            verifier.requireIssued(same,first);
            StrictJson.require(first.begin().equals(begun.committed)&&first.semantic().equals(begun.opening())
                    &&first.session().equals(begun.openingBinding().afterOwner())
                    &&Arrays.equals(first.originalDriver().encode(),begun.openingBinding().driver().encode()),
                    "actual first SAVE belongs to another private BEGIN, opening, physical owner or adopted Driver");
            var waiting=EpisodeWindow.state(same.head().state()).orElseThrow();
            StrictJson.require(waiting.phase()==EpisodeWindow.Phase.AWAITING_FIRST_SAVE&&waiting.begin().equals(owner.descriptor),
                    "new BASELINE requires this exact still-awaiting BEGIN");
            actual=new BaselineAttempt(begun,verifier,first,same.head());owner.baseline=actual;
        }else StrictJson.require(actual.begun==begun&&actual.verifier==verifier&&actual.first==first,
                "BASELINE retry cannot replace its private first-checkpoint issuer or same original pair proof");
        if(actual.result!=null){requireBaseline(same,actual.result);return actual.result;}
        if(!actual.submitted){
            requireHead(actual.before,same.head());actual.verifier.requireIssued(same,actual.first);
            actual.prepared=same.preview(actual.descriptor.request());actual.submitted=true;
            actual.result=new Baselined(this,begun,verifier,first,same.baselineEpisodeWindow(actual.descriptor));
        }else{
            var receipt=queryOriginal(same,actual.prepared,"BASELINE");
            WriterContracts.Pin event=committedEvent(same,actual.prepared,receipt);
            actual.result=new Baselined(this,begun,verifier,first,new EpisodeWindow.CommittedBaseline(actual.descriptor,
                    receipt.head().sequence(),receipt.eventIdentity(),ContinuityJson.digest(receipt.head().toJson()),event));
        }
        requireBaseline(same,actual.result);return actual.result;
    }

    public synchronized void requireBegun(ContinuityStorePort.Session same,Begun begun)throws IOException {
        requireSession(same);Objects.requireNonNull(begun);
        StrictJson.require(begun.issuer==this&&pending==begun.original&&begun.original.begun==begun,
                "foreign or retired private NEXT BEGIN custody");
        begun.stage().requireRetainedOriginal(same);
        same.requireHistoricalState(begun.openingBinding().writerHeadSequence(),begun.openingBinding().writerHeadDigest());
        requireBinding(begun.stage(),begun.openingBinding());
        StrictJson.require(begun.committed.begin().equals(begun.original.descriptor),"BEGIN token changed its original typed descriptor");
        same.requireEpisodeWindowBegin(begun.committed);
    }
    public synchronized void requireBaseline(ContinuityStorePort.Session same,Baselined result)throws IOException {
        requireSession(same);Objects.requireNonNull(result);
        StrictJson.require(result.issuer==this&&result.begun.original.baseline!=null
                &&result.begun.original.baseline.result==result,"foreign private NEXT BASELINE custody");
        requireBegun(same,result.begun);result.firstVerifier.requireIssued(same,result.first);
        StrictJson.require(result.first.baseline().equals(result.committed.baseline()),"BASELINE is not the same privately verified first pair");
        same.requireEpisodeWindowActive(result.committed);
    }

    /** Called by the one EpisodeWindowAuthority under the actual original writer lock, twice if preview and commit require it. */
    @Override public synchronized String requireBegin(WriterContracts.Head actual,EpisodeWindow.Begin descriptor)throws IOException {
        var same=core.writer().borrowedSession();requireSession(same);BeginAttempt attempt=Objects.requireNonNull(pending,"actual private NEXT BEGIN is not prepared");
        StrictJson.require(attempt.begun==null&&attempt.descriptor.equals(descriptor),"BEGIN authority does not own this original typed request");
        requireHead(attempt.before,actual);requireHead(actual,same.head());
        attempt.stage.requireCurrent(same);attempt.inputs.requireCurrent(same,attempt.binding);requireBinding(attempt.stage,attempt.binding);
        StrictJson.require(describe(attempt.stage,attempt.binding,actual,same).equals(descriptor),"actual BEGIN source producer changed its description");
        return proofDigest("BEGIN",descriptor.request().identity(),attempt.binding.semanticDigest(),attempt.before.digest());
    }
    @Override public synchronized String requireBaseline(WriterContracts.Head actual,EpisodeWindow.Baseline descriptor)throws IOException {
        var same=core.writer().borrowedSession();requireSession(same);BeginAttempt owner=Objects.requireNonNull(pending,"actual private NEXT is not prepared");
        BaselineAttempt attempt=Objects.requireNonNull(owner.baseline,"actual private first SAVE is not prepared");
        StrictJson.require(attempt.result==null&&attempt.descriptor.equals(descriptor),"BASELINE authority does not own this original private first pair");
        requireHead(attempt.before,actual);requireHead(actual,same.head());requireBegun(same,attempt.begun);
        attempt.verifier.requireIssued(same,attempt.first);
        StrictJson.require(attempt.first.baseline().equals(descriptor),"private first SAVE proof changed its actual baseline description");
        return proofDigest("BASELINE",descriptor.request().identity(),attempt.first.digest(),attempt.before.digest());
    }

    private void requireSession(ContinuityStorePort.Session same)throws IOException {
        core.writer().requireSession(Objects.requireNonNull(same));
        StrictJson.require(core.writer().borrowedSession()==same,"NEXT window must borrow this exact Core's currently held original Session");
    }
    private static void requireBinding(RootApplicationAssembly.NextEpisodeStage stage,LifecycleEpisodeInputs.Binding binding) {
        StrictJson.require(binding.proof() instanceof LifecycleTransitionProof.NextEpisode&&binding.proof()==stage.original().proof()
                &&binding.parent().equals(stage.original().parent())&&binding.commit().equals(stage.original().commit())
                &&binding.beforeOwner().equals(stage.previous().identity())
                &&stage.original().originalParentFacts().stamp().game().equals(binding.beforeOwner().game())
                &&binding.afterOwner().game().equals(stage.replacement().generation())
                &&binding.driverStamp().game().equals(binding.afterOwner().game())
                &&binding.afterOwner().sessionId().equals(stage.replacement().sessionId())
                &&binding.afterOwner().machineId().equals(stage.source().machineId())
                &&binding.driverStamp().equals(stage.original().published().stamp())
                &&Arrays.equals(binding.driver().encode(),stage.original().published().driver().encode())
                &&Arrays.equals(binding.predecessorDriver().encode(),stage.original().originalParentFacts().driver().encode()),
                "actual M7 opening binding differs from the private Root lifecycle/stage/full Driver ancestry");
    }
    private static EpisodeWindow.Begin describe(RootApplicationAssembly.NextEpisodeStage stage,LifecycleEpisodeInputs.Binding binding,
            WriterContracts.Head head,ContinuityStorePort.Session same)throws IOException {
        var original=stage.original();var before=original.originalParentFacts();var old=binding.beforeOwner();var after=binding.afterOwner();
        long sequence=Math.addExact(original.commit().prepared().predecessor().state().sequence(),1);
        var event=eventPin(original.commit().committedDocuments(),sequence);
        StrictJson.require(head.documents().contains(event),"actual original lifecycle event Pin is absent from the current writer");same.verifyPin(event);
        var row=StrictJson.parse(same.readPinned(event,ContinuityJson.DOCUMENT_MAX_BYTES));
        StrictJson.require(StrictJson.text(row.get("identity")).equals(binding.commitDigest())
                &&StrictJson.text(row.get("kind")).equals(original.commit().prepared().request().kind()),"BEGIN lifecycle original event differs from its real commit");
        var from=new EpisodeWindow.Identity(old.machineId(),old.game(),old.sessionId(),before.stamp().episodeRunId(),
                before.stamp().episodeEpoch(),before.driver().session().actorId().longValueExact(),original.parent().command().lifecycleBefore().frame().dateRaw().longValueExact());
        var to=new EpisodeWindow.Identity(after.machineId(),after.game(),after.sessionId(),binding.driverStamp().episodeRunId(),
                binding.driverStamp().episodeEpoch(),binding.driver().session().actorId().longValueExact(),binding.semantic().frame().frame().identity().dateRaw().longValueExact());
        var evidence=new LinkedHashSet<ExactRef>(original.proof().originalEvidence());
        evidence.addAll(binding.semantic().references());evidence.add(stage.source().sourceRef());
        return describeBegin(new DescriptorData(from,to,head.state().origin().windowId(),original.parent().command().actionId(),
                sequence,binding.commitDigest(),event,original.driverReference(),List.copyOf(evidence)));
    }

    /** Pure DATA producer used by the actual private path. These values cannot mint Begun, stage or writer authority. */
    record DescriptorData(EpisodeWindow.Identity before,EpisodeWindow.Identity after,long oldWindowId,String parentActionId,
            long lifecycleSequence,String lifecycleIdentity,WriterContracts.Pin lifecycleEvent,ExactRef adoptedDriver,List<ExactRef> evidence){
        DescriptorData{Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(lifecycleEvent);Objects.requireNonNull(adoptedDriver);evidence=List.copyOf(evidence);}
    }
    static EpisodeWindow.Begin describeBegin(DescriptorData data){
        Objects.requireNonNull(data);eventPin(List.of(data.lifecycleEvent()),data.lifecycleSequence());
        return new EpisodeWindow.Begin("next-window:"+data.parentActionId(),data.before(),data.after(),data.oldWindowId(),Math.addExact(data.oldWindowId(),1),
                data.parentActionId(),data.lifecycleSequence(),data.lifecycleIdentity(),data.lifecycleEvent().reference(),data.adoptedDriver(),data.evidence());
    }
    static WriterContracts.Pin eventPin(List<WriterContracts.Pin> documents,long sequence){
        StrictJson.safe(sequence,1);String name=String.format(Locale.ROOT,"%08d.json",sequence);
        var matches=List.copyOf(documents).stream().filter(pin->Path.of(pin.reference().path()).getFileName().toString().equals(name)).toList();
        StrictJson.require(matches.size()==1,"one exact original immutable event Pin for its actual sequence required");return matches.getFirst();
    }
    private static WriterContracts.Receipt queryOriginal(ContinuityStorePort.Session same,WriterContracts.Prepared prepared,String phase)throws IOException {
        Objects.requireNonNull(prepared);
        return same.queryCommitted(prepared).orElseThrow(()->new IOException("original "+phase+" result is unavailable; retained request is query-only and is not submitted again"));
    }
    private static WriterContracts.Pin committedEvent(ContinuityStorePort.Session same,WriterContracts.Prepared prepared,WriterContracts.Receipt receipt)throws IOException {
        same.requireCommitted(prepared,receipt);
        StrictJson.require(receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE&&receipt.eventIdentity().equals(prepared.request().identity()),
                "actual original episode request has no committed mutation");
        EpisodeWindow.requireReduction(prepared.predecessor().state(),receipt.head(),prepared.request(),true);
        var pin=eventPin(same.head().documents(),receipt.head().sequence());same.verifyPin(pin);return pin;
    }
    private static void requireHead(WriterContracts.Head expected,WriterContracts.Head actual){
        StrictJson.require(expected.state().sequence()==actual.state().sequence()&&expected.digest().equals(actual.digest())
                &&expected.documents().equals(actual.documents())&&expected.absent().equals(actual.absent())
                &&expected.indexRepairs().equals(actual.indexRepairs())&&expected.snapshotNeedsRecovery()==actual.snapshotNeedsRecovery(),
                "NEXT window authority requires the exact actual full Head under the same original writer lock");
    }
    private static String proofDigest(String phase,String request,String original,String head){
        ObjectNode row=StrictJson.object();row.put("schema","xar.root-next-window-private-binding/v1");row.put("phase",phase);
        row.put("request_identity",request);row.put("original_proof_sha256",original);row.put("original_writer_head_sha256",head);return ContinuityJson.digest(row);
    }
}
