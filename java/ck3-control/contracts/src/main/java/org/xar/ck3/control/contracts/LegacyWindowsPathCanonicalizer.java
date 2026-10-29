package org.xar.ck3.control.contracts;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.Pointer;
import com.sun.jna.WString;
import com.sun.jna.win32.StdCallLibrary;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Objects;

/**
 * The string identity used by the legacy Windows Rite intent scope:
 * {@code ntpath.normcase(ntpath.normpath(original))}.
 *
 * <p>The path pass follows CPython 3.13.2's Windows _Py_skiproot and
 * _Py_normpath_and_size, with UTF-16 lengths, including embedded NULs. The
 * case pass uses the same invariant Windows NLS API as that release's ntpath;
 * neither Java's Unicode tables nor the default locale participate. This is
 * lexical DATA, not proof of an existing directory, allocator, or file identity.
 * No process is started and no filesystem is consulted.
 *
 * <p>Algorithm provenance: CPython v3.13.2 Python/fileutils.c,
 * Modules/posixmodule.c, Modules/_winapi.c and Lib/ntpath.py (PSF License v2).
 * Copyright (c) 2001-2024 Python Software Foundation; All Rights Reserved. See the accompanying
 * source-admission record for source links and license attribution.
 */
public final class LegacyWindowsPathCanonicalizer {
    public static final String ALGORITHM = "cpython-3.13.2-windows-ntpath-normcase-normpath/v1";
    public static final String REFERENCE_CPYTHON = "3.13.2";
    public static final String REFERENCE_UNICODE_DATA = "15.1.0";

    private LegacyWindowsPathCanonicalizer() {}

    /** Full normcase(normpath), preserving the original string's UTF-16 domain. */
    public static String normalize(String original) {
        Objects.requireNonNull(original, "original");
        Nls nls = NativeNls.instance();
        String path = pathPass(original);
        char[] source = path.toCharArray();
        int needed = nls.LCMapStringEx(new WString(""), 0x100, source,
                source.length, null, 0, null, null, null);
        if (needed <= 0) throw nlsFailure("LCMapStringEx(size)");
        char[] destination = new char[needed];
        int written = nls.LCMapStringEx(new WString(""), 0x100, source,
                source.length, destination, destination.length, null, null, null);
        if (written <= 0) throw nlsFailure("LCMapStringEx(map)");
        if (written > destination.length) throw new IllegalStateException("NLS output exceeded allocation");
        return new String(destination, 0, written);
    }

    /**
     * Runtime provenance. CPython's UCD version is not the Windows casing table
     * version. GetNLSVersionEx exposes a sort signature, not a Unicode-standard
     * casing version; the latter is explicitly reported as unexposed.
     */
    public static CasingVersion casingVersion() {
        Nls nls = NativeNls.instance();
        try (Memory version = new Memory(32)) {
            version.clear();
            version.setInt(0, 32);
            if (nls.GetNLSVersionEx(1, new WString(""), version) == 0) {
                throw nlsFailure("GetNLSVersionEx");
            }
            return new CasingVersion(ALGORITHM, REFERENCE_CPYTHON, REFERENCE_UNICODE_DATA,
                    "WINDOWS_NLS_UNICODE_VERSION_NOT_EXPOSED",
                    hex(version.getInt(4)), hex(version.getInt(8)), hex(version.getInt(12)),
                    HexFormat.of().formatHex(version.getByteArray(16, 16)));
        }
    }

    public record CasingVersion(String algorithm, String referenceCpython,
            String referenceUnicodeData, String casingUnicodeVersion,
            String nlsVersionHex, String definedVersionHex, String effectiveLocaleHex,
            String customVersionBytesHex) {
        public CasingVersion {
            Objects.requireNonNull(algorithm); Objects.requireNonNull(referenceCpython);
            Objects.requireNonNull(referenceUnicodeData); Objects.requireNonNull(casingUnicodeVersion);
            Objects.requireNonNull(nlsVersionHex); Objects.requireNonNull(definedVersionHex);
            Objects.requireNonNull(effectiveLocaleHex); Objects.requireNonNull(customVersionBytesHex);
        }
    }

    private static String hex(int value) {
        return String.format(java.util.Locale.ROOT, "%08x", value);
    }

    private static IllegalStateException nlsFailure(String operation) {
        return new IllegalStateException(operation + " failed, Windows error " + Native.getLastError());
    }

    // A fixed-width char buffer is deliberate: WString/NUL-terminated results
    // would truncate embedded NULs that the original explicitly sized APIs keep.
    private interface Nls extends StdCallLibrary {
        int LCMapStringEx(WString locale, int flags, char[] source, int sourceLength,
                char[] destination, int destinationLength, Pointer version, Pointer reserved,
                Pointer sortHandle);
        int GetNLSVersionEx(int function, WString locale, Pointer version);
    }

    private static final class NativeNls {
        private static final class Holder {
            private static final Nls API = Native.load("kernel32", Nls.class);
        }
        private static Nls instance() {
            if (!Platform.isWindows() || Native.WCHAR_SIZE != 2) {
                throw new UnsupportedOperationException("Legacy Windows path identity requires Windows NLS");
            }
            return Holder.API;
        }
    }

    private static boolean separator(char value) { return value == '\\' || value == '/'; }

    private static boolean boundary(char[] path, int offset, int length) {
        return offset == length || separator(path[offset]);
    }

    private static int rootLength(char[] path, int length) {
        if (separator(path[0])) {
            if (!separator(path[1])) return 1;
            int offset = path[2] == '?' && separator(path[3])
                    && (path[4] == 'U' || path[4] == 'u')
                    && (path[5] == 'N' || path[5] == 'n')
                    && (path[6] == 'C' || path[6] == 'c') && separator(path[7]) ? 8 : 2;
            while (!boundary(path, offset, length)) offset++;
            if (offset == length) return offset;
            offset++;
            while (!boundary(path, offset, length)) offset++;
            return offset == length ? offset : offset + 1;
        }
        if (length != 0 && path[1] == ':') return separator(path[2]) ? 3 : 2;
        return 0;
    }

    private static String pathPass(String original) {
        int length = original.length();
        if (length == 0) return ".";
        char[] path = Arrays.copyOf(original.toCharArray(), Math.addExact(length, 8));
        int read = rootLength(path, length);
        int write = read;
        int minimum = 0;
        char last = 0;
        if (read != 0) {
            for (int i = 0; i < read; i++) if (path[i] == '/') path[i] = '\\';
            minimum = write - 1;
            last = path[minimum];
            if (last != '\\') minimum++;
        }
        if (path[read] == '.' && boundary(path, read + 1, length)) {
            last = path[++read];
            if (last == '/') last = '\\';
            while (separator(path[read])) read++;
        }
        while (read != length) {
            char current = path[read] == '/' ? '\\' : path[read];
            if (last == '\\') {
                if (current == '.') {
                    boolean atOne = boundary(path, read + 1, length);
                    boolean atTwo = !atOne && boundary(path, read + 2, length);
                    if (atTwo && path[read + 1] == '.') {
                        int previous = write;
                        while (previous != minimum && path[--previous] == '\\') { }
                        while (previous != minimum && path[previous - 1] != '\\') previous--;
                        if (write == minimum || (path[previous] == '.'
                                && path[previous + 1] == '.' && separator(path[previous + 2]))) {
                            path[write++] = '.'; path[write++] = '.'; last = '.';
                        } else if (path[previous] == '\\') {
                            write = previous + 1;
                        } else {
                            write = previous;
                        }
                        read++;
                    } else if (!atOne) {
                        path[write++] = last = current;
                    }
                } else if (current != '\\') {
                    path[write++] = last = current;
                }
            } else {
                path[write++] = last = current;
            }
            read++;
        }
        path[write] = 0;
        int end = write;
        if (end != minimum) {
            do { end--; } while (end != minimum && path[end] == '\\');
            end++;
        }
        return end == 0 ? "." : new String(path, 0, end);
    }
}
