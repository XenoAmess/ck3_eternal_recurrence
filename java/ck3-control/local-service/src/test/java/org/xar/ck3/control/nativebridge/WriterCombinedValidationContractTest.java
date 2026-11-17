package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual writer/default authority contract; no Game operation or saved-material role is minted. */
final class WriterCombinedValidationContractTest {
    @TempDir Path temporary;
    private static final String KIND="test_combined_validation_v1";
    private static WriterContracts.Request request() {
        var row=StrictJson.object();row.put("evidence_id","same-phase-default");
        row.put("source","java-software-combined-validation-contract/v1");
        return new WriterContracts.Request(KIND,StrictJson.canonical(row),List.of());
    }
    private static final class Probe implements WriterContracts.TransitionAuthority {
        final List<String> trace=new ArrayList<>();int revision;boolean active,failValidation;
        @Override public <T>T withReadValidation(WriterContracts.Head head,WriterContracts.Request request,
                ContinuityStorePort.Session same,ContinuityStorePort.SessionWork<T> work)throws IOException {
            assertFalse(active);trace.add("open");active=true;
            try{return work.run(same);}finally{active=false;trace.add("close");}
        }
        @Override public String revalidate(ContinuityState before,WriterContracts.Request request) {
            throw new AssertionError("the actual original Head must survive default dispatch");
        }
        @Override public String revalidate(WriterContracts.Head head,WriterContracts.Request request)throws IOException {
            assertTrue(active);trace.add("validate");
            if(failValidation)throw new IOException("original source unavailable");
            return ActionCodec.sha256(("actual-proof-"+revision).getBytes(StandardCharsets.UTF_8));
        }
        @Override public ContinuityState reduce(ContinuityState before,WriterContracts.Request request) {
            assertTrue(active);trace.add("reduce");return before;
        }
    }

    @Test void actualWriterDefaultsValidateThenReduceInSeparatePreviewAndCommitPhases()throws Exception {
        try(var f=new ActionWriterIntegrationFixture(temporary.resolve("ordered"),false)) {
            var probe=new Probe();f.bindAdditionalTransitionAuthority(KIND,probe);
            f.writer.locked(same->{
                var before=same.head();var prepared=same.preview(request());
                assertEquals(List.of("open","validate","reduce","close"),probe.trace);
                probe.trace.clear();var receipt=same.commit(prepared);
                assertEquals(WriterContracts.Disposition.NO_CHANGE,receipt.disposition());
                assertEquals(List.of("open","validate","reduce","close"),probe.trace);
                assertFalse(probe.active);assertEquals(before.digest(),same.head().digest());return null;
            });
            assertEquals(0,f.nativeActionWrites());
        }
    }

    @Test void commitDigestMismatchPrecedesDefaultReduceAndAlwaysClosesTheReadScope()throws Exception {
        try(var f=new ActionWriterIntegrationFixture(temporary.resolve("mismatch"),false)) {
            var probe=new Probe();f.bindAdditionalTransitionAuthority(KIND,probe);
            f.writer.locked(same->{
                var prepared=same.preview(request());String before=same.head().digest();
                probe.trace.clear();probe.revision++;
                var failure=assertThrows(Exception.class,()->same.commit(prepared));
                assertTrue(failure.getMessage().contains("preconditions changed"),failure::toString);
                assertEquals(List.of("open","validate","close"),probe.trace);
                assertFalse(probe.active);assertEquals(before,same.head().digest());return null;
            });
            assertEquals(0,f.nativeActionWrites());
        }
    }

    @Test void defaultDigestGateAndSourceFailuresNeverReachReduction()throws Exception {
        try(var f=new ActionWriterIntegrationFixture(temporary.resolve("failure"),false)) {
            var probe=new Probe();
            f.writer.locked(same->{
                var head=same.head();var gateFailure=new IllegalStateException("writer gate rejected");
                var actual=assertThrows(IllegalStateException.class,()->probe.withReadValidation(head,request(),same,
                        borrowed->probe.revalidateAndReduce(head,request(),digest->{probe.trace.add("gate");throw gateFailure;})));
                assertSame(gateFailure,actual);assertEquals(List.of("open","validate","gate","close"),probe.trace);
                probe.trace.clear();probe.failValidation=true;
                assertThrows(IOException.class,()->probe.withReadValidation(head,request(),same,
                        borrowed->probe.revalidateAndReduce(head,request(),digest->fail("source failure must precede gate"))));
                assertEquals(List.of("open","validate","close"),probe.trace);
                assertFalse(probe.active);assertEquals(head.digest(),same.head().digest());return null;
            });
            assertEquals(0,f.nativeActionWrites());
        }
    }
}
