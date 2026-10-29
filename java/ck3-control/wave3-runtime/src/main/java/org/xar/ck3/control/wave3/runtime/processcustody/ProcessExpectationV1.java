package org.xar.ck3.control.wave3.runtime.processcustody;

import java.nio.file.Path;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;

/** Exact optional expectations, separate from an actual captured kernel generation. */
public record ProcessExpectationV1(long pid, Optional<String> creationFiletimeDecimal,
        Optional<Path> executable) {
    public ProcessExpectationV1 {
        StrictJson.require(pid >= 1 && pid <= 0xffff_ffffL, "positive DWORD PID required");
        Objects.requireNonNull(creationFiletimeDecimal); Objects.requireNonNull(executable);
        creationFiletimeDecimal.ifPresent(value -> {
            new CrossJsDecimalUInt64(value);
            StrictJson.require(!value.equals("0"), "positive expected process birth required");
        });
        executable = executable.map(path -> {
            StrictJson.require(path.isAbsolute(), "absolute expected image path required");
            return path.normalize();
        });
    }

    public static ProcessExpectationV1 exact(ProcessIdentityClaimV1 identity) {
        Objects.requireNonNull(identity);
        return new ProcessExpectationV1(identity.pid(), Optional.of(identity.creationFiletimeDecimal()),
                Optional.of(identity.executable()));
    }

    public static ProcessExpectationV1 measuredPid(long pid) {
        return new ProcessExpectationV1(pid, Optional.empty(), Optional.empty());
    }
}
