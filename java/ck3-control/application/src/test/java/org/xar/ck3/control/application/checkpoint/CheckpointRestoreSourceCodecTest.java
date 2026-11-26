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
    @Test void importedRecoveryBasisPersistsOriginalFileIdsAndIndependentRolesOnlyOnDemand() {
        var fixture=importedAttachment();
        var request=fixture.attachment();
        assertTrue(SavedAttachmentSourceStore.importedRecoveryBasis(request.detailsObject()).isEmpty());
        byte[] oldDetails=request.details();
        var durable=SavedAttachmentSourceStore.bindRecoveryBasis(request,fixture.basis());
        assertArrayEquals(oldDetails,request.details());
        assertEquals(request.sourceKey(),durable.sourceKey());
        assertNotEquals(request.identity(),durable.identity());
        var decoded=SavedAttachmentSourceStore.importedRecoveryBasis(org.xar.ck3.control.continuity.ContinuityJson.parseObject(durable.details(),65536)).orElseThrow();
        assertEquals(fixture.basis(),decoded);
        assertEquals("9007199254740993",decoded.readManifest().identity().fileIdDecimal());
        assertEquals(Instant.parse("2026-11-26T22:05:00Z"),decoded.lifecycleDeadline());
        assertTrue(durable.evidence().containsAll(decoded.pins().stream().map(WriterContracts.Pin::reference).toList()));
        assertFalse(durable.evidence().contains(fixture.pair().save().reference()));
        assertDoesNotThrow(()->SavedAttachmentSourceStore.requireRecoveryBasis(fixture.before(),durable,fixture.pair(),fixture.sources(),decoded,decoded.successor()));
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.bindRecoveryBasis(durable,decoded));
    }

    @Test void importedRecoveryBasisRejectsChangedDefaultProducerAndCrossedReadRoles() {
        var fixture=importedAttachment();
        var basis=fixture.basis();
        var durable=SavedAttachmentSourceStore.bindRecoveryBasis(fixture.attachment(),basis);
        var changed=basis.toJson();changed.set("second_native",basis.firstNative().toJson());
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.ImportedRecoveryBasis.decode(changed));
        var crossed=basis.toJson();crossed.set("first_native",basis.secondNative().toJson());crossed.set("second_native",basis.firstNative().toJson());
        var mislabeled=SavedAttachmentSourceStore.ImportedRecoveryBasis.decode(crossed);
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.requireRecoveryBasis(fixture.before(),durable,fixture.pair(),fixture.sources(),mislabeled,basis.successor()));
        var legacy=new SavedAttachmentSourceStore.Sources(SavedCheckpointMaterial.Kind.ORDINARY,fixture.sources().material(),
                fixture.sources().basis(),fixture.sources().game(),fixture.sources().opening(),fixture.sources().progress(),fixture.sources().restoredNative());
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.requireRecoveryBasis(fixture.before(),durable,fixture.pair(),legacy,basis,basis.successor()));
        var missing=new WriterContracts.Request(durable.kind(),durable.details(),fixture.attachment().evidence());
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.requireRecoveryBasis(fixture.before(),missing,fixture.pair(),fixture.sources(),basis,basis.successor()));
        var otherGame=new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(basis.successor().machineId(),
                basis.departed().game(),basis.successor().sessionId());
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.requireRecoveryBasis(fixture.before(),durable,fixture.pair(),fixture.sources(),basis,otherGame));
    }

    private record ImportedAttachmentFixture(org.xar.ck3.control.continuity.ContinuityState before,CheckpointPair pair,
            SavedAttachmentSourceStore.Sources sources,WriterContracts.Request attachment,SavedAttachmentSourceStore.ImportedRecoveryBasis basis) { }

    private static ImportedAttachmentFixture importedAttachment() {
        Path root=Path.of("imported-recovery-basis-software").toAbsolutePath();String machine="machine";
        var departed=new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(machine,
                new GameGeneration(50372,new PythonOnlyUInt64(BigInteger.TEN)),"departed");
        var successor=new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(machine,
                new GameGeneration(61127,new PythonOnlyUInt64(BigInteger.ONE)),"successor");
        var frame=new ObservationIdentity(machine,new GameGeneration(241448,new PythonOnlyUInt64(BigInteger.valueOf(11))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.ONE),
                        "native:1",BigInteger.ONE,"episode"),3);
        var save=new CheckpointPair.FileWitness(new ExactRef(root.resolve("original.ck3").toString(),94604706,"a".repeat(64)),
                new FileStatIdentity(BigInteger.valueOf(94604706),"11","1"));
        var driver=new CheckpointPair.FileWitness(recoveryPin(root,"driver").reference(),new FileStatIdentity(BigInteger.valueOf(17),"12","1"));
        var nativeSaveAck=recoveryPin(root,"save-ack").reference();
        var pair=new CheckpointPair(save,driver,frame,"lineage",1,"original-save",nativeSaveAck,Instant.EPOCH);
        var material=new CheckpointPair.FileWitness(recoveryPin(root,"material").reference(),new FileStatIdentity(BigInteger.valueOf(17),"13","1"));
        var row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",machine).put("sequence",58)
                .put("window_id",1).put("start_date_raw",0).put("target_date_raw",240).put("target_days",10)
                .put("status","running").put("last_settled_cycles",0).put("last_settled_date_raw",0);
        var before=org.xar.ck3.control.continuity.ContinuityState.fromJson(row,machine);
        var importSource=new SavedAttachmentSourceStore.ImportedOrigin(departed,recoveryPin(root,"request").reference(),
                recoveryPin(root,"entry"),recoveryPin(root,"physical-confirmation"));
        var second=recoveryPin(root,"second-native");var doc=recoveryPin(root,"doc").reference();
        var sources=new SavedAttachmentSourceStore.Sources(SavedCheckpointMaterial.Kind.ORDINARY,material,doc,doc,doc,doc,
                second.reference(),Optional.of(save),Optional.of(importSource));
        var basis=new SavedAttachmentSourceStore.ImportedRecoveryBasis("restore",Instant.parse("2026-11-26T22:05:00Z"),58,
                org.xar.ck3.control.continuity.ContinuityJson.digest(row),departed,successor,
                new ExactRef(root.resolve("staged.ck3").toString(),save.reference().bytes(),save.reference().sha256()),
                recoveryPin(root,"control"),recoveryPin(root,"transfer-proof"),recoveryPin(root,"read-manifest"),
                recoveryPin(root,"first-ack"),recoveryPin(root,"first-native"),recoveryPin(root,"second-ack"),second);
        return new ImportedAttachmentFixture(before,pair,sources,SavedAttachmentSourceStore.attachmentRequest(SavedAttachmentAuthority.KIND,
                "restore",pair,sources,List.of()),basis);
    }

    private static WriterContracts.Pin recoveryPin(Path root,String name) {
        var ref=new ExactRef(root.resolve(name+".json").toString(),17,"e".repeat(64));
        return new WriterContracts.Pin(ref,new WriterContracts.FileIdentity("1","9007199254740993","3",Instant.EPOCH.toString(),17));
    }

}
