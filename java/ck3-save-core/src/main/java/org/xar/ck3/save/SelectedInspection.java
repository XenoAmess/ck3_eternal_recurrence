package org.xar.ck3.save;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.save.SaveContracts.*;

/** Bounded selected records; inventory IDs are deliberately absent from this wire contract. */
public final class SelectedInspection {
    private SelectedInspection() { }
    public enum InventoryAssessment { OMITTED_NOT_QUALIFIED }
    public record Selected(List<Scope> scopes, List<RecordObservation> records, List<ProjectionScope> projections,
                           List<ProjectionObservation> projectionObservations, List<String> rootKeys,
                           List<Clausewitz.Entry> rootScalars, long tokens, int selectedTokenBytes) {
        public Selected {
            scopes = List.copyOf(scopes); records = List.copyOf(records); projections = List.copyOf(projections);
            projectionObservations = List.copyOf(projectionObservations); rootKeys = List.copyOf(rootKeys); rootScalars = List.copyOf(rootScalars);
            if (tokens < 0 || selectedTokenBytes < 0 || selectedTokenBytes > 4 * 1024 * 1024 || scopes.size() > 1025
                    || records.size() > 1024 || projections.size() > 65536 || rootKeys.size() > 512 || rootScalars.size() > 512)
                throw new IllegalArgumentException("bounded selected projection required");
        }
    }
    public record Report(String schema, String machineId, String observedAtUtc, Inspection.Request request, Selected selected,
                         SaveDecoder.ReadEvidence decoder, ProducerSources.Binding producerBefore, ProducerSources.Binding producerAfter,
                         InventoryAssessment inventoryAssessment, Inspection.BusinessAssessment businessAssessment, boolean gameStarted) {
        public Report {
            if (!"ck3-save-selected-v1".equals(schema) || request == null || selected == null || decoder == null
                    || !request.save().equals(decoder.save()) || !request.decoder().equals(decoder.decoder())
                    || !request.machineId().equals(machineId) || producerBefore == null || !producerBefore.equals(producerAfter)
                    || inventoryAssessment != InventoryAssessment.OMITTED_NOT_QUALIFIED
                    || businessAssessment != Inspection.BusinessAssessment.NOT_ASSESSED || gameStarted)
                throw new IllegalArgumentException("complete selected-only offline report required");
            Instant.parse(observedAtUtc);
            if (selected.tokens() > Long.parseLong(decoder.streamBytes())) throw new IllegalArgumentException("tokens exceed complete stream bytes");
            validate(request.selection(), selected);
        }
    }
    public static Report inspect(Inspection.Request request) throws IOException { return inspect(request, SaveDecoder::launch); }
    /** Callers may retain their own stronger OS handles and SDK/custody checks around this call. */
    public static Report inspect(Inspection.Request request, SaveDecoder.Launcher launcher) throws IOException {
        requireSelection(request.selection());
        ProducerSources.Binding before = ProducerSources.verify(Path.of(request.repository()));
        SaveDecoder.StreamDecoded<Projection> decoded = SaveDecoder.decode(request.save(), request.decoder(), DecoderLimits.standard(), launcher,
                reader -> new SaveStream(reader, request.selection()).read());
        ProducerSources.Binding after = ProducerSources.verify(Path.of(request.repository()));
        Projection p = decoded.value();
        return InspectionFiles.bounded(new Report("ck3-save-selected-v1", request.machineId(), Instant.now().toString(), request,
                new Selected(p.scopes(), p.records(), p.projections(), p.projectionObservations(), p.rootKeys(), p.rootScalars(), p.tokens(), p.selectedTokenBytes()),
                decoded.evidence(), before, after, InventoryAssessment.OMITTED_NOT_QUALIFIED, Inspection.BusinessAssessment.NOT_ASSESSED, false));
    }
    private static void requireSelection(Selection selection) {
        if (selection.structureCensus()) throw new IllegalArgumentException("selected-only report cannot request structural inventory qualification");
    }
    private static void validate(Selection selection, Selected result) {
        requireSelection(selection);
        List<RecordObservation> expected = new ArrayList<>();
        for (TableSelection table : selection.tables()) for (NativeId id : table.ids()) {
            List<String> path = child(table.path(), id.value());
            List<RecordObservation> found = result.records().stream().filter(r -> r.kind() == table.kind() && r.id().equals(id) && r.path().equals(path)).toList();
            if (found.size() != 1 || table.required() && found.getFirst().status() != RecordStatus.FULL_RECORD)
                throw new IllegalArgumentException("selected record observation missing or duplicated");
            expected.add(found.getFirst());
        }
        if (expected.size() != result.records().size() || new HashSet<>(result.records()).size() != result.records().size())
            throw new IllegalArgumentException("unexpected record observations");
        List<List<String>> scopePaths = new ArrayList<>();
        for (Scope scope : result.scopes()) {
            if (scope.kind() == ScopeKind.METADATA) {
                if (!scope.path().equals(List.of("meta_data")) || scope.coverage() != Coverage.DIRECT_SCALARS)
                    throw new IllegalArgumentException("metadata coverage mismatch");
            } else if (scope.coverage() != Coverage.FULL_RECORD || result.records().stream().noneMatch(r -> r.kind() == scope.kind()
                    && r.path().equals(scope.path()) && r.status() == RecordStatus.FULL_RECORD)) throw new IllegalArgumentException("unrequested scope");
            if (scope.coverage() == Coverage.FULL_RECORD && !scope.canonicalTokenSha256().equals(canonicalHash(scope.ast())))
                throw new IllegalArgumentException("selected AST/token digest mismatch");
            scopePaths.add(scope.path());
        }
        if (new HashSet<>(scopePaths).size() != scopePaths.size() || selection.metadataRequired() && !scopePaths.contains(List.of("meta_data")))
            throw new IllegalArgumentException("missing or duplicate selected AST");
        for (RecordObservation record : result.records()) if ((record.status() == RecordStatus.FULL_RECORD) != scopePaths.contains(record.path()))
            throw new IllegalArgumentException("selected record AST/status mismatch");
        if (result.projectionObservations().size() != selection.projections().size()) throw new IllegalArgumentException("projection observations missing");
        for (ProjectionSelection projection : selection.projections()) {
            List<ProjectionScope> scopes = result.projections().stream().filter(p -> p.name().equals(projection.name())).toList();
            List<ProjectionObservation> observations = result.projectionObservations().stream().filter(p -> p.name().equals(projection.name())).toList();
            if (observations.size() != 1 || observations.getFirst().matches() != scopes.size() || scopes.size() > projection.maxMatches()
                    || projection.required() && scopes.isEmpty()) throw new IllegalArgumentException("projection coverage mismatch");
            for (int i = 0; i < scopes.size(); i++) {
                ProjectionScope scope = scopes.get(i);
                if (scope.kind() != projection.kind() || !scope.path().equals(projection.path()) || scope.occurrence() != i)
                    throw new IllegalArgumentException("projection source mismatch");
                if (!scope.canonicalTokenSha256().equals(canonicalHash(scope.ast()))) throw new IllegalArgumentException("projection AST/token digest mismatch");
            }
        }
        if (result.projections().stream().anyMatch(p -> selection.projections().stream().noneMatch(s -> s.name().equals(p.name()))))
            throw new IllegalArgumentException("unrequested projection");
        Objects.requireNonNull(result.rootScalars());
    }
    private static List<String> child(List<String> path, String id) { List<String> result = new ArrayList<>(path); result.add(id); return List.copyOf(result); }
    private static String canonicalHash(Clausewitz.Block ast) {
        return CanonicalTokens.selectedRecordHash(ast);
    }
    public static int run(String[] args, SaveDecoder.Launcher launcher) {
        return InspectionFiles.run(args, Inspection.Request.class, request -> inspect(request, launcher));
    }
    public static Report readReport(byte[] bytes) throws IOException { return InspectionFiles.readReport(bytes, Report.class); }
}
