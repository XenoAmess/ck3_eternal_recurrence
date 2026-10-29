package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class BoundedSourceInputGuardTest {
    @TempDir Path temporary;
    private ControlBuild.FileRef manifest(List<ControlBuild.FileRef> sources) throws Exception {
        var value = new BoundedSourceInputGuard.Manifest(BoundedSourceInputGuard.SCHEMA,
                WindowsJobProcess.currentMachineId(), "/root/tools_c15", Instant.now().toString(),
                Instant.now().plusSeconds(600).toString(), sources);
        Path path = temporary.resolve("manifest-" + java.util.UUID.randomUUID() + ".json");
        Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value));
        return ControlBuild.FileRef.measure(path);
    }
    @Test void actual513NativeInputsRemainExactAcrossClosureAndDurableReadback() throws Exception {
        var sources = new ArrayList<ControlBuild.FileRef>();
        for (int i = 0; i < 513; i++) {
            Path path = temporary.resolve("source-" + i); Files.writeString(path, "x");
            sources.add(ControlBuild.FileRef.measure(path));
        }
        var guard = BoundedSourceInputGuard.open(manifest(sources), "/root/tools_c15");
        long reservedReceiptBytes = guard.maximumReceiptBytes();
        try (guard) { guard.requireExactInputs(sources); assertThrows(IOException.class, guard::receipt); }
        var receipt = guard.receipt();
        assertEquals(513, receipt.files()); assertEquals(513, receipt.logicalBytes());
        assertEquals(514, receipt.observations().size()); assertEquals("MATCH", receipt.postcheck());
        var mapper = ControlBuild.strictMapper();
        byte[] actualBytes = mapper.writeValueAsBytes(receipt);
        assertTrue(actualBytes.length <= reservedReceiptBytes);
        assertThrows(IOException.class, guard::maximumReceiptBytes);
        assertEquals(receipt, mapper.readValue(actualBytes, BoundedSourceInputGuard.Receipt.class));
    }
    @Test void originalIndexSubsetAndForeignSameBytesRefCannotAuthorizeTheirOwnClosure() throws Exception {
        Path a = temporary.resolve("a"), b = temporary.resolve("b"), foreign = temporary.resolve("foreign");
        Files.writeString(a, "same"); Files.writeString(b, "same"); Files.writeString(foreign, "same");
        var sources = List.of(ControlBuild.FileRef.measure(a), ControlBuild.FileRef.measure(b));
        try (var guard = BoundedSourceInputGuard.open(manifest(sources), "/root/tools_c15")) {
            assertThrows(IOException.class, () -> guard.requireExactInputs(List.of(sources.getFirst())));
            assertThrows(IOException.class, () -> guard.requireExactInputs(List.of(sources.getFirst(), ControlBuild.FileRef.measure(foreign))));
            guard.requireExactInputs(sources);
        }
    }
    @Test void sameBytesReplacementIsRejectedByOriginalNativeBirthAndNoReceiptIsMinted() throws Exception {
        Path path = temporary.resolve("source"); Files.writeString(path, "same");
        var guard = BoundedSourceInputGuard.open(manifest(List.of(ControlBuild.FileRef.measure(path))), "/root/tools_c15");
        Files.move(path, temporary.resolve("retained-original")); Files.writeString(path, "same");
        assertThrows(IOException.class, guard::close); assertThrows(IOException.class, guard::receipt);
    }
    @Test void strictManifestRejectsDuplicatePathsWrongOwnerAndNonintegralBytes() throws Exception {
        Path path = temporary.resolve("source"); Files.writeString(path, "value");
        var pin = ControlBuild.FileRef.measure(path);
        assertThrows(IllegalArgumentException.class, () -> manifest(List.of(pin, pin)));
        var reference = manifest(List.of(pin));
        assertThrows(IOException.class, () -> BoundedSourceInputGuard.open(reference, "/root/another_owner"));
        var mapper = ControlBuild.strictMapper();
        var wire = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                mapper.readTree(Files.readAllBytes(Path.of(reference.path()))));
        var row = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, wire.required("files").get(0));
        row.put("bytes", true);
        assertThrows(IOException.class, () -> mapper.treeToValue(wire, BoundedSourceInputGuard.Manifest.class));
        row.put("bytes", pin.bytes());
        wire.put("undeclared", 1);
        assertThrows(IOException.class, () -> mapper.treeToValue(wire, BoundedSourceInputGuard.Manifest.class));
    }
    @Test void actualTransientReadBodyMustMatchTheOriginalManifestPinEvenWhenTheFileIsRestored() throws Exception {
        Path source = temporary.resolve("source"); Files.writeString(source, "original");
        var exact = manifest(List.of(ControlBuild.FileRef.measure(source)));
        byte[] original = Files.readAllBytes(Path.of(exact.path()));
        String text = new String(original, java.nio.charset.StandardCharsets.UTF_8);
        byte[] transientRead = text.replace("/root/tools_c15", "/root/tools_c16")
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertEquals(original.length, transientRead.length); assertFalse(java.util.Arrays.equals(original, transientRead));
        exact.verify();
        assertThrows(IOException.class, () -> BoundedSourceInputGuard.decodeManifest(exact, transientRead));
        exact.verify();
        assertEquals("/root/tools_c15", BoundedSourceInputGuard.decodeManifest(exact, original).taskOwner());
    }
}
