package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.*;

/** Explicit Florin cancellation proof. Real preflight READ and post-Status Full originals remain separate. */
public final class FullSnapshotSentinelCancellation {
    private static final String SCHEMA = "xar.java.ck3-1210-sentinel-cancellation/v1";
    private static final FieldKey CONFIRMED = new FieldKey("sentinel.cancel_confirmed");
    private static final FieldKey ORIGINALS = new FieldKey("sentinel.cancel_originals");
    private FullSnapshotSentinelCancellation() { }
    public static boolean supports(ActionCommand command) {
        return command.origin() instanceof CommandOrigin.Gameplay && command.operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX)
                && exactBuild(command.source());
    }
    public static boolean exactBuild(org.xar.ck3.control.g2.common.G2Source source) {
        return ExactCk3Build.CK3_1210.executableSha256().equalsIgnoreCase(source.exactBuild())
                ||ExactCk3Build.CK3_1210_STEAM_26757580.executableSha256().equalsIgnoreCase(source.exactBuild());
    }
    public static List<ExpectedValue> expected(String step) {
        return List.of(new ExpectedBoolean(CONFIRMED, true),
                new ExpectedText(new FieldKey("sentinel.generation"), AdvancePrimitives.cancelGeneration(step).toString()));
    }
    /** Called during actual same-writer preparation, before INTENT/Attempt/native dispatch. */
    public static NativeRequest prepare(ActionCommand command, NativeRequest base, ClockStatusRead.Observation before,
            ActionPorts.OutcomeArchive archive) {
        require(supports(command) && base.preparationEvidence().isEmpty(), "exact original 1210 CANCEL preparation required");
        requirePreRead(command, before.receipt(), archive);
        ExactRef original = archive.preserveRead(before.receipt());
        require(before.receipt().equals(archive.loadRead(original)), "original pre-CANCEL Status archive changed");
        return new NativeRequest(base.step(), base.requiredCapability(), base.additionalFields(), List.of(original));
    }
    public static PlanningReadReceipt preparedRead(ActionCommand command, NativeRequest prepared, ActionPorts.OutcomeArchive archive) {
        NativeRequest base = AdvancePrimitives.prepareRequest(command);
        require(supports(command) && prepared.step().equals(base.step()) && prepared.requiredCapability().equals(base.requiredCapability())
                && prepared.additionalFields().equals(base.additionalFields()) && prepared.preparationEvidence().size() == 1,
                "1210 CANCEL requires its real original preflight Status, without changed wire fields");
        PlanningReadReceipt before = archive.loadRead(prepared.preparationEvidence().getFirst());
        require(archive.readReferenceOf(before).equals(prepared.preparationEvidence().getFirst()), "pre-CANCEL read locator changed");
        requirePreRead(command, before, archive); return before;
    }
    private static void requirePreRead(ActionCommand command, PlanningReadReceipt before, ActionPorts.OutcomeArchive archive) {
        if (before.request().origin() instanceof CommandOrigin.PhysicalStatusOnly physical) {
            var observation = new ClockStatusRead.Observation(ClockStatusRead.decode(before.original()), before,
                    archive.referenceOf(before.original()));
            var actual = physical.identity(); var selected = command.before();
            require(before.contractId().equals(PhysicalStatusIdentity.CONTRACT_ID)
                    && before.request().source().equals(command.source()) && before.request().sessionId().equals(command.sessionId())
                    && actual.machineId().equals(selected.machineId()) && actual.game().equals(selected.game())
                    && actual.source().equals(command.source()) && actual.sessionId().equals(command.sessionId())
                    && actual.nativeRevision().compareTo(selected.frame().identity().nativeRevision()) <= 0
                    && !before.request().deadline().isAfter(command.deadline())
                    && observation.status().state() == State.ARMED
                    && selected.frame().identity().dateRaw().equals(BigInteger.valueOf(observation.status().lastObservedDateRaw())),
                    "retained preparation must keep its actual physical ARMED Status and same selected Game/source/date");
            requireTuple(command, observation.status()); return;
        }
        require(before.contractId().equals(ClockStatusRead.CONTRACT_ID) && before.request().operation().value().equals(ClockStatusRead.STEP)
                && before.request().arguments().members().isEmpty() && before.adoption().isEmpty()
                && before.request().source().equals(command.source()) && before.request().sessionId().equals(command.sessionId())
                && !before.request().deadline().isAfter(command.deadline())
                && before.before().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && before.after().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && before.before().paused() && before.after().paused() && before.before().mapReady() && before.after().mapReady()
                && before.before().playerAlive() && before.after().playerAlive(), "real original paused pre-CANCEL Status required");
        requireOwner(command, before.before().binding().observed()); requireOwner(command, before.after().binding().observed());
        require(before.request().before().equals(command.before()), "pre-CANCEL read must retain the actual selected command identity");
        Status prior = ClockStatusRead.decode(before.original());
        requireTuple(command, prior);
        require(before.after().binding().observed().frame().identity().dateRaw().equals(BigInteger.valueOf(prior.lastObservedDateRaw())),
                "original pre-CANCEL Status date differs from its real paused frame");
        require(prior.state() == State.ARMED || prior.state() == State.IDLE
                || (prior.state() == State.TRIGGERED || prior.state() == State.FAILED) && prior.pauseObserved(),
                "pre-CANCEL Status is not the actual requested paused generation");
    }
    public static List<ExpectedValue> observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack,
            PlanningReadReceipt read, AdvanceObservationPort.Frame full, ActionPorts.OutcomeArchive archive) {
        PlanningReadReceipt before = preparedRead(command, attempt.preparedRequest(), archive);
        validate(command, attempt, ack, before, read, full, archive);
        var manifest = full.semantic().get("java_driver_facts_evidence");
        require(manifest instanceof Obj, "1210 CANCEL needs the actual complete Full Driver manifest");
        ExactRef driver = ExactRef.fromJson(toNode(manifest));
        AdvancePrimitiveEvidence.exact(full.originalEvidence(), archive.loadNativeFrame(full.originalEvidence()));
        AdvancePrimitiveEvidence.exact(driver, archive.loadFullMaterial(driver).bytes());
        var row = StrictJson.object(); row.put("schema", SCHEMA).put("body_sha256", ActionCodec.bodySha256(command))
                .put("request_id", attempt.requestId()).put("observed_at", full.observedAt().toString());
        row.set("before_read", archive.readReferenceOf(before).toJson());
        row.set("status_read", archive.preserveRead(read).toJson());
        row.set("native_frame", full.originalEvidence().toJson()); row.set("driver_facts", driver.toJson());
        row.set("provenance", ObservationProvenanceCodec.encode(full.provenance()));
        ExactRef proof = archive.preserveMaterial(new RawJson(StrictJson.canonical(row)));
        return actual(ClockStatusRead.decode(read.original()), proof, references(proof, archive.readReferenceOf(before),
                archive.readReferenceOf(read), full.originalEvidence(), driver, full.provenance()));
    }
    private static List<ExpectedValue> actual(Status status, ExactRef proof, List<ExactRef> references) {
        List<ExpectedValue> values = new ArrayList<>(AdvancePrimitives.statusValues(status));
        values.add(new ExpectedBoolean(CONFIRMED, true));
        var locator = StrictJson.object(); locator.set("proof", proof.toJson());
        var originals = locator.putArray("references"); references.forEach(ref -> originals.add(ref.toJson()));
        values.add(new ExpectedText(ORIGINALS, new String(StrictJson.canonical(locator), StandardCharsets.UTF_8)));
        return List.copyOf(values);
    }
    private static JsonNode locator(ActionState.ControlApplied control) {
        List<ExpectedText> locators = control.actual().stream().filter(value -> value instanceof ExpectedText text && text.field().equals(ORIGINALS))
                .map(value -> (ExpectedText)value).toList();
        require(locators.size() <= 1, "CANCEL proof locator is duplicated");
        if (locators.isEmpty()) return null;
        return StrictJson.object(StrictJson.parse(locators.getFirst().value().getBytes(StandardCharsets.UTF_8)), Set.of("proof", "references"));
    }
    /** The real ACTION/WAL pins every mixed-role original, without changing historical ControlApplied bodies. */
    public static List<ExactRef> references(ActionState.ControlApplied control) {
        JsonNode locator = locator(control); if (locator == null) return List.of();
        JsonNode array = locator.get("references");
        require(array.isArray() && array.size() >= 1 && array.size() <= 10, "bounded exact CANCEL evidence closure required");
        List<ExactRef> refs = new ArrayList<>(); array.forEach(value -> refs.add(ExactRef.fromJson(value)));
        require(refs.stream().allMatch(ref -> ref.bytes() > 0) && refs.stream().distinct().count() == refs.size()
                && refs.contains(ExactRef.fromJson(locator.get("proof"))), "CANCEL closure omitted its proof or repeated an original");
        return List.copyOf(refs);
    }
    private static List<ExactRef> references(ExactRef proof, ExactRef before, ExactRef status, ExactRef nativeFrame,
            ExactRef driver, ObservationProvenance provenance) {
        List<ExactRef> refs = new ArrayList<>(List.of(proof, before, status, nativeFrame, driver));
        var fresh = (ObservationProvenance.FreshSnapshotQuery)provenance; refs.add(fresh.readAcknowledgement());
        if (fresh.basis() instanceof ObservationProvenance.LiveAfterSetter live) refs.add(live.setterAcknowledgement());
        else refs.add(((ObservationProvenance.ColdAfterAcknowledgement)fresh.basis()).originalReceipt());
        return refs.stream().distinct().toList();
    }
    /** Classification only; the actual Root pending binder still supplies writer/source/physical authority. */
    public static boolean isPositiveAckCancellation(ActionReceipt original, ActionPorts.OutcomeArchive archive) {
        try {
            ActionCommand command = original.command();
            if (original.settled() || !(original.state() instanceof ActionState.AckReceived || original.state() instanceof ActionState.Unknown)
                    || !supports(command) || !command.arguments().members().isEmpty()
                    || !original.bodySha256().equals(ActionCodec.bodySha256(command))
                    || !command.expected().equals(AdvancePrimitives.expected(command.before(), command.source(), command.operation(), command.arguments()))) return false;
            var attempt = ActionTransitions.attempt(original.state()).orElse(null);
            var dispatch = ActionTransitions.dispatch(original.state()).orElse(null);
            if (attempt == null || !(dispatch instanceof NativeActionPort.AckReceived ack)
                    || original.ack().filter(ack::equals).isEmpty() || !ack.nativeOk()
                    || !attempt.guard().observed().equals(command.before())) return false;
            var prior = preparedRead(command, attempt.preparedRequest(), archive);
            acknowledgedOriginal(command, attempt, ack, prior);
            return true;
        } catch (RuntimeException rejected) { return false; }
    }
    private static Status acknowledgedOriginal(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.AckReceived ack, PlanningReadReceipt before) {
        require(supports(command) && attempt.requestId().equals(ack.requestId())
                && command.source().equals(attempt.guard().source()) && command.sessionId().equals(attempt.guard().sessionId())
                && command.operation().equals(attempt.guard().operation()) && command.origin().acceptsGuard(attempt.guard().origin()),
                "1210 CANCEL changed its original Attempt/source/owner");
        JsonNode token = AdvancePrimitives.nativeResult(ack, command.operation().value());
        JsonNode envelope = StrictJson.parse(ack.originalFrame().bytes());
        require(envelope.isObject() && envelope.path("protocol_version").isIntegralNumber()
                && envelope.path("protocol_version").bigIntegerValue().equals(BigInteger.ONE) && envelope.path("type").isTextual() && envelope.path("type").textValue().equals("command_result")
                && envelope.path("request_id").isTextual() && envelope.path("request_id").textValue().equals(attempt.requestId())
                && envelope.path("ok").isBoolean() && envelope.path("ok").booleanValue() && token.equals(envelope.get("result"))
                && token.path("status").isTextual() && token.path("status").textValue().equals("available"),
                "1210 cancellation requires the exact original available ACK envelope/token");
        Status actual = AdvancePrimitives.acknowledgedSentinel(ack, command.operation().value());
        Status prior = ClockStatusRead.decode(before.original());
        requireTuple(command, actual);
        require(actual.generation().equals(prior.generation()) && actual.startingDateRaw() == prior.startingDateRaw()
                && actual.targetDateRaw() == prior.targetDateRaw() && actual.speed() == prior.speed()
                && actual.mode() == prior.mode() && actual.armyCount() == prior.armyCount(),
                "available ACK crossed its actual original preflight slot tuple");
        require(prior.state() == State.ARMED || prior.equals(actual), "an already terminal original slot changed during no-op CANCEL");
        require(actual.state() == State.IDLE || (actual.state() == State.TRIGGERED || actual.state() == State.FAILED) && actual.pauseObserved(),
                "1210 cancellation needs IDLE or its real paused terminal generation");
        var submission = ack.custody().orElseThrow(() -> new IllegalArgumentException("actual CANCEL request custody is absent"));
        submission.verify(ack, attempt.guard());
        NativeRequestChronology.requireBeforeSubmission(before, attempt, ack);
        require(submission.writeEntered().observedAt().isBefore(command.deadline()), "original CANCEL write escaped its immutable deadline");
        return actual;
    }
    private static void validate(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack,
            PlanningReadReceipt before, PlanningReadReceipt read, AdvanceObservationPort.Frame full, ActionPorts.OutcomeArchive archive) {
        Status actual = ClockStatusRead.decode(read.original());
        require(actual.equals(acknowledgedOriginal(command, attempt, ack, before)),
                "available CANCEL ACK and independent Status differ in retained content");
        require(read.request().source().equals(command.source()) && read.request().sessionId().equals(command.sessionId())
                && read.request().arguments().members().isEmpty() && read.request().operation().value().equals(ClockStatusRead.STEP),
                "independent cancellation Status changed original source/session/query");
        var submission = ack.custody().orElseThrow(() -> new IllegalArgumentException("actual CANCEL request custody is absent"));
        submission.verify(ack, attempt.guard());
        NativeRequestChronology.requireBeforeSubmission(before, attempt, ack);
        boolean reconciling = read.request().origin() instanceof CommandOrigin.Reconciliation;
        require(read.contractId().equals(reconciling ? ClockStatusRead.RECONCILIATION_CONTRACT_ID : ClockStatusRead.CONTRACT_ID),
                "CANCEL independent Status changed its installed finite contract");
        var observed = reconciling ? read.request().origin().requireReconciliation().factual() : read.after().binding().observed();
        requireOwner(command, observed);
        require(observed.frame().revision().compareTo(command.before().frame().revision()) >= 0
                && observed.frame().identity().nativeRevision().compareTo(command.before().frame().identity().nativeRevision()) >= 0,
                "independent CANCEL Status regressed actual public/native revisions");
        if (reconciling) NativeRequestChronology.requireReconciledSampledAfter(read, command, attempt, ack);
        else {
            require(read.before().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    && read.after().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    && read.before().paused() && read.after().paused() && read.before().mapReady() && read.after().mapReady()
                    && read.before().playerAlive() && read.after().playerAlive(), "independent CANCEL Status lost actual paused-map read guards");
            NativeRequestChronology.requireSampledAfter(read, attempt, ack);
        }
        require(submission.writeEntered().observedAt().isBefore(command.deadline()), "original CANCEL write escaped its immutable deadline");
        requireOwner(command, full.identity());
        require(full.source().equals(command.source()) && full.sessionId().equals(command.sessionId())
                && AdvancePolicy.truth(full.semantic(), "paused") && AdvancePolicy.truth(full.semantic(), "map_ready")
                && integer(full.semantic().get("speed"), "speed").intValueExact() == actual.speed()
                && full.identity().frame().identity().dateRaw().equals(BigInteger.valueOf(actual.lastObservedDateRaw()))
                && full.identity().frame().identity().dateRaw().compareTo(command.before().frame().identity().dateRaw()) >= 0
                && full.identity().frame().revision().compareTo(command.before().frame().revision()) >= 0
                && full.identity().frame().identity().nativeRevision().compareTo(command.before().frame().identity().nativeRevision()) >= 0
                && full.provenance().independentOf(attempt.requestId()) && full.provenance().independentOf(read.requestId())
                && !full.originalEvidence().equals(archive.referenceOf(ack)) && !full.originalEvidence().equals(archive.referenceOf(read.original())),
                "1210 cancellation lacks the actual same-owner paused Full/date/revisions independent of ACK and Status");
        require(full.provenance() instanceof ObservationProvenance.FreshSnapshotQuery, "1210 cancellation requires actual request-backed Full sampling custody");
        var fresh = (ObservationProvenance.FreshSnapshotQuery) full.provenance();
        if (fresh.basis() instanceof ObservationProvenance.LiveAfterSetter setter)
            require(setter.setterAcknowledgement().equals(archive.referenceOf(ack)), "CANCEL Full borrowed another setter ACK");
        else if (fresh.basis() instanceof ObservationProvenance.ColdAfterAcknowledgement cold) {
            var original = archive.loadReceipt(cold.originalReceipt());
            require(original.command().equals(command) && original.bodySha256().equals(ActionCodec.bodySha256(command))
                    && ActionTransitions.attempt(original.state()).filter(attempt::equals).isPresent()
                    && original.ack().filter(ack::equals).isPresent(), "cold CANCEL Full changed its actual original pending command/ACK");
        } else require(false, "ordinary CANCEL Full cannot borrow another continuation watch basis");
        var fullOriginal = archive.load(fresh.readAcknowledgement());
        require(fullOriginal instanceof NativeActionPort.AckReceived && ((NativeActionPort.AckReceived)fullOriginal).nativeOk(),
                "Full sampling needs its real successful independent ACK");
        var fullAck = (NativeActionPort.AckReceived)fullOriginal;
        var fullCustody = fullAck.custody().orElseThrow(() -> new IllegalArgumentException("actual Full query custody absent"));
        fullCustody.verify(fullAck);
        var statusCustody = read.original().custody().orElseThrow();
        require(fresh.requestId().equals(fullAck.requestId()) && !fresh.requestId().equals(attempt.requestId()) && !fresh.requestId().equals(read.requestId())
                && fullCustody.session().equals(statusCustody.session()) && fullCustody.custodyEpoch().equals(statusCustody.custodyEpoch())
                && !fullCustody.writeEntered().observedAt().isBefore(submission.responseReceived().observedAt())
                && fresh.snapshotReceived().order().compareTo(fullCustody.responseReceived().order()) > 0
                && !fresh.snapshotReceived().observedAt().isBefore(fullCustody.responseReceived().observedAt())
                && full.observedAt().equals(fresh.snapshotReceived().observedAt())
                && !full.observedAt().isAfter(read.request().deadline()), "Full and Status did not sample independently after the original CANCEL ACK within their finite window");
        if (fullCustody.custodyEpoch().equals(submission.custodyEpoch()))
            require(fullCustody.writeEntered().order().compareTo(submission.responseReceived().order()) > 0, "Full query reused a pre-CANCEL event");
    }
    private static void requireTuple(ActionCommand command, Status status) {
        require(new BigInteger(status.generation().decimal()).equals(AdvancePrimitives.cancelGeneration(command.operation().value()))
                && (status.triggerFlags() & (1L << 15)) == 0
                && status.mode() == Mode.TERMINAL_OR_SENTINEL && status.armyCount() == 0
                && status.startingDateRaw() > 0 && status.targetDateRaw() > status.startingDateRaw()
                && (status.targetDateRaw() - (long)status.startingDateRaw()) % 24 == 0,
                "exact original 1210 terminal-a-0 positive generation/date slot required");
    }
    private static void requireOwner(ActionCommand command, ObservationIdentity identity) {
        var before = command.before();
        require(identity.machineId().equals(before.machineId()) && identity.game().equals(before.game())
                && identity.observationVersion() == before.observationVersion()
                && identity.frame().episodeRunId().equals(before.frame().episodeRunId())
                && identity.frame().identity().player().equals(before.frame().identity().player()), "1210 CANCEL changed its exact Game/player/episode owner");
    }
    /** No I/O or freshness reconstruction: reopen and replay the exact recorded pre/Status/Full originals. */
    public static void verifyArchived(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack,
            ActionState.ControlApplied control, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames) {
        JsonNode locator = locator(control);
        require(locator != null && control.supportingReads().isEmpty(), "1210 CANCEL needs exactly one complete original proof locator");
        ExactRef proof = ExactRef.fromJson(locator.get("proof"));
        RawJson bytes = archive.loadMaterial(proof); AdvancePrimitiveEvidence.exact(proof, bytes.bytes());
        var row = StrictJson.object(StrictJson.parse(bytes.bytes()), Set.of("schema", "body_sha256", "request_id", "observed_at",
                "before_read", "status_read", "native_frame", "driver_facts", "provenance"));
        require(StrictJson.text(row.get("schema")).equals(SCHEMA) && StrictJson.text(row.get("body_sha256")).equals(ActionCodec.bodySha256(command))
                && StrictJson.text(row.get("request_id")).equals(attempt.requestId()), "CANCEL proof changed its original command/Attempt");
        PlanningReadReceipt before = preparedRead(command, attempt.preparedRequest(), archive);
        require(ExactRef.fromJson(row.get("before_read")).equals(archive.readReferenceOf(before))
                && ExactRef.fromJson(row.get("status_read")).equals(archive.readReferenceOf(control.read())), "CANCEL proof replaced its original query receipts");
        NativeRecordedEvidenceVerifier.requireRead(before, archive); NativeRecordedEvidenceVerifier.requireRead(control.read(), archive);
        if (!(before.request().origin() instanceof CommandOrigin.PhysicalStatusOnly)) {
            org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(before.before().binding(), archive, frames);
            org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(before.after().binding(), archive, frames);
        }
        var basis = new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(row.get("native_frame")), ExactRef.fromJson(row.get("driver_facts")));
        AdvancePrimitiveEvidence.exact(basis.nativeFrame(), archive.loadNativeFrame(basis.nativeFrame()));
        AdvancePrimitiveEvidence.exact(basis.driverFacts(), archive.loadFullMaterial(basis.driverFacts()).bytes());
        var complete = frames.load(basis, archive);
        var provenance = ObservationProvenanceCodec.decode(row.get("provenance"));
        require(provenance instanceof ObservationProvenance.FreshSnapshotQuery, "archived CANCEL Full lacks its actual sampling query");
        frames.verifyFreshSnapshotQuery((ObservationProvenance.FreshSnapshotQuery)provenance, complete, archive);
        require(complete.originalEvidence().equals(basis.nativeFrame())
                && complete.observedAt().equals(Instant.parse(StrictJson.text(row.get("observed_at")))), "CANCEL Full loader changed original identity/time");
        var full = new AdvanceObservationPort.Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(),
                provenance, complete.observedAt(), complete.originalEvidence());
        validate(command, attempt, ack, before, control.read(), full, archive);
        var retained = references(proof, archive.readReferenceOf(before), archive.readReferenceOf(control.read()),
                basis.nativeFrame(), basis.driverFacts(), provenance);
        require(references(control).equals(retained) && control.actual().equals(actual(ClockStatusRead.decode(control.read().original()), proof, retained)),
                "CANCEL actual fields or retained closure differ from the original proof");
    }
}
