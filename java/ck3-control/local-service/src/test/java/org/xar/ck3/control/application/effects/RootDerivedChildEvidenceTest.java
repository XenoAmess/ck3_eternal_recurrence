package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Codec/custody boundary regressions. These values never establish a private Root or native permission. */
final class RootDerivedChildEvidenceTest {
    @TempDir Path temporary;
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static ExactRef ref(String role) { return new ExactRef("D:/derived-data-only/" + role, 1, "a".repeat(64)); }
    private static ObjectNode row() { return assertInstanceOf(ObjectNode.class, StrictJson.parse(data().encode().bytes())); }
    private static RootDerivedChildEvidence data() {
        return new RootDerivedChildEvidence(9007199254740991L, "b".repeat(64), "actual-handler-data-only",
                ref("parent-receipt"), "c".repeat(64), "d".repeat(64), 2, ref("parent-native"), ref("parent-driver"),
                ref("before-native"), ref("before-driver"), ref("parent-producer"), ref("parent-decoder"),
                ref("child-producer"), ref("child-decoder"), ref("child-verifier"), ref("source"), List.of(ref("previous-child")));
    }
    @Test void closedTypedLocatorRoundtripsItsDistinctOrderedOriginsWithoutCreatingAnAuthority() {
        var data = data(); var decoded = RootDerivedChildEvidence.decode(data.encode());
        assertEquals(data, decoded); assertEquals(data.encode(), decoded.encode());
        assertEquals(9007199254740991L, decoded.actualHeadSequence());
        assertNotEquals(decoded.parentNative(), decoded.beforeNative());
        assertEquals(List.of(ref("previous-child")), decoded.previousChildren());
    }
    @Test void wrongMissingNullBooleanFractionalUnsafeSequenceAndOrdinalInputsAreRejected() {
        for (String field : List.of("actual_head_sequence", "child_ordinal")) {
            for (String value : List.of("null", "true", "1.0", "9007199254740992", "-1")) {
                assertThrows(IllegalArgumentException.class, () -> {
                    ObjectNode row = row(); row.set(field, StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
                    RootDerivedChildEvidence.decode(raw(row.toString()));
                });
            }
            ObjectNode missing = row(); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> RootDerivedChildEvidence.decode(raw(missing.toString())));
        }
        ObjectNode schema = row(); schema.put("schema", "xar.army-retreat-derived-child/v1");
        assertThrows(IllegalArgumentException.class, () -> RootDerivedChildEvidence.decode(raw(schema.toString())));
        ObjectNode extra = row(); extra.put("native_permission", true);
        assertThrows(IllegalArgumentException.class, () -> RootDerivedChildEvidence.decode(raw(extra.toString())));
    }
    @Test void orderedChildClosureAndPhysicalOriginalsCannotBeOmittedOrCollapsed() {
        ObjectNode row = row(); row.putArray("previous_children");
        assertThrows(IllegalArgumentException.class, () -> RootDerivedChildEvidence.decode(raw(row.toString())));
        ObjectNode nil = row(); nil.putNull("previous_children");
        assertThrows(IllegalArgumentException.class, () -> RootDerivedChildEvidence.decode(raw(nil.toString())));
        ObjectNode duplicates = row(); duplicates.put("child_ordinal", 3);
        assertInstanceOf(ArrayNode.class, duplicates.get("previous_children")).add(ref("previous-child").toJson());
        assertThrows(IllegalArgumentException.class, () -> RootDerivedChildEvidence.decode(raw(duplicates.toString())));
        for (String field : List.of("parent_receipt", "parent_native", "parent_driver", "before_native", "before_driver",
                "parent_implementation", "child_decoder", "child_verifier", "source_qualification")) {
            ObjectNode missing = row(); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> RootDerivedChildEvidence.decode(raw(missing.toString())));
        }
    }
    @Test void completeOrderedLocatorAboveDefaultJsonLimitUsesItsExplicitClosedBudget() {
        var value = data(); var previous = java.util.stream.IntStream.range(0, 255)
                .mapToObj(index -> ref("previous-" + index + "-" + "p".repeat(220))).toList();
        var large = new RootDerivedChildEvidence(value.actualHeadSequence(), value.actualHeadDigest(), value.handlerId(),
                value.parentReceipt(), value.parentBodySha256(), value.childBodySha256(), 256, value.parentNative(), value.parentDriver(),
                value.beforeNative(), value.beforeDriver(), value.parentImplementation(), value.parentDecoder(), value.childImplementation(),
                value.childDecoder(), value.childVerifier(), value.sourceQualification(), previous);
        var encoded = large.encode();
        assertTrue(encoded.bytes().length > 65536 && encoded.bytes().length <= RootDerivedChildEvidence.MAX_BYTES);
        assertEquals(large, RootDerivedChildEvidence.decode(encoded));
    }
    @Test void actualWriterUnknownArchiveToGuardLocatorReadbackDoesNotReadNativeOrResubmit() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("actual-custody"), true)) {
            var pending = fixture.coordinator.execute(fixture.command("original-custody"));
            var attempt = ActionTransitions.attempt(pending.state()).orElseThrow(); var originalGuard = attempt.guard();
            int reads = fixture.nativeReadWrites();
            fixture.writer.locked(same -> fixture.archive.inSession(same, archive -> {
                var parentRef = archive.receiptReferenceOf(pending); var body = archive.preserveMaterial(raw("{\"fixture_data_only\":true}"));
                // Deliberately has no qualified composite parent. This proves custody parsing, never live admission/replay.
                final RootDerivedChildEvidence proof;
                try {
                    proof = new RootDerivedChildEvidence(same.head().state().sequence(), same.head().digest(), "unqualified-data-only",
                            parentRef, pending.bodySha256(), pending.bodySha256(), 1, originalGuard.nativeEvidence(), body,
                            originalGuard.nativeEvidence(), body, body, body, body, body, body, body, List.of());
                } catch (java.io.IOException failure) {
                    throw new java.io.UncheckedIOException(failure);
                }
                ExactRef preserved = archive.preserveMaterial(proof.encode());
                var guard = new GuardEvidence(originalGuard.origin(), originalGuard.source(), originalGuard.sessionId(),
                        originalGuard.connectionGeneration(), originalGuard.operation(), originalGuard.nativeEvidence(), originalGuard.capabilityEvidence(),
                        originalGuard.authorityId(), originalGuard.observedAt(), originalGuard.validUntil(),
                        List.of(originalGuard.supportingEvidence().getFirst(), preserved));
                assertEquals(proof, RootDerivedChildEvidence.requireGuard(guard, archive));
                assertFalse(pending.settled()); assertFalse(pending.eligibleAdvance());
                var wrong = new RootDerivedChildEvidence(proof.actualHeadSequence(), proof.actualHeadDigest(), proof.handlerId(),
                        proof.parentReceipt(), proof.parentBodySha256(), proof.childBodySha256(), proof.childOrdinal(), proof.parentNative(), proof.parentDriver(),
                        body, proof.beforeDriver(), body, body, body, body, body, body, List.of());
                ExactRef wrongRef = archive.preserveMaterial(wrong.encode());
                var changed = new GuardEvidence(guard.origin(), guard.source(), guard.sessionId(), guard.connectionGeneration(), guard.operation(),
                        guard.nativeEvidence(), guard.capabilityEvidence(), guard.authorityId(), guard.observedAt(), guard.validUntil(),
                        List.of(guard.supportingEvidence().getFirst(), wrongRef));
                assertThrows(IllegalArgumentException.class, () -> RootDerivedChildEvidence.requireGuard(changed, archive));
                return null;
            }));
            assertEquals(reads, fixture.nativeReadWrites()); assertEquals(1, fixture.nativeActionWrites());
        }
    }
}
