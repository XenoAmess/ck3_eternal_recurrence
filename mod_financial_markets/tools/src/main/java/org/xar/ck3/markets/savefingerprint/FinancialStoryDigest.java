package org.xar.ck3.markets.savefingerprint;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PushbackInputStream;
import java.math.BigInteger;
import java.nio.channels.Channels;
import java.nio.channels.FileChannel;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Type;
import org.xar.ck3.markets.saveaudit.SaveAuditSources;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts.*;
import org.xar.ck3.save.SaveJson;
import org.xar.ck3.save.SaveStream;

/** Independent whole-record evidence; does not expand app09's projection or certify financial semantics. */
public final class FinancialStoryDigest {
    private static final long MAX_SAVE_BYTES = 512L * 1024 * 1024;
    private static final int MAX_REPORT_BYTES = 16 * 1024 * 1024;
    private static final BigInteger SCALE = BigInteger.valueOf(100000);
    private FinancialStoryDigest() { }

    public record Limits(int maxTableRecords, int maxFinancialRecords, int maxRecordBytes, long maxStreamedBytes) {
        public Limits {
            if (maxTableRecords < 1 || maxTableRecords > 200000 || maxFinancialRecords < 1
                    || maxFinancialRecords > 65536 || maxFinancialRecords > maxTableRecords
                    || maxRecordBytes < 11 || maxRecordBytes > 512 * 1024
                    || maxStreamedBytes < 11 || maxStreamedBytes > 64L * 1024 * 1024)
                throw new IllegalArgumentException("finite table/record/work limits required");
        }
        public static Limits standard() { return new Limits(200000, 65536, 512 * 1024, 64L * 1024 * 1024); }
    }
    public record Request(int schemaVersion, String machineId, String repository, Pin save, Pin archiveReceipt,
                          Pin readerSource, List<Pin> runtimeJars, Pin classifiedAuditReport,
                          String expectedDate, long expectedDateRaw, Limits limits) {
        public Request {
            if (schemaVersion != 1 || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}")
                    || repository == null || !Path.of(repository).isAbsolute()
                    || expectedDate == null || !expectedDate.matches("[0-9]{1,5}\\.[0-9]{1,2}\\.[0-9]{1,2}") || expectedDateRaw < 1)
                throw new IllegalArgumentException("explicit schema/machine/repository/date required");
            Objects.requireNonNull(save); Objects.requireNonNull(archiveReceipt); Objects.requireNonNull(readerSource);
            Objects.requireNonNull(classifiedAuditReport); Objects.requireNonNull(limits);
            runtimeJars = List.copyOf(runtimeJars);
            if (save.bytes() < 4 || save.bytes() > MAX_SAVE_BYTES || archiveReceipt.bytes() < 1 || archiveReceipt.bytes() > 65536
                    || readerSource.bytes() < 1 || readerSource.bytes() > 512 * 1024
                    || classifiedAuditReport.bytes() < 1 || classifiedAuditReport.bytes() > 16 * 1024 * 1024
                    || runtimeJars.size() != 5 || runtimeJars.stream().map(Pin::path).distinct().count() != 5
                    || runtimeJars.stream().anyMatch(p -> p.bytes() < 1 || p.bytes() > 4 * 1024 * 1024))
                throw new IllegalArgumentException("bounded pinned inputs and five actual runtime JARs required");
        }
    }
    public record RetiredIdentity(String nativeId, String canonicalTokenSha256, int canonicalTokenBytes) {
        public RetiredIdentity { new NativeId(nativeId); org.xar.ck3.save.SaveContracts.digest(canonicalTokenSha256);
            if (canonicalTokenBytes < 11 || canonicalTokenBytes > 512 * 1024) throw new IllegalArgumentException("bounded retired identity required"); }
    }
    public record RecordDigest(String nativeId, String type, boolean permanentIdPresent, String permanentId,
                               String canonicalTokenSha256, int canonicalTokenBytes) { }
    public record FileFacts(String realPath, String providerFileKey, long bytes, String creationTime, String modifiedTime) { }
    public record Result(String schema, String machineId, Pin save, String gameDate, int completePasses,
                         String completeStreamSha256, String completeStreamBytes, int tableRecords, int tableSlots,
                         Map<String, Integer> typeCensus, List<RecordDigest> records, List<NativeTombstone> tombstones,
                         List<RetiredIdentity> admittedRetiredRecords, FileFacts before, FileFacts after,
                         Limits limits, boolean inputUnchanged, boolean financialCertified) {
        public Result { typeCensus = Map.copyOf(typeCensus); records = List.copyOf(records);
            tombstones = List.copyOf(tombstones); admittedRetiredRecords = List.copyOf(admittedRetiredRecords); }
    }
    public record Output(Request request, SaveAuditSources.Binding existingAuditAndParserBinding, Result digest,
                         String status, boolean financialCertified) { }
    private record Pass(String sha256, long bytes, String date, StreamingObservation observation) { }
    private record Descriptor(String wire, String permanentFlag) { }
    private static Descriptor descriptor(String wire) {
        if (wire.equals("xfm_news_entry")) return new Descriptor(wire, "xfm_news_id");
        return Type.fromWire(wire).map(t -> new Descriptor(t.wire(), t.permanentField().map(f -> f.wire()).orElse(""))).orElse(null);
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 4 || !args[0].equals("--inputs") || !args[2].equals("--output"))
            throw new IllegalArgumentException("--inputs ABSOLUTE_REQUEST --output NEW_EXTERNAL_REPORT");
        Path inputs = Path.of(args[1]), output = Path.of(args[3]);
        if (!inputs.isAbsolute() || !output.isAbsolute() || Files.size(inputs) > 65536
                || Files.exists(output, LinkOption.NOFOLLOW_LINKS) || !Files.isDirectory(output.getParent()))
            throw new IOException("bounded request and create-only report with existing parent required");
        Request request = SaveJson.read(Files.readAllBytes(inputs), Request.class);
        Path repository = Path.of(request.repository()).toRealPath();
        if (output.getParent().toRealPath().startsWith(repository)
                || output.getParent().toRealPath().equals(Path.of(request.save().path()).toRealPath().getParent()))
            throw new IOException("report must be external to repository/source archive");
        verifySmallInputs(request); verifyArchive(request); verifyRuntime(request.runtimeJars());
        SaveAuditSources.Binding binding = SaveAuditSources.verify(repository);
        List<RetiredIdentity> retired = classifiedRetired(request);
        Result result = read(Path.of(request.save().path()), request.save(), request.machineId(), request.expectedDate(), request.limits(), retired);
        verifySmallInputs(request); verifyArchive(request); verifyRuntime(request.runtimeJars());
        if (!binding.equals(SaveAuditSources.verify(repository))) throw new IOException("loaded parser/audit source binding changed");
        byte[] encoded = SaveJson.write(new Output(request, binding, result, "UNQUALIFIED_FINANCIAL_AND_NEWS_WHOLE_RECORD_DIGEST", false));
        if (encoded.length > MAX_REPORT_BYTES) throw new IOException("whole-record digest report exceeds finite 16 MiB limit");
        Files.write(output, encoded, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        System.out.println(new String(SaveJson.write(FilePins.pin(output)), StandardCharsets.UTF_8));
    }
    private static void verifySmallInputs(Request request) throws IOException {
        for (Pin pin : concat(request)) {
            Path path = Path.of(pin.path());
            if (Files.size(path) != pin.bytes()) throw new IOException("input size differs: " + path);
            FilePins.verify(path, pin);
        }
    }
    private static List<Pin> concat(Request request) {
        List<Pin> pins = new ArrayList<>(request.runtimeJars());
        pins.add(request.readerSource()); pins.add(request.classifiedAuditReport()); pins.add(request.archiveReceipt()); return pins;
    }
    private static void verifyArchive(Request request) throws IOException {
        JsonNode root = json(request.archiveReceipt(), 65536);
        JsonNode archive = root.path("archive");
        if (!root.path("schema").asText().equals("ck3-financial-checkpoint-archive-v1")
                || !root.path("machine_id").asText().equals(request.machineId())
                || !root.path("date_raw").isIntegralNumber() || !root.path("date_raw").canConvertToLong() || root.path("date_raw").longValue() != request.expectedDateRaw()
                || !archive.isObject() || !archive.path("path").asText().equals(request.save().path())
                || !archive.path("bytes").isIntegralNumber() || !archive.path("bytes").canConvertToLong() || archive.path("bytes").longValue() != request.save().bytes()
                || !archive.path("sha256").asText().equals(request.save().sha256()))
            throw new IOException("actual archive receipt does not bind requested original SAVE");
    }
    private static JsonNode json(Pin pin, int cap) throws IOException {
        Path path = Path.of(pin.path());
        if (pin.bytes() < 1 || pin.bytes() > cap || Files.size(path) != pin.bytes()) throw new IOException("bounded exact JSON input required");
        FilePins.verify(path, pin); return SaveJson.read(Files.readAllBytes(path), JsonNode.class);
    }
    /** The existing audit's explicit strict classification is evidence, never a new permissive missing-type policy. */
    static List<RetiredIdentity> classifiedRetired(Request request) throws IOException {
        JsonNode report = json(request.classifiedAuditReport(), 16 * 1024 * 1024);
        JsonNode financial = report.path("audit").path("financial").path("first");
        if (!report.path("schema").asText().equals("ck3-financial-save-audit-retired-xfma-source-bound-candidate-v1")
                || !report.path("machineId").asText().equals(request.machineId())
                || !financial.path("gameVersion").asText().equals("1.21.0") || !financial.path("saveFormat").asText().equals("19")
                || !financial.path("save").path("sha256").asText().equals(request.save().sha256())
                || !financial.path("save").path("bytes").isIntegralNumber() || !financial.path("save").path("bytes").canConvertToLong()
                || financial.path("save").path("bytes").longValue() != request.save().bytes()
                || !financial.path("gameDate").asText().equals(request.expectedDate())
                || !financial.path("streamingCoverage").path("completeStreamSha256").asText().equals(request.save().sha256())
                || financial.path("streamingCoverage").path("passes").intValue() != 2)
            throw new IOException("classified audit must be actual same-SAVE/date/machine two-pass evidence");
        JsonNode entries = report.path("audit").path("firstUntypedRecords");
        if (!entries.isArray() || entries.size() > request.limits().maxFinancialRecords()) throw new IOException("bounded explicit prior untyped evidence required");
        List<RetiredIdentity> result = new ArrayList<>();
        for (JsonNode entry : entries) {
            if (!entry.path("classification").asText().equals("RETIRED_XFMA_VALUE_ONLY_V1")
                    || !entry.path("canonicalTokenBytes").isIntegralNumber() || !entry.path("canonicalTokenBytes").canConvertToInt()) throw new IOException("only existing strictly classified retired observer admitted");
            result.add(new RetiredIdentity(entry.path("nativeId").asText(), entry.path("canonicalTokenSha256").asText(), entry.path("canonicalTokenBytes").intValue()));
        }
        if (result.stream().map(RetiredIdentity::nativeId).distinct().count() != result.size()) throw new IOException("duplicate retired evidence ID");
        return List.copyOf(result);
    }

    public static Result read(Path path, Pin expected, String machineId, String date, Limits limits,
                              List<RetiredIdentity> retired) throws IOException {
        if (expected.bytes() < 4 || expected.bytes() > MAX_SAVE_BYTES || !Files.isSameFile(path, Path.of(expected.path())))
            throw new IOException("finite same physical input required");
        FileFacts before = facts(path);
        Map<NativeId, Descriptor> selected = new LinkedHashMap<>(); Map<String, Integer> census = new TreeMap<>();
        Map<String, RetiredIdentity> permitted = new LinkedHashMap<>();
        for (RetiredIdentity item : retired) if (permitted.put(item.nativeId(), item) != null) throw new IOException("duplicate retired evidence");
        List<RetiredIdentity> firstUntyped = new ArrayList<>(), secondUntyped = new ArrayList<>();
        StreamingTableSink firstSink = new StreamingTableSink() {
            public void discriminator(NativeId id, String raw) throws IOException {
                String type = unquote(raw); census.merge(type, 1, Math::addExact);
                if (census.size() > 4096) throw new IOException("type census budget exceeded");
                Descriptor known = descriptor(type);
                if (known != null) {
                    if (selected.size() >= limits.maxFinancialRecords()) throw new IOException("selected financial count budget exceeded");
                    selected.put(id, known);
                } else if (type.startsWith("xfm_"))
                    throw new IOException("uncovered monetary/legacy xfm story type: " + type + ":" + id.value());
            }
            public void record(StreamedRecord ignored) throws IOException { throw new IOException("census must not retain typed ASTs"); }
            public void missingDiscriminator(UntypedRecord record) throws IOException { firstUntyped.add(retired(record, permitted)); }
        };
        Pass first = pass(path, expected, limits, List.of(), firstSink, before);
        List<RecordDigest> records = new ArrayList<>(); Map<String, Integer> repeatedCensus = new TreeMap<>();
        StreamingTableSink secondSink = new StreamingTableSink() {
            public void discriminator(NativeId id, String raw) throws IOException {
                String type = unquote(raw); repeatedCensus.merge(type, 1, Math::addExact);
                Descriptor known = selected.get(id);
                if (known != null ? !known.wire().equals(type) : descriptor(type) != null) throw new IOException("financial selection changed");
            }
            public void record(StreamedRecord record) throws IOException {
                Descriptor type = selected.get(record.id());
                if (type == null || !type.wire().equals(unquote(record.discriminator()))) throw new IOException("unexpected selected record");
                String permanent = permanent(record.ast(), type);
                records.add(new RecordDigest(record.id().value(), type.wire(), !permanent.isEmpty(), permanent, record.canonicalTokenSha256(), record.canonicalTokenBytes()));
            }
            public void missingDiscriminator(UntypedRecord record) throws IOException { secondUntyped.add(retired(record, permitted)); }
        };
        Pass second = pass(path, expected, limits, List.copyOf(selected.keySet()), secondSink, before);
        FileFacts after = facts(path);
        if (!before.equals(after) || !first.sha256().equals(second.sha256()) || first.bytes() != second.bytes()
                || !first.date().equals(date) || !second.date().equals(date) || !census.equals(repeatedCensus)
                || !firstUntyped.equals(secondUntyped) || first.observation().records() != second.observation().records()
                || !first.observation().tombstones().equals(second.observation().tombstones())
                || records.size() != selected.size() || second.observation().selectedRecords() != selected.size())
            throw new IOException("complete input/date/census/selection differs between passes");
        return new Result("ck3-financial-and-news-whole-record-digest-v1", machineId, expected, date, 2, second.sha256(),
                Long.toString(second.bytes()), second.observation().records(), second.observation().observedSlots(), census,
                records, second.observation().tombstones(), secondUntyped, before, after, limits, true, false);
    }
    private static RetiredIdentity retired(UntypedRecord record, Map<String, RetiredIdentity> permitted) throws IOException {
        RetiredIdentity actual = new RetiredIdentity(record.id().value(), record.canonicalTokenSha256(), record.canonicalTokenBytes());
        if (!actual.equals(permitted.get(record.id().value()))) throw new IOException("unclassified or changed missing-type record: " + record.id().value());
        return actual;
    }
    private static String permanent(Clausewitz.Block body, Descriptor type) throws IOException {
        if (type.permanentFlag().isEmpty()) return "";
        String flag = type.permanentFlag();
        Clausewitz.Block variables = block(body, "variables"), data = block(variables, "data");
        Clausewitz.Block found = null;
        for (Clausewitz.Entry entry : data.entries()) {
            if (!(entry.value() instanceof Clausewitz.Block item)) continue;
            if (atom(item, "flag").map(FinancialStoryDigest::unquote).orElse("").equals(flag)) {
                if (found != null) throw new IOException("duplicate permanent ID flag"); found = block(item, "data");
            }
        }
        if (found == null || !atom(found, "type").orElse("").equals("value") || found.entries().size() != 2)
            throw new IOException("explicit positive typed permanent ID required");
        String raw = atom(found, "identity").orElseThrow(() -> new IOException("permanent ID identity absent"));
        if (!raw.matches("[1-9][0-9]{0,19}")) throw new IOException("canonical positive permanent ID lexical value required");
        BigInteger number = new BigInteger(raw); BigInteger[] exact = number.divideAndRemainder(SCALE);
        if (number.bitLength() > 63 || exact[1].signum() != 0 || exact[0].signum() <= 0) throw new IOException("positive exact scaled permanent ID required");
        return exact[0].toString();
    }
    private static java.util.Optional<String> atom(Clausewitz.Block body, String key) {
        List<Clausewitz.Entry> entries = body.named(key);
        if (entries.isEmpty()) return java.util.Optional.empty();
        if (entries.size() != 1 || !entries.getFirst().operator().equals("=") || !(entries.getFirst().value() instanceof Clausewitz.Atom value))
            throw new IllegalArgumentException("single assigned atom required: " + key);
        return java.util.Optional.of(value.token());
    }
    private static Clausewitz.Block block(Clausewitz.Block body, String key) throws IOException {
        List<Clausewitz.Entry> entries = body.named(key);
        if (entries.size() != 1 || !entries.getFirst().operator().equals("=") || !(entries.getFirst().value() instanceof Clausewitz.Block value))
            throw new IOException("single assigned block required: " + key); return value;
    }
    private static String unquote(String token) {
        return token.startsWith("\"") && token.endsWith("\"") ? token.substring(1, token.length() - 1) : token;
    }
    private static Pass pass(Path path, Pin expected, Limits limits, List<NativeId> ids, StreamingTableSink sink,
                             FileFacts original) throws IOException {
        StreamingTable table = new StreamingTable(List.of("stories", "active"), "story_cycle", ids,
                limits.maxTableRecords(), limits.maxRecordBytes(), limits.maxStreamedBytes(), true, MissingDiscriminatorPolicy.CAPTURE_MISSING_BOUNDED);
        Selection selection = new Selection(List.of(), List.of(), true, false, List.of());
        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.READ)) {
            if (channel.size() != expected.bytes() || !original.equals(facts(path))) throw new IOException("SAVE changed before open");
            Tracked tracked = new Tracked(Channels.newInputStream(channel), expected.bytes());
            try (PushbackInputStream plain = new PushbackInputStream(tracked, 4)) {
                byte[] signature = plain.readNBytes(4);
                if (signature.length != 4 || signature[0] == 'P' && signature[1] == 'K') throw new IOException("actual plain SAVE required");
                plain.unread(signature);
                SaveStream parser = new SaveStream(new InputStreamReader(plain, StandardCharsets.UTF_8.newDecoder()
                        .onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)), selection, table, sink);
                Projection projection = parser.read();
                if (tracked.read() != -1 || tracked.count != expected.bytes() || channel.position() != tracked.count || channel.size() != tracked.count)
                    throw new IOException("complete SAVE byte extent/EOF differs");
                String hash = HexFormat.of().formatHex(tracked.digest.digest());
                if (!hash.equals(expected.sha256()) || !original.equals(facts(path)) || !Files.isSameFile(path, Path.of(expected.path())))
                    throw new IOException("SAVE SHA/physical identity changed");
                List<String> dates = projection.rootScalars().stream().filter(e -> e.key().equals("date") && e.value() instanceof Clausewitz.Atom)
                        .map(e -> unquote(((Clausewitz.Atom) e.value()).token())).toList();
                if (dates.size() != 1) throw new IOException("one original root date required");
                return new Pass(hash, tracked.count, dates.getFirst(), parser.streamingObservation());
            }
        }
    }
    private static FileFacts facts(Path path) throws IOException {
        BasicFileAttributes a = Files.readAttributes(path, BasicFileAttributes.class);
        if (!a.isRegularFile()) throw new IOException("regular SAVE required");
        return new FileFacts(path.toRealPath().toString(), a.fileKey() == null ? "UNAVAILABLE" : a.fileKey().toString(), a.size(), a.creationTime().toString(), a.lastModifiedTime().toString());
    }
    private static void verifyRuntime(List<Pin> expected) throws Exception {
        List<Class<?>> types = List.of(SaveStream.class, com.fasterxml.jackson.annotation.JsonCreator.class,
                com.fasterxml.jackson.core.JsonParser.class, com.fasterxml.jackson.databind.ObjectMapper.class, SaveAuditSources.class);
        List<Path> observed = new ArrayList<>();
        for (Class<?> type : types) {
            Path loaded = Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
            List<Pin> matches = expected.stream().filter(pin -> Path.of(pin.path()).toAbsolutePath().normalize().equals(loaded)).toList();
            if (!Files.isRegularFile(loaded) || matches.size() != 1 || observed.contains(loaded)) throw new IOException("loaded JAR differs from requested exact classpath");
            FilePins.verify(loaded, matches.getFirst()); observed.add(loaded);
        }
    }
    private static final class Tracked extends FilterInputStream {
        private final MessageDigest digest; private final long limit; private long count;
        Tracked(InputStream input, long limit) { super(input); this.limit = limit;
            try { digest = MessageDigest.getInstance("SHA-256"); } catch (java.security.NoSuchAlgorithmException e) { throw new IllegalStateException(e); } }
        @Override public int read() throws IOException { int value = in.read(); if (value >= 0) { if (++count > limit) throw new IOException("SAVE exceeds expected bound"); digest.update((byte) value); } return value; }
        @Override public int read(byte[] b, int off, int len) throws IOException {
            int n = in.read(b, off, len); if (n > 0) { count = Math.addExact(count, n); if (count > limit) throw new IOException("SAVE exceeds expected bound"); digest.update(b, off, n); } return n;
        }
    }
}
