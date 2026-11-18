package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Immutable request DATA only. No Root, Staged, Installed, observation supplier or submit authority is fabricated. */
final class RootSaveFullSnapshotRequestTest {
    private static final String SHA = ExactCk3Build.CK3_1210.executableSha256();
    private static final String SESSION = "save-request-data-session";
    private static final BigInteger REVISION = new BigInteger("9007199254740993");
    private static final Instant DEADLINE = Instant.parse("2026-11-18T00:30:00.123456789Z");
    private static final OpportunityJson.Obj EMPTY = new OpportunityJson.Obj(Map.of());

    @Test void currentBuildSaveCarriesTheOriginalFullClaimWithoutChangingTheCanonicalCommand() {
        for (String source : List.of(SHA, SHA.toUpperCase(Locale.ROOT))) {
            var command = command("save-checkpoint", source, REVISION, "native:" + REVISION, DEADLINE, EMPTY);
            byte[] original = ActionCodec.encodeCommand(command);
            var actual = RootSaveRuntime.preparedSaveRequest(command);
            assertEquals("save-checkpoint", actual.step());
            assertEquals("game.command.save-checkpoint", actual.requiredCapability().orElseThrow());
            assertTrue(actual.preparationEvidence().isEmpty());
            assertArrayEquals(FullSnapshotClockControl.request("save-checkpoint", "native:" + REVISION,
                    REVISION, DEADLINE).additionalFields().bytes(), actual.additionalFields().bytes());
            var root = StrictJson.parse(actual.additionalFields().bytes());
            assertEquals(Set.of("full_snapshot_clock_control"), names(root));
            var claim = root.get("full_snapshot_clock_control");
            assertEquals(Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend",
                    "snapshot_id", "native_revision", "deadline_unix_ms"), names(claim));
            assertEquals("ck3_1210_full_clock_control_v1", claim.get("schema").textValue());
            assertEquals("1.21.0", claim.get("game_version").textValue());
            assertEquals(SHA.toUpperCase(Locale.ROOT), claim.get("executable_sha256").textValue());
            assertEquals("ck3-1.21.0-msvc-x64", claim.get("adapter_id").textValue());
            assertEquals("ck3-1.21.0-native-headless-main-thread", claim.get("backend").textValue());
            assertEquals("native:" + REVISION, claim.get("snapshot_id").textValue());
            assertTrue(claim.get("native_revision").isIntegralNumber());
            assertEquals(REVISION, claim.get("native_revision").bigIntegerValue());
            assertEquals(DEADLINE.toEpochMilli(), claim.get("deadline_unix_ms").longValue());
            assertEquals(CheckpointRequestFactory.OBSERVER_SCHEMA, command.expected().observerSchema());
            assertEquals(3, command.expected().values().size());
            assertArrayEquals(original, ActionCodec.encodeCommand(command));
        }
    }

    @Test void historicalAndUnknownSourceSpellingsRetainTheOriginalEmptySaveFields() {
        for (String source : List.of(ExactCk3Build.CK3_12004.executableSha256(), "1.20.0.4",
                "1.20.0.4@sha256:" + ExactCk3Build.CK3_12004.executableSha256(),
                "1.21.0@sha256:" + SHA, "unqualified-data-only")) {
            var actual = RootSaveRuntime.preparedSaveRequest(
                    command("save-checkpoint", source, BigInteger.ONE, "historical-snapshot", DEADLINE, EMPTY));
            assertArrayEquals(new byte[]{'{', '}'}, actual.additionalFields().bytes());
            assertEquals("save-checkpoint", actual.step());
            assertEquals("game.command.save-checkpoint", actual.requiredCapability().orElseThrow());
            assertTrue(actual.preparationEvidence().isEmpty());
        }
    }

    @Test void saveDataCannotRouteAnotherOperationExtraArgumentsOrMalformedCurrentFrame() {
        for (String step : List.of("pause-map", "resume-map", "set-speed-1",
                "research-arm-tactical-daily-sentinel-v1-53176992-to-53177016-speed-3-mode-terminal-a-0")) {
            var command = command(step, SHA, REVISION, "native:" + REVISION, DEADLINE, EMPTY);
            assertThrows(IllegalArgumentException.class, () -> RootSaveRuntime.preparedSaveRequest(command));
        }
        var extra = new OpportunityJson.Obj(Map.of("path", new OpportunityJson.Text("data-only.ck3")));
        assertThrows(IllegalArgumentException.class, () -> RootSaveRuntime.preparedSaveRequest(
                command("save-checkpoint", SHA, REVISION, "native:" + REVISION, DEADLINE, extra)));
        assertThrows(IllegalArgumentException.class, () -> RootSaveRuntime.preparedSaveRequest(
                command("save-checkpoint", SHA, REVISION, "native:1", DEADLINE, EMPTY)));
        assertThrows(IllegalArgumentException.class, () -> RootSaveRuntime.preparedSaveRequest(
                command("save-checkpoint", SHA, BigInteger.ZERO, "native:0", DEADLINE, EMPTY)));
        for (Instant invalid : List.of(Instant.EPOCH, Instant.EPOCH.minusMillis(1), Instant.MAX)) {
            assertThrows(IllegalArgumentException.class, () -> RootSaveRuntime.preparedSaveRequest(
                    command("save-checkpoint", SHA, REVISION, "native:" + REVISION, invalid, EMPTY)));
        }
        assertThrows(NullPointerException.class, () -> RootSaveRuntime.preparedSaveRequest(null));
    }

    private static Set<String> names(com.fasterxml.jackson.databind.JsonNode object) {
        assertTrue(object.isObject()); var names = new HashSet<String>(); object.fieldNames().forEachRemaining(names::add); return names;
    }

    private static ActionCommand command(String step, String exactBuild, BigInteger revision,
            String snapshot, Instant deadline, OpportunityJson.Obj arguments) {
        var game = new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE));
        var before = new ObservationIdentity("save-request-data", game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(7),
                        revision, BigInteger.valueOf(53176992)), snapshot, BigInteger.valueOf(77), SESSION), 1);
        var source = new G2Source("save-request-data", "2026-11-18T00:00:00Z", exactBuild,
                new ExactRef("data-only/save-request-source.java", 1, "0".repeat(64)));
        var expected = new ExpectedPostcondition(1, before, source, CheckpointRequestFactory.OBSERVER_SCHEMA,
                List.of(new ExpectedInteger(new FieldKey("date_raw"), before.frame().identity().dateRaw()),
                        new ExpectedInteger(new FieldKey("played_character_id"), before.frame().identity().player()),
                        new ExpectedBoolean(new FieldKey("checkpoint_pair_verified"), true)));
        return new ActionCommand("save-request-data-command", before, source, SESSION, new OperationKey(step),
                arguments, expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), deadline);
    }
}
