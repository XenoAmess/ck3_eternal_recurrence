package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/**
 * Original DATA predicates for a distinct post-resume-paused cleanup protocol.
 * No method issues a token, grants a Native permit, submits CANCEL or completes a parent.
 * Actual generation-conditional backend qualification and canonical issuance remain separate requirements.
 */
public final class LifePostResumePauseCleanupProof {
    private LifePostResumePauseCleanupProof() { }

    public record Original(ActionReceipt parent, List<ActionReceipt> children, ActionReceipt arm,
            ActionReceipt resume, ActionReceipt pause, AdvancePlan plan, Status originalArm) {
        public Original {
            Objects.requireNonNull(parent); children=List.copyOf(children); Objects.requireNonNull(arm);
            Objects.requireNonNull(resume); Objects.requireNonNull(pause); Objects.requireNonNull(plan); Objects.requireNonNull(originalArm);
        }
    }

    /** Complete original three-to-five child prefix only; an appended CANCEL is not silently part of this role. */
    public static Original original(ActionReceipt parent,List<ActionReceipt> children) {
        children=List.copyOf(children);
        var actions=new ArrayList<ActionReceipt>(children);actions.add(parent);
        require(ContinuityBatchJournal.readOnlyPostResumePauseLifeRecoveryRoot(actions).filter(parent::equals).isPresent(),
                "cleanup original is not the complete strict canonical post-resume-paused Life prefix");
        var execution=((ActionState.CompositeUnknown)parent.state()).execution();
        require(children.size()==execution.children().size(),"cleanup cannot omit an original child binding");
        for(int index=0;index<children.size();index++) {
            var bound=execution.children().get(index);var child=children.get(index);
            require(bound.actionId().equals(child.command().actionId())&&bound.bodySha256().equals(child.bodySha256()),
                    "cleanup original child order or body differs");
        }
        var plan=AdvancePlan.decode(parent.command());
        require(plan.dailyWatch().isEmpty(),"this cleanup role does not widen watched Life protocols");
        var arms=children.stream().filter(child->child.command().operation().value().equals(plan.armStep())).toList();
        require(arms.size()==1,"cleanup needs the one original canonical ARM");
        var arm=arms.getFirst();var state=(ActionState.Settled)arm.state();
        require(state.settlement() instanceof ActionState.ControlApplied,"cleanup ARM lacks its actual independent Status settlement");
        var control=(ActionState.ControlApplied)state.settlement();
        var armed=AdvancePrimitives.acknowledgedSentinel(arm.ack().orElseThrow(),plan.armStep());
        AdvanceClock.validateArm(armed,plan);
        require(control.observerSchema().equals(AdvancePrimitives.CLOCK_OBSERVER)
                &&ClockStatusRead.decode(control.read().original()).equals(armed)
                &&control.actual().equals(AdvancePrimitives.statusValues(armed)),
                "cleanup ARM original ACK and independent Status differ");
        return new Original(parent,children,arm,children.get(children.size()-2),children.getLast(),plan,armed);
    }

    /** Actual physical query then a later full paused frame; the caller's real clock must supply the bounded new window. */
    public static void requireFreshArmedPaused(Original original,ClockStatusRead.Observation status,
            AdvanceObservationPort.Frame current,Instant issuedAt,Instant newDeadline,Instant now) {
        original=checked(original);Objects.requireNonNull(status);Objects.requireNonNull(current);
        Objects.requireNonNull(issuedAt);Objects.requireNonNull(newDeadline);Objects.requireNonNull(now);
        require(!now.isBefore(issuedAt)&&now.isBefore(newDeadline)&&newDeadline.isAfter(issuedAt)
                &&!newDeadline.isAfter(issuedAt.plus(Duration.ofMinutes(10))),"cleanup needs its own new finite observation/operation window");
        status.requirePhysicalParent(original.parent().command());
        var receipt=status.receipt();
        require(status.status().equals(ClockStatusRead.decode(receipt.original())),"cleanup physical Status decode differs");
        var custody=LifeSentinelCancellationProof.physical(original.parent().command(),receipt);
        require(!custody.writeEntered().observedAt().isBefore(issuedAt)
                &&!custody.responseReceived().observedAt().isAfter(newDeadline)
                &&!receipt.request().deadline().isAfter(newDeadline)
                &&!receipt.request().deadline().isAfter(issuedAt.plus(Duration.ofMinutes(2))),
                "cleanup Status must use its own at-most-two-minute query window within the new operation window");
        requirePausedFrame(original,current);
        require(!current.observedAt().isAfter(now)&&!custody.responseReceived().observedAt().isAfter(now)
                &&!now.isAfter(custody.responseReceived().observedAt().plus(Duration.ofMinutes(2)))
                &&!now.isAfter(current.observedAt().plus(Duration.ofMinutes(2)))
                &&receipt.request().deadline().isAfter(custody.writeEntered().observedAt())
                &&!custody.responseReceived().observedAt().isAfter(receipt.request().deadline())
                &&!current.observedAt().isBefore(custody.responseReceived().observedAt())
                &&!current.observedAt().isAfter(receipt.request().deadline())
                &&current.identity().frame().identity().nativeRevision().compareTo(
                    status.physicalIdentity().orElseThrow().nativeRevision())>=0,
                "cleanup paused frame predates its actual physical Status or exceeds its new window");
        var actual=status.status();var date=current.identity().frame().identity().dateRaw();
        var delta=date.subtract(original.plan().startingDateRaw());
        require(delta.signum()>0&&delta.mod(AdvancePlan.DAY).signum()==0
                &&date.compareTo(original.plan().targetDateRaw())<0,"cleanup retains only the actual positive partial date");
        AdvanceClock.requireSameSlot(original.originalArm(),actual);
        require(actual.state()==State.ARMED&&!actual.abnormal()&&!actual.terminalObserved()
                &&actual.completedDailyTicks()==delta.divide(AdvancePlan.DAY).longValueExact()
                &&actual.lastObservedDateRaw()==date.longValueExact()&&actual.triggerDateRaw()==0
                &&actual.intermediatePauseCount()==0&&actual.triggerFlags()==0&&actual.triggerReasons().isEmpty()
                &&actual.signedDateDeltaFromTargetRaw()==0&&actual.overshootDays()==-1
                &&!actual.pauseWrapperCalled()&&!actual.pauseObserved(),
                "cleanup Status does not prove the exact original armed partial slot");
    }

    public static void requirePausedFrame(Original original,AdvanceObservationPort.Frame current) {
        original=checked(original);
        var parent=original.parent().command();var paused=ActionEffects.observation(original.pause()).orElseThrow();
        require(current.source().equals(parent.source())&&current.sessionId().equals(parent.sessionId())
                &&current.identity().machineId().equals(paused.after().machineId())&&current.identity().game().equals(paused.after().game())
                &&current.identity().frame().episodeRunId().equals(paused.after().frame().episodeRunId())
                &&current.identity().frame().identity().player().equals(paused.after().frame().identity().player())
                &&current.identity().frame().identity().dateRaw().equals(paused.after().frame().identity().dateRaw())
                &&current.identity().frame().identity().nativeRevision().compareTo(paused.after().frame().identity().nativeRevision())>=0
                &&AdvancePolicy.truth(current.semantic(),"paused")&&AdvancePolicy.truth(current.semantic(),"map_ready"),
                "cleanup current frame differs from its original independently confirmed paused owner/date");
    }


    private static Original checked(Original supplied) {
        Objects.requireNonNull(supplied);
        var actual=original(supplied.parent(),supplied.children());
        require(actual.equals(supplied),"cleanup original DATA fields were substituted");
        return actual;
    }

    /** Constructs only deterministic command DATA. It neither reserves nor submits this action. */
    public static ActionCommand cancellationCommand(Original original,AdvanceObservationPort.Frame beforeCancel,Instant ownDeadline) {
        original=checked(original); Objects.requireNonNull(ownDeadline); requirePausedFrame(original,beforeCancel);
        var parent=original.parent().command();
        var operation=new OperationKey(ClockStatusRead.CANCEL_PREFIX+original.originalArm().generation().decimal());
        var arguments=new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of());
        return new ActionCommand(ActionIds.child(parent.actionId(),original.children().size()+1,operation),
                beforeCancel.identity(),parent.source(),parent.sessionId(),operation,arguments,
                AdvancePrimitives.expected(beforeCancel.identity(),parent.source(),operation,arguments),parent.claims(),ownDeadline);
    }

    /** Original prefix plus at most its one deterministic reservation/receipt. UNKNOWN is DATA, never terminal or submit authority. */
    public static void requireSuccessorPrefix(Original original,CompositeExecution successor,List<ActionReceipt> canonicalChildren,
            AdvanceObservationPort.Frame beforeCancel,Instant ownDeadline,boolean includesActualCancel) {
        original=checked(original); Objects.requireNonNull(successor);canonicalChildren=List.copyOf(canonicalChildren);
        var execution=((ActionState.CompositeUnknown)original.parent().state()).execution();int count=original.children().size();
        require(successor.handlerId().equals(execution.handlerId())&&successor.startedAt().equals(execution.startedAt())
                &&successor.guard().equals(execution.guard())&&successor.children().size()>=count&&successor.children().size()<=count+1
                &&successor.children().subList(0,count).equals(execution.children())
                &&canonicalChildren.size()==count+(includesActualCancel?1:0)
                &&canonicalChildren.subList(0,count).equals(original.children()),
                "cleanup successor changed its original execution, immutable receipts or exact prefix");
        var command=cancellationCommand(original,beforeCancel,ownDeadline);
        if(successor.children().size()==count+1) {
            var reserved=successor.children().getLast();
            require(reserved.actionId().equals(command.actionId())&&reserved.bodySha256().equals(ActionCodec.bodySha256(command)),
                    "cleanup successor reservation is not its one deterministic generation-bound CANCEL");
        }
        if(includesActualCancel) {
            require(successor.children().size()==count+1,"cleanup receipt has no exact canonical reservation");
            var cancel=canonicalChildren.getLast();
            require(ActionTransitions.composite(cancel.state()).isEmpty()
                    &&cancel.command().equals(command)&&cancel.bodySha256().equals(ActionCodec.bodySha256(command))
                    &&cancel.sequence()>original.parent().sequence(),"cleanup receipt replaced its exact reserved command or predates the original UNKNOWN");
            // No settlement is inferred here. A bare Intent, ACK or UNKNOWN remains collection-only.
            ActionTransitions.attempt(cancel.state()).ifPresent(attempt->{
                require(attempt.guard().observed().equals(command.before())&&attempt.guard().source().equals(command.source())
                        &&attempt.guard().sessionId().equals(command.sessionId())&&attempt.guard().operation().equals(command.operation())
                        &&command.origin().acceptsGuard(attempt.guard().origin())
                        &&attempt.preparedRequest().equals(AdvancePrimitives.prepareRequest(command)),
                        "cleanup retained attempt changed the exact original command guard or producer");
            });
        }
    }

    private static NativeRequestChronology reopenPhysical(ActionCommand parent,ClockStatusRead.Observation status,
            ActionPorts.OutcomeArchive archive) {
        status.requirePhysicalParent(parent);
        require(status.status().equals(ClockStatusRead.decode(status.receipt().original()))
                &&archive.load(status.originalEvidence()).equals(status.receipt().original()),
                "cleanup physical Status value or original acknowledgement differs");
        org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(status.receipt(),archive);
        return LifeSentinelCancellationProof.physical(parent,status.receipt());
    }
    private static void reopenFrame(AdvanceObservationPort.Frame frame,ActionPorts.OutcomeArchive archive,
            org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames) {
        var facts=org.xar.ck3.control.contracts.ExactRef.fromJson(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(
                frame.semantic().get("java_driver_facts_evidence")));
        var actual=frames.load(new org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameBasis(frame.originalEvidence(),facts),archive);
        require(actual.identity().equals(frame.identity())&&actual.source().equals(frame.source())
                &&actual.sessionId().equals(frame.sessionId())&&actual.semantic().equals(frame.semantic())
                &&actual.originalEvidence().equals(frame.originalEvidence())&&actual.observedAt().equals(frame.observedAt()),
                "cleanup complete paused frame differs from its actual native/Driver originals");
        if(frame.provenance() instanceof ObservationProvenance.FreshSnapshotQuery query)
            frames.verifyFreshSnapshotQuery(query,actual,archive);
        else if(frame.provenance() instanceof ObservationProvenance.PhysicalAfterAcknowledgement physical)
            frames.verifyPhysicalAfterAcknowledgement(physical,actual,archive);
        else require(frame.provenance().equals(new ObservationProvenance.Push(actual.identity().frame().snapshotId(),
                actual.identity().frame().identity().nativeRevision(),actual.originalEvidence())),
                "cleanup frame lacks its original received Push or independently verified READ basis");
    }

    /** Full archived DATA replay only. Installed authorization/backend qualification and canonical writer membership are not issued here. */
    public static void verify(Original original,CompositeExecution successor,List<ActionReceipt> canonicalChildren,
            org.xar.ck3.control.contracts.ExactRef originalParentReference,
            List<org.xar.ck3.control.contracts.ExactRef> originalChildReferences,
            ClockStatusRead.Observation armedStatus,AdvanceObservationPort.Frame beforeCancel,
            ClockStatusRead.Observation terminalStatus,AdvanceObservationPort.Frame ending,
            Instant issuedAt,Instant ownDeadline,org.xar.ck3.control.contracts.ExactRef authorizationReference,
            ActionPorts.OutcomeArchive archive,org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames) {
        original=checked(original); Objects.requireNonNull(archive);Objects.requireNonNull(frames);
        originalChildReferences=List.copyOf(originalChildReferences);canonicalChildren=List.copyOf(canonicalChildren);
        require(originalParentReference.bytes()>0&&originalChildReferences.size()==original.children().size()
                &&originalChildReferences.stream().allMatch(ref->ref.bytes()>0&&!ref.equals(originalParentReference))
                &&originalChildReferences.stream().distinct().count()==originalChildReferences.size(),
                "cleanup full original receipt reference vector is missing or recursive");
        require(archive.loadReceipt(originalParentReference).equals(original.parent()),"cleanup original parent reference changed");
        for(int index=0;index<original.children().size();index++)
            require(archive.loadReceipt(originalChildReferences.get(index)).equals(original.children().get(index)),
                    "cleanup original child reference changed its complete receipt");
        // Custody of this object is DATA only: its installed-source authorization schema must be
        // independently validated by the actual issuer/replay callback, never inferred from a Ref.
        require(authorizationReference.bytes()>0&&authorizationReference.bytes()<=65_536
                &&!authorizationReference.equals(originalParentReference)
                &&!originalChildReferences.contains(authorizationReference),"bounded distinct durable cleanup authorization required");
        byte[] authorization=archive.loadMaterial(authorizationReference).bytes();
        require(authorization.length==authorizationReference.bytes()&&ActionCodec.sha256(authorization).equals(authorizationReference.sha256()),
                "cleanup durable authorization original bytes changed");
        requireAuthorizationBindings(authorization,original,originalParentReference,originalChildReferences,armedStatus,beforeCancel,issuedAt,ownDeadline,archive);
        requireFreshArmedPaused(original,armedStatus,beforeCancel,issuedAt,ownDeadline,beforeCancel.observedAt());
        var preQuery=reopenPhysical(original.parent().command(),armedStatus,archive);
        reopenFrame(beforeCancel,archive,frames);
        require(beforeCancel.provenance().independentOf(armedStatus.receipt().requestId())
                &&!beforeCancel.originalEvidence().equals(armedStatus.originalEvidence()),
                "cleanup pre-CANCEL frame is not independent of the fresh ARMED query");
        requireSuccessorPrefix(original,successor,canonicalChildren,beforeCancel,ownDeadline,true);
        var cancel=canonicalChildren.getLast();
        require(cancel.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied,
                "cleanup requires the real canonical CANCEL ControlApplied; UNKNOWN or IDLE alone is insufficient");
        var state=(ActionState.Settled)cancel.state();var control=(ActionState.ControlApplied)state.settlement();
        var command=cancel.command();var attempt=state.attempt();
        require(control.observerSchema().equals(AdvancePrimitives.CLOCK_OBSERVER)&&control.supportingReads().isEmpty(),
                "cleanup CANCEL observer or supporting reads changed");
        var ack=ActionEffects.controlAcknowledgement(command,attempt,state.dispatch(),control);
        require(ack.nativeOk()&&ack.requestId().equals(attempt.requestId())&&ack.outbound().isPresent()
                &&ack.originalResultToken().isPresent()&&ack.custody().isPresent(),"cleanup has no actual positive original CANCEL ACK");
        require(attempt.preparedRequest().equals(AdvancePrimitives.prepareRequest(command))
                &&archive.loadRequest(archive.requestReferenceOf(attempt.preparedRequest())).equals(attempt.preparedRequest())
                &&archive.load(archive.referenceOf(state.dispatch())).equals(state.dispatch())
                &&archive.load(archive.referenceOf(ack)).equals(ack),"cleanup original producer, dispatch or ACK changed");
        require(archive.loadReceipt(archive.receiptReferenceOf(cancel)).equals(cancel),"cleanup complete CANCEL receipt changed");
        ActionEffects.validate(command,attempt,state.dispatch(),control);
        var sent=ack.custody().orElseThrow();sent.verify(ack,attempt.guard());
        require(!attempt.submittedAt().isBefore(beforeCancel.observedAt())&&attempt.submittedAt().isBefore(ownDeadline)
                &&!sent.writeEntered().observedAt().isBefore(attempt.submittedAt())&&sent.writeEntered().observedAt().isBefore(ownDeadline)
                &&!sent.writeEntered().observedAt().isAfter(preQuery.responseReceived().observedAt().plus(Duration.ofMinutes(2)))
                &&!sent.writeEntered().observedAt().isAfter(beforeCancel.observedAt().plus(Duration.ofMinutes(2))),
                "cleanup original CANCEL was not submitted within its own unchanged deadline");
        var nativeResult=AdvancePrimitives.nativeResult(ack,command.operation().value());
        require(nativeResult.path("status").isTextual()&&nativeResult.path("status").textValue().equals("canceled"),
                "cleanup raw CANCEL result does not report canceled");
        var actualCancelRead=control.read();
        var canceledStatus=new ClockStatusRead.Observation(ClockStatusRead.decode(actualCancelRead.original()),actualCancelRead,
                archive.referenceOf(actualCancelRead.original()));
        org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(actualCancelRead,archive);
        var canceledQuery=actualCancelRead.original().custody().orElseThrow();canceledQuery.verify(actualCancelRead);
        boolean childReconciling=actualCancelRead.request().origin() instanceof CommandOrigin.Reconciliation;
        require(actualCancelRead.contractId().equals(childReconciling?ClockStatusRead.RECONCILIATION_CONTRACT_ID:ClockStatusRead.CONTRACT_ID)
                &&actualCancelRead.request().operation().value().equals(ClockStatusRead.STEP)
                &&actualCancelRead.request().arguments().members().isEmpty()
                &&actualCancelRead.request().source().equals(command.source())&&actualCancelRead.request().sessionId().equals(command.sessionId())
                &&(childReconciling
                    ?actualCancelRead.before().guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                        &&actualCancelRead.after().guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                    :actualCancelRead.request().origin() instanceof CommandOrigin.Gameplay
                        &&actualCancelRead.before().guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                        &&actualCancelRead.after().guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                        &&actualCancelRead.before().binding().origin() instanceof CommandOrigin.Gameplay
                        &&actualCancelRead.after().binding().origin() instanceof CommandOrigin.Gameplay),
                "cleanup child Status must retain its actual ordinary or reconciliation clock contract");
        AdvancePrimitiveArchivedReplay.verifyRead(command,actualCancelRead,archive);
        new AdvancePrimitiveArchivedReplay(frames).verify(cancel,archive);
        require(control.actual().equals(AdvancePrimitives.statusValues(canceledStatus.status())),"cleanup child Status semantic values changed");
        AdvanceClock.validateCancellation(original.originalArm(),canceledStatus.status(),original.plan(),beforeCancel.identity().frame().identity().dateRaw());
        require(canceledStatus.status().completedDailyTicks()==armedStatus.status().completedDailyTicks()
                &&canceledStatus.status().lastObservedDateRaw()==armedStatus.status().lastObservedDateRaw(),
                "cleanup IDLE status reset or replaced the actually observed original ARMED progress");
        require(!actualCancelRead.requestId().equals(armedStatus.receipt().requestId())&&!actualCancelRead.requestId().equals(ack.requestId())
                &&!sent.writeEntered().observedAt().isBefore(preQuery.responseReceived().observedAt())
                &&!canceledQuery.writeEntered().observedAt().isBefore(sent.responseReceived().observedAt()),
                "cleanup child Status is reused or predates its actual CANCEL ACK");
        var terminalQuery=reopenPhysical(original.parent().command(),terminalStatus,archive);
        require(!terminalStatus.receipt().requestId().equals(actualCancelRead.requestId())
                &&!terminalStatus.receipt().requestId().equals(armedStatus.receipt().requestId())
                &&!terminalStatus.receipt().requestId().equals(ack.requestId())
                &&!terminalQuery.writeEntered().observedAt().isBefore(canceledQuery.responseReceived().observedAt())
                &&terminalStatus.status().equals(canceledStatus.status()),"cleanup terminal must independently read the same confirmed IDLE slot after its child");
        AdvanceClock.validateCancellation(original.originalArm(),terminalStatus.status(),original.plan(),beforeCancel.identity().frame().identity().dateRaw());
        requireReadWindow(actualCancelRead,canceledQuery);requireReadWindow(terminalStatus.receipt(),terminalQuery);
        requirePausedFrame(original,ending);reopenFrame(ending,archive,frames);
        AdvanceClock.requireAfterControl(original.parent().command(),beforeCancel,terminalStatus,ending);
        require(!ending.observedAt().isAfter(terminalStatus.receipt().request().deadline()),
                "cleanup complete ending escaped its actual independent observation window");
        var replay=new AdvancePrimitiveArchivedReplay(frames);
        for(var child:original.children())replay.verify(child,archive);
    }

    private static void requireReadWindow(PlanningReadReceipt read,NativeRequestChronology query) {
        require(read.request().deadline().isAfter(query.writeEntered().observedAt())
                &&!read.request().deadline().isAfter(query.writeEntered().observedAt().plus(Duration.ofMinutes(2)))
                &&!query.responseReceived().observedAt().isAfter(read.request().deadline()),
                "cleanup collection requires its own actual bounded READ window, not a renewed CANCEL deadline");
    }

    private static void requireAuthorizationBindings(byte[] bytes,Original original,
            org.xar.ck3.control.contracts.ExactRef parentReference,List<org.xar.ck3.control.contracts.ExactRef> childReferences,
            ClockStatusRead.Observation armedStatus,AdvanceObservationPort.Frame beforeCancel,Instant issuedAt,Instant ownDeadline,
            ActionPorts.OutcomeArchive archive) {
        var row=org.xar.ck3.control.contracts.StrictJson.object(org.xar.ck3.control.contracts.StrictJson.parse(bytes,65_536),
                java.util.Set.of("schema","original_parent","original_children","armed_read","before_cancel","issued_at_utc","deadline_utc"));
        require(org.xar.ck3.control.contracts.StrictJson.text(row.get("schema")).equals("xar.life-post-resume-pause-authorization/v1")
                &&org.xar.ck3.control.contracts.ExactRef.fromJson(row.get("original_parent")).equals(parentReference)
                &&row.get("original_children").isArray()&&row.get("original_children").size()==childReferences.size(),
                "cleanup durable authorization changed its schema, parent or complete child vector");
        for(int index=0;index<childReferences.size();index++)
            require(org.xar.ck3.control.contracts.ExactRef.fromJson(row.get("original_children").get(index)).equals(childReferences.get(index)),
                    "cleanup durable authorization changed an original child reference");
        require(archive.loadRead(org.xar.ck3.control.contracts.ExactRef.fromJson(row.get("armed_read"))).equals(armedStatus.receipt())
                &&Instant.parse(org.xar.ck3.control.contracts.StrictJson.utc(org.xar.ck3.control.contracts.StrictJson.text(row.get("issued_at_utc")))).equals(issuedAt)
                &&Instant.parse(org.xar.ck3.control.contracts.StrictJson.utc(org.xar.ck3.control.contracts.StrictJson.text(row.get("deadline_utc")))).equals(ownDeadline),
                "cleanup durable authorization changed its actual ARMED read or immutable operation window");
        var frame=org.xar.ck3.control.contracts.StrictJson.object(row.get("before_cancel"),java.util.Set.of(
                "identity","observation_provenance","observed_at_utc","native_frame","driver_facts","semantic"));
        var facts=org.xar.ck3.control.contracts.ExactRef.fromJson(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(
                beforeCancel.semantic().get("java_driver_facts_evidence")));
        require(org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.decodeObservation(frame.get("identity")).equals(beforeCancel.identity())
                &&ObservationProvenanceCodec.decode(frame.get("observation_provenance")).equals(beforeCancel.provenance())
                &&Instant.parse(org.xar.ck3.control.contracts.StrictJson.utc(org.xar.ck3.control.contracts.StrictJson.text(frame.get("observed_at_utc")))).equals(beforeCancel.observedAt())
                &&org.xar.ck3.control.contracts.ExactRef.fromJson(frame.get("native_frame")).equals(beforeCancel.originalEvidence())
                &&org.xar.ck3.control.contracts.ExactRef.fromJson(frame.get("driver_facts")).equals(facts)
                &&org.xar.ck3.control.application.driver.DriverJson.object(archive.loadMaterial(
                    org.xar.ck3.control.contracts.ExactRef.fromJson(frame.get("semantic"))).bytes(),RawJson.MAXIMUM_BYTES).equals(beforeCancel.semantic()),
                "cleanup durable authorization changed the complete original pre-CANCEL paused frame");
    }
}
