package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Exact measured corpus inputs. This manifest confers no Game or fresh Native qualification. */
public final class Person10NativeCorpus {
    public static final String SCHEMA = "xar.person10-native-corpus/v1";
    public static final int MANIFEST_MAX_BYTES = 1 << 20;
    public static final int MAX_FILES = 256;
    public static final long FILE_MAX_BYTES = 1L << 20, TOTAL_MAX_BYTES = 16L << 20;
    private Person10NativeCorpus() { }

    public record Manifest(String schema, String machineId, String observedAtUtc, String corpusRoot,
            List<ControlBuild.FileRef> files) {
        public Manifest {
            if (!SCHEMA.equals(schema) || machineId == null || machineId.isBlank() || machineId.length() > 256)
                throw new IllegalArgumentException("Exact corpus schema and measurement machine required");
            Instant.parse(observedAtUtc); Path root = absolute(corpusRoot); files = List.copyOf(files);
            if (files.isEmpty() || files.size() > MAX_FILES) throw new IllegalArgumentException("Bounded nonempty original corpus required");
            Set<Path> paths = new HashSet<>(); long total = 0;
            for (ControlBuild.FileRef file : files) {
                Path path = absolute(file.path());
                if (!path.startsWith(root) || path.equals(root) || !path.getFileName().toString().endsWith(".json")
                        || !paths.add(path) || file.bytes() < 1 || file.bytes() > FILE_MAX_BYTES)
                    throw new IllegalArgumentException("Distinct bounded actual JSON corpus children required");
                total = Math.addExact(total, file.bytes());
            }
            if (total > TOTAL_MAX_BYTES || !files.equals(files.stream().sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList()))
                throw new IllegalArgumentException("Finite ordered complete corpus required");
        }
    }

    /** Root calls this only after its actual Native producers, in its admitted new metadata root. */
    public static ControlBuild.FileRef produce(Path corpus, Path output) throws IOException {
        Path root = absolute(corpus.toString()), target = absolute(output.toString());
        if (target.startsWith(root)) throw new IOException("Corpus manifest must remain outside its measured input directory");
        SharedSourceFiles.plainAncestors(target);
        Manifest manifest = new Manifest(SCHEMA, WindowsJobProcess.currentMachineId(), Instant.now().toString(),
                root.toString(), measure(root));
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(manifest);
        if (bytes.length > MANIFEST_MAX_BYTES || !manifest.equals(ControlBuild.strictMapper().readValue(bytes, Manifest.class)))
            throw new IOException("Finite corpus manifest strict roundtrip required");
        Files.write(target, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        ControlBuild.FileRef result = ControlBuild.FileRef.measure(target); result.verify();
        require(result, manifest.corpusRoot()); return result;
    }

    /** Live consumer rechecks every original, then rejects newly added or omitted JSON files too. */
    public static Manifest require(ControlBuild.FileRef source, String root) throws IOException {
        if (source.bytes() < 1 || source.bytes() > MANIFEST_MAX_BYTES) throw new IOException("Bounded corpus manifest required");
        plainFile(absolute(source.path())); source.verify();
        byte[] raw = Files.readAllBytes(Path.of(source.path()));
        var node = ControlBuild.strictMapper().readTree(raw);
        if (node == null || !node.isObject() || node.size() != 5 || !node.path("schema").isTextual()
                || !node.path("machine_id").isTextual() || !node.path("observed_at_utc").isTextual()
                || !node.path("corpus_root").isTextual() || !node.path("files").isArray())
            throw new IOException("Exact corpus JSON field types required");
        for (var file : node.path("files")) {
            if (!file.isObject() || file.size() != 3 || !file.path("path").isTextual()
                    || !file.path("bytes").isIntegralNumber() || !file.path("bytes").canConvertToLong()
                    || !file.path("sha256").isTextual()) throw new IOException("Exact original FileRef JSON types required");
        }
        Manifest manifest = ControlBuild.strictMapper().readValue(raw, Manifest.class);
        if (!manifest.corpusRoot().equals(absolute(root).toString())) throw new IOException("Corpus root and pinned manifest differ");
        for (ControlBuild.FileRef file : manifest.files()) { plainFile(absolute(file.path())); file.verify(); }
        if (!manifest.files().equals(measure(absolute(root)))) throw new IOException("Actual complete corpus differs from the pinned original file list");
        source.verify(); return manifest;
    }

    private static List<ControlBuild.FileRef> measure(Path root) throws IOException {
        SharedSourceFiles.plainAncestors(root);
        if (!Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS) || !root.toRealPath().equals(root))
            throw new IOException("Plain actual Native corpus directory required");
        List<ControlBuild.FileRef> result = new ArrayList<>(); int entries = 0; long total = 0;
        try (var walk = Files.walk(root)) {
            var paths = walk.iterator();
            while (paths.hasNext()) {
                Path path = paths.next();
                if (++entries > 1024 || Files.isSymbolicLink(path) || !path.toRealPath().equals(path))
                    throw new IOException("Corpus entry limit or plain path violated");
                if (Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)) continue;
                plainFile(path);
                if (!path.getFileName().toString().endsWith(".json")) continue;
                ControlBuild.FileRef file = ControlBuild.FileRef.measure(path);
                total = Math.addExact(total, file.bytes());
                if (file.bytes() < 1 || file.bytes() > FILE_MAX_BYTES || result.size() >= MAX_FILES || total > TOTAL_MAX_BYTES)
                    throw new IOException("Actual corpus exceeds finite source input bounds");
                result.add(file);
            }
        }
        if (result.isEmpty()) throw new IOException("NOT EXECUTED: original Native corpus is empty");
        result.sort(Comparator.comparing(ControlBuild.FileRef::path)); return List.copyOf(result);
    }
    private static void plainFile(Path path) throws IOException {
        SharedSourceFiles.plainAncestors(path);
        if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || !path.toRealPath().equals(path))
            throw new IOException("Plain original corpus file required");
    }
    private static Path absolute(String value) {
        if (value == null || value.isBlank() || value.length() > 4096
                || value.codePoints().anyMatch(point -> point < 32 || point == 127))
            throw new IllegalArgumentException("Bounded absolute corpus path required");
        Path path = Path.of(value);
        if (!path.isAbsolute() || !path.equals(path.normalize())) throw new IllegalArgumentException("Canonical absolute corpus path required");
        return path;
    }
}
