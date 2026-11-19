package org.xar.ck3.markets.saveaudit;

import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.save.Clausewitz;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.zip.CRC32;
import java.util.zip.ZipEntry;
import java.util.zip.ZipException;
import java.util.zip.ZipFile;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Issue;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Story;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Type;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts;
import org.xar.ck3.save.SaveContracts.*;
import org.xar.ck3.save.SaveDecoder;
import org.xar.ck3.save.SaveStream;

/** Two complete shared-parser passes; only selected per-record ASTs exist transiently. */
public final class FinancialSaveReader {
    private static final long STREAM_LIMIT = 512L * 1024 * 1024;
    private static final String NUMBER_ENCODING_METADATA = "number_encoding_metadata";
    private FinancialSaveReader() { }
    public enum Container { PLAIN_TEXT, ZIP_GAMESTATE, SHARED_DECODER }
    public record Budgets(int maxTableRecords, int maxFinancialRecords, int maxRecordBytes,
                          long maxStreamedBytes, int maxProjectedFields) {
        public Budgets {
            if (maxTableRecords < 1 || maxTableRecords > 200000 || maxFinancialRecords < 1 || maxFinancialRecords > 65536
                    || maxFinancialRecords > maxTableRecords || maxRecordBytes < 11 || maxRecordBytes > 512 * 1024
                    || maxStreamedBytes < 11 || maxStreamedBytes > 64L * 1024 * 1024
                    || maxProjectedFields < 1 || maxProjectedFields > 1000000) throw new IllegalArgumentException("bounded financial streaming budgets required");
        }
        public static Budgets standard() { return new Budgets(200000, 65536, 512 * 1024, 64L * 1024 * 1024, 1000000); }
    }
    public record StreamingCoverage(int passes, String completeStreamSha256, String completeStreamBytes,
                                    int tableRecords, int selectedFinancialRecords, long streamedFinancialTokenBytes,
                                    int projectedFields, Budgets budgets, int tableSlots, List<NativeTombstone> tombstones) {
        public StreamingCoverage {
            tombstones = List.copyOf(tombstones);
            if (tableSlots != tableRecords + tombstones.size() || tableSlots > budgets.maxTableRecords())
                throw new IllegalArgumentException("complete live-record plus native-tombstone coverage required");
        }
    }
    public record Readback(String machineId, String observedAtUtc, Pin save, Container container,
                           Projection projection, List<Story> financialStories, List<Issue> financialIssues,
                           StreamingCoverage coverage, boolean inputUnchanged, boolean sourceLayoutQualified) {
        public Readback {
            if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}")) throw new IllegalArgumentException("explicit machine identity required");
            Instant.parse(observedAtUtc); Objects.requireNonNull(save); Objects.requireNonNull(container);
            Objects.requireNonNull(projection); Objects.requireNonNull(coverage);
            financialStories = List.copyOf(financialStories); financialIssues = List.copyOf(financialIssues);
            if (!inputUnchanged || sourceLayoutQualified) throw new IllegalArgumentException("candidate is unchanged-input readback, never layout qualification");
        }
    }
    public record ObserverVariableEvidence(String flag, String serializedType, boolean identityPresent, String rawIdentity) {
        public ObserverVariableEvidence {
            if (flag == null || !flag.matches("xfma_[a-z0-9_]{1,122}") || !"value".equals(serializedType) || rawIdentity == null)
                throw new IllegalArgumentException("typed canonical observer value evidence required");
            if (identityPresent) new NativeId(rawIdentity);
            else if (!rawIdentity.isEmpty()) throw new IllegalArgumentException("absent identity must retain explicit empty lexical value");
        }
    }
    public record RetiredObserverEvidence(String nativeId, String canonicalTokenSha256, int canonicalTokenBytes,
                                          String classification, String owner, String seed, List<ObserverVariableEvidence> variables) {
        public RetiredObserverEvidence {
            new NativeId(nativeId); SaveContracts.digest(canonicalTokenSha256); new NativeId(owner); new NativeId(seed);
            variables = List.copyOf(variables);
            if (canonicalTokenBytes < 11 || canonicalTokenBytes > 512 * 1024 || !"RETIRED_XFMA_VALUE_ONLY_V1".equals(classification)
                    || variables.isEmpty() || variables.size() > 4096 || variables.stream().map(ObserverVariableEvidence::flag).distinct().count() != variables.size())
                throw new IllegalArgumentException("bounded classified nonempty unique observer evidence required");
        }
    }
    private record RetiredObserverIdentity(String nativeId, String canonicalTokenSha256, int canonicalTokenBytes, String classification) { }
    private static RetiredObserverIdentity identity(RetiredObserverEvidence evidence) {
        return new RetiredObserverIdentity(evidence.nativeId(), evidence.canonicalTokenSha256(), evidence.canonicalTokenBytes(), evidence.classification());
    }
    public record RetiredObserverReadback(Readback financial, List<RetiredObserverEvidence> untypedRecords) {
        public RetiredObserverReadback { Objects.requireNonNull(financial); untypedRecords = List.copyOf(untypedRecords); }
    }
    private record Pass(Projection projection, StreamingObservation observation, String sha256, long bytes, Container container) { }

    /** Retained metadata/globals keep original shared limits; stories are not a whole-block projection. */
    public static Selection selection() {
        return new Selection(List.of(), List.of(new ProjectionSelection("globals", ProjectionKind.GLOBAL_VARIABLES,
                List.of("variables"), 1, 512 * 1024, true)), true, false, List.of());
    }
    /** Opt-in header admission needs the full AST, including same-name block entries.
     * The standard metadata scope exposes direct scalars only. Shared limits stay unchanged.
     */
    private static Selection selection(FinancialProjector.LayoutHypothesis layout) {
        Selection strict = selection();
        if (!layout.numberIdentityEncoding().requiresObserved121Metadata()) return strict;
        List<ProjectionSelection> projections = new ArrayList<>(strict.projections());
        projections.add(new ProjectionSelection(NUMBER_ENCODING_METADATA, ProjectionKind.OTHER,
                List.of("meta_data"), 1, 512 * 1024, true));
        return new Selection(strict.tables(), projections, strict.metadataRequired(), strict.structureCensus(), strict.structureRoots());
    }
    public static Readback read(Path input, String machineId, FinancialProjector.LayoutHypothesis layout) throws IOException {
        return read(input, machineId, layout, Budgets.standard());
    }
    public static Readback read(Path input, String machineId, FinancialProjector.LayoutHypothesis layout, Budgets budgets) throws IOException {
        Pin pin = FilePins.pin(input);
        return readTwoPasses(pin, machineId, layout, budgets, (table, sink) -> pass(pin, table, sink, layout));
    }
    public static Readback readDecoded(Pin input, Pin decoder, String machineId, FinancialProjector.LayoutHypothesis layout) throws IOException {
        return readTwoPasses(input, machineId, layout, Budgets.standard(), (table, sink) -> {
            TrackingSink tracking = new TrackingSink(sink);
            Decoded decoded = SaveDecoder.inspect(input, decoder, selection(layout), DecoderLimits.standard(), SaveDecoder::launch, table, tracking);
            return new Pass(decoded.projection(), tracking.observation(), decoded.streamSha256(), Long.parseLong(decoded.streamBytes()), Container.SHARED_DECODER);
        });
    }
    /** Opt-in is deliberately separate from the existing strict read/readDecoded entry points. */
    public static RetiredObserverReadback readWithRetiredXfma(Path input, String machineId, FinancialProjector.LayoutHypothesis layout) throws IOException {
        Pin pin = FilePins.pin(input);
        return readTwoPassesWithEvidence(pin, machineId, layout, Budgets.standard(), (table, sink) -> pass(pin, table, sink, layout), true);
    }
    public static RetiredObserverReadback readDecodedWithRetiredXfma(Pin input, Pin decoder, String machineId, FinancialProjector.LayoutHypothesis layout) throws IOException {
        return readTwoPassesWithEvidence(input, machineId, layout, Budgets.standard(), (table, sink) -> {
            TrackingSink tracking = new TrackingSink(sink);
            Decoded decoded = SaveDecoder.inspect(input, decoder, selection(layout), DecoderLimits.standard(), SaveDecoder::launch, table, tracking);
            return new Pass(decoded.projection(), tracking.observation(), decoded.streamSha256(), Long.parseLong(decoded.streamBytes()), Container.SHARED_DECODER);
        }, true);
    }
    private static Clausewitz.Block onlyBlock(Clausewitz.Block parent, String key) throws IOException {
        var entries = parent.named(key);
        if (entries.size() != 1 || !entries.getFirst().operator().equals("=") || !(entries.getFirst().value() instanceof Clausewitz.Block block))
            throw new IOException("retired observer requires one assigned block: " + key);
        return block;
    }
    private static String unsignedIdentity(String value) throws IOException {
        if (!value.matches("0|[1-9][0-9]{0,19}") || new BigInteger(value).bitLength() > 64)
            throw new IOException("retired observer requires canonical unsigned64 lexical identity");
        return value;
    }
    private static RetiredObserverEvidence classifyRetired(UntypedRecord record, FinancialProjector.LayoutHypothesis layout) throws IOException {
        Clausewitz.Block body = record.ast();
        try {
            if (body.entries().size() != 3 || !body.entries().stream().map(Clausewitz.Entry::key).collect(java.util.stream.Collectors.toSet()).equals(Set.of("owner", "seed", "variables")))
                throw new IOException("untyped record is not the bounded owner/seed/observer-variables envelope: " + record.id().value());
            String owner = unsignedIdentity(FinancialProjector.atom(body, "owner").orElseThrow());
            String seed = unsignedIdentity(FinancialProjector.atom(body, "seed").orElseThrow());
            Clausewitz.Block variables = onlyBlock(body, "variables");
            if (variables.entries().size() != 1) throw new IOException("retired observer variables must contain only data");
            Clausewitz.Block list = onlyBlock(variables, "data");
            if (list.entries().isEmpty() || list.entries().size() > 4096) throw new IOException("nonempty bounded retired observer variables required");
            List<ObserverVariableEvidence> evidence = new ArrayList<>(); Set<String> names = new HashSet<>();
            for (Clausewitz.Entry item : list.entries()) {
                if (!item.key().isEmpty() || !(item.value() instanceof Clausewitz.Block variable) || variable.entries().size() != 2)
                    throw new IOException("retired observer variable envelope is malformed");
                String flag = FinancialProjector.atom(variable, "flag").map(FinancialProjector::unquote).orElseThrow();
                if (!flag.matches("xfma_[a-z0-9_]{1,122}") || !names.add(flag)) throw new IOException("untyped non-observer/duplicate variable: " + flag);
                Clausewitz.Block data = onlyBlock(variable, "data");
                if (!FinancialProjector.atom(data, "type").orElse("").equals("value")) throw new IOException("retired observer only admits numeric observation values");
                var identity = FinancialProjector.atom(data, "identity");
                if (identity.isPresent()) {
                    if (data.entries().size() != 2) throw new IOException("retired observer value has unknown fields");
                    unsignedIdentity(identity.get());
                } else if (!layout.numberIdentityEncoding().requiresObserved121Metadata() || data.entries().size() != 1)
                    throw new IOException("retired observer value missing identity outside explicit observed121 omitted-zero encoding");
                evidence.add(new ObserverVariableEvidence(flag, "value", identity.isPresent(), identity.orElse("")));
            }
            return new RetiredObserverEvidence(record.id().value(), record.canonicalTokenSha256(), record.canonicalTokenBytes(), "RETIRED_XFMA_VALUE_ONLY_V1", owner, seed, evidence);
        } catch (IllegalArgumentException | java.util.NoSuchElementException malformed) {
            throw new IOException("untyped record is not a structurally exact retired xfma observer: " + record.id().value(), malformed);
        }
    }
    @FunctionalInterface private interface PassReader { Pass read(StreamingTable table, StreamingTableSink sink) throws IOException; }
    private static Readback readTwoPasses(Pin pin, String machineId, FinancialProjector.LayoutHypothesis layout,
                                          Budgets budgets, PassReader reader) throws IOException {
        return readTwoPassesWithEvidence(pin, machineId, layout, budgets, reader, false).financial();
    }
    private static RetiredObserverReadback readTwoPassesWithEvidence(Pin pin, String machineId, FinancialProjector.LayoutHypothesis layout,
                                          Budgets budgets, PassReader reader, boolean allowRetired) throws IOException {
        Map<NativeId, String> selected = new LinkedHashMap<>();
        List<RetiredObserverIdentity> firstUntyped = new ArrayList<>();
        StreamingTableSink census = new StreamingTableSink() {
            private int retiredFields;
            @Override public void missingDiscriminator(UntypedRecord record) throws IOException {
                if (!allowRetired) throw new IOException("retired observer admission is not enabled");
                RetiredObserverEvidence evidence = classifyRetired(record, layout);
                retiredFields = Math.addExact(retiredFields, evidence.variables().size() + 3);
                if (firstUntyped.size() >= budgets.maxFinancialRecords() || retiredFields > budgets.maxProjectedFields()) throw new IOException("retired observer evidence budget exceeded");
                firstUntyped.add(identity(evidence));
            }
            @Override public void discriminator(NativeId id, String rawType) throws IOException {
                String type = normalizedType(rawType);
                if (isFinancial(type)) {
                    if (selected.size() >= budgets.maxFinancialRecords()) throw new IOException("financial record count budget exceeded");
                    selected.put(id, type);
                }
            }
            @Override public void record(StreamedRecord ignored) throws IOException { throw new IOException("census pass must not retain records"); }
        };
        Pass first = reader.read(table(List.of(), budgets, allowRetired), census);
        FilePins.verify(Path.of(pin.path()), pin);
        requireObservedNumberEncoding(first.projection(), layout);
        ProjectionSink projected = new ProjectionSink(selected, layout, budgets, allowRetired);
        Pass second = reader.read(table(List.copyOf(selected.keySet()), budgets, allowRetired), projected);
        if (first.container() != second.container() || first.bytes() != second.bytes() || !first.sha256().equals(second.sha256())
                || first.observation().records() != second.observation().records()
                || !first.observation().tombstones().equals(second.observation().tombstones())
                || second.observation().selectedRecords() != selected.size() || !firstUntyped.equals(projected.untyped.stream().map(FinancialSaveReader::identity).toList())) throw new IOException("save stream/selection changed between complete passes");
        FilePins.verify(Path.of(pin.path()), pin);
        StreamingCoverage coverage = new StreamingCoverage(2, second.sha256(), Long.toString(second.bytes()), second.observation().records(),
                second.observation().selectedRecords(), second.observation().streamedTokenBytes()
                - projected.untyped.stream().mapToLong(RetiredObserverEvidence::canonicalTokenBytes).sum()
                - second.observation().tombstones().stream().mapToLong(NativeTombstone::canonicalTokenBytes).sum(),
                projected.fields, budgets, second.observation().observedSlots(), second.observation().tombstones());
        return new RetiredObserverReadback(new Readback(machineId, Instant.now().toString(), pin, second.container(), second.projection(), projected.stories,
                projected.issues, coverage, true, false), projected.untyped);
    }
    private static void requireObservedNumberEncoding(Projection projection, FinancialProjector.LayoutHypothesis layout) throws IOException {
        if (!layout.numberIdentityEncoding().requiresObserved121Metadata()) return;
        List<ProjectionScope> metadata = projection.projections().stream()
                .filter(scope -> scope.name().equals(NUMBER_ENCODING_METADATA)).toList();
        try {
            if (metadata.size() != 1
                    || !FinancialProjector.atom(metadata.getFirst().ast(), "version").map(FinancialProjector::unquote).orElse("").equals("1.21.0")
                    || !FinancialProjector.atom(metadata.getFirst().ast(), "save_game_version").orElse("").equals("19"))
                throw new IllegalArgumentException(layout.numberIdentityEncoding() + " requires observed 1.21.0 / format 19 metadata");
        } catch (IllegalArgumentException malformed) {
            throw new IOException("actual SAVE metadata does not admit omittedZero", malformed);
        }
    }
    private static StreamingTable table(List<NativeId> selected, Budgets budgets, boolean allowRetired) {
        return new StreamingTable(List.of("stories", "active"), "story_cycle", selected, budgets.maxTableRecords(),
                budgets.maxRecordBytes(), budgets.maxStreamedBytes(), true,
                allowRetired ? MissingDiscriminatorPolicy.CAPTURE_MISSING_BOUNDED : MissingDiscriminatorPolicy.REJECT);
    }
    private static final class ProjectionSink implements StreamingTableSink {
        private final Map<NativeId, String> selected;
        private final FinancialProjector.LayoutHypothesis layout;
        private final Budgets budgets;
        private final List<Story> stories = new ArrayList<>();
        private final List<Issue> issues = new ArrayList<>();
        private int fields;
        private final boolean allowRetired;
        private final List<RetiredObserverEvidence> untyped = new ArrayList<>();
        ProjectionSink(Map<NativeId, String> selected, FinancialProjector.LayoutHypothesis layout, Budgets budgets, boolean allowRetired) {
            this.selected = Map.copyOf(selected); this.layout = layout; this.budgets = budgets; this.allowRetired = allowRetired;
        }
        @Override public void missingDiscriminator(UntypedRecord record) throws IOException {
            if (!allowRetired) throw new IOException("retired observer admission is not enabled");
            RetiredObserverEvidence evidence = classifyRetired(record, layout);
            fields = Math.addExact(fields, evidence.variables().size() + 3);
            if (untyped.size() >= budgets.maxFinancialRecords() || fields > budgets.maxProjectedFields()) throw new IOException("retired observer evidence budget exceeded");
            untyped.add(evidence);
        }
        @Override public void discriminator(NativeId id, String rawType) throws IOException {
            String actual = normalizedType(rawType), expected = selected.get(id);
            if (expected != null ? !expected.equals(actual) : isFinancial(actual)) throw new IOException("financial discriminator changed between passes");
        }
        @Override public void record(StreamedRecord record) throws IOException {
            if (!Objects.equals(selected.get(record.id()), normalizedType(record.discriminator()))) throw new IOException("unexpected selected financial record");
            FinancialProjector.RecordProjection projected;
            try { projected = FinancialProjector.projectRecord(record.id(), record.ast(), layout); }
            catch (IllegalArgumentException malformed) { throw new IOException("unrecognized financial record " + record.id().value(), malformed); }
            fields = Math.addExact(fields, projected.issues().size() + projected.story().map(s -> s.numbers().size() + s.references().size() + 3).orElse(0));
            if (fields > budgets.maxProjectedFields()) throw new IOException("projected financial field/issue budget exceeded");
            projected.story().ifPresent(stories::add); issues.addAll(projected.issues());
        }
    }
    private static boolean isFinancial(String type) {
        return Type.fromWire(type).isPresent() || type.startsWith("xfm_finance_") || type.startsWith("xfm_futures_") || type.startsWith("xfm_debt_claim");
    }
    private static String normalizedType(String raw) throws IOException {
        try { return FinancialProjector.unquote(raw); }
        catch (IllegalArgumentException malformed) { throw new IOException("unrecognized story discriminator", malformed); }
    }
    private static Pass pass(Pin pin, StreamingTable table, StreamingTableSink sink, FinancialProjector.LayoutHypothesis layout) throws IOException {
        Path path = Path.of(pin.path());
        byte[] signature;
        try (InputStream input = Files.newInputStream(path)) { signature = input.readNBytes(4); }
        boolean zipSignature = signature.length == 4 && signature[0] == 'P' && signature[1] == 'K';
        ZipFile opened = null;
        try { opened = new ZipFile(path.toFile(), StandardCharsets.UTF_8); }
        catch (ZipException notZip) { if (zipSignature) throw new IOException("malformed ZIP container", notZip); }
        if (opened != null) {
            try (ZipFile archive = opened) {
                List<? extends ZipEntry> entries = archive.stream().filter(e -> e.getName().equals("gamestate")).toList();
                if (entries.size() != 1 || entries.getFirst().isDirectory()) throw new IOException("exactly one gamestate entry required");
                ZipEntry state = entries.getFirst();
                if (state.getSize() < 0 || state.getSize() > STREAM_LIMIT || state.getCrc() < 0) throw new IOException("unknown or oversized gamestate entry");
                try (BoundedStream stream = new BoundedStream(archive.getInputStream(state)); Reader reader = utf8(stream)) {
                    SaveStream selector = new SaveStream(reader, selection(layout), table, sink);
                    Projection projection = selector.read();
                    if (stream.count != state.getSize() || stream.crc.getValue() != state.getCrc()) throw new IOException("gamestate size/CRC mismatch");
                    return new Pass(projection, selector.streamingObservation(), stream.sha256(), stream.count, Container.ZIP_GAMESTATE);
                }
            }
        }
        try (BoundedStream stream = new BoundedStream(Files.newInputStream(path)); Reader reader = utf8(stream)) {
            SaveStream selector = new SaveStream(reader, selection(layout), table, sink);
            Projection projection = selector.read();
            return new Pass(projection, selector.streamingObservation(), stream.sha256(), stream.count, Container.PLAIN_TEXT);
        }
    }
    private static Reader utf8(InputStream stream) {
        return new InputStreamReader(stream, StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT));
    }
    private static final class TrackingSink implements StreamingTableSink {
        private final StreamingTableSink delegate; private int records; private int selected; private long bytes;
        private final List<NativeTombstone> tombstones = new ArrayList<>();
        TrackingSink(StreamingTableSink delegate) { this.delegate = delegate; }
        @Override public void discriminator(NativeId id, String value) throws IOException { records++; delegate.discriminator(id, value); }
        @Override public void record(StreamedRecord record) throws IOException { selected++; bytes += record.canonicalTokenBytes(); delegate.record(record); }
        @Override public void missingDiscriminator(UntypedRecord record) throws IOException { records++; bytes += record.canonicalTokenBytes(); delegate.missingDiscriminator(record); }
        @Override public void tombstone(NativeTombstone slot) throws IOException { tombstones.add(slot); bytes += slot.canonicalTokenBytes(); delegate.tombstone(slot); }
        StreamingObservation observation() { return new StreamingObservation(true, records, selected, bytes, tombstones); }
    }
    private static final class BoundedStream extends FilterInputStream {
        private long count; private final CRC32 crc = new CRC32(); private final MessageDigest digest = FilePins.digest();
        BoundedStream(InputStream stream) { super(stream); }
        @Override public int read() throws IOException { int value = in.read(); if (value >= 0) { add(1); crc.update(value); digest.update((byte) value); } return value; }
        @Override public int read(byte[] bytes, int offset, int length) throws IOException { int read = in.read(bytes, offset, length); if (read > 0) { add(read); crc.update(bytes, offset, read); digest.update(bytes, offset, read); } return read; }
        private void add(int length) throws IOException { count = Math.addExact(count, length); if (count > STREAM_LIMIT) throw new IOException("gamestate decompression/output limit exceeded"); }
        String sha256() { return HexFormat.of().formatHex(digest.digest()); }
    }
}
