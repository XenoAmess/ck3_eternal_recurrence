package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.application.planning.governance.OrdinaryFeastPolicy;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** The one ordinary FEAST holder. Pending reserves an exact command; only canonical material settlement clears it. */
public final class FeastDomainRuntime implements DomainBodies.Verifier,OrdinaryPlanCompletion {
    public static final String SCHEMA="xar.ck3.activity-feast-stage5-start-private.v1";
    public record Sources(ExactRef implementation,List<ExactRef> producers) {
        public Sources {Objects.requireNonNull(implementation);producers=List.copyOf(producers);StrictJson.require(implementation.bytes()>0
                && !producers.isEmpty() && producers.size()<=64 && producers.stream().allMatch(ref->ref.bytes()>0),"actual Feast source closure required");}
    }
    public record Pending(String episodeRunId,ExactRef command,String commandBodySha256) {
        public Pending {StrictJson.text(episodeRunId);Objects.requireNonNull(command);WriterContracts.requireDigest(commandBodySha256);}
    }
    public record FinalRetention(ExactRef state,long activityFullId,long hostCharacterId) {
        public FinalRetention {Objects.requireNonNull(state);StrictJson.require(state.bytes()>0&&state.bytes()<=131072&&activityFullId>=0&&activityFullId<=0xFFFF_FFFEL&&hostCharacterId>0&&hostCharacterId<=0xFFFF_FFFEL,"bounded actual Activity final locator and full IDs required");}
    }
    public record ActivityOrigin(ExactRef originalStart,Optional<FinalRetention> finalState) {
        public ActivityOrigin {Objects.requireNonNull(originalStart);Objects.requireNonNull(finalState);}
    }
    public record Resolved(ExactRef receipt,ExactRef command,ActionReceipt.Outcome outcome,Optional<ActivityOrigin> activity) {
        public Resolved(ExactRef receipt,ExactRef command,ActionReceipt.Outcome outcome){this(receipt,command,outcome,Optional.empty());}
        public Resolved {Objects.requireNonNull(receipt);Objects.requireNonNull(command);Objects.requireNonNull(outcome);Objects.requireNonNull(activity);
            StrictJson.require(outcome!=ActionReceipt.Outcome.UNRESOLVED,"ACK/UNKNOWN cannot resolve Feast pending");}
    }
    public record Ledger(Optional<Pending> pending,Optional<Resolved> resolved) {
        public Ledger {Objects.requireNonNull(pending);Objects.requireNonNull(resolved);}
    }
    private enum Kind { INITIAL,PENDING,SETTLED,FINAL_STATE }
    private record Input(Kind kind,Optional<ExactRef> previous,Optional<ExactRef> command,Optional<ExactRef> receipt,Optional<ExactRef> initial,Optional<ExactRef> plan,Optional<ExactRef> finalState) {
        Input(Kind kind,Optional<ExactRef> previous,Optional<ExactRef> command,Optional<ExactRef> receipt,Optional<ExactRef> initial,Optional<ExactRef> plan){this(kind,previous,command,receipt,initial,plan,Optional.empty());}
        Input {Objects.requireNonNull(kind);Objects.requireNonNull(previous);Objects.requireNonNull(command);Objects.requireNonNull(receipt);Objects.requireNonNull(initial);Objects.requireNonNull(plan);Objects.requireNonNull(finalState);
            StrictJson.require(switch(kind) {case INITIAL->previous.isEmpty()&&command.isEmpty()&&receipt.isEmpty()&&initial.isPresent()&&plan.isEmpty()&&finalState.isEmpty();
                case PENDING->previous.isPresent()&&command.isPresent()&&receipt.isEmpty()&&initial.isEmpty()&&plan.isPresent()&&finalState.isEmpty();
                case SETTLED->previous.isPresent()&&command.isEmpty()&&receipt.isPresent()&&initial.isEmpty()&&plan.isEmpty()&&finalState.isEmpty();
                case FINAL_STATE->previous.isPresent()&&command.isEmpty()&&receipt.isEmpty()&&initial.isEmpty()&&plan.isEmpty()&&finalState.isPresent();},"exact Feast publication branch fields required");}
    }
    private record Planned(PlanningRequest request,ExactRef original) { }
    private final java.util.Map<String,Planned> plannedInputs=new java.util.HashMap<>();private OrdinaryFeastPolicy actualPolicy;private GovernanceCadenceActions.Publisher cadenceActions;private FeastFinalSettlement finalSettlement;
    public void bindCadenceActions(GovernanceCadenceActions.Publisher actual){cadenceActions=Objects.requireNonNull(actual);}
    public void bindPolicy(OrdinaryFeastPolicy actual){actualPolicy=Objects.requireNonNull(actual);}
    public void bindFinalSettlement(FeastFinalSettlement actual){finalSettlement=Objects.requireNonNull(actual);}
    private final Path writerLock;private final Sources sources;private final DomainBodies.Registration registration;private RootApplicationAssembly.Core core;private RootRuntimeContext context;
    private GovernanceNextInitialization nextVerifier;
    public void bindNextVerifier(GovernanceNextInitialization actual){nextVerifier=Objects.requireNonNull(actual);}
    public FeastDomainRuntime(Path originalWriterLock,Sources sources) {writerLock=Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();this.sources=Objects.requireNonNull(sources);this.registration=new DomainBodies.Registration(DomainBodies.Slot.FEAST,SCHEMA,1_048_576,sources.producers(),this);}
    public DomainBodies.Registration registration() {return registration;}
    public synchronized void bindCore(RootApplicationAssembly.Core actual) {
        StrictJson.require(core==null && actual.configuration().ledger().lock().toAbsolutePath().normalize().equals(writerLock),"Feast binds the one original Core once");core=actual;
    }
    public synchronized void installContext(RootRuntimeContext actual) throws IOException {
        StrictJson.require(actual.core()==core(),"Feast cannot adopt another Core/writer");context=actual;plannedInputs.clear();actualPolicy=null;finalSettlement=null;
    }
    private synchronized RootApplicationAssembly.Core core()throws IOException {if(core==null)throw new IOException("Feast Core not bound");return core;}
    private synchronized RootRuntimeContext context()throws IOException {if(context==null)throw new IOException("Feast actual Game not installed");return context;}
    private ContinuityStorePort.Session session()throws IOException {var same=core().writer().borrowedSession();core().writer().requireSession(same);same.requireWriter(writerLock);return same;}
    public CanonicalFinanceStateSource.Binding financeBinding() {
        var reader=new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.FEAST,sources.implementation(),document->{
            var ledger=decode(document.bytes());ledger.resolved().flatMap(Resolved::activity).filter(value->value.finalState().isPresent()).ifPresent(origin->{
                try{requireFinal().restore(session(),origin);}catch(IOException failure){throw new UncheckedIOException(failure);}});
            return ledger.pending().isPresent()?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR;
        });
        return new CanonicalFinanceStateSource.Binding(reader,DomainBodies.Slot.FEAST,SCHEMA,1_048_576,sources.producers());
    }
    /** Central current-Game router uses this exact producer before INTENT; this does not reserve, dispatch or mint a completed result. */
    public void verifyActivityAction(org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes.Kind kind,ActionCommand command)throws IOException {
        Objects.requireNonNull(kind);Objects.requireNonNull(command);var same=session();context().requireCurrent(command.deadline());
        StrictJson.require(kind==org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes.Kind.exact(command.operation())
                &&OrdinaryFeastPolicy.OWNED.contains(command.operation())&&command.origin() instanceof CommandOrigin.Gameplay
                &&command.before().game().equals(context().game().generation())&&command.source().equals(context().source())
                &&command.sessionId().equals(context().game().sessionId()),"actual ordinary Activity admission crossed its producer or current Game/source/session");
        var planned=plannedInputs.get(command.actionId());if(planned==null)throw new IOException("actual selected Feast planning original is absent");
        if(actualPolicy==null)throw new IOException("actual installed Feast policy is not bound");
        context().collector().currentPlanning(same,planned.request(),command,command.deadline(),(current,lease)->{
            actualPolicy.revalidate(command,current);return Boolean.TRUE;
        });
        ActionReadPublicationScope.requireClearBeforeIntent(same,command);
    }
    public RootDomainIntentPreparation.Binding pendingBinding() {
        return new RootDomainIntentPreparation.Binding("ordinary-feast",sources.implementation(),command->OrdinaryFeastPolicy.OWNED.contains(command.operation()),(same,command)->{
            try {
                core().writer().requireSession(same);context().requireCurrent(command.deadline());
                StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay && command.before().game().equals(context().game().generation())
                        && command.source().equals(context().source()) && command.sessionId().equals(context().game().sessionId()),"Feast pending crossed actual Game/source/session");
                Planned planned=plannedInputs.get(command.actionId());if(planned==null)throw new IOException("actual original Feast planning input was not retained by completion");
                verifyActivityAction(org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes.Kind.exact(command.operation()),command);
                var old=available(same);ExactRef original=core().archive().inSession(same,archive->archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(command))));
                publish(same,new Input(Kind.PENDING,Optional.of(old.reference().payload()),Optional.of(original),Optional.empty(),Optional.empty(),Optional.of(planned.original())));
            } catch(IOException failure) {throw new UncheckedIOException("actual Feast pending publication unavailable",failure);}
        });
    }
    public WriterContracts.Receipt initialize(ContinuityStorePort.Session same,RootInitialEpisodeProof fresh)throws IOException {
        core().writer().requireSession(same);fresh.requireCurrent(same);return initialize(same,fresh.preserveOriginal(same));
    }
    public WriterContracts.Receipt initialize(ContinuityStorePort.Session same,FreshCampaignContext fresh)throws IOException {
        core().writer().requireSession(same);StrictJson.require(fresh.context()==context(),"fresh Feast belongs to another installed Game");
        fresh.requireCurrent(same);return initialize(same,fresh.preserveOriginal(same));
    }
    private WriterContracts.Receipt initialize(ContinuityStorePort.Session same,ExactRef basis)throws IOException {
        core().writer().requireSession(same);var old=same.readDomain(DomainBodies.Slot.FEAST);
        StrictJson.require(old instanceof DomainBodies.Unavailable unavailable && unavailable.reason()==DomainBodies.Reason.UNIMPORTED,
                "fresh Feast initialization cannot clear an existing/unavailable legacy or restored body");
        return publish(same,new Input(Kind.INITIAL,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(basis),Optional.empty())).orElseThrow();
    }
    private Optional<WriterContracts.Receipt> publish(ContinuityStorePort.Session same,Input input)throws IOException {
        core().writer().requireSession(same);var head=same.head();Optional<DomainBodies.BodyRef> previous=DomainBodies.reference(head.state(),DomainBodies.Slot.FEAST);
        byte[] output=reduce(same,head,previous,input);if(previous.isPresent() && Arrays.equals(output,read(same,previous.orElseThrow().payload())))return Optional.empty();
        ExactRef body=core().archive().preserveArtifact(same,output,1_048_576);byte[] producer=encodeInput(input);
        var request=new DomainBodies.ImportRequest(DomainBodies.Slot.FEAST,SCHEMA,body,producer,evidence(input),"ordinary-feast-"+ActionCodec.sha256(producer));
        var prepared=same.previewImport(request);StrictJson.require(prepared.predecessor().digest().equals(head.digest()),"Feast preview crossed its locked head");
        var committed=same.commitImport(prepared);var actual=available(same);
        StrictJson.require(committed.disposition()!=WriterContracts.Disposition.NO_CHANGE && actual.reference().payload().equals(body)
                && Arrays.equals(actual.canonicalBody(),output),"Feast requires actual domain commit and original body readback");return Optional.of(committed);
    }
    @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned) {
        try {
            var same=session();
            if(planned.trace().finalPlan().isPresent() && planned.trace().finalPlan().orElseThrow().command().filter(command->OrdinaryFeastPolicy.OWNED.contains(command.operation())).isPresent()) {
                var command=planned.trace().finalPlan().orElseThrow().command().orElseThrow();
                StrictJson.require(command.before().equals(original.before()) && command.source().equals(original.source()) && command.sessionId().equals(original.sessionId()),"Feast chosen command differs from actual original request");
                var ref=core().archive().inSession(same,archive->archive.preserveMaterial(new RawJson(PlanningWire.encodeRequest(original))));
                plannedInputs.clear();plannedInputs.put(command.actionId(),new Planned(original,ref));
            }
            var body=available(same);var ledger=decode(body.canonicalBody());if(ledger.pending().isEmpty()) {
                var activity=ledger.resolved().flatMap(Resolved::activity);
                if(activity.isPresent()&&activity.orElseThrow().finalState().isEmpty()) {
                    var retained=requireFinal().observe(same,original,activity.orElseThrow());
                    if(retained.isPresent()) {
                        var head=same.head();var changed=publish(same,new Input(Kind.FINAL_STATE,Optional.of(body.reference().payload()),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(retained.orElseThrow().state())));
                        return new Published(head,changed.orElseThrow());
                    }
                }
                if(ledger.resolved().filter(value->value.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED).isPresent()) {
                    var resolved=core().archive().inSession(same,archive->archive.loadReceipt(ledger.resolved().orElseThrow().receipt()));
                    var head=same.head();var changed=resetCadence(same,resolved);
                    return changed.<PlanningDisposition>map(value->new Published(head,value)).orElseGet(()->new Unchanged("Feast result and actual-action cadence already current"));
                }
                return new Unchanged("Feast has no pending command to reconcile");
            }
            var command=command(same,ledger.pending().orElseThrow().command());var canonical=canonical(same,command.actionId());
            if(canonical.isEmpty() || !canonical.orElseThrow().settled())return new Unchanged("Feast original pending/UNKNOWN preserved; no resubmission");
            var head=same.head();var receipt=core().archive().inSession(same,archive->archive.receiptReferenceOf(canonical.orElseThrow()));
            var changed=publish(same,new Input(Kind.SETTLED,Optional.of(body.reference().payload()),Optional.empty(),Optional.of(receipt),Optional.empty(),Optional.empty()));
            var cadence=resetCadence(same,canonical.orElseThrow());var last=cadence.isPresent()?cadence:changed;
            return last.<PlanningDisposition>map(value->new Published(head,value)).orElseGet(()->new Unchanged("Feast original settlement and cadence already current"));
        } catch(IOException|IllegalArgumentException|IllegalStateException failure) {return new Blocked("actual Feast settlement replay unavailable: "+failure.getMessage(),List.of());}
    }
    @Override public ExecutionDisposition afterExecution(ActionReceipt actual) {
        if(!OrdinaryFeastPolicy.OWNED.contains(actual.command().operation()))return new Unchanged("receipt belongs to another domain");
        if(!actual.settled())return new Unchanged("Feast ACK/UNKNOWN retains exact original pending");
        try {
            var same=session();var body=available(same);var head=same.head();
            if(decode(body.canonicalBody()).pending().isEmpty() && actual.outcome()==ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH) {
                var retained=canonical(same,actual.command().actionId()).orElseThrow(()->new IOException("rejected Feast action is not canonical"));
                core().archive().inSession(same,archive->{StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(retained,archive),ActionReceiptCodec.encodeReceipt(actual,archive)),"caller rejection differs from actual canonical Feast action");return Boolean.TRUE;});
                return new Unchanged("canonical rejection preceded any Feast pending reservation; no state is cleared");
            }
            var original=core().archive().inSession(same,archive->archive.receiptReferenceOf(actual));
            var changed=publish(same,new Input(Kind.SETTLED,Optional.of(body.reference().payload()),Optional.empty(),Optional.of(original),Optional.empty(),Optional.empty()));
            var cadence=resetCadence(same,actual);var last=cadence.isPresent()?cadence:changed;
            return last.<ExecutionDisposition>map(value->new Published(head,value)).orElseGet(()->new Unchanged("Feast exact settlement and cadence already current"));
        } catch(IOException|IllegalArgumentException|IllegalStateException failure) {return new Blocked("actual Feast settlement unavailable: "+failure.getMessage(),List.of());}
    }
    private Optional<WriterContracts.Receipt> resetCadence(ContinuityStorePort.Session same,ActionReceipt actual)throws IOException {
        if(actual.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)return Optional.empty();
        if(cadenceActions==null)throw new IOException("actual shared governance action cadence publisher is not bound");
        return cadenceActions.publish(same,actual);
    }
    @Override public String verify(ContinuityState ignored,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest input,byte[] body)throws IOException {throw new IOException("Feast requires actual locked Head");}
    @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] original)throws IOException {
        if(GovernanceNextInitialization.SCHEMA.equals(StrictJson.text(StrictJson.parse(request.producerInput()).get("schema")))) {
            if(nextVerifier==null)throw new IOException("actual NEXT governance initializer is not installed");return nextVerifier.verify(head,previous,request,original);
        }
        var same=session();StrictJson.require(same.head().digest().equals(head.digest()) && request.slot()==DomainBodies.Slot.FEAST && request.contractSchema().equals(SCHEMA),"Feast original head/slot/schema changed");
        var input=decodeInput(request.producerInput());StrictJson.require(request.evidence().equals(evidence(input)),"Feast complete source evidence differs");
        byte[] expected=reduce(same,head,previous,input);StrictJson.require(Arrays.equals(expected,original),"Feast original command/receipt reducer differs from proposed body");
        return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",head.digest()).put("body",ActionCodec.sha256(expected)).put("input",ActionCodec.sha256(request.producerInput()))));
    }
    private byte[] reduce(ContinuityStorePort.Session same,WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,Input input)throws IOException {
        if(input.kind()==Kind.INITIAL) {
            StrictJson.require(previous.isEmpty(),"initial Feast body cannot replace any prior body");ExactRef basis=input.initial().orElseThrow();
            if(FreshCampaignContext.isOriginal(context(),same,basis))FreshCampaignContext.replayOriginal(context(),same,basis).requireInitializationPredecessor(same,head);
            else RootInitialEpisodeProof.replayOriginal(context(),same,basis).requireInitializationPredecessor(same,head);
            return encode(new Ledger(Optional.empty(),Optional.empty()));
        }
        var before=previous.orElseThrow(()->new IOException("actual Feast prior body missing; absence is not CLEAR"));
        // Retained producer references are historical DATA; current code may continue the exact canonical body.
        StrictJson.require(before.payload().equals(input.previous().orElseThrow())
                && DomainBodies.reference(head.state(),DomainBodies.Slot.FEAST).filter(before::equals).isPresent(),"Feast prior original custody differs");
        var old=decode(read(same,before.payload()));
        if(input.kind()==Kind.FINAL_STATE) {
            StrictJson.require(old.pending().isEmpty(),"pending Feast cannot be overwritten by terminal read");var resolved=old.resolved().orElseThrow();var origin=resolved.activity().orElseThrow();
            StrictJson.require(origin.finalState().isEmpty(),"the first real terminal original is immutable");
            var state=requireFinal().restoreArtifact(same,input.finalState().orElseThrow());
            var retained=new FinalRetention(input.finalState().orElseThrow(),state.identity().activityFullId(),state.identity().hostCharacterId());
            var terminal=new ActivityOrigin(origin.originalStart(),Optional.of(retained));requireFinal().restore(same,terminal);
            return encode(new Ledger(Optional.empty(),Optional.of(new Resolved(resolved.receipt(),resolved.command(),resolved.outcome(),Optional.of(terminal)))));
        }
        if(input.kind()==Kind.PENDING) {
            var command=command(same,input.command().orElseThrow());StrictJson.require(OrdinaryFeastPolicy.OWNED.contains(command.operation()) && command.origin() instanceof CommandOrigin.Gameplay,"exact ordinary Feast gameplay command required");
            var planned=PlanningWire.decodeRequest(core().archive().inSession(same,archive->archive.loadMaterial(input.plan().orElseThrow())).bytes());
            StrictJson.require(planned.before().equals(command.before())&&planned.source().equals(command.source())&&planned.sessionId().equals(command.sessionId()),"Feast original plan crossed its reserved exact command");
            Pending pending=new Pending(command.before().frame().episodeRunId(),input.command().orElseThrow(),ActionCodec.bodySha256(command));
            StrictJson.require(old.pending().isEmpty() || old.pending().orElseThrow().equals(pending),"another original Feast pending/UNKNOWN cannot be overwritten");
            return encode(new Ledger(Optional.of(pending),old.resolved()));
        }
        ActionReceipt receipt=core().archive().inSession(same,archive->archive.loadReceipt(input.receipt().orElseThrow()));
        var canonical=canonical(same,receipt.command().actionId()).orElseThrow(()->new IOException("Feast result is absent from actual canonical action chain"));
        core().archive().inSession(same,archive->{StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(receipt,archive),ActionReceiptCodec.encodeReceipt(canonical,archive)),"Feast caller receipt differs from canonical result");return Boolean.TRUE;});
        StrictJson.require(receipt.settled() && OrdinaryFeastPolicy.OWNED.contains(receipt.command().operation()),"unresolved/foreign receipt cannot clear Feast pending");
        if(old.pending().isEmpty()) {
            StrictJson.require(old.resolved().filter(value->value.receipt().equals(input.receipt().orElseThrow())).isPresent(),"Feast result has no matching actual pending command");return encode(old);
        }
        Pending pending=old.pending().orElseThrow();var command=command(same,pending.command());
        StrictJson.require(ActionCodec.bodySha256(command).equals(receipt.bodySha256()) && pending.commandBodySha256().equals(receipt.bodySha256())
                && Arrays.equals(ActionCodec.encodeCommand(command),ActionCodec.encodeCommand(receipt.command())),"Feast result crossed its original exact command");
        if(receipt.state() instanceof ActionState.Settled settled)ActionEffects.validate(command,settled.attempt(),settled.settlement());
        if(receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED)context().bindings().actualArchivedVerifier(command.operation())
                .orElseThrow(()->new IOException("actual Feast native material replay is not installed")).verifier().verify(head,receipt,core().archive().withSession(same));
        Optional<ActivityOrigin> activity=old.resolved().flatMap(Resolved::activity);
        if(receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&command.operation().equals(OrdinaryFeastPolicy.START)) {
            requireFinal().requireStart(same,input.receipt().orElseThrow());activity=Optional.of(new ActivityOrigin(input.receipt().orElseThrow(),Optional.empty()));
        }
        return encode(new Ledger(Optional.empty(),Optional.of(new Resolved(input.receipt().orElseThrow(),pending.command(),receipt.outcome(),activity))));
    }
    private FeastFinalSettlement requireFinal()throws IOException {if(finalSettlement==null)throw new IOException("actual M6 Activity final replay is not installed");return finalSettlement;}
    private Optional<ActionReceipt> canonical(ContinuityStorePort.Session same,String id)throws IOException {return core().archive().inSession(same,archive->ContinuityActionJournal.lookup(uncheckedHead(same).state(),id,archive));}
    private static WriterContracts.Head uncheckedHead(ContinuityStorePort.Session same) {try{return same.head();}catch(IOException failure){throw new UncheckedIOException(failure);}}
    private ActionCommand command(ContinuityStorePort.Session same,ExactRef ref)throws IOException {return ActionCodec.decodeCommand(core().archive().inSession(same,archive->archive.loadMaterial(ref)).bytes());}
    private byte[] read(ContinuityStorePort.Session same,ExactRef ref)throws IOException {return core().archive().readArtifact(same,ref,1_048_576);}
    private DomainBodies.Available available(ContinuityStorePort.Session same)throws IOException {core().writer().requireSession(same);var read=same.readDomain(DomainBodies.Slot.FEAST);if(read instanceof DomainBodies.Available actual)return actual;throw new IOException("actual registered Feast body unavailable");}
    public static byte[] encode(Ledger ledger) {
        var row=StrictJson.object().put("schema",SCHEMA);if(ledger.pending().isEmpty())row.putNull("pending");else {var pending=ledger.pending().orElseThrow();var value=row.putObject("pending").put("schema","xar.java-feast-pending/v1").put("episode_run_id",pending.episodeRunId()).put("command_body_sha256",pending.commandBodySha256());value.set("command",pending.command().toJson());}
        if(ledger.resolved().isEmpty())row.putNull("resolved");else {var resolved=ledger.resolved().orElseThrow();var value=row.putObject("resolved").put("schema","xar.java-feast-result/v1").put("outcome",resolved.outcome().name());value.set("receipt",resolved.receipt().toJson());value.set("command",resolved.command().toJson());
            if(resolved.activity().isEmpty())value.putNull("activity");else {
                var origin=resolved.activity().orElseThrow();var activity=value.putObject("activity");activity.set("original_start",origin.originalStart().toJson());
                if(origin.finalState().isEmpty())activity.putNull("final_state");else {
                    var retained=origin.finalState().orElseThrow();var terminal=activity.putObject("final_state").put("activity_id",retained.activityFullId()).put("host_character_id",retained.hostCharacterId());terminal.set("state",retained.state().toJson());
                    value.put("activity_id",retained.activityFullId()).put("actor_character_id",retained.hostCharacterId());value.putObject("lifecycle").put("terminal_observed",true).put("activity_id",retained.activityFullId()).put("actor_character_id",retained.hostCharacterId()).put("activity_type_key","activity_feast");
                }
            }
        }return StrictJson.canonical(row);
    }
    public static Ledger decode(byte[] body) {
        var row=StrictJson.object(StrictJson.parse(body),Set.of("schema","pending","resolved"));StrictJson.require(StrictJson.text(row.get("schema")).equals(SCHEMA),"exact Feast ledger schema required");
        Optional<Pending> pending=Optional.empty();if(!row.get("pending").isNull()){var value=StrictJson.object(row.get("pending"),Set.of("schema","episode_run_id","command_body_sha256","command"));StrictJson.require(StrictJson.text(value.get("schema")).equals("xar.java-feast-pending/v1"),"original Java Feast pending required; legacy unknown body stays unavailable");pending=Optional.of(new Pending(StrictJson.text(value.get("episode_run_id")),ExactRef.fromJson(value.get("command")),StrictJson.text(value.get("command_body_sha256"))));}
        Optional<Resolved> resolved=Optional.empty();if(!row.get("resolved").isNull()){
            var raw=row.get("resolved");StrictJson.require(raw.isObject(),"complete Java Feast result required");var expected=new java.util.HashSet<>(Set.of("schema","outcome","receipt","command","activity"));
            if(raw.has("lifecycle"))expected.addAll(Set.of("lifecycle","activity_id","actor_character_id"));var value=StrictJson.object(raw,expected);
            StrictJson.require(StrictJson.text(value.get("schema")).equals("xar.java-feast-result/v1"),"complete Java Feast result required");Optional<ActivityOrigin> activity=Optional.empty();
            if(!value.get("activity").isNull()){
                var origin=StrictJson.object(value.get("activity"),Set.of("original_start","final_state"));Optional<FinalRetention> retention=Optional.empty();
                if(!origin.get("final_state").isNull()){
                    var kept=StrictJson.object(origin.get("final_state"),Set.of("state","activity_id","host_character_id"));
                    retention=Optional.of(new FinalRetention(ExactRef.fromJson(kept.get("state")),StrictJson.integer(kept.get("activity_id"),0L,0xFFFF_FFFEL),StrictJson.integer(kept.get("host_character_id"),1L,0xFFFF_FFFEL)));
                }
                activity=Optional.of(new ActivityOrigin(ExactRef.fromJson(origin.get("original_start")),retention));
            }
            var result=new Resolved(ExactRef.fromJson(value.get("receipt")),ExactRef.fromJson(value.get("command")),ActionReceipt.Outcome.valueOf(StrictJson.text(value.get("outcome"))),activity);
            var projection=StrictJson.parse(encode(new Ledger(Optional.empty(),Optional.of(result)))).get("resolved");
            StrictJson.require(projection.equals(value),"Feast terminal projection differs from exact retained origin");resolved=Optional.of(result);
        }
        return new Ledger(pending,resolved);
    }
    private static byte[] encodeInput(Input input) {var row=StrictJson.object().put("schema","xar.java-feast-publication/v2").put("kind",input.kind().name());row.set("previous",input.previous().map(ExactRef::toJson).orElse(null));row.set("command",input.command().map(ExactRef::toJson).orElse(null));row.set("receipt",input.receipt().map(ExactRef::toJson).orElse(null));row.set("initial",input.initial().map(ExactRef::toJson).orElse(null));row.set("plan",input.plan().map(ExactRef::toJson).orElse(null));row.set("final_state",input.finalState().map(ExactRef::toJson).orElse(null));return StrictJson.canonical(row);}
    private static Optional<ExactRef> optional(ObjectNode row,String field) {return row.get(field).isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get(field)));}
    private static Input decodeInput(byte[] raw) {var row=StrictJson.object(StrictJson.parse(raw),Set.of("schema","kind","previous","command","receipt","initial","plan","final_state"));StrictJson.require(StrictJson.text(row.get("schema")).equals("xar.java-feast-publication/v2"),"exact Feast producer input required");return new Input(Kind.valueOf(StrictJson.text(row.get("kind"))),optional(row,"previous"),optional(row,"command"),optional(row,"receipt"),optional(row,"initial"),optional(row,"plan"),optional(row,"final_state"));}
    private static List<ExactRef> evidence(Input input) {return java.util.stream.Stream.of(input.previous(),input.command(),input.receipt(),input.initial(),input.plan(),input.finalState()).flatMap(Optional::stream).toList();}
}
