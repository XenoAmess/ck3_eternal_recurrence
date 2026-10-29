package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.time.Clock;
import java.time.DateTimeException;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Original WAIT arguments with the same exact public revision string profile as snapshot DATA. */
public final class WaitForChangePublicCodec {
    private static final Duration DEFAULT_TIMEOUT=Duration.ofSeconds(10);
    private static final BigInteger NANOS_PER_SECOND=BigInteger.valueOf(1000000000);
    private WaitForChangePublicCodec() { }

    public record Request(BigInteger afterRevision,Optional<Duration> timeout) {
        public Request {
            Objects.requireNonNull(afterRevision);Objects.requireNonNull(timeout);
            McpJson.require(afterRevision.signum()>=0 && afterRevision.toString().length()<=4300,"bounded nonnegative public revision required");
            timeout.ifPresent(WaitForChangePublicCodec::positive);
        }
        public Duration effectiveTimeout(){return timeout.orElse(DEFAULT_TIMEOUT);}
    }
    /** A wait deadline and a separate actual final-capture allowance; no requested wait is silently clipped. */
    public record Deadlines(Instant waitUntil,Instant captureUntil) {
        public Deadlines {
            Objects.requireNonNull(waitUntil);Objects.requireNonNull(captureUntil);
            McpJson.require(captureUntil.isAfter(waitUntil),"actual final snapshot capture allowance required");
        }
    }
    public static Request decode(PublicBindings.Arguments arguments) {
        Objects.requireNonNull(arguments);
        McpJson.require(arguments instanceof PublicBindings.Value,"WAIT requires its named object; missing and null are unsupported distinct inputs");
        var row=McpJson.object(McpJson.parse(((PublicBindings.Value)arguments).original().bytes()));
        McpJson.fields(row,Set.of("after_revision","timeout_seconds"),Set.of("after_revision"));
        McpJson.publicNumbers(row);
        String revision=McpJson.text(row.get("after_revision"));
        McpJson.require(revision.length()<=4300 && revision.matches("0|[1-9][0-9]*"),"canonical public after_revision decimal string required");
        Optional<Duration> timeout=Optional.empty();
        if(row.has("timeout_seconds"))timeout=Optional.of(seconds(row.get("timeout_seconds")));
        return new Request(new BigInteger(revision),timeout);
    }
    public static RawJson encode(Request request) {
        Objects.requireNonNull(request);
        var row=McpJson.object().put("after_revision",request.afterRevision().toString());
        request.timeout().ifPresent(timeout->row.put("timeout_seconds",BigDecimal.valueOf(timeout.getSeconds()).add(BigDecimal.valueOf(timeout.getNano(),9))));
        McpJson.publicNumbers(row);
        return new RawJson(McpJson.encode(row));
    }
    public static Deadlines deadlines(Request request,Clock clock,Duration captureAllowance) {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);positive(captureAllowance);
        try {
            Instant wait=clock.instant().plus(request.effectiveTimeout());
            return new Deadlines(wait,wait.plus(captureAllowance));
        } catch(DateTimeException|ArithmeticException failure) {
            throw new IllegalArgumentException("requested WAIT exceeds representable absolute runtime deadlines",failure);
        }
    }
    private static Duration seconds(JsonNode token) {
        McpJson.require(token!=null && token.isNumber() && Double.isFinite(token.doubleValue()),"timeout_seconds must be a finite positive number");
        try {
            BigInteger nanos=token.decimalValue().movePointRight(9).toBigIntegerExact();
            BigInteger[] parts=nanos.divideAndRemainder(NANOS_PER_SECOND);
            Duration result=Duration.ofSeconds(parts[0].longValueExact(),parts[1].longValueExact());positive(result);return result;
        } catch(ArithmeticException failure) {
            throw new IllegalArgumentException("timeout_seconds must be exactly representable as a positive Duration",failure);
        }
    }
    private static void positive(Duration duration) {
        Objects.requireNonNull(duration);McpJson.require(!duration.isZero() && !duration.isNegative(),"positive actual WAIT duration required");
    }
}
