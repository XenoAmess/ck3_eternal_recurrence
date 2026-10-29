package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;

/** Software scope: original Python producer -> actual Java effect -> physical archive -> original replay. */
final class FrontendRulesEffectArchiveTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final Instant NOW = Instant.parse("2026-10-23T17:35:00Z");
    private static final String MACHINE = "action-writer-software-fixture";
    private static final GameGeneration GAME = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    @TempDir Path temporary;
    private static final String PRODUCER = """
        import json,pathlib,runpy,sys
        root=pathlib.Path(sys.argv[1]).resolve()
        sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
        source=runpy.run_path(str(root/'ck3_autonomous_player'/'tests'/'unit'/'test_frontend_game_rules_control_contract.py'))
        harness=source['driver_harness']()
        before=source['values']()
        selected=harness.select_frontend_game_rule_v1('zg361_enabled','zg361_on','zg361_off')
        print(json.dumps({'before':before,'window':source['window'](),'selected':selected},separators=(',',':')))
        """;
    private static ObjectNode originalProducer() throws Exception {
        String configured = System.getProperty("xar.repository.root");
        assertNotNull(configured, "actual original workspace required; this test cannot pass by skipping");
        assertFalse(configured.isBlank(), "xar.repository.root is mandatory");
        Path root = Path.of(configured).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py")));
        String python = System.getProperty("xar.python"); assertNotNull(python, "xar.python is mandatory"); assertFalse(python.isBlank(), "xar.python is mandatory");
        Process child = new ProcessBuilder(python, "-X", "utf8", "-c", PRODUCER, root.toString()).redirectErrorStream(true).start();
        assertTrue(child.waitFor(30, TimeUnit.SECONDS), "original producer timeout");
        byte[] bytes = child.getInputStream().readNBytes(1024 * 1024); assertEquals(0, child.exitValue(), new String(bytes, StandardCharsets.UTF_8));
        return FrontendRulesCodec.object(new RawJson(bytes));
    }
    @Test void selectionNeedsIndependentReadAndSurvivesPhysicalArchiveReplay() throws Exception {
        ObjectNode original = originalProducer();
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("selection"), false)) {
            fixture.writer.locked(session -> fixture.archive.inSession(session, archive -> {
                try {
                    Path sourceFile = fixture.root.resolve("reviewed-fixture-source.txt"); byte[] sourceBytes = Files.readAllBytes(sourceFile);
                    ExactRef sourceRef = new ExactRef(sourceFile.toString(), sourceBytes.length, ActionCodec.sha256(sourceBytes));
                    var source = new G2Source(MACHINE, NOW.toString(), "1.20.0.3", sourceRef);
                    var definitions = new FrontendRulesDefinitions(Build.CK3_12003, sourceRef);
                    var beforeRead = read(fixture.archive, session, source, definitions.selections(), 1, original.get("before"));
                    var windowRead = read(fixture.archive, session, source, definitions.window(), 2, original.get("window"));
                    var origin = identity(fixture.archive, session, 3);
                    var afterRead = read(fixture.archive, session, source, definitions.selections(), 5, original.get("selected").get("observation"));
                    ExactRef afterRef = archive.preserveRead(afterRead);
                    var reads = new PlanningReadPort() {
                        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                            assertEquals(definitions.selections().operation(), request.operation());
                            return new PlanningReadResult.Known<>(contract.decode(afterRead), afterRead, afterRef);
                        }
                    };
                    var effects = new FrontendRulesEffects(definitions, reads, archive);
                    var select = new FrontendRulesRequests.SelectRule(new ScriptKey("zg361_enabled"), new ScriptKey("zg361_on"), new ScriptKey("zg361_off"));
                    var arguments = FrontendRulesArguments.selection(new FrontendRulesArguments.Select(select, archive.preserveRead(beforeRead), archive.preserveRead(windowRead)));
                    var expected = effects.expected(origin, source, FrontendRulesRequests.Primitive.SELECT_RULE, arguments);
                    var command = new ActionCommand("selection-original", new CommandOrigin.Frontend(origin), source, origin.frontendSessionId(),
                            FrontendRulesRequests.Primitive.SELECT_RULE.operation(), arguments, new CommandExpectation.Frontend(expected), new Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
                    var attempt = new ActionState.Attempt("selection-action-request", NOW, guard(origin, source, command.operation(), NOW), effects.prepare(command));
                    var unknown = new NativeActionPort.Unknown(attempt.requestId(), "original return lost", new byte[0], Optional.empty());
                    assertInstanceOf(ActionPorts.Pending.class, effects.observe(command, attempt, unknown).result(), "missing ACK cannot become an effect from a constructed expectation");
                    var ack = ack(attempt.requestId(), original.get("selected").get("acknowledgement")); archive.preserve(ack);
                    var projected = effects.observe(command, attempt, ack);
                    var observed = assertInstanceOf(ActionPorts.FrontendObserved.class, projected.result()).observation();
                    assertEquals(1, observed.supportingEvidence().size());
                    assertTrue(observed.actual().contains(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("applied_settings_proven"), false)));
                    var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, ack, new ActionState.FrontendApplied(observed)));
                    ExactRef actualReceipt = archive.preserveReceipt(receipt); assertEquals(receipt, archive.loadReceipt(actualReceipt));
                    var verifier = effects.archivedVerifiers(sourceRef).stream().filter(value -> value.operation().equals(command.operation())).findFirst().orElseThrow();
                    verifier.verifier().verify(session.head(), archive.loadReceipt(actualReceipt), archive);
                    var changed = (ObjectNode) original.get("selected").get("observation").deepCopy();
                    ((ObjectNode) changed.get("selections").get(0)).put("selected_setting_key", "unrelated_setting");
                    var wrong = read(fixture.archive, session, source, definitions.selections(), 6, changed); ExactRef wrongRef = archive.preserveRead(wrong);
                    var wrongReads = new PlanningReadPort() {
                        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) { return new PlanningReadResult.Known<>(contract.decode(wrong), wrong, wrongRef); }
                    };
                    assertThrows(IllegalArgumentException.class, () -> new FrontendRulesEffects(definitions, wrongReads, archive).observe(command, attempt, ack), "unrelated or wrong target setting must not settle");
                    return null;
                } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
            }));
        }
    }
    private static <T> PlanningReadReceipt read(NativeOutcomeArchive archive, org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session session,
            G2Source source, ReadContract<T> contract, int sequence, JsonNode result) throws IOException {
        var identity = identity(archive, session, sequence); var evidence = guard(identity, source, contract.operation(), NOW.plusMillis(sequence));
        var permission = new PlanningReadGuard(evidence, FrontendGuardBinding.digest(identity));
        var request = new PlanningReadRequest(new CommandOrigin.Frontend(identity), source, identity.frontendSessionId(), contract.operation(), FrontendRulesArguments.empty(), NOW.plusSeconds(20));
        var receipt = new PlanningReadReceipt(request, contract.contractId(), "native-read-" + sequence, permission, permission, ack("native-read-" + sequence, result));
        archive.preserveRead(receipt); return receipt;
    }
    private static FrontendIdentity identity(NativeOutcomeArchive archive, org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session session, int sequence) throws IOException {
        var controlledRoute = JSON.createObjectNode(); controlledRoute.put("route", "bookmarks"); controlledRoute.put("fixture_sequence", sequence);
        ExactRef packet = archive.preserveArtifact(session, ack("controlled-route-" + sequence, controlledRoute).originalPacket(), 4096);
        var controlledHello = JSON.createObjectNode(); controlledHello.put("fixture_notice", "hello");
        ExactRef hello = archive.preserveArtifact(session, ack("controlled-hello", controlledHello).originalPacket(), 4096);
        return new FrontendIdentity(MACHINE, GAME, "frontend-test", BigInteger.valueOf(5), GAME.pid(), new FrontendFrame.Menu(BigInteger.valueOf(sequence)), packet, hello);
    }
    private static GuardEvidence guard(FrontendIdentity identity, G2Source source, OperationKey operation, Instant observedAt) {
        return new GuardEvidence(new CommandOrigin.Frontend(identity), source, identity.frontendSessionId(), identity.connectionGeneration(), operation,
                identity.nativeEvidence(), identity.capabilityEvidence(), "fixture-authority", observedAt, NOW.plusSeconds(20));
    }
    private static NativeActionPort.AckReceived ack(String request, JsonNode result) throws IOException {
        ObjectNode frame = JSON.createObjectNode(); frame.put("type", "command_result"); frame.put("protocol_version", 1); frame.put("request_id", request); frame.put("ok", true); frame.set("result", result);
        byte[] body = JSON.writeValueAsBytes(frame); byte[] packet = ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        return new NativeActionPort.AckReceived(request, true, Optional.of(new RawJson(JSON.writeValueAsBytes(result))), new RawJson(body), packet);
    }
}
