package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** One empirical recovery rule shared by offline analysis, knowledge lookup and the live planner. */
public final class UiRecoveryEvidenceLookup {
    public static final int FILE_LIMIT = 1_048_576;
    public static final int WIRE_LIMIT = 65_536;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private final EventSourceReadContext configured;
    private final TrustedEventSourceContext reader;
    private final Path stateRoot;
    private final Path attemptRoot;

    public UiRecoveryEvidenceLookup(EventSourceReadContext configured) {
        this.configured = Objects.requireNonNull(configured);
        reader = TrustedEventSourceContext.openEvidence(configured);
        stateRoot = configured.stateRoot(); attemptRoot = Objects.requireNonNull(stateRoot.getParent());
    }


    /** Same Root adapter supplies the real reviewed Native backend pin, rather than a legacy launch pathname. */
    public Optional<EvidenceDocument> lookupRoot(JsonNode dto,BigInteger currentPid,ExactRef backend) {
        Objects.requireNonNull(backend);
        if(currentPid==null||!currentPid.equals(integer(dto==null?null:dto.path("frame_binding").get("game_pid"))))return Optional.empty();
        Path root=stateRoot.resolve("evidence/unknown-mandatory-choice-reviews/root-known-ui-recovery");
        if(absentKnowledge(root))return Optional.empty();
        Optional<ObjectNode> identity=fingerprint(dto,backend.sha256());if(identity.isEmpty())return Optional.empty();
        try{OfflineMandatoryChoiceReviewProducer.rootVerify(backend,64L<<20);}
        catch(IOException changed){throw new UncheckedIOException("actual current Root Native backend source unavailable",changed);}
        for(Path path:reviews(root.resolve(text(identity.orElseThrow().get("source_key"))))) {
            try {
                ObjectNode fact=object(parse(reader.readState(path,FILE_LIMIT),FILE_LIMIT));
                if(!OfflineMandatoryChoiceReviewProducer.ROOT_REVIEW_SCHEMA.equals(text(fact.get("schema")))
                        ||!same(identity.orElseThrow().get("source_key"),fact.get("source_key"))
                        ||!same(identity.orElseThrow().get("stable_source"),fact.get("stable_source")))continue;
                var input=new OfflineMandatoryChoiceReviewProducer.RootInputs(ExactRef.fromJson(fact.get("before_ref")),
                        ExactRef.fromJson(fact.get("after_ref")),ExactRef.fromJson(fact.get("scan_index_ref")));
                var checked=OfflineMandatoryChoiceReviewProducer.reviewRoot(input,text(fact.get("machine_id")));
                if(!fact.equals(checked.fact()))continue;
                for(var source:checked.sources())require(reader.declaredGrant(source.path(),source.role()).equals(source),
                        "Root recovery knowledge original grant/source machine differs");
                ObjectNode result=JSON.createObjectNode().put("known_recovery_source","observed-UI")
                        .put("review_path",path.toString()).put("business_effect_known",false).put("semantic_optimal",false)
                        .put("game_date_progress_verified",true);
                result.set("source_key",fact.get("source_key"));result.set("observed_choice_id",fact.get("selected_choice_id"));
                return Optional.of(document(result,WIRE_LIMIT));
            }catch(IOException|IllegalArgumentException invalid){ /* Changed readable originals stay unknown; no token/effect authority is renewed. */ }
        }
        return Optional.empty();
    }

    /** The expected hash is only a claim. The launch grant supplies the actual backend and current PID. */
    public Optional<EvidenceDocument> lookup(JsonNode dto, BigInteger expectedPid, String expectedBackend) {
        // A first unseen modal has no knowledge to requalify. Only a proved absent
        // fixed directory takes this path; permissions and identity drift remain unknown.
        if (absentKnowledge(stateRoot.resolve("evidence/unknown-mandatory-choice-reviews/known-ui-recovery"))) return Optional.empty();
        Path launchPath = attemptRoot.resolve("ROOT-ACTUAL-GAME-LAUNCH.json");
        if(configured.evidenceGrants().stream().noneMatch(grant->grant.path().equals(launchPath)&&grant.role()==ProjectionEvidenceRole.UI_RECOVERY_LAUNCH))return Optional.empty();
        available(configured.machineId().equals(reader.declaredGrant(launchPath, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH).originMachineId()),
                "current UI launch grant must bind the actual machine");
        ObjectNode launch = declared(launchPath, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH);
        available(configured.machineId().equals(text(launch.get("machine_id"))), "current UI launch machine differs");
        BigInteger currentPid = integer(launch.get("pid"));
        if (currentPid == null || currentPid.signum() <= 0 || expectedPid != null && !currentPid.equals(expectedPid)) return Optional.empty();
        String backend = digest(launch.get("dll_sha256"));
        if (backend == null || expectedBackend != null && !backend.equals(expectedBackend.toLowerCase(Locale.ROOT))) return Optional.empty();
        Optional<ObjectNode> source = fingerprint(dto, backend); if (source.isEmpty()) return Optional.empty();
        ObjectNode identity = source.orElseThrow();
        Path directory = stateRoot.resolve("evidence/unknown-mandatory-choice-reviews/known-ui-recovery")
                .resolve(text(identity.get("source_key")));
        for (Path reviewPath : reviews(directory)) {
            try {
                ObjectNode review = object(parse(reader.readState(reviewPath, FILE_LIMIT), FILE_LIMIT));
                if (!"known_ui_recovery_observed".equals(text(review.get("status"))) || !"observed-UI".equals(text(review.get("known_recovery_source")))
                        || !no(review.get("business_effect_known")) || !no(review.get("semantic_optimal"))
                        || !identity.get("source_key").equals(review.get("source_key")) || !identity.get("stable_source").equals(review.get("stable_source"))) continue;
                Path beforePath = path(review.get("before_path")), afterPath = path(review.get("after_path"));
                Path incidentDirectory = beforePath.getParent();
                if (incidentDirectory == null || incidentDirectory.getParent() == null || incidentDirectory.getParent().getParent() == null
                        || !incidentDirectory.getFileName().toString().equals("unknown-mandatory-choices")
                        || !incidentDirectory.getParent().getFileName().toString().equals("evidence")
                        || !incidentDirectory.getParent().getParent().getFileName().toString().equals("state")
                        || !incidentDirectory.equals(afterPath.getParent())
                        || !beforePath.getFileName().toString().endsWith(".before.json") || !afterPath.getFileName().toString().endsWith(".after.json")) continue;
                Path historical = incidentDirectory.getParent().getParent().getParent(); if (historical == null) continue;
                Path historicalLaunchPath = historical.resolve("ROOT-ACTUAL-GAME-LAUNCH.json");
                ObjectNode historicalLaunch = declared(historicalLaunchPath, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH);
                if (!backend.equals(digest(historicalLaunch.get("dll_sha256")))) continue;
                String origin = reader.declaredGrant(historicalLaunchPath, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH).originMachineId();
                if (!"unknown".equals(origin) && !origin.equals(text(historicalLaunch.get("machine_id")))) continue;
                require(origin.equals(reader.declaredGrant(beforePath, ProjectionEvidenceRole.UI_RECOVERY_BEFORE).originMachineId())
                        && origin.equals(reader.declaredGrant(afterPath, ProjectionEvidenceRole.UI_RECOVERY_AFTER).originMachineId()), "historical UI evidence source machine differs");
                ObjectNode before = checked(beforePath, review.get("before_sha256"), ProjectionEvidenceRole.UI_RECOVERY_BEFORE);
                ObjectNode after = checked(afterPath, review.get("after_sha256"), ProjectionEvidenceRole.UI_RECOVERY_AFTER);
                BigInteger historicalPid = integer(historicalLaunch.get("pid"));
                if (historicalPid == null || historicalPid.signum() <= 0 || !historicalPid.equals(integer(before.path("frame_binding").get("game_pid")))) continue;
                ObjectNode progress = JSON.createObjectNode(); progress.set("source_path", review.get("later_source_path"));
                progress.set("source_sha256", review.get("later_source_sha256")); progress.putArray("json_pointer").add("result").add("structured_content");
                progress.put("game_launch_receipt_path", historicalLaunchPath.toString());
                progress.put("game_launch_receipt_sha256", reader.declaredGrant(historicalLaunchPath, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH).sha256());
                Path laterPath = path(progress.get("source_path"));
                require(origin.equals(reader.declaredGrant(laterPath, ProjectionEvidenceRole.UI_RECOVERY_LATER).originMachineId()), "later UI evidence source machine differs");
                ObjectNode checked = analyzeNode(before, after, backend, progress);
                if (!"known_ui_recovery_observed".equals(text(checked.get("status")))
                        || !same(checked.get("source_key"), identity.get("source_key"))
                        || !same(checked.get("stable_source"), identity.get("stable_source"))
                        || !same(checked.get("selected_choice_id"), review.get("selected_choice_id"))) continue;
                ObjectNode result = JSON.createObjectNode(); result.put("known_recovery_source", "observed-UI");
                result.set("source_key", identity.get("source_key")); result.put("review_path", reviewPath.toString());
                result.set("observed_choice_id", checked.get("selected_choice_id")); result.put("business_effect_known", false); result.put("semantic_optimal", false);
                return Optional.of(document(result, WIRE_LIMIT));
            } catch (IllegalArgumentException invalid) { /* Readable invalid historical knowledge remains unknown. */ }
        }
        return Optional.empty();
    }

    public String boundBackend(JsonNode snapshot) {
        BigInteger pid = integer(snapshot == null ? null : snapshot.path("diagnostics").get("bridge_pid"));
        if (pid == null || pid.signum() <= 0) return null;
        Path launchPath = attemptRoot.resolve("ROOT-ACTUAL-GAME-LAUNCH.json");
        available(configured.machineId().equals(reader.declaredGrant(launchPath, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH).originMachineId()), "current launch source machine differs");
        ObjectNode launch = declared(launchPath, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH);
        if (!configured.machineId().equals(text(launch.get("machine_id"))) || !pid.equals(integer(launch.get("pid")))) return null;
        return digest(launch.get("dll_sha256"));
    }

    /** A pure candidate fact. Publication separately re-reads original completed pair files. */
    public EvidenceDocument analyze(JsonNode before, JsonNode after, String expectedBackend, JsonNode progress) {
        return document(analyzeNode(before, after, expectedBackend, progress), FILE_LIMIT);
    }

    ObjectNode analyzeNode(JsonNode before, JsonNode after, String backend, JsonNode progress) {
        ObjectNode result = JSON.createObjectNode(); result.put("status", "unresolved"); result.putNull("known_recovery_source");
        result.put("business_effect_known", false); result.put("semantic_optimal", false); result.put("reason", "incomplete_evidence");
        if (!(before instanceof ObjectNode) || !(after instanceof ObjectNode) || !same(before.get("incident_id"), after.get("incident_id"))) return reason(result, "incident_pair_mismatch");
        JsonNode dto = before.get("native_window"), frame = before.get("frame_binding"), selection = before.get("selection");
        if (!(dto instanceof ObjectNode) || !(frame instanceof ObjectNode) || !(selection instanceof ObjectNode)) return reason(result, "original_window_or_binding_missing");
        Optional<ObjectNode> source = fingerprint(dto, backend);
        if (source.isEmpty()) return reason(result, "stable_build_widget_callback_source_unavailable");
        result.setAll(source.orElseThrow());
        if (!disappearance(before, after)) return reason(result, "original_window_disappearance_unverified");
        ObjectNode later = progressFrame(progress);
        if (later == null || !sameProgress(frame, later)) return reason(result, "later_same_game_date_progress_unverified");
        if (after.path("captured_at_utc").isTextual() && later.path("_source_ended_at_utc").isTextual()
                && later.path("_source_ended_at_utc").textValue().compareTo(after.path("captured_at_utc").textValue()) <= 0) return reason(result, "later_response_precedes_original_selection");
        result.remove("reason"); result.put("status", "known_ui_recovery_observed"); result.put("known_recovery_source", "observed-UI");
        result.set("incident_id", before.get("incident_id")); result.set("selected_choice_id", selection.get("choice_id"));
        result.set("original_window_instance", dto.get("window_instance_id")); result.set("date_raw_before", frame.get("date_raw"));
        result.set("date_raw_after", later.get("date_raw")); result.set("later_source_path", progress.get("source_path")); result.set("later_source_sha256", progress.get("source_sha256"));
        return result;
    }

    ObjectNode progressFrame(JsonNode progress) {
        if (!(progress instanceof ObjectNode) || digest(progress.get("source_sha256")) == null) return null;
        String sourceName = text(progress.get("source_path")); if (sourceName == null) return null;
        Path sourcePath = path(progress.get("source_path")); if (sourcePath.getFileName().toString().equals("driver-state.json")) return null;
        JsonNode pointer = progress.get("json_pointer"); if (pointer == null || !pointer.isArray()) return null;
        byte[] sourceRaw = reader.readDeclared(sourcePath, FILE_LIMIT, ProjectionEvidenceRole.UI_RECOVERY_LATER);
        if (!sha(sourceRaw).equals(digest(progress.get("source_sha256")))) return null;
        JsonNode sourceNode = parse(sourceRaw, FILE_LIMIT); if (!(sourceNode instanceof ObjectNode source)) return null;
        JsonNode value = source;
        for (JsonNode key : pointer) { if (!key.isTextual() || !value.isObject() || !value.has(key.textValue())) return null; value = value.get(key.textValue()); }
        if (!(value instanceof ObjectNode)) return null;
        ObjectNode frame = ((ObjectNode) value).deepCopy();
        if (!frame.has("game_pid")) {
            if (digest(progress.get("game_launch_receipt_sha256")) == null || text(progress.get("game_launch_receipt_path")) == null) return null;
            Path launchPath = path(progress.get("game_launch_receipt_path")); if (!sourcePath.startsWith(launchPath.getParent())) return null;
            require(reader.declaredGrant(sourcePath, ProjectionEvidenceRole.UI_RECOVERY_LATER).originMachineId()
                    .equals(reader.declaredGrant(launchPath, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH).originMachineId()), "later progress/launch source machines differ");
            byte[] launchRaw = reader.readDeclared(launchPath, FILE_LIMIT, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH);
            if (!sha(launchRaw).equals(digest(progress.get("game_launch_receipt_sha256")))) return null;
            ObjectNode launch = object(parse(launchRaw, FILE_LIMIT));
            if (integer(launch.get("pid")) == null) return null; frame.set("game_pid", launch.get("pid"));
        }
        frame.set("_source_ended_at_utc", source.get("ended_at_utc")); return frame;
    }

    static boolean disappearance(JsonNode before, JsonNode after) {
        JsonNode receipt = after.path("action_receipt"), post = receipt.path("mandatory_choice_postcondition");
        return yes(after.get("original_blocking_window_advanced_verified")) && yes(receipt.get("accepted")) && yes(post.get("verified"))
                && same(post.get("old_window_id"), before.path("native_window").get("window_id"))
                && same(post.get("old_instance"), before.path("native_window").get("window_instance_id"))
                && same(post.get("selected_choice_id"), before.path("selection").get("choice_id")) && yes(post.get("old_window_no_longer_blocking"));
    }
    static boolean sameProgress(JsonNode frame, JsonNode later) {
        for (String key : List.of("game_pid", "connection_generation", "actor_character_id")) {
            BigInteger first = integer(frame.get(key)); if (first == null || !first.equals(integer(later.get(key)))) return false;
        }
        return same(frame.get("episode_run_id"), later.get("episode_run_id")) && increasing(frame.get("date_raw"), later.get("date_raw"))
                && increasing(frame.get("native_revision"), later.get("native_revision"));
    }
    static Optional<ObjectNode> fingerprint(JsonNode dto, String backend) {
        ObjectNode request = JSON.createObjectNode(); request.put("schema", UiRecoveryIdentityJson.SCHEMA); request.set("window", dto);
        if (backend == null) request.putNull("backend_sha256"); else request.put("backend_sha256", backend);
        JsonNode value = parse(UiRecoveryIdentityJson.fingerprint(encode(request, WIRE_LIMIT)), WIRE_LIMIT);
        return value instanceof ObjectNode result ? Optional.of(result) : Optional.empty();
    }
    private List<Path> reviews(Path directory) {
        if (absentKnowledge(directory)) return List.of();
        require(directory.startsWith(stateRoot), "UI review root escape"); List<Path> result = new ArrayList<>(); int count = 0;
        try {
            require(directory.toRealPath().equals(directory), "UI review directory alias");
            try (var paths = Files.newDirectoryStream(directory)) { for (Path item : paths) {
                require(++count <= 1024, "bounded UI review directory required");
                if (item.getFileName().toString().endsWith(".json")) result.add(item);
                require(result.size() <= 128, "bounded UI reviews required");
            } }
        } catch (IOException error) { throw new UncheckedIOException("UI review directory unavailable", error); }
        result.sort(Comparator.comparing(Path::toString)); return List.copyOf(result);
    }
    private boolean absentKnowledge(Path directory) {
        require(directory.startsWith(stateRoot), "UI knowledge directory escapes its fixed root");
        try {
            BasicFileAttributes original = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(stateRoot);
            available(original.isDirectory() && original.fileKey() != null && !original.isSymbolicLink() && stateRoot.toRealPath().equals(stateRoot), "identity-bearing UI state root required");
            Path cursor = stateRoot;
            for (Path part : stateRoot.relativize(directory)) {
                cursor = cursor.resolve(part);
                try {
                    BasicFileAttributes current = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(cursor);
                    available(current.isDirectory() && current.fileKey() != null && !current.isSymbolicLink() && cursor.toRealPath().equals(cursor), "UI knowledge directory alias or type changed");
                } catch (NoSuchFileException absent) {
                    available(original.fileKey().equals(org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(stateRoot).fileKey()), "UI state root changed during absence check");
                    return true;
                }
            }
            available(original.fileKey().equals(org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(stateRoot).fileKey()), "UI state root changed during knowledge check");
            return false;
        } catch (IOException error) { throw new UncheckedIOException("UI knowledge directory availability unknown", error); }
    }
    private ObjectNode declared(Path path, ProjectionEvidenceRole role) { return object(parse(reader.readDeclared(path, FILE_LIMIT, role), FILE_LIMIT)); }
    private ObjectNode checked(Path path, JsonNode expected, ProjectionEvidenceRole role) {
        byte[] raw = reader.readDeclared(path, FILE_LIMIT, role); require(sha(raw).equals(digest(expected)), "review original source SHA drift"); return object(parse(raw, FILE_LIMIT));
    }
    static ObjectNode reason(ObjectNode result, String reason) { result.put("reason", reason); return result; }
    static EvidenceDocument document(JsonNode node, int maximum) { return new EvidenceDocument(new String(encode(node, maximum), StandardCharsets.UTF_8)); }
    static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "UI evidence object required"); return (ObjectNode) node; }
    static JsonNode parse(byte[] raw, int maximum) {
        require(raw != null && raw.length > 0 && raw.length <= maximum, "bounded UI JSON required"); RetainedJson.parse(raw);
        try { JsonNode result = JSON.readTree(raw); require(result != null, "UI JSON value required"); return result; }
        catch (IOException error) { throw new IllegalArgumentException("invalid UI JSON", error); }
    }
    static byte[] encode(JsonNode node, int maximum) {
        try { byte[] raw = JSON.writeValueAsBytes(node); require(raw.length <= maximum, "bounded UI JSON output required"); return raw; }
        catch (IOException error) { throw new IllegalArgumentException("UI JSON encoding failed", error); }
    }
    static String text(JsonNode node) { return node != null && node.isTextual() && !node.textValue().isEmpty() ? node.textValue() : null; }
    static String digest(JsonNode node) { String value = text(node); return value != null && value.matches("[a-fA-F0-9]{64}") ? value.toLowerCase(Locale.ROOT) : null; }
    static Path path(JsonNode node) { String value = text(node); require(value != null, "original absolute UI evidence path required"); Path path = Path.of(value); require(path.isAbsolute(), "absolute UI evidence path required"); return path.normalize(); }
    static BigInteger integer(JsonNode node) { return node != null && node.isIntegralNumber() ? node.bigIntegerValue() : null; }
    static boolean same(JsonNode first, JsonNode second) { return Objects.equals(first, second); }
    static boolean yes(JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
    static boolean no(JsonNode node) { return node != null && node.isBoolean() && !node.booleanValue(); }
    static boolean increasing(JsonNode old, JsonNode next) { BigInteger a = integer(old), b = integer(next); return a != null && b != null && b.compareTo(a) > 0; }
    static String sha(byte[] raw) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); } }
    static void require(boolean condition, String reason) { if (!condition) throw new IllegalArgumentException(reason); }
    private static void available(boolean condition, String reason) { if (!condition) throw new IllegalStateException(reason); }
}

