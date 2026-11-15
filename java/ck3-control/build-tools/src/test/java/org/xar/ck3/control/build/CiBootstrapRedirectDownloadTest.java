package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;

import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;

final class CiBootstrapRedirectDownloadTest {
    @Test
    @Timeout(30)
    void fixedReleaseDownloadFollowsArchiveRedirectWithoutLosingTheBodyBound(@TempDir Path root) throws Exception {
        byte[] archive = "reviewed-fixed-release".getBytes(StandardCharsets.UTF_8);
        AtomicInteger redirects = new AtomicInteger();
        AtomicInteger downloads = new AtomicInteger();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/distribution", exchange -> {
            redirects.incrementAndGet();
            exchange.getResponseHeaders().add("Location", "/archive");
            exchange.sendResponseHeaders(302, -1);
            exchange.close();
        });
        server.createContext("/archive", exchange -> {
            downloads.incrementAndGet();
            exchange.sendResponseHeaders(200, archive.length);
            try (var output = exchange.getResponseBody()) { output.write(archive); }
            exchange.close();
        });
        server.start();
        try {
            var download = CiBootstrap.class.getDeclaredMethod("download", URI.class, Path.class, long.class);
            download.setAccessible(true);
            Path target = root.resolve("fixed-release.zip");
            download.invoke(null, URI.create("http://127.0.0.1:" + server.getAddress().getPort() + "/distribution"),
                    target, (long) archive.length);
            assertArrayEquals(archive, Files.readAllBytes(target));
            assertEquals(1, redirects.get());
            assertEquals(1, downloads.get());
        } finally {
            server.stop(0);
        }
    }
}
