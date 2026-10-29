package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Base64;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryReader;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineInteractionSourceAnalyzer;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Actual preserved stock and before bytes through the analyzer, facts codec and trusted reader. No native execution. */
final class OfflineRiteDeclineSourceKnowledgeTest {
    private static final String INPUT_SHA = "747afd27de03544e64aabe2df96ee23953693bec79447e6cda0b072df44ea5fc";
    @TempDir Path temporary;

    @Test void originalRiteNotificationSourceKnowledgeSurvivesFactsPublicationAndSourceDriftIsRejected() throws Exception {
        var f = new OfflineInteractionCorpus(temporary.resolve("rite-source"));
        byte[] packed;
        try (var resource = getClass().getResourceAsStream("/offlineinteraction/rite-decline-original-input.json.gz")) {
            assertNotNull(resource, "mandatory original rite notification input"); packed = resource.readNBytes(131_073);
        }
        assertTrue(packed.length <= 131_072); assertEquals(INPUT_SHA, OfflineInteractionCorpus.sha(packed));
        var input = StrictJson.parse(inflate(packed, 2_097_152), 2_097_152);
        assertEquals("xar.rite-decline-original-source-test-input/v1", input.path("schema").textValue());
        var source = input.path("source"); var capture = input.path("before");
        assertEquals("common/character_interactions/pam_interactions.txt", source.path("relative").textValue());
        byte[] sourceRaw = inflate(Base64.getDecoder().decode(source.path("gzip_base64").textValue()), 2_097_152);
        byte[] beforeRaw = inflate(Base64.getDecoder().decode(capture.path("gzip_base64").textValue()), 65_536);
        assertEquals(source.path("bytes").intValue(), sourceRaw.length); assertEquals(source.path("sha256").textValue(), OfflineInteractionCorpus.sha(sourceRaw));
        assertEquals(capture.path("bytes").intValue(), beforeRaw.length); assertEquals(capture.path("sha256").textValue(), OfflineInteractionCorpus.sha(beforeRaw));
        Path sourcePath = f.game.resolve(source.path("relative").textValue());
        Files.write(sourcePath, sourceRaw, StandardOpenOption.CREATE_NEW);
        var before = RetainedJson.object(RetainedJson.parse(beforeRaw));
        var actual = OfflineInteractionSourceAnalyzer.analyze(before, TrustedEventSourceContext.open(f.sources));
        var facts = actual.facts();
        assertTrue(facts.analysis().contains("requires recipient is_ai=yes"));
        assertTrue(facts.analysis().contains("pam_sway_to_rite_on_decline_effect"));
        assertTrue(facts.analysis().contains("\"runtime_helper_source_verified\":false"));
        assertTrue(facts.onDecline().contains("pam_sway_to_rite_on_decline_effect = yes"));
        assertFalse(Files.exists(f.game.resolve("common/scripted_effects/pam_effects.txt")), "the result must remain labelled retained static helper knowledge");
        byte[] factsRaw = InteractionRegistryCodec.encodeFacts(facts);
        assertEquals(facts, InteractionRegistryCodec.parseFacts(factsRaw));
        assertFalse(StrictJson.parse(factsRaw).path("material_effects_verified").booleanValue());

        Path registry = Files.createDirectories(f.state.resolve("evidence/interaction-source-registry"));
        Path factsPath = Files.createDirectories(registry.resolve("facts")).resolve(facts.fingerprint() + ".json");
        Files.write(factsPath, factsRaw, StandardOpenOption.CREATE_NEW);
        var entry = new InteractionRegistry.Entry(facts.fingerprint(), facts.binding(), InteractionRegistry.CLASSIFICATION, "reject", facts.paths(),
                new InteractionRegistry.SourceRef(factsPath.toString(), OfflineInteractionCorpus.sha(factsRaw)), OfflineInteractionSourceAnalyzer.REASON);
        Files.write(registry.resolve(facts.fingerprint() + ".json"), InteractionRegistryCodec.encodeEntry(entry), StandardOpenOption.CREATE_NEW);
        var lookup = new InteractionRegistry.Lookup(facts.binding().build(), facts.binding().definition(), facts.binding().guiSha256());
        var reader = new InteractionRegistryReader(OfflineInteractionCorpus.MACHINE);
        var known = assertInstanceOf(InteractionRegistry.Known.class, reader.load(TrustedEventSourceContext.open(f.sources), lookup));
        assertEquals(facts, known.review().facts()); assertFalse(known.review().materialEffectsVerified());
        assertFalse(known.review().nativeAiEquivalent()); assertFalse(known.review().replayAllowed());
        Files.writeString(sourcePath, "\n# source drift", StandardOpenOption.APPEND);
        var drift = assertInstanceOf(InteractionRegistry.Unknown.class, reader.load(TrustedEventSourceContext.open(f.sources), lookup));
        assertEquals(InteractionRegistry.UnknownReason.REJECTED_ENTRY, drift.reason());
        assertEquals(InteractionRegistry.Rejection.SOURCE_MISMATCH, drift.rejectedEntries().getFirst().reason());
    }

    private static byte[] inflate(byte[] packed, int maximum) throws Exception {
        try (var input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
            byte[] raw = input.readNBytes(maximum + 1); assertTrue(raw.length > 0 && raw.length <= maximum); return raw;
        }
    }
}
