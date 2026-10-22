package org.xar.ck3.control.build;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.IPHlpAPI;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.W32APIOptions;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;

/** Read-only, bounded original Windows IPv4 listener ownership through pinned JNA. */
public final class NativeTcpListener {
    private static final int AF_INET = 2;
    private static final int TCP_TABLE_OWNER_PID_LISTENER = 3;
    private static final int ERROR_INSUFFICIENT_BUFFER = 122;
    private static final int TABLE_MAX_BYTES = 1 << 20;
    private static final int ROW_BYTES = 24;

    private NativeTcpListener() {}

    /** A native uint32 PID is retained as a positive Java long without narrowing. */
    public record ListenerOwner(long pid, String address, int port) {
        public ListenerOwner {
            if (pid < 1 || pid > 0xffff_ffffL) {
                throw new IllegalArgumentException("native uint32 PID required");
            }
            requirePort(port);
            Objects.requireNonNull(address, "native IPv4 address");
            String[] octets = address.split("\\.", -1);
            if (octets.length != 4 || address.length() > 15) {
                throw new IllegalArgumentException("canonical native IPv4 address required");
            }
            for (String octet : octets) {
                if (!octet.matches("0|[1-9][0-9]{0,2}") || Integer.parseInt(octet) > 255) {
                    throw new IllegalArgumentException("canonical native IPv4 octet required");
                }
            }
        }
    }

    /**
     * Return current listener owners, never HTTP claims or cached ownership.
     *
     * Native contracts:
     * https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable
     * https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid
     */
    public static List<ListenerOwner> owners(int port) {
        requirePort(port);
        if (!System.getProperty("os.name").startsWith("Windows") || Native.POINTER_SIZE != 8) {
            throw new IllegalStateException("original Windows x64 native environment required; no skip");
        }
        String systemRoot = Objects.requireNonNull(System.getenv("SystemRoot"), "SystemRoot");
        Path libraryPath = Path.of(systemRoot, "System32", "iphlpapi.dll").toAbsolutePath();
        IPHlpAPI api = Native.load(libraryPath.toString(), IPHlpAPI.class, W32APIOptions.DEFAULT_OPTIONS);
        IntByReference size = new IntByReference();
        for (int attempt = 0; attempt < 3; attempt++) {
            size.setValue(0);
            int result = api.GetExtendedTcpTable(Pointer.NULL, size, false,
                    AF_INET, TCP_TABLE_OWNER_PID_LISTENER, 0);
            if (result != 0 && result != ERROR_INSUFFICIENT_BUFFER) {
                throw new IllegalStateException("GetExtendedTcpTable size query failed: "
                        + Integer.toUnsignedString(result));
            }
            long length = Integer.toUnsignedLong(size.getValue());
            if (length < 4 || length > TABLE_MAX_BYTES) {
                throw new IllegalStateException("bounded complete native TCP table required");
            }
            try (Memory table = new Memory(length)) {
                result = api.GetExtendedTcpTable(table, size, false,
                        AF_INET, TCP_TABLE_OWNER_PID_LISTENER, 0);
                if (result == ERROR_INSUFFICIENT_BUFFER) {
                    continue; // The native table can grow between its two read-only calls.
                }
                if (result != 0) {
                    throw new IllegalStateException("GetExtendedTcpTable read failed: "
                            + Integer.toUnsignedString(result));
                }
                long actualLength = Integer.toUnsignedLong(size.getValue());
                if (actualLength < 4 || actualLength > length) {
                    throw new IllegalStateException("original native TCP table extent rejected");
                }
                return parseIpv4Owners(table.getByteBuffer(0, actualLength), port);
            }
        }
        throw new IllegalStateException("native TCP table changed during three bounded read attempts");
    }

    /** Pure native-layout decoder; package visibility permits malformed-buffer regression. */
    static List<ListenerOwner> parseIpv4Owners(ByteBuffer originalTable, int port) {
        requirePort(port);
        ByteBuffer table = originalTable.slice().order(ByteOrder.LITTLE_ENDIAN);
        if (table.remaining() < 4 || table.remaining() > TABLE_MAX_BYTES) {
            throw new IllegalArgumentException("bounded complete native TCP table required");
        }
        long count = Integer.toUnsignedLong(table.getInt(0));
        if (count > (table.remaining() - 4) / ROW_BYTES) {
            throw new IllegalArgumentException("native TCP row count exceeds original table extent");
        }
        List<ListenerOwner> result = new ArrayList<>();
        for (int index = 0; index < count; index++) {
            int offset = 4 + index * ROW_BYTES;
            int state = table.getInt(offset);
            int localAddress = table.getInt(offset + 4);
            int nativePort = table.getInt(offset + 8);
            int actualPort = Short.toUnsignedInt(Short.reverseBytes((short) (nativePort & 0xffff)));
            if (actualPort != port) {
                continue;
            }
            if (state != 2) { // MIB_TCP_STATE_LISTEN
                throw new IllegalArgumentException("listener-only native table returned another TCP state");
            }
            long pid = Integer.toUnsignedLong(table.getInt(offset + 20));
            String address = (localAddress & 0xff) + "." + ((localAddress >>> 8) & 0xff)
                    + "." + ((localAddress >>> 16) & 0xff) + "." + ((localAddress >>> 24) & 0xff);
            result.add(new ListenerOwner(pid, address, port));
        }
        result.sort(Comparator.comparingLong(ListenerOwner::pid)
                .thenComparing(ListenerOwner::address).thenComparingInt(ListenerOwner::port));
        return List.copyOf(result);
    }

    private static void requirePort(int port) {
        if (port < 1 || port > 65535) {
            throw new IllegalArgumentException("TCP port must be an exact integer in 1..65535");
        }
    }
}
