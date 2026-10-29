package org.xar.ck3.control.wave2.runtime.savedproof;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Objects;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/**
 * Deterministic software regression only. No original SDK is imported or executed.
 * Driver/SAVE paths never exist: the identity port supplies synthetic attributes.
 * The synthetic runner writes bounded transport bytes and launches no process.
 */
final class SavedCheckpointMeasurementScopeTest {
    private static final Instant ISSUED = Instant.parse("2036-01-01T00:00:00Z");
    private static final Instant MEASURED = ISSUED.plusSeconds(30);
    private static final Instant CURRENT = ISSUED.plusSeconds(60);
    private static final Instant REVIEW = ISSUED.plusSeconds(120);
    private static final String SHA = "a".repeat(64);
    @TempDir Path temporary;

    private static final class MutableClock extends Clock {
        private Instant current;
        private MutableClock(Instant current) { this.current = Objects.requireNonNull(current); }
        private void set(Instant value) { current = Objects.requireNonNull(value); }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) {
            if (!ZoneOffset.UTC.equals(zone)) { throw new IllegalArgumentException("synthetic UTC clock only"); }
            return this;
        }
        @Override public Instant instant() { return current; }
    }

    private static final class SyntheticIdentities implements SavedProofIdentityReader {
        private final Path driverPath;
        private final Path savePath;
        private FileStatIdentity driver;
        private FileStatIdentity save;
        private int observations;
        private SyntheticIdentities(SavedProofReadTicket ticket) {
            driverPath = ticket.driverPath(); savePath = Path.of(ticket.save().path());
            driver = ticket.driverIdentity(); save = ticket.saveIdentity();
        }
        @Override public FileStatIdentity stat(Path path) throws IOException {
            observations++;
            if (driverPath.equals(path)) { return driver; }
            if (savePath.equals(path)) { return save; }
            throw new IOException("unexpected synthetic attribute path: " + path);
        }
        private void driftDriver() {
            driver = new FileStatIdentity(driver.bytes(),"18446744073709551614",driver.mtimeNs());
        }
        private void driftSave() {
            save = new FileStatIdentity(save.bytes(),"18446744073709551613",save.mtimeNs());
        }
    }

    private static final class HookedSources implements SavedCheckpointMeasurementCoordinator.ExactSourceReader {
        private final Path root;
        private ExactRef trigger;
        private Runnable hook;
        private int reads;
        private HookedSources(Path root) { this.root = root; }
        private void onRead(ExactRef reference, Runnable action) {
            trigger = Objects.requireNonNull(reference); hook = Objects.requireNonNull(action);
        }
        @Override public byte[] exact(ExactRef reference, int maximumBytes) throws IOException {
            assertTrue(Path.of(reference.path()).startsWith(root),"all source reads stay inside this synthetic fixture");
            byte[] bytes = SavedProofFiles.exact(reference,maximumBytes); reads++;
            if (reference.equals(trigger)) {
                Runnable action = hook; trigger = null; hook = null;
                assertNotNull(action); action.run();
            }
            return bytes;
        }
    }

    private static final class SyntheticRunner implements ManagedSdkMeasurementRunner {
        private final SavedProofReadTicket ticket;
        private final List<ExactRef> imported;
        private int calls;
        private boolean throwFailure;
        private int exitCode;
        private SyntheticRunner(SavedProofReadTicket ticket, List<ExactRef> imported) {
            this.ticket = ticket; this.imported = List.copyOf(imported);
        }
        @Override public Outcome run(SavedProofReadTicket actual, Path request) throws IOException {
            calls++; assertSame(ticket,actual); assertTrue(Files.isRegularFile(request));
            if (throwFailure) { throw new IOException("synthetic runner failure after nonce claim"); }
            Path stdout = ticket.outputRoot().resolve("synthetic-transport.stdout.json");
            Path stderr = ticket.outputRoot().resolve("synthetic-transport.stderr.txt");
            Files.write(stdout,StrictJson.canonical(observation()),StandardOpenOption.CREATE_NEW);
            Files.writeString(stderr,"",StandardOpenOption.CREATE_NEW);
            var terminal = new WindowsJobProcess.CommandResult(
                    new WindowsJobProcess.ProcessIdentity(42,"134371430348828741",ticket.pythonExecutable().toString()),
                    exitCode,0.01,new WindowsJobProcess.Accounting(1024,0,ticket.jobMemoryBytes(),WindowsJobProcess.REQUIRED_FLAGS),null);
            return new Outcome(terminal,stdout,stderr);
        }
        private ObjectNode observation() {
            ObjectNode row = StrictJson.object();
            row.put("schema","xar.original-sdk-current-save-transport/v1"); row.put("status","ORIGINAL_SDK_CALL_COMPLETED");
            row.put("machine_id",ticket.machineId()); row.put("nonce",ticket.nonce()); row.put("observed_at_utc",MEASURED.toString());
            row.put("worker_source_sha256",FixedSdkTransport.sourceSha256());
            row.set("sdk_freeze_ref",ticket.sdkFreeze().toJson()); row.set("validator_ref",ticket.validatorSource().toJson());
            row.set("driver_ref",new ExactRef(ticket.driverPath().toString(),17,SHA).toJson());
            row.set("driver_identity_before",ticket.driverIdentity().toJson()); row.set("driver_identity_after",ticket.driverIdentity().toJson());
            row.set("save_ref",ticket.save().toJson()); row.set("save_identity_before",ticket.saveIdentity().toJson()); row.set("save_identity_after",ticket.saveIdentity().toJson());
            ObjectNode checkpoint = row.putObject("checkpoint"); checkpoint.put("name","xar_checkpoint.ck3");
            checkpoint.put("sha256",SHA); checkpoint.put("size",18); checkpoint.put("date_raw",53279400); checkpoint.put("history_index",5944);
            ObjectNode anchor = row.putObject("anchor"); anchor.put("name","xar_checkpoint.ck3"); anchor.put("load_save_name","xar_checkpoint");
            anchor.put("path",ticket.save().path()); anchor.put("size",18); anchor.put("sha256",SHA);
            anchor.put("saved_date_raw",53279400); anchor.put("history_index",5944); anchor.putNull("succession_lifecycle");
            row.put("pipe_name",ticket.pipeName()); ObjectNode counts = row.putObject("counts");
            counts.put("driver_physical_body_reads",1); counts.put("driver_physical_read_bytes",17);
            counts.put("original_validator_calls",1); counts.put("save_sha256_calls",1);
            var sourceRows = row.putArray("imported_sources");
            for (ExactRef reference : imported) {
                ObjectNode source = sourceRows.addObject(); source.put("relative",ticket.sdkRoot().relativize(Path.of(reference.path())).toString().replace('\\','/'));
                source.put("bytes",reference.bytes()); source.put("sha256",reference.sha256());
            }
            row.put("Driver_SAVE_body_rewritten",false); row.put("Game_RPC_calls",0); return row;
        }
    }

    private record Fixture(Path root, SavedProofReadTicket ticket, ExactRef nativeSession, MutableClock clock,
            SyntheticIdentities identities, HookedSources sources, SyntheticRunner runner,
            SavedCheckpointMeasurementCoordinator coordinator) {
        private Path claim() { return root.resolve("sdk-" + ticket.nonce() + ".consumed.json"); }
        private Path qualification() { return root.resolve("sdk-" + ticket.nonce() + ".canonical-qualification.json"); }
        private SavedCheckpointMeasurementCoordinator freshCoordinator() {
            return new SavedCheckpointMeasurementCoordinator(runner,identities,clock,sources);
        }
        private void noPersistenceBodies() {
            assertFalse(Files.exists(ticket.driverPath()),"no Driver body is created or read");
            assertFalse(Files.exists(Path.of(ticket.save().path())),"no SAVE body is created or read");
        }
    }

    private Fixture fixture(String name) throws IOException {
        Path root = Files.createDirectory(temporary.resolve(name)).toAbsolutePath().normalize();
        Path sdk = Files.createDirectories(root.resolve("synthetic-sdk/xar_autoplayer")).getParent();
        ExactRef validator = file(sdk.resolve("xar_autoplayer/cold_checkpoint_validator.py"),"# synthetic validator bytes; never imported\n".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        ExactRef nativeSession = file(sdk.resolve("xar_autoplayer/native_session.py"),"# synthetic hasher bytes; never imported\n".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        ObjectNode freeze = StrictJson.object(); String machine = WindowsJobProcess.currentMachineId();
        freeze.put("machine_id",machine); freeze.put("source_root",sdk.toString()); var rows = freeze.putArray("files");
        for (ExactRef source : List.of(validator,nativeSession)) {
            ObjectNode row = rows.addObject(); row.put("bytes",source.bytes()); row.put("git_blob_sha1","b".repeat(40));
            row.put("git_mode","100644"); row.put("relative",sdk.relativize(Path.of(source.path())).toString().replace('\\','/')); row.put("sha256",source.sha256());
        }
        ExactRef inventory = file(root.resolve("synthetic-freeze.json"),StrictJson.canonical(freeze));
        ObjectNode release = StrictJson.object(); release.put("schema",SavedProofReadTicket.SCHEMA); release.put("machine_id",machine);
        release.put("nonce","0123456789abcdef0123456789abcdef"); release.put("observed_at_utc",ISSUED.toString()); release.put("review_at_utc",REVIEW.toString());
        release.put("driver_path",root.resolve("driver-state.json").toString());
        release.set("driver_identity",new FileStatIdentity(BigInteger.valueOf(17),"9007199254740993","1792672762678085200").toJson());
        release.set("save_ref",new ExactRef(root.resolve("save games/xar_checkpoint.ck3").toString(),18,SHA).toJson());
        release.set("save_identity",new FileStatIdentity(BigInteger.valueOf(18),"9007199254740995","1792672762678085201").toJson());
        release.put("sdk_root",sdk.toString()); release.set("sdk_freeze_ref",inventory.toJson()); release.set("validator_ref",validator.toJson());
        release.put("pipe_name","synthetic-never-opened"); release.put("python_executable",root.resolve("python-never-launched.exe").toString());
        release.put("output_root",root.toString()); release.put("max_driver_bytes",17); release.put("physical_driver_reads",1);
        release.put("original_sdk_save_hash_calls",1); release.put("job_memory_limit_bytes",65536); release.put("timeout_seconds",1);
        byte[] raw = StrictJson.canonical(release); ExactRef releaseRef = file(root.resolve("synthetic-release.json"),raw);
        SavedProofReadTicket ticket = SavedProofReadTicket.parse(new RecoveryEvidence(releaseRef,raw));
        MutableClock clock = new MutableClock(CURRENT); SyntheticIdentities identities = new SyntheticIdentities(ticket);
        HookedSources sources = new HookedSources(root); SyntheticRunner runner = new SyntheticRunner(ticket,List.of(validator,nativeSession));
        return new Fixture(root,ticket,nativeSession,clock,identities,sources,runner,
                new SavedCheckpointMeasurementCoordinator(runner,identities,clock,sources));
    }

    private static ExactRef file(Path path, byte[] bytes) throws IOException {
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW);
        return new ExactRef(path.toString(),bytes.length,RecoveryEvidence.sha256(bytes));
    }

    @Test void oneMeasurementIsCachedAndTheSameNonceCannotLaunchAnotherCoordinator() throws Exception {
        Fixture f = fixture("cache-once"); assertFalse(f.coordinator().hasMeasuredCache());
        SavedCheckpointMeasurement result = f.coordinator().measureOnce(f.ticket());
        assertTrue(f.coordinator().hasMeasuredCache()); assertSame(result,f.coordinator().requireCurrentCached());
        assertSame(result,f.coordinator().requireCurrentCached()); assertEquals(1,f.runner().calls);
        assertThrows(ContractViolationException.class,() -> f.coordinator().measureOnce(f.ticket()));
        assertThrows(FileAlreadyExistsException.class,() -> f.freshCoordinator().measureOnce(f.ticket()));
        assertEquals(1,f.runner().calls); assertTrue(Files.exists(f.claim())); f.noPersistenceBodies();
    }

    @Test void expiredAndNotYetObservedTicketsRejectBeforeSourcesNonceAndRunner() throws Exception {
        for (Instant now : List.of(ISSUED.minusNanos(1),REVIEW)) {
            Fixture f = fixture("ticket-time-" + now.getNano()); f.clock().set(now);
            assertThrows(ContractViolationException.class,() -> f.coordinator().measureOnce(f.ticket()));
            assertEquals(0,f.sources().reads); assertEquals(0,f.runner().calls);
            assertFalse(Files.exists(f.claim())); f.noPersistenceBodies();
        }
    }

    @Test void sourcePreflightCannotExpireBeforeTheNonceClaimAndRunnerStart() throws Exception {
        Fixture f = fixture("preflight-expiry"); f.sources().onRead(f.ticket().sdkFreeze(),() -> f.clock().set(REVIEW));
        assertThrows(ContractViolationException.class,() -> f.coordinator().measureOnce(f.ticket()));
        assertEquals(0,f.runner().calls); assertFalse(Files.exists(f.claim())); f.noPersistenceBodies();
    }

    @Test void measurementRejectsExpiryDuringTheFinalImportedSourceRead() throws Exception {
        Fixture f = fixture("measurement-expiry"); f.sources().onRead(f.nativeSession(),() -> f.clock().set(REVIEW));
        assertThrows(ContractViolationException.class,() -> f.coordinator().measureOnce(f.ticket()));
        assertEquals(1,f.runner().calls); assertTrue(Files.exists(f.claim()));
        assertFalse(f.coordinator().hasMeasuredCache()); assertFalse(Files.exists(f.qualification())); f.noPersistenceBodies();
    }

    @Test void measurementRejectsClockRollbackBehindTheActualWorkerObservation() throws Exception {
        Fixture f = fixture("measurement-rollback"); f.sources().onRead(f.nativeSession(),() -> f.clock().set(MEASURED.minusNanos(1)));
        assertThrows(ContractViolationException.class,() -> f.coordinator().measureOnce(f.ticket()));
        assertEquals(1,f.runner().calls); assertFalse(f.coordinator().hasMeasuredCache()); f.noPersistenceBodies();
    }

    @Test void measurementRejectsEitherPersistenceIdentityDriftingDuringSources() throws Exception {
        for (boolean driver : List.of(true,false)) {
            Fixture f = fixture("measurement-drift-" + driver);
            f.sources().onRead(f.nativeSession(),driver ? f.identities()::driftDriver : f.identities()::driftSave);
            assertThrows(ContractViolationException.class,() -> f.coordinator().measureOnce(f.ticket()));
            assertEquals(1,f.runner().calls); assertFalse(f.coordinator().hasMeasuredCache());
            assertTrue(Files.exists(f.claim())); f.noPersistenceBodies();
        }
    }

    private enum CacheMutation { EXPIRY, CLOCK_ROLLBACK, DRIVER_IDENTITY, SAVE_IDENTITY }
    @Test void cachedSourcesCannotExpireRollBackOrDriftIdentitiesBeforeReturningAuthority() throws Exception {
        for (CacheMutation mutation : CacheMutation.values()) {
            Fixture f = fixture("cache-" + mutation); f.coordinator().measureOnce(f.ticket());
            Runnable action = switch (mutation) {
                case EXPIRY -> () -> f.clock().set(REVIEW);
                case CLOCK_ROLLBACK -> () -> f.clock().set(MEASURED.minusNanos(1));
                case DRIVER_IDENTITY -> f.identities()::driftDriver;
                case SAVE_IDENTITY -> f.identities()::driftSave;
            };
            f.sources().onRead(f.nativeSession(),action);
            assertThrows(ContractViolationException.class,() -> f.coordinator().requireCurrentCached());
            assertEquals(1,f.runner().calls); f.noPersistenceBodies();
        }
    }

    @Test void cachedClockBeforeObservationRejectsBeforeAnySourceOrAttributeRead() throws Exception {
        Fixture f = fixture("cache-observation-lower-bound"); f.coordinator().measureOnce(f.ticket());
        int reads = f.sources().reads; int stats = f.identities().observations; f.clock().set(MEASURED.minusNanos(1));
        assertThrows(ContractViolationException.class,() -> f.coordinator().requireCurrentCached());
        assertEquals(reads,f.sources().reads); assertEquals(stats,f.identities().observations);
        assertEquals(1,f.runner().calls); f.noPersistenceBodies();
    }

    @Test void runnerExceptionConsumesNonceAndCannotRetryInTheSameOrAnotherCoordinator() throws Exception {
        Fixture f = fixture("runner-throws"); f.runner().throwFailure = true;
        assertThrows(IOException.class,() -> f.coordinator().measureOnce(f.ticket()));
        assertTrue(Files.exists(f.claim())); assertFalse(f.coordinator().hasMeasuredCache()); assertEquals(1,f.runner().calls);
        assertThrows(FileAlreadyExistsException.class,() -> f.coordinator().measureOnce(f.ticket()));
        assertThrows(FileAlreadyExistsException.class,() -> f.freshCoordinator().measureOnce(f.ticket()));
        assertEquals(1,f.runner().calls); f.noPersistenceBodies();
    }

    @Test void failedManagedTerminalIsRecordedButCannotCacheOrRetryTheConsumedNonce() throws Exception {
        Fixture f = fixture("runner-exit"); f.runner().exitCode = 9;
        assertThrows(ContractViolationException.class,() -> f.coordinator().measureOnce(f.ticket()));
        Path terminal = f.root().resolve("sdk-" + f.ticket().nonce() + ".terminal.json");
        var actual = StrictJson.parse(Files.readAllBytes(terminal));
        assertEquals(9,actual.get("exit_code").intValue()); assertFalse(actual.get("passed").booleanValue());
        assertFalse(f.coordinator().hasMeasuredCache()); assertTrue(Files.exists(f.claim()));
        assertThrows(FileAlreadyExistsException.class,() -> f.freshCoordinator().measureOnce(f.ticket()));
        assertEquals(1,f.runner().calls); f.noPersistenceBodies();
    }

    @Test void workerObservationCannotBeInTheFutureOfTheOwningClockWhenItIsCached() throws Exception {
        Fixture f = fixture("future-worker-observation"); f.clock().set(MEASURED.minusNanos(1));
        assertThrows(ContractViolationException.class,() -> f.coordinator().measureOnce(f.ticket()));
        assertEquals(1,f.runner().calls); assertFalse(f.coordinator().hasMeasuredCache());
        assertTrue(Files.exists(f.claim())); f.noPersistenceBodies();
    }
}

