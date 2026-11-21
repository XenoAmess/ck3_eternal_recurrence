package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1PublicCodec;

/** Actual C++ serializer DATA and strict Java boundaries, without Game or effect qualification. */
final class NativeRiteDoctrine26785313ProducerTest {
    @FunctionalInterface private interface Edit {void apply(com.fasterxml.jackson.databind.node.ObjectNode row)throws Exception;}
    private static RawJson changed(String file,Edit edit)throws Exception {
        var row=NativeWire.object(NativeWire.parse(RiteDoctrineCppFrames.result(file).bytes()));edit.apply(row);return new RawJson(StrictJson.canonical(row));
    }
    @Test void actualFourRequestsRoundtripWithExactUnsignedLeaseAndOriginalCore()throws Exception {
        String output=System.getProperty("xar.current.rite.java.request.output");
        for(var action:RiteDoctrineFrameV1.Action.values()){
            var request=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(RiteDoctrineCppFrames.json(action.wire()+"-request.json")));
            assertEquals(action,request.action());assertEquals(-16777215,request.expectedCore().prefix().playedCharacterId());
            if(action==RiteDoctrineFrameV1.Action.QUERY)assertTrue(request.lease().isEmpty());else assertEquals(new BigInteger("18446744073709551615"),request.lease().orElseThrow().providerGeneration());
            byte[] encoded=NativeWire.execute("java-contract-"+action.wire(),RiteDoctrineFrameV1.STEP,BigInteger.ZERO,RiteDoctrineFrameV1PublicCodec.additionalFields(request).bytes());
            assertEquals(request,RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(encoded));
            // Optional small test artifact, never a production runner or Native receipt. Actual NoGame qualification supplies a fresh D root.
            if(output!=null){Path dir=Path.of(output).toAbsolutePath().normalize();assertEquals(Path.of("D:/").getRoot(),dir.getRoot());Files.write(dir.resolve(action.wire()+"-java-request.json"),java.util.Arrays.copyOfRange(encoded,4,encoded.length),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);}
        }
    }
    @Test void allSevenActualResultOriginalsRoundtripWithoutPromotingPersistence()throws Exception {
        for(String file:new String[]{"query-SYNTHETIC-DATA.json","category-opened-SYNTHETIC-DATA.json","selected-SYNTHETIC-DATA.json","confirmation-dispatched-SYNTHETIC-DATA.json","indeterminate-SYNTHETIC-DATA.json","pam-unresolved-SYNTHETIC-DATA.json","unavailable-NoGame.json"}){
            var actual=RiteDoctrineCppFrames.response(file);var frame=RiteDoctrineFrameV1PublicCodec.decodePacket(new RawJson(actual.payload().value()),actual.requestId());
            assertEquals(actual.nativeOk(),frame.nativeOk());assertEquals(frame,RiteDoctrineFrameV1.decode(RiteDoctrineFrameV1PublicCodec.encode(frame)));
            var encoded=NativeWire.object(NativeWire.parse(RiteDoctrineFrameV1PublicCodec.encode(frame).bytes()));assertFalse(encoded.get("rite_edit_confirmed").booleanValue());assertFalse(encoded.get("physical_save_confirmed").booleanValue());
        }
    }
    @Test void actualMissingGameRefusalEchoesOriginalLeaseAndNoEffect()throws Exception {
        var actual=RiteDoctrineCppFrames.response("effect-early-unavailable-NoGame.json");var frame=RiteDoctrineFrameV1PublicCodec.decodePacket(new RawJson(actual.payload().value()),actual.requestId());
        assertFalse(actual.nativeOk());assertEquals(RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,frame.action());assertEquals(RiteDoctrineFrameV1.Status.UNAVAILABLE,frame.status());
        assertEquals(new BigInteger("18446744073709551615"),frame.providerGeneration());assertEquals(frame.providerGeneration(),frame.querySequence());assertEquals(BigInteger.ZERO,frame.claimSequence());
        assertFalse(frame.effectAttempted());assertFalse(frame.nativeReturned());assertTrue(frame.facts().isEmpty());assertTrue(frame.ownerWitness().isEmpty());
        assertEquals(frame,RiteDoctrineFrameV1.decode(RiteDoctrineFrameV1PublicCodec.encode(frame)));
    }
    @Test void falseKnownIsUnresolvedPamRatherThanAnEntireOrFalse()throws Exception {
        var frame=RiteDoctrineFrameV1.decode(RiteDoctrineCppFrames.result("pam-unresolved-SYNTHETIC-DATA.json"));
        assertEquals(RiteDoctrineFrameV1.Status.AVAILABLE,frame.status());assertTrue(frame.facts().isPresent());assertFalse(frame.facts().orElseThrow().pamGateAvailable());assertFalse(frame.facts().orElseThrow().selectable());
    }
    @Test void postSelectedIsSeparateFromBeforeFactsAndConfirmationIsOnlyDispatch()throws Exception {
        var selected=RiteDoctrineFrameV1.decode(RiteDoctrineCppFrames.result("selected-SYNTHETIC-DATA.json"));assertTrue(selected.postSelectedEvaluated());assertTrue(selected.postSelected());
        var confirmed=RiteDoctrineFrameV1.decode(RiteDoctrineCppFrames.result("confirmation-dispatched-SYNTHETIC-DATA.json"));assertEquals(RiteDoctrineFrameV1.Status.CONFIRMATION_DISPATCHED,confirmed.status());assertTrue(confirmed.nativeHandled());assertTrue(confirmed.facts().orElseThrow().confirmable());
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed("confirmation-dispatched-SYNTHETIC-DATA.json",row->row.put("rite_edit_confirmed",true))));
    }
    @Test void malformedFactsNullsForeignTupleUnknownAndDuplicateFieldsReject()throws Exception {
        String file="query-SYNTHETIC-DATA.json";
        for(String field:new String[]{"schema","facts","owner_witness","core_frame","facts_available"})assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->row.remove(field))));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->row.putNull("facts"))));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->row.put("unrelated",false))));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->row.put("adapter_id","ck3-1.20.0.4-msvc-x64"))));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->NativeWire.object(row.get("core_frame")).put("game_version","1.20.0.4"))));
        byte[] original=RiteDoctrineCppFrames.result(file).bytes();String text=new String(original,java.nio.charset.StandardCharsets.UTF_8);assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(new RawJson(text.replaceFirst("\\{","{\"schema\":\"duplicate\",").getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }
    @Test void canonicalSignedFixedPointAndUnsignedWitnessBoundariesAreExact()throws Exception {
        String file="query-SYNTHETIC-DATA.json";
        for(String token:new String[]{"+1","01","-0","9223372036854775808","-9223372036854775809","1.0"})assertThrows(RuntimeException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->NativeWire.object(row.get("facts")).put("piety_cost_raw",token))));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->NativeWire.object(row.get("facts")).put("piety_cost_raw",1))));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->NativeWire.object(row.get("facts")).put("raw_scale",100000.0))));
        for(String token:new String[]{"-1","+1","01","18446744073709551616"})assertThrows(RuntimeException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->row.put("provider_generation",token))));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed(file,row->NativeWire.object(row.get("owner_witness")).put("connection_generation","0"))));
        for(String token:new String[]{"-9223372036854775808","9223372036854775807"})assertEquals(Long.parseLong(token),RiteDoctrineFrameV1.decode(changed(file,row->NativeWire.object(row.get("facts")).put("piety_cost_raw",token))).facts().orElseThrow().pietyCostRaw());
    }
    @Test void envelopeOkCannotOverrideIncoherentActualResult()throws Exception {
        var raw=NativeWire.object(NativeWire.parse(RiteDoctrineCppFrames.json("indeterminate-SYNTHETIC-DATA.json")));String id=NativeWire.text(raw.get("request_id"));raw.put("ok",true);
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1PublicCodec.decodePacket(new RawJson(StrictJson.canonical(raw)),id));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(changed("selected-SYNTHETIC-DATA.json",row->row.put("post_selected",false))));
    }
}
