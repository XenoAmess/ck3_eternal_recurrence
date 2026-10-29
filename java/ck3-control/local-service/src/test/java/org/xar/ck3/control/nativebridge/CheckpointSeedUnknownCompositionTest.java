package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.service.mcp.CheckpointPublicCodec;
import org.xar.ck3.control.service.root.RootCheckpointPublicCalls;

/** A real confirmed SAVE remains usable while its separate seed metadata is malformed. FileID custody is tested separately. */
final class CheckpointSeedUnknownCompositionTest {
    @TempDir Path temporary;
    @Test void actualConfirmedPairPreservesUnknownSeedThroughPublicCodecSavedMaterialAndAdoption()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("seed-only-unknown"),false)){
            var producer=new PublicCheckpointMaterialCapture(f.actual.writer,f.batch,f.materials,new ActionSnapshotReader(f.actual.journal));
            var pending=f.actual.writer.locked(same->producer.begin(same,f.owner,f.proof.semantic(),f.request));
            var first=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            var original=assertInstanceOf(SeedAdoption.Available.class,first.seedAdoption()).artifact();
            Path path=Path.of(original.metadata().reference().path());
            Files.writeString(path,"{}");
            var replacement=f.files.observe(path).orElseThrow();
            assertNotEquals(original.metadata().reference(),replacement.reference(),"actual malformed metadata, not a fabricated seed port result");
            var unavailable=assertInstanceOf(SeedAdoption.Unknown.class,f.seedLink.require().read());
            var queried=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.queryOriginal(first.action().command().actionId(),Instant.now().plusSeconds(30)));
            assertEquals(first.pair(),queried.pair());assertEquals(first.action(),queried.action());
            assertEquals(unavailable,assertInstanceOf(SeedAdoption.Unknown.class,queried.seedAdoption()));
            var captured=f.actual.writer.locked(same->{
                var material=producer.confirm(same,pending,queried);
                assertEquals(queried.pair(),material.pair());material.requirePhysical(same);material.material().requireRetained(same);
                assertEquals(f.proof.semantic(),material.material().sourceSemantic());
                assertSame(material.journalCommit(),f.batch.acceptPublicCheckpoint(same,f.owner,material));
                var driver=f.drivers.readArchivedSnapshot(queried.pair(),f.files.read(queried.pair().driver(),DriverCheckpointStore.MAX_DRIVER_BYTES));
                var receipt=f.actual.archive.withSession(same).receiptReferenceOf(queried.action());
                var wire=CheckpointPublicCodec.save(new RootCheckpointPublicCalls.SaveCall(queried,Optional.of(driver),Optional.of(receipt)));
                var result=FullJsonTree.parse(wire.bytes(),64*1024*1024);
                assertEquals("saved",result.get("status").textValue());assertTrue(result.get("accepted").booleanValue());
                assertTrue(result.get("materialization").get("available").booleanValue());assertTrue(result.get("episode_seed").isNull());
                assertEquals("unknown",result.get("seed_adoption").get("status").textValue());
                assertEquals(unavailable.reason(),result.get("seed_adoption").get("reason").textValue());
                assertEquals(unavailable.evidence().size(),result.get("seed_adoption").get("evidence").size());
                for(int i=0;i<unavailable.evidence().size();i++)
                    assertEquals(unavailable.evidence().get(i).toJson(),result.get("seed_adoption").get("evidence").get(i));
                return material;
            });
            String head=f.actual.writer.locked(same->same.head().digest());
            var repeated=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.queryOriginal(first.action().command().actionId(),Instant.now().plusSeconds(30)));
            assertEquals(queried,repeated);
            f.actual.writer.locked(same->{assertSame(captured,producer.confirm(same,pending,repeated));assertEquals(head,same.head().digest());return null;});
            assertInstanceOf(SeedAdoption.Unknown.class,f.seedLink.require().freezeFirst(first.pair(),first.action()));
            assertEquals(replacement,f.files.observe(path).orElseThrow(),"unknown seed metadata cannot be repaired or refrozen");
            assertEquals(1,f.actual.nativeActionWrites());
            Files.writeString(Path.of(first.pair().save().reference().path()),"later changed physical checkpoint");
            assertInstanceOf(CheckpointResult.Unknown.class,f.service.queryOriginal(first.action().command().actionId(),Instant.now().plusSeconds(30)),
                    "unknown physical pair still makes the complete checkpoint result unknown");
            assertEquals(1,f.actual.nativeActionWrites());
        }
    }
}
