package org.xar.ck3.markets.saveaudit;

import java.math.BigInteger;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Objects;
import java.util.TreeMap;
import org.xar.ck3.save.SaveContracts;
import org.xar.ck3.save.SaveJson;
import org.xar.ck3.save.FilePins;

/** Standalone offline candidate entry point. No CK3 process, scripts, input mutation, or implicit output overwrite. */
public final class FinancialSaveAuditMain {
    private FinancialSaveAuditMain() { }
    public record PermanentIdentity(boolean present, String decimal) { }
    public record StoryEvidence(String type, String nativeId, PermanentIdentity permanentId,
                                Map<String, String> exactIntegers, Map<String, ScopeEvidence> scopeReferences) { }
    public record ScopeEvidence(String serializedType, String nativeId) { }
    public record SaveEvidence(SaveContracts.Pin requestedSave, SaveContracts.Pin save, FinancialSaveReader.Container container, String gameVersion,
                               String saveFormat, String gameDate, FinancialSaveReader.StreamingCoverage streamingCoverage,
                               FinancialAudit.Report audit, List<StoryEvidence> stories) { }
    public record Output(String schema, String machineId, String observedAtUtc, boolean financialCertified,
                         FinancialProjector.LayoutHypothesis layoutHypothesis, SaveEvidence first,
                         List<SaveEvidence> second, List<FinancialAudit.ColdComparison> coldComparison) { }
    public record RetiredObserverOutput(Output financial, List<FinancialSaveReader.RetiredObserverEvidence> firstUntypedRecords,
                                        List<List<FinancialSaveReader.RetiredObserverEvidence>> secondUntypedRecords) {
        public RetiredObserverOutput {
            Objects.requireNonNull(financial); firstUntypedRecords = List.copyOf(firstUntypedRecords);
            secondUntypedRecords = secondUntypedRecords.stream().map(List::copyOf).toList();
        }
    }
    /** Exact pins are supplied by the caller; decoder and cold save are explicit zero-or-one lists. */
    public record Inputs(String machineId, SaveContracts.Pin firstSave, List<SaveContracts.Pin> coldSave,
                         FinancialProjector.LayoutHypothesis layout, List<SaveContracts.Pin> decoder) {
        public Inputs {
            if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}")) throw new IllegalArgumentException("explicit machine identity required");
            Objects.requireNonNull(firstSave); Objects.requireNonNull(layout);
            coldSave = List.copyOf(coldSave); decoder = List.copyOf(decoder);
            if (coldSave.size() > 1 || decoder.size() > 1) throw new IllegalArgumentException("zero-or-one cold save/decoder required");
        }
    }

    public static void main(String[] args) throws Exception {
        // Fixed positional arguments avoid ambiguous defaults, particularly numeric scale/reference-type guesses.
        if (args.length != 9 && args.length != 10) throw new IllegalArgumentException(
                "candidate: <save> <unused-output.json> <machine-id> <exact-game-version> <save-format> <numeric-scale> <story-reference-type> <char-reference-type> --unqualified-candidate [same-state-cold-save]");
        if (!args[8].equals("--unqualified-candidate")) throw new IllegalArgumentException("explicit candidate-only flag required");
        Path output = Path.of(args[1]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("output must not exist");
        FinancialProjector.LayoutHypothesis layout = new FinancialProjector.LayoutHypothesis(args[3], args[4], new BigInteger(args[5]), args[6], args[7]);
        Inputs inputs = new Inputs(args[2], FilePins.pin(Path.of(args[0])), args.length == 10 ? List.of(FilePins.pin(Path.of(args[9]))) : List.of(), layout, List.of());
        Output report = inspect(inputs);
        Files.createDirectories(output.getParent());
        Files.write(output, SaveJson.write(report), StandardOpenOption.CREATE_NEW);
        System.out.println("UNQUALIFIED_CANDIDATE " + report.first().audit().assessment() + " " + output);
    }
    public static Output inspect(Inputs inputs) throws IOException {
        FinancialSaveReader.Readback firstRead = readPinned(inputs.firstSave(), inputs);
        FinancialProjector.LayoutHypothesis layout = inputs.layout();
        FinancialSnapshot first = FinancialProjector.project(firstRead, layout);
        Optional<SaveEvidence> second = Optional.empty(); Optional<FinancialAudit.ColdComparison> comparison = Optional.empty();
        if (!inputs.coldSave().isEmpty()) {
            FinancialSaveReader.Readback nextRead = readPinned(inputs.coldSave().getFirst(), inputs);
            FinancialSnapshot next = FinancialProjector.project(nextRead, layout);
            second = Optional.of(evidence(inputs.coldSave().getFirst(), nextRead, next)); comparison = Optional.of(FinancialAudit.compareCold(first, next));
        }
        return new Output("ck3-financial-save-audit-candidate-v3", inputs.machineId(), Instant.now().toString(), false,
                layout, evidence(inputs.firstSave(), firstRead, first), second.stream().toList(), comparison.stream().toList());
    }
    /** Separate explicit admission; the existing inspect() and strict CLI remain unchanged. */
    public static RetiredObserverOutput inspectRetiredXfma(Inputs inputs) throws IOException {
        FinancialSaveReader.RetiredObserverReadback firstRead = readPinnedRetiredXfma(inputs.firstSave(), inputs);
        FinancialSnapshot first = FinancialProjector.project(firstRead.financial(), inputs.layout());
        List<SaveEvidence> second = new java.util.ArrayList<>(); List<FinancialAudit.ColdComparison> comparisons = new java.util.ArrayList<>();
        List<List<FinancialSaveReader.RetiredObserverEvidence>> secondUntyped = new java.util.ArrayList<>();
        for (SaveContracts.Pin nextPin : inputs.coldSave()) {
            FinancialSaveReader.RetiredObserverReadback nextRead = readPinnedRetiredXfma(nextPin, inputs);
            FinancialSnapshot next = FinancialProjector.project(nextRead.financial(), inputs.layout());
            second.add(evidence(nextPin, nextRead.financial(), next)); comparisons.add(FinancialAudit.compareCold(first, next)); secondUntyped.add(nextRead.untypedRecords());
        }
        Output output = new Output("ck3-financial-save-audit-candidate-v3", inputs.machineId(), Instant.now().toString(), false,
                inputs.layout(), evidence(inputs.firstSave(), firstRead.financial(), first), second, comparisons);
        return new RetiredObserverOutput(output, firstRead.untypedRecords(), secondUntyped);
    }
    private static FinancialSaveReader.RetiredObserverReadback readPinnedRetiredXfma(SaveContracts.Pin expected, Inputs inputs) throws IOException {
        Path requested = Path.of(expected.path()), canonical = requested.toRealPath();
        if (!Files.isSameFile(requested, canonical)) throw new IOException("requested compatible save does not resolve to exact source");
        BasicFileAttributes before = Files.readAttributes(canonical, BasicFileAttributes.class);
        if (!before.isRegularFile()) throw new IOException("requested save is not regular");
        FilePins.verify(requested, expected);
        SaveContracts.Pin physical = new SaveContracts.Pin(canonical.toString(), expected.bytes(), expected.sha256()); FilePins.verify(canonical, physical);
        FinancialSaveReader.RetiredObserverReadback readback = inputs.decoder().isEmpty()
                ? FinancialSaveReader.readWithRetiredXfma(canonical, inputs.machineId(), inputs.layout())
                : FinancialSaveReader.readDecodedWithRetiredXfma(physical, inputs.decoder().getFirst(), inputs.machineId(), inputs.layout());
        BasicFileAttributes after = Files.readAttributes(canonical, BasicFileAttributes.class);
        if (!requested.toRealPath().equals(canonical) || !Files.isSameFile(requested, canonical)
                || before.size() != after.size() || !before.lastModifiedTime().equals(after.lastModifiedTime())
                || !before.creationTime().equals(after.creationTime()) || !Objects.equals(before.fileKey(), after.fileKey())
                || !readback.financial().save().equals(physical)) throw new IOException("compatible read changed physical SAVE identity/pin");
        FilePins.verify(requested, expected); FilePins.verify(canonical, physical); return readback;
    }
    private static FinancialSaveReader.Readback readPinned(SaveContracts.Pin expected, Inputs inputs) throws IOException {
        Path requested = Path.of(expected.path());
        Path canonical = requested.toRealPath();
        if (!Files.isSameFile(requested, canonical)) throw new IOException("requested save does not resolve to the pinned physical source");
        BasicFileAttributes before = Files.readAttributes(canonical, BasicFileAttributes.class);
        if (!before.isRegularFile()) throw new IOException("requested save is not a regular file");
        FilePins.verify(requested, expected);
        SaveContracts.Pin canonicalExpected = new SaveContracts.Pin(canonical.toString(), expected.bytes(), expected.sha256());
        FilePins.verify(canonical, canonicalExpected);
        FinancialSaveReader.Readback readback = inputs.decoder().isEmpty()
                ? FinancialSaveReader.read(canonical, inputs.machineId(), inputs.layout())
                : FinancialSaveReader.readDecoded(canonicalExpected, inputs.decoder().getFirst(), inputs.machineId(), inputs.layout());
        BasicFileAttributes after = Files.readAttributes(canonical, BasicFileAttributes.class);
        if (!requested.toRealPath().equals(canonical) || !Files.isSameFile(requested, canonical)
                || before.size() != after.size() || !before.lastModifiedTime().equals(after.lastModifiedTime())
                || !before.creationTime().equals(after.creationTime()) || !Objects.equals(before.fileKey(), after.fileKey()))
            throw new IOException("requested save physical identity or timestamps changed during readback");
        FilePins.verify(requested, expected);
        FilePins.verify(canonical, canonicalExpected);
        if (!readback.save().equals(canonicalExpected)) throw new IOException("readback differs from exact canonical physical pin");
        return readback;
    }
    private static SaveEvidence evidence(SaveContracts.Pin requested, FinancialSaveReader.Readback input, FinancialSnapshot snapshot) {
        List<StoryEvidence> stories = snapshot.stories().stream().map(story -> {
            Map<String, String> integers = new TreeMap<>();
            story.numbers().forEach((field, value) -> integers.put(field.wire(), value.toString()));
            Map<String, ScopeEvidence> references = new TreeMap<>();
            story.references().forEach((field, value) -> references.put(field.wire(), new ScopeEvidence(value.serializedType(), value.nativeId().value())));
            return new StoryEvidence(story.type().wire(), story.nativeId().value(), new PermanentIdentity(story.permanentId().isPresent(), story.permanentId().map(SaveContracts.NativeId::value).orElse("")), Map.copyOf(integers), Map.copyOf(references));
        }).toList();
        return new SaveEvidence(requested, input.save(), input.container(), snapshot.gameVersion(), snapshot.saveFormat(), snapshot.gameDate(), input.coverage(), FinancialAudit.audit(snapshot), stories);
    }
}
