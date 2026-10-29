package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual outbound bytes enter the production archive; none are recreated from a stored request. */
final class NativeOutcomeArchiveOutboundTest {
    private static final String MACHINE = "archive-outbound-fixture";
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    @TempDir Path temp;
    private final Set<StorageWriteGuardTestSupport> storageScopes = new java.util.LinkedHashSet<>();
    @AfterEach void closeStorageScopes() throws IOException {
        IOException failure = null;
        for (StorageWriteGuardTestSupport storage : storageScopes) {
            try { storage.close(); }
            catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        }
        storageScopes.clear();
        if (failure != null) throw failure;
    }
    private final class Fixture {
        final Layout layout; final ImmutableArtifactStore store; final ContinuityWriter writer;
        final NativeOutcomeArchive archive; final ExactRef source;
        Fixture(Path root) throws IOException {
            Files.createDirectory(root);
            String state = """
                    {"schema":"root.ck3.continuity-window/v1","machine_id":"archive-outbound-fixture","sequence":0,"window_id":1,
                    "status":"running","target_days":10958,"target_years":30,"calendar_year_days":365.25,"start_date_raw":1000,
                    "target_date_raw":263992,"last_settled_date_raw":1000,"last_settled_cycles":1,"manual_repair_count":1,
                    "automatic_recovery_count":0,"binding_lineage_count":0,"game_binding":{"pid":123,"creation_date":"2026-10-23T01:00:00Z"},
                    "latest_binding":null,"pending_cycle":{"stage":"auto_unsettled","auto_sequence":11558},"NEXT":11559}
                    """;
            byte[] initial = ContinuityJson.canonical((ObjectNode) StrictJson.parse(state.getBytes(StandardCharsets.UTF_8), 65536));
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "actual reviewed outbound fixture source", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            StorageWriteGuardTestSupport storage = StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            assertSame(storage, store.storageGuard());
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("no production ledger writes in archive fixture"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }
        G2Source source() { return new G2Source(MACHINE, NOW.toString(), "1.20.0.4", source); }
    }
    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name)); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static RawJson raw(String value) { return new RawJson(bytes(value)); }
    private static NativeActionPort.AckReceived ack(String id, Optional<NativeActionPort.OutboundPacket> outbound) throws IOException {
        byte[] packet = NativeWire.packet(bytes("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":true,\"result\":null}"));
        var reply = (NativeWire.CommandResult) NativeWire.decode(packet);
        return new NativeActionPort.AckReceived(id, true, reply.result().token().map(value -> new RawJson(value.value())), new RawJson(reply.payload().value()), packet, outbound);
    }
    private static ProposalLifecycle.ObservationIdentity observation() {
        return new ProposalLifecycle.ObservationIdentity(MACHINE, new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(1000)), "native-1", BigInteger.ONE, "episode-1"), 1);
    }
    private static ActionReceipt receipt(Fixture f, NativeRequest prepared, byte[] sent) throws IOException {
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, observation(), f.source(), "paused/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        var command = new ActionCommand("outbound-action", observation(), f.source(), "session-1", new OperationKey(prepared.step()), new OpportunityJson.Obj(Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(60));
        // This historical empty-basis guard tests byte binding only; it cannot grant a dispatch permission.
        var guard = new GuardEvidence(observation(), f.source(), "session-1", BigInteger.ONE, command.operation(), f.source, f.source, "fixture-authority", NOW, NOW.plusSeconds(60));
        var attempt = new ActionState.Attempt("actual-action", NOW, guard, prepared);
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.AckReceived(attempt, ack("actual-action", Optional.of(new NativeActionPort.OutboundPacket("actual-action", sent)))));
    }

    @Test void actualOutboundBytesRoundtripWithoutWhitespaceOrUInt64RewriteAndLegacyStaysV1() throws IOException {
        Fixture f = fixture("roundtrip");
        byte[] outbound = NativeWire.packet(bytes(" {\"type\":\"execute_step\", \"protocol_version\":1,\"request_id\":\"real-1\",\"step\":\"test-step\",\"expected_revision\":1,\"value\":18446744073709551615} \n"));
        var original = ack("real-1", Optional.of(new NativeActionPort.OutboundPacket("real-1", outbound)));
        ExactRef ref = f.archive.preserve(original); var restored = (NativeActionPort.AckReceived) f.archive.load(ref);
        assertEquals(original, restored); assertArrayEquals(outbound, restored.outbound().orElseThrow().originalPacket());
        ObjectNode metadata = (ObjectNode) StrictJson.parse(f.store.read(ref, StrictJson.EXPLICIT_MAX_BYTES), StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals("xar.native-dispatch-archive/v2", metadata.get("schema").textValue());
        ExactRef outboundRef = ExactRef.fromJson(metadata.get("outbound_packet_ref"));
        assertArrayEquals(outbound, f.writer.locked(session -> f.archive.readArtifact(session, outboundRef, WriterContracts.MAX_PIN_BYTES)));
        var legacy = ack("historical-1", Optional.empty()); ExactRef legacyRef = f.archive.preserve(legacy);
        assertEquals(legacy, f.archive.load(legacyRef));
        assertEquals("xar.native-dispatch-archive/v1", StrictJson.parse(f.store.read(legacyRef, StrictJson.EXPLICIT_MAX_BYTES), StrictJson.EXPLICIT_MAX_BYTES).get("schema").textValue());
    }
    @Test void claimedOutboundIdMustMatchTheActualDecodedExecutePacketBeforeAnyPublication() throws IOException {
        Fixture f = fixture("wrong-id");
        byte[] sent = NativeWire.execute("different-id", "test-step", BigInteger.ONE, bytes("{}"));
        var original = ack("claimed-id", Optional.of(new NativeActionPort.OutboundPacket("claimed-id", sent)));
        assertThrows(UncheckedIOException.class, () -> f.archive.preserve(original)); assertEquals(0, f.store.retainedNativeBytes());
        byte[] wrongType = NativeWire.packet(bytes("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"claimed-id\",\"step\":\"test-step\",\"expected_revision\":true}"));
        var wrong = ack("claimed-id", Optional.of(new NativeActionPort.OutboundPacket("claimed-id", wrongType)));
        assertThrows(UncheckedIOException.class, () -> f.archive.preserve(wrong)); assertEquals(0, f.store.retainedNativeBytes());
    }
    @Test void receiptBindsActualStepExactAdditionalValuesAndGuardedRevision() throws IOException {
        Fixture f = fixture("binding"); byte[] ledger = Files.readAllBytes(f.layout.snapshot());
        NativeRequest prepared = new NativeRequest("test-step", Optional.empty(), raw("{\"value\":1,\"missing\":null,\"empty\":[]}"));
        byte[] sent = NativeWire.execute("actual-action", prepared.step(), BigInteger.ONE, bytes(" {\"empty\":[], \"missing\":null,\"value\":1} "));
        var original = receipt(f, prepared, sent); assertEquals(original, f.archive.loadReceipt(f.archive.preserveReceipt(original)));
        var wrongFields = receipt(f, prepared, NativeWire.execute("actual-action", prepared.step(), BigInteger.ONE, bytes("{\"value\":1,\"missing\":null,\"empty\":{}}")));
        assertThrows(UncheckedIOException.class, () -> f.archive.preserveReceipt(wrongFields));
        var wrongStep = receipt(f, prepared, NativeWire.execute("actual-action", "different-step", BigInteger.ONE, prepared.additionalFields().bytes()));
        assertThrows(UncheckedIOException.class, () -> f.archive.preserveReceipt(wrongStep));
        var wrongRevision = receipt(f, prepared, NativeWire.execute("actual-action", prepared.step(), BigInteger.TWO, prepared.additionalFields().bytes()));
        assertThrows(UncheckedIOException.class, () -> f.archive.preserveReceipt(wrongRevision));
        assertArrayEquals(ledger, Files.readAllBytes(f.layout.snapshot()));
    }
    @Test void explicitSnapshotRevisionIsValidatedAndNormalizedWithoutLosingIntegerType() throws IOException {
        Fixture f = fixture("snapshot-revision");
        NativeRequest prepared = new NativeRequest("test-step", Optional.empty(), raw("{\"expected_snapshot_revision\":1,\"value\":7}"));
        byte[] sent = NativeWire.executePrivateQuery("actual-action", prepared.step(), BigInteger.ONE, prepared.additionalFields().bytes());
        var original = receipt(f, prepared, sent); assertEquals(original, f.archive.loadReceipt(f.archive.preserveReceipt(original)));
        NativeRequest wrongPrepared = new NativeRequest("test-step", Optional.empty(), raw("{\"expected_snapshot_revision\":1.0,\"value\":7}"));
        var wrong = receipt(f, wrongPrepared, sent);
        assertThrows(UncheckedIOException.class, () -> f.archive.preserveReceipt(wrong));
    }
    @Test void actualLargePreparedAndOutboundBodiesUseFullLaneWithoutChangingSmallArchiveMetadata() throws IOException {
        Fixture f=fixture("large-fields");byte[] ledger=Files.readAllBytes(f.layout.snapshot());String payload="x".repeat(1_200_000);
        NativeRequest prepared=new NativeRequest("test-step",Optional.empty(),raw("{\"value\":1,\"missing\":null,\"empty\":[],\"payload\":\""+payload+"\"}"));
        assertTrue(prepared.additionalFields().bytes().length>StrictJson.EXPLICIT_MAX_BYTES);
        byte[] sent=NativeWire.execute("actual-action",prepared.step(),BigInteger.ONE,prepared.additionalFields().bytes());
        var original=receipt(f,prepared,sent);ExactRef kept=f.archive.preserveReceipt(original);
        assertEquals(original,f.archive.loadReceipt(kept));assertTrue(kept.bytes()<StrictJson.EXPLICIT_MAX_BYTES);
        var missingAndWrongType=receipt(f,prepared,NativeWire.execute("actual-action",prepared.step(),BigInteger.ONE,
                bytes("{\"value\":true,\"empty\":[],\"payload\":\""+payload+"\"}")));
        assertThrows(UncheckedIOException.class,()->f.archive.preserveReceipt(missingAndWrongType));
        byte[] duplicate=NativeWire.packet(bytes("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"actual-action\",\"step\":\"test-step\",\"expected_revision\":1,\"value\":1,\"value\":1,\"payload\":\""+payload+"\"}"));
        var repeated=receipt(f,prepared,duplicate);assertThrows(RuntimeException.class,()->f.archive.preserveReceipt(repeated));
        assertArrayEquals(ledger,Files.readAllBytes(f.layout.snapshot()));assertEquals(1_048_576,StrictJson.EXPLICIT_MAX_BYTES);
    }
    @Test void readerRejectsCorruptOutboundOriginalAndPreservesTheCorruptionForDiagnosis() throws IOException {
        Fixture f = fixture("corrupt-outbound");
        byte[] sent = NativeWire.execute("real-1", "test-step", BigInteger.ONE, bytes("{}"));
        var original = ack("real-1", Optional.of(new NativeActionPort.OutboundPacket("real-1", sent)));
        ExactRef ref = f.archive.preserve(original);
        ObjectNode metadata = (ObjectNode) StrictJson.parse(f.store.read(ref, StrictJson.EXPLICIT_MAX_BYTES), StrictJson.EXPLICIT_MAX_BYTES);
        Path outbound = Path.of(ExactRef.fromJson(metadata.get("outbound_packet_ref")).path());
        Files.write(outbound, new byte[] {9, 8, 7});
        assertThrows(UncheckedIOException.class, () -> f.archive.load(ref));
        assertArrayEquals(new byte[] {9, 8, 7}, Files.readAllBytes(outbound));
    }
}
