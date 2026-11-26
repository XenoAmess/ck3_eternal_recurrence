package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionReceiptCodec;
import org.xar.ck3.control.application.action.ActionRecordCodec;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.PortableRecoveryDataArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Exact Source56 originals and the real SETTLE reducer, behind bounded software-only archive and writer ports. */
final class RootImportedSavedOpeningAdvanceTest {
    @Test void actualHead40RetainAndItsLaterOwnedObservationCannotMoveTheOpeningGate() throws Exception {
        var f = new Fixture();
        assertEquals(40, f.head.sequence());
        assertEquals(ContinuityState.Status.REPAIR_REQUIRED, f.head.status());
        assertTrue(f.head.toJson().get(OrdinaryCycleTransitions.STATE_FIELD).get("head").isNull());
        assertEquals(f.life, ExactRef.fromJson(f.head.toJson().get(OrdinaryCycleTransitions.STATE_FIELD).get("pending_receipt")));
        var result = f.project(f.current.frame());
        assertTrue(result.isEmpty());
        assertEquals(0, f.originalReads);
        var gate = RootGovernanceOpeningInputs.openingGate(f.opening, f.current.frame(), Optional.empty(), result);
        assertEquals(BigInteger.valueOf(53179344), gate.dateRaw());
        assertTrue(gate.dateEvidence().isEmpty());
    }

    @Test void actualSettleReducerAllowsFirstOpeningAndPreservesTheRealExistingFocusTurnShape() throws Exception {
        var f = new Fixture();
        var oldBody = DomainBodies.reference(f.head, DomainBodies.Slot.OPENING_GATE);
        f.reduceFirstSettle();
        var actual = f.project(f.current.frame()).orElseThrow();
        assertEquals(f.life, actual.lifeReceipt());
        assertEquals(f.record, actual.cycleRecord());
        assertEquals(f.current, actual.semantic());
        assertEquals(oldBody, DomainBodies.reference(f.head, DomainBodies.Slot.OPENING_GATE));
        assertEquals(56, f.head.settledCycles());
        assertEquals(53179344, f.head.settledDateRaw());
        assertEquals(57, f.head.toJson().get(OrdinaryCycleTransitions.STATE_FIELD).get("completed_cycles").longValue());

        var gate = RootGovernanceOpeningInputs.openingGate(f.opening, f.current.frame(), Optional.empty(), Optional.of(actual));
        assertEquals(OpeningStage.AWAIT_SUBMIT, gate.stage());
        assertEquals(BigInteger.valueOf(53179368), gate.dateRaw());
        assertTrue(gate.action().isEmpty() && gate.checkpoint().isEmpty());
        var storedAfterFirstExistingFocus = new GovernanceOpeningDocument.Document(f.opening.observed(), f.opening.source(),
                f.opening.sessionId(), f.opening.stage(), Optional.empty(), Optional.empty(), f.opening.originals(),
                Optional.empty(), Optional.of(f.current.frame()));
        var next = nextFrame(f.current.frame(), f.current.frame().frame().identity().player(), gate.dateRaw());
        assertEquals(gate, RootGovernanceOpeningInputs.openingGate(storedAfterFirstExistingFocus, next,
                Optional.empty(), f.project(next)));
        assertEquals(f.opening.observed(), storedAfterFirstExistingFocus.observed());
        assertEquals(Optional.of(f.current.frame()), storedAfterFirstExistingFocus.existingObserved());
        assertArrayEquals(f.originalOpening, GovernanceOpeningDocument.encode(f.opening));
        assertFalse(RootGovernanceOpeningInputs.canProjectOpeningDate(storedAfterFirstExistingFocus,
                nextFrame(next, next.frame().identity().player(), gate.dateRaw().add(BigInteger.ONE)), Optional.empty()));
    }

    @Test void theFirstSettleDoesNotQualifyAnotherActorAnotherDayOrMissingCycleRecord() throws Exception {
        var f = new Fixture();
        f.reduceFirstSettle();
        var identity = f.current.frame().frame().identity();
        assertTrue(f.project(nextFrame(f.current.frame(), identity.player(),
                identity.dateRaw().add(BigInteger.valueOf(24)))).isEmpty());
        var foreign = nextFrame(f.current.frame(), identity.player().add(BigInteger.ONE), identity.dateRaw());
        assertThrows(IllegalArgumentException.class, () -> f.project(foreign));
        f.cycleBytes = null;
        assertThrows(IOException.class, () -> f.project(f.current.frame()));
    }

    @Test void exactFirstAndSoftwareSecondSettledLifeProjectTheUnissuedOpeningToTheLatestDate() throws Exception {
        var f = new Fixture();
        var originalGate = DomainBodies.reference(f.head, DomainBodies.Slot.OPENING_GATE);
        var originalSaved = f.head.toJson().get(SavedContinuityBootstrap.FIELD);
        var ending = f.loadSecondSettle();
        var before = f.head;
        var proof = f.project(ending.frame()).orElseThrow();
        assertEquals(f.record, proof.cycleRecord());
        assertEquals(ending, proof.semantic());
        var gate = RootGovernanceOpeningInputs.openingGate(f.opening, ending.frame(), Optional.empty(), Optional.of(proof));
        assertEquals(OpeningStage.AWAIT_SUBMIT, gate.stage());
        assertEquals(BigInteger.valueOf(53179392L), gate.dateRaw());
        assertTrue(f.project(f.current.frame()).isEmpty());
        assertEquals(56, f.head.settledCycles());
        assertEquals(53179344L, f.head.settledDateRaw());
        assertSame(before, f.head);
        assertEquals(originalGate, DomainBodies.reference(f.head, DomainBodies.Slot.OPENING_GATE));
        assertEquals(originalSaved, f.head.toJson().get(SavedContinuityBootstrap.FIELD));
        assertArrayEquals(f.originalOpening, GovernanceOpeningDocument.encode(f.opening));
    }

    @Test void theSecondSettleStillRequiresTheExactFirstCycleRecord() throws Exception {
        var f = new Fixture();
        var ending = f.loadSecondSettle();
        f.cycleBodies.remove(f.firstCycle);
        assertThrows(IOException.class, () -> f.project(ending.frame()));
    }

    @Test void aSettledControlTailPreservesTheLastLifeProofAndActualOpeningDate() throws Exception {
        var f = new Fixture();
        var originalGate = DomainBodies.reference(f.head, DomainBodies.Slot.OPENING_GATE);
        var originalSaved = f.head.toJson().get(SavedContinuityBootstrap.FIELD);
        var control = f.loadControlSuffix();
        var before = f.head;
        var projection = f.project(control.frame());
        var gate = RootGovernanceOpeningInputs.openingGate(f.opening, control.frame(), Optional.empty(), projection);
        assertEquals(OpeningStage.AWAIT_SUBMIT, gate.stage());
        assertEquals(BigInteger.valueOf(53179392L), gate.dateRaw());
        assertTrue(gate.action().isEmpty() && gate.checkpoint().isEmpty());
        var proof = projection.orElseThrow();
        assertEquals("7fce6e4f379e6377d12471b83b98420e0d50d71f9fe45eab44d7a1e3b88e1bac", proof.cycleRecord().sha256());
        assertEquals("1a707ec8a3a336432eccd9753b0d700553b0dd1febe83878610b7ecdf18ae476", proof.lifeReceipt().sha256());
        assertEquals("3110d087b33043133593b696abf8699994cbf9056ab25bce669e9a496d545d93", proof.semantic().semantic().sha256());
        assertNotEquals(control, proof.semantic());
        assertTrue(proof.evidence().containsAll(List.of(proof.cycleRecord(), proof.lifeReceipt(), proof.semantic().semantic())));
        assertEquals(proof.evidence(), gate.dateEvidence());
        assertEquals(originalSaved, f.head.toJson().get(SavedContinuityBootstrap.FIELD));
        assertEquals(originalGate, DomainBodies.reference(f.head, DomainBodies.Slot.OPENING_GATE));
        assertEquals(56L, f.head.settledCycles());
        assertEquals(53179344L, f.head.settledDateRaw());
        assertSame(before, f.head);
    }

    private static ObservationIdentity nextFrame(ObservationIdentity first, BigInteger actor, BigInteger date) {
        var frame = first.frame();
        var identity = new Frame(actor, frame.identity().nativeRevision().add(BigInteger.ONE), date);
        return new ObservationIdentity(first.machineId(), first.game(),
                new ProposalFrame(identity, "fixture-next-snapshot", frame.revision().add(BigInteger.ONE), frame.episodeRunId()),
                first.observationVersion());
    }
    private static final class Fixture {
        private static final String HEAD_SHA = "c2b842b1476486db5182351c717a0154e7a9f20b8dbfcb3028b30ef6d5b07b94";
        private final byte[] originalOpening;
        private final Map<ExactRef, byte[]> actionRecords = new HashMap<>();
        private final Map<ExactRef, ActionReceipt> receipts = new HashMap<>();
        private final Map<ExactRef, byte[]> cycleBodies = new HashMap<>();
        private final GovernanceOpeningDocument.Document opening;
        private final ExactRef life;
        private final SemanticEvidence current;
        private final Session same;
        private final OutcomeArchive archive;
        private final OrdinaryCycleTransitions cycles;
        private ContinuityState head;
        private ExactRef record;
        private byte[] cycleBytes;
        private ExactRef firstCycle;
        private int originalReads;

        Fixture() throws IOException {
            var data = readFixture("source56-opening-advance.json.gz");
            byte[] originalHead = binary(data.get("head"));
            assertEquals(HEAD_SHA, ActionCodec.sha256(originalHead));
            var state = ContinuityJson.parseObject(originalHead, 1 << 20);
            head = ContinuityState.fromJson(state, state.get("machine_id").textValue());
            originalOpening = binary(data.get("opening"));
            requireBytes(DomainBodies.reference(head, DomainBodies.Slot.OPENING_GATE).orElseThrow().payload(), originalOpening);
            opening = GovernanceOpeningDocument.decode(originalOpening);
            var actionHead = ContinuityActionJournal.recordHead(head).orElseThrow();
            byte[] actionRecord = binary(data.get("action_record"));
            requireBytes(actionHead, actionRecord);
            actionRecords.put(actionHead, actionRecord);
            byte[] receiptBytes = binary(data.get("receipt"));
            life = ExactRef.fromJson(state.get(OrdinaryCycleTransitions.STATE_FIELD).get("pending_receipt"));
            requireBytes(life, receiptBytes);
            var parent = ActionReceiptCodec.decodeReceipt(receiptBytes, null);
            receipts.put(life, parent);
            assertTrue(parent.eligibleAdvance());
            current = OrdinaryCycleTransitions.semanticFromJson(data.get("current"));
            same = (Session) Proxy.newProxyInstance(getClass().getClassLoader(), new Class<?>[]{Session.class},
                    (proxy, method, args) -> {
                        if (method.getName().equals("head")) return new WriterContracts.Head(head, List.of(), List.of(), List.of(), false);
                        throw new AssertionError("read-only fixture cannot use " + method);
                    });
            archive = (OutcomeArchive) Proxy.newProxyInstance(getClass().getClassLoader(), new Class<?>[]{OutcomeArchive.class},
                    (proxy, method, args) -> readArchive(method.getName(), args));
            cycles = new OrdinaryCycleTransitions(archive, (session, owner, semantic) -> {
                throw new AssertionError("the projection reads an already-reduced cycle, so it cannot issue a new SEM");
            }, (session, owner, pair, semantic) -> {
                throw new AssertionError("opening projection cannot verify SAVE authority");
            }, new OriginalWindowReducer.Policy(head.origin().targetDays()), session -> assertSame(same, session));
        }

        @SuppressWarnings("unchecked")
        private Object readArchive(String method, Object[] args) {
            return switch (method) {
                case "inSession" -> {
                    assertSame(same, args[0]);
                    yield ((Function<OutcomeArchive, ?>) args[1]).apply(archive);
                }
                case "loadRecord" -> {
                    originalReads++;
                    byte[] bytes = actionRecords.get((ExactRef) args[0]);
                    requireBytes((ExactRef) args[0], bytes);
                    yield ActionRecordCodec.decode(bytes, archive);
                }
                case "loadReceipt" -> {
                    originalReads++;
                    yield java.util.Objects.requireNonNull(receipts.get((ExactRef) args[0]));
                }
                case "receiptReferenceOf" -> {
                    yield receipts.entrySet().stream().filter(entry -> entry.getValue().equals(args[0]))
                            .findFirst().orElseThrow().getKey();
                }
                case "loadMaterial" -> {
                    originalReads++;
                    byte[] bytes = cycleBodies.isEmpty() ? cycleBytes : cycleBodies.get((ExactRef) args[0]);
                    if (bytes == null) throw new java.io.UncheckedIOException(new IOException("absent fixture cycle record"));
                    requireBytes((ExactRef) args[0], bytes);
                    yield new RawJson(bytes);
                }
                default -> throw new AssertionError("read-only archive cannot use " + method);
            };
        }

        private void reduceFirstSettle() {
            var owner = head.toJson().get(SavedContinuityBootstrap.FIELD).get("session");
            var row = StrictJson.object().put("schema", "xar.java-ordinary-cycle-record/v1")
                    .put("classification", "ELIGIBLE_ADVANCE").put("completed_cycles", 57).putNull("previous");
            row.set("session", owner);
            row.set("receipt_ref", life.toJson());
            var semantic = OrdinaryCycleTransitions.semanticToJson(current);
            row.set("semantic", semantic);
            cycleBytes = ContinuityJson.canonical(row);
            record = new ExactRef("fixture-reduced-first-settle", cycleBytes.length, ActionCodec.sha256(cycleBytes));
            var details = StrictJson.object().put("evidence_id", "SETTLE:" + life.sha256() + ":" + current.semantic().sha256())
                    .put("source", "java-ordinary-auto-sem/v1").put("operation", "SETTLE");
            details.set("session", owner);
            details.set("receipt_ref", life.toJson());
            details.set("semantic", semantic);
            details.set("cycle_record_ref", record.toJson());
            details.set("cycle_record", row);
            head = cycles.reduce(head, new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,
                    ContinuityJson.canonical(details), List.of(life, current.semantic(), current.originalNativePacket(),
                    current.driverStamp(), current.originalDriver(), record)));
        }

        private SemanticEvidence loadSecondSettle() throws IOException {
            var data = readFixture("source56-opening-second-settle.json.gz");
            byte[] originalHead = binary(data.get("head"));
            assertEquals("1a951b024dc338bf54e15046f8d537c3fa2359303bf2bf037eb73253f7b596df", ActionCodec.sha256(originalHead));
            var state = ContinuityJson.parseObject(originalHead, 1 << 20);
            head = ContinuityState.fromJson(state, head.machineId());
            assertEquals(62, head.sequence());
            var cycle = state.get(OrdinaryCycleTransitions.STATE_FIELD);
            assertEquals(58, cycle.get("completed_cycles").longValue());
            record = ExactRef.fromJson(cycle.get("head"));
            byte[] lastBytes = binary(data.get("last_cycle"));
            requireBytes(record, lastBytes);
            cycleBodies.put(record, lastBytes);
            var last = ContinuityJson.parseObject(lastBytes, 1 << 20);
            firstCycle = ExactRef.fromJson(last.get("previous"));
            byte[] firstBytes = binary(data.get("first_cycle"));
            requireBytes(firstCycle, firstBytes);
            cycleBodies.put(firstCycle, firstBytes);
            assertEquals(life, ExactRef.fromJson(ContinuityJson.parseObject(firstBytes, 1 << 20).get("receipt_ref")));
            var receipt = ExactRef.fromJson(last.get("receipt_ref"));
            byte[] receiptBytes = binary(data.get("receipt"));
            requireBytes(receipt, receiptBytes);
            receipts.put(receipt, ActionReceiptCodec.decodeReceipt(receiptBytes, null));
            var actionHead = ContinuityActionJournal.recordHead(head).orElseThrow();
            byte[] actionRecord = binary(data.get("action_record"));
            requireBytes(actionHead, actionRecord);
            actionRecords.put(actionHead, actionRecord);
            requireBytes(DomainBodies.reference(head, DomainBodies.Slot.OPENING_GATE).orElseThrow().payload(), originalOpening);
            return OrdinaryCycleTransitions.semanticFromJson(last.get("semantic"));
        }

        private SemanticEvidence loadControlSuffix() throws IOException {
            // Reuse the existing exact first Life body and receipt for the same retained prefix.
            loadSecondSettle();
            var data = readFixture("source56-opening-control-settle.json.gz");
            byte[] importedHead = binary(data.get("head"));
            assertEquals("dd1477cb8f11c913f5541d082f4a976a6fbf355d92d2878fc88f5ff1e2f2b5f0", ActionCodec.sha256(importedHead));
            var state = ContinuityJson.parseObject(importedHead, 1 << 20);
            head = ContinuityState.fromJson(state, head.machineId());
            assertEquals(69, head.sequence());
            var originals = data.get("originals");
            PortableRecoveryDataArchive.DataSource read = (ref, maximum) -> {
                var packed = originals.get(ref.sha256());
                if (packed == null || ref.bytes() > maximum) throw new IOException("missing or oversized archived control DATA");
                byte[] bytes = binary(packed);
                requireBytes(ref, bytes);
                return bytes;
            };
            var controlArchive = new PortableRecoveryDataArchive(session -> assertSame(same, session), read).proxy();
            var actionRef = ContinuityActionJournal.recordHead(head).orElseThrow();
            var control = controlArchive.loadRecord(actionRef).receipt();
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, control.outcome());
            assertFalse(control.visibleGameplay() || control.eligibleAdvance());
            actionRecords.put(actionRef, read.read(actionRef, 1 << 20));
            var controlRef = controlArchive.receiptReferenceOf(control);
            receipts.put(controlRef, control);
            var controlCycle = ExactRef.fromJson(state.get(OrdinaryCycleTransitions.STATE_FIELD).get("head"));
            byte[] cycleBytes = read.read(controlCycle, 1 << 20);
            cycleBodies.put(controlCycle, cycleBytes);
            var record = ContinuityJson.parseObject(cycleBytes, 1 << 20);
            assertEquals("CONTROL_ONLY", record.get("classification").textValue());
            assertEquals(58, record.get("completed_cycles").longValue());
            assertEquals(controlRef, ExactRef.fromJson(record.get("receipt_ref")));
            var previousLife = ExactRef.fromJson(record.get("previous"));
            byte[] previousBytes = read.read(previousLife, 1 << 20);
            cycleBodies.put(previousLife, previousBytes);
            var prior = ContinuityJson.parseObject(previousBytes, 1 << 20);
            assertEquals(firstCycle, ExactRef.fromJson(prior.get("previous")));
            var priorReceipt = ExactRef.fromJson(prior.get("receipt_ref"));
            receipts.put(priorReceipt, controlArchive.loadReceipt(priorReceipt));
            return OrdinaryCycleTransitions.semanticFromJson(record.get("semantic"));
        }

        private Optional<OrdinaryCycleTransitions.ImportedOpeningAdvance> project(ObservationIdentity frame) throws IOException {
            var owner = OrdinaryCycleTransitions.sessionFromJson(head.toJson().get(SavedContinuityBootstrap.FIELD).get("session"));
            return cycles.importedOpeningAdvance(same, owner, opening.observed(), opening.source(), frame);
        }
    }

    private static JsonNode readFixture(String filename) throws IOException {
        try (var raw = RootImportedSavedOpeningAdvanceTest.class.getResourceAsStream(
                "/org/xar/ck3/control/application/session/"+filename)) {
            assertNotNull(raw);
            try (var gzip = new GZIPInputStream(raw)) {
                byte[] bytes = gzip.readNBytes(1 << 20);
                assertTrue(bytes.length < 1 << 20);
                return FullJsonTree.parse(bytes, 1 << 20);
            }
        }
    }

    private static byte[] binary(JsonNode original) { return Base64.getDecoder().decode(original.textValue()); }

    private static void requireBytes(ExactRef original, byte[] received) {
        assertEquals(original.bytes(), received.length);
        assertEquals(original.sha256(), ActionCodec.sha256(received));
    }
}
