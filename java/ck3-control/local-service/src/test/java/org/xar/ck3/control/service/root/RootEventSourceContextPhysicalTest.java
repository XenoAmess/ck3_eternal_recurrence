package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Base64;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Actual native temporary-file custody and real context publisher -> Definitions DATA reader.
 * The finite issuer card is an explicit software fixture, never production capacity or Game authority. */
final class RootEventSourceContextPhysicalTest {
    @TempDir Path directory;
    private static final Instant NOW=Instant.parse("2026-10-24T01:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private record Sources(Path state,Path stock,FileRef manifest) { }

    @Test void actualEmptyPublisherAndGuardedContextOriginalReachTheDefinitionsReaderWithoutHistoricalGrants()throws Exception {
        Sources sources=sourceFixture();Path asset=Files.createDirectory(directory.resolve("asset"));
        Path target=asset.resolve("event-context.json");
        var quote=RootEventSourceContextProducer.prepare(request(sources,target,RootJavaBootstrapInputs.Mode.QUOTE,null),CLOCK);
        assertEquals(0,ProjectionEvidenceCodec.decode(Files.readAllBytes(Path.of(sources.manifest().path()))).size());
        assertFalse(Files.exists(target));FileRef binding=binding(asset,quote.quote().getFirst());
        var actual=RootEventSourceContextProducer.prepare(request(sources,target,RootJavaBootstrapInputs.Mode.CREATE_NEW,binding),CLOCK);
        var created=actual.createNew(CLOCK);
        assertEquals(actual.expected(),created.original());
        var nativeOriginal=SharedSourceFiles.observe(target);
        assertEquals(nativeOriginal.source(),created.original());assertEquals(nativeOriginal.nativeFile(),created.nativeFile());
        var pin=new RootRuntimeDefinitionModel.DataPin(RootRuntimeDefinitionModel.DataRole.TRUSTED_EVENT_SOURCE_CONTEXT,created.original());
        byte[] retained=RootRuntimeDefinitions.readData(pin);
        assertArrayEquals(actual.bytes(),retained);
        var decoded=RootRuntimeDefinitions.decodeEventSources(retained);
        assertEquals(WindowsJobProcess.currentMachineId(),decoded.machineId());
        assertEquals(sources.state(),decoded.stateRoot());assertEquals(sources.stock(),decoded.stockGameRoot());
        assertEquals(List.of(),decoded.evidenceGrants());
        assertArrayEquals(retained,RootRuntimeDefinitions.encodeEventSources(decoded));
        assertThrows(IOException.class,()->actual.createNew(CLOCK));
        Files.writeString(target,"{\"changed_actual_context\":true}\n");
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readData(pin));
    }

    private RootEventSourceContextProducer.Request request(Sources sources,Path target,RootJavaBootstrapInputs.Mode mode,FileRef binding) {
        return new RootEventSourceContextProducer.Request(RootEventSourceContextProducer.SCHEMA,WindowsJobProcess.currentMachineId(),
                NOW.minusSeconds(1).toString(),NOW.plusSeconds(3600).toString(),mode,binding,
                sources.state().toString(),sources.stock().toString(),sources.manifest(),target.toString().replace('\\','/'));
    }

    private Sources sourceFixture()throws Exception {
        Path state=Files.createDirectory(directory.resolve("state")),stock=Files.createDirectory(directory.resolve("stock"));
        byte[] packed;
        try(var input=getClass().getResourceAsStream("/offlineinteraction/offline-stock-inputs.json.gz")) {
            assertNotNull(input,"mandatory original stock fixture");packed=input.readNBytes(131073);
        }
        assertTrue(packed.length<=131072);
        assertEquals("5a6318535c9fc6448149b2e573f4246e1e9697fb9996eded77d86d90ba638918",DriverJson.sha256(packed));
        com.fasterxml.jackson.databind.JsonNode corpus;
        try(var input=new GZIPInputStream(new ByteArrayInputStream(packed))) {
            byte[] raw=input.readNBytes(1_048_577);assertTrue(raw.length<=1_048_576);corpus=StrictJson.parse(raw,1_048_576);
        }
        assertEquals("xar.offline-interaction-source-test-inputs/v1",corpus.path("schema").textValue());
        assertEquals(7,corpus.path("files").size());
        for(var file:corpus.path("files")) {
            String relative=file.path("relative").textValue();Path output=stock.resolve(relative).normalize();
            assertFalse(Path.of(relative).isAbsolute());assertTrue(output.startsWith(stock));byte[] raw;
            try(var input=new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(file.path("gzip_base64").textValue())))) {
                raw=input.readNBytes(2_097_153);assertTrue(raw.length<=2_097_152);
            }
            assertEquals(file.path("bytes").longValue(),raw.length);assertEquals(file.path("sha256").textValue(),DriverJson.sha256(raw));
            Files.createDirectories(output.getParent());Files.write(output,raw);
        }
        Path manifest=state.resolve("evidence/actual-empty-grants.json");Files.createDirectories(manifest.getParent());
        var publication=EvidenceGrantManifestPublisher.publish(manifest,List.of());assertEquals(0,publication.grants());
        var original=SharedSourceFiles.observe(manifest);
        assertEquals(publication.bytes(),original.source().bytes());assertEquals(publication.sha256(),original.source().sha256());
        return new Sources(state,stock,original.source());
    }

    private FileRef binding(Path asset,Output output)throws IOException {
        Path control=Files.createDirectory(directory.resolve("control"));String machine=WindowsJobProcess.currentMachineId();
        String observed=NOW.minusSeconds(1).toString(),review=NOW.plusSeconds(3600).toString();
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root","event-context-physical-software-fixture",observed,review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),
                1536L*1024,512L*1024,1<<20,64,List.of(output),List.of(),List.of());
        FileRef declarationRef=write(control.resolve("declaration.json"),encode(declaration));
        FileRef censusRef=write(control.resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declarationRef,CLOCK)));
        var policy=StrictJson.object().put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);rules.put("default_project_quota_ceiling_bytes",100L<<30);
        rules.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));rules.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume=asset.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object().put("scope","software-fixture-actual-volume-observation").put("machine_id",machine)
                .put("total_bytes",total).put("usable_bytes",free).put("old_workpackage_actual_is_unknown",true);
        FileRef head=write(control.resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null,Math.subtractExact(total,free),head);
        var release=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,"event-context-physical-software-fixture",NOW.toString(),review,
                policyRef,declarationRef,censusRef,head,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef capacity=write(control.resolve("capacity.json"),encode(release));
        return write(control.resolve("binding.json"),encode(new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,
                "event-context-physical-software-fixture",NOW.toString(),review,declarationRef,censusRef,capacity)));
    }
    private static FileRef write(Path target,byte[] bytes)throws IOException {Files.write(target,bytes);return SharedSourceFiles.observe(target).source();}
}
