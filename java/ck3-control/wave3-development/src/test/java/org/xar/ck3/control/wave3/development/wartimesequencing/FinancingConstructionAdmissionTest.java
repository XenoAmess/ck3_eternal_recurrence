package org.xar.ck3.control.wave3.development.wartimesequencing;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** Real composer/consumer regression. The explicit NoPending fixture is software input, never native qualification. */
final class FinancingConstructionAdmissionTest {
    @Test void missingFinancingCannotAdmitTheActualQuotedWartimeOutlay() throws Exception { deferred(missing()); }
    @Test void staleFinancingCannotAdmitTheActualQuotedWartimeOutlay() throws Exception { deferred(stale()); }
    @Test void unavailablePendingLedgerCannotAdmitTheActualQuotedWartimeOutlay() throws Exception { deferred(unavailable()); }

    @Test void unavailableFinancingStopsOnlyTheOptionalQuoteBeforeItsProviderRuns() throws Exception {
        for (ObjectNode request : List.of(missing(), stale(), unavailable())) {
            ObjectNode pre = request.deepCopy(); pre.put("stage", "BEFORE_OPTIONAL_QUERY"); pre.putNull("quoted_outlay");
            AtomicInteger quotes = new AtomicInteger();
            Result result = OrdinaryWartimeConstructionConsumer.plan(() -> observed(pre), () -> {
                quotes.incrementAndGet(); return new OrdinaryWartimeConstructionConsumer.ObservedQuote(observed(request));
            });
            assertEquals(0, quotes.get(), "unobserved financing must defer before optional native query");
            assertDeferred(result);
        }
    }

    @Test void finalFreshFinancingReadCannotReachTheExistingAuthorityWhenUnavailable() throws Exception {
        Result planned = compose(OrdinaryWartimeConstructionCodec.decode(bytes(OrdinaryWartimeConstructionTest.complete())));
        assertEquals(Disposition.QUOTED_CANDIDATE, planned.disposition());
        for (ObjectNode current : List.of(missing(), stale(), unavailable())) {
            ReentrantLock lock = new ReentrantLock(); AtomicInteger calls = new AtomicInteger();
            var result = OrdinaryWartimeConstructionConsumer.withCurrentBeforeIntent(planned, lock, () -> {
                assertTrue(lock.isHeldByCurrentThread()); return observed(current);
            }, assessment -> { calls.incrementAndGet(); return "must-not-call"; });
            assertEquals(0, calls.get()); assertFalse(lock.isLocked());
            assertEquals(OrdinaryWartimeConstructionConsumer.FinalStatus.CURRENT_OPTIONAL_SPEND_DEFERRED, result.status());
            assertTrue(result.existingAuthorityResult().isEmpty());
            assertDeferred(result.currentAssessment().orElseThrow());
            byte[] wire = OrdinaryWartimeConstructionCodec.encodeFinalReview(result.review());
            var persisted = OrdinaryWartimeConstructionCodec.decodeFinalReview(wire,
                    java.util.Optional.of(OrdinaryWartimeConstructionCodec.decode(bytes(current))));
            assertEquals(result.status(), persisted.status()); assertFalse(persisted.nativeActionAppliedVerified());
        }
    }

    @Test void explicitlyObservedSameFrameNoPendingRetainsTheSoleReserveAndRoundtrip() throws Exception {
        ObjectNode current = OrdinaryWartimeConstructionTest.complete(); byte[] raw = bytes(current);
        Result result = OrdinaryWartimeConstructionCodec.verifyResponse(raw, OrdinaryWartimeConstructionCodec.evaluate(raw));
        assertEquals(Disposition.QUOTED_CANDIDATE, result.disposition());
        assertEquals(EmergencyFinancingAssessment.ReplayGuard.NO_UNRESOLVED_ACTION_OBSERVED,
                result.financing().assessment().orElseThrow().replay());
        assertEquals(BigInteger.valueOf(77_000_000), result.cash().reserve().orElseThrow().required());
        assertEquals(BigInteger.valueOf(7_000_000), result.cash().reserve().orElseThrow().commitments());
        assertEquals(BigInteger.ZERO, result.unreceivedFundingCreditedRaw()); assertFalse(result.canSubmitAction());
        assertArrayEquals(OrdinaryWartimeConstructionCodec.encode(result),
                OrdinaryWartimeConstructionCodec.encode(compose(OrdinaryWartimeConstructionCodec.decode(raw))));
        ObjectNode wrongType = current.deepCopy(); wrongType.withObject("/financing_request/pending_observation").put("status", true);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.decode(bytes(wrongType)));
    }

    @Test void unavailableFinancingPreservesSelectedWarWorkAndTheObservedPeaceBranch() throws Exception {
        ObjectNode war = missing(); war.put("original_selected_step", "native-war-army-route-v1"); war.put("opportunity", "CONTINUE_SELECTED_WORK");
        Result selected = compose(OrdinaryWartimeConstructionCodec.decode(bytes(war)));
        assertEquals(Disposition.CONTINUE_SELECTED_WORK, selected.disposition());
        assertEquals("native-war-army-route-v1", selected.selectedStep().orElseThrow()); assertTrue(selected.continueOrdinaryPlanner());
        ObjectNode peace = missing(); peace.put("stage", "BEFORE_OPTIONAL_QUERY"); peace.putNull("quoted_outlay");
        peace.withObject("/cash_input/snapshot").putArray("active_wars");
        Result peaceful = compose(OrdinaryWartimeConstructionCodec.decode(bytes(peace)));
        assertEquals(Disposition.OPTIONAL_QUERY_ALLOWED, peaceful.disposition()); assertTrue(peaceful.continueOrdinaryPlanner());
        assertFalse(peaceful.canSubmitAction());
    }

    private static void deferred(ObjectNode request) {
        byte[] raw = bytes(request);
        Result result = OrdinaryWartimeConstructionCodec.verifyResponse(raw, OrdinaryWartimeConstructionCodec.evaluate(raw));
        assertDeferred(result);
        assertEquals("FINANCING_OBSERVATION_UNAVAILABLE", result.reason().orElseThrow().name());
        ObjectNode forged = (ObjectNode) StrictJson.parse(OrdinaryWartimeConstructionCodec.encode(result), OrdinaryWartimeConstructionCodec.MAX_BYTES);
        forged.put("disposition", "QUOTED_CANDIDATE"); forged.put("can_submit_action", true);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.verifyResponse(raw, bytes(forged)));
    }
    private static void assertDeferred(Result result) {
        assertEquals(Disposition.DEFER_OPTIONAL_CONSTRUCTION, result.disposition());
        assertEquals("life-advance", result.selectedStep().orElseThrow()); assertTrue(result.continueOrdinaryPlanner());
        assertTrue(result.candidate().isEmpty()); assertFalse(result.canSubmitAction());
        assertEquals(BigInteger.ZERO, result.unreceivedFundingCreditedRaw());
    }
    private static ObjectNode missing() throws Exception { ObjectNode request = OrdinaryWartimeConstructionTest.complete(); request.putNull("financing_request"); return request; }
    private static ObjectNode stale() throws Exception {
        ObjectNode request = OrdinaryWartimeConstructionTest.complete();
        request.withObject("/financing_request/gap_request/snapshot").put("revision", 4); return request;
    }
    private static ObjectNode unavailable() throws Exception {
        ObjectNode request = OrdinaryWartimeConstructionTest.complete();
        request.withObject("/financing_request").putNull("pending_observation"); return request;
    }
    private static ObservedRequest observed(ObjectNode request) { return new ObservedRequest(bytes(request)); }
    private static byte[] bytes(JsonNode value) { return SdkProjectionJson.encode(value, OrdinaryWartimeConstructionCodec.MAX_BYTES); }

    /** Only controlled test fixtures call this: a null/absent production reader is never converted to NoPending. */
    static void attachCurrentFinancing(ObjectNode request) {
        ObjectNode financing = request.putObject("financing_request");
        financing.put("schema", "xar.emergency-financing-assessment.request.v1");
        ObjectNode gap = financing.putObject("gap_request"); gap.put("schema", "xar.war-financing-capability-gap.request.v1");
        gap.set("snapshot", request.path("cash_input").path("snapshot").deepCopy());
        gap.putNull("priority"); gap.putNull("root"); gap.putNull("construction_ledger"); gap.putNull("bridge_capabilities");
        financing.putNull("loan_request"); financing.putObject("pending_observation").put("status", "no_pending_action");
    }
}
