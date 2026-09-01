package com.xenoamess.kaishek.profile;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/** Contract checks for the version-pinned profile projection. */
class Ck3Profile11906Test {
    private final Ck3Profile11906 profile = new Ck3Profile11906();

    @Test
    void exactBuildIdentityIsPinned() {
        assertEquals(Ck3Profile11906.ID, profile.id());
        assertEquals(Ck3Profile11906.GAME_VERSION, profile.gameVersion());
        assertEquals(Ck3Profile11906.EXE_SHA256, profile.executableSha256());
        // BuildFingerprint canonicalizes hashes to lowercase while the
        // published profile constant retains the documentation's uppercase
        // spelling.
        assertEquals(Ck3Profile11906.EXE_SHA256.toLowerCase(java.util.Locale.ROOT),
                profile.fingerprint().exeSha256());
        assertEquals("ck3", profile.fingerprint().gameId());
        assertEquals(Ck3Profile11906.GAME_VERSION, profile.fingerprint().gameVersion());
    }

    @Test
    void genericProjectionAndSchemaShareTheSameOpcodeIds() {
        assertEquals(profile.opcodes().size(), profile.opcodeRegistry().size());
        assertTrue(profile.opcode("set_variable") != null);
        assertTrue(profile.opcodeRegistry().contains("set_variable"));
        assertEquals(Ck3Profile11906.GAME_VERSION,
                profile.opcodeRegistry().require("set_variable").profileVersion());
        assertEquals(profile.gameProfile().opcodes().size(), profile.opcodeRegistry().size());
        assertTrue(profile.certifiedSemantics().isEmpty(),
                "Phase 0 must not claim exact-build runtime certification");
        assertEquals(1, profile.opcodeRegistry().require("trigger_event").minParameters());
        assertEquals(2, profile.opcodeRegistry().require("trigger_event").maxParameters());
    }

    @Test
    void schemaArityMatchesEveryTypedOpcodeDescriptor() {
        for (OpcodeDescriptor descriptor : profile.opcodeRegistry().all()) {
            OpcodeSpec spec = profile.opcode(descriptor.id());
            assertNotNull(spec, "schema is missing " + descriptor.id());
            assertEquals(descriptor.minParameters(), spec.minParameters(), descriptor.id());
            assertEquals(descriptor.maxParameters(), spec.maxParameters(), descriptor.id());
        }
    }

    @Test
    void directoryMappingIsCaseAndSeparatorIndependent() {
        assertEquals(ScriptDomain.SCRIPTED_EFFECTS,
                profile.domainForPath("COMMON\\SCRIPTED_EFFECTS\\xar.txt"));
        assertEquals(ScriptDomain.ON_ACTION,
                profile.domainForPath("common/on_actions/xar.txt"));
        assertEquals(ScriptDomain.SCRIPTED_VALUES,
                profile.domainForPath("common/script_values/xar.txt"));
        assertEquals(ScriptDomain.INTERACTIONS,
                profile.domainForPath("common/character_interactions/xar.txt"));
        assertEquals(ScriptDomain.GUI_REGISTRATION,
                profile.domainForPath("gui/zg361_scoreboard.gui"));
        assertEquals(ScriptDomain.UNKNOWN, profile.domainForPath(null));
    }

    @Test
    void exposedCollectionsAreImmutable() {
        assertThrows(UnsupportedOperationException.class,
                () -> profile.allowedStructuralKeys().add("unsafe"));
        assertThrows(UnsupportedOperationException.class,
                () -> profile.opcodes().clear());
        assertThrows(UnsupportedOperationException.class,
                () -> profile.scopeLinks().clear());
        assertThrows(UnsupportedOperationException.class,
                () -> profile.gameProfile().certifiedSemantics().add("fake"));
    }
}
