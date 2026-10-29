package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsRosterContract.*;

/** Mandatory original-producer differential. This source has not itself been executed by its author. */
final class ArmyStrengthsRosterContractTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    private static JsonNode corpus;
    private static final String PRODUCER="""
import copy,json,sys
from dataclasses import asdict
from pathlib import Path
root=Path(sys.argv[1])
sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'/'unit'))
import daily_assault_roster_admission_fixture as f
from xar_autoplayer.bridge.army_daily_assault_roster_admission_contract import normalize_current_daily_assault_roster_admission_v1 as normalize
from xar_autoplayer.simulation.army_daily_assault_roster_admission_12003 import project_current_daily_assault_roster_admission_12003 as project, daily_assault_roster_admission_requests_12003 as requests
cases=[]
def emit(name,raw):
    normalized=normalize(raw)
    p=project(normalized)
    cases.append(dict(name=name,raw=raw,normalized=normalized,projection=p,requests=[asdict(r) for r in requests(p,prefix_only=True)]))
def state(dst,ready,reason):
    dst.update(status='available' if ready else 'partial',ready=ready,unavailable_reason='' if ready else reason or 'source_inputs_incomplete')
def close(raw):
    p=project(raw)
    for key in ('raw_roster_references_ready','original_army_selections_ready','army_appends_ready','arrg_appends_ready','conditional_admission_ready'):
        raw[key]=p[key]
    state(raw,p['ready'],p['unavailable_reason'])
    for observed,row in zip(raw['occurrences'],p['occurrences']):
        state(observed,row['ready'],row['unavailable_reason'])
        for key in ('removal_contains_selected_army','army_append_ready','army_append','army_append_siege_full_id_u32','army_append_full_id_u32','arrg_append_ready','arrg_append_full_ids_u32'):
            observed[key]=row[key]
        gate=observed['gate']; dg=row['gate']
        state(gate,dg['ready'],dg['unavailable_reason']);gate['verdict']=dg['verdict']
        relation=gate['relation_lookup']; dr=dg['relation_lookup']
        state(relation,dr['ready'],dr['unavailable_reason'])
        for key in ('candidate_slot_index_i64','selection'):
            relation[key]=dr[key]
        pending=observed['pending_selection'];dp=row['pending_selection']
        state(pending,dp['ready'],dp['unavailable_reason'])
        for key in ('selected_physical_slot_i64','selected_is_end_marker','selected_control_raw_u8'):
            pending[key]=dp[key]
        observed['arrg_occurrences']=[]
        for a in row['arrg_occurrences']:
            dst=dict(a);state(dst,a['ready'],a['unavailable_reason']);observed['arrg_occurrences'].append(dst)
    return raw
for name,producer in (
    ('whole',f.roster_admission_source),('zero',f.zero_roster_admission_source),
    ('fallback_metadata_unread',f.fallback_war_metadata_unavailable_source),
    ('partial_pending',f.partial_pending_admission_source),
    ('matched_suppression_unread_tail',f.matched_suppression_with_unread_tail_source),
    ('reused_queue_pointer_unread',f.reused_queue_pointer_metadata_unavailable_source),
    ('partial_raw_roster',f.partial_raw_roster_source)):
    emit(name,producer())
emit('null',None)
for field,value in (
    ('original_unit_kind_raw_u32',1),('selected_province_comparison_identity_raw_u32',999),
    ('original_unit_counter_170_raw_i32',1),('province_siege_id_raw_u32',0xFFFFFFFF),
    ('province_counter_850_raw_i32',0),('associated_army_flag_1d4_raw_u8',1),
    ('associated_army_flag_1ec_raw_u8',1),('province_character_full_id_raw_u32',101),
    ('selected_war_ended_358_raw_u8',1),('selected_war_ended_358_raw_u8',None)):
    raw=f.roster_admission_source();raw['occurrences'][0]['gate'][field]=value
    emit('gate_'+field+'_'+str(value),close(raw))
for classification in (-2147483648,-1,0,1,2147483647):
    raw=f.roster_admission_source();g=raw['occurrences'][0]['gate']
    g.update(province_character_id_73c_raw_u32=0xFFFFFFFF,province_character_resolution=f.operand_resolution(),
        native_2c099f0_character_identity=g['associated_character_resolution']['object_identity'],
        native_2c099f0_province_identity=g['original_unit_province_identity'],
        native_2c099f0_third_argument_is_null=True,native_2c099f0_returned=True,
        native_2c099f0_classification_raw_i32=classification)
    emit('classifier_'+str(classification),close(raw))
for field,value in (
    ('native_2c099f0_character_identity','native:wrong'),
    ('native_2c099f0_province_identity','native:wrong'),
    ('native_2c099f0_third_argument_is_null',False),
    ('native_2c099f0_returned',False),
    ('native_2c099f0_classification_raw_i32',None)):
    raw=f.roster_admission_source();g=raw['occurrences'][0]['gate']
    g.update(province_character_id_73c_raw_u32=0xFFFFFFFF,province_character_resolution=f.operand_resolution(),
        native_2c099f0_character_identity=g['associated_character_resolution']['object_identity'],
        native_2c099f0_province_identity=g['original_unit_province_identity'],
        native_2c099f0_third_argument_is_null=True,native_2c099f0_returned=True,
        native_2c099f0_classification_raw_i32=0)
    g[field]=value;emit('classifier_missing_'+field,close(raw))
for count in (None,-1,0):
    raw=f.roster_admission_source();g=raw['occurrences'][0]['gate'];r=g['relation_lookup']
    r.update(table_count_raw_i32=count,default_relationship_present=True,
        default_relationship_identity=r['selected_relationship_identity'])
    emit('relation_count_'+str(count),close(raw))
raw=f.roster_admission_source();r=raw['occurrences'][0]['gate']['relation_lookup']
r.update(component_present=False,default_relationship_present=True,default_relationship_identity=r['selected_relationship_identity'])
emit('relation_native_fallback',close(raw))
for mask in (-2147483648,-1,0,7,2147483647):
    for tail in (0,255):
        raw=f.roster_admission_source();p=raw['occurrences'][0]['pending_selection']
        signed=f.fnv(11);signed=signed-0x100000000 if signed&0x80000000 else signed
        home=signed&mask
        p.update(mask_raw_i32=mask,tail_distance_raw_u8=tail,selected_control_raw_u8=255,
                 probes=[dict(native_index=0,physical_slot_i64=home,distance_raw_u8=1,
                              control_raw_u8=0,key_raw_full_id_u32=None)])
        emit('pending_end_'+str(mask)+'_'+str(tail),close(raw))
for field,value in (('entries_present',False),('mask_raw_i32',None),('selected_control_raw_u8',None)):
    raw=f.roster_admission_source();raw['occurrences'][0]['pending_selection'][field]=value
    emit('pending_missing_'+field,close(raw))
raw=f.roster_admission_source();raw['removal_queue']=f.references([11,None]);emit('removal_early_match',close(raw))
raw=f.roster_admission_source()
raw['occurrences'].pop(2);refs=raw['original_roster'];refs['occurrences'].pop(2)
refs['observed_occurrence_count']=4;refs['references_ready']=False;state(refs,False,'gap')
emit('raw_roster_gap',close(raw))
raw=f.zero_roster_admission_source();r=raw['original_roster'];r.update(count_raw_i32=-1,references_ready=False);state(r,False,'negative')
emit('negative_roster_count',close(raw))
print(json.dumps(cases,separators=(',',':')))
""";
    private static synchronized JsonNode corpus() throws Exception {
        if(corpus!=null)return corpus;
        String python=System.getProperty("xar.python");
        String repository=System.getProperty("xar.repository.root");
        assertNotNull(python,"Required -Dxar.python actual interpreter; differential must not be skipped");
        assertNotNull(repository,"Required -Dxar.repository.root");
        Path root=Path.of(repository).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_roster_admission_contract.py")));
        assertSource(root,"ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_roster_admission_contract.py","a9c8ad14f0b528e2f0da49104e6dfc29afd0407ca6155df1cb701fb21bd202b5");
        assertSource(root,"ck3_autonomous_player/src/xar_autoplayer/simulation/army_daily_assault_roster_admission_12003.py","b0c5397de2b03f0e0826b01c48d71de2120cba814080ddc328dd2484cdbcf0f2");
        assertSource(root,"ck3_autonomous_player/tests/unit/daily_assault_roster_admission_fixture.py","112a279acfdd73d60cb2ec4891293237a81e092f71dad3d506fb2571d12d1197");
        assertSource(root,"ck3_autonomous_player/src/xar_autoplayer/simulation/army_daily_assault_placement_12003.py","9d4c1774a5c3e63247bb0bf10a9f412530821d225b57f359859bc078017f91f9");
        Path scratch=Files.createTempDirectory("roster-original-producer-"),out=scratch.resolve("out.json"),err=scratch.resolve("err.txt");
        Process child=null;
        try {
            child=new ProcessBuilder(python,"-c",PRODUCER,root.toString()).redirectOutput(out.toFile()).redirectError(err.toFile()).start();
            assertTrue(child.waitFor(60,TimeUnit.SECONDS),"Original producer timed out");
            assertEquals(0,child.exitValue(),()->readDiagnostic(err));
            assertTrue(Files.size(out)>0 && Files.size(out)<=16*1024*1024,"bounded original producer corpus required");
            corpus=JSON.readTree(Files.readAllBytes(out));
            assertTrue(corpus.isArray() && corpus.size()>=40,"full producer corpus required");
            return corpus;
        } finally {
            if(child!=null && child.isAlive()){child.destroyForcibly();child.waitFor(5,TimeUnit.SECONDS);}
            Files.deleteIfExists(out);Files.deleteIfExists(err);Files.deleteIfExists(scratch);
        }
    }
    private static void assertSource(Path root,String relative,String expected) throws Exception {
        byte[] bytes=Files.readAllBytes(root.resolve(relative));
        String actual=HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));
        assertEquals(expected,actual,"Original producer source changed: "+relative);
    }
    private static String readDiagnostic(Path path) {
        try {byte[] bytes=Files.readAllBytes(path);return new String(bytes,0,Math.min(bytes.length,8192),java.nio.charset.StandardCharsets.UTF_8);}
        catch(Exception unavailable){return unavailable.toString();}
    }
    private static JsonNode domain(JsonNode n) {
        if(n.isIntegralNumber())return BigIntegerNode.valueOf(n.bigIntegerValue());
        if(n.isArray()){ArrayNode a=JSON.createArrayNode();for(JsonNode item:n)a.add(domain(item));return a;}
        if(n.isObject()){ObjectNode o=JSON.createObjectNode();n.properties().iterator().forEachRemaining(e->o.set(e.getKey(),domain(e.getValue())));return o;}
        return n;
    }
    private static ObjectNode first() throws Exception {
        return (ObjectNode)corpus().get(0).get("normalized").deepCopy();
    }
    @Test void originalProducerToStrictTypedCodecAndCompleteDerivation() throws Exception {
        for(JsonNode fixture:corpus()){
            String name=fixture.get("name").textValue();
            JsonNode expected=fixture.get("normalized");
            ObjectNode normalized=normalizeRoster(fixture.get("raw"));
            assertEquals(domain(expected),domain(normalized==null?NullNode.instance:normalized),name+" normalized");
            Root typed=normalized==null?null:decodeRoot(normalized);
            JsonNode actual=encodeProjection(project(typed,11));
            assertEquals(domain(fixture.get("projection")),domain(actual),name+" full projection");
            if(typed!=null){
                assertEquals(typed,decodeRoot(JSON.readTree(encodeRoot(typed).toString())),name+" record roundtrip");
                assertEquals(domain(actual),domain(encodeProjection(project(typed,987))),name+" whole original roster survives changed query scope");
                Projection p=project(typed,11);
                if(!p.ready())assertThrows(IllegalArgumentException.class,()->requests(p,false),name);
                assertEquals(p.request_prefix(),requests(p,true));
                ArrayNode actualRequests=JSON.createArrayNode();
                for(PlacementRequest request:requests(p,true))actualRequests.add(encodeRequest(request));
                assertEquals(domain(fixture.get("requests")),domain(actualRequests),name+" original request producer to typed consumer");
            }
        }
    }
    @Test void everySharedClosedShapeRejectsMissingExtraAndWrongJsonTypes() throws Exception {
        ObjectNode root=first();JsonNode row=root.path("occurrences").get(0),gate=row.path("gate");
        Map<String,JsonNode> examples=Map.ofEntries(
            Map.entry("ArmyCurrentDailyAssaultRosterAdmissionV1",root),
            Map.entry("OperandResolution",row.path("original_army_resolution")),
            Map.entry("RawReferenceOccurrence",root.path("original_roster").path("occurrences").get(0)),
            Map.entry("RawReferences",root.path("original_roster")),Map.entry("RelationProbe",gate.path("relation_lookup").path("probes").get(0)),
            Map.entry("RelationLookup",gate.path("relation_lookup")),Map.entry("AdmissionGate",gate),
            Map.entry("PendingProbe",row.path("pending_selection").path("probes").get(0)),
            Map.entry("PendingSelection",row.path("pending_selection")),Map.entry("ArRgAdmissionOccurrence",row.path("arrg_occurrences").get(0)),
            Map.entry("RosterAdmissionOccurrence",row));
        for(var entry:examples.entrySet()){
            String kind=entry.getKey();ObjectNode raw=(ObjectNode)entry.getValue();
            validateType(raw,kind);String first=raw.fieldNames().next();
            ObjectNode missing=raw.deepCopy();missing.remove(first);assertThrows(IllegalArgumentException.class,()->validateType(missing,kind),kind+" missing");
            ObjectNode extra=raw.deepCopy();extra.put("unknown",1);assertThrows(IllegalArgumentException.class,()->validateType(extra,kind),kind+" extra");
            for(var fields=raw.properties().iterator();fields.hasNext();){
                var field=fields.next();
                if(field.getValue().isIntegralNumber()){
                    ObjectNode fraction=raw.deepCopy();fraction.put(field.getKey(),1.0);
                    assertThrows(IllegalArgumentException.class,()->validateType(fraction,kind),kind+" "+field.getKey()+" floating");
                    ObjectNode bool=raw.deepCopy();bool.put(field.getKey(),true);
                    assertThrows(IllegalArgumentException.class,()->validateType(bool,kind),kind+" "+field.getKey()+" bool integer");
                }
            }
        }
    }
    @Test void shapeValidationDoesNotGrantSemanticReadinessAndDeclarationsCannotLie() throws Exception {
        ObjectNode raw=first();ObjectNode gate=(ObjectNode)raw.path("occurrences").get(0).path("gate");
        gate.put("verdict",false);validateType(raw,"ArmyCurrentDailyAssaultRosterAdmissionV1");
        Root typed=decodeRoot(raw);
        assertTrue(project(typed,11).occurrences().get(0).gate().verdict());
        assertThrows(IllegalArgumentException.class,()->normalizeRoster(raw));
        ObjectNode wrong=first();ObjectNode resolution=(ObjectNode)wrong.path("occurrences").get(0).path("original_army_resolution");
        resolution.put("requested_full_id_u32",12);
        assertThrows(IllegalArgumentException.class,()->normalizeRoster(wrong));
        ObjectNode probes=first();ObjectNode probe=(ObjectNode)probes.path("occurrences").get(0).path("gate").path("relation_lookup").path("probes").get(0);
        probe.put("slot_index_i64",0);
        assertThrows(IllegalArgumentException.class,()->normalizeRoster(probes));
        ObjectNode pending=first();ObjectNode p=(ObjectNode)pending.path("occurrences").get(0).path("pending_selection").path("probes").get(0);
        p.put("distance_raw_u8",2);
        assertThrows(IllegalArgumentException.class,()->normalizeRoster(pending));
    }
    @Test void legacyExtensionIsWholeOrAbsentAndOriginalsRemainImmutable() throws Exception {
        ObjectNode raw=first();ObjectNode gate=(ObjectNode)raw.path("occurrences").get(0).path("gate");
        List<String> extension=List.of("native_2c099f0_character_identity","native_2c099f0_province_identity","native_2c099f0_third_argument_is_null","native_2c099f0_returned","native_2c099f0_classification_raw_i32");
        for(String name:extension)gate.remove(name);
        ObjectNode original=raw.deepCopy();ObjectNode normalized=normalizeRoster(raw);
        assertEquals(original,raw,"normalization cannot mutate original producer");
        Root typed=decodeRoot(normalized);
        assertThrows(UnsupportedOperationException.class,()->typed.occurrences().clear());
        assertThrows(UnsupportedOperationException.class,()->typed.original_roster().occurrences().clear());
        encodeRoot(typed).remove("occurrences");assertEquals(5,typed.occurrences().size());
        gate.put("native_2c099f0_returned",false);
        assertThrows(IllegalArgumentException.class,()->normalizeRoster(raw),"partial classifier extension must not be defaulted");
        ObjectNode id=first();ObjectNode r=(ObjectNode)id.path("occurrences").get(0).path("original_army_resolution");
        r.put("requested_full_id_u32",4294967296L);
        assertThrows(IllegalArgumentException.class,()->decodeRoot(id));
        assertNull(normalizeRoster(NullNode.instance));
        assertThrows(IllegalArgumentException.class,()->validateType(JSON.createObjectNode(),"RawReferences"));
    }
}

