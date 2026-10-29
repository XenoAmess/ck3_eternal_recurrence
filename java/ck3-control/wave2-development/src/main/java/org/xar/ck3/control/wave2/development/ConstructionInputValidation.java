package org.xar.ck3.control.wave2.development;

import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Only explicit input-token validators use this adapter; algorithms and encoders run outside it. */
public final class ConstructionInputValidation {
    private ConstructionInputValidation() { }

    public static <T> T read(Supplier<T> inputValidator) {
        Objects.requireNonNull(inputValidator);
        try {
            return inputValidator.get();
        } catch (ContractViolationException rejected) {
            throw new ProjectionDomainRejection(rejected.getMessage());
        }
    }

    public static void check(Runnable inputValidator) {
        Objects.requireNonNull(inputValidator);
        read(() -> { inputValidator.run(); return Boolean.TRUE; });
    }
}
