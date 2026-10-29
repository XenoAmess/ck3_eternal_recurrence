package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** DATA-only producer/consumer regression. Placeholder historical refs grant no runtime or Game permission. */
class RootRuntimeDefinitionsPublicationRequestProducerTest {
    @TempDir Path root;
    private static final String SHA = "a".repeat(64);
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-01T00:00:00Z"), ZoneOffset.UTC);
    private record Fixture(RootRuntimeDefinitionsPublisher.Request request,
            RootRuntimeDefinitionsPublicationRequestProducer.Prepared prepared, Path target) { }

    private Fixture fixture() throws IOException {
        var request = new RootRuntimeDefinitionsPublisher.Request(RootRuntimeDefinitionsPublisher.SCHEMA,
                configuration(), pin(root.resolve("absent-definitions-binding.json")), root.resolve("definitions.json").toString());
        return new Fixture(request, RootRuntimeDefinitionsPublicationRequestProducer.prepare(request), root.resolve("publication-request.json"));
    }

    @Test void directDataProducerFeedsTheSoleTypedConsumerWithoutHistoricalInputs() throws Exception {
        var f = fixture(); byte[] bytes = f.prepared().bytes(); byte[] mutation = f.prepared().bytes(); mutation[0] ^= 1;
        assertArrayEquals(bytes, f.prepared().bytes());
        assertFalse(Files.exists(Path.of(f.request().outputBindingRef().path())));
        assertFalse(Files.exists(Path.of(f.request().configuration().nativeLaunchPlanRef().path())));
        var published = f.prepared().publish(f.target(), CLOCK);
        assertEquals(f.prepared().quote(f.target()).bytes(), published.original().bytes());
        assertEquals(published.original(), published.actualWitness().source());
        assertEquals(published.original().bytes(), published.actualWitness().nativeFile().logicalBytes());
        assertArrayEquals(bytes, Files.readAllBytes(f.target()));
        assertEquals(f.request(), published.readExact(CLOCK));
        assertEquals(f.request(), RootRuntimeDefinitionsPublisher.decodeRequest(Files.readAllBytes(f.target())));
        assertFalse(Files.exists(Path.of(f.request().target())), "publishing Request DATA does not execute Definitions");
    }

    @Test void compatibleEntrypointDoesNotOpenMissingOrMalformedCardsOrRenewHistoricalFreshness() throws Exception {
        var f = fixture(); Path malformed = root.resolve("malformed-request-card.json"); Files.writeString(malformed, "{}");
        var legacy = new FileRef(malformed.toString(), 1, SHA);
        var published = f.prepared().publish(legacy, f.target(), CLOCK);
        Files.delete(malformed);
        assertEquals(f.request(), published.readExact(Clock.fixed(Instant.parse("2040-01-01T00:00:00Z"), ZoneOffset.UTC)));
        assertEquals(f.request(), f.prepared().publish(pin(root.resolve("missing-request-card.json")),
                root.resolve("missing-card-request.json"), CLOCK).readExact(CLOCK));
    }

    @Test void exactRequestCannotBeOverwrittenOrImplicitlyReplayed() throws Exception {
        var f = fixture(); var published = f.prepared().publish(f.target(), CLOCK); byte[] before = Files.readAllBytes(f.target());
        assertThrows(IOException.class, () -> f.prepared().publish(f.target(), CLOCK));
        assertThrows(IOException.class, () -> f.prepared().publish(pin(root.resolve("missing-card.json")), f.target(), CLOCK));
        assertArrayEquals(before, Files.readAllBytes(f.target())); assertEquals(f.request(), published.readExact(CLOCK));
    }

    @Test void explicitTargetCannotAliasDefinitionsOrPassiveHistoricalData() throws Exception {
        var f = fixture();
        for (Path target : List.of(Path.of(f.request().target()), Path.of(f.request().outputBindingRef().path()))) {
            assertThrows(IOException.class, () -> f.prepared().publish(target, CLOCK)); assertFalse(Files.exists(target));
        }
        assertThrows(IllegalArgumentException.class, () -> f.prepared().publish(Path.of("relative.json"), CLOCK));
        Path unnormalized = root.resolve("absent").resolve("..").resolve("unnormalized.json");
        assertThrows(IllegalArgumentException.class, () -> f.prepared().publish(unnormalized, CLOCK));
        assertFalse(Files.exists(f.target()));
    }

    @Test void realProducedWireRejectsMissingWrongTypedUnknownDuplicateAndOldFields() throws Exception {
        var f = fixture(); var published = f.prepared().publish(f.target(), CLOCK);
        var mapper = ControlBuild.strictMapper(); byte[] bytes = Files.readAllBytes(f.target());
        ObjectNode missing = (ObjectNode) mapper.readTree(bytes); missing.remove("configuration");
        assertThrows(IOException.class, () -> RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(missing)));
        ObjectNode nil = (ObjectNode) mapper.readTree(bytes); nil.putNull("configuration");
        assertThrows(IOException.class, () -> RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(nil)));
        ObjectNode bool = (ObjectNode) mapper.readTree(bytes); ((ObjectNode) bool.get("output_binding_ref")).put("bytes", true);
        assertThrows(IOException.class, () -> RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(bool)));
        ObjectNode fraction = (ObjectNode) mapper.readTree(bytes); ((ObjectNode) fraction.get("output_binding_ref")).put("bytes", 1.0);
        assertThrows(IOException.class, () -> RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(fraction)));
        ObjectNode extra = (ObjectNode) mapper.readTree(bytes); extra.put("existing_definitions_template", "not-an-input");
        assertThrows(IOException.class, () -> RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(extra)));
        ObjectNode old = (ObjectNode) mapper.readTree(bytes); old.put("schema", "xar.java-root-runtime-definitions-publication/v0");
        assertThrows(IOException.class, () -> RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(old)));
        byte[] duplicate = ("{\"schema\":\"duplicate\"," + new String(bytes, java.nio.charset.StandardCharsets.UTF_8).substring(1))
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> RootRuntimeDefinitionsPublisher.decodeRequest(duplicate));
        assertEquals(f.request(), published.readExact(CLOCK));
    }

    @Test void requestContentMutationIsRejectedByTheActualDataReader() throws Exception {
        var f = fixture(); var published = f.prepared().publish(f.target(), CLOCK); byte[] original = Files.readAllBytes(f.target());
        byte[] bytes = original.clone();
        bytes[0] ^= 1; Files.write(f.target(), bytes);
        assertThrows(IOException.class, () -> published.readExact(CLOCK));
        var mapper = ControlBuild.strictMapper(); ObjectNode reordered = (ObjectNode) mapper.readTree(original);
        var schema = reordered.remove("schema"); reordered.set("schema", schema);
        byte[] sameValue = mapper.writeValueAsBytes(reordered);
        assertFalse(Arrays.equals(original, sameValue)); assertEquals(original.length, sameValue.length);
        assertEquals(f.request(), RootRuntimeDefinitionsPublisher.decodeRequest(sameValue));
        Files.write(f.target(), sameValue);
        assertThrows(IOException.class, () -> published.readExact(CLOCK), "same typed value does not replace the recorded DATA bytes");
    }

    @Test void identicalDataBytesRemainReadableAfterFileReplacement() throws Exception {
        var f = fixture(); var published = f.prepared().publish(f.target(), CLOCK);
        Path replacement = root.resolve("same-bytes-replacement.json"); Files.copy(f.target(), replacement);
        Files.move(replacement, f.target(), StandardCopyOption.REPLACE_EXISTING);
        assertEquals(f.request(), published.readExact(CLOCK));
    }

    /** Existing Definitions codec fixture structure: complete typed configuration, no physical source claim. */
    private Configuration configuration() {
        FileRef input = pin(root.resolve("missing-required.json")); Build build = new Build("1.20.0.4", SHA);
        List<SourcePin> sources = Arrays.stream(SourceRole.values()).map(role -> {
            SourceKind kind = expectedKind(role); String suffix = switch (kind) {
                case JAVA -> ".java"; case NATIVE -> ".cpp"; case ORIGINAL_PYTHON -> ".py"; case STOCK_SCRIPT -> ".txt";
            };
            String target = role == SourceRole.ARMY_WAR_EXIT_TRUCE_DEFINITION ? ARMY_WAR_EXIT_TRUCE_TARGET
                    : "local-service/src/main/java/fixture/" + role.name() + suffix;
            return new SourcePin(role, kind, new SelectedSource(target, new ExactRef(root.resolve(role.name() + suffix).toString(), 1, SHA)));
        }).toList();
        SelectedSource java = sources.stream().filter(source -> source.kind() == SourceKind.JAVA).findFirst().orElseThrow().selected();
        SelectedSource episode = sources.stream().filter(source -> source.role() == SourceRole.PRISONER_EPISODE_LEDGER).findFirst().orElseThrow().selected();
        List<ProducerClosure> closures = Arrays.stream(ClosureRole.values()).map(role -> new ProducerClosure(role,
                role == ClosureRole.PRISONER_DOMAIN ? List.of(java, episode) : List.of(java))).toList();
        List<DataPin> data = Arrays.stream(DataRole.values()).map(role -> new DataPin(role, input)).toList();
        ReadPermission permission = new ReadPermission(null, "fixture-permission", PermissionMode.SOURCE_QUALIFIED_PRIVATE, WireProfile.EXECUTE_STEP);
        List<FinanceRead> finance = Arrays.stream(FinanceQuery.values()).map(query -> new FinanceRead(query, java, permission)).toList();
        var activity = new ActivityInputs(Arrays.stream(ActivityNativeContracts.Query.values()).map(query -> new ActivityQuery(query, java)).toList(),
                Arrays.stream(ActivityActionRoutes.Kind.values()).map(kind -> new ActivityMutation(kind, java)).toList());
        return new Configuration(SCHEMA, "definition-fixture-machine", "2026-10-24T00:00:00Z", "2026-10-24T01:00:00Z",
                input, input, input, input, new SourceIndex(input, 1, SHA), sources, closures, data,
                new GovInputs(build, "fixture-governance", List.copyOf(GovernanceActionPreparation.OPERATIONS), 10, 3),
                new FinanceInputs(finance, java, permission), new ArmyInputs(1000, 2000, "fixture-army"),
                new PrisonerInputs(build, "fixture-prisoners"), new FamilyInputs(true, true, true, true, null),
                new FrontendInputs(build, 1000, 1000, 8, 32, "fixture-frontend"),
                new InteractionInputs(build, List.of(0L), List.of(List.of(0)), List.of(0)), activity,
                new CrossRunInputs(new OriginalHistory(root.resolve("strategy/one-life-history.json").toString(), null)),
                new IncidentInputs(root.resolve("incidents").toString(), root.resolve("scans").toString(), 65536),
                new PublicInputs(1000, 2000, List.of(PublicMethod.values()[0])), new StartupInputs(16, 1000, "fixture-startup"));
    }
    private FileRef pin(Path path) { return new FileRef(path.toString(), 1, SHA); }
}
