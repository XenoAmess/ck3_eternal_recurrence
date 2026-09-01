package com.xenoamess.kaishek.zg361;

import com.xenoamess.kaishek.profile.BuildFingerprint;
import com.xenoamess.kaishek.profile.GameProfile;
import com.xenoamess.kaishek.profile.InputType;
import com.xenoamess.kaishek.profile.KaishekProfile;
import com.xenoamess.kaishek.profile.OpcodeDescriptor;
import com.xenoamess.kaishek.profile.OpcodeKind;
import com.xenoamess.kaishek.profile.OpcodeRegistry;
import com.xenoamess.kaishek.profile.OpcodeSpec;
import com.xenoamess.kaishek.profile.RandomnessClass;
import com.xenoamess.kaishek.profile.ScopeType;
import com.xenoamess.kaishek.profile.ScriptDomain;

import java.util.Collections;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Explicitly synthetic profile for the first 361 vertical-slice fixture.
 *
 * <p>This profile is not a CK3 build profile.  Its all-zero fingerprint and
 * namespaced opcodes make accidental use against CK3 impossible to mistake
 * for a certified native semantic.  Certification here only means that the
 * small in-memory fixture handlers are intentionally available to the local
 * finite runtime.</p>
 */
public final class Synthetic361Profile implements KaishekProfile {
    public static final String ID = "zg361-synthetic-014";
    public static final String GAME_ID = "zg361-synthetic";
    public static final String GAME_VERSION = "phase0-fixture-1";
    /** Deliberately non-CK3 identity; never use this as a real executable hash. */
    public static final String SYNTHETIC_EXE_SHA256 = "0".repeat(64);

    public static final String OPEN_CASE = "zg361_014_open_case";
    public static final String CHOOSE = "zg361_014_choose";
    public static final String CLOSE_CASE = "zg361_014_close_case";

    private static final BuildFingerprint FINGERPRINT = new BuildFingerprint(
            GAME_ID, GAME_VERSION, SYNTHETIC_EXE_SHA256, List.of(), null, null);

    private static final List<OpcodeDescriptor> DESCRIPTORS = List.of(
            descriptor(OPEN_CASE, List.of("case_id")),
            descriptor(CHOOSE, List.of("choice")),
            descriptor(CLOSE_CASE, List.of()));
    private static final OpcodeRegistry REGISTRY = new OpcodeRegistry(DESCRIPTORS);
    private static final Map<String, OpcodeSpec> SCHEMA = schema();
    private static final Set<String> CERTIFIED = Set.of(OPEN_CASE, CHOOSE, CLOSE_CASE);
    private static final Map<ScopeType, Set<ScopeType>> SCOPE_LINKS = identityLinks();

    @Override public String id() { return ID; }
    @Override public String gameVersion() { return GAME_VERSION; }
    @Override public String executableSha256() { return SYNTHETIC_EXE_SHA256; }
    @Override public ScriptDomain domainForPath(String sourcePath) { return ScriptDomain.fromPath(sourcePath); }
    @Override public OpcodeSpec opcode(String name) { return name == null ? null : SCHEMA.get(name); }
    @Override public Set<String> allowedStructuralKeys() { return KaishekProfile.DEFAULT_STRUCTURAL_KEYS; }
    @Override public Map<String, OpcodeSpec> opcodes() { return SCHEMA; }

    public BuildFingerprint fingerprint() { return FINGERPRINT; }
    public OpcodeRegistry opcodeRegistry() { return REGISTRY; }
    public Set<String> certifiedSemantics() { return CERTIFIED; }
    public Map<ScopeType, Set<ScopeType>> scopeLinks() { return SCOPE_LINKS; }

    public GameProfile gameProfile() {
        return new GameProfile(ID, GAME_VERSION, FINGERPRINT, REGISTRY, CERTIFIED, SCOPE_LINKS);
    }

    private static OpcodeDescriptor descriptor(String id, List<String> parameters) {
        return new OpcodeDescriptor(id, GAME_VERSION, OpcodeKind.EFFECT, InputType.BLOCK,
                ScopeType.CHARACTER, parameters, RandomnessClass.DETERMINISTIC,
                true, true, true);
    }

    private static Map<String, OpcodeSpec> schema() {
        Map<String, OpcodeSpec> result = new LinkedHashMap<>();
        result.put(OPEN_CASE, new OpcodeSpec(OPEN_CASE, OpcodeSpec.Kind.EFFECT,
                1, 1, Set.of("CHARACTER", "character"), GAME_VERSION, Set.of("case_id")));
        result.put(CHOOSE, new OpcodeSpec(CHOOSE, OpcodeSpec.Kind.EFFECT,
                1, 1, Set.of("CHARACTER", "character"), GAME_VERSION, Set.of("choice")));
        result.put(CLOSE_CASE, new OpcodeSpec(CLOSE_CASE, OpcodeSpec.Kind.EFFECT,
                0, 0, Set.of("CHARACTER", "character"), GAME_VERSION, Set.of()));
        return Collections.unmodifiableMap(result);
    }

    private static Map<ScopeType, Set<ScopeType>> identityLinks() {
        EnumMap<ScopeType, Set<ScopeType>> result = new EnumMap<>(ScopeType.class);
        for (ScopeType type : ScopeType.values()) result.put(type, Set.of(type));
        return Collections.unmodifiableMap(result);
    }
}
