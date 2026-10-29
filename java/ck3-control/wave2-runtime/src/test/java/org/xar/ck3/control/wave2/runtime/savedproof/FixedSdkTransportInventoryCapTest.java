package org.xar.ck3.control.wave2.runtime.savedproof;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Executes the fixed producer entry with a synthetic SDK import stop, never an SDK measurement token. */
class FixedSdkTransportInventoryCapTest {
    private static final int CODE_CAP = 2_097_152;
    private static final int RESOURCE_CAP = 8_388_608;
    private static final String IMPORT_STOP = "SYNTHETIC_INVENTORY_ACCEPTED_BEFORE_DRIVER";
    @TempDir Path temporary;

    @Test void nonCodeResourceAboveTwoMiBReachesFrozenImportWithoutReadingPersistence() throws Exception {
        JsonNode result = runEntry("xar_autoplayer/data/fixture.bin",CODE_CAP+1,true);
        assertEquals("RuntimeError",result.get("error_type").textValue());
        assertEquals(IMPORT_STOP,result.get("error").textValue());
        assertNoBodyOperation(result);
    }

    @Test void pythonAndStubSourcesAboveTwoMiBAreRejectedByTheActualEntry() throws Exception {
        for (String suffix : List.of(".py",".pyi",".PY",".PYI")) {
            JsonNode result = runEntry("xar_autoplayer/oversize"+suffix,CODE_CAP+1,false);
            assertEquals("ValueError",result.get("error_type").textValue());
            assertEquals("explicit SDK source cap",result.get("error").textValue());
            assertNoBodyOperation(result);
        }
    }

    @Test void nonCodeResourceAboveEightMiBIsRejectedBeforeImportsOrPersistence() throws Exception {
        JsonNode result = runEntry("xar_autoplayer/data/oversize.bin",RESOURCE_CAP+1,false);
        assertEquals("ValueError",result.get("error_type").textValue());
        assertEquals("explicit SDK source cap",result.get("error").textValue());
        assertNoBodyOperation(result);
    }

    private JsonNode runEntry(String relative, int declaredBytes, boolean materializeResource) throws Exception {
        Path work = Files.createTempDirectory(temporary,"inventory-entry-").toAbsolutePath();
        Path sdk = Files.createDirectory(work.resolve("sdk"));
        Path packageRoot = Files.createDirectory(sdk.resolve("xar_autoplayer"));
        var emptyPackage = write(packageRoot.resolve("__init__.py"),new byte[0]);
        var validator = write(packageRoot.resolve("cold_checkpoint_validator.py"),
                ("raise RuntimeError('"+IMPORT_STOP+"')\n").getBytes(java.nio.charset.StandardCharsets.UTF_8));
        ExactRef resource;
        if (materializeResource) {
            Path path = sdk.resolve(relative); Files.createDirectories(path.getParent());
            // Bounded generated fixture, unrelated to the retained original multi-MiB SDK resources.
            resource = write(path,new byte[declaredBytes]);
        } else {
            // Rejected declared sizes must fail before any attempt to open their absent source file.
            resource = new ExactRef(sdk.resolve(relative).toString(),declaredBytes,"0".repeat(64));
        }
        var inventory = StrictJson.object(); inventory.put("machine_id","synthetic-inventory-fixture");
        inventory.put("source_root",sdk.toString()); var files = inventory.putArray("files");
        inventoryItem(files,sdk,emptyPackage); inventoryItem(files,sdk,validator); inventoryItem(files,sdk,resource);
        var freeze = write(work.resolve("freeze.json"),StrictJson.canonical(inventory));
        Path python = python();
        Instant now = Instant.now(), deadline = now.plusSeconds(30);
        var identity = new FileStatIdentity(BigInteger.ONE,"1","1");
        // This ordinary synthetic ticket value is never issued, published as a release, or passed to measureOnce.
        byte[] releaseBytes = StrictJson.canonical(StrictJson.object().put("synthetic_fixture",true));
        var release = new RecoveryEvidence(new ExactRef(work.resolve("NOT-ISSUED.json").toString(),
                releaseBytes.length,RecoveryEvidence.sha256(releaseBytes)),releaseBytes);
        var ticket = new SavedProofReadTicket(release,"synthetic-inventory-fixture","1".repeat(32),
                now.minusSeconds(1),deadline,work.resolve("DO-NOT-EXIST-driver-state.json"),identity,
                new ExactRef(work.resolve("save games/xar_checkpoint.ck3").toString(),1,"0".repeat(64)),identity,
                sdk,freeze,validator,"synthetic-no-pipe",python,work,67_108_864,268_435_456,30);
        Path request = work.resolve("request.json"); Files.write(request,FixedSdkTransport.request(ticket));
        Path stdout = work.resolve("stdout.json"), stderr = work.resolve("stderr.log");
        var command = new WindowsJobProcess.CommandSpec(python,
                List.of("-B","-u","-X","utf8","-c",FixedSdkTransport.PROGRAM,request.toString()),
                work,Map.copyOf(System.getenv()),stdout,stderr,268_435_456);
        try (var job = WindowsJobProcess.start(command)) {
            var terminal = job.await(Duration.ofSeconds(25),deadline,() -> { });
            assertEquals(1,terminal.exitCode(),"fixed worker must stop at its explicit synthetic import or cap rejection; stderr="+stderr);
            assertEquals(0,terminal.accounting().activeProcesses());
            assertFalse(terminal.passed(),"fixture rejection is not successful original SDK qualification");
        }
        byte[] raw;
        try (var input = Files.newInputStream(stdout)) { raw = input.readNBytes(65_537); }
        assertTrue(raw.length > 0 && raw.length <= 65_536);
        JsonNode result = StrictJson.parse(raw);
        assertEquals("xar.original-sdk-current-save-transport-failure/v1",result.get("schema").textValue());
        assertEquals("REJECTED",result.get("status").textValue());
        assertFalse(Files.exists(ticket.driverPath()));
        assertFalse(Files.exists(Path.of(ticket.save().path())));
        return result;
    }

    private static ExactRef write(Path path, byte[] raw) throws IOException {
        Files.write(path,raw); return new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw));
    }

    private static void inventoryItem(ArrayNode files, Path sdk, ExactRef reference) {
        var row = files.addObject(); row.put("relative",sdk.relativize(Path.of(reference.path())).toString().replace('\\','/'));
        row.put("bytes",reference.bytes()); row.put("sha256",reference.sha256());
        row.put("git_blob_sha1","0".repeat(40)); row.put("git_mode","100644");
    }

    private static void assertNoBodyOperation(JsonNode result) {
        for (String counter : List.of("driver_physical_body_reads","driver_physical_read_bytes",
                "original_validator_calls","save_sha256_calls")) {
            assertEquals(0,StrictJson.integer(result.get("counts").get(counter),0,0),counter);
        }
    }

    private static Path python() {
        String value = System.getProperty("xar.python");
        if (value == null || value.isBlank()) { value = System.getenv("XAR_ORACLE_PYTHON"); }
        if (value == null || value.isBlank()) {
            throw new IllegalStateException("UNAVAILABLE: fixed-entry regression requires xar.python or XAR_ORACLE_PYTHON");
        }
        Path path = Path.of(value).toAbsolutePath();
        if (!Files.isRegularFile(path)) { throw new IllegalStateException("UNAVAILABLE: configured Python does not exist"); }
        return path;
    }
}
