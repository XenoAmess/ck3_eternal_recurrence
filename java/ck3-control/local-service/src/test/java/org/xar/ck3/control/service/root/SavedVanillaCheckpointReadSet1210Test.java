package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;

/** Executes the actual private checkpoint collector with real Windows read-only file HANDLEs. */
final class SavedVanillaCheckpointReadSet1210Test {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-11-18T00:00:00Z");
    private static final class MutableClock extends Clock {
        private Instant now=NOW;
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){return this;}
        @Override public Instant instant(){return now;}
    }
    /** Reflection invokes private production methods; it never alters private fields. */
    private static final class Capture implements AutoCloseable {
        private final Object issuer,readset;
        private final CheckpointFiles files;
        private boolean detached;
        private Capture(CheckpointFiles actual,Clock clock)throws Exception {
            var type=Class.forName(RootJavaSavedBootstrap.class.getName()+"$PreReadCheckpointFiles");
            var constructor=type.getDeclaredConstructor(CheckpointFiles.class);constructor.setAccessible(true);
            issuer=constructor.newInstance(actual);files=(CheckpointFiles)issuer;
            readset=invoke(issuer,"capture",new Class<?>[]{Clock.class,Instant.class},clock,NOW.plusSeconds(60));
        }
        private void detach()throws Exception {
            if(!detached){invoke(issuer,"detach",new Class<?>[]{readset.getClass()},readset);detached=true;}
        }
        private void seal()throws Exception {invoke(readset,"seal",new Class<?>[0]);detach();}
        private void verify()throws Exception {invoke(readset,"requireCurrent",new Class<?>[0]);}
        @Override public void close()throws IOException {
            Throwable failure=null;
            try{detach();}catch(Exception|Error problem){
                if(problem instanceof InterruptedException)Thread.currentThread().interrupt();
                failure=problem;
            }
            try{((AutoCloseable)readset).close();}catch(Exception|Error problem){
                if(problem instanceof InterruptedException)Thread.currentThread().interrupt();
                if(failure==null)failure=problem;else if(problem!=failure)failure.addSuppressed(problem);
            }
            if(failure instanceof IOException problem)throw problem;
            if(failure instanceof RuntimeException problem)throw problem;
            if(failure instanceof Error problem)throw problem;
            if(failure!=null)throw new IOException("checkpoint readset cleanup failed",failure);
        }
    }
    private static Object invoke(Object owner,String name,Class<?>[] types,Object... arguments)throws Exception {
        Method method=owner.getClass().getDeclaredMethod(name,types);method.setAccessible(true);
        try{return method.invoke(owner,arguments);}catch(InvocationTargetException failure){
            Throwable actual=failure.getCause();
            if(actual instanceof Exception problem)throw problem;
            if(actual instanceof Error problem)throw problem;
            throw new AssertionError(actual);
        }
    }
    private Path original(String name)throws IOException {
        Path path=temporary.resolve(name);Files.writeString(path,"original source checkpoint bytes");return path;
    }
    @Test void sealedActualHandlesDenyWriteAndDeleteUntilExplicitClose()throws Exception {
        Path path=original("held.json");var nativeFiles=new NativeCheckpointFiles();
        var witness=nativeFiles.observe(path).orElseThrow();
        var capture=new Capture(nativeFiles,new MutableClock());
        try{
            assertArrayEquals(Files.readAllBytes(path),capture.files.read(witness,1024));
            capture.seal();capture.verify();
            assertThrows(IOException.class,()->Files.writeString(path,"replaced"));
            assertThrows(IOException.class,()->Files.move(path,path.resolveSibling("moved.json")));
            capture.verify();
        }finally{capture.close();}
        assertThrows(IOException.class,capture::verify);
        Files.writeString(path,"after release");assertEquals("after release",Files.readString(path));
    }
    @Test void finiteExpiryPermanentlyInvalidatesReadsetEvenIfClockMovesBack()throws Exception {
        Path path=original("expiry.json");var actual=new NativeCheckpointFiles();var clock=new MutableClock();
        var capture=new Capture(actual,clock);
        try{
            capture.files.read(actual.observe(path).orElseThrow(),1024);capture.seal();capture.verify();
            clock.now=NOW.plusSeconds(60);assertThrows(IOException.class,capture::verify);
            clock.now=NOW;assertThrows(IOException.class,capture::verify);
        }finally{capture.close();}
        Files.writeString(path,"released after expiry");
    }
    @Test void caughtAbsentDependencyCannotSealAnApparentlySuccessfulReadset()throws Exception {
        Path path=original("positive.json");var actual=new NativeCheckpointFiles();
        var capture=new Capture(actual,new MutableClock());
        try{
            capture.files.read(actual.observe(path).orElseThrow(),1024);
            assertThrows(IOException.class,()->capture.files.observe(temporary.resolve("absent.json")));
            assertThrows(IOException.class,capture::seal);
        }finally{capture.close();}
        Files.writeString(path,"released after failed qualification");
    }
    @Test void foreignThreadClosePoisonsButOwnerCanStillReleaseTheHeldHandles()throws Exception {
        Path path=original("owner.json");var actual=new NativeCheckpointFiles();
        var capture=new Capture(actual,new MutableClock());
        try{
            capture.files.read(actual.observe(path).orElseThrow(),1024);capture.seal();
            var failure=new AtomicReference<Throwable>();
            var worker=new Thread(()->{
                try{((AutoCloseable)capture.readset).close();}catch(Throwable problem){failure.set(problem);}
            });
            worker.start();worker.join();assertInstanceOf(IOException.class,failure.get());
            assertThrows(IOException.class,capture::verify);
            assertThrows(IOException.class,()->Files.writeString(path,"still held"));
        }finally{capture.close();}
        Files.writeString(path,"owner released");assertEquals("owner released",Files.readString(path));
    }
    @Test void returnedBytesMustMatchTheActuallyHeldPhysicalOriginal()throws Exception {
        Path path=original("wrong-producer.json");var actual=new NativeCheckpointFiles();
        CheckpointFiles altered=new CheckpointFiles(){
            public java.util.Optional<org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness> observe(Path file)throws IOException{return actual.observe(file);}
            public byte[] read(org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness expected,int maximum)throws IOException {
                byte[] raw=actual.read(expected,maximum);raw[raw.length-1]^=1;return raw;
            }
            public org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness replace(Path file,byte[] raw)throws IOException{return actual.replace(file,raw);}
            public org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness createNew(Path file,byte[] raw)throws IOException{return actual.createNew(file,raw);}
            public org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness copyNew(org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness source,Path file)throws IOException{return actual.copyNew(source,file);}
        };
        var capture=new Capture(altered,new MutableClock());
        try{
            assertThrows(IOException.class,()->capture.files.read(actual.observe(path).orElseThrow(),1024));
            assertThrows(IOException.class,capture::seal);
        }finally{capture.close();}
        Files.writeString(path,"released after producer mismatch");
    }
    private static Object field(Object owner,String name)throws ReflectiveOperationException {
        var field=owner.getClass().getDeclaredField(name);field.setAccessible(true);return field.get(owner);
    }
    @Test void nativeCloseFailureStaysUnknownAcrossRepeatedCloseAndKeepsOriginalHandleHeld()throws Exception {
        Path path=original("cleanup-fault.json");var actual=new NativeCheckpointFiles();
        var capture=new Capture(actual,new MutableClock());
        com.sun.jna.platform.win32.WinNT.HANDLE originalHandle=null;
        boolean detached=false;IOException firstFailure=null;
        try{
            capture.files.read(actual.observe(path).orElseThrow(),1024);capture.seal();
            var held=(java.util.Map<?,?>)field(capture.readset,"held");
            Object lease=field(held.values().iterator().next(),"lease");
            var handle=lease.getClass().getDeclaredField("handle");handle.setAccessible(true);
            originalHandle=(com.sun.jna.platform.win32.WinNT.HANDLE)handle.get(lease);
            assertNotNull(originalHandle);
            var invalid=new com.sun.jna.platform.win32.WinNT.HANDLE(com.sun.jna.Pointer.NULL);
            assertFalse(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(invalid));
            assertEquals(6,com.sun.jna.Native.getLastError(),"actual ERROR_INVALID_HANDLE precondition");
            // Preserve the real descriptor, so its numeric HANDLE cannot be recycled into a stranger.
            handle.set(lease,invalid);detached=true;
            firstFailure=assertThrows(IOException.class,capture::close);
            var repeated=assertThrows(IOException.class,capture::close);
            assertNotSame(firstFailure,repeated,"AutoCloseable must not self-suppress the same failure instance");
            assertSame(firstFailure,repeated.getCause(),"normal repeated close cannot prove release after native failure");
            assertThrows(IOException.class,capture::verify);
            assertThrows(IOException.class,()->Files.writeString(path,"still actually held"));
        }finally{
            try{
                if(detached){
                    var repeated=assertThrows(IOException.class,capture::close);
                    if(firstFailure!=null)assertSame(firstFailure,repeated.getCause());
                }else capture.close();
            }finally{
                if(detached)assertTrue(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(originalHandle),
                        "fixture alone releases its preserved real descriptor");
            }
        }
        Files.writeString(path,"released by explicit fixture cleanup");
    }
    @Test void successfulReleaseAllowsForeignDestroyButNeverRevivesCurrentEligibility()throws Exception {
        Path path=original("already-released.json");var actual=new NativeCheckpointFiles();
        var capture=new Capture(actual,new MutableClock());
        try{capture.files.read(actual.observe(path).orElseThrow(),1024);capture.seal();}
        finally{capture.close();}
        var failure=new AtomicReference<Throwable>();
        var worker=new Thread(()->{
            try{((AutoCloseable)capture.readset).close();}catch(Throwable problem){failure.set(problem);}
        });
        worker.start();worker.join();assertNull(failure.get(),"already released destruction has no thread-owned work left");
        assertThrows(IOException.class,capture::verify,"destruction success never creates current read permission");
        Files.writeString(path,"released owner data remains mutable");
    }
}
