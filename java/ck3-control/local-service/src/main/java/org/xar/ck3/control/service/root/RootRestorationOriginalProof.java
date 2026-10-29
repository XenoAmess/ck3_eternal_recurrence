package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.readiness.ReadinessArchive;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;

/**
 * Original domain material from one genuinely admitted restoration.
 * This evidence grants neither current readiness, a physical reload nor a second restore.
 */
public final class RootRestorationOriginalProof {
    private static final String SCHEMA="xar.java.restoration-domain-originals/v3";
    private static final int METADATA_MAX=1024*1024;
    private final RootRuntimeContext context;
    private final RestoreCheckpointService.RestoreBinding admitted;
    private final SavedCheckpointMaterial material;
    private final ObjectNode original;
    private RootRestorationOriginalProof(RootRuntimeContext context,RestoreCheckpointService.RestoreBinding admitted,
            SavedCheckpointMaterial material,ObjectNode original) {
        this.context=context;this.admitted=admitted;this.material=material;this.original=original.deepCopy();
    }
    public static RootRestorationOriginalProof require(RootRuntimeContext context,ContinuityStorePort.Session same,
            RestoreCheckpointService.RestoreBinding actual)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(actual);
        context.requireRestorationOriginal(same,actual);
        // The real restore producer retained this sealed private material before physical replacement.
        var material=actual.savedMaterial();material.requireRetained(same);
        var transaction=actual.originalAttachment();var request=transaction.request();
        StrictJson.require(SavedAttachmentAuthority.kinds().contains(request.kind())
                && SavedAttachmentAuthority.pairFromDetails(request).equals(actual.pair())
                && actual.attachment().disposition()!=WriterContracts.Disposition.NO_CHANGE
                && actual.attachment().eventIdentity().equals(request.identity()),
                "actual original restore attachment transaction is required");
        var row=StrictJson.object();row.put("schema",SCHEMA);row.put("machine_id",actual.session().machineId());
        row.set("session",OrdinaryCycleTransitions.sessionToJson(actual.session()));
        row.set("source",StrictJson.parse(G2Wire.sourceBytes(actual.source())));
        row.set("pair",StrictJson.parse(CheckpointPairCodec.encode(actual.pair())));
        row.put("saved_material_kind",material.kind().name());
        row.set("saved_material_witness",CheckpointPairCodec.fileWitnessToJson(material.witness()));
        row.set("semantic",OrdinaryCycleTransitions.semanticToJson(actual.semantic()));
        row.set("original_history_basis",actual.originalHistoryBasis().toJson());
        row.set("attachment_predecessor",transaction.predecessor().state().toJson());
        row.set("attachment_head",actual.attachment().head().toJson());
        row.put("event_identity",actual.attachment().eventIdentity());row.put("kind",request.kind());
        row.set("details",request.detailsObject());
        var refs=row.putArray("request_evidence");request.evidence().forEach(ref->refs.add(ref.toJson()));
        var result=new RootRestorationOriginalProof(context,actual,material,row);
        result.requireCurrent(same);return result;
    }
    public ExactRef preserveOriginal(ContinuityStorePort.Session same)throws IOException {
        requireCurrent(same);
        var archive=context.archive().withSession(same);
        ExactRef basis=archive.preserveMaterial(new RawJson(ContinuityJson.canonical(original)));
        Original replayed=replayOriginal(context,same,basis);
        StrictJson.require(replayed.material().kind()==material.kind()&&replayed.material().witness().equals(material.witness()),
                "restoration original readback changed its private saved material");
        return basis;
    }
    /** Reuse the actually captured immutable input during the same early domain-import chain. */
    public static RootRestorationOriginalProof requireRetained(RootRuntimeContext context,ContinuityStorePort.Session same,
            RestoreCheckpointService.RestoreBinding actual)throws IOException {
        context.requireRestorationOriginal(same,actual);
        var original=context.restorationOriginal(same);
        var raw=context.archive().withSession(same).loadMaterial(original.basis());
        var row=ContinuityJson.parseObject(raw.bytes(),WriterContracts.MAX_PIN_BYTES);
        var result=new RootRestorationOriginalProof(context,actual,original.material(),row);
        result.requireCurrent(same);return result;
    }
    public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
        context.requireRestorationOriginal(same,admitted);
        var attachment=admitted.attachment().head();
        same.requireHistoricalState(attachment.sequence(),ContinuityJson.digest(attachment.toJson()));
        requireImportShape(attachment,same.head().state());
        StrictJson.require(material.pair().equals(admitted.pair())
                &&material.kind()==admitted.savedMaterial().kind()&&material.witness().equals(admitted.savedMaterial().witness())
                && material.session().machineId().equals(context.game().machineId())
                && admitted.session().game().equals(context.game().generation())
                && admitted.session().sessionId().equals(context.game().sessionId())
                && admitted.source().equals(context.source()),
                "restoration original crossed the genuinely admitted replacement");
    }
    public static Original replayOriginal(RootRuntimeContext context,ContinuityStorePort.Session same,ExactRef basis)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(basis);context.writer().requireSession(same);
        var archive=context.archive().withSession(same);RawJson raw=archive.loadMaterial(basis);
        StrictJson.require(archive.materialReferenceOf(raw).equals(basis),"restoration original basis bytes changed");
        var row=StrictJson.object(ContinuityJson.parseObject(raw.bytes(),WriterContracts.MAX_PIN_BYTES),
                Set.of("schema","machine_id","session","source","pair","saved_material_kind","saved_material_witness","semantic","original_history_basis",
                        "attachment_predecessor","attachment_head","event_identity","kind","details","request_evidence"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))
                &&context.game().machineId().equals(StrictJson.text(row.get("machine_id"))),
                "restoration original schema or machine differs");
        var owner=OrdinaryCycleTransitions.sessionFromJson(row.get("session"));var source=G2Wire.source(row.get("source"));
        var pair=CheckpointPairCodec.decode(StrictJson.canonical(row.get("pair")));
        var semantic=OrdinaryCycleTransitions.semanticFromJson(row.get("semantic"));
        var previous=ContinuityState.fromJson(row.get("attachment_predecessor"),owner.machineId());
        var after=ContinuityState.fromJson(row.get("attachment_head"),owner.machineId());
        same.requireHistoricalState(previous.sequence(),ContinuityJson.digest(previous.toJson()));
        same.requireHistoricalState(after.sequence(),ContinuityJson.digest(after.toJson()));
        StrictJson.require(row.get("request_evidence").isArray()&&row.get("request_evidence").size()<=64,
                "bounded original attachment evidence required");
        var declared=new java.util.ArrayList<ExactRef>();
        for(JsonNode ref:row.get("request_evidence"))declared.add(ExactRef.fromJson(ref));
        var request=new WriterContracts.Request(StrictJson.text(row.get("kind")),StrictJson.canonical(row.get("details")),declared);
        StrictJson.require(SavedAttachmentAuthority.kinds().contains(request.kind())
                &&pair.equals(SavedAttachmentAuthority.pairFromDetails(request))
                &&request.identity().equals(StrictJson.text(row.get("event_identity")))
                &&request.identity().equals(StrictJson.text(after.toJson().get("last_event_identity")))
                &&after.sequence()==Math.addExact(previous.sequence(),1),
                "restoration original is not its actual immediate canonical attachment");
        var sources=SavedAttachmentSourceStore.Sources.decode(request.detailsObject().get(SavedAttachmentSourceStore.SOURCES_DETAIL));
        MaterialIdentity materialIdentity=requireMaterialIdentity(row,sources);
        CheckpointPair.FileWitness materialWitness=materialIdentity.witness();
        // The sole saved-material producer reruns archived SAVE/Driver/SEM and canonical ancestry.
        // It deliberately grants no physical reload and does not compare today's overwritten SAVE path.
        var saved=context.loadRestorationMaterialOriginal(same,materialIdentity.kind(),materialWitness,pair);
        StrictJson.require(saved.kind()==materialIdentity.kind()&&saved.witness().equals(materialWitness)&&saved.pair().equals(pair),
                "actual aggregate material loader changed the explicit kind, original identity or physical pair");
        saved.requireRetained(same);
        var sourceRefs=new LinkedHashSet<ExactRef>(sources.references());
        StrictJson.require(request.evidence().containsAll(sourceRefs),"attachment did not preserve its complete original reducer source closure");
        byte[] savedBasis=read(context,same,sources.basis(),METADATA_MAX);
        byte[] game=read(context,same,sources.game(),METADATA_MAX);
        byte[] opening=read(context,same,sources.opening(),METADATA_MAX);
        byte[] progress=read(context,same,sources.progress(),METADATA_MAX);
        var reduced=SavedContinuityAttachment.reduce(new SavedContinuityAttachment.Input(previous,request.details(),savedBasis,game,opening,progress)).toJson();
        reduced.put("sequence",after.sequence());reduced.put("last_event_identity",request.identity());
        StrictJson.require(reduced.equals(after.toJson()),"actual original saved attachment reducer differs from the canonical successor");
        var savedBasisRow=ContinuityJson.parseObject(savedBasis,METADATA_MAX);
        requireMaterialBasis(saved,savedBasisRow,request.kind());
        requireBinding(owner,source,semantic,pair,game,opening,sources);
        context.semanticVerifier().verify(same,owner,semantic);
        ExactRef history=ExactRef.fromJson(row.get("original_history_basis"));
        read(context,same,history,ReadinessArchive.Role.DRIVER.maximumBytes());
        var driver=DriverStateSnapshot.decodeComplete(read(context,same,semantic.originalDriver(),ReadinessArchive.Role.DRIVER.maximumBytes()));
        StrictJson.require(driver.session().bridgePid()==owner.game().pid()
                &&driver.session().actorId().equals(semantic.frame().frame().identity().player())
                &&driver.session().episodeRunId().equals(pair.frame().frame().episodeRunId()),
                "original restored complete Driver differs from exact replacement player/episode");
        var refs=new LinkedHashSet<ExactRef>(sourceRefs);refs.add(basis);refs.add(history);refs.addAll(semantic.references());
        for(ExactRef ref:refs)read(context,same,ref,WriterContracts.MAX_PIN_BYTES);
        return new Original(context,basis,saved,owner,source,semantic,after,List.copyOf(refs));
    }
    /** Legacy digest-only material metadata cannot acquire original physical identity retroactively. */
    record MaterialIdentity(SavedCheckpointMaterial.Kind kind,CheckpointPair.FileWitness witness) {
        MaterialIdentity {Objects.requireNonNull(kind);Objects.requireNonNull(witness);}
    }
    static MaterialIdentity requireMaterialIdentity(JsonNode original,SavedAttachmentSourceStore.Sources sources) {
        Objects.requireNonNull(sources);
        StrictJson.require(SCHEMA.equals(StrictJson.text(original.get("schema"))),
                "explicit original and attachment FileWitness contracts required; legacy material is unqualified");
        var material=CheckpointPairCodec.fileWitnessFromJson(original.get("saved_material_witness"));
        var kind=SavedCheckpointMaterial.Kind.valueOf(StrictJson.text(original.get("saved_material_kind")));
        StrictJson.require(kind==sources.kind()&&material.equals(sources.material()),
                "restoration material differs from actual source-bound attachment identity");
        return new MaterialIdentity(kind,material);
    }
    private static void requireMaterialBasis(SavedCheckpointMaterial saved,ObjectNode basis,String attachmentKind) {
        var refs=ContinuityJson.object(basis.get("refs"));var pair=saved.pair();
        StrictJson.require(pair.driver().reference().equals(ExactRef.fromJson(refs.get("driver")))
                &&pair.save().reference().equals(ExactRef.fromJson(refs.get("save"))),"actual retained material must bind its exact Driver/SAVE pair");
        switch(saved.kind()) {
            case ORDINARY -> {
                StrictJson.require(saved instanceof SavedAttachmentSourceStore.SavedMaterial
                        &&SavedAttachmentAuthority.KIND.equals(attachmentKind)
                        &&materialReference(saved).equals(ExactRef.fromJson(refs.get("saved_material")))
                        &&saved.sourceSemantic().semantic().equals(ExactRef.fromJson(refs.get("settled_full_response"))),
                        "ordinary original must retain its real completed-cycle material and semantic basis");
            }
            case FIRST_BASELINE -> {
                if(!(saved instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial first))
                    throw new IllegalArgumentException("FIRST requires the actual private baselined material, not retained first DATA");
                var actual=SavedContinuityAttachment.FirstBasis.fromJson(basis);
                StrictJson.require(SavedContinuityAttachment.FIRST_ATTACHMENT_KIND.equals(attachmentKind)
                        &&actual.firstMaterialRef().equals(materialReference(saved))&&actual.baseline().equals(first.baseline())
                        &&actual.driverIdentity().equals(pair.driver().identity())&&actual.saveIdentity().equals(pair.save().identity())
                        &&actual.checkpointBindingSha256().equals(saved.checkpointDigest())
                        &&actual.firstPairRef().equals(first.baseline().baseline().pairRef())
                        &&actual.firstSaveReceiptRef().equals(first.baseline().baseline().canonicalSaveReceiptRef())
                        &&!refs.has("settled_full_response"),"FIRST basis must preserve the actual strong BASELINE manifest, pair, SAVE receipt and file identities");
            }
        }
    }
    private static ExactRef materialReference(SavedCheckpointMaterial material) {return material.witness().reference();}
    public static final class Original {
        private final RootRuntimeContext context;
        private final ExactRef basis;
        private final SavedCheckpointMaterial saved;
        private final SessionIdentity owner;
        private final G2Source source;
        private final SemanticEvidence semantic;
        private final ContinuityState attachmentHead;
        private final List<ExactRef> evidence;
        private Original(RootRuntimeContext context,ExactRef basis,SavedCheckpointMaterial saved,
                SessionIdentity owner,G2Source source,SemanticEvidence semantic,ContinuityState attachmentHead,List<ExactRef> evidence) {
            this.context=context;this.basis=basis;this.saved=saved;this.owner=owner;this.source=source;
            this.semantic=semantic;this.attachmentHead=attachmentHead;this.evidence=evidence;
        }
        public ExactRef basis(){return basis;}
        public SavedCheckpointMaterial material(){return saved;}
        public ContinuityState originalSavedHead(){return saved.originalHead();}
        public ContinuityState attachmentHead(){return attachmentHead;}
        public CheckpointPair pair(){return saved.pair();}
        public GameGeneration game(){return owner.game();}
        public String sessionId(){return owner.sessionId();}
        public G2Source source(){return source;}
        public SemanticEvidence semantic(){return semantic;}
        public List<ExactRef> evidence(){return evidence;}
        public void requireImportPredecessor(ContinuityStorePort.Session same,WriterContracts.Head actual)throws IOException {
            context.writer().requireSession(same);Objects.requireNonNull(actual);
            same.requireHistoricalState(actual.state().sequence(),actual.digest());
            requireImportShape(attachmentHead,actual.state());
        }
    }
    private static void requireBinding(SessionIdentity owner,G2Source source,SemanticEvidence semantic,CheckpointPair pair,
            byte[] game,byte[] opening,SavedAttachmentSourceStore.Sources sources) {
        var raw=ContinuityJson.parseObject(opening,METADATA_MAX);
        StrictJson.require(owner.machineId().equals(pair.frame().machineId())&&source.machineId().equals(owner.machineId())
                &&owner.game().equals(GameGeneration.fromJson(StrictJson.parse(game)))
                &&owner.game().equals(semantic.frame().game())&&owner.machineId().equals(semantic.frame().machineId())
                &&owner.sessionId().equals(StrictJson.text(raw.get("session_id")))
                &&owner.game().equals(GameGeneration.fromJson(raw.get("game")))
                &&semantic.originalNativePacket().equals(sources.restoredNative())
                &&pair.frame().frame().episodeRunId().equals(semantic.frame().frame().episodeRunId())
                &&pair.frame().frame().identity().player().equals(semantic.frame().frame().identity().player())
                &&pair.frame().frame().identity().dateRaw().equals(semantic.frame().frame().identity().dateRaw()),
                "actual restored original source/session/Game/actor/date differs from loaded SAVE");
    }
    private static byte[] read(RootRuntimeContext context,ContinuityStorePort.Session same,ExactRef ref,int maximum)throws IOException {
        var pin=same.capturePin(ref,maximum);byte[] bytes=same.readPinned(pin,maximum);same.verifyPin(pin);return bytes;
    }
    private static ObjectNode importShape(ContinuityState state) {
        ObjectNode value=state.toJson().deepCopy();value.remove(Set.of("sequence","last_event_identity",DomainBodies.FIELD));return value;
    }
    private static void requireImportShape(ContinuityState attachment,ContinuityState actual) {
        StrictJson.require(actual.sequence()>=attachment.sequence()&&importShape(attachment).equals(importShape(actual)),
                "restoration domain import is outside its original attachment and domain-import chain");
    }
}

