package org.xar.ck3.control.application.ritecreation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.semantic.NativePlayerReligionContext;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;

/** Pure original independent-poststate diagnostics. No query, dispatch, business acceptance or Ready issuer.
 * Independent managed scope must be verified by its existing owner before this diagnostic API is called. */
public final class RiteCreationIndependentPoststate {
    public static final String SCOPE="independent religion identity and actual piety wallet comparison";
    public static final String FOLLOW_UP="Read actual current/main Rite core and parameter bags, directional hostility and normal adoption Can; edit also requires actual changed payload readback.";
    private static final Set<String> RESULT_FIELDS=Set.of("scope","expected_outcome_kind","identity_pattern_matches","before_ids","after_ids",
        "after_current_rite_is_main","piety_before_raw","piety_after_raw","piety_delta_raw","quoted_piety_cost_raw","piety_quote_comparison",
        "edit_payload_changed_observed","other_resource_effects_verified","doctrine_parameters_verified","adoption_native_permission_verified",
        "business_outcome_verified","action_ready","follow_up");
    private static final List<String> FALSE_FIELDS=List.of("edit_payload_changed_observed","other_resource_effects_verified",
        "doctrine_parameters_verified","adoption_native_permission_verified","business_outcome_verified","action_ready");
    private RiteCreationIndependentPoststate(){ }
    public record DiagnosticFrame(String snapshotId,BigInteger revision,BigInteger nativeRevision,BigInteger connectionGeneration,
            BigInteger gamePid,BigInteger actor,BigInteger date,Optional<String> episode,Scope independentlyVerifiedScope,Optional<RawJson> managedBinding) {
        public DiagnosticFrame {
            Objects.requireNonNull(snapshotId);Objects.requireNonNull(date);Objects.requireNonNull(episode);Objects.requireNonNull(independentlyVerifiedScope);Objects.requireNonNull(managedBinding);
            for(var v:List.of(revision,nativeRevision,connectionGeneration,gamePid,actor))need(v!=null&&v.signum()>0,"positive original frame integer required");
            need(revision.compareTo(U64)<=0,"original public revision is uint64");
        }
        public void requireSameOwner(DiagnosticFrame after){
            need(connectionGeneration.equals(after.connectionGeneration)&&gamePid.equals(after.gamePid)&&actor.equals(after.actor)&&date.equals(after.date)
                &&episode.equals(after.episode)&&independentlyVerifiedScope.equals(after.independentlyVerifiedScope),"poststate crossed owner/actor/episode/date");
            need(managedBinding.map(RiteCreationCodec::object).equals(after.managedBinding.map(RiteCreationCodec::object)),"poststate crossed managed campaign binding");
        }
    }
    public static final class DiagnosticSnapshot {
        private final RawJson original;private final DiagnosticFrame frame;private final OptionalLong piety;
        private DiagnosticSnapshot(RawJson original,DiagnosticFrame frame,OptionalLong piety){this.original=original;this.frame=frame;this.piety=piety;}
        public RawJson original(){return original;}public DiagnosticFrame frame(){return frame;}public OptionalLong piety(){return piety;}
    }
    /** Replay/data boundary only; constructing diagnostics grants no live read or action authority. */
    public static DiagnosticSnapshot replaySnapshot(RawJson original,Scope independentlyVerifiedScope){
        Objects.requireNonNull(original);Objects.requireNonNull(independentlyVerifiedScope);
        var n=object(original);var d=object(get(n,"diagnostics"));var hello=object(get(d,"hello"));var player=object(get(n,"played_character"));
        yes(get(n,"paused"));yes(get(n,"map_ready"));yes(get(player,"alive"));yes(get(hello,"ck3_build_match"));
        equal(get(hello,"expected_ck3_version"),VERSION);need(text(get(hello,"expected_ck3_sha256")).equalsIgnoreCase(SHA),"diagnostic requires actual .4");
        equal(get(hello,"game_adapter_id"),"ck3-1.20.0.4-msvc-x64");
        BigInteger rev=uint64(get(n,"revision")),nativeRev=positive(get(n,"native_revision")),connection=positive(get(d,"connection_generation"));
        BigInteger pid=positive(get(hello,"pid")),actor=positive(get(player,"character_id")),date=exactInteger(get(n,"date_raw"));
        Optional<String> episode=optionalText(n.get("episode_run_id"));Optional<RawJson> managed=Optional.empty();
        if(independentlyVerifiedScope instanceof EpisodeScope selected){
            need(!"native_campaign".equals(n.path("episode_projection").asText()),"managed campaign requires its independently verified scope");
            need(episode.filter(v->!v.isEmpty()).isPresent()&&episode.orElseThrow().equals(selected.episode()),"durable actual episode required");
        }else {
            equal(get(n,"episode_projection"),"native_campaign");var binding=object(get(n,"managed_campaign_run_binding"));
            need(get(binding,"state_dir").isTextual(),"actual managed state directory absent");
            managed=Optional.of(new RawJson(binding.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        }
        JsonNode wallet=n.get("played_character_piety");OptionalLong piety=OptionalLong.empty();
        if(wallet!=null&&!wallet.isNull()){
            var w=object(wallet);shape(w,Set.of("raw","scale"),Set.of());need(exactInteger(get(w,"scale")).equals(BigInteger.valueOf(100000)),"actual piety scale differs");
            piety=OptionalLong.of(signed64(get(w,"raw")));
        }
        String id=n.has("snapshot_id")&&!n.get("snapshot_id").isNull()?text(n.get("snapshot_id")):"";
        return new DiagnosticSnapshot(original,new DiagnosticFrame(id,rev,nativeRev,connection,pid,actor,date,episode,independentlyVerifiedScope,managed),piety);
    }
    /** Live callers retain the actual assembler product; snapshot/frame values are rechecked, not reconstructed from intent. */
    public static DiagnosticSnapshot snapshot(Complete actual,Scope independentlyVerifiedScope){
        Objects.requireNonNull(actual);var value=replaySnapshot(new RawJson(DriverJson.encode(actual.semantic())),independentlyVerifiedScope);var f=value.frame();
        need(f.snapshotId().equals(actual.identity().frame().snapshotId())&&f.revision().equals(actual.identity().frame().revision())
            &&f.nativeRevision().equals(actual.identity().frame().identity().nativeRevision())&&f.date().equals(actual.identity().frame().identity().dateRaw())
            &&f.actor().equals(actual.identity().frame().identity().player())&&f.connectionGeneration().equals(actual.connectionGeneration())
            &&f.gamePid().equals(BigInteger.valueOf(actual.identity().game().pid())),"diagnostic differs from actual Complete");
        return value;
    }
    public static final class Observation {
        private final DiagnosticSnapshot snapshot;private final NativePlayerReligionContext context;private final RawJson original;
        private Observation(DiagnosticSnapshot snapshot,NativePlayerReligionContext context,RawJson original){this.snapshot=snapshot;this.context=context;this.original=original;}
        public DiagnosticSnapshot snapshot(){return snapshot;}public NativePlayerReligionContext context(){return context;}public RawJson original(){return original;}
    }
    /** Exact flattened original context provenance; the registered receipt adapter supplies this actual view.
     * Unknown extra addon fields are retained, as in the original projection onto _CONTEXT_KEYS. */
    public static Observation observe(DiagnosticSnapshot snapshot,RawJson original){
        Objects.requireNonNull(snapshot);Objects.requireNonNull(original);var n=object(original);yes(get(n,"read_only"));equal(get(n,"domain_key"),"player_religion_context_v1");
        need(exactInteger(get(n,"queried_revision")).equals(snapshot.frame().revision())&&exactInteger(get(n,"snapshot_revision")).equals(snapshot.frame().nativeRevision()),"independent query provenance/frame differs");
        equal(get(n,"backend_id"),"ck3-1.20.0.4-native-player-religion-context-v1");
        var projection=empty();for(String field:NativePlayerReligionContext.FIELDS)projection.set(field,get(n,field));
        var context=NativePlayerReligionContext.decode(projection);need(context.exactBuild()==NativePlayerReligionContext.Build.CROZIER4,"independent context requires .4");
        context.requireAvailableFrame(snapshot.frame().date(),snapshot.frame().actor());return new Observation(snapshot,context,original);
    }
    public record Ids(OptionalLong rite,OptionalLong faith,OptionalLong religion,OptionalLong main){
        public Ids {for(var id:new OptionalLong[]{rite,faith,religion,main}){Objects.requireNonNull(id);need(id.isEmpty()||id.getAsLong()>=0&&id.getAsLong()<=0xffff_ffffL,"original uint32 references required");}}
        public boolean complete(){for(var id:new OptionalLong[]{rite,faith,religion,main})if(id.isEmpty()||id.getAsLong()==0xffff_ffffL)return false;return true;}
        static Ids from(NativePlayerReligionContext c){return new Ids(c.riteId(),c.faithId(),c.religionId(),c.faithMainRiteId());}
        ObjectNode json(){var n=empty();number(n,"rite_id",rite);number(n,"faith_id",faith);number(n,"religion_id",religion);number(n,"faith_main_rite_id",main);return n;}
    }
    public enum QuoteComparison { UNKNOWN,EQUAL,DIFFERENT;public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}}
    public record Result(Outcome expected,Optional<Boolean> identityPatternMatches,Ids before,Ids after,Optional<Boolean> afterCurrentRiteIsMain,
            OptionalLong pietyBefore,OptionalLong pietyAfter,Optional<BigInteger> delta,OptionalLong quote,QuoteComparison comparison){
        public Result {
            Objects.requireNonNull(expected);Objects.requireNonNull(identityPatternMatches);Objects.requireNonNull(before);Objects.requireNonNull(after);
            Objects.requireNonNull(afterCurrentRiteIsMain);Objects.requireNonNull(pietyBefore);Objects.requireNonNull(pietyAfter);Objects.requireNonNull(delta);Objects.requireNonNull(quote);Objects.requireNonNull(comparison);
            var calculated=difference(pietyBefore,pietyAfter);need(delta.equals(calculated)&&comparison==compare(calculated,quote),"diagnostic wallet arithmetic/quote comparison differs");
            need(identityPatternMatches.isPresent()==afterCurrentRiteIsMain.isPresent(),"identity completion presence differs");
            if(identityPatternMatches.isPresent())need(before.complete()&&after.complete()
                &&identityPatternMatches.orElseThrow()==pattern(expected,before,after)&&afterCurrentRiteIsMain.orElseThrow()==(after.rite.getAsLong()==after.main.getAsLong()),"diagnostic identity pattern differs");
        }
        public boolean businessOutcomeVerified(){return false;}public boolean actionReady(){return false;}
    }
    public static Result evaluate(DiagnosticSnapshot before,DiagnosticSnapshot after,Observation first,Observation last,Outcome expected,OptionalLong quotedPietyCostRaw){
        Objects.requireNonNull(first);Objects.requireNonNull(last);Objects.requireNonNull(expected);Objects.requireNonNull(quotedPietyCostRaw);
        need(first.snapshot==before&&last.snapshot==after,"observations must retain their actual supplied snapshot objects");before.frame.requireSameOwner(after.frame);
        var a=Ids.from(first.context);var b=Ids.from(last.context);boolean complete=first.context.available()&&last.context.available()&&a.complete()&&b.complete();
        var delta=difference(before.piety,after.piety);return new Result(expected,complete?Optional.of(pattern(expected,a,b)):Optional.empty(),a,b,
            complete?Optional.of(b.rite.getAsLong()==b.main.getAsLong()):Optional.empty(),before.piety,after.piety,delta,quotedPietyCostRaw,compare(delta,quotedPietyCostRaw));
    }
    public static ObjectNode json(Result value){
        var n=empty().put("scope",SCOPE).put("expected_outcome_kind",value.expected.wire()).put("follow_up",FOLLOW_UP);
        optionalBoolean(n,"identity_pattern_matches",value.identityPatternMatches);n.set("before_ids",value.before.json());n.set("after_ids",value.after.json());
        optionalBoolean(n,"after_current_rite_is_main",value.afterCurrentRiteIsMain);number(n,"piety_before_raw",value.pietyBefore);number(n,"piety_after_raw",value.pietyAfter);number(n,"quoted_piety_cost_raw",value.quote);
        if(value.delta.isPresent())n.put("piety_delta_raw",value.delta.orElseThrow());else n.putNull("piety_delta_raw");
        n.put("piety_quote_comparison",value.comparison.wire());for(String field:FALSE_FIELDS)n.put(field,false);return n;
    }
    public static RawJson encode(Result value){return raw(json(Objects.requireNonNull(value)));}
    public static Result decode(RawJson original){
        var n=object(original);shape(n,RESULT_FIELDS,Set.of());equal(get(n,"scope"),SCOPE);equal(get(n,"follow_up"),FOLLOW_UP);for(String field:FALSE_FIELDS)no(get(n,field));
        Optional<BigInteger> delta=get(n,"piety_delta_raw").isNull()?Optional.empty():Optional.of(exactInteger(get(n,"piety_delta_raw")));
        QuoteComparison comparison;try{comparison=QuoteComparison.valueOf(text(get(n,"piety_quote_comparison")).toUpperCase(java.util.Locale.ROOT));}catch(IllegalArgumentException invalid){throw new IllegalArgumentException("unknown quote comparison",invalid);}
        need(comparison.wire().equals(text(get(n,"piety_quote_comparison"))),"canonical quote comparison required");
        return new Result(Outcome.parse(text(get(n,"expected_outcome_kind"))),nullable(n,"identity_pattern_matches",RiteCreationCodec::bool),ids(get(n,"before_ids")),ids(get(n,"after_ids")),
            nullable(n,"after_current_rite_is_main",RiteCreationCodec::bool),nullableLong(n,"piety_before_raw"),nullableLong(n,"piety_after_raw"),delta,nullableLong(n,"quoted_piety_cost_raw"),comparison);
    }
    private static Ids ids(JsonNode node){var n=object(node);shape(n,Set.of("rite_id","faith_id","religion_id","faith_main_rite_id"),Set.of());return new Ids(nullableLong(n,"rite_id"),nullableLong(n,"faith_id"),nullableLong(n,"religion_id"),nullableLong(n,"faith_main_rite_id"));}
    private static OptionalLong nullableLong(ObjectNode n,String field){var value=get(n,field);return value.isNull()?OptionalLong.empty():OptionalLong.of(signed64(value));}
    private static Optional<String> optionalText(JsonNode n){return n==null||n.isNull()?Optional.empty():Optional.of(text(n));}
    private static BigInteger exactInteger(JsonNode value){need(value!=null&&value.isIntegralNumber(),"exact JSON integer required");return value.bigIntegerValue();}
    private static BigInteger positive(JsonNode value){var n=exactInteger(value);need(n.signum()>0,"positive original frame integer required");return n;}
    private static Optional<BigInteger> difference(OptionalLong before,OptionalLong after){return before.isPresent()&&after.isPresent()?Optional.of(BigInteger.valueOf(after.getAsLong()).subtract(BigInteger.valueOf(before.getAsLong()))):Optional.empty();}
    private static QuoteComparison compare(Optional<BigInteger> delta,OptionalLong quote){return delta.isEmpty()||quote.isEmpty()?QuoteComparison.UNKNOWN:delta.orElseThrow().equals(BigInteger.valueOf(quote.getAsLong()).negate())?QuoteComparison.EQUAL:QuoteComparison.DIFFERENT;}
    private static boolean pattern(Outcome kind,Ids a,Ids b){return switch(kind){case CREATE_FAITH->a.religion.equals(b.religion)&&!a.faith.equals(b.faith)&&!a.rite.equals(b.rite);case CREATE_RITE->a.religion.equals(b.religion)&&a.faith.equals(b.faith)&&!a.rite.equals(b.rite);case EDIT_RITE->a.equals(b);};}
    private static void number(ObjectNode n,String key,OptionalLong value){if(value.isPresent())n.put(key,value.getAsLong());else n.putNull(key);}
    private static void optionalBoolean(ObjectNode n,String key,Optional<Boolean> value){if(value.isPresent())n.put(key,value.orElseThrow());else n.putNull(key);}
}
