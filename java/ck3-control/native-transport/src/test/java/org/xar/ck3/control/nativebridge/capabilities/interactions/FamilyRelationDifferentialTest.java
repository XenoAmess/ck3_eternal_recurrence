package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyCurrentRelationTest.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Runs the unchanged original Python producers in another process; missing CI inputs fail, never skip. */
final class FamilyRelationDifferentialTest {
    @TempDir Path directory;
    private static final String ORIGINAL="""
        import json,sys
        from copy import deepcopy
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch
        root=Path(sys.argv[1]); sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
        data=json.loads(Path(sys.argv[2]).read_text('utf-8'))
        from xar_autoplayer.bridge import current_first_heir_relationship_private_transport as transport
        from xar_autoplayer.bridge.guardian_factory_create_inputs_contract_v1 import validate_guardian_factory_create_inputs_v1,project_guardian_family_decision_inputs_v1
        from xar_autoplayer.bridge.conception_natural_observation_contract_12004 import normalize_conception_natural_observations_12004
        from xar_autoplayer.simulation.conception_natural_observation_12004 import project_conception_natural_observations_12004
        if data['kind']=='natural':
            journal=normalize_conception_natural_observations_12004(data['journal'],expected_first_character_id=38822,expected_second_character_id=38718)
            print(json.dumps({'normalized':journal,'projected':project_conception_natural_observations_12004(journal)},separators=(',',':')))
        else:
            frame=data['frame'];packet=data['packet'];sidecar=Path(data['sidecar_path'])
            sidecar.unlink(missing_ok=True)
            class Driver:
                allow_private_current_first_heir_relationship_query=True
                def __init__(self): self.endpoint=self;self.state=self;self.sent=[];self.reads=0;self.roots=0
                def take_snapshot(self): self.reads+=1;return deepcopy(frame)
                def _execute_campaign_root_context_v1_query(self,*,expected_revision):
                    assert expected_revision==frame['revision'];self.roots+=1
                    return {'status':'available','query_sequence':11,'held_title_partition':[{'primary':True,'first_heir_character_id':38822}]}
                def send(self,request):
                    assert not self.sent and request['step']==transport.STEP and request['expected_revision']==frame['native_revision']
                    assert request['request_id']==packet['request_id'] and 'candidate_character_id' not in request and 'heir_character_id' not in request
                    assert Path(request['guardian_factory_sidecar_path'])==sidecar
                    self.sent.append(deepcopy(request));sidecar.write_bytes(data['sidecar_utf8'].encode('utf-8'))
                def wait_for_command_result(self,request_id,timeout_seconds):
                    assert request_id==packet['request_id'];return deepcopy(packet)
            driver=Driver()
            with patch.object(transport.uuid,'uuid4',return_value=SimpleNamespace(hex=packet['request_id'][len('family-relation-'):])):
                family=transport.query_current_first_heir_relationship_private_v1(driver,expected_native_revision=frame['native_revision'],guardian_factory_sidecar_path=sidecar,include_relation_materials=True)
            owned=validate_guardian_factory_create_inputs_v1(json.loads(data['sidecar_utf8']),command_result=packet,snapshot=frame,family_result=family)
            decision=project_guardian_family_decision_inputs_v1(owned,family_result=family)
            assert len(driver.sent)==1 and driver.reads==3 and driver.roots==1
            print(json.dumps({'family':family,'guardian_decision':decision,'native_submissions':0,'software_query_responses':1},separators=(',',':')))
        """;
    private JsonNode original(ObjectNode input)throws Exception{
        FamilyRelationOriginalPins.verify();Path request=directory.resolve("compat-input-"+java.util.UUID.randomUUID()+".json"),output=request.resolveSibling(request.getFileName()+".out"),error=request.resolveSibling(request.getFileName()+".err");Files.write(request,raw(input).bytes());ProcessBuilder builder=new ProcessBuilder(FamilyRelationOriginalPins.required("xar.python"),"-B","-c",ORIGINAL,FamilyRelationOriginalPins.repository().toString(),request.toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.redirectOutput(output.toFile());builder.redirectError(error.toFile());Process process=builder.start();if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new AssertionError("original relationship producer timeout");}assertEquals(0,process.exitValue(),()->{try{return Files.readString(error).substring(0,(int)Math.min(Files.size(error),8192));}catch(Exception failed){return failed.toString();}});assertTrue(Files.size(output)<=4*1024*1024,"bounded independent original producer output required");byte[] bytes=Files.readAllBytes(output);FamilyRelationOriginalPins.verify();return NativeWire.parse(bytes);
    }
    private static ObjectNode snapshot(){ObjectNode frame=InteractionJson.F.objectNode().put("snapshot_id","native:3").put("revision",4).put("native_revision",REV).put("date_raw",DATE).put("paused",true).put("map_ready",true).put("episode_run_id","fixture-relation");frame.putObject("played_character").put("character_id",ACTOR).put("alive",true);frame.putObject("diagnostics").put("bridge_pid",59077).put("connection_generation",2).putObject("hello").put("expected_ck3_version",InteractionModels.Build.CROZIER4.version()).put("expected_ck3_sha256",InteractionModels.Build.CROZIER4.sha256());return frame;}
    @Test void fullQueryDescendantsSignedFullChildEducationProviderAndReproductiveUnknownMatchOriginal()throws Exception{
        String id="family-relation-diff-current";ObjectNode result=relation();result.set(FamilyRelationDescendants.LEAF,descendants());result.set(FamilyRelationReproductive.LEAF,reproductive());ObjectNode material=completeMaterials(id);var fixture=new FamilyCurrentRelationTest();fixture.directory=directory;var f=fixture.fixture(id,result,material);
        ObjectNode input=InteractionJson.F.objectNode().put("kind","query").put("sidecar_path",f.sidecar().toString()).put("sidecar_utf8",new String(raw(material).bytes(),StandardCharsets.UTF_8));input.set("frame",snapshot());input.set("packet",InteractionJson.parse(f.receipt().original().originalFrame()));JsonNode python=original(input);OpportunityJson.Obj observed=f.queries().contract().decode(f.receipt());ObjectNode javaBody=((ObjectNode)OpportunityJson.toNode(observed)).deepCopy();javaBody.remove("guardian_factory_materials_v2");assertEquals(python.get("family"),javaBody);
        var typed=f.queries().decodeReceipt(f.receipt());assertEquals(python.get("guardian_decision"),OpportunityJson.toNode(FamilyRelationGuardianMaterials.decision(typed.materials(),typed.descendants(),REV,HEIR)));var child=typed.descendants().orElseThrow().children().getFirst();assertEquals(CHILD,child.fullId());assertTrue(child.signedCharacterId()<0);assertEquals(2,child.occurrenceIndices().size());JsonNode decision=javaBody.get("family_generation_education_decision_inputs_v1");assertTrue(decision.get("education_rows").get(0).get("current_focus").get("known_null").booleanValue());assertTrue(decision.get("education_rows").get(0).get("current_court_owner").get("known_null").booleanValue());assertEquals(5,decision.get("education_rows").get(0).get("stock_skill_options").size());assertFalse(javaBody.get(FamilyRelationEducationProvider.LEAF).get("m6_inputs_complete").booleanValue());assertEquals(observed,f.queries().contract().replay(f.receipt()));
        var publicBody=FamilyCurrentRelationPublic.encode(typed);assertEquals(observed,FamilyCurrentRelationPublic.decode(publicBody,typed));JsonNode publicNode=OpportunityJson.toNode(publicBody);assertEquals("18446744073709551615",publicNode.get("guardian_factory_materials_v2").get("observation").get("pump_epoch").textValue());assertTrue(publicNode.get(FamilyRelationDescendants.LEAF).get("child_inputs").get("rows").get(0).get("character_id").isIntegralNumber());assertEquals("9223372036854775809",publicNode.get(FamilyRelationDescendants.LEAF).get("child_inputs").get("rows").get(0).get("court_owner_source").get("child_address").textValue());assertEquals(f.receipt().request().arguments(),FamilyCurrentRelationPublic.decodeArguments(FamilyCurrentRelationPublic.arguments(f.receipt(),typed),f.receipt(),typed));ObjectNode rounded=((ObjectNode)publicNode).deepCopy();((ObjectNode)rounded.get("guardian_factory_materials_v2").get("observation")).put("pump_epoch",18446744073709552000.0);assertThrows(IllegalArgumentException.class,()->FamilyCurrentRelationPublic.decode(app(rounded),typed));ObjectNode padded=((ObjectNode)publicNode).deepCopy();padded.put("native_revision","03");assertThrows(IllegalArgumentException.class,()->FamilyCurrentRelationPublic.decode(app(padded),typed));
    }
    @Test void exactNaturalOriginalJournalNormalizationProjectionAndRaw64StringsMatchUnchangedConsumer()throws Exception{
        FamilyRelationOriginalPins.verify();Path path=FamilyRelationOriginalPins.repository().resolve("ck3_autonomous_player/native_bridge/tests/fixtures/conception_pair_passive_12004_joined_journal.json");JsonNode journal=NativeWire.parse(Files.readAllBytes(path));ObjectNode input=InteractionJson.F.objectNode().put("kind","natural");input.set("journal",journal);JsonNode python=original(input);var value=FamilyConceptionNatural.decode(journal,BigInteger.valueOf(HEIR),BigInteger.valueOf(38718));assertEquals(python.get("normalized"),OpportunityJson.toNode(value.orElseThrow().original()));assertEquals(python.get("projected"),OpportunityJson.toNode(FamilyConceptionNatural.project(value)));JsonNode projection=OpportunityJson.toNode(FamilyConceptionNatural.project(value));assertFalse(projection.get("records").get(0).get("current_natural_observation_available").booleanValue());assertTrue(projection.get("records").get(0).get("accepted_causal").isNull());assertEquals("11868043649729791745",projection.get("records").get(0).get("original_rax_bits").textValue());
        ObjectNode number=((ObjectNode)journal).deepCopy();((ObjectNode)number.get("events").get(0)).put("original_rax_bits",new BigInteger("11868043649729791745"));assertThrows(IllegalArgumentException.class,()->FamilyConceptionNatural.decode(number,BigInteger.valueOf(HEIR),BigInteger.valueOf(38718)));ObjectNode mismatch=((ObjectNode)journal).deepCopy();((ObjectNode)mismatch.get("events").get(0)).put("original_al",0);assertThrows(IllegalArgumentException.class,()->FamilyConceptionNatural.decode(mismatch,BigInteger.valueOf(HEIR),BigInteger.valueOf(38718)));assertThrows(IllegalArgumentException.class,()->FamilyConceptionNatural.decode(journal,BigInteger.valueOf(HEIR+1),BigInteger.valueOf(38718)));
    }
    @Test void duplicateChildOccurrenceClassificationAndIndependentEducationNullsCannotBeInvented(){
        ObjectNode d=descendants();var typed=FamilyRelationDescendants.decode(d,ACTOR,HEIR,REV,DATE).orElseThrow();assertEquals(1,typed.children().size());assertEquals(2,typed.occurrences().size());ObjectNode family=relation();family.set(FamilyRelationDescendants.LEAF,d);family.put("exact_ck3_build",InteractionModels.Build.CROZIER4.version()).put("exe_sha256",InteractionModels.Build.CROZIER4.sha256());ObjectNode p=educationProvider("fixture-leaf");assertTrue(FamilyRelationEducationProvider.decode(p,family,true,"fixture-leaf",REV,ACTOR,HEIR,DATE).isPresent());
        ObjectNode duplicate=d.deepCopy();((ObjectNode)duplicate.get("rows").get(1)).put("alive",false);family.set(FamilyRelationDescendants.LEAF,duplicate);assertThrows(IllegalArgumentException.class,()->FamilyRelationEducationProvider.decode(p,family,true,"fixture-leaf",REV,ACTOR,HEIR,DATE));family.set(FamilyRelationDescendants.LEAF,d);ObjectNode invented=p.deepCopy();((ObjectNode)invented.get("rows").get(0)).put("guardian_full_id",ACTOR);assertThrows(IllegalArgumentException.class,()->FamilyRelationEducationProvider.decode(invented,family,true,"fixture-leaf",REV,ACTOR,HEIR,DATE));ObjectNode nullLost=p.deepCopy();((ObjectNode)nullLost.get("rows").get(0)).remove("education_progress");assertThrows(IllegalArgumentException.class,()->FamilyRelationEducationProvider.decode(nullLost,family,true,"fixture-leaf",REV,ACTOR,HEIR,DATE));
        ObjectNode bool=d.deepCopy();((ObjectNode)bool.get("rows").get(0)).put("raw_character_id",true);assertThrows(IllegalArgumentException.class,()->FamilyRelationDescendants.decode(bool,ACTOR,HEIR,REV,DATE));ObjectNode focus=d.deepCopy();((ObjectNode)focus.get("child_inputs").get("rows").get(0).get("native_focus")).put("key","invented_default");assertThrows(IllegalArgumentException.class,()->FamilyRelationDescendants.decode(focus,ACTOR,HEIR,REV,DATE));
    }
}
