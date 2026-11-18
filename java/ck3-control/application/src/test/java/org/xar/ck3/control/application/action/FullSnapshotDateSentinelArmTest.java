package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Request DATA only: no actual frame, lease, receiver, Native queue or Game permission is constructed. */
final class FullSnapshotDateSentinelArmTest {
    private static final String SHA = ExactCk3Build.CK3_1210.executableSha256();
    private static final String SESSION = "date-arm-data-session";
    private static final BigInteger REVISION = new BigInteger("9007199254740993");
    private static final Instant DEADLINE = Instant.parse("2026-11-18T01:30:00.123456789Z");
    private static final OpportunityJson.Obj EMPTY = new OpportunityJson.Obj(Map.of());
    private static final String ARM = step(53176992, 53177016, 3);

    @Test void exactBuildOrdinaryArmAndNativeOnlyDataHaveIdenticalEightFieldClaims() {
        for (String source : List.of(SHA, SHA.toUpperCase(Locale.ROOT))) {
            for (int speed = 1; speed <= 5; speed++) {
                String operation = step(53176992, 53177016, speed);
                var command = command(operation, source, 53176992, EMPTY);
                byte[] original = ActionCodec.encodeCommand(command);
                var actual = AdvancePrimitives.prepareRequest(command);
                var direct = FullSnapshotDateSentinelArm.request(operation, "native:" + REVISION, REVISION, DEADLINE);
                assertTrue(FullSnapshotDateSentinelArm.supports(command.operation()));
                assertFalse(FullSnapshotClockControl.supports(command.operation()));
                assertEquals(operation, actual.step());
                assertEquals(ClockStatusRead.ARM_CAP, actual.requiredCapability().orElseThrow());
                assertTrue(actual.preparationEvidence().isEmpty());
                assertArrayEquals(direct.additionalFields().bytes(), actual.additionalFields().bytes());
                var root = StrictJson.parse(actual.additionalFields().bytes());
                assertEquals(Set.of("date_sentinel_arm"), names(root));
                var claim = root.get("date_sentinel_arm");
                assertEquals(Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend",
                        "snapshot_id", "native_revision", "deadline_unix_ms"), names(claim));
                assertEquals("ck3_1210_date_sentinel_arm_v1", claim.get("schema").textValue());
                assertEquals("1.21.0", claim.get("game_version").textValue());
                assertEquals(SHA.toUpperCase(Locale.ROOT), claim.get("executable_sha256").textValue());
                assertEquals("ck3-1.21.0-msvc-x64", claim.get("adapter_id").textValue());
                assertEquals("ck3-1.21.0-native-headless-main-thread", claim.get("backend").textValue());
                assertEquals("native:" + REVISION, claim.get("snapshot_id").textValue());
                assertTrue(claim.get("native_revision").isIntegralNumber());
                assertEquals(REVISION, claim.get("native_revision").bigIntegerValue());
                assertEquals(DEADLINE.toEpochMilli(), claim.get("deadline_unix_ms").longValue());
                assertArrayEquals(original, ActionCodec.encodeCommand(command));
            }
        }
    }

    @Test void legacyArmModesAndUnknownSourceSpellingsKeepTheirOriginalEmptyFields() {
        for (String source : List.of(ExactCk3Build.CK3_12004.executableSha256(), "1.20.0.4",
                "1.21.0@sha256:" + SHA, "unqualified-data-only")) {
            for (String operation : List.of(ARM, step(0, 24, 1),
                    "research-arm-tactical-daily-sentinel-v1-53176992-to-53177016-speed-2-mode-decision-a-1-7")) {
                int date = AdvancePrimitives.armSpec(operation).startingDateRaw();
                var actual = AdvancePrimitives.prepareRequest(command(operation, source, date, EMPTY));
                assertArrayEquals(new byte[]{'{', '}'}, actual.additionalFields().bytes());
                assertEquals(ClockStatusRead.ARM_CAP, actual.requiredCapability().orElseThrow());
            }
        }
    }

    @Test void dateOnlyGrammarRejectsAliasesUnsupportedModesAndInt32OrDayBoundaries() {
        for (String invalid : List.of(step(0, 24, 1), step(25, 1, 1), step(1, 24, 1), step(1, 1, 1),
                "research-arm-tactical-daily-sentinel-v1-01-to-25-speed-1-mode-terminal-a-0",
                "research-arm-tactical-daily-sentinel-v1-1-to-025-speed-1-mode-terminal-a-0",
                "research-arm-tactical-daily-sentinel-v1-2147483648-to-2147483672-speed-1-mode-terminal-a-0",
                "research-arm-tactical-daily-sentinel-v1-2147483624-to-2147483648-speed-1-mode-terminal-a-0",
                "research-arm-tactical-daily-sentinel-v1-1-to-25-speed-0-mode-terminal-a-0",
                "research-arm-tactical-daily-sentinel-v1-1-to-25-speed-6-mode-terminal-a-0",
                "research-arm-tactical-daily-sentinel-v1-1-to-25-speed-1-mode-decision-a-0",
                "research-arm-tactical-daily-sentinel-v1-1-to-25-speed-1-mode-terminal-a-1-7",
                "research-arm-tactical-daily-sentinel-v1-1-to-25-speed-1-mode-terminal-a-0-7",
                "pause-map", ClockStatusRead.CANCEL_PREFIX + "7")) {
            assertFalse(FullSnapshotDateSentinelArm.supports(new OperationKey(invalid)));
            assertThrows(IllegalArgumentException.class,
                    () -> FullSnapshotDateSentinelArm.request(invalid, "native:" + REVISION, REVISION, DEADLINE));
        }
        assertTrue(FullSnapshotDateSentinelArm.supports(new OperationKey(step(2147483623, Integer.MAX_VALUE, 5))));
    }

    @Test void claimRetainsExactUint64RevisionAndOriginalDeadlineWithoutReadingAClock() {
        for (BigInteger revision : List.of(BigInteger.ONE, REVISION, new BigInteger("18446744073709551615"))) {
            for (Instant deadline : List.of(Instant.ofEpochMilli(1), DEADLINE, Instant.ofEpochMilli(Long.MAX_VALUE))) {
                var body = StrictJson.parse(FullSnapshotDateSentinelArm.request(ARM, "native:" + revision,
                        revision, deadline).additionalFields().bytes()).get("date_sentinel_arm");
                assertTrue(body.get("native_revision").isIntegralNumber());
                assertEquals(revision, body.get("native_revision").bigIntegerValue());
                assertTrue(body.get("deadline_unix_ms").isIntegralNumber());
                assertEquals(BigInteger.valueOf(deadline.toEpochMilli()), body.get("deadline_unix_ms").bigIntegerValue());
            }
        }
        for (BigInteger revision : List.of(BigInteger.ZERO, BigInteger.ONE.negate(), new BigInteger("18446744073709551616"))) {
            assertThrows(IllegalArgumentException.class,
                    () -> FullSnapshotDateSentinelArm.request(ARM, "native:" + revision, revision, DEADLINE));
        }
        for (String snapshot : List.of("native:0", "native:01", "native:+1", "snapshot-data-only")) {
            assertThrows(IllegalArgumentException.class,
                    () -> FullSnapshotDateSentinelArm.request(ARM, snapshot, BigInteger.ONE, DEADLINE));
        }
        for (Instant deadline : List.of(Instant.EPOCH, Instant.EPOCH.minusMillis(1), Instant.MAX, Instant.MIN)) {
            assertThrows(IllegalArgumentException.class,
                    () -> FullSnapshotDateSentinelArm.request(ARM, "native:1", BigInteger.ONE, deadline));
        }
    }

    @Test void originalCommandDateAndEmptyArgumentsAreRequiredBeforeClaimPreparation() {
        assertThrows(IllegalArgumentException.class,
                () -> AdvancePrimitives.prepareRequest(command(ARM, SHA, 53177016, EMPTY)));
        var extra = new OpportunityJson.Obj(Map.of("deadline", new OpportunityJson.IntegerValue(BigInteger.ONE)));
        assertThrows(IllegalArgumentException.class,
                () -> AdvancePrimitives.prepareRequest(command(ARM, SHA, 53176992, extra)));
        String decision = "research-arm-tactical-daily-sentinel-v1-53176992-to-53177016-speed-3-mode-decision-a-0";
        assertThrows(IllegalArgumentException.class,
                () -> AdvancePrimitives.prepareRequest(command(decision, SHA, 53176992, EMPTY)));
    }

    @Test void cancelAndFixedClockRemainOnTheirDistinctExistingPreparationPaths() {
        var cancel = AdvancePrimitives.prepareRequest(command(ClockStatusRead.CANCEL_PREFIX + "7", SHA, 53176992, EMPTY));
        assertArrayEquals(new byte[]{'{', '}'}, cancel.additionalFields().bytes());
        assertEquals(ClockStatusRead.CANCEL_CAP, cancel.requiredCapability().orElseThrow());
        var pause = AdvancePrimitives.prepareRequest(command("pause-map", SHA, 53176992, EMPTY));
        assertEquals(Set.of("full_snapshot_clock_control"), names(StrictJson.parse(pause.additionalFields().bytes())));
        assertThrows(IllegalArgumentException.class,
                () -> FullSnapshotDateSentinelArm.additionalFields(command("pause-map", SHA, 53176992, EMPTY)));
        assertThrows(IllegalArgumentException.class,
                () -> FullSnapshotClockControl.additionalFields(command(ARM, SHA, 53176992, EMPTY)));
    }

    private static String step(int start, int target, int speed) {
        return FullSnapshotDateSentinelArm.PREFIX + start + "-to-" + target + "-speed-" + speed + "-mode-terminal-a-0";
    }
    private static Set<String> names(com.fasterxml.jackson.databind.JsonNode object) {
        assertTrue(object.isObject()); var names = new HashSet<String>(); object.fieldNames().forEachRemaining(names::add); return names;
    }
    private static ActionCommand command(String step, String exactBuild, int dateRaw, OpportunityJson.Obj arguments) {
        var before = new ObservationIdentity("date-arm-data", new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(7), REVISION,
                        BigInteger.valueOf(dateRaw)), "native:" + REVISION, BigInteger.valueOf(77), SESSION), 1);
        var source = new G2Source("date-arm-data", "2026-11-18T01:00:00Z", exactBuild,
                new ExactRef("data-only/date-arm-source.java", 1, "0".repeat(64)));
        var expected = new ExpectedPostcondition(1, before, source, "data-only/date-arm-poststate",
                List.of(new ExpectedBoolean(new FieldKey("ready"), true)));
        return new ActionCommand("date-arm-data-command", before, source, SESSION, new OperationKey(step), arguments,
                expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), DEADLINE);
    }
}
