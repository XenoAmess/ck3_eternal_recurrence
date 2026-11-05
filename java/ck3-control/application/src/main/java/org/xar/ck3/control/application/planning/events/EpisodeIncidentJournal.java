package org.xar.ck3.control.application.planning.events;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.channels.OverlappingFileLockException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeEventEffects;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding;
import org.xar.ck3.control.contracts.offline.IncidentReadIndex;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeComposer;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence;
import org.xar.ck3.control.wave2.events.interactionreceipt.InteractionReceipt;
import org.xar.ck3.control.wave2.events.unhandledevent.InteractionHostJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedInteractionContinuation;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventEvidenceJson;

/** Actual incident bodies and finite source-bound scans. The sole action coordinator retains submission/ledger authority. */
public final class EpisodeIncidentJournal {
    public static final String MANIFEST_SCHEMA = OfflineBatchBinding.MANIFEST_V3;
    public static final String STAMP_SCHEMA = "xar.episode-incident-root/v1";
    public static final String SCAN_SCHEMA = "xar.episode-incident-scan/v2";
    public static final String OBSERVED_STAMP_SCHEMA = "xar.episode-incident-root/v2";
    private static final String AFTER_INDEX_SCHEMA = "xar.episode-incident-after-index/v2";
    private static final String LEGACY_AFTER_INDEX_SCHEMA = "xar.episode-incident-after-index/v1";
    private static final String UNSETTLED_SCHEMA = "xar.episode-incident-unsettled-observation/v1";
    public static final String LEGACY_BINDING_SCHEMA = "xar.episode-incident-legacy-command-binding/v1";
    private static final String LEGACY_RECOVERY_AFTER_SCHEMA = "xar.episode-incident-after-index/v3";
    private static final String LEGACY_RECOVERY_UNSETTLED_SCHEMA = "xar.episode-incident-unsettled-observation/v2";
    private static final int MAX_METADATA = 1 << 20;
    // Complete incident bodies stay within the existing material cap; scan inventory remains separately bounded.
    private static final int MAX_BODY = FullJsonTree.MAXIMUM_BYTES;
    private static final long MAX_SCAN_BYTES = 64L << 20;
    private final Configuration configured;
    private final ExactRef episodeRef;
    private final Binding episode;
    public enum Kind { EVENT, INTERACTION, MANDATORY }
    @FunctionalInterface public interface IoGuard { void require(long pendingBytes) throws IOException; }
    @FunctionalInterface public interface ProgressOriginal { ExactRef preserve() throws IOException; }
    public record Configuration(Path incidentRoot, Path scanRoot, Clock clock, IoGuard io,
            Optional<TrustedEventSourceContext> trustedInteractions, Optional<java.util.function.Consumer<RawJson>> legacyVerifier) {
        public Configuration(Path incidentRoot, Path scanRoot, Clock clock, IoGuard io, Optional<TrustedEventSourceContext> trustedInteractions) {
            this(incidentRoot,scanRoot,clock,io,trustedInteractions,Optional.empty());
        }
        public Configuration {
            incidentRoot = absolute(incidentRoot); scanRoot = absolute(scanRoot);
            Objects.requireNonNull(clock); Objects.requireNonNull(io); Objects.requireNonNull(trustedInteractions);Objects.requireNonNull(legacyVerifier);
            if (incidentRoot.equals(scanRoot) || scanRoot.startsWith(incidentRoot) || incidentRoot.startsWith(scanRoot))
                throw new IllegalArgumentException("Distinct configured incident and scan roots required");
        }
    }
    public record Binding(ObservationIdentity before, G2Source source, String sessionId) {
        public Binding { Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(sessionId); StrictJson.require(before.machineId().equals(source.machineId()), "incident source machine differs"); }
        public void requireEpisode(Binding actual) {
            StrictJson.require(before.machineId().equals(actual.before.machineId()) && before.game().equals(actual.before.game())
                    && before.frame().episodeRunId().equals(actual.before.frame().episodeRunId()) && source.equals(actual.source)
                    && sessionId.equals(actual.sessionId), "incident journal crossed physical Game, source, session or episode");
        }
    }
    /** Actual coordinator outcome and prepared request; this is not a successful read receipt. */
    public record FailedReadReferences(ExactRef originalOutcome, ExactRef preparedRequest, Optional<ExactRef> observedFailure,
            List<ExactRef> dependencies) {
        public FailedReadReferences { Objects.requireNonNull(originalOutcome); Objects.requireNonNull(preparedRequest);
            Objects.requireNonNull(observedFailure); dependencies = List.copyOf(dependencies); }
    }
    private sealed interface ReadOriginals permits NoRead, KnownRead, FailedRead { List<ExactRef> refs(); }
    private enum NoRead implements ReadOriginals {
        INSTANCE;
        @Override public List<ExactRef> refs() { return List.of(); }
    }
    private record KnownRead(ExactRef original) implements ReadOriginals {
        private KnownRead { Objects.requireNonNull(original); }
        @Override public List<ExactRef> refs() { return List.of(original); }
    }
    private record FailedRead(FailedReadReferences original) implements ReadOriginals {
        private FailedRead { Objects.requireNonNull(original); }
        @Override public List<ExactRef> refs() { return indexReadValue(this).references(); }
    }
    public record Ticket(String incidentId, Kind kind, ExactRef before, ExactRef index, Binding origin) {
        public Ticket { StrictJson.text(incidentId); Objects.requireNonNull(kind); Objects.requireNonNull(before); Objects.requireNonNull(index); Objects.requireNonNull(origin); }
    }
    public record Scan(Binding binding, ExactRef episodeRef, ExactRef indexRef, Optional<BatchRequest> batch,
            List<ExactRef> originals, int incidents, int capturedIncidents, int incompleteAfter, int diagnosticOnly) {
        public Scan { Objects.requireNonNull(binding); Objects.requireNonNull(episodeRef); Objects.requireNonNull(indexRef); Objects.requireNonNull(batch); originals = List.copyOf(originals); }
        public List<ExactRef> evidence() {
            List<ExactRef> all = new ArrayList<>(List.of(episodeRef, indexRef)); all.addAll(originals);
            batch.ifPresent(value -> { all.add(value.manifestRef()); for (var ref : value.capturedRefs()) if (!all.contains(ref)) all.add(ref); });
            return List.copyOf(all);
        }
    }
    private EpisodeIncidentJournal(Configuration configured, ExactRef episodeRef, Binding episode) {
        this.configured = configured; this.episodeRef = episodeRef; this.episode = episode;
    }
    public Configuration configuration() { return configured; }
    public ExactRef episodeReference() { return episodeRef; }
    public Binding origin() { return episode; }
    public Optional<ExactRef> originalObservationBasis() throws IOException {
        ObjectNode row = object(read(episodeRef));
        return OBSERVED_STAMP_SCHEMA.equals(text(row, "schema")) ? Optional.of(ExactRef.fromJson(row.get("original_observation_basis"))) : Optional.empty();
    }
    /** A real current full-frame archive basis; this stamp does not qualify an initial entry or restore. */
    public static EpisodeIncidentJournal initializeObserved(Configuration configured, Binding actual, ExactRef originalBasis) throws IOException {
        plainDirectory(configured.incidentRoot()); plainDirectory(configured.scanRoot()); verifyExternal(originalBasis);
        require(originalBasis.bytes() <= MAX_METADATA, "Bounded typed original observation basis required");
        Path stamp = configured.incidentRoot().resolve("EPISODE.json");
        try (var listing = Files.list(configured.incidentRoot())) { require(listing.findAny().isEmpty(), "New observed journal must actually be empty"); }
        ObjectNode row = binding(actual); row.put("schema", OBSERVED_STAMP_SCHEMA); row.set("original_observation_basis", originalBasis.toJson());
        return new EpisodeIncidentJournal(configured, write(configured, stamp, encode(row)), actual);
    }
    /** Opens historical side evidence only; the caller replays its original full-frame basis in the same archive. */
    public static EpisodeIncidentJournal openOriginal(Configuration configured, ExactRef originalEpisode) throws IOException {
        ObjectNode body = object(read(originalEpisode));
        return open(configured, decodeBinding(body), originalEpisode);
    }
    /** Only explicit new-episode initialization may create the original empty root stamp. */
    public static EpisodeIncidentJournal initialize(Configuration configured, Binding initial) throws IOException {
        plainDirectory(configured.incidentRoot()); plainDirectory(configured.scanRoot());
        Path stamp = configured.incidentRoot().resolve("EPISODE.json");
        require(Files.notExists(stamp, LinkOption.NOFOLLOW_LINKS), "Existing episode root cannot be reset or silently repaired");
        try (var listing = Files.list(configured.incidentRoot())) { require(listing.findAny().isEmpty(), "New episode incident root must actually be empty"); }
        ObjectNode body = binding(initial); body.put("schema", STAMP_SCHEMA);
        ExactRef ref = write(configured, stamp, encode(body)); return new EpisodeIncidentJournal(configured, ref, initial);
    }
    public static EpisodeIncidentJournal open(Configuration configured, Binding actual, ExactRef originalEpisode) throws IOException {
        plainDirectory(configured.incidentRoot()); plainDirectory(configured.scanRoot());
        require(Path.of(originalEpisode.path()).equals(configured.incidentRoot().resolve("EPISODE.json")), "Original episode stamp path differs");
        ObjectNode body = object(read(originalEpisode)); require(Set.of(STAMP_SCHEMA, OBSERVED_STAMP_SCHEMA).contains(text(body, "schema")), "Original episode stamp schema required");
        Binding bound = decodeBinding(body); bound.requireEpisode(actual);
        return new EpisodeIncidentJournal(configured, originalEpisode, bound);
    }
    public boolean handles(ActionCommand command) {
        boolean event = command.arguments().get("unhandled_event_fallback") instanceof OpportunityJson.Obj;
        boolean interaction = command.arguments().get("unhandled_interaction_fallback") instanceof OpportunityJson.Obj;
        boolean mandatory = command.arguments().get("unknown_mandatory_choice_v1") instanceof OpportunityJson.Obj;
        if (mandatory) {
            StrictJson.require(!event && !interaction && "select-mandatory-choice-v1".equals(command.operation().value()), "One original native mandatory incident required");
            return true;
        }
        if (!event && !interaction) return false;
        StrictJson.require(event != interaction, "One original foreground incident kind required");
        StrictJson.require(event ? command.operation().value().matches("select-event-option-[1-9][0-9]{0,8}")
                : Set.of("reject-pending-character-interaction", "acknowledge-pending-character-interaction").contains(command.operation().value()),
                "Fallback evidence cannot authorize another operation or an acceptance");
        return true;
    }
    /** Actual displayed fallback with no legal command; this creates no action ID, dispatch or after. */
    public Ticket captureBlocked(PlanningRequest request, OpportunityJson.Obj retainedPlan, ExactRef actualFrame) throws IOException {
        Objects.requireNonNull(request);
        return captureBlocked(new Binding(request.before(), request.source(), request.sessionId()), retainedPlan, actualFrame, Optional.empty());
    }
    /** Retained actual frame binding also serves private pending UI diagnostics without an ordinary request. */
    public Ticket captureBlocked(Binding actual, OpportunityJson.Obj retainedPlan, ExactRef actualFrame, Optional<ExactRef> originalRead) throws IOException {
        Objects.requireNonNull(originalRead);
        return captureBlocked(actual, retainedPlan, actualFrame,
                originalRead.<ReadOriginals>map(KnownRead::new).orElse(NoRead.INSTANCE));
    }
    /** A genuine failed query retains its two originals without claiming a successful read receipt. */
    public Ticket captureFailedRead(Binding actual, OpportunityJson.Obj retainedPlan, ExactRef actualFrame,
            FailedReadReferences originals) throws IOException {
        return captureBlocked(actual, retainedPlan, actualFrame, new FailedRead(originals));
    }
    private Ticket captureBlocked(Binding actual, OpportunityJson.Obj retainedPlan, ExactRef actualFrame,
            ReadOriginals originalRead) throws IOException {
        Objects.requireNonNull(actual); Objects.requireNonNull(originalRead); episode.requireEpisode(actual);
        verifyReadOriginals(originalRead);
        verifyEpisode(); verifyExternal(actualFrame);
        ObjectNode plan = object(DriverJson.encode(retainedPlan));
        require(plan.path("selected_step").isNull(), "Blocked capture must explicitly retain a null selected step");
        boolean diagnostic = plan.path("unhandled_native_window_diagnostic").isObject();
        require(!(originalRead instanceof FailedRead) || diagnostic, "Failed query cannot manufacture a first-rendered fallback");
        ObjectNode unavailable = diagnostic ? object(plan.get("unhandled_native_window_diagnostic")) : null;
        boolean event = diagnostic ? "unhandled_event".equals(text(unavailable, "kind")) : plan.path("unhandled_event_fallback").isObject();
        boolean interaction = diagnostic ? "pending_character_interaction".equals(text(unavailable, "kind")) : plan.path("unhandled_interaction_fallback").isObject();
        boolean mandatory=diagnostic&&"unknown_mandatory_choice".equals(text(unavailable,"kind"));
        require((event?1:0)+(interaction?1:0)+(mandatory?1:0)==1, "One actual blocked foreground capture required");
        Kind kind = mandatory?Kind.MANDATORY:event?Kind.EVENT:Kind.INTERACTION;
        ObjectNode capture = diagnostic ? unavailable : object(plan.get(event ? "unhandled_event_fallback" : "unhandled_interaction_fallback"));
        if (!diagnostic) validateCaptureBinding(actual.before(), capture);
        else require(ProposalLifecycleCodec.decodeObservation(capture.get("origin")).equals(actual.before())
                && capture.get("selection").isNull() && "xar.unhandled-native-window-diagnostic/v1".equals(text(capture, "schema")), "Actual unavailable-window frame and null selection required");
        String hash = digest(DriverJson.encode(retainedPlan));
        String id = digest(("planning-diagnostic|" + actual.sessionId() + "|" + hash).getBytes(java.nio.charset.StandardCharsets.UTF_8)).substring(0, 32);
        return locked(() -> {
            Path indexPath = configured.incidentRoot().resolve(id + ".before-index.json");
            if (Files.exists(indexPath, LinkOption.NOFOLLOW_LINKS)) {
                ExactRef pin = measure(indexPath); ObjectNode old = object(read(pin));
                require(decodeBinding(old).equals(actual) && "planning_diagnostic".equals(text(old, "capture_stage"))
                        && hash.equals(text(old, "arguments_sha256")) && old.path("action_id").isNull()
                        && beforeIndexRead(old).equals(originalRead), "Original blocked capture differs");
                ExactRef before = ExactRef.fromJson(old.get("before_ref")); read(before); return new Ticket(id, kind, before, pin, actual);
            }
            ObjectNode planned = StrictJson.object().put("snapshot_id", actual.before().frame().snapshotId()).put("revision", actual.before().frame().revision());
            planned.set("plan", plan); String now = configured.clock().instant().toString(); byte[] raw;
            if (diagnostic) {
                ObjectNode body = capture.deepCopy(); body.put("incident_id", id).put("captured_at_utc", now).put("stage", "planning_diagnostic").put("dispatch_attempted", false);
                raw = encode(body);
            } else if (kind == Kind.EVENT) raw = UnhandledEventEvidenceJson.encodeBody(UnhandledEventEvidenceJson.before(
                    new UnhandledEventEvidenceJson.BeforeInput(Optional.of(retained(planned)), id, now)));
            else {
                var trusted = configured.trustedInteractions().orElseThrow(() -> new IOException("Actual stock GUI source required for blocked interaction"));
                SourceReviewedInteractionContinuation.verifyGui(trusted); byte[] original = encode(planned);
                var body = InteractionBeforeComposer.compose(original, digest(original), new InteractionBeforeEvidence.Identity(id, now, actual.before().machineId()),
                        new InteractionBeforeEvidence.GuiSourcePin(InteractionFallback.GUI_SOURCE, InteractionFallback.GUI_SHA256));
                require(body instanceof InteractionBeforeEvidence.Prepared, "Original blocked interaction capture unavailable"); raw = ((InteractionBeforeEvidence.Prepared)body).json();
            }
            ObjectNode actualBody = object(raw); actualBody.put("stage", "planning_diagnostic").put("dispatch_attempted", false);
            if (!diagnostic && kind == Kind.EVENT) object(actualBody.get("selection")).putNull("selected_step");
            ExactRef before = write(configured, configured.incidentRoot().resolve(id + ".before.json"), encode(actualBody));
            ObjectNode index = binding(actual); index.put("incident_id", id).put("kind", kind.name())
                    .put("capture_stage", "planning_diagnostic").putNull("action_id").put("arguments_sha256", hash);
            index.set("before_ref", before.toJson()); index.set("original_frame_ref", actualFrame.toJson());
            index = IncidentReadIndex.encode(indexReadValue(originalRead), index);
            ExactRef pin = write(configured, indexPath, encode(index)); return new Ticket(id, kind, before, pin, actual);
        });
    }
    /** Called from the actual coordinator's pre-INTENT hook under its original writer session. */
    public Optional<Ticket> before(ActionCommand command) throws IOException {
        if (!handles(command)) return Optional.empty();
        Binding actual = new Binding(command.before(), command.source(), command.sessionId()); episode.requireEpisode(actual);
        verifyEpisode();
        Kind kind = command.arguments().get("unknown_mandatory_choice_v1") instanceof OpportunityJson.Obj ? Kind.MANDATORY
                : command.arguments().get("unhandled_event_fallback") instanceof OpportunityJson.Obj ? Kind.EVENT : Kind.INTERACTION;
        OpportunityJson.Obj capturedArguments = incidentArguments(command);
        String id = incidentId(command.actionId(), digest(DriverJson.encode(capturedArguments)));
        return locked(() -> {
            Path indexPath = originalIndexPath(command, capturedArguments);
            if (Files.exists(indexPath, LinkOption.NOFOLLOW_LINKS)) return Optional.of(readTicket(command, indexPath));
            ObjectNode planned = StrictJson.object().put("snapshot_id", command.before().frame().snapshotId()).put("revision", command.before().frame().revision());
            planned.set("plan", StrictJson.parse(DriverJson.encode(capturedArguments)));
            String now = configured.clock().instant().toString(); byte[] raw;
            ObjectNode capture = object(planned.path("plan").get(kind == Kind.MANDATORY ? "unknown_mandatory_choice_v1"
                    : kind == Kind.EVENT ? "unhandled_event_fallback" : "unhandled_interaction_fallback"));
            if (kind == Kind.MANDATORY) {
                // The actual mandatory adapter already checked this catalogue against its archived original query.
                ExactRef originalRead = ExactRef.fromJson(planned.path("plan").get("mandatory_choice_original_read"));
                ExactRef backend = ExactRef.fromJson(planned.path("plan").get("mandatory_backend_source"));
                verifyExternal(originalRead); verifyExternal(backend);
                ObjectNode body = binding(actual); body.setAll(capture);
                body.put("schema", "xar.root-mandatory-choice-incident/v1").put("incident_id", id).put("captured_at_utc", now);
                body.set("backend_source", backend.toJson()); body.set("original_read", originalRead.toJson());
                body.put("business_effect_known", false).put("semantic_optimal", false);
                raw = encode(body);
            } else if (kind == Kind.EVENT) {
                validateCaptureBinding(command.before(), capture);
                var body = UnhandledEventEvidenceJson.before(new UnhandledEventEvidenceJson.BeforeInput(Optional.of(retained(planned)), id, now));
                require(body.isPresent(), "Actual fallback plan did not produce its before incident"); raw = UnhandledEventEvidenceJson.encodeBody(body);
            } else {
                validateCaptureBinding(command.before(), capture);
                var trusted = configured.trustedInteractions().orElseThrow(() -> new IOException("Actual stock GUI source context required for interaction capture"));
                SourceReviewedInteractionContinuation.verifyGui(trusted);
                byte[] original = encode(planned);
                var result = InteractionBeforeComposer.compose(original, digest(original), new InteractionBeforeEvidence.Identity(id, now, command.before().machineId()),
                        new InteractionBeforeEvidence.GuiSourcePin(InteractionFallback.GUI_SOURCE, InteractionFallback.GUI_SHA256));
                require(result instanceof InteractionBeforeEvidence.Prepared, "Actual native-left producer did not prepare a before incident");
                raw = ((InteractionBeforeEvidence.Prepared)result).json();
            }
            ExactRef before = write(configured, configured.incidentRoot().resolve(id + ".before.json"), raw);
            ObjectNode index = binding(actual); index.put("schema", "xar.episode-incident-before-index/v1").put("incident_id", id)
                    .put("kind", kind.name()).put("action_id", command.actionId()).put("arguments_sha256", digest(DriverJson.encode(capturedArguments)));
            index.set("before_ref", before.toJson());
            if (kind == Kind.MANDATORY) index = IncidentReadIndex.encode(new IncidentReadIndex.KnownReceipt(
                    ExactRef.fromJson(planned.path("plan").get("mandatory_choice_original_read"))), index);
            ExactRef indexed = write(configured, indexPath, encode(index)); return Optional.of(new Ticket(id, kind, before, indexed, actual));
        });
    }
    /** Called only by the actual observer after independent evidence has been durably archived. It performs no native query. */
    public void observedAfter(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            NativeEffectRegistry.Projected projected) {
        observedAfterBound(command,attempt,pair,projected,Optional.empty());
    }
    public void observedAfterLegacy(ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair pair,
            NativeEffectRegistry.Projected projected,RawJson proof)throws IOException {
        requireLegacyLive(command,attempt,pair,proof);
        ObjectNode data=object(StrictJson.parse(proof.bytes(),MAX_METADATA));var supports=new ArrayList<ExactRef>();
        for(JsonNode ref:data.get("observation_supporting_refs"))supports.add(ExactRef.fromJson(ref));
        require(projected.result() instanceof ActionPorts.EffectObserved&&supports.size()==1
                &&((ActionPorts.EffectObserved)projected.result()).observation().supportingEvidence().equals(supports),"legacy proof changed the actual effect supporting closure");
        observedAfterBound(command,attempt,pair,projected,Optional.of(proof));
    }
    private void observedAfterBound(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            NativeEffectRegistry.Projected projected, Optional<RawJson> legacy) {
        if (!handles(command)) return;
        try {
            StrictJson.require(projected.result() instanceof ActionPorts.EffectObserved && projected.compatibleResult().isPresent(), "Independent observed effect required for incident after");
            var effect = ((ActionPorts.EffectObserved)projected.result()).observation();
            StrictJson.require(pair.before().identity().equals(command.before()) && pair.before().originalEvidence().equals(attempt.guard().nativeEvidence())
                    && pair.after().identity().equals(effect.after()) && pair.after().source().equals(command.source())
                    && pair.after().sessionId().equals(command.sessionId()) && !effect.supportingEvidence().isEmpty(), "Incident after lost original frame/evidence binding");
            for (ExactRef source : effect.supportingEvidence()) verifyExternal(source);
            verifyExternal(pair.after().originalEvidence());
            Ticket ticket = legacy.isPresent()?legacyTicket(legacy.orElseThrow(),command):existing(command);
            locked(() -> {
                Path afterIndex = configured.incidentRoot().resolve(ticket.incidentId() + ".after-index.json");
                if (Files.exists(afterIndex, LinkOption.NOFOLLOW_LINKS)) {
                    ObjectNode previous = object(read(measure(afterIndex)));
                    require(ExactRef.fromJson(previous.get("before_ref")).equals(ticket.before())
                            && ProposalLifecycleCodec.decodeObservation(previous.get("after_observation")).equals(pair.after().identity()), "Original incident after already differs");
                    ExactRef originalAfter=ExactRef.fromJson(previous.get("after_ref"));
                    verifyPolicyReceipt(previous,object(read(ticket.index())),read(ticket.before()),read(originalAfter));return null;
                }
                byte[] originalBeforeBody=read(ticket.before());ObjectNode before = object(originalBeforeBody);
                ObjectNode originalTicket = StrictJson.object().put("incident_id", ticket.incidentId()); originalTicket.set("before", ticket.before().toJson());
                byte[] compatible = projected.compatibleResult().orElseThrow().bytes();
                String now = configured.clock().instant().toString(); byte[] raw;
                if (ticket.kind() == Kind.MANDATORY) {
                    ObjectNode body = binding(ticket.origin()); body.put("schema", "xar.root-mandatory-choice-incident/v1")
                            .put("incident_id", ticket.incidentId()).put("captured_at_utc", now)
                            .put("original_blocking_window_advanced_verified", true).put("business_effect_known", false).put("semantic_optimal", false);
                    body.set("before", ticket.before().toJson()); body.set("action_receipt", StrictJson.parse(compatible));
                    body.set("after_observation", ProposalLifecycleCodec.observation(pair.after().identity()));
                    body.set("effect_basis", effect.supportingEvidence().getFirst().toJson());
                    raw = encode(body);
                } else if (ticket.kind() == Kind.EVENT) {
                    originalTicket.set("current_event_instance_id", before.get("current_event_instance_id"));
                    originalTicket.set("selected_native_option_index", before.path("selection").get("native_option_index"));
                    ObjectNode outcome = StrictJson.object().put("status", "independent_effect_observed"); outcome.set("result", StrictJson.parse(compatible));
                    var after = UnhandledEventEvidenceJson.after(new UnhandledEventEvidenceJson.AfterInput(Optional.of(retained(originalTicket)),
                            Optional.of(retained(outcome)), RetainedJson.NULL, now)); raw = UnhandledEventEvidenceJson.encodeBody(after);
                } else {
                    originalTicket.set("pending_interaction_id", before.get("pending_interaction_id"));
                    originalTicket.set("action", before.path("selection").get("action"));
                    var response = new InteractionHostJson.Original(compatible, digest(compatible));
                    var input = new InteractionHostJson.AfterBodyInput(Optional.of(retained(originalTicket)), response, InteractionReceipt.Origin.EXECUTE_STEP, null, now);
                    raw = InteractionHostJson.encodeReceipt(InteractionHostJson.projectReceipt(input));
                }
                ExactRef after = write(configured, configured.incidentRoot().resolve(ticket.incidentId() + ".after.json"), raw);
                ObjectNode index = binding(ticket.origin()); index.put("schema", legacy.isPresent()?LEGACY_RECOVERY_AFTER_SCHEMA:AFTER_INDEX_SCHEMA).put("incident_id", ticket.incidentId())
                        .put("independent_postcondition_verified", true).put("legacy_body_scope", "original_reply_ack_and_response_assessment");
                index.set("before_ref", ticket.before().toJson()); index.set("after_ref", after.toJson());
                index.set("after_observation", ProposalLifecycleCodec.observation(pair.after().identity())); index.set("after_frame", pair.after().originalEvidence().toJson());
                var evidence = index.putArray("supporting_refs"); effect.supportingEvidence().forEach(ref -> evidence.add(ref.toJson()));
                Optional<RawJson> policyInput=legacy.isPresent()?Optional.empty():EventIncidentReceipt.prepare(indexedArguments(command,object(read(ticket.index()))),projected.compatibleResult().orElseThrow(),ticket.before(),after,new RawJson(raw));
                if(legacy.isPresent())index.set("legacy_command_binding",StrictJson.parse(legacy.orElseThrow().bytes(),MAX_METADATA));
                if(policyInput.isPresent())index.set("policy_receipt_input",StrictJson.parse(policyInput.orElseThrow().bytes(),MAX_METADATA));else index.putNull("policy_receipt_input");
                // A mismatch must remain inspectable and unresolved. The coordinator already converts
                // this verifier's failure into UNKNOWN; no event selection is submitted again.
                write(configured, afterIndex, encode(index));verifyPolicyReceipt(index,object(read(ticket.index())),originalBeforeBody,read(after));return null;
            });
        } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
    }
    /** Retains the first actual negative observation separately from a qualified after index.
     * A later real advancement can still produce the original .after.json; this diagnostic cannot settle it.
     */
    public ExactRef observedUnsettled(ActionCommand command,ActionState.Attempt attempt,
            NativeEventEffects.UnsettledObservation actual,ExactRef originalDispatch)throws IOException {
        return observedUnsettledBound(command,attempt,actual,originalDispatch,Optional.empty());
    }
    public ExactRef observedUnsettledLegacy(ActionCommand command,ActionState.Attempt attempt,
            NativeEventEffects.UnsettledObservation actual,ExactRef originalDispatch,RawJson proof)throws IOException {
        requireLegacyLive(command,attempt,actual.frames(),proof);
        ObjectNode data=object(StrictJson.parse(proof.bytes(),MAX_METADATA));
        require(data.path("observation_supporting_refs").isArray()&&data.path("observation_supporting_refs").isEmpty()
                &&originalDispatch.equals(ExactRef.fromJson(data.get("canonical_dispatch_ref"))),"legacy unsettled diagnostic changed its original dispatch or gained effect support");
        return observedUnsettledBound(command,attempt,actual,originalDispatch,Optional.of(proof));
    }
    private ExactRef observedUnsettledBound(ActionCommand command,ActionState.Attempt attempt,
            NativeEventEffects.UnsettledObservation actual,ExactRef originalDispatch,Optional<RawJson> legacy)throws IOException {
        require(handles(command),"actual captured event/interaction required");
        var pair=actual.frames();require(actual.dispatch().requestId().equals(attempt.requestId())
                &&pair.before().identity().equals(command.before())&&pair.before().source().equals(command.source())
                &&pair.before().sessionId().equals(command.sessionId())&&pair.before().originalEvidence().equals(attempt.guard().nativeEvidence())
                &&pair.after().identity().machineId().equals(command.before().machineId())&&pair.after().identity().game().equals(command.before().game())
                &&pair.after().identity().frame().episodeRunId().equals(command.before().frame().episodeRunId())
                &&pair.after().source().equals(command.source())&&pair.after().sessionId().equals(command.sessionId()),"unsettled observation crossed its actual original command/Game/source");
        verifyExternal(originalDispatch);var initial=NativeEffectEvidence.basis(pair.before());var ending=NativeEffectEvidence.basis(pair.after());
        for(ExactRef ref:List.of(initial.nativeFrame(),initial.driverFacts(),ending.nativeFrame(),ending.driverFacts()))verifyExternal(ref);
        Ticket ticket=legacy.isPresent()?legacyTicket(legacy.orElseThrow(),command):existing(command);
        return locked(()->{
            Path path=configured.incidentRoot().resolve(ticket.incidentId()+".unsettled.json");
            ObjectNode beforeIndex=object(read(ticket.index()));
            if(Files.exists(path,LinkOption.NOFOLLOW_LINKS)) {
                ExactRef retained=measure(path);ObjectNode prior=object(read(retained));validateUnsettled(prior,beforeIndex,ticket.before(),ticket.incidentId());
                require(ExactRef.fromJson(prior.get("original_dispatch_ref")).equals(originalDispatch),"unsettled original dispatch changed");return retained;
            }
            String field=ticket.kind()==Kind.EVENT?"active_event":"pending_character_interaction";
            ObjectNode old=object(object(DriverJson.toNode(pair.before().semantic(), DriverJson.MAX_NATIVE_BYTES)).get(field));
            JsonNode oldId=old.get("instance_id"),next=object(DriverJson.toNode(pair.after().semantic(), DriverJson.MAX_NATIVE_BYTES)).get(field);
            require(oldId!=null&&oldId.isIntegralNumber(),"original full native instance required");
            ObjectNode row=binding(ticket.origin());row.put("schema",legacy.isPresent()?LEGACY_RECOVERY_UNSETTLED_SCHEMA:UNSETTLED_SCHEMA).put("incident_id",ticket.incidentId()).put("kind",ticket.kind().name())
                    .put("action_id",command.actionId()).put("arguments_sha256",legacy.isPresent()?text(beforeIndex,"arguments_sha256"):digest(DriverJson.encode(indexedArguments(command,beforeIndex))))
                    .put("request_id",attempt.requestId()).put("observation_status","UNSETTLED").put("reason",actual.reason())
                    .put("independent_postcondition_verified",false).put("replay_allowed",false).put("observed_at_utc",pair.after().observedAt().toString());
            row.set("before_ref",ticket.before().toJson());row.set("before_frame",initial.nativeFrame().toJson());row.set("before_driver_facts",initial.driverFacts().toJson());
            row.set("after_frame",ending.nativeFrame().toJson());row.set("after_driver_facts",ending.driverFacts().toJson());
            row.set("after_observation",ProposalLifecycleCodec.observation(pair.after().identity()));row.set("original_dispatch_ref",originalDispatch.toJson());row.set("original_instance_id",oldId);
            if(next!=null&&next.isNull())row.put("original_instance_present",false);
            else if(next!=null&&next.isObject()&&next.path("instance_id").isIntegralNumber())row.put("original_instance_present",oldId.bigIntegerValue().equals(next.get("instance_id").bigIntegerValue()));
            else row.putNull("original_instance_present");
            row.putNull("native_ok");
            if(actual.dispatch() instanceof NativeActionPort.AckReceived ack) {
                row.put("dispatch_kind","ACK_RECEIVED").put("native_ok",ack.nativeOk());
            } else row.put("dispatch_kind",actual.dispatch() instanceof NativeActionPort.Unknown?"UNKNOWN":"REJECTED_BEFORE_DISPATCH");
            if(legacy.isPresent())row.set("legacy_command_binding",StrictJson.parse(legacy.orElseThrow().bytes(),MAX_METADATA));
            validateUnsettled(row,beforeIndex,ticket.before(),ticket.incidentId());return write(configured,path,encode(row));
        });
    }
    private void validateUnsettled(ObjectNode row,ObjectNode beforeIndex,ExactRef before,String id)throws IOException {
        boolean legacy=LEGACY_RECOVERY_UNSETTLED_SCHEMA.equals(text(row,"schema"));
        var fields=new java.util.HashSet<>(Set.of("session_id","origin","source","schema","incident_id","kind","action_id","arguments_sha256","request_id","observation_status","reason",
                "independent_postcondition_verified","replay_allowed","observed_at_utc","before_ref","before_frame","before_driver_facts","after_frame","after_driver_facts",
                "after_observation","original_dispatch_ref","original_instance_id","original_instance_present","native_ok","dispatch_kind"));
        if(legacy)fields.add("legacy_command_binding");StrictJson.object(row,fields);
        StrictJson.require(row.get("independent_postcondition_verified").isBoolean()&&!row.get("independent_postcondition_verified").booleanValue()
                &&row.get("replay_allowed").isBoolean()&&!row.get("replay_allowed").booleanValue(), "unsettled diagnostic changed or gained effect/replay credit");
        require((legacy||UNSETTLED_SCHEMA.equals(text(row,"schema")))&&id.equals(text(row,"incident_id"))&&"UNSETTLED".equals(text(row,"observation_status"))
                &&ExactRef.fromJson(row.get("before_ref")).equals(before)&&text(row,"action_id").equals(text(beforeIndex,"action_id"))
                &&text(row,"arguments_sha256").equals(text(beforeIndex,"arguments_sha256"))&&text(row,"kind").equals(text(beforeIndex,"kind")),"unsettled diagnostic changed or gained effect/replay credit");
        episode.requireEpisode(decodeBinding(row));StrictJson.text(row.get("request_id"));StrictJson.text(row.get("reason"));StrictJson.utc(text(row,"observed_at_utc"));
        require(row.get("original_instance_id").isIntegralNumber(),"original native instance integer required");
        for(String key:List.of("original_instance_present","native_ok"))require(row.get(key).isNull()||row.get(key).isBoolean(),"nullable actual diagnostic boolean required");
        require(Set.of("ACK_RECEIVED","UNKNOWN","REJECTED_BEFORE_DISPATCH").contains(text(row,"dispatch_kind")),"typed original dispatch kind required");
        require("ACK_RECEIVED".equals(text(row,"dispatch_kind"))==row.get("native_ok").isBoolean(),"actual ACK presence and native_ok value differ");
        ObservationIdentity after=ProposalLifecycleCodec.decodeObservation(row.get("after_observation"));Binding origin=decodeBinding(row);
        require(after.machineId().equals(origin.before().machineId())&&after.game().equals(origin.before().game())
                &&after.frame().episodeRunId().equals(origin.before().frame().episodeRunId()),"unsettled actual after crossed Game/episode");
        for(String key:List.of("before_frame","before_driver_facts","after_frame","after_driver_facts","original_dispatch_ref"))verifyExternal(ExactRef.fromJson(row.get(key)));
        if(legacy)verifyStoredLegacy(row,beforeIndex,before,"after_frame");
    }
    /** Reads actual incident originals; no Driver history or absent directory is an empty scan. */
    public Scan scan(Binding actual) throws IOException { return scan(actual, Optional.empty()); }
    /** Current full-frame original from the identical Root archive; retained-only scans cannot invent progress. */
    public Scan scan(Binding actual, Optional<ExactRef> currentBasis) throws IOException {
        return scan(actual, Objects.requireNonNull(currentBasis), Optional.empty());
    }
    /** Preserve current recovery progress synchronously only when the actual inventory contains an incident/window. */
    public Scan scanWithProgress(Binding actual, ProgressOriginal progress) throws IOException {
        return scan(actual, Optional.empty(), Optional.of(Objects.requireNonNull(progress)));
    }
    private Scan scan(Binding actual, Optional<ExactRef> currentBasis, Optional<ProgressOriginal> deferred) throws IOException {
        episode.requireEpisode(actual); verifyEpisode();
        if (currentBasis.isPresent()) requireProgress(actual, currentBasis.orElseThrow());
        return locked(() -> {
            List<Path> files;
            try (var listing = Files.list(configured.incidentRoot())) { files = listing.sorted().toList(); }
            require(files.size() <= 1282, "Finite episode incident inventory exceeded");
            List<ExactRef> originals = new ArrayList<>(); List<ObjectNode> incidents = new ArrayList<>(); Set<String> indexedIds = new java.util.HashSet<>(); int incomplete = 0, diagnosticOnly = 0; long bytes = 0;
            Optional<ExactRef> originalBasis = originalObservationBasis();
            if (originalBasis.isPresent()) { ExactRef ref = originalBasis.orElseThrow(); require(ref.bytes() <= MAX_METADATA, "Bounded typed original basis required"); verifyExternal(ref); originals.add(ref); }
            for (Path path : files) {
                plain(path); require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS), "Incident root contains an unexpected entry");
                String filename = path.getFileName().toString();
                if (filename.equals(".incident.lock") || filename.matches("incidents-[0-9a-f]{64}[.]batch[.]json")) continue;
                require(filename.equals("EPISODE.json") || filename.matches("[0-9a-f]{32}[.](?:before|after|before-index|after-index|review-index|unsettled)[.]json"), "Unknown incident-directory entry requires reconciliation");
                ExactRef pin = measure(path); bytes = Math.addExact(bytes, pin.bytes()); require(bytes <= MAX_SCAN_BYTES, "Incident scan byte limit exceeded");
                originals.add(pin);
                if (!path.getFileName().toString().endsWith(".before-index.json")) continue;
                ObjectNode index = object(read(pin)); ReadOriginals readOriginal = beforeIndexRead(index);
                for (ExactRef ref : readOriginal.refs()) if (!originals.contains(ref)) {
                    originals.add(ref); bytes = Math.addExact(bytes, ref.bytes());
                    require(bytes <= MAX_SCAN_BYTES, "Incident read-original scan byte limit exceeded");
                }
                Binding origin = decodeBinding(index); episode.requireEpisode(origin);
                String id = text(index, "incident_id"); require(id.matches("[0-9a-f]{32}"), "Original incident identity required");
                require(filename.equals(id + ".before-index.json"), "Original incident filename/identity differs");
                require(indexedIds.add(id), "Duplicate incident index identity");
                Kind kind = Kind.valueOf(text(index, "kind")); ExactRef beforeRef = ExactRef.fromJson(index.get("before_ref"));
                require(Path.of(beforeRef.path()).equals(configured.incidentRoot().resolve(id + ".before.json")), "Original before escaped the episode root");
                byte[] originalBeforeBody=read(beforeRef);ObjectNode before = object(originalBeforeBody); require(id.equals(text(before, "incident_id")), "Original before incident ID differs");
                Path unsettled=configured.incidentRoot().resolve(id+".unsettled.json");
                if(Files.exists(unsettled,LinkOption.NOFOLLOW_LINKS))validateUnsettled(object(read(measure(unsettled))),index,beforeRef,id);
                boolean diagnostic = "planning_diagnostic".equals(index.path("capture_stage").asText());
                if (diagnostic) { require(index.path("action_id").isNull(), "Blocked diagnosis cannot claim an action ID"); ExactRef frame = ExactRef.fromJson(index.get("original_frame_ref")); verifyExternal(frame); if (!originals.contains(frame)) originals.add(frame); diagnosticOnly++; }
                boolean reviewed = false;
                Path reviewedPath = configured.incidentRoot().resolve(id + ".review-index.json");
                if (Files.exists(reviewedPath, LinkOption.NOFOLLOW_LINKS)) {
                    ObjectNode review = object(read(measure(reviewedPath)));
                    require("xar.episode-incident-reviewed/v1".equals(text(review, "schema"))
                            && ExactRef.fromJson(review.get("before_ref")).equals(beforeRef), "Original reviewed incident binding differs");
                    episode.requireEpisode(decodeBinding(review)); read(ExactRef.fromJson(review.get("report_ref")));
                    reviewed = true;
                }
                if (before.path("registry_known").isBoolean() && before.path("registry_known").booleanValue()
                        && before.path("offline_followup_required").isBoolean() && !before.path("offline_followup_required").booleanValue()) reviewed = true;
                ObjectNode item = StrictJson.object().put("incident_id", id).put("kind", kind == Kind.MANDATORY
                        ? "unknown_mandatory_choice" : kind == Kind.EVENT ? "unhandled_event" : "pending_character_interaction");
                item.put("before", beforeRef.path()).put("before_sha256", beforeRef.sha256());
                if (kind == Kind.EVENT) { item.set("event_definition_key", before.get("event_definition_key")); item.set("current_event_instance_id", before.get("current_event_instance_id")); }
                else if (kind == Kind.INTERACTION) item.set("interaction_definition_key", before.get("interaction_definition_key"));
                Path afterIndex = configured.incidentRoot().resolve(id + ".after-index.json");
                if (Files.exists(afterIndex, LinkOption.NOFOLLOW_LINKS)) {
                    ObjectNode after = object(read(measure(afterIndex))); require(ExactRef.fromJson(after.get("before_ref")).equals(beforeRef), "Original after lost before pin");
                    episode.requireEpisode(decodeBinding(after)); ExactRef afterRef = ExactRef.fromJson(after.get("after_ref"));
                    require(Path.of(afterRef.path()).equals(configured.incidentRoot().resolve(id + ".after.json")), "Original after escaped episode root");
                    byte[] originalAfterBody=read(afterRef);ObjectNode afterBody = object(originalAfterBody); require(id.equals(text(afterBody, "incident_id")), "Original after incident ID differs");
                    ObservationIdentity afterIdentity = ProposalLifecycleCodec.decodeObservation(after.get("after_observation"));
                    require(afterIdentity.machineId().equals(origin.before().machineId()) && afterIdentity.game().equals(origin.before().game())
                            && afterIdentity.frame().episodeRunId().equals(origin.before().frame().episodeRunId()), "Original independent after crossed Game/episode");
                    verifyExternal(ExactRef.fromJson(after.get("after_frame")));
                    require(after.path("independent_postcondition_verified").isBoolean() && after.path("independent_postcondition_verified").booleanValue()
                            && after.path("supporting_refs").isArray() && !after.path("supporting_refs").isEmpty(), "Original independent after basis missing");
                    for (JsonNode supporting : after.get("supporting_refs")) verifyExternal(ExactRef.fromJson(supporting));
                    verifyPolicyReceipt(after,index,originalBeforeBody,originalAfterBody);
                    item.put("after", afterRef.path()).put("after_sha256", afterRef.sha256());
                } else { item.putNull("after").putNull("after_sha256"); if (!diagnostic) incomplete++; }
                if (!reviewed) incidents.add(item);
                require(indexedIds.size() <= 256, "Bounded actual captured episode incidents required");
            }
            // Reject orphaned/torn bodies instead of silently recording a source-bound empty batch.
            Set<String> indexed = Set.copyOf(indexedIds);
            for (Path path : files) {
                String name = path.getFileName().toString();
                if (name.endsWith(".before.json") || name.endsWith(".after.json") || name.endsWith(".after-index.json") || name.endsWith(".review-index.json") || name.endsWith(".unsettled.json"))
                    require(indexed.stream().anyMatch(id -> name.startsWith(id + ".")), "Orphan/torn incident requires reconciliation before scan");
            }
            // Later full-frame progress serves captured incident recovery; an empty inventory has no recovery to review.
            Optional<ExactRef> progress = indexedIds.isEmpty() ? Optional.empty() : deferred.isPresent()
                    ? Optional.of(Objects.requireNonNull(deferred.orElseThrow().preserve())) : currentBasis;
            if (deferred.isPresent() && progress.isPresent()) requireProgress(actual, progress.orElseThrow());
            if (progress.isPresent() && !originals.contains(progress.orElseThrow())) originals.add(progress.orElseThrow());
            ObjectNode scan = binding(actual); scan.put("schema", progress.isPresent() ? "xar.episode-incident-scan/v3" : SCAN_SCHEMA).put("incidents", incidents.size())
                    .put("captured_incidents", indexedIds.size()).put("incomplete_after", incomplete).put("diagnostic_only", diagnosticOnly);
            scan.set("episode_ref", episodeRef.toJson());
            progress.ifPresent(ref -> scan.set("scan_observation_basis", ref.toJson()));
            var refs = scan.putArray("original_refs"); originals.forEach(ref -> refs.add(ref.toJson()));
            byte[] scanRaw = encode(scan); String scanId = digest(scanRaw);
            ExactRef scanRef = writeSame(configured.scanRoot().resolve(scanId + ".scan.json"), scanRaw);
            Optional<BatchRequest> request = Optional.empty();
            if (!incidents.isEmpty()) {
                var observed = observedScan(actual, scanRef);
                ObjectNode manifest = StrictJson.object().put("schema", OfflineBatchBinding.manifestSchema(observed)).put("session_id", actual.sessionId());
                manifest.set("scan_observation", observed.observation().toJson()); manifest.set("scan_source", observed.source().toJson());
                manifest.set("index_ref", scanRef.toJson()); var rows = manifest.putArray("new_incidents"); incidents.forEach(rows::add);
                byte[] raw = encode(manifest); String batchId = "incidents-" + digest(raw);
                ExactRef manifestRef = writeSame(configured.scanRoot().resolve(batchId + ".batch.json"), raw);
                List<ExactRef> captured = new ArrayList<>();
                for (ObjectNode item : incidents) for (String stage : List.of("before", "after")) if (item.get(stage).isTextual()) {
                    ExactRef ref = measure(Path.of(item.get(stage).textValue())); require(ref.sha256().equals(text(item, stage + "_sha256")), "Captured original changed before batch publication"); captured.add(ref);
                }
                request = Optional.of(new BatchRequest(batchId, manifestRef, captured));
            }
            for (ExactRef original : originals) verifyExternal(original); verifyEpisode();
            return new Scan(actual, episodeRef, scanRef, request, originals, incidents.size(), indexedIds.size(), incomplete, diagnosticOnly);
        });
    }
    /** Maps the existing in-memory carrier to its sole versioned wire contract. */
    private static IncidentReadIndex.Value indexReadValue(ReadOriginals original) {
        if (original instanceof KnownRead known) return new IncidentReadIndex.KnownReceipt(known.original());
        if (original instanceof FailedRead failed) {
            var value = failed.original();
            return new IncidentReadIndex.FailedQuery(value.originalOutcome(), value.preparedRequest(),
                    value.observedFailure(), value.dependencies());
        }
        return IncidentReadIndex.None.INSTANCE;
    }
    /** v1 has no read proof; v2 has a successful receipt; v3 retains a failed outcome/request pair. */
    private static ReadOriginals beforeIndexRead(ObjectNode row) throws IOException {
        try {
            var decoded = IncidentReadIndex.decode(row);
            ReadOriginals result;
            if (decoded instanceof IncidentReadIndex.KnownReceipt known) result = new KnownRead(known.original());
            else if (decoded instanceof IncidentReadIndex.FailedQuery failed) result = new FailedRead(new FailedReadReferences(
                    failed.originalOutcome(), failed.preparedRequest(), failed.observedFailure(), failed.dependencies()));
            else result = NoRead.INSTANCE;
            verifyReadOriginals(result); return result;
        } catch (IllegalArgumentException malformed) { throw new IOException("Malformed versioned before-index read originals", malformed); }
    }
    private static void verifyReadOriginals(ReadOriginals original) throws IOException {
        if (original instanceof KnownRead known) require(known.original().bytes() > 0 && known.original().bytes() <= MAX_METADATA,
                "Bounded actual private receipt required");
        for (ExactRef ref : original.refs()) verifyExternal(ref);
    }

    /** Strict sole versioned decoder plus the caller's observed-scan guard, shared with actual Root ACK. */
    public static OfflineBatchBinding.ObservedScan requireBatchManifest(JsonNode manifest)throws IOException {
        try{var decoded=OfflineBatchBinding.manifest(manifest);if(decoded instanceof OfflineBatchBinding.ObservedScan observed)return observed;throw new IOException("Actual observed incident scan required; historical completed sequence is not a scan");}
        catch(IllegalArgumentException invalid){throw new IOException("Malformed versioned original incident scan",invalid);}
    }
    private static OfflineBatchBinding.ObservedScan observedScan(Binding actual,ExactRef index){
        var identity=actual.before();var frame=identity.frame();var nativeFrame=frame.identity();
        // Already typed actual public actor: preserve its signed value; never reinterpret it as uint64.
        var value=new OfflineBatchBinding.Frame(NativeCharacterId.of(nativeFrame.player()),
                new CrossJsDecimalUInt64(nativeFrame.nativeRevision().toString()),new CrossJsDecimalUInt64(nativeFrame.dateRaw().toString()),
                frame.snapshotId(),new CrossJsDecimalUInt64(frame.revision().toString()),frame.episodeRunId());
        var observation=new OfflineBatchBinding.Observation(identity.machineId(),identity.game(),identity.observationVersion(),value);
        var source=actual.source();return new OfflineBatchBinding.ObservedScan(actual.sessionId(),observation,
                new OfflineBatchBinding.Source(source.machineId(),source.observedAtUtc(),source.exactBuild(),source.sourceRef()),index);
    }
    /** The offline host calls this only after its real source-review publication; unresolved IDs remain pending. */
    public void acknowledge(BatchRequest original, ExactRef actualReport) throws IOException {
        ObjectNode manifest = object(read(original.manifestRef()));
        OfflineBatchBinding.ObservedScan observed=requireBatchManifest(manifest);
        // Internal G2 observations deliberately retain their signed-decimal actor representation.
        // This explicit memory-domain projection never rewrites the manifest's versioned original bytes.
        ObjectNode internal=observed.observation().toJson();((ObjectNode)internal.get("frame")).put("played_character_id",observed.observation().frame().playedCharacterId().decimal());
        Binding scanned=new Binding(ProposalLifecycleCodec.decodeObservation(internal),source(observed.source().toJson()),observed.sessionId());episode.requireEpisode(scanned);
        ObjectNode retainedScan = object(read(observed.indexRef()));
        require(Set.of(SCAN_SCHEMA, "xar.episode-incident-scan/v3").contains(text(retainedScan, "schema")) && retainedScan.path("original_refs").isArray(), "Original observed scan required at source-review completion");
        List<ExactRef> originalRefs = new ArrayList<>();
        for (JsonNode value : retainedScan.get("original_refs")) {
            ExactRef ref = ExactRef.fromJson(value); verifyExternal(ref); originalRefs.add(ref);
        }
        ObjectNode report = object(read(actualReport));
        try{OfflineBatchBinding.requireReport(report,observed,original.manifestRef());}
        catch(IllegalArgumentException invalid){throw new IOException("Source-review report crossed its actual versioned manifest binding",invalid);}
        require(report.path("entries").isArray() && report.path("already_known").isArray() && report.path("unresolved").isArray(), "Complete actual source-review classification required");
        Set<String> unresolved = new java.util.HashSet<>(), complete = new java.util.HashSet<>();
        for (JsonNode row : report.path("unresolved")) unresolved.add(text(row, "incident_id"));
        for (String field : List.of("entries", "already_known")) for (JsonNode row : report.get(field)) complete.add(text(row, "incident_id"));
        complete.removeAll(unresolved);
        locked(() -> {
            for (JsonNode item : manifest.path("new_incidents")) {
                String id = text(item, "incident_id"); if (!complete.contains(id)) continue;
                ExactRef before = original.capturedRefs().stream().filter(ref -> ref.path().equals(text(item, "before"))).findFirst()
                        .orElseThrow(() -> new IOException("Reviewed incident lacks its captured original"));
                require(before.sha256().equals(text(item, "before_sha256")), "Reviewed incident before SHA differs"); read(before);
                Path indexPath = configured.incidentRoot().resolve(id + ".before-index.json");
                ExactRef indexRef = originalRefs.stream().filter(ref -> Path.of(ref.path()).equals(indexPath)).findFirst()
                        .orElseThrow(() -> new IOException("Reviewed incident lacks its scanned original before index"));
                beforeIndexRead(object(read(indexRef)));
                ObjectNode row = binding(scanned); row.put("schema", "xar.episode-incident-reviewed/v1").put("incident_id", id);
                row.set("before_ref", before.toJson()); row.set("report_ref", actualReport.toJson());
                writeSame(configured.incidentRoot().resolve(id + ".review-index.json"), encode(row));
            }
            return null;
        });
    }
    private static final Set<String> LEGACY_FIELDS=Set.of("schema","episode_ref","scan_ref","original_index","original_before",
            "canonical_receipt_ref","canonical_record_ref","canonical_dispatch_ref","canonical_command_base64","canonical_command_sha256",
            "canonical_arguments_sha256","recorded_arguments_sha256","reconciliation_guard","observation_supporting_refs");
    private static boolean legacyPhase(ActionCommand command) {
        if(!(command.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay)
                ||!new OpportunityJson.Text("active_event_unhandled_first_rendered_option").equals(command.arguments().get("phase"))
                ||!command.operation().value().matches("select-event-option-[1-9][0-9]{0,8}"))return false;
        if(!(command.arguments().get("unhandled_event_fallback") instanceof OpportunityJson.Obj capture))return false;
        return new OpportunityJson.Text("user-authorized-capture-then-first-rendered-option").equals(capture.get("policy"))
                &&new OpportunityJson.Bool(false).equals(capture.get("registry_known"))
                &&capture.get("source_knowledge") instanceof OpportunityJson.Obj knowledge
                &&new OpportunityJson.Text("unknown").equals(knowledge.get("status"));
    }
    /** Absence only: corrupt/ambiguous existing paths never enter semantic compatibility. */
    public boolean legacyLookupRequired(ActionCommand command)throws IOException {
        if(!legacyPhase(command))return false;
        var canonical=incidentArguments(command);Path selected=originalIndexPath(command,canonical);
        return Files.notExists(selected,LinkOption.NOFOLLOW_LINKS)
                &&Files.notExists(configured.incidentRoot().resolve(incidentId(command.actionId(),digest(DriverJson.encode(command.arguments())))+".before-index.json"),LinkOption.NOFOLLOW_LINKS);
    }
    public RawJson prepareLegacyBinding(ActionCommand command,ActionState.Attempt attempt,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete before,RawJson canonicalEvidence)throws IOException {
        require(legacyPhase(command)&&legacyLookupRequired(command),"legacy compatibility is restricted to an absent exact unhandled EVENT original");
        var identity=org.xar.ck3.control.application.action.ActionReconciliationScope.requireIdentity(command,attempt);
        var guard=org.xar.ck3.control.application.action.ActionReconciliationScope.requireObservationGuard(command,attempt);
        require(identity.driverRelation()==org.xar.ck3.control.application.action.ReconciliationIdentity.DriverRelation.EXACT,"legacy EVENT history append is not authorized");
        ObjectNode proof=object(StrictJson.parse(canonicalEvidence.bytes(),MAX_METADATA));
        require(ExactRef.fromJson(proof.get("canonical_receipt_ref")).equals(identity.pending().originalReceipt())
                &&org.xar.ck3.control.application.action.CommandOriginCodec.guard(proof.get("reconciliation_guard")).equals(guard),"legacy canonical evidence did not come from this issued observation");
        Scan pinned=scan(new Binding(command.before(),command.source(),command.sessionId()));
        List<ExactRef> candidates=new ArrayList<>();
        for(ExactRef ref:pinned.originals())if(ref.path().endsWith(".before-index.json")) {
            ObjectNode row=object(read(ref));
            if(command.actionId().equals(row.path("action_id").asText()))candidates.add(ref);
        }
        require(candidates.size()==1,"one exact original in the fully pinned legacy scan required");
        ExactRef index=candidates.getFirst();ObjectNode row=object(read(index));ExactRef oldBefore=ExactRef.fromJson(row.get("before_ref"));
        proof.set("episode_ref",episodeRef.toJson());proof.set("scan_ref",pinned.indexRef().toJson());
        proof.set("original_index",index.toJson());proof.set("original_before",oldBefore.toJson());proof.put("recorded_arguments_sha256",text(row,"arguments_sha256"));
        RawJson result=new RawJson(StrictJson.canonical(proof,MAX_METADATA));
        verifyLegacyBindingData(result,command,before);verifyLegacyAuthority(result);
        for(ExactRef ref:pinned.originals())verifyExternal(ref);verifyExternal(pinned.indexRef());verifyEpisode();
        return result;
    }
    /** Fully verified owned original DATA only; only the installed Root may reconstruct an archived effect from it. */
    public Optional<RawJson> existingLegacyAfter(ActionCommand command)throws IOException {
        if(!legacyPhase(command)||!legacyLookupRequired(command))return Optional.empty();
        List<Path> inventory;try(var files=Files.list(configured.incidentRoot())){inventory=files.sorted().toList();}
        require(inventory.size()<=1282,"bounded existing legacy incident inventory required");
        Scan pinned=scan(new Binding(command.before(),command.source(),command.sessionId()));
        List<ExactRef> candidates=new ArrayList<>();
        for(ExactRef original:pinned.originals())if(original.path().endsWith(".before-index.json")) {
            ObjectNode index=object(read(original));
            if(command.actionId().equals(index.path("action_id").asText()))candidates.add(original);
        }
        require(candidates.size()==1,"one fully validated owned original event is required");
        ExactRef beforeIndex=candidates.getFirst();ObjectNode original=object(read(beforeIndex));String id=text(original,"incident_id");
        Path afterPath=configured.incidentRoot().resolve(id+".after.json"),indexPath=configured.incidentRoot().resolve(id+".after-index.json");
        boolean hasAfter=Files.exists(afterPath,LinkOption.NOFOLLOW_LINKS),hasIndex=Files.exists(indexPath,LinkOption.NOFOLLOW_LINKS);
        require(hasAfter==hasIndex,"partial existing event after requires reconciliation");
        if(!hasAfter) {
            for(ExactRef ref:pinned.originals())verifyExternal(ref);verifyExternal(pinned.indexRef());verifyEpisode();
            verifyLegacyCandidateInventory(command,beforeIndex);
            try(var files=Files.list(configured.incidentRoot())){require(files.sorted().toList().equals(inventory),"existing event inventory changed before absence");}
            return Optional.empty();
        }
        ExactRef afterIndex=measure(indexPath),after=measure(afterPath);ObjectNode index=object(read(afterIndex));
        require(pinned.originals().contains(beforeIndex)&&pinned.originals().contains(afterIndex)&&pinned.originals().contains(after)
                &&LEGACY_RECOVERY_AFTER_SCHEMA.equals(text(index,"schema"))
                &&after.equals(ExactRef.fromJson(index.get("after_ref")))
                &&ExactRef.fromJson(original.get("before_ref")).equals(ExactRef.fromJson(index.get("before_ref"))),
                "existing event after escaped its validated original inventory");
        ObjectNode proof=object(index.get("legacy_command_binding"));
        byte[] encoded=java.util.Base64.getDecoder().decode(text(proof,"canonical_command_base64"));
        require(java.util.Arrays.equals(encoded,ActionCodec.encodeCommand(command))
                &&ActionCodec.bodySha256(command).equals(text(proof,"canonical_command_sha256"))
                &&beforeIndex.equals(ExactRef.fromJson(proof.get("original_index")))
                &&ExactRef.fromJson(original.get("before_ref")).equals(ExactRef.fromJson(proof.get("original_before")))
                &&index.path("supporting_refs").isArray()&&index.path("supporting_refs").size()==1
                &&index.get("supporting_refs").equals(proof.get("observation_supporting_refs")),
                "existing event after changed its complete original command or owned proof");
        var basis=NativeEffectEvidence.reconciliationProvenance(new RawJson(read(ExactRef.fromJson(index.get("supporting_refs").get(0)))));
        require(basis.isPresent(),"existing legacy event after requires its explicit original READ profile");
        for(ExactRef ref:pinned.originals())verifyExternal(ref);verifyExternal(pinned.indexRef());verifyEpisode();
        verifyLegacyCandidateInventory(command,beforeIndex);
        try(var files=Files.list(configured.incidentRoot())){require(files.sorted().toList().equals(inventory),"existing event inventory changed during validation");}
        ObjectNode result=StrictJson.object().put("schema","xar.episode-incident-existing-after/v1");
        result.set("scan_ref",pinned.indexRef().toJson());result.set("before_index",beforeIndex.toJson());
        result.set("after_index",afterIndex.toJson());result.set("after",after.toJson());
        return Optional.of(new RawJson(StrictJson.canonical(result,MAX_METADATA)));
    }
    /** Pure original DATA checking. It does not enter a reconciliation scope or issue an effect/permit. */
    public void verifyLegacyBindingData(RawJson serialized,ActionCommand command,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete before)throws IOException {
        require(legacyPhase(command),"legacy recovery is not a dedicated policy, interaction or mandatory receipt exemption");
        ObjectNode proof=StrictJson.object(StrictJson.parse(serialized.bytes(),MAX_METADATA),LEGACY_FIELDS);
        require(LEGACY_BINDING_SCHEMA.equals(text(proof,"schema")),"versioned legacy compatibility proof required");
        byte[] encoded=java.util.Base64.getDecoder().decode(text(proof,"canonical_command_base64"));
        require(encoded.length>0&&encoded.length<=ActionCodec.MAX_COMMAND_BYTES
                &&java.util.Base64.getEncoder().encodeToString(encoded).equals(text(proof,"canonical_command_base64"))
                &&java.util.Arrays.equals(encoded,ActionCodec.encodeCommand(command))
                &&digest(encoded).equals(text(proof,"canonical_command_sha256"))
                &&digest(DriverJson.encode(incidentArguments(command))).equals(text(proof,"canonical_arguments_sha256")),"legacy proof changed the complete canonical original command");
        require(before.identity().equals(command.before())&&before.source().equals(command.source())&&before.sessionId().equals(command.sessionId()),"legacy actual before differs from canonical original");
        for(String field:List.of("canonical_receipt_ref","canonical_record_ref","canonical_dispatch_ref"))verifyExternal(ExactRef.fromJson(proof.get(field)));
        require(proof.path("observation_supporting_refs").isArray()&&proof.path("observation_supporting_refs").size()<=1,"bounded explicit legacy observation supports required");
        for(JsonNode ref:proof.get("observation_supporting_refs"))verifyExternal(ExactRef.fromJson(ref));
        require(episodeRef.equals(ExactRef.fromJson(proof.get("episode_ref"))),"legacy proof crossed the exact original episode");verifyEpisode();
        ExactRef scanRef=ExactRef.fromJson(proof.get("scan_ref"));
        require(Path.of(scanRef.path()).getParent().equals(configured.scanRoot()),"legacy scan escaped configured scan root");
        ObjectNode scan=object(read(scanRef));episode.requireEpisode(decodeBinding(scan));
        require(Set.of(SCAN_SCHEMA,"xar.episode-incident-scan/v3").contains(text(scan,"schema"))
                &&episodeRef.equals(ExactRef.fromJson(scan.get("episode_ref")))&&scan.path("original_refs").isArray(),"legacy proof lacks its exact original validated scan");
        ExactRef index=ExactRef.fromJson(proof.get("original_index")),oldBefore=ExactRef.fromJson(proof.get("original_before"));
        boolean hasIndex=false,hasBefore=false;long total=0;int count=0;
        for(JsonNode value:scan.get("original_refs")) {
            require(++count<=4096,"bounded legacy scan inventory required");ExactRef ref=ExactRef.fromJson(value);verifyExternal(ref);
            total=Math.addExact(total,ref.bytes());require(total<=MAX_SCAN_BYTES,"legacy original scan byte limit exceeded");
            hasIndex|=ref.equals(index);hasBefore|=ref.equals(oldBefore);
        }
        require(hasIndex&&hasBefore,"legacy selected originals are absent from its pinned complete scan");
        verifyLegacyCandidateInventory(command,index);
        ObjectNode old=object(read(index));require(beforeIndexRead(old)==NoRead.INSTANCE,"legacy EVENT cannot change its original query role");
        String recorded=text(proof,"recorded_arguments_sha256");require(recorded.matches("[0-9a-f]{64}")&&recorded.equals(text(old,"arguments_sha256")),"legacy recorded commitment changed");
        String id=incidentId(command.actionId(),recorded);
        require("EVENT".equals(text(old,"kind"))&&command.actionId().equals(text(old,"action_id"))
                &&decodeBinding(old).equals(new Binding(command.before(),command.source(),command.sessionId()))
                &&id.equals(text(old,"incident_id"))&&Path.of(index.path()).equals(configured.incidentRoot().resolve(id+".before-index.json"))
                &&oldBefore.equals(ExactRef.fromJson(old.get("before_ref")))&&Path.of(oldBefore.path()).equals(configured.incidentRoot().resolve(id+".before.json")),"legacy original index/before/source identity differs");
        ObjectNode body=object(read(oldBefore));ObjectNode capture=object(DriverJson.toNode(command.arguments()).get("unhandled_event_fallback"));
        validateCaptureBinding(command.before(),capture);
        capture.properties().forEach(field->StrictJson.require(java.util.Objects.equals(field.getValue(),body.get(field.getKey())),"legacy original capture field changed: "+field.getKey()));
        var extra=Set.of("incident_id","stage","captured_at_utc","dispatch_attempted");
        body.properties().forEach(field->StrictJson.require(capture.has(field.getKey())||extra.contains(field.getKey()),"legacy original capture gained an unknown field"));
        require(id.equals(text(body,"incident_id"))&&"before_submission".equals(text(body,"stage"))&&body.path("dispatch_attempted").isBoolean()
                &&!body.path("dispatch_attempted").booleanValue(),"legacy before envelope changed its original dispatch role");StrictJson.utc(text(body,"captured_at_utc"));
        var guard=org.xar.ck3.control.application.action.CommandOriginCodec.guard(proof.get("reconciliation_guard"));
        require(guard.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Reconciliation,"legacy proof requires an actual reconciliation guard");
        var identity=guard.origin().requireReconciliation();
        require(identity.driverRelation()==org.xar.ck3.control.application.action.ReconciliationIdentity.DriverRelation.EXACT
                &&identity.pending().actionId().equals(command.actionId())&&identity.pending().bodySha256().equals(text(proof,"canonical_command_sha256"))
                &&identity.pending().originalReceipt().equals(ExactRef.fromJson(proof.get("canonical_receipt_ref")))
                &&identity.pending().originalBefore().equals(command.before())&&identity.source().equals(command.source())&&identity.sessionId().equals(command.sessionId()),"legacy guard changed its canonical original role");
        verifyExternal(index);verifyExternal(oldBefore);verifyExternal(scanRef);verifyEpisode();verifyLegacyCandidateInventory(command,index);
    }
    private void verifyLegacyAuthority(RawJson proof)throws IOException {
        var verifier=configured.legacyVerifier().orElseThrow(()->new IOException("legacy compatibility requires the installed actual Root verifier"));
        verifier.accept(proof);
    }
    private Ticket legacyTicket(RawJson serialized,ActionCommand command)throws IOException {
        ObjectNode proof=object(StrictJson.parse(serialized.bytes(),MAX_METADATA));ExactRef index=ExactRef.fromJson(proof.get("original_index"));
        ObjectNode row=object(read(index));return new Ticket(text(row,"incident_id"),Kind.EVENT,ExactRef.fromJson(proof.get("original_before")),index,new Binding(command.before(),command.source(),command.sessionId()));
    }
    private void requireLegacyLive(ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair pair,RawJson proof)throws IOException {
        var identity=org.xar.ck3.control.application.action.ActionReconciliationScope.requireIdentity(command,attempt);
        var guard=org.xar.ck3.control.application.action.ActionReconciliationScope.requireObservationGuard(command,attempt);
        ObjectNode row=object(StrictJson.parse(proof.bytes(),MAX_METADATA));
        require(org.xar.ck3.control.application.action.CommandOriginCodec.guard(row.get("reconciliation_guard")).equals(guard)
                &&pair.after().identity().equals(identity.factual())&&pair.after().originalEvidence().equals(identity.nativeEvidence())
                &&pair.after().source().equals(identity.source())&&pair.after().sessionId().equals(identity.sessionId()),"legacy observer escaped its exact issued actual frame/guard");
        verifyLegacyBindingData(proof,command,pair.before());verifyLegacyAuthority(proof);
    }
    private void verifyStoredLegacy(ObjectNode row,ObjectNode beforeIndex,ExactRef before,String afterFrameField)throws IOException {
        require(row.get("legacy_command_binding") instanceof ObjectNode,"versioned legacy original proof required");
        RawJson proof=new RawJson(StrictJson.canonical(row.get("legacy_command_binding"),MAX_METADATA));ObjectNode data=object(StrictJson.parse(proof.bytes(),MAX_METADATA));
        var command=ActionCodec.decodeCommand(java.util.Base64.getDecoder().decode(text(data,"canonical_command_base64")));
        require(legacyPhase(command)&&before.equals(ExactRef.fromJson(data.get("original_before")))
                &&object(read(ExactRef.fromJson(data.get("original_index")))).equals(beforeIndex),"stored legacy proof changed its exact original before/index");
        var guard=org.xar.ck3.control.application.action.CommandOriginCodec.guard(data.get("reconciliation_guard"));
        require(guard.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Reconciliation
                &&guard.origin().requireReconciliation().factual().equals(ProposalLifecycleCodec.decodeObservation(row.get("after_observation")))
                &&guard.nativeEvidence().equals(ExactRef.fromJson(row.get(afterFrameField))),"stored legacy proof changed its actual qualified after");
        if(LEGACY_RECOVERY_AFTER_SCHEMA.equals(text(row,"schema"))) {
            require(row.path("supporting_refs").isArray()&&row.path("supporting_refs").size()==1
                    &&row.get("supporting_refs").equals(data.get("observation_supporting_refs")),"stored legacy after changed its qualified effect closure");
        } else {
            require(data.path("observation_supporting_refs").isArray()&&data.path("observation_supporting_refs").isEmpty()
                    &&ExactRef.fromJson(row.get("original_dispatch_ref")).equals(ExactRef.fromJson(data.get("canonical_dispatch_ref"))),"stored legacy unsettled changed its original dispatch or gained effect credit");
        }
        verifyLegacyAuthority(proof);
    }
    /** A negative ambiguity fence over the bounded current inventory, never an accepting id-only lookup. */
    private void verifyLegacyCandidateInventory(ActionCommand command,ExactRef selected)throws IOException {
        List<Path> paths;try(var files=Files.list(configured.incidentRoot())){paths=files.sorted().toList();}
        require(paths.size()<=1026,"bounded current legacy inventory required");List<ExactRef> pins=new ArrayList<>();long bytes=0;int candidates=0;
        for(Path path:paths) {
            plain(path);require(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS),"legacy inventory contains a non-original entry");String name=path.getFileName().toString();
            if(name.equals(".incident.lock")||name.matches("incidents-[0-9a-f]{64}[.]batch[.]json"))continue;
            require(name.equals("EPISODE.json")||name.matches("[0-9a-f]{32}[.](?:before|after|before-index|after-index|review-index|unsettled)[.]json"),"legacy inventory contains an unknown entry");
            ExactRef pin=measure(path);pins.add(pin);bytes=Math.addExact(bytes,pin.bytes());require(bytes<=MAX_SCAN_BYTES,"legacy inventory byte limit exceeded");
            if(name.endsWith(".before-index.json")) {
                ObjectNode row=object(read(pin));episode.requireEpisode(decodeBinding(row));
                if(command.actionId().equals(row.path("action_id").asText())) {candidates++;require(pin.equals(selected),"another current legacy candidate conflicts with the selected exact original");}
            }
        }
        require(candidates==1,"one unchanged explicit legacy original required");for(ExactRef pin:pins)verifyExternal(pin);
        try(var files=Files.list(configured.incidentRoot())){require(files.sorted().toList().equals(paths),"legacy inventory changed during verification");}
    }
    private Ticket existing(ActionCommand command) throws IOException {
        require(handles(command), "Actual original fallback command required");
        return readTicket(command, originalIndexPath(command, incidentArguments(command)));
    }
    /** The command codec already owns its persistent argument representation; no hash or parser is changed. */
    private static OpportunityJson.Obj incidentArguments(ActionCommand command) {
        var arguments = OpportunityJson.object(DriverJson.object(ActionCodec.encodeCommand(command), ActionCodec.MAX_COMMAND_BYTES).get("arguments"), "original incident command arguments");
        StrictJson.require(arguments.equals(command.arguments()), "Incident command codec changed typed arguments");
        return arguments;
    }
    private static String incidentId(String actionId, String argumentsHash) {
        return digest((actionId + "|" + argumentsHash).getBytes(java.nio.charset.StandardCharsets.UTF_8)).substring(0, 32);
    }
    /** Only the exact original raw lane and the existing command-codec lane may name an original. */
    private Path originalIndexPath(ActionCommand command, OpportunityJson.Obj canonical) throws IOException {
        Path raw = configured.incidentRoot().resolve(incidentId(command.actionId(), digest(DriverJson.encode(command.arguments()))) + ".before-index.json");
        Path stable = configured.incidentRoot().resolve(incidentId(command.actionId(), digest(DriverJson.encode(canonical))) + ".before-index.json");
        boolean rawExists = Files.exists(raw, LinkOption.NOFOLLOW_LINKS);
        require(raw.equals(stable) || !rawExists || !Files.exists(stable, LinkOption.NOFOLLOW_LINKS), "Conflicting exact incident originals require reconciliation");
        return rawExists ? raw : stable;
    }
    private Ticket readTicket(ActionCommand command, Path indexPath) throws IOException {
        ExactRef index = measure(indexPath); ObjectNode body = object(read(index));
        Kind kind = command.arguments().get("unknown_mandatory_choice_v1") instanceof OpportunityJson.Obj ? Kind.MANDATORY
                : command.arguments().get("unhandled_event_fallback") instanceof OpportunityJson.Obj ? Kind.EVENT : Kind.INTERACTION;
        Binding origin = new Binding(command.before(), command.source(), command.sessionId());
        validateIndex(body, origin, command, kind);
        String id = incidentId(command.actionId(), text(body, "arguments_sha256"));
        require(id.equals(text(body, "incident_id")) && indexPath.equals(configured.incidentRoot().resolve(id + ".before-index.json")), "Original incident index identity differs");
        ExactRef before = ExactRef.fromJson(body.get("before_ref"));
        require(Path.of(before.path()).equals(configured.incidentRoot().resolve(id + ".before.json")), "Original before escaped the episode root");
        read(before); return new Ticket(id, kind, before, index, origin);
    }
    private static OpportunityJson.Obj indexedArguments(ActionCommand command, ObjectNode index) throws IOException {
        String retained = text(index, "arguments_sha256");
        if (retained.equals(digest(DriverJson.encode(command.arguments())))) return command.arguments();
        OpportunityJson.Obj canonical = incidentArguments(command);
        require(retained.equals(digest(DriverJson.encode(canonical))), "Original incident command arguments differ in both exact representations");
        return canonical;
    }
    private void validateIndex(ObjectNode row, Binding actual, ActionCommand command, Kind kind) throws IOException {
        ReadOriginals originalRead = beforeIndexRead(row);
        require(kind == Kind.MANDATORY ? originalRead instanceof KnownRead known && known.original().equals(
                ExactRef.fromJson(StrictJson.parse(DriverJson.encode(command.arguments())).get("mandatory_choice_original_read")))
                : originalRead == NoRead.INSTANCE, "Action incident lost its exact original query role");
        OpportunityJson.Obj originalArguments = indexedArguments(command, row);
        require(decodeBinding(row).equals(actual) && text(row, "action_id").equals(command.actionId()) && text(row, "kind").equals(kind.name())
                && text(row, "arguments_sha256").equals(digest(DriverJson.encode(originalArguments))), "Original incident command/source binding differs");
    }
    private static void validateCaptureBinding(ObservationIdentity observed, ObjectNode capture) {
        JsonNode b = capture.get("binding"); StrictJson.require(b != null && b.isObject(), "Actual fallback binding required");
        var f = observed.frame();
        StrictJson.require(f.snapshotId().equals(text(b, "snapshot_id")) && f.episodeRunId().equals(text(b, "episode_run_id"))
                && f.revision().equals(integer(b, "revision")) && f.identity().nativeRevision().equals(integer(b, "native_revision"))
                && f.identity().dateRaw().equals(integer(b, "date_raw")) && f.identity().player().equals(integer(b, "actor_character_id"))
                && java.math.BigInteger.valueOf(observed.game().pid()).equals(integer(b, "bridge_pid"))
                && integer(b, "connection_generation").signum() > 0
                && b.path("paused").isBoolean() && b.path("paused").booleanValue() && b.path("map_ready").isBoolean() && b.path("map_ready").booleanValue()
                && capture.path("selection").isObject(), "Fallback capture crossed its actual command frame/actor");
    }
    private void verifyPolicyReceipt(ObjectNode afterIndex,ObjectNode beforeIndex,byte[] actualBeforeBody,byte[] actualAfterBody)throws IOException {
        String schema=text(afterIndex,"schema");
        if(LEGACY_RECOVERY_AFTER_SCHEMA.equals(schema)) {
            require(afterIndex.has("policy_receipt_input")&&afterIndex.get("policy_receipt_input").isNull(),"legacy first-rendered proof cannot bypass a policy receipt");
            verifyLegacyAfterBody(afterIndex,actualBeforeBody,actualAfterBody);
            verifyStoredLegacy(afterIndex,beforeIndex,ExactRef.fromJson(afterIndex.get("before_ref")),"after_frame");return;
        }
        if(LEGACY_AFTER_INDEX_SCHEMA.equals(schema)) {
            StrictJson.require(!afterIndex.has("policy_receipt_input"),"legacy after index cannot claim a new policy receipt comparison");return;
        }
        StrictJson.require(AFTER_INDEX_SCHEMA.equals(schema)&&afterIndex.has("policy_receipt_input"),"versioned after index requires explicit nullable policy receipt input");
        JsonNode input=afterIndex.get("policy_receipt_input");
        if(input.isNull()) {
            StrictJson.require(!"exact-source-reviewed-populist-refuse-preserve-realm".equals(object(actualBeforeBody).path("policy").asText()),"current populist after index lost its actual policy receipt input");return;
        }
        EventIncidentReceipt.verify(new RawJson(StrictJson.canonical(input,MAX_METADATA)),text(beforeIndex,"arguments_sha256"),
            ExactRef.fromJson(afterIndex.get("before_ref")),ExactRef.fromJson(afterIndex.get("after_ref")),new RawJson(actualBeforeBody),new RawJson(actualAfterBody));
    }
    /** Reuses the actual original after producer; no subset of stored result flags can substitute for its output. */
    private void verifyLegacyAfterBody(ObjectNode afterIndex,byte[] actualBeforeBody,byte[] actualAfterBody)throws IOException {
        ObjectNode proof=object(afterIndex.get("legacy_command_binding"));
        require(proof.path("observation_supporting_refs").isArray()&&proof.path("observation_supporting_refs").size()==1,
                "legacy after requires its explicit sole original native-effect basis");
        byte[] basisBody=read(ExactRef.fromJson(proof.get("observation_supporting_refs").get(0)));
        ObjectNode basis=object(basisBody);
        require((NativeEffectEvidence.RECONCILIATION_SCHEMA.equals(text(basis,"schema"))
                ||NativeEffectEvidence.RECONCILED_EVENT_READ_SCHEMA.equals(text(basis,"schema")))
                &&text(proof,"canonical_command_sha256").equals(text(basis,"command_body_sha256")),"legacy after material crossed its original effect command");
        if(NativeEffectEvidence.RECONCILED_EVENT_READ_SCHEMA.equals(text(basis,"schema")))
            NativeEffectEvidence.reconciliationProvenance(new RawJson(basisBody));
        RawJson compatible=new RawJson(read(ExactRef.fromJson(basis.get("compatible_material"))));
        ObjectNode before=object(actualBeforeBody),stored=object(actualAfterBody);
        ExactRef beforeRef=ExactRef.fromJson(afterIndex.get("before_ref"));
        ObjectNode ticket=StrictJson.object().put("incident_id",text(before,"incident_id"));ticket.set("before",beforeRef.toJson());
        ticket.set("current_event_instance_id",before.get("current_event_instance_id"));ticket.set("selected_native_option_index",before.path("selection").get("native_option_index"));
        ObjectNode outcome=StrictJson.object().put("status","independent_effect_observed");outcome.set("result",StrictJson.parse(compatible.bytes(),MAX_METADATA));
        String captured=text(stored,"captured_at_utc");StrictJson.utc(captured);
        var guard=org.xar.ck3.control.application.action.CommandOriginCodec.guard(proof.get("reconciliation_guard"));
        java.time.Instant capturedAt=java.time.Instant.parse(captured);
        require(!capturedAt.isBefore(guard.observedAt())&&capturedAt.isBefore(guard.validUntil()),"legacy recorded capture time escaped its original observation window");
        var regenerated=UnhandledEventEvidenceJson.after(new UnhandledEventEvidenceJson.AfterInput(Optional.of(retained(ticket)),
                Optional.of(retained(outcome)),RetainedJson.NULL,captured));
        byte[] expected=UnhandledEventEvidenceJson.encodeBody(regenerated);
        require(object(expected).equals(stored),"legacy complete after body differs from the actual original compatible-result producer");
        verifyExternal(beforeRef);verifyExternal(ExactRef.fromJson(afterIndex.get("after_ref")));
    }
    private static void requireProgress(Binding actual, ExactRef original) throws IOException {
        ObjectNode basis = object(read(original));
        require("xar.java.incident-observation-original/v1".equals(text(basis, "schema")) && decodeBinding(basis).equals(actual),
                "Actual scan progress must retain its own original full-frame source/session");
    }
    private void verifyEpisode() throws IOException { read(episodeRef); }
    private ExactRef writeSame(Path target, byte[] raw) throws IOException {
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) { ExactRef old = measure(target); require(java.util.Arrays.equals(read(old), raw), "Immutable scan/batch output differs"); return old; }
        return write(configured, target, raw);
    }
    @FunctionalInterface private interface Work<T> { T run() throws IOException; }
    private synchronized <T> T locked(Work<T> work) throws IOException {
        configured.io().require(4096); Path lockPath = configured.incidentRoot().resolve(".incident.lock"); plain(lockPath);
        try (FileChannel channel = FileChannel.open(lockPath, StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            try (FileLock lock = channel.tryLock()) { require(lock != null, "Actual incident producer/scan is already owned"); return work.run(); }
            catch (OverlappingFileLockException busy) { throw new IOException("Actual incident producer/scan is already owned", busy); }
        }
    }
    private static ObjectNode binding(Binding value) {
        ObjectNode root = StrictJson.object().put("session_id", value.sessionId());
        root.set("origin", ProposalLifecycleCodec.observation(value.before())); root.set("source", ProposalLifecycleCodec.source(value.source())); return root;
    }
    private static Binding decodeBinding(ObjectNode value) {
        return new Binding(ProposalLifecycleCodec.decodeObservation(value.get("origin")), source(object(value.get("source"))), text(value, "session_id"));
    }
    private static G2Source source(ObjectNode source) {
        StrictJson.object(source, Set.of("machine_id", "observed_at_utc", "exact_build", "source_ref"));
        return new G2Source(text(source, "machine_id"), text(source, "observed_at_utc"), text(source, "exact_build"), ExactRef.fromJson(source.get("source_ref")));
    }
    public static ExactRef measure(Path path) throws IOException { plain(path); require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && Files.size(path) > 0 && Files.size(path) <= MAX_BODY, "Plain bounded original incident file required"); byte[] raw = Files.readAllBytes(path); require(raw.length > 0 && raw.length <= MAX_BODY, "Bounded original evidence file required"); return new ExactRef(path.toString(), raw.length, digest(raw)); }
    private static byte[] read(ExactRef ref) throws IOException { verify(ref); byte[] raw = Files.readAllBytes(Path.of(ref.path())); verify(ref); require(raw.length == ref.bytes() && digest(raw).equals(ref.sha256()), "Original evidence changed during read"); return raw; }
    private static void verify(ExactRef ref) throws IOException { require(ref.bytes() > 0 && ref.bytes() <= MAX_BODY && measure(Path.of(ref.path())).equals(ref), "Actual original evidence source changed"); }
    private static void verifyExternal(ExactRef ref) throws IOException {
        Path path = absolute(Path.of(ref.path())); plain(path);
        require(ref.bytes() > 0 && ref.bytes() <= (long)DriverJson.MAX_NATIVE_BYTES + Integer.BYTES && Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)
                && Files.size(path) == ref.bytes(), "Bounded original native/source reference required");
        try {
            MessageDigest sha = MessageDigest.getInstance("SHA-256"); long count = 0;
            try (var input = Files.newInputStream(path)) { byte[] buffer = new byte[65536]; int length; while ((length = input.read(buffer)) != -1) {
                count = Math.addExact(count, length); require(count <= ref.bytes(), "Original native/source grew during hash read"); sha.update(buffer, 0, length);
            } }
            require(count == ref.bytes() && HexFormat.of().formatHex(sha.digest()).equals(ref.sha256()) && Files.size(path) == ref.bytes(), "Original native/source evidence changed");
        } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private static ExactRef write(Configuration configured, Path target, byte[] raw) throws IOException {
        plain(target); require(raw.length > 0 && raw.length <= MAX_BODY, "Bounded original incident/scan body required");
        require(target.startsWith(configured.incidentRoot()) || target.startsWith(configured.scanRoot()), "Incident output escaped configured roots");
        configured.io().require(Math.addExact(raw.length, 4096));
        try (FileChannel file = FileChannel.open(target, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            var buffer = java.nio.ByteBuffer.wrap(raw); while (buffer.hasRemaining()) file.write(buffer); file.force(true);
        }
        return measure(target);
    }
    private static byte[] encode(ObjectNode body) {
        byte[] complete = FullJsonTree.encode(body, MAX_BODY);
        return complete.length <= MAX_METADATA ? ProposalLifecycleCodec.encodePayload(body, MAX_METADATA) : complete;
    }
    private static RetainedJson.ObjectValue retained(ObjectNode value) { return RetainedJson.object(RetainedJson.parse(encode(value))); }
    private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "Actual JSON object required"); return (ObjectNode)node; }
    private static ObjectNode object(byte[] raw) { return object(FullJsonTree.parse(raw, MAX_BODY)); }
    private static String text(JsonNode row, String name) { return StrictJson.text(row.get(name)); }
    private static java.math.BigInteger integer(JsonNode row, String name) { JsonNode value = row.get(name); StrictJson.require(value != null && value.isIntegralNumber(), "Exact integer required: " + name); return value.bigIntegerValue(); }
    private static Path absolute(Path value) { StrictJson.require(value != null && value.isAbsolute() && value.equals(value.normalize()), "Absolute normalized incident root required"); return value; }
    private static void plainDirectory(Path path) throws IOException { plain(path); require(Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS), "Configured original incident/scan root is unavailable"); }
    private static void plain(Path path) throws IOException { absolute(path); for (Path cursor = path; cursor != null; cursor = cursor.getParent()) if (Files.exists(cursor, LinkOption.NOFOLLOW_LINKS)) require(!Files.isSymbolicLink(cursor) && cursor.toRealPath().equals(cursor), "Incident path is not a plain canonical original"); }
    private static String digest(byte[] raw) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
    private static void require(boolean value, String reason) throws IOException { if (!value) throw new IOException(reason); }
}
