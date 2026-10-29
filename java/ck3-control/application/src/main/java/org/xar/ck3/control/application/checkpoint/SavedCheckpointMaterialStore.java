package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** One typed dispatch over the actual ordinary and BASELINE-first stores. Never probes a fallback path. */
public final class SavedCheckpointMaterialStore implements SavedAttachmentAuthority.SourceLoader {
    private final SavedAttachmentSourceStore ordinary;
    private final SavedFirstCheckpointMaterialStore first;
    public SavedCheckpointMaterialStore(SavedAttachmentSourceStore ordinary,SavedFirstCheckpointMaterialStore first){
        this.ordinary=Objects.requireNonNull(ordinary);this.first=Objects.requireNonNull(first);
    }
    /** The actual configured issuers; read-only access never transfers their private material custody. */
    public SavedAttachmentSourceStore ordinaryStore(){return ordinary;}
    public SavedFirstCheckpointMaterialStore firstStore(){return first;}
    public void requireOwn(SavedCheckpointMaterial material){
        StrictJson.require(ordinary.owns(material)||first.owns(material),"material was not minted by these actual configured stores");
    }
    public SavedCheckpointMaterial loadOriginal(ContinuityStorePort.Session same,SavedCheckpointMaterial.Kind kind,FileWitness witness,CheckpointPair pair)throws IOException {
        Objects.requireNonNull(kind);
        return switch(kind){
            case ORDINARY -> ordinary.loadOriginal(same,witness,pair);
            case FIRST_BASELINE -> first.loadBaselinedOriginal(same,witness,pair);
        };
    }
    public SavedCheckpointMaterial loadRetainedOriginal(ContinuityStorePort.Session same,SavedCheckpointMaterial.Kind kind,FileWitness witness,CheckpointPair pair)throws IOException {
        Objects.requireNonNull(kind);
        return switch(kind){
            case ORDINARY -> ordinary.loadRetainedOriginal(same,witness,pair);
            case FIRST_BASELINE -> first.loadRetainedBaselinedOriginal(same,witness,pair);
        };
    }
    public SavedCheckpointMaterial currentPhysical(ContinuityStorePort.Session same,CheckpointPair pair)throws IOException {
        var window=EpisodeWindow.state(same.head().state());
        if(window.isPresent()&&window.orElseThrow().phase()==EpisodeWindow.Phase.ACTIVE){
            var baseline=window.orElseThrow().baseline().orElseThrow();
            if(baseline.saveActionId().equals(pair.saveActionId())){
                StrictJson.require(baseline.pairDigest().equals(DriverCheckpointStore.sha256(CheckpointPairCodec.encode(pair))),
                        "current first SAVE ID cannot be reused for another physical pair");
                return first.currentPhysical(same,pair);
            }
        }
        var material=ordinary.load(pair);material.requirePhysical(same);return material;
    }
    SavedFirstCheckpointMaterialStore.BaselinedMaterial reopenFirstOriginal(ContinuityStorePort.Session same,
            RestoreCheckpointService.FirstReopenCustody actual)throws IOException {
        var reopened=first.reopenOriginal(same,actual);requireOwn(reopened);return reopened;
    }
    /** Actual pre-dispatch basis check. It grants no replacement, raw frame, reducer commit or material authority. */
    void requireRestorePredecessor(ContinuityStorePort.Session same,SavedCheckpointMaterial material)throws IOException {
        requireOwn(material);material.requirePhysical(same);String head=same.head().digest();
        if(material instanceof SavedAttachmentSourceStore.SavedMaterial saved){
            var originalBasis=ordinary.basis(same.head().state(),saved);
            SavedContinuityAttachment.requireOrdinaryPredecessor(same.head().state(),
                    org.xar.ck3.control.contracts.FullJsonTree.encode(originalBasis,1024*1024));
        }else{
            first.basis(same,same.head().state(),(SavedFirstCheckpointMaterialStore.BaselinedMaterial)material);
        }
        StrictJson.require(head.equals(same.head().digest()),"restore preflight changed the canonical predecessor");
    }
    SavedAttachmentSourceStore.SavedMaterial reopenOrdinaryOriginal(ContinuityStorePort.Session same,
            RestoreCheckpointService.OrdinaryReopenCustody actual)throws IOException {
        var reopened=ordinary.reopenOriginal(same,actual);requireOwn(reopened);return reopened;
    }
    SavedAttachmentAuthority.Loaded loadHistoricalOriginal(ContinuityStorePort.Session same,WriterContracts.Prepared original,
            SavedCheckpointMaterial material)throws IOException {
        requireOwn(material);
        var sources=SavedAttachmentSourceStore.Sources.decode(original.request().detailsObject().get(SavedAttachmentSourceStore.SOURCES_DETAIL));
        StrictJson.require(sources.kind()==material.kind()&&sources.material().equals(material.witness())
                &&SavedAttachmentAuthority.pairFromDetails(original.request()).equals(material.pair()),
                "historical attachment must retain its private material kind, witness and pair");
        if(material instanceof SavedAttachmentSourceStore.SavedMaterial saved){
            StrictJson.require(SavedAttachmentAuthority.KIND.equals(original.request().kind()),"ordinary historical kind required");
            return ordinary.loadHistoricalMaterial(same,original,saved,ordinary.basis(original.predecessor().state(),saved));
        }
        StrictJson.require(SavedContinuityAttachment.FIRST_ATTACHMENT_KIND.equals(original.request().kind()),"FIRST historical kind required");
        var saved=(SavedFirstCheckpointMaterialStore.BaselinedMaterial)material;
        return ordinary.loadHistoricalMaterial(same,original,saved,first.basis(same,original.predecessor().state(),saved).toJson());
    }
    public RestoreCheckpointService.Attachment prepare(RestoreCheckpointService.Request request,
            RestoreCheckpointService.NativeCandidate restored,DriverStateSnapshot.Complete saved)throws IOException {
        var material=request.savedMaterial();requireOwn(material);
        if(material instanceof SavedAttachmentSourceStore.SavedMaterial)return ordinary.prepare(request,restored,saved);
        var actual=(SavedFirstCheckpointMaterialStore.BaselinedMaterial)material;
        return ordinary.prepareMaterial(request,restored,saved,actual,first.basisSession(request,actual).toJson(),SavedContinuityAttachment.FIRST_ATTACHMENT_KIND);
    }
    @Override public SavedAttachmentAuthority.Loaded load(ContinuityState predecessor,WriterContracts.Request request)throws IOException {
        var sources=SavedAttachmentSourceStore.Sources.decode(request.detailsObject().get(SavedAttachmentSourceStore.SOURCES_DETAIL));
        if(SavedAttachmentAuthority.KIND.equals(request.kind())){
            StrictJson.require(sources.kind()==SavedCheckpointMaterial.Kind.ORDINARY,"ordinary event requires ordinary material");
            return ordinary.load(predecessor,request);
        }
        StrictJson.require(SavedContinuityAttachment.FIRST_ATTACHMENT_KIND.equals(request.kind())
                &&sources.kind()==SavedCheckpointMaterial.Kind.FIRST_BASELINE,"explicit FIRST event requires BASELINE material");
        return first.loadAttachment(ordinary,predecessor,request,sources);
    }
}
