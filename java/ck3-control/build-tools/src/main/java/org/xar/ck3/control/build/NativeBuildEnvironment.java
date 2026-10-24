package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.TreeMap;

/** Shared allowlisted vcvars snapshot producer and reader. This class never starts a process. */
public final class NativeBuildEnvironment {
    private static final String SCHEMA = "xar.native-allowlisted-build-environment.v1";
    private static final String CONFIG_SCHEMA = "xar.native-shared-vcvars-environment/v1";
    private static final String SCOPE = "allowlisted vcvars values; outer actual process identity and Job receipt required";
    public static final String SNAPSHOT_NAME = "VCVARS-ENVIRONMENT01.properties";
    private static final List<String> KEYS = List.of("PATH", "INCLUDE", "LIB", "LIBPATH", "VCToolsInstallDir",
            "VCINSTALLDIR", "WindowsSdkDir", "WindowsSDKVersion", "WindowsSdkBinPath", "WindowsLibPath",
            "UCRTVersion", "UniversalCRTSdkDir", "VSINSTALLDIR", "VisualStudioVersion", "VSCMD_ARG_HOST_ARCH",
            "VSCMD_ARG_TGT_ARCH", "VSCMD_VER", "SystemRoot", "TEMP", "TMP", "TMPDIR");
    private static final Set<String> METADATA = Set.of("schema", "machine_id", "observed_at_utc", "scope");
    private NativeBuildEnvironment() { }

    public record Configuration(String schema, String snapshotOutput) {
        public Configuration {
            if (!CONFIG_SCHEMA.equals(schema) || snapshotOutput == null || !Path.of(snapshotOutput).isAbsolute()) {
                throw new IllegalArgumentException("shared environment configuration and absolute output required");
            }
        }
        public void validateScratch(Path scratch) throws IOException {
            require(absolute(scratch).resolve(SNAPSHOT_NAME).equals(absolute(Path.of(snapshotOutput))),
                    "environment output differs from approved fresh scratch");
        }
    }

    public record Snapshot(String schema, String machineId, Instant observedAt, Map<String, String> values) {
        public Snapshot {
            if (!SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{0,127}")
                    || observedAt == null || values == null) throw new IllegalArgumentException("typed snapshot identity required");
            values = Map.copyOf(values);
            if (!Set.copyOf(KEYS).containsAll(values.keySet())) throw new IllegalArgumentException("unknown snapshot environment field");
            for (var entry : values.entrySet()) {
                String value = entry.getValue();
                if (value.length() > 32768 || value.indexOf('\0') >= 0) throw new IllegalArgumentException("bounded environment value required");
            }
            for (String key : List.of("PATH", "INCLUDE", "LIB", "VCToolsInstallDir", "WindowsSdkDir", "SystemRoot", "TEMP", "TMP", "TMPDIR")) {
                if (!values.containsKey(key) || values.get(key).isBlank()) throw new IllegalArgumentException("missing actual environment field: " + key);
            }
            if (!"x64".equals(values.get("VSCMD_ARG_HOST_ARCH")) || !"x64".equals(values.get("VSCMD_ARG_TGT_ARCH"))) {
                throw new IllegalArgumentException("actual vcvars host and target must be x64");
            }
        }
        public void validateScratch(Path scratch) throws IOException {
            Path expected = absolute(scratch);
            for (String key : List.of("TEMP", "TMP", "TMPDIR")) {
                require(absolute(Path.of(values.get(key))).equals(expected), "native temporary environment escaped approved scratch");
            }
        }
    }

    public static Configuration readConfiguration(JsonNode value, Path scratch) throws IOException {
        require(value != null && value.isObject() && value.size() == 2
                && value.has("schema") && value.get("schema").isTextual()
                && value.has("snapshot_output") && value.get("snapshot_output").isTextual(),
                "exact shared environment configuration fields required; legacy bootstrap argv is not supported");
        try {
            Configuration configuration = new Configuration(value.get("schema").textValue(), value.get("snapshot_output").textValue());
            configuration.validateScratch(scratch); return configuration;
        } catch (IllegalArgumentException error) { throw new IOException("invalid shared environment configuration", error); }
    }

    public static Snapshot capture(Path scratch, String machineId, Map<String, String> environment, Instant observedAt) throws IOException {
        require(environment != null, "actual named environment required");
        Map<String, String> allowed = new TreeMap<>();
        for (String key : KEYS) if (environment.containsKey(key)) allowed.put(key, environment.get(key));
        try {
            Snapshot snapshot = new Snapshot(SCHEMA, machineId, observedAt, allowed);
            snapshot.validateScratch(scratch); return snapshot;
        } catch (IllegalArgumentException | NullPointerException error) { throw new IOException("invalid allowlisted vcvars snapshot", error); }
    }

    public static void write(Path scratch, Path output, Snapshot snapshot) throws IOException {
        require(snapshot != null, "typed snapshot required");
        Path directory = absolute(scratch), target = absolute(output);
        require(target.equals(directory.resolve(SNAPSHOT_NAME)), "create-only environment output differs from approved scratch");
        snapshot.validateScratch(directory);
        require(Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS)
                && directory.toRealPath().equals(directory) && !Files.exists(target, LinkOption.NOFOLLOW_LINKS),
                "plain existing fresh scratch and absent snapshot required");
        Properties properties = new Properties();
        properties.setProperty("schema", snapshot.schema()); properties.setProperty("machine_id", snapshot.machineId());
        properties.setProperty("observed_at_utc", snapshot.observedAt().toString()); properties.setProperty("scope", SCOPE);
        snapshot.values().forEach(properties::setProperty);
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        properties.store(bytes, "Only explicit build environment fields; process qualification is external");
        require(bytes.size() <= 65536, "bounded environment snapshot exceeded");
        Files.write(target, bytes.toByteArray(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }

    public static Snapshot read(Path scratch, String expectedMachineId, byte[] raw) throws IOException {
        require(raw != null && raw.length <= 65536, "bounded actual environment snapshot required");
        require(expectedMachineId != null && expectedMachineId.matches("[a-z0-9][a-z0-9-]{0,127}"), "expected snapshot machine required");
        Properties properties = new UniqueProperties();
        try (InputStream input = new ByteArrayInputStream(raw)) { properties.load(input); }
        catch (IllegalArgumentException error) { throw new IOException("duplicate or malformed environment property", error); }
        Set<String> allowed = new java.util.HashSet<>(KEYS); allowed.addAll(METADATA);
        require(allowed.containsAll(properties.stringPropertyNames()) && properties.stringPropertyNames().containsAll(METADATA),
                "unknown or missing environment snapshot metadata");
        require(SCHEMA.equals(properties.getProperty("schema")) && SCOPE.equals(properties.getProperty("scope"))
                && expectedMachineId.equals(properties.getProperty("machine_id")), "snapshot identity or scope differs");
        Map<String, String> values = new TreeMap<>();
        for (String key : KEYS) if (properties.containsKey(key)) values.put(key, properties.getProperty(key));
        try { return capture(scratch, expectedMachineId, values, Instant.parse(properties.getProperty("observed_at_utc"))); }
        catch (java.time.format.DateTimeParseException error) { throw new IOException("invalid actual environment timestamp", error); }
    }

    /** Only constructs the exact shared vcvars-to-Java metadata command; the caller owns any Job. */
    public static List<String> bootstrapArguments(Path vcvars64, Path javaExecutable, List<Path> classPath,
            Path scratch, String machineId) throws IOException {
        require(classPath != null && !classPath.isEmpty() && classPath.size() <= 7, "finite accepted Java classpath required");
        require(machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{0,127}"), "canonical machine identity required");
        List<String> paths = new ArrayList<>();
        for (Path item : classPath) paths.add(shellPath(item));
        Path directory = absolute(scratch);
        String javaArguments = "-Xms16m -Xmx64m -XX:+UseSerialGC -XX:ActiveProcessorCount=2 -XX:MaxMetaspaceSize=64m "
                + "-XX:ReservedCodeCacheSize=16m -XX:MaxDirectMemorySize=8m -Xss256k -Dfile.encoding=UTF-8 "
                + quote("-Djava.io.tmpdir=" + shellPath(directory)) + " " + quote("-Djna.tmpdir=" + shellPath(directory))
                + " " + quote("-XX:ErrorFile=" + shellPath(directory.resolve("hs_err-native-environment.log")))
                + " " + quote("-XX:ReplayDataFile=" + shellPath(directory.resolve("replay-native-environment.log")))
                + " " + quote("-XX:HeapDumpPath=" + shellPath(directory.resolve("native-environment-heap.hprof")))
                + " -cp " + quote(String.join(";", paths)) + " " + NativeBuildEnvironment.class.getName()
                + " capture " + quote(shellPath(directory)) + " " + quote(shellPath(directory.resolve(SNAPSHOT_NAME))) + " " + machineId;
        return List.of("/d", "/v:off", "/s", "/c", "call " + quote(shellPath(vcvars64)) + " && " + quote(shellPath(javaExecutable)) + " " + javaArguments);
    }

    private static Path absolute(Path value) throws IOException {
        require(value != null && value.isAbsolute(), "absolute environment path required"); return value.toAbsolutePath().normalize();
    }
    private static String shellPath(Path value) throws IOException {
        String text = absolute(value).toString();
        require(!text.matches(".*[\"%!&|<>^;\\r\\n].*"), "shell expansion or control characters in environment path");
        return text;
    }
    private static String quote(String value) { return "\"" + value + "\""; }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }

    /** java.util.Properties is the single dynamic boundary; duplicate decoded names fail before the typed model. */
    private static final class UniqueProperties extends Properties {
        private static final long serialVersionUID = 1L;
        @Override public synchronized Object put(Object key, Object value) {
            if (containsKey(key)) throw new IllegalArgumentException("duplicate environment property");
            return super.put(key, value);
        }
    }

    /** Metadata-only child of the already admitted ENV Job; no stage or native action is dispatched here. */
    public static void main(String[] args) throws IOException {
        require(args.length == 4 && args[0].equals("capture"), "capture APPROVED_SCRATCH EXACT_OUTPUT MACHINE_ID required");
        String actualMachineId = WindowsJobProcess.currentMachineId();
        require(actualMachineId.equals(args[3]), "actual snapshot machine mismatch");
        Path scratch = absolute(Path.of(args[1])), output = absolute(Path.of(args[2]));
        SharedSourceFiles.plainAncestors(scratch);
        write(scratch, output, capture(scratch, actualMachineId, System.getenv(), Instant.now()));
        System.out.println("Actual allowlisted build environment bytes=" + Files.size(output));
    }
}
