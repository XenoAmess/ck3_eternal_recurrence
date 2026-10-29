package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventReviewGrantPublisher;

/** Calls the original Python analyze_batch in its own process; neither implementation executes an interaction. */
final class OfflineInteractionOriginalProducerParityTest {
    private static final String ORIGINAL_SHA = "a96fbbb20836a237126560e0901690e39f534061e1754ccdfc69b0bea1bcddfc";
    @TempDir Path temporary;
    @Test void originalFullBatchProducerMatchesJavaSourceBodiesFingerprintPolicyAndPublishedEntry() throws Exception {
        String python = required("xar.python"); Path repository = Path.of(required("xar.repository.root"));
        assertTrue(repository.isAbsolute()); Path original = repository.resolve("ck3_autonomous_player/src/xar_autoplayer/interaction_offline_analysis.py");
        byte[] oldSource = Files.readAllBytes(original); assertTrue(oldSource.length <= (1 << 20)); assertEquals(ORIGINAL_SHA, OfflineInteractionCorpus.sha(oldSource));
        var f = new OfflineInteractionCorpus(temporary.resolve("actual-producers")); var ticket = f.journal.before(f.command).orElseThrow();
        // A controlled legacy after envelope tests historical custody only; it grants no native/material completion.
        ObjectNode after = StrictJson.object().put("schema", "xar.pending-interaction-left-reply/v1").put("incident_id", ticket.incidentId());
        after.set("before", ticket.before().toJson()); after.put("material_effects_verified", false);
        Path afterPath = f.incidents.resolve(ticket.incidentId() + ".after.json"); Files.write(afterPath, StrictJson.canonical(after));
        var afterPin = OfflineInteractionCorpus.pin(afterPath);
        ObjectNode manifest = StrictJson.object().put("completed_control_sequence", 17); var item = manifest.putArray("new_incidents").addObject();
        item.put("incident_id", ticket.incidentId()).put("kind", "pending_character_interaction").put("before", ticket.before().path()).put("before_sha256", ticket.before().sha256())
                .put("after", afterPin.path()).put("after_sha256", afterPin.sha256()).put("interaction_definition_key", "request_clerical_chastity_interaction");
        Path legacy = f.incidents.resolve("original-completed-batch.json"); Files.write(legacy, StrictJson.canonical(manifest));
        var batch = new BatchRequest("legacy-original-parity", OfflineInteractionCorpus.pin(legacy), List.of(ticket.before(), afterPin));
        ObjectNode actual = OfflineEventAnalysisWire.parseMetadataObject(f.host(false).batch(batch));
        Path output = temporary.resolve("original-python-output"), state = temporary.resolve("original-python-state");
        String program = "import json,sys;from pathlib import Path;sys.path.insert(0,str(Path(sys.argv[1])/'ck3_autonomous_player'/'src'));"
                + "from xar_autoplayer.interaction_offline_analysis import analyze_batch;"
                + "r=analyze_batch(Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]),publish_state_dir=Path(sys.argv[5]));"
                + "print(json.dumps({'reviewed':len(r['entries']),'unresolved':len(r['unresolved'])},sort_keys=True))";
        Path stdout = temporary.resolve("original.stdout"), stderr = temporary.resolve("original.stderr");
        Process process = new ProcessBuilder(python, "-I", "-B", "-c", program, repository.toString(), legacy.toString(), f.game.toString(), output.toString(), state.toString())
                .redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();
        boolean exited = process.waitFor(60, TimeUnit.SECONDS);
        if (!exited) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); }
        assertTrue(exited, "original producer timeout; NOT EXECUTED successfully"); assertTrue(Files.size(stdout) <= (1 << 20)); assertTrue(Files.size(stderr) <= (1 << 20));
        assertEquals(0, process.exitValue(), Files.readString(stderr, StandardCharsets.UTF_8));
        var summary = StrictJson.parse(Files.readAllBytes(stdout)); assertEquals(1, summary.path("reviewed").intValue()); assertEquals(0, summary.path("unresolved").intValue());
        assertArrayEquals(oldSource, Files.readAllBytes(original), "original producer source changed during execution");
        var row = actual.path("report").path("entries").get(0); String fingerprint = row.path("fingerprint").textValue();
        Path actualFacts = Path.of(row.path("canonical_source_facts").path("path").textValue());
        byte[] expectedFacts = Files.readAllBytes(output.resolve(fingerprint + ".source-facts.json"));
        assertArrayEquals(expectedFacts, Files.readAllBytes(actualFacts), "all original source scopes, conditional effects, categories and path bindings must match");
        InteractionRegistry.Entry expected = InteractionRegistryCodec.parseEntry(Files.readAllBytes(output.resolve(fingerprint + ".registry-entry.json")));
        InteractionRegistry.Entry produced = InteractionRegistryCodec.parseEntry(Files.readAllBytes(Path.of(row.path("published").path("path").textValue())));
        var projected = new InteractionRegistry.Entry(expected.fingerprint(), expected.binding(), expected.classification(), expected.preferredAction(), expected.paths(),
                new InteractionRegistry.SourceRef(actualFacts.toString(), OfflineInteractionCorpus.sha(expectedFacts)), expected.reason());
        assertEquals(projected, produced); assertEquals(17, actual.path("report").path("completed_control_sequence").intValue());
        assertEquals(0, OfflineEventReviewGrantPublisher.publish(new OfflineEventReviewGrantPublisher.Configuration(f.sources, f.incidents, f.knowledge, f.grants),
                Path.of(actual.path("report_ref").path("path").textValue())).added());
        assertFalse(actual.path("report").has("scan_observation")); assertTrue(OfflineEventAnalysisWire.parseMetadataObject(f.host(false).batch(batch)).path("idempotent").booleanValue());
    }
    @Test void legacyInteractionWithoutItsOriginalAfterCannotBeReinterpretedAsObservedScan() throws Exception {
        var f = new OfflineInteractionCorpus(temporary.resolve("legacy-incomplete")); var ticket = f.journal.before(f.command).orElseThrow();
        ObjectNode manifest = StrictJson.object().put("completed_control_sequence", 1); var item = manifest.putArray("new_incidents").addObject();
        item.put("incident_id", ticket.incidentId()).put("kind", "pending_character_interaction").put("before", ticket.before().path()).put("before_sha256", ticket.before().sha256());
        item.putNull("after"); item.putNull("after_sha256"); Path path = f.incidents.resolve("legacy.json"); Files.write(path, StrictJson.canonical(manifest));
        var batch = new BatchRequest("legacy-incomplete", OfflineInteractionCorpus.pin(path), List.of(ticket.before()));
        assertThrows(IllegalArgumentException.class, () -> f.host(false).batch(batch)); assertFalse(Files.exists(f.knowledge));
    }
    private static String required(String name) { String value = System.getProperty(name); assertNotNull(value, "Missing required " + name + "; NOT EXECUTED"); assertFalse(value.isBlank()); return value; }
}
