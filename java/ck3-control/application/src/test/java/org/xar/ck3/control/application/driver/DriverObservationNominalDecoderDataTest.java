package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Public DATA boundaries for the explicit nominal Reader overload.
 * Pure software DATA: no Session, owner binding, Root, native I/O or active cache.
 * Reuses the existing application tests' original-wire fixtures in this package.
 */
final class DriverObservationNominalDecoderDataTest {
    @Test void nominalAndStrictFallbackRoutesRetainFullMaterialAndOriginalMetadata() {
        String opaque = "7".repeat(4301);
        byte[] wire = DriverStateAssemblerTest.bytes(DriverStateAssemblerTest.WIRE.replace(
                "\"campaign_id\":\"campaign-original\"",
                "\"campaign_id\":\"campaign-original\",\"opaque_counter\":" + opaque));
        var known = DriverFactsRepository.imported(DriverStateAssemblerTest.ref(wire), wire, 3, 7,
                DriverStateAssemblerTest.game(), new OpportunityJson.Obj(Map.of()));
        byte[] fullBytes = known.driver().encode();
        var fullDriver = RawJson.fullMaterial(fullBytes);
        assertThrows(IllegalArgumentException.class, () -> new RawJson(fullBytes));

        var actual = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE.replace(
                "\"speed\":3", "\"speed\":3,\"original_metric\":1.00"));
        var extras = new OpportunityJson.Obj(Map.of("retained_semantic_marker",
                new OpportunityJson.Text("retained-from-manifest")));
        var manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.valueOf(2), 1,
                DriverStateAssemblerTest.source(), extras, DriverStateAssemblerTest.ref(fullBytes));
        var manifestRef = DriverStateAssemblerTest.ref(manifest.bytes());
        byte[] manifestBytes = manifest.bytes();
        var replay = DriverObservationEvidenceReader.nativeFrame(manifestRef, manifest, actual.originalPacket());
        var nativeRef = DriverStateAssemblerTest.ref(replay.originalPacket());
        assertArrayEquals(actual.state().bytes(), replay.state().bytes());

        // The pre-existing entry has no archive capability argument.
        assertRetained(DriverObservationEvidenceReader.decode(manifestRef, manifest, fullDriver, replay),
                fullBytes, opaque, manifestRef, nativeRef, extras, replay);

        var defaultEvents = new ArrayList<String>();
        var legacyLoaderEvents = new ArrayList<String>();
        var inactiveLoaderEvents = new ArrayList<String>();
        var legacyLoader = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        var inactiveLoader = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        OutcomeArchive[] routes = {
                null,
                getterOnly(null, defaultEvents),
                getterOnly(() -> legacyLoader, legacyLoaderEvents),
                getterOnly(() -> inactiveLoader, inactiveLoaderEvents)
        };
        for (var route : routes) {
            assertRetained(DriverObservationEvidenceReader.decode(manifestRef, manifest, fullDriver, replay, route),
                    fullBytes, opaque, manifestRef, nativeRef, extras, replay);
        }
        assertEquals(List.of("getter"), defaultEvents);
        assertEquals(List.of("getter"), legacyLoaderEvents);
        assertEquals(List.of("getter"), inactiveLoaderEvents);
        assertArrayEquals(fullBytes, fullDriver.bytes());
        assertArrayEquals(manifestBytes, manifest.bytes());
    }

    @Test void originalIntegrityPrecedesGetterWhileNominalSelectionPrecedesStrictDecodeAndBinding() {
        var known = DriverStateAssemblerTest.known();
        var actual = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);
        var fullDriver = RawJson.fullMaterial(known.driver().encode());
        var manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.valueOf(2), 1,
                DriverStateAssemblerTest.source(), new OpportunityJson.Obj(Map.of()),
                DriverStateAssemblerTest.ref(fullDriver.bytes()));
        var manifestRef = DriverStateAssemblerTest.ref(manifest.bytes());
        var events = new ArrayList<String>();
        var sentinel = new IllegalStateException("software nominal getter sentinel");
        var throwingGetter = getterOnly(() -> { throw sentinel; }, events);

        assertThrows(NullPointerException.class,
                () -> DriverObservationEvidenceReader.decode(null, null, null, null, throwingGetter));
        assertThrows(NullPointerException.class,
                () -> DriverObservationEvidenceReader.decode(null, null, fullDriver, null, throwingGetter));
        assertThrows(NullPointerException.class,
                () -> DriverObservationEvidenceReader.decode(null, null, fullDriver, actual, throwingGetter));
        assertThrows(NullPointerException.class,
                () -> DriverObservationEvidenceReader.decode(null, manifest, fullDriver, actual, throwingGetter));

        assertEquals("semantic facts manifest exact bytes/SHA differ",
                assertThrows(ContractViolationException.class, () -> DriverObservationEvidenceReader.decode(
                        differentDigest(manifestRef), manifest, fullDriver, actual, throwingGetter)).getMessage());
        var unknownField = changedManifest(manifest, "unexpected", new OpportunityJson.Bool(true));
        assertEquals("exact semantic evidence manifest contract required",
                assertThrows(ContractViolationException.class, () -> DriverObservationEvidenceReader.decode(
                        DriverStateAssemblerTest.ref(unknownField.bytes()), unknownField, fullDriver,
                        actual, throwingGetter)).getMessage());
        var malformedRef = changedManifest(manifest, "driver_ref", new OpportunityJson.Bool(false));
        assertEquals("exact reference must be an object",
                assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.decode(
                        DriverStateAssemblerTest.ref(malformedRef.bytes()), malformedRef, fullDriver,
                        actual, throwingGetter)).getMessage());
        var changedDriver = RawJson.fullMaterial(DriverStateAssemblerTest.bytes(new String(
                fullDriver.bytes(), java.nio.charset.StandardCharsets.UTF_8)
                .replace("campaign-original", "changed-campaign")));
        assertEquals("archived complete Driver exact bytes/SHA differ",
                assertThrows(ContractViolationException.class, () -> DriverObservationEvidenceReader.decode(
                        manifestRef, manifest, changedDriver, actual, throwingGetter)).getMessage());
        assertTrue(events.isEmpty(), "invalid originals must fail before the capability getter");

        // Both originals are now exact, but the full Driver has an invalid format version.
        var malformedDriver = RawJson.fullMaterial(DriverStateAssemblerTest.bytes(
                DriverStateAssemblerTest.WIRE.replace("\"format_version\":2", "\"format_version\":1")));
        var malformedDriverManifest = changedManifest(manifest, "driver_ref",
                DriverObservationEvidenceReader.reference(DriverStateAssemblerTest.ref(malformedDriver.bytes())));
        var malformedDriverManifestRef = DriverStateAssemblerTest.ref(malformedDriverManifest.bytes());
        assertSame(sentinel, assertThrows(IllegalStateException.class, () -> DriverObservationEvidenceReader.decode(
                malformedDriverManifestRef, malformedDriverManifest, malformedDriver, actual, throwingGetter)));
        assertEquals(List.of("getter"), events);

        var fallbackEvents = new ArrayList<String>();
        var finalStrictLoader = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        var inactiveCapability = getterOnly(() -> finalStrictLoader, fallbackEvents);
        assertEquals("integer outside contract range",
                assertThrows(ContractViolationException.class, () -> DriverObservationEvidenceReader.decode(
                        malformedDriverManifestRef, malformedDriverManifest, malformedDriver,
                        actual, inactiveCapability)).getMessage());
        assertEquals(List.of("getter"), fallbackEvents);
        assertEquals("integer outside contract range",
                assertThrows(ContractViolationException.class, () -> DriverObservationEvidenceReader.decode(
                        malformedDriverManifestRef, malformedDriverManifest, malformedDriver, actual)).getMessage());


        // Earlier native binding wins over a separately malformed later source object.
        var wrongBinding = changedManifest(changedManifest(manifest, "snapshot_id",
                new OpportunityJson.Text("other-snapshot")), "source", new OpportunityJson.Bool(false));
        var wrongBindingRef = DriverStateAssemblerTest.ref(wrongBinding.bytes());
        events.clear();
        assertSame(sentinel, assertThrows(IllegalStateException.class, () -> DriverObservationEvidenceReader.decode(
                wrongBindingRef, wrongBinding, fullDriver, actual, throwingGetter)));
        assertEquals(List.of("getter"), events);
        assertEquals("archived semantic facts crossed actual native packet/session",
                assertThrows(ContractViolationException.class, () -> DriverObservationEvidenceReader.decode(
                        wrongBindingRef, wrongBinding, fullDriver, actual, inactiveCapability)).getMessage());
        var badSource = changedManifest(manifest, "source", new OpportunityJson.Bool(false));
        assertEquals("source must be an object",
                assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.decode(
                        DriverStateAssemblerTest.ref(badSource.bytes()), badSource, fullDriver,
                        actual, inactiveCapability)).getMessage());
    }

    private static void assertRetained(DriverObservationFacts facts, byte[] fullBytes, String opaque,
            ExactRef manifestRef, ExactRef nativeRef, OpportunityJson.Obj extras,
            org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame actual) {
        assertArrayEquals(fullBytes, facts.driver().encode());
        assertEquals(3, facts.driverVersion());
        assertEquals(7, facts.episodeEpoch());
        assertEquals(2, facts.driver().commandHistory().size());
        assertEquals(1, facts.driver().commandHistory().get(0).index());
        assertEquals(2, facts.driver().commandHistory().get(1).index());
        assertInstanceOf(DriverStateSnapshot.NullValue.class, facts.driver().lastCheckpoint());
        assertInstanceOf(DriverStateSnapshot.NullValue.class, facts.driver().successionExpectation());
        var first = DriverJson.object(facts.driver().commandHistory().get(0).originalRow().json(),
                DriverJson.MAX_NATIVE_BYTES);
        assertEquals(new OpportunityJson.DecimalValue("1.0"),
                OpportunityJson.object(first.get("result"), "result").get("scale"));
        var campaign = DriverJson.object(assertInstanceOf(DriverStateSnapshot.Value.class,
                facts.driver().campaignGoal()).json(), DriverJson.MAX_NATIVE_BYTES);
        assertEquals("campaign-original", OpportunityJson.text(campaign.get("campaign_id"), "campaign_id"));
        assertEquals(new BigInteger(opaque), OpportunityJson.integer(campaign.get("opaque_counter"), "opaque_counter"));
        assertEquals("held-session", facts.transport().sessionId());
        assertEquals(BigInteger.valueOf(5), facts.transport().connectionGeneration());
        assertEquals(DriverStateAssemblerTest.game(), facts.transport().game());
        assertEquals(new BigInteger("9007199254740993"), facts.transport().game().creationFiletime().value());
        assertEquals("snapshot-9", facts.snapshotId());
        assertEquals(BigInteger.valueOf(9), facts.nativeRevision());
        assertEquals(BigInteger.valueOf(2), facts.publicRevision());
        assertEquals(1, facts.observationVersion());
        assertEquals(DriverStateAssemblerTest.source(), facts.source());
        assertEquals(extras, facts.originalSemanticFields());
        assertEquals(manifestRef, facts.semanticFactsEvidence());
        assertEquals(DriverJson.sha256(actual.state().bytes()), facts.nativeStateSha256());

        var joined = assertInstanceOf(DriverObservationAssembler.Complete.class,
                new DriverObservationAssembler().assemble(actual, facts, nativeRef));
        assertEquals(DriverStateAssemblerTest.identity(), joined.identity());
        assertEquals(nativeRef, joined.originalEvidence());
        assertEquals(actual.observedAt(), joined.observedAt());
        assertEquals(new OpportunityJson.DecimalValue("1.00"), joined.semantic().get("original_metric"));
        assertEquals(new OpportunityJson.Text("retained-from-manifest"),
                joined.semantic().get("retained_semantic_marker"));
        assertEquals(2, OpportunityJson.array(joined.semantic().get("native_command_history"), "history").size());
        assertEquals(manifestRef,
                DriverObservationEvidenceReader.reference(joined.semantic().get("java_driver_facts_evidence")));
    }

    /** A DATA-only getter probe. It exposes no material, Native, receipt, owner or Session operation. */
    private static OutcomeArchive getterOnly(Supplier<DriverFrameEvidenceLoader> supplied, List<String> events) {
        return (OutcomeArchive) Proxy.newProxyInstance(OutcomeArchive.class.getClassLoader(),
                new Class<?>[] {OutcomeArchive.class}, (proxy, method, arguments) -> {
                    if (method.getName().equals("scopedDriverDecoder") && method.getParameterCount() == 0) {
                        events.add("getter");
                        return supplied == null ? InvocationHandler.invokeDefault(proxy, method) : supplied.get();
                    }
                    throw new AssertionError("Reader must not call archive operation: " + method.getName());
                });
    }

    /** Test input mutation through the existing public typed codec; no duplicate schema predicate. */
    private static RawJson changedManifest(RawJson original, String field, OpportunityJson.Value replacement) {
        return RawJson.fullMaterial(DriverJson.encode(DriverJson.object(original.bytes(), DriverJson.MAX_NATIVE_BYTES)
                .with(field, replacement)));
    }

    private static ExactRef differentDigest(ExactRef original) {
        String changed = (original.sha256().charAt(0) == '0' ? "1" : "0") + original.sha256().substring(1);
        return new ExactRef(original.path(), original.bytes(), changed);
    }
}