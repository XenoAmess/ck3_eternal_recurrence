package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Controlled boundary cases execute the actual shared policy reducer, including the observed root0/live-vctip failure shape. */
final class MsvcAuxiliaryPolicyTest {
    static final String BIRTH = "134373430414528345", FILE_ID = "170141183460469231731687303715884105729";
    static final String SHA = "a".repeat(64);
    static MsvcAuxiliaryPolicy.Image image(String name, String id) {
        return new MsvcAuxiliaryPolicy.Image(Path.of("D:/msvc-test",name).toAbsolutePath().toString(), "18446744073709551615", id, 1024, SHA);
    }
    static MsvcAuxiliaryPolicy.Binding binding() {
        return new MsvcAuxiliaryPolicy.Binding(MsvcAuxiliaryPolicy.SCHEMA,image("cl.exe","1"),image("vctip.exe",FILE_ID),image("mspdbsrv.exe","3"));
    }
    static MsvcAuxiliaryPolicy.ExecutionBinding execution() {
        var tools=binding();return new MsvcAuxiliaryPolicy.ExecutionBinding("xar.exact-msvc-owned-execution/v1",tools,
                new ControlBuild.FileRef(tools.compiler().canonicalPath(),tools.compiler().bytes(),tools.compiler().sha256()));
    }
    private static final class Boundary implements MsvcAuxiliaryPolicy.Backend {
        long now; long rootWait; long rootCode; int closes; int terminations; int memberCalls;
        boolean unknownSecond, drift, outside, newMember, lingering, closeFailure, empty, unknownTermination;
        final List<Long> opened = new ArrayList<>(); final List<Long> terminated = new ArrayList<>();
        MsvcAuxiliaryPolicy.ExecutionBinding binding = execution();
        MsvcAuxiliaryPolicy.Budget budget(long nanos) {
            return new MsvcAuxiliaryPolicy.Budget(nanos,Instant.parse("2026-10-24T20:30:00Z"),()->now,
                    ()->Instant.parse("2026-10-24T19:30:00Z").plusNanos(now),millis->now+=millis*1_000_000L);
        }
        @Override public MsvcAuxiliaryPolicy.Root root() {
            return new MsvcAuxiliaryPolicy.Root(new WindowsJobProcess.ProcessIdentity(17,"134373430403521273",binding.rootExecutable().path()),rootWait,rootCode);
        }
        @Override public int active() { return empty?0:terminations>0&&!lingering&&!newMember?0:unknownSecond?2:1; }
        @Override public List<Long> members() {
            memberCalls++;
            if(empty || terminations>0&&!lingering&&!newMember)return List.of();
            if(terminations>0&&newMember)return List.of(99L);
            return unknownSecond?List.of(41L,42L):List.of(41L);
        }
        @Override public MsvcAuxiliaryPolicy.Member retain(long pid) {
            opened.add(pid);
            return new MsvcAuxiliaryPolicy.Member() {
                int observations; boolean killed;
                @Override public MsvcAuxiliaryPolicy.MemberObservation observe() {
                    observations++;
                    var expected=pid==42?image("unknown.exe","22"):binding.toolchain().vctip();
                    String birth=drift&&observations>1?"134373430414528346":BIRTH;
                    return new MsvcAuxiliaryPolicy.MemberObservation(new WindowsJobProcess.ProcessIdentity(pid,birth,expected.canonicalPath()),expected,!outside,258);
                }
                @Override public MsvcAuxiliaryPolicy.Termination terminate74() {
                    terminations++;terminated.add(pid);
                    if(unknownTermination)return new MsvcAuxiliaryPolicy.Termination(false,5L,"controlled native submit unknown");
                    killed=true;return new MsvcAuxiliaryPolicy.Termination(true,null,null);
                }
                @Override public long waitZero() { return killed?0:258; }
                @Override public long exitCode() { return killed?74:259; }
                @Override public void close() throws IOException { closes++;if(closeFailure)throw new IOException("actual controlled close failure"); }
            };
        }
        MsvcAuxiliaryPolicy.Outcome finish() { return MsvcAuxiliaryPolicy.finish(this,binding,budget(10_000_000_000L),()->{}); }
    }
    @Test void rootZeroAndLiveExactVctipAreCleanedByOriginalHandleAfterGraceAndRecordedAsForced() {
        Boundary boundary=new Boundary();var result=boundary.finish();
        assertEquals(MsvcAuxiliaryPolicy.State.FORCED_AUXILIARY_CLEANUP,result.state());assertTrue(result.completed());
        assertEquals(0,result.originalRoot().exitCode());assertEquals(1,boundary.terminations);assertEquals(1,boundary.closes);
        assertEquals(List.of(41L),boundary.opened);assertEquals(List.of(41L),boundary.terminated);
        assertEquals(74L,result.forcedCleanup().getFirst().actualExitCode().longValue());assertFalse(result.failureJobTerminationRequested());
        assertTrue(boundary.now>=1_000_000_000L);assertTrue(boundary.now<6_000_000_000L);
    }
    @Test void completeSetIsVerifiedBeforeTheFirstKillSoUnknownSecondMemberPreventsAllCleanup() {
        Boundary boundary=new Boundary();boundary.unknownSecond=true;var result=boundary.finish();
        assertEquals(MsvcAuxiliaryPolicy.State.FAILED,result.state());assertEquals(0,boundary.terminations);
        assertEquals(List.of(41L,42L),boundary.opened);assertEquals(2,boundary.closes);assertTrue(result.forcedCleanup().isEmpty());
    }
    @Test void signalledRoot259IsNotSuccessfulAndNoMemberHandleIsOpened() {
        Boundary boundary=new Boundary();boundary.rootCode=259;var result=boundary.finish();
        assertEquals(MsvcAuxiliaryPolicy.State.FAILED,result.state());assertEquals(259,result.originalRoot().exitCode());
        assertTrue(boundary.opened.isEmpty());assertEquals(0,boundary.terminations);
    }
    @Test void rootTimeoutNeverBecomesExitedFromZeroExitCode() {
        Boundary boundary=new Boundary();boundary.rootWait=258;var result=boundary.finish();
        assertFalse(result.completed());assertEquals(258,result.originalRoot().waitZero());assertTrue(boundary.opened.isEmpty());
        Boundary build=new Boundary();build.binding=new MsvcAuxiliaryPolicy.ExecutionBinding("xar.exact-msvc-owned-execution/v1",
                binding(),new ControlBuild.FileRef(Path.of("D:/msvc-test/cmake.exe").toAbsolutePath().toString(),1024,SHA));
        assertEquals(MsvcAuxiliaryPolicy.State.FORCED_AUXILIARY_CLEANUP,build.finish().state());
    }
    @Test void retainedBirthDriftOrLostJobMembershipPreventsHandleTermination() {
        for(boolean drift:List.of(false,true)) {
            Boundary boundary=new Boundary();boundary.drift=drift;boundary.outside=!drift;
            assertEquals(MsvcAuxiliaryPolicy.State.FAILED,boundary.finish().state());
            assertEquals(0,boundary.terminations);assertEquals(1,boundary.closes);
        }
    }
    @Test void deadlineIsNotRenewedForOneSecondGraceOrFiveSecondCleanup() {
        Boundary boundary=new Boundary();
        var result=MsvcAuxiliaryPolicy.finish(boundary,boundary.binding,boundary.budget(100_000_000L),()->{});
        assertFalse(result.completed());assertEquals(100_000_000L,boundary.now);assertEquals(0,boundary.terminations);
        Boundary lingering=new Boundary();lingering.lingering=true;
        var second=MsvcAuxiliaryPolicy.finish(lingering,lingering.binding,lingering.budget(1_100_000_000L),()->{});
        assertFalse(second.completed());assertEquals(1_100_000_000L,lingering.now);
        assertEquals(1,second.forcedCleanup().size());assertNull(second.forcedCleanup().getFirst().actualExitCode());
    }
    @Test void newMemberAfterExactCleanupIsUnknownAndNeverGetsBlindlyOpenedOrKilled() {
        Boundary boundary=new Boundary();boundary.newMember=true;var result=boundary.finish();
        assertFalse(result.completed());assertEquals(1,boundary.terminations);assertEquals(List.of(41L),boundary.opened);
        assertEquals(1,result.forcedCleanup().size());assertNull(result.forcedCleanup().getFirst().actualExitCode());
    }
    @Test void emptyActualJobNeedsNoForcedCleanupOrLiveGuard() {
        Boundary boundary=new Boundary();boundary.empty=true;
        var result=MsvcAuxiliaryPolicy.finish(boundary,boundary.binding,boundary.budget(10_000_000_000L),()->{throw new AssertionError("No live writer");});
        assertEquals(MsvcAuxiliaryPolicy.State.NATURAL_DRAIN,result.state());assertTrue(result.forcedCleanup().isEmpty());
        assertEquals(0,boundary.terminations);assertEquals(0,boundary.closes);
    }
    @Test void guardOrRetainedCloseFailureCannotBecomeSuccessfulPolicy() {
        Boundary boundary=new Boundary();
        var rejected=MsvcAuxiliaryPolicy.finish(boundary,boundary.binding,boundary.budget(10_000_000_000L),()->{throw new IllegalStateException("original source guard");});
        assertFalse(rejected.completed());assertEquals(0,boundary.terminations);
        Boundary closing=new Boundary();closing.closeFailure=true;var result=closing.finish();
        assertFalse(result.completed());assertEquals(1,result.forcedCleanup().size());assertEquals(1,closing.closes);
        Boundary unknown=new Boundary();unknown.unknownTermination=true;var unknownResult=unknown.finish();
        assertFalse(unknownResult.completed());assertEquals(1,unknown.terminations);assertEquals(1,unknownResult.forcedCleanup().size());
        assertFalse(unknownResult.forcedCleanup().getFirst().termination().acknowledged());
        assertEquals(5L,unknownResult.forcedCleanup().getFirst().termination().win32Error().longValue());
        assertNull(unknownResult.forcedCleanup().getFirst().actualExitCode());assertEquals(1,unknown.closes);
    }
    @Test void explicitBindingAndForcedReportRoundTripPreserveDecimal128BitFileIdAndBirth() throws Exception {
        var result=new Boundary().finish();var mapper=ControlBuild.strictMapper();byte[] bytes=mapper.writeValueAsBytes(result);
        assertEquals(result,mapper.readValue(bytes,MsvcAuxiliaryPolicy.Outcome.class));
        ObjectNode wire=(ObjectNode)mapper.readTree(bytes);
        assertEquals(FILE_ID,wire.path("binding").path("toolchain").path("vctip").path("file_id_decimal").textValue());
        assertEquals(BIRTH,wire.path("forced_cleanup").get(0).path("identity").path("creation_filetime_decimal").textValue());
        ObjectNode bad=wire.deepCopy();((ObjectNode)bad.path("binding").path("toolchain").path("vctip")).put("file_id_decimal",1);
        assertThrows(IOException.class,()->mapper.treeToValue(bad,MsvcAuxiliaryPolicy.Outcome.class));
        ObjectNode nullExit=wire.deepCopy();((ObjectNode)nullExit.path("forced_cleanup").get(0)).putNull("actual_exit_code");
        assertThrows(IOException.class,()->mapper.treeToValue(nullExit,MsvcAuxiliaryPolicy.Outcome.class));
    }
}
