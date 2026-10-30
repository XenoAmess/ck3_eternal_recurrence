package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.LinkedHashMap;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.interactionbefore.CurrentInteractionPresentation;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;

/** The native bridge translates the one-based step into the exact native option index; it takes no extra event payload. */
public final class EventActionPreparation {
    public static final String EVENT_CAPABILITY="game.command.select-event-option-N";
    private EventActionPreparation() { }
    public sealed interface PendingPresentation permits EventPresentation,InteractionPresentation {
        int instanceId();
    }
    /** The v1 enabled field samples the option flag; stock GUI validity also depends on its native owner gate. */
    public record EventPresentation(EventWindowModels.Available context,EventWindowModels.Option selected) implements PendingPresentation {
        public EventPresentation {
            Objects.requireNonNull(context);Objects.requireNonNull(selected);
            StrictJson.require(context.options().contains(selected)&&selected.selectionAllowed(),"pending event requires its original displayed option to permit selection");
        }
        @Override public int instanceId(){return context.binding().eventInstanceId();}
    }
    public record InteractionPresentation(CurrentInteractionPresentation.Presentation current) implements PendingPresentation {
        public InteractionPresentation{Objects.requireNonNull(current);}
        @Override public int instanceId(){return current.pending().instanceId();}
    }
    /** Immutable preparation DATA for the Root's own canonical once-event intent. No token or submit permission. */
    public record PendingPrepared(ActionCommand command,PlanningReadReceipt originalRead,ExactRef originalReadRef,
            PendingPresentation presentation,List<ExactRef> sourceOriginals){
        public PendingPrepared{
            Objects.requireNonNull(command);Objects.requireNonNull(originalRead);Objects.requireNonNull(originalReadRef);Objects.requireNonNull(presentation);
            sourceOriginals=List.copyOf(sourceOriginals);StrictJson.require(!sourceOriginals.isEmpty()&&sourceOriginals.size()<=32&&originalReadRef.bytes()>0
                    &&sourceOriginals.contains(originalReadRef)&&new java.util.HashSet<>(sourceOriginals).size()==sourceOriginals.size(),"actual pending preparation unique original read/source closure required");
            StrictJson.require(originalRead.request().before().equals(command.before())&&originalRead.request().source().equals(command.source())
                    &&originalRead.request().sessionId().equals(command.sessionId())&&originalRead.request().deadline().equals(command.deadline())
                    &&originalRead.original().nativeOk(),"pending preparation changed its original physical read frame/source/session/deadline");
            NativeRequest prepared=prepare(command);
            if(presentation instanceof EventPresentation event){
                StrictJson.require(option(command.operation()).value()==event.selected().publicOptionNumber().intValueExact()
                        &&integer(command.arguments(),"event_instance_id").equals(BigInteger.valueOf(event.instanceId()))
                        &&integer(command.arguments(),"rendered_index").equals(BigInteger.valueOf(event.selected().renderedIndex()))
                        &&event.context().binding().nativeRevision().equals(command.before().frame().identity().nativeRevision())
                        &&BigInteger.valueOf(event.context().binding().dateRaw()).equals(command.before().frame().identity().dateRaw()),"pending event prepared another original instance/frame/displayed native option");
            }else StrictJson.require(CurrentInteractionPresentation.requireSubmission(StrictJson.parse(OpportunityJson.encode(command.arguments().get("unhandled_interaction_fallback"))),prepared.step(),presentation.instanceId())
                    .equals(((InteractionPresentation)presentation).current()),"pending reply presentation differs from its retained complete capture");
        }
    }
    public static final class PendingSelectionRejected extends IllegalArgumentException {
        private static final long serialVersionUID=1L;
        private final OpportunityJson.Obj diagnosis;private final ExactRef originalRead;
        public PendingSelectionRejected(OpportunityJson.Obj diagnosis,ExactRef originalRead){
            super("private pending UI has no supported retained choice; original read="+Objects.requireNonNull(originalRead).sha256());
            this.diagnosis=Objects.requireNonNull(diagnosis);this.originalRead=originalRead;
        }
        public OpportunityJson.Obj diagnosis(){return diagnosis;}
        public ExactRef originalRead(){return originalRead;}
    }
    /** Pure original presentation/identity recheck. The Root Source separately proves the once-intent and publication CAS lineage. */
    public static void requirePendingUiEventCurrent(PendingPrepared original,PendingPrepared actualFresh){
        var old=original.command();var fresh=actualFresh.command();
        StrictJson.require(old.actionId().equals(fresh.actionId())&&old.origin().equals(fresh.origin())&&old.source().equals(fresh.source())
                &&old.sessionId().equals(fresh.sessionId())&&old.operation().equals(fresh.operation())&&old.expectation().equals(fresh.expectation())
                &&old.claims().equals(fresh.claims())&&old.deadline().equals(fresh.deadline()),"private event recheck changed retained command identity/expectation/claims/deadline");
        StrictJson.require(original.presentation().getClass()==actualFresh.presentation().getClass()
                &&original.presentation().instanceId()==actualFresh.presentation().instanceId(),"private event recheck changed original window or primary reply kind");
        if(original.presentation() instanceof EventPresentation event){
            var now=(EventPresentation)actualFresh.presentation();StrictJson.require(event.selected().equals(now.selected())
                    &&jsonEqual(event.context().original().bytes(),now.context().original().bytes()),"private event definition/scopes/display/options/effects changed");
        }else StrictJson.require(((InteractionPresentation)original.presentation()).current().equals(((InteractionPresentation)actualFresh.presentation()).current()),"private notification definition/roles/left-button legality changed");
        var a=original.originalRead();var b=actualFresh.originalRead();
        StrictJson.require(a.contractId().equals(b.contractId())&&a.request().origin().equals(b.request().origin())&&a.request().source().equals(b.request().source())
                &&a.request().sessionId().equals(b.request().sessionId())&&a.request().operation().equals(b.request().operation())&&a.request().deadline().equals(b.request().deadline())
                &&!a.requestId().equals(b.requestId())&&!original.originalReadRef().equals(actualFresh.originalReadRef()),"private event freshness reused or changed its original query identity/contract");
        var originalGuard=a.before().binding();
        for(var guard:List.of(a.after().binding(),b.before().binding(),b.after().binding()))
            StrictJson.require(guard.origin().equals(originalGuard.origin())&&guard.source().equals(originalGuard.source())
                    &&guard.sessionId().equals(originalGuard.sessionId())&&guard.connectionGeneration().equals(originalGuard.connectionGeneration())
                    &&guard.operation().equals(originalGuard.operation())&&guard.nativeEvidence().equals(originalGuard.nativeEvidence())
                    &&guard.capabilityEvidence().equals(originalGuard.capabilityEvidence())&&guard.authorityId().equals(originalGuard.authorityId()),
                    "private event recheck changed the original physical native/HELLO/source/session read authority");
        var first=DriverJson.object(a.original().originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES);
        var second=DriverJson.object(b.original().originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES);
        var sequence=integer(first,"query_sequence");var later=integer(second,"query_sequence");
        StrictJson.require(sequence.signum()>0&&later.compareTo(sequence)>0&&later.bitLength()<=64,"private event recheck lacks an actual later native query sequence");
        StrictJson.require(without(first,Set.of("query_sequence")).equals(without(second,Set.of("query_sequence"))),"private event original native context or envelope changed beyond its query sequence");
        StrictJson.require(comparableArguments(original).equals(comparableArguments(actualFresh)),"private event recheck changed non-observational command arguments");
        prepare(old);prepare(fresh);
    }
    private static OpportunityJson.Obj comparableArguments(PendingPrepared value){
        var args=value.command().arguments();var meta=OpportunityJson.object(args.get("pending_ui_event_source"),"actual private source metadata");
        StrictJson.require(meta.members().keySet().equals(Set.of("schema","original_parent_action_id","original_parent_body_sha256","original_read","source_originals"))
                &&new OpportunityJson.Text("xar.pending-ui-event-source/v1").equals(meta.get("schema"))
                &&org.xar.ck3.control.contracts.ExactRef.fromJson(DriverJson.toNode(meta.get("original_read"))).equals(value.originalReadRef()),"private source metadata/read binding differs");
        var refs=(OpportunityJson.Arr)meta.get("source_originals");var sourceRefs=refs.items().stream().map(row->ExactRef.fromJson(DriverJson.toNode(row))).toList();
        var expected=new java.util.ArrayList<>(sourceRefs);if(!expected.contains(value.originalReadRef()))expected.add(value.originalReadRef());
        StrictJson.require(expected.equals(value.sourceOriginals()),"private source metadata dropped or replaced an original provenance reference");
        var result=new LinkedHashMap<>(args.members());result.put("pending_ui_event_source",without(meta,Set.of("original_read","source_originals")));
        if(value.presentation() instanceof EventPresentation){
            var read=OpportunityJson.object(result.get("public_event_window_read"),"actual private event history");
            StrictJson.require(read.members().keySet().equals(Set.of("command","ok","result","native_read_request_id","read_contract_id","native_read_original_receipt"))
                    &&new OpportunityJson.Text(value.originalRead().requestId()).equals(read.get("native_read_request_id"))
                    &&new OpportunityJson.Text(value.originalRead().contractId()).equals(read.get("read_contract_id"))
                    &&ExactRef.fromJson(DriverJson.toNode(read.get("native_read_original_receipt"))).equals(value.originalReadRef()),"private event history changed original read identity");
            var row=new LinkedHashMap<>(read.members());row.put("result",without(OpportunityJson.object(read.get("result"),"actual window publication"),Set.of("query_sequence")));
            result.put("public_event_window_read",without(new OpportunityJson.Obj(row),Set.of("native_read_request_id","native_read_original_receipt")));
        }
        return new OpportunityJson.Obj(result);
    }
    private static OpportunityJson.Obj without(OpportunityJson.Obj row,Set<String> fields){var copy=new LinkedHashMap<>(row.members());fields.forEach(copy::remove);return new OpportunityJson.Obj(copy);}
    private static boolean jsonEqual(byte[] first,byte[] second){return DriverJson.object(first,RawJson.MAXIMUM_BYTES).equals(DriverJson.object(second,RawJson.MAXIMUM_BYTES));}
    public record OptionNumber(int value) {
        public OptionNumber { StrictJson.require(value>0&&value<=999999999,"source-supported positive event option number required"); }
        public org.xar.ck3.control.application.action.OperationKey operation() { return new org.xar.ck3.control.application.action.OperationKey("select-event-option-"+value); }
    }
    public static OptionNumber option(org.xar.ck3.control.application.action.OperationKey operation) {
        String step=Objects.requireNonNull(operation).value();StrictJson.require(step.matches("select-event-option-[1-9][0-9]{0,8}"),"exact source-supported event option step required");return new OptionNumber(Integer.parseInt(step.substring("select-event-option-".length())));
    }
    public static RawJson encode(OptionNumber value) { return new RawJson(StrictJson.canonical(StrictJson.object().put("option_number",value.value()))); }
    public static NativeRequest prepare(ActionCommand command) {
        Objects.requireNonNull(command);String schema=command.expected().observerSchema();
        List<BigInteger> originals=command.expected().values().stream().filter(value->value.field().value().equals("old_instance_id"))
                .filter(ExpectedInteger.class::isInstance).map(ExpectedInteger.class::cast).map(ExpectedInteger::value).toList();
        StrictJson.require(originals.size()==1,"event/pending command requires its exact original native instance");BigInteger old=originals.getFirst();
        StrictJson.require(old.bitLength()<=31,"native full instance width differs");
        if(NativeEventPostconditionPort.EVENT_SCHEMA.equals(schema)) {
            OptionNumber option=option(command.operation());OpportunityJson.Obj args=command.arguments();StrictJson.require(old.signum()>0,"positive full event instance required");
            StrictJson.require(integer(args,"event_instance_id").equals(old)&&integer(args,"option_number").equals(BigInteger.valueOf(option.value()))
                    &&integer(args,"native_option_index").equals(BigInteger.valueOf(option.value()-1L))
                    &&integer(args,"rendered_index").signum()>=0,"selected native/rendered option differs from its retained event plan");
            StrictJson.require(args.get("selected_step") instanceof OpportunityJson.Text selected&&selected.value().equals(command.operation().value()),"event selected step differs from the prepared operation");
            return new NativeRequest(command.operation().value(),EVENT_CAPABILITY,new RawJson(new byte[]{'{','}'}));
        }
        StrictJson.require(NativeEventPostconditionPort.PENDING_SCHEMA.equals(schema)&&!old.equals(BigInteger.valueOf(-1))
                &&List.of("reject-pending-character-interaction","acknowledge-pending-character-interaction").contains(command.operation().value()),"source-reviewed pending reply/schema required");
        StrictJson.require(command.arguments().get("selected_step") instanceof OpportunityJson.Text selected
                &&selected.value().equals(command.operation().value()),"source-reviewed pending selected step differs from its installed operation");
        OpportunityJson.Value declared=command.arguments().get("pending_interaction_id");if(declared!=null&&declared!=OpportunityJson.Nil.INSTANCE)StrictJson.require(OpportunityJson.integer(declared,"pending instance").equals(old),"retained pending instance changed");
        StrictJson.require(command.arguments().get("unhandled_interaction_fallback") instanceof OpportunityJson.Obj capture
                &&new OpportunityJson.Text("xar.pending-interaction-left-reply/v1").equals(capture.get("schema"))
                &&old.equals(integer(capture,"pending_interaction_id")),"actual source-reviewed left-reply capture must bind the original pending instance");
        var current=CurrentInteractionPresentation.requireSubmission(
                StrictJson.parse(OpportunityJson.encode(command.arguments().get("unhandled_interaction_fallback"))),command.operation().value(),old.intValueExact());
        var binding=current.binding();var before=command.before();
        StrictJson.require(binding.snapshotId().equals(before.frame().snapshotId())&&binding.revision().equals(before.frame().revision())
                &&binding.nativeRevision().equals(before.frame().identity().nativeRevision())&&binding.dateRaw().equals(before.frame().identity().dateRaw())
                &&binding.episodeRunId().equals(before.frame().episodeRunId())&&BigInteger.valueOf(binding.actorCharacterId()).equals(before.frame().identity().player())
                &&binding.bridgePid()==before.game().pid(),"source-reviewed reply changed its original complete planning frame");
        List<String> generations=command.expected().values().stream().filter(value->value.field().value().equals("connection_generation_decimal"))
                .filter(org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText.class::isInstance)
                .map(org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText.class::cast).map(org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText::value).toList();
        StrictJson.require(generations.size()==1&&generations.getFirst().equals(binding.connectionGeneration().toString()),"source-reviewed reply changed its original connection generation");
        return new NativeRequest(command.operation().value(),"game.command."+command.operation().value(),new RawJson(StrictJson.canonical(StrictJson.object().put("pending_interaction_id",old))));
    }
    private static BigInteger integer(OpportunityJson.Obj object,String field) { return OpportunityJson.integer(object.get(field),field); }
}
