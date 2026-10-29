package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels.*;

/** Typed public GUI entries. Only the existing action coordinator may submit a mutation. */
public final class GuiCapabilities {
    public static final String OBSERVER="xar.java.native-gui-postcondition/v1";
    private final ActionCoordinatorPort actions;private final PlanningReadPort reads;private final GuiReads contracts;
    public GuiCapabilities(ActionCoordinatorPort actions,PlanningReadPort reads,GuiReads contracts){this.actions=Objects.requireNonNull(actions);this.reads=Objects.requireNonNull(reads);this.contracts=Objects.requireNonNull(contracts);}
    public PlanningReadResult<UiWindow> query_ingame_ui_window_v1(Context c,WindowKind kind){return semantic(c,kind,new Subject(0),fields());}
    public PlanningReadResult<UiWindow> query_army_tooltip_v1(Context c,Subject army,TooltipKind kind,ReceiptId receipt){ObjectNode f=fields();f.put("army_tooltip_kind",kind.wire());f.put("army_tooltip_receipt",receipt.value());return semantic(c,WindowKind.ARMY,army,f);}
    PlanningReadResult<UiWindow> semantic(Context c,WindowKind kind,Subject subject,ObjectNode options){ObjectNode f=options.deepCopy();f.put("window_kind",kind.wire());f.put("subject_id",subject.value());return contracts.read(reads,contracts.semantic,c,f);}
    /** Campaign-bound overload; the frontend-session overload is installed by the shared session-read owner. */
    public PlanningReadResult<WindowTree> inspect_gui_window_tree_v1(Context c,TreeKind kind){ObjectNode f=fields();f.put("window_kind",kind.wire());return contracts.read(reads,contracts.census,c,f);}
    public PlanningReadResult<DecisionItem> query_ingame_decision_item_v1(Context c,DecisionKey key){ObjectNode f=boundFields(c);f.put("decision_key",key.value());return contracts.read(reads,contracts.decision,c,f);}
    public PlanningReadResult<Policies> query_aub_policy_options_v1(Context c){return contracts.read(reads,contracts.aubPolicy,c,boundFields(c));}
    public PlanningReadResult<AubState> query_aub_business_state_v1(Context c){return contracts.read(reads,contracts.aubState,c,boundFields(c));}
    public PlanningReadResult<WhiteBusiness> query_white_player_business_variables_v1(Context c){return contracts.read(reads,contracts.whiteBusiness,c,boundFields(c));}
    public PlanningReadResult<WhiteText> query_white_rendered_text_v1(Context c){return contracts.read(reads,contracts.whiteText,c,boundFields(c));}
    public ActionReceipt open_character_window_v1(Intent i,Subject character){return navigate(i,"open_character",WindowKind.CHARACTER,character,fields(),"visible",true);}
    public ActionReceipt open_faith_window_v1(Intent i,Subject faith){return navigate(i,"open_faith",WindowKind.FAITH,faith,fields(),"visible",true);}
    public ActionReceipt select_army_ui_v1(Intent i,Subject army){return navigate(i,"select_army",WindowKind.ARMY,army,fields(),"visible",true);}
    public ActionReceipt open_combat_window_v1(Intent i,Subject combat){return navigate(i,"open_combat",WindowKind.COMBAT,combat,fields(),"visible",true);}
    public ActionReceipt fit_combat_window_v1(Intent i,Subject combat){return navigate(i,"fit_combat_window",WindowKind.COMBAT,combat,fields(),"fit",true);}
    public ActionReceipt open_knights_window_v1(Intent i){return navigate(i,"open_knights",WindowKind.KNIGHTS,new Subject(0),fields(),"visible",true);}
    public ActionReceipt hover_combat_knights_v1(Intent i,Subject combat,Side side){ObjectNode f=fields();f.put("_gui_side",side.wire());return navigate(i,"hover_"+side.wire()+"_knights",WindowKind.COMBAT,combat,f,"combat_hover",true);}
    public ActionReceipt hover_army_tooltip_v1(Intent i,Subject army,TooltipKind kind){ObjectNode f=fields();f.put("army_tooltip_kind",kind.wire());return navigate(i,"hover_army_tooltip",WindowKind.ARMY,army,f,"army_hover",true);}
    public ActionReceipt leave_army_tooltip_v1(Intent i,Subject army,TooltipKind kind,ReceiptId receipt){ObjectNode f=fields();f.put("army_tooltip_kind",kind.wire());f.put("army_tooltip_receipt",receipt.value());return navigate(i,"leave_army_tooltip",WindowKind.ARMY,army,f,"army_leave",true);}
    /** Read queries and original callbacks remain distinct result branches. */
    public sealed interface PresentationResult permits PresentationRead,PresentationAction { }
    public record PresentationRead(PlanningReadResult<UiWindow> result) implements PresentationResult { }
    public record PresentationAction(ActionReceipt result) implements PresentationResult { }
    public PresentationResult present_faith_power_ui_v1(Intent i,Presentation p){GuiValidation.presentation(i.frame(),p);ObjectNode f=fields();
        p.target().ifPresent(v->f.put("presentation_target",v));p.index().ifPresent(v->f.put("presentation_index",v));p.tab().ifPresent(v->f.put("presentation_tab",v));p.receipt().ifPresent(v->f.put("presentation_receipt",v.value()));
        if(p.operation().equals("query")){if(f.isEmpty()&&!Set.of(WindowKind.CLERICAL_INTERACTION,WindowKind.TOOLTIPS).contains(p.kind()))f.put("presentation_tab","");return new PresentationRead(semantic(i.frame(),p.kind(),p.subject(),f));}
        boolean visible=!Set.of("close_presentation_window","close_clerical_preview").contains(p.operation());
        return new PresentationAction(navigate(i,p.operation(),p.kind(),p.subject(),f,p.operation().equals("select_presentation_tab")?"tab":"presentation",visible));}
    public ActionReceipt center_map_on_landed_title_v1(Intent i,TitleKey title){ObjectNode f=fields();f.put("title_key",title.value());return execute(i,"center-map-on-landed-title-v1",f,"camera",List.of(new ExpectedText(new FieldKey("gui.title_key"),title.value()),new ExpectedBoolean(new FieldKey("gui.camera_settled"),true)));}
    public ActionReceipt select_ingame_decision_item_v1(Intent i,DecisionKey key){ObjectNode f=boundFields(i.frame());f.put("decision_key",key.value());return execute(i,"select-ingame-decision-item-v1",f,"decision_select",List.of(new ExpectedText(new FieldKey("gui.decision_key"),key.value()),new ExpectedBoolean(new FieldKey("gui.selected_detail"),true)));}
    public ActionReceipt confirm_ingame_decision_item_v1(Intent i,DecisionKey key,TreeKind expectedWindow){need(expectedWindow==TreeKind.WHITE,"only original fixed White inner modal Confirm");ObjectNode f=boundFields(i.frame());f.put("decision_key",key.value());f.put("expected_window_kind",expectedWindow.wire());return execute(i,"confirm-ingame-decision-item-v1",f,"decision_confirm",List.of(new ExpectedBoolean(new FieldKey("gui.white_inner_modal"),true)));}
    public ActionReceipt confirm_ingame_decision_outcome_v1(Intent i,DecisionKey key,Outcome outcome,Optional<String> eventDefinition){
        need(outcome==Outcome.EVENT_WINDOW?eventDefinition.isPresent()&&org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.eventDefinitionKey(eventDefinition.orElseThrow()):eventDefinition.map(String::isEmpty).orElse(true),"declared event/closed outcome mismatch");
        ObjectNode f=boundFields(i.frame());f.put("decision_key",key.value());f.put("expected_outcome",outcome.wire());f.put("expected_event_definition_key",eventDefinition.orElse(""));
        return execute(i,"confirm-ingame-decision-outcome-v1",f,"decision_outcome",List.of(new ExpectedText(new FieldKey("gui.outcome"),outcome.wire()),new ExpectedBoolean(new FieldKey("gui.outcome_observed"),true)));}
    public ActionReceipt select_aub_policy_option_v1(Intent i,Policy expected,Policy desired){ObjectNode f=boundFields(i.frame());f.put("expected_selected_key",expected.wire());f.put("desired_key",desired.wire());return execute(i,"select-aub-policy-option-v1",f,"aub_select",List.of(new ExpectedText(new FieldKey("gui.selected_policy"),desired.wire())));}
    public ActionReceipt confirm_aub_policy_v1(Intent i,Policy expected){ObjectNode f=boundFields(i.frame());f.put("expected_selected_key",expected.wire());return execute(i,"confirm-aub-policy-v1",f,"aub_confirm",List.of(new ExpectedText(new FieldKey("gui.confirmed_policy"),expected.wire()),new ExpectedBoolean(new FieldKey("gui.detail_closed"),true)));}
    public ActionReceipt click_white_control_v1(Intent i,int expectedAge,String intentId){need(expectedAge>=0&&expectedAge<120,"fixed age before bound");GuiValidation.intentId(intentId);ObjectNode f=whiteBefore(i.frame());f.put("control","age_plus_1");f.put("expected_before_age",expectedAge);f.put("_gui_intent_id",intentId);return white(i,"click-white-control-v1",f,Variable.AGE,TextName.AGE,expectedAge);}
    public ActionReceipt click_white_numeric_control_v1(Intent i,NumericControl control,int expectedValue,String expectedPrice,String intentId){need(expectedValue>=0&&expectedValue<100,"fixed numeric before bound");GuiValidation.intentId(intentId);need(expectedPrice!=null&&!expectedPrice.isEmpty()&&expectedPrice.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=2048,"actual before price text required");
        ObjectNode f=whiteBefore(i.frame());f.put("control",control.wire());f.put("expected_before_value",expectedValue);f.put("expected_before_price_text",expectedPrice);f.put("_gui_intent_id",intentId);return white(i,"click-white-numeric-control-v1",f,Variable.valueOf(control.name()),TextName.valueOf(control.name()),expectedValue);}
    private ObjectNode whiteBefore(Context c){var businessRead=GuiReads.known(query_white_player_business_variables_v1(c));var textRead=GuiReads.known(query_white_rendered_text_v1(c));WhiteBusiness business=businessRead.value();WhiteText text=textRead.value();
        need(business.availability().available()&&business.allIntegers()&&text.availability().available(),"separate actual White before observations required");ObjectNode f=boundFields(c),values=fields(),texts=fields();
        for(Variable key:Variable.values())values.put(key.wire(),business.integer(key));for(TextName key:TextName.values())texts.put(key.wire(),text.text(key));f.set("_gui_before_values",values);f.set("_gui_before_texts",texts);GuiWhiteOriginals.retainBefore(f,businessRead,textRead);return f;}
    private ActionReceipt white(Intent i,String step,ObjectNode f,Variable variable,TextName widget,int expected){equal(obj(required(f,"_gui_before_values")),variable.wire(),BigInteger.valueOf(expected));equal(obj(required(f,"_gui_before_texts")),widget.wire(),Integer.toString(expected));
        if(f.has("expected_before_price_text"))equal(obj(required(f,"_gui_before_texts")),TextName.PRICE.wire(),text(f,"expected_before_price_text"));
        return execute(i,step,f,"white",List.of(new ExpectedInteger(new FieldKey("gui.white_value"),BigInteger.valueOf(expected+1L)),new ExpectedText(new FieldKey("gui.white_text"),Integer.toString(expected+1)),new ExpectedBoolean(new FieldKey("gui.unrelated_business_unchanged"),true)));}
    private ActionReceipt navigate(Intent i,String operation,WindowKind kind,Subject subject,ObjectNode options,String verify,boolean visible){ObjectNode f=options.deepCopy();f.put("operation",operation);f.put("window_kind",kind.wire());f.put("subject_id",subject.value());
        ObjectNode validate=f.deepCopy();validate.remove("_gui_side");GuiValidation.semantic(i.frame(),operation,kind,subject,validate);
        List<ExpectedValue> expected=new ArrayList<>();expected.add(new ExpectedBoolean(new FieldKey("gui.visible"),visible));expected.add(new ExpectedText(new FieldKey("gui.window_kind"),kind.wire()));
        if(subject.value().signum()>0||operation.equals("select_army")||operation.equals("open_faith"))expected.add(new ExpectedInteger(new FieldKey("gui.subject"),subject.value()));
        if(verify.equals("fit"))expected.add(new ExpectedBoolean(new FieldKey("gui.content_inside_viewport"),true));
        if(verify.equals("tab"))expected.add(new ExpectedText(new FieldKey("gui.active_tab"),text(f,"presentation_tab")));
        return execute(i,"navigate-ingame-ui-v1",f,verify,expected);}
    private ActionReceipt execute(Intent i,String step,ObjectNode fields,String verify,List<ExpectedValue> values){Context c=i.frame();ObjectNode a=GuiReads.metadata(c,fields);a.put("_gui_verify",verify);
        ExpectedPostcondition expected=new ExpectedPostcondition(1,c.before(),c.source(),OBSERVER,values);
        Claims claims=new Claims(Set.of(),Set.of(),Set.of(c.before().frame().identity().player()),Set.of("native-gui"));
        return actions.execute(new ActionCommand(i.actionId(),c.before(),c.source(),c.sessionId(),new OperationKey(step),arguments(a),expected,claims,c.deadline()));}
}


