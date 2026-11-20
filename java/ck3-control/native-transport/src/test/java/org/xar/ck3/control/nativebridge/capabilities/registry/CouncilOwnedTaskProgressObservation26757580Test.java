package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import java.util.zip.ZipInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.CouncilOwnedTaskProgressObservation26757580.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.CouncilOwnedTaskObservation26757580.Frame;

/** Actual Cpp NoGame bytes. Malformed/signed-edge mutations are DATA tests, not new Native/live/evaluator evidence. */
final class CouncilOwnedTaskProgressObservation26757580Test {
    private static final String ROOT="originals-ON/0-percentage-raw/";
    private static final Map<String,byte[]> CORPUS=corpus();
    private static String sha(byte[] b)throws Exception{return java.util.HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b));}
    private static Map<String,byte[]> corpus(){try{
        byte[] archive;String explicit=System.getProperty("xar.native.council70.corpus");
        if(explicit!=null){Path p=Path.of(explicit);if(!p.isAbsolute())throw new IOException("absolute explicit corpus required");archive=Files.readAllBytes(p);}
        else try(var input=CouncilOwnedTaskProgressObservation26757580Test.class.getResourceAsStream("/newnative/council70/council70-actual.zip")){
            if(input==null)throw new IOException("real Cpp corpus missing");archive=input.readNBytes(48213);}
        assertEquals(48212,archive.length);assertEquals("6f67eff18532715b7c1e415c32c0f5afc3420e4394d9e8aa34e5cad6da0f1a3e",sha(archive));
        var entries=new LinkedHashMap<String,byte[]>();try(var z=new ZipInputStream(new ByteArrayInputStream(archive))){
            for(var e=z.getNextEntry();e!=null;e=z.getNextEntry()){
                byte[] b=z.readNBytes(262145);if(e.isDirectory()||b.length>262144||entries.putIfAbsent(e.getName(),b)!=null)throw new IOException("bad ZIP entry");}}
        assertEquals(69,entries.size());ObjectNode index=RegistryJson.object(new RawJson(entries.remove("index.json")));
        assertEquals("3f67db77df018c21dcce4dd27fe8344f550a6f48565a830822fe9b8f8544911b",RegistryJson.text(index.get("manifest_sha256")));
        var names=new java.util.HashSet<String>();long raw=0;
        for(JsonNode item:RegistryJson.array(index.get("files"))){ObjectNode r=RegistryJson.object(item);String n=RegistryJson.text(r.get("entry"));assertTrue(names.add(n));byte[] b=entries.get(n);assertNotNull(b);
            assertEquals(BigInteger.valueOf(b.length),RegistryJson.integer(r.get("bytes"),BigInteger.ONE,null));assertEquals(RegistryJson.text(r.get("sha256")),sha(b));assertFalse(RegistryJson.text(r.get("source_path")).isBlank());raw+=b.length;}
        assertEquals(entries.keySet(),names);assertEquals(68,names.size());assertEquals(69439,raw);return Map.copyOf(entries);
    }catch(Exception failure){throw new ExceptionInInitializerError(failure);}}
    private static byte[] bytes(String name){return CORPUS.get(name).clone();}
    private static RawJson data(String prefix){return new RawJson(bytes(prefix+"data.json"));}
    private static RawJson mutate(String prefix,Consumer<ObjectNode> change){ObjectNode n=RegistryJson.object(data(prefix)).deepCopy();change.accept(n);return RegistryJson.encode(n);}
    private static ObjectNode row(ObjectNode n){return (ObjectNode)n.withArray("owned_task_rows").get(0);}
    private static ObjectNode progress(ObjectNode n){return (ObjectNode)row(n).get("progress_observation");}
    private static Frame expected(String prefix)throws IOException{return CouncilOwnedTaskProgressObservation26757580.frameFromFull(assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(bytes(prefix+"full.json.bin"))));}
    private static Partial actual(String caseName){return assertInstanceOf(Partial.class,CouncilOwnedTaskProgressObservation26757580.decodeData(data("originals-ON/"+caseName+"/")));}
    @Test void actualFourteenV2DataDocumentsUseIndependentFullAndNeverClaimLive()throws Exception{
        int partial=0,missing=0;
        for(var e:CORPUS.entrySet())if(e.getKey().endsWith("/data.json")){
            RawJson raw=new RawJson(e.getValue());if(!RegistryJson.text(RegistryJson.object(raw).get("schema")).equals(CouncilOwnedTaskProgressObservation26757580.SCHEMA))continue;
            var value=CouncilOwnedTaskProgressObservation26757580.decodeData(raw);assertFalse(value.origin().mainOwnerObserved());
            if(value instanceof Partial p){partial++;String prefix=e.getKey().substring(0,e.getKey().length()-"data.json".length());
                Frame independent=expected(prefix);p.requireFrame(independent);assertEquals(p,CouncilOwnedTaskProgressObservation26757580.decodeData(raw,independent));
                assertEquals(-2130706431,p.frame().playerCharacterId());assertEquals(CouncilOwnedTaskObservation26757580.OriginKind.OFFLINE_FIXTURE,p.origin().kind());
            }else{missing++;assertFalse(((Unavailable)value).reason().isEmpty());}
        }
        assertEquals(6,partial);assertEquals(8,missing);
    }
    @Test void actualIntegerModesPreserveMinimumOverMaximumOpaqueAndFrozenUnknown(){
        var percent=actual("0-percentage-raw").ownedTaskRows().get(0).progressObservation();assertEquals(10000001,percent.backingRaw());assertEquals(10000001,percent.currentRaw().orElseThrow());assertEquals(10000000,percent.maximumRaw().orElseThrow());
        var infinite=actual("1-infinite-minimum").ownedTaskRows().get(0).progressObservation();assertEquals(Kind.INFINITE,infinite.kind());assertEquals(Long.MIN_VALUE,infinite.backingRaw());assertEquals(Long.MIN_VALUE,infinite.currentRaw().orElseThrow());assertEquals(0,infinite.maximumRaw().orElseThrow());
        var opaque=actual("2-value-opaque").ownedTaskRows().get(0).progressObservation();assertEquals(Kind.VALUE,opaque.kind());assertEquals(Long.MAX_VALUE,opaque.backingRaw());assertTrue(opaque.currentRaw().isEmpty());assertTrue(opaque.maximumRaw().isEmpty());assertEquals(CurrentReason.VALUE_EVALUATOR_UNOBSERVED,opaque.currentReason().orElseThrow());
        var unknown=actual("3-unknown-kind").ownedTaskRows().get(0).progressObservation();assertEquals(-1,unknown.kindRaw());assertEquals(Kind.UNKNOWN,unknown.kind());assertEquals(CurrentReason.KIND_UNRECOGNIZED,unknown.currentReason().orElseThrow());
        var frozen=actual("4-noncanonical-frozen").ownedTaskRows().get(0).progressObservation();assertEquals(255,frozen.frozenRaw());assertFalse(frozen.frozenKnown());assertTrue(frozen.frozenValue().isEmpty());
        var vacant=actual("5-vacant-stored").ownedTaskRows().get(0);assertTrue(vacant.identity().holderCharacterId().isEmpty());assertEquals(77,vacant.progressObservation().backingRaw());assertEquals(CurrentReason.HOLDER_UNVERIFIED,vacant.progressObservation().currentReason().orElseThrow());assertFalse(vacant.progressObservation().frozenValue().orElseThrow());
        for(String name:List.of("0-percentage-raw","1-infinite-minimum","2-value-opaque","3-unknown-kind","4-noncanonical-frozen","5-vacant-stored"))assertFalse(actual(name).ownedTaskRows().get(0).progressObservation().nativeFloatObserved());
    }

    @Test void actualCommandResultsAndEightRequestRefusalsNeverBecomeFalseDataSuccess()throws Exception{
        int success=0,failure=0,requestFailure=0;
        for(var e:CORPUS.entrySet()){
            boolean normal=e.getKey().endsWith("/command.json.bin")&&!e.getKey().contains("/preserved67/");boolean request=e.getKey().contains("/request-negatives/")&&e.getKey().endsWith(".json.bin");if(!normal&&!request)continue;
            byte[] raw=e.getValue().clone();String digest=sha(raw);var cmd=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(raw));
            if(cmd.nativeOk()){
                assertFalse(request);success++;String prefix=e.getKey().substring(0,e.getKey().length()-"command.json.bin".length());
                var value=CouncilOwnedTaskProgressObservation26757580.decodeCommandResult(raw,cmd.requestId());assertEquals(CouncilOwnedTaskProgressObservation26757580.decodeData(data(prefix)),value);
                if(value instanceof Partial)assertEquals(value,CouncilOwnedTaskProgressObservation26757580.decodeCommandResult(raw,cmd.requestId(),expected(prefix)));
            }else{
                if(request)requestFailure++;else failure++;
                String error=RegistryJson.text(RegistryJson.object(new RawJson(cmd.payload().value())).get("error"));
                assertTrue(assertThrows(IOException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeCommandResult(raw,cmd.requestId())).getMessage().contains(error));
            }
            assertEquals(digest,sha(raw));
        }
        assertEquals(7,success);assertEquals(7,failure);assertEquals(8,requestFailure);
    }
    @Test void old67AndOpeningRemainSeparateInsteadOfBeingRelabeledAsV2(){
        int old67=0,opening=0;
        for(var e:CORPUS.entrySet())if(e.getKey().endsWith("/data.json")){
            RawJson raw=new RawJson(e.getValue());String schema=RegistryJson.text(RegistryJson.object(raw).get("schema"));
            if(schema.equals(CouncilOwnedTaskObservation26757580.SCHEMA)){
                old67++;assertNotNull(CouncilOwnedTaskObservation26757580.decodeData(raw));assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(raw));
            }else if(!schema.equals(CouncilOwnedTaskProgressObservation26757580.SCHEMA)){
                opening++;assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(raw));
            }
        }
        assertEquals(2,old67);assertEquals(1,opening);assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(data(ROOT)));
    }
    @Test void progressThirteenFieldsRejectCoercionsMissingFieldsAndIntegerOverflow(){
        var fields=List.of("kind_raw","kind","backing_raw","scale","current_source_verified","current_raw","maximum_raw","current_reason","native_float_observed","frozen_raw","frozen_known","frozen_value","frozen_reason");
        for(String field:fields)assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->progress(n).remove(field))));
        for(String field:List.of("kind_raw","backing_raw","scale","current_raw","maximum_raw","frozen_raw")){
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->progress(n).put(field,"1"))));
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->progress(n).put(field,true))));
            String text=new String(data(ROOT).bytes(),StandardCharsets.UTF_8);var matcher=java.util.regex.Pattern.compile("(\""+field+"\"[ ]*:[ ]*)-?[0-9]+").matcher(text);assertTrue(matcher.find());
            String floating=matcher.replaceFirst(java.util.regex.Matcher.quoteReplacement(matcher.group(1)+"1.0"));
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(new RawJson(floating.getBytes(StandardCharsets.UTF_8))));
        }
        for(String field:List.of("current_source_verified","native_float_observed","frozen_known","frozen_value"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->progress(n).put(field,1))));
        for(BigInteger value:List.of(BigInteger.ONE.shiftLeft(63),BigInteger.ONE.shiftLeft(63).negate().subtract(BigInteger.ONE)))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->progress(n).put("backing_raw",value))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->progress(n).put("kind_raw",BigInteger.ONE.shiftLeft(31)))));
        for(int value:List.of(-1,256))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->progress(n).put("frozen_raw",value))));
    }

    @Test void currentAndFrozenReasonRulesStayCoupledWithoutClampingOrLegacyProgress(){
        for(Consumer<ObjectNode> change:List.<Consumer<ObjectNode>>of(p->p.put("kind","value"),p->p.put("scale",100001),p->p.put("backing_raw",1),p->p.put("maximum_raw",10000001),p->p.put("current_source_verified",false),p->p.put("native_float_observed",true),p->p.put("current_reason","council70_current_holder_unverified"),p->p.put("frozen_known",false),p->p.put("frozen_value",false)))
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->change.accept(progress(n)))));
        for(String prefix:List.of("originals-ON/2-value-opaque/","originals-ON/3-unknown-kind/","originals-ON/5-vacant-stored/")){
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(prefix,n->progress(n).put("current_raw",0))));
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(prefix,n->progress(n).putNull("current_reason"))));
        }
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate("originals-ON/2-value-opaque/",n->progress(n).put("current_reason","council70_current_holder_unverified"))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate("originals-ON/5-vacant-stored/",n->progress(n).put("current_reason","council70_progress_kind_unrecognized"))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate("originals-ON/4-noncanonical-frozen/",n->progress(n).put("frozen_known",true))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate("originals-ON/4-noncanonical-frozen/",n->progress(n).put("frozen_value",false))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate("originals-ON/4-noncanonical-frozen/",n->progress(n).putNull("frozen_reason"))));
        for(String field:List.of("target","progress","max_progress","frozen"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->row(n).put(field,0))));
        var negative=assertInstanceOf(Partial.class,CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->{progress(n).put("backing_raw",Long.MIN_VALUE);progress(n).put("current_raw",Long.MIN_VALUE);})));
        assertEquals(Long.MIN_VALUE,negative.ownedTaskRows().get(0).progressObservation().currentRaw().orElseThrow());
    }
    @Test void independentFrameSignedIdentityAndPartialOnlyFlagsRemainStrict()throws Exception{
        Frame independent=expected(ROOT);
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->{var frame=(ObjectNode)n.get("frame");frame.put("native_snapshot_id","native:68").put("native_revision",68);}),independent));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->((ObjectNode)n.get("frame")).put("player_character_id",0)),independent));
        var zero=assertInstanceOf(Partial.class,CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->row(n).put("task_id",0))));assertEquals(0,zero.ownedTaskRows().get(0).identity().taskId());
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->row(n).put("task_id",-1))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->n.withArray("owned_task_rows").add(row(n).deepCopy()))));
        for(String field:List.of("all_seats_enumerated","full_council_read_available","candidate_collection_complete","progress_ready","action_ready"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->n.put(field,true))));
        for(String field:List.of("reader_sha256","abi_sha256","frame_sha256"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->((ObjectNode)n.get("provenance")).put(field,"0".repeat(64)))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(mutate(ROOT,n->((ObjectNode)n.get("origin")).put("main_owner_observed",true))));
        var unavailable=data("originals-ON/6-default-source-unavailable/");assertInstanceOf(Unavailable.class,CouncilOwnedTaskProgressObservation26757580.decodeData(unavailable,independent));
    }
    @Test void actualConditionalOuterFieldsRejectLiteralPlaceholderWrongIdsAndMalformedPackets()throws Exception{
        byte[] raw=bytes(ROOT+"command.json.bin");var command=(NativeWire.CommandResult)NativeWire.decode(raw);
        assertThrows(IOException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeCommandResult(raw,"foreign-id"));
        assertThrows(IOException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeCommandResult(java.util.Arrays.copyOf(raw,raw.length+1),command.requestId()));
        ObjectNode envelope=RegistryJson.object(new RawJson(command.payload().value()));
        var placeholder=envelope.deepCopy();placeholder.set("result_or_error",placeholder.remove("result"));
        assertThrows(IOException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeCommandResult(packet(RegistryJson.encode(placeholder).bytes()),command.requestId()));
        var protocol=envelope.deepCopy();protocol.put("protocol_version",2);assertThrows(IOException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeCommandResult(packet(RegistryJson.encode(protocol).bytes()),command.requestId()));
        var noResult=envelope.deepCopy();noResult.putNull("result");assertThrows(IOException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeCommandResult(packet(RegistryJson.encode(noResult).bytes()),command.requestId()));
        String original=new String(data(ROOT).bytes(),StandardCharsets.UTF_8);String duplicate=original.replaceFirst("(\"status\"[ ]*:[ ]*\"partial\")","$1,\"status\":\"partial\"");assertNotEquals(original,duplicate);
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(new RawJson(duplicate.getBytes(StandardCharsets.UTF_8))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskProgressObservation26757580.decodeData(new RawJson((original+"{}").getBytes(StandardCharsets.UTF_8))));
    }
    private static byte[] packet(byte[] raw){return ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();}
}
