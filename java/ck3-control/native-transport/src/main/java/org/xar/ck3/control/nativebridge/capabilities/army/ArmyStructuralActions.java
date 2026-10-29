package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original three structural Army branches. Pure DATA rules grant neither a Native ticket nor Applied. */
public final class ArmyStructuralActions {
    public enum Kind { HALT,SPLIT_HALF,MERGE }
    public enum DriverFailureReason { CONTROLLABLE_SOURCE, CONTROLLABLE_PAIR, SAME_PROVINCE_NONCOMBAT, DATE_RAW, HALT_ROUTE_READBACK }
    /** Only the original Driver branches issue this fault; parsing failures are not Driver failures. */
    public static final class DriverUnavailable extends IllegalArgumentException {
        private static final long serialVersionUID=1L;
        private final DriverFailureReason reason;
        private DriverUnavailable(DriverFailureReason reason,String message){super(message);this.reason=Objects.requireNonNull(reason);}
        public DriverFailureReason reason(){return reason;}
    }
    public sealed interface Call permits Halt,SplitHalf,Merge {
        Kind kind();ArmyTypes.PublicUnitId source();OperationKey operation();String capability();
    }
    public record Halt(ArmyTypes.PublicUnitId source) implements Call {
        public Halt {Objects.requireNonNull(source);}
        public Kind kind(){return Kind.HALT;}
        public OperationKey operation(){return new OperationKey("halt-army-"+source.value());}
        public String capability(){return "game.command.halt-army-N";}
    }
    public record SplitHalf(ArmyTypes.PublicUnitId source) implements Call {
        public SplitHalf {Objects.requireNonNull(source);}
        public Kind kind(){return Kind.SPLIT_HALF;}
        public OperationKey operation(){return new OperationKey("split-army-half-"+source.value());}
        public String capability(){return "game.command.split-army-half-N";}
    }
    public record Merge(ArmyTypes.PublicUnitId destination,ArmyTypes.PublicUnitId source) implements Call {
        public Merge {Objects.requireNonNull(destination);Objects.requireNonNull(source);StrictJson.require(!destination.equals(source),"merge subjects must differ");}
        public Kind kind(){return Kind.MERGE;}
        public OperationKey operation(){return new OperationKey("merge-armies-"+destination.value()+"-with-"+source.value());}
        public String capability(){return "game.command.merge-armies-N-with-N";}
    }
    private static final Pattern HALT=Pattern.compile("halt-army-(0|[1-9][0-9]*)");
    private static final Pattern SPLIT=Pattern.compile("split-army-half-(0|[1-9][0-9]*)");
    private static final Pattern MERGE=Pattern.compile("merge-armies-(0|[1-9][0-9]*)-with-(0|[1-9][0-9]*)");
    private ArmyStructuralActions(){ }
    public static Optional<Call> parse(OperationKey operation) {
        Objects.requireNonNull(operation);String text=operation.value();
        try {
            var halt=HALT.matcher(text);if(halt.matches())return Optional.of(new Halt(unit(halt.group(1))));
            var split=SPLIT.matcher(text);if(split.matches())return Optional.of(new SplitHalf(unit(split.group(1))));
            var merge=MERGE.matcher(text);if(merge.matches())return Optional.of(new Merge(unit(merge.group(1)),unit(merge.group(2))));
        }catch(IllegalArgumentException outside){return Optional.empty();}
        return Optional.empty();
    }
    private static ArmyTypes.PublicUnitId unit(String value){return new ArmyTypes.PublicUnitId(Integer.parseInt(value));}
    public static void preflight(Call call,Obj before) {
        Objects.requireNonNull(call);Objects.requireNonNull(before);
        Optional<Obj> selected=army(before,call.source().value());
        if(selected.isEmpty()||!truth(selected.orElseThrow(),"controllable"))throw unavailableSource(call);
        Obj source=selected.orElseThrow();
        if(call instanceof Merge merge) {
            Optional<Obj> destination=army(before,merge.destination().value());
            if(destination.isEmpty()||!truth(destination.orElseThrow(),"controllable"))throw unavailableSource(call);
            Value province=value(destination.orElseThrow(),"current_province_id");
            if(!(province instanceof IntegerValue id)||id.value().signum()<=0||id.value().bitLength()>31
                    ||!value(source,"current_province_id").equals(province)||mergeBlocked(source)||mergeBlocked(destination.orElseThrow()))
                throw new DriverUnavailable(DriverFailureReason.SAME_PROVINCE_NONCOMBAT,"native merge-armies requires an advertised same-province non-combat pair");
        }
        // The original Halt branch validates date only after the primitive returned successfully.
        // Its exact validator-deferred branch never requires an integral date.
        if(!(call instanceof Halt))dateRaw(call,before);
    }
    private static DriverUnavailable unavailableSource(Call call) {
        if(call instanceof Merge)return new DriverUnavailable(DriverFailureReason.CONTROLLABLE_PAIR,"native merge-armies requires two controllable player armies");
        return new DriverUnavailable(DriverFailureReason.CONTROLLABLE_SOURCE,call instanceof Halt?"native halt requires a controllable player army":
                "native split-army-half-"+call.source().value()+" requires a controllable player army");
    }
    private static BigInteger dateRaw(Call call,Obj before) {
        if(before.get("date_raw") instanceof IntegerValue date)return date.value();
        throw new DriverUnavailable(DriverFailureReason.DATE_RAW,
                "native "+(call instanceof Halt?"halt":call instanceof Merge?"merge-armies":"split-army-half")+" starting snapshot lacks date_raw");
    }
    /** Original first matching row, but boolean/float/string/overflow IDs cannot alias a public CUnit. */
    public static Optional<Obj> army(Obj frame,int subject) {
        if(!(frame.get("player_armies") instanceof Arr armies))return Optional.empty();
        for(Value row:armies.items())if(row instanceof Obj object && object.get("army_id") instanceof IntegerValue id
                &&id.value().equals(BigInteger.valueOf(subject)))return Optional.of(object);
        return Optional.empty();
    }
    public static List<Integer> controllableIds(Obj frame) {
        var ids=new TreeSet<Integer>();
        if(frame.get("player_armies") instanceof Arr armies)for(Value row:armies.items())
            if(row instanceof Obj object&&truth(object,"controllable")&&object.get("army_id") instanceof IntegerValue id
                    &&id.value().signum()>=0&&id.value().bitLength()<=31)ids.add(id.value().intValueExact());
        return List.copyOf(ids);
    }
    public static boolean mergeBlocked(Obj army) {
        if(truth(army,"in_combat")||truth(army,"retreating"))return true;
        Value state=army.get("army_state");
        if(state instanceof Text text&&text.value().chars().allMatch(c->c<128)
                &&(text.value().equalsIgnoreCase("combat")||text.value().equalsIgnoreCase("retreating")))return true;
        return army.get("army_state_code") instanceof IntegerValue code
                &&(code.value().equals(BigInteger.TWO)||code.value().equals(BigInteger.valueOf(6)));
    }
    public static boolean applied(Call call,Obj before,Obj after) {
        if(call instanceof Halt)return false;
        List<Integer> previous=controllableIds(before),current=controllableIds(after);
        if(call instanceof SplitHalf) {
            var added=new TreeSet<>(current);added.removeAll(previous);
            return current.contains(call.source().value())&&added.size()==1;
        }
        Merge merge=(Merge)call;Obj destinationBefore=army(before,merge.destination().value()).orElseThrow();
        Optional<Obj> destination=army(after,merge.destination().value());
        var expected=new TreeSet<>(previous);expected.remove(merge.source().value());
        return truth(after,"paused")&&truth(after,"map_ready")
                &&value(after,"episode_run_id").equals(value(before,"episode_run_id"))
                &&later(before,after,"revision")&&later(before,after,"native_revision")
                &&after.get("snapshot_id") instanceof Text&& !value(after,"snapshot_id").equals(value(before,"snapshot_id"))
                &&destination.isPresent()
                &&value(destination.orElseThrow(),"owner_character_id").equals(value(destinationBefore,"owner_character_id"))
                &&value(destination.orElseThrow(),"current_province_id").equals(value(destinationBefore,"current_province_id"))
                &&army(after,merge.source().value()).isEmpty()&&new TreeSet<>(current).equals(expected);
    }
    private static boolean later(Obj before,Obj after,String key) {
        return before.get(key) instanceof IntegerValue previous&&after.get(key) instanceof IntegerValue current
                &&current.value().compareTo(previous.value())>0;
    }
    /** Full original war_action, including submitted and observed frame/set fields. */
    public static RawJson format(Call call,Obj before,Obj after,RawJson primitive) {
        preflight(call,before);
        Obj result=DriverJson.object(primitive.bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(new Text(call.operation().value()).equals(result.get("step"))&&result.get("accepted") instanceof Bool,
                "structural primitive changed its original step/strict accepted token");
        var fields=new LinkedHashMap<>(result.members());fields.put("backend_id",new Text("native-headless"));
        var action=new LinkedHashMap<String,Value>();boolean applied=applied(call,before,after);
        List<Integer> previous=controllableIds(before);
        action.put("status",new Text(call instanceof Halt?"halt_submitted":call instanceof SplitHalf?
                (applied?"split_applied":"split_submitted"):(applied?"merge_applied":"merge_submitted")));
        action.put(call instanceof Halt?"army_id":"source_army_id",number(call.source().value()));
        action.put("submitted_date_raw",new IntegerValue(dateRaw(call,before)));
        if(call instanceof SplitHalf) {
            action.put("player_army_ids_before",ids(previous));
            if(applied){var added=new TreeSet<>(controllableIds(after));added.removeAll(previous);action.put("sibling_army_id",number(added.first()));}
        } else if(call instanceof Merge merge) {
            Obj destination=army(before,merge.destination().value()).orElseThrow(), source=army(before,merge.source().value()).orElseThrow();
            action.put("destination_army_id",number(merge.destination().value()));
            for(String key:List.of("snapshot_id","revision","native_revision","episode_run_id"))
                action.put(switch(key){case "revision"->"submitted_public_revision";default->"submitted_"+key;},value(before,key));
            action.put("destination_owner_character_id",value(destination,"owner_character_id"));
            action.put("destination_province_id",value(destination,"current_province_id"));
            action.put("source_owner_character_id",value(source,"owner_character_id"));action.put("source_province_id",value(source,"current_province_id"));
            action.put("player_army_ids_before",ids(previous));action.put("postcondition_verified",new Bool(applied));
            action.put("source_army_id_absent",new Bool(army(after,merge.source().value()).isEmpty()));
            action.put("player_army_ids_after",ids(controllableIds(after)));
            for(String key:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id"))
                action.put(switch(key){case "revision"->"observed_public_revision";default->"observed_"+key;},value(after,key));
        } else {
            Obj source=army(before,call.source().value()).orElseThrow();
            action.put("submitted_native_revision",value(before,"native_revision"));
            action.put("submitted_connection_generation",before.get("diagnostics") instanceof Obj d?value(d,"connection_generation"):Nil.INSTANCE);
            action.put("submitted_episode_run_id",value(before,"episode_run_id"));action.put("owner_character_id",value(source,"owner_character_id"));
            action.put("original_current_province_id",value(source,"current_province_id"));
            action.put("original_move_target_province_id",value(source,"move_target_province_id"));
            action.put("original_route_province_ids",route(source));action.put("postcondition_verified",new Bool(false));
        }
        fields.put("war_action",new Obj(action));return new RawJson(DriverJson.encode(new Obj(fields)));
    }
    /** The original rejection guard runs before its route readback; a mismatch retains NativeCommandRejected. */
    public static boolean matchesHaltRefusal(Halt call,Obj before,Obj request,Obj response,String requestId) {
        Objects.requireNonNull(call);Objects.requireNonNull(before);Objects.requireNonNull(request);Objects.requireNonNull(response);
        return requestId!=null&&!requestId.isEmpty()&&new Text("execute_step").equals(request.get("type"))
                &&new Text(call.operation().value()).equals(request.get("step"))
                &&value(request,"expected_revision").equals(value(before,"native_revision"))
                &&new Text(requestId).equals(request.get("request_id"))&&new Text(requestId).equals(response.get("request_id"))
                &&new Text("command_result").equals(response.get("type"))&&value(request,"protocol_version").equals(value(response,"protocol_version"))
                &&new Bool(false).equals(response.get("ok"))&&new Text("CK3 halt-army command validation failed").equals(response.get("error"))
                &&!(response.get("result") instanceof Obj);
    }
    private static DriverUnavailable haltReadbackUnavailable() {
        return new DriverUnavailable(DriverFailureReason.HALT_ROUTE_READBACK,
                "native halt validator rejection lacks unchanged route/owner readback");
    }
    /** Exact stock validation refusal, zero gameplay submission. No ordinary rejection may borrow it. */
    public static RawJson haltDeferred(Halt call,Obj before,Obj after,Obj request,Obj response,String requestId) {
        StrictJson.require(matchesHaltRefusal(call,before,request,response,requestId),"halt refusal lacks exact native request/result original");
        Optional<Obj> oldArmy=army(before,call.source().value()),newArmy=army(after,call.source().value());
        if(oldArmy.isEmpty()||newArmy.isEmpty()||!(before.get("diagnostics") instanceof Obj previousOwner)
                ||!(after.get("diagnostics") instanceof Obj owner)||!(before.get("played_character") instanceof Obj previousActor)
                ||!(after.get("played_character") instanceof Obj actor)
                ||!(oldArmy.orElseThrow().get("route_province_ids") instanceof Arr))throw haltReadbackUnavailable();
        Obj prior=oldArmy.orElseThrow(),current=newArmy.orElseThrow();
        Arr route=route(prior);
        if(!(truth(before,"paused")&&truth(after,"paused")&&truth(before,"map_ready")&&truth(after,"map_ready")
                &&value(before,"date_raw").equals(value(after,"date_raw"))&&truth(previousActor,"alive")&&truth(actor,"alive")
                &&value(previousActor,"character_id").equals(value(actor,"character_id"))
                &&value(prior,"owner_character_id").equals(value(current,"owner_character_id"))
                &&value(prior,"owner_character_id").equals(value(previousActor,"character_id"))
                &&truth(prior,"controllable")&&truth(current,"controllable")
                &&new Bool(false).equals(prior.get("in_combat"))&&new Bool(false).equals(current.get("in_combat"))
                &&new Bool(false).equals(prior.get("retreating"))&&new Bool(false).equals(current.get("retreating"))
                &&value(before,"episode_run_id").equals(value(after,"episode_run_id"))
                &&value(previousOwner,"bridge_pid").equals(value(owner,"bridge_pid"))
                &&value(previousOwner,"connection_generation").equals(value(owner,"connection_generation"))
                &&route.items().size()>=2&&new Text("complete_nonempty").equals(prior.get("route_read_status"))
                &&new Text("complete_nonempty").equals(current.get("route_read_status"))&&route.equals(value(current,"route_province_ids"))
                &&value(prior,"current_province_id").equals(value(current,"current_province_id"))
                &&value(prior,"move_target_province_id").equals(value(current,"move_target_province_id"))
                &&value(after,"active_event")==Nil.INSTANCE&&value(after,"pending_character_interaction")==Nil.INSTANCE
                &&!(after.get("top_exclusive_modal_choice_hint") instanceof Obj hint&&new Text("present").equals(hint.get("status")))))
            throw haltReadbackUnavailable();
        var action=new Obj(java.util.Map.of("status",new Text("halt_validator_rejected_current_route_retained"),
                "army_id",number(call.source().value()),"reason",new Text("native_halt_validator_rejected"),
                "current_province_id",value(current,"current_province_id"),"move_target_province_id",value(current,"move_target_province_id"),
                "route_province_ids",route,"contact_free_proven",new Bool(false)));
        var observed=new LinkedHashMap<String,Value>();
        for(String key:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id"))observed.put(key,value(after,key));
        observed.put("actor_character_id",value(actor,"character_id"));observed.put("bridge_pid",value(owner,"bridge_pid"));
        observed.put("connection_generation",value(owner,"connection_generation"));
        var out=new LinkedHashMap<String,Value>();out.put("schema",new Text("xar.halt-army-validator-deferred/v1"));
        out.put("step",new Text(call.operation().value()));out.put("accepted",new Bool(false));out.put("status",new Text("deferred"));
        out.put("business_submission",new Bool(false));out.put("replay_allowed",new Bool(false));out.put("backend_id",new Text("native-headless"));
        out.put("war_action",action);out.put("halt_rejection_evidence",new Obj(java.util.Map.of("native_request_id",new Text(requestId),
                "native_request",request,"native_command_result",response,"observed_frame",new Obj(observed))));
        for(String key:List.of("snapshot_id","revision","native_revision"))out.put(key,value(after,key));
        return new RawJson(DriverJson.encode(new Obj(out)));
    }
    static Value value(Obj row,String key){return row.members().getOrDefault(key,Nil.INSTANCE);}
    static boolean truth(Obj row,String key){return new Bool(true).equals(row.get(key));}
    static BigInteger nonnegative(Obj row,String key){BigInteger value=integer(value(row,key),key);StrictJson.require(value.signum()>=0,key+" must be nonnegative");return value;}
    static Arr route(Obj army) {
        Value value=value(army,"route_province_ids");if(value==Nil.INSTANCE)return new Arr(List.of());
        Arr route=new Arr(array(value,"original route"));for(Value id:route.items()){BigInteger nativeId=integer(id,"route province");StrictJson.require(nativeId.signum()>0&&nativeId.bitLength()<=31,"route province must be positive int32");}
        return route;
    }
    static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    static Arr ids(List<Integer> ids){return new Arr(ids.stream().map(id->(Value)number(id)).toList());}
}

