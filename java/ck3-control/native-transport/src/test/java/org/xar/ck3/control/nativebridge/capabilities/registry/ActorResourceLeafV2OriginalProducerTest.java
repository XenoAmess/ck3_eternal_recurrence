package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Locale;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;

/** Owner-only cold-read source: fixture properties must name actual C++ output, never static templates. */
final class ActorResourceLeafV2OriginalProducerTest {
    private static RawJson original(String kind)throws Exception {
        String prefix="xar.resource.leaf.v2."+kind;
        String file=System.getProperty(prefix+".file"),sha=System.getProperty(prefix+".sha256");
        assertNotNull(file,"NOT_RUN: actual Native formatter stdout path required: "+prefix);
        assertNotNull(sha,"NOT_RUN: actual Native original SHA required: "+prefix);
        Path path=Path.of(file);assertTrue(path.isAbsolute(),"absolute original producer path required");
        assertTrue(sha.matches("[0-9A-Fa-f]{64}"),"exact original SHA256 required");
        byte[] bytes=Files.readAllBytes(path);
        assertEquals(sha.toLowerCase(Locale.ROOT),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return new RawJson(bytes);
    }
    private static ActorResourceLeafV2 read(String kind)throws Exception {
        return ActorResourceLeafV2.decodePacket(original(kind),"ram-resource-leaf-v2");
    }
    private static ObjectNode partial()throws Exception {
        var packet=RegistryJson.object(original("partial"));return RegistryJson.object(packet.get("result")).deepCopy();
    }
    private static void reject(Consumer<ObjectNode> mutation)throws Exception {
        ObjectNode row=partial();mutation.accept(row);
        assertThrows(IllegalArgumentException.class,()->ActorResourceLeafV2.decode(RegistryJson.encode(row)));
    }
    @Test void actualOriginalSignedResourceExitPreservesPartialUnknownAndFrame()throws Exception {
        var p=assertInstanceOf(ActorResourceLeafV2.Partial.class,read("partial"));
        var consumed=p.observedNonCash().orElseThrow();
        assertEquals(-2130706431,consumed.actorCharacterId());assertEquals(p.coreBefore(),consumed.core());
        assertEquals(Long.MIN_VALUE,consumed.prestige().raw());assertEquals(Long.MAX_VALUE,consumed.piety().raw());
        assertEquals(100000,consumed.prestige().scale());assertEquals(-500000,p.goldInterval().before().raw());
        assertEquals(ActorResourceLeafV2.RENOWN_UNKNOWN,p.renown().reason());
        assertEquals(ActorResourceLeafV2.TREASURY_UNKNOWN,p.trueTreasury().reason());
        assertEquals(p,ActorResourceLeafV2.decode(ActorResourceLeafV2.encode(p)));
        var encoded=RegistryJson.object(ActorResourceLeafV2.encode(p));
        assertFalse(encoded.get("complete_snapshot").booleanValue());assertFalse(encoded.get("root_ready").booleanValue());
        assertTrue(encoded.path("resources").path("true_treasury").path("amount").isNull());
        assertTrue(encoded.path("resources").path("renown").path("amount").isNull());
        var u=assertInstanceOf(ActorResourceLeafV2.Unavailable.class,read("unavailable"));
        assertTrue(u.observedNonCash().isEmpty());assertEquals(u,ActorResourceLeafV2.decode(ActorResourceLeafV2.encode(u)));
        assertThrows(IllegalArgumentException.class,()->ActorResourceLeafV2.decodePacket(original("partial"),"wrong-original-request"));
    }
    @Test void exactSourceFrameUnitsAndUnknownCannotBeBroadened()throws Exception {
        reject(r->r.put("game_version","1.20.0.4"));
        reject(r->r.put("executable_sha256","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"));
        reject(r->r.put("source_kind","personal_cash_is_treasury"));
        reject(r->((ObjectNode)r.get("getter_sources")).put("prestige","0x2DA2818"));
        reject(r->r.put("actor_character_id",7));
        reject(r->r.put("source_identity_verified",false));
        reject(r->r.put("formal_action_ready",true));
        reject(r->((ObjectNode)r.get("core_after")).put("date_raw",123457));
        reject(r->((ObjectNode)r.get("core_after")).put("played_character_id",0));
        reject(r->((ObjectNode)r.path("personal_gold_interval").path("after")).put("raw",-499999));
        reject(r->((ObjectNode)r.path("resources").path("prestige").path("amount")).put("scale",1000));
        reject(r->((ObjectNode)r.path("resources").path("piety").path("amount")).put("raw",true));
        reject(r->((ObjectNode)r.path("resources").path("piety").path("amount")).put("raw",1.0));
        reject(r->((ObjectNode)r.path("resources").path("piety").path("amount")).put("raw","0"));
        reject(r->((ObjectNode)r.get("resources")).remove("piety"));
        reject(r->{var treasury=(ObjectNode)r.path("resources").path("true_treasury");
            treasury.put("status","available").putNull("unavailable_reason");
            treasury.putObject("amount").put("raw",0).put("scale",100000);});
        reject(r->((ObjectNode)r.path("resources").path("renown")).put("unavailable_reason","wallet_has_no_renown"));
        ObjectNode zero=partial();
        ((ObjectNode)zero.path("resources").path("prestige").path("amount")).put("raw",0);
        ((ObjectNode)zero.path("resources").path("piety").path("amount")).put("raw",0);
        var values=ActorResourceLeafV2.decode(RegistryJson.encode(zero)).observedNonCash().orElseThrow();
        assertEquals(0,values.prestige().raw());assertEquals(0,values.piety().raw());
        assertThrows(IllegalArgumentException.class,()->ActorResourceLeafV2.decode(new RawJson(
                "{\"schema\":\"x\",\"schema\":\"ck3_1210_actor_resource_leaf_v2\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }
}
