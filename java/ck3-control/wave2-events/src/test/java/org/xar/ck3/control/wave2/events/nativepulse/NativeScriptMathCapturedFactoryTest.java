package org.xar.ck3.control.wave2.events.nativepulse;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeScriptMathProgram.*;

/** Mandatory actual retained C24 RF input; no native image reader, fixture eligibility or loaded AST claim. */
final class NativeScriptMathCapturedFactoryTest {
    private static byte[] original() throws IOException {
        String configured = System.getProperty("xar.g2.m2.factory.raw.path");
        assertNotNull(configured, "actual retained whole factory RF is required; no skipped source regression");
        Path path = Path.of(configured);
        assertEquals(2922L, Files.size(path), "only the exact retained RF artifact may be consumed");
        return Files.readAllBytes(path);
    }
    @Test void actualWholeFactoryProducerProjectionArchiveAndColdReplayPreservePhysicalLayout() throws Exception {
        byte[] raw = original(); MemoryStore store = new MemoryStore(); ExactRef source = store.preserve(raw);
        assertEquals(FACTORY_SHA256, source.sha256()); FactoryReview review = reviewFactory(source, raw);
        assertEquals(296, review.allocationBytes()); assertEquals(48, review.operandOffset());
        assertEquals(288, review.opcodeOffset()); assertEquals(SIMPLE_VTABLE_RVA, review.nodeVtableRva());
        assertEquals(24, review.loadVtableSlot()); assertFalse(review.currentLoadedAstQualified()); assertFalse(review.operandLoadClosed());
        byte[] derived = NativeScriptMathProgramJson.encodeFactoryReview(review);
        assertEquals(review, NativeScriptMathProgramJson.replayFactoryReview(derived, source, raw));
        var record = NativeScriptMathProgramArchive.preserveFactory(source, store);
        var cold = NativeScriptMathProgramArchive.decodeFactory(NativeScriptMathProgramArchive.encodeFactory(record));
        assertEquals(record, cold); assertEquals(review, NativeScriptMathProgramArchive.replayFactory(cold, store));
        assertArrayEquals(raw, store.load(cold.original()));
    }
    @Test void truncatedOrChangedFunctionAndCoercedMissingExtraOrQualifiedProjectionAreRejected() throws Exception {
        byte[] raw = original(); MemoryStore store = new MemoryStore(); ExactRef source = store.preserve(raw);
        assertThrows(IllegalArgumentException.class, () -> reviewFactory(source, Arrays.copyOf(raw, raw.length - 1)));
        byte[] changed = raw.clone(); changed[0x374cc05 - 0x374c250] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> reviewFactory(source, changed));
        var review = reviewFactory(source, raw); byte[] encoded = NativeScriptMathProgramJson.encodeFactoryReview(review);
        for (String field : new String[]{"allocation_bytes", "operand_offset", "opcode_offset", "load_vtable_slot"}) {
            var row = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(encoded);
            row.put(field, true); byte[] coerced = StrictJson.canonical(row);
            assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgramJson.replayFactoryReview(coerced, source, raw));
            row = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(encoded); row.remove(field);
            byte[] missing = StrictJson.canonical(row); assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgramJson.replayFactoryReview(missing, source, raw));
        }
        var row = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(encoded); row.put("current_loaded_ast_qualified", true);
        byte[] forged = StrictJson.canonical(row); assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgramJson.replayFactoryReview(forged, source, raw));
        row = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(encoded); row.put("extra", 1);
        byte[] extra = StrictJson.canonical(row); assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgramJson.replayFactoryReview(extra, source, raw));
        var record = NativeScriptMathProgramArchive.preserveFactory(source, store); store.bytes.put(record.original().path(), changed);
        assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgramArchive.replayFactory(record, store));
    }
    private static final class MemoryStore implements NativeOnActionFieldArchive.Store {
        private final Map<String, byte[]> bytes = new HashMap<>(); private int sequence;
        @Override public ExactRef preserve(byte[] original) {
            try { byte[] raw = original.clone(); String path = "factory-memory/" + sequence++; bytes.put(path, raw);
                return new ExactRef(path, raw.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))); }
            catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        }
        @Override public byte[] load(ExactRef ref) throws IOException {
            byte[] raw = bytes.get(ref.path()); if (raw == null) throw new IOException("missing original"); return raw.clone();
        }
    }
}
