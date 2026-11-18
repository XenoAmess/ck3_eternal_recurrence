package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Synthetic immutable command DATA only. No Full/Live frame, permission, Native receiver or actual Game is constructed. */
final class FullSnapshotClockControlTest {
    private static final String MACHINE = "full-clock-data", SESSION = "full-clock-data-session";
    private static final String SHA = "2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc";
    private static final Instant OBSERVED = Instant.parse("2026-11-18T00:00:00Z");
    private static final Instant DEADLINE = Instant.parse("2026-11-18T00:30:00.123456789Z");
    private static final BigInteger REVISION = new BigInteger("9007199254740993");
    private static final GameGeneration GAME = new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE));
    private static final ExactRef SOURCE_REF = new ExactRef("data-only/full-clock-source.java", 1, "0".repeat(64));
    private static final OpportunityJson.Obj EMPTY = new OpportunityJson.Obj(Map.of());
    private static final JointBudgetSelector.Claims NO_CLAIMS = new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of());
    private static final List<String> REGULAR = List.of("pause-map", "resume-map", "set-speed-1", "set-speed-2",
            "set-speed-3", "set-speed-4", "set-speed-5");
    private static final Set<String> CLAIM_FIELDS = Set.of("schema", "game_version", "executable_sha256", "adapter_id",
            "backend", "snapshot_id", "native_revision", "deadline_unix_ms");

    @Test
    void exactRawShaPreparesEveryOrdinaryClockStepWithoutChangingTheCommandOrCapability() {
        for (String sourceSha : List.of(SHA, SHA.toUpperCase(Locale.ROOT))) {
            for (String step : REGULAR) {
                var command = command(step, sourceSha, REVISION, "native:" + REVISION, DEADLINE, EMPTY);
                byte[] originalCommand = ActionCodec.encodeCommand(command);
                var request = AdvancePrimitives.prepareRequest(command);
                assertEquals(step, request.step());
                assertEquals("game.command." + step, request.requiredCapability().orElseThrow());
                assertTrue(request.preparationEvidence().isEmpty());
                assertArrayEquals(FullSnapshotClockControl.additionalFields(command).bytes(), request.additionalFields().bytes());
                assertClaim(command, request.additionalFields());
                assertArrayEquals(originalCommand, ActionCodec.encodeCommand(command));
            }
        }
    }

    @Test
    void saveCanUseTheSamePureDataHelperWithoutBecomingAnAdvancePrimitive() {
        var command = command("save-checkpoint", SHA, REVISION, "native:" + REVISION, DEADLINE, EMPTY);
        assertTrue(FullSnapshotClockControl.supports(command.operation()));
        assertFalse(AdvancePrimitives.supports(command.operation()));
        assertClaim(command, FullSnapshotClockControl.additionalFields(command));
        assertThrows(IllegalArgumentException.class, () -> AdvancePrimitives.prepareRequest(command));
    }

    @Test
    void nativeRevisionRemainsAnExactIntegerTokenThroughTheUnsigned64Boundary() {
        for (var revision : List.of(BigInteger.ONE, REVISION, new BigInteger("18446744073709551615"))) {
            var command = command("pause-map", SHA, revision, "native:" + revision, DEADLINE, EMPTY);
            var raw = AdvancePrimitives.prepareRequest(command).additionalFields();
            var value = claim(raw).get("native_revision");
            assertTrue(value.isIntegralNumber());
            assertFalse(value.isTextual()); assertFalse(value.isFloatingPointNumber());
            assertEquals(revision, value.bigIntegerValue());
            assertTrue(new String(raw.bytes(), StandardCharsets.UTF_8).contains("\"native_revision\":" + revision));
            assertEquals("native:" + revision, claim(raw).get("snapshot_id").textValue());
        }
    }

    @Test
    void originalAbsoluteDeadlineIsCopiedWithoutAClockOrARefreshedWindow() {
        // A positive historical time is still DATA. The helper never grants freshness or extends it from now.
        for (Instant deadline : List.of(Instant.parse("2000-01-01T00:00:00.001Z"), DEADLINE)) {
            var command = command("resume-map", SHA, REVISION, "native:" + REVISION, deadline, EMPTY);
            var fields = claim(AdvancePrimitives.prepareRequest(command).additionalFields());
            assertTrue(fields.get("deadline_unix_ms").isIntegralNumber());
            assertEquals(deadline.toEpochMilli(), fields.get("deadline_unix_ms").longValue());
            assertEquals(deadline, command.deadline());
        }
        for (Instant invalid : List.of(Instant.EPOCH, Instant.EPOCH.minusMillis(1), Instant.MAX)) {
            var command = command("pause-map", SHA, REVISION, "native:" + REVISION, invalid, EMPTY);
            assertThrows(IllegalArgumentException.class, () -> AdvancePrimitives.prepareRequest(command));
        }
    }

    @Test
    void legacyAndUnknownSourceSpellingsKeepTheirExactOriginalEmptyNativeFields() {
        for (String build : List.of(ExactCk3Build.CK3_12004.executableSha256(), "1.20.0.4",
                "1.20.0.4@sha256:" + ExactCk3Build.CK3_12004.executableSha256(), "1.21.0@sha256:" + SHA,
                "unqualified-data-only")) {
            for (String step : REGULAR) {
                // Legacy arbitrary snapshot spelling remains unchanged by this new-build-only DATA branch.
                var command = command(step, build, BigInteger.ONE, "legacy-snapshot", DEADLINE, EMPTY);
                var request = AdvancePrimitives.prepareRequest(command);
                assertArrayEquals(new byte[] {'{', '}'}, request.additionalFields().bytes());
                assertEquals("game.command." + step, request.requiredCapability().orElseThrow());
                assertTrue(request.preparationEvidence().isEmpty());
            }
            var save = command("save-checkpoint", build, BigInteger.ONE, "legacy-snapshot", DEADLINE, EMPTY);
            assertArrayEquals(new byte[] {'{', '}'}, FullSnapshotClockControl.additionalFields(save).bytes());
        }
    }

    @Test
    void variableArmAndCancelDoNotBorrowTheFixedEightFieldClaimOrChangeTheirOriginalCapabilities() {
        String arm = "research-arm-tactical-daily-sentinel-v1-53176992-to-53177016-speed-3-mode-terminal-a-0";
        String cancel = ClockStatusRead.CANCEL_PREFIX + "37";
        for (String build : List.of(SHA, ExactCk3Build.CK3_12004.executableSha256())) {
            for (String step : List.of(arm, cancel)) {
                var command = command(step, build, REVISION, "native:" + REVISION, DEADLINE, EMPTY);
                var request = AdvancePrimitives.prepareRequest(command);
                if (build.equals(SHA) && step.equals(arm)) {
                    assertArrayEquals(FullSnapshotDateSentinelArm.additionalFields(command).bytes(), request.additionalFields().bytes());
                    assertEquals(Set.of("date_sentinel_arm"), names(StrictJson.parse(request.additionalFields().bytes())));
                } else {
                    assertArrayEquals(new byte[] {'{', '}'}, request.additionalFields().bytes());
                }
                assertEquals(step.equals(arm) ? ClockStatusRead.ARM_CAP : ClockStatusRead.CANCEL_CAP,
                        request.requiredCapability().orElseThrow());
                assertFalse(FullSnapshotClockControl.supports(command.operation()));
                assertThrows(IllegalArgumentException.class, () -> FullSnapshotClockControl.additionalFields(command));
            }
        }
        assertFalse(FullSnapshotClockControl.supports(new OperationKey("set-speed-6")));
    }

    @Test
    void invalidNativeIdentityExtraArgumentsAndNonGameplayOriginCannotGenerateTheNewClaim() {
        for (String snapshot : List.of("snapshot-data-only", "native:1", "native:09007199254740993",
                "native:+9007199254740993")) {
            var command = command("pause-map", SHA, REVISION, snapshot, DEADLINE, EMPTY);
            assertThrows(IllegalArgumentException.class, () -> AdvancePrimitives.prepareRequest(command));
        }
        // The existing observation DATA constructor rejects zero before a command can exist.
        assertThrows(IllegalArgumentException.class,
                () -> command("pause-map", SHA, BigInteger.ZERO, "native:0", DEADLINE, EMPTY));
        var arguments = new OpportunityJson.Obj(Map.of("speed", new OpportunityJson.IntegerValue(BigInteger.ONE)));
        var extra = command("set-speed-1", SHA, REVISION, "native:" + REVISION, DEADLINE, arguments);
        assertThrows(IllegalArgumentException.class, () -> AdvancePrimitives.prepareRequest(extra));
        assertThrows(IllegalArgumentException.class, () -> FullSnapshotClockControl.additionalFields(extra));

        var source = source(SHA);
        var frontend = new FrontendIdentity(MACHINE, GAME, SESSION, BigInteger.ONE, GAME.pid(),
                new FrontendFrame.Menu(BigInteger.ONE), SOURCE_REF, SOURCE_REF);
        var expected = new FrontendExpectedPostcondition(frontend, source, "data-only/frontend-clock-negative",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("ready"), true)));
        var nonGameplay = new ActionCommand("frontend-clock-data", new CommandOrigin.Frontend(frontend), source, SESSION,
                new OperationKey("pause-map"), EMPTY, new CommandExpectation.Frontend(expected), NO_CLAIMS, DEADLINE);
        assertThrows(IllegalArgumentException.class, () -> FullSnapshotClockControl.additionalFields(nonGameplay));
        assertThrows(IllegalArgumentException.class, () -> AdvancePrimitives.prepareRequest(nonGameplay));
    }

    @Test
    void nativeOnlyDataRequestMatchesTheOrdinaryPreparationBytesIncludingSave() {
        var steps = new java.util.ArrayList<>(REGULAR); steps.add("save-checkpoint");
        for (String step : steps) {
            var command = command(step, SHA, REVISION, "native:" + REVISION, DEADLINE, EMPTY);
            byte[] originalCommand = ActionCodec.encodeCommand(command);
            var actual = FullSnapshotClockControl.request(step, "native:" + REVISION, REVISION, DEADLINE);
            var ordinary = step.equals("save-checkpoint")
                    ? new NativeRequest(step, "game.command." + step, FullSnapshotClockControl.additionalFields(command))
                    : AdvancePrimitives.prepareRequest(command);
            assertEquals(ordinary.step(), actual.step());
            assertEquals(ordinary.requiredCapability(), actual.requiredCapability());
            assertEquals("game.command." + step, actual.requiredCapability().orElseThrow());
            assertArrayEquals(ordinary.additionalFields().bytes(), actual.additionalFields().bytes());
            assertTrue(actual.preparationEvidence().isEmpty());
            assertClaim(command, actual.additionalFields());
            assertArrayEquals(originalCommand, ActionCodec.encodeCommand(command));
        }
    }

    @Test
    void nativeOnlyDataRequestKeepsUint64RevisionAndOriginalFiniteMillisecondDeadline() {
        var maxRevision = new BigInteger("18446744073709551615");
        for (BigInteger revision : List.of(BigInteger.ONE, REVISION, maxRevision)) {
            for (Instant deadline : List.of(Instant.ofEpochMilli(1), DEADLINE, Instant.ofEpochMilli(Long.MAX_VALUE))) {
                var actual = FullSnapshotClockControl.request("save-checkpoint", "native:" + revision, revision, deadline);
                JsonNode body = claim(actual.additionalFields());
                assertEquals(CLAIM_FIELDS, names(body));
                assertTrue(body.get("native_revision").isIntegralNumber());
                assertEquals(revision, body.get("native_revision").bigIntegerValue());
                assertTrue(body.get("deadline_unix_ms").isIntegralNumber());
                assertEquals(BigInteger.valueOf(deadline.toEpochMilli()), body.get("deadline_unix_ms").bigIntegerValue());
                assertEquals("native:" + revision, body.get("snapshot_id").textValue());
                assertTrue(actual.preparationEvidence().isEmpty());
            }
        }
    }

    @Test
    void nativeOnlyDataRequestRejectsUnsupportedStepsIdentityOverflowAndInvalidDeadlines() {
        for (String step : List.of("", "pause-map ", "set-speed-0", "set-speed-6", "query-fresh-full-state-v1",
                "research-arm-tactical-daily-sentinel-v1-53176992-to-53177016-speed-3-mode-terminal-a-0",
                ClockStatusRead.CANCEL_PREFIX + "37")) {
            assertThrows(IllegalArgumentException.class,
                    () -> FullSnapshotClockControl.request(step, "native:1", BigInteger.ONE, DEADLINE));
        }
        for (BigInteger revision : List.of(BigInteger.ZERO, BigInteger.ONE.negate(),
                new BigInteger("18446744073709551616"))) {
            assertThrows(IllegalArgumentException.class,
                    () -> FullSnapshotClockControl.request("pause-map", "native:" + revision, revision, DEADLINE));
        }
        for (String snapshot : List.of("", "snapshot-data-only", "native:0", "native:01", "native:+1", "native:2")) {
            assertThrows(IllegalArgumentException.class,
                    () -> FullSnapshotClockControl.request("pause-map", snapshot, BigInteger.ONE, DEADLINE));
        }
        for (Instant deadline : List.of(Instant.EPOCH, Instant.EPOCH.minusMillis(1),
                Instant.ofEpochSecond(0, 1), Instant.MAX, Instant.MIN)) {
            assertThrows(IllegalArgumentException.class,
                    () -> FullSnapshotClockControl.request("pause-map", "native:1", BigInteger.ONE, deadline));
        }
        assertThrows(NullPointerException.class, () -> FullSnapshotClockControl.request(null, "native:1", BigInteger.ONE, DEADLINE));
        assertThrows(NullPointerException.class, () -> FullSnapshotClockControl.request("pause-map", null, BigInteger.ONE, DEADLINE));
        assertThrows(NullPointerException.class, () -> FullSnapshotClockControl.request("pause-map", "native:1", null, DEADLINE));
        assertThrows(NullPointerException.class, () -> FullSnapshotClockControl.request("pause-map", "native:1", BigInteger.ONE, null));
    }

    private static void assertClaim(ActionCommand command, RawJson fields) {
        var root = StrictJson.parse(fields.bytes());
        assertEquals(Set.of("full_snapshot_clock_control"), names(root));
        var body = root.get("full_snapshot_clock_control");
        assertEquals(CLAIM_FIELDS, names(body));
        assertEquals("ck3_1210_full_clock_control_v1", body.get("schema").textValue());
        assertEquals("1.21.0", body.get("game_version").textValue());
        assertEquals("2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC",
                body.get("executable_sha256").textValue());
        assertEquals("ck3-1.21.0-msvc-x64", body.get("adapter_id").textValue());
        assertEquals("ck3-1.21.0-native-headless-main-thread", body.get("backend").textValue());
        assertEquals(command.before().frame().snapshotId(), body.get("snapshot_id").textValue());
        assertTrue(body.get("native_revision").isIntegralNumber());
        assertEquals(command.before().frame().identity().nativeRevision(), body.get("native_revision").bigIntegerValue());
        assertEquals(command.deadline().toEpochMilli(), body.get("deadline_unix_ms").longValue());
    }

    private static JsonNode claim(RawJson fields) { return StrictJson.parse(fields.bytes()).get("full_snapshot_clock_control"); }
    private static Set<String> names(JsonNode value) {
        assertTrue(value.isObject()); var names = new HashSet<String>(); value.fieldNames().forEachRemaining(names::add); return names;
    }
    private static G2Source source(String exactBuild) { return new G2Source(MACHINE, OBSERVED.toString(), exactBuild, SOURCE_REF); }
    private static ActionCommand command(String step, String exactBuild, BigInteger revision, String snapshot,
            Instant deadline, OpportunityJson.Obj arguments) {
        var before = new ProposalLifecycle.ObservationIdentity(MACHINE, GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(7), revision,
                        BigInteger.valueOf(53176992)), snapshot, BigInteger.valueOf(77), SESSION), 1);
        var source = source(exactBuild);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "data-only/full-clock-control",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("ready"), true)));
        return new ActionCommand("full-clock-data-command", before, source, SESSION, new OperationKey(step), arguments,
                expected, NO_CLAIMS, deadline);
    }
}
