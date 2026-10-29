package org.xar.ck3.control.g2.m2;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryReader;
import org.xar.ck3.control.wave2.events.unhandledevent.InteractionHostJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedEventConsumer;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedInteractionContinuation;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedPlanJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedPopulistReceipt;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventEvidenceJson;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback;

/** Shared G2 adapter to the original event domain. Evaluation reads sources and composes proposals only. */
public final class M2Research implements G2Domain {
    private final Optional<EventSourceReadContext> configured;
    public M2Research() { configured = Optional.empty(); }
    public M2Research(EventSourceReadContext configured) { this.configured = Optional.of(Objects.requireNonNull(configured)); }
    @Override public Milestone milestone() { return Milestone.M2; }

    @Override public G2Response evaluate(G2Request request) {
        Objects.requireNonNull(request); StrictJson.require(request.milestone() == Milestone.M2, "M2 request milestone required");
        configured.ifPresent(context -> {
            if (!context.machineId().equals(request.source().machineId())) throw new G2Exception(G2HttpError.Code.SOURCE_MISMATCH,
                    "M2 request source machine differs from its server context");
        });
        M2Payload.Input input = M2Payload.decode(request.payload());
        boolean sourceReading = switch (input.operation()) {
            case EVENT_PLAN_SOURCE_REVIEWED, EVENT_REGISTRY_LOOKUP, INTERACTION_PLAN, INTERACTION_BEFORE, INTERACTION_REGISTRY_LOOKUP -> true;
            default -> false;
        };
        if (sourceReading && !"1.20.0.4".equals(request.source().exactBuild())) throw new G2Exception(G2HttpError.Code.SOURCE_MISMATCH,
                "M2 source-reading request must bind the reviewed exact build");
        byte[] raw = input.input().bytes();
        byte[] result;
        try { result = switch (input.operation()) {
            case EVENT_PLAN_CANDIDATE -> UnhandledEventCodec.encode(UnhandledEventFallback.plan(UnhandledEventCodec.decodePlan(raw)));
            case EVENT_PLAN_SOURCE_REVIEWED -> reviewedEvent(raw);
            case EVENT_BEFORE -> UnhandledEventEvidenceJson.encodeBody(UnhandledEventEvidenceJson.before(UnhandledEventEvidenceJson.decodeBefore(raw)));
            case EVENT_AFTER -> UnhandledEventEvidenceJson.encodeBody(UnhandledEventEvidenceJson.after(UnhandledEventEvidenceJson.decodeAfter(raw)));
            case INTERACTION_PLAN -> SourceReviewedInteractionContinuation.encode(SourceReviewedInteractionContinuation.plan(
                    SourceReviewedInteractionContinuation.decode(raw), trusted(false)));
            case INTERACTION_BEFORE -> InteractionHostJson.encodeBefore(InteractionHostJson.before(InteractionHostJson.decodeBefore(raw), trusted(false)));
            case INTERACTION_AFTER -> interactionAfter(raw);
            case INTERACTION_REGISTRY_LOOKUP -> registryLookup(raw);
            case EVENT_REGISTRY_LOOKUP -> SourceReviewedEventConsumer.lookup(raw, trusted(true)).encode();
            case EVENT_SOURCE_REVIEWED_RECEIPT -> SourceReviewedPopulistReceipt.encodeResult(
                    SourceReviewedPopulistReceipt.verify(SourceReviewedPopulistReceipt.decode(raw)));
        }; } catch (TrustedEventSourceContext.UnavailableException unavailable) {
            throw new G2Exception(G2HttpError.Code.ENGINE_UNAVAILABLE, "configured M2 source evidence is unavailable");
        }
        ProjectionJson output = M2Payload.output(input.operation(), ProjectionJson.value(result, M2Payload.MAX_BYTES));
        return new G2Response(request.requestId(), Milestone.M2, request.source(), output);
    }
    private byte[] reviewedEvent(byte[] raw) {
        SourceReviewedPlanJson.Input input = SourceReviewedPlanJson.decode(raw);
        return SourceReviewedPlanJson.encode(SourceReviewedEventConsumer.continueWithExistingPlan(
                input.plan(), input.snapshot(), input.actionSteps(), trusted(true)));
    }
    private static byte[] interactionAfter(byte[] raw) {
        InteractionHostJson.ReceiptRequest request = InteractionHostJson.decodeReceipt(raw);
        StrictJson.require(request instanceof InteractionHostJson.AfterBodyInput, "M2 interaction_after requires the original after-body wrapper");
        return InteractionHostJson.encodeReceipt(InteractionHostJson.projectReceipt(request));
    }
    private byte[] registryLookup(byte[] raw) {
        InteractionRegistry.Lookup input = InteractionRegistryCodec.parseLookup(raw);
        TrustedEventSourceContext trusted = trusted(false); SourceReviewedInteractionContinuation.verifyGui(trusted);
        StrictJson.require(InteractionFallback.GUI_SHA256.equals(input.guiSha256()), "M2 interaction GUI assertion differs from actual source");
        return InteractionHostJson.encodeRegistry(new InteractionRegistryReader(trusted.machineId()).load(trusted, input));
    }
    private TrustedEventSourceContext trusted(boolean fullEventSources) {
        EventSourceReadContext context = configured.orElseThrow(() -> new G2Exception(G2HttpError.Code.ENGINE_UNAVAILABLE,
                "M2 source-reading operation requires server-owned source context"));
        return fullEventSources ? TrustedEventSourceContext.open(context) : TrustedEventSourceContext.openEvidence(context);
    }
}
