package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual framed software Native input -> Driver join -> shared public codec -> GUI context DATA. */
final class DriverPublicContextTest {
    private static final BigInteger WIDE = new BigInteger("18446744073709551615");

    private static DriverObservationAssembler.Complete complete(String state) {
        var actual = DriverObservationAssemblerTest.actual(state);
        var facts = DriverObservationAssemblerTest.facts(actual);
        return assertInstanceOf(DriverObservationAssembler.Complete.class,
                new DriverObservationAssembler().assemble(actual, facts,
                        DriverStateAssemblerTest.ref(actual.originalPacket())));
    }

    private static DriverObservationAssembler.Complete changed(DriverObservationAssembler.Complete original,
            OpportunityJson.Obj semantic, String binding) {
        return new DriverObservationAssembler.Complete(original.identity(), original.source(), original.sessionId(),
                original.connectionGeneration(), semantic, original.originalEvidence(), original.observedAt(), binding);
    }

    @Test void actualCompleteKeepsFullHistoryWideDiagnosticRolesAndDecimalTokens() {
        String state = DriverObservationAssemblerTest.STATE.replace("\"original\":\"retained\"",
                "\"original\":\"retained\",\"connection_generation\":5,"
                + "\"last_heartbeat\":{\"sequence\":" + WIDE + ",\"monotonic_ms\":" + WIDE + "},"
                + "\"rejected_state_snapshot_count\":" + WIDE + ","
                + "\"snapshot_publish_diagnostic_count\":" + WIDE + ",\"original_metric\":-0.00");
        var frame = complete(state);
        var context = DriverPublicContext.from(frame);
        var diagnostics = DriverJson.object(context.diagnostics().bytes(), RawJson.MAXIMUM_BYTES);
        assertEquals(new OpportunityJson.Text("5"), diagnostics.get("connection_generation"));
        assertEquals(new OpportunityJson.Text(WIDE.toString()), diagnostics.get("rejected_state_snapshot_count"));
        var heartbeat = OpportunityJson.object(diagnostics.get("last_heartbeat"), "last_heartbeat");
        assertEquals(new OpportunityJson.Text(WIDE.toString()), heartbeat.get("sequence"));
        assertEquals(new OpportunityJson.Text(WIDE.toString()), heartbeat.get("monotonic_ms"));
        assertEquals(new OpportunityJson.DecimalValue("-0.00"), diagnostics.get("original_metric"));
        assertEquals(frame.semantic(), PublicSnapshotCodec.decode(context.snapshot()));
        assertEquals(2, OpportunityJson.array(PublicSnapshotCodec.decode(context.snapshot())
                .get("native_command_history"), "native_command_history").size());
        assertEquals(diagnostics, DriverJson.object(context.snapshot().bytes(), RawJson.MAXIMUM_BYTES).get("diagnostics"));
    }

    @Test void archivedDriverDiagnosticMaterialKeepsOpaqueDecimalBeyondNativeTokenBound() {
        var actual = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);
        var originalKnown = DriverStateAssemblerTest.known();
        String token = "0." + "0".repeat(5000) + "1";
        var diagnosticFields = new LinkedHashMap<>(OpportunityJson.object(
                DriverObservationAssembler.originalNativeState(actual).get("diagnostics"), "diagnostics").members());
        diagnosticFields.put("opaque_original_metric", new OpportunityJson.DecimalValue(token));
        var extra = new OpportunityJson.Obj(java.util.Map.of("diagnostics", new OpportunityJson.Obj(diagnosticFields)));
        var known = new DriverSnapshotFacts.Known(originalKnown.driver(), originalKnown.stamp(),
                originalKnown.originalHistoryBasis(), originalKnown.actionRows(), extra,
                originalKnown.loop(), java.util.Optional.empty());
        var driverReference = DriverStateAssemblerTest.ref(known.driver().encode());
        var manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.valueOf(2), 1,
                DriverStateAssemblerTest.source(), extra, driverReference);
        var manifestReference = DriverStateAssemblerTest.ref(manifest.bytes());
        var restored = DriverObservationEvidenceReader.nativeFrame(manifestReference, manifest, actual.originalPacket());
        var facts = DriverObservationEvidenceReader.decode(manifestReference, manifest,
                RawJson.fullMaterial(known.driver().encode()), restored);
        var frame = assertInstanceOf(DriverObservationAssembler.Complete.class, new DriverObservationAssembler()
                .assemble(restored, facts, DriverStateAssemblerTest.ref(actual.originalPacket())));
        var context = DriverPublicContext.from(frame);
        assertEquals(new OpportunityJson.DecimalValue(token), DriverJson.object(context.diagnostics().bytes(),
                RawJson.MAXIMUM_BYTES).get("opaque_original_metric"));
        assertEquals(frame.semantic(), PublicSnapshotCodec.decode(context.snapshot()));
        assertThrows(IllegalArgumentException.class, () -> new RawJson(context.diagnostics().bytes()),
                "complete diagnostic material must not broaden the Native protocol token lane");
        assertThrows(IllegalArgumentException.class, context.diagnostics()::requireProtocolBound);
    }

    @Test void absentNullWrongTypedOrCrossedDiagnosticsCannotBecomeContext() {
        var original = complete(DriverObservationAssemblerTest.STATE);
        for (OpportunityJson.Value invalid : List.of(OpportunityJson.Nil.INSTANCE,
                new OpportunityJson.Bool(false), new OpportunityJson.Arr(List.of()))) {
            var fields = new LinkedHashMap<>(original.semantic().members());
            fields.put("diagnostics", invalid);
            var semantic = new OpportunityJson.Obj(fields);
            assertThrows(IllegalArgumentException.class, () -> DriverPublicContext.from(
                    changed(original, semantic, DriverObservationAssembler.bindingSha256(semantic))));
        }
        var fields = new LinkedHashMap<>(original.semantic().members());
        fields.remove("diagnostics");
        var absent = new OpportunityJson.Obj(fields);
        assertThrows(IllegalArgumentException.class, () -> DriverPublicContext.from(
                changed(original, absent, DriverObservationAssembler.bindingSha256(absent))));
        var actual = DriverPublicContext.from(original);
        assertThrows(IllegalArgumentException.class, () -> new DriverPublicContext.Context(actual.snapshot(),
                new RawJson(DriverStateAssemblerTest.bytes("{\"different\":true}"))));
    }

    @Test void crossedFrameIdentityBindingAndWrongWideTypesAreRejected() {
        var original = complete(DriverObservationAssemblerTest.STATE);
        var fields = new LinkedHashMap<>(original.semantic().members());
        fields.put("snapshot_id", new OpportunityJson.Text("different-snapshot"));
        var semantic = new OpportunityJson.Obj(fields);
        assertThrows(IllegalArgumentException.class, () -> DriverPublicContext.from(
                changed(original, semantic, DriverObservationAssembler.bindingSha256(semantic))));
        assertThrows(IllegalArgumentException.class, () -> DriverPublicContext.from(
                changed(original, original.semantic(), "0".repeat(64))));
        for (String token : List.of("true", "5.0", "-1", "18446744073709551616")) {
            String state = DriverObservationAssemblerTest.STATE.replace("\"original\":\"retained\"",
                    "\"original\":\"retained\",\"last_heartbeat\":{\"sequence\":" + token + "}");
            assertThrows(IllegalArgumentException.class, () -> DriverPublicContext.from(complete(state)));
        }
    }
}
