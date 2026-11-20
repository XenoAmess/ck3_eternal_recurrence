package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Owned temporary files exercise original bytes only; this never calls a preparation, attachment, capture or Host entry. */
class RootPublicInputOriginalFileTest {
    @TempDir Path temporary;
    private static FileRef actual(Path path, byte[] original) throws Exception {
        return new FileRef(path.toString(), original.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
    }
    @Test void incompleteOriginalCannotCreateApplicationOrFutureBusinessRoot() throws Exception {
        Path request = temporary.resolve("unbound-request.json");
        byte[] original = ("{\"schema\":\"" + RootRuntimeDefinitions.UNBOUND_APPLICATION_SCHEMA + "\"}").getBytes(StandardCharsets.UTF_8);
        Files.write(request, original); FileRef held = actual(request, original);
        assertThrows(IOException.class, () -> RootRuntimeDefinitions.readPublicInputRequest(held, Clock.systemUTC()));
        assertArrayEquals(original, Files.readAllBytes(request));
        try (var files = Files.list(temporary)) { assertEquals(1, files.count()); }
        assertFalse(Files.exists(temporary.resolve("business")));
        assertFalse(Files.exists(temporary.resolve("application.json")));
    }
    @Test void originalByteDriftFailsBeforeAnyDecoderOrPublicationCanDefaultIt() throws Exception {
        Path request = temporary.resolve("original.json");
        byte[] original = "{}".getBytes(StandardCharsets.UTF_8);
        Files.write(request, original); FileRef held = actual(request, original);
        Files.writeString(request, "{\"changed\":true}");
        var failed = assertThrows(IOException.class, () -> RootRuntimeDefinitions.readPublicInputRequest(held, Clock.systemUTC()));
        assertTrue(failed.getMessage().contains("exact runtime input changed"));
        try (var files = Files.list(temporary)) { assertEquals(1, files.count()); }
    }
}
