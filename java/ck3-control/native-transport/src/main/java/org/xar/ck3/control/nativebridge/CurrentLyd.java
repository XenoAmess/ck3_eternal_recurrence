package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Finite LYD DATA only. Core custody, native leases, deadlines, modal association and once belong to Transport. */
public final class CurrentLyd {
    public static final String SCHEMA="ck3.lyd.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.lyd.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.lyd.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-lyd";
    public enum Kind {
        DECISIONS("decisions"),EVENTS("events"),PERSONAL("personal"),READBACK("readback");
        private final String wire;Kind(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Kind parse(String value)throws IOException{for(var k:values())if(k.wire.equals(value))return k;throw new IOException("Unknown LYD Source kind");}
    }
    public enum Action {
        QUERY_DECISIONS("query_decisions","query-lyd-decisions-current-v1","game.query.current-lyd-decisions.v1",Kind.DECISIONS,true),
        OPEN_LIST("open_list","open-lyd-decisions-current-v1","game.command.open-current-lyd-decisions.v1",Kind.DECISIONS,false),
        OPEN_DETAIL("open_detail","open-lyd-decision-current-v1","game.command.open-current-lyd-decision.v1",Kind.DECISIONS,false),
        CONFIRM_DECISION("confirm_decision","confirm-lyd-decision-current-v1","game.command.confirm-current-lyd-decision.v1",Kind.DECISIONS,false),
        QUERY_EVENTS("query_events","query-lyd-events-current-v1","game.query.current-lyd-events.v1",Kind.EVENTS,true),
        CHOOSE_KNOWN_EVENT_OPTION("choose_known_event_option","select-lyd-known-event-option-current-v1","game.command.select-current-lyd-event-option.v1",Kind.EVENTS,false),
        QUERY_PERSONAL("query_personal","query-lyd-personal-current-v1","game.query.current-lyd-personal.v1",Kind.PERSONAL,true),
        OPEN_PERSONAL("open_personal","open-lyd-personal-current-v1","game.command.open-current-lyd-personal.v1",Kind.PERSONAL,false),
        START_ADD_PERSONAL("start_add_personal","start-add-lyd-personal-current-v1","game.command.start-add-current-lyd-personal.v1",Kind.PERSONAL,false),
        SELECT_PERSONAL_CANDIDATE("select_personal_candidate","select-lyd-personal-candidate-current-v1","game.command.select-current-lyd-personal-candidate.v1",Kind.PERSONAL,false),
        QUERY_ADD_CONFIRMATION("query_add_confirmation","query-lyd-add-confirmation-current-v1","game.query.current-lyd-add-confirmation.v1",Kind.PERSONAL,true),
        CONFIRM_PERSONAL_ADD("confirm_personal_add","confirm-lyd-personal-add-current-v1","game.command.confirm-current-lyd-personal-add.v1",Kind.PERSONAL,false),
        QUERY_READBACK("query_readback","query-lyd-readback-current-v1","game.query.current-lyd-readback.v1",Kind.READBACK,true);
        private final String wire,step,capability;private final Kind kind;private final boolean query;
        Action(String wire,String step,String capability,Kind kind,boolean query){this.wire=wire;this.step=step;this.capability=capability;this.kind=kind;this.query=query;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}public Kind kind(){return kind;}public boolean isQuery(){return query;}
        public static Action parse(String value)throws IOException{for(var a:values())if(a.wire.equals(value))return a;throw new IOException("Unknown LYD action");}
    }
    public enum DecisionKey {
        ENTRY("lyd_enter_decision"),RITUAL_MUSIC("lyd_play_ritual_music_decision"),REVERENT_HEAVEN("lyd_play_reverent_heaven_decision"),
        KNOWING_ACTING_SUPPORT("lyd_play_knowing_acting_support_decision"),BEGIN_READONLY("lyd_i3b_begin_decision");
        private final String wire;DecisionKey(String wire){this.wire=wire;}public String wire(){return wire;}
        public static DecisionKey parse(String value)throws IOException{for(var d:values())if(d.wire.equals(value))return d;throw new IOException("Unknown fixed LYD decision");}
    }
    public enum PersonalKey {
        REVERENT_HEAVEN("lyd_tenet_reverent_heaven"),KNOWING_ACTING_SUPPORT("lyd_tenet_knowing_acting_support");
        private final String wire;PersonalKey(String wire){this.wire=wire;}public String wire(){return wire;}
        public static PersonalKey parse(String value)throws IOException{for(var p:values())if(p.wire.equals(value))return p;throw new IOException("Unknown fixed LYD personal key");}
        static boolean contains(String value){for(var p:values())if(p.wire.equals(value))return true;return false;}
    }
    public enum EventRole {
        WELCOME_CONTINUE("welcome_continue","lyd.1","lyd_welcome_continue",1,0),
        RITUAL_MUSIC_PAY("ritual_music_pay","lyd.1002","lyd_play_ritual_music_option_0",2,0),
        RITUAL_MUSIC_CANCEL("ritual_music_cancel","lyd.1002","lyd_play_cancel",2,1),
        REVERENT_HEAVEN_PAY("reverent_heaven_pay","lyd.1000","lyd_play_reverent_heaven_option_0",2,0),
        REVERENT_HEAVEN_CANCEL("reverent_heaven_cancel","lyd.1000","lyd_play_cancel",2,1),
        KNOWING_ACTING_INQUIRY("knowing_acting_inquiry","lyd.1032","lyd_play_knowing_acting_support_option_0",3,0),
        KNOWING_ACTING_CANCEL("knowing_acting_cancel","lyd.1032","lyd_play_cancel",3,2);
        private final String wire,definitionKey,optionKey;private final int authoredCount,authoredIndex;
        EventRole(String wire,String definitionKey,String optionKey,int authoredCount,int authoredIndex){this.wire=wire;this.definitionKey=definitionKey;this.optionKey=optionKey;this.authoredCount=authoredCount;this.authoredIndex=authoredIndex;}
        public String wire(){return wire;}
        public boolean matches(String definition,int count,int index,String option){return definitionKey.equals(definition)&&authoredCount==count&&authoredIndex==index&&optionKey.equals(option);}
        public static EventRole parse(String value)throws IOException{for(var r:values())if(r.wire.equals(value))return r;throw new IOException("Unknown fixed LYD event role; practice is not permitted");}
    }
    public record Target(Optional<DecisionKey> decisionKey,Optional<PersonalKey> personalKey,Optional<EventRole> eventRole,
            Optional<Integer> instanceId,String choiceToken) {
        public Target {Objects.requireNonNull(decisionKey);Objects.requireNonNull(personalKey);Objects.requireNonNull(eventRole);Objects.requireNonNull(instanceId);Objects.requireNonNull(choiceToken);
            instanceId.ifPresent(id->StrictJson.require(id>0,"Actual positive instance required"));if(!choiceToken.isEmpty())key(choiceToken,96);}
        public static Target none(){return new Target(Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),"");}
        public static Target decision(DecisionKey key){return new Target(Optional.of(key),Optional.empty(),Optional.empty(),Optional.empty(),"");}
        public static Target personal(PersonalKey key){return new Target(Optional.empty(),Optional.of(key),Optional.empty(),Optional.empty(),"");}
        public static Target candidate(PersonalKey key,String token){return new Target(Optional.empty(),Optional.of(key),Optional.empty(),Optional.empty(),token);}
        public static Target event(EventRole role,int instance){return new Target(Optional.empty(),Optional.empty(),Optional.of(role),Optional.of(instance),"");}
    }
    private CurrentLyd() { }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query,Target target){
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(target);
        CurrentLetter.unsigned(provider,false);CurrentLetter.unsigned(query,false);CurrentLetter.requirePrefix(actual.prefix());
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313
                ||actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313_FULL111&&action==Action.QUERY_EVENTS,
                "Exact current267 Core or Full111 ordinary-event read required");
        requireTarget(action,target,true);
        StrictJson.require(action.isQuery()?provider.signum()==0&&query.signum()==0:provider.signum()>0&&query.signum()>0,"Actual query/action lease roles differ");
        var b=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256())
                .put("adapter_id",b.coreFrameAdapterId()).put("backend",BACKEND).put("action",action.wire()).put("provider_generation",provider.toString()).put("query_sequence",query.toString());
        claim.set("expected_core",core(actual.prefix()));
        putText(claim,"decision_key",target.decisionKey().map(DecisionKey::wire));putText(claim,"personal_key",target.personalKey().map(PersonalKey::wire));
        putText(claim,"event_role",target.eventRole().map(EventRole::wire));putInteger(claim,"instance_id",target.instanceId());claim.put("choice_token",target.choiceToken());
        var fields=StrictJson.object();fields.set("arguments",StrictJson.object());fields.set("lyd",claim);
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
    static void requireTarget(Action action,Target t,boolean request){
        Objects.requireNonNull(action);Objects.requireNonNull(t);
        if(action.kind()==Kind.DECISIONS)StrictJson.require(t.personalKey().isEmpty()&&t.eventRole().isEmpty()&&t.instanceId().isEmpty()&&t.choiceToken().isEmpty()
                &&((action==Action.QUERY_DECISIONS||action==Action.OPEN_LIST)?t.decisionKey().isEmpty():t.decisionKey().isPresent())
                &&!(action==Action.CONFIRM_DECISION&&t.decisionKey().filter(d->d==DecisionKey.BEGIN_READONLY).isPresent()),"Fixed decision target shape differs; begin is inspect-only");
        else if(action.kind()==Kind.EVENTS)StrictJson.require(t.decisionKey().isEmpty()&&t.personalKey().isEmpty()&&t.choiceToken().isEmpty()
                &&(action==Action.QUERY_EVENTS?t.eventRole().isEmpty()&&t.instanceId().isEmpty():t.eventRole().isPresent()&&t.instanceId().isPresent()),"Fixed event target shape differs");
        else if(action.kind()==Kind.PERSONAL)StrictJson.require(t.decisionKey().isEmpty()&&t.eventRole().isEmpty()&&t.instanceId().isEmpty()&&t.personalKey().isPresent()
                &&(action==Action.SELECT_PERSONAL_CANDIDATE&&request?!t.choiceToken().isEmpty():t.choiceToken().isEmpty()),"Fixed personal target/token shape differs");
        else StrictJson.require(t.decisionKey().isEmpty()&&t.personalKey().isEmpty()&&t.eventRole().isEmpty()&&t.instanceId().isEmpty()&&t.choiceToken().isEmpty(),"Readback has no target");
    }
    static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    static boolean bool(ObjectNode r,String k)throws IOException{var n=r.get(k);if(n==null||!n.isBoolean())throw new IOException("Actual LYD bool required: "+k);return n.booleanValue();}
    static Optional<Integer> integer(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(i32(n));}
    static Optional<Boolean> boolOptional(ObjectNode r,String k)throws IOException{return r.get(k).isNull()?Optional.empty():Optional.of(bool(r,k));}
    static BigInteger decimal(ObjectNode r,String k)throws IOException{String s=NativeWire.text(r.get(k));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical uint64 string required");var n=new BigInteger(s);CurrentLetter.unsigned(n,false);return n;}
    static long rawLong(JsonNode n)throws IOException{String s=NativeWire.text(n);if(!s.matches("0|-?[1-9][0-9]{0,18}"))throw new IOException("Canonical signed64 string required");try{return Long.parseLong(s);}catch(NumberFormatException bad){throw new IOException("LYD raw value outside signed64",bad);}}
    static Optional<Long> rawOptional(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(rawLong(n));}
    static String nativeText(JsonNode n)throws IOException{if(!n.isTextual())throw new IOException("Native LYD string required");String s=n.textValue();text(s);return s;}
    static Optional<String> nativeTextOptional(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(nativeText(n));}
    static void text(String s){Objects.requireNonNull(s);StrictJson.require(s.getBytes(StandardCharsets.UTF_8).length<=16384,"Native UTF8 text bound exceeded");}
    static void key(String s,int bound){Objects.requireNonNull(s);StrictJson.require(s.length()>=1&&s.length()<=bound&&s.matches("[A-Za-z0-9_.-]+"),"Exact bounded ASCII key required");}
    static CoreFrame.Prefix readCore(JsonNode node)throws IOException{var p=StrictJson.object(node,Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));var result=new CoreFrame.Prefix(i32(p.get("date_raw")),i32(p.get("speed")),bool(p,"paused"),i32(p.get("local_player_id")),bool(p,"map_ready"),bool(p,"has_played_character"),i32(p.get("played_character_id")),bool(p,"played_character_alive"));CurrentLetter.requirePrefix(result);return result;}
    static ObjectNode core(CoreFrame.Prefix p){CurrentLetter.requirePrefix(p);return StrictJson.object().put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());}
    static void putText(ObjectNode r,String k,Optional<String> value){if(value.isPresent())r.put(k,value.orElseThrow());else r.putNull(k);}
    static void putInteger(ObjectNode r,String k,Optional<Integer> value){if(value.isPresent())r.put(k,value.orElseThrow().intValue());else r.putNull(k);}
}
