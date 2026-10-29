package org.xar.ck3.control.nativebridge.publicmethods.gui;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlContract.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiReads;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original single-dispatch native pipe controls followed by independent same-frame GUI census.
 * No caller can submit through this class; it only prepares the canonical writer's native request and observes it.
 */
public final class MilitaryControlActions implements ActionPorts.PreparationPort,ActionPorts.PostconditionPort {
    @FunctionalInterface public interface CurrentArchive {ActionPorts.OutcomeArchive current()throws IOException;}
    private final GuiReads contracts;private final PlanningReadPort reads;private final CurrentArchive archives;private final Clock clock;private final org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames;
    public MilitaryControlActions(GuiReads sameInstalled,PlanningReadPort actualReads,CurrentArchive actualArchive,org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader actualFrames,Clock clock){
        frames=Objects.requireNonNull(actualFrames);contracts=Objects.requireNonNull(sameInstalled);reads=Objects.requireNonNull(actualReads);archives=Objects.requireNonNull(actualArchive);this.clock=Objects.requireNonNull(clock);
    }
    public static List<ExpectedValue> expected(Control control){return List.of(
            new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),
            new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false),new ExpectedText(new FieldKey("military.control"),control.name()),
            new ExpectedBoolean(new FieldKey("military.control_verified"),true));}
    public ActionCommand prepareCommand(Control control,Binding binding,String actionId)throws IOException {
        Objects.requireNonNull(control);Objects.requireNonNull(binding);StrictJson.text(actionId);
        Optional<ExactRef> before=Optional.empty();
        if(control!=Control.OPEN){var original=census(binding);MilitaryReceiverProof.observeFixedReinforcement(normalized(original,binding),binding);before=Optional.of(archive().preserveRead(original));}
        return command(control,binding,actionId,before);
    }
    /** Pure typed command producer; a retained READ reference is only DATA until prepare reloads it under the actual writer. */
    public static ActionCommand command(Control control,Binding binding,String actionId,Optional<ExactRef> originalBefore){
        require((control==Control.OPEN)==originalBefore.isEmpty(),"reinforcement requires its exact independent before census");
        ObjectNode fields=StrictJson.object().put("_gui_build",binding.context().build().name()).put("_gui_generation",binding.generation());
        if(originalBefore.isPresent())fields.set("_military_before_read",originalBefore.orElseThrow().toJson());else fields.putNull("_military_before_read");
        var c=binding.context();return new ActionCommand(actionId,c.before(),c.source(),c.sessionId(),control.operation(),
                (OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(fields)),new ExpectedPostcondition(1,c.before(),c.source(),OBSERVER,expected(control)),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),c.deadline());
    }
    public static Binding binding(ActionCommand command){
        Control control=Control.parse(command.operation()).orElseThrow(()->new IllegalArgumentException("unregistered fixed military control"));
        ObjectNode a=StrictJson.object(OpportunityJson.toNode(command.arguments()),Set.of("_gui_build","_gui_generation","_military_before_read"));
        require(command.origin() instanceof CommandOrigin.Gameplay&&command.expected().observerSchema().equals(OBSERVER)
                &&command.expected().values().equals(expected(control)),"actual fixed military command/expected contract differs");
        require((control==Control.OPEN)==a.get("_military_before_read").isNull(),"before READ presence differs from typed control");
        return new Binding(GuiReads.context(command));
    }
    private ActionPorts.OutcomeArchive archive(){try{return Objects.requireNonNull(archives.current());}catch(IOException error){throw new UncheckedIOException("actual military writer archive unavailable",error);}}
    private Optional<PlanningReadReceipt> before(ActionCommand command,Binding binding,ActionPorts.OutcomeArchive archive){
        JsonNode original=OpportunityJson.toNode(command.arguments()).get("_military_before_read");if(original.isNull())return Optional.empty();
        var reference=ExactRef.fromJson(original);var receipt=archive.loadRead(reference);require(archive.readReferenceOf(receipt).equals(reference),"before census custody changed");
        normalized(receipt,binding);MilitaryReceiverProof.observeFixedReinforcement(normalized(receipt,binding),binding);return Optional.of(receipt);
    }
    @Override public NativeRequest prepare(ActionCommand command){
        Binding binding=binding(command);Control control=Control.parse(command.operation()).orElseThrow();var archive=archive();
        Optional<PlanningReadReceipt> before=before(command,binding,archive);
        ObjectNode fields=StrictJson.object().put("expected_player_character_id",binding.actor()).put("expected_game_pid",binding.pid()).put("expected_connection_generation",binding.generation());
        return new NativeRequest(control.operation().value(),control.capability(),raw(fields),before.stream().map(archive::readReferenceOf).toList());
    }
    private PlanningReadReceipt census(Binding binding){
        ObjectNode args=StrictJson.object().put("window_kind","military");
        PlanningReadResult<GuiModels.WindowTree> result=contracts.read(reads,contracts.census,binding.context(),args);
        if(!(result instanceof PlanningReadResult.Known<GuiModels.WindowTree> known))throw new IllegalArgumentException("actual military census unavailable: "+((PlanningReadResult.Unavailable<GuiModels.WindowTree>)result).reason());
        normalized(known.receipt(),binding);return known.receipt();
    }
    public RawJson normalized(PlanningReadReceipt receipt,Binding binding){
        NativeRecordedEvidenceVerifier.requireRead(receipt,archive());
        contracts.census.replay(receipt);
        require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"actual military READ changed its complete original binding");
        var actualArchive=archive();
        var originalBefore=org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(receipt.before().binding(),actualArchive,frames);
        var originalAfter=org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(receipt.after().binding(),actualArchive,frames);
        require(originalBefore.fullBindingSha256().equals(receipt.before().originalBindingSha256())
                &&originalAfter.fullBindingSha256().equals(receipt.after().originalBindingSha256())
                &&originalBefore.semantic().equals(originalAfter.semantic())&&originalBefore.connectionGeneration().equals(binding.generation())
                &&originalAfter.connectionGeneration().equals(binding.generation()),"actual military READ full native/Driver originals changed");
        require(receipt.contractId().equals(contracts.census.contractId())&&receipt.request().operation().equals(contracts.census.operation())
                &&receipt.request().source().equals(binding.context().source())&&receipt.request().sessionId().equals(binding.context().sessionId())
                &&receipt.before().binding().source().equals(binding.context().source())&&receipt.after().binding().source().equals(binding.context().source())
                &&receipt.before().binding().sessionId().equals(binding.context().sessionId())&&receipt.after().binding().sessionId().equals(binding.context().sessionId())
                &&receipt.request().before().equals(binding.context().before())&&receipt.before().binding().observed().equals(binding.context().before())
                &&receipt.after().binding().observed().equals(binding.context().before())&&receipt.before().paused()&&receipt.after().paused()
                &&receipt.before().mapReady()&&receipt.after().mapReady()&&receipt.before().playerAlive()&&receipt.after().playerAlive(),"actual military READ crossed original paused public/native frame");
        var args=OpportunityJson.toNode(receipt.request().arguments());require(args.get("window_kind").isTextual()&&args.get("window_kind").textValue().equals("military"),"wrong census scope");
        return MilitaryReceiverProof.normalizeTree(receipt.original().originalResultToken().orElseThrow(),binding);
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
        Binding binding=binding(command);Control control=Control.parse(command.operation()).orElseThrow();var archive=archive();
        if(dispatch instanceof NativeActionPort.Unknown unknown)return new ActionPorts.Pending("original military control UNKNOWN; no retry: "+unknown.reason(),List.of());
        if(!(dispatch instanceof NativeActionPort.AckReceived ack))return new ActionPorts.Pending("military control lacks its original native ACK; no retry",List.of());
        if(!ack.nativeOk()){
            JsonNode raw=StrictJson.parse(ack.originalFrame().bytes());JsonNode error=raw.get("error");
            return error!=null&&error.isTextual()&&!error.textValue().isEmpty()
                    ?new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),error.textValue(),archive.preserve(ack)))
                    :new ActionPorts.Pending("military rejection lacks actual original native error",List.of());
        }
        var before=before(command,binding,archive).map(value->MilitaryReceiverProof.observeFixedReinforcement(normalized(value,binding),binding));
        acknowledgement(control,binding,ack.originalResultToken().orElseThrow(),before);
        Instant verification=clock.instant().plusSeconds(5);if(command.deadline().isBefore(verification))verification=command.deadline();
        var retained=new ArrayList<PlanningReadReceipt>();
        for(int ordinal=0;ordinal<51;ordinal++){
            if(!clock.instant().isBefore(verification))break;
            PlanningReadReceipt actual=census(binding);retained.add(actual);RawJson tree=normalized(actual,binding);boolean verified;
            if(control==Control.OPEN)verified=visible(tree);
            else {var later=MilitaryReceiverProof.observeFixedReinforcement(tree,binding);requireLater(before.orElseThrow(),later);verified=later.sourceSwitch().enabled()==control.desiredEnabled();}
            if(verified)return new ActionPorts.ControlObserved(new ActionState.ControlApplied(actual,retained.subList(0,retained.size()-1),OBSERVER,expected(control)));
            long remaining=java.time.Duration.between(clock.instant(),verification).toMillis();if(remaining<=0)break;
            try{Thread.sleep(Math.min(100,remaining));}catch(InterruptedException error){Thread.currentThread().interrupt();throw new IllegalStateException("military independent observation interrupted; no retry",error);}
        }
        return new ActionPorts.Pending(control==Control.OPEN?"military ACK lacks later visible root; no retry":"acknowledged_verification_pending",
                retained.stream().map(archive::preserveRead).toList());
    }
    public static boolean visible(RawJson normalized){
        ObjectNode tree=node(normalized);eq(tree,"scope_root_name","military_view");require(!bool(tree,"truncated"),"incomplete military tree");
        if(!bool(tree,"root_available"))return false;JsonNode widgets=tree.get("widgets");require(widgets!=null&&widgets.isArray(),"actual military rows missing");
        int count=0;boolean visible=false;for(JsonNode value:widgets){require(value instanceof ObjectNode,"actual widget object required");ObjectNode row=(ObjectNode)value;if(text(row,"child_path").isEmpty()){eq(row,"runtime_name","military_view");count++;visible=bool(row,"effective_visible");}}
        require(count==1,"actual military root ambiguous");return visible;
    }
    /** Pure cold observer over original ACK, actual registered READ receipts and canonical outcome. No new query or action. */
    public void replay(Head actualHead,ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
        Binding binding=binding(receipt.command());Control control=Control.parse(receipt.command().operation()).orElseThrow();
        if(receipt.state() instanceof ActionState.IntentDurable)return;
        var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow(()->new UncheckedIOException(new IOException("actual military attempt is absent")));
        require(attempt.preparedRequest().step().equals(control.operation().value())&&attempt.preparedRequest().requiredCapability().equals(Optional.of(control.capability())),"archived military request differs");
        var before=before(receipt.command(),binding,archive).map(value->MilitaryReceiverProof.observeFixedReinforcement(normalized(value,binding),binding));
        var dispatch=ActionTransitions.dispatch(receipt.state());if(dispatch.isEmpty()||!(dispatch.orElseThrow() instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()){
            require(!(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied),"control cannot settle without original successful ACK");return;
        }
        acknowledgement(control,binding,ack.originalResultToken().orElseThrow(),before);
        if(receipt.state() instanceof ActionState.Settled settled){
            require(settled.settlement() instanceof ActionState.ControlApplied,"military UI controls cannot grant ordinary Applied/gameplay credit");
            var actual=(ActionState.ControlApplied)settled.settlement();require(actual.observerSchema().equals(OBSERVER)&&actual.actual().equals(expected(control)),"archived control effect differs");
            require(actual.supportingReads().size()<=50,"finite independent GUI observation bound exceeded");
            for(var read:actual.supportingReads()){RawJson tree=normalized(read,binding);if(control!=Control.OPEN)requireLater(before.orElseThrow(),MilitaryReceiverProof.observeFixedReinforcement(tree,binding));}
            RawJson tree=normalized(actual.read(),binding);
            if(control==Control.OPEN)require(visible(tree),"archived opener has no visible root");
            else {var later=MilitaryReceiverProof.observeFixedReinforcement(tree,binding);requireLater(before.orElseThrow(),later);require(later.sourceSwitch().enabled()==control.desiredEnabled(),"archived later switch differs from desired");}
        }
    }
}
