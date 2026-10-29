package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2ResearchEngine;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Adapter failure regressions. Synthetic domains are fault fixtures, never business acceptance or a second host. */
class G2ResearchResourceTest {
    @TempDir Path temporary;

    @Test void everyTypedDomainFailureRetainsItsClosedCodeAndHttpStatus() {
        for (G2HttpError.Code code : G2HttpError.Code.values()) {
            var resource = resource(new FaultDomain(code));
            var response = resource.evaluate(G2Wire.encodeRequest(request()));
            assertEquals(code.httpStatus(), response.getStatus());
            G2HttpError error = G2Wire.decodeError((byte[]) response.getEntity());
            assertEquals(code, error.code());
            assertFalse(error.message().contains("private-local-path"));
        }
    }

    @Test void anUnexpectedIllegalStateRemainsInternalFailureRatherThanMasqueradingAsUnavailable() {
        G2Domain domain = new G2Domain() {
            @Override public Milestone milestone() { return Milestone.M0; }
            @Override public G2Response evaluate(G2Request input) { throw new IllegalStateException("private-local-path"); }
        };
        var response = resource(domain).evaluate(G2Wire.encodeRequest(request()));
        assertEquals(500, response.getStatus());
        assertEquals(G2HttpError.Code.INTERNAL_FAILURE, G2Wire.decodeError((byte[]) response.getEntity()).code());
    }

    @Test void sourceOrRequestIdentityDriftIsRejectedByTheSharedEngineAndPreservedByHttpAdapter() {
        for (boolean changeSource : List.of(false, true)) {
            G2Domain domain = new G2Domain() {
                @Override public Milestone milestone() { return Milestone.M0; }
                @Override public G2Response evaluate(G2Request input) {
                    G2Source source = changeSource ? new G2Source("another-fixture-machine", input.source().observedAtUtc(),
                            input.source().exactBuild(), input.source().sourceRef()) : input.source();
                    return new G2Response(changeSource ? input.requestId() : "different-request", Milestone.M0, source, json());
                }
            };
            var response = resource(domain).evaluate(G2Wire.encodeRequest(request()));
            assertEquals(409, response.getStatus());
            assertEquals(G2HttpError.Code.SOURCE_MISMATCH, G2Wire.decodeError((byte[]) response.getEntity()).code());
        }
    }

    @Test void nullDomainOutputIsInvalidResultAndCannotBecomeSuccessfulHttpJson() {
        G2Domain domain = new G2Domain() {
            @Override public Milestone milestone() { return Milestone.M0; }
            @Override public G2Response evaluate(G2Request input) { return null; }
        };
        var response = resource(domain).evaluate(G2Wire.encodeRequest(request()));
        assertEquals(500, response.getStatus());
        assertEquals(G2HttpError.Code.INVALID_RESULT, G2Wire.decodeError((byte[]) response.getEntity()).code());
    }

    @Test void malformedAndOversizedInputsAreRejectedBeforeAnyDomainRuns() {
        AtomicInteger calls = new AtomicInteger();
        G2Domain domain = new G2Domain() {
            @Override public Milestone milestone() { return Milestone.M0; }
            @Override public G2Response evaluate(G2Request input) {
                calls.incrementAndGet(); return new G2Response(input.requestId(), input.milestone(), input.source(), json());
            }
        };
        var resource = resource(domain);
        assertEquals(400, resource.evaluate("{}".getBytes(StandardCharsets.UTF_8)).getStatus());
        var oversized = resource.evaluate(new byte[G2Wire.MAX_REQUEST_BYTES + 1]);
        assertEquals(413, oversized.getStatus());
        assertEquals(G2HttpError.Code.PAYLOAD_TOO_LARGE, G2Wire.decodeError((byte[]) oversized.getEntity()).code());
        assertEquals(0, calls.get());
    }

    @Test void aProvenanceReferenceDoesNotCauseAnyFileReadOrRequireTheReferencedFileToExist() {
        G2Domain domain = new G2Domain() {
            @Override public Milestone milestone() { return Milestone.M0; }
            @Override public G2Response evaluate(G2Request input) {
                return new G2Response(input.requestId(), input.milestone(), input.source(), json());
            }
        };
        Path missing = temporary.resolve("not-an-opened-source.json");
        assertFalse(Files.exists(missing));
        var response = resource(domain).evaluate(G2Wire.encodeRequest(request()));
        assertEquals(200, response.getStatus());
        assertFalse(Files.exists(missing));
        assertEquals(request().source(), G2Wire.decodeResponse((byte[]) response.getEntity()).source());
    }

    private G2Request request() {
        G2Source source = new G2Source("http-adapter-fixture", "2026-10-22T20:00:00Z", "synthetic-no-game",
                new ExactRef(temporary.resolve("not-an-opened-source.json").toAbsolutePath().toString(), 1, "1".repeat(64)));
        return new G2Request("adapter-fixture", Milestone.M0, source, json());
    }

    private static G2ResearchResource resource(G2Domain domain) {
        return new G2ResearchResource(new G2ResearchHost(new G2ResearchEngine(List.of(domain))));
    }

    private static ProjectionJson json() { return ProjectionJson.object("{}".getBytes(StandardCharsets.UTF_8), 16); }

    private record FaultDomain(G2HttpError.Code code) implements G2Domain {
        @Override public Milestone milestone() { return Milestone.M0; }
        @Override public G2Response evaluate(G2Request request) { throw new G2Exception(code, "private-local-path"); }
    }
}
