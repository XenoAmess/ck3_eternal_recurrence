package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.ritecreation.*;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import org.xar.ck3.control.application.ritecreation.RiteCreationState.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.ritecreation.RiteCreationNative;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;

/** Original conditional Rite public controls, one per-Game instance and one durable writer. */
public final class RootRiteCreationRuntimeFactory {
    private RootRiteCreationRuntimeFactory(){}
    public static final String OBSERVER="xar.java.rite-original-control-post/v1";
    @FunctionalInterface public interface ScopeProvider{Scope require(Complete actual)throws IOException;}
    public record Sources(RiteCreationNative.Sources nativeSources,ExactRef runtimeSource,List<ExactRef> producerClosure,boolean privateActionsEnabled,ScopeProvider scopes,OriginalRuntimeHandoffProof.Provider legacyRuntime){
        public Sources{Objects.requireNonNull(nativeSources);Objects.requireNonNull(runtimeSource);producerClosure=List.copyOf(producerClosure);Objects.requireNonNull(scopes);Objects.requireNonNull(legacyRuntime);need(runtimeSource.bytes()>0&&!producerClosure.isEmpty()&&producerClosure.size()<=32,"actual Rite runtime/full producer closure required");}
        List<ExactRef> refs(){var refs=new LinkedHashSet<ExactRef>(nativeSources.originalProducerClosure());refs.add(nativeSources.definition());refs.add(nativeSources.decoder());refs.add(runtimeSource);refs.addAll(producerClosure);return List.copyOf(refs);}
    }
    /** Explicit ordinary business controls and actual live scope provider; no registration or Prepared wrapper. */
    public record OrdinaryConfiguration(boolean privateActionsEnabled,ScopeProvider scopes) {
        public OrdinaryConfiguration {Objects.requireNonNull(scopes);}
    }
    public record OrdinarySources(RiteCreationNative.Sources nativeSources,ExactRef runtime,List<ExactRef> producers) {
        public OrdinarySources {Objects.requireNonNull(nativeSources);Objects.requireNonNull(runtime);producers=List.copyOf(producers);}
    }
    public static Prepared prepareOrdinary(OrdinaryConfiguration configuration,OrdinarySources sources) {
        Objects.requireNonNull(configuration);Objects.requireNonNull(sources);
        return new Prepared(new Sources(sources.nativeSources(),sources.runtime(),sources.producers(),
                configuration.privateActionsEnabled(),configuration.scopes(),
                org.xar.ck3.control.platform.WindowsOriginalRuntimeHandoff.originalOwnedLaunch(Optional.empty())),true);
    }
    public record Installed(Runtime runtime,RootDomainInstallation installation){public Installed{Objects.requireNonNull(runtime);Objects.requireNonNull(installation);}}
    public static final class Prepared{
        private final Sources sources;private final RootRiteCreationDomain domain;private RootApplicationAssembly.Core core;private final boolean ordinary;
        private final IdentityHashMap<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        public Prepared(Sources sources){this(sources,false);}
        private Prepared(Sources sources,boolean ordinary){this.sources=Objects.requireNonNull(sources);this.ordinary=ordinary;domain=new RootRiteCreationDomain(sources.refs());}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of(domain.registration());}
        public synchronized void bindCore(RootApplicationAssembly.Core actual){need(core==null,"Rite Prepared Core is once bound");core=Objects.requireNonNull(actual);domain.bindCore(actual);}
        public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized Installed install(RootRuntimeContext context)throws IOException{
            need(context.core()==core,"Rite installation requires the identical pre-bound Core");Installed old=installed.get(context);if(old!=null)return old;
            var pins=ordinary?List.<SharedSourceFiles.Witness>of():witness(sources.refs());Runtime runtime=new Runtime(context,sources,domain,ordinary);Installed actual=new Installed(runtime,runtime.installation);for(var pin:pins)SharedSourceFiles.assertUnchanged(pin);installed.put(context,actual);return actual;
        }
    }
    private record CommandData(Frame frame,Execute request,Optional<ExactRef> previewRead){ }
    public static final class Runtime{
        private final RootRuntimeContext context;private final Sources sources;private final RootRiteCreationDomain domain;private final boolean ordinary;
        private final RiteCreationNative nativePort;private final RootDomainInstallation installation;private final RootRiteCreationLegacyImport legacyImport;
        private Runtime(RootRuntimeContext context,Sources sources,RootRiteCreationDomain domain,boolean ordinary)throws IOException{
            this.context=context;this.sources=sources;this.domain=domain;this.ordinary=ordinary;nativePort=new RiteCreationNative(context.transport(),sources.nativeSources());legacyImport=new RootRiteCreationLegacyImport(context,domain);
            var actions=new ArrayList<RootExecutableBindings.ActionBinding>();var recorded=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();var required=new LinkedHashSet<OperationKey>();
            if(sources.privateActionsEnabled())for(RiteCreation operation:RiteCreation.values())if(operation!=RiteCreation.PREVIEW){actions.add(action(operation));recorded.add(recorded(operation));required.add(operation.operationKey());}
            var intent=new RootDomainIntentPreparation.Binding("original-rite-once-before-intent/v1",sources.runtimeSource(),command->required.contains(command.operation()),(same,command)->{try{beforeIntent(same,command);}catch(IOException failure){throw new UncheckedIOException(failure);}});
            installation=new RootDomainInstallation("original-rite-creation-12004/v1",List.of(domain.registration()),List.of(),sources.privateActionsEnabled()?List.of(nativePort.previewFamily()):List.of(),actions,List.of(),recorded,List.of(),List.of(),List.of(),sources.privateActionsEnabled()?List.of(intent):List.of(),required,List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public DomainBodies.Registration registration(){return domain.registration();}
        public RootDomainInstallation installation(){return installation;}
        public DomainBodies.BodyRef initializeFresh(RootRuntimeContext same,Session original,RootInitialEpisodeProof proof)throws IOException{requireContext(same);var body=domain.initializeFresh(context,original,proof,sources.scopes());return initializeOriginalStore(original,body);}
        public DomainBodies.BodyRef initializeFresh(RootRuntimeContext same,Session original,FreshCampaignContext proof)throws IOException{requireContext(same);return domain.initializeFresh(context,original,proof);}
        public DomainBodies.BodyRef initializeNext(RootRuntimeContext same,Session original,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException{requireContext(same);var body=domain.initializeNext(context,original,proof);return initializeOriginalStore(original,body);}
        public void requireOwner(RootApplicationSession actual){need(context.actions()==actual,"Rite adapter must resolve identical current per-Game runtime");}
        public boolean enabled(){return sources.privateActionsEnabled();}
        private OriginalRuntimeHandoffProof.Result<RootRiteCreationLegacyImport.Publication> refreshOriginalStore(Session same)throws IOException{
            domain.requireContext(context,same);return sources.legacyRuntime().withOriginalStore(RootRiteCreationLegacyImport.actualStore(context),context.game().machineId(),lease->legacyImport.importOriginal(same,lease));
        }
        private DomainBodies.BodyRef initializeOriginalStore(Session same,DomainBodies.BodyRef actualBasis)throws IOException{
            var result=refreshOriginalStore(same);if(result instanceof OriginalRuntimeHandoffProof.Available<RootRiteCreationLegacyImport.Publication> available)return Objects.requireNonNull(available.value()).body();
            // A genuine missing old runtime leaves a valid initialized v2 body with legacyStore absent. That absence never grants final confirm.
            return actualBasis;
        }
        private void requireOriginalStore(Session same)throws IOException{
            // Already admitted canonical history replays from its original immutable manifest, not a new OS lease.
            // Every newly read filesystem update still goes through refreshOriginalStore and its actual scoped provider.
            if(domain.fullState(same).legacyStore().isPresent())return;
            var result=refreshOriginalStore(same);if(result instanceof OriginalRuntimeHandoffProof.Available<RootRiteCreationLegacyImport.Publication> available){var publication=Objects.requireNonNull(available.value());if(!publication.qualified())throw new IOException(publication.diagnosis()+"; original manifest="+publication.originalManifest().path());return;}
            var missing=(OriginalRuntimeHandoffProof.Unavailable<RootRiteCreationLegacyImport.Publication>)result;throw new IOException("actual original once custody unavailable: "+missing.reason()+": "+missing.detail());
        }
        private RawJson retainedLegacy(Session same,RiteCreationLegacyStore.Intent original)throws IOException{
            if(original.originalResultFailure().isPresent())return legacyPending(original,false);
            if(original.originalNativeResult().isEmpty())return legacyPending(original,!original.blocksRetry());
            var evidence=original.originalNativeResult().orElseThrow();byte[] packet=context.archive().readArtifact(same,evidence.preserved(),RootRiteCreationLegacyImport.MAX_FILE);var result=RiteCreationLegacyStore.decodeResult(new RawJson(packet),original.binding(),original.fields());
            need(result.knownNoDispatch()==!original.blocksRetry(),"legacy retained no-dispatch state contradicts original packet");return RiteCreationCodec.retainedResult(result,original.id(),evidence.preserved(),!original.blocksRetry());
        }
        private RawJson collectLegacy(Session same,ActionId action)throws IOException{
            var stored=domain.fullState(same).legacyStore();Optional<RiteCreationLegacyStore.Intent> original=stored.flatMap(v->v.intents().stream().filter(i->i.id().equals(action)).findFirst());
            if(original.isPresent()&&original.orElseThrow().status()!=RiteCreationLegacyStore.Status.ORIGINAL_UNKNOWN_NO_RETRY)return retainedLegacy(same,original.orElseThrow());
            var refreshed=refreshOriginalStore(same);
            if(refreshed instanceof OriginalRuntimeHandoffProof.Unavailable<RootRiteCreationLegacyImport.Publication> missing){if(original.isPresent()){ObjectNode pending=object(legacyPending(original.orElseThrow(),false));pending.put("original_store_refresh_unavailable",missing.reason().name());return raw(pending);}throw new IOException("actual original Python once request and current custody unavailable; no new intent or native submit");}
            var found=domain.fullState(same).legacyStore().flatMap(v->v.intents().stream().filter(i->i.id().equals(action)).findFirst()).orElseThrow(()->new IOException("actual original Python once request absent; no new intent or native submit"));return retainedLegacy(same,found);
        }
        private static RawJson legacyPending(RiteCreationLegacyStore.Intent original,boolean released){ObjectNode n=object(pending(original.id(),released));n.put("status_scope","original_request_result_only_not_current_legality");original.originalResultFailure().ifPresent(v->n.put("original_result_unavailable_reason",v));return raw(n);}
        public RawJson query(Session same,Complete actual,Query request,Instant deadline)throws IOException{
            requireEnabled();Frame frame=requireFrame(actual);need(frame.publicRevision().equals(request.expectedRevision()),"stale Rite query revision");domain.requireContext(context,same);RiteCreationState.requireBasis(domain.read(same),frame);
            var known=read(same,actual,request,deadline);var archive=context.archive().withSession(same);ExactRef receipt=archive.readReferenceOf(known.receipt()),token=archive.preserveMaterial(known.value().original());
            var input=empty().put("kind","original_rite_preview");input.set("original_read",receipt.toJson());input.set("original_native_result",token.toJson());
            domain.publish(same,raw(input),List.of(receipt,token),(original,previous)->{
                domain.requireContext(context,original);need(requireFrame(actual).equals(frame),"actual Rite preview scope changed");Result result=originalPreview(archive.loadRead(receipt),frame,request.source(),archive);
                need(archive.loadMaterial(token).equals(result.original()),"Rite retained preview token changed");return RiteCreationState.observedPreview(previous.orElseThrow(),new Preview(frame,request.source(),receipt,token),result);
            });return publicResult(known.value(),frame,new ActionId("rite-action-"+UUID.randomUUID().toString().replace("-","")),receipt,false,false);
        }
        private PlanningReadResult.Known<Result> read(Session same,Complete actual,Query query,Instant deadline)throws IOException{
            Frame frame=requireFrame(actual);var selection=new RiteCreationNative.Selection(actual,frame,query,deadline);var contract=nativePort.issue(context.readCatalog(),selection);var value=context.reads().read(same,contract,nativePort.request(selection));
            if(value instanceof PlanningReadResult.Known<Result> known)return known;throw new IOException("actual original Rite preview unavailable: "+value);
        }
        public RootApplicationSession.PublicActionDecision<RawJson> prepare(Session same,Complete actual,Execute request,Instant deadline)throws IOException{
            requireEnabled();domain.requireContext(context,same);Frame frame=requireFrame(actual);need(request.expectedRevision().equals(frame.publicRevision()),"stale Rite action revision");State old=domain.read(same);RiteCreationState.requireBasis(old,frame);
            Optional<ExactRef> preview=Optional.empty();
            if(request.action() instanceof Confirm confirm){
                Optional<Claim> blocking=old.blocking(new Key(frame.scope(),frame.actor(),request.source()));
                if(blocking.isPresent())return new RootApplicationSession.RetainPublicResult<>(retained(same,blocking.orElseThrow(),false));
                requireOriginalStore(same);var legacy=domain.fullState(same).legacyBlocking(new Key(frame.scope(),frame.actor(),request.source()));if(legacy.isPresent())return new RootApplicationSession.RetainPublicResult<>(retainedLegacy(same,legacy.orElseThrow()));
                Preview retained=old.preview().orElseThrow(()->new IOException("actual post-modal Rite preview is not retained"));need(retained.frame().equals(frame)&&retained.source().equals(request.source()),"Rite final preview crossed source/frame");
                originalPreview(context.archive().withSession(same).loadRead(retained.originalRead()),frame,request.source(),context.archive().withSession(same)).requireFinalPreview(confirm);preview=Optional.of(retained.originalRead());
            }
            var args=empty().put("schema","xar.java.rite-original-command/v1");args.set("frame",RiteCreationState.frame(frame));args.set("execution",object(execution(request)));if(preview.isPresent())args.set("original_preview_read",preview.orElseThrow().toJson());else args.putNull("original_preview_read");
            var expected=new ExpectedPostcondition(1,actual.identity(),actual.source(),OBSERVER,controlValues());var claims=new Claims(Set.of(),Set.of(),Set.of(actual.identity().frame().identity().player()),Set.of("rite-creation:"+frame.scope().kind()+":"+frame.scope().stableKey()+":"+request.source().value()));
            String id="rite-action-"+UUID.randomUUID().toString().replace("-","");return new RootApplicationSession.SubmitPublicAction<>(new ActionCommand(id,actual.identity(),actual.source(),actual.sessionId(),request.action().operation().operationKey(),obj(args),expected,claims,deadline));
        }
        private void beforeIntent(Session same,ActionCommand command)throws IOException{
            requireCommand(command);CommandData data=data(command);var input=new RawJson(ActionCodec.encodeCommand(command));var evidence=data.previewRead().map(List::of).orElse(List.of(sources.runtimeSource()));
            domain.publish(same,input,evidence,(original,previous)->{
                domain.requireContext(context,original);State old=previous.orElseThrow();RiteCreationState.requireBasis(old,data.frame());nativePort.requireHeld(data.frame());
                context.core().actions().withFrozen(original,lease->{need(lease.find(command.actionId()).isEmpty(),"original Rite INTENT already exists; never recreate its claim");lease.assertCurrent();return null;});
                if(data.request().action() instanceof Confirm){need(domain.fullState(original).legacyBlocking(new Key(data.frame().scope(),data.frame().actor(),data.request().source())).isEmpty(),"original Python once scope already claimed; no canonical retry");var archive=context.archive().withSession(original);Result actual=originalPreview(archive.loadRead(data.previewRead().orElseThrow()),data.frame(),data.request().source(),archive);
                    return RiteCreationState.start(old,new Claim(new ActionId(command.actionId()),data.frame(),data.request(),data.previewRead().orElseThrow(),Status.CLAIMED_RESULT_UNKNOWN_NO_RETRY,Optional.empty()),actual);}
                return RiteCreationState.invalidatePreview(old);
            });
        }
        private RootExecutableBindings.ActionBinding action(RiteCreation operation){
            var producer=new ActionPorts.PreparationPort(){
                @Override public NativeRequest prepare(ActionCommand command){throw new IllegalArgumentException("Rite producer requires the actual canonical writer and protocol request identity");}
                @Override public NativeRequest prepare(Session same,ActionCommand command,String originalRequestId){
                    try{domain.requireContext(context,same);requireCommand(command);need(command.operation().equals(operation.operationKey()),"finite Rite logical selector changed");CommandData data=data(command);
                        need(originalRequestId.equals(RequestIds.forActionBody(ActionCodec.bodySha256(command))),"Rite original coordinator request identity differs");var pins=ordinary?List.<SharedSourceFiles.Witness>of():witness(sources.refs());
                        var fields=fields(data,originalRequestId);NativeRequest request=nativePort.prepare(data.frame(),fields);for(var pin:pins)SharedSourceFiles.assertUnchanged(pin);return request;
                    }catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
                }
            };
            var effect=new NativeEffectRegistry.Binding(operation.operationKey(),sources.runtimeSource(),producer,this::observe);
            return new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(CAPABILITY),sources.nativeSources().decoder());
        }
        private NativeRecordedEvidenceVerifier.Binding recorded(RiteCreation operation){
            return new NativeRecordedEvidenceVerifier.Binding(operation.operationKey(),sources.runtimeSource(),(head,receipt,archive)->{
                try{
                need(receipt.state() instanceof ActionState.Settled,"Rite archived settlement is absent");var settled=(ActionState.Settled)receipt.state();CommandData data=data(receipt.command());Result ack=validateAck(receipt.command(),settled.attempt(),settled.dispatch(),archive);
                if(settled.settlement() instanceof ActionState.Rejected rejected){need(ack.knownNoDispatch()&&rejected.originalEvidence().equals(archive.referenceOf(settled.dispatch())),"Rite rejection lacks actual no-dispatch native proof");return;}
                need(settled.settlement() instanceof ActionState.ControlApplied,"Rite cannot claim business, game progression, SAVE or final religious outcome");var control=(ActionState.ControlApplied)settled.settlement();
                replayControl(receipt.command(),settled.attempt(),(NativeActionPort.AckReceived)settled.dispatch(),control,data,archive);
                }catch(IOException failure){throw new UncheckedIOException("actual Rite archived proof unavailable",failure);}
            });
        }
        private NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
            if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return NativeEffectRegistry.Projected.pending("original Rite result unknown; never replay",List.of(attempt.guard().nativeEvidence()));
            try{return context.withSession(same->{
                var archive=context.archive().withSession(same);Result original=validateAck(command,attempt,ack,archive);CommandData data=data(command);
                if(original.knownNoDispatch())return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"matching original Rite result proves no native dispatch and no possible queue",archive.referenceOf(ack))),Optional.empty());
                if(data.request().action() instanceof Confirm)return NativeEffectRegistry.Projected.pending("original Rite final writer may be queued; independent religious business observation remains unqualified",List.of(archive.referenceOf(ack)));
                var identity=new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());
                return context.collector().currentOwned(same,identity,ActionObservationWindow.deadline(command),lease->{
                    Complete current=lease.frame();Frame frame=requireFrame(current);requireSameOwner(data.frame(),frame);var after=read(same,current,new Query(frame.publicRevision(),data.request().source()),ActionObservationWindow.deadline(command));
                    requireControl(data.request().action(),after.value());var control=new ActionState.ControlApplied(after.receipt(),OBSERVER,controlValues());replayControl(command,attempt,ack,control,data,archive);
                    return new NativeEffectRegistry.Projected(new ActionPorts.ControlObserved(control),Optional.empty());
                });
            });}catch(IOException|IllegalArgumentException|IllegalStateException unavailable){return NativeEffectRegistry.Projected.pending("original Rite independent control postcondition unavailable: "+unavailable.getMessage(),List.of(attempt.guard().nativeEvidence()));}
        }
        private Result validateAck(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,ActionPorts.OutcomeArchive archive)throws IOException{
            need(dispatch instanceof NativeActionPort.AckReceived,"actual original Rite ACK absent");var ack=(NativeActionPort.AckReceived)dispatch;CommandData data=data(command);
            need(attempt.requestId().equals(RequestIds.forActionBody(ActionCodec.bodySha256(command)))&&attempt.guard().connectionGeneration().equals(data.frame().connectionGeneration()),"Rite attempt identity/generation changed");
            ack.custody().orElseThrow(()->new IllegalArgumentException("actual Rite original custody absent")).verify(ack,attempt.guard());RiteCreationNative.requireWire(ack,attempt.requestId(),data.frame(),fields(data,attempt.requestId()));
            return RiteCreationCodec.result(ack.originalResultToken().orElseThrow(),data.frame(),fields(data,attempt.requestId()));
        }
        private void replayControl(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,ActionState.ControlApplied control,CommandData data,ActionPorts.OutcomeArchive archive)throws IOException{
            validateAck(command,attempt,ack,archive);need(!(data.request().action() instanceof Confirm),"final Rite business outcome cannot be settled as a UI control");NativeRecordedEvidenceVerifier.requireRead(control.read(),archive);NativeRequestChronology.requireSampledAfter(control.read(),attempt,ack);
            Frame after=RiteCreationState.frame(get(node(control.read().request().arguments()),"frame"));requireSameOwner(data.frame(),after);Result observed=originalPreview(control.read(),after,data.request().source(),archive);requireControl(data.request().action(),observed);
            need(control.supportingReads().isEmpty()&&control.observerSchema().equals(OBSERVER)&&control.actual().equals(controlValues()),"Rite independent control evidence differs");ActionEffects.validate(command,attempt,ack,control);
        }
        public RawJson result(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive archive)throws IOException{
            requireCommand(actual.command());CommandData data=data(actual.command());var id=new ActionId(actual.command().actionId());
            if(data.request().action() instanceof Confirm){
                retainOutcome(same,actual,actual.ack());Claim retained=domain.read(same).find(id).orElseThrow();return retained(same,retained,false);
            }
            if(actual.ack().isEmpty())return pending(id,actual.state() instanceof ActionState.RejectedBeforeDispatch);
            var ack=actual.ack().orElseThrow();Result result=validateAck(actual.command(),attempt(actual),ack,archive);return publicResult(result,data.frame(),id,archive.referenceOf(ack),false,false);
        }
        public RawJson collect(Session same,Collect request,Instant deadline)throws IOException,InterruptedException{
            requireEnabled();domain.requireContext(context,same);Optional<Claim> javaClaim=domain.read(same).find(request.action());if(javaClaim.isEmpty())return collectLegacy(same,request.action());Claim claim=javaClaim.orElseThrow();
            if(claim.result().isPresent())return retained(same,claim,true);
            var archive=context.archive().withSession(same);ActionReceipt original=ContinuityActionJournal.lookup(same.head().state(),request.action().value(),archive).orElseThrow(()->new IOException("original Rite canonical action chain absent"));
            requireClaim(original,claim);if(original.state() instanceof ActionState.RejectedBeforeDispatch){retainOutcome(same,original,Optional.empty());return retained(same,domain.read(same).find(claim.id()).orElseThrow(),true);}
            Optional<NativeActionPort.AckReceived> ack=original.ack();if(ack.isEmpty())ack=nativePort.collect(RequestIds.forActionBody(original.bodySha256()),deadline);
            if(ack.isEmpty())return pending(claim.id(),false);retainOutcome(same,original,ack);return retained(same,domain.read(same).find(claim.id()).orElseThrow(),true);
        }
        private void retainOutcome(Session same,ActionReceipt actual,Optional<NativeActionPort.AckReceived> result)throws IOException{
            var archive=context.archive().withSession(same);ExactRef receipt=archive.receiptReferenceOf(actual);need(actual.equals(archive.loadReceipt(receipt)),"Rite original action archive readback differs");
            if(result.isEmpty()&&!(actual.state() instanceof ActionState.RejectedBeforeDispatch))return;
            ExactRef dispatch=actual.state() instanceof ActionState.RejectedBeforeDispatch zero?archive.referenceOf(zero.dispatch()):archive.preserve(result.orElseThrow());
            var input=empty().put("kind","original_rite_outcome");input.set("canonical_action_receipt",receipt.toJson());input.set("original_dispatch",dispatch.toJson());
            domain.publish(same,raw(input),List.of(receipt,dispatch),(original,previous)->{
                domain.requireContext(context,original);var scoped=context.archive().withSession(original);ActionReceipt retained=scoped.loadReceipt(receipt);Claim claim=previous.orElseThrow().find(new ActionId(retained.command().actionId())).orElseThrow();requireClaim(retained,claim);
                ActionReceipt canonical=ContinuityActionJournal.lookup(original.head().state(),retained.command().actionId(),scoped).orElseThrow();need(java.util.Arrays.equals(ActionReceiptCodec.encodeReceipt(retained,scoped),ActionReceiptCodec.encodeReceipt(canonical,scoped)),"Rite result is outside the canonical original action chain");
                String protocol=RequestIds.forActionBody(retained.bodySha256());
                if(retained.state() instanceof ActionState.RejectedBeforeDispatch zero){
                    need(zero.dispatch().equals(scoped.load(dispatch))&&zero.dispatch().requestId().equals(protocol)&&zero.dispatch().proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE&&zero.dispatch().proof().requestBytesWritten()==0,"Rite known-before-send release requires actual canonical BEFORE_WRITE zero bytes");
                    RootGuardEvidence.loadFrame(zero.attempt().guard(),scoped,context.core().frameLoader());return RiteCreationState.beforeSendRejected(previous.orElseThrow(),claim.id(),new OriginalResult(protocol,dispatch,receipt,ResultKind.CANONICAL_ZERO_DISPATCH_BEFORE_WRITE));
                }
                NativeActionPort.DispatchOutcome originalDispatch=scoped.load(dispatch);Result observed=validateAck(retained.command(),attempt(retained),originalDispatch,scoped);
                return RiteCreationState.originalResult(previous.orElseThrow(),claim.id(),observed,new OriginalResult(protocol,dispatch,receipt));
            });
        }
        private RawJson retained(Session same,Claim claim,boolean collecting)throws IOException{
            if(claim.result().isEmpty())return pending(claim.id(),false);OriginalResult proof=claim.result().orElseThrow();var archive=context.archive().withSession(same);ActionReceipt original=archive.loadReceipt(proof.canonicalActionReceipt());requireClaim(original,claim);
            if(proof.kind()==ResultKind.CANONICAL_ZERO_DISPATCH_BEFORE_WRITE){need(original.state() instanceof ActionState.RejectedBeforeDispatch,"Rite retained zero-dispatch subtype changed");var zero=(ActionState.RejectedBeforeDispatch)original.state();need(zero.dispatch().equals(archive.load(proof.originalPacket()))&&zero.dispatch().proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE&&zero.dispatch().proof().requestBytesWritten()==0,"Rite retained zero-write source changed");return pending(claim.id(),true);}
            Result result=validateAck(original.command(),attempt(original),archive.load(proof.originalPacket()),archive);need(result.knownNoDispatch()==(claim.status()==Status.KNOWN_NO_DISPATCH_RELEASED),"Rite retained release contradicts original result");
            return publicResult(result,claim.frame(),claim.id(),proof.originalPacket(),claim.status()==Status.KNOWN_NO_DISPATCH_RELEASED,collecting);
        }
        private Result originalPreview(PlanningReadReceipt original,Frame frame,SourceRite source,ActionPorts.OutcomeArchive archive)throws IOException{
            NativeRecordedEvidenceVerifier.requireRead(original,archive);need(original.request().operation().equals(RiteCreation.PREVIEW.operationKey()),"actual Rite preview logical operation changed");
            need(RiteCreationState.frame(get(node(original.request().arguments()),"frame")).equals(frame),"Rite original preview request/frame changed");
            need(original.before().binding().observed().equals(original.request().before())&&original.after().binding().observed().equals(original.request().before())&&original.before().binding().connectionGeneration().equals(frame.connectionGeneration())&&original.after().binding().connectionGeneration().equals(frame.connectionGeneration()),"Rite original preview guard owner changed");
            RiteCreationNative.requireWire(original.original(),original.requestId(),frame,NativeFields.preview(source));return RiteCreationCodec.result(original.original().originalResultToken().orElseThrow(),frame,NativeFields.preview(source));
        }
        private void requireCommand(ActionCommand command){data(command);need(command.source().equals(context.source())&&command.sessionId().equals(context.game().sessionId())&&command.before().game().equals(context.game().generation())&&command.before().machineId().equals(context.game().machineId()),"Rite action crossed actual per-Game source/session");}
        public void requireContext(RootRuntimeContext same){need(same==context,"Rite provider crossed its actual per-Game context");}
        private Frame requireFrame(Complete actual)throws IOException{need(actual.source().equals(context.source())&&actual.sessionId().equals(context.game().sessionId())&&actual.identity().game().equals(context.game().generation()),"Rite current source/Game/session differs");return RiteCreationCodec.frame(actual,sources.scopes().require(actual));}
        private void requireEnabled(){need(enabled(),"original allow_private_player_rite_creation_actions is not true");}
    }
    private static CommandData data(ActionCommand command){
        ObjectNode n=node(command.arguments());shape(n,Set.of("schema","frame","execution","original_preview_read"),Set.of());equal(get(n,"schema"),"xar.java.rite-original-command/v1");Frame frame=RiteCreationState.frame(get(n,"frame"));Execute request=RiteCreationCodec.execute(raw(get(n,"execution")));Optional<ExactRef> preview=nullable(n,"original_preview_read",ExactRef::fromJson);
        need(command.actionId().matches("rite-action-[a-f0-9]{32}")&&command.operation().equals(request.action().operation().operationKey())&&request.expectedRevision().equals(frame.publicRevision())&&(request.action() instanceof Confirm)==preview.isPresent(),"Rite command selector/identity/final preview changed");
        need(command.before().frame().snapshotId().equals(frame.snapshotId())&&command.before().frame().revision().equals(frame.publicRevision())&&command.before().frame().identity().nativeRevision().equals(frame.nativeRevision())&&command.before().frame().identity().player().intValueExact()==frame.actor()&&command.before().frame().identity().dateRaw().intValueExact()==frame.dateRaw()&&command.before().game().pid()==frame.gamePid(),"Rite command actual observation/frame differs");
        return new CommandData(frame,request,preview);
    }
    private static NativeFields fields(CommandData data,String originalProtocolRequestId){return new NativeFields(data.request().action().operation(),data.request().source(),Optional.of(data.request().action()),data.request().action() instanceof Confirm?Optional.of(originalProtocolRequestId):Optional.empty());}
    private static void requireClaim(ActionReceipt actual,Claim claim){CommandData data=data(actual.command());need(actual.command().actionId().equals(claim.id().value())&&data.frame().equals(claim.frame())&&data.request().equals(claim.request())&&data.previewRead().equals(Optional.of(claim.originalPreviewRead())),"Rite claim differs from its original canonical action body");}
    private static ActionState.Attempt attempt(ActionReceipt actual){return switch(actual.state()){case ActionState.AckReceived ack->ack.attempt();case ActionState.Settled settled->settled.attempt();case ActionState.Unknown unknown->unknown.attempt().orElseThrow();case ActionState.RejectedBeforeDispatch zero->zero.attempt();default->throw new IllegalArgumentException("Rite original attempt not durably recorded");};}
    private static List<ExpectedValue> controlValues(){return List.of(new ExpectedBoolean(new FieldKey("rite_control_postcondition_verified"),true));}
    private static void requireSameOwner(Frame before,Frame after){need(before.scope().equals(after.scope())&&before.actor()==after.actor()&&before.gamePid()==after.gamePid()&&before.connectionGeneration().equals(after.connectionGeneration())&&before.dateRaw()==after.dateRaw(),"Rite post-control read crossed actual owner/paused date");}
    private static void requireControl(Write requested,Result actual){
        need(actual.operation()==RiteCreation.PREVIEW&&actual.available()&&actual.draft().observed(),"independent actual Rite draft unavailable");
        switch(requested){
            case OpenCreate ignored->need(actual.draft().outcome().filter(v->v==Outcome.CREATE_FAITH||v==Outcome.CREATE_RITE).isPresent(),"actual create draft not observed");
            case OpenEdit ignored->need(actual.draft().outcome().equals(Optional.of(Outcome.EDIT_RITE)),"actual edit draft not observed");
            case CoreTenet tenet->need(actual.draft().tenets().orElseThrow().stream().anyMatch(v->v.slot()==tenet.slot()&&v.key().equals(tenet.tenet())),"actual selected tenet differs");
            case Doctrine doctrine->need(actual.draft().doctrines().orElseThrow().stream().anyMatch(v->v.group().equals(doctrine.group())&&v.key().equals(doctrine.doctrine())),"actual selected doctrine differs");
            case Name name->{Names values=actual.draft().names();Optional<String> value=switch(name.field()){case NAME->values.name();case ADJECTIVE->values.adjective();case ADHERENT->values.adherent();case ADHERENT_PLURAL->values.adherentPlural();case DESCRIPTION->values.description();};need(value.equals(Optional.of(name.text())),"actual native name write differs");}
            case Prepare prepare->actual.requireFinalPreview(new Confirm(actual.preview().orElseThrow(),prepare.outcome()));
            case Confirm ignored->throw new IllegalArgumentException("final Rite business outcome has no qualified independent producer");
        }
    }
    private static List<SharedSourceFiles.Witness> witness(List<ExactRef> refs)throws IOException{var out=new ArrayList<SharedSourceFiles.Witness>();for(ExactRef ref:refs){var pin=SharedSourceFiles.observe(java.nio.file.Path.of(ref.path()));need(pin.source().bytes()==ref.bytes()&&pin.source().sha256().equals(ref.sha256()),"actual Rite full producer source drift");out.add(pin);}return List.copyOf(out);}
}
