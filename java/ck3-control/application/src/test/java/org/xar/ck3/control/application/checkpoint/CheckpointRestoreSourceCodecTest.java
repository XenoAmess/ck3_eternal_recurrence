package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict shared restore source codecs preserve decimal identity and uint64 roles across persistence. */
final class CheckpointRestoreSourceCodecTest {
    @Test void nativeAndPersistedRevisionsRetainUint64MaximumWithDistinctWireTypes(){
        BigInteger maximum=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
        assertEquals(maximum,SavedAttachmentSourceStore.nativeRevision(StrictJson.parse(maximum.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        var row=StrictJson.object();row.put("revision",maximum.toString());
        assertEquals(maximum,SavedAttachmentSourceStore.decimalRevision(row.get("revision")));
        for(String bad:List.of("true","1.0","-1","18446744073709551616","null","\"1\""))
            assertThrows(Exception.class,()->SavedAttachmentSourceStore.nativeRevision(StrictJson.parse(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        for(String bad:List.of("true","1","null","\"01\"","\"+1\"","\"18446744073709551616\""))
            assertThrows(Exception.class,()->SavedAttachmentSourceStore.decimalRevision(StrictJson.parse(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }
    @Test void sourceKindsRoundTripThroughOnlyOneStrictFieldContract(){
        var ref=new ExactRef(Path.of("original-source.json").toAbsolutePath().toString(),17,"a".repeat(64));
        var witness=new CheckpointPair.FileWitness(ref,new FileStatIdentity(BigInteger.valueOf(17),"9007199254740993","13400000000000000100"));
        for(var kind:SavedCheckpointMaterial.Kind.values()){
            var source=new SavedAttachmentSourceStore.Sources(kind,witness,ref,ref,ref,ref,ref);
            var json=source.toJson();
            assertEquals(source,SavedAttachmentSourceStore.Sources.decode(StrictJson.parse(StrictJson.canonical(json))));
            assertEquals(kind.name(),json.get("material_kind").textValue());
            assertEquals("9007199254740993",json.get("material_witness").get("identity").get("file_id").textValue());
            for(String key:List.of("material_kind","material_witness")){
                var missing=json.deepCopy();missing.remove(key);
                assertThrows(Exception.class,()->SavedAttachmentSourceStore.Sources.decode(missing));
                var nul=json.deepCopy();nul.putNull(key);
                assertThrows(Exception.class,()->SavedAttachmentSourceStore.Sources.decode(nul));
            }
            var legacy=json.deepCopy();legacy.put("schema","xar.java-saved-attachment-sources/v2");
            assertThrows(Exception.class,()->SavedAttachmentSourceStore.Sources.decode(legacy));
            var unknown=json.deepCopy();unknown.put("material_kind","FIRST");
            assertThrows(Exception.class,()->SavedAttachmentSourceStore.Sources.decode(unknown));
        }
    }
}
