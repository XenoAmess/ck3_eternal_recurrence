package org.xar.ck3.markets.saveaudit;

import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.Arrays;
import java.util.Map;
import java.util.LinkedHashMap;
import java.util.Set;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts.Pin;
import org.xar.ck3.save.SaveJson;
import org.xar.ck3.save.SaveDecoder;

/** Optional named host; default validate/build and the acceptance entry stay unchanged. */
@QuarkusMain(name = "save-audit")
public final class SaveAuditCommand implements QuarkusApplication {
    public record Request(int schemaVersion, String repository, FinancialSaveAuditMain.Inputs audit) {
        public Request {
            if (schemaVersion != 1 || repository == null || !Path.of(repository).isAbsolute() || audit == null)
                throw new IllegalArgumentException("version 1, absolute repository and complete audit inputs required");
        }
    }
    public record Report(String schema, String machineId, String observedAtUtc, Request request,
                         SaveAuditSources.Binding producers, FinancialSaveAuditMain.Output audit,
                         boolean financialCertified) {
        public Report {
            if (!"ck3-financial-save-audit-source-bound-candidate-v2".equals(schema) || request == null || producers == null
                    || audit == null || financialCertified || audit.financialCertified()
                    || !request.audit().machineId().equals(machineId) || !audit.machineId().equals(machineId))
                throw new IllegalArgumentException("source-bound unqualified candidate report required");
            Instant.parse(observedAtUtc);
        }
    }
    public record RetiredObserverReport(String schema, String machineId, String observedAtUtc, Request request,
                                        SaveAuditSources.Binding producers, FinancialSaveAuditMain.RetiredObserverOutput audit,
                                        boolean financialCertified) {
        public RetiredObserverReport {
            if (!"ck3-financial-save-audit-retired-xfma-source-bound-candidate-v1".equals(schema) || request == null || producers == null
                    || audit == null || financialCertified || audit.financial().financialCertified()
                    || !request.audit().machineId().equals(machineId) || !audit.financial().machineId().equals(machineId))
                throw new IllegalArgumentException("explicit source-bound retired-xfma candidate report required");
            Instant.parse(observedAtUtc);
        }
    }
    public record Receipt(Pin report, FinancialAudit.Assessment firstAssessment, List<FinancialAudit.Assessment> coldAssessments,
                          int exitCode, boolean financialCertified) {
        public Receipt {
            coldAssessments = List.copyOf(coldAssessments);
            if (report == null || firstAssessment == null || financialCertified || exitCode < 0 || exitCode > 3)
                throw new IllegalArgumentException("written candidate report receipt required");
        }
    }
    @Override public int run(String... args) {
        if (args.length > 0 && args[0].equals("audit-news-toast"))
            return NewsToastAuditCommand.run(Arrays.copyOfRange(args, 1, args.length), SaveDecoder::launch);
        try {
            if (args.length != 5 || !Set.of("audit", "audit-retired-xfma").contains(args[0])) throw new IllegalArgumentException("expected audit|audit-retired-xfma --inputs request.json --output unused-report.json");
            Map<String, String> options = new LinkedHashMap<>(); Set<String> allowed = Set.of("--inputs", "--output");
            for (int i = 1; i < args.length; i += 2) {
                if (!allowed.contains(args[i]) || args[i + 1].isBlank() || options.putIfAbsent(args[i], args[i + 1]) != null)
                    throw new IllegalArgumentException("invalid or duplicate audit option");
            }
            Request request = readRequest(Path.of(options.get("--inputs"))); Path output = Path.of(options.get("--output"));
            Receipt receipt = args[0].equals("audit") ? emit(request, output) : emitRetiredXfma(request, output);
            System.out.println(new String(SaveJson.write(receipt), java.nio.charset.StandardCharsets.UTF_8));
            return receipt.exitCode();
        } catch (IOException | IllegalArgumentException | IllegalStateException error) {
            System.err.println("XFM SAVE AUDIT FAILED: " + error.getMessage()); return 1;
        }
    }
    public static Request readRequest(Path input) throws IOException {
        if (Files.size(input) > 65536) throw new IOException("audit request exceeds 64 KiB");
        return SaveJson.read(Files.readAllBytes(input), Request.class);
    }
    public static Receipt emitRetiredXfma(Request request, Path output) throws IOException {
        Path repo = Path.of(request.repository()).toRealPath(), destination = output.toAbsolutePath().normalize();
        Path parent = destination.getParent();
        if (parent == null || !Files.isDirectory(parent) || destination.startsWith(repo) || repo.startsWith(destination)
                || parent.toRealPath().startsWith(repo) || Files.exists(destination, LinkOption.NOFOLLOW_LINKS))
            throw new IOException("unused report path with existing external parent required");
        SaveAuditSources.Binding before = SaveAuditSources.verify(repo);
        FinancialSaveAuditMain.RetiredObserverOutput data = FinancialSaveAuditMain.inspectRetiredXfma(request.audit());
        if (!before.equals(SaveAuditSources.verify(repo))) throw new IOException("loaded compatible audit/parser producer changed");
        RetiredObserverReport report = new RetiredObserverReport("ck3-financial-save-audit-retired-xfma-source-bound-candidate-v1",
                request.audit().machineId(), Instant.now().toString(), request, before, data, false);
        Files.write(destination, SaveJson.write(report), StandardOpenOption.CREATE_NEW);
        List<FinancialAudit.Assessment> cold = data.financial().second().stream().map(s -> s.audit().assessment()).toList();
        FinancialAudit.Assessment first = data.financial().first().audit().assessment();
        boolean violation = first == FinancialAudit.Assessment.VIOLATION || cold.contains(FinancialAudit.Assessment.VIOLATION);
        boolean incomplete = first == FinancialAudit.Assessment.INCOMPLETE || cold.contains(FinancialAudit.Assessment.INCOMPLETE)
                || data.financial().coldComparison().stream().anyMatch(c -> !c.exactSelectedFinancialState());
        return new Receipt(FilePins.pin(destination), first, cold, violation ? 3 : incomplete ? 2 : 0, false);
    }
    public static Receipt emit(Request request, Path output) throws IOException {
        Path repo = Path.of(request.repository()).toRealPath(), destination = output.toAbsolutePath().normalize();
        Path parent = destination.getParent();
        if (parent == null || !Files.isDirectory(parent) || destination.startsWith(repo) || repo.startsWith(destination)
                || parent.toRealPath().startsWith(repo) || Files.exists(destination, LinkOption.NOFOLLOW_LINKS))
            throw new IOException("unused report path with existing external parent required");
        SaveAuditSources.Binding before = SaveAuditSources.verify(repo);
        FinancialSaveAuditMain.Output data = FinancialSaveAuditMain.inspect(request.audit());
        if (!before.equals(SaveAuditSources.verify(repo))) throw new IOException("loaded audit/parser producer changed during inspection");
        Report report = new Report("ck3-financial-save-audit-source-bound-candidate-v2", request.audit().machineId(), Instant.now().toString(), request, before, data, false);
        byte[] encoded = SaveJson.write(report);
        Files.write(destination, encoded, StandardOpenOption.CREATE_NEW);
        List<FinancialAudit.Assessment> cold = data.second().stream().map(s -> s.audit().assessment()).toList();
        boolean violation = data.first().audit().assessment() == FinancialAudit.Assessment.VIOLATION || cold.contains(FinancialAudit.Assessment.VIOLATION);
        boolean incomplete = data.first().audit().assessment() == FinancialAudit.Assessment.INCOMPLETE || cold.contains(FinancialAudit.Assessment.INCOMPLETE)
                || data.coldComparison().stream().anyMatch(c -> !c.exactSelectedFinancialState());
        return new Receipt(FilePins.pin(destination), data.first().audit().assessment(), cold, violation ? 3 : incomplete ? 2 : 0, false);
    }
}
