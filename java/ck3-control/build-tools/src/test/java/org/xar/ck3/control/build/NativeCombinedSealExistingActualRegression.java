package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeCombinedSourceCut.*;

/** Full existing-directory producer, using actual caller-supplied Tools/capacity, not a fabricated successful grant. */
final class NativeCombinedSealExistingActualRegression {
    @TempDir Path temporary;
    private record Fixture(FileRef request, Limits limits, Path output, Path control, Path marker, Path cmake) { }

    @Test void exactExistingTreeSealsWithoutWritingOrReplacingItsSources() throws IOException {
        Fixture f = fixture();
        var marker = SharedSourceFiles.observe(f.marker());
        var cmake = SharedSourceFiles.observe(f.cmake());
        FileRef spec = json(Path.of(f.request().path()).resolveSibling("seal-spec.json"),
                new Spec("xar.native-combined-existing-source-seal-execution/v1", f.request(), f.limits()));
        NativeCombinedSourceCut.main(new String[]{"seal-existing", spec.path(), Long.toString(spec.bytes()), spec.sha256()});
        FileRef actual = FileRef.measure(f.control().resolve("NATIVE-SOURCE-ACTUAL.json"));
        NativeCombinedSourceCut.main(new String[]{"verify-source", actual.path(), Long.toString(actual.bytes()), actual.sha256()});
        assertEquals(f.control().resolve("NATIVE-SOURCE-ACTUAL.json"), Path.of(actual.path()));
        Actual accepted = NativeCombinedSourceCut.readAcceptedSource(actual);
        assertEquals(2, accepted.completePackageSources().size());
        assertEquals(2, accepted.completeNativeSources().size());
        SharedSourceFiles.assertUnchanged(marker);
        SharedSourceFiles.assertUnchanged(cmake);
        assertEquals("patched\n", Files.readString(f.marker()));
        assertEquals(List.of(actual.path()), NativeBridgeBuild.inventory(f.control()).stream().map(FileRef::path).toList());
    }

    @Test void originalMaterializeStillRejectsAnExistingDirectory() throws IOException {
        Fixture f = fixture();
        IOException failure = assertThrows(IOException.class, () -> NativeCombinedSourceCut.materialize(f.request(), f.limits()));
        assertTrue(failure.getMessage().contains("New exact source root required"));
        assertFalse(Files.exists(f.control().resolve("NATIVE-SOURCE-ACTUAL.json")));
        assertEquals("patched\n", Files.readString(f.marker()));
    }

    @Test void wrongExistingBytesCannotBeSealedOrOverwritten() throws IOException {
        Fixture f = fixture();
        Files.writeString(f.marker(), "different\n");
        assertThrows(IOException.class, () -> NativeCombinedSourceCut.sealExisting(f.request(), f.limits()));
        assertFalse(Files.exists(f.control().resolve("NATIVE-SOURCE-ACTUAL.json")));
        assertEquals("different\n", Files.readString(f.marker()));
    }

    @Test void missingExpectedSourceCannotBeCreatedBySeal() throws IOException {
        Fixture f = fixture();
        Files.delete(f.marker());
        assertThrows(IOException.class, () -> NativeCombinedSourceCut.sealExisting(f.request(), f.limits()));
        assertFalse(Files.exists(f.control().resolve("NATIVE-SOURCE-ACTUAL.json")));
        assertFalse(Files.exists(f.marker()));
    }

    @Test void extraExistingSourceCannotEnterTheExactPackageDomain() throws IOException {
        Fixture f = fixture();
        Path extra = f.marker().resolveSibling("extra.hpp");
        Files.writeString(extra, "extra\n");
        assertThrows(IOException.class, () -> NativeCombinedSourceCut.sealExisting(f.request(), f.limits()));
        assertFalse(Files.exists(f.control().resolve("NATIVE-SOURCE-ACTUAL.json")));
        assertEquals("extra\n", Files.readString(extra));
    }

    private Fixture fixture() throws IOException {
        String machine = WindowsJobProcess.currentMachineId();
        FileRef qualified = requiredPin("xar.nativeSeal.tools");
        var receipt = ControlBuild.verifiedCompletedReceipt(qualified);
        if (!receipt.completeDeployment().equals(ControlBuild.producerClosure()))
            throw new IOException("Fixture must load the actual supplied complete Tools runtime");
        FileRef capacity = requiredPin("xar.nativeSeal.capacity");
        var release = RootNativePlanJson.mapper().readValue(Files.readAllBytes(Path.of(capacity.path())), ControlBuild.CapacityRelease.class);
        String owner = required("xar.nativeSeal.owner");
        Instant deadline = Instant.parse(required("xar.nativeSeal.deadline"));
        long allowance = Long.parseLong(required("xar.nativeSeal.outputLimitBytes"));
        if (!Long.toString(allowance).equals(required("xar.nativeSeal.outputLimitBytes")))
            throw new IOException("Canonical actual complete allocation bound required");
        Limits limits = new Limits(owner, capacity, deadline, allowance);
        Path inputs = Files.createDirectory(temporary.resolve("inputs"));
        Path output = Files.createDirectory(temporary.resolve("existing"));
        Path control = Files.createDirectory(temporary.resolve("control"));
        Path nativeRoot = output.resolve("ck3_autonomous_player/native_bridge");
        Files.createDirectories(nativeRoot);
        String baseText = "left\n", finalText = "patched\n";
        FileRef markerSource = put(inputs, "marker.hpp", baseText);
        var nativeFile = SharedSourceFiles.nativeFile(Path.of(markerSource.path()));
        var identity = new PreparationIdentity("win32-file-id-info", nativeFile.volumeSerialDecimal(), nativeFile.fileIdDecimal(),
                unixNs(nativeFile.lastWriteFiletimeDecimal()), unixNs(nativeFile.changeFiletimeDecimal()));
        FileRef census = gzip(inputs.resolve("base.json.gz"), new BaseCensus("xar.native-source-base-census/v1", machine,
                inputs.toString(), Instant.now().toString(), "FIXTURE_EXACT_SOURCE", List.of(
                    new BaseRow("marker.hpp", markerSource.bytes(), markerSource.sha256(), true, identity))));
        FileRef patch = put(inputs, "marker.patch", "--- a/marker.hpp\n+++ b/marker.hpp\n@@ -1,1 +1,1 @@\n-left\n+patched\n");
        FileRef cmakeBase = put(inputs, "cmake-base.txt", "cmake_minimum_required(VERSION 3.20)\n");
        String append = "# exact fixture composition\n";
        FileRef cmakeFinal = put(inputs, "cmake-final.txt", Files.readString(Path.of(cmakeBase.path())) + append);
        Content before = new Content(cmakeBase.bytes(), cmakeBase.sha256());
        Content after = new Content(cmakeFinal.bytes(), cmakeFinal.sha256());
        var step = new CompositionStep("append", CompositionSyntax.APPEND_EXACT, null, null, null, null, before, after,
                "Actual fixture CMake body", append);
        FileRef composition = json(inputs.resolve("composition.json"), new CmakeComposition("xar.native-cmake-strict-composition/v1",
                machine, "FIXTURE_COMPOSITION", cmakeBase, List.of(step), cmakeFinal, "OFF"));
        Path marker = nativeRoot.resolve("marker.hpp"), cmake = nativeRoot.resolve("CMakeLists.txt");
        Files.writeString(marker, finalText, StandardCharsets.UTF_8);
        Files.write(cmake, Files.readAllBytes(Path.of(cmakeFinal.path())));
        FileRef markerFinal = FileRef.measure(marker);
        FileRef expected = gzip(inputs.resolve("expected.json.gz"), new ExpectedFileSet("xar.native-combined-expected-file-set/v1",
                machine, 2, List.of(new ExpectedRow("ck3_autonomous_player/native_bridge/marker.hpp", markerFinal.bytes(), markerFinal.sha256()),
                new ExpectedRow("ck3_autonomous_player/native_bridge/CMakeLists.txt", cmakeFinal.bytes(), cmakeFinal.sha256()))));
        var request = new Request("xar.native-combined-source-cut-request/v1", machine, qualified, census, expected,
                List.of(new Selected("ck3_autonomous_player/native_bridge/CMakeLists.txt", cmakeFinal)),
                List.of(new Patch("ck3_autonomous_player/native_bridge/marker.hpp", new Content(markerSource.bytes(), markerSource.sha256()),
                        markerSource, patch, ExactSourcePatch.Syntax.UNIFIED_DIFF, "marker.hpp", new Content(markerFinal.bytes(), markerFinal.sha256()))),
                composition, List.of(), output, control, 4096);
        return new Fixture(json(inputs.resolve("request.json"), request), limits, output, control, marker, cmake);
    }

    private static String unixNs(String filetime) {
        return new BigInteger(filetime).subtract(new BigInteger("116444736000000000")).multiply(BigInteger.valueOf(100)).toString();
    }
    private static FileRef put(Path root, String name, String text) throws IOException {
        Path path = root.resolve(name); Files.writeString(path, text, StandardCharsets.UTF_8); return FileRef.measure(path);
    }
    private static FileRef json(Path path, Object value) throws IOException {
        Files.write(path, RootNativePlanJson.mapper().writeValueAsBytes(value)); return FileRef.measure(path);
    }
    private static FileRef gzip(Path path, Object value) throws IOException {
        try (var out = new GZIPOutputStream(Files.newOutputStream(path))) { out.write(RootNativePlanJson.mapper().writeValueAsBytes(value)); }
        return FileRef.measure(path);
    }
    private static String required(String name) throws IOException {
        String value = System.getProperty(name);
        if (value == null || value.isBlank()) throw new IOException("Actual fixture property required: " + name);
        return value;
    }
    private static FileRef requiredPin(String prefix) throws IOException {
        String bytes = required(prefix + ".bytes");
        long length = Long.parseLong(bytes);
        if (!Long.toString(length).equals(bytes)) throw new IOException("Canonical original byte count required");
        FileRef pin = new FileRef(required(prefix + ".path"), length, required(prefix + ".sha256"));
        pin.verify(); return pin;
    }
}
