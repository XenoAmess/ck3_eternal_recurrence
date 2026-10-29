package org.xar.ck3.control.wave2.runtime.savedproof;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.platform.win32.WinBase;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import org.xar.ck3.control.contracts.FileStatIdentity;

/** Native metadata counterpart of Python os.stat (FILE_ID_INFO and Unix ns). */
public final class WindowsSavedProofIdentityReader implements SavedProofIdentityReader {
    public interface AttributeApi extends com.sun.jna.win32.StdCallLibrary {
        boolean GetFileInformationByHandleEx(HANDLE handle, int kind, Pointer memory, int length);
    }
    private final AttributeApi attributes = Native.load("kernel32", AttributeApi.class);

    @Override public FileStatIdentity stat(Path path) throws IOException {
        if (!com.sun.jna.Platform.isWindows() || !path.isAbsolute()) { throw new IOException("Windows absolute metadata path required"); }
        HANDLE handle = Kernel32.INSTANCE.CreateFile(path.toString(), 0x80, 7, null, 3, 0x00200000, null);
        if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) { throw new IOException("metadata open Win32=" + Native.getLastError()); }
        try (Memory id = new Memory(24); Memory basic = new Memory(40); Memory standard = new Memory(24)) {
            if (!attributes.GetFileInformationByHandleEx(handle, 18, id, 24)
                    || !attributes.GetFileInformationByHandleEx(handle, 0, basic, 40)
                    || !attributes.GetFileInformationByHandleEx(handle, 1, standard, 24)) {
                throw new IOException("native metadata Win32=" + Native.getLastError());
            }
            if ((basic.getInt(32) & 0x400) != 0 || standard.getByte(20) != 0 || standard.getByte(21) != 0) { throw new IOException("ordinary non-reparse non-delete-pending file required"); }
            byte[] fileId = id.getByteArray(8, 16), reversed = new byte[16];
            for (int i = 0; i < 16; i++) { reversed[i] = fileId[15-i]; }
            BigInteger modified = new BigInteger(Long.toUnsignedString(basic.getLong(16))).multiply(BigInteger.valueOf(100))
                .subtract(new BigInteger("11644473600000000000"));
            return new FileStatIdentity(BigInteger.valueOf(standard.getLong(8)), new BigInteger(1, reversed).toString(), modified.toString());
        } finally { Kernel32.INSTANCE.CloseHandle(handle); }
    }
}
