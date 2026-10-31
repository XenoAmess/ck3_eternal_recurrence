package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointCommitVerifier.VerifiedCheckpoint;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.CompletedCycleProof;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Immutable saved proof producer and the canonical original-lock attachment loader. No Python or live replay. */
public final class SavedAttachmentSourceStore implements SavedAttachmentAuthority.SourceLoader {
    public static final String SOURCES_DETAIL="java_saved_attachment_sources";
    public static final String MATERIAL_SCHEMA="xar.java-saved-checkpoint-material/v1";
    public static final String SOURCES_SCHEMA="xar.java-saved-attachment-sources/v3";
    private static final String OPENING_SCHEMA="xar.java-restored-raw-binding/v2";
    private static final int MAX_METADATA=1024*1024, MAX_NATIVE=DriverJson.MAX_NATIVE_BYTES;
    @FunctionalInterface public interface BorrowedSession {
        /** Exact currently held ContinuityWriter Session; no new lock and no default/session fabrication. */
        ContinuityStorePort.Session current() throws IOException;
    }
    @FunctionalInterface public interface CycleProofVerifier {
        /** Rechecks the original canonical ordinary state and classified receipt chain, including the saved-pair branch. */
        String verify(ContinuityStorePort.Session borrowed,SessionIdentity source,CompletedCycleProof actual) throws IOException;
    }
    @FunctionalInterface public interface HistoricalCycleProofVerifier {
        /** Actual canonical captured original state and immutable chain; grants no current cycle or credit. */
        String verify(ContinuityStorePort.Session borrowed,SessionIdentity source,CompletedCycleProof proof,ContinuityState capturedOriginalHead)throws IOException;
    }
    public static final class SavedMaterial implements SavedCheckpointMaterial {
        private final SavedAttachmentSourceStore issuer;
        private final CheckpointPair pair;
        private final SessionIdentity session;
        private final CompletedCycleProof proof;
        private final ContinuityState originalHead;
        private final String originalHeadDigest, checkpointDigest;
        private final FileWitness manifest;
        private final DriverStateSnapshot.Complete savedDriver;
        private SavedMaterial(SavedAttachmentSourceStore issuer,CheckpointPair pair,SessionIdentity session,CompletedCycleProof proof,
                ContinuityState originalHead,String originalHeadDigest,String checkpointDigest,FileWitness manifest,DriverStateSnapshot.Complete savedDriver) {
            this.issuer=issuer;this.pair=pair;this.session=session;this.proof=proof;this.originalHeadDigest=originalHeadDigest;
            this.originalHead=originalHead;this.checkpointDigest=checkpointDigest;this.manifest=manifest;this.savedDriver=savedDriver;
        }
        public Kind kind(){return Kind.ORDINARY;}
        public SemanticEvidence sourceSemantic(){return proof.semantic();}
        public void requireRetained(ContinuityStorePort.Session same)throws IOException{issuer.loadRetainedOriginal(same,witness(),pair);}
        public void requirePhysical(ContinuityStorePort.Session same)throws IOException{issuer.loadOriginal(same,witness(),pair);}
        public CheckpointPair pair(){return pair;}
        public SessionIdentity session(){return session;}
        public CompletedCycleProof proof(){return proof;}
        public ExactRef reference(){return manifest.reference();}
        public FileWitness witness(){return manifest;}
        public String originalHeadDigest(){return originalHeadDigest;}
        public long originalHeadSequence(){return originalHead.sequence();}
        /** Immutable original canonical state; this accessor grants no current Game or replay eligibility. */
        public ContinuityState originalHead(){return originalHead;}
        public String checkpointDigest(){return checkpointDigest;}
        /** Archived complete Driver; this data accessor grants no current physical reload permit. */
        public DriverStateSnapshot.Complete savedDriver(){return savedDriver;}
    }
    public static record Sources(SavedCheckpointMaterial.Kind kind,FileWitness material,ExactRef basis,ExactRef game,ExactRef opening,
            ExactRef progress,ExactRef restoredNative) {
        public Sources { Objects.requireNonNull(kind);Objects.requireNonNull(material);for(ExactRef ref:List.of(material.reference(),basis,game,opening,progress,restoredNative))
            StrictJson.require(ref.bytes()>0&&Path.of(ref.path()).isAbsolute(),"actual nonempty absolute restore source"); }
        public List<ExactRef> references(){return List.of(material.reference(),basis,game,opening,progress,restoredNative);}
        public ObjectNode toJson(){
            var row=StrictJson.object();row.put("schema",SOURCES_SCHEMA);row.put("material_kind",kind.name());row.set("material_witness",CheckpointPairCodec.fileWitnessToJson(material));row.set("basis",basis.toJson());
            row.set("game",game.toJson());row.set("opening",opening.toJson());row.set("progress",progress.toJson());row.set("restored_native",restoredNative.toJson());return row;
        }
        public static Sources decode(JsonNode value){
            var row=StrictJson.object(value,Set.of("schema","material_kind","material_witness","basis","game","opening","progress","restored_native"));
            StrictJson.require(SOURCES_SCHEMA.equals(StrictJson.text(row.get("schema"))),"saved attachment source contract");
            return new Sources(SavedCheckpointMaterial.Kind.valueOf(StrictJson.text(row.get("material_kind"))),CheckpointPairCodec.fileWitnessFromJson(row.get("material_witness")),ExactRef.fromJson(row.get("basis")),ExactRef.fromJson(row.get("game")),
                    ExactRef.fromJson(row.get("opening")),ExactRef.fromJson(row.get("progress")),ExactRef.fromJson(row.get("restored_native")));
        }
    }
    private final CheckpointFiles files;
    private final DriverCheckpointStore drivers;
    private final CheckpointCommitVerifier verifier;
    private final BorrowedSession sessions;
    private final CycleProofVerifier cycles;
    private final HistoricalCycleProofVerifier historicalCycles;
    private final Path root;
    private final java.util.concurrent.ConcurrentHashMap<Path,FileWitness> capturedMaterialWitnesses=new java.util.concurrent.ConcurrentHashMap<>();
    private record ReopenedOriginal(RestoreCheckpointService.OrdinaryReopenCustody custody,SavedMaterial issued) { }
    private final java.util.concurrent.ConcurrentHashMap<String,ReopenedOriginal> reopenedOriginals=new java.util.concurrent.ConcurrentHashMap<>();
    public SavedAttachmentSourceStore(CheckpointFiles files,DriverCheckpointStore drivers,CheckpointCommitVerifier verifier,
            BorrowedSession sessions,Path root,CycleProofVerifier cycles,HistoricalCycleProofVerifier historicalCycles) {
        this.files=Objects.requireNonNull(files);this.drivers=Objects.requireNonNull(drivers);this.verifier=Objects.requireNonNull(verifier);
        this.sessions=Objects.requireNonNull(sessions);this.root=Objects.requireNonNull(root).normalize();
        this.cycles=Objects.requireNonNull(cycles);this.historicalCycles=Objects.requireNonNull(historicalCycles);
        StrictJson.require(root.isAbsolute(),"configured immutable checkpoint material root required");
    }
    /** Root calls this from its actual SAVE verifier adapter before the existing writer lease is released. */
    public SavedMaterial capture(VerifiedCheckpoint verified) throws IOException {
        var borrowed=sessions.current();verifier.requireIssued(borrowed,verified);
        String captureHead=borrowed.head().digest();
        String cycleAuthority=cycles.verify(borrowed,verified.session(),verified.proof());WriterContracts.requireDigest(cycleAuthority);
        Path path=materialPath(verified.pair());var existing=files.observe(path);
        if(existing.isPresent()) {
            var existingWitness=existing.orElseThrow();
            var mapWitness=capturedMaterialWitnesses.get(path);
            if(mapWitness!=null) {
                StrictJson.require(existingWitness.equals(mapWitness),
                        "existing material has no original capture identity custody; supply its persisted original witness");
                SavedMaterial retained=load(verified.pair());
                StrictJson.require(retained.session.equals(verified.session())&&sameProof(retained.proof,verified.proof()),
                        "same physical pair cannot acquire a different original semantic/cycle source");return retained;
            }
            // This is a newly source-qualified current capture witness; the failed preview
            // did not persist its original capture identity, and that identity is not recovered.
            // Requalify against the genuine current VerifiedCheckpoint before publishing any map entry.
            ObjectNode expected=StrictJson.object();expected.put("schema",MATERIAL_SCHEMA);expected.set("pair",StrictJson.parse(CheckpointPairCodec.encode(verified.pair())));
            expected.set("session",session(verified.session()));expected.set("proof",proof(verified.proof()));
            expected.set("original_writer_head",verified.originalHead().toJson());
            expected.put("cycle_authority_sha256",cycleAuthority);
            expected.put("original_writer_head_sha256",verified.originalHeadDigest());expected.put("checkpoint_binding_sha256",verified.digest());
            byte[] expectedBytes=metadataBytes(expected);
            files.verify(existingWitness);
            byte[] actualBytes=files.read(existingWitness,MAX_METADATA);
            StrictJson.require(Arrays.equals(actualBytes,expectedBytes),"orphan material bytes differ from current verified capture identity");
            files.verify(existingWitness);
            SavedMaterial requalified=readMaterial(borrowed,verified.pair(),existingWitness,false);
            files.verify(existingWitness);
            StrictJson.require(sessions.current()==borrowed&&captureHead.equals(borrowed.head().digest()),"orphan requalification changed actual writer head or session");
            var prior=capturedMaterialWitnesses.putIfAbsent(path,existingWitness);
            StrictJson.require(prior==null||prior.equals(existingWitness),"orphan material source conflicts with already captured identity");
            return requalified;
        }
        ObjectNode row=StrictJson.object();row.put("schema",MATERIAL_SCHEMA);row.set("pair",StrictJson.parse(CheckpointPairCodec.encode(verified.pair())));
        row.set("session",session(verified.session()));row.set("proof",proof(verified.proof()));
        row.set("original_writer_head",verified.originalHead().toJson());
        row.put("cycle_authority_sha256",cycleAuthority);
        row.put("original_writer_head_sha256",verified.originalHeadDigest());row.put("checkpoint_binding_sha256",verified.digest());
        FileWitness created=files.createNew(path,metadataBytes(row));files.verify(created);
        FileWitness previous=capturedMaterialWitnesses.putIfAbsent(path,created);
        StrictJson.require(previous==null||previous.equals(created),"material capture original identity conflict");
        return load(verified.pair());
    }
    /** Restart recovery uses the actual immutable index and reruns the archived semantic verifier under the same current writer. */
    public SavedMaterial load(CheckpointPair pair) throws IOException {
        Objects.requireNonNull(pair);var borrowed=sessions.current();
        ReopenedOriginal reopened=reopenedOriginals.get(pairKey(pair));
        if(reopened!=null){requireReopened(borrowed,reopened,pair,true);return reopened.issued();}
        FileWitness manifest=capturedMaterialWitnesses.get(materialPath(pair));
        if(manifest==null)throw new IOException("original captured material identity is unavailable; explicit persisted FileWitness is required");
        return loadOriginal(borrowed,manifest,pair);
    }
    /** Physical/cold producer consumes the previously persisted original identity, never recaptures it from a hash. */
    public SavedMaterial loadOriginal(ContinuityStorePort.Session borrowed,FileWitness originalMaterial,CheckpointPair pair)throws IOException {
        Objects.requireNonNull(originalMaterial);Objects.requireNonNull(pair);
        ReopenedOriginal reopened=reopenedOriginals.get(pairKey(pair));
        if(reopened!=null){
            requireReopened(borrowed,reopened,pair,true);
            StrictJson.require(reopened.issued().witness().equals(originalMaterial),"reopened ordinary original witness changed");return reopened.issued();
        }
        StrictJson.require(sessions.current()==borrowed&&materialPath(pair).equals(Path.of(originalMaterial.reference().path()).normalize()),
                "actual same-writer original material source required");
        files.verify(originalMaterial);SavedMaterial material=readMaterial(borrowed,pair,originalMaterial,false);files.verify(originalMaterial);
        var prior=capturedMaterialWitnesses.putIfAbsent(materialPath(pair),originalMaterial);
        StrictJson.require(prior==null||prior.equals(originalMaterial),"original material source conflicts with already captured identity");return material;
    }
    /** Durable original material only. This never qualifies the current physical pair for reload or grants a new Game. */
    public SavedMaterial loadRetainedOriginal(ContinuityStorePort.Session borrowed,FileWitness originalMaterial,CheckpointPair exactPair)throws IOException {
        Objects.requireNonNull(borrowed);Objects.requireNonNull(originalMaterial);Objects.requireNonNull(exactPair);
        ReopenedOriginal reopened=reopenedOriginals.get(pairKey(exactPair));
        if(reopened!=null){
            requireReopened(borrowed,reopened,exactPair,false);
            StrictJson.require(reopened.issued().witness().equals(originalMaterial),"retained reopened ordinary witness changed");return reopened.issued();
        }
        StrictJson.require(sessions.current()==borrowed,"retained material must borrow this source store's actual original writer");
        StrictJson.require(materialPath(exactPair).normalize().equals(Path.of(originalMaterial.reference().path()).normalize()),"retained material is not this source store's exact original pair index");
        String current=borrowed.head().digest();files.verify(originalMaterial);
        var manifest=files.observe(Path.of(originalMaterial.reference().path())).orElseThrow(()->new IOException("retained saved material original unavailable"));
        StrictJson.require(manifest.equals(originalMaterial),"retained saved material original file identity changed");
        var result=readMaterial(borrowed,exactPair,manifest,true);
        files.verify(originalMaterial);StrictJson.require(current.equals(borrowed.head().digest()),"retained saved material verification mutated canonical head");return result;
    }
    private SavedMaterial readMaterial(ContinuityStorePort.Session borrowed,CheckpointPair pair,FileWitness manifest,boolean retained)throws IOException {
        ObjectNode row=StrictJson.object(FullJsonTree.parse(files.read(manifest,MAX_METADATA),MAX_METADATA),Set.of("schema","pair","session","proof","original_writer_head","original_writer_head_sha256","checkpoint_binding_sha256","cycle_authority_sha256"));
        StrictJson.require(MATERIAL_SCHEMA.equals(StrictJson.text(row.get("schema")))
                &&pair.equals(CheckpointPairCodec.decode(StrictJson.canonical(row.get("pair")))),"immutable material belongs to a different physical pair");
        SessionIdentity source=session(row.get("session"));CompletedCycleProof proof=proof(row.get("proof"));
        String head=StrictJson.text(row.get("original_writer_head_sha256")),digest=StrictJson.text(row.get("checkpoint_binding_sha256"));
        ContinuityState original=ContinuityState.fromJson(object(row.get("original_writer_head")),pair.frame().machineId());
        StrictJson.require(ContinuityJson.digest(original.toJson()).equals(head),"actual original saved writer head differs from captured digest");
        borrowed.requireHistoricalState(original.sequence(),head);
        // Both reads prove the immutable saved cycle against its actual historical state. Physical
        // eligibility is checked separately below; a replacement Game must not impersonate the saved owner.
        String cycleAuthority=historicalCycles.verify(borrowed,source,proof,original);WriterContracts.requireDigest(cycleAuthority);
        StrictJson.require(cycleAuthority.equals(StrictJson.text(row.get("cycle_authority_sha256"))),"actual original cycle authority differs from saved material");
        if(retained)verifier.verifyRetainedOriginal(borrowed,source,pair,proof,head,digest);
        else verifier.verifyHistorical(borrowed,source,pair,proof,head,digest);
        files.verify(manifest);
        return new SavedMaterial(this,pair,source,proof,original,head,digest,manifest,verifier.retainedDriver(borrowed,pair));
    }
    /** Only an admitted private RestoreBinding can transfer this original custody to its replacement aggregate. */
    synchronized SavedMaterial reopenOriginal(ContinuityStorePort.Session same,RestoreCheckpointService.OrdinaryReopenCustody custody)throws IOException {
        Objects.requireNonNull(custody);StrictJson.require(sessions.current()==same,"ordinary reopen requires this actual borrowed writer");
        custody.require(same,this,true);SavedMaterial source=custody.original();String key=pairKey(source.pair());
        StrictJson.require(source.issuer!=this,"ordinary issuer cannot import its own material as replacement custody");
        ReopenedOriginal previous=reopenedOriginals.get(key);
        if(previous!=null){
            StrictJson.require(previous.custody().sameOriginal(custody),"ordinary custody cannot switch its original admitted restoration");
            requireReopened(same,previous,source.pair(),true);return previous.issued();
        }
        StrictJson.require(reopenedOriginals.size()<16&&!capturedMaterialWitnesses.containsKey(materialPath(source.pair())),
                "ordinary custody cannot overwrite captured identity or exceed its finite route inventory");
        var issued=new SavedMaterial(this,source.pair,source.session,source.proof,source.originalHead,
                source.originalHeadDigest,source.checkpointDigest,source.manifest,source.savedDriver);
        var reopened=new ReopenedOriginal(custody,issued);reopenedOriginals.put(key,reopened);
        requireReopened(same,reopened,source.pair(),true);return issued;
    }
    private void requireReopened(ContinuityStorePort.Session same,ReopenedOriginal reopened,CheckpointPair pair,boolean physical)throws IOException {
        StrictJson.require(sessions.current()==same&&reopened.issued().issuer==this&&reopened.issued().pair.equals(pair),
                "ordinary custody crossed pair, aggregate or actual writer");
        String head=same.head().digest();reopened.custody().require(same,this,physical);
        SavedMaterial original=reopened.custody().original(),issued=reopened.issued();
        StrictJson.require(original.pair.equals(issued.pair)&&original.manifest.equals(issued.manifest)
                &&original.session.equals(issued.session)&&sameProof(original.proof,issued.proof)
                &&ContinuityJson.same(original.originalHead.toJson(),issued.originalHead.toJson())
                &&original.originalHeadDigest.equals(issued.originalHeadDigest)
                &&original.checkpointDigest.equals(issued.checkpointDigest)&&original.savedDriver==issued.savedDriver
                &&head.equals(same.head().digest()),"reopened ordinary custody changed original identity, history, Driver or SEM");
    }
    private static String pairKey(CheckpointPair pair){return DriverCheckpointStore.sha256(CheckpointPairCodec.encode(Objects.requireNonNull(pair)));}
    /** Revalidate original material identity/canonical ancestry and return the one actual saved-Driver archive. */
    public DriverStateSnapshot.Complete readRetainedDriver(ContinuityStorePort.Session borrowed,SavedMaterial material)throws IOException {
        Objects.requireNonNull(material);requireOwn(material);return loadRetainedOriginal(borrowed,material.witness(),material.pair()).savedDriver();
    }
    /** Concrete AttachmentPort producer. All four reducer documents come from original saved proof and actual new raw frame. */
    public RestoreCheckpointService.Attachment prepare(RestoreCheckpointService.Request request,
            RestoreCheckpointService.NativeCandidate restored,DriverStateSnapshot.Complete saved) throws IOException {
        SavedMaterial material=load(request.pair());
        StrictJson.require(request.savedMaterial().witness().equals(material.witness()),"request must retain its original ordinary material");
        return prepareMaterial(request,restored,saved,material,basis(sessions.current().head().state(),material),SavedAttachmentAuthority.KIND);
    }
    boolean owns(SavedCheckpointMaterial material){return material instanceof SavedMaterial ordinary&&ordinary.issuer==this;}
    private void requireOwn(SavedMaterial material){StrictJson.require(owns(material),"foreign ordinary saved material issuer");}
    RestoreCheckpointService.Attachment prepareMaterial(RestoreCheckpointService.Request request,
            RestoreCheckpointService.NativeCandidate restored,DriverStateSnapshot.Complete saved,
            SavedCheckpointMaterial material,ObjectNode actualBasis,String kind)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(restored);Objects.requireNonNull(saved);
        var borrowed=sessions.current();var predecessor=borrowed.head().state();
        material.requirePhysical(borrowed);
        StrictJson.require(ContinuityJson.digest(predecessor.toJson()).equals(request.expectedHeadDigest()),"original restore predecessor drift before material production");
        StrictJson.require(Arrays.equals(saved.encode(),material.savedDriver().encode())
                &&Arrays.equals(saved.encode(),drivers.readVerifiedOriginal(request.pair(),saved.session()).encode()),"actual full saved Driver required");
        ObjectNode opening=opening(request,restored);ObjectNode game=restored.actual().session().game().toJson();
        requireOpening(request.pair(),opening,game,restored.originalNativePacket());
        String restoreKey=DriverCheckpointStore.sha256(request.requestId().getBytes(StandardCharsets.UTF_8));
        Path directory=root.resolve("restores").resolve(restoreKey);
        ExactRef basis=immutable(directory.resolve("basis.json"),metadataBytes(actualBasis));
        ExactRef gameRef=immutable(directory.resolve("game.json"),metadataBytes(game));
        ExactRef openingRef=immutable(directory.resolve("opening.json"),metadataBytes(opening));
        ExactRef progress=immutable(directory.resolve("progress.json"),metadataBytes(progress(predecessor)));
        Sources sources=new Sources(material.kind(),material.witness(),basis,gameRef,openingRef,progress,restored.originalNativePacket());
        ObjectNode details=StrictJson.object();details.put("evidence_id",request.requestId());details.put("source","java_saved_checkpoint_restore_v1");
        details.put("new_ordinary_cycle_credit",0);details.put("game_day_credit",0);details.put("original_actions_replayed",false);details.put("window_origin_reset",false);
        details.set(SavedAttachmentAuthority.PAIR_DETAIL,StrictJson.parse(CheckpointPairCodec.encode(request.pair())));details.set(SOURCES_DETAIL,sources.toJson());
        var evidence=new LinkedHashSet<>(sources.references());evidence.add(request.pair().nativeAckRef());
        evidence.add(request.pair().driver().reference());evidence.add(request.pair().save().reference());evidence.addAll(materialEvidence(material));
        var action=new WriterContracts.Request(kind,metadataBytes(details),List.copyOf(evidence));
        SavedAttachmentAuthority.Loaded loaded=loadMaterial(predecessor,action,material,actualBasis);
        return new RestoreCheckpointService.Attachment(action,loaded.input(),material);
    }
    @Override public SavedAttachmentAuthority.Loaded load(ContinuityState predecessor,WriterContracts.Request request) throws IOException {
        StrictJson.require(SavedAttachmentAuthority.KIND.equals(request.kind()),"ordinary attachment kind required");
        Sources sources=Sources.decode(request.detailsObject().get(SOURCES_DETAIL));
        StrictJson.require(sources.kind()==SavedCheckpointMaterial.Kind.ORDINARY,"ordinary source kind required");
        SavedMaterial material=loadOriginal(sessions.current(),sources.material(),SavedAttachmentAuthority.pairFromDetails(request));
        return loadMaterial(predecessor,request,material,basis(predecessor,material));
    }
    SavedAttachmentAuthority.Loaded loadMaterial(ContinuityState predecessor,WriterContracts.Request request,
            SavedCheckpointMaterial material,ObjectNode expectedBasis)throws IOException {
        Objects.requireNonNull(predecessor);Objects.requireNonNull(request);var borrowed=sessions.current();
        StrictJson.require(SavedAttachmentAuthority.kinds().contains(request.kind())
                &&ContinuityJson.same(predecessor.toJson(),borrowed.head().state().toJson()),"source loader must run on the exact original writer predecessor");
        return readDocuments(borrowed,predecessor,request,material,expectedBasis);
    }
    /** Historical DATA replay of an actual prepared transaction; it never relaxes the live predecessor loader. */
    SavedAttachmentAuthority.Loaded loadHistoricalMaterial(ContinuityStorePort.Session same,WriterContracts.Prepared original,
            SavedCheckpointMaterial material,ObjectNode expectedBasis)throws IOException {
        Objects.requireNonNull(original);StrictJson.require(sessions.current()==same,"historical source replay must borrow this actual writer");
        var predecessor=original.predecessor();
        var historical=same.requireHistoricalState(predecessor.state().sequence(),predecessor.digest());
        StrictJson.require(ContinuityJson.same(historical.toJson(),predecessor.state().toJson()),
                "historical prepared predecessor differs from its actual canonical ancestor");
        return readDocuments(same,predecessor.state(),original.request(),material,expectedBasis);
    }
    private SavedAttachmentAuthority.Loaded readDocuments(ContinuityStorePort.Session borrowed,ContinuityState predecessor,
            WriterContracts.Request request,SavedCheckpointMaterial material,ObjectNode expectedBasis)throws IOException {
        StrictJson.require(SavedAttachmentAuthority.kinds().contains(request.kind()),"saved attachment kind required");
        String currentHead=borrowed.head().digest();
        CheckpointPair pair=SavedAttachmentAuthority.pairFromDetails(request);
        Sources sources=Sources.decode(request.detailsObject().get(SOURCES_DETAIL));
        StrictJson.require(material.kind()==sources.kind()&&material.pair().equals(pair)&&material.witness().equals(sources.material()),
                "typed source kind, original witness and pair must agree");
        material.requirePhysical(borrowed);
        files.verify(sources.material);
        StrictJson.require(sources.material.equals(material.witness())&&request.evidence().containsAll(sources.references())
                &&request.evidence().containsAll(materialEvidence(material))
                &&request.evidence().containsAll(List.of(pair.nativeAckRef(),pair.driver().reference(),pair.save().reference())),"writer evidence must include complete exact material/physical/semantic closure");
        byte[] basis=read(sources.basis,MAX_METADATA),game=read(sources.game,MAX_METADATA),opening=read(sources.opening,MAX_METADATA),progress=read(sources.progress,MAX_METADATA);
        StrictJson.require(FullJsonTree.parse(basis,MAX_METADATA).equals(expectedBasis)&&FullJsonTree.parse(progress,MAX_METADATA).equals(progress(predecessor)),
                "original saved frontier and predecessor progress differ from actual producer");
        requireOpening(pair,object(FullJsonTree.parse(opening,MAX_METADATA)),object(FullJsonTree.parse(game,MAX_METADATA)),sources.restoredNative);
        var input=new SavedContinuityAttachment.Input(predecessor,request.details(),basis,game,opening,progress);
        SavedContinuityAttachment.reduce(input);
        for(ExactRef ref:sources.references())read(ref,ref.equals(sources.restoredNative)?MAX_NATIVE+4:MAX_METADATA);
        files.verify(material.witness());
        StrictJson.require(currentHead.equals(borrowed.head().digest()),"canonical writer changed during original source loading");
        return new SavedAttachmentAuthority.Loaded(pair,input,material);
    }
    private ObjectNode opening(RestoreCheckpointService.Request request,RestoreCheckpointService.NativeCandidate actual) {
        var pair=request.pair();var transport=actual.actual().session();var raw=object(FullJsonTree.parse(actual.actual().state().bytes(),MAX_NATIVE));
        var player=object(raw.get("played_character"));var row=StrictJson.object();row.put("schema",OPENING_SCHEMA);
        row.put("machine_id",transport.machineId());row.put("session_id",transport.sessionId());row.set("game",transport.game().toJson());
        row.put("lineage_id",actual.lineageId());row.put("episode_run_id",pair.frame().frame().episodeRunId());
        row.put("snapshot_id",actual.actual().snapshotId());row.put("native_revision",actual.actual().nativeRevision().toString());
        row.set("date_raw",raw.get("date_raw"));row.set("actor_character_id",player.get("character_id"));
        row.set("original_native_packet",actual.originalNativePacket().toJson());
        StrictJson.require(actual.source().machineId().equals(transport.machineId())&&actual.source().exactBuild().equals(request.current().source().exactBuild())
                &&!transport.sessionId().equals(request.current().sessionId())&&actual.lineageId().equals(pair.lineageId()),"actual replacement session/source/lineage required");return row;
    }
    private void requireOpening(CheckpointPair pair,ObjectNode opening,ObjectNode game,ExactRef nativePacket) throws IOException {
        StrictJson.object(opening,Set.of("schema","machine_id","session_id","game","lineage_id","episode_run_id","snapshot_id","native_revision","date_raw","actor_character_id","original_native_packet"));
        GameGeneration replacement=GameGeneration.fromJson(game);
        StrictJson.require(OPENING_SCHEMA.equals(StrictJson.text(opening.get("schema")))&&replacement.equals(GameGeneration.fromJson(opening.get("game")))
                &&!replacement.equals(pair.frame().game())&&pair.frame().machineId().equals(StrictJson.text(opening.get("machine_id")))
                &&pair.lineageId().equals(StrictJson.text(opening.get("lineage_id")))&&pair.frame().frame().episodeRunId().equals(StrictJson.text(opening.get("episode_run_id")))
                &&pair.frame().frame().identity().dateRaw().longValueExact()==StrictJson.integer(opening.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER)
                &&pair.frame().frame().identity().player().equals(NativeCharacterId.fromJson(opening.get("actor_character_id")).asBigInteger())
                &&nativePacket.equals(ExactRef.fromJson(opening.get("original_native_packet"))),"restored raw binding must retain exact machine/episode/actor/date/pair");
        StrictJson.text(opening.get("session_id"));byte[] raw=read(nativePacket,MAX_NATIVE+4);
        StrictJson.require(raw.length>=5,"original framed replacement packet required");
        int length=ByteBuffer.wrap(raw,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        StrictJson.require(length>0&&length<=MAX_NATIVE&&raw.length==length+4,"original replacement LE packet boundary");
        ObjectNode envelope=object(FullJsonTree.parse(Arrays.copyOfRange(raw,4,raw.length),MAX_NATIVE)),state=object(envelope.get("state")),player=object(state.get("played_character"));
        StrictJson.require("state_snapshot".equals(StrictJson.text(envelope.get("type")))&&StrictJson.integer(envelope.get("protocol_version"),1,1)==1
                &&StrictJson.text(envelope.get("snapshot_id")).equals(StrictJson.text(opening.get("snapshot_id")))
                &&nativeRevision(envelope.get("revision")).equals(decimalRevision(opening.get("native_revision")))
                &&yes(state.get("paused"))&&yes(state.get("map_ready"))&&yes(player.get("alive"))
                &&StrictJson.integer(state.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER)==StrictJson.integer(opening.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER)
                &&NativeCharacterId.fromJson(player.get("character_id")).equals(NativeCharacterId.fromJson(opening.get("actor_character_id"))),"actual original replacement packet does not prove paused living restored map");
    }
    ObjectNode basis(ContinuityState predecessor,SavedMaterial material) {
        var pair=material.pair;var before=material.originalHead.toJson();
        var row=StrictJson.object();row.put("machine_id",pair.frame().machineId());
        row.put("completed_cycles",material.proof.completedCycles());var origin=row.putObject("origin");
        origin.set("window_id",before.get("window_id"));origin.set("start_date_raw",before.get("start_date_raw"));origin.set("target_date_raw",before.get("target_date_raw"));origin.set("target_days",before.get("target_days"));
        var frame=row.putObject("frame");frame.put("snapshot_id",pair.frame().frame().snapshotId());frame.put("revision",pair.frame().frame().revision());
        frame.put("native_revision",pair.frame().frame().identity().nativeRevision());frame.put("date_raw",pair.frame().frame().identity().dateRaw());
        frame.put("actor_character_id",pair.frame().frame().identity().player());frame.put("episode_run_id",pair.frame().frame().episodeRunId());
        var refs=row.putObject("refs");refs.set("driver",pair.driver().reference().toJson());refs.set("save",pair.save().reference().toJson());
        refs.set("settled_full_response",material.proof.semantic().semantic().toJson());refs.set("saved_material",material.reference().toJson());
        row.put("identity_schema",FileStatIdentity.SCHEMA);row.set("driver_identity",pair.driver().identity().toJson());row.set("save_identity",pair.save().identity().toJson());
        var checkpoint=row.putObject("checkpoint");checkpoint.put("path",pair.save().reference().path());checkpoint.put("size",pair.save().reference().bytes());
        checkpoint.put("sha256",pair.save().reference().sha256());checkpoint.put("history_index",pair.historyIndex());checkpoint.put("saved_date_raw",pair.frame().frame().identity().dateRaw());
        var goal=row.putObject("campaign_goal_anchor");goal.put("campaign_id",pair.lineageId());goal.put("current_character_id",pair.frame().frame().identity().player());
        row.put("checkpoint_binding_sha256",material.checkpointDigest);
        SavedContinuityAttachment.requireOrdinaryPredecessor(predecessor,metadataBytes(row));return row;
    }
    private static ObjectNode progress(ContinuityState predecessor) {
        var before=predecessor.toJson();var row=StrictJson.object();row.set("ledger_cycles",before.get("last_settled_cycles"));row.set("ledger_date_raw",before.get("last_settled_date_raw"));return row;
    }
    private Path materialPath(CheckpointPair pair){return root.resolve("checkpoints").resolve(DriverCheckpointStore.sha256(CheckpointPairCodec.encode(pair))+".json");}
    private ExactRef immutable(Path target,byte[] raw) throws IOException {
        var existing=files.observe(target);
        if(existing.isPresent()) {
            FileWitness actual=existing.orElseThrow();StrictJson.require(Arrays.equals(files.read(actual,MAX_METADATA),raw),"immutable saved material/source publication conflict");return actual.reference();
        }
        FileWitness created=files.createNew(target,raw);StrictJson.require(Arrays.equals(files.read(created,MAX_METADATA),raw),"immutable saved material readback differs");return created.reference();
    }
    private static byte[] metadataBytes(JsonNode value){return FullJsonTree.encode(value,MAX_METADATA);}
    private byte[] read(ExactRef ref,int limit)throws IOException {
        FileWitness actual=files.observe(Path.of(ref.path())).orElseThrow(()->new IOException("original saved attachment source unavailable"));
        StrictJson.require(actual.reference().equals(ref),"original saved attachment source content or path changed");return files.read(actual,limit);
    }
    private static List<ExactRef> materialEvidence(SavedCheckpointMaterial material){
        var refs=new LinkedHashSet<ExactRef>(material.sourceSemantic().references());
        if(material instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial first){
            refs.add(first.firstMaterial().witness().reference());refs.add(first.baseline().eventRef());
            var checkpoint=first.firstMaterial().checkpoint();refs.add(checkpoint.begin().eventRef());
            refs.add(checkpoint.canonicalSaveReference());refs.add(checkpoint.pairReference());
            refs.addAll(checkpoint.semantic().references());
        }
        return List.copyOf(refs);
    }
    private static ObjectNode session(SessionIdentity value){return OrdinaryCycleTransitions.sessionToJson(value);}
    private static SessionIdentity session(JsonNode value){return OrdinaryCycleTransitions.sessionFromJson(value);}
    private static ObjectNode proof(CompletedCycleProof value){return OrdinaryCycleTransitions.proofToJson(value);}
    private static CompletedCycleProof proof(JsonNode value){return OrdinaryCycleTransitions.proofFromJson(value);}
    private static boolean sameProof(CompletedCycleProof first,CompletedCycleProof second){return proof(first).equals(proof(second));}
    private static ObjectNode object(JsonNode node){StrictJson.require(node instanceof ObjectNode,"saved attachment object required");return (ObjectNode)node;}
    static java.math.BigInteger nativeRevision(JsonNode value){
        StrictJson.require(value!=null&&value.isIntegralNumber(),"exact original native uint64 integer required");
        java.math.BigInteger result=value.bigIntegerValue();
        StrictJson.require(result.signum()>=0&&result.bitLength()<=64,"native revision outside uint64");return result;
    }
    static java.math.BigInteger decimalRevision(JsonNode value){
        String text=StrictJson.text(value);
        StrictJson.require(text.matches("0|[1-9][0-9]*")&&text.length()<=20,"canonical uint64 decimal string required");
        java.math.BigInteger result=new java.math.BigInteger(text);
        StrictJson.require(result.bitLength()<=64,"revision outside uint64");return result;
    }
    private static boolean yes(JsonNode value){return value!=null&&value.isBoolean()&&value.booleanValue();}
}
