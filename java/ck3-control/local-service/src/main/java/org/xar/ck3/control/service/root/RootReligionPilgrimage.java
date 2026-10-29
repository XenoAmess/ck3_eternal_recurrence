package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage.Observed;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;

/** Original pilgrimage query/UI/Start routes. One actual canonical intent, independent readback, no resend of UNKNOWN. */
public final class RootReligionPilgrimage {
    public static final String OBSERVER="xar.java.pilgrimage-original-control/v1";
    private RootReligionPilgrimage(){ }
    public record Sources(ExactRef implementation,ExactRef decoder,ExactRef activitiesDefinition,ExactRef plannerDefinition,List<ExactRef> closure){
        public Sources{Objects.requireNonNull(implementation);Objects.requireNonNull(decoder);Objects.requireNonNull(activitiesDefinition);Objects.requireNonNull(plannerDefinition);closure=List.copyOf(closure);need(!closure.isEmpty()&&closure.size()<=32,"complete original pilgrimage closure required");}
        public Sources(RootRuntimeDefinitions.Inputs inputs,RootRuntimeNativeOriginals.Bound originals,Clock clock,
                ExactRef implementation,ExactRef decoder,ExactRef activitiesDefinition,ExactRef plannerDefinition,List<ExactRef> closure){
            this(implementation,decoder,activitiesDefinition,plannerDefinition,closure);
        }
        public List<ExactRef> refs(){var refs=new LinkedHashSet<>(closure);refs.add(implementation);refs.add(decoder);refs.add(activitiesDefinition);refs.add(plannerDefinition);return List.copyOf(refs);}
        ReligionTemporalFinance.Sources readSources(boolean activities){return new ReligionTemporalFinance.Sources(activities?activitiesDefinition:plannerDefinition,decoder,closure);}
    }
    public static Prepared ordinary(RootAdditionalDomains.ImplementationMetadata metadata){
        Objects.requireNonNull(metadata);var implementation=metadata.implementation(RootReligionPilgrimage.class);
        var producer=metadata.implementation(ReligionPilgrimage.class);
        return new Prepared(new Sources(implementation,producer,producer,producer,java.util.stream.Stream.of(implementation,producer).distinct().toList()));
    }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Clock clock)throws IOException{
        String prefix="ck3_autonomous_player/src/xar_autoplayer/bridge/";var closure=new ArrayList<ExactRef>();for(String name:List.of("native_driver.py","player_pilgrimage_activities_private_transport.py","player_pilgrimage_planner_private_transport.py","player_pilgrimage_planner_contract.py","activity_feast_stage5_start_private_transport.py","nonwar_private_build.py","version_identity.py"))closure.add(RootReligionSourcesFactory.original(inputs,selected,prefix+name));
        var sources=new Sources(inputs,originals,clock,selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootReligionPilgrimage.class),selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionPilgrimage.class),RootReligionSourcesFactory.original(inputs,selected,prefix+"player_pilgrimage_activities_private_transport.py"),RootReligionSourcesFactory.original(inputs,selected,prefix+"player_pilgrimage_planner_private_transport.py"),closure);return new Prepared(sources);
    }
    private static final class Attempt{Runtime runtime;IOException failure;}
    public static final class Prepared implements RootReligionPublicProducts.ExtensionPrepared{
        private final Sources sources;private RootReligionPublicProducts.SharedKernel kernel;private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();private List<NativePrivateActionPermission> permissions;
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);}public String id(){return "religion-pilgrimage-original/v1";}public List<String> originalMethods(){return List.of(ACTIVITIES_METHOD,QUERY_METHOD,SUBMIT_METHOD);}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public synchronized void bindShared(RootReligionPublicProducts.SharedKernel same){need(kernel==null||kernel==same,"pilgrimage changed shared kernel");kernel=Objects.requireNonNull(same);}
        public synchronized void bindCore(RootApplicationAssembly.Core same){need(core==null||core==same,"pilgrimage changed actual Core");core=Objects.requireNonNull(same);}
        public synchronized List<NativePrivateActionPermission> privatePermissions(){need(kernel!=null,"pilgrimage needs bound shared kernel before permission enumeration");if(permissions==null)permissions=List.of(new NativePrivateActionPermission(new OperationKey(SUBMIT_STEP),PERMISSION,sources.plannerDefinition(),request->validateSubmit(request),kernel.actionQualification()));return permissions;}
        public synchronized RootReligionPublicProducts.ExtensionInstalled install(RootRuntimeContext context)throws IOException{
            if(kernel==null||core==null||context.core()!=core||context.writer()!=core.writer()||context.archive().writer()!=core.writer())throw new IOException("pilgrimage requires identical installed Core/kernel/writer");var prior=attempts.get(context);if(prior!=null){if(prior.failure!=null)throw new IOException("previous partial pilgrimage installation retained, never retry",prior.failure);return new RootReligionPublicProducts.ExtensionInstalled(prior.runtime.installation,prior.runtime);}
            if(attempts.size()>=64)throw new IOException("pilgrimage per-Game installation bound exceeded");var attempt=new Attempt();attempts.put(context,attempt);try{attempt.runtime=new Runtime(context,sources,kernel);return new RootReligionPublicProducts.ExtensionInstalled(attempt.runtime.installation,attempt.runtime);}catch(RuntimeException failure){attempt.failure=new IOException("pilgrimage actual installation failed",failure);throw attempt.failure;}
        }
        private synchronized Runtime installed(RootRuntimeContext context)throws IOException{var attempt=attempts.get(context);if(attempt==null||attempt.runtime==null||attempt.failure!=null)throw new IOException("pilgrimage component was not actually installed in this physical Root");return attempt.runtime;}
        public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context publicContext,PublicBindings registry)throws IOException{
            need(!registry.frozen(),"pilgrimage public registry changed");
            return new RootPublicHandlerProductsFactory.Contribution(bindings(sources.implementation(),request->{try{var deadline=publicContext.clock().instant().plus(timeout(request,request.method().name().equals(SUBMIT_METHOD)?publicContext.actionTimeout():publicContext.observationTimeout()));return publicContext.withCurrent(root->{var runtime=installed(publicContext.installed(root).context());
                if(request.method().name().equals(SUBMIT_METHOD))return root.executePublicDecision(deadline,(frame,known,same)->runtime.decide(same,frame,ReligionPilgrimage.Request.from(request),deadline),(receipt,archive,same)->new ReligionContract.Response(request.method(),runtime.result(same,receipt,archive)));
                return root.withPublicObservation(deadline,(frame,known,same)->runtime.invoke(same,new ReligionService.ActualFrame(frame,runtime.context.transport().originalHello(),deadline),request));
            });}catch(IOException failure){throw new UncheckedIOException(failure);}}),List.of(),List.of());
        }
    }
    static List<McpExecutableDirectory.DirectBinding<?,?>> bindings(ExactRef source,PublicRoutes.Handler<ReligionContract.Request,ReligionContract.Response> actual){return List.of(ACTIVITIES_METHOD,QUERY_METHOD,SUBMIT_METHOD).stream().<McpExecutableDirectory.DirectBinding<?,?>>map(name->new McpExecutableDirectory.DirectBinding<>(name,PublicMcpBindings.Kind.DRIVER_DIRECT,ReligionContract.Request.class,ReligionContract.Response.class,actual,call->{need(call.name().equals(name),"pilgrimage public identity differs");var request=ReligionCodec.decode(name,call.arguments().objectOrEmpty());if(!name.equals(ACTIVITIES_METHOD))ReligionPilgrimage.Request.from(request);return request;},response->PublicMcpDirectory.CallResult.fromBusinessJson(ReligionCodec.encode(response)),new PublicRoutes.Target(Runtime.class.getName(),name.equals(SUBMIT_METHOD)?"decide":"invoke",source))).toList();}
    private record Verified(Frame before,ReligionPilgrimage.Request request,PlanningReadReceipt independent,Readback verification){ }
    public static final class Runtime implements ReligionService.Component{
        private final RootRuntimeContext context;private final Sources sources;private final RootReligionPublicProducts.SharedKernel kernel;
        private final RootReadContractCatalog.Family<ReadInput,Observed> activities,planner;private final RootDomainInstallation installation;
        private final RootExecutableBindings.ActionBinding actionBinding;
        private final NativeRecordedEvidenceVerifier.Binding archivedBinding;
        private Runtime(RootRuntimeContext context,Sources sources,RootReligionPublicProducts.SharedKernel kernel){
            this.context=context;this.sources=sources;this.kernel=kernel;
            activities=family(true);planner=family(false);
            var effect=new NativeEffectRegistry.Binding(new OperationKey(SUBMIT_STEP),sources.implementation(),command->{try{requireCommand(command);var request=new NativeRequest(SUBMIT_STEP,Optional.empty(),new RawJson(OpportunityJson.encode(command.arguments())));validateSubmit(request);return request;}catch(IOException failure){throw new UncheckedIOException(failure);}},this::observe);
            actionBinding=new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.decoder());
            archivedBinding=new NativeRecordedEvidenceVerifier.Binding(new OperationKey(SUBMIT_STEP),sources.implementation(),(head,receipt,archive)->verifyArchived(receipt,archive));
            installation=new RootDomainInstallation("religion-pilgrimage-original/v1",List.of(),List.of(),List.of(activities,planner),List.of(actionBinding),List.of(),List.of(archivedBinding),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        private RootReadContractCatalog.Family<ReadInput,Observed> family(boolean isActivities){return new RootReadContractCatalog.Family<>("religion-original-pilgrimage-"+(isActivities?"activities":"planner")+"/v1",ReadInput.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),isActivities?sources.activitiesDefinition():sources.plannerDefinition(),sources.decoder(),selected->{need((selected.selection() instanceof Activities)==isActivities,"pilgrimage family selector changed");return raw(selectionFields(selected.selection()));},selected->new OperationKey(selected.selection().step()),selected->{need((selected.selection() instanceof Activities)==isActivities,"pilgrimage family selector changed");return ReligionPilgrimage.contract(selected.selection(),sources.readSources(isActivities),kernel.readAdmission()::verify);});}
        public RootDomainInstallation installation(){return installation;}public List<String> methods(){return List.of(ACTIVITIES_METHOD,QUERY_METHOD);}
        /** Same installed objects only. These accessors mint no action, permission, observation or history. */
        public RootExecutableBindings.ActionBinding actionBinding(){return actionBinding;}
        public NativeRecordedEvidenceVerifier.Binding archivedBinding(){return archivedBinding;}
        public void requireContext(RootRuntimeContext actual)throws IOException{
            if(actual!=context||actual.core()!=context.core()||actual.writer()!=context.writer()||actual.archive()!=context.archive())throw new IOException("pilgrimage control runtime crossed its identical installed context");
            if(installation.actions().size()!=1||installation.actions().getFirst()!=actionBinding||installation.archived().size()!=1||installation.archived().getFirst()!=archivedBinding
                    ||actual.bindings().actualActionBinding(actionBinding.effect().operation()).orElse(null)!=actionBinding.effect()
                    ||actual.bindings().actualArchivedVerifier(archivedBinding.operation()).orElse(null)!=archivedBinding)throw new IOException("pilgrimage control lost its original installed action/replay identity");
        }
        /** Shape/ownership selector for the central zero-business ControlApplied consumer; it never proves an outcome. */
        public boolean matchesControl(ActionCommand command)throws IOException{
            Objects.requireNonNull(command);if(!command.operation().equals(actionBinding.effect().operation()))return false;
            requireContext(context);requireCommand(command);return true;
        }
        public ReligionContract.Response invoke(Session same,ReligionService.ActualFrame actual,ReligionContract.Request request){
            try{context.writer().requireSession(same);requireFrame(actual.frame());need(actual.frame().identity().frame().revision().equals(request.expectedRevision()),"pilgrimage public revision changed");ReadSelection selected=request.method().name().equals(ACTIVITIES_METHOD)?new Activities(request.expectedRevision()):new PlannerRead(ReligionPilgrimage.Request.from(request));var value=read(same,actual,selected);return new ReligionContract.Response(request.method(),raw(value.value().publicResult()));}catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private PlanningReadResult.Known<Observed> read(Session same,ReligionService.ActualFrame actual,ReadSelection selected){var scope=Frame.from(actual.frame().identity(),actual.frame().connectionGeneration(),actual.hello());var contract=context.readCatalog().issue(selected instanceof Activities?activities:planner,new ReadInput(selected,scope));return ReligionService.readKnown(context.reads(),context.archive(),same,contract,actual,selectionFields(selected));}
        public RootApplicationSession.PublicActionDecision<ReligionContract.Response> decide(Session same,Complete complete,ReligionPilgrimage.Request request,Instant deadline)throws IOException{
            context.writer().requireSession(same);requireFrame(complete);need(request.operation().submit(),"public action requires original submit operation");Frame frame=Frame.from(complete.identity(),complete.connectionGeneration(),context.transport().originalHello());String id=intentId(frame,request);var archive=context.archive().withSession(same);var existing=ContinuityActionJournal.lookup(same.head().state(),id,archive);
            if(existing.isPresent()){var receipt=existing.orElseThrow();requireCommand(receipt.command());var previous=validateSubmit(new NativeRequest(SUBMIT_STEP,Optional.empty(),new RawJson(OpportunityJson.encode(receipt.command().arguments()))));need(previous.operation()==request.operation()&&previous.province().equals(request.province())&&previous.option()==request.option()&&previous.reserves().equals(request.reserves()),"existing pilgrimage intent has another original body");return new RootApplicationSession.ReconcilePublicAction<>(id,archive.receiptReferenceOf(receipt));}
            need(frame.publicRevision().equals(request.expectedRevision()),"new pilgrimage action requires current expected public revision");return new RootApplicationSession.SubmitPublicAction<>(controlCommand(id,complete,frame,request,deadline));
        }
        private NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
            if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return NativeEffectRegistry.Projected.pending("pilgrimage original result absent; never resend submit",List.of(attempt.guard().nativeEvidence()));
            try{requireCommand(command);ack.custody().orElseThrow().verify(ack,attempt.guard());var before=Frame.from(command.before(),attempt.guard().connectionGeneration(),context.transport().originalHello());var request=validateSubmit(attempt.preparedRequest()).at(before);submissionResult(ack.originalResultToken().orElseThrow(),before,request);
                return context.withSession(same->{var identity=new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());return context.collector().currentOwned(same,identity,ActionObservationWindow.deadline(command),lease->{var complete=lease.frame();requireFrame(complete);need(complete.identity().frame().identity().dateRaw().equals(before.date())&&complete.identity().frame().identity().player().equals(before.actor()),"pilgrimage post actor/date changed");Operation op=request.operation()==Operation.START?Operation.POST:Operation.READ;var selected=new PlannerRead(new ReligionPilgrimage.Request(op,complete.identity().frame().revision(),BigInteger.ZERO,0,request.option(),false,Reserves.zero(),BigDecimal.valueOf(30)));var independent=read(same,new ReligionService.ActualFrame(complete,context.transport().originalHello(),ActionObservationWindow.deadline(command)),selected);var archive=context.archive().withSession(same);var verified=verify(command,attempt,ack,independent.receipt(),archive);
                    if(verified.verification()==Readback.PENDING)return NativeEffectRegistry.Projected.pending("pilgrimage independent ledger/UI result remains pending; canonical intent consumed",List.of(archive.readReferenceOf(independent.receipt())));
                    if(verified.verification()==Readback.REJECTED){var proof=StrictJson.object().put("schema","xar.java.pilgrimage-original-rejection/v1");proof.set("independent_read",archive.readReferenceOf(independent.receipt()).toJson());var original=archive.preserveMaterial(raw(proof));return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"native_pilgrimage_operation_rejected",original)),Optional.empty());}
                    var control=new ActionState.ControlApplied(independent.receipt(),OBSERVER,actualValues(request.operation()));ActionEffects.validate(command,attempt,ack,control);return new NativeEffectRegistry.Projected(new ActionPorts.ControlObserved(control),Optional.empty());
                });});
            }catch(IOException|IllegalArgumentException|IllegalStateException failure){return NativeEffectRegistry.Projected.pending("pilgrimage postread unresolved: "+failure.getMessage(),List.of(attempt.guard().nativeEvidence()));}
        }
        private Verified verify(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,PlanningReadReceipt read,ActionPorts.OutcomeArchive archive)throws IOException{
            requireCommand(command);ack.custody().orElseThrow().verify(ack,attempt.guard());NativeRecordedEvidenceVerifier.requireRead(read,archive);NativeRequestChronology.requireSampledAfter(read,attempt,ack);need(read.request().source().equals(command.source())&&read.request().sessionId().equals(command.sessionId())&&read.request().before().game().equals(command.before().game())&&read.request().before().frame().episodeRunId().equals(command.before().frame().episodeRunId()),"pilgrimage independent read source/episode differs");Frame after=Frame.from(read);Frame before=new Frame(after.build(),command.before().frame().revision(),command.before().frame().identity().nativeRevision(),command.before().frame().identity().dateRaw(),command.before().frame().identity().player(),command.before().game().pid(),attempt.guard().connectionGeneration(),command.before().frame().snapshotId(),command.before().frame().episodeRunId());need(after.date().equals(before.date())&&after.actor().equals(before.actor())&&after.generation().equals(before.generation()),"pilgrimage independent actor/date/generation changed");var request=validateSubmit(attempt.preparedRequest()).at(before);var selected=new PlannerRead(new ReligionPilgrimage.Request(request.operation()==Operation.START?Operation.POST:Operation.READ,after.publicRevision(),BigInteger.ZERO,0,request.option(),false,Reserves.zero(),BigDecimal.valueOf(30)));
            var observed=ReligionPilgrimage.decode(read,selected);var verification=classifyReadback(ack.originalResultToken().orElseThrow(),before,request,observed);
            return new Verified(before,request,read,verification);
        }
        private Verified verifyArchived(ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
            try{need(receipt.state() instanceof ActionState.Settled,"settled original pilgrimage receipt required");var settled=(ActionState.Settled)receipt.state();need(settled.dispatch() instanceof NativeActionPort.AckReceived ack&&ack.nativeOk(),"original successful native pilgrimage response required");var ack=(NativeActionPort.AckReceived)settled.dispatch();PlanningReadReceipt read;
                if(settled.settlement() instanceof ActionState.ControlApplied control){read=control.read();var verified=verify(receipt.command(),settled.attempt(),ack,read,archive);need(verified.verification()==Readback.UI_OBSERVED||verified.verification()==Readback.START_IDENTITY_OBSERVED,"pilgrimage control has no independent native result");need(control.supportingReads().isEmpty()&&control.observerSchema().equals(OBSERVER)&&control.actual().equals(actualValues(verified.request().operation())),"pilgrimage original control changed");ActionEffects.validate(receipt.command(),settled.attempt(),ack,control);return verified;}
                need(settled.settlement() instanceof ActionState.Rejected,"original pilgrimage must be control or native rejection");var rejected=(ActionState.Rejected)settled.settlement();var proof=obj(archive.loadMaterial(rejected.originalEvidence()));exact(proof,"schema independent_read");eq(proof,"schema","xar.java.pilgrimage-original-rejection/v1");read=archive.loadRead(ExactRef.fromJson(proof.get("independent_read")));var verified=verify(receipt.command(),settled.attempt(),ack,read,archive);need(verified.verification()==Readback.REJECTED&&rejected.requestId().equals(settled.attempt().requestId()),"pilgrimage rejection lost original native observation");return verified;
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        public RawJson result(Session same,ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException{
            context.writer().requireSession(same);Verified verified;
            if(receipt.state() instanceof ActionState.Unknown unknown){need(unknown.attempt().isPresent()&&unknown.dispatch().orElse(null) instanceof NativeActionPort.AckReceived&&unknown.evidence().size()==1,"pilgrimage original ACK/postread unavailable; UNKNOWN retained without retry");var ack=(NativeActionPort.AckReceived)unknown.dispatch().orElseThrow();need(ack.nativeOk(),"original pilgrimage native result unavailable");verified=verify(receipt.command(),unknown.attempt().orElseThrow(),ack,archive.loadRead(unknown.evidence().getFirst()),archive);}
            else verified=verifyArchived(receipt,archive);
            return raw(publicSubmission(receipt.ack().orElseThrow().originalResultToken().orElseThrow(),verified.before(),verified.request(),receipt.ack().orElseThrow().requestId(),verified.independent().after().binding().observed().frame().snapshotId()));
        }
        private void requireCommand(ActionCommand command)throws IOException{controlContract(command);need(command.source().equals(context.source())&&command.sessionId().equals(context.game().sessionId())&&command.before().game().equals(context.game().generation()),"pilgrimage command crossed actual runtime source/Game/session");}
        private void requireFrame(Complete frame){need(frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId())&&frame.identity().game().equals(context.game().generation()),"pilgrimage frame crossed same actual installed runtime");}
    }
    /** Shared pure producer for the existing canonical command. Runtime still owns source qualification and submission. */
    static ActionCommand controlCommand(String id,Complete complete,Frame frame,ReligionPilgrimage.Request request,Instant deadline){
        var actual=complete.identity();need(frame.publicRevision().equals(actual.frame().revision())&&frame.nativeRevision().equals(actual.frame().identity().nativeRevision())&&frame.date().equals(actual.frame().identity().dateRaw())&&frame.actor().equals(actual.frame().identity().player())&&frame.pid()==actual.game().pid()&&frame.generation().equals(complete.connectionGeneration())&&frame.snapshot().equals(actual.frame().snapshotId())&&frame.episode().equals(actual.frame().episodeRunId()),"pilgrimage pure command source frame differs from the actual Complete");
        var args=OpportunityJson.object(OpportunityJson.parse(raw(submitFields(request,frame)).bytes()),"pilgrimage submit arguments");
        var expected=new ExpectedPostcondition(1,actual,complete.source(),OBSERVER,actualValues(request.operation()));
        return new ActionCommand(id,actual,complete.source(),complete.sessionId(),new OperationKey(SUBMIT_STEP),args,expected,new Claims(Set.of(),Set.of(),Set.of(frame.actor()),Set.of("original-pilgrimage-process-ledger")),deadline);
    }
    /** Pure original command contract; source and installed-context qualification remain with Runtime. */
    static NativeSubmit controlContract(ActionCommand command){
        Objects.requireNonNull(command);need(command.origin() instanceof CommandOrigin.Gameplay&&command.expectation() instanceof CommandExpectation.Gameplay,"pilgrimage control requires its original gameplay phase");
        need(command.operation().value().equals(SUBMIT_STEP),"not the installed original pilgrimage submit");
        var parsed=validateSubmit(new NativeRequest(SUBMIT_STEP,Optional.empty(),new RawJson(OpportunityJson.encode(command.arguments()))));
        need(parsed.expectedDate().equals(command.before().frame().identity().dateRaw())&&parsed.expectedActor().equals(command.before().frame().identity().player()),"pilgrimage original request changed its command source frame");
        need(command.expected().observerSchema().equals(OBSERVER)&&command.expected().values().equals(actualValues(parsed.operation())),"pilgrimage control changed its exact typed observer contract");
        need(command.claims().armyIds().isEmpty()&&command.claims().allyCharacterIds().isEmpty()&&command.claims().characterIds().equals(Set.of(parsed.expectedActor()))&&command.claims().commitmentKeys().equals(Set.of("original-pilgrimage-process-ledger")),"pilgrimage control changed its original resource custody");
        return parsed;
    }
    public record ReadInput(ReadSelection selection,Frame frame){public ReadInput{Objects.requireNonNull(selection);Objects.requireNonNull(frame);need(selection.expectedRevision().equals(frame.publicRevision()),"pilgrimage read selector source revision differs");}}
    private static List<ExpectedValue> actualValues(Operation operation){return List.of(new ExpectedText(new FieldKey("operation"),operation.wire()),new ExpectedBoolean(new FieldKey("native_control_observed"),true));}
    private static String intentId(Frame frame,ReligionPilgrimage.Request request){var value=StrictJson.object().put("episode",frame.episode()).put("pid",frame.pid()).put("generation",frame.generation().toString()).put("actor",frame.actor()).put("public_revision",request.expectedRevision().toString()).put("operation",request.operation().wire()).put("province",request.province()).put("option",request.option().key());var resources=value.putArray("reserves");request.reserves().values().forEach(resources::add);return "pilgrimage-original:"+ActionCodec.sha256(raw(value).bytes());}
}
