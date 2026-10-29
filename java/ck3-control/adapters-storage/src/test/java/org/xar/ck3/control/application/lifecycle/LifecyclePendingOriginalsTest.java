package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Original producer/codec DATA regressions. None constructs a private retained finalization or episode proof. */
final class LifecyclePendingOriginalsTest {
    @TempDir Path temporary;
    private static WriterContracts.Pin pin(ExactRef ref,String fileId) {
        return new WriterContracts.Pin(ref,new WriterContracts.FileIdentity("9007199254740993",fileId,
                "18446744073709551615","2026-10-24T00:00:00Z",ref.bytes()));
    }
    @Test void actualFullKnownProducerAndOriginalPinsRoundTripWithoutEmbeddingOrTruncatingTheKnown()throws Exception {
        var actual=new LifecycleBusinessFixture(temporary.resolve("actual"));
        var encoded=DriverSnapshotFacts.encodeKnownOriginal(actual.snapshot.facts());
        assertTrue(encoded.bytes().length>128*1024);
        var known=actual.files.createNew(temporary.resolve("actual-known.json"),encoded.bytes()).reference();
        var aux=actual.files.createNew(temporary.resolve("actual-aux.json"),org.xar.ck3.control.application.driver.DriverJson.encode(actual.snapshot.facts().auxiliary())).reference();
        var knownPin=pin(known,"18446744073709551614");var auxPin=pin(aux,"18446744073709551613");
        var source=pin(actual.parent.source().sourceRef(),"18446744073709551612");
        var originals=new LifecyclePendingOriginals(7,"a".repeat(64),auxPin,knownPin,List.of(source),List.of(knownPin,auxPin));
        byte[] wire=originals.encode();assertTrue(wire.length<8192);
        var decoded=LifecyclePendingOriginals.decode(wire);assertEquals(originals,decoded);assertArrayEquals(wire,decoded.encode());
        assertEquals(encoded,DriverSnapshotFacts.originalKnownJson(actual.files.read(actual.files.observe(Path.of(known.path())).orElseThrow(),DriverSnapshotFacts.MAX_ORIGINAL_BYTES)));
        var json=LifecycleJson.parse(wire,LifecyclePendingOriginals.MAXIMUM_BYTES);
        assertEquals("18446744073709551614",json.get("before_known").get("native_identity").get("file_id").textValue());
    }
    @Test void decimalNativeIdentitiesMustNotBecomeNumbersOrAcceptUnknownMetadataFields() {
        var ref=new ExactRef("D:/source/original.json",13,"a".repeat(64));var pin=pin(ref,"18446744073709551614");
        var original=new LifecyclePendingOriginals(0,"b".repeat(64),pin,pin,List.of(pin),List.of(pin));
        var row=LifecycleJson.parse(original.encode(),LifecyclePendingOriginals.MAXIMUM_BYTES);
        ((com.fasterxml.jackson.databind.node.ObjectNode)row.get("before_known").get("native_identity")).put("file_id",9007199254740993L);
        assertThrows(IllegalArgumentException.class,()->LifecyclePendingOriginals.decode(LifecycleJson.bytes(row)));
        var extra=LifecycleJson.parse(original.encode(),LifecyclePendingOriginals.MAXIMUM_BYTES);extra.put("completed_cycles",0);
        assertThrows(IllegalArgumentException.class,()->LifecyclePendingOriginals.decode(LifecycleJson.bytes(extra)));
        var missing=LifecycleJson.parse(original.encode(),LifecyclePendingOriginals.MAXIMUM_BYTES);missing.remove("before_known");
        assertThrows(IllegalArgumentException.class,()->LifecyclePendingOriginals.decode(LifecycleJson.bytes(missing)));
    }
    @Test void historicalHashOnlyOrNullOriginalsDoNotBecomeCurrentMaterial() {
        var historical=LifecycleJson.row();historical.put("schema",LifecyclePendingOriginals.SCHEMA);
        historical.put("before_sequence",0);historical.put("before_digest","a".repeat(64));historical.put("auxiliary_sha256","b".repeat(64));
        assertThrows(IllegalArgumentException.class,()->LifecyclePendingOriginals.decode(LifecycleJson.bytes(historical)));
        assertThrows(IllegalArgumentException.class,()->LifecyclePendingOriginals.decode("null".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    @Test void theWarmAuthorityAndColdPureProjectionShareOneReducerAndPreserveUnrelatedState()throws Exception {
        var actual=new LifecycleBusinessFixture(temporary.resolve("pure-projection"));var result=actual.reduction();
        var delta=LifecycleJson.row();delta.set("result",LifecycleJson.parse(result.result(),LifecycleProofCodec.MAX_RESULT_BYTES));
        var child=new LifecycleChild(actual.parent,LifecycleChild.Phase.DEATH_RECORDED,actual.snapshot.facts().stamp(),
                result.driver(),result.auxiliary(),actual.parent.origin().game(),delta,List.of(actual.snapshot.originalEvidence()));
        var authority=new LifecycleContinuityAuthority();authority.register(child);
        var raw=LifecycleJson.row();raw.put("schema","root.ck3.continuity-window/v1");raw.put("machine_id","test-machine");
        raw.put("sequence",0);raw.put("window_id",1);raw.put("start_date_raw",0);raw.put("target_date_raw",480);raw.put("target_days",20);
        raw.put("status","running");raw.put("last_settled_cycles",0);raw.put("last_settled_date_raw",240);raw.put("NEXT",11559);
        raw.putObject("pending_cycle").put("auto_sequence",11558).put("stage","auto_unsettled");
        var before=org.xar.ck3.control.continuity.ContinuityState.fromJson(raw,"test-machine");
        var warm=authority.reduce(before,child.request());var historical=LifecycleContinuityAuthority.project(before,child.request(),result.driver());
        assertEquals(warm.toJson(),historical.toJson());assertEquals(0,historical.sequence());
        assertEquals(raw.get("pending_cycle"),historical.toJson().get("pending_cycle"));
        assertEquals(raw.get("NEXT"),historical.toJson().get("NEXT"));
        assertThrows(IllegalArgumentException.class,()->LifecycleContinuityAuthority.project(historical,child.request(),result.driver()));
    }
}
