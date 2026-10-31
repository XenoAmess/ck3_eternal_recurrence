package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.session.AutoFailureDiagnostic;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Original pre-normal-Status failure custody and its read-only public projection. No Native I/O or credit. */
public final class ExactDayClockFailureEvidence implements AutoFailureDiagnostic.Port {
    public static final String SCHEMA="xar.java.exact-day-clock-stop-not-observed/v1";
    public static final String GATE_SCHEMA="xar.java.exact-day-clock-stop-not-observed-gate/v1";
    public static final String PUBLIC_SCHEMA="xar.exact-day-clock-failure.v2";
    private static final Set<String> FIELDS=Set.of("schema","failure_kind","parent_action_id","parent_body_sha256","plan",
            "starting","last_wait","armed","action_start","cleanup_start","children","cleanup_before","cleanup_status_read","cleanup_error","original_gate",
            "normal_status_query_attempted","stop_validation_attempted","stopped_status","stop_credit");
    private final NativeEffectEvidence.FrameLoader frames;
    public ExactDayClockFailureEvidence(NativeEffectEvidence.FrameLoader frames){this.frames=Objects.requireNonNull(frames);}
    public static ExactRef preserveOriginal(ExactDayClockFailure.StopNotObserved original,ActionSnapshotReader canonical,ActionPorts.OutcomeArchive archive){
        return preserve(original,ExactDayClockFailure.CleanupTrace.empty(),Optional.empty(),canonical,archive);
    }
    public static ExactRef preserve(ExactDayClockFailure.StopNotObserved original,ExactDayClockFailure.CleanupTrace cleanup,
            ExactRef originalGate,ActionSnapshotReader canonical,ActionPorts.OutcomeArchive archive){
        return preserve(original,cleanup,Optional.of(Objects.requireNonNull(originalGate)),canonical,archive);
    }
    private static ExactRef preserve(ExactDayClockFailure.StopNotObserved original, ExactDayClockFailure.CleanupTrace cleanup,
            Optional<ExactRef> originalGate, ActionSnapshotReader canonical, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(original);Objects.requireNonNull(cleanup);Objects.requireNonNull(canonical);Objects.requireNonNull(archive);
        ActionCommand parent=original.parent();
        return canonical.withFrozen(lease -> {
            ActionReceipt actual=lease.find(parent.actionId()).orElseThrow(() -> new IllegalArgumentException("canonical exact-day failure parent absent"));
            require(actual.command().equals(parent) && actual.bodySha256().equals(ActionCodec.bodySha256(parent)),"canonical exact-day parent body changed");
            CompositeExecution execution=ActionTransitions.composite(actual.state()).orElseThrow();
            require(execution.handlerId().equals(LifeAdvanceComposite.HANDLER) && execution.guard().observed().equals(parent.before()),
                    "original exact-day gate must originate in the actual Life parent guard");
            List<ActionReceipt> children=new ArrayList<>();
            for(var retained:execution.children()){
                ActionReceipt child=lease.find(retained.actionId()).orElseThrow();
                require(child.command().actionId().equals(retained.actionId()) && child.bodySha256().equals(retained.bodySha256()),"canonical exact-day original child changed");
                requireChild(parent,child);children.add(child);
            }
            require(original.cleanupStart()<=children.size()
                    && children.subList(original.actionStart(),original.cleanupStart()).equals(original.beforeCleanup()),
                    "original exact-day slice differs from canonical child custody");
            require(originalGate.isPresent() || children.size()==original.cleanupStart(),"typed original gate must precede cleanup children");
            var row=StrictJson.object();row.put("schema",originalGate.isPresent()?SCHEMA:GATE_SCHEMA);row.set("original_gate",originalGate.<JsonNode>map(ExactRef::toJson).orElseGet(()->com.fasterxml.jackson.databind.node.NullNode.getInstance()));row.put("failure_kind","STOP_NOT_OBSERVED_BEFORE_NORMAL_STATUS");
            row.put("parent_action_id",parent.actionId());row.put("parent_body_sha256",actual.bodySha256());
            row.set("plan",OpportunityJson.toNode(original.plan().json()));row.set("starting",preserveFrame(original.starting(),archive));
            row.set("last_wait",preserveFrame(original.lastWait(),archive));row.set("armed",SentinelObservation.toJson(original.armed()));
            row.put("action_start",original.actionStart());row.put("cleanup_start",original.cleanupStart());
            var refs=row.putArray("children");for(ActionReceipt child:children)refs.add(archive.preserveReceipt(child).toJson());
            row.set("cleanup_before",cleanup.beforePause().<JsonNode>map(value -> preserveFrame(value,archive)).orElseGet(()->com.fasterxml.jackson.databind.node.NullNode.getInstance()));
            row.set("cleanup_status_read",cleanup.status().<JsonNode>map(value -> archive.preserveRead(value.receipt()).toJson()).orElseGet(()->com.fasterxml.jackson.databind.node.NullNode.getInstance()));
            if(cleanup.error().isPresent())row.put("cleanup_error",cleanup.error().orElseThrow());else row.putNull("cleanup_error");
            row.put("normal_status_query_attempted",false);row.put("stop_validation_attempted",false);row.putNull("stopped_status");row.put("stop_credit",false);
            RawJson material=new RawJson(StrictJson.canonical(row));ExactRef result=archive.preserveMaterial(material);
            exact(result,archive.loadMaterial(result).bytes());lease.assertCurrent();return result;
        });
    }
    /** A real retained typed failure permanently fences post-hoc cleanup from becoming original stop credit. */
    public static Optional<ActionPorts.Pending> retainedPending(ActionCommand parent, CompositeExecution retained,
            ActionSnapshotReader canonical, ActionPorts.OutcomeArchive archive) {
        return canonical.withFrozen(lease -> {
            Optional<ActionReceipt> actual=lease.find(parent.actionId());if(actual.isEmpty())return Optional.empty();
            ActionReceipt receipt=actual.orElseThrow();
            require(receipt.command().equals(parent) && receipt.bodySha256().equals(ActionCodec.bodySha256(parent)),"canonical exact-day continuation parent changed");
            if(!(receipt.state() instanceof ActionState.CompositeUnknown unknown))return Optional.empty();
            require(unknown.execution().equals(retained),"exact-day continuation execution differs from canonical custody");
            for(ExactRef ref:unknown.evidence()){
                Optional<ObjectNode> row=originalRow(ref,archive);if(row.isEmpty())continue;
                header(row.orElseThrow(),parent);lease.assertCurrent();
                return Optional.of(new ActionPorts.Pending(ExactDayClockFailure.MESSAGE,unknown.evidence()));
            }
            lease.assertCurrent();return Optional.empty();
        });
    }
    @Override public Optional<AutoFailureDiagnostic> project(ActionReceipt actual,ActionPorts.OutcomeArchive archive){
        Objects.requireNonNull(actual);Objects.requireNonNull(archive);
        if(!(actual.state() instanceof ActionState.CompositeUnknown unknown))return Optional.empty();
        List<AutoFailureDiagnostic> found=new ArrayList<>();
        for(ExactRef ref:unknown.evidence()){
            Optional<ObjectNode> value=originalRow(ref,archive);if(value.isEmpty())continue;
            ObjectNode row=value.orElseThrow();if(!SCHEMA.equals(row.path("schema").textValue()))continue;
            ActionCommand parent=actual.command();header(row,parent);
            ExactRef gateRef=ExactRef.fromJson(row.get("original_gate"));
            require(unknown.evidence().contains(gateRef),"exact-day final basis lost its canonically retained original gate");
            ObjectNode gate=originalRow(gateRef,archive).orElseThrow();header(gate,parent);
            require(GATE_SCHEMA.equals(gate.path("schema").textValue()) && gate.get("original_gate").isNull(),"exact-day original pre-cleanup gate changed");
            for(String key:List.of("starting","last_wait","armed","action_start","cleanup_start","plan"))require(gate.get(key).equals(row.get(key)),"exact-day original gate differs from final cleanup basis");
            require(gate.get("children").isArray() && gate.get("children").size()==index(row.get("cleanup_start"))
                    && gate.get("cleanup_before").isNull() && gate.get("cleanup_status_read").isNull() && gate.get("cleanup_error").isNull(),"exact-day gate contains cleanup or lost its original action boundary");
            for(int i=0;i<gate.get("children").size();i++)require(gate.get("children").get(i).equals(row.get("children").get(i)),"exact-day original gate child prefix changed");
            require(actual.bodySha256().equals(ActionCodec.bodySha256(parent)) && unknown.execution().handlerId().equals(LifeAdvanceComposite.HANDLER)
                    && unknown.execution().guard().observed().equals(parent.before())
                    && unknown.execution().guard().source().equals(parent.source()) && unknown.execution().guard().sessionId().equals(parent.sessionId()),
                    "exact-day diagnostic differs from the actual Life handler/entry guard");
            var entry=RootGuardEvidence.loadFrame(unknown.execution().guard(),archive,frames);
            var starting=loadFrame(row.get("starting"),parent,archive);
            var last=loadFrame(row.get("last_wait"),parent,archive);
            require(entry.identity().equals(starting.identity()) && entry.semantic().equals(starting.semantic())
                    && entry.originalEvidence().equals(starting.originalEvidence()),"exact-day original starting Native/Driver differs from canonical entry");
            List<ActionReceipt> children=loadChildren(row.get("children"),parent,unknown.execution(),archive);
            int start=index(row.get("action_start")),cleanupStart=index(row.get("cleanup_start"));
            require(start<=cleanupStart && cleanupStart<=children.size(),"exact-day original action bounds differ");
            AdvancePlan plan=AdvancePlan.decode(parent);
            var armed=SentinelObservation.decode(row.get("armed"));
            var failure=new ExactDayClockFailure.StopNotObserved(parent,plan,starting,last,armed,start,children.subList(start,cleanupStart));
            var primitiveReplay=new AdvancePrimitiveArchivedReplay(frames);
            for(ActionReceipt child:failure.beforeCleanup())primitiveReplay.verify(child,archive);
            Optional<AdvanceObservationPort.Frame> cleanupBefore=row.get("cleanup_before").isNull()?Optional.empty():Optional.of(loadFrame(row.get("cleanup_before"),parent,archive));
            verifyCleanupChildren(failure,cleanupBefore,children,primitiveReplay,archive);
            Optional<ClockStatusRead.Observation> cleanupRead=Optional.empty();
            if(!row.get("cleanup_status_read").isNull()){
                ExactRef readRef=ExactRef.fromJson(row.get("cleanup_status_read"));PlanningReadReceipt read=archive.loadRead(readRef);
                require(archive.readReferenceOf(read).equals(readRef) && read.request().source().equals(parent.source())
                        && read.request().sessionId().equals(parent.sessionId()) && read.contractId().equals(ClockStatusRead.CONTRACT_ID)
                        && read.request().operation().equals(new OperationKey(ClockStatusRead.STEP)),"cleanup query source/contract changed");
                NativeRecordedEvidenceVerifier.requireRead(read,archive);
                var resume=failure.beforeCleanup().stream().filter(child->child.command().operation().value().equals("resume-map")).findFirst().orElseThrow();
                NativeRequestChronology.requireSampledAfter(read,((ActionState.Settled)resume.state()).attempt(),resume.ack().orElseThrow());
                verifyCleanupRead(failure,cleanupBefore.orElseThrow(() -> new IllegalArgumentException("cleanup Status lost its actual pre-pause frame")),read,children,archive);
                cleanupRead=Optional.of(new ClockStatusRead.Observation(ClockStatusRead.decode(read.original()),read,archive.referenceOf(read.original())));
            }
            Optional<String> error=row.get("cleanup_error").isNull()?Optional.empty():Optional.of(StrictJson.text(row.get("cleanup_error")));
            var cleanup=new ExactDayClockFailure.CleanupTrace(cleanupBefore,cleanupRead,error);
            RawJson publicBody=projectActual(failure,cleanup,children);
            found.add(new AutoFailureDiagnostic(AutoFailureDiagnostic.Kind.EXACT_DAY,parent.actionId(),actual.bodySha256(),
                    ExactDayClockFailure.MESSAGE,publicBody,ref));
        }
        require(found.size()<=1,"two original exact-day failure bases claim one parent");return found.stream().findFirst();
    }
    private void verifyCleanupRead(ExactDayClockFailure.StopNotObserved failure,AdvanceObservationPort.Frame cleanupBefore,
            PlanningReadReceipt read,List<ActionReceipt> children,ActionPorts.OutcomeArchive archive) {
        var before=guardFrame(read.before().binding(),archive);
        var after=guardFrame(read.after().binding(),archive);
        requireNotEarlier(failure.parent(),cleanupBefore,before);
        requireNotEarlier(failure.parent(),before,after);
        require(AdvancePolicy.truth(before.semantic(),"paused") && AdvancePolicy.truth(before.semantic(),"map_ready")
                && AdvancePolicy.truth(after.semantic(),"paused") && AdvancePolicy.truth(after.semantic(),"map_ready")
                && before.identity().equals(read.request().before()) && before.identity().equals(after.identity()),
                "cleanup Status does not retain its actual stable paused request frame");
        AdvanceClock.requireSameSlot(failure.armed(),ClockStatusRead.decode(read.original()));
        for(ActionReceipt child:children.subList(failure.cleanupStart(),children.size())) {
            if(child.command().operation().value().equals("pause-map") && (child.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED || child.state() instanceof ActionState.Settled typed && typed.settlement() instanceof ActionState.PauseConfirmed)) {
                var settled=(ActionState.Settled)child.state();
                NativeRequestChronology.requireSampledAfter(read,settled.attempt(),child.ack().orElseThrow());
            } else if(child.command().operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX)) {
                var attempt=ActionTransitions.attempt(child.state());
                var ack=child.ack();
                if(attempt.isPresent()) {
                    if(ack.isPresent() && ack.orElseThrow().nativeOk()) NativeRequestChronology.requireBeforeSubmission(read,attempt.orElseThrow(),ack.orElseThrow());
                    else require(!read.original().custody().orElseThrow().responseReceived().observedAt().isAfter(attempt.orElseThrow().submittedAt()),
                            "cleanup Status was not observed before its original unresolved/rejected cancellation attempt");
                } else require(ack.isEmpty() && child.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED,
                        "cleanup without an actual attempt cannot claim a dispatch or applied cancellation");
                require(ClockStatusRead.decode(read.original()).state()==org.xar.ck3.control.reconciliation.LateOutcome.State.ARMED,
                        "cleanup cancellation did not use its original pre-cancel ARMED Status");
            }
        }
    }
    private static void verifyCleanupChildren(ExactDayClockFailure.StopNotObserved failure,
            Optional<AdvanceObservationPort.Frame> cleanupBefore,List<ActionReceipt> children,
            AdvancePrimitiveArchivedReplay primitives,ActionPorts.OutcomeArchive archive) {
        if(cleanupBefore.isPresent())requireNotEarlier(failure.parent(),failure.lastWait(),cleanupBefore.orElseThrow());
        require(children.size()==failure.cleanupStart() || cleanupBefore.isPresent(),"cleanup mutation lost its actual pre-pause frame");
        boolean unresolved=false,canceled=false;
        for(ActionReceipt child:children.subList(failure.cleanupStart(),children.size())) {
            require(!unresolved,"cleanup continued after an original UNKNOWN child");
            String step=child.command().operation().value();
            require(!canceled && (step.equals("pause-map") || step.equals(ClockStatusRead.CANCEL_PREFIX+failure.armed().generation().decimal())),
                    "exact-day cleanup contains a foreign control or a post-cancel mutation");
            canceled=step.startsWith(ClockStatusRead.CANCEL_PREFIX);unresolved=!child.settled();
            if(child.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED || child.state() instanceof ActionState.Settled typed && typed.settlement() instanceof ActionState.PauseConfirmed)primitives.verify(child,archive);
            else if(child.state() instanceof ActionState.Settled settled)
                ActionEffects.validate(child.command(),settled.attempt(),settled.dispatch(),settled.settlement());
        }
    }
    private AdvanceObservationPort.Frame guardFrame(GuardEvidence guard,ActionPorts.OutcomeArchive archive) {
        var actual=RootGuardEvidence.loadFrame(guard,archive,frames);
        var push=new ObservationProvenance.Push(actual.identity().frame().snapshotId(),actual.identity().frame().identity().nativeRevision(),actual.originalEvidence());
        return new AdvanceObservationPort.Frame(actual.identity(),actual.source(),actual.sessionId(),actual.semantic(),push,actual.observedAt(),actual.originalEvidence());
    }
    private static void requireNotEarlier(ActionCommand parent,AdvanceObservationPort.Frame previous,AdvanceObservationPort.Frame actual) {
        AdvanceWait.binding(parent,previous,actual);
        require(actual.identity().frame().identity().player().equals(previous.identity().frame().identity().player())
                && actual.identity().frame().revision().compareTo(previous.identity().frame().revision())>=0
                && actual.identity().frame().identity().nativeRevision().compareTo(previous.identity().frame().identity().nativeRevision())>=0
                && !actual.observedAt().isBefore(previous.observedAt()),"cleanup frame predates or crosses its actual original failure/control frame");
    }
    private static Optional<ObjectNode> originalRow(ExactRef ref,ActionPorts.OutcomeArchive archive){
        RawJson raw;try{raw=archive.loadMaterial(ref);}catch(IllegalArgumentException|UnsupportedOperationException nonMaterial){return Optional.empty();}
        exact(ref,raw.bytes());JsonNode node=StrictJson.parse(raw.bytes());
        if(!node.isObject()||!node.path("schema").isTextual()||!Set.of(SCHEMA,GATE_SCHEMA).contains(node.path("schema").textValue()))return Optional.empty();
        return Optional.of(StrictJson.object(node,FIELDS));
    }
    private static void header(ObjectNode row,ActionCommand parent){
        AdvancePlan plan=AdvancePlan.decode(parent);
        require(LifeAdvanceComposite.accepts(parent.operation().value())
                && plan.exactOneDay() && plan.clockMode()==AdvancePlan.ClockMode.EXACT_SENTINEL && plan.dailyWatch().isEmpty()
                && parent.actionId().equals(StrictJson.text(row.get("parent_action_id")))
                && ActionCodec.bodySha256(parent).equals(StrictJson.text(row.get("parent_body_sha256")))
                && "STOP_NOT_OBSERVED_BEFORE_NORMAL_STATUS".equals(StrictJson.text(row.get("failure_kind")))
                && row.get("plan").equals(OpportunityJson.toNode(AdvancePlan.decode(parent).json()))
                && row.get("normal_status_query_attempted").isBoolean()&&!row.get("normal_status_query_attempted").booleanValue()
                && row.get("stop_validation_attempted").isBoolean()&&!row.get("stop_validation_attempted").booleanValue()
                && row.get("stopped_status").isNull()&&row.get("stop_credit").isBoolean()&&!row.get("stop_credit").booleanValue(),
                "typed exact-day original failure parent/plan/phase changed");
    }
    private static ObjectNode preserveFrame(AdvanceObservationPort.Frame actual,ActionPorts.OutcomeArchive archive){
        var value=actual.semantic().get("java_driver_facts_evidence");require(value instanceof OpportunityJson.Obj,"exact-day frame requires complete original Driver evidence");
        ExactRef facts=ExactRef.fromJson(OpportunityJson.toNode(value));exact(actual.originalEvidence(),archive.loadNativeFrame(actual.originalEvidence()));
        exact(facts,archive.loadFullMaterial(facts).bytes());var row=StrictJson.object();row.set("native_frame",actual.originalEvidence().toJson());
        row.set("driver_facts",facts.toJson());row.set("provenance",ObservationProvenanceCodec.encode(actual.provenance()));
        row.set("semantic",archive.preserveMaterial(RawJson.fullMaterial(org.xar.ck3.control.application.driver.DriverJson.encode(actual.semantic()))).toJson());return row;
    }
    private AdvanceObservationPort.Frame loadFrame(JsonNode value,ActionCommand parent,ActionPorts.OutcomeArchive archive){
        ObjectNode row=StrictJson.object(value,Set.of("native_frame","driver_facts","provenance","semantic"));
        ExactRef nativeRef=ExactRef.fromJson(row.get("native_frame")),facts=ExactRef.fromJson(row.get("driver_facts")),semantic=ExactRef.fromJson(row.get("semantic"));
        exact(nativeRef,archive.loadNativeFrame(nativeRef));exact(facts,archive.loadFullMaterial(facts).bytes());
        RawJson originalSemantic=archive.loadFullMaterial(semantic);exact(semantic,originalSemantic.bytes());
        var actual=frames.load(new NativeEffectEvidence.FrameBasis(nativeRef,facts),archive);
        var provenance=ObservationProvenanceCodec.decode(row.get("provenance"));
        if (provenance instanceof ObservationProvenance.FreshSnapshotQuery query) {
            frames.verifyFreshSnapshotQuery(query, actual, archive);
        } else if (provenance instanceof ObservationProvenance.Push push) {
            var actualPush = new ObservationProvenance.Push(actual.identity().frame().snapshotId(), actual.identity().frame().identity().nativeRevision(), actual.originalEvidence());
            require(push.equals(actualPush), "exact-day original Native/Driver/Push/connection changed");
        } else {
            throw new IllegalArgumentException("exact-day original provenance must be Push or FreshSnapshotQuery");
        }
        require(actual.semantic().equals(org.xar.ck3.control.application.driver.DriverJson.object(originalSemantic.bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES))
                && actual.originalEvidence().equals(nativeRef)
                && actual.source().equals(parent.source())&&actual.sessionId().equals(parent.sessionId())&&actual.identity().game().equals(parent.before().game()),
                "exact-day original Native/Driver/connection changed");
        return new AdvanceObservationPort.Frame(actual.identity(),actual.source(),actual.sessionId(),actual.semantic(),provenance,actual.observedAt(),actual.originalEvidence());
    }
    private static List<ActionReceipt> loadChildren(JsonNode values,ActionCommand parent,CompositeExecution execution,ActionPorts.OutcomeArchive archive){
        require(values.isArray()&&values.size()<=256&&values.size()==execution.children().size(),"exact-day failure must retain every canonical child");
        List<ActionReceipt> result=new ArrayList<>();Set<String> ids=new java.util.HashSet<>();
        for(int i=0;i<values.size();i++){
            ExactRef ref=ExactRef.fromJson(values.get(i));ActionReceipt child=archive.loadReceipt(ref);var retained=execution.children().get(i);
            require(child.command().actionId().equals(retained.actionId())&&child.bodySha256().equals(retained.bodySha256())
                    && archive.receiptReferenceOf(child).equals(ref)&&ids.add(child.command().actionId()),"exact-day canonical child order/body/reference changed");
            requireChild(parent,child);result.add(child);
        }
        return List.copyOf(result);
    }
    private static void requireChild(ActionCommand parent,ActionReceipt child){
        ActionCommand command=child.command();require(child.bodySha256().equals(ActionCodec.bodySha256(command))
                && command.source().equals(parent.source())&&command.sessionId().equals(parent.sessionId())&&command.before().game().equals(parent.before().game())
                && command.before().machineId().equals(parent.before().machineId())&&command.claims().equals(parent.claims())
                && !command.deadline().isAfter(parent.deadline())&&AdvancePrimitives.supports(command.operation()),"exact-day canonical child original authority changed");
    }
    private static int index(JsonNode node){require(node!=null&&node.isIntegralNumber()&&node.canConvertToInt()&&node.intValue()>=0&&node.intValue()<=256,"bounded exact original action index required");return node.intValue();}
    private static RawJson projectActual(ExactDayClockFailure.StopNotObserved original,ExactDayClockFailure.CleanupTrace cleanup,List<ActionReceipt> all){
        var body=StrictJson.object();body.put("schema",PUBLIC_SCHEMA);body.put("is_error",true);body.put("credit",0);body.put("never_replay",true);
        body.put("original_error_type",original.getClass().getSimpleName());body.put("original_error",ExactDayClockFailure.MESSAGE);
        body.put("starting_date_raw",original.plan().startingDateRaw());body.put("target_date_raw",original.plan().targetDateRaw());body.put("requested_speed",original.plan().speed());
        body.put("normal_status_query_attempted",false);body.put("stop_validation_attempted",false);body.putNull("stopped_status");body.put("stop_credit",false);
        JsonNode fullArm=SentinelObservation.toJson(original.armed());ObjectNode arm=StrictJson.object();
        for(String key:List.of("state","generation","starting_date_raw","target_date_raw","last_observed_date_raw","trigger_date_raw","speed","mode","army_count","combat_count","completed_daily_ticks","intermediate_pause_count","trigger_flags","signed_date_delta_from_target_raw","overshoot_days","pause_wrapper_called","pause_observed","terminal_observed","abnormal"))arm.set(key,fullArm.get(key));
        arm.put("generation",original.armed().generation().decimal());body.set("armed_reply",arm);
        body.set("starting_frame",frameProjection(original.starting()));body.set("last_wait_frame",frameProjection(original.lastWait()));
        body.set("cleanup_before_pause_frame",cleanup.beforePause().<JsonNode>map(ExactDayClockFailureEvidence::frameProjection).orElseGet(()->com.fasterxml.jackson.databind.node.NullNode.getInstance()));
        body.set("before_cleanup_actions",actions(all.subList(original.actionStart(),original.cleanupStart()),Optional.empty()));
        body.set("cleanup_actions",actions(all.subList(original.cleanupStart(),all.size()),cleanup.error()));body.put("truncated",false);body.putNull("wait_progress");
        if(StrictJson.canonical(body).length>8192){for(String key:List.of("starting_frame","last_wait_frame","cleanup_before_pause_frame","before_cleanup_actions","cleanup_actions"))body.putNull(key);body.put("truncated",true);}
        if(StrictJson.canonical(body).length>8192)body.putNull("armed_reply");
        RawJson result=new RawJson(StrictJson.canonical(body));require(result.bytes().length<=8192,"bounded original exact-day diagnostic exceeded limit");return result;
    }
    private static ObjectNode frameProjection(AdvanceObservationPort.Frame actual){
        JsonNode semantic=OpportunityJson.toNode(actual.semantic());ObjectNode row=StrictJson.object();
        for(String key:List.of("date_raw","native_revision","revision","snapshot_id","speed","paused","player_character_id","episode_character_id","episode_id","alive","map_ready","monotonic_ms"))row.set(key,scalar(semantic.get(key),Set.of("native_revision","revision","monotonic_ms").contains(key)));
        var diagnostic=semantic.path("diagnostics");var connection=row.putObject("connection");
        connection.set("connection_generation",scalar(diagnostic.get("connection_generation"),true));connection.set("bridge_pid",scalar(diagnostic.get("bridge_pid"),false));
        var heartbeat=diagnostic.path("last_heartbeat");
        ObjectNode cached=row.putObject("cached_heartbeat");for(String key:List.of("sequence","monotonic_ms","pid"))cached.set(key,scalar(heartbeat.get(key),!key.equals("pid")));
        ObjectNode owner=row.putObject("cached_owner");for(String key:List.of("pump_epochs","owner_verified_pump_epochs","date_raw","paused","failure"))owner.set(key,scalar(heartbeat.path("main_thread_query_mailbox_v1").get(key),key.endsWith("epochs")));
        ObjectNode observer=row.putObject("cached_observer");for(String key:List.of("started_ms","completed_ms","read_in_progress","last_read_available"))observer.set(key,scalar(heartbeat.path("snapshot_observer_12002").get(key),key.endsWith("_ms")));
        return row;
    }
    private static ObjectNode actions(List<ActionReceipt> values,Optional<String> cleanupError){
        ObjectNode row=StrictJson.object();var rows=row.putArray("rows");int count=0;
        for(ActionReceipt child:values.stream().limit(4).toList()){
            var action=rows.addObject();action.put("step",child.command().operation().value());action.putNull("error");
            var ack=child.ack();action.put("result_observed",ack.isPresent()&&ack.orElseThrow().originalResultToken().isPresent());var projected=action.putObject("ack");
            JsonNode token=ack.isPresent()&&ack.orElseThrow().originalResultToken().isPresent()?StrictJson.parse(ack.orElseThrow().originalResultToken().orElseThrow().bytes()):com.fasterxml.jackson.databind.node.NullNode.getInstance();
            for(String key:List.of("step","status"))projected.set(key,scalar(token.get(key),false));
            JsonNode accepted=token.get("accepted");projected.set("accepted",accepted!=null&&accepted.isBoolean()?accepted:com.fasterxml.jackson.databind.node.NullNode.getInstance());
            if(ack.isPresent()&&ack.orElseThrow().requestId().length()<=192)projected.put("request_id",ack.orElseThrow().requestId());else projected.putNull("request_id");
            projected.set("native_request_id",scalar(token.get("native_request_id"),true));count++;
        }
        if(cleanupError.isPresent()&&count<4){var error=rows.addObject();error.put("step","exact-day-clock-cleanup");error.put("error",bounded(cleanupError.orElseThrow()));error.put("result_observed",false);var ack=error.putObject("ack");for(String key:List.of("step","accepted","status","request_id","native_request_id"))ack.putNull(key);count++;}
        row.put("omitted_count",Math.max(0,values.size()+(cleanupError.isPresent()?1:0)-count));return row;
    }
    private static JsonNode scalar(JsonNode value,boolean decimal){
        if(value==null||value.isNull())return com.fasterxml.jackson.databind.node.NullNode.getInstance();
        if(decimal){
            String exact=value.isIntegralNumber()?value.bigIntegerValue().toString():value.isTextual()?value.textValue():null;
            if(exact==null)return com.fasterxml.jackson.databind.node.NullNode.getInstance();
            try{return new com.fasterxml.jackson.databind.node.TextNode(new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(exact).decimal());}
            catch(IllegalArgumentException invalidRole){return com.fasterxml.jackson.databind.node.NullNode.getInstance();}
        }
        if(value.isBoolean()||value.isIntegralNumber())return value.deepCopy();
        if(value.isTextual())return new com.fasterxml.jackson.databind.node.TextNode(bounded(value.textValue()));return com.fasterxml.jackson.databind.node.NullNode.getInstance();
    }
    private static String bounded(String value){return value.length()<=192?value:value.substring(0,192);}
    private static void exact(ExactRef ref,byte[] actual){require(ref.bytes()==actual.length&&ref.sha256().equals(ActionCodec.sha256(actual)),"exact-day original bytes/SHA changed");}
}
