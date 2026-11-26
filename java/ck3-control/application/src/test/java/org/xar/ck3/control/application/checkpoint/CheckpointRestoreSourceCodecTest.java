package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

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

    @Test void ordinaryAttachmentSwitchesOnlyOversizedSaveToItsPhysicalWitness(){
        Path root=Path.of("restore-source-codec-test").toAbsolutePath();
        var driverRef=new ExactRef(root.resolve("driver.json").toString(),19,"b".repeat(64));
        var ack=new ExactRef(root.resolve("save-ack.bin").toString(),37,"c".repeat(64));
        var metadata=new ExactRef(root.resolve("attachment-metadata.json").toString(),23,"d".repeat(64));
        var driver=new CheckpointPair.FileWitness(driverRef,new FileStatIdentity(BigInteger.valueOf(19),"15","1"));
        var material=new CheckpointPair.FileWitness(metadata,new FileStatIdentity(BigInteger.valueOf(23),"16","1"));
        var frame=new ObservationIdentity("restore-source-codec-test",new GameGeneration(123,new PythonOnlyUInt64(BigInteger.TEN)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.ONE),
                        "native:1",BigInteger.ONE,"episode"),3);
        for(long size:List.of(17L,(long)WriterContracts.MAX_PIN_BYTES,1L+WriterContracts.MAX_PIN_BYTES)) {
            var saveRef=new ExactRef(root.resolve("xar_checkpoint.ck3").toString(),size,"a".repeat(64));
            var save=new CheckpointPair.FileWitness(saveRef,new FileStatIdentity(BigInteger.valueOf(size),"9007199254740993","1"));
            var pair=new CheckpointPair(save,driver,frame,"lineage",1,"original-save",ack,Instant.EPOCH);
            boolean oversized=size>WriterContracts.MAX_PIN_BYTES;
            var witness=SavedAttachmentSourceStore.ordinaryPhysicalSaveWitness(pair);
            assertEquals(oversized?Optional.of(save):Optional.empty(),witness);
            var sources=new SavedAttachmentSourceStore.Sources(SavedCheckpointMaterial.Kind.ORDINARY,material,
                    metadata,metadata,metadata,metadata,ack,witness);
            var request=SavedAttachmentSourceStore.attachmentRequest(SavedAttachmentAuthority.KIND,"restore",pair,sources,List.of(metadata));
            var encoded=request.detailsObject().get(SavedAttachmentSourceStore.SOURCES_DETAIL);
            assertEquals(oversized?SavedAttachmentSourceStore.SOURCES_SCHEMA_PHYSICAL_SAVE_WITNESS:SavedAttachmentSourceStore.SOURCES_SCHEMA,
                    encoded.get("schema").textValue());
            assertEquals(sources,SavedAttachmentSourceStore.Sources.decode(encoded));
            assertEquals(pair,SavedAttachmentAuthority.pairFromDetails(request));
            assertEquals(!oversized,request.evidence().contains(saveRef));
            assertTrue(request.evidence().containsAll(List.of(ack,driverRef,metadata)));
            var foreign=new CheckpointPair.FileWitness(saveRef,new FileStatIdentity(BigInteger.valueOf(size),"9007199254740994","1"));
            var wrong=new SavedAttachmentSourceStore.Sources(SavedCheckpointMaterial.Kind.ORDINARY,material,
                    metadata,metadata,metadata,metadata,ack,Optional.of(foreign));
            assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.attachmentRequest(
                    SavedAttachmentAuthority.KIND,"restore",pair,wrong,List.of(metadata)));
        }
    }
}
