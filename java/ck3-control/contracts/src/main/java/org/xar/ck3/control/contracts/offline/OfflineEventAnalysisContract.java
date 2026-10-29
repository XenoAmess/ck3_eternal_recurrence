package org.xar.ck3.control.contracts.offline;

import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Typed metadata for existing offline knowledge producers. Caller references never configure output roots. */
public final class OfflineEventAnalysisContract {
    public static final String CONTRACT = "xar.offline-event-analysis/v1";
    public static final int MAX_METADATA_BYTES = 2_097_152;
    public static final String CAPTURE_REQUEST_SCHEMA = "xar.offline-mandatory-capture-request/v1";
    public static final String REVIEW_REQUEST_SCHEMA = "xar.offline-mandatory-review-request/v1";
    public static final String BATCH_REQUEST_SCHEMA = "xar.offline-event-batch-request/v1";
    public static final String CAPTURE_RESULT_SCHEMA = "xar.offline-mandatory-capture-result/v1";
    public static final String REVIEW_RESULT_SCHEMA = "xar.offline-mandatory-review-result/v1";
    public static final String BATCH_RESULT_SCHEMA = "xar.offline-event-analysis-result/v1";
    public static final String ERROR_SCHEMA = "xar.offline-event-analysis-error/v1";
    private OfflineEventAnalysisContract() { }
    public enum ErrorCode {
        INVALID_REQUEST, SOURCE_CHANGED, OPERATION_UNAVAILABLE, PUBLICATION_FAILED;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT).replace('_', '-'); }
    }
    public enum ReviewStatus {
        UNRESOLVED("unresolved"), KNOWN_UI_RECOVERY_OBSERVED("known_ui_recovery_observed");
        private final String wire;
        ReviewStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static ReviewStatus fromWire(String wire) {
            for (ReviewStatus value : values()) { if (value.wire.equals(wire)) return value; }
            throw new IllegalArgumentException("unknown offline UI review status");
        }
    }
    public record CaptureRequest(String batchId, ExactRef launchRef) {
        public CaptureRequest { batchId = OfflineEventAnalysisContract.batchId(batchId); launchRef = absolute(launchRef); }
    }
    public record ReviewRequest(String batchId, List<ExactRef> sourceRefs) {
        public ReviewRequest { batchId = OfflineEventAnalysisContract.batchId(batchId); sourceRefs = references(sourceRefs, 4609); }
    }
    public record BatchRequest(String batchId, ExactRef manifestRef, List<ExactRef> capturedRefs) {
        public BatchRequest { batchId = OfflineEventAnalysisContract.batchId(batchId); manifestRef = absolute(manifestRef); capturedRefs = references(capturedRefs, 512); }
    }
    public record CaptureResult(String batchId, List<ExactRef> sourceRefs) {
        public CaptureResult { batchId = OfflineEventAnalysisContract.batchId(batchId); sourceRefs = references(sourceRefs, 4609); }
    }
    public record Review(String incidentId, ReviewStatus status, ExactRef review) {
        public Review {
            if (incidentId == null || !incidentId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}")) throw new IllegalArgumentException("bounded UI incident identifier required");
            Objects.requireNonNull(status); review = absolute(review);
        }
    }
    public record Publication(ExactRef reference, int grants, int added) {
        public Publication {
            reference = absolute(reference);
            if (grants < 0 || added < 0 || added > grants) throw new IllegalArgumentException("exact publication counts required");
        }
    }
    public record ReviewResult(String batchId, List<Review> reviews, Publication publication, List<ExactRef> sourceRefs) {
        public ReviewResult {
            batchId = OfflineEventAnalysisContract.batchId(batchId); reviews = List.copyOf(reviews); Objects.requireNonNull(publication); sourceRefs = references(sourceRefs, 4609);
            if (reviews.size() > 256 || reviews.stream().map(Review::incidentId).distinct().count() != reviews.size()) throw new IllegalArgumentException("bounded unique UI review results required");
        }
    }
    public record Error(Optional<String> batchId, ErrorCode code, String message) {
        public Error {
            Objects.requireNonNull(batchId); Objects.requireNonNull(code); StrictJson.text(message);
            batchId.ifPresent(OfflineEventAnalysisContract::batchId);
            if (message.length() > 512) throw new IllegalArgumentException("bounded offline public error required");
        }
    }
    public static String batchId(String value) {
        if (value == null || !value.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}")) throw new IllegalArgumentException("bounded offline batch identifier required");
        return value;
    }
    public static ExactRef absolute(ExactRef reference) {
        Objects.requireNonNull(reference);
        if (!Path.of(reference.path()).isAbsolute()) throw new IllegalArgumentException("absolute captured reference path required");
        return reference;
    }
    public static List<ExactRef> references(List<ExactRef> references, int maximum) {
        List<ExactRef> snapshot = List.copyOf(references);
        if (snapshot.size() > maximum) throw new IllegalArgumentException("bounded captured source inventory required");
        var paths = new HashSet<Path>();
        for (ExactRef reference : snapshot) {
            absolute(reference);
            if (!paths.add(Path.of(reference.path()).normalize())) throw new IllegalArgumentException("duplicate captured source path");
        }
        return snapshot;
    }
}
