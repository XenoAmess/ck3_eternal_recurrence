package org.xar.ck3.control.wave2.runtime.providerchain;

import java.math.BigInteger;
import org.xar.ck3.control.contracts.StrictJson;

/** Values from the original private-origin readback. No handle or resource seal is serializable here. */
public final class OriginReadbackValues {
    private OriginReadbackValues() { }

    /** Preserve the original opaque epoch label; equality binds it to the local source owner. */
    public record SourceEpoch(String value) {
        public SourceEpoch { StrictJson.text(value); }
    }

    public record ProcessKey(BigInteger pid, String creationFiletimeDecimal, String normalizedExecutable) {
        public ProcessKey {
            positive(pid); uint64(creationFiletimeDecimal, true);
            CreatorSourceManifest.requireAbsoluteWindows(normalizedExecutable);
        }
    }

    public record DllFileKey(String volumeSerialDecimal, String fileIdHex, BigInteger size,
                             SourceSha256 sha256, String normalizedFinalPath) {
        public DllFileKey {
            uint64(volumeSerialDecimal, false); positive(size);
            StrictJson.require(fileIdHex != null && fileIdHex.matches("[0-9a-f]{32}"), "exact original 16-byte file identity required");
            StrictJson.require(sha256 != null, "held file digest value required");
            CreatorSourceManifest.requireAbsoluteWindows(normalizedFinalPath);
        }
    }

    public record Body(SourceEpoch epoch, SourceSha256 creator, ProcessKey target,
                       DllFileKey file, ProcessKey origin, ProcessKey app) {
        public Body {
            StrictJson.require(epoch != null && creator != null && target != null && file != null
                            && origin != null && app != null, "complete original origin body required");
        }
    }

    public record Reply(BigInteger sequence, String nonce, Body body) {
        public Reply {
            positive(sequence);
            StrictJson.text(nonce);
            StrictJson.require(nonce.codePointCount(0, nonce.length()) == 32, "exact original request nonce length required");
            StrictJson.require(body != null, "original origin body required");
        }

        /** Equality of values; the original caller still holds and checks the actual resources. */
        public boolean matchesExpected(BigInteger expectedSequence, String expectedNonce, Body expectedBody) {
            return sequence.equals(expectedSequence) && nonce.equals(expectedNonce) && body.equals(expectedBody);
        }
    }

    static void positive(BigInteger value) {
        StrictJson.require(value != null && value.signum() > 0, "exact positive original integer required");
    }

    private static void uint64(String value, boolean positive) {
        StrictJson.require(value != null && value.matches("0|[1-9][0-9]*") && value.length() <= 20,
                "canonical uint64 decimal text required");
        BigInteger number = new BigInteger(value);
        StrictJson.require(number.compareTo(StrictJson.UINT64_MAX) <= 0 && (!positive || number.signum() > 0),
                "original uint64 decimal range required");
    }
}
