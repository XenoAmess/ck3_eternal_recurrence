package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;

/** Actual original writer transactions; decoding DATA never substitutes for same-lock membership checks. */
final class WriterTransactionCodecTest {
    @TempDir Path root;

    @Test void actualPreviewCommitAndColdReceiptRequireTheSameOriginalWriter() throws Exception {
        WriterFixture fixture = new WriterFixture(root.resolve("actual"));
        Prepared prepared = fixture.writer.preview(WriterFixture.settled("codec-entry", 1048, 2));
        byte[] bytes = WriterTransactionCodec.encodePrepared(prepared);
        Prepared decoded = WriterTransactionCodec.decodePrepared(bytes, WriterFixture.MACHINE);
        assertArrayEquals(bytes, WriterTransactionCodec.encodePrepared(decoded));
        assertEquals(prepared.predecessor().documents(), decoded.predecessor().documents());
        assertEquals(prepared.sources(), decoded.sources()); assertEquals(prepared.evidence(), decoded.evidence());
        assertArrayEquals(prepared.request().details(), decoded.request().details());
        fixture.writer.locked(same -> {
            assertThrows(java.io.IOException.class, () -> same.requireCommitted(decoded,
                    new Receipt(Disposition.COMMITTED, decoded.reduced(), decoded.request().identity(), 3, false)));
            return null;
        });
        Receipt committed = fixture.writer.commit(decoded);
        byte[] receiptBytes = WriterTransactionCodec.encodeReceipt(committed);
        Receipt cold = WriterTransactionCodec.decodeReceipt(receiptBytes, WriterFixture.MACHINE);
        fixture.writer.locked(same -> { same.requireCommitted(decoded, cold); return null; });
        assertArrayEquals(receiptBytes, WriterTransactionCodec.encodeReceipt(cold));
        assertEquals(Disposition.ALREADY_COMMITTED, fixture.writer.commit(decoded).disposition());
        assertThrows(IllegalArgumentException.class, () -> WriterTransactionCodec.decodePrepared(bytes, "foreign-machine"));
        assertThrows(IllegalArgumentException.class, () -> WriterTransactionCodec.decodeReceipt(receiptBytes, "foreign-machine"));
    }

    @Test void decodedPreparedStillFailsActualSourceIdentityRevalidationBeforeAnyLedgerMutation() throws Exception {
        WriterFixture fixture = new WriterFixture(root.resolve("changed-source"));
        Prepared actual = fixture.writer.preview(WriterFixture.settled("changed-after-archive", 1048, 2));
        Prepared decoded = WriterTransactionCodec.decodePrepared(WriterTransactionCodec.encodePrepared(actual), WriterFixture.MACHINE);
        byte[] before = Files.readAllBytes(fixture.layout.snapshot());
        Files.writeString(fixture.source, "changed actual source after strict DATA roundtrip");
        assertThrows(java.io.IOException.class, () -> fixture.writer.commit(decoded));
        assertArrayEquals(before, Files.readAllBytes(fixture.layout.snapshot()));
        assertFalse(Files.exists(fixture.layout.event(1)));
    }

    @Test void strictPreparedRejectsMissingNullWrongTypesFieldsAndNoncanonicalBytes() throws Exception {
        WriterFixture fixture = new WriterFixture(root.resolve("strict"));
        byte[] actual = WriterTransactionCodec.encodePrepared(fixture.writer.preview(WriterFixture.settled("strict", 1048, 2)));
        ObjectNode missing = object(actual); missing.remove("evidence");
        assertInvalidPrepared(missing);
        ObjectNode absentAsNull = object(actual); absentAsNull.putNull("sources"); assertInvalidPrepared(absentAsNull);
        ObjectNode wrongEvidence = object(actual); wrongEvidence.putArray("evidence").add(wrongEvidence.get("sources").get(0).deepCopy()); assertInvalidPrepared(wrongEvidence);
        ObjectNode extra = object(actual); extra.put("accepted", true); assertInvalidPrepared(extra);
        ObjectNode floatingSequence = object(actual); ((ObjectNode)floatingSequence.get("reduced")).put("sequence", 0.0); assertInvalidPrepared(floatingSequence);
        ObjectNode boolSequence = object(actual); ((ObjectNode)boolSequence.get("reduced")).put("sequence", false); assertInvalidPrepared(boolSequence);
        ObjectNode missingRecovery = object(actual); ((ObjectNode)missingRecovery.get("predecessor")).remove("snapshot_needs_recovery"); assertInvalidPrepared(missingRecovery);
        ObjectNode relative = object(actual); ((ObjectNode)relative.get("predecessor")).putArray("absent").add("relative.json"); assertInvalidPrepared(relative);
        byte[] whitespace = (new String(actual, StandardCharsets.UTF_8) + "\n").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> WriterTransactionCodec.decodePrepared(whitespace, WriterFixture.MACHINE));
    }

    @Test void receiptRetainsExactDispositionAndBooleanAndRejectsIntegerAliases() throws Exception {
        WriterFixture fixture = new WriterFixture(root.resolve("receipt"));
        Receipt actual = fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("receipt", 1048, 2)));
        byte[] encoded = WriterTransactionCodec.encodeReceipt(actual);
        ObjectNode floating = object(encoded); floating.put("writes", (double) actual.writes()); assertInvalidReceipt(floating);
        ObjectNode booleanCount = object(encoded); booleanCount.put("writes", true); assertInvalidReceipt(booleanCount);
        ObjectNode numericBoolean = object(encoded); numericBoolean.put("recovered_committed_receipt", 0); assertInvalidReceipt(numericBoolean);
        ObjectNode alias = object(encoded); alias.put("disposition", "committed"); assertInvalidReceipt(alias);
        ObjectNode extra = object(encoded); extra.put("fixture_ready", true); assertInvalidReceipt(extra);
    }

    @Test void nativeIdentityDecimalDataAndEmptyCollectionsRoundtripWithoutBecomingPhysicalProof() throws Exception {
        WriterFixture fixture = new WriterFixture(root.resolve("decimal"));
        Prepared actual = fixture.writer.preview(WriterFixture.settled("decimal", 1048, 2));
        Pin original = actual.sources().getFirst();
        // Deliberately constructed DATA exercises the decimal codec only and is never submitted to the writer.
        Pin decimalData = new Pin(original.reference(), new FileIdentity("18446744073709551615", "9007199254740993",
                "18446744073709551615", original.identity().modifiedInstant(), original.reference().bytes()));
        Prepared data = new Prepared(actual.predecessor(), actual.request(), List.of(decimalData), actual.evidence(), actual.reduced(), actual.preconditionDigest());
        Prepared roundtrip = WriterTransactionCodec.decodePrepared(WriterTransactionCodec.encodePrepared(data), WriterFixture.MACHINE);
        assertEquals(decimalData, roundtrip.sources().getFirst());
        assertEquals(actual.predecessor().absent(), roundtrip.predecessor().absent());
        assertEquals(actual.predecessor().indexRepairs(), roundtrip.predecessor().indexRepairs());
    }

    private static ObjectNode object(byte[] bytes) { return ContinuityJson.parseObject(bytes, WriterTransactionCodec.MAXIMUM_BYTES); }
    private static void assertInvalidPrepared(ObjectNode row) {
        assertThrows(IllegalArgumentException.class, () -> WriterTransactionCodec.decodePrepared(
                ContinuityJson.canonical(row, WriterTransactionCodec.MAXIMUM_BYTES), WriterFixture.MACHINE));
    }
    private static void assertInvalidReceipt(ObjectNode row) {
        assertThrows(IllegalArgumentException.class, () -> WriterTransactionCodec.decodeReceipt(
                ContinuityJson.canonical(row, WriterTransactionCodec.MAXIMUM_BYTES), WriterFixture.MACHINE));
    }
}
