package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Pure DATA helper coverage with real full-stream Windows SAVE witnesses; no Loaded role is constructed. */
final class RootLoadedFrozenPhysicalSaveEvidenceTest {
    @TempDir Path temporary;
    private static final long LARGE_BYTES=(long)WriterContracts.MAX_PIN_BYTES+1;
    private static final NativeCheckpointFiles FILES=new NativeCheckpointFiles();
    private record Physical(Path path,SharedSourceFiles.Witness source,FileWitness checkpoint){ }

    private static ExactRef exact(SharedSourceFiles.Witness witness){
        var source=witness.source();return new ExactRef(source.path(),source.bytes(),source.sha256());
    }
    private static String expectedSparseSha()throws Exception {
        var digest=MessageDigest.getInstance("SHA-256");byte[] zero=new byte[8192];long remaining=LARGE_BYTES-1;
        while(remaining>0){int count=(int)Math.min(remaining,zero.length);digest.update(zero,0,count);remaining-=count;}
        digest.update((byte)7);return HexFormat.of().formatHex(digest.digest());
    }
    private Physical sparse(String name)throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows(),"real NTFS sparse-file and FileID witnesses required");
        Path path=temporary.resolve(name).toAbsolutePath();
        try(var output=FileChannel.open(path,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE,StandardOpenOption.SPARSE)){
            assertEquals(0,output.size());
            int attributes=com.sun.jna.platform.win32.Kernel32.INSTANCE.GetFileAttributes("\\\\?\\"+path);
            assertTrue(attributes!=-1&&(attributes&0x200)!=0,"sparse attribute must exist before extending the empty file");
            output.position(LARGE_BYTES-1);output.write(ByteBuffer.wrap(new byte[]{7}));output.force(true);
        }
        var source=SharedSourceFiles.observe(path);var checkpoint=FILES.observe(path).orElseThrow();
        assertEquals(67108869,LARGE_BYTES);assertEquals(LARGE_BYTES,source.source().bytes());
        assertEquals(expectedSparseSha(),source.source().sha256(),"independent complete zero-stream plus final-byte SHA");
        assertEquals(exact(source),checkpoint.reference());assertEquals(LARGE_BYTES,source.nativeFile().logicalBytes());
        assertTrue(source.nativeFile().allocatedBytes()<=65536,"the complete logical SAVE must remain physically sparse");
        assertEquals(1,source.nativeFile().linkCount());
        return new Physical(path,source,checkpoint);
    }
    private SharedSourceFiles.Witness metadata(String name)throws IOException {
        Path path=temporary.resolve(name).toAbsolutePath();Files.writeString(path,"{\"original\":true}",StandardOpenOption.CREATE_NEW);
        return SharedSourceFiles.observe(path);
    }
    private static void rejected(Executable work){
        Throwable failure=assertThrows(Throwable.class,work);
        assertTrue(failure instanceof IOException||failure instanceof IllegalArgumentException,()->"unexpected failure: "+failure);
    }

    @Test void fullSparseSaveWitnessIsVerifiedAndOnlyItsExactRoleLeavesMetadata()throws Exception {
        var save=sparse("qualified-save.ck3");var first=metadata("environment.json");var second=metadata("policy.json");
        var refs=RootFrozenRunProfile.physicalSaveMetadataReferences(FILES,
                List.of(first,save.source(),second,first,save.source()),save.checkpoint(),save.checkpoint().reference());
        assertEquals(List.of(exact(first),exact(second)),refs,"metadata order and distinct originals survive the SAVE partition");
        assertFalse(refs.contains(save.checkpoint().reference()));
        SharedSourceFiles.assertUnchanged(save.source());FILES.verify(save.checkpoint());
    }

    @Test void wrongQualifiedReferenceMissingWitnessAndWrongNativeIdentityAreRejected()throws Exception {
        var save=sparse("qualified-save.ck3");var other=metadata("unrelated.json");
        rejected(()->RootFrozenRunProfile.physicalSaveMetadataReferences(FILES,List.of(save.source(),other),save.checkpoint(),exact(other)));
        rejected(()->RootFrozenRunProfile.physicalSaveMetadataReferences(FILES,List.of(other),save.checkpoint(),save.checkpoint().reference()));
        var wrongIdentity=new SharedSourceFiles.Witness(save.source().source(),other.nativeFile());
        rejected(()->RootFrozenRunProfile.physicalSaveMetadataReferences(FILES,List.of(wrongIdentity),save.checkpoint(),save.checkpoint().reference()));
        SharedSourceFiles.assertUnchanged(save.source());FILES.verify(save.checkpoint());
    }

    @Test void changedSaveBytesAndAnEqualContentReplacementFileIdAreRejected()throws Exception {
        var changed=sparse("changed-save.ck3");
        try(var output=FileChannel.open(changed.path(),StandardOpenOption.WRITE)){
            output.position(0);output.write(ByteBuffer.wrap(new byte[]{9}));output.force(true);
        }
        rejected(()->RootFrozenRunProfile.physicalSaveMetadataReferences(FILES,List.of(changed.source()),changed.checkpoint(),changed.checkpoint().reference()));
        var original=sparse("original-save.ck3");var replacement=sparse("replacement-save.ck3");
        assertNotEquals(original.source().nativeFile().identityKey(),replacement.source().nativeFile().identityKey());
        Files.setLastModifiedTime(replacement.path(),Files.getLastModifiedTime(original.path()));
        Files.move(original.path(),temporary.resolve("retained-original.ck3"),StandardCopyOption.ATOMIC_MOVE);
        Files.move(replacement.path(),original.path(),StandardCopyOption.ATOMIC_MOVE);
        var current=FILES.observe(original.path()).orElseThrow();
        assertEquals(original.checkpoint().reference(),current.reference(),"path, complete bytes and SHA alone cannot replace FileID");
        assertNotEquals(original.checkpoint().identity().fileId(),current.identity().fileId());
        rejected(()->RootFrozenRunProfile.physicalSaveMetadataReferences(FILES,List.of(original.source()),original.checkpoint(),original.checkpoint().reference()));
    }

    @Test void anotherLargeMetadataReferenceStillReachesTheOriginalBoundedWriterReader()throws Exception {
        var save=sparse("qualified-save.ck3");var largeMetadata=sparse("large-non-save.bin");var small=metadata("environment.json");
        var refs=RootFrozenRunProfile.physicalSaveMetadataReferences(FILES,List.of(save.source(),largeMetadata.source(),small),
                save.checkpoint(),save.checkpoint().reference());
        assertEquals(List.of(largeMetadata.checkpoint().reference(),exact(small)),refs);
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("real-writer"),false)){
            actual.writer.locked(same->{
                String before=same.head().digest();
                rejected(()->RootRestoreMaterials.readPinned(same,FILES,refs.getFirst(),WriterContracts.MAX_PIN_BYTES));
                var accepted=RootRestoreMaterials.readPinned(same,FILES,refs.get(1),WriterContracts.MAX_PIN_BYTES);
                assertArrayEquals(Files.readAllBytes(Path.of(exact(small).path())),accepted.contents());
                assertEquals(before,same.head().digest());return null;
            });
            assertEquals(0,actual.nativeActionWrites());
        }
    }
}
