package org.xar.ck3.control.wave2.finance.giftroute;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.RootProjection;
import org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatCodec;
import org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatObserver;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFrameCodec;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransportCodec;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.CheckpointRead;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.Context;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.Directory;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ExistingCheckpointPort;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ExistingPorts;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ManagedDirectory;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.NoManagedDirectory;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ProcessObservation;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashCodec;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashObserver;

final class GiftRouteCoordinatorTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private static byte[] bytes(JsonNode node) { return GiftReadTransportCodec.encodeObjectProjection(node); }
    private static JsonNode tree(byte[] bytes) {
        try { return JSON.readTree(bytes); } catch (IOException error) { throw new IllegalStateException(error); }
    }
    private static JsonNode golden() throws IOException {
        InputStream resource = GiftRouteCoordinatorTest.class.getResourceAsStream("/giftroute/producer-golden.json.gz");
        if (resource == null) { throw new IOException("committed original full-route gzip golden required"); }
        try (InputStream raw = resource; GZIPInputStream gzip = new GZIPInputStream(raw)) {
            byte[] bytes = gzip.readNBytes(240_001);
            if (bytes.length == 0 || bytes.length > 240_000) { throw new IOException("bounded uncompressed artifact required"); }
            return JSON.readTree(bytes);
        }
    }
    private static JsonNode scenario(String name) throws IOException {
        for (JsonNode item : golden().get("cases")) {
            if (item.get("name").textValue().equals(name)) { return item.get("scenario").deepCopy(); }
        }
        throw new IOException("missing original case " + name);
    }

    private static final class Ports implements ExistingPorts, GiftReadTransport.ExistingOwnedReadPort {
        private final JsonNode scenario;
        private int directoryReads;
        private int ledgerReads;
        private int candidateQueries;
        private int candidateSends;
        private int snapshotReads;
        private int boundedWaits;
        private int checkpointReads;
        private int threatReads;
        private int cashReads;
        private Context quotedContext;
        private RootProjection quotedRoot;
        Ports(JsonNode scenario) { this.scenario = scenario; }
        @Override public Directory managedDirectory() {
            directoryReads++;
            return scenario.get("managed").booleanValue() ? new ManagedDirectory(Path.of("fixture-no-io")) : new NoManagedDirectory();
        }
        @Override public Ledger readCurrentLedger(ManagedDirectory directory) {
            ledgerReads++; return GiftPendingCodec.decodeLedger(bytes(scenario.get("ledger")));
        }
        @Override public ProcessObservation readProcessObservation(PendingAction pending) {
            JsonNode current = scenario.get("current_process");
            return new ProcessObservation(new ProcessIdentity(current.get("pid").bigIntegerValue(),
                    current.get("creation_date").textValue()), pending.sourceProcess());
        }
        @Override public Optional<GiftPendingFramePolicy.ExistingSnapshotWaitPort> originalBoundedWait() {
            if (!scenario.get("wait_enabled").booleanValue()) { return Optional.empty(); }
            return Optional.of((source, predicate, timeout) -> {
                boundedWaits++; assertEquals(GiftPendingFramePolicy.WAIT_TIMEOUT, timeout);
                JsonNode fresh = scenario.get("fresh_snapshot");
                GiftPendingFramePolicy.Frame frame = fresh.isNull() ? source : GiftPendingFrameCodec.decodeSnapshot(bytes(fresh));
                if (scenario.has("wait_predicate_ready")) { assertEquals(scenario.get("wait_predicate_ready").booleanValue(), predicate.test(frame)); }
                return frame;
            });
        }
        @Override public Optional<GiftReadTransport.ExistingOwnedReadPort> originalCandidateRead() {
            if (!scenario.get("candidate_reader").booleanValue()) { return Optional.empty(); }
            candidateQueries++; return Optional.of(this);
        }
        @Override public GiftReadTransport.Snapshot takeInternalSemanticSnapshot() {
            snapshotReads++; return GiftReadTransportCodec.decodeSnapshot(bytes(scenario.get("input").get("snapshot")));
        }
        @Override public GiftReadTransport.Diagnostics diagnostics() { return GiftReadTransportCodec.decodeDiagnostics(bytes(scenario.get("private_diagnostics"))); }
        @Override public void send(GiftReadTransport.Command command) {
            candidateSends++;
            assertEquals("private-query-faction-gift-member-v1", tree(GiftReadTransportCodec.encodeCommand(command)).get("step").textValue());
        }
        @Override public GiftReadTransport.WaitResult waitForCommandResult(GiftReadTransport.ReadId id, GiftReadTransport.Timeout timeout) {
            ObjectNode reply = JSON.createObjectNode(); reply.put("type", "command_result"); reply.put("protocol_version", 1);
            reply.put("request_id", id.value()); reply.put("ok", true); reply.set("result", scenario.get("private_result"));
            return new GiftReadTransport.Received(GiftReadTransportCodec.decodeEnvelope(bytes(reply)));
        }
        private JsonNode actualCandidate(Context context, RootProjection root) {
            JsonNode result = tree(FactionCandidateCodec.encodeCandidateResult(FactionCandidateCodec.evaluatePrivateCandidate(
                    context.snapshot().original().bytes(), root, bytes(scenario.get("private_result")), GiftRouteCoordinator.MINIMUM_RESERVE_RAW)));
            assertEquals(scenario.get("observed_candidate"), result, "actual Java candidate must match real old producer before downstream inputs");
            return result;
        }
        @Override public FactionThreatObserver.Request currentThreatInputs(FactionGiftChoice.Selected gift, Context context) {
            threatReads++; ObjectNode input = JSON.createObjectNode();
            input.set("snapshot", scenario.get("input").get("snapshot")); input.set("history", scenario.get("input").get("history"));
            RootProjection root = FactionCandidatePolicy.latestSameFrameRoot(context.rootSearch()).root().orElseThrow();
            input.set("candidate", actualCandidate(context, root)); input.put("expected_revision", context.plannedRevision());
            return FactionThreatCodec.decodeRequest(bytes(input));
        }
        @Override public FactionThreatObserver.ExistingAlertReader originalAlertReader() {
            return new FactionThreatObserver.ExistingAlertReader() {
                @Override public boolean supportsExistingObserver() { return false; }
                @Override public FactionThreatObserver.ReadResult readExistingObserver(BigInteger revision) {
                    throw new AssertionError("all original route fixtures use actual same-frame history, never an extra RPC");
                }
            };
        }
        @Override public GiftRouteCoordinator.CashQuote currentCashQuote(FactionGiftChoice.Selected gift, RootProjection root, Context context) {
            quotedContext = context; quotedRoot = root;
            ObjectNode input = JSON.createObjectNode(); input.put("schema", GiftWarCashCodec.SCHEMA);
            input.set("snapshot", scenario.get("input").get("snapshot")); input.set("candidate", actualCandidate(context, root));
            input.set("root", tree(root.original().json()));
            for (String name : java.util.List.of("spending", "market", "market_source_frame", "mercenary_ledger")) { input.putNull(name); }
            GiftWarCashModel.Request quote = GiftWarCashCodec.decode(bytes(input));
            return new GiftRouteCoordinator.CashQuote(quote.snapshot(), quote.candidate(), quote.root());
        }
        @Override public GiftWarCashObserver.CurrentInputsPort originalCashInputs() {
            return (snapshot, root) -> readSpendingInputs();
        }
        private GiftWarCashObserver.StoredInputs readSpendingInputs() {
            cashReads++; JsonNode snapshot = scenario.get("input").get("snapshot"); RootProjection root = quotedRoot; Context context = quotedContext;
            // Run the migrated shared spending producer; the captured spending object is only the differential oracle.
            ObjectNode spendingInput = JSON.createObjectNode(); spendingInput.put("schema", FeastBudgetCodec.SCHEMA);
            spendingInput.set("snapshot", snapshot); ObjectNode bound = spendingInput.putObject("inputs");
            bound.set("actor_character_id", snapshot.get("played_character").get("character_id"));
            bound.set("snapshot_revision", snapshot.get("native_revision")); bound.set("date_raw", snapshot.get("date_raw"));
            bound.set("post_snapshot_id", snapshot.get("snapshot_id")); bound.set("queried_revision", snapshot.get("revision"));
            ObjectNode ledgers = spendingInput.putObject("ledgers");
            for (String name : java.util.List.of("construction", "faction_gift", "first_heir_marriage", "child_marriage")) { ledgers.putObject(name).putNull("pending"); }
            spendingInput.set("campaign_root", tree(root.original().json()));
            JsonNode spending = tree(FeastBudgetCodec.assess(bytes(spendingInput)));
            assertEquals(scenario.get("spending"), spending);
            ObjectNode input = JSON.createObjectNode(); input.put("schema", GiftWarCashCodec.SCHEMA);
            input.set("snapshot", snapshot); input.set("candidate", actualCandidate(context, root));
            input.set("root", tree(root.original().json())); input.set("spending", spending);
            input.set("market", scenario.get("market")); input.set("market_source_frame", scenario.get("market_source_frame"));
            input.set("mercenary_ledger", scenario.get("mercenary_ledger")); GiftWarCashModel.Request full = GiftWarCashCodec.decode(bytes(input));
            return new GiftWarCashObserver.StoredInputs(full.spending(), full.market(), full.marketSourceFrame(), full.mercenaryPending());
        }
        @Override public ExistingCheckpointPort originalCheckpointReader() {
            return () -> {
                checkpointReads++; JsonNode checkpoint = scenario.get("checkpoint");
                return checkpoint.isNull() ? Optional.empty() : Optional.of(GiftRouteCodec.decodeExistingCheckpoint(bytes(checkpoint)));
            };
        }
    }

    @Test void twentyFiveRealFullProducerCasesMatchAcrossAllSharedJavaConsumers() throws IOException {
        JsonNode captured = golden(); assertEquals(25, captured.get("cases").size()); assertEquals(13, captured.get("source_bindings").size());
        assertEquals("xar.faction-gift-route-original-producer-golden.v1", captured.get("schema").textValue());
        for (JsonNode item : captured.get("cases")) {
            Ports ports = new Ports(item.get("scenario")); GiftRouteCodec.Input input = GiftRouteCodec.decode(bytes(item.get("scenario").get("input")));
            JsonNode expected = item.get("expected");
            if (expected.get("kind").textValue().equals("error")) {
                RuntimeException failure = assertThrows(RuntimeException.class, () -> GiftRouteCoordinator.plan(input.context(), ports));
                assertEquals(expected.get("message").textValue(), failure.getMessage(), item.get("name").textValue());
            } else {
                assertEquals(expected, tree(GiftRouteCodec.encodeOutcome(input.original(), GiftRouteCoordinator.plan(input.context(), ports))), item.get("name").textValue());
            }
            JsonNode effects = item.get("effects"); assertEquals(effects.get("candidate_queries").intValue(), ports.candidateQueries);
            assertEquals(effects.get("candidate_sends").intValue(), ports.candidateSends); assertEquals(effects.get("snapshot_reads").intValue(), ports.snapshotReads);
            assertEquals(effects.get("bounded_waits").intValue(), ports.boundedWaits); assertEquals(effects.get("checkpoint_reads").intValue(), ports.checkpointReads);
        }
    }

    @Test void pendingReceiptAndColdPathsPrecedeEveryNewGiftAndCheckpointRead() throws IOException {
        for (String name : java.util.List.of("pending_receipt_precedes_cash", "pending_cold_process", "pending_equivalent_cim_birth")) {
            JsonNode scenario = scenario(name); Ports ports = new Ports(scenario); GiftRouteCodec.Input input = GiftRouteCodec.decode(bytes(scenario.get("input")));
            GiftRouteCoordinator.PlanPatch result = (GiftRouteCoordinator.PlanPatch) GiftRouteCoordinator.plan(input.context(), ports);
            assertTrue(result.patch().pending().isPresent()); assertFalse(result.patch().attachGiftAction());
            assertEquals(0, ports.candidateQueries); assertEquals(0, ports.threatReads); assertEquals(0, ports.cashReads); assertEquals(0, ports.checkpointReads);
        }
    }

    @Test void unknownBirthCannotAuthorizeColdAndSharedParserAcceptsEquivalentWindowsSpellings() throws IOException {
        JsonNode scenario = scenario("pending_unknown_birth"); Ports ports = new Ports(scenario);
        GiftRouteCodec.Input input = GiftRouteCodec.decode(bytes(scenario.get("input")));
        assertThrows(IllegalArgumentException.class, () -> GiftRouteCoordinator.plan(input.context(), ports));
        assertEquals(0, ports.candidateQueries); assertEquals(0, ports.checkpointReads);
        PendingAction pending = GiftPendingCodec.decodeLedger(bytes(scenario.get("ledger"))).pending().orElseThrow();
        assertTrue(new ProcessObservation(new ProcessIdentity(pending.sourceProcess().pid(), "2026-09-16T12:00:00.0000000Z"), pending.sourceProcess()).sameProcess(pending));
        assertFalse(new ProcessObservation(new ProcessIdentity(BigInteger.valueOf(23456), "2026-09-16T12:00:00.0000000Z"), pending.sourceProcess()).sameProcess(pending));
        ProcessIdentity historic = new ProcessIdentity(pending.sourceProcess().pid(), "same-owner");
        PendingAction literal = new PendingAction(pending.requestId(), pending.episodeRunId(), pending.sourceRoundId(), historic,
                pending.baseline(), pending.minimumGoldReserveRaw(), pending.checkpointSha256BeforeSubmit(), pending.status(), pending.ack());
        assertTrue(new ProcessObservation(historic, historic).sameProcess(literal));
        assertThrows(IllegalArgumentException.class,
                () -> new ProcessObservation(new ProcessIdentity(BigInteger.valueOf(23456), "same-owner"), historic).sameProcess(literal));
    }

    @Test void freshFrameProofRequiresWholeTurnReplanAndRoundTripsWithoutAnyDispatch() throws IOException {
        JsonNode scenario = scenario("pending_fresh_frame_requires_whole_turn_replan"); Ports ports = new Ports(scenario);
        GiftRouteCodec.Input input = GiftRouteCodec.decode(bytes(scenario.get("input")));
        GiftRouteCoordinator.ReadOnlyReplan replan = (GiftRouteCoordinator.ReadOnlyReplan) GiftRouteCoordinator.plan(input.context(), ports);
        assertEquals(replan.proof(), GiftPendingFrameCodec.decodeProof(GiftPendingFrameCodec.encodeProof(replan.proof())));
        assertEquals(1, ports.boundedWaits); assertEquals(0, ports.candidateSends); assertEquals(0, ports.checkpointReads);
        assertFalse(replan.proof().businessSubmissionAttempted()); assertFalse(replan.proof().receiptQueryAttempted());
        assertFalse(replan.proof().giftSubmissionReplayed());
        assertEquals("return", tree(GiftRouteCodec.encodeOutcome(input.original(), new GiftRouteCoordinator.PlanPatch(GiftRouteCoordinator.Patch.keep()))).get("kind").textValue());
        assertEquals(BigInteger.valueOf(412), tree(input.original().bytes()).get("revision").bigIntegerValue());
    }

    @Test void optionalCashDeferralKeepsWarClockAndNeverRequestsSaveOrBuildsNewAction() throws IOException {
        for (String name : java.util.List.of("war_cash_floor_preserves_clock", "query_native_frame_crossed_defer", "market_unknown_preserves_clock", "stock_not_dangerous")) {
            JsonNode scenario = scenario(name); Ports ports = new Ports(scenario); GiftRouteCodec.Input input = GiftRouteCodec.decode(bytes(scenario.get("input")));
            GiftRouteCoordinator.PlanPatch patch = (GiftRouteCoordinator.PlanPatch) GiftRouteCoordinator.plan(input.context(), ports);
            JsonNode plan = tree(GiftRouteCodec.encodePlan(input.original(), patch)).get("plan");
            assertEquals("life-advance", plan.get("selected_step").textValue()); assertEquals("native_war_no_safe_route_defensive_hold_progress", plan.get("phase").textValue());
            assertFalse(plan.has("faction_gift_action")); assertFalse(plan.get("faction_gift_spending_deferred_v1").get("new_gift_spending_authorized").booleanValue());
            assertEquals(0, ports.checkpointReads); assertEquals(1, ports.candidateSends);
            if (!name.equals("market_unknown_preserves_clock")) { assertEquals(0, ports.cashReads, "decisive lower-bound/source/threat refusal must not read optional spending ledgers"); }
        }
    }

    @Test void checkpointIsSameDateEpisodeReferenceAndRejectsMalformedLegacyDigest() throws IOException {
        JsonNode scenario = scenario("ready_typed_submit_plan"); GiftRouteCodec.Input input = GiftRouteCodec.decode(bytes(scenario.get("input")));
        CheckpointRead valid = GiftRouteCodec.decodeExistingCheckpoint(bytes(scenario.get("checkpoint")));
        assertTrue(GiftRouteCoordinator.currentCheckpoint(input.context().snapshot(), input.context().episodeRunId(), () -> Optional.of(valid)).isPresent());
        ObjectNode changed = scenario.get("checkpoint").deepCopy(); changed.put("sha256", "x".repeat(64));
        assertTrue(GiftRouteCoordinator.currentCheckpoint(input.context(), () -> Optional.of(GiftRouteCodec.decodeExistingCheckpoint(bytes(changed)))).isEmpty());
        changed.put("sha256", "a".repeat(64)); changed.putNull("episode_run_id");
        assertTrue(GiftRouteCoordinator.currentCheckpoint(input.context(), () -> Optional.of(GiftRouteCodec.decodeExistingCheckpoint(bytes(changed)))).isEmpty());
    }

    @Test void exactInputFieldsAndRawIntegerTokensRejectCoercionAndCopiesStayImmutable() throws IOException {
        String source = scenario("ready_typed_submit_plan").get("input").toString();
        for (String token : java.util.List.of("true", "412.0", "412e0", "\"412\"")) {
            String raw = source.replace("\"revision\":412", "\"revision\":" + token);
            assertThrows(ContractViolationException.class, () -> GiftRouteCodec.decode(raw.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode missing = scenario("ready_typed_submit_plan").get("input").deepCopy(); missing.remove("available_steps");
        assertThrows(ContractViolationException.class, () -> GiftRouteCodec.decode(bytes(missing)));
        ObjectNode extra = scenario("ready_typed_submit_plan").get("input").deepCopy(); extra.put("approved", true);
        assertThrows(ContractViolationException.class, () -> GiftRouteCodec.decode(bytes(extra)));
        GiftRouteCodec.Input input = GiftRouteCodec.decode(source.getBytes(StandardCharsets.UTF_8)); byte[] exposed = input.original().bytes(); exposed[0] = 0;
        assertEquals((byte) '{', input.original().bytes()[0]);
        ObjectNode absent = scenario("absent_plan").get("input").deepCopy(); GiftRouteCodec.Input noPlan = GiftRouteCodec.decode(bytes(absent)); Ports port = new Ports(scenario("absent_plan"));
        assertEquals(absent.get("planned"), tree(GiftRouteCodec.encodeOutcome(noPlan.original(), GiftRouteCoordinator.plan(noPlan.context(), port))).get("planned"));
        assertEquals(0, port.directoryReads); assertEquals(0, port.ledgerReads);
    }
}
