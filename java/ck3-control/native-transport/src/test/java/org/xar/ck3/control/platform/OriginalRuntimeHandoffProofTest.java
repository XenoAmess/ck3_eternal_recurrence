package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.Modifier;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Actual public provider entry to importer callback. No fake token or fabricated successful custody. */
final class OriginalRuntimeHandoffProofTest {
    @TempDir Path temporary;
    private static final String MACHINE = "source-fixture-machine-001";
    @Test void missingActualOwnedProducerRefusesBeforeCapturePreviewOrCommitEvenWithReadableStore() throws Exception {
        Path store = Files.createDirectories(temporary.resolve("native-session/rite-creation-actions"));
        // This reproduces the real missing category: driver/claim GamePID is not the old Python PID.
        Files.writeString(store.getParent().resolve("driver-state.json"), "{\"bridge_pid\":50688}");
        Files.writeString(store.resolve("readable-original.json"), "{\"game_pid\":50688}");
        var provider = WindowsOriginalRuntimeHandoff.originalOwnedLaunch(Optional.empty());
        var called = new AtomicInteger();
        OriginalRuntimeHandoffProof.Result<Integer> actual = provider.withOriginalStore(store, MACHINE, lease -> {
            called.incrementAndGet(); lease.requireCurrent(); return 1;
        });
        assertInstanceOf(OriginalRuntimeHandoffProof.Unavailable.class, actual);
        if (!(actual instanceof OriginalRuntimeHandoffProof.Unavailable<Integer> unavailable))
            fail("Missing original object must remain Unavailable");
        else {
            assertEquals(OriginalRuntimeHandoffProof.Reason.ORIGINAL_OWNED_LAUNCH_UNAVAILABLE, unavailable.reason());
            assertTrue(unavailable.originalEvidence().isEmpty());
            var mapper = ControlBuild.strictMapper();
            byte[] raw = mapper.writeValueAsBytes(unavailable);
            var roundTrip = mapper.readTree(raw);
            assertEquals(unavailable.reason().name(), roundTrip.get("reason").textValue());
            assertEquals(unavailable.detail(), roundTrip.get("detail").textValue());
            assertTrue(roundTrip.get("original_evidence").isArray());
            assertEquals(0, roundTrip.get("original_evidence").size());
            assertEquals(roundTrip, mapper.readTree(mapper.writeValueAsBytes(roundTrip)));
        }
        assertEquals(0, called.get(), "No source capture, reducer preview or commit may run without the proof");
        assertEquals("{\"game_pid\":50688}", Files.readString(store.resolve("readable-original.json")));
    }
    @Test void absentStoreIsNotFreshProofAndMalformedScopeNeverReachesTheWork() throws Exception {
        var provider = WindowsOriginalRuntimeHandoff.originalOwnedLaunch(Optional.empty());
        Path absent = temporary.resolve("never-created/native-session/rite-creation-actions");
        assertFalse(Files.exists(absent));
        assertInstanceOf(OriginalRuntimeHandoffProof.Unavailable.class,
                provider.withOriginalStore(absent, MACHINE, lease -> fail("Absent store cannot mint original retirement")));
        assertThrows(IllegalArgumentException.class, () -> provider.withOriginalStore(Path.of("relative"), MACHINE, lease -> 1));
        assertThrows(IllegalArgumentException.class, () -> provider.withOriginalStore(absent, "unknown", lease -> 1));
        assertThrows(IllegalArgumentException.class, () -> provider.withOriginalStore(absent.resolve("../other"), MACHINE, lease -> 1));
        assertFalse(Files.exists(absent));
    }
    @Test void noPublicLeaseProviderOrRuntimeBindingConstructorCanRestoreAuthorityFromJsonOrFlags() {
        for (Class<?> type : new Class<?>[]{OriginalRuntimeHandoffProof.Lease.class,
                OriginalRuntimeHandoffProof.Provider.class, WindowsOriginalRuntimeHandoff.class}) {
            assertTrue(Modifier.isFinal(type.getModifiers()));
            assertEquals(0, type.getConstructors().length);
            for (var constructor : type.getDeclaredConstructors()) assertTrue(Modifier.isPrivate(constructor.getModifiers()));
        }
        assertEquals(0, WindowsJobProcess.OwnedStdio.class.getConstructors().length);
        for (var method : WindowsOriginalRuntimeHandoff.class.getMethods())
            if (method.getDeclaringClass() == WindowsOriginalRuntimeHandoff.class)
                assertTrue(java.util.Set.of("originalOwnedLaunch", "relicOriginalOwnedLaunch",
                        "holyCreationOriginalOwnedLaunch", "grantOriginalOwnedLaunch").contains(method.getName()));
    }
}
