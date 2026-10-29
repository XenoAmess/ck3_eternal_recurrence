package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/**
 * New assertion adapter for the existing actual Host/NEXT acceptance entry.
 * "Published" means the current Root's real Driver/history initialization, not
 * the occurrence of a public RETURNED invocation. Those issuers are lazy.
 * This adapter uses the retained publisher, journal, Native/Driver archive and
 * production initialization replay. It never initializes, flushes, queries,
 * installs an issuer or turns recorded UNKNOWN into a settled action.
 */
public final class RootArmyReturnedHistoryInitializationAssertions {
    private RootArmyReturnedHistoryInitializationAssertions() { }

    public static void requirePublished(RootApplicationAssembly.Core core,
            RootInstalledCatalog catalog, ContinuityStorePort.Session same) throws IOException {
        assertNotNull(core); assertNotNull(catalog); assertNotNull(same);
        core.writer().requireSession(same);
        var head = same.head();
        var context = catalog.context();
        var current = core.sessionAccess().current();
        assertSame(core, context.core()); assertSame(core.writer(), context.writer());
        assertSame(core.archive(), context.archive()); assertSame(current, context.actions());
        assertTrue(current.ownedBy(core)); assertFalse(current.isRetired());
        assertTrue(current.hasInstalledHost(), "actual NEXT Host must already be published");
        assertSame(current.driver(), context.adopted());
        assertSame(catalog.bindings(), context.bindings());
        catalog.additionalDomains().requireContext(context);

        var publisher = catalog.readHistory();
        var authority = context.adopted().authority();
        assertSame(publisher, context.readHistoryPublisher());
        assertSame(publisher, current.capabilityRuntime().readHistoryPublisher());
        current.capabilityRuntime().requireOwner(authority, core.archive(), catalog.bindings());
        publisher.requireOwner(authority, core.archive(), context.readCatalog());
        assertSame(context.readCatalog(), publisher.catalog());
        // This is the actual pre-registered writer route, not a lookalike publisher.
        core.readHistoryAuthority().requireCurrent(same, publisher);
        var persistence = publisher.statusSnapshot();
        var original = authority.withFrozenFacts(same, frozen -> {
            if (!(frozen.state() instanceof DriverSnapshotFacts.Known known))
                throw new IOException("MISSING_ACTUAL_INITIALIZED_HISTORY: published NEXT has no actual Known Driver");
            assertEquals(head.digest(), frozen.actions().headSha256());
            assertEquals(head.state().sequence(), frozen.actions().ledgerSequence());
            var basis = assertInstanceOf(ActionJournal.BoundHistoryBasis.class, frozen.actions().originalHistory(),
                    "the canonical journal must retain the actual complete Driver-history basis");
            assertEquals(known.originalHistoryBasis(), basis.originalDriverHistory());
            verifyPin(same, basis.originalDriverHistory());
            assertEquals(current.identity().game(), known.stamp().game());

            var observation = known.observation().orElseThrow(() ->
                    new IOException("MISSING_ACTUAL_INITIALIZED_HISTORY: no original Native/complete-Driver manifest"));
            var nativeFrame = DriverObservationEvidenceReader.reference(
                    known.auxiliary().get("capability_observed_native_source"));
            var originals = core.archive().withSession(same);
            var full = core.frameLoader().loadFull(new NativeEffectEvidence.FrameBasis(
                    nativeFrame, observation.semanticFactsEvidence()), originals);
            assertEquals(observation, full.facts());
            assertArrayEquals(known.driver().encode(), full.facts().driver().encode());
            assertEquals(current.identity().machineId(), full.actual().session().machineId());
            assertEquals(current.identity().game(), full.actual().session().game());
            assertEquals(current.identity().sessionId(), full.actual().session().sessionId());
            assertEquals(context.adopted().session().connectionGeneration(),
                    full.actual().session().connectionGeneration());
            assertEquals(context.source(), full.facts().source());
            var frame = assertInstanceOf(DriverObservationAssembler.Complete.class,
                    core.observationAssembler().assemble(full.actual(), full.facts(), full.originalEvidence()),
                    "the sole production assembler must rebuild the genuine published ordinary frame");
            assertEquals(context.source(), frame.source());
            assertEquals(current.identity().sessionId(), frame.sessionId());
            assertEquals(known, DriverSnapshotFacts.decodeKnownOriginal(
                    DriverSnapshotFacts.encodeKnownOriginal(known), Optional.of(full.facts())));

            // The real initializer's archived capsule includes its policy, Native,
            // query sources and persistent planning state. Missing inputs fail here.
            if (!known.auxiliary().members().containsKey(DriverCapabilityStateProducer.STATE_SOURCE))
                throw new IOException("MISSING_ACTUAL_INITIALIZED_HISTORY: no actual capability initialization source");
            var stateSource = DriverObservationEvidenceReader.reference(
                    known.auxiliary().get(DriverCapabilityStateProducer.STATE_SOURCE));
            assertEquals(known.auxiliary(), DriverCapabilityStateProducer.replay(frame, known, stateSource, originals),
                    "published initialization must replay from its complete actual archived input chain");

            for (var covered : known.actionRows()) {
                var matches = frozen.actions().actions().stream()
                        .filter(action -> action.command().actionId().equals(covered.actionId())).toList();
                assertEquals(1, matches.size(), "actual covered action must occur once in the canonical journal");
                var action = matches.getFirst();
                assertEquals(covered.bodySha256(), action.bodySha256());
                assertTrue(covered.durableSequence() <= action.sequence());
                if (covered.coverageSource() instanceof DriverSnapshotFacts.LegacyHistoryRow legacy) {
                    var entry = known.driver().commandHistory().get(Math.toIntExact(legacy.historyIndex() - 1));
                    var row = DriverJson.object(entry.originalRow().json(), DriverJson.MAX_NATIVE_BYTES);
                    if (row.members().containsKey(DriverActionHistoryCodec.SOURCE_FIELD))
                        assertEquals(covered.durableSequence(), action.sequence());
                    var pin = same.capturePin(legacy.originalRow(), WriterContracts.MAX_PIN_BYTES);
                    same.verifyPin(pin);
                    assertArrayEquals(entry.originalRow().json(), same.readPinned(pin, WriterContracts.MAX_PIN_BYTES));
                    same.verifyPin(pin);
                } else if (covered.coverageSource() instanceof DriverSnapshotFacts.CanonicalOnly canonical) {
                    assertEquals(covered.durableSequence(), action.sequence());
                    verifyPin(same, canonical.originalSource());
                }
            }
            for (var entry : known.driver().commandHistory()) {
                var row = DriverJson.object(entry.originalRow().json(), DriverJson.MAX_NATIVE_BYTES);
                if (row.members().containsKey(DriverArmySummaryHistoryRowProducer.SOURCE_FIELD)) {
                    var decoded = DriverArmySummaryHistoryRowProducer.decode(entry.originalRow().json());
                    var replayed = DriverArmySummaryHistoryRowProducer.replayOriginals(originals, context.readCatalog(), decoded);
                    assertArrayEquals(entry.originalRow().json(), replayed.encode());
                }
            }
            return known;
        });
        authority.withFrozenFacts(same, frozen -> {
            assertSame(original, frozen.state(), "the assertion must not replace the actual Known/cache/history");
            return null;
        });
        core.readHistoryAuthority().requireCurrent(same, publisher);
        assertEquals(persistence, publisher.statusSnapshot());
        core.writer().requireSession(same);
        var after = same.head();
        assertEquals(head.digest(), after.digest()); assertEquals(head.documents(), after.documents());
        assertEquals(head.state().sequence(), after.state().sequence());
    }

    private static void verifyPin(ContinuityStorePort.Session same, ExactRef reference) throws IOException {
        same.verifyPin(same.capturePin(reference, WriterContracts.MAX_PIN_BYTES));
    }
}
