package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.contracts.ExactRef;

/** Real temporary Windows files and production capture; no current Driver, Root Ready or Game credit. */
final class RootOrdinaryClaimOriginalsTest {
    @TempDir Path temporary;
    static byte[] legacy(String request, String actor) {
        return ("{\"schema\":\"ck3-ordinary-interaction-once-claim-v1\",\"request_id\":\"" + request + "\",\"binding\":{\"native_revision\":11},"
                + "\"action_identity\":{\"game_pid\":121,\"actor_id\":" + actor + ",\"process_create_time\":1792800000.123456,\"interaction_key\":\"educate_child_interaction\",\"recipient_id\":4000000002,\"action\":\"initiate_ordinary\"},"
                + "\"claim_ordinal\":0,\"host_provenance\":null,\"new_intent_lineage\":null,\"status\":\"claimed_result_unknown_no_retry\"}").getBytes(StandardCharsets.UTF_8);
    }
    private ExactRef reference(String name, byte[] bytes) { return new ExactRef(temporary.resolve(name).toString(), bytes.length, ActionCodec.sha256(bytes)); }
    @Test void actualLegacyFilesBecomeConservativeBlockersWithoutInventingExactBirthOrClaims() throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows(), "actual native source identity regression requires Windows");
        Path directory = Files.createDirectory(temporary.resolve("ordinary-interaction-actions"));
        byte[] raw = legacy("old-original-request", "2147483647"); Files.write(directory.resolve("old.00000000.claim.json"), raw);
        var actual = RootOrdinaryClaimOriginals.capture(directory); assertEquals(1, actual.originals().size());
        var state = actual.state("fixture-claim-machine", List.of(reference("retained-original.json", raw)));
        assertEquals(state, OrdinaryOnceClaims.decode(OrdinaryOnceClaims.encode(state)));
        assertTrue(state.claims().isEmpty()); assertTrue(state.consumptions().isEmpty()); assertEquals(1, state.legacyBlockers().size());
        assertEquals(2_147_483_647L, state.legacyBlockers().getFirst().actorId());
        var identity = new OrdinaryOnceClaims.Identity("fixture-claim-machine", 121, "134999999999999999", 2_147_483_647L, "educate_child_interaction", 4_000_000_002L);
        var next = new OrdinaryOnceClaims.Request(identity, new OrdinaryOnceClaims.Binding("native:12", "13", "12", "1000", "2", "episode"), "next-request");
        assertThrows(IllegalArgumentException.class, () -> OrdinaryOnceClaims.prepareClaim(state, next));
        assertFalse(new String(OrdinaryOnceClaims.encode(state), StandardCharsets.UTF_8).contains("creation_filetime_decimal"));
    }
    @Test void missingDirectoryCannotBeAnEmptySeedWhileActualZeroCensusRetainsNativeDirectoryIdentity() throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows());
        assertThrows(java.io.IOException.class, () -> RootOrdinaryClaimOriginals.capture(temporary.resolve("missing")));
        var actual = RootOrdinaryClaimOriginals.capture(Files.createDirectory(temporary.resolve("actual-zero-census")));
        assertNotNull(actual.identity()); actual.requireUnchanged();
        assertTrue(actual.state("fixture-claim-machine", List.of()).claims().isEmpty());
    }
    @Test void samePathSameBytesReplacementAndAddedClaimsInvalidateTheActualCensus() throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows());
        Path directory = Files.createDirectory(temporary.resolve("identity-census")), path = directory.resolve("one.claim.json");
        byte[] raw = legacy("original", "2147483647"); Files.write(path, raw);
        var captured = RootOrdinaryClaimOriginals.capture(directory);
        Files.move(path, directory.resolve("retained-original.json")); Files.write(path, raw);
        assertThrows(java.io.IOException.class, captured::requireUnchanged);
        var second = RootOrdinaryClaimOriginals.capture(directory); Files.write(directory.resolve("two.CLAIM.JSON"), legacy("another", "2147483647"));
        assertThrows(IllegalArgumentException.class, second::requireUnchanged);
    }
    @Test void unsignedLegacyWireActorCannotBecomeModernSignedBlocker() throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows(), "actual legacy capture regression requires Windows");
        byte[] raw = legacy("unsigned-actor-original", "4000000001");
        var decoded = RootOrdinaryClaimOriginals.decodeLegacy(raw);
        assertEquals(4_000_000_001L, decoded.actorId(), "legacy wire decode retains its original unsigned value");
        assertEquals(4_000_000_002L, decoded.recipientId(), "recipient keeps the independent unsigned FullID domain");
        Path directory = Files.createDirectory(temporary.resolve("unsigned-actor-original"));
        Path original = directory.resolve("unsigned.claim.json"); Files.write(original, raw);
        var captured = RootOrdinaryClaimOriginals.capture(directory);
        assertEquals(1, captured.originals().size());
        assertEquals(decoded, captured.originals().getFirst().legacy());
        assertArrayEquals(raw, captured.originals().getFirst().bytes());
        ExactRef retained = reference("retained-unsigned-original.json", raw);
        assertThrows(IllegalArgumentException.class, () -> captured.state("fixture-claim-machine", List.of(retained)));
        assertArrayEquals(raw, Files.readAllBytes(original), "refusal preserves the exact original bytes");
        captured.requireUnchanged();
    }
    @Test void malformedRuntimeTypesMissingAndExtraFieldsNeverDisappearFromMigration() {
        for (String actor : List.of("true", "1.0", "\"4000000001\"", "null", "-1", "4294967295"))
            assertThrows(IllegalArgumentException.class, () -> RootOrdinaryClaimOriginals.decodeLegacy(legacy("source", actor)));
        byte[] raw = legacy("source", "2147483647");
        String valid = new String(raw, StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> RootOrdinaryClaimOriginals.decodeLegacy(valid.replace("\"host_provenance\":null,", "").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> RootOrdinaryClaimOriginals.decodeLegacy(valid.replaceFirst("\\{", "{\"native_ok\":true,").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> RootOrdinaryClaimOriginals.decodeLegacy(valid.replace("claimed_result_unknown_no_retry", "ack_released").getBytes(StandardCharsets.UTF_8)));
    }
}
