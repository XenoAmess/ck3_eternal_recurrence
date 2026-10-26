package org.xar.ck3.save;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.save.SaveContracts.Decoded;
import org.xar.ck3.save.SaveContracts.DecoderLimits;
import org.xar.ck3.save.SaveContracts.Pin;
import org.xar.ck3.save.SaveContracts.Selection;

/** Shared executable offline inspection. It does not assert product business success or start CK3. */
public final class Inspection {
    private Inspection() { }
    public static void main(String[] args) { System.exit(run(args)); }
    public record Request(int schemaVersion, String machineId, String repository, Pin save, Pin decoder, Selection selection) {
        public Request {
            if (schemaVersion != 4 || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}") || repository == null || !Path.of(repository).isAbsolute()) throw new IllegalArgumentException("version 4, machine and repository required");
            Objects.requireNonNull(save); Objects.requireNonNull(decoder); Objects.requireNonNull(selection);
        }
    }
    public enum BusinessAssessment { NOT_ASSESSED }
    public record Report(String schema, String machineId, String observedAtUtc, Request request, Decoded decoded,
                         ProducerSources.Binding producer, BusinessAssessment businessAssessment, boolean gameStarted) {
        public Report {
            if (!"ck3-save-inspection-v4".equals(schema) || request == null || decoded == null || producer == null || businessAssessment != BusinessAssessment.NOT_ASSESSED || gameStarted || !request.machineId().equals(machineId) || !request.save().equals(decoded.save()) || !request.decoder().equals(decoded.decoder())) throw new IllegalArgumentException("complete offline inspection required");
            Instant.parse(observedAtUtc);
        }
    }
    public record Receipt(Pin report, int selectedRecords, int selectedProjections, boolean gameStarted) { }
    public static Report inspect(Request request) throws IOException {
        return inspect(request, SaveDecoder::launch);
    }
    public static Report inspect(Request request, SaveDecoder.Launcher launcher) throws IOException {
        ProducerSources.Binding before = ProducerSources.verify(Path.of(request.repository()));
        Decoded decoded = SaveDecoder.inspect(request.save(), request.decoder(), request.selection(), DecoderLimits.standard(), launcher);
        if (!before.equals(ProducerSources.verify(Path.of(request.repository())))) throw new IOException("save-core producer changed during inspection");
        return new Report("ck3-save-inspection-v4", request.machineId(), Instant.now().toString(), request, decoded, before, BusinessAssessment.NOT_ASSESSED, false);
    }
    public static int run(String[] args) {
        return run(args, SaveDecoder::launch);
    }
    public static int run(String[] args, SaveDecoder.Launcher launcher) {
        try {
            if (args.length != 4 || !args[0].equals("--inputs") || !args[2].equals("--output")) throw new IllegalArgumentException("inspect-save-v4 requires --inputs request.json --output unused-report.json");
            Path input = Path.of(args[1]); Path output = Path.of(args[3]).toAbsolutePath().normalize();
            if (Files.size(input) > 65536 || Files.exists(output)) throw new IOException("bounded request and unused output required");
            Request request = SaveJson.read(Files.readAllBytes(input), Request.class);
            Report report = inspect(request, launcher); byte[] bytes = SaveJson.write(report);
            if (bytes.length > 1024 * 1024) throw new IOException("report exceeds one MiB output budget");
            Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
            System.out.println(new String(SaveJson.write(new Receipt(FilePins.pin(output), report.decoded().projection().scopes().size(), report.decoded().projection().projections().size(), false)), StandardCharsets.UTF_8));
            return 0;
        } catch (IOException | IllegalArgumentException error) {
            System.err.println("SHARED SAVE INSPECTION FAILED: " + error.getMessage()); return 1;
        }
    }
}
