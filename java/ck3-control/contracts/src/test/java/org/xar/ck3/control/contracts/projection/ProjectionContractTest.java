package org.xar.ck3.control.contracts.projection;

import java.math.BigInteger;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

class ProjectionContractTest {
    private record CheckedInput(BigInteger id, ProjectionJson original) { }
    private static final ProjectionOperation OP = ProjectionOperation.WAR_BUDGET_EVALUATE;

    @Test void requestRoundTripRetainsOriginalNumericTokensAndJsonDistinctions() {
        byte[] payload = utf8("{\"id\":18446744073709551615,\"float\":1.0,\"exponent\":0e0,\"null\":null,\"empty\":[],\"object\":{}}");
        var call = new ProjectionCall(new ProjectionCall.Identity("round-1", OP), ProjectionJson.object(payload, 1024));
        ProjectionCall parsed = ProjectionWire.decodeCall(ProjectionWire.encodeCall(call));
        assertEquals(call.identity(), parsed.identity()); assertArrayEquals(payload, parsed.payload().bytes());
        var result = assertInstanceOf(ProjectionResult.Succeeded.class, dispatcher(new AtomicInteger()).dispatch(ProjectionWire.encodeCall(call)));
        assertArrayEquals(payload, result.result().bytes());
        String reply = new String(ProjectionWire.encodeResult(result), StandardCharsets.UTF_8);
        assertTrue(reply.contains("\"float\":1.0")); assertTrue(reply.contains("\"exponent\":0e0"));
        assertTrue(reply.contains("18446744073709551615"));
    }

    @Test void actualDomainIntegerCodecRejectsWrongTokensBeforeApplication() {
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null")) {
            AtomicInteger applied = new AtomicInteger();
            var rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                    dispatcher(applied).dispatch(call("{\"id\":" + token + "}")));
            assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code()); assertEquals(0, applied.get());
        }
    }

    @Test void versionFieldAndExactEnvelopeRejectCoercionMissingNullExtraAndDuplicates() {
        String valid = new String(call("{\"id\":1}"), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null", "2")) {
            assertThrows(ProjectionProtocolException.class,
                    () -> ProjectionWire.decodeCall(utf8(valid.replace("\"schema_version\":1", "\"schema_version\":" + token))));
        }
        for (String bad : List.of(valid.replace("\"schema_version\":1,", ""), valid.replace("\"payload\":{\"id\":1}", "\"payload\":null"),
                valid.replace("\"payload\":{\"id\":1}", "\"payload\":[]"), valid.replace("\"payload\":{\"id\":1}", "\"payload\":{} ,\"extra\":0"),
                valid.replace("\"payload\":{\"id\":1}", "\"payload\":{\"id\":1,\"id\":2}"),
                valid.replace("\"request_id\":\"test-1\"", "\"request_id\":\"test-1\",\"request_id\":\"test-2\""), valid + " {}")) {
            assertThrows(ProjectionProtocolException.class, () -> ProjectionWire.decodeCall(utf8(bad)));
        }
    }

    @Test void unknownWireOperationAndMissingPortRemainDifferentFailures() {
        byte[] unknown = utf8(new String(call("{\"id\":1}"), StandardCharsets.UTF_8).replace(OP.wire(), "not-registered-anywhere"));
        assertEquals(ProjectionError.Code.UNSUPPORTED_OPERATION,
                assertInstanceOf(ProjectionResult.Rejected.class, new ProjectionDispatcher(List.of()).dispatch(unknown)).error().code());
        var unavailable = assertInstanceOf(ProjectionResult.Rejected.class, new ProjectionDispatcher(List.of()).dispatch(call("{\"id\":1}")));
        assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE, unavailable.error().code());
        assertEquals("test-1", unavailable.identity().orElseThrow().requestId());
    }

    @Test void invalidUtf8SurrogatesTrailingTokensAndDuplicateKeysNeverReachPorts() {
        assertThrows(ProjectionProtocolException.class, () -> ProjectionJson.value(new byte[] {(byte) 0xc3, 0x28}, 8));
        for (String bad : List.of("{\"x\":\"\\ud800\"}", "{\"\\udc00\":0}", "{} {}", "{\"x\":NaN}", "{\"x\":1,\"x\":2}")) {
            assertThrows(ProjectionProtocolException.class, () -> ProjectionJson.value(utf8(bad), 1024));
        }
        assertThrows(ProjectionProtocolException.class, () -> new ProjectionCall(new ProjectionCall.Identity("test", OP), ProjectionJson.value(utf8("null"), 8)));
    }

    @Test void bomCannotMoveFromAStandaloneValueIntoTheMiddleOfAJsonEnvelope() {
        assertThrows(ProjectionProtocolException.class, () -> ProjectionJson.object(bom(utf8("{}")), 64));
        assertThrows(ProjectionProtocolException.class, () -> ProjectionJson.value(bom(utf8("null")), 64));
        assertThrows(ProjectionProtocolException.class, () -> ProjectionWire.decodeCall(bom(call("{}"))));
        ProjectionPort<ProjectionJson, ProjectionJson> port = new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return OP; }
            @Override public ProjectionJson decode(byte[] raw) { return ProjectionJson.object(raw, 64); }
            @Override public ProjectionJson project(ProjectionJson input) { return input; }
            @Override public byte[] encode(ProjectionJson result) { return bom(utf8("null")); }
        };
        assertEquals(ProjectionError.Code.INVALID_RESULT, assertInstanceOf(ProjectionResult.Rejected.class,
                new ProjectionDispatcher(List.of(RegisteredProjection.of(port))).dispatch(call("{}"))).error().code());
    }

    @Test void bomlessUtf16AndUtf32AreNotUtf8JsonDespiteByteParserAutoDetection() {
        for (String encoding : List.of("UTF-16BE", "UTF-16LE", "UTF-32BE", "UTF-32LE")) {
            byte[] wrong = "{}".getBytes(java.nio.charset.Charset.forName(encoding));
            assertThrows(ProjectionProtocolException.class, () -> ProjectionJson.object(wrong, 64));
            byte[] envelope = new String(call("{}"), StandardCharsets.UTF_8).getBytes(java.nio.charset.Charset.forName(encoding));
            assertThrows(ProjectionProtocolException.class, () -> ProjectionWire.decodeCall(envelope));
        }
        assertArrayEquals(utf8("{\"allowed\":\"\\u0000\"}"), ProjectionJson.object(utf8("{\"allowed\":\"\\u0000\"}"), 64).bytes());
    }

    @Test void rawSpanUsesUtf8ByteOffsetsWithUnicodeAndEnvelopeFieldOrderChanges() {
        String payload = "{ \"id\":18446744073709551615, \"名字\":\"中文😀\", \"decimal\":0e0 }";
        String envelope = " \n{\"payload\":" + payload + ",\"operation\":\"war-budget-evaluate\",\"request_id\":\"unicode-1\",\"schema_version\":1,\"schema\":\"xar.projection-call/v1\"} \n";
        ProjectionCall decoded = ProjectionWire.decodeCall(utf8(envelope));
        assertArrayEquals(utf8(payload), decoded.payload().bytes());
        assertArrayEquals(utf8(payload), ProjectionWire.decodeCall(ProjectionWire.encodeCall(decoded)).payload().bytes());
    }

    @Test void alternateEncodingsAndRawNulCannotReachARegisteredDecoder() {
        AtomicInteger decoded = new AtomicInteger();
        var dispatcher = new ProjectionDispatcher(List.of(RegisteredProjection.of(echoPort(decoded, 1024, 1024))));
        List<byte[]> malformed = new ArrayList<>(alternateEncodings(new String(call("{}"), StandardCharsets.UTF_8)));
        malformed.add(utf8(new String(call("{\"text\":\"raw-nul\"}"), StandardCharsets.UTF_8)
                .replace("raw-nul", String.valueOf('\0'))));
        for (byte[] raw : malformed) {
            var rejected = assertInstanceOf(ProjectionResult.Rejected.class, dispatcher.dispatch(raw));
            assertEquals(ProjectionError.Code.INVALID_ENVELOPE, rejected.error().code());
            assertTrue(rejected.identity().isEmpty());
            ProjectionJson.object(ProjectionWire.encodeResult(rejected), 1024);
        }
        assertEquals(0, decoded.get());
    }

    @Test void alternateEncoderBytesBecomeAValidWireRejectionInsteadOfAnInvalidSuccess() {
        List<byte[]> malformed = new ArrayList<>(alternateEncodings("null"));
        malformed.add(utf8("\"literal" + '\0' + "\""));
        for (byte[] rawResult : malformed) {
            ProjectionPort<ProjectionJson, ProjectionJson> port = new ProjectionPort<>() {
                @Override public ProjectionOperation operation() { return OP; }
                @Override public ProjectionJson decode(byte[] raw) { return ProjectionJson.object(raw, 64); }
                @Override public ProjectionJson project(ProjectionJson input) { return input; }
                @Override public byte[] encode(ProjectionJson result) { return rawResult; }
            };
            var rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                    new ProjectionDispatcher(List.of(RegisteredProjection.of(port))).dispatch(call("{}")));
            assertEquals(ProjectionError.Code.INVALID_RESULT, rejected.error().code());
            byte[] wire = ProjectionWire.encodeResult(rejected);
            ProjectionJson.object(wire, 1024);
            assertFalse(new String(wire, StandardCharsets.UTF_8).contains("\"result\":"));
        }
    }

    @Test void escapedNulAndOriginalNumberTokensSurviveTheCompleteRegisteredWire() {
        String payload = "{ \"escaped\":\"\\u0000\", \"decimal\":1.0, \"exponent\":0e0, \"id\":18446744073709551615 }";
        var dispatcher = new ProjectionDispatcher(List.of(RegisteredProjection.of(echoPort(new AtomicInteger(), 1024, 1024))));
        var succeeded = assertInstanceOf(ProjectionResult.Succeeded.class, dispatcher.dispatch(call(payload)));
        assertArrayEquals(utf8(payload), succeeded.result().bytes());
        byte[] expected = utf8("{\"schema\":\"xar.projection-result/v1\",\"schema_version\":1,\"request_id\":\"test-1\","
                + "\"operation\":\"war-budget-evaluate\",\"status\":\"succeeded\",\"result\":" + payload + "}");
        assertArrayEquals(expected, ProjectionWire.encodeResult(succeeded));
        assertArrayEquals(utf8(payload), assertInstanceOf(ProjectionResult.Succeeded.class,
                ProjectionWire.decodeResult(ProjectionWire.encodeResult(succeeded))).result().bytes());
    }

    @Test void resultConsumerPreservesOriginalScalarArrayObjectAndNullValueBytes() {
        var identity = new ProjectionCall.Identity("consumer-1", OP);
        for (String value : List.of("null", "true", "false", "18446744073709551615", "1.0", "0e0",
                "\"中文😀\\u0000\"", "[ null, 1.0, 0e0, 18446744073709551615 ]",
                "{ \"null\":null, \"empty\":[], \"value\":1.0 }")) {
            byte[] expected = utf8(value);
            byte[] wire = ProjectionWire.encodeResult(new ProjectionResult.Succeeded(identity, ProjectionJson.value(expected, 1024)));
            var decoded = assertInstanceOf(ProjectionResult.Succeeded.class, ProjectionWire.decodeResult(wire));
            assertEquals(identity, decoded.identity()); assertArrayEquals(expected, decoded.result().bytes());
            assertArrayEquals(wire, ProjectionWire.encodeResult(decoded));
        }
    }

    @Test void resultConsumerUsesByteSpansAcrossUnicodeAndUnorderedEnvelopeFields() {
        String value = "\"中文😀\\u0000\"";
        String envelope = " \n{\"result\":" + value + ",\"status\":\"succeeded\",\"operation\":\"war-budget-evaluate\","
                + "\"request_id\":\"consumer-2\",\"schema_version\":1,\"schema\":\"xar.projection-result/v1\"} \n";
        var decoded = assertInstanceOf(ProjectionResult.Succeeded.class, ProjectionWire.decodeResult(utf8(envelope)));
        assertArrayEquals(utf8(value), decoded.result().bytes());
    }

    @Test void resultConsumerRoundTripsEveryBoundErrorAndOnlyThreeUnboundProtocolErrors() {
        for (ProjectionError.Code code : ProjectionError.Code.values()) {
            assertEquals(code, ProjectionError.Code.fromWire(code.wire()));
            var expected = new ProjectionResult.Rejected(Optional.of(new ProjectionCall.Identity("consumer-error-1", OP)),
                    new ProjectionError(code, "public refusal 中文😀"));
            byte[] wire = ProjectionWire.encodeResult(expected);
            assertEquals(expected, ProjectionWire.decodeResult(wire));
            assertArrayEquals(wire, ProjectionWire.encodeResult(ProjectionWire.decodeResult(wire)));
        }
        for (ProjectionError.Code code : List.of(ProjectionError.Code.INVALID_ENVELOPE,
                ProjectionError.Code.UNSUPPORTED_VERSION, ProjectionError.Code.UNSUPPORTED_OPERATION)) {
            var expected = new ProjectionResult.Rejected(Optional.empty(), new ProjectionError(code, "protocol rejection"));
            byte[] wire = ProjectionWire.encodeResult(expected);
            assertEquals(expected, ProjectionWire.decodeResult(wire));
            assertArrayEquals(wire, ProjectionWire.encodeResult(ProjectionWire.decodeResult(wire)));
        }
    }

    @Test void unboundBusinessAndExecutionErrorsCannotBecomeDomainRejections() {
        String unbound = new String(ProjectionWire.encodeResult(new ProjectionResult.Rejected(Optional.empty(),
                new ProjectionError(ProjectionError.Code.INVALID_ENVELOPE, "protocol rejection"))), StandardCharsets.UTF_8);
        for (ProjectionError.Code code : List.of(ProjectionError.Code.DOMAIN_REJECTED, ProjectionError.Code.INVALID_PAYLOAD,
                ProjectionError.Code.OPERATION_UNAVAILABLE, ProjectionError.Code.PROJECTION_FAILED,
                ProjectionError.Code.PAYLOAD_TOO_LARGE, ProjectionError.Code.INVALID_RESULT)) {
            assertThrows(IllegalArgumentException.class, () -> new ProjectionResult.Rejected(Optional.empty(),
                    new ProjectionError(code, "unbound rejection")));
            byte[] raw = utf8(unbound.replace("\"code\":\"invalid-envelope\"", "\"code\":\"" + code.wire() + "\""));
            var rejected = assertThrows(ProjectionProtocolException.class, () -> ProjectionWire.decodeResult(raw));
            assertEquals(ProjectionError.Code.INVALID_ENVELOPE, rejected.code());
        }
    }

    @Test void resultConsumerRejectsMissingNullExtraDuplicateAndMixedStatusFields() {
        String success = new String(ProjectionWire.encodeResult(new ProjectionResult.Succeeded(
                new ProjectionCall.Identity("consumer-1", OP), ProjectionJson.value(utf8("null"), 4))), StandardCharsets.UTF_8);
        String rejection = new String(ProjectionWire.encodeResult(new ProjectionResult.Rejected(Optional.empty(),
                new ProjectionError(ProjectionError.Code.INVALID_ENVELOPE, "invalid request"))), StandardCharsets.UTF_8);
        for (String bad : List.of(success.replace(",\"result\":null", ""), success.replace("\"request_id\":\"consumer-1\"", "\"request_id\":null"),
                success.replace("\"operation\":\"war-budget-evaluate\"", "\"operation\":null"),
                success.replace("\"status\":\"succeeded\"", "\"status\":\"rejected\""),
                success.replace("\"schema_version\":1,", ""), success.replace("\"schema\":\"xar.projection-result/v1\"", "\"schema\":\"xar.projection-result/v2\""),
                success.replace("\"result\":null", "\"result\":null,\"extra\":0"),
                success.replace("\"result\":null", "\"result\":null,\"result\":0"), success + " {}",
                success.replace("\"result\":null", "\"result\":{\"x\":1,\"x\":2}"),
                success.replace("\"result\":null", "\"result\":\"\\ud800\""),
                rejection.replace("\"request_id\":null", "\"request_id\":\"consumer-1\""),
                rejection.replace("\"operation\":null", "\"operation\":\"war-budget-evaluate\""),
                rejection.replace("\"error\":{", "\"result\":null,\"error\":{"),
                rejection.replace("\"error\":{\"code\":\"invalid-envelope\",\"message\":\"invalid request\"}", "\"error\":null"),
                rejection.replace("\"code\":\"invalid-envelope\",", ""),
                rejection.replace("\"code\":\"invalid-envelope\"", "\"code\":\"INVALID_ENVELOPE\""),
                rejection.replace("\"code\":\"invalid-envelope\"", "\"code\":\"invalid_envelope\""),
                rejection.replace("\"code\":\"invalid-envelope\"", "\"code\":\"invalid-envelope\",\"code\":\"invalid-result\""),
                rejection.replace("\"message\":\"invalid request\"", "\"message\":null"),
                rejection.replace("\"message\":\"invalid request\"", "\"message\":\"\\ud800\""),
                rejection.replace("\"message\":\"invalid request\"", "\"message\":\"invalid request\",\"extra\":0"))) {
            assertThrows(ProjectionProtocolException.class, () -> ProjectionWire.decodeResult(utf8(bad)));
        }
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null", "2")) {
            var error = assertThrows(ProjectionProtocolException.class,
                    () -> ProjectionWire.decodeResult(utf8(success.replace("\"schema_version\":1", "\"schema_version\":" + token))));
            assertEquals(ProjectionError.Code.UNSUPPORTED_VERSION, error.code());
        }
    }

    @Test void resultConsumerRejectsAlternateEncodingsAndLiteralNulAtTheSharedBoundary() {
        byte[] wire = ProjectionWire.encodeResult(new ProjectionResult.Succeeded(new ProjectionCall.Identity("consumer-1", OP),
                ProjectionJson.value(utf8("\"raw-nul\""), 32)));
        List<byte[]> malformed = new ArrayList<>(alternateEncodings(new String(wire, StandardCharsets.UTF_8)));
        malformed.add(utf8(new String(wire, StandardCharsets.UTF_8).replace("raw-nul", String.valueOf('\0'))));
        for (byte[] raw : malformed) {
            assertThrows(ProjectionProtocolException.class, () -> ProjectionWire.decodeResult(raw));
        }
    }

    @Test void outputNullIsAProducedValueRatherThanAnAbsentResult() {
        var port = new ProjectionPort<ProjectionJson, ProjectionJson>() {
            @Override public ProjectionOperation operation() { return OP; }
            @Override public ProjectionJson decode(byte[] raw) { return ProjectionJson.object(raw, 16); }
            @Override public ProjectionJson project(ProjectionJson input) { return ProjectionJson.value(utf8("null"), 4); }
            @Override public byte[] encode(ProjectionJson output) { return output.bytes(); }
        };
        var result = assertInstanceOf(ProjectionResult.Succeeded.class, new ProjectionDispatcher(List.of(RegisteredProjection.of(port))).dispatch(call("{}")));
        assertArrayEquals(utf8("null"), result.result().bytes());
        assertTrue(new String(ProjectionWire.encodeResult(result), StandardCharsets.UTF_8).endsWith("\"result\":null}"));
    }

    @Test void operationBudgetRefusesBeforeDecodeAndDoesNotWidenDefaultMapBudget() {
        AtomicInteger decoded = new AtomicInteger();
        var port = echoPort(decoded, 16, 16);
        var result = assertInstanceOf(ProjectionResult.Rejected.class,
                new ProjectionDispatcher(List.of(RegisteredProjection.of(port))).dispatch(call("{\"too-long-for-role\":1}")));
        assertEquals(ProjectionError.Code.PAYLOAD_TOO_LARGE, result.error().code()); assertEquals(0, decoded.get());
        assertEquals(65_536, StrictJson.INPUT_MAX_BYTES); assertEquals(1_048_576, StrictJson.EXPLICIT_MAX_BYTES);
    }

    @Test void invalidDomainOutputAndApplicationFailureAreClosedBranches() {
        ProjectionPort<ProjectionJson, ProjectionJson> broken = new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return OP; }
            @Override public ProjectionJson decode(byte[] raw) { return ProjectionJson.object(raw, 64); }
            @Override public ProjectionJson project(ProjectionJson input) { throw new IllegalStateException("fixture application failure"); }
            @Override public byte[] encode(ProjectionJson output) { return output.bytes(); }
        };
        assertEquals(ProjectionError.Code.PROJECTION_FAILED, assertInstanceOf(ProjectionResult.Rejected.class,
                new ProjectionDispatcher(List.of(RegisteredProjection.of(broken))).dispatch(call("{}"))).error().code());
        ProjectionPort<ProjectionJson, ProjectionJson> invalid = new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return OP; }
            @Override public ProjectionJson decode(byte[] raw) { return ProjectionJson.object(raw, 64); }
            @Override public ProjectionJson project(ProjectionJson input) { return input; }
            @Override public byte[] encode(ProjectionJson output) { return utf8("{\"missing\":"); }
        };
        assertEquals(ProjectionError.Code.INVALID_RESULT, assertInstanceOf(ProjectionResult.Rejected.class,
                new ProjectionDispatcher(List.of(RegisteredProjection.of(invalid))).dispatch(call("{}"))).error().code());
    }

    @Test void explicitProjectionRoleCanCarryLargerInputsWithoutWideningAnyExistingCodec() {
        byte[] payload = utf8("{\"opaque\":\"" + "x".repeat(65_536) + "\"}");
        byte[] request = call(new String(payload, StandardCharsets.UTF_8));
        var original = new ProjectionDispatcher(List.of(RegisteredProjection.of(echoPort(new AtomicInteger(), 65_536, 65_536))));
        assertEquals(ProjectionError.Code.PAYLOAD_TOO_LARGE,
                assertInstanceOf(ProjectionResult.Rejected.class, original.dispatch(request)).error().code());
        var explicit = new ProjectionDispatcher(List.of(RegisteredProjection.of(echoPort(new AtomicInteger(), ProjectionJson.MAX_BYTES, ProjectionJson.MAX_BYTES))));
        assertArrayEquals(payload, assertInstanceOf(ProjectionResult.Succeeded.class, explicit.dispatch(request)).result().bytes());
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(payload));
    }

    @Test void publicBusinessRefusalPreservesItsReasonWithoutBecomingTransportSuccess() {
        ProjectionPort<ProjectionJson, ProjectionJson> port = new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return OP; }
            @Override public ProjectionJson decode(byte[] raw) { return ProjectionJson.object(raw, 64); }
            @Override public ProjectionJson project(ProjectionJson input) { throw new ProjectionDomainRejection("original public refusal 中文"); }
            @Override public byte[] encode(ProjectionJson result) { return result.bytes(); }
        };
        var rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                new ProjectionDispatcher(List.of(RegisteredProjection.of(port))).dispatch(call("{}")));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected.error().code());
        assertEquals("original public refusal 中文", rejected.error().message());
        String reply = new String(ProjectionWire.encodeResult(rejected), StandardCharsets.UTF_8);
        assertTrue(reply.contains("\"code\":\"domain-rejected\"")); assertFalse(reply.contains("\"result\""));
    }

    @Test void catalogsRejectDuplicateOperationInsteadOfSelectingAnArbitraryProvider() {
        ProjectionPortCatalog catalog = () -> List.of(RegisteredProjection.of(echoPort(new AtomicInteger(), 64, 64)));
        assertThrows(IllegalArgumentException.class, () -> ProjectionDispatcher.fromCatalogs(List.of(catalog, catalog)));
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(List.of(catalog));
        assertEquals(List.of(new ProjectionDispatcher.OperationProfile(OP, 64, 64)), dispatcher.profiles());
        assertThrows(UnsupportedOperationException.class, () -> dispatcher.profiles().clear());
    }

    @Test void validatedDocumentsAndPortArgumentsHaveDefensiveByteOwnership() {
        byte[] original = utf8("{\"id\":1}"); ProjectionJson json = ProjectionJson.object(original, 64); original[0] = 0;
        byte[] returned = json.bytes(); returned[0] = 0; assertEquals((byte) '{', json.bytes()[0]);
        assertThrows(IllegalArgumentException.class, () -> RegisteredProjection.of(echoPort(new AtomicInteger(), ProjectionJson.MAX_BYTES + 1, 64)));
    }

    private static ProjectionDispatcher dispatcher(AtomicInteger applied) {
        ProjectionPort<CheckedInput, ProjectionJson> port = new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return OP; }
            @Override public CheckedInput decode(byte[] raw) {
                BigInteger id = StrictJson.integer(StrictJson.parse(raw).get("id"), BigInteger.ZERO, StrictJson.UINT64_MAX);
                return new CheckedInput(id, ProjectionJson.object(raw, 1024));
            }
            @Override public ProjectionJson project(CheckedInput input) { applied.incrementAndGet(); return input.original(); }
            @Override public byte[] encode(ProjectionJson output) { return output.bytes(); }
        };
        return new ProjectionDispatcher(List.of(RegisteredProjection.of(port)));
    }
    private static ProjectionPort<ProjectionJson, ProjectionJson> echoPort(AtomicInteger decoded, int input, int output) {
        return new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return OP; }
            @Override public ProjectionJson decode(byte[] raw) { decoded.incrementAndGet(); return ProjectionJson.object(raw, input); }
            @Override public ProjectionJson project(ProjectionJson value) { return value; }
            @Override public byte[] encode(ProjectionJson value) { return value.bytes(); }
            @Override public int inputMaximumBytes() { return input; }
            @Override public int outputMaximumBytes() { return output; }
        };
    }
    private static byte[] call(String payload) {
        return ProjectionWire.encodeCall(new ProjectionCall(new ProjectionCall.Identity("test-1", OP), ProjectionJson.object(utf8(payload), ProjectionJson.MAX_BYTES)));
    }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static List<byte[]> alternateEncodings(String json) {
        List<byte[]> encodings = new ArrayList<>(); encodings.add(bom(utf8(json)));
        for (String name : List.of("UTF-16BE", "UTF-16LE", "UTF-32BE", "UTF-32LE")) {
            byte[] encoded = json.getBytes(Charset.forName(name)); encodings.add(encoded);
            byte[] marker = switch (name) {
                case "UTF-16BE" -> new byte[] {(byte) 0xfe, (byte) 0xff};
                case "UTF-16LE" -> new byte[] {(byte) 0xff, (byte) 0xfe};
                case "UTF-32BE" -> new byte[] {0, 0, (byte) 0xfe, (byte) 0xff};
                case "UTF-32LE" -> new byte[] {(byte) 0xff, (byte) 0xfe, 0, 0};
                default -> throw new IllegalArgumentException("unexpected test encoding");
            };
            byte[] marked = new byte[marker.length + encoded.length];
            System.arraycopy(marker, 0, marked, 0, marker.length);
            System.arraycopy(encoded, 0, marked, marker.length, encoded.length); encodings.add(marked);
        }
        return List.copyOf(encodings);
    }
    private static byte[] bom(byte[] raw) {
        byte[] output = new byte[raw.length + 3]; output[0] = (byte) 0xef; output[1] = (byte) 0xbb; output[2] = (byte) 0xbf;
        System.arraycopy(raw, 0, output, 3, raw.length); return output;
    }
}
