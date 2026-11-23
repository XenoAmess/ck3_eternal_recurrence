package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Actual independently owned C++ bytes; Java mutations below are DATA, never new Native frames or exchanges. */
final class NativeCurrentRmtmTitleQuery26785313ProducerTest {
    record Artifact(String name,int bytes,String sha256){}
    private static final List<Artifact> CPP=List.of(
        new Artifact("available-dead-holder-data.json",1341,"268d9077872c4ef54ea8eb37b13cf0b98d95bb0f20b8b8b7ab118fa00112179d"),
        new Artifact("available-empty-laws.json",1273,"6a64c5b3905149729c7885d9b92dea5232335bc2aa8bd7dcdecad62f1cf306d1"),
        new Artifact("available-full-bits.json",1353,"01ba0a94a4cadd39d218f9ca558693dbbf9cd43b441948edd91bf05424dab303"),
        new Artifact("available-law.json",1327,"5a56bc5168136f65c80ad3df1b82c5c10364214b4b07df8e50395c300f8ed0b0"),
        new Artifact("available-none-holder-heir.json",1226,"796cd1923998663d7a43f173a235b374412397806d836e4d8919b2e36906d6e5"),
        new Artifact("expired.json",786,"7fedf0e061cb7e9ace76e989f5bddf4818cf3a6109bf7b6c0379113442a5a830"),
        new Artifact("indeterminate.json",805,"3bb903ee4d138d18dee71c4121a5360cb7d5f7c8b8da47984770ebf2065cff6c"),
        new Artifact("query.request.json",709,"001332bfd1c861c5317c131f46f3904ca8c99c6da1c690b05614c1552b1957e2"),
        new Artifact("stale_source.json",801,"49a38b3b62d6c6137c18e87d60bbacd7154408bcba04fbf4bd0d93eab08bb3cc"),
        new Artifact("unavailable.json",798,"7f0bd913fc1617e5d3906afecede1f378fc41fedf77cbedbe58299e6161820df")
    );
    private static final List<String> RESPONSES=List.of("available-dead-holder-data.json","available-empty-laws.json","available-full-bits.json","available-law.json","available-none-holder-heir.json","expired.json","indeterminate.json","stale_source.json","unavailable.json");
    private static byte[] raw(String name)throws Exception{
        var p=CPP.stream().filter(v->v.name().equals(name)).findFirst().orElseThrow();
        try(var in=NativeCurrentRmtmTitleQuery26785313ProducerTest.class.getResourceAsStream("/current267-rmtm-title-query-cpp-a01/"+name)){
            if(in==null)throw new IOException("Original C++ RMTM resource absent: "+name);var bytes=in.readAllBytes();assertEquals(p.bytes(),bytes.length);
            assertEquals(p.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));return bytes;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(raw(name)));}
    private static ObjectNode token(String name)throws Exception{return NativeWire.object(envelope(name).get("result"));}
    private static CurrentRmtmTitleQueryResult frame(String name)throws Exception{return CurrentRmtmTitleQueryResult.decode(new RawJson(NativeWire.token(raw(name),"result")));}
    private static CurrentRmtmTitleQueryResult changed(ObjectNode n)throws IOException{return CurrentRmtmTitleQueryResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}

    @Test void nineActualCppResponsesRoundtripAndAllTenOriginalFilesRemainPinned()throws Exception{
        assertEquals(10,CPP.size());assertEquals(9,RESPONSES.size());int available=0;
        for(String name:RESPONSES){var e=StrictJson.object(envelope(name),Set.of("type","protocol_version","request_id","ok","result"));
            assertEquals("command_result",e.get("type").textValue());assertEquals(1,e.get("protocol_version").intValue());
            var f=frame(name);assertEquals(f,CurrentRmtmTitleQueryResult.decode(f.encode()));assertEquals(e.get("ok").booleanValue(),f.successful());assertEquals(22,token(name).size());
            if(f.source().isPresent()){available++;assertEquals(9,f.source().orElseThrow().encode().size());assertEquals(f.factsBefore().orElseThrow().playedCharacterId(),f.source().orElseThrow().actorId());}
        }
        assertEquals(5,available);raw("query.request.json");
    }
    @Test void actualJavaFactoryKeepsOriginalIdAndMaximumDeadlineWithoutCallerTitle()throws Exception{
        var original=StrictJson.object(envelope("query.request.json"),Set.of("type","protocol_version","request_id","step","expected_revision","arguments","rmtm_title","core_control_deadline_unix_ms"));
        var claim=StrictJson.object(original.get("rmtm_title"),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","expected_core"));
        var p=StrictJson.object(claim.get("expected_core"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));
        var core=new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,new CoreFrame.Prefix(CurrentRmtmTitleQuery.i32(p.get("date_raw")),CurrentRmtmTitleQuery.i32(p.get("speed")),CurrentRmtmTitleQuery.bool(p,"paused"),CurrentRmtmTitleQuery.i32(p.get("local_player_id")),CurrentRmtmTitleQuery.bool(p,"map_ready"),CurrentRmtmTitleQuery.bool(p,"has_played_character"),CurrentRmtmTitleQuery.i32(p.get("played_character_id")),CurrentRmtmTitleQuery.bool(p,"played_character_alive")));
        var factory=CurrentRmtmTitleQuery.request(core);var fields=NativeWire.object(NativeWire.parse(factory.additionalFields().bytes()));
        assertEquals(7,fields.get("rmtm_title").size());assertFalse(fields.get("rmtm_title").has("title_id"));
        var max=new BigInteger("18446744073709551615");assertEquals(max,original.get("core_control_deadline_unix_ms").bigIntegerValue());fields.put("core_control_deadline_unix_ms",max);
        var packet=NativeWire.execute(original.get("request_id").textValue(),factory.step(),BigInteger.ZERO,StrictJson.canonical(fields));
        var decoded=NativeWire.decodeExecuteRequest(packet);assertEquals("rmtm-title-original-query-01",decoded.requestId());assertEquals(factory.step(),decoded.step());
        assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());var body=Arrays.copyOfRange(packet,4,packet.length);
        var expected=original.deepCopy();String generated=fields.get("rmtm_title").get("executable_sha256").textValue();
        assertEquals(claim.get("executable_sha256").textValue().toLowerCase(Locale.ROOT),generated.toLowerCase(Locale.ROOT));((ObjectNode)expected.get("rmtm_title")).put("executable_sha256",generated);
        assertEquals(expected,NativeWire.parse(body));assertArrayEquals(packet,NativeWire.packet(body));
        String output=System.getProperty("xar.rmtm.title.java.requests.output.directory");if(output!=null){assertFalse(output.isBlank());Path root=Path.of(output).toAbsolutePath();Files.createDirectories(root);assertFalse(Files.isSymbolicLink(root));
            Files.write(root.resolve("java-query.packet.bin"),packet,StandardOpenOption.CREATE_NEW);Files.write(root.resolve("java-query.body.json"),body,StandardOpenOption.CREATE_NEW);}
    }
    @Test void actualKnownEmptyNullRolesAndDeadHolderStayDistinctFromUnavailable()throws Exception{
        var empty=frame("available-empty-laws.json").source().orElseThrow();assertEquals(0,empty.nativeLawCount());assertTrue(empty.physicalOwnLaws().isEmpty());
        var none=frame("available-none-holder-heir.json").source().orElseThrow();assertTrue(none.holder().isEmpty());assertTrue(none.engineCurrentHeir().isEmpty());assertEquals(0,none.engineSuccessorCount());
        assertFalse(frame("available-dead-holder-data.json").source().orElseThrow().holder().orElseThrow().alive());
        assertTrue(frame("unavailable.json").source().isEmpty());assertFalse(frame("unavailable.json").successful());
    }
    @Test void actualHighBitTitleAndPackedActorAreNeverSignedCoerced()throws Exception{
        var full=frame("available-full-bits.json").source().orElseThrow();assertEquals(-2,full.actorId());assertEquals(2768240641L,full.fullTitleId());assertEquals(0xffff_fffeL,full.holder().orElseThrow().fullId());
        var zero=frame("available-law.json").source().orElseThrow();assertEquals(0,zero.actorId());assertEquals(0,zero.fullTitleId());assertEquals(0,zero.physicalOwnLaws().getFirst().nativeDefinitionId());
        assertEquals("single_heir_succession_law",zero.physicalOwnLaws().getFirst().key());
        var sentinel=token("available-full-bits.json");source(sentinel).put("full_title_id",0xffff_ffffL);assertThrows(IOException.class,()->changed(sentinel));
        var floating=token("available-law.json");source(floating).put("full_title_id",0.0);assertThrows(IOException.class,()->changed(floating));
    }
    @Test void actualRefusalsAndUnknownKeepSourceNullAndInformationalCountersZero()throws Exception{
        for(String name:List.of("unavailable.json","expired.json","stale_source.json","indeterminate.json")){
            var f=frame(name);assertFalse(f.successful());assertTrue(f.source().isEmpty());assertEquals(BigInteger.ZERO,f.providerGeneration());assertEquals(BigInteger.ZERO,f.querySequence());assertTrue(f.unavailableReason().isPresent());
        }
        var unknown=frame("indeterminate.json");assertEquals(CurrentRmtmTitleQueryResult.Status.INDETERMINATE,unknown.status());assertFalse(unknown.cleanupKnown());
        var promoted=token("indeterminate.json");promoted.put("status","available");assertThrows(IOException.class,()->changed(promoted));
        var sourceAsEmpty=token("unavailable.json");sourceAsEmpty.set("source",frame("available-empty-laws.json").source().orElseThrow().encode());assertThrows(IOException.class,()->changed(sourceAsEmpty));
    }
    @Test void actualLawArrayAndEveryResponseRemainReadonlyWithoutRealmOrExecuteTimeClaims()throws Exception{
        for(String name:RESPONSES){var f=frame(name);assertEquals(BigInteger.ZERO,f.claimSequence());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertFalse(f.nativeHandled());assertFalse(f.newDateObserved());assertFalse(f.physicalSaveConfirmed());}
        var missing=token("available-law.json");source(missing).put("native_law_count",0);assertThrows(IOException.class,()->changed(missing));
        var doubled=token("available-law.json");var rows=(com.fasterxml.jackson.databind.node.ArrayNode)source(doubled).get("physical_own_laws");rows.add(rows.get(0).deepCopy());source(doubled).put("native_law_count",2);assertThrows(IOException.class,()->changed(doubled));
        var action=token("available-law.json");action.put("effect_attempted",true);assertThrows(IOException.class,()->changed(action));
        var epoch=token("available-law.json");epoch.put("CCC_epoch",1);assertThrows(IOException.class,()->changed(epoch));
    }
}
