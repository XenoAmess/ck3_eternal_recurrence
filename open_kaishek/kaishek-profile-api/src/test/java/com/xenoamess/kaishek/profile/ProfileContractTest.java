package com.xenoamess.kaishek.profile;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Focused tests for the profile identity and deterministic serialization contracts. */
class ProfileContractTest {
    private static final String HASH = "A".repeat(64);

    @Test
    void fingerprintNormalizesHashesAndKeepsOptionalIdentity() {
        var fingerprint = new BuildFingerprint("ck3", "1.19.0.6", HASH,
                List.of(HASH), null, HASH.toLowerCase());
        assertEquals(HASH.toLowerCase(), fingerprint.exeSha256());
        assertEquals(HASH.toLowerCase(), fingerprint.assetHashes().get(0));
        assertEquals(HASH.toLowerCase(), fingerprint.configurationHash());
        assertNull(fingerprint.modTreeHash());
    }

    @Test
    void registryIsImmutableAndRejectsAmbiguousEntries() {
        var descriptor = new OpcodeDescriptor("known", "1.19.0.6", OpcodeKind.EFFECT,
                InputType.NONE, ScopeType.THIS, List.of(), RandomnessClass.DETERMINISTIC,
                false, false, false);
        var registry = new OpcodeRegistry(List.of(descriptor));
        assertTrue(registry.contains("known"));
        assertTrue(registry.find(null).isEmpty());
        assertThrows(UnsupportedOperationException.class, () -> registry.all().clear());
        assertThrows(IllegalArgumentException.class, () -> new OpcodeRegistry(List.of(descriptor, descriptor)));
        assertThrows(IllegalArgumentException.class,
                () -> new OpcodeRegistry(Map.of("other", descriptor)));
        assertEquals(0, descriptor.minParameters());
        assertEquals(0, descriptor.maxParameters());
        assertThrows(IllegalArgumentException.class,
                () -> new OpcodeDescriptor("bad", "1.19.0.6", OpcodeKind.EFFECT,
                        InputType.NONE, ScopeType.THIS, List.of(),
                        RandomnessClass.DETERMINISTIC, false, false, false, 2, 1));
    }

    @Test
    void jsonWriterSortsSetsAndRejectsNonFiniteNumbers() {
        assertEquals("[\"a\",\"b\"]", JsonCodec.write(Set.of("b", "a")));
        assertThrows(IllegalArgumentException.class, () -> JsonCodec.write(Double.NaN));
        assertThrows(IllegalArgumentException.class, () -> JsonCodec.write(Double.POSITIVE_INFINITY));
    }

    @Test
    void genericProjectionPreservesInterfaceOpcodeKind() {
        var descriptor = new OpcodeDescriptor("GetPlayer", "synthetic", OpcodeKind.GUI,
                InputType.SCOPE, ScopeType.ROOT, List.of(), RandomnessClass.DETERMINISTIC,
                false, true, false);
        var fingerprint = new BuildFingerprint("synthetic", "synthetic", HASH, List.of(), null, null);
        var profile = new GameProfile("synthetic", "synthetic", fingerprint,
                new OpcodeRegistry(List.of(descriptor)), Set.of(), Map.of());
        assertEquals(OpcodeSpec.Kind.INTERFACE,
                KaishekProfile.fromGameProfile(profile).opcode("GetPlayer").kind());
    }
}
