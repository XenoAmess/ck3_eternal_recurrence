package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.util.Base64;
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
        assertEquals(BigInteger.valueOf(53179344),
                RootGovernanceOpeningInputs.openingGate(f.opening, f.current.frame(), Optional.empty(), result).dateRaw());
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
        private final byte[] originalActionRecord;
        private final GovernanceOpeningDocument.Document opening;
        private final ActionReceipt parent;
        private final ExactRef life;
        private final SemanticEvidence current;
        private final Session same;
        private final OutcomeArchive archive;
        private final OrdinaryCycleTransitions cycles;
        private ContinuityState head;
        private ExactRef record;
        private byte[] cycleBytes;
        private int originalReads;

        Fixture() throws IOException {
            JsonNode data;
            try (var raw = getClass().getResourceAsStream(
                    "/org/xar/ck3/control/application/session/source56-opening-advance.json.gz")) {
                assertNotNull(raw);
                try (var gzip = new GZIPInputStream(raw)) {
                    byte[] bytes = gzip.readNBytes(1 << 20);
                    assertTrue(bytes.length < 1 << 20);
                    data = FullJsonTree.parse(bytes, 1 << 20);
                }
            }
            byte[] originalHead = binary(data.get("head"));
            assertEquals(HEAD_SHA, ActionCodec.sha256(originalHead));
            var state = ContinuityJson.parseObject(originalHead, 1 << 20);
            head = ContinuityState.fromJson(state, state.get("machine_id").textValue());
            originalOpening = binary(data.get("opening"));
            requireBytes(DomainBodies.reference(head, DomainBodies.Slot.OPENING_GATE).orElseThrow().payload(), originalOpening);
            opening = GovernanceOpeningDocument.decode(originalOpening);
            originalActionRecord = binary(data.get("action_record"));
            requireBytes(ContinuityActionJournal.recordHead(head).orElseThrow(), originalActionRecord);
            byte[] receiptBytes = binary(data.get("receipt"));
            life = ExactRef.fromJson(state.get(OrdinaryCycleTransitions.STATE_FIELD).get("pending_receipt"));
            requireBytes(life, receiptBytes);
            parent = ActionReceiptCodec.decodeReceipt(receiptBytes, null);
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
                    requireBytes((ExactRef) args[0], originalActionRecord);
                    yield ActionRecordCodec.decode(originalActionRecord, archive);
                }
                case "loadReceipt" -> {
                    originalReads++;
                    assertEquals(life, args[0]);
                    yield parent;
                }
                case "receiptReferenceOf" -> {
                    assertEquals(parent, args[0]);
                    yield life;
                }
                case "loadMaterial" -> {
                    originalReads++;
                    if (cycleBytes == null) throw new java.io.UncheckedIOException(new IOException("absent fixture cycle record"));
                    requireBytes((ExactRef) args[0], cycleBytes);
                    yield new RawJson(cycleBytes);
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

        private Optional<OrdinaryCycleTransitions.ImportedOpeningAdvance> project(ObservationIdentity frame) throws IOException {
            var owner = OrdinaryCycleTransitions.sessionFromJson(head.toJson().get(SavedContinuityBootstrap.FIELD).get("session"));
            return cycles.importedOpeningAdvance(same, owner, opening.observed(), opening.source(), frame);
        }
    }

    private static byte[] binary(JsonNode original) { return Base64.getDecoder().decode(original.textValue()); }

    private static void requireBytes(ExactRef original, byte[] received) {
        assertEquals(original.bytes(), received.length);
        assertEquals(original.sha256(), ActionCodec.sha256(received));
    }
}
