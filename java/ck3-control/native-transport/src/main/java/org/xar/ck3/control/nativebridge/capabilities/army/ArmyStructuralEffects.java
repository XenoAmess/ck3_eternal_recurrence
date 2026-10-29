package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Independent whole-frame observer and original cold replay. No submit method or cached-SEM Applied exception. */
public final class ArmyStructuralEffects implements NativeEffectRegistry.Observer {
    public static final String SCHEMA="xar.java.army-structural-applied/v1";
    private final Supplier<HeldDriverObservationPort> held;
    private final ActionPorts.OutcomeArchive archive;
    private final NativeEffectEvidence.FrameLoader frames;
    private final Clock clock;
    private final Duration mergeWait;
    public ArmyStructuralEffects(Supplier<HeldDriverObservationPort> held,ActionPorts.OutcomeArchive archive,
            NativeEffectEvidence.FrameLoader frames,Clock clock,Duration commandTimeout) {
        this.held=Objects.requireNonNull(held);this.archive=Objects.requireNonNull(archive);this.frames=Objects.requireNonNull(frames);
        this.clock=Objects.requireNonNull(clock);Objects.requireNonNull(commandTimeout);
        StrictJson.require(!commandTimeout.isNegative()&&!commandTimeout.isZero()&&commandTimeout.compareTo(Duration.ofHours(1))<=0,"finite actual Army timeout required");
        mergeWait=commandTimeout.compareTo(Duration.ofSeconds(3))<0?commandTimeout:Duration.ofSeconds(3);
    }
    public static List<ExpectedValue> values(ArmyStructuralActions.Call call) {
        var values=new ArrayList<ExpectedValue>();
        values.add(new ExpectedText(new FieldKey("kind"),call.kind().name()));
        values.add(new ExpectedInteger(new FieldKey("source_army_id"),java.math.BigInteger.valueOf(call.source().value())));
        if(call instanceof ArmyStructuralActions.Merge merge)
            values.add(new ExpectedInteger(new FieldKey("destination_army_id"),java.math.BigInteger.valueOf(merge.destination().value())));
        return List.copyOf(values);
    }
    public static ExpectedPostcondition expected(ObservationIdentity before,G2Source source,ArmyStructuralActions.Call call) {
        return new ExpectedPostcondition(1,before,source,SCHEMA,values(call));
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        ArmyStructuralActions.Call call=ArmyStructuralActionCodec.decode(new RawJson(DriverJson.encode(command.arguments())));
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.originalResultToken().isEmpty())
            return NativeEffectRegistry.Projected.pending("original structural outcome is unknown/rejected; no replay",List.of(attempt.guard().nativeEvidence()));
        ArmyStructuralActionCodec.outbound(command,attempt,ack,archive);
        Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,frames);
        requireBefore(command,before);ArmyStructuralActions.preflight(call,before.semantic());
        if(call instanceof ArmyStructuralActions.Halt)
            return NativeEffectRegistry.Projected.pending("original halt reports submitted only; no route effect is inferred from ACK",List.of(before.originalEvidence()));
        Complete after=observeAfter(command,attempt,call,before);
        requireScope(before,after);
        RawJson material=ArmyStructuralActions.format(call,before.semantic(),after.semantic(),ack.originalResultToken().orElseThrow());
        boolean accepted=new Bool(true).equals(DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES).get("accepted"));
        if(!accepted||!ArmyStructuralActions.applied(call,before.semantic(),after.semantic()))
            return pending(command,attempt,before,after,material);
        var pair=new NativeEffectSnapshots.Pair(before,after);
        StrictJson.require(!after.observedAt().isBefore(attempt.submittedAt()),"structural applied publication predates submission");
        var projected=NativeEffectSnapshots.observed(command,attempt,after,SCHEMA,values(call),NativeEffectSnapshots.publication(after),material,List.of());
        ExactRef basis=NativeEffectEvidence.preserve(command,attempt,pair,List.of(),material,archive);
        return NativeEffectSnapshots.withEvidence(projected,List.of(basis));
    }
    private Complete observeAfter(ActionCommand command,ActionState.Attempt attempt,ArmyStructuralActions.Call call,Complete before) {
        try {
            if(ActionReconciliationScope.activeFor(command))return ActionReconciliationScope.requireFrame(command,attempt);
            Instant deadline=ActionObservationWindow.deadline(command);
            Instant local=clock.instant().plus(mergeWait);if(local.isBefore(deadline))deadline=local;
            long started=System.nanoTime();long allowed=mergeWait.toNanos();
            Complete after=held.get().observe(deadline);requireScope(before,after);
            if(call instanceof ArmyStructuralActions.Merge) {
                // This local loop only waits for independent frames; it has no submit/replay edge.
                while(!ArmyStructuralActions.applied(call,before.semantic(),after.semantic())
                        &&clock.instant().isBefore(deadline)&&System.nanoTime()-started<allowed) {
                    Thread.sleep(10);
                    if(!clock.instant().isBefore(deadline)||System.nanoTime()-started>=allowed)break;
                    after=held.get().observe(deadline);requireScope(before,after);
                }
            }
            return after;
        }catch(IOException unavailable){throw new UncheckedIOException("actual structural after observation unavailable; never replay",unavailable);}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("structural observation interrupted; never replay",interrupted);}
    }
    private NativeEffectRegistry.Projected pending(ActionCommand command,ActionState.Attempt attempt,Complete before,Complete after,RawJson material) {
        var original=NativeEffectEvidence.basis(before);var observed=NativeEffectEvidence.basis(after);
        ExactRef materialRef=archive.preserveMaterial(material);
        var basis=new ArmyStructuralActionCodec.PendingBasis(ActionCodec.bodySha256(command),attempt.requestId(),
                original.nativeFrame(),original.driverFacts(),observed.nativeFrame(),observed.driverFacts(),materialRef);
        RawJson encoded=ArmyStructuralActionCodec.encode(basis);ExactRef reference=archive.preserveMaterial(encoded);
        StrictJson.require(encoded.equals(archive.loadMaterial(reference))&&material.equals(archive.loadMaterial(materialRef)),"structural pending originals changed");
        var refs=new java.util.LinkedHashSet<ExactRef>();
        refs.add(reference);refs.add(materialRef);refs.add(original.nativeFrame());refs.add(original.driverFacts());refs.add(observed.nativeFrame());refs.add(observed.driverFacts());
        return NativeEffectRegistry.Projected.pending("structural command submitted; independent exact postcondition remains unverified",List.copyOf(refs));
    }
    public static void requireBefore(ActionCommand command,Complete before) {
        StrictJson.require(before.identity().equals(command.before())&&before.source().equals(command.source())
                &&before.sessionId().equals(command.sessionId()),"structural original frame crossed the command");
    }
    public static void requireScope(Complete before,Complete after) {
        StrictJson.require(before.identity().machineId().equals(after.identity().machineId())&&before.identity().game().equals(after.identity().game())
                &&before.source().equals(after.source())&&before.sessionId().equals(after.sessionId())
                &&before.connectionGeneration().equals(after.connectionGeneration())
                &&before.identity().frame().episodeRunId().equals(after.identity().frame().episodeRunId())
                &&before.identity().frame().identity().player().equals(after.identity().frame().identity().player()),
                "structural observation crossed actual Game/source/player/episode/connection");
    }
    /** Rebuilds only original pending DATA, then reruns the full pure formatter; it does not grant Applied. */
    public static Optional<RawJson> pendingMaterial(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames) {
        if(!(receipt.state() instanceof ActionState.Unknown unknown))return Optional.empty();
        // Normal halt is deliberately submitted-only and has no after-frame material basis.
        // Its native guard packet must never be probed as a JSON material descriptor.
        if(ArmyStructuralActionCodec.decode(new RawJson(DriverJson.encode(receipt.command().arguments()))) instanceof ArmyStructuralActions.Halt)return Optional.empty();
        var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();
        var dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow();
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.originalResultToken().isEmpty())return Optional.empty();
        ArmyStructuralActionCodec.outbound(receipt.command(),attempt,ack,archive);
        for(ExactRef ref:unknown.evidence()) {
            if(ref.equals(attempt.guard().nativeEvidence())||ref.bytes()>65536)continue;
            RawJson body;
            try{body=archive.loadMaterial(ref);}catch(IllegalArgumentException unavailable){continue;}
            Obj row=DriverJson.object(body.bytes(),65536);
            if(!new Text(ArmyStructuralActionCodec.PENDING_SCHEMA).equals(row.get("schema")))continue;
            requireExactOriginal(ref,body.bytes());var basis=ArmyStructuralActionCodec.decodeBasis(body);
            StrictJson.require(basis.commandBodySha256().equals(receipt.bodySha256())&&basis.requestId().equals(attempt.requestId()),"pending structural body/request drift");
            Complete before=frames.load(new NativeEffectEvidence.FrameBasis(basis.beforeNative(),basis.beforeDriver()),archive);
            Complete after=frames.load(new NativeEffectEvidence.FrameBasis(basis.afterNative(),basis.afterDriver()),archive);
            Complete guarded=RootGuardEvidence.loadFrame(attempt.guard(),archive,frames);
            StrictJson.require(NativeEffectEvidence.basis(before).equals(NativeEffectEvidence.basis(guarded))
                    &&unknown.evidence().containsAll(List.of(basis.beforeNative(),basis.beforeDriver(),basis.afterNative(),basis.afterDriver(),basis.material())),
                    "cold pending structural originals differ from the actual guard or retained receipt custody");
            requireBefore(receipt.command(),before);requireScope(before,after);
            RawJson original=archive.loadMaterial(basis.material());requireExactOriginal(basis.material(),original.bytes());
            RawJson replayed=ArmyStructuralActions.format(ArmyStructuralActionCodec.decode(new RawJson(DriverJson.encode(receipt.command().arguments()))),
                    before.semantic(),after.semantic(),ack.originalResultToken().orElseThrow());
            StrictJson.require(original.equals(replayed),"cold structural submitted result differs from original raw frames");
            return Optional.of(original);
        }
        return Optional.empty();
    }
    // Preserve the existing package-private guard predicate without exposing its authority helpers.
    private static void requireExactOriginal(ExactRef reference,byte[] bytes) {
        StrictJson.require(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),
                "archived original bytes/SHA changed");
    }
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation,ExactRef definition) {
        return new NativeRecordedEvidenceVerifier.Binding(operation,definition,(head,receipt,actualArchive)->{
            StrictJson.require(receipt.command().operation().equals(operation),"structural archived operation drift");
            if(receipt.state() instanceof ActionState.Unknown){pendingMaterial(receipt,actualArchive,frames);return;}
            if(!(receipt.state() instanceof ActionState.Settled settled)||!(settled.settlement() instanceof ActionState.Applied))return;
            var original=NativeEffectEvidence.load(receipt,actualArchive,frames);var call=ArmyStructuralActionCodec.decode(new RawJson(DriverJson.encode(receipt.command().arguments())));
            var ack=(NativeActionPort.AckReceived)settled.dispatch();ArmyStructuralActionCodec.outbound(receipt.command(),settled.attempt(),ack,actualArchive);
            StrictJson.require(!(call instanceof ArmyStructuralActions.Halt)&&ArmyStructuralActions.applied(call,original.frames().before().semantic(),original.frames().after().semantic()),"archived structural effect does not recompute");
            RawJson material=ArmyStructuralActions.format(call,original.frames().before().semantic(),original.frames().after().semantic(),ack.originalResultToken().orElseThrow());
            var projected=NativeEffectSnapshots.observed(receipt.command(),settled.attempt(),original.frames().after(),SCHEMA,values(call),
                    NativeEffectSnapshots.publication(original.frames().after()),material,List.of());
            projected=NativeEffectSnapshots.withEvidence(projected,((ActionState.Applied)settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(),projected,original.compatibleResult());
        });
    }
}

