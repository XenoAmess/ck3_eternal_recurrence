package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal.Order;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal.SourceFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure single-writer domain reducer. No file IO, native submit, secondary lock or claim writer. */
public final class ActiveRetreatState {
    private ActiveRetreatState() {}
    public static final String SCHEMA="xar.ordinary-active-retreat.v2";
    public enum ClaimStatus {SUBMITTING,UNKNOWN,ACK_RETAINED,NATIVE_REJECTED,OPERATIONAL_OBSERVED}
    public enum AttemptKind {PREVIEW,OBSERVE}
    public record ClaimKey(String episodeRunId,int selectedPublicCunitId,int expectedCombatId) {
        public ClaimKey {StrictJson.text(episodeRunId);require(selectedPublicCunitId>=0&&expectedCombatId!=-1,"exact public CUnit and full CombatID claim key required");}
        public static ClaimKey of(Order order){return new ClaimKey(order.source().episodeRunId(),order.arguments().selectedPublicCunitId(),order.arguments().expectedCombatId());}
    }
    public record Claim(ClaimKey key,ClaimStatus status) {public Claim {Objects.requireNonNull(key);Objects.requireNonNull(status);}}
    public record Attempt(AttemptKind kind,SourceFrame frame) {public Attempt {Objects.requireNonNull(kind);Objects.requireNonNull(frame);}}
    public record State(Optional<Order> pending,Optional<Obj> preview,Optional<Attempt> lastAttempt,
                        Optional<Obj> lastPost,List<Claim> claims) {
        public State {
            Objects.requireNonNull(pending);Objects.requireNonNull(preview);Objects.requireNonNull(lastAttempt);Objects.requireNonNull(lastPost);claims=List.copyOf(claims);
            require(claims.stream().map(Claim::key).distinct().count()==claims.size(),"retreat claim keys cannot repeat");
            if(pending.isPresent()) {
                ClaimKey key=ClaimKey.of(pending.orElseThrow());
                require(claims.stream().anyMatch(c->c.key().equals(key)&&Set.of(ClaimStatus.SUBMITTING,ClaimStatus.UNKNOWN,ClaimStatus.ACK_RETAINED).contains(c.status())),"pending retreat requires its unresolved durable claim");
            }
        }
        /** Only a genuinely new, independently qualified domain may use this initial state. */
        public static State initial(){return new State(Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),List.of());}
        public boolean claimed(ClaimKey key){return claims.stream().anyMatch(c->c.key().equals(key));}
    }
    public sealed interface Event permits StartPreview,FinishPreview,StartOrder,UnknownOrder,NativeOrderResult,StartObserve,FinishObserve {}
    public record StartPreview(SourceFrame frame) implements Event {public StartPreview {Objects.requireNonNull(frame);}}
    public record FinishPreview(SourceFrame frame,Obj normalizedPreview) implements Event {public FinishPreview {Objects.requireNonNull(frame);Objects.requireNonNull(normalizedPreview);}}
    public record StartOrder(Order order) implements Event {public StartOrder {Objects.requireNonNull(order);}}
    public record UnknownOrder(ClaimKey key,String failure) implements Event {public UnknownOrder {Objects.requireNonNull(key);StrictJson.text(failure);}}
    public record NativeOrderResult(ClaimKey key,Obj originalNativeResult) implements Event {public NativeOrderResult {Objects.requireNonNull(key);Objects.requireNonNull(originalNativeResult);}}
    public record StartObserve(SourceFrame frame) implements Event {public StartObserve {Objects.requireNonNull(frame);}}
    public record FinishObserve(SourceFrame frame,ActiveRetreatPost.Result independentPost) implements Event {public FinishObserve {Objects.requireNonNull(frame);Objects.requireNonNull(independentPost);}}
    public static State reduce(State before,Event event) {
        Objects.requireNonNull(before);Objects.requireNonNull(event);
        return switch(event) {
            case StartPreview value -> {
                require(before.pending().isEmpty(),"unresolved original retreat has priority over preview");
                yield new State(before.pending(),Optional.empty(),Optional.of(new Attempt(AttemptKind.PREVIEW,value.frame())),before.lastPost(),before.claims());
            }
            case FinishPreview value -> {
                require(before.pending().isEmpty()&&before.lastAttempt().equals(Optional.of(new Attempt(AttemptKind.PREVIEW,value.frame()))),"preview completion crossed original frame/attempt");
                require(value.frame().json().equals(value.normalizedPreview().get("source_binding")),"preview source differs from actual attempt");
                yield new State(before.pending(),Optional.of(value.normalizedPreview()),before.lastAttempt(),before.lastPost(),before.claims());
            }
            case StartOrder value -> {
                ClaimKey key=ClaimKey.of(value.order());
                require(before.pending().isEmpty()&&!before.claimed(key),"original retreat claim retained; target/token changes cannot replay");
                List<Claim> claims=new ArrayList<>(before.claims());claims.add(new Claim(key,ClaimStatus.SUBMITTING));
                // Pending and exclusion are one writer CAS, before the sole ActionCoordinator can submit.
                yield new State(Optional.of(value.order()),Optional.empty(),before.lastAttempt(),before.lastPost(),claims);
            }
            case UnknownOrder value -> {
                Order order=bound(before,value.key());
                Obj post=obj(f("status",text("unknown")),f("error",text(value.failure())),f("replay_allowed",new Bool(false)),f("operational_retreat_verified",new Bool(false)));
                yield new State(Optional.of(order),Optional.empty(),before.lastAttempt(),Optional.of(post),status(before.claims(),value.key(),ClaimStatus.UNKNOWN));
            }
            case NativeOrderResult value -> {
                Order order=bound(before,value.key());Obj result=value.originalNativeResult();
                boolean rejected=no(result.get("accepted"))&&new Text("rejected").equals(result.get("status"));
                ClaimStatus next=rejected?ClaimStatus.NATIVE_REJECTED:ClaimStatus.ACK_RETAINED;
                Obj post=obj(f("status",text(rejected?"native_rejected":"ack_retained_independent_post_required")),f("ack",result),
                        f("operational_retreat_verified",new Bool(false)),f("command_causation_verified",new Bool(false)),f("replay_allowed",new Bool(false)));
                yield new State(rejected?Optional.empty():Optional.of(order),Optional.empty(),before.lastAttempt(),Optional.of(post),status(before.claims(),value.key(),next));
            }
            case StartObserve value -> {
                Order order=before.pending().orElseThrow(()->new IllegalArgumentException("observe requires original pending retreat"));
                require(order.source().episodeRunId().equals(value.frame().episodeRunId()),"prior episode original intent must be retained without observation replay");
                yield new State(before.pending(),before.preview(),Optional.of(new Attempt(AttemptKind.OBSERVE,value.frame())),before.lastPost(),before.claims());
            }
            case FinishObserve value -> {
                Order order=before.pending().orElseThrow(()->new IllegalArgumentException("post requires original pending retreat"));
                require(before.lastAttempt().equals(Optional.of(new Attempt(AttemptKind.OBSERVE,value.frame()))),"post crossed original observe attempt");
                if(value.independentPost() instanceof ActiveRetreatPost.Observed observed) {
                    require(observed.after().equals(value.frame())&&observed.scope()==order.arguments().expectedScope(),"independent observed result crossed current frame/scope");
                    yield new State(Optional.empty(),Optional.empty(),before.lastAttempt(),Optional.of(observed.json()),status(before.claims(),ClaimKey.of(order),ClaimStatus.OPERATIONAL_OBSERVED));
                }
                yield new State(before.pending(),before.preview(),before.lastAttempt(),Optional.of(value.independentPost().json()),before.claims());
            }
        };
    }
    private static Order bound(State before,ClaimKey key){Order order=before.pending().orElseThrow(()->new IllegalArgumentException("original pending retreat is absent"));require(ClaimKey.of(order).equals(key),"original claim key changed");return order;}
    private static List<Claim> status(List<Claim> claims,ClaimKey key,ClaimStatus status){return claims.stream().map(c->c.key().equals(key)?new Claim(key,status):c).toList();}
    /** Import/restore cannot discard an exclusion, even after a completed or rejected attempt. */
    public static void requireClaimsRetained(State previous,State restored) {
        for(Claim old:previous.claims())require(restored.claims().stream().anyMatch(c->c.key().equals(old.key())),"restore discarded an original no-replay retreat claim");
        if(previous.pending().isPresent())require(restored.pending().equals(previous.pending()),"restore replaced an unresolved original retreat");
    }
    public static void verifyTransition(State before,State after,Event event){require(reduce(before,event).equals(after),"retreat domain body is not the actual pure reducer result");}
    public static Obj encode(State state) {
        List<Obj> claims=state.claims().stream().map(c->obj(f("episode_run_id",text(c.key().episodeRunId())),f("selected_public_cunit_id",number(c.key().selectedPublicCunitId())),
                f("expected_combat_id",number(c.key().expectedCombatId())),f("status",text(c.status().name().toLowerCase(java.util.Locale.ROOT))))).toList();
        Value attempt=state.lastAttempt().<Value>map(a->obj(f("kind",text(a.kind().name().toLowerCase(java.util.Locale.ROOT))),f("frame",a.frame().json()))).orElse(Nil.INSTANCE);
        return obj(f("schema",text(SCHEMA)),f("pending",state.pending().<Value>map(ActiveRetreatState::order).orElse(Nil.INSTANCE)),f("preview",state.preview().<Value>map(v->v).orElse(Nil.INSTANCE)),
                f("last_attempt",attempt),f("last_post",state.lastPost().<Value>map(v->v).orElse(Nil.INSTANCE)),f("claims",objects(claims)));
    }
    public static State decode(Obj body) {
        require(body.members().keySet().equals(Set.of("schema","pending","preview","last_attempt","last_post","claims"))&&new Text(SCHEMA).equals(body.get("schema")),"exact retreat v2 domain required; legacy once files need a complete explicit import");
        Optional<Order> pending=body.get("pending")==Nil.INSTANCE?Optional.empty():Optional.of(order(OpportunityJson.object(body.get("pending"),"pending")));
        Optional<Obj> preview=optionalObject(body.get("preview"),"preview"),post=optionalObject(body.get("last_post"),"last post");
        Optional<Attempt> attempt=Optional.empty();
        if(body.get("last_attempt")!=Nil.INSTANCE){Obj value=OpportunityJson.object(body.get("last_attempt"),"last attempt");require(value.members().keySet().equals(Set.of("kind","frame")),"exact attempt fields required");attempt=Optional.of(new Attempt(enumValue(AttemptKind.class,value.get("kind")),source(OpportunityJson.object(value.get("frame"),"attempt source"))));}
        List<Claim> claims=new ArrayList<>();
        for(Obj value:rows(body.get("claims"))){require(value.members().keySet().equals(Set.of("episode_run_id","selected_public_cunit_id","expected_combat_id","status")),"exact claim fields required");claims.add(new Claim(new ClaimKey(OpportunityJson.text(value.get("episode_run_id"),"episode"),id(value.get("selected_public_cunit_id")),int32(value.get("expected_combat_id"))),enumValue(ClaimStatus.class,value.get("status"))));}
        return new State(pending,preview,attempt,post,claims);
    }
    public static Obj order(Order value) {
        var a=value.arguments();Obj args=obj(f("selected_public_cunit_id",number(a.selectedPublicCunitId())),f("expected_revision",number(a.expectedRevision())),f("expected_combat_id",number(a.expectedCombatId())),
                f("expected_side_index",number(a.expectedSideIndex())),f("expected_scope",text(a.expectedScope().wire())),f("target_province_id",number(a.targetProvinceId())),f("candidate_token",text(a.candidateToken())));
        return obj(f("source_binding",value.source().json()),f("selected_owner_character_id",number(value.selectedOwnerCharacterId())),f("arguments",args),
                f("affected_public_cunit_ids_in_stored_order",numbers(value.affectedInStoredOrder())),f("unaffected_same_side_public_cunit_ids_in_stored_order",numbers(value.unaffectedInStoredOrder())),f("route_province_ids",numbers(value.routeProvinceIds())),f("assessment",value.assessment()));
    }
    public static Order order(Obj value) {
        require(value.members().keySet().equals(Set.of("source_binding","selected_owner_character_id","arguments","affected_public_cunit_ids_in_stored_order","unaffected_same_side_public_cunit_ids_in_stored_order","route_province_ids","assessment")),"exact pending order fields required");
        Obj a=OpportunityJson.object(value.get("arguments"),"order arguments");require(a.members().keySet().equals(Set.of("selected_public_cunit_id","expected_revision","expected_combat_id","expected_side_index","expected_scope","target_province_id","candidate_token")),"exact typed order fields required");
        String wire=OpportunityJson.text(a.get("expected_scope"),"scope");BattleRetreatPolicy.Scope scope=switch(wire){case "full_side"->BattleRetreatPolicy.Scope.FULL_SIDE;case "owner_subset"->BattleRetreatPolicy.Scope.OWNER_SUBSET;default->throw new IllegalArgumentException("unknown retreat scope");};
        var args=new BattleRetreatPolicy.RetreatOrder(id(a.get("selected_public_cunit_id")),OpportunityJson.integer(a.get("expected_revision"),"expected_revision"),int32(a.get("expected_combat_id")),int32(a.get("expected_side_index")),scope,province(a.get("target_province_id")),OpportunityJson.text(a.get("candidate_token"),"token"));
        return new Order(source(OpportunityJson.object(value.get("source_binding"),"source")),id(value.get("selected_owner_character_id")),args,ids(value.get("affected_public_cunit_ids_in_stored_order")),ids(value.get("unaffected_same_side_public_cunit_ids_in_stored_order")),ids(value.get("route_province_ids")),OpportunityJson.object(value.get("assessment"),"assessment"));
    }
    public static SourceFrame source(Obj value) {
        require(value.members().keySet().equals(Set.of("snapshot_id","revision","native_revision","date_raw","episode_run_id","connection_generation")),"exact retreat source fields required");
        return new SourceFrame(OpportunityJson.text(value.get("snapshot_id"),"snapshot"),OpportunityJson.integer(value.get("revision"),"revision"),OpportunityJson.integer(value.get("native_revision"),"native revision"),OpportunityJson.integer(value.get("date_raw"),"date"),OpportunityJson.text(value.get("episode_run_id"),"episode"),OpportunityJson.integer(value.get("connection_generation"),"generation"));
    }
    private static Optional<Obj> optionalObject(Value value,String name){return value==Nil.INSTANCE?Optional.empty():Optional.of(OpportunityJson.object(value,name));}
    private static <E extends Enum<E>> E enumValue(Class<E> type,Value value){String wire=OpportunityJson.text(value,"enum");for(E candidate:type.getEnumConstants())if(candidate.name().toLowerCase(java.util.Locale.ROOT).equals(wire))return candidate;throw new IllegalArgumentException("unknown "+type.getSimpleName());}
}
