package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual restored Root's explicit original-ordinary custody consumer; it publishes no SAVE or process and grants no readiness. */
public final class RootSavedOrdinaryReopen {
    private RootSavedOrdinaryReopen() { }
    public static final class Reopened {
        private final RootRuntimeContext context;private final RestoreCheckpointService service;
        private final RestoreCheckpointService.RestoreBinding binding;private final RootRestorationOriginalProof proof;
        private final SavedAttachmentSourceStore.SavedMaterial material;
        private Reopened(RootRuntimeContext context,RestoreCheckpointService service,
                RestoreCheckpointService.RestoreBinding binding,RootRestorationOriginalProof proof,
                SavedAttachmentSourceStore.SavedMaterial material) {
            this.context=context;this.service=service;this.binding=binding;this.proof=proof;this.material=material;
        }
        public SavedAttachmentSourceStore.SavedMaterial material(){return material;}
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);context.requireRestorationOriginal(same,binding);
            service.requireRetainedOriginal(same,binding);proof.requireCurrent(same);
            context.savedMaterials().requireOwn(material);material.requirePhysical(same);
            var driverSession=context.adopted().session();
            StrictJson.require(binding.pair().equals(material.pair())
                    &&binding.savedMaterial().witness().equals(material.witness())
                    &&binding.savedMaterial().session().equals(material.session())
                    &&binding.savedMaterial().sourceSemantic().equals(material.sourceSemantic())
                    &&binding.session().game().equals(context.game().generation())
                    &&binding.session().sessionId().equals(context.game().sessionId())
                    &&binding.session().machineId().equals(driverSession.machineId())
                    &&binding.session().game().equals(driverSession.game())
                    &&binding.session().sessionId().equals(driverSession.sessionId())
                    &&binding.source().equals(context.source()),
                    "reopened ordinary original or actual replacement context changed");
        }
    }
    /** Called after the actual restored context is bound and before its domain initialization/Host publication. */
    public static Reopened reopen(RootRuntimeContext context,ContinuityStorePort.Session same,
            RestoreCheckpointService actualPreviousService,RestoreCheckpointService.RestoreBinding actualBinding)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(actualPreviousService);Objects.requireNonNull(actualBinding);
        context.writer().requireSession(same);context.requireRestorationOriginal(same,actualBinding);
        if(actualBinding.savedMaterial().kind()!=SavedCheckpointMaterial.Kind.ORDINARY)
            throw new IOException("FIRST checkpoint restoration cannot enter ordinary custody");
        String head=same.head().digest();
        var proof=RootRestorationOriginalProof.requireRetained(context,same,actualBinding);proof.requireCurrent(same);
        var retained=context.restorationOriginal(same);
        var original=RootRestorationOriginalProof.replayOriginal(context,same,retained.basis());
        original.requireImportPredecessor(same,same.head());
        StrictJson.require(original.material().kind()==SavedCheckpointMaterial.Kind.ORDINARY
                &&original.material().witness().equals(actualBinding.savedMaterial().witness())
                &&original.pair().equals(actualBinding.pair())
                &&original.semantic().equals(actualBinding.semantic())
                &&original.game().equals(actualBinding.session().game())
                &&original.sessionId().equals(actualBinding.session().sessionId())
                &&original.source().equals(context.source())
                &&ContinuityJson.same(original.attachmentHead().toJson(),actualBinding.attachment().head().toJson()),
                "private restored Root source/reducer proof differs from its actual ordinary admission");
        var material=actualPreviousService.reopenOrdinaryMaterial(same,actualBinding,context.savedMaterials(),
                actualBinding.session(),actualBinding.semantic());
        StrictJson.require(head.equals(same.head().digest()),"ordinary original custody import mutated the canonical writer");
        var result=new Reopened(context,actualPreviousService,actualBinding,proof,material);result.requireCurrent(same);return result;
    }
}
