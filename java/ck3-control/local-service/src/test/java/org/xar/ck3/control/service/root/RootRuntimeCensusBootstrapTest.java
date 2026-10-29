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
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Real temporary Native census/immutable publication/consumer roundtrips, not Root financial authority.
 * The managed Maven invocation must provide its admitted Windows data-volume temporary directory.
 * Missing Windows custody is a failure, never a skipped positive qualification or a fabricated census. */
final class RootRuntimeCensusBootstrapTest {
    @TempDir Path temporary;
    private record Fixture(Path managed,Path controls,FileRef declaration,FileRef evidence,
            ExistingUsage usage,String machine,Clock clock,String review) { }

    private Fixture fixture(boolean createManaged)throws IOException {
        assertTrue(System.getProperty("os.name").startsWith("Windows"),"real Windows Native custody is required");
        Path managed=temporary.resolve("managed");if(createManaged)Files.createDirectory(managed);
        Path controls=Files.createDirectory(temporary.resolve("controls"));
        String machine=WindowsJobProcess.currentMachineId();Instant now=Instant.now();
        Clock clock=Clock.fixed(now,ZoneOffset.UTC);String review=now.plusSeconds(600).toString();
        FileRef evidence=write(controls.resolve("existing-usage.json"),
                StrictJson.canonical(StrictJson.object().put("scope","temporary-software-evidence-only").put("machine_id",machine)));
        long total=Files.getFileStore(temporary).getTotalSpace(),free=Files.getFileStore(temporary).getUsableSpace();
        var usage=new ExistingUsage(ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,Math.subtractExact(total,free),evidence);
        var declaration=new Declaration(DECLARATION,machine,"/root","runtime-census-software",now.minusSeconds(1).toString(),review,
                List.of(new ManagedRoot("temporary-runtime",managed.toString(),2L<<20,1L<<20)),
                "temporary-runtime",1000,30000,30000,List.of("temporary-runtime-census-regression"));
        FileRef declared=write(controls.resolve("declaration.json"),encode(declaration));
        return new Fixture(managed,controls,declared,evidence,usage,machine,clock,review);
    }
    private static RootProfileBootstrapCommand.RuntimeCensusRequest request(Fixture f,Path target) {
        return new RootProfileBootstrapCommand.RuntimeCensusRequest("xar.java-root-runtime-census-bootstrap/v1",
                f.machine(),f.review(),f.declaration(),f.usage(),target.toString());
    }
    private static FileRef write(Path target,byte[] bytes)throws IOException {
        Files.write(target,bytes,StandardOpenOption.CREATE_NEW);return FileRef.measure(target);
    }
    private static void changeSameLength(FileRef original)throws IOException {
        byte[] changed=Files.readAllBytes(Path.of(original.path()));changed[changed.length-1]=' ';
        Files.write(Path.of(original.path()),changed,StandardOpenOption.TRUNCATE_EXISTING);
    }

    @Test void actualCliProducesCompleteCensusAndItsExistingConsumerReadsTheSamePhysicalOriginal()throws Exception {
        var f=fixture(true);Files.writeString(f.managed().resolve("payload.json"),"{}",StandardOpenOption.CREATE_NEW);
        Path target=f.controls().resolve("actual-census.json");
        FileRef raw=write(f.controls().resolve("request.json"),ControlBuild.strictMapper().writeValueAsBytes(request(f,target)));
        RootProfileBootstrapCommand.main(new String[]{"RUNTIME_CENSUS",raw.path(),Long.toString(raw.bytes()),raw.sha256()});
        var actual=SharedSourceFiles.observe(target);var decoded=decodeCensus(Files.readAllBytes(target));
        var complete=assertInstanceOf(CompleteCensus.class,decoded);
        assertEquals("COMPLETE",complete.status());assertEquals(f.declaration(),complete.declarationRef());
        assertEquals(f.usage(),complete.existingWorkpackage());assertEquals(1,complete.runtimeRoots().getFirst().files());
        assertEquals(SharedSourceFiles.nativeDirectory(f.managed()),complete.runtimeRoots().getFirst().directoryIdentity());
        assertArrayEquals(encode(complete),Files.readAllBytes(target));SharedSourceFiles.assertUnchanged(actual);
    }

    @Test void missingActualRootPublishesOnlyTheOriginalIncompleteBranch()throws Exception {
        var f=fixture(false);Path target=f.controls().resolve("missing-census.json");
        var result=RootProfileBootstrapCommand.observeRuntimeCensus(request(f,target),f.clock());
        var incomplete=assertInstanceOf(IncompleteCensus.class,result.census());
        assertFalse(incomplete.reasons().isEmpty());assertEquals("INCOMPLETE",incomplete.status());
        assertEquals(incomplete,decodeCensus(Files.readAllBytes(target)));assertFalse(Files.exists(f.managed()));
        assertEquals(FileRef.measure(target),result.publication().original());
    }

    @Test void actualDirectoryReplacementIsObservedAnewRatherThanReusingTheOldCensus()throws Exception {
        var f=fixture(true);
        var first=RootProfileBootstrapCommand.observeRuntimeCensus(request(f,f.controls().resolve("before.json")),f.clock());
        var oldRoot=assertInstanceOf(CompleteCensus.class,first.census()).runtimeRoots().getFirst();
        Path retired=temporary.resolve("retired-managed");
        assertEquals(temporary,f.managed().getParent());assertEquals(temporary,retired.getParent());
        Files.move(f.managed(),retired);Files.createDirectory(f.managed());
        var second=RootProfileBootstrapCommand.observeRuntimeCensus(request(f,f.controls().resolve("after.json")),f.clock());
        var currentRoot=assertInstanceOf(CompleteCensus.class,second.census()).runtimeRoots().getFirst();
        assertNotEquals(oldRoot.directoryIdentity(),currentRoot.directoryIdentity());
        assertEquals(SharedSourceFiles.nativeDirectory(f.managed()),currentRoot.directoryIdentity());
        assertEquals(first.census(),decodeCensus(Files.readAllBytes(Path.of(first.publication().original().path()))));
    }

    @Test void sameLengthDeclarationDriftIsRefusedBeforeAnyOutput()throws Exception {
        var f=fixture(true);Path target=f.controls().resolve("refused.json");var request=request(f,target);
        changeSameLength(f.declaration());
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.observeRuntimeCensus(request,f.clock()));
        assertFalse(Files.exists(target));
    }

    @Test void existingUsageEvidenceDriftIsRefusedBeforeAnyOutput()throws Exception {
        var f=fixture(true);Path target=f.controls().resolve("refused.json");var request=request(f,target);
        changeSameLength(f.evidence());
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.observeRuntimeCensus(request,f.clock()));
        assertFalse(Files.exists(target));
    }

    @Test void publicationCannotMutateTheRootsItJustMeasuredOrOverwriteAnExistingOriginal()throws Exception {
        var f=fixture(true);Path inside=f.managed().resolve("census.json");
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.observeRuntimeCensus(request(f,inside),f.clock()));
        assertFalse(Files.exists(inside));
        Path target=f.controls().resolve("once.json");var request=request(f,target);
        var actual=RootProfileBootstrapCommand.observeRuntimeCensus(request,f.clock());
        var retained=SharedSourceFiles.observe(target);byte[] before=Files.readAllBytes(target);
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.observeRuntimeCensus(request,f.clock()));
        assertArrayEquals(before,Files.readAllBytes(target));SharedSourceFiles.assertUnchanged(retained);
        assertEquals(FileRef.measure(target),actual.publication().original());
    }

    @Test void expiredOrForeignRequestsDoNotWriteOrRenewTheDeclaration()throws Exception {
        var f=fixture(true);Path target=f.controls().resolve("refused.json");var request=request(f,target);
        Clock expired=Clock.fixed(Instant.parse(f.review()),ZoneOffset.UTC);
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.observeRuntimeCensus(request,expired));
        var foreign=new RootProfileBootstrapCommand.RuntimeCensusRequest(request.schema(),"other-software-machine",f.review(),
                f.declaration(),f.usage(),target.toString());
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.observeRuntimeCensus(foreign,f.clock()));
        assertFalse(Files.exists(target));
    }

    @Test void theExistingStrictMapperOwnsOneSnakeCaseWireContract()throws Exception {
        var f=fixture(true);var request=request(f,f.controls().resolve("wire.json"));
        byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(request);
        assertEquals(request,ControlBuild.strictMapper().readValue(bytes,RootProfileBootstrapCommand.RuntimeCensusRequest.class));
        var row=assertInstanceOf(ObjectNode.class,StrictJson.parse(bytes));
        assertTrue(row.has("existing_workpackage"));assertFalse(row.has("existingWorkpackage"));
        row.put("unexpected",true);
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(StrictJson.canonical(row),RootProfileBootstrapCommand.RuntimeCensusRequest.class));
        var wrong=assertInstanceOf(ObjectNode.class,StrictJson.parse(bytes));
        assertInstanceOf(ObjectNode.class,wrong.get("declaration")).put("bytes",true);
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(StrictJson.canonical(wrong),RootProfileBootstrapCommand.RuntimeCensusRequest.class));
    }
}
