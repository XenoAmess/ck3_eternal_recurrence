package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.ExecutionProfile;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind;

/** Pure producer/consumer contract regression; these metadata values grant no Native read, source or ManagedGame qualification. */
final class DirectArmyWarWindowConsumerTest {
    @Test void explicitDirectProfileReachesItsFiniteExpectedSchemaAndSdkV1StillRequiresItsQuote() {
        for (Kind kind : List.of(Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1, Kind.CLOSE_WAR_RESULTS_WINDOW_V1)) {
            OperationKey operation = operation(kind);
            var direct = arguments(kind, "4", List.of(), ExecutionProfile.DIRECT_FIXED_WINDOW);
            var reopened = ArmyOrdinaryActionArguments.decode(direct.raw());
            assertTrue(NativeArmyWarWindowEffects.direct(reopened));
            assertEquals(NativeDirectFixedWindowObservation.SCHEMA,
                    NativeArmyWarWindowEffects.expected(before(), source(), operation, reopened.raw()).observerSchema());
            var ordinary = arguments(kind, "4", List.of(reference("unread-quote")), ExecutionProfile.SDK_ORDINARY);
            assertFalse(NativeArmyWarWindowEffects.direct(ordinary));
            assertEquals(NativeArmyWarWindowEffects.SCHEMA,
                    NativeArmyWarWindowEffects.expected(before(), source(), operation, ordinary.raw()).observerSchema());
        }
    }

    @Test void emptyOrdinaryQuoteInventoryCannotImplyTheDirectProfileOrRelaxTheOriginalWindowContract() {
        for (Kind kind : List.of(Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1, Kind.CLOSE_WAR_RESULTS_WINDOW_V1)) {
            var original = new ArmyOrdinaryActionArguments(kind, rawRevision("4"), List.of());
            var reopened = ArmyOrdinaryActionArguments.decode(original.raw());
            assertEquals(ExecutionProfile.SDK_ORDINARY, reopened.executionProfile());
            assertFalse(NativeArmyWarWindowEffects.direct(reopened));
            assertFalse(new String(original.raw().bytes(), java.nio.charset.StandardCharsets.UTF_8).contains("execution_profile"));
            assertThrows(IllegalArgumentException.class,
                    () -> NativeArmyWarWindowEffects.expected(before(), source(), operation(kind), reopened.raw()));
            assertThrows(IllegalArgumentException.class,
                    () -> arguments(kind, "4", List.of(reference("unread-quote")), ExecutionProfile.DIRECT_FIXED_WINDOW));
        }
        assertThrows(IllegalArgumentException.class,
                () -> arguments(Kind.RAISE_TROOPS_DEFAULT, "4", List.of(), ExecutionProfile.DIRECT_FIXED_WINDOW));
    }

    @Test void directExpectedCannotCrossTheOriginalOperationOrCallerRevision() {
        var direct = arguments(Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1, "4", List.of(), ExecutionProfile.DIRECT_FIXED_WINDOW);
        assertThrows(IllegalArgumentException.class, () -> NativeArmyWarWindowEffects.expected(before(), source(),
                operation(Kind.CLOSE_WAR_RESULTS_WINDOW_V1), direct.raw()));
        for (String revision : List.of("0", "5")) {
            var wrong = arguments(Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1, revision, List.of(), ExecutionProfile.DIRECT_FIXED_WINDOW);
            assertThrows(IllegalArgumentException.class, () -> NativeArmyWarWindowEffects.expected(before(), source(),
                    operation(Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1), wrong.raw()));
        }
        for (RawJson missingOrNull : List.of(raw("{}"), raw("{\"expected_revision\":null}"))) {
            var wrong = new ArmyOrdinaryActionArguments(Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1, missingOrNull, List.of(),
                    ExecutionProfile.DIRECT_FIXED_WINDOW, Optional.empty());
            assertThrows(IllegalArgumentException.class, () -> NativeArmyWarWindowEffects.expected(before(), source(),
                    operation(Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1), wrong.raw()));
        }
    }

    private static ArmyOrdinaryActionArguments arguments(Kind kind, String revision, List<ExactRef> originalQuotes,
            ExecutionProfile profile) {
        return new ArmyOrdinaryActionArguments(kind, rawRevision(revision), originalQuotes, profile, Optional.empty());
    }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
    private static RawJson rawRevision(String value) { return raw("{\"expected_revision\":\"" + value + "\"}"); }
    private static OperationKey operation(Kind kind) {
        return new OperationKey(kind == Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1
                ? "close-war-declared-overview-v1" : "close-war-results-window-v1");
    }
    private static ExactRef reference(String label) {
        return new ExactRef(Path.of(label + ".metadata-only").toAbsolutePath().normalize().toString(), 1, "a".repeat(64));
    }
    private static G2Source source() {
        return new G2Source("software-metadata-fixture", "2026-10-24T00:00:00Z", "direct-window-contract-only", reference("source"));
    }
    private static ObservationIdentity before() {
        var frame = new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(7), BigInteger.valueOf(3), BigInteger.valueOf(102)),
                "metadata-only-frame", BigInteger.valueOf(4), "metadata-only-episode");
        return new ObservationIdentity(source().machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
    }
}
