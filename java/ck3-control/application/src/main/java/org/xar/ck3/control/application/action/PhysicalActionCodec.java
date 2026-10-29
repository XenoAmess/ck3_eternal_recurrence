package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.*;

/** Sole v5 physical metadata codec. Historical Native pipe receipt schemas retain their original parser. */
public final class PhysicalActionCodec {
    private PhysicalActionCodec() { }
    public static void preserve(PhysicalActionState state, ActionPorts.OutcomeArchive archive) {
        if (state.request() instanceof PreparedAction.MmapRequest mmap) archive.preserveMaterial(new RawJson(mmap.value().encode()));
        else if (state.request() instanceof PreparedAction.WindowCaptureRequest window) archive.preserveFrontendWindowCaptureRequest(window.value());
        else throw new IllegalArgumentException("pipe originals retain their sole native archive codec");
        state.outcome().ifPresent(value -> { if (value instanceof PhysicalOutcome.MmapOutcome mmap) archive.preservePresentationOutcome(mmap.value());
            else if (value instanceof PhysicalOutcome.WindowCaptureOutcome window) archive.preserveFrontendWindowCaptureOutcome(window.value());
            else throw new IllegalArgumentException("pipe outcome cannot enter physical v5 state"); });
    }
    private static ExactRef preparedReference(PreparedAction request, ActionPorts.OutcomeArchive archive) {
        if (request instanceof PreparedAction.MmapRequest mmap) return archive.materialReferenceOf(new RawJson(mmap.value().encode()));
        if (request instanceof PreparedAction.WindowCaptureRequest window) return archive.frontendWindowCaptureRequestReferenceOf(window.value());
        throw new IllegalArgumentException("pipe metadata must retain the historical Native request codec");
    }
    public static List<ExactRef> references(PhysicalActionState state, ActionPorts.OutcomeArchive archive) {
        List<ExactRef> refs = new ArrayList<>(state.request().preparationEvidence()); refs.add(preparedReference(state.request(), archive));
        refs.add(state.guard().nativeEvidence()); refs.add(state.guard().capabilityEvidence()); refs.addAll(state.guard().supportingEvidence()); refs.addAll(state.evidence());
        state.outcome().ifPresent(value -> refs.add(value instanceof PhysicalOutcome.MmapOutcome mmap ? archive.presentationOutcomeReferenceOf(mmap.value())
                : archive.frontendWindowCaptureOutcomeReferenceOf(((PhysicalOutcome.WindowCaptureOutcome) value).value())));
        return refs.stream().distinct().toList();
    }
    public static ObjectNode encode(PhysicalActionState state, ActionPorts.OutcomeArchive archive) {
        ObjectNode row = StrictJson.object(); row.put("kind", "PHYSICAL_ACTION"); row.put("transport", state.request().transportKind().name());
        row.put("request_id", state.request().requestId()); row.set("prepared_ref", preparedReference(state.request(), archive).toJson());
        row.put("submitted_at", state.submittedAt().toString()); row.set("guard", ActionReceiptCodec.encodeGuard(state.guard())); row.put("phase", state.phase().name());
        row.set("outcome_ref", state.outcome().map(value -> (JsonNode) (value instanceof PhysicalOutcome.MmapOutcome mmap ? archive.presentationOutcomeReferenceOf(mmap.value())
                : archive.frontendWindowCaptureOutcomeReferenceOf(((PhysicalOutcome.WindowCaptureOutcome) value).value())).toJson()).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));
        var refs = row.putArray("evidence"); state.evidence().forEach(ref -> refs.add(ref.toJson())); row.put("diagnostic", state.diagnostic()); return row;
    }
    public static PhysicalActionState decode(JsonNode raw, ActionPorts.OutcomeArchive archive) {
        ObjectNode row = StrictJson.object(raw, Set.of("kind", "transport", "request_id", "prepared_ref", "submitted_at", "guard", "phase", "outcome_ref", "evidence", "diagnostic"));
        StrictJson.require(StrictJson.text(row.get("kind")).equals("PHYSICAL_ACTION"), "physical v5 state required");
        TransportKind kind = TransportKind.valueOf(StrictJson.text(row.get("transport"))); ExactRef ref = ExactRef.fromJson(row.get("prepared_ref")); PreparedAction prepared;
        if (kind == TransportKind.PRESENTATION_MMAP) prepared = new PreparedAction.MmapRequest(PresentationRequest.decode(archive.loadMaterial(ref).bytes()));
        else if (kind == TransportKind.WIN32_FRONTEND_CAPTURE) prepared = new PreparedAction.WindowCaptureRequest(archive.loadFrontendWindowCaptureRequest(ref));
        else throw new IllegalArgumentException("Native pipe state cannot be decoded through a presentation contract");
        StrictJson.require(prepared.requestId().equals(StrictJson.text(row.get("request_id"))), "physical prepared request ID changed");
        Optional<PhysicalOutcome> outcome = row.get("outcome_ref").isNull() ? Optional.empty() : Optional.of(kind == TransportKind.PRESENTATION_MMAP
                ? new PhysicalOutcome.MmapOutcome(archive.loadPresentationOutcome(ExactRef.fromJson(row.get("outcome_ref"))))
                : new PhysicalOutcome.WindowCaptureOutcome(archive.loadFrontendWindowCaptureOutcome(ExactRef.fromJson(row.get("outcome_ref")))));
        List<ExactRef> refs = new ArrayList<>(); StrictJson.require(row.get("evidence").isArray(), "physical evidence array required"); row.get("evidence").forEach(value -> refs.add(ExactRef.fromJson(value)));
        return new PhysicalActionState(prepared, Instant.parse(StrictJson.text(row.get("submitted_at"))), ActionReceiptCodec.decodeGuard(row.get("guard")),
                PhysicalActionState.Phase.valueOf(StrictJson.text(row.get("phase"))), outcome, refs, StrictJson.text(row.get("diagnostic")));
    }
    public static boolean sameAttempt(PhysicalActionState before, PhysicalActionState after) {
        return before.submittedAt().equals(after.submittedAt()) && before.guard().equals(after.guard()) && before.request().transportKind() == after.request().transportKind()
                && Arrays.equals(requestBytes(before.request()), requestBytes(after.request()));
    }
    public static byte[] requestBytes(PreparedAction request) {
        if (request instanceof PreparedAction.MmapRequest mmap) return mmap.value().encode();
        if (request instanceof PreparedAction.WindowCaptureRequest window) return window.value().encode();
        throw new IllegalArgumentException("Native request bytes require their original pipe codec");
    }
}
