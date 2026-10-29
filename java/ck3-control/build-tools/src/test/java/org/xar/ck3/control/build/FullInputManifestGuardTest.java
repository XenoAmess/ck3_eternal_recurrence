package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Locale;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.junit.jupiter.api.Assertions.*;

/** Real shared producer/consumer regressions; no replacement process lifecycle. */
@org.junit.jupiter.api.parallel.Isolated("owned temporary properties used by the actual version2 software regression")
final class FullInputManifestGuardTest {
    @TempDir Path temporary;

    private FileRef request(String mode) throws Exception {
        var mapper=ControlBuild.strictMapper();
        Path executable=Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toAbsolutePath().normalize();
        FileRef java=FileRef.measure(executable);
        ObjectNode manifest=mapper.createObjectNode();manifest.put("schema","xar.full-input-files/v1");
        manifest.put("machine_id",WindowsJobProcess.currentMachineId());manifest.put("observed_at_utc","2026-10-23T00:00:00Z");
        JsonNode original=mapper.valueToTree(java);ObjectNode declared=original.deepCopy();
        if(mode.equals("boolean"))declared.put("bytes",true);
        manifest.putArray("files").add(declared);
        Path manifestFile=temporary.resolve(mode+"-manifest.json");Files.write(manifestFile,mapper.writeValueAsBytes(manifest),StandardOpenOption.CREATE_NEW);
        Path output=temporary.resolve(mode+"-output");Files.createDirectory(output);
        ObjectNode config=mapper.createObjectNode();config.put("schema","xar.full-input-manifest-guard-request/v1");
        config.put("machine_id",WindowsJobProcess.currentMachineId());config.set("manifest_ref",mapper.valueToTree(FileRef.measure(manifestFile)));
        config.put("manifest_schema","xar.full-input-files/v1");config.put("output_root",output.toString());
        ObjectNode alias=original.deepCopy();alias.put("path",java.path().toUpperCase(Locale.ROOT));
        assertNotEquals(java.path(),alias.path("path").textValue(),"test must use a distinct Windows spelling");
        if(mode.equals("conflict"))alias.put("sha256","0".repeat(64));
        config.putArray("additional_inputs").add(alias);
        ObjectNode command=config.putObject("command");command.set("executable",original);
        var arguments=command.putArray("arguments");for(String argument:List.of("-Xms16m","-Xmx32m","-XX:+UseSerialGC","-XX:ActiveProcessorCount=2","-XX:MaxMetaspaceSize=64m","-XX:ReservedCodeCacheSize=16m","-XX:MaxDirectMemorySize=8m","-Xss256k","-version"))arguments.add(argument);
        command.put("cwd",temporary.toString());command.putObject("environment");command.put("memory_limit_bytes",192L<<20);command.put("timeout_seconds",10);
        Path requestFile=temporary.resolve(mode+"-request.json");Files.write(requestFile,mapper.writeValueAsBytes(config),StandardOpenOption.CREATE_NEW);
        return FileRef.measure(requestFile);
    }

    @Test void caseAliasIsVerifiedAsTheSameNativeFileAndBothPathsRemainGuarded() throws Exception {
        var terminal=FullInputManifestGuard.execute(request("alias"));
        assertEquals(FullInputManifestGuard.State.PASS,terminal.status(),terminal.error());
        assertTrue(terminal.childStarted());assertEquals(0,terminal.child().exitCode());assertEquals(0,terminal.child().accounting().activeProcesses());
        assertEquals(terminal.guardedFiles(),terminal.verifiedBefore());assertEquals(terminal.guardedFiles(),terminal.verifiedAfter());
        JsonNode snapshot;
        try(var input=new GZIPInputStream(Files.newInputStream(Path.of(terminal.snapshotRef().path())))) {snapshot=ControlBuild.strictMapper().readTree(input);}
        JsonNode witnesses=snapshot.path("witnesses");assertEquals(4,witnesses.size());
        assertNotEquals(witnesses.get(2).path("source").path("path"),witnesses.get(3).path("source").path("path"));
        assertEquals(witnesses.get(2).path("native_file"),witnesses.get(3).path("native_file"));
        assertTrue(witnesses.get(2).path("native_file").path("file_id_decimal").isTextual());
    }

    @Test void samePathAliasWithConflictingDigestRejectsBeforeChild() throws Exception {
        var terminal=FullInputManifestGuard.execute(request("conflict"));
        assertEquals(FullInputManifestGuard.State.REJECTED,terminal.status());assertFalse(terminal.childStarted());assertNull(terminal.child());
        assertTrue(terminal.error().contains("conflicting duplicate input"));
    }

    @Test void booleanManifestBytesRejectsBeforeChild() throws Exception {
        var terminal=FullInputManifestGuard.execute(request("boolean"));
        assertEquals(FullInputManifestGuard.State.REJECTED,terminal.status());assertFalse(terminal.childStarted());assertNull(terminal.child());
        assertTrue(terminal.error().contains("integer required: bytes"));
    }
    @Test void version2ActualOwnedChildAndAllBoundaryCasesUseTheSameProducer() throws Exception {
        var actual=FullInputManifestGuardV2Regression.run(temporary.resolve("version2-cases"));
        assertEquals(6,actual.cases().size());
        assertTrue(actual.cases().stream().allMatch(value->value.outcome().equals("PASS")));
        assertEquals("OWNED_SOFTWARE_FIXTURE_DATA_NOT_FINANCIAL_RELEASE_NOT_NATIVE_BUILD_READY",actual.scope());
    }
}

