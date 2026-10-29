package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.nativebridge.publicmethods.gui.GuiRealmCameraStatus;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Exact original public names and typed arguments; DATA values grant no Native authority. */
public final class GuiContract {
 private GuiContract(){}
 public enum Method {
  CENTER_TITLE("center_map_on_landed_title_v1",true),CENTER_REALM("center_map_on_player_realm_v1",true),
  WHITE_AGE("click_white_control_v1",true),WHITE_NUMERIC("click_white_numeric_control_v1",true),
  CONFIRM_ITEM("confirm_ingame_decision_item_v1",true),CONFIRM_OUTCOME("confirm_ingame_decision_outcome_v1",true),
  FIT_COMBAT("fit_combat_window_v1",true),HOVER_ARMY("hover_army_tooltip_v1",true),HOVER_KNIGHTS("hover_combat_knights_v1",true),
  TREE("inspect_gui_window_tree_v1",false),LEAVE_ARMY("leave_army_tooltip_v1",true),
  OPEN_CHARACTER("open_character_window_v1",true),OPEN_COMBAT("open_combat_window_v1",true),OPEN_FAITH("open_faith_window_v1",true),
  OPEN_DECISIONS("open_ingame_decisions_v1",true),OPEN_KNIGHTS("open_knights_window_v1",true),
  PRESENT("present_faith_power_ui_v1",true),QUERY_ARMY("query_army_tooltip_v1",false),
  QUERY_PRESENT_TOOLTIP("query_faith_power_tooltip_v1",false),QUERY_PRESENT("query_faith_power_ui_v1",false),
  QUERY_WINDOW("query_ingame_ui_window_v1",false),QUERY_BOUNDS("query_player_realm_map_bounds_v1",true),
  WHITE_BUSINESS("query_white_player_business_variables_v1",false),WHITE_TEXT("query_white_rendered_text_v1",false),
  CAMERA_STATUS("realm_camera_status_v1",false),SELECT_ARMY("select_army_ui_v1",true),SELECT_DECISION("select_ingame_decision_item_v1",true),
  QUERY_DECISION("query_ingame_decision_item_v1",false);
  private final String name; private final boolean mutation;
  Method(String name,boolean mutation){this.name="ck3_"+name;this.mutation=mutation;}
  public String originalName(){return name;} public boolean mutation(){return mutation;}
  public static Method exact(String original){for(Method m:values())if(m.name.equals(original))return m;throw new IllegalArgumentException("unknown original GUI method");}
 }
 public sealed interface Slot<T> permits Absent,Null,Present { }
 public record Absent<T>() implements Slot<T>{}
 public record Null<T>() implements Slot<T>{}
 public record Present<T>(T value) implements Slot<T>{public Present{Objects.requireNonNull(value);}}
 public static <T> Optional<T> optional(Slot<T> slot){Objects.requireNonNull(slot);return slot instanceof Present<T> p?Optional.of(p.value()):Optional.empty();}
 public sealed interface Arguments permits Empty,Subject,ArmyTooltip,KnightHover,WindowQuery,TreeQuery,Title,Decision,ConfirmItem,ConfirmOutcome,WhiteAge,WhiteNumeric,Presentation { }
 public record Empty() implements Arguments{}
 public record Subject(GuiModels.Subject value) implements Arguments{public Subject{Objects.requireNonNull(value);}}
 public record ArmyTooltip(GuiModels.Subject army,GuiModels.TooltipKind kind,Slot<GuiModels.ReceiptId> receipt) implements Arguments{
  public ArmyTooltip{Objects.requireNonNull(army);Objects.requireNonNull(kind);Objects.requireNonNull(receipt);require(army.value().compareTo(BigInteger.valueOf(2147483647L))<=0,"public CUnit integer domain");}}
 public record KnightHover(GuiModels.Subject combat,GuiModels.Side side) implements Arguments{public KnightHover{positive(combat);Objects.requireNonNull(side);}}
 public record WindowQuery(String kind) implements Arguments{public WindowQuery{require(Set.of("character","army","combat","knights","holy_site","faith","holy_site_creation","holding","personal_beliefs","rite_creation","inventory").contains(kind),"original public window kind");}}
 public record TreeQuery(GuiModels.TreeKind kind) implements Arguments{public TreeQuery{Objects.requireNonNull(kind);}}
 public record Title(GuiModels.TitleKey key) implements Arguments{public Title{Objects.requireNonNull(key);}}
 public record Decision(GuiModels.DecisionKey key) implements Arguments{public Decision{Objects.requireNonNull(key);}}
 public record ConfirmItem(GuiModels.DecisionKey key,GuiModels.TreeKind window) implements Arguments{public ConfirmItem{Objects.requireNonNull(key);require(window==GuiModels.TreeKind.WHITE,"only fixed White original modal");}}
 public record ConfirmOutcome(GuiModels.DecisionKey key,GuiModels.Outcome outcome,Slot<String> eventDefinition) implements Arguments{
  public ConfirmOutcome{Objects.requireNonNull(key);Objects.requireNonNull(outcome);Objects.requireNonNull(eventDefinition);Optional<String> actual=optional(eventDefinition);
   require(outcome==GuiModels.Outcome.EVENT_WINDOW?actual.isPresent()&&eventDefinitionKey(actual.orElseThrow()):actual.map(String::isEmpty).orElse(true),"original declared event/closed outcome");}}
 public static boolean eventDefinitionKey(String value){return value!=null&&value.length()<=192&&value.matches("[A-Za-z_][A-Za-z0-9_]*\\.[0-9]{1,10}");}
 public record WhiteAge(int before,String intentId) implements Arguments{public WhiteAge{require(before>=0&&before<120,"White age before bound");intent(intentId);}}
 public record WhiteNumeric(GuiModels.NumericControl control,int before,String price,String intentId) implements Arguments{
  public WhiteNumeric{Objects.requireNonNull(control);require(before>=0&&before<100,"White numeric before bound");require(price!=null&&!price.isEmpty()&&price.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=2048,"original nonempty price bound");intent(intentId);}}
 public record Presentation(String operation,GuiModels.WindowKind window,Slot<GuiModels.Subject> subject,Slot<String> target,Slot<Integer> index,Slot<String> tab,Slot<GuiModels.ReceiptId> receipt) implements Arguments{
  public Presentation{Objects.requireNonNull(operation);Objects.requireNonNull(window);Objects.requireNonNull(subject);Objects.requireNonNull(target);Objects.requireNonNull(index);Objects.requireNonNull(tab);Objects.requireNonNull(receipt);
   require(Set.of("query","open_holding","open_personal_beliefs","close_presentation_window","select_presentation_tab","open_rite_core_picker","show_building_details","open_building_track","hover_presentation_tooltip","leave_presentation_tooltip","close_tooltips","open_clerical_preview","close_clerical_preview").contains(operation),"finite original presentation operation");
   optional(index).ifPresent(v->require(v>=0&&v<=127,"presentation index 0..127"));
   optional(tab).ifPresent(v->require(v.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=128,"presentation tab bound"));}
  public GuiModels.Presentation nativeRequest(){return nativeRequest(Method.PRESENT);}
  public GuiModels.Presentation nativeRequest(Method publicMethod){
   require(Set.of(Method.PRESENT,Method.QUERY_PRESENT,Method.QUERY_PRESENT_TOOLTIP).contains(publicMethod),"original presentation method required");
   Optional<String> actualTab=optional(tab);
   if(operation.equals("query")&&publicMethod==Method.QUERY_PRESENT){
    if(actualTab.isEmpty())actualTab=Optional.of("");
    if(Set.of(GuiModels.WindowKind.CLERICAL_INTERACTION,GuiModels.WindowKind.TOOLTIPS).contains(window)&&actualTab.filter(String::isEmpty).isPresent())actualTab=Optional.empty();}
   if(operation.equals("query")&&window!=GuiModels.WindowKind.TOOLTIPS&&actualTab.isEmpty()
       &&optional(target).isEmpty()&&optional(index).isEmpty()&&optional(receipt).isEmpty())actualTab=Optional.of("");
   return new GuiModels.Presentation(operation,window,optional(subject).orElse(new GuiModels.Subject(0)),optional(target),optional(index),actualTab,optional(receipt));}

 }
 public record Request(Method method,Arguments arguments,PublicUnsigned64.Field expectedRevision){
  public Request{Objects.requireNonNull(method);Objects.requireNonNull(arguments);Objects.requireNonNull(expectedRevision);
   boolean matches=switch(method){
    case CENTER_TITLE->arguments instanceof Title;
    case WHITE_AGE->arguments instanceof WhiteAge;case WHITE_NUMERIC->arguments instanceof WhiteNumeric;
    case CONFIRM_ITEM->arguments instanceof ConfirmItem;case CONFIRM_OUTCOME->arguments instanceof ConfirmOutcome;
    case FIT_COMBAT,OPEN_CHARACTER,OPEN_COMBAT,OPEN_FAITH,SELECT_ARMY->arguments instanceof Subject;
    case HOVER_ARMY,LEAVE_ARMY,QUERY_ARMY->arguments instanceof ArmyTooltip;
    case HOVER_KNIGHTS->arguments instanceof KnightHover;case TREE->arguments instanceof TreeQuery;
    case PRESENT,QUERY_PRESENT,QUERY_PRESENT_TOOLTIP->arguments instanceof Presentation;
    case QUERY_WINDOW->arguments instanceof WindowQuery;case SELECT_DECISION,QUERY_DECISION->arguments instanceof Decision;
    default->arguments instanceof Empty;};
   require(matches,"typed GUI method/argument branch mismatch");
   if(method==Method.QUERY_PRESENT||method==Method.QUERY_PRESENT_TOOLTIP)require(((Presentation)arguments).operation().equals("query"),"original presentation aliases are read-only");
   if(arguments instanceof Subject s){if(method==Method.OPEN_FAITH){}else if(method==Method.SELECT_ARMY)require(s.value().value().compareTo(BigInteger.valueOf(2147483647L))<=0,"public CUnit integer domain");else positive(s.value());}
   if(arguments instanceof ArmyTooltip a)require(method==Method.HOVER_ARMY? a.receipt() instanceof Absent<?>:a.receipt() instanceof Present<?>,"original tooltip receipt requirement");
   if(method==Method.TREE||method==Method.CAMERA_STATUS)require(expectedRevision instanceof PublicUnsigned64.Missing,"this original method has no revision parameter");
   else if(!Set.of(Method.WHITE_AGE,Method.WHITE_NUMERIC,Method.CONFIRM_ITEM,Method.OPEN_DECISIONS,Method.WHITE_BUSINESS,Method.WHITE_TEXT,Method.SELECT_DECISION,Method.QUERY_DECISION).contains(method))
    require(expectedRevision instanceof PublicUnsigned64.Value,"required original expected_revision");}
  /** The original presentation method also exposes a READ; dispatch follows the typed selector. */
  public boolean submitsAction(){return method.mutation()&&!(arguments instanceof Presentation p&&p.operation().equals("query"));}
 }
 public sealed interface Reply permits ReadReply,ActionReply,CameraReply,NativeReply { }
 /** The actual original query is retained, rather than a lossy projection of its typed decoder. */
 public record ReadReply(PlanningReadReceipt receipt,ExactRef originalReference,
   Optional<RawJson> beforeSnapshot,Optional<RawJson> parsedReturnReference) implements Reply{
  public ReadReply{Objects.requireNonNull(receipt);Objects.requireNonNull(originalReference);Objects.requireNonNull(beforeSnapshot);Objects.requireNonNull(parsedReturnReference);
   parsedReturnReference.ifPresent(GuiPublicMetadata::requireParsedReturnReference);}}
 public record ActionReply(ActionReceipt receipt,byte[] archivedReceipt,ExactRef originalReference,
   Optional<RawJson> beforeSnapshot,Optional<RawJson> parsedReturnReference) implements Reply{
  public ActionReply{Objects.requireNonNull(receipt);Objects.requireNonNull(originalReference);Objects.requireNonNull(beforeSnapshot);Objects.requireNonNull(parsedReturnReference);
   parsedReturnReference.ifPresent(GuiPublicMetadata::requireParsedReturnReference);archivedReceipt=Objects.requireNonNull(archivedReceipt).clone();} @Override public byte[] archivedReceipt(){return archivedReceipt.clone();}}
 public record CameraReply(GuiRealmCameraStatus.StatusData status) implements Reply{public CameraReply{Objects.requireNonNull(status);}}
 /** A current same-Root domain extension supplies this original, never an ACK-only success. */
 public record NativeReply(RawJson original) implements Reply{public NativeReply{Objects.requireNonNull(original);}}
 private static void positive(GuiModels.Subject subject){Objects.requireNonNull(subject);require(subject.value().signum()>0,"positive original GUI handle");}
 private static void intent(String id){require(id!=null&&id.matches("[A-Za-z0-9_.:-]{1,64}"),"original White intent identity");}
}

