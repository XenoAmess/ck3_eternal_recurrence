package org.xar.ck3.control.application.action.council;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** Sole Council continuation issuer. Every potentially mutating STATUS is durably issued before its one write. */
public final class CouncilContinuationCoordinator {
    public static final String INPUT_SCHEMA = "xar.java-council-continuation-reducer-input/v1";
    public enum Boundary { ISSUED_COMMITTED, OUTCOME_ARCHIVED, OUTCOME_COMMITTED }
    @FunctionalInterface public interface FaultProbe { void after(Boundary boundary) throws IOException; }
    private record Runtime(ActionJournal journal, ActionPorts.OutcomeArchive archive, CouncilContinuationPorts.GuardPort guard,
            CouncilContinuationPorts.NativePort nativePort, CouncilContinuationPorts.Policy policy) { }
    private record Commit(ExactRef payload, ExactRef event,WriterContracts.Receipt receipt) { }
    private record View(DomainBodies.Available body, State state, List<Retained> records) { }
    @FunctionalInterface private interface Work<T> { T run() throws IOException; }
    private final Path originalLock;
    private final List<ExactRef> sources;
    private final Clock clock;
    private final FaultProbe faults;
    private final ThreadLocal<ContinuityStorePort.Session> active = new ThreadLocal<>();
    private Runtime runtime;
    private CouncilContinuationPorts.RecoveryAuthority recoveryAuthority;
    private boolean recoveryStarted;
    private final ThreadLocal<RecoveryOriginal> recovered = new ThreadLocal<>();

    public record SeatRead(String contractId,PlanningReadRequest request,String requestId,ExactRef prepared,
            Optional<ExactRef> outcome,Optional<ExactRef> known,Optional<String> failure) {
        public SeatRead {
            StrictJson.text(contractId);Objects.requireNonNull(request);StrictJson.text(requestId);Objects.requireNonNull(prepared);
            Objects.requireNonNull(outcome);Objects.requireNonNull(known);Objects.requireNonNull(failure);
            StrictJson.require(known.isEmpty()||outcome.isPresent()&&failure.isEmpty(),"known seat read needs its actual outcome and no failure");
        }
    }
    public record SeatCheckpoint(ExactRef tuple,List<SeatRead> reads) {
        public SeatCheckpoint {
            Objects.requireNonNull(tuple);reads=List.copyOf(reads);
            StrictJson.require(tuple.bytes()>0&&reads.size()<=MAX_ACTIVE_REQUESTS
                    &&reads.stream().map(SeatRead::requestId).distinct().count()==reads.size(),"finite distinct actual seat read ids required");
        }
    }
    private record SeatRow(Scope scope,ExactRef parent,Optional<ExactRef> previous,long sequence,String predecessor,SeatCheckpoint value) { }
    private static final String SEAT_CHECKPOINT_SCHEMA="xar.java-council-recovery-seat-checkpoint/v1";

    private SeatRow seatRow(ExactRef reference) {
        var row=StrictJson.object(StrictJson.parse(readMaterial(reference),MAX_BODY_BYTES),
                Set.of("schema","scope","parent","previous","sequence","predecessor","tuple","reads"));
        StrictJson.require(SEAT_CHECKPOINT_SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact seat checkpoint schema required");
        var subject=StrictJson.object(row.get("scope"),Set.of("parent_action_id","parent_body_sha256","original_attempt_request_id"));
        Scope scope=new Scope(StrictJson.text(subject.get("parent_action_id")),StrictJson.text(subject.get("parent_body_sha256")),StrictJson.text(subject.get("original_attempt_request_id")));
        StrictJson.require(row.get("reads").isArray(),"actual seat reads array required");var reads=new ArrayList<SeatRead>();
        for(var item:row.get("reads")) {
            var read=StrictJson.object(item,Set.of("contract_id","request","request_id","prepared","outcome","known","failure"));
            var argumentRef=ExactRef.fromJson(read.get("request").get("arguments_ref"));
            var arguments=org.xar.ck3.control.application.driver.DriverJson.object(readMaterial(argumentRef),PlanningReadRequest.MAX_ARGUMENT_BYTES);
            reads.add(new SeatRead(StrictJson.text(read.get("contract_id")),CommandOriginCodec.planningRequest(read.get("request"),arguments),
                    StrictJson.text(read.get("request_id")),ExactRef.fromJson(read.get("prepared")),seatRef(read.get("outcome")),seatRef(read.get("known")),
                    read.get("failure").isNull()?Optional.empty():Optional.of(StrictJson.text(read.get("failure")))));
        }
        return new SeatRow(scope,ExactRef.fromJson(row.get("parent")),seatRef(row.get("previous")),
                StrictJson.integer(row.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(row.get("predecessor")),
                new SeatCheckpoint(ExactRef.fromJson(row.get("tuple")),reads));
    }
    private static Optional<ExactRef> seatRef(JsonNode value) { return value.isNull()?Optional.empty():Optional.of(ExactRef.fromJson(value)); }
    private byte[] seatBody(SeatRow checkpoint) {
        var row=StrictJson.object().put("schema",SEAT_CHECKPOINT_SCHEMA);
        var scope=row.putObject("scope");scope.put("parent_action_id",checkpoint.scope().parentActionId()).put("parent_body_sha256",checkpoint.scope().parentBodySha256())
                .put("original_attempt_request_id",checkpoint.scope().originalAttemptRequestId());
        row.set("parent",checkpoint.parent().toJson());row.set("previous",checkpoint.previous().map(ExactRef::toJson).orElse(null));
        row.put("sequence",checkpoint.sequence()).put("predecessor",checkpoint.predecessor());row.set("tuple",checkpoint.value().tuple().toJson());
        var items=row.putArray("reads");for(var read:checkpoint.value().reads()) {
            var item=items.addObject().put("contract_id",read.contractId()).put("request_id",read.requestId());
            var arguments=preserveMaterial(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(read.request().arguments()));
            item.set("request",CommandOriginCodec.planningRequest(read.request(),arguments));item.set("prepared",read.prepared().toJson());
            item.set("outcome",read.outcome().map(ExactRef::toJson).orElse(null));item.set("known",read.known().map(ExactRef::toJson).orElse(null));
            if(read.failure().isPresent())item.put("failure",read.failure().orElseThrow());else item.putNull("failure");
        }
        return StrictJson.canonical(row,MAX_BODY_BYTES);
    }
    private GuardEvidence verifySeatTuple(ActionReceipt parent,ExactRef tuple) {
        var row=StrictJson.object(StrictJson.parse(readMaterial(tuple),MAX_BODY_BYTES),Set.of("schema","command_body_sha256","original_request_id","before","after","reconciliation_guard","provenance"));
        var attempt=ActionTransitions.attempt(parent.state()).orElseThrow();
        StrictJson.require("xar.java.council-current-seat-observation/v1".equals(StrictJson.text(row.get("schema")))
                &&parent.bodySha256().equals(StrictJson.text(row.get("command_body_sha256")))&&attempt.requestId().equals(StrictJson.text(row.get("original_request_id"))),
                "seat tuple crossed original command or attempt");
        GuardEvidence guard=CommandOriginCodec.guard(row.get("reconciliation_guard"));var identity=guard.origin().requireReconciliation();
        var proof=ObservationProvenanceCodec.decode(row.get("provenance"));
        StrictJson.require(proof instanceof ObservationProvenance.FreshSnapshotQuery
                &&identity.pending().actionId().equals(parent.command().actionId())&&identity.pending().bodySha256().equals(parent.bodySha256())
                &&identity.pending().requestId().equals(attempt.requestId())&&identity.pending().originalBefore().equals(parent.command().before())
                &&identity.pending().originalReceipt().equals(runtime().archive().receiptReferenceOf(parent))
                &&identity.source().equals(parent.command().source())&&identity.sessionId().equals(parent.command().sessionId())
                &&guard.operation().equals(parent.command().operation())&&guard.authorityId().equals(attempt.guard().authorityId()),"seat tuple is not the actual original Council observation DATA");
        proof.validate(identity.factual(),identity.nativeEvidence());identity.requireOriginalConnection(attempt.guard());
        var after=StrictJson.object(row.get("after"),Set.of("native_frame","driver_facts"));
        var before=StrictJson.object(row.get("before"),Set.of("native_frame","driver_facts"));
        var original=org.xar.ck3.control.application.effects.RootGuardEvidence.frameBasis(attempt.guard(),runtime().archive());
        StrictJson.require(ExactRef.fromJson(before.get("native_frame")).equals(original.nativeFrame())&&ExactRef.fromJson(before.get("driver_facts")).equals(original.driverFacts())
                &&ExactRef.fromJson(after.get("native_frame")).equals(identity.nativeEvidence())
                &&ExactRef.fromJson(after.get("driver_facts")).equals(identity.evidence().observationManifest()),"seat tuple lost its exact before/after frame basis");
        return guard;
    }
    private void verifySeatReads(ActionReceipt parent,SeatCheckpoint value) throws IOException {
        var tupleGuard=verifySeatTuple(parent,value.tuple());var identity=tupleGuard.origin().requireReconciliation();
        boolean statusAllowed=false;
        for(var read:value.reads()) {
            var request=read.request();String operation=request.operation().value();
            StrictJson.require(operation.equals("private-query-council-composition-candidates-v1")||operation.equals("private-council-application-main-status-v1"),"seat checkpoint cannot name another read operation");
            StrictJson.require(request.before().equals(identity.factual())&&request.source().equals(parent.command().source())&&request.sessionId().equals(parent.command().sessionId()),"seat read crossed exact captured frame/source/session");
            StrictJson.require(!read.requestId().equals(ActionTransitions.attempt(parent.state()).orElseThrow().requestId()),"seat read reused assignment request id");
            var prepared=runtime().archive().loadRequest(read.prepared());
            StrictJson.require(prepared.step().equals(operation)&&prepared.requiredCapability().isEmpty(),"seat prepared request changed its operation/capability");
            if(operation.equals("private-query-council-composition-candidates-v1"))StrictJson.require(!statusAllowed&&request.arguments().members().keySet().equals(Set.of("position_key")),"seat QUERY must be first and name its actual position");
            else StrictJson.require(statusAllowed&&request.arguments().members().isEmpty(),"seat STATUS requires its actual earlier known QUERY");
            if(read.outcome().isPresent())StrictJson.require(runtime().archive().load(read.outcome().orElseThrow()).requestId().equals(read.requestId()),"seat outcome crossed original read id");
            if(read.known().isPresent()) {
                var known=runtime().archive().loadRead(read.known().orElseThrow());
                StrictJson.require(known.request().equals(request)&&known.contractId().equals(read.contractId())&&known.requestId().equals(read.requestId())
                        &&known.original().equals(runtime().archive().load(read.outcome().orElseThrow()))
                        &&runtime().archive().readReferenceOf(known).equals(read.known().orElseThrow()),"known seat receipt lost exact request/outcome archive");
                org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(known,runtime().archive());statusAllowed=true;
            } else StrictJson.require(read==value.reads().getLast(),"an unfinished original seat read blocks all later request ids");
        }
    }
    private State verifySeatTransition(ContinuityStorePort.Session same,WriterContracts.Head head,State before,ExactRef reference) throws IOException {
        SeatRow row=seatRow(reference);var parent=runtime().archive().loadReceipt(row.parent());
        StrictJson.require(row.previous().equals(before.seatCheckpoint())&&row.sequence()==Math.addExact(head.state().sequence(),1)
                &&row.predecessor().equals(head.digest())&&canonical(head,row.scope().parentActionId()).equals(parent)
                &&parent.bodySha256().equals(row.scope().parentBodySha256())
                &&ActionTransitions.attempt(parent.state()).orElseThrow().requestId().equals(row.scope().originalAttemptRequestId()),"seat checkpoint lost its actual predecessor/original canonical scope");
        requireOriginal(parent,parent.command(),ActionTransitions.attempt(parent.state()).orElseThrow(),false);verifySeatReads(parent,row.value());
        if(row.previous().isPresent()) {
            var old=seatRow(row.previous().orElseThrow()).value();
            StrictJson.require(old.tuple().equals(row.value().tuple()),"pending seat tuple cannot be replaced");
            var a=old.reads();var b=row.value().reads();
            StrictJson.require(b.size()==a.size()||b.size()==a.size()+1,"one actual seat read transition required");
            for(int i=0;i<Math.max(0,a.size()-1);i++)StrictJson.require(a.get(i).equals(b.get(i)),"seat checkpoint changed an earlier actual read");
            if(!a.isEmpty()) {
                var prior=a.getLast();var next=b.get(a.size()-1);
                StrictJson.require(prior.contractId().equals(next.contractId())&&prior.request().equals(next.request())&&prior.requestId().equals(next.requestId())&&prior.prepared().equals(next.prepared()),"seat original prepared identity is immutable");
                if(prior.known().isPresent())StrictJson.require(prior.equals(next),"known original seat receipt is immutable");
                if(prior.outcome().isPresent()&&!prior.outcome().equals(next.outcome()))StrictJson.require(runtime().archive().load(prior.outcome().orElseThrow()) instanceof NativeActionPort.Unknown
                        &&next.outcome().isPresent()&&runtime().archive().load(next.outcome().orElseThrow()) instanceof NativeActionPort.AckReceived,"only actual original late ACK can resolve a seat UNKNOWN");
                if(b.size()>a.size())StrictJson.require(prior.known().isPresent(),"prepared or UNKNOWN original read is collect-only");
            }
        } else StrictJson.require(row.value().reads().isEmpty(),"seat tuple must be durably committed before query preparation");
        return CouncilContinuationReducer.seatCheckpoint(before,load(before),row.scope(),reference);
    }
    private Optional<SeatCheckpoint> readSeatHistory(ContinuityStorePort.Session same,WriterContracts.Head head,State current) throws IOException {
        var next=current.seatCheckpoint();Optional<SeatCheckpoint> answer=Optional.empty();var seen=new java.util.HashSet<ExactRef>();
        while(next.isPresent()) {
            var ref=next.orElseThrow();StrictJson.require(seen.add(ref)&&seen.size()<=MAX_ACTIVE_REQUESTS*4+1,"finite acyclic seat checkpoint history required");
            var row=seatRow(ref);if(answer.isEmpty())answer=Optional.of(row.value());
            var edge=same.readHistoricalTransition(same.capturePin(event(head,row.sequence()),MAX_BODY_BYTES));
            var original=same.requireHistoricalImport(DomainBodies.Slot.COUNCIL_CONTINUATION,row.sequence(),ContinuityJson.digest(edge.after().toJson()));
            var input=StrictJson.object(StrictJson.parse(original.request().producerInput(),MAX_BODY_BYTES),Set.of("schema","kind","record","seed_manifest","closed_scope"));
            StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(input.get("schema")))&&"SEAT_CHECKPOINT".equals(StrictJson.text(input.get("kind")))
                    &&ExactRef.fromJson(input.get("record")).equals(ref)&&input.get("seed_manifest").isNull()&&input.get("closed_scope").isNull(),"actual canonical import does not bind this seat checkpoint");
            var previous=DomainBodies.reference(original.predecessor().state(),DomainBodies.Slot.COUNCIL_CONTINUATION).orElseThrow();
            var before=CouncilContinuationCodec.decodeState(readMaterial(previous.payload()));
            var expected=verifySeatTransition(same,original.predecessor(),before,ref);
            StrictJson.require(Arrays.equals(CouncilContinuationCodec.encodeState(expected),readMaterial(original.body().payload())),"canonical seat checkpoint did not replay its complete exact state");
            next=row.previous();
        }
        return answer;
    }
    private Commit checkpointSeat(RecoveryOriginal token,SeatCheckpoint value) throws IOException {
        token.requireCurrent();return scoped(token.same,()->{
            var head=token.same.head();if(token.seatHead!=null)StrictJson.require(token.seatHead.digest().equals(head.digest()),"unrelated canonical head drift cannot become a seat checkpoint");
            var view=view(token.same);Scope scope=new Scope(token.command().actionId(),token.parent.bodySha256(),token.attempt.requestId());
            var row=new SeatRow(scope,runtime().archive().receiptReferenceOf(token.parent),view.state().seatCheckpoint(),Math.addExact(head.state().sequence(),1),head.digest(),value);
            ExactRef ref=preserveMaterial(seatBody(row));var expected=verifySeatTransition(token.same,head,view.state(),ref);
            var refs=new ArrayList<ExactRef>(List.of(ref,value.tuple(),row.parent(),view.body().reference().payload()));
            for(var read:value.reads()){refs.add(read.prepared());read.outcome().ifPresent(refs::add);read.known().ifPresent(refs::add);}
            var commit=commit(token.same,expected,input("SEAT_CHECKPOINT",Optional.of(ref),Optional.empty(),Optional.empty()),refs);
            token.seatHead=token.same.head();return commit;
        });
    }
    private void seatReadUpdate(RecoveryOriginal token,ReadContract<?> contract,PlanningReadRequest request,String id,NativeRequest prepared,
            Optional<NativeActionPort.DispatchOutcome> outcome,Optional<PlanningReadReceipt> known,Optional<String> failure) throws IOException {
        var value=token.seatCheckpoint().orElseThrow(()->new IOException("actual same-capture tuple is not durably checkpointed"));
        var reads=new ArrayList<>(value.reads());int index=-1;for(int i=0;i<reads.size();i++)if(reads.get(i).requestId().equals(id))index=i;
        ExactRef preparedRef=runtime().archive().preserveRequest(prepared);Optional<ExactRef> outcomeRef=outcome.map(runtime().archive()::preserve);
        Optional<ExactRef> knownRef=known.map(runtime().archive()::preserveRead);
        if(index>=0) {var old=reads.get(index);if(outcomeRef.isEmpty())outcomeRef=old.outcome();if(knownRef.isEmpty())knownRef=old.known();
            reads.set(index,new SeatRead(contract.contractId(),request,id,preparedRef,outcomeRef,knownRef,failure));}
        else {StrictJson.require(outcome.isEmpty()&&known.isEmpty(),"original seat outcome requires durable PREPARED navigation");
            reads.add(new SeatRead(contract.contractId(),request,id,preparedRef,outcomeRef,knownRef,failure));}
        checkpointSeat(token,new SeatCheckpoint(value.tuple(),reads));
    }
    public void verifyCanonicalSeatCheckpoint(ContinuityStorePort.Session same,WriterContracts.Head head,Scope scope,ExactRef tuple,List<ExactRef> knownReadRefs) throws IOException {
        scoped(same,()->{
            StrictJson.require(same.head().digest().equals(head.digest()),"seat verifier requires exact actual canonical head");
            var state=view(same).state();Optional<SeatCheckpoint> found=Optional.empty();var visited=new java.util.HashSet<ExactRef>();
            while(true) {
                if(state.active().filter(scope::equals).isPresent()) {found=readSeatHistory(same,head,state);break;}
                if(state.completedScopeChain().isEmpty())break;var closure=state.completedScopeChain().orElseThrow();
                StrictJson.require(visited.add(closure)&&visited.size()<=MAX_ACTIVE_REQUESTS,"finite canonical retired scopes required");
                var closed=StrictJson.object(StrictJson.parse(readMaterial(closure),MAX_BODY_BYTES),Set.of("schema","previous_state","settled_parent"));
                StrictJson.require("xar.java-council-closed-scope/v1".equals(StrictJson.text(closed.get("schema"))),"actual closed Council scope archive required");
                var parent=runtime().archive().loadReceipt(ExactRef.fromJson(closed.get("settled_parent")));
                ContinuityActionJournal.requireHistoricalReceipt(head.state(),parent,runtime().archive());
                StrictJson.require(parent.settled(),"only truly settled parent may archive a seat scope");
                state=CouncilContinuationCodec.decodeState(readMaterial(ExactRef.fromJson(closed.get("previous_state"))));
            }
            var checkpoint=found.orElseThrow(()->new IOException("canonical seat checkpoint absent for this original scope"));
            StrictJson.require(checkpoint.tuple().equals(tuple)&&!checkpoint.reads().isEmpty()&&checkpoint.reads().stream().allMatch(read->read.known().isPresent()&&read.failure().isEmpty())
                    &&checkpoint.reads().stream().map(read->read.known().orElseThrow()).toList().equals(List.copyOf(knownReadRefs)),"seat evidence differs from complete ordered canonical known originals");
            StrictJson.require(same.head().digest().equals(head.digest()),"canonical head changed during seat DATA replay");return null;
        });
    }

    /** Opaque live role for one unchanged original; only this coordinator can issue it. */
    public static final class RecoveryOriginal {
        private final CouncilContinuationCoordinator issuer;
        private final ContinuityStorePort.Session same;
        private final ActionReceipt parent;
        private final ActionState.Attempt attempt;
        private final NativeActionPort.AckReceived ack;
        private final Instant deadline;
        private final Thread owner = Thread.currentThread();
        private boolean open = true;
        private GuardEvidence qualifiedGuard;
        private GuardEvidence observationGuard;
        private ObservationProvenance observationProvenance;
        private RecoveryOriginal(CouncilContinuationCoordinator issuer, ContinuityStorePort.Session same,
                ActionReceipt parent, ActionState.Attempt attempt, NativeActionPort.AckReceived ack, Instant deadline) {
            this.issuer=issuer; this.same=same; this.parent=parent; this.attempt=attempt; this.ack=ack; this.deadline=deadline;
        }
        public ActionCommand command() { return parent.command(); }
        public ActionState.Attempt attempt() { return attempt; }
        public NativeActionPort.AckReceived originalAck() { return ack; }
        public ActionReceipt originalParent() { return parent; }
        /** Deep physical source capture only; callers must be outside Native transport locks. */
        public GuardEvidence captureObservationGuard() throws IOException {
            issuer.recoveredGuard(this);
            var captured=issuer.recoverySource().captureRecoveredObservation(same,this,deadline);
            var guard=captured.guard();
            requireCurrent();
            StrictJson.require(guard.origin() instanceof CommandOrigin.Reconciliation,"actual dedicated Council reconciliation guard required");
            var identity=guard.origin().requireReconciliation();
            StrictJson.require(identity.pending().actionId().equals(command().actionId())
                    &&identity.pending().bodySha256().equals(parent.bodySha256())
                    &&identity.pending().requestId().equals(attempt.requestId())
                    &&identity.pending().originalBefore().equals(command().before())
                    &&identity.pending().originalReceipt().equals(issuer.runtime().archive().receiptReferenceOf(parent))
                    &&identity.source().equals(command().source())&&identity.sessionId().equals(command().sessionId())
                    &&guard.source().equals(identity.source())&&guard.sessionId().equals(identity.sessionId())
                    &&guard.connectionGeneration().equals(identity.connectionGeneration())
                    &&guard.nativeEvidence().equals(identity.nativeEvidence())&&guard.capabilityEvidence().equals(identity.capabilityEvidence())
                    &&guard.operation().equals(command().operation())&&guard.authorityId().equals(attempt.guard().authorityId())
                    &&!guard.supportingEvidence().isEmpty()&&!issuer.clock.instant().isAfter(guard.validUntil()),
                    "recovered Council observation crossed its real original/source/frame custody");
            identity.requireOriginalConnection(attempt.guard());
            captured.provenance().validate(identity.factual(),identity.nativeEvidence());
            observationGuard=guard;observationProvenance=captured.provenance();return guard;
        }
        /** Exact already captured DATA; no second physical occurrence is sampled here. */
        public GuardEvidence observationGuard() throws IOException {
            requireCurrent();StrictJson.require(observationGuard!=null&&!issuer.clock.instant().isAfter(observationGuard.validUntil()),
                    "actual recovered Council observation guard is absent or expired");
            return observationGuard;
        }
        public ObservationProvenance observationProvenance() throws IOException {
            var guard=observationGuard();
            StrictJson.require(observationProvenance!=null,"actual recovered observation provenance is absent");
            observationProvenance.validate(guard.origin().requireReconciliation().factual(),guard.nativeEvidence());
            return observationProvenance;
        }
        private WriterContracts.Head seatHead;
        public Optional<SeatCheckpoint> seatCheckpoint() throws IOException {
            requireCurrent();return issuer.scoped(same,()->issuer.readSeatHistory(same,same.head(),issuer.view(same).state()));
        }
        public WriterContracts.Receipt checkpointSeatTuple(ExactRef actualSameCaptureTuple) throws IOException {
            requireCurrent();var guard=issuer.verifySeatTuple(parent,actualSameCaptureTuple);
            StrictJson.require(observationGuard().equals(guard),"only this private role's actual same-capture tuple can begin live checkpointing");
            var tuple=StrictJson.object(StrictJson.parse(issuer.readMaterial(actualSameCaptureTuple),MAX_BODY_BYTES),Set.of("schema","command_body_sha256","original_request_id","before","after","reconciliation_guard","provenance"));
            StrictJson.require(ObservationProvenanceCodec.decode(tuple.get("provenance")).equals(observationProvenance()),"tuple lost this same actual FreshQuery proof");
            var old=seatCheckpoint();
            StrictJson.require(old.isEmpty()||old.orElseThrow().tuple().equals(actualSameCaptureTuple),"old prepared/known tuple is immutable; reopen its actual checkpoint instead");
            return issuer.checkpointSeat(this,new SeatCheckpoint(actualSameCaptureTuple,old.map(SeatCheckpoint::reads).orElse(List.of()))).receipt();
        }
        public WriterContracts.Head seatCheckpointHead() throws IOException {
            requireCurrent();var actual=same.head();if(seatHead==null)seatHead=actual;
            StrictJson.require(actual.digest().equals(seatHead.digest())&&actual.documents().equals(seatHead.documents())
                    &&actual.absent().equals(seatHead.absent())&&actual.indexRepairs().equals(seatHead.indexRepairs()),"unrelated writer drift is not this role's committed seat checkpoint");
            return actual;
        }
        public PlanningReadCoordinator.ReadLifecycleObserver seatReadLifecycle() {
            return new PlanningReadCoordinator.ReadLifecycleObserver() {
                private void require(ContinuityStorePort.Session actual) throws IOException {
                    StrictJson.require(actual==same,"seat read observer escaped its actual borrowed writer");requireCurrent();
                }
                private SeatRead original(String id) throws IOException {
                    return seatCheckpoint().orElseThrow().reads().stream().filter(read->read.requestId().equals(id)).findFirst()
                            .orElseThrow(()->new IOException("actual original seat read was not durably prepared"));
                }
                @Override public void prepared(ContinuityStorePort.Session actual,ReadContract<?> contract,PlanningReadRequest request,String id,NativeRequest prepared)throws IOException {
                    require(actual);StrictJson.require(contract.prepare(request,id).equals(prepared),"seat observer changed actual installed preparation");
                    issuer.seatReadUpdate(RecoveryOriginal.this,contract,request,id,prepared,Optional.empty(),Optional.empty(),Optional.empty());
                }
                @Override public void received(ContinuityStorePort.Session actual,ReadContract<?> contract,PlanningReadRequest request,String id,NativeActionPort.DispatchOutcome outcome)throws IOException {
                    require(actual);var old=original(id);
                    issuer.seatReadUpdate(RecoveryOriginal.this,contract,request,id,issuer.runtime().archive().loadRequest(old.prepared()),Optional.of(outcome),Optional.empty(),Optional.empty());
                }
                @Override public void known(ContinuityStorePort.Session actual,ReadContract<?> contract,PlanningReadResult.Known<?> known)throws IOException {
                    require(actual);var read=known.receipt();var old=original(read.requestId());
                    StrictJson.require(known.originalReceipt().equals(issuer.runtime().archive().readReferenceOf(read)),"seat Known must retain its actual original receipt ref");
                    issuer.seatReadUpdate(RecoveryOriginal.this,contract,read.request(),read.requestId(),issuer.runtime().archive().loadRequest(old.prepared()),Optional.of(read.original()),Optional.of(read),Optional.empty());
                }
                @Override public void failed(ContinuityStorePort.Session actual,ReadContract<?> contract,PlanningReadRequest request,Optional<NativeActionPort.DispatchOutcome> outcome,String reason)throws IOException {
                    require(actual);var all=seatCheckpoint().orElseThrow().reads();
                    var old=all.stream().filter(read->read.contractId().equals(contract.contractId())&&read.request().equals(request)
                            &&outcome.map(value->value.requestId().equals(read.requestId())).orElse(true)).reduce((a,b)->b)
                            .orElseThrow(()->new IOException("failed seat read has no actual PREPARED id; no UNKNOWN is invented"));
                    issuer.seatReadUpdate(RecoveryOriginal.this,contract,request,old.requestId(),issuer.runtime().archive().loadRequest(old.prepared()),outcome,Optional.empty(),Optional.of(reason));
                }
            };
        }

        public void requireCurrent() throws IOException { issuer.requireRecoveredRetained(this); }
    }
    /** One actual source observer result; construction is private and consumption remains session/action scoped. */
    public static final class RecoveryCompletion {
        private final CouncilContinuationCoordinator issuer;
        private final ContinuityStorePort.Session same;
        private final ActionReceipt parent;
        private final ActionPorts.PostconditionResult result;
        private final Instant deadline;
        private final Thread owner = Thread.currentThread();
        private final java.util.concurrent.atomic.AtomicBoolean consumed = new java.util.concurrent.atomic.AtomicBoolean();
        private RecoveryCompletion(CouncilContinuationCoordinator issuer, ContinuityStorePort.Session same,
                ActionReceipt parent, ActionPorts.PostconditionResult result, Instant deadline) {
            this.issuer=issuer;this.same=same;this.parent=parent;this.result=result;this.deadline=deadline;
        }
        public ActionPorts.PostconditionResult consume(ContinuityStorePort.Session actual, ActionReceipt original) throws IOException {
            StrictJson.require(owner==Thread.currentThread() && actual==same && parent.equals(original)
                    && ActionScope.currentActionId().filter(parent.command().actionId()::equals).isPresent()
                    && issuer.clock.instant().isBefore(deadline), "recovered Council completion escaped its exact live original");
            issuer.scoped(same,()->{
                StrictJson.require(issuer.canonical(same.head(),parent.command().actionId()).equals(parent),"recovered Council original changed before terminal consumption");
                var guard=issuer.recoverySource().currentRecovered(same,same.head(),parent,deadline);
                issuer.verifyRecoveredFresh(parent,ActionTransitions.attempt(parent.state()).orElseThrow(),guard,deadline);
                return null;
            });
            StrictJson.require(consumed.compareAndSet(false,true),"recovered Council completion already consumed");
            return result;
        }
    }
    private static final class RecoveryInterrupted extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final InterruptedException original;
        private RecoveryInterrupted(InterruptedException original) { super(original);this.original=original; }
    }
    public synchronized void bindRecoveryAuthority(CouncilContinuationPorts.RecoveryAuthority actual) {
        StrictJson.require(recoveryAuthority==null && !recoveryStarted,"actual Council recovery source binds once before recovery use");
        recoveryAuthority=Objects.requireNonNull(actual);
    }
    private synchronized CouncilContinuationPorts.RecoveryAuthority recoverySource() {
        recoveryStarted=true;
        return Objects.requireNonNull(recoveryAuthority,"actual Council recovery source is not installed");
    }
    public RecoveryCompletion observeRecoveredOriginal(ContinuityStorePort.Session same,String actionId,Instant callerDeadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(callerDeadline);
        try { return scoped(same,()->{
            StrictJson.require(recovered.get()==null,"recovered Council scope cannot nest");
            var parent=canonical(same.head(),actionId);
            var all=ContinuityActionJournal.receipts(same.head().state(),runtime().archive().withSession(same));
            StrictJson.require(org.xar.ck3.control.application.session.ContinuityBatchJournal.readOnlyPositiveAckCouncilRecoveryRoot(all)
                    .filter(parent::equals).isPresent(),"only the unique exact original positive-ACK Council UNKNOWN may recover");
            var attempt=ActionTransitions.attempt(parent.state()).orElseThrow();
            var ack=(NativeActionPort.AckReceived)ActionTransitions.dispatch(parent.state()).orElseThrow();
            var bound=ActionObservationWindow.deadline(parent.command());
            var deadline=callerDeadline.isBefore(bound)?callerDeadline:bound;
            var token=new RecoveryOriginal(this,same,parent,attempt,ack,deadline);
            recovered.set(token);
            try {
                recoveredGuard(token);
                ActionPorts.PostconditionResult result;
                try { result=Objects.requireNonNull(recoverySource().observeRecovered(same,parent,attempt,ack,deadline)); }
                catch(InterruptedException interrupted){throw new RecoveryInterrupted(interrupted);}
                recoveredGuard(token);
                StrictJson.require(result instanceof ActionPorts.Pending || result instanceof ActionPorts.EffectObserved
                        || result instanceof ActionPorts.RejectionObserved,"Council recovery cannot issue unrelated terminal authority");
                return new RecoveryCompletion(this,same,parent,result,deadline);
            } finally {token.open=false;recovered.remove();}
        }); } catch(RecoveryInterrupted interrupted){throw interrupted.original;}
    }
    private RecoveryOriginal recovery(ContinuityStorePort.Session same,ActionReceipt parent) throws IOException {
        var token=recovered.get();
        if(token==null)return null;
        StrictJson.require(token.same==same && token.parent.equals(parent),"recovered Council crossed its exact original/session");
        return token;
    }
    public RecoveryOriginal currentRecoveryOriginal(ContinuityStorePort.Session same,String originalActionId) throws IOException {
        var token=recovered.get();
        StrictJson.require(token!=null && token.same==same && token.command().actionId().equals(originalActionId),
                "no actual active recovered Council original for this session/action");
        token.requireCurrent();return token;
    }
    /** No Root/readiness callback: this also runs under the Native transport monitor. */
    private void requireRecoveredRetained(RecoveryOriginal token) throws IOException {
        requireRecoveredScope(token);
        StrictJson.require(token.qualifiedGuard!=null && !clock.instant().isAfter(token.qualifiedGuard.validUntil()),
                "recovered Council source-qualified lease expired");
    }
    private void requireRecoveredScope(RecoveryOriginal token) throws IOException {
        requireSession(token.same);
        StrictJson.require(token.issuer==this && recovered.get()==token && token.open && token.owner==Thread.currentThread()
                && ActionScope.currentActionId().filter(token.command().actionId()::equals).isPresent()
                && clock.instant().isBefore(token.deadline)
                && canonical(token.same.head(),token.command().actionId()).equals(token.parent),"recovered Council source is closed, stale or changed");
    }
    /** Source qualification runs before issuing/validating a query, outside the transport monitor. */
    private GuardEvidence recoveredGuard(RecoveryOriginal token) throws IOException {
        requireRecoveredScope(token);
        var guard=recoverySource().currentRecovered(token.same,token.same.head(),token.parent,token.deadline);
        verifyRecoveredFresh(token.parent,token.attempt,guard,token.deadline);
        token.qualifiedGuard=guard;
        return guard;
    }
    private void verifyRecoveredFresh(ActionReceipt parent,ActionState.Attempt original,GuardEvidence guard,Instant deadline) {
        var old=original.guard(); var before=old.observed();var current=guard.observed();var now=clock.instant();
        StrictJson.require(parent.state() instanceof ActionState.Unknown && guard.origin() instanceof CommandOrigin.Gameplay
                && before.machineId().equals(current.machineId()) && before.game().equals(current.game())
                && before.frame().episodeRunId().equals(current.frame().episodeRunId())
                && before.frame().identity().player().equals(current.frame().identity().player())
                && current.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision())>=0
                && (!guard.connectionGeneration().equals(old.connectionGeneration())
                    || current.frame().revision().compareTo(before.frame().revision())>=0)
                && current.frame().identity().dateRaw().compareTo(before.frame().identity().dateRaw())>=0
                && guard.source().equals(old.source()) && guard.sessionId().equals(old.sessionId())
                && guard.authorityId().equals(old.authorityId()) && guard.operation().equals(parent.command().operation())
                && !guard.supportingEvidence().isEmpty() && now.isBefore(deadline)
                && now.isBefore(ActionObservationWindow.deadline(parent.command()))
                && !guard.observedAt().isAfter(now) && !now.isAfter(guard.validUntil()),
                "recovered Council source changed original identity, chronology or bounded observation authority");
    }

    public CouncilContinuationCoordinator(Path originalWriterLock, List<ExactRef> exactProducerSources, Clock clock) {
        this(originalWriterLock, exactProducerSources, clock, boundary -> { });
    }
    public CouncilContinuationCoordinator(Path originalWriterLock, List<ExactRef> exactProducerSources, Clock clock, FaultProbe faults) {
        originalLock = Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize(); sources = List.copyOf(exactProducerSources);
        StrictJson.require(!sources.isEmpty() && sources.size() <= 64, "actual fixed continuation producer/reducer source closure required");
        this.clock = Objects.requireNonNull(clock); this.faults = Objects.requireNonNull(faults);
    }
    /** One bootstrap binding, before Root freezes/uses the runtime. Rebinding an installed graph is forbidden. */
    public synchronized void bind(ActionJournal journal, ActionPorts.OutcomeArchive archive, CouncilContinuationPorts.GuardPort guard,
            CouncilContinuationPorts.NativePort nativePort, CouncilContinuationPorts.Policy policy) {
        StrictJson.require(runtime == null, "continuation runtime already bound");
        runtime = new Runtime(Objects.requireNonNull(journal), Objects.requireNonNull(archive), Objects.requireNonNull(guard), Objects.requireNonNull(nativePort), Objects.requireNonNull(policy));
    }
    private synchronized Runtime runtime() { return Objects.requireNonNull(runtime, "actual Root continuation runtime is not bound"); }

    public CouncilContinuationReceipt continueOnce(ContinuityStorePort.Session same, ActionCommand parent, ActionState.Attempt original,
            Stage stage, Instant callerDeadline) throws IOException {
        return scoped(same, () -> runtime().journal().locked(same, locked -> {
            try { return issueAndSend(same, locked, parent, original, stage, callerDeadline); }
            catch (IOException failure) { throw new UncheckedIOException(failure); }
        }));
    }
    private CouncilContinuationReceipt issueAndSend(ContinuityStorePort.Session same, ActionJournal.LockedJournal locked,
            ActionCommand parent, ActionState.Attempt original, Stage stage, Instant callerDeadline) throws IOException {
        Objects.requireNonNull(stage); Objects.requireNonNull(callerDeadline); Runtime r = runtime();
        ActionReceipt actual = canonical(locked.head(), parent.actionId());
        RecoveryOriginal recovery = recovery(same,actual);
        requireOriginal(actual,parent,original,recovery==null);
        if(recovery!=null)recovery.requireCurrent();
        StrictJson.require(ActionScope.currentActionId().filter(parent.actionId()::equals).isPresent(), "continuation requires the original coordinator-owned parent scope");
        Instant observationDeadline = ActionObservationWindow.deadline(parent);
        Instant deadline = callerDeadline.isBefore(observationDeadline) ? callerDeadline : observationDeadline;
        StrictJson.require(clock.instant().isBefore(deadline), "continuation caller deadline already expired");
        View view = view(same);
        Scope scope = new Scope(parent.actionId(), actual.bodySha256(), original.requestId());
        if (view.state().active().isPresent() && !view.state().active().orElseThrow().equals(scope)) view = rotate(same, view);
        StrictJson.require(view.records().stream().allMatch(row -> row.status() == Status.ACK), "original ISSUED or UNKNOWN continuation blocks all further request IDs");
        GuardEvidence guard;
        if(recovery==null){guard=r.guard().current(same,locked.head(),actual,deadline);verifyFresh(actual,original,guard,deadline);}
        else {guard=recoveredGuard(recovery);verifyRecoveredFresh(actual,original,guard,deadline);}
        List<ExactRef> supporting = List.copyOf(r.policy().prepareEvidence(same, locked.head(), actual, stage, view.records(), r.archive()));
        String id = RequestIds.nextRead(); NativeRequest prepared = new NativeRequest(stage.step(), Optional.empty(), new RawJson(new byte[] {'{', '}'}));
        ExactRef preparedRef = r.archive().preserveRequest(prepared), parentRef = r.archive().preserveReceipt(actual);
        Request request = new Request(scope, id, stage, parentRef, preparedRef, guard, clock.instant(), deadline,
                Math.addExact(same.head().state().sequence(), 1), supporting);
        Retained issued = preserve(new Entry(request, Status.ISSUED, Optional.empty(), Optional.empty(), 0));
        State issuedState = CouncilContinuationReducer.issue(view.state(), view.records(), issued);
        Commit committed = commit(same, issuedState, input("ISSUE", Optional.of(issued.reference()), Optional.empty(), Optional.empty()), evidence(view, issued));
        StrictJson.require(same.head().state().sequence() == request.issuedSequence(), "actual issued canonical sequence differs from the original request");
        IssuedCustody custody = new IssuedCustody(issued.reference(), committed.payload(), committed.event());
        faults.after(Boundary.ISSUED_COMMITTED);
        String issuedHead = same.head().digest();
        CouncilContinuationPermit permit = new CouncilContinuationPermit(request, prepared, () -> {
            try {
                requireSession(same); View current = view(same);
                StrictJson.require(current.body().reference().payload().equals(custody.domainPayload()) && same.head().digest().equals(issuedHead)
                        && current.records().getLast().equals(issued), "durable original ISSUED state changed before the one native write");
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }, clock, Optional.ofNullable(recovery));
        NativeActionPort.DispatchOutcome outcome;
        try { outcome = Objects.requireNonNull(r.nativePort().submit(permit, prepared, deadline)); }
        catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); outcome = new NativeActionPort.Unknown(id, "continuation interrupted after durable ISSUED; collect original only", new byte[0], Optional.empty());
        } catch (IOException | RuntimeException failure) {
            outcome = new NativeActionPort.Unknown(id, "continuation result unavailable after durable ISSUED: " + failure.getClass().getName(), new byte[0], Optional.empty());
        } finally { permit.close(); }
        if (!outcome.requestId().equals(id)) outcome = new NativeActionPort.Unknown(id, "continuation returned another request ID; no replay", new byte[0], Optional.empty());
        return recordOutcome(same, issued, custody, outcome, false);
    }

    /** Collects the already issued exact request ID. No permit, fresh nonce or submission port is available here. */
    public CouncilContinuationReceipt recover(ContinuityStorePort.Session same, String requestId, Instant deadline) throws IOException {
        return scoped(same, () -> runtime().journal().locked(same, locked -> {
            try {
                View current = view(same); Retained previous = current.records().stream().filter(row -> row.request().requestId().equals(requestId)).findFirst().orElseThrow(() -> new IllegalArgumentException("original continuation request absent"));
                if (previous.status() == Status.ACK) return retainedReceipt(same, previous);
                IssuedCustody custody = previous.entry().issued().orElseGet(() -> new IssuedCustody(previous.reference(), current.body().reference().payload(), event(locked.head(), previous.request().issuedSequence())));
                Optional<NativeActionPort.AckReceived> late;
                try { late = runtime().nativePort().collectOriginalOutcome(requestId, deadline); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); late = Optional.empty(); }
                catch (IOException failure) { late = Optional.empty(); }
                if (previous.status() == Status.UNKNOWN && (late.isEmpty() || late.orElseThrow().outbound().isEmpty())) return retainedReceipt(same, previous);
                NativeActionPort.DispatchOutcome outcome = late.<NativeActionPort.DispatchOutcome>map(value -> value).orElseGet(() ->
                        new NativeActionPort.Unknown(requestId, "restored ISSUED has no original terminal result; collect only, never replay", new byte[0], Optional.empty()));
                return recordOutcome(same, previous, custody, outcome, true);
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }));
    }
    public List<Retained> retained(ContinuityStorePort.Session same) throws IOException { return scoped(same, () -> view(same).records()); }

    /** Re-opens exact immutable ledger events and their actual producer inputs; decoding a row alone grants nothing. */
    public void verifyCanonicalChain(ContinuityStorePort.Session same, WriterContracts.Head actualHead,
            List<CouncilContinuationReceipt> receipts) throws IOException {
        scoped(same, () -> {
            WriterContracts.Head current = same.head();
            StrictJson.require(current.digest().equals(actualHead.digest()) && current.documents().equals(actualHead.documents())
                    && current.absent().equals(actualHead.absent()) && current.indexRepairs().equals(actualHead.indexRepairs()), "continuation verifier needs the exact current original writer Head");
            StrictJson.require(!receipts.isEmpty() && receipts.size() <= MAX_ACTIVE_REQUESTS, "complete bounded continuation receipt chain required");
            Set<String> seen = new java.util.HashSet<>(); Scope scope = receipts.getFirst().request().scope();
            for (CouncilContinuationReceipt receipt : List.copyOf(receipts)) {
                StrictJson.require(scope.equals(receipt.request().scope()) && seen.add(receipt.request().requestId()), "continuation chain repeats or crosses an original action");
                Retained issued = retained(receipt.issued().record()), result = retained(receipt.latestRecord());
                StrictJson.require(issued.status() == Status.ISSUED && issued.request().equals(receipt.request())
                        && result.request().equals(receipt.request()) && result.status() == receipt.status()
                        && result.entry().issued().filter(receipt.issued()::equals).isPresent(), "receipt does not retain the original immutable issued/result rows");
                NativeActionPort.DispatchOutcome original = runtime().archive().load(result.entry().outcome().orElseThrow());
                StrictJson.require(receipt.outcome().filter(original::equals).isPresent() && original.requestId().equals(receipt.request().requestId()), "receipt original dispatch changed");
                verifyCanonicalEvent(same, actualHead, receipt.issued().event(), receipt.request().issuedSequence(), receipt.issued().domainPayload(),
                        receipt.issued().record(), Set.of("ISSUE"));
                verifyCanonicalEvent(same, actualHead, receipt.resultEvent(), result.entry().resultSequence(), receipt.resultDomainPayload(),
                        receipt.latestRecord(), Set.of("OUTCOME", "COLLECT"));
                var parent = runtime().archive().loadReceipt(receipt.request().originalParentReceipt());
                StrictJson.require(parent.command().actionId().equals(scope.parentActionId()) && parent.bodySha256().equals(scope.parentBodySha256())
                        && ActionTransitions.attempt(parent.state()).filter(attempt -> attempt.requestId().equals(scope.originalAttemptRequestId())).isPresent(), "continuation chain crossed its original action/attempt");
                verifyRequest(receipt.request());
            }
            return null;
        });
    }
    private void verifyCanonicalEvent(ContinuityStorePort.Session same, WriterContracts.Head head, ExactRef reference, long sequence,
            ExactRef payload, ExactRef record, Set<String> kinds) throws IOException {
        WriterContracts.Pin pin = same.capturePin(reference, MAX_BODY_BYTES);
        StrictJson.require(head.documents().contains(pin) && reference.equals(event(head, sequence)), "continuation event is not an actual immutable canonical pin");
        byte[] raw = same.readPinned(pin, MAX_BODY_BYTES); same.verifyPin(pin);
        ObjectNode event = StrictJson.object(StrictJson.parse(raw, MAX_BODY_BYTES), Set.of("sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"));
        StrictJson.require(StrictJson.integer(event.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER) == sequence
                && DomainBodies.IMPORT_KIND.equals(StrictJson.text(event.get("kind"))), "continuation event has another sequence/kind");
        ObjectNode details = StrictJson.object(event.get("details"), Set.of("evidence_id", "machine_id", "source", "domain_body", "precondition_digest"));
        StrictJson.require(StrictJson.text(details.get("machine_id")).equals(head.state().machineId()), "continuation event crossed machines");
        DomainBodies.BodyRef body = DomainBodies.BodyRef.fromJson(details.get("domain_body"));
        StrictJson.require(body.slot() == DomainBodies.Slot.COUNCIL_CONTINUATION && body.contractSchema().equals(SCHEMA)
                && body.payload().equals(payload), "continuation event references another domain/body");
        ObjectNode source = StrictJson.object(details.get("source"), Set.of("original_body", "producer_input", "producer_sources", "evidence"));
        StrictJson.require(source.get("producer_sources").isArray()
                && source.get("producer_sources").size() == body.producerSources().size(), "continuation event lost its exact historical producer closure");
        var historicalSources = new ArrayList<ExactRef>();
        for (var producer : source.get("producer_sources")) historicalSources.add(ExactRef.fromJson(producer));
        StrictJson.require(body.producerSources().equals(historicalSources), "continuation event producer closure differs from its original body DATA");
        StrictJson.require(ExactRef.fromJson(source.get("original_body")).equals(payload), "continuation publication lost its original full body");
        ObjectNode input = StrictJson.object(StrictJson.parse(readMaterial(ExactRef.fromJson(source.get("producer_input"))), MAX_BODY_BYTES), Set.of("schema", "kind", "record", "seed_manifest", "closed_scope"));
        StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(input.get("schema"))) && kinds.contains(StrictJson.text(input.get("kind")))
                && ExactRef.fromJson(input.get("record")).equals(record) && input.get("seed_manifest").isNull() && input.get("closed_scope").isNull(), "canonical continuation producer input does not bind its exact issued/result row");
        State state = CouncilContinuationCodec.decodeState(readMaterial(payload)); StrictJson.require(state.records().contains(record), "canonical continuation body omitted its exact row");
        ContinuityState after = ContinuityState.fromJson(event.get("after"), head.state().machineId());
        StrictJson.require(after.sequence() == sequence && DomainBodies.reference(after, DomainBodies.Slot.COUNCIL_CONTINUATION).filter(body::equals).isPresent(), "canonical event after-state lost the original continuation body");
        var request = new WriterContracts.Request(DomainBodies.IMPORT_KIND, ContinuityJson.canonical(details), List.of());
        StrictJson.require(request.identity().equals(StrictJson.text(event.get("identity"))), "canonical continuation event identity differs");
    }

    private CouncilContinuationReceipt recordOutcome(ContinuityStorePort.Session same, Retained previous, IssuedCustody custody,
            NativeActionPort.DispatchOutcome original, boolean collectedLate) throws IOException {
        Runtime r = runtime(); ExactRef originalRef = r.archive().preserve(original);
        StrictJson.require(original.equals(r.archive().load(originalRef)), "actual continuation outcome archive changed");
        faults.after(Boundary.OUTCOME_ARCHIVED);
        Status status = original instanceof NativeActionPort.AckReceived ack && ack.outbound().isPresent() ? Status.ACK : Status.UNKNOWN;
        Retained next = preserve(new Entry(previous.request(), status, Optional.of(originalRef), Optional.of(custody), Math.addExact(same.head().state().sequence(), 1)));
        View before = view(same); State reduced = CouncilContinuationReducer.outcome(before.state(), before.records(), previous, next, collectedLate);
        Commit committed = commit(same, reduced, input(collectedLate ? "COLLECT" : "OUTCOME", Optional.of(next.reference()), Optional.empty(), Optional.empty()), evidence(before, next));
        StrictJson.require(same.head().state().sequence() == next.entry().resultSequence(), "actual result event sequence differs from its original durable row");
        faults.after(Boundary.OUTCOME_COMMITTED);
        return new CouncilContinuationReceipt(next.request(), next.status(), Optional.of(original), custody, next.reference(), committed.payload(), committed.event());
    }
    private CouncilContinuationReceipt retainedReceipt(ContinuityStorePort.Session same, Retained retained) throws IOException {
        var issued = retained.entry().issued().orElseThrow(); var outcome = runtime().archive().load(retained.entry().outcome().orElseThrow());
        ExactRef result = event(same.head(), retained.entry().resultSequence());
        WriterContracts.Pin pin = same.capturePin(result, MAX_BODY_BYTES);
        StrictJson.require(same.head().documents().contains(pin), "historical result must retain its exact immutable event pin");
        ObjectNode event = StrictJson.object(StrictJson.parse(same.readPinned(pin, MAX_BODY_BYTES), MAX_BODY_BYTES), Set.of("sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"));
        same.verifyPin(pin);
        ObjectNode details = StrictJson.object(event.get("details"), Set.of("evidence_id", "machine_id", "source", "domain_body", "precondition_digest"));
        DomainBodies.BodyRef body = DomainBodies.BodyRef.fromJson(details.get("domain_body"));
        ExactRef payload = body.payload();
        verifyCanonicalEvent(same, same.head(), result, retained.entry().resultSequence(), payload, retained.reference(), Set.of("OUTCOME", "COLLECT"));
        return new CouncilContinuationReceipt(retained.request(), retained.status(), Optional.of(outcome), issued, retained.reference(), payload, result);
    }
    private View rotate(ContinuityStorePort.Session same, View before) throws IOException {
        Scope scope = before.state().active().orElseThrow(); ActionReceipt settled = canonical(same.head(), scope.parentActionId());
        ExactRef parent = runtime().archive().preserveReceipt(settled);
        ObjectNode complete = StrictJson.object(); complete.put("schema", "xar.java-council-closed-scope/v1");
        complete.set("previous_state", before.body().reference().payload().toJson()); complete.set("settled_parent", parent.toJson());
        ExactRef completeRef = preserveMaterial(StrictJson.canonical(complete, MAX_BODY_BYTES));
        State reduced = CouncilContinuationReducer.rotate(before.state(), before.records(), settled, completeRef);
        commit(same, reduced, input("ROTATE", Optional.empty(), Optional.empty(), Optional.of(completeRef)), List.of(before.body().reference().payload(), parent, completeRef));
        return view(same);
    }

    /** Missing storage never means clear. Root must adopt a complete original manifest or a proven fresh-session seed. */
    public void adoptOriginal(ContinuityStorePort.Session same, ExactRef completeOriginalManifest, CouncilContinuationPorts.SeedAuthority seed) throws IOException {
        scoped(same, () -> {
            StrictJson.require(same.readDomain(DomainBodies.Slot.COUNCIL_CONTINUATION) instanceof DomainBodies.Unavailable, "continuation seed is only imported once");
            State original = seed.readCompleteOriginal(same, same.head(), completeOriginalManifest, runtime().archive());
            StrictJson.require(original.machineId().equals(same.head().state().machineId()), "continuation seed crossed the original writer machine");
            commit(same, original, input("SEED", Optional.empty(), Optional.of(completeOriginalManifest), Optional.empty()), List.of(completeOriginalManifest)); return null;
        });
    }
    public DomainBodies.Registration registration(CouncilContinuationPorts.SeedAuthority seed) {
        Objects.requireNonNull(seed);
        return new DomainBodies.Registration(DomainBodies.Slot.COUNCIL_CONTINUATION, SCHEMA, MAX_BODY_BYTES, sources, new DomainBodies.Verifier() {
            @Override public String verify(ContinuityState detached, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request, byte[] body) { throw new IllegalStateException("continuation verification needs the actual held writer Head"); }
            @Override public String verify(WriterContracts.Head head, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request, byte[] body) throws IOException {
                return verifyImport(head, previous, request, body, seed);
            }
        });
    }
    private String verifyImport(WriterContracts.Head head, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request,
            byte[] proposedBody, CouncilContinuationPorts.SeedAuthority seed) throws IOException {
        ContinuityStorePort.Session same = active.get(); requireSession(same);
        StrictJson.require(same.head().digest().equals(head.digest()) && same.head().documents().equals(head.documents()), "continuation reducer received a detached writer Head");
        ObjectNode in = StrictJson.object(StrictJson.parse(request.producerInput(), MAX_BODY_BYTES), Set.of("schema", "kind", "record", "seed_manifest", "closed_scope"));
        StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(in.get("schema"))), "continuation reducer input schema");
        String kind = StrictJson.text(in.get("kind")); State expected;
        if (kind.equals("SEED")) {
            StrictJson.require(previous.isEmpty() && in.get("record").isNull() && in.get("closed_scope").isNull(), "seed cannot overwrite an existing continuation domain");
            ExactRef manifest = ExactRef.fromJson(in.get("seed_manifest")); StrictJson.require(request.evidence().contains(manifest), "complete original seed manifest must be pinned");
            expected = seed.readCompleteOriginal(same, head, manifest, runtime().archive());
        } else {
            StrictJson.require(previous.isPresent() && in.get("seed_manifest").isNull(), "unimported continuation state is unavailable");
            State before = CouncilContinuationCodec.decodeState(readMaterial(previous.orElseThrow().payload())); List<Retained> prior = load(before);
            if(kind.equals("SEAT_CHECKPOINT")) {
                StrictJson.require(in.get("closed_scope").isNull(),"seat checkpoint is not a retired scope");
                var ref=ExactRef.fromJson(in.get("record"));var row=seatRow(ref);
                var parent=canonical(head,row.scope().parentActionId());var token=recovery(same,parent);
                StrictJson.require(token!=null,"live seat checkpoint requires its actual private recovered original");
                token.requireCurrent();StrictJson.require(request.evidence().contains(ref)&&request.evidence().contains(row.value().tuple()),"seat checkpoint original refs must be pinned");
                expected=verifySeatTransition(same,head,before,ref);
            } else if (kind.equals("ROTATE")) {
                StrictJson.require(in.get("record").isNull(), "closed scope is a distinct transition"); ExactRef closed = ExactRef.fromJson(in.get("closed_scope"));
                var closure = StrictJson.object(StrictJson.parse(readMaterial(closed), MAX_BODY_BYTES), Set.of("schema", "previous_state", "settled_parent"));
                StrictJson.require("xar.java-council-closed-scope/v1".equals(StrictJson.text(closure.get("schema"))) && ExactRef.fromJson(closure.get("previous_state")).equals(previous.orElseThrow().payload()), "closed scope lost the complete prior manifest");
                ActionReceipt actual = canonical(head, before.active().orElseThrow().parentActionId());
                StrictJson.require(actual.equals(runtime().archive().loadReceipt(ExactRef.fromJson(closure.get("settled_parent")))), "closed scope did not preserve the canonical settled parent");
                expected = CouncilContinuationReducer.rotate(before, prior, actual, closed);
            } else {
                StrictJson.require(in.get("closed_scope").isNull(), "request transition cannot archive its scope");
                Retained next = retained(ExactRef.fromJson(in.get("record"))); ActionReceipt parent = canonical(head, next.request().scope().parentActionId());
                RecoveryOriginal recovery=recovery(same,parent);
                requireOriginal(parent, runtime().archive().loadReceipt(next.request().originalParentReceipt()).command(), ActionTransitions.attempt(parent.state()).orElseThrow(), kind.equals("ISSUE") && recovery==null);
                if(kind.equals("ISSUE") && recovery!=null)recovery.requireCurrent();
                StrictJson.require(parent.bodySha256().equals(next.request().scope().parentBodySha256())
                        && ActionTransitions.attempt(parent.state()).orElseThrow().requestId().equals(next.request().scope().originalAttemptRequestId()), "continuation row changed the original attempt");
                verifyRequest(next.request());
                if (kind.equals("ISSUE")) {
                    StrictJson.require(next.request().issuedSequence() == Math.addExact(head.state().sequence(), 1), "issued request did not consume the actual next sequence");
                    GuardEvidence actual;
                    if(recovery==null){actual=runtime().guard().current(same,head,parent,next.request().deadline());
                        verifyFresh(parent,ActionTransitions.attempt(parent.state()).orElseThrow(),actual,next.request().deadline());}
                    else {actual=recoveredGuard(recovery);verifyRecoveredFresh(parent,recovery.attempt(),actual,next.request().deadline());}
                    StrictJson.require(actual.origin().equals(next.request().guard().origin()) && actual.source().equals(next.request().guard().source())
                            && actual.connectionGeneration().equals(next.request().guard().connectionGeneration())
                            && actual.nativeEvidence().equals(next.request().guard().nativeEvidence()) && actual.capabilityEvidence().equals(next.request().guard().capabilityEvidence()), "actual source frame changed before continuation issue");
                    runtime().policy().verifyIssue(same, head, parent, prior, next.request(), runtime().archive());
                    expected = CouncilContinuationReducer.issue(before, prior, next);
                } else {
                    StrictJson.require(kind.equals("OUTCOME") || kind.equals("COLLECT"), "known continuation reducer transition required");
                    StrictJson.require(next.entry().resultSequence() == Math.addExact(head.state().sequence(), 1), "result must consume the actual next canonical sequence");
                    Retained old = prior.stream().filter(row -> row.request().requestId().equals(next.request().requestId())).findFirst().orElseThrow();
                    NativeActionPort.DispatchOutcome original = runtime().archive().load(next.entry().outcome().orElseThrow());
                    StrictJson.require(original.requestId().equals(next.request().requestId()), "original continuation result belongs to another request");
                    Status actual = original instanceof NativeActionPort.AckReceived ack && ack.outbound().isPresent() ? Status.ACK : Status.UNKNOWN;
                    StrictJson.require(actual == next.status(), "ACK/UNKNOWN classification changed");
                    runtime().policy().verifyOutcome(same, head, parent, prior, next.entry(), original, runtime().archive());
                    expected = CouncilContinuationReducer.outcome(before, prior, old, next, kind.equals("COLLECT"));
                }
            }
        }
        StrictJson.require(expected.machineId().equals(head.state().machineId()) && Arrays.equals(CouncilContinuationCodec.encodeState(expected), proposedBody), "continuation body differs from the same real reducer replay");
        return ActionCodec.sha256(proposedBody);
    }

    private Commit commit(ContinuityStorePort.Session same, State state, byte[] producer, List<ExactRef> evidence) throws IOException {
        ExactRef body = preserveMaterial(CouncilContinuationCodec.encodeState(state));
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.COUNCIL_CONTINUATION, SCHEMA, body, producer, List.copyOf(new LinkedHashSet<>(evidence)),
                "council-continuation-" + same.head().state().sequence() + "-" + body.sha256());
        var result = same.commitImport(same.previewImport(request)); View actual = view(same);
        StrictJson.require(actual.body().reference().payload().equals(body) && actual.state().equals(state), "canonical continuation commit readback differs");
        return new Commit(body, event(same.head(), result.head().sequence()),result);
    }
    private View view(ContinuityStorePort.Session same) throws IOException {
        requireSession(same); var read = same.readDomain(DomainBodies.Slot.COUNCIL_CONTINUATION);
        if (!(read instanceof DomainBodies.Available body)) throw new IOException("complete continuation domain unavailable; missing never means empty");
        StrictJson.require(body.reference().contractSchema().equals(SCHEMA), "continuation domain schema changed");
        State state = CouncilContinuationCodec.decodeState(body.canonicalBody()); return new View(body, state, load(state));
    }
    private List<Retained> load(State state) { return state.records().stream().map(this::retained).toList(); }
    private Retained retained(ExactRef reference) { return new Retained(reference, CouncilContinuationCodec.decodeEntry(readMaterial(reference))); }
    private Retained preserve(Entry entry) { ExactRef ref = preserveMaterial(CouncilContinuationCodec.encodeEntry(entry)); return retained(ref); }
    private ExactRef preserveMaterial(byte[] body) {
        var raw = new RawJson(body); ExactRef ref = runtime().archive().preserveMaterial(raw);
        StrictJson.require(Arrays.equals(body, readMaterial(ref)), "continuation immutable archive differs"); return ref;
    }
    private byte[] readMaterial(ExactRef reference) {
        byte[] raw = runtime().archive().loadMaterial(reference).bytes();
        StrictJson.require(reference.bytes() == raw.length && reference.sha256().equals(ActionCodec.sha256(raw)), "continuation original body changed"); return raw;
    }
    private ActionReceipt canonical(WriterContracts.Head head, String actionId) { return ContinuityActionJournal.lookup(head.state(), actionId, runtime().archive()).orElseThrow(() -> new IllegalArgumentException("canonical original action absent")); }
    private void requireOriginal(ActionReceipt actual, ActionCommand expected, ActionState.Attempt attempt, boolean issuing) {
        StrictJson.require(Arrays.equals(ActionCodec.encodeCommand(actual.command()), ActionCodec.encodeCommand(expected))
                && ActionTransitions.attempt(actual.state()).filter(attempt::equals).isPresent(), "continuation changed the complete canonical parent/original attempt");
        StrictJson.require(actual.command().operation().value().equals("private-assign-councillor-v1"), "only the reviewed Council action may use continuation");
        StrictJson.require(!actual.settled() && (!issuing || actual.state() instanceof ActionState.AckReceived), "new continuation only follows the live original ACK; UNKNOWN is collect-only");
        var original = ActionTransitions.dispatch(actual.state()).orElseThrow();
        StrictJson.require(original instanceof NativeActionPort.AckReceived ack && ack.nativeOk() && ack.outbound().isPresent(), "original Council submit needs its actual successful pending ACK and outbound");
    }
    private void verifyFresh(ActionReceipt parent, ActionState.Attempt original, GuardEvidence actual, Instant deadline) {
        Instant now = clock.instant(); GuardEvidence before = original.guard();
        StrictJson.require(actual.origin() instanceof CommandOrigin.Gameplay && before.origin() instanceof CommandOrigin.Gameplay
                && actual.origin().machineId().equals(before.origin().machineId()) && actual.origin().game().equals(before.origin().game())
                && actual.observed().frame().episodeRunId().equals(before.observed().frame().episodeRunId())
                && actual.observed().frame().identity().player().equals(before.observed().frame().identity().player())
                && actual.observed().frame().identity().nativeRevision().compareTo(before.observed().frame().identity().nativeRevision()) >= 0,
                "fresh continuation crossed original Game/player/episode or moved backward");
        StrictJson.require(actual.source().equals(parent.command().source()) && actual.sessionId().equals(parent.command().sessionId())
                && actual.connectionGeneration().equals(before.connectionGeneration()) && actual.authorityId().equals(before.authorityId())
                && actual.operation().equals(parent.command().operation()) && !actual.supportingEvidence().isEmpty(), "fresh continuation source/session/authority/original operation changed");
        StrictJson.require(now.isBefore(deadline) && now.isBefore(ActionObservationWindow.deadline(parent.command())) && !now.isBefore(actual.observedAt()) && !now.isAfter(actual.validUntil()), "continuation source guard is stale or future-dated");
    }
    private void verifyRequest(Request request) {
        NativeRequest prepared = runtime().archive().loadRequest(request.preparedRequest());
        StrictJson.require(prepared.step().equals(request.stage().step()) && prepared.requiredCapability().isEmpty()
                && prepared.additionalFields().objectFieldNames().isEmpty(), "continuation cannot select another step/capability/argument");
        request.supportingEvidence().forEach(ref -> { try { var pin = active.get().capturePin(ref, WriterContracts.MAX_PIN_BYTES); active.get().verifyPin(pin); } catch (IOException failure) { throw new UncheckedIOException(failure); } });
    }
    private void requireSession(ContinuityStorePort.Session same) throws IOException {
        Objects.requireNonNull(same, "live original continuation writer Session required"); same.requireWriter(originalLock);
        runtime().archive().withSession(same); StrictJson.require(active.get() == same, "continuation writer scope is escaped or on another thread");
    }
    private <T> T scoped(ContinuityStorePort.Session same, Work<T> work) throws IOException {
        ContinuityStorePort.Session previous = active.get(); StrictJson.require(previous == null || previous == same, "another continuation writer Session is active"); active.set(same);
        try {
            requireSession(same);
            return runtime().archive().inSession(same, bound -> {
                try { return work.run(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            });
        }
        catch (UncheckedIOException failure) { throw failure.getCause(); }
        finally { if (previous == null) active.remove(); else active.set(previous); }
    }
    private List<ExactRef> evidence(View previous, Retained next) {
        var refs = new ArrayList<ExactRef>(); refs.add(previous.body().reference().payload()); refs.add(next.reference());
        Request request = next.request(); refs.add(request.originalParentReceipt()); refs.add(request.preparedRequest());
        refs.add(request.guard().nativeEvidence()); refs.add(request.guard().capabilityEvidence()); refs.addAll(request.guard().supportingEvidence()); refs.addAll(request.supportingEvidence());
        next.entry().outcome().ifPresent(refs::add); next.entry().issued().ifPresent(custody -> { refs.add(custody.record()); refs.add(custody.domainPayload()); refs.add(custody.event()); });
        return List.copyOf(new LinkedHashSet<>(refs));
    }
    private static byte[] input(String kind, Optional<ExactRef> record, Optional<ExactRef> seed, Optional<ExactRef> closed) {
        var row = StrictJson.object(); row.put("schema", INPUT_SCHEMA); row.put("kind", kind); row.set("record", record.map(ExactRef::toJson).orElse(null));
        row.set("seed_manifest", seed.map(ExactRef::toJson).orElse(null)); row.set("closed_scope", closed.map(ExactRef::toJson).orElse(null)); return StrictJson.canonical(row, MAX_BODY_BYTES);
    }
    private static ExactRef event(WriterContracts.Head head, long sequence) {
        String name = String.format(java.util.Locale.ROOT, "%08d.json", sequence);
        List<ExactRef> actual = head.documents().stream().map(WriterContracts.Pin::reference).filter(ref -> {
            Path path = Path.of(ref.path()); return path.getFileName().toString().equals(name) && path.getParent() != null
                    && path.getParent().getFileName().toString().equals("ROOT-CONTINUITY-WINDOW-EVENTS");
        }).toList(); StrictJson.require(actual.size() == 1, "exact actual immutable continuation event pin required"); return actual.getFirst();
    }
}
