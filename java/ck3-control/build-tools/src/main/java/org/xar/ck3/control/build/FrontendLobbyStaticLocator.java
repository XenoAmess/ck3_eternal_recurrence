package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** Closed, one-pass lobby-name candidate discovery. No instruction or callable qualification is issued. */
public final class FrontendLobbyStaticLocator {
    public static final String SCHEMA = "xar.frontend-lobby-static-locator/v1";
    public static final String INPUT = "Z:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe";
    public static final String IMAGE_SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final String SOURCE_SHA = "4fe465cf2fe32ba51e1df1d318b0318bb3444aa394e6c37a4083cd082e43cd17";
    public static final long IMAGE_BYTES = 101040248, IMAGE_BASE = 5368709120L;
    public static final int BODY_MAX = 32768, JOURNAL_MAX = 262144, CHUNK_MAX = 1048576;
    private static final int NAME_MAX = 8, XREF_MAX = 64, CARRY = 64;
    private static final long META_MAX = 18L * 1048576, CODE_MAX = 72L * 1048576;
    private FrontendLobbyStaticLocator() { }

    public enum Name { GetSelectedPlayable, CanTryStartRulerDesigning, SetRandomPlayableObserverCharacter }
    public enum Encoding { RIP_LEA, RIP_LOAD, RIP_STORE, MOVABS_IMMEDIATE }
    public enum Status { COMPLETE_UNVALIDATED, MISSING_ANCHOR, AMBIGUOUS_OVER_LIMIT, BODY_LIMIT, FAILED }
    public enum Origin { SOURCE17_IMAGE, SOFTWARE_FIXTURE }
    public record Section(String name, long rva, long offset, int bytes) {
        public Section {
            Objects.requireNonNull(name);
            if (rva < 0 || offset < 0 || bytes < 1 || offset > Long.MAX_VALUE - bytes) throw new IllegalArgumentException("finite section required");
        }
    }
    private static final Section RDATA = new Section(".rdata", 71147520, 71142912, 17124352);
    private static final Section TEXT = new Section(".text", 4096, 1024, 71141888);
    public record Budget(long metadataMaximum, long codeMaximum, long dataMaximum, long identityApiMaximum,
                         int chunkBytes, int journalMaximum, int bodyMaximum) {
        public Budget {
            if (metadataMaximum < 1216 || metadataMaximum > META_MAX || codeMaximum < 1 || codeMaximum > CODE_MAX
                    || dataMaximum != 0 || identityApiMaximum < 32768 || identityApiMaximum > 1048576
                    || chunkBytes < 64 || chunkBytes > CHUNK_MAX || journalMaximum < 16384 || journalMaximum > JOURNAL_MAX
                    || bodyMaximum < 2048 || bodyMaximum > BODY_MAX) throw new IllegalArgumentException("closed finite budgets required");
        }
    }
    public record Request(String schema, String machineId, String runId, String inputPath, FileRef fullHashEvidence,
                          String outputRoot, SharedSourceFiles.DirectoryIdentity outputRootIdentity,
                          Budget budget, String reviewAtUtc) {
        public Request {
            if (!SCHEMA.equals(schema) || machineId == null || !machineId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
                    || runId == null || !runId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,95}") || !INPUT.equals(inputPath))
                throw new IllegalArgumentException("closed source17 named-lobby request required");
            Objects.requireNonNull(fullHashEvidence); Objects.requireNonNull(outputRootIdentity); Objects.requireNonNull(budget);
            if (fullHashEvidence.bytes() != 6746 || !SOURCE_SHA.equals(fullHashEvidence.sha256())
                    || !Path.of(outputRoot).isAbsolute() || !Path.of(outputRoot).normalize().equals(Path.of(outputRoot)))
                throw new IllegalArgumentException("exact source17 and normalized absolute output root required");
            Instant.parse(reviewAtUtc);
        }
    }
    /** Issued only after the new producer software PASS and a separate Root limited acceptance. */
    public record Admission(String schema, String machineId, String issuer, String scope, FileRef request,
                            FileRef financialGrant, FileRef softwareQualification, FileRef rootLimitedAcceptance,
                            String reviewAtUtc) {
        public Admission {
            if (!SCHEMA.equals(schema) || !"/root/budget_fast_lane".equals(issuer)
                    || !"FRONTEND_LOBBY_CLOSED_THREE_NAMES_ONE_SHOT".equals(scope))
                throw new IllegalArgumentException("new finite named-lobby admission required");
            Objects.requireNonNull(machineId); Objects.requireNonNull(request); Objects.requireNonNull(financialGrant);
            Objects.requireNonNull(softwareQualification); Objects.requireNonNull(rootLimitedAcceptance); Instant.parse(reviewAtUtc);
        }
    }
    public record Anchor(Name name, long rva, long fileOffset) {
        public Anchor { Objects.requireNonNull(name); if (rva < 0 || fileOffset < 0) throw new IllegalArgumentException("nonnegative anchor location required"); }
    }
    public record Xref(long anchorRva, @JsonProperty("rva") long instructionRva, @JsonProperty("offset") long fileOffset,
                       Encoding encoding, @JsonProperty("width") int operandWidth, @JsonProperty("bytes") String bytesHex) {
        public Xref {
            Objects.requireNonNull(encoding);
            int width = encoding == Encoding.MOVABS_IMMEDIATE ? 8 : 4;
            if (anchorRva < 0 || instructionRva < 0 || fileOffset < 0 || operandWidth != width || bytesHex == null
                    || !bytesHex.matches(width == 8 ? "[0-9a-f]{20}" : "[0-9a-f]{14}")) throw new IllegalArgumentException("exact bounded candidate encoding required");
        }
    }
    public record NameResult(Name name, long anchorCount, long xrefCount, boolean xrefCountComplete,
                             boolean anchorDetailsTruncated, boolean xrefDetailsTruncated, List<Anchor> anchors, List<Xref> candidates) {
        public NameResult {
            Objects.requireNonNull(name); anchors = List.copyOf(anchors); candidates = List.copyOf(candidates);
            if (anchorCount < anchors.size() || xrefCount < candidates.size() || anchors.size() > NAME_MAX || candidates.size() > XREF_MAX
                    || anchorCount < 0 || xrefCount < 0 || xrefCountComplete && anchorCount > NAME_MAX)
                throw new IllegalArgumentException("bounded truthful name counts required");
        }
    }
    public record SectionResult(Section section, long bytesRead, String sha256, boolean complete) { }
    public record Counts(long metadataRequested, long metadataReported, long codeRequested, long codeReported,
                         long identityApiBufferUpper, int readCalls, boolean physicalIoMeasured) {
        public Counts {
            if (metadataRequested < 0 || metadataReported < 0 || metadataReported > metadataRequested || codeRequested < 0
                    || codeReported < 0 || codeReported > codeRequested || identityApiBufferUpper < 0 || readCalls < 0 || physicalIoMeasured)
                throw new IllegalArgumentException("reported logical reads only; physical IO was not measured");
        }
    }
    public record Body(String schema, String machineId, String observedAtUtc, Origin origin, Status status,
                       String qualification, FileRef request, FileRef admission, FileRef reusedFullHash,
                       String reusedImageSha256, SharedSourceFiles.NativeFile beforeIdentity, SharedSourceFiles.NativeFile afterIdentity,
                       String beforePeSha256, String afterPeSha256,
                       List<SectionResult> sections, List<NameResult> names, Counts counts,
                       boolean candidatesOmittedForBodyLimit, String inputClose, String failure) {
        public Body {
            if (!SCHEMA.equals(schema) || !"UNVALIDATED_CANDIDATES_ONLY".equals(qualification)) throw new IllegalArgumentException("unvalidated locator data only");
            Objects.requireNonNull(origin); Objects.requireNonNull(status); Objects.requireNonNull(counts);
            Instant.parse(observedAtUtc); sections = List.copyOf(sections); names = List.copyOf(names);
            if (sections.size() > 2 || names.size() != 3 || origin == Origin.SOFTWARE_FIXTURE && (reusedFullHash != null || reusedImageSha256 != null))
                throw new IllegalArgumentException("bounded section/name DATA origin required");
        }
    }
    private record Plan(String machine, String input, String root, SharedSourceFiles.DirectoryIdentity rootIdentity,
                        Budget budget, Instant review, Origin origin, Section rdata, Section text, long imageBase,
                        long fileBytes, FileRef request, FileRef admission, RawWindowImageProof.Proof proof,
                        SharedSourceFiles.NativeFile softwareFile) { }
    private record Event(String schema, String observedAtUtc, String phase, long offset, int requested,
                         String status, Integer reported, String sha256, String detail) { }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("exact request.json admission.json required");
        var originalRequest = RawWindowCaptureJson.readOriginal(Path.of(args[0]), 65536);
        var originalAdmission = RawWindowCaptureJson.readOriginal(Path.of(args[1]), 65536);
        Request request = RawWindowCaptureJson.decode(originalRequest.bytes(), Request.class, 65536);
        Admission admission = RawWindowCaptureJson.decode(originalAdmission.bytes(), Admission.class, 65536);
        validateAdmission(request, originalRequest.reference(), admission);
        RawWindowImageProof.Proof proof = RawWindowImageProof.load(request.fullHashEvidence());
        if (!IMAGE_SHA.equals(proof.sha256()) || proof.identity().size() != IMAGE_BYTES) throw new IOException("source17 actual image differs");
        Plan plan = new Plan(request.machineId(), request.inputPath(), request.outputRoot(), request.outputRootIdentity(),
                request.budget(), earlier(Instant.parse(request.reviewAtUtc()), Instant.parse(admission.reviewAtUtc())),
                Origin.SOURCE17_IMAGE, RDATA, TEXT, IMAGE_BASE, IMAGE_BYTES,
                originalRequest.reference(), originalAdmission.reference(), proof, null);
        Body result = run(plan);
        System.out.println(new String(encode(result), StandardCharsets.UTF_8));
        if (result.status() != Status.COMPLETE_UNVALIDATED) System.exit(2);
    }
    static void validateAdmission(Request request, FileRef requestRef, Admission admission) throws IOException {
        if (!request.machineId().equals(admission.machineId()) || !requestRef.equals(admission.request()))
            throw new IOException("same machine and exact new request admission required");
        deadline(earlier(Instant.parse(request.reviewAtUtc()), Instant.parse(admission.reviewAtUtc())));
        RawWindowCaptureJson.exactBytes(admission.financialGrant(), 131072);
        JsonNode software = RawWindowCaptureJson.tree(RawWindowCaptureJson.exactBytes(admission.softwareQualification(), 65536));
        JsonNode accepted = RawWindowCaptureJson.tree(RawWindowCaptureJson.exactBytes(admission.rootLimitedAcceptance(), 65536));
        if (!"xar.frontend-lobby-locator-software/v1".equals(text(software, "schema"))
                || !"PASS".equals(text(software, "status")) || !request.machineId().equals(text(software, "machine_id"))
                || !"xar.frontend-lobby-locator-limited-acceptance/v1".equals(text(accepted, "schema"))
                || !"ACCEPTED_UNVALIDATED_CANDIDATES_ONLY".equals(text(accepted, "status"))
                || !"/root".equals(text(accepted, "owner")) || !request.machineId().equals(text(accepted, "machine_id")))
            throw new IOException("actual new software qualification and Root limited acceptance required");
        if (!admission.softwareQualification().equals(ControlBuild.strictMapper().treeToValue(accepted.get("software_qualification"), FileRef.class))
                || !requestRef.equals(ControlBuild.strictMapper().treeToValue(accepted.get("request"), FileRef.class)))
            throw new IOException("Root acceptance must bind exact request and actual software receipt");
        for (String field : List.of("found", "started", "succeeded")) if (RawWindowCaptureJson.integer(software.get(field)) != 10)
            throw new IOException("all ten fixed software methods must execute");
        for (String field : List.of("skipped", "failed")) if (RawWindowCaptureJson.integer(software.get(field)) != 0)
            throw new IOException("no skipped or failed software methods admitted");
        JsonNode read = software.get("real_image_read");
        if (read == null || !read.isBoolean() || read.booleanValue()) throw new IOException("qualification must use only the software fixture");
        for (String field : List.of("producer_class_sha256", "test_class_sha256")) if (!text(software, field).matches("[0-9a-f]{64}"))
            throw new IOException("actual compiled software class hashes required");
    }
    private static String text(JsonNode node, String key) throws IOException { return RawWindowCaptureJson.text(node.get(key)); }

    /** Test-only DATA origin: no admission token, source17 substitution or production CLI route. Uses the actual retained native backend. */
    static Body softwareFixture(Path input, Path root, Section rdata, Section code, long imageBase, Budget budget) throws IOException {
        SharedSourceFiles.NativeFile source = SharedSourceFiles.nativeFile(input);
        Plan plan = new Plan(WindowsJobProcess.currentMachineId(), input.toAbsolutePath().normalize().toString(),
                root.toAbsolutePath().normalize().toString(), SharedSourceFiles.nativeDirectory(root), budget,
                Instant.now().plusSeconds(60), Origin.SOFTWARE_FIXTURE, rdata, code, imageBase,
                source.logicalBytes(), null, null, null, source);
        return run(plan);
    }
    private static Body run(Plan plan) throws IOException {
        Budget budget = plan.budget();
        if (plan.rdata().bytes() + 1216L + budget.identityApiMaximum() > budget.metadataMaximum()
                || plan.text().bytes() > budget.codeMaximum()) throw new IOException("entire once-only scan must fit before any native read");
        long calls = 4L + (plan.rdata().bytes() + (long) budget.chunkBytes() - 1) / budget.chunkBytes()
                + (plan.text().bytes() + (long) budget.chunkBytes() - 1) / budget.chunkBytes();
        if (calls * 1024 + 8192 > budget.journalMaximum()) throw new IOException("complete intent/observation journal must fit before first native read");
        var descriptor = new RawWindowNativeIo.NamedInput(plan.input(), plan.root(), plan.rootIdentity(),
                budget.identityApiMaximum(), budget.journalMaximum(), budget.bodyMaximum());
        try (RawWindowNativeIo io = RawWindowNativeIo.namedFrontend(descriptor)) {
            if (!plan.machine().equals(io.machineId())) throw new IOException("actual machine differs");
            deadline(plan.review());
            io.startMetadataJournal(event("STARTED", 0, 0, plan.origin().name(), null, null, "closed-three-names; no raw copies"));
            State state = new State(plan, io); SharedSourceFiles.NativeFile before = null, after = null;
            String failure = ""; CloseStatus close = CloseStatus.NOT_OPENED;
            List<SectionResult> sections = new ArrayList<>(); Status status = Status.FAILED;
            try {
                io.openInput(); before = state.identity();
                byte[] dos = state.read(0, 64, false), pe = state.read(344, 544, false);
                state.beforePeSha = headerHash(dos, pe);
                requirePe(dos, pe, plan.rdata(), plan.text(), plan.imageBase(), plan.fileBytes(), plan.origin());
                sections.add(state.section(plan.rdata(), false));
                sections.add(state.section(plan.text(), true));
                byte[] afterDos = state.read(0, 64, false), afterPe = state.read(344, 544, false);
                state.afterPeSha = headerHash(afterDos, afterPe);
                if (!Arrays.equals(dos, afterDos) || !Arrays.equals(pe, afterPe)) throw new IOException("fresh PE changed across scan");
                after = state.identity();
                if (!before.equals(after)) throw new IOException("actual held/path native identity drift");
                DirectoryProbe directory = io.directory();
                if (directory.status() != ProbeStatus.OBSERVED || !plan.rootIdentity().equals(directory.value())) throw new IOException("output directory custody drift");
                status = state.scan.status();
            } catch (IOException | RuntimeException error) {
                failure = error.getClass().getSimpleName() + ": " + String.valueOf(error.getMessage());
                if (failure.length() > 768) failure = failure.substring(0, 768);
            } finally { close = io.closeInput(); }
            if (close != CloseStatus.CLOSED) { status = Status.FAILED; failure = "input close not confirmed; " + failure; }
            Body body = state.body(status, before, after, sections, false, close, failure);
            byte[] encoded = encode(body);
            if (encoded.length > budget.bodyMaximum()) {
                body = state.body(Status.BODY_LIMIT, before, after, sections, true, close, "candidate details omitted: reserved body limit");
                encoded = encode(body);
            }
            if (encoded.length > budget.bodyMaximum()) throw new IOException("even bounded failure body exceeds reservation; journal retained");
            io.appendMetadata(event("FINISHED", 0, 0, body.status().name(), encoded.length, RawWindowCaptureJson.hash(encoded), body.failure()));
            io.publishBody(encoded); return body;
        }
    }
    private static final class State {
        final Plan plan; final RawWindowNativeIo io; final Scanner scan;
        long metadataRequested, metadataReported, codeRequested, codeReported; int calls; String beforePeSha, afterPeSha;
        State(Plan plan, RawWindowNativeIo io) { this.plan = plan; this.io = io; scan = new Scanner(plan.rdata(), plan.text(), plan.imageBase()); }
        SharedSourceFiles.NativeFile identity() throws IOException {
            deadline(plan.review()); FileProbe held = io.held(), path = io.path();
            if (held.status() != ProbeStatus.OBSERVED || path.status() != ProbeStatus.OBSERVED || held.value() == null
                    || !held.value().equals(path.value()) || held.finalPath() == null
                    || !SharedSourceFiles.nativePathValue(RawWindowImageProof.stripExtended(held.finalPath()).replace('/', '\\'))
                    .equals(SharedSourceFiles.nativePathValue(plan.input().replace('/', '\\'))))
                throw new IOException("actual same held/path identity and final spelling required");
            if (plan.origin() == Origin.SOURCE17_IMAGE) plan.proof().requireCurrent(plan.machine(), plan.input(), held.value());
            else if (!plan.softwareFile().equals(held.value())) throw new IOException("actual software fixture identity drift");
            return held.value();
        }
        byte[] read(long offset, int length, boolean code) throws IOException {
            deadline(plan.review());
            if (offset < 0 || length < 1 || length > plan.budget().chunkBytes() && length > 544 || offset > plan.fileBytes() - length)
                throw new IOException("finite exact in-file range required");
            long next = Math.addExact(code ? codeRequested : metadataRequested, length);
            if (next > (code ? plan.budget().codeMaximum() : plan.budget().metadataMaximum() - plan.budget().identityApiMaximum()))
                throw new IOException("read category budget exhausted before intent");
            io.appendMetadata(event("READ_INTENT", offset, length, code ? "CODE" : "METADATA", null, null, "one-shot range"));
            if (code) codeRequested = next; else metadataRequested = next; calls++;
            ReadResult result = io.read(new ReadRange(offset, length)); byte[] actual = result.returnedBytes();
            Integer count = actual == null ? null : actual.length;
            if (count != null) { if (code) codeReported += count; else metadataReported += count; }
            io.appendMetadata(event("READ_OBSERVED", offset, length, result.status().name(), count,
                    actual == null ? null : RawWindowCaptureJson.hash(actual), "win32=" + result.win32Error()));
            if (result.status() != ReadStatus.COMPLETE || actual == null || actual.length != length)
                throw new IOException("short/error/unknown native read; no retry or zero-fill");
            return actual;
        }
        SectionResult section(Section section, boolean code) throws IOException {
            MessageDigest digest = digest(); byte[] carry = new byte[0]; long cursor = 0;
            while (cursor < section.bytes()) {
                int size = (int) Math.min(plan.budget().chunkBytes(), section.bytes() - cursor);
                byte[] raw = read(section.offset() + cursor, size, code); digest.update(raw);
                byte[] joined = new byte[carry.length + raw.length]; System.arraycopy(carry, 0, joined, 0, carry.length);
                System.arraycopy(raw, 0, joined, carry.length, raw.length);
                long base = cursor - carry.length;
                if (code) scan.references(joined, base, cursor); else scan.anchors(joined, base, cursor);
                carry = Arrays.copyOfRange(joined, Math.max(0, joined.length - CARRY), joined.length); cursor += raw.length;
            }
            return new SectionResult(section, cursor, HexFormat.of().formatHex(digest.digest()), true);
        }
        Body body(Status status, SharedSourceFiles.NativeFile before, SharedSourceFiles.NativeFile after,
                  List<SectionResult> sections, boolean omitted, CloseStatus close, String failure) {
            return new Body(SCHEMA, plan.machine(), Instant.now().toString(), plan.origin(), status, "UNVALIDATED_CANDIDATES_ONLY",
                    plan.request(), plan.admission(), plan.proof() == null ? null : plan.proof().original(),
                    plan.proof() == null ? null : plan.proof().sha256(), before, after, beforePeSha, afterPeSha, sections, scan.results(omitted),
                    new Counts(metadataRequested, metadataReported, codeRequested, codeReported, io.fileIdentityApiBufferChargeUpper(), calls, false),
                    omitted, close.name(), failure);
        }
    }
    /** Pure bounded candidate engine. Original section bytes are streamed by the same production loop. */
    static final class Scanner {
        final Section rdata, code; final long imageBase;
        final long[] anchorCounts = new long[3], xrefCounts = new long[3];
        final List<List<Anchor>> names = new ArrayList<>(); final List<List<Xref>> refs = new ArrayList<>();
        Scanner(Section rdata, Section code, long imageBase) {
            this.rdata = rdata; this.code = code; this.imageBase = imageBase;
            for (Name ignored : Name.values()) { names.add(new ArrayList<>()); refs.add(new ArrayList<>()); }
        }
        void anchors(byte[] bytes, long base, long newStart) {
            for (Name name : Name.values()) {
                // Trailing NUL is exact; a pooled suffix may have a nonzero preceding byte.
                byte[] needle = (name.name() + "\0").getBytes(StandardCharsets.US_ASCII);
                for (int i = 0; i + needle.length <= bytes.length; i++) {
                    long start = base + i, end = start + needle.length;
                    if (end <= newStart || start < 0 || end > rdata.bytes()) continue;
                    if (!matches(bytes, i, needle)) continue;
                    int index = name.ordinal(); anchorCounts[index]++;
                    if (names.get(index).size() < NAME_MAX) names.get(index).add(new Anchor(name, rdata.rva() + start, rdata.offset() + start));
                }
            }
        }
        void references(byte[] bytes, long base, long newStart) {
            for (int i = 0; i < bytes.length; i++) {
                int rex = u8(bytes, i); if (rex < 0x48 || rex > 0x4f || i + 2 >= bytes.length) continue;
                int op = u8(bytes, i + 1), length; long target; Encoding encoding;
                if ((op == 0x8d || op == 0x8b || op == 0x89) && (u8(bytes, i + 2) & 0xc7) == 5) {
                    length = 7; if (i + length > bytes.length) continue;
                    target = code.rva() + base + i + length + i32(bytes, i + 3);
                    encoding = op == 0x8d ? Encoding.RIP_LEA : op == 0x8b ? Encoding.RIP_LOAD : Encoding.RIP_STORE;
                } else if (op >= 0xb8 && op <= 0xbf) {
                    length = 10; if (i + length > bytes.length) continue;
                    target = i64(bytes, i + 2) - imageBase; encoding = Encoding.MOVABS_IMMEDIATE;
                } else continue;
                long start = base + i;
                if (start < 0 || start + length <= newStart || start + length > code.bytes()) continue;
                for (Name name : Name.values()) for (Anchor anchor : names.get(name.ordinal())) if (anchor.rva() == target) {
                    int index = name.ordinal(); xrefCounts[index]++;
                    if (refs.get(index).size() < XREF_MAX) refs.get(index).add(new Xref(target, code.rva() + start,
                            code.offset() + start, encoding, length == 10 ? 8 : 4, HexFormat.of().formatHex(bytes, i, i + length)));
                }
            }
        }
        Status status() {
            for (int i = 0; i < 3; i++) if (anchorCounts[i] > NAME_MAX || xrefCounts[i] > XREF_MAX) return Status.AMBIGUOUS_OVER_LIMIT;
            for (long count : anchorCounts) if (count == 0) return Status.MISSING_ANCHOR;
            return Status.COMPLETE_UNVALIDATED;
        }
        List<NameResult> results(boolean omit) {
            List<NameResult> result = new ArrayList<>();
            for (Name name : Name.values()) { int i = name.ordinal(); result.add(new NameResult(name, anchorCounts[i], xrefCounts[i],
                    anchorCounts[i] <= NAME_MAX, omit || anchorCounts[i] > NAME_MAX, omit || xrefCounts[i] > XREF_MAX,
                    omit ? List.of() : names.get(i), omit ? List.of() : refs.get(i))); }
            return List.copyOf(result);
        }
    }
    static void requirePe(byte[] dos, byte[] pe, Section rdata, Section text, long base, long fileBytes, Origin origin) throws IOException {
        if (dos.length != 64 || pe.length != 544 || u8(dos, 0) != 0x4d || u8(dos, 1) != 0x5a || i32(dos, 60) != 344
                || i32(pe, 0) != 0x4550 || u16(pe, 4) != 0x8664 || u16(pe, 6) != 7 || u16(pe, 20) != 240
                || u16(pe, 24) != 0x20b || i64(pe, 48) != base) throw new IOException("fresh fixed PE32+ geometry differs");
        if (origin == Origin.SOURCE17_IMAGE && (Integer.toUnsignedLong(i32(pe, 8)) != 1791204405L
                || i32(pe, 160) != 98316288 || i32(pe, 164) != 2933220 || fileBytes != IMAGE_BYTES))
            throw new IOException("source17 fresh PE header differs");
        sectionHeader(pe, 264, text, fileBytes); sectionHeader(pe, 304, rdata, fileBytes);
        if (origin == Origin.SOURCE17_IMAGE) {
            int[] virtualSizes = {71141448,17123946,10040928,2933220,1040,79496,1176160};
            for (int i = 0; i < 7; i++) if (i32(pe, 264 + 40 * i + 8) != virtualSizes[i]) throw new IOException("fresh section virtual size differs");
            long[][] rest = {{88272896,8571392,88267264},{98316288,2933248,96838656},{101253120,1536,99771904},
                    {101257216,79872,99773440},{101339136,1176576,99853312}};
            String[] labels = {".data", ".pdata", "_RDATA", ".rsrc", ".reloc"};
            for (int i = 0; i < 5; i++) sectionHeader(pe, 344 + 40 * i,
                    new Section(labels[i], rest[i][0], rest[i][2], (int) rest[i][1]), fileBytes);
        }
    }
    private static void sectionHeader(byte[] pe, int at, Section section, long size) throws IOException {
        byte[] name = section.name().getBytes(StandardCharsets.US_ASCII);
        for (int i = 0; i < 8; i++) if (u8(pe, at + i) != (i < name.length ? name[i] & 255 : 0)) throw new IOException("section name differs");
        if (Integer.toUnsignedLong(i32(pe, at + 12)) != section.rva() || Integer.toUnsignedLong(i32(pe, at + 16)) != section.bytes()
                || Integer.toUnsignedLong(i32(pe, at + 20)) != section.offset() || section.offset() > size - section.bytes())
            throw new IOException("fresh section bounds differ");
    }
    static byte[] encode(Body value) throws IOException { return ControlBuild.strictMapper().writeValueAsBytes(value); }
    private static String headerHash(byte[] dos, byte[] pe) { MessageDigest hash = digest(); hash.update(dos); hash.update(pe); return HexFormat.of().formatHex(hash.digest()); }
    private static byte[] event(String phase, long offset, int requested, String status, Integer reported, String sha, String detail) throws IOException {
        return ControlBuild.strictMapper().writeValueAsBytes(new Event(SCHEMA, Instant.now().toString(), phase, offset, requested, status, reported, sha, detail));
    }
    private static boolean matches(byte[] haystack, int at, byte[] needle) { for (int j = 0; j < needle.length; j++) if (haystack[at + j] != needle[j]) return false; return true; }
    private static int u8(byte[] b, int at) { return b[at] & 255; }
    private static int u16(byte[] b, int at) { return u8(b, at) | u8(b, at + 1) << 8; }
    private static int i32(byte[] b, int at) { return u8(b, at) | u8(b, at + 1) << 8 | u8(b, at + 2) << 16 | u8(b, at + 3) << 24; }
    private static long i64(byte[] b, int at) { return Integer.toUnsignedLong(i32(b, at)) | ((long) i32(b, at + 4) << 32); }
    private static MessageDigest digest() { try { return MessageDigest.getInstance("SHA-256"); } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
    private static Instant earlier(Instant a, Instant b) { return a.isBefore(b) ? a : b; }
    private static void deadline(Instant review) throws IOException { if (!Instant.now().isBefore(review)) throw new IOException("new admission/review expired; no further native read"); }
}
