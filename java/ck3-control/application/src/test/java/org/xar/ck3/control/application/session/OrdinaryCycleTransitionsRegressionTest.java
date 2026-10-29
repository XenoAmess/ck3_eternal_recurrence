package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Actual application producer/journal/authority/reducer; the store and native evidence are explicit test ports. */
final class OrdinaryCycleTransitionsRegressionTest {
    private static final Instant TIME = Instant.parse("2026-10-23T20:00:00Z");
    private static final SessionIdentity OWNER = new SessionIdentity("fixture-machine-1",
            new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001"))), "ordinary-1");
    private static final ExactRef REF = ref("source", "a");
    private static ExactRef ref(String name, String digit) { return new ExactRef("D:/fixture/" + name + ".json", 1, digit.repeat(64)); }
    private static ObservationIdentity frame(long revision, long date, String snapshot) {
        return new ObservationIdentity(OWNER.machineId(), OWNER.game(), new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(revision), BigInteger.valueOf(date)), snapshot, BigInteger.valueOf(revision), "episode-1"), 1);
    }
    private static SemanticEvidence semantic(ObservationIdentity frame, Instant time) {
        return new SemanticEvidence(frame, ref("semantic-" + time.getEpochSecond(), "b"), ref("native", "c"), ref("driver-stamp", "d"), ref("driver", "e"), time);
    }
    @Test void operatorDataCannotUseAnAbsentOrRejectingInstalledPrivateSourceToWriteACycle()throws IOException {
        Fixture fixture=new Fixture(true);var data=OperatorRebindConsumerTest.data();
        SessionIdentity owner=new SessionIdentity(data.actual().command().origin().machineId(),data.actual().command().origin().game(),data.actual().command().sessionId());
        byte[] original=fixture.store.current.canonicalBytes();int commits=fixture.store.commits;
        assertThrows(IOException.class,()->fixture.journal.acceptOperatorRebound(owner,data.actual(),data.semantic()));
        var checks=new java.util.concurrent.atomic.AtomicInteger();
        fixture.authority.bindOperatorAuthority((same,expected,actual,semantic)->{
            assertSame(fixture.store.session,same);assertTrue(fixture.store.open);assertSame(data.actual(),actual);assertSame(data.semantic(),semantic);
            checks.incrementAndGet();throw new IOException("no genuine installed Root private execution input in this DATA test");
        });
        assertThrows(IllegalArgumentException.class,()->fixture.authority.bindOperatorAuthority((a,b,c,e)->{}));
        // Canonical source validation occurs before this callback for the unrelated DATA receipt.
        assertThrows(IllegalArgumentException.class,()->fixture.journal.acceptOperatorRebound(owner,data.actual(),data.semantic()));
        assertEquals(0,checks.get());assertEquals(commits,fixture.store.commits);assertArrayEquals(original,fixture.store.current.canonicalBytes());
        assertTrue(fixture.archive.materials.isEmpty());
    }
    @Test void operatorPureReducerPreservesEveryOriginalFieldAndRejectsNewCycleCreditOrAnotherPredecessor() {
        Fixture fixture=new Fixture(true);var data=OperatorRebindConsumerTest.data();
        SessionIdentity owner=new SessionIdentity(data.actual().command().origin().machineId(),data.actual().command().origin().game(),data.actual().command().sessionId());
        ObjectNode before=fixture.store.current.toJson();ObjectNode retained=StrictJson.object();retained.put("explicit_data_marker","original slot, not a qualified Saved material");
        before.set(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,retained);ContinuityState original=ContinuityState.fromJson(before,OWNER.machineId());
        ObjectNode state=StrictJson.object();state.put("schema","xar.java-ordinary-cycle-state/v2");state.set("session",OrdinaryCycleTransitions.sessionToJson(owner));
        state.put("basis_cycles",3);state.put("completed_cycles",3);state.putNull("head");state.putNull("pending_receipt");state.putNull("retained_legacy_pending_digest");
        state.set("origin_frame",org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(data.semantic().frame()));state.set("episode_origin",REF.toJson());
        ObjectNode row=StrictJson.object();row.put("evidence_id","operator-cycle:explicit-data");row.put("source","java-private-operator-cycle/v1");row.put("operation","OPERATOR_REBIND");
        row.set("session",OrdinaryCycleTransitions.sessionToJson(owner));row.set("operator_receipt_ref",REF.toJson());row.put("predecessor_head_digest",ContinuityJson.digest(original.toJson()));
        row.set("semantic",OrdinaryCycleTransitions.semanticToJson(data.semantic()));row.set("previous_state_ref",REF.toJson());row.set("new_cycle_state",state);
        var request=new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,ContinuityJson.canonical(row),List.of(REF));
        ContinuityState reduced=fixture.authority.reduce(original,request);ObjectNode expected=original.toJson();
        expected.set(WriterContracts.ORDINARY_CYCLE_FIELD,state);expected.set(WriterContracts.ORDINARY_CYCLE_REBIND_FIELD,REF.toJson());
        assertTrue(ContinuityJson.same(expected,reduced.toJson()));assertEquals(3,reduced.settledCycles());assertEquals(original.settledDateRaw(),reduced.settledDateRaw());
        assertEquals(retained,reduced.toJson().get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));
        for(String field:List.of("basis_cycles","completed_cycles")){
            ObjectNode changed=row.deepCopy();((ObjectNode)changed.get("new_cycle_state")).put(field,4);
            assertThrows(IllegalArgumentException.class,()->fixture.authority.reduce(original,new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,ContinuityJson.canonical(changed),List.of(REF))));
            for(String wrongType:List.of("true","3.0")) {
                ObjectNode typed=row.deepCopy();
                ((ObjectNode)typed.get("new_cycle_state")).set(field,StrictJson.parse(wrongType.getBytes(StandardCharsets.UTF_8),1024));
                assertThrows(IllegalArgumentException.class,()->fixture.authority.reduce(original,new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,ContinuityJson.canonical(typed),List.of(REF))));
            }
        }
        ObjectNode changed=row.deepCopy();changed.put("predecessor_head_digest","0".repeat(64));
        assertThrows(IllegalArgumentException.class,()->fixture.authority.reduce(original,new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,ContinuityJson.canonical(changed),List.of(REF))));
        // Pure reducer DATA is deliberately not offered to a real writer as a qualified Root admission.
    }
    @Test void canonicalAutoPlusFreshSemCountsOnceAndOnlyPairedSaveCreditsDays() throws IOException {
        Fixture fixture = new Fixture(false); ActionReceipt auto = fixture.receipt;
        SemanticEvidence after = semantic(frame(2, 24024, "after-sem"), TIME.plusSeconds(3));
        assertTrue(fixture.journal.cycleProof(OWNER, semantic(frame(1, 24000, "before-sem"), TIME)).isPresent());
        fixture.journal.retainCycle(OWNER, auto);
        assertTrue(fixture.journal.cycleProof(OWNER, after).isEmpty());
        CompletedCycleProof completed = fixture.journal.settleCycle(OWNER, auto, after);
        assertEquals(4, completed.completedCycles()); assertEquals(3, fixture.store.current.settledCycles());
        assertEquals(24000, fixture.store.current.settledDateRaw());
        int writes = fixture.store.commits;
        fixture.journal.retainCycle(OWNER, auto);
        assertEquals(4, fixture.journal.settleCycle(OWNER, auto, after).completedCycles());
        assertEquals(writes, fixture.store.commits);
        String authority = fixture.store.locked(session -> fixture.authority.verifyCompletedCycleProof(session, OWNER, completed));
        CheckpointPair pair = pair(after.frame());
        JournalCommit saved = fixture.journal.commit(new JournalInput(OWNER, "batch-1", JournalKind.SAVE_CONFIRMED,
                Optional.of(pair.frame()), Optional.of(pair), Optional.of(completed), List.of(pair.save().reference(), pair.driver().reference(), pair.nativeAckRef())));
        assertEquals(1, saved.committedSavedDays()); assertEquals(4, fixture.store.current.settledCycles());
        assertEquals(24024, fixture.store.current.settledDateRaw()); assertEquals(2, fixture.checkpointChecks); // preview and commit both revalidate
        assertEquals(authority, fixture.store.locked(session -> fixture.authority.verifyCompletedCycleProof(session, OWNER, completed)));
    }
    @Test void zeroDayControlAcceptsSameNativeRevisionButGrantsNoCycleDayOrCheckpointCredit() throws IOException {
        Fixture fixture = new Fixture(true);
        fixture.journal.retainCycle(OWNER, fixture.receipt);
        var proof = fixture.journal.settleCycle(OWNER, fixture.receipt, semantic(frame(1, 24000, "fresh-modal"), TIME.plusSeconds(3)));
        assertEquals(3, proof.completedCycles()); assertFalse(fixture.receipt.visibleGameplay()); assertFalse(fixture.receipt.eligibleAdvance());
        assertEquals(24000, fixture.store.current.settledDateRaw()); assertEquals(0, fixture.checkpointChecks);
        assertEquals("CONTROL_ONLY", fixture.archive.latestMaterial().get("classification").textValue());
    }
    @Test void saveRevisionContinuationUsesOnlyTheExactSavedBranchAndGrantsNoAdditionalCycle() throws IOException {
        Fixture fixture=new Fixture(false);fixture.journal.retainCycle(OWNER,fixture.receipt);
        var before=semantic(frame(2,24024,"before-save"),TIME.plusSeconds(3));
        CompletedCycleProof proof=fixture.journal.settleCycle(OWNER,fixture.receipt,before);
        CheckpointPair pair=pair(frame(3,24024,"actual-pair-post-save"));
        fixture.journal.commit(new JournalInput(OWNER,"save-with-new-revision",JournalKind.SAVE_CONFIRMED,
                Optional.of(pair.frame()),Optional.of(pair),Optional.of(proof),List.of(REF)));
        var post=semantic(frame(3,24024,"fresh-after-save"),TIME.plusSeconds(6));
        assertEquals(proof.completedCycles(),fixture.journal.cycleProof(OWNER,post).orElseThrow().completedCycles());
        assertEquals(4,fixture.store.current.settledCycles());assertEquals(24024,fixture.store.current.settledDateRaw());
        assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(OWNER,
                semantic(frame(4,24024,"unproved-next-native"),TIME.plusSeconds(7))));
        String retained=fixture.store.locked(same->fixture.authority.verifyCompletedCycleProof(same,OWNER,proof));
        assertEquals(retained,fixture.store.locked(same->fixture.authority.verifyCompletedCycleProof(same,OWNER,proof)));
    }
    @Test void saveContinuationCannotChangeDateOrRegressEitherRevision() throws IOException {
        Fixture fixture=new Fixture(false);fixture.journal.retainCycle(OWNER,fixture.receipt);
        var before=semantic(frame(2,24024,"before-save"),TIME.plusSeconds(3));
        CompletedCycleProof proof=fixture.journal.settleCycle(OWNER,fixture.receipt,before);byte[] original=fixture.store.current.canonicalBytes();
        for(ObservationIdentity changed:List.of(frame(3,24048,"future-date"),frame(1,24024,"old-native"),
                new ObservationIdentity(OWNER.machineId(),OWNER.game(),new JointBudgetSelector.ProposalFrame(
                        new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(3),BigInteger.valueOf(24024)),
                        "old-public",BigInteger.ONE,"episode-1"),1))) {
            CheckpointPair pair=pair(changed);
            assertThrows(IllegalArgumentException.class,()->fixture.journal.commit(new JournalInput(OWNER,"invalid-save",JournalKind.SAVE_CONFIRMED,
                    Optional.of(pair.frame()),Optional.of(pair),Optional.of(proof),List.of(REF))));
            assertArrayEquals(original,fixture.store.current.canonicalBytes());
        }
        assertEquals(0,fixture.checkpointChecks);
    }
    @Test void retainedHistoricalCycleCannotTrustAProvidedHeadWithoutTheActualWriterAncestryVerifier() throws IOException {
        Fixture fixture=new Fixture(false);fixture.journal.retainCycle(OWNER,fixture.receipt);
        var proof=fixture.journal.settleCycle(OWNER,fixture.receipt,semantic(frame(2,24024,"actual-after"),TIME.plusSeconds(3)));
        ContinuityState captured=fixture.store.current;int commits=fixture.store.commits;
        assertThrows(IOException.class,()->fixture.store.locked(same->fixture.authority.verifyHistoricalCompletedCycleProof(same,OWNER,proof,captured)));
        assertEquals(commits,fixture.store.commits);assertEquals(captured,fixture.store.current);
    }
    @Test void ackAndUnknownCannotBeRetainedAsACompletedAuto() {
        Fixture fixture = new Fixture(false);
        ActionReceipt unknown = new ActionReceipt(1, 1, fixture.receipt.command(), fixture.receipt.bodySha256(),
                new ActionState.Unknown(Optional.empty(), Optional.empty(), "actual outcome lost", List.of(REF)));
        fixture.install(unknown);
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.retainCycle(OWNER, unknown));
        assertEquals(0, fixture.store.commits); assertFalse(fixture.store.current.toJson().has(OrdinaryCycleTransitions.STATE_FIELD));
    }
    @Test void sameOrStaleTerminalSemCannotSettleAndActualPendingReceiptSurvives() throws IOException {
        Fixture fixture = new Fixture(false); fixture.journal.retainCycle(OWNER, fixture.receipt); byte[] pending = fixture.store.current.canonicalBytes();
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.settleCycle(OWNER, fixture.receipt,
                semantic(frame(2, 24024, "terminal-reused"), TIME.plusSeconds(2))));
        assertArrayEquals(pending, fixture.store.current.canonicalBytes()); assertEquals(1, fixture.store.commits);
    }
    @Test void verifierFailureInsideActualLockPreventsTheSettleMutation() throws IOException {
        Fixture fixture = new Fixture(false); fixture.journal.retainCycle(OWNER, fixture.receipt); fixture.rejectSemantic = true;
        assertThrows(IOException.class, () -> fixture.journal.settleCycle(OWNER, fixture.receipt,
                semantic(frame(2, 24024, "after"), TIME.plusSeconds(3))));
        assertEquals(1, fixture.store.commits); assertEquals(3, fixture.store.current.settledCycles());
        assertNotNull(fixture.store.current.toJson().get(OrdinaryCycleTransitions.STATE_FIELD).get("pending_receipt"));
    }
    @Test void changedActorOrEpisodeAndRegressingNativeRevisionAreRejectedWithoutCounterCredit() throws IOException {
        Fixture fixture = new Fixture(false); fixture.journal.retainCycle(OWNER, fixture.receipt);
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.settleCycle(OWNER, fixture.receipt,
                semantic(frame(1, 24024, "regressed-native"), TIME.plusSeconds(3))));
        var wrong = new ObservationIdentity(OWNER.machineId(), OWNER.game(), new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29830), BigInteger.TWO, BigInteger.valueOf(24024)), "wrong-actor", BigInteger.TWO, "episode-2"), 1);
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.settleCycle(OWNER, fixture.receipt, semantic(wrong, TIME.plusSeconds(3))));
        assertEquals(1, fixture.store.commits);
    }
    @Test void anUnsettledOriginalPythonAutoIsPreservedAndNeverConvertedToJavaCredit() {
        Fixture fixture = new Fixture(false); ObjectNode state = fixture.store.current.toJson(); ObjectNode pending = state.putObject("pending_cycle");
        pending.put("stage", "auto_unsettled"); pending.put("auto_sequence", 11558); state.putArray("unknown_requests").add(11558);
        fixture.store.current = ContinuityState.fromJson(state, OWNER.machineId()); byte[] before = fixture.store.current.canonicalBytes();
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.retainCycle(OWNER, fixture.receipt));
        assertArrayEquals(before, fixture.store.current.canonicalBytes()); assertEquals(0, fixture.store.commits);
    }
    @Test void aForgedCycleCountOrFutureFrameCannotGrantSavedDays() throws IOException {
        Fixture fixture = new Fixture(false); fixture.journal.retainCycle(OWNER, fixture.receipt);
        var semantic = semantic(frame(2, 24024, "after"), TIME.plusSeconds(3)); var proof = fixture.journal.settleCycle(OWNER, fixture.receipt, semantic);
        var forged = new CompletedCycleProof(5, semantic, proof.cycleStateDigest()); var pair = pair(semantic.frame());
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.commit(new JournalInput(OWNER, "forged", JournalKind.SAVE_CONFIRMED,
                Optional.of(pair.frame()), Optional.of(pair), Optional.of(forged), List.of(REF))));
        var futureSemantic = semantic(frame(3, 24048, "unearned-future"), TIME.plusSeconds(4)); var futurePair = pair(futureSemantic.frame());
        var future = new CompletedCycleProof(proof.completedCycles(), futureSemantic, proof.cycleStateDigest());
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.commit(new JournalInput(OWNER, "future", JournalKind.SAVE_CONFIRMED,
                Optional.of(futurePair.frame()), Optional.of(futurePair), Optional.of(future), List.of(REF))));
        assertEquals(24000, fixture.store.current.settledDateRaw()); assertEquals(0, fixture.checkpointChecks);
    }
    @Test void semanticAndProofRoundTripRejectMissingWrongFieldsBooleanAndFloatCycleCounts() {
        var semantic = semantic(frame(1, 24000, "sem"), TIME); var proof = new CompletedCycleProof(3, semantic, "f".repeat(64));
        assertEquals(proof, OrdinaryCycleTransitions.proofFromJson(OrdinaryCycleTransitions.proofToJson(proof)));
        ObjectNode bool = OrdinaryCycleTransitions.proofToJson(proof); bool.put("completed_cycles", true);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCycleTransitions.proofFromJson(bool));
        ObjectNode floating = OrdinaryCycleTransitions.proofToJson(proof); floating.put("completed_cycles", 3.0);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCycleTransitions.proofFromJson(floating));
        ObjectNode missing = OrdinaryCycleTransitions.semanticToJson(semantic); missing.remove("original_driver");
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCycleTransitions.semanticFromJson(missing));
        ObjectNode extra = OrdinaryCycleTransitions.semanticToJson(semantic); extra.put("completed_cycle_proof", true);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCycleTransitions.semanticFromJson(extra));
    }
    @Test void authorityRefusesHeadOnlyAndPredecessorOnlyCallsOutsideTheOriginalSession() {
        Fixture fixture = new Fixture(false); var input = new JournalInput(OWNER, "metadata", JournalKind.BATCH_STARTED, Optional.empty(), Optional.empty(), Optional.empty(), List.of());
        var request = fixture.authority.batchRequest(input);
        assertThrows(IllegalStateException.class, () -> fixture.authority.revalidate(fixture.store.current, request));
        assertThrows(IllegalArgumentException.class, () -> fixture.authority.revalidate(fixture.store.head(), request));
    }
    @Test void deferredModalBoundaryPreservesRunningButActualInterruptionUsesOriginalRepairReducer() throws IOException {
        Fixture fixture = new Fixture(true);
        fixture.journal.commit(new JournalInput(OWNER, "modal-tail", JournalKind.BATCH_DEFERRED, Optional.empty(), Optional.empty(), Optional.empty(), List.of()));
        assertEquals(ContinuityState.Status.RUNNING, fixture.store.current.status()); assertEquals(24000, fixture.store.current.settledDateRaw());
        fixture.journal.commit(new JournalInput(OWNER, "failed", JournalKind.BATCH_INTERRUPTED, Optional.empty(), Optional.empty(), Optional.empty(), List.of()));
        assertEquals(ContinuityState.Status.REPAIR_REQUIRED, fixture.store.current.status()); assertEquals(3, fixture.store.current.settledCycles());
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.cycleProof(OWNER, semantic(frame(1, 24000, "paused"), TIME.plusSeconds(3))));
    }
    @Test void sessionCodecPreservesExactFiletimeAsDecimalStringAndRejectsNumericAlternative() {
        ObjectNode json = OrdinaryCycleTransitions.sessionToJson(OWNER);
        assertTrue(json.get("game").get("creation_filetime").isTextual());
        assertEquals("134000000000000001", json.get("game").get("creation_filetime").textValue());
        assertEquals(OWNER, OrdinaryCycleTransitions.sessionFromJson(json));
        ((ObjectNode) json.get("game")).put("creation_filetime", new BigInteger("134000000000000001"));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCycleTransitions.sessionFromJson(json));
    }
    @Test void aCounterDetachedFromItsActualArchivedHeadCannotMintCycleProofOrSaveCredit() throws IOException {
        Fixture fixture = new Fixture(false); fixture.journal.retainCycle(OWNER, fixture.receipt);
        var after = semantic(frame(2, 24024, "after"), TIME.plusSeconds(3));
        fixture.journal.settleCycle(OWNER, fixture.receipt, after);
        ObjectNode row = fixture.store.current.toJson();
        ((ObjectNode) row.get(OrdinaryCycleTransitions.STATE_FIELD)).put("completed_cycles", 5);
        fixture.store.current = ContinuityState.fromJson(row, OWNER.machineId());
        int writes = fixture.store.commits;
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.cycleProof(OWNER, after));
        var forgedProof = new CompletedCycleProof(5, after, ContinuityJson.digest(row.get(OrdinaryCycleTransitions.STATE_FIELD)));
        assertThrows(IllegalArgumentException.class, () -> fixture.store.locked(session -> fixture.authority.verifyCompletedCycleProof(session, OWNER, forgedProof)));
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.settleCycle(OWNER, fixture.receipt, after));
        assertEquals(writes, fixture.store.commits); assertEquals(24000, fixture.store.current.settledDateRaw());
    }
    @Test void aNewValidArchiveObjectCannotSkipTheRetainedCycleBasis() throws IOException {
        Fixture fixture = new Fixture(false); fixture.journal.retainCycle(OWNER, fixture.receipt);
        var after = semantic(frame(2, 24024, "after"), TIME.plusSeconds(3)); fixture.journal.settleCycle(OWNER, fixture.receipt, after);
        ObjectNode forged = fixture.archive.latestMaterial().deepCopy(); forged.put("completed_cycles", 5);
        ExactRef forgedRef = fixture.archive.preserveMaterial(new RawJson(ContinuityJson.canonical(forged)));
        ObjectNode row = fixture.store.current.toJson(); ObjectNode cycle = (ObjectNode) row.get(OrdinaryCycleTransitions.STATE_FIELD);
        cycle.set("head", forgedRef.toJson()); cycle.put("completed_cycles", 5);
        fixture.store.current = ContinuityState.fromJson(row, OWNER.machineId());
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.cycleProof(OWNER, after));
        assertEquals(2, fixture.store.commits); assertEquals(3, fixture.store.current.settledCycles());
    }
    @Test void duplicateAutoIsRejectedAcrossTheWholeBranchEvenForZeroDayControlAndAnImmediateLookupHit() throws IOException {
        for (boolean controlOnly : List.of(false, true)) {
            Fixture fixture = new Fixture(controlOnly); fixture.journal.retainCycle(OWNER, fixture.receipt);
            var after = semantic(frame(controlOnly ? 1 : 2, controlOnly ? 24000 : 24024, "after"), TIME.plusSeconds(3));
            fixture.journal.settleCycle(OWNER, fixture.receipt, after);
            ObjectNode row = fixture.store.current.toJson(); ObjectNode cycle = (ObjectNode) row.get(OrdinaryCycleTransitions.STATE_FIELD);
            ObjectNode duplicate = fixture.archive.latestMaterial().deepCopy(); duplicate.set("previous", cycle.get("head"));
            duplicate.put("completed_cycles", controlOnly ? 3 : 5);
            ExactRef duplicateRef = fixture.archive.preserveMaterial(new RawJson(ContinuityJson.canonical(duplicate)));
            cycle.set("head", duplicateRef.toJson()); cycle.put("completed_cycles", controlOnly ? 3 : 5);
            fixture.store.current = ContinuityState.fromJson(row, OWNER.machineId());
            assertThrows(IllegalArgumentException.class, () -> fixture.journal.cycleProof(OWNER, after));
            assertThrows(IllegalArgumentException.class, () -> fixture.journal.settleCycle(OWNER, fixture.receipt, after));
            assertEquals(2, fixture.store.commits);
        }
    }
    @Test void anEmptyBranchCannotInventADifferentSavedFrontierAsItsBasis() throws IOException {
        Fixture fixture = new Fixture(false); fixture.journal.retainCycle(OWNER, fixture.receipt);
        ObjectNode row = fixture.store.current.toJson(); ObjectNode cycle = (ObjectNode) row.get(OrdinaryCycleTransitions.STATE_FIELD);
        cycle.put("basis_cycles", 5); cycle.put("completed_cycles", 5); cycle.putNull("pending_receipt");
        fixture.store.current = ContinuityState.fromJson(row, OWNER.machineId());
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.cycleProof(OWNER, semantic(frame(1, 24000, "before"), TIME)));
        assertEquals(1, fixture.store.commits); assertEquals(3, fixture.store.current.settledCycles());
    }
    @Test void anotherStoreWithTheSameHeadCannotBorrowTheOriginalCycleAuthority() throws IOException {
        Fixture fixture = new Fixture(false); Store other = new Store(); other.current = fixture.store.current; other.authority = fixture.authority;
        var foreignJournal = new ContinuityBatchJournal(other, fixture.authority);
        var before = semantic(frame(1, 24000, "before"), TIME);
        assertThrows(IOException.class, () -> foreignJournal.cycleProof(OWNER, before));
        assertFalse(other.open); assertFalse(fixture.store.open); assertEquals(0, other.commits);
        assertTrue(fixture.journal.cycleProof(OWNER, before).isPresent());
    }
    @Test void actualOrdinaryBusinessWithoutTimelineFlagsCountsAsVisibleGameplayThroughTheSharedReceiptContract() throws IOException {
        Fixture fixture = new Fixture(false); ActionReceipt original = fixture.receipt; var command = original.command();
        List<ExpectedValue> actual = List.of(new ExpectedText(new FieldKey("construction.status"), "queued"));
        var expected = new ExpectedPostcondition(1, command.before(), command.source(), "construction-observer/v1", actual);
        var ordinary = new ActionCommand(command.actionId(), command.before(), command.source(), command.sessionId(), command.operation(),
                command.arguments(), expected, command.claims(), command.deadline());
        var composite = (ActionState.CompositeSettled) original.state();
        var observed = ((ActionState.Applied) composite.settlement()).observation();
        var effect = new ActionState.EffectObservation(observed.after(), observed.source(), observed.sessionId(), "construction-observer/v1", actual,
                observed.provenance(), observed.observedAt(), observed.originalEvidence());
        fixture.install(new ActionReceipt(1, original.sequence(), ordinary, ActionCodec.bodySha256(ordinary),
                new ActionState.CompositeSettled(composite.execution(), new ActionState.Applied(effect))));
        assertTrue(fixture.receipt.visibleGameplay()); assertFalse(fixture.receipt.eligibleAdvance());
        fixture.journal.retainCycle(OWNER, fixture.receipt);
        var proof = fixture.journal.settleCycle(OWNER, fixture.receipt, semantic(frame(2, 24024, "after"), TIME.plusSeconds(3)));
        assertEquals(4, proof.completedCycles()); assertEquals("VISIBLE_GAMEPLAY", fixture.archive.latestMaterial().get("classification").textValue());
        assertEquals(24000, fixture.store.current.settledDateRaw());
    }
    @Test void aCycleRecordCannotRelabelAnActualBusinessReceiptAsZeroDayControl() throws IOException {
        Fixture fixture = new Fixture(false); fixture.journal.retainCycle(OWNER, fixture.receipt);
        var after = semantic(frame(2, 24024, "after"), TIME.plusSeconds(3)); fixture.journal.settleCycle(OWNER, fixture.receipt, after);
        ObjectNode forged = fixture.archive.latestMaterial().deepCopy(); forged.put("classification", "CONTROL_ONLY"); forged.put("completed_cycles", 3);
        ExactRef forgedRef = fixture.archive.preserveMaterial(new RawJson(ContinuityJson.canonical(forged)));
        ObjectNode row = fixture.store.current.toJson(); ObjectNode cycle = (ObjectNode) row.get(OrdinaryCycleTransitions.STATE_FIELD);
        cycle.set("head", forgedRef.toJson()); cycle.put("completed_cycles", 3); fixture.store.current = ContinuityState.fromJson(row, OWNER.machineId());
        assertThrows(IllegalArgumentException.class, () -> fixture.journal.cycleProof(OWNER, after));
        assertEquals(2, fixture.store.commits);
    }
    @Test void savedInitialProofRemainsValidAfterRestoreOpeningChangesTheCurrentBinding() throws IOException {
        Fixture fixture = new Fixture(true); var before = semantic(frame(1, 24000, "initial"), TIME);
        CompletedCycleProof proof = fixture.journal.cycleProof(OWNER, before).orElseThrow(); CheckpointPair pair = pair(before.frame());
        fixture.journal.commit(new JournalInput(OWNER, "initial-save", JournalKind.SAVE_CONFIRMED,
                Optional.of(pair.frame()), Optional.of(pair), Optional.of(proof), List.of(REF)));
        String checked = fixture.store.locked(session -> fixture.authority.verifyCompletedCycleProof(session, OWNER, proof));
        ObjectNode row = fixture.store.current.toJson(); ObjectNode opening = ((ObjectNode) row.get("latest_binding")).deepCopy();
        opening.put("snapshot_id", "actual-restored-opening"); opening.put("episode_run_id", "restored-episode"); row.set("latest_binding", opening);
        fixture.store.current = ContinuityState.fromJson(row, OWNER.machineId());
        assertEquals(checked, fixture.store.locked(session -> fixture.authority.verifyCompletedCycleProof(session, OWNER, proof)));
        assertEquals(0, fixture.store.current.settledDateRaw() - 24000);
    }
    @Test void episodeReducerRetainsTheActualUnsavedCountWithoutMovingTheSavedFrontierOrGrantingLiveAdmission() throws IOException {
        Fixture fixture=new Fixture(false);fixture.journal.retainCycle(OWNER,fixture.receipt);
        var after=semantic(frame(2,24024,"after"),TIME.plusSeconds(3));fixture.journal.settleCycle(OWNER,fixture.receipt,after);
        ObjectNode original=fixture.store.current.toJson();ObjectNode next=((ObjectNode)original.get(OrdinaryCycleTransitions.STATE_FIELD)).deepCopy();
        var successor=new ObservationIdentity(OWNER.machineId(),OWNER.game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29830),BigInteger.valueOf(3),BigInteger.valueOf(24024)),"successor",BigInteger.valueOf(3),"episode-2"),1);
        SemanticEvidence fresh=semantic(successor,TIME.plusSeconds(6));ExactRef retained=ref("unqualified-episode-origin","9");
        next.put("basis_cycles",4);next.put("completed_cycles",4);next.putNull("head");next.putNull("pending_receipt");
        next.set("origin_frame",org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(successor));next.set("episode_origin",retained.toJson());
        ObjectNode row=StrictJson.object();row.put("evidence_id","unqualified-episode-json");row.put("source","java-private-lifecycle-episode/v1");row.put("operation","EPISODE_REBIND");
        row.set("session",OrdinaryCycleTransitions.sessionToJson(OWNER));row.set("before_session",OrdinaryCycleTransitions.sessionToJson(OWNER));
        row.set("parent_receipt_ref",fixture.archive.receiptReferenceOf(fixture.receipt).toJson());row.put("lifecycle_commit_digest","a".repeat(64));
        row.put("predecessor_head_digest",fixture.store.head().digest());row.set("semantic",OrdinaryCycleTransitions.semanticToJson(fresh));row.set("previous_state_ref",retained.toJson());row.set("new_cycle_state",next);
        var request=new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,ContinuityJson.canonical(row),List.of(retained));
        ContinuityState reduced=fixture.authority.reduce(fixture.store.current,request);
        assertEquals(4,reduced.toJson().get(OrdinaryCycleTransitions.STATE_FIELD).get("completed_cycles").longValue());
        assertEquals(3,reduced.settledCycles());assertEquals(24000,reduced.settledDateRaw());assertEquals(original.get("latest_binding"),reduced.toJson().get("latest_binding"));
        assertEquals(original.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),reduced.toJson().get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));
        assertThrows(IllegalArgumentException.class,()->fixture.store.locked(session->fixture.authority.withLocked(session,()->session.preview(request))));
        assertEquals(2,fixture.store.commits);assertEquals(original,fixture.store.current.toJson());
        next.put("completed_cycles",5);var forged=new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,ContinuityJson.canonical(row),List.of(retained));
        assertThrows(IllegalArgumentException.class,()->fixture.authority.reduce(fixture.store.current,forged));
    }
    @Test void episodeOriginAndNullableFieldsAreStrictAndOldStateCannotClaimNewEpisodeAuthority() throws IOException {
        Fixture fixture=new Fixture(true);fixture.journal.retainCycle(OWNER,fixture.receipt);
        fixture.journal.settleCycle(OWNER,fixture.receipt,semantic(frame(1,24000,"modal"),TIME.plusSeconds(3)));
        ObjectNode base=fixture.store.current.toJson();
        for(String missing:List.of("origin_frame","episode_origin")) {
            ObjectNode changed=base.deepCopy();((ObjectNode)changed.get(OrdinaryCycleTransitions.STATE_FIELD)).remove(missing);
            fixture.store.current=ContinuityState.fromJson(changed,OWNER.machineId());
            assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(OWNER,semantic(frame(1,24000,"sem"),TIME.plusSeconds(4))));
        }
        ObjectNode old=base.deepCopy();((ObjectNode)old.get(OrdinaryCycleTransitions.STATE_FIELD)).put("schema","xar.java-ordinary-cycle-state/v1");
        fixture.store.current=ContinuityState.fromJson(old,OWNER.machineId());
        assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(OWNER,semantic(frame(1,24000,"sem"),TIME.plusSeconds(4))));
    }
    @Test void borrowedRestoreAdmissionCannotOpenANestedWriterLockOrAcceptANullToken() throws IOException {
        Fixture fixture=new Fixture(true);
        fixture.store.locked(session->{
            assertThrows(IllegalArgumentException.class,()->fixture.journal.requireCurrent(session,(ContinuityBatchJournal.ReboundCycle)null));
            assertTrue(fixture.store.open);return true;
        });
        assertFalse(fixture.store.open);assertEquals(0,fixture.store.commits);
    }
    @Test void awaitingFirstSaveCannotManufactureAnOrdinaryCycleProof() {
        Fixture fixture=new Fixture(false);NextWindow described=describeNextWindow(fixture);
        fixture.store.current=described.waiting();byte[] original=fixture.store.current.canonicalBytes();
        assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(described.owner(),described.semantic()));
        assertArrayEquals(original,fixture.store.current.canonicalBytes());assertEquals(0,fixture.store.commits);
    }
    @Test void anActiveBaselineCannotBorrowTheOldCycleOrConstructAnAbsentZeroCycle() throws IOException {
        Fixture fixture=new Fixture(true);fixture.journal.retainCycle(OWNER,fixture.receipt);
        fixture.journal.settleCycle(OWNER,fixture.receipt,semantic(frame(1,24000,"actual-control"),TIME.plusSeconds(3)));
        NextWindow described=describeNextWindow(fixture);fixture.store.current=described.active();int committed=fixture.store.commits;
        assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(described.owner(),described.semantic()));
        ObjectNode absent=fixture.store.current.toJson();absent.remove(OrdinaryCycleTransitions.STATE_FIELD);
        fixture.store.current=ContinuityState.fromJson(absent,OWNER.machineId());
        assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(described.owner(),described.semantic()));
        assertEquals(committed,fixture.store.commits);
    }
    @Test void nextWindowPureReductionPreservesOldPendingButDoesNotGrantALivePrivateAdmission() throws IOException {
        Fixture fixture=new Fixture(false);fixture.journal.retainCycle(OWNER,fixture.receipt);
        var after=semantic(frame(2,24024,"old-after"),TIME.plusSeconds(3));var oldProof=fixture.journal.settleCycle(OWNER,fixture.receipt,after);
        var saved=pair(after.frame());fixture.journal.commit(new JournalInput(OWNER,"old-window-save",JournalKind.SAVE_CONFIRMED,
                Optional.of(saved.frame()),Optional.of(saved),Optional.of(oldProof),List.of(REF)));
        ObjectNode pending=fixture.store.current.toJson();pending.putObject("pending_cycle").put("stage","old-auto-unknown");
        pending.putArray("unknown_requests").add(11558);fixture.store.current=ContinuityState.fromJson(pending,OWNER.machineId());
        NextWindow described=describeNextWindow(fixture);fixture.store.current=described.active();
        byte[] original=fixture.store.current.canonicalBytes();int committed=fixture.store.commits;
        ContinuityState reduced=fixture.authority.reduce(fixture.store.current,described.request());
        ObjectNode branch=(ObjectNode)reduced.toJson().get(OrdinaryCycleTransitions.STATE_FIELD);
        assertEquals(0,branch.get("completed_cycles").longValue());assertEquals(0,branch.get("basis_cycles").longValue());
        assertTrue(branch.get("head").isNull());assertTrue(branch.get("pending_receipt").isNull());
        assertEquals(pending.get("pending_cycle"),reduced.toJson().get("pending_cycle"));
        assertTrue(ContinuityJson.same(pending.get("unknown_requests"),reduced.toJson().get("unknown_requests")));
        assertFalse(reduced.toJson().has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));
        assertEquals(0,reduced.settledCycles());assertEquals(24000,reduced.settledDateRaw());
        assertEquals(described.active().origin(),reduced.origin());
        assertThrows(IllegalArgumentException.class,()->fixture.store.locked(same->fixture.authority.withLocked(same,()->same.preview(described.request()))));
        assertArrayEquals(original,fixture.store.current.canonicalBytes());assertEquals(committed,fixture.store.commits);
    }
    @Test void firstBaselineReductionRejectsInheritedCreditPendingHeadAndMissingOrigins() {
        Fixture fixture=new Fixture(false);NextWindow described=describeNextWindow(fixture);
        for(String field:List.of("basis_cycles","completed_cycles","head","pending_receipt","origin_frame","episode_origin","retained_legacy_pending_digest")) {
            ObjectNode row=described.request().detailsObject();ObjectNode branch=(ObjectNode)row.get("new_cycle_state");
            if(field.equals("basis_cycles")||field.equals("completed_cycles"))branch.put(field,1);
            else if(field.equals("head")||field.equals("pending_receipt"))branch.set(field,REF.toJson());
            else branch.putNull(field);
            var changed=new WriterContracts.Request(OrdinaryCycleTransitions.NEXT_BASELINE_KIND,ContinuityJson.canonical(row),List.of(REF));
            assertThrows(IllegalArgumentException.class,()->fixture.authority.reduce(described.active(),changed),field);
        }
        assertEquals(0,fixture.store.commits);
    }
    @Test void firstBaselineReductionRejectsAnotherSaveOrChangedActualActorDateAndOwner() {
        Fixture fixture=new Fixture(false);NextWindow described=describeNextWindow(fixture);
        ObjectNode otherSave=described.request().detailsObject();
        ((ObjectNode)otherSave.get("baseline").get("baseline")).put("save_action_id","another-save");
        assertThrows(IllegalArgumentException.class,()->fixture.authority.reduce(described.active(),new WriterContracts.Request(
                OrdinaryCycleTransitions.NEXT_BASELINE_KIND,ContinuityJson.canonical(otherSave),List.of(REF))));
        for(ObservationIdentity wrong:List.of(
                new ObservationIdentity(described.owner().machineId(),described.owner().game(),new JointBudgetSelector.ProposalFrame(
                        new JointBudgetSelector.Frame(BigInteger.valueOf(29830),BigInteger.TWO,BigInteger.valueOf(24000)),"wrong-actor",BigInteger.TWO,"episode-2"),1),
                new ObservationIdentity(described.owner().machineId(),described.owner().game(),new JointBudgetSelector.ProposalFrame(
                        new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.TWO,BigInteger.valueOf(24024)),"wrong-date",BigInteger.TWO,"episode-2"),1),
                frame(2,24000,"wrong-Game"))) {
            ObjectNode row=described.request().detailsObject();row.set("semantic",OrdinaryCycleTransitions.semanticToJson(semantic(wrong,TIME.plusSeconds(9))));
            assertThrows(IllegalArgumentException.class,()->fixture.authority.reduce(described.active(),new WriterContracts.Request(
                    OrdinaryCycleTransitions.NEXT_BASELINE_KIND,ContinuityJson.canonical(row),List.of(REF))));
        }
        assertEquals(0,fixture.store.commits);
    }
    @Test void firstBaselineNullTokenCannotBorrowAWriterOrOpenAnotherLock() throws IOException {
        Fixture fixture=new Fixture(true);
        fixture.store.locked(same->{
            assertThrows(IllegalArgumentException.class,()->fixture.journal.requireCurrent(same,(ContinuityBatchJournal.ReboundNextBaseline)null));
            assertTrue(fixture.store.open);return true;
        });
        assertFalse(fixture.store.open);assertEquals(0,fixture.store.commits);
    }
    /** Public descriptions exercise only the pure reducer and refusal boundaries, never private physical SAVE custody. */
    private record NextWindow(ContinuityState waiting,ContinuityState active,SessionIdentity owner,SemanticEvidence semantic,WriterContracts.Request request) { }
    private static NextWindow describeNextWindow(Fixture fixture) {
        var owner=new SessionIdentity(OWNER.machineId(),new GameGeneration(456,new PythonOnlyUInt64(new BigInteger("134000000000000099"))),"ordinary-2");
        var before=new EpisodeWindow.Identity(OWNER.machineId(),OWNER.game(),OWNER.sessionId(),"episode-1",0,29829,24000);
        var after=new EpisodeWindow.Identity(owner.machineId(),owner.game(),owner.sessionId(),"episode-2",1,29829,24000);
        var begin=new EpisodeWindow.Begin("described-next-window",before,after,1,2,"old-next-episode",1,"a".repeat(64),REF,REF,List.of());
        var pin=new WriterContracts.Pin(REF,new WriterContracts.FileIdentity("1","9007199254740993","134000000000000001",TIME.toString(),1));
        var committedBegin=new EpisodeWindow.CommittedBegin(begin,2,begin.request().identity(),"c".repeat(64),pin);
        ObjectNode beginCommitted=EpisodeWindow.reduce(fixture.store.current,begin.request()).toJson();
        beginCommitted.put("sequence",committedBegin.sequence());
        ContinuityState waiting=ContinuityState.fromJson(beginCommitted,OWNER.machineId());
        var baseline=new EpisodeWindow.Baseline(committedBegin,"actual-first-save",REF,REF.sha256(),REF,"d".repeat(64),after);
        var committedBaseline=new EpisodeWindow.CommittedBaseline(baseline,5,baseline.request().identity(),"e".repeat(64),pin);
        ObjectNode baselineCommitted=EpisodeWindow.reduce(waiting,baseline.request()).toJson();
        baselineCommitted.put("sequence",committedBaseline.sequence());
        ContinuityState active=ContinuityState.fromJson(baselineCommitted,OWNER.machineId());
        var observed=new ObservationIdentity(owner.machineId(),owner.game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.TWO,BigInteger.valueOf(24000)),"post-first-save",BigInteger.TWO,"episode-2"),1);
        var semantic=semantic(observed,TIME.plusSeconds(9));ExactRef origin=ref("described-next-window-origin","9");
        ObjectNode branch=StrictJson.object();branch.put("schema","xar.java-ordinary-cycle-state/v2");branch.set("session",OrdinaryCycleTransitions.sessionToJson(owner));
        branch.put("basis_cycles",0);branch.put("completed_cycles",0);branch.putNull("head");branch.putNull("pending_receipt");
        ObjectNode pending=StrictJson.object();ObjectNode current=active.toJson();
        for(String key:List.of("pending_cycle","pending_checkpoint")){ObjectNode slot=pending.putObject(key);slot.put("present",current.has(key));if(current.has(key))slot.set("value",current.get(key));}
        branch.put("retained_legacy_pending_digest",ContinuityJson.digest(pending));
        branch.set("origin_frame",org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(observed));branch.set("episode_origin",origin.toJson());
        ObjectNode row=StrictJson.object();row.put("evidence_id","described-next-cycle");row.put("source","java-private-first-save-baseline/v1");
        row.set("session",OrdinaryCycleTransitions.sessionToJson(owner));row.set("before_session",OrdinaryCycleTransitions.sessionToJson(OWNER));
        row.set("baseline",committedBaseline.toJson());row.put("predecessor_head_digest",ContinuityJson.digest(active.toJson()));
        row.set("semantic",OrdinaryCycleTransitions.semanticToJson(semantic));row.set("previous_state_ref",origin.toJson());row.set("new_cycle_state",branch);
        return new NextWindow(waiting,active,owner,semantic,new WriterContracts.Request(OrdinaryCycleTransitions.NEXT_BASELINE_KIND,ContinuityJson.canonical(row),List.of(origin)));
    }
    private static CheckpointPair pair(ObservationIdentity frame) {
        return new CheckpointPair(new CheckpointPair.FileWitness(ref("save", "7"), new FileStatIdentity(BigInteger.ONE, "9007199254740993", "134000000000000001")),
                new CheckpointPair.FileWitness(ref("driver", "e"), new FileStatIdentity(BigInteger.ONE, "9007199254740995", "134000000000000003")),
                frame, "lineage-1", 1, "save-1", REF, TIME.plusSeconds(4));
    }
    @Test void initialReadRevisionMayAdvanceWithoutChangingCanonicalFrontier()throws IOException {
        Fixture fixture=new Fixture(false);byte[] before=fixture.store.current.canonicalBytes();int commits=fixture.store.commits;
        var proof=fixture.journal.cycleProof(OWNER,semantic(frame(95,24000,"new-read"),TIME.plusSeconds(2))).orElseThrow();
        assertEquals(3,proof.completedCycles());assertEquals(commits,fixture.store.commits);assertArrayEquals(before,fixture.store.current.canonicalBytes());
        ObjectNode higher=fixture.store.current.toJson();((ObjectNode)higher.get("latest_binding")).put("native_revision",29);
        fixture.store.current=ContinuityState.fromJson(higher,OWNER.machineId());
        assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(OWNER,semantic(frame(28,24000,"older-read"),TIME)));
        assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(OWNER,semantic(frame(95,24024,"different-date"),TIME)));
        var changedActor=new ObservationIdentity(OWNER.machineId(),OWNER.game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29830),BigInteger.valueOf(95),BigInteger.valueOf(24000)),"other-actor",BigInteger.valueOf(95),"episode-1"),1);
        var changedEpisode=new ObservationIdentity(OWNER.machineId(),OWNER.game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(95),BigInteger.valueOf(24000)),"other-episode",BigInteger.valueOf(95),"episode-2"),1);
        for(var invalid:List.of(changedActor,changedEpisode))assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(OWNER,semantic(invalid,TIME)));
    }
    @Test void aRetainedRealCycleStillRequiresItsExactNativeIdentity()throws IOException {
        Fixture fixture=new Fixture(false);fixture.journal.retainCycle(OWNER,fixture.receipt);
        fixture.journal.settleCycle(OWNER,fixture.receipt,semantic(frame(2,24024,"settled"),TIME.plusSeconds(3)));
        assertThrows(IllegalArgumentException.class,()->fixture.journal.cycleProof(OWNER,semantic(frame(95,24024,"unrelated-read"),TIME.plusSeconds(4))));
    }
    private static final class Fixture {
        final Archive archive = new Archive(); final Store store = new Store(); final OrdinaryCycleTransitions authority; final ContinuityBatchJournal journal;
        ActionReceipt receipt; boolean rejectSemantic; int checkpointChecks;
        Fixture(boolean controlOnly) {
            authority = new OrdinaryCycleTransitions(archive, (session, owner, semantic) -> {
                assertTrue(store.open); assertSame(store.session, session); assertEquals(OWNER, owner);
                if (rejectSemantic) throw new IOException("actual archived native/Driver changed");
                return new OrdinaryCycleTransitions.VerifiedSemantic(semantic.frame(), semantic.observedAt(), "archive-" + semantic.semantic().sha256(), "f".repeat(64));
            }, (session, owner, pair, proof) -> { assertTrue(store.open); checkpointChecks++; return "a".repeat(64); }, new OriginalWindowReducer.Policy(10958),
                    session -> { if (session != store.session) throw new IOException("another writer object's session is not the original authority"); assertTrue(store.open); });
            store.authority = authority; journal = new ContinuityBatchJournal(store, authority); install(makeReceipt(controlOnly));
        }
        void install(ActionReceipt value) {
            receipt = value; ExactRef receiptRef = archive.preserveReceipt(value); assertEquals(value, archive.loadReceipt(receiptRef));
            ExactRef record = archive.preserveRecord(new ActionRecord(value, Optional.empty())); ObjectNode row = store.current.toJson();
            row.put("sequence", value.sequence()); row.set(ContinuityActionJournal.STATE_FIELD, record.toJson()); store.current = ContinuityState.fromJson(row, OWNER.machineId());
        }
        private ActionReceipt makeReceipt(boolean controlOnly) {
            var before = frame(1, 24000, "before"); var after = controlOnly ? frame(1, 24000, "modal") : frame(2, 24024, "after");
            var source = new G2Source(OWNER.machineId(), TIME.toString(), "fixture-build", REF); var operation = new OperationKey("advance_life");
            List<ExpectedValue> flags = List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), !controlOnly),
                    new ExpectedBoolean(new FieldKey("timeline.advance_verified"), !controlOnly), new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), !controlOnly),
                    new ExpectedText(new FieldKey("progress_status"), controlOnly ? "modal_pending" : "postcondition"));
            var command = new ActionCommand("auto-1", before, source, OWNER.sessionId(), operation, new OpportunityJson.Obj(Map.of()),
                    new ExpectedPostcondition(1, before, source, "fixture-observer/v1", flags), new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), TIME.plusSeconds(10));
            var guard = new GuardEvidence(before, source, OWNER.sessionId(), BigInteger.ONE, operation, REF, REF, "fixture", TIME, TIME.plusSeconds(10));
            ActionState state;
            if (controlOnly) {
                var terminal = new GuardEvidence(after, source, OWNER.sessionId(), BigInteger.ONE, new OperationKey("advance_clock_status"), REF, REF, "fixture", TIME.plusSeconds(2), TIME.plusSeconds(10));
                var readGuard = new PlanningReadGuard(terminal, true, true, true, "a".repeat(64));
                var readRequest = new PlanningReadRequest(after, source, OWNER.sessionId(), new OperationKey("advance_clock_status"), new OpportunityJson.Obj(Map.of()), TIME.plusSeconds(10));
                var raw = new RawJson("{}".getBytes(StandardCharsets.UTF_8));
                var read = new PlanningReadReceipt(readRequest, "status/v1", "status-2", readGuard, readGuard,
                        new NativeActionPort.AckReceived("status-2", true, Optional.of(raw), raw, raw.bytes()));
                var request = new NativeRequest("advance_clock_cancel", Optional.empty(), raw);
                var attempt = new ActionState.Attempt("cancel-1", TIME.plusSeconds(1), guard, request);
                state = new ActionState.Settled(attempt, new NativeActionPort.AckReceived("cancel-1", true, Optional.of(raw), raw, raw.bytes()), new ActionState.ControlApplied(read, "status/v1", flags));
            } else {
                var observed = new ActionState.EffectObservation(after, source, OWNER.sessionId(), "fixture-observer/v1", flags, new ObservationProvenance.Query("native-read-2"), TIME.plusSeconds(2), REF);
                state = new ActionState.CompositeSettled(new CompositeExecution("advance-life/v1", TIME, guard, List.of()), new ActionState.Applied(observed));
            }
            return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), state);
        }
    }
    private static final class Store implements ContinuityStorePort {
        ContinuityState current = initial(); OrdinaryCycleTransitions authority; boolean open; int commits;
        private Thread ownerThread;
        final Session session = new Session() {
            @Override public void requireWriter(java.nio.file.Path originalWriterLock) {
                throw new AssertionError("in-memory cycle fixture has no physical writer-lock authority");
            }
            @Override public WriterContracts.Pin capturePin(ExactRef reference, int maximumBytes) {
                throw new AssertionError("in-memory cycle fixture cannot capture a physical file pin");
            }
            @Override public void verifyPin(WriterContracts.Pin pin) {
                throw new AssertionError("in-memory cycle fixture cannot verify a physical file pin");
            }
            @Override public WriterContracts.Head head() { assertTrue(open); return Store.this.head(); }
            @Override public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException {
                assertTrue(open); var before = head(); String checked = authority.revalidate(before, request);
                return new WriterContracts.Prepared(before, request, List.of(), List.of(), authority.reduce(current, request), checked);
            }
            @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException {
                assertTrue(open); assertEquals(prepared.predecessor().digest(), head().digest());
                assertEquals(prepared.preconditionDigest(), authority.revalidate(head(), prepared.request()));
                var reduced = authority.reduce(current, prepared.request()); assertArrayEquals(prepared.reduced().canonicalBytes(), reduced.canonicalBytes());
                ObjectNode row = reduced.toJson(); row.put("sequence", current.sequence() + 1); current = ContinuityState.fromJson(row, OWNER.machineId()); commits++;
                return new WriterContracts.Receipt(WriterContracts.Disposition.COMMITTED, current, prepared.request().identity(), 1, false);
            }
            @Override public ExactRef persistedHead() { assertTrue(open); return REF; }
        };
        WriterContracts.Head head() { return new WriterContracts.Head(current, List.of(), List.of(), List.of(), false); }
        @Override public void requireSession(ContinuityStorePort.Session actual)throws IOException { if(!open||actual!=session||Thread.currentThread()!=ownerThread)throw new IOException("not the active original fixture writer session"); }
        @Override public <T> T locked(SessionWork<T> work) throws IOException { assertFalse(open); open = true; ownerThread = Thread.currentThread(); try { return work.run(session); } finally { open = false; ownerThread = null; } }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException { return locked(view -> view.preview(request)); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException { return locked(view -> view.commit(prepared)); }
        @Override public ExactRef persistedHead() { return REF; }
        private static ContinuityState initial() {
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", OWNER.machineId()); row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running");
            row.put("start_date_raw", 24000); row.put("target_date_raw", 286992); row.put("target_days", 10958); row.put("last_settled_cycles", 3); row.put("last_settled_date_raw", 24000); row.put("binding_lineage_count", 0);
            ObjectNode bound = row.putObject("latest_binding"); bound.put("date_raw", 24000); bound.put("actor_character_id", 29829); bound.put("episode_run_id", "episode-1"); bound.put("snapshot_id", "baseline"); bound.put("revision", 1); bound.put("native_revision", 1);
            return ContinuityState.fromJson(row, OWNER.machineId());
        }
    }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        final Map<ExactRef, ActionReceipt> receipts = new HashMap<>(); final Map<ExactRef, ActionRecord> records = new HashMap<>(); final Map<ExactRef, RawJson> materials = new HashMap<>();
        ExactRef lastMaterial;
        @Override public <T> T inSession(ContinuityStorePort.Session session, java.util.function.Function<ActionPorts.OutcomeArchive,T> work) { return work.apply(this); }
        @Override public ActionPorts.OutcomeArchive withSession(ContinuityStorePort.Session session) { return this; }
        @Override public ExactRef preserveReceipt(ActionReceipt value) { ExactRef ref = ref("receipt-" + value.sequence(), "1"); receipts.put(ref,value); return ref; }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { return Optional.ofNullable(receipts.get(ref)).orElseThrow(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { return receipts.entrySet().stream().filter(entry -> entry.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { ExactRef ref = ref("record-" + value.receipt().sequence(), "2"); records.put(ref,value); return ref; }
        @Override public ActionRecord loadRecord(ExactRef ref) { return Optional.ofNullable(records.get(ref)).orElseThrow(); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { return records.entrySet().stream().filter(entry -> entry.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserveMaterial(RawJson value) { String sha = ActionCodec.sha256(value.bytes()); ExactRef ref = new ExactRef("D:/fixture/material-" + sha + ".json", value.bytes().length, sha); materials.put(ref,value); lastMaterial=ref; return ref; }
        @Override public RawJson loadMaterial(ExactRef ref) { return Optional.ofNullable(materials.get(ref)).orElseThrow(); }
        @Override public ExactRef materialReferenceOf(RawJson value) { return materials.entrySet().stream().filter(entry -> entry.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        ObjectNode latestMaterial() { return ContinuityJson.parseObject(materials.get(lastMaterial).bytes(), ContinuityJson.DOCUMENT_MAX_BYTES); }
        private static <T> T unexpected() { throw new AssertionError("unrequested native/archive operation"); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) { return unexpected(); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original) { return unexpected(); }
        @Override public ExactRef preserveRequest(NativeRequest original) { return unexpected(); }
        @Override public NativeRequest loadRequest(ExactRef original) { return unexpected(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { return unexpected(); }
        @Override public ExactRef requestReferenceOf(NativeRequest original) { return unexpected(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt original) { return unexpected(); }
        @Override public PlanningReadReceipt loadRead(ExactRef original) { return unexpected(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { return unexpected(); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { return unexpected(); }
        @Override public byte[] loadNativeFrame(ExactRef original) { return unexpected(); }
    }
}
