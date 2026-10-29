package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Installed in the sole writer. Both preview and original-lock commit call the real reducer and source loader. */
public final class SavedAttachmentAuthority implements WriterContracts.TransitionAuthority {
    public static final String KIND = "current_saved_checkpoint_cold_verified_v1";
    public static final String PAIR_DETAIL = "java_checkpoint_pair";
    public static java.util.Set<String> kinds(){return java.util.Set.of(KIND,SavedContinuityAttachment.FIRST_ATTACHMENT_KIND);}
    public record Loaded(CheckpointPair pair, SavedContinuityAttachment.Input input,SavedCheckpointMaterial material) {
        public Loaded { Objects.requireNonNull(pair); Objects.requireNonNull(input);Objects.requireNonNull(material);
            StrictJson.require(pair.equals(material.pair()),"loaded original material and physical pair differ"); }
    }
    /** Must reread actual pinned basis/Game/opening/progress and current pair, never return an unchecked JSON shape. */
    @FunctionalInterface public interface SourceLoader { Loaded load(ContinuityState predecessor, WriterContracts.Request request) throws IOException; }
    private final DriverCheckpointStore drivers; private final SourceLoader loader;
    public SavedAttachmentAuthority(DriverCheckpointStore drivers, SourceLoader loader) { this.drivers = Objects.requireNonNull(drivers); this.loader = Objects.requireNonNull(loader); }
    private Loaded checked(ContinuityState predecessor, WriterContracts.Request request) throws IOException {
        StrictJson.require(kinds().contains(request.kind()), "saved attachment event kind"); Loaded actual = loader.load(predecessor, request);
        drivers.verifyOriginal(actual.pair(),actual.material().savedDriver().session());
        StrictJson.require((KIND.equals(request.kind())&&actual.material().kind()==SavedCheckpointMaterial.Kind.ORDINARY)
                ||(SavedContinuityAttachment.FIRST_ATTACHMENT_KIND.equals(request.kind())&&actual.material().kind()==SavedCheckpointMaterial.Kind.FIRST_BASELINE),
                "event kind and actual private material branch differ");
        StrictJson.require(ContinuityJson.same(predecessor.toJson(), actual.input().predecessor().toJson())
                && java.util.Arrays.equals(request.details(), actual.input().details()) && pairFromDetails(request).equals(actual.pair()), "exact original head/details/pair in writer lock");
        requireBasisPair(actual.pair(), actual.input(),actual.material());
        SavedContinuityAttachment.reduce(actual.input()); return actual;
    }
    public static CheckpointPair pairFromDetails(WriterContracts.Request request) {
        return CheckpointPairCodec.decode(ContinuityJson.canonical(ContinuityJson.object(request.detailsObject().get(PAIR_DETAIL))));
    }
    private static void requireBasisPair(CheckpointPair pair, SavedContinuityAttachment.Input input,SavedCheckpointMaterial material) {
        var basis = ContinuityJson.parseObject(input.basis(),65536); var refs=ContinuityJson.object(basis.get("refs"));
        StrictJson.require(pair.driver().reference().equals(ExactRef.fromJson(refs.get("driver"))) && pair.save().reference().equals(ExactRef.fromJson(refs.get("save")))
                && pair.driver().identity().equals(FileStatIdentity.fromJson(basis.get("driver_identity"),StrictJson.text(basis.get("identity_schema"))))
                && pair.save().identity().equals(FileStatIdentity.fromJson(basis.get("save_identity"),StrictJson.text(basis.get("identity_schema")))), "original saved basis exact Driver/SAVE and identities equal physical pair");
        if(material instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial first){
            var typed=SavedContinuityAttachment.FirstBasis.fromJson(basis);var frame=typed.frame();var expected=pair.frame().frame();
            StrictJson.require(typed.firstMaterialRef().equals(first.reference())&&typed.baseline().equals(first.baseline())
                    &&typed.firstPairRef().equals(first.firstMaterial().checkpoint().pairReference())
                    &&typed.firstSaveReceiptRef().equals(first.firstMaterial().checkpoint().canonicalSaveReference())
                    &&typed.checkpointBindingSha256().equals(first.checkpointDigest())
                    &&frame.snapshotId().equals(expected.snapshotId())&&frame.revision().equals(expected.revision())
                    &&frame.nativeRevision().equals(expected.identity().nativeRevision())&&frame.dateRaw()==expected.identity().dateRaw().longValueExact()
                    &&frame.actorCharacterId()==expected.identity().player().longValueExact()&&frame.episodeRunId().equals(expected.episodeRunId())
                    &&typed.lineageId().equals(pair.lineageId())&&typed.historyIndex()==pair.historyIndex(),
                    "FIRST basis must bind the actual BASELINE manifest, original SAVE receipt and exact uint64 frame");
            typed.requirePredecessor(input.predecessor());return;
        }
        StrictJson.require(!basis.has("schema")&&material.kind()==SavedCheckpointMaterial.Kind.ORDINARY,"ordinary saved basis required");
        SavedFrame frame=SavedFrame.fromJson(basis.get("frame")); var expected=pair.frame().frame();
        StrictJson.require(pair.frame().machineId().equals(StrictJson.text(basis.get("machine_id"))) && frame.snapshotId().equals(expected.snapshotId())
                && frame.revision()==expected.revision().longValueExact() && frame.nativeRevision()==expected.identity().nativeRevision().longValueExact()
                && frame.dateRaw()==expected.identity().dateRaw().longValueExact() && frame.actorCharacterId()==expected.identity().player().longValueExact()
                && frame.episodeRunId().equals(expected.episodeRunId()), "basis original saved frame equals paired actual frame");
        var checkpoint=ContinuityJson.object(basis.get("checkpoint")); var goal=ContinuityJson.object(basis.get("campaign_goal_anchor"));
        StrictJson.require(pair.save().reference().path().equals(StrictJson.text(checkpoint.get("path")))
                && pair.save().reference().bytes()==StrictJson.integer(checkpoint.get("size"),1,StrictJson.MAX_SAFE_INTEGER)
                && pair.save().reference().sha256().equals(StrictJson.text(checkpoint.get("sha256")))
                && pair.historyIndex()==StrictJson.integer(checkpoint.get("history_index"),1,StrictJson.MAX_SAFE_INTEGER)
                && frame.dateRaw()==StrictJson.integer(checkpoint.get("saved_date_raw"),0,StrictJson.MAX_SAFE_INTEGER)
                && pair.lineageId().equals(StrictJson.text(goal.get("campaign_id")))
                && frame.actorCharacterId()==NativeCharacterId.fromJson(goal.get("current_character_id")).value(), "canonical checkpoint anchor and campaign lineage bind same physical SAVE");
    }
    @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request request) throws IOException {
        Loaded actual = checked(predecessor,request); var row = StrictJson.object(); row.set("pair", ContinuityJson.parseObject(CheckpointPairCodec.encode(actual.pair()),65536));
        row.set("previous",predecessor.toJson()); row.set("details",ContinuityJson.parseObject(actual.input().details(),65536)); row.set("basis",ContinuityJson.parseObject(actual.input().basis(),65536));
        row.set("game",ContinuityJson.parseObject(actual.input().game(),65536)); row.set("opening",ContinuityJson.parseObject(actual.input().opening(),65536)); row.set("progress",ContinuityJson.parseObject(actual.input().progress(),65536));
        return ContinuityJson.digest(row);
    }
    @Override public ContinuityState reduce(ContinuityState predecessor, WriterContracts.Request request) throws IOException { return SavedContinuityAttachment.reduce(checked(predecessor,request).input()); }
}
