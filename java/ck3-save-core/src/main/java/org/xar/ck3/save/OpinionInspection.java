package org.xar.ck3.save;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.save.SaveContracts.*;

/** Parameterized directed opinions; no product, run, character or modifier identity is inferred. */
public final class OpinionInspection {
    private OpinionInspection() { }
    public enum Expectation { EXACT_ONE, ABSENT }
    public record Pair(NativeId owner, NativeId target, Expectation expectation) {
        public Pair { Objects.requireNonNull(owner); Objects.requireNonNull(target); Objects.requireNonNull(expectation); }
    }
    public record Selection(List<String> tablePath, String modifier, String expectedValue, String expectedModify, List<Pair> pairs,
                            int maxRecordBytes, int maxMatchedBytes, int maxMatchedRows) {
        public Selection {
            tablePath = SaveContracts.checkedPath(tablePath); pairs = List.copyOf(pairs);
            if (modifier == null || !modifier.matches("[A-Za-z_][A-Za-z0-9_]{0,127}") || !number(expectedValue) || !number(expectedModify)
                    || pairs.isEmpty() || pairs.size() > 64 || maxRecordBytes < 1 || maxRecordBytes > 512 * 1024
                    || maxMatchedBytes < 1 || maxMatchedBytes > 256 * 1024 || maxMatchedRows < 1 || maxMatchedRows > 64)
                throw new IllegalArgumentException("bounded directed opinion selection required");
            if (new HashSet<>(pairs.stream().map(p -> List.of(p.owner(), p.target())).toList()).size() != pairs.size())
                throw new IllegalArgumentException("duplicate owner-target direction");
        }
    }
    public record Request(int schemaVersion, String machineId, String repository, Pin save, Pin decoder, Selection selection) {
        public Request {
            if (schemaVersion != 1 || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}")
                    || repository == null || !Path.of(repository).isAbsolute()) throw new IllegalArgumentException("version, machine and absolute repository required");
            Objects.requireNonNull(save); Objects.requireNonNull(decoder); Objects.requireNonNull(selection);
        }
    }
    public record Row(long ordinal, NativeId owner, NativeId target, Clausewitz.Block completeAst) {
        public Row {
            if (ordinal < 1 || owner == null || target == null || completeAst == null || !owner.equals(id(completeAst, "owner"))
                    || !target.equals(id(completeAst, "target"))) throw new IllegalArgumentException("original directed row AST required");
        }
    }
    public record Modifier(String value, String modify, Clausewitz.Block completeAst) {
        public Modifier {
            if (completeAst == null || !number(value) || !number(modify) || !value.equals(atom(completeAst, "value"))
                    || !modify.equals(atom(completeAst, "modify"))) throw new IllegalArgumentException("original numeric modifier fields required");
        }
    }
    public record Finding(Pair pair, List<Row> rows, List<Modifier> modifiers) {
        public Finding {
            Objects.requireNonNull(pair); rows = List.copyOf(rows); modifiers = List.copyOf(modifiers);
            if (rows.size() > 64 || modifiers.size() > 65536) throw new IllegalArgumentException("bounded matched rows required");
        }
    }
    public record Projection(long tokens, long rowsScanned, List<Finding> findings) {
        public Projection { findings = List.copyOf(findings); if (tokens < 1 || rowsScanned < 0 || findings.isEmpty() || findings.size() > 64) throw new IllegalArgumentException("complete opinion scan required"); }
    }
    public record Report(String schema, String machineId, String observedAtUtc, Request request, Projection projection,
                         SaveDecoder.ReadEvidence decoder, ProducerSources.Binding producerBefore, ProducerSources.Binding producerAfter,
                         Inspection.BusinessAssessment businessAssessment, boolean gameStarted) {
        public Report {
            if (!"ck3-save-opinions-v1".equals(schema) || request == null || projection == null || decoder == null
                    || !request.save().equals(decoder.save()) || !request.decoder().equals(decoder.decoder())
                    || !request.machineId().equals(machineId) || producerBefore == null || !producerBefore.equals(producerAfter)
                    || businessAssessment != Inspection.BusinessAssessment.NOT_ASSESSED || gameStarted)
                throw new IllegalArgumentException("complete offline opinion report required");
            Instant.parse(observedAtUtc);
            if (projection.tokens() > Long.parseLong(decoder.streamBytes())) throw new IllegalArgumentException("tokens exceed complete stream bytes");
            validate(request.selection(), projection);
        }
    }
    public static Report inspect(Request request) throws IOException { return inspect(request, SaveDecoder::launch); }
    /** External retained-save callers keep their existing OS-held custody/SDK/source checks around this API. */
    public static Report inspect(Request request, SaveDecoder.Launcher launcher) throws IOException {
        ProducerSources.Binding before = ProducerSources.verify(Path.of(request.repository()));
        SaveDecoder.StreamDecoded<Projection> decoded = SaveDecoder.decode(request.save(), request.decoder(), DecoderLimits.standard(), launcher,
                reader -> new OpinionStream(reader, request.selection()).read());
        ProducerSources.Binding after = ProducerSources.verify(Path.of(request.repository()));
        return InspectionFiles.bounded(new Report("ck3-save-opinions-v1", request.machineId(), Instant.now().toString(), request, decoded.value(), decoded.evidence(), before, after,
                Inspection.BusinessAssessment.NOT_ASSESSED, false));
    }
    static List<Modifier> modifiers(Selection selection, List<Row> rows) {
        java.util.ArrayList<Modifier> result = new java.util.ArrayList<>();
        for (Row row : rows) for (Clausewitz.Entry entry : row.completeAst().named("temporary_opinion")) {
            if (!entry.operator().equals("=") || !(entry.value() instanceof Clausewitz.Block block)) throw new IllegalArgumentException("temporary opinion block required");
            String source = atom(block, "modifier");
            if (source.equals(selection.modifier()) || source.equals('"' + selection.modifier() + '"'))
                result.add(new Modifier(atom(block, "value"), atom(block, "modify"), block));
        }
        return List.copyOf(result);
    }
    static void validate(Selection selection, Projection result) {
        if (result.findings().size() != selection.pairs().size()) throw new IllegalArgumentException("all requested directions required");
        HashSet<Long> ordinals = new HashSet<>(); int bytes = 0; int rows = 0;
        for (int i = 0; i < selection.pairs().size(); i++) {
            Pair pair = selection.pairs().get(i); Finding finding = result.findings().get(i);
            if (!finding.pair().equals(pair)) throw new IllegalArgumentException("direction/expectation mismatch");
            for (Row row : finding.rows()) {
                if (!row.owner().equals(pair.owner()) || !row.target().equals(pair.target()) || row.ordinal() > result.rowsScanned() || !ordinals.add(row.ordinal()))
                    throw new IllegalArgumentException("wrong or repeated directed row");
                int size = OpinionStream.tokenBytes(row.completeAst()); bytes = Math.addExact(bytes, size); rows++;
                if (size > selection.maxRecordBytes()) throw new IllegalArgumentException("row byte cap exceeded");
            }
            List<Modifier> modifiers = modifiers(selection, finding.rows());
            if (!modifiers.equals(finding.modifiers())) throw new IllegalArgumentException("modifier AST differs from directed row");
            if (pair.expectation() == Expectation.ABSENT ? !modifiers.isEmpty()
                    : modifiers.size() != 1 || !modifiers.getFirst().value().equals(selection.expectedValue()) || !modifiers.getFirst().modify().equals(selection.expectedModify()))
                throw new IllegalArgumentException("named modifier count/value mismatch");
        }
        if (rows > selection.maxMatchedRows() || bytes > selection.maxMatchedBytes()) throw new IllegalArgumentException("matched-only cap exceeded");
    }
    static NativeId id(Clausewitz.Block block, String name) { return new NativeId(atom(block, name)); }
    static String atom(Clausewitz.Block block, String name) {
        List<Clausewitz.Entry> found = block.named(name);
        if (found.size() != 1 || !found.getFirst().operator().equals("=") || !(found.getFirst().value() instanceof Clausewitz.Atom atom))
            throw new IllegalArgumentException("one assigned atom required: " + name);
        return atom.token();
    }
    private static boolean number(String value) { return value != null && value.length() <= 64 && value.matches("-?(0|[1-9][0-9]*)(\\.[0-9]+)?"); }
    public static int run(String[] args, SaveDecoder.Launcher launcher) { return InspectionFiles.run(args, Request.class, request -> inspect(request, launcher)); }
    public static Report readReport(byte[] bytes) throws IOException { return InspectionFiles.readReport(bytes, Report.class); }
}
