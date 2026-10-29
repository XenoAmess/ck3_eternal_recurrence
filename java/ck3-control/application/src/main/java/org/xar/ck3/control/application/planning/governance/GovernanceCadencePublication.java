package org.xar.ck3.control.application.planning.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.planning.optionalcadence.OptionalCheckCadence;

/** Ordered no-action reads, their actual replay, and one same-writer cadence publication. */
public final class GovernanceCadencePublication implements DomainBodies.Verifier {
    public static final String FIELD = "governance_cadence_plan";
    public static final String SCHEMA = "xar.java-governance-cadence-plan/v1";
    public static final String INPUT_SCHEMA = "xar.java-governance-cadence-publication/v1";
    public static final String TECHNICAL_SCHEMA = "xar.java-governance-cadence-plan/v2";
    public record Plan(ObservationIdentity observed, G2Source source, String sessionId,
            CadenceModels.State before, List<CadenceModels.Domain> completeNoActionDomains,
            Optional<ExactRef> councilTechnicalFailure) {
        public Plan(ObservationIdentity observed, G2Source source, String sessionId,
                CadenceModels.State before, List<CadenceModels.Domain> completeNoActionDomains) {
            this(observed, source, sessionId, before, completeNoActionDomains, Optional.empty());
        }
        public Plan {
            Objects.requireNonNull(observed); Objects.requireNonNull(source); StrictJson.text(sessionId); Objects.requireNonNull(before);
            completeNoActionDomains = List.copyOf(completeNoActionDomains); Objects.requireNonNull(councilTechnicalFailure);
            StrictJson.require(source.machineId().equals(observed.machineId()) && before.episodeRunId().equals(observed.frame().episodeRunId())
                    && (!completeNoActionDomains.isEmpty() || councilTechnicalFailure.isPresent())
                    && completeNoActionDomains.size() <= CadenceModels.Domain.values().length
                    && completeNoActionDomains.stream().distinct().count() == completeNoActionDomains.size(), "exact bounded ordered cadence plan required");
            StrictJson.require(councilTechnicalFailure.isEmpty() || councilTechnicalFailure.orElseThrow().bytes() > 0
                    && !completeNoActionDomains.contains(CadenceModels.Domain.COUNCIL),
                    "technical Council read cannot receive completed no-action credit");
        }
    }
    public record Material(byte[] previousBody, Plan actualReplayedPlan, List<ExactRef> originalReadEvidence) {
        public Material {
            previousBody = previousBody.clone(); Objects.requireNonNull(actualReplayedPlan); originalReadEvidence = List.copyOf(originalReadEvidence);
            StrictJson.require(!originalReadEvidence.isEmpty() && originalReadEvidence.size() <= 32, "actual complete-read evidence closure required");
        }
        @Override public byte[] previousBody() { return previousBody.clone(); }
    }
    /** Root must replay the actual domain policies over their archived original receipts, never echo the requested plan. */
    @FunctionalInterface public interface MaterialPort {
        Material replay(WriterContracts.Head actualHead, DomainBodies.BodyRef previous, Plan requested,
                List<ExactRef> originalReadEvidence) throws IOException;
    }
    @FunctionalInterface public interface ImmutableBodyPort { ExactRef publish(String evidenceId, byte[] canonicalBody) throws IOException; }
    public sealed interface Publication permits Changed, AlreadyCurrent { }
    public record Changed(WriterContracts.Receipt committed, ExactRef body) implements Publication {
        public Changed { Objects.requireNonNull(committed); Objects.requireNonNull(body); }
    }
    public record AlreadyCurrent(ExactRef actualHead) implements Publication { public AlreadyCurrent { Objects.requireNonNull(actualHead); } }
    private record Input(Plan plan, ExactRef previousBody, List<ExactRef> originalReadEvidence) {
        private Input { Objects.requireNonNull(plan); Objects.requireNonNull(previousBody); originalReadEvidence = List.copyOf(originalReadEvidence);
            StrictJson.require(!originalReadEvidence.isEmpty() && originalReadEvidence.size() <= 32 && originalReadEvidence.stream().allMatch(ref -> ref.bytes() > 0)
                    && originalReadEvidence.stream().distinct().count() == originalReadEvidence.size(), "actual bounded distinct cadence original reads required"); }
    }
    private final Path originalWriterLock;
    private final GovernanceBorrowedSession.Authority authority;
    private final List<ExactRef> producerSources;
    private final MaterialPort materials;
    private final ImmutableBodyPort bodies;
    public GovernanceCadencePublication(Path originalWriterLock, GovernanceBorrowedSession.Authority authority,
            List<ExactRef> producerSources, MaterialPort materials, ImmutableBodyPort bodies) {
        this.originalWriterLock = Objects.requireNonNull(originalWriterLock); this.authority = Objects.requireNonNull(authority);
        this.producerSources = List.copyOf(producerSources); this.materials = Objects.requireNonNull(materials); this.bodies = Objects.requireNonNull(bodies);
        StrictJson.require(originalWriterLock.isAbsolute() && !this.producerSources.isEmpty() && this.producerSources.size() <= 32
                && this.producerSources.stream().allMatch(ref -> ref.bytes() > 0), "actual cadence writer/source authority required");
    }
    public DomainBodies.Registration registration() {
        return new DomainBodies.Registration(DomainBodies.Slot.OPTIONAL_CADENCE, CadenceModels.SCHEMA, 1_048_576, producerSources, this);
    }
    public static OpportunityJson.Obj append(OpportunityJson.Obj detail, CadenceModels.Domain domain,
            PlanningRequest request, CadenceModels.State before) {
        Objects.requireNonNull(detail); Objects.requireNonNull(domain); Objects.requireNonNull(request); Objects.requireNonNull(before);
        StrictJson.require(detail.get("governance_required_cadence_intent") == null, "unmigrated single cadence intent producer remains selected");
        Optional<Plan> existing = fromDetail(detail);
        var domains = new ArrayList<CadenceModels.Domain>();
        if (existing.isPresent()) {
            Plan current = existing.orElseThrow();
            StrictJson.require(current.observed().equals(request.before()) && current.source().equals(request.source())
                    && current.sessionId().equals(request.sessionId()) && current.before().equals(before), "cadence stages crossed their original full plan frame or state");
            domains.addAll(current.completeNoActionDomains());
        }
        if (!domains.contains(domain)) domains.add(domain);
        Plan next = new Plan(request.before(), request.source(), request.sessionId(), before, domains,
                existing.flatMap(Plan::councilTechnicalFailure));
        return detail.with(FIELD, OpportunityJson.parse(encode(next)));
    }
    /** Pure intent only. The private transcript must replay the actual failed-read producer before publication. */
    public static OpportunityJson.Obj appendCouncilTechnical(OpportunityJson.Obj detail, PlanningRequest request,
            CadenceModels.State before, ExactRef diagnostic) {
        Objects.requireNonNull(detail); Objects.requireNonNull(request); Objects.requireNonNull(before); Objects.requireNonNull(diagnostic);
        StrictJson.require(detail.get("governance_required_cadence_intent") == null, "unmigrated single cadence intent producer remains selected");
        Optional<Plan> existing = fromDetail(detail);
        List<CadenceModels.Domain> domains = List.of();
        if (existing.isPresent()) {
            Plan current = existing.orElseThrow();
            StrictJson.require(current.observed().equals(request.before()) && current.source().equals(request.source())
                    && current.sessionId().equals(request.sessionId()) && current.before().equals(before)
                    && current.councilTechnicalFailure().filter(ref -> !ref.equals(diagnostic)).isEmpty(),
                    "technical Council cadence crossed its exact original frame/state/diagnostic");
            domains = current.completeNoActionDomains();
        }
        return detail.with(FIELD, OpportunityJson.parse(encode(new Plan(request.before(), request.source(), request.sessionId(),
                before, domains, Optional.of(diagnostic)))));
    }
    public static Optional<Plan> fromDetail(OpportunityJson.Obj detail) {
        Objects.requireNonNull(detail); var value = detail.get(FIELD);
        return value == null ? Optional.empty() : Optional.of(decode(OpportunityJson.encode(value)));
    }
    public static CadenceModels.State reduce(Plan plan) {
        CadenceModels.State after = plan.before(); var frame = plan.observed().frame();
        var marker = new CadenceModels.Frame(frame.episodeRunId(), frame.identity().dateRaw(), frame.identity().nativeRevision());
        for (var domain : plan.completeNoActionDomains())
            after = OptionalCheckCadence.observeRead(after, domain, marker, CadenceModels.ReadCompletion.COMPLETE_NO_ACTION);
        if (plan.councilTechnicalFailure().isPresent())
            after = OptionalCheckCadence.deferCouncilTechnicalRead(after, marker, plan.councilTechnicalFailure().orElseThrow().path());
        return after;
    }
    /** Must run before executing the chosen command; Changed requires fresh planning against the new head. */
    public Publication publish(ContinuityStorePort.Session session, Plan plan, List<ExactRef> originalReadEvidence) throws IOException {
        authority.requireSession(session); session.requireWriter(originalWriterLock);
        var actual = available(session.readDomain(DomainBodies.Slot.OPTIONAL_CADENCE));
        Input input = new Input(plan, actual.reference().payload(), originalReadEvidence); WriterContracts.Head head = session.head();
        requirePrevious(head, actual.reference(), input);
        Material material = materials.replay(head, actual.reference(), plan, input.originalReadEvidence());
        byte[] after = replay(input, material);
        StrictJson.require(CadenceJson.readState(actual.canonicalBody(), plan.before().episodeRunId()).equals(
                CadenceJson.readState(material.previousBody(), plan.before().episodeRunId())), "cadence replay did not read the actual same-head original body");
        if (reduce(plan).equals(plan.before())) return new AlreadyCurrent(session.persistedHead());
        String evidenceId = "governance-cadence-" + org.xar.ck3.control.application.action.ActionCodec.sha256(encodeInput(input));
        ExactRef output = bodies.publish(evidenceId, after); exact(output, after);
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.OPTIONAL_CADENCE, CadenceModels.SCHEMA, output,
                encodeInput(input), evidence(input), evidenceId);
        var prepared = session.previewImport(request);
        StrictJson.require(prepared.predecessor().digest().equals(head.digest()), "cadence preparation crossed its original writer head");
        var committed = session.commitImport(prepared); var published = available(session.readDomain(DomainBodies.Slot.OPTIONAL_CADENCE));
        StrictJson.require(committed.disposition() != WriterContracts.Disposition.NO_CHANGE && published.reference().payload().equals(output)
                && Arrays.equals(published.canonicalBody(), after), "actual cadence publication/readback required");
        authority.requireSession(session); session.requireWriter(originalWriterLock);
        return new Changed(committed, output);
    }
    @Override public String verify(ContinuityState head, Optional<DomainBodies.BodyRef> previous,
            DomainBodies.ImportRequest request, byte[] actualOriginalBody) throws IOException {
        throw new IOException("cadence qualification requires the actual locked Head and original complete-read replay");
    }
    @Override public String verify(WriterContracts.Head head, Optional<DomainBodies.BodyRef> previous,
            DomainBodies.ImportRequest request, byte[] actualOriginalBody) throws IOException {
        StrictJson.require(request.slot() == DomainBodies.Slot.OPTIONAL_CADENCE && request.contractSchema().equals(CadenceModels.SCHEMA), "unique cadence slot/schema required");
        Input input = decodeInput(request.producerInput()); var original = previous.orElseThrow(() -> new IllegalArgumentException("missing cadence is not an initialized state"));
        requirePrevious(head, original, input); StrictJson.require(request.evidence().equals(evidence(input)), "complete ordered cadence source evidence required");
        byte[] expected = replay(input, materials.replay(head, original, input.plan(), input.originalReadEvidence()));
        StrictJson.require(Arrays.equals(expected, CadenceJson.writeState(CadenceJson.readState(actualOriginalBody, input.plan().before().episodeRunId()))),
                "actual original completed-read reducer differs from the proposed cadence body");
        ObjectNode proof = StrictJson.object().put("head", head.digest()).put("input", org.xar.ck3.control.application.action.ActionCodec.sha256(encodeInput(input)))
                .put("body", org.xar.ck3.control.application.action.ActionCodec.sha256(expected));
        return ContinuityJson.digest(proof);
    }
    private void requirePrevious(WriterContracts.Head head, DomainBodies.BodyRef previous, Input input) {
        StrictJson.require(head.state().machineId().equals(input.plan().observed().machineId()) && previous.slot() == DomainBodies.Slot.OPTIONAL_CADENCE
                && previous.contractSchema().equals(CadenceModels.SCHEMA)
                && previous.payload().equals(input.previousBody())
                && DomainBodies.reference(head.state(), DomainBodies.Slot.OPTIONAL_CADENCE).filter(previous::equals).isPresent(), "cadence same-head original source custody required");
    }
    private static byte[] replay(Input input, Material actual) {
        exact(input.previousBody(), actual.previousBody());
        StrictJson.require(actual.actualReplayedPlan().equals(input.plan()) && actual.originalReadEvidence().equals(input.originalReadEvidence())
                && CadenceJson.readState(actual.previousBody(), input.plan().before().episodeRunId()).equals(input.plan().before()),
                "actual complete ordinary-policy replay/frame/evidence differs from the requested plan");
        return CadenceJson.writeState(reduce(actual.actualReplayedPlan()));
    }
    public static byte[] encode(Plan plan) {
        ObjectNode row = StrictJson.object().put("schema", plan.councilTechnicalFailure().isPresent() ? TECHNICAL_SCHEMA : SCHEMA).put("session_id", plan.sessionId());
        row.set("observation", ProposalLifecycleCodec.observation(plan.observed())); row.set("source", ProposalLifecycleCodec.source(plan.source()));
        row.set("before", StrictJson.parse(CadenceJson.writeState(plan.before()))); var domains = row.putArray("complete_no_action_domains");
        plan.completeNoActionDomains().forEach(domain -> domains.add(domain.wire()));
        plan.councilTechnicalFailure().ifPresent(ref -> row.set("council_technical_failure", ref.toJson()));
        return StrictJson.canonical(row);
    }
    public static Plan decode(byte[] bytes) {
        var parsed = StrictJson.parse(bytes);
        boolean technical = TECHNICAL_SCHEMA.equals(StrictJson.text(parsed.get("schema")));
        ObjectNode row = StrictJson.object(parsed, technical
                ? Set.of("schema", "session_id", "observation", "source", "before", "complete_no_action_domains", "council_technical_failure")
                : Set.of("schema", "session_id", "observation", "source", "before", "complete_no_action_domains"));
        StrictJson.require(technical || StrictJson.text(row.get("schema")).equals(SCHEMA), "explicit ordered cadence plan schema required");
        var observed = ProposalLifecycleCodec.decodeObservation(row.get("observation")); var entries = row.get("complete_no_action_domains");
        StrictJson.require(entries.isArray(), "ordered cadence domains must be an array"); var domains = new ArrayList<CadenceModels.Domain>();
        entries.forEach(value -> domains.add(CadenceModels.Domain.fromWire(StrictJson.text(value))));
        return new Plan(observed, G2Wire.source(row.get("source")), StrictJson.text(row.get("session_id")),
                CadenceJson.readState(StrictJson.canonical(row.get("before")), observed.frame().episodeRunId()), domains,
                technical ? Optional.of(ExactRef.fromJson(row.get("council_technical_failure"))) : Optional.empty());
    }
    private static byte[] encodeInput(Input input) {
        ObjectNode row = StrictJson.object().put("schema", INPUT_SCHEMA); row.set("plan", StrictJson.parse(encode(input.plan())));
        row.set("previous_body", input.previousBody().toJson()); var reads = row.putArray("original_read_evidence"); input.originalReadEvidence().forEach(ref -> reads.add(ref.toJson()));
        return StrictJson.canonical(row);
    }
    private static Input decodeInput(byte[] bytes) {
        ObjectNode row = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "plan", "previous_body", "original_read_evidence"));
        StrictJson.require(StrictJson.text(row.get("schema")).equals(INPUT_SCHEMA) && row.get("original_read_evidence").isArray(), "explicit cadence publication input required");
        var refs = new ArrayList<ExactRef>(); row.get("original_read_evidence").forEach(value -> refs.add(ExactRef.fromJson(value)));
        return new Input(decode(StrictJson.canonical(row.get("plan"))), ExactRef.fromJson(row.get("previous_body")), refs);
    }
    private static List<ExactRef> evidence(Input input) {
        var result = new ArrayList<ExactRef>(); result.add(input.previousBody()); result.add(input.plan().source().sourceRef()); result.addAll(input.originalReadEvidence()); return List.copyOf(result);
    }
    private static DomainBodies.Available available(DomainBodies.Read read) throws IOException {
        if (read instanceof DomainBodies.Available actual) return actual;
        throw new IOException("actual cadence body unavailable; no implicit clear/empty initialization");
    }
    private static void exact(ExactRef reference, byte[] bytes) {
        StrictJson.require(reference.bytes() == bytes.length && reference.sha256().equals(org.xar.ck3.control.application.action.ActionCodec.sha256(bytes)), "actual cadence source bytes/SHA differ");
    }
}
