package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Executes the pinned original normalizer/projector/builder; fixtures come from their original compound, never a second Python implementation. */
final class ArmyDetachmentDataProducerParityTest {
    private record Pin(String relative,String sha256) { }
    private static final List<Pin> PINS=List.of(
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py","b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_detachment_data_projection.py","50f55aa6cde3ffd60c52fbdc0fe73c853a4c31429c05e2c423cd1536a69b389a"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_detachment_data_contract.py","acb8a9d0cddef6d7d2fb48b6e83fcd3930c7e6ecfa3c9ff491c81910b498b4fe"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_detachment_data_builder.py","69fc784ebb3dd686419ce4143ebf00f7cf3333b2edaf64c91094dbfe1242fc92"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_active_table_contract.py","f92755b2c8cdee8ac5e9df2806014feccc84b7797aedc23a8d69194dad7d8c52"),
            new Pin("ck3_autonomous_player/tests/test_current_detachment_data_service_compound.py","920e5fa33654bfc59a88d42fa4daae20dc49650fc9ef4385f644226271178631"));
    private static List<JsonNode> cached;
    private static final String SCRIPT="""
            import ast,copy,json,pathlib,sys
            repo=pathlib.Path(sys.argv[1]).resolve()
            sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src'))
            from xar_autoplayer.bridge.army_current_detachment_data_contract import normalize_current_detachment_data_inputs_v1 as normalize
            from xar_autoplayer.bridge.army_current_detachment_data_projection import project_current_detachment_data_prefix as project
            from xar_autoplayer.bridge.army_current_detachment_data_builder import build_same_input_current_detachment_data_prefix as build
            from xar_autoplayer.bridge.war_contract import normalize_army_strengths
            fixture=repo/'ck3_autonomous_player'/'tests'/'test_current_detachment_data_service_compound.py'
            source=ast.parse(fixture.read_text(encoding='utf-8'),filename=str(fixture))
            helpers={'_id','_state','_resolution','_association','_owner','_date','_chunk','_data','_pending','_incoming','_family','_whole','_growth'}
            constants={'_FAMILY','_SERVICE','_DATE','_GREATER','_SMALLER','_SENTINEL','_IMAGE','_VTABLE','_CALLBACK','_REGI','_PROV','_INVALID'}
            # Only original fixture constants/functions are compiled. No MCP/service import or original test class runs here.
            nodes=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in helpers or isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in constants for t in n.targets)]
            namespace={'deepcopy':copy.deepcopy}
            exec(compile(ast.Module(body=nodes,type_ignores=[]),str(fixture),'exec'),namespace)
            whole=namespace['_whole'];growth=namespace['_growth'];family=namespace['_family'];incoming=namespace['_incoming']
            chunk=namespace['_chunk'];data=namespace['_data'];resolution=namespace['_resolution'];DATE=namespace['_DATE']
            def add(name,value,override=None,native_id=-2147483647):
                before=copy.deepcopy(value)
                normalized=normalize(value)
                expected=project(normalized,current_date_storage_raw64=override)
                # Use the actual whole-row producer that precedes the original service builder.
                army={'status':'available' if native_id is not None else 'unavailable','army_id':11,'native_carmy_id':native_id,
                      'scope_role':'player','war_ids':[],'regiment_count':0 if native_id is not None else None,
                      'current_soldiers':0 if native_id is not None else None,'maximum_soldiers':0 if native_id is not None else None,
                      'ai_base_power_raw':0 if native_id is not None else None,'ai_base_power_scale':100000,
                      'unavailable_reason':None if native_id is not None else 'unresolved original CArmy',
                      'current_detachment_data_inputs_v1':normalized}
                actual_row=normalize_army_strengths([army])[0]
                assert actual_row['native_carmy_id']==native_id
                built=build(actual_row) if override is None else None
                assert value==before
                print(json.dumps({'name':name,'input':normalized,'override':override,'native_id':native_id,'expected':expected,'builder':built},separators=(',',':')))
            def changed(name,value,path,replacement,override=None):
                value=copy.deepcopy(value);target=value
                for key in path[:-1]:target=target[key]
                target[path[-1]]=replacement;add(name,value,override)
            add('absent',None);add('whole-ordered-six',whole())
            for native_id in (-2147483648,0,2147483647,None):add('normalized-CArmy-'+str(native_id),None,native_id=native_id)
            for count in (0,1,2,3):add('growth-'+str(count),growth(count))
            for count in (-2147483648,-1,16777217,1431655765,2147483647):
                value=growth(0);pending=value['incoming'][0]['pending'];pending['count_0c_raw_i32']=count;pending['capacity_08_raw_i32']=count
                add('float32-growth-'+str(count),value)
            value=growth(2);value['incoming'][0]['pending']['records'][0]['vtable_identity']='native:1234';add('other-vtable-same-callback',value)
            value=growth(2);value['incoming'][0]['pending']['records'][0]['slot0_target_identity']='native:1234';add('unknown-selected-callback',value)
            changed('zero-old-records-unused-callback',growth(0),['ready_pending_callback_identity'],None)
            for field in ('primary_receiver_identity','canonical_pending_vtable_identity','ready_pending_callback_identity','current_date_storage_raw64'):
                changed('top-null-'+field,growth(1),[field],None)
            for field in ('header_identity','buffer_identity','allocator_identity','capacity_08_raw_i32','count_0c_raw_i32'):
                changed('pending-null-'+field,growth(1),['incoming',0,'pending',field],None)
            for field in ('maximum_00_raw_i32','current_04_raw_i32','owner_08_raw_u32','ordinal_0c_raw_i32','association_10_raw_u32','flag_14_raw_u8','date_1c_raw64'):
                changed('chunk-null-'+field,whole(),['incoming',0,'physical_chunks',0,field],None)
            for field in ('output_date_raw64','unit_identity','source_origin_identity'):
                changed('computed-date-null-'+field,growth(1),['incoming',0,'date_inputs',0,field],None)
            changed('capital-tag-null',whole(),['incoming',0,'date_inputs',0,'capital_origin_magic_85c_raw_u32'],None)
            changed('setter-owner-state-null',whole(),['incoming',0,'owner_inputs',0,'state_138_raw_i32'],None)
            changed('setter-owner-definition-null',whole(),['incoming',0,'owner_inputs',0,'definition_magic_38_raw_u32'],None)
            changed('missing-selected-full-id',whole(),['incoming',0,'data_occurrences',0,'resolution','selected_full_id_u32'],None)
            changed('missing-selected-magic',whole(),['incoming',0,'data_occurrences',0,'magic_14_raw_u32'],None)
            changed('overridden-date-rechecks-current-computation',whole(),['selection_ready'],True,DATE+24)
            changed('selection-incomplete',whole(),['selection_ready'],False)
            changed('roster-incomplete',whole(),['roster_ready'],False)
            changed('candidate-missing-incoming',whole(),['candidate_occurrences',0,'incoming_index'],99)
            for value in (False,None):changed('candidate-admission-'+str(value),whole(),['candidate_occurrences',0,'incoming_valid'],value)
            value=whole();value['incoming'][0]['data_occurrences'][0]['resolution']['ready']=False;add('raw-resolution-unready',value)
            value=family(incoming([],[]));value['incoming'][0]['data_count_raw_i32']=-1;add('negative-count-equal-endpoints',value)
            value=family(incoming([],[]));value['incoming'][0].update(data_count_raw_i32=-1,captured_end_identity='native:1048560');add('negative-count-not-empty',value)
            for present in (False,True,None):
                value=family(incoming([],[]));seed=value['incoming'][0];seed.update(character_full_id_148_u32=29829,character_resolution=resolution(29829,12582912),character_pointer_1b8_present=present)
                add('character-suffix-'+str(present),value)
            changed('character-id-null',family(incoming([],[])),['incoming',0,'character_full_id_148_u32'],None)
            value=family(incoming([],[]));value['incoming']=[];value['candidate_occurrences']=[];add('empty-selected-roster',value)
            # Actual pending stores overwrite the chunk owner/ordinal before their source reloads.
            value=growth(0);value['incoming'][0]['pending'].update(capacity_08_raw_i32=8,buffer_identity='native:2097152');add('pending-destination-aliases-selected-chunk',value)
            # Growth commits an unknown pointer at header0. Later physical reads may not use old snapshot fallback bytes.
            value=growth(0);seed=value['incoming'][0];header=int(seed['pending']['header_identity'][7:]);seed['physical_chunks'].append(chunk(1,header,10,2,0x03000020,0,0x04000002));seed['data_occurrences'].append(data(1,header,0,1));seed.update(data_count_raw_i32=2,captured_end_identity='native:1048608');add('growth-unknown-header-alias',value)
            value=growth(0);seed=value['incoming'][0];seed['pending']=namespace['_pending'](1);seed['pending'].update(capacity_08_raw_i32=8,buffer_identity='native:1048576');seed['physical_chunks'].append(chunk(1,0x204000,10,2,0x03000020,0,0x04000002));seed['data_occurrences'].append(data(1,0x204000,0,1));seed.update(data_count_raw_i32=2,captured_end_identity='native:1048608');add('pending-stores-alias-next-DATA-request',value)
            value=growth(0);seed=value['incoming'][0];seed['data_occurrences'][0]['record_identity']='native:18446744073709551608';seed.update(captured_cursor_identity='native:18446744073709551608',captured_end_identity='native:8');add('u64-cursor-wrap',value)
            value=growth(0);seed=value['incoming'][0];seed['data_occurrences'][0]['resolution']['object_identity']='native:18446744073709551592';seed['physical_chunks']=[];add('physical-address-wraps-null',value)
            value=growth(0);value['incoming'][0]['pending']['header_identity']='native:0009585768';add('native-leading-zero-text-retained',value)
            value=whole();other=copy.deepcopy(value['incoming'][0]);other['native_index']=1;value['incoming'].append(other);value['candidate_occurrences'][1]['incoming_index']=1;add('independent-repeated-incoming-seeds',value)
            changed('empty-unavailable-reason-is-raw-text',whole(),['unavailable_reason'],'')
            for name,path,replacement in [('bool-schema',['schema_version'],True),('float-count',['incoming',0,'data_count_raw_i32'],1.0),('bool-u32',['incoming',0,'physical_chunks',0,'owner_08_raw_u32'],True),('bad-native-pointer',['primary_receiver_identity'],'native:18446744073709551616')]:
                value=whole();target=value
                for key in path[:-1]:target=target[key]
                target[path[-1]]=replacement
                try:normalize(value)
                except (ValueError,TypeError):print(json.dumps({'name':name,'input':value,'error':True},separators=(',',':')))
                else:raise AssertionError('original normalizer accepted invalid '+name)
            """;
    private static void pins(Path root)throws Exception {
        for(Pin pin:PINS){byte[] original=Files.readAllBytes(root.resolve(pin.relative()));assertEquals(pin.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)),pin.relative());}
    }
    private static byte[] bounded(Process process){
        try(var input=process.getInputStream();var bytes=new ByteArrayOutputStream()){
            byte[] buffer=new byte[8192];int count;while((count=input.read(buffer))!=-1){if(bytes.size()+count>8*1024*1024){process.destroyForcibly();throw new IOException("bounded original producer output exceeded");}bytes.write(buffer,0,count);}return bytes.toByteArray();
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private static synchronized List<JsonNode> vectors()throws Exception {
        if(cached!=null)return cached;
        Path root=Path.of(Objects.requireNonNull(System.getProperty("xar.repository.root"),"explicit xar.repository.root required")).toAbsolutePath().normalize();
        String python=Objects.requireNonNull(System.getProperty("xar.python"),"explicit xar.python required; no fallback interpreter");pins(root);
        ProcessBuilder builder=new ProcessBuilder(python,"-I","-B","-c",SCRIPT,root.toString()).redirectErrorStream(true);builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process process=builder.start();var output=CompletableFuture.supplyAsync(()->bounded(process));
        if(!process.waitFor(120,TimeUnit.SECONDS)){process.destroyForcibly();fail("original DATA producer deadline exceeded");}
        byte[] raw=output.get(5,TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(raw,StandardCharsets.UTF_8));pins(root);
        List<JsonNode> result=new ArrayList<>();for(String line:new String(raw,StandardCharsets.UTF_8).lines().toList())if(!line.isBlank())result.add(StrictJson.parse(line.getBytes(StandardCharsets.UTF_8),StrictJson.EXPLICIT_MAX_BYTES));
        assertTrue(result.size()>=55,"full actual branch/alias/growth corpus is mandatory");cached=List.copyOf(result);return cached;
    }
    private static JsonNode normalized(JsonNode value){return StrictJson.parse(StrictJson.canonical(value,StrictJson.EXPLICIT_MAX_BYTES),StrictJson.EXPLICIT_MAX_BYTES);}
    private static ArmyDetachmentDataProjection.Result project(JsonNode vector){return ArmyDetachmentDataProjection.project(ArmyStrengthsDetachment.decodeData(vector.get("input")),vector.hasNonNull("override")?vector.get("override").longValue():null);}
    private static ArmyStrengths.Row row(JsonNode input,boolean omitFamily,Long nativeId){
        boolean available=nativeId!=null;Field<FullId> nativeArmy=available?new Present<>(new FullId(Math.toIntExact(nativeId))):new NullValue<>();
        Field<Integer> aggregate=available?new Present<>(0):new NullValue<>();Field<Long> power=available?new Present<>(0L):new NullValue<>();
        Field<String> reason=available?new NullValue<>():new Present<>("unresolved original CArmy");
        var core=new ArmyStrengths.Core(available?ArmyStrengths.Status.AVAILABLE:ArmyStrengths.Status.UNAVAILABLE,new PublicUnitId(11),nativeArmy,ArmyStrengths.Role.PLAYER,List.of(),aggregate,aggregate,aggregate,power,reason);
        var data=ArmyStrengthsDetachment.decodeData(input);Field<ArmyDetachmentDataInputs> value=data==null?new NullValue<>():new Present<>(data);
        ArmyStrengths.FamilyValue<ArmyDetachmentDataInputs> family=new ArmyStrengths.FamilyValue<>(ArmyStrengthsFamilies.Key.CURRENT_DETACHMENT_DATA_INPUTS_V1,ArmyDetachmentDataInputs.class,value,new RawJson(StrictJson.canonical(input,StrictJson.EXPLICIT_MAX_BYTES)));
        return new ArmyStrengths.Row(core,List.of(),new Missing<>(),new Missing<>(),omitFamily?List.of():List.of(family));
    }
    @Test void completeOriginalProducerAndBuilderMatchForAllOrderedSeedsAndAliasingBranches()throws Exception {
        for(JsonNode vector:vectors()){
            String name=vector.get("name").textValue();if(vector.path("error").asBoolean()){assertThrows(IllegalArgumentException.class,()->ArmyStrengthsDetachment.decodeData(vector.get("input")),name);continue;}
            assertEquals(vector.get("input"),normalized(ArmyStrengthsDetachment.encodeData(ArmyStrengthsDetachment.decodeData(vector.get("input")))),name+" complete input contract roundtrip");
            var result=project(vector);assertEquals(vector.get("expected"),normalized(ArmyDetachmentDataProjection.nativeJson(result)),name);
            Long nativeId=vector.hasNonNull("native_id")?vector.get("native_id").longValue():null;
            if(!vector.hasNonNull("override")){
                assertEquals(vector.get("builder"),normalized(ArmyDetachmentDataProjection.nativeJson(new ArmyDetachmentDataProjection.ArmyResult(11,nativeId,result))),name+" actual normalized-row builder");
                assertEquals(vector.get("builder"),normalized(ArmyDetachmentDataProjection.nativeJson(ArmyDetachmentDataProjection.build(row(vector.get("input"),false,nativeId)))),name+" actual typed Row builder");
                if(vector.get("input").isNull())assertEquals(vector.get("builder"),normalized(ArmyDetachmentDataProjection.nativeJson(ArmyDetachmentDataProjection.build(row(vector.get("input"),true,nativeId)))),name+" missing DATA family builder");
            }
            assertEquals(result,project(vector),name+" deterministic independent seed replay");
        }
    }
    @Test void publicV2UsesExplicit64BitWidthsWithoutChangingNativeNumbersOrFourByteEffects()throws Exception {
        JsonNode vector=vectors().stream().filter(row->row.path("name").asText().equals("growth-2")).findFirst().orElseThrow();var result=project(vector);
        JsonNode nativeJson=ArmyDetachmentDataProjection.nativeJson(result),publicJson=ArmyDetachmentDataProjection.publicV2Json(result);
        JsonNode before=nativeJson.get("incoming").get(0),after=publicJson.get("incoming").get(0);
        assertTrue(before.get("conditional_entry_date_raw64").isIntegralNumber());assertTrue(after.get("conditional_entry_date_raw64").isTextual());
        assertEquals(before.get("conditional_entry_date_raw64").bigIntegerValue().toString(),after.get("conditional_entry_date_raw64").textValue());
        assertEquals(before.get("conditional_pending").get("events").get(0).get("allocation_bytes").bigIntegerValue().toString(),after.get("conditional_pending").get("events").get(0).get("allocation_bytes").textValue());
        for(int index=0;index<before.get("physical_chunks").size();index++){
            JsonNode old=before.get("physical_chunks").get(index).get("date_1c_raw64"),next=after.get("physical_chunks").get(index).get("date_1c_raw64");
            if(old.isNull())assertTrue(next.isNull());else{assertTrue(next.isTextual());assertEquals(old.bigIntegerValue().toString(),next.textValue());}
        }
        for(int index=0;index<before.get("effects").size();index++){
            JsonNode old=before.get("effects").get(index),next=after.get("effects").get(index);assertEquals(old.get("address_identity"),next.get("address_identity"));
            for(String field:List.of("before_raw","after_raw")){
                if(old.get(field).isNull())assertTrue(next.get(field).isNull());
                else if(old.get("size").intValue()==8){assertTrue(next.get(field).isTextual());assertEquals(old.get(field).bigIntegerValue().toString(),next.get(field).textValue());}
                else assertEquals(old.get(field).bigIntegerValue(),next.get(field).bigIntegerValue());
            }
        }
        assertFalse(publicJson.get("actual_effects").booleanValue());assertEquals(0,publicJson.get("native_writes_executed").intValue());
    }
}
