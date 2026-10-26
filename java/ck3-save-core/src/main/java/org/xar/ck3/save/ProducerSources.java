package org.xar.ck3.save;

import java.io.IOException;
import java.io.InputStream;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.jar.JarFile;
import org.xar.ck3.save.SaveContracts.Pin;

/** Binds the code actually loaded to the sources embedded in that same JAR/classes root. */
public final class ProducerSources {
    private static final String PREFIX = "producer-source/ck3-save-core/";
    private ProducerSources() { }
    public enum CodeKind { JAR, CLASSES }
    public record Binding(List<Pin> repositorySources, CodeKind loadedKind, List<Pin> loadedCode) {
        public Binding {
            repositorySources = List.copyOf(repositorySources); loadedCode = List.copyOf(loadedCode);
            if (loadedKind == null || repositorySources.isEmpty() || loadedCode.isEmpty() || loadedKind == CodeKind.JAR && loadedCode.size() != 1) throw new IllegalArgumentException("complete loaded producer binding required");
        }
    }
    public static List<Path> requiredSources(Path repository) throws IOException {
        Path root = repository.resolve("java/ck3-save-core").toRealPath();
        List<Path> files = new ArrayList<>(); files.add(root.resolve("pom.xml"));
        try (var paths = Files.walk(root.resolve("src/main/java"))) {
            files.addAll(paths.filter(Files::isRegularFile).filter(p -> p.toString().endsWith(".java")).sorted().toList());
        }
        if (files.size() < 2 || files.size() > 64) throw new IOException("bounded save-core source closure required");
        return List.copyOf(files);
    }
    public static Binding verify(Path repository) throws IOException {
        Path repo = repository.toRealPath(); Path root = repo.resolve("java/ck3-save-core").toRealPath();
        List<Path> sources = requiredSources(repo);
        Set<String> expected = new TreeSet<>();
        for (Path source : sources) expected.add(root.relativize(source).toString().replace('\\', '/'));
        Path code;
        try { code = Path.of(ProducerSources.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath(); }
        catch (URISyntaxException | NullPointerException invalid) { throw new IOException("save-core loaded code location unavailable", invalid); }
        List<Pin> loaded = new ArrayList<>(); List<Pin> pins = new ArrayList<>();
        if (Files.isRegularFile(code)) {
            loaded.add(FilePins.pin(code));
            try (JarFile jar = new JarFile(code.toFile())) {
                Set<String> actual = new TreeSet<>();
                jar.stream().filter(e -> !e.isDirectory() && e.getName().startsWith(PREFIX)).forEach(e -> actual.add(e.getName().substring(PREFIX.length())));
                if (!actual.equals(expected)) throw new IOException("loaded save-core embedded source inventory differs");
                for (Path source : sources) {
                    String name = PREFIX + root.relativize(source).toString().replace('\\', '/');
                    try (InputStream input = jar.getInputStream(jar.getJarEntry(name))) { check(source, input); }
                    pins.add(FilePins.pin(source));
                }
            }
        } else if (Files.isDirectory(code)) {
            Path embedded = code.resolve(PREFIX); Set<String> actual = new TreeSet<>();
            try (var paths = Files.walk(embedded)) {
                for (Path path : paths.filter(Files::isRegularFile).toList()) actual.add(embedded.relativize(path).toString().replace('\\', '/'));
            }
            if (!actual.equals(expected)) throw new IOException("loaded save-core classes embedded source inventory differs");
            for (Path source : sources) {
                try (InputStream input = Files.newInputStream(embedded.resolve(root.relativize(source)))) { check(source, input); }
                pins.add(FilePins.pin(source));
            }
            try (var paths = Files.walk(code.resolve("org/xar/ck3/save"))) {
                List<Path> classes = paths.filter(Files::isRegularFile).filter(p -> p.toString().endsWith(".class")).sorted().toList();
                if (classes.isEmpty() || classes.size() > 256) throw new IOException("bounded loaded save-core class inventory required");
                for (Path path : classes) loaded.add(FilePins.pin(path));
            }
        } else throw new IOException("save-core code must be a JAR or classes directory");
        return new Binding(pins, Files.isRegularFile(code) ? CodeKind.JAR : CodeKind.CLASSES, loaded);
    }
    private static void check(Path source, InputStream input) throws IOException {
        if (Files.size(source) > 2 * 1024 * 1024) throw new IOException("save-core source byte cap exceeded");
        byte[] embedded = input.readNBytes(2 * 1024 * 1024 + 1);
        if (embedded.length > 2 * 1024 * 1024 || !Arrays.equals(Files.readAllBytes(source), embedded)) throw new IOException("loaded save-core source differs: " + source);
    }
}
