package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.OriginalOutcome;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome;

/** Same canonical coordinator/writer, separate physical bytes and private once permits. */
final class PhysicalCoordinatorSupport {
    private PhysicalCoordinatorSupport() { }
    static ActionReceipt execute(ActionJournal.LockedJournal locked, ActionCommand command, PhysicalActionRegistry registry,
            String authorityId, Clock clock, ActionPorts.IntentPreparationPort intents, ActionPorts.IntentBarrierPort barrier) {
        var binding = registry.require(command); String body = ActionCodec.bodySha256(command);
        try {
            var initial = binding.producer().guard(locked.head(), command); ActionCoordinator.verifyGuard(command, initial, authorityId, clock.instant());
            barrier.check(locked.writerSession(), command);
            var prepared = binding.producer().prepare(locked.writerSession(), command, RequestIds.forCommand(command));
            StrictJson.require(prepared.transportKind() == binding.transportKind() && prepared.requestId().equals(RequestIds.forCommand(command))
                    && !prepared.preparationEvidence().isEmpty(), "actual physical producer changed plane/request ID/original preparation");
            requireOwner(command, prepared, initial, binding); intents.prepare(locked.writerSession(), command); barrier.check(locked.writerSession(), command);
            ActionCoordinator.append(locked, command, body, new ActionState.IntentDurable());
            var fresh = binding.producer().guard(locked.head(), command); ActionCoordinator.verifyGuard(command, fresh, authorityId, clock.instant());
            barrier.check(locked.writerSession(), command);
            var submitting = new PhysicalActionState(prepared, clock.instant(), fresh, PhysicalActionState.Phase.SUBMITTING, Optional.empty(), List.of(), "actual physical SUBMITTING");
            ActionCoordinator.append(locked, command, body, submitting);
            PresentationPermit.Check check = () -> {
                StrictJson.require(ActionScope.currentActionId().filter(command.actionId()::equals).isPresent(), "physical permit escaped its actual action scope");
                var actual = locked.find(command.actionId()).orElseThrow();
                StrictJson.require(actual.bodySha256().equals(body) && actual.state() instanceof PhysicalActionState physical
                        && physical.phase() == PhysicalActionState.Phase.SUBMITTING && PhysicalActionCodec.sameAttempt(submitting, physical), "physical permit lost its original durable SUBMITTING");
                ActionCoordinator.verifyGuard(command, binding.producer().guard(locked.head(), command), authorityId, clock.instant());
                barrier.check(locked.writerSession(), command);
            };
            PhysicalSubmission permit = prepared instanceof PreparedAction.MmapRequest mmap ? new PresentationPermit(mmap.value(), command.deadline(), check)
                    : new FrontendWindowCapturePermit(((PreparedAction.WindowCaptureRequest) prepared).value(), command.deadline(), check);
            PhysicalOutcome outcome;
            try { outcome = binding.producer().post(permit, prepared, command.deadline()); }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); return unknown(locked, command, body, submitting, Optional.empty(), "physical post interrupted; no replay"); }
            catch (IOException | RuntimeException failure) { return unknown(locked, command, body, submitting, Optional.empty(), "physical result unavailable:" + failure.getClass().getName() + "; no replay"); }
            StrictJson.require(outcome.requestId().equals(prepared.requestId()) && outcome.transportKind() == prepared.transportKind(), "physical result changed its original request/plane");
            boolean notPosted = outcome instanceof PhysicalOutcome.MmapOutcome mmap && mmap.value() instanceof OriginalOutcome.NotPosted
                    || outcome instanceof PhysicalOutcome.WindowCaptureOutcome window && window.value().status() == FrontendWindowCaptureOutcome.Status.OBSERVED_REJECTED;
            var returned = new PhysicalActionState(prepared, submitting.submittedAt(), fresh, notPosted ? PhysicalActionState.Phase.NOT_POSTED : PhysicalActionState.Phase.UNKNOWN,
                    Optional.of(outcome), List.of(), notPosted ? "actual source proved no physical post" : "physical return retained; independent completion required");
            var receipt = ActionCoordinator.append(locked, command, body, returned);
            return notPosted ? receipt : observe(locked, receipt, registry, clock);
        } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }

    static ActionReceipt defer(ActionJournal.LockedJournal locked,ActionCommand command,PhysicalActionRegistry registry,
            String authorityId,Clock clock,ActionPorts.IntentPreparationPort intents,ActionPorts.IntentBarrierPort barrier) {
        return ActionScope.run(command.actionId(),()->ActionCommandScope.within(command,()->ActionReadPublicationScope.within(locked,command,barrier,()->deferOwned(locked,command,registry,authorityId,clock,intents,barrier))));
    }
    private static ActionReceipt deferOwned(ActionJournal.LockedJournal locked,ActionCommand command,PhysicalActionRegistry registry,
            String authorityId,Clock clock,ActionPorts.IntentPreparationPort intents,ActionPorts.IntentBarrierPort barrier) {
        var binding=registry.require(command);var producer=binding.producer();
        StrictJson.require(binding.transportKind()==org.xar.ck3.control.contracts.presentation.TransportKind.PRESENTATION_MMAP
                &&producer.automatic(command),"only actual source-owned automatic presentation may defer");
        String digest=ActionCodec.bodySha256(command);var previous=locked.find(command.actionId());
        if(previous.isPresent()){StrictJson.require(previous.orElseThrow().bodySha256().equals(digest),"automatic action body conflict");return previous.orElseThrow();}
        try {
            var snapshot=locked.snapshot();
            ProtocolIdentityAdmission.requireUnique(snapshot.actions(),command);
            for(var receipt:snapshot.actions())if(receipt.command().operation().equals(command.operation())
                    &&receipt.command().origin().machineId().equals(command.origin().machineId())
                    &&receipt.command().origin().game().equals(command.origin().game())
                    &&producer.automatic(receipt.command())){
                producer.verifyOptional(locked.writerSession(),receipt);
                var state=receipt.state();
                if(state instanceof ActionState.IntentDurable){
                    if(!producer.liveCustody(locked.writerSession(),receipt.command()))
                        throw new IllegalArgumentException("orphaned automatic intent blocks a new camera action");
                } else if(state instanceof ActionState.Unknown unknown){
                    if(unknown.attempt().isPresent()||unknown.dispatch().isPresent())
                        throw new IllegalArgumentException("automatic physical UNKNOWN blocks a new camera action");
                } else if(state instanceof PhysicalActionState physical){
                    if(!physical.terminal()){
                        var outcome=physical.outcome().orElseThrow(() -> new IllegalArgumentException("automatic physical UNKNOWN blocks a new camera action"));
                        if(outcome instanceof PhysicalOutcome.MmapOutcome mmap){
                            var value=mmap.value();
                            if(!(value instanceof OriginalOutcome.Posted||value instanceof OriginalOutcome.NotPosted))
                                throw new IllegalArgumentException("automatic physical UNKNOWN blocks a new camera action");
                        } else throw new IllegalArgumentException("automatic physical UNKNOWN blocks a new camera action");
                    }
                } else throw new IllegalArgumentException("automatic physical UNKNOWN blocks a new camera action");
            }
            StrictJson.require(snapshot.headSha256().equals(locked.head().digest())&&snapshot.ledgerSequence()==locked.head().state().sequence(),"canonical head changed during lane validation");
            var actual=producer.guard(locked.head(),command);ActionCoordinator.verifyGuard(command,actual,authorityId,clock.instant());
            barrier.check(locked.writerSession(),command);intents.prepare(locked.writerSession(),command);barrier.check(locked.writerSession(),command);
            var intent=ActionCoordinator.append(locked,command,digest,new ActionState.IntentDurable());
            var permit=new PresentationPermit(producer.automaticIntent(command),()->producer.verifyDeferredOwner(command));
            // The source computes its exact body-derived request ID from this same durable command.
            producer.queued(locked.writerSession(),command,actual,permit);return intent;
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    static void collect(ActionJournal.LockedJournal locked,PhysicalActionRegistry registry) {
        try {
            for(var binding:registry.installed())for(var result:binding.producer().collect(locked.writerSession())){
                var original=locked.find(result.command().actionId()).orElseThrow();
                StrictJson.require(registry.require(result.command())==binding&&binding.producer().automatic(result.command())
                        &&original.bodySha256().equals(ActionCodec.bodySha256(result.command())),"deferred capture crossed its original source/body");
                if(original.state() instanceof ActionState.IntentDurable)
                    ActionCoordinator.append(locked,result.command(),original.bodySha256(),result.state());
                else StrictJson.require(!(original.state() instanceof ActionState.Submitting),"automatic capture crossed native pipe SUBMITTING");
                binding.producer().committed(result.command().actionId());
            }
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private static ActionReceipt unknown(ActionJournal.LockedJournal locked, ActionCommand command, String body, PhysicalActionState attempt,
            Optional<PhysicalOutcome> outcome, String reason) {
        return ActionCoordinator.append(locked, command, body, new PhysicalActionState(attempt.request(), attempt.submittedAt(), attempt.guard(),
                PhysicalActionState.Phase.UNKNOWN, outcome, List.of(), reason));
    }
    static ActionReceipt observe(ActionJournal.LockedJournal locked, ActionReceipt receipt, PhysicalActionRegistry registry, Clock clock) {
        var original = (PhysicalActionState) receipt.state(); if (original.terminal()) return receipt;
        try {
            var result = registry.require(receipt.command()).producer().observe(locked.writerSession(), receipt.command(), original, ActionObservationWindow.deadline(receipt.command()));
            var after = result instanceof PhysicalActionRegistry.Completed complete
                    ? new PhysicalActionState(original.request(), original.submittedAt(), original.guard(), PhysicalActionState.Phase.COMPLETED, original.outcome(), complete.evidence(), "independent actual physical completion; no Game/day credit")
                    : new PhysicalActionState(original.request(), original.submittedAt(), original.guard(), PhysicalActionState.Phase.UNKNOWN, original.outcome(), ((PhysicalActionRegistry.Pending) result).evidence(), ((PhysicalActionRegistry.Pending) result).reason());
            return ActionCoordinator.append(locked, receipt.command(), receipt.bodySha256(), after);
        } catch (IOException | RuntimeException failure) { return unknown(locked, receipt.command(), receipt.bodySha256(), original, original.outcome(), "physical observation unavailable:" + failure.getClass().getName() + "; original retained"); }
    }
    private static void requireOwner(ActionCommand command, PreparedAction prepared, GuardEvidence actualGuard, PhysicalActionRegistry.Binding actualBinding) {
        String machine, session, birth, generation; long pid;
        if (prepared instanceof PreparedAction.MmapRequest mmap) {
            var request = mmap.value(); var owner = request.owner(); var before = command.before(); var frame = request.frame();
            machine = owner.machineId(); session = owner.sessionId(); birth = owner.processBirthFiletime(); pid = owner.processId(); generation = owner.connectionGeneration();
            StrictJson.require(owner.episodeRunId().equals(before.frame().episodeRunId())
                    && frame.snapshotId().equals(before.frame().snapshotId()) && frame.revision().equals(before.frame().revision().toString())
                    && frame.nativeRevision().equals(before.frame().identity().nativeRevision().toString())
                    && java.math.BigInteger.valueOf(frame.actor()).equals(before.frame().identity().player())
                    && java.math.BigInteger.valueOf(frame.dateRaw()).equals(before.frame().identity().dateRaw()),
                    "physical mmap preparation changed its actual complete current frame or episode");
        } else {
            var request = ((PreparedAction.WindowCaptureRequest) prepared).value(); var owner = request.owner(); var frontend = command.origin().requireFrontend();
            machine = owner.machineId(); session = owner.sessionId(); birth = owner.processBirthFiletime(); pid = owner.processId(); generation = owner.connectionGeneration();
            StrictJson.require(request.deadline().equals(command.deadline()) && request.actualFrontendEvidence().equals(frontend.nativeEvidence())
                    && actualBinding.sources().contains(request.sourceRef()), "physical window preparation changed its original frontend/deadline/installed implementation");
        }
        StrictJson.require(machine.equals(command.origin().machineId()) && session.equals(command.sessionId()) && pid == command.origin().game().pid()
                && birth.equals(command.origin().game().creationFiletime().value().toString())
                && generation.equals(actualGuard.connectionGeneration().toString()), "physical prepared request changed actual Game birth/session/machine/connection");
    }
}
