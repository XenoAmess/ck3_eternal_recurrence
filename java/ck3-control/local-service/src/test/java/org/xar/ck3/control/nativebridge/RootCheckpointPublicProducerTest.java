package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.CheckpointPublicCodec;
import org.xar.ck3.control.service.root.RootCheckpointPublicCalls.SaveCall;

/** The actual SAVE producer/canonical archive supplies the public encoder; no Root authority is synthesized. */
public final class RootCheckpointPublicProducerTest {
    @TempDir Path temporary;
    @Test void actualCanonicalSavePublishesItsOriginalCheckpointAndFileWitnessWithoutAnotherWrite()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("public-save"),false)){
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            var call=f.actual.writer.locked(same->new SaveCall(confirmed,Optional.of(f.drivers.readVerified(confirmed.pair())),
                    Optional.of(f.actual.archive.withSession(same).receiptReferenceOf(confirmed.action()))));
            var output=StrictJson.parse(CheckpointPublicCodec.save(call).bytes());
            var original=StrictJson.parse(((DriverStateSnapshot.Value)call.savedDriver().orElseThrow().lastCheckpoint()).json());
            assertEquals(original,output.get("checkpoint"));assertEquals("saved",output.get("status").textValue());
            assertEquals(confirmed.pair(),CheckpointPairCodec.decode(StrictJson.canonical(output.get("checkpoint_pair"))));
            assertEquals(confirmed.pair().save().identity().fileId(),output.get("materialization").get("save_witness").get("identity").get("file_id").textValue());
            assertTrue(output.get("revision").isTextual());assertTrue(output.get("checkpoint").get("date_raw").isIntegralNumber());
            assertEquals(output,StrictJson.parse(CheckpointPublicCodec.save(call).bytes()));assertEquals(1,f.actual.nativeActionWrites());
            assertThrows(Exception.class,()->new SaveCall(confirmed,Optional.empty(),call.canonicalReceipt()));
            assertThrows(Exception.class,()->new SaveCall(confirmed,call.savedDriver(),Optional.empty()));
        }
    }
    @Test void actualUnknownSaveRemainsUnknownAfterPublicEncodingAndIsNotEncodedAsMaterialized()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("public-save-unknown"),true)){
            var unknown=assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));
            var call=f.actual.writer.locked(same->new SaveCall(unknown,Optional.empty(),
                    unknown.action().map(action->f.actual.archive.withSession(same).receiptReferenceOf(action))));
            var output=StrictJson.parse(CheckpointPublicCodec.save(call).bytes());
            assertEquals("unknown",output.get("status").textValue());assertFalse(output.get("materialization").get("available").booleanValue());
            assertFalse(output.has("checkpoint"));CheckpointPublicCodec.save(call);assertEquals(1,f.actual.nativeActionWrites());
        }
    }
}
