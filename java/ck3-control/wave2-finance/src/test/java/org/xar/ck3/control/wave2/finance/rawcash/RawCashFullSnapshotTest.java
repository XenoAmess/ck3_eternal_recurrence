package org.xar.ck3.control.wave2.finance.rawcash;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;

/** Existing software raw-cash originals with a larger contextual SDK snapshot; no Native dispatch. */
final class RawCashFullSnapshotTest {
    private record Vector(ObjectNode current,ObjectNode snapshot,JsonNode expected) { }

    @Test void allRetainedSuccessfulOriginalsNormalizeWithCompleteSnapshotExtensions() throws Exception {
        List<Vector> vectors=successfulOriginals();assertEquals(50,vectors.size());
        for(Vector vector:vectors) {
            byte[] current=SdkProjectionJson.encode(vector.current());
            byte[] unchanged=current.clone();
            byte[] snapshot=largeSnapshot(vector.snapshot());
            assertTrue(snapshot.length>StrictJson.INPUT_MAX_BYTES);
            var result=RawCashCodec.normalize(current,snapshot);
            assertEquals(vector.expected(),StrictJson.parse(result.toJson()));
            assertArrayEquals(unchanged,current,"full snapshot support cannot rewrite the raw cash original");
            assertEquals(vector.current().get("snapshot_revision").bigIntegerValue(),result.frame().snapshotRevision());
            if(result.loanObservation().known()) {
                var loan=result.loanObservation().value();
                assertEquals(0,loan.fundingCreditRaw());assertFalse(loan.receivedFundsVerified());
                assertFalse(loan.submitPlanned());assertFalse(loan.completeLoanTerms());
            }
        }
    }

    @Test void largerSnapshotsKeepExactFrameBindingAndTheSmallRawSourceBudget() throws Exception {
        var vector=successfulOriginals().getFirst();byte[] current=SdkProjectionJson.encode(vector.current());
        var wrong=vector.snapshot().deepCopy();
        wrong.put("native_revision",wrong.get("native_revision").bigIntegerValue().add(java.math.BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->RawCashCodec.normalize(current,largeSnapshot(wrong)));
        var oversized=vector.current().deepCopy();oversized.put("software_source_extension","x".repeat(StrictJson.INPUT_MAX_BYTES));
        byte[] largeSource=FullJsonTree.encode(oversized,FullJsonTree.MAXIMUM_BYTES);
        assertThrows(IllegalArgumentException.class,()->RawCashCodec.normalize(largeSource,largeSnapshot(vector.snapshot())));
    }

    private static byte[] largeSnapshot(ObjectNode original) {
        var snapshot=original.deepCopy();
        snapshot.put("software_contextual_sdk_extension","x".repeat(StrictJson.INPUT_MAX_BYTES+1));
        return FullJsonTree.encode(snapshot,FullJsonTree.MAXIMUM_BYTES);
    }

    private static List<Vector> successfulOriginals() throws IOException {
        var resource=RawCashFullSnapshotTest.class.getResourceAsStream("/holyloan/original-v1.jsonl.gz");
        if(resource==null)throw new IOException("required existing raw-cash software original corpus is absent");
        String text;
        try(var input=resource;var gzip=new GZIPInputStream(input)) {
            byte[] raw=gzip.readNBytes(8*1024*1024+1);
            if(raw.length>8*1024*1024)throw new IOException("bounded existing raw-cash corpus required");
            text=new String(raw,StandardCharsets.UTF_8);
        }
        String[] lines=text.split("\n",-1);var result=new ArrayList<Vector>();
        for(int index=1;index<lines.length-1;index+=3) {
            var metadata=StrictJson.parse(lines[index].getBytes(StandardCharsets.UTF_8));
            var request=StrictJson.parse(lines[index+1].getBytes(StandardCharsets.UTF_8));
            if("result".equals(metadata.path("expected_kind").textValue())&&"normalize".equals(request.path("operation").textValue())) {
                var arguments=request.get("arguments");
                result.add(new Vector((ObjectNode)arguments.get("value"),(ObjectNode)arguments.get("snapshot"),
                        StrictJson.parse(lines[index+2].getBytes(StandardCharsets.UTF_8))));
            }
        }
        return List.copyOf(result);
    }
}
