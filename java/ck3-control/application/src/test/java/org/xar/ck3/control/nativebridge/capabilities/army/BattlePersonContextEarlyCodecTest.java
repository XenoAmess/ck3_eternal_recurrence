package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;

/** Real Python producer/normalizer to the sole Java typed facade; required environment never becomes a skip. */
class BattlePersonContextEarlyCodecTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    private static List<Fixture> originalFixtures;
    private record Fixture(BattlePersonExternalCodec.Leaf leaf,ObjectNode raw,JsonNode expected) { }
    private static String required(String name) {String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("explicit -D"+name+" required");return value;}
    private static synchronized List<Fixture> fixtures() throws Exception {
        if(originalFixtures!=null)return originalFixtures;
        String script="""
                import sys,json,copy
                from pathlib import Path
                r=Path(sys.argv[1]);sys.path.insert(0,str(r/'ck3_autonomous_player'/'src'));sys.path.insert(0,str(r/'ck3_autonomous_player'/'tests'/'unit'))
                from xar_autoplayer.bridge.battle_person_trait_stage_291d460_contract import normalize_trait_stage_291d460
                from xar_autoplayer.bridge.battle_person_absent_recipient_contract import normalize_absent_recipient_inputs
                from xar_autoplayer.bridge.battle_person_helper_2922070_contract import normalize_helper_2922070
                from xar_autoplayer.bridge.battle_person_conference_24b1d00_contract import normalize_conference_24b1d00
                from xar_autoplayer.bridge.battle_person_uncached_recipient_contract import normalize_uncached_recipient_inputs
                from xar_autoplayer.bridge.battle_person_provider_bucket_contract import normalize_provider_bucket_291c5b2
                from test_battle_person_2922070_stage_chain_12003 import helper_2922070
                from test_battle_person_conference_stage_chain_12003 import conference
                from test_battle_person_uncached_recipient_12003 import raw as uncached
                pc={'keys_count':0,'values_count':0,'keys_u16':[],'values_q64':[],'reason':None}
                group={'role':'base','track_index':None,'level_index':None,'property_identity':'actual-base','base_property_block':pc,'conditional_b_count':0,'conditional_b_rows':[],'conditional_a_count':0,'conditional_a_rows':[],'ready':True,'reason':None}
                h=0x811c9dc5
                for _ in range(8):h=((h^0)*0x1000193)&0xffffffff
                side={'status':'available','ready':True,'map_mask_raw':0,'map_overflow_raw':0,'hash_u32':h,'first_row_index':0,'probes':[{'row_index':0,'distance_u8':1,'control_u8':0,'key_pointer_raw':None,'admitted':False,'reason':None}],'kind_raw':0,'owner_selection':None,'property_identity':None,'property_block':None,'reason':None}
                row={'native_index':0,'trait_id_raw':17,'definition_selection':'indexed_trait_database','definition_identity':'actual-trait','definition_pointer_raw':0,'composite_ready':True,'composite_groups':[group],'growth_flag_raw':1,'definition_id_raw':17,'track_count_raw':None,'growth_trait_match_index':None,'growth_prefix_offset_raw':None,'growth_aux_count_raw':None,'growth_output_count_raw':0,'growth_prefix_track_counts':None,'growth_tracks':[],'growth_selection':'empty_character_flag','composite_reason':None,'side':side,'reason':None}
                trait={'status':'available','ready':True,'character_id':29829,'trait_count':1,'trait_array_present':True,'rows':[row],'selector_a_selection':'actual','selector_a_identity':'actual-a','selector_b_selection':'actual','selector_b_identity':'actual-b','selector_a_key_raw':None,'selector_b_key_raw':None,'selector_a_membership_count':0,'selector_b_primary_count':0,'selector_b_nested_count':0,'selector_a_keys_i32':[],'selector_b_primary_keys_i32':[],'selector_b_nested_keys':[],'reason':None}
                mapping={'count':0,'mask':None,'max_probe_u8':None,'entries':[]}
                absent={'status':'available','ready':True,'character_id':29829,'carrier_present':False,'associated_full_id':None,'associated_resolved_full_id':None,'associated_used_fallback':None,'associated_cache_440':1,'cached_map_430':copy.deepcopy(mapping),'cached_map_458':copy.deepcopy(mapping),'trait_ids':{'count':None,'values_u32':None},'membership_ids':{'count':None,'values_u64':None},'membership_header_guard_raw':None,'aggregate_properties':{'count':0,'keys_u16':None,'values_q64':None},'aggregate_context_selection':'owned_model_10','aggregate_context_guard_raw':None,'member_multiplier_q64':None,'clamp_lower_q64':-(1<<63),'clamp_upper_q64':(1<<63)-1,'calculated_recipient_q64':0,'reason':None}
                provider={'status':'available','ready':True,'character_id':29829,'provider_present':True,'provider_identity':'held-provider','carrier_present':False,'key_2f8_raw':None,'denominator_5c68ce8_raw':None,'bucket_index_raw':0,'provider_count_1204_raw':0,'provider_array_present':None,'selection':'native_fallback_5d1e0b0','selected_definition_identity':'actual-fallback','selected_magic_raw':0,'admitted':False,'property_identity':None,'property_block':None,'reason':None}
                rows=[('trait_stage_291d460',trait,normalize_trait_stage_291d460),('absent_recipient_inputs',absent,normalize_absent_recipient_inputs),('helper_2922070',helper_2922070(),normalize_helper_2922070),('conference_24b1d00',conference(),normalize_conference_24b1d00),('uncached_recipient_inputs',uncached(),normalize_uncached_recipient_inputs),('provider_bucket_291c5b2',provider,normalize_provider_bucket_291c5b2)]
                pointer=copy.deepcopy(absent);pointer.update(status='partial',ready=False,reason='actual trait operand unavailable',calculated_recipient_q64=None)
                pointer['cached_map_430']={'count':1,'mask':0,'max_probe_u8':1,'entries':[{'bucket_index':0,'hash_u32':None,'probe_u8':1,'key_object':'0xffffffffffffffff','trait_id_u32':None,'value_q64':None}]}
                rows.append(('absent_recipient_inputs',pointer,normalize_absent_recipient_inputs))
                print(json.dumps([{'leaf':leaf,'raw':raw,'expected':normalize(raw,'fixture.'+leaf)} for leaf,raw,normalize in rows],separators=(',',':')))
                """;
        Process child=new ProcessBuilder(required("xar.python"),"-B","-X","utf8","-c",script,required("xar.repository.root")).redirectErrorStream(true).start();
        CompletableFuture<byte[]> read=CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readNBytes(262145);}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}});
        try {
            assertTrue(child.waitFor(30,TimeUnit.SECONDS),"original producer exceeded finite deadline");byte[] output=read.get(5,TimeUnit.SECONDS);
            assertTrue(output.length<=262144,"producer fixture output exceeds finite bound");assertEquals(0,child.exitValue(),new String(output,StandardCharsets.UTF_8));
            List<Fixture> result=new ArrayList<>();for(JsonNode row:JSON.readTree(output))result.add(new Fixture(BattlePersonExternalCodec.Leaf.fromWire(row.get("leaf").textValue()),(ObjectNode)row.get("raw"),row.get("expected")));originalFixtures=List.copyOf(result);return originalFixtures;
        } finally {child.destroyForcibly();}
    }
    private static JsonNode normalize(Fixture fixture,ObjectNode raw) {return BattlePersonExternalCodec.normalize(fixture.leaf(),raw,"fixture."+fixture.leaf().wire());}
    private static JsonNode jsonDomain(JsonNode value) throws IOException {return JSON.readTree(JSON.writeValueAsBytes(value));}
    @Test void realPythonProducerAndNormalizerMatchEveryLeafThroughTheSoleTypedFacadeAndRoundTrip() throws Exception {
        List<Fixture> fixtures=fixtures();assertEquals(7,fixtures.size());
        for(Fixture fixture:fixtures) {
            JsonNode actual=normalize(fixture,fixture.raw());assertEquals(fixture.expected(),jsonDomain(actual),fixture.leaf().wire());
            assertEquals(jsonDomain(actual),jsonDomain(BattlePersonExternalCodec.normalize(fixture.leaf(),jsonDomain(actual),"roundtrip")));
            assertTrue(BattlePersonExternalCodec.normalize(fixture.leaf(),com.fasterxml.jackson.databind.node.NullNode.instance,"null").isNull());
        }
        JsonNode pointer=normalize(fixtures.get(6),fixtures.get(6).raw()).get("cached_map_430").get("entries").get(0).get("key_object");
        assertEquals(new BigInteger("18446744073709551615"),pointer.bigIntegerValue());
    }
    @Test void everyLeafRejectsMissingExtraBooleanAndFloatingIntegerTokens() throws Exception {
        for(Fixture fixture:fixtures()) {
            ObjectNode missing=fixture.raw().deepCopy();missing.remove("character_id");assertThrows(IllegalArgumentException.class,()->normalize(fixture,missing));
            ObjectNode extra=fixture.raw().deepCopy();extra.put("unrecognized_field",1);assertThrows(IllegalArgumentException.class,()->normalize(fixture,extra));
            ObjectNode bool=fixture.raw().deepCopy();bool.put("character_id",true);assertThrows(IllegalArgumentException.class,()->normalize(fixture,bool));
            ObjectNode floating=fixture.raw().deepCopy();floating.put("character_id",29829.0);assertThrows(IllegalArgumentException.class,()->normalize(fixture,floating));
        }
    }
    @Test void actualNativeProbeClampPackAndCalculatedScalarClaimsAreRevalidated() throws Exception {
        List<Fixture> fixtures=fixtures();
        ObjectNode trait=fixtures.get(0).raw().deepCopy();((ObjectNode)trait.get("rows").get(0).get("side")).put("hash_u32",1);assertThrows(IllegalArgumentException.class,()->normalize(fixtures.get(0),trait));
        ObjectNode helper=fixtures.get(2).raw().deepCopy();((ObjectNode)helper.get("rows").get(0)).put("selected_index_raw",0);assertThrows(IllegalArgumentException.class,()->normalize(fixtures.get(2),helper));
        ObjectNode conference=fixtures.get(3).raw().deepCopy();((ObjectNode)conference.get("pack").get("probes").get(0)).put("native_index",0);assertThrows(IllegalArgumentException.class,()->normalize(fixtures.get(3),conference));
        for(int index:List.of(1,4)){Fixture fixture=fixtures.get(index);ObjectNode changed=fixture.raw().deepCopy();changed.put("calculated_recipient_q64",fixture.raw().get("calculated_recipient_q64").longValue()+1);assertThrows(IllegalArgumentException.class,()->normalize(fixture,changed));}
        ObjectNode provider=fixtures.get(5).raw().deepCopy();provider.put("bucket_index_raw",1);assertThrows(IllegalArgumentException.class,()->normalize(fixtures.get(5),provider));
    }
    @Test void signedScratchArithmeticMatchesTheOriginalKernelAcrossNativeEdges() throws Exception {
        String script="import sys,json;sys.path.insert(0,sys.argv[1]+'/ck3_autonomous_player/src');from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import native_scratch_factor_multiplier_12003 as f;rows=[(a,b) for a in (-2147483648,-100000,-1,0,1,100000,2147483647) for b in (-2147483648,-100001,-1,0,1,100001,2147483647)];print(json.dumps([[a,b,f(a,b)] for a,b in rows]))";
        Process child=new ProcessBuilder(required("xar.python"),"-B","-X","utf8","-c",script,required("xar.repository.root")).redirectErrorStream(true).start();
        CompletableFuture<byte[]> read=CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readNBytes(65537);}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}});
        try {assertTrue(child.waitFor(20,TimeUnit.SECONDS));byte[] bytes=read.get(5,TimeUnit.SECONDS);assertTrue(bytes.length<=65536);assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));for(JsonNode row:JSON.readTree(bytes))assertEquals(row.get(2).intValue(),BattleProviderBucketCodec.scratchFactor(row.get(0).intValue(),row.get(1).intValue()));}
        finally {child.destroyForcibly();}
    }
}
