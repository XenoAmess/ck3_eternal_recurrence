package org.xar.ck3.control.continuity.writer;

import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.nio.file.Path;

/** The original msvcrt lock file and byte range [0,1). No replacement lock namespace. */
final class WindowsLedgerLock implements AutoCloseable {
    private static final ThreadLocal<java.util.Set<Path>> HELD = ThreadLocal.withInitial(java.util.HashSet::new);
    interface LockApi extends StdCallLibrary {
        boolean LockFileEx(HANDLE handle, int flags, int reserved, int low, int high, WinBase.OVERLAPPED overlap);
        boolean UnlockFileEx(HANDLE handle, int reserved, int low, int high, WinBase.OVERLAPPED overlap);
        int SetFilePointer(HANDLE handle, int distance, IntByReference distanceHigh, int moveMethod);
    }
    private static final class Api {
        static final LockApi VALUE = Native.load("kernel32", LockApi.class, W32APIOptions.DEFAULT_OPTIONS);
    }
    private final HANDLE handle;
    private final WinBase.OVERLAPPED overlap;
    private final Path path;
    private boolean open = true;
    private WindowsLedgerLock(HANDLE handle, WinBase.OVERLAPPED overlap, Path path) { this.handle = handle; this.overlap = overlap; this.path = path; }
    static void requireHeld(Path supplied) throws IOException {
        if (!HELD.get().contains(supplied.toAbsolutePath().normalize())) throw new IOException("this thread does not own the actual original writer lock");
    }
    static WindowsLedgerLock acquire(Path path) throws IOException {
        path = path.toAbsolutePath().normalize();
        if (!Platform.isWindows()) throw new IOException("Windows msvcrt interoperability must be qualified on Windows");
        var before = LedgerFiles.identity(path); // Requires the existing original lock; never creates a fresh authority.
        // Deny FILE_SHARE_DELETE for the lifetime of the lock, binding the pathname to this handle.
        HANDLE handle = Kernel32.INSTANCE.CreateFile(LedgerFiles.winPath(path), 0xc0000000, 3, null, 3, 0x00200080, null);
        if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("original lock open Win32=" + Native.getLastError());
        WinBase.OVERLAPPED overlap = new WinBase.OVERLAPPED();
        boolean locked = false;
        try {
            // LOCKFILE_FAIL_IMMEDIATELY | LOCKFILE_EXCLUSIVE_LOCK, exact original byte range [0,1).
            if (!Api.VALUE.LockFileEx(handle, 3, 0, 1, 0, overlap))
                throw new IOException("original continuity writer lock busy/unavailable Win32=" + Native.getLastError());
            locked = true;
            if (!before.equals(LedgerFiles.identity(path))) throw new IOException("original lock file identity changed");
            if (!HELD.get().add(path)) throw new IOException("duplicate original-lock custody registration");
            return new WindowsLedgerLock(handle, overlap, path);
        } catch (IOException | RuntimeException error) {
            if (locked) Api.VALUE.UnlockFileEx(handle, 0, 1, 0, overlap);
            Kernel32.INSTANCE.CloseHandle(handle);
            throw error;
        }
    }
    /** Read the bounded original lock through the same handle that owns its exclusive byte range. */
    WriterContracts.Pin readOriginalPin() throws IOException {
        requireHeld(path);
        if (!open) throw new IOException("original writer lock is closed");
        var before = LedgerFiles.identity(path);
        if (before.bytes() > 1) throw new IOException("original lock pin exceeds its finite bound");
        if (Api.VALUE.SetFilePointer(handle, 0, null, 0) != 0)
            throw new IOException("original lock seek failed Win32=" + Native.getLastError());
        byte[] raw = new byte[2];
        IntByReference transferred = new IntByReference();
        if (!Kernel32.INSTANCE.ReadFile(handle, raw, raw.length, transferred, null))
            throw new IOException("original held lock read failed Win32=" + Native.getLastError());
        int length = transferred.getValue();
        if (length < 0 || length > 1 || length != before.bytes())
            throw new IOException("original held lock size drift");
        var after = LedgerFiles.identity(path);
        if (!before.equals(after)) throw new IOException("original held lock native identity drift");
        byte[] actual = java.util.Arrays.copyOf(raw, length);
        return new WriterContracts.Pin(new org.xar.ck3.control.contracts.ExactRef(path.toString(), length,
                LedgerFiles.sha(actual)), after);
    }
    @Override public void close() throws IOException {
        if (!open) throw new IOException("writer lock already closed");
        requireHeld(path); open = false;
        boolean unlocked = Api.VALUE.UnlockFileEx(handle, 0, 1, 0, overlap);
        int failure = Native.getLastError();
        boolean closed = Kernel32.INSTANCE.CloseHandle(handle);
        HELD.get().remove(path);
        if (!unlocked || !closed) throw new IOException("original lock release/close failed Win32=" + failure);
    }
}
