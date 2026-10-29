package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubBusinessStateRead;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootSessionAccess;
import org.xar.ck3.control.service.root.RootApplicationSession;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** One original public AUB query on the actual Root session; mutations require their own contracts. */
public final class RootMcpAubReads {
    public static final String PUBLIC_NAME = "ck3_query_aub_business_state_v1";
    private static final BigInteger MAXIMUM_PUBLIC_REVISION = new BigInteger("18446744073709551615");
    @FunctionalInterface public interface RegistrationResolver {
        AubBusinessStateRead.Registration requireCurrent(RootApplicationSession actualCurrent) throws IOException;
    }
    public sealed interface Revision permits Missing, NullValue, Value { Optional<BigInteger> expected(); }
    public record Missing() implements Revision { @Override public Optional<BigInteger> expected() { return Optional.empty(); } }
    public record NullValue() implements Revision { @Override public Optional<BigInteger> expected() { return Optional.empty(); } }
    public record Value(BigInteger value) implements Revision {
        public Value { Objects.requireNonNull(value); McpJson.require(value.signum() >= 0 && value.compareTo(MAXIMUM_PUBLIC_REVISION) <= 0, "exact uint64 public revision required"); }
        @Override public Optional<BigInteger> expected() { return Optional.of(value); }
    }
    public record Request(Revision revision) { public Request { Objects.requireNonNull(revision); } }
    private final RootSessionAccess sessions;
    private final RegistrationResolver registrations;
    private final Clock clock;
    private final Duration timeout;
    public RootMcpAubReads(RootSessionAccess actualSessions, RegistrationResolver actualRegistrations, Clock clock, Duration timeout) {
        sessions = Objects.requireNonNull(actualSessions); registrations = Objects.requireNonNull(actualRegistrations);
        this.clock = Objects.requireNonNull(clock); this.timeout = Objects.requireNonNull(timeout);
        McpJson.require(!timeout.isNegative() && !timeout.isZero() && timeout.compareTo(Duration.ofMinutes(2)) <= 0, "finite positive AUB timeout required");
    }
    public RawJson read(Request request) throws InterruptedException {
        Objects.requireNonNull(request);
        final PlanningReadResult<AubBusinessStateRead.State> result;
        try {
            result = sessions.withCurrent(root -> {
                AubBusinessStateRead.Registration current = Objects.requireNonNull(registrations.requireCurrent(root));
                return root.readCurrent(current.contract(), request.revision().expected(),
                        new OpportunityJson.Obj(java.util.Map.of()), clock.instant().plus(timeout));
            });
        } catch (IOException unavailable) { throw new UncheckedIOException("actual same-session AUB state unavailable", unavailable); }
        if (result instanceof PlanningReadResult.Known<AubBusinessStateRead.State> known) return AubBusinessStateRead.normalizedForPublic(known.value());
        var unavailable = (PlanningReadResult.Unavailable<AubBusinessStateRead.State>) result;
        throw new IllegalStateException("actual AUB source unavailable: " + unavailable.reason());
    }
    public List<McpExecutableDirectory.DirectBinding<?, ?>> actualMethods(ExactRef actualThisSource) {
        return List.of(new McpExecutableDirectory.DirectBinding<>(PUBLIC_NAME, PublicMcpBindings.Kind.DRIVER_DIRECT, Request.class, RawJson.class,
                this::read, call -> decode(call.arguments()), CallResult::fromBusinessJson,
                new PublicRoutes.Target(RootMcpAubReads.class.getName(), "read", actualThisSource)));
    }
    public static Request decode(Arguments arguments) {
        ObjectNode row = McpJson.object(McpJson.parse(arguments.objectOrEmpty().bytes()));
        McpJson.publicNumbers(row); McpJson.fields(row, Set.of("expected_revision"), Set.of());
        return new Request(revision(row));
    }
    public static Revision revision(ObjectNode row) {
        if(!row.has("expected_revision"))return new Missing();var value=row.get("expected_revision");if(value.isNull())return new NullValue();
        if(value.isTextual()) {
            McpJson.require(value.textValue().length()<=20&&value.textValue().matches("0|[1-9][0-9]*"),"expected_revision requires a canonical uint64 decimal string");
            return new Value(new BigInteger(value.textValue()));
        }
        McpJson.require(value.isIntegralNumber()&&value.bigIntegerValue().signum()>=0&&value.bigIntegerValue().compareTo(new BigInteger("9007199254740991"))<=0,
                "legacy numeric expected_revision must be an exact nonnegative safe integer");
        return new Value(value.bigIntegerValue());
    }
}
