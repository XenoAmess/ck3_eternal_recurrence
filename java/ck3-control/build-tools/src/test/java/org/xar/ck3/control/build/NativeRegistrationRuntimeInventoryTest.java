package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Uses real owned files/native metadata; no fake receipt is accepted as publication authority. */
final class NativeRegistrationRuntimeInventoryTest {
    @TempDir Path temporary;
    @Test void actualQuoteIncludesAllBaseVenvBrokerAndCanonicalHelperDependencies()throws Exception {
        var roots=roots();var quote=NativeRegistrationRuntimeInventory.quote(roots,bounds(16,16,4096));
        var geometry=NativeStorageGeometry.read(temporary);
        assertEquals(Math.multiplyExact(geometry.sectorsPerCluster(),geometry.bytesPerSector()),geometry.clusterBytes());
        assertEquals(temporary.getRoot(),geometry.root());
        assertEquals(6,quote.files().size());assertEquals(4,quote.directories().size());
        assertEquals(quote.files().stream().mapToLong(row->row.nativeFile().logicalBytes()).sum(),quote.logicalBytes());
        assertEquals(quote.files().stream().mapToLong(row->row.nativeFile().allocatedBytes()).sum(),quote.nativeAllocatedBytes());
        assertTrue(quote.files().stream().anyMatch(row->row.path().equals(roots.client().path())));
        assertTrue(quote.files().stream().anyMatch(row->row.path().equals(roots.helper().path())));
        assertTrue(quote.files().stream().anyMatch(row->row.path().equals(Path.of(roots.repository()).resolve(NativeRegistrationRuntimeInventory.MACHINE_IDENTITY_SOURCE).toString())));
        assertEquals(quote,ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(quote),NativeRegistrationRuntimeInventory.Quote.class));
    }
    @Test void actualInventoryCannotTruncateAtAFileDirectoryOrByteCeiling()throws Exception {
        var roots=roots();
        assertThrows(IOException.class,()->NativeRegistrationRuntimeInventory.quote(roots,bounds(4,16,4096)));
        assertThrows(IOException.class,()->NativeRegistrationRuntimeInventory.quote(roots,bounds(16,3,4096)));
        assertThrows(IOException.class,()->NativeRegistrationRuntimeInventory.quote(roots,bounds(16,16,1)));
        var before=NativeRegistrationRuntimeInventory.quote(roots,bounds(16,16,4096));
        Files.writeString(Path.of(roots.pythonBase()).resolve("new.dll"),"new original");
        var added=NativeRegistrationRuntimeInventory.quote(roots,bounds(16,16,4096));
        assertEquals(before.files().size()+1,added.files().size());assertNotEquals(before.files(),added.files());
        Files.delete(Path.of(roots.broker()).resolve("policy.json"));
        var removed=NativeRegistrationRuntimeInventory.quote(roots,bounds(16,16,4096));
        assertNotEquals(before.files(),removed.files());
    }
    @Test void fullRuntimeOver16000HasAClosedChunkDenominatorButNoShapeOnlyQualification()throws Exception {
        var roots=roots();var bounds=bounds(16001,3,16001);var chunks=new ArrayList<FileRef>();
        for(int i=0;i<32;i++)chunks.add(new FileRef(temporary.resolve(String.format(java.util.Locale.ROOT,"runtime-%06d.json",i)).toString(),128,"0".repeat(64)));
        var input=new FileRef(temporary.resolve("missing-source.json").toString(),128,"0".repeat(64));
        var manifest=new NativeRegistrationRuntimeInventory.Manifest(NativeRegistrationRuntimeInventory.MANIFEST_SCHEMA,
                WindowsJobProcess.currentMachineId(),"2026-10-24T00:00:00Z","2026-10-24T00:00:01Z",input,input,input,input,
                bounds,roots,List.of(directory("one"),directory("two"),directory("three")),16001,16001,16001,chunks,4096);
        assertEquals(32,manifest.chunks().size());assertEquals(16001,manifest.fileCount());
        var original=write(temporary.resolve("runtime-inventory.json"),ControlBuild.strictMapper().writeValueAsBytes(manifest));
        assertThrows(IOException.class,()->NativeRegistrationRuntimeInventory.verify(original));
        assertThrows(IOException.class,()->NativeRegistrationRuntimeInventory.evidenceReferences(original));
        var flat=new ArrayList<FileRef>();for(int i=0;i<16001;i++)flat.add(new FileRef(temporary.resolve("flat-"+i).toString(),1,"0".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->NativeBridgeBuild.unique(flat));
    }
    @Test void actualChunkNativeWitnessRoundTripRetainsIdentityAndRejectsSourceDrift()throws Exception {
        var roots=roots();var held=SharedSourceFiles.observe(Path.of(roots.python().path()));
        var chunk=new NativeRegistrationRuntimeInventory.Chunk(NativeRegistrationRuntimeInventory.CHUNK_SCHEMA,
                WindowsJobProcess.currentMachineId(),0,List.of(held));
        assertEquals(chunk,ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(chunk),NativeRegistrationRuntimeInventory.Chunk.class));
        Files.writeString(Path.of(roots.python().path()),"changed software fixture");
        assertThrows(IOException.class,()->SharedSourceFiles.assertUnchanged(held));
        assertThrows(IllegalArgumentException.class,()->new NativeRegistrationRuntimeInventory.Chunk(chunk.schema(),chunk.machineId(),0,List.of(held,held)));
    }
    @Test void publicProducerRejectsUnqualifiedReceiptBeforeCreatingAnyOutput()throws Exception {
        var roots=roots();Path output=temporary.resolve("not-created");var invalid=write(temporary.resolve("unqualified.json"),"{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var request=new NativeRegistrationRuntimeInventory.Request(NativeRegistrationRuntimeInventory.REQUEST_SCHEMA,
                WindowsJobProcess.currentMachineId(),NativeRegistrationRuntimeInventory.Mode.QUOTE,roots,bounds(16,16,4096),output.toString(),null,invalid,invalid);
        var original=write(temporary.resolve("request.json"),ControlBuild.strictMapper().writeValueAsBytes(request));
        assertThrows(IOException.class,()->NativeRegistrationRuntimeInventory.execute(original));assertFalse(Files.exists(output));
    }
    @Test void machineIdentitySourceIsInTheActualWitnessAndCannotDisappearOrDrift()throws Exception {
        var roots=roots();var before=NativeRegistrationRuntimeInventory.quote(roots,bounds(16,16,4096));
        Path machine=Path.of(roots.repository()).resolve(NativeRegistrationRuntimeInventory.MACHINE_IDENTITY_SOURCE);
        var held=SharedSourceFiles.observe(machine);
        var chunk=new NativeRegistrationRuntimeInventory.Chunk(NativeRegistrationRuntimeInventory.CHUNK_SCHEMA,
                WindowsJobProcess.currentMachineId(),0,List.of(held));
        assertEquals(chunk,ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(chunk),
                NativeRegistrationRuntimeInventory.Chunk.class));
        Files.writeString(machine,"changed machine identity software fixture");
        assertThrows(IOException.class,()->SharedSourceFiles.assertUnchanged(held));
        assertNotEquals(before.files(),NativeRegistrationRuntimeInventory.quote(roots,bounds(16,16,4096)).files());
        Files.delete(machine);
        assertThrows(IOException.class,()->NativeRegistrationRuntimeInventory.quote(roots,bounds(16,16,4096)));
    }
    private NativeRegistrationRuntimeInventory.Roots roots()throws IOException {
        Path repo=temporary.resolve("repo"),base=temporary.resolve("base"),venv=repo.resolve("tools/.venv"),broker=repo.resolve("tools/project_exe_broker");
        Files.createDirectories(base);Files.createDirectories(venv.resolve("Scripts"));Files.createDirectories(broker);
        write(base.resolve("base.dll"),new byte[]{1});write(broker.resolve("policy.json"),new byte[]{2});
        var python=write(venv.resolve("Scripts/python.exe"),new byte[]{3});
        var helper=write(repo.resolve("tools/register_project_exe_exclusions.py"),new byte[]{4});
        var client=write(repo.resolve("tools/project_exe_exclusion_broker_client.py"),new byte[]{5});
        write(repo.resolve(NativeRegistrationRuntimeInventory.MACHINE_IDENTITY_SOURCE),new byte[]{6});
        return new NativeRegistrationRuntimeInventory.Roots(repo.toString(),base.toString(),venv.toString(),broker.toString(),python,helper,client);
    }
    private NativeRegistrationRuntimeInventory.Directory directory(String name)throws IOException {
        Path path=temporary.resolve(name);Files.createDirectory(path);return new NativeRegistrationRuntimeInventory.Directory(path.toString(),SharedSourceFiles.nativeDirectory(path));
    }
    private static NativeRegistrationRuntimeInventory.Bounds bounds(int files,int dirs,long logical){return new NativeRegistrationRuntimeInventory.Bounds(files,dirs,logical,32L<<20,30);}
    private static FileRef write(Path path,byte[] bytes)throws IOException {Files.write(path,bytes);return FileRef.measure(path);}
}
