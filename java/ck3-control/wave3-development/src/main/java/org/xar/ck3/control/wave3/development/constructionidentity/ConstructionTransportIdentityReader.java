package org.xar.ck3.control.wave3.development.constructionidentity;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.development.constructionidentity.ConstructionProcessIdentityCache.CachedIdentity;
import org.xar.ck3.control.wave3.development.constructionidentity.ConstructionProcessIdentityCache.OriginalIdentityProducer;
import org.xar.ck3.control.wave3.development.constructionidentity.ConstructionProcessIdentityCache.ProducerIdentity;

/** Exact original transport _identity consumer. The tuple is source data, not Game/adoption eligibility. */
public final class ConstructionTransportIdentityReader {
    private ConstructionTransportIdentityReader() { }
    public record IdentityTuple(long pid, String originalCreationDate) {
        public IdentityTuple {
            StrictJson.require(pid >= 1 && pid <= 0xffff_ffffL, "positive DWORD transport PID required");
            StrictJson.text(originalCreationDate);
        }
    }
    public static final class IdentityUnavailableException extends IOException {
        private static final long serialVersionUID = 1L;
        public IdentityUnavailableException() { super("construction trial lacks a live exact process identity"); }
    }
    public static long parseSessionPid(byte[] originalJsonToken) {
        return StrictJson.integer(StrictJson.parse(originalJsonToken), 1, 0xffff_ffffL);
    }
    public static IdentityTuple read(long sessionPid, ConstructionProcessIdentityCache cache,
                                     OriginalIdentityProducer originalProducer) throws IOException {
        Objects.requireNonNull(cache);
        var result = cache.read(sessionPid, originalProducer);
        String creation = switch (result) {
            case CachedIdentity cached -> cached.originalCreationDate();
            case ProducerIdentity producer -> producer.original().fields().creationDate();
            case ConstructionProcessIdentityCache.NoIdentity ignored -> null;
        };
        if (creation == null || creation.isEmpty()) { throw new IdentityUnavailableException(); }
        return new IdentityTuple(sessionPid, creation);
    }
}
