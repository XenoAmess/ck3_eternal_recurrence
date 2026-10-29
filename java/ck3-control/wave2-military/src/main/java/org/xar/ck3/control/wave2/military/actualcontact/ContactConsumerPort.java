package org.xar.ck3.control.wave2.military.actualcontact;

import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.armyinventory.ArmyInventoryValidation;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowCodec;
import org.xar.ck3.control.wave2.military.routewindowstep.RouteWindowStepCodec;

/** The existing consumer seam: all five wire routes call their single Java producer.
 * Native pipe ownership, current-frame checks, planning and clock submission stay with
 * the callers. This port does not acquire a frame or infer native qualification.
 */
public final class ContactConsumerPort {
    private ContactConsumerPort() { }

    public enum Operation {
        INVENTORY, ROUTE_WINDOW, ROUTE_STEP, ACTUAL_SCOPE, ACTUAL_QUERY
    }

    /** Exact original UTF-8 bytes; no String encoding or JSON tree round trip. */
    public record Request(Operation operation, byte[] inputJson) {
        public Request {
            Objects.requireNonNull(operation, "operation"); Objects.requireNonNull(inputJson, "inputJson");
            inputJson = inputJson.clone();
            int length = inputJson.length;
            StrictJson.require(length > 0 && length <= StrictJson.INPUT_MAX_BYTES, "bounded original contact request required");
            try {
                StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(inputJson));
            } catch (CharacterCodingException error) { throw new ContractViolationException("invalid original request UTF-8", error); }
        }
        @Override public byte[] inputJson() { return inputJson.clone(); }
        @Override public boolean equals(Object other) { return other instanceof Request that && operation == that.operation && Arrays.equals(inputJson, that.inputJson); }
        @Override public int hashCode() { return 31 * operation.hashCode() + Arrays.hashCode(inputJson); }
    }

    /** Immutable JSON representation; a parser tuple stays its declared JSON array. */
    public record Result(byte[] outputJson) {
        public Result {
            Objects.requireNonNull(outputJson, "outputJson");
            outputJson = outputJson.clone(); StrictJson.parse(outputJson);
        }
        @Override public byte[] outputJson() { return outputJson.clone(); }
        public byte[] utf8() { return outputJson.clone(); }
        @Override public boolean equals(Object other) { return other instanceof Result that && Arrays.equals(outputJson, that.outputJson); }
        @Override public int hashCode() { return Arrays.hashCode(outputJson); }
    }

    /** Validate only input contracts on the host decoder lane; keep original bytes. */
    public static void validateRequest(Request request) {
        Objects.requireNonNull(request, "request");
        byte[] original = request.inputJson();
        switch (request.operation()) {
            case INVENTORY -> ArmyInventoryValidation.validateRequest(original);
            case ROUTE_WINDOW -> RouteWindowCodec.validateRequest(original);
            case ROUTE_STEP -> RouteWindowStepCodec.validateRequest(original);
            case ACTUAL_SCOPE -> ActualContactCodec.validateScopeRequest(original);
            case ACTUAL_QUERY -> ActualContactCodec.validateQueryRequest(original);
        }
    }

    public static Result apply(Request request) {
        Objects.requireNonNull(request, "request");
        byte[] original = request.inputJson();
        byte[] output = switch (request.operation()) {
            case INVENTORY -> ArmyInventoryValidation.validate(original);
            case ROUTE_WINDOW -> RouteWindowCodec.project(original);
            case ROUTE_STEP -> RouteWindowStepCodec.execute(original);
            case ACTUAL_SCOPE -> ActualContactCodec.normalize(original);
            case ACTUAL_QUERY -> ActualContactCodec.query(original);
        };
        return new Result(output);
    }
}
