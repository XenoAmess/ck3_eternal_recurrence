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
    private static final int MAX_BODY = 1 << 20;
    private static final long MAX_SCAN_BYTES = 16L << 20;
    private final Configuration configured;
    private final ExactRef episodeRef;
    private final Binding episode;
    public enum Kind { EVENT, INTERACTION, MANDATORY }
    @FunctionalInterface public interface IoGuard { void require(long pendingBytes) throws IOException; }
    @FunctionalInterface public interface ProgressOriginal { ExactRef preserve() throws IOException; }
    public record Configuration(Path incidentRoot, Path scanRoot, Clock clock, IoGuard io,
            Optional<TrustedEventSourceContext> trustedInteractions) {
        public Configuration {
            incidentRoot = absolute(incidentRoot); scanRoot = absolute(scanRoot);
            Objects.requireNonNull(clock); Objects.requireNonNull(io); Objects.requireNonNull(trustedInteractions);
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
        require(originalBasis.bytes() <= MAX_BODY, "Bounded typed original observation basis required");
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
        ObjectNode plan = object(StrictJson.parse(DriverJson.encode(retainedPlan)));
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
            ObjectNode actualBody = object(StrictJson.parse(raw)); actualBody.put("stage", "planning_diagnostic").put("dispatch_attempted", false);
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
        String id = digest((command.actionId() + "|" + digest(DriverJson.encode(command.arguments()))).getBytes(java.nio.charset.StandardCharsets.UTF_8)).substring(0, 32);
        return locked(() -> {
            Path indexPath = configured.incidentRoot().resolve(id + ".before-index.json");
            if (Files.exists(indexPath, LinkOption.NOFOLLOW_LINKS)) {
                var index = measure(indexPath); ObjectNode row = object(read(index)); validateIndex(row, actual, command, kind);
                ExactRef before = ExactRef.fromJson(row.get("before_ref")); read(before); return Optional.of(new Ticket(id, kind, before, index, actual));
            }
            ObjectNode planned = StrictJson.object().put("snapshot_id", command.before().frame().snapshotId()).put("revision", command.before().frame().revision());
            planned.set("plan", StrictJson.parse(DriverJson.encode(command.arguments())));
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
                    .put("kind", kind.name()).put("action_id", command.actionId()).put("arguments_sha256", digest(DriverJson.encode(command.arguments())));
            index.set("before_ref", before.toJson());
            if (kind == Kind.MANDATORY) index = IncidentReadIndex.encode(new IncidentReadIndex.KnownReceipt(
                    ExactRef.fromJson(planned.path("plan").get("mandatory_choice_original_read"))), index);
            ExactRef indexed = write(configured, indexPath, encode(index)); return Optional.of(new Ticket(id, kind, before, indexed, actual));
        });
    }
    /** Called only by the actual observer after independent evidence has been durably archived. It performs no native query. */
    public void observedAfter(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            NativeEffectRegistry.Projected projected) {
        if (!handles(command)) return;
        try {
            StrictJson.require(projected.result() instanceof ActionPorts.EffectObserved && projected.compatibleResult().isPresent(), "Independent observed effect required for incident after");
            var effect = ((ActionPorts.EffectObserved)projected.result()).observation();
            StrictJson.require(pair.before().identity().equals(command.before()) && pair.before().originalEvidence().equals(attempt.guard().nativeEvidence())
                    && pair.after().identity().equals(effect.after()) && pair.after().source().equals(command.source())
                    && pair.after().sessionId().equals(command.sessionId()) && !effect.supportingEvidence().isEmpty(), "Incident after lost original frame/evidence binding");
            for (ExactRef source : effect.supportingEvidence()) verifyExternal(source);
            verifyExternal(pair.after().originalEvidence());
            Ticket ticket = existing(command);
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
                ObjectNode index = binding(ticket.origin()); index.put("schema", AFTER_INDEX_SCHEMA).put("incident_id", ticket.incidentId())
                        .put("independent_postcondition_verified", true).put("legacy_body_scope", "original_reply_ack_and_response_assessment");
                index.set("before_ref", ticket.before().toJson()); index.set("after_ref", after.toJson());
                index.set("after_observation", ProposalLifecycleCodec.observation(pair.after().identity())); index.set("after_frame", pair.after().originalEvidence().toJson());
                var evidence = index.putArray("supporting_refs"); effect.supportingEvidence().forEach(ref -> evidence.add(ref.toJson()));
                Optional<RawJson> policyInput=EventIncidentReceipt.prepare(command.arguments(),projected.compatibleResult().orElseThrow(),ticket.before(),after,new RawJson(raw));
                if(policyInput.isPresent())index.set("policy_receipt_input",StrictJson.parse(policyInput.orElseThrow().bytes(),MAX_BODY));else index.putNull("policy_receipt_input");
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
        require(handles(command),"actual captured event/interaction required");
        var pair=actual.frames();require(actual.dispatch().requestId().equals(attempt.requestId())
                &&pair.before().identity().equals(command.before())&&pair.before().source().equals(command.source())
                &&pair.before().sessionId().equals(command.sessionId())&&pair.before().originalEvidence().equals(attempt.guard().nativeEvidence())
                &&pair.after().identity().machineId().equals(command.before().machineId())&&pair.after().identity().game().equals(command.before().game())
                &&pair.after().identity().frame().episodeRunId().equals(command.before().frame().episodeRunId())
                &&pair.after().source().equals(command.source())&&pair.after().sessionId().equals(command.sessionId()),"unsettled observation crossed its actual original command/Game/source");
        verifyExternal(originalDispatch);var initial=NativeEffectEvidence.basis(pair.before());var ending=NativeEffectEvidence.basis(pair.after());
        for(ExactRef ref:List.of(initial.nativeFrame(),initial.driverFacts(),ending.nativeFrame(),ending.driverFacts()))verifyExternal(ref);
        Ticket ticket=existing(command);
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
            ObjectNode row=binding(ticket.origin());row.put("schema",UNSETTLED_SCHEMA).put("incident_id",ticket.incidentId()).put("kind",ticket.kind().name())
                    .put("action_id",command.actionId()).put("arguments_sha256",digest(DriverJson.encode(command.arguments())))
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
            validateUnsettled(row,beforeIndex,ticket.before(),ticket.incidentId());return write(configured,path,encode(row));
        });
    }
    private void validateUnsettled(ObjectNode row,ObjectNode beforeIndex,ExactRef before,String id)throws IOException {
        StrictJson.object(row,Set.of("session_id","origin","source","schema","incident_id","kind","action_id","arguments_sha256","request_id","observation_status","reason",
                "independent_postcondition_verified","replay_allowed","observed_at_utc","before_ref","before_frame","before_driver_facts","after_frame","after_driver_facts",
                "after_observation","original_dispatch_ref","original_instance_id","original_instance_present","native_ok","dispatch_kind"));
        StrictJson.require(row.get("independent_postcondition_verified").isBoolean()&&!row.get("independent_postcondition_verified").booleanValue()
                &&row.get("replay_allowed").isBoolean()&&!row.get("replay_allowed").booleanValue(), "unsettled diagnostic changed or gained effect/replay credit");
        require(UNSETTLED_SCHEMA.equals(text(row,"schema"))&&id.equals(text(row,"incident_id"))&&"UNSETTLED".equals(text(row,"observation_status"))
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
            if (originalBasis.isPresent()) { ExactRef ref = originalBasis.orElseThrow(); require(ref.bytes() <= MAX_BODY, "Bounded typed original basis required"); verifyExternal(ref); originals.add(ref); }
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
        if (original instanceof KnownRead known) require(known.original().bytes() > 0 && known.original().bytes() <= MAX_BODY,
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
    private Ticket existing(ActionCommand command) throws IOException {
        require(handles(command), "Actual original fallback command required");
        String id = digest((command.actionId() + "|" + digest(DriverJson.encode(command.arguments()))).getBytes(java.nio.charset.StandardCharsets.UTF_8)).substring(0, 32);
        ExactRef index = measure(configured.incidentRoot().resolve(id + ".before-index.json")); ObjectNode body = object(read(index));
        Kind kind = Kind.valueOf(text(body, "kind")); Binding origin = new Binding(command.before(), command.source(), command.sessionId());
        validateIndex(body, origin, command, kind); return new Ticket(id, kind, ExactRef.fromJson(body.get("before_ref")), index, origin);
    }
    private void validateIndex(ObjectNode row, Binding actual, ActionCommand command, Kind kind) throws IOException {
        ReadOriginals originalRead = beforeIndexRead(row);
        require(kind == Kind.MANDATORY ? originalRead instanceof KnownRead known && known.original().equals(
                ExactRef.fromJson(StrictJson.parse(DriverJson.encode(command.arguments())).get("mandatory_choice_original_read")))
                : originalRead == NoRead.INSTANCE, "Action incident lost its exact original query role");
        require(decodeBinding(row).equals(actual) && text(row, "action_id").equals(command.actionId()) && text(row, "kind").equals(kind.name())
                && text(row, "arguments_sha256").equals(digest(DriverJson.encode(command.arguments()))), "Original incident command/source binding differs");
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
    private static void verifyPolicyReceipt(ObjectNode afterIndex,ObjectNode beforeIndex,byte[] actualBeforeBody,byte[] actualAfterBody) {
        String schema=text(afterIndex,"schema");
        if(LEGACY_AFTER_INDEX_SCHEMA.equals(schema)) {
            StrictJson.require(!afterIndex.has("policy_receipt_input"),"legacy after index cannot claim a new policy receipt comparison");return;
        }
        StrictJson.require(AFTER_INDEX_SCHEMA.equals(schema)&&afterIndex.has("policy_receipt_input"),"versioned after index requires explicit nullable policy receipt input");
        JsonNode input=afterIndex.get("policy_receipt_input");
        if(input.isNull()) {
            StrictJson.require(!"exact-source-reviewed-populist-refuse-preserve-realm".equals(object(actualBeforeBody).path("policy").asText()),"current populist after index lost its actual policy receipt input");return;
        }
        EventIncidentReceipt.verify(new RawJson(StrictJson.canonical(input,MAX_BODY)),text(beforeIndex,"arguments_sha256"),
            ExactRef.fromJson(afterIndex.get("before_ref")),ExactRef.fromJson(afterIndex.get("after_ref")),new RawJson(actualBeforeBody),new RawJson(actualAfterBody));
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
    private static byte[] encode(ObjectNode body) { return ProposalLifecycleCodec.encodePayload(body, MAX_BODY); }
    private static RetainedJson.ObjectValue retained(ObjectNode value) { return RetainedJson.object(RetainedJson.parse(encode(value))); }
    private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "Actual JSON object required"); return (ObjectNode)node; }
    private static ObjectNode object(byte[] raw) { return object(StrictJson.parse(raw, MAX_BODY)); }
    private static String text(JsonNode row, String name) { return StrictJson.text(row.get(name)); }
    private static java.math.BigInteger integer(JsonNode row, String name) { JsonNode value = row.get(name); StrictJson.require(value != null && value.isIntegralNumber(), "Exact integer required: " + name); return value.bigIntegerValue(); }
    private static Path absolute(Path value) { StrictJson.require(value != null && value.isAbsolute() && value.equals(value.normalize()), "Absolute normalized incident root required"); return value; }
    private static void plainDirectory(Path path) throws IOException { plain(path); require(Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS), "Configured original incident/scan root is unavailable"); }
    private static void plain(Path path) throws IOException { absolute(path); for (Path cursor = path; cursor != null; cursor = cursor.getParent()) if (Files.exists(cursor, LinkOption.NOFOLLOW_LINKS)) require(!Files.isSymbolicLink(cursor) && cursor.toRealPath().equals(cursor), "Incident path is not a plain canonical original"); }
    private static String digest(byte[] raw) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
    private static void require(boolean value, String reason) throws IOException { if (!value) throw new IOException(reason); }
}
