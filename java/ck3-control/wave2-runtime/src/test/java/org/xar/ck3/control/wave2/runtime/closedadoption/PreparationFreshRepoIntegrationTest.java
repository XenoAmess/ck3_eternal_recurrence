package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Real small-source prepare/refresh/import. Missing original machine/cohort is RED/UNAVAILABLE, never a synthetic pass. */
class PreparationFreshRepoIntegrationTest {
    private static final int SOURCE_CAP = 2*1024*1024;
    private static final String PRIOR = "java/ck3-control/admission-contracts/src/test/resources/closedpartial/original-sources.json";
    private static final String BUSINESS = "java/ck3-control/wave2-runtime/src/test/resources/closedadoption/original-business-sources.json";
    private static final String MECHANICAL = "tools/g2_saved_campaign/current_saved_continuity_v1.py";
    private static final String OWNER = "tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py";
    private record Actual(ExactRef ref, FileStatIdentity identity, byte[] raw) { }
    private record Work(Path root, Path repo, Path output, ClosedAdoptionPreparation.OriginalManifests manifests,
            JsonNode prior, JsonNode business, ExactRef mechanical, ExactRef owner, AtomicInteger guardCalls) { }
    private record Retained(Actual request, Actual snapshot, Actual canonical, Actual event) { }

    private static Path canonicalRepo() {
        String explicit = System.getProperty("xar.repo");
        if (explicit == null || explicit.isBlank()) { explicit = System.getenv("XAR_REPO_ROOT"); }
        Path path = Path.of(explicit == null || explicit.isBlank() ? System.getProperty("user.dir") : explicit).toAbsolutePath().normalize();
        for (int count=0; count<6 && path!=null; count++,path=path.getParent()) {
            if (Files.isRegularFile(path.resolve(PRIOR)) && Files.isRegularFile(path.resolve(BUSINESS))
                    && Files.isRegularFile(path.resolve(MECHANICAL)) && Files.isRegularFile(path.resolve(OWNER))) { return path; }
        }
        throw new IllegalStateException("UNAVAILABLE: set xar.repo or XAR_REPO_ROOT to the canonical original manifests/current transport source checkout");
    }
    private static Actual actual(Path path, int maximum) throws IOException {
        String name = path.toString().replace('\\','/').toLowerCase(Locale.ROOT);
        assertTrue(path.isAbsolute() && !name.endsWith("/driver-state.json") && !name.endsWith(".ck3") && !name.endsWith(".sav"),
                "test reads only exact small original metadata/source paths; Driver/SAVE bodies are excluded");
        assertTrue(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS),"UNAVAILABLE: required real source: "+path);
        var ids = new WindowsSavedProofIdentityReader(); FileStatIdentity before = ids.stat(path);
        assertTrue(before.bytes().signum()>0 && before.bytes().longValueExact()<=maximum,"finite complete source input");
        byte[] raw; try (var input=Files.newInputStream(path)) { raw=input.readNBytes(maximum+1); }
        assertEquals(before.bytes().longValueExact(),raw.length); assertTrue(raw.length<=maximum);
        assertEquals(before,ids.stat(path),"source remained stable across its complete small read");
        return new Actual(new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw)),before,raw);
    }
    private static Work work() throws IOException {
        Path original = canonicalRepo(); Actual business = actual(original.resolve(BUSINESS),RecoveryEvidence.MAX_BYTES);
        JsonNode businessValue = StrictJson.parse(business.raw());
        ExactRef declaredPrior = ExactRef.fromJson(businessValue.get("prior_fixture_manifest").get("ref"));
        Actual prior = actual(Path.of(declaredPrior.path()),RecoveryEvidence.MAX_BYTES);
        assertEquals(declaredPrior,prior.ref(),"canonical outer business manifest still binds the actual original prior ref");
        JsonNode priorValue = StrictJson.parse(prior.raw()); String expectedMachine = StrictJson.text(priorValue.get("machine_id"));
        assertEquals(expectedMachine,WindowsJobProcess.currentMachineId(),"UNAVAILABLE: original cohort belongs to another execution machine");
        assertEquals(expectedMachine,StrictJson.text(businessValue.get("machine_id")));
        var manifests = new ClosedAdoptionPreparation.OriginalManifests(prior.ref(),business.ref());
        Path scratch = Path.of(System.getProperty("xar.scratch","D:/codex-ck3-demos/2026-10-22-java-phase1/scratch")).toAbsolutePath().normalize();
        assertTrue(Files.isDirectory(scratch),"UNAVAILABLE: Root must release an existing owned scratch root");
        Path root = Files.createTempDirectory(scratch,"preparation-fresh-repo-");
        Path repo = root.resolve("current-transport-repo"), output = root.resolve("prepared");
        Files.createDirectories(repo.resolve("tools/g2_saved_campaign")); Files.createDirectory(output);
        Actual currentMechanical = actual(original.resolve(MECHANICAL),SOURCE_CAP), currentOwner = actual(original.resolve(OWNER),SOURCE_CAP);
        Files.copy(Path.of(currentMechanical.ref().path()),repo.resolve(MECHANICAL));
        Files.copy(Path.of(currentOwner.ref().path()),repo.resolve(OWNER));
        Actual mechanical = actual(repo.resolve(MECHANICAL),SOURCE_CAP), owner = actual(repo.resolve(OWNER),SOURCE_CAP);
        assertArrayEquals(currentMechanical.raw(),mechanical.raw()); assertArrayEquals(currentOwner.raw(),owner.raw());
        assertFalse(Files.exists(repo.resolve(PRIOR))); assertFalse(Files.exists(repo.resolve(BUSINESS)),"no historical manifest is copied into the transport repo");
        return new Work(root,repo,output,manifests,priorValue,businessValue,mechanical.ref(),owner.ref(),new AtomicInteger());
    }
    private static Runnable guard(Work work) {
        return () -> {
            work.guardCalls().incrementAndGet();
            try { assertTrue(Files.getFileStore(work.root()).getUsableSpace()>=16L*1024*1024,"Root scratch must retain its released free-space margin"); }
            catch (IOException error) { throw new UncheckedIOException(error); }
        };
    }
    private static ClosedAdoptionPreparation.Prepared prepare(Work work, Instant observed) throws IOException {
        return ClosedAdoptionPreparation.prepare(work.repo(),work.output(),work.manifests(),observed,guard(work));
    }
    private static ClosedAdoptionPreparation.Note note(Work work, int revision) throws IOException {
        return ClosedAdoptionPreparation.parseNote(actual(work.output().resolve(ClosedAdoptionPreparation.noteName(revision)),RecoveryEvidence.MAX_BYTES).raw());
    }
    private static ClosedAdoptionPreparation.SourceRoster roster(Work work, int revision) throws IOException {
        return ClosedAdoptionPreparation.parseRoster(actual(work.output().resolve(ClosedAdoptionPreparation.rosterName(revision)),RecoveryEvidence.MAX_BYTES).raw());
    }
    private static Retained retained(ClosedAdoptionPreparation.Prepared prepared) throws IOException {
        Path canonical = prepared.request().canonicalPath();
        return new Retained(actual(Path.of(prepared.requestRef().path()),RecoveryEvidence.MAX_BYTES),
                actual(Path.of(prepared.request().inputs().predecessor().path()),RecoveryEvidence.MAX_BYTES),
                actual(canonical,RecoveryEvidence.MAX_BYTES),actual(canonical.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS/00000240.json"),RecoveryEvidence.MAX_BYTES));
    }
    private static void unchanged(Retained before, ClosedAdoptionPreparation.Prepared after) throws IOException {
        Retained current = retained(after);
        for (List<Actual> pair : List.of(List.of(before.request(),current.request()),List.of(before.snapshot(),current.snapshot()),
                List.of(before.canonical(),current.canonical()),List.of(before.event(),current.event()))) {
            assertEquals(pair.get(0).ref(),pair.get(1).ref()); assertEquals(pair.get(0).identity(),pair.get(1).identity());
            assertArrayEquals(pair.get(0).raw(),pair.get(1).raw(),"refresh never rewrites the retained request or three original preseed files");
        }
    }
    private static void verifyAllOriginalSources(Work work, ClosedAdoptionPreparation.SourceRoster roster) throws IOException {
        assertEquals(work.manifests().prior(),roster.priorManifestRef()); assertEquals(work.manifests().business(),roster.businessManifestRef());
        assertEquals(88,roster.sourceRoster().size()); Set<String> uniquePaths = new HashSet<>();
        for (var row : roster.sourceRoster()) {
            assertTrue(uniquePaths.add(row.expectedRef().path())); assertFalse(row.labels().isEmpty());
            for (String label : row.labels()) {
                int slash = label.indexOf('/'); assertTrue(slash>0); String origin=label.substring(0,slash);
                JsonNode manifest = switch(origin) {
                    case "prior" -> work.prior(); case "business" -> work.business();
                    default -> throw new AssertionError("unexpected source origin: "+origin);
                };
                JsonNode originalField = manifest.at(label.substring(slash));
                assertFalse(originalField.isMissingNode(),"actual outer source pointer exists: "+label);
                assertEquals(row.expectedRef(),ExactRef.fromJson(originalField),"each roster label resolves to its actual exact original manifest ref");
            }
            Actual source = actual(Path.of(row.expectedRef().path()),SOURCE_CAP);
            assertEquals(row.expectedRef(),source.ref()); assertEquals(row.actualIdentity(),source.identity());
        }
    }
    private static void sourceOnly(Work work, ClosedAdoptionPreparation.Note note) throws IOException {
        JsonNode row = note.toJson();
        for (String counter : List.of("driver_body_reads","save_body_reads","writer_launches","game_launches")) { assertEquals(0,row.get(counter).longValue()); }
        for (String flag : List.of("invocation_created","review_plan_created","grants_warm_attachment")) { assertFalse(row.get(flag).booleanValue()); }
        for (String name : List.of("root-invocation.json","root-review-plan.json","root-review-challenge.json","root-review-approval.json",
                "root-review-approval-consumed.json","root-production-committed.json","root-two-stage-result.json","closed-adoption-result.json","root-consumer-session")) {
            assertFalse(Files.exists(work.output().resolve(name)),"preparation cannot launch or bind a session: "+name);
        }
        try (var entries=Files.newDirectoryStream(work.output(),"sdk-*")) { assertFalse(entries.iterator().hasNext(),"no SDK ticket/nonce artifacts"); }
        assertFalse(Files.exists(work.repo().resolve(PRIOR))); assertFalse(Files.exists(work.repo().resolve(BUSINESS)));
    }
    private static void emptyOutput(Work work) throws IOException {
        try (var files=Files.list(work.output())) { assertEquals(0,files.count(),"failed provenance creates no request, note, roster, or preseed"); }
    }

    @Test void freshTransportRepoPreparesAndImportsCanonicalProvenanceAndAllEightyEightRealSources() throws Exception {
        Work work = work(); Instant observed = Instant.now().minusSeconds(1);
        var prepared = prepare(work,observed); var note = note(work,1); var roster = roster(work,1);
        assertEquals(work.repo(),prepared.repo()); assertEquals(work.repo(),note.repo()); assertEquals(work.output(),note.outputRoot());
        assertEquals(observed.toString(),prepared.request().observedAtUtc()); assertEquals(observed,note.observedAtUtc());
        assertEquals(work.mechanical(),prepared.mechanicalSource()); assertEquals(work.owner(),prepared.coldOwnerSource());
        assertEquals(work.mechanical(),note.mechanicalSourceRef()); assertEquals(work.owner(),note.coldOwnerSourceRef());
        assertEquals(prepared.requestRef(),note.requestRef()); assertEquals(prepared.sourceRosterRef(),note.sourceRosterRef());
        verifyAllOriginalSources(work,roster); sourceOnly(work,note);
        ExactRef actualNote = actual(work.output().resolve(ClosedAdoptionPreparation.noteName(1)),RecoveryEvidence.MAX_BYTES).ref();
        assertEquals(prepared,ClosedAdoptionPreparation.inspectPrepared(work.repo(),work.output(),actualNote,guard(work)),
                "runtime import restores original manifests from roster, never from the fresh transport repo");
        assertTrue(work.guardCalls().get()>88,"the existing producer capacity guard participates in real capture");
    }
    @Test void refreshUsesCanonicalManifestsAndKeepsRequestObservationAndAllPreseedBytesAndIdentities() throws Exception {
        Work work = work(); var original = prepare(work,Instant.now().minusSeconds(1)); Retained before = retained(original);
        byte[] oldNote = actual(work.output().resolve(ClosedAdoptionPreparation.noteName(1)),RecoveryEvidence.MAX_BYTES).raw();
        byte[] oldRoster = actual(work.output().resolve(ClosedAdoptionPreparation.rosterName(1)),RecoveryEvidence.MAX_BYTES).raw();
        Instant fresh = Instant.now();
        var refreshed = ClosedAdoptionPreparation.refreshTransportSources(work.repo(),work.output(),work.manifests(),original.requestRef(),2,fresh,guard(work));
        var note = note(work,2); var roster = roster(work,2);
        assertEquals(original.request(),refreshed.request()); assertEquals(original.requestRef(),refreshed.requestRef());
        assertEquals(original.request().observedAtUtc(),note.requestObservedAtUtc()); assertEquals(fresh,note.observedAtUtc());
        assertEquals(fresh,roster.observedAtUtc()); assertEquals(2,roster.revision());
        assertEquals(work.mechanical(),note.mechanicalSourceRef()); assertEquals(work.owner(),note.coldOwnerSourceRef());
        assertNotEquals(original.sourceRosterRef(),refreshed.sourceRosterRef()); unchanged(before,refreshed);
        assertArrayEquals(oldNote,actual(work.output().resolve(ClosedAdoptionPreparation.noteName(1)),RecoveryEvidence.MAX_BYTES).raw());
        assertArrayEquals(oldRoster,actual(work.output().resolve(ClosedAdoptionPreparation.rosterName(1)),RecoveryEvidence.MAX_BYTES).raw());
        verifyAllOriginalSources(work,roster); sourceOnly(work,note);
        ExactRef noteRef = actual(work.output().resolve(ClosedAdoptionPreparation.noteName(2)),RecoveryEvidence.MAX_BYTES).ref();
        assertEquals(refreshed,ClosedAdoptionPreparation.inspectPrepared(work.repo(),work.output(),noteRef,guard(work)));
    }
    @Test void wrongPriorBytesReachTheRealExactSourceFailureBeforeAnyPublication() throws Exception {
        Work work = work(); Actual prior = actual(Path.of(work.manifests().prior().path()),RecoveryEvidence.MAX_BYTES);
        byte[] wrong = prior.raw().clone(); wrong[wrong.length-1] ^= 1;
        Path wrongPath = work.root().resolve("wrong-prior.json"); Files.write(wrongPath,wrong,StandardOpenOption.CREATE_NEW);
        ExactRef assertedOriginal = new ExactRef(wrongPath.toString(),prior.ref().bytes(),prior.ref().sha256());
        var manifests = new ClosedAdoptionPreparation.OriginalManifests(assertedOriginal,work.manifests().business());
        ContractViolationException error = assertThrows(ContractViolationException.class,() ->
                ClosedAdoptionPreparation.prepare(work.repo(),work.output(),manifests,Instant.now().minusSeconds(1),guard(work)));
        assertEquals("exact original source bytes and SHA",error.getMessage()); emptyOutput(work);
    }
    @Test void identicalPriorCopyCannotReplaceTheCanonicalBusinessPriorReference() throws Exception {
        Work work = work(); Path copy = work.root().resolve("copied-prior.json");
        Files.copy(Path.of(work.manifests().prior().path()),copy); Actual copied = actual(copy,RecoveryEvidence.MAX_BYTES);
        assertEquals(work.manifests().prior().sha256(),copied.ref().sha256()); assertNotEquals(work.manifests().prior(),copied.ref());
        var manifests = new ClosedAdoptionPreparation.OriginalManifests(copied.ref(),work.manifests().business());
        ContractViolationException error = assertThrows(ContractViolationException.class,() ->
                ClosedAdoptionPreparation.prepare(work.repo(),work.output(),manifests,Instant.now().minusSeconds(1),guard(work)));
        assertEquals("actual machine and outer manifest source binding",error.getMessage()); emptyOutput(work);
        assertFalse(copy.startsWith(work.repo()),"negative prior copies also stay outside the fresh transport repo");
    }
    @Test void refreshCannotSubstituteAPriorCopyOrOverwriteTheExistingPreparedPackage() throws Exception {
        Work work = work(); var original = prepare(work,Instant.now().minusSeconds(1)); Retained before = retained(original);
        Path copy = work.root().resolve("refresh-copied-prior.json"); Files.copy(Path.of(work.manifests().prior().path()),copy);
        var manifests = new ClosedAdoptionPreparation.OriginalManifests(actual(copy,RecoveryEvidence.MAX_BYTES).ref(),work.manifests().business());
        ContractViolationException error = assertThrows(ContractViolationException.class,() ->
                ClosedAdoptionPreparation.refreshTransportSources(work.repo(),work.output(),manifests,original.requestRef(),2,Instant.now(),guard(work)));
        assertEquals("actual machine and outer manifest source binding",error.getMessage()); unchanged(before,original);
        assertFalse(Files.exists(work.output().resolve(ClosedAdoptionPreparation.noteName(2))));
        assertFalse(Files.exists(work.output().resolve(ClosedAdoptionPreparation.rosterName(2)))); sourceOnly(work,note(work,1));
    }

    private static com.fasterxml.jackson.databind.node.ObjectNode cliConfiguration(Work work, String action) {
        var row = StrictJson.object(); row.put("schema","xar.closed-adoption-preparation-cli-config/v1"); row.put("action",action);
        row.put("machine_id",StrictJson.text(work.prior().get("machine_id"))); row.put("repo",work.repo().toString());
        row.put("output_root",work.output().toString()); var capacity = row.putObject("capacity");
        capacity.put("minimum_free_bytes",1_048_576); capacity.put("maximum_output_bytes",8*1024*1024);
        capacity.put("deadline_utc",Instant.now().plusSeconds(90).toString());
        if ("PREPARE".equals(action) || "REFRESH".equals(action)) {
            var manifests = row.putObject("original_manifests");
            manifests.set("prior",work.manifests().prior().toJson()); manifests.set("business",work.manifests().business().toJson());
        }
        if ("PREPARE".equals(action)) { row.put("observed_at_utc",Instant.now().minusSeconds(1).toString()); }
        else if ("REFRESH".equals(action)) {
            row.set("original_request_ref",new ExactRef(work.output().resolve("adoption-request.json").toString(),17,"0".repeat(64)).toJson());
            row.put("revision",2); row.put("fresh_observed_at_utc",Instant.now().toString());
        } else if ("BIND".equals(action)) {
            // These nonexistent refs exercise configuration rejection only; no ticket/cache is created or parsed.
            row.set("preparation_ref",new ExactRef(work.output().resolve("PREPARATION-refresh0001.json").toString(),17,"0".repeat(64)).toJson());
            row.set("sdk_read_ticket_ref",new ExactRef(work.output().resolve("never-created-sdk-ticket.json").toString(),17,"0".repeat(64)).toJson());
            var limits = row.putObject("limits"); limits.put("writer_memory_bytes",512*1024*1024); limits.put("timeout_seconds",60);
            limits.put("deadline_utc",Instant.now().plusSeconds(60).toString()); limits.put("minimum_free_bytes",1_048_576);
            limits.put("maximum_output_bytes",8*1024*1024);
        }
        return row;
    }
    private static ExactRef cliFile(Work work, String name, com.fasterxml.jackson.databind.node.ObjectNode config) throws IOException {
        byte[] raw = ClosedAdoptionJson.encode(config); Path path = work.root().resolve(name);
        Files.write(path,raw,StandardOpenOption.CREATE_NEW); return actual(path,RecoveryEvidence.MAX_BYTES).ref();
    }
    private static void invokePreparationCli(ExactRef ref) throws Exception {
        ClosedAdoptionPreparation.PreparationMain.main(new String[]{ref.path(),Long.toString(ref.bytes()),ref.sha256()});
    }
    private static void cliRejected(Work work, String name, com.fasterxml.jackson.databind.node.ObjectNode config, String message) throws Exception {
        ExactRef ref = cliFile(work,name,config); // Complete wire encoding/readback occurs outside the expected parser failure.
        ContractViolationException error = assertThrows(ContractViolationException.class,() -> invokePreparationCli(ref));
        assertTrue(error.getMessage().contains(message),error.getMessage()); emptyOutput(work);
        assertFalse(Files.exists(work.output().resolve("never-created-sdk-ticket.json")));
    }
    @Test void realRefreshCliPublishesStrictCanonicalProvenanceThenTheTypedRuntimeImportsIt() throws Exception {
        Work work = work(); var original = prepare(work,Instant.now().minusSeconds(1)); Retained before = retained(original);
        var config = cliConfiguration(work,"REFRESH"); config.set("original_request_ref",original.requestRef().toJson());
        ExactRef configRef = cliFile(work,"refresh-cli-config.json",config); invokePreparationCli(configRef);
        var refreshedNote = note(work,2); var refreshedRoster = roster(work,2);
        assertEquals(original.requestRef(),refreshedNote.requestRef());
        assertEquals(original.request().observedAtUtc(),refreshedNote.requestObservedAtUtc());
        assertEquals(Instant.parse(config.get("fresh_observed_at_utc").textValue()),refreshedNote.observedAtUtc());
        assertEquals(work.mechanical(),refreshedNote.mechanicalSourceRef()); assertEquals(work.owner(),refreshedNote.coldOwnerSourceRef());
        verifyAllOriginalSources(work,refreshedRoster); sourceOnly(work,refreshedNote);
        ExactRef noteRef = actual(work.output().resolve(ClosedAdoptionPreparation.noteName(2)),RecoveryEvidence.MAX_BYTES).ref();
        var imported = ClosedAdoptionPreparation.inspectPrepared(work.repo(),work.output(),noteRef,guard(work));
        assertEquals(refreshedNote.sourceRosterRef(),imported.sourceRosterRef()); unchanged(before,imported);
    }
    @Test void realCliRejectsWrongShapeEqualValueWrongTypesUnknownMachineAndExclusiveBranchFieldsBeforeSourceExecution() throws Exception {
        Work work = work(); int index=0;
        List<java.util.function.Consumer<com.fasterxml.jackson.databind.node.ObjectNode>> invalidPrepare = List.of(
                row -> row.put("capacity",true),
                row -> ((com.fasterxml.jackson.databind.node.ObjectNode)row.get("capacity")).put("minimum_free_bytes",false),
                row -> ((com.fasterxml.jackson.databind.node.ObjectNode)row.get("capacity")).put("maximum_output_bytes",8388608.0),
                row -> row.set("sdk_read_ticket_ref",work.manifests().prior().toJson()),
                row -> row.put("observed_at_utc",true),
                row -> row.remove("original_manifests"),
                row -> row.put("unknown_flag",true),
                row -> row.put("action","RESUME"),
                row -> row.put("machine_id","different-preparation-cli-machine"));
        List<String> expected = List.of("JSON object required","exact JSON integer required","exact JSON integer required",
                "exact JSON fields required","JSON string required","exact JSON fields required","exact JSON fields required",
                "preparation CLI action","actual preparation CLI machine");
        for (int change=0; change<invalidPrepare.size(); change++) {
            var config=cliConfiguration(work,"PREPARE"); invalidPrepare.get(change).accept(config);
            cliRejected(work,"bad-cli-"+index+++".json",config,expected.get(change));
        }
        for (boolean floating : List.of(false,true)) {
            var config=cliConfiguration(work,"REFRESH");
            if(floating){config.put("revision",1.0);}else{config.put("revision",true);}
            ExactRef ref=cliFile(work,"bad-cli-"+index+++".json",config);
            JsonNode actualWire=StrictJson.parse(actual(Path.of(ref.path()),RecoveryEvidence.MAX_BYTES).raw());
            assertTrue(floating ? actualWire.get("revision").isFloatingPointNumber() : actualWire.get("revision").isBoolean());
            ContractViolationException error=assertThrows(ContractViolationException.class,() -> invokePreparationCli(ref));
            assertTrue(error.getMessage().contains("exact JSON integer required")); emptyOutput(work);
        }
        var refresh=cliConfiguration(work,"REFRESH"); refresh.put("observed_at_utc",Instant.now().toString());
        cliRejected(work,"bad-cli-"+index+++".json",refresh,"exact JSON fields required");
        var bind=cliConfiguration(work,"BIND"); bind.set("original_manifests",cliConfiguration(work,"PREPARE").get("original_manifests"));
        cliRejected(work,"bad-cli-"+index+++".json",bind,"exact JSON fields required");
        var bindBool=cliConfiguration(work,"BIND");
        ((com.fasterxml.jackson.databind.node.ObjectNode)bindBool.get("limits")).put("timeout_seconds",true);
        cliRejected(work,"bad-cli-"+index+++".json",bindBool,"exact JSON integer required");
        var bindFloat=cliConfiguration(work,"BIND");
        ((com.fasterxml.jackson.databind.node.ObjectNode)bindFloat.get("limits")).put("writer_memory_bytes",536870912.0);
        cliRejected(work,"bad-cli-"+index+++".json",bindFloat,"exact JSON integer required");
        assertFalse(Files.exists(work.output().resolve("never-created-sdk-ticket.json"))); emptyOutput(work);
    }
}
