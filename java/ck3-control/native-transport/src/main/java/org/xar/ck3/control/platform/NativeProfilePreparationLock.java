package org.xar.ck3.control.platform;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;

/** Shared pre-Core preparation custody using the actual lifecycle mutex and OS process reader. */
public final class NativeProfilePreparationLock implements AutoCloseable {
    private static final String LIFECYCLE_MUTEX="Local\\XarJavaGameLifecycle-v1";
    private final Win32Host.Mutex mutex;
    private final Instant deadline;
    private boolean closed;
    private NativeProfilePreparationLock(Win32Host.Mutex mutex,Instant deadline){this.mutex=mutex;this.deadline=deadline;}
    public static NativeProfilePreparationLock acquire(Instant deadline)throws IOException,InterruptedException{
        Objects.requireNonNull(deadline);var mutex=Win32Host.mutex(LIFECYCLE_MUTEX,deadline);
        var custody=new NativeProfilePreparationLock(mutex,deadline);
        try{custody.requireNoGame();return custody;}
        catch(IOException|RuntimeException failure){try{mutex.close();}catch(IOException close){failure.addSuppressed(close);}throw failure;}
    }
    /** The hierarchical bootstrap writer must invoke this immediately before and after each actual file write. */
    public void requireNoGame()throws IOException{
        if(closed)throw new IOException("profile preparation lifecycle custody is closed");
        mutex.requireHeld();Win32Host.deadline(deadline);
        if(!Win32Host.processes("ck3.exe",deadline).isEmpty())throw new IOException("actual global CK3 process blocks profile preparation");
    }
    @Override public void close()throws IOException{
        if(closed)return;
        IOException failure=null;
        try{requireNoGame();}catch(IOException error){failure=error;}
        closed=true;
        try{mutex.close();}catch(IOException error){if(failure==null)failure=error;else failure.addSuppressed(error);}
        if(failure!=null)throw failure;
    }
}
