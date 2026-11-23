package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact observation DATA union. Independent physical/script facts never imply effective-law business or execution proof. */
public record CurrentRmtmObservationSource(CurrentRmtmObservation.Kind kind,boolean caseBound,boolean sampledTwice,
        Optional<TitlePhase> titlePhase,Optional<Council> council,Optional<Budget> budget,Optional<Offer> offer) {
    public static final List<String> COUNCIL_KEYS=List.of("councillor_chancellor","councillor_spymaster","minister_grand_marshal","minister_personnel","councillor_marshal","councillor_steward","minister_justice","councillor_court_chaplain","minister_works");
    public record TitlePhase(CurrentRmtmObservation.Phase phase,CurrentRmtmTitleQuerySource physical,boolean scriptOwnSingleHeir,
            boolean holderRealmSingleHeir,boolean witnessGuardBound,boolean witnessSampledTwice){
        public TitlePhase{Objects.requireNonNull(phase);Objects.requireNonNull(physical);StrictJson.require(witnessGuardBound&&witnessSampledTwice,"Independent actual script binding/two samples required");}
        ObjectNode encode(){var n=StrictJson.object().put("phase",phase.wire()).put("script_own_single_heir",scriptOwnSingleHeir).put("holder_realm_single_heir",holderRealmSingleHeir).put("witness_guard_bound",witnessGuardBound).put("witness_sampled_twice",witnessSampledTwice);n.set("physical",physical.encode());return n;}
        static TitlePhase decode(JsonNode n)throws IOException{var r=StrictJson.object(n,Set.of("phase","physical","script_own_single_heir","holder_realm_single_heir","witness_guard_bound","witness_sampled_twice"));return new TitlePhase(CurrentRmtmObservation.Phase.parse(NativeWire.text(r.get("phase"))),CurrentRmtmTitleQuerySource.decode(r.get("physical")),b(r,"script_own_single_heir"),b(r,"holder_realm_single_heir"),b(r,"witness_guard_bound"),b(r,"witness_sampled_twice"));}
    }
    public record Seat(String positionKey,long fullTaskId,Optional<Long> incumbentId,Optional<Boolean> incumbentAlive){
        public Seat{Objects.requireNonNull(positionKey);CurrentRmtmTitleQuery.requireFullId(fullTaskId);Objects.requireNonNull(incumbentId);Objects.requireNonNull(incumbentAlive);incumbentId.ifPresent(CurrentRmtmTitleQuery::requireFullId);StrictJson.require(incumbentId.isPresent()==incumbentAlive.isPresent(),"Actual incumbent/alive nullable pair differs");}
        ObjectNode encode(){var n=StrictJson.object().put("position_key",positionKey).put("full_task_id",fullTaskId);id(n,"incumbent_id",incumbentId);flag(n,"incumbent_alive",incumbentAlive);return n;}
        static Seat decode(JsonNode n)throws IOException{var r=StrictJson.object(n,Set.of("position_key","full_task_id","incumbent_id","incumbent_alive"));return new Seat(NativeWire.text(r.get("position_key")),CurrentRmtmTitleQuery.fullId(r.get("full_task_id")),oid(r.get("incumbent_id")),ob(r,"incumbent_alive"));}
    }
    public record Council(int ownerId,int nativeTaskCount,boolean completeModelCensus,boolean sampledTwice,List<Seat> seats){
        public Council{seats=List.copyOf(seats);StrictJson.require(ownerId!=-1&&nativeTaskCount>=0&&nativeTaskCount<=4096&&completeModelCensus&&sampledTwice&&seats.size()==9,"Complete actual nine-seat model required");var ids=new HashSet<Long>();for(int i=0;i<9;i++)StrictJson.require(COUNCIL_KEYS.get(i).equals(seats.get(i).positionKey())&&ids.add(seats.get(i).fullTaskId()),"Canonical ordered positions and distinct actual tasks required");}
        ObjectNode encode(){var n=StrictJson.object().put("owner_id",ownerId).put("native_task_count",nativeTaskCount).put("complete_model_census",completeModelCensus).put("sampled_twice",sampledTwice);var a=n.putArray("seats");for(var s:seats)a.add(s.encode());return n;}
        static Council decode(JsonNode n)throws IOException{var r=StrictJson.object(n,Set.of("owner_id","native_task_count","complete_model_census","sampled_twice","seats"));var a=r.get("seats");if(!a.isArray()||a.size()!=9)throw new IOException("Exactly nine fixed material seats required");var seats=new ArrayList<Seat>();for(var s:a)seats.add(Seat.decode(s));return new Council(i(r,"owner_id"),i(r,"native_task_count"),b(r,"complete_model_census"),b(r,"sampled_twice"),seats);}
    }
    public record Budget(boolean found,boolean visible,boolean enabled,boolean blockedByVisibleModal,Optional<Integer> ownerId,
            Optional<Long> fullTitleId,Optional<Long> holderId,boolean openAdmissible,boolean cancelAdmissible,String route,boolean sampledTwice){
        public Budget{Objects.requireNonNull(ownerId);Objects.requireNonNull(fullTitleId);Objects.requireNonNull(holderId);StrictJson.require(sampledTwice&&"my_realm_player".equals(route),"Fixed MyRealm GetPlayer.Self route required");ownerId.ifPresent(n->StrictJson.require(n!=-1,"Owner sentinel invalid"));fullTitleId.ifPresent(CurrentRmtmTitleQuery::requireFullId);holderId.ifPresent(CurrentRmtmTitleQuery::requireFullId);StrictJson.require(fullTitleId.isPresent()==holderId.isPresent(),"Actual title/holder nullable pair differs");if(!found)StrictJson.require(!visible&&!enabled&&ownerId.isEmpty()&&fullTitleId.isEmpty()&&!cancelAdmissible,"Known absent budget has no material model");if(cancelAdmissible)StrictJson.require(found&&visible&&enabled&&!blockedByVisibleModal,"Cancel requires actual visible ordinary budget");if(openAdmissible)StrictJson.require(!visible&&!blockedByVisibleModal,"Open requires actual hidden fixed view");}
        ObjectNode encode(){var n=StrictJson.object().put("found",found).put("visible",visible).put("enabled",enabled).put("blocked_by_visible_modal",blockedByVisibleModal).put("open_admissible",openAdmissible).put("cancel_admissible",cancelAdmissible).put("route",route).put("sampled_twice",sampledTwice);actor(n,"owner_id",ownerId);id(n,"full_title_id",fullTitleId);id(n,"holder_id",holderId);return n;}
        static Budget decode(JsonNode n)throws IOException{var r=StrictJson.object(n,Set.of("found","visible","enabled","blocked_by_visible_modal","owner_id","full_title_id","holder_id","open_admissible","cancel_admissible","route","sampled_twice"));return new Budget(b(r,"found"),b(r,"visible"),b(r,"enabled"),b(r,"blocked_by_visible_modal"),oi(r.get("owner_id")),oid(r.get("full_title_id")),oid(r.get("holder_id")),b(r,"open_admissible"),b(r,"cancel_admissible"),NativeWire.text(r.get("route")),b(r,"sampled_twice"));}
    }
    public record Offer(CurrentRmtmObservation.OfferTarget target,boolean found,boolean visible,boolean enabled,boolean blockedByVisibleModal,
            int actorId,int recipientId,String interactionKey,String description,boolean openAdmissible,boolean cancelAdmissible,boolean sampledTwice){
        public Offer{Objects.requireNonNull(target);StrictJson.require(actorId!=-1&&recipientId!=-1&&sampledTwice&&"offer_vassalization_interaction".equals(interactionKey),"Actual fixed Offer subject required");text(description);if(!found)StrictJson.require(!visible&&!enabled&&!cancelAdmissible,"Known absent Offer has no material window");if(openAdmissible)StrictJson.require(!visible&&!blockedByVisibleModal,"Actual hidden Offer required");if(cancelAdmissible)StrictJson.require(found&&visible&&enabled&&!blockedByVisibleModal,"Actual visible ordinary Close route required");}
        ObjectNode encode(){return StrictJson.object().put("target",target.wire()).put("found",found).put("visible",visible).put("enabled",enabled).put("blocked_by_visible_modal",blockedByVisibleModal).put("actor_id",actorId).put("recipient_id",recipientId).put("interaction_key",interactionKey).put("description",description).put("open_admissible",openAdmissible).put("cancel_admissible",cancelAdmissible).put("sampled_twice",sampledTwice);}
        static Offer decode(JsonNode n)throws IOException{var r=StrictJson.object(n,Set.of("target","found","visible","enabled","blocked_by_visible_modal","actor_id","recipient_id","interaction_key","description","open_admissible","cancel_admissible","sampled_twice"));var d=r.get("description");if(!d.isTextual())throw new IOException("Actual full description string required, including empty");return new Offer(CurrentRmtmObservation.OfferTarget.parse(NativeWire.text(r.get("target"))),b(r,"found"),b(r,"visible"),b(r,"enabled"),b(r,"blocked_by_visible_modal"),i(r,"actor_id"),i(r,"recipient_id"),NativeWire.text(r.get("interaction_key")),d.textValue(),b(r,"open_admissible"),b(r,"cancel_admissible"),b(r,"sampled_twice"));}
    }
    public CurrentRmtmObservationSource{
        Objects.requireNonNull(kind);Objects.requireNonNull(titlePhase);Objects.requireNonNull(council);Objects.requireNonNull(budget);Objects.requireNonNull(offer);
        int count=(titlePhase.isPresent()?1:0)+(council.isPresent()?1:0)+(budget.isPresent()?1:0)+(offer.isPresent()?1:0);
        StrictJson.require(sampledTwice&&count==1&&(kind==CurrentRmtmObservation.Kind.TITLE_PHASE)==titlePhase.isPresent()&&(kind==CurrentRmtmObservation.Kind.COUNCIL)==council.isPresent()&&(kind==CurrentRmtmObservation.Kind.BUDGET)==budget.isPresent()&&(kind==CurrentRmtmObservation.Kind.OFFER)==offer.isPresent(),"Exactly one actual kind component required");
        budget.ifPresent(v->StrictJson.require(caseBound||!v.openAdmissible()&&!v.cancelAdmissible(),"Unbound budget is readonly DATA"));
        offer.ifPresent(v->StrictJson.require(caseBound||!v.openAdmissible()&&!v.cancelAdmissible(),"Unbound Offer is readonly DATA"));
    }
    void requireFacts(CoreFrame.Prefix f){
        titlePhase.ifPresent(v->StrictJson.require(v.physical().actorId()==f.playedCharacterId(),"Physical actor differs from actual Core"));
        council.ifPresent(v->StrictJson.require(v.ownerId()==f.playedCharacterId(),"Council actual owner differs"));
        budget.ifPresent(v->{if(v.cancelAdmissible())StrictJson.require(v.ownerId().equals(Optional.of(f.playedCharacterId())),"Cancel subject differs from actual Core");});
        offer.ifPresent(v->StrictJson.require(v.actorId()==f.playedCharacterId(),"Offer actual issuer differs"));
    }
    public static CurrentRmtmObservationSource decode(JsonNode n)throws IOException{
        try{var r=StrictJson.object(n,Set.of("schema","kind","case_bound","sampled_twice","title_phase","council","budget","offer"));CurrentRmtmActorTransition.identity(r,"schema",CurrentRmtmObservation.SOURCE_SCHEMA);
            return new CurrentRmtmObservationSource(CurrentRmtmObservation.Kind.parse(NativeWire.text(r.get("kind"))),b(r,"case_bound"),b(r,"sampled_twice"),r.get("title_phase").isNull()?Optional.empty():Optional.of(TitlePhase.decode(r.get("title_phase"))),r.get("council").isNull()?Optional.empty():Optional.of(Council.decode(r.get("council"))),r.get("budget").isNull()?Optional.empty():Optional.of(Budget.decode(r.get("budget"))),r.get("offer").isNull()?Optional.empty():Optional.of(Offer.decode(r.get("offer"))));
        }catch(IllegalArgumentException|ArithmeticException e){throw new IOException("Invalid exact RMTM observation DATA",e);}
    }
    public ObjectNode encode(){var n=StrictJson.object().put("schema",CurrentRmtmObservation.SOURCE_SCHEMA).put("kind",kind.wire()).put("case_bound",caseBound).put("sampled_twice",sampledTwice);if(titlePhase.isPresent())n.set("title_phase",titlePhase.orElseThrow().encode());else n.putNull("title_phase");if(council.isPresent())n.set("council",council.orElseThrow().encode());else n.putNull("council");if(budget.isPresent())n.set("budget",budget.orElseThrow().encode());else n.putNull("budget");if(offer.isPresent())n.set("offer",offer.orElseThrow().encode());else n.putNull("offer");return n;}
    private static boolean b(ObjectNode n,String k)throws IOException{return CurrentRmtmActorTransition.bool(n,k);}
    private static int i(ObjectNode n,String k)throws IOException{return CurrentRmtmActorTransition.i32(n.get(k));}
    private static Optional<Integer> oi(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentRmtmActorTransition.i32(n));}
    private static Optional<Long> oid(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentRmtmTitleQuery.fullId(n));}
    private static Optional<Boolean> ob(ObjectNode n,String k)throws IOException{return n.get(k).isNull()?Optional.empty():Optional.of(b(n,k));}
    private static void actor(ObjectNode n,String k,Optional<Integer> v){if(v.isPresent())n.put(k,v.orElseThrow());else n.putNull(k);}
    private static void id(ObjectNode n,String k,Optional<Long> v){if(v.isPresent())n.put(k,v.orElseThrow());else n.putNull(k);}
    private static void flag(ObjectNode n,String k,Optional<Boolean> v){if(v.isPresent())n.put(k,v.orElseThrow());else n.putNull(k);}
    private static void text(String s){Objects.requireNonNull(s);StrictJson.require(s.getBytes(StandardCharsets.UTF_8).length<=16384,"Actual full Offer description exceeds16KiB");for(int p=0;p<s.length();){char c=s.charAt(p++);if(Character.isHighSurrogate(c)){StrictJson.require(p<s.length()&&Character.isLowSurrogate(s.charAt(p)),"Unpaired surrogate");p++;}else StrictJson.require(!Character.isLowSurrogate(c),"Unpaired surrogate");}}
}
