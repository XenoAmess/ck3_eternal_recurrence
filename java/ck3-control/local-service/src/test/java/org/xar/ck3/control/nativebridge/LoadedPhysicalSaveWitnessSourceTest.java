package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Real file identity/hash and software SAVE/source/writer edges; no Native loaded-Game role or adoption is minted. */
final class LoadedPhysicalSaveWitnessSourceTest {
    @TempDir Path temporary;
    @Test void explicitPhysicalSaveWitnessCodecPreservesV3AndRejectsMixedOrFirstBaselineShapes()throws Exception {
        var files=new NativeCheckpointFiles();
        var document=files.createNew(temporary.resolve("source.json"),new byte[]{'{','}'});
        var physical=files.createNew(temporary.resolve("physical.ck3"),new byte[]{1,2,3});
        var ref=document.reference();
        var old=new SavedAttachmentSourceStore.Sources(SavedCheckpointMaterial.Kind.ORDINARY,document,ref,ref,ref,ref,ref);
        var oldJson=old.toJson();
        assertEquals("xar.java-saved-attachment-sources/v3",oldJson.get("schema").textValue());
        assertFalse(oldJson.has("physical_save_witness"));assertEquals(8,oldJson.size());
        assertTrue(SavedAttachmentSourceStore.Sources.decode(oldJson).physicalSaveWitness().isEmpty());
        var current=new SavedAttachmentSourceStore.Sources(SavedCheckpointMaterial.Kind.ORDINARY,document,ref,ref,ref,ref,ref,Optional.of(physical));
        var currentJson=current.toJson();assertEquals("xar.java-saved-attachment-sources/v4",currentJson.get("schema").textValue());
        assertEquals(9,currentJson.size());assertEquals(current,SavedAttachmentSourceStore.Sources.decode(currentJson));
        assertFalse(current.references().contains(physical.reference()),"the physical witness is inline DATA, not a raw Writer artifact pin");
        var mixed=oldJson.deepCopy();mixed.set("physical_save_witness",currentJson.get("physical_save_witness"));
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.Sources.decode(mixed));
        var missing=currentJson.deepCopy();missing.remove("physical_save_witness");
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.Sources.decode(missing));
        var alias=currentJson.deepCopy();alias.put("schema","xar.java-saved-attachment-sources/v2");
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.Sources.decode(alias));
        assertThrows(IllegalArgumentException.class,()->new SavedAttachmentSourceStore.Sources(SavedCheckpointMaterial.Kind.FIRST_BASELINE,
                document,ref,ref,ref,ref,ref,Optional.of(physical)));
        files.verify(document);files.verify(physical);
    }
    @Test void realSparseSaveAboveWriterPinBoundPreviewsV4ForOrdinaryAndLoadedAndRejectsTampering()throws Exception {
        // Physical Game inputs have a separate profile root; the Writer's finite whole-root plan covers only its actual small writes.
        Path root=temporary.resolve("actual-software-save"),profile=temporary.resolve("physical-profile"),save=profile.resolve("save games/xar_checkpoint.ck3");
        long logicalBytes=Math.addExact((long)WriterContracts.MAX_PIN_BYTES,1);
        assertEquals(67_108_869L,logicalBytes);
        try(var f=new CheckpointSourceCompositionTest.Fixture(root,false,Clock.systemUTC(),Optional.empty(),Optional.empty(),
                List.of(),Duration.ofSeconds(90),profile,Optional.of(()->writeSparseSave(save,logicalBytes)),
                Optional.of(CheckpointSourceCompositionTest.freshReconciliationReads()),true,true)) {
            assertNotNull(f.materialOutputGuard);f.materialOutputGuard.requireFilePort(f.materialOutputFiles);
            // A real orphan seed preserves the independent SeedStore refusal; no large seed copy or seed authority is requested.
            f.files.createNew(root.resolve("save-games").resolve(org.xar.ck3.control.application.lifecycle.SeedArtifact.NAME),new byte[]{3});
            var actual=f.service.checkpoint(f.request);
            if(actual instanceof CheckpointResult.Unknown unknown&&unknown.action().flatMap(receipt->receipt.ack()).filter(ack->ack.nativeOk()).isPresent()) {
                var original=f.request.saveCommand();int writes=f.actual.nativeActionWrites();
                String body=org.xar.ck3.control.application.action.ActionCodec.bodySha256(original);Instant deadline=original.deadline();
                actual=f.service.queryOriginal(original.actionId(),Instant.now().plusSeconds(30));
                assertEquals(writes,f.actual.nativeActionWrites(),"second stable observation collects this original SAVE without another write");
                assertEquals(body,org.xar.ck3.control.application.action.ActionCodec.bodySha256(f.request.saveCommand()));
                assertEquals(deadline,f.request.saveCommand().deadline());
            }
            var collected=actual;
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,collected,()->"actual sparse SAVE fixture returned "+collected);
            assertEquals(org.xar.ck3.control.application.lifecycle.SeedAdoption.Reason.ORPHAN_SEED,
                    assertInstanceOf(org.xar.ck3.control.application.lifecycle.SeedAdoption.Unavailable.class,confirmed.seedAdoption()).reason());
            var pair=confirmed.pair();assertEquals(logicalBytes,pair.save().reference().bytes());
            assertFalse(Path.of(pair.save().reference().path()).startsWith(f.actual.root),"large physical SAVE is outside the Writer's small-object storage plan");
            assertTrue(pair.save().reference().bytes()>WriterContracts.MAX_PIN_BYTES);
            f.files.verify(pair.save()); // NativeCheckpointFiles observes the complete stream, never a fabricated large FileRef.
            f.saveBoundary(pair);f.actual.ready();
            var current=f.actual.collector.checkpoint("software-save-lineage").observe(Instant.now().plusSeconds(30));
            var candidate=replacementPacket(f,pair,current);
            f.actual.writer.locked(same->{
                String before=same.head().digest();long sequence=same.head().state().sequence();
                var savedNativeRef=confirmed.action().applied().orElseThrow().observation().originalEvidence();
                byte[] savedNativeOriginal=f.actual.archive.withSession(same).loadNativeFrame(savedNativeRef);
                assertEquals(savedNativeRef.bytes(),savedNativeOriginal.length);
                assertEquals(savedNativeRef.sha256(),org.xar.ck3.control.application.action.ActionCodec.sha256(savedNativeOriginal));
                var savedEnvelope=(NativeWire.Snapshot)NativeWire.decode(savedNativeOriginal);
                assertEquals(pair.frame().frame().snapshotId(),savedEnvelope.snapshotId());
                assertEquals(pair.frame().frame().identity().nativeRevision(),savedEnvelope.revision());
                assertEquals("native:"+savedEnvelope.revision(),savedEnvelope.snapshotId(),"the original software packet carries the saved-frame identity before capture");
                var material=f.materials.currentPhysical(same,pair);assertEquals(SavedCheckpointMaterial.Kind.ORDINARY,material.kind());
                var request=new RestoreCheckpointService.Request("sparse-save-source",pair,current,before,Instant.now().plusSeconds(30),material);
                Path restoreRoot=Path.of(material.reference().path()).getParent().getParent().resolve("restores");
                assertTrue(restoreRoot.startsWith(root.resolve("saved-material")));assertFalse(Files.exists(restoreRoot));
                long chargedBefore=f.materialOutputGuard.accounting().roots().stream().mapToLong(rootAccounting->rootAccounting.measuredChargedUpperBytes()).sum();
                var attachment=f.materials.prepare(request,candidate,material.savedDriver());
                assertEquals(f.owner,attachment.material().session());
                var accounting=f.materialOutputGuard.accounting();
                assertEquals(org.xar.ck3.control.service.root.RootRuntimeStorageGuard.Status.ADMITTED,accounting.status());
                assertEquals(0,accounting.unresolvedWrites());
                assertTrue(accounting.roots().stream().allMatch(rootAccounting->rootAccounting.outstandingPeakBytes()==0));
                assertTrue(accounting.roots().stream().mapToLong(rootAccounting->rootAccounting.measuredChargedUpperBytes()).sum()>chargedBefore);
                var sources=SavedAttachmentSourceStore.Sources.decode(attachment.request().detailsObject().get(SavedAttachmentSourceStore.SOURCES_DETAIL));
                Path restoreParent=Path.of(sources.basis().path()).getParent();
                assertTrue(restoreParent.startsWith(restoreRoot));assertTrue(Files.isDirectory(restoreParent));
                assertEquals(pair.save(),sources.physicalSaveWitness().orElseThrow());
                assertFalse(attachment.request().evidence().contains(pair.save().reference()));
                assertTrue(attachment.request().evidence().contains(pair.nativeAckRef()));
                assertTrue(attachment.request().evidence().contains(pair.driver().reference()));
                for(var ref:attachment.request().evidence())assertTrue(ref.bytes()<=WriterContracts.MAX_PIN_BYTES);
                assertNotNull(same.preview(attachment.request()),"the genuine original-lock source loader and bounded writer must accept the explicit physical witness");
                assertNotNull(f.sources.load(same.head().state(),attachment.request()));
                var basisWitness=f.files.observe(Path.of(sources.basis().path())).orElseThrow();
                assertEquals(sources.basis(),basisWitness.reference());
                var originalBasis=(com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.FullJsonTree.parse(f.files.read(basisWitness,1<<20),1<<20);
                var originalCycles=originalBasis.get("completed_cycles");assertTrue(originalCycles.isBigInteger());
                var javaLongCycles=com.fasterxml.jackson.databind.node.LongNode.valueOf(originalCycles.bigIntegerValue().longValueExact());
                assertNotEquals(javaLongCycles,originalCycles,"Java integer node representation differs before metadata roundtrip");
                assertEquals(originalCycles,org.xar.ck3.control.contracts.FullJsonTree.parse(org.xar.ck3.control.contracts.FullJsonTree.encode(javaLongCycles,1<<20),1<<20));
                var wrongCycleValues=List.<com.fasterxml.jackson.databind.JsonNode>of(
                        com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(originalCycles.bigIntegerValue().add(BigInteger.ONE)),
                        com.fasterxml.jackson.databind.node.DecimalNode.valueOf(new java.math.BigDecimal(originalCycles.bigIntegerValue()).setScale(1)),
                        com.fasterxml.jackson.databind.node.TextNode.valueOf(originalCycles.bigIntegerValue().toString()));
                for(int index=0;index<wrongCycleValues.size();index++) {
                    var alteredBasis=originalBasis.deepCopy();alteredBasis.set("completed_cycles",wrongCycleValues.get(index));
                    var alteredRef=f.materialOutputFiles.createNew(restoreParent.resolve("basis-negative-"+index+".json"),
                            org.xar.ck3.control.contracts.FullJsonTree.encode(alteredBasis,1<<20)).reference();
                    var alteredSources=new SavedAttachmentSourceStore.Sources(sources.kind(),sources.material(),alteredRef,sources.game(),
                            sources.opening(),sources.progress(),sources.restoredNative(),sources.physicalSaveWitness());
                    var alteredDetails=attachment.request().detailsObject().deepCopy();alteredDetails.set(SavedAttachmentSourceStore.SOURCES_DETAIL,alteredSources.toJson());
                    var alteredEvidence=new java.util.LinkedHashSet<>(attachment.request().evidence());alteredEvidence.remove(sources.basis());alteredEvidence.add(alteredRef);
                    var alteredRequest=new WriterContracts.Request(attachment.request().kind(),StrictJson.canonical(alteredDetails),List.copyOf(alteredEvidence));
                    var rejected=assertThrows(Exception.class,()->f.sources.load(same.head().state(),alteredRequest));
                    assertTrue(rejected.getMessage().contains("frontier"),()->"altered basis must fail the original full-tree frontier comparison: "+rejected);
                    assertEquals(before,same.head().digest());assertEquals(sequence,same.head().state().sequence());
                }

                var loaded=f.sources.prepareLoaded(request,candidate,material.savedDriver());
                assertArrayEquals(attachment.request().details(),loaded.request().details());
                assertEquals(attachment.request().evidence(),loaded.request().evidence());
                var legacySources=new SavedAttachmentSourceStore.Sources(sources.kind(),sources.material(),sources.basis(),sources.game(),
                        sources.opening(),sources.progress(),sources.restoredNative());
                var legacyDetails=attachment.request().detailsObject().deepCopy();
                legacyDetails.set(SavedAttachmentSourceStore.SOURCES_DETAIL,legacySources.toJson());
                var legacyEvidence=new java.util.LinkedHashSet<>(attachment.request().evidence());legacyEvidence.add(pair.save().reference());
                var legacy=new WriterContracts.Request(attachment.request().kind(),StrictJson.canonical(legacyDetails),List.copyOf(legacyEvidence));
                assertThrows(IOException.class,()->same.preview(legacy),"the unchanged v3 raw artifact path must retain the Writer pin bound");

                var other=f.files.createNew(root.resolve("different-save.ck3"),new byte[]{9,8,7});
                var wrongSources=new SavedAttachmentSourceStore.Sources(sources.kind(),sources.material(),sources.basis(),sources.game(),
                        sources.opening(),sources.progress(),sources.restoredNative(),Optional.of(other));
                var wrongDetails=attachment.request().detailsObject().deepCopy();wrongDetails.set(SavedAttachmentSourceStore.SOURCES_DETAIL,wrongSources.toJson());
                var wrong=new WriterContracts.Request(attachment.request().kind(),StrictJson.canonical(wrongDetails),attachment.request().evidence());
                assertThrows(Exception.class,()->f.sources.load(same.head().state(),wrong));
                assertEquals(before,same.head().digest());assertEquals(sequence,same.head().state().sequence());

                // Modify an interior byte without changing the real length or FileID; full-stream hash must detect it.
                try(var channel=FileChannel.open(save,StandardOpenOption.WRITE)) {
                    channel.position(logicalBytes/2);channel.write(ByteBuffer.wrap(new byte[]{5}));channel.force(true);
                }
                assertEquals(logicalBytes,Files.size(save));
                assertThrows(IOException.class,()->f.files.verify(pair.save()));
                assertThrows(Exception.class,()->f.sources.load(same.head().state(),attachment.request()));
                assertEquals(before,same.head().digest());assertEquals(sequence,same.head().state().sequence());return null;
            });
            assertEquals(1,f.actual.nativeActionWrites(),"only the software fixture's original SAVE occurred; no Game replacement or READ was granted");
        }
    }
    @Test void physicalWitnessVerificationRejectsSameContentWithAChangedNativeFileIdentity()throws Exception {
        var files=new NativeCheckpointFiles();Path save=temporary.resolve("small-original.ck3");byte[] body={1,2,3,4};
        var original=files.createNew(save,body);files.verify(original);
        Files.move(save,save.resolveSibling("small-original.retained.ck3"));
        var changed=files.createNew(save,body);
        assertEquals(original.reference(),changed.reference());assertNotEquals(original.identity().fileId(),changed.identity().fileId());
        assertThrows(IOException.class,()->files.verify(original));files.verify(changed);
    }
    private static void writeSparseSave(Path save,long logicalBytes)throws IOException {
        try(var channel=FileChannel.open(save,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE,StandardOpenOption.SPARSE)) {
            channel.position(logicalBytes-1);if(channel.write(ByteBuffer.wrap(new byte[]{1}))!=1)throw new IOException("sparse SAVE terminal byte was not written");channel.force(true);
        }
        var nativeFile=SharedSourceFiles.nativeFile(save);
        if(nativeFile.logicalBytes()!=logicalBytes||nativeFile.allocatedBytes()>(1L<<20))
            throw new IOException("real sparse SAVE allocation qualification failed: logical="+nativeFile.logicalBytes()+",allocated="+nativeFile.allocatedBytes());
        System.err.println("LOADED_PHYSICAL_SAVE_WITNESS_SPARSE logical_bytes="+nativeFile.logicalBytes()+" allocated_bytes="+nativeFile.allocatedBytes());
    }
    private static RestoreCheckpointService.NativeCandidate replacementPacket(CheckpointSourceCompositionTest.Fixture f,
            CheckpointPair pair,CheckpointRequest.Readiness current)throws IOException {
        // Read the producer's real raw state packet through the original privately issued saved material.
        var material=f.actual.writer.locked(same->f.materials.currentPhysical(same,pair));
        byte[] packet=Files.readAllBytes(Path.of(material.sourceSemantic().originalNativePacket().path()));
        var snapshot=(NativeWire.Snapshot)NativeWire.decode(packet);var old=pair.frame().game();
        var replacement=new GameGeneration(old.pid()+1,new PythonOnlyUInt64(old.creationFiletime().value().add(BigInteger.ONE)));
        var ref=f.files.createNew(f.actual.root.resolve("replacement-raw-source.bin"),packet).reference();
        var frame=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(current.observed().machineId(),replacement,
                BigInteger.ONE,"software-physical-witness-replacement"),snapshot.snapshotId(),snapshot.revision(),new RawJson(snapshot.state().value()),packet,Instant.now());
        return new RestoreCheckpointService.NativeCandidate(frame,current.source(),pair.lineageId(),ref);
    }
}
