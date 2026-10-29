package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Actual original stock bytes and synthetic frame inputs call the real journal; no Native/Game credit. */
final class OfflineInteractionCorpus {
    static final String MACHINE = "offline-interaction-fixture";
    static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    static final String SOURCE = "common/character_interactions/clerical_chastity_interaction.txt";
    static final ObjectMapper JSON = new ObjectMapper();
    final Path root, state, game, incidents, scans, knowledge, grants;
    final ObjectNode corpus;
    final EventSourceReadContext sources;
    final EpisodeIncidentJournal journal;
    final EpisodeIncidentJournal.Binding binding;
    final ActionCommand command;

    OfflineInteractionCorpus(Path root) throws Exception {
        this.root = root; state = Files.createDirectories(root.resolve("state")); game = Files.createDirectories(root.resolve("game"));
        incidents = Files.createDirectory(root.resolve("incidents")); scans = Files.createDirectory(root.resolve("scans"));
        knowledge = root.resolve("knowledge"); grants = state.resolve("evidence/shared-grants.json");
        try (var resource = OfflineInteractionCorpus.class.getResourceAsStream("/offlineinteraction/offline-stock-inputs.json.gz")) {
            assertNotNull(resource, "mandatory actual original stock fixture"); byte[] packed = resource.readNBytes(131073);
            assertTrue(packed.length <= 131072); assertEquals("5a6318535c9fc6448149b2e573f4246e1e9697fb9996eded77d86d90ba638918", sha(packed));
            try (var input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                byte[] raw = input.readNBytes(1_048_577); assertTrue(raw.length <= 1_048_576); corpus = (ObjectNode)StrictJson.parse(raw, 1_048_576);
            }
        }
        assertEquals("xar.offline-interaction-source-test-inputs/v1", corpus.path("schema").textValue()); assertEquals(7, corpus.path("files").size());
        for (JsonNode file : corpus.path("files")) {
            String relative = file.path("relative").textValue(); Path output = game.resolve(relative).normalize();
            assertFalse(Path.of(relative).isAbsolute()); assertTrue(output.startsWith(game)); byte[] raw;
            try (var input = new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(file.path("gzip_base64").textValue())))) {
                raw = input.readNBytes(2_097_153); assertTrue(raw.length <= 2_097_152);
            }
            assertEquals(file.path("bytes").longValue(), raw.length); assertEquals(file.path("sha256").textValue(), sha(raw));
            Files.createDirectories(output.getParent()); Files.write(output, raw);
        }
        sources = new EventSourceReadContext(MACHINE, state, game, () -> {
            // The actual server takes a fresh immutable grant snapshot for each projection.
            if (!Files.exists(grants)) return List.of();
            try { return ProjectionEvidenceCodec.decode(Files.readAllBytes(grants)); }
            catch (java.io.IOException failure) { throw new IllegalStateException("Actual fixture grant source unavailable", failure); }
        });
        ObjectNode original = (ObjectNode)corpus.path("known_before").path("binding");
        var identity = new ProposalLifecycle.ObservationIdentity(MACHINE, new GameGeneration(original.path("bridge_pid").longValue(),
                new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(integer(original, "actor_character_id"),
                        integer(original, "native_revision"), integer(original, "date_raw")), original.path("snapshot_id").textValue(),
                        integer(original, "revision"), original.path("episode_run_id").textValue()), 1);
        Path sourceFile = root.resolve("SYNTHETIC-NATIVE-SOURCE.json"); Files.writeString(sourceFile, "{\"scope\":\"synthetic-frame-original-producer-test\"}");
        var source = new G2Source(MACHINE, NOW.toString(), "1.20.0.4", pin(sourceFile)); binding = new EpisodeIncidentJournal.Binding(identity, source, "fixture-session");
        var configured = new EpisodeIncidentJournal.Configuration(incidents, scans, Clock.fixed(NOW, ZoneOffset.UTC), bytes -> {
            if (bytes < 0 || bytes > (1 << 20)) throw new java.io.IOException("finite source-only regression output cap");
        }, Optional.of(TrustedEventSourceContext.open(sources)));
        journal = EpisodeIncidentJournal.initialize(configured, binding);
        var arguments = OpportunityJson.object(OpportunityJson.parse(bytes(corpus.path("known_plan"))), "actual original native-left plan");
        command = new ActionCommand("offline-interaction-action", identity, source, binding.sessionId(), new OperationKey("reject-pending-character-interaction"), arguments,
                new ProposalLifecycle.ExpectedPostcondition(1, identity, source, "synthetic-observer/v1",
                        List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(60));
    }
    OfflineEventAnalysisHost host(boolean completion) {
        var settings = new OfflineEventAnalysisHost.Settings(true, false, Optional.of(grants), Optional.of(incidents), Optional.of(knowledge), Optional.of(scans));
        return new OfflineEventAnalysisHost(Optional.of(sources), settings, completion ? Optional.of(journal::acknowledge) : Optional.empty());
    }
    static ExactRef pin(Path path) throws Exception { byte[] raw = Files.readAllBytes(path); return new ExactRef(path.toString(), raw.length, sha(raw)); }
    static byte[] bytes(JsonNode value) throws Exception { return JSON.writeValueAsBytes(value); }
    static String sha(byte[] raw) { return InteractionRegistryCodec.digest(raw); }
    private static BigInteger integer(JsonNode row, String field) { JsonNode value = row.get(field); assertTrue(value.isIntegralNumber()); return value.bigIntegerValue(); }
}
