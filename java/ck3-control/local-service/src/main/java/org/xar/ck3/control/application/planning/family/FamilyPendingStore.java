package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Same original writer pre-intent import. Root supplies actual Driver/Bridge/native preparation and its archived replay. */
public final class FamilyPendingStore implements ActionPorts.IntentPreparationPort {
    public static final String INPUT_SCHEMA = "xar.java.family-pending-producer-input/v2";
    private static final int MAX = ContinuityJson.DOMAIN_MAX_BYTES;
    private static final List<Slot> SLOTS = List.of(Slot.FAMILY, Slot.CHILD_MATRILINEAL, Slot.DEFAULT_MARRIAGE);
    public record Basis(Obj snapshot, FamilyPorts.BridgeIdentity bridge, ExactRef snapshotEvidence,
            ExactRef bridgeEvidence, List<ExactRef> nativePreparationEvidence, Obj preparedPlan,FamilyNativePreparation.MaterializedSend materializedSend) {
        public Basis {
            Objects.requireNonNull(snapshot); Objects.requireNonNull(bridge); Objects.requireNonNull(snapshotEvidence); Objects.requireNonNull(bridgeEvidence);
            Objects.requireNonNull(preparedPlan);
            Objects.requireNonNull(materializedSend);
            nativePreparationEvidence = List.copyOf(nativePreparationEvidence);
            if (snapshotEvidence.bytes() <= 0 || bridgeEvidence.bytes() <= 0 || nativePreparationEvidence.isEmpty() || nativePreparationEvidence.size() > 16
                    || new java.util.HashSet<>(nativePreparationEvidence).size() != nativePreparationEvidence.size())
                throw new IllegalArgumentException("actual original frame, Bridge identity and fresh full native preparation evidence required");
        }
    }
    public interface Sources {
        /** Re-read all original selected terms, including the full child comparator and final selected proof, inside this held owner/session. */
        Basis current(ContinuityStorePort.Session originalSession, ActionCommand command) throws IOException;
        /** Decode the actual original Driver/Bridge/native read packets and redo the same complete preparation; no live query, token-only or constructor fallback. */
        Basis replay(ActionCommand command, ExactRef snapshotEvidence, ExactRef bridgeEvidence,
                List<ExactRef> nativePreparationEvidence) throws IOException;
    }
    private final ImmutableArtifactStore artifacts;
    private final Sources sources;
    public FamilyPendingStore(ImmutableArtifactStore artifacts, Sources sources) { this.artifacts = Objects.requireNonNull(artifacts); this.sources = Objects.requireNonNull(sources); }
    @Override public void prepare(ContinuityStorePort.Session originalSession, ActionCommand command) {
        Objects.requireNonNull(originalSession); Objects.requireNonNull(command);
        if (!FamilyPendingProducer.supports(command)) throw new IllegalArgumentException("family pre-intent dispatcher received another operation");
        try {
            if (!originalSession.head().state().machineId().equals(command.source().machineId())) throw new IllegalArgumentException("family pre-intent writer machine differs");
            Basis basis = sources.current(originalSession, command);
            Map<Slot, DomainBodies.Available> bodies = new EnumMap<>(Slot.class);
            for (Slot slot : SLOTS) {
                DomainBodies.Read read = originalSession.readDomain(slot);
                if (!(read instanceof DomainBodies.Available body)) throw new IllegalArgumentException("original full family documents must be imported before any family action");
                bodies.put(slot, body);
            }
            var produced = FamilyPendingProducer.produce(command, basis.snapshot(), basis.bridge(), state(bodies), basis.preparedPlan(),basis.materializedSend());
            var body = artifacts.publish(canonical(produced.body()), MAX);
            var commandBody = artifacts.publish(ActionCodec.encodeCommand(command), ActionCodec.MAX_COMMAND_BYTES);
            Obj bodyRefs = obj(); List<ExactRef> evidence = new ArrayList<>();
            for (Slot slot : SLOTS) { ExactRef reference = bodies.get(slot).reference().payload(); bodyRefs = bodyRefs.with(slot.name(), ref(reference)); evidence.add(reference); }
            evidence.add(commandBody.reference()); evidence.add(basis.snapshotEvidence()); evidence.add(basis.bridgeEvidence()); evidence.addAll(basis.nativePreparationEvidence());
            Obj input = obj("schema", t(INPUT_SCHEMA), "command", ref(commandBody.reference()), "original_bodies", bodyRefs,
                    "snapshot_evidence", ref(basis.snapshotEvidence()), "bridge_evidence", ref(basis.bridgeEvidence()),
                    "native_preparation_evidence", new Arr(basis.nativePreparationEvidence().stream().<Value>map(FamilyPendingStore::ref).toList()));
            var request = new DomainBodies.ImportRequest(produced.branch().slot(), FamilyDomainSource.schema(produced.branch().slot()), body.reference(),
                    canonical(input), evidence, "family-before-intent-" + command.actionId());
            originalSession.commitImport(originalSession.previewImport(request));
        } catch (IOException failure) { throw new java.io.UncheckedIOException("family original same-writer pre-intent import unavailable", failure); }
    }
    /** One registration per original slot handles both pending and result producers; never register two writers for a slot. */
    public DomainBodies.Registration registration(Slot slot, List<ExactRef> actualProducerSources, FamilyMaterialStore materialResults) {
        if (!SLOTS.contains(slot)) throw new IllegalArgumentException("family slot required"); Objects.requireNonNull(materialResults);
        DomainBodies.Registration results = materialResults.registration(slot, actualProducerSources);
        return new DomainBodies.Registration(slot, FamilyDomainSource.schema(slot), MAX, actualProducerSources, (head, previous, request, actualBody) -> {
            Obj input = decodeDomain(request.producerInput());
            if (!INPUT_SCHEMA.equals(string(input.get("schema")))) return results.verifier().verify(head, previous, request, actualBody);
            if (!input.members().keySet().equals(java.util.Set.of("schema", "command", "original_bodies", "snapshot_evidence", "bridge_evidence", "native_preparation_evidence")))
                throw new IllegalArgumentException("closed family pending producer input required");
            var retained = previous.orElseThrow(() -> new IllegalArgumentException("missing original family ledger never means empty"));
            if (request.slot() != slot || !FamilyDomainSource.schema(slot).equals(request.contractSchema())) throw new IllegalArgumentException("family pending slot/schema differs");
            ExactRef commandRef = reference(input.get("command")); ActionCommand command = ActionCodec.decodeCommand(artifacts.read(commandRef, ActionCodec.MAX_COMMAND_BYTES));
            if (!FamilyPendingProducer.supports(command) || FamilyPendingProducer.branch(command.operation()).slot() != slot
                    || !command.source().machineId().equals(head.machineId())) throw new IllegalArgumentException("family pending command operation/machine differs");
            Obj refs = object(input.get("original_bodies")); Map<Slot, Obj> bodies = new EnumMap<>(Slot.class);
            if (!refs.members().keySet().equals(java.util.Set.of("FAMILY", "CHILD_MATRILINEAL", "DEFAULT_MARRIAGE"))) throw new IllegalArgumentException("all three exact original family documents required");
            for (Slot current : SLOTS) {
                ExactRef reference = reference(refs.get(current.name()));
                var actual = DomainBodies.reference(head, current).orElseThrow(() -> new IllegalArgumentException("full family registry is not imported"));
                if (!actual.payload().equals(reference) || current == slot && !retained.payload().equals(reference) || !request.evidence().contains(reference))
                    throw new IllegalArgumentException("family pending original document/predecessor changed");
                bodies.put(current, FamilyDomainSource.validate(current, artifacts.read(reference, MAX)));
            }
            ExactRef snapshot = reference(input.get("snapshot_evidence")), bridge = reference(input.get("bridge_evidence"));
            List<ExactRef> preparations = array(input.get("native_preparation_evidence")).stream().map(FamilyPendingStore::reference).toList();
            List<ExactRef> originals = new ArrayList<>(List.of(commandRef, snapshot, bridge)); originals.addAll(preparations);
            if (!request.evidence().containsAll(originals)) throw new IllegalArgumentException("family original preparation evidence missing");
            Basis basis = sources.replay(command, snapshot, bridge, preparations);
            if (!basis.snapshotEvidence().equals(snapshot) || !basis.bridgeEvidence().equals(bridge) || !basis.nativePreparationEvidence().equals(preparations))
                throw new IllegalArgumentException("family archived source decoder changed original evidence identity");
            var produced = FamilyPendingProducer.produce(command, basis.snapshot(), basis.bridge(),
                    new FamilyPendingProducer.State(bodies.get(Slot.FAMILY), bodies.get(Slot.CHILD_MATRILINEAL), bodies.get(Slot.DEFAULT_MARRIAGE)), basis.preparedPlan(),basis.materializedSend());
            FamilyDomainSource.validate(slot, actualBody);
            if (!Arrays.equals(canonical(produced.body()), actualBody)) throw new IllegalArgumentException("family pending body differs from complete original producer replay");
            return ActionCodec.sha256(canonical(obj("actual_head_digest", t(ContinuityJson.digest(head.toJson())), "input", input,
                    "output_sha256", t(ActionCodec.sha256(actualBody)))));
        });
    }
    private static FamilyPendingProducer.State state(Map<Slot, DomainBodies.Available> bodies) {
        return new FamilyPendingProducer.State(FamilyDomainSource.validate(Slot.FAMILY, bodies.get(Slot.FAMILY).canonicalBody()),
                FamilyDomainSource.validate(Slot.CHILD_MATRILINEAL, bodies.get(Slot.CHILD_MATRILINEAL).canonicalBody()),
                FamilyDomainSource.validate(Slot.DEFAULT_MARRIAGE, bodies.get(Slot.DEFAULT_MARRIAGE).canonicalBody()));
    }
    private static byte[] canonical(Obj value) { return ContinuityJson.canonical(OpportunityJson.toNode(value), MAX); }
    private static Obj ref(ExactRef reference) { return object(OpportunityJson.parse(reference.toJson().toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))); }
    private static ExactRef reference(Value value) { return ExactRef.fromJson(OpportunityJson.toNode(value)); }
}
