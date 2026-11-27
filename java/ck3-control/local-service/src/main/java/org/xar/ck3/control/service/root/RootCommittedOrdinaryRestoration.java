package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore.SavedMaterial;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Original domain input for a committed imported ordinary attachment followed by a new Native connection. */
public final class RootCommittedOrdinaryRestoration {
    private static final String SCHEMA = "xar.java-committed-imported-ordinary-domain-origin/v1";
    private static final int MAXIMUM_BYTES = ContinuityJson.DOCUMENT_MAX_BYTES;
    private final RootRuntimeContext context;
    private final RootSavedOrdinaryReopen.Committed admission;
    private final RootExitedSavedMaterialSource.PreparedImportedRestore oldSource;
    private final SavedMaterial material;
    private final SemanticEvidence semantic;
    private final WriterContracts.Pin basis;

    private RootCommittedOrdinaryRestoration(RootRuntimeContext context, RootSavedOrdinaryReopen.Committed admission,
            RootExitedSavedMaterialSource.PreparedImportedRestore oldSource, SavedMaterial material,
            SemanticEvidence semantic, WriterContracts.Pin basis) {
        this.context = context;
        this.admission = admission;
        this.oldSource = oldSource;
        this.material = material;
        this.semantic = semantic;
        this.basis = basis;
    }

    static RootCommittedOrdinaryRestoration capture(RootRuntimeContext context, ContinuityStorePort.Session same,
            RootSavedOrdinaryReopen.Committed admission, RootExitedSavedMaterialSource.PreparedImportedRestore oldSource,
            Instant deadline) throws IOException {
        admission.requireContext(context);
        admission.requireCurrent(same);
        var retained = Objects.requireNonNull(oldSource).material(same);
        var data = admission.data();
        if (!retained.pair().equals(data.pair()) || !retained.witness().equals(data.materialWitness())
                || retained.importedOrigin().filter(data.importedOrigin()::equals).isEmpty()
                || !retained.session().game().equals(data.pair().frame().game())
                || !retained.session().machineId().equals(data.pair().frame().machineId()))
            throw new IOException("committed imported domain origin requires its exact independent original Saved material");

        // The old attachment's raw READ remains historical. The independently captured SEM is from
        // this new connection and must stay outside the stable identity used by domain imports.
        same.verifyPin(data.recoveryBasis().secondNative());
        var semantic = admission.captureSemantic(same, deadline);
        var history = context.adopted().seed().originalHistoryBasis();
        byte[] bytes = encodeBasis(data, retained, history);
        ExactRef archived = context.archive().preserveArtifact(same, bytes, MAXIMUM_BYTES);
        var basis = same.capturePin(archived, MAXIMUM_BYTES);
        if (!Arrays.equals(bytes, same.readPinned(basis, MAXIMUM_BYTES)))
            throw new IOException("committed imported domain origin differs from its immutable readback");
        var result = new RootCommittedOrdinaryRestoration(context, admission, oldSource, retained, semantic, basis);
        result.requireCurrent(same, context);
        return result;
    }

    private static byte[] encodeBasis(RootSavedOrdinaryReopen.CommittedData data, SavedMaterial material, ExactRef history) {
        var result = StrictJson.object().put("schema", SCHEMA)
                .put("attachment_identity", data.edge().eventIdentity()).put("attachment_sha256", data.attachmentDigest())
                .put("saved_head_sequence", material.originalHeadSequence()).put("saved_head_sha256", material.originalHeadDigest());
        result.set("attachment", data.edge().eventPin().toJson());
        result.set("original_read", data.recoveryBasis().secondNative().toJson());
        result.set("departed", OrdinaryCycleTransitions.sessionToJson(data.recoveryBasis().departed()));
        result.set("successor", OrdinaryCycleTransitions.sessionToJson(data.recoveryBasis().successor()));
        result.set("saved_owner", OrdinaryCycleTransitions.sessionToJson(material.session()));
        result.set("pair", StrictJson.parse(CheckpointPairCodec.encode(data.pair())));
        result.set("saved_material", CheckpointPairCodec.fileWitnessToJson(data.materialWitness()));
        result.set("saved_entry", data.importedOrigin().targetEntry().toJson());
        result.set("saved_confirmation", data.importedOrigin().physicalConfirmation().toJson());
        result.set("history", history.toJson());
        return ContinuityJson.canonical(result);
    }

    public ExactRef basis() { return basis.reference(); }
    public WriterContracts.Pin attachment() { return admission.attachment(); }
    public ContinuityState attachmentHead() { return admission.attachmentHead(); }
    public SavedMaterial material() { return material; }
    public CheckpointPair pair() { return admission.pair(); }
    public SemanticEvidence semantic() { return semantic; }
    public G2Source source() { return context.source(); }
    public SessionIdentity departed() { return admission.data().recoveryBasis().departed(); }
    public SessionIdentity successor() { return admission.successor(); }
    public SavedAttachmentSourceStore.ImportedOrigin importedOrigin() { return admission.data().importedOrigin(); }

    public void requireCurrent(ContinuityStorePort.Session same, RootRuntimeContext actual) throws IOException {
        admission.requireContext(actual);
        admission.requireCurrent(same);
        same.verifyPin(basis);
    }

    @FunctionalInterface
    interface SavedWriterRead<T> {
        T read(ContinuityStorePort.Session oldWriter, ContinuityState savedHead) throws IOException;
    }

    /** Use the source writer that actually owns the pre-SAVE canonical state and original domain bodies. */
    <T> T withOriginalSavedWriter(ContinuityStorePort.Session same, SavedWriterRead<T> work) throws IOException {
        requireCurrent(same, context);
        var result = oldSource.read(same, old -> {
            var retained = old.requireHistoricalState(material.originalHeadSequence(), material.originalHeadDigest());
            if (!Arrays.equals(material.originalHead().canonicalBytes(), retained.canonicalBytes()))
                throw new IOException("original imported Saved head was not retained by the independent source writer");
            return Objects.requireNonNull(work).read(old, retained);
        });
        requireCurrent(same, context);
        return result;
    }
}
