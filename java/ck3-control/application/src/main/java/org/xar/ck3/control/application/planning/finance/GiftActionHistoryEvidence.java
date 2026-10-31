package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicCodec;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.Method;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.*;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.*;

/** Two original Gift recordings from one canonical action. No second action, writer, live observation or funding is issued. */
public final class GiftActionHistoryEvidence {
    public static final String SCHEMA="xar.java.gift-action-history-originals/v1";
    public static final OperationKey RECEIPT=FinanceReadContracts.Query.FACTION_GIFT_RECEIPT.operation();
    private static final Set<String> FIELDS=Set.of("schema","action_receipt","canonical_record","pending_writer_point",
            "pending_body","independent_read","submit_result","receipt_result");
    private GiftActionHistoryEvidence() { }
    /** Validated native DATA. Only capture/verifyArchived can issue Captured historical material. */
    public record Submission(Obj result,Ack ack) {
        public Submission {Objects.requireNonNull(result);Objects.requireNonNull(ack);}
    }
    /** Pure original recorder projections. These contain no archive or writer qualification. */
    public record Projections(RawJson submitResult,RawJson receiptResult) {
        public Projections {Objects.requireNonNull(submitResult);Objects.requireNonNull(receiptResult);}
    }
    public static final class Captured {
        private final ExactRef originals;private final Projections results;
        private Captured(ExactRef originals,Projections results){this.originals=originals;this.results=results;}
        public ExactRef originals(){return originals;}
        public RawJson submitResult(){return results.submitResult();}
        public RawJson receiptResult(){return results.receiptResult();}
        public RawJson submitPublic(){return FactionGiftPublicCodec.businessPublic(Method.SEND,submitResult());}
        public RawJson receiptPublic(){return FactionGiftPublicCodec.businessPublic(Method.RECEIPT,receiptResult());}
    }
    private record Derived(ExactRef action,ExactRef record,RootGuardEvidence.WriterPoint point,DomainBodies.BodyRef body,
            PlanningReadReceipt read,Projections results) { }

    /** Sole submit decoder, shared with the actual Gift domain consumer. The original ACK is native.ack, never a top-level alias. */
    public static Submission decodeSubmission(NativeActionPort.AckReceived ack) {
        Objects.requireNonNull(ack);byte[] packet=ack.originalPacket(),frame=ack.originalFrame().bytes();
        StrictJson.require(ack.nativeOk()&&packet.length>=5&&ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4
                &&Arrays.equals(Arrays.copyOfRange(packet,4,packet.length),frame),"Gift original submit packet/frame differs");
        Obj envelope=DriverJson.object(frame,RawJson.MAXIMUM_BYTES);
        StrictJson.require(new Text("command_result").equals(envelope.get("type"))&&new IntegerValue(BigInteger.ONE).equals(envelope.get("protocol_version"))
                &&new Text(ack.requestId()).equals(envelope.get("request_id"))&&new Bool(true).equals(envelope.get("ok"))
                &&ack.originalResultToken().isPresent(),"Gift original submit envelope/request differs");
        Obj result=object(envelope.get("result"),"Gift original submit result");
        StrictJson.require(result.equals(DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES))
                &&new Text(OrdinaryFinancePolicies.GIFT.value()).equals(result.get("step"))&&new Bool(true).equals(result.get("private_build"))
                &&new Bool(false).equals(result.get("advertised"))&&new Text("submitted_verification_pending").equals(result.get("status")),
                "Gift original submit result/token differs");
        Ack typed=GiftPendingCodec.decodeAck(encode(object(object(result.get("native"),"original Gift native result").get("ack"),"original native Gift ACK")));
        StrictJson.require(typed.requestId().equals(ack.requestId()),"Gift native ACK crossed original request");
        return new Submission(result,typed);
    }
    /** Replays exactly the original Python recorder semantics, including complete ACK-marked and completed ledgers. */
    public static Projections project(Ledger originalPending,Submission originalSubmit,Obj independentResult) {
        String request=originalSubmit.ack().requestId();GiftPendingReducer.matching(originalPending,request);
        Ledger acknowledged=GiftPendingReducer.markAck(originalPending,request,originalSubmit.ack());
        StrictJson.require(new Text(RECEIPT.value()).equals(independentResult.get("step"))&&new Bool(true).equals(independentResult.get("accepted"))
                &&new Bool(true).equals(independentResult.get("private_build"))&&new Bool(false).equals(independentResult.get("advertised"))
                &&new Text("applied").equals(independentResult.get("status")),"actual independent Gift route has not proved application");
        AppliedReceipt receipt=GiftPendingCodec.decodeReceipt(encode(object(independentResult.get("receipt"),"actual Gift receipt")));
        Ledger completed=GiftPendingReducer.complete(acknowledged,request,receipt);
        return new Projections(json(originalSubmit.result().with("pending_ledger",ledger(acknowledged))),
                json(independentResult.with("pending_ledger",ledger(completed))));
    }
    public static Captured capture(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive archive,
            NativeEffectEvidence.FrameLoader frames,FinanceReadContracts definitions)throws IOException {
        Derived derived=derive(same,actual,archive);requireDeep(actual,derived,archive,frames,definitions);
        ExactRef submit=preserve(archive,derived.results().submitResult()),receipt=preserve(archive,derived.results().receiptResult());
        RawJson facts=facts(derived,submit,receipt,archive);ExactRef reference=preserve(archive,facts);
        return verifyArchived(same,actual,reference,archive);
    }
    public static Captured verify(Session same,ActionReceipt actual,ExactRef originals,ActionPorts.OutcomeArchive archive,
            NativeEffectEvidence.FrameLoader frames,FinanceReadContracts definitions)throws IOException {
        Captured result=verifyArchived(same,actual,originals,archive);requireDeep(actual,derive(same,actual,archive),archive,frames,definitions);return result;
    }
    /** Cold canonical consumer: actual canonical action and historical registered FACTION membership are mandatory.
     * No fresh scope, cached Captured object or arbitrary RawJson can substitute for these originals. */
    public static Captured verifyArchived(Session same,ActionReceipt actual,ExactRef originals,ActionPorts.OutcomeArchive archive)throws IOException {
        String head=same.head().digest();RawJson raw=archive.loadMaterial(originals);requireExactOriginal(originals,raw.bytes());
        var row=StrictJson.object(StrictJson.parse(raw.bytes(),StrictJson.EXPLICIT_MAX_BYTES),FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact Gift history originals schema required");
        Derived derived=derive(same,actual,archive);ExactRef submit=ExactRef.fromJson(row.get("submit_result")),receipt=ExactRef.fromJson(row.get("receipt_result"));
        requireMaterial(archive,submit,derived.results().submitResult());requireMaterial(archive,receipt,derived.results().receiptResult());
        StrictJson.require(StrictJson.parse(facts(derived,submit,receipt,archive).bytes(),StrictJson.EXPLICIT_MAX_BYTES).equals(row)
                &&same.head().digest().equals(head),"Gift history originals crossed canonical action/body/read or changed writer head");
        return new Captured(originals,derived.results());
    }
    private static Derived derive(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive archive)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(actual);Objects.requireNonNull(archive);
        StrictJson.require(actual.command().operation().equals(OrdinaryFinancePolicies.GIFT)&&actual.state() instanceof ActionState.Settled settled
                &&settled.settlement() instanceof ActionState.Applied,"only actual settled primitive Gift has two successful original recordings");
        var settled=(ActionState.Settled)actual.state();ExactRef action=archive.receiptReferenceOf(actual);
        StrictJson.require(actual.equals(archive.loadReceipt(action)),"Gift canonical receipt archive differs");
        ExactRef record=ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,archive);
        RootGuardEvidence.requireHistory(settled.attempt().guard(),archive,same);
        RootGuardEvidence.WriterPoint point=RootGuardEvidence.writerPoint(settled.attempt().guard(),archive);
        var historical=same.requireHistoricalState(point.sequence(),point.digest());
        DomainBodies.BodyRef body=DomainBodies.reference(historical,DomainBodies.Slot.FACTION).orElseThrow(()->new IOException("original Gift submission guard has no historical FACTION body"));
        var registered=same.readDomain(DomainBodies.Slot.FACTION);
        StrictJson.require(registered instanceof DomainBodies.Available,"actual registered Gift body is unavailable; no closure migration is implied");
        var current=(DomainBodies.Available)registered;
        StrictJson.require(body.contractSchema().equals(GiftPendingModel.SCHEMA)&&body.contractSchema().equals(current.reference().contractSchema())
                &&current.head().equals(same.persistedHead()),"historical Gift body crossed actual current registration schema or head");
        var pin=same.capturePin(body.payload(),ContinuityJson.DOMAIN_MAX_BYTES);
        StrictJson.require(pin.identity().equals(body.identity()),"historical Gift pending payload native identity changed");
        byte[] originalBody=same.readPinned(pin,ContinuityJson.DOMAIN_MAX_BYTES);same.verifyPin(pin);
        requireExactOriginal(body.payload(),originalBody);
        Ledger pending=GiftPendingCodec.decodeLedger(originalBody);String id=RequestIds.forActionBody(actual.bodySha256());
        PendingAction pre=GiftPendingReducer.matching(pending,id);var command=actual.command();
        StrictJson.require(pre.status()==PendingStatus.SUBMISSION_STARTED_UNCONFIRMED&&pre.ack().isEmpty()
                &&pre.episodeRunId().equals(command.before().frame().episodeRunId())&&pre.sourceRoundId().equals("R"+command.before().frame().revision())
                &&pre.baseline().equals(NativeFinanceEffects.giftBaseline(command.arguments()))
                &&pre.minimumGoldReserveRaw().equals(integer(command.arguments().get("minimum_gold_reserve_raw"),"actual Gift reserve"))
                &&pre.checkpointSha256BeforeSubmit().equals(text(command.arguments().get("checkpoint_sha256"),"actual Gift checkpoint"))
                &&GiftProcessIdentity.compare(pre.sourceProcess(),command.before().game())==GiftProcessIdentity.Relation.SAME,
                "historical pending is not this original Gift begin before native submission");
        Submission submit=decodeSubmission(actual.ack().orElseThrow(()->new IllegalArgumentException("canonical Gift submit ACK absent")));
        StrictJson.require(submit.ack().requestId().equals(settled.attempt().requestId())&&id.equals(submit.ack().requestId()),"Gift native ACK differs from canonical original attempt");
        List<PlanningReadReceipt> reads=NativeEffectEvidence.archivedReads(actual,archive);
        StrictJson.require(reads.size()==1,"actual Gift effect has exactly its one original independent receipt");
        PlanningReadReceipt read=reads.getFirst();var after=((ActionState.Applied)settled.settlement()).observation();
        StrictJson.require(read.request().before().equals(after.after())&&read.request().source().equals(command.source())
                &&read.request().sessionId().equals(command.sessionId())&&!read.requestId().equals(id),"Gift receipt read crossed actual settled after frame/source/session");
        for(var guard:List.of(read.before().binding(),read.after().binding()))RootGuardEvidence.requireHistory(guard,archive,same);
        Obj result=FinanceReadContracts.decodeArchivedGiftReceipt(read).result();
        return new Derived(action,record,point,body,read,project(pending,submit,result));
    }
    private static void requireDeep(ActionReceipt actual,Derived derived,ActionPorts.OutcomeArchive archive,
            NativeEffectEvidence.FrameLoader frames,FinanceReadContracts definitions) {
        var material=NativeEffectEvidence.load(actual,archive,Objects.requireNonNull(frames));
        StrictJson.require(material.independentReads().equals(List.of(derived.read())),"Gift archived independent read differs from actual physical material");
        var packet=Objects.requireNonNull(definitions).decodeOriginal(FinanceReadContracts.Query.FACTION_GIFT_RECEIPT,derived.read(),material.frames().after().semantic());
        StrictJson.require(packet.result().equals(FinanceReadContracts.decodeArchivedGiftReceipt(derived.read()).result()),"actual installed Gift receipt parser differs from archived owning decoder");
    }
    private static RawJson facts(Derived value,ExactRef submit,ExactRef receipt,ActionPorts.OutcomeArchive archive) {
        var row=StrictJson.object().put("schema",SCHEMA);row.set("action_receipt",value.action().toJson());row.set("canonical_record",value.record().toJson());
        row.set("pending_writer_point",StrictJson.object().put("sequence",value.point().sequence()).put("digest",value.point().digest()));
        row.set("pending_body",value.body().toJson());row.set("independent_read",archive.readReferenceOf(value.read()).toJson());
        row.set("submit_result",submit.toJson());row.set("receipt_result",receipt.toJson());return new RawJson(StrictJson.canonical(row,StrictJson.EXPLICIT_MAX_BYTES));
    }
    private static ExactRef preserve(ActionPorts.OutcomeArchive archive,RawJson raw) {
        ExactRef result=archive.preserveMaterial(raw);requireMaterial(archive,result,raw);return result;
    }
    private static void requireMaterial(ActionPorts.OutcomeArchive archive,ExactRef reference,RawJson expected) {
        RawJson actual=archive.loadMaterial(reference);requireExactOriginal(reference,actual.bytes());
        StrictJson.require(DriverJson.object(actual.bytes(),RawJson.MAXIMUM_BYTES).equals(DriverJson.object(expected.bytes(),RawJson.MAXIMUM_BYTES)),"Gift original projected result changed");
    }
    /** Exact archive-content check; held Guard authority remains private to its owning package. */
    private static void requireExactOriginal(ExactRef reference, byte[] bytes) {
        StrictJson.require(reference.bytes() == bytes.length && reference.sha256().equals(ActionCodec.sha256(bytes)), "archived original bytes/SHA changed");
    }
    private static Obj ledger(Ledger ledger){return DriverJson.object(GiftPendingCodec.encodeLedger(ledger),GiftPendingCodec.MAX_BYTES);}
    private static RawJson json(Obj value){return new RawJson(DriverJson.encode(value));}
}
