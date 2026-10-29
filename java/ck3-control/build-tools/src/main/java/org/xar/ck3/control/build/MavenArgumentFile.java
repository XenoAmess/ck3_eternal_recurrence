package org.xar.ck3.control.build;

import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Default Maven's one-argument-per-line transport, derived only in the unfrozen compiler snapshot. */
public final class MavenArgumentFile {
    public static final String LEGACY_SCHEMA = "xar.maven-argument-file/v1";
    public static final String SCHEMA = "xar.maven-argument-file/v2";
    public static final String CONFIG = ".mvn/maven.config";
    public static final String MANIFEST = ".mvn/xar-control-arguments.json";
    public static final int MAXIMUM_BYTES = 1 << 20;
    public static final int CMD_LIMIT = 8191;
    private MavenArgumentFile() {}

    public record Manifest(String schema, String machineId, String observedUtc, String sourceRoot,
            String compiledRoot, FileRef sourceConfigRef, List<String> inheritedArguments,
            List<String> arguments, FileRef configRef) {
        public Manifest {
            if ((!SCHEMA.equals(schema) && !LEGACY_SCHEMA.equals(schema)) || machineId == null || machineId.isBlank() || observedUtc == null
                    || sourceRoot == null || compiledRoot == null || inheritedArguments == null
                    || arguments == null || configRef == null) throw new IllegalArgumentException("Complete Maven argument artifact required");
            Instant.parse(observedUtc);
            inheritedArguments = List.copyOf(inheritedArguments); arguments = List.copyOf(arguments);
        }
    }
    public record Inventories(List<FileRef> source, List<FileRef> compiled) {
        public Inventories { source = List.copyOf(source); compiled = List.copyOf(compiled); }
    }
    public static boolean required(Path override, List<String> arguments) {
        if (arguments.stream().anyMatch(value -> value.startsWith("-D" + ControlBuild.LobbyVerifyTestInputs.PATH_PROPERTY + "=")))
            return true; // Freeze the complete typed lobby argv even when the physical command is short.
        String batch = ControlBuild.mavenBatchText(override, arguments);
        return batch.lines().anyMatch(line -> line.length() > CMD_LIMIT);
    }
    public static List<String> inheritedArguments(Path root) throws IOException {
        return inheritedArguments(root, Files::newInputStream);
    }
    /** Package-local I/O boundary for deterministic file-replacement failure regressions. */
    @FunctionalInterface interface ArtifactOpener { InputStream open(Path path) throws IOException; }
    static List<String> inheritedArguments(Path root, ArtifactOpener opener) throws IOException {
        Path path = absolute(root).resolve(CONFIG);
        if (!Files.exists(path, LinkOption.NOFOLLOW_LINKS)) return List.of();
        byte[] bytes = read(path, opener); List<String> result = new ArrayList<>();
        for (String line : utf8(bytes).split("\r?\n", -1)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            argument(line);
            if (!line.matches("-D[A-Za-z0-9_.-]+=.*")) throw new IOException("Existing Maven config must contain unambiguous -Dname=value lines");
            result.add(line);
        }
        uniqueProperties(result); return List.copyOf(result);
    }
    public static void prepare(Path sourceRoot, Path compiledRoot, Path override, List<String> arguments) throws IOException {
        Path source = absolute(sourceRoot), compiled = absolute(compiledRoot);
        if (source.equals(compiled) || source.startsWith(compiled) || compiled.startsWith(source)) throw new IOException("Independent compiler snapshot required");
        if (Files.exists(source.resolve(MANIFEST), LinkOption.NOFOLLOW_LINKS)
                || Files.exists(compiled.resolve(MANIFEST), LinkOption.NOFOLLOW_LINKS)) throw new IOException("Reserved argument artifact already exists");
        List<String> inherited = inheritedArguments(source);
        if (!inherited.equals(inheritedArguments(compiled))) throw new IOException("Copied Maven config differs");
        List<String> combined = new ArrayList<>(inherited); combined.addAll(arguments);
        for (String value : combined) argument(value);
        uniqueProperties(combined);
        if (!required(override, arguments)) return;
        Path original = source.resolve(CONFIG), config = compiled.resolve(CONFIG);
        FileRef originalRef = Files.exists(original, LinkOption.NOFOLLOW_LINKS) ? FileRef.measure(original) : null;
        if (originalRef != null) {
            FileRef copied = FileRef.measure(config);
            if (originalRef.bytes() != copied.bytes() || !originalRef.sha256().equals(copied.sha256())) throw new IOException("Copied Maven config bytes differ");
        } else if (Files.exists(config, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Unexpected copied Maven config");
        if (arguments.contains("--")) throw new IOException("Argument-file transport cannot cross an end-of-options marker");
        byte[] bytes = encode(properties(combined)); Files.createDirectories(config.getParent());
        if (originalRef == null) Files.write(config, bytes, StandardOpenOption.CREATE_NEW);
        else { originalRef.verify(); Files.write(config, bytes, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE); originalRef.verify(); }
        Manifest manifest = new Manifest(SCHEMA, WindowsJobProcess.currentMachineId(), Instant.now().toString(),
                source.toString(), compiled.toString(), originalRef, inherited, arguments, FileRef.measure(config));
        byte[] wire = ControlBuild.strictMapper().writeValueAsBytes(manifest);
        if (wire.length > MAXIMUM_BYTES) throw new IOException("Maven argument manifest exceeds bound");
        Files.write(compiled.resolve(MANIFEST), wire, StandardOpenOption.CREATE_NEW);
        readManifest(compiled, arguments);
    }
    public static Manifest readManifest(Path root, List<String> expected) throws IOException {
        Path compiled = absolute(root), path = compiled.resolve(MANIFEST);
        FileRef witness = FileRef.measure(path); byte[] bytes = read(path, witness, Files::newInputStream);
        Manifest manifest = ControlBuild.strictMapper().readValue(bytes, Manifest.class); witness.verify();
        Path source = absolute(Path.of(manifest.sourceRoot()));
        if (!compiled.equals(absolute(Path.of(manifest.compiledRoot()))) || source.equals(compiled)
                || !manifest.arguments().equals(expected)
                || !absolute(Path.of(manifest.configRef().path())).equals(compiled.resolve(CONFIG))) throw new IOException("Maven argument artifact crossed compiler roots or argv");
        List<String> combined = new ArrayList<>(manifest.inheritedArguments()); combined.addAll(manifest.arguments());
        for (String value : combined) argument(value);
        uniqueProperties(combined); manifest.configRef().verify();
        List<String> transported = LEGACY_SCHEMA.equals(manifest.schema()) ? combined : properties(combined);
        if (!Arrays.equals(encode(transported), read(compiled.resolve(CONFIG)))) throw new IOException("Actual Maven config differs from recorded argv");
        manifest.configRef().verify();
        FileRef original = manifest.sourceConfigRef();
        if (original == null) {
            if (!manifest.inheritedArguments().isEmpty() || Files.exists(source.resolve(CONFIG), LinkOption.NOFOLLOW_LINKS)) throw new IOException("Maven source config appeared after compilation");
        } else {
            if (!absolute(Path.of(original.path())).equals(source.resolve(CONFIG))) throw new IOException("Maven original config path differs");
            original.verify();
            if (!manifest.inheritedArguments().equals(inheritedArguments(source))) throw new IOException("Original Maven arguments differ");
            original.verify();
        }
        witness.verify(); return manifest;
    }
    public static String batchText(Path override, List<String> arguments, Path root) throws IOException {
        Path compiled = absolute(root), path = compiled.resolve(MANIFEST);
        if (!Files.exists(path, LinkOption.NOFOLLOW_LINKS)) {
            if (required(override, arguments)) throw new IOException("Long Maven command requires its frozen argument artifact");
            return ControlBuild.mavenBatchText(override, arguments);
        }
        Manifest manifest = readManifest(compiled, arguments); FileRef ref = FileRef.measure(path);
        ControlBuild.mavenBatchText(null, List.of(ref.path(), manifest.configRef().path()));
        String batch = "@echo off\r\nrem xar.maven.arguments " + ref.path() + " " + ref.bytes() + " " + ref.sha256()
                + "\r\nrem xar.maven.config " + manifest.configRef().path() + " " + manifest.configRef().bytes() + " " + manifest.configRef().sha256()
                + "\r\n" + ControlBuild.mavenBatchText(override, LEGACY_SCHEMA.equals(manifest.schema()) ? List.of()
                        : manifest.arguments().stream().filter(value -> !value.startsWith("-D")).toList()).substring("@echo off\r\n".length());
        if (batch.lines().anyMatch(line -> line.length() > CMD_LIMIT)) throw new IOException("Physical Maven batch exceeds CMD line limit");
        ref.verify(); return batch;
    }
    /** Only these two verified derived files may differ from the exact original source inventory. */
    public static Inventories ordinaryInventories(Path sourceRoot, Path compiledRoot,
            List<FileRef> sourcePins, List<FileRef> compiledPins) throws IOException {
        Path source = absolute(sourceRoot), compiled = absolute(compiledRoot), path = compiled.resolve(MANIFEST);
        if (!Files.exists(path, LinkOption.NOFOLLOW_LINKS)) return new Inventories(sourcePins, compiledPins);
        Manifest raw = ControlBuild.strictMapper().readValue(read(path), Manifest.class);
        Manifest manifest = readManifest(compiled, raw.arguments());
        if (!source.equals(absolute(Path.of(manifest.sourceRoot())))) throw new IOException("Unexpected derived Maven argument inventory");
        FileRef manifestRef = FileRef.measure(path);
        if (!compiledPins.contains(manifestRef) || !compiledPins.contains(manifest.configRef())) throw new IOException("Compiled inventory omitted actual Maven argument files");
        if (manifest.sourceConfigRef() != null && !sourcePins.contains(manifest.sourceConfigRef())) throw new IOException("Source inventory omitted original Maven config");
        if (sourcePins.stream().anyMatch(ref -> absolute(Path.of(ref.path())).equals(source.resolve(MANIFEST)))) throw new IOException("Reserved Maven artifact in source");
        List<FileRef> left = sourcePins.stream().filter(ref -> !absolute(Path.of(ref.path())).equals(source.resolve(CONFIG))).toList();
        List<FileRef> right = compiledPins.stream().filter(ref -> !absolute(Path.of(ref.path())).equals(compiled.resolve(CONFIG))
                && !absolute(Path.of(ref.path())).equals(path)).toList();
        return new Inventories(left, right);
    }
    /** Maven config accepts options only; the complete original argv remains in the versioned manifest. */
    private static List<String> properties(List<String> arguments) {
        return arguments.stream().filter(value -> value.startsWith("-D")).toList();
    }
    private static byte[] encode(List<String> arguments) throws IOException {
        byte[] bytes = (String.join("\n", arguments) + "\n").getBytes(StandardCharsets.UTF_8);
        if (bytes.length > MAXIMUM_BYTES) throw new IOException("Maven config exceeds bound");
        return bytes;
    }
    private static void uniqueProperties(List<String> arguments) throws IOException {
        Set<String> keys = new HashSet<>();
        for (String value : arguments) if (value.startsWith("-D")) {
            int end = value.indexOf('='); String key = end < 0 ? value.substring(2) : value.substring(2, end);
            if (!key.matches("[A-Za-z0-9_.-]+") || !keys.add(key)) throw new IOException("Duplicate or invalid Maven property: " + key);
        }
    }
    private static void argument(String value) throws IOException {
        if (value == null || value.isEmpty() || !value.equals(value.strip()) || value.codePoints().anyMatch(c -> c < 32 || c == 127)) throw new IOException("One exact Maven argument per line required");
        try { ControlBuild.mavenBatchText(null, List.of(value)); }
        catch (IllegalArgumentException error) { throw new IOException("Unsafe Maven argument", error); }
    }
    private static Path absolute(Path path) {
        if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IllegalArgumentException("Normalized absolute Maven path required");
        return path;
    }
    private static byte[] read(Path path) throws IOException {
        return read(path, Files::newInputStream);
    }
    private static byte[] read(Path path, ArtifactOpener opener) throws IOException {
        return read(path, FileRef.measure(path), opener);
    }
    private static byte[] read(Path path, FileRef ref, ArtifactOpener opener) throws IOException {
        if (!absolute(Path.of(ref.path())).equals(absolute(path))) throw new IOException("Maven artifact body reference crossed its path");
        if (ref.bytes() > MAXIMUM_BYTES) throw new IOException("Maven argument artifact exceeds bound");
        byte[] bytes;
        try (InputStream input = opener.open(path)) {
            bytes = input.readNBytes(Math.toIntExact(ref.bytes()) + 1);
        }
        if (bytes.length != ref.bytes()) throw new IOException("Maven argument artifact body length differs from measured bytes");
        final String bodySha256;
        try { bodySha256 = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException unavailable) { throw new IOException("Maven artifact SHA-256 is unavailable", unavailable); }
        if (!bodySha256.equals(ref.sha256())) throw new IOException("Maven argument artifact body SHA-256 differs from measured bytes");
        ref.verify(); return bytes;
    }
    private static String utf8(byte[] bytes) throws IOException {
        try { return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString(); }
        catch (CharacterCodingException error) { throw new IOException("Strict UTF-8 Maven config required", error); }
    }
}
