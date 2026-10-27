package org.xar.ck3.save;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

/** Shared bounded request/output boundary; original inspect-save-v4 remains unchanged. */
final class InspectionFiles {
    private InspectionFiles() { }
    @FunctionalInterface interface Producer<Q, R> { R produce(Q request) throws IOException; }
    record Receipt(SaveContracts.Pin report, boolean gameStarted) { }
    static <T> T bounded(T report) throws IOException {
        if (SaveJson.write(report).length > 1024 * 1024) throw new IOException("report exceeds one MiB output budget");
        return report;
    }
    static <T> T readReport(byte[] bytes, Class<T> type) throws IOException {
        if (bytes.length > 1024 * 1024) throw new IOException("report exceeds one MiB output budget");
        return SaveJson.read(bytes, type);
    }
    static <Q, R> int run(String[] args, Class<Q> requestType, Producer<Q, R> producer) {
        try {
            if (args.length != 4 || !args[0].equals("--inputs") || !args[2].equals("--output"))
                throw new IllegalArgumentException("requires --inputs request.json --output unused-report.json");
            Path input = Path.of(args[1]); Path output = Path.of(args[3]).toAbsolutePath().normalize();
            if (Files.size(input) > 65536 || Files.exists(output)) throw new IOException("bounded request and unused output required");
            R report = producer.produce(SaveJson.read(Files.readAllBytes(input), requestType));
            byte[] bytes = SaveJson.write(report);
            if (bytes.length > 1024 * 1024) throw new IOException("report exceeds one MiB output budget");
            Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
            System.out.println(new String(SaveJson.write(new Receipt(FilePins.pin(output), false)), StandardCharsets.UTF_8)); return 0;
        } catch (IOException | IllegalArgumentException error) {
            System.err.println("SHARED SAVE INSPECTION FAILED: " + error.getMessage()); return 1;
        }
    }
}
