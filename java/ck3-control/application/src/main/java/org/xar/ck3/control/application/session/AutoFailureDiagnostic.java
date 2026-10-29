package org.xar.ck3.control.application.session;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Source-qualified domain projection of a retained failed action; no action/retry/settlement authority. */
public record AutoFailureDiagnostic(Kind kind,String actionId,String actionBodySha256,String message,
        RawJson diagnostic,ExactRef originalEvidence) {
    public enum Kind {
        EXACT_DAY("exact_day_clock_failure_v1","StepPostconditionError",16384),
        TACTICAL_CLOCK("tactical_clock_failure_v1","StepPostconditionError",16384),
        CONSTRUCTION_TRANSPORT("construction_transport_v1","BridgeUnavailableError",4096);
        private final String key,errorType;private final int maximumBytes;
        Kind(String key,String errorType,int maximumBytes){this.key=key;this.errorType=errorType;this.maximumBytes=maximumBytes;}
        public String key(){return key;}public String errorType(){return errorType;}public int maximumBytes(){return maximumBytes;}
    }
    @FunctionalInterface public interface Port {
        /** Read the actual same-writer archived failure basis; absence never means success or retry permission. */
        Optional<AutoFailureDiagnostic> project(ActionReceipt actual,ActionPorts.OutcomeArchive sameWriterArchive);
    }
    public AutoFailureDiagnostic {
        Objects.requireNonNull(kind);StrictJson.text(actionId);StrictJson.text(message);Objects.requireNonNull(diagnostic);Objects.requireNonNull(originalEvidence);
        StrictJson.require(actionBodySha256!=null && actionBodySha256.matches("[0-9a-f]{64}") && originalEvidence.bytes()>0,"exact original action/failure evidence required");
        StrictJson.require(diagnostic.bytes().length<=kind.maximumBytes(),"finite original diagnostic required");
        var body=StrictJson.parse(diagnostic.bytes());StrictJson.require(body.isObject(),"domain diagnostic must be a JSON object");
        if(kind==Kind.EXACT_DAY || kind==Kind.TACTICAL_CLOCK) {
            String schema=kind==Kind.EXACT_DAY?"xar.exact-day-clock-failure.v2":"xar.tactical-clock-failure.v1";
            StrictJson.require(body.path("schema").isTextual() && schema.equals(body.get("schema").textValue()),"exact domain diagnostic schema required");
            StrictJson.require(body.path("is_error").isBoolean() && body.get("is_error").booleanValue()
                    && body.path("never_replay").isBoolean() && body.get("never_replay").booleanValue()
                    && body.path("credit").isIntegralNumber() && body.get("credit").bigIntegerValue().signum()==0,"failed clock is never replay or credit authority");
            if(kind==Kind.EXACT_DAY)StrictJson.require(body.path("normal_status_query_attempted").isBoolean() && !body.get("normal_status_query_attempted").booleanValue()
                    && body.path("stop_validation_attempted").isBoolean() && !body.get("stop_validation_attempted").booleanValue()
                    && body.has("stopped_status") && body.get("stopped_status").isNull() && body.path("stop_credit").isBoolean() && !body.get("stop_credit").booleanValue(),"unobserved exact-day stop cannot become observed/credited");
        } else StrictJson.require(body.path("schema_version").isIntegralNumber() && body.get("schema_version").bigIntegerValue().equals(java.math.BigInteger.ONE)
                && body.path("source").isTextual() && body.get("source").textValue().equals("construction_transport_v1")
                && body.path("diagnostic_only").isBoolean() && body.get("diagnostic_only").booleanValue(),"exact construction diagnostic source required");
    }
    public void require(ActionReceipt actual) {
        StrictJson.require(actual.command().actionId().equals(actionId) && actual.bodySha256().equals(actionBodySha256),"diagnostic crossed original action body");
    }
}
