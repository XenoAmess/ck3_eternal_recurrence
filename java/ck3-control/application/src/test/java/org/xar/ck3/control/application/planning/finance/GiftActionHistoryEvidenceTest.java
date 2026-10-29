package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.List;
import java.util.Optional;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicCodec;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.Method;
import org.xar.ck3.control.wave2.finance.giftpending.*;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.*;

/** Actual pending reducer -> original native.ack schema -> same decoder used by GiftDomainSource -> recorder projections.
 * Source fixture follows original formal_route test_submit_persists_identity_before_accepting_pending_ack.
 * This is pure DATA; no private Root, archived canonical action, current read or Captured authority is fabricated. */
final class GiftActionHistoryEvidenceTest {
    private static final String REQUEST="faction-gift-original-source";
    private static final BigInteger WIDE=new BigInteger("18446744073709551615");
    private static BigInteger n(long value){return BigInteger.valueOf(value);}
    private static Ledger originalPending() {
        var baseline=new Baseline(n(771),n(33011),n(3),n(3),n(53288472),n(32904),n(100000000),n(-25),n(11000000),n(5000000),
                List.of(n(33011),n(33435)),n(15000000),n(37));
        return GiftPendingReducer.begin(Ledger.empty(),new BeginRequest(REQUEST,"native-32904-a","R3",new ProcessIdentity(n(222),"2026-10-19T05:10:54.525692Z"),
                baseline,n(10000000),"a".repeat(64)));
    }
    private static Obj submit() {
        Obj ack=obj("schema_version",new IntegerValue(n(1)),"request_id",new Text(REQUEST),"status",new Text("submitted_verification_pending"),
                "verification_pending",new Bool(true),"source_faction_id",new IntegerValue(n(771)),"recipient_character_id",new IntegerValue(n(33011)));
        return obj("step",new Text(OrdinaryFinancePolicies.GIFT.value()),"private_build",new Bool(true),"advertised",new Bool(false),
                "status",new Text("submitted_verification_pending"),"query_sequence",new IntegerValue(WIDE),"native",obj("ack",ack));
    }
    private static Obj receipt() {
        Obj receipt=obj("schema_version",new IntegerValue(n(1)),"request_id",new Text(REQUEST),"status",new Text("mitigated"),
                "postcondition_verified",new Bool(true),"mitigation_applied",new Bool(true),"post_gift_opinion_present",new Bool(true),
                "source_faction_id",new IntegerValue(n(771)),"recipient_character_id",new IntegerValue(n(33011)),"player_character_id",new IntegerValue(n(32904)),
                "post_snapshot_revision",new IntegerValue(n(4)),"post_native_snapshot_revision",new IntegerValue(n(4)),
                "post_observed_date_raw",new IntegerValue(n(53288472)),"post_player_gold_raw",new IntegerValue(n(85000000)),
                "post_gift_opinion_modifier_value",new IntegerValue(n(37)));
        return obj("step",new Text(GiftActionHistoryEvidence.RECEIPT.value()),"accepted",new Bool(true),"private_build",new Bool(true),
                "advertised",new Bool(false),"status",new Text("applied"),"query_sequence",new IntegerValue(WIDE),"receipt",receipt);
    }
    private static NativeActionPort.AckReceived ack(Obj result) {
        RawJson token=new RawJson(DriverJson.encode(result));
        RawJson frame=new RawJson(DriverJson.encode(obj("type",new Text("command_result"),"protocol_version",new IntegerValue(n(1)),
                "request_id",new Text(REQUEST),"ok",new Bool(true),"result",result)));
        byte[] packet=ByteBuffer.allocate(frame.bytes().length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(frame.bytes().length).put(frame.bytes()).array();
        return new NativeActionPort.AckReceived(REQUEST,true,Optional.of(token),frame,packet);
    }
    @Test void nativeNestedAckProducesBothOriginalRecorderShapesAndRetiresOnlyAfterIndependentReceipt() {
        Ledger pending=originalPending();var submission=GiftActionHistoryEvidence.decodeSubmission(ack(submit()));
        var projected=GiftActionHistoryEvidence.project(pending,submission,receipt());
        Obj sent=DriverJson.object(projected.submitResult().bytes(),RawJson.MAXIMUM_BYTES);
        Obj received=DriverJson.object(projected.receiptResult().bytes(),RawJson.MAXIMUM_BYTES);
        Ledger acknowledged=GiftPendingCodec.decodeLedger(DriverJson.encode(object(sent.get("pending_ledger"),"actual original submit ledger")));
        assertEquals(PendingStatus.SUBMITTED_VERIFICATION_PENDING,acknowledged.pending().orElseThrow().status());
        assertEquals(submission.ack().evidence(),acknowledged.pending().orElseThrow().ack().orElseThrow());
        assertFalse(sent.members().containsKey("accepted")); // Original submit recorder uses explicit ok=True, not accepted.
        Ledger completed=GiftPendingCodec.decodeLedger(DriverJson.encode(object(received.get("pending_ledger"),"completed original ledger")));
        assertTrue(completed.pending().isEmpty());assertEquals(ResolvedOutcome.APPLIED,completed.resolvedRequestOutcomes().get(REQUEST));
        assertTrue(pending.pending().isPresent());assertTrue(pending.resolvedRequestOutcomes().isEmpty());
        assertEquals(sent,DriverJson.object(DriverJson.encode(sent),RawJson.MAXIMUM_BYTES));
        assertEquals(received,DriverJson.object(DriverJson.encode(received),RawJson.MAXIMUM_BYTES));
    }
    @Test void oldWrongTopLevelAckAliasAndChangedOriginalTokenAreRejected() {
        Obj original=submit();Obj nativeAck=object(object(original.get("native"),"native").get("ack"),"ack");
        var fields=new java.util.LinkedHashMap<String,Value>(original.members());fields.remove("native");fields.put("ack",nativeAck);
        assertThrows(IllegalArgumentException.class,()->GiftActionHistoryEvidence.decodeSubmission(ack(new Obj(fields))));
        var valid=ack(original);var changed=new NativeActionPort.AckReceived(REQUEST,true,Optional.of(new RawJson(DriverJson.encode(original.with("status",new Text("different"))))),
                valid.originalFrame(),valid.originalPacket());
        assertThrows(IllegalArgumentException.class,()->GiftActionHistoryEvidence.decodeSubmission(changed));
        assertThrows(IllegalArgumentException.class,()->GiftActionHistoryEvidence.decodeSubmission(ack(original.with("native",obj("ack",nativeAck.with("request_id",new Text("other")))))));
    }
    @Test void missingOrWrongWalletReceiptCannotCreateSuccessfulPairedProjection() {
        var original=GiftActionHistoryEvidence.decodeSubmission(ack(submit()));Obj result=receipt();
        assertThrows(IllegalArgumentException.class,()->GiftActionHistoryEvidence.project(Ledger.empty(),original,result));
        assertThrows(IllegalArgumentException.class,()->GiftActionHistoryEvidence.project(originalPending(),original,result.with("accepted",new Bool(false))));
        Obj material=object(result.get("receipt"),"receipt");
        assertThrows(IllegalArgumentException.class,()->GiftActionHistoryEvidence.project(originalPending(),original,
                result.with("receipt",material.with("post_player_gold_raw",new IntegerValue(n(100000000))))));
        assertThrows(IllegalArgumentException.class,()->GiftActionHistoryEvidence.project(originalPending(),original,
                result.with("receipt",material.with("post_native_snapshot_revision",new Bool(true)))));
    }
    @Test void actualPairedProjectionsUseSolePublicWidthCodecAndPreserveNativeOriginalIntegers() {
        var projected=GiftActionHistoryEvidence.project(originalPending(),GiftActionHistoryEvidence.decodeSubmission(ack(submit())),receipt());
        for(var method:List.of(Method.SEND,Method.RECEIPT)) {
            RawJson actual=method==Method.SEND?projected.submitResult():projected.receiptResult();
            RawJson external=FactionGiftPublicCodec.businessPublic(method,actual);
            Obj body=DriverJson.object(external.bytes(),RawJson.MAXIMUM_BYTES);
            assertEquals(new Text(WIDE.toString()),body.get("query_sequence"));
            assertEquals(new IntegerValue(WIDE),DriverJson.object(actual.bytes(),RawJson.MAXIMUM_BYTES).get("query_sequence"));
            assertEquals(DriverJson.object(actual.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(FactionGiftPublicCodec.businessNative(method,external).bytes(),RawJson.MAXIMUM_BYTES));
        }
    }
    @Test void archivedReceiptParserRequiresTheExactOwningFixedContractAndOriginalPacket() {
        var read=receiptData("ordinary-finance-read:FACTION_GIFT_RECEIPT",new Obj(java.util.Map.of()));
        assertEquals(receipt(),FinanceReadContracts.decodeArchivedGiftReceipt(read).result());
        assertThrows(IllegalArgumentException.class,()->FinanceReadContracts.decodeArchivedGiftReceipt(
                receiptData("another-contract",new Obj(java.util.Map.of()))));
        assertThrows(IllegalArgumentException.class,()->FinanceReadContracts.decodeArchivedGiftReceipt(
                receiptData("ordinary-finance-read:FACTION_GIFT_RECEIPT",obj("selector",new Bool(true)))));
        var changed=new PlanningReadReceipt(read.request(),read.contractId(),read.requestId(),read.before(),read.after(),
                new NativeActionPort.AckReceived(REQUEST,true,Optional.of(new RawJson(DriverJson.encode(submit()))),read.original().originalFrame(),read.original().originalPacket()));
        assertThrows(IllegalArgumentException.class,()->FinanceReadContracts.decodeArchivedGiftReceipt(changed));
    }
    private static PlanningReadReceipt receiptData(String contract,Obj arguments) {
        var source=new ExactRef("software-packet-data",1,"a".repeat(64));
        var frame=new ObservationIdentity("software-machine",new GameGeneration(42,new PythonOnlyUInt64(n(1))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(n(32904),n(4),n(53288472)),"native:4",n(4),"native-32904-a"),1);
        var origin=new G2Source("software-machine","2026-10-24T00:00:00Z","1.20.0.4",source);
        Instant deadline=Instant.now().plusSeconds(60);
        var request=new PlanningReadRequest(frame,origin,"software-session",GiftActionHistoryEvidence.RECEIPT,arguments,deadline);
        var binding=new GuardEvidence(frame,origin,"software-session",n(1),request.operation(),source,source,"software-packet-data",deadline.minusSeconds(20),deadline);
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        return new PlanningReadReceipt(request,contract,REQUEST,guard,guard,ack(receipt()));
    }
}
