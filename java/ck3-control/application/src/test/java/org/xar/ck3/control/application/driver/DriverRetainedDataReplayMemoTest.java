package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;

/** Mechanism tests only. A fake access installed through package scope is not Root source authorization. */
final class DriverRetainedDataReplayMemoTest {
    private static final Instant NOW = Instant.parse("2026-11-16T12:00:00Z");
    private static final String DRIVER = """
            {"format_version":2,"pipe_name":"memo-software","bridge_pid":123,"episode_character_id":73,"episode_run_id":"memo-episode",
             "last_checkpoint":null,"command_history":[],"rollback_war_failure":null,"managed_restore_transaction":null,
             "succession_expectation":null,"succession_lifecycle":null,"campaign_goal":{"name":"memo-software"},"rollback_war_failures":null}
            """;
    private static final String NATIVE = """
            {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
             "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
             "active_wars":[],"player_armies":[],"diagnostics":{}}
            """;
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static Obj reference(ExactRef value) { return org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities.referenceJson(value); }
    private static Obj node(com.fasterxml.jackson.databind.JsonNode value) {
        return DriverJson.object(StrictJson.canonical(value), StrictJson.EXPLICIT_MAX_BYTES);
    }

    private static final class Fixture {
        final Map<ExactRef, RawJson> materials = new LinkedHashMap<>();
        final Map<ExactRef, byte[]> packets = new LinkedHashMap<>();
        final Access access = new Access();
        int reads;
        final ActionPorts.OutcomeArchive archive = archive();
        private ActionPorts.OutcomeArchive archive() {
            return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(getClass().getClassLoader(),
                    new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                        return switch (method.getName()) {
                            case "loadMaterial", "loadFullMaterial" -> {
                                ExactRef ref = (ExactRef) args[0]; read(ref); yield Optional.ofNullable(materials.get(ref)).orElseThrow();
                            }
                            case "loadNativeFrame" -> { ExactRef ref = (ExactRef) args[0]; read(ref); yield packets.get(ref).clone(); }
                            case "scopedDriverDecoder" -> null;
                            case "toString" -> "software DATA archive";
                            case "hashCode" -> System.identityHashCode(proxy);
                            case "equals" -> proxy == args[0];
                            default -> throw new AssertionError("pure replay unexpectedly requested " + method.getName());
                        };
                    });
        }
        private void read(ExactRef reference) { reads++; access.record(Set.of(reference)); }
        ExactRef material(RawJson value) {
            byte[] raw = value.bytes(); ExactRef ref = new ExactRef("memory/" + DriverJson.sha256(raw), raw.length, DriverJson.sha256(raw));
            materials.put(ref, value); return ref;
        }
        Obj strategy(Obj auxiliary) {
            byte[] body = CrossRunPlanning.encodeState(CrossRunPlanning.empty());
            ExactRef archived = material(new RawJson(body));
            Obj strategy = DriverJson.object(body, CrossRunPlanning.MAX_BYTES);
            ExactRef proof = material(new RawJson(DriverJson.encode(new Obj(Map.of("schema", new Text("xar.driver-persistent-planning-source/v2"),
                    "mode", new Text("CROSS_RUN"), "body", reference(archived), "archived_body", reference(archived),
                    "canonical_head", reference(archived), "strategy", strategy)))));
            return auxiliary.with("one_life_strategy", strategy).with(DriverPersistentPlanningState.STRATEGY_SOURCE, reference(proof));
        }
        Obj cooldown() {
            byte[] rawDriver = DriverStateSnapshot.decodeComplete(bytes(DRIVER)).encode();
            var driver = new RawJson(rawDriver); ExactRef driverRef = material(driver);
            var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
            var known = DriverFactsRepository.imported(driverRef, rawDriver, 3, 7, game, new Obj(Map.of()));
            byte[] packetJson = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"memo-snapshot\",\"revision\":9,\"state\":" + NATIVE.strip() + "}");
            byte[] packet = ByteBuffer.allocate(packetJson.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(packetJson.length).put(packetJson).array();
            ExactRef nativeRef = new ExactRef("memory/native-" + DriverJson.sha256(packet), packet.length, DriverJson.sha256(packet));
            packets.put(nativeRef, packet);
            var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("memo-machine", game, BigInteger.valueOf(5), "memo-session"),
                    "memo-snapshot", BigInteger.valueOf(9), new RawJson(bytes(NATIVE.strip())), packet, NOW);
            var source = new G2Source("memo-machine", NOW.toString(), "memo-source", driverRef);
            RawJson manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.TWO, 1, source, new Obj(Map.of()), driverRef);
            ExactRef manifestRef = material(manifest);
            var frame = assertInstanceOf(DriverObservationAssembler.Complete.class,
                    DriverObservationEvidenceReader.replayOriginals(manifestRef, manifest, driver, packet, nativeRef));
            var identity = DeclarationOpportunityCooldown.frame(frame);
            var snapshot = DeclarationOpportunityCooldown.snapshot(DriverJson.toNode(frame.semantic()));
            var state = DeclarationOpportunityCooldown.decode(com.fasterxml.jackson.databind.node.NullNode.getInstance(), identity);
            var reduction = DeclarationOpportunityCooldown.view(state, snapshot, identity);
            Obj basis = new Obj(Map.of("manifest", reference(manifestRef), "native", reference(nativeRef)));
            Obj input = new Obj(Map.of("configured_path", new Text(Path.of("memo-software").toAbsolutePath().resolve(DeclarationOpportunityCooldown.LEGACY_FILENAME).toString()),
                    "observed_at", new Text(NOW.toString()), "original", Nil.INSTANCE, "saved", Nil.INSTANCE, "baseline_receipts", new Arr(List.of())));
            Obj encodedState = node(DeclarationOpportunityCooldown.encode(reduction.state()));
            Obj view = node(DeclarationOpportunityCooldown.encodeView(reduction.view()));
            ExactRef proof = material(new RawJson(DriverJson.encode(new Obj(Map.of("schema", new Text("xar.driver-persistent-planning-source/v2"),
                    "mode", new Text("INITIAL"), "previous", Nil.INSTANCE, "frame", basis, "input", input,
                    "state", encodedState, "view", view, "processed", new Arr(List.of()))))));
            reads = 0;
            return new Obj(Map.of(DriverPersistentPlanningState.COOLDOWN_STATE, encodedState,
                    DeclarationOpportunityCooldown.VIEW_KEY, view, DriverPersistentPlanningState.COOLDOWN_SOURCE, reference(proof)));
        }
        <T> T scope(ActionPorts.CheckedArchiveRead<T> work) throws IOException {
            return DriverPersistentPlanningState.inRetainedDataReplayScope(access, archive, work);
        }
        final class Trace { final Set<ExactRef> references = new LinkedHashSet<>(); }
        final class Access implements DriverPersistentPlanningState.RetainedDataReplayAccess {
            final Deque<Trace> traces = new ArrayDeque<>();
            final List<Set<ExactRef>> verifiedDependencies = new ArrayList<>();
            int captures, closes;
            boolean eligible = true, retained = true, complete = true, failClose;
            Runnable afterClose = () -> { }, beforeVerify = () -> { };
            Set<ExactRef> overrideDependencies;
            @Override public boolean accepts(ActionPorts.OutcomeArchive value) { return eligible && value == archive; }
            @Override public void requireCurrent() { }
            @Override public Object beginCapture() { captures++; Trace trace = new Trace(); traces.push(trace); return trace; }
            @Override public Optional<Set<ExactRef>> dependencies(Object capture) {
                assertSame(capture, traces.peek());
                return complete ? Optional.of(overrideDependencies == null ? Set.copyOf(((Trace) capture).references) : overrideDependencies) : Optional.empty();
            }
            @Override public void closeCapture(Object capture) throws IOException {
                assertSame(capture, traces.pop()); closes++; afterClose.run();
                if (failClose) { failClose = false; throw new IOException("software trace close failed"); }
            }
            @Override public boolean verify(Set<ExactRef> dependencies) {
                beforeVerify.run(); verifiedDependencies.add(Set.copyOf(dependencies));
                if (!retained || !eligible) return false;
                record(dependencies); return true;
            }
            void record(Set<ExactRef> dependencies) { for (Trace trace : traces) trace.references.addAll(dependencies); }
        }
    }

    @Test void wholeHeaderAndCompleteAuxiliaryAreDistinctFromTheCooldownSource() throws Exception {
        var f = new Fixture(); Obj auxiliary = f.strategy(f.cooldown());
        f.scope(archive -> {
            DriverPersistentPlanningState.replay(auxiliary, archive);
            Set<ExactRef> complete = f.access.verifiedDependencies.getLast();
            assertTrue(complete.containsAll(f.materials.keySet()), "header and nested cooldown originals must share the complete trace");
            int reads = f.reads;
            DriverPersistentPlanningState.replay(new Obj(auxiliary.members()), archive);
            assertEquals(reads, f.reads);
            Obj changedHeader = auxiliary.with("war_declaration_continuity_v1", new Obj(Map.of()));
            assertThrows(IllegalArgumentException.class, () -> DriverPersistentPlanningState.replay(changedHeader, archive));
            DriverPersistentPlanningState.replay(auxiliary, archive);
            assertTrue(f.reads > reads, "a failed header clears the prior complete proof");
            return null;
        });
    }

    @Test void finalAuxiliaryMismatchCannotPublishACompleteProof() throws Exception {
        var f = new Fixture(); Obj auxiliary = f.cooldown();
        Obj wrong = auxiliary.with(DeclarationOpportunityCooldown.VIEW_KEY, Nil.INSTANCE);
        f.scope(archive -> {
            for (int i = 0; i < 2; i++) {
                var failure = assertThrows(IllegalArgumentException.class, () -> DriverPersistentPlanningState.replay(wrong, archive));
                assertEquals("persistent cooldown auxiliary differs from its complete source chain", failure.getMessage());
            }
            assertEquals(2, f.access.captures); assertEquals(2, f.access.closes);
            DriverPersistentPlanningState.replay(auxiliary, archive);
            int reads = f.reads; DriverPersistentPlanningState.replay(auxiliary, archive); assertEquals(reads, f.reads);
            return null;
        });
    }

    @Test void traceCloseFailureClearsAnEarlierCompleteProofAndDoesNotPublishTheNewOne() throws Exception {
        var f = new Fixture(); Obj first = f.strategy(new Obj(Map.of())); Obj second = first.with("unrelated", new Bool(true));
        f.scope(archive -> {
            DriverPersistentPlanningState.replay(first, archive);
            f.access.failClose = true;
            assertThrows(UncheckedIOException.class, () -> DriverPersistentPlanningState.replay(second, archive));
            int captures = f.access.captures;
            DriverPersistentPlanningState.replay(first, archive); DriverPersistentPlanningState.replay(second, archive);
            assertEquals(captures + 2, f.access.captures);
            return null;
        });
    }

    @Test void aHitContributesItsWholeClosureToAnAlreadyOpenOuterTrace() throws Exception {
        var f = new Fixture(); Obj auxiliary = f.strategy(new Obj(Map.of()));
        f.scope(archive -> {
            DriverPersistentPlanningState.replay(auxiliary, archive);
            Object outer = f.access.beginCapture(); int reads = f.reads;
            DriverPersistentPlanningState.replay(auxiliary, archive);
            assertEquals(reads, f.reads);
            assertEquals(f.materials.keySet(), f.access.dependencies(outer).orElseThrow());
            f.access.closeCapture(outer); return null;
        });
    }

    @Test void missingCustodyAndUnknownDependenciesBothKeepTheFullReader() throws Exception {
        var f = new Fixture(); Obj auxiliary = f.strategy(new Obj(Map.of()));
        f.scope(archive -> {
            DriverPersistentPlanningState.replay(auxiliary, archive);
            f.access.retained = false; int reads = f.reads;
            DriverPersistentPlanningState.replay(auxiliary, archive); assertTrue(f.reads > reads);
            f.access.retained = true; f.access.complete = false; reads = f.reads;
            DriverPersistentPlanningState.replay(auxiliary, archive); assertTrue(f.reads > reads);
            reads = f.reads; DriverPersistentPlanningState.replay(auxiliary, archive); assertTrue(f.reads > reads);
            return null;
        });
    }

    @Test void uncertainAuxiliaryAndIneligibleCapturesDoNotAddEncodingOrValidationFailures() throws Exception {
        var f = new Fixture(); Obj auxiliary = f.strategy(new Obj(Map.of()));
        var fields = new LinkedHashMap<>(auxiliary.members()); fields.put("ignored-null", null);
        Obj uncertain = new Obj(fields);
        f.scope(archive -> {
            DriverPersistentPlanningState.replay(uncertain, archive); int reads = f.reads;
            DriverPersistentPlanningState.replay(uncertain, archive); assertTrue(f.reads > reads); assertEquals(0, f.access.captures);
            Obj nonPlainInteger = auxiliary.with("ignored-integer", new IntegerValue(new BigInteger("3") { }));
            DriverPersistentPlanningState.replay(nonPlainInteger, archive); assertEquals(0, f.access.captures);
            f.access.eligible = false;
            DriverPersistentPlanningState.replay(auxiliary, archive); reads = f.reads;
            DriverPersistentPlanningState.replay(auxiliary, archive); assertTrue(f.reads > reads); assertEquals(0, f.access.captures);
            return null;
        });
    }

    @Test void eligibilityIsCheckedAgainAfterCloseAndBeforeAHitCanReturn() throws Exception {
        var f = new Fixture(); Obj auxiliary = f.strategy(new Obj(Map.of()));
        f.scope(archive -> {
            f.access.afterClose = () -> f.access.eligible = false;
            DriverPersistentPlanningState.replay(auxiliary, archive);
            f.access.afterClose = () -> { }; f.access.eligible = true;
            DriverPersistentPlanningState.replay(auxiliary, archive); assertEquals(2, f.access.captures);
            f.access.beforeVerify = () -> f.access.eligible = false; int reads = f.reads;
            DriverPersistentPlanningState.replay(auxiliary, archive); assertTrue(f.reads > reads);
            assertEquals(2, f.access.captures, "READ capture activity uses the original full reader without a new proof capture");
            return null;
        });
    }

    @Test void scopeFacadeAndThreadCannotBorrowAnotherMemo() throws Exception {
        var f = new Fixture(); Obj auxiliary = f.strategy(new Obj(Map.of()));
        f.scope(archive -> {
            DriverPersistentPlanningState.replay(auxiliary, archive); int reads = f.reads;
            f.scope(inner -> { DriverPersistentPlanningState.replay(auxiliary, inner); return null; });
            assertTrue(f.reads > reads); reads = f.reads;
            DriverPersistentPlanningState.replay(auxiliary, archive); assertEquals(reads, f.reads, "the previous lexical scope is restored");
            DriverPersistentPlanningState.replay(auxiliary, f.archive()); assertTrue(f.reads > reads);
            reads = f.reads;
            var failure = new java.util.concurrent.atomic.AtomicReference<Throwable>();
            Thread worker = new Thread(() -> {
                try { DriverPersistentPlanningState.replay(auxiliary, archive); }
                catch (Throwable problem) { failure.set(problem); }
            });
            worker.start();
            try { worker.join(); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
            assertNull(failure.get()); assertTrue(f.reads > reads, "another thread uses the original full reader");
            return null;
        });
        int reads = f.reads; DriverPersistentPlanningState.replay(auxiliary, f.archive); assertTrue(f.reads > reads);
        f.scope(archive -> { DriverPersistentPlanningState.replay(auxiliary, archive); return null; });
        assertEquals(3, f.access.captures);
    }

    @Test void entryWeightAndDependencyBudgetsOnlyDeclineRetention() throws Exception {
        var f = new Fixture(); Obj auxiliary = f.strategy(new Obj(Map.of()));
        f.scope(archive -> {
            for (int i = 0; i < 129; i++) DriverPersistentPlanningState.replay(auxiliary.with("ignored", new IntegerValue(BigInteger.valueOf(i))), archive);
            int reads = f.reads;
            DriverPersistentPlanningState.replay(auxiliary.with("ignored", new IntegerValue(BigInteger.ZERO)), archive); assertTrue(f.reads > reads);
            Obj tooHeavy = auxiliary.with("ignored", new Text("x".repeat(4 * 1024 * 1024)));
            DriverPersistentPlanningState.replay(tooHeavy, archive); reads = f.reads;
            DriverPersistentPlanningState.replay(tooHeavy, archive); assertTrue(f.reads > reads, "oversized unrelated DATA stays valid and fully replayed");
            var many = new LinkedHashSet<ExactRef>();
            for (int i = 0; i < 32769; i++) many.add(new ExactRef("memory/dependency-" + i, 0, "0".repeat(64)));
            f.access.overrideDependencies = Set.copyOf(many);
            Obj tooMany = auxiliary.with("ignored", new Bool(true));
            DriverPersistentPlanningState.replay(tooMany, archive); reads = f.reads;
            DriverPersistentPlanningState.replay(tooMany, archive); assertTrue(f.reads > reads);
            return null;
        });
    }

    @Test void nullAccessRunsFullAndCannotBorrowAnOuterMemo() throws Exception {
        var f = new Fixture(); Obj auxiliary = f.strategy(new Obj(Map.of()));
        f.scope(archive -> {
            DriverPersistentPlanningState.replay(auxiliary, archive); int reads = f.reads;
            DriverPersistentPlanningState.inRetainedDataReplayScope(null, archive, full -> {
                DriverPersistentPlanningState.replay(auxiliary, full); int first = f.reads;
                DriverPersistentPlanningState.replay(auxiliary, full); assertTrue(f.reads > first); return null;
            });
            assertTrue(f.reads > reads); assertEquals(1, f.access.captures);
            reads = f.reads; DriverPersistentPlanningState.replay(auxiliary, archive); assertEquals(reads, f.reads);
            return null;
        });
    }
}
