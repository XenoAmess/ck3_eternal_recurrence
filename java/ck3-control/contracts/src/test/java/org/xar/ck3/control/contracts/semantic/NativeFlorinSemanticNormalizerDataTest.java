package org.xar.ck3.control.contracts.semantic;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Explicit versioned normalizer DATA examples, not a Native/C++ full-packet oracle, live frame or readiness permit. */
final class NativeFlorinSemanticNormalizerDataTest {
    private static final BigInteger REVISION=BigInteger.valueOf(9);
    private static final JsonNodeFactory JSON=JsonNodeFactory.instance;
    private static JsonNode parse(String value){return FullJsonTree.parse(value.getBytes(StandardCharsets.UTF_8),65536);}
    private static ObjectNode identity(String schema){
        return JSON.objectNode().put("schema",schema).put("game_version",ExactCk3Build.CK3_1210.version())
                .put("executable_sha256",ExactCk3Build.CK3_1210.executableSha256())
                .put("adapter_id",NativePlayedCharacter.FLORIN_ADAPTER).put("backend",NativePlayedCharacter.FLORIN_BACKEND);
    }
    private static ObjectNode actor(){
        var actor=identity(NativePlayedCharacter.FLORIN_SCHEMA).put("character_id",-2130706431).put("alive",true).put("stress_points",42)
                .put("has_heir",true).put("primary_heir_id",Integer.MIN_VALUE).put("betrothed_id",0).put("primary_spouse_id",-2113929214);
        actor.putArray("spouse_ids").add(-2113929214).add(0);return actor;
    }
    private static ObjectNode state(){
        var root=identity(NativeSemanticNormalizer.FLORIN_SCHEMA).put("date_raw",123456).put("paused",true).put("map_ready",true);
        root.set("played_character",actor());root.putArray("history");return root;
    }
    private static ObjectNode normalize(ObjectNode raw){
        return NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(raw),"normalizer-data-snapshot",REVISION).semantic();
    }
    private static void reject(Consumer<ObjectNode> mutation){
        var raw=state();mutation.accept(raw);assertThrows(IllegalArgumentException.class,()->normalize(raw));
    }
    private static ObjectNode played(ObjectNode root){return (ObjectNode)root.get("played_character");}
    private static ObjectNode unmarked(ObjectNode original){
        var result=original.deepCopy();
        for(String key:List.of("schema","game_version","executable_sha256","adapter_id","backend"))result.remove(key);
        return result;
    }

    @Test void explicitFlorinDataRetainsSignedActorHeirFamilyAndItsMarkersAcrossReplay(){
        var raw=state();var captured=NativeSemanticNormalizer.original(raw);
        var semantic=NativeSemanticNormalizer.normalize(captured,"normalizer-data-snapshot",REVISION).semantic();
        var actual=played(semantic);
        assertEquals(-2130706431,actual.get("character_id").intValue());assertEquals(Integer.MIN_VALUE,actual.get("primary_heir_id").intValue());
        assertEquals(0,actual.get("betrothed_id").intValue());assertEquals(-2113929214,actual.get("primary_spouse_id").intValue());
        assertEquals(-2113929214,actual.get("spouse_ids").get(0).intValue());assertEquals(0,actual.get("spouse_ids").get(1).intValue());
        assertEquals("native",actual.get("source").textValue());assertEquals(42,actual.get("stress_points").intValue());
        for(String key:List.of("schema","game_version","executable_sha256","adapter_id","backend")){
            assertEquals(raw.get(key),semantic.get(key));assertEquals(played(raw).get(key),actual.get(key));
        }
        assertEquals(semantic,normalize(semantic),"the marked canonical actor must re-enter the same explicit version branch");
        raw.put("schema","mutated after Raw capture");played(raw).put("character_id",1);
        assertEquals(semantic,NativeSemanticNormalizer.normalize(captured,"normalizer-data-snapshot",REVISION).semantic());
    }

    @Test void legacyPathKeepsItsIndependentNonnegativeFamilyRulesAndTransparentUnknownMetadata(){
        var signed=unmarked(actor());
        assertThrows(IllegalArgumentException.class,()->NativePlayedCharacter.normalize(signed,REVISION,parse("123456")));
        var versionOnly=state();versionOnly.remove("schema");played(versionOnly).remove("schema");
        assertThrows(IllegalArgumentException.class,()->normalize(versionOnly),"version and SHA alone must not select Florin");
        var legacy=JSON.objectNode().put("character_id",-2).put("alive",true).put("stress_points",0).put("has_heir",false);
        legacy.putNull("betrothed_id").putNull("primary_spouse_id");legacy.putArray("spouse_ids");
        var before=NativePlayedCharacter.normalize(legacy,REVISION,parse("123456"));
        var withMetadata=legacy.deepCopy().put("schema","legacy-actor-metadata").put("game_version","unreviewed");
        assertArrayEquals(FullJsonTree.encode(before,65536),FullJsonTree.encode(NativePlayedCharacter.normalize(withMetadata,REVISION,parse("123456")),65536));
        var bare=JSON.objectNode().put("date_raw",123456);bare.set("played_character",legacy);
        var tagged=bare.deepCopy().put("schema","legacy-root-schema").put("game_version","1.21.0")
                .put("executable_sha256",ExactCk3Build.CK3_1210.executableSha256());
        var normalized=normalize(tagged);assertEquals("legacy-root-schema",normalized.get("schema").textValue());
        for(String key:List.of("schema","game_version","executable_sha256"))normalized.remove(key);
        assertEquals(normalize(bare),normalized);
    }

    @Test void missingWrongAndMixedFlorinMarkersAndEverySourceTupleFieldAreRejected(){
        for(String field:List.of("schema","game_version","executable_sha256","adapter_id","backend")){
            reject(root->root.remove(field));reject(root->played(root).remove(field));
        }
        reject(root->root.put("schema","ck3_1210_full_state_v2"));
        reject(root->played(root).put("schema","ck3_1210_played_character_v2"));
        reject(root->root.put("game_version","1.21.0.0"));reject(root->played(root).put("game_version","1.21.0 (Florin)"));
        reject(root->root.put("executable_sha256",ExactCk3Build.CK3_12004.executableSha256()));
        reject(root->played(root).put("executable_sha256",ExactCk3Build.CK3_12004.executableSha256()));
        reject(root->root.put("adapter_id","ck3-1.20.0.4-msvc-x64"));reject(root->played(root).put("backend","native-headless"));
        reject(root->root.put("backend",true));reject(root->played(root).put("adapter_id",42));
        var missing=actor();missing.remove("schema");
        assertThrows(IllegalArgumentException.class,()->NativePlayedCharacter.normalizeFlorin(missing,REVISION,parse("123456")));
    }

    @Test void invalidIdentityTokensNeverNarrowCoerceOrTurnTheAbsentSentinelIntoAnId(){
        for(String token:List.of("-1","-2147483649","2147483648","4294967294","true","1.0","null","\"-2\"")){
            reject(root->played(root).set("character_id",parse(token)));
            reject(root->played(root).set("primary_heir_id",parse(token)));
            reject(root->{played(root).putArray("spouse_ids").add(parse(token));played(root).set("primary_spouse_id",parse(token));});
        }
        for(String token:List.of("-1","-2147483649","2147483648","4294967294","true","1.0","\"-2\""))
            reject(root->played(root).set("betrothed_id",parse(token)));
    }

    @Test void completeRelationsMembershipNoDuplicatesAndNonnegativeFullStressRemainMandatory(){
        for(String field:List.of("betrothed_id","primary_spouse_id","spouse_ids"))reject(root->played(root).remove(field));
        reject(root->played(root).putArray("spouse_ids").add(-2113929214).add(-2113929214));
        reject(root->played(root).put("primary_spouse_id",-2));
        reject(root->played(root).put("stress_points",-1));reject(root->played(root).put("stress_points",2147483648L));
        reject(root->played(root).put("stress_points",true));reject(root->played(root).put("stress_points",1.0));
        var old=unmarked(actor()).put("primary_heir_id",1).put("betrothed_id",0).put("primary_spouse_id",0).put("stress_points",-1);
        old.putArray("spouse_ids").add(0);
        assertThrows(IllegalArgumentException.class,()->NativePlayedCharacter.normalize(old,REVISION,parse("123456")));
    }

    @Test void explicitNullIsAbsenceAndAnAbsentActorDoesNotMintAnIdentityOrFreshnessRole(){
        var nullActor=state();nullActor.putNull("played_character");assertTrue(normalize(nullActor).get("played_character").isNull());
        var noActor=state();noActor.remove("played_character");assertTrue(normalize(noActor).get("played_character").isNull());
        var noRelations=state();var original=played(noRelations).put("has_heir",false).putNull("primary_heir_id")
                .putNull("betrothed_id").putNull("primary_spouse_id");original.putArray("spouse_ids");
        var semantic=played(normalize(noRelations));assertTrue(semantic.get("primary_heir_id").isNull());
        assertTrue(semantic.get("betrothed_id").isNull());assertTrue(semantic.get("primary_spouse_id").isNull());assertEquals(0,semantic.get("spouse_ids").size());
        original.remove("primary_heir_id");assertThrows(IllegalArgumentException.class,()->normalize(noRelations));
        assertThrows(IllegalArgumentException.class,()->normalize(state().put("schema","wrong root marker")));
    }
}
