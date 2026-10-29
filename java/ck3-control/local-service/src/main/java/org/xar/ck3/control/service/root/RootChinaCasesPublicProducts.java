package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesService;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One per-Game original facade, held READ scope and Root action binding. Construction never observes or submits. */
public final class RootChinaCasesPublicProducts {
    /** Pure ordinary construction; the metadata is DATA and does not qualify a native command. */
    public static Prepared ordinary(RootAdditionalDomains.ImplementationMetadata metadata) {
        Objects.requireNonNull(metadata);
        return prepare(new Sources(metadata.implementation(ChinaCasesFacade.class),
                metadata.implementation(org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.class),
                metadata.implementation(ChinaCasesContract.class),metadata.implementation(ChinaCasesCodec.class),
                metadata.implementation(ChinaCasesService.class),metadata.implementation(RootChinaCasesPublicProducts.class)));
    }
    private static final OperationKey ACTIVATE=new OperationKey("activate-zhongguo-scoreboard-v1");
    private static final String TRANSPORT_CAP="game.contract.zhongguo-scoreboard-action-v1-fail-closed";
    private static final String PRODUCTION_CAP="game.command.activate-zhongguo-scoreboard-v1";
    private static final String ACK_SCHEMA="china-cases/public-scoreboard-independent-postcondition/v1";
    private RootChinaCasesPublicProducts() { }

    public record Sources(ExactRef facade,ExactRef originalDecoder,ExactRef publicContract,ExactRef publicCodec,
            ExactRef publicService,ExactRef rootProduct) {
        public Sources {for(ExactRef ref:List.of(facade,originalDecoder,publicContract,publicCodec,publicService,rootProduct))
            require(ref.bytes()>0,"actual selected ChinaCases implementation/decoder source required");}
    }
    public static final class Prepared {
        private final Sources sources;
        private RootApplicationAssembly.Core core;
        private static final class Attempt {private Installed installed;}
        private final java.util.IdentityHashMap<RootRuntimeContext,Attempt> installs=new java.util.IdentityHashMap<>();
        private Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);}
        public Sources sources(){return sources;}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public List<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized void bindCore(RootApplicationAssembly.Core same){require(core==null||core==same,"ChinaCases prepared Core cannot change");core=Objects.requireNonNull(same);}
        public synchronized Installed install(RootRuntimeContext actual)throws IOException {
            Objects.requireNonNull(actual);require(core!=null&&actual.core()==core,"ChinaCases requires its actual prepared Core");
            Attempt prior=installs.get(actual);if(prior!=null){if(prior.installed==null)throw new IOException("prior ChinaCases install failed; no partial replay");return prior.installed;}
            require(installs.size()<64,"bounded actual ChinaCases physical contexts required");var attempt=new Attempt();installs.put(actual,attempt);
            attempt.installed=new Installed(actual,sources);return attempt.installed;
        }
    }
    public static Prepared prepare(Sources sources){return new Prepared(sources);}

    /** Fixed pure source projector, installed by the facade before the identical contracts enter the catalog. */
    static ChinaCasesFacade.HistoryProjectionFactory historyFactory(Sources actual) {
        Objects.requireNonNull(actual);
        List<ExactRef> closure=List.of(actual.facade(),actual.originalDecoder(),actual.publicContract(),actual.publicCodec(),actual.publicService(),actual.rootProduct()).stream().distinct().toList();
        return new ChinaCasesFacade.HistoryProjectionFactory() {
            @Override public DriverReadHistoryRichMaterial.Kind kind(){return DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY;}
            @Override public <T>Optional<ReadContract.OriginalHistoryProjection<T>> forFamily(
                    org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family family) {
                Objects.requireNonNull(family);
                if(family==org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family.PROGRESS)return Optional.empty();
                Method method=Arrays.stream(Method.values()).filter(value->value.readOnly()&&value.family()==family).findFirst()
                        .orElseThrow(()->new IllegalArgumentException("family is not one of the original Cases10 reads"));
                return Optional.of((original,replayed)->{
                    Objects.requireNonNull(replayed);
                    RawJson numeric=ChinaCasesCodec.encodeNumericExecutionResult(method,original);
                    RawJson exposed=ChinaCasesCodec.encodeExecutionResult(method,original);
                    return new DriverReadHistoryRichMaterial.ExecuteProjection(original.request().operation(),ChinaCasesCodec.executionStep(method,original),
                            numeric,DriverReadHistoryRichMaterial.PublicNumbers.fromResults(numeric,exposed),closure);
                });
            }
        };
    }

    /** Result DATA retains its exact canonical receipt; encoding never submits or claims an observed UI effect. */
    public record ActionResponse(RawJson publicJson,ActionReceipt original,ExactRef originalReceipt) {
        public ActionResponse {Objects.requireNonNull(publicJson);Objects.requireNonNull(original);Objects.requireNonNull(originalReceipt);}
    }
    public static final class Installed {
        private final RootRuntimeContext context;
        private final Sources sources;
        private final ScopedQueries held;
        private final ChinaCasesService service;
        private final RootDomainInstallation installation;
        private Installed(RootRuntimeContext actual,Sources sources) {
            context=actual;this.sources=sources;
            held=new ScopedQueries(()->{
                try {var same=context.borrowedSession();return new QueryPorts(context.reads(),context.archive().withSession(same),context.frameLoader(),same);}
                catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
            });
            // These methods are not used by query(). Legacy action helpers cannot bypass the original Root authority.
            var soleActions=new ActionCoordinatorPort(){
                @Override public ActionReceipt execute(ActionCommand command){return context.actions().execute(command);}
                @Override public ActionReceipt reconcile(String id){return context.actions().reconcile(id);}
            };
            var original=new ChinaCasesFacade(held,soleActions,historyFactory(sources));service=new ChinaCasesService(original);
            Set<OperationKey> queryOps=Arrays.stream(Method.values()).filter(Method::readOnly)
                    .map(method->new OperationKey(method.family().step())).collect(java.util.stream.Collectors.toUnmodifiableSet());
            var installedReads=original.readContracts().stream().filter(contract->queryOps.contains(contract.operation()))
                    .map(contract->new RootReadContractCatalog.InstalledRead(contract,sources.originalDecoder())).toList();
            require(installedReads.size()==10,"exact ten original ChinaCases query objects required");
            var effect=new NativeEffectRegistry.Binding(ACTIVATE,sources.rootProduct(),this::prepareNative,this::observeAck);
            var action=new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(TRANSPORT_CAP),sources.publicCodec());
            var replay=new NativeRecordedEvidenceVerifier.Binding(ACTIVATE,sources.publicCodec(),this::verifySettlement);
            installation=new RootDomainInstallation("china-cases-public-eleven",List.of(),installedReads,List.of(),List.of(action),List.of(),List.of(replay),
                    List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public ChinaCasesService service(){return service;}
        public RootRuntimeContext context(){return context;}
        public RootDomainInstallation installation(){return installation;}

        ChinaCasesService.ReadResponse query(ReadRequest request,Complete actual,DriverSnapshotFacts.Known known,Session same,Instant deadline)throws IOException {
            requireOwner(actual,known,same,deadline);
            var originalContext=queryContext(actual,deadline);
            var hello=context.transport().originalHello();
            var metadata=helloContext(actual,originalContext,hello);
            ChinaCasesService.ReadOutcome result=held.within(actual,same,hello,()->service.query(request,metadata));
            requireOwner(actual,known,same,deadline);
            if(result instanceof ChinaCasesService.Unavailable unavailable) {
                Optional<PublicServiceFailure> originalFailure=RootChinaCasesPublicStepProducts.originalDirectDriverFailure(
                        unavailable,service.originalFacade(),request.method().family(),originalContext);
                if(originalFailure.isPresent())throw originalFailure.orElseThrow();
                throw new IOException("actual original ChinaCases READ unavailable: "+unavailable.reason());
            }
            return ((ChinaCasesService.Known)result).response();
        }
        private void requireOwner(Complete actual,DriverSnapshotFacts.Known known,Session same,Instant deadline)throws IOException {
            context.writer().requireSession(same);context.requireCurrent(deadline);
            var root=context.core().sessionAccess().current();
            require(root.ownedBy(context.core())&&!root.isRetired()&&context.actions()==root&&context.adopted()==root.driver()
                    &&root.writer()==context.writer()&&root.archive()==context.archive(),"ChinaCases crossed actual current Root/writer/Driver");
            require(actual.source().equals(context.source())&&actual.sessionId().equals(root.identity().sessionId())
                    &&known.observation().isPresent(),"ChinaCases requires actual current source-bound Driver observation");
            var facts=known.observation().orElseThrow();
            require(facts.source().equals(actual.source())&&facts.publicRevision().equals(actual.identity().frame().revision())
                    &&facts.nativeRevision().equals(actual.identity().frame().identity().nativeRevision())
                    &&facts.snapshotId().equals(actual.identity().frame().snapshotId())&&facts.transport().connectionGeneration().equals(actual.connectionGeneration()),
                    "ChinaCases actual Known facts differ from the held frame");
        }
        ActionCommand command(ActionRequest request,Complete actual,DriverSnapshotFacts.Known known,Session same,Instant deadline)throws IOException {
            requireOwner(actual,known,same,deadline);requireActionFrame(request,queryContext(actual,deadline));
            require(context.transport().originalHello().capabilities().contains(TRANSPORT_CAP),"original scoreboard fail-closed transport contract is not advertised");
            return commandFor(request,actual,deadline);
        }
        private NativeRequest prepareNative(ActionCommand command) {return preparePrimitive(command);}
        private NativeEffectRegistry.Projected observeAck(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
            return projectAck(command,attempt,dispatch,scopedArchive(),context.frameLoader());
        }
        private ActionPorts.OutcomeArchive scopedArchive(){try{return context.archive().withSession(context.borrowedSession());}catch(IOException unavailable){throw new UncheckedIOException(unavailable);}}
        private void verifySettlement(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
            verifyArchived(receipt,archive,context.frameLoader());
        }
        ActionResponse response(ActionRequest request,ActionReceipt receipt,ActionPorts.OutcomeArchive archive,Session same,Instant deadline)throws IOException {
            context.writer().requireSession(same);context.requireCurrent(deadline);
            var canonical=ContinuityActionJournal.lookup(same.head().state(),receipt.command().actionId(),archive)
                    .orElseThrow(()->new IOException("scoreboard receipt is absent from actual canonical writer"));
            require(canonical.equals(receipt)&&decodeCommand(receipt.command()).equals(request),"scoreboard canonical request/receipt changed");
            ExactRef reference=archive.receiptReferenceOf(receipt);require(archive.loadReceipt(reference).equals(receipt),"scoreboard receipt archive changed");
            var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow(()->new IOException("original scoreboard was not dispatched"));
            var dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow(()->new IOException("scoreboard outcome is unknown; no replay"));
            if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())throw new IOException("scoreboard has no successful original native result; no replay");
            var actual=originalAction(receipt.command(),attempt,ack,archive,context.frameLoader());
            requireCurrentAfter(actual.frame(),same,deadline);
            RawJson encoded=PublicDataJson.encode(ChinaCasesCodec.encodeActionResult(request,actual.context(),actual.raw()));
            return new ActionResponse(encoded,receipt,reference);
        }
        private void requireCurrentAfter(Complete original,Session same,Instant deadline)throws IOException {
            context.adopted().authority().withFrozenFacts(same,frozen->{
                require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual Driver unavailable after scoreboard ACK");
                var known=(DriverSnapshotFacts.Known)frozen.state();var facts=known.observation().orElseThrow(()->new IOException("actual scoreboard observation missing"));
                var current=context.transport().currentSnapshot(deadline);
                var rebuilt=context.core().observationAssembler().assemble(current,facts,original.originalEvidence());
                require(rebuilt instanceof Complete,"scoreboard ACK crossed the original ordinary frame");sameFrame(original,(Complete)rebuilt);return null;
            });
        }
    }

    /** Existing actual port/archive/frame loader, resolved once per read. No new authority or synthetic Known is created. */
    record QueryPorts(PlanningReadPort reads,ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames,Session same) {
        QueryPorts {Objects.requireNonNull(reads);Objects.requireNonNull(archive);Objects.requireNonNull(frames);Objects.requireNonNull(same);}
    }
    @FunctionalInterface interface ReadWork<T>{T read()throws IOException;}
    static final class ScopedQueries implements PlanningReadPort {
        private record Scope(Complete frame,Session same,NativeWire.Hello hello,Thread thread) { }
        private final Supplier<QueryPorts> actual;
        private final ThreadLocal<Scope> scope=new ThreadLocal<>();
        ScopedQueries(Supplier<QueryPorts> actual){this.actual=Objects.requireNonNull(actual);}
        <T>T within(Complete frame,Session same,NativeWire.Hello hello,ReadWork<T> work)throws IOException {
            require(scope.get()==null,"ChinaCases query scope cannot nest");scope.set(new Scope(Objects.requireNonNull(frame),Objects.requireNonNull(same),Objects.requireNonNull(hello),Thread.currentThread()));
            try{return work.read();}finally{scope.remove();}
        }
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            Scope held=scope.get();require(held!=null&&held.thread()==Thread.currentThread(),"ChinaCases query must retain actual Root READ scope");
            QueryPorts ports=Objects.requireNonNull(actual.get());require(ports.same()==held.same(),"ChinaCases read crossed borrowed writer session");
            require(request.before().equals(held.frame().identity())&&request.source().equals(held.frame().source())
                    &&request.sessionId().equals(held.frame().sessionId())&&contract.operation().equals(request.operation()),"ChinaCases request differs from held actual frame");
            var result=ports.reads().read(held.same(),contract,request);
            if(result instanceof PlanningReadResult.Known<T> known){
                verifyKnown(held.frame(),request,known,ports.archive(),ports.frames());
                for(var guard:List.of(known.receipt().before(),known.receipt().after()))require(Arrays.equals(held.hello().packet().value(),
                        ports.archive().readOriginalPacket(guard.binding().capabilityEvidence())),"ChinaCases original READ guard HELLO differs from actual held source");
            }
            return result;
        }
    }
    static <T>void verifyKnown(Complete expected,PlanningReadRequest requested,PlanningReadResult.Known<T> known,
            ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames) {
        var receipt=known.receipt();require(receipt.request().equals(requested),"ChinaCases returned a different original request");
        require(archive.readReferenceOf(receipt).equals(known.originalReceipt())&&archive.loadRead(known.originalReceipt()).equals(receipt),"ChinaCases original READ archive changed");
        require(archive.load(archive.referenceOf(receipt.original())).equals(receipt.original()),"ChinaCases original native dispatch archive changed");
        for(var guard:List.of(receipt.before(),receipt.after())) {
            require(guard.paused()&&guard.mapReady(),"ChinaCases original query requires paused ready map; no fabricated MainMenu wrapper");
            var binding=guard.binding();sameFrame(expected,RootGuardEvidence.loadFrame(binding,archive,frames));
            require(binding.observed().equals(expected.identity())&&binding.source().equals(expected.source())&&binding.sessionId().equals(expected.sessionId())
                    &&binding.connectionGeneration().equals(expected.connectionGeneration())&&guard.originalBindingSha256().equals(expected.fullBindingSha256()),"ChinaCases original source/frame changed across query");
        }
    }
    static void sameFrame(Complete expected,Complete actual) {
        require(expected.identity().equals(actual.identity())&&expected.source().equals(actual.source())&&expected.sessionId().equals(actual.sessionId())
                &&expected.connectionGeneration().equals(actual.connectionGeneration())&&expected.semantic().equals(actual.semantic())
                &&expected.originalEvidence().equals(actual.originalEvidence())&&expected.observedAt().equals(actual.observedAt())
                &&expected.fullBindingSha256().equals(actual.fullBindingSha256()),"ChinaCases original actual frame differs");
    }
    private static ChinaCasesFacade.Context queryContext(Complete frame,Instant deadline){return new ChinaCasesFacade.Context(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),deadline);}
    static ChinaCasesService.Context helloContext(Complete actual,ChinaCasesFacade.Context query,NativeWire.Hello hello) {
        require(hello.pid()==actual.identity().game().pid()&&hello.connectionGeneration().equals(actual.connectionGeneration())&&hello.buildMatch(),"ChinaCases HELLO differs from actual Native frame");
        byte[] packet=hello.packet().value();ObjectNode original=PublicDataJson.object(new RawJson(Arrays.copyOfRange(packet,4,packet.length)));
        var version=original.get("expected_ck3_version");
        if(version==null||version.isNull()||version.isTextual()&&version.textValue().isEmpty())version=original.get("game_version");
        String bridge=hello.bridgeVersion();
        if(actual.semantic().get("diagnostics") instanceof OpportunityJson.Obj diagnostics) {
            var diagnostic=diagnostics.get("bridge_version");
            require(diagnostic==null||diagnostic instanceof OpportunityJson.Nil||diagnostic instanceof OpportunityJson.Text,"actual bridge version diagnostic must be string or null");
            if(diagnostic instanceof OpportunityJson.Text text&&!text.value().isEmpty())bridge=text.value();
        }
        return new ChinaCasesService.Context(query,bridge,hello.adapterId(),StrictJson.text(version),hello.gameSha256());
    }
    static ActionCommand commandFor(ActionRequest request,Complete actual,Instant deadline) {
        requireActionFrame(request,queryContext(actual,deadline));
        var expected=new ExpectedPostcondition(1,actual.identity(),actual.source(),ACK_SCHEMA,
                List.of(new ExpectedBoolean(new FieldKey("scoreboard_modal_effective_visible"),!request.action().wire().equals("close"))));
        ObjectNode identity=StrictJson.object().put("schema","china-cases/public-scoreboard-intent/v1").put("machine_id",actual.identity().machineId())
                .put("session_id",actual.sessionId()).put("episode_run_id",actual.identity().frame().episodeRunId())
                .put("snapshot_id",actual.identity().frame().snapshotId()).put("public_revision",actual.identity().frame().revision().toString())
                .put("observation_version",actual.identity().observationVersion()).put("source_machine_id",actual.source().machineId())
                .put("source_observed_at_utc",actual.source().observedAtUtc()).put("source_exact_build",actual.source().exactBuild());
        identity.set("game",actual.identity().game().toJson());identity.set("source_ref",actual.source().sourceRef().toJson());
        identity.set("arguments",OpportunityJson.toNode(request.nativeArguments()));
        String actionId="china-scoreboard-"+DriverJson.sha256(PublicDataJson.encode(identity).bytes());
        return new ActionCommand(actionId,actual.identity(),actual.source(),actual.sessionId(),ACTIVATE,request.nativeArguments(),expected,
                new Claims(Set.of(),Set.of(),Set.of(actual.identity().frame().identity().player()),Set.of("china-scoreboard-provider")),deadline);
    }
    private static void requireActionFrame(ActionRequest request,ChinaCasesFacade.Context actual) {
        require(request.expectedRevision().equals(actual.before().frame().revision())&&request.expectedNativeRevision().equals(actual.before().frame().identity().nativeRevision())
                &&request.expectedConnectionGeneration().equals(actual.connectionGeneration())
                &&request.expectedPlayerCharacterId()==actual.before().frame().identity().player().intValueExact(),"scoreboard original public/native/player/connection binding is stale");
    }
    private static void requireExpected(ActionCommand command) {
        require(command.operation().equals(ACTIVATE)&&command.expected().observerSchema().equals(ACK_SCHEMA)
                &&command.expected().before().equals(command.before())&&command.expected().source().equals(command.source())
                &&command.expected().values().equals(List.of(new ExpectedBoolean(new FieldKey("scoreboard_modal_effective_visible"),
                        !OpportunityJson.text(command.arguments().get("action"),"action").equals("close")))),"scoreboard public ACK binding changed its independent visible-state expectation");
    }
    static ActionRequest decodeCommand(ActionCommand command) {
        requireExpected(command);ObjectNode n=(ObjectNode)OpportunityJson.toNode(command.arguments());
        require(n.has("expected_public_revision")&&!n.has("expected_revision"),"scoreboard native/public revision vocabulary differs");
        n.set("expected_revision",n.remove("expected_public_revision"));
        // Original native fields are exact integral tokens, so public safe-number limits must not rewrite their values.
        for(String key:Set.of("expected_revision","expected_native_revision","expected_connection_generation","expected_observation_sequence","expected_observed_state_revision")) {
            require(n.get(key)!=null&&n.get(key).isIntegralNumber(),"scoreboard original native uint64 requires integer token");n.put(key,n.get(key).bigIntegerValue().toString());
        }
        ActionRequest decoded=ChinaCasesCodec.decodeAction(n);require(decoded.nativeArguments().equals(command.arguments()),"scoreboard original arguments changed on roundtrip");return decoded;
    }
    static NativeRequest preparePrimitive(ActionCommand command) {
        ActionRequest request=decodeCommand(command);requireExpected(command);
        return new NativeRequest(ACTIVATE.value(),TRANSPORT_CAP,new RawJson(DriverJson.encode(request.nativeArguments())));
    }
    static NativeEffectRegistry.Projected projectAck(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames) {
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return NativeEffectRegistry.Projected.pending(
                "original scoreboard native result failed or is unknown; no replay",List.of(attempt.guard().nativeEvidence()));
        var original=originalAction(command,attempt,ack,archive,frames);ObjectNode data=PublicDataJson.object(original.raw());
        if(!bool(data.get("accepted")))return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(
                new ActionState.Rejected(attempt.requestId(),StrictJson.text(data.get("rejection_reason")),archive.referenceOf(dispatch))),Optional.empty());
        return NativeEffectRegistry.Projected.pending("original scoreboard ACK requires an independent provider query; no verified effect and no replay",List.of(archive.referenceOf(dispatch)));
    }
    static void verifyArchived(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames) {
        require(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Rejected,
                "ACK-only public scoreboard binding cannot grant an Applied/control/frontend settlement");
        var settled=(ActionState.Settled)receipt.state();require(settled.dispatch() instanceof NativeActionPort.AckReceived,"scoreboard rejection lacks original ACK envelope");
        var actual=originalAction(receipt.command(),settled.attempt(),(NativeActionPort.AckReceived)settled.dispatch(),archive,frames);
        ObjectNode n=PublicDataJson.object(actual.raw());var rejected=(ActionState.Rejected)settled.settlement();
        require(!bool(n.get("accepted"))&&rejected.reason().equals(StrictJson.text(n.get("rejection_reason")))
                &&rejected.originalEvidence().equals(archive.referenceOf(settled.dispatch())),"scoreboard rejection differs from original native result");
    }
    record OriginalAction(ActionRequest request,ChinaCasesFacade.Context context,Complete frame,RawJson raw) { }
    static OriginalAction originalAction(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,
            ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames) {
        require(ack.nativeOk(),"scoreboard outer Native result failed; no public ACK or effect qualification");
        ActionRequest request=decodeCommand(command);Complete frame=RootGuardEvidence.loadFrame(attempt.guard(),archive,frames);
        require(command.before().equals(frame.identity())&&command.source().equals(frame.source())&&command.sessionId().equals(frame.sessionId())
                &&attempt.requestId().equals(ack.requestId()),"scoreboard original command/guard/ACK binding changed");
        require(attempt.preparedRequest().equals(archive.loadRequest(archive.requestReferenceOf(attempt.preparedRequest())))
                &&attempt.preparedRequest().step().equals(ACTIVATE.value())&&attempt.preparedRequest().requiredCapability().equals(Optional.of(TRANSPORT_CAP))
                &&new RawJson(DriverJson.encode(request.nativeArguments())).equals(attempt.preparedRequest().additionalFields()),"scoreboard actual prepared request changed");
        require(ack.equals(archive.load(archive.referenceOf(ack)))&&ack.outbound().isPresent(),"scoreboard ACK lacks exact retained native dispatch/outbound");
        ack.custody().orElseThrow(()->new IllegalArgumentException("scoreboard ACK lacks actual native request chronology")).verify(ack,attempt.guard());
        try {
            var sent=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
            require(sent.requestId().equals(attempt.requestId())&&sent.step().equals(ACTIVATE.value())
                    &&sent.expectedRevision().equals(Optional.of(request.expectedNativeRevision()))&&sent.expectedSnapshotRevision().isEmpty()
                    &&DriverJson.object(sent.normalizedAdditionalFields().value(),ActionCommand.MAX_ARGUMENT_BYTES).equals(request.nativeArguments()),
                    "scoreboard original outbound packet differs from actual prepared request/revision");
            require(NativeWire.decode(ack.originalPacket()) instanceof NativeWire.CommandResult,"scoreboard original ACK packet is not a command result");
            var received=(NativeWire.CommandResult)NativeWire.decode(ack.originalPacket());
            require(received.requestId().equals(ack.requestId())&&received.nativeOk()==ack.nativeOk()&&received.result().presence()==NativeWire.Presence.VALUE
                    &&Arrays.equals(received.payload().value(),ack.originalFrame().bytes())
                    &&Arrays.equals(received.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),
                    "scoreboard original result token/native frame differs from retained packet");
            byte[] bytes=archive.readOriginalPacket(attempt.guard().capabilityEvidence());
            require(bytes.length==attempt.guard().capabilityEvidence().bytes()&&DriverJson.sha256(bytes).equals(attempt.guard().capabilityEvidence().sha256()),"scoreboard original HELLO changed");
            require(NativeWire.decode(bytes) instanceof NativeWire.Hello,"scoreboard guard capability evidence is not original HELLO");
            NativeWire.Hello hello=(NativeWire.Hello)NativeWire.decode(bytes);
            require(hello.pid()==command.before().game().pid()&&hello.connectionGeneration().equals(frame.connectionGeneration())&&hello.buildMatch()
                    &&hello.capabilities().contains(TRANSPORT_CAP),"scoreboard original transport contract/source differs");
            var before=queryContext(frame,command.deadline());
            RawJson raw=ack.originalResultToken().orElseThrow(()->new IllegalArgumentException("scoreboard original result token absent"));
            ChinaCasesCodec.validateActionResult(request,before,raw,hello.capabilities().contains(PRODUCTION_CAP));
            return new OriginalAction(request,before,frame,raw);
        }catch(IOException unavailable){throw new UncheckedIOException("original scoreboard HELLO unavailable",unavailable);}
    }

    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry) {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        try {
            ExactRef source=context.source(RootChinaCasesPublicProducts.class);
            context.source(RootChinaCasesPublicStepProducts.class);
            context.source(PublicServiceFailure.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ChinaCasesContract.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ChinaCasesCodec.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ChinaCasesService.class);
            register(registry,source,request->{
                Instant deadline=context.clock().instant().plus(context.observationTimeout());
                try{return context.withCurrent(root->{Installed installed=context.installed(root).additionalDomains().chinaCases();
                    return root.withPublicObservation(deadline,(actual,known,same)->installed.query(request,actual,known,same,deadline));});}
                catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
            },request->{
                Instant deadline=context.clock().instant().plus(context.actionTimeout());
                try{return context.withCurrent(root->{Installed installed=context.installed(root).additionalDomains().chinaCases();
                    return root.executePublicAction(deadline,(actual,known,same)->installed.command(request,actual,known,same,deadline),
                            (receipt,archive,same)->installed.response(request,receipt,archive,same,deadline));});}
                catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
            });
            return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
        }catch(IOException unavailable){return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),Arrays.stream(Method.values())
                .map(method->new RootRuntimePublicCatalog.DefinitionGap(method.publicName(),"actual selected ChinaCases source closure unavailable: "+unavailable.getMessage())).toList());}
    }
    /** Exact same registration producer used by pre-Core factory and strict registry regressions. */
    static void register(PublicBindings registry,ExactRef source,PublicRoutes.Handler<ReadRequest,ChinaCasesService.ReadResponse> read,
            PublicRoutes.Handler<ActionRequest,ActionResponse> activate) {
        for(Method method:Method.values())if(method.readOnly())registry.register(publicMethod(method),ReadRequest.class,ChinaCasesService.ReadResponse.class,read,
                n->ChinaCasesCodec.decodeRead(method,required(n)),result->PublicDataJson.encode(ChinaCasesCodec.encodeReadResult(result)),
                new PublicRoutes.Target(RootChinaCasesPublicProducts.class.getName(),"query",source),PublicRoutes.Status.IMPLEMENTED,
                "original source-bound same-frame paused-map ChinaCases READ; actual unavailable reason retained");
        registry.register(PublicMethod.ACTIVATE_ZHONGGUO_SCOREBOARD_V1,ActionRequest.class,ActionResponse.class,activate,n->ChinaCasesCodec.decodeAction(required(n)),
                ActionResponse::publicJson,new PublicRoutes.Target(RootChinaCasesPublicProducts.class.getName(),"activate",source),PublicRoutes.Status.IMPLEMENTED,
                "original Root-only scoreboard transport ACK; independent effect remains pending and UNKNOWN is not replayed");
    }
    static PublicMethod publicMethod(Method method){return switch(method){
        case B1->PublicMethod.QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1;case CASE->PublicMethod.QUERY_ZHONGGUO_CASE_SNAPSHOT_V1;
        case AI_OWNED->PublicMethod.QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1;case RESULT->PublicMethod.QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1;
        case PIP->PublicMethod.QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1;case PROMOTION->PublicMethod.QUERY_ZHONGGUO_PROMOTION_COMPENSATION_POSTCONDITION_V1;
        case AF5->PublicMethod.QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1;case PROJECTS->PublicMethod.QUERY_ZHONGGUO_PROJECTS_METRICS_POSTCONDITION_V1;
        case INCIDENT->PublicMethod.QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1;case SCOREBOARD->PublicMethod.QUERY_ZHONGGUO_SCOREBOARD_STATE_V1;
        case ACTIVATE_SCOREBOARD->PublicMethod.ACTIVATE_ZHONGGUO_SCOREBOARD_V1;};}
    private static void require(boolean value,String reason){StrictJson.require(value,reason);}
    private static ObjectNode required(PublicBindings.Arguments value){require(value instanceof PublicBindings.Value,"ChinaCases requires the original named argument object; missing/null are distinct");return PublicDataJson.object(((PublicBindings.Value)value).original());}
    private static boolean bool(com.fasterxml.jackson.databind.JsonNode value){require(value!=null&&value.isBoolean(),"exact boolean required");return value.booleanValue();}
}
