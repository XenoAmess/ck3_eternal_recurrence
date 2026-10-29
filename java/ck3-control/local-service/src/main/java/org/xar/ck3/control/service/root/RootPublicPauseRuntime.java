package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.advance.GenericPublicPauseRecovery.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.application.readiness.ReadinessAuthority.PhysicalReadLease;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** The original public pause owns one canonical Java parent and at most two actual reserved primitives. */
public final class RootPublicPauseRuntime {
    private RootPublicPauseRuntime() { }
    public static final String HANDLER="original-public-pause-with-recovery/v1";
    public static final OperationKey PUBLIC_STEP=new OperationKey("pause-map");
    public static Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected)throws IOException {
        return new Prepared(inputs,selected);
    }
    public record Sources(ExactRef runtime,ExactRef product,ExactRef algorithm,List<ExactRef> producers) {
        public Sources {
            Objects.requireNonNull(runtime);Objects.requireNonNull(product);Objects.requireNonNull(algorithm);
            producers=List.copyOf(producers);
            require(!producers.isEmpty()&&producers.size()<=64&&producers.containsAll(List.of(runtime,product,algorithm))
                    &&producers.stream().allMatch(source->source.bytes()>0),"complete public pause producer identities required");
        }
    }
    public static Prepared prepare(Sources sources){return new Prepared(Objects.requireNonNull(sources));}
    public static final class Prepared {
        private final Optional<RootRuntimeSelectedSources> selected;
        private final ExactRef runtime,product,algorithm;
        private final List<ExactRef> sources;
        private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private Prepared(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected)throws IOException {
            Objects.requireNonNull(inputs);this.selected=Optional.of(Objects.requireNonNull(selected));
            selected.requireInputs(inputs);
            runtime=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootPublicPauseRuntime.class);
            product=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootPublicPauseStepProducts.class);
            algorithm=selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,GenericPublicPauseRecovery.class);
            var all=new LinkedHashSet<ExactRef>();all.add(runtime);all.add(product);all.add(algorithm);
            all.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootPublicPausePublicResult.class));
            all.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootPublicPauseArchiveClassifier.class));
            all.add(selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,ControlSequenceObservation.class));
            all.add(inputs.source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER));
            sources=List.copyOf(all);
        }
        private Prepared(Sources configuration) {
            selected=Optional.empty();runtime=configuration.runtime();product=configuration.product();
            algorithm=configuration.algorithm();sources=configuration.producers();
        }
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public List<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
            if(core!=null&&core!=actual)throw new IOException("public pause cannot replace its original Core");
            core=Objects.requireNonNull(actual);
        }
        public synchronized Installed install(RootRuntimeContext context,RootAdvanceInfrastructureFactory.Installed infrastructure)throws IOException {
            require(core!=null&&context.core()==core,"public pause requires its identical privately bound Core");
            var old=attempts.get(context);if(old!=null){if(old.value!=null){require(old.value.infrastructure==infrastructure,"same pause infrastructure required");return old.value;}throw new IOException("partial public pause installation cannot replay",old.failure);}
            require(attempts.size()<64,"finite per-Game public pause installations required");
            var attempt=new Attempt();attempts.put(context,attempt);
            try {
                if(selected.isPresent())selected.orElseThrow().requireLoadedClasses(context.game().launchPlan());
                attempt.value=new Installed(context,infrastructure,this);return attempt.value;
            }
            catch(IOException|RuntimeException failure){attempt.failure=failure;throw failure;}
        }
        private static final class Attempt {Installed value;Throwable failure;}
    }
    /** Only Prepared can construct this capability. Parsed proof DATA cannot construct an Installed issuer. */
    public static final class Installed implements CompositeActionPort,RootExecutableBindings.PublicPauseAuthority {
        private final RootRuntimeContext context;
        private final RootAdvanceInfrastructureFactory.Installed infrastructure;
        private final Prepared prepared;
        private final RootDomainInstallation installation;
        private RootInstalledCatalog catalog;
        private RootPublicStepExecution.OwnedAction publicProduct;
        private boolean inventoryBound;
        private final ThreadLocal<Call> current=new ThreadLocal<>();
        private Installed(RootRuntimeContext context,RootAdvanceInfrastructureFactory.Installed infrastructure,Prepared prepared)throws IOException {
            this.context=Objects.requireNonNull(context);this.infrastructure=Objects.requireNonNull(infrastructure);this.prepared=prepared;
            var parent=new RootExecutableBindings.CompositeBinding(this,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),prepared.runtime,prepared.algorithm);
            var archived=new NativeRecordedEvidenceVerifier.Binding(ControlSequenceObservation.OPERATION,prepared.runtime,
                    (head,receipt,originals)->{try{verifyReceipt(head,receipt,originals,context.borrowedSession());}catch(IOException failure){throw new UncheckedIOException(failure);}});
            installation=new RootDomainInstallation("actual-public-pause-with-recovery",List.of(),List.of(),List.of(),List.of(),
                    List.of(parent),List.of(archived),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public RootDomainInstallation installation(){return installation;}
        public ExactRef definitionSource(){return prepared.runtime;}
        public CompositeActionPort handler(){return this;}
        public String handlerId(){return HANDLER;}
        public boolean supports(OperationKey operation){return ControlSequenceObservation.OPERATION.equals(operation);}
        public void requireContext(RootRuntimeContext same)throws IOException {if(context!=same)throw new IOException("public pause belongs to another actual context");}
        public void requireOwner(org.xar.ck3.control.contracts.GameGeneration game,String session,G2Source source) {
            require(context.game().generation().equals(game)&&context.game().sessionId().equals(session)&&context.source().equals(source),"public pause crossed actual Game/session/source");
        }
        /** No Root session or observation is requested during pre-adoption installation. */
        public synchronized void postInventoryBind(RootExecutableBindings actual)throws IOException {
            require(context.bindings()==actual,"public pause must bind its actual Root inventory");
            infrastructure.requireOwner(context,actual);
            require(actual.compositeBindings().stream().filter(value->value.handler()==this).count()==1,"public pause handler is not uniquely installed");
            if(inventoryBound)return;actual.bindPublicPauseAuthority(this);inventoryBound=true;
        }
        synchronized void bindPublicProduct(RootInstalledCatalog actual,RootPublicStepExecution.OwnedAction product)throws IOException {
            require(actual.context()==context&&product.owner()!=null,"public pause product crossed its installed catalog");
            if(catalog!=null){require(catalog==actual&&publicProduct==product,"public pause product cannot be rebound");return;}
            catalog=actual;publicProduct=product;
        }
        public List<ExactRef> historyProducerSources(){return prepared.sources;}
        /** Read-only replay by the same installed authority, writer, physical archive and borrowed session. */
        public void verifyArchivedReceipt(Session same,ActionReceipt receipt,ActionPorts.OutcomeArchive actualArchive)throws IOException {
            Objects.requireNonNull(receipt);Objects.requireNonNull(actualArchive);context.writer().requireSession(same);
            require(same==context.borrowedSession()&&inventoryBound&&catalog!=null,
                    "public pause replay requires its installed authority and identical borrowed writer session");
            require(actualArchive instanceof NativeOutcomeArchive,
                    "public pause replay requires its actual physical native archive");
            var nativeArchive=(NativeOutcomeArchive)actualArchive;
            require(nativeArchive.writer()==context.writer()&&nativeArchive.artifactStore()==context.archive().artifactStore(),
                    "public pause replay crossed its original writer or physical archive");
            // withSession rejects a foreign borrowed scope; no live observation or clock check is made here.
            verifyReceipt(same.head(),receipt,nativeArchive.withSession(same),same);
        }
        public boolean matchesParent(ActionCommand command) {
            try {GenericPublicPauseRecovery.validateParent(command);requireOwner(command.before().game(),command.sessionId(),command.source());return true;}
            catch(RuntimeException unavailable){return false;}
        }
        public void validate(ActionCommand parent) {
            require(matchesParent(parent)&&inventoryBound,"only the identical installed public pause handler may run");
            var call=Objects.requireNonNull(current.get(),"actual public Driver invocation is unavailable");
            require(call.parent.equals(parent),"public pause parent differs from its original private preparation");
        }
        public RawJson execute(RootApplicationSession root,PublicPlanningCodec.ExecuteRequest caller,Instant deadline)throws IOException,InterruptedException {
            require(context.actions()==root&&catalog!=null&&catalog.context()==context&&inventoryBound,"public pause requires its actual installed Root");
            require(PUBLIC_STEP.equals(caller.step())&&!caller.h2743(),"only original public pause caller is supported");
            require(catalog.publicSteps().require(caller)==publicProduct&&RootPublicStepFailureOriginals.inGenericDriverCall(caller),
                    "public pause caller is not the active identical source-owned catalog product");
            return root.withPublicStandaloneRead(deadline,same->{
                context.core().requireCurrentForAccess(same,root);
                var originals=context.archive().withSession(same);
                // An earlier unresolved parent is read-only reconciliation; never allocate another action ID.
                var pending=context.core().actions().withFrozen(same,lease->{
                    var found=lease.snapshot().actions().stream().filter(row->matchesParent(row.command())&&!row.settled()).toList();
                    require(found.size()<=1,"multiple unresolved original public pause parents");lease.assertCurrent();return found.stream().findFirst();
                });
                if(pending.isPresent()) {
                    var original=pending.orElseThrow();var result=root.reconcile(same,original.command().actionId());
                    return present(result,originals,same,caller);
                }
                var call=withPhysical(same,deadline,lease->{
                    if(!lease.bridgeCapabilities().contains("game.command.pause-map"))
                        throw new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,"native DLL cannot execute pause-map",Optional.empty());
                    if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue expected
                            &&!expected.value().equals(lease.frame().identity().frame().revision()))
                        throw new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                                "native gameplay revision mismatch: expected "+expected.value()+", current "+lease.frame().identity().frame().revision(),Optional.empty());
                    String id=ActionIds.forDecision(lease.frame().sessionId(),lease.frame().identity(),
                            "public-pause:"+ActionCodec.sha256(PublicPlanningCodec.encodeExecute(caller).bytes()));
                    var expected=new ProposalLifecycle.ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION,lease.frame().identity(),
                            context.source(),ControlSequenceObservation.OBSERVER,ControlSequenceObservation.expected());
                    var parent=new ActionCommand(id,lease.frame().identity(),context.source(),context.game().sessionId(),
                            ControlSequenceObservation.OPERATION,new OpportunityJson.Obj(Map.of()),expected,new Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
                    return new Call(root,caller,same,parent,lease.frame(),lease.driver(),snapshot(lease,originals),deadline);
                });
                require(current.get()==null,"public pause cannot replace an active invocation");current.set(call);
                try(var driver=RootPublicStepFailureOriginals.beginDriver(call.before,call.known,same,caller)) {
                    RootPublicStepFailureOriginals.trackPreparedAction(call.parent);
                    var result=root.execute(same,call.parent);return present(result,originals,same,caller);
                } finally {current.remove();}
            });
        }
        public GuardEvidence verifyParent(WriterContracts.Head head,ActionCommand command) {
            try {
                var call=Objects.requireNonNull(current.get(),"public pause has no actual private caller");
                require(call.parent.equals(command)&&call.same.head().equals(head),"public pause changed its canonical parent/body/head");
                return withPhysical(call.same,command.deadline(),lease->{
                    require(lease.frame().identity().equals(command.before())&&lease.frame().originalEvidence().equals(call.before.originalEvidence()),
                            "public pause current raw/Driver differs from its prepared caller");
                    var archive=context.archive().withSession(call.same);
                    var proof=new ParentProof(command,PublicPlanningCodec.encodeExecute(call.caller),lease.frame().originalEvidence(),
                            NativeEffectEvidence.basis(lease.frame()).driverFacts(),prepared.runtime,prepared.product,prepared.sources,
                            head.state().sequence(),head.digest());
                    var original=archive.preserveMaterial(new RawJson(proof.encode()));call.parentProof=original;
                    var capabilities=archive.preserveMaterial(new RawJson(OpportunityJson.encode(lease.capabilities())));
                    var basis=RootGuardEvidence.preservePhysicalRead(new RootGuardEvidence.PhysicalReadOriginals(lease.frame(),lease.semantic(),
                            lease.originalHello(),lease.originalHeartbeat(),lease.originalSourceQualification(),capabilities),
                            command.operation(),context.core().authorityId(),archive,head);
                    Instant until=lease.validUntil().isBefore(command.deadline())?lease.validUntil():command.deadline();
                    var guard=new GuardEvidence(command.origin(),command.source(),command.sessionId(),lease.frame().connectionGeneration(),
                            command.operation(),lease.frame().originalEvidence(),lease.originalHello(),context.core().authorityId(),lease.frame().observedAt(),until,List.of(basis,original));
                    call.phaseGuards.put(lease.semantic().semantic(),guard);return guard;
                });
            } catch(IOException failure){throw new UncheckedIOException("actual public pause parent source unavailable",failure);}
        }
        public ExactRef verifyReservedPause(Session same,WriterContracts.Head head,ActionCommand child,PhysicalReadLease lease,
                ExecutableStepBindings.InstalledStep definition,ActionPorts.OutcomeArchive archive)throws IOException {
            context.writer().requireSession(same);require(head.equals(same.head()),"pause child changed writer head");
            var scope=ActionChildPlanningScope.reservedParent(same,head,child).orElseThrow(()->new IOException("pause child has no actual canonical reservation"));
            var parent=ContinuityActionJournal.lookup(head.state(),scope.actionId(),archive).orElseThrow();
            require(parent.state() instanceof ActionState.CompositeRunning&&parent.bodySha256().equals(scope.bodySha256()),"pause child has no intact running original parent");
            var execution=((ActionState.CompositeRunning)parent.state()).execution();
            verifyArchivedParent(parent.command(),execution.guard(),archive,same,context.originals());
            var previous=preceding(parent,child,head.state(),archive);require(previous.size()<=1,"public pause permits at most one retry");
            var actual=context.bindings().resolve(child.operation(),child.origin()).orElseThrow();
            require(actual.equals(definition)&&child.operation().equals(PUBLIC_STEP)
                    &&context.bindings().actualActionBinding(PUBLIC_STEP).orElseThrow().preparation()==infrastructure.primitives()
                    &&definition.implementationSource().equals(infrastructure.sources().primitiveProducer())
                    &&definition.decoderSource().equals(infrastructure.sources().primitiveDecoder()),"public pause child is not the same shared primitive");
            var before=RootGuardEvidence.loadFrame(execution.guard(),archive,context.frameLoader());
            require(child.equals(AdvancePrimitives.child(parent.command(),frame(lease.frame()),child.actionId(),"pause-map",child.deadline())),
                    "public pause changed its canonical derived primitive body");
            var call=Objects.requireNonNull(current.get(),"new public pause child needs its original live private caller");
            require(call.same==same&&call.parent.equals(parent.command()),"pause child crossed actual public invocation");
            if(!previous.isEmpty()) {
                ControlSequenceObservation.requireMapUnavailable(previous.getFirst());
                require(call.decision instanceof Retry&&call.retryFrame!=null&&call.retryFrame.identity().equals(lease.frame().identity())
                        &&((Retry)call.decision).expectedNativeRevision().equals(lease.frame().identity().frame().identity().nativeRevision()),
                        "only the exact source-bound APP retry phase may reserve the second child");
            } else require(child.before().equals(parent.command().before()),"first public pause child changed original caller revision");
            var original=NativeEffectEvidence.basis(before);var current=NativeEffectEvidence.basis(lease.frame());
            var verifier=context.bindings().actualArchivedVerifier(PUBLIC_STEP).orElseThrow();
            var proof=new RootDerivedChildEvidence(head.state().sequence(),head.digest(),HANDLER,archive.preserveReceipt(parent),
                    parent.bodySha256(),ActionCodec.bodySha256(child),execution.children().size(),original.nativeFrame(),original.driverFacts(),
                    current.nativeFrame(),current.driverFacts(),prepared.runtime,prepared.algorithm,definition.implementationSource(),
                    definition.decoderSource(),verifier.definitionSource(),lease.originalSourceQualification(),previous.stream().map(archive::receiptReferenceOf).toList());
            return archive.preserveMaterial(proof.encode());
        }
        public void verifyArchivedParent(ActionCommand parent,GuardEvidence guard,ActionPorts.OutcomeArchive archive,Session same,
                OriginalEvidencePort originals)throws IOException {
            require(matchesParent(parent)&&guard.supportingEvidence().size()==2,"exact public pause parent source roles required");
            var reference=guard.supportingEvidence().getLast();var proof=ParentProof.decode(archive.loadMaterial(reference).bytes());
            require(proof.matchesGuard(guard,RootGuardEvidence.frameBasis(guard,archive).driverFacts(),reference)
                    &&proof.parent().equals(parent)&&proof.runtimeSource().equals(prepared.runtime)&&proof.productSource().equals(prepared.product)
                    &&proof.sourceClosure().equals(prepared.sources),"public pause caller/body/catalog source changed");
            same.requireHistoricalState(proof.writerSequence(),proof.writerDigest());RootGuardEvidence.requireHistory(guard,archive,same);
            var caller=PublicPlanningCodec.decodeExecute(org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings.present(proof.originalCaller()));
            require(PUBLIC_STEP.equals(caller.step())&&!caller.h2743(),"archived public pause changed original caller");
            var before=RootGuardEvidence.loadFrame(guard,archive,context.frameLoader());
            verifyPhysicalOriginal(guard,same,archive);
            if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue value)
                require(value.value().equals(before.identity().frame().revision()),"archived pause caller revision differs");
            require(parent.actionId().equals(ActionIds.forDecision(parent.sessionId(),parent.before(),
                    "public-pause:"+ActionCodec.sha256(proof.originalCaller().bytes()))),"archived pause replaced the original caller-derived action ID");
            require(context.bindings().composites().find(parent.operation()).orElseThrow()==this,"public pause handler changed");
            for(var source:prepared.sources){var pin=same.capturePin(source,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
        }
        public void verifyArchivedChild(WriterContracts.Head head,ActionReceipt child,GuardEvidence guard,ActionPorts.OutcomeArchive archive,
                Session same,OriginalEvidencePort originals)throws IOException {
            var proof=RootDerivedChildEvidence.requireGuard(guard,archive);same.requireHistoricalState(proof.actualHeadSequence(),proof.actualHeadDigest());
            var parent=archive.loadReceipt(proof.parentReceipt());require(parent.state() instanceof ActionState.CompositeRunning,"pause child lost original running parent");
            var execution=((ActionState.CompositeRunning)parent.state()).execution();verifyArchivedParent(parent.command(),execution.guard(),archive,same,originals);
            require(proof.handlerId().equals(HANDLER)&&proof.parentImplementation().equals(prepared.runtime)&&proof.parentDecoder().equals(prepared.algorithm)
                    &&proof.childBodySha256().equals(child.bodySha256())&&child.command().operation().equals(PUBLIC_STEP),"archived public pause child source/body differs");
            requireCanonicalOrPreview(head,child,archive);
            var historical=same.requireHistoricalState(proof.actualHeadSequence(),proof.actualHeadDigest());
            ContinuityActionJournal.requireHistoricalReceipt(historical,parent,archive);
            require(execution.children().size()==proof.childOrdinal()&&proof.childOrdinal()>=1&&proof.childOrdinal()<=2,"pause child ordinal differs");
            var current=RootGuardEvidence.loadFrame(guard,archive,context.frameLoader());
            verifyPhysicalOriginal(guard,same,archive);
            var parentBasis=RootGuardEvidence.frameBasis(execution.guard(),archive);var currentBasis=RootGuardEvidence.frameBasis(guard,archive);
            var definition=context.bindings().resolve(child.command().operation(),child.command().origin()).orElseThrow();
            var verifier=context.bindings().actualArchivedVerifier(PUBLIC_STEP).orElseThrow();
            require(proof.parentNative().equals(parentBasis.nativeFrame())&&proof.parentDriver().equals(parentBasis.driverFacts())
                    &&proof.beforeNative().equals(currentBasis.nativeFrame())&&proof.beforeDriver().equals(currentBasis.driverFacts())
                    &&proof.sourceQualification().equals(RootGuardEvidence.sourceQualification(guard,archive))
                    &&proof.childImplementation().equals(definition.implementationSource())&&proof.childDecoder().equals(definition.decoderSource())
                    &&proof.childVerifier().equals(verifier.definitionSource()),"pause child changed actual full native/Driver/source roles");
            require(child.command().equals(AdvancePrimitives.child(parent.command(),frame(current),child.command().actionId(),"pause-map",child.command().deadline())),
                    "archived pause primitive body differs");
            var old=preceding(parent,child.command(),historical,archive);
            require(old.stream().map(archive::receiptReferenceOf).toList().equals(proof.previousChildren()),"pause prior canonical children changed");
            if(!old.isEmpty()) {
                ControlSequenceObservation.requireMapUnavailable(old.getFirst());
                var start=originalSnapshot(execution.guard(),archive);
                var awaiting=GenericPublicPauseRecovery.afterFirst(start,old.getFirst(),parent.command().deadline(),
                        ActionTransitions.attempt(old.getFirst().state()).orElseThrow().submittedAt());
                require(awaiting instanceof AwaitFresh,"second pause lost its original recoverable first phase");
                var retry=GenericPublicPauseRecovery.afterRefresh((AwaitFresh)awaiting,originalSnapshot(guard,archive),guard.observedAt());
                require(retry instanceof Retry&&((Retry)retry).expectedNativeRevision().equals(child.command().before().frame().identity().nativeRevision()),
                        "historical second pause lost its actual fresh same-owner retry basis");
            } else require(child.command().before().equals(parent.command().before()),"historical first pause changed original caller frame");
            for(var source:java.util.stream.Stream.concat(List.of(proof.parentImplementation(),proof.parentDecoder(),proof.childImplementation(),
                    proof.childDecoder(),proof.childVerifier()).stream(),proof.sourceQualification().stream()).toList()){var pin=same.capturePin(source,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
            RootGuardEvidence.requireHistory(guard,archive,same);
        }
        public ActionPorts.PostconditionResult run(ActionCommand parent,Children children)throws InterruptedException {
            try {
                validate(parent);var call=current.get();var archive=context.archive().withSession(call.same);
                require(children.completed().isEmpty(),"public pause run cannot replay an original child");
                ActionReceipt first=children.submit(AdvancePrimitives.child(parent,frame(call.before),children.nextActionId(PUBLIC_STEP),"pause-map",parent.deadline()));
                Decision decision=GenericPublicPauseRecovery.afterFirst(call.starting,first,parent.deadline(),context.clock().instant());
                call.decision=decision;
                for(int waits=0;decision instanceof AwaitFresh&&waits<infrastructure.timings().maximumFrames();waits++){
                    var awaiting=(AwaitFresh)decision;
                    try {
                        var fresh=refresh(call,call.starting.publicRevision().orElseThrow(),archive);
                        decision=GenericPublicPauseRecovery.afterRefresh(awaiting,fresh,context.clock().instant());
                    }catch(IOException unavailable){
                        var at=context.clock().instant();call.waitFailure=Optional.of(preserveWaitFailure(WaitPhase.REFRESH,at,unavailable,archive));
                        decision=GenericPublicPauseRecovery.afterRefreshUnavailable(awaiting,at);
                    }
                    call.decision=decision;
                }
                if(decision instanceof Retry retry) {
                        var second=children.submit(AdvancePrimitives.child(parent,frame(call.retryFrame),children.nextActionId(PUBLIC_STEP),"pause-map",parent.deadline()));
                        decision=GenericPublicPauseRecovery.afterRetry(retry,second,Optional.empty(),context.clock().instant());call.decision=decision;
                        for(int waits=0;decision instanceof AwaitEnding&&waits<infrastructure.timings().maximumFrames();waits++){
                            var ending=(AwaitEnding)decision;
                            try{
                                var last=refresh(call,ending.partial().ending().orElse(retry.partial().refreshed().orElseThrow()).publicRevision().orElseThrow(),archive);
                                decision=GenericPublicPauseRecovery.afterEnding(ending,last,context.clock().instant());
                            }catch(IOException unavailable){
                                var at=context.clock().instant();call.waitFailure=Optional.of(preserveWaitFailure(WaitPhase.ENDING,at,unavailable,archive));
                                decision=GenericPublicPauseRecovery.afterEndingUnavailable(ending,at);
                            }
                            call.decision=decision;
                        }
                }
                return finish(parent,decision,children.completed(),archive);
            } catch(IOException|RuntimeException failure) {
                try {
                    var call=current.get();if(call!=null&&call.decision instanceof Retry retry){
                        var archive=context.archive().withSession(call.same);
                        var retained=ContinuityActionJournal.lookup(call.same.head().state(),parent.actionId(),archive).orElseThrow();
                        var captured=new ArrayList<ActionReceipt>();
                        for(var child:execution(retained.state()).children())
                            captured.add(ContinuityActionJournal.lookup(call.same.head().state(),child.actionId(),archive).orElseThrow());
                        var originals=List.copyOf(captured);
                        if(originals.size()==2){
                            var decision=GenericPublicPauseRecovery.afterRetry(retry,originals.getLast(),Optional.empty(),context.clock().instant());
                            return finish(parent,decision,originals,archive);
                        }
                    }
                } catch(IOException|RuntimeException preservationFailure){if(preservationFailure!=failure)failure.addSuppressed(preservationFailure);}
                return new ActionPorts.Pending("public pause source/recovery unavailable; original children are never replayed: "+failure.getMessage(),List.of());
            }
        }
        /** Reconciliation has no submitter. It can settle a collected direct pause, never start a recovery retry. */
        public ActionPorts.PostconditionResult observe(ActionCommand parent,CompositeExecution retained) {
            try {
                var same=context.borrowedSession();var archive=context.archive().withSession(same);
                verifyArchivedParent(parent,retained.guard(),archive,same,context.originals());
                if(retained.children().size()!=1)return new ActionPorts.Pending("original pause recovery awaits its original proof; no new child is allowed",List.of());
                var child=ContinuityActionJournal.lookup(same.head().state(),retained.children().getFirst().actionId(),archive).orElseThrow();
                infrastructure.replay().verify(child,archive);
                if(!(child.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.PauseConfirmed confirmed))
                    return new ActionPorts.Pending("original pause child is not independently confirmed; no resubmission",List.of());
                var before=RootGuardEvidence.loadFrame(retained.guard(),archive,context.frameLoader());
                var start=originalSnapshot(retained.guard(),archive);
                var decision=GenericPublicPauseRecovery.afterFirst(start,child,parent.deadline(),confirmed.observation().observedAt());
                return finish(parent,decision,List.of(child),archive);
            }catch(IOException|RuntimeException unavailable){return new ActionPorts.Pending("original public pause reconciliation unavailable: "+unavailable.getMessage(),List.of());}
        }
        private ActionPorts.PostconditionResult finish(ActionCommand parent,Decision decision,List<ActionReceipt> children,ActionPorts.OutcomeArchive archive)throws IOException {
            var bytes=GenericPublicPauseRecovery.encode(decision,archive::preserveReceipt);
            var decisionRef=archive.preserveMaterial(new RawJson(bytes));
            var same=context.borrowedSession();
            var actualParent=ContinuityActionJournal.lookup(same.head().state(),parent.actionId(),archive).orElseThrow();
            var parentGuard=execution(actualParent.state()).guard();
            var guards=new LinkedHashMap<ExactRef,GuardEvidence>();guards.put(RootGuardEvidence.semanticReference(parentGuard,archive),parentGuard);
            var call=current.get();
            for(var original:List.of(decision.partial().refreshed(),decision.partial().ending()))if(original.isPresent()){
                var ref=original.orElseThrow().originalSemantic();
                if(!guards.containsKey(ref))guards.put(ref,Objects.requireNonNull(call==null?null:call.phaseGuards.get(ref),"actual phase Root basis is unavailable"));
            }
            var proof=archive.preserveMaterial(new RecordedRecovery(decisionRef,List.copyOf(guards.values()),
                    call==null?Optional.empty():call.waitFailure).encode());
            if(decision.partial().needsOriginalReconciliation())
                return new ActionPorts.Pending("original pause attempt remains UNKNOWN; this exact report cannot authorize a new child",List.of(proof));
            if(decision instanceof Completed completed) {
                var finalFrame=decision.partial().ending().isPresent()
                        ?RootGuardEvidence.loadFrame(Objects.requireNonNull(guards.get(decision.partial().ending().orElseThrow().originalSemantic())),archive,context.frameLoader())
                        :AdvancePrimitiveEvidence.load(children.getLast(),archive,context.frameLoader());
                var refs=children.stream().map(row->new ControlSequenceObservation.Child(row.command().actionId(),row.bodySha256(),archive.receiptReferenceOf(row))).toList();
                return new ActionPorts.ControlSequenceObserved(new ControlSequenceObservation(parent,completed.mode(),finalFrame.identity(),proof,refs,List.of(proof)));
            }
            if(decision instanceof Failed failed)return new ActionPorts.CompositeRejectionObserved(
                    "native pause-map recovery stopped: "+failed.reason().message(),children.stream().map(row->new CompositeExecution.Child(row.command().actionId(),row.bodySha256())).toList(),List.of(proof));
            if(decision instanceof Original&&children.size()==1&&originalRejectionReason(children.getFirst()).isPresent())
                return new ActionPorts.CompositeRejectionObserved(originalRejectionReason(children.getFirst()).orElseThrow(),
                        List.of(new CompositeExecution.Child(children.getFirst().command().actionId(),children.getFirst().bodySha256())));
            return new ActionPorts.Pending("original pause is unresolved; no retry or replay is permitted",List.of(proof));
        }
        public RawJson recordedResult(ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
            require(matchesParent(receipt.command()),"pause result crossed its actual original parent");
            var settlement=receipt.state() instanceof ActionState.CompositeSettled value?value.settlement():null;
            ExactRef reference;
            if(settlement instanceof ActionState.ControlSequenceCompleted completed)reference=completed.observation().proof();
            else if(settlement instanceof ActionState.CompositeRejected rejected&&rejected.evidence().size()==1)reference=rejected.evidence().getFirst();
            else throw new IOException("original public pause has no terminal source-bound report; UNKNOWN is never retried");
            var decision=decodeDecision(reference,archive);GenericPublicPauseRecovery.replay(decision);
            var nativeResults=new ArrayList<Optional<RawJson>>();
            for(var attempt:decision.partial().attempts()) {
                var child=attempt.receipt();
                if(child.isPresent()&&child.orElseThrow().ack().filter(NativeActionPort.AckReceived::nativeOk).isPresent())
                    nativeResults.add(Optional.of(AdvancePrimitiveEvidence.compatiblePauseResult(child.orElseThrow(),archive,context.frameLoader())));
                else if(child.isPresent()&&nativeFailureMessage(child.orElseThrow()).isPresent())
                    nativeResults.add(Optional.of(new RawJson(StrictJson.canonical(StrictJson.object().put("accepted",false).put("status","failed")
                            .put("error",nativeFailureMessage(child.orElseThrow()).orElseThrow())))));
                else nativeResults.add(Optional.empty());
            }
            return GenericPublicPauseRecovery.result(decision,nativeResults);
        }
        private RawJson present(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,Session same,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
            verifyReceipt(same.head(),receipt,archive,same);
            if(receipt.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.CompositeRejected rejected) {
                if(rejected.evidence().isEmpty())
                    throw new PublicServiceFailure(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,
                            "native gameplay step failed: "+rejected.reason(),Optional.of(archive.receiptReferenceOf(receipt)));
                recordedResult(receipt,archive);
                throw new PublicServiceFailure(PublicServiceFailure.Kind.STEP_POSTCONDITION_ERROR,rejected.reason(),Optional.of(rejected.evidence().getFirst()));
            }
            return publicResult(recordedResult(receipt,archive));
        }
        private void verifyReceipt(WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive,Session same)throws IOException {
            var execution=execution(receipt.state());verifyArchivedParent(receipt.command(),execution.guard(),archive,same,context.originals());
            requireCanonicalOrPreview(head,receipt,archive);
            for(var child:execution.children())infrastructure.replay().verify(ContinuityActionJournal.lookup(head.state(),child.actionId(),archive).orElseThrow(),archive);
            if(receipt.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.ControlSequenceCompleted completed) {
                var actual=completed.observation();require(actual.parent().equals(receipt.command()),"pause observation changed parent");
                var children=execution.children().stream().map(child->ContinuityActionJournal.lookup(head.state(),child.actionId(),archive).orElseThrow()).toList();
                actual.validateChildren(execution,children);var decision=verifyReport(actual.proof(),receipt,execution,children,archive,same);
                require(decision instanceof Completed&&((Completed)decision).mode()==actual.mode(),"pause report mode changed");
                var ending=decision.partial().ending();
                var expectedAfter=ending.isPresent()?reportFrame(actual.proof(),ending.orElseThrow().originalSemantic(),archive).identity()
                        :AdvancePrimitiveEvidence.load(children.getLast(),archive,context.frameLoader()).identity();
                require(expectedAfter.equals(actual.after()),"pause control ending lost its exact original physical frame");
            }else if(receipt.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.CompositeRejected rejected) {
                var children=execution.children().stream().map(child->ContinuityActionJournal.lookup(head.state(),child.actionId(),archive).orElseThrow()).toList();
                ActionEffects.validateCompositeChildren(execution,rejected,children);
                if(rejected.evidence().isEmpty()){
                    require(children.size()==1&&originalRejectionReason(children.getFirst()).filter(rejected.reason()::equals).isPresent(),
                            "original public pause rejection changed its sole canonical child cause");
                    var child=children.getFirst();
                    require(GenericPublicPauseRecovery.afterFirst(originalSnapshot(execution.guard(),archive),child,receipt.command().deadline(),
                            ActionTransitions.attempt(child.state()).orElseThrow().submittedAt()) instanceof Original,
                            "recoverable map unavailable rejection lost its required original recovery report");
                }else{
                    require(rejected.evidence().size()==1,"one typed public pause failure report required");
                    var decision=verifyReport(rejected.evidence().getFirst(),receipt,execution,children,archive,same);
                    require(decision instanceof Failed&&rejected.reason().equals("native pause-map recovery stopped: "+((Failed)decision).reason().message()),
                            "pause failure reason changed its actual replayed terminal decision");
                }
            }
        }
        private Decision decodeDecision(ExactRef reference,ActionPorts.OutcomeArchive archive)throws IOException {
            var report=RecordedRecovery.decode(checkedMaterial(reference,archive));
            return GenericPublicPauseRecovery.decode(checkedMaterial(report.decision(),archive).bytes(),new ReplayReader(){
                public Snapshot snapshot(ExactRef ref){return GenericPublicPauseRecovery.snapshot(DriverJson.object(archive.loadFullMaterial(ref).bytes(),DriverJson.MAX_NATIVE_BYTES),ref);}
                public ActionReceipt receipt(ExactRef ref){return archive.loadReceipt(ref);}
            });
        }
        private Decision verifyReport(ExactRef reference,ActionReceipt parent,CompositeExecution execution,List<ActionReceipt> children,
                ActionPorts.OutcomeArchive archive,Session same)throws IOException {
            var report=RecordedRecovery.decode(checkedMaterial(reference,archive));var decision=decodeDecision(reference,archive);
            require(GenericPublicPauseRecovery.replay(decision).equals(decision),"public pause report differs from original pure phase replay");
            var snapshots=new ArrayList<Snapshot>();snapshots.add(decision.partial().starting());
            decision.partial().refreshed().ifPresent(snapshots::add);decision.partial().ending().ifPresent(snapshots::add);
            var required=snapshots.stream().map(Snapshot::originalSemantic).distinct().toList();
            require(report.guards().size()==required.size()&&report.guards().getFirst().equals(execution.guard()),
                    "pause report changed its original parent or physical phase roster");
            for(int i=0;i<required.size();i++){
                var guard=report.guards().get(i);require(RootGuardEvidence.semanticReference(guard,archive).equals(required.get(i)),
                        "pause phase semantic is not its named original Root basis");
                require(guard.supportingEvidence().size()==(i==0?2:1),"pause phase replaced its finite parent/read DATA role");
                require(guard.source().equals(parent.command().source())&&guard.sessionId().equals(parent.command().sessionId())
                        &&guard.operation().equals(parent.command().operation())&&guard.authorityId().equals(context.core().authorityId()),
                        "pause phase crossed its installed operation/source/session");
                RootGuardEvidence.requireHistory(guard,archive,same);var physical=RootGuardEvidence.loadFrame(guard,archive,context.frameLoader());
                verifyPhysicalOriginal(guard,same,archive);
                require(physical.identity().game().equals(parent.command().before().game())
                        &&physical.identity().machineId().equals(parent.command().before().machineId()),"pause phase crossed physical Game/machine");
            }
            require(decision.partial().deadline().equals(parent.command().deadline())&&decision.partial().attempts().size()==children.size()
                    &&!decision.partial().needsOriginalReconciliation(),"a terminal public pause may not discard an UNKNOWN original attempt");
            for(int i=0;i<children.size();i++)require(decision.partial().attempts().get(i).receipt().orElseThrow().equals(children.get(i)),
                    "pause report replaced its same-writer actual canonical child");
            require(report.waitFailure().isPresent()==decision.partial().times().unavailableAt().isPresent(),
                    "pause unavailable phase lost its actual caught diagnostic");
            if(report.waitFailure().isPresent()){
                var diagnostic=WaitFailure.decode(checkedMaterial(report.waitFailure().orElseThrow(),archive));
                require(diagnostic.at().equals(decision.partial().times().unavailableAt().orElseThrow())
                        &&diagnostic.runtimeSource().equals(prepared.runtime)
                        &&decision instanceof Failed&&diagnostic.phase()==(((Failed)decision).reason()==FailureReason.NO_FRESH_SEMANTIC_FRAME?WaitPhase.REFRESH:WaitPhase.ENDING),
                        "pause diagnostic changed original occurrence/phase/source");
            }
            return decision;
        }
        private Complete reportFrame(ExactRef reference,ExactRef semantic,ActionPorts.OutcomeArchive archive) {
            return RecordedRecovery.decode(checkedMaterial(reference,archive)).guards().stream()
                    .filter(guard->RootGuardEvidence.semanticReference(guard,archive).equals(semantic))
                    .map(guard->RootGuardEvidence.loadFrame(guard,archive,context.frameLoader())).findFirst().orElseThrow();
        }
        private Snapshot originalSnapshot(GuardEvidence guard,ActionPorts.OutcomeArchive archive) {
            var ref=RootGuardEvidence.semanticReference(guard,archive);
            return GenericPublicPauseRecovery.snapshot(DriverJson.object(archive.loadFullMaterial(ref).bytes(),DriverJson.MAX_NATIVE_BYTES),ref);
        }
        private static RawJson checkedMaterial(ExactRef reference,ActionPorts.OutcomeArchive archive){
            var original=archive.loadMaterial(reference);require(reference.bytes()==original.bytes().length
                    &&reference.sha256().equals(ActionCodec.sha256(original.bytes())),"original pause material bytes/SHA changed");
            return original;
        }
        private static void requireCanonicalOrPreview(WriterContracts.Head head,ActionReceipt proposed,ActionPorts.OutcomeArchive archive) {
            if(proposed.sequence()<=head.state().sequence()){
                ContinuityActionJournal.requireHistoricalReceipt(head.state(),proposed,archive);return;
            }
            require(proposed.sequence()==Math.addExact(head.state().sequence(),1),"pause candidate is not the actual sole next writer event");
            var previous=ContinuityActionJournal.lookup(head.state(),proposed.command().actionId(),archive).orElseThrow();
            require(previous.command().equals(proposed.command())&&previous.bodySha256().equals(proposed.bodySha256()),
                    "pause next-event candidate changed its actual surviving canonical predecessor");
            ActionTransitions.validate(Optional.of(previous),proposed.command(),proposed.bodySha256(),proposed.state());
            ActionTransitions.composite(proposed.state()).ifPresent(execution->require(
                    ActionTransitions.composite(previous.state()).orElseThrow().equals(execution),
                    "pause terminal candidate changed the actual canonical parent/child roster"));
        }
        private void verifyPhysicalOriginal(GuardEvidence guard,Session same,ActionPorts.OutcomeArchive archive)throws IOException {
            var driver=RootGuardEvidence.originalDriverSource(guard,archive);
            var identity=new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(
                    context.game().machineId(),context.game().generation(),context.game().sessionId());
            context.semanticVerifier().verify(same,identity,new org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence(
                    guard.observed(),RootGuardEvidence.semanticReference(guard,archive),guard.nativeEvidence(),driver.stampRef(),driver.driverRef(),guard.observedAt()));
            context.sources().requireArchivedOrigin(same,guard,archive);
            for(var ref:java.util.stream.Stream.concat(java.util.stream.Stream.of(guard.capabilityEvidence()),RootGuardEvidence.sourceQualification(guard,archive).stream()).toList()){
                byte[] bytes=context.originals().read(same,ref,WriterContracts.MAX_PIN_BYTES);
                require(bytes.length==ref.bytes()&&ref.sha256().equals(ActionCodec.sha256(bytes)),"pause physical original/source pin changed");
            }
        }
        private void capturePhase(Call call,PhysicalReadLease lease,ActionPorts.OutcomeArchive archive)throws IOException {
            var capabilities=archive.preserveMaterial(new RawJson(OpportunityJson.encode(lease.capabilities())));
            var basis=RootGuardEvidence.preservePhysicalRead(new RootGuardEvidence.PhysicalReadOriginals(lease.frame(),lease.semantic(),
                    lease.originalHello(),lease.originalHeartbeat(),lease.originalSourceQualification(),capabilities),
                    call.parent.operation(),context.core().authorityId(),archive,call.same.head());
            var until=lease.validUntil().isBefore(call.deadline)?lease.validUntil():call.deadline;
            var guard=new GuardEvidence(new CommandOrigin.Gameplay(lease.frame().identity()),context.source(),context.game().sessionId(),
                    lease.frame().connectionGeneration(),call.parent.operation(),lease.frame().originalEvidence(),lease.originalHello(),
                    context.core().authorityId(),lease.frame().observedAt(),until,List.of(basis));
            call.phaseGuards.putIfAbsent(lease.semantic().semantic(),guard);
        }
        private Snapshot refresh(Call call,java.math.BigInteger afterPublic,ActionPorts.OutcomeArchive archive)throws IOException,InterruptedException {
            infrastructure.timings().requireOriginal(context.archive());
            var now=context.clock().instant();var until=now.plus(infrastructure.timings().commandTimeout());
            if(!until.isBefore(call.deadline))until=call.deadline.minusNanos(1);
            if(!now.isBefore(until))throw new IOException("public pause total deadline has no remaining actual snapshot wait");
            var adopted=context.adopted();adopted.producer().requireSameTransport(context.transport(),context.source());
            var received=adopted.observations().waitForChange(afterPublic,until,call.deadline,true).actual();
            return withPhysical(call.same,call.deadline,lease->{
                require(lease.frame().identity().frame().revision().compareTo(received.identity().frame().revision())>=0,
                        "public pause lost the actual waited packet's Driver publication");
                call.retryFrame=lease.frame();capturePhase(call,lease,archive);return snapshot(lease,archive);
            });
        }
        private Snapshot snapshot(PhysicalReadLease lease,ActionPorts.OutcomeArchive archive) {
            return GenericPublicPauseRecovery.snapshot(DriverJson.object(archive.loadFullMaterial(lease.semantic().semantic()).bytes(),DriverJson.MAX_NATIVE_BYTES),lease.semantic().semantic());
        }
        static Optional<String> nativeFailureMessage(ActionReceipt receipt) {
            var ack=receipt.ack();if(ack.isPresent()&&!ack.orElseThrow().nativeOk()) {
                var packet=DriverJson.object(ack.orElseThrow().originalFrame().bytes(),DriverJson.MAX_NATIVE_BYTES);
                var error=packet.get("error") instanceof OpportunityJson.Text text?text.value():"unknown error";
                return Optional.of("native gameplay step failed: "+error);
            }
            if(receipt.state() instanceof ActionState.RejectedBeforeDispatch rejected)return Optional.of(rejected.dispatch().proof().reason());
            return Optional.empty();
        }
        static Optional<String> originalRejectionReason(ActionReceipt receipt){
            if(receipt.state() instanceof ActionState.RejectedBeforeDispatch rejected)return Optional.of(rejected.dispatch().proof().reason());
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Rejected rejected)
                return Optional.of(rejected.reason());
            return Optional.empty();
        }
        /** Only the actual original pause counter roles change representation on the public wire. */
        static RawJson publicResult(RawJson numeric) {
            return RootPublicPausePublicResult.present(numeric);
        }
        private ExactRef preserveWaitFailure(WaitPhase phase,Instant at,IOException original,ActionPorts.OutcomeArchive archive){
            var trace=new java.io.StringWriter();original.printStackTrace(new java.io.PrintWriter(trace));
            return archive.preserveMaterial(new WaitFailure(phase,at,original.getClass().getName(),
                    Objects.toString(original.getMessage(),original.getClass().getName()),trace.toString(),prepared.runtime).encode());
        }
        @FunctionalInterface private interface PhysicalWork<T>{T read(PhysicalReadLease original)throws IOException;}
        private <T>T withPhysical(Session same,Instant deadline,PhysicalWork<T> work)throws IOException {
            context.requireCurrent(deadline);context.writer().requireSession(same);
            var identity=new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(
                    context.game().machineId(),context.game().generation(),context.game().sessionId());
            return context.collector().withHeldReadScope(same,identity,deadline,
                    frame->context.readiness().currentDerivedCleanup(same,frame.identity(),deadline,work::read));
        }
        private static AdvanceObservationPort.Frame frame(Complete complete) {
            return new AdvanceObservationPort.Frame(complete.identity(),complete.source(),complete.sessionId(),complete.semantic(),
                    new ObservationProvenance.Push(complete.identity().frame().snapshotId(),complete.identity().frame().identity().nativeRevision(),complete.originalEvidence()),
                    complete.observedAt(),complete.originalEvidence());
        }
        private static CompositeExecution execution(ActionState state) {
            if(state instanceof ActionState.CompositeRunning value)return value.execution();
            if(state instanceof ActionState.CompositeUnknown value)return value.execution();
            if(state instanceof ActionState.CompositeSettled value)return value.execution();
            throw new IllegalArgumentException("actual public pause composite execution required");
        }
        private static List<ActionReceipt> preceding(ActionReceipt parent,ActionCommand child,org.xar.ck3.control.continuity.ContinuityState state,ActionPorts.OutcomeArchive archive) {
            var execution=execution(parent.state());var children=execution.children();
            require(!children.isEmpty()&&children.getLast().equals(new CompositeExecution.Child(child.actionId(),ActionCodec.bodySha256(child)))
                    &&child.actionId().equals(ActionIds.child(parent.command().actionId(),children.size(),PUBLIC_STEP)),"pause child changed original reserved ordinal/body");
            var old=children.subList(0,children.size()-1).stream().map(key->ContinuityActionJournal.lookup(state,key.actionId(),archive).orElseThrow()).toList();
            require(old.stream().allMatch(ActionReceipt::settled),"UNKNOWN prior pause forbids another child");return old;
        }
        private static final class Call {
            final RootApplicationSession root;final PublicPlanningCodec.ExecuteRequest caller;final Session same;final ActionCommand parent;
            final Complete before;final org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known;final Snapshot starting;final Instant deadline;
            Complete retryFrame;Decision decision;ExactRef parentProof;
            final LinkedHashMap<ExactRef,GuardEvidence> phaseGuards=new LinkedHashMap<>();
            Optional<ExactRef> waitFailure=Optional.empty();
            Call(RootApplicationSession root,PublicPlanningCodec.ExecuteRequest caller,Session same,ActionCommand parent,Complete before,
                    org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,Snapshot starting,Instant deadline){
                this.root=root;this.caller=caller;this.same=same;this.parent=parent;this.before=before;this.known=known;this.starting=starting;this.deadline=deadline;
            }
        }
    }
    /** Finite local source DATA. Guard fields belong to the existing shared codec; no parsed value grants authority. */
    static record RecordedRecovery(ExactRef decision,List<GuardEvidence> guards,Optional<ExactRef> waitFailure) {
        static final String SCHEMA="xar.java.public-pause-original-phases/v1";
        static final int MAX_BYTES=256*1024;
        RecordedRecovery{Objects.requireNonNull(decision);guards=List.copyOf(guards);waitFailure=Objects.requireNonNull(waitFailure);
            require(decision.bytes()>0&&guards.size()>=1&&guards.size()<=3&&new HashSet<>(guards).size()==guards.size(),
                    "one decision and one to three unique original pause phases required");
            waitFailure.ifPresent(reference->require(reference.bytes()>0,"nonempty original pause wait diagnostic required"));}
        RawJson encode(){
            var row=StrictJson.object().put("schema",SCHEMA);row.set("decision",decision.toJson());var list=row.putArray("phase_guards");
            guards.forEach(guard->list.add(ActionReceiptCodec.encodeGuard(guard)));
            if(waitFailure.isPresent())row.set("wait_failure",waitFailure.orElseThrow().toJson());else row.putNull("wait_failure");
            var bytes=org.xar.ck3.control.application.driver.DriverJson.encodeNode(row);
            require(bytes.length<=MAX_BYTES,"bounded pause phase metadata required");return new RawJson(bytes);
        }
        static RecordedRecovery decode(RawJson raw){
            var row=StrictJson.object(StrictJson.parse(raw.bytes(),MAX_BYTES),Set.of("schema","decision","phase_guards","wait_failure"));
            require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&row.get("phase_guards").isArray(),"exact pause phase envelope required");
            var guards=new ArrayList<GuardEvidence>();row.get("phase_guards").forEach(node->guards.add(ActionReceiptCodec.decodeGuard(node)));
            return new RecordedRecovery(ExactRef.fromJson(row.get("decision")),guards,
                    row.get("wait_failure").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get("wait_failure"))));
        }
    }
    enum WaitPhase { REFRESH,ENDING }
    static record WaitFailure(WaitPhase phase,Instant at,String javaType,String message,String originalTrace,ExactRef runtimeSource){
        static final String SCHEMA="xar.java.public-pause-original-wait-diagnostic/v1";
        static final int MAX_BYTES=65536;
        WaitFailure{Objects.requireNonNull(phase);Objects.requireNonNull(at);StrictJson.text(javaType);StrictJson.text(message);
            StrictJson.text(originalTrace);Objects.requireNonNull(runtimeSource);require(runtimeSource.bytes()>0,"actual diagnostic producer required");}
        RawJson encode(){
            var row=StrictJson.object().put("schema",SCHEMA).put("phase",phase.name()).put("at",at.toString()).put("java_type",javaType)
                    .put("message",message).put("original_trace",originalTrace);row.set("runtime_source",runtimeSource.toJson());
            byte[] bytes=DriverJson.encodeNode(row);require(bytes.length<=MAX_BYTES,"bounded original pause wait diagnostic required");return new RawJson(bytes);
        }
        static WaitFailure decode(RawJson original){
            var row=StrictJson.object(StrictJson.parse(original.bytes(),MAX_BYTES),Set.of("schema","phase","at","java_type","message","original_trace","runtime_source"));
            require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact original pause diagnostic schema required");
            return new WaitFailure(WaitPhase.valueOf(StrictJson.text(row.get("phase"))),Instant.parse(StrictJson.text(row.get("at"))),
                    StrictJson.text(row.get("java_type")),StrictJson.text(row.get("message")),StrictJson.text(row.get("original_trace")),ExactRef.fromJson(row.get("runtime_source")));
        }
    }
}
