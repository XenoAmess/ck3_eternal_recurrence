package org.xar.ck3.dynastic.release;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/** Exact runtime projection with new-attempt outputs and readback through the real manifest consumer. */
public final class ReleaseBuilder {
    private static final LocalDateTime ZIP_TIME = LocalDateTime.of(1980, 1, 1, 0, 0);

    public record BuildResult(Path staging, Path manifest, Path archive, ReleaseManifest payload) { }
    public record Verification(int verifiedFiles, String modVersion, String gitSha) { }
    public record CheckResult(int fileCount, String manifestSha256, String zipSha256) { }

    public BuildResult build(ReleaseProduct product, Path repository, Path output, String revision, String gitTag, String workshopItemId) throws IOException {
        StaticValidation.ValidationReport validation = StaticValidation.validate(product, repository);
        if (revision == null || !ReleaseProduct.REVISION.matcher(revision).matches()) throw new IllegalArgumentException("revision must be a full lowercase Git SHA");
        if (gitTag != null && !gitTag.equals(product.tagPrefix() + validation.modVersion())) throw new IllegalArgumentException("Git tag does not match product version");
        ReleaseProduct.workshopItemId(workshopItemId);
        Path staging = output.toAbsolutePath().normalize();
        if (staging.startsWith(product.source()) || product.source().startsWith(staging)) throw new IllegalArgumentException("source and staging cannot contain each other");
        Path manifest = sibling(staging, ".manifest.json");
        Path archive = sibling(staging, ".zip");
        for (Path target : List.of(staging, manifest, archive)) {
            if (Files.exists(target)) throw new IllegalArgumentException("output already exists; use a new attempt: " + target);
        }
        Files.createDirectories(staging.getParent());
        Files.createDirectory(staging);
        List<ReleaseManifest.FileEntry> entries = new ArrayList<>();
        for (String relative : product.runtimeFiles()) {
            byte[] data = Files.readAllBytes(product.source().resolve(relative));
            if (relative.equals("descriptor.mod")) data = CompatibilityTags.render(data, repository);
            StaticValidation.validateBytes(relative, data);
            Path target = staging.resolve(relative);
            Files.createDirectories(target.getParent());
            Files.write(target, data, StandardOpenOption.CREATE_NEW);
            entries.add(new ReleaseManifest.FileEntry(relative, data.length, sha256(data)));
        }
        String stagedVersion = StaticValidation.descriptorVersion(Files.readString(staging.resolve("descriptor.mod"), StandardCharsets.UTF_8));
        if (!stagedVersion.equals(validation.modVersion())) throw new IllegalArgumentException("descriptor version changed during build");
        ReleaseManifest payload = new ReleaseManifest(1, product.productId(), stagedVersion, gitTag, revision, workshopItemId, entries);
        Files.write(manifest, ManifestJson.encode(payload), StandardOpenOption.CREATE_NEW);
        try (OutputStream stream = Files.newOutputStream(archive, StandardOpenOption.CREATE_NEW);
                ZipOutputStream zip = new ZipOutputStream(stream, StandardCharsets.UTF_8)) {
            zip.setLevel(9);
            for (ReleaseManifest.FileEntry entry : entries) {
                ZipEntry member = new ZipEntry(product.productId() + "/" + entry.path());
                member.setTimeLocal(ZIP_TIME);
                zip.putNextEntry(member);
                zip.write(Files.readAllBytes(staging.resolve(entry.path())));
                zip.closeEntry();
            }
        }
        verify(product, staging, manifest);
        return new BuildResult(staging, manifest, archive, payload);
    }

    public Verification verify(ReleaseProduct product, Path staging, Path manifestPath) throws IOException {
        ReleaseManifest manifest = ManifestJson.decode(Files.readAllBytes(manifestPath), product);
        Map<String, Path> files = StaticValidation.inventory(staging, false);
        if (!files.keySet().equals(Set.copyOf(product.runtimeFiles()))) throw new IllegalArgumentException("staging runtime inventory differs from allowlist");
        for (ReleaseManifest.FileEntry entry : manifest.files()) {
            byte[] data = Files.readAllBytes(files.get(entry.path()));
            if (data.length != entry.size() || !sha256(data).equals(entry.sha256())) throw new IllegalArgumentException("staging file mismatch: " + entry.path());
            StaticValidation.validateBytes(entry.path(), data);
        }
        StaticValidation.validateLocalization(product, staging);
        String version = StaticValidation.descriptorVersion(Files.readString(staging.resolve("descriptor.mod"), StandardCharsets.UTF_8));
        if (!version.equals(manifest.modVersion())) throw new IllegalArgumentException("manifest and descriptor versions differ");
        return new Verification(files.size(), version, manifest.gitSha());
    }

    /** Keeps both new builds available for review; no recursive cleanup or overwrite. */
    public CheckResult check(ReleaseProduct product, Path repository, Path output, String revision, String workshopItemId) throws IOException {
        Path root = output.toAbsolutePath().normalize();
        if (Files.exists(root)) throw new IllegalArgumentException("check output already exists; use a new attempt: " + root);
        BuildResult first = build(product, repository, root.resolve("one"), revision, null, workshopItemId);
        BuildResult second = build(product, repository, root.resolve("two"), revision, null, workshopItemId);
        byte[] firstManifest = Files.readAllBytes(first.manifest());
        byte[] firstZip = Files.readAllBytes(first.archive());
        if (!MessageDigest.isEqual(firstManifest, Files.readAllBytes(second.manifest()))
                || !MessageDigest.isEqual(firstZip, Files.readAllBytes(second.archive()))) {
            throw new IllegalArgumentException("manifest or ZIP is not byte reproducible");
        }
        return new CheckResult(first.payload().files().size(), sha256(firstManifest), sha256(firstZip));
    }

    public static String sha256(byte[] data) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("JVM lacks SHA-256", error);
        }
    }

    private static Path sibling(Path staging, String suffix) {
        return staging.resolveSibling(staging.getFileName() + suffix);
    }
}
