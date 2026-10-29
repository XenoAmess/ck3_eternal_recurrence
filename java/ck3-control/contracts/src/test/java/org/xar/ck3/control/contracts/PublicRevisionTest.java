package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;

final class PublicRevisionTest {
    private static com.fasterxml.jackson.databind.JsonNode json(String value) { return StrictJson.parse(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
    @Test void publicCounterHasItsOwnDomainAndCanonicalDecimalRoundtrip() {
        for(BigInteger value:List.of(BigInteger.ZERO,BigInteger.ONE.shiftLeft(64),BigInteger.ONE.shiftLeft(100))) {
            PublicRevision counter=new PublicRevision(value);
            assertEquals(counter,PublicRevision.decimal(counter.canonical()));
            assertEquals(counter,PublicRevision.parse(json("\""+counter.canonical()+"\"")));
        }
        assertEquals(BigInteger.ZERO,PublicRevision.parse(json("0")).value());
        assertEquals(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER),PublicRevision.parse(json("9007199254740991")).value());
        assertEquals(4300,PublicRevision.decimal("9".repeat(4300)).canonical().length());
    }
    @Test void missingNullAndWrongTokenDomainsCannotBecomeZeroOrRoundedCounters() {
        assertThrows(IllegalArgumentException.class,()->PublicRevision.parse(null));
        assertThrows(IllegalArgumentException.class,()->new PublicRevision(null));
        assertThrows(IllegalArgumentException.class,()->new PublicRevision(BigInteger.valueOf(-1)));
        for(String raw:List.of("null","true","false","1.0","-1","9007199254740992","\"01\"","\"+1\"","\"-1\"","\"1\n\"","[]","{}"))
            assertThrows(IllegalArgumentException.class,()->PublicRevision.parse(json(raw)),raw);
        assertThrows(IllegalArgumentException.class,()->PublicRevision.decimal("9".repeat(4301)));
        assertThrows(IllegalArgumentException.class,()->new CrossJsDecimalUInt64(BigInteger.ONE.shiftLeft(64).toString()));
    }

    @Test void decimalPatternKeepsAbsoluteEndAndCanonicalAsciiDigits() {
        var pattern=java.util.regex.Pattern.compile(PublicRevision.DECIMAL_PATTERN);
        for(String raw:List.of("0","1",BigInteger.ONE.shiftLeft(100).toString(),"9".repeat(4300))) {
            assertTrue(pattern.matcher(raw).find(),raw);
            assertEquals(raw,PublicRevision.decimal(raw).canonical());
        }
        for(String raw:List.of("","00","01"," 0","0 ","\t0","0\t","0\n","0\r\n","0\r",
                "1\n","1\r\n","1\r","\n1","-1","+1","1.0","\u0661","\uff11","1\u00a0","1\u2028")) {
            assertFalse(pattern.matcher(raw).find(),raw);
            assertThrows(IllegalArgumentException.class,()->PublicRevision.decimal(raw),raw);
        }
    }
}
