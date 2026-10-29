package org.xar.ck3.control.wave2.finance.feastterminal;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Set;

/** Narrow dynamic boundary helpers; no JsonNode is retained in the domain model. */
final class TerminalJson {
    private TerminalJson() { }
    static void fields(JsonNode node, Set<String> expected) {
        require(node != null && node.isObject());
        Set<String> actual = new HashSet<>(); node.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(expected));
    }
    static boolean bool(JsonNode node) {
        require(node != null && node.isBoolean()); return node.booleanValue();
    }
    static String text(JsonNode node) {
        require(node != null && node.isTextual()); return node.textValue();
    }
    static BigInteger integer(JsonNode node, BigInteger low, BigInteger high) {
        require(node != null && node.isIntegralNumber());
        BigInteger result = node.bigIntegerValue();
        require(result.compareTo(low) >= 0 && result.compareTo(high) <= 0);
        return result;
    }
    static long number(JsonNode node, long low, long high) {
        return integer(node, BigInteger.valueOf(low), BigInteger.valueOf(high)).longValueExact();
    }
    static BigInteger nonnegative(JsonNode node, boolean positive) {
        require(node != null && node.isIntegralNumber());
        BigInteger result = node.bigIntegerValue(); require(result.signum() >= (positive ? 1 : 0)); return result;
    }
    static void require(boolean condition) {
        if (!condition) throw new IllegalArgumentException("private feast terminal contract malformed");
    }
}
