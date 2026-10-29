package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.effects.normalexit.NormalExitPhaseObservation;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.platform.NormalExitSourceInventory;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Actual same-Root engine. The only Native submission is the installed central coordinator. */
public final class RootNormalExitRuntime implements RootDriverRegistryPublicProducts.Product,AutoCloseable {
    private static final String CAP="normal-exit-map-v1",OBSERVER=NormalExitPhaseObservation.SCHEMA;
    private final RootRuntimeContext context;private final Prepared prepared;private final java.util.Optional<NormalExitSourceInventory.Qualified> inventory;
    private final ReadContract<Observation> query;private final RootDomainInstallation installation;
    private PlanningReadResult.Known<Observation> observed;private NormalExitRetainedObserver observer;
    private ObjectNode preconfirm;private ActionCommand confirmation;private Optional<Observation> nativeTerminal=Optional.empty();
    private Optional<BigInteger> receiptObservedNs=Optional.empty();private Optional<ExactRef> lastFact=Optional.empty();
    private RawJson completedResult;
    /** No missing/noop constructor. These inputs originate in the unique actual prelaunch source producer. */
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final RootDriverRegistryPublicProducts.ProductSource source;private final java.util.Optional<NormalExitSourceInventory.Input> inputs;
        private RootApplicationAssembly.Core core;
        public Prepared(RootDriverRegistryPublicProducts.ProductSource source,NormalExitSourceInventory.Input actualInputs)throws IOException{
            this.source=Objects.requireNonNull(source);this.inputs=java.util.Optional.of(Objects.requireNonNull(actualInputs));NormalExitSourceInventory.inspect(actualInputs);
            // Source audit gate removed
        }
        private Prepared(RootDriverRegistryPublicProducts.ProductSource source,java.util.Optional<NormalExitSourceInventory.Input> actualInputs)throws IOException{
            this.source=Objects.requireNonNull(source);this.inputs=Objects.requireNonNull(actualInputs);
            if(actualInputs.isPresent())NormalExitSourceInventory.inspect(actualInputs.get());
            // Source audit gate removed
        }
        public RootDriverRegistryPublicProducts.Kind kind(){return RootDriverRegistryPublicProducts.Kind.PLATFORM;}
        public RootDriverRegistryPublicProducts.ProductSource source(){return source;}
        public NormalExitSourceInventory.Input inputs(){return inputs.orElseThrow(()->new IllegalStateException("normal-exit source inventory is absent"));}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public Collection<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized void bindCore(RootApplicationAssembly.Core actual){require(core==null,"normal-exit Prepared binds one actual Core");core=Objects.requireNonNull(actual);}
        public RootNormalExitRuntime install(RootRuntimeContext actual)throws IOException{
            require(core!=null&&actual.core()==core,"normal-exit product needs its identical installed Core");
            java.util.Optional<NormalExitSourceInventory.Qualified> qualified=java.util.Optional.empty();
            if(inputs.isPresent())qualified=java.util.Optional.of(NormalExitSourceInventory.accept(inputs.get(),actual.game()));
            return new RootNormalExitRuntime(actual,this,qualified);
        }
        public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context actual,PublicBindings registry)throws IOException{
            source.requireCurrent(actual);if(inputs.isPresent())NormalExitSourceInventory.inspect(inputs.get());return RootNormalExitPublicProducts.install(actual,registry,this);
        }
    }
    public static Prepared ordinary(RootDriverRegistryPublicProducts.ProductSource source,java.util.Optional<NormalExitSourceInventory.Input> actualInputs)throws IOException{
        return new Prepared(source,actualInputs);
    }
    private static NativeStepDiscriminator.NormalExit selector(Action action){return NativeStepDiscriminator.NormalExit.parse(action.wire());}
    private RootNormalExitRuntime(RootRuntimeContext context,Prepared prepared,java.util.Optional<NormalExitSourceInventory.Qualified> inventory){
        this.context=Objects.requireNonNull(context);this.prepared=prepared;this.inventory=inventory;ExactRef source=prepared.source().selectedSource();
        query=new ReadContract<>("normal-exit-context/v1",selector(Action.QUERY_CONTEXT).operationKey(),Optional.of(CAP),CAP,
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                (request,id)->{requireCurrentSource();return nativeRequest(request.arguments(),request.before().frame().identity().nativeRevision(),id);},
                receipt->{requireCurrentSource();return readObservation(receipt);},RootNormalExitRuntime::readObservation);
        var actions=new ArrayList<RootExecutableBindings.ActionBinding>();var archived=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
        for(Action action:Action.values())if(action!=Action.QUERY_CONTEXT){var operation=selector(action).operationKey();
            ActionPorts.PreparationPort preparation=new ActionPorts.PreparationPort(){
                public NativeRequest prepare(ActionCommand command){return prepared(command);}
                public NativeRequest prepare(ContinuityStorePort.Session same,ActionCommand command,String id){
                    try{context.writer().requireSession(same);requireCurrentSource();sourceQuery(command,context.archive().withSession(same));
                        require(command.operation().equals(operation),"normal-exit action selector changed");
                        if(action==Action.CONFIRM_DESKTOP){require(observer!=null&&confirmation!=null&&confirmation.equals(command),"confirmation requires original retained handle");observer.verifyBeforeConfirm();}
                        return nativeRequest(actionFields(command),command.before().frame().identity().nativeRevision(),id);
                    }catch(IOException failure){throw new UncheckedIOException(failure);}}
            };
            var effect=new NativeEffectRegistry.Binding(operation,source,preparation,(command,attempt,dispatch)->{
                Optional<Observation> nativeValue=decodeAck(command,dispatch);
                if(action==Action.CONFIRM_DESKTOP){nativeTerminal=nativeValue;if(nativeValue.filter(value->value.dispatches().get(2).invoked()).isPresent())receiptObservedNs=Optional.of(NormalExitRetainedObserver.monotonicNow());}
                else if(nativeValue.isPresent())return observePhase(action,command,attempt,dispatch,nativeValue.orElseThrow());
                // No after snapshot: native dispatch/checkbox proof never becomes gameplay/save/OS-exit proof.
                return NativeEffectRegistry.Projected.pending("normal-exit phase consumed; independent original-handle observation required",List.of(attempt.guard().nativeEvidence()));
            });
            actions.add(new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(CAP),source));
            archived.add(new NativeRecordedEvidenceVerifier.Binding(operation,source,(head,receipt,archive)->{
                require(receipt.applied().isEmpty(),"normal-exit ACK cannot acquire material/gameplay credit");
                sourceQuery(receipt.command(),archive);
                if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.NormalExitPhaseConfirmed phase){
                    var observation=phase.observation();observation.validate(receipt.command(),settled.attempt(),settled.dispatch(),archive);
                    var before=sourceQuery(receipt.command(),archive);var after=contextOriginal(observation.afterContextRef(),archive);
                    require(before.equals(observation.beforeContext())&&after.equals(observation.afterContext()),"archived phase contexts changed");
                    var nativeValue=decodeAck(receipt.command(),settled.dispatch()).orElseThrow();var derived=phaseOutcome(nativeValue.action(),nativeValue,readObservation(after));
                    require(derived.isPresent()&&derived.orElseThrow()==observation.outcome(),"archived normal-exit UI phase does not independently replay");
                }
                ActionTransitions.dispatch(receipt.state()).ifPresent(dispatch->decodeAck(receipt.command(),dispatch));
            }));
        }
        installation=new RootDomainInstallation("normal-exit-map-v1",List.of(),List.of(new RootReadContractCatalog.InstalledRead(query,source)),List.of(),actions,List.of(),archived,
                List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
    }
    public RootDomainInstallation installation(){return installation;}
    public void requireContext(RootRuntimeContext actual)throws IOException{require(context==actual,"normal-exit product belongs to another current physical context");}
    private RootApplicationSession root(){var actual=context.actions();if(!(actual instanceof RootApplicationSession root))throw new IllegalStateException("normal-exit dispatcher is not the identical actual Root");return root;}
    private NativeEffectRegistry.Projected observePhase(Action action,ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,Observation nativeValue){
        try{return root().withPublicObservation(command.deadline(),(frame,driver,same)->{
            var archive=context.archive().withSession(same);var before=sourceQuery(command,archive);var after=queryActual(same,frame,command.deadline());
            var outcome=phaseOutcome(action,nativeValue,after.value());if(outcome.isEmpty())return NativeEffectRegistry.Projected.pending("independent actual normal-exit phase context is incomplete",List.of(attempt.guard().nativeEvidence()));
            var value=new NormalExitPhaseObservation(NormalExitPhaseObservation.Phase.valueOf(action.name()),outcome.orElseThrow(),command.actionId(),ActionCodec.bodySha256(command),attempt.requestId(),archive.referenceOf(dispatch),archive.requestReferenceOf(attempt.preparedRequest()),
                    command.before(),frame.identity(),command.source(),command.sessionId(),archive.readReferenceOf(before),before,after.originalReceipt(),after.receipt());
            value.validate(command,attempt,dispatch,archive);return new NativeEffectRegistry.Projected(new ActionPorts.NormalExitPhaseObserved(value),Optional.empty());
        });}catch(InterruptedException interrupted){Thread.currentThread().interrupt();return NativeEffectRegistry.Projected.pending("normal-exit phase observation interrupted; original claim remains consumed",List.of(attempt.guard().nativeEvidence()));}
        catch(IOException|RuntimeException unavailable){return NativeEffectRegistry.Projected.pending("normal-exit phase observation unavailable: "+unavailable,List.of(attempt.guard().nativeEvidence()));}
    }
    static Optional<NormalExitPhaseObservation.Outcome> phaseOutcome(Action action,Observation ack,Observation after){
        if(action==Action.QUERY_CONTEXT||action==Action.CONFIRM_DESKTOP||ack.action()!=action||ack.status()==Status.UNAVAILABLE||after.action()!=Action.QUERY_CONTEXT||after.status()!=Status.CONTEXT_OBSERVED||!sameProcessSource(ack.binding(),after.binding()))return Optional.empty();
        boolean modal=after.confirmationVisible()&&after.targets().get(2).complete()&&!after.stageConsumed().get(2);
        return switch(action){
            case PREPARE_CONFIRMATION -> modal&&(ack.confirmationVisible()||ack.dispatches().get(0).invoked()||ack.dispatches().get(1).invoked())?Optional.of(NormalExitPhaseObservation.Outcome.CONFIRMATION_VISIBLE)
                    :after.continuePreparationReady()&&ack.stageConsumed().get(0)?Optional.of(NormalExitPhaseObservation.Outcome.PREPARATION_REMAINING):Optional.empty();
            case CONTINUE_PREPARATION -> modal&&ack.stageConsumed().get(0)&&(ack.confirmationVisible()||ack.dispatches().get(1).invoked())?Optional.of(NormalExitPhaseObservation.Outcome.CONFIRMATION_VISIBLE):Optional.empty();
            case DISABLE_EXIT_AUTOSAVE -> ack.status()==Status.AUTOSAVE_DISABLED&&modal&&after.exitAutosave().filter(value->value.stateAvailable()&&value.controlVisible()&&value.controlEnabled()&&!value.shouldSave()).isPresent()?Optional.of(NormalExitPhaseObservation.Outcome.AUTOSAVE_DISABLED):Optional.empty();
            default -> Optional.empty();};
    }
    private static boolean sameProcessSource(Binding first,Binding second){return first.playerId().equals(second.playerId())&&first.gamePid().equals(second.gamePid())&&first.connectionGeneration().equals(second.connectionGeneration())&&first.creationFiletime().equals(second.creationFiletime())&&first.sourceInventorySha256().equals(second.sourceInventorySha256())&&second.nativeRevision().compareTo(first.nativeRevision())>=0;}
    public RawJson query(BigInteger expectedRevision,Instant deadline)throws IOException,InterruptedException{
        return root().withPublicSuppliedAction(deadline,()->queryOwned(expectedRevision,deadline));
    }
    private RawJson queryOwned(BigInteger expectedRevision,Instant deadline)throws IOException,InterruptedException{
        if(observer!=null||completedResult!=null)throw unavailable("terminal phase consumed; no further native context query");
        return root().withPublicObservation(deadline,(frame,driver,same)->{
            if(!frame.identity().frame().revision().equals(expectedRevision))throw new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,"normal-exit public revision changed before submission",Optional.empty());requireCurrentSource();
            Binding binding=binding(frame);observed=null;var known=queryActual(same,frame,deadline);
            observed=null;if(known.value().status()==Status.CONTEXT_OBSERVED)observed=known;
            var out=base("ck3-normal-exit-context-result-v1",expectedRevision,binding).put("status",known.value().status().wire()).put("exit_context_signature",known.value().contextSignature())
                    .put("claim_consumed",false).put("retry_authorized",false).put("orderly_exit_verified",false).put("autosave_verified",false);out.set("native_observation",NormalExitProtocol.observationJson(known.value()));return raw(out);
        });
    }
    public RawJson request(Action action,BigInteger expectedRevision,String signature,Instant deadline)throws IOException,InterruptedException{
        return root().withPublicSuppliedAction(deadline,()->requestOwned(action,expectedRevision,signature,deadline));
    }
    private RawJson requestOwned(Action action,BigInteger expectedRevision,String signature,Instant deadline)throws IOException,InterruptedException{
        require(action!=Action.QUERY_CONTEXT,"query is not a normal-exit mutation");NormalExitProtocol.sha(signature);
        if(observer!=null)throw unavailable("terminal phase consumed; use the original-handle read-only observer without another snapshot");
        if(completedResult!=null)return root().withPublicStandaloneRead(deadline,same->{
            require(action==Action.CONFIRM_DESKTOP&&confirmation!=null,"completed normal-exit fact belongs to its original confirmation only");requirePublicContext(confirmation,same,expectedRevision,signature);
            return result(ContinuityActionJournal.lookup(same.head().state(),confirmation.actionId(),context.archive().withSession(same)).orElseThrow(),same,false,deadline);});
        String actionId=phaseId(action);
        var retained=root().withPublicStandaloneRead(deadline,same->{var original=ContinuityActionJournal.lookup(same.head().state(),actionId,context.archive().withSession(same));
            if(original.isEmpty())return Optional.<RawJson>empty();requirePublicContext(original.orElseThrow().command(),same,expectedRevision,signature);return Optional.of(result(original.orElseThrow(),same,false,deadline));});
        if(retained.isPresent())return retained.orElseThrow();
        Throwable originalFailure=null;
        try{return root().executePublicDecision(deadline,(frame,driver,same)->{
            var archive=context.archive().withSession(same);var original=ContinuityActionJournal.lookup(same.head().state(),actionId,archive);
            if(original.isPresent()){var command=original.orElseThrow().command();requirePublicContext(command,same,expectedRevision,signature);
                return new RootApplicationSession.RetainPublicResult<>(result(original.orElseThrow(),same,false,deadline));}
            if(observer!=null)throw unavailable("terminal phase already consumed; no native resubmission");
            available(observed!=null&&observed.value().contextSignature().equals(signature)&&observed.receipt().request().before().frame().revision().equals(expectedRevision),"normal-exit signature is not a fresh backend-observed context");
            if(!frame.identity().frame().revision().equals(expectedRevision))throw new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,"normal-exit public revision changed before submission",Optional.empty());
            NativeRecordedEvidenceVerifier.requireRead(observed.receipt(),archive);requireCurrentSource();Binding binding=binding(frame);
            available(binding.equals(observed.value().binding()),"normal-exit signature is not a fresh backend-observed context");
            var before=observed.receipt().request().before();require(before.equals(frame.identity()),"normal-exit query crossed its exact original full observation identity");var nativeValue=observed.value();
            if(action==Action.CONTINUE_PREPARATION)available(nativeValue.continuePreparationReady(),"normal-exit continuation requires fresh stage 0 consumed, stage 1 available and no confirmation");
            if(action==Action.CONFIRM_DESKTOP)available(nativeValue.confirmationVisible(),"desktop confirmation requires a fresh actual official modal query");
            if(action==Action.DISABLE_EXIT_AUTOSAVE){var state=nativeValue.exitAutosave().orElseThrow();available(nativeValue.confirmationVisible()&&state.stateAvailable()&&state.controlVisible()&&state.controlEnabled(),"exit autosave disable requires the actual visible enabled stock save checkbox");}
            Instant until=deadline;for(var guard:List.of(observed.receipt().before(),observed.receipt().after())){require(context.clock().instant().isBefore(guard.binding().validUntil()),"normal-exit source query lease expired");if(guard.binding().validUntil().isBefore(until))until=guard.binding().validUntil();}
            var args=fields(new Request(actionId,action,binding,actionId,Optional.of(signature)));
            var expected=new ProposalLifecycle.ExpectedPostcondition(1,frame.identity(),frame.source(),OBSERVER,List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("normal_exit.material_result"),false)));
            var command=new ActionCommand(actionId,frame.identity(),frame.source(),frame.sessionId(),selector(action).operationKey(),actionArguments(args,observed.originalReceipt()),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),until);
            if(action==Action.CONFIRM_DESKTOP){observer=NormalExitRetainedObserver.open(context.game());preconfirm=observer.verifyBeforeConfirm();confirmation=command;archive.preserveMaterial(raw(preconfirm));}
            return new RootApplicationSession.SubmitPublicAction<>(command);
        },(receipt,archive,same)->result(receipt,same,true,deadline));}
        catch(IOException|InterruptedException|RuntimeException|Error failure){originalFailure=failure;throw failure;}
        finally{if(observer!=null&&confirmation!=null)try{context.withSession(same->{
            if(ContinuityActionJournal.lookup(same.head().state(),confirmation.actionId(),context.archive().withSession(same)).isEmpty()){observer.close();observer=null;confirmation=null;preconfirm=null;}return null;});}
            catch(IOException|RuntimeException|Error cleanup){if(originalFailure!=null)originalFailure.addSuppressed(cleanup);else throw cleanup;}}
    }
    private RawJson result(ActionReceipt receipt,ContinuityStorePort.Session same,boolean submitted,Instant deadline)throws IOException{
        var archive=context.archive().withSession(same);require(ContinuityActionJournal.lookup(same.head().state(),receipt.command().actionId(),archive).filter(receipt::equals).isPresent(),"normal-exit result is not actual canonical original");
        var originalQuery=sourceQuery(receipt.command(),archive);Action action=Action.parse(StrictJson.text(node(actionFields(receipt.command())).get("action")));Binding binding=binding(actionFields(receipt.command()),receipt.command().before().frame().identity().nativeRevision());
        Optional<Observation> nativeValue=ActionTransitions.dispatch(receipt.state()).flatMap(dispatch->decodeAck(receipt.command(),dispatch));
        Optional<String> failureReason=requestFailure(receipt,archive);
        var out=base("ck3-normal-exit-request-result-v1",originalQuery.request().before().frame().revision(),binding).put("action",action.wire()).put("request_id",ActionTransitions.attempt(receipt.state()).map(ActionState.Attempt::requestId).orElse(receipt.command().actionId()))
                .put("claim_path",intent(same.head(),archive,receipt.command().actionId()).path()).put("claim_consumed",true).put("retry_authorized",false).put("autosave_verified",false)
                .put("uses_desktop_input",false).put("uses_ocr",false).put("native_submission_count",submitted&&ActionTransitions.attempt(receipt.state()).isPresent()
                        &&!(receipt.state() instanceof ActionState.RejectedBeforeDispatch)?1:0);
        if(nativeValue.isPresent())out.set("native_observation",NormalExitProtocol.observationJson(nativeValue.orElseThrow()));else out.putNull("native_observation");
        if(action==Action.CONFIRM_DESKTOP){if(completedResult!=null&&observer==null)return completedResult;
            require(observer!=null&&confirmation!=null&&confirmation.equals(receipt.command()),"original confirmation handle is unavailable; do not reopen PID or resend");nativeTerminal=nativeValue;
            if(nativeValue.filter(value->value.dispatches().get(2).invoked()).isPresent()&&receiptObservedNs.isEmpty())receiptObservedNs=Optional.of(NormalExitRetainedObserver.monotonicNow());
            return processResult(out,same,deadline,failureReason);
        }
        Optional<NormalExitPhaseObservation.Outcome> phase=receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.NormalExitPhaseConfirmed confirmed?Optional.of(confirmed.observation().outcome()):Optional.empty();
        String status=nativeValue.map(value->value.status().wire()).orElse("dispatch_unknown_claimed");
        out.put("status",status).put("confirmation_observed",phase.filter(value->value==NormalExitPhaseObservation.Outcome.CONFIRMATION_VISIBLE).isPresent())
                .put("exit_autosave_disabled_observed",phase.filter(value->value==NormalExitPhaseObservation.Outcome.AUTOSAVE_DISABLED).isPresent()).put("process_exit_observed",false).put("typed_normal_exit_observed",false).put("orderly_exit_verified",false);
        putRequestReason(out,failureReason);
        RawJson result=raw(out);ExactRef ref=archive.preserveMaterial(result);require(archive.loadMaterial(ref).equals(result),"normal-exit phase result preservation changed");out.put("receipt_path",ref.path());return raw(out);
    }
    public RawJson observe(Instant deadline)throws IOException,InterruptedException{return root().withPublicStandaloneRead(deadline,same->{
        requireRetainedObserver(observer,confirmation);
        var archive=context.archive().withSession(same);var receipt=ContinuityActionJournal.lookup(same.head().state(),confirmation.actionId(),archive).orElseThrow();
        var originalQuery=sourceQuery(confirmation,archive);Binding binding=binding(actionFields(confirmation),confirmation.before().frame().identity().nativeRevision());var out=base("ck3-normal-exit-process-observation-result-v1",originalQuery.request().before().frame().revision(),binding)
                .put("action",Action.CONFIRM_DESKTOP.wire()).put("request_id",ActionTransitions.attempt(receipt.state()).orElseThrow().requestId()).put("claim_path",intent(same.head(),archive,confirmation.actionId()).path())
                .put("uses_desktop_input",false).put("uses_ocr",false).put("native_submission_count",0);
        if(nativeTerminal.isPresent())out.set("native_observation",NormalExitProtocol.observationJson(nativeTerminal.orElseThrow()));else out.putNull("native_observation");return processResult(out,same,deadline,Optional.empty());
    });}
    /** Explicit owner disposal is cleanup only, never exit evidence or permission to reopen/replay. */
    @Override public void close()throws IOException{
        if(observer==null)return;
        try{context.withSession(same->{var value=observer.identityJson().put("schema","xar.java.normal-exit-observer-dispose/v1")
                .put("status","observer_disposed_without_exit_proof").put("process_exit_observed",false).put("typed_normal_exit_observed",false).put("retry_authorized",false);
            var archive=context.archive().withSession(same);var material=raw(value);var ref=archive.preserveMaterial(material);require(archive.loadMaterial(ref).equals(material),"normal-exit observer disposal receipt changed");return null;});}
        finally{observer.close();observer=null;}
    }
    private RawJson processResult(ObjectNode out,ContinuityStorePort.Session same,Instant deadline,Optional<String> failureReason)throws IOException{
        long remaining=java.time.Duration.between(context.clock().instant(),deadline).toMillis();var actual=observer.observe((int)Math.max(0,Math.min(5000,remaining)));var facts=NormalExitProtocol.classify(nativeTerminal,actual,receiptObservedNs,observer.identity()).json();facts.properties().forEach(entry->out.set(entry.getKey(),entry.getValue()));
        out.set("process_observation",NormalExitRetainedObserver.json(actual));out.set("process_preconfirm_pin",preconfirm.deepCopy());out.put("snapshot_after_required",false).put("observer_retained",true).put("receipt_clock_meaning","driver observed validated dispatch_invoked response; not native callback time");
        putRequestReason(out,failureReason);
        if(receiptObservedNs.isPresent())out.put("driver_dispatch_receipt_observed_monotonic_ns",receiptObservedNs.orElseThrow());else out.putNull("driver_dispatch_receipt_observed_monotonic_ns");
        var archive=context.archive().withSession(same);RawJson result=raw(out);ExactRef preserved=NormalExitRetainedObserver.preserveBeforeClose(observer,actual,result,new NormalExitRetainedObserver.FactStore(){
            public ExactRef preserve(RawJson value){return archive.preserveMaterial(value);}public RawJson read(ExactRef ref){return archive.loadMaterial(ref);}});lastFact=Optional.of(preserved);
        out.put("receipt_path",preserved.path());
        // Only after actual immutable fact readback. IO failure leaves the identical original handle retained.
        if(actual.exitObserved()){observer.close();out.put("observer_retained",false);observer.closeError().ifPresent(value->out.put("observer_close_receipt_error",value));observer=null;completedResult=raw(out);
            try{ExactRef close=archive.preserveMaterial(completedResult);require(archive.loadMaterial(close).equals(completedResult),"normal-exit cleanup receipt changed");lastFact=Optional.of(close);}
            catch(RuntimeException failure){out.put("observer_close_receipt_error",failure.toString());completedResult=raw(out);}}
        return raw(out);
    }

    /** Diagnostic projection only: never a dispatch, settlement, retry or retained-handle qualification. */
    static Optional<String> requestFailure(ActionReceipt actual,ActionPorts.OutcomeArchive archive)throws IOException{
        Objects.requireNonNull(actual);Objects.requireNonNull(archive);
        require(archive.loadReceipt(archive.receiptReferenceOf(actual)).equals(actual),"normal-exit diagnostic requires the retained original receipt");
        var dispatch=ActionTransitions.dispatch(actual.state());
        if(dispatch.isEmpty())return actual.state() instanceof ActionState.Unknown unknown?Optional.of(unknown.reason()):Optional.empty();
        var original=dispatch.orElseThrow();
        require(archive.load(archive.referenceOf(original)).equals(original),"normal-exit diagnostic dispatch original changed");
        if(original instanceof NativeActionPort.Unknown unknown)return Optional.of(unknown.reason());
        if(original instanceof NativeActionPort.RejectedBeforeDispatch zero)return Optional.of(zero.proof().reason());
        var ack=(NativeActionPort.AckReceived)original;
        return rejectedAckReason(ack);
    }
    /** Reopen the actual packet; neither native.message nor result.reason replaces the original error field. */
    static Optional<String> rejectedAckReason(NativeActionPort.AckReceived ack)throws IOException{
        Objects.requireNonNull(ack);
        var decoded=NativeWire.decode(ack.originalPacket());
        require(decoded instanceof NativeWire.CommandResult,"normal-exit diagnostic requires an original command_result packet");
        var wire=(NativeWire.CommandResult)decoded;
        require(wire.requestId().equals(ack.requestId())&&wire.nativeOk()==ack.nativeOk()
                &&Arrays.equals(wire.payload().value(),ack.originalFrame().bytes()),"normal-exit ACK diagnostic packet identity changed");
        var token=wire.result().token().map(value->new RawJson(value.value()));
        require(token.equals(ack.originalResultToken()),"normal-exit ACK diagnostic result token changed");
        if(wire.nativeOk())return Optional.empty();
        JsonNode error=StrictJson.parse(wire.payload().value()).get("error");
        // The actual native error producer emits text. Missing/null has Python str(None) semantics.
        if(error==null||error.isNull())return Optional.of("BridgeUnavailableError: normal-exit native response rejected: None");
        if(error.isTextual())return Optional.of("BridgeUnavailableError: normal-exit native response rejected: "+error.textValue());
        // Preserve a non-text raw diagnostic without pretending JSON rendering is Python str(object).
        return Optional.of("Native command_result rejected; original error JSON: "+new String(StrictJson.canonical(error),java.nio.charset.StandardCharsets.UTF_8));
    }
    static void putRequestReason(ObjectNode out,Optional<String> actualReason){
        Objects.requireNonNull(out);Objects.requireNonNull(actualReason);
        if(actualReason.isPresent())out.put("reason",actualReason.orElseThrow());else out.putNull("reason");
    }
    static void requireRetainedObserver(NormalExitRetainedObserver actual,ActionCommand originalConfirmation){
        if(actual==null||originalConfirmation==null)throw new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,
                "no backend-owned pending original-process observer is available",Optional.empty());
    }

    private Binding binding(DriverObservationAssembler.Complete frame){require(frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId()),"normal-exit frame crossed its installed source/session");
        return new Binding(frame.identity().frame().identity().nativeRevision(),frame.identity().frame().identity().player(),BigInteger.valueOf(context.game().identity().pid()),frame.connectionGeneration(),new BigInteger(context.game().identity().creationFiletimeDecimal()),requireInventory().sha256());}
    private String phaseId(Action action){return "normal-exit-"+action.wire()+"-"+ActionCodec.sha256((context.game().generation()+":"+context.game().sessionId()+":"+requireInventory().sha256()).getBytes(java.nio.charset.StandardCharsets.UTF_8)).substring(0,32);}
    private PlanningReadResult.Known<Observation> queryActual(ContinuityStorePort.Session same,DriverObservationAssembler.Complete frame,Instant deadline)throws IOException{
        String nonce="normal-exit-query-"+UUID.randomUUID();var args=fields(new Request(nonce,Action.QUERY_CONTEXT,binding(frame),nonce,Optional.empty()));
        var result=context.reads().read(same,query,new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),query.operation(),args,deadline));
        if(!(result instanceof PlanningReadResult.Known<Observation> known))throw unavailable("actual normal-exit context read is unavailable");return known;}
    private static Binding binding(OpportunityJson.Obj args,BigInteger nativeRevision){var row=node(args);return new Binding(nativeRevision,StrictJson.integer(row.get("expected_player_character_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)),StrictJson.integer(row.get("expected_game_pid"),BigInteger.ONE,new BigInteger("4294967295")),StrictJson.integer(row.get("expected_connection_generation"),BigInteger.ONE,StrictJson.UINT64_MAX),StrictJson.integer(row.get("expected_process_creation_filetime_100ns"),BigInteger.ONE,StrictJson.UINT64_MAX),StrictJson.text(row.get("source_inventory_sha256")));}
    private static OpportunityJson.Obj fields(Request request){var value=(ObjectNode)StrictJson.parse(NormalExitProtocol.payload(request));for(String key:List.of("type","protocol_version","request_id","step","expected_revision"))value.remove(key);return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"normal-exit native fields");}
    private static NativeRequest nativeRequest(OpportunityJson.Obj args,BigInteger revision,String id){var row=node(args);Action action=Action.parse(StrictJson.text(row.get("action")));Request actual=new Request(id,action,binding(args,revision),StrictJson.text(row.get("request_nonce")),row.has("expected_exit_context_signature")?Optional.of(StrictJson.text(row.get("expected_exit_context_signature"))):Optional.empty());require(node(fields(actual)).equals(row),"normal-exit native fields differ from the sole strict protocol encoder");return new NativeRequest(STEP,Optional.of(CAP),raw(row));}
    private static OpportunityJson.Obj actionArguments(OpportunityJson.Obj nativeFields,ExactRef sourceQuery){var value=StrictJson.object();value.set("native",node(nativeFields));value.set("source_query",sourceQuery.toJson());return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"source-bound normal-exit command");}
    private static OpportunityJson.Obj actionFields(ActionCommand command){var value=StrictJson.object(node(command.arguments()),Set.of("native","source_query"));ExactRef.fromJson(value.get("source_query"));var action=Action.parse(StrictJson.text(value.path("native").get("action")));require(action!=Action.QUERY_CONTEXT&&command.operation().equals(selector(action).operationKey()),"normal-exit command crossed its closed mutation selector");return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value.get("native"))),"actual normal-exit native fields");}
    private PlanningReadReceipt contextOriginal(ExactRef ref,ActionPorts.OutcomeArchive archive){var receipt=archive.loadRead(ref);
        require(archive.readReferenceOf(receipt).equals(ref),"normal-exit context query original changed");NativeRecordedEvidenceVerifier.requireRead(receipt,archive);
        for(var guard:List.of(receipt.before(),receipt.after())){var frame=RootGuardEvidence.loadFrame(guard.binding(),archive,context.frameLoader());require(frame.fullBindingSha256().equals(guard.originalBindingSha256()),"normal-exit original context lost native/full Driver guard closure");
            try{RootGuardEvidence.requireHistory(guard.binding(),archive,context.borrowedSession());}catch(IOException failure){throw new UncheckedIOException("normal-exit original context history is unavailable",failure);}}return receipt;}
    private PlanningReadReceipt sourceQuery(ActionCommand command,ActionPorts.OutcomeArchive archive){var receipt=contextOriginal(ExactRef.fromJson(node(command.arguments()).get("source_query")),archive);var value=readObservation(receipt);var nativeFields=actionFields(command);
        var before=receipt.request().before();require(receipt.request().source().equals(command.source())&&receipt.request().sessionId().equals(command.sessionId())
                &&before.machineId().equals(command.before().machineId())&&before.game().equals(command.before().game())&&before.frame().identity().equals(command.before().frame().identity())
                &&before.frame().snapshotId().equals(command.before().frame().snapshotId())&&before.frame().episodeRunId().equals(command.before().frame().episodeRunId())
                &&before.frame().revision().equals(command.before().frame().revision())&&value.status()==Status.CONTEXT_OBSERVED
                &&value.binding().equals(binding(nativeFields,command.before().frame().identity().nativeRevision()))&&value.contextSignature().equals(StrictJson.text(node(nativeFields).get("expected_exit_context_signature"))),"normal-exit command lost its original queried context");
        for(var guard:List.of(receipt.before(),receipt.after())){
            require(!command.deadline().isAfter(guard.binding().validUntil()),"normal-exit command exceeds original context lease");}return receipt;}
    private void requirePublicContext(ActionCommand command,ContinuityStorePort.Session same,BigInteger revision,String signature){var original=sourceQuery(command,context.archive().withSession(same));require(original.request().before().frame().revision().equals(revision)
            &&StrictJson.text(node(actionFields(command)).get("expected_exit_context_signature")).equals(signature),"canonical phase belongs to another original public context");}
    private static NativeRequest prepared(ActionCommand command){return nativeRequest(actionFields(command),command.before().frame().identity().nativeRevision(),RequestIds.forCommand(command));}
    private static Observation readObservation(PlanningReadReceipt receipt){require(receipt.request().operation().equals(selector(Action.QUERY_CONTEXT).operationKey()),"normal-exit context is not its actual query contract");for(var guard:List.of(receipt.before(),receipt.after()))require(guard.binding().observed().equals(receipt.request().before()),"normal-exit context crossed actual before/after frame");require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"normal-exit query guard frame changed");require(receipt.original().nativeOk(),"normal-exit native query failed");return NormalExitProtocol.decodeObservation(StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes()),binding(receipt.request().arguments(),receipt.request().before().frame().identity().nativeRevision()),Action.QUERY_CONTEXT);}
    private static Optional<Observation> decodeAck(ActionCommand command,NativeActionPort.DispatchOutcome dispatch){if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.originalResultToken().isEmpty())return Optional.empty();var args=actionFields(command);return Optional.of(NormalExitProtocol.decodeObservation(StrictJson.parse(ack.originalResultToken().orElseThrow().bytes()),binding(args,command.before().frame().identity().nativeRevision()),Action.parse(StrictJson.text(node(args).get("action")))));}
    private static ExactRef intent(WriterContracts.Head head,ActionPorts.OutcomeArchive archive,String action){Optional<ExactRef> cursor=ContinuityActionJournal.recordHead(head.state());Set<ExactRef> seen=new HashSet<>();while(cursor.isPresent()){var ref=cursor.orElseThrow();require(seen.add(ref)&&seen.size()<=100000,"bounded actual action intent lineage required");var record=archive.loadRecord(ref);require(archive.recordReferenceOf(record).equals(ref),"normal-exit canonical record changed");if(record.receipt().command().actionId().equals(action)&&record.receipt().state() instanceof ActionState.IntentDurable)return ref;cursor=record.previous();}throw new IllegalArgumentException("normal-exit durable intent is absent");}
    private static ObjectNode base(String schema,BigInteger revision,Binding binding){return StrictJson.object().put("schema",schema).put("public_revision",revision).put("source_inventory_sha256",binding.sourceInventorySha256()).put("process_creation_filetime_100ns",binding.creationFiletime());}
    private static ObjectNode node(OpportunityJson.Obj value){var parsed=StrictJson.parse(OpportunityJson.encode(value));if(!(parsed instanceof ObjectNode result))throw new IllegalArgumentException("normal-exit object required");return result;}
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value));}
    private NormalExitSourceInventory.Qualified requireInventory(){return inventory.orElseThrow(()->new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,"normal-exit source inventory is absent",Optional.empty()));}
    private void requireCurrentSource(){var inv=requireInventory();try{inv.requireCurrent(context.game());}catch(IOException|IllegalArgumentException failure){throw new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,"normal-exit source inventory unsupported: "+failure.getMessage(),Optional.empty());}}
    private static void available(boolean condition,String message){if(!condition)throw unavailable(message);}
    private static PublicServiceFailure unavailable(String message){return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,message,Optional.empty());}
}
