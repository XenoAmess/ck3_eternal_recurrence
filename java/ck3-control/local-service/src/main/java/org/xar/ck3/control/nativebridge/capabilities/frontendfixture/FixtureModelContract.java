package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;

/** Original probe and independent selected-model domains. Missing diagnostics remain missing, never defaulted. */
public final class FixtureModelContract {
    public sealed interface State permits Unavailable,Probe,Selected { }
    public record Unavailable(Optional<String> selectedBookmarkKey) implements State {
        public Unavailable {Objects.requireNonNull(selectedBookmarkKey);}
    }
    public record Probe(List<String> candidateKeys,int targetIndex,int selectedIndex,boolean candidateIdentityReady) implements State {
        public Probe {candidateKeys=List.copyOf(candidateKeys);StrictJson.require(candidateKeys.size()<=4096&&targetIndex>=-1&&targetIndex<candidateKeys.size()
                &&selectedIndex>=-1&&selectedIndex<candidateKeys.size(),"bounded original fixture probe indices required");}
    }
    public record Selected(Probe probe,boolean accepted,String status,Optional<String> bookmarkGroupKey,String bookmarkKey,
            int dateRaw,String governmentKey,boolean dateMatches,Optional<Boolean> feudal,Optional<BigInteger> originalDateQword) implements State {
        public Selected {Objects.requireNonNull(probe);Objects.requireNonNull(status);Objects.requireNonNull(bookmarkGroupKey);Objects.requireNonNull(bookmarkKey);
            Objects.requireNonNull(governmentKey);Objects.requireNonNull(feudal);Objects.requireNonNull(originalDateQword);}
    }
    public record Observation(Source source,BigInteger querySequence,State state,RawJson original) {
        public Observation {Objects.requireNonNull(source);positiveU64(querySequence);Objects.requireNonNull(state);Objects.requireNonNull(original);}
        public Optional<String> selectedBookmarkKey(){return state instanceof Unavailable value?value.selectedBookmarkKey():state instanceof Selected value?Optional.of(value.bookmarkKey()):Optional.empty();}
        public Probe probe(){return state instanceof Probe value?value:state instanceof Selected value?value.probe():fail("native fixture model is unavailable");}
        public int targetIndex(){return probe().targetIndex();}
        public int selectedIndex(){return probe().selectedIndex();}
        public void probeTarget(String key,boolean scenario) {
            Probe value=probe();StrictJson.require(value.candidateIdentityReady()&&value.targetIndex()>=0&&value.candidateKeys().get(value.targetIndex()).equals(key)
                    &&key.equals(scenario?FrontendFixturePolicy.SCENARIO_TARGET.characterNameKey():FrontendFixturePolicy.ROBERT_KEY),"original fixture probe differs from exact target");
        }
        public Candidate selected(String key,boolean scenario,boolean requireSelected) {
            probeTarget(key,scenario);StrictJson.require(state instanceof Selected,"independent actual selected-model fields are not yet available");var value=(Selected)state;
            String bookmark=scenario?FrontendFixturePolicy.SCENARIO_TARGET.bookmarkKey():"bm_1066_rags_to_riches";
            String group=scenario?"bm_group_867":"bm_group_1066";String government=scenario?"clan_government":"feudal_government";
            StrictJson.require(value.accepted()&&value.status().equals("identity_ready")&&value.bookmarkKey().equals(bookmark)
                    &&(value.bookmarkGroupKey().isEmpty()||value.bookmarkGroupKey().equals(Optional.of(group)))&&value.governmentKey().equals(government)
                    &&value.dateMatches()&&(scenario?value.dateRaw()==51394920:value.dateRaw()>0&&value.feudal().equals(Optional.of(true)))
                    &&(!requireSelected||value.probe().selectedIndex()==value.probe().targetIndex()),"independent fixture selected identity/government/date/bookmark not proven");
            return new Candidate(source,querySequence,value.bookmarkGroupKey(),bookmark,key,government,value.dateRaw(),scenario);
        }
    }
    private final PreparedFixture fixture;
    private final FrontendRulesDefinitions definitions;
    private final ReadContract<Observation> model;
    public FixtureModelContract(PreparedFixture fixture,FrontendRulesDefinitions identicalDefinitions) {
        this.fixture=Objects.requireNonNull(fixture);definitions=Objects.requireNonNull(identicalDefinitions);
        var primitive=fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO?FrontendRulesRequests.Primitive.SCENARIO_PROBE:FrontendRulesRequests.Primitive.BOOKMARK_MODEL;
        model=new ReadContract<>("fixture-start.original-model."+fixture.policy().kind().name().toLowerCase(java.util.Locale.ROOT)+".v1",primitive.operation(),Optional.of(primitive.capability()),
                "original-driver."+primitive.operation().value(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.FRONTEND_SESSION,definitions.originalDriverSource(),request->{
                    StrictJson.require(request.origin() instanceof CommandOrigin.Frontend&&request.origin().requireFrontend().frame() instanceof FrontendFrame.Menu
                            &&request.arguments().members().isEmpty(),"fixture probe requires original zero-revision Menu and empty arguments");return primitive.emptyRequest();
                },receipt->decode(FrontendRulesDefinitions.result(receipt),definitions.source(receipt),FrontendRulesDefinitions.sequence(receipt),fixture.policy().kind()));
    }
    public ReadContract<Observation> model(){return model;}
    public static Observation decode(RawJson raw,Source source,BigInteger sequence,FrontendFixturePolicy.Kind kind) {
        JsonNode row=StrictJson.parse(raw.bytes());StrictJson.require(row.isObject(),"original native model object required");
        if(kind==FrontendFixturePolicy.Kind.SCENARIO&&row.has("status")&&StrictJson.text(row.get("status")).equals("unavailable")) {
            StrictJson.require(row.has("accepted")&&bool(row,"accepted"),"actual unavailable scenario probe must retain successful query ACK");
            return new Observation(source,sequence,new Unavailable(optionalText(row,"selected_bookmark_key")),raw);
        }
        JsonNode keys=row.get("candidate_keys");StrictJson.require(keys!=null&&keys.isArray()&&keys.size()<=4096,"original bounded candidate keys required");
        var names=new ArrayList<String>();for(JsonNode key:keys)names.add(StrictJson.text(key));
        var probe=new Probe(names,integer(row,"supported_1066_candidate_index",-1,4095),integer(row,"selected_character_index",-1,4095),bool(row,"candidate_identity_ready"));
        List<String> fields=List.of("accepted","status","selected_bookmark_key","selected_date_low_raw","supported_1066_government_key","supported_1066_date_matches");
        long present=fields.stream().filter(row::has).count();
        if(present==0)return new Observation(source,sequence,probe,raw);
        StrictJson.require(present==fields.size(),"partial independent selected-model fields cannot prove identity");
        var selected=new Selected(probe,bool(row,"accepted"),StrictJson.text(row.get("status")),optionalText(row,"selected_bookmark_group_key"),StrictJson.text(row.get("selected_bookmark_key")),
                integer(row,"selected_date_low_raw",Integer.MIN_VALUE,Integer.MAX_VALUE),StrictJson.text(row.get("supported_1066_government_key")),bool(row,"supported_1066_date_matches"),
                row.has("supported_1066_feudal")?Optional.of(bool(row,"supported_1066_feudal")):Optional.empty(),
                row.has("selected_date_raw")?Optional.of(StrictJson.integer(row.get("selected_date_raw"),BigInteger.valueOf(Long.MIN_VALUE),StrictJson.UINT64_MAX)):Optional.empty());
        return new Observation(source,sequence,selected,raw);
    }
    private static int integer(JsonNode n,String field,long min,long max){return Math.toIntExact(StrictJson.integer(n.get(field),min,max));}
    private static boolean bool(JsonNode n,String field){JsonNode value=n.get(field);StrictJson.require(value!=null&&value.isBoolean(),"exact native boolean required: "+field);return value.booleanValue();}
    private static Optional<String> optionalText(JsonNode n,String field){JsonNode value=n.get(field);return value==null||value.isNull()?Optional.empty():Optional.of(StrictJson.text(value));}
    private static <T>T fail(String reason){throw new IllegalArgumentException(reason);}
}
