package org.xar.ck3.control.wave2.runtime.stdioidentity;

import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Expected identity only; constructing a claim does not measure or retain a process. */
public record ProcessIdentityClaimV1(long pid, String creationFiletimeDecimal, Path executable) {
    public ProcessIdentityClaimV1 {
        StrictJson.require(pid >= 1 && pid <= 0xffff_ffffL, "positive DWORD PID required");
        new CrossJsDecimalUInt64(creationFiletimeDecimal);
        StrictJson.require(!"0".equals(creationFiletimeDecimal), "positive creation FILETIME required");
        StrictJson.require(executable != null && executable.isAbsolute()
                && executable.toString().indexOf('\0') < 0, "absolute process image path required");
        StrictJson.require(StandardCharsets.UTF_8.newEncoder().canEncode(executable.toString()),
                "well-formed process image Unicode required");
        executable = executable.normalize();
    }

    public boolean sameGeneration(ProcessIdentityClaimV1 other) {
        return other != null && pid == other.pid && creationFiletimeDecimal.equals(other.creationFiletimeDecimal)
                && imageIdentity(executable).equals(imageIdentity(other.executable));
    }

    private static String imageIdentity(Path image) {
        return image.normalize().toString().replace('/', '\\').toLowerCase(Locale.ROOT);
    }
}
