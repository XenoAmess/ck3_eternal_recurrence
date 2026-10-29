package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;

/** The original three private ART primitives, on the existing Root/coordinator/writer. */
public final class RootArtifactsPrivateActions {
    public static final String COMMAND_SCHEMA="xar.java.artifact-private-original/v1";
    public static final String OBSERVER="xar.java.artifact-private-control/v1";
    private static final Set<Method> METHODS=Set.of(Method.OPEN,Method.CLOSE,Method.PERSONAL_SUBMIT);
    private static final Set<Method> POSTS=Set.of(Method.OPEN_POST,Method.CLOSE_POST,Method.PERSONAL_POST);
    private RootArtifactsPrivateActions(){ }
    public static Set<Method> supportedMethods(){return METHODS;}
    private static OperationKey operation(Method method){return new OperationKey(method.step());}

    /** Factory supplies the identical actual Sources and exact loaded helper source before Core installation. */
    public static final class Prepared {
        private final ArtifactsService.Sources sources;
        private final ExactRef helperSource;
        private final IdentityHashMap<RootRuntimeContext,InstallAttempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        public Prepared(ArtifactsService.Sources actualSources,ExactRef helperSource)throws IOException {
            sources=Objects.requireNonNull(actualSources);this.helperSource=Objects.requireNonNull(helperSource);
            require(sources.enabled().containsAll(METHODS)&&sources.enabled().containsAll(POSTS),"actual three private sources and their independent POST producers required");
            require(helperSource.bytes()>0,"actual private-artifact implementation metadata required");
        }
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        /** ArtifactsService already owns the actual three SOURCE_QUALIFIED_PRIVATE permissions. */
        public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        public Set<Method> supportedMethods(){return METHODS;}
        public synchronized void bindCore(RootApplicationAssembly.Core actual){require(core==null,"private artifacts bind the actual Core once");core=Objects.requireNonNull(actual);}
        public synchronized Installed install(RootRuntimeContext actual,ArtifactsService sameService)throws IOException {
            Objects.requireNonNull(actual);Objects.requireNonNull(sameService);
            require(core!=null&&actual.core()==core&&sameService.sources()==sources,"private artifacts require their identical Core, actual Sources and Service");
            InstallAttempt previous=attempts.get(actual);
            if(previous!=null){if(previous.failure().isPresent())throw new IOException("original private-artifact installation failed; not repeated",previous.failure().orElseThrow());return previous.installed().orElseThrow();}
            require(attempts.size()<64,"bounded private-artifact actual context history exhausted");
            try {Installed installed=new Installed(this,actual,sameService);attempts.put(actual,new InstallAttempt(Optional.of(installed),Optional.empty()));return installed;}
            catch(RuntimeException failure){IOException retained=new IOException("private-artifact actual installation failed",failure);attempts.put(actual,new InstallAttempt(Optional.empty(),Optional.of(retained)));throw retained;}
        }
    }
    private record InstallAttempt(Optional<Installed> installed,Optional<IOException> failure){
        private InstallAttempt{require(installed.isPresent()!=failure.isPresent(),"one retained install result required");}
    }

    /** A canonical command keeps complete original request/frame/inventory DATA; none of these fields is a permit. */
    public static OpportunityJson.Obj commandArguments(ArtifactsService.Selection original) {
        Request request=original.query();require(METHODS.contains(request.method()),"only the three original private ART requests belong here");
        ObjectNode n=StrictJson.object().put("schema",COMMAND_SCHEMA).put("method",request.method().originalName()).put("full_binding_sha256",original.captured().fullBindingSha256());
        n.set("request",ArtifactsCodec.encode(request));n.set("original_frame",original.captured().originalEvidence().toJson());
        if(original.sourceInventory().isPresent())n.put("source_inventory_sha256",original.sourceInventory().orElseThrow());else n.putNull("source_inventory_sha256");
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(n)),"original private ART command");
    }
    private record Arguments(Request request,ExactRef originalFrame,String fullBinding,Optional<String> inventory){ }
    private static Arguments arguments(ActionCommand command){return arguments(command.arguments());}
    private static Arguments arguments(OpportunityJson.Obj actual) {
        ObjectNode n=object(OpportunityJson.toNode(actual));Set<String> fields=new java.util.HashSet<>();n.fieldNames().forEachRemaining(fields::add);
        require(fields.equals(Set.of("schema","method","full_binding_sha256","request","original_frame","source_inventory_sha256")),"private ART canonical arguments differ");
        require(text(n,"schema").equals(COMMAND_SCHEMA),"private ART command version differs");Method method=Method.exact(text(n,"method"));require(METHODS.contains(method),"another ART family cannot borrow the private command");
        Request request=ArtifactsCodec.decode(method.originalName(),n.get("request"));String binding=text(n,"full_binding_sha256");require(binding.matches("[0-9a-f]{64}"),"complete original frame binding required");
        JsonNode inventory=n.get("source_inventory_sha256");require(inventory!=null&&(inventory.isNull()||inventory.isTextual()),"inventory source digest must be explicit text or null");
        Optional<String> digest=inventory.isNull()?Optional.empty():Optional.of(inventory.textValue());digest.ifPresent(value->require(value.matches("[0-9a-f]{64}"),"actual managed inventory digest required"));
        require((method==Method.PERSONAL_SUBMIT)==digest.isEmpty(),"private family inventory-source role differs");
        return new Arguments(request,ExactRef.fromJson(n.get("original_frame")),binding,digest);
    }
    /** Revision is an observation boundary, not a second unresolved-intent identity. */
    public static boolean sameIntent(Request a,Request b){
        if(a.method()!=b.method())return false;ObjectNode left=ArtifactsCodec.encode(a),right=ArtifactsCodec.encode(b);left.remove("expected_revision");right.remove("expected_revision");return same(left,right);
    }
    /** Called only over actual journal receipts reopened from the same canonical state and archive. */
    public static Optional<ActionReceipt> unresolvedOriginal(List<ActionReceipt> actual,String machine,String episode,BigInteger actor) {
        Objects.requireNonNull(actual);Objects.requireNonNull(machine);Objects.requireNonNull(episode);Objects.requireNonNull(actor);
        ActionReceipt unresolved=null;
        for(ActionReceipt receipt:actual) {
            ActionCommand command=receipt.command();if(METHODS.stream().noneMatch(m->operation(m).equals(command.operation()))||receipt.settled())continue;
            if(!command.before().machineId().equals(machine)||!command.before().frame().episodeRunId().equals(episode)||!command.before().frame().identity().player().equals(actor))continue;
            require(unresolved==null||unresolved.command().actionId().equals(command.actionId()),"multiple original private ART obligations remain; no new submission");unresolved=receipt;
        }
        return Optional.ofNullable(unresolved);
    }
    /** Pure gate over the canonical journal material; callers must hold their actual writer Session. */
    public static void requireNoUnresolved(List<ActionReceipt> actual,String machine,String episode,BigInteger actor){require(unresolvedOriginal(actual,machine,episode,actor).isEmpty(),"original private ART pending intent remains; do not submit another open/close/personal command");}
    public static boolean knownNoDispatch(Reply original) {
        require(METHODS.contains(original.method()),"only original private action results can release their client pending intent");
        Facts f=original.facts();if(f.onceIntentConsumed()||f.invoked()||f.needsRecovery())return false;
        String status=text(original.payload().original(),"status");
        return original.method()==Method.PERSONAL_SUBMIT||!Set.of("inventory_pending_or_once_ledger_rejected","inventory_close_pending_or_once_intent_rejected").contains(status);
    }
    public static Request postRequest(Request original,BigInteger currentPublicRevision,BigInteger actualNativeIntent) {
        require(METHODS.contains(original.method()),"original private action required");
        return switch(original.method()) {
            case OPEN->new InventoryPost(Method.OPEN_POST,currentPublicRevision,actualNativeIntent);
            case CLOSE->new InventoryPost(Method.CLOSE_POST,currentPublicRevision,actualNativeIntent);
            case PERSONAL_SUBMIT->new PersonalPost(currentPublicRevision,((PersonalSubmit)original).artifactId(),actualNativeIntent);
            default->throw new IllegalArgumentException("unregistered private ART post");
        };
    }
    /** Both values must first come from the sole strict codec. A latest unrelated native row is never a recovery proof. */
    public static void requireCorrelatedPost(Request original,Reply submitted,Reply independentlyRead) {
        require(submitted.method()==original.method()&&METHODS.contains(original.method()),"different original action owner");
        Method expected=original.method()==Method.OPEN?Method.OPEN_POST:original.method()==Method.CLOSE?Method.CLOSE_POST:Method.PERSONAL_POST;
        require(independentlyRead.method()==expected,"independent post belongs to another private operation");
        BigInteger sequence=submitted.facts().actualIntentSequence().orElseThrow(()->new IllegalArgumentException("original ACK has no native intent sequence; UNKNOWN cannot bind the latest row"));
        require(independentlyRead.facts().actualIntentSequence().orElseThrow().equals(sequence),"independent post changed the actual original native intent sequence");
        require(submitted.facts().onceIntentConsumed()&&independentlyRead.facts().onceIntentConsumed()&&independentlyRead.facts().available()&&independentlyRead.facts().independentDesiredObserved()&&!independentlyRead.facts().needsRecovery(),"independent desired state remains unknown");
        ObjectNode before=submitted.payload().original(),post=independentlyRead.payload().original();
        require(same(object(before.get("before")),object(post.get("before"))),"native post replaced the complete original owning baseline");
        if(original instanceof PersonalSubmit intent) {
            for(String key:List.of("artifact_id","desired_equipped","expected_slot_index","expected_replacing_artifact_id","before_native_revision","before_connection_generation","before_game_pid"))require(sameValue(before.get(key),post.get(key)),"personal post changed frozen owner field "+key);
            require(intent.policyPositive(),"retained private personal policy was not positive");
        }
    }

    public static final class Installed implements RootArtifactsPublicProducts.ActionProducts {
        private final Prepared prepared;private final RootRuntimeContext context;private final ArtifactsService service;
        private final RootDomainInstallation installation;private final ThreadLocal<ArtifactsService.Selection> active=new ThreadLocal<>();
        private Installed(Prepared prepared,RootRuntimeContext context,ArtifactsService service) {
            this.prepared=prepared;this.context=context;this.service=service;
            var actionBindings=new ArrayList<RootExecutableBindings.ActionBinding>();var archived=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
            var preparation=new ActionPorts.PreparationPort(){
                @Override public NativeRequest prepare(ActionCommand command){throw new IllegalStateException("private ART preparation requires the original writer/request scope");}
                @Override public NativeRequest prepare(Session same,ActionCommand command,String requestId){
                    try {context.writer().requireSession(same);ArtifactsService.Selection original=requireActive(command);requireNoPending(same,original.captured());
                        return context.collector().currentOwned(same,identity(),command.deadline(),lease->{
                            require(lease.frame().identity().equals(command.before())&&lease.frame().source().equals(command.source())&&lease.frame().sessionId().equals(command.sessionId()),"private ART physical frame changed before preparation");
                            ArtifactsService.Selection selected=service.select(lease.frame(),original.query(),command.deadline());require(selected.sourceInventory().equals(original.sourceInventory()),"managed inventory sources changed before original INTENT");
                            return service.prepare(selected,requestId);
                        });
                    }catch(IOException failure){throw new UncheckedIOException(failure);}
                }
            };
            for(Method method:METHODS){
                var binding=new NativeEffectRegistry.Binding(operation(method),prepared.helperSource,preparation,this::observe);
                actionBindings.add(new RootExecutableBindings.ActionBinding(binding,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),prepared.helperSource));
                archived.add(new NativeRecordedEvidenceVerifier.Binding(operation(method),prepared.helperSource,this::verifyArchived));
            }
            var pending=new RootDomainIntentPreparation.Binding("artifact-private-original-once/v1",prepared.helperSource,Installed::supports,(same,command)->{
                try {context.writer().requireSession(same);ArtifactsService.Selection original=requireActive(command);requireNoPending(same,original.captured());
                    NativeRequest actual=ActionPreparationScope.requirePrepared(same,command);requirePrepared(command,original,actual);
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            Set<OperationKey> operations=METHODS.stream().map(RootArtifactsPrivateActions::operation).collect(java.util.stream.Collectors.toUnmodifiableSet());
            installation=new RootDomainInstallation("artifact-private-original/v1",List.of(),List.of(),List.of(),actionBindings,List.of(),archived,List.of(),List.of(),List.of(),List.of(pending),operations,List.of(),List.of(),List.of(),List.of(),List.of());
        }
        private static boolean supports(ActionCommand command){return METHODS.stream().anyMatch(m->operation(m).equals(command.operation()));}
        public Set<Method> supportedMethods(){return METHODS;}
        public RootDomainInstallation installation(){return installation;}
        public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        private SessionIdentity identity(){return new SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());}
        private ArtifactsService.Selection requireActive(ActionCommand command) {
            ArtifactsService.Selection original=active.get();require(original!=null,"private ART command escaped its actual Root capture");Arguments args=arguments(command);
            require(command.operation().equals(operation(original.query().method()))&&sameIntent(original.query(),args.request())&&original.query().expectedRevision().equals(args.request().expectedRevision())&&original.captured().identity().equals(command.before())&&original.captured().source().equals(command.source())&&original.captured().sessionId().equals(command.sessionId())&&original.captured().originalEvidence().equals(args.originalFrame())&&original.captured().fullBindingSha256().equals(args.fullBinding())&&original.sourceInventory().equals(args.inventory()),"private ART command changed original request/frame/source/inventory");return original;
        }
        private List<ActionReceipt> history(Session same)throws IOException {context.writer().requireSession(same);return ContinuityActionJournal.receipts(same.head().state(),context.archive().withSession(same));}
        private Optional<ActionReceipt> pending(Session same,Complete current)throws IOException{return unresolvedOriginal(history(same),current.identity().machineId(),current.identity().frame().episodeRunId(),current.identity().frame().identity().player());}
        private void requireNoPending(Session same,Complete current)throws IOException {requireNoUnresolved(history(same),current.identity().machineId(),current.identity().frame().episodeRunId(),current.identity().frame().identity().player());}
        @Override public Reply execute(RootApplicationSession actualRoot,Request request,Instant deadline)throws IOException,InterruptedException {
            require(actualRoot==context.actions()&&context.core()==prepared.core&&METHODS.contains(request.method())&&active.get()==null,"private ART execution crossed actual Root/Core or operation");
            try{return actualRoot.executePublicDecision(deadline,(frame,driver,same)->{
                context.writer().requireSession(same);Optional<ActionReceipt> original=pending(same,frame);
                if(original.isPresent()){
                    ActionReceipt retained=original.orElseThrow();Request old=arguments(retained.command()).request();
                    require(sameIntent(old,request),"different unresolved private ART intent is retained; exact original post is required");
                    return new RootApplicationSession.ReconcilePublicAction<Reply>(retained.command().actionId(),context.archive().withSession(same).receiptReferenceOf(retained));
                }
                ArtifactsService.Selection selected=service.select(frame,request,deadline);active.set(selected);
                String id=ActionIds.forDecision(frame.sessionId(),frame.identity(),"artifact-private:"+same.head().digest()+":"+ActionCodec.sha256(StrictJson.canonical(ArtifactsCodec.encode(request))));
                var expected=new ExpectedPostcondition(1,frame.identity(),frame.source(),OBSERVER,values(request.method()));
                var claims=new Claims(Set.of(),Set.of(),Set.of(frame.identity().frame().identity().player()),Set.of("artifact-private-owner"));
                return new RootApplicationSession.SubmitPublicAction<Reply>(new ActionCommand(id,frame.identity(),frame.source(),frame.sessionId(),operation(request.method()),commandArguments(selected),expected,claims,deadline));
            },(receipt,archive,same)->publication(same,receipt));}finally{active.remove();}
        }
        private void requirePrepared(ActionCommand command,ArtifactsService.Selection original,NativeRequest actual) {
            ObjectNode expected=ArtifactsCodec.nativeFields(original.query(),original.frame(),original.sourceInventory());expected.put("expected_snapshot_revision",original.frame().nativeRevision());
            require(actual.step().equals(command.operation().value())&&actual.requiredCapability().isEmpty()&&actual.preparationEvidence().isEmpty()&&same(expected,object(StrictJson.parse(actual.additionalFields().bytes(),StrictJson.EXPLICIT_MAX_BYTES))),"private ART outbound differs from the sole typed original producer");
        }
        private ArtifactsService.Selection original(ActionCommand command,ActionState.Attempt attempt,ActionPorts.OutcomeArchive archive)throws IOException {
            Arguments args=arguments(command);Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
            require(before.identity().equals(command.before())&&before.source().equals(command.source())&&before.sessionId().equals(command.sessionId())&&before.originalEvidence().equals(args.originalFrame())&&before.fullBindingSha256().equals(args.fullBinding())&&command.operation().equals(operation(args.request().method())),"private ART canonical guard differs from complete original request/frame/source");
            var selection=new ArtifactsService.Selection(before,ArtifactsService.actualFrame(before),args.request(),args.inventory(),command.deadline());requirePrepared(command,selection,attempt.preparedRequest());return selection;
        }
        private NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
            if(!(dispatch instanceof NativeActionPort.AckReceived ack))return NativeEffectRegistry.Projected.pending("private ART original Native ACK/sequence missing; preserve UNKNOWN without resending",List.of(attempt.guard().nativeEvidence()));
            var evidence=new ArrayList<ExactRef>();
            try{return context.withSession(same->{var archive=context.archive().withSession(same);evidence.add(archive.referenceOf(ack));ArtifactsService.Selection original=original(command,attempt,archive);Instant observationDeadline=ActionObservationWindow.deadline(command);
                return context.collector().currentOwned(same,identity(),observationDeadline,lease->{
                    Complete after=lease.frame();requireNativeContinuation(original.captured(),after);Reply submitted=service.decodeAction(original,attempt,ack,ArtifactsService.actualFrame(after));
                    if(knownNoDispatch(submitted)){
                        PlanningReadReceipt probe=probeRead(same,after,original.query(),observationDeadline);evidence.add(archive.readReferenceOf(probe));verifyPostFrames(original.captured(),after,probe,archive);requireProbeOriginals(same,probe,attempt,ack,archive);
                        RawJson basis=noDispatchBasis(command,archive.referenceOf(ack),archive.readReferenceOf(probe));archive.preserveMaterial(basis);ExactRef basisRef=archive.materialReferenceOf(basis);
                        return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),rejection(submitted),basisRef)),Optional.empty());
                    }
                    if(submitted.facts().actualIntentSequence().isEmpty()){
                        PlanningReadReceipt probe=probeRead(same,after,original.query(),observationDeadline);evidence.add(archive.readReferenceOf(probe));verifyPostFrames(original.captured(),after,probe,archive);requireProbeOriginals(same,probe,attempt,ack,archive);
                        return NativeEffectRegistry.Projected.pending("original Native sequence missing; actual current probe is DATA only and cannot bind a latest intent",List.copyOf(evidence));
                    }
                    BigInteger sequence=submitted.facts().actualIntentSequence().orElseThrow();
                    Request post=postRequest(original.query(),after.identity().frame().revision(),sequence);ArtifactsService.Selection selection=service.select(after,post,observationDeadline);
                    var result=context.reads().read(same,service.issue(context.readCatalog(),selection),service.request(selection));
                    if(!(result instanceof PlanningReadResult.Known<?>)){
                        PlanningReadReceipt probe=probeRead(same,after,original.query(),observationDeadline);evidence.add(archive.readReferenceOf(probe));verifyPostFrames(original.captured(),after,probe,archive);requireProbeOriginals(same,probe,attempt,ack,archive);
                        return NativeEffectRegistry.Projected.pending("original POST unavailable; current probe cannot resolve original intent",List.copyOf(evidence));
                    }
                    PlanningReadReceipt read=((PlanningReadResult.Known<?>)result).receipt();evidence.add(archive.readReferenceOf(read));
                    Reply independentlyRead=service.decodeRead(selection,read);requireCorrelatedPost(original.query(),submitted,independentlyRead);
                    verifyPostFrames(original.captured(),after,read,archive);
                    return new NativeEffectRegistry.Projected(new ActionPorts.ControlObserved(new ActionState.ControlApplied(read,OBSERVER,values(original.query().method()))),Optional.empty());
                });
            });}catch(IOException|UncheckedIOException|IllegalArgumentException|IllegalStateException unavailable){return NativeEffectRegistry.Projected.pending("private ART original intent remains UNKNOWN: "+unavailable.getMessage(),evidence.isEmpty()?List.of(attempt.guard().nativeEvidence()):List.copyOf(evidence));}
        }
        private void verifyPostFrames(Complete original,Complete beforeRead,PlanningReadReceipt read,ActionPorts.OutcomeArchive archive)throws IOException {
            NativeRecordedEvidenceVerifier.requireRead(read,archive);Complete before=RootGuardEvidence.loadFrame(read.before().binding(),archive,context.frameLoader());Complete after=RootGuardEvidence.loadFrame(read.after().binding(),archive,context.frameLoader());
            require(before.identity().equals(beforeRead.identity())&&before.fullBindingSha256().equals(beforeRead.fullBindingSha256()),"independent POST is not the actual captured current frame");requireNativeContinuation(original,before);requireNativeContinuation(before,after);
        }
        private PlanningReadReceipt probeRead(Session same,Complete current,Request original,Instant deadline)throws IOException {
            PlanningReadResult<?> result;
            if(original instanceof PersonalSubmit personal){var selected=service.select(current,new ArtifactRead(current.identity().frame().revision(),personal.artifactId()),deadline);result=context.reads().read(same,service.issue(context.readCatalog(),selected),service.request(selected));}
            else {var selected=service.inventorySelection(current,deadline);result=context.reads().read(same,service.inventoryContract(context.readCatalog(),selected),service.inventoryRequest(selected));}
            require(result instanceof PlanningReadResult.Known<?>,"real read frame for original no-dispatch proof unavailable");return ((PlanningReadResult.Known<?>)result).receipt();
        }
        private void requireProbeOriginals(Session same,PlanningReadReceipt read,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,ActionPorts.OutcomeArchive archive)throws IOException {
            context.writer().requireSession(same);NativeRecordedEvidenceVerifier.requireRead(read,archive);requireProbeAfter(read,attempt,ack);
            for(GuardEvidence guard:List.of(read.before().binding(),read.after().binding())) {
                require(guard.origin() instanceof CommandOrigin.Gameplay&&guard.supportingEvidence().size()==1,"private no-dispatch probe requires the original ordinary Root guard; derived/reconciliation authority unavailable");
                RootGuardEvidence.requireHistory(guard,archive,same);RootGuardEvidence.loadFrame(guard,archive,context.frameLoader());
                ExactRef reference=guard.capabilityEvidence();byte[] bytes=context.originals().read(same,reference,StrictJson.EXPLICIT_MAX_BYTES);
                require(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),"no-dispatch probe original HELLO bytes/SHA changed");
                var packet=NativeWire.decode(bytes);require(packet instanceof NativeWire.Hello,"original Native HELLO packet required for both probe guards");var hello=(NativeWire.Hello)packet;
                require(hello.pid()==guard.observed().game().pid()&&hello.connectionGeneration().equals(guard.connectionGeneration())&&hello.gameSha256().equalsIgnoreCase(EXECUTABLE_SHA256)&&hello.buildMatch()&&hello.adapterStatus().equals("ready"),"no-dispatch probe original HELLO/process/build/generation changed");
            }
        }
        private void verifyArchived(Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
            try {ActionState.Attempt attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();ArtifactsService.Selection original=original(receipt.command(),attempt,archive);
                require(receipt.state() instanceof ActionState.Settled,"archived private ART grant must be settled");var settled=(ActionState.Settled)receipt.state();require(settled.dispatch() instanceof NativeActionPort.AckReceived,"private ART settlement lacks original Native ACK");var ack=(NativeActionPort.AckReceived)settled.dispatch();
                if(settled.settlement() instanceof ActionState.Rejected rejected){
                    ObjectNode basis=object(StrictJson.parse(archive.loadMaterial(rejected.originalEvidence()).bytes(),StrictJson.EXPLICIT_MAX_BYTES));
                    require(basis.size()==4&&text(basis,"schema").equals("xar.java.artifact-private-no-dispatch/v1")&&text(basis,"action_id").equals(receipt.command().actionId())&&ExactRef.fromJson(basis.get("ack")).equals(archive.referenceOf(ack)),"private ART no-dispatch original basis changed");
                    PlanningReadReceipt read=archive.loadRead(ExactRef.fromJson(basis.get("read")));Complete current=RootGuardEvidence.loadFrame(read.before().binding(),archive,context.frameLoader());verifyPostFrames(original.captured(),current,read,archive);
                    OperationKey expectedProbe=original.query() instanceof PersonalSubmit?operation(Method.PERSONAL_ITEM):new OperationKey("query-player-inventory-window-v1-private");require(read.request().operation().equals(expectedProbe),"no-dispatch proof borrowed another read operation");
                    context.withSession(same->{context.writer().requireSession(same);require(same.head().digest().equals(head.digest())&&same.head().state().sequence()==head.state().sequence(),"private rejection replay crossed actual locked head");requireProbeOriginals(same,read,attempt,ack,archive);return null;});
                    Reply submitted=service.decodeAction(original,attempt,ack,ArtifactsService.actualFrame(current));require(knownNoDispatch(submitted)&&rejected.reason().equals(rejection(submitted)),"private ART no-dispatch proof changed");return;
                }
                require(settled.settlement() instanceof ActionState.ControlApplied,"private ART cannot grant inferred aggregate/business effects");var control=(ActionState.ControlApplied)settled.settlement();
                require(control.observerSchema().equals(OBSERVER)&&control.actual().equals(values(original.query().method()))&&control.supportingReads().isEmpty(),"private ART control effect contract changed");
                PlanningReadReceipt read=control.read();Complete current=RootGuardEvidence.loadFrame(read.before().binding(),archive,context.frameLoader());verifyPostFrames(original.captured(),current,read,archive);
                Reply submitted=service.decodeAction(original,attempt,ack,ArtifactsService.actualFrame(current));BigInteger sequence=submitted.facts().actualIntentSequence().orElseThrow();
                Request post=postRequest(original.query(),current.identity().frame().revision(),sequence);var selected=new ArtifactsService.Selection(current,ArtifactsService.actualFrame(current),post,original.sourceInventory(),read.request().deadline());
                require(service.request(selected).operation().equals(read.request().operation())&&same(object(OpportunityJson.toNode(service.request(selected).arguments())),object(OpportunityJson.toNode(read.request().arguments()))),"archived private ART post request changed");
                Reply decoded=service.decodeRead(selected,read);requireCorrelatedPost(original.query(),submitted,decoded);
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private Reply publication(Session same,ActionReceipt receipt)throws IOException {
            context.writer().requireSession(same);var archive=context.archive().withSession(same);ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),receipt,archive);
            ActionState.Attempt attempt=ActionTransitions.attempt(receipt.state()).orElseThrow(()->new IOException("private ART original INTENT remains UNKNOWN; "+archive.receiptReferenceOf(receipt).path()));
            NativeActionPort.DispatchOutcome dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow(()->new IOException("private ART original dispatch remains UNKNOWN; do not resend"));
            if(!(dispatch instanceof NativeActionPort.AckReceived ack))throw new IOException("private ART original ACK/sequence unavailable; UNKNOWN retained: "+archive.receiptReferenceOf(receipt).path());
            ArtifactsService.Selection original=original(receipt.command(),attempt,archive);PlanningReadReceipt read=observedRead(receipt,ack,archive);requireProbeOriginals(same,read,attempt,ack,archive);
            Complete after=RootGuardEvidence.loadFrame(read.after().binding(),archive,context.frameLoader());requireNativeContinuation(original.captured(),after);
            Reply normalized=service.decodeAction(original,attempt,ack,ArtifactsService.actualFrame(after));
            return ArtifactsService.publishPrivateAction(normalized,new ArtifactsService.PrivateActionPublication(original.captured(),after,receipt,archive.receiptReferenceOf(receipt),archive.referenceOf(ack),!receipt.settled()));
        }
        private PlanningReadReceipt observedRead(ActionReceipt receipt,NativeActionPort.AckReceived ack,ActionPorts.OutcomeArchive archive)throws IOException {
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied control)return control.read();
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Rejected rejected){
                ObjectNode basis=object(StrictJson.parse(archive.loadMaterial(rejected.originalEvidence()).bytes(),StrictJson.EXPLICIT_MAX_BYTES));
                require(basis.size()==4&&text(basis,"schema").equals("xar.java.artifact-private-no-dispatch/v1")&&text(basis,"action_id").equals(receipt.command().actionId())&&ExactRef.fromJson(basis.get("ack")).equals(archive.referenceOf(ack)),"private original no-dispatch observation basis changed");return archive.loadRead(ExactRef.fromJson(basis.get("read")));
            }
            if(receipt.state() instanceof ActionState.Unknown unknown&&unknown.evidence().size()==2&&unknown.evidence().getFirst().equals(archive.referenceOf(ack)))return archive.loadRead(unknown.evidence().get(1));
            throw new IOException("actual original post/probe read is missing; no post_snapshot_id is invented; UNKNOWN retained");
        }
    }
    /** Existing unique Native chronology; applying an old READ to a later no-dispatch ACK is forbidden. */
    public static void requireProbeAfter(PlanningReadReceipt read,ActionState.Attempt attempt,NativeActionPort.AckReceived ack){NativeRequestChronology.requireSampledAfter(read,attempt,ack);}
    private static String rejection(Reply original){return "artifact-private-no-dispatch:"+original.method().name()+":"+text(original.payload().original(),"status");}
    private static RawJson noDispatchBasis(ActionCommand command,ExactRef ack,ExactRef read){ObjectNode n=StrictJson.object().put("schema","xar.java.artifact-private-no-dispatch/v1").put("action_id",command.actionId());n.set("ack",ack.toJson());n.set("read",read.toJson());return new RawJson(StrictJson.canonical(n));}
    private static List<ExpectedValue> values(Method method){return List.of(new ExpectedBoolean(new FieldKey(switch(method){case OPEN->"artifact.inventory_open_observed";case CLOSE->"artifact.inventory_close_observed";case PERSONAL_SUBMIT->"artifact.personal_inventory_state_observed";default->throw new IllegalArgumentException("not a private ART action");}),true));}
    private static void requireNativeContinuation(Complete original,Complete current) {
        NativeFrame a=ArtifactsService.actualFrame(original),b=ArtifactsService.actualFrame(current);
        require(original.identity().machineId().equals(current.identity().machineId())&&original.source().equals(current.source())&&original.sessionId().equals(current.sessionId())&&a.gamePid()==b.gamePid()&&a.gameCreationFiletime().equals(b.gameCreationFiletime())&&a.actorCharacterId()==b.actorCharacterId()&&a.episodeRunId().equals(b.episodeRunId())&&a.connectionGeneration().equals(b.connectionGeneration())&&a.executableSha256().equals(b.executableSha256())&&b.nativeRevision().compareTo(a.nativeRevision())>=0&&b.dateRaw().compareTo(a.dateRaw())>=0&&b.paused()&&b.mapReady()&&b.alive(),"private native process/owner/generation continuity unavailable; retain UNKNOWN");
    }
    private static ObjectNode object(JsonNode n){require(n instanceof ObjectNode,"validated object required");return (ObjectNode)n;}
    private static String text(ObjectNode n,String key){return StrictJson.text(n.get(key));}
    private static boolean same(ObjectNode a,ObjectNode b){return Arrays.equals(StrictJson.canonical(a),StrictJson.canonical(b));}
    private static boolean sameValue(JsonNode a,JsonNode b){ObjectNode left=StrictJson.object(),right=StrictJson.object();left.set("value",a);right.set("value",b);return same(left,right);}
    private static void require(boolean condition,String detail){StrictJson.require(condition,detail);}
}
