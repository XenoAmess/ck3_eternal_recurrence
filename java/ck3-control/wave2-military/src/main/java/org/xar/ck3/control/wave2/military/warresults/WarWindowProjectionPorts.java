package org.xar.ck3.control.wave2.military.warresults;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaselineCodec;
import org.xar.ck3.control.wave2.military.wardeclaredoverview.WarDeclaredOverviewPolicy;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTermsCodec;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceCodec;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract;

/** Pure domain ports in the single existing host. None provides transport, submit or writer authority. */
public final class WarWindowProjectionPorts {
    private WarWindowProjectionPorts() { }
    private record Port<I, O>(ProjectionOperation operation, int inputMaximumBytes, int outputMaximumBytes,
            Function<byte[], I> decoder, Function<I, O> application, Function<O, byte[]> encoder) implements ProjectionPort<I, O> {
        public I decode(byte[] raw) { return decoder.apply(raw); }
        public O project(I input) { return application.apply(input); }
        public byte[] encode(O result) { return encoder.apply(result); }
    }
    public record OwnerInput(WarResultsSourceContract.OwnerReceipt receipt, String expectedRequestId) { }

    public record Operations(ProjectionOperation resultsPlan, ProjectionOperation overviewPlan, ProjectionOperation resultsPresence, ProjectionOperation overviewPresence, ProjectionOperation resultsQueryFrame, ProjectionOperation overviewQueryFrame, ProjectionOperation sourceNormalize, ProjectionOperation sourceOwner, ProjectionOperation baselineNormalize, ProjectionOperation termsNormalize) {
        public Operations {
            Objects.requireNonNull(resultsPlan);
            Objects.requireNonNull(overviewPlan);
            Objects.requireNonNull(resultsPresence);
            Objects.requireNonNull(overviewPresence);
            Objects.requireNonNull(resultsQueryFrame);
            Objects.requireNonNull(overviewQueryFrame);
            Objects.requireNonNull(sourceNormalize);
            Objects.requireNonNull(sourceOwner);
            Objects.requireNonNull(baselineNormalize);
            Objects.requireNonNull(termsNormalize);
            if (Set.of(resultsPlan, overviewPlan, resultsPresence, overviewPresence, resultsQueryFrame, overviewQueryFrame, sourceNormalize, sourceOwner, baselineNormalize, termsNormalize).size() != 10) { throw new IllegalArgumentException("ten distinct war projection operations required"); }
        }
    }
    public static List<RegisteredProjection> registrations(Operations operations) {
        Objects.requireNonNull(operations);
        List<RegisteredProjection> rows = new ArrayList<>();
        rows.add(RegisteredProjection.of(new Port<>(operations.resultsPlan(), 65_536, 65_536,
                WarResultsCodec::decode, WarResultsPolicy::plan, WarResultsCodec::encodePlan)));
        rows.add(RegisteredProjection.of(new Port<>(operations.overviewPlan(), 65_536, 65_536,
                WarDeclaredOverviewPolicy::decode, WarDeclaredOverviewPolicy::plan, WarDeclaredOverviewPolicy::encodePlan)));
        rows.add(RegisteredProjection.of(new Port<WarResultsPolicy.Request, WarResultsPolicy.WindowPresence>(
                operations.resultsPresence(), 65_536, 65_536, WarResultsCodec::decode,
                input -> presence(input, false), WarWindowProjectionPorts::encodePresence)));
        rows.add(RegisteredProjection.of(new Port<WarResultsPolicy.Request, WarResultsPolicy.WindowPresence>(
                operations.overviewPresence(), 65_536, 65_536, WarDeclaredOverviewPolicy::decode,
                input -> presence(input, true), WarWindowProjectionPorts::encodePresence)));
        rows.add(RegisteredProjection.of(new Port<WarResultsPolicy.Snapshot, WarResultsPolicy.QueryFrame>(
                operations.resultsQueryFrame(), 65_536, 65_536, raw -> decodeQueryFrame(raw, false),
                WarResultsPolicy::queryFrame,
                WarResultsCodec::encodeQueryFrame)));
        rows.add(RegisteredProjection.of(new Port<WarResultsPolicy.Snapshot, WarResultsPolicy.QueryFrame>(
                operations.overviewQueryFrame(), 65_536, 65_536, raw -> decodeQueryFrame(raw, true),
                WarDeclaredOverviewPolicy::queryFrame,
                WarDeclaredOverviewPolicy::encodeQueryFrame)));
        rows.add(RegisteredProjection.of(new Port<>(operations.sourceNormalize(),
                65_536, 65_536, WarResultsSourceCodec::validate, Function.identity(), WarResultsSourceCodec::encodeNormalized)));
        rows.add(RegisteredProjection.of(new Port<WarResultsSourceContract.OwnerReceipt, WarResultsSourceContract.OwnerReceipt>(
                operations.sourceOwner(), 65_536, 65_536,
                WarWindowProjectionPorts::decodeOwner, Function.identity(),
                WarResultsSourceCodec::encodeOwnerReceipt)));
        rows.add(RegisteredProjection.of(new Port<DeJureExitBaseline, DeJureExitBaseline>(
                operations.baselineNormalize(), 1_048_576, 1_048_576,
                WarWindowProjectionPorts::decodeBaseline, Function.identity(), DeJureExitBaselineCodec::encodeProjection)));
        rows.add(RegisteredProjection.of(new Port<WarExitTerms, WarExitTerms>(
                operations.termsNormalize(), 1_048_576, 1_048_576,
                WarWindowProjectionPorts::decodeTerms, Function.identity(), WarExitTermsCodec::encode)));
        return List.copyOf(rows);
    }
    private static WarResultsPolicy.WindowPresence presence(WarResultsPolicy.Request input, boolean overview) {
        return input.snapshot().flatMap(snapshot -> snapshot.observation().value()).map(value -> overview
                ? WarDeclaredOverviewPolicy.presence(value) : WarResultsPolicy.presence(value)).orElse(WarResultsPolicy.WindowPresence.UNKNOWN);
    }
    private static byte[] encodePresence(WarResultsPolicy.WindowPresence value) {
        return StrictJson.canonical(com.fasterxml.jackson.databind.node.TextNode.valueOf(value.name().toLowerCase(Locale.ROOT)));
    }
    private static WarResultsPolicy.Snapshot decodeQueryFrame(byte[] raw, boolean overview) {
        var input = overview ? WarDeclaredOverviewPolicy.decode(raw) : WarResultsCodec.decode(raw);
        return input.snapshot().orElseThrow(() -> new IllegalArgumentException("snapshot required"));
    }
    private static WarResultsSourceContract.OwnerReceipt decodeOwner(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "expected_request_id", "owner_receipt"));
        StrictJson.require("xar.ck3.war-results-owner-receipt-input/v1".equals(StrictJson.text(root.get("schema"))), "owner input schema");
        var input = new OwnerInput(WarResultsSourceCodec.decodeOwnerReceipt(StrictJson.canonical(root.get("owner_receipt"))),
                StrictJson.text(root.get("expected_request_id")));
        return WarResultsSourceContract.validateOwner(input.receipt(), input.expectedRequestId());
    }
    private static DeJureExitBaseline decodeBaseline(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw, 1_048_576), Set.of("schema", "observation", "expected_frame"));
        StrictJson.require("xar.ck3.dejure-baseline-input/v1".equals(StrictJson.text(root.get("schema"))), "baseline input schema");
        ObjectNode frame = StrictJson.object(root.get("expected_frame"), Set.of("war_id", "native_revision", "date_raw", "defender_id", "attacker_id", "target_title_ids"));
        List<Long> titles = new ArrayList<>(); StrictJson.require(frame.get("target_title_ids").isArray(), "target title JSON array required");
        for (JsonNode title : frame.get("target_title_ids")) { titles.add(StrictJson.integer(title, 1, Long.MAX_VALUE)); }
        var binding = new DeJureExitBaseline.Frame(StrictJson.integer(frame.get("war_id"), 1, Long.MAX_VALUE),
                StrictJson.integer(frame.get("native_revision"), 1, Long.MAX_VALUE), StrictJson.integer(frame.get("date_raw"), Long.MIN_VALUE, Long.MAX_VALUE),
                StrictJson.integer(frame.get("defender_id"), 1, Long.MAX_VALUE), StrictJson.integer(frame.get("attacker_id"), 1, Long.MAX_VALUE), titles);
        return DeJureExitBaselineCodec.decode(StrictJson.canonical(root.get("observation"), 1_048_576), binding);
    }
    private static WarExitTerms decodeTerms(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw, 1_048_576), Set.of("schema", "observation", "expected_war_id"));
        StrictJson.require("xar.ck3.war-exit-terms-input/v1".equals(StrictJson.text(root.get("schema"))), "exit terms input schema");
        byte[] observation = StrictJson.canonical(root.get("observation"), 1_048_576);
        return root.get("expected_war_id").isNull() ? WarExitTermsCodec.decode(observation)
                : WarExitTermsCodec.decode(observation, (int) StrictJson.integer(root.get("expected_war_id"), 1, Integer.MAX_VALUE));
    }
}
