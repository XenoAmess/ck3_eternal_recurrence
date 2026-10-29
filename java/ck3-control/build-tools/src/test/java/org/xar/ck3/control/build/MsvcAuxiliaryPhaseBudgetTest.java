package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Controlled timing of the actual shared reducer after real configure02 exhausted cleanup while rechecking member two. */
final class MsvcAuxiliaryPhaseBudgetTest {
    private static final long SECOND = 1_000_000_000L;
    private static final class Boundary implements MsvcAuxiliaryPolicy.Backend {
        final MsvcAuxiliaryPolicy.ExecutionBinding binding = MsvcAuxiliaryPolicyTest.execution();
        final List<Long> terminated = new ArrayList<>();
        final HashMap<Long,Integer> observations = new HashMap<>();
        long now, firstMutation = -1, drainDelay; int completeChecksBeforeMutation, checksAfterMutation, closes;
        boolean lingering, expensiveAfterMutationGuard;
        MsvcAuxiliaryPolicy.Outcome finish(long commandSeconds) {
            return finish(commandSeconds, 60);
        }
        MsvcAuxiliaryPolicy.Outcome finish(long commandSeconds, long leaseSeconds) {
            Instant base = Instant.parse("2026-10-26T00:00:00Z");
            var budget = new MsvcAuxiliaryPolicy.Budget(commandSeconds * SECOND, base.plusSeconds(leaseSeconds),
                    () -> now, () -> base.plusNanos(now), millis -> now += millis * 1_000_000L);
            return MsvcAuxiliaryPolicy.finish(this, binding, budget, () -> {
                if(firstMutation<0&&now>=SECOND)completeChecksBeforeMutation++;
                if(firstMutation>=0) {
                    checksAfterMutation++;
                    if(expensiveAfterMutationGuard)now+=6*SECOND;
                }
            });
        }
        @Override public MsvcAuxiliaryPolicy.Root root() {
            return new MsvcAuxiliaryPolicy.Root(new WindowsJobProcess.ProcessIdentity(17,
                    MsvcAuxiliaryPolicyTest.BIRTH,binding.rootExecutable().path()),0,0);
        }
        private boolean drained() { return terminated.size()==2&&!lingering&&now-firstMutation>=drainDelay; }
        @Override public int active() { return drained()?0:terminated.size()==2?2:2-terminated.size(); }
        @Override public List<Long> members() { return drained()?List.of():List.of(41L,42L); }
        @Override public MsvcAuxiliaryPolicy.Member retain(long pid) {
            var image=pid==41?binding.toolchain().vctip():binding.toolchain().mspdbsrv();
            return new MsvcAuxiliaryPolicy.Member() {
                boolean killed;
                @Override public MsvcAuxiliaryPolicy.MemberObservation observe() {
                    int count=observations.merge(pid,1,Integer::sum);
                    if(count==2)now+=3*SECOND;
                    return new MsvcAuxiliaryPolicy.MemberObservation(new WindowsJobProcess.ProcessIdentity(
                            pid,MsvcAuxiliaryPolicyTest.BIRTH,image.canonicalPath()),image,true,258);
                }
                @Override public MsvcAuxiliaryPolicy.Termination terminate74() {
                    if(firstMutation<0)firstMutation=now;
                    terminated.add(pid);killed=true;
                    return new MsvcAuxiliaryPolicy.Termination(true,null,null);
                }
                @Override public long waitZero() { return killed?0:258; }
                @Override public long exitCode() { return killed?74:259; }
                @Override public void close() { closes++; }
            };
        }
    }

    @Test void sourceAndImageChecksBeforeMutationCanUseTheRemainingOriginalCommandBudget() {
        var boundary=new Boundary();var result=boundary.finish(20);
        assertTrue(result.completed(),result.error());
        assertEquals(MsvcAuxiliaryPolicy.State.FORCED_AUXILIARY_CLEANUP,result.state());
        assertEquals(List.of(41L,42L),boundary.terminated);
        assertEquals(2,result.forcedCleanup().size());
        assertEquals(7*SECOND,boundary.firstMutation);
        assertEquals(Integer.valueOf(2),boundary.observations.get(41L));
        assertEquals(Integer.valueOf(2),boundary.observations.get(42L));
        assertTrue(boundary.completeChecksBeforeMutation>=4,"Both complete source checks for both members must precede mutation");
        assertEquals(2,boundary.closes);
        for(var member:result.forcedCleanup()) {
            assertEquals(0L,member.actualWaitZero().longValue());
            assertEquals(74L,member.actualExitCode().longValue());
        }
    }

    @Test void actualTerminationAndDrainStillHaveOnlyFiveSeconds() {
        var boundary=new Boundary();boundary.lingering=true;var result=boundary.finish(20);
        assertFalse(result.completed());
        assertEquals(List.of(41L,42L),boundary.terminated);
        assertEquals(5*SECOND,boundary.now-boundary.firstMutation);
        assertEquals(2,result.forcedCleanup().size());
        assertNull(result.forcedCleanup().get(0).actualExitCode());
        assertNull(result.forcedCleanup().get(1).actualExitCode());
        assertEquals(2,boundary.closes);
    }

    @Test void acknowledgedTerminationDrainObservesJobZeroAndActual74WithoutRepeatingTheExpensiveSourceGuard() {
        var boundary=new Boundary();boundary.drainDelay=250_000_000L;boundary.expensiveAfterMutationGuard=true;
        var result=boundary.finish(20);
        assertTrue(result.completed(),result.error());
        assertEquals(MsvcAuxiliaryPolicy.State.FORCED_AUXILIARY_CLEANUP,result.state());
        assertTrue(boundary.completeChecksBeforeMutation>=4,"Complete source checks for both exact members still precede termination");
        assertEquals(0,boundary.checksAfterMutation,"The finite post-ACK drain must not repeat the full source/output walk");
        assertEquals(250_000_000L,boundary.now-boundary.firstMutation);
        assertEquals(0,result.ownedActiveAfter().intValue());assertEquals(2,boundary.closes);
        for(var member:result.forcedCleanup()) {
            assertTrue(member.termination().acknowledged());
            assertEquals(0L,member.actualWaitZero().longValue());
            assertEquals(74L,member.actualExitCode().longValue());
        }
    }

    @Test void postAckDrainCannotRenewTheOriginalCommandOrLeaseDeadline() {
        for(boolean commandExpires:List.of(false,true)) {
            var boundary=new Boundary();boundary.drainDelay=2*SECOND;boundary.expensiveAfterMutationGuard=true;
            var result=boundary.finish(commandExpires?8:20,commandExpires?60:8);
            assertFalse(result.completed());
            assertEquals(List.of(41L,42L),boundary.terminated);
            assertEquals(SECOND,boundary.now-boundary.firstMutation);
            assertEquals(0,boundary.checksAfterMutation);
            assertEquals(2,result.forcedCleanup().size());assertEquals(2,boundary.closes);
            for(var member:result.forcedCleanup()) {
                assertTrue(member.termination().acknowledged());
                assertNull(member.actualWaitZero());assertNull(member.actualExitCode());
            }
        }
    }

    @Test void expensiveChecksCannotRenewTheOriginalCommandDeadlineOrPartiallyMutate() {
        var boundary=new Boundary();var result=boundary.finish(5);
        assertFalse(result.completed());
        assertTrue(boundary.terminated.isEmpty());
        assertTrue(result.forcedCleanup().isEmpty());
        assertEquals(-1,boundary.firstMutation);
        assertEquals(2,boundary.closes);
    }
}
