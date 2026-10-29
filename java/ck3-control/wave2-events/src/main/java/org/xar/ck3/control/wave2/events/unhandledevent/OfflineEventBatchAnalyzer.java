package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding.ObservedScan;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.OfflineMandatoryChoiceReviewProducer;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Existing offline batch analysis and publication in the shared host, without Python, Game or timeline calls. */
public final class OfflineEventBatchAnalyzer {
    public static final int MAX_REQUEST_BYTES = 2_097_152;
    private static final int SOURCE_MAXIMUM = 1_048_576;
    public static final String REQUEST_SCHEMA = "xar.offline-event-batch-request/v1";
    private OfflineEventBatchAnalyzer() { }
    private static final class OutputFailure extends IOException {
        private static final long serialVersionUID = 1L;
        OutputFailure(IOException cause) { super("offline immutable publication failed", cause); }
    }
    private static final class OutputConflict extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        OutputConflict(IllegalArgumentException cause) { super("immutable offline output already differs", cause); }
    }

    public record Configuration(EventSourceReadContext sources, Path incidentRoot, Path knowledgeRoot, Path grantsManifest, Optional<Path> scanRoot) {
        public Configuration(EventSourceReadContext sources, Path incidentRoot, Path knowledgeRoot, Path grantsManifest) {
            this(sources, incidentRoot, knowledgeRoot, grantsManifest, Optional.empty());
        }
        public Configuration {
            Objects.requireNonNull(sources); incidentRoot = fixed(incidentRoot); knowledgeRoot = fixed(knowledgeRoot); grantsManifest = fixed(grantsManifest);
            scanRoot = Objects.requireNonNull(scanRoot).map(OfflineEventBatchAnalyzer::fixed);
            if (scanRoot.isPresent()) require(!scanRoot.orElseThrow().startsWith(sources.stockGameRoot())
                    && !scanRoot.orElseThrow().startsWith(incidentRoot) && !incidentRoot.startsWith(scanRoot.orElseThrow()), "Distinct fixed offline scan root required");
            require(!incidentRoot.startsWith(sources.stockGameRoot()) && !knowledgeRoot.startsWith(sources.stockGameRoot())
                    && !grantsManifest.startsWith(sources.stockGameRoot()), "offline evidence cannot write into installed stock roots");
        }
    }
    public record Request(String batchId, ExactRef manifest, List<ExactRef> capturedRefs) {
        public Request {
            require(batchId != null && batchId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"), "bounded offline batch identifier required");
            Objects.requireNonNull(manifest); capturedRefs = List.copyOf(capturedRefs); require(capturedRefs.size() <= 512, "bounded captured reference list required");
        }
    }
    public record Result(String batchId, ExactRef report, ObjectValue reportDocument, List<ExactRef> outputs,
            EvidenceGrantManifestPublisher.Publication grants, boolean idempotent, String machineId, String observedAtUtc) {
        public Result { outputs = List.copyOf(outputs); }
    }
    public static Request decode(byte[] raw) {
        var decoded = OfflineEventAnalysisWire.decodeBatch(raw);
        return new Request(decoded.batchId(), decoded.manifestRef(), decoded.capturedRefs());
    }

    public static OfflineBatchBinding.Binding validateInputs(Configuration configured, Request request) throws IOException {
        return OfflineScanSource.load(configured.incidentRoot(), configured.scanRoot(), configured.sources().machineId(), request.manifest(), request.capturedRefs()).binding();
    }

    public static Result run(Configuration configured, Request request) throws IOException {
        Objects.requireNonNull(configured); Objects.requireNonNull(request);
        TrustedEventSourceContext trusted = TrustedEventSourceContext.open(configured.sources());
        OfflineEventSourceIndex index = OfflineEventSourceIndex.currentBuild();
        return EvidenceGrantManifestPublisher.transaction(configured.grantsManifest(), writer -> analyze(configured, request, trusted, index, writer));
    }
    private static Result analyze(Configuration configured, Request request, TrustedEventSourceContext trusted,
            OfflineEventSourceIndex index, EvidenceGrantManifestPublisher.Writer writer) throws IOException {
        OfflineScanSource.Loaded originalScan = OfflineScanSource.load(configured.incidentRoot(), configured.scanRoot(), trusted.machineId(), request.manifest(), request.capturedRefs());
        byte[] manifestRaw = originalScan.manifestBytes();
        var batchBinding = originalScan.binding(); boolean observedScan = batchBinding instanceof ObservedScan;
        ObjectValue batch = RetainedJson.object(RetainedJson.parse(manifestRaw));
        List<ObjectValue> incidents = objects(batch, "new_incidents"); require(incidents.size() <= 256, "bounded offline incident batch required");
        Map<Path, ExactRef> pins = new LinkedHashMap<>();
        for (ExactRef ref : request.capturedRefs()) require(pins.put(fixed(Path.of(ref.path())), ref) == null, "duplicate captured source path");
        // Source pins are checked before any durable output. A stale/cross-root request cannot publish partial knowledge.
        for (ObjectValue item : incidents) {
            require(observedScan || !interaction(item) || hasAfter(item), "legacy completed interaction batch requires its original after receipt");
            captured(configured.incidentRoot(), pins, item, "before");
            if (hasAfter(item)) captured(configured.incidentRoot(), pins, item, "after");
        }
        Path output = configured.knowledgeRoot().resolve(request.batchId()); Path reportPath = output.resolve("EVENT-SOURCE-REVIEW.json");
        boolean idempotent = Files.exists(reportPath, LinkOption.NOFOLLOW_LINKS); ObjectValue previous = null;
        String observed = Instant.now().toString();
        if (idempotent) {
            previous = RetainedJson.object(RetainedJson.parse(EvidenceGrantManifestPublisher.readStable(reportPath, SOURCE_MAXIMUM)));
            require(eq(previous, "machine_id", s(trusted.machineId())) && o(previous, "manifest") != null
                    && eq(o(previous, "manifest"), "sha256", s(request.manifest().sha256()))
                    && eq(o(previous, "manifest"), "path", s(request.manifest().path())), "offline batch identifier already binds a different source or machine");
            OfflineBatchBinding.requireReport(StrictJson.parse(RetainedJson.encode(previous), SOURCE_MAXIMUM), batchBinding, request.manifest());
            observed = required(previous, "observed_at_utc"); StrictJson.utc(observed);
        }
        List<String> previousEntries = previous == null ? List.of() : objects(previous, "entries").stream().map(row -> required(row, "incident_id")).toList();
        List<Value> entries = new ArrayList<>(), known = new ArrayList<>(), unresolved = new ArrayList<>();
        Map<String, ExactRef> outputs = new LinkedHashMap<>(); List<ProjectionEvidenceGrant> grants = new ArrayList<>();
        for (ObjectValue item : incidents) {
            if (skip(item)) {
                unresolved.add(obj(f("incident_id", v(item, "incident_id")), f("event_definition_key", v(item, "event_definition_key")),
                        f("status", s("unknown_unable_to_source_review")), f("reason", s("original event definition key unavailable; no analysis completion"))));
                continue;
            }
            try {
                String incident = required(item, "incident_id");
                ObjectValue before = RetainedJson.object(RetainedJson.parse(captured(configured.incidentRoot(), pins, item, "before")));
                if(mandatory(item)&&eq(before,"schema",s("xar.unhandled-native-window-diagnostic/v1"))) {
                    require(eq(before,"incident_id",s(incident))&&eq(before,"kind",s("unknown_mandatory_choice"))
                            &&eq(before,"stage",s("planning_diagnostic"))&&eq(before,"dispatch_attempted",b(false))
                            &&before.get("selection") instanceof NullValue&&!hasAfter(item),"mandatory diagnostic cannot claim a submitted selection or after");
                    unresolved.add(obj(f("incident_id",s(incident)),f("kind",s("unknown_mandatory_choice")),f("status",s("diagnostic_only")),
                            f("reason",v(before,"diagnostic_reason"))));
                    continue;
                }
                require(eq(before, "incident_id", s(incident)) && eq(before, "schema", s(mandatory(item)
                        ? OfflineMandatoryChoiceReviewProducer.ROOT_INCIDENT_SCHEMA : interaction(item)
                        ? "xar.pending-interaction-left-reply/v1" : "xar.unhandled-event-first-rendered/v1")), "incident source SHA/identity differs");
                if (hasAfter(item)) {
                    ObjectValue after = RetainedJson.object(RetainedJson.parse(captured(configured.incidentRoot(), pins, item, "after")));
                    require(eq(after, "incident_id", s(incident)), "event after source SHA/identity differs");
                    if (interaction(item)) {
                        ExactRef beforeRef = pins.get(fixed(Path.of(required(item, "before")))); ObjectValue declared = o(after, "before");
                        require(eq(after, "schema", s("xar.pending-interaction-left-reply/v1")) && declared != null
                                && eq(declared, "path", s(beforeRef.path())) && eq(declared, "sha256", s(beforeRef.sha256()))
                                && eq(declared, "bytes", i(beforeRef.bytes())), "interaction after crossed its original before reference");
                    }
                }
                if (mandatory(item)) {
                    require(batchBinding instanceof ObservedScan && hasAfter(item), "Root modal analysis requires its real observed completed pair");
                    var scan=(ObservedScan)batchBinding;
                    var reviewed=OfflineMandatoryChoiceReviewProducer.reviewRoot(new OfflineMandatoryChoiceReviewProducer.RootInputs(
                            pins.get(fixed(Path.of(required(item,"before")))),pins.get(fixed(Path.of(required(item,"after")))),scan.indexRef()),trusted.machineId());
                    ObjectValue fact=RetainedJson.object(RetainedJson.parse(StrictJson.canonical(reviewed.fact(),SOURCE_MAXIMUM)));
                    String key=required(fact,"source_key");
                    Path canonicalPath=trusted.stateDirectory().resolve("evidence/unknown-mandatory-choice-reviews/root-known-ui-recovery").resolve(key).resolve(incident+".json");
                    boolean existed=Files.exists(canonicalPath,LinkOption.NOFOLLOW_LINKS);
                    ExactRef canonical=writeOutput(trusted.stateDirectory(),canonicalPath,fact);
                    ExactRef local=linkOutput(configured.knowledgeRoot(),output.resolve(incident+".mandatory-source-facts.json"),canonical);
                    outputs.put(canonical.path(),canonical);outputs.put(local.path(),local);
                    for(var source:reviewed.sources())add(grants,source);
                    ObjectValue classification=obj(f("incident_id",s(incident)),f("kind",s("unknown_mandatory_choice")),
                            f("fingerprint",s(key)),f("status",s("known_ui_recovery_observed")),f("business_effect_known",b(false)),
                            f("semantic_optimal",b(false)),f("source_facts",OfflineReviewDocuments.reference(local)),
                            f("published",OfflineReviewDocuments.reference(canonical)),f("known_next_same_key",b(true)));
                    if(existed&&!previousEntries.contains(incident))known.add(classification);else entries.add(classification);
                    continue;
                }
                if (interaction(item)) {
                    if (!previousEntries.contains(incident) && eq(before, "registry_known", b(true)) && eq(before, "offline_followup_required", b(false))) {
                        InteractionRegistry.Result existing = OfflineInteractionSourceAnalyzer.reviewed(before, trusted);
                        if (existing instanceof InteractionRegistry.Known reviewed) {
                            var review = reviewed.review();
                            known.add(obj(f("incident_id", s(incident)), f("canonical_key", s(review.entry().binding().definition().canonicalKey())),
                                    f("fingerprint", s(review.entry().fingerprint())), f("status", s("source_reviewed_known")), f("offline_followup_required", b(false))));
                            addExistingInteractionFacts(trusted, review.entry(), grants); continue;
                        }
                    }
                    OfflineInteractionSourceAnalyzer.Analysis analysis = OfflineInteractionSourceAnalyzer.analyze(before, trusted);
                    InteractionRegistry.Facts facts = analysis.facts(); String fingerprint = facts.fingerprint();
                    Path registry = trusted.stateDirectory().resolve("evidence/interaction-source-registry");
                    Path factsPath = registry.resolve("facts").resolve(fingerprint + ".json"); boolean factsExisted = Files.exists(factsPath, LinkOption.NOFOLLOW_LINKS);
                    ExactRef canonical = writeOutput(trusted.stateDirectory(), factsPath, RetainedJson.parse(InteractionRegistryCodec.encodeFacts(facts)));
                    ExactRef local = linkOutput(configured.knowledgeRoot(), output.resolve(fingerprint + ".source-facts.json"), canonical);
                    InteractionRegistry.Entry entry = new InteractionRegistry.Entry(fingerprint, facts.binding(), InteractionRegistry.CLASSIFICATION,
                            "reject", facts.paths(), new InteractionRegistry.SourceRef(canonical.path(), canonical.sha256()), OfflineInteractionSourceAnalyzer.REASON);
                    ExactRef published = writeOutput(trusted.stateDirectory(), registry.resolve(fingerprint + ".json"),
                            RetainedJson.parse(InteractionRegistryCodec.encodeEntry(entry)));
                    ExactRef candidate = linkOutput(configured.knowledgeRoot(), output.resolve(fingerprint + ".registry-entry.json"), published);
                    for (ExactRef ref : List.of(canonical, local, published, candidate)) outputs.put(ref.path(), ref);
                    String origin = grants.stream().filter(grant -> grant.path().equals(factsPath) && grant.role() == ProjectionEvidenceRole.EVENT_SOURCE_FACTS)
                            .map(ProjectionEvidenceGrant::originMachineId).findFirst().orElseGet(() -> factsExisted ? origin(trusted, factsPath) : trusted.machineId());
                    add(grants, new ProjectionEvidenceGrant(factsPath, canonical.bytes(), canonical.sha256(),
                            origin, ProjectionEvidenceRole.EVENT_SOURCE_FACTS));
                    entries.add(obj(f("incident_id", s(incident)), f("canonical_key", s(facts.binding().definition().canonicalKey())), f("fingerprint", s(fingerprint)),
                            f("source_facts", OfflineReviewDocuments.reference(local)), f("canonical_source_facts", OfflineReviewDocuments.reference(canonical)),
                            f("candidate", OfflineReviewDocuments.reference(candidate)), f("published", OfflineReviewDocuments.reference(published)), f("known_next_same_key", b(true))));
                    continue;
                }
                SourceReviewedEventConsumer.NativeBinding nativeBinding = SourceReviewedEventConsumer.nativeBinding(before);
                if (!previousEntries.contains(incident) && eq(before, "registry_known", b(true)) && eq(before, "offline_followup_required", b(false))) {
                    var existing = SourceReviewedEventConsumer.reviewedReference(before, trusted);
                    if (existing.isPresent()) {
                        var review = existing.orElseThrow();
                        known.add(obj(f("incident_id", s(incident)), f("event_definition_key", s(nativeBinding.eventKey())), f("fingerprint", s(review.fingerprint())),
                                f("status", s("source_reviewed_known")), f("offline_followup_required", b(false))));
                        addExistingFacts(trusted, review.entryPath(), grants); continue;
                    }
                }
                OfflineEventSourceIndex.Loaded source = index.load(trusted, before);
                OfflineEventSourceAnalyzer.Analysis analysis = OfflineEventSourceAnalyzer.analyze(before, source.path(), source.relative(), source.bytes());
                String fingerprint = analysis.fingerprint(); Path registry = trusted.stateDirectory().resolve("evidence/event-source-registry");
                Path factsPath = registry.resolve("facts").resolve(fingerprint + ".json"); boolean factsExisted = Files.exists(factsPath, LinkOption.NOFOLLOW_LINKS);
                ExactRef canonical = writeOutput(trusted.stateDirectory(), factsPath, analysis.facts());
                ExactRef local = linkOutput(configured.knowledgeRoot(), output.resolve(fingerprint + ".source-facts.json"), canonical);
                ObjectValue entry = obj(f("schema", s(SourceReviewedEventConsumer.SCHEMA)), f("fingerprint", s(fingerprint)), f("binding", analysis.binding()),
                        f("source_path", s(source.path().toString())), f("source_facts", OfflineReviewDocuments.reference(canonical)),
                        f("classification", s("offline-source-reviewed-user-first-rendered-policy")), f("registry_contract_accepted", b(false)), f("material_effects_verified", b(false)));
                ExactRef published = writeOutput(trusted.stateDirectory(), registry.resolve(fingerprint + ".json"), entry);
                ExactRef candidate = linkOutput(configured.knowledgeRoot(), output.resolve(fingerprint + ".registry-entry.json"), published);
                for (ExactRef ref : List.of(canonical, local, published, candidate)) outputs.put(ref.path(), ref);
                String origin = grants.stream().filter(grant -> grant.path().equals(factsPath) && grant.role() == ProjectionEvidenceRole.EVENT_SOURCE_FACTS)
                        .map(ProjectionEvidenceGrant::originMachineId).findFirst().orElseGet(() -> factsExisted ? origin(trusted, factsPath) : trusted.machineId());
                add(grants, new ProjectionEvidenceGrant(factsPath, canonical.bytes(), canonical.sha256(), origin, ProjectionEvidenceRole.EVENT_SOURCE_FACTS));
                entries.add(obj(f("incident_id", s(incident)), f("event_definition_key", s(nativeBinding.eventKey())), f("fingerprint", s(fingerprint)),
                        f("source_facts", OfflineReviewDocuments.reference(local)), f("canonical_source_facts", OfflineReviewDocuments.reference(canonical)),
                        f("candidate", OfflineReviewDocuments.reference(candidate)), f("published", OfflineReviewDocuments.reference(published))));
            } catch (OutputFailure publication) { throw publication; }
            catch (OutputConflict conflict) { throw conflict; }
            catch (IOException | IllegalArgumentException | TrustedEventSourceContext.UnavailableException refused) {
                unresolved.add(obj(f("incident_id", v(item, "incident_id")), f("event_definition_key", v(item, "event_definition_key")),
                        f("status", s("unknown_unable_to_source_review")), f("reason", s(refused.getMessage() == null ? refused.getClass().getSimpleName() : refused.getMessage()))));
            }
        }
        trusted.verifyCurrentRoots();
        OfflineScanSource.recheck(configured.incidentRoot(), configured.scanRoot(), request.manifest(), originalScan);
        ObjectValue report = obj(f("machine_id", s(trusted.machineId())), f("observed_at_utc", s(observed)),
                f("manifest", observedScan ? exactRef(request.manifest()) : OfflineReviewDocuments.reference(request.manifest())),
                f("entries", new ArrayValue(entries)), f("already_known", new ArrayValue(known)), f("unresolved", new ArrayValue(unresolved)), f("Game_MCP_OBS_calls", i(0)));
        var reportNode = (com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RetainedJson.encode(report), SOURCE_MAXIMUM);
        OfflineBatchBinding.addReportBinding(reportNode, batchBinding);
        if (observedScan) reportNode.put("material_effects_verified", false);
        report = RetainedJson.object(RetainedJson.parse(StrictJson.canonical(reportNode, SOURCE_MAXIMUM)));
        OfflineBatchBinding.requireReport(reportNode, batchBinding, request.manifest());
        ExactRef reportRef = OfflineReviewDocuments.write(configured.knowledgeRoot(), reportPath, report); outputs.put(reportRef.path(), reportRef);
        EvidenceGrantManifestPublisher.Publication publication = writer.publish(grants);
        return new Result(request.batchId(), reportRef, report, List.copyOf(outputs.values()), publication, idempotent, trusted.machineId(), Instant.now().toString());
    }
    private static void addExistingFacts(TrustedEventSourceContext trusted, Path entryPath, List<ProjectionEvidenceGrant> grants) throws IOException {
        ObjectValue entry = RetainedJson.object(RetainedJson.parse(trusted.readState(entryPath, 65_536))); ObjectValue ref = o(entry, "source_facts");
        require(ref != null, "existing source facts reference missing"); Path path = fixed(Path.of(required(ref, "path")));
        byte[] raw = trusted.read(path, SOURCE_MAXIMUM, TrustedEventSourceContext.FileRole.FACTS);
        require(eq(ref, "sha256", s(sha(raw))), "existing source facts original SHA differs");
        add(grants, new ProjectionEvidenceGrant(path, raw.length, sha(raw), origin(trusted, path), ProjectionEvidenceRole.EVENT_SOURCE_FACTS));
    }
    private static void addExistingInteractionFacts(TrustedEventSourceContext trusted, InteractionRegistry.Entry entry,
            List<ProjectionEvidenceGrant> grants) {
        Path path = fixed(Path.of(entry.sourceFacts().path())); byte[] raw = trusted.readInteractionFacts(path);
        require(sha(raw).equals(entry.sourceFacts().sha256()), "existing interaction facts original SHA differs");
        add(grants, new ProjectionEvidenceGrant(path, raw.length, sha(raw), origin(trusted, path), ProjectionEvidenceRole.EVENT_SOURCE_FACTS));
    }
    private static ExactRef writeOutput(Path root, Path path, Value value) throws IOException {
        try { return OfflineReviewDocuments.write(root, path, value); }
        catch (IOException error) { throw new OutputFailure(error); }
        catch (IllegalArgumentException error) { throw new OutputConflict(error); }
    }
    private static ExactRef linkOutput(Path root, Path path, ExactRef source) throws IOException {
        try { return OfflineReviewDocuments.link(root, path, source); }
        catch (IOException error) { throw new OutputFailure(error); }
        catch (IllegalArgumentException error) { throw new OutputConflict(error); }
    }
    private static String origin(TrustedEventSourceContext trusted, Path path) {
        return trusted.evidenceGrantsSnapshot().stream().filter(grant -> grant.path().equals(path) && grant.role() == ProjectionEvidenceRole.EVENT_SOURCE_FACTS)
                .map(ProjectionEvidenceGrant::originMachineId).findFirst().orElse("unknown");
    }
    private static void add(List<ProjectionEvidenceGrant> grants, ProjectionEvidenceGrant grant) {
        if (!grants.contains(grant)) grants.add(grant);
    }
    private static boolean interaction(ObjectValue item) { return eq(item, "kind", s("pending_character_interaction")); }
    private static boolean mandatory(ObjectValue item) { return eq(item, "kind", s("unknown_mandatory_choice")); }
    private static boolean skip(ObjectValue item) { return !mandatory(item) && !interaction(item) && (v(item, "event_definition_key") instanceof NullValue || eq(item, "event_definition_key", s(""))); }
    private static boolean hasAfter(ObjectValue item) { return !(v(item, "after") instanceof NullValue) && !eq(item, "after", s("")); }
    private static byte[] captured(Path root, Map<Path, ExactRef> pins, ObjectValue item, String stage) throws IOException {
        Path path = fixed(Path.of(required(item, stage))); ExactRef ref = pins.get(path);
        require(ref != null && eq(item, stage + "_sha256", s(ref.sha256())), "captured source reference missing or crossed its manifest pin"); return read(root, ref);
    }
    private static byte[] read(Path root, ExactRef ref) throws IOException {
        Path path = fixed(Path.of(ref.path())); require(path.startsWith(root) && !path.equals(root) && ref.bytes() > 0 && ref.bytes() <= SOURCE_MAXIMUM,
                "captured source escapes its fixed incident root or role bound");
        byte[] raw = EvidenceGrantManifestPublisher.readStable(path, SOURCE_MAXIMUM);
        require(raw.length == ref.bytes() && sha(raw).equals(ref.sha256()), "actual captured source pin changed"); return raw;
    }
    public static byte[] encode(Result result) {
        List<Value> outputs = result.outputs().stream().map(ref -> (Value) exactRef(ref)).toList();
        var grants = result.grants();
        byte[] raw = RetainedJson.encodeOfflineMetadata(obj(f("schema", s("xar.offline-event-analysis-result/v1")), f("batch_id", s(result.batchId())),
                f("machine_id", s(result.machineId())), f("observed_at_utc", s(result.observedAtUtc())), f("idempotent", b(result.idempotent())),
                f("report_ref", exactRef(result.report())), f("report", result.reportDocument()), f("outputs", new ArrayValue(outputs)),
                f("grants_manifest", obj(f("path", s(grants.path().toString())), f("bytes", i(grants.bytes())), f("sha256", s(grants.sha256())), f("grants", i(grants.grants())), f("added", i(grants.added())))),
                f("Game_MCP_OBS_calls", i(0)), f("timeline_writer_calls", i(0))));
        require(raw.length <= MAX_REQUEST_BYTES, "offline response byte bound exceeded");
        return OfflineEventAnalysisWire.validateBatchResult(raw, result.batchId());
    }
    private static ObjectValue exactRef(ExactRef ref) { return obj(f("path", s(ref.path())), f("bytes", i(ref.bytes())), f("sha256", s(ref.sha256()))); }
    private static Path fixed(Path path) { require(path != null && path.isAbsolute(), "absolute server-configured offline path required"); return path.normalize(); }
    private static String required(ObjectValue row, String field) { String value = text(row, field); require(value != null && !value.isBlank(), "original offline text required: " + field); return value; }
}
