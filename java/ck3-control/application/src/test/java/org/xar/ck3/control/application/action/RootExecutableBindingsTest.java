package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;

final class RootExecutableBindingsTest {
    private static final ExactRef PREPARER = new ExactRef("D:/fixture/preparer.java", 1, "a".repeat(64));
    private static final ExactRef DECODER = new ExactRef("D:/fixture/decoder.java", 1, "b".repeat(64));
    private static final ExactRef VERIFIER = new ExactRef("D:/fixture/verifier.java", 1, "c".repeat(64));
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static RootExecutableBindings.IssuedAction pair(int target) {
        OperationKey operation = new OperationKey("move-army-" + target);
        var binding = new NativeEffectRegistry.Binding(operation, PREPARER,
                command -> new NativeRequest(operation.value(), Optional.empty(), raw("{}")),
                (command, attempt, dispatch) -> NativeEffectRegistry.Projected.pending("fixture pending", List.of()));
        return new RootExecutableBindings.IssuedAction(new RootExecutableBindings.ActionBinding(binding,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), DECODER),
                new NativeRecordedEvidenceVerifier.Binding(operation, VERIFIER, (head, proposed, archive) -> { }));
    }
    private static RootExecutableBindings.Family<Integer> family(String id) {
        return new RootExecutableBindings.Family<>(id, Integer.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.empty(), PREPARER, DECODER, VERIFIER, value -> raw("{\"target\":" + value + "}"),
                value -> new OperationKey("move-army-" + value), RootExecutableBindingsTest::pair);
    }
    @Test void issuedActionAndOriginalEvidenceReplayEnterTheSameLiveRegistry() {
        var family = family("army-move");
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(), List.of(), List.of(family), 16);
        NativeEffectRegistry live = catalog.effects(); assertTrue(live.installed().isEmpty());
        var actual = catalog.issue(family, 7); OperationKey operation = actual.effect().operation();
        assertSame(actual.effect(), live.installed().getFirst()); assertSame(actual.effect(), catalog.actualActionBinding(operation).orElseThrow());
        assertSame(actual, catalog.issue(family, 7)); assertEquals(1, live.installed().size());
        assertEquals(operation, catalog.actualArchivedVerifier(operation).orElseThrow().operation());
        assertSame(family, catalog.actualFamily(operation).orElseThrow());
        catalog.requireCompleteArchiveCoverage();
    }
    @Test void equalButUninstalledFamilyCannotIssueAnAction() {
        var actual = family("army-move"); var forged = family("army-move");
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(), List.of(), List.of(actual), 16);
        assertThrows(IllegalArgumentException.class, () -> catalog.issue(forged, 7));
        assertTrue(catalog.effects().installed().isEmpty()); assertTrue(catalog.archivedBindings().isEmpty());
    }
    @Test void conflictingFamiliesCannotReplaceTheActualOperationOrVerifier() {
        var first = family("one"); var second = family("two");
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(), List.of(), List.of(first, second), 16);
        var retained = catalog.issue(first, 7); var verifier = catalog.actualArchivedVerifier(retained.effect().operation()).orElseThrow();
        assertThrows(IllegalArgumentException.class, () -> catalog.issue(second, 7));
        assertSame(retained.effect(), catalog.actualActionBinding(retained.effect().operation()).orElseThrow());
        assertSame(verifier, catalog.actualArchivedVerifier(retained.effect().operation()).orElseThrow());
        assertSame(first, catalog.actualFamily(retained.effect().operation()).orElseThrow());
    }
    @Test void actionWithoutItsRealArchiveVerifierCannotCompleteTheRootGraph() {
        var action = pair(7).action();
        var catalog = RootExecutableBindings.freeze(List.of(action), RootReadContractCatalog.staticOnly(List.of()), List.of(), 16);
        assertThrows(IllegalArgumentException.class, catalog::requireCompleteArchiveCoverage);
    }
    private static RootExecutableBindings.Family<Integer> operationFamily(String id, AtomicInteger constructed,
            RootExecutableBindings.OperationDecoder<Integer> decoder) {
        return new RootExecutableBindings.Family<>(id, Integer.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.empty(), PREPARER, DECODER, VERIFIER, value -> raw("{\"target\":" + value + "}"),
                value -> new OperationKey("move-army-" + value), value -> { constructed.incrementAndGet(); return pair(value); }, decoder);
    }
    @Test void typedOperationResolutionInstallsOneActualActionAndReplayBeforeTheGuardLookup() {
        var constructed = new AtomicInteger();
        var family = operationFamily("operation-move", constructed, operation ->
                operation.value().equals("move-army-7") ? Optional.of(7) : Optional.empty());
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(),
                List.of(), List.of(family), 16);
        var operation = new OperationKey("move-army-7");
        assertEquals(ExecutableStepBindings.Kind.ACTION, catalog.resolve(operation).orElseThrow().kind());
        var original = catalog.actualActionBinding(operation).orElseThrow();
        assertEquals(1, constructed.get());
        assertSame(original, catalog.actualActionBinding(operation).orElseThrow());
        assertSame(original, catalog.issue(family, 7).effect());
        assertSame(family, catalog.actualFamily(operation).orElseThrow());
        assertEquals(VERIFIER, catalog.actualArchivedVerifier(operation).orElseThrow().definitionSource());
        catalog.requireCompleteArchiveCoverage();
        assertEquals(1, constructed.get());
    }
    @Test void unrecognizedOperationCannotConstructAnyNativeBinding() {
        var constructed = new AtomicInteger();
        var family = operationFamily("operation-move", constructed, operation -> Optional.empty());
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(),
                List.of(), List.of(family), 16);
        assertTrue(catalog.resolve(new OperationKey("move-army-7")).isEmpty());
        assertTrue(catalog.actualActionBinding(new OperationKey("move-army-07")).isEmpty());
        assertEquals(0, constructed.get()); assertTrue(catalog.archivedBindings().isEmpty());
    }
    @Test void ambiguousOperationDecodersFailBeforeEitherActualFactoryRuns() {
        var constructed = new AtomicInteger();
        var first = operationFamily("operation-one", constructed, operation -> Optional.of(7));
        var second = operationFamily("operation-two", constructed, operation -> Optional.of(7));
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(),
                List.of(), List.of(first, second), 16);
        assertThrows(IllegalArgumentException.class, () -> catalog.resolve(new OperationKey("move-army-7")));
        assertEquals(0, constructed.get()); assertTrue(catalog.actionBindings().isEmpty()); assertTrue(catalog.archivedBindings().isEmpty());
    }
    @Test void operationDecoderCannotRenameTheRequestedTypedOperation() {
        var constructed = new AtomicInteger();
        var family = operationFamily("operation-move", constructed, operation -> Optional.of(8));
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(),
                List.of(), List.of(family), 16);
        assertThrows(IllegalArgumentException.class, () -> catalog.resolve(new OperationKey("move-army-7")));
        assertEquals(0, constructed.get()); assertTrue(catalog.actionBindings().isEmpty()); assertTrue(catalog.archivedBindings().isEmpty());
    }
    private static RootExecutableBindings.CompositeBinding composite() {
        CompositeActionPort actual = new CompositeActionPort() {
            @Override public String handlerId() { return "retreat-composite-fixture"; }
            @Override public boolean supports(OperationKey operation) { return operation.value().matches("retreat-token-[0-9]+"); }
            @Override public void validate(ActionCommand parent) { throw new AssertionError("issuance test cannot validate a live action"); }
            @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) { throw new AssertionError("issuance test cannot submit"); }
            @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution retained) { throw new AssertionError("issuance test cannot observe a game"); }
        };
        return new RootExecutableBindings.CompositeBinding(actual, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), PREPARER, DECODER);
    }
    private static RootExecutableBindings.CompositeFamily<Integer> compositeFamily(String id,
            RootExecutableBindings.CompositeBinding actual, ExactRef expectedReplaySource) {
        return new RootExecutableBindings.CompositeFamily<>(id, Integer.class, actual, expectedReplaySource,
                token -> raw("{\"token\":" + token + "}"), token -> new OperationKey("retreat-token-" + token),
                token -> new NativeRecordedEvidenceVerifier.Binding(new OperationKey("retreat-token-" + token), VERIFIER,
                        (head, proposed, archive) -> { throw new AssertionError("fixture cannot grant archived business success"); }));
    }
    @Test void dynamicCompositeRequiresItsActualReplayAndNeverBecomesAPrimitive() {
        var actual = composite(); var family = compositeFamily("retreat", actual, VERIFIER);
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(actual),
                List.of(), List.of(), List.of(family), 16);
        var operation = new OperationKey("retreat-token-7"); assertTrue(catalog.resolve(operation).isEmpty());
        assertSame(actual, catalog.issueComposite(family, 7));
        assertSame(actual.handler(), catalog.composites().find(operation).orElseThrow());
        assertEquals(ExecutableStepBindings.Kind.COMPOSITE, catalog.resolve(operation).orElseThrow().kind());
        assertSame(family, catalog.actualCompositeFamily(operation).orElseThrow());
        assertEquals(VERIFIER, catalog.actualArchivedVerifier(operation).orElseThrow().definitionSource());
        assertSame(actual, catalog.issueComposite(family, 7)); assertEquals(1, catalog.archivedBindings().size());
        assertTrue(catalog.actualActionBinding(operation).isEmpty()); assertTrue(catalog.effects().installed().isEmpty());
    }
    @Test void equalButUninstalledCompositeFamilyCannotPublishReplay() {
        var actual = composite(); var installed = compositeFamily("retreat", actual, VERIFIER);
        var forged = compositeFamily("retreat", actual, VERIFIER);
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(actual),
                List.of(), List.of(), List.of(installed), 16);
        assertThrows(IllegalArgumentException.class, () -> catalog.issueComposite(forged, 7));
        assertTrue(catalog.archivedBindings().isEmpty()); assertTrue(catalog.resolve(new OperationKey("retreat-token-7")).isEmpty());
    }
    @Test void compositeReplayCannotChangeItsFixedSource() {
        var actual = composite(); var family = compositeFamily("retreat", actual, DECODER);
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(actual),
                List.of(), List.of(), List.of(family), 16);
        assertThrows(IllegalArgumentException.class, () -> catalog.issueComposite(family, 7));
        assertTrue(catalog.archivedBindings().isEmpty()); assertTrue(catalog.resolve(new OperationKey("retreat-token-7")).isEmpty());
    }
    @Test void compositeFamilyCannotInstallADifferentHandlerObject() {
        var actual = composite(); var forgedHandler = composite(); var family = compositeFamily("retreat", forgedHandler, VERIFIER);
        assertThrows(IllegalArgumentException.class, () -> RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()),
                List.of(actual), List.of(), List.of(), List.of(family), 16));
    }

    @Test void operationOnlyResolutionIsAmbiguousWithDirectReadAndComposite() {
        var comp = composite();
        var readOp = new OperationKey("retreat-token-7");
        var readContract = new ReadContract<RawJson>("read-7", readOp, Optional.empty(), "perm", ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.FRONTEND_SESSION, PREPARER, req -> { throw new AssertionError("read prepare"); }, rec -> { throw new AssertionError("read decode"); });
        var replay = new NativeRecordedEvidenceVerifier.Binding(readOp, VERIFIER, (head, proposed, archive) -> { throw new AssertionError("no live replay"); });
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of(readContract)), List.of(comp), List.of(replay), List.of(), List.of(), 16);
        assertEquals(ExecutableStepBindings.Kind.READ, catalog.resolve(readOp, ReadContract.GuardMode.FRONTEND_SESSION).orElseThrow().kind());
        assertEquals(ExecutableStepBindings.Kind.COMPOSITE, catalog.resolve(readOp, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).orElseThrow().kind());
        assertSame(comp.handler(), catalog.composites().find(readOp).orElseThrow());
        assertThrows(IllegalArgumentException.class, () -> catalog.resolve(readOp));
    }

    @Test void sameModeReadAndCompositeConflictThrows() {
        var comp = composite();
        var readOp = new OperationKey("retreat-token-7");
        var readContract = new ReadContract<RawJson>("read-7", readOp, Optional.empty(), "perm", ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, PREPARER, req -> { throw new AssertionError("read prepare"); }, rec -> { throw new AssertionError("read decode"); });
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of(readContract)), List.of(comp), List.of(), List.of(), List.of(), 16);
        assertThrows(IllegalArgumentException.class, () -> catalog.resolve(readOp, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP));
    }
    @Test void compositeProtocolIdentityRejectsExplicitOriginalId() {
        var operation = ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT.operation();
        var handler = new CompositeActionPort() {
            @Override public String handlerId() { return "council-composite-fixture"; }
            @Override public boolean supports(OperationKey op) { return op.equals(operation); }
            @Override public void validate(ActionCommand parent) { throw new AssertionError("composite protocol qualification cannot validate"); }
            @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) { throw new AssertionError("composite protocol qualification cannot run"); }
            @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution retained) { throw new AssertionError("composite protocol qualification cannot observe"); }
        };
        var binding = new RootExecutableBindings.CompositeBinding(handler, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), PREPARER, DECODER);
        var replay = new NativeRecordedEvidenceVerifier.Binding(operation, VERIFIER, (head, proposed, archive) -> { throw new AssertionError("protocol qualification cannot replay archived business"); });
        var catalog = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(binding), List.of(replay), List.of(), List.of(), 16);
        var base = ActionCoordinatorTest.command("composite-protocol", operation.value());
        catalog.requireProtocolIdentity(base);
        var explicit = new ActionCommand(base.actionId(), base.origin(), base.source(), base.sessionId(), base.operation(), base.arguments(), base.expectation(), base.claims(), base.deadline(),
                new ExplicitOriginalProtocolId(ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT, "council-test", PREPARER));
        assertThrows(IllegalArgumentException.class, () -> catalog.requireProtocolIdentity(explicit));
    }

    @Test void readMetadataViewsShareOnlyAvailabilityAndReportEveryCapabilityConflict() {
        var operation=new OperationKey("query-read-view-test");
        var base=new ReadContract<RawJson>("read-view-base",operation,Optional.of("view-cap"),"view-cap",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,PREPARER,
                request->{throw new AssertionError("inventory is not a live read");},receipt->raw("{}"));
        
        // Case 1: Same op/mode/cap, different wire/perm/key -> should coalesce in installed(), but both remain in readCatalog
        var sameCapDiffWire=new ReadContract<RawJson>("read-view-same-cap",operation,Optional.of("view-cap"),"other-key",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.G2_PRIVATE_QUERY,DECODER,
                request->{throw new AssertionError("inventory is not a live read");},receipt->raw("{}"));
        var catalog1=RootExecutableBindings.freeze(List.of(),RootReadContractCatalog.staticOnly(List.of(base,sameCapDiffWire)),List.of(),16);
        var installed1=catalog1.installed();
        assertEquals(1, installed1.stream().filter(s -> s.kind() == ExecutableStepBindings.Kind.READ && s.operation().equals(operation)).count(), "same op/mode/cap must coalesce to one metadata view");
        assertEquals(2, catalog1.readCatalog().installed().size(), "actual contracts must remain distinct in readCatalog");
        
        // Case 2: Different cap -> must conflict
        var diffCap=new ReadContract<RawJson>("read-view-diff-cap",operation,Optional.of("other-cap"),"view-cap",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,DECODER,
                request->{throw new AssertionError("inventory is not a live read");},receipt->raw("{}"));
        var catalog2=RootExecutableBindings.freeze(List.of(),RootReadContractCatalog.staticOnly(List.of(base,diffCap)),List.of(),16);
        var ex2=assertThrows(IllegalArgumentException.class,catalog2::installed,"different capability must remain a real conflict");
        assertTrue(ex2.getMessage().contains("read-view-base") && ex2.getMessage().contains("read-view-diff-cap"),"exception must include all conflicting contract IDs");
        
        // Case 3: Multiple conflicts on at least two operations appear in ONE exception
        var op1=new OperationKey("query-conflict-1");
        var op2=new OperationKey("query-conflict-2");
        var c1a=new ReadContract<RawJson>("c1a",op1,Optional.of("cap1"),"k1",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,PREPARER,
                request->{throw new AssertionError("no live read");},receipt->raw("{}"));
        var c1b=new ReadContract<RawJson>("c1b",op1,Optional.of("cap2"),"k1",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,DECODER,
                request->{throw new AssertionError("no live read");},receipt->raw("{}"));
        var c1c=new ReadContract<RawJson>("c1c",op1,Optional.of("cap1"),"k1",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,PREPARER,
                request->{throw new AssertionError("no live read");},receipt->raw("{}"));
        var c2a=new ReadContract<RawJson>("c2a",op2,Optional.of("cap3"),"k2",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,PREPARER,
                request->{throw new AssertionError("no live read");},receipt->raw("{}"));
        var c2b=new ReadContract<RawJson>("c2b",op2,Optional.of("cap4"),"k2",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,DECODER,
                request->{throw new AssertionError("no live read");},receipt->raw("{}"));
        var catalog3=RootExecutableBindings.freeze(List.of(),RootReadContractCatalog.staticOnly(List.of(c1a,c1b,c1c,c2a,c2b)),List.of(),16);
        var ex3=assertThrows(IllegalArgumentException.class,catalog3::installed);
        var msg=ex3.getMessage();
        assertTrue(msg.contains("query-conflict-1"),"exception must include first conflicting operation");
        assertTrue(msg.contains("query-conflict-2"),"exception must include second conflicting operation");
        assertTrue(msg.contains("c1a") && msg.contains("c1b") && msg.contains("c1c"),"exception must include all member IDs in first group");
        assertTrue(msg.contains("c2a") && msg.contains("c2b"),"exception must include all member IDs in second group");
        
        // Case 4: Private contracts with Optional.empty cap, different key/wire -> coalesce
        var privOp=new OperationKey("query-private-test");
        var p1=new ReadContract<RawJson>("p1",privOp,Optional.empty(),"key1",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,PREPARER,
                request->{throw new AssertionError("no live read");},receipt->raw("{}"));
        var p2=new ReadContract<RawJson>("p2",privOp,Optional.empty(),"key2",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,DECODER,
                request->{throw new AssertionError("no live read");},receipt->raw("{}"));
        var catalog4=RootExecutableBindings.freeze(List.of(),RootReadContractCatalog.staticOnly(List.of(p1,p2)),List.of(),16);
        var installed4=catalog4.installed();
        assertEquals(1, installed4.stream().filter(s -> s.kind() == ExecutableStepBindings.Kind.READ && s.operation().equals(privOp)).count(), "private same cap(empty) must coalesce");
        assertEquals(2, catalog4.readCatalog().installed().size(), "actual private contracts must remain distinct");
        assertTrue(catalog4.readCatalog().containsIdentity(p1));assertTrue(catalog4.readCatalog().containsIdentity(p2));
        assertEquals(ExecutableStepBindings.Kind.READ,catalog4.describeForPublicPlanning(privOp).orElseThrow().descriptor().kind());
        assertEquals("key1",p1.permissionKey());assertEquals("key2",p2.permissionKey());
        assertEquals(ReadContract.WireProfile.EXECUTE_STEP,p1.wireProfile());assertEquals(ReadContract.WireProfile.G2_PRIVATE_QUERY,p2.wireProfile());
        for(String field:List.of("guardMode=","cap=","wire=","permMode=","permKey="))assertTrue(msg.contains(field),field);
    }

}
