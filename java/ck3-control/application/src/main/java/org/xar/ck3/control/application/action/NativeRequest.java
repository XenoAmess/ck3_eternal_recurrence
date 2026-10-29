package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One prepared primitive. Durable preparation originals are metadata; only additionalFields are sent on the native wire. */
public record NativeRequest(String step, Optional<String> requiredCapability, RawJson additionalFields, List<ExactRef> preparationEvidence) {
    public NativeRequest {
        NativeStepDiscriminator.requireNativeStep(step); requiredCapability = Objects.requireNonNull(requiredCapability); requiredCapability.ifPresent(StrictJson::text); Objects.requireNonNull(additionalFields);
        additionalFields.requireProtocolBound();
        var fields = additionalFields.objectFieldNames();
        for (String reserved : java.util.Set.of("type", "protocol_version", "request_id", "step", "expected_revision"))
            StrictJson.require(!fields.contains(reserved), "native fields cannot replace reserved protocol fields");
        preparationEvidence = List.copyOf(preparationEvidence);
        StrictJson.require(preparationEvidence.size() <= 32 && new java.util.HashSet<>(preparationEvidence).size() == preparationEvidence.size(), "bounded unique actual preparation originals required");
        preparationEvidence.forEach(ref -> StrictJson.require(ref.bytes() > 0, "nonempty original preparation evidence required"));
    }
    /** Historical preparations retain empty evidence; this constructor invents no original preflight. */
    public NativeRequest(String step, Optional<String> requiredCapability, RawJson additionalFields) { this(step, requiredCapability, additionalFields, List.of()); }
    public NativeRequest(String step, String requiredCapability, RawJson additionalFields) { this(step, Optional.of(StrictJson.text(requiredCapability)), additionalFields, List.of()); }
    public NativeRequest(String step, String requiredCapability, RawJson additionalFields, List<ExactRef> preparationEvidence) { this(step, Optional.of(StrictJson.text(requiredCapability)), additionalFields, preparationEvidence); }
}
