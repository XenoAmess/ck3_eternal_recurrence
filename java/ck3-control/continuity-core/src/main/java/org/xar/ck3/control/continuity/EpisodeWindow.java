package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Versioned new-Game window. Values are descriptions; only the original writer proves commitment. */
public final class EpisodeWindow {
    public static final String STATE_SCHEMA = "root.ck3.continuity-window/v2";
    public static final String SCHEMA = "xar.java-episode-window/v1";
    public static final String FIELD = "java_episode_window";
    public static final String BEGIN_KIND = "JAVA_EPISODE_WINDOW_BEGIN_V1";
    public static final String BASELINE_KIND = "JAVA_EPISODE_WINDOW_BASELINE_V1";
    public static final String OPERATOR_REBIND_KIND = "JAVA_EPISODE_OPERATOR_REBIND_V1";
    public static final String OPERATOR_SCHEMA = "xar.java-episode-window/v2";
    public static final String ORIGINAL_OPERATOR_FIELD="java_original_root_operator_lineage";
    public static final String ORIGINAL_OPERATOR_SCHEMA="xar.java-original-root-operator-lineage/v1";
    public enum Phase { AWAITING_FIRST_SAVE, ACTIVE }
    private EpisodeWindow() { }

    public record Identity(String machineId, GameGeneration game, String sessionId, String episodeRunId,
                           long epoch, long actorId, long dateRaw) {
        public Identity {
            StrictJson.text(machineId); Objects.requireNonNull(game); StrictJson.text(sessionId);
            StrictJson.text(episodeRunId); StrictJson.safe(epoch, 0); NativeCharacterId.of(actorId); StrictJson.safe(dateRaw, 0);
        }
        public ObjectNode toJson() {
            ObjectNode row=StrictJson.object(); row.put("machine_id",machineId); row.set("game",game.toJson());
            row.put("session_id",sessionId); row.put("episode_run_id",episodeRunId); row.put("epoch",epoch);
            row.put("actor_id",actorId); row.put("date_raw",dateRaw); return row;
        }
        public static Identity fromJson(JsonNode value) {
            ObjectNode row=StrictJson.object(value,Set.of("machine_id","game","session_id","episode_run_id","epoch","actor_id","date_raw"));
            return new Identity(text(row,"machine_id"),GameGeneration.fromJson(row.get("game")),text(row,"session_id"),
                    text(row,"episode_run_id"),number(row,"epoch",0),NativeCharacterId.fromJson(row.get("actor_id")).value(),number(row,"date_raw",0));
        }
    }

    public record Begin(String evidenceId, Identity before, Identity after, long oldWindowId, long newWindowId,
                        String parentActionId, long lifecycleSequence, String lifecycleEventIdentity,
                        ExactRef lifecycleEventRef, ExactRef adoptedDriverRef, List<ExactRef> evidence) {
        public Begin {
            StrictJson.text(evidenceId); Objects.requireNonNull(before); Objects.requireNonNull(after);
            StrictJson.safe(oldWindowId,1); StrictJson.safe(newWindowId,1); StrictJson.text(parentActionId);
            StrictJson.safe(lifecycleSequence,1); requireDigest(lifecycleEventIdentity);
            Objects.requireNonNull(lifecycleEventRef); Objects.requireNonNull(adoptedDriverRef); evidence=List.copyOf(evidence);
            StrictJson.require(evidence.size()<=60 && evidence.stream().distinct().count()==evidence.size(),"finite distinct episode evidence");
            StrictJson.require(before.machineId().equals(after.machineId()) && !before.game().equals(after.game())
                    && !before.episodeRunId().equals(after.episodeRunId()) && after.epoch()==Math.addExact(before.epoch(),1)
                    && newWindowId==Math.addExact(oldWindowId,1),"actual next Game, episode, epoch and window ancestry required");
        }
        public ObjectNode toJson() {
            ObjectNode row=StrictJson.object(); row.put("evidence_id",evidenceId); row.set("before",before.toJson()); row.set("after",after.toJson());
            row.put("old_window_id",oldWindowId); row.put("new_window_id",newWindowId); row.put("parent_action_id",parentActionId);
            row.put("lifecycle_sequence",lifecycleSequence); row.put("lifecycle_event_identity",lifecycleEventIdentity);
            row.set("lifecycle_event_ref",lifecycleEventRef.toJson()); row.set("adopted_driver_ref",adoptedDriverRef.toJson());
            var refs=row.putArray("evidence"); evidence.forEach(ref->refs.add(ref.toJson())); return row;
        }
        public static Begin fromJson(JsonNode value) {
            ObjectNode row=StrictJson.object(value,Set.of("evidence_id","before","after","old_window_id","new_window_id","parent_action_id",
                    "lifecycle_sequence","lifecycle_event_identity","lifecycle_event_ref","adopted_driver_ref","evidence"));
            return new Begin(text(row,"evidence_id"),Identity.fromJson(row.get("before")),Identity.fromJson(row.get("after")),
                    number(row,"old_window_id",1),number(row,"new_window_id",1),text(row,"parent_action_id"),number(row,"lifecycle_sequence",1),
                    text(row,"lifecycle_event_identity"),ExactRef.fromJson(row.get("lifecycle_event_ref")),ExactRef.fromJson(row.get("adopted_driver_ref")),refs(row.get("evidence"),60));
        }
        public Request request() {
            ObjectNode details=envelope("begin:"+evidenceId,after.machineId(),lifecycleEventRef); details.set("begin",toJson());
            List<ExactRef> originals=new ArrayList<>(evidence); originals.add(lifecycleEventRef); originals.add(adoptedDriverRef);
            return new Request(BEGIN_KIND,ContinuityJson.canonical(details),originals.stream().distinct().toList());
        }
    }

    public record CommittedBegin(Begin begin,long sequence,String eventIdentity,String headDigest,Pin eventPin) {
        public CommittedBegin {
            Objects.requireNonNull(begin); StrictJson.safe(sequence,1); requireDigest(eventIdentity); requireDigest(headDigest);
            Objects.requireNonNull(eventPin); StrictJson.require(eventIdentity.equals(begin.request().identity()) && sequence>begin.lifecycleSequence(),"exact BEGIN event identity/ancestry");
        }
        public ExactRef eventRef(){return eventPin.reference();}
        public ObjectNode toJson(){return committed(begin.toJson(),"begin",sequence,eventIdentity,headDigest,eventPin);}
        public static CommittedBegin fromJson(JsonNode value){
            ObjectNode row=StrictJson.object(value,Set.of("begin","sequence","event_identity","head_digest","event_pin"));
            return new CommittedBegin(Begin.fromJson(row.get("begin")),number(row,"sequence",1),text(row,"event_identity"),text(row,"head_digest"),pin(row.get("event_pin")));
        }
    }

    public record Baseline(CommittedBegin begin,String saveActionId,ExactRef pairRef,String pairDigest,
                           ExactRef canonicalSaveReceiptRef,String proofDigest,Identity savedIdentity) {
        public Baseline {
            Objects.requireNonNull(begin); StrictJson.text(saveActionId); Objects.requireNonNull(pairRef); requireDigest(pairDigest);
            Objects.requireNonNull(canonicalSaveReceiptRef); requireDigest(proofDigest); Objects.requireNonNull(savedIdentity);
            StrictJson.require(pairRef.sha256().equals(pairDigest) && savedIdentity.equals(begin.begin().after()),
                    "first SAVE must retain the exact new opening Game/episode/actor/date/epoch and pair");
        }
        public ObjectNode toJson(){
            ObjectNode row=StrictJson.object(); row.set("begin",begin.toJson()); row.put("save_action_id",saveActionId);
            row.set("pair_ref",pairRef.toJson()); row.put("pair_digest",pairDigest); row.set("canonical_save_receipt_ref",canonicalSaveReceiptRef.toJson());
            row.put("proof_digest",proofDigest); row.set("saved_identity",savedIdentity.toJson()); return row;
        }
        public static Baseline fromJson(JsonNode value){
            ObjectNode row=StrictJson.object(value,Set.of("begin","save_action_id","pair_ref","pair_digest","canonical_save_receipt_ref","proof_digest","saved_identity"));
            return new Baseline(CommittedBegin.fromJson(row.get("begin")),text(row,"save_action_id"),ExactRef.fromJson(row.get("pair_ref")),text(row,"pair_digest"),
                    ExactRef.fromJson(row.get("canonical_save_receipt_ref")),text(row,"proof_digest"),Identity.fromJson(row.get("saved_identity")));
        }
        public Request request(){
            ObjectNode details=envelope("baseline:"+begin.begin().evidenceId(),savedIdentity.machineId(),pairRef); details.set("baseline",toJson());
            return new Request(BASELINE_KIND,ContinuityJson.canonical(details),List.of(begin.eventRef(),pairRef,canonicalSaveReceiptRef));
        }
    }
    public record CommittedBaseline(Baseline baseline,long sequence,String eventIdentity,String headDigest,Pin eventPin) {
        public CommittedBaseline {
            Objects.requireNonNull(baseline); StrictJson.safe(sequence,1); requireDigest(eventIdentity); requireDigest(headDigest); Objects.requireNonNull(eventPin);
            StrictJson.require(sequence>baseline.begin().sequence()&&eventIdentity.equals(baseline.request().identity()),"exact BASELINE event identity/ancestry");
        }
        public ExactRef eventRef(){return eventPin.reference();}
        public ObjectNode toJson(){return committed(baseline.toJson(),"baseline",sequence,eventIdentity,headDigest,eventPin);}
        public static CommittedBaseline fromJson(JsonNode value){
            ObjectNode row=StrictJson.object(value,Set.of("baseline","sequence","event_identity","head_digest","event_pin"));
            return new CommittedBaseline(Baseline.fromJson(row.get("baseline")),number(row,"sequence",1),text(row,"event_identity"),text(row,"head_digest"),pin(row.get("event_pin")));
        }
    }
    /** Original pre-commit artifacts only. The future operator commit cannot be its own input. */
    public record OperatorOriginals(ExactRef hello,ExactRef beforeNative,ExactRef ack,ExactRef afterNative,
            ExactRef beforeDriver,ExactRef afterDriver,ExactRef beforeAuxiliary,ExactRef afterAuxiliary) {
        public OperatorOriginals {
            for(ExactRef ref:List.of(hello,beforeNative,ack,afterNative,beforeDriver,afterDriver,beforeAuxiliary,afterAuxiliary))
                StrictJson.require(ref.bytes()>0,"nonempty original operator artifact required");
            StrictJson.require(!beforeDriver.equals(afterDriver),"operator requires distinct full Driver before and after originals; native receive independence belongs to the actual source custody/chronology proof");
        }
        public List<ExactRef> references(){return List.of(hello,beforeNative,ack,afterNative,beforeDriver,afterDriver,beforeAuxiliary,afterAuxiliary).stream().distinct().toList();}
        public ObjectNode toJson(){ObjectNode n=StrictJson.object();n.set("hello",hello.toJson());n.set("before_native",beforeNative.toJson());n.set("ack",ack.toJson());n.set("after_native",afterNative.toJson());n.set("before_driver",beforeDriver.toJson());n.set("after_driver",afterDriver.toJson());n.set("before_auxiliary",beforeAuxiliary.toJson());n.set("after_auxiliary",afterAuxiliary.toJson());return n;}
        public static OperatorOriginals fromJson(JsonNode value){ObjectNode n=StrictJson.object(value,Set.of("hello","before_native","ack","after_native","before_driver","after_driver","before_auxiliary","after_auxiliary"));return new OperatorOriginals(ExactRef.fromJson(n.get("hello")),ExactRef.fromJson(n.get("before_native")),ExactRef.fromJson(n.get("ack")),ExactRef.fromJson(n.get("after_native")),ExactRef.fromJson(n.get("before_driver")),ExactRef.fromJson(n.get("after_driver")),ExactRef.fromJson(n.get("before_auxiliary")),ExactRef.fromJson(n.get("after_auxiliary")));}
    }
    /** Pure DATA. Live qualification must reopen the canonical attempt/ACK/native/Driver artifacts under the original writer lock. */
    public record OperatorRebind(String evidenceId,Identity before,Identity after,long beforeDriverVersion,long afterDriverVersion,
            String actionId,String bodySha256,String requestId,ExactRef source,OperatorOriginals originals,Optional<String> previousOperatorSha256) {
        public OperatorRebind {
            StrictJson.text(evidenceId);Objects.requireNonNull(before);Objects.requireNonNull(after);StrictJson.safe(beforeDriverVersion,0);StrictJson.safe(afterDriverVersion,0);
            StrictJson.text(actionId);requireDigest(bodySha256);StrictJson.text(requestId);Objects.requireNonNull(source);Objects.requireNonNull(originals);previousOperatorSha256=Objects.requireNonNull(previousOperatorSha256);previousOperatorSha256.ifPresent(WriterContracts::requireDigest);
            StrictJson.require(source.bytes()>0&&before.machineId().equals(after.machineId())&&before.game().equals(after.game())
                    &&before.sessionId().equals(after.sessionId())&&before.episodeRunId().equals(after.episodeRunId())&&before.epoch()==after.epoch()
                    &&before.actorId()!=after.actorId()&&after.dateRaw()>=before.dateRaw()&&afterDriverVersion==Math.addExact(beforeDriverVersion,1),"operator rebind keeps the actual Game/session/run/epoch and changes actor/Driver version once");
        }
        public ObjectNode toJson(){ObjectNode n=StrictJson.object();n.put("evidence_id",evidenceId);n.set("before",before.toJson());n.set("after",after.toJson());n.put("before_driver_version",beforeDriverVersion);n.put("after_driver_version",afterDriverVersion);n.put("action_id",actionId);n.put("body_sha256",bodySha256);n.put("request_id",requestId);n.set("source",source.toJson());n.set("originals",originals.toJson());if(previousOperatorSha256.isPresent())n.put("previous_operator_sha256",previousOperatorSha256.orElseThrow());else n.putNull("previous_operator_sha256");return n;}
        public static OperatorRebind fromJson(JsonNode value){ObjectNode n=StrictJson.object(value,Set.of("evidence_id","before","after","before_driver_version","after_driver_version","action_id","body_sha256","request_id","source","originals","previous_operator_sha256"));JsonNode previous=n.get("previous_operator_sha256");return new OperatorRebind(text(n,"evidence_id"),Identity.fromJson(n.get("before")),Identity.fromJson(n.get("after")),number(n,"before_driver_version",0),number(n,"after_driver_version",0),text(n,"action_id"),text(n,"body_sha256"),text(n,"request_id"),ExactRef.fromJson(n.get("source")),OperatorOriginals.fromJson(n.get("originals")),previous.isNull()?Optional.empty():Optional.of(StrictJson.text(previous)));}
        public Request request(){ObjectNode n=envelope("operator:"+evidenceId,after.machineId(),source);n.set("operator_rebind",toJson());List<ExactRef> refs=new ArrayList<>(originals.references());refs.add(source);return new Request(OPERATOR_REBIND_KIND,ContinuityJson.canonical(n),refs.stream().distinct().toList());}
        public String digest(){return ContinuityJson.digest(toJson());}
    }
    public record State(Phase phase,Begin begin,Optional<Baseline> baseline,List<OperatorRebind> operatorLineage) {
        public State(Phase phase,Begin begin,Optional<Baseline> baseline){this(phase,begin,baseline,List.of());}
        public State {
            Objects.requireNonNull(phase); Objects.requireNonNull(begin); baseline=Objects.requireNonNull(baseline);operatorLineage=List.copyOf(operatorLineage);
            StrictJson.require((phase==Phase.ACTIVE)==baseline.isPresent(),"ACTIVE requires exactly its first SAVE baseline");
            baseline.ifPresent(value->StrictJson.require(value.begin().begin().equals(begin),"BASELINE changed original BEGIN"));
            StrictJson.require(phase==Phase.ACTIVE||operatorLineage.isEmpty(),"an awaiting first SAVE has no operator lineage");
            Optional<String> prior=Optional.empty();var ids=new java.util.HashSet<String>();
            for(OperatorRebind rebind:operatorLineage){StrictJson.require(rebind.previousOperatorSha256().equals(prior)&&ids.add(rebind.actionId())
                    &&rebind.after().machineId().equals(begin.after().machineId()),"operator lineage must retain its exact original order and machine");prior=Optional.of(rebind.digest());}
        }
        public ObjectNode toJson(){
            ObjectNode row=StrictJson.object(); row.put("schema",operatorLineage.isEmpty()?SCHEMA:OPERATOR_SCHEMA); row.put("phase",phase.name()); row.set("begin",begin.toJson());
            if(baseline.isPresent())row.set("baseline",baseline.orElseThrow().toJson());else row.putNull("baseline");
            if(!operatorLineage.isEmpty()){var entries=row.putArray("operator_lineage");operatorLineage.forEach(value->entries.add(value.toJson()));}return row;
        }
        public static State fromJson(JsonNode value){
            StrictJson.require(value!=null&&value.isObject(),"episode-window object required");String schema=StrictJson.text(value.get("schema"));boolean operator=OPERATOR_SCHEMA.equals(schema);
            ObjectNode row=StrictJson.object(value,operator?Set.of("schema","phase","begin","baseline","operator_lineage"):Set.of("schema","phase","begin","baseline"));
            StrictJson.require(operator||SCHEMA.equals(schema),"exact episode-window schema");
            Phase phase;try{phase=Phase.valueOf(text(row,"phase"));}catch(IllegalArgumentException failure){throw new org.xar.ck3.control.contracts.ContractViolationException("episode-window phase");}
            StrictJson.require(row.has("baseline"),"explicit baseline null/value required");
            List<OperatorRebind> entries=new ArrayList<>();if(operator){StrictJson.require(row.get("operator_lineage").isArray()&&!row.get("operator_lineage").isEmpty(),"v2 requires actual nonempty operator lineage");row.get("operator_lineage").forEach(entry->entries.add(OperatorRebind.fromJson(entry)));}
            return new State(phase,Begin.fromJson(row.get("begin")),row.get("baseline").isNull()?Optional.empty():Optional.of(Baseline.fromJson(row.get("baseline"))),entries);
        }
    }
    /** Original Root has no invented BEGIN/BASELINE. Its operator ancestry is a separate versioned DATA branch. */
    public record OriginalRootOperators(List<OperatorRebind> entries) {
        public OriginalRootOperators {
            entries=List.copyOf(entries);StrictJson.require(!entries.isEmpty(),"original Root operator lineage must be nonempty");
            Optional<String> prior=Optional.empty();var ids=new java.util.HashSet<String>();String machine=entries.getFirst().before().machineId();
            for(var entry:entries){StrictJson.require(entry.before().machineId().equals(machine)&&entry.previousOperatorSha256().equals(prior)
                    &&ids.add(entry.actionId()),"original Root operator lineage order/machine/action identity changed");prior=Optional.of(entry.digest());}
        }
        public ObjectNode toJson(){ObjectNode row=StrictJson.object();row.put("schema",ORIGINAL_OPERATOR_SCHEMA);var values=row.putArray("entries");entries.forEach(entry->values.add(entry.toJson()));return row;}
        public static OriginalRootOperators fromJson(JsonNode value){ObjectNode row=StrictJson.object(value,Set.of("schema","entries"));
            StrictJson.require(ORIGINAL_OPERATOR_SCHEMA.equals(text(row,"schema"))&&row.get("entries").isArray(),"exact original Root operator schema/list required");
            List<OperatorRebind> entries=new ArrayList<>();row.get("entries").forEach(entry->entries.add(OperatorRebind.fromJson(entry)));return new OriginalRootOperators(entries);}
    }
    /** The active branch only; earlier original-Root ancestry remains immutable after a genuine new window. */
    public static List<OperatorRebind> operatorLineage(ContinuityState value){
        Optional<State> window=state(value);if(window.isPresent())return window.orElseThrow().operatorLineage();
        ObjectNode row=value.toJson();return row.has(ORIGINAL_OPERATOR_FIELD)?OriginalRootOperators.fromJson(row.get(ORIGINAL_OPERATOR_FIELD)).entries():List.of();
    }
    public static Optional<State> state(ContinuityState state){return state(state.toJson());}
    public static Optional<State> state(ObjectNode row){return row.has(FIELD)?Optional.of(State.fromJson(row.get(FIELD))):Optional.empty();}
    public static State requireActive(ContinuityState head){
        State active=state(head).orElseThrow(()->new org.xar.ck3.control.contracts.ContractViolationException("explicit new episode window unavailable"));
        StrictJson.require(active.phase()==Phase.ACTIVE,"first SAVE BASELINE has not been committed");return active;
    }
    public static boolean isTransition(String kind){return BEGIN_KIND.equals(kind)||BASELINE_KIND.equals(kind)||OPERATOR_REBIND_KIND.equals(kind);}
    public static OperatorRebind operatorRebind(Request request){ObjectNode n=StrictJson.object(request.detailsObject(),Set.of("evidence_id","machine_id","source","operator_rebind"));OperatorRebind result=OperatorRebind.fromJson(n.get("operator_rebind"));StrictJson.require(request.kind().equals(OPERATOR_REBIND_KIND)&&ContinuityJson.same(n,result.request().detailsObject()),"exact typed operator envelope required");return result;}
    public static Begin begin(Request request){
        ObjectNode row=StrictJson.object(request.detailsObject(),Set.of("evidence_id","machine_id","source","begin"));Begin begin=Begin.fromJson(row.get("begin"));
        StrictJson.require(request.kind().equals(BEGIN_KIND)&&ContinuityJson.same(begin.request().detailsObject(),row),"exact typed BEGIN envelope required");return begin;
    }
    public static Baseline baseline(Request request){
        ObjectNode row=StrictJson.object(request.detailsObject(),Set.of("evidence_id","machine_id","source","baseline"));Baseline baseline=Baseline.fromJson(row.get("baseline"));
        StrictJson.require(request.kind().equals(BASELINE_KIND)&&ContinuityJson.same(baseline.request().detailsObject(),row),"exact typed BASELINE envelope required");return baseline;
    }
    /** Pure reducer. Runtime custody and actual canonical SAVE validation are mandatory authority work. */
    public static ContinuityState reduce(ContinuityState before,Request request){
        ObjectNode next=before.toJson();
        if(BEGIN_KIND.equals(request.kind())){
            Begin begin=begin(request);StrictJson.require(begin.after().machineId().equals(before.machineId())&&before.origin().windowId()==begin.oldWindowId()
                    &&begin.lifecycleSequence()<=before.sequence(),"BEGIN predecessor machine/window/lifecycle ancestry differs");
            Optional<State> old=state(before);if(old.isPresent()){
                State previous=old.orElseThrow();StrictJson.require(previous.phase()==Phase.ACTIVE,"unresolved first SAVE cannot begin another Game");
                Identity prior=previous.begin().after();GameGeneration current=GameGeneration.fromJson(before.toJson().get("game_binding"));
                StrictJson.require(current.equals(begin.before().game())&&(!current.equals(prior.game())||prior.sessionId().equals(begin.before().sessionId()))
                        &&prior.epoch()<=begin.before().epoch(),"new window must descend from the actual current Game and nondecreasing episode ancestry");
                // A real saved attachment may have replaced Game/session since the immutable first opening.
                // The installed authority still revalidates the actual private current owner; old BEGIN is never rewritten.
            }
            next.put("schema",STATE_SCHEMA);next.put("status","awaiting_first_save");next.set(FIELD,new State(Phase.AWAITING_FIRST_SAVE,begin,Optional.empty()).toJson());
        }else if(BASELINE_KIND.equals(request.kind())){
            Baseline baseline=baseline(request);State waiting=state(before).orElseThrow();
            StrictJson.require(waiting.phase()==Phase.AWAITING_FIRST_SAVE&&waiting.begin().equals(baseline.begin().begin())
                    &&before.origin().windowId()==waiting.begin().oldWindowId()&&baseline.begin().sequence()<=before.sequence(),"BASELINE requires this exact still-awaiting BEGIN");
            Identity identity=baseline.savedIdentity();long targetDays=before.origin().targetDays();
            next.set(FIELD,new State(Phase.ACTIVE,waiting.begin(),Optional.of(baseline)).toJson());next.put("window_id",waiting.begin().newWindowId());
            next.put("start_date_raw",identity.dateRaw());next.put("target_date_raw",Math.addExact(identity.dateRaw(),Math.multiplyExact(targetDays,24)));
            next.put("last_settled_date_raw",identity.dateRaw());next.put("last_settled_cycles",0);next.put("status","running");next.set("game_binding",identity.game().toJson());
            ObjectNode frame=StrictJson.object();frame.put("date_raw",identity.dateRaw());frame.put("actor_character_id",identity.actorId());frame.put("episode_run_id",identity.episodeRunId());
            next.set("latest_binding",frame);next.set("window_start_source",baseline.pairRef().toJson());
        }else if(OPERATOR_REBIND_KIND.equals(request.kind())){
            OperatorRebind rebind=operatorRebind(request);Optional<State> window=state(before);window.ifPresent(value->requireActive(before));Identity identity=rebind.before();
            StrictJson.require(before.status()!=ContinuityState.Status.AWAITING_FIRST_SAVE,"operator cannot bypass an actual pending first SAVE");
            StrictJson.require(identity.machineId().equals(before.machineId()),"operator source crossed the original writer machine");
            if(window.isPresent()) {
                StrictJson.require(GameGeneration.fromJson(next.get("game_binding")).equals(identity.game()),"operator cannot replace another active window Game");
                ObjectNode binding=StrictJson.object(next.get("latest_binding"),Set.of("date_raw","actor_character_id","episode_run_id"));StrictJson.require(NativeCharacterId.fromJson(binding.get("actor_character_id")).value()==identity.actorId()
                        &&StrictJson.text(binding.get("episode_run_id")).equals(identity.episodeRunId())&&number(binding,"date_raw",0)<=identity.dateRaw(),"operator predecessor does not match actual current window binding");
            }
            var entries=new ArrayList<>(operatorLineage(before));Optional<String> expected=entries.isEmpty()?Optional.empty():Optional.of(entries.getLast().digest());StrictJson.require(rebind.previousOperatorSha256().equals(expected),"operator predecessor lineage differs");entries.add(rebind);
            if(window.isPresent()){
                State active=window.orElseThrow();next.set(FIELD,new State(active.phase(),active.begin(),active.baseline(),entries).toJson());
                ObjectNode after=StrictJson.object();after.put("actor_character_id",rebind.after().actorId());after.put("date_raw",rebind.after().dateRaw());after.put("episode_run_id",rebind.after().episodeRunId());next.set("latest_binding",after);
            }else {
                // Original Root's older opening may be absent or have a legacy representation. It is never
                // converted into a full identity here. The installed private authority must bind the real
                // full Game/session/Driver/ACK/after originals; this pure DATA branch preserves the old opening.
                next.set(ORIGINAL_OPERATOR_FIELD,new OriginalRootOperators(entries).toJson());
            }
            next.put("binding_lineage_count",Math.addExact(number(next,"binding_lineage_count",0),1));
        }else throw new org.xar.ck3.control.contracts.ContractViolationException("unsupported EpisodeWindow transition");
        return ContinuityState.fromJson(next,before.machineId());
    }
    /** Envelope/history and writer share this exact whole-state comparison. */
    public static void requireReduction(ContinuityState before,ContinuityState after,Request request,boolean committed){
        ContinuityState reduced=reduce(before,request);ObjectNode expected=reduced.toJson();
        if(committed){expected.put("sequence",Math.addExact(before.sequence(),1));expected.put("last_event_identity",request.identity());}
        StrictJson.require(ContinuityJson.same(expected,after.toJson()),"episode transition differs from its exact pure reducer");
    }
    private static ObjectNode envelope(String id,String machine,ExactRef source){ObjectNode row=StrictJson.object();row.put("evidence_id",id);row.put("machine_id",machine);row.set("source",source.toJson());return row;}
    private static ObjectNode committed(ObjectNode body,String key,long sequence,String identity,String digest,Pin pin){
        ObjectNode row=StrictJson.object();row.set(key,body);row.put("sequence",sequence);row.put("event_identity",identity);row.put("head_digest",digest);row.set("event_pin",pin(pin));return row;
    }
    private static ObjectNode pin(Pin pin){
        return pin.toJson();
    }
    private static Pin pin(JsonNode value){
        return Pin.fromJson(value);
    }
    private static List<ExactRef> refs(JsonNode value,int maximum){StrictJson.require(value!=null&&value.isArray()&&value.size()<=maximum,"finite exact reference array");List<ExactRef> result=new ArrayList<>();value.forEach(row->result.add(ExactRef.fromJson(row)));return List.copyOf(result);}
    private static long number(ObjectNode row,String key,long minimum){return StrictJson.integer(row.get(key),minimum,StrictJson.MAX_SAFE_INTEGER);}
    private static String text(ObjectNode row,String key){return StrictJson.text(row.get(key));}
}
