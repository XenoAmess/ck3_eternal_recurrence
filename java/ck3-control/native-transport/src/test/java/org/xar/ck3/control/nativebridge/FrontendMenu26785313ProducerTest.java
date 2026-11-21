package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1PublicCodec;

final class FrontendMenu26785313ProducerTest {
    @Test void everyGenuineCppRequestAndResultRoundtripsWithoutCoreOrConfirmationCredits()throws Exception {
        int requests=0,results=0;
        for(var entry:FrontendMenuCppFrames.entries()){
            if(entry.kind().equals("request")){
                requests++;var request=FrontendMenuFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(entry.json()));
                byte[] encoded=NativeWire.execute("java-menu-data-"+request.action().wire(),request.action().step(),BigInteger.ZERO,FrontendMenuFrameV1PublicCodec.additionalFields(request).bytes());assertEquals(request,FrontendMenuFrameV1PublicCodec.decodeRequestPacket(encoded));
                String destination=System.getProperty("xar.frontend.menu.java.requests");if(destination!=null)java.nio.file.Files.write(java.nio.file.Path.of(destination).resolve(request.action().wire()+"-java-request.json"),java.util.Arrays.copyOfRange(encoded,4,encoded.length),java.nio.file.StandardOpenOption.CREATE_NEW);
            }else{
                results++;var original=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(entry.json())));
                var frame=FrontendMenuFrameV1PublicCodec.decodePacket(new RawJson(original.payload().value()),original.requestId());assertEquals(frame,FrontendMenuFrameV1.decode(FrontendMenuFrameV1PublicCodec.encode(frame)));
                var row=NativeWire.object(NativeWire.parse(FrontendMenuFrameV1PublicCodec.encode(frame).bytes()));
                for(String field:new String[]{"world_core_fabricated","application_exit_confirmed","game_started_confirmed","physical_save_confirmed"})assertFalse(row.get(field).booleanValue());
                assertFalse(row.has("core_frame"));assertFalse(row.has("native_handled"));
            }
        }
        assertTrue(requests>=2);assertTrue(results>=2);
    }
    @Test void queryAndEffectsCannotExchangeTheirLeasesOrActions()throws Exception {
        byte[] original=FrontendMenuCppFrames.request(FrontendMenuFrameV1.Action.QUIT_MENU);var row=NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(original,4,original.length)));
        row.put("step",FrontendMenuFrameV1.Action.QUERY_MENU.step());assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(row))));
        var request=FrontendMenuFrameV1PublicCodec.decodeRequestPacket(original);
        assertThrows(IllegalArgumentException.class,()->new FrontendMenuFrameV1PublicCodec.Request(FrontendMenuFrameV1.Action.QUERY_MENU,request.deadlineUnixMs(),request.lease()));
        assertThrows(IllegalArgumentException.class,()->new FrontendMenuFrameV1PublicCodec.Request(FrontendMenuFrameV1.Action.QUIT_MENU,request.deadlineUnixMs(),new FrontendMenuFrameV1PublicCodec.Lease(BigInteger.ZERO,BigInteger.ZERO)));
    }
    @Test void uint64StringsAndJsonIntegerDeadlinesRejectCoercionAndOverflow()throws Exception {
        for(String field:new String[]{"provider_generation","query_sequence"})for(String bad:new String[]{"+1","01","-0","-1","18446744073709551616"}){
            var row=NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(FrontendMenuCppFrames.request(FrontendMenuFrameV1.Action.QUIT_MENU),4,FrontendMenuCppFrames.request(FrontendMenuFrameV1.Action.QUIT_MENU).length)));NativeWire.object(row.get("frontend_menu")).put(field,bad);
            assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(row))));
        }
        for(String token:new String[]{"true","1.0","null","\"123\"","0","18446744073709551616"}){
            byte[] packet=FrontendMenuCppFrames.request(FrontendMenuFrameV1.Action.QUERY_MENU);var row=NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(packet,4,packet.length)));NativeWire.object(row.get("frontend_menu")).set("deadline_unix_ms",StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(row))));
        }
    }
    @Test void callerCoreAddressesOwnerFlagsTargetsAndExtraFieldsCannotEnterTheRequest()throws Exception {
        for(String field:new String[]{"expected_core","actor","owner_verified","no_world","address","target","ordinal","connection_generation","unknown"}){
            byte[] packet=FrontendMenuCppFrames.request(FrontendMenuFrameV1.Action.QUERY_MENU);var row=NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(packet,4,packet.length)));NativeWire.object(row.get("frontend_menu")).put(field,true);
            assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(row))));
        }
    }
    @Test void actualNoWorldSourceRequiresAllFiveNativeGuardsAndAtomicWitness()throws Exception {
        var original=FrontendMenuCppFrames.result(FrontendMenuFrameV1.Action.QUERY_MENU,FrontendMenuFrameV1.Status.AVAILABLE);
        for(String field:new String[]{"application_verified","gui_context_verified","global_root_verified","route_root_visible","no_world"}){
            var row=NativeWire.object(NativeWire.parse(original.bytes()));NativeWire.object(row.get("source")).put(field,false);assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(row))));
        }
        for(String field:new String[]{"source","owner_witness"}){var row=NativeWire.object(NativeWire.parse(original.bytes()));row.putNull(field);assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(row))));}
        var absent=NativeWire.object(NativeWire.parse(original.bytes()));absent.put("facts_available",false);assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(absent))));
    }
    @Test void wrongCurrentTupleOrInventedProcessWorldSaveFlagsAreRejected()throws Exception {
        var original=FrontendMenuCppFrames.result(FrontendMenuFrameV1.Action.QUIT_MENU,FrontendMenuFrameV1.Status.EXIT_REQUESTED);
        for(String field:new String[]{"game_version","executable_sha256","adapter_id","backend"}){var row=NativeWire.object(NativeWire.parse(original.bytes()));row.put(field,"old-or-forged");assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(row))));}
        for(String field:new String[]{"world_core_fabricated","application_exit_confirmed","game_started_confirmed","physical_save_confirmed"}){var row=NativeWire.object(NativeWire.parse(original.bytes()));row.put(field,true);assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(row))));}
        var extra=NativeWire.object(NativeWire.parse(original.bytes()));extra.put("native_handled",true);assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(extra))));
    }
    @Test void voidQuitCannotBeAvailableQueryOrInventPostSelection()throws Exception {
        var original=FrontendMenuCppFrames.result(FrontendMenuFrameV1.Action.QUIT_MENU,FrontendMenuFrameV1.Status.EXIT_REQUESTED);
        for(String field:new String[]{"native_returned","effect_attempted"}){var row=NativeWire.object(NativeWire.parse(original.bytes()));row.put(field,false);assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(row))));}
        var selected=NativeWire.object(NativeWire.parse(original.bytes()));selected.put("post_selection_verified",true);assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(selected))));
        var claim=NativeWire.object(NativeWire.parse(original.bytes()));claim.put("claim_sequence","0");assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(claim))));
    }
    @Test void fixedRobertSourceCannotBeConfiguredOrPromotedWithoutExactModelKeys()throws Exception {
        var original=FrontendMenuCppFrames.result(FrontendMenuFrameV1.Action.QUERY_MENU,FrontendMenuFrameV1.Status.AVAILABLE);var row=NativeWire.object(NativeWire.parse(original.bytes()));var source=NativeWire.object(row.get("source"));
        source.put("robert_source_verified",true).putNull("selected_bookmark_key").putNull("selected_character_key");assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(row))));
        source.put("robert_source_verified",false).put("start_admissible",true);assertThrows(IllegalArgumentException.class,()->FrontendMenuFrameV1.decode(new RawJson(StrictJson.canonical(row))));
    }
}
