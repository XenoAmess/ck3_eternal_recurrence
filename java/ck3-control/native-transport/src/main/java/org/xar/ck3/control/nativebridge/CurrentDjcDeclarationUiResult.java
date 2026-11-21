package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact current UI DATA. Even a native void dispatch is never a war, payment or SAVE receipt. */
public record CurrentDjcDeclarationUiResult(CurrentDjcDeclarationUi.Action action,Status status,
        boolean effectAttempted,boolean nativeReturned,boolean cleanupKnown,
        BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        Optional<CoreFrame.Prefix> factsBefore,Optional<CurrentDjcTargetWarQueryResult.OwnerWitness> ownerWitness,
        Optional<CurrentDjcDeclarationUiSource> source,Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),
        AVAILABLE("available"),OPEN_DISPATCHED("open_dispatched"),SELECTION_DISPATCHED("selection_dispatched"),
        SEND_DISPATCHED("send_dispatched"),WARNING_PENDING("warning_pending"),WARNING_READY("warning_ready"),
        WARNING_DISPATCHED("warning_dispatched"),INDETERMINATE("indeterminate");
        private final String wire;Status(String s){wire=s;}public String wire(){return wire;}
        static Status parse(String s)throws IOException {for(var a:values())if(a.wire.equals(s))return a;throw new IOException("Unknown exact current DJC UI status");}
        boolean positive(){return this==AVAILABLE||this==OPEN_DISPATCHED||this==SELECTION_DISPATCHED||this==SEND_DISPATCHED||this==WARNING_READY||this==WARNING_DISPATCHED;}
    }
    public CurrentDjcDeclarationUiResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);u64(providerGeneration,false);u64(querySequence,false);u64(claimSequence,false);
        Objects.requireNonNull(factsBefore);Objects.requireNonNull(ownerWitness);Objects.requireNonNull(source);Objects.requireNonNull(unavailableReason);
        StrictJson.require(factsBefore.isPresent()==ownerWitness.isPresent(),"Actual Core/owner DATA must be present or null together");
        factsBefore.ifPresent(CurrentDjcTargetWarQuery::requirePrefix);
        source.ifPresent(s->{StrictJson.require(cleanupKnown&&factsBefore.isPresent(),"Actual source requires completed scratch cleanup and actual Core/owner");sourceShape(s,factsBefore.orElseThrow());});
        boolean lease=providerGeneration.signum()>0&&querySequence.signum()>0;
        boolean read=!effectAttempted&&!nativeReturned&&claimSequence.signum()==0;
        if(status.positive()) {
            StrictJson.require(source.isPresent()&&lease&&unavailableReason.isEmpty(),"Positive UI response needs actual source, private lease and null reason");
            var s=source.orElseThrow();boolean coherent=switch(status) {
                case AVAILABLE->action==CurrentDjcDeclarationUi.Action.QUERY_UI&&read;
                case WARNING_READY->action==CurrentDjcDeclarationUi.Action.QUERY_WARNING&&read&&s.warningSourceAvailable();
                case OPEN_DISPATCHED->action==CurrentDjcDeclarationUi.Action.OPEN_UI&&effectAttempted&&nativeReturned&&claimSequence.signum()>0&&s.permitsOpen();
                case SELECTION_DISPATCHED->action==CurrentDjcDeclarationUi.Action.SELECT_CHOICE&&effectAttempted&&nativeReturned&&claimSequence.signum()>0&&s.residentAvailable()&&s.namedRootBound()&&s.windowVisible()&&s.windowEnabled();
                case SEND_DISPATCHED->action==CurrentDjcDeclarationUi.Action.SEND_UI&&effectAttempted&&nativeReturned&&claimSequence.signum()>0&&s.permitsSend();
                case WARNING_DISPATCHED->action==CurrentDjcDeclarationUi.Action.ACCEPT_WARNING&&effectAttempted&&nativeReturned&&claimSequence.signum()>0&&s.permitsAccept();
                default->false;
            };StrictJson.require(coherent,"Fixed action/status/native before-source coherence differs");
        } else {
            StrictJson.require(unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Negative response must preserve its actual nonempty reason");
            if(status==Status.WARNING_PENDING)StrictJson.require(action==CurrentDjcDeclarationUi.Action.QUERY_WARNING&&source.isPresent()&&lease&&read&&!source.orElseThrow().warningSourceAvailable(),"Pending is only a readonly observation under an original private Send lease");
        }
    }
    public boolean nativeOk(){return status.positive();}
    private static void sourceShape(CurrentDjcDeclarationUiSource s,CoreFrame.Prefix p) {
        StrictJson.require(s.target().value()!=p.playedCharacterId()&&s.interactionDefinitionVerified()&&s.nativeConfirmation().isPresent()&&s.nativeIsValid().isPresent()
                &&s.actor().filter(a->a.value()==p.playedCharacterId()).isPresent()&&s.recipient().filter(a->a.equals(s.target())).isPresent(),"Actual target/CB definition/interaction actor tuple required");
        StrictJson.require(!s.openAdmissible()||(s.loadedInterface()==4&&s.nativeConfirmation().orElse(false)&&s.nativeIsValid().orElse(false)&&!s.windowVisible()&&!s.warningSourceAvailable()),"Open requires its actual confirmation/interface/IsValid before-source");
        StrictJson.require(!s.namedRootBound()||s.residentAvailable(),"Named root requires actual resident interface");
        StrictJson.require((!s.windowVisible()&&!s.windowEnabled())||s.residentAvailable()&&s.namedRootBound(),"Observed visible/enabled window requires actual typed resident root");
        StrictJson.require(s.selected().isEmpty()||s.residentAvailable(),"Selected native tuple requires actual resident interface");
        StrictJson.require(s.nativeCanSend().isEmpty()||s.residentAvailable()&&s.namedRootBound()&&s.selected().isPresent(),"Native CanSend is nullable unless actual selected resident source exists");
        StrictJson.require(!s.sendAdmissible()||(s.permitsSend()&&!s.warningSourceAvailable()),"Send admissible differs from actual selected native CanSend source");
        StrictJson.require(s.nativeCanAccept().isPresent()==s.warningSourceAvailable(),"Accept predicate must be actually observed exactly with warning source");
        StrictJson.require(!s.acceptAdmissible()||(s.nativeCanAccept().orElse(false)&&s.warningSourceAvailable()&&s.selected().filter(t->t.casusBelli()==s.casusBelli()).isPresent()),"Warning acceptance must bind its actual selected fixed CB");
        var tokens=new HashSet<BigInteger>();StrictJson.require(s.choices().size()<=10000,"Bounded actual native choices required");
        for(var c:s.choices())StrictJson.require(s.residentAvailable()&&c.nativeToken().signum()>0&&tokens.add(c.nativeToken())&&c.tuple().casusBelli()==s.casusBelli(),"Actual choice lease must be positive, unique and from this same CB source");
    }
    public static CurrentDjcDeclarationUiResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","adapter_id","backend","step","action","status","source_available","effect_attempted","native_returned","native_handled","cleanup_known","provider_generation","query_sequence","claim_sequence","facts_before","owner_witness","source","addresses_redacted","submitted","war_created","payment_confirmed","physical_save_confirmed","war_id","total_debit","unavailable_reason"));
            var b=ExactCk3Build.CK3_121003_STEAM_26785313;eq(r,"schema",CurrentDjcDeclarationUi.RESULT_SCHEMA);eq(r,"game_version",b.version());eq(r,"executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT));eq(r,"adapter_id",b.coreFrameAdapterId());eq(r,"backend",CurrentDjcDeclarationUi.BACKEND);
            var action=CurrentDjcDeclarationUi.Action.parse(NativeWire.text(r.get("action")));eq(r,"step",action.step());
            if(bool(r,"native_handled")||!bool(r,"addresses_redacted")||bool(r,"submitted")||bool(r,"war_created")||bool(r,"payment_confirmed")||bool(r,"physical_save_confirmed")||!r.get("war_id").isNull()||!r.get("total_debit").isNull())throw new IOException("A void UI dispatch cannot grant handled/war/payment/SAVE knowledge");
            Optional<CoreFrame.Prefix> facts=Optional.empty();Optional<CurrentDjcTargetWarQueryResult.OwnerWitness> owner=Optional.empty();Optional<CurrentDjcDeclarationUiSource> source=Optional.empty();
            if(!r.get("facts_before").isNull()){var c=StrictJson.object(r.get("facts_before"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));facts=Optional.of(new CoreFrame.Prefix(i32(c.get("date_raw")),i32(c.get("speed")),bool(c,"paused"),i32(c.get("local_player_id")),bool(c,"map_ready"),bool(c,"has_played_character"),i32(c.get("played_character_id")),bool(c,"played_character_alive")));}
            if(!r.get("owner_witness").isNull()){var w=StrictJson.object(r.get("owner_witness"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new CurrentDjcTargetWarQueryResult.OwnerWitness(decimal(w,"connection_generation",true),decimal(w,"ticket_sequence",true),decimal(w,"pump_epoch",true),NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
            if(!r.get("source").isNull())source=Optional.of(source(r.get("source")));
            if(bool(r,"source_available")!=source.isPresent())throw new IOException("Actual source_available/null role differs");
            return new CurrentDjcDeclarationUiResult(action,Status.parse(NativeWire.text(r.get("status"))),bool(r,"effect_attempted"),bool(r,"native_returned"),bool(r,"cleanup_known"),decimal(r,"provider_generation",false),decimal(r,"query_sequence",false),decimal(r,"claim_sequence",false),facts,owner,source,optionalText(r.get("unavailable_reason")));
        }catch(IllegalArgumentException|ArithmeticException bad){throw new IOException("Invalid exact current DJC declaration UI DATA",bad);}
    }
    public static CurrentDjcDeclarationUiResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));eq(e,"type","command_result");eq(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(bool(e,"ok")!=original.nativeOk())throw new IOException("Actual UI envelope ok differs from original custody");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original current UI result token required"));if(!NativeWire.parse(token.bytes()).equals(e.get("result")))throw new IOException("Current UI original result token differs from its raw envelope");
            var r=decode(new RawJson(token.bytes()));if(r.nativeOk()!=original.nativeOk())throw new IOException("Actual current UI envelope/status coherence differs");return r;
        }catch(IllegalArgumentException bad){throw new IOException("Invalid original current DJC UI envelope",bad);}
    }
    private static CurrentDjcDeclarationUiSource source(JsonNode raw)throws IOException {
        var s=StrictJson.object(raw,Set.of("schema","target_character_id","cb_key","interaction_definition_verified","loaded_interface","native_confirmation","native_is_valid","open_admissible","resident_available","named_root_bound","window_visible","window_enabled","actor_id","recipient_id","additional_role_id","selected","choices","native_can_send","send_admissible","warning_source_available","native_can_accept","accept_admissible"));eq(s,"schema",CurrentDjcDeclarationUi.SOURCE_SCHEMA);
        var target=new NativeCharacterId(i32(s.get("target_character_id")));var cb=CurrentDjcTargetWarQueryResult.CasusBelliKey.parse(NativeWire.text(s.get("cb_key")));
        Optional<CurrentDjcDeclarationUiSource.SelectedTuple> selected=s.get("selected").isNull()?Optional.empty():Optional.of(tuple(s.get("selected"),false));
        if(!s.get("choices").isArray()||s.get("choices").size()>10000)throw new IOException("Bounded actual ordered choices required");var choices=new ArrayList<CurrentDjcDeclarationUiSource.Choice>();
        for(var row:s.get("choices")){var q=StrictJson.object(row,Set.of("choice_token","cb_key","claimant_character_id","target_title_ids","extra_configuration_ids","native_enabled"));choices.add(new CurrentDjcDeclarationUiSource.Choice(decimal(q,"choice_token",true),tuple(q,true)));}
        return new CurrentDjcDeclarationUiSource(target,cb,bool(s,"interaction_definition_verified"),i32(s.get("loaded_interface")),optionalBool(s,"native_confirmation"),optionalBool(s,"native_is_valid"),bool(s,"open_admissible"),bool(s,"resident_available"),bool(s,"named_root_bound"),bool(s,"window_visible"),bool(s,"window_enabled"),character(i32(s.get("actor_id"))),character(i32(s.get("recipient_id"))),character(i32(s.get("additional_role_id"))),selected,choices,optionalBool(s,"native_can_send"),bool(s,"send_admissible"),bool(s,"warning_source_available"),optionalBool(s,"native_can_accept"),bool(s,"accept_admissible"));
    }
    private static CurrentDjcDeclarationUiSource.SelectedTuple tuple(JsonNode raw,boolean choice)throws IOException {
        var t=StrictJson.object(raw,choice?Set.of("choice_token","cb_key","claimant_character_id","target_title_ids","extra_configuration_ids","native_enabled"):Set.of("cb_key","claimant_character_id","target_title_ids","extra_configuration_ids","source_row_enabled"));
        return new CurrentDjcDeclarationUiSource.SelectedTuple(CurrentDjcTargetWarQueryResult.CasusBelliKey.parse(NativeWire.text(t.get("cb_key"))),character(i32(t.get("claimant_character_id"))),ids(t.get("target_title_ids")),ids(t.get("extra_configuration_ids")),bool(t,choice?"native_enabled":"source_row_enabled"));
    }
    private static Optional<Boolean> optionalBool(ObjectNode r,String k)throws IOException{return r.get(k).isNull()?Optional.empty():Optional.of(bool(r,k));}
    private static Optional<String> optionalText(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(NativeWire.text(n));}
    private static Optional<NativeCharacterId> character(int n){return n==-1?Optional.empty():Optional.of(new NativeCharacterId(n));}
    private static List<Integer> ids(JsonNode n)throws IOException {if(!n.isArray()||n.size()>10000)throw new IOException("Bounded ordered signed native vector required");var out=new ArrayList<Integer>();for(var x:n)out.add(i32(x));return List.copyOf(out);}
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static void u64(BigInteger n,boolean positive){Objects.requireNonNull(n);StrictJson.require(n.signum()>=0&&(!positive||n.signum()>0)&&n.compareTo(NativeWire.UINT64_MAX)<=0,"Exact unsigned64 DATA required");}
    private static BigInteger decimal(ObjectNode r,String k,boolean positive)throws IOException {String s=NativeWire.text(r.get(k));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical unsigned64 string required: "+k);BigInteger n=new BigInteger(s);try{u64(n,positive);}catch(IllegalArgumentException bad){throw new IOException("Unsigned64 range mismatch",bad);}return n;}
    private static boolean bool(ObjectNode r,String k)throws IOException {var n=r.get(k);if(n==null||!n.isBoolean())throw new IOException("Actual bool required: "+k);return n.booleanValue();}
    private static void eq(ObjectNode r,String k,String expected)throws IOException {if(!NativeWire.text(r.get(k)).equals(expected))throw new IOException("Exact current UI identity mismatch: "+k);}
}
