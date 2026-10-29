package org.xar.ck3.control.application.lifecycle;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.LifecycleIdentityCodec;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.*;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** One closed durable wire contract, bounded by the original small UI ledger budget. It mints no qualification. */
public final class SuccessorUiObligationCodec {
    private static final String CONTINUITY_SCHEMA="xar.java.successor-ui-obligation/v2";
    private static final String UNOBSERVED_SCHEMA="xar.java.successor-ui-obligation/v3";
    private SuccessorUiObligationCodec(){ }
    public static byte[] encode(SuccessorUiObligation value){return StrictJson.canonical(toJson(value),SuccessorUiObligation.MAXIMUM_BYTES);}
    public static SuccessorUiObligation decode(byte[] original){return fromJson(StrictJson.parse(original,SuccessorUiObligation.MAXIMUM_BYTES));}
    public static ObjectNode toJson(SuccessorUiObligation value) {
        boolean continuity=value.finalization().flatMap(Finalization::continuityBinding).isPresent();
        boolean unobserved=value.rebind().flatMap(Rebind::retainedPending).isPresent();
        var row=StrictJson.object().put("schema",unobserved?UNOBSERVED_SCHEMA:continuity?CONTINUITY_SCHEMA:SuccessorUiObligation.SCHEMA).put("phase",value.phase().name()).put("machine_id",value.binding().predecessor().machineId()).put("observed_at_utc",recordedAt(value).toString());row.set("binding",binding(value.binding()));
        put(row,"observation",value.observation(),SuccessorUiObligationCodec::observation);put(row,"close_attempt",value.closeAttempt(),SuccessorUiObligationCodec::close);
        put(row,"rebind",value.rebind(),SuccessorUiObligationCodec::rebind);put(row,"finalization",value.finalization(),SuccessorUiObligationCodec::finalization);return row;
    }
    public static SuccessorUiObligation fromJson(JsonNode value) {
        var row=row(value,"schema","phase","machine_id","observed_at_utc","binding","observation","close_attempt","rebind","finalization");
        boolean unobserved=text(row,"schema").equals(UNOBSERVED_SCHEMA);
        boolean continuity=text(row,"schema").equals(CONTINUITY_SCHEMA)||(unobserved&&row.get("finalization").isObject()&&row.get("finalization").has("continuity_binding"));
        require(unobserved||continuity||text(row,"schema").equals(SuccessorUiObligation.SCHEMA),"unsupported exact UI obligation schema");
        var result=new SuccessorUiObligation(binding(row.get("binding")),Phase.valueOf(text(row,"phase")),optional(row,"observation",SuccessorUiObligationCodec::observation),
                optional(row,"close_attempt",SuccessorUiObligationCodec::close),optional(row,"rebind",SuccessorUiObligationCodec::rebind),optional(row,"finalization",v->finalization(v,continuity)));
        require(continuity==result.finalization().flatMap(Finalization::continuityBinding).isPresent(),"UI continuity schema requires its actual original binding");
        require(unobserved==result.rebind().flatMap(Rebind::retainedPending).isPresent(),"UI unobserved schema must retain its actual original binding variant");
        require(text(row,"machine_id").equals(result.binding().predecessor().machineId())&&time(row,"observed_at_utc").equals(recordedAt(result)),"UI record machine/time differs from actual retained frame");return result;
    }
    private static Instant recordedAt(SuccessorUiObligation v) {
        Instant at=v.binding().qualifiedAtUtc();
        if(v.observation().isPresent()&&v.observation().orElseThrow().frame().observedAtUtc().isAfter(at))at=v.observation().orElseThrow().frame().observedAtUtc();
        if(v.closeAttempt().isPresent()&&v.closeAttempt().orElseThrow().enteredAtUtc().isAfter(at))at=v.closeAttempt().orElseThrow().enteredAtUtc();
        if(v.rebind().isPresent()&&v.rebind().orElseThrow().resumed().observedAtUtc().isAfter(at))at=v.rebind().orElseThrow().resumed().observedAtUtc();
        if(v.finalization().isPresent()&&v.finalization().orElseThrow().finalizedAtUtc().isAfter(at))at=v.finalization().orElseThrow().finalizedAtUtc();return at;
    }
    private static ObjectNode binding(Binding value) {
        var row=StrictJson.object().put("successor_character_id",value.successorCharacterId()).put("successor_episode_run_id",value.successorEpisodeRunId())
                .put("cause_digest",value.causeDigest()).put("parent_action_id",value.parentActionId())
                .put("parent_body_sha256",value.parentBodySha256()).put("qualified_at_utc",value.qualifiedAtUtc().toString());
        putOptionalText(row,"source_epoch_sha256",value.sourceEpochSha256());
        row.set("predecessor",LifecycleIdentityCodec.encode(value.predecessor()));row.set("original_parent_command",value.originalParentCommand().toJson());
        row.set("preclock_document",value.preclockDocument().toJson());row.set("qualified_cause",value.qualifiedCause().toJson());return row;
    }
    private static Binding binding(JsonNode value) {
        var row=StrictJson.object(value,Set.of("successor_character_id","successor_episode_run_id","cause_digest","parent_action_id","parent_body_sha256","qualified_at_utc","predecessor","original_parent_command","preclock_document","qualified_cause"),Set.of("source_epoch_sha256"));
        return new Binding(LifecycleIdentityCodec.decode(row.get("predecessor")),character(row,"successor_character_id"),text(row,"successor_episode_run_id"),optionalText(row,"source_epoch_sha256"),
                text(row,"cause_digest"),text(row,"parent_action_id"),text(row,"parent_body_sha256"),ref(row,"original_parent_command"),ref(row,"preclock_document"),ref(row,"qualified_cause"),time(row,"qualified_at_utc"));
    }
    private static ObjectNode frame(UiFrame value) {
        var row=StrictJson.object().put("machine_id",value.machineId()).put("session_id",value.sessionId()).put("connection_generation",decimal(value.connectionGeneration()))
                .put("snapshot_id",value.snapshotId()).put("revision",decimal(value.revision())).put("native_revision",decimal(value.nativeRevision()))
                .put("date_raw",value.dateRaw().toString()).put("actor_character_id",value.actorCharacterId()).put("episode_run_id",value.episodeRunId()).put("episode_epoch",value.episodeEpoch())
                .put("driver_version",value.driverVersion()).put("observed_at_utc",value.observedAtUtc().toString());row.set("game",value.game().toJson());
        row.set("native_packet",value.nativePacket().toJson());row.set("semantic",value.semantic().toJson());row.set("original_driver",value.originalDriver().toJson());
        putOptionalText(row,"source_epoch_sha256",value.sourceEpochSha256());
        row.set("source_qualification",ExactRef.optionalToJson(value.sourceQualification()));return row;
    }
    private static UiFrame frame(JsonNode value) {
        var row=StrictJson.object(value,Set.of("machine_id","session_id","connection_generation","snapshot_id","revision","native_revision","date_raw","actor_character_id","episode_run_id","episode_epoch","driver_version","observed_at_utc","game","native_packet","semantic","original_driver"),Set.of("source_epoch_sha256","source_qualification"));
        return new UiFrame(text(row,"machine_id"),GameGeneration.fromJson(row.get("game")),text(row,"session_id"),uint64(row,"connection_generation"),optionalText(row,"source_epoch_sha256"),text(row,"snapshot_id"),
                uint64(row,"revision"),uint64(row,"native_revision"),signed(row,"date_raw"),character(row,"actor_character_id"),text(row,"episode_run_id"),safe(row,"episode_epoch"),safe(row,"driver_version"),
                ref(row,"native_packet"),ref(row,"semantic"),ref(row,"original_driver"),ExactRef.optionalFromJson(row.get("source_qualification")),time(row,"observed_at_utc"));
    }
    private static ObjectNode observation(Observation v){var r=StrictJson.object().put("state",v.state().name()).put("query_sequence",v.querySequence().toString()).put("observation_revision",v.observationRevision().toString());r.set("frame",frame(v.frame()));r.set("timeline_read",v.timelineRead().toJson());r.set("timeline_native_frame",v.timelineNativeFrame().toJson());put(r,"event_instance_id",v.eventInstanceId(),n->com.fasterxml.jackson.databind.node.TextNode.valueOf(n.toString()));put(r,"event_read",v.eventRead(),ExactRef::toJson);return r;}
    private static Observation observation(JsonNode v){var r=row(v,"state","query_sequence","observation_revision","frame","timeline_read","timeline_native_frame","event_instance_id","event_read");return new Observation(frame(r.get("frame")),UiState.valueOf(text(r,"state")),unsigned(r,"query_sequence"),unsigned(r,"observation_revision"),ref(r,"timeline_read"),ref(r,"timeline_native_frame"),optional(r,"event_instance_id",SuccessorUiObligationCodec::unsigned),optional(r,"event_read",ExactRef::fromJson));}
    private static ObjectNode close(CloseAttempt v){var r=StrictJson.object().put("action_id",v.actionId()).put("command_body_sha256",v.commandBodySha256()).put("entered_at_utc",v.enteredAtUtc().toString());r.set("original_command",v.originalCommand().toJson());r.set("before",frame(v.before()));put(r,"receipt",v.receipt(),SuccessorUiObligationCodec::receipt);return r;}
    private static CloseAttempt close(JsonNode v){var r=row(v,"action_id","command_body_sha256","entered_at_utc","original_command","before","receipt");return new CloseAttempt(text(r,"action_id"),text(r,"command_body_sha256"),ref(r,"original_command"),frame(r.get("before")),time(r,"entered_at_utc"),optional(r,"receipt",SuccessorUiObligationCodec::receipt));}
    private static ObjectNode receipt(CloseReceipt v){var r=StrictJson.object().put("outcome",v.outcome().name());r.set("canonical_receipt",v.canonicalReceipt().toJson());put(r,"material_clearance",v.materialClearance(),ExactRef::toJson);put(r,"verified_date_advance",v.verifiedDateAdvance(),ExactRef::toJson);put(r,"reconciliation",v.reconciliation(),SuccessorUiObligationCodec::reconciliation);return r;}
    private static CloseReceipt receipt(JsonNode v){var r=row(v,"outcome","canonical_receipt","material_clearance","verified_date_advance","reconciliation");return new CloseReceipt(ActionReceipt.Outcome.valueOf(text(r,"outcome")),ref(r,"canonical_receipt"),optional(r,"material_clearance",ExactRef::fromJson),optional(r,"verified_date_advance",ExactRef::fromJson),optional(r,"reconciliation",SuccessorUiObligationCodec::reconciliation));}
    private static ObjectNode reconciliation(ReadOnlyReconciliation v){var r=StrictJson.object();r.set("original_unknown_receipt",v.originalUnknownReceipt().toJson());r.set("confirmed_receipt",v.confirmedReceipt().toJson());r.set("same_original_action_proof",v.sameOriginalActionProof().toJson());put(r,"material_clearance",v.materialClearance(),ExactRef::toJson);put(r,"verified_date_advance",v.verifiedDateAdvance(),ExactRef::toJson);return r;}
    private static ReadOnlyReconciliation reconciliation(JsonNode v){var r=row(v,"original_unknown_receipt","confirmed_receipt","same_original_action_proof","material_clearance","verified_date_advance");return new ReadOnlyReconciliation(ref(r,"original_unknown_receipt"),ref(r,"confirmed_receipt"),ref(r,"same_original_action_proof"),optional(r,"material_clearance",ExactRef::fromJson),optional(r,"verified_date_advance",ExactRef::fromJson));}
    private static ObjectNode rebind(Rebind v){var r=StrictJson.object();if(v.retainedPending().isPresent())r.set("retained_pending_binding",binding(v.retainedPending().orElseThrow()));else r.set("retained",frame(v.retained()));r.set("resumed",frame(v.resumed()));r.set("prior_canonical_obligation",v.priorCanonicalObligation().toJson());r.set("actual_private_rebind_proof",v.actualPrivateRebindProof().toJson());return r;}
    private static Rebind rebind(JsonNode v){boolean unobserved=v.has("retained_pending_binding");var r=unobserved?row(v,"retained_pending_binding","resumed","prior_canonical_obligation","actual_private_rebind_proof"):row(v,"retained","resumed","prior_canonical_obligation","actual_private_rebind_proof");return unobserved?Rebind.unobserved(binding(r.get("retained_pending_binding")),frame(r.get("resumed")),ref(r,"prior_canonical_obligation"),ref(r,"actual_private_rebind_proof")):new Rebind(frame(r.get("retained")),frame(r.get("resumed")),ref(r,"prior_canonical_obligation"),ref(r,"actual_private_rebind_proof"));}
    private static ObjectNode finalization(Finalization v){var r=StrictJson.object().put("cause_digest",v.causeDigest()).put("finalized_at_utc",v.finalizedAtUtc().toString());r.set("final_m3_proof",v.finalM3Proof().toJson());r.set("current",frame(v.current()));put(r,"actual_close_receipt",v.actualCloseReceipt(),ExactRef::toJson);put(r,"verified_date_advance",v.verifiedDateAdvance(),ExactRef::toJson);v.continuityBinding().ifPresent(ref->r.set("continuity_binding",ref.toJson()));return r;}
    private static Finalization finalization(JsonNode v,boolean continuity){var r=continuity?row(v,"cause_digest","finalized_at_utc","final_m3_proof","current","actual_close_receipt","verified_date_advance","continuity_binding"):row(v,"cause_digest","finalized_at_utc","final_m3_proof","current","actual_close_receipt","verified_date_advance");return new Finalization(text(r,"cause_digest"),ref(r,"final_m3_proof"),frame(r.get("current")),optional(r,"actual_close_receipt",ExactRef::fromJson),optional(r,"verified_date_advance",ExactRef::fromJson),time(r,"finalized_at_utc"),continuity?Optional.of(ref(r,"continuity_binding")):Optional.empty());}
    private static ObjectNode row(JsonNode v,String... names){require(v instanceof ObjectNode,"closed UI object required");var r=(ObjectNode)v;var actual=new HashSet<String>();r.fieldNames().forEachRemaining(actual::add);require(actual.equals(Set.of(names)),"UI fields differ: "+actual);return r;}
    private static String text(ObjectNode r,String k){JsonNode v=r.get(k);require(v!=null&&v.isTextual(),"UI text required: "+k);return v.textValue();}
    private static ExactRef ref(ObjectNode r,String k){return ExactRef.fromJson(r.get(k));}
    private static Instant time(ObjectNode r,String k){return Instant.parse(text(r,k));}
    private static BigInteger integer(ObjectNode r,String k){JsonNode v=r.get(k);require(v!=null&&v.isIntegralNumber(),"UI integral JSON number required: "+k);return v.bigIntegerValue();}
    private static BigInteger character(ObjectNode r,String k){return NativeCharacterId.fromJson(r.get(k)).asBigInteger();}
    private static long safe(ObjectNode r,String k){BigInteger v=integer(r,k);require(v.bitLength()<63,"UI safe integer required: "+k);long actual=v.longValueExact();StrictJson.safe(actual,0);return actual;}
    private static BigInteger signed(ObjectNode r,String k){String v=text(r,k);require(v.matches("0|-?[1-9][0-9]*"),"canonical signed UI integer required: "+k);return new BigInteger(v);}
    private static String decimal(BigInteger v){return new CrossJsDecimalUInt64(v.toString()).decimal();}
    private static BigInteger uint64(ObjectNode r,String k){return new BigInteger(new CrossJsDecimalUInt64(text(r,k)).decimal());}
    private static BigInteger unsigned(ObjectNode r,String k){return unsigned(r.get(k));}
    private static BigInteger unsigned(JsonNode v){require(v!=null&&v.isTextual()&&v.textValue().matches("0|[1-9][0-9]*"),"canonical exact unsigned UI integer string required");return new BigInteger(v.textValue());}
    private static <T> Optional<T> optional(ObjectNode r,String k,Function<JsonNode,T> decoder){JsonNode v=r.get(k);require(v!=null,"explicit UI optional field required: "+k);return v.isNull()?Optional.empty():Optional.of(decoder.apply(v));}
    private static Optional<String> optionalText(ObjectNode r,String k){JsonNode v=r.get(k);return v==null||v.isNull()?Optional.empty():Optional.of(StrictJson.text(v));}
    private static <T> void put(ObjectNode r,String k,Optional<T> value,Function<T,? extends JsonNode> encoder){if(value.isPresent())r.set(k,encoder.apply(value.orElseThrow()));else r.putNull(k);}
    private static void putOptionalText(ObjectNode r,String k,Optional<String> value){if(value.isPresent())r.put(k,value.orElseThrow());else r.putNull(k);}
}
