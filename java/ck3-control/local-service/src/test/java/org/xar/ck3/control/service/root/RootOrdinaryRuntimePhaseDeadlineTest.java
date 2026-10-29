package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Real ordinary-assembly operation boundary and failure propagation only; no physical Game qualification. */
final class RootOrdinaryRuntimePhaseDeadlineTest {
    private static final Instant BASE=Instant.parse("2026-10-29T00:00:00Z");
    private static final Duration TIMEOUT=Duration.ofSeconds(60);

    @Test void recoveryTimeAndCatalogTimeDoNotConsumeTheNextOperationsOwnBudget()throws Exception {
        MutableClock clock=new MutableClock(BASE);
        Instant oldSharedDeadline=clock.instant().plus(TIMEOUT);
        clock.advance(Duration.ofSeconds(30)); // Earlier recovery has consumed part, not all, of its operation budget.
        List<Instant> deadlines=new ArrayList<>();
        Instant catalog=RootOrdinaryRuntimeAssembly.runOperationPhase(clock,TIMEOUT,deadline->{
            deadlines.add(deadline);assertEquals(BASE.plusSeconds(90),deadline);
            requireCurrentTime(clock,deadline);
            clock.advance(Duration.ofSeconds(40));
            assertThrows(ContractViolationException.class,()->requireCurrentTime(clock,oldSharedDeadline));
            requireCurrentTime(clock,deadline); // The catalog's own forty-second operation remains within sixty seconds.
            return deadline;
        });
        Instant configured=RootOrdinaryRuntimeAssembly.runOperationPhase(clock,TIMEOUT,deadline->{
            deadlines.add(deadline);assertEquals(BASE.plusSeconds(130),deadline);
            clock.advance(Duration.ofSeconds(40));
            assertThrows(ContractViolationException.class,()->requireCurrentTime(clock,catalog));
            requireCurrentTime(clock,deadline);
            return deadline;
        });
        Instant installed=RootOrdinaryRuntimeAssembly.runOperationPhase(clock,TIMEOUT,deadline->{
            deadlines.add(deadline);assertEquals(BASE.plusSeconds(170),deadline);
            clock.advance(Duration.ofSeconds(1));requireCurrentTime(clock,deadline);return deadline;
        });
        assertEquals(List.of(BASE.plusSeconds(90),BASE.plusSeconds(130),BASE.plusSeconds(170)),deadlines);
        assertEquals(BASE.plusSeconds(111),clock.instant());assertTrue(configured.isBefore(installed));
    }

    @Test void anOperationThatActuallyExpiresStillRefusesAndDoesNotEnterTheFollowingOperation() {
        for(long spent:List.of(60L,61L)) {
            MutableClock clock=new MutableClock(BASE.plusSeconds(30));
            AtomicInteger originalCalls=new AtomicInteger(),followingCalls=new AtomicInteger();
            ContractViolationException failure=assertThrows(ContractViolationException.class,()->{
                RootOrdinaryRuntimeAssembly.runOperationPhase(clock,TIMEOUT,deadline->{
                    originalCalls.incrementAndGet();assertEquals(BASE.plusSeconds(90),deadline);
                    clock.advance(Duration.ofSeconds(spent));requireCurrentTime(clock,deadline);return "unreachable";
                });
                RootOrdinaryRuntimeAssembly.runOperationPhase(clock,TIMEOUT,deadline->{followingCalls.incrementAndGet();return "unreachable";});
            });
            assertEquals("runtime context deadline expired",failure.getMessage());
            assertEquals(1,originalCalls.get());assertEquals(0,followingCalls.get());
        }
    }

    @Test void openingCoreBeyondThePriorBudgetDoesNotExpireTheNextPhysicalOperation()throws Exception {
        MutableClock clock=new MutableClock(BASE);Instant earlierDeadline=clock.instant().plus(TIMEOUT);
        clock.advance(Duration.ofSeconds(125));
        assertThrows(ContractViolationException.class,()->requireCurrentTime(clock,earlierDeadline));
        Instant actualDeadline=RootOrdinaryRuntimeAssembly.runOperationPhase(clock,TIMEOUT,deadline->{
            assertEquals(BASE.plusSeconds(185),deadline);requireCurrentTime(clock,deadline);
            clock.advance(Duration.ofSeconds(40));requireCurrentTime(clock,deadline);return deadline;
        });
        assertEquals(BASE.plusSeconds(185),actualDeadline);assertEquals(BASE.plusSeconds(165),clock.instant());
    }

    @Test void originalIoAndInterruptFailuresPassThroughWithoutRetryOrASecondPhase() {
        MutableClock clock=new MutableClock(BASE);
        AtomicInteger calls=new AtomicInteger();IOException io=new IOException("actual phase publication failed");
        assertSame(io,assertThrows(IOException.class,()->RootOrdinaryRuntimeAssembly.runOperationPhase(clock,TIMEOUT,deadline->{
            calls.incrementAndGet();clock.advance(Duration.ofSeconds(61));throw io;
        })));
        InterruptedException interrupted=new InterruptedException("actual phase interrupted");
        assertSame(interrupted,assertThrows(InterruptedException.class,()->RootOrdinaryRuntimeAssembly.runOperationPhase(clock,TIMEOUT,deadline->{
            calls.incrementAndGet();throw interrupted;
        })));
        assertEquals(2,calls.get());
    }

    /** The existing RootRuntimeContext time condition uses StrictJson and strict isBefore; no Game is fabricated. */
    private static void requireCurrentTime(Clock clock,Instant deadline) {
        StrictJson.require(clock.instant().isBefore(deadline),"runtime context deadline expired");
    }
    private static final class MutableClock extends Clock {
        private final AtomicReference<Instant> now;private final ZoneId zone;
        MutableClock(Instant initial){this(new AtomicReference<>(Objects.requireNonNull(initial)),ZoneOffset.UTC);}
        private MutableClock(AtomicReference<Instant> now,ZoneId zone){this.now=now;this.zone=Objects.requireNonNull(zone);}
        void advance(Duration duration){now.updateAndGet(value->value.plus(duration));}
        @Override public Instant instant(){return now.get();}
        @Override public ZoneId getZone(){return zone;}
        @Override public Clock withZone(ZoneId requested){return new MutableClock(now,requested);}
    }
}
