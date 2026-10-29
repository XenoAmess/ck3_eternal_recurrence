package org.xar.ck3.control.wave3.development.constructiondiagnostics;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.RoundingMode;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.ToIntFunction;

import static org.xar.ck3.control.wave3.development.constructiondiagnostics.ConstructionDiagnosticModel.*;

/** Pure fixed-path projector. Wrong observed protocol token types cannot bind business fields. */
public final class ConstructionDiagnosticProjection {
    private static final BigInteger MIN = BigInteger.ONE.shiftLeft(63).negate();
    private static final BigInteger MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    private ConstructionDiagnosticProjection() { }

    public static Projection project(Request request, ToIntFunction<Projection> encodedSize) {
        Frame frame = request.frame();
        boolean type = frame.frameType().equals(new Text("command_result"));
        boolean protocol = frame.protocol().equals(new IntegerValue(BigInteger.ONE));
        boolean identity = frame.requestId().equals(new Text(request.requestId()));
        boolean bound = frame.mapping() && type && protocol && identity;
        Classification classification = frame.type() == PythonType.NONE ? Classification.ABSENT
                : !bound ? Classification.INVALID_ENVELOPE
                : frame.ok().equals(new Flag(false)) ? Classification.REJECTED : Classification.INVALID_RESULT;
        Map<Field, Value> result = new LinkedHashMap<>();
        result.put(Field.SCHEMA, new IntegerValue(BigInteger.ONE)); result.put(Field.SOURCE, new Text(MARKER));
        result.put(Field.DIAGNOSTIC_ONLY, new Flag(true)); result.put(Field.CLASSIFICATION, new Text(classification.wire()));
        result.put(Field.REQUEST_ID, scalar(new Text(request.requestId()), 160)); result.put(Field.STEP, scalar(new Text(request.step()), 96));
        result.put(Field.REVISION, scalar(new IntegerValue(request.revision()), 128)); result.put(Field.TIMEOUT, scalar(request.timeout(), 128));
        result.put(Field.ELAPSED, scalar(new FloatingValue(roundSix(request.elapsed())), 128));
        result.put(Field.FRAME_TYPE, scalar(new Text(frame.pythonTypeName()), 64));
        result.put(Field.GATE_MAPPING, new Flag(frame.mapping())); result.put(Field.GATE_TYPE, new Flag(frame.mapping() && type));
        result.put(Field.GATE_PROTOCOL, new Flag(frame.mapping() && protocol)); result.put(Field.GATE_REQUEST, new Flag(frame.mapping() && identity));
        result.put(Field.GATE_OK, new Flag(frame.mapping() && frame.ok().equals(new Flag(true))));
        result.put(Field.GATE_RESULT, new Flag(frame.mapping() && frame.resultMapping()));
        if (frame.mapping()) {
            result.put(Field.RECEIVED_TYPE, scalar(frame.frameType(), 64)); result.put(Field.RECEIVED_PROTOCOL, scalar(frame.protocol(), 64));
            result.put(Field.RECEIVED_REQUEST, scalar(frame.requestId(), 160)); result.put(Field.RECEIVED_OK, scalar(frame.ok(), 64));
        }
        if (bound) {
            result.put(Field.NATIVE_ERROR, scalar(frame.error(), 512)); result.put(Field.RESULT_TYPE, scalar(new Text(frame.resultPythonTypeName()), 64));
            if (frame.resultMapping()) {
                result.put(Field.RESULT_STEP, scalar(frame.resultStep(), 96)); result.put(Field.RESULT_ACCEPTED, scalar(frame.resultAccepted(), 128));
            }
            for (Field field : Field.values()) {
                if (field.ordinal() >= Field.PROBE_STATUS.ordinal() && field.ordinal() <= Field.DEFINITION_INDEX.ordinal()) {
                    int limit = field == Field.PROBE_FAILURE || field == Field.MODEL_FAILURE || field == Field.WORLD_FAILURE ? 128 : 64;
                    result.put(field, scalar(frame.probeFields().getOrDefault(field, new Nil()), limit));
                }
            }
        }
        while (encodedSize.applyAsInt(new Projection(result)) > LIMIT) {
            Field largest = null; int size = -1;
            for (Map.Entry<Field, Value> entry : result.entrySet()) {
                if (entry.getKey() != Field.SOURCE && entry.getKey() != Field.CLASSIFICATION && entry.getValue() instanceof Text text
                        && !text.value().isEmpty() && utf8Size(text.value()) > size) {
                    largest = entry.getKey(); size = utf8Size(text.value());
                }
            }
            if (largest == null) return fallback(request, classification, result);
            result.put(largest, scalar(result.get(largest), size / 2)); result.put(Field.TEXT_TRUNCATED, new Flag(true));
        }
        return new Projection(result);
    }

    public static Value scalar(Value value, int limit) {
        if (limit < 0) throw new IllegalArgumentException("nonnegative diagnostic text limit");
        if (value instanceof Nil || value instanceof Flag) return value;
        if (value instanceof IntegerValue integer) return integer.value().compareTo(MIN) >= 0 && integer.value().compareTo(MAX) <= 0 ? value : new Nil();
        if (value instanceof FloatingValue number) return Double.isFinite(number.value()) ? value : new Nil();
        if (value instanceof Text text) return new Text(clip(text.value(), limit));
        return new Nil();
    }
    private static String clip(String value, int limit) {
        int end = value.offsetByCodePoints(0, Math.min(limit, value.codePointCount(0, value.length())));
        byte[] bytes = value.substring(0, end).getBytes(StandardCharsets.UTF_8);
        try {
            return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.IGNORE).onUnmappableCharacter(CodingErrorAction.IGNORE)
                    .decode(ByteBuffer.wrap(bytes, 0, Math.min(limit, bytes.length))).toString();
        } catch (java.nio.charset.CharacterCodingException failure) { throw new IllegalStateException("ignore decoder failed", failure); }
    }
    private static int utf8Size(String value) { return value.getBytes(StandardCharsets.UTF_8).length; }
    private static double roundSix(double value) {
        if (!Double.isFinite(value)) return value;
        BigDecimal rounded = new BigDecimal(value).setScale(6, RoundingMode.HALF_EVEN);
        if (rounded.signum() == 0 && Double.doubleToRawLongBits(value) < 0) return -0.0;
        return rounded.doubleValue();
    }
    private static Projection fallback(Request request, Classification classification, Map<Field, Value> previous) {
        Map<Field, Value> result = new LinkedHashMap<>();
        result.put(Field.SCHEMA, new IntegerValue(BigInteger.ONE)); result.put(Field.SOURCE, new Text(MARKER));
        result.put(Field.DIAGNOSTIC_ONLY, new Flag(true)); result.put(Field.CLASSIFICATION, new Text(classification.wire()));
        result.put(Field.LIMIT_REACHED, new Flag(true)); result.put(Field.REQUEST_ID, scalar(new Text(request.requestId()), 160));
        result.put(Field.STEP, scalar(new Text(request.step()), 96)); result.put(Field.NATIVE_ERROR, scalar(previous.getOrDefault(Field.NATIVE_ERROR, new Nil()), 128));
        for (Field field : new Field[]{Field.DEFINITION_STAGE, Field.PROBE_REVISION, Field.PROBE_DATE, Field.PROBE_EPOCH})
            result.put(field, previous.getOrDefault(field, new Nil()));
        return new Projection(result);
    }
}
