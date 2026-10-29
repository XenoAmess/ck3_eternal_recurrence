package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedSourceCopy12004.QuoteBinding;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.SupportedBuild;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.ReleaseOption;

/** Read-only normalized collection adapter; it delegates common custody/collection validation. */
public final class NegotiatedCollectionProjection12004 {
    private NegotiatedCollectionProjection12004() { }

    /** Public and native snapshot identities are deliberately distinct. */
    public record QueryBinding(FrameBinding nativeFrame, String queriedSnapshotId,
            BigInteger queriedPublicRevision, List<ReleaseOption> requestedOptions) {
        public QueryBinding {
            Objects.requireNonNull(nativeFrame, "nativeFrame");
            StrictJson.text(queriedSnapshotId);
            NegotiatedPreview12003.positiveUInt64(queriedPublicRevision);
            requestedOptions = List.copyOf(requestedOptions);
            NegotiatedPreview12003.releaseOptionMask(requestedOptions);
        }
        public int requestedMask() { return NegotiatedPreview12003.releaseOptionMask(requestedOptions); }
    }

    public record Observation(ReleaseCollectionProjection12003.Observation collection,
            QueryBinding query, List<NegotiatedPreview12003> negotiatedPreviews,
            Optional<NegotiatedSourceCopy12004> source, Optional<NegotiatedQuoteResult12004> quoteResult) {
        public Observation {
            Objects.requireNonNull(collection, "collection");
            Objects.requireNonNull(query, "query");
            negotiatedPreviews = List.copyOf(negotiatedPreviews);
            StrictJson.require(!negotiatedPreviews.isEmpty() && negotiatedPreviews.size() == collection.rows().size(),
                    "complete negotiated rows required");
            Objects.requireNonNull(source, "source");
            Objects.requireNonNull(quoteResult, "quoteResult");
        }
        public NegotiatedPreview12003 selectedPreview() { return negotiatedPreviews.get(collection.selectedOrdinal()); }
    }

    /**
     * Consumes the unchanged Python transport's normalized response, preserving its original SHA.
     * It never queries native state or infers a successful release from these inputs.
     */
    public static Observation decodeNormalizedResponse(byte[] original, SupportedBuild build, QueryBinding query) {
        Objects.requireNonNull(query, "query");
        var common = ReleaseCollectionProjection12003.decode(original, build, query.nativeFrame());
        StrictJson.require(!common.rows().isEmpty(), "negotiated selected row is absent");
        JsonNode envelope = StrictJson.parse(original, ReleaseCollectionProjection12003.MAX_BYTES);
        StrictJson.require(StrictJson.text(envelope.get("exact_ck3_build")).equals(build.version())
                && StrictJson.text(envelope.get("exe_sha256")).equalsIgnoreCase(build.executableSha256()),
                "normalized response differs from its exact supported build");
        StrictJson.require(StrictJson.text(envelope.get("queried_snapshot_id")).equals(query.queriedSnapshotId()),
                "normalized response differs from queried public snapshot");
        StrictJson.integer(envelope.get("queried_revision"), query.queriedPublicRevision(), query.queriedPublicRevision());
        StrictJson.integer(envelope.get("queried_native_revision"), query.nativeFrame().nativeRevision(), query.nativeFrame().nativeRevision());
        StrictJson.integer(envelope.get("queried_release_option_mask_bits"), query.requestedMask(), query.requestedMask());
        JsonNode keys = envelope.get("queried_release_option_keys");
        StrictJson.require(keys != null && keys.isArray() && keys.size() == query.requestedOptions().size(), "queried option keys differ");
        for (int index = 0; index < keys.size(); index++) {
            StrictJson.require(StrictJson.text(keys.get(index)).equals(query.requestedOptions().get(index).key()),
                    "queried option order differs from the actual request");
        }
        List<NegotiatedPreview12003> previews = new ArrayList<>();
        JsonNode rows = envelope.get("player_prisoner_collection").get("prisoners");
        for (int ordinal = 0; ordinal < common.rows().size(); ordinal++) {
            FrameBinding frame = new FrameBinding(query.nativeFrame().nativeRevision(), query.nativeFrame().dateRaw(),
                    query.nativeFrame().playerCharacterId(), common.rows().get(ordinal).prisonerCharacterId());
            var preview = NegotiatedPreviewCodec.decode(rows.get(ordinal).get("negotiated_release_preview"), frame, query.requestedMask());
            if (preview instanceof NegotiatedPreview12003.Available available) {
                StrictJson.require(available.proofEpoch().equals(common.proofEpoch()), "negotiated row proof differs from collection");
            }
            boolean notEvaluated = preview instanceof NegotiatedPreview12003.Unavailable unavailable
                    && unavailable.unavailableReason().equals("not_evaluated");
            StrictJson.require(notEvaluated != (ordinal == common.selectedOrdinal()), "negotiated evaluation belongs to another ordinal");
            previews.add(preview);
        }
        QuoteBinding binding = new QuoteBinding(query.nativeFrame(), common.querySequence(), common.proofEpoch(),
                common.selectedOrdinal(), query.requestedMask());
        Optional<NegotiatedSourceCopy12004> source = Optional.empty();
        if (envelope.has("prisoner_negotiated_quote_source_12004")) {
            StrictJson.require(build == SupportedBuild.CK3_12004, "selected source requires actual 1.20.0.4 build");
            source = Optional.of(NegotiatedSourceCodec12004.decode(envelope.get("prisoner_negotiated_quote_source_12004"), binding));
        }
        Optional<NegotiatedQuoteResult12004> result = Optional.empty();
        if (build == SupportedBuild.CK3_12004) {
            var consumed = NegotiatedQuoteResult12004.consume(previews.get(common.selectedOrdinal()), source, binding);
            JsonNode originalResult = envelope.get("prisoner_negotiated_quote_result_12004");
            StrictJson.require(originalResult != null && originalResult.equals(StrictJson.parse(NegotiatedQuoteResult12004.encode(consumed))),
                    "normalized response differs from the actual negotiated result consumer");
            result = Optional.of(consumed);
        } else {
            StrictJson.require(!envelope.has("prisoner_negotiated_quote_result_12004"), "actual4 result attached to another build");
        }
        return new Observation(common, query, previews, source, result);
    }
}
