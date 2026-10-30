package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.FixtureStartupHandler;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContextRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventoutcome.RegisteredEventMaterial;
import org.xar.ck3.control.wave2.events.eventmaterial.RiteGrowthMaterial;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Concrete event installation for one physical Game, using the sole Root writer and original read contracts. */
public final class EventRuntimeInstaller {
    public record Sources(ExactRef installer,ExactRef windowRead,ExactRef windowDecoder,ExactRef windowService,
            ExactRef religionReadDecoder,PlayerReligionContextRead.Sources religionSources,ExactRef policies,
            ExactRef registeredCore,ExactRef nativeEffects,ExactRef nativeEffectsDecoder,
            ExactRef actionPreparation,ExactRef pendingMux,ExactRef armyMaterial,ExactRef mandatoryChoice) {
        public Sources {
            Objects.requireNonNull(religionSources);
            for(ExactRef ref:List.of(installer,windowRead,windowDecoder,windowService,religionReadDecoder,policies,
                    registeredCore,nativeEffects,nativeEffectsDecoder,actionPreparation,pendingMux,armyMaterial,mandatoryChoice))
                StrictJson.require(ref.bytes()>0,"actual selected event producer/consumer source required");
        }
    }
    /** These are the canonical complete Strengths objects from the actual Army installation. */
    public record ArmySources(ArmyStrengthsContracts contracts,ArmyStrengthsPipeline pipeline,ArmyStrengthsService.Current current,ArmyForecastReads forecasts) {
        public ArmySources { Objects.requireNonNull(contracts);Objects.requireNonNull(pipeline);Objects.requireNonNull(current);Objects.requireNonNull(forecasts);contracts.requireCompleteRich();pipeline.requireComplete(); }
    }
    /** Pre-Core immutable definitions. Events have no mutable DomainBodies slot; their real state is the incident journal. */
    public static final class Prepared {
        private final Sources sources;
        private final EventSourceReadContext eventSources;
        private final RegisteredEventKnowledge knowledge;
        private RootApplicationAssembly.Core core;
        public Prepared(Sources sources,EventSourceReadContext actualEventSources)throws IOException {
            this.sources=Objects.requireNonNull(sources);eventSources=Objects.requireNonNull(actualEventSources);
            knowledge=RegisteredEventKnowledge.load();
        }
        public Sources sources() { return sources; }
        public EventSourceReadContext eventSources() { return eventSources; }
        public synchronized void bindCore(RootApplicationAssembly.Core actual) {
            StrictJson.require(core==null,"event definitions bind the sole Core exactly once");
            Objects.requireNonNull(actual);StrictJson.require(actual.archive().writer()==actual.writer(),"event archive/writer identity differs");core=actual;
        }
        /** Root installs this exact private read permission before opening the actual native transport. */
        public List<NativePrivateActionPermission> privatePermissions(NativePrivateActionPermission.QualificationVerifier actual) {
            Objects.requireNonNull(actual);
            return List.of(new NativePrivateActionPermission(PlayerReligionContextRead.OPERATION,PlayerReligionContextRead.PERMISSION,
                    sources.religionSources().pythonProducer(),request->{
                        StrictJson.require(request.requiredCapability().isEmpty()
                                &&OpportunityJson.object(OpportunityJson.parse(request.additionalFields().bytes()),"religion native arguments").members().isEmpty(),
                                "the original current-player religion private query takes no additional arguments");
                    },actual));
        }
        public EventRuntimeInstaller install(RootRuntimeContext actual,KnownInteractionsRuntimeInstaller sameKnown,
                RootIncidentRuntime sameIncidents,ArmySources sameArmy,
                OrdinaryCorePolicy.CommandBinding sameSharedBinding)throws IOException {
            synchronized(this){StrictJson.require(core!=null&&actual.core()==core,"event installation requires its exact once-bound Core");}
            StrictJson.require(eventSources.machineId().equals(actual.game().machineId()),"event source configuration belongs to another physical machine");
            // Re-open all actual roots and grants for every physical Game; no previous Game's trusted object is retained.
            TrustedEventSourceContext trusted=TrustedEventSourceContext.open(eventSources);
            actual.game().launchPlan().sources().requireLoadedClass(EventWarEntryReadBindings.class);
            for(Class<?> type:List.of(PendingUiEvent.class,PendingUiEventPreparation.class,NativeEffectSnapshots.class,RootMandatoryChoiceRuntime.class))
                actual.game().launchPlan().sources().requireLoadedClass(type);
            return new EventRuntimeInstaller(actual,sources,knowledge,trusted,eventSources,sameKnown,sameIncidents,sameArmy,sameSharedBinding,actual.game().nativeTransport());
        }
    }

    private final RootRuntimeContext context;
    private final Sources sources;
    private final RootIncidentRuntime incidents;
    private final RegisteredEventKnowledge knowledge;
    private final TrustedEventSourceContext trusted;
    private final EventSourceReadContext eventSources;
    private final KnownInteractionsRuntimeInstaller sameKnown;
    private final ThreadLocal<PendingUiEvent.Source> privateEventSource=new ThreadLocal<>();
    /** Borrowed only inside the actual Source callback. This never outlives its physical read lease. */
    private final ThreadLocal<PendingUiEvent.Current> privateReadCurrent=new ThreadLocal<>();
    private final ThreadLocal<QualifiedFixtureScope> fixtureEventSource=new ThreadLocal<>();
    private final ThreadLocal<ReadinessAuthority.LeaseSnapshot> fixtureReadCurrent=new ThreadLocal<>();
    private final ReadContract<EventPolicies.ReadPublication> window;
    private final EventWindowService windowService;
    private final RootMandatoryChoiceRuntime mandatoryChoice;
    private final PlayerReligionContextRead religion;
    private final ArmyStrengthsMaterialQuery armyMaterial;
    private final NativeEventEffects.MaterialQueries material;
    private final NativeEventEffects effects;
    private final RootPendingInteractionEffects pending;
    private final RootExecutableBindings.Family<EventActionPreparation.OptionNumber> options;
    private final NativeEventPostconditionPort nativeExpectations;
    private final EventPolicies.NativeExpectationPort expectations;
    private final List<EventReadBinding<?>> eventReads;
    private final RegisteredEventCore registered;
    private final RegisteredEventCore.ContextValidator validator;
    private final RootDomainInstallation installation;

    private EventRuntimeInstaller(RootRuntimeContext context,Sources sources,RegisteredEventKnowledge knowledge,
            TrustedEventSourceContext trusted,EventSourceReadContext eventSources,KnownInteractionsRuntimeInstaller sameKnown,RootIncidentRuntime sameIncidents,
            ArmySources sameArmy,OrdinaryCorePolicy.CommandBinding sameSharedBinding,NativeGameTransport sameTransport) {
        this.context=Objects.requireNonNull(context);this.sources=Objects.requireNonNull(sources);incidents=Objects.requireNonNull(sameIncidents);
        this.knowledge=Objects.requireNonNull(knowledge);this.trusted=Objects.requireNonNull(trusted);this.eventSources=Objects.requireNonNull(eventSources);
        this.sameKnown=Objects.requireNonNull(sameKnown);Objects.requireNonNull(sameArmy);Objects.requireNonNull(sameSharedBinding);
        sameKnown.bindIncidents(incidents);
        window=EventWindowRead.contractForCapabilities(sources.windowRead(),this::admit,sameTransport.diagnostics().originalHello().map(observed->java.util.Set.copyOf(observed.original().capabilities())).orElse(java.util.Set.of()));
        windowService=new EventWindowService(context.reads(),window,this::currentWindow,receipt ->
                org.xar.ck3.control.nativebridge.capabilities.events.EventOptionLocatorDiagnostics.project(
                        org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnosticsCapture.capture(
                                sameTransport.pipeName(),sameTransport.diagnostics(),Optional.empty()),receipt));
        mandatoryChoice=new RootMandatoryChoiceRuntime(context,sources.mandatoryChoice(),this::admit,eventSources,incidents);
        religion=new PlayerReligionContextRead(context.reads(),sources.religionSources(),(pins,request)->admit(request));
        StrictJson.require(window.hasPureReplay()&&religion.contract().hasPureReplay(),"actual event/religion contracts must explicitly install original-only replay");
        armyMaterial=new ArmyStrengthsMaterialQuery(sameArmy.contracts(),sameArmy.pipeline(),sameArmy.current(),context::readCatalog,
                (original,maximum)->context.withSession(same->context.archive().preserveArtifact(same,original,maximum)));
        var religionMaterial=new NativeEventEffects.MaterialQuery<>(religion.contract(),
                value->new RawJson(StrictJson.canonical(PlayerReligionContextRead.flattened(value))),ignored->empty());
        material=new NativeEventEffects.MaterialQueries(Optional.of(armyMaterial),Optional.of(religionMaterial));
        var snapshots=new NativeEffectSnapshots(()->context.adopted().observations(),context.archive(),context.frameLoader(),this::privateEventAfter);
        nativeExpectations=new NativeEventPostconditionPort(snapshots.eventReads());
        effects=new NativeEventEffects(snapshots,context.reads(),(NativeEventEffects.MaterialQuerySelection)original->
                privateEventSource.get()!=null||privatePendingCommand(original)?new NativeEventEffects.MaterialQueries(Optional.empty(),Optional.empty()):material,incidents.observedAfter());
        pending=new RootPendingInteractionEffects(sameKnown.actualEffects(),effects,material,context.frameLoader(),
                new RootPendingInteractionEffects.Sources(sources.pendingMux(),sameKnown.sources().effects(),sources.nativeEffects()));
        options=new RootExecutableBindings.Family<>("native-event-option-v1",EventActionPreparation.OptionNumber.class,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(EventActionPreparation.EVENT_CAPABILITY),
                sources.actionPreparation(),sources.nativeEffectsDecoder(),sources.nativeEffects(),EventActionPreparation::encode,
                EventActionPreparation.OptionNumber::operation,number->{
                    OperationKey operation=number.operation();
                    var binding=new NativeEffectRegistry.Binding(operation,sources.actionPreparation(),EventActionPreparation::prepare,effects);
                    var action=new RootExecutableBindings.ActionBinding(binding,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                            Optional.of(EventActionPreparation.EVENT_CAPABILITY),sources.nativeEffectsDecoder());
                    return new RootExecutableBindings.IssuedAction(action,NativeEventEffects.archivedVerifier(operation,sources.nativeEffects(),context.frameLoader(),material));
                });
        expectations=(request,operation,plan,trait)-> {
            StrictJson.require(NativeEventEffects.supports(operation),"non-event operations must use the actual shared command preparer, not event expected-value reconstruction");
            if(operation.value().matches("select-event-option-[1-9][0-9]{0,8}"))
                context.bindings().issue(options,EventActionPreparation.option(operation));
            return nativeExpectations.expected(request,operation,plan,trait);
        };
        var windowMaterial=new NativeEventEffects.MaterialQuery<>(window,value->new RawJson(OpportunityJson.encode(value.result())),value->value);
        var windowBinding=new EventReadBinding<>(windowMaterial,(request,value)->value);
        var religionBinding=new EventReadBinding<>(religionMaterial,(request,value,actualEncoded)-> {
            OpportunityJson.Obj result=object(actualEncoded);
            var observed=RiteGrowthMaterial.observe(StrictJson.parse(actualEncoded.bytes()),DriverJson.toNode(request.observations().snapshot()));
            var detached=OpportunityJson.parse(RiteGrowthMaterial.encode(observed));
            return new EventPolicies.ReadPublication(result,Optional.of(request.observations().snapshot().with(RiteGrowthMaterial.SNAPSHOT_FIELD,detached)));
        });
        var armyBinding=new EventReadBinding<>(armyMaterial,(request,value,actualEncoded)-> {
            OpportunityJson.Obj result=object(actualEncoded);
            return new EventPolicies.ReadPublication(result,Optional.empty());
        });
        var pendingBinding=EventReadBinding.actualReceipt(sameKnown.definitions().pendingQuery(),
                request->PendingInteractionReadArguments.current(sameKnown.current(request)),
                known->new EventPolicies.ReadPublication(InteractionReadPublications.pending(known),Optional.empty()));
        var savedWarEntry=new EventWarEntryReadBindings(sameArmy.forecasts(),context::readCatalog,window,Objects.requireNonNull(sameTransport),context.archive(),this::borrowedSession);
        var mandatoryBinding=EventReadBinding.actualReceipt(mandatoryChoice.query(),request->request.observations().snapshot(),
                known->known.value());
        var fixedWindows=EventReadBinding.actualReceiptFamily(new OperationKey("query-war-results-window-v1"),
                operation->Set.of("query-war-results-window-v1","query-war-declared-overview-v1").contains(operation.value()),this::fixedWindowRead);
        eventReads=List.of(windowBinding,pendingBinding,armyBinding,religionBinding,savedWarEntry.binding(),mandatoryBinding,fixedWindows);
        validator=EventWindowService.validator(this::build);
        registered=new RegisteredEventCore(knowledge,context.reads(),operation->eventReads.stream().filter(row->row.supports(operation)).findFirst(),
                validator,RegisteredEventMaterial::plan,RegisteredEventCore.exactSourcePhases(),
                (request,operation,args,plan,purpose,domain)-> {
                    if(!operation.value().matches("select-event-option-[1-9][0-9]{0,8}"))return sameSharedBinding.propose(request,operation,args,plan,purpose,domain);
                    var expected=expectations.expected(request,operation,plan,Optional.empty());
                    if(expected.isEmpty())return new OrdinaryCorePolicy.MissingHandler("the original event instance is unavailable to its actual independent observer");
                    String id=ActionIds.forDecision(request.sessionId(),request.before(),operation.value()+":"+ActionCodec.sha256(DriverJson.encode(args)));
                    return new OrdinaryCorePolicy.Prepared(new ActionCommand(id,request.before(),request.source(),request.sessionId(),operation,args,
                            expected.orElseThrow(),foregroundClaims(request),request.deadline()));
                },incidents.capturePort());
        List<RootExecutableBindings.ActionBinding> actions=new ArrayList<>();
        actions.add(mandatoryChoice.action());
        for(var binding:pending.bindings())actions.add(new RootExecutableBindings.ActionBinding(binding,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("game.command."+binding.operation().value()),sources.pendingMux()));
        OperationKey block=new OperationKey("block-pending-character-interaction");
        actions.add(new RootExecutableBindings.ActionBinding(new NativeEffectRegistry.Binding(block,sources.actionPreparation(),EventActionPreparation::prepare,effects),
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of("game.command."+block.value()),sources.nativeEffectsDecoder()));
        List<NativeRecordedEvidenceVerifier.Binding> archived=new ArrayList<>(pending.archivedVerifiers());
        archived.add(mandatoryChoice.archived());
        archived.add(NativeEventEffects.archivedVerifier(block,sources.nativeEffects(),context.frameLoader(),material));
        installation=new RootDomainInstallation("complete-native-events-and-shared-pending-mux",List.of(),
                List.of(new RootReadContractCatalog.InstalledRead(window,sources.windowDecoder()),new RootReadContractCatalog.InstalledRead(religion.contract(),sources.religionReadDecoder()),
                        new RootReadContractCatalog.InstalledRead(mandatoryChoice.query(),sources.mandatoryChoice())),
                List.of(),actions,List.of(),archived,List.of(options),List.of(),List.of(),List.of(incidents.intentBinding()),Set.of(),
                EventPolicies.policies(sources.policies(),Optional.of(trusted),expectations,context.reads(),eventReads,validator,incidents.capturePort(),
                        (request,operation,args,plan,purpose,domain)->operation.value().equals(RootMandatoryChoiceRuntime.SELECT)
                                ? mandatoryChoice.prepare(request,plan):sameSharedBinding.propose(request,operation,args,plan,purpose,domain),
                        Optional.of(eventSources)),List.of(),
                actions.stream().map(action->new RootDomainInstallation.FixedDomain(action,Domain.diplomacy)).toList(),
                List.of(new RootDomainInstallation.FamilyDomain(options,Domain.diplomacy)),List.of());
    }
    private EventReadBinding.ReceiptResolution<ArmyWindowCodec.Observation> fixedWindowRead(PlanningRequest request,OperationKey operation) {
        try {
            return context.withSession(same->fixedWindowFrame(context.collector(),same,request,lease->{
                boolean overview=operation.value().equals("query-war-declared-overview-v1");
                var method=overview?org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1
                        :org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1;
                var frame=lease.frame();var windows=context.remainingDomains().armyOrdinary().quotes().producers().windows();
                var selected=new ArmyWindowReads.Selection(new ArmyCalls.Frame(method,new ArmyCalls.Revision(new ArmyTypes.Present<>(frame.identity().frame().revision()))),
                        new ArmyTypes.Context(frame.identity(),frame.source(),frame.sessionId(),request.deadline()),frame.connectionGeneration(),ArmyWindowReads.driverGeneration(frame));
                var contract=windows.issue(context.readCatalog(),selected);
                return new EventReadBinding.ReceiptResolution<>(contract,windows.request(selected).arguments(),known->{
                    var result=OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(known.value().normalized())),"actual fixed-window original");
                    String field=overview?"war_declared_overview_v1_observation":"war_results_window_v1_observation";
                    return new EventPolicies.ReadPublication(result,Optional.of(request.observations().snapshot().with(field,result)));
                });
            }));
        }catch(IOException failure){throw fixedWindowFailure(failure);}
    }
    /** Resolves only the typed READ descriptor inside the original held ordinary observation.
     * The coordinator still owns both physical read guards, Native dispatch and original custody. */
    static <T> T fixedWindowFrame(org.xar.ck3.control.application.readiness.ReadinessAuthority authority,
            Session same, PlanningRequest original,
            org.xar.ck3.control.application.readiness.ReadinessAuthority.CheckedWork<T> work) throws IOException {
        return Objects.requireNonNull(authority).current(same,original.before(),original.deadline(),lease->{
            var frame=lease.frame();
            StrictJson.require(frame.identity().equals(original.before()) && frame.source().equals(original.source())
                    && frame.sessionId().equals(original.sessionId()), "fixed-window READ definition crossed its original frame/source/session");
            return work.apply(lease);
        });
    }
    static UncheckedIOException fixedWindowFailure(IOException failure) {
        return new UncheckedIOException("actual original fixed-window collector unavailable: "
                + failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage()),failure);
    }
    public RootDomainInstallation installation() { return installation; }
    public RegisteredEventCore registeredCore() { return registered; }
    /** Immutable source-pinned provider shared with the actual public knowledge handlers. */
    public RegisteredEventKnowledge registeredKnowledge() { return knowledge; }
    /** The original configured roots/grant provider, shared by the offline worker; never a replacement trusted context. */
    public EventSourceReadContext eventSources() { return eventSources; }
    public EventWindowService eventWindow() { return windowService; }
    public ReadContract<EventPolicies.ReadPublication> eventWindowContract() { return window; }
    /** Exact installed objects for the Root private read allowlist; no aliases or new query permissions. */
    public List<ReadContract<?>> pendingUiReadContracts(){return List.of(window,sameKnown.definitions().pendingQuery());}
    @FunctionalInterface public interface FixtureWork<T>{T run()throws IOException;}
    /** The only startup caller is the same Root's sealed, privately issued upfront-parent scope.
     * It retains the existing Core read/action coordinators; this hook cannot submit an action. */
    public <T>T withFixtureStartupScope(Session same,QualifiedFixtureScope actual,FixtureWork<T> work)throws IOException{
        context.writer().requireSession(same);Objects.requireNonNull(actual);Objects.requireNonNull(work);
        actual.requireContext(context);actual.requireCurrent(same);
        StrictJson.require(privateEventSource.get()==null,"fixture startup cannot borrow a successor pending-UI source");
        var prior=fixtureEventSource.get();StrictJson.require(prior==null||prior==actual,"fixture startup crossed its original upfront parent scope");
        fixtureEventSource.set(actual);
        try{T value=work.run();actual.requireCurrent(same);return value;}
        finally{if(prior==null)fixtureEventSource.remove();else fixtureEventSource.set(prior);}
    }
    /** Privately minted observation of the actual installed event read. Getters expose DATA only;
     * preparation still requires its identical live Root scope and current source/frame. */
    public static final class FixtureEventObservation {
        private final EventRuntimeInstaller installer;
        private final QualifiedFixtureScope scope;
        private final ReadinessAuthority.LeaseSnapshot current;
        private final PlanningReadResult.Known<EventPolicies.ReadPublication> original;
        private final EventWindowModels.Build build;
        private final List<OpportunityJson.Obj> history;
        private final Set<OperationKey> actionSteps;
        private final List<ExactRef> originals;
        private FixtureEventObservation(EventRuntimeInstaller installer,QualifiedFixtureScope scope,ReadinessAuthority.LeaseSnapshot current,
                PlanningReadResult.Known<EventPolicies.ReadPublication> original,EventWindowModels.Build build,List<OpportunityJson.Obj> history,
                Set<OperationKey> actionSteps,List<ExactRef> originals){
            this.installer=installer;this.scope=scope;this.current=current;this.original=original;this.build=build;
            this.history=List.copyOf(history);this.actionSteps=Set.copyOf(actionSteps);this.originals=List.copyOf(originals);
        }
        public Complete frame(){return current.frame();}
        public PlanningReadResult.Known<EventPolicies.ReadPublication> originalRead(){return original;}
        public EventWindowModels.Build build(){return build;}
        public List<OpportunityJson.Obj> history(){return history;}
        public Set<OperationKey> actionSteps(){return actionSteps;}
        public Set<String> bridgeCapabilities(){return current.bridgeCapabilities();}
        public List<ExactRef> originals(){return originals;}
    }
    public FixtureEventObservation observeFixtureStartupEvent(Session same,QualifiedFixtureScope actual,Instant deadline)throws IOException{
        requireFixtureScope(same,actual);Objects.requireNonNull(deadline);
        return actual.withCurrent(same,deadline,current->{
            requireFixtureCurrent(current);StrictJson.require(fixtureReadCurrent.get()==null,"fixture event read cannot nest physical callbacks");
            var frame=current.frame();StrictJson.require(frame.semantic().get("active_event") instanceof OpportunityJson.Obj,"actual fixture source has no active event");
            List<OpportunityJson.Obj> history=actual.history(same);
            var steps=new LinkedHashSet<>(current.executableSteps());steps.addAll(issueCurrentOptions(frame,current.bridgeCapabilities()));
            fixtureReadCurrent.set(current);
            try{
                var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),window.operation(),frame.semantic(),deadline);
                var received=actual.read(same,window,request);var original=verifyPendingRead(same,window,request,received);
                var refs=new LinkedHashSet<ExactRef>(List.of(actual.policySource(),sources.installer(),sources.windowRead(),sources.windowDecoder(),
                        sources.actionPreparation(),sources.nativeEffects(),frame.source().sourceRef(),frame.originalEvidence(),
                        current.originalHello(),current.originalHeartbeat(),original.originalReceipt()));
                current.originalSourceQualification().ifPresent(refs::add);
                return new FixtureEventObservation(this,actual,current,original,pendingBuild(same,original.receipt()),history,steps,List.copyOf(refs));
            }finally{fixtureReadCurrent.remove();}
        });
    }
    public ActionCommand prepareFixtureStartupAutomatic(Session same,QualifiedFixtureScope actual,FixtureEventObservation observed,
            String childActionId,Instant deadline)throws IOException{
        return prepareFixtureStartupEvent(same,actual,observed,Optional.empty(),Optional.empty(),List.of(),Optional.empty(),childActionId,deadline);
    }
    public Optional<ActionCommand> prepareFixtureStartupDecision(Session same,QualifiedFixtureScope actual,FixtureEventObservation observed,
            FixtureStartupHandler.Decision decision,String childActionId,Instant deadline)throws IOException{
        requireFixtureScope(same,actual);Objects.requireNonNull(observed);Objects.requireNonNull(decision);
        StrictJson.require(observed.installer==this&&observed.scope==actual,"fixture handler decision changed its actual installed observation/source");
        if(decision instanceof FixtureStartupHandler.ObserveOnly){
            return actual.withCurrent(same,deadline,current->{requireFixtureCurrent(current);requireFixtureUnchanged(observed,current);return Optional.empty();});
        }
        Optional<Integer> selected=Optional.empty();
        if(decision instanceof FixtureStartupHandler.SelectDisplayedOption requested){
            var event=OpportunityJson.object(observed.frame().semantic().get("active_event"),"actual fixture handler event");
            StrictJson.require(OpportunityJson.integer(event.get("instance_id"),"actual fixture handler event instance").equals(java.math.BigInteger.valueOf(requested.eventInstanceId())),"fixture handler selected another actual native event instance");
            selected=Optional.of(requested.optionNumber());
        }else StrictJson.require(decision instanceof FixtureStartupHandler.AutomaticSharedPolicy,"unimplemented closed fixture handler decision");
        return Optional.of(prepareFixtureStartupEvent(same,actual,observed,selected,Optional.of(decision.implementationSource()),
                FixtureStartupHandler.decisionSources(decision),Optional.of(FixtureStartupHandler.encodeDecision(decision)),childActionId,deadline));
    }
    private ActionCommand prepareFixtureStartupEvent(Session same,QualifiedFixtureScope actual,FixtureEventObservation observed,
            Optional<Integer> requestedOption,Optional<ExactRef> handlerSource,List<ExactRef> handlerOriginals,Optional<OpportunityJson.Obj> handlerDecision,
            String childActionId,Instant deadline)throws IOException{
        requireFixtureScope(same,actual);Objects.requireNonNull(observed);Objects.requireNonNull(requestedOption);Objects.requireNonNull(handlerSource);
        StrictJson.require(observed.installer==this&&observed.scope==actual,"fixture event preparation changed its original installed observer/upfront parent");
        return actual.withCurrent(same,deadline,current->{
            requireFixtureCurrent(current);requireFixtureUnchanged(observed,current);
            var data=new FixtureEventData(observed.frame(),observed.originalRead(),observed.build(),observed.history(),observed.actionSteps(),
                    observed.bridgeCapabilities(),observed.originals(),fixtureFocus(current));
            var origin=new FixtureDecisionOrigin(actual.parentActionId(),actual.policySource(),handlerSource,handlerOriginals,handlerDecision);
            ActionCommand command=prepareFixtureEventData(data,origin,requestedOption,childActionId,deadline,knowledge,trusted);
            requireFixtureChild(actual,command);return command;
        });
    }
    private static void requireFixtureUnchanged(FixtureEventObservation observed,ReadinessAuthority.LeaseSnapshot current){
        var fresh=current.frame();StrictJson.require(fresh.identity().equals(observed.frame().identity())&&fresh.source().equals(observed.frame().source())
                &&fresh.sessionId().equals(observed.frame().sessionId())&&fresh.semantic().equals(observed.frame().semantic()),"fixture event changed its original current frame before child preparation");
    }
    /** Pure preparation DATA for the same existing strategy/preparer. It cannot construct the
     * sealed fixture scope, dispatch, a submitted child, or an adoption qualification. */
    record FixtureEventData(Complete frame,PlanningReadResult.Known<EventPolicies.ReadPublication> original,
            EventWindowModels.Build build,List<OpportunityJson.Obj> history,Set<OperationKey> actionSteps,
            Set<String> bridgeCapabilities,List<ExactRef> sourceOriginals,Optional<String> focus){
        FixtureEventData{Objects.requireNonNull(frame);Objects.requireNonNull(original);Objects.requireNonNull(build);history=List.copyOf(history);
            actionSteps=Set.copyOf(actionSteps);bridgeCapabilities=Set.copyOf(bridgeCapabilities);sourceOriginals=List.copyOf(sourceOriginals);Objects.requireNonNull(focus);
            StrictJson.require(!sourceOriginals.isEmpty()&&sourceOriginals.size()<=32,"bounded actual fixture source originals required");}
    }
    record FixtureDecisionOrigin(String parentActionId,ExactRef policySource,Optional<ExactRef> handlerSource,List<ExactRef> handlerOriginals,Optional<OpportunityJson.Obj> handlerDecision){
        FixtureDecisionOrigin{StrictJson.require(parentActionId!=null&&!parentActionId.isBlank(),"actual upfront fixture parent identity required");
            StrictJson.require(Objects.requireNonNull(policySource).bytes()>0,"actual fixture policy source required");Objects.requireNonNull(handlerSource);handlerSource.ifPresent(source->StrictJson.require(source.bytes()>0,"actual bound Java startup handler source required"));
            handlerOriginals=List.copyOf(handlerOriginals);Objects.requireNonNull(handlerDecision);StrictJson.require(handlerSource.isPresent()==handlerDecision.isPresent(),"fixture handler source and its original typed decision must be retained together");}
    }
    static ActionCommand prepareFixtureEventData(FixtureEventData data,FixtureDecisionOrigin origin,Optional<Integer> requestedOption,
            String childActionId,Instant deadline,RegisteredEventKnowledge knowledge,TrustedEventSourceContext trusted){
        Objects.requireNonNull(data);Objects.requireNonNull(origin);Objects.requireNonNull(requestedOption);Objects.requireNonNull(deadline);
        var frame=data.frame();var read=data.original();var receipt=read.receipt();
        StrictJson.require(Set.of("native/event-window-v1","native/event-window-v2").contains(receipt.contractId())&&receipt.request().operation().value().equals(EventWindowRead.STEP)
                &&receipt.request().before().equals(frame.identity())&&receipt.request().source().equals(frame.source())&&receipt.request().sessionId().equals(frame.sessionId())
                &&receipt.request().deadline().equals(deadline)&&receipt.request().arguments().equals(frame.semantic())&&receipt.original().nativeOk(),"fixture decision lost its actual original same-frame event read");
        var active=OpportunityJson.object(frame.semantic().get("active_event"),"actual fixture active event");
        int instance=OpportunityJson.integer(active.get("instance_id"),"actual fixture event instance").intValueExact();
        var rawWindow=OpportunityJson.object(read.value().result().get("current_event_window_context"),"actual fixture native event window");
        boolean guiObservation=receipt.contractId().equals("native/event-window-v2");
        StrictJson.require(new OpportunityJson.Text(guiObservation?"current-event-window-context-v2":"current-event-window-context-v1").equals(rawWindow.get("schema"))
                &&new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(guiObservation?2:1)).equals(rawWindow.get("schema_version")),
                "fixture event read contract differs from its original window version");
        var decoded=EventWindowCodec.decode(new RawJson(DriverJson.encode(rawWindow)),new EventWindowModels.Binding(data.build(),frame.identity().frame().identity().nativeRevision(),frame.identity().frame().identity().dateRaw().intValueExact(),instance));
        if(!(decoded instanceof EventWindowModels.Available available))throw new PublicSelectionRejected(new OpportunityJson.Obj(Map.of("phase",new OpportunityJson.Text("fixture_event_window_unavailable"),"selected_step",OpportunityJson.Nil.INSTANCE,"event_window_context",rawWindow)));
        var captured=new EventReadBinding.Captured(read.value(),receipt.request().operation(),receipt.requestId(),receipt.contractId(),read.originalReceipt(),Optional.empty());
        var history=new ArrayList<>(data.history());history.add(captured.history());
        var input=new EventDecisionInput(frame.identity(),frame.source(),frame.sessionId(),frame.semantic(),history,data.actionSteps(),data.bridgeCapabilities(),deadline,
                org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.object(org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.parse(EventWindowCodec.encode(available).bytes())),data.focus());
        OpportunityJson.Obj plan=requestedOption.isPresent()?PublicEventSelection.plan(input,requestedOption.orElseThrow(),Optional.of(instance),knowledge,trusted)
                :PublicEventResolution.plan(input,Optional.of(instance),knowledge,trusted);
        plan=plan.with("public_event_window_read",captured.history());
        if(!(plan.get("selected_step") instanceof OpportunityJson.Text selected))throw new PublicSelectionRejected(plan);
        var operation=new OperationKey(selected.value());var number=EventActionPreparation.option(operation);
        StrictJson.require(data.actionSteps().contains(operation)&&data.bridgeCapabilities().contains(EventActionPreparation.EVENT_CAPABILITY),"fixture event has no actual installed selected native family/capability");
        var option=available.options().stream().filter(value->value.nativeOptionIndex()==number.value()-1).findFirst().orElseThrow(()->new IllegalArgumentException("fixture strategy selected an absent actual native option"));
        StrictJson.require(option.selectionAllowed(),"fixture strategy selected an option that does not permit selection");
        var refs=new LinkedHashSet<>(data.sourceOriginals());refs.add(read.originalReceipt());refs.add(origin.policySource());origin.handlerSource().ifPresent(refs::add);refs.addAll(origin.handlerOriginals());
        var encodedRefs=new ArrayList<OpportunityJson.Value>();refs.forEach(ref->encodedRefs.add(OpportunityJson.parse(StrictJson.canonical(ref.toJson()))));
        var metadata=new OpportunityJson.Obj(Map.of("schema",new OpportunityJson.Text("xar.fixture-startup-event-source/v1"),"original_parent_action_id",new OpportunityJson.Text(origin.parentActionId()),
                "policy_source",OpportunityJson.parse(StrictJson.canonical(origin.policySource().toJson())),"original_read",OpportunityJson.parse(StrictJson.canonical(read.originalReceipt().toJson())),"source_originals",new OpportunityJson.Arr(encodedRefs)));
        plan=plan.with("fixture_startup_event_source",metadata);
        if(origin.handlerSource().isPresent())plan=plan.with("fixture_startup_handler_source",OpportunityJson.parse(StrictJson.canonical(origin.handlerSource().orElseThrow().toJson())));
        if(origin.handlerDecision().isPresent())plan=plan.with("fixture_startup_handler_decision",origin.handlerDecision().orElseThrow());
        Optional<org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome.Expectation> trait=Optional.empty();
        if(plan.get("event_decision") instanceof OpportunityJson.Obj decision)trait=RegisteredEventMaterial.poet(
                org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.object(org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.parse(DriverJson.encode(decision))),
                org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.object(org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.parse(DriverJson.encode(frame.semantic()))));
        var expected=NativeEventPostconditionPort.expected(frame.identity(),frame.source(),frame.semantic(),operation,plan,trait).orElseThrow(()->new PublicSelectionRejected(metadata.with("phase",new OpportunityJson.Text("fixture_event_native_postcondition_unavailable"))));
        var claims=new Claims(Set.of(),Set.of(),Set.of(frame.identity().frame().identity().player()),Set.of("foreground-window"));
        var command=new ActionCommand(childActionId,frame.identity(),frame.source(),frame.sessionId(),operation,plan,expected,claims,deadline);
        EventActionPreparation.prepare(command);return command;
    }
    private static Optional<String> fixtureFocus(ReadinessAuthority.LeaseSnapshot current){
        var snapshot=current.frame().semantic();var retained=current.driver().driver().campaignGoal();
        if(retained instanceof org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value original){
            var goal=org.xar.ck3.control.g2.m7.GoalCodec.decodeGoal(original.json());
            StrictJson.require(java.math.BigInteger.valueOf(goal.currentCharacterId()).equals(current.frame().identity().frame().identity().player())
                    &&DriverJson.object(original.json(),DriverJson.MAX_NATIVE_BYTES).equals(snapshot.get("campaign_goal")),"fixture event focus crossed its actual retained Driver goal/actor");
            return Optional.of(org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.plan(goal).focus());
        }
        StrictJson.require(snapshot.get("campaign_goal")==null||snapshot.get("campaign_goal")==OpportunityJson.Nil.INSTANCE,"fixture semantic goal has no actual retained Driver original");
        return org.xar.ck3.control.application.planning.campaign.CrossRunPlanning.focus(snapshot.get("cross_run_plan") instanceof OpportunityJson.Obj plan?Optional.of(plan):Optional.empty());
    }
    private void requireFixtureScope(Session same,QualifiedFixtureScope actual)throws IOException{
        context.writer().requireSession(same);Objects.requireNonNull(actual);
        StrictJson.require(fixtureEventSource.get()==actual,"fixture event hook requires its original active sealed Root scope");
        actual.requireContext(context);actual.requireCurrent(same);
    }
    private void requireFixtureCurrent(ReadinessAuthority.LeaseSnapshot current){
        var frame=Objects.requireNonNull(current).frame();StrictJson.require(frame.identity().game().equals(context.game().generation())
                &&frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId()),"fixture event source crossed actual Root Game/source/session");
    }
    /** Retains only the actual Root private Source, never a physical read lease across submission. */
    public <T>T withPendingEventSource(Session same,PendingUiEvent.Source actual,PendingUiEvent.ScopedWork<T> work)throws IOException{
        context.writer().requireSession(same);Objects.requireNonNull(actual);Objects.requireNonNull(work);actual.requireCurrent(same);
        StrictJson.require(fixtureEventSource.get()==null,"successor pending-UI source cannot borrow a fixture startup scope");
        var prior=privateEventSource.get();StrictJson.require(prior==null||prior==actual,"private pending event crossed its original Root source custody");
        privateEventSource.set(actual);
        try{T result=work.run();actual.requireCurrent(same);return result;}
        finally{if(prior==null)privateEventSource.remove();else privateEventSource.set(prior);}
    }
    public EventActionPreparation.PendingPrepared preparePendingUiEvent(Session same,PendingUiEvent.Source actual,String actionId,Instant deadline)throws IOException{
        Objects.requireNonNull(deadline);return withPendingEventSource(same,actual,()->actual.withCurrent(same,deadline,current->{
            requirePendingCurrent(current);StrictJson.require(privateReadCurrent.get()==null,"private event preparation cannot nest physical read callbacks");
            privateReadCurrent.set(current);
            try{
            incidents.retainPendingUiFrame(same,current,deadline);
            var natural=context.remainingDomains().lifecycle().natural();
            var frame=current.frame();var steps=new LinkedHashSet<OperationKey>();
            if(frame.semantic().get("active_event") instanceof OpportunityJson.Obj)steps.addAll(issueCurrentOptions(frame,current.bridgeCapabilities()));
            var origin=new CommandOrigin.Gameplay(frame.identity());
            for(var installed:context.bindings().installed())if(context.bindings().resolve(installed.operation(),origin).isPresent()
                    &&installed.requiredCapability().map(current.bridgeCapabilities()::contains).orElse(true))steps.add(installed.operation());
            if(frame.semantic().get("active_event") instanceof OpportunityJson.Obj){
                var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),window.operation(),frame.semantic(),deadline);
                var received=natural.withPendingReadFailureEvidence(same,actual,current,window,request,
                    (borrowed,exactContract,exactRequest,unavailable,attempted,originals)->
                            incidents.retainPendingUiReadFailure(borrowed,new RootIncidentRuntime.PendingReadFailure(current,exactContract,exactRequest,unavailable,attempted),originals),
                    ()->actual.read(same,window,request));var original=verifyPendingRead(same,window,request,received);
                try{
                    return PendingUiEventPreparation.event(current,original,pendingBuild(same,original.receipt()),Set.copyOf(steps),actionId,deadline,knowledge,trusted);
                }catch(EventActionPreparation.PendingSelectionRejected rejected){
                    StrictJson.require(rejected.originalRead().equals(original.originalReceipt()),"private pending rejection crossed its verified original read");
                    incidents.retainPendingUiBlocked(same,new RootIncidentRuntime.PendingBlocked(current,original.receipt(),original.originalReceipt(),rejected.diagnosis()),deadline);
                    throw rejected;
                }
            }
            StrictJson.require(frame.semantic().get("pending_character_interaction") instanceof OpportunityJson.Obj,"private pending source has no event or character notification");
            var controls=sameKnown.projection().project(frame,deadline);var contract=sameKnown.definitions().pendingQuery();
            var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),PendingInteractionReadArguments.current(controls),deadline);
            var received=natural.withPendingReadFailureEvidence(same,actual,current,contract,request,
                (borrowed,exactContract,exactRequest,unavailable,attempted,originals)->
                        incidents.retainPendingUiReadFailure(borrowed,new RootIncidentRuntime.PendingReadFailure(current,exactContract,exactRequest,unavailable,attempted),originals),
                ()->actual.read(same,contract,request));var original=verifyPendingRead(same,contract,request,received);
            try{
                return PendingUiEventPreparation.interaction(current,original,controls,Set.copyOf(steps),actionId,deadline,trusted);
            }catch(EventActionPreparation.PendingSelectionRejected rejected){
                StrictJson.require(rejected.originalRead().equals(original.originalReceipt()),"private pending rejection crossed its verified original read");
                incidents.retainPendingUiBlocked(same,new RootIncidentRuntime.PendingBlocked(current,original.receipt(),original.originalReceipt(),rejected.diagnosis()),deadline);
                throw rejected;
            }
            }finally{privateReadCurrent.remove();}
        }));
    }
    /** Root's actual post-CAS authority check precedes the pure same-window recheck. Original command bytes are retained. */
    public void requirePendingUiEventCurrent(Session same,PendingUiEvent.Source actual,EventActionPreparation.PendingPrepared retained,
            EventActionPreparation.PendingPrepared actualFresh)throws IOException{
        context.writer().requireSession(same);actual.requireCurrent(same);
        actual.requireOriginalPreparation(same,retained.command(),actualFresh.command());
        EventActionPreparation.requirePendingUiEventCurrent(retained,actualFresh);actual.requireCurrent(same);
    }
    private <T>PlanningReadResult.Known<T> verifyPendingRead(Session same,ReadContract<T> contract,PlanningReadRequest request,PlanningReadResult.Known<T> received){
        StrictJson.require(received.receipt().request().equals(request)&&received.receipt().contractId().equals(contract.contractId())
                &&context.readCatalog().containsIdentity(contract),"private pending window changed its actual installed contract/request");
        var archive=context.archive().withSession(same);NativeRecordedEvidenceVerifier.requireRead(received.receipt(),archive);
        StrictJson.require(archive.readReferenceOf(received.receipt()).equals(received.originalReceipt()),"private pending original read reference differs");
        return new PlanningReadResult.Known<>(contract.decode(received.receipt()),received.receipt(),received.originalReceipt());
    }
    private EventWindowModels.Build pendingBuild(Session same,PlanningReadReceipt read)throws IOException{
        var packet=NativeWire.decode(context.originals().read(same,read.before().binding().capabilityEvidence(),NativeWire.MAXIMUM_FRAME_BYTES+4));
        StrictJson.require(packet instanceof NativeWire.Hello,"private event read has no actual original HELLO");var hello=(NativeWire.Hello)packet;
        for(var candidate:EventWindowModels.Build.values())if(candidate.sha256().equalsIgnoreCase(hello.gameSha256()))return candidate;
        throw new IOException("private pending event exact connected build is unsupported");
    }
    private void requirePendingCurrent(PendingUiEvent.Current current){
        var frame=current.frame();StrictJson.require(frame.identity().game().equals(context.game().generation())&&frame.source().equals(context.source())
                &&frame.sessionId().equals(context.game().sessionId()),"private event source belongs to another actual Root Game/source/session");
    }
    private Optional<Complete> privateEventAfter(ActionCommand original,Instant deadline)throws IOException{
        var fixture=fixtureEventSource.get();
        if(fixture!=null){
            var same=context.borrowedSession();requireFixtureScope(same,fixture);requireFixtureChild(fixture,original);
            Optional<Complete> after=fixture.after(same,original,deadline);
            after.ifPresent(frame->StrictJson.require(frame.source().equals(original.source())&&frame.sessionId().equals(original.sessionId())
                    &&frame.identity().game().equals(original.origin().game())
                    &&frame.identity().frame().identity().player().equals(original.before().frame().identity().player())
                    &&frame.identity().frame().episodeRunId().equals(original.before().frame().episodeRunId()),"fixture event independent after crossed original Game/actor/source/session/episode"));
            return after;
        }
        StrictJson.require(!fixtureStartupCommand(original),"fixture startup command requires its original sealed source or canonical physical reconciliation scope");
        var source=privateEventSource.get();if(source==null){
            StrictJson.require(!privatePendingCommand(original),"pending UI command requires its actual private source or canonical physical reconciliation scope");
            return Optional.empty();
        }
        var same=context.borrowedSession();source.requireCurrent(same);
        StrictJson.require(NativeEventEffects.supports(original.operation()),"private event source cannot observe an unrelated ordinary action");
        return source.withCurrent(same,deadline,current->{requirePendingCurrent(current);var frame=current.frame();
            StrictJson.require(frame.source().equals(original.source())&&frame.sessionId().equals(original.sessionId())
                    &&frame.identity().frame().identity().player().equals(original.before().frame().identity().player())
                    &&frame.identity().frame().episodeRunId().equals(original.before().frame().episodeRunId()),"private after observation crossed the original successor actor/run/source");
            return Optional.of(frame);});
    }
    /** Retained original profile only selects the readers that really existed; it grants no read or submit authority. */
    private static boolean privatePendingCommand(ActionCommand original){
        if(!original.arguments().members().containsKey("pending_ui_event_source"))return false;
        var profile=OpportunityJson.object(original.arguments().get("pending_ui_event_source"),"original pending UI source profile");
        StrictJson.require(profile.members().keySet().equals(Set.of("schema","original_parent_action_id","original_parent_body_sha256","original_read","source_originals"))
                &&new OpportunityJson.Text("xar.pending-ui-event-source/v1").equals(profile.get("schema")),"original pending UI source profile differs");
        return true;
    }
    private static boolean fixtureStartupCommand(ActionCommand original){
        if(!original.arguments().members().containsKey("fixture_startup_event_source"))return false;
        var profile=OpportunityJson.object(original.arguments().get("fixture_startup_event_source"),"original fixture event source profile");
        StrictJson.require(profile.members().keySet().equals(Set.of("schema","original_parent_action_id","policy_source","original_read","source_originals"))
                &&new OpportunityJson.Text("xar.fixture-startup-event-source/v1").equals(profile.get("schema")),"original fixture event source profile differs");
        return true;
    }
    private static void requireFixtureChild(QualifiedFixtureScope actual,ActionCommand original){
        StrictJson.require(NativeEventEffects.supports(original.operation())&&fixtureStartupCommand(original),"fixture event source cannot observe an unrelated or unbound action");
        var profile=OpportunityJson.object(original.arguments().get("fixture_startup_event_source"),"original fixture event source profile");
        StrictJson.require(new OpportunityJson.Text(actual.parentActionId()).equals(profile.get("original_parent_action_id"))
                &&ExactRef.fromJson(DriverJson.toNode(profile.get("policy_source"))).equals(actual.policySource()),"fixture event child crossed its upfront parent/policy source");
    }
    public PlayerReligionContextRead religion() { return religion; }
    public ArmyStrengthsMaterialQuery armyMaterial() { return armyMaterial; }
    public NativeEventEffects.MaterialQueries materialQueries() { return material; }
    public RootPendingInteractionEffects pendingMux() { return pending; }
    public List<OrdinaryPolicy> policies() { return installation.policies(); }
    public PublicBindings.TypedBinding<EventWindowService.Query,EventWindowService.Response> installPublic(PublicBindings same) {
        return windowService.install(Objects.requireNonNull(same),sources.windowService());
    }
    /** No action was prepared or dispatched. Unfamiliar blocked plans are retained by the same incident producer. */
    public static final class PublicSelectionRejected extends IllegalArgumentException {
        private static final long serialVersionUID=1L;
        private final OpportunityJson.Obj diagnosis;
        private PublicSelectionRejected(OpportunityJson.Obj diagnosis) {
            super("the native event selection is unavailable; retained original plan: "+ActionCodec.sha256(DriverJson.encode(diagnosis)));
            this.diagnosis=Objects.requireNonNull(diagnosis);
        }
        public OpportunityJson.Obj diagnosis() { return diagnosis; }
    }
    /**
     * Called inside Root's same-writer public preparation scope with its genuine complete planning input.
     * This reads the installed window once and returns one command; Root dispatches only after the Driver freeze exits.
     * The caller validates its optional expected revision against actual.before without replacing that identity.
     */
    public ActionCommand preparePublicSelection(PlanningRequest actual,int optionNumber,Optional<Integer> expectedInstance)throws IOException {
        new EventActionPreparation.OptionNumber(optionNumber);
        return preparePublicEvent(actual,expectedInstance,Optional.of(optionNumber));
    }
    /** Automatic public resolution shares the same original collector/read/command preparation as explicit selection. */
    public ActionCommand preparePublicResolution(PlanningRequest actual,Optional<Integer> expectedInstance)throws IOException {
        return preparePublicEvent(actual,expectedInstance,Optional.empty());
    }
    private ActionCommand preparePublicEvent(PlanningRequest actual,Optional<Integer> expectedInstance,Optional<Integer> callerOption)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(expectedInstance);Objects.requireNonNull(callerOption);
        context.requireCurrent(actual.deadline());Session same=context.borrowedSession();context.writer().requireSession(same);
        StrictJson.require(actual.before().game().equals(context.game().generation())&&actual.source().equals(context.source())
                &&actual.sessionId().equals(context.game().sessionId()),"public event selection crossed this actual physical Game/source/session");
        return context.collector().currentPlanning(same,actual,actual.deadline(),(retained,lease)-> {
            EventReadBinding<?> installed=eventReads.stream().filter(binding->binding.operation().equals(window.operation())).findFirst().orElseThrow();
            EventReadBinding.Outcome read=installed.read(context.reads(),retained,installed.operation(),incidents.capturePort());
            EventReadBinding.Captured captured=switch(read) {
                case EventReadBinding.Unavailable unavailable -> {
                    capturePublicNativeGap(retained,unavailable.result().reason());
                    throw new IllegalArgumentException("the actual current event window read is unavailable: "+unavailable.result().reason()+"; no event option was submitted");
                }
                case EventReadBinding.Captured known -> known;
            };
            PlanningRequest withRead=appendPublicRead(retained,captured);
            OpportunityJson.Obj plan=publicPlan(withRead,expectedInstance,callerOption).with("public_event_window_read",captured.history());
            Set<OperationKey> attempted=new LinkedHashSet<>();attempted.add(window.operation());
            // Only an exact installed operation may satisfy the existing dedicated policy's required read.
            while(callerOption.isEmpty()&&!(plan.get("selected_step") instanceof OpportunityJson.Text)
                    &&plan.get("required_step") instanceof OpportunityJson.Text required&&attempted.size()<=eventReads.size()) {
                OperationKey operation=new OperationKey(required.value());
                if(!attempted.add(operation))break;
                Optional<EventReadBinding<?>> exact=eventReads.stream().filter(binding->binding.supports(operation)).findFirst();
                if(exact.isEmpty()) {
                    plan=plan.with("public_required_read_unavailable",new OpportunityJson.Text("no exact installed binding: "+operation.value()));break;
                }
                EventReadBinding.Outcome materialRead=exact.orElseThrow().read(context.reads(),withRead,operation,incidents.capturePort());
                if(materialRead instanceof EventReadBinding.Unavailable unavailable) {
                    plan=plan.with("public_required_read_unavailable",new OpportunityJson.Text(unavailable.result().reason()));break;
                }
                EventReadBinding.Captured materialCapture=switch(materialRead) {
                    case EventReadBinding.Captured known -> known;
                    case EventReadBinding.Unavailable unavailable -> throw new IllegalStateException("unavailable read cannot publish material");
                };
                withRead=appendPublicRead(withRead,materialCapture);
                plan=publicPlan(withRead,expectedInstance,callerOption).with("public_event_window_read",captured.history());
            }
            if(!(plan.get("selected_step") instanceof OpportunityJson.Text selected)) {
                if(!captureOriginalBlocked(withRead,plan))capturePublicNativeGap(withRead,"the dedicated public event decision has no actual exact read binding or executable choice");
                throw new PublicSelectionRejected(plan);
            }
            EventActionPreparation.OptionNumber requested=EventActionPreparation.option(new OperationKey(selected.value()));
            callerOption.ifPresent(number->StrictJson.require(number==requested.value(),"public selection must preserve the caller authored option"));
            if(!withRead.observations().actionSteps().contains(requested.operation())
                    ||!withRead.observations().bridgeCapabilities().contains(EventActionPreparation.EVENT_CAPABILITY)) {
                OpportunityJson.Obj unavailable=plan.with("unsubmitted_candidate_step",plan.get("selected_step")).with("selected_step",OpportunityJson.Nil.INSTANCE);
                if(!captureOriginalBlocked(withRead,unavailable))capturePublicNativeGap(withRead,"the selected event option has no actual installed executable step/native template capability");
                throw new PublicSelectionRejected(unavailable);
            }
            Optional<org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome.Expectation> trait=Optional.empty();
            if(plan.get("event_decision") instanceof OpportunityJson.Obj decision)
                trait=RegisteredEventMaterial.poet(
                        org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.object(org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.parse(DriverJson.encode(decision))),
                        org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.object(org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.parse(DriverJson.encode(withRead.observations().snapshot()),new org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ParseBudget(DriverJson.MAX_NATIVE_BYTES,DriverJson.MAX_NATIVE_BYTES,128))));
            var expected=expectations.expected(withRead,requested.operation(),plan,trait);
            if(expected.isEmpty()) {
                OpportunityJson.Obj unavailable=plan.with("unsubmitted_candidate_step",plan.get("selected_step")).with("selected_step",OpportunityJson.Nil.INSTANCE);
                if(!captureOriginalBlocked(withRead,unavailable))capturePublicNativeGap(withRead,"the selected event option has no genuine native postcondition contract");
                throw new PublicSelectionRejected(unavailable);
            }
            String id=ActionIds.forDecision(withRead.sessionId(),withRead.before(),"public:"+requested.operation().value()+":"+ActionCodec.sha256(DriverJson.encode(plan)));
            ActionCommand command=new ActionCommand(id,withRead.before(),withRead.source(),withRead.sessionId(),requested.operation(),plan,
                    expected.orElseThrow(),foregroundClaims(withRead),withRead.deadline());
            // The same installed preparer validates the exact native/rendered mapping now. It produces no ACK or native call.
            EventActionPreparation.prepare(command);context.writer().requireSession(same);return command;
        });
    }
    private OpportunityJson.Obj publicPlan(PlanningRequest retained,Optional<Integer> expectedInstance,Optional<Integer> callerOption) {
        return callerOption.isPresent()?PublicEventSelection.plan(retained,callerOption.orElseThrow(),expectedInstance,knowledge,trusted,validator)
                :PublicEventResolution.plan(retained,expectedInstance,knowledge,trusted,validator);
    }
    private static PlanningRequest appendPublicRead(PlanningRequest request,EventReadBinding.Captured captured) {
        PlanningObservation before=request.observations();OpportunityJson.Obj snapshot=captured.publication().snapshot().orElse(before.snapshot());
        for(String key:List.of("active_event","current_event","pending_character_interaction","one_life_terminal_reason","paused","map_ready"))
            StrictJson.require(Objects.equals(before.snapshot().get(key),snapshot.get(key)),"public material read changed the frozen event/control frame: "+key);
        var originalPlayer=OpportunityJson.object(before.snapshot().get("played_character"),"original actual player");
        var materialPlayer=OpportunityJson.object(snapshot.get("played_character"),"material actual player");
        StrictJson.require(Objects.equals(originalPlayer.get("alive"),materialPlayer.get("alive")),"public material read changed player terminal state");
        List<OpportunityJson.Obj> history=new ArrayList<>(before.history());history.add(captured.history());
        var next=new PlanningObservation(snapshot,history,before.actionSteps(),before.bridgeCapabilities(),before.battleSpeedReadiness(),before.actionFacts(),
                before.campaignGoal(),before.crossRunPlan(),before.initialLifestyleFocusRequired());
        return new PlanningRequest(request.before(),request.source(),request.sessionId(),request.deadline(),next);
    }
    /** Original Applied material only; no live query, dispatch, ACK interpretation or alternative event encoder. */
    public Optional<RawJson> publicSelectionResult(ActionReceipt original)throws IOException {
        Objects.requireNonNull(original);ActionCommand command=original.command();EventActionPreparation.option(command.operation());
        StrictJson.require(command.before().game().equals(context.game().generation())&&command.source().equals(context.source())
                &&command.sessionId().equals(context.game().sessionId())&&command.expected().observerSchema().equals(NativeEventPostconditionPort.EVENT_SCHEMA),
                "public event result must belong to this same actual runtime and native event contract");
        if(!(original.state() instanceof ActionState.Settled settled)||!(settled.settlement() instanceof ActionState.Applied))return Optional.empty();
        return context.withSession(same->{
            var archive=context.archive().withSession(same);var reference=archive.receiptReferenceOf(original);
            StrictJson.require(archive.loadReceipt(reference).equals(original),"public event material must use its actual canonical archived receipt");
            var actualVerifier=context.bindings().actualArchivedVerifier(command.operation()).orElseThrow(()->new IllegalStateException("the exact event action has no installed original-evidence verifier"));
            actualVerifier.verifier().verify(same.head(),original,archive);
            return Optional.of(EventSelectionPublicResult.encode(original,NativeEffectEvidence.load(original,archive,context.frameLoader())));
        });
    }
    private static Claims foregroundClaims(PlanningRequest request) {
        return new Claims(Set.of(),Set.of(),Set.of(request.before().frame().identity().player()),Set.of("foreground-window"));
    }
    private boolean captureOriginalBlocked(PlanningRequest actual,OpportunityJson.Obj plan)throws IOException {
        if(!(plan.get("unhandled_event_fallback") instanceof OpportunityJson.Obj)
                &&!(plan.get("unhandled_native_window_diagnostic") instanceof OpportunityJson.Obj))return false;
        incidents.capturePort().captureBlocked(actual,plan);return true;
    }
    private void capturePublicNativeGap(PlanningRequest actual,String reason)throws IOException {
        var captured=EventPolicies.captureUnavailable(actual,reason,incidents.capturePort());
        if(captured instanceof OrdinaryPolicy.Stop stop)throw new IOException(stop.reason());
    }
    /** Invoke in the actual readiness capability producer, before its actionSteps set is frozen. No command is submitted. */
    public Set<OperationKey> issueCurrentOptions(Complete actual,Set<String> originalNativeCapabilities) {
        Objects.requireNonNull(actual);Objects.requireNonNull(originalNativeCapabilities);
        StrictJson.require(actual.identity().game().equals(context.game().generation())&&actual.source().equals(context.source())
                &&actual.sessionId().equals(context.game().sessionId()),"event executable inventory crossed its actual physical Game/source/session");
        if(!originalNativeCapabilities.contains(EventActionPreparation.EVENT_CAPABILITY))return Set.of();
        if(!(actual.semantic().get("active_event") instanceof OpportunityJson.Obj event))return Set.of();
        var count=OpportunityJson.integer(event.get("option_count"),"actual event option count");
        StrictJson.require(count.signum()>0&&count.compareTo(java.math.BigInteger.valueOf(4096))<=0,"bounded actual event option family required");
        Set<OperationKey> result=new LinkedHashSet<>();
        for(int number=1;number<=count.intValueExact();number++)result.add(context.bindings().issue(options,new EventActionPreparation.OptionNumber(number)).effect().operation());
        return Set.copyOf(result);
    }
    private void admit(PlanningReadRequest request) {
        try {
            var fixture=fixtureEventSource.get();
            if(fixture!=null){
                var same=context.borrowedSession();requireFixtureScope(same,fixture);
                var current=fixtureReadCurrent.get();
                if(current!=null)requireFixtureRead(request,current);
                else fixture.withCurrent(same,request.deadline(),lease->{requireFixtureRead(request,lease);return null;});
                return;
            }
            var source=privateEventSource.get();
            if(source!=null){var same=context.borrowedSession();source.requireCurrent(same);
                var current=Objects.requireNonNull(privateReadCurrent.get(),"private event read has no actual active physical callback");
                requirePendingCurrent(current);var frame=current.frame();StrictJson.require(request.operation().equals(window.operation())
                        &&request.before().equals(frame.identity())&&request.source().equals(frame.source())&&request.sessionId().equals(frame.sessionId())
                        &&request.arguments().equals(frame.semantic()),"private event window read escaped its exact actual source scope");return;}
            context.requireCurrent(request.deadline());context.withSession(same->context.collector().current(same,request.before(),request.deadline(),lease->{
                StrictJson.require(lease.frame().source().equals(request.source())&&lease.frame().sessionId().equals(request.sessionId()),"event native read source/session changed");return null;
            }));
        }catch(IOException failure){throw new UncheckedIOException("actual event native read admission unavailable",failure);}
    }
    private void requireFixtureRead(PlanningReadRequest request,ReadinessAuthority.LeaseSnapshot current){
        requireFixtureCurrent(current);var frame=current.frame();
        StrictJson.require(request.before().equals(frame.identity())&&request.source().equals(frame.source())&&request.sessionId().equals(frame.sessionId()),"fixture event read escaped its exact actual source/frame/session");
        if(request.operation().equals(window.operation()))StrictJson.require(request.arguments().equals(frame.semantic()),"fixture window read changed its original complete native snapshot");
        else StrictJson.require(request.operation().equals(religion.contract().operation())&&request.arguments().members().isEmpty(),"fixture event admission has no installed source-owned read for these arguments");
    }
    private EventWindowModels.Build build(PlanningRequest request) {
        try {
            return context.withSession(same->context.collector().currentPlanning(same,request,request.deadline(),(original,lease)-> {
                NativeWire.Frame packet=NativeWire.decode(context.originals().read(same,lease.originalHello(),NativeWire.MAXIMUM_FRAME_BYTES+4));
                StrictJson.require(packet instanceof NativeWire.Hello,"actual original event HELLO required");NativeWire.Hello hello=(NativeWire.Hello)packet;
                var diagnostics=OpportunityJson.object(request.observations().snapshot().get("diagnostics"),"actual native diagnostics");
                StrictJson.require(hello.pid()==request.before().game().pid()&&hello.connectionGeneration().equals(OpportunityJson.integer(diagnostics.get("connection_generation"),"actual connection generation"))
                        &&hello.buildMatch()&&hello.adapterStatus().equals("ready"),"actual event HELLO process/connection/build differs");
                for(var candidate:EventWindowModels.Build.values())if(candidate.sha256().equalsIgnoreCase(hello.gameSha256()))return candidate;
                throw new IllegalArgumentException("actual connected event build SHA is unsupported");
            }));
        }catch(IOException failure){throw new UncheckedIOException("actual original event HELLO unavailable",failure);}
    }
    private PlanningReadRequest currentWindow(EventWindowService.Query query) {
        try {
            Instant deadline=context.clock().instant().plusSeconds(30);context.requireCurrent(deadline);
            return context.withSession(same->context.collector().currentOwned(same,context.collector().identity(),deadline,lease-> {
                Complete current=lease.frame();
                PlanningReadRequest request=new PlanningReadRequest(current.identity(),current.source(),current.sessionId(),window.operation(),current.semantic(),deadline);
                StrictJson.require(current.identity().frame().revision().equals(query.expectedRevision())&&EventWindowRead.activeEvent(request)==query.eventInstanceId(),"public event query differs from its actual current window");return request;
            }));
        }catch(IOException failure){throw new UncheckedIOException("actual current event frame unavailable",failure);}
    }
    private Session borrowedSession() {
        try { return context.borrowedSession(); }
        catch(IOException failure) { throw new UncheckedIOException("actual event read borrowed writer session unavailable",failure); }
    }
    private static OpportunityJson.Obj empty() { return new OpportunityJson.Obj(Map.of()); }
    private static OpportunityJson.Obj object(RawJson original) { return OpportunityJson.object(OpportunityJson.parse(original.bytes()),"actual complete event material"); }
}
