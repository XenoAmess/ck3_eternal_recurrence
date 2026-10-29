package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.g2.m6.ActivityFinalState;
import org.xar.ck3.control.g2.m6.ActivityFinalStateCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;

/** Actual software transport -> strict private Packet -> same writer archive -> original guard replay. No Game claim. */
final class RootActivityFinalReadBridgeTest {
    private static final int INITIAL_DATE = ActionWriterIntegrationFixture.INITIAL_DATE_RAW;
    @TempDir Path temporary;

    @Test void originalPrivateHostedPacketRetainsUint64AndColdReplayDoesNotQueryOrMutate() throws Exception {
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("valid", selected, ActivityFinalIngressData.result())) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var packet = packet(fixture, selected.get(), same, request);
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var observed = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID), request.before()),
                        packet, request.before(), same);
                assertEquals(ActivityFinalState.Kind.FINAL_UNATTRIBUTED, observed.state().currentKind());
                assertTrue(observed.state().observedFinalAt(request.before()));
                assertEquals(packet.receipt(), observed.originalReceipt());
                assertEquals(fixture.archive.withSession(same).readReferenceOf(packet.receipt()), observed.provenance().originalRead());
                for (var guard : List.of(packet.receipt().before(), packet.receipt().after())) {
                    var originalPoint = RootGuardEvidence.writerPoint(guard.binding(), fixture.archive.withSession(same));
                    assertEquals(same.head().state().sequence(), originalPoint.sequence());
                    assertEquals(same.head().digest(), originalPoint.digest());
                }
                var flags = assertInstanceOf(ActivityFinalState.Flags.class,
                        observed.state().firstFinal().orElseThrow().instance());
                assertEquals(ActivityFinalIngressData.STAMP, flags.rawCompletionStamp().orElseThrow());
                assertFalse(observed.state().firstFinal().orElseThrow().benefitObserved());
                assertFalse(observed.state().firstFinal().orElseThrow().terminalCauseObserved());
                int reads = fixture.nativeReadWrites(), actions = fixture.nativeActionWrites();
                byte[] saved = ActivityFinalStateCodec.encode(observed.state());
                assertEquals(ActivityFinalIngressData.STAMP.toString(), StrictJson.parse(saved).at("/latest/instance/raw_stamp").textValue());
                var restored = bridge.restore(saved, same);
                assertArrayEquals(saved, ActivityFinalStateCodec.encode(restored));
                assertEquals(reads, fixture.nativeReadWrites()); assertEquals(actions, fixture.nativeActionWrites());
                assertEquals(0, actions, "the final observation must not execute Start or any world action");
                // Old API, same exact retained payload: only implementation source A becomes B.
                var sourceA = observed.provenance().producerSource();
                Path producerFile = Path.of(sourceA.path());
                byte[] sourceBBytes = "replacement Activity implementation B".getBytes(java.nio.charset.StandardCharsets.UTF_8);
                Files.write(producerFile, sourceBBytes);
                var sourceB = new ExactRef(sourceA.path(), sourceBBytes.length,
                        org.xar.ck3.control.application.action.ActionCodec.sha256(sourceBBytes));
                assertNotEquals(sourceA, sourceB);
                var replacement = ActivityFinalIngressData.installation(sourceB);
                var reloaded = new RootActivityFinalReadBridge(replacement, fixture.archive, fixture.frameLoader());
                String originalHead = same.head().digest();
                assertArrayEquals(saved, ActivityFinalStateCodec.encode(reloaded.restore(saved, same)));
                Files.delete(producerFile);
                assertArrayEquals(saved, ActivityFinalStateCodec.encode(reloaded.restore(saved, same)));
                assertEquals(sourceA, observed.provenance().producerSource());
                assertEquals(originalHead, same.head().digest());
                ObjectNode forgedAfterReload = (ObjectNode) StrictJson.parse(saved);
                ((ObjectNode) forgedAfterReload.at("/latest/instance")).put("invalidated", true);
                assertThrows(IllegalArgumentException.class,
                        () -> reloaded.restore(StrictJson.canonical(forgedAfterReload), same));
                assertEquals(reads, fixture.nativeReadWrites()); assertEquals(actions, fixture.nativeActionWrites());
                return null;
            });
        }
    }

    /**
     * Native20 3F980B0 returns parse success for both decoded false and true.
     * The persisted +421 field remains distinct from that status and from the +408 phase stamp.
     * This is the actual software Packet/archive/FrameLoader path, not a native SAVE run.
     */
    @Test void successfullyDecodedFalseFlagAndNonzeroPhaseStampCannotBecomeAColdFinalState() throws Exception {
        ObjectNode decodedFalse = (ObjectNode) StrictJson.parse(ActivityFinalIngressData.result().bytes());
        ((ObjectNode) decodedFalse.at("/activity_feast_hosted_post/hosted_activities/0"))
                .put("native_completed", false).put("native_invalidated", false);
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("decoded-false-is-active", selected,
                new RawJson(StrictJson.canonical(decodedFalse)))) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var observed = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID),
                        request.before()), packet(fixture, selected.get(), same, request), request.before(), same);
                var state = observed.state();
                assertEquals(ActivityFinalState.Kind.ACTIVE, state.currentKind());
                assertFalse(state.observedFinalAt(request.before()));
                assertTrue(state.firstFinal().isEmpty());
                var sample = state.latest().orElseThrow();
                var flags = assertInstanceOf(ActivityFinalState.Flags.class, sample.instance());
                assertFalse(flags.completed()); assertFalse(flags.invalidated());
                assertEquals(ActivityFinalIngressData.STAMP, flags.rawCompletionStamp().orElseThrow());
                assertFalse(sample.terminalCauseObserved()); assertFalse(sample.benefitObserved());
                assertFalse(sample.actionAuthorized());
                int reads = fixture.nativeReadWrites();
                byte[] original = ActivityFinalStateCodec.encode(state);
                assertTrue(StrictJson.parse(original).get("first_final").isNull());
                assertArrayEquals(original, ActivityFinalStateCodec.encode(bridge.restore(original, same)));
                // A coherent copied final-state claim must still match its genuine archived native Packet.
                ObjectNode forged = (ObjectNode) StrictJson.parse(original);
                ((ObjectNode) forged.at("/latest/instance")).put("completed", true);
                forged.set("first_final", forged.get("latest").deepCopy());
                assertThrows(IllegalArgumentException.class,
                        () -> bridge.restore(StrictJson.canonical(forged), same));
                assertArrayEquals(original, ActivityFinalStateCodec.encode(bridge.restore(original, same)));
                assertEquals(reads, fixture.nativeReadWrites());
                assertEquals(0, fixture.nativeActionWrites()); return null;
            });
        }
    }

    /** Native21 yes/no/empty text token operands never change the hosted JSON boolean contract. */
    @Test void saveTextTokenOperandsAreRejectedAtActualHostedIngressAndColdStateBoundary() throws Exception {
        for (String token : List.of("yes", "no", "")) {
            ObjectNode tokenised = (ObjectNode) StrictJson.parse(ActivityFinalIngressData.result().bytes());
            ((ObjectNode) tokenised.at("/activity_feast_hosted_post/hosted_activities/0"))
                    .put("native_completed", token);
            var selected = new AtomicReference<ActivityNativeContracts.Installation>();
            try (var fixture = fixture("save-text-token-" + (token.isEmpty() ? "empty" : token), selected,
                    new RawJson(StrictJson.canonical(tokenised)))) {
                PlanningRequest request = fixture.ready().request();
                fixture.writer.locked(same -> {
                    var outcome = fixture.reads.read(same,
                            selected.get().contract(ActivityNativeContracts.Query.HOSTED), read(request));
                    assertInstanceOf(PlanningReadResult.Unavailable.class, outcome);
                    assertEquals(0, fixture.nativeActionWrites()); return null;
                });
            }
        }
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("strict-bool-cold-original", selected, ActivityFinalIngressData.result())) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var observed = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID),
                        request.before()), packet(fixture, selected.get(), same, request), request.before(), same);
                byte[] original = ActivityFinalStateCodec.encode(observed.state());
                assertFalse(observed.state().firstFinal().orElseThrow().terminalCauseObserved());
                int reads = fixture.nativeReadWrites();
                for (String token : List.of("yes", "no", "")) {
                    ObjectNode tokenised = (ObjectNode) StrictJson.parse(original);
                    for (String key : List.of("latest", "first_final"))
                        ((ObjectNode) tokenised.at("/" + key + "/instance")).put("completed", token);
                    assertThrows(IllegalArgumentException.class,
                            () -> bridge.restore(StrictJson.canonical(tokenised), same));
                }
                assertArrayEquals(original, ActivityFinalStateCodec.encode(bridge.restore(original, same)));
                assertEquals(reads, fixture.nativeReadWrites());
                assertEquals(0, fixture.nativeActionWrites()); return null;
            });
        }
    }

    @Test void persistedFlagsCannotReplaceTheActualArchivedPacket() throws Exception {
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("tamper", selected, ActivityFinalIngressData.result())) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var packet = packet(fixture, selected.get(), same, request);
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var observed = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID), request.before()),
                        packet, request.before(), same);
                ObjectNode forged = (ObjectNode)StrictJson.parse(ActivityFinalStateCodec.encode(observed.state()));
                ((ObjectNode)forged.at("/latest/instance")).put("invalidated", true);
                assertThrows(IllegalArgumentException.class, () -> bridge.restore(StrictJson.canonical(forged), same));
                assertEquals(0, fixture.nativeActionWrites()); return null;
            });
        }
    }

    @Test void anotherGenerationIsUnknownAndSameFullIdWithDifferentHostIsRejected() throws Exception {
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("generation", selected, ActivityFinalIngressData.result())) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var packet = packet(fixture, selected.get(), same, request);
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var absent = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID + 0x0100_0000L),
                        request.before()), packet, request.before(), same).state();
                assertEquals(ActivityFinalState.Kind.UNKNOWN, absent.currentKind()); assertTrue(absent.firstFinal().isEmpty());
                return null;
            });
        }
        ObjectNode wrong = (ObjectNode)StrictJson.parse(ActivityFinalIngressData.result().bytes());
        ((ObjectNode)wrong.at("/activity_feast_hosted_post/hosted_activities/0")).put("host_character_id", 74);
        var wrongSelected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("host", wrongSelected, new RawJson(StrictJson.canonical(wrong)))) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var packet = packet(fixture, wrongSelected.get(), same, request);
                var bridge = new RootActivityFinalReadBridge(wrongSelected.get(), fixture.archive, fixture.frameLoader());
                assertThrows(IllegalArgumentException.class, () -> bridge.observe(
                        ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID), request.before()),
                        packet, request.before(), same));
                assertEquals(0, fixture.nativeActionWrites()); return null;
            });
        }
    }

    @Test void malformedNativeFlagIsRejectedByTheActualInstalledIngress() throws Exception {
        ObjectNode wrong = (ObjectNode)StrictJson.parse(ActivityFinalIngressData.result().bytes());
        ((ObjectNode)wrong.at("/activity_feast_hosted_post/hosted_activities/0")).put("native_completed", 1);
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("wrong-type", selected, new RawJson(StrictJson.canonical(wrong)))) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var outcome = fixture.reads.read(same, selected.get().contract(ActivityNativeContracts.Query.HOSTED), read(request));
                assertInstanceOf(PlanningReadResult.Unavailable.class, outcome);
                assertEquals(0, fixture.nativeActionWrites()); return null;
            });
        }
    }

    /** Generic manager jobs wait for integer state2 OR3; hosted Activity flags have their own strict boolean producer. */
    @Test void genericJobTerminalCodesAreUnavailableAtTheActualHostedPacketIngress() throws Exception {
        for (int terminal : List.of(2, 3)) {
            ObjectNode wrong = (ObjectNode) StrictJson.parse(ActivityFinalIngressData.result().bytes());
            ((ObjectNode) wrong.at("/activity_feast_hosted_post/hosted_activities/0"))
                    .put("native_completed", terminal);
            var selected = new AtomicReference<ActivityNativeContracts.Installation>();
            try (var fixture = fixture("generic-job-state-" + terminal, selected, new RawJson(StrictJson.canonical(wrong)))) {
                PlanningRequest request = fixture.ready().request();
                fixture.writer.locked(same -> {
                    var outcome = fixture.reads.read(same,
                            selected.get().contract(ActivityNativeContracts.Query.HOSTED), read(request));
                    assertInstanceOf(PlanningReadResult.Unavailable.class, outcome);
                    assertEquals(0, fixture.nativeActionWrites()); return null;
                });
            }
        }
    }

    /** Retaining copied native fields cannot move original query provenance to another Game birth. */
    @Test void retainedFullIdentityAndFinalFlagsCannotRelabelTheOriginalArchiveToAnotherGameBirth() throws Exception {
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("saved-flags-original-game", selected, ActivityFinalIngressData.result())) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var origin = ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID), request.before());
                var observed = bridge.observe(origin, packet(fixture, selected.get(), same, request), request.before(), same);
                assertEquals(ActivityFinalState.Kind.FINAL_UNATTRIBUTED, observed.state().currentKind());
                assertFalse(observed.state().firstFinal().orElseThrow().terminalCauseObserved());
                assertFalse(observed.state().firstFinal().orElseThrow().benefitObserved());
                int reads = fixture.nativeReadWrites();
                byte[] original = ActivityFinalStateCodec.encode(observed.state());
                assertArrayEquals(original, ActivityFinalStateCodec.encode(bridge.restore(original, same)));
                var oldGame = request.before().game();
                BigInteger birth = oldGame.creationFiletime().value();
                BigInteger differentBirth = birth.equals(BigInteger.ONE) ? BigInteger.TWO : birth.subtract(BigInteger.ONE);
                var anotherBirth = new GameGeneration(oldGame.pid(),
                        new PythonOnlyUInt64(differentBirth));
                assertNotEquals(oldGame, anotherBirth);
                ObjectNode originOnly = (ObjectNode) StrictJson.parse(original);
                ((ObjectNode) originOnly.get("origin")).set("game", anotherBirth.toJson());
                assertThrows(IllegalArgumentException.class,
                        () -> bridge.restore(StrictJson.canonical(originOnly), same));
                ObjectNode allSamples = (ObjectNode) StrictJson.parse(original);
                ((ObjectNode) allSamples.get("origin")).set("game", anotherBirth.toJson());
                for (String key : List.of("latest", "first_final")) {
                    var retained = allSamples.get(key);
                    if (!retained.isNull()) ((ObjectNode) retained.get("queried")).set("game", anotherBirth.toJson());
                }
                assertEquals(StrictJson.parse(original).get("identity"), allSamples.get("identity"));
                assertEquals(StrictJson.parse(original).at("/latest/instance"), allSamples.at("/latest/instance"));
                assertThrows(IllegalArgumentException.class,
                        () -> bridge.restore(StrictJson.canonical(allSamples), same));
                assertArrayEquals(original, ActivityFinalStateCodec.encode(bridge.restore(original, same)));
                assertEquals(reads, fixture.nativeReadWrites());
                assertEquals(0, fixture.nativeActionWrites()); return null;
            });
        }
    }

    @Test void physicallyArchivedFutureWriterPointCannotGrantLiveOrColdFinalQualification() throws Exception {
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("future-head", selected, ActivityFinalIngressData.result())) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var actual = fixture.archive.withSession(same);
                var originalPacket = packet(fixture, selected.get(), same, request);
                var original = originalPacket.receipt();
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var origin = ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID), request.before());
                byte[] legitimate = ActivityFinalStateCodec.encode(bridge.observe(origin, originalPacket, request.before(), same).state());
                assertEquals(1, original.before().binding().supportingEvidence().size());
                ExactRef originalBasis = original.before().binding().supportingEvidence().getFirst();
                ObjectNode adversarial = (ObjectNode)StrictJson.parse(actual.loadMaterial(originalBasis).bytes());
                assertEquals("xar.java.root-guard-original-basis/v3", adversarial.get("schema").textValue());
                ((ObjectNode)adversarial.get("writer_point")).put("sequence", Math.addExact(same.head().state().sequence(), 1));
                // Deliberately archived adversarial input: physical existence and correct native bytes grant no ancestry.
                ExactRef futureBasis = actual.preserveMaterial(new RawJson(StrictJson.canonical(adversarial)));
                var forged = new PlanningReadReceipt(original.request(), original.contractId(), original.requestId(),
                        replaceBasis(original.before(), futureBasis), original.after(), original.original());
                ExactRef forgedRead = actual.preserveRead(forged);
                var strictButUnqualified = selected.get().contract(ActivityNativeContracts.Query.HOSTED).decode(forged);
                assertThrows(IOException.class, () -> bridge.observe(origin, strictButUnqualified, request.before(), same));
                ObjectNode cold = (ObjectNode)StrictJson.parse(legitimate);
                ((ObjectNode)cold.at("/latest/provenance")).set("original_read", forgedRead.toJson());
                ((ObjectNode)cold.at("/first_final/provenance")).set("original_read", forgedRead.toJson());
                assertThrows(IOException.class, () -> bridge.restore(StrictJson.canonical(cold), same));
                assertEquals(0, fixture.nativeActionWrites()); return null;
            });
        }
    }

    /**
     * Native31 routes key0x2820 through the manager secondary+4F8 receiver, whereas
     * Activity key0x2820 targets the distinct completed byte. These adversarial JSON
     * carriers assert no native SAVE payload format; they exercise the actual typed boundary.
     */
    @Test void managerKey2820PayloadCannotReplaceAnActivityFlagAtLiveOrColdIngress() throws Exception {
        for (String carrier : List.of("[]", "{}")) {
            ObjectNode wrong = (ObjectNode) StrictJson.parse(ActivityFinalIngressData.result().bytes());
            ((ObjectNode) wrong.at("/activity_feast_hosted_post/hosted_activities/0"))
                    .set("native_completed", StrictJson.parse(carrier.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            var selected = new AtomicReference<ActivityNativeContracts.Installation>();
            try (var fixture = fixture("manager-payload-" + (carrier.equals("[]") ? "array" : "object"),
                    selected, new RawJson(StrictJson.canonical(wrong)))) {
                PlanningRequest request = fixture.ready().request();
                fixture.writer.locked(same -> {
                    var outcome = fixture.reads.read(same,
                            selected.get().contract(ActivityNativeContracts.Query.HOSTED), read(request));
                    assertInstanceOf(PlanningReadResult.Unavailable.class, outcome);
                    assertEquals(0, fixture.nativeActionWrites()); return null;
                });
            }
        }
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("manager-cold-payload", selected, ActivityFinalIngressData.result())) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var observed = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID),
                        request.before()), packet(fixture, selected.get(), same, request), request.before(), same);
                byte[] original = ActivityFinalStateCodec.encode(observed.state());
                int reads = fixture.nativeReadWrites();
                for (String carrier : List.of("[]", "{}")) {
                    ObjectNode forged = (ObjectNode) StrictJson.parse(original);
                    for (String key : List.of("latest", "first_final"))
                        ((ObjectNode) forged.at("/" + key + "/instance")).set("completed", StrictJson.parse(carrier.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                    assertThrows(IllegalArgumentException.class,
                            () -> bridge.restore(StrictJson.canonical(forged), same));
                }
                assertArrayEquals(original, ActivityFinalStateCodec.encode(bridge.restore(original, same)));
                assertFalse(observed.state().firstFinal().orElseThrow().terminalCauseObserved());
                assertFalse(observed.state().firstFinal().orElseThrow().benefitObserved());
                assertEquals(reads, fixture.nativeReadWrites());
                assertEquals(0, fixture.nativeActionWrites()); return null;
            });
        }
    }

    /** Activity completion and replay retain their real meaning without publishing a canonical SAVE. */
    @Test void completedActivityAndItsColdReplayLeaveTheActualSavedFrontierUnsaved() throws Exception {
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("activity-completed-unsaved-frontier", selected, ActivityFinalIngressData.result())) {
            var semantic = new NativeSemanticEvidenceVerifier(
                    (same, reference, maximum) -> fixture.archive.readArtifact(same, reference, maximum));
            var cycles = new OrdinaryCycleTransitions(fixture.archive, semantic,
                    (same, source, pair, completed) -> {
                        throw new AssertionError("Activity observation or replay must not verify or publish a SAVE");
                    }, new OriginalWindowReducer.Policy(10958), fixture.writer::requireSession);
            cycles.bindTerminalFrameLoader(fixture.frameLoader());
            for (String kind : cycles.kinds()) fixture.bindAdditionalTransitionAuthority(kind, cycles);
            var journal = new ContinuityBatchJournal(fixture.writer, cycles);
            var owner = fixture.observationIdentity();
            var ready = fixture.ready();
            var proof = journal.cycleProof(owner, ready.semanticEvidence().orElseThrow()).orElseThrow();
            PlanningRequest request = ready.request();
            fixture.writer.locked(same -> {
                var before = journal.currentSavedFrontier(same, owner, proof);
                assertTrue(before.checkpointRequired());
                assertTrue(before.pair().isEmpty());
                String head = same.head().digest();
                long savedDate = same.head().state().settledDateRaw();
                long savedCycles = same.head().state().settledCycles();
                byte[] canonical = ContinuityJson.canonical(same.head().state().toJson());
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var observed = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID),
                        request.before()), packet(fixture, selected.get(), same, request), request.before(), same);
                assertEquals(ActivityFinalState.Kind.FINAL_UNATTRIBUTED, observed.state().currentKind());
                assertTrue(assertInstanceOf(ActivityFinalState.Flags.class,
                        observed.state().latest().orElseThrow().instance()).completed());
                byte[] persisted = ActivityFinalStateCodec.encode(observed.state());
                int reads = fixture.nativeReadWrites(), actions = fixture.nativeActionWrites();
                var restored = bridge.restore(persisted, same);
                assertArrayEquals(persisted, ActivityFinalStateCodec.encode(restored));
                assertFalse(restored.firstFinal().orElseThrow().terminalCauseObserved());
                assertFalse(restored.firstFinal().orElseThrow().benefitObserved());
                var after = journal.currentSavedFrontier(same, owner, proof);
                assertTrue(after.checkpointRequired());
                assertEquals(before.pair(), after.pair());
                assertEquals(head, same.head().digest());
                assertArrayEquals(canonical, ContinuityJson.canonical(same.head().state().toJson()));
                assertEquals(savedDate, same.head().state().settledDateRaw());
                assertEquals(savedCycles, same.head().state().settledCycles());
                assertEquals(reads, fixture.nativeReadWrites());
                assertEquals(actions, fixture.nativeActionWrites());
                assertEquals(0, actions);
                return null;
            });
        }
    }

    @Test void removedInstanceUsesTheActualDecodedCutAndColdReplayPreservesTheUnknownOtherByte() throws Exception {
        var selected = new AtomicReference<ActivityNativeContracts.Installation>();
        try (var fixture = fixture("retained-cut-removed-instance", selected,
                journalResult(ActivityFinalIngressData.FULL_ID, INITIAL_DATE, null, 255, false))) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                var observed = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID),
                        request.before()), packet(fixture, selected.get(), same, request), request.before(), same);
                var retained = assertInstanceOf(ActivityFinalState.RetainedFlags.class,
                        observed.state().firstFinal().orElseThrow().instance());
                assertTrue(retained.completedRaw().isEmpty()); assertEquals(255, retained.invalidatedRaw().orElseThrow());
                assertEquals(ActivityFinalIngressData.STAMP, retained.captureSequence());
                assertEquals(BigInteger.valueOf(INITIAL_DATE), retained.capturedDateRaw());
                assertEquals(ActivityFinalIngressData.STAMP, retained.rawCompletionStamp().orElseThrow());
                assertFalse(observed.state().observedFinalAt(request.before()));
                assertFalse(observed.state().firstFinal().orElseThrow().benefitObserved());
                assertFalse(observed.state().firstFinal().orElseThrow().terminalCauseObserved());
                assertFalse(observed.state().firstFinal().orElseThrow().actionAuthorized());
                byte[] saved = ActivityFinalStateCodec.encode(observed.state());
                int reads = fixture.nativeReadWrites();
                assertArrayEquals(saved, ActivityFinalStateCodec.encode(bridge.restore(saved, same)));
                ObjectNode changed = (ObjectNode) StrictJson.parse(saved);
                for (String field : List.of("latest", "first_final"))
                    ((ObjectNode) changed.at("/" + field + "/instance")).put("invalidated_raw", 1);
                assertThrows(IllegalArgumentException.class, () -> bridge.restore(StrictJson.canonical(changed), same));
                assertEquals(reads, fixture.nativeReadWrites()); assertEquals(0, fixture.nativeActionWrites()); return null;
            });
        }
    }

    @Test void currentHostedFalseFlagsAndUnreadFlagsTakePrecedenceOverTheHistoricalCut() throws Exception {
        for (boolean readable : List.of(true, false)) {
            ObjectNode wire = (ObjectNode) StrictJson.parse(journalResult(
                    ActivityFinalIngressData.FULL_ID, INITIAL_DATE, 1, 1, true).bytes());
            if (!readable) {
                ObjectNode row = (ObjectNode) wire.at("/activity_feast_hosted_post/hosted_activities/0");
                row.remove(List.of("terminal_flags_observed", "native_completed", "native_invalidated"));
            }
            var selected = new AtomicReference<ActivityNativeContracts.Installation>();
            try (var fixture = fixture("current-flags-over-cut-" + readable, selected, new RawJson(StrictJson.canonical(wire)))) {
                PlanningRequest request = fixture.ready().request();
                fixture.writer.locked(same -> {
                    var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                    var state = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID),
                            request.before()), packet(fixture, selected.get(), same, request), request.before(), same).state();
                    assertEquals(readable ? ActivityFinalState.Kind.ACTIVE : ActivityFinalState.Kind.UNKNOWN, state.currentKind());
                    assertTrue(state.firstFinal().isEmpty());
                    byte[] saved = ActivityFinalStateCodec.encode(state);
                    assertArrayEquals(saved, ActivityFinalStateCodec.encode(bridge.restore(saved, same)));
                    assertEquals(0, fixture.nativeActionWrites()); return null;
                });
            }
        }
    }

    @Test void unmatchedNonterminalAndRejectedCutsCannotReplaceAMissingInstance() throws Exception {
        for (int variant : List.of(0, 1, 2)) {
            ObjectNode wire = (ObjectNode) StrictJson.parse(journalResult(
                    variant == 0 ? ActivityFinalIngressData.FULL_ID + 0x0100_0000L : ActivityFinalIngressData.FULL_ID,
                    INITIAL_DATE, null, variant == 1 ? 0 : 1, false).bytes());
            if (variant == 2) ((ObjectNode) wire.at("/activity_feast_hosted_post/native_terminal_observations/records/0"))
                    .put("type_key", "activity_hunt");
            var selected = new AtomicReference<ActivityNativeContracts.Installation>();
            try (var fixture = fixture("unqualified-cut-" + variant, selected, new RawJson(StrictJson.canonical(wire)))) {
                PlanningRequest request = fixture.ready().request();
                fixture.writer.locked(same -> {
                    var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                    var state = bridge.observe(ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID),
                            request.before()), packet(fixture, selected.get(), same, request), request.before(), same).state();
                    assertInstanceOf(ActivityFinalState.Missing.class, state.latest().orElseThrow().instance());
                    assertTrue(state.firstFinal().isEmpty()); assertEquals(0, fixture.nativeActionWrites()); return null;
                });
            }
        }
    }

    @Test void exactCutStillCannotCrossTheOriginalStartToQueryDateWindow() throws Exception {
        for (int captureDate : List.of(Math.subtractExact(INITIAL_DATE, CampaignCalendar.TICKS_PER_DAY),
                Math.addExact(INITIAL_DATE, CampaignCalendar.TICKS_PER_DAY))) {
            var selected = new AtomicReference<ActivityNativeContracts.Installation>();
            try (var fixture = fixture("cut-date-window-" + captureDate, selected,
                    journalResult(ActivityFinalIngressData.FULL_ID, captureDate, null, 1, false))) {
                PlanningRequest request = fixture.ready().request();
                fixture.writer.locked(same -> {
                    var bridge = new RootActivityFinalReadBridge(selected.get(), fixture.archive, fixture.frameLoader());
                    var origin = ActivityFinalState.empty(identity(ActivityFinalIngressData.FULL_ID), request.before());
                    var original = packet(fixture, selected.get(), same, request);
                    assertThrows(IllegalArgumentException.class, () -> bridge.observe(origin, original, request.before(), same));
                    assertTrue(origin.firstFinal().isEmpty()); assertEquals(0, fixture.nativeActionWrites()); return null;
                });
            }
        }
    }

    /** Controlled bytes pass through the actual native decoder, transport, archive and guard replay. */
    private static RawJson journalResult(long fullId, int captureDate, Integer completed, Integer invalidated, boolean hosted) {
        ObjectNode root = (ObjectNode) StrictJson.parse(ActivityFinalIngressData.result().bytes());
        ObjectNode body = (ObjectNode) root.get("activity_feast_hosted_post");
        if (hosted) ((ObjectNode) body.at("/hosted_activities/0")).put("native_completed", false).put("native_invalidated", false);
        else body.putArray("hosted_activities");
        ObjectNode journal = body.putObject("native_terminal_observations");
        journal.put("schema", "activity_terminal_observations_12004_v1").put("available", true).putNull("unavailable_reason");
        journal.put("observer_attached", true).put("process_lifetime", true).put("read_only", true)
                .put("query_thread_id_u32", 7).put("query_actor_full_id_u32", 73).put("record_capacity", 64)
                .put("earliest_retained_sequence_u64", ActivityFinalIngressData.STAMP)
                .put("latest_capture_sequence_u64", ActivityFinalIngressData.STAMP)
                .put("overflow_dropped_count_u64", 0).put("record_count", 1);
        ObjectNode row = journal.putArray("records").addObject();
        row.put("capture_sequence_u64", ActivityFinalIngressData.STAMP).put("capture_thread_id_u32", 7)
                .put("source_cut_rva_u64", 0x29BF68CL).put("manager_identity_u64", 4096)
                .put("activity_identity_u64", 8192).put("type_identity_u64", 12288)
                .put("activity_full_id_u32", fullId).put("activity_instance_generation_u8", fullId >>> 24)
                .put("host_character_id_i32", 73).put("type_key", "activity_feast");
        row.put("completed_observed", completed != null).put("invalidated_observed", invalidated != null);
        if (completed == null) row.putNull("completed_raw_u8"); else row.put("completed_raw_u8", completed);
        if (invalidated == null) row.putNull("invalidated_raw_u8"); else row.put("invalidated_raw_u8", invalidated);
        row.put("native_completion_stamp_observed", true).put("native_completion_stamp_raw_u64", ActivityFinalIngressData.STAMP);
        row.putObject("capture_frame").put("date_raw_i64", captureDate).put("actor_character_id_i32", 73)
                .put("owner_thread_id_u32", 7).put("paused", true).put("map_ready", true)
                .put("has_played_character", true).put("played_character_alive", true);
        return new RawJson(StrictJson.canonical(root, 65_536));
    }

    private static PlanningReadGuard replaceBasis(PlanningReadGuard original, ExactRef adversarialBasis) {
        GuardEvidence old = original.binding();
        var replacement = new GuardEvidence(old.origin(), old.source(), old.sessionId(), old.connectionGeneration(),
                old.operation(), old.nativeEvidence(), old.capabilityEvidence(), old.authorityId(), old.observedAt(),
                old.validUntil(), List.of(adversarialBasis));
        return new PlanningReadGuard(replacement, original.paused(), original.mapReady(), original.playerAlive(),
                original.originalBindingSha256());
    }

    private ActionWriterIntegrationFixture fixture(String name,
            AtomicReference<ActivityNativeContracts.Installation> selected, RawJson originalResult) throws IOException {
        var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario(
                ActivityFinalIngressData.SOFTWARE_PROFILE_SHA, ActivityFinalIngressData.SOFTWARE_PROFILE_ADAPTER,
                source -> {
                    var installed = ActivityFinalIngressData.installation(source); selected.set(installed);
                    return List.of(installed.contract(ActivityNativeContracts.Query.HOSTED));
                }, request -> {
                    assertEquals(ActivityNativeContracts.Query.HOSTED.step(), request.step()); return originalResult;
                });
        return new ActionWriterIntegrationFixture(temporary.resolve(name), false, scenario);
    }
    private static ActivityNativeContracts.Packet packet(ActionWriterIntegrationFixture fixture,
            ActivityNativeContracts.Installation selected, Session same, PlanningRequest request) {
        var outcome = fixture.reads.read(same, selected.contract(ActivityNativeContracts.Query.HOSTED), read(request));
        var known = assertInstanceOf(PlanningReadResult.Known.class, outcome);
        return assertInstanceOf(ActivityNativeContracts.Packet.class, known.value());
    }
    private static PlanningReadRequest read(PlanningRequest request) {
        return new PlanningReadRequest(request.before(), request.source(), request.sessionId(),
                ActivityNativeContracts.Query.HOSTED.operation(), new OpportunityJson.Obj(Map.of()), Instant.now().plusSeconds(20));
    }
    private static ActivityFinalState.Identity identity(long fullId) {
        return new ActivityFinalState.Identity("canonical-start-software-fixture", fullId, 73, "activity_feast");
    }
}
