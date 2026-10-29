package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayInputStream;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.planning.jointintake.FormalProposalIntake;

/** Frozen actual Python producer/candidate rows -> new pool -> original assembly/intake/selector and complete serialization.
 * The original fixture remains a software source oracle, not fresh Native/Game qualification. */
final class M5FamilyCandidatePoolTest {
    private static Obj vector()throws Exception {
        try(var stream=M5FamilyCandidatePoolTest.class.getResourceAsStream("/m5peacetimeassembly/producer-golden-v1.json.gz")) {
            assertNotNull(stream,"actual complete original producer corpus required; never skip");byte[] compressed=stream.readNBytes(65537);assertTrue(compressed.length<=65536);
            assertEquals("61374f70cb7398c98bf88a16d7a797106ecdd47e1e8ee86c83b483461b5df6e6",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)),"actual retained producer corpus drift");
            byte[] raw;try(var gzip=new GZIPInputStream(new ByteArrayInputStream(compressed))){raw=gzip.readNBytes(1048577);assertTrue(raw.length<=1048576);assertEquals(-1,gzip.read());}
            var document=StrictJson.parse(raw,1048576);assertEquals("MATCH",document.get("source_postcheck").textValue());assertEquals(0,document.get("game_rpc_count").intValue());
            assertTrue(document.get("original_tests_run").intValue()>20);assertEquals(0,document.get("original_failures").intValue());assertEquals(0,document.get("original_errors").intValue());assertEquals(0,document.get("original_skipped").intValue());
            var sample=java.util.stream.StreamSupport.stream(document.get("cases").spliterator(),false).filter(x->x.get("name").textValue().equals("family-five-choices")).findFirst().orElseThrow();
            assertTrue(sample.get("accepted").booleanValue());assertTrue(sample.get("actual_native_driver_entry_executed").booleanValue());assertTrue(sample.get("actual_collector_executed").booleanValue());
            return object(OpportunityJson.parse(StrictJson.canonical(sample,131072)));
        }
    }
    private static Obj plan(Obj sample){return object(object(object(sample.get("input")).get("family")).get("plan"));}
    private static PeacetimeAssembly.Inputs input(Obj sample,M5FamilyCandidatePool.Pool pool) {
        var old=PeacetimeAssemblyCodec.decodeHistoricalV1(OpportunityJson.encode(sample.get("input")));
        return new PeacetimeAssembly.Inputs(old.scope(),old.initialSnapshot(),old.baselinePlan(),old.before(),old.after(),old.constructionRelease(),old.construction(),old.faction(),pool.family());
    }
    private static Obj intake(PeacetimeAssembly.Inputs input,Obj sources) {
        return object(OpportunityJson.parse(FormalProposalIntake.collect(OpportunityJson.encode(new Obj(Map.of("schema",new Text(FormalProposalIntake.REQUEST_SCHEMA),"snapshot",input.initialSnapshot(),"sources",sources))))));
    }
    @Test void allFiveActualAlternativesMatchTheOriginalProducerAndCompleteConsumerGraph()throws Exception {
        Obj sample=vector();var pool=M5FamilyCandidatePool.collect(plan(sample));assertEquals(5,pool.variants().size());
        var original=PeacetimeAssemblyCodec.decodeHistoricalV1(OpportunityJson.encode(sample.get("input")));
        assertEquals(original.family(),pool.family(),"actual Python choice-by-choice variant expansion must match exactly");
        assertEquals(pool,M5FamilyCandidatePool.decode(M5FamilyCandidatePool.encode(pool)));
        var input=input(sample,pool);Obj sources=PeacetimeAssembly.source(PeacetimeAssembly.compose(input));var observed=intake(input,sources);Obj expected=object(sample.get("collector"));
        assertEquals(expected.get("collected_candidate_ids"),observed.get("collected_candidate_ids"));assertEquals(expected.get("collected_domains"),observed.get("collected_domains"));
        assertEquals(expected.get("analysis_sha256"),new Text(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(StrictJson.canonical(OpportunityJson.toNode(observed.get("analysis")),131072)))));
        assertEquals(observed,OpportunityJson.parse(OpportunityJson.encode(observed)),"complete producer-to-selector result round trip");
        assertEquals(5,pool.variants().stream().map(M5FamilyCandidatePool.Variant::candidateCharacterId).distinct().count());
    }
    @Test void occupiedFirstCandidateAllowsARealLaterAlternativeInsteadOfRepeatingTheSelectedPlan()throws Exception {
        Obj sample=vector();var pool=M5FamilyCandidatePool.collect(plan(sample));var input=input(sample,pool);Obj source=PeacetimeAssembly.source(PeacetimeAssembly.compose(input));
        Obj domains=object(source.get("domains")),commitments=object(source.get("existing_commitments"));
        Obj onlyFamily=source.with("domains",new Obj(Map.of("marriage",domains.get("marriage"))))
                .with("existing_commitments",commitments.with("character_ids",new Arr(List.of(new IntegerValue(pool.variants().getFirst().candidateCharacterId())))));
        Obj selected=intake(input,onlyFamily),analysis=object(selected.get("analysis"));
        String id=OpportunityJson.text(analysis.get("selected_candidate_id"),"actual later selected identity");
        assertTrue(id.contains(":"+pool.variants().get(1).candidateCharacterId()+":"),"joint selector must choose actual second native candidate when first is occupied");
        assertFalse(id.contains(":"+pool.variants().getFirst().candidateCharacterId()+":"));
        Obj proof=object(pool.variants().get(1).plan().get("family_marriage_private_diagnostic"));
        assertEquals(new IntegerValue(pool.variants().get(1).candidateCharacterId()),proof.get("selected_candidate_character_id"));
    }
    @Test void noMissingListFallbackDuplicatesWrongTypesOrFakeVariantsCanEnterThePool()throws Exception {
        Obj actual=plan(vector());var missing=new java.util.LinkedHashMap<>(actual.members());missing.remove("family_marriage_valued_choices");
        assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.collect(new Obj(missing)));
        List<Value> choices=OpportunityJson.array(actual.get("family_marriage_valued_choices"),"real choices");
        var duplicate=new ArrayList<>(choices);duplicate.set(1,duplicate.getFirst());
        assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.collect(actual.with("family_marriage_valued_choices",new Arr(duplicate))));
        for(Value wrong:List.of(new Bool(true),new DecimalValue("38710.0"),new Text("38710"))) {
            var changed=new ArrayList<>(choices);changed.set(0,object(changed.getFirst()).with("candidate_character_id",wrong));
            assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.collect(actual.with("family_marriage_valued_choices",new Arr(changed))));
        }
        var pool=M5FamilyCandidatePool.collect(actual);var forged=new ArrayList<>(pool.variants());
        var second=forged.get(1);forged.set(1,new M5FamilyCandidatePool.Variant(second.candidateCharacterId(),second.plan().with("reason",new Text("changed outside the original two-field expansion"))));
        assertThrows(IllegalArgumentException.class,()->new M5FamilyCandidatePool.Pool(actual,forged));
        assertThrows(IllegalArgumentException.class,()->pool.candidate(BigInteger.valueOf(999)));
    }
    @Test void exactPoolSerializationRejectsWrongAndMissingFields()throws Exception {
        var pool=M5FamilyCandidatePool.collect(plan(vector()));Obj wire=object(OpportunityJson.parse(M5FamilyCandidatePool.encode(pool)));
        assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.decode(OpportunityJson.encode(wire.with("unknown",Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.decode(OpportunityJson.encode(wire.with("choice_indices",Nil.INSTANCE))));
        var missing=new java.util.LinkedHashMap<>(wire.members());missing.remove("original_plan");
        assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.decode(OpportunityJson.encode(new Obj(missing))));
        for(Value wrong:List.of(new Bool(true),new DecimalValue("0.0"),new Text("0"),new IntegerValue(BigInteger.ONE)))
            assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.fromJson(wire.with("choice_indices",new Arr(List.of(wrong,new IntegerValue(BigInteger.ONE),new IntegerValue(BigInteger.TWO),new IntegerValue(BigInteger.valueOf(3)),new IntegerValue(BigInteger.valueOf(4)))))));
        assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.fromJson(wire.with("choice_indices",new Arr(List.of(new IntegerValue(BigInteger.ZERO))))));
        Obj legacy=new Obj(Map.of("schema",new Text("xar.java.m5-family-candidate-pool/v1"),"original_plan",pool.originalPlan(),"variants",new Arr(List.of())));
        assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.decode(OpportunityJson.encode(legacy)),"production compact parser must not silently accept legacy expanded fields");
    }
    @Test void javaResourceContextFollowsEachActualChoiceAndRetainsEveryOtherObservedField()throws Exception {
        Obj original=plan(vector());
        Obj context=new Obj(Map.of("active_wars",new Arr(List.of()),"treasury_observed",Nil.INSTANCE,
                "future_war_cash_reserve_raw",Nil.INSTANCE,"prospective_ally_war_obligation",new Text("unknown"),
                "proposal",original.get("family_marriage_choice")));
        var pool=M5FamilyCandidatePool.collect(original.with("family_marriage_war_context",context));
        for(var variant:pool.variants())assertEquals(context.with("proposal",variant.plan().get("family_marriage_choice")),variant.plan().get("family_marriage_war_context"));
        assertEquals(pool,M5FamilyCandidatePool.decode(M5FamilyCandidatePool.encode(pool)));
        assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.collect(original.with("family_marriage_war_context",context.with("proposal",Nil.INSTANCE))));
    }
    @Test void actualFormalConsumerStillRejectsCrossFrameProofAndNativeDeniedAlternative()throws Exception {
        Obj sample=vector(),original=plan(sample),diagnostic=object(original.get("family_marriage_private_diagnostic")),legality=object(original.get("family_marriage_legality"));
        Obj crossed=original.with("family_marriage_private_diagnostic",diagnostic.with("native_revision",new IntegerValue(OpportunityJson.integer(diagnostic.get("native_revision"),"revision").add(BigInteger.ONE))));
        var legalRows=new ArrayList<>(OpportunityJson.array(legality.get("native_legal_candidates"),"actual legal candidates"));
        BigInteger second=M5FamilyCandidatePool.collect(original).variants().get(1).candidateCharacterId();
        for(int i=0;i<legalRows.size();i++)if(new IntegerValue(second).equals(object(legalRows.get(i)).get("candidate_character_id")))
            legalRows.set(i,object(legalRows.get(i)).with("complete_can_send",new Bool(false)));
        Obj denied=original.with("family_marriage_legality",legality.with("native_legal_candidates",new Arr(legalRows)));
        for(Obj invalid:List.of(crossed,denied)) {
            var pool=M5FamilyCandidatePool.decode(M5FamilyCandidatePool.encode(M5FamilyCandidatePool.collect(invalid)));
            var input=input(sample,pool);
            assertThrows(org.xar.ck3.control.contracts.projection.ProjectionDomainRejection.class,
                    ()->intake(input,PeacetimeAssembly.source(PeacetimeAssembly.compose(input))));
        }
    }
    @Test void productionV2AndExplicitHistoricalV1CannotAliasEachOthersWireShape()throws Exception {
        Obj sample=vector(),oldRequest=object(sample.get("input"));var pool=M5FamilyCandidatePool.collect(plan(sample));
        assertThrows(IllegalArgumentException.class,()->PeacetimeAssemblyCodec.decode(OpportunityJson.encode(oldRequest)));
        var historical=PeacetimeAssemblyCodec.decodeHistoricalV1(OpportunityJson.encode(oldRequest));
        Obj current=oldRequest.with("schema",new Text(PeacetimeAssembly.REQUEST_SCHEMA)).with("family",PeacetimeAssemblyCodec.familyStage(pool.family()));
        var actual=PeacetimeAssemblyCodec.decode(OpportunityJson.encode(current));assertEquals(historical,actual);
        assertThrows(IllegalArgumentException.class,()->PeacetimeAssemblyCodec.decodeHistoricalV1(OpportunityJson.encode(current)));
        Obj sources=PeacetimeAssembly.source(PeacetimeAssembly.compose(actual)),domains=object(sources.get("domains"));
        Obj legacyMarriage=new Obj(Map.of("plan",pool.originalPlan(),"plans",new Arr(pool.variants().stream().<Value>map(M5FamilyCandidatePool.Variant::plan).toList())));
        Obj oldSources=sources.with("domains",domains.with("marriage",legacyMarriage));
        Obj oldIntake=new Obj(Map.of("schema",new Text(FormalProposalIntake.HISTORICAL_REQUEST_SCHEMA),"snapshot",actual.initialSnapshot(),"sources",oldSources));
        assertThrows(IllegalArgumentException.class,()->FormalProposalIntake.collect(OpportunityJson.encode(oldIntake)));
        Obj oldResult=object(OpportunityJson.parse(FormalProposalIntake.collectHistoricalV1(OpportunityJson.encode(oldIntake))));
        Obj newResult=intake(actual,sources);assertEquals(oldResult,newResult,"explicit historical source and compact production source retain the same original proposals/selector result");
        assertThrows(IllegalArgumentException.class,()->FormalProposalIntake.collect(OpportunityJson.encode(oldIntake.with("schema",new Text(FormalProposalIntake.REQUEST_SCHEMA)))));
        Obj newIntake=oldIntake.with("schema",new Text(FormalProposalIntake.REQUEST_SCHEMA)).with("sources",sources);
        assertThrows(IllegalArgumentException.class,()->FormalProposalIntake.collectHistoricalV1(OpportunityJson.encode(newIntake)));
        assertThrows(IllegalArgumentException.class,()->M5FamilyCandidatePool.encode(M5FamilyCandidatePool.collect(pool.originalPlan().with("large_original_extension",new Text("x".repeat(131073))))),"oversize original proof remains RED without truncation or a raised shared bound");
    }
    private static Obj object(Value value){return OpportunityJson.object(value,"actual original fixture object");}
}
