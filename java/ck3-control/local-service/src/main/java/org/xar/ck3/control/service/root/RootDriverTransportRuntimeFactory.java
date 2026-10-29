package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real Driver subgroup, installed before the sole read/action catalog freezes. */
public final class RootDriverTransportRuntimeFactory {
    private RootDriverTransportRuntimeFactory() { }
    public record Sources(ExactRef nativeDefinition,ExactRef decoder,ExactRef runtime,List<ExactRef> nativeProducerClosure,ExactRef richMaterial) {
        public Sources {Objects.requireNonNull(nativeDefinition);Objects.requireNonNull(decoder);Objects.requireNonNull(runtime);Objects.requireNonNull(richMaterial);nativeProducerClosure=List.copyOf(nativeProducerClosure);}
        public List<ExactRef> refs(){return refs(nativeDefinition,decoder,runtime,nativeProducerClosure,richMaterial);}
        private static List<ExactRef> refs(ExactRef a,ExactRef b,ExactRef c,List<ExactRef> closure,ExactRef richMaterial){var result=new ArrayList<>(List.of(a,b,c,richMaterial));result.addAll(closure);return List.copyOf(new LinkedHashSet<>(result));}
    }
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final Sources sources;private final boolean privateSemanticReadonly;
        private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,Runtime> installed=new IdentityHashMap<>();
        public Prepared(Sources sources,boolean actualAllowPrivateSemanticSnapshotReadonly){this.sources=Objects.requireNonNull(sources);privateSemanticReadonly=actualAllowPrivateSemanticSnapshotReadonly;}
        public boolean privateSemanticReadonly(){return privateSemanticReadonly;}
        public RootDriverRegistryPublicProducts.Kind kind(){return RootDriverRegistryPublicProducts.Kind.TRANSPORT;}
        public RootDriverRegistryPublicProducts.ProductSource source(){return new RootDriverRegistryPublicProducts.ProductSource(RootDriverTransportRuntimeFactory.class,"local-service/src/main/java/org/xar/ck3/control/service/root/RootDriverTransportRuntimeFactory.java",sources.runtime());}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public Collection<NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {if(core!=null&&core!=actual)throw new IOException("transport products already bound to another Core");core=Objects.requireNonNull(actual);}
        public synchronized Runtime install(RootRuntimeContext context)throws IOException {
            if(core==null||core!=context.core())throw new IOException("transport product needs the identical bound Core");Runtime old=installed.get(context);if(old!=null)return old;
            if(installed.size()>=64)throw new IOException("bounded actual transport per-Game products exhausted");
            Runtime result=new Runtime(context,sources,privateSemanticReadonly);
            installed.put(context,result);return result;
        }
        public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,PublicBindings bindings)throws IOException {return RootDriverTransportPublicSupplier.install(context,bindings);}
    }
    public static final class Runtime implements RootDriverRegistryPublicProducts.Product {
        private final RootRuntimeContext context;private final Sources sources;private final boolean privateSemanticReadonly;
        private final RootReadContractCatalog.Family<Selection,Result> family;
        private final RootDomainInstallation installation;
        private Runtime(RootRuntimeContext context,Sources sources,boolean privateSemanticReadonly){
            this.context=context;this.sources=sources;this.privateSemanticReadonly=privateSemanticReadonly;
            family=new RootReadContractCatalog.Family<>("army-observer-research-sampling-query-v1",Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(ArmyObserverSampling.CAPABILITY),sources.nativeDefinition(),sources.decoder(),ArmyObserverSampling::fields,selected->new OperationKey(ArmyObserverSampling.QUERY),selected->{
                StrictJson.require(selected.subjects().isEmpty(),"query cannot acquire scoped setter arguments");
                java.util.function.Function<PlanningReadReceipt,Result> decode=receipt->ArmyObserverSampling.verifyRead(receipt,selected,context.archive());
                return new ReadContract<>("java.army.observer-sampling."+selected.family().wire()+".v1",new OperationKey(ArmyObserverSampling.QUERY),Optional.of(ArmyObserverSampling.CAPABILITY),"army-observer-sampling-query-v1",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,sources.nativeDefinition(),(request,id)->prepareRead(request,selected),decode,decode)
                    .withOriginalHistoryProjection(DriverReadHistoryRichMaterial.Kind.ARMY_OBSERVER_SAMPLING,(receipt,replayed)->{
                        var internal=ArmyObserverSampling.driverResult(replayed,receipt.request().before(),receipt.before().binding().connectionGeneration());
                        var publicResult=ArmyObserverSampling.publicResult(replayed,receipt.request().before(),receipt.before().binding().connectionGeneration());
                        return new DriverReadHistoryRichMaterial.Projection(DriverReadHistoryRichMaterial.Kind.ARMY_OBSERVER_SAMPLING,internal,
                                DriverReadHistoryRichMaterial.PublicNumbers.fromResults(internal,publicResult),sources.refs());
                    });
            });
            var enable=action(true);var disable=action(false);
            installation=new RootDomainInstallation("driver-transport-original-seven/v1",List.of(),List.of(),List.of(family),List.of(enable,disable),List.of(),List.of(recorded(true),recorded(false)),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public RootDomainInstallation installation(){return installation;}
        public List<ExactRef> historySources(){return sources.refs();}
        public void requireContext(RootRuntimeContext actual)throws IOException {if(context!=actual)throw new IOException("transport product belongs to another actual per-Game context");}
        public RootRuntimeContext context(){return context;}
        public boolean privateSemanticReadonly(){return privateSemanticReadonly;}
        public RootExecutableBindings.ActionBinding enableAction(){return installation.actions().get(0);}
        public RootExecutableBindings.ActionBinding disableAction(){return installation.actions().get(1);}
        public ReadContract<Result> contract(Selection selected){return context.readCatalog().issue(family,selected.query());}
        private NativeRequest prepareRead(PlanningReadRequest request,Selection selected){
            try {StrictJson.require(ArmyObserverSampling.selection(request.arguments()).equals(selected.query()),"actual observer query selection changed");validateCurrent(request.before(),request.sessionId());return ArmyObserverSampling.request(ArmyObserverSampling.QUERY,selected.query());}
            catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private void validateCurrent(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,String session)throws IOException {
            var original=context.transport().latestObservedSnapshot().orElseThrow(()->new IOException("actual sampling snapshot absent"));
            StrictJson.require(original.session().sessionId().equals(session)&&session.equals(context.game().sessionId())&&before.game().equals(context.game().generation()),"sampling request crossed actual Game/session");
            ArmyObserverSampling.validate(before,original.session().connectionGeneration(),(NativeWire.Snapshot)NativeWire.decode(original.originalPacket()),context.transport().originalHello());
        }
        public ActionCommand prepare(ContinuityStorePort.Session same,Complete frame,boolean enable,Selection selected,java.math.BigInteger expected,Instant deadline)throws IOException {
            context.writer().requireSession(same);context.requireCurrent(deadline);requireFrame(frame);StrictJson.require(frame.identity().frame().revision().equals(expected),"sampling source revision changed");
            validateCurrent(frame.identity(),frame.sessionId());NativeRequest request=ArmyObserverSampling.request(enable?ArmyObserverSampling.ENABLE:ArmyObserverSampling.DISABLE,selected);
            OpportunityJson.Obj args=OpportunityJson.object(OpportunityJson.parse(request.additionalFields().bytes()),"observer sampling action arguments");
            String id="army-observer-control:"+UUID.randomUUID();var archive=context.archive().withSession(same);
            if(ContinuityActionJournal.lookup(same.head().state(),id,archive).isPresent())throw new IOException("original observer control intent exists; reconcile it without replay");
            var post=new ExpectedPostcondition(1,frame.identity(),frame.source(),ArmyObserverSampling.OBSERVER,ArmyObserverSampling.expected(enable,selected.family()));
            return new ActionCommand(id,frame.identity(),frame.source(),frame.sessionId(),new OperationKey(request.step()),args,post,new Claims(Set.of(),Set.of(),Set.of(frame.identity().frame().identity().player()),Set.of("army-observer-research-gates")),deadline);
        }
        private RootExecutableBindings.ActionBinding action(boolean enable){
            String step=enable?ArmyObserverSampling.ENABLE:ArmyObserverSampling.DISABLE;
            var effect=new NativeEffectRegistry.Binding(new OperationKey(step),sources.runtime(),command->{
                try {requireCommand(command,enable);validateCurrent(command.before(),command.sessionId());NativeRequest actual=ArmyObserverSampling.request(step,ArmyObserverSampling.selection(command.arguments()));return actual;}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            },(command,attempt,dispatch)->observe(command,attempt,dispatch,enable));
            return new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(ArmyObserverSampling.CAPABILITY),sources.decoder());
        }
        private NativeRecordedEvidenceVerifier.Binding recorded(boolean enable){return new NativeRecordedEvidenceVerifier.Binding(new OperationKey(enable?ArmyObserverSampling.ENABLE:ArmyObserverSampling.DISABLE),sources.runtime(),(head,receipt,archive)->{
            StrictJson.require(receipt.state() instanceof ActionState.Settled,"settled observer control required");var settled=(ActionState.Settled)receipt.state();StrictJson.require(settled.settlement() instanceof ActionState.ControlApplied,"observer sampling grants only ControlApplied");replay(receipt.command(),settled.attempt(),settled.dispatch(),(ActionState.ControlApplied)settled.settlement(),enable,archive);
        });}
        private NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,boolean enable){
            if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return NativeEffectRegistry.Projected.pending("original observer control unresolved; never replay",List.of(attempt.guard().nativeEvidence()));
            try {requireCommand(command,enable);var selection=ArmyObserverSampling.selection(command.arguments());ArmyObserverSampling.verifyAck(ack,command.operation().value(),selection,command.before());
                var original=ArmyObserverSampling.decode(ack.originalResultToken().orElseThrow(),command.operation().value(),selection);StrictJson.require(original.accepted(),"original observer setter returned incomplete; no retry");
                return context.withSession(same->{var identity=new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());return context.collector().currentOwned(same,identity,ActionObservationWindow.deadline(command),lease->{
                    var frame=lease.frame();requireFrame(frame);ArmyObserverSampling.sameFrame(command.before(),frame.identity());
                    var contract=contract(selection.query());var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),OpportunityJson.object(OpportunityJson.parse(ArmyObserverSampling.fields(selection.query()).bytes()),"observer independent query"),ActionObservationWindow.deadline(command));
                    var value=context.reads().read(same,contract,request);if(!(value instanceof PlanningReadResult.Known<Result> known))throw new IOException("actual independent observer query unavailable");
                    var control=new ActionState.ControlApplied(known.receipt(),ArmyObserverSampling.OBSERVER,ArmyObserverSampling.actual(enable,known.value()));
                    replay(command,attempt,ack,control,enable,context.archive().withSession(same));return new NativeEffectRegistry.Projected(new ActionPorts.ControlObserved(control),Optional.empty());
                });});
            }catch(IOException|IllegalArgumentException|IllegalStateException failure){return NativeEffectRegistry.Projected.pending("observer independent postcondition unresolved: "+failure.getMessage(),List.of(attempt.guard().nativeEvidence()));}
        }
        private void replay(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,ActionState.ControlApplied control,boolean enable,ActionPorts.OutcomeArchive archive){
            try {
                requireCommand(command,enable);StrictJson.require(dispatch instanceof NativeActionPort.AckReceived&&((NativeActionPort.AckReceived)dispatch).nativeOk(),"successful original observer setter ACK required");
                var ack=(NativeActionPort.AckReceived)dispatch;ack.custody().orElseThrow().verify(ack,attempt.guard());var selection=ArmyObserverSampling.selection(command.arguments());
                ArmyObserverSampling.verifyAck(ack,command.operation().value(),selection,command.before());
                StrictJson.require(ArmyObserverSampling.decode(ack.originalResultToken().orElseThrow(),command.operation().value(),selection).accepted(),"incomplete observer ACK cannot settle");
                NativeRecordedEvidenceVerifier.requireRead(control.read(),archive);NativeRequestChronology.requireSampledAfter(control.read(),attempt,ack);
                ArmyObserverSampling.sameFrame(command.before(),control.read().request().before());
                StrictJson.require(control.read().request().source().equals(command.source())&&control.read().request().sessionId().equals(command.sessionId())&&control.supportingReads().isEmpty(),"observer independent query source/session drift");
                Result actual=ArmyObserverSampling.verifyRead(control.read(),selection.query(),archive);
                StrictJson.require(control.observerSchema().equals(ArmyObserverSampling.OBSERVER)&&control.actual().equals(ArmyObserverSampling.actual(enable,actual)),"archived observer control postcondition changed");
                ActionEffects.validate(command,attempt,dispatch,control);
            }catch(IOException failure){throw new UncheckedIOException("archived observer original unavailable",failure);}
        }
        private record OriginalReturned(Result value,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,java.math.BigInteger generation) { }
        /** Public projection preserves an original incomplete return without releasing the canonical UNKNOWN. */
        public RawJson result(ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
            var actual=returned(receipt,archive);return ArmyObserverSampling.publicResult(actual.value(),actual.before(),actual.generation());
        }
        /** Legacy history is the complete internal numeric Driver result, distinct from the public decimal codec. */
        public RawJson driverResult(ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
            var actual=returned(receipt,archive);return ArmyObserverSampling.driverResult(actual.value(),actual.before(),actual.generation());
        }
        private OriginalReturned returned(ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
            boolean enable=receipt.command().operation().value().equals(ArmyObserverSampling.ENABLE);requireCommand(receipt.command(),enable);
            var selected=ArmyObserverSampling.selection(receipt.command().arguments());
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied control){
                replay(receipt.command(),settled.attempt(),settled.dispatch(),control,enable,archive);
                var ack=(NativeActionPort.AckReceived)settled.dispatch();
                return new OriginalReturned(ArmyObserverSampling.decode(ack.originalResultToken().orElseThrow(),receipt.command().operation().value(),selected),receipt.command().before(),settled.attempt().guard().connectionGeneration());
            }
            if(receipt.state() instanceof ActionState.Unknown unknown&&unknown.attempt().isPresent()&&unknown.dispatch().isPresent()
                    &&unknown.dispatch().orElseThrow() instanceof NativeActionPort.AckReceived ack&&ack.nativeOk()){
                var attempted=unknown.attempt().orElseThrow();
                var original=ArmyObserverSampling.incompleteOriginal(receipt.command(),attempted,ack);
                return new OriginalReturned(original,receipt.command().before(),attempted.guard().connectionGeneration());
            }
            throw new IOException("original observer control unresolved; canonical intent remains consumed");
        }
        private void requireCommand(ActionCommand command,boolean enable){StrictJson.require(command.source().equals(context.source())&&command.sessionId().equals(context.game().sessionId())&&command.before().game().equals(context.game().generation())&&command.before().machineId().equals(context.game().machineId())&&command.operation().value().equals(enable?ArmyObserverSampling.ENABLE:ArmyObserverSampling.DISABLE),"observer action crossed actual same-Game owner/operation");ArmyObserverSampling.request(command.operation().value(),ArmyObserverSampling.selection(command.arguments()));}
        private void requireFrame(Complete frame){StrictJson.require(frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId())&&frame.identity().game().equals(context.game().generation()),"observer frame crossed its actual per-Game context");}
    }

}
