package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.zip.ZipFile;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Exercises the actual separate observer against the default installed Maven API, without a nested build. */
final class MavenRepositoryDiagnosticTest {
    private static URLClassLoader loader;
    private static Class<?> spy;

    @BeforeAll static void compileActualObserver(@TempDir Path temporary) throws Exception {
        assertTrue(Runtime.version().feature() >= 21, "JDK21 or newer is required to compile --release 21");
        Path module = Path.of(System.getProperty("basedir")).toRealPath();
        Path versionLog = temporary.resolve("default-maven-version.log");
        Path cmd = Path.of(System.getenv("SystemRoot"), "System32/cmd.exe").toRealPath();
        Process child = new ProcessBuilder(cmd.toString(), "/d", "/c", "call mvn --version")
                .directory(module.toFile()).redirectErrorStream(true).redirectOutput(versionLog.toFile()).start();
        try {
            assertTrue(child.waitFor(30, TimeUnit.SECONDS), "Original default Maven version probe timed out");
            assertEquals(0, child.exitValue()); assertTrue(Files.size(versionLog) < 8192);
        } finally { if (child.isAlive()) { child.destroyForcibly(); assertTrue(child.waitFor(10, TimeUnit.SECONDS)); } }
        var maven = CiBootstrap.requireDefaultMaven(Files.readString(versionLog));
        Path output = Files.createDirectory(temporary.resolve("compiled-observer"));
        Path jar = CiBootstrap.buildRepositorySpy(module, output, "unit-fixture-not-pipeline-qualification", maven, "0".repeat(40));
        try (ZipFile archive = new ZipFile(jar.toFile())) {
            assertNotNull(archive.getEntry("org/xar/ck3/control/build/MavenRepositorySpy.class"));
            assertNotNull(archive.getEntry("org/xar/ck3/control/build/CiBootstrap.class"));
            assertNull(archive.getEntry("org/apache/maven/eventspy/EventSpy.class"), "Actual Maven API stays provided");
            String component = new String(archive.getInputStream(archive.getEntry("META-INF/plexus/components.xml")).readAllBytes(), StandardCharsets.UTF_8);
            assertTrue(component.contains("org.apache.maven.eventspy.EventSpy"));
        }
        List<java.net.URL> urls = new ArrayList<>(); urls.add(jar.toUri().toURL());
        for (Path library : CiBootstrap.observedMavenLibraries(maven)) urls.add(library.toUri().toURL());
        loader = new URLClassLoader(urls.toArray(java.net.URL[]::new), ClassLoader.getPlatformClassLoader());
        spy = loader.loadClass("org.xar.ck3.control.build.MavenRepositorySpy");
        assertTrue(loader.loadClass("org.apache.maven.eventspy.EventSpy").isAssignableFrom(spy));
    }

    @AfterAll static void closeActualObserver() throws IOException { if (loader != null) loader.close(); }

    @Test void onlyOriginalVerboseClassLoadsCountAndTestRepositoryDriftIsRetained(@TempDir Path root) throws Exception {
        Path log = root.resolve("product.stdout.log");
        Files.writeString(log, "[DEBUG] Using manager EnhancedLocalRepositoryManager for C:\\Users\\runneradmin\\.m2\\repository\n"
                + "[INFO] --- quarkus:3.33.3.2:generate-code-tests (default) ---\n"
                + "[DEBUG] Using manager EnhancedLocalRepositoryManager for D:\\Users\\runneradmin\\.m2\\repository\n"
                + "Candidate classpath: io.quarkus.bootstrap.resolver.maven.BootstrapMavenContext source: file:/ignored.jar\n"
                + "[0.221s][1234][info][class,load] io.quarkus.bootstrap.resolver.maven.BootstrapMavenContext source: file:/actual.jar\n"
                + "[0.222s][1234][info][class,load] io.quarkus.maven.QuarkusBootstrapProvider source: file:/actual-provider.jar\n"
                + "[0.223s][1234][info][class,load] io.quarkus.bootstrap.util.PropertyUtils source: file:/actual-properties.jar\n"
                + "[0.224s][1234][info][class,load] io.quarkus.maven.QuarkusBootstrapProvider$QuarkusMavenAppBootstrap source: file:/actual-provider.jar\n"
                + "[0.225s][4321][info][class,load] io.quarkus.maven.QuarkusBootstrapProvider source: file:/child-only.jar\n"
                + "[0.226s][info][class,load] io.quarkus.bootstrap.util.PropertyUtils source: file:/without-pid.jar\n"
                + "[0.226s][1234][info][class,load] io.quarkus.maven.QuarkusBootstrapProvider$$FastClassByGuice$$235309042 source: __JVM_DefineClass__\n"
                + "[0.227s][1234][info][class,load] io.quarkus.maven.QuarkusBootstrapProviderOther source: file:/unrelated-provider.jar\n"
                + "[0.222s][info][class,load] some.unrelated.Class source: file:/unrelated.jar\n");
        Object facts = invoke("logFacts", new Class<?>[] {Path.class, String.class, String.class}, log, "product", "stdout");
        Object managersValue = accessor(facts, "managers"), classesValue = accessor(facts, "loadedClasses");
        assertInstanceOf(List.class, managersValue); assertInstanceOf(List.class, classesValue);
        if (!(managersValue instanceof List<?> managers) || !(classesValue instanceof List<?> classes)) throw new AssertionError("Typed list contract changed");
        assertEquals(2, managers.size()); assertEquals(false, accessor(managers.getFirst(), "afterGenerateCodeTests"));
        assertEquals(true, accessor(managers.getLast(), "afterGenerateCodeTests"));
        assertEquals("D:\\Users\\runneradmin\\.m2\\repository", accessor(managers.getLast(), "repository"));
        assertEquals(6, classes.size()); assertEquals("file:/actual.jar", accessor(classes.getFirst(), "source"));
        assertEquals("1234", accessor(classes.getFirst(), "processIdDecimal"));
        assertEquals(List.of("io.quarkus.bootstrap.resolver.maven.BootstrapMavenContext", "io.quarkus.maven.QuarkusBootstrapProvider",
                "io.quarkus.bootstrap.util.PropertyUtils", "io.quarkus.maven.QuarkusBootstrapProvider$QuarkusMavenAppBootstrap"),
                List.of(accessor(classes.get(0), "binaryName"), accessor(classes.get(1), "binaryName"),
                        accessor(classes.get(2), "binaryName"), accessor(classes.get(3), "binaryName")));
        for (int index = 0; index < classes.size(); index++) {
            Object observed = classes.get(index);
            assertEquals(index < 4, invoke("isOriginalJvmClass", new Class<?>[] {observed.getClass(), String.class}, observed, "1234"),
                    "Child JVM and unbound legacy verbose-class lines cannot qualify as the original Maven JVM");
        }
        assertEquals("4321", accessor(classes.get(4), "processIdDecimal"));
        assertNull(accessor(classes.get(5), "processIdDecimal"));
        assertEquals(true, invoke("isObservedTarget", new Class<?>[] {String.class}, "io.quarkus.maven.QuarkusBootstrapProvider$QuarkusMavenAppBootstrap"));
        assertEquals(false, invoke("isObservedTarget", new Class<?>[] {String.class}, "io.quarkus.maven.QuarkusBootstrapProviderOther"));
        assertEquals(false, invoke("isObservedTarget", new Class<?>[] {String.class}, "io.quarkus.maven.QuarkusBootstrapProvider$$FastClassByGuice$$235309042"));
        assertEquals(false, invoke("isObservedTarget", new Class<?>[] {String.class}, "io.quarkus.maven.QuarkusBootstrapProvider$UnlistedNested"));
    }

    @Test void originalNonzeroProcessWaitCannotBecomeObserverPass(@TempDir Path root) throws Exception {
        Path cmd = Path.of(System.getenv("SystemRoot"), "System32/cmd.exe").toRealPath();
        Object result = invoke("capture", new Class<?>[] {List.class, Path.class, Path.class, Path.class, long.class, long.class, Path.class},
                List.of(cmd.toString(), "/d", "/c", "exit /b 37"), root, root.resolve("stdout.log"), root.resolve("stderr.log"), 4096L, 10_000L, root);
        assertEquals(37, accessor(result, "originalExit")); assertNull(accessor(result, "stopReason"));
        assertTrue(accessor(result, "processIdDecimal") instanceof String);
    }

    @Test void inheritedJvmExtensionsAndSpacedPathsArePreservedAndInjectionRejected() throws Exception {
        String original = "-Xmx512m \"-Dmaven.ext.class.path=C:\\Existing Tools\\observer.jar\" -Dother=value";
        assertEquals("C:\\Existing Tools\\observer.jar", invoke("inheritedProperty", new Class<?>[] {String.class, String.class}, original, "maven.ext.class.path"));
        assertEquals("\"-Dmaven.ext.class.path=C:\\Existing Tools\\observer.jar;D:\\new observer.jar\"",
                invoke("jvmProperty", new Class<?>[] {String.class, String.class}, "maven.ext.class.path", "C:\\Existing Tools\\observer.jar;D:\\new observer.jar"));
        assertThrows(IOException.class, () -> invoke("inheritedProperty", new Class<?>[] {String.class, String.class}, "\"unfinished", "maven.ext.class.path"));
        assertThrows(IOException.class, () -> invoke("cmdArgument", new Class<?>[] {String.class}, "safe&other"));
        assertThrows(IOException.class, () -> invoke("jvmProperty", new Class<?>[] {String.class, String.class}, "name", "value\nGITHUB_ENV=injection"));
    }

    @Test void sensitiveOriginalSettingsAreOnlyHashedWithoutCopyingXml(@TempDir Path root) throws Exception {
        Path settings = root.resolve("original-settings.xml");
        byte[] secret = "<settings><servers><server><password>unit-fixture-secret</password></server></servers></settings>".getBytes(StandardCharsets.UTF_8);
        Files.write(settings, secret);
        Object pin = invoke("settingsPin", new Class<?>[] {java.io.File.class}, settings.toFile());
        assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(secret)), accessor(pin, "sha256"));
        assertEquals((long) secret.length, accessor(pin, "bytes"));
        try (var files = Files.list(root)) { assertEquals(List.of(settings), files.toList(), "No full sensitive settings copy is produced"); }
    }

    @Test void boundedStreamsStopRecordingInsteadOfReportingCleanBusinessFailure(@TempDir Path root) throws Exception {
        Path cmd = Path.of(System.getenv("SystemRoot"), "System32/cmd.exe").toRealPath();
        Object result = invoke("capture", new Class<?>[] {List.class, Path.class, Path.class, Path.class, long.class, long.class, Path.class},
                List.of(cmd.toString(), "/d", "/c", "for /L %i in (1,1,3000) do @echo evidence-output"), root,
                root.resolve("stdout.log"), root.resolve("stderr.log"), 256L, 10_000L, root);
        assertEquals("DIAGNOSTIC_OUTPUT_LIMIT_OR_IO", accessor(result, "stopReason"));
        assertTrue(Files.size(root.resolve("stdout.log")) + Files.size(root.resolve("stderr.log")) <= 256);
    }

    @Test void actualCollectRetainsUnavailableDeclaredSourceAndNeverPromotesGeneratedOrigin(@TempDir Path root) throws Exception {
        String target = "io.quarkus.bootstrap.resolver.maven.BootstrapMavenContext";
        String generated = "io.quarkus.maven.QuarkusBootstrapProvider$$FastClassByGuice$$235309042";
        Path repository = Files.createDirectory(root.resolve("repository"));
        Path gav = Files.createDirectories(repository.resolve("org/xar/ck3/ck3-save-core/0.1.0"));
        Files.writeString(gav.resolve("ck3-save-core-0.1.0.jar"), "unit selected-GAV bytes, not a loaded-class origin");
        Files.writeString(gav.resolve("ck3-save-core-0.1.0.pom"), "unit selected-GAV POM");
        Files.writeString(root.resolve("maven-jvm.pid"), "1234", StandardCharsets.US_ASCII);
        Files.writeString(root.resolve("leaf.stdout.log"), "[DEBUG] Using manager EnhancedLocalRepositoryManager for " + repository + "\n");
        Files.writeString(root.resolve("leaf.stderr.log"), "");
        String originalLog = "[0.221s][1234][info][class,load] " + target + " source: __JVM_DefineClass__\n"
                + "[0.222s][1234][info][class,load] " + generated + " source: __JVM_DefineClass__\n";
        Files.writeString(root.resolve("product.stdout.log"), originalLog);
        Files.writeString(root.resolve("product.stderr.log"), "");
        Path cmd = Path.of(System.getenv("SystemRoot"), "System32/cmd.exe").toRealPath();
        Object waited = invoke("capture", new Class<?>[] {List.class, Path.class, Path.class, Path.class, long.class, long.class, Path.class},
                List.of(cmd.toString(), "/d", "/c", "exit /b 0"), root, root.resolve("fixture.stdout.log"),
                root.resolve("fixture.stderr.log"), 4096L, 10_000L, root);
        if (!(waited instanceof Record originalWait)) throw new AssertionError("Actual command wait record required");
        // This is an actual harmless command wait in a deliberately unavailable unit fixture, never a Maven qualification.
        Path wait = root.resolve("product.original-wait.actual.json"); CiBootstrap.publish(wait, originalWait);
        List<String> classpath = new ArrayList<>();
        classpath.add(Path.of(MavenRepositoryDiagnosticTest.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString());
        for (var url : loader.getURLs()) classpath.add(Path.of(url.toURI()).toString());
        Path output = root.resolve("collect.stdout.log"), error = root.resolve("collect.stderr.log");
        ProcessBuilder builder = new ProcessBuilder(Path.of(System.getProperty("java.home"), "bin/java.exe").toString(),
                "-Xmx128m", "-cp", String.join(java.io.File.pathSeparator, classpath), CollectFixture.class.getName(), root.toString())
                .directory(root.toFile()).redirectOutput(output.toFile()).redirectError(error.toFile());
        builder.environment().put("GITHUB_SHA", "0".repeat(40));
        Process child = builder.start();
        try {
            assertTrue(child.waitFor(30, TimeUnit.SECONDS), "Actual collect fixture timed out");
            assertEquals(1, child.exitValue(), "A declared target with no file-scheme origin must remain unavailable");
        } finally { if (child.isAlive()) { child.destroyForcibly(); assertTrue(child.waitFor(10, TimeUnit.SECONDS)); } }
        assertTrue(Files.size(output) + Files.size(error) < 8192);
        Method parse = CiBootstrap.class.getDeclaredMethod("parse", byte[].class); parse.setAccessible(true);
        Object readback = parse.invoke(null, (Object) Files.readAllBytes(root.resolve("gav-readback.actual.json")));
        assertEquals(false, accessor(jsonField(readback, "diagnostic_complete"), "value"));
        Object classesValue = accessor(jsonField(readback, "loaded_classes"), "values");
        if (!(classesValue instanceof List<?> classes)) throw new AssertionError("Actual class array required");
        assertEquals(1, classes.size(), "Generated Guice pseudo-source is not a declared target or JAR origin");
        Object actual = classes.getFirst();
        assertEquals(target, accessor(jsonField(actual, "binary_name"), "value"));
        assertEquals("__JVM_DefineClass__", accessor(jsonField(actual, "observed_source"), "value"));
        assertEquals("IOException: Actual local file-scheme JAR class code-source required", accessor(jsonField(actual, "unavailable"), "value"));
        assertEquals("JNull", jsonField(actual, "jar_ref").getClass().getSimpleName());
        assertEquals("JNull", jsonField(actual, "javap_ref").getClass().getSimpleName());
        assertEquals(2, ((List<?>) accessor(jsonField(readback, "selected_gav_files"), "values")).size(), "Collect must finish GAV readback after unavailable class");
        assertFalse(Files.readString(root.resolve("gav-readback.actual.json")).contains("NullPointerException"));
        assertEquals(originalLog, Files.readString(root.resolve("product.stdout.log")), "Raw generated-class observation remains unchanged");
    }

    /** Child fixture binds its own GITHUB_SHA; no production environment or Maven build is changed. */
    public static final class CollectFixture {
        private CollectFixture() { }
        public static void main(String[] arguments) throws Exception {
            Path root = Path.of(arguments[0]);
            Method execute = Class.forName("org.xar.ck3.control.build.MavenRepositorySpy").getMethod("execute",
                    String.class, Path.class, Path.class, String.class, Path.class, String[].class);
            System.exit((Integer) execute.invoke(null, "collect", root, root, "unit-fixture-not-pipeline-qualification", root, new String[0]));
        }
    }

    private static Object jsonField(Object value, String name) throws Exception {
        Object fields = accessor(value, "values");
        if (!(fields instanceof java.util.Map<?, ?> object) || !object.containsKey(name)) throw new AssertionError("Missing typed JSON field: " + name);
        return object.get(name);
    }

    private static Object accessor(Object value, String name) throws Exception {
        Method method = value.getClass().getDeclaredMethod(name); method.setAccessible(true); return method.invoke(value);
    }
    private static Object invoke(String name, Class<?>[] types, Object... arguments) throws Exception {
        Method method = spy.getDeclaredMethod(name, types); method.setAccessible(true);
        try { return method.invoke(null, arguments); }
        catch (InvocationTargetException failure) {
            if (failure.getCause() instanceof Exception actual) throw actual;
            throw new AssertionError(failure.getCause());
        }
    }
}
