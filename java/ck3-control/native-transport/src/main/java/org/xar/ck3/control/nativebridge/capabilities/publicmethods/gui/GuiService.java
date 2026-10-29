package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.gui.*;
import org.xar.ck3.control.nativebridge.publicmethods.gui.GuiRealmCameraStatus;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Per-Game public business service. All writes use the supplied sole Root coordinator. */
public final class GuiService {
 public record Invocation(GuiModels.Context nativeContext,BigInteger publicRevision,boolean paused,boolean mapReady){
  public Invocation{Objects.requireNonNull(nativeContext);Objects.requireNonNull(publicRevision);require(publicRevision.signum()>=0,"actual public revision");}
 }
 /** A distinct presentation plane needs its real registered durable origin, not a pipe-shaped stand-in. */
 public interface PresentationPlane {
  Reply submit(Invocation frame,boolean queryOnly)throws IOException;
  Optional<GuiRealmCameraStatus.Submission> originalSubmission();
  Optional<NativeCameraObserver> actualObserver();
  GuiRealmCameraStatus.Owner currentOwner()throws IOException;
 }
 @FunctionalInterface public interface InventoryRead {Reply query(Invocation frame)throws IOException;}
 public record NavigationSelector(String windowKind,String operation){
  public NavigationSelector{require(windowKind!=null&&windowKind.matches("[a-z_]{1,64}")&&operation!=null&&operation.matches("[a-z_]{1,96}"),"finite native GUI selector");}}
 public record NavigationExtension(Set<NavigationSelector> selectors,ActionPorts.PreparationPort preparation,
   ActionPorts.PostconditionPort observation,NativeRecordedEvidenceVerifier.ArchivedVerifier replay,ExactRef source){
  public NavigationExtension{selectors=Set.copyOf(selectors);require(!selectors.isEmpty()&&selectors.size()<=32,"bounded actual selector extension");Objects.requireNonNull(preparation);Objects.requireNonNull(observation);Objects.requireNonNull(replay);Objects.requireNonNull(source);}}
 private final GuiCapabilities capabilities;private final GuiReads contracts;private final PlanningReadPort reads;
 @FunctionalInterface public interface CurrentArchive{ActionPorts.OutcomeArchive current()throws IOException;}
 private final ActionCoordinatorPort actions;private final CurrentArchive archives;
 private final Optional<PresentationPlane> presentation;private final Optional<InventoryRead> inventory;
 private final Optional<NativeCameraObserver> observer;
 public GuiService(GuiCapabilities capabilities,GuiReads contracts,PlanningReadPort reads,ActionCoordinatorPort actions,
   CurrentArchive archives,Optional<PresentationPlane> presentation,Optional<InventoryRead> inventory,Optional<NativeCameraObserver> observer){
  this.capabilities=Objects.requireNonNull(capabilities);this.contracts=Objects.requireNonNull(contracts);this.reads=Objects.requireNonNull(reads);
  this.actions=Objects.requireNonNull(actions);this.archives=Objects.requireNonNull(archives);this.presentation=Objects.requireNonNull(presentation);
  this.inventory=Objects.requireNonNull(inventory);this.observer=Objects.requireNonNull(observer);
  presentation.ifPresent(p->require(p.actualObserver().isPresent()==observer.isPresent()&&(observer.isEmpty()||p.actualObserver().orElseThrow()==observer.orElseThrow()),"presentation status must retain the identical actual observer"));}
 public GuiCapabilities capabilities(){return capabilities;}public GuiReads contracts(){return contracts;}
 /** A preparation-only interception returns the real command before any canonical writer append. */
 public static ActionCoordinatorPort captureCapable(ActionCoordinatorPort actual){return new CapturePort(actual);}
 private static final class CapturedCommand extends RuntimeException{
  @java.io.Serial private static final long serialVersionUID=1L;
  // In-process preparation unwinding retains the original command; Java serialization carries no domain authority.
  private final transient ActionCommand command;
  private CapturedCommand(ActionCommand command){super(null,null,false,false);this.command=command;}
 }
 private static final class CapturePort implements ActionCoordinatorPort{
  private final ActionCoordinatorPort actual;private final ThreadLocal<Boolean> preparing=new ThreadLocal<>();
  private CapturePort(ActionCoordinatorPort actual){this.actual=Objects.requireNonNull(actual);}
  @Override public ActionReceipt execute(ActionCommand command){if(Boolean.TRUE.equals(preparing.get()))throw new CapturedCommand(Objects.requireNonNull(command));return actual.execute(command);}
  @Override public ActionReceipt reconcile(String actionId){require(!Boolean.TRUE.equals(preparing.get()),"preparation cannot reconcile or fabricate an existing outcome");return actual.reconcile(actionId);}
  private ActionCommand prepare(GuiService service,Request request,Invocation frame)throws IOException{
   require(preparing.get()==null,"GUI preparation cannot nest or replace another captured command");preparing.set(true);
   try{service.invoke(request,frame);throw new IllegalStateException("actual mutating GUI producer returned no command");}
   catch(CapturedCommand captured){return captured.command;}finally{preparing.remove();}
  }
 }
 public ActionCommand prepareAction(Request request,Invocation frame)throws IOException{
  require(request.submitsAction()&&request.method()!=Method.CENTER_REALM,"physical presentation uses its independent registered producer");
  require(actions instanceof CapturePort,"GUI action preparation requires its original capture-capable Root port");
  return ((CapturePort)actions).prepare(this,request,frame);
 }
 public Reply presentAction(ActionReceipt actual)throws IOException{return action(Objects.requireNonNull(actual));}

 public Reply invoke(Request request,Invocation frame)throws IOException{
  Objects.requireNonNull(request);Objects.requireNonNull(frame);
  if(request.expectedRevision() instanceof PublicUnsigned64.Value revision)require(revision.value().equals(frame.publicRevision()),"original GUI expected_revision differs from current public revision");
  // The census/status original routes have no paused-frame argument. Root still owns their source.
  if(request.method()!=Method.TREE&&request.method()!=Method.CAMERA_STATUS)require(frame.paused()&&frame.mapReady(),"original GUI requires actual paused map-ready frame");
  GuiModels.Context c=frame.nativeContext();GuiModels.Intent i=new GuiModels.Intent(c,actionId(request,c));Arguments a=request.arguments();
  return switch(request.method()){
   case CENTER_TITLE->action(capabilities.center_map_on_landed_title_v1(i,((Title)a).key()));
   case CENTER_REALM,QUERY_BOUNDS->presentation.orElseThrow(()->new IOException("MIGRATION_GAP: sole durable native presentation plane has not been installed")).submit(frame,request.method()==Method.QUERY_BOUNDS);
   case CAMERA_STATUS->cameraStatus();
   case OPEN_CHARACTER->action(capabilities.open_character_window_v1(i,((Subject)a).value()));
   case OPEN_FAITH->action(capabilities.open_faith_window_v1(i,((Subject)a).value()));
   case SELECT_ARMY->action(capabilities.select_army_ui_v1(i,((Subject)a).value()));
   case OPEN_COMBAT->action(capabilities.open_combat_window_v1(i,((Subject)a).value()));
   case FIT_COMBAT->action(capabilities.fit_combat_window_v1(i,((Subject)a).value()));
   case OPEN_KNIGHTS->action(capabilities.open_knights_window_v1(i));
   case HOVER_KNIGHTS->{KnightHover h=(KnightHover)a;yield action(capabilities.hover_combat_knights_v1(i,h.combat(),h.side()));}
   case HOVER_ARMY->{ArmyTooltip t=(ArmyTooltip)a;yield action(capabilities.hover_army_tooltip_v1(i,t.army(),t.kind()));}
   case LEAVE_ARMY->{ArmyTooltip t=(ArmyTooltip)a;yield action(capabilities.leave_army_tooltip_v1(i,t.army(),t.kind(),optional(t.receipt()).orElseThrow()));}
   case QUERY_ARMY->{ArmyTooltip t=(ArmyTooltip)a;yield read(capabilities.query_army_tooltip_v1(c,t.army(),t.kind(),optional(t.receipt()).orElseThrow()));}
   case QUERY_WINDOW->{String kind=((WindowQuery)a).kind();yield kind.equals("inventory")?inventory.orElseThrow(()->new IOException("actual same-Root inventory reader not installed")).query(frame):read(capabilities.query_ingame_ui_window_v1(c,GuiModels.WindowKind.parse(kind)));}
   case TREE->read(capabilities.inspect_gui_window_tree_v1(c,((TreeQuery)a).kind()));
   case QUERY_DECISION->read(capabilities.query_ingame_decision_item_v1(c,((Decision)a).key()));
   case SELECT_DECISION->action(capabilities.select_ingame_decision_item_v1(i,((Decision)a).key()));
   case CONFIRM_ITEM->{ConfirmItem v=(ConfirmItem)a;yield action(capabilities.confirm_ingame_decision_item_v1(i,v.key(),v.window()));}
   case CONFIRM_OUTCOME->{ConfirmOutcome v=(ConfirmOutcome)a;yield action(capabilities.confirm_ingame_decision_outcome_v1(i,v.key(),v.outcome(),optional(v.eventDefinition())));}
   case WHITE_AGE->{WhiteAge v=(WhiteAge)a;yield action(capabilities.click_white_control_v1(i,v.before(),v.intentId()));}
   case WHITE_NUMERIC->{WhiteNumeric v=(WhiteNumeric)a;yield action(capabilities.click_white_numeric_control_v1(i,v.control(),v.before(),v.price(),v.intentId()));}
   case WHITE_BUSINESS->read(capabilities.query_white_player_business_variables_v1(c));
   case WHITE_TEXT->read(capabilities.query_white_rendered_text_v1(c));
   case PRESENT,QUERY_PRESENT,QUERY_PRESENT_TOOLTIP->{var actual=capabilities.present_faith_power_ui_v1(i,((Presentation)a).nativeRequest(request.method()));
    yield actual instanceof GuiCapabilities.PresentationRead r?read(r.result()):action(((GuiCapabilities.PresentationAction)actual).result());}
   case OPEN_DECISIONS->action(openDecisions(i));
  };
 }
 private Reply read(PlanningReadResult<?> result)throws IOException{
  ActionPorts.OutcomeArchive archive=archives.current();
  if(!(result instanceof PlanningReadResult.Known<?> known))throw GuiReadFailure.from((PlanningReadResult.Unavailable<?>)result);
  require(archive.readReferenceOf(known.receipt()).equals(known.originalReceipt())&&archive.loadRead(known.originalReceipt()).equals(known.receipt()),"GUI actual original read is absent or changed");
  return new ReadReply(known.receipt(),known.originalReceipt(),Optional.empty(),Optional.empty());
 }
 private ActionReply action(ActionReceipt receipt)throws IOException{ActionPorts.OutcomeArchive archive=archives.current();byte[] canonical=ActionReceiptCodec.encodeReceipt(receipt,archive);ActionReceipt reloaded=ActionReceiptCodec.decodeReceipt(canonical,archive);
  require(Arrays.equals(canonical,ActionReceiptCodec.encodeReceipt(reloaded,archive)),"canonical GUI action original roundtrip changed");ExactRef original=archive.preserveMaterial(new RawJson(canonical));require(Arrays.equals(canonical,archive.loadMaterial(original).bytes()),"actual canonical GUI receipt material changed");return new ActionReply(receipt,canonical,original,Optional.empty(),Optional.empty());}
 public static String actionId(Request request,GuiModels.Context source){
  String intent=request.arguments() instanceof WhiteAge a?a.intentId():request.arguments() instanceof WhiteNumeric a?a.intentId():null;
  if(intent==null)return "gui-"+UUID.randomUUID();
  String original=source.before().machineId()+"|"+source.before().game()+"|"+source.before().frame().episodeRunId()+"|"+source.before().frame().identity().player()+"|"+intent;
  try{return "gui-white-"+java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(original.getBytes(java.nio.charset.StandardCharsets.UTF_8)));}catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
 }
 /** Original status has no fresh snapshot, paused, map-ready or action prerequisite. */
 public CameraReply cameraStatus()throws IOException{
  if(presentation.isEmpty())return new CameraReply(new GuiRealmCameraStatus.StatusData(observer.isPresent()?GuiRealmCameraStatus.Availability.AVAILABLE:GuiRealmCameraStatus.Availability.NOT_REQUESTED,java.util.OptionalLong.empty(),Optional.empty()));
  PresentationPlane plane=presentation.orElseThrow();var original=plane.originalSubmission();
  if(original.isEmpty())return new CameraReply(new GuiRealmCameraStatus.StatusData(GuiRealmCameraStatus.Availability.NOT_REQUESTED,java.util.OptionalLong.empty(),Optional.empty()));
  return new CameraReply(GuiRealmCameraStatus.query(observer,plane.currentOwner(),original));
 }
 private static GuiRealmCameraStatus.Owner owner(GuiModels.Context c){return new GuiRealmCameraStatus.Owner(c.before().frame().identity().player().intValueExact(),c.before().frame().episodeRunId(),c.before().game().pid(),c.connectionGeneration());}
 private ActionReceipt openDecisions(GuiModels.Intent intent){
  GuiModels.Context c=intent.frame();require(c.build()==GuiModels.Build.CROZIER3||c.build()==GuiModels.Build.CROZIER4,"original Decisions exact Crozier GUI profile required");
  ObjectNode fields=metadata(c);fields.put("expected_player_character_id",c.before().frame().identity().player()).put("expected_game_pid",c.before().game().pid()).put("expected_connection_generation",c.connectionGeneration());
  ExpectedPostcondition expected=new ExpectedPostcondition(1,c.before(),c.source(),GuiCapabilities.OBSERVER,List.of(new ExpectedBoolean(new FieldKey("gui.decisions_visible"),true)));
  Claims claims=new Claims(Set.of(),Set.of(),Set.of(c.before().frame().identity().player()),Set.of("native-gui"));
  return actions.execute(new ActionCommand(intent.actionId(),c.before(),c.source(),c.sessionId(),new OperationKey("activate-ingame-decisions-v1"),arguments(fields),expected,claims,c.deadline()));
 }
 public static ObjectNode metadata(GuiModels.Context c){return StrictJson.object().put("_gui_build",c.build().name()).put("_gui_generation",c.connectionGeneration());}
 public static OpportunityJson.Obj arguments(ObjectNode fields){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(fields)),"GUI command");}
 public static ObjectNode argumentFields(ActionCommand command){return (ObjectNode)OpportunityJson.toNode(command.arguments());}
 /** One installed binding routes only exact finite selectors; all other GUI commands retain their original producer. */
 public static final class NavigationPorts implements ActionPorts.PreparationPort,ActionPorts.PostconditionPort{
  private final GuiActions original;private final GuiReads contracts;private final PlanningReadPort reads;private final List<NavigationExtension> extensions;
  public NavigationPorts(GuiActions original,GuiReads contracts,PlanningReadPort reads,List<NavigationExtension> extensions){this.original=Objects.requireNonNull(original);this.contracts=Objects.requireNonNull(contracts);this.reads=Objects.requireNonNull(reads);this.extensions=List.copyOf(extensions);var seen=new HashSet<NavigationSelector>();for(var e:this.extensions)for(var s:e.selectors())require(seen.add(s),"two actual Nav extensions claim same selector");}
  private Optional<NavigationExtension> extension(ActionCommand command){
   if(!command.operation().value().equals("navigate-ingame-ui-v1"))return Optional.empty();ObjectNode a=argumentFields(command);
   NavigationSelector selector=new NavigationSelector(StrictJson.text(a.get("window_kind")),StrictJson.text(a.get("operation")));
   return extensions.stream().filter(e->e.selectors().contains(selector)).findFirst();}
  public NativeRequest prepare(ActionCommand command){return extension(command).map(e->e.preparation().prepare(command)).orElseGet(()->command.operation().value().equals("activate-ingame-decisions-v1")?prepareOpen(command):original.prepare(command));}
  @Override public NativeRequest prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ActionCommand command,String requestId){return extension(command).map(e->e.preparation().prepare(same,command,requestId)).orElseGet(()->prepare(command));}
  public ActionPorts.PostconditionResult observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
   Optional<NavigationExtension> extension=extension(command);if(extension.isPresent())return extension.orElseThrow().observation().observe(command,attempt,dispatch);
   if(!command.operation().value().equals("activate-ingame-decisions-v1"))return original.observe(command,attempt,dispatch);
   if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return new ActionPorts.Pending("Decisions original result unknown/rejected; do not replay",List.of());
   try{ObjectNode result=(ObjectNode)StrictJson.parse(ack.originalResultToken().orElseThrow().bytes(),65536);GuiModels.Context c=GuiReads.context(command);
    equal(result,"schema","ck3-ingame-decisions-open-v1");equal(result,"step","activate-ingame-decisions-v1");equal(result,"game_version",c.build().version());equal(result,"executable_sha256",c.build().sha256());
    equalInteger(result,"native_revision",c.before().frame().identity().nativeRevision());equalInteger(result,"connection_generation",c.connectionGeneration());equalInteger(result,"game_pid",BigInteger.valueOf(c.before().game().pid()));
    equalInteger(result,"played_character_id",c.before().frame().identity().player());equalInteger(result,"date_raw",c.before().frame().identity().dateRaw());
    for(String f:List.of("owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified","native_after_read"))require(result.path(f).isBoolean()&&result.path(f).booleanValue(),"actual Decisions "+f);
    for(String f:List.of("before_visible","dispatch_invoked","native_after_visible","native_after_tree_complete","postcondition_verified","verification_pending"))require(result.path(f).isBoolean(),"original Decisions boolean "+f);
    boolean dispatched=result.get("dispatch_invoked").booleanValue(),beforeVisible=result.get("before_visible").booleanValue();
    if(dispatched)require(!beforeVisible&&result.path("topbar_tree_complete").isBoolean()&&result.get("topbar_tree_complete").booleanValue()&&result.path("receiver_qualified").isBoolean()&&result.get("receiver_qualified").booleanValue(),"Decisions dispatch lacks actual HUD receiver proof");else require(beforeVisible,"Decisions neither already visible nor actually dispatched");
    boolean verified=result.get("native_after_tree_complete").booleanValue()&&result.get("native_after_visible").booleanValue();
    require(result.get("postcondition_verified").booleanValue()==verified&&result.get("verification_pending").booleanValue()==(dispatched&&!verified),"original Decisions same-call visibility/pending inconsistency");
    ObjectNode query=StrictJson.object().put("window_kind","decisions");var actual=contracts.read(reads,contracts.census,c,query);
    if(!(actual instanceof PlanningReadResult.Known<GuiModels.WindowTree> known))return new ActionPorts.Pending("Decisions independent later census unavailable; do not replay",List.of());
    return new ActionPorts.ControlObserved(new ActionState.ControlApplied(known.receipt(),GuiCapabilities.OBSERVER,List.of(new ExpectedBoolean(new FieldKey("gui.decisions_visible"),known.value().completeVisibleRoot()))));
   }catch(RuntimeException invalid){return new ActionPorts.Pending("Decisions independent actual observation unavailable: "+invalid.getMessage(),List.of());}
  }
  private NativeRequest prepareOpen(ActionCommand command){GuiModels.Context c=GuiReads.context(command);require(command.expected().observerSchema().equals(GuiCapabilities.OBSERVER),"original GUI observer required");require(c.build()==GuiModels.Build.CROZIER3||c.build()==GuiModels.Build.CROZIER4,"actual Crozier profile required");
   ObjectNode a=argumentFields(command);require(a.size()==5,"strict Decisions original fields");a.remove(List.of("_gui_build","_gui_generation"));
   equalInteger(a,"expected_player_character_id",c.before().frame().identity().player());equalInteger(a,"expected_game_pid",BigInteger.valueOf(c.before().game().pid()));equalInteger(a,"expected_connection_generation",c.connectionGeneration());
   return new NativeRequest("activate-ingame-decisions-v1","game.command.activate-ingame-decisions-v1",new RawJson(StrictJson.canonical(a)));}
  /** Replay invokes the exact original pure decoder and observer against immutable archived READs only. */
  public void replay(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
   Optional<NavigationExtension> extension=extension(receipt.command());if(extension.isPresent()){extension.orElseThrow().replay().verify(head,receipt,archive);return;}
   if(!(receipt.state() instanceof ActionState.Settled settled)||!(settled.settlement() instanceof ActionState.ControlApplied control))throw new IllegalArgumentException("GUI settlement requires its actual independent ControlApplied original");
   List<PlanningReadReceipt> originals=new ArrayList<>();originals.add(control.read());originals.addAll(control.supportingReads());
   PlanningReadPort historical=new PlanningReadPort(){public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
    List<PlanningReadReceipt> matches=originals.stream().filter(r->r.contractId().equals(contract.contractId())&&r.request().equals(request)).toList();
    require(matches.size()==1,"GUI archived observer requires exactly one original registered READ");var actual=matches.getFirst();
    NativeRecordedEvidenceVerifier.requireRead(actual,archive);return new PlanningReadResult.Known<>(contract.decode(actual),actual,archive.readReferenceOf(actual));}};
   if(receipt.command().operation().value().startsWith("click-white-"))require(control.supportingReads().size()==1,"White replay requires exactly business/text after READ roles");
   NavigationPorts replay=new NavigationPorts(new GuiActions(historical,contracts,()->archive),contracts,historical,List.of());
   var rebuilt=replay.observe(receipt.command(),settled.attempt(),settled.dispatch());
   require(rebuilt instanceof ActionPorts.ControlObserved observed&&observed.observation().equals(control),"GUI archived independent observer disagrees with canonical settlement");
  }
 }
 private static void equal(ObjectNode node,String field,String expected){require(node.has(field)&&node.get(field).isTextual()&&expected.equals(node.get(field).textValue()),"actual "+field+" binding");}
 private static void equalInteger(ObjectNode node,String field,BigInteger expected){require(node.has(field)&&node.get(field).isIntegralNumber()&&expected.equals(node.get(field).bigIntegerValue()),"actual integer "+field+" binding");}
}


