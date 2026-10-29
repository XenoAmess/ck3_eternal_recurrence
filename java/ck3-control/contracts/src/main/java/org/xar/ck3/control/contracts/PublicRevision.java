package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;

/** Public semantic counter, independent of native uint64 identity and native revision. */
public record PublicRevision(BigInteger value) {
    public static final int MAX_DECIMAL_CHARACTERS=4300;
    public static final String DECIMAL_PATTERN="^(?:0|[1-9][0-9]*)(?![\\s\\S])";
    public PublicRevision {
        StrictJson.require(value!=null && value.signum()>=0,"non-negative public revision required");
    }
    /** Canonical decimal text is the wire; numeric compatibility is limited to safe integers. */
    public static PublicRevision parse(JsonNode raw) {
        StrictJson.require(raw!=null,"public revision is missing");
        StrictJson.require(!raw.isNull(),"public revision is null");
        if(raw.isTextual())return decimal(raw.textValue());
        StrictJson.require(raw.isIntegralNumber(),"public revision must be an integer or canonical decimal text");
        BigInteger value=raw.bigIntegerValue();
        StrictJson.require(value.signum()>=0 && value.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,
                "public numeric revision must be a non-negative safe integer; use decimal text otherwise");
        return new PublicRevision(value);
    }
    public static PublicRevision decimal(String raw) {
        StrictJson.require(raw!=null && raw.length()<=MAX_DECIMAL_CHARACTERS && raw.matches("0|[1-9][0-9]*"),
                "canonical non-negative public revision decimal text required");
        return new PublicRevision(new BigInteger(raw));
    }
    public String canonical() {
        String raw=value.toString();
        StrictJson.require(raw.length()<=MAX_DECIMAL_CHARACTERS,"public revision exceeds the decimal wire limit");
        return raw;
    }
}
