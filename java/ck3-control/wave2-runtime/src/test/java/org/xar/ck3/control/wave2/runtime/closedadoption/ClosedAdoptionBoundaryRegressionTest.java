package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Original small receipt fixtures, production counter accumulator and actual protocol/document entry points. */
class ClosedAdoptionBoundaryRegressionTest {
    private static Path repo() {
        String explicit = System.getProperty("xar.repo");
        if (explicit == null || explicit.isBlank()) { explicit = System.getenv("XAR_REPO_ROOT"); }
        Path path = Path.of(explicit == null || explicit.isBlank() ? System.getProperty("user.dir") : explicit).toAbsolutePath();
        for (int i = 0; i < 6 && path != null; i++, path = path.getParent()) {
            if (Files.isRegularFile(path.resolve("java/ck3-control/wave2-runtime/src/test/resources/closedadoption/original-business-sources.json"))) { return path; }
        }
        throw new IllegalStateException("UNAVAILABLE: original fixture repository; set xar.repo or XAR_REPO_ROOT");
    }
    private static byte[] bounded(Path path) throws IOException {
        try (var input = Files.newInputStream(path)) {
            byte[] raw = input.readNBytes(RecoveryEvidence.MAX_BYTES + 1);
            assertTrue(raw.length > 0 && raw.length <= RecoveryEvidence.MAX_BYTES); return raw;
        }
    }
    private static ObjectNode object(byte[] raw) {
        JsonNode value = StrictJson.parse(raw); assertInstanceOf(ObjectNode.class, value); return (ObjectNode) value;
    }
    private static byte[] exact(JsonNode value) throws IOException {
        ExactRef ref = ExactRef.fromJson(value); String name = ref.path().replace('\\', '/').toLowerCase(java.util.Locale.ROOT);
        assertFalse(name.endsWith("/driver-state.json") || name.endsWith(".ck3") || name.endsWith(".sav"));
        byte[] raw = bounded(Path.of(ref.path())); assertEquals(ref.bytes(), raw.length); assertEquals(ref.sha256(), RecoveryEvidence.sha256(raw)); return raw;
    }
    @Test void originalSevenCycleCountsRetainExactIntegerDomainAndReadonlySkipOrdering() throws IOException {
        Path base = repo().resolve("java/ck3-control/wave2-runtime/src/test/resources/closedadoption");
        ObjectNode manifest = object(bounded(base.resolve("original-business-sources.json")));
        ObjectNode seed = object(exact(manifest.get("sources").get("seed").get("ref")));
        ObjectNode counts = ((ObjectNode) seed.get("counts")).deepCopy();
        for (JsonNode cycle : manifest.get("cycles")) {
            ObjectNode event = object(exact(cycle.get("event").get("ref")));
            ClosedPartialBusinessAuthority.observeCounts(counts, (ObjectNode) event.get("observation"));
            assertEquals(event.get("cumulative_observation_counts"), counts, "original event comparison before optional checkpoint skip");
            if (!cycle.get("readonlySaveSkip").isNull()) {
                ObjectNode skip = object(exact(cycle.get("readonlySaveSkip").get("ref")));
                assertEquals("unchanged_readonly_evidence_chain", skip.get("status").textValue());
                ClosedPartialBusinessAuthority.recordReadonlyCheckpointSkip(counts);
            }
        }
        Path rawState = repo().resolve("java/ck3-control/admission-contracts/src/test/resources/closedpartial/n46-raw-state.actual.json");
        assertEquals(object(bounded(rawState)).get("counts"), counts, "all counters, including unchanged material credit, match the original final state");
        assertEquals(1594, counts.get("typed_nonmaterial_observation_turns").intValue());
        assertEquals(26, counts.get("checkpoint_readonly_skipped").intValue());
    }
    @Test void productionCounterIncrementRejectsMissingBooleanFloatAndOutOfRangeRatherThanDefaulting() {
        ObjectNode observation = StrictJson.object(); observation.put("primitive_accepted",true);
        for (JsonNode wrong : new JsonNode[] {null, StrictJson.parse("true".getBytes(StandardCharsets.UTF_8)),
                StrictJson.parse("1.0".getBytes(StandardCharsets.UTF_8)), StrictJson.parse("9007199254740991".getBytes(StandardCharsets.UTF_8))}) {
            ObjectNode counts = StrictJson.object(); if (wrong != null) { counts.set("primitive_accepted_turns",wrong); }
            assertThrows(ContractViolationException.class, () -> ClosedPartialBusinessAuthority.observeCounts(counts,observation));
        }
    }
    /** Synthetic stat fields test envelope decoding only; no SDK or native custody claim is made. */
    private static ObjectNode document(byte[] raw) {
        ObjectNode row = StrictJson.object();
        ExactRef ref = new ExactRef(Path.of("synthetic-small-document.json").toAbsolutePath().toString(), raw.length, RecoveryEvidence.sha256(raw));
        row.set("ref",ref.toJson()); row.set("identity",new FileStatIdentity(BigInteger.valueOf(raw.length),"1","1").toJson());
        row.put("raw_utf8",new String(raw,StandardCharsets.UTF_8)); return row;
    }
    @Test void actualHeadRawDocumentCrossesMetadataTextCapThroughProductionWireAndDocumentDecoder() throws IOException {
        byte[] head = bounded(repo().resolve("java/ck3-control/admission-contracts/src/test/resources/closedpartial/n46-head240.actual.json"));
        assertTrue(head.length > 32_768); ObjectNode row = document(head);
        ByteArrayOutputStream stream = new ByteArrayOutputStream(); OriginalWriterTransaction.send(stream,row);
        JsonNode received = OriginalWriterTransaction.read(new ByteArrayInputStream(stream.toByteArray()));
        assertArrayEquals(head,OriginalWriterTransaction.Document.decode(received).evidence().bytes());
        assertThrows(ContractViolationException.class, () -> StrictJson.canonical(row));
    }
    @Test void rawDocumentQuotesAllEscapesAndRetainsFloatingTokensWhileRejectingInvalidUnicodeAndDocumentOverflow() throws IOException {
        ObjectNode inner = StrictJson.object(); inner.put("escaped","\"\\\b\f\n\r\t\u0001汉😀");
        byte[] raw = StrictJson.canonical(inner); ObjectNode row = document(raw);
        assertArrayEquals(raw,OriginalWriterTransaction.Document.decode(StrictJson.parse(ClosedAdoptionJson.encode(row))).evidence().bytes());
        ObjectNode invalid = row.deepCopy(); invalid.put("raw_utf8","{\"x\":\"" + '\ud800' + "\"}");
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionJson.encode(invalid));
        byte[] oversized = ("{\"x\":\"" + "a".repeat(RecoveryEvidence.MAX_BYTES - 7) + "\"}").getBytes(StandardCharsets.UTF_8);
        assertEquals(RecoveryEvidence.MAX_BYTES + 1,oversized.length);
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionJson.encode(document(oversized),OriginalWriterTransaction.MAX_PROTOCOL_BYTES));
        ObjectNode scalar = StrictJson.object(); scalar.put("unrelated","a".repeat(32_769));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionJson.encode(scalar,OriginalWriterTransaction.MAX_PROTOCOL_BYTES));
        ObjectNode floating = StrictJson.object(); floating.set("v",StrictJson.parse("6.0".getBytes(StandardCharsets.UTF_8)));
        assertTrue(StrictJson.parse(ClosedAdoptionJson.encode(floating)).get("v").isFloatingPointNumber());
    }
    @Test void actualWireAcceptsExact256KiBAndRejectsOneByteOverflowWithBoundedIndividualFields() throws IOException {
        ObjectNode row = StrictJson.object(); for (int i=0;i<8;i++) { row.put("k"+i,"a".repeat(32_000)); }
        row.put("padding",""); int padding=OriginalWriterTransaction.MAX_PROTOCOL_BYTES-ClosedAdoptionJson.encode(row,OriginalWriterTransaction.MAX_PROTOCOL_BYTES).length;
        assertTrue(padding < 32_768); row.put("padding","b".repeat(padding));
        ByteArrayOutputStream stream = new ByteArrayOutputStream(); OriginalWriterTransaction.send(stream,row);
        assertEquals(OriginalWriterTransaction.MAX_PROTOCOL_BYTES+1,stream.size());
        assertEquals(row,OriginalWriterTransaction.read(new ByteArrayInputStream(stream.toByteArray())));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionJson.encode(row));
        row.put("padding","b".repeat(padding+1));
        assertThrows(ContractViolationException.class, () -> OriginalWriterTransaction.send(new ByteArrayOutputStream(),row));
        byte[] raw = StrictJson.canonical(row,StrictJson.EXPLICIT_MAX_BYTES);
        assertThrows(IOException.class, () -> OriginalWriterTransaction.read(new ByteArrayInputStream(concatNewline(raw))));
    }
    private static byte[] concatNewline(byte[] raw) { byte[] line=java.util.Arrays.copyOf(raw,raw.length+1);line[raw.length]='\n';return line; }
}
