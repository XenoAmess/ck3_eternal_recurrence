package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeStorageContract.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual allocation-census/guard -> sole initializer -> original Core/read-only CLI consumer.
 * Issuer cards are bounded temporary software fixtures, never actual Root runtime or Game authority.
 * CI must put its native temporary root on an admitted data volume; actual safety failures fail the test.
 */
final class RootFreshContinuityInputsTest {
    @TempDir Path temporary;
    private static final long CAP=2L<<20;
    private record Fixture(Path managed,Path control,Path snapshot,Path anchor,FileRef plan,FileRef lease,
            String machine,Clock clock) { }
    private Fixture fixture(String name)throws IOException {
        Path base=Files.createDirectory(temporary.resolve(name));Path managed=Files.createDirectory(base.resolve("managed"));
        Path control=Files.createDirectory(base.resolve("control"));String machine=WindowsJobProcess.currentMachineId();
        Instant now=Instant.now();Clock clock=Clock.fixed(now,ZoneOffset.UTC);String observed=now.minusSeconds(1).toString(),review=now.plusSeconds(3600).toString();
        String window="fresh-continuity-inputs-software";Path volume=managed.getRoot();
        long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var facts=StrictJson.object().put("scope","actual-temporary-volume-only").put("machine_id",machine)
                .put("total_volume_bytes",total).put("available_bytes",free).put("other_project_usage_is_unknown",true);
        FileRef financial=write(control.resolve("financial.json"),StrictJson.canonical(facts));
        var usage=new ExistingUsage(ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,Math.subtractExact(total,free),financial);
        var policy=StrictJson.object().put("policy_version","1.0.0");var limits=policy.putObject("capacity");
        limits.put("safety_floor_bytes",2L<<30).put("safety_ceiling_bytes",20L<<30).put("default_project_quota_ceiling_bytes",100L<<30)
                .put("safety_volume_fraction",new java.math.BigDecimal("0.05")).put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),StrictJson.canonical(policy));
        var declaration=new Declaration(DECLARATION,machine,"/root",window,observed,review,
                List.of(new ManagedRoot("runtime",managed.toString(),CAP,CAP)),"runtime",1000,30000,30000,List.of("bounded-software-genesis-regression"));
        FileRef declared=write(control.resolve("declaration.json"),encode(declaration));
        var censusPublication=RootProfileBootstrapCommand.observeRuntimeCensus(
                new RootProfileBootstrapCommand.RuntimeCensusRequest("xar.java-root-runtime-census-bootstrap/v1",machine,
                        now.plusSeconds(1200).toString(),declared,usage,control.resolve("census.json").toString()),clock);
        WholeCensus census=censusPublication.census();
        assertInstanceOf(CompleteCensus.class,census,"temporary actual allocation must be measurable");
        FileRef measured=censusPublication.publication().original();
        var capacity=new Capacity(CAPACITY,machine,"/root",ISSUER,window,now.toString(),review,policyRef,declared,measured,
                List.of(new VolumeAllowance(volume.toString(),CAP,0,total,"/root",review)));
        FileRef released=write(control.resolve("capacity.json"),encode(capacity));
        var claim=new ReservationClaim("own-genesis-peak","/root",machine,window,ClaimScope.CANONICAL_OUTPUT_ROOTS,List.of(managed.toString()),CAP,released);
        var ledger=new ReservationLedger(LEDGER,"fresh-genesis-software-ledger",1,machine,"/root",ISSUER,window,now.toString(),review,
                policyRef,declared,released,null,List.of(new VolumeReservations(volume.toString(),List.of(claim),CAP)));
        FileRef head=write(control.resolve("reservation-head.json"),encode(ledger));
        FileRef binding=write(control.resolve("binding.json"),encode(new RuntimeBinding(BINDING,machine,"/root",ISSUER,window,now.toString(),review,
                policyRef,declared,measured,released,head,1)));
        var lease=new RootRuntimeDefinitionModel.StorageLease(RootRuntimeDefinitionModel.LEASE_SCHEMA,"ROOT_GAME_RUNTIME",machine,"/root",now.toString(),review,
                policyRef,released,binding,measured,CAP,List.of(new RootRuntimeDefinitionModel.RootBudget(managed.toString(),CAP)),
                List.of(new RootRuntimeDefinitionModel.VolumeThreshold(volume.toString(),0,0)));
        FileRef actualLease=write(control.resolve("lease.json"),ControlBuild.strictMapper().writeValueAsBytes(lease));
        FileRef plan=write(control.resolve("plan.json"),FreshContinuityGenesis.encode(new FreshContinuityGenesis.Plan(machine,1,OriginalWindowReducer.TARGET_DAYS)));
        return new Fixture(managed,control,managed.resolve("ledger/ROOT-CONTINUITY-WINDOW.json"),managed.resolve("ledger/anchor.json"),plan,actualLease,machine,clock);
    }
    private static RootFreshContinuityInputs.Request request(Fixture fixture,RootFreshContinuityInputs.Mode mode) {
        return new RootFreshContinuityInputs.Request(RootFreshContinuityInputs.SCHEMA,fixture.machine(),fixture.clock().instant().plusSeconds(3600).toString(),
                mode,fixture.plan(),fixture.snapshot().toString(),fixture.anchor().toString(),mode==RootFreshContinuityInputs.Mode.CREATE_NEW?fixture.lease():null);
    }
    @Test void strictActualPlanQuoteHasNoOutputRefsOrFilesystemMutationAndRejectsDrift()throws Exception {
        var f=fixture("quote");var request=request(f,RootFreshContinuityInputs.Mode.QUOTE);
        byte[] encoded=RootFreshContinuityInputs.encodeRequest(request);assertEquals(request,RootFreshContinuityInputs.decodeRequest(encoded));
        var prepared=RootFreshContinuityInputs.prepare(request,f.clock());var quote=prepared.quote();
        assertEquals(f.snapshot().toString(),quote.snapshot());assertTrue(quote.canonicalBytesPerFile()>0);
        var receipt=StrictJson.parse(RootFreshContinuityInputs.execute(request,f.clock()));
        assertEquals("QUOTED_NOT_WRITTEN",receipt.path("status").textValue());assertFalse(receipt.has("layout"));assertFalse(receipt.has("anchor"));
        try(var files=Files.list(f.managed())){assertEquals(0,files.count());}
        for(int variant=0;variant<4;variant++) {
            var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encoded);
            switch(variant){case 0->row.remove("storage_lease");case 1->row.put("mode","CREATE_NEW");
                case 2->((com.fasterxml.jackson.databind.node.ObjectNode)row.get("plan_original")).put("bytes",true);
                case 3->row.put("unexpected",1);default->throw new AssertionError();}
            byte[] invalid=StrictJson.canonical(row);assertThrows(IllegalArgumentException.class,()->RootFreshContinuityInputs.decodeRequest(invalid));
        }
        Files.writeString(Path.of(f.plan().path()),"{}");assertThrows(IOException.class,prepared::quote);
        assertThrows(IOException.class,()->RootFreshContinuityInputs.prepare(request,f.clock()));assertFalse(Files.exists(f.snapshot()));
    }
    @Test void actualGuardInitializationBindsOnlyItsRealCoreAndQueryIssuesNoReplayPermit()throws Exception {
        var f=fixture("create");var request=request(f,RootFreshContinuityInputs.Mode.CREATE_NEW);
        var decoded=RootFreshContinuityInputs.decodeRequest(RootFreshContinuityInputs.encodeRequest(request));
        var prepared=RootFreshContinuityInputs.prepare(decoded,f.clock());
        try(var created=prepared.createNew()) {
            var actual=created.initialized();var storage=created.storage();
            assertTrue(actual.initialHead().state().initializedOrigin().isEmpty());assertEquals(0,actual.initialHead().state().settledCycles());
            assertThrows(IOException.class,()->((RootRuntimeStorageGuard)storage).requireCompleteAdmission());
            assertThrows(IOException.class,prepared::createNew);
            FileRef nativeData=write(f.control().resolve("native-plan-data.json"),new byte[]{'{','}'});
            FileRef source=write(f.control().resolve("reviewed-source.txt"),"software-source-only".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var configuration=new RootApplicationConfiguration(f.machine(),HostMode.MCP_STDIO,f.clock().instant().plusSeconds(3600),exact(nativeData),actual.layout(),
                    List.of(exact(source)),f.snapshot().getParent().resolve("immutable-artifacts"),1L<<20);
            try(var core=RootApplicationAssembly.open(configuration,f.clock(),List.of(),Optional.empty(),storage)) {
                created.bindCore(core);assertSame(storage,core.storageGuard());
                ((RootRuntimeStorageGuard)storage).requireCompleteAdmission();
                core.writer().locked(same->{assertEquals(ContinuityState.Status.AWAITING_INITIAL_ENTRY,same.head().state().status());
                    assertEquals(0,same.head().state().sequence());assertFalse(same.head().state().toJson().has("game_binding"));return null;});
                assertEquals(0,((RootRuntimeStorageGuard)storage).accounting().unresolvedWrites());
            }
            var query=request(f,RootFreshContinuityInputs.Mode.QUERY_ORIGINAL);
            var receipt=StrictJson.parse(RootFreshContinuityInputs.execute(query,f.clock()));
            assertEquals("ORIGINAL_INITIALIZATION_READ_ONLY_NOT_ALLOCATION_RECONCILED",receipt.path("status").textValue());
            assertFalse(receipt.get("allocation_unknown_reconciled").booleanValue());assertFalse(receipt.get("write_retry_permitted").booleanValue());
            assertEquals(actual.anchor(),org.xar.ck3.control.continuity.writer.WriterContracts.Pin.fromJson(receipt.get("anchor")));
            try(var events=Files.list(actual.layout().events())){assertEquals(0,events.count());}
        }
    }
    @Test void sharedExecutionReturnsMeasuredCreateOutputsAndRejectsExpiredOrForeignRequests()throws Exception {
        var f=fixture("execute");var request=request(f,RootFreshContinuityInputs.Mode.CREATE_NEW);
        var receipt=StrictJson.parse(RootFreshContinuityInputs.execute(request,f.clock()));
        assertEquals("CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION",receipt.path("status").textValue());
        assertTrue(receipt.get("next_process_requires_fresh_actual_storage_census").booleanValue());
        assertEquals(SharedSourceFiles.observe(f.anchor()).source(),file(ExactRef.fromJson(receipt.path("anchor").get("ref"))));
        assertThrows(IOException.class,()->RootFreshContinuityInputs.execute(request,f.clock()));
        assertThrows(IOException.class,()->RootFreshContinuityInputs.prepare(request,Clock.fixed(f.clock().instant().plusSeconds(3601),ZoneOffset.UTC)));
        var foreign=new RootFreshContinuityInputs.Request(RootFreshContinuityInputs.SCHEMA,"another-actual-machine",request.reviewAtUtc(),
                RootFreshContinuityInputs.Mode.QUOTE,f.plan(),f.snapshot().toString(),f.anchor().toString(),null);
        assertThrows(IOException.class,()->RootFreshContinuityInputs.prepare(foreign,f.clock()));
    }
    private static FileRef write(Path path,byte[] bytes)throws IOException {Files.write(path,bytes,StandardOpenOption.CREATE_NEW);return FileRef.measure(path);}
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static FileRef file(ExactRef ref){return new FileRef(ref.path(),ref.bytes(),ref.sha256());}
}
