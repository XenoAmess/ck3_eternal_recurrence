package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual canonical writer/archive closure with controlled software native edges; no live Game qualification. */
final class ReconciliationIdentityTest {
    @TempDir Path root;
    private static ReconciliationPendingBinding binder(ActionWriterIntegrationFixture f){
        return new ReconciliationPendingBinding(f.writer,f.archive,f.archive::readArtifact);
    }
    private static ObservationIdentity changed(ObservationIdentity original,Consumer<ObjectNode> mutation){
        ObjectNode row=ProposalLifecycleCodec.observation(original);mutation.accept(row);return ProposalLifecycleCodec.decodeObservation(row);
    }
    private static ReconciliationIdentity identity(ActionWriterIntegrationFixture f,ActionReceipt pending)throws IOException{
        return f.writer.locked(session->f.archive.inSession(session,archive->{
            ActionState.Attempt attempt=ActionTransitions.attempt(pending.state()).orElseThrow();
            ExactRef driver=archive.preserveMaterial(raw("{\"fixture_only\":\"same-full-driver-custody\"}"));
            ExactRef heartbeat=archive.preserveMaterial(raw("{\"fixture_only\":\"heartbeat-raw-custody\"}"));
            ExactRef manifest=archive.preserveMaterial(raw("{\"fixture_only\":\"observation-manifest-custody\"}"));
            ExactRef qualification=archive.preserveMaterial(raw("{\"fixture_only\":\"source-qualification-custody\"}"));
            // These four fixture documents exercise only immutable raw custody.
            // Production old-guard-to-Driver/source/native semantics are mandatory readiness callbacks.
            var evidence=new ReconciliationIdentity.Evidence(attempt.guard().nativeEvidence(),attempt.guard().capabilityEvidence(),
                    heartbeat,manifest,driver,qualification);
            return ReconciliationIdentity.fromCanonical(pending,pending.command().before(),pending.command().source(),
                    pending.command().sessionId(),attempt.guard().connectionGeneration(),archive.receiptReferenceOf(pending),
                    driver,evidence,Instant.now());
        }));
    }
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static Set<Path> files(Path directory)throws IOException{
        try(var stream=Files.walk(directory)){return stream.filter(Files::isRegularFile).map(p->p.toAbsolutePath().normalize()).collect(java.util.stream.Collectors.toUnmodifiableSet());}
    }
    @Test void actualUnknownCanonicalAttemptAndEvidenceVerifyReadOnlyUnderTheOriginalSession()throws Exception{
        try(var f=new ActionWriterIntegrationFixture(root.resolve("canonical"),true)){
            ActionReceipt pending=f.coordinator.execute(f.command("reconcile-original"));
            assertInstanceOf(ActionState.Unknown.class,pending.state());assertFalse(pending.settled());assertEquals(1,f.nativeActionWrites());
            var identity=identity(f,pending);byte[] before=f.ledgerBytes();long sequence=f.sequence();
            Set<Path> originals=files(f.root);int reads=f.nativeReadWrites(),packets=f.nativePacketReads();
            f.writer.locked(session->{
                assertEquals(ActionTransitions.attempt(pending.state()).orElseThrow(),binder(f).requirePending(session,pending));
                binder(f).verify(session,identity);return null;
            });
            assertArrayEquals(before,f.ledgerBytes());assertEquals(sequence,f.sequence());assertEquals(originals,files(f.root));
            assertEquals(1,f.nativeActionWrites());assertEquals(reads,f.nativeReadWrites());assertEquals(packets,f.nativePacketReads());
            assertEquals(pending,f.reopenAndReturnExisting(pending.command()));
        }
    }
    @Test void supersededAckAndAnOrphanReceiptCannotBorrowCurrentUnknownMembership()throws Exception{
        try(var f=new ActionWriterIntegrationFixture(root.resolve("old-ack"),false)){
            ActionReceipt current=f.coordinator.execute(f.command("latest-original"));
            assertInstanceOf(ActionState.Unknown.class,current.state());
            f.writer.locked(session->f.archive.inSession(session,archive->{
                var head=assertDoesNotThrow(session::head);
                var latest=archive.loadRecord(ContinuityActionJournal.recordHead(head.state()).orElseThrow());
                ActionReceipt ack=archive.loadRecord(latest.previous().orElseThrow()).receipt();
                assertInstanceOf(ActionState.AckReceived.class,ack.state());
                assertThrows(IOException.class,()->binder(f).requirePending(session,ack));
                ActionCommand command=current.command();
                ActionCommand other=new ActionCommand("orphan-original",command.origin(),command.source(),command.sessionId(),
                        command.operation(),command.arguments(),command.expectation(),command.claims(),command.deadline());
                ActionReceipt orphan=new ActionReceipt(1,current.sequence(),other,ActionCodec.bodySha256(other),current.state());
                archive.preserveReceipt(orphan);
                assertThrows(IOException.class,()->binder(f).requirePending(session,orphan));
                assertEquals(current,assertDoesNotThrow(()->ContinuityActionJournal.lookup(session.head().state(),command.actionId(),archive).orElseThrow()));
                return null;
            }));
            assertEquals(1,f.nativeActionWrites());
        }
    }
    @Test void originalPrimitiveIdentityRoundTripsAndDiagnosticTimeCannotChangeGuardScope()throws Exception{
        try(var f=new ActionWriterIntegrationFixture(root.resolve("identity"),true)){
            var pending=f.coordinator.execute(f.command("identity-original"));var original=identity(f,pending);
            var encoded=ReconciliationIdentityCodec.encode(original);
            assertEquals(original,ReconciliationIdentityCodec.decode(encoded));assertEquals(64,original.bindingSha256().length());
            var later=new ReconciliationIdentity(original.factual(),original.source(),original.sessionId(),original.connectionGeneration(),
                    original.pending(),original.evidence(),original.observedAt().plusSeconds(1));
            assertTrue(original.sameGuardFrame(later));assertFalse(original.sameGuardFrame(null));
            var advanced=changed(original.factual(),row->((ObjectNode)row.get("frame")).put("snapshot_id","another-factual-snapshot"));
            var another=new ReconciliationIdentity(advanced,original.source(),original.sessionId(),original.connectionGeneration(),
                    original.pending(),original.evidence(),original.observedAt());
            assertFalse(original.sameGuardFrame(another));
            ObjectNode extra=encoded.deepCopy();extra.put("unknown_extra_field",true);
            assertThrows(RuntimeException.class,()->ReconciliationIdentityCodec.decode(extra));
            ObjectNode wrong=encoded.deepCopy();wrong.put("connection_generation",true);
            assertThrows(RuntimeException.class,()->ReconciliationIdentityCodec.decode(wrong));
        }
    }
    @Test void dataFactoryRejectsUnknownWithoutAttemptIntentSettledSourceSessionAndConnectionDrift()throws Exception{
        try(var f=new ActionWriterIntegrationFixture(root.resolve("factory"),false)){
            ActionReceipt pending=f.coordinator.execute(f.command("factory-original"));var original=identity(f,pending);
            var attempt=ActionTransitions.attempt(pending.state()).orElseThrow();
            List<ActionState> forbidden=List.of(new ActionState.IntentDurable(),
                    new ActionState.Unknown(Optional.empty(),Optional.empty(),"no original primitive request",List.of()),
                    new ActionState.Settled(attempt,ActionTransitions.dispatch(pending.state()).orElseThrow(),
                            new ActionState.Rejected(attempt.requestId(),"fixture-only-terminal",attempt.guard().nativeEvidence())));
            for(ActionState state:forbidden){
                var invalid=new ActionReceipt(1,pending.sequence(),pending.command(),pending.bodySha256(),state);
                assertThrows(RuntimeException.class,()->factory(invalid,original,original.source(),original.sessionId(),original.connectionGeneration(),original.factual()));
            }
            var foreignSource=new G2Source(original.source().machineId(),original.source().observedAtUtc(),"changed-source-build",original.source().sourceRef());
            assertThrows(RuntimeException.class,()->factory(pending,original,foreignSource,original.sessionId(),original.connectionGeneration(),original.factual()));
            assertThrows(RuntimeException.class,()->factory(pending,original,original.source(),"another-session",original.connectionGeneration(),original.factual()));
            assertThrows(RuntimeException.class,()->factory(pending,original,original.source(),original.sessionId(),original.connectionGeneration().add(BigInteger.ONE),original.factual()));
            Instant retainedPublication=attempt.guard().observedAt();
            var retainedTime=ReconciliationIdentity.fromCanonical(pending,original.factual(),original.source(),original.sessionId(),
                    original.connectionGeneration(),original.pending().originalReceipt(),original.pending().originalBeforeDriver(),original.evidence(),retainedPublication);
            assertEquals(retainedPublication,retainedTime.observedAt(),"cached raw SEM publication time is retained without inventing query freshness");
            assertEquals(1,f.nativeActionWrites());
        }
    }
    private static ReconciliationIdentity factory(ActionReceipt pending,ReconciliationIdentity basis,G2Source source,String session,BigInteger generation,ObservationIdentity factual){
        return ReconciliationIdentity.fromCanonical(pending,factual,source,session,generation,basis.pending().originalReceipt(),
                basis.pending().originalBeforeDriver(),basis.evidence(),basis.observedAt());
    }
    @Test void changedGameBirthActorEpisodeMachineAndRegressingNativeDateCannotAcquireIdentity()throws Exception{
        try(var f=new ActionWriterIntegrationFixture(root.resolve("subject"),true)){
            var pending=f.coordinator.execute(f.command("subject-original"));var basis=identity(f,pending);
            List<Consumer<ObjectNode>> mutations=List.of(
                row->row.put("machine_id","another-machine"),
                row->((ObjectNode)row.get("game")).put("creation_filetime","9007199254740994"),
                row->((ObjectNode)row.get("frame")).put("played_character_id","74"),
                row->((ObjectNode)row.get("frame")).put("episode_run_id","another-episode"),
                row->((ObjectNode)row.get("frame")).put("native_revision","0"),
                row->((ObjectNode)row.get("frame")).put("date_raw","999"),
                row->row.put("observation_version",basis.factual().observationVersion()+1));
            for(Consumer<ObjectNode> mutation:mutations)assertThrows(RuntimeException.class,()->{
                var factual=changed(basis.factual(),mutation);
                factory(pending,basis,basis.source(),basis.sessionId(),basis.connectionGeneration(),factual);
            });
            byte[] snapshot=f.ledgerBytes();var invalid=new ReconciliationIdentity.Pending(basis.pending().actionId(),basis.pending().bodySha256(),
                    "another-request",basis.pending().originalBefore(),basis.pending().originalReceipt(),basis.pending().originalBeforeDriver());
            var substituted=new ReconciliationIdentity(basis.factual(),basis.source(),basis.sessionId(),basis.connectionGeneration(),invalid,basis.evidence(),basis.observedAt());
            f.writer.locked(session->{assertThrows(IOException.class,()->binder(f).verify(session,substituted));return null;});
            assertArrayEquals(snapshot,f.ledgerBytes());assertEquals(1,f.nativeActionWrites());
        }
    }
    @Test void historicalReadProofSurvivesARealLaterUnknownButCannotAcquireLiveScope()throws Exception{
        try(var f=new ActionWriterIntegrationFixture(root.resolve("historical-scope"),false)){
            ActionReceipt latest=f.coordinator.execute(f.command("historical-scope-original"));
            ActionReceipt originalAck=f.writer.locked(session->f.archive.inSession(session,archive->{
                var current=archive.loadRecord(ContinuityActionJournal.recordHead(assertDoesNotThrow(session::head).state()).orElseThrow());
                return archive.loadRecord(current.previous().orElseThrow()).receipt();
            }));
            assertInstanceOf(ActionState.AckReceived.class,originalAck.state());assertTrue(originalAck.sequence()<latest.sequence());
            ReconciliationIdentity archived=identity(f,originalAck);byte[] ledger=f.ledgerBytes();Set<Path> originals=files(f.root);
            int reads=f.nativeReadWrites(),packets=f.nativePacketReads();
            f.writer.locked(session->{
                assertThrows(IOException.class,()->binder(f).requirePending(session,originalAck));
                assertThrows(IOException.class,()->binder(f).verify(session,archived));
                binder(f).verifyHistorical(session,archived);return null;
            });
            assertArrayEquals(ledger,f.ledgerBytes());assertEquals(originals,files(f.root));
            assertEquals(reads,f.nativeReadWrites());assertEquals(packets,f.nativePacketReads());assertEquals(1,f.nativeActionWrites());
        }
    }
    @Test void cachedRawPublicationTimeIsPreservedAndNeverCreatesNativeQueryFreshness()throws Exception{
        try(var f=new ActionWriterIntegrationFixture(root.resolve("cached-raw-time"),true)){
            var pending=f.coordinator.execute(f.command("cached-time-original"));var basis=identity(f,pending);
            var attempt=ActionTransitions.attempt(pending.state()).orElseThrow();
            Instant originalRawTime=attempt.guard().observedAt();
            assertFalse(originalRawTime.isAfter(attempt.submittedAt()),"actual original guard publication precedes the submitted primitive");
            int reads=f.nativeReadWrites(),packets=f.nativePacketReads();byte[] ledger=f.ledgerBytes();
            var retained=ReconciliationIdentity.fromCanonical(pending,basis.factual(),basis.source(),basis.sessionId(),
                    basis.connectionGeneration(),basis.pending().originalReceipt(),basis.pending().originalBeforeDriver(),basis.evidence(),originalRawTime);
            assertEquals(originalRawTime,retained.observedAt());
            assertEquals(retained,ReconciliationIdentityCodec.decode(ReconciliationIdentityCodec.encode(retained)));
            assertThrows(NullPointerException.class,()->ReconciliationIdentity.fromCanonical(pending,basis.factual(),basis.source(),basis.sessionId(),
                    basis.connectionGeneration(),basis.pending().originalReceipt(),basis.pending().originalBeforeDriver(),basis.evidence(),null));
            assertEquals(reads,f.nativeReadWrites());assertEquals(packets,f.nativePacketReads());assertArrayEquals(ledger,f.ledgerBytes());
            assertEquals(1,f.nativeActionWrites(),"a DATA constructor neither queries nor repeats the unresolved primitive");
        }
    }
    @Test void tamperedOriginalAndAnUnavailableOriginalsPortFailWithoutQueriesOrWrites()throws Exception{
        try(var f=new ActionWriterIntegrationFixture(root.resolve("tamper"),true)){
            var pending=f.coordinator.execute(f.command("tamper-original"));var identity=identity(f,pending);
            byte[] ledger=f.ledgerBytes();int reads=f.nativeReadWrites();Set<Path> baseline=files(f.root);
            f.writer.locked(session->{
                var unavailable=new ReconciliationPendingBinding(f.writer,f.archive,(same,ref,limit)->{throw new IOException("actual original port unavailable");});
                assertThrows(IOException.class,()->unavailable.requirePending(session,pending));return null;
            });
            assertArrayEquals(ledger,f.ledgerBytes());assertEquals(baseline,files(f.root));
            Files.writeString(Path.of(identity.evidence().observationManifest().path()),"{\"tampered\":true}");
            f.writer.locked(session->{assertThrows(IOException.class,()->binder(f).verify(session,identity));return null;});
            assertArrayEquals(ledger,f.ledgerBytes());assertEquals(reads,f.nativeReadWrites());assertEquals(1,f.nativeActionWrites());
        }
    }
}

