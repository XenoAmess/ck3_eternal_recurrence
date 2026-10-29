package org.xar.ck3.control.service.root;

import java.io.IOException;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import java.math.BigInteger;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailure;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.*;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;

/** The original generic Driver catch boundary, issued only within this actual installed Root call. */
public final class RootPublicStepFailureOriginals implements DriverPublicExecuteFailureMaterial.Source,DriverEarlyExecuteFailure.Source {
    private static final ThreadLocal<Call> ACTIVE=new ThreadLocal<>();
    private static final ThreadLocal<Start> DRIVER=new ThreadLocal<>();
    private final RootInstalledCatalog installed;
    private final RootRuntimeContext context;
    private final DriverStateAssembler authority;
    private final ActionJournal journal;
    private final OutcomeArchive archive;
    private final RootReadContractCatalog reads;
    private final List<ExactRef> commonSources,allSources;
    private final ThreadLocal<IdentityHashMap<OriginalInvocation,Capture>> captures=ThreadLocal.withInitial(IdentityHashMap::new);

    private final ThreadLocal<IdentityHashMap<DriverEarlyExecuteFailure.OriginalInvocation,EarlyCapture>> earlyCaptures=ThreadLocal.withInitial(IdentityHashMap::new);

    RootPublicStepFailureOriginals(RootInstalledCatalog installed)throws IOException {
        this.installed=Objects.requireNonNull(installed);context=installed.context();authority=context.adopted().authority();
        journal=context.core().journal();archive=context.archive();reads=installed.bindings().readCatalog();
        var common=new ArrayList<ExactRef>(List.of(installed.publicStepSource(LOCAL_SERVICE,RootPublicStepFailureOriginals.class),
                installed.publicStepSource(LOCAL_SERVICE,RootPublicStepExecution.class),
                installed.publicStepSource(LOCAL_SERVICE,RootApplicationAssembly.class),
                installed.publicStepSource(LOCAL_SERVICE,RootApplicationSession.class),
                installed.publicStepSource(LOCAL_SERVICE,RootNativeSourceAuthority.class),
                installed.publicStepSource(LOCAL_SERVICE,PublicPlanningCodec.class),
                installed.publicStepSource(LOCAL_SERVICE,PublicServiceFailure.class),
                installed.publicStepSource(APPLICATION,DriverPublicExecuteFailureMaterial.class),
                installed.publicStepSource(APPLICATION,DriverEarlyExecuteFailure.class),
                installed.publicStepSource(APPLICATION,DriverEarlyExecuteFailureRowProducer.class),
                installed.publicStepSource(APPLICATION,DriverPublicExecuteFailureRowProducer.class),
                installed.publicStepSource(APPLICATION,DriverSnapshotFacts.class),
                installed.definitions().frontend().originalNativeDriver()));
        ExactRef nativeDriver=installed.definitions().frontend().originalNativeDriver();
        StrictJson.require(nativeDriver.bytes()==1658471&&nativeDriver.sha256().equals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"),
                "the exact original generic Driver recording policy is required");
        // Reuse the already installed material owner's explicit original recording policy closure.
        // No path derivation, parser, action family or replacement material owner is introduced.
        var materials=installed.remainingDomains().actionHistory(context,installed).materials();
        materials.requireOwner(authority,journal,archive);
        var war=materials.sources().stream().filter(ref->ref.bytes()==241556
                &&ref.sha256().equals("b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937")).toList();
        StrictJson.require(war.size()==1,"the actual installed original war recording policy is required");common.add(war.getFirst());
        for(Class<?> type:List.of(org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsService.class,org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsContracts.class,org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsCache.class,org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline.class,org.xar.ck3.control.nativebridge.capabilities.army.ArmyPrivateScalarControl.class))
            common.add(installed.publicStepSource(NATIVE_TRANSPORT,type));
        commonSources=List.copyOf(common);
        var closure=new LinkedHashSet<ExactRef>(commonSources);
        for(var product:installed.publicSteps().products())closure.addAll(product.sources());
        StrictJson.require(closure.size()<=1024,"finite actual public failure source closure required");allSources=List.copyOf(closure);
    }
    @Override public void requireOwner(DriverStateAssembler same,ActionJournal sameJournal,OutcomeArchive sameArchive,RootReadContractCatalog sameReads){
        StrictJson.require(authority==same&&journal==sameJournal&&archive==sameArchive&&reads==sameReads
                &&context.adopted().authority()==same&&context.bindings()==installed.bindings()
                &&context.readHistoryPublisher().catalog()==sameReads,"public failure source lost its actual Root/Driver/journal/archive/catalog owner");
    }
    @Override public ActionJournal journal(){return journal;}
    @Override public List<ExactRef> sources(){return allSources;}
    final class Window implements AutoCloseable {
        private final Call call;
        private Window(Call call){this.call=call;}
        @Override public void close(){StrictJson.require(ACTIVE.get()==call,"public Driver failure call scope changed");ACTIVE.remove();}
    }
    private record Call(RootPublicStepFailureOriginals source,RootApplicationSession root,
            Optional<RootPublicStepExecution.Product> product,PublicPlanningCodec.ExecuteRequest caller,Instant deadline,
            java.util.concurrent.atomic.AtomicReference<ActionBinding> action,java.util.concurrent.atomic.AtomicBoolean readStarted) { }
    private record ActionBinding(ActionCommand command,Start entry) { }
    Window enter(RootApplicationSession root,Optional<RootPublicStepExecution.Product> product,PublicPlanningCodec.ExecuteRequest caller,Instant deadline)throws IOException {
        if(ACTIVE.get()!=null)throw new IOException("a public step cannot replace another active original Driver invocation");
        StrictJson.require(context.actions()==root&&root.writer()==context.writer()&&root.archive()==context.archive(),"failure invocation must use its identical actual Root");
        if(product.isPresent()) {
            var value=product.orElseThrow();
            StrictJson.require(installed.publicSteps().products().stream().anyMatch(item->item==value),"failure product was not installed in this actual catalog");
        }
        var call=new Call(this,root,product,Objects.requireNonNull(caller),Objects.requireNonNull(deadline),new java.util.concurrent.atomic.AtomicReference<>(),new java.util.concurrent.atomic.AtomicBoolean());
        ACTIVE.set(call);return new Window(call);
    }
    /** This source invokes the actual Root itself; no caller supplies an exception or phase flag.
     * The original outer Core borrow remains live until the Root's existing final flush. */
    RawJson executeRead()throws IOException,InterruptedException {
        Call call=ACTIVE.get();
        if(call==null||call.source()!=this||!(call.product().orElse(null) instanceof RootPublicStepExecution.Read read)
                ||!call.readStarted().compareAndSet(false,true))
            throw new IOException("no unused actual installed Root READ invocation exists");
        return context.core().withBorrowed(()->{
            Session same=context.core().activeBorrowedSession();context.writer().requireSession(same);
            read.requireContext(context);
            var producers=new LinkedHashSet<ExactRef>(commonSources);producers.addAll(read.sources());
            StrictJson.require(producers.size()<=DriverEarlyExecuteFailure.MAX_PRODUCER_SOURCES,"early actual producer closure exceeds finite domain");
            var sourcePins=new ArrayList<Pin>();for(ExactRef ref:producers)sourcePins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
            var run=new EarlyRun(call,same,List.copyOf(producers),List.copyOf(sourcePins));
            return call.root().withPublicSuppliedAction(call.deadline(),()->{
                try {
                    return call.root().withPublicPlanning(call.deadline(),(observation,borrowed)->{
                        observation.assertCurrent(borrowed);
                        var original=RootPlanningInputsFactory.publicRequest(observation,borrowed,call.deadline());
                        StrictJson.require(observation.frame().joined() instanceof DriverObservationAssembler.Complete,
                                "actual public READ has no complete original Native/Driver join");
                        var frame=(DriverObservationAssembler.Complete)observation.frame().joined();
                        var known=observation.frame().driver();
                        // Set before all Driver entry validation and owner code.
                        run.callbackEntered=true;
                        StrictJson.require(borrowed==same,"actual public READ changed its outer writer borrow");
                        try(var actualDriver=beginDriver(original,frame,known,borrowed,call.caller())) {
                            if(read.validation()==RootPublicStepExecution.ReadValidation.CENTRAL_BEFORE)call.caller().requireCurrent(original);
                            read.requireContext(context);
                            RawJson result=Objects.requireNonNull(read.work().read(original,frame,known,borrowed,call.caller(),archive.withSession(borrowed)));
                            result.objectFieldNames();for(Pin pin:sourcePins)same.verifyPin(pin);read.requireContext(context);return result;
                        }
                    });
                } catch(IOException|InterruptedException|RuntimeException original) {
                    // The separate original H2743 reader also records its real entry failure
                    // (native_driver.py14485..14503); no Native receipt exists before this callback.
                    if(!run.callbackEntered) {
                        run.originalFailure=original;captureEarly(run,original);
                    }
                    throw original;
                }
            });
        });
    }
    /** The matching action path owns preparation/dispatch/presentation in the same closed call. */
    RawJson executeAction()throws IOException,InterruptedException {
        Call call=ACTIVE.get();
        if(call==null||call.source()!=this||!(call.product().orElse(null) instanceof RootPublicStepExecution.Action action)
                ||!call.readStarted().compareAndSet(false,true))throw new IOException("no unused actual installed Root action invocation exists");
        return context.core().withBorrowed(()->{
            Session same=context.core().activeBorrowedSession();context.writer().requireSession(same);action.requireContext(context);
            var producers=new LinkedHashSet<ExactRef>(commonSources);producers.addAll(action.sources());
            StrictJson.require(producers.size()<=DriverEarlyExecuteFailure.MAX_PRODUCER_SOURCES,"early action source closure exceeds finite domain");
            var pins=new ArrayList<Pin>();for(ExactRef ref:producers)pins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
            var run=new EarlyRun(call,same,List.copyOf(producers),List.copyOf(pins));
            var prepared=new java.util.concurrent.atomic.AtomicReference<ActionCommand>();
            return call.root().withPublicSuppliedAction(call.deadline(),()->{
                try {
                    return call.root().executePublicPlanningAction(call.deadline(),(original,frame,known,borrowed)->{
                        run.callbackEntered=true;StrictJson.require(borrowed==same,"actual action changed its outer writer borrow");
                        try(var actualDriver=beginDriver(original,frame,known,borrowed,call.caller())) {
                            if(action.validation()==RootPublicStepExecution.ActionValidation.CENTRAL_BEFORE)call.caller().requireCurrent(original);
                            action.requireContext(context);
                            var command=Objects.requireNonNull(action.preparation().prepare(original,frame,known,borrowed,call.caller()));
                            StrictJson.require(command.operation().equals(call.caller().step()),"actual step owner changed caller operation");
                            trackPreparedAction(command);for(Pin pin:pins)same.verifyPin(pin);action.requireContext(context);
                            if(!prepared.compareAndSet(null,command))throw new IOException("public action preparation was repeated");return command;
                        }
                    },(actual,bound,borrowed)->{
                        var command=prepared.get();
                        if(borrowed!=same||command==null||!actual.command().equals(command))throw new IOException("action result changed its actual original preparation/writer");
                        for(Pin pin:pins)same.verifyPin(pin);action.requireContext(context);
                        var result=Objects.requireNonNull(action.result().present(actual,bound,borrowed,call.caller()));result.objectFieldNames();
                        for(Pin pin:pins)same.verifyPin(pin);action.requireContext(context);return result;
                    });
                } catch(IOException|InterruptedException|RuntimeException original) {
                    if(!run.callbackEntered&&!call.caller().h2743()){run.originalFailure=original;captureEarly(run,original);}throw original;
                }
            });
        });
    }
    /** The fixed unsupported-hire branch has the same real pre-observation failure boundary. */
    RawJson executeUnsupportedHire()throws IOException,InterruptedException {
        Call call=ACTIVE.get();
        if(call==null||call.source()!=this||call.product().isPresent()
                ||!DriverPublicExecuteFailureRowProducer.fixedUnsupportedHire(call.caller().step().value())
                ||!call.readStarted().compareAndSet(false,true))
            throw new IOException("no unused actual fixed unsupported-hire invocation exists");
        return context.core().withBorrowed(()->{
            Session same=context.core().activeBorrowedSession();context.writer().requireSession(same);
            var pins=new ArrayList<Pin>();
            for(ExactRef ref:commonSources)pins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
            var run=new EarlyRun(call,same,commonSources,List.copyOf(pins));
            return call.root().withPublicSuppliedAction(call.deadline(),()->{
                try {
                    return call.root().withPublicCapabilitiesObservation(call.deadline(),(frame,known,borrowed,capabilities)->{
                        run.callbackEntered=true;
                        StrictJson.require(borrowed==same,"unsupported hire changed its original writer borrow");
                        throw unsupportedHire(frame,known,borrowed,capabilities);
                    });
                } catch(IOException|InterruptedException|RuntimeException original) {
                    if(!run.callbackEntered){run.originalFailure=original;captureEarly(run,original);}throw original;
                }
            });
        });
    }
    /**
     * The comparison facade delegates the real Army query to this same installed issuer.
     * The service owns its actual try boundary and its private, one-use failure token.
     */
    public static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsService.Reply executeArmyComparisonQuery(
            RootApplicationSession root,RootInstalledCatalog installed,
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsService service,
            Optional<BigInteger> expectedRevision,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(root);Objects.requireNonNull(installed);Objects.requireNonNull(service);
        Objects.requireNonNull(expectedRevision);Objects.requireNonNull(deadline);
        var context=installed.context();var strengths=installed.remainingDomains().strengths();
        StrictJson.require(context.actions()==root&&root.writer()==context.writer()&&root.archive()==context.archive(),
                "Army comparison must retain its identical installed Root, writer and archive");
        context.writer().requireSession(context.core().activeBorrowedSession());
        service.requireSame(strengths.current(),context.reads(),context.readCatalog(),strengths.contracts(),
                strengths.cache(),strengths.pipeline(),strengths.scalarControl(),context.readHistoryPublisher());
        var source=installed.publicSteps().failureSource(installed);
        context.readHistoryPublisher().bindPublicExecuteFailureSource(source);
        context.readHistoryPublisher().bindEarlyExecuteFailureSource(source);
        PublicPlanningCodec.Revision revision=expectedRevision.<PublicPlanningCodec.Revision>map(PublicPlanningCodec.RevisionValue::new)
                .orElseGet(PublicPlanningCodec.RevisionMissing::new);
        var caller=new PublicPlanningCodec.ExecuteRequest(new OperationKey("query-army-strengths-v1"),revision,
                new PublicPlanningCodec.FrameMissing());
        try(var originalCall=source.enter(root,Optional.empty(),caller,deadline)) {
            return source.executeArmyComparison(service,expectedRevision);
        }
    }
    private org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsService.Reply executeArmyComparison(
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsService service,
            Optional<BigInteger> expectedRevision)throws IOException,InterruptedException {
        Call call=ACTIVE.get();
        if(call==null||call.source()!=this||call.product().isPresent()
                ||!call.caller().step().value().equals("query-army-strengths-v1")
                ||!call.readStarted().compareAndSet(false,true))
            throw new IOException("no unused actual private Army comparison invocation exists");
        Session same=context.core().activeBorrowedSession();context.writer().requireSession(same);
        var pins=new ArrayList<Pin>();
        for(ExactRef ref:commonSources)pins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
        var run=new EarlyRun(call,same,commonSources,List.copyOf(pins));
        // The supplier already holds Root.withPublicObservation. Its original finally
        // flushes only after the physical/Driver observation has ended; no nested flush.
        try {
            var reply=service.queryAutoCore(expectedRevision);
            for(Pin pin:pins)same.verifyPin(pin);
            return reply;
        } catch(RuntimeException original) {
            // The exact service catch token distinguishes a previously queued row from a
            // storage diagnostic. Neither may be published again through the early lane.
            try {
                var failure=service.takeInvocationFailure(original);
                if(failure.disposition()==org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsService.HistoryDisposition.UNRECORDED) {
                    run.originalFailure=original;captureEarly(run,original);
                }
            } catch(RuntimeException diagnostic) {
                if(diagnostic!=original)original.addSuppressed(diagnostic);
            }
            throw original;
        }
    }
    private static final class EarlyRun {
        private final Call call;private final Session same;private final List<ExactRef> producers;private final List<Pin> sourcePins;
        private boolean callbackEntered;private Throwable originalFailure;
        private EarlyRun(Call call,Session same,List<ExactRef> producers,List<Pin> sourcePins){this.call=call;this.same=same;this.producers=producers;this.sourcePins=sourcePins;}
    }
    private static final class EarlyCapture implements DriverEarlyExecuteFailure.OriginalInvocation {
        private final RootPublicStepFailureOriginals source;private final EarlyRun run;private final Throwable thrown;
        private final DriverEarlyExecuteFailure.Originals originals;private final List<Pin> pins;
        private EarlyCapture(RootPublicStepFailureOriginals source,EarlyRun run,Throwable thrown,DriverEarlyExecuteFailure.Originals originals,List<Pin> pins){
            this.source=source;this.run=run;this.thrown=thrown;this.originals=originals;this.pins=pins;
        }
        @Override public DriverEarlyExecuteFailure.Source issuer(){return source;}
    }
    static DriverEarlyExecuteFailure.Error earlyError(Throwable actual) {
        Objects.requireNonNull(actual);
        if(actual instanceof PublicServiceFailure migrated)return new DriverEarlyExecuteFailure.Error(
                DriverEarlyExecuteFailure.ErrorOrigin.MIGRATED_PUBLIC_FAULT,migrated.kind().pythonClassName(),Optional.of(migrated.getMessage()));
        return new DriverEarlyExecuteFailure.Error(DriverEarlyExecuteFailure.ErrorOrigin.ACTUAL_JAVA_FAILURE,
                actual.getClass().getName(),Optional.ofNullable(actual.getMessage()));
    }
    private void captureEarly(EarlyRun run,Throwable original) {
        try {
            Session same=run.same;context.writer().requireSession(same);requireOwner(authority,journal,archive,reads);
            StrictJson.require(!run.callbackEntered&&run.originalFailure==original&&ACTIVE.get()==run.call
                    &&context.actions()==run.call.root()&&run.call.readStarted().get()&&DRIVER.get()==null,
                    "early failure did not come from this source's actual unentered Root observation call");
            for(Pin pin:run.sourcePins)same.verifyPin(pin);
            Optional<ExactRef> historicalEpoch=context.sources().retainedEpochManifestOriginal(same);
            var bound=archive.withSession(same);var pins=new ArrayList<Pin>(run.sourcePins);
            if(historicalEpoch.isPresent())pins.add(same.capturePin(historicalEpoch.orElseThrow(),16<<20));
            DriverEarlyExecuteFailure.Retained retained=authority.withFrozenFacts(same,frozen->{
                if(!(frozen.state() instanceof Known cached))return new DriverEarlyExecuteFailure.Absent(
                        new DriverEarlyExecuteFailure.Missing(List.of("actual Root retained state is not a complete cached Known")));
                StrictJson.require(cached.stamp().game().equals(context.game().generation()),
                        "retained cached Known belongs to another complete physical Game generation");
                ExactRef driver=bound.preserveMaterial(RawJson.fullMaterial(cached.driver().encode()));
                ExactRef known=bound.preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(cached));
                return new DriverEarlyExecuteFailure.Cached(cached,driver,known,cached.observation().map(DriverObservationFacts::semanticFactsEvidence));
            });
            var head=same.head();ExactRef caller=bound.preserveMaterial(PublicPlanningCodec.encodeExecute(run.call.caller()));
            var error=earlyError(original);
            var data=new DriverEarlyExecuteFailure.InvocationData(run.call.caller().step(),error,Optional.empty(),Optional.empty(),
                    DriverEarlyExecuteFailure.retainedData(retained),caller,historicalEpoch,Optional.empty(),Optional.empty(),
                    head.state().sequence(),head.digest(),run.producers);
            ExactRef invocation=bound.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(DriverEarlyExecuteFailureRowProducer.invocationJson(data))));
            var originals=new DriverEarlyExecuteFailure.Originals(data.originalCommand(),data.error(),data.result(),data.publicNumbers(),retained,
                    invocation,data.caller(),data.epochManifest(),data.unsupportedCapabilities(),data.unresolvedAction(),data.headSequence(),data.headDigest(),data.producerSources());
            var captured=new EarlyCapture(this,run,original,originals,List.copyOf(pins));
            var map=earlyCaptures.get();StrictJson.require(map.size()<128,"finite private early invocation retention exhausted");map.put(captured,captured);
            try {
                requireOriginal(same,authority,bound,captured);
                var outcome=context.readHistoryPublisher().enqueueEarlyExecuteFailure(same,captured);
                if(outcome instanceof DriverEarlyExecuteFailure.StorageDiagnostic failure)
                    original.addSuppressed(new IOException(failure.errorType()+": "+failure.message()));
                else if(outcome instanceof DriverEarlyExecuteFailure.MissingFacts missing)
                    original.addSuppressed(new IOException("NO_FRESH_FRAME retained history unavailable: "+String.join("; ",missing.missing().reasons())));
            } catch(IOException|RuntimeException diagnostic) {map.remove(captured);if(diagnostic!=original)original.addSuppressed(diagnostic);}
        } catch(IOException|RuntimeException diagnostic) {if(diagnostic!=original)original.addSuppressed(diagnostic);}
    }
    @Override public DriverEarlyExecuteFailure.Originals requireOriginal(Session same,DriverStateAssembler sameAuthority,OutcomeArchive bound,
            DriverEarlyExecuteFailure.OriginalInvocation invocation)throws IOException {
        if(!(invocation instanceof EarlyCapture captured)||captured.source!=this||captured.run.same!=same
                ||earlyCaptures.get().get(invocation)!=captured||invocation.issuer()!=this)
            throw new IOException("early exception lacks this Root's identical private actual-call origin");
        context.writer().requireSession(same);requireOwner(sameAuthority,journal,archive,reads);
        var run=captured.run;var original=captured.originals;
        StrictJson.require(!run.callbackEntered&&run.originalFailure==captured.thrown&&context.actions()==run.call.root()
                &&run.call.source()==this&&run.call.readStarted().get()&&original.error().equals(earlyError(captured.thrown))
                &&original.originalCommand().equals(run.call.caller().step())
                &&Arrays.equals(PublicPlanningCodec.encodeExecute(run.call.caller()).bytes(),bound.loadFullMaterial(original.caller()).bytes()),
                "early failure changed its actual Root/call/Throwable/phase");
        StrictJson.require(same.head().state().sequence()==original.headSequence()&&same.head().digest().equals(original.headDigest()),
                "early private invocation escaped its actual catch writer head");
        for(Pin pin:captured.pins)same.verifyPin(pin);
        StrictJson.require(DriverEarlyExecuteFailureRowProducer.decodeInvocation(bound.loadFullMaterial(original.invocation()).bytes())
                .equals(DriverEarlyExecuteFailure.invocationData(original)),"early original invocation bytes changed");
        if(original.retained() instanceof DriverEarlyExecuteFailure.Cached cached)authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==cached.before()&&cached.before().stamp().game().equals(context.game().generation()),
                    "early failure lost its identical retained cached Known/full physical Game generation");
            StrictJson.require(Arrays.equals(cached.before().driver().encode(),bound.loadFullMaterial(cached.beforeDriver()).bytes())
                    &&Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(cached.before()).bytes(),bound.loadFullMaterial(cached.originalKnown()).bytes()),
                    "early cached full Driver/Known originals changed");return null;
        });
        return original;
    }
    @Override public void release(DriverEarlyExecuteFailure.OriginalInvocation invocation)throws IOException {
        if(!(invocation instanceof EarlyCapture captured)||captured.source!=this||earlyCaptures.get().remove(invocation)!=captured)
            throw new IOException("cannot release another Root's private early invocation");
        if(earlyCaptures.get().isEmpty())earlyCaptures.remove();
    }

    private record Start(Call call,Session same,Complete frame,Known known,Optional<ExactRef> epoch,List<ExactRef> producers,List<Pin> pins,
            Optional<OpportunityJson.Obj> unsupportedCapabilities,Optional<PlanningRequest> planning,long entrySequence,String entryDigest) { }
    public static final class DriverScope implements AutoCloseable {
        private final Start start,previous;
        private DriverScope(Start start,Start previous){this.start=start;this.previous=previous;}
        @Override public void close(){StrictJson.require(DRIVER.get()==start,"actual Driver failure scope changed");if(previous==null)DRIVER.remove();else DRIVER.set(previous);}
    }
    /** Qualifies the real entry before a Native wait can exhaust its deadline. This records no row. */
    public static DriverScope beginDriver(PlanningRequest original,Complete frame,Known known,Session same,
            PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        Objects.requireNonNull(original);Call call=ACTIVE.get();
        if(call==null||call.caller()!=caller||call.product().isEmpty())throw new IOException("no actual installed public Driver invocation exists");
        StrictJson.require(original.before().equals(frame.identity())&&original.source().equals(frame.source())&&original.sessionId().equals(frame.sessionId()),
                "Driver entry crossed its original held planning frame");
        return call.source().begin(call,frame,known,same,Optional.empty(),Optional.of(original));
    }
    /** OwnedAction uses its actual Root decision lease; it need not manufacture a PlanningRequest. */
    public static DriverScope beginDriver(Complete frame,Known known,Session same,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        Call call=ACTIVE.get();if(call==null||call.caller()!=caller||call.product().isEmpty())
            throw new IOException("no actual installed public Driver invocation exists");
        return call.source().begin(call,frame,known,same,Optional.empty(),Optional.empty());
    }
    private DriverScope begin(Call call,Complete frame,Known known,Session same,Optional<OpportunityJson.Obj> unsupportedCapabilities,Optional<PlanningRequest> planning)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(call.deadline());
        if(call.product().isPresent())call.product().orElseThrow().requireContext(context);
        var metadata=context.sources().optionalCurrentMetadata(same);requireObserved(same,frame,known);
        var activeSources=new LinkedHashSet<>(commonSources);call.product().ifPresent(value->activeSources.addAll(value.sources()));
        StrictJson.require(activeSources.size()<=DriverPublicExecuteFailureMaterial.MAX_PRODUCER_SOURCES,"active public Driver failure source closure exceeds its finite material lane");
        var pins=new ArrayList<Pin>();for(var source:activeSources)pins.add(same.capturePin(source,WriterContracts.MAX_PIN_BYTES));
        if(metadata.isPresent())pins.add(same.capturePin(metadata.orElseThrow().epochManifest(),16<<20));
        var head=same.head();
        Start start=new Start(call,same,frame,known,metadata.map(RootNativeSourceAuthority.QualifiedMetadata::epochManifest),List.copyOf(activeSources),List.copyOf(pins),unsupportedCapabilities,planning,
                head.state().sequence(),head.digest());
        Start previous=DRIVER.get();DRIVER.set(start);return new DriverScope(start,previous);
    }
    PublicServiceFailure unsupportedHire(Complete frame,Known known,Session same,OpportunityJson.Obj actualCapabilities)throws IOException {
        Call call=ACTIVE.get();
        if(call==null||call.source()!=this||call.product().isPresent()
                ||!DriverPublicExecuteFailureRowProducer.fixedUnsupportedHire(call.caller().step().value()))
            throw new IOException("this actual Root call does not own the fixed original unsupported hire branch");
        try(var ignored=begin(call,frame,known,same,Optional.of(actualCapabilities),Optional.empty())) {
            var original=DriverPublicExecuteFailureRowProducer.unsupportedHireError(call.caller().step().value(),actualCapabilities);
            var failure=new PublicServiceFailure(PublicServiceFailure.Kind.exact(original.pythonClass()),original.message(),Optional.empty());
            return record(DRIVER.get(),failure,Optional.empty(),Optional.empty());
        }
    }
    /** Origin of this exact held READ only. It grants no CP19 replay, projection, mutation or Ready. */
    public static final class ReadInvocation {
        private final RootPublicStepFailureOriginals issuer;private final Start start;private final long sequence;private final String digest;
        private ReadInvocation(RootPublicStepFailureOriginals issuer,Start start,long sequence,String digest){this.issuer=issuer;this.start=start;this.sequence=sequence;this.digest=digest;}
        public PlanningRequest original(){return start.planning().orElseThrow();}
        public RootRuntimeContext context(){return issuer.context;}
        public RootApplicationSession root(){return start.call().root();}
        public Complete frame(){return start.frame();}
        public Known known(){return start.known();}
        public PublicPlanningCodec.ExecuteRequest caller(){return start.call().caller();}
        public Optional<ExactRef> epochManifest(){return start.epoch();}
        public List<ExactRef> producerSources(){return start.producers();}
        public long writerHeadSequence(){return sequence;}
        public String writerHeadDigest(){return digest;}
        public ReadInvocation requireCurrent(Session same)throws IOException{issuer.requireBridge(start,same,sequence,digest);return this;}
    }
    public static ReadInvocation requireReadInvocation(PlanningRequest original,Complete frame,Known known,Session same,
            PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        Call call=ACTIVE.get();Start start=DRIVER.get();
        if(call==null||start==null||start.call()!=call||call.caller()!=caller||start.same()!=same||start.frame()!=frame||start.known()!=known
                ||start.planning().orElse(null)!=original||!(call.product().orElse(null) instanceof RootPublicStepExecution.Read))
            throw new IOException("returned READ has no identical actual Root planning invocation");
        var head=same.head();var token=new ReadInvocation(call.source(),start,head.state().sequence(),head.digest());return token.requireCurrent(same);
    }
    /** Origin of an existing strong command and its actual canonical receipt. No result is certified. */
    public static final class PreparedInvocation {
        private final RootPublicStepFailureOriginals issuer;private final ActionBinding binding;private final ActionReceipt actual;
        private final long sequence;private final String digest;
        private PreparedInvocation(RootPublicStepFailureOriginals issuer,ActionBinding binding,ActionReceipt actual,long sequence,String digest){
            this.issuer=issuer;this.binding=binding;this.actual=actual;this.sequence=sequence;this.digest=digest;
        }
        public RootRuntimeContext context(){return issuer.context;}
        public RootApplicationSession root(){return binding.entry().call().root();}
        public Complete frame(){return binding.entry().frame();}
        public Known known(){return binding.entry().known();}
        public PublicPlanningCodec.ExecuteRequest caller(){return binding.entry().call().caller();}
        public ActionCommand command(){return binding.command();}
        public ActionReceipt receipt(){return actual;}
        public Optional<ExactRef> epochManifest(){return binding.entry().epoch();}
        public List<ExactRef> producerSources(){return binding.entry().producers();}
        public long writerHeadSequence(){return sequence;}
        public String writerHeadDigest(){return digest;}
        public PreparedInvocation requireCurrent(Session same)throws IOException {
            issuer.requireBridge(binding.entry(),same,sequence,digest);
            StrictJson.require(binding.entry().call().action().get()==binding,"prepared invocation changed its actual tracked command");
            var bound=issuer.archive.withSession(same);
            ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,bound);
            StrictJson.require(Arrays.equals(ActionCodec.encodeCommand(binding.command()),ActionCodec.encodeCommand(actual.command())),
                    "prepared invocation receipt differs from its actual strong command");return this;
        }
    }
    public static PreparedInvocation requirePreparedInvocation(ActionReceipt actual,Session same,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        Call call=ACTIVE.get();ActionBinding binding=call==null?null:call.action().get();
        if(call==null||call.caller()!=caller||binding==null||binding.entry().same()!=same)
            throw new IOException("returned action has no identical actual Root prepared invocation");
        var head=same.head();var token=new PreparedInvocation(call.source(),binding,Objects.requireNonNull(actual),head.state().sequence(),head.digest());
        return token.requireCurrent(same);
    }
    private void requireBridge(Start start,Session same,long sequence,String digest)throws IOException {
        context.writer().requireSession(same);requireOwner(authority,journal,archive,reads);
        StrictJson.require(start.same()==same&&start.call().source()==this&&context.actions()==start.call().root()
                &&start.call().product().isPresent()&&installed.publicSteps().products().stream().anyMatch(value->value==start.call().product().orElseThrow()),
                "invocation bridge crossed its actual private Root/product/writer owner");
        var head=same.head();StrictJson.require(head.state().sequence()==sequence&&head.digest().equals(digest),"invocation bridge escaped its original current writer head");
        same.requireHistoricalHead(start.entrySequence(),start.entryDigest());
        for(Pin pin:start.pins())same.verifyPin(pin);
        authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"actual invocation Driver owner is unavailable");var current=(Known)frozen.state();
            StrictJson.require(current.stamp().game().equals(start.known().stamp().game())
                    &&current.stamp().episodeEpoch()==start.known().stamp().episodeEpoch()
                    &&current.stamp().episodeRunId().equals(start.known().stamp().episodeRunId())
                    &&current.stamp().driverVersion()>=start.known().stamp().driverVersion()
                    &&current.driver().session().equals(start.known().driver().session()),"invocation bridge crossed its full Game/episode/Driver subject");return null;
        });
    }

    private static final class Capture implements OriginalInvocation {
        private final RootPublicStepFailureOriginals source;private final Start start;private final Call call;private final Session session;
        private final PublicServiceFailure thrown;private final Optional<RawJson> numeric,exposed;
        private final Complete frame;private final Originals originals;private final List<Pin> pins;
        private Capture(RootPublicStepFailureOriginals source,Start start,Call call,Session session,PublicServiceFailure thrown,
                Optional<RawJson> numeric,Optional<RawJson> exposed,Complete frame,Originals originals,List<Pin> pins){
            this.source=source;this.start=start;this.call=call;this.session=session;this.thrown=thrown;this.numeric=numeric;this.exposed=exposed;
            this.frame=frame;this.originals=originals;this.pins=pins;
        }
        @Override public DriverPublicExecuteFailureMaterial.Source issuer(){return source;}
    }
    /**
     * Called by the installed owner at its actual Driver catch, before Service-only formatting.
     * The original Throwable is returned unchanged. Storage failures become suppressed diagnostics;
     * they cannot change an UNKNOWN into another dispatch or replace the original public exception.
     */
    public static PublicServiceFailure recordDriverFailure(PlanningRequest original,Complete frame,Known known,Session same,
            PublicPlanningCodec.ExecuteRequest caller,PublicServiceFailure actual,
            Optional<RawJson> originalResult,Optional<RawJson> owningPublicResult)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(frame);Objects.requireNonNull(known);
        Call call=ACTIVE.get();if(call==null||caller.h2743())return actual;
        StrictJson.require(original.before().equals(frame.identity())&&original.source().equals(frame.source())
                &&original.sessionId().equals(frame.sessionId()),"failed Driver catch crossed its original held planning frame");
        return recordDriverFailure(frame,known,same,caller,actual,originalResult,owningPublicResult);
    }
    public static PublicServiceFailure recordDriverFailure(Complete frame,Known known,Session same,
            PublicPlanningCodec.ExecuteRequest caller,PublicServiceFailure actual,
            Optional<RawJson> originalResult,Optional<RawJson> owningPublicResult)throws IOException {
        Call call=ACTIVE.get();if(call==null||caller.h2743())return actual;
        Start start=DRIVER.get();
        if(call.caller()!=caller||call.product().isEmpty()||start==null||start.call()!=call||start.same()!=same||start.frame()!=frame||start.known()!=known){
            actual.addSuppressed(new IOException("failure lacks the identical actual Driver entry issued before its wait"));return actual;
        }
        return call.source().record(start,actual,originalResult,owningPublicResult);
    }
    public static boolean inGenericDriverCall(PublicPlanningCodec.ExecuteRequest caller){
        Call call=ACTIVE.get();return call!=null&&call.caller()==caller&&call.product().isPresent()&&!caller.h2743();
    }
    /** Tracks an existing strong command, never constructs, changes or submits one. */
    public static void trackPreparedAction(ActionCommand actual)throws IOException {
        Call call=ACTIVE.get();Start start=DRIVER.get();
        if(call==null||start==null||start.call()!=call||call.product().isEmpty())
            throw new IOException("actual strong preparation has no original generic Driver entry");
        StrictJson.require(actual.origin() instanceof CommandOrigin.Gameplay&&actual.before().equals(start.frame().identity())
                &&actual.source().equals(start.frame().source())&&actual.sessionId().equals(start.frame().sessionId()),
                "failure tracking command crossed its actual entry Native/Driver frame");
        if(!call.action().compareAndSet(null,new ActionBinding(actual,start)))
            throw new IOException("a generic Driver invocation cannot replace its original strong prepared command");
    }
    /** The owner calls this at the original Driver action catch, before Service-only formatting. */
    public static PublicServiceFailure recordActionDriverFailure(ActionReceipt actual,OutcomeArchive bound,Session same,
            PublicPlanningCodec.ExecuteRequest caller,PublicServiceFailure error,
            Optional<RawJson> originalResult,Optional<RawJson> owningPublicResult)throws IOException {
        Call call=ACTIVE.get();if(call==null||caller.h2743())return error;
        ActionBinding binding=call.action().get();
        if(call.caller()!=caller||binding==null||binding.entry().same()!=same
                ||!Arrays.equals(ActionCodec.encodeCommand(binding.command()),ActionCodec.encodeCommand(actual.command()))){
            error.addSuppressed(new IOException("action failure lacks this invocation's actual strong prepared command"));return error;
        }
        try {
        ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,bound);
        var covered=DriverActionHistoryState.findCommittedCoverage(same,actual,bound);
        if(covered.isPresent()) {
            // The sole ACTION publisher has already preserved the original result/error. No second row or CAS.
            var source=DriverActionHistoryCodec.decode(bound.loadFullMaterial(covered.orElseThrow().originalSource()));
            DriverActionHistoryCodec.requireCanonicalMembership(same,actual,source,bound);
            DriverActionHistoryCodec.requireSource(actual,source,bound);
            return error;
        }
        return call.source().record(binding.entry(),error,originalResult,owningPublicResult);
        } catch(IOException|RuntimeException diagnostic) {if(diagnostic!=error)error.addSuppressed(diagnostic);return error;}
    }
    private PublicServiceFailure record(Start start,PublicServiceFailure actual,
            Optional<RawJson> numeric,Optional<RawJson> exposed)throws IOException {
        Call call=start.call();Session same=start.same();Complete frame=start.frame();Known known=start.known();
        Objects.requireNonNull(actual);Objects.requireNonNull(numeric);Objects.requireNonNull(exposed);
        StrictJson.require(numeric.isPresent()==exposed.isPresent(),"a real result requires the same owner's public projection");
        StrictJson.require(!call.caller().h2743(),"the separate H2743 reader does not enter the generic Driver recorder");
        if(actual.kind()==PublicServiceFailure.Kind.STEP_POSTCONDITION_ERROR&&numeric.isEmpty())
            {actual.addSuppressed(new IOException("the actual StepPostconditionError result is missing; no result may be invented"));return actual;}
        if(actual.kind()==PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED
                &&call.caller().step().value().startsWith("assign-army-commander-v1-army-")&&numeric.isEmpty())
            {actual.addSuppressed(new IOException("the original Commander rejection frames are missing"));return actual;}
        try {
            context.writer().requireSession(same);
            StrictJson.require(call.source()==this&&context.actions()==call.root()
                    &&(call.product().isEmpty()||installed.publicSteps().products().stream().anyMatch(value->value==call.product().orElseThrow())),
                    "failed invocation lost its originally qualified Root/product identity");
            var head=same.head();var bound=context.archive().withSession(same);
            for(Pin pin:start.pins())same.verifyPin(pin);
            var basis=NativeEffectEvidence.basis(frame);
            ExactRef beforeDriver=bound.preserveMaterial(RawJson.fullMaterial(known.driver().encode()));
            ExactRef beforeKnown=bound.preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(known));
            ExactRef callerRef=bound.preserveMaterial(PublicPlanningCodec.encodeExecute(call.caller()));
            Optional<ExactRef> unsupported=start.unsupportedCapabilities().map(value->bound.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(value))));
            Optional<ExactRef> unresolved=unresolved(start,same,bound);
            Optional<ExactRef> result=numeric.map(bound::preserveMaterial);
            Optional<PublicNumbers> numbers=numeric.map(value->PublicNumbers.fromResults(value,exposed.orElseThrow()));
            var error=new OriginalError(actual.kind().pythonClassName(),actual.getMessage());
            var body=new InvocationData(call.caller().step(),error,result,numbers,beforeDriver,beforeKnown,basis.nativeFrame(),basis.driverFacts(),
                    callerRef,start.epoch(),unsupported,unresolved,head.state().sequence(),head.digest(),start.producers());
            ExactRef invocation=bound.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(DriverPublicExecuteFailureRowProducer.invocationJson(body))));
            var originals=new Originals(call.caller().step(),error,result,numbers,known,beforeDriver,beforeKnown,basis.nativeFrame(),basis.driverFacts(),
                    invocation,callerRef,start.epoch(),unsupported,unresolved,head.state().sequence(),head.digest(),start.producers());
            var retained=new Capture(this,start,call,same,actual,numeric,exposed,frame,originals,start.pins());
            var map=captures.get();StrictJson.require(map.size()<128,"finite original public Driver failures exhausted");map.put(retained,retained);
            try {
                requireOriginal(same,authority,bound,retained);
                var outcome=context.readHistoryPublisher().enqueuePublicExecuteFailure(same,retained);
                if(outcome instanceof StorageDiagnostic failure){release(retained);actual.addSuppressed(new IOException(failure.errorType()+": "+failure.message()));}
            } catch(IOException|RuntimeException failure) {map.remove(retained);actual.addSuppressed(failure);}
        } catch(IOException|RuntimeException failure) {if(failure!=actual)actual.addSuppressed(failure);}
        return actual;
    }
    private Optional<ExactRef> unresolved(Start start,Session same,OutcomeArchive bound)throws IOException {
        ActionBinding binding=start.call().action().get();if(binding==null)return Optional.empty();
        var actual=journal.locked(same,locked->locked.find(binding.command().actionId()));
        if(actual.isEmpty()||actual.orElseThrow().outcome()!=ActionReceipt.Outcome.UNRESOLVED)return Optional.empty();
        var receipt=actual.orElseThrow();
        StrictJson.require(binding.entry()==start&&Arrays.equals(ActionCodec.encodeCommand(binding.command()),ActionCodec.encodeCommand(receipt.command()))
                &&receipt.command().before().equals(start.frame().identity())&&receipt.command().source().equals(start.frame().source()),
                "unresolved receipt is not this exact original Driver invocation's strong command");
        ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),receipt,bound);
        ExactRef reference=bound.receiptReferenceOf(receipt);
        StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(receipt,bound),ActionReceiptCodec.encodeReceipt(bound.loadReceipt(reference),bound)),
                "unresolved actual receipt archive changed");return Optional.of(reference);
    }
    @Override public Originals requireOriginal(Session same,DriverStateAssembler sameAuthority,OutcomeArchive bound,OriginalInvocation invocation)throws IOException {
        if(!(invocation instanceof Capture captured)||captured.source!=this||captured.session!=same
                ||captures.get().get(invocation)!=captured||invocation.issuer()!=this)
            throw new IOException("failure was not issued by this Root's identical private catch");
        context.writer().requireSession(same);requireOwner(sameAuthority,journal,archive,reads);
        StrictJson.require(context.actions()==captured.call.root()&&captured.call.caller().step().equals(captured.originals.originalCommand())
                &&captured.thrown.kind().pythonClassName().equals(captured.originals.error().pythonClass())
                &&captured.thrown.getMessage().equals(captured.originals.error().message())
                &&Arrays.equals(PublicPlanningCodec.encodeExecute(captured.call.caller()).bytes(),bound.loadFullMaterial(captured.originals.caller()).bytes()),
                "failure lost its exact real Throwable/caller/Root origin");
        var originals=captured.originals;
        var entry=same.requireHistoricalHead(captured.start.entrySequence(),captured.start.entryDigest());
        StrictJson.require(entry.state().sequence()==captured.start.entrySequence()&&entry.digest().equals(captured.start.entryDigest()),
                "failure lost the actual entry writer ancestry; catch head is not an entry Native observation");
        StrictJson.require(same.head().digest().equals(originals.headDigest())&&same.head().state().sequence()==originals.headSequence(),"failed invocation writer head advanced");
        authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"actual failed Driver predecessor is unavailable");var current=(Known)frozen.state();
            StrictJson.require(current.stamp().game().equals(originals.before().stamp().game())
                    &&current.stamp().episodeEpoch()==originals.before().stamp().episodeEpoch()
                    &&current.stamp().episodeRunId().equals(originals.before().stamp().episodeRunId())
                    &&current.driver().session().equals(originals.before().driver().session()),
                    "failure crossed its actual Driver episode/session; the original entry is not an after-frame");return null;
        });
        for(Pin pin:captured.pins)same.verifyPin(pin);
        StrictJson.require(captured.numeric.isPresent()==originals.result().isPresent(),"original result presence changed");
        if(captured.numeric.isPresent()) {
            StrictJson.require(captured.numeric.orElseThrow().equals(bound.loadFullMaterial(originals.result().orElseThrow()))
                    &&PublicNumbers.fromResults(captured.numeric.orElseThrow(),captured.exposed.orElseThrow()).equals(originals.publicNumbers().orElseThrow()),
                    "original failure result/public number roles changed");
        }
        return originals;
    }
    @Override public void release(OriginalInvocation invocation)throws IOException {
        if(!(invocation instanceof Capture captured)||captured.source!=this||captures.get().remove(invocation)!=captured)
            throw new IOException("cannot release another Root's private original Driver failure");
        if(captures.get().isEmpty())captures.remove();
    }
    private void requireObserved(Session same,Complete frame,Known known)throws IOException {
        StrictJson.require(frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId())
                &&frame.identity().game().equals(context.game().generation()),"failed frame crossed this physical Game/source");
        var bound=context.archive().withSession(same);var basis=NativeEffectEvidence.basis(frame);
        var manifest=bound.loadFullMaterial(basis.driverFacts());
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(basis.driverFacts(),manifest,bound.loadNativeFrame(basis.nativeFrame()));
        var facts=DriverObservationEvidenceReader.decode(basis.driverFacts(),manifest,
                bound.loadFullMaterial(DriverObservationEvidenceReader.currentDriverReference(basis.driverFacts(),manifest)),nativeFrame);
        var projected=new DriverObservationAssembler().assemble(nativeFrame,facts,basis.nativeFrame());
        StrictJson.require(projected instanceof Complete&&projected.equals(frame)
                &&known.stamp().driverVersion()==facts.driverVersion()&&known.stamp().episodeEpoch()==facts.episodeEpoch()
                &&known.stamp().game().equals(nativeFrame.session().game())
                &&Arrays.equals(known.driver().encode(),facts.driver().encode()),"failure frame/Known did not come from the actual sole Native/Driver projection");
        var current=context.transport().latestObservedSnapshot().orElseThrow(()->new IOException("actual Managed Native observation is absent"));
        StrictJson.require(current.session().equals(nativeFrame.session())&&Arrays.equals(current.originalPacket(),nativeFrame.originalPacket()),
                "failed invocation is not the Managed transport's actual held frame");
        authority.withFrozenFacts(same,frozen->{StrictJson.require(frozen.state() instanceof Known
                &&Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal((Known)frozen.state()).bytes(),DriverSnapshotFacts.encodeKnownOriginal(known).bytes()),
                "actual current Known differs from the failed Driver invocation");return null;});
    }
}

