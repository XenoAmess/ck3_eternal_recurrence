package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.NativeStepDiscriminator;
import org.xar.ck3.control.application.action.ExecutableStepBindings.Kind;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ExactRef;

/** Fixed root installation of an original private mutation. An absent advertised capability grants nothing. */
public final class NativePrivateActionPermission {
    @FunctionalInterface public interface RequestValidator { void validate(NativeRequest request) throws IOException; }
    /** Runs the real business/runtime verifier and returns caller metadata, without source-file admission. */
    @FunctionalInterface public interface QualificationVerifier {
        ExactRef verify(NativePipeEndpoint.Config actualConfig, NativeWire.Hello actualHello,
                GuardEvidence actualFrame, NativeRequest typedRequest) throws IOException;
    }
    private final OperationKey operation;
    private final String permissionKey;
    private final ExactRef originalProducerSource;
    private final RequestValidator validator;
    private final java.util.Optional<QualificationVerifier> qualification;

    public NativePrivateActionPermission(OperationKey operation, String permissionKey, ExactRef originalProducerSource,
            RequestValidator validator, QualificationVerifier qualification) {
        this(operation,permissionKey,originalProducerSource,validator,java.util.Optional.of(qualification));
    }
    private NativePrivateActionPermission(OperationKey operation,String permissionKey,ExactRef originalProducerSource,
            RequestValidator validator,java.util.Optional<QualificationVerifier> qualification) {
        this.operation = Objects.requireNonNull(operation); this.permissionKey = Objects.requireNonNull(permissionKey);
        if (permissionKey.isBlank()) throw new IllegalArgumentException("explicit original private permission key required");
        this.originalProducerSource = Objects.requireNonNull(originalProducerSource);
        if (originalProducerSource.bytes() < 1) throw new IllegalArgumentException("original private mutation source required");
        this.validator = Objects.requireNonNull(validator); this.qualification = Objects.requireNonNull(qualification);
    }
    public OperationKey operation() { return operation; }
    public String permissionKey() { return permissionKey; }
    public ExactRef originalProducerSource() { return originalProducerSource; }
    /** Keeps the fixed operation and request validator without historical source qualification. */
    public NativePrivateActionPermission withoutSourceQualification() {
        return new NativePrivateActionPermission(operation,permissionKey,originalProducerSource,validator,java.util.Optional.empty());
    }
    /** Adds the actual Root qualification without replacing this operation's original domain verifier. */
    public NativePrivateActionPermission withAdditionalQualification(QualificationVerifier additional) {
        Objects.requireNonNull(additional);
        if(qualification.isEmpty())return new NativePrivateActionPermission(operation,permissionKey,originalProducerSource,validator,additional);
        return new NativePrivateActionPermission(operation, permissionKey, originalProducerSource, validator,
                (config, hello, guard, request) -> {
                    ExactRef originalEvidence = qualification.orElseThrow().verify(config, hello, guard, request);
                    if (originalEvidence == null || originalEvidence.bytes() < 1) throw new IOException("private mutation original qualification returned absent or empty evidence");
                    ExactRef additionalEvidence = additional.verify(config, hello, guard, request);
                    if (additionalEvidence == null || additionalEvidence.bytes() < 1) throw new IOException("private mutation additional qualification returned absent or empty evidence");
                    return additionalEvidence;
                });
    }
    void verify(NativePipeEndpoint.Config config, NativeWire.Hello hello, GuardEvidence guard, NativeRequest request) throws IOException {
        if (request.requiredCapability().isPresent()) throw new IOException("private mutation differs from its fixed root registration");
        try { NativeStepDiscriminator.requireRequest(operation, Kind.ACTION, request); }
        catch (IllegalArgumentException invalid) { throw new IOException("private mutation differs from its fixed logical registration", invalid); }
        validator.validate(request);
        if(qualification.isEmpty())return;
        ExactRef qualified = qualification.orElseThrow().verify(config, hello, guard, request);
        if (qualified == null || qualified.bytes() < 1) throw new IOException("private mutation qualification returned absent or empty evidence");
    }
}
