package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit first-SAVE material branch. The ordinary SavedMaterial cycle contract stays unchanged. */
public final class SavedFirstCheckpointMaterialStore {
    public static final String SCHEMA="xar.java-first-checkpoint-material/v1";
    private static final int MAX_METADATA=1024*1024;
    public static final class Material {
        private final SavedFirstCheckpointMaterialStore issuer;
        private final FileWitness witness;
        private final FirstCheckpointVerifier.RetainedFirstCheckpoint checkpoint;
        private Material(SavedFirstCheckpointMaterialStore issuer,FileWitness witness,FirstCheckpointVerifier.RetainedFirstCheckpoint checkpoint){
            this.issuer=issuer;this.witness=witness;this.checkpoint=checkpoint;
        }
        public FileWitness witness(){return witness;}
        public FirstCheckpointVerifier.RetainedFirstCheckpoint checkpoint(){return checkpoint;}
    }
    public static final String BASELINED_SCHEMA="xar.java-baselined-first-checkpoint-material/v1";
    /** Only an actual canonical BASELINE plus original SAVE and saved SEM can mint this material. */
    public static final class BaselinedMaterial implements SavedCheckpointMaterial {
        private final SavedFirstCheckpointMaterialStore issuer;private final FileWitness witness;
        private final Material first;private final EpisodeWindow.CommittedBaseline baseline;
        private final SemanticEvidence semantic;private final String semanticDigest;
        private final ContinuityState originalHead;
        private BaselinedMaterial(SavedFirstCheckpointMaterialStore issuer,FileWitness witness,Material first,
                EpisodeWindow.CommittedBaseline baseline,SemanticEvidence semantic,String semanticDigest,ContinuityState originalHead){
            this.issuer=issuer;this.witness=witness;this.first=first;this.baseline=baseline;
            this.semantic=semantic;this.semanticDigest=semanticDigest;this.originalHead=originalHead;
        }
        public Kind kind(){return Kind.FIRST_BASELINE;}
        public CheckpointPair pair(){return first.checkpoint.pair();}
        public SessionIdentity session(){return first.checkpoint.session();}
        public FileWitness witness(){return witness;}
        public ExactRef reference(){return witness.reference();}
        public Material firstMaterial(){return first;}
        public EpisodeWindow.CommittedBaseline baseline(){return baseline;}
        public ContinuityState originalHead(){return originalHead;}
        public String originalHeadDigest(){return baseline.headDigest();}
        public long originalHeadSequence(){return baseline.sequence();}
        public String checkpointDigest(){return first.checkpoint.digest();}
        public DriverStateSnapshot.Complete savedDriver(){return first.checkpoint.savedDriver();}
        public SemanticEvidence sourceSemantic(){return semantic;}
        public void requireRetained(ContinuityStorePort.Session same)throws IOException{
            issuer.requireOwn(this);issuer.loadRetainedBaselinedOriginal(same,witness,pair());
        }
        public void requirePhysical(ContinuityStorePort.Session same)throws IOException{
            issuer.requireOwn(this);issuer.loadBaselinedOriginal(same,witness,pair());
        }
    }
    private record ReopenedOriginal(RestoreCheckpointService.FirstReopenCustody custody,BaselinedMaterial issued) { }
    private final java.util.concurrent.ConcurrentHashMap<String,ReopenedOriginal> reopenedOriginals=new java.util.concurrent.ConcurrentHashMap<>();
    private final java.util.concurrent.ConcurrentHashMap<Path,FileWitness> baselineWitnesses=new java.util.concurrent.ConcurrentHashMap<>();
    private final CheckpointFiles files;private final FirstCheckpointVerifier verifier;
    private final SavedAttachmentSourceStore.BorrowedSession sessions;private final Path root;
    private final java.util.concurrent.ConcurrentHashMap<Path,FileWitness> capturedWitnesses=new java.util.concurrent.ConcurrentHashMap<>();
    public SavedFirstCheckpointMaterialStore(CheckpointFiles files,FirstCheckpointVerifier verifier,
            SavedAttachmentSourceStore.BorrowedSession sessions,Path root){
        this.files=Objects.requireNonNull(files);this.verifier=Objects.requireNonNull(verifier);this.sessions=Objects.requireNonNull(sessions);
        this.root=Objects.requireNonNull(root).normalize();StrictJson.require(root.isAbsolute(),"actual first SAVE material root required");
    }
    /** Capture only an actual private proof while its original physical pair still exists. */
    public Material capture(FirstCheckpointVerifier.VerifiedFirstCheckpoint proof)throws IOException {
        var same=sessions.current();verifier.requireIssued(same,proof);Path target=path(proof.pair());
        var row=StrictJson.object();row.put("schema",SCHEMA);row.set("pair",StrictJson.parse(CheckpointPairCodec.encode(proof.pair())));
        row.set("session",OrdinaryCycleTransitions.sessionToJson(proof.session()));row.set("opening_semantic",OrdinaryCycleTransitions.semanticToJson(proof.semantic()));
        row.set("begin",proof.begin().toJson());row.set("original_writer_head",proof.originalHead().toJson());
        row.put("original_writer_head_sha256",proof.originalHeadDigest());row.put("first_checkpoint_binding_sha256",proof.digest());
        byte[] encoded=StrictJson.canonical(row,MAX_METADATA);StrictJson.require(encoded.length<=MAX_METADATA,"bounded first SAVE material");
        var existing=files.observe(target);FileWitness witness;
        if(existing.isPresent()){
            witness=existing.orElseThrow();StrictJson.require(witness.equals(capturedWitnesses.get(target)),
                    "existing first material has no original capture identity custody; use its persisted original witness");
            StrictJson.require(Arrays.equals(encoded,files.read(witness,MAX_METADATA)),"immutable first SAVE material publication conflict");
        }else{
            witness=files.createNew(target,encoded);files.verify(witness);
            var prior=capturedWitnesses.putIfAbsent(target,witness);StrictJson.require(prior==null||prior.equals(witness),"first material original capture identity conflict");
        }
        return loadRetainedOriginal(same,witness,proof.pair());
    }
    /** Caller must retain the old FileWitness. A fresh path/hash cannot recreate the original file identity. */
    public Material loadRetainedOriginal(ContinuityStorePort.Session same,FileWitness original,CheckpointPair pair)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(pair);StrictJson.require(sessions.current()==same,"actual source store writer Session required");
        ReopenedOriginal reopened=reopenedOriginals.get(pairKey(pair));
        if(reopened!=null){
            requireReopened(same,reopened,pair,false);
            StrictJson.require(reopened.issued.first.witness.equals(original),"reopened FIRST child material lost its original witness");
            return reopened.issued.first;
        }
        StrictJson.require(path(pair).equals(Path.of(original.reference().path()).normalize()),"exact original first SAVE material path required");
        String head=same.head().digest();files.verify(original);var actual=files.observe(Path.of(original.reference().path())).orElseThrow();
        StrictJson.require(actual.equals(original),"first SAVE material original FileID/FILETIME changed");
        ObjectNode row=decode(files.read(original,MAX_METADATA));
        StrictJson.require(pair.equals(CheckpointPairCodec.decode(StrictJson.canonical(row.get("pair")))),"first SAVE material belongs to another pair");
        var owner=OrdinaryCycleTransitions.sessionFromJson(row.get("session"));var opening=OrdinaryCycleTransitions.semanticFromJson(row.get("opening_semantic"));
        var begin=EpisodeWindow.CommittedBegin.fromJson(row.get("begin"));
        StrictJson.require(row.get("original_writer_head") instanceof ObjectNode,"actual first SAVE original canonical state object required");
        var originalHead=ContinuityState.fromJson((ObjectNode)row.get("original_writer_head"),owner.machineId());
        var retained=verifier.verifyRetainedOriginal(same,owner,pair,opening,begin,originalHead,
                StrictJson.text(row.get("original_writer_head_sha256")),StrictJson.text(row.get("first_checkpoint_binding_sha256")));
        files.verify(original);StrictJson.require(head.equals(same.head().digest()),"retained first SAVE material read changed canonical head");
        return new Material(this,original,retained);
    }
    public void requireRetained(ContinuityStorePort.Session same,Material material)throws IOException {
        Objects.requireNonNull(material);StrictJson.require(material.issuer==this,"foreign first SAVE material issuer");
        var loaded=loadRetainedOriginal(same,material.witness,material.checkpoint.pair());
        StrictJson.require(loaded.checkpoint.digest().equals(material.checkpoint.digest()),"retained first SAVE binding changed");
    }
    /** Called after the real BASELINE commit and post-SAVE SEM, under the same original writer. */
    public BaselinedMaterial captureBaseline(ContinuityStorePort.Session same,Material original,
            EpisodeWindow.CommittedBaseline baseline,SemanticEvidence freshSavedSemantic)throws IOException {
        StrictJson.require(sessions.current()==same,"actual original writer required for first BASELINE capture");
        requireRetained(same,original);same.requireEpisodeWindowActive(baseline);
        requireBaseline(original,baseline);
        String semanticDigest=verifier.requireSavedSemantic(same,original.checkpoint,freshSavedSemantic,true);
        var head=same.requireHistoricalState(baseline.sequence(),baseline.headDigest());
        byte[] raw=new BaselineMetadata(original.checkpoint.pair(),original.witness,baseline,freshSavedSemantic,semanticDigest,head).encode();
        Path target=baselinePath(original.checkpoint.pair());var existing=files.observe(target);FileWitness witness;
        if(existing.isPresent()){
            witness=existing.orElseThrow();
            StrictJson.require(witness.equals(baselineWitnesses.get(target))&&Arrays.equals(raw,files.read(witness,MAX_METADATA)),
                    "existing first BASELINE material lacks its original witness or differs from actual committed source");
        }else{
            witness=files.createNew(target,raw);files.verify(witness);
            var previous=baselineWitnesses.putIfAbsent(target,witness);
            StrictJson.require(previous==null||previous.equals(witness),"first BASELINE original manifest identity conflict");
        }
        return loadBaselinedOriginal(same,witness,original.checkpoint.pair());
    }
    public BaselinedMaterial loadBaselinedOriginal(ContinuityStorePort.Session same,FileWitness original,CheckpointPair pair)throws IOException {
        BaselinedMaterial material=readBaseline(same,original,pair,false);
        // Imported originals retain their real old paths; do not relabel the old witness as this store's local path.
        if(reopenedOriginals.containsKey(pairKey(pair)))return material;
        var previous=baselineWitnesses.putIfAbsent(baselinePath(pair),original);
        StrictJson.require(previous==null||previous.equals(original),"first BASELINE identity conflicts with captured original");
        return material;
    }
    public BaselinedMaterial loadRetainedBaselinedOriginal(ContinuityStorePort.Session same,FileWitness original,CheckpointPair pair)throws IOException {
        return readBaseline(same,original,pair,true);
    }
    BaselinedMaterial currentPhysical(ContinuityStorePort.Session same,CheckpointPair pair)throws IOException {
        ReopenedOriginal reopened=reopenedOriginals.get(pairKey(pair));
        if(reopened!=null){requireReopened(same,reopened,pair,true);return reopened.issued;}
        FileWitness original=baselineWitnesses.get(baselinePath(pair));
        if(original==null)throw new IOException("first BASELINE manifest original identity unavailable; persisted FileWitness required");
        return loadBaselinedOriginal(same,original,pair);
    }
    /** Only the actual restore service can issue this token after original-source/reducer verification under the same writer. */
    synchronized BaselinedMaterial reopenOriginal(ContinuityStorePort.Session same,RestoreCheckpointService.FirstReopenCustody custody)throws IOException {
        Objects.requireNonNull(custody);StrictJson.require(sessions.current()==same,"reopened FIRST custody requires this actual writer Session");
        custody.require(same,this,true);BaselinedMaterial source=custody.original();String key=pairKey(source.pair());
        StrictJson.require(source.issuer!=this,"an original FIRST issuer cannot be replaced with its own import wrapper");
        ReopenedOriginal existing=reopenedOriginals.get(key);
        if(existing!=null){
            StrictJson.require(existing.custody.sameOriginal(custody),"FIRST custody route cannot switch its original admitted restoration");
            requireReopened(same,existing,source.pair(),true);return existing.issued;
        }
        StrictJson.require(reopenedOriginals.size()<16&&!baselineWitnesses.containsKey(baselinePath(source.pair()))
                &&!capturedWitnesses.containsKey(path(source.pair())),"new FIRST custody cannot overwrite a captured original or exceed its finite route inventory");
        // Keep the original paths, FileIDs, canonical receipt, historical head, saved Driver, SEM and saved session.
        // New private wrappers only associate that proven custody with this aggregate; no file is published or re-observed.
        var child=new Material(this,source.first.witness,source.first.checkpoint);
        var issued=new BaselinedMaterial(this,source.witness,child,source.baseline,source.semantic,source.semanticDigest,source.originalHead);
        var retained=new ReopenedOriginal(custody,issued);reopenedOriginals.put(key,retained);
        requireReopened(same,retained,source.pair(),true);return issued;
    }
    private void requireReopened(ContinuityStorePort.Session same,ReopenedOriginal reopened,CheckpointPair pair,boolean physical)throws IOException {
        StrictJson.require(sessions.current()==same&&reopened.issued.issuer==this&&reopened.issued.pair().equals(pair),
                "FIRST original custody crossed its exact pair, aggregate or borrowed writer");
        String head=same.head().digest();reopened.custody.require(same,this,physical);
        var source=reopened.custody.original();
        StrictJson.require(source.pair().equals(pair)&&source.witness.equals(reopened.issued.witness)
                &&source.first.witness.equals(reopened.issued.first.witness)
                &&source.baseline.equals(reopened.issued.baseline)&&source.semantic.equals(reopened.issued.semantic)
                &&source.checkpointDigest().equals(reopened.issued.checkpointDigest())
                &&source.first.checkpoint==reopened.issued.first.checkpoint&&source.savedDriver()==reopened.issued.savedDriver()
                &&head.equals(same.head().digest()),"reopened FIRST custody changed original metadata, full Driver, SEM or canonical head");
    }
    private static String pairKey(CheckpointPair pair){return DriverCheckpointStore.sha256(CheckpointPairCodec.encode(Objects.requireNonNull(pair)));}

    boolean owns(SavedCheckpointMaterial material){return material instanceof BaselinedMaterial first&&first.issuer==this;}
    private void requireOwn(BaselinedMaterial material){StrictJson.require(owns(material),"foreign first BASELINE material issuer");}
    private BaselinedMaterial readBaseline(ContinuityStorePort.Session same,FileWitness original,CheckpointPair pair,boolean retained)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(original);Objects.requireNonNull(pair);
        ReopenedOriginal reopened=reopenedOriginals.get(pairKey(pair));
        if(reopened!=null){
            requireReopened(same,reopened,pair,!retained);
            StrictJson.require(reopened.issued.witness.equals(original),"reopened FIRST BASELINE material lost its original witness");
            return reopened.issued;
        }
        StrictJson.require(sessions.current()==same&&baselinePath(pair).equals(Path.of(original.reference().path()).normalize()),
                "actual same-writer and exact first BASELINE manifest required");
        String before=same.head().digest();files.verify(original);
        BaselineMetadata metadata=decodeBaselineMetadata(files.read(original,MAX_METADATA));
        StrictJson.require(pair.equals(metadata.pair()),"first BASELINE schema/pair differs");
        Material first=loadRetainedOriginal(same,metadata.firstMaterial(),pair);
        var baseline=metadata.baseline();requireBaseline(first,baseline);
        same.requireHistoricalEpisodeWindowBaseline(baseline);
        if(!retained)same.requireEpisodeWindowActive(baseline);
        var head=metadata.originalHead();var historical=same.requireHistoricalState(baseline.sequence(),baseline.headDigest());
        StrictJson.require(ContinuityJson.same(head.toJson(),historical.toJson()),"first BASELINE manifest lost its actual canonical ancestor");
        SemanticEvidence semantic=metadata.savedSemantic();
        String digest=verifier.requireSavedSemantic(same,first.checkpoint,semantic,!retained);
        StrictJson.require(digest.equals(metadata.semanticDigest()),"original post-SAVE semantic verifier changed");
        files.verify(original);StrictJson.require(before.equals(same.head().digest()),"first BASELINE source read mutated original writer");
        return new BaselinedMaterial(this,original,first,baseline,semantic,digest,head);
    }
    /** Pure archived metadata validation only. This reads no file/writer and cannot mint private material or admission. */
    public static void verifyArchivedBaselineMetadata(byte[] original,EpisodeWindow.CommittedBaseline expected,
            SemanticEvidence savedSemantic){
        Objects.requireNonNull(expected);Objects.requireNonNull(savedSemantic);
        BaselineMetadata metadata=decodeBaselineMetadata(original);
        StrictJson.require(metadata.baseline().equals(expected)
                &&OrdinaryCycleTransitions.semanticToJson(metadata.savedSemantic()).equals(OrdinaryCycleTransitions.semanticToJson(savedSemantic)),
                "archived first BASELINE metadata differs from the exact expected committed baseline or original saved SEM");
    }
    private static final Set<String> BASELINE_FIELDS=Set.of("schema","pair","first_material_witness","committed_baseline",
            "saved_semantic","saved_semantic_verifier_sha256","original_writer_head");
    /** Typed DATA decoded by both the real retained issuer and pure domain replay. */
    private record BaselineMetadata(CheckpointPair pair,FileWitness firstMaterial,EpisodeWindow.CommittedBaseline baseline,
            SemanticEvidence savedSemantic,String semanticDigest,ContinuityState originalHead){
        private BaselineMetadata{
            Objects.requireNonNull(pair);Objects.requireNonNull(firstMaterial);Objects.requireNonNull(baseline);
            Objects.requireNonNull(savedSemantic);Objects.requireNonNull(originalHead);
            org.xar.ck3.control.continuity.writer.WriterContracts.requireDigest(semanticDigest);
            var actual=baseline.baseline();var identity=actual.savedIdentity();var paired=pair.frame();var saved=savedSemantic.frame();
            byte[] pairBytes=CheckpointPairCodec.encode(pair);
            StrictJson.require(actual.saveActionId().equals(pair.saveActionId())
                    &&actual.pairRef().bytes()==pairBytes.length&&actual.pairDigest().equals(DriverCheckpointStore.sha256(pairBytes))
                    &&identity.machineId().equals(paired.machineId())&&identity.game().equals(paired.game())
                    &&identity.actorId()==paired.frame().identity().player().longValueExact()
                    &&identity.dateRaw()==paired.frame().identity().dateRaw().longValueExact()
                    &&identity.episodeRunId().equals(paired.frame().episodeRunId()),"archived BASELINE metadata pair/action/opening identity differs");
            StrictJson.require(originalHead.machineId().equals(identity.machineId())&&originalHead.sequence()==baseline.sequence()
                    &&ContinuityJson.digest(originalHead.toJson()).equals(baseline.headDigest())
                    &&EpisodeWindow.requireActive(originalHead).baseline().orElseThrow().equals(actual),
                    "archived BASELINE metadata lost its exact canonical state");
            StrictJson.require(saved.machineId().equals(paired.machineId())&&saved.game().equals(paired.game())
                    &&saved.frame().episodeRunId().equals(paired.frame().episodeRunId())
                    &&saved.frame().identity().player().equals(paired.frame().identity().player())
                    &&saved.frame().identity().dateRaw().equals(paired.frame().identity().dateRaw())
                    &&saved.frame().revision().compareTo(paired.frame().revision())>=0
                    &&saved.frame().identity().nativeRevision().compareTo(paired.frame().identity().nativeRevision())>=0
                    &&savedSemantic.originalDriver().sha256().equals(pair.driver().reference().sha256())
                    &&savedSemantic.originalDriver().bytes()==pair.driver().reference().bytes(),
                    "archived post-SAVE SEM must retain the actual first pair identity and full saved Driver digest");
        }
        private byte[] encode(){
            var row=StrictJson.object();row.put("schema",BASELINED_SCHEMA);row.set("pair",StrictJson.parse(CheckpointPairCodec.encode(pair)));
            row.set("first_material_witness",CheckpointPairCodec.fileWitnessToJson(firstMaterial));row.set("committed_baseline",baseline.toJson());
            row.set("saved_semantic",OrdinaryCycleTransitions.semanticToJson(savedSemantic));row.put("saved_semantic_verifier_sha256",semanticDigest);
            row.set("original_writer_head",originalHead.toJson());return StrictJson.canonical(row,MAX_METADATA);
        }
    }
    private static BaselineMetadata decodeBaselineMetadata(byte[] original){
        Objects.requireNonNull(original);
        ObjectNode row=StrictJson.object(StrictJson.parse(original,MAX_METADATA),BASELINE_FIELDS);
        StrictJson.require(BASELINED_SCHEMA.equals(StrictJson.text(row.get("schema"))),"explicit first BASELINE metadata schema required");
        var pair=CheckpointPairCodec.decode(StrictJson.canonical(row.get("pair")));
        var head=ContinuityJson.object(row.get("original_writer_head"));
        return new BaselineMetadata(pair,CheckpointPairCodec.fileWitnessFromJson(row.get("first_material_witness")),
                EpisodeWindow.CommittedBaseline.fromJson(row.get("committed_baseline")),OrdinaryCycleTransitions.semanticFromJson(row.get("saved_semantic")),
                StrictJson.text(row.get("saved_semantic_verifier_sha256")),ContinuityState.fromJson(head,pair.frame().machineId()));
    }
    private static void requireBaseline(Material first,EpisodeWindow.CommittedBaseline baseline){
        var expected=baseline.baseline();var actual=first.checkpoint;var saved=actual.begin().begin().after();
        StrictJson.require(expected.begin().equals(actual.begin())&&expected.saveActionId().equals(actual.pair().saveActionId())
                &&expected.pairRef().equals(actual.pairReference())&&expected.pairDigest().equals(actual.pairReference().sha256())
                &&expected.canonicalSaveReceiptRef().equals(actual.canonicalSaveReference())&&expected.proofDigest().equals(actual.digest())
                &&expected.savedIdentity().equals(saved),"BASELINE must bind the exact private original first SAVE and new episode identity");
    }
    SavedContinuityAttachment.FirstBasis basis(ContinuityStorePort.Session same,ContinuityState predecessor,BaselinedMaterial material)throws IOException {
        requireOwn(material);material.requirePhysical(same);same.requireHistoricalEpisodeWindowBaseline(material.baseline);
        var pair=material.pair();var frame=pair.frame().frame();
        var basis=new SavedContinuityAttachment.FirstBasis(pair.frame().machineId(),material.originalHead.origin(),
                new SavedContinuityAttachment.FirstBasis.Frame(frame.snapshotId(),frame.revision(),frame.identity().nativeRevision(),
                        frame.identity().dateRaw().longValueExact(),frame.identity().player().longValueExact(),frame.episodeRunId()),
                material.baseline,pair.driver().reference(),pair.driver().identity(),pair.save().reference(),pair.save().identity(),
                material.first.checkpoint.canonicalSaveReference(),material.first.checkpoint.pairReference(),material.reference(),
                material.checkpointDigest(),pair.lineageId(),pair.historyIndex());
        basis.requirePredecessor(predecessor);return basis;
    }
    private Path baselinePath(CheckpointPair pair){
        return root.resolve("first-baselines").resolve(DriverCheckpointStore.sha256(CheckpointPairCodec.encode(pair))+".json");
    }
    SavedContinuityAttachment.FirstBasis basisSession(RestoreCheckpointService.Request request,BaselinedMaterial material)throws IOException {
        var same=sessions.current();StrictJson.require(same.head().digest().equals(request.expectedHeadDigest()),"first restore predecessor drift");
        return basis(same,same.head().state(),material);
    }
    SavedAttachmentAuthority.Loaded loadAttachment(SavedAttachmentSourceStore sourceDocuments,ContinuityState predecessor,
            org.xar.ck3.control.continuity.writer.WriterContracts.Request request,SavedAttachmentSourceStore.Sources sources)throws IOException {
        var same=sessions.current();var pair=SavedAttachmentAuthority.pairFromDetails(request);
        var material=loadBaselinedOriginal(same,sources.material(),pair);
        return sourceDocuments.loadMaterial(predecessor,request,material,basis(same,predecessor,material).toJson());
    }
    static ObjectNode decode(byte[] raw){
        ObjectNode row=StrictJson.object(StrictJson.parse(raw,MAX_METADATA),Set.of("schema","pair","session","opening_semantic","begin","original_writer_head",
                "original_writer_head_sha256","first_checkpoint_binding_sha256"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"explicit first SAVE material schema required");
        return row;
    }
    private Path path(CheckpointPair pair){return root.resolve("first-checkpoints").resolve(DriverCheckpointStore.sha256(CheckpointPairCodec.encode(pair))+".json");}
}
