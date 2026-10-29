package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared original-identity field contract; no private SAVE authority is manufactured. */
public final class CheckpointFileWitnessCodecTest {
    private static CheckpointPair.FileWitness actual(){
        return new CheckpointPair.FileWitness(new ExactRef(Path.of("checkpoint-material.json").toAbsolutePath().toString(),17,"a".repeat(64)),
                new FileStatIdentity(BigInteger.valueOf(17),"9007199254740993","13400000000000000100"));
    }
    @Test void sharedWitnessRoundTripRetainsEveryDecimalDigit(){
        var witness=actual();var json=CheckpointPairCodec.fileWitnessToJson(witness);
        assertEquals(witness,CheckpointPairCodec.fileWitnessFromJson(StrictJson.parse(StrictJson.canonical(json))));
        assertTrue(json.get("identity").get("file_id").isTextual());
        assertEquals("9007199254740993",json.get("identity").get("file_id").textValue());
    }
    @Test void missingNullUnknownAndIntegerAliasesFailTheSameSharedConsumer(){
        for(String field:List.of("ref","identity_schema","identity")){
            var missing=CheckpointPairCodec.fileWitnessToJson(actual());missing.remove(field);
            assertThrows(Exception.class,()->CheckpointPairCodec.fileWitnessFromJson(missing));
            var nul=CheckpointPairCodec.fileWitnessToJson(actual());nul.putNull(field);
            assertThrows(Exception.class,()->CheckpointPairCodec.fileWitnessFromJson(nul));
        }
        var extra=CheckpointPairCodec.fileWitnessToJson(actual());extra.put("file_id",true);
        assertThrows(Exception.class,()->CheckpointPairCodec.fileWitnessFromJson(extra));
        var numeric=CheckpointPairCodec.fileWitnessToJson(actual());((ObjectNode)numeric.get("identity")).put("file_id",9007199254740993L);
        assertThrows(Exception.class,()->CheckpointPairCodec.fileWitnessFromJson(numeric));
        var floating=CheckpointPairCodec.fileWitnessToJson(actual());((ObjectNode)floating.get("identity")).put("bytes",17.0);
        assertThrows(Exception.class,()->CheckpointPairCodec.fileWitnessFromJson(floating));
        var mismatched=CheckpointPairCodec.fileWitnessToJson(actual());((ObjectNode)mismatched.get("identity")).put("bytes",18);
        assertThrows(Exception.class,()->CheckpointPairCodec.fileWitnessFromJson(mismatched));
    }
    @Test void firstMaterialCannotDecodeOrdinaryCycleMaterialOrAnEnvelopeWithExtraFields(){
        var ordinary=StrictJson.object();ordinary.put("schema",SavedAttachmentSourceStore.MATERIAL_SCHEMA);
        assertThrows(Exception.class,()->SavedFirstCheckpointMaterialStore.decode(StrictJson.canonical(ordinary)));
        var malformed=StrictJson.object();malformed.put("schema",SavedFirstCheckpointMaterialStore.SCHEMA);
        for(String key:List.of("pair","session","opening_semantic","begin","original_writer_head","original_writer_head_sha256","first_checkpoint_binding_sha256"))malformed.putNull(key);
        malformed.put("completed_cycles",0);
        assertThrows(Exception.class,()->SavedFirstCheckpointMaterialStore.decode(StrictJson.canonical(malformed)));
    }
}
