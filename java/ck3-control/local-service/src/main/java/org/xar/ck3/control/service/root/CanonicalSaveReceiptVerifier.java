package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.session.SessionPorts.CompletedCycleProof;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Replays the original canonical SAVE evidence without submitting or constructing an applied receipt. */
public final class CanonicalSaveReceiptVerifier implements CheckpointCommitVerifier.SaveReceiptVerifier, FirstSaveReceiptVerifier {
    private final ContinuityStorePort writer;
    private final ActionSnapshotReader actions;
    private final ActionPorts.OutcomeArchive archive;
    private final CheckpointFiles files;
    private final DriverCheckpointStore drivers;
    public CanonicalSaveReceiptVerifier(ContinuityStorePort writer, ActionSnapshotReader actions,
            ActionPorts.OutcomeArchive archive, CheckpointFiles files, DriverCheckpointStore drivers) {
        this.writer=Objects.requireNonNull(writer);this.actions=Objects.requireNonNull(actions);
        this.archive=Objects.requireNonNull(archive);this.files=Objects.requireNonNull(files);
        this.drivers=Objects.requireNonNull(drivers);
    }
    /** Installed in the one executable catalog. The proposed receipt is still rederived from actual originals. */
    public NativeRecordedEvidenceVerifier.Binding archivedBinding(ExactRef definitionSource,CheckpointService.BorrowedSession sessions) {
        Objects.requireNonNull(sessions);
        return new NativeRecordedEvidenceVerifier.Binding(new OperationKey("save-checkpoint"),definitionSource,(head,proposed,bound)->{
            try {
                var same=sessions.current();writer.requireSession(same);
                StrictJson.require(head.digest().equals(same.head().digest()),"SAVE archived verifier did not borrow the actual writer head");
                boolean recorded=actions.withFrozen(same,held->{
                    boolean exact=held.find(proposed.command().actionId()).filter(proposed::equals).isPresent();held.assertCurrent();return exact;
                });
                // Only an actual already canonical complete receipt has historical scope. A proposed
                // settlement replacing ACK/UNKNOWN still needs the present physical pair before commit.
                verifyOriginal(same,proposed,bound,!recorded);
            }catch(IOException failure){throw new UncheckedIOException("actual same-writer SAVE originals are unavailable",failure);}
        });
    }
    @Override public String verify(ContinuityStorePort.Session same,SessionIdentity owner,CheckpointPair pair,
            CompletedCycleProof cycle)throws IOException {
        return verifySaved(same,owner,pair,cycle,true);
    }
    @Override public String verifyRetained(ContinuityStorePort.Session same,SessionIdentity owner,CheckpointPair pair,
            CompletedCycleProof cycle)throws IOException {
        return verifySaved(same,owner,pair,cycle,false);
    }
    @Override public DriverStateSnapshot.Complete retainedDriver(ContinuityStorePort.Session same,CheckpointPair pair)throws IOException {
        writer.requireSession(same);
        try {
            var receipt=actions.withFrozen(same,held->{var found=held.find(pair.saveActionId()).orElseThrow();held.assertCurrent();return found;});
            var bound=archive.withSession(same);verifyOriginal(same,receipt,bound,false);
            var actual=receipt.applied().orElseThrow().observation();
            StrictJson.require(pair.equals(CheckpointPairCodec.decode(bound.loadMaterial(actual.supportingEvidence().getFirst()).bytes())),"retained original saved Driver belongs to another pair");
            return DriverStateSnapshot.decodeComplete(bound.loadMaterial(actual.supportingEvidence().get(1)).bytes());
        }catch(UncheckedIOException failure){throw failure.getCause();}
    }
    private String verifySaved(ContinuityStorePort.Session same,SessionIdentity owner,CheckpointPair pair,
            CompletedCycleProof cycle,boolean physical)throws IOException {
        Objects.requireNonNull(cycle);
        return verifyFirst(same,owner,pair,cycle.semantic().frame(),physical).digest();
    }
    @Override public FirstSaveReceiptVerifier.Original verifyFirst(ContinuityStorePort.Session same,SessionIdentity owner,
            CheckpointPair pair,ObservationIdentity opening,boolean physical)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(owner);Objects.requireNonNull(pair);Objects.requireNonNull(opening);
        String head=same.head().digest();
        try {
            ActionReceipt receipt=actions.withFrozen(same,held->{
                var found=held.find(pair.saveActionId()).orElseThrow(()->new IllegalArgumentException("physical pair lacks its canonical original SAVE"));
                held.assertCurrent();return found;
            });
            var command=receipt.command();
            StrictJson.require(receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                    &&receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Applied
                    &&command.operation().equals(new OperationKey("save-checkpoint"))
                    &&command.origin() instanceof CommandOrigin.Gameplay
                    &&command.before().equals(opening)
                    &&owner.machineId().equals(command.before().machineId())&&owner.game().equals(command.before().game())
                    &&owner.sessionId().equals(command.sessionId())
                    &&command.expected().observerSchema().equals(CheckpointRequestFactory.OBSERVER_SCHEMA),
                    "canonical settled primitive SAVE must bind this original opening/session");
            var bound=archive.withSession(same);String originals=verifyOriginal(same,receipt,bound,physical);
            ExactRef pairRef=receipt.applied().orElseThrow().observation().supportingEvidence().getFirst();
            CheckpointPair actualPair=CheckpointPairCodec.decode(bound.loadMaterial(pairRef).bytes());
            StrictJson.require(actualPair.equals(pair),"canonical SAVE belongs to another physical checkpoint pair");
            ExactRef receiptRef=bound.receiptReferenceOf(receipt);
            StrictJson.require(bound.loadReceipt(receiptRef).equals(receipt),"actual canonical SAVE receipt archive readback differs");
            var material=StrictJson.object();material.put("schema","xar.canonical-save-receipt-binding/v2");
            material.set("receipt",receiptRef.toJson());material.put("originals_sha256",originals);
            StrictJson.require(head.equals(same.head().digest()),"canonical SAVE verification changed the original writer head");
            var savedDriver=drivers.readArchivedSnapshot(pair,bound.loadMaterial(receipt.applied().orElseThrow().observation().supportingEvidence().get(1)).bytes());
            writer.requireSession(same);return new FirstSaveReceiptVerifier.Original(ContinuityJson.digest(material),receipt,receiptRef,pairRef,savedDriver);
        }catch(UncheckedIOException failure){throw failure.getCause();}
    }
    private String verifyOriginal(ContinuityStorePort.Session same,ActionReceipt receipt,ActionPorts.OutcomeArchive bound,boolean physical)throws IOException {
            writer.requireSession(same);var command=receipt.command();
            StrictJson.require(command.operation().equals(new OperationKey("save-checkpoint"))&&command.origin() instanceof CommandOrigin.Gameplay
                    &&command.expected().observerSchema().equals(CheckpointRequestFactory.OBSERVER_SCHEMA)
                    &&receipt.state() instanceof ActionState.Settled state&&state.settlement() instanceof ActionState.Applied,
                    "actual original SAVE primitive settlement required");
            var state=(ActionState.Settled)receipt.state();var attempt=state.attempt();
            StrictJson.require(state.dispatch() instanceof NativeActionPort.AckReceived,
                    "UNKNOWN, zero dispatch and ACK-only SAVE cannot qualify a pair");
            var ack=(NativeActionPort.AckReceived)state.dispatch();
            StrictJson.require(ack.nativeOk()&&ack.outbound().isPresent(),"positive original SAVE ACK and actual outbound packet required");
            ExactRef requestRef=bound.requestReferenceOf(attempt.preparedRequest()),dispatchRef=bound.referenceOf(ack);
            StrictJson.require(bound.loadRequest(requestRef).equals(attempt.preparedRequest())&&bound.load(dispatchRef).equals(ack),
                    "original durable request/ACK archive readback differs");
            var outbound=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
            StrictJson.require(outbound.requestId().equals(attempt.requestId())&&ack.requestId().equals(attempt.requestId())
                    &&outbound.step().equals("save-checkpoint")&&attempt.preparedRequest().step().equals(outbound.step())
                    &&outbound.expectedRevision().or(()->outbound.expectedSnapshotRevision()).filter(command.before().frame().identity().nativeRevision()::equals).isPresent()
                    &&StrictJson.parse(outbound.normalizedAdditionalFields().value()).equals(StrictJson.parse(attempt.preparedRequest().additionalFields().bytes())),
                    "SAVE original execute request ID/step/native revision/fields differ from its durable preparation");
            var actual=((ActionState.Applied)state.settlement()).observation();
            StrictJson.require(actual.supportingEvidence().size()==2,"SAVE requires its typed pair and complete saved Driver archived originals");
            ExactRef pairRef=actual.supportingEvidence().getFirst();byte[] pairBytes=bound.loadMaterial(pairRef).bytes();
            CheckpointPair pair=CheckpointPairCodec.decode(pairBytes);
            ExactRef savedDriverRef=actual.supportingEvidence().get(1);
            var originalSavedDriver=drivers.readArchivedSnapshot(pair,bound.loadMaterial(savedDriverRef).bytes());
            if(physical)drivers.verifyOriginal(pair,originalSavedDriver.session());
            StrictJson.require(pair.saveActionId().equals(command.actionId())&&Arrays.equals(pairBytes,CheckpointPairCodec.encode(pair)),
                    "SAVE physical material differs from its original exact pair");
            StrictJson.require(pair.nativeAckRef().bytes()==ack.originalPacket().length
                    &&pair.nativeAckRef().sha256().equals(ActionCodec.sha256(ack.originalPacket()))
                    &&(!physical||Arrays.equals(read(pair.nativeAckRef(),RawJson.MAXIMUM_BYTES+4),ack.originalPacket())),
                    "physical pair ACK differs from the canonical original native packet");
            requireContinuation(command.before(),pair.frame());requireContinuation(pair.frame(),actual.after());
            StrictJson.require(actual.sessionId().equals(command.sessionId())&&actual.source().equals(command.source())
                    &&actual.observerSchema().equals(CheckpointRequestFactory.OBSERVER_SCHEMA)
                    &&actual.actual().containsAll(List.of(new ExpectedInteger(new FieldKey("date_raw"),pair.frame().frame().identity().dateRaw()),
                        new ExpectedInteger(new FieldKey("played_character_id"),pair.frame().frame().identity().player()),
                        new ExpectedBoolean(new FieldKey("checkpoint_pair_verified"),true))),
                    "canonical SAVE independently observed effect does not prove this exact physical pair");
            var post=NativeWire.decode(bound.loadNativeFrame(actual.originalEvidence()));
            StrictJson.require(post instanceof NativeWire.Snapshot,"original post-SAVE native snapshot required");
            var snapshot=(NativeWire.Snapshot)post;var nativeState=org.xar.ck3.control.contracts.FullJsonTree.parse(snapshot.state().value(),
                    org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);var player=nativeState.get("played_character");
            StrictJson.require(player!=null&&player.isObject(),"actual post-SAVE played character must be an original object");
            StrictJson.require(snapshot.snapshotId().equals(actual.after().frame().snapshotId())
                    &&snapshot.revision().equals(actual.after().frame().identity().nativeRevision())
                    &&StrictJson.integer(nativeState.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER)==actual.after().frame().identity().dateRaw().longValueExact()
                    &&org.xar.ck3.control.contracts.NativeCharacterId.fromJson(player.get("character_id")).asBigInteger().equals(actual.after().frame().identity().player())
                    &&nativeState.path("map_ready").isBoolean()&&nativeState.path("map_ready").booleanValue()
                    &&nativeState.path("paused").isBoolean()&&nativeState.path("paused").booleanValue()
                    &&player.path("alive").isBoolean()&&player.path("alive").booleanValue(),"actual post-SAVE native identity/paused map differs");
            var material=StrictJson.object();material.put("schema","xar.canonical-save-receipt-binding/v1");
            material.set("request",requestRef.toJson());material.set("dispatch",dispatchRef.toJson());
            material.set("pair_proof",pairRef.toJson());material.set("post_native",actual.originalEvidence().toJson());material.put("action_body_sha256",receipt.bodySha256());
            material.set("saved_driver",savedDriverRef.toJson());
            material.set("pair",StrictJson.parse(CheckpointPairCodec.encode(pair)));
            writer.requireSession(same);return ContinuityJson.digest(material);
    }
    private byte[] read(ExactRef ref,int maximum)throws IOException {
        var witness=files.observe(Path.of(ref.path())).orElseThrow(()->new IOException("original SAVE source unavailable"));
        StrictJson.require(witness.reference().equals(ref),"original SAVE source changed");return files.read(witness,maximum);
    }
    private static void requireContinuation(ObservationIdentity before,ObservationIdentity after) {
        StrictJson.require(before.machineId().equals(after.machineId())&&before.game().equals(after.game())
                &&before.frame().episodeRunId().equals(after.frame().episodeRunId())
                &&before.frame().identity().player().equals(after.frame().identity().player())
                &&before.frame().identity().dateRaw().equals(after.frame().identity().dateRaw())
                &&after.frame().revision().compareTo(before.frame().revision())>=0
                &&after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision())>=0,
                "actual SAVE crossed Game/episode/actor/date or moved an observed revision backwards");
    }
}
