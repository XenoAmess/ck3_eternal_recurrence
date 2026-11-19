package org.xar.ck3.markets.saveaudit;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts.Pin;
import org.xar.ck3.save.SaveDecoder;
import org.xar.ck3.save.SaveJson;

/** Operation of the existing save-audit Quarkus host; no new parser, transport or Game worker. */
public final class NewsToastAuditCommand {
    private NewsToastAuditCommand() { }
    public record Receipt(Pin report, NewsToastDelivery.Assessment assessment, NewsToastDelivery.Reason reason,
                          int exitCode, boolean sourceJoinMatched, boolean deliveryConfirmed, boolean gameStarted) {
        public Receipt {
            if (report == null || assessment == null || reason == null || deliveryConfirmed || gameStarted
                    || exitCode < 0 || exitCode > 3 || sourceJoinMatched != (assessment == NewsToastDelivery.Assessment.LOCAL_NATIVE_JOIN_MATCH))
                throw new IllegalArgumentException("written unqualified news join receipt required");
        }
    }
    public static int run(String[] args, SaveDecoder.Launcher launcher) {
        try {
            if (args.length != 4 || !args[0].equals("--inputs") || !args[2].equals("--output"))
                throw new IllegalArgumentException("audit-news-toast requires --inputs request.json --output unused-report.json");
            Path input = Path.of(args[1]), output = Path.of(args[3]).toAbsolutePath().normalize();
            if (Files.size(input) > 65536) throw new IOException("bounded news join request required");
            NewsToastDelivery.Request request = SaveJson.read(NewsToastDelivery.readBounded(input, 65536), NewsToastDelivery.Request.class);
            Path repo = Path.of(request.repository()).toRealPath(), parent = output.getParent();
            if (parent == null || !Files.isDirectory(parent) || output.startsWith(repo) || repo.startsWith(output)
                    || parent.toRealPath().startsWith(repo) || Files.exists(output, LinkOption.NOFOLLOW_LINKS))
                throw new IOException("unused external report with existing parent required");
            NewsToastDelivery.Report report = NewsToastDelivery.inspect(request, launcher);
            byte[] bytes = SaveJson.write(report);
            if (bytes.length > 2 * 1024 * 1024) throw new IOException("bounded news join report required");
            Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
            int code = switch (report.assessment()) { case LOCAL_NATIVE_JOIN_MATCH -> 0; case UNAVAILABLE -> 2; case MISMATCH -> 3; };
            System.out.println(new String(SaveJson.write(new Receipt(FilePins.pin(output), report.assessment(), report.reason(), code,
                    report.sourceJoinMatched(), false, false)), StandardCharsets.UTF_8));
            return code;
        } catch (IOException | IllegalArgumentException | IllegalStateException failed) {
            System.err.println("NEWS TOAST SOURCE JOIN FAILED: " + failed.getMessage()); return 1;
        }
    }
}
