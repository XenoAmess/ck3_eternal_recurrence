package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Actual software writer/Router/7arg authority; no private Core issuer or physical Game qualification. */
final class NormalAppendLiveReadScopeTest {
    @TempDir Path root;
    private static final ActionPorts.HistoricalReadLimits LIMITS=new ActionPorts.HistoricalReadLimits(4096,256L*1024*1024,8192);
    @FunctionalInterface private interface HeldWork<T> {
        T run(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive archive)throws IOException;
    }
    private static <T> T held(ActionWriterIntegrationFixture fixture,HeldWork<T> work)throws IOException {
        return fixture.writer.locked(same->{
            try {
                return fixture.journal.locked(same,journal->{
                    assertSame(same,journal.writerSession());
                    try {return work.run(same,fixture.archive.withSession(same));}
                    catch(IOException failure) {throw new UncheckedIOException(failure);}
                });
            } catch(UncheckedIOException failure) {throw failure.getCause();}
        });
    }
    private static ObjectNode details(ActionReceipt receipt,ExactRef record) {
        ObjectNode data=StrictJson.object();data.put("evidence_id",receipt.command().actionId()+":"+receipt.sequence());
        data.set("source",ProposalLifecycleCodec.source(receipt.command().source()));data.set("receipt_ref",record.toJson());return data;
    }
    /** Input originals follow the real Journal producer; no reduction/validation result is implemented here. */
    private static WriterContracts.Request intent(WriterContracts.Head head,ActionCommand command,ActionPorts.OutcomeArchive archive) {
        var receipt=new ActionReceipt(1,head.state().sequence()+1,command,ActionCodec.bodySha256(command),new ActionState.IntentDurable());
        ExactRef receiptRef=archive.preserveReceipt(receipt);
        var record=new ActionRecord(receipt,ContinuityActionJournal.recordHead(head.state()));
        ExactRef recordRef=archive.preserveRecord(record);var evidence=new ArrayList<ExactRef>();
        evidence.add(recordRef);evidence.add(receiptRef);record.previous().ifPresent(evidence::add);
        return new WriterContracts.Request(ContinuityActionJournal.KIND,ContinuityJson.canonical(details(receipt,recordRef)),evidence);
    }
    private static WriterContracts.Request current(WriterContracts.Head head,ActionPorts.OutcomeArchive archive) {
        ExactRef record=ContinuityActionJournal.recordHead(head.state()).orElseThrow();
        return new WriterContracts.Request(ContinuityActionJournal.KIND,ContinuityJson.canonical(details(archive.loadRecord(record).receipt(),record)),List.of(record));
    }
    private static ActionCommand named(ActionCommand original,String id) {
        return new ActionCommand(id,original.origin(),original.source(),original.sessionId(),original.operation(),original.arguments(),
                original.expectation(),original.claims(),original.deadline(),original.protocolIdentity());
    }
    private static WriterContracts.Layout layout(ActionWriterIntegrationFixture fixture,WriterContracts.Head head)throws IOException {
        Path anchorPath=fixture.root.resolve("anchor.json").toAbsolutePath().normalize();
        ExactRef anchor=head.documents().stream().filter(pin->Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(anchorPath))
                .map(WriterContracts.Pin::reference).findFirst().orElseThrow(()->new IOException("actual head lacks its original fixture anchor pin"));
        return new WriterContracts.Layout(fixture.root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor,head.state().machineId());
    }
    private static void restore(Path path,byte[] raw,FileTime modified)throws IOException {
        Files.write(path,raw);Files.setLastModifiedTime(path,modified);
    }
    private static byte[] corrupt(byte[] raw) {
        byte[] changed=raw.clone();changed[changed.length-1]^=1;return changed;
    }

    @Test void realCoordinatorTraversesOptedInIntentAndSubmittingAndUnknownKeepsOldScope()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("coordinator"),false)) {
            ActionCommand command=fixture.command("scope-coordinator",Duration.ofMinutes(2));
            ActionReceipt actual=fixture.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class,actual.state());assertEquals(ActionReceipt.Outcome.UNRESOLVED,actual.outcome());
            assertFalse(actual.visibleGameplay());assertFalse(actual.eligibleAdvance());assertTrue(actual.applied().isEmpty());
            assertEquals(1,fixture.nativeActionWrites());assertTrue(fixture.sourceChecks.get()>0);
            assertNotNull(fixture.originalHookSession.get());assertNotNull(fixture.originalPreparedAtHook.get());
            held(fixture,(same,archive)->{
                var before=same.head();
                var actualPaths=layout(fixture,before);
                var anchorPin=before.documents().stream().filter(pin->pin.reference().equals(actualPaths.anchor())).findFirst().orElseThrow();
                long anchorSequence=org.xar.ck3.control.continuity.ContinuityState.fromJson(ContinuityJson.parseObject(
                        same.readPinned(anchorPin,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES),before.state().machineId()).sequence();
                var eventPins=new ArrayList<WriterContracts.Pin>();
                for(long sequence=anchorSequence+1;sequence<=before.state().sequence();sequence++) {
                    Path eventPath=actualPaths.event(sequence);
                    eventPins.add(before.documents().stream().filter(pin->Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(eventPath))
                            .findFirst().orElseThrow(()->new IOException("actual head lacks its exact canonical event pin")));
                }
                var history=same.withHistoricalTransitions(eventPins,edges->{
                    var rows=new ArrayList<ActionReceipt>();
                    for(var edge:edges)if(edge.kind().equals(ContinuityActionJournal.KIND)) {
                        var data=ContinuityJson.parseObject(edge.details(),ContinuityJson.LEDGER_MAX_BYTES);
                        var row=archive.loadRecord(ExactRef.fromJson(data.get("receipt_ref"))).receipt();
                        if(row.command().actionId().equals(command.actionId()))rows.add(row);
                    }
                    return List.copyOf(rows);
                });
                assertEquals(history.size(),ContinuityActionJournal.requireHistoricalReceipts(before.state(),history,archive).size());
                assertTrue(history.stream().anyMatch(value->value.state() instanceof ActionState.IntentDurable));
                assertTrue(history.stream().anyMatch(value->value.state() instanceof ActionState.Submitting));
                assertTrue(history.stream().anyMatch(value->value.state() instanceof ActionState.AckReceived));
                assertTrue(history.stream().anyMatch(value->value.state() instanceof ActionState.Unknown));
                for(ActionReceipt row:history) {
                    assertEquals(command,row.command());assertEquals(ActionCodec.bodySha256(command),row.bodySha256());
                    assertFalse(row.visibleGameplay());assertFalse(row.eligibleAdvance());
                }
                WriterContracts.Request nonPreDispatch=current(before,archive);var innerCalls=new AtomicInteger();
                String result=fixture.actionRouter.withReadValidation(before,nonPreDispatch,same,borrowed->{
                    assertSame(same,borrowed);
                    return fixture.archive.inHistoricalReadScope(borrowed,LIMITS,scoped->{
                        innerCalls.incrementAndGet();assertEquals(actual,scoped.loadRecord(ContinuityActionJournal.recordHead(before.state()).orElseThrow()).receipt());
                        return "unknown-explicit-inner-scope";
                    });
                });
                assertEquals("unknown-explicit-inner-scope",result);assertEquals(1,innerCalls.get());
                assertEquals(before.digest(),same.head().digest());assertEquals(before.state().sequence(),same.head().state().sequence());
                assertFalse(Files.exists(layout(fixture,before).event(before.state().sequence()+1)));
                return null;
            });
            assertEquals(1,fixture.nativeActionWrites());
            System.out.println("SOFTWARE_NORMAL_APPEND coordinator_intent_submitting=true native_writes=1 unknown_no_credit=true unknown_explicit_scope=true");
        }
    }

    @Test void caughtActualOriginalReadFailureAndPrimaryCallbackCannotReturnSuccessOrLeakScope()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("failure"),false)) {
            ActionCommand command=fixture.command("scope-failure",Duration.ofMinutes(2));
            fixture.journal.locked(journal->journal.append(command,ActionCodec.bodySha256(command),new ActionState.IntentDurable()));
            held(fixture,(same,archive)->{
                var head=same.head();WriterContracts.Request request=current(head,archive);
                ExactRef material=archive.preserveMaterial(new RawJson("{\"actual_original\":\"before_read_failure\"}".getBytes(StandardCharsets.UTF_8)));
                Path path=Path.of(material.path());byte[] raw=Files.readAllBytes(path);FileTime modified=Files.getLastModifiedTime(path);
                var identity=same.capturePin(material,WriterContracts.MAX_PIN_BYTES).identity();var calls=new AtomicInteger();var fired=new AtomicInteger();
                var caught=new AtomicReference<IOException>();var delivered=new AtomicReference<String>();
                try {
                    assertThrows(IOException.class,()->delivered.set(fixture.actionRouter.withReadValidation(head,request,same,borrowed->{
                        calls.incrementAndGet();assertSame(same,borrowed);Files.write(path,corrupt(raw));fired.incrementAndGet();
                        try {
                            UncheckedIOException read=assertThrows(UncheckedIOException.class,()->archive.loadMaterial(material));
                            caught.set(read.getCause());
                        } finally {restore(path,raw,modified);}
                        assertEquals(identity,same.capturePin(material,WriterContracts.MAX_PIN_BYTES).identity());return "must-not-return";
                    })));
                } finally {restore(path,raw,modified);}
                assertNull(delivered.get());assertEquals(1,calls.get());assertEquals(1,fired.get());assertNotNull(caught.get());
                assertEquals(identity,same.capturePin(material,WriterContracts.MAX_PIN_BYTES).identity());
                assertEquals("restored",fixture.actionRouter.withReadValidation(head,request,same,borrowed->{
                    assertArrayEquals(raw,archive.loadMaterial(material).bytes());return "restored";
                }));
                IOException primary=new IOException("actual callback primary");var primaryCalls=new AtomicInteger();
                IOException escaped=assertThrows(IOException.class,()->fixture.actionRouter.withReadValidation(head,request,same,borrowed->{
                    primaryCalls.incrementAndGet();throw primary;
                }));
                assertSame(primary,escaped);assertEquals(1,primaryCalls.get());
                assertEquals("fresh-again",fixture.actionRouter.withReadValidation(head,request,same,borrowed->{
                    assertArrayEquals(raw,archive.loadMaterial(material).bytes());return "fresh-again";
                }));
                assertEquals(head.digest(),same.head().digest());assertFalse(Files.exists(layout(fixture,head).event(2)));
                return null;
            });
            assertEquals(0,fixture.nativeActionWrites());
            System.out.println("SOFTWARE_NORMAL_FAILURE actual_read_failure_caught=true restored_identity=true result_delivered=false primary_preserved=true fresh_scopes=true");
        }
    }

    @Test void changedHeadStalePreparedAndLaterOriginalDriftRequireFreshQualification()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("head"),false)) {
            ActionCommand a=fixture.command("scope-head-a",Duration.ofMinutes(2));
            ActionCommand b=named(a,"scope-head-b"),c=named(a,"scope-head-c");
            held(fixture,(same,archive)->{
                var initial=same.head();var paths=layout(fixture,initial);
                WriterContracts.Request requestA=intent(initial,a,archive),staleRequestB=intent(initial,b,archive);
                var preparedA=same.preview(requestA);var preparedB=same.preview(staleRequestB);
                assertEquals(WriterContracts.Disposition.COMMITTED,same.commit(preparedA).disposition());
                var afterA=same.head();assertEquals(1,afterA.state().sequence());
                ContractViolationException stale=assertThrows(ContractViolationException.class,()->same.commit(preparedB));
                assertTrue(stale.getMessage().contains("real head/source/file-identity CAS drift"));
                assertFalse(Files.exists(paths.event(2)));
                ExactRef recordA=ContinuityActionJournal.recordHead(afterA.state()).orElseThrow();
                WriterContracts.Request requestB=intent(afterA,b,archive);
                assertEquals(WriterContracts.Disposition.COMMITTED,same.commit(same.preview(requestB)).disposition());
                var afterB=same.head();assertEquals(2,afterB.state().sequence());
                ExactRef recordB=ContinuityActionJournal.recordHead(afterB.state()).orElseThrow();
                assertEquals(recordA,archive.loadRecord(recordB).previous().orElseThrow());
                WriterContracts.Request requestC=intent(afterB,c,archive);
                // C's immediate evidence is B. A is reached by real full canonical traversal inside the next scope.
                assertFalse(requestC.evidence().contains(recordA));assertTrue(requestC.evidence().contains(recordB));
                Path target=Path.of(recordA.path());byte[] raw=Files.readAllBytes(target);FileTime modified=Files.getLastModifiedTime(target);
                var identity=same.capturePin(recordA,WriterContracts.MAX_PIN_BYTES).identity();var delivered=new AtomicReference<WriterContracts.Prepared>();
                try {
                    Files.write(target,corrupt(raw));
                    assertThrows(UncheckedIOException.class,()->delivered.set(same.preview(requestC)));
                } finally {restore(target,raw,modified);}
                assertNull(delivered.get());assertEquals(identity,same.capturePin(recordA,WriterContracts.MAX_PIN_BYTES).identity());
                assertFalse(Files.exists(paths.event(3)));assertEquals(afterB.digest(),same.head().digest());
                assertEquals(WriterContracts.Disposition.COMMITTED,same.commit(same.preview(requestC)).disposition());
                var afterC=same.head();assertEquals(3,afterC.state().sequence());
                var expected=Map.of(a.actionId(),a,b.actionId(),b,c.actionId(),c);
                var receipts=ContinuityActionJournal.receipts(afterC.state(),archive);assertEquals(3,receipts.size());
                assertEquals(3,receipts.stream().map(value->value.command().actionId()).distinct().count());
                for(ActionReceipt receipt:receipts) {
                    assertEquals(expected.get(receipt.command().actionId()),receipt.command());
                    assertEquals(ActionCodec.bodySha256(receipt.command()),receipt.bodySha256());assertEquals(1,receipt.version());
                    assertInstanceOf(ActionState.IntentDurable.class,receipt.state());assertFalse(receipt.eligibleAdvance());assertFalse(receipt.visibleGameplay());
                }
                byte[] snapshot=Files.readAllBytes(paths.snapshot());
                assertEquals(WriterContracts.Disposition.ALREADY_COMMITTED,same.commit(same.preview(requestC)).disposition());
                assertArrayEquals(snapshot,Files.readAllBytes(paths.snapshot()));assertEquals(3,same.head().state().sequence());
                assertFalse(Files.exists(paths.event(4)));return null;
            });
            assertEquals(0,fixture.nativeActionWrites());
            System.out.println("SOFTWARE_NORMAL_HEAD stale_prepared_rejected=true older_canonical_original_drift_rejected=true later_head=3 duplicate_no_event=true native_writes=0");
        }
    }
}
