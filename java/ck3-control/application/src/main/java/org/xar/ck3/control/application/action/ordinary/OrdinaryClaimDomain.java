package org.xar.ck3.control.application.action.ordinary;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims.*;

/** Two original-writer transactions: consume a verified next intent first, then durably claim before send. */
public final class OrdinaryClaimDomain {
    public static final String INPUT_SCHEMA = "xar.ck3.ordinary-once-claim-reducer-input/v1";
    public interface Artifacts {
        ExactRef publish(ContinuityStorePort.Session same, byte[] original);
        byte[] read(ExactRef original);
    }
    /** Root supplies an immutable, source-bound implementation which reads actual event/save consumption evidence. */
    public interface PermitAuthority {
        Permit requireNextIntent(ContinuityStorePort.Session same, State before, Request request);
        void verifyOriginal(State before, Request request, Permit permit);
    }
    /** The migration seed must come from complete original claim files, not a missing directory interpreted as empty. */
    @FunctionalInterface public interface SeedAuthority {
        State readOriginalSeed(ExactRef originalClaimManifest, ContinuityState actualHead);
    }
    private final Path originalWriterLock;
    private final Artifacts artifacts;
    private final PermitAuthority permits;
    private final ThreadLocal<String> liveClaimRequest = new ThreadLocal<>();
    public OrdinaryClaimDomain(Path originalWriterLock, Artifacts artifacts, PermitAuthority permits) {
        this.originalWriterLock = Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();
        this.artifacts = Objects.requireNonNull(artifacts); this.permits = Objects.requireNonNull(permits);
    }
    public RetainedClaim claim(ContinuityStorePort.Session same, Request request) {
        try {
            same.requireWriter(originalWriterLock);
            DomainBodies.Available original = available(same); State before = decode(original.canonicalBody());
            if (before.latest(request.identity()).isPresent()) {
                Permit permit = permits.requireNextIntent(same, before, request); permits.verifyOriginal(before, request, permit);
                State consumed = consume(before, request, permit);
                // A later publication/claim failure deliberately leaves this original permit consumed.
                commit(same, original, consumed, input("CONSUME", request, Optional.of(permit), Optional.empty(), Optional.empty()), evidence(original, permit));
                original = available(same); before = decode(original.canonicalBody());
                StrictJson.require(before.equals(consumed), "writer did not persist the actual permit consumption");
            }
            StrictJson.require(liveClaimRequest.get() == null, "ordinary claim publication cannot nest");
            liveClaimRequest.set(request.requestId());
            try {
                Claim prepared = prepareClaim(before, request);
                byte[] claimBody = encodeClaim(prepared); ExactRef claimRef = publish(same, claimBody);
                RetainedClaim retained = new RetainedClaim(prepared, claimRef); State after = append(before, retained);
                List<ExactRef> evidence = new ArrayList<>(List.of(original.reference().payload(), claimRef));
                prepared.lineage().ifPresent(lineage -> evidence.addAll(permitEvidence(lineage.permit())));
                commit(same, original, after, input("CLAIM", request, Optional.empty(), Optional.of(claimRef), Optional.empty()), List.copyOf(evidence));
                State actual = decode(available(same).canonicalBody()); StrictJson.require(actual.equals(after), "writer claim readback differs");
                return retained;
            } finally { liveClaimRequest.remove(); }
        } catch (IOException error) { throw new UncheckedIOException("ordinary once claim unavailable; never dispatch", error); }
    }
    public RetainedClaim requireClaim(ContinuityStorePort.Session same, String requestId) {
        try {
            same.requireWriter(originalWriterLock);
            List<RetainedClaim> found = decode(available(same).canonicalBody()).claims().stream()
                    .filter(row -> row.claim().request().requestId().equals(requestId)).toList();
            StrictJson.require(found.size() == 1, "exact durable ordinary request claim required"); return found.getFirst();
        } catch (IOException error) { throw new UncheckedIOException("actual ordinary claim unavailable", error); }
    }
    public DomainBodies.Registration registration(List<ExactRef> exactProducerSources, SeedAuthority originalSeed) {
        List<ExactRef> sources = List.copyOf(exactProducerSources); Objects.requireNonNull(originalSeed);
        return new DomainBodies.Registration(DomainBodies.Slot.ORDINARY_ONCE_CLAIM, SCHEMA, MAX_BYTES, sources,
                (actualHead, previous, request, originalBody) -> {
                    ObjectNode n = StrictJson.object(StrictJson.parse(request.producerInput(), MAX_BYTES),
                            Set.of("schema", "kind", "request", "permit", "claim_ref", "original_claim_manifest"));
                    StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(n.get("schema"))), "claim reducer input schema");
                    String kind = StrictJson.text(n.get("kind")); State expected;
                    if (kind.equals("LEGACY_SEED") || kind.equals("FRESH_SEED")) {
                        StrictJson.require(previous.isEmpty() && n.get("request").isNull() && n.get("permit").isNull()
                                && n.get("claim_ref").isNull(), "seed only imports the complete original domain once");
                        ExactRef manifest = ExactRef.fromJson(n.get("original_claim_manifest"));
                        StrictJson.require(request.evidence().contains(manifest), "complete original claim manifest must be pinned evidence");
                        expected = Objects.requireNonNull(originalSeed.readOriginalSeed(manifest, actualHead));
                    } else {
                        StrictJson.require(previous.isPresent() && n.get("original_claim_manifest").isNull(), "unimported claim domain is unavailable");
                        State before = decode(read(previous.orElseThrow().payload())); Request next = readRequest(n.get("request"));
                        if (kind.equals("CONSUME")) {
                            StrictJson.require(n.get("claim_ref").isNull(), "permit consumption precedes claim publication");
                            Permit permit = readPermit(n.get("permit"));
                            StrictJson.require(request.evidence().containsAll(permitEvidence(permit)), "all original permit verifier evidence must be pinned");
                            permits.verifyOriginal(before, next, permit); expected = consume(before, next, permit);
                        } else {
                            StrictJson.require(kind.equals("CLAIM") && n.get("permit").isNull(), "closed ordinary reducer transition");
                            StrictJson.require(next.requestId().equals(liveClaimRequest.get()),
                                    "a persisted consumed permit cannot resume a crashed claim publication");
                            ExactRef claimRef = ExactRef.fromJson(n.get("claim_ref")); Claim claim = prepareClaim(before, next);
                            StrictJson.require(Arrays.equals(read(claimRef), encodeClaim(claim)) && request.evidence().contains(claimRef), "actual immutable claim body differs");
                            claim.lineage().ifPresent(lineage -> {
                                StrictJson.require(request.evidence().containsAll(permitEvidence(lineage.permit())), "claim retains original consumption inputs");
                                permits.verifyOriginal(before, next, lineage.permit());
                            });
                            expected = append(before, new RetainedClaim(claim, claimRef));
                        }
                    }
                    StrictJson.require(Arrays.equals(encode(expected), originalBody), "actual claim body differs from real reducer replay");
                    return ActionCodec.sha256(originalBody);
                });
    }
    public void importOriginal(ContinuityStorePort.Session same, ExactRef completeOriginalClaimManifest, State actualOriginalState) throws IOException {
        importSeed(same,completeOriginalClaimManifest,actualOriginalState,"LEGACY_SEED");
    }
    /** Actual fresh campaign automation history uses its own reducer input kind, without a legacy census. */
    public void initializeFresh(ContinuityStorePort.Session same,ExactRef freshCampaign,State actualInitialState)throws IOException {
        importSeed(same,freshCampaign,actualInitialState,"FRESH_SEED");
    }
    private void importSeed(ContinuityStorePort.Session same,ExactRef completeOriginalClaimManifest,State actualOriginalState,String kind)throws IOException {
        same.requireWriter(originalWriterLock);
        StrictJson.require(same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM) instanceof DomainBodies.Unavailable unavailable
                &&unavailable.reason()==DomainBodies.Reason.UNIMPORTED,
                "ordinary claims may only be initialized into an unimported domain");
        byte[] body = encode(actualOriginalState); ExactRef source = publish(same, body);
        byte[] producer = input(kind, null, Optional.empty(), Optional.empty(), Optional.of(completeOriginalClaimManifest));
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.ORDINARY_ONCE_CLAIM, SCHEMA, source, producer,
                List.of(completeOriginalClaimManifest), "ordinary-original-seed-" + source.sha256());
        same.commitImport(same.previewImport(request));
        StrictJson.require(Arrays.equals(available(same).canonicalBody(), body), "original ordinary domain adoption readback differs");
    }
    private void commit(ContinuityStorePort.Session same, DomainBodies.Available previous, State next, byte[] input, List<ExactRef> evidence) throws IOException {
        same.requireWriter(originalWriterLock); byte[] body = encode(next); ExactRef ref = publish(same, body);
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.ORDINARY_ONCE_CLAIM, SCHEMA, ref, input, evidence,
                "ordinary-transition-" + previous.reference().payload().sha256() + "-" + ref.sha256());
        same.commitImport(same.previewImport(request));
    }
    private DomainBodies.Available available(ContinuityStorePort.Session same) throws IOException {
        DomainBodies.Read read = same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM);
        if (!(read instanceof DomainBodies.Available actual)) throw new IOException("complete original once-claim domain is unavailable; no implicit empty state");
        StrictJson.require(actual.reference().contractSchema().equals(SCHEMA), "ordinary domain contract"); return actual;
    }
    private ExactRef publish(ContinuityStorePort.Session same, byte[] raw) {
        ExactRef ref = artifacts.publish(same, raw.clone()); StrictJson.require(ref.bytes() == raw.length
                && ref.sha256().equals(ActionCodec.sha256(raw)) && Arrays.equals(read(ref), raw), "exact durable ordinary artifact publication required"); return ref;
    }
    private byte[] read(ExactRef ref) {
        byte[] raw = artifacts.read(ref); StrictJson.require(raw.length == ref.bytes() && ref.sha256().equals(ActionCodec.sha256(raw)), "original ordinary artifact changed"); return raw;
    }
    private static List<ExactRef> evidence(DomainBodies.Available previous, Permit permit) {
        List<ExactRef> refs = new ArrayList<>(List.of(previous.reference().payload())); refs.addAll(permitEvidence(permit)); return List.copyOf(refs);
    }
    private static List<ExactRef> permitEvidence(Permit permit) {
        return List.of(permit.authorization(), permit.registry(), permit.verifierBundle(), permit.consumptionManifest(), permit.parentClaim());
    }
    private static byte[] input(String kind, Request request, Optional<Permit> permit, Optional<ExactRef> claim, Optional<ExactRef> original) {
        ObjectNode n = StrictJson.object().put("schema", INPUT_SCHEMA).put("kind", kind);
        if (request == null) n.putNull("request"); else n.set("request", OrdinaryOnceClaims.request(request));
        if (permit.isEmpty()) n.putNull("permit"); else n.set("permit", OrdinaryOnceClaims.permit(permit.orElseThrow()));
        if (claim.isEmpty()) n.putNull("claim_ref"); else n.set("claim_ref", claim.orElseThrow().toJson());
        if (original.isEmpty()) n.putNull("original_claim_manifest"); else n.set("original_claim_manifest", original.orElseThrow().toJson());
        return StrictJson.canonical(n, MAX_BYTES);
    }
}
