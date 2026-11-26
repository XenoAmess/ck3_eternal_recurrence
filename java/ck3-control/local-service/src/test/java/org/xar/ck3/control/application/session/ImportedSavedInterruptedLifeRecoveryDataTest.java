package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionContinuityAuthority;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionReceiptCodec;
import org.xar.ck3.control.application.action.ActionRecord;
import org.xar.ck3.control.application.action.ActionRecordCodec;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineSource;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.PortableRecoveryDataArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Recovery04 through the original imported-save admission; the Driver payload and full event history are separate evidence. */
final class ImportedSavedInterruptedLifeRecoveryDataTest {
    private static final String HEAD_SHA = "2712b29737154b0fa7ac10c814961fb36f310df560aaf3f566d3438f77656718";
    private static final String OLD_FRONTIER_FAILURE = "settled recovery requires its unsaved or fully replayable actual saved frontier";

    @Test void theNextInterruptedLifeReachesItsOriginalDriverRead() throws IOException {
        var fixture = new Fixture();
        assertEquals(57, fixture.state.sequence());
        assertEquals(56, fixture.state.settledCycles());
        assertEquals(53179344, fixture.state.settledDateRaw());

        var original = fixture.readOnlyParent();
        assertEquals(56, original.sequence());
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, original.outcome());
        assertEquals(Instant.parse("2026-11-26T11:18:00.125727300Z"), original.command().deadline());
        byte[] command = ActionCodec.encodeCommand(original.command());

        assertSame(fixture.driverRead, assertThrows(IllegalStateException.class, fixture::recover));
        assertEquals(1, fixture.driverReads);
        assertArrayEquals(command, ActionCodec.encodeCommand(fixture.readOnlyParent().command()));
        assertEquals(HEAD_SHA, ActionCodec.sha256(fixture.originalHead));
    }

    @Test void exitedImportedPreflightRetainsItsExactTwoChildrenAndOriginalDriverPath() throws IOException {
        var fixture=new Fixture();
        fixture.locked(same->{
            // The old numbered writer data is genuine. These software request bytes carry no decision or process authority.
            var source=fixture.softwareExitedSource(same);
            assertSame(fixture.driverRead,assertThrows(IllegalStateException.class,
                    ()->fixture.journal.readExitedImportedHistory(same,fixture.owner,source)));
            var campaignEpisode=source.request().episodeRunId();
            var wrongOwner=new SessionIdentity(fixture.owner.machineId(),fixture.owner.game(),campaignEpisode);
            var failure=assertThrows(ContractViolationException.class,
                    ()->fixture.journal.readExitedImportedHistory(same,wrongOwner,source));
            assertTrue(failure.getMessage().contains("exact original interrupted owner"));
            assertEquals(1,fixture.driverReads);
            var original=ContinuityActionJournal.receipts(fixture.state,fixture.archive.withSession(same));
            assertTrue(original.stream().anyMatch(receipt->receipt.sequence()==55
                    &&receipt.state() instanceof ActionState.Unknown && receipt.ack().orElseThrow().nativeOk()));
            return null;
        });
        assertEquals(HEAD_SHA,ActionCodec.sha256(fixture.originalHead));
    }

    @Test void committedV5DriverRetirementProofKeepsTheOriginalPositiveResumeUnknown() throws IOException {
        var fixture = new Fixture();
        fixture.locked(same -> {
            var source = fixture.softwareExitedSource(same);
            var parent = ContinuityActionJournal.lookup(fixture.state, source.request().parentActionId(), fixture.archive).orElseThrow();
            var oldActionHead = ContinuityActionJournal.recordHead(fixture.state).orElseThrow();
            var materials = new HashMap<ExactRef, RawJson>();
            var records = new HashMap<ExactRef, ActionRecord>();
            var receiptReferences = new HashMap<ActionReceipt, ExactRef>();
            var archive = (OutcomeArchive) Proxy.newProxyInstance(getClass().getClassLoader(), new Class<?>[]{OutcomeArchive.class},
                    (proxy, method, arguments) -> {
                        switch (method.getName()) {
                            case "withSession" -> {
                                fixture.requireSession((ContinuityStorePort.Session) arguments[0]);
                                return proxy;
                            }
                            case "preserveMaterial" -> {
                                var raw = (RawJson) arguments[0];
                                var ref = Fixture.reference(ActionCodec.sha256(raw.bytes()), raw.bytes());
                                materials.put(ref, raw);
                                return ref;
                            }
                            case "materialReferenceOf" -> {
                                for (var entry : materials.entrySet()) if (entry.getValue().equals(arguments[0])) return entry.getKey();
                            }
                            case "materialReference" -> {
                                for (var ref : materials.keySet())
                                    if (ref.sha256().equals(arguments[0]) && ref.bytes() == (Long) arguments[1]) return ref;
                            }
                            case "loadMaterial" -> {
                                if (materials.containsKey(arguments[0])) return materials.get(arguments[0]);
                            }
                            case "loadRecord" -> {
                                if (records.containsKey(arguments[0])) return records.get(arguments[0]);
                            }
                            case "receiptReferenceOf" -> {
                                if (receiptReferences.containsKey(arguments[0])) return receiptReferences.get(arguments[0]);
                            }
                            default -> { }
                        }
                        try { return method.invoke(fixture.archive, arguments); }
                        catch (InvocationTargetException failure) { throw failure.getCause(); }
                    });
            var observation = source.capture(same, parent, archive);
            long terminalSequence = Math.addExact(fixture.state.sequence(), 1);
            var terminal = new ActionReceipt(parent.version(), terminalSequence, parent.command(), parent.bodySha256(),
                    new ActionState.CompositeOperatorQuarantined(((ActionState.CompositeUnknown) parent.state()).execution(), observation));
            source.verify(same, same.head(), terminal, archive);
            byte[] terminalBytes = ActionReceiptCodec.encodeReceipt(terminal, archive);
            receiptReferences.put(terminal, Fixture.reference("terminal-receipt", terminalBytes));
            var record = new ActionRecord(terminal, Optional.of(oldActionHead));
            var recordRef = Fixture.reference("terminal-record", ActionRecordCodec.encode(record, archive));
            records.put(recordRef, record);
            var terminalDetails = StrictJson.object().put("evidence_id", parent.command().actionId() + ":" + terminalSequence);
            terminalDetails.set("source", ProposalLifecycleCodec.source(parent.command().source()));
            terminalDetails.set("receipt_ref", recordRef.toJson());
            var retirement = new WriterContracts.Request(ContinuityActionJournal.KIND, ContinuityJson.canonical(terminalDetails), List.of(recordRef, observation));
            var actionAuthority = new ActionContinuityAuthority("offline-imported-driver", archive,
                    (head, command) -> { throw Fixture.unavailable(); }, (head, receipt) -> { throw Fixture.unavailable(); }, Clock.systemUTC());
            var retired = actionAuthority.reduce(fixture.state, retirement).toJson().put("sequence", terminalSequence)
                    .put("last_event_identity", retirement.identity());
            fixture.state = ContinuityState.fromJson(retired, fixture.owner.machineId());
            var predecessor = same.head();

            // Every physical pair/source coordinate is copied byte-for-byte from the prior dual-writer
            // production material builder. The replacement attachment and administrative events are software DATA.
            var sources = fixtureData("source56-imported-v5-attachment.json.gz");
            var request = new WriterContracts.Request(SavedAttachmentAuthority.KIND, binary(sources.get("details")), List.of());
            var reduced = SavedContinuityAttachment.reduce(new SavedContinuityAttachment.Input(fixture.state,
                    request.details(), binary(sources.get("basis")), binary(sources.get("game")),
                    binary(sources.get("opening")), binary(sources.get("progress"))));
            var prepared = new WriterContracts.Prepared(predecessor, request, List.of(), List.of(), reduced, "a".repeat(64));
            var attached = reduced.toJson().put("sequence", Math.addExact(terminalSequence, 1)).put("last_event_identity", request.identity());
            fixture.state = ContinuityState.fromJson(attached, fixture.owner.machineId());
            var committed = new WriterContracts.Receipt(WriterContracts.Disposition.COMMITTED, fixture.state, request.identity(), 1, false);
            var raw = ContinuityActionJournal.receipts(fixture.state, archive);
            var snapshot = new ActionJournal.Snapshot(fixture.state.sequence(), same.head().digest(), raw,
                    new ActionJournal.BoundHistoryBasis(ExactRef.fromJson(attached.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD))));
            var game = GameGeneration.fromJson(attached.get("game_binding"));
            String session = StrictJson.text(attached.get("latest_binding").get("session_id"));
            var replacement = new SessionIdentity(fixture.owner.machineId(), game, session);
            assertThrows(IOException.class, () -> ContinuityActionJournal.committedImportedRestoreRetirement(
                    same, prepared, committed, snapshot, archive, replacement));
            fixture.committedPreparation = prepared;
            fixture.committedAttachment = committed;
            var admitted = ContinuityActionJournal.committedImportedRestoreRetirement(same, prepared, committed, snapshot, archive, replacement).orElseThrow();
            var resume = admitted.retainedResume(same, snapshot, archive).orElseThrow();
            assertEquals(55, resume.sequence());
            assertInstanceOf(ActionState.Unknown.class, resume.state());
            assertTrue(resume.ack().orElseThrow().nativeOk());
            assertEquals(raw, ContinuityActionJournal.receipts(fixture.state, archive));
            assertEquals(predecessor.state().settledDateRaw(), fixture.state.settledDateRaw());
            assertEquals(predecessor.state().settledCycles(), fixture.state.settledCycles());
            var foreign = new SessionIdentity(fixture.owner.machineId(), game, "different-software-game-session");
            assertThrows(ContractViolationException.class, () -> ContinuityActionJournal.committedImportedRestoreRetirement(
                    same, prepared, committed, snapshot, archive, foreign));
            assertImportedKeeperRestartClean(fixture, same, archive, request, sources, replacement, raw);
            return null;
        });
    }

    private static void assertImportedKeeperRestartClean(Fixture fixture, ContinuityStorePort.Session same,
            OutcomeArchive archive, WriterContracts.Request attachment, JsonNode sources, SessionIdentity replacement,
            List<ActionReceipt> originalActions) throws IOException {
        var attached = fixture.state.toJson();
        var pair = SavedAttachmentAuthority.pairFromDetails(attachment);
        var loaded = ContinuityJson.parseObject(binary(sources.get("opening")), 1 << 20);
        var retainedCycle = ContinuityJson.parseObject(archive.loadMaterial(
                ExactRef.fromJson(attached.path(WriterContracts.ORDINARY_CYCLE_FIELD).get("head"))).bytes(), 1 << 20);
        var oldSemantic = OrdinaryCycleTransitions.semanticFromJson(retainedCycle.get("semantic"));
        // The new ordinary cycle uses the archived restoration coordinates. These references recur only as
        // reducer DATA in this fixture. The fixture cannot publish a fresh observation or issue a native action.
        var observed = ProposalLifecycleCodec.observation(pair.frame());
        observed.set("game", replacement.game().toJson());
        ((ObjectNode) observed.get("frame")).put("snapshot_id", StrictJson.text(loaded.get("snapshot_id")))
                .put("native_revision", StrictJson.text(loaded.get("native_revision")));
        var semantic = new SessionPorts.SemanticEvidence(ProposalLifecycleCodec.decodeObservation(observed),
                oldSemantic.semantic(), ExactRef.fromJson(loaded.get("original_native_packet")), oldSemantic.driverStamp(),
                oldSemantic.originalDriver(), oldSemantic.observedAt());
        var retainedPending = StrictJson.object();
        for (String field : List.of("pending_cycle", "pending_checkpoint")) {
            var entry = retainedPending.putObject(field).put("present", attached.has(field));
            if (attached.has(field)) entry.set("value", attached.get(field));
        }
        String pendingDigest = ContinuityJson.digest(retainedPending);
        var cycle = StrictJson.object().put("schema", "xar.java-ordinary-cycle-state/v2")
                .put("basis_cycles", fixture.state.settledCycles()).put("completed_cycles", fixture.state.settledCycles())
                .putNull("head").putNull("pending_receipt").putNull("episode_origin").put("retained_legacy_pending_digest", pendingDigest);
        cycle.set("session", OrdinaryCycleTransitions.sessionToJson(replacement));
        cycle.set("origin_frame", observed);
        var tombstone = StrictJson.object().put("schema", "xar.java-ordinary-cycle-restore-tombstone/v2")
                .put("attachment_identity", attachment.identity()).put("retained_legacy_pending_digest", pendingDigest);
        tombstone.set("restored_session", cycle.get("session"));
        tombstone.set("restore_pair", attachment.detailsObject().get(SavedAttachmentAuthority.PAIR_DETAIL));
        for (String field : List.of(WriterContracts.ORDINARY_CYCLE_FIELD, WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,
                WriterContracts.ORDINARY_CYCLE_REBIND_FIELD)) {
            var entry = tombstone.putObject(field).put("present", attached.has(field));
            if (attached.has(field)) entry.set("value", attached.get(field));
        }
        tombstone.set("original_action_head", ContinuityActionJournal.recordHead(fixture.state).orElseThrow().toJson());
        var original = archive.preserveMaterial(new RawJson(ContinuityJson.canonical(tombstone)));
        var rebind = StrictJson.object().put("evidence_id", "software-imported-keeper-rebind")
                .put("source", WriterContracts.ORDINARY_IMPORTED_CYCLE_RESTORE_SOURCE).put("operation", "REBIND")
                .put("attachment_identity", attachment.identity()).put("attachment_head_digest", same.head().digest());
        rebind.set("session", cycle.get("session"));
        rebind.set("restore_pair", tombstone.get("restore_pair"));
        rebind.set("semantic", OrdinaryCycleTransitions.semanticToJson(semantic));
        rebind.set("previous_state_ref", original.toJson());
        rebind.set("new_cycle_state", cycle);
        fixture.applyCycle(rebind);

        var keeperCycles = new OrdinaryCycleTransitions(archive,
                (session, identity, evidence) -> { throw Fixture.unavailable(); },
                (session, identity, saved, settlement) -> { throw Fixture.unavailable(); },
                new OriginalWindowReducer.Policy(fixture.state.origin().targetDays()), fixture::requireSession);
        keeperCycles.withLocked(same, () -> {
            var keeperPredecessor = fixture.state;
            keeperCycles.requireRestartClean(same, replacement);
            assertSame(keeperPredecessor, fixture.state);
            assertEquals(originalActions, ContinuityActionJournal.receipts(fixture.state, archive));
            assertEquals(56, fixture.state.settledCycles());
            assertEquals(53179344, fixture.state.settledDateRaw());
            try {
                var incomplete = fixture.state.toJson();
                incomplete.remove(WriterContracts.ORDINARY_IMPORTED_CYCLE_ORIGIN_FIELD);
                fixture.state = ContinuityState.fromJson(incomplete, replacement.machineId());
                var failure = assertThrows(ContractViolationException.class, () -> keeperCycles.requireRestartClean(same, replacement));
                assertTrue(failure.getMessage().contains("unresolved original action remains retained"), failure::getMessage);
            } finally {
                fixture.state = keeperPredecessor;
            }
            return null;
        });
    }

    @Test void theHistoricalReaderRejectsAnotherBasisOrAnUninterruptedBatch() throws IOException {
        var fixture = new Fixture();
        var differentBasis = fixture.state.toJson();
        ((ObjectNode) differentBasis.get(WriterContracts.ORDINARY_CYCLE_FIELD)).put("basis_cycles", 55);
        fixture.state = ContinuityState.fromJson(differentBasis, fixture.owner.machineId());
        assertEquals(OLD_FRONTIER_FAILURE, assertThrows(ContractViolationException.class, fixture::recover).getMessage());

        var unfinished = fixture.originalState.toJson();
        ((ObjectNode) unfinished.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)).put("boundary", "BATCH_STARTED");
        fixture.state = ContinuityState.fromJson(unfinished, fixture.owner.machineId());
        assertEquals(OLD_FRONTIER_FAILURE, assertThrows(ContractViolationException.class, fixture::recover).getMessage());
        assertEquals(0, fixture.driverReads);
    }

    @Test void partialExpiryUsesTheLastObservedCycleInsteadOfThePhysicalSaveDate() throws IOException {
        var fixture = new Fixture();
        var original = fixture.readOnlyParent();
        var whole = fixture.state.toJson();
        var cycle = whole.get(WriterContracts.ORDINARY_CYCLE_FIELD);
        var opening = org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.decodeObservation(
                whole.get(SavedContinuityBootstrap.FIELD).get("opening"));
        assertEquals(53179344, opening.frame().identity().dateRaw().longValueExact());
        assertEquals(53179368, original.command().before().frame().identity().dateRaw().longValueExact());
        fixture.locked(session -> {
            var originals = fixture.archive.withSession(session);
            assertTrue(ContinuityBatchJournal.expiredPartialStartsAtFrontier(
                    fixture.state, whole, cycle, fixture.owner, original.command().before(), originals));
            assertFalse(ContinuityBatchJournal.expiredPartialStartsAtFrontier(
                    fixture.state, whole, cycle, fixture.owner, opening, originals));
            var actions = ContinuityActionJournal.receipts(fixture.state, originals);
            assertTrue(ContinuityBatchJournal.readOnlyPartialLifeTerminalRoot(
                    fixture.state, fixture.owner, actions, originals).isEmpty());
            assertTrue(ContinuityBatchJournal.readOnlyPendingPartialLifeCycle(
                    fixture.state, fixture.owner, actions, originals).isEmpty());
            return null;
        });
    }

    @Test void secondSoftwareSettlementKeepsTheImportedPhysicalFrontier() throws IOException {
        var fixture = new Fixture();
        var genuine = fixtureData("source56-first-imported-settlement.json.gz");
        assertEquals(2, genuine.size());
        var retain = genuine.get(0);
        var settle = genuine.get(1);
        assertEquals("43f4bb73939a748ffb52d3afd580b4a5cd56b96c88b5941e772eaf1a6eb67d04",
                ActionCodec.sha256(ContinuityJson.canonical(retain)));
        assertEquals("9997b9d453b28fc3abccd2a8f6db4e65831df77f748e5f534b1033e6d481e609",
                ActionCodec.sha256(ContinuityJson.canonical(settle)));

        fixture.state = ContinuityState.fromJson(retain.get("after"), fixture.owner.machineId());
        var firstDetails = (ObjectNode) settle.get("details");
        fixture.applyCycle(firstDetails);
        assertArrayEquals(ContinuityJson.canonical(settle.get("after")), fixture.state.canonicalBytes());
        var originalPair = fixture.state.toJson().path(SavedContinuityBootstrap.FIELD).get("checkpoint_pair");
        var firstCycle = fixture.state.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD);
        assertEquals(57, firstCycle.path("completed_cycles").asLong());

        // The new action, SEM and record below are independent software reducer inputs.
        // This fixture never supplies their native or writer admission and never updates head57.
        String batchId = "source56-software-recovery-1";
        fixture.applyBoundary(batchId, SessionPorts.JournalKind.BATCH_STARTED);
        fixture.applyBoundary(batchId, SessionPorts.JournalKind.BATCH_INTERRUPTED);
        byte[] receiptToken = "isolated software receipt without native authority".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        var receipt = new ExactRef("software-only/second-life-receipt.json", receiptToken.length, ActionCodec.sha256(receiptToken));

        var nextRetain = firstDetails.deepCopy();
        nextRetain.put("operation", "RETAIN").put("evidence_id", "RETAIN:" + receipt.sha256());
        nextRetain.set("receipt_ref", receipt.toJson());
        for (String field : List.of("semantic", "cycle_record_ref", "cycle_record")) nextRetain.putNull(field);
        fixture.applyCycle(nextRetain);

        var nextSettle = firstDetails.deepCopy();
        var semantic = (ObjectNode) nextSettle.get("semantic");
        var frame = (ObjectNode) semantic.path("frame").path("frame");
        frame.put("date_raw", "53179392").put("native_revision", "28").put("revision", "14").put("snapshot_id", "native:28");
        semantic.put("observed_at", Instant.parse(semantic.path("observed_at").asText()).plusSeconds(1).toString());
        var record = (ObjectNode) nextSettle.get("cycle_record");
        record.put("completed_cycles", 58).put("classification", "VISIBLE_GAMEPLAY");
        record.set("previous", firstCycle.get("head"));
        record.set("receipt_ref", receipt.toJson());
        record.set("semantic", semantic);
        byte[] recordBytes = ContinuityJson.canonical(record);
        var recordRef = new ExactRef("software-only/second-cycle-record.json", recordBytes.length, ActionCodec.sha256(recordBytes));
        nextSettle.put("evidence_id", "SETTLE:" + receipt.sha256() + ":" + ExactRef.fromJson(semantic.get("semantic")).sha256());
        nextSettle.set("receipt_ref", receipt.toJson());
        nextSettle.set("cycle_record_ref", recordRef.toJson());
        fixture.applyCycle(nextSettle);
        assertEquals(45, fixture.state.sequence());
        assertSecondUnsavedFrontier(fixture, originalPair, recordRef);

        fixture.state = fixture.originalState;
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, fixture.readOnlyParent().outcome());
        fixture.locked(same -> {
            var resume = ContinuityActionJournal.receipts(fixture.originalState, fixture.archive.withSession(same)).stream()
                    .filter(action -> action.sequence() == 55).findFirst().orElseThrow();
            assertInstanceOf(ActionState.Unknown.class, resume.state());
            assertTrue(resume.ack().orElseThrow().nativeOk());
            return null;
        });
        assertEquals(HEAD_SHA, ActionCodec.sha256(fixture.originalHead));
    }

    private static void assertSecondUnsavedFrontier(Fixture fixture, JsonNode originalPair, ExactRef recordRef) {
        var whole = fixture.state.toJson();
        var cycle = whole.get(WriterContracts.ORDINARY_CYCLE_FIELD);
        assertEquals(58, cycle.path("completed_cycles").asLong());
        assertEquals(56, cycle.path("basis_cycles").asLong());
        assertEquals(recordRef, ExactRef.fromJson(cycle.get("head")));
        assertTrue(cycle.path("pending_receipt").isNull());
        assertEquals(originalPair, whole.path(SavedContinuityBootstrap.FIELD).get("checkpoint_pair"));
        assertEquals(56, fixture.state.settledCycles());
        assertEquals(53179344, fixture.state.settledDateRaw());
        assertFalse(whole.hasNonNull(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));
        assertEquals(ContinuityState.Status.RUNNING, fixture.state.status());
        assertEquals(SessionPorts.JournalKind.BATCH_INTERRUPTED.name(),
                whole.path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).path("boundary").asText());

        // A cold reader gets past the imported physical frontier but still requires the original Driver.
        assertSame(fixture.driverRead, assertThrows(IllegalStateException.class, fixture::recoverSettled));
        assertEquals(1, fixture.driverReads);
    }

    private static final class Fixture implements ContinuityStorePort {
        private final byte[] originalHead;
        private final ContinuityState originalState;
        private final SessionIdentity owner;
        private final JsonNode artifacts;
        private final ExactRef initialDriverFacts;
        private final OutcomeArchive archive;
        private final ContinuityBatchJournal journal;
        private final OrdinaryCycleTransitions transitions;
        private final IllegalStateException driverRead = new IllegalStateException("fixture reached the original saved Driver read");
        private boolean held;
        private int driverReads;
        private ContinuityState state;
        private WriterContracts.Prepared committedPreparation;
        private WriterContracts.Receipt committedAttachment;

        private final Session same = (Session) Proxy.newProxyInstance(getClass().getClassLoader(), new Class<?>[]{Session.class},
                (proxy, method, args) -> {
                    requireSession((Session) proxy);
                    if (method.getName().equals("head"))
                        return new WriterContracts.Head(state, List.of(), List.of(), List.of(), false);
                    if (method.getName().equals("requireCommitted")) {
                        if (args[0] == committedPreparation && args[1] == committedAttachment) return null;
                        throw new IOException("software fixture has no matching committed attachment");
                    }
                    throw new AssertionError("test archive prefix cannot perform " + method.getName());
                });

        private Fixture() throws IOException {
            var data = fixtureData();
            originalHead = binary(data.get("head"));
            assertEquals(HEAD_SHA, ActionCodec.sha256(originalHead));
            var row = ContinuityJson.parseObject(originalHead, 1 << 20);
            originalState = ContinuityState.fromJson(row, row.get("machine_id").textValue());
            state = originalState;
            var marker = SavedContinuityBootstrap.request((ObjectNode) row.get(SavedContinuityBootstrap.FIELD)).detailsObject();
            owner = OrdinaryCycleTransitions.sessionFromJson(marker.get("session"));
            initialDriverFacts = ExactRef.fromJson(marker.get("driver_facts"));
            artifacts = data.get("artifacts");
            // Immutable locators inside the originals are archive metadata. The software test resolves only bundled bytes.
            archive = new PortableRecoveryDataArchive(this::requireSession, (reference, maximumBytes) -> {
                assertTrue(held);
                if (reference.equals(initialDriverFacts)) {
                    driverReads++;
                    throw driverRead;
                }
                var material = artifacts.get(reference.sha256());
                assertNotNull(material, "fixture archive is missing " + reference.sha256());
                return binary(material);
            }).proxy();
            transitions = new OrdinaryCycleTransitions(archive, (session, identity, semantic) -> { throw unavailable(); },
                    (session, identity, pair, settlement) -> { throw unavailable(); },
                    new OriginalWindowReducer.Policy(originalState.origin().targetDays()), this::requireSession);
            journal = new ContinuityBatchJournal(this, transitions);
        }

        private CompositeOperatorQuarantineSource softwareExitedSource(Session same) throws IOException {
            var originals=archive.withSession(same);
            var parent=ContinuityBatchJournal.readOnlyLifeRecoveryRoot(ContinuityActionJournal.receipts(state,originals)).orElseThrow();
            var requestHead=same.head();
            var command=parent.command();
            var issued=Instant.parse("2026-11-26T20:00:00Z");
            var pair=CheckpointPairCodec.decode(ContinuityJson.canonical(
                    state.toJson().path(SavedContinuityBootstrap.FIELD).get("checkpoint_pair")));
            byte[] terminal=ContinuityJson.canonical(StrictJson.object().put("software_only",true));
            var terminalReference=reference("terminal",terminal);
            var identity=StrictJson.object().put("machine_id",owner.machineId())
                    .put("episode_run_id",command.before().frame().episodeRunId()).put("parent_action_id",command.actionId())
                    .put("parent_body_sha256",parent.bodySha256()).put("expected_head_sequence",state.sequence())
                    .put("expected_head_digest",requestHead.digest()).put("issued_at_utc",issued.toString());
            identity.set("game",owner.game().toJson());
            String pairDigest=ActionCodec.sha256(CheckpointPairCodec.encode(pair));
            var decision=identity.deepCopy().put("schema",CompositeOperatorQuarantineRequest.EXITED_LIFE_DECISION_SCHEMA)
                    .put("decision",CompositeOperatorQuarantineRequest.EXITED_LIFE_DECISION)
                    .put("owner_session_id",owner.sessionId()).put("saved_pair_sha256",pairDigest)
                    .put("operator_statement","software test fixture has no authority");
            decision.set("original_terminal",terminalReference.toJson());
            byte[] decisionBytes=ContinuityJson.canonical(decision);
            var request=identity.deepCopy().put("schema",CompositeOperatorQuarantineRequest.EXITED_LIFE_SCHEMA)
                    .put("scope",CompositeOperatorQuarantineRequest.EXITED_LIFE_SCOPE)
                    .put("observation_deadline_utc",issued.plusSeconds(90).toString());
            request.set("authorized_by",reference("decision",decisionBytes).toJson());
            request.set("original_receipt_ref",originals.receiptReferenceOf(parent).toJson());
            request.putArray("prior_requests");
            var children=request.putArray("children");
            var execution=((ActionState.CompositeUnknown)parent.state()).execution();
            for(var child:execution.children())children.addObject().put("ordinal",children.size())
                    .put("action_id",child.actionId()).put("body_sha256",child.bodySha256());
            request.putObject("exited_life").put("owner_session_id",owner.sessionId()).put("saved_pair_sha256",pairDigest)
                    .set("original_terminal",terminalReference.toJson());
            byte[] requestBytes=ContinuityJson.canonical(request);
            return new CompositeOperatorQuarantineSource(reference("request",requestBytes),requestBytes,decisionBytes,owner.game(),
                    command.before().frame().episodeRunId(),command.operation(),execution.handlerId(),Clock.fixed(issued,ZoneOffset.UTC),
                    Optional.of(new RawJson(terminal)));
        }

        private static ExactRef reference(String name,byte[] bytes) {
            return new ExactRef("software-only/"+name+".json",bytes.length,ActionCodec.sha256(bytes));
        }

        private ActionReceipt readOnlyParent() throws IOException {
            return locked(session -> ContinuityBatchJournal.readOnlyLifeRecoveryRoot(
                    ContinuityActionJournal.receipts(state, archive.withSession(session))).orElseThrow());
        }

        private ContinuityBatchJournal.UnresolvedSameGameData recover() throws IOException {
            return locked(session -> journal.readUnresolvedSameGame(session, owner));
        }

        private ContinuityBatchJournal.SettledSameGameData recoverSettled() throws IOException {
            return locked(session -> journal.readSettledSameGame(session, owner));
        }

        private void applyCycle(ObjectNode details) {
            apply(new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND, ContinuityJson.canonical(details), List.of()));
        }

        private void applyBoundary(String batch, SessionPorts.JournalKind kind) {
            apply(transitions.batchRequest(new SessionPorts.JournalInput(owner, batch, kind,
                    Optional.empty(), Optional.empty(), Optional.empty(), List.of())));
        }

        private void apply(WriterContracts.Request request) {
            var next = transitions.reduce(state, request).toJson();
            next.put("sequence", state.sequence() + 1);
            next.put("last_event_identity", request.identity());
            state = ContinuityState.fromJson(next, owner.machineId());
        }

        @Override public void requireSession(Session session) { assertTrue(held); assertSame(same, session); }
        @Override public <T> T locked(SessionWork<T> work) throws IOException {
            assertFalse(held);
            held = true;
            try { return work.run(same); }
            finally { held = false; }
        }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request ignored) { throw unavailable(); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared ignored) { throw unavailable(); }
        @Override public ExactRef persistedHead() { throw unavailable(); }

        private static AssertionError unavailable() { return new AssertionError("fixture has no writer, SAVE or Native authority"); }
    }

    private static byte[] binary(JsonNode value) { return Base64.getDecoder().decode(value.textValue()); }

    private static JsonNode fixtureData() throws IOException {
        return fixtureData("source56-interrupted-recovery-prefix.json.gz");
    }

    private static JsonNode fixtureData(String resource) throws IOException {
        try (var original = ImportedSavedInterruptedLifeRecoveryDataTest.class.getResourceAsStream(resource)) {
            assertNotNull(original);
            try (var input = new GZIPInputStream(original)) {
                byte[] bytes = input.readNBytes(1 << 20);
                assertTrue(bytes.length < 1 << 20);
                return FullJsonTree.parse(bytes, 1 << 20);
            }
        }
    }
}
