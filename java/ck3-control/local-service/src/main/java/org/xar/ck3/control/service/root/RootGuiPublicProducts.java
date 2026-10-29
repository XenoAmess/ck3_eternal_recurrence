package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverPublicContext;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.capabilities.gui.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Original GUI public producers, fixed typed registrations, and one runtime per actual Root context. */
public final class RootGuiPublicProducts {
 private RootGuiPublicProducts(){}
 static Set<String> actionOperations(){
  var steps=new TreeSet<>(GuiActions.operations());
  steps.remove(org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.SELECT);
  steps.remove(org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.CONFIRM);
  steps.add("activate-ingame-decisions-v1");
  return Collections.unmodifiableSet(steps);
 }

 @FunctionalInterface public interface NavigationFactory{GuiService.NavigationExtension create(RootRuntimeContext actual)throws IOException;}
 /** A finite source-owned partition. Descriptor DATA alone never establishes an installed control producer. */
 public record NavigationControlMetadata(String observerSchema,Set<GuiService.NavigationSelector> controlSelectors,Set<GuiService.NavigationSelector> pendingSelectors){
  public NavigationControlMetadata{StrictJson.text(observerSchema);controlSelectors=Set.copyOf(controlSelectors);pendingSelectors=Set.copyOf(pendingSelectors);
   require(!controlSelectors.isEmpty()&&controlSelectors.size()+pendingSelectors.size()<=32,"finite original control partition required");
   require(Collections.disjoint(controlSelectors,pendingSelectors),"a final pending selector cannot also claim control settlement");}
 }
 public record NavigationDefinition(Set<GuiService.NavigationSelector> selectors,ExactRef source,Optional<NativePrivateActionPermission> permission,NavigationFactory factory,Optional<NavigationControlMetadata> controlMetadata){
  public NavigationDefinition{selectors=Set.copyOf(selectors);require(!selectors.isEmpty()&&selectors.size()<=32,"finite original Nav selectors");Objects.requireNonNull(source);Objects.requireNonNull(permission);Objects.requireNonNull(factory);Objects.requireNonNull(controlMetadata);
   permission.ifPresent(p->require(p.operation().value().equals("navigate-ingame-ui-v1"),"Nav descriptor cannot grant another operation"));
   var exact=selectors;controlMetadata.ifPresent(metadata->{var union=new HashSet<>(metadata.controlSelectors());union.addAll(metadata.pendingSelectors());require(union.equals(exact),"control and pending selectors must partition the original definition");});}
  public NavigationDefinition(Set<GuiService.NavigationSelector> selectors,ExactRef source,Optional<NativePrivateActionPermission> permission,NavigationFactory factory){this(selectors,source,permission,factory,Optional.empty());}
 }
 /** Issued only by the identical installed GUI factory; retains every actual delegate and replay binding. */
 public static final class InstalledNavigation{
  private final RootRuntimeContext context;private final NavigationDefinition definition;private final GuiService.NavigationExtension extension;
  private final RootExecutableBindings.ActionBinding actionBinding;private final NativeRecordedEvidenceVerifier.Binding archivedBinding;
  private InstalledNavigation(RootRuntimeContext context,NavigationDefinition definition,GuiService.NavigationExtension extension,RootExecutableBindings.ActionBinding actionBinding,NativeRecordedEvidenceVerifier.Binding archivedBinding){
   this.context=Objects.requireNonNull(context);this.definition=Objects.requireNonNull(definition);this.extension=Objects.requireNonNull(extension);this.actionBinding=Objects.requireNonNull(actionBinding);this.archivedBinding=Objects.requireNonNull(archivedBinding);
   require(definition.selectors().equals(extension.selectors())&&definition.source().equals(extension.source()),"installed original navigation identity differs");
   require(actionBinding.effect().operation().value().equals("navigate-ingame-ui-v1")&&archivedBinding.operation().equals(actionBinding.effect().operation()),"installed sole navigation effect/replay operation differs");
  }
  public NavigationDefinition definition(){return definition;}public GuiService.NavigationExtension extension(){return extension;}
  public RootExecutableBindings.ActionBinding actionBinding(){return actionBinding;}public NativeRecordedEvidenceVerifier.Binding archivedBinding(){return archivedBinding;}
  private boolean matchesActualContext(ActionCommand command){
   Objects.requireNonNull(command);return definition.controlMetadata().isPresent()&&command.origin() instanceof CommandOrigin.Gameplay&&command.operation().equals(actionBinding.effect().operation())
    &&command.before().game().equals(context.game().generation())&&command.source().equals(context.source())&&command.sessionId().equals(context.game().sessionId());
  }
  public boolean matchesControl(ActionCommand command){return matchesActualContext(command)&&matchesFiniteControl(definition.controlMetadata().orElseThrow(),command);}
  /** Final native dispatches remain UNKNOWN; a later verified rejection/terminal is still a zero-business outcome. */
  public boolean matchesPending(ActionCommand command){return matchesActualContext(command)&&matchesFinitePending(definition.controlMetadata().orElseThrow(),command);}
 }
 /** Shared by the actual installed identity chain and its producer-to-consumer regression. */
 static boolean matchesFiniteControl(NavigationControlMetadata metadata,ActionCommand command){return matchesFiniteSelector(metadata,metadata.controlSelectors(),command);}
 static boolean matchesFinitePending(NavigationControlMetadata metadata,ActionCommand command){return matchesFiniteSelector(metadata,metadata.pendingSelectors(),command);}
 private static boolean matchesFiniteSelector(NavigationControlMetadata metadata,Set<GuiService.NavigationSelector> selectors,ActionCommand command){
  if(!command.operation().value().equals("navigate-ingame-ui-v1")||!command.expected().observerSchema().equals(metadata.observerSchema()))return false;
  var fields=OpportunityJson.toNode(command.arguments());var window=fields.get("window_kind");var operation=fields.get("operation");
  return window!=null&&window.isTextual()&&operation!=null&&operation.isTextual()&&window.textValue().matches("[a-z_]{1,64}")&&operation.textValue().matches("[a-z_]{1,96}")&&selectors.contains(new GuiService.NavigationSelector(window.textValue(),operation.textValue()));
 }
 @FunctionalInterface public interface InventoryFactory{GuiService.InventoryRead create(RootRuntimeContext actual)throws IOException;}
 @FunctionalInterface public interface PresentationFactory{GuiService.PresentationPlane create(RootRuntimeContext actual)throws IOException;}
 @FunctionalInterface public interface ObserverFactory{NativeCameraObserver create(RootRuntimeContext actual)throws IOException;}
 /** Ordinary native read definitions and physical execution metadata; no definitions publication is required. */
 public record Config(GuiReads.Sources reads,List<ExactRef> physicalMetadata){
  public Config{Objects.requireNonNull(reads);physicalMetadata=List.copyOf(physicalMetadata);}
 }
 public static Prepared ordinary(Config config,RootAdditionalDomains.ImplementationMetadata metadata){return new Prepared(config,metadata);}
 public static Prepared prepare(RootRuntimeDefinitions.Inputs actual)throws IOException{return new Prepared(actual);}

 public static final class Prepared {
  private final GuiReads contracts;private final ReadContract<GuiModels.WindowTree> frontendCensus;private final ExactRef actionSource,serviceSource,decoderSource;
  private final List<ExactRef> originals;private final List<ExactRef> physicalSources;private final List<PhysicalActionRegistry.Binding> physical;private final List<NavigationDefinition> navigation=new ArrayList<>();
  private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
  private RootApplicationAssembly.Core core;private Optional<InventoryFactory> inventory=Optional.empty();
  private Optional<PresentationFactory> presentation=Optional.empty();private Optional<ObserverFactory> observer=Optional.empty();
  private Prepared(Config config,RootAdditionalDomains.ImplementationMetadata metadata){
   Objects.requireNonNull(config);Objects.requireNonNull(metadata);var definitions=config.reads();
   contracts=new GuiReads(definitions);frontendCensus=frontendCensus(definitions.census());
   actionSource=metadata.implementation(GuiActions.class);serviceSource=metadata.implementation(GuiService.class);decoderSource=metadata.implementation(GuiDecoders.class);
   originals=List.of(definitions.semantic(),definitions.census(),definitions.decision(),definitions.aubPolicy(),definitions.aubState(),definitions.whiteBusiness(),definitions.whiteText());
   var executionMetadata=new LinkedHashSet<ExactRef>(config.physicalMetadata());
   for(var type:List.of(RootGuiPresentation.class,RootGuiPublicProducts.class,GuiService.class,NativeCameraObserver.class,
     org.xar.ck3.control.nativebridge.NativePresentationTransport.class,org.xar.ck3.control.platform.ManagedGameSession.class,
     org.xar.ck3.control.platform.JavaGameLifecycle.class,RootAutoCamera.class))executionMetadata.add(metadata.implementation(type));
   physicalSources=List.copyOf(executionMetadata);
   physical=List.of(RootGuiPresentation.binding(physicalSources,this::physicalRuntime,this::physicalRuntime,this::automaticRuntime,this::presentationRuntimes));
  }
  private Prepared(RootRuntimeDefinitions.Inputs actual)throws IOException{
   Objects.requireNonNull(actual);var selectedSources=new RootRuntimeSelectedSources(actual);
   ExactRef driver=actual.source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER);Path path=Path.of(driver.path()).toAbsolutePath().normalize();
   require(path.getFileName().toString().equals("native_driver.py")&&path.getParent().getFileName().toString().equals("bridge"),"configured original bridge driver required");
   requireSame(driver);Path bridge=path.getParent();
   var semantic=source(bridge.resolve("ingame_ui_contract.py"));var census=source(bridge.resolve("gui_window_tree_contract.py"));
   var decision=source(bridge.resolve("ingame_decision_item_contract.py"));var aubPolicy=source(bridge.resolve("aub_policy_options_contract.py"));
   var aubState=source(bridge.resolve("aub_business_state_contract.py"));var whiteBusiness=source(bridge.resolve("white_player_business_variables_contract.py"));var whiteText=source(bridge.resolve("white_rendered_text_contract.py"));
   originals=List.of(driver,source(bridge.resolve("service.py")),source(bridge.resolve("mcp_server.py")),semantic,census,decision,aubPolicy,aubState,whiteBusiness,whiteText,
    source(bridge.resolve("ingame_decisions_open_contract.py")),source(bridge.resolve("ingame_decision_outcome_contract.py")),source(bridge.resolve("religion_presentation_ui_contract.py")),source(bridge.resolve("realm_overview_camera.py")),
    source(bridge.resolve("white_control_action_driver.py")),source(bridge.resolve("white_control_action_contract.py")),source(bridge.resolve("white_numeric_control_action_driver.py")),source(bridge.resolve("white_numeric_control_action_contract.py")),source(bridge.resolve("clerical_preview_ui_contract.py")));
   contracts=new GuiReads(new GuiReads.Sources(semantic,census,decision,aubPolicy,aubState,whiteBusiness,whiteText));
   frontendCensus=frontendCensus(census);
   actionSource=selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiActions.class);
   serviceSource=selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiService.class);
   decoderSource=selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiDecoders.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NativeUiParsedReturn.class);selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiContract.class);selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiCodec.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiPublicBinder.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiPublicMetadata.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiFaithWhitePublicFormatter.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiWhiteOriginals.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiPresentationResult.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiReads.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiCapabilities.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ArmyGuiPublicFormatter.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiDecisionPublicFormatter.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiReadFailure.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiActionFailure.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GuiSelectedDecisionTerms.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NativeFreshSnapshotPort.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,DriverPublicContext.class);
   selectedSources.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootGuiPublicProducts.class);
   var physicalInventory=new ArrayList<ExactRef>();physicalInventory.add(selectedSources.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootGuiPresentation.class));
   physicalInventory.add(selectedSources.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootGuiPublicProducts.class));physicalInventory.add(serviceSource);
   for(var unit:org.xar.ck3.control.nativebridge.NativePresentationTransport.sourceUnits())physicalInventory.add(unit.targetRelative().endsWith("/"+unit.actualClass().getSimpleName()+".java")?selectedSources.javaSourceAt(unit.targetRelative(),unit.actualClass()):selectedSources.javaTarget(unit.targetRelative()));
   physicalInventory.add(selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NativeCameraObserver.class));
   physicalInventory.add(selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,org.xar.ck3.control.platform.ManagedGameSession.class));
   physicalInventory.add(selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,org.xar.ck3.control.platform.JavaGameLifecycle.class));
   physicalInventory.add(source(bridge.resolve("realm_overview_camera.py")));
   for(var type:List.of(org.xar.ck3.control.application.presentation.AutoCameraModel.class,org.xar.ck3.control.application.presentation.AutoCameraPolicy.class,
     org.xar.ck3.control.application.presentation.LatestCameraFollow.class,org.xar.ck3.control.application.action.SubmissionPermit.class,
     org.xar.ck3.control.application.action.PhysicalActionRegistry.class,org.xar.ck3.control.application.driver.DriverStateAssembler.class))
    physicalInventory.add(selectedSources.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,type));
   for(var type:List.of(org.xar.ck3.control.contracts.presentation.PresentationIntent.class,org.xar.ck3.control.contracts.presentation.PresentationCapture.class))
    physicalInventory.add(selectedSources.javaSource(RootRuntimeSelectedSources.Module.CONTRACTS,type));
   physicalInventory.add(selectedSources.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootAutoCamera.class));
   physicalInventory.add(selectedSources.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,LandedProvinceIndex.class));
   physicalSources=physicalInventory.stream().distinct().toList();
   physical=List.of(RootGuiPresentation.binding(physicalSources,this::physicalRuntime,this::physicalRuntime,this::automaticRuntime,this::presentationRuntimes));
  }
  public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
  public List<PhysicalActionRegistry.Binding> physicalBindings(){return physical;}
  private synchronized RootGuiPresentation physicalRuntime(ActionCommand command)throws IOException{
   RootGuiPresentation found=null;for(var attempt:attempts.values())if(attempt.installed!=null&&attempt.installed.presentationRuntime.owns(command)){
    if(found!=null)throw new IOException("two actual GUI contexts claim this physical command");found=attempt.installed.presentationRuntime;}
   if(found==null)throw new IOException("physical command has no identical installed GUI owner");return found;
  }
  private synchronized RootGuiPresentation physicalRuntime(org.xar.ck3.control.contracts.presentation.PresentationRequest request)throws IOException{
   RootGuiPresentation found=null;for(var attempt:attempts.values())if(attempt.installed!=null&&attempt.installed.presentationRuntime.owns(request)){
    if(found!=null)throw new IOException("two actual GUI contexts claim this physical request");found=attempt.installed.presentationRuntime;}
   if(found==null)throw new IOException("physical request has no retained original GUI preparation");return found;
  }
  private synchronized List<RootGuiPresentation> presentationRuntimes(){
   return attempts.values().stream().filter(a->a.installed!=null).map(a->a.installed.presentationRuntime).toList();
  }
  private synchronized RootGuiPresentation automaticRuntime(ActionCommand command)throws IOException{
   var all=presentationRuntimes().stream().filter(r->r.ownsGame(command)).toList();
   if(all.size()!=1)throw new IOException("one identical actual GUI automatic owner required");return all.getFirst();
  }
  /** No new domain body: GUI once/UNKNOWN remains in the existing canonical Action journal. */
  public synchronized void addNavigationDefinition(NavigationDefinition definition){
   require(core==null&&attempts.isEmpty(),"Nav definitions freeze before actual Core binding");Objects.requireNonNull(definition);
   var existing=new HashSet<GuiService.NavigationSelector>();navigation.forEach(d->existing.addAll(d.selectors()));
   require(definition.selectors().stream().noneMatch(existing::contains),"two GUI producers claim same native selector");
   require(navigation.size()<16,"finite original Nav producer bound");navigation.add(definition);
  }
  public synchronized void addInventoryDefinition(InventoryFactory actual){require(core==null&&inventory.isEmpty(),"inventory producer freezes once before Core");inventory=Optional.of(Objects.requireNonNull(actual));}
  public synchronized void addPresentationDefinition(PresentationFactory actual,ObserverFactory actualObserver){
   require(core==null&&presentation.isEmpty()&&observer.isEmpty(),"actual presentation producer freezes once before Core");presentation=Optional.of(Objects.requireNonNull(actual));observer=Optional.of(Objects.requireNonNull(actualObserver));}
  public synchronized boolean hasPresentationDefinition(){return !physical.isEmpty();}
  public synchronized boolean hasInventoryDefinition(){return inventory.isPresent();}
  public synchronized List<NativePrivateActionPermission> privatePermissions(){
   List<NativePrivateActionPermission> result=navigation.stream().flatMap(d->d.permission().stream()).toList();
   require(result.size()<=1,"one fixed private Nav permission maximum; advertised original Nav requires none");return result;
  }
  public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException{
   Objects.requireNonNull(same);if(core!=null&&core!=same)throw new IOException("GUI producers belong to another actual Core");core=same;
  }
  public synchronized Installed install(RootRuntimeContext same)throws IOException{
   Objects.requireNonNull(same);if(core==null||same.core()!=core)throw new IOException("GUI installation requires its identical actual Core");
   Attempt prior=attempts.get(same);if(prior!=null){if(prior.installed!=null){prior.installed.requireContext(same);return prior.installed;}throw new IOException("GUI partial installation is never replayed",prior.failure);}
   if(attempts.size()>=64)throw new IOException("GUI actual context attempt bound exhausted");Attempt attempt=new Attempt();attempts.put(same,attempt);
   try{
    var extensions=new ArrayList<GuiService.NavigationExtension>();
    for(NavigationDefinition definition:navigation){var actual=Objects.requireNonNull(definition.factory().create(same));
     require(actual.selectors().equals(definition.selectors())&&actual.source().equals(definition.source()),"actual Nav runtime differs from pre-Core original descriptor");extensions.add(actual);}
    var originalActions=new GuiActions(same.reads(),contracts,()->same.archive().withSession(same.borrowedSession()));var ports=new GuiService.NavigationPorts(originalActions,contracts,same.reads(),extensions);
    ActionCoordinatorPort actions=GuiService.captureCapable(new ActionCoordinatorPort(){
     @Override public ActionReceipt execute(ActionCommand command){return same.actions().execute(command);}
     @Override public ActionReceipt reconcile(String actionId){return same.actions().reconcile(actionId);}
    });
    var capabilities=new GuiCapabilities(actions,same.reads(),contracts);
    Optional<GuiService.InventoryRead> actualInventory=inventory.isPresent()?Optional.of(inventory.orElseThrow().create(same)):Optional.empty();
    require(presentation.isEmpty()&&observer.isEmpty(),"the actual registered physical GUI producer cannot be replaced by a caller callback");
    var physicalRuntime=new RootGuiPresentation(same,physicalSources);
    Optional<NativeCameraObserver> actualObserver=physicalRuntime.actualObserver();
    Optional<GuiService.PresentationPlane> actualPresentation=Optional.of(physicalRuntime);
    var service=new GuiService(capabilities,contracts,same.reads(),actions,()->same.archive().withSession(same.borrowedSession()),actualPresentation,actualInventory,actualObserver);
    var reads=new ArrayList<RootReadContractCatalog.InstalledRead>();for(var read:contracts.registered())reads.add(new RootReadContractCatalog.InstalledRead(read,decoderSource));reads.add(new RootReadContractCatalog.InstalledRead(frontendCensus,decoderSource));
    var installedActions=new ArrayList<RootExecutableBindings.ActionBinding>();var archived=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
    var steps=actionOperations();
    for(String step:steps){OperationKey operation=new OperationKey(step);ExactRef producer=step.equals("activate-ingame-decisions-v1")?serviceSource:actionSource;
     var effect=NativeEffectRegistry.Binding.existing(operation,producer,ports,ports);
     installedActions.add(new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of("game.command."+step),serviceSource));
     archived.add(new NativeRecordedEvidenceVerifier.Binding(operation,serviceSource,ports::replay));}
    Set<FrontendRulesData.Route> routes=EnumSet.allOf(FrontendRulesData.Route.class);routes.remove(FrontendRulesData.Route.UNAVAILABLE);
    var admission=new FrontendRouteAdmission(frontendCensus.operation(),routes,FrontendRouteAdmission.FrameMode.MENU,serviceSource);
    RootDomainInstallation installation=new RootDomainInstallation("original-public-gui",List.of(),reads,List.of(),installedActions,List.of(),archived,List.of(),List.of(),List.of(admission),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
    var navAction=installedActions.stream().filter(b->b.effect().operation().value().equals("navigate-ingame-ui-v1")).findFirst().orElseThrow();
    var navReplay=archived.stream().filter(b->b.operation().value().equals("navigate-ingame-ui-v1")).findFirst().orElseThrow();
    var installedNavigation=new ArrayList<InstalledNavigation>();for(int i=0;i<navigation.size();i++)installedNavigation.add(new InstalledNavigation(same,navigation.get(i),extensions.get(i),navAction,navReplay));
    attempt.installed=new Installed(same,installation,service,contracts,frontendCensus,installedNavigation,physicalRuntime,physical.getFirst());return attempt.installed;
   }catch(IOException failure){attempt.failure=failure;throw failure;}catch(RuntimeException failure){attempt.failure=new IOException("actual GUI installation failed",failure);throw attempt.failure;}
  }
 }
 private static final class Attempt{private Installed installed;private IOException failure;}
 public static final class Installed implements AutoCloseable{
  private final RootRuntimeContext context;private final RootDomainInstallation installation;private final GuiService service;private final GuiReads contracts;private final ReadContract<GuiModels.WindowTree> frontendCensus;private final List<InstalledNavigation> navigationBindings;private final RootGuiPresentation presentationRuntime;private final PhysicalActionRegistry.Binding physicalBinding;private boolean closed;
  private Installed(RootRuntimeContext context,RootDomainInstallation installation,GuiService service,GuiReads contracts,ReadContract<GuiModels.WindowTree> frontendCensus,List<InstalledNavigation> navigationBindings,RootGuiPresentation presentationRuntime,PhysicalActionRegistry.Binding physicalBinding){this.context=context;this.installation=installation;this.service=service;this.contracts=contracts;this.frontendCensus=frontendCensus;this.navigationBindings=List.copyOf(navigationBindings);this.presentationRuntime=Objects.requireNonNull(presentationRuntime);this.physicalBinding=Objects.requireNonNull(physicalBinding);}
  public RootAutoCamera automaticCamera(){return presentationRuntime.automaticCamera();}
  public PhysicalActionRegistry.Binding physicalBinding(){return physicalBinding;}
  public boolean matchesPhysical(ActionCommand command){return !closed&&presentationRuntime.matchesCommand(command);}
  @Override public synchronized void close()throws IOException{if(closed)return;closed=true;presentationRuntime.close();}
  public List<InstalledNavigation> navigationBindings(){return navigationBindings;}
  public RootDomainInstallation installation(){return installation;}public GuiService service(){return service;}public GuiReads contracts(){return contracts;}
  public void requireContext(RootRuntimeContext same)throws IOException{if(closed||context!=same)throw new IOException("GUI products are closed or crossed their actual per-Game context");}
 }
 public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context actual,PublicBindings registry)throws IOException{
  Objects.requireNonNull(actual);Objects.requireNonNull(registry);ExactRef source=actual.source(RootGuiPublicProducts.class);
  var bindings=bindings(request->invoke(actual,request),source);
  // These are concrete missing producer prerequisites; all other exact handlers above execute their real installed algorithms.
  var original=actual.definitions().additionalDomains().gui();var gaps=new ArrayList<RootRuntimePublicCatalog.DefinitionGap>();
  if(!original.hasPresentationDefinition()){
   gaps.add(new RootRuntimePublicCatalog.DefinitionGap("ck3_center_map_on_player_realm_v1","sole durable native mmap presentation origin/dispatch/archive is not yet installed"));
   gaps.add(new RootRuntimePublicCatalog.DefinitionGap("ck3_query_player_realm_map_bounds_v1","original query queues native mmap presentation and needs the same missing durable plane"));}
  if(!original.hasInventoryDefinition())gaps.add(new RootRuntimePublicCatalog.DefinitionGap("ck3_query_ingame_ui_window_v1","original inventory branch requires the same installed internal artifact inventory query"));
  return new RootPublicHandlerProductsFactory.Contribution(new ArrayList<>(bindings),List.of(),gaps);
 }
 @FunctionalInterface public interface Handler{RawJson invoke(GuiContract.Request request)throws InterruptedException;}
 /** Production and full original descriptor regressions use this identical typed route list. */
 public static List<McpExecutableDirectory.DirectBinding<GuiContract.Request,RawJson>> bindings(Handler actual,ExactRef source){
  Objects.requireNonNull(actual);Objects.requireNonNull(source);var bindings=new ArrayList<McpExecutableDirectory.DirectBinding<GuiContract.Request,RawJson>>();
  for(GuiContract.Method method:GuiContract.Method.values())bindings.add(new McpExecutableDirectory.DirectBinding<>(
   method.originalName(),PublicMcpBindings.Kind.DRIVER_DIRECT,GuiContract.Request.class,RawJson.class,
   actual::invoke,call->GuiCodec.decode(method.originalName(),call.arguments().objectOrEmpty()),PublicMcpDirectory.CallResult::fromBusinessJson,
   new PublicRoutes.Target(RootGuiPublicProducts.class.getName(),"invoke",source)));
  return List.copyOf(bindings);
 }
 public static RawJson invoke(RootPublicHandlerProductsFactory.Context context,GuiContract.Request request)throws InterruptedException{
  Objects.requireNonNull(context);Objects.requireNonNull(request);Instant deadline=context.clock().instant().plus(request.submitsAction()?context.actionTimeout():context.observationTimeout());
  try{
   if(request.method()==GuiContract.Method.CAMERA_STATUS)return context.withInstalledData(deadline,(actual,same)->{var gui=actual.additionalDomains().gui();gui.requireContext(actual.context());actual.context().writer().requireSession(same);var status=StrictJson.parse(GuiCodec.encode(gui.service().cameraStatus()).bytes());
    require(status.isObject(),"actual camera status object required");((com.fasterxml.jackson.databind.node.ObjectNode)status).set("auto_camera_follow",StrictJson.parse(gui.automaticCamera().status().bytes()));
    return new RawJson(StrictJson.canonical(status));});
   if(request.method()==GuiContract.Method.TREE)return context.withActualReadView(deadline,root->{var actual=context.installed(root);var gui=actual.additionalDomains().gui();return root.withPublicObservation(deadline,(frame,known,same)->invokeObserved(gui,actual.context(),frame,request,deadline));},(actual,menu,lease)->invokeFrontend(actual,menu,lease,request,deadline));
   return context.withCurrent(root->{
   var installed=context.installed(root);var gui=installed.additionalDomains().gui();gui.requireContext(installed.context());
   if(request.method()==GuiContract.Method.CENTER_REALM||request.method()==GuiContract.Method.QUERY_BOUNDS)return GuiCodec.encode(gui.presentationRuntime.execute(root,request,deadline));
   if(request.submitsAction()){
    var retained=new java.util.concurrent.atomic.AtomicReference<PublicBefore>();
    return root.executePublicDecision(deadline,(frame,known,same)->{
     var invocation=observedInvocation(installed.context(),frame,deadline);
     requireWhiteFrame(request,frame);
     if(request.method()==GuiContract.Method.WHITE_AGE||request.method()==GuiContract.Method.WHITE_NUMERIC){
      installed.context().core().actions().withFrozen(same,lease->{requireWhiteIntentUnclaimed(request,invocation.nativeContext(),lease.snapshot().actions());lease.assertCurrent();return null;});
     }
     require(retained.compareAndSet(null,publicBefore(frame,invocation.nativeContext())),"GUI public before can be retained only once");
     return new RootApplicationSession.SubmitPublicAction<RawJson>(gui.service().prepareAction(request,invocation));},
     (receipt,archive,same)->presentAction(gui,request,Objects.requireNonNull(retained.get(),"actual retained GUI before absent"),receipt,archive,same));
   }
   return root.withPublicObservation(deadline,(frame,known,same)->invokeObserved(gui,installed.context(),frame,request,deadline));
  });}catch(IOException unavailable){throw new UncheckedIOException("actual original GUI service unavailable; UNKNOWN is never replayed",unavailable);}
 }

 private record PublicBefore(DriverObservationAssembler.Complete actual,GuiPublicBinder.Before publicData){
  private PublicBefore{Objects.requireNonNull(actual);Objects.requireNonNull(publicData);require(actual.identity().equals(publicData.context().before()),"GUI retained public before identity differs");}
 }
 private static PublicBefore publicBefore(DriverObservationAssembler.Complete actual,GuiModels.Context context){
  var original=DriverPublicContext.from(actual);
  return new PublicBefore(actual,new GuiPublicBinder.Before(context,GuiPublicMetadata.beforeSource(original.snapshot(),original.diagnostics())));
 }
 private static Optional<RawJson> parsedReturn(Installed gui,NativeActionPort.AckReceived ack,PublicBefore before,
   org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException{
  var outbound=ack.outbound().orElseThrow(()->new IOException("actual UI original outbound absent"));
  if(!Set.of("navigate-ingame-ui-v1","query-ingame-ui-window-v1").contains(org.xar.ck3.control.nativebridge.NativeWire.decodeExecuteRequest(outbound.originalPacket()).step()))return Optional.empty();
  var original=NativeUiParsedReturn.encode(outbound.originalPacket(),ack.originalPacket(),before.actual().semantic());
  return Optional.of(preserveParsedReturn(gui.context.archive(),same,original));
 }
 /** Actual Root persistence uses the same complete artifact decoder and bound for both IO directions. */
 static RawJson preserveParsedReturn(NativeOutcomeArchive archive,
   org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,RawJson original)throws IOException{
  Objects.requireNonNull(archive);Objects.requireNonNull(same);Objects.requireNonNull(original);
  NativeUiParsedReturn.decode(original.bytes());
  var reference=archive.preserveArtifact(same,original.bytes(),NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);
  byte[] reloaded=archive.readArtifact(same,reference,NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);
  NativeUiParsedReturn.decode(reloaded);
  require(Arrays.equals(original.bytes(),reloaded),"actual original UI parsed-return custody changed");
  return PublicDataJson.encode(NativeUiParsedReturn.reference(reference));
 }
 private static RawJson presentAction(Installed gui,GuiContract.Request request,PublicBefore before,ActionReceipt receipt,
   ActionPorts.OutcomeArchive archive,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException{
  var original=(GuiContract.ActionReply)gui.service().presentAction(receipt);
  if(receipt.ack().isPresent()){
   ActionState.Attempt attempt=switch(receipt.state()){
    case ActionState.Settled value->value.attempt();case ActionState.Unknown value->value.attempt().orElseThrow();
    case ActionState.AckReceived value->value.attempt();case ActionState.Submitting value->value.attempt();
    default->throw new IOException("actual GUI ACK has no original attempt");};
   var ack=receipt.ack().orElseThrow();ack.custody().orElseThrow(()->new IOException("actual GUI ACK custody absent")).verify(ack,attempt.guard());
   var reconstructed=RootGuardEvidence.loadFrame(attempt.guard(),archive,gui.context.frameLoader());
   require(reconstructed.identity().equals(before.actual().identity())&&reconstructed.fullBindingSha256().equals(before.actual().fullBindingSha256()),"GUI original action crossed its retained before frame");
  }
  Optional<RawJson> parsed=receipt.ack().isPresent()?parsedReturn(gui,receipt.ack().orElseThrow(),before,same):Optional.empty();
  var reply=new GuiContract.ActionReply(original.receipt(),original.archivedReceipt(),original.originalReference(),Optional.of(before.publicData().source()),parsed);
  Optional<RawJson> later=Optional.empty(),after=Optional.empty();
  if(GuiDecisionPublicFormatter.supports(request.method())&&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED){
   require(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied,"GUI successful decision requires actual independent ControlApplied");
   var control=(ActionState.ControlApplied)((ActionState.Settled)receipt.state()).settlement();
   var read=control.read();ExactRef reference=archive.readReferenceOf(read);
   require(archive.loadRead(reference).equals(read),"GUI later READ original changed");
   later=Optional.of(GuiCodec.encode(new GuiContract.ReadReply(read,reference,Optional.empty(),Optional.empty())));
   if(request.method()==GuiContract.Method.CONFIRM_OUTCOME)after=Optional.of(freshOutcomeSnapshot(gui,receipt,before,same));
  }
  return GuiPublicBinder.action(request,reply,before.publicData(),later,after,whiteEvidence(request,receipt,gui.contracts,archive));
 }
 static Optional<GuiFaithWhitePublicFormatter.WhiteEvidence> whiteEvidence(GuiContract.Request request,
   ActionReceipt receipt,GuiReads contracts,ActionPorts.OutcomeArchive archive){
  if(request.method()!=GuiContract.Method.WHITE_AGE&&request.method()!=GuiContract.Method.WHITE_NUMERIC)return Optional.empty();
  var before=GuiWhiteOriginals.before(receipt.command(),contracts,archive);
  Optional<ActionState.ControlApplied> after=Optional.empty();
  if(receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED){
   require(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied,"actual White double-READ settlement absent");
   var settled=(ActionState.Settled)receipt.state();var control=(ActionState.ControlApplied)settled.settlement();
   require(control.supportingReads().size()==1,"White requires exactly business/text after READs");
   var ack=receipt.ack().orElseThrow();GuiWhiteOriginals.requireBeforeSubmission(before,settled.attempt(),ack);
   var c=GuiReads.context(receipt.command());
   NativeRecordedEvidenceVerifier.requireRead(control.read(),archive);NativeRecordedEvidenceVerifier.requireRead(control.supportingReads().getFirst(),archive);
   NativeRequestChronology.requireSampledAfter(control.read(),settled.attempt(),ack);NativeRequestChronology.requireSampledAfter(control.supportingReads().getFirst(),settled.attempt(),ack);
   var business=GuiWhiteOriginals.requireRole(control.read(),c,contracts.whiteBusiness);
   var text=GuiWhiteOriginals.requireRole(control.supportingReads().getFirst(),c,contracts.whiteText);
   var actual=GuiWhiteOriginals.actual(GuiService.argumentFields(receipt.command()),business,text,receipt.command().operation().value());
   require(control.equals(new ActionState.ControlApplied(control.read(),control.supportingReads(),GuiCapabilities.OBSERVER,actual)),"White original double-READ settlement changed its actual values");after=Optional.of(control);
  }
  return Optional.of(new GuiFaithWhitePublicFormatter.WhiteEvidence(before,after));
 }
 /** DATA predicate; the caller owns the actual frozen canonical head and its source/current checks. */
 static void requireWhiteIntentUnclaimed(GuiContract.Request request,GuiModels.Context context,List<ActionReceipt> actualCanonical){
  require(request.method()==GuiContract.Method.WHITE_AGE||request.method()==GuiContract.Method.WHITE_NUMERIC,"fixed original White action required");
  String identity=GuiService.actionId(request,context);
  require(List.copyOf(actualCanonical).stream().noneMatch(r->r.command().actionId().equals(identity)),"White action intent already claimed; result unknown or complete, no retry");
 }
 /** One explicit fresh full-state READ. A missing or unknown result is retained by transport and never retried here. */
 private static RawJson freshOutcomeSnapshot(Installed gui,ActionReceipt setter,PublicBefore before,
   org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException{
  gui.context.writer().requireSession(same);
  var acknowledgement=setter.ack().orElseThrow(()->new IOException("GUI outcome has no original native acknowledgement"));
  var deadline=before.publicData().context().deadline();
  try{
   var result=gui.context.transport().readFreshFullState(deadline);
   if(!(result instanceof NativeFreshSnapshotPort.Received received))
    throw new IOException("GUI outcome fresh full-state READ unavailable; do not retry: "+((NativeFreshSnapshotPort.Unavailable)result).reason());
   NativeFreshSnapshotPort.verifyAfter(acknowledgement,received);
   var actual=gui.context.adopted().observations().project(received.originalFrame(),deadline);
   require(actual.source().equals(before.actual().source())&&actual.sessionId().equals(before.actual().sessionId())
     &&actual.identity().game().equals(before.actual().identity().game()),"GUI fresh outcome changed physical source/session");
   return DriverPublicContext.from(actual).snapshot();
  }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("GUI outcome fresh full-state READ interrupted; do not retry",interrupted);}
 }
 private static RawJson invokeFrontend(RootInstalledCatalog actual,RootMenuSession menu,FrontendAuthority.LeaseSnapshot lease,GuiContract.Request request,Instant deadline)throws IOException{
  var same=actual.context();var gui=actual.additionalDomains().gui();gui.requireContext(same);
  require(same.core().requireFrontendMenu(same)==menu&&menu.frontend==same.frontend().authority()&&lease.source().equals(same.source())&&lease.identity().frontendSessionId().equals(same.game().sessionId()),"GUI frontend crossed actual Core/menu/source/session");
  String window=((GuiContract.TreeQuery)request.arguments()).kind().wire();var fields=StrictJson.object().put("window_kind",window);
  var query=new PlanningReadRequest(new CommandOrigin.Frontend(lease.identity()),lease.source(),lease.identity().frontendSessionId(),gui.frontendCensus.operation(),GuiService.arguments(fields),deadline);
  var result=menu.read(gui.frontendCensus,query);if(!(result instanceof PlanningReadResult.Known<GuiModels.WindowTree> known))throw new IOException(((PlanningReadResult.Unavailable<GuiModels.WindowTree>)result).reason());
  return same.withSession(borrowed->{var archive=same.archive().withSession(borrowed);require(archive.readReferenceOf(known.receipt()).equals(known.originalReceipt())&&archive.loadRead(known.originalReceipt()).equals(known.receipt()),"GUI frontend original read changed");return GuiCodec.encode(new GuiContract.ReadReply(known.receipt(),known.originalReceipt(),Optional.empty(),Optional.empty()));});
 }
 /** Same original wire operation, separate exact origin/contract. No alias or gameplay frame is created. */
 public static ReadContract<GuiModels.WindowTree> frontendCensus(ExactRef original){
  return new ReadContract<>("gui:frontend:inspect-gui-window-tree-v1",new OperationKey("inspect-gui-window-tree-v1"),Optional.of("game.command.inspect-gui-window-tree-v1"),"original-native-frontend-census",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.FRONTEND_SESSION,original,
   request->{ObjectNodeFields.validateWindow(request.arguments());return new NativeRequest("inspect-gui-window-tree-v1","game.command.inspect-gui-window-tree-v1",new RawJson(OpportunityJson.encode(request.arguments())));},
   receipt->{var args=(com.fasterxml.jackson.databind.node.ObjectNode)OpportunityJson.toNode(receipt.request().arguments());GuiModels.TreeKind kind=GuiModels.TreeKind.parse(StrictJson.text(args.get("window_kind")));return GuiDecoders.windowTree(org.xar.ck3.control.application.driver.PublicDataJson.object(receipt.original().originalResultToken().orElseThrow()),kind);});
 }
 private static final class ObjectNodeFields{private static void validateWindow(OpportunityJson.Obj fields){var node=StrictJson.object(OpportunityJson.toNode(fields),Set.of("window_kind"));GuiModels.TreeKind.parse(StrictJson.text(node.get("window_kind")));}}
 private static RawJson invokeObserved(Installed installed,RootRuntimeContext same,DriverObservationAssembler.Complete frame,GuiContract.Request request,Instant deadline)throws IOException{
  installed.requireContext(same);var invocation=observedInvocation(same,frame,deadline);var before=publicBefore(frame,invocation.nativeContext());
  requireWhiteFrame(request,frame);
  var result=installed.service().invoke(request,invocation);
  if(!(result instanceof GuiContract.ReadReply original))return GuiCodec.encode(result);
  NativeRecordedEvidenceVerifier.requireRead(original.receipt(),same.archive().withSession(same.borrowedSession()));
  Optional<RawJson> parsed=parsedReturn(installed,original.receipt().original(),before,same.borrowedSession());
  var reply=new GuiContract.ReadReply(original.receipt(),original.originalReference(),Optional.of(before.publicData().source()),parsed);
  return GuiPublicBinder.read(request,reply,Optional.of(before.publicData()));
 }
 private static GuiService.Invocation observedInvocation(RootRuntimeContext same,DriverObservationAssembler.Complete frame,Instant deadline)throws IOException{
  same.writer().requireSession(same.borrowedSession());same.requireCurrent(deadline);
  require(frame.source().equals(same.source())&&frame.sessionId().equals(same.game().sessionId())&&frame.identity().game().equals(same.game().generation()),"GUI public frame crossed actual Root owner");
  var hello=same.transport().originalHello();require(hello.pid()==frame.identity().game().pid()&&hello.connectionGeneration().equals(frame.connectionGeneration())&&hello.buildMatch(),"GUI original HELLO differs from actual frame");
  GuiModels.Build build=Arrays.stream(GuiModels.Build.values()).filter(value->value.sha256().equals(hello.gameSha256())).findFirst().orElseThrow(()->new IOException("GUI executable has no source-qualified exact profile"));
  GuiModels.Context c=new GuiModels.Context(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),build,deadline);
  return new GuiService.Invocation(c,frame.identity().frame().revision(),flag(frame,"paused"),flag(frame,"map_ready"));
 }
 private static boolean flag(DriverObservationAssembler.Complete actual,String name){return actual.semantic().get(name) instanceof OpportunityJson.Bool b&&b.value();}
 private static void requireWhiteFrame(GuiContract.Request request,DriverObservationAssembler.Complete actual){
  if(!GuiFaithWhitePublicFormatter.white(request.method()))return;
  var snapshot=actual.semantic();require(snapshot.members().containsKey("active_event")&&snapshot.get("active_event")==OpportunityJson.Nil.INSTANCE,"original White requires an actual no-event frame");
  require(snapshot.get("episode_run_id") instanceof OpportunityJson.Text run&&!run.value().isBlank(),"original White requires actual nonempty episode identity");
  var player=OpportunityJson.object(snapshot.get("played_character"),"played_character");require(player.get("alive") instanceof OpportunityJson.Bool alive&&alive.value(),"original White requires actual alive player");
 }
 private static ExactRef source(Path path)throws IOException{var observed=SharedSourceFiles.observe(path);SharedSourceFiles.assertUnchanged(observed);var original=observed.source();return new ExactRef(original.path(),original.bytes(),original.sha256());}
 private static void requireSame(ExactRef expected)throws IOException{var observed=source(Path.of(expected.path()));if(observed.bytes()!=expected.bytes()||!observed.sha256().equals(expected.sha256()))throw new IOException("actual GUI original source changed: "+expected.path());}
}


