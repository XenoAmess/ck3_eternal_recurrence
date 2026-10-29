package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;

/** Production ordinary completion control flow only. No fabricated Core, writer, READ token or Root qualification.
 * Actual failed-READ producer/publisher and complete Root consumer tests remain separately required and NOT_RUN. */
final class RootReadPublicationCompletionFailureTest {
    @Test void workFailurePublishesAfterWorkUnwindsAndPreservesItsOriginalThrowable() {
        var frozen=new AtomicBoolean();var calls=new AtomicInteger();var original=new IOException("actual work failed");
        IOException received=assertThrows(IOException.class,()->RootReadPublicationCompletion.finishOriginalWork(()->{
            frozen.set(true);try{throw original;}finally{frozen.set(false);}
        },()->{assertFalse(frozen.get());calls.incrementAndGet();return Optional.empty();},()->false));
        assertSame(original,received);assertEquals(1,calls.get());assertEquals(0,received.getSuppressed().length);
        var interrupted=new InterruptedException("work interrupted");
        assertSame(interrupted,assertThrows(InterruptedException.class,()->RootReadPublicationCompletion.finishOriginalWork(()->{throw interrupted;},Optional::empty,()->false)));
        var error=new AssertionError("work failed with Error");
        assertSame(error,assertThrows(AssertionError.class,()->RootReadPublicationCompletion.finishOriginalWork(()->{throw error;},Optional::empty,()->false)));
    }
    @Test void failedPublicationIsSuppressedOnOriginalWorkFailureWithoutReplacingIt() {
        var original=new IllegalStateException("work failed");var publication=new IOException("publisher failed");var calls=new AtomicInteger();
        var received=assertThrows(IllegalStateException.class,()->RootReadPublicationCompletion.finishOriginalWork(()->{throw original;},()->{
            calls.incrementAndGet();throw publication;
        },()->false));
        assertSame(original,received);assertArrayEquals(new Throwable[]{publication},received.getSuppressed());assertEquals(1,calls.get());
    }
    @Test void typedPhysicalReadIsDistinctOnlyAfterTheOriginalPublicationReturns() {
        var original=new IOException("the retained Native READ response was not returned");
        var physical=org.xar.ck3.control.application.planning.PlanningReadFailure.physical(original);
        var calls=new AtomicInteger();
        var received=assertThrows(org.xar.ck3.control.application.planning.PlanningReadFailure.class,
                ()->RootReadPublicationCompletion.finishOriginalWork(()->{throw physical;},()->{calls.incrementAndGet();return Optional.empty();},()->false));
        assertTrue(org.xar.ck3.control.application.planning.PlanningReadFailure.hasCompletedPublication(received));
        assertTrue(received.toString().contains(original.toString()));
        assertSame(physical,received.getCause());assertSame(original,physical.getCause());assertEquals(1,calls.get());
        var wrapped=new UncheckedIOException("actual Root planning-read authority unavailable",physical);
        var wrappedReceived=assertThrows(org.xar.ck3.control.application.planning.PlanningReadFailure.class,
                ()->RootReadPublicationCompletion.finishOriginalWork(()->{throw wrapped;},Optional::empty,()->false));
        assertTrue(org.xar.ck3.control.application.planning.PlanningReadFailure.hasCompletedPublication(wrappedReceived));
        assertTrue(wrappedReceived.toString().contains(original.toString()));
        assertSame(wrapped,wrappedReceived.getCause());
    }
    @Test void physicalReadWithSuppressedWriterFailureNeverClaimsCompletedPublication() {
        var original=org.xar.ck3.control.application.planning.PlanningReadFailure.physical(new IOException("physical READ failed"));
        var writer=new IOException("actual read publication writer completion lost");var calls=new AtomicInteger();
        var received=assertThrows(IOException.class,()->RootReadPublicationCompletion.finishOriginalWork(()->{throw original;},()->{
            calls.incrementAndGet();throw writer;
        },()->false));
        assertSame(original,received);assertArrayEquals(new Throwable[]{writer},received.getSuppressed());assertEquals(1,calls.get());
        assertFalse(org.xar.ck3.control.application.planning.PlanningReadFailure.hasCompletedPublication(received));
        assertTrue(org.xar.ck3.control.application.planning.PlanningReadFailure.afterPublication(received).isEmpty());
    }
    @Test void alreadyFailedPhysicalReadPublicationDoesNotRetryOrClaimCompletion() {
        var original=org.xar.ck3.control.application.planning.PlanningReadFailure.physical(new IOException("original physical READ failed"));
        var received=assertThrows(IOException.class,()->RootReadPublicationCompletion.finishOriginalWork(()->{throw original;},()->{
            throw new AssertionError("the same failed publication must not be retried");
        },()->true));
        assertSame(original,received);assertFalse(org.xar.ck3.control.application.planning.PlanningReadFailure.hasCompletedPublication(received));
    }
    @Test void transportWrapperSuppressedFailureSurvivesPhysicalProvenanceAndPreventsDowngrade() {
        var nativeFailure=new IOException("Native response deadline expired");
        var transport=new UncheckedIOException(nativeFailure);var writer=new IOException("suppressed original writer failure");
        transport.addSuppressed(writer);
        var physical=org.xar.ck3.control.application.planning.PlanningReadFailure.physical(transport);
        var received=assertThrows(IOException.class,()->RootReadPublicationCompletion.finishOriginalWork(()->{throw physical;},Optional::empty,()->false));
        assertSame(physical,received);assertSame(transport,physical.getCause());assertSame(nativeFailure,transport.getCause());
        assertArrayEquals(new Throwable[]{writer},transport.getSuppressed());
        assertFalse(org.xar.ck3.control.application.planning.PlanningReadFailure.hasCompletedPublication(received));
    }
    @Test void normalOrAlreadyFailedPublicationNeverBlindlyRetries() {
        var publication=new IOException("normal flush failure");var calls=new AtomicInteger();
        assertSame(publication,assertThrows(IOException.class,()->RootReadPublicationCompletion.finishOriginalWork(()->"result",()->{
            calls.incrementAndGet();throw publication;
        },()->false)));assertEquals(1,calls.get());
        var seenFailure=new AtomicBoolean();var original=new UncheckedIOException(publication);calls.set(0);
        assertSame(original,assertThrows(UncheckedIOException.class,()->RootReadPublicationCompletion.finishOriginalWork(()->{
            calls.incrementAndGet();seenFailure.set(true);throw original;
        },()->{throw new AssertionError("failed in-round flush cannot be attempted twice");},seenFailure::get)));
        assertEquals(1,calls.get());
    }
}
