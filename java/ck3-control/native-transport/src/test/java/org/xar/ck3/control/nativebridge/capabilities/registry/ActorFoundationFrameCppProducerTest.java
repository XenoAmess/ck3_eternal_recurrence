package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;

/** Four original C++ command_result packets are the positive oracle. Mutations below are only invalid grammar DATA. */
final class ActorFoundationFrameCppProducerTest {
    private static final String RESOURCE="/org/xar/ck3/control/nativebridge/capabilities/registry/actor-foundation1210/";
    private record Sample(String name,int bytes,String sha){ }
    private static final List<Sample> SAMPLES=List.of(
            new Sample("empty",1582,"e7c66e80cd0f45e238de06957de5b7e9789bdfae51f0c7c3c5d2b85e0dff57a0"),
            new Sample("nonempty",1613,"32402538d29b5cc366a1877e5b535a26d7baf3159af243aca94b3c04963a7f8f"),
            new Sample("partial",1520,"da062a2496a134653744af75aeb65018489d1420da29d50c1b7fc8aea9348936"),
            new Sample("unavailable",1467,"cc351f3cd22c3094ec7a4943c4ce5d51a506823da46619f3f3803c469a18f7bc"));
    private static RawJson packet(String name)throws Exception {
        var sample=SAMPLES.stream().filter(row->row.name().equals(name)).findFirst().orElseThrow();
        String filename="actor-foundation-producer-"+name+"01.json";byte[] bytes;
        try(var stream=ActorFoundationFrameCppProducerTest.class.getResourceAsStream(RESOURCE+filename)){
            if(stream!=null)bytes=stream.readAllBytes();
            else{
                String root=System.getProperty("xar.native.actor-foundation1210.fixtures");
                if(root==null||root.isBlank()||!Path.of(root).isAbsolute())throw new IOException("NOT_RUN: classpath actor-foundation1210 resources or absolute fixture fallback required");
                bytes=Files.readAllBytes(Path.of(root).resolve(filename));
            }
        }
        assertEquals(sample.bytes(),bytes.length);assertEquals(sample.sha(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return new RawJson(bytes);
    }
    private static ActorFoundationFrame decode(String name)throws Exception {
        return ActorFoundationFramePublicCodec.decodePacket(packet(name),"foundation-"+name+"-fixture");
    }
    private static ObjectNode result(String name)throws Exception{return RegistryJson.object(RegistryJson.object(packet(name)).get("result"));}
    private static void reject(Consumer<ObjectNode> mutation)throws Exception {
        var changed=result("nonempty").deepCopy();mutation.accept(changed);
        assertThrows(IllegalArgumentException.class,()->ActorFoundationFrame.decode(RegistryJson.encode(changed)));
    }

    @Test void fourActualCppPacketsRoundTripWithoutTurningPartialDataIntoACompleteObservation()throws Exception {
        for(var sample:SAMPLES){
            var frame=decode(sample.name());assertEquals(ExactCk3Build.CK3_1210,frame.build());
            var encoded=ActorFoundationFramePublicCodec.encode(frame);
            assertEquals(result(sample.name()),RegistryJson.object(encoded));
            assertEquals(frame,ActorFoundationFrame.decode(encoded));
            var raw=RegistryJson.object(encoded);
            assertFalse(raw.get("complete_snapshot").booleanValue());assertFalse(raw.get("treasury_observed").booleanValue());
            assertFalse(raw.get("monthly_flow_observed").booleanValue());
            assertEquals("query-actor-foundation-frame-v1",raw.get("step").textValue());
            assertEquals("ck3_1210_actor_foundation_frame_v1",raw.get("schema").textValue());
        }
    }

    @Test void actualSignedResourcesAndNativeRelationshipOrderKeepZeroNegativeAndKnownEmptySemantics()throws Exception {
        var empty=assertInstanceOf(ActorFoundationFrame.Partial.class,decode("empty"));
        var resources=assertInstanceOf(ActorFoundationFrame.AvailableResources.class,empty.resources());
        assertEquals(12345000L,resources.gold().raw());assertEquals(-200000L,resources.prestige().raw());
        assertEquals(0L,resources.piety().raw());assertEquals(100000,resources.piety().scale());assertEquals(42,resources.stressPoints());
        assertEquals(-2130706431,empty.coreFrame().prefix().playedCharacterId());
        var family=assertInstanceOf(ActorFoundationFrame.AvailableRelationships.class,empty.relationships());
        assertEquals(-1,family.betrothedCharacterId());assertEquals(-1,family.primarySpouseCharacterId());assertEquals(List.of(),family.spouseCharacterIds());
        var nonempty=assertInstanceOf(ActorFoundationFrame.Partial.class,decode("nonempty"));
        var original=assertInstanceOf(ActorFoundationFrame.AvailableRelationships.class,nonempty.relationships());
        assertEquals(50331651,original.betrothedCharacterId());assertEquals(-2113929214,original.primarySpouseCharacterId());
        assertEquals(List.of(-2113929214,0),original.spouseCharacterIds());
        assertThrows(UnsupportedOperationException.class,()->original.spouseCharacterIds().add(1));
    }

    @Test void independentlyUnavailableRelationshipGroupStaysNullAndDoesNotEraseTheActualResources()throws Exception {
        var partial=assertInstanceOf(ActorFoundationFrame.Partial.class,decode("partial"));
        assertInstanceOf(ActorFoundationFrame.AvailableResources.class,partial.resources());
        assertEquals(new ActorFoundationFrame.UnavailableRelationships("family_header_invalid"),partial.relationships());
        var partialRaw=RegistryJson.object(ActorFoundationFramePublicCodec.encode(partial));assertTrue(partialRaw.get("relationships").isNull());
        assertTrue(partialRaw.get("foundation_available").booleanValue());assertTrue(partialRaw.get("resources_available").booleanValue());
        assertFalse(partialRaw.get("relationships_available").booleanValue());
        var unavailable=assertInstanceOf(ActorFoundationFrame.Unavailable.class,decode("unavailable"));
        assertFalse(unavailable.applicationMainObserved());assertEquals("actor_foundation_not_read",unavailable.reason());
        assertEquals(new ActorFoundationFrame.UnavailableResources("resources_not_read"),unavailable.resources());
        assertEquals(new ActorFoundationFrame.UnavailableRelationships("relationships_not_read"),unavailable.relationships());
        assertInstanceOf(CoreFrame.Unavailable.class,unavailable.coreFrame());
        var raw=RegistryJson.object(ActorFoundationFramePublicCodec.encode(unavailable));
        assertTrue(raw.get("resources").isNull());assertTrue(raw.get("relationships").isNull());
    }

    @Test void exactIdentityPartialFlagsNestedCoreAndGroupGrammarRejectDriftRatherThanCoercingIt()throws Exception {
        reject(row->row.put("step","query-personal-gold-frame-v1"));
        reject(row->row.put("schema","ck3_1210_actor_foundation_v1"));
        reject(row->row.put("game_version","1.21.0.0"));
        reject(row->row.put("executable_sha256",ExactCk3Build.CK3_12004.executableSha256()));
        reject(row->row.put("adapter_id","ck3-1.20.0.4-msvc-x64"));
        reject(row->row.put("backend","native-headless"));
        for(String name:List.of("complete_snapshot","treasury_observed","monthly_flow_observed"))reject(row->row.put(name,true));
        reject(row->row.put("foundation_available",false));reject(row->row.put("resources_available",1));
        reject(row->row.remove("relationships_unavailable_reason"));
        reject(row->((ObjectNode)row.get("core_frame")).put("application_main_observed",false));
        reject(row->{var old=CoreFramePublicCodec.encode(new CoreFrame.Partial(ExactCk3Build.CK3_12004,
                assertInstanceOf(CoreFrame.Partial.class,CoreFrame.decodeObject(RegistryJson.object(row.get("core_frame")))).prefix()));
            row.set("core_frame",RegistryJson.object(old));});
        reject(row->row.putNull("resources"));reject(row->row.put("resources_unavailable_reason","invented"));
        reject(row->((ObjectNode)((ObjectNode)row.get("resources")).get("gold")).put("raw",true));
        reject(row->((ObjectNode)((ObjectNode)row.get("resources")).get("piety")).put("scale",1));
        reject(row->((ObjectNode)row.get("resources")).put("stress_points",2147483648L));
        reject(row->row.put("relationships_available",false));
        reject(row->((ObjectNode)row.get("relationships")).put("primary_spouse_character_id",4294967295L));
        reject(row->((ObjectNode)row.get("relationships")).putArray("spouse_character_ids").add(-1));
        reject(row->((ObjectNode)row.get("relationships")).putArray("spouse_character_ids").add(true));
        reject(row->{var ids=((ObjectNode)row.get("relationships")).putArray("spouse_character_ids");for(int n=0;n<65;n++)ids.add(0);});
    }

    @Test void originalCppEnvelopeRequiresTheExactRequestAndCannotHideMissingNullDuplicateOrFalseResultFields()throws Exception {
        var packet=packet("empty");
        assertThrows(IllegalArgumentException.class,()->ActorFoundationFramePublicCodec.decodePacket(packet,"different-original"));
        var negative=RegistryJson.object(packet).deepCopy();negative.put("ok",false);
        assertThrows(IllegalArgumentException.class,()->ActorFoundationFramePublicCodec.decodePacket(RegistryJson.encode(negative),"foundation-empty-fixture"));
        var missing=RegistryJson.object(packet).deepCopy();missing.remove("result");
        assertThrows(IllegalArgumentException.class,()->ActorFoundationFramePublicCodec.decodePacket(RegistryJson.encode(missing),"foundation-empty-fixture"));
        var empty=RegistryJson.object(packet).deepCopy();empty.putNull("result");
        assertThrows(IllegalArgumentException.class,()->ActorFoundationFramePublicCodec.decodePacket(RegistryJson.encode(empty),"foundation-empty-fixture"));
        String duplicate=new String(packet.bytes(),java.nio.charset.StandardCharsets.UTF_8).replace("\"ok\":true","\"ok\":true,\"ok\":true");
        assertThrows(IllegalArgumentException.class,()->ActorFoundationFramePublicCodec.decodePacket(new RawJson(duplicate.getBytes(java.nio.charset.StandardCharsets.UTF_8)),"foundation-empty-fixture"));
    }
}
