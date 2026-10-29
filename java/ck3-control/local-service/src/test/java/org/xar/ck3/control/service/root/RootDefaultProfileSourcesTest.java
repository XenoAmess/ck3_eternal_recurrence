package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;
import java.io.IOException;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.zip.*;
import java.security.MessageDigest;
import com.fasterxml.jackson.databind.node.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionConfigurationAssembler.*;

/** Source-only role resolution and existing genuine pre-Core fixtures; no manufactured Inputs or admission. */
final class RootDefaultProfileSourcesTest {
    @TempDir Path temporary;
    @Test void actualExportedIndexFeedsDefaultProfileClosuresCodecAndOriginalConsumer()throws Exception {
        exercise(false);
    }
    @Test void actualExportedRestoreRolesFeedDefaultProducerCodecAndSameConsumer()throws Exception {
        exercise(true);
    }
    /** Software-only source custody regression; no Inputs, Native plan or admission is constructed. */
    @Test void driverBootstrapRoleResolvesOnlyItsLocalServiceOriginal()throws Exception {
        var required=RootRestoreRuntimeSources.requiredSources().stream()
                .filter(row->row.role()==RootRestoreRuntimeSources.Role.DRIVER_BOOTSTRAP).findFirst().orElseThrow();
        var type=org.xar.ck3.control.application.driver.DriverBootstrap.class;
        String suffix="src/main/java/"+type.getName().replace('.','/')+".java";
        Path source=temporary.resolve("DriverBootstrap.java");
        Files.writeString(source,"package org.xar.ck3.control.application.driver; public final class DriverBootstrap {}\n");
        var measured=ControlBuild.FileRef.measure(source);
        var original=new org.xar.ck3.control.contracts.ExactRef(measured.path(),measured.bytes(),measured.sha256());
        var selected=new RootRuntimeSelectedSources(List.of(new SelectedSource("local-service/"+suffix,original)));
        assertEquals(type,required.type());
        assertEquals(original,selected.javaSource(required.module(),required.type()));
        assertThrows(IOException.class,()->selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,required.type()));
        var wrongModule=new RootRuntimeSelectedSources(List.of(new SelectedSource("application/"+suffix,original)));
        assertThrows(IOException.class,()->wrongModule.javaSource(required.module(),required.type()));
    }
    private void exercise(boolean restoration)throws Exception {
        var fixture=RootDriverProductSourcesFactoryTest.actual();
        var c=fixture.definitions().inputs().configuration();
        var clock=Clock.systemUTC();var index=c.sourceIndex();
        RootRuntimeDefinitions.sourceIndexOriginalInput(index).verify();
        var winners=RootRuntimeDefinitions.readSourceIndex(index,c.machineId(),clock);
        var domains=new DeclaredDomainInputs(c.governance(),c.finance(),c.army(),c.prisoners(),c.family(),c.frontend(),
                c.interactions(),c.activity(),c.crossRun(),c.incidents(),c.publicCatalog(),c.startup());
        var required=new LinkedHashSet<SelectedSource>();
        if(restoration)for(var row:RootRestoreRuntimeSources.requiredSources()) {
            String target=row.module().directory()+"/src/main/java/"+row.type().getNestHost().getName().replace('.','/')+".java";
            required.add(winners.stream().filter(source->source.targetRelative().equals(target)).findFirst().orElseThrow());
        } else for(var type:RootRuntimeConfigurationSources.requiredProfileSourceTypes().stream().map(type->type.getNestHost()).distinct().toList()) {
            String suffix="/src/main/java/"+type.getName().replace('.','/')+".java";
            required.add(winners.stream().filter(row->row.targetRelative().endsWith(suffix)).findFirst().orElseThrow());
        }
        var made=RootRuntimeDefinitionConfigurationAssembler.productionConfiguration(physical(c,index,required),domains,c.machineId(),
                clock.instant(),clock.instant().plusSeconds(600),clock);
        byte[] bytes=RootRuntimeDefinitions.encodeConfiguration(made);
        var decoded=RootRuntimeDefinitions.decodeConfiguration(bytes);assertEquals(made,decoded);
        ObjectNode graph;
        try(var in=new GZIPInputStream(Files.newInputStream(Path.of(index.compressedRef().path())))) {
            graph=(ObjectNode)ControlBuild.strictMapper().readTree(in);
        }
        if(restoration) {
            var selected=new RootRuntimeSelectedSources(winners);
            var plan=fixture.definitions().nativeLaunchPlan();
            RootRestoreRuntimeSources.capture(selected,plan).requireCurrent(selected,plan);
        }
        for(var expected:required) {
            assertTrue(decoded.closure(ClosureRole.STARTUP).contains(expected.sourceRef()));
            RootSavedNativeCoordinator.requireConfiguredSource(decoded,expected.sourceRef());
            var ref=expected.sourceRef();
            assertThrows(IOException.class,()->RootSavedNativeCoordinator.requireConfiguredSource(decoded,
                    new org.xar.ck3.control.contracts.ExactRef(ref.path(),ref.bytes(),"0".repeat(64))));
            var missing=graph.deepCopy();var rows=(ArrayNode)missing.get("selected_files");
            for(int at=rows.size()-1;at>=0;at--)if(expected.targetRelative().equals(rows.get(at).get("target_relative").textValue()))rows.remove(at);
            byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(missing);Path path=temporary.resolve(Path.of(expected.targetRelative()).getFileName()+".gz");
            try(var out=new GZIPOutputStream(Files.newOutputStream(path))){out.write(raw);}
            var absent=new SourceIndex(ControlBuild.FileRef.measure(path),raw.length,
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
            assertThrows(IOException.class,()->RootRuntimeDefinitionConfigurationAssembler.productionConfiguration(
                    physical(c,absent,required),domains,c.machineId(),clock.instant(),clock.instant().plusSeconds(600),clock));
        }
    }
    private static PhysicalOriginals physical(Configuration c,SourceIndex index,Set<SelectedSource> required) {
        var targets=required.stream().map(SelectedSource::targetRelative).collect(java.util.stream.Collectors.toSet());
        var closures=c.closures().stream().map(row->row.role()==ClosureRole.STARTUP
                ?new ProducerClosure(row.role(),row.sources().stream().filter(source->!targets.contains(source.targetRelative())).toList()):row).toList();
        return new PhysicalOriginals(c.applicationRef(),c.storageLeaseRef(),c.nativeLaunchPlanRef(),c.runtimePackageRequestRef(),
                index,c.sources(),closures,c.originalData());
    }
}
