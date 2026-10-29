package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.FrontendAuthority;
import org.xar.ck3.control.application.effects.RootFrontendGuardEvidence;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome;
import org.xar.ck3.control.contracts.presentation.TransportKind;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaFramebufferExtension;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;

/** Actual Root framebuffer component. Image DATA alone never grants a current frontend or presentation lease. */
public final class RootCoaFramebuffer {
    private RootCoaFramebuffer() { }
    public static final OperationKey PREPARE_OPERATION=new OperationKey("prepare-frontend-coat-of-arms-framebuffer-v1");
    private static final String EXPECTATION="xar.java-coa-foreground-postcondition/v1";
    private static final String SOURCES="xar.java-coa-window-capture-source-closure/v1",OBSERVATION="xar.java-coa-window-capture-independent-observation/v1";
    public static final class Prepared implements RootFrontendCoaPublicProducts.ComponentPrepared {
        private final CoaDesigner.ReadDefinitions reads;
        private final ExactRef originalDriver;
        private final List<ExactRef> sources;
        private final Duration timeout;
        private final RootRuntimeSelectedSources selected;
        private final List<PhysicalActionRegistry.Binding> physical;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        /** Identical definitions from the actual designer component; no second tree/grid observer is installed. */
        public Prepared(RootRuntimeDefinitions.Inputs actual,CoaDesigner.ReadDefinitions sameDesignerReads)throws IOException {
            this(actual,new RootRuntimeSelectedSources(actual),sameDesignerReads);
        }
        /** Production source assembly shares one qualified selector with the other actual frontend components. */
        public Prepared(RootRuntimeDefinitions.Inputs actual,RootRuntimeSelectedSources selected,CoaDesigner.ReadDefinitions sameDesignerReads)throws IOException {
            Objects.requireNonNull(actual);reads=Objects.requireNonNull(sameDesignerReads);
            this.selected=Objects.requireNonNull(selected);selected.requireInputs(actual);
            originalDriver=original(selected,actual.source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER));
            Path driver=Path.of(originalDriver.path()).toAbsolutePath().normalize();
            need(driver.getFileName().toString().equals("native_driver.py")&&driver.getParent().getFileName().toString().equals("bridge"),"original frontend driver source required");
            requireSame(originalDriver);var closure=new ArrayList<ExactRef>();closure.add(originalDriver);
            var originalFramebuffer=original(selected,source(driver.resolveSibling("coat_of_arms_framebuffer.py")));
            need(originalFramebuffer.bytes()==57331&&originalFramebuffer.sha256().equals("abc75bfc0e2aeee9dfc7dcfcb29e0f7b9932f4b53f969069d8187fc6ebca31d0"),"unreviewed original framebuffer algorithm source");
            closure.add(originalFramebuffer);
            closure.add(original(selected,source(driver.resolveSibling("service.py"))));
            var originalWindow=original(selected,source(driver.getParent().getParent().resolve("vision/window.py")));
            need(originalWindow.bytes()==56367&&originalWindow.sha256().equals("1af3e4ad6190c3a3fc941a9b57b3ada022046aacfaf3a550f8989500a0c73f2e"),"unreviewed original window identity source");closure.add(originalWindow);
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaFramebuffer.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaCalibrations.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaWindowCapture.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaFramebufferExtension.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaPostconditions.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaData.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,CoaDesigner.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,FrontendRulesCodec.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,FrontendCoaCodec.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootCoaFramebuffer.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,RootFrontendGuardEvidence.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,PhysicalActionRegistry.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,FrontendWindowCapturePermit.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.CONTRACTS,FrontendWindowCaptureRequest.class));
            closure.add(selected.javaSource(RootRuntimeSelectedSources.Module.CONTRACTS,FrontendWindowCaptureOutcome.class));
            sources=List.copyOf(closure);for(var source:sources)need(source.bytes()>0&&source.bytes()<=4*1024*1024,"bounded actual source-file material required");
            physical=List.of(new PhysicalActionRegistry.Binding(PREPARE_OPERATION,TransportKind.WIN32_FRONTEND_CAPTURE,sources,new PhysicalActionRegistry.Producer(){
                public GuardEvidence guard(WriterContracts.Head head,ActionCommand command)throws IOException{return runtime(command).guard(head,command);}
                public PreparedAction prepare(ContinuityStorePort.Session same,ActionCommand command,String id)throws IOException{return runtime(command).preparePhysical(same,command,id);}
                public PhysicalOutcome post(PhysicalSubmission permit,PreparedAction exact,Instant deadline)throws IOException{
                    if(!(exact instanceof PreparedAction.WindowCaptureRequest window))throw new IOException("foreign prepared physical plane");
                    return runtime(window.value()).post(permit,window,deadline);
                }
                public PhysicalActionRegistry.Observation observe(ContinuityStorePort.Session same,ActionCommand command,PhysicalActionState original,Instant deadline)throws IOException{return runtime(command).observePhysical(same,command,original,deadline);}
                public void verifyArchived(WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException{installedDecoder().verifyArchived(head,receipt,archive);}
            }));
            timeout=Duration.ofMillis(actual.configuration().publicCatalog().observationTimeoutMs());
            need(!timeout.isNegative()&&!timeout.isZero()&&timeout.compareTo(Duration.ofMinutes(2))<=0,"finite framebuffer observation deadline required");
        }
        @Override public Set<Method> methods(){return CoaFramebufferExtension.METHODS;}
        @Override public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        @Override public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public List<PhysicalActionRegistry.Binding> physicalBindings(){return physical;}
        private synchronized Runtime runtime(ActionCommand command)throws IOException {
            if(!(command.origin() instanceof CommandOrigin.Frontend frontend)||!command.operation().equals(PREPARE_OPERATION))throw new IOException("foreign physical frontend command");
            Runtime found=null;for(var attempt:attempts.values())if(attempt.installed!=null&&attempt.installed.service() instanceof Runtime actual
                    &&actual.context.game().generation().equals(frontend.identity().game())&&actual.context.game().sessionId().equals(command.sessionId())&&actual.context.source().equals(command.source())&&active(actual)){
                if(found!=null&&found!=actual)throw new IOException("ambiguous actual frontend context");found=actual;
            }
            if(found==null)throw new IOException("same Core/context framebuffer producer is not installed");return found;
        }
        private synchronized Runtime runtime(FrontendWindowCaptureRequest request)throws IOException {
            Runtime found=null;for(var attempt:attempts.values())if(attempt.installed!=null&&attempt.installed.service() instanceof Runtime actual
                    &&actual.context.game().generation().pid()==request.owner().processId()
                    &&actual.context.game().generation().creationFiletime().value().toString().equals(request.owner().processBirthFiletime())
                    &&actual.context.game().sessionId().equals(request.owner().sessionId())&&actual.context.game().machineId().equals(request.owner().machineId())&&active(actual)){
                if(found!=null&&found!=actual)throw new IOException("ambiguous actual WindowCapture context");found=actual;
            }if(found==null)throw new IOException("actual WindowCapture context is unavailable");return found;
        }
        private synchronized Runtime installedDecoder()throws IOException {
            // Historical verification reopens originals and does not require a current frontend/physical lease.
            for(var attempt:attempts.values())if(attempt.installed!=null&&attempt.installed.service() instanceof Runtime actual)return actual;
            throw new IOException("actual source-owned framebuffer archival decoder is not installed");
        }
        private boolean active(Runtime actual){
            try{var menu=core.requireFrontendMenu(actual.context);return menu.publicPhase()==RootMenuSession.PublicPhase.FRONTEND
                    &&menu.frontend==actual.context.frontend().authority()&&menu.bindings==actual.context.bindings();}
            catch(IOException unavailable){return false;}
        }
        @Override public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException {
            Objects.requireNonNull(same);if(core!=null&&core!=same)throw new IOException("framebuffer component belongs to another actual Core");core=same;
        }
        @Override public synchronized RootFrontendCoaPublicProducts.ComponentInstalled install(RootRuntimeContext same)throws IOException {
            Objects.requireNonNull(same);if(core==null||same.core()!=core)throw new IOException("framebuffer requires its identical pre-bound Core");
            Attempt old=attempts.get(same);if(old!=null){if(old.installed!=null)return old.installed;throw new IOException("partial framebuffer installation is never replayed",old.failure);}
            if(attempts.size()>=64)throw new IOException("actual framebuffer context installation bound exhausted");
            var attempt=new Attempt();attempts.put(same,attempt);
            try {
                selected.requireLoadedClasses(same.game().launchPlan());
                for(var original:sources)requireSame(original);
                need(same.frontend().rules().definitions().originalDriverSource().equals(originalDriver),"framebuffer uses a different original frontend source");
                // The physical guard retains the actual managed process birth and source, never an injected PID-only predicate.
                var capture=new CoaWindowCapture(same.game().generation(),expected->{
                    same.game().verify();need(expected.equals(same.game().generation()),"physical capture crossed actual Game birth");
                    selected.requireLoadedClasses(same.game().launchPlan());
                    for(var original:sources)requireSame(original);
                },same.clock());
                var extension=new CoaFramebufferExtension(same.game().generation().pid(),new CoaCalibrations(),capture::captureReadOnly,
                        CoaFramebufferExtension.Backend.WINDOWS_AWT_AUTHENTICATED_CLIENT);
                var runtime=new Runtime(same,reads,extension,capture,sources,timeout,selected);
                // Designer already installs the two identical read contracts and their route admissions.
                var installation=new RootDomainInstallation("original-seven-coa-framebuffer-methods/v1",List.of(),List.of(),List.of(),
                        List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
                attempt.installed=new RootFrontendCoaPublicProducts.ComponentInstalled(installation,runtime);return attempt.installed;
            }catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("actual framebuffer installation failed",failure);throw attempt.failure;}
        }
    }
    private static final class Attempt {RootFrontendCoaPublicProducts.ComponentInstalled installed;IOException failure;}
    private static final class Runtime implements FrontendCoaService.NativeAccess {
        private final RootRuntimeContext context;
        private final CoaDesigner.ReadDefinitions reads;
        private final CoaFramebufferExtension extension;
        private final CoaWindowCapture capture;
        private final List<ExactRef> sources;
        private final Duration timeout;
        private final RootRuntimeSelectedSources selected;
        private ActionCommand pendingPreparation;
        private Runtime(RootRuntimeContext context,CoaDesigner.ReadDefinitions reads,CoaFramebufferExtension extension,
                CoaWindowCapture capture,List<ExactRef> sources,Duration timeout,RootRuntimeSelectedSources selected){
            this.context=context;this.reads=reads;this.extension=extension;this.capture=capture;this.sources=sources;this.timeout=timeout;this.selected=selected;
        }
        @Override public synchronized Response execute(Request request)throws IOException {
            Objects.requireNonNull(request);need(CoaFramebufferExtension.METHODS.contains(request.method()),"foreign framebuffer method");
            Instant now=context.clock().instant(),candidate=now.plus(timeout),review=context.core().configuration().reviewAt();
            final Instant deadline=review.isBefore(candidate)?review:candidate;
            context.requireCurrent(deadline);if(!now.isBefore(deadline))throw new IOException("framebuffer source review or request deadline expired");
            RootMenuSession menu=context.core().requireFrontendMenu(context);
            need(menu.frontend==context.frontend().authority()&&menu.bindings==context.bindings()
                    &&menu.publicPhase()==RootMenuSession.PublicPhase.FRONTEND,"framebuffer crossed actual Root/Menu inventory");
            if(request.method()==Method.PREPARE)return prepare(menu,deadline);
            // The original capture prepares a hidden client. The one canonical action runs outside the READ scope.
            boolean foreground=context.withSession(same->context.frontend().withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,deadline,lease->{
                verifySources(same);requirePage(observe(same,menu,lease,deadline));return capture.foregroundReady();
            }));
            if(!foreground)prepare(menu,deadline);
            return context.withSession(same->context.frontend().withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,deadline,lease->{
                verifySources(same);requireLease(lease);
                var before=observe(same,menu,lease,deadline);
                requirePage(before);
                Response result=extension.execute(request,CoaFramebuffer.SearchBudget.until(context.clock(),deadline));
                // New independent native reads run after the actual original image-domain operation.
                var after=observe(same,menu,lease,deadline);requirePage(after);
                var verified=CoaPostconditions.stableCapture(result,before.binding(),after.binding(),before.route(),before.tree(),after.route(),after.tree());
                context.requireCurrent(deadline);verifySources(same);
                var row=FrontendCoaCodec.object(verified.result().original());
                row.put("route","coat_of_arms_designer").put("routeStable",verified.routeStable())
                        .put("nativePageRootAvailableBefore",verified.nativePageRootAvailableBefore())
                        .put("nativePageRootAvailableAfter",verified.nativePageRootAvailableAfter())
                        .put("connectionGeneration",verified.binding().connectionGeneration().toString());
                return FrontendCoaCodec.response(row);
            }));
        }
        private Response prepare(RootMenuSession menu,Instant deadline)throws IOException {
            context.frontend().authority().requireOutsideSourceBoundFrontendRead();
            ActionReceipt receipt;
            if(pendingPreparation!=null)receipt=menu.reconcile(pendingPreparation.actionId());
            else {
                pendingPreparation=context.withSession(same->context.frontend().withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,deadline,lease->{
                    verifySources(same);var before=observe(same,menu,lease,deadline);requirePage(before);
                    var args=FrontendCoaCodec.empty();args.set("before_route",before.route().originalEvidence().toJson());args.set("before_tree",before.tree().originalEvidence().toJson());
                    var origin=before.identity();var values=List.<org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue>of(
                            new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("route"),"coat_of_arms_designer"),
                            new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("exact_client_foreground"),true));
                    return new ActionCommand("coa-window-"+java.util.UUID.randomUUID().toString().replace("-",""),new CommandOrigin.Frontend(origin),context.source(),context.game().sessionId(),
                            PREPARE_OPERATION,OpportunityJson.object(DriverJson.fromNode(args),"window preparation originals"),
                            new CommandExpectation.Frontend(new FrontendExpectedPostcondition(origin,context.source(),EXPECTATION,values)),
                            new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
                }));
                receipt=menu.execute(pendingPreparation);
            }
            if(!(receipt.state() instanceof PhysicalActionState state)||state.phase()!=PhysicalActionState.Phase.COMPLETED
                    ||state.outcome().isEmpty()||!(state.outcome().orElseThrow() instanceof PhysicalOutcome.WindowCaptureOutcome value))
                throw new IOException("canonical foreground preparation unresolved; no replay; action_id="+pendingPreparation.actionId());
            final ActionReceipt actual=receipt;
            Response response=context.withSession(same->{
                var archive=context.archive().withSession(same);verifyArchived(same.head(),actual,archive);
                var result=value.value();var body=CoaFramebufferExtension.preparation(result);
                body.put("route","coat_of_arms_designer").put("routeStable",true).put("nativePageRootAvailableBefore",true).put("nativePageRootAvailableAfter",true)
                        .put("connectionGeneration",result.request().owner().connectionGeneration());
                return FrontendCoaCodec.response(body);
            });pendingPreparation=null;return response;
        }
        private void requireCommand(ActionCommand command){
            need(command.operation().equals(PREPARE_OPERATION)&&command.origin() instanceof CommandOrigin.Frontend
                    &&command.source().equals(context.source())&&command.sessionId().equals(context.game().sessionId())
                    &&command.origin().game().equals(context.game().generation())&&command.origin().requireFrontend().frame() instanceof FrontendFrame.Menu,
                    "physical framebuffer command crossed actual source/fullbirth/Menu owner");
            var expected=command.expectation().requireFrontend();
            need(expected.observerSchema().equals(EXPECTATION)&&expected.before().equals(command.origin().requireFrontend())
                    &&expected.values().equals(List.of(
                    new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("route"),"coat_of_arms_designer"),
                    new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("exact_client_foreground"),true))),"physical framebuffer expectation changed");
        }
        GuardEvidence guard(WriterContracts.Head head,ActionCommand command)throws IOException {
            requireCommand(command);context.requireCurrent(command.deadline());
            return context.withSession(same->context.frontend().withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,command.deadline(),lease->{
                need(same.head().digest().equals(head.digest()),"physical guard crossed actual writer head");verifySources(same);requireLease(lease);
                var before=checkBefore(command,context.archive().withSession(same));
                var route=FrontendRulesCodec.route(lease.originalRoute().originalResultToken().orElseThrow(()->new IOException("actual source-bound frontend route token missing")),
                        before.actual().route().value().source(),lease.identity().frame().querySequence());
                need(route.route()==FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER,"actual current guard route left the native designer before OS preparation");
                return RootFrontendGuardEvidence.sourceBound(context.frontend().authority(),command.origin().requireFrontend(),context.source(),context.game().sessionId(),PREPARE_OPERATION,
                        command.deadline(),head,context.core().authorityId(),context.clock(),same,context.archive().withSession(same),context.originals());
            }));
        }
        PreparedAction preparePhysical(ContinuityStorePort.Session same,ActionCommand command,String id)throws IOException {
            context.writer().requireSession(same);requireCommand(command);verifySources(same);var archive=context.archive().withSession(same);
            var refs=checkBefore(command,archive);var before=capture.preflightReadOnly();
            var sourceProof=FrontendCoaCodec.empty().put("schema",SOURCES);var list=sourceProof.putArray("sources");for(var original:sources)list.add(original.toJson());
            ExactRef proof=archive.preserveMaterial(FrontendCoaCodec.raw(sourceProof));
            var identity=command.origin().requireFrontend();
            String exe=context.game().launchPlan().sources().review().gameExecutable().sha256().toLowerCase(java.util.Locale.ROOT);
            var owner=new FrontendWindowCaptureRequest.Owner(identity.machineId(),identity.frontendSessionId(),identity.game().pid(),identity.game().creationFiletime().value().toString(),exe,identity.connectionGeneration().toString());
            var request=new FrontendWindowCaptureRequest(id,context.clock().instant(),command.deadline(),owner,identity.nativeEvidence(),
                    selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootCoaFramebuffer.class),List.of(proof,refs.route(),refs.tree()),before.requestWindow(),before.foregroundRoot());
            return new PreparedAction.WindowCaptureRequest(request);
        }
        PhysicalOutcome post(PhysicalSubmission submission,PreparedAction.WindowCaptureRequest exact,Instant deadline)throws IOException {
            if(!(submission instanceof FrontendWindowCapturePermit permit)||!exact.value().deadline().equals(deadline))throw new IOException("wrong private physical permit/deadline");
            return context.withSession(same->{verifySources(same);var archive=context.archive().withSession(same);var ref=archive.frontendWindowCaptureRequestReferenceOf(exact.value());
                need(archive.loadFrontendWindowCaptureRequest(ref).equals(exact.value()),"actual original window request changed before post");
                return new PhysicalOutcome.WindowCaptureOutcome(capture.present(exact.value(),ref,permit));});
        }
        PhysicalActionRegistry.Observation observePhysical(ContinuityStorePort.Session same,ActionCommand command,PhysicalActionState original,Instant deadline)throws IOException {
            context.writer().requireSession(same);requireCommand(command);verifySources(same);
            if(!(original.request() instanceof PreparedAction.WindowCaptureRequest prepared)||original.outcome().isEmpty()
                    ||!(original.outcome().orElseThrow() instanceof PhysicalOutcome.WindowCaptureOutcome returned)
                    ||returned.value().status()!=FrontendWindowCaptureOutcome.Status.VERIFIED)
                return new PhysicalActionRegistry.Pending("original Win32 post is unresolved; no retry or fabricated VERIFIED",original.evidence());
            var menu=context.core().requireFrontendMenu(context);var archive=context.archive().withSession(same);
            return context.frontend().withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,deadline,lease->{
                verifySources(same);var after=observe(same,menu,lease,deadline);requirePage(after);
                need(!after.route().observedAt().isBefore(original.submittedAt())&&!after.tree().observedAt().isBefore(original.submittedAt())
                        &&after.identity().frame().querySequence().compareTo(original.guard().origin().requireFrontend().frame().querySequence())>0,"physical completion lacks independent later native reads");
                var actual=capture.preflightReadOnly();need(actual.requestWindow().equals(prepared.value().window())&&actual.foregroundRoot().equals(prepared.value().window().hwnd())
                        &&!actual.observedAt().isBefore(original.submittedAt()),"physical completion lacks actual stable after-window/foreground");
                var evidence=FrontendCoaCodec.empty().put("schema",OBSERVATION).put("observed_at",actual.observedAt().toString()).put("foreground",actual.foregroundRoot());
                evidence.set("window",actual.requestWindow().toJson());evidence.set("request",archive.frontendWindowCaptureRequestReferenceOf(prepared.value()).toJson());
                evidence.set("outcome",archive.frontendWindowCaptureOutcomeReferenceOf(returned.value()).toJson());
                evidence.set("after_route",after.route().originalEvidence().toJson());evidence.set("after_tree",after.tree().originalEvidence().toJson());
                var ref=archive.preserveMaterial(FrontendCoaCodec.raw(evidence));return new PhysicalActionRegistry.Completed(List.of(ref));
            });
        }
        private Before checkBefore(ActionCommand command,ActionPorts.OutcomeArchive archive){
            var args=StrictJson.object(DriverJson.toNode(command.arguments()),Set.of("before_route","before_tree"));
            ExactRef routeRef=ExactRef.fromJson(args.get("before_route")),treeRef=ExactRef.fromJson(args.get("before_tree"));
            var routeContract=context.frontend().rules().definitions().route();
            var route=checkedRead(command,routeRef,routeContract,archive);var tree=checkedRead(command,treeRef,reads.tree(),archive);
            need(route.after().binding().origin().requireFrontend().frame().querySequence().compareTo(command.origin().requireFrontend().frame().querySequence())<=0
                    &&tree.after().binding().origin().requireFrontend().frame().querySequence().compareTo(command.origin().requireFrontend().frame().querySequence())<=0,"window before-read is later than its exact command origin");
            var typed=observed(routeContract.decode(route),reads.tree().decode(tree),route,tree,routeRef,treeRef);requirePage(typed);
            return new Before(routeRef,treeRef,typed);
        }
        private static <T> PlanningReadReceipt checkedRead(ActionCommand command,ExactRef ref,ReadContract<T> contract,ActionPorts.OutcomeArchive archive){
            var read=archive.loadRead(ref);need(ref.equals(archive.readReferenceOf(read))&&read.contractId().equals(contract.contractId())
                    &&read.request().operation().equals(contract.operation())&&read.request().source().equals(command.source())
                    &&read.request().sessionId().equals(command.sessionId())&&read.request().origin() instanceof CommandOrigin.Frontend
                    &&read.after().binding().origin() instanceof CommandOrigin.Frontend
                    &&command.origin().requireFrontend().sameSession(read.request().origin().requireFrontend())
                    &&command.origin().requireFrontend().sameSession(read.after().binding().origin().requireFrontend())
                    &&read.after().binding().origin().requireFrontend().frame() instanceof FrontendFrame.Menu&&read.original().nativeOk(),"window original read crossed exact contract/source/session/fullbirth/Menu");
            contract.decode(read);return read;
        }
        void verifyArchived(WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive originals)throws IOException {
            if(receipt.state() instanceof ActionState.IntentDurable){
                // Canonical INTENT precedes the prepared physical state. Original command DATA grants no post permission.
                need(receipt.command().operation().equals(PREPARE_OPERATION)&&receipt.command().origin() instanceof CommandOrigin.Frontend
                        &&receipt.command().origin().requireFrontend().frame() instanceof FrontendFrame.Menu
                        &&receipt.command().origin().machineId().equals(head.state().machineId()),"archived physical intent changed its finite frontend origin");
                var expected=receipt.command().expectation().requireFrontend();
                need(expected.observerSchema().equals(EXPECTATION)&&expected.before().equals(receipt.command().origin().requireFrontend())
                        &&expected.values().equals(List.of(
                        new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("route"),"coat_of_arms_designer"),
                        new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("exact_client_foreground"),true))),"archived physical intent changed its original expected result");
                context.withSession(same->{
                    context.writer().requireSession(same);checkBefore(receipt.command(),originals);
                    for(var ref:sources){var pin=same.capturePin(ref,Math.toIntExact(ref.bytes()));same.verifyPin(pin);}
                    return null;
                });
                return;
            }
            if(!receipt.command().operation().equals(PREPARE_OPERATION)||!(receipt.command().origin() instanceof CommandOrigin.Frontend)
                    ||!(receipt.state() instanceof PhysicalActionState state)||!(state.request() instanceof PreparedAction.WindowCaptureRequest prepared))
                throw new IOException("archived request is not the finite frontend window plane");
            context.withSession(same->{
                context.writer().requireSession(same);need(head.state().machineId().equals(receipt.command().source().machineId()),"archived physical action machine differs");
                RootFrontendGuardEvidence.verify(state.guard(),originals,same,context.originals());
                var request=prepared.value();var identity=receipt.command().origin().requireFrontend();var owner=request.owner();
                need(owner.machineId().equals(identity.machineId())&&owner.sessionId().equals(identity.frontendSessionId())&&owner.processId()==identity.game().pid()
                        &&owner.processBirthFiletime().equals(identity.game().creationFiletime().value().toString())&&owner.connectionGeneration().equals(identity.connectionGeneration().toString())
                        &&owner.actualExecutableSha256().equals(context.game().launchPlan().sources().review().gameExecutable().sha256().toLowerCase(java.util.Locale.ROOT))
                        &&request.actualFrontendEvidence().equals(identity.nativeEvidence())&&request.deadline().equals(receipt.command().deadline()),"archived Window request changed original owner/fullbirth/connection/deadline");
                var requestRef=originals.frontendWindowCaptureRequestReferenceOf(request);need(originals.loadFrontendWindowCaptureRequest(requestRef).equals(request),"archived Window request bytes differ");
                var before=checkBefore(receipt.command(),originals);need(request.preparationEvidence().size()==3
                        &&request.preparationEvidence().get(1).equals(before.route())&&request.preparationEvidence().get(2).equals(before.tree()),"physical request lost exact original native preconditions");
                var sourceProof=StrictJson.object(FrontendCoaCodec.object(originals.loadMaterial(request.preparationEvidence().getFirst())),Set.of("schema","sources"));
                need(StrictJson.text(sourceProof.get("schema")).equals(SOURCES)&&sourceProof.get("sources").isArray()
                        &&sourceProof.get("sources").size()>0&&sourceProof.get("sources").size()<=64,"original physical producer source closure missing");
                var seen=new java.util.HashSet<ExactRef>();for(var raw:sourceProof.get("sources")){
                    var ref=ExactRef.fromJson(raw);need(seen.add(ref)&&ref.bytes()>0&&ref.bytes()<=4*1024*1024,"bounded unique physical source original required");
                    var pin=same.capturePin(ref,Math.toIntExact(ref.bytes()));same.verifyPin(pin);
                }need(seen.equals(new java.util.HashSet<>(sources))&&seen.contains(request.sourceRef()),"physical original source closure differs from the identical installed producer");
                FrontendWindowCaptureOutcome returned=null;
                if(state.outcome().isPresent()){
                    need(state.outcome().orElseThrow() instanceof PhysicalOutcome.WindowCaptureOutcome,"physical outcome plane changed");
                    returned=((PhysicalOutcome.WindowCaptureOutcome)state.outcome().orElseThrow()).value();
                    need(returned.request().equals(request),"archived foreground outcome changed request");
                    returned.verifyOriginalRequest(request.encode());var ref=originals.frontendWindowCaptureOutcomeReferenceOf(returned);
                    need(originals.loadFrontendWindowCaptureOutcome(ref).equals(returned),"archived foreground outcome bytes differ");
                }
                if(state.phase()==PhysicalActionState.Phase.COMPLETED){
                    need(returned!=null&&returned.status()==FrontendWindowCaptureOutcome.Status.VERIFIED&&state.evidence().size()==1,"completed physical action lacks actual verified original and independent proof");
                    var proof=StrictJson.object(FrontendCoaCodec.object(originals.loadMaterial(state.evidence().getFirst())),Set.of("schema","observed_at","foreground","window","request","outcome","after_route","after_tree"));
                    need(StrictJson.text(proof.get("schema")).equals(OBSERVATION)&&ExactRef.fromJson(proof.get("request")).equals(requestRef)
                            &&ExactRef.fromJson(proof.get("outcome")).equals(originals.frontendWindowCaptureOutcomeReferenceOf(returned))
                            &&FrontendWindowCaptureRequest.Window.fromJson(proof.get("window")).equals(request.window())
                            &&StrictJson.text(proof.get("foreground")).equals(request.window().hwnd())&&!Instant.parse(StrictJson.text(proof.get("observed_at"))).isBefore(state.submittedAt()),"physical completion actual window/foreground/chronology differs");
                    var routeContract=context.frontend().rules().definitions().route();var routeRef=ExactRef.fromJson(proof.get("after_route"));var treeRef=ExactRef.fromJson(proof.get("after_tree"));
                    var route=checkedRead(receipt.command(),routeRef,routeContract,originals);var tree=checkedRead(receipt.command(),treeRef,reads.tree(),originals);
                    var after=observed(routeContract.decode(route),reads.tree().decode(tree),route,tree,routeRef,treeRef);requirePage(after);
                    need(!after.route().observedAt().isBefore(state.submittedAt())&&!after.tree().observedAt().isBefore(state.submittedAt())
                            &&after.identity().frame().querySequence().compareTo(state.guard().origin().requireFrontend().frame().querySequence())>0,"archived completion lacks independent native after-state");
                    CoaPostconditions.stableCapture(returned,before.actual().binding(),after.binding(),before.actual().route(),before.actual().tree(),after.route(),after.tree());
                }return null;
            });
        }
        private Observed observe(ContinuityStorePort.Session same,RootMenuSession menu,FrontendAuthority.LeaseSnapshot lease,Instant deadline)throws IOException {
            requireLease(lease);var route=context.frontend().rules().definitions().route();
            var actualRoute=known(menu.read(route,request(lease.identity(),route.operation(),deadline)));
            var actualTree=known(menu.read(reads.tree(),request(lease.identity(),reads.tree().operation(),deadline)));
            requireOriginal(same,actualRoute);requireOriginal(same,actualTree);
            var nativeBinding=actualRoute.value().source().binding();
            need(nativeBinding.bridgePid()==lease.identity().bridgePid()&&nativeBinding.connectionGeneration().equals(lease.identity().connectionGeneration()),"fresh route binding crossed actual held frontend lease");
            return new Observed(actualTree.receipt().after().binding().origin().requireFrontend(),new CoaData.FrontendBinding(nativeBinding.connectionGeneration(),nativeBinding.bridgePid()),evidence(actualRoute),evidence(actualTree));
        }
        private void requireLease(FrontendAuthority.LeaseSnapshot lease){
            need(lease.source().equals(context.source())&&lease.identity().game().equals(context.game().generation())
                    &&lease.identity().frontendSessionId().equals(context.game().sessionId())&&lease.identity().frame() instanceof FrontendFrame.Menu,
                    "framebuffer read crossed original source/process birth/session/Menu identity");
        }
        private static void requirePage(Observed observed){
            need(observed.route().value().route()==FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER,"framebuffer requires actual native designer route");
            need(observed.tree().value().available()&&observed.tree().value().scopeRootName().equals("coat_of_arms_page"),"framebuffer requires actual visible native page root");
        }
        private PlanningReadRequest request(FrontendIdentity actual,OperationKey operation,Instant deadline){
            return new PlanningReadRequest(new CommandOrigin.Frontend(actual),context.source(),context.game().sessionId(),operation,new OpportunityJson.Obj(java.util.Map.of()),deadline);
        }
        private void verifySources(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);context.game().verify();
            selected.requireLoadedClasses(context.game().launchPlan());
            need(context.readCatalog().containsIdentity(reads.tree())&&context.readCatalog().containsIdentity(reads.grid())
                    &&context.readCatalog().containsIdentity(context.frontend().rules().definitions().route()),"framebuffer must consume the identical actually installed shared CoA/native-route contracts");
            for(var original:sources){
                need(original.bytes()>0&&original.bytes()<=4*1024*1024,"bounded actual source-file material required");
                var pin=same.capturePin(original,Math.toIntExact(original.bytes()));same.verifyPin(pin);
            }
        }
        private void requireOriginal(ContinuityStorePort.Session same,PlanningReadResult.Known<?> known){
            var archive=context.archive().withSession(same);
            need(archive.readReferenceOf(known.receipt()).equals(known.originalReceipt())&&archive.loadRead(known.originalReceipt()).equals(known.receipt()),"framebuffer read lost its actual canonical archived receipt");
        }
    }
    private record Before(ExactRef route,ExactRef tree,Observed actual) { }
    private static Observed observed(FrontendRulesData.ObservedRoute route,CoaData.Tree tree,PlanningReadReceipt routeReceipt,PlanningReadReceipt treeReceipt,ExactRef routeRef,ExactRef treeRef){
        var binding=route.source().binding();return new Observed(treeReceipt.after().binding().origin().requireFrontend(),new CoaData.FrontendBinding(binding.connectionGeneration(),binding.bridgePid()),
                new CoaPostconditions.ReadEvidence<>(route,routeReceipt.requestId(),routeReceipt.after().binding().observedAt(),routeRef),
                new CoaPostconditions.ReadEvidence<>(tree,treeReceipt.requestId(),treeReceipt.after().binding().observedAt(),treeRef));
    }
    private record Observed(FrontendIdentity identity,CoaData.FrontendBinding binding,CoaPostconditions.ReadEvidence<FrontendRulesData.ObservedRoute> route,
            CoaPostconditions.ReadEvidence<CoaData.Tree> tree) { }
    private static <T> CoaPostconditions.ReadEvidence<T> evidence(PlanningReadResult.Known<T> known){
        return new CoaPostconditions.ReadEvidence<>(known.value(),known.receipt().requestId(),known.receipt().after().binding().observedAt(),known.originalReceipt());
    }
    private static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> actual)throws IOException {
        if(actual instanceof PlanningReadResult.Known<T> known)return known;
        throw new IOException("actual independent framebuffer native read unavailable: "+((PlanningReadResult.Unavailable<T>)actual).reason());
    }
    private static ExactRef source(Path path)throws IOException {var actual=SharedSourceFiles.observe(path);SharedSourceFiles.assertUnchanged(actual);var ref=actual.source();return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static ExactRef original(RootRuntimeSelectedSources selected,ExactRef source)throws IOException {
        return selected.original(new FileRef(source.path(),source.bytes(),source.sha256()),RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON);
    }
    private static void requireSame(ExactRef ref)throws IOException {
        var actual=SharedSourceFiles.observe(Path.of(ref.path()));SharedSourceFiles.assertUnchanged(actual);
        var found=actual.source();if(!new ExactRef(found.path(),found.bytes(),found.sha256()).equals(ref))throw new IOException("framebuffer original source changed: "+ref.path());
    }
}
