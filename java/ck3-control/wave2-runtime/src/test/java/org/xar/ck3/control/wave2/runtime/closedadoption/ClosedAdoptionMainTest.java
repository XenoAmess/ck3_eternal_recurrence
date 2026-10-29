package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedProofReadTicket;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** The operational Main is entered, but a deliberate pre-measurement guard always refuses the synthetic ticket. */
class ClosedAdoptionMainTest {
    private record Fixture(Path root, ObjectNode invocation) { }
    private static Path repo() {
        String explicit = System.getProperty("xar.repo");
        if (explicit == null || explicit.isBlank()) { explicit = System.getenv("XAR_REPO_ROOT"); }
        Path current = Path.of(explicit == null || explicit.isBlank() ? System.getProperty("user.dir") : explicit).toAbsolutePath();
        for (int count = 0; count < 6 && current != null; count++, current = current.getParent()) {
            if (Files.isRegularFile(current.resolve("tools/g2_saved_campaign/current_saved_continuity_v1.py"))) { return current; }
        }
        throw new IllegalStateException("UNAVAILABLE: set xar.repo or XAR_REPO_ROOT to the actual source checkout");
    }
    private static ExactRef write(Path path, byte[] raw) throws IOException {
        Files.write(path, raw); return new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw));
    }
    private static ExactRef source(Path repo, String name) throws IOException {
        Path path = repo.resolve("tools/g2_saved_campaign").resolve(name);
        byte[] raw;
        try (var input = Files.newInputStream(path)) { raw = input.readNBytes(2 * 1024 * 1024 + 1); }
        assertTrue(raw.length > RecoveryEvidence.MAX_BYTES && raw.length <= 2 * 1024 * 1024,
                "actual non-JSON module requires its independent source budget");
        return new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw));
    }
    private static Fixture fixture() throws IOException {
        Path scratch = Path.of(System.getProperty("xar.scratch","D:/codex-ck3-demos/2026-10-22-java-phase1/scratch")).toAbsolutePath();
        Files.createDirectories(scratch); Path root = Files.createTempDirectory(scratch,"closedadoption-main-");
        Path repository = repo(), canonical = root.resolve("fixture-canonical/ROOT-CONTINUITY-WINDOW.json");
        Files.createDirectories(canonical.getParent()); Files.createDirectory(root.resolve("metadata"));
        Files.writeString(canonical,"{}\n",StandardCharsets.UTF_8);
        ExactRef metadata = write(root.resolve("synthetic-metadata.json"),"{}".getBytes(StandardCharsets.UTF_8));
        String machine = WindowsJobProcess.currentMachineId(); Instant now = Instant.now();
        ObjectNode request = StrictJson.object(); request.put("schema","xar.java-closed-partial-adoption-request/v1");
        request.put("machine_id",machine); request.put("observed_at_utc",now.toString());
        ObjectNode inputs = request.putObject("inputs");
        for (String field : List.of("predecessor","saved_basis","prior_qualification","full_request","failed_full","auto_request","failed_auto","raw_state","raw_governance","actual_next")) { inputs.set(field,metadata.toJson()); }
        ObjectNode closed = request.putObject("closed");
        for (String field : List.of("sdk","game_exit","supervisor","recording","capture","screen")) { closed.set(field,metadata.toJson()); }
        var tasks = request.putArray("tasks");
        for (String role : List.of("SUPERVISOR","FEEDER","DISPLAY")) {
            ObjectNode task = tasks.addObject(); task.put("role",role);
            for (String field : List.of("spec","closed","unregistered")) { task.set(field,metadata.toJson()); }
        }
        ObjectNode cycle = request.putArray("cycles").addObject();
        for (String field : List.of("auto","metrics","event","ordinary_credit","auto_after","metrics_after","before_plan")) { cycle.set(field,metadata.toJson()); }
        cycle.putNull("readonly_save_skip");
        ObjectNode business = request.putObject("business");
        for (String field : List.of("saved_seed","saved_governance","cold_bound","opening_semantic","opening_capabilities","classifier_pin","classifier_source","queue_source","capture_probe","capture_cleanup")) { business.set(field,metadata.toJson()); }
        request.put("canonical_path",canonical.toString()); request.put("metadata_root",root.resolve("metadata").toString());
        request.set("writer_source",metadata.toJson());
        ExactRef requestRef = write(root.resolve("synthetic-request.json"),StrictJson.canonical(request));
        ObjectNode ticket = StrictJson.object(); ticket.put("schema",SavedProofReadTicket.SCHEMA); ticket.put("machine_id",machine);
        ticket.put("nonce","0".repeat(32)); ticket.put("observed_at_utc",now.toString()); ticket.put("review_at_utc",now.plusSeconds(180).toString());
        ticket.put("driver_path",root.resolve("driver-state.json").toString());
        FileStatIdentity identity = new FileStatIdentity(BigInteger.ONE,"1","1"); ticket.set("driver_identity",identity.toJson());
        ticket.set("save_ref",new ExactRef(root.resolve("save games/xar_checkpoint.ck3").toString(),1,"0".repeat(64)).toJson());
        ticket.set("save_identity",identity.toJson()); Path sdk = root.resolve("sdk"); ticket.put("sdk_root",sdk.toString());
        ticket.set("sdk_freeze_ref",metadata.toJson());
        ticket.set("validator_ref",new ExactRef(sdk.resolve("xar_autoplayer/cold_checkpoint_validator.py").toString(),1,"0".repeat(64)).toJson());
        ticket.put("pipe_name","synthetic-never-opened"); Path python = repository.resolve("tools/.venv/Scripts/python.exe");
        ticket.put("python_executable",python.toString()); ticket.put("output_root",root.toString()); ticket.put("max_driver_bytes",1);
        ticket.put("physical_driver_reads",1); ticket.put("original_sdk_save_hash_calls",1); ticket.put("job_memory_limit_bytes",1024); ticket.put("timeout_seconds",60);
        ExactRef ticketRef = write(root.resolve("synthetic-ticket.json"),StrictJson.canonical(ticket));
        ObjectNode invocation = StrictJson.object(); invocation.put("schema","xar.closed-partial-temporary-invocation/v1"); invocation.put("machine_id",machine);
        invocation.set("adoption_request_ref",requestRef.toJson()); invocation.set("sdk_read_ticket_ref",ticketRef.toJson());
        invocation.put("repo",repository.toString()); invocation.put("python_executable",python.toString()); invocation.put("output_root",root.toString());
        invocation.put("memory_limit_bytes",1024); invocation.put("timeout_seconds",60); invocation.put("lease_deadline_utc",now.plusSeconds(120).toString());
        invocation.put("minimum_free_bytes",1); invocation.put("maximum_output_bytes",8*1024*1024);
        invocation.set("mechanical_source_ref",source(repository,"current_saved_continuity_v1.py").toJson());
        invocation.set("cold_owner_source_ref",source(repository,"root_current_saved_campaign_cold_owner_v1.py").toJson());
        return new Fixture(root,invocation);
    }
    private static ContractViolationException reject(Fixture fixture, ObjectNode invocation) throws IOException {
        Path file = Files.createTempFile(fixture.root(),"invocation-",".json");
        ExactRef ref = write(file,StrictJson.canonical(invocation));
        ContractViolationException error = assertThrows(ContractViolationException.class,() -> ClosedAdoptionMain.runTemporary(ref));
        assertFalse(Files.exists(fixture.root().resolve("sdk-"+"0".repeat(32)+".consumed.json")));
        assertFalse(Files.exists(fixture.root().resolve("closed-adoption-result.json")));
        return error;
    }
    @Test void realEntryAcceptsBothOriginalPythonSourcesBeforeTheDeliberatePreMeasurementGuard() throws Exception {
        Fixture fixture = fixture();
        assertEquals("temporary canonical starts at the exact immutable predecessor",reject(fixture,fixture.invocation()).getMessage());
    }
    @Test void realEntryRejectsWrongSourceHashesAndLengthsForBothModules() throws Exception {
        Fixture fixture = fixture();
        for (String field : List.of("mechanical_source_ref","cold_owner_source_ref")) {
            ObjectNode hash = fixture.invocation().deepCopy(); ((ObjectNode)hash.get(field)).put("sha256","0".repeat(64));
            assertEquals("exact original input length and SHA required",reject(fixture,hash).getMessage());
            ObjectNode length = fixture.invocation().deepCopy(); ObjectNode ref = (ObjectNode)length.get(field); ref.put("bytes",ref.get("bytes").longValue()-1);
            assertEquals("exact original input length and SHA required",reject(fixture,length).getMessage());
            ObjectNode oversized = fixture.invocation().deepCopy(); ((ObjectNode)oversized.get(field)).put("bytes",2*1024*1024+1);
            assertEquals("bounded exact Root parameter/source",reject(fixture,oversized).getMessage());
        }
    }
    @Test void jsonMetadataStillRequiresAnObjectAndPersistenceNamesAreRejectedBeforeReading() throws Exception {
        Fixture fixture = fixture();
        ExactRef array = write(fixture.root().resolve("not-an-object.json"),"[]".getBytes(StandardCharsets.UTF_8));
        for (String field : List.of("adoption_request_ref","sdk_read_ticket_ref")) {
            ObjectNode invalid = fixture.invocation().deepCopy(); invalid.set(field,array.toJson());
            assertEquals("complete original JSON object required",reject(fixture,invalid).getMessage());
        }
        for (String name : List.of("driver-state.json","forbidden.ck3","forbidden.sav")) {
            ExactRef forbidden = new ExactRef(fixture.root().resolve(name).toString(),1,"0".repeat(64));
            ContractViolationException error = assertThrows(ContractViolationException.class,() -> ClosedAdoptionMain.runTemporary(forbidden));
            assertEquals("CLI only reads small metadata/source inputs",error.getMessage());
            assertFalse(Files.exists(Path.of(forbidden.path())));
        }
    }
    @Test void operationalRootEntryValidatesReviewBeforeTheSingleMeasurementAndKeepsTheTemporaryGuard() throws Exception {
        Fixture fixture = fixture();
        ExactRef requestRef = ExactRef.fromJson(fixture.invocation().get("adoption_request_ref"));
        ClosedAdoptionRequest request = ClosedAdoptionRequest.decode(Files.readAllBytes(Path.of(requestRef.path())));
        Path productionRoot = Files.createTempDirectory(fixture.root().getParent(),"root-main-production-fixture-");
        ExactRef head = write(productionRoot.resolve("ROOT-CONTINUITY-WINDOW.json"),"{}".getBytes(StandardCharsets.UTF_8));
        var identities = new WindowsSavedProofIdentityReader();
        var plan = new ClosedAdoptionReview.Plan(fixture.invocation().get("machine_id").textValue(),
                ExactRef.fromJson(fixture.invocation().get("sdk_read_ticket_ref")),"0".repeat(32),
                new OriginalWriterTransaction.Target(Path.of(head.path()),request.writerSource()),head,
                identities.stat(Path.of(head.path())),Instant.parse(fixture.invocation().get("lease_deadline_utc").textValue()));
        ExactRef invocation = write(fixture.root().resolve("root-invocation.json"),StrictJson.canonical(fixture.invocation()));
        ExactRef valid = write(fixture.root().resolve("root-review-plan.json"),StrictJson.canonical(plan.toJson()));
        ContractViolationException guard = assertThrows(ContractViolationException.class,() -> ClosedAdoptionMain.runRootTwoStage(invocation,valid));
        assertEquals("temporary canonical starts at the exact immutable predecessor",guard.getMessage());
        var wrong = new ClosedAdoptionReview.Plan(plan.machineId(),plan.ticketRef(),"1".repeat(32),plan.target(),plan.predecessorRef(),plan.predecessorIdentity(),plan.deadlineUtc());
        ExactRef wrongRef = write(fixture.root().resolve("root-review-wrong-nonce.json"),StrictJson.canonical(wrong.toJson()));
        assertEquals("Root plan binds the actual ticket nonce, machine and earliest existing lease",
                assertThrows(ContractViolationException.class,() -> ClosedAdoptionMain.runRootTwoStage(invocation,wrongRef)).getMessage());
        Files.writeString(fixture.root().resolve("root-review-approval.json"),"{}",StandardCharsets.UTF_8);
        assertEquals("Root review paths must be absent before the temporary stage",
                assertThrows(ContractViolationException.class,() -> ClosedAdoptionMain.runRootTwoStage(invocation,valid)).getMessage());
        assertFalse(Files.exists(fixture.root().resolve("sdk-"+"0".repeat(32)+".consumed.json")));
        assertFalse(Files.exists(fixture.root().resolve("root-review-challenge.json")));
    }
}
