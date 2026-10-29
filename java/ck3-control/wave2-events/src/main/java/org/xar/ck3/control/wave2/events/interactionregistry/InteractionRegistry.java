package org.xar.ck3.control.wave2.events.interactionregistry;

import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Immutable source knowledge, distinct from native choice execution or material effects. */
public final class InteractionRegistry {
    public static final String ENTRY_SCHEMA = "xar.interaction-offline-reviewed-entry/v1";
    public static final String FACTS_SCHEMA = "xar.interaction-offline-source-facts/v1";
    public static final String CLASSIFICATION = "offline-source-reviewed-user-left-policy";
    private InteractionRegistry() { }

    public record BuildIdentity(String version, String exeSha256) {
        public BuildIdentity {
            StrictJson.require(version != null && version.matches("[0-9]+(?:\\.[0-9]+){2,3}"), "numeric exact CK3 build version required"); sha(exeSha256);
        }
    }
    public record Definition(String canonicalKey, long deterministicKeyHash) {
        public Definition {
            StrictJson.require(canonicalKey != null && canonicalKey.matches("[A-Za-z0-9_]{1,1024}"), "canonical interaction key required");
            StrictJson.require(deterministicKeyHash >= 0 && deterministicKeyHash <= 0xffff_ffffL, "uint32 deterministic hash required");
        }
    }
    public record Lookup(BuildIdentity build, Definition definition, String guiSha256) {
        public Lookup { Objects.requireNonNull(build); Objects.requireNonNull(definition); sha(guiSha256); }
    }
    public record Binding(BuildIdentity build, Definition definition, String sourceSha256, String guiSha256) {
        public Binding { Objects.requireNonNull(build); Objects.requireNonNull(definition); sha(sourceSha256); sha(guiSha256); }
    }
    public record SourcePaths(String sourcePath, String guiPath) {
        public SourcePaths { stable(sourcePath); stable(guiPath); }
    }
    public record SourceRef(String path, String sha256) {
        public SourceRef { stable(path); sha(sha256); }
    }
    public record Entry(String fingerprint, Binding binding, String classification, String preferredAction,
            SourcePaths paths, SourceRef sourceFacts, String reason) {
        public Entry {
            lowerSha(fingerprint); Objects.requireNonNull(binding); Objects.requireNonNull(paths); Objects.requireNonNull(sourceFacts); stable(reason);
            StrictJson.require(CLASSIFICATION.equals(classification) && "reject".equals(preferredAction), "catalogue grants only the authored-left policy");
        }
    }
    public record Facts(String fingerprint, Binding binding, SourcePaths paths, String sourceRelative,
            List<String> category, String definition, String onAccept, String onDecline, String analysis) {
        public Facts {
            lowerSha(fingerprint); Objects.requireNonNull(binding); Objects.requireNonNull(paths); stable(sourceRelative);
            category = List.copyOf(category); StrictJson.require(category.size() <= 64, "bounded category list required"); category.forEach(InteractionRegistry::stable);
            body(definition); if (onAccept != null) { body(onAccept); } if (onDecline != null) { body(onDecline); } body(analysis);
        }
    }
    public record Roots(Path stateRoot, Path gameRoot) {
        public Roots { Objects.requireNonNull(stateRoot); Objects.requireNonNull(gameRoot); StrictJson.require(stateRoot.isAbsolute() && gameRoot.isAbsolute(), "explicit absolute roots required"); }
    }
    public record Audit(String machineId, String observedAtUtc, String fingerprint, String entryPath, String entrySha256, String sourceSha256, String guiSha256) {
        public Audit { stable(machineId); StrictJson.utc(observedAtUtc); lowerSha(fingerprint); stable(entryPath); lowerSha(entrySha256); sha(sourceSha256); sha(guiSha256); }
        public boolean materialEffectsVerified() { return false; }
    }

    /** Only this package's source reader can construct verified knowledge. No JSON reviewed=true constructor exists. */
    public static final class VerifiedReview {
        private final Entry entry;
        private final Facts facts;
        private final Audit audit;
        VerifiedReview(Entry entry, Facts facts, Audit audit) {
            this.entry = Objects.requireNonNull(entry); this.facts = Objects.requireNonNull(facts); this.audit = Objects.requireNonNull(audit);
        }
        public Entry entry() { return entry; }
        public Facts facts() { return facts; }
        public Audit audit() { return audit; }
        public boolean materialEffectsVerified() { return false; }
        public boolean nativeAiEquivalent() { return false; }
        public boolean replayAllowed() { return false; }
    }
    public sealed interface Result permits Known, Unknown { }
    public record Known(VerifiedReview review) implements Result { public Known { Objects.requireNonNull(review); } }
    public enum UnknownReason { NO_MATCH, REJECTED_ENTRY, REGISTRY_UNAVAILABLE, RESOURCE_LIMIT }
    public enum Rejection { INVALID_CONTRACT, LOOKUP_BINDING_MISMATCH, FINGERPRINT_MISMATCH, SOURCE_MISMATCH, FILE_UNAVAILABLE, FILE_CHANGED, PATH_OUTSIDE_ROOT }
    public record RejectedEntry(String name, Rejection reason) {
        public RejectedEntry { stable(name); Objects.requireNonNull(reason); }
    }
    public record Unknown(UnknownReason reason, List<RejectedEntry> rejectedEntries) implements Result {
        public Unknown { Objects.requireNonNull(reason); rejectedEntries = List.copyOf(rejectedEntries); StrictJson.require(rejectedEntries.size() <= 8, "at most eight rejection details"); }
    }
    static void sha(String value) { StrictJson.require(value != null && value.matches("[0-9a-fA-F]{64}"), "SHA-256 required"); }
    static void lowerSha(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "lowercase canonical SHA-256 required"); }
    static void stable(String value) { StrictJson.text(value); StrictJson.require(value.length() <= 4096 && value.chars().noneMatch(c -> c < 0x20), "bounded stable text required"); }
    static void body(String value) {
        StrictJson.require(value != null && !value.isEmpty() && value.length() <= 524_288, "bounded source body required");
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) {
                StrictJson.require(index + 1 < value.length() && Character.isLowSurrogate(value.charAt(index + 1)), "unpaired source surrogate"); index++;
            } else { StrictJson.require(!Character.isLowSurrogate(current), "unpaired source surrogate"); }
        }
    }
}
