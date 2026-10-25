package org.xar.ck3.rrf;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Set;

/** Versioned, immutable JSON contracts shared by the real producer and consumers. */
public final class Contracts {
    private Contracts() { }
    public enum Kind { TENET, DOCTRINE }
    public enum ProvenanceKind { OBSERVED_MACHINE, SYNTHETIC_FIXTURE }
    public record Provenance(ProvenanceKind kind, String machineId, String observedAt) {
        public Provenance { if (kind == null || machineId == null || machineId.isBlank()) throw new IllegalArgumentException("explicit machine provenance required"); java.time.Instant.parse(observedAt); }
    }
    public record SourceFile(String path, String sha256) {
        public SourceFile { safePath(path); digest(sha256); }
    }
    public record Group(String id, String category, String lock, String availableOnCreate) {
        public Group { identifier(id); identifier(category); if (!Set.of("none", "rite", "faith", "religion").contains(lock)) throw new IllegalArgumentException("invalid lock"); Clausewitz.parse(availableOnCreate); }
    }
    public record Definition(Kind kind, String id, String group, String sourcePath, String shown, String canPick,
                             String requiresDlc, boolean visible, List<String> blockedReasons) {
        public Definition {
            if (kind == null) throw new IllegalArgumentException("missing kind");
            identifier(id); if (kind == Kind.DOCTRINE) identifier(group); else if (!group.isEmpty()) throw new IllegalArgumentException("tenet group");
            safePath(sourcePath); Clausewitz.parse(shown); Clausewitz.parse(canPick);
            if (!requiresDlc.isEmpty()) identifier(requiresDlc);
            blockedReasons = List.copyOf(blockedReasons);
        }
    }
    public record Catalog(int schemaVersion, String machineId, String observedAt, List<SourceFile> sources, List<Group> groups, List<Definition> definitions) {
        public Catalog {
            schema(schemaVersion); if (machineId == null || machineId.isBlank()) throw new IllegalArgumentException("machineId required");
            java.time.Instant.parse(observedAt); sources = List.copyOf(sources); groups = List.copyOf(groups); definitions = List.copyOf(definitions);
            unique(sources.stream().map(SourceFile::path).toList()); unique(groups.stream().map(Group::id).toList()); unique(definitions.stream().map(Definition::id).toList());
            Set<String> groupIds = Set.copyOf(groups.stream().map(Group::id).toList()); Set<String> sourcePaths = Set.copyOf(sources.stream().map(SourceFile::path).toList());
            for (Definition d : definitions) if (!sourcePaths.contains(d.sourcePath()) || (d.kind() == Kind.DOCTRINE && !groupIds.contains(d.group()))) throw new IllegalArgumentException("unbound definition: " + d.id());
            if (definitions.isEmpty() || sources.isEmpty()) throw new IllegalArgumentException("empty catalog");
        }
    }
    public record Product(int schemaVersion, String productId, String version, List<String> runtimeFiles) {
        public Product {
            schema(schemaVersion); identifier(productId); releaseVersion(version);
            runtimeFiles = List.copyOf(runtimeFiles); runtimeFiles.forEach(Contracts::safeRuntimePath); unique(runtimeFiles);
            if (!runtimeFiles.contains("descriptor.mod")) throw new IllegalArgumentException("descriptor missing from product");
        }
    }
    public record GeneratedFiles(int schemaVersion, String catalogSha256, List<String> runtimeFiles) {
        public GeneratedFiles { schema(schemaVersion); digest(catalogSha256); runtimeFiles = List.copyOf(runtimeFiles); unique(runtimeFiles); runtimeFiles.forEach(Contracts::safeRuntimePath); }
    }
    public record FileEntry(String path, long size, String sha256) {
        public FileEntry { safeRuntimePath(path); if (size < 0) throw new IllegalArgumentException("negative size"); digest(sha256); }
    }
    public record ReleaseIdentity(String workshopItemId, String gitTag, String gitSha) {
        public ReleaseIdentity {
            if (workshopItemId == null || !workshopItemId.matches("[1-9][0-9]*")) throw new IllegalArgumentException("canonical Workshop item string required");
            if (gitTag == null || !gitTag.matches("[A-Za-z0-9][A-Za-z0-9._-]*") || gitTag.contains("..") || gitTag.endsWith(".") || gitTag.endsWith(".lock")) throw new IllegalArgumentException("explicit release tag token required");
            if (gitSha == null || !gitSha.matches("[a-f0-9]{40}")) throw new IllegalArgumentException("full revision required");
        }
    }
    /** Canonical shared Workshop cache format; unrelated generated/fixture schemas remain separate. */
    public record Manifest(@JsonProperty("format_version") int formatVersion,
                           @JsonProperty("workshop_item_id") String workshopItemId,
                           @JsonProperty("git_tag") String gitTag, @JsonProperty("git_sha") String gitSha,
                           @JsonProperty("product_id") String productId, String version,
                           Provenance provenance, List<FileEntry> files) {
        public Manifest {
            if (formatVersion != 2) throw new IllegalArgumentException("unsupported formal format_version");
            new ReleaseIdentity(workshopItemId, gitTag, gitSha); identifier(productId); releaseVersion(version);
            if (provenance == null) throw new IllegalArgumentException("provenance required");
            files = List.copyOf(files); unique(files.stream().map(FileEntry::path).toList());
            if (files.stream().noneMatch(entry -> entry.path().equals("descriptor.mod"))) throw new IllegalArgumentException("formal descriptor missing");
        }
    }
    public static void schema(int version) { if (version != 1) throw new IllegalArgumentException("unsupported schemaVersion"); }
    public static void releaseVersion(String value) {
        if (value == null || !value.matches("[0-9]+\\.[0-9]+\\.[0-9]+(?:-[a-z0-9]+(?:\\.[a-z0-9]+)*)?")) throw new IllegalArgumentException("invalid release version token");
    }
    public static void identifier(String value) { if (value == null || !value.matches("[A-Za-z_][A-Za-z_0-9]*")) throw new IllegalArgumentException("invalid identifier: " + value); }
    public static void digest(String value) { if (value == null || !value.matches("[a-f0-9]{64}")) throw new IllegalArgumentException("invalid SHA-256"); }
    public static void unique(List<String> values) { if (Set.copyOf(values).size() != values.size()) throw new IllegalArgumentException("duplicate entries"); }
    public static void safePath(String path) {
        if (path == null || path.isEmpty() || path.startsWith("/") || path.contains("\\") || path.contains(":") || List.of(path.split("/", -1)).stream().anyMatch(p -> p.isEmpty() || p.equals(".") || p.equals(".."))) throw new IllegalArgumentException("unsafe relative path: " + path);
    }
    public static void safeRuntimePath(String path) {
        safePath(path);
        if (!(path.equals("descriptor.mod") || path.equals("thumbnail.png") || path.startsWith("common/") || path.startsWith("gui/") || path.startsWith("localization/") || path.startsWith("gfx/"))) throw new IllegalArgumentException("non-runtime path: " + path);
        if (path.contains("fixture") || path.contains("acceptance")) throw new IllegalArgumentException("fixture in runtime");
    }
}
