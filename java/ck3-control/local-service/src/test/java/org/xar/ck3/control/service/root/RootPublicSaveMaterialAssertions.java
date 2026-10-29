package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;

/** Actual-input integration assertions. No Root, cycle proof, SAVE pair or material permission is constructed. */
public final class RootPublicSaveMaterialAssertions {
    private RootPublicSaveMaterialAssertions() { }

    /** The actual fixture supplies a current Root with a genuine completed-cycle frontier and physical SAVE support. */
    public static CheckpointResult.Confirmed saveAndRequireMaterial(RootApplicationSession root,
            RootCheckpointPublicCalls.Request request,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(root);Objects.requireNonNull(request);Objects.requireNonNull(deadline);
        var result=root.saveCheckpointPublic(request,deadline);
        require(result.actual() instanceof CheckpointResult.Confirmed,
                "MISSING_ACTUAL_SAVE_POSTSTATE: UNKNOWN/rejection cannot qualify public restore material");
        var confirmed=(CheckpointResult.Confirmed)result.actual();
        require(result.savedDriver().isPresent()&&result.canonicalReceipt().isPresent(),
                "actual public SAVE did not return its verified Driver and original canonical receipt");
        requireMaterial(root,confirmed);return confirmed;
    }

    /** Also accepts a genuine confirmation obtained through the retained UNKNOWN-query regression. */
    public static void requireMaterial(RootApplicationSession root,CheckpointResult.Confirmed confirmed)throws IOException {
        root.writer().locked(same->{
            var scoped=root.archive().withSession(same);
            var reference=scoped.receiptReferenceOf(confirmed.action());
            require(scoped.loadReceipt(reference).equals(confirmed.action()),"SAVE confirmation is not the actual canonical original action");
            var material=root.savedMaterials().currentPhysical(same,confirmed.pair());
            root.savedMaterials().requireOwn(material);material.requirePhysical(same);
            require(material.kind()==SavedCheckpointMaterial.Kind.ORDINARY&&material.pair().equals(confirmed.pair())
                    &&material.session().equals(root.identity()),
                    "SAVE_CONFIRMED did not produce the original ordinary material for this actual Root");
            return null;
        });
    }

    /** Use a fixture whose last explicit SAVE is newer than its Controller pair; this calls the real replacement route once. */
    public static RootCheckpointPublicCalls.RestoreCall restoreAndRequirePublicPair(RootApplicationSession original,
            RootSessionAccess actualAccess,CheckpointResult.Confirmed actualPublicSave,
            RootCheckpointPublicCalls.Request request,Instant deadline)throws IOException,InterruptedException {
        requireMaterial(original,actualPublicSave);
        var result=actualAccess.restoreCheckpointPublic(request,deadline);
        require(result.actual() instanceof RestoreCheckpointService.Restored,
                "MISSING_ACTUAL_RESTORE: UNKNOWN is not a passed public SAVE-to-restore regression");
        var restored=(RestoreCheckpointService.Restored)result.actual();
        require(restored.binding().savedMaterial().pair().equals(actualPublicSave.pair()),
                "public restore selected an older Controller pair instead of the actual newer confirmed public SAVE");
        require(result.published().isPresent()&&original.isRetired()
                &&!result.published().orElseThrow().identity().game().equals(original.identity().game()),
                "actual material was not consumed by a distinct published replacement Game");
        return result;
    }
    private static void require(boolean actual,String message){if(!actual)throw new AssertionError(message);}
}
