package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Durable family pending consumes the coordinator's actual successful primitive preparation, then replays the same originals. */
public final class RootFamilyPendingSources implements FamilyPendingStore.Sources {
    private static final String SCHEMA="xar.java.family-actual-preparation-custody/v1";
    private static final int MAX=1_048_576;
    private final RootRuntimeContext context;private final RootFamilyBridge bridge;
    private final FamilyNativePreparation.Replay nativeReplay;private final ExactRef replayImplementation;
    public RootFamilyPendingSources(RootRuntimeContext context,RootFamilyBridge bridge,
            FamilyNativePreparation.Replay actualNativeReplay,ExactRef actualReplayImplementation) {
        this.context=Objects.requireNonNull(context);this.bridge=Objects.requireNonNull(bridge);nativeReplay=Objects.requireNonNull(actualNativeReplay);
        replayImplementation=Objects.requireNonNull(actualReplayImplementation);StrictJson.require(replayImplementation.bytes()>0,"actual native family replay implementation required");
    }
    @Override public FamilyPendingStore.Basis current(Session same,ActionCommand command)throws IOException {
        context.writer().requireSession(same);NativeRequest prepared=ActionPreparationScope.requirePrepared(same,command);
        requirePrepared(command,prepared);var archive=context.archive().withSession(same);
        var verified=nativeReplay.replay(command,prepared,archive);check(same,command,verified);
        ActionReadPublicationScope.requireClearBeforeIntent(same,command);
        ExactRef originalRequest=archive.preserveRequest(prepared);
        var body=StrictJson.object().put("schema",SCHEMA).put("command_sha256",ActionCodec.sha256(ActionCodec.encodeCommand(command)));
        body.set("prepared_request",originalRequest.toJson());body.set("replay_implementation",replayImplementation.toJson());
        var refs=body.putArray("preparation_evidence");prepared.preparationEvidence().forEach(ref->refs.add(ref.toJson()));
        ExactRef manifest=archive.preserveMaterial(new RawJson(StrictJson.canonical(body,MAX)));
        return basis(verified,List.of(manifest));
    }
    @Override public FamilyPendingStore.Basis replay(ActionCommand command,ExactRef snapshotEvidence,ExactRef bridgeEvidence,List<ExactRef> nativePreparationEvidence)throws IOException {
        StrictJson.require(nativePreparationEvidence.size()==1,"one actual preparation custody manifest required");
        var same=context.borrowedSession();context.writer().requireSession(same);var archive=context.archive().withSession(same);
        ExactRef manifest=nativePreparationEvidence.getFirst();var raw=archive.loadMaterial(manifest);
        StrictJson.require(archive.materialReferenceOf(raw).equals(manifest),"actual family preparation custody identity differs");
        var body=StrictJson.object(StrictJson.parse(raw.bytes(),MAX),Set.of("schema","command_sha256","prepared_request","replay_implementation","preparation_evidence"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(body.get("schema")))
                && ActionCodec.sha256(ActionCodec.encodeCommand(command)).equals(StrictJson.text(body.get("command_sha256")))
                && ExactRef.fromJson(body.get("replay_implementation")).bytes()>0,"family preparation custody source/command differs");
        ExactRef originalRequest=ExactRef.fromJson(body.get("prepared_request"));NativeRequest prepared=archive.loadRequest(originalRequest);
        StrictJson.require(archive.requestReferenceOf(prepared).equals(originalRequest),"original prepared family request identity differs");requirePrepared(command,prepared);
        var evidence=body.get("preparation_evidence");StrictJson.require(evidence.isArray() && evidence.size()==prepared.preparationEvidence().size(),"prepared original evidence count differs");
        for(int index=0;index<evidence.size();index++)StrictJson.require(ExactRef.fromJson(evidence.get(index)).equals(prepared.preparationEvidence().get(index)),"prepared evidence order/identity differs");
        var verified=nativeReplay.replay(command,prepared,archive);check(same,command,verified);
        StrictJson.require(verified.snapshotEvidence().equals(snapshotEvidence) && verified.bridgeEvidence().equals(bridgeEvidence),"family native replay changed its original snapshot/Bridge refs");
        return basis(verified,nativePreparationEvidence);
    }
    private static void requirePrepared(ActionCommand command,NativeRequest prepared) {
        StrictJson.require(FamilyPendingProducer.supports(command) && command.origin() instanceof CommandOrigin.Gameplay
                && prepared.step().equals(command.operation().value()) && !prepared.preparationEvidence().isEmpty(),"actual complete primitive family preparation required");
    }
    private void check(Session same,ActionCommand command,FamilyNativePreparation.VerifiedBasis verified)throws IOException {
        var original=bridge.replay(same,verified.bridgeEvidence());var frame=original.frame();
        StrictJson.require(frame.identity().equals(command.before()) && frame.source().equals(command.source()) && frame.sessionId().equals(command.sessionId())
                && original.observation().identity().equals(verified.bridgeIdentity()) && original.semantic().equals(verified.snapshotEvidence())
                && frame.semantic().equals(verified.snapshot()),"native family replay lacks the identical actual full Driver/Bridge basis");
    }
    private static FamilyPendingStore.Basis basis(FamilyNativePreparation.VerifiedBasis verified,List<ExactRef> evidence) {
        return new FamilyPendingStore.Basis(verified.snapshot(),verified.bridgeIdentity(),verified.snapshotEvidence(),verified.bridgeEvidence(),evidence,
                verified.preparedPlan().orElseThrow(()->new IllegalArgumentException("native archive replay did not rebuild the actual fresh selected plan")),
                verified.materializedSend().orElseThrow(()->new IllegalArgumentException("actual native before context has no qualified materialized sender/role arity")));
    }
}
