package org.xar.ck3.save;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

/** Shared bounded request/output boundary; original inspect-save-v4 remains unchanged. */
final class InspectionFiles {
    private static final int MAX_REQUEST_BYTES = 64 * 1024;
    private static final int MAX_REPORT_BYTES = 1024 * 1024;

    private InspectionFiles() { }
    @FunctionalInterface interface Producer<Q, R> { R produce(Q request) throws IOException; }
    record Receipt(SaveContracts.Pin report, boolean gameStarted) { }
    static <T> T bounded(T report) throws IOException {
        if (SaveJson.write(report).length > MAX_REPORT_BYTES) throw new IOException("report exceeds one MiB output budget");
        return report;
    }
    static <T> T readReport(byte[] bytes, Class<T> type) throws IOException {
        if (bytes.length > MAX_REPORT_BYTES) throw new IOException("report exceeds one MiB output budget");
        return SaveJson.read(bytes, type);
    }
    static <Q, R> int run(String[] args, Class<Q> requestType, Producer<Q, R> producer) {
        try {
            if (args.length != 4 || !args[0].equals("--inputs") || !args[2].equals("--output"))
                throw new IllegalArgumentException("requires --inputs request.json --output unused-report.json");
            Path input = Path.of(args[1]); Path output = Path.of(args[3]).toAbsolutePath().normalize();
            if (Files.exists(output)) throw new IOException("unused report output required");
            byte[] request;
            try (InputStream stream = Files.newInputStream(input)) {
                request = stream.readNBytes(MAX_REQUEST_BYTES + 1);
            }
            if (request.length > MAX_REQUEST_BYTES) throw new IOException("request exceeds 64 KiB input budget");
            R report = producer.produce(SaveJson.read(request, requestType));
            byte[] bytes = SaveJson.write(report);
            if (bytes.length > MAX_REPORT_BYTES) throw new IOException("report exceeds one MiB output budget");
            Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
            System.out.println(new String(SaveJson.write(new Receipt(FilePins.pin(output), false)), StandardCharsets.UTF_8)); return 0;
        } catch (IOException | IllegalArgumentException error) {
            System.err.println("SHARED SAVE INSPECTION FAILED: " + error.getMessage()); return 1;
        }
    }
}
