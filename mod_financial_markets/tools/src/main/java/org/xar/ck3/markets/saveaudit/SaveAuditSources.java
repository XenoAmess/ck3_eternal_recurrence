package org.xar.ck3.markets.saveaudit;

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
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.ProducerSources;
import org.xar.ck3.save.SaveContracts.Pin;

/** Binds both the actual loaded shared parser and this audit package to their embedded sources. */
public final class SaveAuditSources {
    private SaveAuditSources() { }
    private static final String PREFIX = "producer-source/financial-save-audit/";
    private static final String PACKAGE = "src/main/java/org/xar/ck3/markets/saveaudit";
    public record Binding(ProducerSources.Binding saveCore, List<Pin> auditSources,
                          ProducerSources.CodeKind auditCodeKind, List<Pin> loadedAuditCode) {
        public Binding {
            auditSources = List.copyOf(auditSources); loadedAuditCode = List.copyOf(loadedAuditCode);
            if (saveCore == null || auditCodeKind == null || auditSources.isEmpty() || loadedAuditCode.isEmpty()
                    || auditCodeKind == ProducerSources.CodeKind.JAR && loadedAuditCode.size() != 1)
                throw new IllegalArgumentException("complete shared-parser and audit-source binding required");
        }
    }
    public static Binding verify(Path repository) throws IOException {
        Path repo = repository.toRealPath(), tools = repo.resolve("mod_financial_markets/tools").toRealPath();
        ProducerSources.Binding shared = ProducerSources.verify(repo);
        List<Path> sources = new ArrayList<>(); sources.add(tools.resolve("pom.xml"));
        try (var paths = Files.walk(tools.resolve(PACKAGE))) {
            sources.addAll(paths.filter(Files::isRegularFile).filter(p -> p.toString().endsWith(".java")).sorted().toList());
        }
        if (sources.size() < 4 || sources.size() > 32) throw new IOException("bounded audit source closure required");
        Set<String> expected = new TreeSet<>();
        for (Path source : sources) expected.add(tools.relativize(source).toString().replace('\\', '/'));
        Path code;
        try { code = Path.of(SaveAuditSources.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath(); }
        catch (URISyntaxException | NullPointerException invalid) { throw new IOException("loaded audit code location unavailable", invalid); }
        List<Pin> pins = new ArrayList<>(), loaded = new ArrayList<>();
        if (Files.isRegularFile(code)) {
            loaded.add(FilePins.pin(code));
            try (JarFile jar = new JarFile(code.toFile())) {
                Set<String> actual = new TreeSet<>();
                jar.stream().filter(e -> !e.isDirectory() && e.getName().startsWith(PREFIX)).forEach(e -> actual.add(e.getName().substring(PREFIX.length())));
                if (!actual.equals(expected)) throw new IOException("loaded audit embedded source inventory differs");
                for (Path source : sources) {
                    try (InputStream input = jar.getInputStream(jar.getJarEntry(PREFIX + tools.relativize(source).toString().replace('\\', '/')))) { check(source, input); }
                    pins.add(FilePins.pin(source));
                }
            }
        } else if (Files.isDirectory(code)) {
            Path embedded = code.resolve(PREFIX); Set<String> actual = new TreeSet<>();
            try (var paths = Files.walk(embedded)) {
                for (Path source : paths.filter(Files::isRegularFile).toList()) actual.add(embedded.relativize(source).toString().replace('\\', '/'));
            }
            if (!actual.equals(expected)) throw new IOException("loaded audit classes source inventory differs");
            for (Path source : sources) {
                try (InputStream input = Files.newInputStream(embedded.resolve(tools.relativize(source)))) { check(source, input); }
                pins.add(FilePins.pin(source));
            }
            try (var paths = Files.walk(code.resolve("org/xar/ck3/markets/saveaudit"))) {
                List<Path> classes = paths.filter(Files::isRegularFile).filter(p -> p.toString().endsWith(".class")).sorted().toList();
                if (classes.isEmpty() || classes.size() > 256) throw new IOException("bounded loaded audit class inventory required");
                for (Path item : classes) loaded.add(FilePins.pin(item));
            }
        } else throw new IOException("loaded audit code must be a JAR or classes directory");
        return new Binding(shared, pins, Files.isRegularFile(code) ? ProducerSources.CodeKind.JAR : ProducerSources.CodeKind.CLASSES, loaded);
    }
    private static void check(Path source, InputStream embedded) throws IOException {
        if (embedded == null || Files.size(source) > 2 * 1024 * 1024
                || !Arrays.equals(Files.readAllBytes(source), embedded.readNBytes(2 * 1024 * 1024 + 1)))
            throw new IOException("loaded audit source differs: " + source);
    }
}
