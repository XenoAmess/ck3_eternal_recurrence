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
import java.util.HashSet;
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
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Loads the real manifest, complete scan index and its original journal files under fixed server roots. */
public final class OfflineScanSource {
    public static final int CAPTURED_DIAGNOSTIC_MAXIMUM = 16 << 20;
    private static final int FILE_MAX = 1 << 20;
    private static final long TOTAL_INVENTORY_MAX = 64L << 20;
    private OfflineScanSource() { }
    public record ExternalOriginal(ExactRef source, long maximumBytes) { }
    public record Loaded(Binding binding, byte[] manifestBytes, List<ExactRef> scanOriginals, List<ExternalOriginal> externalOriginals, Set<ExactRef> diagnosticBeforeRefs) {
        public Loaded { manifestBytes = manifestBytes.clone(); scanOriginals = List.copyOf(scanOriginals); externalOriginals = List.copyOf(externalOriginals); diagnosticBeforeRefs = Set.copyOf(diagnosticBeforeRefs); }
        public Loaded(Binding binding, byte[] manifestBytes, List<ExactRef> scanOriginals) { this(binding, manifestBytes, scanOriginals, List.of(), Set.of()); }
        public Loaded(Binding binding, byte[] manifestBytes, List<ExactRef> scanOriginals, List<ExternalOriginal> externalOriginals) { this(binding, manifestBytes, scanOriginals, externalOriginals, Set.of()); }
        @Override public byte[] manifestBytes() { return manifestBytes.clone(); }
        public int capturedMaximum(ExactRef ref) { return diagnosticBeforeRefs.contains(ref) ? CAPTURED_DIAGNOSTIC_MAXIMUM : FILE_MAX; }
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
        Set<ExactRef> diagnosticBeforeRefs = new HashSet<>();
        for (JsonNode item : index.path("original_refs")) {
            ExactRef ref = ExactRef.fromJson(item); Path path = absolute(ref.path());
            require(originals.put(path, ref) == null, "Duplicate original journal path");
            if (path.startsWith(incidentRoot)) { total = Math.addExact(total, ref.bytes()); require(total <= TOTAL_INVENTORY_MAX, "Actual internal journal source inventory exceeds its finite bound"); }
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
            // Aggregate inventory is separate; each declared failed-read original retains its 16 MiB role.
            for (ExactRef ref : readOriginals.references()) {
                Path path = absolute(ref.path());
                if (!path.startsWith(incidentRoot) && !external.containsKey(path)) {
                    total = Math.addExact(total, ref.bytes());
                    require(total <= TOTAL_INVENTORY_MAX, "Actual read-original scan inventory exceeds its finite bound");
                }
                long maximum = readOriginals instanceof IncidentReadIndex.KnownReceipt ? FILE_MAX : (16L << 20);
                declareExternal(originals, external, ref, maximum);
            }
            if (diagnostic) {
                require(diagnostics && "planning_diagnostic".equals(text(origin, "capture_stage")) && origin.get("action_id").isNull(), "Planning diagnostic cannot claim a submitted action");
                declareExternal(originals, external, ExactRef.fromJson(origin.get("original_frame_ref")), (64L << 20) + 4); actualDiagnosticCount++;
                if (qualifiesNativeDiagnostic(incidentRoot, before, origin)) {
                    require(!originals.containsKey(incidentRoot.resolve(id + ".after.json"))
                            && !originals.containsKey(incidentRoot.resolve(id + ".after-index.json")), "Native planning diagnostic cannot claim an after");
                    diagnosticBeforeRefs.add(before);
                }
            } else require(!text(origin, "action_id").isBlank(), "Submitted before index needs its real action identity");
            actualCapturedCount++;
        }
        for (var entry : originals.entrySet()) if (entry.getKey().startsWith(incidentRoot)) read(incidentRoot, entry.getValue(), diagnosticBeforeRefs.contains(entry.getValue()) ? CAPTURED_DIAGNOSTIC_MAXIMUM : FILE_MAX);
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
            ObjectNode beforeBody = diagnosticBeforeRefs.contains(before) ? object(FullJsonTree.parse(read(incidentRoot, before, CAPTURED_DIAGNOSTIC_MAXIMUM), CAPTURED_DIAGNOSTIC_MAXIMUM)) : json(read(incidentRoot, before));
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
                if ("xar.episode-incident-after-index/v3".equals(text(afterIndex,"schema"))) {
                    verifyLegacyAfter(afterIndex,origin,originRef,before,beforeBody,after,kind,id,
                            incidentRoot,scans,episodeRef,actual,originals,external,diagnosticBeforeRefs);
                } else {
                String afterSchema=text(afterIndex,"schema");boolean version2="xar.episode-incident-after-index/v2".equals(afterSchema);
                require((version2?afterIndex.has("policy_receipt_input")&&(afterIndex.get("policy_receipt_input").isNull()||afterIndex.get("policy_receipt_input").isObject()):"xar.episode-incident-after-index/v1".equals(afterSchema)&&!afterIndex.has("policy_receipt_input")) && id.equals(text(afterIndex, "incident_id"))
                        && before.equals(ExactRef.fromJson(afterIndex.get("before_ref"))) && after.equals(ExactRef.fromJson(afterIndex.get("after_ref"))), "Actual after index crossed its original before/after source");
                }
            }
        }
        require(used.equals(supplied), "Captured inventory must be exactly the actual batch's before/after originals");
        require(StrictJson.integer(index.get("incomplete_after"), 0, 1026) >= incomplete, "Actual scan lost incomplete-after diagnostics");
        read(scans, actual.indexRef()); read(scans, manifest);
        return new Loaded(binding, raw, originals.entrySet().stream().filter(entry -> !external.containsKey(entry.getKey())).map(Map.Entry::getValue).toList(), List.copyOf(external.values()), diagnosticBeforeRefs);
    }

    /** V3 side-evidence DATA only. Issued reconciliation/effect authority remains in Journal/Root. */
    private static void verifyLegacyAfter(ObjectNode afterIndex,ObjectNode origin,ExactRef originRef,
            ExactRef before,ObjectNode beforeBody,ExactRef after,String kind,String id,
            Path incidentRoot,Path scans,ExactRef episodeRef,ObservedScan actual,
            Map<Path,ExactRef> originals,Map<Path,ExternalOriginal> external,Set<ExactRef> diagnosticBeforeRefs) throws IOException {
        StrictJson.object(afterIndex,Set.of("schema","origin","source","session_id","incident_id",
                "independent_postcondition_verified","legacy_body_scope","before_ref","after_ref",
                "after_observation","after_frame","supporting_refs","policy_receipt_input","legacy_command_binding"));
        require("unhandled_event".equals(kind)&&"EVENT".equals(text(origin,"kind"))&&!origin.has("capture_stage")
                &&"before_submission".equals(text(beforeBody,"stage"))&&beforeBody.path("dispatch_attempted").isBoolean()
                &&!beforeBody.path("dispatch_attempted").booleanValue(),"V3 legacy side-evidence requires the original submitted EVENT capture");
        require(id.equals(text(afterIndex,"incident_id"))&&before.equals(ExactRef.fromJson(afterIndex.get("before_ref")))
                &&after.equals(ExactRef.fromJson(afterIndex.get("after_ref")))&&afterIndex.get("policy_receipt_input").isNull()
                &&afterIndex.path("independent_postcondition_verified").isBoolean()&&afterIndex.path("independent_postcondition_verified").booleanValue()
                &&"original_reply_ack_and_response_assessment".equals(text(afterIndex,"legacy_body_scope")),"V3 legacy after changed its exact originals or policy-receipt role");
        ObjectNode proof=StrictJson.object(afterIndex.get("legacy_command_binding"),Set.of("schema","episode_ref","scan_ref",
                "original_index","original_before","canonical_receipt_ref","canonical_record_ref","canonical_dispatch_ref",
                "canonical_command_base64","canonical_command_sha256","canonical_arguments_sha256","recorded_arguments_sha256",
                "reconciliation_guard","observation_supporting_refs"));
        require("xar.episode-incident-legacy-command-binding/v1".equals(text(proof,"schema"))
                &&originRef.equals(ExactRef.fromJson(proof.get("original_index")))&&before.equals(ExactRef.fromJson(proof.get("original_before")))
                &&episodeRef.equals(ExactRef.fromJson(proof.get("episode_ref"))),"Legacy proof changed its exact episode/index/before references");
        String recorded=text(proof,"recorded_arguments_sha256"),commandSha=text(proof,"canonical_command_sha256");
        require(recorded.matches("[0-9a-f]{64}")&&recorded.equals(text(origin,"arguments_sha256"))
                &&SourceReviewJson.sha((text(origin,"action_id")+"|"+recorded).getBytes(java.nio.charset.StandardCharsets.UTF_8)).substring(0,32).equals(id)
                &&commandSha.matches("[0-9a-f]{64}")&&text(proof,"canonical_arguments_sha256").matches("[0-9a-f]{64}"),"Legacy proof changed its recorded incident commitment or canonical SHA roles");
        String token=text(proof,"canonical_command_base64");
        require(token.length()<=((FILE_MAX+2)/3)*4,"Bounded complete canonical command base64 required");
        byte[] bytes=java.util.Base64.getDecoder().decode(token);
        require(bytes.length>0&&bytes.length<=FILE_MAX&&java.util.Base64.getEncoder().encodeToString(bytes).equals(token)
                &&SourceReviewJson.sha(bytes).equals(commandSha),"Canonical command bytes/base64/SHA differ");
        ObjectNode command=object(FullJsonTree.parse(bytes,FILE_MAX));String commandSchema=text(command,"schema");
        boolean explicit="xar.java-action-command/v4".equals(commandSchema);
        require(explicit||"xar.java-action-command/v1".equals(commandSchema),"Legacy EVENT proof requires its existing gameplay command codec");
        StrictJson.object(command,explicit?Set.of("schema","action_id","before","source","session_id","operation","arguments","expected","claims","deadline","protocol_identity")
                :Set.of("schema","action_id","before","source","session_id","operation","arguments","expected","claims","deadline"));
        require(text(origin,"action_id").equals(text(command,"action_id"))
                &&journalObservation(actual,origin.get("origin")).equals(journalObservation(actual,command.get("before")))
                &&OfflineBatchBinding.source(origin.get("source")).equals(OfflineBatchBinding.source(command.get("source")))
                &&text(origin,"session_id").equals(text(command,"session_id"))
                &&text(command,"operation").matches("select-event-option-[1-9][0-9]{0,8}"),"Canonical command crossed its complete original binding");
        object(command.get("expected"));object(command.get("claims"));StrictJson.utc(text(command,"deadline"));
        ObjectNode arguments=object(command.get("arguments")),capture=object(arguments.get("unhandled_event_fallback"));
        require("active_event_unhandled_first_rendered_option".equals(text(arguments,"phase"))
                &&"user-authorized-capture-then-first-rendered-option".equals(text(capture,"policy"))
                &&capture.path("registry_known").isBoolean()&&!capture.path("registry_known").booleanValue()
                &&"unknown".equals(text(object(capture.get("source_knowledge")),"status"))
                &&capture.get("policy").equals(beforeBody.get("policy"))&&capture.get("registry_known").equals(beforeBody.get("registry_known"))
                &&"unknown".equals(text(object(beforeBody.get("source_knowledge")),"status")),"Legacy proof cannot admit a dedicated, Populist or known-source policy");
        ExactRef scanRef=legacyRef(proof.get("scan_ref"),FILE_MAX);
        require(absolute(scanRef.path()).equals(scans.resolve(scanRef.sha256()+".scan.json")),"Legacy proof scan lost its fixed root/digest filename");
        ObjectNode selectedScan=json(loadLegacyOriginal(incidentRoot,originals,external,scanRef,FILE_MAX));
        sameEpisode(actual,selectedScan);String scanSchema=text(selectedScan,"schema");boolean progress="xar.episode-incident-scan/v3".equals(scanSchema);
        require(progress||"xar.episode-incident-scan/v2".equals(scanSchema),"Legacy proof requires its original complete versioned scan");
        StrictJson.object(selectedScan,progress?Set.of("schema","origin","source","session_id","incidents","captured_incidents","incomplete_after","diagnostic_only","episode_ref","original_refs","scan_observation_basis")
                :Set.of("schema","origin","source","session_id","incidents","captured_incidents","incomplete_after","diagnostic_only","episode_ref","original_refs"));
        require(episodeRef.equals(ExactRef.fromJson(selectedScan.get("episode_ref")))&&selectedScan.path("original_refs").isArray()
                &&selectedScan.path("original_refs").size()<=1026,"Legacy proof scan changed its original episode/inventory");
        ExactRef oldProgress=progress?legacyRef(selectedScan.get("scan_observation_basis"),FILE_MAX):null;
        Set<Path> selectedPaths=new HashSet<>();boolean hasIndex=false,hasBefore=false,hasEpisode=false;long selectedBytes=0;
        for(JsonNode value:selectedScan.get("original_refs")) {
            ExactRef ref=ExactRef.fromJson(value);Path path=absolute(ref.path());
            require(selectedPaths.add(path)&&ref.bytes()>0,"Distinct positive legacy scan originals required");
            selectedBytes=Math.addExact(selectedBytes,ref.bytes());require(selectedBytes<=TOTAL_INVENTORY_MAX,"Legacy proof scan inventory exceeds its finite bound");
            int maximum;
            if(path.startsWith(incidentRoot)) {
                require(ref.equals(originals.get(path)),"Legacy scan internal original differs from the complete current inventory");
                maximum=diagnosticBeforeRefs.contains(ref)?CAPTURED_DIAGNOSTIC_MAXIMUM:FILE_MAX;
            } else {
                ExternalOriginal known=external.get(path);
                require(ref.equals(oldProgress)||known!=null&&known.source().equals(ref),"Legacy scan external original has no declared bounded role");
                maximum=known==null?FILE_MAX:Math.toIntExact(known.maximumBytes());
            }
            loadLegacyOriginal(incidentRoot,originals,external,ref,maximum);
            hasIndex|=ref.equals(originRef);hasBefore|=ref.equals(before);hasEpisode|=ref.equals(episodeRef);
        }
        require(hasIndex&&hasBefore&&hasEpisode&&(oldProgress==null||selectedPaths.contains(absolute(oldProgress.path()))),"Legacy selected originals are absent from the complete pinned scan");
        if(oldProgress!=null) {
            ObjectNode basis=json(loadLegacyOriginal(incidentRoot,originals,external,oldProgress,FILE_MAX));
            require("xar.java.incident-observation-original/v1".equals(text(basis,"schema"))
                    &&selectedScan.get("origin").equals(basis.get("origin"))&&selectedScan.get("source").equals(basis.get("source"))
                    &&selectedScan.get("session_id").equals(basis.get("session_id")),"Legacy scan progress lost its original full-frame binding");
        }
        for(String field:List.of("canonical_receipt_ref","canonical_record_ref","canonical_dispatch_ref"))
            loadLegacyOriginal(incidentRoot,originals,external,legacyRef(proof.get(field),FILE_MAX),FILE_MAX);
        require(afterIndex.path("supporting_refs").isArray()&&afterIndex.path("supporting_refs").size()==1
                &&afterIndex.get("supporting_refs").equals(proof.get("observation_supporting_refs")),"Legacy after changed its sole observation support basis");
        loadLegacyOriginal(incidentRoot,originals,external,legacyRef(proof.get("observation_supporting_refs").get(0),FILE_MAX),FILE_MAX);
        verifyLegacyGuard(object(proof.get("reconciliation_guard")),command,proof,afterIndex,actual);
        // Repeat immutable source verification after parsing and all nested DATA checks.
        read(incidentRoot,originRef);read(incidentRoot,before);read(incidentRoot,episodeRef);read(scans,scanRef);
        long closure=0;Set<Path> closurePaths=new HashSet<>();
        for(var entry:originals.entrySet()){closurePaths.add(entry.getKey());closure=Math.addExact(closure,entry.getValue().bytes());}
        for(var entry:external.entrySet())if(closurePaths.add(entry.getKey()))closure=Math.addExact(closure,entry.getValue().source().bytes());
        require(closure<=TOTAL_INVENTORY_MAX,"Complete legacy side-evidence closure exceeds its finite inventory bound");
    }
    private static void verifyLegacyGuard(ObjectNode guard,ObjectNode command,ObjectNode proof,ObjectNode afterIndex,ObservedScan actual) {
        StrictJson.object(guard,Set.of("schema","origin","source","session_id","connection_generation","operation","native_evidence",
                "capability_evidence","authority_id","observed_at","valid_until","supporting_evidence"));
        require("xar.command-guard/v2".equals(text(guard,"schema"))&&guard.path("supporting_evidence").isArray()
                &&guard.path("supporting_evidence").size()>0&&guard.path("supporting_evidence").size()<=64,"Exact bounded reconciliation guard DATA required");
        ObjectNode origin=StrictJson.object(guard.get("origin"),Set.of("schema","kind","identity"));
        require("xar.command-origin/v3".equals(text(origin,"schema"))&&"RECONCILIATION".equals(text(origin,"kind")),"Legacy guard must retain its reconciliation origin");
        ObjectNode identity=StrictJson.object(origin.get("identity"),Set.of("schema","factual","source","session_id","connection_generation","pending","evidence","observed_at"));
        require("xar.java.reconciliation-identity/v1".equals(text(identity,"schema")),"Legacy DATA requires the EXACT relation, never HISTORY_APPEND");
        ObjectNode pending=StrictJson.object(identity.get("pending"),Set.of("action_id","body_sha256","request_id","original_before","original_receipt","original_before_driver"));
        ObjectNode evidence=StrictJson.object(identity.get("evidence"),Set.of("actual_native_packet","actual_hello","original_heartbeat","observation_manifest","current_original_driver"),Set.of("complete_source_qualification"));
        require(identity.get("factual").equals(afterIndex.get("after_observation"))
                &&OfflineBatchBinding.source(identity.get("source")).equals(OfflineBatchBinding.source(command.get("source")))
                &&identity.get("session_id").equals(command.get("session_id"))&&guard.get("source").equals(identity.get("source"))
                &&guard.get("session_id").equals(identity.get("session_id"))&&guard.get("connection_generation").equals(identity.get("connection_generation"))
                &&guard.get("operation").equals(command.get("operation")),"Reconciliation guard crossed its actual after/source/session/operation");
        require(command.get("action_id").equals(pending.get("action_id"))&&proof.get("canonical_command_sha256").equals(pending.get("body_sha256"))
                &&journalObservation(actual,command.get("before")).equals(journalObservation(actual,pending.get("original_before")))
                &&ExactRef.fromJson(proof.get("canonical_receipt_ref")).equals(ExactRef.fromJson(pending.get("original_receipt"))),"Reconciliation pending changed its original complete command/receipt");
        ExactRef nativeAfter=legacyRef(afterIndex.get("after_frame"),(64L<<20)+4);
        require(nativeAfter.equals(legacyRef(guard.get("native_evidence"),(64L<<20)+4))
                &&nativeAfter.equals(legacyRef(evidence.get("actual_native_packet"),(64L<<20)+4)),"Reconciliation guard changed its original after frame");
        legacyRef(guard.get("capability_evidence"),FILE_MAX);legacyRef(pending.get("original_before_driver"),FullJsonTree.MAXIMUM_DRIVER_BYTES);
        for(String field:List.of("actual_hello","original_heartbeat","observation_manifest"))legacyRef(evidence.get(field),FILE_MAX);
        legacyRef(evidence.get("current_original_driver"),FullJsonTree.MAXIMUM_DRIVER_BYTES);
        if(evidence.has("complete_source_qualification")&&!evidence.get("complete_source_qualification").isNull())legacyRef(evidence.get("complete_source_qualification"),FILE_MAX);
        for(JsonNode ref:guard.get("supporting_evidence"))legacyRef(ref,FullJsonTree.MAXIMUM_DRIVER_BYTES);
        text(guard,"authority_id");text(pending,"request_id");
        var generation=new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(text(guard,"connection_generation"));
        require(new java.math.BigInteger(generation.decimal()).signum()>0,"Positive original reconciliation generation required");
        StrictJson.utc(text(guard,"observed_at"));StrictJson.utc(text(guard,"valid_until"));StrictJson.utc(text(identity,"observed_at"));
        var factual=journalObservation(actual,identity.get("factual"));
        require(actual.observation().machineId().equals(factual.machineId())&&actual.observation().game().equals(factual.game())
                &&actual.observation().frame().episodeRunId().equals(factual.frame().episodeRunId()),"Legacy after observation crossed its original physical episode");
    }
    private static ExactRef legacyRef(JsonNode value,long maximum) {
        ExactRef ref=ExactRef.fromJson(value);absolute(ref.path());require(ref.bytes()>0&&ref.bytes()<=maximum,"Positive finite legacy original reference required");return ref;
    }
    /** Only exact fields of the recognized proof may declare new bounded nested originals. */
    private static byte[] loadLegacyOriginal(Path incidentRoot,Map<Path,ExactRef> originals,Map<Path,ExternalOriginal> external,
            ExactRef ref,int maximum) throws IOException {
        Path path=absolute(ref.path());require(ref.bytes()>0&&ref.bytes()<=maximum,"Finite legacy original role required");
        ExactRef existing=originals.get(path);require(existing==null||existing.equals(ref),"Legacy original conflicts with current inventory pin");
        if(path.startsWith(incidentRoot)) {
            require(ref.equals(existing),"Legacy internal original is absent from the complete inventory");return read(incidentRoot,ref,maximum);
        }
        ExternalOriginal old=external.putIfAbsent(path,new ExternalOriginal(ref,maximum));
        require(old==null||old.source().equals(ref),"Conflicting legacy nested original");
        if(old!=null&&maximum<old.maximumBytes())external.put(path,new ExternalOriginal(ref,maximum));
        verifyExternal(ref,maximum);byte[] raw=EvidenceGrantManifestPublisher.readStable(path,maximum);
        require(raw.length==ref.bytes()&&SourceReviewJson.sha(raw).equals(ref.sha256()),"Legacy nested original bytes/SHA changed");verifyExternal(ref,maximum);return raw;
    }

    private static boolean qualifiesNativeDiagnostic(Path root, ExactRef before, ObjectNode origin) throws IOException {
        byte[] raw = read(root, before, CAPTURED_DIAGNOSTIC_MAXIMUM);
        ObjectNode body = object(FullJsonTree.parse(raw, CAPTURED_DIAGNOSTIC_MAXIMUM));
        if (!"xar.unhandled-native-window-diagnostic/v1".equals(text(body, "schema"))) {
            require(raw.length <= FILE_MAX, "Legacy before body exceeds its unchanged role bound");
            return false;
        }
        String expectedKind = switch (text(origin, "kind")) {
            case "EVENT" -> "unhandled_event";
            case "INTERACTION" -> "pending_character_interaction";
            case "MANDATORY" -> "unknown_mandatory_choice";
            default -> throw new IllegalArgumentException("Unknown original diagnostic kind");
        };
        require(text(origin, "incident_id").equals(text(body, "incident_id"))
                && expectedKind.equals(text(body, "kind"))
                && "planning_diagnostic".equals(text(body, "stage"))
                && body.path("selection").isNull() && body.path("dispatch_attempted").isBoolean()
                && !body.path("dispatch_attempted").booleanValue()
                && origin.get("origin").equals(body.get("origin")), "Native diagnostic crossed its original index binding");
        return true;
    }

    public static void recheck(Path incidentRoot, Optional<Path> scanRoot, ExactRef manifest, Loaded original) throws IOException {
        Path root = original.binding() instanceof ObservedScan ? scanRoot.orElseThrow() : incidentRoot;
        if (original.binding() instanceof ObservedScan actual && !absolute(manifest.path()).getParent().equals(root)) {
            var scope = IncidentJournalLayout.scope(incidentRoot, root, actual.observation().machineId(), actual.observation().game(), actual.sessionId(), actual.observation().frame().episodeRunId(), actual.source().sourceRef());
            require(absolute(manifest.path()).getParent().equals(scope.scanRoot()), "Rechecked scan escaped its derived identity"); incidentRoot = scope.incidentRoot(); root = scope.scanRoot();
        }
        for (ExactRef ref : original.scanOriginals()) read(incidentRoot, ref, original.capturedMaximum(ref));
        for (ExternalOriginal ref : original.externalOriginals()) verifyExternal(ref.source(), ref.maximumBytes());
        if (original.binding() instanceof ObservedScan actual) read(root, actual.indexRef());
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
    private static byte[] read(Path root, ExactRef ref) throws IOException { return read(root, ref, FILE_MAX); }
    private static byte[] read(Path root, ExactRef ref, int maximum) throws IOException {
        require(maximum == FILE_MAX || maximum == CAPTURED_DIAGNOSTIC_MAXIMUM, "Finite original journal role required");
        Path path = absolute(ref.path()); require(path.startsWith(root) && !path.equals(root) && ref.bytes() > 0 && ref.bytes() <= maximum, "Original source escapes its fixed journal role");
        byte[] raw = EvidenceGrantManifestPublisher.readStable(path, maximum);
        require(raw.length == ref.bytes() && SourceReviewJson.sha(raw).equals(ref.sha256()), "Actual journal source bytes or SHA changed"); return raw;
    }
    private static ObjectNode json(byte[] raw) { return object(StrictJson.parse(ProjectionJson.object(raw, FILE_MAX).bytes(), FILE_MAX)); }
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
