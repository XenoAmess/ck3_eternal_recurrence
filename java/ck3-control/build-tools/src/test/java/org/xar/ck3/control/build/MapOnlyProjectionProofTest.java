package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.util.jar.*;
import org.junit.jupiter.api.io.TempDir;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;

final class MapOnlyProjectionProofTest {
    private static final String MACHINE = "declared-software-map-fixture";
    private static final String ARTIFACT = Path.of(System.getProperty("java.io.tmpdir")).resolve("map-fixture.jar").toAbsolutePath().toString();
    private static final ProjectionDeploymentProof.OperationProfile MAP =
            new ProjectionDeploymentProof.OperationProfile(MapOnlyProjectionProof.OPERATION,65536,16384);
    private static ProjectionDeploymentProof.Identity identity() {
        return new ProjectionDeploymentProof.Identity("xar.projection-host-identity/v1",ProjectionDeploymentProof.PRODUCER,
                ProjectionDeploymentProof.VERSION,ProjectionDeploymentProof.CALL_SCHEMA,ProjectionDeploymentProof.RESULT_SCHEMA,
                ProjectionDeploymentProof.MAX_ENVELOPE_BYTES,List.of(MAP));
    }
    private static MapOnlyProjectionProof.Inventory inventory(List<MapOnlyProjectionProof.CatalogRow> rows) {
        return new MapOnlyProjectionProof.Inventory("xar.projection-host-catalogs/v1",MACHINE,Instant.now().toString(),rows);
    }
    private static MapOnlyProjectionProof.CatalogRow map() {
        return new MapOnlyProjectionProof.CatalogRow(MapOnlyProjectionProof.PROVIDER,ARTIFACT,List.of(MAP));
    }
    @Test void mapObservationAllowsUnavailableUnrelatedCatalogWithoutWeakeningFullContract() throws IOException {
        var unrelated = new MapOnlyProjectionProof.CatalogRow("fixture.UnavailableCatalog",ARTIFACT,List.of());
        assertEquals(map(),MapOnlyProjectionProof.selected(identity(),inventory(List.of(unrelated,map())),MACHINE));
        assertThrows(IllegalArgumentException.class,()->new ProjectionDeploymentProof.CatalogIdentity("fixture.UnavailableCatalog",ARTIFACT,List.of()));
    }
    @Test void mapProfileOwnerAndMachineMustRemainUnique() {
        var alias = new MapOnlyProjectionProof.CatalogRow("fixture.Alias",ARTIFACT,List.of(MAP));
        assertThrows(IOException.class,()->MapOnlyProjectionProof.selected(identity(),inventory(List.of(map(),alias)),MACHINE));
        assertThrows(IOException.class,()->MapOnlyProjectionProof.selected(identity(),inventory(List.of(map())),"other-machine"));
        var changed = new MapOnlyProjectionProof.CatalogRow(MapOnlyProjectionProof.PROVIDER,ARTIFACT,
                List.of(new ProjectionDeploymentProof.OperationProfile(MapOnlyProjectionProof.OPERATION,65536,65536)));
        assertThrows(IOException.class,()->MapOnlyProjectionProof.selected(identity(),inventory(List.of(changed)),MACHINE));
    }
    @Test void actualTypedWireRoundTripAndWrongNumericTokens() throws IOException {
        var original=inventory(List.of(map())); var mapper=ControlBuild.strictMapper();
        String raw=mapper.writeValueAsString(original);
        assertEquals(original,mapper.readValue(raw,MapOnlyProjectionProof.Inventory.class));
        for(String value:List.of("true","65536.0","null","\"65536\""))
            assertThrows(IOException.class,()->mapper.readValue(raw.replace("\"input_max_bytes\":65536","\"input_max_bytes\":"+value),MapOnlyProjectionProof.Inventory.class));
        assertThrows(IOException.class,()->mapper.readValue(raw.replace("\"output_max_bytes\":16384","\"unknown\":16384"),MapOnlyProjectionProof.Inventory.class));
    }
    @Test void mapOnlyEntryCannotInstallEventSourceAuthority() {
        Path root=Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath();
        var config=new MapAdmissionServiceOwner.Config(root.resolve("receipt.json"),root.resolve("owner"),root.resolve("java.exe"),
                Instant.now().plusSeconds(60),24891,root.resolve("events"),root.resolve("stock"));
        assertThrows(IllegalArgumentException.class,()->MapAdmissionServiceOwner.startMapOnlyCapture(config,root.resolve("scope.json")));
    }
    @Test void fastJarWithoutMavenEntriesUsesCapturedPomsAndManifest(@TempDir Path root) throws IOException {
        String project="<project xmlns=\"http://maven.apache.org/POM/4.0.0\">";
        String parent="<groupId>org.xar.ck3.control</groupId><artifactId>ck3-control-parent</artifactId><version>0.1.0-SNAPSHOT</version>";
        Path pom=root.resolve("pom.xml"), module=Files.createDirectory(root.resolve("local-service")).resolve("pom.xml");
        Files.writeString(pom,project+parent+"</project>");
        Files.writeString(module,project+"<parent>"+parent+"<relativePath>../pom.xml</relativePath></parent><artifactId>ck3-control-local-service</artifactId></project>");
        var coordinates=MapOnlyProjectionProof.moduleCoordinates(ControlBuild.FileRef.measure(module),ControlBuild.FileRef.measure(pom));
        Path jar=root.resolve("map.jar"); fixtureJar(jar,"0.1.0-SNAPSHOT",true,true);
        assertArrayEquals("fixture\n".getBytes(StandardCharsets.UTF_8),MapOnlyProjectionProof.mapJar(jar,coordinates,MapOnlyProjectionProofTest.class.getName()));
        try(var read=new JarFile(jar.toFile())) { assertFalse(read.stream().anyMatch(e->e.getName().startsWith("META-INF/maven/"))); }
        fixtureJar(jar,"wrong",true,true);
        assertThrows(IOException.class,()->MapOnlyProjectionProof.mapJar(jar,coordinates,MapOnlyProjectionProofTest.class.getName()));
        fixtureJar(jar,"0.1.0-SNAPSHOT",false,true);
        assertThrows(IOException.class,()->MapOnlyProjectionProof.mapJar(jar,coordinates,MapOnlyProjectionProofTest.class.getName()));
        fixtureJar(jar,"0.1.0-SNAPSHOT",true,false);
        assertThrows(IOException.class,()->MapOnlyProjectionProof.mapJar(jar,coordinates,MapOnlyProjectionProofTest.class.getName()));
        Files.writeString(module,Files.readString(module).replace("org.xar.ck3.control","wrong.group"));
        assertThrows(IOException.class,()->MapOnlyProjectionProof.moduleCoordinates(ControlBuild.FileRef.measure(module),ControlBuild.FileRef.measure(pom)));
    }
    private static void fixtureJar(Path jar,String version,boolean provider,boolean descriptor) throws IOException {
        var manifest=new Manifest(); var attrs=manifest.getMainAttributes();
        attrs.putValue("Manifest-Version","1.0"); attrs.putValue("Implementation-Title","ck3-control-local-service"); attrs.putValue("Implementation-Version",version);
        try(var out=new JarOutputStream(Files.newOutputStream(jar),manifest)) {
            if(provider) {
                String name=MapOnlyProjectionProofTest.class.getName().replace('.','/')+".class";
                out.putNextEntry(new JarEntry(name));
                try(var in=MapOnlyProjectionProofTest.class.getResourceAsStream("/"+name)) { if(in==null) throw new IOException("Actual compiled test class absent"); in.transferTo(out); }
                out.closeEntry();
            }
            if(descriptor) {
                out.putNextEntry(new JarEntry(ProjectionDeploymentProof.SERVICE_ENTRY));
                out.write("fixture\n".getBytes(StandardCharsets.UTF_8)); out.closeEntry();
            }
        }
    }

}

