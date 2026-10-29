package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeStorageContract.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import static org.xar.ck3.control.continuity.writer.StorageWriteGuard.*;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real temporary native allocation and original-writer locks. Cards are fixture originals, never Game authority.
 * CI must place its temporary root on its admitted test volume; insufficient actual safety space fails, not skips. */
class RootRuntimeStorageGuardTest {
    @TempDir Path directory;
    private final List<RootRuntimeStorageGuard> ownedGuards=new ArrayList<>();
    @AfterEach void releaseActualNativeOwnership()throws IOException {
        IOException failure=null;
        for(int index=ownedGuards.size()-1;index>=0;index--)try{ownedGuards.get(index).close();}
        catch(IOException rejected){if(failure==null)failure=rejected;else failure.addSuppressed(rejected);}
        if(failure!=null)throw failure;
    }
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final long ROOT_CAP=1<<20;
    private static final class MutableClock extends Clock {
        private Instant now=NOW;
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){if(!zone.equals(ZoneOffset.UTC))throw new IllegalArgumentException("fixture UTC required");return this;}
        @Override public Instant instant(){return now;}
    }
    private final class Fixture {
        final Path managed,control;
        final String machine;
        final MutableClock clock=new MutableClock();
        ContinuityWriter writer;
        final Path writerRoot;
        final boolean invalidAdmission;
        final NativeCheckpointFiles raw=new NativeCheckpointFiles();
        final FileRef ledger;
        final RootRuntimeDefinitionModel.StorageLease lease;
        Fixture(Path base,boolean incomplete,boolean reserveAllFree,long maximumWrite,boolean earlyQuota)throws IOException {
            managed=Files.createDirectory(base.resolve("managed"));control=Files.createDirectory(base.resolve("control"));
            machine=WindowsJobProcess.currentMachineId();invalidAdmission=incomplete||reserveAllFree;
            writerRoot=Files.createDirectory(managed.resolve("writer"));prepareWriterOriginals(writerRoot,machine);
            Files.createFile(managed.resolve(".runtime-storage-"+DriverJson.sha256("storage-regression".getBytes(java.nio.charset.StandardCharsets.UTF_8))+".lock"));
            String observed=NOW.minusSeconds(1).toString(),review=NOW.plusSeconds(3600).toString();
            Path volume=managed.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
            var original=StrictJson.object();original.put("kind","actual-temporary-volume-observation");original.put("machine_id",machine);
            original.put("total_volume_bytes",total);original.put("available_bytes",free);original.put("actual_old_workpackage_bytes_is_unknown",true);
            FileRef oldEvidence=write(control.resolve("existing-usage-evidence.json"),StrictJson.canonical(original));
            var old=new ExistingUsage(ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,Math.subtractExact(total,free),oldEvidence);
            var policy=StrictJson.object();policy.put("policy_version","1.0.0");var pc=policy.putObject("capacity");
            pc.put("safety_floor_bytes",2L<<30);pc.put("safety_ceiling_bytes",20L<<30);pc.put("default_project_quota_ceiling_bytes",100L<<30);
            pc.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));pc.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
            FileRef policyRef=write(control.resolve("policy.json"),wire(policy));
            var declaration=new Declaration(DECLARATION,machine,"/root","storage-regression",observed,review,
                    List.of(new ManagedRoot("runtime",managed.toString(),ROOT_CAP,maximumWrite)),"runtime",1000,30000,30000,List.of("temporary-native-storage-regression"));
            FileRef declarationRef=write(control.resolve("declaration.json"),encode(declaration));
            WholeCensus measured=RootRuntimeAllocationCensus.observe(declarationRef,old,clock);
            assertInstanceOf(CompleteCensus.class,measured,"actual isolated temporary allocation must be measurable");
            WholeCensus census=incomplete?new IncompleteCensus(CENSUS,"INCOMPLETE",machine,"/root","storage-regression",NOW.toString(),review,declarationRef,
                    List.of("fixture intentionally lacks a complete runtime allocation observation"),old):measured;
            FileRef censusRef=write(control.resolve("census.json"),encode(census));
            String quotaReview=earlyQuota?NOW.plusSeconds(10).toString():review;
            var capacity=new Capacity(CAPACITY,machine,"/root",ISSUER,"storage-regression",NOW.toString(),review,policyRef,declarationRef,censusRef,
                    List.of(new VolumeAllowance(volume.toString(),ROOT_CAP,0,total,"/root",quotaReview)));
            FileRef capacityRef=write(control.resolve("capacity.json"),encode(capacity));
            var claims=new ArrayList<ReservationClaim>();claims.add(new ReservationClaim("own-peak","/root",machine,"storage-regression",
                    ClaimScope.CANONICAL_OUTPUT_ROOTS,List.of(managed.toString()),ROOT_CAP,capacityRef));
            if(reserveAllFree)claims.add(new ReservationClaim("actual-other-held-bound","/root/other",machine,"other-window",
                    ClaimScope.EXTERNAL_CONSERVATIVE_EVIDENCE,List.of(),free,oldEvidence));
            long all=reserveAllFree?Math.addExact(ROOT_CAP,free):ROOT_CAP;
            var head=new ReservationLedger(LEDGER,"new-fixture-ledger",1,machine,"/root",ISSUER,"storage-regression",NOW.toString(),review,
                    policyRef,declarationRef,capacityRef,null,List.of(new VolumeReservations(volume.toString(),claims,all)));
            ledger=write(control.resolve("runtime-ledger-head.json"),encode(head));
            var binding=new RuntimeBinding(BINDING,machine,"/root",ISSUER,"storage-regression",NOW.toString(),review,policyRef,declarationRef,censusRef,capacityRef,ledger,1);
            FileRef bindingRef=write(control.resolve("binding.json"),encode(binding));
            lease=new RootRuntimeDefinitionModel.StorageLease(RootRuntimeDefinitionModel.LEASE_SCHEMA,"ROOT_GAME_RUNTIME",machine,"/root",NOW.toString(),review,
                    policyRef,capacityRef,bindingRef,censusRef,ROOT_CAP,List.of(new RootRuntimeDefinitionModel.RootBudget(managed.toString(),ROOT_CAP)),
                    List.of(new RootRuntimeDefinitionModel.VolumeThreshold(volume.toString(),0,0)));

        }
        RootRuntimeStorageGuard guard(CheckpointFiles files)throws IOException {
            RootRuntimeStorageGuard guard=RootRuntimeStorageGuard.readExact(lease,machine,()->{
                if(writer==null)throw new IOException("the rejected allocation never constructed a canonical writer");return writer;
            },clock);ownedGuards.add(guard);guard.checkpointFiles(files);
            if(invalidAdmission){assertThrows(IOException.class,()->guard.requireInitialization(writerRoot.resolve("ROOT-CONTINUITY-WINDOW.lock"),List.of(writerRoot)));return guard;}
            guard.requireInitialization(writerRoot.resolve("ROOT-CONTINUITY-WINDOW.lock"),List.of(writerRoot));
            writer=writer(writerRoot,machine,clock,guard);return guard;
        }
    }

    @Test void fixedControlOwnerObservationIsReadOnlyAndCannotInventAnAbsentOwner()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);
        var guard=RootRuntimeStorageGuard.readExact(f.lease,f.machine,()->{throw new IOException("no canonical writer exists yet");},f.clock);
        Path lock=f.writerRoot.resolve("ROOT-CONTINUITY-WINDOW.lock");
        List<Path> before;try(var paths=Files.list(f.managed)){before=paths.sorted().toList();}
        guard.requireExistingAllocationOwner(lock);
        try(var paths=Files.list(f.managed)){assertEquals(before,paths.sorted().toList());}
        assertEquals(0,guard.accounting().unresolvedWrites());
        Path owner=before.stream().filter(path->path.getFileName().toString().startsWith(".runtime-storage-")).findFirst().orElseThrow();
        Files.delete(owner);
        assertThrows(IOException.class,()->guard.requireExistingAllocationOwner(lock));guard.close();
    }
    @Test void actualProducerCensusToGuardedNativeConsumerSettlesAllocationWithoutLedgerMutation()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);CheckpointFiles files=guard.checkpointFiles(f.raw);
        String head=f.writer.locked(same->same.head().digest());guard.requireCompleteAdmission();
        FileWitness actual=files.createNew(f.managed.resolve("actual-save-fragment.bin"),new byte[8192]);f.raw.verify(actual);
        assertEquals(RootRuntimeStorageGuard.Status.ADMITTED,guard.accounting().status());
        assertEquals(0,guard.accounting().unresolvedWrites());assertTrue(guard.accounting().roots().getFirst().measuredChargedUpperBytes()>4096);
        assertEquals(head,f.writer.locked(same->same.head().digest()));
    }
    @Test void existingOriginalWriterSessionIsBorrowedWithoutNestedLock()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);var files=guard.checkpointFiles(f.raw);
        f.writer.locked(same->{guard.requireCompleteAdmission();guard.requireSeed(16384);files.createNew(f.managed.resolve("same-session.json"),new byte[]{'{','}'});
            assertSame(same,f.writer.borrowedSession());return null;});
    }
    @Test void readOnlyImportRequiresActualOriginalWriterScopeSameFilesAndUnexpiredCards()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);var files=guard.checkpointFiles(f.raw);
        Fixture other=new Fixture(Files.createDirectory(f.control.resolve("other-fixture")),false,false,ROOT_CAP,false);
        var otherGuard=other.guard(other.raw);ContinuityWriter another=other.writer;
        String before=f.writer.locked(same->{
            String head=same.head().digest();guard.requireReadScope(same,files);
            assertEquals(RootRuntimeStorageGuard.Status.ADMITTED,guard.accounting().status());
            assertThrows(IOException.class,()->guard.requireReadScope(same,f.raw));
            another.locked(foreign->{assertThrows(IOException.class,()->guard.requireReadScope(foreign,files));return null;});
            assertEquals(head,same.head().digest());return head;
        });
        f.clock.now=NOW.plusSeconds(3601);
        f.writer.locked(same->{assertThrows(IOException.class,()->guard.requireReadScope(same,files));return null;});
        assertEquals(before,f.writer.locked(same->same.head().digest()));assertEquals(0,guard.accounting().unresolvedWrites());
    }
    @Test void actualOriginalWriterCreatesOnlyControlledDescendantsAndSamePortWritesTheirEvidence()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);var files=guard.checkpointFiles(f.raw);
        Path next=f.managed.resolve("episodes").resolve("next-original");String head=f.writer.locked(same->same.head().digest());
        f.writer.locked(same->{guard.requireCompleteAdmission();guard.createManagedDirectories(next);guard.createManagedDirectories(next);
            guard.requireManagedRoots(List.of(next));files.createNew(next.resolve("original-evidence.json"),new byte[]{'{','}'});return null;});
        assertTrue(Files.isDirectory(next));assertEquals(0,guard.accounting().unresolvedWrites());
        assertTrue(guard.accounting().roots().getFirst().measuredChargedUpperBytes()>=3*4096);
        assertEquals(head,f.writer.locked(same->same.head().digest()));
    }
    @Test void directoryPeakIsReservedBeforeTheFirstPhysicalCreate()throws IOException {
        Fixture f=new Fixture(directory,false,false,4095,false);var guard=f.guard(f.raw);guard.requireCompleteAdmission();
        Path next=f.managed.resolve("next-must-not-exist");assertThrows(IOException.class,()->guard.createManagedDirectories(next));
        assertFalse(Files.exists(next));assertEquals(0,guard.accounting().unresolvedWrites());
    }
    @Test void controlledDirectoriesRejectForeignExpiredAndUnboundedAncestryWithoutCreatingAnything()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);guard.requireCompleteAdmission();
        Path foreign=f.control.resolve("foreign-output");assertThrows(IOException.class,()->guard.createManagedDirectories(foreign));assertFalse(Files.exists(foreign));
        Path excessive=f.managed;for(int index=0;index<65;index++)excessive=excessive.resolve("child");Path bounded=excessive;
        assertThrows(IOException.class,()->guard.createManagedDirectories(bounded));assertFalse(Files.exists(f.managed.resolve("child")));
        f.clock.now=NOW.plusSeconds(3601);Path expired=f.managed.resolve("expired-output");
        assertThrows(IOException.class,()->guard.createManagedDirectories(expired));assertFalse(Files.exists(expired));
    }
    @Test void anotherGuardCannotResetLiveAccountingForTheSameOriginalWriterAndWindow()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var first=f.guard(f.raw);first.requireCompleteAdmission();
        var replacement=RootRuntimeStorageGuard.readExact(f.lease,f.machine,()->f.writer,f.clock);replacement.checkpointFiles(f.raw);
        assertThrows(IOException.class,()->replacement.requireInitialization(f.writer.originalLockPath(),List.of(f.writerRoot)));
    }
    @Test void incompleteCensusNeverGrantsWriteAdmission()throws IOException {
        Fixture f=new Fixture(directory,true,false,ROOT_CAP,false);var guard=f.guard(f.raw);var files=guard.checkpointFiles(f.raw);
        assertThrows(IOException.class,guard::requireCompleteAdmission);
        assertThrows(IOException.class,()->files.createNew(f.managed.resolve("refused.json"),new byte[]{'{','}'}));
        assertFalse(Files.exists(f.managed.resolve("refused.json")));
    }
    @Test void originalLedgerHeadFileIdentityCannotBeReplacedEvenWithSameBytes()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);guard.requireCompleteAdmission();
        Path head=Path.of(f.ledger.path()),replacement=f.control.resolve("same-bytes-ledger.json");Files.copy(head,replacement);
        Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(head));Files.move(replacement,head,StandardCopyOption.REPLACE_EXISTING);
        assertThrows(IOException.class,()->guard.requireSeed(4096));
    }
    @Test void perWritePeakCapRefusesBeforePhysicalCreation()throws IOException {
        Fixture f=new Fixture(directory,false,false,4096,false);var guard=f.guard(f.raw);var files=guard.checkpointFiles(f.raw);guard.requireCompleteAdmission();
        assertThrows(IOException.class,()->files.createNew(f.managed.resolve("too-big.bin"),new byte[8192]));
        assertFalse(Files.exists(f.managed.resolve("too-big.bin")));assertEquals(0,guard.accounting().unresolvedWrites());
    }
    @Test void otherUnspentReservationsCannotBeDroppedFromActualFreeSpaceFormula()throws IOException {
        Fixture f=new Fixture(directory,false,true,ROOT_CAP,false);var guard=f.guard(f.raw);
        IOException failure=assertThrows(IOException.class,guard::requireCompleteAdmission);assertTrue(failure.getMessage().contains("other reservations"));
    }
    @Test void aNewRootAtTheSamePathCannotReplaceItsSignedDirectoryIdentity()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);
        Files.move(f.managed,directory.resolve("old-managed"));Files.createDirectory(f.managed);
        assertThrows(IOException.class,guard::requireCompleteAdmission);
    }
    @Test void targetOutsideManagedRootIsRejectedBeforeAnyFileWrite()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);var files=guard.checkpointFiles(f.raw);guard.requireCompleteAdmission();
        Path escaped=f.control.resolve("not-authorized.bin");assertThrows(IOException.class,()->files.createNew(escaped,new byte[1]));assertFalse(Files.exists(escaped));
    }
    @Test void unknownPhysicalWriteRetainsPeakAndRequiresExactReconciliation()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);
        CheckpointFiles failing=new CheckpointFiles(){
            @Override public Optional<FileWitness> observe(Path path)throws IOException{return f.raw.observe(path);}
            @Override public byte[] read(FileWitness expected,int limit)throws IOException{return f.raw.read(expected,limit);}
            @Override public FileWitness replace(Path target,byte[] bytes)throws IOException{return f.raw.replace(target,bytes);}
            @Override public FileWitness copyNew(FileWitness source,Path target)throws IOException{return f.raw.copyNew(source,target);}
            @Override public FileWitness createNew(Path target,byte[] bytes)throws IOException{f.raw.createNew(target,bytes);throw new IOException("actual file created before fixture lost return");}
        };
        var guard=f.guard(failing);var files=guard.checkpointFiles(failing);guard.requireCompleteAdmission();Path target=f.managed.resolve("unknown.json");
        assertThrows(IOException.class,()->files.createNew(target,new byte[]{'{','}'}));
        assertEquals(RootRuntimeStorageGuard.Status.UNKNOWN_WRITE,guard.accounting().status());assertEquals(1,guard.accounting().unresolvedWrites());
        assertTrue(guard.accounting().roots().getFirst().outstandingPeakBytes()>0);assertThrows(IOException.class,()->guard.requireSeed(4096));
        guard.reconcileWrite(f.raw.observe(target).orElseThrow());assertEquals(0,guard.accounting().unresolvedWrites());
        assertEquals(RootRuntimeStorageGuard.Status.ADMITTED,guard.accounting().status());
    }
    @Test void expiredSignedQuotaIsNotExtendedByValidOuterLease()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,true);var guard=f.guard(f.raw);guard.requireCompleteAdmission();f.clock.now=NOW.plusSeconds(11);
        assertThrows(IOException.class,()->guard.requireSeed(4096));
    }
    @Test void unknownOldWholeUsageCannotBecomeZeroOrInventActualBytes()throws IOException {
        FileRef source=write(directory.resolve("evidence.json"),new byte[]{'{','}'});
        assertThrows(IllegalArgumentException.class,()->new ExistingUsage(ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,0,source));
        assertThrows(IllegalArgumentException.class,()->new ExistingUsage(ExistingUsageKind.ACTUAL,null,10,source));
    }
    @Test void expiredDeclarationCannotIssueFreshCensusAndClaimsCannotOverlap()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);
        RuntimeBinding binding=decode(Files.readAllBytes(Path.of(f.lease.runtimeBindingRef().path())),RuntimeBinding.class);
        f.clock.now=NOW.plusSeconds(3601);
        ExistingUsage old=decodeCensus(Files.readAllBytes(Path.of(binding.censusRef().path()))).existingWorkpackage();
        assertThrows(IOException.class,()->RootRuntimeAllocationCensus.observe(binding.declarationRef(),old,f.clock));
        ReservationClaim first=new ReservationClaim("first","/root",f.machine,"first-window",ClaimScope.CANONICAL_OUTPUT_ROOTS,
                List.of(f.managed.toString()),1,binding.capacityRef());
        ReservationClaim child=new ReservationClaim("child","/root",f.machine,"child-window",ClaimScope.CANONICAL_OUTPUT_ROOTS,
                List.of(f.managed.resolve("nested").toString()),1,binding.capacityRef());
        assertThrows(IllegalArgumentException.class,()->new VolumeReservations(f.managed.getRoot().toString(),List.of(first,child),2));
    }
    @Test void strictWireRejectsWrongTypeUnknownFieldAndMissingLedgerGeneration()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);byte[] original=Files.readAllBytes(Path.of(f.ledger.path()));
        com.fasterxml.jackson.databind.node.ObjectNode wrong=org.xar.ck3.control.build.ControlBuild.strictMapper().valueToTree(decode(original,ReservationLedger.class));wrong.put("generation",true);
        assertThrows(IOException.class,()->decode(wire(wrong),ReservationLedger.class));
        wrong.put("generation",1.0);assertThrows(IOException.class,()->decode(wire(wrong),ReservationLedger.class));
        wrong.putNull("generation");assertThrows(IOException.class,()->decode(wire(wrong),ReservationLedger.class));
        com.fasterxml.jackson.databind.node.ObjectNode missing=org.xar.ck3.control.build.ControlBuild.strictMapper().valueToTree(decode(original,ReservationLedger.class));missing.remove("generation");
        assertThrows(IOException.class,()->decode(wire(missing),ReservationLedger.class));
        com.fasterxml.jackson.databind.node.ObjectNode extra=org.xar.ck3.control.build.ControlBuild.strictMapper().valueToTree(decode(original,ReservationLedger.class));extra.put("unchecked_alias",1);
        assertThrows(IOException.class,()->decode(wire(extra),ReservationLedger.class));
        assertEquals(decode(original,ReservationLedger.class),decode(encode(decode(original,ReservationLedger.class)),ReservationLedger.class));
    }
    @Test void commonSafetyFormulaRetainsFloorCeilingAndExactPercentage() {
        assertEquals(2L<<30,RootRuntimeStorageGuard.safety(10L<<30));assertEquals(5L<<30,RootRuntimeStorageGuard.safety(100L<<30));
        assertEquals(20L<<30,RootRuntimeStorageGuard.safety(1000L<<30));
    }

    private static FileRef write(Path path,byte[] bytes)throws IOException{Files.write(path,bytes);return FileRef.measure(path);}
    private static byte[] wire(com.fasterxml.jackson.databind.JsonNode body)throws IOException{return org.xar.ck3.control.build.ControlBuild.strictMapper().writeValueAsBytes(body);}
    private static ExactRef exact(Path path)throws IOException{FileRef value=FileRef.measure(path);return new ExactRef(value.path(),value.bytes(),value.sha256());}
    private static void prepareWriterOriginals(Path root,String machine)throws IOException {
        Path source=root.resolve("fixture-source.java");Files.writeString(source,"actual native temporary storage writer source");
        var state=StrictJson.object();state.put("schema","root.ck3.continuity-window/v1");state.put("machine_id",machine);state.put("sequence",0);state.put("window_id",1);
        state.put("status","repair_required");state.put("target_days",10958);state.put("target_years",30);state.put("calendar_year_days",365.25);
        state.put("start_date_raw",1000);state.put("target_date_raw",263992);state.put("last_settled_date_raw",1000);state.put("last_settled_cycles",0);
        state.put("manual_repair_count",0);state.put("automatic_recovery_count",0);state.put("binding_lineage_count",0);state.putNull("game_binding");
        state.putNull("latest_binding");state.putNull("pending_cycle");state.put("NEXT",1);
        Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");byte[] bytes=ContinuityJson.canonical(state);Files.write(snapshot,bytes);Files.write(anchor,bytes);
        Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
    }
    private static ContinuityWriter writer(Path root,String machine,Clock clock,StorageWriteGuard guard)throws IOException {
        return new ContinuityWriter(new WriterContracts.Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),exact(root.resolve("anchor.json")),machine),
                List.of(exact(root.resolve("fixture-source.java"))),new WriterContracts.TransitionAuthority(){
            @Override public String revalidate(ContinuityState old,WriterContracts.Request request){throw new AssertionError("storage regression must not submit a transition");}
            @Override public ContinuityState reduce(ContinuityState old,WriterContracts.Request request){throw new AssertionError("storage regression must not reduce a transition");}
        },clock,guard);
    }
    @Test void mainReceiptProducerCreatesGuardedParentsAndReadsBackWithoutReplace()throws Exception {
        var fixture=new Fixture(directory,false,false,65536,false);
        var guard=fixture.guard(fixture.raw);var files=guard.checkpointFiles(fixture.raw);
        Path target=fixture.managed.resolve("main-receipts").resolve("startup-intent.json");
        byte[] body="{\"schema\":\"actual-main-receipt-test/v1\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        fixture.writer.locked(same->{
            var written=RootStartupReceiptFiles.writeExact(guard,files,same,target,body);
            assertArrayEquals(body,files.read(written,65536));
            assertThrows(IOException.class,()->RootStartupReceiptFiles.writeExact(guard,files,same,target,body));
            assertThrows(IOException.class,()->RootStartupReceiptFiles.writeExact(guard,fixture.raw,same,
                    fixture.managed.resolve("bypass.json"),body));
            return null;
        });
        assertTrue(Files.exists(target));assertFalse(Files.exists(fixture.managed.resolve("bypass.json")));
    }

    @Test void wholePersistentPlanMeasuresRealNestedCreateAndSameIdentityRenameWithoutDoubleQuote()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);
        Path temporary=f.managed.resolve("event.pending"),target=f.managed.resolve("event.json");
        var create=new FileCreate(temporary,8192);var rename=new FileRename(temporary,target,false);
        var whole=new WritePlan(f.writer.originalLockPath(),List.of(create,rename));
        guard.write(whole,()->guard.write(whole,()->{
            guard.write(new WritePlan(whole.originalLock(),List.of(create)),()->{
                assertEquals(1,guard.accounting().unresolvedWrites(),"the original full reservation is not duplicated by a nested child");
                Files.write(temporary,new byte[8192],java.nio.file.StandardOpenOption.CREATE_NEW);return null;
            });
            var identity=org.xar.ck3.control.build.SharedSourceFiles.nativeFile(temporary).identityKey();
            guard.write(new WritePlan(whole.originalLock(),List.of(rename)),()->{Files.move(temporary,target);return null;});
            assertEquals(identity,org.xar.ck3.control.build.SharedSourceFiles.nativeFile(target).identityKey());return null;
        }));
        assertFalse(Files.exists(temporary));assertEquals(8192,Files.size(target));assertEquals(0,guard.accounting().unresolvedWrites());
        assertEquals(RootRuntimeStorageGuard.Status.ADMITTED,guard.accounting().status());
        assertThrows(IOException.class,()->guard.write(whole,()->{throw new AssertionError("CREATE_NEW cannot replay");}));
    }
    @Test void persistentPreflightRefusesForeignOutputBeforeAnyPhysicalCallback()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);var called=new java.util.concurrent.atomic.AtomicInteger();
        var plan=new WritePlan(f.writer.originalLockPath(),List.of(new FileCreate(f.control.resolve("escape"),123)));
        assertThrows(IOException.class,()->guard.write(plan,()->{called.incrementAndGet();return null;}));assertEquals(0,called.get());
    }
    @Test void lostPersistentReturnRetainsItsOriginalQuoteAndOnlyExactPhysicalPostStateCanReconcile()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);Path target=f.managed.resolve("lost-original.json");
        var plan=new WritePlan(f.writer.originalLockPath(),List.of(new FileCreate(target,4096)));var called=new java.util.concurrent.atomic.AtomicInteger();
        assertThrows(IOException.class,()->guard.write(plan,()->{called.incrementAndGet();Files.write(target,new byte[2048],java.nio.file.StandardOpenOption.CREATE_NEW);throw new IOException("actual return was lost");}));
        assertEquals(RootRuntimeStorageGuard.Status.UNKNOWN_WRITE,guard.accounting().status());assertTrue(guard.accounting().unresolvedWrites()>0);
        assertThrows(IOException.class,()->guard.write(plan,()->{called.incrementAndGet();return null;}));assertEquals(1,called.get());
        guard.reconcilePersistentWrite(plan);assertEquals(0,guard.accounting().unresolvedWrites());assertEquals(1,called.get());
    }
    @Test void unobservedCreatedSourceRenameCannotInventItsIntermediateNativeIdentity()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);
        Path source=f.managed.resolve("unobserved.pending"),target=f.managed.resolve("unobserved.json");
        var plan=new WritePlan(f.writer.originalLockPath(),List.of(new FileCreate(source,4096),new FileRename(source,target,false)));
        assertThrows(IOException.class,()->guard.write(plan,()->{Files.write(source,new byte[17],java.nio.file.StandardOpenOption.CREATE_NEW);Files.move(source,target);return null;}));
        assertTrue(Files.exists(target));assertEquals(RootRuntimeStorageGuard.Status.UNKNOWN_WRITE,guard.accounting().status());
    }

    @Test void emptyMetadataSelfIdentityIsCapturedBeforeBoundedFillAndRename()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);
        Path temporary=f.managed.resolve("commit.pending"),target=f.managed.resolve("commit.json");
        var create=new FileCreate(temporary,0);var fill=new FileFillExistingEmpty(temporary,4096);var rename=new FileRename(temporary,target,false);
        var whole=new WritePlan(f.writer.originalLockPath(),List.of(create,fill,rename));
        guard.write(whole,()->{
            guard.write(new WritePlan(whole.originalLock(),List.of(create)),()->{Files.createFile(temporary);return null;});
            String identity=org.xar.ck3.control.build.SharedSourceFiles.nativeFile(temporary).identityKey();
            guard.write(new WritePlan(whole.originalLock(),List.of(fill)),()->{Files.write(temporary,identity.getBytes(java.nio.charset.StandardCharsets.UTF_8),java.nio.file.StandardOpenOption.WRITE);return null;});
            guard.write(new WritePlan(whole.originalLock(),List.of(rename)),()->{Files.move(temporary,target);return null;});
            assertEquals(identity,org.xar.ck3.control.build.SharedSourceFiles.nativeFile(target).identityKey());return null;
        });
        assertEquals(0,guard.accounting().unresolvedWrites());assertTrue(Files.readString(target).contains(":"));
    }

    @Test void callerCannotTurnARealNestedPhysicalFailureIntoSuccessfulWholeWrite()throws IOException {
        Fixture f=new Fixture(directory,false,false,ROOT_CAP,false);var guard=f.guard(f.raw);Path target=f.managed.resolve("swallowed.json");
        var plan=new WritePlan(f.writer.originalLockPath(),List.of(new FileCreate(target,4096)));
        assertThrows(IOException.class,()->guard.write(plan,()->{
            try{guard.write(plan,()->{Files.write(target,new byte[9],java.nio.file.StandardOpenOption.CREATE_NEW);throw new IOException("lost original nested return");});}
            catch(IOException original){assertTrue(Files.exists(target));}
            return null;
        }));
        assertEquals(RootRuntimeStorageGuard.Status.UNKNOWN_WRITE,guard.accounting().status());assertTrue(guard.accounting().unresolvedWrites()>0);
    }

}
