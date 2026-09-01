package com.xenoamess.kaishek.profile;

import java.util.*;

/**
 * Concrete, version-pinned CK3 profile for executable build 1.19.0.6.
 *
 * <p>The schema view implemented by {@link KaishekProfile} is used by the
 * static validator.  {@link #gameProfile()} exposes the framework-neutral
 * profile contract used by IR/differential tooling.  The opcode table is a
 * deliberately small Phase 0 baseline: entries describe syntax and shape, but
 * are not runtime-certified until an exact-build differential artifact exists.
 * Unknown semantics therefore remain fail-closed.</p>
 */
public final class Ck3Profile11906 implements KaishekProfile {
    public static final String ID = "ck3-1.19.0.6";
    public static final String GAME_ID = "ck3";
    public static final String GAME_VERSION = "1.19.0.6";
    public static final String EXE_SHA256 =
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

    private static final Set<String> STRUCTURAL = KaishekProfile.DEFAULT_STRUCTURAL_KEYS;

    private static final BuildFingerprint FINGERPRINT = new BuildFingerprint(
            GAME_ID, GAME_VERSION, EXE_SHA256, List.of(), null, null);

    /*
     * These are syntax-level descriptors only.  None is marked certified:
     * certification belongs to exact-build differential evidence, not to an
     * allow-list entry inferred from source text.
     */
    private static final List<OpcodeDescriptor> DESCRIPTORS = List.of(
            descriptor("always", OpcodeKind.TRIGGER, InputType.BOOLEAN, ScopeType.THIS,
                    List.of(), RandomnessClass.DETERMINISTIC, false, true),
            descriptor("is_ai", OpcodeKind.TRIGGER, InputType.BOOLEAN, ScopeType.THIS,
                    List.of("value"), RandomnessClass.DETERMINISTIC, false, true),
            descriptor("has_character_flag", OpcodeKind.TRIGGER, InputType.BOOLEAN, ScopeType.CHARACTER,
                    List.of("flag"), RandomnessClass.DETERMINISTIC, false, true),
            descriptor("has_trait", OpcodeKind.TRIGGER, InputType.BOOLEAN, ScopeType.CHARACTER,
                    List.of("trait"), RandomnessClass.DETERMINISTIC, false, true),
            descriptor("has_title", OpcodeKind.TRIGGER, InputType.BOOLEAN, ScopeType.CHARACTER,
                    List.of("title"), RandomnessClass.DETERMINISTIC, false, true),
            descriptor("is_alive", OpcodeKind.TRIGGER, InputType.BOOLEAN, ScopeType.THIS,
                    List.of(), RandomnessClass.DETERMINISTIC, false, true),
            descriptor("check_variable", OpcodeKind.TRIGGER, InputType.BOOLEAN, ScopeType.THIS,
                    List.of("name", "value"), 1, 2, RandomnessClass.DETERMINISTIC, false, true),
            // CK3 accepts duration modifiers in addition to name/value for
            // set_variable; keep the static shape broad until the exact-build
            // parameter contract is certified.
            descriptor("set_variable", OpcodeKind.EFFECT, InputType.BLOCK, ScopeType.THIS,
                    List.of("name", "value", "days", "weeks", "months", "years"),
                    1, Integer.MAX_VALUE, RandomnessClass.DETERMINISTIC, true, true),
            // change_variable uses arithmetic keys (add/subtract/etc.).  Keep
            // `value` as a compatibility spelling for expression forms until
            // the exact-build contract is narrowed by differential evidence.
            descriptor("change_variable", OpcodeKind.EFFECT, InputType.BLOCK, ScopeType.THIS,
                    List.of("name", "add", "subtract", "multiply", "divide", "min", "max", "value"),
                    1, Integer.MAX_VALUE, RandomnessClass.DETERMINISTIC, true, true),
            descriptor("remove_variable", OpcodeKind.EFFECT, InputType.BLOCK, ScopeType.THIS,
                    List.of("name"), RandomnessClass.DETERMINISTIC, true, true),
            descriptor("set_character_flag", OpcodeKind.EFFECT, InputType.BLOCK, ScopeType.CHARACTER,
                    List.of("flag"), RandomnessClass.DETERMINISTIC, true, true),
            descriptor("remove_character_flag", OpcodeKind.EFFECT, InputType.BLOCK, ScopeType.CHARACTER,
                    List.of("flag"), RandomnessClass.DETERMINISTIC, true, true),
            descriptor("trigger_event", OpcodeKind.EVENT, InputType.BLOCK, ScopeType.CHARACTER,
                    List.of("id", "on_action", "saved_event_id", "days", "weeks", "months",
                            "years", "delayed", "trigger_on_next_date"),
                    1, 2, RandomnessClass.DETERMINISTIC, true, true),
            // Resource effects accept scalar values and expression blocks
            // whose keys vary by caller (value/subtract/multiply/min/max...).
            // An empty name set deliberately leaves that polymorphic shape
            // unconstrained until exact-build schema evidence is recorded.
            descriptor("add_gold", OpcodeKind.EFFECT, InputType.ANY, ScopeType.CHARACTER,
                    List.of(), 0, Integer.MAX_VALUE, RandomnessClass.DETERMINISTIC, true, true),
            descriptor("add_prestige", OpcodeKind.EFFECT, InputType.ANY, ScopeType.CHARACTER,
                    List.of(), 0, Integer.MAX_VALUE, RandomnessClass.DETERMINISTIC, true, true),
            descriptor("add_piety", OpcodeKind.EFFECT, InputType.ANY, ScopeType.CHARACTER,
                    List.of(), 0, Integer.MAX_VALUE, RandomnessClass.DETERMINISTIC, true, true),
            // CK3's candidate materialisation order is not yet certified.
            descriptor("random", OpcodeKind.SCRIPTED_CALL, InputType.BLOCK, ScopeType.THIS,
                    List.of(), 0, Integer.MAX_VALUE, RandomnessClass.UNSUPPORTED, false, true),
            descriptor("script_value", OpcodeKind.SCRIPT_VALUE, InputType.VALUE, ScopeType.THIS,
                    List.of(), 0, Integer.MAX_VALUE, RandomnessClass.DETERMINISTIC, false, true),
            descriptor("GetPlayer", OpcodeKind.GUI, InputType.SCOPE, ScopeType.ROOT,
                    List.of(), RandomnessClass.DETERMINISTIC, false, true));

    private static final OpcodeRegistry OPCODE_REGISTRY = new OpcodeRegistry(DESCRIPTORS);
    private static final Map<String, OpcodeSpec> SCHEMA_OPCODES = schemaOpcodes();
    private static final Map<ScopeType, Set<ScopeType>> SCOPE_LINKS = identityScopeLinks();
    private static final Set<String> CERTIFIED_SEMANTICS = Set.of();

    public Ck3Profile11906() {
        // Keep an instance type for the validator-facing API.  All state is
        // immutable and shared safely between callers.
    }

    /** Exact build identity used by generic profile consumers. */
    public BuildFingerprint fingerprint() {
        return FINGERPRINT;
    }

    /** Immutable typed opcode registry used by IR and differential contracts. */
    public OpcodeRegistry opcodeRegistry() {
        return OPCODE_REGISTRY;
    }

    /** Framework-neutral profile projection for APIs that do not need schema domains. */
    public GameProfile gameProfile() {
        return new GameProfile(ID, GAME_VERSION, FINGERPRINT, OPCODE_REGISTRY,
                CERTIFIED_SEMANTICS, SCOPE_LINKS);
    }

    /** Alias for callers that use the shorter profile contract name. */
    public Profile profile() {
        return new Profile(ID, GAME_VERSION, FINGERPRINT, OPCODE_REGISTRY,
                CERTIFIED_SEMANTICS, SCOPE_LINKS);
    }

    public Set<String> certifiedSemantics() {
        return CERTIFIED_SEMANTICS;
    }

    public Map<ScopeType, Set<ScopeType>> scopeLinks() {
        return SCOPE_LINKS;
    }

    @Override
    public String id() {
        return ID;
    }

    @Override
    public String gameVersion() {
        return GAME_VERSION;
    }

    @Override
    public String executableSha256() {
        return EXE_SHA256;
    }

    @Override
    public Set<String> allowedStructuralKeys() {
        return STRUCTURAL;
    }

    @Override
    public Map<String, OpcodeSpec> opcodes() {
        return SCHEMA_OPCODES;
    }

    @Override
    public OpcodeSpec opcode(String name) {
        return name == null ? null : SCHEMA_OPCODES.get(name);
    }

    @Override
    public ScriptDomain domainForPath(String sourcePath) {
        return ScriptDomain.fromPath(sourcePath);
    }

    private static OpcodeDescriptor descriptor(String id, OpcodeKind kind, InputType input,
                                                ScopeType scope, List<String> parameters,
                                                RandomnessClass randomness, boolean writes,
                                                boolean reads) {
        return new OpcodeDescriptor(id, GAME_VERSION, kind, input, scope, parameters,
                randomness, writes, reads, false);
    }

    private static OpcodeDescriptor descriptor(String id, OpcodeKind kind, InputType input,
                                                ScopeType scope, List<String> parameters,
                                                int minParameters, int maxParameters,
                                                RandomnessClass randomness, boolean writes,
                                                boolean reads) {
        return new OpcodeDescriptor(id, GAME_VERSION, kind, input, scope, parameters,
                randomness, writes, reads, false, minParameters, maxParameters);
    }

    private static Map<String, OpcodeSpec> schemaOpcodes() {
        Map<String, OpcodeSpec> m = new LinkedHashMap<>();
        add(m, "always", OpcodeSpec.Kind.TRIGGER);
        add(m, "is_ai", OpcodeSpec.Kind.TRIGGER);
        add(m, "has_character_flag", OpcodeSpec.Kind.TRIGGER);
        add(m, "has_trait", OpcodeSpec.Kind.TRIGGER);
        add(m, "has_title", OpcodeSpec.Kind.TRIGGER);
        add(m, "is_alive", OpcodeSpec.Kind.TRIGGER);
        add(m, "check_variable", OpcodeSpec.Kind.TRIGGER);
        add(m, "set_variable", OpcodeSpec.Kind.EFFECT);
        add(m, "change_variable", OpcodeSpec.Kind.EFFECT);
        add(m, "remove_variable", OpcodeSpec.Kind.EFFECT);
        add(m, "set_character_flag", OpcodeSpec.Kind.EFFECT);
        add(m, "remove_character_flag", OpcodeSpec.Kind.EFFECT);
        add(m, "trigger_event", OpcodeSpec.Kind.EFFECT);
        add(m, "add_gold", OpcodeSpec.Kind.EFFECT);
        add(m, "add_prestige", OpcodeSpec.Kind.EFFECT);
        add(m, "add_piety", OpcodeSpec.Kind.EFFECT);
        add(m, "random", OpcodeSpec.Kind.STRUCTURAL);
        add(m, "script_value", OpcodeSpec.Kind.VALUE);
        add(m, "GetPlayer", OpcodeSpec.Kind.INTERFACE);
        return Collections.unmodifiableMap(m);
    }

    private static void add(Map<String, OpcodeSpec> m, String name, OpcodeSpec.Kind kind) {
        // Keep the validator-facing schema and the typed registry on the same
        // scope contract.  An empty scope set would silently disable the
        // INVALID_SCOPE diagnostic for every registered opcode.
        OpcodeDescriptor descriptor = OPCODE_REGISTRY.require(name);
        Set<String> scopes = Set.of(
                descriptor.requiredScope().name(),
                descriptor.requiredScope().name().toLowerCase(Locale.ROOT));
        Set<String> parameters = Set.copyOf(descriptor.parameterNames());
        m.put(name, new OpcodeSpec(name, kind, descriptor.minParameters(), descriptor.maxParameters(),
                scopes, GAME_VERSION, parameters));
    }

    private static Map<ScopeType, Set<ScopeType>> identityScopeLinks() {
        EnumMap<ScopeType, Set<ScopeType>> links = new EnumMap<>(ScopeType.class);
        for (ScopeType type : ScopeType.values()) links.put(type, Set.of(type));
        return Collections.unmodifiableMap(links);
    }
}
