package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Calls the same Main continuation used after ordinary Start. Receipt DATA grants no entry or Native authority. */
final class RootInitialEntryContinuationTest {
    private static final Instant NOW=Instant.parse("2026-10-26T08:00:00Z");
    private static final ExactRef DATA=new ExactRef("software-entry-control-original",1,"a".repeat(64));

    @Test void repeatedAwaitingCallsOnlyTheOriginalResumeAndRetainsItsCommitUnknown() throws Exception {
        Instant deadline=NOW.plusSeconds(1);var clock=new MutableClock();
        var original=pending(deadline,"first map packet is not ready");
        var later=new GameplayEntryService.Awaiting(original.actual(),"later original map packet is not ready");
        var terminal=new GameplayEntryService.EntryCommitUnknown(original.actual(),"b".repeat(64),"original writer commit remains unknown");
        var starts=new AtomicInteger();var resumes=new AtomicInteger();var pauses=new ArrayList<Duration>();
        var actual=RootApplicationMain.startAndAwaitEntry(()->{starts.incrementAndGet();return original;},()->{
            int call=resumes.incrementAndGet();assertEquals(deadline,original.actual().command().deadline());
            assertEquals("original-start",original.actual().command().actionId());
            if(call==1)return later;
            if(call==2)return terminal;
            throw new AssertionError("terminal entry outcome must not reconcile or commit again");
        },deadline,clock,duration->{pauses.add(duration);clock.advance(duration);});
        assertSame(terminal,actual);assertEquals(1,starts.get());assertEquals(2,resumes.get());
        assertEquals(List.of(Duration.ofMillis(50),Duration.ofMillis(50)),pauses);
        assertFalse(original.actual().settled());
    }

    @Test void originalDeadlineReturnsTheLastAwaitingWithoutAnotherResumeOrLongerDeadline() throws Exception {
        Instant deadline=NOW.plusMillis(125);var clock=new MutableClock();
        var first=pending(deadline,"map not ready");var last=new GameplayEntryService.Awaiting(first.actual(),"original request still unresolved");
        var starts=new AtomicInteger();var resumes=new AtomicInteger();var pauses=new ArrayList<Duration>();
        var actual=RootApplicationMain.startAndAwaitEntry(()->{starts.incrementAndGet();return first;},()->{
            resumes.incrementAndGet();return last;
        },deadline,clock,duration->{pauses.add(duration);clock.advance(duration);});
        assertSame(last,actual);assertEquals(deadline,clock.instant());
        assertEquals(deadline,last.actual().command().deadline());assertSame(first.actual(),last.actual());
        assertEquals(1,starts.get());assertEquals(2,resumes.get());
        assertEquals(List.of(Duration.ofMillis(50),Duration.ofMillis(50),Duration.ofMillis(25)),pauses);
    }

    @Test void entryCommitUnknownStopsWithoutReconcilingOrRetryingTheCommit() throws Exception {
        Instant deadline=NOW.plusSeconds(1);var first=pending(deadline,"original");
        var terminal=new GameplayEntryService.EntryCommitUnknown(first.actual(),"c".repeat(64),"retain original commit uncertainty");
        var starts=new AtomicInteger();
        var actual=RootApplicationMain.startAndAwaitEntry(()->{starts.incrementAndGet();return terminal;},
                ()->{throw new AssertionError("commit UNKNOWN is not Awaiting native entry");},deadline,new MutableClock(),
                ignored->{throw new AssertionError("commit UNKNOWN must not wait");});
        assertSame(terminal,actual);assertEquals(1,starts.get());
    }

    @Test void settledNativeRejectionAndZeroDispatchAreNotPolledUntilTheDeadline() throws Exception {
        Instant deadline=NOW.plusSeconds(1);
        for(ActionReceipt receipt:rejections(deadline)) {
            assertTrue(receipt.settled());var terminal=new GameplayEntryService.Awaiting(receipt,"retain actual terminal refusal");
            var starts=new AtomicInteger();
            assertSame(terminal,RootApplicationMain.startAndAwaitEntry(()->{starts.incrementAndGet();return terminal;},
                    ()->{throw new AssertionError("settled original Start is immutable");},deadline,new MutableClock(),
                    ignored->{throw new AssertionError("settled refusal must not busy-wait");}));
            assertEquals(1,starts.get());
        }
    }

    @Test void anExpiredOriginalDeadlineDoesNotResumeAnAlreadyAttemptedStart() throws Exception {
        var original=pending(NOW,"original deadline expired");var starts=new AtomicInteger();
        assertSame(original,RootApplicationMain.startAndAwaitEntry(()->{starts.incrementAndGet();return original;},
                ()->{throw new AssertionError("deadline cannot be extended for reconciliation");},NOW,new MutableClock(),
                ignored->{throw new AssertionError("expired entry cannot sleep");}));
        assertEquals(1,starts.get());
    }

    @Test void aSourceOrReconciliationFailurePropagatesWithoutASecondStart() throws Exception {
        Instant deadline=NOW.plusSeconds(1);var original=pending(deadline,"loading");
        var sourceFailure=new IOException("actual retained source changed");var starts=new AtomicInteger();var resumes=new AtomicInteger();
        assertSame(sourceFailure,assertThrows(IOException.class,()->RootApplicationMain.startAndAwaitEntry(
                ()->{starts.incrementAndGet();return original;},()->{resumes.incrementAndGet();throw sourceFailure;},
                deadline,new MutableClock(),ignored->{})));
        assertEquals(1,starts.get());assertEquals(1,resumes.get());
    }

    @Test void aFailureDuringTheOriginalStartDoesNotScheduleAContinuation() throws Exception {
        var failure=new IOException("original source admission failed before entry was retained");var starts=new AtomicInteger();
        assertSame(failure,assertThrows(IOException.class,()->RootApplicationMain.startAndAwaitEntry(
                ()->{starts.incrementAndGet();throw failure;},()->{throw new AssertionError("no original entry to reconcile");},
                NOW.plusSeconds(1),new MutableClock(),ignored->{throw new AssertionError("no retained entry to wait for");})));
        assertEquals(1,starts.get());
    }

    @Test void interruptionRetainsTheInterruptAndNeverReconcilesOrRestarts() throws Exception {
        var original=pending(NOW.plusSeconds(1),"loading");var starts=new AtomicInteger();
        try {
            assertThrows(InterruptedException.class,()->RootApplicationMain.startAndAwaitEntry(
                    ()->{starts.incrementAndGet();return original;},()->{throw new AssertionError("interrupted entry cannot resume");},
                    NOW.plusSeconds(1),new MutableClock(),ignored->{throw new InterruptedException("actual startup interrupted");}));
            assertTrue(Thread.currentThread().isInterrupted());assertEquals(1,starts.get());
        } finally {Thread.interrupted();}
    }

    @Test void physicalCaptureReturnsTheSameActualUnknownWithoutSleepingOrReconciling() throws Exception {
        Instant deadline=NOW.plusSeconds(1);var original=pending(deadline,"retain actual unknown");
        var starts=new AtomicInteger();
        assertSame(original,RootApplicationMain.startAndAwaitPhysicalEntry(()->{starts.incrementAndGet();return original;},
                ()->{throw new AssertionError("capture UNKNOWN may not reconcile or resubmit");},deadline,new MutableClock(),
                ignored->{throw new AssertionError("observe UNKNOWN before its original deadline expires");}));
        assertEquals(1,starts.get());assertFalse(original.actual().settled());
        assertInstanceOf(ActionState.Unknown.class,original.actual().state());
    }

    @Test void physicalCapturePreservesSettledNativeRejectionAndItsOriginalReceipt() throws Exception {
        Instant deadline=NOW.plusSeconds(1);
        for(ActionReceipt receipt:rejections(deadline)) {
            var original=new GameplayEntryService.Awaiting(receipt,"actual immutable refusal");
            assertSame(original,RootApplicationMain.startAndAwaitPhysicalEntry(()->original,
                    ()->{throw new AssertionError("settled refusal is not a new UNKNOWN");},deadline,new MutableClock(),
                    ignored->{throw new AssertionError("settled refusal must not wait");}));
            assertSame(receipt,original.actual());assertTrue(receipt.settled());
            assertFalse(receipt.state() instanceof ActionState.Unknown);
        }
    }

    @Test void physicalCaptureRetainsEntryCommitUncertaintyWithoutRepeatingItsTransaction() throws Exception {
        Instant deadline=NOW.plusSeconds(1);var original=pending(deadline,"original receipt DATA");
        var commit=new GameplayEntryService.EntryCommitUnknown(original.actual(),"d".repeat(64),"retain original commit");
        assertSame(commit,RootApplicationMain.startAndAwaitPhysicalEntry(()->commit,
                ()->{throw new AssertionError("entry commit uncertainty cannot resume native Start");},deadline,new MutableClock(),
                ignored->{throw new AssertionError("entry commit uncertainty must not busy-wait");}));
        assertSame(original.actual(),commit.actual());
    }

    private static GameplayEntryService.Awaiting pending(Instant deadline,String reason) {
        var command=command(deadline);
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(),Optional.empty(),"retained original Start is unknown",List.of(DATA)));
        return new GameplayEntryService.Awaiting(receipt,reason);
    }
    private static ActionCommand command(Instant deadline) {
        var game=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE));
        var source=new G2Source("entry-control-fixture",NOW.toString(),"software-control-only",DATA);
        var menu=new FrontendIdentity(source.machineId(),game,"original-menu-session",BigInteger.ONE,42,
                new FrontendFrame.Menu(BigInteger.ONE),DATA,DATA);
        var expected=new FrontendGameplayExpectedPostcondition(menu,source,FrontendGameplayExpectedPostcondition.SCHEMA,
                "bookmark_1066","bookmark_rags_to_riches_duke_robert",1000,
                List.of(new ExpectedText(new FieldKey("selected_bookmark_key"),"bookmark_1066"),
                        new ExpectedText(new FieldKey("selected_character_name_key"),"bookmark_rags_to_riches_duke_robert"),
                        new ExpectedInteger(new FieldKey("date_raw"),BigInteger.valueOf(1000)),
                        new ExpectedBoolean(new FieldKey("map_ready"),true),new ExpectedBoolean(new FieldKey("paused"),true)));
        return new ActionCommand("original-start",new CommandOrigin.Frontend(menu),source,menu.frontendSessionId(),
                FrontendRulesRequests.Primitive.START_BOOKMARK.operation(),new OpportunityJson.Obj(Map.of()),
                new CommandExpectation.GameplayEntry(expected),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
    }
    private static List<ActionReceipt> rejections(Instant deadline) {
        var command=command(deadline);var origin=command.origin().requireFrontend();
        var guard=new GuardEvidence(new CommandOrigin.Frontend(origin),command.source(),command.sessionId(),BigInteger.ONE,
                command.operation(),DATA,DATA,"software-entry-control-guard",NOW,deadline);
        var prepared=new NativeRequest(command.operation().value(),Optional.empty(),new RawJson(new byte[]{'{','}'}));
        var attempt=new ActionState.Attempt("original-native-request",NOW,guard,prepared);
        var zero=new NativeActionPort.RejectedBeforeDispatch(attempt.requestId(),
                new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,0,"zero dispatch",Optional.empty()));
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),false,Optional.empty(),new RawJson(new byte[]{'{','}'}),new byte[]{0});
        return List.of(new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.RejectedBeforeDispatch(attempt,zero)),
                new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),
                        new ActionState.Settled(attempt,ack,new ActionState.Rejected(attempt.requestId(),"native rejection",DATA))));
    }
    private static final class MutableClock extends Clock {
        private Instant current=NOW;
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC fixture only");return this;}
        @Override public Instant instant(){return current;}
        void advance(Duration duration){assertFalse(duration.isNegative());assertFalse(duration.isZero());current=current.plus(duration);}
    }
}
