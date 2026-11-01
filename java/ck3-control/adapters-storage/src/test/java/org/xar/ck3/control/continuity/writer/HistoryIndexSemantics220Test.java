package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Files;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.ContinuityJson;

final class HistoryIndexSemantics220Test {
    @TempDir Path root;

    @Test void firstMatchesKeepDistinctKeysAndDoNotVisitAnInvalidTail() throws Exception {
        Path target = root.resolve("canonical.json").toAbsolutePath().normalize();
        String alias = target.getParent().resolve("unused").resolve("..").resolve(target.getFileName()).toString();
        Pin first = pin(alias, "2"), duplicate = pin(alias, "2");
        Pin anchor = pin(target.toString(), "3");
        Pin invalid = pin("invalid" + (char) 0 + "path", "4");
        Pin trailing = pin(root.resolve("trailing.json").toString(), "5");
        Object index = index(List.of(first, duplicate, anchor, invalid, trailing), anchor.reference());

        assertSame(first, path(index, target, "missing-path"));
        assertSame(anchor, call(index, "anchor", new Class<?>[0]));
        assertSame(first, exact(index, duplicate, "missing-pin"));
        assertSame(trailing, exact(index, trailing, "missing-pin"));
        Pin missing = pin(root.resolve("absent.json").toString(), "6");
        IOException absent = assertThrows(IOException.class, () -> exact(index, missing, "exact-missing220"));
        assertEquals("exact-missing220", absent.getMessage());

        assertThrows(InvalidPathException.class, () -> path(index, root.resolve("not-present.json"), "unused"));
        assertThrows(InvalidPathException.class, () -> path(index, root.resolve("trailing.json"), "unused"));
        assertSame(first, path(index, target, "missing-path"));
        Object valid = index(List.of(first, duplicate, anchor), anchor.reference());
        IOException absentPath = assertThrows(IOException.class,
                () -> path(valid, root.resolve("not-present.json"), "path-missing220"));
        assertEquals("path-missing220", absentPath.getMessage());
    }

    @Test void warmPublicReadsSeeNewHeadRejectForeignThreadAndReplacedOriginal() throws Exception {
        WriterFixture fixture = new WriterFixture(root.resolve("public-chain"));
        Receipt one = fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("one220", 1024, 2)));
        Receipt two = fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("two220", 1048, 3)));
        String digestOne = ContinuityJson.digest(one.head().toJson());
        String digestTwo = ContinuityJson.digest(two.head().toJson());
        fixture.writer.locked(same -> {
            assertArrayEquals(one.head().canonicalBytes(), same.requireHistoricalCanonicalState(1, digestOne).canonicalBytes());
            assertArrayEquals(two.head().canonicalBytes(), same.requireHistoricalCanonicalState(2, digestTwo).canonicalBytes());
            Receipt three = same.commit(same.preview(WriterFixture.settled("three220", 1072, 4)));
            String digestThree = ContinuityJson.digest(three.head().toJson());
            assertArrayEquals(three.head().canonicalBytes(), same.requireHistoricalCanonicalState(3, digestThree).canonicalBytes());
            Pin firstPin = LedgerFiles.read(fixture.layout.event(1), ContinuityJson.LEDGER_MAX_BYTES).pin();
            Pin thirdPin = LedgerFiles.read(fixture.layout.event(3), ContinuityJson.LEDGER_MAX_BYTES).pin();
            var edges = same.readHistoricalTransitions(List.of(thirdPin, firstPin, thirdPin));
            assertEquals(List.of(3L, 1L, 3L), edges.stream().map(HistoricalTransition::sequence).toList());
            assertArrayEquals(one.head().canonicalBytes(), edges.get(1).after().canonicalBytes());
            assertArrayEquals(three.head().canonicalBytes(), edges.get(2).after().canonicalBytes());

            AtomicReference<Throwable> rejected = new AtomicReference<>();
            Thread foreign = new Thread(() -> {
                try { same.requireHistoricalCanonicalState(1, digestOne); }
                catch (Throwable failure) { rejected.set(failure); }
            }, "writer220-foreign-fixture");
            foreign.setDaemon(true);
            foreign.start();
            try { foreign.join(2000); }
            catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                throw new IOException("fixture join interrupted", interrupted);
            }
            if (foreign.isAlive()) {
                foreign.interrupt();
                throw new IOException("foreign fixture call did not terminate within its finite bound");
            }
            assertInstanceOf(ContractViolationException.class, rejected.get());
            assertArrayEquals(three.head().canonicalBytes(), same.requireHistoricalCanonicalState(3, digestThree).canonicalBytes());

            Path original = fixture.layout.event(3);
            byte[] body = Files.readAllBytes(original);
            byte[] snapshot = Files.readAllBytes(fixture.layout.snapshot());
            Path replacement = root.resolve("replacement220.json");
            Files.write(replacement, body);
            Files.move(replacement, original, StandardCopyOption.REPLACE_EXISTING);
            Pin replaced = LedgerFiles.read(original, ContinuityJson.LEDGER_MAX_BYTES).pin();
            assertArrayEquals(body, Files.readAllBytes(original));
            assertNotEquals(thirdPin.identity(), replaced.identity());
            assertThrows(IOException.class, () -> same.requireHistoricalCanonicalState(3, digestThree));
            assertFalse(Files.exists(fixture.layout.event(4)));
            assertArrayEquals(snapshot, Files.readAllBytes(fixture.layout.snapshot()));
            return null;
        });
    }

    private static Pin pin(String path, String fileId) {
        return new Pin(new ExactRef(path, 0, "0".repeat(64)),
                new FileIdentity("1", fileId, "134000000000000000", "2026-11-01T00:00:00Z", 0));
    }

    private static Object index(List<Pin> documents, ExactRef anchor) throws ReflectiveOperationException {
        Class<?> type = Class.forName(ContinuityWriter.class.getName() + "$Session$HistoryIndex");
        var constructor = type.getDeclaredConstructor(List.class, ExactRef.class);
        constructor.setAccessible(true);
        return constructor.newInstance(documents, anchor);
    }

    private static Pin path(Object index, Path path, String missing) throws Exception {
        return call(index, "path", new Class<?>[]{Path.class, String.class}, path, missing);
    }

    private static Pin exact(Object index, Pin pin, String missing) throws Exception {
        return call(index, "pin", new Class<?>[]{Pin.class, String.class}, pin, missing);
    }

    private static Pin call(Object index, String name, Class<?>[] parameters, Object... arguments) throws Exception {
        var method = index.getClass().getDeclaredMethod(name, parameters);
        method.setAccessible(true);
        try { return (Pin) method.invoke(index, arguments); }
        catch (InvocationTargetException wrapped) {
            Throwable cause = wrapped.getCause();
            if (cause instanceof Exception failure) throw failure;
            if (cause instanceof Error failure) throw failure;
            throw new AssertionError(cause);
        }
    }
}
