package org.xar.ck3.control.contracts.projection;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ProjectionExplicitRejectionTest {
    private enum Stage { DECODE, PROJECT, ENCODE }
    private static final ProjectionCall.Identity ID = new ProjectionCall.Identity("explicit-refusal-1", ProjectionOperation.WAR_BUDGET_EVALUATE);

    @Test void decodeValidationKeepsItsInvalidPayloadClassification() {
        rejected(Stage.DECODE, new IllegalArgumentException("domain integer required"),
                ProjectionError.Code.INVALID_PAYLOAD, "domain integer required");
    }

    @Test void explicitDomainRefusalFromDecodeOrProjectPreservesThePublicReason() {
        for (Stage stage : List.of(Stage.DECODE, Stage.PROJECT)) {
            rejected(stage, new ProjectionDomainRejection("original public refusal 中文"),
                    ProjectionError.Code.DOMAIN_REJECTED, "original public refusal 中文");
        }
    }

    @Test void projectImplementationExceptionsCannotMasqueradeAsBusinessRefusals() {
        for (RuntimeException failure : List.of(new IllegalArgumentException("internal serializer argument bug"),
                new IllegalStateException("internal implementation failure"))) {
            rejected(Stage.PROJECT, failure, ProjectionError.Code.PROJECTION_FAILED, "registered pure projection failed");
        }
    }

    @Test void encoderFailuresRemainInvalidResultsEvenWhenTheyUseTheDomainMarker() {
        for (RuntimeException failure : List.of(new IllegalArgumentException("internal serializer argument bug"),
                new ProjectionDomainRejection("encoder is not a business refusal channel"))) {
            rejected(Stage.ENCODE, failure, ProjectionError.Code.INVALID_RESULT, "result rejected by registered encoder or role budget");
        }
    }

    @Test void missingServerContextCannotBecomeABusinessRefusal() {
        for (Stage stage : List.of(Stage.DECODE, Stage.PROJECT)) {
            rejected(stage, new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, "fixture source absent"),
                    ProjectionError.Code.OPERATION_UNAVAILABLE, "registered operation server context unavailable");
        }
    }

    private static void rejected(Stage stage, RuntimeException failure, ProjectionError.Code code, String message) {
        ProjectionPort<ProjectionJson, ProjectionJson> port = new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return ID.operation(); }
            @Override public ProjectionJson decode(byte[] raw) {
                if (stage == Stage.DECODE) { throw failure; }
                return ProjectionJson.object(raw, 64);
            }
            @Override public ProjectionJson project(ProjectionJson input) {
                if (stage == Stage.PROJECT) { throw failure; }
                return input;
            }
            @Override public byte[] encode(ProjectionJson result) {
                if (stage == Stage.ENCODE) { throw failure; }
                return result.bytes();
            }
        };
        ProjectionCall call = new ProjectionCall(ID, ProjectionJson.object("{}".getBytes(StandardCharsets.UTF_8), 64));
        var result = assertInstanceOf(ProjectionResult.Rejected.class, new ProjectionDispatcher(List.of(RegisteredProjection.of(port)))
                .dispatch(ProjectionWire.encodeCall(call)));
        assertEquals(Optional.of(ID), result.identity()); assertEquals(code, result.error().code()); assertEquals(message, result.error().message());
        byte[] wire = ProjectionWire.encodeResult(result);
        assertEquals(result, ProjectionWire.decodeResult(wire));
        assertFalse(new String(wire, StandardCharsets.UTF_8).contains("\"result\":"));
    }
}
