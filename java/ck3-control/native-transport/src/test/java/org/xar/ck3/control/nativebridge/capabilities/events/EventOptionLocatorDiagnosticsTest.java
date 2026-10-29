package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.function.UnaryOperator;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software packet receiver -> original capture -> typed DATA. No live query, trigger or Game authority. */
final class EventOptionLocatorDiagnosticsTest {
    private static final Instant NOW = Instant.now();
    private static final String REQUEST = "software-locator-query", SESSION = "software-event-session";
    private static final int EVENT = 0x01000029, DATE = 741221;
    private static final BigInteger N = BigInteger.valueOf(17), P = BigInteger.valueOf(41);
    private static final BigInteger AUTHORED = new BigInteger("9007199254742000");
    // Exact private Native fixture serializer output, 2026-10-29, machine xenoamess-full-tower-eb9d2c1186.
    // 3-FIXTURE-WHOLE.txt: 7776 B, SHA355ceeb6812a12a8e5ffb9e4ba22d9569ac49070fca1a0d027d783481c2d6216.
    // These are historical fixture-process addresses/PID, never a CK3/world-frame observation.
    private static final String NATIVE_DETAIL = "{\"schema_version\":1,\"pid\":238852,\"connection_generation\":\"8\",\"query_sequence\":\"11\",\"mailbox_ticket_sequence\":\"12\",\"application_pump_epoch\":\"13\",\"thread_id\":\"293244\",\"module_base\":\"140700380823552\",\"module_size\":null,\"frame_identity\":null,\"snapshot_identity\":null,\"unavailable_reason\":null,\"rows\":[{\"rendered_index\":0,\"native_option_index\":3,\"authored_vector_slot\":\"948293849368\",\"authored_option\":\"948293848192\",\"receiver80\":{\"address\":\"948293848320\",\"vptr\":\"948293627360\",\"slot58\":\"0\",\"slot60\":\"18446744073709551615\",\"slotC8\":\"291\",\"unavailable_reason\":null},\"receiver150\":{\"address\":\"948293848528\",\"vptr\":\"948293627568\",\"slot58\":\"1110\",\"slot60\":\"1929\",\"slotC8\":\"0\",\"unavailable_reason\":null}}]}";
    @TempDir Path temporary;
    private record Fixture(NativeGameTransport transport, Packets packets, BridgeDiagnostics.Received received,
            PlanningReadReceipt receipt, ObjectNode notice,
            ReadContract<org.xar.ck3.control.application.planning.events.EventPolicies.ReadPublication> contract) implements AutoCloseable {
        public void close() throws IOException { transport.close(); }
    }
    private static ObjectNode object() { return EventWindowCodec.parse(new RawJson("{}".getBytes(StandardCharsets.UTF_8))); }
    private static RawJson raw(ObjectNode value) { return EventWindowRead.raw(value); }
    private ExactRef preserve(byte[] bytes) throws Exception {
        Path path = temporary.resolve(UUID.randomUUID() + ".bin"); Files.write(path, bytes);
        var ref = SharedSourceFiles.observe(path).source(); return new ExactRef(ref.path(), ref.bytes(), ref.sha256());
    }
    private static ObjectNode hello() {
        var row = object(); row.put("type", "hello").put("protocol_version", 1).put("pid", 123).put("connection_generation", 1)
                .put("bridge_version", "software").put("expected_ck3_sha256", Build.CROZIER4.sha256())
                .put("game_adapter_id", "ck3-1.20.0.4-msvc-x64").put("game_adapter_status", "ready").put("ck3_build_match", true);
        row.putArray("capabilities").add("game.state.snapshot").add(EventWindowRead.CAPABILITY); return row;
    }
    private static ObjectNode context() {
        var row = object(); row.put("schema", "current-event-window-context-v1").put("schema_version", 1).put("status", "available")
                .put("snapshot_revision", N).put("date_raw", DATE).put("current_event_instance_id", EVENT).put("window_match_count", 1)
                .put("event_definition_key", "software.event").put("calculated_event_id", 7).put("runtime_stats_ordinal", 3);
        row.putNull("unavailable_reason");
        var root = row.putObject("root_scope"); root.put("status", "available").put("raw_type_index", 4).put("type_key", "character").put("subtype", 0);
        root.putObject("typed_identity").put("status", "available").put("kind", "character").put("character_id", 73);
        row.putArray("saved_scopes");
        var option = row.putArray("options").addObject(); option.put("rendered_index", 0).put("native_option_index", 3).put("shown", true)
                .put("enabled", false).put("fallback", false).put("cancel", false).put("resolved_name", "software disabled row").put("unavailable_reason", "");
        var indicators = option.putObject("effect_indicators"); indicators.put("status", "available").put("coverage", Build.CROZIER4.coverage()).put("complete_effect_set", false); indicators.putArray("rows");
        option.putObject("effect_preview").put("status", "unavailable").put("reason", "indicator_subset_has_no_completeness_signal");
        option.putObject("resource_deltas").put("status", "unavailable"); option.putObject("relationship_deltas").put("status", "unavailable");
        var ready = row.putObject("readiness");
        for (String name : List.of("event_definition_identity_ready", "root_scope_ready", "saved_scopes_ready", "option_presentation_ready", "effect_indicators_ready")) ready.put(name, true);
        ready.put("effect_preview_ready", false).put("semantic_decision_ready", false);
        row.putObject("provenance").put("root", Build.CROZIER4.root()).put("idler_vtable_rva", Build.CROZIER4.vtable()).put("manager_offset", "+0x28").put("backend_id", Build.CROZIER4.backend());
        return row;
    }
    private static ObjectNode receiver(BigInteger address, boolean zeroVptr) {
        var row = object(); row.put("address", address.toString()).put("vptr", zeroVptr ? "0" : "5368750080");
        if (zeroVptr) { row.putNull("slot58"); row.putNull("slot60"); row.putNull("slotC8"); row.put("unavailable_reason", "null_vptr"); }
        else { row.put("slot58", StrictJson.UINT64_MAX.toString()).put("slot60", "0").put("slotC8", "5368782848"); row.putNull("unavailable_reason"); }
        return row;
    }
    private static ObjectNode notice() {
        var row = object(); row.put("type", "snapshot_publish_diagnostic").put("protocol_version", 1).put("request_id", REQUEST)
                .put("phase", "end").put("status", "available").put("revision", N).put("payload_bytes", 0).put("diagnostic_kind", EventOptionLocatorDiagnostics.KIND);
        var detail = row.putObject("detail"); detail.put("schema_version", 1).put("pid", 123).put("connection_generation", "1")
                .put("query_sequence", "9").put("mailbox_ticket_sequence", "18446744073709551615").put("application_pump_epoch", "0")
                .put("thread_id", "1234").put("module_base", "5368709120");
        detail.putNull("module_size"); detail.putNull("frame_identity"); detail.putNull("snapshot_identity"); detail.putNull("unavailable_reason");
        var item = detail.putArray("rows").addObject(); item.put("rendered_index", 0).put("native_option_index", 3)
                .put("authored_vector_slot", "9007199254741024").put("authored_option", AUTHORED.toString());
        item.set("receiver80", receiver(AUTHORED.add(BigInteger.valueOf(0x80)), false));
        item.set("receiver150", receiver(AUTHORED.add(BigInteger.valueOf(0x150)), true)); return row;
    }
    private Fixture fixture(UnaryOperator<ObjectNode> mutation, boolean includeNotice, long transportBirth) throws Exception {
        return fixture(mutation, includeNotice, transportBirth, 123, BigInteger.ONE, BigInteger.valueOf(9));
    }
    private Fixture fixture(UnaryOperator<ObjectNode> mutation, boolean includeNotice, long transportBirth,
            long pid, BigInteger generation, BigInteger querySequence) throws Exception {
        var originalNotice = mutation.apply(notice());
        var originalHello = hello().put("pid", pid).put("connection_generation", generation);
        var snapshot = object(); snapshot.put("type", "state_snapshot").put("protocol_version", 1).put("snapshot_id", "software-frame").put("revision", N);
        var state = snapshot.putObject("state"); state.put("paused", true).put("map_ready", true).put("date_raw", DATE);
        state.putObject("played_character").put("character_id", 73).put("alive", true);
        var packets = includeNotice ? new Packets(originalHello, originalNotice, snapshot) : new Packets(originalHello, snapshot);
        var game = new GameGeneration(pid, new PythonOnlyUInt64(BigInteger.ONE));
        var config = new NativePipeEndpoint.Config("\\\\.\\pipe\\software-event-locator", "software-event-machine",
                new GameGeneration(pid, new PythonOnlyUInt64(BigInteger.valueOf(transportBirth))), SESSION, "software", Build.CROZIER4.sha256(), "ck3-1.20.0.4-msvc-x64");
        var transport = NativeTransportReplayTestFactory.create(packets, config, 8, 2);
        var observed = transport.observe(NOW.plusSeconds(30));
        var received = BridgeDiagnosticsCapture.capture(transport.pipeName(), transport.diagnostics(), Optional.of(observed));
        var source = preserve(new byte[]{'e','v','e','n','t'}); var capability = preserve(NativeWire.packet(raw(originalHello).bytes()));
        var identity = new ObservationIdentity("software-event-machine", game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(707), N, BigInteger.valueOf(DATE)), "software-frame", P, "software-episode"), 1);
        var g2 = new G2Source(identity.machineId(), NOW.toString(), "1.20.0.4", source);
        var semantic = object(); semantic.put("snapshot_id", "software-frame").put("revision", P).put("native_revision", N).put("date_raw", DATE).put("paused", true);
        semantic.putObject("active_event").put("instance_id", EVENT);
        var contract = EventWindowRead.contract(source, request -> { });
        var request = new PlanningReadRequest(identity, g2, SESSION, contract.operation(), OpportunityJson.object(OpportunityJson.parse(raw(semantic).bytes()), "software semantic"), NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(new GuardEvidence(identity, g2, SESSION, generation, contract.operation(), source, capability, "software-only", NOW, NOW.plusSeconds(30)), true, true, true, "b".repeat(64));
        var result = object(); result.put("step", EventWindowRead.STEP).put("accepted", true).put("status", "available").put("query_sequence", querySequence).put("snapshot_revision", N).put("backend_id", "native-headless"); result.set("current_event_window_context", context());
        var returned = object(); returned.put("type", "command_result").put("protocol_version", 1).put("request_id", REQUEST).put("ok", true); returned.set("result", result);
        var outbound = NativeWire.execute(REQUEST, EventWindowRead.STEP, N, raw(object().put("event_instance_id", EVENT)).bytes());
        var ack = new NativeActionPort.AckReceived(REQUEST, true, Optional.of(raw(result)), raw(returned), NativeWire.packet(raw(returned).bytes()), Optional.of(new NativeActionPort.OutboundPacket(REQUEST, outbound)));
        return new Fixture(transport, packets, received, new PlanningReadReceipt(request, contract.contractId(), REQUEST, guard, guard, ack), originalNotice, contract);
    }
    private static ObjectNode detail(ObjectNode notice) { return (ObjectNode) notice.get("detail"); }
    private static ObjectNode first(ObjectNode notice) { return (ObjectNode) detail(notice).get("rows").get(0); }
    @Test void receivedOriginalsRetainWideValuesZeroAndDisabledRowsWithoutAnyReadOrWrite() throws Exception {
        try (var f = fixture(UnaryOperator.identity(), true, 1)) {
            int reads = f.packets().reads;
            var data = assertInstanceOf(EventOptionLocatorDiagnostics.Data.class, EventOptionLocatorDiagnostics.project(f.received(), f.receipt()));
            assertEquals(N, data.occurrence().nativeRevision()); assertEquals("0", data.occurrence().applicationPumpEpoch().decimal());
            assertEquals(StrictJson.UINT64_MAX, data.rows().get(0).receiver80().slot58().orElseThrow().value());
            assertEquals(BigInteger.ZERO, data.rows().get(0).receiver80().slot60().orElseThrow().value());
            assertEquals("0", data.rows().get(0).receiver150().vptr().decimal()); assertTrue(data.rows().get(0).receiver150().slot58().isEmpty());
            assertTrue(data.module().rva(data.rows().get(0).receiver80().slot58().orElseThrow()).isEmpty());
            assertEquals(raw(f.notice()), data.originalNotice());
            var result = EventWindowCodec.parse(data.originalResult());
            assertFalse(result.get("current_event_window_context").get("options").get(0).get("enabled").booleanValue());
            assertEquals(reads, f.packets().reads); assertEquals(0, f.packets().writes);
        }
    }
    @Test void missingOrOverwrittenLatestNoticeIsUnavailableRatherThanAnEventFailure() throws Exception {
        try (var f = fixture(UnaryOperator.identity(), false, 1)) {
            assertEquals(EventOptionLocatorDiagnostics.Reason.NO_MATCHING_NOTICE, assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, EventOptionLocatorDiagnostics.project(f.received(), f.receipt())).reason());
        }
        try (var f = fixture(n -> n.put("request_id", "other-query"), true, 1)) {
            assertEquals(EventOptionLocatorDiagnostics.Reason.NO_MATCHING_NOTICE, assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, EventOptionLocatorDiagnostics.project(f.received(), f.receipt())).reason());
        }
    }
    @Test void receiptNativeRevisionSequenceAndPhysicalSessionAreIndependent() throws Exception {
        for (UnaryOperator<ObjectNode> change : List.<UnaryOperator<ObjectNode>>of(
                n -> { n.put("revision", P); return n; },
                n -> { detail(n).put("query_sequence", "10"); return n; },
                n -> { detail(n).put("connection_generation", "2"); return n; },
                n -> { detail(n).put("pid", 124); return n; })) {
            try (var f = fixture(change, true, 1)) {
                assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, EventOptionLocatorDiagnostics.project(f.received(), f.receipt()));
                assertEquals(0, f.packets().writes);
            }
        }
        try (var f = fixture(UnaryOperator.identity(), true, 2)) {
            assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, EventOptionLocatorDiagnostics.project(f.received(), f.receipt()));
        }
    }
    @Test void malformedPrivateFieldsCannotChangeOrdinaryEventPresentation() throws Exception {
        for (UnaryOperator<ObjectNode> change : List.<UnaryOperator<ObjectNode>>of(
                n -> { detail(n).put("connection_generation", true); return n; },
                n -> { detail(n).put("connection_generation", 1.0); return n; },
                n -> { first(n).put("authored_option", "0x2000"); return n; },
                n -> { first(n).put("authored_option", "09007199254742000"); return n; },
                n -> { first(n).put("authored_option", StrictJson.UINT64_MAX.toString()); return n; },
                n -> { first(n).put("native_option_index", 4); return n; },
                n -> { ((ObjectNode) first(n).get("receiver80")).put("address", "1"); return n; },
                n -> { ((ObjectNode) first(n).get("receiver80")).remove("slot58"); return n; },
                n -> { detail(n).put("frame_identity", "not-a-worldframe"); return n; })) {
            try (var f = fixture(change, true, 1)) {
                assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, EventOptionLocatorDiagnostics.project(f.received(), f.receipt()));
                var binding = new Binding(Build.CROZIER4, N, DATE, EVENT);
                assertFalse(assertInstanceOf(Available.class, EventWindowCodec.decode(raw(context()), binding)).firstDisplayed().orElseThrow().enabled());
                assertEquals(0, f.packets().writes);
            }
        }
    }
    @Test void nativeCopyFailurePreservesUnavailableWithoutInventingRows() throws Exception {
        try (var f = fixture(n -> { n.put("status", "unavailable"); detail(n).putNull("rows"); detail(n).put("unavailable_reason", "receiver_read_fault"); return n; }, true, 1)) {
            var result = assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, EventOptionLocatorDiagnostics.project(f.received(), f.receipt()));
            assertEquals(EventOptionLocatorDiagnostics.Reason.NATIVE_UNAVAILABLE, result.reason()); assertEquals("receiver_read_fault", result.detail()); assertEquals(0, f.packets().writes);
        }
    }
    @Test void originalEventServiceConsumesOnlyOptionalDataAndKeepsItsPublicResponse() throws Exception {
        try (var f = fixture(UnaryOperator.identity(), true, 1)) {
            var calls = new java.util.concurrent.atomic.AtomicInteger();
            PlanningReadPort reads = new PlanningReadPort() {
                public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                    assertSame(f.contract(), contract); assertEquals(f.receipt().request(), request); calls.incrementAndGet();
                    return new PlanningReadResult.Known<>(contract.decode(f.receipt()), f.receipt(), f.receipt().before().binding().nativeEvidence());
                }
            };
            var query = new EventWindowService.Query(EVENT, P);
            var plain = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request());
            var expected = EventWindowService.encode(plain.query_current_event_window_context_v1(query));
            int readsBefore = f.packets().reads;
            var actual = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request(),
                    receipt -> EventOptionLocatorDiagnostics.project(f.received(), receipt));
            var received = EventWindowService.encode(actual.query_current_event_window_context_v1(query));
            assertEquals(expected, received); assertInstanceOf(EventOptionLocatorDiagnostics.Data.class, actual.latestLocatorDiagnostic());
            var failed = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request(),
                    receipt -> { throw new IOException("software optional capture fault"); });
            assertEquals(expected, EventWindowService.encode(failed.query_current_event_window_context_v1(query)));
            assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, failed.latestLocatorDiagnostic());
            assertEquals(3, calls.get()); assertEquals(readsBefore, f.packets().reads); assertEquals(0, f.packets().writes);
        }
    }
    @Test void originalNativeSerializedDetailReachesJavaThroughActualPacketReceiver() throws Exception {
        var nativeDetail = EventWindowCodec.parse(new RawJson(NATIVE_DETAIL.getBytes(StandardCharsets.UTF_8)));
        long pid = nativeDetail.get("pid").longValue();
        var generation = new BigInteger(nativeDetail.get("connection_generation").textValue());
        var sequence = new BigInteger(nativeDetail.get("query_sequence").textValue());
        try (var f = fixture(n -> { n.set("detail", nativeDetail.deepCopy()); return n; }, true, 1, pid, generation, sequence)) {
            var data = assertInstanceOf(EventOptionLocatorDiagnostics.Data.class, EventOptionLocatorDiagnostics.project(f.received(), f.receipt()));
            assertEquals(nativeDetail, EventWindowCodec.parse(data.originalNotice()).get("detail"));
            assertEquals(sequence, data.occurrence().querySequence().value());
            assertEquals(StrictJson.UINT64_MAX, data.rows().get(0).receiver80().slot60().orElseThrow().value());
            assertEquals(BigInteger.ZERO, data.rows().get(0).receiver80().slot58().orElseThrow().value());
            assertEquals(BigInteger.ZERO, data.rows().get(0).receiver150().slotC8().orElseThrow().value());
            assertTrue(data.module().size().isEmpty()); assertEquals(0, f.packets().writes);
        }
        for (boolean wrongSequence : List.of(true, false)) {
            try (var f = fixture(n -> { n.set("detail", nativeDetail.deepCopy());
                if (wrongSequence) detail(n).put("query_sequence", sequence.add(BigInteger.ONE).toString());
                else ((ObjectNode) first(n).get("receiver80")).put("address", "1");
                return n; }, true, 1, pid, generation, sequence)) {
                assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, EventOptionLocatorDiagnostics.project(f.received(), f.receipt()));
                assertEquals(0, f.packets().writes);
            }
        }
    }
    private static PlanningReadReceipt returned(Fixture f, String requestId,
            BigInteger querySequence, ObjectNode originalContext) throws IOException {
        var result = object(); result.put("step", EventWindowRead.STEP).put("accepted", true)
                .put("status", "available").put("query_sequence", querySequence)
                .put("snapshot_revision", N).put("backend_id", "native-headless");
        result.set("current_event_window_context", originalContext);
        var packet = object(); packet.put("type", "command_result").put("protocol_version", 1)
                .put("request_id", requestId).put("ok", true); packet.set("result", result);
        var outbound = NativeWire.execute(requestId, EventWindowRead.STEP, N,
                raw(object().put("event_instance_id", EVENT)).bytes());
        var ack = new NativeActionPort.AckReceived(requestId, true, Optional.of(raw(result)),
                raw(packet), NativeWire.packet(raw(packet).bytes()),
                Optional.of(new NativeActionPort.OutboundPacket(requestId, outbound)));
        return new PlanningReadReceipt(f.receipt().request(), f.contract().contractId(), requestId,
                f.receipt().before(), f.receipt().after(), ack);
    }
    private static PlanningReadPort currentReceiptPort(Fixture f,
            java.util.concurrent.atomic.AtomicReference<PlanningReadReceipt> current) {
        return new PlanningReadPort() {
            public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                assertSame(f.contract(), contract);
                var receipt = current.get();
                assertEquals(receipt.request(), request);
                return new PlanningReadResult.Known<>(contract.decode(receipt), receipt,
                        receipt.before().binding().nativeEvidence());
            }
        };
    }
    private static EventWindowService service(Fixture f, PlanningReadPort reads) {
        return new EventWindowService(reads, f.contract(), ignored -> f.receipt().request(),
                receipt -> EventOptionLocatorDiagnostics.project(
                        BridgeDiagnosticsCapture.capture(f.transport().pipeName(),
                                f.transport().diagnostics(), Optional.empty()), receipt));
    }
    private static void receiveNext(Fixture f, ObjectNode actualNotice, String snapshotId) throws Exception {
        f.packets().packets.add(NativeWire.packet(raw(actualNotice).bytes()));
        byte[] framed = f.received().retainedSnapshot().orElseThrow().originalPacket();
        var snapshot = EventWindowCodec.parse(new RawJson(java.util.Arrays.copyOfRange(framed, 4, framed.length)));
        snapshot.put("snapshot_id", snapshotId);
        f.packets().packets.add(NativeWire.packet(raw(snapshot).bytes()));
        assertEquals(snapshotId, f.transport().observe(NOW.plusSeconds(30)).snapshotId());
        assertArrayEquals(raw(actualNotice).bytes(), f.transport().diagnostics()
                .latestSnapshotDiagnostic().orElseThrow().original().payload().value());
    }
    @Test void actualReceiverReplacementCannotLeaveDataAOnCurrentResponseB() throws Exception {
        try (var f = fixture(UnaryOperator.identity(), true, 1)) {
            var current = new java.util.concurrent.atomic.AtomicReference<>(f.receipt());
            var reads = currentReceiptPort(f, current);
            var installed = service(f, reads);
            var query = new EventWindowService.Query(EVENT, P);
            var responseA = installed.query_current_event_window_context_v1(query);
            var dataA = assertInstanceOf(EventOptionLocatorDiagnostics.Data.class,
                    installed.latestLocatorDiagnostic());
            assertEquals(REQUEST, dataA.occurrence().requestId());
            byte[] originalA = responseA.observation() instanceof PlanningReadResult.Known<?> k
                    ? k.receipt().original().originalPacket() : new byte[0];
            String requestB = "software-current-query-B";
            var receiptB = returned(f, requestB, BigInteger.TEN, context());
            current.set(receiptB);
            var foreign = notice(); foreign.put("request_id", "software-later-foreign-query");
            detail(foreign).put("query_sequence", "10");
            receiveNext(f, foreign, "software-after-overwrite");
            int readsAfterReceiver = f.packets().reads;
            var responseB = installed.query_current_event_window_context_v1(query);
            var missing = assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class,
                    installed.latestLocatorDiagnostic());
            assertEquals(EventOptionLocatorDiagnostics.Reason.NO_MATCHING_NOTICE, missing.reason());
            assertSame(receiptB, assertInstanceOf(PlanningReadResult.Known.class,
                    responseB.observation()).receipt());
            var plain = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request());
            assertEquals(EventWindowService.encode(plain.query_current_event_window_context_v1(query)),
                    EventWindowService.encode(responseB));
            assertArrayEquals(originalA, f.receipt().original().originalPacket());
            assertEquals(REQUEST, dataA.occurrence().requestId());
            assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class,
                    EventOptionLocatorDiagnostics.project(f.received(), receiptB));
            assertEquals(readsAfterReceiver, f.packets().reads);
            assertEquals(0, f.packets().writes);

            // A new matching original Notice may attach only to receipt B, never to A.
            var matchingB = notice(); matchingB.put("request_id", requestB);
            detail(matchingB).put("query_sequence", "10");
            receiveNext(f, matchingB, "software-after-matching-B");
            int beforePureProjection = f.packets().reads;
            var responseB2 = installed.query_current_event_window_context_v1(query);
            var dataB = assertInstanceOf(EventOptionLocatorDiagnostics.Data.class,
                    installed.latestLocatorDiagnostic());
            assertEquals(requestB, dataB.occurrence().requestId());
            assertEquals(BigInteger.TEN, dataB.occurrence().querySequence().value());
            assertNotEquals(dataA.originalNotice(), dataB.originalNotice());
            assertEquals(EventWindowService.encode(responseB), EventWindowService.encode(responseB2));
            assertEquals(beforePureProjection, f.packets().reads);
            assertEquals(0, f.packets().writes);
        }
    }
    private static ObjectNode context64() {
        var ctx = context();
        var template = ((ObjectNode) ctx.get("options").get(0)).deepCopy();
        var options = ctx.putArray("options");
        for (int i = 0; i < 64; i++) {
            var row = template.deepCopy(); row.put("rendered_index", i).put("native_option_index", i);
            options.add(row);
        }
        return ctx;
    }
    private static ObjectNode locatorRows(ObjectNode notice, int count) {
        var rows = detail(notice).putArray("rows");
        var vectorBase = new BigInteger("9007199254741000");
        for (int i = 0; i < count; i++) {
            BigInteger authored = AUTHORED.add(BigInteger.valueOf(i).multiply(BigInteger.valueOf(0x500)));
            var row = rows.addObject(); row.put("rendered_index", i).put("native_option_index", i)
                    .put("authored_vector_slot", vectorBase.add(BigInteger.valueOf(i * 8L)).toString())
                    .put("authored_option", authored.toString());
            row.set("receiver80", receiver(authored.add(BigInteger.valueOf(0x80)), false));
            row.set("receiver150", receiver(authored.add(BigInteger.valueOf(0x150)), true));
        }
        return notice;
    }
    @Test void complete64RowsPartial63Overflow65AndUnavailableRemainDistinct() throws Exception {
        for (int rows : List.of(64, 63, 65, -1)) {
            try (var f = fixture(n -> {
                if (rows < 0) {
                    n.put("status", "unavailable");
                    detail(n).putNull("rows"); detail(n).put("unavailable_reason", "raw_binding_changed");
                    return n;
                }
                return locatorRows(n, rows);
            }, true, 1)) {
                var receipt = returned(f, REQUEST, BigInteger.valueOf(9), context64());
                var current = new java.util.concurrent.atomic.AtomicReference<>(receipt);
                var reads = currentReceiptPort(f, current);
                var installed = service(f, reads);
                int beforePureProjection = f.packets().reads;
                var response = installed.query_current_event_window_context_v1(
                        new EventWindowService.Query(EVENT, P));
                var plain = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request());
                assertEquals(EventWindowService.encode(plain.query_current_event_window_context_v1(
                        new EventWindowService.Query(EVENT, P))), EventWindowService.encode(response));
                if (rows == 64) {
                    var data = assertInstanceOf(EventOptionLocatorDiagnostics.Data.class,
                            installed.latestLocatorDiagnostic());
                    assertEquals(64, data.rows().size());
                    assertEquals(63, data.rows().get(63).renderedIndex());
                    assertEquals(63, data.rows().get(63).nativeOptionIndex());
                } else {
                    var unavailable = assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class,
                            installed.latestLocatorDiagnostic());
                    assertEquals(rows < 0 ? EventOptionLocatorDiagnostics.Reason.NATIVE_UNAVAILABLE
                            : EventOptionLocatorDiagnostics.Reason.INVALID_DIAGNOSTIC, unavailable.reason());
                }
                assertEquals(beforePureProjection, f.packets().reads);
                assertEquals(0, f.packets().writes);
            }
        }
    }
    private static byte[] nativeResource(String name) throws IOException {
        try (var input = EventOptionLocatorDiagnosticsTest.class.getResourceAsStream("native-locator/" + name)) {
            if (input == null) throw new IOException("missing exact Native fixture resource: " + name);
            byte[] bytes = input.readAllBytes();
            if (bytes.length == 0) throw new IOException("empty exact Native fixture resource: " + name);
            return bytes;
        }
    }
    private static BridgeDiagnostics.Received currentCapture(Fixture f) throws IOException {
        return BridgeDiagnosticsCapture.capture(f.transport().pipeName(), f.transport().diagnostics(), Optional.empty());
    }
    private static void receiveOriginalNotice(Fixture f, byte[] noticeBytes, String snapshotId) throws Exception {
        f.packets().packets.add(NativeWire.packet(noticeBytes));
        byte[] retained = f.received().retainedSnapshot().orElseThrow().originalPacket();
        var snapshot = EventWindowCodec.parse(new RawJson(java.util.Arrays.copyOfRange(retained, 4, retained.length)));
        snapshot.put("snapshot_id", snapshotId);
        f.packets().packets.add(NativeWire.packet(raw(snapshot).bytes()));
        assertEquals(snapshotId, f.transport().observe(NOW.plusSeconds(30)).snapshotId());
        assertArrayEquals(noticeBytes, f.transport().diagnostics().latestSnapshotDiagnostic().orElseThrow().original().payload().value());
    }
    /** The only fabricated packets here are the explicitly software HELLO/snapshot/outbound context. */
    private Fixture pairedNativeFixture(boolean unavailable) throws Exception {
        return pairedNativeFixture(unavailable, Build.CROZIER2, "", "native-event-locator-11");
    }
    private Fixture pairedNativeFixture(boolean unavailable, Build build, String resourcePrefix,
            String expectedRequestId) throws Exception {
        byte[] noticeBytes = nativeResource(resourcePrefix + (unavailable ? "unavailable-notice.json" : "available-notice.json"));
        byte[] resultBytes = nativeResource(resourcePrefix + (unavailable ? "unavailable-result.json" : "available-result.json"));
        var originalNotice = EventWindowCodec.parse(new RawJson(noticeBytes));
        var nativeDetail = detail(originalNotice);
        long pid = nativeDetail.get("pid").longValue();
        var generation = new BigInteger(nativeDetail.get("connection_generation").textValue());
        var nativeHello = hello().put("pid", pid).put("connection_generation", generation)
                .put("expected_ck3_sha256", build.sha256()).put("game_adapter_id", "ck3-" + build.version() + "-msvc-x64");
        var snapshot = object(); snapshot.put("type", "state_snapshot").put("protocol_version", 1)
                .put("snapshot_id", "software-native-fixture-frame").put("revision", N);
        var state = snapshot.putObject("state"); state.put("paused", true).put("map_ready", true).put("date_raw", DATE);
        state.putObject("played_character").put("character_id", 42).put("alive", true);
        var packets = new Packets(nativeHello);
        packets.packets.add(NativeWire.packet(noticeBytes));
        packets.packets.add(NativeWire.packet(resultBytes));
        packets.packets.add(NativeWire.packet(raw(snapshot).bytes()));
        var game = new GameGeneration(pid, new PythonOnlyUInt64(BigInteger.ONE));
        var config = new NativePipeEndpoint.Config("\\\\.\\pipe\\software-native-locator-fixture", "software-native-fixture-machine",
                game, SESSION, "software", build.sha256(), "ck3-" + build.version() + "-msvc-x64");
        var transport = NativeTransportReplayTestFactory.create(packets, config, 8, 2);
        try {
            var observed = transport.observe(NOW.plusSeconds(30));
            var received = BridgeDiagnosticsCapture.capture(transport.pipeName(), transport.diagnostics(), Optional.of(observed));
            var returned = transport.drainLateResults(); assertEquals(1, returned.size());
            var originalResult = returned.getFirst();
            assertEquals(expectedRequestId, originalResult.requestId());
            assertArrayEquals(NativeWire.packet(resultBytes), originalResult.packet().value());
            assertArrayEquals(noticeBytes, transport.diagnostics().latestSnapshotDiagnostic().orElseThrow().original().payload().value());
            var source = preserve(new byte[]{'e', 'v', 'e', 'n', 't'});
            var capability = preserve(NativeWire.packet(raw(nativeHello).bytes()));
            var identity = new ObservationIdentity("software-native-fixture-machine", game,
                    new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(707), N, BigInteger.valueOf(DATE)),
                            observed.snapshotId(), P, "software-native-fixture-episode"), 1);
            var g2 = new G2Source(identity.machineId(), NOW.toString(), build.version(), source);
            var semantic = object(); semantic.put("snapshot_id", observed.snapshotId()).put("revision", P).put("native_revision", N)
                    .put("date_raw", DATE).put("paused", true); semantic.putObject("active_event").put("instance_id", EVENT);
            var contract = EventWindowRead.contract(source, request -> { });
            var request = new PlanningReadRequest(identity, g2, SESSION, contract.operation(),
                    OpportunityJson.object(OpportunityJson.parse(raw(semantic).bytes()), "software Native fixture semantic"), NOW.plusSeconds(30));
            var guard = new PlanningReadGuard(new GuardEvidence(identity, g2, SESSION, generation, contract.operation(), source, capability,
                    "software-only", NOW, NOW.plusSeconds(30)), true, true, true, "b".repeat(64));
            String requestId = originalResult.requestId();
            var outbound = NativeWire.execute(requestId, EventWindowRead.STEP, N, raw(object().put("event_instance_id", EVENT)).bytes());
            var ack = new NativeActionPort.AckReceived(requestId, originalResult.nativeOk(),
                    originalResult.result().token().map(token -> new RawJson(token.value())), new RawJson(originalResult.payload().value()),
                    originalResult.packet().value(), Optional.of(new NativeActionPort.OutboundPacket(requestId, outbound)));
            return new Fixture(transport, packets, received, new PlanningReadReceipt(request, contract.contractId(), requestId, guard, guard, ack), originalNotice, contract);
        } catch (Exception | AssertionError failure) {
            transport.close(); throw failure;
        }
    }
    @Test void completeHistoricalNativeNoticesRetainExactBytesWithoutInventingPairedResults() throws Exception {
        try (var f = fixture(UnaryOperator.identity(), false, 1)) {
            for (String mode : List.of("available", "unavailable")) {
                byte[] original = nativeResource("historical-" + mode + "-notice.json");
                assertEquals(mode.equals("available") ? 909 : 540, original.length);
                String sha = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(original));
                assertEquals(mode.equals("available") ? "70e9c64df856d0eefe3274fb911f8a7cb2087a6deda34d2e46dd580c1727cb7c"
                        : "632d1e3a03a6c5aee13d755732e79cb4223a2e35660ce2b5e6a9e6a81a223752", sha);
                receiveOriginalNotice(f, original, "software-historical-" + mode);
                var received = currentCapture(f);
                assertArrayEquals(original, received.original().latestSnapshotDiagnostic().orElseThrow().original().payload().value());
                assertEquals("native-event-locator-11", EventWindowCodec.parse(new RawJson(original)).get("request_id").textValue());
                int reads = f.packets().reads;
                var unavailable = assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class,
                        EventOptionLocatorDiagnostics.project(received, f.receipt()));
                assertEquals(EventOptionLocatorDiagnostics.Reason.NO_MATCHING_NOTICE, unavailable.reason());
                assertEquals(reads, f.packets().reads); assertEquals(0, f.packets().writes);
            }
        }
    }
    @Test void completeSameReadNativeNoticeAndResultReachDataWithOriginalBytesAndActualPresentation() throws Exception {
        try (var f = pairedNativeFixture(false)) {
            var reads = currentReceiptPort(f, new java.util.concurrent.atomic.AtomicReference<>(f.receipt()));
            var installed = service(f, reads);
            var query = new EventWindowService.Query(EVENT, P);
            var plain = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request());
            int packetReads = f.packets().reads;
            assertEquals(EventWindowService.encode(plain.query_current_event_window_context_v1(query)),
                    EventWindowService.encode(installed.query_current_event_window_context_v1(query)));
            var data = assertInstanceOf(EventOptionLocatorDiagnostics.Data.class, installed.latestLocatorDiagnostic());
            assertArrayEquals(nativeResource("available-notice.json"), data.originalNotice().bytes());
            assertArrayEquals(f.receipt().original().originalResultToken().orElseThrow().bytes(), data.originalResult().bytes());
            assertEquals("native-event-locator-11", data.occurrence().requestId());
            assertEquals(BigInteger.valueOf(11), data.occurrence().querySequence().value());
            assertEquals(N, data.occurrence().nativeRevision()); assertEquals(P, f.receipt().request().before().frame().revision());
            var row = data.rows().getFirst(); assertEquals(0, row.renderedIndex()); assertEquals(3, row.nativeOptionIndex());
            assertEquals(BigInteger.ZERO, row.receiver80().slot58().orElseThrow().value());
            assertEquals(StrictJson.UINT64_MAX, row.receiver80().slot60().orElseThrow().value());
            assertEquals(BigInteger.ZERO, row.receiver150().slotC8().orElseThrow().value());
            assertNotEquals(row.receiver80().address(), row.receiver150().address()); assertTrue(data.module().size().isEmpty());
            var rawContext = EventWindowCodec.parse(data.originalResult()).get("current_event_window_context");
            var context = assertInstanceOf(Available.class, EventWindowCodec.decode(EventWindowRead.raw(rawContext), new Binding(Build.CROZIER2, N, DATE, EVENT)));
            var first = context.firstDisplayed().orElseThrow(); var originalOption = rawContext.get("options").get(0);
            assertEquals(originalOption.get("enabled").booleanValue(), first.enabled());
            assertEquals(originalOption.get("fallback").booleanValue(), first.fallback());
            assertEquals(originalOption.get("cancel").booleanValue(), first.cancel());
            assertEquals(originalOption.get("resolved_name").textValue(), first.resolvedName());
            assertEquals(originalOption.get("unavailable_reason").textValue(), first.unavailableReason());
            assertEquals(packetReads, f.packets().reads); assertEquals(0, f.packets().writes);
        }
    }
    @Test void completeSameReadNativeUnavailableDoesNotChangePublicResponse() throws Exception {
        try (var f = pairedNativeFixture(true)) {
            var reads = currentReceiptPort(f, new java.util.concurrent.atomic.AtomicReference<>(f.receipt()));
            var installed = service(f, reads);
            var plain = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request());
            var query = new EventWindowService.Query(EVENT, P); int packetReads = f.packets().reads;
            assertEquals(EventWindowService.encode(plain.query_current_event_window_context_v1(query)),
                    EventWindowService.encode(installed.query_current_event_window_context_v1(query)));
            var unavailable = assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, installed.latestLocatorDiagnostic());
            assertEquals(EventOptionLocatorDiagnostics.Reason.NATIVE_UNAVAILABLE, unavailable.reason());
            assertEquals("raw_read_unavailable", unavailable.detail());
            assertArrayEquals(nativeResource("unavailable-notice.json"), currentCapture(f).original().latestSnapshotDiagnostic().orElseThrow().original().payload().value());
            assertArrayEquals(NativeWire.packet(nativeResource("unavailable-result.json")), f.receipt().original().originalPacket());
            assertEquals(packetReads, f.packets().reads); assertEquals(0, f.packets().writes);
        }
    }
    @Test void completeNativeNoticeReplacementClearsSidecarAndKeepsPriorOriginalsAndPublicResponse() throws Exception {
        try (var f = pairedNativeFixture(false)) {
            var reads = currentReceiptPort(f, new java.util.concurrent.atomic.AtomicReference<>(f.receipt()));
            var installed = service(f, reads); var query = new EventWindowService.Query(EVENT, P);
            var before = EventWindowService.encode(installed.query_current_event_window_context_v1(query));
            var retained = assertInstanceOf(EventOptionLocatorDiagnostics.Data.class, installed.latestLocatorDiagnostic());
            byte[] retainedNotice = retained.originalNotice().bytes(), retainedResult = retained.originalResult().bytes();
            // Foreign software packet has its own unchanged request; the Native fixture bytes are never edited.
            receiveOriginalNotice(f, raw(notice()).bytes(), "software-after-native-notice-overwrite");
            int packetReads = f.packets().reads;
            assertEquals(before, EventWindowService.encode(installed.query_current_event_window_context_v1(query)));
            assertEquals(EventOptionLocatorDiagnostics.Reason.NO_MATCHING_NOTICE,
                    assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, installed.latestLocatorDiagnostic()).reason());
            assertArrayEquals(retainedNotice, retained.originalNotice().bytes()); assertArrayEquals(retainedResult, retained.originalResult().bytes());
            assertArrayEquals(nativeResource("available-notice.json"), retainedNotice);
            assertEquals(packetReads, f.packets().reads); assertEquals(0, f.packets().writes);
        }
    }
    @Test void completeFresh12004NativePairRetainsOriginalsAndExactBuildThroughService() throws Exception {
        try (var f = pairedNativeFixture(false, Build.CROZIER4, "12004-", "native-event-locator-12004-21")) {
            var reads = currentReceiptPort(f, new java.util.concurrent.atomic.AtomicReference<>(f.receipt()));
            var installed = service(f, reads);
            var plain = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request());
            var query = new EventWindowService.Query(EVENT, P);
            int packetReads = f.packets().reads;
            assertEquals(EventWindowService.encode(plain.query_current_event_window_context_v1(query)),
                    EventWindowService.encode(installed.query_current_event_window_context_v1(query)));
            var data = assertInstanceOf(EventOptionLocatorDiagnostics.Data.class, installed.latestLocatorDiagnostic());
            byte[] originalNotice = nativeResource("12004-available-notice.json");
            assertArrayEquals(originalNotice, data.originalNotice().bytes());
            assertArrayEquals(NativeWire.packet(nativeResource("12004-available-result.json")), f.receipt().original().originalPacket());
            assertArrayEquals(f.receipt().original().originalResultToken().orElseThrow().bytes(), data.originalResult().bytes());
            var actualDetail = detail(EventWindowCodec.parse(new RawJson(originalNotice)));
            var occurrence = data.occurrence();
            assertEquals("native-event-locator-12004-21", occurrence.requestId());
            assertEquals(actualDetail.get("pid").longValue(), occurrence.pid());
            assertEquals(actualDetail.get("thread_id").textValue(), occurrence.threadId().decimal());
            assertEquals(actualDetail.get("module_base").textValue(), data.module().base().decimal());
            assertEquals(BigInteger.valueOf(8), occurrence.connectionGeneration().value());
            assertEquals(BigInteger.valueOf(21), occurrence.querySequence().value());
            assertEquals(BigInteger.valueOf(22), occurrence.mailboxTicketSequence().value());
            assertEquals(BigInteger.valueOf(23), occurrence.applicationPumpEpoch().value());
            assertEquals(N, occurrence.nativeRevision());
            assertEquals(P, f.receipt().request().before().frame().revision());
            assertEquals(1, data.rows().size());
            var row = data.rows().getFirst();
            assertEquals(0, row.renderedIndex()); assertEquals(3, row.nativeOptionIndex());
            assertEquals(BigInteger.valueOf(291), row.receiver80().slot58().orElseThrow().value());
            assertEquals(BigInteger.ZERO, row.receiver80().slot60().orElseThrow().value());
            assertEquals(BigInteger.ZERO, row.receiver80().slotC8().orElseThrow().value());
            assertEquals(BigInteger.ZERO, row.receiver150().slot58().orElseThrow().value());
            assertEquals(BigInteger.ZERO, row.receiver150().slot60().orElseThrow().value());
            assertEquals(BigInteger.valueOf(1110), row.receiver150().slotC8().orElseThrow().value());
            assertNotEquals(row.receiver80().address(), row.receiver150().address());
            assertTrue(data.module().size().isEmpty());
            var contextRaw = EventWindowRead.raw(EventWindowCodec.parse(data.originalResult()).get("current_event_window_context"));
            var context = assertInstanceOf(Available.class,
                    EventWindowCodec.decode(contextRaw, new Binding(Build.CROZIER4, N, DATE, EVENT)));
            assertEquals(Build.CROZIER4, context.binding().build());
            assertThrows(IllegalArgumentException.class,
                    () -> EventWindowCodec.decode(contextRaw, new Binding(Build.CROZIER2, N, DATE, EVENT)));
            var option = context.firstDisplayed().orElseThrow();
            assertFalse(option.enabled()); assertTrue(option.fallback()); assertTrue(option.cancel());
            assertEquals("Wait", option.resolvedName()); assertEquals("Not today", option.unavailableReason());
            assertTrue(option.indicators().isEmpty());
            assertEquals(packetReads, f.packets().reads); assertEquals(0, f.packets().writes);
        }
    }
    @Test void completeFresh12004UnavailableRetainsOrdinaryOriginalResult() throws Exception {
        try (var f = pairedNativeFixture(true, Build.CROZIER4, "12004-", "native-event-locator-12004-21")) {
            var reads = currentReceiptPort(f, new java.util.concurrent.atomic.AtomicReference<>(f.receipt()));
            var installed = service(f, reads);
            var plain = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request());
            var query = new EventWindowService.Query(EVENT, P);
            int packetReads = f.packets().reads;
            assertEquals(EventWindowService.encode(plain.query_current_event_window_context_v1(query)),
                    EventWindowService.encode(installed.query_current_event_window_context_v1(query)));
            var unavailable = assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, installed.latestLocatorDiagnostic());
            assertEquals(EventOptionLocatorDiagnostics.Reason.NATIVE_UNAVAILABLE, unavailable.reason());
            assertEquals("raw_read_unavailable", unavailable.detail());
            assertArrayEquals(nativeResource("12004-unavailable-notice.json"),
                    currentCapture(f).original().latestSnapshotDiagnostic().orElseThrow().original().payload().value());
            byte[] resultBytes = nativeResource("12004-unavailable-result.json");
            assertArrayEquals(nativeResource("12004-available-result.json"), resultBytes);
            assertArrayEquals(NativeWire.packet(resultBytes), f.receipt().original().originalPacket());
            var original = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(NativeWire.packet(resultBytes)));
            assertArrayEquals(original.result().token().orElseThrow().value(),
                    f.receipt().original().originalResultToken().orElseThrow().bytes());
            assertEquals(packetReads, f.packets().reads); assertEquals(0, f.packets().writes);
        }
    }
    @Test void completeFresh12004ReplacementClearsOnlyCurrentOptionalSidecar() throws Exception {
        try (var f = pairedNativeFixture(false, Build.CROZIER4, "12004-", "native-event-locator-12004-21")) {
            var reads = currentReceiptPort(f, new java.util.concurrent.atomic.AtomicReference<>(f.receipt()));
            var installed = service(f, reads);
            var plain = new EventWindowService(reads, f.contract(), ignored -> f.receipt().request());
            var query = new EventWindowService.Query(EVENT, P);
            var before = EventWindowService.encode(installed.query_current_event_window_context_v1(query));
            var retained = assertInstanceOf(EventOptionLocatorDiagnostics.Data.class, installed.latestLocatorDiagnostic());
            byte[] retainedNotice = retained.originalNotice().bytes(), retainedResult = retained.originalResult().bytes();
            // This foreign software Notice is separate; neither Native fixture Envelope is edited.
            receiveOriginalNotice(f, raw(notice()).bytes(), "software-after-fresh12004-overwrite");
            int packetReads = f.packets().reads;
            assertEquals(before, EventWindowService.encode(installed.query_current_event_window_context_v1(query)));
            assertEquals(EventWindowService.encode(plain.query_current_event_window_context_v1(query)), before);
            assertEquals(EventOptionLocatorDiagnostics.Reason.NO_MATCHING_NOTICE,
                    assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class, installed.latestLocatorDiagnostic()).reason());
            assertEquals(EventOptionLocatorDiagnostics.Reason.NO_MATCHING_NOTICE,
                    assertInstanceOf(EventOptionLocatorDiagnostics.Unavailable.class,
                            EventOptionLocatorDiagnostics.project(currentCapture(f), f.receipt())).reason());
            assertArrayEquals(nativeResource("12004-available-notice.json"), retainedNotice);
            assertArrayEquals(retainedNotice, retained.originalNotice().bytes());
            assertArrayEquals(retainedResult, retained.originalResult().bytes());
            assertArrayEquals(f.receipt().original().originalResultToken().orElseThrow().bytes(), retainedResult);
            assertArrayEquals(NativeWire.packet(nativeResource("12004-available-result.json")), f.receipt().original().originalPacket());
            assertEquals(packetReads, f.packets().reads); assertEquals(0, f.packets().writes);
        }
    }

    private static final class Packets implements NativePacketPort {
        private final ArrayDeque<byte[]> packets = new ArrayDeque<>(); private int reads, writes;
        private Packets(ObjectNode... values) throws IOException { for (ObjectNode value : values) packets.add(NativeWire.packet(raw(value).bytes())); }
        public void verify() { }
        public void awaitConnection(Instant deadline) { }
        public byte[] readPacket(Instant deadline) throws IOException { reads++; if (packets.isEmpty()) throw new IOException("software packets exhausted"); return packets.removeFirst(); }
        public void writePacket(byte[] packet, Instant deadline) { writes++; throw new AssertionError("offline locator projection must not issue a request"); }
        public void close() { }
    }
}
