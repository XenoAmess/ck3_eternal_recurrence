package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real ordinary native producer for rejection boundaries. Test DATA never qualifies a physical source. */
public final class PhysicalStatusReadBoundaryTest {
    @TempDir Path directory;
    private static PlanningReadResult.Known<RawJson> ordinary(ActionWriterIntegrationFixture actual, ActionCommand before) {
        var result = actual.reads.read(actual.readContract, new PlanningReadRequest(before.before(), before.source(),
                before.sessionId(), actual.readContract.operation(), new OpportunityJson.Obj(Map.of()), before.deadline()));
        if (result instanceof PlanningReadResult.Known<RawJson> known) return known;
        throw new AssertionError("actual ordinary native READ producer is unavailable: "
                + (result instanceof PlanningReadResult.Unavailable<?> unavailable ? unavailable.reason() : String.valueOf(result)));
    }
    private static PhysicalStatusIdentity unqualifiedData(ActionWriterIntegrationFixture actual,
            ActionCommand before, PlanningReadReceipt original) {
        var binding = original.before().binding();
        var transport = actual.physicalInputs().transport().diagnostics().session().orElseThrow();
        var data = actual.archive.preserveMaterial(new RawJson(
                "{\"kind\":\"UNQUALIFIED_TEST_DATA_ONLY\"}".getBytes(StandardCharsets.UTF_8)));
        return new PhysicalStatusIdentity(transport, before.before().frame().snapshotId(),
                before.before().frame().identity().nativeRevision(), before.source(), binding.nativeEvidence(),
                binding.capabilityEvidence(), data, data, data, binding.observedAt());
    }
    @Test public void actualOrdinaryReceiptCannotBeRelabelledPhysicalAndColdReadDoesNotQueryAgain() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(directory.resolve("ordinary"), false)) {
            var command = actual.command("ordinary-read-boundary"); var known = ordinary(actual, command);
            int writes = actual.nativeReadWrites(); byte[] ledger = actual.ledgerBytes();
            assertEquals(PlanningReadReceipt.ArchiveVersion.CURRENT_V2, known.receipt().archiveVersion());
            assertEquals(known.receipt(), actual.archive.loadRead(known.originalReceipt()));
            var old = known.receipt();
            assertThrows(IllegalArgumentException.class, () -> new PlanningReadReceipt(old.request(), old.contractId(),
                    old.requestId(), old.before(), old.after(), old.original(), Optional.empty(),
                    PlanningReadReceipt.ArchiveVersion.PHYSICAL_STATUS_V3));
            assertEquals(writes, actual.nativeReadWrites()); assertEquals(0, actual.nativeActionWrites());
            assertArrayEquals(ledger, actual.ledgerBytes());
        }
    }
    @Test public void typedButUnqualifiedStatusDataCannotConstructActionOrBorrowOrdinaryReadAuthority() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(directory.resolve("non-read"), false)) {
            var command = actual.command("physical-data-boundary"); var known = ordinary(actual, command);
            var identity = unqualifiedData(actual, command, known.receipt());
            var origin = new CommandOrigin.PhysicalStatusOnly(identity);
            assertThrows(IllegalStateException.class, origin::requireGameplay);
            var rejected = assertThrows(IllegalArgumentException.class, () -> new ActionCommand(command.actionId(), origin,
                    command.source(), command.sessionId(), command.operation(), command.arguments(), command.expectation(),
                    command.claims(), command.deadline(), command.protocolIdentity()));
            assertTrue(rejected.getMessage().contains("physical status"));
            var request = PlanningReadRequest.newStatusOnly(identity, new OperationKey(PhysicalStatusIdentity.OPERATION),
                    new OpportunityJson.Obj(Map.of()), Instant.now().plusSeconds(5));
            int writes = actual.nativeReadWrites(); byte[] ledger = actual.ledgerBytes();
            assertInstanceOf(PlanningReadResult.Unavailable.class, actual.reads.read(actual.readContract, request));
            assertTrue(actual.reads.readOriginal(actual.readContract, request).original().isEmpty());
            assertEquals(writes, actual.nativeReadWrites()); assertEquals(0, actual.nativeActionWrites());
            assertArrayEquals(ledger, actual.ledgerBytes());
        }
    }
    private static RootExecutableBindings captureBindings() {
        return RootExecutableBindings.freeze(java.util.List.of(),RootReadContractCatalog.staticOnly(java.util.List.of()),
                java.util.List.of(),4);
    }
    private static ActionCoordinator captureCoordinator(ActionWriterIntegrationFixture actual,RootExecutableBindings bindings,
            java.util.concurrent.atomic.AtomicInteger reached) {
        var coordinator=new ActionCoordinator("capture-denial-software-boundary",actual.journal,
                (head,command)->{reached.incrementAndGet();throw new AssertionError("capture reached an action guard");},
                bindings,actual.physicalInputs().transport(),bindings.effects(),java.time.Clock.systemUTC());
        var source=actual.physicalInputs().source().sourceRef();
        PhysicalActionRegistry.Producer never=new PhysicalActionRegistry.Producer() {
            private AssertionError reached(){reached.incrementAndGet();return new AssertionError("capture reached a physical producer");}
            @Override public GuardEvidence guard(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ActionCommand command){throw reached();}
            @Override public PreparedAction prepare(Session same,ActionCommand command,String id){throw reached();}
            @Override public PhysicalOutcome post(PhysicalSubmission permit,PreparedAction prepared,Instant deadline){throw reached();}
            @Override public PhysicalActionRegistry.Observation observe(Session same,ActionCommand command,PhysicalActionState original,Instant deadline){throw reached();}
            @Override public void verifyArchived(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive originals){throw reached();}
            @Override public java.util.List<PhysicalActionRegistry.DeferredResult> collect(Session same){throw reached();}
        };
        coordinator.bindPhysicalActions(new PhysicalActionRegistry(java.util.List.of(new PhysicalActionRegistry.Binding(
                new OperationKey("pause-map"),org.xar.ck3.control.contracts.presentation.TransportKind.PRESENTATION_MMAP,
                java.util.List.of(source),never))));
        return coordinator;
    }
    /** Controlled original transport/writer regression only; the denial grants no Managed or physical authority. */
    @Test public void captureDeniesExecuteReconcileCompositeAndAutomaticBeforeIntentOrTransport()throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(directory.resolve("capture-all-entries"),true)) {
            var command=actual.command("original-before-capture",java.time.Duration.ofSeconds(120));var original=actual.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class,original.state(), () -> "actual original action before capture: " + original);
            var bindings=captureBindings();var reached=new java.util.concurrent.atomic.AtomicInteger();
            var denied=captureCoordinator(actual,bindings,reached);
            var continuation=new CompositeContinuationToken() {
                @Override public ActionCommand originalParent(){return command;}
                @Override public Instant deadline(){return command.deadline();}
                @Override public Kind kind(){return Kind.FIXTURE_STARTUP;}
            };
            int writes=actual.nativeActionWrites();byte[] ledger=actual.ledgerBytes();
            bindings.withCaptureReadOnly(command.origin().game(),()->{
                assertThrows(java.io.UncheckedIOException.class,()->denied.execute(command));
                assertThrows(java.io.UncheckedIOException.class,()->denied.reconcile(command.actionId()));
                assertThrows(java.io.IOException.class,()->denied.continueOriginalComposite(continuation));
                actual.writer.locked(same->{
                    assertThrows(java.io.UncheckedIOException.class,()->denied.execute(same,command));
                    assertThrows(java.io.UncheckedIOException.class,()->denied.reconcile(same,command.actionId()));
                    assertThrows(java.io.IOException.class,()->denied.continueOriginalComposite(same,continuation));
                    assertThrows(java.io.UncheckedIOException.class,()->denied.deferAutomatic(same,command));
                    assertThrows(java.io.UncheckedIOException.class,()->denied.collectAutomatic(same));
                    return null;
                });
                assertEquals(0,reached.get());assertEquals(writes,actual.nativeActionWrites());
                assertArrayEquals(ledger,actual.ledgerBytes());return null;
            });
            actual.writer.locked(same->{assertDoesNotThrow(()->bindings.requireOutsideReadOnlyScope(same,command));return null;});
            assertEquals(original,actual.reopenAndReturnExisting(command));
            assertEquals(0,reached.get());assertEquals(writes,actual.nativeActionWrites());assertArrayEquals(ledger,actual.ledgerBytes());
        }
    }
    @Test public void nestedCaptureFailureRestoresOnlyItsParentAndAnotherThreadCannotClearIt()throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(directory.resolve("capture-owner"),false)) {
            var command=actual.command("after-original-capture",java.time.Duration.ofSeconds(120));var bindings=captureBindings();
            var reached=new java.util.concurrent.atomic.AtomicInteger();var denied=captureCoordinator(actual,bindings,reached);
            var originalFailure=new java.io.IOException("original capture callback failed");
            byte[] ledger=actual.ledgerBytes();int writes=actual.nativeActionWrites();
            var returned=assertThrows(java.io.IOException.class,()->bindings.withCaptureReadOnly(command.origin().game(),()->{
                var nested=assertThrows(java.io.IOException.class,()->bindings.withCaptureReadOnly(command.origin().game(),()->{
                    throw originalFailure;
                }));
                assertSame(originalFailure,nested);
                assertThrows(java.io.IOException.class,()->bindings.requireOutsideCaptureReadOnly(command.origin().game()));
                var otherScope=new java.util.concurrent.atomic.AtomicReference<Throwable>();
                var otherAction=new java.util.concurrent.atomic.AtomicReference<Throwable>();
                Thread another=Thread.ofPlatform().start(()->{
                    try{bindings.withCaptureReadOnly(command.origin().game(),()->{reached.incrementAndGet();return null;});}
                    catch(Throwable failure){otherScope.set(failure);}
                    try{denied.execute(command);}
                    catch(Throwable failure){otherAction.set(failure);}
                });
                another.join(5000);if(another.isAlive()){another.interrupt();fail("capture denial worker did not terminate");}
                assertInstanceOf(java.io.IOException.class,otherScope.get());
                assertInstanceOf(java.io.UncheckedIOException.class,otherAction.get());
                assertThrows(java.io.IOException.class,bindings::requireOutsideCaptureReadOnly);
                assertEquals(0,reached.get());assertEquals(writes,actual.nativeActionWrites());
                assertArrayEquals(ledger,actual.ledgerBytes());throw originalFailure;
            }));
            assertSame(originalFailure,returned);assertDoesNotThrow(()->bindings.requireOutsideCaptureReadOnly(command.origin().game()));
            assertDoesNotThrow(() -> { bindings.requireOutsideCaptureReadOnly(); });
            var actualAfter=actual.coordinator.execute(command);
            assertEquals(command,actualAfter.command());assertEquals(writes+1,actual.nativeActionWrites(),
                    () -> "actual original action after capture closed: " + actualAfter);
            assertEquals(0,reached.get());
        }
    }
    /** Only the real installed physical provider's test may supply this positive. No guard/token is minted here. */
    public static void assertActualPhysicalReceipt(Session same, ReadContract<?> identicalInstalled,
            PlanningReadResult.Known<?> actualKnown, ActionPorts.OutcomeArchive originals) {
        PhysicalStatusIdentity.requireProfile(identicalInstalled);
        var receipt = actualKnown.receipt();
        assertInstanceOf(CommandOrigin.PhysicalStatusOnly.class, receipt.request().origin());
        assertEquals(identicalInstalled.contractId(), receipt.contractId());
        assertEquals(PlanningReadReceipt.ArchiveVersion.PHYSICAL_STATUS_V3, receipt.archiveVersion());
        assertTrue(receipt.adoption().isEmpty());
        assertEquals(ReadContract.GuardMode.STATUS_ONLY, receipt.before().guardMode());
        assertEquals(ReadContract.GuardMode.STATUS_ONLY, receipt.after().guardMode());
        assertEquals(receipt, originals.withSession(same).loadRead(actualKnown.originalReceipt()));
        assertThrows(IllegalArgumentException.class, () -> new PlanningReadReceipt(receipt.request(), receipt.contractId(),
                receipt.requestId(), receipt.before(), receipt.after(), receipt.original(), Optional.empty(),
                PlanningReadReceipt.ArchiveVersion.CURRENT_V2));
    }
}
