package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import static org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoveryEvidenceLookup.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import java.math.BigInteger;
import java.util.Optional;
import java.util.Set;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Actual offline worker body. The qualified offline dispatcher supplies its fixed configuration. */
public final class OfflineMandatoryChoiceReviewProducer {
    private static final String INCIDENT_SCHEMA = "xar.unknown-mandatory-choice-incident/v1";
    private static final String REVIEW_SCHEMA = "xar.unknown-mandatory-choice-offline-review/v1";
    private static final String REVIEW_DIRECTORY = "evidence/unknown-mandatory-choice-reviews";
    private OfflineMandatoryChoiceReviewProducer() { }
    public static final class SourceChangedException extends IOException {
        private static final long serialVersionUID = 1L;
        public SourceChangedException(String message) { super(message); }
    }
    public static final class SourceUnavailableException extends IOException {
        private static final long serialVersionUID = 1L;
        public SourceUnavailableException(String message, IOException cause) { super(message, cause); }
    }
    public static final class PublicationException extends IOException {
        private static final long serialVersionUID = 1L;
        public PublicationException(String message, IOException cause) { super(message, cause); }
    }
    public record Configuration(EventSourceReadContext sources, Path reviewRoot, Path grantsManifest, Path incidentAttempt) {
        public Configuration(EventSourceReadContext sources, Path reviewRoot, Path grantsManifest) {
            this(sources, reviewRoot, grantsManifest, Objects.requireNonNull(sources.stateRoot().getParent()));
        }
        public Configuration {
            Objects.requireNonNull(sources); reviewRoot = fixed(reviewRoot); grantsManifest = fixed(grantsManifest); incidentAttempt = fixed(incidentAttempt);
            require(reviewRoot.equals(sources.stateRoot().resolve(REVIEW_DIRECTORY)), "offline UI review output must match the shared live knowledge root");
            require(!grantsManifest.startsWith(sources.stockGameRoot()), "offline grant publication cannot write stock source roots");
            require(!incidentAttempt.startsWith(sources.stockGameRoot()), "offline incident input cannot use installed stock source roots");
        }
    }
    public record ReviewSummary(String incidentId, String status, Path review, int bytes, String sha256) { }
    public record SourcePin(Path path, long bytes, String sha256) {
        public SourcePin { path = fixed(path); require(bytes > 0 && bytes <= FILE_LIMIT && sha256 != null && sha256.matches("[a-f0-9]{64}"), "bounded exact captured UI input required"); }
    }
    public record CapturedInputs(Path incidentAttempt, List<SourcePin> sources) {
        public CapturedInputs {
            incidentAttempt = fixed(incidentAttempt); sources = List.copyOf(sources);
            require(sources.size() <= 4609 && sources.stream().map(SourcePin::path).distinct().count() == sources.size(), "bounded unique captured UI source inventory required");
            for (SourcePin pin : sources) {
                Path path = pin.path(); String name = path.getFileName().toString();
                boolean launch = path.equals(incidentAttempt.resolve("ROOT-ACTUAL-GAME-LAUNCH.json"));
                boolean pair = path.getParent().equals(incidentAttempt.resolve("state/evidence/unknown-mandatory-choices")) && (name.endsWith(".before.json") || name.endsWith(".after.json"));
                boolean response = path.getParent().getParent() != null && path.getParent().getParent().equals(incidentAttempt)
                        && path.getParent().getFileName().toString().matches("p.*-responses") && name.endsWith("-result.json");
                require(launch || pair || response, "captured UI file is outside its exact original role layout");
            }
        }
    }
    public record Result(List<ReviewSummary> reviews, EvidenceGrantManifestPublisher.Publication grants, List<SourcePin> sources) {
        public Result { reviews = List.copyOf(reviews); Objects.requireNonNull(grants); sources = List.copyOf(sources); }
    }
    private record Original(Path path, byte[] bytes, ObjectNode value, ProjectionEvidenceGrant grant) { }
    private record Prior(ObjectNode review, ObjectNode progress) { }

    public static Result reviewOnce(Configuration configured) throws IOException {
        Path anchor = configured.incidentAttempt().resolve("ROOT-ACTUAL-GAME-LAUNCH.json");
        byte[] raw = readWithin(configured.incidentAttempt(), anchor);
        return reviewCaptured(configured, captureInputs(configured, new SourcePin(anchor, raw.length, sha(raw))));
    }

    /** The dispatcher has already admitted this exact historical/current launch anchor. */
    public static CapturedInputs captureInputs(Configuration configured, SourcePin launchAnchor) throws IOException {
        Path attempt = configured.incidentAttempt();
        require(launchAnchor.path().equals(attempt.resolve("ROOT-ACTUAL-GAME-LAUNCH.json")), "captured UI launch anchor differs from configured source attempt");
        verifyPin(attempt, launchAnchor); List<SourcePin> pins = new ArrayList<>(); pins.add(launchAnchor);
        for (Path before : files(attempt.resolve("state/evidence/unknown-mandatory-choices"), ".before.json", 256)) {
            String name = before.getFileName().toString(); Path after = before.resolveSibling(name.substring(0, name.length() - ".before.json".length()) + ".after.json");
            if (!regularPresent(after)) continue;
            for (Path path : List.of(before, after)) { byte[] raw = readWithin(attempt, path); pins.add(new SourcePin(path, raw.length, sha(raw))); }
        }
        for (Path path : responseFiles(attempt)) { byte[] raw = readWithin(attempt, path); pins.add(new SourcePin(path, raw.length, sha(raw))); }
        CapturedInputs captured = new CapturedInputs(attempt, pins);
        for (SourcePin pin : captured.sources()) verifyPin(attempt, pin);
        return captured;
    }

    /** New response files are left for the next batch; every opened captured file is rechecked. */
    public static Result reviewCaptured(Configuration configured, CapturedInputs captured) throws IOException {
        return EvidenceGrantManifestPublisher.transaction(configured.grantsManifest(), writer -> reviewUnderLock(configured, captured, writer));
    }

    private static Result reviewUnderLock(Configuration configured, CapturedInputs captured, EvidenceGrantManifestPublisher.Writer writer) throws IOException {
        require(configured.incidentAttempt().equals(captured.incidentAttempt()), "captured UI batch crossed its configured attempt");
        for (SourcePin pin : captured.sources()) verifyPin(captured.incidentAttempt(), pin);
        Path attempt = configured.incidentAttempt();
        Path incidents = attempt.resolve("state/evidence/unknown-mandatory-choices");
        byte[] launchRaw = readWithin(attempt, attempt.resolve("ROOT-ACTUAL-GAME-LAUNCH.json"));
        ObjectNode launch = object(parse(launchRaw, FILE_LIMIT));
        String backend = digest(launch.get("dll_sha256"));
        ProjectionEvidenceGrant admittedLaunch = configured.sources().evidenceGrants().stream()
                .filter(grant -> grant.path().equals(attempt.resolve("ROOT-ACTUAL-GAME-LAUNCH.json")) && grant.role() == ProjectionEvidenceRole.UI_RECOVERY_LAUNCH).findFirst().orElse(null);
        String origin = admittedLaunch == null ? "unknown" : admittedLaunch.originMachineId();
        if (admittedLaunch != null) require(admittedLaunch.bytes() == launchRaw.length && admittedLaunch.sha256().equals(sha(launchRaw)), "admitted original UI launch SHA drift");
        ProjectionEvidenceGrant launchGrant = new ProjectionEvidenceGrant(attempt.resolve("ROOT-ACTUAL-GAME-LAUNCH.json"), launchRaw.length,
                sha(launchRaw), origin, ProjectionEvidenceRole.UI_RECOVERY_LAUNCH);
        List<ProjectionEvidenceGrant> additions = new ArrayList<>(); additions.add(launchGrant);
        List<ReviewSummary> results = new ArrayList<>();
        List<Path> laterPaths = captured.sources().stream().map(SourcePin::path).filter(path -> path.getFileName().toString().endsWith("-result.json")
                && path.getParent().getParent().equals(attempt) && path.getParent().getFileName().toString().matches("p.*-responses")).sorted(Comparator.comparing(Path::toString)).toList();
        List<Path> beforePaths = captured.sources().stream().map(SourcePin::path).filter(path -> path.getParent().equals(incidents)
                && path.getFileName().toString().endsWith(".before.json")).sorted(Comparator.comparing(Path::toString)).toList();
        require(beforePaths.size() <= 256 && laterPaths.size() <= 4096, "captured UI cohort exceeds original role bounds");
        require(captured.sources().stream().anyMatch(pin -> pin.path().equals(attempt.resolve("ROOT-ACTUAL-GAME-LAUNCH.json"))), "captured UI batch lacks its own launch");
        for (Path beforePath : beforePaths) {
            String incident = beforePath.getFileName().toString().replaceFirst("\\.before\\.json$", "");
            require(incident.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"), "bounded original UI incident identity required");
            Path afterPath = beforePath.resolveSibling(incident + ".after.json");
            require(captured.sources().stream().anyMatch(pin -> pin.path().equals(afterPath)), "captured UI completed pair lacks exact after input");
            Original before = original(attempt, beforePath, origin, ProjectionEvidenceRole.UI_RECOVERY_BEFORE);
            Original after = original(attempt, afterPath, origin, ProjectionEvidenceRole.UI_RECOVERY_AFTER);
            require(INCIDENT_SCHEMA.equals(text(before.value().get("schema"))) && INCIDENT_SCHEMA.equals(text(after.value().get("schema")))
                    && incident.equals(text(before.value().get("incident_id"))) && incident.equals(text(after.value().get("incident_id")))
                    && before.grant().sha256().equals(digest(after.value().path("before").get("sha256"))), "mandatory-choice incident pair identity changed");
            additions.add(before.grant()); additions.add(after.grant());
            Prior prior = priorReview(configured, before, after, backend, launchGrant, origin, additions);
            ObjectNode progress = prior == null ? null : prior.progress();
            if (prior == null && yes(after.value().get("original_blocking_window_advanced_verified")) && fingerprint(before.value().get("native_window"), backend).isPresent()) {
                progress = laterProgress(attempt, before.value(), after.value(), launch, launchGrant, origin, laterPaths, additions);
            }
            EventSourceReadContext snapshot = new EventSourceReadContext(configured.sources().machineId(), configured.sources().stateRoot(),
                    configured.sources().stockGameRoot(), merge(configured.sources().evidenceGrants(), additions));
            ObjectNode review = prior == null ? new UiRecoveryEvidenceLookup(snapshot).analyzeNode(before.value(), after.value(), backend, progress) : prior.review();
            review.put("schema", REVIEW_SCHEMA); review.put("incident_id", incident); review.put("before_path", beforePath.toString());
            review.put("before_sha256", before.grant().sha256()); review.put("after_path", afterPath.toString()); review.put("after_sha256", after.grant().sha256()); review.put("Game_MCP_OBS_calls", 0);
            String suffix = progress == null ? "no-progress" : Objects.requireNonNull(text(progress.get("source_sha256"))).substring(0, 12);
            Path target = configured.reviewRoot().resolve(incident + "." + suffix + ".review.json");
            byte[] output = pretty(review); writeOnce(configured.reviewRoot(), target, output);
            if ("known_ui_recovery_observed".equals(text(review.get("status")))) {
                // The publication uses the exact re-read incident/later/launch bytes, never a caller-known assertion.
                require(disappearance(before.value(), after.value()) && integer(launch.get("pid")) != null
                        && integer(launch.get("pid")).equals(integer(before.value().path("frame_binding").get("game_pid"))), "review cannot promote an incident from another game process");
                Path known = configured.reviewRoot().resolve("known-ui-recovery").resolve(Objects.requireNonNull(text(review.get("source_key")))).resolve(incident + ".json");
                writeOnce(configured.reviewRoot(), known, output);
            }
            // Re-read originals immediately before collecting exact grants for the common manifest lock.
            require(Arrays.equals(before.bytes(), readWithin(attempt, beforePath)) && Arrays.equals(after.bytes(), readWithin(attempt, afterPath)), "completed pair changed before publication");
            results.add(new ReviewSummary(incident, Objects.requireNonNull(text(review.get("status"))), target, output.length, sha(output)));
        }
        require(Arrays.equals(launchRaw, readWithin(attempt, launchGrant.path())), "own immutable launch changed before publication");
        for (SourcePin pin : captured.sources()) verifyPin(attempt, pin);
        EvidenceGrantManifestPublisher.Publication publication;
        try { publication = writer.publish(merge(List.of(), additions)); }
        catch (IOException error) { throw new PublicationException("offline UI grant publication unavailable", error); }
        return new Result(results, publication, captured.sources());
    }


    public static final String ROOT_INCIDENT_SCHEMA = "xar.root-mandatory-choice-incident/v1";
    public static final String ROOT_REVIEW_SCHEMA = "xar.root-mandatory-choice-offline-review/v1";
    /** The existing observed-scan cohort, never a copied Python launch or a caller-supplied known assertion. */
    public record RootInputs(ExactRef before, ExactRef after, ExactRef scanIndex) {
        public RootInputs { Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(scanIndex); }
    }
    public record RootReview(ObjectNode fact, List<ProjectionEvidenceGrant> sources) {
        public RootReview { fact=fact.deepCopy(); sources=List.copyOf(sources); }
        @Override public ObjectNode fact(){return fact.deepCopy();}
    }
    /** Domain analysis only; the existing batch analyzer owns the same knowledge writer and manifest transaction. */
    public static RootReview reviewRoot(RootInputs input, String machine) throws IOException {
        require(machine!=null&&machine.matches("[a-z0-9][a-z0-9-]{0,63}")&&!machine.equals("unknown"),"actual Root review machine required");
        List<ProjectionEvidenceGrant> grants=new ArrayList<>();
        ObjectNode before=rootObject(input.before(),FILE_LIMIT,machine,ProjectionEvidenceRole.UI_RECOVERY_BEFORE,grants);
        ObjectNode after=rootObject(input.after(),FILE_LIMIT,machine,ProjectionEvidenceRole.UI_RECOVERY_AFTER,grants);
        ObjectNode scan=rootObject(input.scanIndex(),FILE_LIMIT,machine,ProjectionEvidenceRole.UI_RECOVERY_LATER,grants);
        require(ROOT_INCIDENT_SCHEMA.equals(text(before.get("schema")))&&ROOT_INCIDENT_SCHEMA.equals(text(after.get("schema")))
                &&same(before.get("incident_id"),after.get("incident_id"))&&input.before().equals(ExactRef.fromJson(after.get("before"))),
                "Root mandatory completed pair identity/source differs");
        for(String field:List.of("origin","source","session_id"))require(same(before.get(field),after.get(field)),"Root mandatory after crossed its original "+field);
        require(machine.equals(text(before.path("origin").get("machine_id")))&&machine.equals(text(before.path("source").get("machine_id")))
                &&same(before.path("origin").get("game"),scan.path("origin").get("game"))
                &&same(before.get("source"),scan.get("source"))&&same(before.get("session_id"),scan.get("session_id")),
                "Root mandatory review crossed the physical Game/source/session/machine");
        require("xar.episode-incident-scan/v3".equals(text(scan.get("schema"))),"Root modal recovery needs the real later full-frame scan, not retained-only origin DATA");
        ExactRef backend=ExactRef.fromJson(before.get("backend_source"));rootVerify(backend,64L<<20);
        var fingerprint=fingerprint(before.get("native_window"),backend.sha256());
        require(fingerprint.isPresent(),"stable build/widget/callback source unavailable; no modal business or semantic claim");
        ExactRef read=ExactRef.fromJson(before.get("original_read"));rootObject(read,FILE_LIMIT,machine,ProjectionEvidenceRole.UI_RECOVERY_BEFORE,grants);
        ObjectNode effect=rootObject(ExactRef.fromJson(after.get("effect_basis")),FILE_LIMIT,machine,ProjectionEvidenceRole.UI_RECOVERY_AFTER,grants);
        require(Set.of("xar.java.native-effect-original-basis/v2","xar.java.native-effect-original-basis/v3").contains(text(effect.get("schema")))
                &&effect.path("independent_reads").isArray()&&effect.path("independent_reads").size()==1
                &&read.equals(ExactRef.fromJson(effect.path("independent_reads").get(0))),"Root modal effect lost its original sole native catalogue read");
        ObjectNode compatible=rootObject(ExactRef.fromJson(effect.get("compatible_material")),FILE_LIMIT,machine,ProjectionEvidenceRole.UI_RECOVERY_AFTER,grants);
        require(same(compatible,after.get("action_receipt"))&&disappearance(before,after)
                &&no(compatible.get("material_effects_verified")),"Root modal ACK/disappearance cannot claim gameplay material");
        ObjectNode nativeBefore=rootFrame(object(effect.get("before")),before,machine,ProjectionEvidenceRole.UI_RECOVERY_BEFORE,grants);
        ObjectNode nativeAfter=rootFrame(object(effect.get("after")),before,machine,ProjectionEvidenceRole.UI_RECOVERY_AFTER,grants);
        require(sameFrame(before.get("frame_binding"),nativeBefore)&&sameFrame(before.get("frame_binding"),before.path("native_window").get("frame_binding")),
                "Root modal catalogue lost its original native/public frame");
        require(sameActor(before.get("frame_binding"),nativeAfter)&&increasing(before.path("frame_binding").get("native_revision"),nativeAfter.get("native_revision"))
                &&increasing(before.path("frame_binding").get("revision"),nativeAfter.get("revision")),"Root modal postcondition needs a distinct same-actor native/public frame");
        JsonNode hint=nativeAfter.get("_hint");
        require(hint!=null&&yes(hint.get("owner_verified"))&&"application_main_pump_observed_modal_receiver".equals(text(hint.get("source")))
                &&BigInteger.valueOf(2000).equals(integer(hint.get("max_observation_age_ms")))
                &&("absent".equals(text(hint.get("status")))&&hint.path("opaque_root_id").isNull()
                ||"present".equals(text(hint.get("status")))&&text(hint.get("opaque_root_id"))!=null
                &&!same(hint.get("opaque_root_id"),before.path("native_window").get("window_instance_id"))),
                "Root modal independent after receiver is still present or unavailable");
        ExactRef progressRef=ExactRef.fromJson(scan.get("scan_observation_basis"));
        ObjectNode progress=rootObject(progressRef,FILE_LIMIT,machine,ProjectionEvidenceRole.UI_RECOVERY_LATER,grants);
        require("xar.java.incident-observation-original/v1".equals(text(progress.get("schema"))),"actual Root scan observation original required");
        for(String field:List.of("origin","source","session_id"))require(same(scan.get(field),progress.get(field)),"Root scan original changed "+field);
        ObjectNode later=rootFrame(progress,before,machine,ProjectionEvidenceRole.UI_RECOVERY_LATER,grants);
        require(sameActor(before.get("frame_binding"),later)&&increasing(before.path("frame_binding").get("date_raw"),later.get("date_raw"))
                &&increasing(nativeAfter.get("native_revision"),later.get("native_revision"))
                &&increasing(nativeAfter.get("revision"),later.get("revision")),"later same-Game date progress is not yet observed");
        require(originFrame(scan.get("origin"),later),"Root scan progress semantic frame differs from its indexed observation");
        ObjectNode fact=object(fingerprint.orElseThrow()).deepCopy();fact.put("schema",ROOT_REVIEW_SCHEMA).put("machine_id",machine)
                .put("incident_id",text(before.get("incident_id"))).put("status","known_ui_recovery_observed").put("known_recovery_source","observed-UI")
                .put("business_effect_known",false).put("semantic_optimal",false).put("game_date_progress_verified",true);
        fact.set("selected_choice_id",before.path("selection").get("choice_id"));
        fact.set("before_ref",input.before().toJson());fact.set("after_ref",input.after().toJson());fact.set("scan_index_ref",input.scanIndex().toJson());
        fact.set("backend_source",backend.toJson());fact.set("date_raw_before",before.path("frame_binding").get("date_raw"));fact.set("date_raw_after",later.get("date_raw"));
        rootVerify(input.before(),FILE_LIMIT);rootVerify(input.after(),FILE_LIMIT);rootVerify(input.scanIndex(),FILE_LIMIT);
        return new RootReview(fact,grants);
    }
    private static ObjectNode rootFrame(ObjectNode basis,ObjectNode before,String machine,ProjectionEvidenceRole role,List<ProjectionEvidenceGrant> grants)throws IOException {
        ExactRef nativeRef=ExactRef.fromJson(basis.get("native_frame")),driverRef=ExactRef.fromJson(basis.get("driver_facts"));
        rootVerify(nativeRef,(64L<<20)+4);
        ObjectNode facts=rootObject(driverRef,64<<20,machine,role,grants);
        require("xar.java-driver-observation-evidence/v1".equals(text(facts.get("schema")))&&nativeRef.sha256().equals(text(facts.get("native_packet_sha256")))
                &&BigInteger.valueOf(nativeRef.bytes()).equals(integer(facts.get("native_packet_bytes")))&&same(before.get("source"),facts.get("source"))
                &&same(before.get("session_id"),facts.path("transport").get("session_id")),"Root UI source lost its exact native/Driver original closure");
        rootVerify(ExactRef.fromJson(facts.get("driver_ref")),64L<<20);
        ObjectNode snapshot=object(facts.get("original_semantic_fields")),transport=object(facts.get("transport")),frame=JsonNodeFactory.instance.objectNode();
        require(machine.equals(text(transport.get("machine_id")))&&same(transport.get("pid"),before.path("frame_binding").get("game_pid"))
                &&same(transport.get("creation_filetime"),before.path("origin").path("game").get("creation_filetime")),"Root frame process/birth/machine differs");
        frame.set("game_pid",transport.get("pid"));
        frame.put("connection_generation",new BigInteger(new CrossJsDecimalUInt64(text(transport.get("connection_generation"))).decimal()));
        for(String field:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id"))frame.set(field,snapshot.get(field));
        frame.set("actor_character_id",snapshot.path("played_character").get("character_id"));frame.set("_hint",snapshot.get("top_exclusive_modal_choice_hint"));
        require(same(snapshot.path("diagnostics").get("bridge_pid"),frame.get("game_pid"))
                &&same(snapshot.path("diagnostics").get("connection_generation"),frame.get("connection_generation")),"Root semantic frame transport differs");
        require(same(frame.get("snapshot_id"),facts.get("snapshot_id"))&&same(frame.get("revision"),facts.get("public_revision"))
                &&same(frame.get("native_revision"),facts.get("native_revision")),"Root semantic frame differs from its native/Driver source");
        org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceCodec.decodeFrame(encode(withoutHint(frame),WIRE_LIMIT));
        return frame;
    }
    private static ObjectNode withoutHint(ObjectNode frame){ObjectNode copy=frame.deepCopy();copy.remove("_hint");return copy;}
    private static boolean sameActor(JsonNode first,JsonNode next){
        for(String field:List.of("game_pid","connection_generation","actor_character_id","episode_run_id"))if(!same(first.get(field),next.get(field)))return false;
        return true;
    }
    private static boolean sameFrame(JsonNode first,JsonNode next){return first!=null&&next!=null&&withoutHint(object(first)).equals(withoutHint(object(next)));}
    private static boolean originFrame(JsonNode origin,JsonNode later){
        JsonNode frame=origin.path("frame");
        String actor=text(frame.get("played_character_id"));
        return actor!=null&&integer(later.get("actor_character_id"))!=null&&actor.equals(integer(later.get("actor_character_id")).toString())
                &&same(frame.get("snapshot_id"),later.get("snapshot_id"))&&same(frame.get("episode_run_id"),later.get("episode_run_id"))
                &&decimalEquals(frame.get("revision"),later.get("revision"))&&decimalEquals(frame.get("native_revision"),later.get("native_revision"))
                &&decimalEquals(frame.get("date_raw"),later.get("date_raw"));
    }
    private static boolean decimalEquals(JsonNode decimal,JsonNode integer){
        String text=text(decimal);BigInteger value=integer(integer);
        return text!=null&&value!=null&&text.equals(value.toString());
    }
    private static ObjectNode rootObject(ExactRef ref,int maximum,String machine,ProjectionEvidenceRole role,List<ProjectionEvidenceGrant> grants)throws IOException {
        rootVerify(ref,maximum);byte[] raw=EvidenceGrantManifestPublisher.readStable(Path.of(ref.path()),maximum);
        require(raw.length==ref.bytes()&&sha(raw).equals(ref.sha256()),"Root original bytes/SHA changed");
        var grant=new ProjectionEvidenceGrant(Path.of(ref.path()),ref.bytes(),ref.sha256(),machine,role);if(!grants.contains(grant))grants.add(grant);
        return object(parse(raw,maximum));
    }
    static void rootVerify(ExactRef ref,long maximum)throws IOException {
        Path path=Path.of(ref.path());require(path.isAbsolute()&&path.equals(path.normalize())&&ref.bytes()>0&&ref.bytes()<=maximum,"bounded canonical Root original required");
        for(Path cursor=path;cursor!=null;cursor=cursor.getParent())require(!Files.isSymbolicLink(cursor)&&cursor.toRealPath().equals(cursor),"Root original cannot traverse an alias");
        BasicFileAttributes before=org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
        require(before.isRegularFile()&&before.fileKey()!=null&&before.size()==ref.bytes(),"Root original source identity/size differs");
        try {
            MessageDigest digest=MessageDigest.getInstance("SHA-256");long count=0;
            try(var input=Files.newInputStream(path)){byte[] buffer=new byte[65536];for(int n;(n=input.read(buffer))!=-1;){count=Math.addExact(count,n);require(count<=ref.bytes(),"Root original grew");digest.update(buffer,0,n);}}
            BasicFileAttributes after=org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
            require(count==ref.bytes()&&HexFormat.of().formatHex(digest.digest()).equals(ref.sha256())&&before.fileKey().equals(after.fileKey())
                    &&before.lastModifiedTime().equals(after.lastModifiedTime())&&after.size()==ref.bytes(),"Root original SHA/identity changed");
        }catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
    }

    private static void verifyPin(Path attempt, SourcePin pin) throws IOException {
        byte[] raw = readWithin(attempt, pin.path());
        if (raw.length != pin.bytes() || !sha(raw).equals(pin.sha256())) throw new SourceChangedException("captured original UI input SHA/bytes drift");
    }

    private static Prior priorReview(Configuration configured, Original before, Original after, String backend,
            ProjectionEvidenceGrant launch, String origin, List<ProjectionEvidenceGrant> additions) throws IOException {
        var source = fingerprint(before.value().get("native_window"), backend); if (source.isEmpty()) return null;
        String key = Objects.requireNonNull(text(source.orElseThrow().get("source_key")));
        Path known = configured.reviewRoot().resolve("known-ui-recovery").resolve(key).resolve(text(before.value().get("incident_id")) + ".json");
        try { org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(known); }
        catch (NoSuchFileException absent) { return null; }
        ObjectNode review = object(parse(EvidenceGrantManifestPublisher.readStable(known, FILE_LIMIT), FILE_LIMIT));
        require(REVIEW_SCHEMA.equals(text(review.get("schema"))) && "known_ui_recovery_observed".equals(text(review.get("status")))
                && "observed-UI".equals(text(review.get("known_recovery_source"))) && no(review.get("business_effect_known")) && no(review.get("semantic_optimal"))
                && key.equals(text(review.get("source_key"))) && same(source.orElseThrow().get("stable_source"), review.get("stable_source"))
                && before.path().equals(path(review.get("before_path"))) && after.path().equals(path(review.get("after_path")))
                && before.grant().sha256().equals(digest(review.get("before_sha256"))) && after.grant().sha256().equals(digest(review.get("after_sha256")))
                && integer(before.value().path("frame_binding").get("game_pid")) != null, "existing immutable UI knowledge does not bind this completed pair");
        Original later = original(configured.incidentAttempt(), path(review.get("later_source_path")), origin, ProjectionEvidenceRole.UI_RECOVERY_LATER);
        require(later.grant().sha256().equals(digest(review.get("later_source_sha256"))), "existing immutable UI progress SHA drift"); additions.add(later.grant());
        ObjectNode progress = JsonNodeFactory.instance.objectNode(); progress.put("source_path", later.path().toString()); progress.put("source_sha256", later.grant().sha256());
        progress.putArray("json_pointer").add("result").add("structured_content"); progress.put("game_launch_receipt_path", launch.path().toString()); progress.put("game_launch_receipt_sha256", launch.sha256());
        EventSourceReadContext snapshot = new EventSourceReadContext(configured.sources().machineId(), configured.sources().stateRoot(), configured.sources().stockGameRoot(), merge(configured.sources().evidenceGrants(), additions));
        ObjectNode checked = new UiRecoveryEvidenceLookup(snapshot).analyzeNode(before.value(), after.value(), backend, progress);
        require("known_ui_recovery_observed".equals(text(checked.get("status"))) && same(checked.get("source_key"), review.get("source_key"))
                && same(checked.get("selected_choice_id"), review.get("selected_choice_id")), "existing immutable UI knowledge failed actual evidence reanalysis");
        return new Prior(review, progress);
    }

    private static ObjectNode laterProgress(Path attempt, ObjectNode before, ObjectNode after, ObjectNode launch,
            ProjectionEvidenceGrant launchGrant, String origin, List<Path> candidates, List<ProjectionEvidenceGrant> additions) throws IOException {
        JsonNode frame = before.get("frame_binding"); if (!(frame instanceof ObjectNode) || integer(launch.get("pid")) == null
                || !integer(launch.get("pid")).equals(integer(frame.get("game_pid")))) return null;
        String afterAt = text(after.get("captured_at_utc"));
        for (int index = candidates.size() - 1; index >= 0; index--) {
            Path path = candidates.get(index); Original candidate = original(attempt, path, origin, ProjectionEvidenceRole.UI_RECOVERY_LATER);
            String ended = text(candidate.value().get("ended_at_utc"));
            // This break is intentional: preserve the original worker's sorted reverse/time boundary.
            if (afterAt != null && (ended == null || ended.compareTo(afterAt) <= 0)) break;
            JsonNode envelope = candidate.value().get("result");
            if (!(envelope instanceof ObjectNode) || yes(envelope.get("is_error"))) continue;
            JsonNode later = envelope.get("structured_content"); if (!(later instanceof ObjectNode)) continue;
            // The original scanner chooses by actor/episode/generation/date/revision.
            // The shared analyzer then checks an explicit later PID and may reject
            // that chosen response. Do not skip it here and silently select another.
            if (!sameWorkerProgress(frame, later)) continue;
            ObjectNode progress = JsonNodeFactory.instance.objectNode(); progress.put("source_path", path.toString()); progress.put("source_sha256", candidate.grant().sha256());
            progress.putArray("json_pointer").add("result").add("structured_content"); progress.put("game_launch_receipt_path", launchGrant.path().toString());
            progress.put("game_launch_receipt_sha256", launchGrant.sha256()); additions.add(candidate.grant()); return progress;
        }
        return null;
    }
    private static boolean sameWorkerProgress(JsonNode before, JsonNode later) {
        for (String key : List.of("actor_character_id", "connection_generation")) {
            if (integer(before.get(key)) == null || !integer(before.get(key)).equals(integer(later.get(key)))) return false;
        }
        return same(before.get("episode_run_id"), later.get("episode_run_id"))
                && increasing(before.get("date_raw"), later.get("date_raw")) && increasing(before.get("native_revision"), later.get("native_revision"));
    }
    private static List<ProjectionEvidenceGrant> merge(List<ProjectionEvidenceGrant> original, List<ProjectionEvidenceGrant> additions) {
        List<ProjectionEvidenceGrant> result = new ArrayList<>(original);
        for (ProjectionEvidenceGrant grant : additions) {
            ProjectionEvidenceGrant old = result.stream().filter(row -> row.path().equals(grant.path()) && row.role() == grant.role()).findFirst().orElse(null);
            require(old == null || old.equals(grant), "immutable UI evidence grant changed"); if (old == null) result.add(grant);
        }
        return List.copyOf(result);
    }
    private static Original original(Path attempt, Path path, String origin, ProjectionEvidenceRole role) throws IOException {
        byte[] raw = readWithin(attempt, path); return new Original(path, raw, object(parse(raw, FILE_LIMIT)), new ProjectionEvidenceGrant(path, raw.length, sha(raw), origin, role));
    }
    private static byte[] readWithin(Path attempt, Path path) throws IOException {
        require(path.startsWith(attempt) && !path.equals(attempt), "offline UI input escapes its configured attempt");
        try { return EvidenceGrantManifestPublisher.readStable(path, FILE_LIMIT); }
        catch (IOException error) { throw new SourceUnavailableException("original offline UI input unavailable", error); }
    }
    private static List<Path> responseFiles(Path attempt) throws IOException {
        BasicFileAttributes witness = directoryStamp(attempt); List<Path> result = new ArrayList<>(); int count = 0;
        try (var children = Files.newDirectoryStream(attempt)) { for (Path directory : children) {
            require(++count <= 1024, "bounded offline attempt directory required");
            if (directory.getFileName().toString().matches("p.*-responses")) {
                BasicFileAttributes entry = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(directory);
                require(!entry.isSymbolicLink(), "original response source directory cannot be a symbolic link");
                if (entry.isDirectory()) { result.addAll(files(directory, "-result.json", 4096)); require(result.size() <= 4096, "bounded immutable progress corpus required"); }
            }
        } }
        require(witness.fileKey().equals(directoryStamp(attempt).fileKey()), "original source attempt directory changed during capture");
        result.sort(Comparator.comparing(Path::toString)); return List.copyOf(result);
    }
    private static List<Path> files(Path directory, String suffix, int maximum) throws IOException {
        BasicFileAttributes witness;
        try { witness = directoryStamp(directory); }
        catch (NoSuchFileException absent) { return List.of(); }
        List<Path> result = new ArrayList<>(); int count = 0;
        try (var entries = Files.newDirectoryStream(directory)) { for (Path path : entries) {
            require(++count <= 8192, "bounded offline source directory required");
            if (path.getFileName().toString().endsWith(suffix)) result.add(path); require(result.size() <= maximum, "offline source cohort exceeds its declared bound");
        } }
        require(witness.fileKey().equals(directoryStamp(directory).fileKey()), "original source directory changed during capture");
        result.sort(Comparator.comparing(Path::toString)); return List.copyOf(result);
    }
    private static boolean regularPresent(Path path) throws IOException {
        try {
            BasicFileAttributes stamp = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
            require(stamp.isRegularFile() && !stamp.isSymbolicLink() && stamp.fileKey() != null && path.toRealPath().equals(path), "original completed-pair source must be a regular file without aliases");
            return true;
        } catch (NoSuchFileException absent) { return false; }
        catch (IOException unavailable) { throw new SourceUnavailableException("original completed-pair source unavailable", unavailable); }
    }
    private static BasicFileAttributes directoryStamp(Path path) throws IOException {
        BasicFileAttributes stamp = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
        require(stamp.isDirectory() && !stamp.isSymbolicLink() && stamp.fileKey() != null && path.toRealPath().equals(path), "fixed offline source directory without aliases required");
        return stamp;
    }
    private static Path fixed(Path path) { require(path != null && path.isAbsolute(), "absolute Root-configured offline path required"); return path.normalize(); }
    private static byte[] pretty(JsonNode value) { StringBuilder text = new StringBuilder(); pretty(value, text, 0); return (text + "\n").getBytes(java.nio.charset.StandardCharsets.UTF_8); }
    private static void pretty(JsonNode value, StringBuilder text, int depth) {
        if (value.isObject()) {
            List<String> names = new ArrayList<>(); value.fieldNames().forEachRemaining(names::add); names.sort(String::compareTo); text.append('{');
            for (int index = 0; index < names.size(); index++) { String name = names.get(index); if (index > 0) text.append(','); text.append('\n').append("  ".repeat(depth + 1));
                text.append(new String(encode(JsonNodeFactory.instance.textNode(name), FILE_LIMIT), java.nio.charset.StandardCharsets.UTF_8)).append(": "); pretty(value.get(name), text, depth + 1); }
            if (!names.isEmpty()) text.append('\n').append("  ".repeat(depth)); text.append('}');
        } else if (value.isArray()) {
            text.append('['); for (int index = 0; index < value.size(); index++) { if (index > 0) text.append(','); text.append('\n').append("  ".repeat(depth + 1)); pretty(value.get(index), text, depth + 1); }
            if (!value.isEmpty()) text.append('\n').append("  ".repeat(depth)); text.append(']');
        } else text.append(new String(encode(value, FILE_LIMIT), java.nio.charset.StandardCharsets.UTF_8));
        require(text.length() <= FILE_LIMIT, "offline UI output character bound exceeded");
    }
    private static void writeOnce(Path root, Path path, byte[] raw) throws IOException {
        require(path.startsWith(root) && raw.length <= FILE_LIMIT, "bounded canonical offline UI publication required"); Files.createDirectories(path.getParent());
        Map<Path, Object> parents = new LinkedHashMap<>(); Path cursor = path.getRoot();
        for (Path part : cursor.relativize(path.getParent())) { cursor = cursor.resolve(part); BasicFileAttributes stamp = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(cursor);
            require(stamp.isDirectory() && !stamp.isSymbolicLink() && stamp.fileKey() != null && cursor.toRealPath().equals(cursor), "immutable offline UI directory without aliases required"); parents.put(cursor, stamp.fileKey()); }
        try (FileChannel output = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS)) {
            ByteBuffer bytes = ByteBuffer.wrap(raw); while (bytes.hasRemaining()) output.write(bytes); output.force(true);
        } catch (FileAlreadyExistsException exists) { if (!Arrays.equals(EvidenceGrantManifestPublisher.readStable(path, FILE_LIMIT), raw)) throw new IOException("immutable review path changed: " + path); }
        for (Map.Entry<Path, Object> parent : parents.entrySet()) require(parent.getValue().equals(org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(parent.getKey()).fileKey()), "offline UI publication directory changed");
        require(Arrays.equals(raw, EvidenceGrantManifestPublisher.readStable(path, FILE_LIMIT)), "offline UI immutable publication readback differs");
    }
}

