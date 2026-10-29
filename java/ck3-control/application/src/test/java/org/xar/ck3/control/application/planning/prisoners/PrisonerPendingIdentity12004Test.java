package org.xar.ck3.control.application.planning.prisoners;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.math.BigInteger;
import java.time.Instant;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;

/** Untrusted legacy producer shapes only. These values grant no action, archive, writer or native qualification. */
final class PrisonerPendingIdentity12004Test {
    @Test void originalPersistedUnconditionalEmptyArrayRemainsDistinctFromInvalidEmptyNativeOptionRequest() {
        ObjectNode pending=release();
        var decoded=PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RELEASE,raw(pending));
        assertInstanceOf(PrisonerOptionIntent.Unconditional.class,decoded.release().orElseThrow().options());
        ObjectNode nativeRequest=StrictJson.object();nativeRequest.putArray("release_option_keys");
        assertThrows(IllegalArgumentException.class,()->PrisonerOptionIntent.decode(nativeRequest));
        assertEquals(88,decoded.target());assertTrue(decoded.actionId().isEmpty());assertTrue(decoded.requestId().isEmpty());
        assertArrayEquals(raw(pending).bytes(),decoded.original().bytes());
    }
    @Test void legacyPendingAckRetainsExactRequestAndCannotChangeOriginalTargetFrameOrQuery() {
        ObjectNode pending=release();ObjectNode ack=pending.putObject("action_ack");
        ack.put("status","submitted_verification_pending").put("material_result",false).put("request_id","actual-old-request")
                .put("player_character_id",77).put("prisoner_character_id",88).put("pre_native_revision",1014).put("pre_date_raw",53286360)
                .put("release_query_sequence",123).put("release_option_mask_bits",0);
        assertEquals("actual-old-request",PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RELEASE,raw(pending)).requestId().orElseThrow());
        for(String key:List.of("player_character_id","prisoner_character_id","pre_native_revision","pre_date_raw","release_query_sequence","release_option_mask_bits")) {
            ObjectNode changed=pending.deepCopy();((ObjectNode)changed.get("action_ack")).put(key,1);
            assertThrows(IllegalArgumentException.class,()->PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RELEASE,raw(changed)),key);
        }
        ack.put("material_result",true);
        assertThrows(IllegalArgumentException.class,()->PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RELEASE,raw(pending)));
    }
    @Test void exactIntegralIdentitiesAndExplicitOptionCostsAreRequiredBeforeAnyJoin() {
        for(String key:List.of("player_character_id","prisoner_character_id","pre_native_revision","pre_date_raw","release_query_sequence","release_option_mask_bits")) {
            ObjectNode booleanValue=release();booleanValue.put(key,true);
            assertThrows(IllegalArgumentException.class,()->PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RELEASE,raw(booleanValue)),key);
            ObjectNode floating=release();floating.put(key,1.0);
            assertThrows(IllegalArgumentException.class,()->PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RELEASE,raw(floating)),key);
        }
        for(String key:List.of("release_option_keys","costs","acceptance")) {
            ObjectNode missing=release();missing.remove(key);
            assertThrows(IllegalArgumentException.class,()->PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RELEASE,raw(missing)),key);
            ObjectNode nil=release();nil.putNull(key);
            assertThrows(IllegalArgumentException.class,()->PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RELEASE,raw(nil)),key);
        }
    }
    @Test void redirectedRansomPayerAndAcceptanceTimeQuoteRemainIndependentOfPrisonerIdentity() {
        ObjectNode pending=base().put("payer_character_id",99).put("selected_option","current_gold")
                .put("amount_is_acceptance_time_quote",true).put("quoted_gold_raw",500000).put("pre_player_gold_raw",-20000);
        var decoded=PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RANSOM,raw(pending));
        assertEquals(99,decoded.ransom().orElseThrow().payer());assertEquals(88,decoded.target());
        assertTrue(decoded.ransom().orElseThrow().acceptanceTime());
        pending.put("amount_is_acceptance_time_quote",false);
        assertThrows(IllegalArgumentException.class,()->PrisonerPendingIdentity12004.decode(PrisonerPlanningPorts.Family.RANSOM,raw(pending)));
    }
    @Test void missingPendingCannotBeReadAsClearAndPresentUnresolvedBodySurvivesCanonicalRoundTrip() {
        assertThrows(IllegalArgumentException.class,()->PrisonerLedgerReducer12004.validate(PrisonerPlanningPorts.Family.RELEASE,StrictJson.object()));
        ObjectNode body=StrictJson.object();body.set("pending",release());body.putNull("resolved");
        PrisonerLedgerReducer12004.validate(PrisonerPlanningPorts.Family.RELEASE,StrictJson.parse(raw(body).bytes()));
        assertArrayEquals(raw(body).bytes(),StrictJson.canonical(StrictJson.parse(raw(body).bytes())));
        body.put("unexpected_alias",true);
        assertThrows(IllegalArgumentException.class,()->PrisonerLedgerReducer12004.validate(PrisonerPlanningPorts.Family.RELEASE,body));
    }
    private static ObjectNode release() {
        ObjectNode pending=base().put("release_query_sequence",123).put("release_option_mask_bits",0);
        pending.putArray("release_option_keys");pending.putObject("costs");pending.putObject("acceptance");return pending;
    }
    private static ObjectNode base() {
        return StrictJson.object().put("stage","submission_unresolved").put("material_result",false)
                .put("player_character_id",77).put("prisoner_character_id",88).put("pre_native_revision",1014).put("pre_date_raw",53286360);
    }
    private static RawJson raw(ObjectNode row) { return new RawJson(StrictJson.canonical(row)); }
    // Pure command/pending contract originals only. No archive, writer, Native custody or Game is qualified here.
    @Test void modernZeroActorPendingCanJoinItsUnknownCommand() { assertModernPendingJoin(0); }
    @Test void modernNegativeActorPendingCanJoinItsUnknownCommand() { assertModernPendingJoin(-2); }
    @Test void modernMinimumActorPendingCanJoinItsUnknownCommand() { assertModernPendingJoin(Integer.MIN_VALUE); }
    @Test void modernMaximumActorPendingCanJoinItsUnknownCommand() { assertModernPendingJoin(Integer.MAX_VALUE); }
    private static void assertModernPendingJoin(long actor) {
        for (var family : PrisonerPlanningPorts.Family.values()) {
            ObjectNode pending = family == PrisonerPlanningPorts.Family.RELEASE ? release()
                    : base().put("payer_character_id",99).put("selected_option","current_gold")
                        .put("amount_is_acceptance_time_quote",true).put("quoted_gold_raw",500000).put("pre_player_gold_raw",-20000);
            pending.put("player_character_id",actor);
            var receipt = modernUnknown(family,actor,pending);
            pending.put("action_id",receipt.command().actionId());
            RawJson originalPending = raw(pending);
            var identity = PrisonerPendingIdentity12004.decode(family,originalPending);
            assertEquals(actor,identity.actor());
            assertTrue(identity.matches(receipt));
            assertArrayEquals(originalPending.bytes(),identity.original().bytes());
            assertEquals(ActionReceipt.Outcome.UNRESOLVED,receipt.outcome());
            assertFalse(receipt.settled());assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
            assertTrue(receipt.ack().isEmpty());
            ObjectNode body = StrictJson.object();body.set("pending",pending);body.putNull("resolved");
            if(family==PrisonerPlanningPorts.Family.RANSOM)body.put("schema","xar.ck3.prisoner-ransom-formal.v1");
            assertThrows(IllegalArgumentException.class,()->PrisonerLedgerReducer12004.resolve(family,raw(body),receipt,raw(StrictJson.object())));
        }
    }
    private static ActionReceipt modernUnknown(PrisonerPlanningPorts.Family family,long actor,ObjectNode pending) {
        var now=Instant.parse("2026-10-29T00:00:00Z");
        var ref=new ExactRef("D:/synthetic-contract-fixture/prisoner-original.json",1,"a".repeat(64));
        var source=new G2Source("software-prisoner-identity",now.toString(),"1.20.0.4",ref);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),
                BigInteger.valueOf(1014),BigInteger.valueOf(53286360)),"native:1014",BigInteger.valueOf(73),"identity-episode");
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1);
        var operation=family==PrisonerPlanningPorts.Family.RELEASE?PrisonerOrdinaryPolicy12004.RELEASE:PrisonerOrdinaryPolicy12004.RANSOM;
        var args=StrictJson.object().put("prisoner_character_id",88);
        for(String key:family==PrisonerPlanningPorts.Family.RELEASE?List.of("release_query_sequence","release_option_mask_bits")
                :List.of("payer_character_id","selected_option","amount_is_acceptance_time_quote","quoted_gold_raw","pre_player_gold_raw"))args.set(key,pending.get(key));
        var command=new ActionCommand("pending-identity-"+family+"-"+actor,before,source,"identity-session",operation,
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)),"command contract DATA"),
                PrisonerActionBinding12004.expected(before,source,operation,88),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),now.plusSeconds(30));
        byte[] commandWire=ActionCodec.encodeCommand(command);var decoded=ActionCodec.decodeCommand(commandWire);
        assertArrayEquals(commandWire,ActionCodec.encodeCommand(decoded));assertEquals(command,decoded);
        var guard=new GuardEvidence(decoded.before(),source,decoded.sessionId(),BigInteger.ONE,operation,ref,ref,"contract-DATA",now,now.plusSeconds(20));
        var attempt=new ActionState.Attempt("original-prisoner-request-"+actor,now,guard,new NativeRequest(operation.value(),Optional.empty(),raw(args)));
        return new ActionReceipt(1,4,decoded,ActionCodec.bodySha256(decoded),new ActionState.Unknown(Optional.of(attempt),Optional.empty(),"unresolved software original",List.of()));
    }

}

