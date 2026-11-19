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
import org.xar.ck3.control.nativebridge.capabilities.registry.CouncilOwnedTaskObservation26757580.*;

/** Actual NoGame Cpp bytes plus explicitly malformed DATA mutations. No live Main, SDK custody or Council permission. */
final class CouncilOwnedTaskObservation26757580Test {
    private static final String ROOT="originals-ON/0-current-live/";
    private static final Map<String,byte[]> CORPUS=loadCorpus();
    private static String sha(byte[] b)throws Exception{return java.util.HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b));}
    private static Map<String,byte[]> loadCorpus(){
        try {
            String explicit=System.getProperty("xar.native.council67.corpus");byte[] archive;
            if(explicit!=null){Path p=Path.of(explicit);if(!p.isAbsolute())throw new IOException("explicit corpus path must be absolute");archive=Files.readAllBytes(p);}
            else try(var input=CouncilOwnedTaskObservation26757580Test.class.getResourceAsStream("/newnative/council67/council67-actual.zip")){
                if(input==null)throw new IOException("real Cpp Council67 corpus is missing");archive=input.readNBytes(39004);
            }
            if(archive.length!=39003||!sha(archive).equals("6ba65afad08f55a9afec1c7a2fddace9c6ea8986aa2fd90ac05903ad0c104ceb"))throw new IOException("actual corpus ZIP bytes/SHA differ");
            var entries=new LinkedHashMap<String,byte[]>();
            try(var zip=new ZipInputStream(new ByteArrayInputStream(archive))){
                for(var entry=zip.getNextEntry();entry!=null;entry=zip.getNextEntry()){
                    byte[] b=zip.readNBytes(262145);if(entry.isDirectory()||b.length>262144||entries.putIfAbsent(entry.getName(),b)!=null)throw new IOException("invalid corpus entry");
                }
            }
            assertEquals(58,entries.size());ObjectNode index=RegistryJson.object(new RawJson(entries.remove("index.json")));
            RegistryJson.keys(index,Set.of("source_manifest_sha256","files"));
            assertEquals("7ceabd2bf847905e2be975f76611f24381bf080868721f22cc86358a39717987",RegistryJson.text(index.get("source_manifest_sha256")));
            var names=new java.util.HashSet<String>();long total=0;
            for(JsonNode raw:RegistryJson.array(index.get("files"))){
                ObjectNode row=RegistryJson.object(raw);RegistryJson.keys(row,Set.of("entry","bytes","sha256","source_path"));String name=RegistryJson.text(row.get("entry"));
                assertTrue(names.add(name));byte[] b=entries.get(name);assertNotNull(b);assertEquals(BigInteger.valueOf(b.length),RegistryJson.integer(row.get("bytes"),BigInteger.ONE,null));
                assertEquals(RegistryJson.text(row.get("sha256")),sha(b));assertFalse(RegistryJson.text(row.get("source_path")).isBlank());total+=b.length;
            }
            assertEquals(entries.keySet(),names);assertEquals(57,names.size());assertEquals(47707,total);return Map.copyOf(entries);
        }catch(Exception failure){throw new ExceptionInInitializerError(failure);}
    }
    private static byte[] bytes(String name){return CORPUS.get(name).clone();}
    private static RawJson data(){return new RawJson(bytes(ROOT+"data.json"));}
    private static RawJson mutate(Consumer<ObjectNode> change){var n=RegistryJson.object(data()).deepCopy();change.accept(n);return RegistryJson.encode(n);}
    private static ObjectNode object(ObjectNode n,String key){return (ObjectNode)n.get(key);}
    private static ObjectNode task(ObjectNode n){return (ObjectNode)n.withArray("owned_task_rows").get(0);}
    private static Frame actualExpected(String prefix)throws IOException{
        var snapshot=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(bytes(prefix+"full.json.bin")));
        return CouncilOwnedTaskObservation26757580.frameFromFull(snapshot);
    }
    @Test void allTwentySevenActualDataDocumentsRemainThreePartialAndTwentyFourUnavailable()throws Exception{
        int partial=0,unavailable=0,offline=0,unobserved=0;
        for(var entry:CORPUS.entrySet())if(entry.getKey().endsWith("/data.json")){
            var value=CouncilOwnedTaskObservation26757580.decodeData(new RawJson(entry.getValue()));
            assertFalse(value.origin().mainOwnerObserved());
            if(value.origin().kind()==OriginKind.OFFLINE_FIXTURE){offline++;assertEquals(BigInteger.valueOf(68),value.origin().ticketSequence().orElseThrow());assertEquals(49092,value.origin().threadId().orElseThrow());}
            else{unobserved++;assertEquals(OriginKind.UNAVAILABLE,value.origin().kind());assertTrue(value.origin().ticketSequence().isEmpty());}
            if(value instanceof Partial current){partial++;String prefix=entry.getKey().substring(0,entry.getKey().length()-"data.json".length());Frame independent=actualExpected(prefix);
                assertEquals(current,CouncilOwnedTaskObservation26757580.decodeData(new RawJson(entry.getValue()),independent));current.requireFrame(independent);
                assertEquals(-2130706431,current.frame().playerCharacterId());assertEquals("native:67",current.frame().nativeSnapshotId());
            }else{unavailable++;assertFalse(((Unavailable)value).reason().isEmpty());}
        }
        assertEquals(3,partial);assertEquals(24,unavailable);assertEquals(25,offline);assertEquals(2,unobserved);
        var vacant=assertInstanceOf(Partial.class,CouncilOwnedTaskObservation26757580.decodeData(new RawJson(bytes("originals-ON/1-vacant/data.json"))));
        assertTrue(vacant.ownedTaskRows().get(0).holderCharacterId().isEmpty());assertFalse(vacant.ownedTaskRows().get(0).holderAlive());
        var empty=assertInstanceOf(Partial.class,CouncilOwnedTaskObservation26757580.decodeData(new RawJson(bytes("originals-ON/2-owned-empty/data.json"))));
        assertTrue(empty.ownedTaskRows().isEmpty());assertEquals(OriginKind.OFFLINE_FIXTURE,empty.origin().kind());
    }

    @Test void actualCommandLayerKeepsEightSuccessfulPacketsSeparateFromNineteenRejectedOriginals()throws Exception{
        int ok=0,rejected=0;
        for(var entry:CORPUS.entrySet())if(entry.getKey().endsWith("/command.json.bin")){
            byte[] original=entry.getValue().clone();var command=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(original));String digest=sha(original);
            if(command.nativeOk()){
                ok++;String prefix=entry.getKey().substring(0,entry.getKey().length()-"command.json.bin".length());
                var expected=CouncilOwnedTaskObservation26757580.decodeData(new RawJson(bytes(prefix+"data.json")));
                assertEquals(expected,CouncilOwnedTaskObservation26757580.decodeCommandResult(original,command.requestId()));
                if(expected instanceof Partial)assertEquals(expected,CouncilOwnedTaskObservation26757580.decodeCommandResult(original,command.requestId(),actualExpected(prefix)));
            }else{
                rejected++;var error=RegistryJson.text(RegistryJson.object(new RawJson(command.payload().value())).get("error"));
                IOException failure=assertThrows(IOException.class,()->CouncilOwnedTaskObservation26757580.decodeCommandResult(original,command.requestId()));
                assertTrue(failure.getMessage().contains(error));
            }
            assertEquals(digest,sha(original));
        }
        assertEquals(8,ok);assertEquals(19,rejected);
    }
    @Test void dataFrameMustMatchASeparatelyParsedActualFullAndUnavailableNeverBecomesFrameReady()throws Exception{
        Frame independent=actualExpected(ROOT);
        var actual=assertInstanceOf(Partial.class,CouncilOwnedTaskObservation26757580.decodeData(data(),independent));
        assertEquals(-2097151999,actual.ownedTaskRows().get(0).taskId());assertEquals(-2113929214,actual.ownedTaskRows().get(0).holderCharacterId().orElseThrow());
        for(RawJson changed:List.of(mutate(n->object(n,"frame").put("date_raw",123457)),mutate(n->object(n,"frame").put("player_character_id",0)),
                mutate(n->{object(n,"frame").put("native_snapshot_id","native:68");object(n,"frame").put("native_revision",68);}))){
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(changed,independent));
        }
        RawJson missing=new RawJson(bytes("originals-ON/3-default-type/data.json"));
        assertInstanceOf(Unavailable.class,CouncilOwnedTaskObservation26757580.decodeData(missing,independent));
        byte[] full=bytes(ROOT+"full.json.bin");var snapshot=(NativeWire.Snapshot)NativeWire.decode(full);
        ObjectNode state=RegistryJson.object(new RawJson(snapshot.state().value()));state.put("adapter_id","ck3-1.21.0-msvc-x64");
        var forged=new NativeWire.Snapshot(snapshot.snapshotId(),snapshot.revision(),new NativeWire.Bytes(RegistryJson.encode(state).bytes()),snapshot.packet());
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.frameFromFull(forged));
    }
    @Test void signedAndZeroIdsAreDataWhileMinusOneAndDuplicateRowsAreRejected(){
        var zero=assertInstanceOf(Partial.class,CouncilOwnedTaskObservation26757580.decodeData(mutate(n->{task(n).put("task_id",0);task(n).put("holder_character_id",0);object(n,"frame").put("player_character_id",0);})));
        assertEquals(0,zero.ownedTaskRows().get(0).taskId());assertEquals(0,zero.ownedTaskRows().get(0).holderCharacterId().orElseThrow());assertEquals(0,zero.frame().playerCharacterId());
        for(String field:List.of("task_id","holder_character_id"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->task(n).put(field,-1))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"frame").put("player_character_id",-1))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->{var rows=n.withArray("owned_task_rows");rows.add(rows.get(0).deepCopy());})));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->{var row=task(n).deepCopy();row.put("task_id",0);n.withArray("owned_task_rows").add(row);})));
        var ordered=assertInstanceOf(Partial.class,CouncilOwnedTaskObservation26757580.decodeData(mutate(n->{var row=task(n).deepCopy();row.put("task_id",0).put("position_key","councillor_chancellor");n.withArray("owned_task_rows").add(row);})));
        assertEquals(List.of(-2097151999,0),ordered.ownedTaskRows().stream().map(OwnedTaskRow::taskId).toList());
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->{var rows=n.withArray("owned_task_rows");for(int i=1;i<65;i++){var row=task(n).deepCopy();row.put("task_id",i).put("position_key","p"+i);rows.add(row);}})));
    }

    @Test void everyBooleanAndIntegerBoundaryRejectsNullStringBooleanAndFloatingPointCoercion(){
        for(String field:List.of("private_build","advertised","read_only","data_ready","same_frame_ready","all_seats_enumerated","full_council_read_available","candidate_collection_complete","progress_ready","action_ready"))
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->n.put(field,1))));
        for(String field:List.of("paused","map_ready"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"frame").put(field,"true"))));
        for(String field:List.of("holder_alive","current_type_source_verified"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->task(n).putNull(field))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"origin").put("main_owner_observed",0))));
        for(String field:List.of("native_revision","date_raw","player_character_id","task_id","holder_character_id","ticket_sequence","pump_epoch","thread_id")){
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->integerOwner(n,field).put(field,"1"))));
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->integerOwner(n,field).put(field,true))));
            String original=new String(data().bytes(),StandardCharsets.UTF_8);
            var matcher=java.util.regex.Pattern.compile("(\""+field+"\"[ ]*:[ ]*)-?[0-9]+").matcher(original);assertTrue(matcher.find());
            String floating=matcher.replaceFirst(java.util.regex.Matcher.quoteReplacement(matcher.group(1)+"1.0"));
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(new RawJson(floating.getBytes(StandardCharsets.UTF_8))));
        }
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"origin").put("ticket_sequence",BigInteger.ONE.shiftLeft(64)))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"origin").put("thread_id",BigInteger.ONE.shiftLeft(32)))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->task(n).put("task_id",BigInteger.ONE.shiftLeft(31)))));
    }
    private static ObjectNode integerOwner(ObjectNode n,String field){return switch(field){
        case "native_revision","date_raw","player_character_id"->object(n,"frame");
        case "task_id","holder_character_id"->task(n);default->object(n,"origin");};}
    @Test void exactKeysOriginsNullsAndNonCompleteClaimsCannotDrift(){
        for(String field:List.of("all_seats_enumerated","full_council_read_available","candidate_collection_complete","progress_ready","action_ready"))
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->n.put(field,true))));
        for(String field:List.of("target","progress","max_progress","frozen"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->task(n).put(field,0))));
        for(String field:List.of("candidates","final_gates","assignment_quote"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->n.putArray(field))));
        for(String field:List.of("position_key","stored_task_type_key","current_task_type_key"))for(String value:List.of("", "x".repeat(96),"bad key","non_ascii_é"))
            assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->task(n).put(field,value))));
        assertInstanceOf(Partial.class,CouncilOwnedTaskObservation26757580.decodeData(mutate(n->task(n).put("position_key","x".repeat(95)))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->task(n).put("current_task_type_key","task_other"))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->task(n).put("current_type_source_verified",false))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->task(n).putNull("holder_character_id"))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"origin").put("main_owner_observed",true))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"origin").put("source_kind","application_main_ticket"))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"origin").put("source_kind","unavailable"))));
        for(String field:List.of("schema","step","status"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->n.put(field,"wrong"))));
        for(String field:List.of("adapter_id","game_version","steam_build_id","executable_sha256"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"build").put(field,"old-profile"))));
        for(String field:List.of("reader_sha256","abi_sha256","frame_sha256"))assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"provenance").put(field,"0".repeat(64)))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->n.put("extra",true))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->n.remove("reason"))));
        String original=new String(data().bytes(),StandardCharsets.UTF_8);
        String duplicate=original.replaceFirst("(\"status\"[ ]*:[ ]*\"partial\")","$1,\"status\":\"partial\"");assertNotEquals(original,duplicate);
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(new RawJson(duplicate.getBytes(StandardCharsets.UTF_8))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(new RawJson((original+"{}").getBytes(StandardCharsets.UTF_8))));
    }

    @Test void unavailableNullSemanticsAndMalformedOriginalPacketsFailClosed()throws Exception{
        var missing=RegistryJson.object(new RawJson(bytes("originals-ON/3-default-type/data.json")));
        var emptyReason=missing.deepCopy();emptyReason.put("reason","");assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(RegistryJson.encode(emptyReason)));
        var falseFrame=missing.deepCopy();falseFrame.set("frame",RegistryJson.object(data()).get("frame"));assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(RegistryJson.encode(falseFrame)));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->n.put("same_frame_ready",false))));
        assertThrows(IllegalArgumentException.class,()->CouncilOwnedTaskObservation26757580.decodeData(mutate(n->object(n,"frame").put("native_snapshot_id","native:067"))));
        byte[] original=bytes(ROOT+"command.json.bin");var command=(NativeWire.CommandResult)NativeWire.decode(original);
        assertThrows(IOException.class,()->CouncilOwnedTaskObservation26757580.decodeCommandResult(original,"foreign-request"));
        byte[] trailing=java.util.Arrays.copyOf(original,original.length+1);assertThrows(IOException.class,()->CouncilOwnedTaskObservation26757580.decodeCommandResult(trailing,command.requestId()));
        ObjectNode envelope=RegistryJson.object(new RawJson(command.payload().value()));
        var wrongProtocol=envelope.deepCopy();wrongProtocol.put("protocol_version",2);
        assertThrows(IOException.class,()->CouncilOwnedTaskObservation26757580.decodeCommandResult(packet(RegistryJson.encode(wrongProtocol).bytes()),command.requestId()));
        var noResult=envelope.deepCopy();noResult.remove("result");
        assertThrows(IOException.class,()->CouncilOwnedTaskObservation26757580.decodeCommandResult(packet(RegistryJson.encode(noResult).bytes()),command.requestId()));
        String payload=new String(command.payload().value(),StandardCharsets.UTF_8);
        var revisionPattern=java.util.regex.Pattern.compile("(\"native_revision\"[ ]*:[ ]*)67").matcher(payload);assertTrue(revisionPattern.find());
        String floatRevision=revisionPattern.replaceFirst(java.util.regex.Matcher.quoteReplacement(revisionPattern.group(1)+"67.0"));assertNotEquals(payload,floatRevision);
        assertThrows(IOException.class,()->CouncilOwnedTaskObservation26757580.decodeCommandResult(packet(floatRevision.getBytes(StandardCharsets.UTF_8)),command.requestId()));
    }
    private static byte[] packet(byte[] payload){return ByteBuffer.allocate(payload.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();}
}
