package org.xar.ck3.control.nativebridge;

import java.io.IOException;

/** Private physical boundary. No public caller can obtain an unpermitted mapping writer. */
interface NativePresentationMemoryPort extends AutoCloseable {
    void verify()throws IOException;
    byte[] read(int offset,int length)throws IOException;
    boolean compareAndSetSequence(int offset,long expected,long update)throws IOException;
    void writeRequest(byte[] exact168)throws IOException;
    default void writeTracking(byte[] exact4264)throws IOException { throw new IOException("tracking writer is unavailable"); }
    void flush()throws IOException;
    long uptimeMillis()throws IOException;
    String ownedDesktopOneWindow()throws IOException;
    @Override void close()throws IOException;
}
