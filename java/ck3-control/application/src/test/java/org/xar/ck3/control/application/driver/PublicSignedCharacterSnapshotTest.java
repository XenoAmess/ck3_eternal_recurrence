package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Synthetic framed Native DATA -> original Driver manifest -> actual assembler -> public serializer.
 * No negative-ID live packet, current source/Managed authority, private positive-domain qualification or Game pass is claimed. */
final class PublicSignedCharacterSnapshotTest {
    private record Original(DriverObservationAssembler.Complete complete,RawJson originalDriver,RawJson originalState) { }
    private static Original original(int actor) {
        NativeCharacterId.of(BigInteger.valueOf(actor));
        String wire=DriverStateAssemblerTest.WIRE;
        wire=wire.replace(String.valueOf((char)34)+"episode_character_id"+(char)34+":73",String.valueOf((char)34)+"episode_character_id"+(char)34+":"+actor);
        byte[] raw=wire.getBytes(StandardCharsets.UTF_8);var driver=new RawJson(raw);var source=ref("driver-"+actor+".json",raw);
        var known=DriverFactsRepository.imported(source,raw,3,7,DriverStateAssemblerTest.game(),new Obj(java.util.Map.of()));
        String state=DriverObservationAssemblerTest.STATE.replace(String.valueOf((char)34)+"character_id"+(char)34+":73,"+(char)34+"alive"+(char)34+":true",
                String.valueOf((char)34)+"character_id"+(char)34+":"+actor+","+(char)34+"alive"+(char)34+":true");
        var actual=DriverObservationAssemblerTest.actual(state);
        var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(9),2,DriverStateAssemblerTest.source(),new Obj(java.util.Map.of()),source);
        var facts=DriverObservationEvidenceReader.decode(ref("facts-"+actor+".json",manifest.bytes()),manifest,driver,actual);
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,ref("native-"+actor+".bin",actual.originalPacket())));
        return new Original(complete,driver,actual.state());
    }
    @Test void signedGenericActorKeepsOriginalSignAcrossNativeDriverManifestHistoryAndSemanticPublicLanes() {
        for(int actor:List.of(Integer.MIN_VALUE,-2,0,1,Integer.MAX_VALUE)) {
            var original=original(actor);var actual=original.complete();byte[] before=DriverJson.encode(actual.semantic());
            var full=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(actual,true));var restored=PublicSnapshotCodec.decode(full);
            assertEquals(actual.semantic(),restored);
            var publicTree=DriverJson.object(full.bytes(),RawJson.MAXIMUM_BYTES);
            assertEquals(BigInteger.valueOf(actor),integer(object(publicTree.get("played_character"),"actual player").get("character_id"),"character_id"));
            assertEquals(BigInteger.valueOf(actor),integer(publicTree.get("episode_character_id"),"episode actor"));
            assertEquals(BigInteger.valueOf(actor),integer(object(restored.get("played_character"),"restored player").get("character_id"),"character_id"));
            assertEquals(actual.semantic().get("native_command_history"),restored.get("native_command_history"));
            var semantic=PublicSnapshotCodec.decodeSemanticOnly(PublicSnapshotCodec.exportSemanticOnly(actual));
            assertEquals(BigInteger.valueOf(actor),integer(object(semantic.get("played_character"),"semantic player").get("character_id"),"character_id"));
            for(String key:List.of("native_command_history","native_rollback_war_failure","native_rollback_war_failures"))assertFalse(semantic.members().containsKey(key));
            assertArrayEquals(before,DriverJson.encode(actual.semantic()));
        }
    }
    @Test void invalidActorDomainsAreRefusedAtThePublicBoundaryWithoutSignedUnsignedAliases() {
        Obj valid=DriverJson.object(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(original(-2).complete(),true)).bytes(),RawJson.MAXIMUM_BYTES);
        for(Value invalid:List.of(new IntegerValue(BigInteger.valueOf(-1)),new IntegerValue(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),new IntegerValue(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)),new Bool(true),new DecimalValue("1.0"),new Text("-2"),Nil.INSTANCE)) {
            var changed=valid.with("played_character",object(valid.get("played_character"),"actual player").with("character_id",invalid));
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(PublicDataJson.encodeTyped(changed)));
            var episode=valid.with("episode_character_id",invalid);
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(PublicDataJson.encodeTyped(episode)));
        }
        assertThrows(IllegalArgumentException.class,()->original(-1));
    }
    private static ExactRef ref(String name,byte[] bytes) {return new ExactRef(Path.of(System.getProperty("java.io.tmpdir"),"xar-signed-character-data",name).toAbsolutePath().toString(),bytes.length,DriverJson.sha256(bytes));}
}
