package org.xar.ck3.markets.build;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;

/** Produces a fresh allowlisted candidate, never overwrites a live mod or claims release acceptance. */
public final class SnapshotBuilder {
    public record FilePin(String path, long bytes, String sha256) { }
    public record Result(String schema, String sourceRevision, String qualification, List<FilePin> files) { }
    private SnapshotBuilder() { }

    public static Result build(Path source, Path output, String revision) throws IOException {
        ContentValidator.require(revision.matches("[0-9a-f]{40}"), "revision must be a full lowercase Git SHA");
        Path root = source.toRealPath();
        Path destination = output.toAbsolutePath().normalize();
        ContentValidator.require(!destination.startsWith(root) && !root.startsWith(destination), "output overlaps source");
        ContentValidator.require(!Files.exists(destination), "output must be new: " + destination);
        Path ancestor = destination.getParent();
        while (ancestor != null && !Files.exists(ancestor)) ancestor = ancestor.getParent();
        ContentValidator.require(ancestor != null, "no existing output ancestor");
        ContentValidator.require(!ancestor.toRealPath().resolve(ancestor.relativize(destination)).normalize().startsWith(root), "output link overlaps source");
        var validation = ContentValidator.validate(root);
        List<FilePin> pins = new ArrayList<>();
        // Cache all validated source bytes before creating output. A rejected input leaves no output.
        List<byte[]> content = new ArrayList<>();
        for (String name : validation.runtimeFiles()) content.add(Files.readAllBytes(ContentValidator.safeFile(root, name)));
        Files.createDirectories(destination.resolve("content"));
        for (int i = 0; i < validation.runtimeFiles().size(); i++) {
            String name = validation.runtimeFiles().get(i);
            byte[] bytes = content.get(i);
            Path target = destination.resolve("content").resolve(name);
            Files.createDirectories(target.getParent());
            Files.write(target, bytes);
            pins.add(new FilePin(name, bytes.length, hash(bytes)));
        }
        Result result = new Result("xfm.candidate-build.v1", revision, "CANDIDATE_STATIC_ONLY_NO_ENGINE_OR_RELEASE_CREDIT", List.copyOf(pins));
        new ObjectMapper().writerWithDefaultPrettyPrinter().writeValue(destination.resolve("manifest.json").toFile(), result);
        return result;
    }

    private static String hash(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
