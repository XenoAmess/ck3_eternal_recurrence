package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityEvent;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

class CanonicalContinuityTransactionsTest {
    @TempDir Path root;
    private static final TransitionAuthority ORDINARY = new TransitionAuthority() {
        @Override public String revalidate(ContinuityState state, Request request) { return request.identity(); }
        @Override public ContinuityState reduce(ContinuityState state, Request request) { return OriginalWindowReducer.reduce(state, request); }
    };
    static final class PairFixture {
        final WriterFixture initial; final Layout layout; final RollbackPair.Evidence evidence; final ContinuityWriter writer;
        PairFixture(Path root) throws IOException {
            initial = new WriterFixture(root); ObjectNode before = WriterFixture.state(); before.put("sequence", 1);
            before.put("last_settled_cycles", 3); before.put("last_settled_date_raw", 1048); before.put("status", "repair_required");
            before.putArray("unknown_actions").add("AUTO11558"); before.putObject("UNKNOWN").put("AUTO11558", "do_not_replay");
            before.put("next_control_sequence", 11559); before.putNull("pending_checkpoint");
            Files.write(initial.layout.snapshot(), ContinuityJson.canonical(before));
            Files.write(Path.of(initial.layout.anchor().path()), ContinuityJson.canonical(before));
            layout = new Layout(initial.layout.snapshot(), LedgerFiles.read(Path.of(initial.layout.anchor().path()), 65_536).pin().reference(), WriterFixture.MACHINE);
            Path proof = root.resolve("actual-recovery-proof.json"); Files.writeString(proof, "{\"proof\":\"source-bound-test\"}");
            ObjectNode basis = StrictJson.object(); basis.put("machine_id", WriterFixture.MACHINE); basis.put("completed_cycles", 1);
            ObjectNode origin = basis.putObject("origin"); origin.put("start_date_raw", 1000); origin.put("target_date_raw", 1000 + 10_958 * 24); origin.put("target_days", 10_958);
            ObjectNode frame = basis.putObject("frame"); frame.put("date_raw", 1000); frame.put("actor_character_id", 29829); frame.put("episode_run_id", "robert-episode");
            frame.put("snapshot_id", "native:1"); frame.put("revision", 1); frame.put("native_revision", 1);
            basis.putObject("refs").set("settled_full_response", LedgerFiles.read(proof, 65_536).pin().reference().toJson());
            ObjectNode current = frame.deepCopy(); current.put("date_raw", 1048); current.put("revision", 3); current.put("native_revision", 3);
            Pin proofPin = LedgerFiles.read(proof, 65_536).pin(); evidence = new RollbackPair.Evidence(proofPin.reference(),
                    ContinuityJson.canonical(basis), ContinuityJson.canonical(current), 3, List.of(proofPin), ContinuityJson.digest(basis));
            writer = new ContinuityWriter(layout, List.of(LedgerFiles.read(initial.source, 65_536).pin().reference()), ORDINARY, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.empty(), Optional.of((head, requested) -> evidence)), StorageWriteGuardTestSupport.forLayout(layout));
        }
    }
    private static List<byte[]> plannedEvents(RollbackPair.Plan plan) {
        List<byte[]> events = new ArrayList<>(); ContinuityState previous = plan.originalHead().state();
        for (RollbackPair.EventPlan event : List.of(plan.first(), plan.second())) {
            var envelope = new ContinuityEvent(event.committed().sequence(), "2026-10-24T00:00:00Z", event.request().kind(), event.request().details(),
                    event.request().identity(), ContinuityJson.digest(previous.toJson()), event.committed());
            events.add(ContinuityJson.canonical(envelope.toJson())); previous = event.committed();
        }
        return events;
    }
    @Test void originalPythonTwoReducersAndActualTransactionProduceSameHeadAndSingleIndexKeys() throws Exception {
        assertTrue(Platform.isWindows()); PairFixture fixture = new PairFixture(root.resolve("java"));
        RollbackPair.Plan plan = fixture.writer.previewRollback(fixture.evidence.proof());
        ObjectNode input = StrictJson.object(); input.set("before", plan.originalHead().state().toJson());
        input.set("basis", WriterContracts.object(fixture.evidence.savedBasis())); input.set("current_frame", WriterContracts.object(fixture.evidence.currentFrame()));
        input.put("current_cycles", fixture.evidence.currentCycles()); input.set("proof", fixture.evidence.proof().toJson());
        input.put("root", root.resolve("python").toString());
        String script = "import sys,json,hashlib\nfrom pathlib import Path\nfrom types import SimpleNamespace as N\nsys.path.insert(0,sys.argv[1])\nfrom tools.g2_saved_campaign import current_saved_continuity_v1 as c\nfrom tools.g2_saved_campaign import root_continuity_window as w\nfrom tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1,digest\nv=json.load(sys.stdin);r=Path(v['root']);r.mkdir();p=r/'ROOT-CONTINUITY-WINDOW.json';a=r/'anchor.json';w._atomic(p,v['before']);w._atomic(a,v['before']);p.with_suffix('.lock').touch();ledger=w.WindowLedger(p);ledger.events.mkdir()\ndef ref(z):return ExactRefV1(z['path'],z['bytes'],z['sha256'])\ndef frame(z):return N(**z,to_wire=lambda:z)\nb=v['basis'];basis=N(machine_id=b['machine_id'],completed_cycles=b['completed_cycles'],origin=N(**b['origin']),frame=frame(b['frame']),refs=N(settled_full_response=ref(b['refs']['settled_full_response'])))\nvalidated=N(evidence_ref=ref(v['proof']),saved_basis=basis,current_cycles=v['current_cycles'],current_frame=frame(v['current_frame']),discarded_cycles=v['current_cycles']-b['completed_cycles'],discarded_date_raw=v['current_frame']['date_raw']-b['frame']['date_raw'])\nanchor=ExactRefV1(str(a),a.stat().st_size,hashlib.sha256(a.read_bytes()).hexdigest());frontier=c.HistoricalRollbackFrontierV1(machine_id=b['machine_id'],canonical_path=str(p.resolve()),anchor_ref=anchor,head_event_ref=anchor,writer_source_ref=anchor,head_state=v['before'])\nplan=c.build_saved_rollback_pair_plan_v1(validated,frontier);store=c._OriginalRollbackPairStoreV1(canonical_path=p,anchor_ref=anchor,machine_id=b['machine_id'],reader=c.LocalContinuityReaderV1(),ledger=ledger,atomic=w._atomic)\nresult=c._commit_saved_rollback_pair_v1(store,plan,revalidate=lambda requested:plan,now_utc='2026-10-24T00:00:00Z')\nkeys=[c._source_key(plan.first),c._source_key(plan.second)]\nprint(json.dumps({'first':plan.first.reduced_state,'second':plan.second.reduced_state,'head':w.read_small(p),'writes':result.writes,'index_keys':keys,'validated_keys':[digest(k) for k in keys],'indices_exist':[(ledger.events/('source-'+k+'.json')).is_file() for k in keys]},sort_keys=True,ensure_ascii=False,separators=(',',':')))\n";
        Process child = new ProcessBuilder(WindowsWriterInteropTest.python(), "-B", "-X", "utf8", "-c", script,
                WindowsWriterInteropTest.repository().toString()).redirectErrorStream(true).start();
        try {
            child.getOutputStream().write(ContinuityJson.canonical(input)); child.getOutputStream().close();
            assertTrue(child.waitFor(20, TimeUnit.SECONDS)); byte[] output = child.getInputStream().readAllBytes(); assertEquals(0, child.exitValue(), new String(output, StandardCharsets.UTF_8));
            ObjectNode python = WriterContracts.object(output);
            assertTrue(ContinuityJson.same(python.get("first"), plan.first().reduced().toJson())); assertTrue(ContinuityJson.same(python.get("second"), plan.second().reduced().toJson()));
            assertEquals(python.get("index_keys"), python.get("validated_keys"), "basis.digest validates SHA text; it does not hash twice");
            assertTrue(python.get("indices_exist").get(0).booleanValue()); assertTrue(python.get("indices_exist").get(1).booleanValue());
            var committed = fixture.writer.commitRollback(plan); assertEquals(6, committed.writes()); assertEquals(python.get("writes").intValue(), committed.writes());
            assertTrue(ContinuityJson.same(python.get("head"), fixture.writer.locked(session -> session.head().state().toJson())));
        } finally { child.destroyForcibly(); }
    }
    @Test void eachOfSevenRealPersistenceBoundariesRecoversExactPairWithoutReplayingOrResettingPending() throws Exception {
        assertTrue(Platform.isWindows());
        for (int prefix = 0; prefix <= 6; prefix++) {
            PairFixture fixture = new PairFixture(root.resolve("prefix-" + prefix)); RollbackPair.Plan plan = fixture.writer.previewRollback(fixture.evidence.proof());
            List<byte[]> events = plannedEvents(plan); int operation = 0;
            for (RollbackPair.EventPlan event : List.of(plan.first(), plan.second())) {
                int offset = event == plan.first() ? 0 : 1;
                if (operation++ < prefix) StorageWriteGuardTestSupport.atomic(fixture.layout.event(event.committed().sequence()), events.get(offset), false);
                if (operation++ < prefix) StorageWriteGuardTestSupport.atomic(fixture.layout.snapshot(), event.committed().canonicalBytes(), true);
                if (operation++ < prefix) StorageWriteGuardTestSupport.atomic(fixture.layout.sourceIndex(event.request().sourceKey()),
                        ContinuityJson.canonical(new IndexRepair(fixture.layout.sourceIndex(event.request().sourceKey()), event.committed().sequence(), event.request().identity()).toJson()), false);
            }
            var committed = fixture.writer.commitRollback(plan); assertEquals(3, committed.committedSequence()); assertEquals(6 - prefix, committed.writes());
            ContinuityState head = fixture.writer.locked(session -> session.head().state()); assertEquals(1, head.settledCycles()); assertEquals(1000, head.settledDateRaw());
            assertEquals(plan.originalHead().state().toJson().get("pending_cycle"), head.toJson().get("pending_cycle")); assertEquals(11559, head.toJson().get("NEXT").intValue());
            assertEquals(0, fixture.writer.commitRollback(plan).writes());
        }
    }
    @Test void pairConflictsOrChangedProofRejectBeforeAnyNewReceipt() throws Exception {
        assertTrue(Platform.isWindows()); PairFixture fixture = new PairFixture(root.resolve("conflict")); RollbackPair.Plan plan = fixture.writer.previewRollback(fixture.evidence.proof());
        StorageWriteGuardTestSupport.atomic(fixture.layout.event(3), "{}".getBytes(StandardCharsets.UTF_8), false);
        assertThrows(RuntimeException.class, () -> fixture.writer.commitRollback(plan)); assertFalse(Files.exists(fixture.layout.event(2)));
        PairFixture changed = new PairFixture(root.resolve("proof")); RollbackPair.Plan old = changed.writer.previewRollback(changed.evidence.proof());
        Files.writeString(Path.of(changed.evidence.proof().path()), "{\"proof\":\"changed\"}");
        assertThrows(IOException.class, () -> changed.writer.commitRollback(old)); assertFalse(Files.exists(changed.layout.event(2)));
    }
    private static ContinuityWriter domainWriter(WriterFixture fixture, ImmutableArtifactStore archive) throws IOException {
        ExactRef source = LedgerFiles.read(fixture.source, 65_536).pin().reference();
        DomainBodies.Registration registration = new DomainBodies.Registration(DomainBodies.Slot.COUNCIL, "fixture.original-council/v1", 1_048_576, List.of(source),
                (head, previous, request, body) -> {
                    ObjectNode value = ContinuityJson.parseObject(body, 1_048_576);
                    StrictJson.require(StrictJson.text(value.get("schema")).equals("fixture.original-council/v1") && value.has("pending") && value.has("applied"), "actual full original body fields");
                    ObjectNode input = WriterContracts.object(request.producerInput()); StrictJson.require(input.get("explicit_initial_proof").isBoolean() && input.get("explicit_initial_proof").booleanValue(), "missing body does not grant initial clear");
                    return LedgerFiles.sha(ContinuityJson.canonical(value, 1_048_576));
                });
        return new ContinuityWriter(fixture.layout, List.of(source), ORDINARY, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(registration), Optional.of(archive), Optional.empty()), StorageWriteGuardTestSupport.forLayout(fixture.layout));
    }
    @Test void originalFullDomainBodyLivesOutsideSmallHeadAndMissingNeverMeansClear() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("domains")); Path archiveRoot = fixture.layout.snapshot().getParent().resolve("archive"); Files.createDirectory(archiveRoot);
        ImmutableArtifactStore archive = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archiveRoot, fixture.layout.lock(), 4_194_304), StorageWriteGuardTestSupport.forOriginalLock(fixture.layout.lock()));
        ContinuityWriter writer = domainWriter(fixture, archive);
        assertEquals(DomainBodies.Reason.UNIMPORTED, ((DomainBodies.Unavailable)writer.read(DomainBodies.Slot.COUNCIL)).reason());
        ObjectNode body = StrictJson.object(); body.put("schema", "fixture.original-council/v1"); body.putObject("pending").put("unknown_action", "retained"); body.putArray("applied"); body.put("large_original_history", "a".repeat(100_000));
        Path original = root.resolve("original-council.json"); Files.write(original, ContinuityJson.canonical(body, 1_048_576));
        ExactRef reference = LedgerFiles.read(original, 1_048_576).pin().reference();
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.COUNCIL, "fixture.original-council/v1", reference,
                "{\"explicit_initial_proof\":true}".getBytes(StandardCharsets.UTF_8), List.of(), "actual-original-council");
        var prepared = writer.previewImport(request); var receipt = writer.commitImport(prepared); assertEquals(Disposition.COMMITTED, receipt.disposition());
        DomainBodies.Available read = (DomainBodies.Available)writer.read(DomainBodies.Slot.COUNCIL);
        assertTrue(ContinuityJson.same(ContinuityJson.parseObject(read.canonicalBody(), 1_048_576), body));
        assertTrue(Files.size(fixture.layout.snapshot()) < 65_536); assertFalse(Files.readString(fixture.layout.snapshot()).contains("large_original_history"));
        assertEquals(Disposition.ALREADY_COMMITTED, writer.commitImport(prepared).disposition());
        assertEquals(DomainBodies.Reason.SLOT_UNREGISTERED, ((DomainBodies.Unavailable)writer.read(DomainBodies.Slot.CROWN)).reason());
        Files.writeString(original, "{}"); assertTrue(writer.read(DomainBodies.Slot.COUNCIL) instanceof DomainBodies.Available, "imported immutable full body does not depend on mutable sidecar");
    }
    @Test void importBodyIdentityAndActualInitializationProofAreRecheckedUnderWriterLock() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("guard")); Path archiveRoot = fixture.layout.snapshot().getParent().resolve("archive"); Files.createDirectory(archiveRoot);
        ContinuityWriter writer = domainWriter(fixture, new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archiveRoot, fixture.layout.lock(), 4_194_304), StorageWriteGuardTestSupport.forOriginalLock(fixture.layout.lock())));
        Path body = root.resolve("body.json"); Files.writeString(body, "{\"schema\":\"fixture.original-council/v1\",\"pending\":null,\"applied\":[]}");
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.COUNCIL, "fixture.original-council/v1", LedgerFiles.read(body, 65_536).pin().reference(), "{\"explicit_initial_proof\":true}".getBytes(StandardCharsets.UTF_8), List.of(), "one");
        var prepared = writer.previewImport(request); Path sameBytes = root.resolve("same-bytes.json"); Files.write(sameBytes, Files.readAllBytes(body)); Files.move(sameBytes, body, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        assertThrows(IOException.class, () -> writer.commitImport(prepared)); assertFalse(Files.exists(fixture.layout.event(1)));
        var invalid = new DomainBodies.ImportRequest(DomainBodies.Slot.COUNCIL, request.contractSchema(), LedgerFiles.read(body, 65_536).pin().reference(), "{\"explicit_initial_proof\":false}".getBytes(StandardCharsets.UTF_8), List.of(), "two");
        assertThrows(ContractViolationException.class, () -> writer.previewImport(invalid)); assertFalse(Files.exists(fixture.layout.event(1)));
    }
}
