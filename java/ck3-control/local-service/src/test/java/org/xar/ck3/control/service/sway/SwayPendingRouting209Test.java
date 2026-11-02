package org.xar.ck3.control.service.sway;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.sway.SwayNativeWire;
import org.xar.ck3.control.contracts.ExactRef;

/** Software registry classification only; no Root writer, permit, action preparation or Native call. */
final class SwayPendingRouting209Test {
    private static final ExactRef SOURCE = new ExactRef("software:sway-routing209", 1, "a".repeat(64));

    private static OperationKey start(long target) {
        return new OperationKey(SwayNativeWire.START + target);
    }

    private static RootExecutableBindings.Family<Long> family(String id, AtomicInteger factories) {
        return new RootExecutableBindings.Family<>(id, Long.class,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), SOURCE, SOURCE, SOURCE,
                value -> new RawJson(("{\"target_character_id\":" + value + "}").getBytes(StandardCharsets.UTF_8)),
                SwayPendingRouting209Test::start, value -> {
                    factories.incrementAndGet();
                    var operation = start(value);
                    var effect = new NativeEffectRegistry.Binding(operation, SOURCE,
                            command -> { throw new AssertionError("routing cannot prepare an action"); },
                            (command, attempt, dispatch) -> { throw new AssertionError("routing cannot observe an action"); });
                    var replay = new NativeRecordedEvidenceVerifier.Binding(operation, SOURCE,
                            (head, proposed, originals) -> { throw new AssertionError("routing cannot verify an effect"); });
                    return new RootExecutableBindings.IssuedAction(new RootExecutableBindings.ActionBinding(
                            effect, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), SOURCE), replay);
                });
    }

    private static RootExecutableBindings catalog(List<RootExecutableBindings.Family<?>> families) {
        return RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()),
                List.of(), List.of(), families, 16);
    }

    private static Function<OperationKey, Optional<RootExecutableBindings.Family<?>>> lookup(
            RootExecutableBindings actual, AtomicInteger queries) {
        return operation -> {
            queries.incrementAndGet();
            return actual.actualFamily(operation);
        };
    }

    @Test void signedIssuedBoundariesPreserveActualRegistryWithoutIssuing() {
        var factories = new AtomicInteger();
        var queries = new AtomicInteger();
        var expected = family("software-sway209", factories);
        var actual = catalog(List.of(expected));
        long[] targets = { Integer.MIN_VALUE, -2, 0, 1, Integer.MAX_VALUE };
        for (long target : targets) actual.issue(expected, target);
        var actions = actual.actionBindings();
        var replays = actual.archivedBindings();
        assertEquals(targets.length, factories.get());
        for (long target : targets) {
            assertTrue(SwayRuntimeInstaller.supportsPendingOperation(start(target), expected, lookup(actual, queries)));
            assertSame(expected, actual.actualFamily(start(target)).orElseThrow());
        }
        assertEquals(targets.length, queries.get());
        assertEquals(targets.length, factories.get(), "classification must never issue an action");
        assertEquals(actions, actual.actionBindings());
        assertEquals(replays, actual.archivedBindings());
    }

    @Test void invalidIdsAndAliasesAndShortcutsNeverLookupOrIssue() {
        var factories = new AtomicInteger();
        var queries = new AtomicInteger();
        var expected = family("software-sway209-invalid", factories);
        var actual = catalog(List.of(expected));
        for (String suffix : List.of("-1", "2147483648", "-2147483649", "4294967294", "4294967295",
                "01", "-02", "-0", "--2", "", "2.0", "1_0", "9223372036854775808")) {
            assertFalse(SwayRuntimeInstaller.supportsPendingOperation(new OperationKey(SwayNativeWire.START + suffix),
                    expected, lookup(actual, queries)), suffix);
        }
        assertTrue(SwayRuntimeInstaller.supportsPendingOperation(new OperationKey(SwayNativeWire.STOP),
                expected, lookup(actual, queries)));
        assertFalse(SwayRuntimeInstaller.supportsPendingOperation(new OperationKey("move-army-7"),
                expected, lookup(actual, queries)));
        assertEquals(0, queries.get());
        assertEquals(0, factories.get());
        assertTrue(actual.actionBindings().isEmpty());
        assertTrue(actual.archivedBindings().isEmpty());
    }

    @Test void unissuedAndActuallyForeignFamilyCannotClaimPendingProducer() {
        var expectedFactories = new AtomicInteger();
        var foreignFactories = new AtomicInteger();
        var queries = new AtomicInteger();
        var expected = family("software-sway209-expected", expectedFactories);
        var foreign = family("software-sway209-foreign", foreignFactories);
        var actual = catalog(List.of(expected, foreign));
        assertFalse(SwayRuntimeInstaller.supportsPendingOperation(start(7), expected, lookup(actual, queries)));
        assertEquals(1, queries.get());
        assertEquals(0, expectedFactories.get());
        assertEquals(0, foreignFactories.get());
        actual.issue(foreign, 7L);
        var actions = actual.actionBindings();
        var replays = actual.archivedBindings();
        assertFalse(SwayRuntimeInstaller.supportsPendingOperation(start(7), expected, lookup(actual, queries)));
        assertTrue(SwayRuntimeInstaller.supportsPendingOperation(start(7), foreign, lookup(actual, queries)));
        var matchingButUninstalled = family("software-sway209-foreign", new AtomicInteger());
        assertFalse(SwayRuntimeInstaller.supportsPendingOperation(start(7), matchingButUninstalled, lookup(actual, queries)));
        assertEquals(4, queries.get());
        assertEquals(0, expectedFactories.get());
        assertEquals(1, foreignFactories.get());
        assertEquals(actions, actual.actionBindings());
        assertEquals(replays, actual.archivedBindings());
    }

    @Test void actualLookupFailureIsPropagatedOutsideIdentityParsingCatch() {
        var factories = new AtomicInteger();
        var queries = new AtomicInteger();
        var expected = family("software-sway209-failure", factories);
        var actual = catalog(List.of(expected));
        actual.issue(expected, -2L);
        var actions = actual.actionBindings();
        var replays = actual.archivedBindings();
        var failure = new IllegalArgumentException("software actual-family lookup failed");
        Function<OperationKey, Optional<RootExecutableBindings.Family<?>>> failing = operation -> {
            queries.incrementAndGet();
            assertSame(expected, actual.actualFamily(operation).orElseThrow());
            throw failure;
        };
        assertSame(failure, assertThrows(IllegalArgumentException.class,
                () -> SwayRuntimeInstaller.supportsPendingOperation(start(-2), expected, failing)));
        assertEquals(1, queries.get());
        assertEquals(1, factories.get());
        assertEquals(actions, actual.actionBindings());
        assertEquals(replays, actual.archivedBindings());
    }
}
