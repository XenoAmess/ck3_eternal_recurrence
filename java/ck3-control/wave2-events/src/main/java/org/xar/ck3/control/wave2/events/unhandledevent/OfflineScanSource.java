package org.xar.ck3.control.wave2.events.unhandledevent;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.offline.IncidentJournalLayout;
import org.xar.ck3.control.contracts.offline.IncidentReadIndex;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding.Binding;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding.ObservedScan;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Loads the real manifest, complete scan index and its original journal files under fixed server roots. */
public final class OfflineScanSource {
    private static final int FILE_MAX = 1 << 20;
    private OfflineScanSource() { }
    public record ExternalOriginal(ExactRef source, long maximumBytes) { }
    public record Loaded(Binding binding, byte[] manifestBytes, List<ExactRef> scanOriginals, List<ExternalOriginal> externalOriginals) {
        public Loaded { manifestBytes = manifestBytes.clone(); scanOriginals = List.copyOf(scanOriginals); externalOriginals = List.copyOf(externalOriginals); }
        public Loaded(Binding binding, byte[] manifestBytes, List<ExactRef> scanOriginals) { this(binding, manifestBytes, scanOriginals, List.of()); }
        @Override public byte[] manifestBytes() { return manifestBytes.clone(); }
    }

    public static Loaded load(Path incidentRoot, Optional<Path> scanRoot, String machineId,
            ExactRef manifest, List<ExactRef> captured) throws IOException {
        Path manifestPath = absolute(manifest.path());
        Path admitted = manifestPath.startsWith(incidentRoot) ? incidentRoot
                : scanRoot.filter(root -> manifestPath.startsWith(root)).orElseThrow(() -> new IllegalArgumentException("Manifest escapes fixed incident/scan roots"));
        byte[] raw = read(admitted, manifest); ObjectNode document = json(raw);
        Binding binding = OfflineBatchBinding.manifest(document);
        if (!(binding instanceof ObservedScan actual)) {
            require(admitted.equals(incidentRoot), "Legacy manifest must use its original fixed incident root");
            return new Loaded(binding, raw, List.of());
        }
        Path scans = scanRoot.orElseThrow(() -> new IllegalArgumentException("Actual v2 scan requires an explicit fixed server scan root"));
        require(admitted.equals(scans) && !scans.startsWith(incidentRoot) && !incidentRoot.startsWith(scans), "V2 scan and incident roots must be distinct");
        if (!manifestPath.getParent().equals(scans)) {
            var scope = IncidentJournalLayout.scope(incidentRoot, scans, actual.observation().machineId(), actual.observation().game(),
                    actual.sessionId(), actual.observation().frame().episodeRunId(), actual.source().sourceRef());
            require(manifestPath.getParent().equals(scope.scanRoot()), "Actual per-Game scan path differs from its complete source identity");
            incidentRoot = scope.incidentRoot(); scans = scope.scanRoot();
        }
        require(actual.observation().machineId().equals(machineId), "Actual scan belongs to another source machine");
        verifySource(actual.source().sourceRef());
        require(manifestPath.equals(scans.resolve("incidents-" + manifest.sha256() + ".batch.json")), "Actual manifest filename lost its source digest");
        byte[] indexRaw = read(scans, actual.indexRef());
        require(Path.of(actual.indexRef().path()).equals(scans.resolve(actual.indexRef().sha256() + ".scan.json")), "Actual scan-index filename lost its source digest");
        ObjectNode index = json(indexRaw); boolean progress = "xar.episode-incident-scan/v3".equals(text(index, "schema"));
        boolean diagnostics = progress || "xar.episode-incident-scan/v2".equals(text(index, "schema"));
        StrictJson.object(index, progress ? Set.of("schema", "origin", "source", "session_id", "incidents", "captured_incidents", "incomplete_after", "diagnostic_only", "episode_ref", "original_refs", "scan_observation_basis")
                : diagnostics ? Set.of("schema", "origin", "source", "session_id", "incidents", "captured_incidents", "incomplete_after", "diagnostic_only", "episode_ref", "original_refs")
                : Set.of("schema", "origin", "source", "session_id", "incidents", "captured_incidents", "incomplete_after", "episode_ref", "original_refs"));
        require((diagnostics || "xar.episode-incident-scan/v1".equals(text(index, "schema")))
                && actual.sessionId().equals(text(index, "session_id"))
                && actual.observation().equals(journalObservation(actual,index.get("origin")))
                && actual.source().equals(OfflineBatchBinding.source(index.get("source"))), "Original scan index differs from its actual manifest binding");
        require(index.path("original_refs").isArray() && index.path("original_refs").size() <= 1026, "Bounded complete journal source inventory required");
        Map<Path, ExactRef> originals = new LinkedHashMap<>(); long total = 0;
        for (JsonNode item : index.path("original_refs")) {
            ExactRef ref = ExactRef.fromJson(item); Path path = absolute(ref.path());
            require(originals.put(path, ref) == null, "Duplicate original journal path");
            if (path.startsWith(incidentRoot)) { total = Math.addExact(total, ref.bytes()); require(total <= 16L << 20, "Actual internal journal source inventory exceeds its finite bound"); read(incidentRoot, ref); }
        }
        ExactRef episodeRef = ExactRef.fromJson(index.get("episode_ref"));
        require(absolute(episodeRef.path()).equals(incidentRoot.resolve("EPISODE.json")) && episodeRef.equals(originals.get(absolute(episodeRef.path()))), "Original episode stamp is outside the actual scan inventory");
        ObjectNode episode = json(read(incidentRoot, episodeRef));
        boolean basisStamp = "xar.episode-incident-root/v2".equals(text(episode, "schema"));
        StrictJson.object(episode, basisStamp ? Set.of("schema", "session_id", "origin", "source", "original_observation_basis") : Set.of("schema", "session_id", "origin", "source"));
        require(basisStamp || "xar.episode-incident-root/v1".equals(text(episode, "schema")), "Actual original episode stamp required");
        sameEpisode(actual, episode);
        Map<Path, ExternalOriginal> external = new LinkedHashMap<>();
        if (basisStamp) {
            ExactRef basisRef = ExactRef.fromJson(episode.get("original_observation_basis")); declareExternal(originals, external, basisRef, FILE_MAX); verifyExternal(basisRef, FILE_MAX);
            ObjectNode basis = StrictJson.object(json(EvidenceGrantManifestPublisher.readStable(absolute(basisRef.path()), FILE_MAX)), Set.of("schema", "session_id", "origin", "source", "native_frame", "driver_facts"));
            require("xar.java.incident-observation-original/v1".equals(text(basis, "schema")) && episode.get("session_id").equals(basis.get("session_id"))
                    && episode.get("origin").equals(basis.get("origin")) && episode.get("source").equals(basis.get("source")), "Original observation basis crossed its exact historical episode binding");
            ExactRef.fromJson(basis.get("native_frame")); ExactRef.fromJson(basis.get("driver_facts")); verifyExternal(basisRef, FILE_MAX);
        }
        if (progress) {
            ExactRef basis = ExactRef.fromJson(index.get("scan_observation_basis"));
            declareExternal(originals, external, basis, FILE_MAX); verifyExternal(basis, FILE_MAX);
            ObjectNode original = json(EvidenceGrantManifestPublisher.readStable(absolute(basis.path()), FILE_MAX));
            require("xar.java.incident-observation-original/v1".equals(text(original, "schema"))
                    && index.get("origin").equals(original.get("origin")) && index.get("source").equals(original.get("source"))
                    && index.get("session_id").equals(original.get("session_id")), "Current scan progress lost its exact full-frame original");
        }
        long actualDiagnosticCount = 0, actualCapturedCount = 0;
        for (var entry : originals.entrySet()) if (entry.getKey().startsWith(incidentRoot) && entry.getKey().getFileName().toString().endsWith(".before-index.json")) {
            ObjectNode origin = json(read(incidentRoot, entry.getValue())); sameEpisode(actual, origin);
            boolean diagnostic = origin.has("capture_stage");
            IncidentReadIndex.Value readOriginals = IncidentReadIndex.decode(origin);
            StrictJson.object(origin, IncidentReadIndex.indexFields(readOriginals, diagnostic));
            String id = text(origin, "incident_id");
            require(id.matches("[0-9a-f]{32}") && entry.getKey().equals(incidentRoot.resolve(id + ".before-index.json"))
                    && Set.of("EVENT", "INTERACTION", "MANDATORY").contains(text(origin, "kind")) && text(origin, "arguments_sha256").matches("[0-9a-f]{64}"), "Strict original before index required");
            ExactRef before = ExactRef.fromJson(origin.get("before_ref"));
            require(absolute(before.path()).equals(incidentRoot.resolve(id + ".before.json")) && before.equals(originals.get(absolute(before.path()))), "Before index lost its complete inventory pin");
            // V2 retains its one receipt; V3 retains only the explicitly declared failed-read set.
            // Match the producer's 16 MiB scan budget without recursively following any receipt.
            for (ExactRef ref : readOriginals.references()) {
                Path path = absolute(ref.path());
                if (!path.startsWith(incidentRoot) && !external.containsKey(path)) {
                    total = Math.addExact(total, ref.bytes());
                    require(total <= 16L << 20, "Actual read-original scan inventory exceeds its finite bound");
                }
                long maximum = readOriginals instanceof IncidentReadIndex.KnownReceipt ? FILE_MAX : (16L << 20);
                declareExternal(originals, external, ref, maximum);
            }
            if (diagnostic) {
                require(diagnostics && "planning_diagnostic".equals(text(origin, "capture_stage")) && origin.get("action_id").isNull(), "Planning diagnostic cannot claim a submitted action");
                declareExternal(originals, external, ExactRef.fromJson(origin.get("original_frame_ref")), (64L << 20) + 4); actualDiagnosticCount++;
            } else require(!text(origin, "action_id").isBlank(), "Submitted before index needs its real action identity");
            actualCapturedCount++;
        }
        for (var entry : originals.entrySet()) if (!entry.getKey().startsWith(incidentRoot)) {
            ExternalOriginal role = external.get(entry.getKey()); require(role != null && role.source().equals(entry.getValue()), "Only explicitly declared original basis/frame may escape the journal scope"); verifyExternal(role.source(), role.maximumBytes());
        }
        Map<Path, ExactRef> supplied = new LinkedHashMap<>();
        for (ExactRef ref : captured) require(supplied.put(absolute(ref.path()), ref) == null, "Duplicate captured original path");
        Map<Path, ExactRef> used = new LinkedHashMap<>(); int incomplete = 0;
        require(StrictJson.integer(index.get("incidents"), 0, 256) == document.path("new_incidents").size(), "Actual scan incident count differs");
        long capturedCount = StrictJson.integer(index.get("captured_incidents"), 0, 1026);
        require(capturedCount >= document.path("new_incidents").size() && capturedCount == actualCapturedCount, "Actual scan lost captured incident diagnostics");
        long diagnosticCount = diagnostics ? StrictJson.integer(index.get("diagnostic_only"), 0, capturedCount) : 0;
        require(diagnosticCount == actualDiagnosticCount, "Actual scan diagnostic count differs from its original captures");
        StrictJson.integer(index.get("incomplete_after"), 0, capturedCount);
        java.util.Set<String> ids = new java.util.HashSet<>();
        for (JsonNode item : document.path("new_incidents")) {
            ObjectNode row = object(item); String kind = text(row, "kind"), id = text(row, "incident_id");
            require(id.matches("[0-9a-f]{32}") && ids.add(id), "Distinct original incident identities required");
            Set<String> fields = switch (kind) {
                case "unhandled_event" -> Set.of("incident_id", "kind", "before", "before_sha256", "after", "after_sha256", "event_definition_key", "current_event_instance_id");
                case "pending_character_interaction" -> Set.of("incident_id", "kind", "before", "before_sha256", "after", "after_sha256", "interaction_definition_key");
                case "unknown_mandatory_choice" -> Set.of("incident_id", "kind", "before", "before_sha256", "after", "after_sha256");
                default -> throw new IllegalArgumentException("Unsupported actual incident kind");
            };
            StrictJson.object(row, fields);
            Path beforePath = incidentRoot.resolve(id + ".before.json");
            ExactRef before = stage(row, "before", beforePath, supplied, originals); used.put(beforePath, before);
            ObjectNode beforeBody = json(read(incidentRoot, before));
            require(id.equals(text(beforeBody, "incident_id")), "Actual before identity differs from its batch");
            if (!kind.equals("unknown_mandatory_choice")) {
                String definitionField = kind.equals("unhandled_event") ? "event_definition_key" : "interaction_definition_key";
                require(row.get(definitionField).equals(beforeBody.get(definitionField)), "Actual batch changed its captured definition key");
            }
            if (kind.equals("unhandled_event")) require(row.get("current_event_instance_id").equals(beforeBody.get("current_event_instance_id")), "Actual batch changed its original event instance");
            Path originPath = incidentRoot.resolve(id + ".before-index.json");
            ExactRef originRef = originals.get(originPath); require(originRef != null, "Actual incident lacks its indexed producer origin");
            ObjectNode origin = json(read(incidentRoot, originRef)); sameEpisode(actual, origin);
            IncidentReadIndex.decode(origin);
            require(id.equals(text(origin, "incident_id"))
                    && (kind.equals("unknown_mandatory_choice") ? "MANDATORY" : kind.equals("unhandled_event") ? "EVENT" : "INTERACTION").equals(text(origin, "kind"))
                    && before.equals(ExactRef.fromJson(origin.get("before_ref"))), "Actual incident index crossed its before body or kind");
            if (row.get("after").isNull()) {
                require(row.get("after_sha256").isNull(), "Absent after needs an explicit absent SHA"); if (!origin.has("capture_stage")) incomplete++;
            } else {
                Path afterPath = incidentRoot.resolve(id + ".after.json"); ExactRef after = stage(row, "after", afterPath, supplied, originals); used.put(afterPath, after);
                ExactRef afterIndexRef = originals.get(incidentRoot.resolve(id + ".after-index.json"));
                require(afterIndexRef != null, "Actual after body lacks its original producer index");
                ObjectNode afterIndex = json(read(incidentRoot, afterIndexRef)); sameEpisode(actual, afterIndex);
                String afterSchema=text(afterIndex,"schema");boolean version2="xar.episode-incident-after-index/v2".equals(afterSchema);
                require((version2?afterIndex.has("policy_receipt_input")&&(afterIndex.get("policy_receipt_input").isNull()||afterIndex.get("policy_receipt_input").isObject()):"xar.episode-incident-after-index/v1".equals(afterSchema)&&!afterIndex.has("policy_receipt_input")) && id.equals(text(afterIndex, "incident_id"))
                        && before.equals(ExactRef.fromJson(afterIndex.get("before_ref"))) && after.equals(ExactRef.fromJson(afterIndex.get("after_ref"))), "Actual after index crossed its original before/after source");
            }
        }
        require(used.equals(supplied), "Captured inventory must be exactly the actual batch's before/after originals");
        require(StrictJson.integer(index.get("incomplete_after"), 0, 1026) >= incomplete, "Actual scan lost incomplete-after diagnostics");
        read(scans, actual.indexRef()); read(scans, manifest);
        return new Loaded(binding, raw, originals.entrySet().stream().filter(entry -> !external.containsKey(entry.getKey())).map(Map.Entry::getValue).toList(), List.copyOf(external.values()));
    }

    public static void recheck(Path incidentRoot, Optional<Path> scanRoot, ExactRef manifest, Loaded original) throws IOException {
        Path root = original.binding() instanceof ObservedScan ? scanRoot.orElseThrow() : incidentRoot;
        if (original.binding() instanceof ObservedScan actual && !absolute(manifest.path()).getParent().equals(root)) {
            var scope = IncidentJournalLayout.scope(incidentRoot, root, actual.observation().machineId(), actual.observation().game(), actual.sessionId(), actual.observation().frame().episodeRunId(), actual.source().sourceRef());
            require(absolute(manifest.path()).getParent().equals(scope.scanRoot()), "Rechecked scan escaped its derived identity"); incidentRoot = scope.incidentRoot(); root = scope.scanRoot();
        }
        for (ExactRef ref : original.scanOriginals()) read(incidentRoot, ref);
        for (ExternalOriginal ref : original.externalOriginals()) verifyExternal(ref.source(), ref.maximumBytes());
        if (original.binding() instanceof ObservedScan actual) read(root, actual.indexRef());
        if (original.binding() instanceof ObservedScan actual) verifySource(actual.source().sourceRef());
        byte[] actual = read(root, manifest); require(java.util.Arrays.equals(actual, original.manifestBytes()), "Original manifest changed during source review");
    }
    private static ExactRef stage(ObjectNode row, String name, Path expected, Map<Path, ExactRef> supplied, Map<Path, ExactRef> actual) {
        require(expected.equals(absolute(text(row, name))), "Actual incident source path differs");
        ExactRef ref = supplied.get(expected); require(ref != null && ref.equals(actual.get(expected)) && ref.sha256().equals(text(row, name + "_sha256")), "Actual incident pin differs from scan/capture inventory"); return ref;
    }
    /** The journal's internal G2 actor is canonical signed decimal text. Only a V3 manifest
     * requests this explicit memory-domain projection; public NativeCharacterId never accepts strings. */
    private static OfflineBatchBinding.Observation journalObservation(ObservedScan scan,JsonNode original){
        if(!(scan.observation().frame().playedCharacterId() instanceof OfflineBatchBinding.NativeObservedActor))return OfflineBatchBinding.observation(original);
        ObjectNode projected=object(original).deepCopy();ObjectNode frame=object(projected.get("frame"));JsonNode raw=frame.get("played_character_id");
        require(raw!=null&&raw.isTextual()&&raw.textValue().length()<=11&&raw.textValue().matches("-?(?:0|[1-9][0-9]*)"),"V3 journal actor must retain its original canonical internal decimal token");
        java.math.BigInteger exact=new java.math.BigInteger(raw.textValue());require(exact.toString().equals(raw.textValue()),"V3 journal signed actor decimal is not canonical");
        frame.set("played_character_id",NativeCharacterId.of(exact).toJson());return OfflineBatchBinding.nativeObservation(projected);
    }
    private static void sameEpisode(ObservedScan scan, ObjectNode value) {
        var observation = journalObservation(scan,value.get("origin"));
        require(scan.observation().machineId().equals(observation.machineId()) && scan.observation().game().equals(observation.game())
                && scan.observation().frame().episodeRunId().equals(observation.frame().episodeRunId())
                && scan.source().equals(OfflineBatchBinding.source(value.get("source"))) && scan.sessionId().equals(text(value, "session_id")), "Journal original crossed physical Game, source, session or episode");
    }
    private static byte[] read(Path root, ExactRef ref) throws IOException {
        Path path = absolute(ref.path()); require(path.startsWith(root) && !path.equals(root) && ref.bytes() > 0 && ref.bytes() <= FILE_MAX, "Original source escapes its fixed journal role");
        byte[] raw = EvidenceGrantManifestPublisher.readStable(path, FILE_MAX);
        require(raw.length == ref.bytes() && SourceReviewJson.sha(raw).equals(ref.sha256()), "Actual journal source bytes or SHA changed"); return raw;
    }
    private static ObjectNode json(byte[] raw) { return object(StrictJson.parse(ProjectionJson.object(raw, FILE_MAX).bytes(), FILE_MAX)); }
    private static void verifySource(ExactRef ref) throws IOException {
        verifyExternal(ref, 64L << 20);
    }
    private static void declareExternal(Map<Path, ExactRef> originals, Map<Path, ExternalOriginal> external, ExactRef ref, long maximum) {
        Path path = absolute(ref.path()); require(ref.equals(originals.get(path)), "Declared external original is missing from the complete scan inventory");
        ExternalOriginal old = external.putIfAbsent(path, new ExternalOriginal(ref, maximum));
        require(old == null || old.source().equals(ref), "Conflicting declared external original");
        if (old != null && maximum < old.maximumBytes()) external.put(path, new ExternalOriginal(ref, maximum));
    }
    private static void verifyExternal(ExactRef ref, long maximum) throws IOException {
        Path path = absolute(ref.path()); require(ref.bytes() > 0 && ref.bytes() <= maximum, "Finite declared external original bound required");
        for (Path part = path; part != null; part = part.getParent()) require(!Files.isSymbolicLink(part), "Original external source cannot traverse a link");
        require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && path.toRealPath().equals(path), "Plain canonical external original required");
        var before = Files.readAttributes(path, java.nio.file.attribute.BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256"); long count = 0;
            try (var input = Files.newInputStream(path)) { byte[] buffer = new byte[65536]; for (int n; (n = input.read(buffer)) != -1;) { count = Math.addExact(count, n); require(count <= maximum, "External original grew beyond its role bound"); digest.update(buffer, 0, n); } }
            var after = Files.readAttributes(path, java.nio.file.attribute.BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            require(count == ref.bytes() && before.size() == count && after.size() == count && java.util.Objects.equals(before.fileKey(), after.fileKey())
                    && before.lastModifiedTime().equals(after.lastModifiedTime()) && java.util.HexFormat.of().formatHex(digest.digest()).equals(ref.sha256()), "Actual external original changed identity, bytes or SHA");
        } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private static ObjectNode object(JsonNode value) { require(value instanceof ObjectNode, "Actual journal JSON object required"); return (ObjectNode)value; }
    private static Path absolute(String value) { Path path = Path.of(value); require(path.isAbsolute() && path.equals(path.normalize()), "Canonical absolute journal path required"); return path; }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static void require(boolean value, String message) { StrictJson.require(value, message); }
}
