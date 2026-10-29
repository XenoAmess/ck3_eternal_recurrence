package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

class ClosedAdoptionEnvironmentTest {
    @Test void explicitRootsReplaceInheritedRootsCaseInsensitivelyAndCannotBeMutated() {
        Path repo = Path.of("D:/owned/current-repo"), sdk = Path.of("D:/owned/original-sdk"), output = Path.of("D:/owned/output");
        Map<String,String> inherited = new HashMap<>(Map.of("PythonPath","Z:/unqualified/repo","pYtHoNhOmE","Z:/unqualified/python",
                "PYTHONUSERBASE","Z:/unqualified/user","pythonNoUserSite","0","pythonSafePath","0","TMP","Z:/old/temp","XAR_KEEP","retained"));
        Map<String,String> before = Map.copyOf(inherited);
        Map<String,String> environment = ClosedAdoptionMain.sessionEnvironment(repo,sdk,output,inherited);
        assertEquals(before,inherited);
        assertEquals(repo.toAbsolutePath().normalize()+java.io.File.pathSeparator+sdk.toAbsolutePath().normalize(),environment.get("PYTHONPATH"));
        assertFalse(environment.keySet().stream().anyMatch(key -> key.equalsIgnoreCase("PYTHONHOME") || key.equalsIgnoreCase("PYTHONUSERBASE")));
        assertEquals(1,environment.keySet().stream().filter(key -> key.equalsIgnoreCase("PYTHONPATH")).count());
        for (String key : List.of("PYTHONNOUSERSITE","PYTHONSAFEPATH","PYTHONDONTWRITEBYTECODE","PYTHONUTF8")) { assertEquals("1",environment.get(key)); }
        assertEquals(output.toAbsolutePath().normalize().toString(),environment.get("TMP"));
        assertEquals(environment.get("TMP"),environment.get("TEMP")); assertEquals("retained",environment.get("XAR_KEEP"));
        assertThrows(UnsupportedOperationException.class,() -> environment.put("PYTHONPATH","Z:/replacement"));
    }

    @Test void realOriginalInterpreterImportsOnlyExplicitFreshRootsAndRejectsInheritedAndCwdFallback() throws Exception {
        String configured = System.getProperty("xar.python");
        if (configured == null || configured.isBlank()) { configured = System.getenv("XAR_ORACLE_PYTHON"); }
        assertNotNull(configured,"UNAVAILABLE: Root must supply the actual Python EXE through xar.python or XAR_ORACLE_PYTHON");
        Path python = Path.of(configured).toRealPath();
        Path scratch = Path.of(System.getProperty("xar.scratch","D:/codex-ck3-demos/2026-10-22-java-phase1/scratch")).toRealPath();
        Path root = Files.createTempDirectory(scratch,"closed-environment-"), repo = Files.createDirectory(root.resolve("fresh-repo")),
                sdk = Files.createDirectory(root.resolve("original-sdk")), output = Files.createDirectory(root.resolve("output")),
                inheritedRoot = Files.createDirectory(root.resolve("inherited-repo"));
        Files.writeString(repo.resolve("fresh_transport_probe.py"),"VALUE = 'fresh'\n",StandardCharsets.UTF_8);
        Files.writeString(sdk.resolve("fresh_sdk_probe.py"),"VALUE = 'original'\n",StandardCharsets.UTF_8);
        Files.writeString(inheritedRoot.resolve("fresh_transport_probe.py"),"raise RuntimeError('inherited transport fallback')\n",StandardCharsets.UTF_8);
        Files.writeString(inheritedRoot.resolve("canonical_fallback_probe.py"),"VALUE = 'unqualified'\n",StandardCharsets.UTF_8);
        Files.writeString(output.resolve("canonical_fallback_probe.py"),"VALUE = 'cwd fallback'\n",StandardCharsets.UTF_8);
        Map<String,String> inherited = new HashMap<>(System.getenv()); inherited.put("PYTHONPATH",inheritedRoot.toString());
        inherited.put("PyThOnHoMe",inheritedRoot.toString());
        Map<String,String> environment = ClosedAdoptionMain.sessionEnvironment(repo,sdk,output,inherited);
        String program = "import importlib.util,json; import fresh_transport_probe as transport; import fresh_sdk_probe as sdk; "
                +"assert transport.VALUE == 'fresh'; assert sdk.VALUE == 'original'; "
                +"assert importlib.util.find_spec('canonical_fallback_probe') is None; "
                +"print(json.dumps({'transport':transport.__file__,'sdk':sdk.__file__,'fallback':False}))";
        Path stdout = output.resolve("stdout.json"), stderr = output.resolve("stderr.log");
        var command = new WindowsJobProcess.CommandSpec(python,List.of("-B","-u","-X","utf8","-c",program),output,environment,stdout,stderr,268_435_456);
        Instant deadline = Instant.now().plusSeconds(30);
        try (var job = WindowsJobProcess.start(command)) {
            var actual = job.await(Duration.ofSeconds(25),deadline,() -> {
                try { assertTrue((!Files.exists(stdout) || Files.size(stdout)<=65536) && (!Files.exists(stderr) || Files.size(stderr)<=65536)); }
                catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
            });
            assertTrue(actual.passed(),"actual process/Job must pass; stderr="+Files.readString(stderr,StandardCharsets.UTF_8));
            assertEquals(0,actual.accounting().activeProcesses());
        }
        var result = StrictJson.parse(Files.readAllBytes(stdout));
        assertEquals(repo.resolve("fresh_transport_probe.py").toRealPath(),Path.of(StrictJson.text(result.get("transport"))).toRealPath());
        assertEquals(sdk.resolve("fresh_sdk_probe.py").toRealPath(),Path.of(StrictJson.text(result.get("sdk"))).toRealPath());
        assertFalse(result.get("fallback").booleanValue());
        assertFalse(Files.exists(repo.resolve("__pycache__"))); assertFalse(Files.exists(sdk.resolve("__pycache__")));
    }
}
