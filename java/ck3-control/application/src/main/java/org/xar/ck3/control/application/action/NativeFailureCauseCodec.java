package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.action.NativeActionPort.*;

/** Sole strict DATA codec for actual dispatch failure provenance. It grants no retry or timeout inference. */
public final class NativeFailureCauseCodec {
    public static final String SCHEMA="xar.native.dispatch-failure-cause/v1";
    private NativeFailureCauseCodec() { }
    public static RawJson encode(FailureCause original){return new RawJson(StrictJson.canonical(encodeValue(original)));}
    public static FailureCause decode(RawJson encoded){return decodeValue(StrictJson.parse(Objects.requireNonNull(encoded).bytes()));}
    public static ObjectNode encodeValue(FailureCause original) {
        Objects.requireNonNull(original);
        ObjectNode row=StrictJson.object().put("schema",SCHEMA).put("kind",original.kind().name()).put("stage",original.stage().name());
        row.set("exception",exceptionValue(original.originalException()));row.set("cause",exceptionValue(original.originalCause()));
        if(original.deadline().isEmpty())row.putNull("deadline");
        else {
            DeadlineObservation actual=original.deadline().orElseThrow();
            row.set("deadline",StrictJson.object().put("supplied_deadline",actual.suppliedDeadline().toString())
                    .put("observed_at",actual.observedAt().toString()).put("monotonic_expired",actual.monotonicExpired()));
        }
        return row;
    }
    public static FailureCause decodeValue(JsonNode encoded) {
        ObjectNode row=StrictJson.object(encoded,Set.of("schema","kind","stage","exception","cause","deadline"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"actual Native failure-cause schema required");
        Optional<DeadlineObservation> deadline=Optional.empty();JsonNode value=row.get("deadline");
        if(!value.isNull()) {
            ObjectNode observed=StrictJson.object(value,Set.of("supplied_deadline","observed_at","monotonic_expired"));
            StrictJson.require(observed.get("monotonic_expired").isBoolean(),"actual boolean monotonic expiration required");
            deadline=Optional.of(new DeadlineObservation(instant(observed.get("supplied_deadline")),instant(observed.get("observed_at")),observed.get("monotonic_expired").booleanValue()));
        }
        return new FailureCause(FailureKind.valueOf(StrictJson.text(row.get("kind"))),FailureStage.valueOf(StrictJson.text(row.get("stage"))),
                exception(row.get("exception")),exception(row.get("cause")),deadline);
    }
    private static JsonNode exceptionValue(Optional<OriginalException> original) {
        if(original.isEmpty())return com.fasterxml.jackson.databind.node.NullNode.getInstance();
        OriginalException actual=original.orElseThrow();ObjectNode row=StrictJson.object().put("java_type",actual.javaType());
        if(actual.message()==null)row.putNull("message");else row.put("message",actual.message());return row;
    }
    private static Optional<OriginalException> exception(JsonNode value) {
        if(value.isNull())return Optional.empty();ObjectNode row=StrictJson.object(value,Set.of("java_type","message"));
        JsonNode message=row.get("message");StrictJson.require(message.isNull()||message.isTextual(),"original nullable Java message required");
        return Optional.of(new OriginalException(StrictJson.text(row.get("java_type")),message.isNull()?null:message.textValue()));
    }
    private static Instant instant(JsonNode value) {
        String text=StrictJson.text(value);Instant actual=Instant.parse(text);
        StrictJson.require(actual.toString().equals(text),"canonical actual deadline instant required");return actual;
    }
}
