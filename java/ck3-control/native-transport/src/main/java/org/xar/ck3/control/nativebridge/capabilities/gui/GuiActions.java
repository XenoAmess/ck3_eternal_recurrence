package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels.*;

/** Root composes these preparation/postcondition functions with its one ActionCoordinator. */
public final class GuiActions implements ActionPorts.PreparationPort,ActionPorts.PostconditionPort {
    private final PlanningReadPort reads;private final GuiReads contracts;
    private final org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiService.CurrentArchive archives;
    public GuiActions(PlanningReadPort reads,GuiReads contracts,org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiService.CurrentArchive archives){this.reads=java.util.Objects.requireNonNull(reads);this.contracts=java.util.Objects.requireNonNull(contracts);this.archives=java.util.Objects.requireNonNull(archives);}
    private ActionPorts.OutcomeArchive archive(){try{return archives.current();}catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}}
    public static Set<String> operations(){return Set.of("navigate-ingame-ui-v1","center-map-on-landed-title-v1","select-ingame-decision-item-v1","confirm-ingame-decision-item-v1","confirm-ingame-decision-outcome-v1","select-aub-policy-option-v1","confirm-aub-policy-v1","click-white-control-v1","click-white-numeric-control-v1");}
    @Override public NativeRequest prepare(ActionCommand command){
        String step=command.operation().value();need(operations().contains(step),"not a registered GUI mutation");Context c=GuiReads.context(command);ObjectNode a=arguments(command.arguments());
        need(command.expected().observerSchema().equals(GuiCapabilities.OBSERVER),"GUI expected observer schema differs");
        List<ExactRef> preparationEvidence=List.of();
        a.remove(List.of("_gui_build","_gui_generation","_gui_verify","_gui_side","_gui_intent_id"));
        switch(step){
            case "navigate-ingame-ui-v1"->{ObjectNode v=a.deepCopy();String op=text(v,"operation");WindowKind k=WindowKind.parse(text(v,"window_kind"));Subject s=new Subject(integer(v,"subject_id"));GuiValidation.semantic(c,op,k,s,v);
                keys(v,Set.of("operation","window_kind","subject_id"),Set.of("army_tooltip_kind","army_tooltip_receipt","presentation_target","presentation_index","presentation_tab","presentation_receipt"));}
            case "center-map-on-landed-title-v1"->{keys(a,Set.of("title_key"),Set.of());new TitleKey(text(a,"title_key"));}
            case "select-ingame-decision-item-v1","confirm-ingame-decision-item-v1","confirm-ingame-decision-outcome-v1"->{
                DecisionKey key=new DecisionKey(text(a,"decision_key"));DecisionItem actual=GuiReads.known(decision(c,key)).value();need(actual.availability().available(),"actual unique decision row/owner unavailable");
                if(!step.startsWith("select-"))need(actual.selectedFor(c.before().frame().identity().player()),"Confirm requires actual selected complete detail and player actor");
                if(step.equals("confirm-ingame-decision-item-v1"))equal(a,"expected_window_kind",TreeKind.WHITE.wire());
                if(step.equals("confirm-ingame-decision-outcome-v1")){String out=text(a,"expected_outcome");need(Set.of("event_window","decision_closed").contains(out),"declared outcome invalid");
                    if(out.equals("event_window"))need(org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.eventDefinitionKey(text(a,"expected_event_definition_key")),"expected actual event definition required");else need(text(a,"expected_event_definition_key").isEmpty(),"closed outcome must carry original empty native event key");}}
            case "select-aub-policy-option-v1","confirm-aub-policy-v1"->{need(c.build()==Build.CROZIER3,"original AUB action only exact .3");Policy expected=Policy.parse(text(a,"expected_selected_key"));Policies actual=GuiReads.known(contracts.read(reads,contracts.aubPolicy,c,boundFields(c))).value();need(actual.selected().filter(expected::equals).isPresent(),"actual selected policy changed before dispatch");
                if(step.startsWith("select-"))Policy.parse(text(a,"desired_key"));else{DecisionItem detail=GuiReads.known(decision(c,new DecisionKey("enable_auto_build"))).value();need(detail.selectedFor(c.before().frame().identity().player()),"AUB Confirm detail is not actually selected");AubState state=GuiReads.known(contracts.read(reads,contracts.aubState,c,boundFields(c))).value();need(state.detailVisible()&&!state.flags().getFirst().present(),"AUB already enabled or detail hidden");}}
            case "click-white-control-v1","click-white-numeric-control-v1"->{need(c.build()==Build.CROZIER3,"original fixed White action only exact .3");var originals=archive();var before=GuiWhiteOriginals.before(command,contracts,originals);
                preparationEvidence=List.of(originals.readReferenceOf(before.business()),originals.readReferenceOf(before.text()));
                if(step.equals("click-white-control-v1")){equal(a,"control","age_plus_1");count(a,"expected_before_age",0,119);}else{NumericControl.parse(text(a,"control"));count(a,"expected_before_value",0,99);need(!text(a,"expected_before_price_text").isEmpty(),"actual price before missing");}
                a.remove(List.of("_gui_before_values","_gui_before_texts",GuiWhiteOriginals.BUSINESS_BEFORE,GuiWhiteOriginals.TEXT_BEFORE));}
            default->throw new IllegalArgumentException("unhandled GUI action");}
        if(!step.equals("navigate-ingame-ui-v1")&&!step.equals("center-map-on-landed-title-v1")){
            equal(a,"expected_player_character_id",c.before().frame().identity().player());equal(a,"expected_game_pid",BigInteger.valueOf(c.before().game().pid()));equal(a,"expected_connection_generation",c.connectionGeneration());}
        return new NativeRequest(step,"game.command."+step,raw(a),preparationEvidence);
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return pending("native GUI result absent/rejected/unknown; mutation is never replayed");
        Context c=GuiReads.context(command);ObjectNode a=arguments(command.arguments());String step=command.operation().value();
        try{
            ObjectNode rawAck=parse(ack.originalResultToken().orElseThrow());
            if(Set.of("select-ingame-decision-item-v1","confirm-ingame-decision-item-v1","confirm-ingame-decision-outcome-v1").contains(step))requireDecisionAck(rawAck,c,a,step);
            if(step.equals("navigate-ingame-ui-v1"))return semanticPost(command,attempt,rawAck,c,a);
            if(step.equals("center-map-on-landed-title-v1"))return pending("original landed-title command has only same-call camera readback; independent native camera observation is not installed");
            if(step.equals("select-ingame-decision-item-v1")){
                DecisionKey key=new DecisionKey(text(a,"decision_key"));var actual=GuiReads.known(decision(c,key));return control(actual.receipt(),List.of(new ExpectedText(new FieldKey("gui.decision_key"),actual.value().key().value()),new ExpectedBoolean(new FieldKey("gui.selected_detail"),actual.value().selectedFor(c.before().frame().identity().player()))));}
            if(step.equals("confirm-ingame-decision-item-v1")){var actual=GuiReads.known(census(c,TreeKind.WHITE));return control(actual.receipt(),List.of(new ExpectedBoolean(new FieldKey("gui.white_inner_modal"),actual.value().whiteInnerModalVisible())));}
            if(step.equals("confirm-ingame-decision-outcome-v1")){
                if(text(a,"expected_outcome").equals("decision_closed")){var actual=GuiReads.known(census(c,TreeKind.DECISION_DETAIL));return control(actual.receipt(),List.of(new ExpectedText(new FieldKey("gui.outcome"),"decision_closed"),new ExpectedBoolean(new FieldKey("gui.outcome_observed"),actual.value().decisionDetailClosed())));}
                return pending("event-window outcome requires the shared actual event-context observer, never native Confirm ACK or selected option authority");}
            if(step.equals("select-aub-policy-option-v1")){var actual=GuiReads.known(contracts.read(reads,contracts.aubPolicy,c,boundFields(c)));return control(actual.receipt(),List.of(new ExpectedText(new FieldKey("gui.selected_policy"),actual.value().selected().map(Policy::wire).orElse(""))));}
            if(step.equals("confirm-aub-policy-v1")){Policy policy=Policy.parse(text(a,"expected_selected_key"));var actual=GuiReads.known(contracts.read(reads,contracts.aubState,c,boundFields(c)));return control(actual.receipt(),List.of(new ExpectedText(new FieldKey("gui.confirmed_policy"),actual.value().confirmed(policy)?policy.wire():"unverified"),new ExpectedBoolean(new FieldKey("gui.detail_closed"),!actual.value().detailVisible())));}
            if(step.startsWith("click-white-"))return whitePost(command,attempt,ack,c,a,step,rawAck);
            return pending("unregistered GUI postcondition");
        }catch(RuntimeException unavailable){return pending("independent GUI postcondition unavailable: "+String.valueOf(unavailable.getMessage()));}
    }
    private ActionPorts.PostconditionResult semanticPost(ActionCommand command,ActionState.Attempt attempt,ObjectNode ack,Context c,ObjectNode a){
        WindowKind kind=WindowKind.parse(text(a,"window_kind"));Subject subject=new Subject(integer(a,"subject_id"));String verify=text(a,"_gui_verify"),operation=text(a,"operation");
        if(c.build()==Build.CROZIER4&&Set.of(WindowKind.FAITH,WindowKind.HOLDING,WindowKind.PERSONAL_BELIEFS,WindowKind.RITE_CREATION,WindowKind.CLERICAL_INTERACTION,WindowKind.TOOLTIPS).contains(kind))GuiPresentationResult.validate(ack,c,operation,kind,subject,a);
        equal(ack,"schema","ck3-ingame-ui-window-v1");equal(ack,"window_kind",kind.wire());equal(ack,"requested_subject_id",subject.value());
        equal(ack,"native_revision",c.before().frame().identity().nativeRevision());equal(ack,"date_raw",c.before().frame().identity().dateRaw());equal(ack,"played_character_id",c.before().frame().identity().player());build(ack,c.build());
        yes(ack,"application_owner_thread_verified","gui_owner_binding_verified");BigInteger submittedEpoch=integer(ack,"pump_epoch");
        ObjectNode query=fields();query.put("window_kind",kind.wire());query.put("subject_id",0);
        if(a.has("presentation_tab")||a.has("presentation_target")||a.has("presentation_index")||a.has("presentation_receipt")){
            query.put("subject_id",subject.value());for(String name:List.of("presentation_target","presentation_index","presentation_tab","presentation_receipt"))if(a.has(name))query.set(name,a.get(name));
            if(operation.equals("select_presentation_tab"))query.remove("presentation_tab");
            if(Set.of("open_rite_core_picker","show_building_details","open_building_track").contains(operation)){query.remove(List.of("presentation_target","presentation_index","presentation_receipt"));query.put("presentation_tab","");}}
        if(a.has("army_tooltip_kind")){query.put("subject_id",subject.value());query.put("army_tooltip_kind",text(a,"army_tooltip_kind"));ObjectNode tooltip=obj(required(ack,"army_tooltip"));ReceiptId receipt=new ReceiptId(text(tooltip,"receipt_id"));query.put("army_tooltip_receipt",receipt.value());}
        var actual=GuiReads.known(contracts.read(reads,contracts.semantic,c,query));UiWindow w=actual.value();need(w.captureEpoch().compareTo(submittedEpoch)>0,"UI read did not capture a later application owner epoch");
        List<ExpectedValue> values=new ArrayList<>();values.add(new ExpectedBoolean(new FieldKey("gui.visible"),w.visible()));values.add(new ExpectedText(new FieldKey("gui.window_kind"),w.kind().wire()));
        w.subject().ifPresent(v->values.add(new ExpectedInteger(new FieldKey("gui.subject"),v)));
        if(verify.equals("fit"))values.add(new ExpectedBoolean(new FieldKey("gui.content_inside_viewport"),w.geometry().available()&&w.geometry().insideViewport()&&!w.geometry().fitRequired()));
        if(verify.equals("army_hover")||verify.equals("army_leave")){ArmyTooltip t=w.tooltip().orElseThrow();values.add(new ExpectedBoolean(new FieldKey("gui.tooltip_action_observed"),verify.equals("army_leave")?t.leaveObserved():t.sourceBound()&&t.hoverMatches()&&t.cache().isPresent()));}
        ObjectNode nativeRead=result(actual.receipt());
        if(verify.equals("combat_hover")){equal(nativeRead,"hovered_ui_side",text(a,"_gui_side"));equal(nativeRead,"hovered_combat_id",subject.value());yes(nativeRead,"hover_state_available");values.add(new ExpectedBoolean(new FieldKey("gui.combat_hover_observed"),true));}
        if(verify.equals("tab")){ObjectNode leaf=obj(required(nativeRead,"presentation_ui"));yes(leaf,"tab_observed","source_bound");values.add(new ExpectedText(new FieldKey("gui.active_tab"),text(leaf,"active_tab")));}
        if(verify.equals("presentation")&&Set.of("open_rite_core_picker","show_building_details","open_building_track","hover_presentation_tooltip","leave_presentation_tooltip","close_tooltips","open_clerical_preview","close_clerical_preview").contains(operation))
            return pending("original presentation callback submitted and independently sampled; operation-specific typed leaf observer has not closed all selector semantics");
        return control(actual.receipt(),values);
    }
    private static void requireDecisionAck(ObjectNode r,Context c,ObjectNode a,String step){
        need(c.build()==Build.CROZIER3||c.build()==Build.CROZIER4,"original decision action exact Crozier profile required");
        boolean select=step.equals("select-ingame-decision-item-v1"),generic=step.equals("confirm-ingame-decision-outcome-v1");
        equal(r,"schema",generic?"ck3-ingame-decision-outcome-confirm-v1":"ck3-ingame-decision-item-action-v1");
        equal(r,"step",step);equal(r,"action",select?"select":generic?"confirm_outcome":"confirm");
        DecisionKey key=new DecisionKey(text(a,"decision_key"));equal(r,"decision_key",key.value());build(r,c.build());binding(r,c);
        yes(r,"owner_thread_verified","source_abi_pins_verified","action_abi_pins_verified","receiver_qualified","gui_owner_binding_verified","frame_verified");
        DecisionItem before=GuiDecoders.decisionItem(obj(required(r,"before_actual_model")),c,key);
        need(before.availability().available(),"decision action actual before model unavailable");
        for(String field:List.of("dispatch_invoked","native_call_completed","before_already_selected","native_handled","native_after_read","selected_after_verified","inner_modal_visible","inner_modal_tree_complete","postcondition_verified","verification_pending","detail_actor_binding_verified","no_blocking_modal_verified"))bool(r,field);
        equal(r,"unavailable_reason","");need(Set.of("observed_postcondition","acknowledged_verification_pending").contains(text(r,"status")),"decision action rejected or completion unknown");
        if(select){
            yes(r,"no_blocking_modal_verified");
            if(bool(r,"before_already_selected")){no(r,"dispatch_invoked","native_call_completed");need(before.definitionMatches(),"already-selected acknowledgement changed actual definition");}
            else yes(r,"dispatch_invoked","native_call_completed");
        }else{
            yes(r,"dispatch_invoked","detail_actor_binding_verified");no(r,"before_already_selected");
            need(before.selectedFor(c.before().frame().identity().player()),"Confirm lacks actual selected detail and player owner");
        }
        if(generic){
            equal(r,"expected_outcome",text(a,"expected_outcome"));equal(r,"expected_event_definition_key",text(a,"expected_event_definition_key"));
            no(r,"postcondition_verified");yes(r,"verification_pending","no_blocking_modal_verified");equal(r,"status","acknowledged_verification_pending");
        }
    }
    private ActionPorts.PostconditionResult whitePost(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,Context c,ObjectNode a,String step,ObjectNode rawAck){
        GuiWhiteOriginals.requireAck(rawAck,c,a,step);
        var before=GuiWhiteOriginals.before(command,contracts,archive());GuiWhiteOriginals.requireBeforeSubmission(before,attempt,ack);
        need(prepare(command).equals(attempt.preparedRequest()),"White cold preparation differs from the actual submitted request/evidence");
        var business=GuiReads.known(contracts.read(reads,contracts.whiteBusiness,c,boundFields(c)));var text=GuiReads.known(contracts.read(reads,contracts.whiteText,c,boundFields(c)));
        var b=GuiWhiteOriginals.requireRole(business.receipt(),c,contracts.whiteBusiness);var t=GuiWhiteOriginals.requireRole(text.receipt(),c,contracts.whiteText);
        List<ExpectedValue> actual;
        try{actual=GuiWhiteOriginals.actual(a,b,t,step);}catch(RuntimeException unavailable){return new ActionPorts.Pending("actual White business/text after unavailable: "+unavailable.getMessage(),List.of(business.originalReceipt(),text.originalReceipt()));}
        if(!command.expected().equals(new ExpectedPostcondition(1,c.before(),c.source(),GuiCapabilities.OBSERVER,actual)))
            return new ActionPorts.Pending("actual White after does not yet prove the one-step business/text change; never redispatch",List.of(business.originalReceipt(),text.originalReceipt()));
        return new ActionPorts.ControlObserved(new ActionState.ControlApplied(business.receipt(),List.of(text.receipt()),GuiCapabilities.OBSERVER,actual));
    }
    private PlanningReadResult<DecisionItem> decision(Context c,DecisionKey key){ObjectNode f=boundFields(c);f.put("decision_key",key.value());return contracts.read(reads,contracts.decision,c,f);}
    private PlanningReadResult<WindowTree> census(Context c,TreeKind kind){ObjectNode f=fields();f.put("window_kind",kind.wire());return contracts.read(reads,contracts.census,c,f);}
    private static ActionPorts.ControlObserved control(PlanningReadReceipt read,List<ExpectedValue> actual){return new ActionPorts.ControlObserved(new ActionState.ControlApplied(read,GuiCapabilities.OBSERVER,actual));}
    private static ActionPorts.Pending pending(String reason){return new ActionPorts.Pending(reason,List.of());}
}
