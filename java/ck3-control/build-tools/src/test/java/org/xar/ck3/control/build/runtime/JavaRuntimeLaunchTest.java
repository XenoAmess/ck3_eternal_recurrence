package org.xar.ck3.control.build.runtime;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;
import org.xar.ck3.control.build.ProjectStoragePolicy;

final class JavaRuntimeLaunchTest {
    @TempDir Path temporary;

    @Test void versionedProducerAndStrictConsumerPreserveModeAndRejectMissingUnknownOrCoercedFields() throws Exception {
        Request request = JavaRuntimePackageTest.request(temporary, HostMode.MCP_STDIO);
        byte[] produced = JavaRuntimePackageCodec.encodeRequest(request);
        assertEquals(request, JavaRuntimePackageCodec.decodeRequest(produced));
        String body = new String(produced, StandardCharsets.UTF_8);
        for (String replacement : List.of("true", "1.0", "\"18080\"", "null")) {
            assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(body.replace("\"http_port\":18080",
                    "\"http_port\":" + replacement).getBytes(StandardCharsets.UTF_8)));
        }
        for (String replacement : List.of("null", "true", "0", "\"OTHER\"")) {
            assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(body.replace("\"mode\":\"MCP_STDIO\"",
                    "\"mode\":" + replacement).getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(body.replace("\"mode\":\"MCP_STDIO\",", "").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest((body + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest((body.substring(0, body.length() - 1) + ",\"unknown\":0}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(body.replace("/v3", "/v2").getBytes(StandardCharsets.UTF_8)));
    }

    @Test void metadataDecoderRejectsMalformedUtf8AndDuplicateProducerFields() throws Exception {
        Request request = JavaRuntimePackageTest.request(temporary, HostMode.HTTP);
        String body = new String(JavaRuntimePackageCodec.encodeRequest(request), StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(body.replace("\"http_port\":18080",
                "\"http_port\":18080,\"http_port\":18080").getBytes(StandardCharsets.UTF_8)));
    }

    @Test void fixedJavaArgvUsesManifestModeAndExactPackagePathsWithZeroApplicationArguments() throws Exception {
        Request request = JavaRuntimePackageTest.request(temporary, HostMode.MCP_STDIO);
        List<String> arguments = JavaRuntimeLaunch.fixedArguments(request);
        assertEquals(List.of("-Xms33554432", "-Xmx268435456", "-Dfile.encoding=UTF-8",
                "-Djava.io.tmpdir=" + request.launch().temporaryRoot(), "-Djna.tmpdir=" + request.launch().nativeScratchRoot(),
                "-Djna.nosys=true", "-Dquarkus.http.host=127.0.0.1", "-Dquarkus.http.port=18080",
                "-Dquarkus.log.console.stderr=true", "-Dquarkus.banner.enabled=false", "-Dxar.application.mode=MCP_STDIO",
                "-Dxar.application.configuration=" + Path.of(request.outputRoot()).resolve(JavaRuntimePackage.HOST_CONFIGURATION_FILE),
                "-Dxar.runtime.package.manifest=" + Path.of(request.outputRoot()).resolve(JavaRuntimePackage.MANIFEST_FILE),
                "-jar", Path.of(request.outputRoot()).resolve("quarkus-app/quarkus-run.jar").toString()), arguments);
        assertEquals(arguments.size() - 2, arguments.indexOf("-jar"));
        assertThrows(UnsupportedOperationException.class, () -> arguments.add("--nonwar-only"));
    }

    @Test void managedProducerKeepsFiniteThreeArgumentsAndOwnsDiagnosticsBeforeJar()throws Exception {
        Request request=JavaRuntimePackageTest.request(temporary,HostMode.MCP_STDIO);
        Path out=temporary.resolve("owned-output");
        var paths=new JavaRuntimeLaunch.ManagedCommandPaths(out.resolve("stdout.log"),out.resolve("stderr.log"),
                Path.of(request.launch().temporaryRoot()),Path.of(request.launch().nativeScratchRoot()),512L<<20);
        var finite=List.of(temporary.resolve("finite-request.json").toString(),"17","a".repeat(64));
        var managed=JavaRuntimeLaunch.managedArguments(request,finite,paths);
        assertEquals(finite,managed.subList(managed.size()-3,managed.size()));
        assertEquals(1,java.util.Collections.frequency(managed,"-jar"));
        assertEquals(1,java.util.Collections.frequency(managed,finite.getFirst()));
        for(String diagnostic:List.of("-XX:ErrorFile="+out.resolve("hs_err_pid%p.log"),
                "-XX:ReplayDataFile="+out.resolve("replay_pid%p.log"),"-XX:HeapDumpPath="+out)) {
            assertTrue(managed.contains(diagnostic));assertTrue(managed.indexOf(diagnostic)<managed.indexOf("-jar"));
        }
        assertEquals("-Djava.io.tmpdir="+request.launch().temporaryRoot(),managed.get(3));
        assertEquals("-Djna.tmpdir="+request.launch().nativeScratchRoot(),managed.get(4));
        assertThrows(IOException.class,()->JavaRuntimeLaunch.managedArguments(request,List.of("extra"),paths));
        assertThrows(UnsupportedOperationException.class,()->managed.add("extra"));
    }
    @Test void managedProducerRejectsEitherScratchOverrideAndInvalidOwnedLogs()throws Exception {
        Request request=JavaRuntimePackageTest.request(temporary,HostMode.MCP_STDIO);Path out=temporary.resolve("out");
        for(boolean overrideTemporary:List.of(true,false)) {
            var paths=new JavaRuntimeLaunch.ManagedCommandPaths(out.resolve("stdout"),out.resolve("stderr"),
                    overrideTemporary?temporary.resolve("wrong-tmp"):Path.of(request.launch().temporaryRoot()),
                    overrideTemporary?Path.of(request.launch().nativeScratchRoot()):temporary.resolve("wrong-jna"),512L<<20);
            assertThrows(IOException.class,()->JavaRuntimeLaunch.managedArguments(request,List.of("request","1","a".repeat(64)),paths));
        }
        assertThrows(IllegalArgumentException.class,()->new JavaRuntimeLaunch.ManagedCommandPaths(out.resolve("same"),out.resolve("same"),out,out,1));
        assertThrows(IllegalArgumentException.class,()->new JavaRuntimeLaunch.ManagedCommandPaths(out.resolve("a"),temporary.resolve("elsewhere/b"),out,out,1));
        assertThrows(IllegalArgumentException.class,()->new JavaRuntimeLaunch.ManagedCommandPaths(out.resolve("a"),out.resolve("b"),out,out,0));
    }
    @Test void managedEnvironmentAddsOnlyTheFixedPythonBytecodePolicyToTheSanitizedMap()throws Exception {
        Request request=JavaRuntimePackageTest.request(temporary,HostMode.HTTP);String windows=temporary.resolve("Windows").toString();
        var sanitized=JavaRuntimeLaunch.sanitizedEnvironment(request,Map.of("SystemRoot",windows,"PYTHONPATH","bad",
                "QUARKUS_CONFIG_LOCATIONS","bad","JAVA_TOOL_OPTIONS","bad"),new ProjectStoragePolicy.Configuration(false,Optional.empty()));
        var managed=JavaRuntimeLaunch.managedEnvironment(sanitized);var expected=new LinkedHashMap<>(sanitized);
        expected.put("PYTHONDONTWRITEBYTECODE","1");assertEquals(expected,managed);assertEquals("1",managed.get("PYTHONDONTWRITEBYTECODE"));
        assertFalse(managed.containsKey("PYTHONPATH"));assertFalse(managed.containsKey("JAVA_TOOL_OPTIONS"));
        assertFalse(managed.containsKey("QUARKUS_CONFIG_LOCATIONS"));assertThrows(UnsupportedOperationException.class,()->managed.put("TMP","changed"));
    }
    @Test void environmentIsRebuiltWithoutJavaOptionsQuarkusConfigProxiesPythonOrPathInjection() throws Exception {
        Request request = JavaRuntimePackageTest.request(temporary, HostMode.HTTP);
        String windows = temporary.resolve("Windows").toAbsolutePath().toString();
        Map<String, String> inherited = Map.of("SystemRoot", windows, "WINDIR", windows,
                "PATH", "unreviewed", "JAVA_TOOL_OPTIONS", "-javaagent:unreviewed.jar", "JDK_JAVA_OPTIONS", "-Droot=wrong",
                "QUARKUS_CONFIG_LOCATIONS", "http://unreviewed", "HTTP_PROXY", "http://unreviewed", "PYTHONPATH", "unreviewed");
        Map<String, String> environment = JavaRuntimeLaunch.sanitizedEnvironment(request, inherited,
                new ProjectStoragePolicy.Configuration(false, Optional.empty()));
        assertEquals(7, environment.size());
        assertEquals("false", environment.get(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK));
        assertEquals(request.javaHome().root(), environment.get("JAVA_HOME"));
        assertEquals(request.launch().temporaryRoot(), environment.get("TEMP"));
        assertEquals(environment.get("TEMP"), environment.get("TMP"));
        assertTrue(environment.get("PATH").startsWith(Path.of(request.javaHome().root()).resolve("bin").toString() + ";"));
        for (String key : List.of("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "QUARKUS_CONFIG_LOCATIONS", "HTTP_PROXY", "PYTHONPATH"))
            assertFalse(environment.containsKey(key));
        assertFalse(environment.values().stream().anyMatch(value -> value.contains("unreviewed")));
        assertThrows(UnsupportedOperationException.class, () -> environment.put("JAVA_TOOL_OPTIONS", "bad"));
    }

    @Test void ambiguousOrMissingWindowsEnvironmentFailsClosed() throws Exception {
        Request request = JavaRuntimePackageTest.request(temporary, HostMode.HTTP);
        var storage = new ProjectStoragePolicy.Configuration(false, Optional.empty());
        String windows = temporary.resolve("Windows").toAbsolutePath().toString();
        Map<String, String> duplicate = new LinkedHashMap<>(); duplicate.put("SystemRoot", windows); duplicate.put("systemroot", windows);
        assertThrows(IOException.class, () -> JavaRuntimeLaunch.sanitizedEnvironment(request, duplicate, storage));
        assertThrows(IOException.class, () -> JavaRuntimeLaunch.sanitizedEnvironment(request, Map.of(), storage));
        assertThrows(IOException.class, () -> JavaRuntimeLaunch.sanitizedEnvironment(request, Map.of("SystemRoot", "relative"), storage));
        assertThrows(IOException.class, () -> JavaRuntimeLaunch.sanitizedEnvironment(request, Map.of("SystemRoot", windows,
                "WINDIR", temporary.resolve("OtherWindows").toAbsolutePath().toString()), storage));
    }

    @Test void parsedStoragePolicySurvivesAChildOutsideTheCheckoutWithoutTrustingInheritedFlags() throws Exception {
        Request request = JavaRuntimePackageTest.request(temporary, HostMode.MCP_STDIO);
        Path preferred = temporary.resolve("approved-bulk");
        String windows = temporary.resolve("Windows").toString();
        var storage = new ProjectStoragePolicy.Configuration(true, Optional.of(preferred));
        Map<String, String> environment = JavaRuntimeLaunch.sanitizedEnvironment(request,
                Map.of("SystemRoot", windows, ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "false",
                        ProjectStoragePolicy.PROJECT_STORAGE_ROOT, "relative-unreviewed"), storage);
        assertEquals("true", environment.get(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK));
        assertEquals(preferred.toString(), environment.get(ProjectStoragePolicy.PROJECT_STORAGE_ROOT));
        assertEquals(request.launch().temporaryRoot(), environment.get("TEMP"));
        assertEquals(environment.get("TEMP"), environment.get("TMP"));
        assertFalse(environment.values().contains("relative-unreviewed"));
        assertFalse(environment.containsKey("XAR_AUTOPLAYER_STATE_DIR"));
        assertThrows(UnsupportedOperationException.class, () -> environment.put("TMP", "relative"));
    }
}
