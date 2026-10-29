package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
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
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;

/** One concrete per-Root producer for the five original frontend designer methods. */
public final class RootCoaDesigner {
    private RootCoaDesigner() { }
    private static final int MAXIMUM_SOURCE_FILE_BYTES=4<<20;
    public static final Set<Method> METHODS=Set.of(Method.ACTIVATE,Method.CUSTOM,Method.COMMIT_DYNASTY,Method.GRID,Method.TREE);
    public static Prepared prepare(RootRuntimeDefinitions.Inputs actual)throws IOException { return new Prepared(actual); }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs actual,RootRuntimeSelectedSources sameSelected)throws IOException { return new Prepared(actual,sameSelected); }
    public static final class Prepared implements RootFrontendCoaPublicProducts.ComponentPrepared {
        private final ExactRef originalDriver,implementation,decoder;
        private final List<ExactRef> sources;
        private final CoaDesigner.ReadDefinitions reads;
        private final Duration observationTimeout,actionTimeout;
        private final RootRuntimeSelectedSources selected;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        public Prepared(RootRuntimeDefinitions.Inputs actual)throws IOException { this(actual,new RootRuntimeSelectedSources(actual)); }
        public Prepared(RootRuntimeDefinitions.Inputs actual,RootRuntimeSelectedSources sameSelected)throws IOException {
            Objects.requireNonNull(actual);selected=Objects.requireNonNull(sameSelected);
            originalDriver=original(selected,actual.source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER));
            Path driver=Path.of(originalDriver.path()).toAbsolutePath().normalize();
            need(driver.getFileName().toString().equals("native_driver.py")&&driver.getParent().getFileName().toString().equals("bridge"),"original native driver source required");
            requireSame(originalDriver);var bridge=driver.getParent();var closure=new ArrayList<ExactRef>();
            closure.add(originalDriver);closure.add(original(selected,source(bridge.resolve("frontend_gui_route_contract.py"))));
            closure.add(original(selected,source(bridge.resolve("service.py"))));closure.add(original(selected,source(bridge.resolve("mcp_server.py"))));
            implementation=selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaDesigner.class);
            decoder=selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaCodec.class);
            closure.add(implementation);closure.add(decoder);
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaPostconditions.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaData.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,FrontendCoaContract.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,FrontendCoaCodec.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,FrontendCoaService.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootCoaDesigner.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootFrontendCoaPublicProducts.class));
            sources=List.copyOf(closure);for(ExactRef source:sources)need(source.bytes()>0&&source.bytes()<=MAXIMUM_SOURCE_FILE_BYTES,"bounded exact designer source file required");
            reads=CoaDesigner.readDefinitions(originalDriver);
            observationTimeout=Duration.ofMillis(actual.configuration().publicCatalog().observationTimeoutMs());
            actionTimeout=Duration.ofMillis(actual.configuration().publicCatalog().autoTimeoutMs());
            need(!observationTimeout.isNegative()&&!observationTimeout.isZero()&&observationTimeout.compareTo(Duration.ofMinutes(2))<=0
                    &&!actionTimeout.isNegative()&&!actionTimeout.isZero()&&actionTimeout.compareTo(Duration.ofMinutes(30))<=0,"finite original public designer timeouts required");
        }
        public CoaDesigner.ReadDefinitions coaReads() { return reads; }
        @Override public Set<Method> methods() { return METHODS; }
        @Override public List<DomainBodies.Registration> domainRegistrations() { return List.of(); }
        @Override public List<NativePrivateActionPermission> privatePermissions() { return List.of(); }
        @Override public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException {
            Objects.requireNonNull(same);if(core!=null&&core!=same)throw new IOException("designer component already belongs to another actual Core");core=same;
        }
        @Override public synchronized RootFrontendCoaPublicProducts.ComponentInstalled install(RootRuntimeContext same)throws IOException {
            Objects.requireNonNull(same);if(core==null||same.core()!=core)throw new IOException("designer component requires its identical pre-bound Core");
            Attempt prior=attempts.get(same);if(prior!=null){if(prior.installed!=null)return prior.installed;throw new IOException("partial designer installation is not replayed",prior.failure);}
            if(attempts.size()>=64)throw new IOException("designer actual context installation bound exhausted");
            var attempt=new Attempt();attempts.put(same,attempt);
            try {
                selected.requireLoadedClasses(same.game().launchPlan());
                for(ExactRef source:sources)requireSame(source);
                var shared=same.frontend().rules().definitions();
                need(shared.originalDriverSource().equals(originalDriver),"designer and existing frontend definitions use different original driver sources");
                var definitions=new CoaDesigner.Definitions(shared.route(),shared.tree(),reads);
                var designer=new CoaDesigner(definitions,same.reads(),same.archive(),
                        (verified,ack)->FrontendCoaCodec.encode(FrontendCoaCodec.designer(verified,ack)));
                var actions=designer.bindings(implementation).stream().map(binding->new RootExecutableBindings.ActionBinding(binding,
                        ReadContract.GuardMode.FRONTEND_SESSION,Optional.of("game.command."+binding.operation().value()),decoder)).toList();
                var admissions=new ArrayList<FrontendRouteAdmission>();
                admissions.add(new FrontendRouteAdmission(reads.tree().operation(),Set.of(FrontendRulesData.Route.MAIN_MENU,FrontendRulesData.Route.BOOKMARKS,
                        FrontendRulesData.Route.LOBBY,FrontendRulesData.Route.RULER_DESIGNER,FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER),FrontendRouteAdmission.FrameMode.MENU,implementation));
                admissions.add(new FrontendRouteAdmission(reads.grid().operation(),Set.of(FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER),FrontendRouteAdmission.FrameMode.MENU,implementation));
                for(var action:CoaPostconditions.DesignerAction.values())admissions.add(new FrontendRouteAdmission(new OperationKey(action.step()),
                        Set.of(action.beforeRoute()),FrontendRouteAdmission.FrameMode.MENU,implementation));
                var installation=new RootDomainInstallation("original-five-coa-designer-methods/v1",List.of(),
                        List.of(new RootReadContractCatalog.InstalledRead(reads.tree(),decoder),new RootReadContractCatalog.InstalledRead(reads.grid(),decoder)),
                        List.of(),actions,List.of(),designer.archivedVerifiers(implementation),List.of(),List.of(),admissions,List.of(),Set.of(),
                        List.of(),List.of(),List.of(),List.of(),List.of());
                var runtime=new Runtime(same,designer,sources,selected,observationTimeout,actionTimeout);
                attempt.installed=new RootFrontendCoaPublicProducts.ComponentInstalled(installation,runtime);return attempt.installed;
            } catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("actual designer installation failed",failure);throw attempt.failure;}
        }
    }
    private static final class Attempt {RootFrontendCoaPublicProducts.ComponentInstalled installed;IOException failure;}
    private static final class Runtime implements FrontendCoaService.NativeAccess {
        private final RootRuntimeContext context;private final CoaDesigner designer;private final List<ExactRef> sources;
        private final RootRuntimeSelectedSources selected;
        private final Duration observationTimeout,actionTimeout;
        private Runtime(RootRuntimeContext same,CoaDesigner designer,List<ExactRef> sources,RootRuntimeSelectedSources selected,Duration observationTimeout,Duration actionTimeout) {
            context=same;this.designer=designer;this.sources=sources;this.selected=selected;this.observationTimeout=observationTimeout;this.actionTimeout=actionTimeout;
        }
        @Override public Response execute(Request request)throws IOException {
            Objects.requireNonNull(request);need(request instanceof Empty&&METHODS.contains(request.method()),"designer component accepts only its five exact empty requests");
            boolean mutation=request.method()!=Method.TREE&&request.method()!=Method.GRID;
            Instant now=context.clock().instant();Instant deadline=now.plus(mutation?actionTimeout:observationTimeout);
            Instant review=context.core().configuration().reviewAt();if(review.isBefore(deadline))deadline=review;
            if(!now.isBefore(deadline))throw new IOException("actual designer source review/deadline has expired");
            final Instant until=deadline;context.requireCurrent(until);
            RootMenuSession menu=context.core().requireFrontendMenu(context);
            need(menu.frontend==context.frontend().authority()&&menu.bindings==context.bindings()
                    &&menu.publicPhase()==RootMenuSession.PublicPhase.FRONTEND,"designer invocation crossed its exact current Menu/Root inventory");
            if(!mutation)return context.withSession(same->context.frontend().withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,until,lease->{
                verifySources(same);requireLease(lease);
                var contract=request.method()==Method.TREE?designer.definitions().tree():designer.definitions().grid();
                var known=known(menu.read(contract,request(lease.identity(),contract.operation(),until)));
                requireOriginal(same,known);return FrontendCoaCodec.response(FrontendCoaCodec.tree(known.value()));
            }));
            var action=switch(request.method()) {
                case ACTIVATE->CoaPostconditions.DesignerAction.OPEN;
                case CUSTOM->CoaPostconditions.DesignerAction.CUSTOM_MODE;
                case COMMIT_DYNASTY->CoaPostconditions.DesignerAction.COMMIT;
                default->throw new IllegalArgumentException("foreign designer mutation");
            };
            // Only precondition reads are scoped. The scope and original writer close before the sole canonical execute.
            ActionCommand command=context.withSession(same->context.frontend().withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,until,lease->{
                verifySources(same);requireLease(lease);
                var before=known(menu.read(designer.definitions().route(),request(lease.identity(),designer.definitions().route().operation(),until)));
                requireOriginal(same,before);PlanningReadResult.Known<?> tree;
                if(action==CoaPostconditions.DesignerAction.CUSTOM_MODE)tree=known(menu.read(designer.definitions().tree(),request(lease.identity(),designer.definitions().tree().operation(),until)));
                else tree=known(menu.read(designer.definitions().rulerTree(),request(lease.identity(),designer.definitions().rulerTree().operation(),until)));
                requireOriginal(same,tree);
                return designer.command("coa-designer-"+UUID.randomUUID().toString().replace("-",""),action,before,tree,until);
            }));
            context.frontend().authority().requireOutsideSourceBoundFrontendRead();
            ActionReceipt receipt=menu.execute(command);
            if(!(receipt.state() instanceof ActionState.Settled settled)||!(settled.settlement() instanceof ActionState.FrontendApplied))
                throw new IOException("canonical designer action remains unresolved; no replay; action_id="+receipt.command().actionId());
            return context.withSession(same->{
                verifySources(same);
                context.core().actions().withFrozen(same,lease->{need(lease.find(command.actionId()).filter(receipt::equals).isPresent(),"designer result is not its actual canonical receipt");lease.assertCurrent();return null;});
                var archive=context.archive().withSession(same);var ref=archive.preserveReceipt(receipt);
                need(receipt.equals(archive.loadReceipt(ref)),"designer original canonical archive read-back changed");
                return new Response(designer.publicResult(receipt,archive));
            });
        }
        private void requireLease(org.xar.ck3.control.application.effects.FrontendAuthority.LeaseSnapshot lease) {
            need(lease.source().equals(context.source())&&lease.identity().game().equals(context.game().generation())
                    &&lease.identity().frontendSessionId().equals(context.game().sessionId())&&lease.identity().frame() instanceof FrontendFrame.Menu,
                    "designer read crossed actual source/Game/session/Menu origin");
        }
        private PlanningReadRequest request(FrontendIdentity actual,OperationKey operation,Instant deadline) {
            return new PlanningReadRequest(new CommandOrigin.Frontend(actual),context.source(),context.game().sessionId(),operation,
                    new OpportunityJson.Obj(java.util.Map.of()),deadline);
        }
        private void verifySources(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException {
            selected.requireLoadedClasses(context.game().launchPlan());
            context.writer().requireSession(same);
            for(ExactRef source:sources){
                need(source.bytes()>0&&source.bytes()<=MAXIMUM_SOURCE_FILE_BYTES,"designer source file exceeds its separate physical pin budget");
                var pin=same.capturePin(source,Math.toIntExact(source.bytes()));same.verifyPin(pin);
            }
        }
        private void requireOriginal(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,PlanningReadResult.Known<?> known) {
            var archive=context.archive().withSession(same);need(archive.readReferenceOf(known.receipt()).equals(known.originalReceipt())
                    &&archive.loadRead(known.originalReceipt()).equals(known.receipt()),"designer read lost its actual original receipt");
        }
        private static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> result)throws IOException {
            if(result instanceof PlanningReadResult.Known<T> known)return known;
            throw new IOException("actual independent designer read unavailable: "+((PlanningReadResult.Unavailable<T>)result).reason());
        }
    }
    private static ExactRef source(Path path)throws IOException {
        var actual=SharedSourceFiles.observe(path);SharedSourceFiles.assertUnchanged(actual);var ref=actual.source();
        return new ExactRef(ref.path(),ref.bytes(),ref.sha256());
    }
    private static ExactRef original(RootRuntimeSelectedSources selected,ExactRef source)throws IOException {
        return selected.original(new FileRef(source.path(),source.bytes(),source.sha256()),RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON);
    }
    private static void requireSame(ExactRef ref)throws IOException {
        var actual=SharedSourceFiles.observe(Path.of(ref.path()));SharedSourceFiles.assertUnchanged(actual);
        var found=actual.source();
        if(!new ExactRef(found.path(),found.bytes(),found.sha256()).equals(ref))throw new IOException("original designer source changed: "+ref.path());
    }
    private static void need(boolean condition,String reason) { StrictJson.require(condition,reason); }
}
