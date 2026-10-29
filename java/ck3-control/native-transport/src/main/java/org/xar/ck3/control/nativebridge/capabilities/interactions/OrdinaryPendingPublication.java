package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Versioned native queue DATA with its actual individual frames. It grants no Applied effect, retry or once-claim. */
public final class OrdinaryPendingPublication {
    public static final String SCHEMA="xar.java.ordinary-public-pending-basis/v2";
    public static final String LEGACY_SCHEMA="xar.java.ordinary-public-pending-basis/v1";
    public static final String EXPECTATION_SCHEMA="xar.java.ordinary-public-pending-only/v1";
    private OrdinaryPendingPublication() { }
    /** The generic native observer never settles this request; a queue receipt is separate from any business result. */
    public static ExpectedPostcondition requestExpectation(Context current) {
        Objects.requireNonNull(current);
        return new ExpectedPostcondition(1,current.before(),current.source(),EXPECTATION_SCHEMA,
                List.of(new ExpectedBoolean(new FieldKey("business_effects_verified"),false)));
    }
    public record Publication(RawJson value,OrdinaryInitiationPreparation.ActualFrame before,OrdinaryInitiationPreparation.ActualFrame after) {
        public Publication { Objects.requireNonNull(value);Objects.requireNonNull(before);Objects.requireNonNull(after); }
    }
    static ExactRef preserve(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,
            OrdinaryInitiationPreparation.ActualFrame before,OrdinaryInitiationPreparation.ActualFrame after,
            ExactRef actualClaim,RawJson projected,ActionPorts.OutcomeArchive archive) {
        OrdinaryInitiationPreparation.requireAfterControl(before,after);
        require(command.before().equals(before.actual().identity())&&before.actual().originalEvidence().equals(attempt.guard().nativeEvidence())
                &&attempt.requestId().equals(ack.requestId()),"ordinary publication lost the actual original attempt");
        require(projected.equals(OrdinaryInitiationPreparation.projectPending(ack.originalResultToken().orElseThrow(),before.interaction(),after.actual(),attempt.requestId(),actualClaim)),"ordinary publication differs from sole original public producer");
        var initial=NativeEffectEvidence.basis(before.actual());var ending=NativeEffectEvidence.basis(after.actual());
        verifyFrame(initial,archive);verifyFrame(ending,archive);exact(actualClaim,archive.loadMaterial(actualClaim).bytes());
        ExactRef material=archive.preserveMaterial(projected);ExactRef dispatch=archive.referenceOf(ack),request=archive.requestReferenceOf(attempt.preparedRequest());
        require(archive.load(dispatch).equals(ack)&&archive.loadRequest(request).equals(attempt.preparedRequest()),"ordinary publication changed its original dispatch/request archive");
        ObjectNode body=StrictJson.object().put("schema",SCHEMA).put("command_body_sha256",ActionCodec.bodySha256(command)).put("request_id",attempt.requestId());
        body.put("after_projection_deadline",after.interaction().deadline().toString());
        body.set("before",frame(initial));body.set("after",frame(ending));body.set("native_publication",material.toJson());body.set("original_claim",actualClaim.toJson());
        body.set("original_dispatch",dispatch.toJson());body.set("prepared_request",request.toJson());
        return archive.preserveMaterial(new RawJson(DriverJson.encodeNode(body)));
    }
    /** Exact four-reference current profile. Historical/no-ACK receipts have no invented publication. */
    public static Optional<Publication> load(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader loader,Build build) {
        Objects.requireNonNull(receipt);Objects.requireNonNull(archive);Objects.requireNonNull(loader);Objects.requireNonNull(build);
        require(receipt.command().operation().value().equals(OrdinaryInteractionCodec.INITIATE_STEP),"ordinary publication requires its original operation");
        require(receipt.applied().isEmpty(),"ordinary queue publication cannot become an Applied result");
        if(!(receipt.state() instanceof ActionState.Unknown unknown)||unknown.evidence().size()!=4
                ||unknown.attempt().isEmpty()||!(unknown.dispatch().orElse(null) instanceof NativeActionPort.AckReceived ack))return Optional.empty();
        ActionState.Attempt attempt=unknown.attempt().orElseThrow();ExactRef basis=unknown.evidence().getFirst();RawJson original=archive.loadMaterial(basis);exact(basis,original.bytes());
        JsonNode encoded=DriverJson.toNode(DriverJson.object(original.bytes(),DriverJson.MAX_NATIVE_BYTES));
        String schema=StrictJson.text(encoded.get("schema"));boolean legacy=LEGACY_SCHEMA.equals(schema);
        require(legacy||SCHEMA.equals(schema),"unknown ordinary publication basis version");
        Set<String> fields=new java.util.HashSet<>(Set.of("schema","command_body_sha256","request_id","before","after","native_publication","original_claim","original_dispatch","prepared_request"));
        if(!legacy)fields.add("after_projection_deadline");ObjectNode body=StrictJson.object(encoded,fields);
        require(receipt.bodySha256().equals(StrictJson.text(body.get("command_body_sha256")))
                &&attempt.requestId().equals(StrictJson.text(body.get("request_id"))),"ordinary publication basis crossed command/request");
        ExactRef material=ExactRef.fromJson(body.get("native_publication")),claim=ExactRef.fromJson(body.get("original_claim")),dispatch=ExactRef.fromJson(body.get("original_dispatch")),request=ExactRef.fromJson(body.get("prepared_request"));
        var first=decodeFrame(body.get("before"));var last=decodeFrame(body.get("after"));verifyFrame(first,archive);verifyFrame(last,archive);
        require(unknown.evidence().equals(List.of(basis,last.nativeFrame(),dispatch,material))&&archive.load(dispatch).equals(ack)
                &&archive.loadRequest(request).equals(attempt.preparedRequest()),"ordinary publication lost its canonical exact evidence vector");
        var projection=new RootInteractionContextProjection(build);var actualBefore=loader.load(first,archive);var actualAfter=loader.load(last,archive);
        var before=new OrdinaryInitiationPreparation.ActualFrame(actualBefore,projection.project(actualBefore,receipt.command().deadline()));
        // This is the producer's archived observation window, not a fresh request/submit permission.
        // A later valid reconciliation may outlive the original command deadline; never invent a replacement deadline.
        java.time.Instant afterDeadline=legacy?receipt.command().deadline():java.time.Instant.parse(StrictJson.text(body.get("after_projection_deadline")));
        require(afterDeadline.isAfter(actualAfter.observedAt()),"ordinary archived observation window expired before its actual after frame");
        var after=new OrdinaryInitiationPreparation.ActualFrame(actualAfter,projection.project(actualAfter,afterDeadline));
        require(actualBefore.identity().equals(receipt.command().before())&&actualBefore.source().equals(receipt.command().source())
                &&actualBefore.sessionId().equals(receipt.command().sessionId())&&actualBefore.originalEvidence().equals(attempt.guard().nativeEvidence())
                &&!actualAfter.observedAt().isBefore(attempt.submittedAt()),"ordinary publication original/full frame changed");
        OrdinaryInitiationPreparation.requireAfterControl(before,after);
        require(!attempt.preparedRequest().preparationEvidence().isEmpty(),"current ordinary publication has no retained preparation");
        ExactRef preparation=attempt.preparedRequest().preparationEvidence().getFirst();RawJson preparationBody=archive.loadMaterial(preparation);exact(preparation,preparationBody.bytes());
        ObjectNode prepared=StrictJson.object(DriverJson.toNode(DriverJson.object(preparationBody.bytes(),DriverJson.MAX_NATIVE_BYTES)),Set.of("schema","command_body_sha256","request_id","prepared_fields_sha256","preflight_read","claim","education_materialization"));
        require(GuardianOutgoingEffects.PREPARATION_SCHEMA.equals(StrictJson.text(prepared.get("schema")))&&receipt.bodySha256().equals(StrictJson.text(prepared.get("command_body_sha256")))
                &&attempt.requestId().equals(StrictJson.text(prepared.get("request_id")))&&claim.equals(ExactRef.fromJson(prepared.get("claim")))
                &&ActionCodec.sha256(attempt.preparedRequest().additionalFields().bytes()).equals(StrictJson.text(prepared.get("prepared_fields_sha256"))),"ordinary publication changed its exact once-claim preparation");
        ExactRef preflight=ExactRef.fromJson(prepared.get("preflight_read"));PlanningReadReceipt read=archive.loadRead(preflight);NativeRecordedEvidenceVerifier.requireRead(read,archive);
        require(archive.readReferenceOf(read).equals(preflight)&&read.request().before().equals(actualBefore.identity())
                &&read.request().source().equals(receipt.command().source())&&read.request().sessionId().equals(receipt.command().sessionId())
                &&read.request().operation().value().equals(OrdinaryInteractionCodec.QUERY_STEP)&&read.contractId().equals("interactions:ordinary-query"),"ordinary public publication lost its original final terms read");
        var intent=GuardianOutgoingEffects.nativeIntent(OrdinaryInitiationIntent.fromJson(receipt.command().arguments()));
        OrdinaryInteractionCodec.query(read.original().originalResultToken().orElseThrow(),before.interaction(),intent);
        OrdinaryInteractionCodec.initiation(ack.originalResultToken().orElseThrow(),before.interaction(),intent);
        RawJson originalClaim=archive.loadMaterial(claim);exact(claim,originalClaim.bytes());
        ObjectNode claimBody=StrictJson.object(DriverJson.toNode(DriverJson.object(originalClaim.bytes(),DriverJson.MAX_NATIVE_BYTES)),Set.of("identity","binding","request_id","ordinal","status","new_intent_lineage"));
        require("claimed_result_unknown_no_retry".equals(StrictJson.text(claimBody.get("status"))),"ordinary original claim cannot be released by an ACK");
        ObjectNode requestBody=StrictJson.object();for(String key:List.of("identity","binding","request_id"))requestBody.set(key,claimBody.get(key));
        var claimed=OrdinaryOnceClaims.readRequest(requestBody);
        var expectedIdentity=new OrdinaryOnceClaims.Identity(receipt.command().before().machineId(),receipt.command().before().game().pid(),
                receipt.command().before().game().creationFiletime().value().toString(),before.interaction().actor().longValueExact(),intent.interaction().value(),intent.recipient().value());
        var expectedBinding=new OrdinaryOnceClaims.Binding(actualBefore.identity().frame().snapshotId(),actualBefore.identity().frame().revision().toString(),before.interaction().revision().toString(),
                before.interaction().date().toString(),before.interaction().connectionGeneration().toString(),actualBefore.identity().frame().episodeRunId());
        require(claimed.equals(new OrdinaryOnceClaims.Request(expectedIdentity,expectedBinding,attempt.requestId())),"ordinary original claim belongs to another request/pair/frame");
        RawJson value=archive.loadMaterial(material);exact(material,value.bytes());
        require(value.equals(OrdinaryInitiationPreparation.projectPending(ack.originalResultToken().orElseThrow(),before.interaction(),actualAfter,attempt.requestId(),claim)),"ordinary original public queue DATA replay differs");
        return Optional.of(new Publication(value,before,after));
    }
    private static void verifyFrame(NativeEffectEvidence.FrameBasis frame,ActionPorts.OutcomeArchive archive){exact(frame.nativeFrame(),archive.loadNativeFrame(frame.nativeFrame()));exact(frame.driverFacts(),archive.loadMaterial(frame.driverFacts()).bytes());}
    private static ObjectNode frame(NativeEffectEvidence.FrameBasis value){ObjectNode row=StrictJson.object();row.set("native_frame",value.nativeFrame().toJson());row.set("driver_facts",value.driverFacts().toJson());return row;}
    private static NativeEffectEvidence.FrameBasis decodeFrame(JsonNode value){ObjectNode row=StrictJson.object(value,Set.of("native_frame","driver_facts"));return new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(row.get("native_frame")),ExactRef.fromJson(row.get("driver_facts")));}
    private static void exact(ExactRef reference,byte[] raw){require(reference.bytes()==raw.length&&reference.sha256().equals(ActionCodec.sha256(raw)),"ordinary original publication bytes changed");}
    private static void require(boolean condition,String message){StrictJson.require(condition,message);}
}
