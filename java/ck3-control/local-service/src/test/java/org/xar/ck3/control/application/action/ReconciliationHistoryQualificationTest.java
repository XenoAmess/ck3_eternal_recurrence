package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence.WriterPoint;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual sole-writer/archive custody at software Native edges; no private Root history qualification is fabricated. */
final class ReconciliationHistoryQualificationTest {
    @TempDir Path root;
    private static ActionReceipt execute(ActionWriterIntegrationFixture fixture,String id)throws Exception {
        var command=fixture.command(id);var retained=new AtomicReference<ActionReceipt>();
        try {fixture.physicalInputs().transport().withMailbox(command.deadline(),scope->{retained.set(fixture.coordinator.execute(command));return null;});}
        catch(IOException poisoned){if(retained.get()==null)throw poisoned;assertFalse(retained.get().settled());}
        assertInstanceOf(ActionState.Unknown.class,retained.get().state());return retained.get();
    }
    private static ReconciliationPendingBinding binder(ActionWriterIntegrationFixture fixture,
            ReconciliationPendingBinding.HistoryQualification qualification) {
        return new ReconciliationPendingBinding(fixture.writer,fixture.archive,fixture.archive::readArtifact,qualification);
    }
    private record Originals(ReconciliationIdentity exact,ReconciliationIdentity changed,WriterPoint point) { }
    private static Originals originals(ActionWriterIntegrationFixture fixture,ActionReceipt pending)throws IOException {
        return fixture.writer.locked(same->fixture.archive.inSession(same,archive->{
            var attempt=ActionTransitions.attempt(pending.state()).orElseThrow();var guard=attempt.guard();
            ExactRef driver=RootGuardEvidence.originalDriverSource(guard,archive).driverRef();
            ObjectNode basis=(ObjectNode)StrictJson.parse(archive.loadMaterial(guard.supportingEvidence().getFirst()).bytes());
            ExactRef heartbeat=ExactRef.fromJson(basis.get("heartbeat"));
            ExactRef manifest=RootGuardEvidence.frameBasis(guard,archive).driverFacts();
            var qualification=RootGuardEvidence.sourceQualification(guard,archive);
            var evidence=new ReconciliationIdentity.Evidence(guard.nativeEvidence(),guard.capabilityEvidence(),heartbeat,manifest,driver,qualification);
            var exact=ReconciliationIdentity.fromCanonical(pending,pending.command().before(),pending.command().source(),pending.command().sessionId(),
                    guard.connectionGeneration(),archive.receiptReferenceOf(pending),driver,evidence,guard.observedAt());
            // Intentionally unqualified authored DATA. This is never called a real Driver append or a private Root proof.
            ObjectNode unqualified=StrictJson.object().put("unqualified_history_data",true);unqualified.set("original_driver",driver.toJson());
            ExactRef different=archive.preserveMaterial(new RawJson(StrictJson.canonical(unqualified)));
            var changedEvidence=new ReconciliationIdentity.Evidence(guard.nativeEvidence(),guard.capabilityEvidence(),heartbeat,manifest,different,qualification);
            var head=assertDoesNotThrow(same::head);var point=new WriterPoint(head.state().sequence(),head.digest());
            var changed=ReconciliationIdentity.fromCanonicalHistoryAppend(pending,exact.factual(),exact.source(),exact.sessionId(),exact.connectionGeneration(),
                    exact.pending().originalReceipt(),driver,changedEvidence,exact.observedAt(),point);
            return new Originals(exact,changed,point);
        }));
    }
    private static Set<Path> files(Path root)throws IOException {
        try(var paths=Files.walk(root)){return paths.filter(Files::isRegularFile).map(path->path.toAbsolutePath().normalize()).collect(java.util.stream.Collectors.toUnmodifiableSet());}
    }
    @Test void actualExactOriginalDriverRetainsV1AndNeverCallsHistoryProvider()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("exact"),true)) {
            ActionReceipt pending=execute(fixture,"exact-pending");var inputs=originals(fixture,pending);var identity=inputs.exact();
            AtomicInteger calls=new AtomicInteger();var binding=binder(fixture,actual->{calls.incrementAndGet();throw new AssertionError("EXACT must not call the history provider");});
            byte[] ledger=fixture.ledgerBytes();Set<Path> originalFiles=files(fixture.root);int reads=fixture.nativeReadWrites(),packets=fixture.nativePacketReads();
            fixture.writer.locked(same->{binding.verify(same,identity);binding.verifyHistorical(same,identity);return null;});
            ObjectNode encoded=ReconciliationIdentityCodec.encode(identity);assertEquals(ReconciliationIdentityCodec.SCHEMA,encoded.get("schema").textValue());
            assertFalse(encoded.has("driver_relation"));assertFalse(encoded.has("history_point"));assertEquals(identity,ReconciliationIdentityCodec.decode(encoded));
            assertEquals(ReconciliationIdentity.DriverRelation.EXACT,identity.driverRelation());assertTrue(identity.historyPoint().isEmpty());
            assertEquals(0,calls.get());assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(originalFiles,files(fixture.root));
            assertEquals(reads,fixture.nativeReadWrites());assertEquals(packets,fixture.nativePacketReads());assertEquals(1,fixture.nativeActionWrites());
        }
    }
    @Test void v2ChangedDriverDataIsDeniedByOldConstructorAndDefaultPrivatePortWithoutAnyWrite()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("default-deny"),true)) {
            ActionReceipt pending=execute(fixture,"changed-data-pending");var inputs=originals(fixture,pending);var identity=inputs.changed();
            var old=new ReconciliationPendingBinding(fixture.writer,fixture.archive,fixture.archive::readArtifact);
            assertSame(ReconciliationPendingBinding.HistoryQualification.unavailable(),old.historyQualification());
            assertThrows(NullPointerException.class,()->binder(fixture,null));
            assertThrows(IllegalArgumentException.class,()->new ReconciliationIdentity(identity.factual(),identity.source(),identity.sessionId(),
                    identity.connectionGeneration(),identity.pending(),identity.evidence(),identity.observedAt()));
            byte[] ledger=fixture.ledgerBytes();Set<Path> originalFiles=files(fixture.root);int reads=fixture.nativeReadWrites(),packets=fixture.nativePacketReads();
            fixture.writer.locked(same->{assertThrows(IOException.class,()->old.verify(same,identity));assertThrows(IOException.class,()->old.verifyHistorical(same,identity));return null;});
            assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(originalFiles,files(fixture.root));assertEquals(reads,fixture.nativeReadWrites());
            assertEquals(packets,fixture.nativePacketReads());assertEquals(1,fixture.nativeActionWrites());assertEquals(pending,fixture.reopenAndReturnExisting(pending.command()));
        }
    }
    @Test void actualSessionCanonicalRecordOwnedBytesAndOriginalTargetAreDeliveredToTheDenyingProvider()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("private-inputs"),true)) {
            ActionReceipt pending=execute(fixture,"provider-original-pending");var inputs=originals(fixture,pending);var identity=inputs.changed();
            var contexts=new java.util.ArrayList<ReconciliationPendingBinding.HistoryContext>();
            var qualification=(ReconciliationPendingBinding.HistoryQualification)actual->{contexts.add(actual);throw new IOException("no actual private Root producer was installed");};
            var binding=binder(fixture,qualification);assertSame(qualification,binding.historyQualification());byte[] ledger=fixture.ledgerBytes();
            fixture.writer.locked(same->{
                var head=same.head();assertThrows(IOException.class,()->binding.verify(same,identity));assertThrows(IOException.class,()->binding.verifyHistorical(same,identity));
                assertEquals(2,contexts.size());for(var context:contexts) {
                    assertSame(same,context.session());assertEquals(head,context.head());assertEquals(head.digest(),context.targetHead().digest());
                    assertEquals(inputs.point().sequence(),context.targetHead().state().sequence());assertEquals(pending,context.original());
                    assertEquals(ActionTransitions.attempt(pending.state()).orElseThrow(),context.attempt());assertEquals(identity,context.identity());
                    assertEquals(identity.pending().originalReceipt(),context.receiptReference());
                    assertEquals(ContinuityActionJournal.requireHistoricalReceipt(head.state(),pending,fixture.archive.withSession(same)),context.recordReference());
                    assertEquals(identity.pending().originalBeforeDriver(),context.beforeDriver().reference());assertEquals(identity.evidence().currentOriginalDriver(),context.currentDriver().reference());
                    assertFalse(Arrays.equals(context.beforeDriver().bytes(),context.currentDriver().bytes()));
                    assertArrayEquals(fixture.archive.readArtifact(same,context.beforeDriver().reference(),org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES),context.beforeDriver().bytes());
                    byte[] copy=context.beforeDriver().bytes();copy[0]^=1;assertFalse(Arrays.equals(copy,context.beforeDriver().bytes()));
                }
                assertEquals(ReconciliationPendingBinding.Mode.LIVE_PENDING,contexts.getFirst().mode());assertEquals(ReconciliationPendingBinding.Mode.HISTORICAL_READ,contexts.getLast().mode());
                return null;
            });assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(1,fixture.nativeActionWrites());
        }
    }
    @Test void explicitV2SerdeRejectsMissingNullWrongTypesForeignSubjectsAndV1Smuggling()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("serde"),true)) {
            ActionReceipt pending=execute(fixture,"serde-original-pending");var inputs=originals(fixture,pending);var identity=inputs.changed();
            ObjectNode encoded=ReconciliationIdentityCodec.encode(identity);assertEquals(ReconciliationIdentityCodec.HISTORY_SCHEMA,encoded.get("schema").textValue());
            assertEquals(identity,ReconciliationIdentityCodec.decode(encoded));assertEquals(identity.bindingSha256(),ReconciliationIdentityCodec.decode(encoded).bindingSha256());
            var variants=new java.util.ArrayList<ObjectNode>();
            ObjectNode missing=encoded.deepCopy();missing.remove("history_point");variants.add(missing);
            ObjectNode nil=encoded.deepCopy();nil.putNull("history_point");variants.add(nil);
            ObjectNode relation=encoded.deepCopy();relation.put("driver_relation","EXACT");variants.add(relation);
            ObjectNode v1=encoded.deepCopy();v1.put("schema",ReconciliationIdentityCodec.SCHEMA);variants.add(v1);
            ObjectNode unknown=encoded.deepCopy();unknown.put("schema","xar.java.reconciliation-identity/v3");variants.add(unknown);
            for(com.fasterxml.jackson.databind.JsonNode wrong:List.of(StrictJson.object().booleanNode(true),StrictJson.object().numberNode(1.0),StrictJson.object().textNode("1"))) {
                ObjectNode row=encoded.deepCopy();((ObjectNode)row.get("history_point")).set("sequence",wrong);variants.add(row);
            }
            ObjectNode extra=encoded.deepCopy();((ObjectNode)extra.get("history_point")).put("qualification",true);variants.add(extra);
            ObjectNode equal=encoded.deepCopy();((ObjectNode)equal.get("evidence")).set("current_original_driver",identity.pending().originalBeforeDriver().toJson());variants.add(equal);
            ObjectNode actor=encoded.deepCopy();((ObjectNode)actor.get("factual").get("frame")).put("played_character_id","74");variants.add(actor);
            ObjectNode birth=encoded.deepCopy();((ObjectNode)birth.get("factual").get("game")).put("creation_filetime","9007199254740994");variants.add(birth);
            ObjectNode backwards=encoded.deepCopy();((ObjectNode)backwards.get("factual").get("frame")).put("native_revision","0");variants.add(backwards);
            for(ObjectNode invalid:variants)assertThrows(RuntimeException.class,()->ReconciliationIdentityCodec.decode(invalid));
            var exact=inputs.exact();ObjectNode old=ReconciliationIdentityCodec.encode(exact);old.put("driver_relation","EXACT");assertThrows(RuntimeException.class,()->ReconciliationIdentityCodec.decode(old));
            assertThrows(IllegalArgumentException.class,()->new ReconciliationIdentity(exact.factual(),exact.source(),exact.sessionId(),exact.connectionGeneration(),
                    exact.pending(),exact.evidence(),exact.observedAt(),ReconciliationIdentity.DriverRelation.HISTORY_APPEND,Optional.of(inputs.point())));
        }
    }
    @Test void alteredLiveTargetAndForeignPendingRequestAreRejectedBeforePrivateCallback()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("wrong-target"),true)) {
            ActionReceipt pending=execute(fixture,"wrong-target-pending");var inputs=originals(fixture,pending);var basis=inputs.changed();AtomicInteger calls=new AtomicInteger();
            var binding=binder(fixture,actual->{calls.incrementAndGet();throw new IOException("unavailable");});
            var wrongPoint=ReconciliationIdentity.fromCanonicalHistoryAppend(pending,basis.factual(),basis.source(),basis.sessionId(),basis.connectionGeneration(),
                    basis.pending().originalReceipt(),basis.pending().originalBeforeDriver(),basis.evidence(),basis.observedAt(),new WriterPoint(inputs.point().sequence(),"f".repeat(64)));
            var original=basis.pending();var foreign=new ReconciliationIdentity.Pending(original.actionId(),original.bodySha256(),"foreign-request",original.originalBefore(),original.originalReceipt(),original.originalBeforeDriver());
            var wrongPending=new ReconciliationIdentity(basis.factual(),basis.source(),basis.sessionId(),basis.connectionGeneration(),foreign,basis.evidence(),basis.observedAt(),basis.driverRelation(),basis.historyPoint());
            byte[] ledger=fixture.ledgerBytes();fixture.writer.locked(same->{
                assertThrows(IOException.class,()->binding.verify(same,wrongPoint));assertThrows(IOException.class,()->binding.verifyHistorical(same,wrongPoint));
                assertThrows(IOException.class,()->binding.verify(same,wrongPending));return null;
            });assertEquals(0,calls.get());assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(1,fixture.nativeActionWrites());
        }
    }
    @Test void exactOwnedMaterialUsesContentEqualityDefensiveCopiesAndStrictReferenceBytes() {
        byte[] bytes="{\"owned\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8);var ref=new ExactRef("C:/software-data/driver.json",bytes.length,ActionCodec.sha256(bytes));
        var first=new ReconciliationPendingBinding.DriverMaterial(ref,bytes);var second=new ReconciliationPendingBinding.DriverMaterial(ref,bytes.clone());
        assertEquals(first,second);assertEquals(first.hashCode(),second.hashCode());bytes[0]^=1;assertNotEquals(bytes[0],first.bytes()[0]);
        byte[] returned=first.bytes();returned[0]^=1;assertNotEquals(returned[0],first.bytes()[0]);
        assertThrows(IllegalArgumentException.class,()->new ReconciliationPendingBinding.DriverMaterial(ref,bytes));
        assertThrows(IllegalArgumentException.class,()->new ReconciliationPendingBinding.DriverMaterial(new ExactRef(ref.path(),ref.bytes()+1,ref.sha256()),first.bytes()));
        assertThrows(IllegalArgumentException.class,()->new ReconciliationPendingBinding.DriverMaterial(new ExactRef(ref.path(),ref.bytes(),"a".repeat(64)),first.bytes()));
        assertThrows(IOException.class,()->ReconciliationPendingBinding.HistoryQualification.unavailable().require(null));
    }
    @Test void actualBinderOwnerIdentityRejectsAnotherWriterArchiveAndBorrowedDecorator()throws Exception {
        try(var first=new ActionWriterIntegrationFixture(root.resolve("owner-first"),true);
            var other=new ActionWriterIntegrationFixture(root.resolve("owner-other"),true)) {
            var binding=binder(first,ReconciliationPendingBinding.HistoryQualification.unavailable());
            binding.requireOwner(first.writer,first.archive);byte[] before=first.ledgerBytes(),foreign=other.ledgerBytes();
            assertThrows(IOException.class,()->binding.requireOwner(other.writer,first.archive));
            assertThrows(IOException.class,()->binding.requireOwner(first.writer,other.archive));
            first.writer.locked(same->{assertThrows(IOException.class,()->binding.requireOwner(first.writer,first.archive.withSession(same)));return null;});
            assertArrayEquals(before,first.ledgerBytes());assertArrayEquals(foreign,other.ledgerBytes());
            assertEquals(0,first.nativeActionWrites());assertEquals(0,other.nativeActionWrites());
        }
    }
}
