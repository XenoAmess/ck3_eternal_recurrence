package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Route;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions.CoaUpload;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions.CoaSourceEffects;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions.NativeCoaClipboard;
import org.xar.ck3.control.application.effects.coa.NativeSourceObservation;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;

/** Installs only the six source methods in the shared CoA component owner. No second public registry or writer. */
public final class RootCoaUpload {
    private RootCoaUpload(){ }
    /** Called by the sole pre-Core CoA source-products composer against its actual selected index. */
    public static Prepared prepare(RootRuntimeSelectedSources actual,Duration timeout)throws IOException{
        Objects.requireNonNull(actual);ExactRef runtime=actual.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootCoaUpload.class);
        ExactRef helper=actual.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaUpload.class);
        ExactRef decoder=actual.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaCodec.class);
        for(Class<?> type:List.of(CoaData.class,CoaUploads.class,CoaSourceMaterials.class,
                org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.class,FrontendCoaCodec.class))
            actual.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,type);
        ExactRef completion=actual.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaSourceEffects.class);
        ExactRef clipboard=actual.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NativeCoaClipboard.class);
        ExactRef observation=actual.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,NativeSourceObservation.class);
        actual.requireCurrent();return new Prepared(new Sources(runtime,helper,decoder,completion,clipboard,observation,timeout));
    }
    public record Sources(ExactRef runtime,ExactRef helper,ExactRef decoder,ExactRef completion,ExactRef clipboard,ExactRef observation,Duration timeout){
        public Sources{for(ExactRef ref:List.of(runtime,helper,decoder,completion,clipboard,observation))need(ref.bytes()>0,"actual source refs required");Objects.requireNonNull(timeout);need(!timeout.isNegative()&&!timeout.isZero()&&timeout.compareTo(Duration.ofSeconds(60))<=0,"finite CoA action deadline required");}
    }
    public static final class Prepared implements RootFrontendCoaPublicProducts.ComponentPrepared {
        private final Sources sources;
        private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);}
        @Override public Set<Method> methods(){return CoaUpload.METHODS;}
        @Override public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        /** These two operations require their actually advertised capabilities; no private permission substitutes. */
        @Override public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException{
            Objects.requireNonNull(actual);if(core!=null&&core!=actual)throw new IOException("CoA upload belongs to another Core");core=actual;
        }
        @Override public synchronized RootFrontendCoaPublicProducts.ComponentInstalled install(RootRuntimeContext actual)throws IOException{
            Objects.requireNonNull(actual);if(core==null||actual.core()!=core)throw new IOException("CoA upload requires its identical pre-bound Core");
            Attempt old=attempts.get(actual);if(old!=null){if(old.value!=null)return old.value;throw new IOException("partial CoA upload installation cannot be replayed",old.failure);}
            if(attempts.size()>=64)throw new IOException("CoA upload finite per-Game installation bound exhausted");
            Attempt attempt=new Attempt();attempts.put(actual,attempt);
            try{
                for(Class<?> type:List.of(RootCoaUpload.class,CoaUpload.class,CoaData.class,CoaCodec.class,CoaUploads.class,CoaSourceMaterials.class,CoaSourceEffects.class,NativeCoaClipboard.class,NativeSourceObservation.class))actual.game().launchPlan().sources().requireLoadedClass(type);
                Runtime runtime=new Runtime(actual,sources);
                attempt.value=new RootFrontendCoaPublicProducts.ComponentInstalled(runtime.installation,new CoaUpload(new CoaUploads(),runtime));return attempt.value;
            }catch(IOException|RuntimeException failure){attempt.failure=failure instanceof IOException io?io:new IOException("CoA actual upload installation failed",failure);throw attempt.failure;}
        }
        private static final class Attempt{RootFrontendCoaPublicProducts.ComponentInstalled value;IOException failure;}
    }
    /** Same actual context and source archive throughout Menu, adopted Gameplay, and cold receipt reads. */
    private static final class Runtime implements CoaUpload.Runtime {
        private final RootRuntimeContext context;
        private final Sources sources;
        private final CoaSourceMaterials materials;
        private final CoaUpload.Preparation preparation;
        private final CoaSourceEffects effects;
        private final RootDomainInstallation installation;
        Runtime(RootRuntimeContext actual,Sources sources){
            context=actual;this.sources=sources;materials=new CoaSourceMaterials(context.archive());
            preparation=new CoaUpload.Preparation(sources.helper(),materials,this::requireOrigin,()->{
                try{return context.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            var clipboard=new NativeCoaClipboard(context.clock());
            effects=new CoaSourceEffects(materials,context.archive(),this::sourceScope,clipboard::read,
                    (ref,maximum)->context.withSession(same->context.originals().read(same,ref,maximum)),
                    List.of(sources.runtime(),sources.helper(),sources.decoder(),sources.completion(),sources.clipboard(),sources.observation()));
            var actions=new ArrayList<RootExecutableBindings.ActionBinding>();var archived=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();var routes=new ArrayList<FrontendRouteAdmission>();
            for(String step:List.of(PROBE_STEP,EXPORT_STEP)){
                OperationKey operation=new OperationKey(step);
                var effect=new NativeEffectRegistry.Binding(operation,sources.helper(),preparation,effects);
                actions.add(RootExecutableBindings.ActionBinding.coaSource(effect,sources.decoder(),preparation));
                archived.add(new NativeRecordedEvidenceVerifier.Binding(operation,sources.helper(),(head,receipt,archive)->effects.replay(receipt,archive)));
                // The original native method may return factual UNAVAILABLE outside its visible designer.
                // Source admission does not invent a target or add a public planner policy.
                Set<Route> observedRoutes=Set.of(Route.MAIN_MENU,Route.BOOKMARKS,Route.LOBBY,Route.RULER_DESIGNER,Route.COAT_OF_ARMS_DESIGNER);
                routes.add(new FrontendRouteAdmission(operation,observedRoutes,FrontendRouteAdmission.FrameMode.MENU,sources.helper()));
                routes.add(new FrontendRouteAdmission(operation,observedRoutes,FrontendRouteAdmission.FrameMode.SNAPSHOT,sources.helper()));
            }
            Set<OperationKey> operations=actions.stream().map(a->a.effect().operation()).collect(java.util.stream.Collectors.toUnmodifiableSet());
            var once=new RootDomainIntentPreparation.Binding("coa-original-source-binding/v1",sources.helper(),c->operations.contains(c.operation()),(same,command)->{
                try{requireOrigin(same,command);}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            installation=new RootDomainInstallation("coa-original-source-upload6",List.of(),List.of(),List.of(),actions,List.of(),archived,List.of(),List.of(),routes,List.of(once),operations,List.of(),List.of(),List.of(),List.of(),List.of());
        }
        private Instant deadline(){return context.clock().instant().plus(sources.timeout());}
        private CoaSourceEffects.Scope sourceScope(ActionCommand command,ActionState.Attempt attempt)throws IOException{
            Instant until=ActionObservationWindow.deadline(command);
            return context.withSession(same->{
                if(command.origin() instanceof CommandOrigin.Frontend front){
                    var mode=front.identity().frame() instanceof FrontendFrame.Menu?FrontendRouteAdmission.FrameMode.MENU:FrontendRouteAdmission.FrameMode.SNAPSHOT;
                    return context.frontend().withSourceBoundFrontendRead(same,mode,until,lease->{
                        need(lease.source().equals(command.source())&&lease.identity().sameSession(front.identity()),"independent CoA after scope changed actual Frontend source/session");
                        // FOS frontend_host10 is the sole producer of this exact roster: source qualification first;
                        // SNAPSHOT additionally retains its original manifest, Driver and Native snapshot.
                        need(!lease.supportingEvidence().isEmpty(),"actual frontend source qualification missing");
                        var support=new java.util.LinkedHashSet<ExactRef>(lease.supportingEvidence());support.add(lease.originalHeartbeat());
                        return new CoaSourceEffects.Scope(CoaSourceMaterials.bindingOf(new CommandOrigin.Frontend(lease.identity()),command.sessionId()),Optional.of(lease.identity().frame().querySequence()),lease.identity().nativeEvidence(),lease.identity().capabilityEvidence(),lease.supportingEvidence().getFirst(),context.clock().instant(),lease.validUntil(),List.copyOf(support));
                    });
                }
                return context.collector().current(same,command.before(),until,lease->{
                    need(lease.frame().source().equals(command.source())&&lease.frame().sessionId().equals(command.sessionId()),"independent CoA after scope changed actual Gameplay source/session");
                    var support=new java.util.LinkedHashSet<ExactRef>(lease.semantic().references());support.add(lease.frame().originalEvidence());support.add(lease.originalHeartbeat());
                    return new CoaSourceEffects.Scope(gameplayBinding(lease.frame()),Optional.empty(),lease.semantic().originalNativePacket(),lease.originalHello(),lease.originalSourceQualification(),context.clock().instant(),lease.validUntil(),List.copyOf(support));
                });
            });
        }
        private RootMenuSession menu()throws IOException{return context.core().requireFrontendMenu(context);}
        private NativeWire.Hello hello(String capability,BigInteger generation)throws IOException{
            NativeWire.Hello received=context.transport().originalHello();
            NativeWire.Frame parsed=NativeWire.decode(received.packet().value());
            need(parsed instanceof NativeWire.Hello,"actual complete native HELLO required");NativeWire.Hello actual=(NativeWire.Hello)parsed;
            need(actual.pid()==received.pid()&&actual.connectionGeneration().equals(received.connectionGeneration())&&actual.capabilities().equals(received.capabilities())
                    &&actual.gameSha256().equals(received.gameSha256())&&actual.adapterId().equals(received.adapterId())&&actual.adapterStatus().equals(received.adapterStatus())&&actual.buildMatch()==received.buildMatch()
                    &&actual.pid()==context.game().generation().pid()&&actual.connectionGeneration().equals(generation)
                    &&actual.gameSha256().equalsIgnoreCase(EXE_SHA256)&&actual.adapterId().equals(ADAPTER_ID)&&actual.adapterStatus().equals("ready")&&actual.buildMatch()
                    &&actual.capabilities().contains(capability),"CoA current original HELLO/build/process/generation/capability unavailable");
            return actual;
        }
        @Override public Binding current(BigInteger revision,String capability)throws IOException,InterruptedException{
            Instant until=deadline();context.requireCurrent(until);
            if(menu().publicPhase()==RootMenuSession.PublicPhase.FRONTEND){
                var mode=revision.signum()==0?FrontendRouteAdmission.FrameMode.MENU:FrontendRouteAdmission.FrameMode.SNAPSHOT;
                return context.withSession(same->context.frontend().withSourceBoundFrontendRead(same,mode,until,lease->{
                    need(lease.source().equals(context.source())&&lease.bridgeCapabilities().contains(capability),"frontend CoA requires its actual source and advertised capability");
                    hello(capability,lease.identity().connectionGeneration());Binding actual=CoaSourceMaterials.bindingOf(new CommandOrigin.Frontend(lease.identity()),context.game().sessionId());
                    need(actual.revision().equals(revision),"frontend CoA expected revision differs from original Menu/snapshot");return actual;
                }));
            }
            return context.core().sessionAccess().withCurrent(root->{requireRoot(root);return root.withPublicObservation(until,(frame,known,same)->{
                context.collector().requireHeldFrame(same,frame);need(frame.identity().frame().revision().equals(revision),"CoA public expected revision differs from actual held frame");
                hello(capability,frame.connectionGeneration());return gameplayBinding(frame);
            });});
        }
        private Binding gameplayBinding(Complete frame){
            var value=frame.identity().frame();return new SnapshotBinding(SnapshotMode.GAMEPLAY,value.snapshotId(),value.revision(),value.identity().nativeRevision(),value.identity().dateRaw().longValueExact(),Optional.of(value.episodeRunId()),frame.connectionGeneration(),context.game().generation().pid());
        }
        private void requireRoot(RootApplicationSession actual){need(context.actions()==actual&&actual.identity().game().equals(context.game().generation())&&actual.identity().sessionId().equals(context.game().sessionId()),"CoA public operation crossed its identical installed Root action owner");}
        private void requireOrigin(Session same,ActionCommand command)throws IOException{
            context.writer().requireSession(same);context.requireCurrent(command.deadline());
            need(command.source().equals(context.source())&&command.sessionId().equals(context.game().sessionId())&&command.origin().game().equals(context.game().generation()),"CoA preparation crossed its actual source/session/physical Game");
            Binding binding;
            if(command.origin() instanceof CommandOrigin.Frontend){
                need(menu().publicPhase()==RootMenuSession.PublicPhase.FRONTEND,"retired Menu cannot dispatch after gameplay admission");binding=CoaSourceMaterials.bindingOf(command.origin(),command.sessionId());
            }else{
                requireRoot(context.core().currentForAccess());
                var row=FrontendCoaCodec.object(FrontendCoaCodec.raw(OpportunityJson.toNode(command.arguments())));
                if(command.operation().value().equals(PROBE_STEP))binding=CoaCodec.binding(FrontendCoaCodec.raw(row.get("binding")));
                else {
                    var before=command.before().frame();
                    binding=new SnapshotBinding(SnapshotMode.GAMEPLAY,before.snapshotId(),before.revision(),before.identity().nativeRevision(),before.identity().dateRaw().longValueExact(),Optional.of(before.episodeRunId()),expectedGeneration(command),context.game().generation().pid());
                }
            }
            CoaSourceMaterials.requireOrigin(command.origin(),binding);hello(CoaUpload.capability(command.operation().value()),binding.connectionGeneration());
            need(command.expectation().source().equals(context.source())&&binding.connectionGeneration().equals(expectedGeneration(command)),"CoA expectation differs from actual source or original connection");
            String observer=command.expectation() instanceof CommandExpectation.Frontend f?f.expected().observerSchema():command.expectation().requireGameplay().observerSchema();
            need(observer.equals(CoaUpload.EXPECTATION),"CoA source command changed its original observer schema");
        }
        private ActionCommand command(CommandOrigin origin,Binding binding,String step,EncodedSource source,boolean large,boolean apply,Instant until){
            OpportunityJson.Obj args=new OpportunityJson.Obj(java.util.Map.of());
            if(source!=null)args=CoaSourceMaterials.arguments(materials.preserve(source,binding,origin,context.game().sessionId(),large),apply);
            List<ExpectedValue> fields=List.of(new ExpectedBoolean(new FieldKey("independent_game_effect_proven"),false),new ExpectedText(new FieldKey("original_connection_generation"),binding.connectionGeneration().toString()));
            CommandExpectation expectation=origin instanceof CommandOrigin.Frontend front
                    ?new CommandExpectation.Frontend(new FrontendExpectedPostcondition(front.identity(),context.source(),CoaUpload.EXPECTATION,fields))
                    :new CommandExpectation.Gameplay(new ExpectedPostcondition(1,origin.requireGameplay(),context.source(),CoaUpload.EXPECTATION,fields));
            return new ActionCommand("public-coa-"+UUID.randomUUID(),origin,context.source(),context.game().sessionId(),new OperationKey(step),args,expectation,new Claims(Set.of(),Set.of(),Set.of(),Set.of()),until);
        }
        private static List<ExpectedValue> expectedValues(ActionCommand command){return command.expectation() instanceof CommandExpectation.Frontend f?f.expected().values():command.expectation().requireGameplay().values();}
        private static BigInteger expectedGeneration(ActionCommand command){
            var values=expectedValues(command);need(values.size()==2&&values.get(0) instanceof ExpectedBoolean&&values.get(0).field().value().equals("independent_game_effect_proven")&&!((ExpectedBoolean)values.get(0)).value()
                    &&values.get(1) instanceof ExpectedText&&values.get(1).field().value().equals("original_connection_generation"),"CoA original finite expectation profile changed");
            String value=((ExpectedText)values.get(1)).value();need(value.matches("[1-9][0-9]{0,19}"),"canonical original connection generation required");return u64(new BigInteger(value),true);
        }
        private ActionReceipt execute(Binding binding,String step,EncodedSource source,boolean large,boolean apply)throws IOException,InterruptedException{
            Instant until=deadline();
            if(binding instanceof FrontendBinding||binding instanceof SnapshotBinding snapshot&&snapshot.mode()==SnapshotMode.FRONTEND_SNAPSHOT){
                var mode=binding instanceof FrontendBinding?FrontendRouteAdmission.FrameMode.MENU:FrontendRouteAdmission.FrameMode.SNAPSHOT;
                ActionCommand command=context.withSession(same->context.frontend().withSourceBoundFrontendRead(same,mode,until,lease->{var origin=new CommandOrigin.Frontend(lease.identity());
                    need(CoaSourceMaterials.bindingOf(origin,context.game().sessionId()).equals(binding),"CoA source crossed the original frontend binding before prepare");
                    return command(origin,binding,step,source,large,apply,until);
                }));
                // No read-only frontend scope is retained across mutation; the original menu owns dispatch.
                return menu().execute(command);
            }
            return context.core().sessionAccess().withCurrent(root->{requireRoot(root);return root.executePublicDecision(until,(frame,known,same)->{
                need(gameplayBinding(frame).equals(binding),"CoA source crossed the original complete Gameplay binding before prepare");
                ActionCommand command=command(new CommandOrigin.Gameplay(frame.identity()),binding,step,source,large,apply,until);
                return new RootApplicationSession.SubmitPublicAction<ActionReceipt>(command);
            },(receipt,archive,same)->receipt);});
        }
        private RawJson token(ActionReceipt receipt)throws IOException{
            need(receipt.state() instanceof ActionState.Settled&&((ActionState.Settled)receipt.state()).settlement() instanceof ActionState.NativeSourceCompleted,"CoA native source completion remains unresolved; retain the original action and never resend");
            return context.withSession(same->{effects.replay(receipt,context.archive().withSession(same));
                var settled=(ActionState.Settled)receipt.state();need(settled.dispatch() instanceof NativeActionPort.AckReceived,"CoA completed source lost its original dispatch");
                return ((NativeActionPort.AckReceived)settled.dispatch()).originalResultToken().orElseThrow(()->new IllegalStateException("CoA original native token missing"));});
        }
        @Override public ProbeResult probe(EncodedSource source,Binding binding,boolean large,boolean apply)throws IOException,InterruptedException{
            ActionReceipt receipt=execute(binding,PROBE_STEP,source,large,apply);return CoaCodec.nativeProbe(token(receipt),source,binding,apply);
        }
        @Override public ExportResult export(Binding binding)throws IOException,InterruptedException{
            ActionReceipt receipt=execute(binding,EXPORT_STEP,null,false,false);return CoaCodec.nativeExport(token(receipt),binding);
        }
    }
}
