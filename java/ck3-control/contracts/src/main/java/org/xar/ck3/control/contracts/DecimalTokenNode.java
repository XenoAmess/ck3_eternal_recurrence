package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.node.NumericNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;

/** Immutable JSON floating token. Tree interop must not erase the sign of zero or its category. */
public final class DecimalTokenNode extends NumericNode {
    private static final long serialVersionUID = 1L;
    private final String token;
    public DecimalTokenNode(String originalToken) {
        requireToken(originalToken); token = originalToken;
    }
    public static void requireToken(String originalToken) {
        StrictJson.require(originalToken != null && !originalToken.isEmpty()
                && originalToken.length() <= FullJsonTree.MAXIMUM_DRIVER_BYTES
                && originalToken.matches("-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
                && (originalToken.indexOf('.') >= 0 || originalToken.indexOf('e') >= 0 || originalToken.indexOf('E') >= 0),
                "original JSON floating token required");
    }
    public String originalToken() { return token; }
    @Override public JsonToken asToken() { return JsonToken.VALUE_NUMBER_FLOAT; }
    @Override public JsonParser.NumberType numberType() { return JsonParser.NumberType.BIG_DECIMAL; }
    @Override public boolean isFloatingPointNumber() { return true; }
    @Override public boolean isBigDecimal() { return true; }
    @Override public Number numberValue() { return decimalValue(); }
    @Override public BigDecimal decimalValue() { return new BigDecimal(token); }
    @Override public BigInteger bigIntegerValue() { return decimalValue().toBigInteger(); }
    @Override public int intValue() { return decimalValue().intValue(); }
    @Override public long longValue() { return decimalValue().longValue(); }
    @Override public double doubleValue() { return Double.parseDouble(token); }
    @Override public float floatValue() { return Float.parseFloat(token); }
    @Override public boolean canConvertToInt() {
        try { var value=decimalValue(); return value.compareTo(BigDecimal.valueOf(Integer.MIN_VALUE))>=0
                && value.compareTo(BigDecimal.valueOf(Integer.MAX_VALUE))<=0; } catch (NumberFormatException failure) { return false; }
    }
    @Override public boolean canConvertToLong() {
        try { var value=decimalValue(); return value.compareTo(BigDecimal.valueOf(Long.MIN_VALUE))>=0
                && value.compareTo(BigDecimal.valueOf(Long.MAX_VALUE))<=0; } catch (NumberFormatException failure) { return false; }
    }
    @Override public boolean canConvertToExactIntegral() {
        try { decimalValue().toBigIntegerExact(); return true; } catch (ArithmeticException | NumberFormatException failure) { return false; }
    }
    @Override public String asText() { return token; }
    @Override public void serialize(JsonGenerator output, SerializerProvider provider) throws IOException { output.writeNumber(token); }
    @Override public String toString() { return token; }
    @Override public boolean equals(Object other) { return other instanceof DecimalTokenNode node && token.equals(node.token); }
    @Override public int hashCode() { return token.hashCode(); }
}
