package org.xar.ck3.control.application.readiness;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.contracts.ExactRef;

/** Software DATA contract tests; these records do not fabricate Root/Game authority. */
final class NativeSourceProofCodecTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String SHA = "a".repeat(64);
    private static final ExactRef HOST = ref("host.json"), GAME = ref("ck3.exe"), EVIDENCE = ref("native.json");

    @Test void completeProducerCodecRoundtripPreservesEveryWideOriginalIdentityField() throws Exception {
        NativeSourceProofDocument original = document();
        byte[] bytes = NativeSourceProofCodec.encode(original);
        assertEquals(original, NativeSourceProofCodec.decode(bytes));
        assertArrayEquals(bytes, NativeSourceProofCodec.encode(NativeSourceProofCodec.decode(bytes)));
        SourceWitness retained = NativeSourceProofCodec.decode(bytes).liveWitnesses().get(0);
        assertEquals("340282366920938463463374607431768211455", retained.nativeFile().fileIdDecimal());
        assertEquals("18446744073709551615", retained.nativeFile().creationFiletimeDecimal());
        assertEquals("9007199254740993", retained.nativeFile().lastWriteFiletimeDecimal());
        assertEquals("ffffffffffffffff", retained.nativeFile().legacyFileIdHex());
        ObjectNode nativeJson = facts((ObjectNode) JSON.readTree(bytes));
        assertEquals("18446744073709551615", nativeJson.get("legacy_file_id_decimal").textValue());
        assertFalse(nativeJson.has("legacy_file_id_hex"));
        assertEquals(0xffff_ffffL, retained.nativeFile().linkCount());
        assertThrows(UnsupportedOperationException.class, () -> original.liveWitnesses().clear());
        assertThrows(UnsupportedOperationException.class, () -> original.completeEvidenceClosure().clear());
    }

    @Test void v2IsMissingEvenWhenItsHashClosureIsIdentical() throws Exception {
        ObjectNode old = json(); old.put("schema", "xar.java-root-native-source-proof/v2"); old.remove("live_witnesses");
        assertRejected(old);
        old.set("live_witnesses", JSON.createArrayNode()); assertRejected(old);
    }

    @Test void completeDurableProofMayExceedSharedSmallReceiptBudget() throws Exception {
        var original = document(); List<SourceWitness> witnesses = new ArrayList<>(original.liveWitnesses());
        for (int index = 0; index < 2500; index++)
            witnesses.add(new SourceWitness(ref("runtime/actual-source-" + index + ".java"), identity()));
        var large = new NativeSourceProofDocument(original.machineId(), original.sessionId(), original.observedAtUtc(),
                original.mode(), original.hostConfiguration(), original.source(), original.ownerSourceEpoch(),
                original.sourceEpochManifest(), original.gameExecutable(), original.completeEvidenceClosure(), witnesses);
        byte[] encoded = NativeSourceProofCodec.encode(large);
        assertTrue(encoded.length > 1_048_576);
        assertEquals(large, NativeSourceProofCodec.decode(encoded));
    }

    @Test void identityCannotPassThroughJsonNumberBooleanNullOrNoncanonicalText() throws Exception {
        for (String field : List.of("volume_serial_decimal", "file_id_decimal", "legacy_volume_serial_decimal", "legacy_file_id_decimal",
                "creation_filetime_decimal", "last_write_filetime_decimal", "change_filetime_decimal")) {
            ObjectNode numeric = json(); facts(numeric).put(field, 9_007_199_254_740_993L); assertRejected(numeric);
            ObjectNode bool = json(); facts(bool).put(field, true); assertRejected(bool);
            ObjectNode missing = json(); facts(missing).remove(field); assertRejected(missing);
            ObjectNode nullable = json(); facts(nullable).putNull(field); assertRejected(nullable);
            ObjectNode leadingZero = json(); facts(leadingZero).put(field, "01"); assertRejected(leadingZero);
        }
        ObjectNode over128 = json(); facts(over128).put("file_id_decimal", "340282366920938463463374607431768211456"); assertRejected(over128);
        ObjectNode over64 = json(); facts(over64).put("creation_filetime_decimal", "18446744073709551616"); assertRejected(over64);
        ObjectNode overLegacy64 = json(); facts(overLegacy64).put("legacy_file_id_decimal", "18446744073709551616"); assertRejected(overLegacy64);
        ObjectNode floatSize = json(); facts(floatSize).put("logical_bytes", 3.0); assertRejected(floatSize);
        ObjectNode boolSize = json(); facts(boolSize).put("allocated_bytes", true); assertRejected(boolSize);
        ObjectNode unsafeSize = json(); facts(unsafeSize).put("allocated_bytes", 9_007_199_254_740_992L); assertRejected(unsafeSize);
        ObjectNode zeroLinks = json(); facts(zeroLinks).put("link_count", 0); assertRejected(zeroLinks);
        ObjectNode overDword = json(); facts(overDword).put("link_count", 4_294_967_296L); assertRejected(overDword);
    }

    @Test void requiresClosedFieldsWitnessCoverageEpochBindingAndActualMode() throws Exception {
        ObjectNode missing = json(); missing.remove("source"); assertRejected(missing);
        ObjectNode extra = json(); extra.put("current", true); assertRejected(extra);
        ObjectNode missingWitness = json(); missingWitness.withArray("live_witnesses").remove(0); assertRejected(missingWitness);
        ObjectNode nullWitness = json(); nullWitness.putNull("live_witnesses"); assertRejected(nullWitness);
        ObjectNode duplicate = json(); duplicate.withArray("live_witnesses").add(duplicate.withArray("live_witnesses").get(0).deepCopy()); assertRejected(duplicate);
        ObjectNode size = json(); facts(size).put("logical_bytes", 4); assertRejected(size);
        ObjectNode epoch = json(); epoch.put("owner_source_epoch", "b".repeat(64)); assertRejected(epoch);
        ObjectNode mode = json(); mode.put("mode", "MCP"); assertRejected(mode);
        ObjectNode time = json(); time.put("observed_at_utc", "2026-10-24T19:00:00+08:00"); assertRejected(time);
        ObjectNode relative = json(); ((ObjectNode) relative.get("source")).put("path", "relative.json"); assertRejected(relative);
    }

    @Test void duplicateKeysTrailingTokensInvalidUtf8AndExcessRoleBytesReject() throws Exception {
        String valid = new String(NativeSourceProofCodec.encode(document()), StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> NativeSourceProofCodec.decode(("{\"schema\":\"duplicate\"," + valid.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class, () -> NativeSourceProofCodec.decode((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class, () -> NativeSourceProofCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IOException.class, () -> NativeSourceProofCodec.decode(new byte[NativeSourceProofDocument.MAXIMUM_BYTES + 1]));
    }

    @Test void immutableIdentityComparisonPreservesPhysicalReplacementFailure() {
        NativeSourceFileIdentity original = identity();
        NativeSourceFileIdentity changedAllocation = new NativeSourceFileIdentity(original.volumeSerialDecimal(), original.fileIdDecimal(),
                original.legacyVolumeSerialDecimal(), original.legacyFileIdHex(), original.creationFiletimeDecimal(),
                original.lastWriteFiletimeDecimal(), "10", 3, 8192, 1);
        assertTrue(original.sameImmutableFile(changedAllocation));
        NativeSourceFileIdentity replaced = new NativeSourceFileIdentity(original.volumeSerialDecimal(), "9007199254740994",
                original.legacyVolumeSerialDecimal(), original.legacyFileIdHex(), original.creationFiletimeDecimal(),
                original.lastWriteFiletimeDecimal(), original.changeFiletimeDecimal(), 3, 4096, 1);
        assertFalse(original.sameImmutableFile(replaced));
    }

    @Test void decimalWireRoundtripRetainsLeadingZerosInOriginalExporterHexMemory() throws Exception {
        var original = document(); var nativeFile = original.liveWitnesses().get(0).nativeFile();
        NativeSourceFileIdentity leadingZero = new NativeSourceFileIdentity(nativeFile.volumeSerialDecimal(), nativeFile.fileIdDecimal(),
                nativeFile.legacyVolumeSerialDecimal(), "0000000000000001", nativeFile.creationFiletimeDecimal(),
                nativeFile.lastWriteFiletimeDecimal(), nativeFile.changeFiletimeDecimal(), 3, 4096, 1);
        List<SourceWitness> witnesses = new ArrayList<>(original.liveWitnesses()); witnesses.set(0, new SourceWitness(HOST, leadingZero));
        var value = new NativeSourceProofDocument(original.machineId(), original.sessionId(), original.observedAtUtc(), original.mode(),
                original.hostConfiguration(), original.source(), original.ownerSourceEpoch(), original.sourceEpochManifest(),
                original.gameExecutable(), original.completeEvidenceClosure(), witnesses);
        byte[] bytes = NativeSourceProofCodec.encode(value);
        assertEquals("1", facts((ObjectNode) JSON.readTree(bytes)).get("legacy_file_id_decimal").textValue());
        assertEquals("0000000000000001", NativeSourceProofCodec.decode(bytes).liveWitnesses().get(0).nativeFile().legacyFileIdHex());
        assertEquals(value, NativeSourceProofCodec.decode(bytes));
    }

    private static NativeSourceProofDocument document() {
        List<SourceWitness> original = new ArrayList<>(List.of(new SourceWitness(HOST, identity()),
                new SourceWitness(GAME, identity()), new SourceWitness(EVIDENCE, identity())));
        NativeSourceProofDocument value = new NativeSourceProofDocument("software-data-machine", "software-data-session",
                "2026-10-24T19:00:00Z", NativeSourceProofDocument.Mode.HTTP, HOST, ref("original-source.json"), SHA,
                ref("epoch.json"), GAME, List.of(GAME, EVIDENCE), original);
        original.clear(); return value;
    }

    private static NativeSourceFileIdentity identity() {
        return new NativeSourceFileIdentity("18446744073709551615", "340282366920938463463374607431768211455",
                "4294967295", "ffffffffffffffff", "18446744073709551615", "9007199254740993",
                "9007199254740995", 3, 4096, 0xffff_ffffL);
    }

    private static ExactRef ref(String name) { return new ExactRef("D:/software-data-only/" + name, 3, SHA); }
    private static ObjectNode json() throws IOException { return (ObjectNode) JSON.readTree(NativeSourceProofCodec.encode(document())); }
    private static ObjectNode facts(ObjectNode row) { return (ObjectNode) row.get("live_witnesses").get(0).get("native_file"); }
    private static void assertRejected(ObjectNode row) throws IOException {
        byte[] bytes = JSON.writeValueAsBytes(row);
        assertThrows(IOException.class, () -> NativeSourceProofCodec.decode(bytes));
    }
}
