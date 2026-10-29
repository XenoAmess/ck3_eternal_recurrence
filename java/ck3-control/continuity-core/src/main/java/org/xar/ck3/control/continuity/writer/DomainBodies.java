package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Canonical references to original full domain bodies; missing is never evidence of clear state. */
public final class DomainBodies {
    public static final String FIELD = "java_domain_bodies_v1";
    public static final String SCHEMA = "xar.continuity-domain-bodies/v1";
    public static final String IMPORT_KIND = "java_domain_body_import_v1";
    private DomainBodies() { }
    public enum Slot {
        LIFE, OPENING_GATE, OPTIONAL_CADENCE, COUNCIL, CROWN, FACTION, FAMILY, CHILD_MATRILINEAL, DEFAULT_MARRIAGE, RESOLVED_ALLIANCE,
        CONSTRUCTION, MERCENARY, FEAST, PRISONER_RELEASE, PRISONER_RANSOM, SUCCESSION, SWAY,
        ACTIVE_RETREAT, CROSS_RUN_PLANNING, ORDINARY_ONCE_CLAIM, COUNCIL_CONTINUATION, NATURAL_CLOCK_ORIGINALS, RITE_CREATION
    }
    /** Only this finite Natural original closure includes cause/final postquery materials beyond the ordinary domain limit. */
    public static int maximumEvidence(Slot slot) {
        return Objects.requireNonNull(slot)==Slot.NATURAL_CLOCK_ORIGINALS?128:64;
    }
    public enum Reason { UNIMPORTED, SLOT_UNREGISTERED, SOURCE_UNAVAILABLE, BODY_IDENTITY_CHANGED, INVALID_BODY }
    public record BodyRef(Slot slot, String contractSchema, ExactRef payload, FileIdentity identity,
                          List<ExactRef> producerSources) {
        public BodyRef {
            Objects.requireNonNull(slot); StrictJson.text(contractSchema); Objects.requireNonNull(payload); Objects.requireNonNull(identity);
            producerSources = List.copyOf(producerSources); StrictJson.require(!producerSources.isEmpty() && producerSources.size() <= 64, "exact body producer closure");
            StrictJson.require(payload.bytes() == identity.bytes(), "domain payload/native size binding");
        }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("slot", slot.name()); row.put("contract_schema", contractSchema);
            row.set("payload", payload.toJson()); row.set("native_identity",identity.toJson());
            var sources = row.putArray("producer_sources"); producerSources.forEach(ref -> sources.add(ref.toJson())); return row;
        }
        public static BodyRef fromJson(com.fasterxml.jackson.databind.JsonNode value) {
            ObjectNode row = StrictJson.object(value, Set.of("slot", "contract_schema", "payload", "native_identity", "producer_sources"));
            Slot slot;
            try { slot = Slot.valueOf(StrictJson.text(row.get("slot"))); }
            catch (IllegalArgumentException error) { throw new org.xar.ck3.control.contracts.ContractViolationException("domain slot", error); }
            var sources = row.get("producer_sources"); StrictJson.require(sources != null && sources.isArray(), "domain source list required");
            List<ExactRef> refs = new java.util.ArrayList<>(); sources.forEach(ref -> refs.add(ExactRef.fromJson(ref)));
            return new BodyRef(slot, StrictJson.text(row.get("contract_schema")), ExactRef.fromJson(row.get("payload")),FileIdentity.fromJson(row.get("native_identity")),refs);
        }
    }
    public sealed interface Read permits Available, Unavailable { }
    public record Available(BodyRef reference, byte[] canonicalBody, ExactRef head, List<Pin> headSources) implements Read {
        public Available { Objects.requireNonNull(reference); canonicalBody = canonicalBody.clone(); Objects.requireNonNull(head); headSources = List.copyOf(headSources); }
        @Override public byte[] canonicalBody() { return canonicalBody.clone(); }
    }
    public record Unavailable(Reason reason, Optional<ExactRef> head, String detail) implements Read {
        public Unavailable { Objects.requireNonNull(reason); Objects.requireNonNull(head); StrictJson.text(detail); }
    }
    public record ImportRequest(Slot slot, String contractSchema, ExactRef originalBody,
                                byte[] producerInput, List<ExactRef> evidence, String evidenceId) {
        public ImportRequest {
            Objects.requireNonNull(slot); StrictJson.text(contractSchema); Objects.requireNonNull(originalBody);
            producerInput = canonical(producerInput); evidence = List.copyOf(evidence); StrictJson.text(evidenceId);
            StrictJson.require(evidence.size() <= maximumEvidence(slot), "finite domain original evidence for its exact slot");
        }
        @Override public byte[] producerInput() { return producerInput.clone(); }
    }
    /** Host-owned verifier re-runs the original producer/reducer and source/machine/episode guards. */
    @FunctionalInterface public interface Verifier {
        String verify(ContinuityState actualHead, Optional<BodyRef> previousBody, ImportRequest request,
                      byte[] actualOriginalBody) throws IOException;
        default String verify(Head actualHead, Optional<BodyRef> previousBody, ImportRequest request,
                              byte[] actualOriginalBody) throws IOException {
            return verify(actualHead.state(), previousBody, request, actualOriginalBody);
        }
    }
    public record Registration(Slot slot, String contractSchema, int maximumBodyBytes,
                               List<ExactRef> producerSources, Verifier verifier) {
        public Registration {
            Objects.requireNonNull(slot); StrictJson.text(contractSchema); Objects.requireNonNull(verifier);
            StrictJson.require(maximumBodyBytes > 0 && maximumBodyBytes <= ContinuityJson.DOMAIN_MAX_BYTES, "bounded original JSON domain body");
            producerSources = List.copyOf(producerSources);
            StrictJson.require(!producerSources.isEmpty() && producerSources.size() <= 64, "actual original producer source closure required");
        }
    }
    public record PreparedImport(Head predecessor, ImportRequest request, Pin originalBody,
                                 List<Pin> sources, List<Pin> evidence, String preconditionDigest) {
        public PreparedImport { Objects.requireNonNull(predecessor); Objects.requireNonNull(request); Objects.requireNonNull(originalBody);
            sources = List.copyOf(sources); evidence = List.copyOf(evidence); requireDigest(preconditionDigest); }
    }
    /** Read-only historical edge, deliberately different from a warm CAS PreparedImport. */
    public record RecordedImport(Head predecessor,Receipt receipt,ImportRequest request,BodyRef body,
            ExactRef canonicalEvent,List<Pin> currentInputs) {
        public RecordedImport {Objects.requireNonNull(predecessor);Objects.requireNonNull(receipt);Objects.requireNonNull(request);Objects.requireNonNull(body);Objects.requireNonNull(canonicalEvent);currentInputs=List.copyOf(currentInputs);
            StrictJson.require(receipt.disposition()!=Disposition.NO_CHANGE&&receipt.head().sequence()==Math.addExact(predecessor.state().sequence(),1)
                    &&request.slot()==body.slot()&&request.contractSchema().equals(body.contractSchema())
                    &&request.originalBody().bytes()==body.payload().bytes()&&request.originalBody().sha256().equals(body.payload().sha256()),"actual recorded domain edge/body/request mismatch");}
    }
    public interface Store {
        Read read(Slot slot) throws IOException;
        PreparedImport previewImport(ImportRequest request) throws IOException;
        Receipt commitImport(PreparedImport prepared) throws IOException;
    }
    /** Registry shape is strict. A missing registry/slot has no implicit migration or initialization meaning. */
    public static Optional<BodyRef> reference(ContinuityState state, Slot slot) {
        ObjectNode head = state.toJson();
        if (!head.has(FIELD)) return Optional.empty();
        ObjectNode registry = StrictJson.object(head.get(FIELD), Set.of("schema", "entries"));
        StrictJson.require(StrictJson.text(registry.get("schema")).equals(SCHEMA), "explicit domain registry version");
        ObjectNode entries = ContinuityJson.object(registry.get("entries"));
        entries.fields().forEachRemaining(entry -> {
            BodyRef body = BodyRef.fromJson(entry.getValue());
            StrictJson.require(body.slot().name().equals(entry.getKey()), "domain registry slot binding");
        });
        return entries.has(slot.name()) ? Optional.of(BodyRef.fromJson(entries.get(slot.name()))) : Optional.empty();
    }
    public static ContinuityState reduceImport(ContinuityState previous, BodyRef body) {
        ObjectNode after = previous.toJson(); ObjectNode registry;
        if (after.has(FIELD)) { reference(previous, body.slot()); registry = ContinuityJson.object(after.get(FIELD)); }
        else { registry = after.putObject(FIELD); registry.put("schema", SCHEMA); registry.putObject("entries"); }
        ContinuityJson.object(registry.get("entries")).set(body.slot().name(), body.toJson());
        return ContinuityState.fromJson(after, previous.machineId());
    }
}
