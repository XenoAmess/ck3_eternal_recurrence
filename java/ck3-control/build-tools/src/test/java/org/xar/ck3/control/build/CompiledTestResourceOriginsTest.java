package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real compiler/resource copies test the inventory boundary, never a fake accepted receipt. */
final class CompiledTestResourceOriginsTest {
    @TempDir Path temporary;
    private record Fixture(Path snapshot, Path module, Path output, Path pom, Path source, Path resource,
            List<ControlBuild.FileRef> pins, ControlBuild.TestCompilationManifest manifest,
            CompiledOriginalCaptureProfile.Selection selection) { }
    private Fixture fixture(String declaration, boolean imported) throws Exception {
        Path snapshot = temporary.resolve("snapshot"), module = snapshot.resolve("module"), output = module.resolve("test-classes");
        Files.createDirectories(output);
        Path source = module.resolve("src/test/java/fixture/CaptureFixture.java"); Files.createDirectories(source.getParent());
        Files.writeString(source, "package fixture; public final class CaptureFixture {"
                + "public static String source(){return \"ORIGINAL\";} public static void main(String[] args){} }");
        var compiler = ToolProvider.getSystemJavaCompiler(); var errors = new ByteArrayOutputStream();
        assertEquals(0, compiler.run(null, errors, errors, "--release", "21", "-Xlint:all", "-Werror", "-d", output.toString(), source.toString()),
                errors.toString(StandardCharsets.UTF_8));
        Path pom = module.resolve("pom.xml"); Files.writeString(pom, "<project xmlns=\"http://maven.apache.org/POM/4.0.0\">" + declaration + "</project>");
        Path resource = (imported ? snapshot.resolve("g2-research") : module).resolve("src/test/resources/m4producer/wartime-original02.json.gz");
        Files.createDirectories(resource.getParent()); Files.writeString(resource, "original producer bytes");
        Path copied = output.resolve("m4producer/wartime-original02.json.gz"); Files.createDirectories(copied.getParent()); Files.copy(resource, copied);
        Path inputs = module.resolve("inputs.lst"), created = module.resolve("created.lst");
        Files.writeString(inputs, source.toString()); Files.writeString(created, "fixture/CaptureFixture.class\n");
        var sourceRef = ControlBuild.FileRef.measure(source); var pomRef = ControlBuild.FileRef.measure(pom);
        var manifest = new ControlBuild.TestCompilationManifest(ControlBuild.TEST_COMPILATION_SCHEMA, "unit-machine", Instant.now().toString(),
                ControlBuild.CaptureTestState.NOT_RUN, List.of(new ControlBuild.ModuleTestCompilation(pomRef, output.toString(),
                        ControlBuild.FileRef.measure(inputs), ControlBuild.FileRef.measure(created))),
                List.of(new ControlBuild.NotRunTestCompilation(sourceRef, List.of(ControlBuild.FileRef.measure(output.resolve("fixture/CaptureFixture.class"))),
                        ControlBuild.CaptureTestState.NOT_RUN)));
        return new Fixture(snapshot, module, output, pom, source, resource,
                List.of(pomRef, sourceRef, ControlBuild.FileRef.measure(resource)), manifest,
                new CompiledOriginalCaptureProfile.Selection("fixture.CaptureFixture", sourceRef, List.of(pomRef), List.of()));
    }
    private static String resource(String directory, String extra) {
        return "<build><testResources><testResource><directory>" + directory + "</directory>" + extra + "</testResource></testResources></build>";
    }
    private CompiledOriginalCaptureProfile.Inventory inventory(Fixture f) throws IOException {
        return CompiledOriginalCaptureProfile.inventory(f.snapshot(), f.pins(), f.manifest(), f.selection());
    }
    private CompiledTestResourceOrigins.Plan plan(Fixture f) throws IOException {
        return CompiledTestResourceOrigins.read(f.snapshot(), ControlBuild.FileRef.measure(f.pom()), f.pins());
    }
    private static Path copied(Fixture f) { return f.output().resolve("m4producer/wartime-original02.json.gz"); }

    @Test void actualCompilerImportedCopyAndInventoryWireCloseTheLoop() throws Exception {
        var f = fixture(resource("../g2-research/src/test/resources", "<includes><include>m4producer/wartime-original02.json.gz</include></includes>"), true);
        var result = inventory(f);
        assertEquals(List.of(ControlBuild.FileRef.measure(copied(f))), result.runtimeResources());
        assertTrue(result.compiledSources().contains(ControlBuild.FileRef.measure(f.resource())));
        assertEquals(1, result.runtimeClasses().size());
        var mapper = ControlBuild.strictMapper();
        assertEquals(result, mapper.readValue(mapper.writeValueAsBytes(result), CompiledOriginalCaptureProfile.Inventory.class));
        assertFalse(Files.exists(f.module().resolve("src/test/resources/m4producer/wartime-original02.json.gz")));
    }
    @Test void defaultOwnResourcesRemainExact() throws Exception {
        var f = fixture("", false); var result = inventory(f);
        assertEquals(ControlBuild.FileRef.measure(f.resource()), plan(f).attest(f.output(), copied(f)).sourceRef());
        assertEquals(1, result.runtimeResources().size());
        for (String name : List.of("backup.txt~", ".gitignore")) {
            Path source = f.module().resolve("src/test/resources").resolve(name); Files.writeString(source, "identical bytes");
            Path output = f.output().resolve(name); Files.copy(source, output);
            var pins = new ArrayList<>(f.pins()); pins.add(ControlBuild.FileRef.measure(source));
            var p = CompiledTestResourceOrigins.read(f.snapshot(), ControlBuild.FileRef.measure(f.pom()), pins);
            assertThrows(IOException.class, () -> p.attest(f.output(), output));
        }
    }
    @Test void capturedBasedirAndParentPomAreVerified() throws Exception {
        String parent = "<parent><groupId>fixture</groupId><artifactId>parent</artifactId><version>1</version></parent>";
        var f = fixture(parent + resource("${project.basedir}/../g2-research/src/test/resources", ""), true);
        Path parentPom = f.snapshot().resolve("pom.xml"); Files.writeString(parentPom, "<project/>");
        var pins = new ArrayList<>(f.pins()); pins.add(ControlBuild.FileRef.measure(parentPom));
        var result = CompiledTestResourceOrigins.read(f.snapshot(), ControlBuild.FileRef.measure(f.pom()), pins);
        assertEquals(ControlBuild.FileRef.measure(f.resource()), result.attest(f.output(), copied(f)).sourceRef());
        Files.writeString(parentPom, "<project><build/></project>");
        assertThrows(IOException.class, () -> CompiledTestResourceOrigins.read(f.snapshot(), ControlBuild.FileRef.measure(f.pom()), pins));
    }
    @Test void antIncludesExcludesAndTargetPathMatchActualRelativeNames() throws Exception {
        var f = fixture(resource("../g2-research/src/test/resources",
                "<targetPath>prefixed</targetPath><includes><include>**/*.gz</include></includes><excludes><exclude>**/blocked?.gz</exclude></excludes>"), true);
        Path moved = f.output().resolve("prefixed/m4producer/wartime-original02.json.gz"); Files.createDirectories(moved.getParent()); Files.move(copied(f), moved);
        assertEquals(ControlBuild.FileRef.measure(f.resource()), plan(f).attest(f.output(), moved).sourceRef());
        Path blocked = f.resource().getParent().resolve("blocked1.gz"); Files.copy(f.resource(), blocked);
        var pins = new ArrayList<>(f.pins()); pins.add(ControlBuild.FileRef.measure(blocked));
        Path blockedCopy = moved.getParent().resolve("blocked1.gz"); Files.copy(blocked, blockedCopy);
        var p = CompiledTestResourceOrigins.read(f.snapshot(), ControlBuild.FileRef.measure(f.pom()), pins);
        assertThrows(IOException.class, () -> p.attest(f.output(), blockedCopy));
        Path rootResource = f.snapshot().resolve("g2-research/src/test/resources/root.gz"); Files.copy(f.resource(), rootResource);
        pins.add(ControlBuild.FileRef.measure(rootResource)); Path rootCopy = f.output().resolve("prefixed/root.gz"); Files.copy(rootResource, rootCopy);
        assertEquals(ControlBuild.FileRef.measure(rootResource), CompiledTestResourceOrigins.read(f.snapshot(), ControlBuild.FileRef.measure(f.pom()), pins)
                .attest(f.output(), rootCopy).sourceRef());
    }
    @Test void escapedDirectoriesAndTargetsAreRejected() throws Exception {
        var f = fixture(resource("../../outside", ""), true);
        assertThrows(IOException.class, () -> plan(f));
        Files.writeString(f.pom(), "<project>" + resource("../g2-research/src/test/resources", "<targetPath>../escape</targetPath>") + "</project>");
        var pins = new ArrayList<>(f.pins()); pins.set(0, ControlBuild.FileRef.measure(f.pom()));
        assertThrows(IOException.class, () -> CompiledTestResourceOrigins.read(f.snapshot(), pins.getFirst(), pins));
    }
    @Test void unresolvedPropertiesAndFilteringCannotMasqueradeAsCopies() throws Exception {
        var f = fixture(resource("${unknown}/resources", ""), true);
        assertThrows(IOException.class, () -> plan(f));
        Files.writeString(f.pom(), "<project>" + resource("../g2-research/src/test/resources", "<filtering>true</filtering>") + "</project>");
        var pins = new ArrayList<>(f.pins()); pins.set(0, ControlBuild.FileRef.measure(f.pom()));
        assertThrows(IOException.class, () -> CompiledTestResourceOrigins.read(f.snapshot(), pins.getFirst(), pins));
    }
    @Test void twoDeclaredIdenticalByteOriginsAreAmbiguous() throws Exception {
        String declarations = "<build><testResources><testResource><directory>src/test/resources</directory></testResource>"
                + "<testResource><directory>../g2-research/src/test/resources</directory></testResource></testResources></build>";
        var f = fixture(declarations, true);
        Path own = f.module().resolve("src/test/resources/m4producer/wartime-original02.json.gz"); Files.createDirectories(own.getParent()); Files.copy(f.resource(), own);
        var pins = new ArrayList<>(f.pins()); pins.add(ControlBuild.FileRef.measure(own));
        var p = CompiledTestResourceOrigins.read(f.snapshot(), ControlBuild.FileRef.measure(f.pom()), pins);
        assertThrows(IOException.class, () -> p.attest(f.output(), copied(f)));
    }
    @Test void undeclaredImportAndMissingPinKeepOriginalFailure() throws Exception {
        var f = fixture("", true);
        assertThrows(IOException.class, () -> inventory(f));
        Files.writeString(f.pom(), "<project>" + resource("../g2-research/src/test/resources", "") + "</project>");
        var pins = List.of(ControlBuild.FileRef.measure(f.pom()), ControlBuild.FileRef.measure(f.source()));
        var p = CompiledTestResourceOrigins.read(f.snapshot(), pins.getFirst(), pins);
        assertThrows(IOException.class, () -> p.attest(f.output(), copied(f)));
    }
    @Test void copiedOutputDriftFailsActualInventory() throws Exception {
        var f = fixture(resource("../g2-research/src/test/resources", ""), true);
        Files.writeString(copied(f), "changed output");
        assertThrows(IOException.class, () -> inventory(f));
    }
    @Test void pinnedOriginalAndPomDriftAreRejected() throws Exception {
        var f = fixture(resource("../g2-research/src/test/resources", ""), true);
        var p = plan(f); Files.writeString(f.resource(), "changed original");
        assertThrows(IOException.class, () -> p.attest(f.output(), copied(f)));
        Files.writeString(f.pom(), "<project/>");
        assertThrows(IOException.class, () -> plan(f));
    }
    @Test void dtdEntitiesAndRepeatedResourceFieldsAreRejected() throws Exception {
        var f = fixture("", true);
        Files.writeString(f.pom(), "<!DOCTYPE project [<!ENTITY secret SYSTEM \"file:///not-read\">]><project>&secret;</project>");
        var pins = List.of(ControlBuild.FileRef.measure(f.pom()), ControlBuild.FileRef.measure(f.source()));
        assertThrows(IOException.class, () -> CompiledTestResourceOrigins.read(f.snapshot(), pins.getFirst(), pins));
        Files.writeString(f.pom(), "<project><build><testResources/><testResources/></build></project>");
        var updated = List.of(ControlBuild.FileRef.measure(f.pom()), ControlBuild.FileRef.measure(f.source()));
        assertThrows(IOException.class, () -> CompiledTestResourceOrigins.read(f.snapshot(), updated.getFirst(), updated));
        for (String shape : List.of("<includes/>", "<includes><include><nested>**</nested></include></includes>")) {
            Files.writeString(f.pom(), "<project>" + resource("../g2-research/src/test/resources", shape) + "</project>");
            var malformed = List.of(ControlBuild.FileRef.measure(f.pom()), ControlBuild.FileRef.measure(f.source()));
            assertThrows(IOException.class, () -> CompiledTestResourceOrigins.read(f.snapshot(), malformed.getFirst(), malformed));
        }
    }
    @Test void inheritedAndProfileDependentResourcesNeedEffectiveModelProvenance() throws Exception {
        var f = fixture("<parent><relativePath>../pom.xml</relativePath></parent>", false);
        Path parent = f.snapshot().resolve("pom.xml"); Files.writeString(parent, "<project>" + resource("src/test/resources", "") + "</project>");
        var pins = new ArrayList<>(f.pins()); pins.add(ControlBuild.FileRef.measure(parent));
        assertThrows(IOException.class, () -> CompiledTestResourceOrigins.read(f.snapshot(), ControlBuild.FileRef.measure(f.pom()), pins));
        Files.writeString(f.pom(), "<project><profiles><profile><build><testResources/></build></profile></profiles></project>");
        var updated = List.of(ControlBuild.FileRef.measure(f.pom()), ControlBuild.FileRef.measure(f.source()));
        assertThrows(IOException.class, () -> CompiledTestResourceOrigins.read(f.snapshot(), updated.getFirst(), updated));
    }
}


