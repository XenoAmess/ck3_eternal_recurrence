package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;

/** Actual catalog/family metadata boundary only; no native, source qualification, origin or permission is invented. */
final class PublicPlanningStepMetadataTest {
    private static final ExactRef PRODUCER = new ExactRef("D:/planning-metadata-fixture/producer.java", 1, "a".repeat(64));
    private static final ExactRef DECODER = new ExactRef("D:/planning-metadata-fixture/decoder.java", 1, "b".repeat(64));
    private static final ExactRef VERIFIER = new ExactRef("D:/planning-metadata-fixture/verifier.java", 1, "c".repeat(64));
    private static final Set<String> TERMINAL = Set.of("death-terminal", "start-next-episode", "continue-as-reconciled-successor");
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static RootExecutableBindings.ActionBinding action(OperationKey operation) {
        var effect = new NativeEffectRegistry.Binding(operation, PRODUCER,
                command -> { throw new AssertionError("metadata must not prepare an action"); },
                (command, attempt, outcome) -> { throw new AssertionError("metadata must not observe an action"); });
        return new RootExecutableBindings.ActionBinding(effect, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("game.command.metadata-action"), DECODER);
    }
    private static NativeRecordedEvidenceVerifier.Binding archived(OperationKey operation) {
        return new NativeRecordedEvidenceVerifier.Binding(operation, VERIFIER,
                (head, receipt, archive) -> { throw new AssertionError("metadata must not run a domain verifier"); });
    }
    private static CompositeActionPort terminalHandler() {
        return new CompositeActionPort() {
            @Override public String handlerId() { return "planning-metadata-terminal"; }
            @Override public boolean supports(OperationKey operation) { return TERMINAL.contains(operation.value()); }
            @Override public void validate(ActionCommand parent) { throw new AssertionError("metadata must not validate an action"); }
            @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) { throw new AssertionError("metadata must not run a composite"); }
            @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution execution) { throw new AssertionError("metadata must not observe a composite"); }
        };
    }
    private static RootExecutableBindings.CompositeBinding terminalBinding() {
        return new RootExecutableBindings.CompositeBinding(terminalHandler(), ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,
                Optional.empty(), PRODUCER, DECODER);
    }
    private static RootExecutableBindings.Family<Long> family(String id, AtomicInteger factories) {
        return new RootExecutableBindings.Family<>(id, Long.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("game.command.metadata-action"), PRODUCER, DECODER, VERIFIER,
                value -> raw("{\"id\":" + value + "}"), value -> new OperationKey("metadata-action-" + value),
                value -> {
                    factories.incrementAndGet(); var operation = new OperationKey("metadata-action-" + value);
                    return new RootExecutableBindings.IssuedAction(action(operation), archived(operation));
                }, operation -> operation.value().equals("metadata-action-7") ? Optional.of(7L) : Optional.empty());
    }

    @Test void fixedActionAndThreeActualTerminalCompositesDescribeOnlyTheirInstalledSources() {
        var operation = new OperationKey("metadata-fixed-action"); var binding = terminalBinding();
        var verifiers = new java.util.ArrayList<NativeRecordedEvidenceVerifier.Binding>(); verifiers.add(archived(operation));
        TERMINAL.stream().map(OperationKey::new).map(PublicPlanningStepMetadataTest::archived).forEach(verifiers::add);
        var catalog = RootExecutableBindings.freeze(List.of(action(operation)), RootReadContractCatalog.staticOnly(List.of()),
                List.of(binding), verifiers, List.of(), 4);
        var beforeActions = catalog.actionBindings(); var beforeArchive = catalog.archivedBindings();
        var description = catalog.describeForPublicPlanning(operation).orElseThrow();
        assertEquals(ExecutableStepBindings.Kind.ACTION, description.descriptor().kind());
        assertEquals(PRODUCER, description.descriptor().implementationSource()); assertEquals(DECODER, description.descriptor().decoderSource());
        assertEquals(Optional.of(VERIFIER), description.archivedVerifierSource());
        assertEquals(description.descriptor().nativeIdentity(), NativeStepDiscriminator.fromJson(NativeStepDiscriminator.toJson(description.descriptor().nativeIdentity())));
        for (String role : TERMINAL) {
            var terminal = catalog.describeForPublicPlanning(new OperationKey(role)).orElseThrow();
            assertEquals(ExecutableStepBindings.Kind.COMPOSITE, terminal.descriptor().kind());
            assertEquals(ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION, terminal.descriptor().guardMode());
            assertEquals(PRODUCER, terminal.descriptor().implementationSource()); assertEquals(Optional.of(VERIFIER), terminal.archivedVerifierSource());
        }
        assertTrue(catalog.describeForPublicPlanning(new OperationKey("restore-checkpoint")).isEmpty());
        assertEquals(beforeActions, catalog.actionBindings()); assertEquals(beforeArchive, catalog.archivedBindings());
        var missingVerifier = RootExecutableBindings.freeze(List.of(action(operation)), RootReadContractCatalog.staticOnly(List.of()), List.of(binding), 4);
        assertTrue(missingVerifier.describeForPublicPlanning(operation).isEmpty());
        assertTrue(missingVerifier.describeForPublicPlanning(new OperationKey("death-terminal")).isEmpty());
    }

    @Test void actionFamilyGrammarDescribesBeforeAnyIssueAndOrdinaryIssueStillOwnsMembership() {
        var calls = new AtomicInteger(); var family = family("actual-installed-family", calls); var operation = new OperationKey("metadata-action-7");
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(), List.of(), List.of(family), 4);
        var first = catalog.describeForPublicPlanning(operation).orElseThrow();
        assertEquals(PRODUCER, first.descriptor().implementationSource()); assertEquals(DECODER, first.descriptor().decoderSource());
        assertEquals(Optional.of(VERIFIER), first.archivedVerifierSource());
        assertEquals(first, catalog.describeForPublicPlanning(operation).orElseThrow());
        assertTrue(catalog.actionBindings().isEmpty()); assertTrue(catalog.archivedBindings().isEmpty());
        assertTrue(catalog.actualFamily(operation).isEmpty()); assertEquals(0, calls.get());
        assertTrue(catalog.describeForPublicPlanning(new OperationKey("metadata-action-8")).isEmpty());
        catalog.issue(family, 7L);
        assertEquals(1, calls.get()); assertEquals(1, catalog.actionBindings().size()); assertEquals(1, catalog.archivedBindings().size());
        assertEquals(first, catalog.describeForPublicPlanning(operation).orElseThrow());
        assertTrue(catalog.resolve(operation, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).isPresent()); assertEquals(1, calls.get());
    }

    @Test void compositeFamilyGrammarDescribesThreeRolesWithoutProducingReplayMembership() {
        var calls = new AtomicInteger(); var binding = terminalBinding();
        var family = new RootExecutableBindings.CompositeFamily<>("installed-terminal-family", String.class, binding, VERIFIER,
                value -> raw("{\"role\":\"" + value + "\"}"), OperationKey::new,
                value -> { calls.incrementAndGet(); return archived(new OperationKey(value)); },
                operation -> TERMINAL.contains(operation.value()) ? Optional.of(operation.value()) : Optional.empty());
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(binding),
                List.of(), List.of(), List.of(family), 4);
        for (String role : TERMINAL) {
            var operation = new OperationKey(role); var metadata = catalog.describeForPublicPlanning(operation).orElseThrow();
            assertEquals(ExecutableStepBindings.Kind.COMPOSITE, metadata.descriptor().kind());
            assertEquals(Optional.of(VERIFIER), metadata.archivedVerifierSource()); assertTrue(catalog.actualCompositeFamily(operation).isEmpty());
        }
        assertTrue(catalog.archivedBindings().isEmpty()); assertEquals(0, calls.get());
        catalog.issueComposite(family, "death-terminal");
        assertEquals(1, calls.get()); assertEquals(1, catalog.archivedBindings().size());
        assertTrue(catalog.describeForPublicPlanning(new OperationKey("death-terminal")).isPresent()); assertEquals(1, calls.get());
    }

    @Test void conflictingAndMalformedPureGrammarsRejectWithoutAnyFactoryInvocation() {
        var calls = new AtomicInteger(); var first = family("first", calls); var second = family("second", calls);
        var conflict = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(), List.of(), List.of(first, second), 4);
        assertThrows(IllegalArgumentException.class, () -> conflict.describeForPublicPlanning(new OperationKey("metadata-action-7")));
        assertTrue(conflict.actionBindings().isEmpty()); assertTrue(conflict.archivedBindings().isEmpty()); assertEquals(0, calls.get());
        var malformed = new RootExecutableBindings.Family<>("malformed", Long.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.empty(), PRODUCER, DECODER, VERIFIER, value -> raw("{}"), value -> new OperationKey("another-operation"),
                value -> { throw new AssertionError("malformed decoder must not issue"); }, operation -> Optional.of(7L));
        var invalid = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(), List.of(), List.of(malformed), 4);
        assertThrows(IllegalArgumentException.class, () -> invalid.describeForPublicPlanning(new OperationKey("metadata-action-7")));
        assertTrue(invalid.actionBindings().isEmpty());
    }

    @Test void recordRequiresVerifierForActionsWhileReadMetadataMayOmitIt() {
        var action = new ExecutableStepBindings.InstalledStep(new OperationKey("metadata-action-7"), ExecutableStepBindings.Kind.ACTION,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), PRODUCER, DECODER);
        assertThrows(IllegalArgumentException.class, () -> new ExecutableStepBindings.PublicPlanningStep(action, Optional.empty()));
        var read = new ExecutableStepBindings.InstalledStep(new OperationKey("metadata-read"), ExecutableStepBindings.Kind.READ,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), PRODUCER, DECODER);
        assertEquals(Optional.empty(), new ExecutableStepBindings.PublicPlanningStep(read, Optional.empty()).archivedVerifierSource());
    }

    private static ReadContract<PlanningReadReceipt> read(String id, ReadContract.GuardMode mode) {
        return new ReadContract<>(id, new OperationKey("metadata-read"), Optional.of("game.query.metadata-read"), "metadata-only",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, mode, PRODUCER,
                request -> { throw new AssertionError("metadata must not prepare a read"); },
                receipt -> { throw new AssertionError("metadata must not decode a read result"); });
    }
    @Test void installedReadOriginAmbiguityAndFamilyWithoutPureDecoderNeverGuessADescription() {
        var gameplay = read("metadata:gameplay", ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
        var single = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of(gameplay)), List.of(), 4);
        var actual = single.describeForPublicPlanning(new OperationKey("metadata-read")).orElseThrow();
        assertEquals(ExecutableStepBindings.Kind.READ, actual.descriptor().kind()); assertTrue(actual.archivedVerifierSource().isEmpty());
        var frontend = read("metadata:frontend", ReadContract.GuardMode.FRONTEND_SESSION);
        var ambiguous = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of(gameplay, frontend)), List.of(), 4);
        assertThrows(IllegalArgumentException.class, () -> ambiguous.describeForPublicPlanning(new OperationKey("metadata-read")));
        var noDecoder = new RootExecutableBindings.Family<>("no-pure-decoder", Long.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.empty(), PRODUCER, DECODER, VERIFIER, value -> raw("{}"), value -> new OperationKey("metadata-action-" + value),
                value -> { throw new AssertionError("metadata must not invoke an opaque family factory"); });
        var opaque = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(), List.of(), List.of(noDecoder), 4);
        assertTrue(opaque.describeForPublicPlanning(new OperationKey("metadata-action-7")).isEmpty());
        assertTrue(opaque.actionBindings().isEmpty()); assertTrue(opaque.archivedBindings().isEmpty());
    }
}
