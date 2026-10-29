package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original derived-child evidence locator. Decoding this value grants no submission or domain authority. */
public record ArmyDerivedAdmissionEvidence(long actualHeadSequence, String actualHeadDigest, String childBodySha256, String parentBodySha256,
        ExactRef parentReceipt, ExactRef currentDomain, ExactRef previewBody, List<ExactRef> preflightReads,
        ExactRef beforeNative, ExactRef beforeDriver) {
    public static final String SCHEMA = "xar.army-retreat-derived-child/v1";
    private static final Set<String> FIELDS = Set.of("schema", "actual_head_sequence", "actual_head_digest", "child_body_sha256", "parent_body_sha256", "parent_receipt", "current_domain", "preview_body", "preflight_reads", "before_native", "before_driver");
    public ArmyDerivedAdmissionEvidence {
        StrictJson.require(actualHeadSequence >= 0,"canonical writer head sequence required"); digest(actualHeadDigest); digest(childBodySha256); digest(parentBodySha256); Objects.requireNonNull(parentReceipt); Objects.requireNonNull(currentDomain); Objects.requireNonNull(previewBody); Objects.requireNonNull(beforeNative); Objects.requireNonNull(beforeDriver);
        preflightReads = List.copyOf(preflightReads); StrictJson.require(preflightReads.size() == 2 && !preflightReads.getFirst().equals(preflightReads.getLast()), "two distinct original retreat preflight receipts required");
    }
    public RawJson encode() {
        var n = StrictJson.object().put("schema", SCHEMA).put("actual_head_sequence",actualHeadSequence).put("actual_head_digest", actualHeadDigest).put("child_body_sha256", childBodySha256).put("parent_body_sha256", parentBodySha256);
        n.set("parent_receipt", parentReceipt.toJson()); n.set("current_domain", currentDomain.toJson()); n.set("preview_body", previewBody.toJson());
        var reads = n.putArray("preflight_reads"); preflightReads.forEach(ref -> reads.add(ref.toJson())); n.set("before_native", beforeNative.toJson()); n.set("before_driver", beforeDriver.toJson()); return new RawJson(StrictJson.canonical(n));
    }
    public static ArmyDerivedAdmissionEvidence decode(RawJson value) {
        var n = StrictJson.object(StrictJson.parse(value.bytes()), FIELDS); StrictJson.require(StrictJson.text(n.get("schema")).equals(SCHEMA), "exact derived retreat evidence schema required");
        StrictJson.require(n.get("preflight_reads").isArray(), "original preflight receipt list required"); List<ExactRef> reads = new ArrayList<>(); n.get("preflight_reads").forEach(ref -> reads.add(ExactRef.fromJson(ref)));
        var sequence = n.get("actual_head_sequence"); StrictJson.require(sequence.isIntegralNumber() && sequence.canConvertToLong() && sequence.longValue() >= 0,"exact writer sequence required");
        return new ArmyDerivedAdmissionEvidence(sequence.longValue(),StrictJson.text(n.get("actual_head_digest")), StrictJson.text(n.get("child_body_sha256")), StrictJson.text(n.get("parent_body_sha256")),
                ExactRef.fromJson(n.get("parent_receipt")), ExactRef.fromJson(n.get("current_domain")), ExactRef.fromJson(n.get("preview_body")), reads, ExactRef.fromJson(n.get("before_native")), ExactRef.fromJson(n.get("before_driver")));
    }
    public List<ExactRef> references() { List<ExactRef> all = new ArrayList<>(List.of(parentReceipt, currentDomain, previewBody, beforeNative, beforeDriver)); all.addAll(preflightReads); return all.stream().distinct().toList(); }
    /** Packet/source binding only. The Native verifier must also replay canonical ancestry, claims and both full reads. */
    public static ArmyDerivedAdmissionEvidence requireGuard(GuardEvidence guard, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(guard.supportingEvidence().size() == 2, "derived guard must retain its original Root basis and exact Army proof");
        ExactRef proof = guard.supportingEvidence().get(1); RawJson raw = archive.loadMaterial(proof); exact(proof, raw.bytes()); var value = decode(raw);
        StrictJson.require(value.beforeNative().equals(guard.nativeEvidence()), "derived guard changed its actual original before packet"); exact(value.beforeNative(), archive.loadNativeFrame(value.beforeNative()));
        exact(value.beforeDriver(), archive.loadMaterial(value.beforeDriver()).bytes());
        var parent = archive.loadReceipt(value.parentReceipt()); StrictJson.require(parent.bodySha256().equals(value.parentBodySha256())
                && parent.state() instanceof ActionState.CompositeRunning running && running.execution().children().size() == 1
                && running.execution().children().getFirst().bodySha256().equals(value.childBodySha256())
                && parent.command().source().equals(guard.source()) && parent.command().sessionId().equals(guard.sessionId())
                && parent.command().before().machineId().equals(guard.observed().machineId()) && parent.command().before().game().equals(guard.observed().game()), "derived guard original parent locator/source changed");
        StrictJson.require(archive.receiptReferenceOf(parent).equals(value.parentReceipt()), "derived guard original parent receipt bytes changed");
        for (ExactRef ref : value.preflightReads()) { var read = archive.loadRead(ref); StrictJson.require(ref.equals(archive.readReferenceOf(read)), "derived guard original query identity changed"); }
        exact(value.currentDomain(), archive.loadMaterial(value.currentDomain()).bytes()); exact(value.previewBody(), archive.loadMaterial(value.previewBody()).bytes()); return value;
    }
    private static void exact(ExactRef ref, byte[] actual) { StrictJson.require(ref.bytes() == actual.length && ref.sha256().equals(ActionCodec.sha256(actual)), "derived evidence original bytes changed"); }
    private static void digest(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "canonical original SHA256 digest required"); }
}
