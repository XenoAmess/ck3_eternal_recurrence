package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventoutcome.RegisteredEventMaterial;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome;
import org.xar.ck3.control.wave2.events.interactionbefore.CurrentInteractionPresentation;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedInteractionContinuation;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Converts actual private-window originals into the existing event/reply command. No ordinary planning request or Ready. */
public final class PendingUiEventPreparation {
    private PendingUiEventPreparation(){ }
    public static EventActionPreparation.PendingPrepared event(PendingUiEvent.Current current,
            PlanningReadResult.Known<EventPolicies.ReadPublication> actual,EventWindowModels.Build actualBuild,
            Set<OperationKey> actionSteps,String actionId,Instant deadline,RegisteredEventKnowledge knowledge,TrustedEventSourceContext trusted){
        requireRead(current,actual.receipt());var frame=current.frame();
        var active=OpportunityJson.object(frame.semantic().get("active_event"),"actual private active event");
        int instance=OpportunityJson.integer(active.get("instance_id"),"event instance").intValueExact();
        var wire=OpportunityJson.object(actual.value().result().get("current_event_window_context"),"original current event-window result");
        var decoded=EventWindowCodec.decode(new RawJson(DriverJson.encode(wire)),new EventWindowModels.Binding(actualBuild,frame.identity().frame().identity().nativeRevision(),frame.identity().frame().identity().dateRaw().intValueExact(),instance));
        if(!(decoded instanceof EventWindowModels.Available available))throw rejected(current,actual.originalReceipt(),new OpportunityJson.Obj(java.util.Map.of("phase",new OpportunityJson.Text("pending_event_window_unavailable"),"selected_step",OpportunityJson.Nil.INSTANCE,"event_window_context",wire)));
        var normalized=RetainedJson.object(RetainedJson.parse(EventWindowCodec.encode(available).bytes()));
        var history=new ArrayList<>(current.history());var read=new EventReadBinding.Captured(actual.value(),actual.receipt().request().operation(),actual.receipt().requestId(),actual.receipt().contractId(),actual.originalReceipt(),Optional.empty());history.add(read.history());
        var retainedFocus=focus(current,actual.originalReceipt());
        var input=new EventDecisionInput(frame.identity(),frame.source(),frame.sessionId(),frame.semantic(),history,actionSteps,current.bridgeCapabilities(),deadline,normalized,retainedFocus.value());
        OpportunityJson.Obj plan=PublicEventResolution.plan(input,knowledge,trusted).with("public_event_window_read",read.history())
                .with("pending_ui_focus_evidence",retainedFocus.evidence());
        plan=retain(current,actual.originalReceipt(),plan);
        if(!(plan.get("selected_step") instanceof OpportunityJson.Text selected))throw new EventActionPreparation.PendingSelectionRejected(plan,actual.originalReceipt());
        var operation=new OperationKey(selected.value());var number=EventActionPreparation.option(operation);
        StrictJson.require(actionSteps.contains(operation)&&current.bridgeCapabilities().contains(EventActionPreparation.EVENT_CAPABILITY),"private selected event has no actual installed native family/capability");
        var option=available.options().stream().filter(row->row.nativeOptionIndex()==number.value()-1).findFirst().orElseThrow(()->new IllegalArgumentException("private event plan has no original displayed native option"));
        // The v1 field samples the option flag; stock GUI validity also depends on its native owner gate.
        if(!option.enabled())throw new EventActionPreparation.PendingSelectionRejected(plan.with("selected_step",OpportunityJson.Nil.INSTANCE),actual.originalReceipt());
        var presentation=new EventActionPreparation.EventPresentation(available,option);
        return command(current,actual.receipt(),actual.originalReceipt(),presentation,operation,plan,actionId,deadline);
    }
    public static EventActionPreparation.PendingPrepared interaction(PendingUiEvent.Current current,
            PlanningReadResult.Known<PendingContext> actual,InteractionModels.Context actualContext,Set<OperationKey> actionSteps,String actionId,Instant deadline,TrustedEventSourceContext trusted){
        requireRead(current,actual.receipt());var frame=current.frame();var publication=InteractionReadPublications.pending(actual);
        var context=OpportunityJson.object(publication.get("pending_character_interaction_context"),"actual private pending context");
        List<String> steps=actionSteps.stream().map(OperationKey::value).sorted().toList();
        StrictJson.require(actualContext.before().equals(frame.identity())&&actualContext.source().equals(frame.source())&&actualContext.sessionId().equals(frame.sessionId()),"private notification context crossed the actual pending physical source");
        RetainedJson.Value previous=RetainedJson.NULL;
        if(!actualContext.controls().pending().autoAcceptNotification()&&KnownPendingInteractionRules.classify(actual.value()).dedicated()){
            var snapshot=(com.fasterxml.jackson.databind.node.ObjectNode)DriverJson.toNode(frame.semantic());
            var policy=KnownPendingInteractionRules.evaluate(new KnownPendingInteractionRules.Input(actual.value(),actualContext,
                    org.xar.ck3.control.application.planning.warexit.WarExitEvidence.wars(snapshot),KnownPendingInteractionEvidence.warSignature(snapshot),Optional.empty(),Optional.empty(),Set.copyOf(steps)));
            var encoded=KnownPendingInteractionPlanCodec.encode(policy);
            // This private producer can submit the already selected legal left reject. A selected accept retains
            // its dedicated priority; a diagnosis with no selected action follows the common left-reply policy.
            var original=StrictJson.object().put("policy","one-life-turn-v1").put("phase",policy.phase()).putNull("selected_step");
            original.set("java_policy_plan",encoded);
            String definitionKey=actual.value().definition()==null?null:actual.value().definition().key();
            var decision=original.putObject("decision").put("classification",policy.classification().key())
                    .put("interaction_key",definitionKey);
            decision.putObject("definition_classification").put("definition_key",definitionKey);
            previous=RetainedJson.parse(StrictJson.canonical(original));
            if(policy.selected().filter(action->action!=KnownPendingInteractionRules.Action.REJECT).isPresent()
                    ||SourceReviewedInteractionContinuation.originalPlan(previous).blockedMarriageReply()){
                var blocked=new OpportunityJson.Obj(java.util.Map.of("phase",new OpportunityJson.Text(policy.phase()),"selected_step",OpportunityJson.Nil.INSTANCE,"known_policy_handled",new OpportunityJson.Bool(true),"java_policy_plan",OpportunityJson.parse(StrictJson.canonical(encoded)),"reason",new OpportunityJson.Text("the existing dedicated strategy has priority; its required private material or exact accept producer is unavailable")));
                if(policy.requiredStep().isPresent())blocked=blocked.with("required_step",new OpportunityJson.Text(policy.requiredStep().orElseThrow()));
                if(policy.requiredTool().isPresent())blocked=blocked.with("required_mcp_tool",new OpportunityJson.Text(policy.requiredTool().orElseThrow()));
                throw rejected(current,actual.originalReceipt(),blocked);
            }
        }
        var initial=new SourceReviewedInteractionContinuation.Input(Optional.of(retained(frame.semantic())),Optional.of(retained(context)),previous,steps,true);
        var result=SourceReviewedInteractionContinuation.plan(initial,trusted).orElseThrow(()->rejected(current,actual.originalReceipt(),new OpportunityJson.Obj(java.util.Map.of("phase",new OpportunityJson.Text("pending_interaction_source_presentation_unavailable"),"selected_step",OpportunityJson.Nil.INSTANCE,"pending_context",context))));
        OpportunityJson.Obj plan=retain(current,actual.originalReceipt(),opportunity(result));
        if(!(plan.get("selected_step") instanceof OpportunityJson.Text selected))throw new EventActionPreparation.PendingSelectionRejected(plan,actual.originalReceipt());
        var operation=new OperationKey(selected.value());
        StrictJson.require(actionSteps.contains(operation)&&current.bridgeCapabilities().contains("game.command."+operation.value()),"private pending left reply has no actual installed native channel");
        int instance=actual.value().instance().value();
        var presentation=CurrentInteractionPresentation.requireSubmission(DriverJson.toNode(OpportunityJson.object(plan.get("unhandled_interaction_fallback"),"original private left-reply capture")),operation.value(),instance);
        return command(current,actual.receipt(),actual.originalReceipt(),new EventActionPreparation.InteractionPresentation(presentation),operation,plan,actionId,deadline);
    }
    private static EventActionPreparation.PendingPrepared command(PendingUiEvent.Current current,PlanningReadReceipt read,ExactRef originalRead,
            EventActionPreparation.PendingPresentation presentation,OperationKey operation,OpportunityJson.Obj plan,String id,Instant deadline){
        var frame=current.frame();Optional<PoetTraitOutcome.Expectation> trait=Optional.empty();
        if(plan.get("event_decision") instanceof OpportunityJson.Obj decision)trait=RegisteredEventMaterial.poet(retained(decision),retained(frame.semantic()));
        var expected=NativeEventPostconditionPort.expected(frame.identity(),frame.source(),frame.semantic(),operation,plan,trait)
                .orElseThrow(()->new EventActionPreparation.PendingSelectionRejected(plan,originalRead));
        var claims=new Claims(Set.of(),Set.of(),Set.of(frame.identity().frame().identity().player()),Set.of("foreground-window"));
        var command=new ActionCommand(id,frame.identity(),frame.source(),frame.sessionId(),operation,plan,expected,claims,deadline);
        var refs=new LinkedHashSet<>(current.originals());refs.add(originalRead);
        return new EventActionPreparation.PendingPrepared(command,read,originalRead,presentation,List.copyOf(refs));
    }
    private record Focus(Optional<String> value,OpportunityJson.Obj evidence){ }
    private static Focus focus(PendingUiEvent.Current current,ExactRef originalRead){
        var snapshot=current.frame().semantic();var retained=current.known().driver().campaignGoal();
        var predecessor=current.originalParent().lifecycleBefore().subject().characterId();
        var fields=new java.util.LinkedHashMap<String,OpportunityJson.Value>();
        fields.put("schema",new OpportunityJson.Text("xar.pending-ui-retained-focus/v1"));
        fields.put("parent_subject_character_id",new OpportunityJson.IntegerValue(predecessor));
        fields.put("actual_pending_actor_character_id",new OpportunityJson.IntegerValue(current.frame().identity().frame().identity().player()));
        fields.put("goal_progress_advanced",new OpportunityJson.Bool(false));
        if(retained instanceof org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value original){
            OpportunityJson.Obj actualGoal;OrdinaryCampaignGoal.Goal decoded;
            try{actualGoal=DriverJson.object(original.json(),DriverJson.MAX_NATIVE_BYTES);decoded=GoalCodec.decodeGoal(original.json());}
            catch(IllegalArgumentException invalid){
                throw rejected(current,originalRead,new OpportunityJson.Obj(java.util.Map.of("phase",new OpportunityJson.Text("pending_event_retained_campaign_goal_invalid"),"selected_step",OpportunityJson.Nil.INSTANCE,
                        "reason",new OpportunityJson.Text("the actual retained Driver goal is malformed: "+String.valueOf(invalid.getMessage())),"pending_ui_focus_evidence",new OpportunityJson.Obj(fields))));
            }
            fields.put("retained_goal",actualGoal);
            if(!actualGoal.equals(snapshot.get("campaign_goal"))||!BigInteger.valueOf(decoded.currentCharacterId()).equals(predecessor)){
                var diagnosis=new OpportunityJson.Obj(java.util.Map.of("phase",new OpportunityJson.Text("pending_event_retained_campaign_goal_mismatch"),"selected_step",OpportunityJson.Nil.INSTANCE,
                        "reason",new OpportunityJson.Text("the unchanged actual pending Driver goal must belong to the original CONTINUE predecessor; no succession progress is granted before Finalized"),
                        "pending_ui_focus_evidence",new OpportunityJson.Obj(fields)));
                throw rejected(current,originalRead,diagnosis);
            }
            String value=OrdinaryCampaignGoal.plan(decoded).focus();fields.put("status",new OpportunityJson.Text("retained_parent_goal"));fields.put("focus",new OpportunityJson.Text(value));
            return new Focus(Optional.of(value),new OpportunityJson.Obj(fields));
        }
        if(snapshot.get("campaign_goal")!=null&&snapshot.get("campaign_goal")!=OpportunityJson.Nil.INSTANCE){
            throw rejected(current,originalRead,new OpportunityJson.Obj(java.util.Map.of("phase",new OpportunityJson.Text("pending_event_retained_campaign_goal_missing"),"selected_step",OpportunityJson.Nil.INSTANCE,
                    "reason",new OpportunityJson.Text("the full semantic goal has no identical retained actual Driver original"),"pending_ui_focus_evidence",new OpportunityJson.Obj(fields))));
        }
        var fallback=CrossRunPlanning.focus(snapshot.get("cross_run_plan") instanceof OpportunityJson.Obj plan?Optional.of(plan):Optional.empty());
        fields.put("status",new OpportunityJson.Text(fallback.isPresent()?"existing_cross_run_focus":"goal_absent"));
        fields.put("retained_goal",OpportunityJson.Nil.INSTANCE);fields.put("focus",fallback.<OpportunityJson.Value>map(OpportunityJson.Text::new).orElse(OpportunityJson.Nil.INSTANCE));
        return new Focus(fallback,new OpportunityJson.Obj(fields));
    }
    private static void requireRead(PendingUiEvent.Current current,PlanningReadReceipt receipt){
        var frame=current.frame();StrictJson.require(receipt.request().before().equals(frame.identity())&&receipt.request().source().equals(frame.source())&&receipt.request().sessionId().equals(frame.sessionId())&&receipt.original().nativeOk(),"private pending event read crossed its actual complete source/frame/session");
    }
    private static OpportunityJson.Obj retain(PendingUiEvent.Current current,ExactRef originalRead,OpportunityJson.Obj plan){
        var refs=new ArrayList<OpportunityJson.Value>();current.originals().forEach(ref->refs.add(OpportunityJson.parse(StrictJson.canonical(ref.toJson()))));
        var source=new OpportunityJson.Obj(java.util.Map.of("schema",new OpportunityJson.Text("xar.pending-ui-event-source/v1"),"original_parent_action_id",new OpportunityJson.Text(current.originalParent().actionId()),"original_parent_body_sha256",new OpportunityJson.Text(ActionCodec.bodySha256(current.originalParent())),"original_read",OpportunityJson.parse(StrictJson.canonical(originalRead.toJson())),"source_originals",new OpportunityJson.Arr(refs)));
        return plan.with("pending_ui_event_source",source);
    }
    private static EventActionPreparation.PendingSelectionRejected rejected(PendingUiEvent.Current current,ExactRef read,OpportunityJson.Obj plan){return new EventActionPreparation.PendingSelectionRejected(retain(current,read,plan),read);}
    private static RetainedJson.ObjectValue retained(OpportunityJson.Obj value){return RetainedJson.object(RetainedJson.parse(DriverJson.encode(value)));}
    private static OpportunityJson.Obj opportunity(RetainedJson.ObjectValue value){return DriverJson.object(RetainedJson.encode(value),ActionCommand.MAX_ARGUMENT_BYTES);}
}
