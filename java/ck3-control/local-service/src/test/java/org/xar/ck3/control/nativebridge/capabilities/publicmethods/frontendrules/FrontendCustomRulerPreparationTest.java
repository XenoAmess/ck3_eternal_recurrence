package org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendRulesContract.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.FrontendGuardBinding;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesDefinitions;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesExecutor;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesInstaller;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendCustomRulerPreparation.*;

/** Existing Executor/Effects/Service and physical software archive -> sole preparation helper -> public codec.
 * No Root/Game lease is fabricated. There is no qualified selected/ineligible producer to fake in this fixture.
 */
final class FrontendCustomRulerPreparationTest {
    @TempDir Path temporary;
    private static final Instant NOW = Instant.parse("2026-10-24T07:50:00Z");
    private static final String MACHINE = "action-writer-software-fixture";
    private static final String PICK = "activate-frontend-pick-any-character-v1";

    @Test void actualProducerServicePortPreparedCodecMatchesOriginalPythonAndReceiptSerde() throws Exception {
        run("ready", h -> {
            Prepared result = FrontendCustomRulerPreparation.prepare(h.port());
            assertEquals(List.of("pick", "target", "draw:1"), h.calls);
            assertEquals(2, h.submitted); assertEquals(1, result.selections().size());
            assertSame(h.last, result.selections().getFirst());
            ObjectNode encoded = FrontendRulesCodec.object(FrontendRulesCodec.encode(result));
            assertEquals(1, encoded.path("selection_attempt_count").intValue());
            assertEquals(1, encoded.path("selection_acknowledgements").size());
            assertTrue(encoded.path("postcondition_verified").booleanValue());
            ExactRef receipt = h.archive.preserveReceipt(result.selections().getFirst());
            assertEquals(result.selections().getFirst(), h.archive.loadReceipt(receipt));
            assertEquals(encoded, FrontendRulesCodec.object(new RawJson(FrontendRulesCodec.encode(result).bytes())));
            assertEquals(original(result), encoded, "complete original Python normalizer result differs");
            return null;
        });
    }

    @Test void unavailableBeforeDispatchAndInterruptedDrawStopWithoutAnotherAttempt() throws Exception {
        run("unavailable", h -> {
            Port delegate = h.port();
            Port unavailable = new Port() {
                public Transition pickAny() throws IOException, InterruptedException { return delegate.pickAny(); }
                public Tree randomTarget() throws IOException, InterruptedException { return delegate.randomTarget(); }
                public DrawOutcome drawOnce(int attempt) { h.calls.add("unavailable:" + attempt); return new Unavailable("actual selected/ineligible read is not installed"); }
            };
            UnavailableStop stopped = assertThrows(UnavailableStop.class, () -> FrontendCustomRulerPreparation.prepare(unavailable));
            assertEquals(0, stopped.drawsCompleted()); assertEquals(1, h.submitted);
            assertEquals(List.of("pick", "target", "unavailable:1"), h.calls);
            return null;
        });
        run("interrupted", h -> {
            Port delegate = h.port();
            Port interrupted = new Port() {
                public Transition pickAny() throws IOException, InterruptedException { return delegate.pickAny(); }
                public Tree randomTarget() throws IOException, InterruptedException { return delegate.randomTarget(); }
                public DrawOutcome drawOnce(int attempt) throws InterruptedException { h.calls.add("interrupted:" + attempt); throw new InterruptedException("actual cancellation"); }
            };
            assertThrows(InterruptedException.class, () -> FrontendCustomRulerPreparation.prepare(interrupted));
            assertEquals(1, h.submitted); assertEquals(List.of("pick", "target", "interrupted:1"), h.calls);
            return null;
        });
    }

    @Test void actualNegativeTreeCannotTurnAcknowledgementIntoIneligibleOrCauseReplay() throws Exception {
        run("unknown", h -> {
            h.designerReady = false;
            UnresolvedStop stopped = assertThrows(UnresolvedStop.class, () -> FrontendCustomRulerPreparation.prepare(h.port()));
            assertEquals(List.of("pick", "target", "draw:1"), h.calls); assertEquals(2, h.submitted);
            assertEquals(0, stopped.drawsCompleted()); assertSame(h.last, stopped.action());
            assertInstanceOf(ActionState.AckReceived.class, stopped.action().state());
            assertTrue(stopped.action().ack().isPresent());
            RawJson ack = stopped.action().ack().orElseThrow().originalResultToken().orElseThrow();
            assertThrows(IllegalArgumentException.class, () -> new SelectedIneligible(stopped.action(), ack, h.lastTree));
            assertThrows(IllegalArgumentException.class, () -> new DesignerReady(stopped.action(), ack, h.lastTree));
            assertEquals(stopped.action(), h.archive.loadReceipt(h.archive.preserveReceipt(stopped.action())));
            return null;
        });
    }

    @Test void unavailableRandomTargetStopsBeforeAnyDraw() throws Exception {
        run("target", h -> {
            h.targetAvailable = false;
            UnavailableStop stopped = assertThrows(UnavailableStop.class, () -> FrontendCustomRulerPreparation.prepare(h.port()));
            assertEquals(0, stopped.drawsCompleted()); assertEquals(List.of("pick", "target"), h.calls);
            assertEquals(1, h.submitted); return null;
        });
    }

    @Test void acknowledgementSubstitutionAndDetachedTreeDoNotConstructReadyData() throws Exception {
        run("tampering", h -> {
            Prepared ready = FrontendCustomRulerPreparation.prepare(h.port());
            ActionReceipt action = ready.selections().getFirst();
            ObjectNode changed = FrontendRulesCodec.object(ready.selectionAcknowledgements().getFirst()); changed.put("accepted", false);
            assertThrows(IllegalArgumentException.class, () -> new DesignerReady(action, FrontendRulesCodec.raw(changed), ready.lobbyInspection()));
            var actual = ready.lobbyInspection().actual(); GuiTree tree = actual.value();
            GuiTree detached = new GuiTree(new Source(new Binding(tree.source().binding().bridgePid(), BigInteger.TWO), tree.source().build()),
                    tree.querySequence(), tree.scopeRootName(), tree.rootAvailable(), tree.truncated(), tree.widgets());
            Tree wrong = new Tree(new PlanningReadResult.Known<>(detached, actual.receipt(), actual.originalReceipt()));
            assertThrows(IllegalArgumentException.class, () -> new DesignerReady(action, ready.selectionAcknowledgements().getFirst(), wrong));
            assertThrows(IllegalArgumentException.class, () -> new Unavailable(" "));
            assertThrows(IllegalArgumentException.class, () -> new Unresolved(action, ""));
            return null;
        });
    }

    @FunctionalInterface private interface Work<T> { T run(Harness harness) throws Exception; }
    private <T> T run(String name, Work<T> work) throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve(name), false)) {
            return fixture.writer.locked(same -> fixture.archive.inSession(same, archive -> {
                try { return work.run(new Harness(fixture, archive, same)); }
                catch (Exception error) { throw new IllegalStateException(error); }
            }));
        }
    }

    private static final class Harness {
        final ActionWriterIntegrationFixture fixture; final ActionPorts.OutcomeArchive archive;
        final ContinuityStorePort.Session session;
        final ExactRef sourceRef; final G2Source source; final FrontendRulesDefinitions definitions;
        final FrontendRulesInstaller installed; final FrontendRulesService service;
        final List<String> calls = new ArrayList<>();
        int sequence = 1, submitted; boolean selected, designerReady = true, targetAvailable = true;
        Route route = Route.BOOKMARKS; ActionReceipt last; Tree lastTree;
        Harness(ActionWriterIntegrationFixture fixture, ActionPorts.OutcomeArchive archive, ContinuityStorePort.Session session) throws IOException {
            this.fixture = fixture; this.archive = archive; this.session = session;
            Path file = fixture.root.resolve("reviewed-fixture-source.txt"); byte[] bytes = Files.readAllBytes(file);
            sourceRef = new ExactRef(file.toString(), bytes.length, ActionCodec.sha256(bytes));
            source = new G2Source(MACHINE, NOW.toString(), Build.CK3_12003.version(), sourceRef);
            definitions = new FrontendRulesDefinitions(Build.CK3_12003, sourceRef);
            installed = new FrontendRulesInstaller(definitions, reads, archive, sourceRef, sourceRef);
            service = new FrontendRulesService(definitions, archive);
        }
        Port port() {
            return new Port() {
                public Transition pickAny() throws IOException, InterruptedException {
                    calls.add("pick"); return (Transition) service.execute(new Empty(Method.PICK_ANY), invocation());
                }
                public Tree randomTarget() throws IOException, InterruptedException {
                    calls.add("target"); return (Tree) ((ReadResponse) service.execute(new Empty(Method.TREE), invocation())).observation();
                }
                public DrawOutcome drawOnce(int attempt) throws IOException, InterruptedException {
                    calls.add("draw:" + attempt);
                    var executor = new FrontendRulesExecutor(installed, reads, actions, archive);
                    ActionReceipt action = executor.selectRandomPlayable(context("random-" + attempt)).receipt();
                    if (action.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.FrontendApplied)
                        return new DesignerReady(action, action.ack().orElseThrow().originalResultToken().orElseThrow(), lastTree);
                    return new Unresolved(action, "independent actual designer observation was not confirmed; never redraw");
                }
            };
        }
        final PlanningReadPort reads = new PlanningReadPort() {
            public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                try {
                    ObjectNode original = contract == definitions.route() ? routeBody(route) : treeBody(targetAvailable, selected && designerReady);
                    PlanningReadReceipt receipt = readReceipt(contract, original); ExactRef ref = archive.preserveRead(receipt);
                    if (contract == definitions.tree()) lastTree = new Tree(new PlanningReadResult.Known<>(definitions.tree().decode(receipt), receipt, ref));
                    return new PlanningReadResult.Known<>(contract.decode(receipt), receipt, ref);
                } catch (IOException failure) { throw new IllegalStateException(failure); }
            }
        };
        final ActionCoordinatorPort actions = new ActionCoordinatorPort() {
            public ActionReceipt execute(ActionCommand command) {
                submitted++; NativeRequest prepared = installed.effects().prepare(command);
                var attempt = new ActionState.Attempt("software-custom-ruler-" + sequence, NOW,
                        guard(command.origin().requireFrontend(), command.operation()), prepared);
                if (command.operation().value().equals(PICK)) route = Route.LOBBY; else selected = true;
                NativeActionPort.AckReceived dispatch = ack(attempt.requestId(), actionBody(command.operation().value()));
                archive.preserve(dispatch); ActionState state;
                try {
                    var observed = installed.effects().observe(command, attempt, dispatch);
                    state = new ActionState.Settled(attempt, dispatch,
                            new ActionState.FrontendApplied(((ActionPorts.FrontendObserved) observed.result()).observation()));
                } catch (IllegalArgumentException noIndependentDesigner) {
                    // Preserve the actual unresolved ACK. A negative tree is never promoted to ineligible/confirmed.
                    state = new ActionState.AckReceived(attempt, dispatch);
                }
                last = new ActionReceipt(1, submitted, command, ActionCodec.bodySha256(command), state);
                archive.preserveReceipt(last); return last;
            }
            public ActionReceipt reconcile(String actionId) { assertEquals(last.command().actionId(), actionId); return last; }
        };
        FrontendRulesService.Invocation invocation() throws IOException {
            return new FrontendRulesService.Invocation(new FrontendRulesExecutor(installed, reads, actions, archive), actions,
                    context("public"), (actual, key) -> { throw new AssertionError("preparation never starts a Game"); }, Clock.fixed(NOW, ZoneOffset.UTC));
        }
        FrontendRulesExecutor.Context context(String label) throws IOException {
            return new FrontendRulesExecutor.Context("custom-ruler-" + sequence + "-" + label, identity(), source, NOW.plusSeconds(30));
        }
        FrontendIdentity identity() throws IOException {
            int id = ++sequence;
            ExactRef packet = fixture.archive.preserveArtifact(session, ack("identity-" + id, routeBody(route)).originalPacket(), 4096);
            ExactRef hello = fixture.archive.preserveArtifact(session, ack("hello", StrictJson.object().put("fixture_notice", "hello")).originalPacket(), 4096);
            return new FrontendIdentity(MACHINE, new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993"))),
                    "custom-ruler-software", BigInteger.ONE, 42, new FrontendFrame.Menu(BigInteger.valueOf(id)), packet, hello);
        }
        GuardEvidence guard(FrontendIdentity identity, OperationKey operation) {
            return new GuardEvidence(new CommandOrigin.Frontend(identity), source, identity.frontendSessionId(), identity.connectionGeneration(),
                    operation, identity.nativeEvidence(), identity.capabilityEvidence(), "custom-ruler-software", NOW, NOW.plusSeconds(60));
        }
        <T> PlanningReadReceipt readReceipt(ReadContract<T> contract, ObjectNode original) throws IOException {
            FrontendIdentity identity = identity(); GuardEvidence evidence = guard(identity, contract.operation());
            PlanningReadGuard permission = new PlanningReadGuard(evidence, FrontendGuardBinding.digest(identity));
            PlanningReadRequest request = new PlanningReadRequest(new CommandOrigin.Frontend(identity), source, identity.frontendSessionId(),
                    contract.operation(), new OpportunityJson.Obj(java.util.Map.of()), NOW.plusSeconds(30));
            return new PlanningReadReceipt(request, contract.contractId(), "custom-read-" + sequence, permission, permission,
                    ack("custom-read-" + sequence, original));
        }
    }

    private static ObjectNode actionBody(String step) {
        return StrictJson.object().put("step", step).put("accepted", true).put("status", "acknowledged_verification_pending").put("backend_id", "native-headless");
    }
    private static ObjectNode routeBody(Route route) {
        return StrictJson.object().put("step", "query-frontend-gui-route-v1").put("accepted", true).put("status", route.wire()).put("backend_id", "native-headless");
    }
    private static ObjectNode treeBody(boolean available, boolean ready) {
        ObjectNode n = StrictJson.object().put("step", "inspect-frontend-gui-tree-v1").put("accepted", true)
                .put("status", available ? "available" : "unavailable").put("scope_root_name", "lobbyview")
                .put("root_available", available).put("truncated", false).put("backend_id", "native-headless");
        var widgets = n.putArray("widgets");
        if (available) widget(widgets.addObject(), "4/0/1/0/1");
        if (available && ready) widget(widgets.addObject(), "3/0/2/3");
        n.put("widget_count", widgets.size()); return n;
    }
    private static void widget(ObjectNode n, String path) {
        n.put("runtime_name", "").put("child_path", path).put("depth", path.split("/").length).put("child_count", 0)
                .put("vtable_rva", 1).put("effective_visible", true).put("enabled", true);
    }
    private static NativeActionPort.AckReceived ack(String request, JsonNode result) {
        ObjectNode frame = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", request).put("ok", true);
        frame.set("result", result); byte[] json = StrictJson.canonical(frame);
        byte[] packet = ByteBuffer.allocate(json.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        return new NativeActionPort.AckReceived(request, true, Optional.of(FrontendRulesCodec.raw((ObjectNode) result)), new RawJson(json), packet);
    }

    private static ObjectNode original(Prepared result) throws Exception {
        Path root = Path.of(required("xar.repository.root")); assertTrue(root.isAbsolute() && Files.isDirectory(root));
        root = root.normalize();
        Path python = Path.of(required("xar.python")); assertTrue(python.isAbsolute() && Files.isRegularFile(python));
        Path source = root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/frontend_gui_route_contract.py");
        assertEquals("a1c938b59aab6ac1e18889bf874e14708615ec4fc4fb6b4069c58c626e94c2c9", ActionCodec.sha256(Files.readAllBytes(source)));
        ObjectNode input = StrictJson.object(); input.set("before", FrontendRulesCodec.original(result.pickAny().before().receipt()));
        input.set("after", FrontendRulesCodec.original(result.pickAny().after().receipt()));
        input.set("target", FrontendRulesCodec.original(result.selectionTarget().receipt())); input.set("lobby", FrontendRulesCodec.original(result.lobbyInspection().receipt()));
        input.set("pick", FrontendRulesCodec.object(result.pickAny().acknowledgement())); input.set("draw", FrontendRulesCodec.object(result.selectionAcknowledgements().getFirst()));
        String script = """
            import json,pathlib,sys
            sys.dont_write_bytecode=True
            root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge.frontend_gui_route_contract import normalize_frontend_gui_route_v1 as route,normalize_frontend_gui_tree_inspection_v1 as tree,normalize_frontend_prepare_custom_ruler_v1 as prepare
            value=json.load(sys.stdin)
            result=prepare(value['pick'],value['draw'],before=route(value['before']),after=route(value['after']),selection_target_inspection=tree(value['target']),lobby_inspection=tree(value['lobby']))
            result['selection_attempt_count']=1;result['selection_acknowledgements']=[value['draw']]
            print(json.dumps(result,separators=(',',':')))
            """;
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-c", script, root.toString()).directory(root.toFile()).redirectErrorStream(true);
        builder.environment().put("PYTHONPATH", root.resolve("ck3_autonomous_player/src").toString()); builder.environment().put("XAR_SOURCE_REPOSITORY", root.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("PYTHONUTF8", "1");
        Process child = builder.start();
        try {
            var output = CompletableFuture.supplyAsync(() -> { try { return child.getInputStream().readNBytes(1048577); } catch(IOException error) { throw new java.io.UncheckedIOException(error); } });
            try (var stdin = child.getOutputStream()) { stdin.write(StrictJson.canonical(input)); }
            assertTrue(child.waitFor(30, TimeUnit.SECONDS)); byte[] bytes = output.get(5, TimeUnit.SECONDS);
            assertEquals(0, child.exitValue(), new String(bytes, StandardCharsets.UTF_8)); assertTrue(bytes.length <= 1048576);
            return FrontendRulesCodec.object(new RawJson(bytes));
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }
    private static String required(String key) { String value = System.getProperty(key); assertTrue(value != null && !value.isBlank(), "required actual CI input: " + key); return value; }
}
