package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** The one typed pending/material/result boundary shared by the three result and alliance routes. */
public final class FamilyMarriageResults {
    private FamilyMarriageResults() { }
    public enum Route {
        FAMILY("xar.ck3.observed-first-heir-marriage-private-action.v1","query-observed-first-heir-marriage-result-v1-private","source_qualified_observed_first_heir_marriage_result_v1"),
        MATRILINEAL("xar.ck3.player-child-matrilineal-private-action.v1","query-player-child-matrilineal-marriage-result-v1-private","allow_private_player_child_matrilineal_action"),
        DEFAULT("xar.ck3.player-child-default-private-action.v1","query-player-child-default-marriage-result-v1-private","allow_private_player_child_default_action");
        private final String schema,step,permission;
        Route(String schema,String step,String permission){this.schema=schema;this.step=step;this.permission=permission;}
        public String schema(){return schema;} public String step(){return step;} public String permission(){return permission;}
    }
    public enum Status {
        PENDING, ACCEPTED_PENDING, REFUSED, INVALIDATED, MARRIAGE, BETROTHAL, GONE_UNMATERIALIZED;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}
        public boolean material(){return this==MARRIAGE||this==BETROTHAL;}
    }
    public enum Relationship { MARRIAGE, BETROTHAL }
    public enum OutboundState { ACTIVE,ABSENT,AMBIGUOUS,UNAVAILABLE,NOT_APPLICABLE }
    public enum Presence { MISSING,NULL,PRESENT }
    /** Missing, explicit null, and an actual typed value remain different through every public round trip. */
    public record Field<T>(Presence presence,T value) {
        public Field { Objects.requireNonNull(presence); need((presence==Presence.PRESENT)==(value!=null),"optional field presence/value mismatch"); }
    }
    /** Original is immutable application JSON, retained for exact durable-body equality and lossless extension fields. */
    public record Pending(Route route,BigInteger playedCharacterId,BigInteger subjectCharacterId,
            BigInteger candidateCharacterId,BigInteger recipientCharacterId,BigInteger preNativeRevision,
            BigInteger sourceDateRaw,boolean matrilinealOptionSelected,boolean fulfillExistingBetrothal,Obj original) {
        public Pending { Objects.requireNonNull(route); Objects.requireNonNull(subjectCharacterId); Objects.requireNonNull(candidateCharacterId);
            Objects.requireNonNull(preNativeRevision); Objects.requireNonNull(original); }
    }
    public record Resolved(Route route,Pending pending,Relationship relationship,Obj original) {
        public Resolved { Objects.requireNonNull(route);Objects.requireNonNull(pending);Objects.requireNonNull(relationship);Objects.requireNonNull(original);need(route==pending.route(),"resolved route differs from source pending"); }
    }
    public record Outbound(OutboundState state,Field<BigInteger> id,Field<BigInteger> ageDays,Field<BigInteger> cutoffDays) {
        public Outbound {Objects.requireNonNull(state);Objects.requireNonNull(id);Objects.requireNonNull(ageDays);Objects.requireNonNull(cutoffDays);}
    }
    public record TerminalDisposition(String source,boolean terminalCauseAvailable,String terminalCause) { }
    public record RetainedEvents(boolean available,boolean readComplete,boolean stable,BigInteger count,
            BigInteger matchedOriginalRoles,String kind,String unavailableReason) { }
    public record Observation(Route route,Pending pending,boolean cold,Status status,boolean materialResult,
            BigInteger preNativeRevision,BigInteger postNativeRevision,BigInteger subjectCharacterId,
            BigInteger candidateCharacterId,Field<BigInteger> recipientCharacterId,Field<Boolean> matrilinealOption,
            Field<Boolean> fulfillment,Field<Outbound> outbound,Field<TerminalDisposition> disposition,
            Field<RetainedEvents> retainedEvents,Obj original) {
        public Observation {Objects.requireNonNull(route);Objects.requireNonNull(pending);Objects.requireNonNull(status);
            Objects.requireNonNull(original);need(route==pending.route(),"observation route differs from pending");}
    }
    public static Pending decodePending(Route route,Obj original) {
        Objects.requireNonNull(route);Objects.requireNonNull(original);JsonNode n=OpportunityJson.toNode(original);
        eq(n,"schema",route.schema());eq(n,"status","receipt_pending");
        optionalConstant(n,"schema_version",BigInteger.ONE);
        BigInteger actor=optionalInteger(n,"played_character_id",BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));
        BigInteger subject=character(n,"heir_character_id"),candidate=character(n,"candidate_character_id");
        BigInteger recipient=optionalInteger(n,"recipient_character_id",BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));
        BigInteger pre=positive64(n,"pre_native_revision"),date=optionalInteger(n,"source_date_raw",route==Route.FAMILY?BigInteger.ZERO:I64_MIN,I64_MAX);
        need(!subject.equals(candidate),"durable proposal subject/candidate must differ");
        boolean lineality=n.has("matrilineal_option_selected")?bool(n,"matrilineal_option_selected"):false;
        boolean fulfillment=n.has("fulfill_existing_betrothal")?bool(n,"fulfill_existing_betrothal"):false;
        if(route!=Route.FAMILY) {
            need(actor!=null&&recipient!=null,"child pending requires original actor/recipient");
            need(n.has("matrilineal_option_selected")&&lineality==(route==Route.MATRILINEAL),"child pending route/lineality differs");
            need(!fulfillment,"child proposal is not first-heir betrothal fulfillment");
        }
        if(n.has("material_result")) no(n,"material_result");
        if(n.has("advertised")) no(n,"advertised");
        for(String key:List.of("source_bridge_pid","last_checked_bridge_pid","last_checked_native_revision","last_consumed_checkpoint_native_revision"))
            if(n.has(key))number(n,key,BigInteger.ONE,U64);
        for(String key:List.of("prior_rejected_candidate_ids","prior_attempted_candidate_ids"))
            if(n.has(key)){List<BigInteger> ids=list(n,key,65536,v->{need(v.isIntegralNumber(),"candidate history must contain integers");return range(v.bigIntegerValue(),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));});unique(ids,65536);}
        return new Pending(route,actor,subject,candidate,recipient,pre,date,lineality,fulfillment,original);
    }
    /** Material views are shared with alliance reads; rejected or merely pending states never become a material pair. */
    public static Resolved decodeResolved(Route route,Obj original) {
        Objects.requireNonNull(original);JsonNode n=OpportunityJson.toNode(original);
        String status=text(n,"status");need(status.equals("marriage")||status.equals("betrothal"),"resolved alliance input is not material");
        yes(n,"material_result");Obj source=InteractionArguments.app(object(field(n,"source_pending")));
        Pending pending=decodePending(route,source);
        for(String key:List.of("heir_character_id","candidate_character_id"))
            if(n.has(key))eq(n,key,key.equals("heir_character_id")?pending.subjectCharacterId():pending.candidateCharacterId());
        if(n.has("played_character_id"))eq(n,"played_character_id",Objects.requireNonNull(pending.playedCharacterId()));
        if(n.has("recipient_character_id"))eq(n,"recipient_character_id",Objects.requireNonNull(pending.recipientCharacterId()));
        if(n.has("matrilineal_option_selected"))need(bool(n,"matrilineal_option_selected")==pending.matrilinealOptionSelected(),"resolved lineality differs from original pending");
        if(pending.fulfillExistingBetrothal())need(status.equals("marriage"),"fulfillment cannot resolve to the earlier betrothal");
        if(route!=Route.FAMILY){eq(n,"schema",route.schema());need(bool(n,"matrilineal_option_selected")==(route==Route.MATRILINEAL),"resolved child route differs");}
        if(n.has("post_native_revision"))positive64(n,"post_native_revision");
        return new Resolved(route,pending,status.equals("marriage")?Relationship.MARRIAGE:Relationship.BETROTHAL,original);
    }
    public static Obj verifyPending(Pending pending) {
        Objects.requireNonNull(pending);need(decodePending(pending.route(),pending.original()).equals(pending),"typed pending differs from exact original durable body");return pending.original();
    }
    public static Obj verifyResolved(Resolved resolved) {
        Objects.requireNonNull(resolved);need(decodeResolved(resolved.route(),resolved.original()).equals(resolved),"typed resolved pair differs from exact original durable body");return resolved.original();
    }
    /** Original paused/native prerequisites, distinct from Root's current ledger/source/read-proof admission. */
    public static void requireFrame(Context c,Pending pending,boolean cold) {
        Objects.requireNonNull(c);verifyPending(pending);
        need(c.controls().paused()&&c.controls().mapReady()&&c.controls().alive(),"result requires paused living map");
        need(c.actor().signum()>0&&c.revision().signum()>0,"result requires actual actor/native revision");
        if(cold||pending.route()!=Route.FAMILY)need(c.actor().equals(pending.playedCharacterId()),"result actor differs from durable pending");
        if(!cold)need(c.revision().compareTo(pending.preNativeRevision())>0,"warm result needs a strictly later native frame");
        if(cold) {
            need(pending.sourceDateRaw()!=null&&c.date().compareTo(pending.sourceDateRaw())>=0,"cold result lacks original date binding");
            need(pending.recipientCharacterId()!=null,"cold result lacks durable recipient");
            if(pending.fulfillExistingBetrothal())need(pending.original().get("matrilineal_option_selected") instanceof OpportunityJson.Bool,"cold fulfillment lacks observed native lineality");
        }
        if(pending.route()==Route.FAMILY&&!cold)no(OpportunityJson.toNode(pending.original()),"material_result");
    }
    public static Observation decode(RawJson raw,Context context,Pending pending,boolean cold) {
        requireFrame(context,pending,cold);JsonNode n=parse(raw);Route route=pending.route();
        eq(n,"step",route.step());yes(n,"accepted");yes(n,"private_build");no(n,"advertised");
        Status status=enumeration(n,"status",Status.class);need(text(n,"status").equals(status.wire()),"native result status must use its exact lowercase literal");
        boolean fulfill=pending.fulfillExistingBetrothal();
        if(route==Route.FAMILY) {
            need(status!=Status.GONE_UNMATERIALIZED&&(!fulfill||status!=Status.BETROTHAL),"invalid first-heir material status");
            if(cold)need(status==Status.PENDING||status==Status.MARRIAGE||!fulfill&&status==Status.BETROTHAL,"cold first-heir result cannot infer refusal");
        } else if(cold)need(status!=Status.ACCEPTED_PENDING&&status!=Status.REFUSED&&status!=Status.INVALIDATED,"cold child result cannot infer refusal");
        boolean material=bool(n,"material_result");need(material==status.material(),"status/material_result differ");
        need(bool(n,"cold_recovery")==cold,"result changed cold recovery mode");
        BigInteger pre=number(n,"pre_native_revision",BigInteger.ZERO,U64),post=positive64(n,"post_native_revision");
        need(pre.equals(cold?BigInteger.ZERO:pending.preNativeRevision())&&post.equals(context.revision()),"result native revision differs from original frame");
        BigInteger subject=character(n,"heir_character_id"),candidate=character(n,"candidate_character_id");
        need(subject.equals(pending.subjectCharacterId())&&candidate.equals(pending.candidateCharacterId()),"result crossed durable proposal pair");
        Field<BigInteger> recipient=integerField(n,"recipient_character_id",BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));
        Field<Boolean> lineality=booleanField(n,"matrilineal_option_selected"),fulfillment=booleanField(n,"fulfill_existing_betrothal");
        if(route!=Route.FAMILY) {
            need(recipient.presence()==Presence.PRESENT&&recipient.value().equals(pending.recipientCharacterId()),"child result recipient differs");
            need(lineality.presence()==Presence.PRESENT&&lineality.value()==(route==Route.MATRILINEAL),"child result lineality differs");
        }
        if(fulfill)need(fulfillment.presence()==Presence.PRESENT&&fulfillment.value(),"fulfillment result lost observed fulfillment");
        Field<Outbound> outbound=outbound(n);
        if(cold) {
            need(outbound.presence()==Presence.PRESENT,"cold result lacks outbound state");
            Outbound o=outbound.value();boolean pendingStatus=status==Status.PENDING||status==Status.GONE_UNMATERIALIZED;
            need(pendingStatus?o.state()!=OutboundState.NOT_APPLICABLE:o.state()==OutboundState.NOT_APPLICABLE,"cold result outbound state differs");
            if(o.state()==OutboundState.ACTIVE) {
                need(o.id().presence()==Presence.PRESENT&&o.ageDays().presence()==Presence.PRESENT&&o.cutoffDays().presence()==Presence.PRESENT,"active outbound lacks exact integer receipt");
                if(route==Route.FAMILY)need(!o.id().value().equals(BigInteger.valueOf(-1))&&o.ageDays().value().signum()>=0&&o.cutoffDays().value().signum()>=0,"first-heir active outbound receipt malformed");
            } else if(route==Route.FAMILY)need(o.id().presence()!=Presence.PRESENT&&o.ageDays().presence()!=Presence.PRESENT&&o.cutoffDays().presence()!=Presence.PRESENT,"inactive first-heir outbound invented active receipt");
        }
        Field<TerminalDisposition> disposition=disposition(n);
        if(status==Status.GONE_UNMATERIALIZED)need(route==Route.DEFAULT&&cold&&outbound.value().state()==OutboundState.ABSENT&&disposition.presence()==Presence.PRESENT
                &&disposition.value().source().equals("native_outbound_and_bilateral_pair")&&!disposition.value().terminalCauseAvailable()
                &&disposition.value().terminalCause().equals("not_observed"),"gone_unmaterialized lacks actual native disposition");
        Field<RetainedEvents> retained=retained(n);
        optionalConstant(n,"schema",route.schema());optionalConstant(n,"schema_version",BigInteger.ONE);
        optionalConstant(n,"exact_ck3_build",context.build().version());
        if(n.has("exe_sha256"))need(text(n,"exe_sha256").equalsIgnoreCase(context.build().sha256()),"result source SHA differs");
        if(n.has("cold_absent_relation_unresolved"))need(bool(n,"cold_absent_relation_unresolved")==(cold&&status==Status.PENDING),"result unresolved cold marker differs");
        return new Observation(route,pending,cold,status,material,pre,post,subject,candidate,recipient,lineality,fulfillment,outbound,disposition,retained,InteractionArguments.app(object(n)));
    }
    /** Same merge order as the unchanged Python producer, retaining all original diagnostic fields. */
    public static Obj project(Observation value,Context context) {
        verify(value,context);ObjectNode out=F.objectNode().put("schema",value.route().schema()).put("schema_version",1).put("exact_ck3_build",context.build().version());
        if(context.build()!=Build.WANDERER6)out.put("exe_sha256",context.build().sha256());
        out.put("advertised",false);
        if(value.route()!=Route.FAMILY||value.cold())out.put("cold_absent_relation_unresolved",value.cold()&&value.status()==Status.PENDING);
        out.setAll(object(OpportunityJson.toNode(value.original())));return InteractionArguments.app(out);
    }
    public static void verify(Observation value,Context context) {
        need(decode(new RawJson(OpportunityJson.encode(value.original())),context,value.pending(),value.cold()).equals(value),"typed result differs from original packet");
    }
    public static RawJson nativeFields(Context context,Pending pending,boolean cold) {
        // NativeWire supplies the reserved expected_revision from the same held observation.
        requireFrame(context,pending,cold);ObjectNode out=F.objectNode();
        if(cold){out.put("cold_recovery",1).put("heir_character_id",pending.subjectCharacterId()).put("candidate_character_id",pending.candidateCharacterId())
            .put("recipient_character_id",pending.recipientCharacterId()).put("source_date_raw",pending.sourceDateRaw());}
        if(pending.route()!=Route.FAMILY&&cold||pending.fulfillExistingBetrothal()&&cold)out.put("matrilineal_option_selected",pending.matrilinealOptionSelected());
        if(pending.fulfillExistingBetrothal())out.put("fulfill_existing_betrothal",true);
        return encode(out);
    }
    private static Field<Outbound> outbound(JsonNode n) {
        if(!n.has("outbound_pending_state")) {
            for(String key:List.of("outbound_pending_id","outbound_pending_age_days","outbound_pending_ai_reply_cutoff_days"))need(!n.has(key),"outbound receipt lacks state");
            return new Field<>(Presence.MISSING,null);
        }
        OutboundState state=enumeration(n,"outbound_pending_state",OutboundState.class);need(text(n,"outbound_pending_state").equals(state.name().toLowerCase(java.util.Locale.ROOT)),"native outbound state must use its exact lowercase literal");
        return new Field<>(Presence.PRESENT,new Outbound(state,integerField(n,"outbound_pending_id",I64_MIN,I64_MAX),
                integerField(n,"outbound_pending_age_days",I64_MIN,I64_MAX),integerField(n,"outbound_pending_ai_reply_cutoff_days",I64_MIN,I64_MAX)));
    }
    private static Field<TerminalDisposition> disposition(JsonNode n) {
        Set<String> fields=Set.of("proposal_disposition_source","terminal_cause_available","terminal_cause");
        if(fields.stream().noneMatch(n::has))return new Field<>(Presence.MISSING,null);
        return new Field<>(Presence.PRESENT,new TerminalDisposition(text(n,"proposal_disposition_source"),bool(n,"terminal_cause_available"),text(n,"terminal_cause")));
    }
    private static Field<RetainedEvents> retained(JsonNode n) {
        Set<String> fields=Set.of("retained_player_event_queue_available","retained_player_event_queue_read_complete","retained_player_event_queue_stable",
                "retained_player_event_queue_count","retained_original_role_letter_count","retained_original_role_letter_kind","retained_player_event_unavailable_reason");
        if(fields.stream().noneMatch(n::has))return new Field<>(Presence.MISSING,null);
        return new Field<>(Presence.PRESENT,new RetainedEvents(bool(n,"retained_player_event_queue_available"),bool(n,"retained_player_event_queue_read_complete"),
                bool(n,"retained_player_event_queue_stable"),number(n,"retained_player_event_queue_count",I64_MIN,I64_MAX),u64(n,"retained_original_role_letter_count"),
                text(n,"retained_original_role_letter_kind"),text(n,"retained_player_event_unavailable_reason")));
    }
    private static BigInteger character(JsonNode n,String key){return number(n,key,BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));}
    private static BigInteger optionalInteger(JsonNode n,String key,BigInteger min,BigInteger max){return n.has(key)?number(n,key,min,max):null;}
    private static Field<BigInteger> integerField(JsonNode n,String key,BigInteger min,BigInteger max){return !n.has(key)?new Field<>(Presence.MISSING,null):n.get(key).isNull()?new Field<>(Presence.NULL,null):new Field<>(Presence.PRESENT,number(n,key,min,max));}
    private static Field<Boolean> booleanField(JsonNode n,String key){return !n.has(key)?new Field<>(Presence.MISSING,null):n.get(key).isNull()?new Field<>(Presence.NULL,null):new Field<>(Presence.PRESENT,bool(n,key));}
    private static void optionalConstant(JsonNode n,String key,String value){if(n.has(key))eq(n,key,value);}
    private static void optionalConstant(JsonNode n,String key,BigInteger value){if(n.has(key))eq(n,key,value);}
}

