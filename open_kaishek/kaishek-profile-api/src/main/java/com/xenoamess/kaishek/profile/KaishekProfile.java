package com.xenoamess.kaishek.profile;

import java.util.*;

/**
 * Schema-facing profile contract consumed by the syntax validator.
 *
 * <p>The low-level {@link GameProfile} contract describes an exact build and
 * typed opcode registry.  This view additionally exposes the source-directory
 * classification and the small parameter shape used by the static validator.
 * Keeping the contract in the profile API lets concrete game profiles live in
 * their own modules without making the validator depend on one particular
 * game.</p>
 */
public interface KaishekProfile {
    /** Conservative structural words shared by the generic adapter. */
    Set<String> DEFAULT_STRUCTURAL_KEYS = Set.of(
            "limit", "trigger", "effect", "value", "if", "else", "else_if", "while",
            "ordered", "random", "weight", "modifier", "scope", "save_scope_as",
            "save_temporary_scope_as", "use_saved_scope_as", "from", "to", "title", "name",
            "id", "type", "text", "icon", "desc", "potential", "allow", "ai_will_do",
            "on_action", "first_valid", "fallback", "check", "compare", "localization",
            "parameter", "flag", "amount", "days", "target", "event", "yes", "no");

    String id();
    String gameVersion();
    String executableSha256();
    ScriptDomain domainForPath(String sourcePath);
    OpcodeSpec opcode(String name);
    Set<String> allowedStructuralKeys();
    Map<String, OpcodeSpec> opcodes();

    /**
     * Adapt the framework-neutral profile contract for validator consumers.
     * The adapter has no dependency on a concrete game profile; directory
     * classification is the conservative common Paradox layout and concrete
     * profiles can provide a richer implementation directly.
     */
    static KaishekProfile fromGameProfile(GameProfile profile) {
        Objects.requireNonNull(profile, "profile");
        Map<String, OpcodeSpec> specs = new TreeMap<>();
        for (OpcodeDescriptor descriptor : profile.opcodes().all()) {
            OpcodeSpec.Kind kind = switch (descriptor.kind()) {
                case TRIGGER -> OpcodeSpec.Kind.TRIGGER;
                case EFFECT -> OpcodeSpec.Kind.EFFECT;
                case SCRIPT_VALUE -> OpcodeSpec.Kind.VALUE;
                // CK3 dispatches `trigger_event` as an effect statement.  The
                // generic schema vocabulary has no separate EVENT domain, so
                // retain the effect classification through this adapter.
                case EVENT -> OpcodeSpec.Kind.EFFECT;
                // GUI opcodes are interface-facing operations (for example
                // `GetPlayer`), not executable structural control words.  Keep
                // that distinction in the generic projection so validators
                // do not recurse into their arguments as script blocks.
                case GUI -> OpcodeSpec.Kind.INTERFACE;
                case DECISION, INTERACTION, SCRIPTED_CALL -> OpcodeSpec.Kind.STRUCTURAL;
            };
            Set<String> scopes = Set.of(
                    descriptor.requiredScope().name(),
                    descriptor.requiredScope().name().toLowerCase(Locale.ROOT));
            specs.put(descriptor.id(), new OpcodeSpec(descriptor.id(), kind,
                    descriptor.minParameters(), descriptor.maxParameters(),
                    scopes, descriptor.profileVersion(), Set.copyOf(descriptor.parameterNames())));
        }
        Map<String, OpcodeSpec> immutableSpecs = Collections.unmodifiableMap(specs);
        return new KaishekProfile() {
            @Override public String id() { return profile.id(); }
            @Override public String gameVersion() { return profile.gameVersion(); }
            @Override public String executableSha256() { return profile.fingerprint().exeSha256(); }
            @Override public ScriptDomain domainForPath(String sourcePath) { return ScriptDomain.fromPath(sourcePath); }
            @Override public OpcodeSpec opcode(String name) { return name == null ? null : immutableSpecs.get(name); }
            @Override public Set<String> allowedStructuralKeys() { return DEFAULT_STRUCTURAL_KEYS; }
            @Override public Map<String, OpcodeSpec> opcodes() { return immutableSpecs; }
        };
    }
}
