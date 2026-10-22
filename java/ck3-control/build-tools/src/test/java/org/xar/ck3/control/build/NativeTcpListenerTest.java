package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.net.InetAddress;
import java.net.ServerSocket;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Native ownership is actually observed; missing Windows/JNA is a failure, never a skip. */
final class NativeTcpListenerTest {
    @Test
    void actualLoopbackListenerBelongsToThisProcessAndDisappearsAfterClose() throws Exception {
        int port;
        try (ServerSocket listener = new ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"))) {
            port = listener.getLocalPort();
            assertEquals(List.of(new NativeTcpListener.ListenerOwner(
                    ProcessHandle.current().pid(), "127.0.0.1", port)), NativeTcpListener.owners(port));
        }
        long until = System.nanoTime() + Duration.ofSeconds(2).toNanos();
        List<NativeTcpListener.ListenerOwner> owners;
        do {
            owners = NativeTcpListener.owners(port);
            if (!owners.isEmpty()) {
                Thread.sleep(10);
            }
        } while (!owners.isEmpty() && System.nanoTime() < until);
        assertTrue(owners.isEmpty(), "closed listener must not retain ownership credit");
    }

    @Test
    void decodesNetworkPortAddressAndUnsignedPidAndRejectsTruncatedOrWrongState() {
        ByteBuffer table = ByteBuffer.allocate(28).order(ByteOrder.LITTLE_ENDIAN);
        table.putInt(0, 1);
        table.putInt(4, 2);
        table.putInt(8, 0x0100007f);
        table.putInt(12, 0x991f); // network byte order for 8089
        table.putInt(24, -1);
        assertEquals(List.of(new NativeTcpListener.ListenerOwner(0xffff_ffffL, "127.0.0.1", 8089)),
                NativeTcpListener.parseIpv4Owners(table, 8089));
        assertEquals(List.of(), NativeTcpListener.parseIpv4Owners(table, 8090));
        assertThrows(IllegalArgumentException.class,
                () -> NativeTcpListener.parseIpv4Owners(table.duplicate().limit(27), 8089));
        table.putInt(4, 5);
        assertThrows(IllegalArgumentException.class,
                () -> NativeTcpListener.parseIpv4Owners(table, 8089));
        table.putInt(0, -1);
        assertThrows(IllegalArgumentException.class,
                () -> NativeTcpListener.parseIpv4Owners(table, 8089));
        assertThrows(IllegalArgumentException.class, () -> NativeTcpListener.owners(0));
        assertThrows(IllegalArgumentException.class, () -> NativeTcpListener.owners(65536));
    }
}
