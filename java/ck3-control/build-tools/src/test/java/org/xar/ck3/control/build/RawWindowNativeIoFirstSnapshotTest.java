package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.RawWindowCaptureContract.CloseStatus.CLOSED;
import static org.xar.ck3.control.build.RawWindowCaptureContract.CloseStatus.NOT_OPENED;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.RawWindowCaptureContract.ReadRange;

/** Software fixture files only; no PE, Game, admission, Root guard or private helper. */
final class RawWindowNativeIoFirstSnapshotTest {
    @TempDir Path temporary;

    @Test
    void forcedSnapshotsDetachAliasesAndAChangedFirstAliasIsRevalidated() throws Exception {
        Path output = Files.createDirectory(temporary.resolve("aliases"));
        Path journal = output.resolve("fallback.jsonl");
        byte[] first = utf8("{\"first\":true}");
        byte[] later = utf8("{\"later\":1}");
        byte[] expected = utf8("{\"first\":true}\n{\"later\":1}\n");
        try (RawWindowNativeIo io = softwareIo(output, 65536)) {
            io.startMetadataJournal(first);
            Arrays.fill(first, (byte) 'x');
            assertArrayEquals(utf8("{\"first\":true}\n"), Files.readAllBytes(journal));
            io.appendMetadata(later);
            Arrays.fill(later, (byte) 'y');
            assertArrayEquals(expected, Files.readAllBytes(journal));

            io.openInput();
            // Reusing an accepted array identity must not authorize its now-invalid contents.
            assertThrows(IOException.class, () -> io.appendMetadata(first));
            assertArrayEquals(expected, Files.readAllBytes(journal));
            assertThrows(IOException.class, () -> io.read(new ReadRange(0, 1)));
            assertEquals(CLOSED, io.closeInput());
            assertEquals(NOT_OPENED, io.closeInput());
        }
        assertArrayEquals(expected, Files.readAllBytes(journal));
        // Real Windows fixture cleanup also observes release of journal and held-directory handles.
        Files.delete(journal);
        Files.delete(output);
    }

    @Test
    void initialAndExternalValidationFailuresPoisonAndNewlinesCountAgainstTheCap() throws Exception {
        byte[] malformedUtf8 = {(byte) 0xc3, 0x28};
        Path beforeOpen = Files.createDirectory(temporary.resolve("before-open"));
        try (RawWindowNativeIo io = softwareIo(beforeOpen, 65536)) {
            assertThrows(IOException.class, () -> io.startMetadataJournal(malformedUtf8));
            IOException retry = assertThrows(IOException.class, () -> io.startMetadataJournal(utf8("{}")));
            assertEquals("durable fallback poisoned before open", retry.getMessage());
            assertFalse(Files.exists(beforeOpen.resolve("fallback.jsonl")));
            assertEquals(NOT_OPENED, io.closeInput());
        }

        List<byte[]> invalid = Arrays.asList(null, new byte[0], new byte[4096], malformedUtf8, utf8("{} {}"), utf8("[]"));
        for (int index = 0; index < invalid.size(); index++) {
            byte[] external = invalid.get(index);
            Path output = Files.createDirectory(temporary.resolve("invalid-" + index));
            try (RawWindowNativeIo io = softwareIo(output, 65536)) {
                io.startMetadataJournal(utf8("{}"));
                io.openInput();
                assertThrows(IOException.class, () -> io.appendMetadata(external));
                assertArrayEquals(utf8("{}\n"), Files.readAllBytes(output.resolve("fallback.jsonl")));
                assertThrows(IOException.class, () -> io.appendMetadata(utf8("{}")));
                assertThrows(IOException.class, () -> io.read(new ReadRange(0, 1)));
                assertEquals(CLOSED, io.closeInput());
            }
        }

        byte[] maximum = utf8("{\"v\":\"" + "x".repeat(4087) + "\"}");
        assertEquals(4095, maximum.length);
        byte[] expected = Arrays.copyOf(maximum, maximum.length + 1);
        expected[maximum.length] = '\n';
        Path exactCap = Files.createDirectory(temporary.resolve("exact-cap"));
        try (RawWindowNativeIo io = softwareIo(exactCap, 4096)) {
            io.startMetadataJournal(maximum);
            assertArrayEquals(expected, Files.readAllBytes(exactCap.resolve("fallback.jsonl")));
            io.openInput();
            IOException exceeded = assertThrows(IOException.class, () -> io.appendMetadata(utf8("{}")));
            assertEquals("bounded fallback event/budget exceeded before further input", exceeded.getMessage());
            assertArrayEquals(expected, Files.readAllBytes(exactCap.resolve("fallback.jsonl")));
            assertThrows(IOException.class, () -> io.read(new ReadRange(0, 1)));
            assertEquals(CLOSED, io.closeInput());
        }
    }

    private RawWindowNativeIo softwareIo(Path output, int journalCap) throws IOException {
        Path input = temporary.resolve(output.getFileName() + ".bin").toAbsolutePath().normalize();
        Files.write(input, new byte[] {1, 2, 3, 4}, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        Path root = output.toAbsolutePath().normalize();
        return RawWindowNativeIo.namedFrontend(new RawWindowNativeIo.NamedInput(input.toString(), root.toString(),
                SharedSourceFiles.nativeDirectory(root), 32768, journalCap, 32768));
    }

    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
