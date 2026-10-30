package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyHeirLegality;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyRootBinding;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Build;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Context;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RootInteractionContextProjection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.root.RootFamilyCampaignRead;

/** Relocated natural worker96 DATA traverses the production decoder/projectors. No RootContext, readiness lease, Native query or lineage proof is invented. */
final class FamilyRootPortableRegressionTest {
    @org.junit.jupiter.api.io.TempDir Path temporary;
    record Actual(PlanningReadResult.Known<Obj> root, Context context) { }

    @Test void naturalRootReceiptAndRealFrameProjectionReachHeirBindingWithActualExeSha() throws Exception {
        var actual = actual(); var context = actual.context();
        assertEquals(Build.CROZIER4, context.build());
        assertEquals("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518", context.source().exactBuild());
        assertEquals(BigInteger.valueOf(11), context.connectionGeneration());
        assertEquals(BigInteger.valueOf(21), context.before().frame().identity().nativeRevision());
        assertEquals(BigInteger.valueOf(22), context.before().frame().revision());
        var basis = FamilyRootBinding.fromOriginal(actual.root(), context);
        assertEquals(actual.root().originalReceipt(), basis.originalRootReceipt());
        assertEquals(context, basis.binding().context());
        assertTrue(basis.binding().observedFirstHeir().orElseThrow() > 0);
        assertEquals(actual.root().value().get("query_sequence"),
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(basis.binding().rootQuerySequence()));
    }

    @Test void bindingRejectsVersionStringsWrongExeAndWrongBuildWhileAcceptingHashCase() throws Exception {
        var actual = actual(); var context = actual.context();
        var root = actual.root().originalReceipt();
        var sequence = BigInteger.ONE;
        assertThrows(IllegalArgumentException.class, () -> new FamilyHeirLegality.Binding(
                changedSource(context, Build.CROZIER4.version(), Build.CROZIER4), sequence, java.util.OptionalLong.empty(), root));
        assertThrows(IllegalArgumentException.class, () -> new FamilyHeirLegality.Binding(
                changedSource(context, "0".repeat(64), Build.CROZIER4), sequence, java.util.OptionalLong.empty(), root));
        assertThrows(IllegalArgumentException.class, () -> new FamilyHeirLegality.Binding(
                changedSource(context, context.source().exactBuild(), Build.CROZIER3), sequence, java.util.OptionalLong.empty(), root));
        var lowercase = changedSource(context, context.source().exactBuild().toLowerCase(Locale.ROOT), Build.CROZIER4);
        assertEquals(lowercase, new FamilyHeirLegality.Binding(lowercase, sequence, java.util.OptionalLong.empty(), root).context());
        // A qualified Build3 projection cannot consume this actual Build4 HELLO.
        var receipt = actual.root().receipt();
        var frame = RootGuardEvidence.loadFrame(receipt.before().binding(), originals(),
                new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
        assertThrows(IllegalArgumentException.class, () -> new RootInteractionContextProjection(Build.CROZIER3).project(frame, receipt.request().deadline()));
    }

    Actual actual() throws Exception {
        var reference = PortableRoot96Fixture.materialize(temporary);
        var receipt = new NativeArchiveDataCodec(FamilyRootPortableRegressionTest::exact).decodeRead(reference);
        var frame = RootGuardEvidence.loadFrame(receipt.before().binding(), originals(),
                new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
        var context = new RootInteractionContextProjection(Build.CROZIER4).project(frame, receipt.request().deadline());
        assertEquals(receipt.request().before(), context.before());
        var definitions = new FinanceReadContracts(query -> new FinanceReadContracts.Registration(reference,
                new FinanceReadContracts.Permission(Optional.empty(), query.operation().value(),
                        org.xar.ck3.control.application.action.ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                        org.xar.ck3.control.application.action.ReadContract.WireProfile.EXECUTE_STEP)));
        var packet = definitions.decodeOriginal(FinanceReadContracts.Query.ROOT, receipt, frame.semantic());
        var value = RootFamilyCampaignRead.project(packet.result(), receipt);
        return new Actual(new PlanningReadResult.Known<>(value, receipt, reference), context);
    }

    private static Context changedSource(Context original, String exactBuild, Build build) {
        var source = original.source();
        return new Context(original.before(), new G2Source(source.machineId(), source.observedAtUtc(), exactBuild, source.sourceRef()),
                original.sessionId(), original.connectionGeneration(), build, original.deadline(), original.controls());
    }

    private static ActionPorts.OutcomeArchive originals() {
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(FamilyRootPortableRegressionTest.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, arguments) -> switch (method.getName()) {
                    case "loadNativeFrame", "readOriginalPacket" -> exact((ExactRef) arguments[0], WriterContracts.MAX_PIN_BYTES);
                    case "loadMaterial" -> new RawJson(exact((ExactRef) arguments[0], RawJson.MAXIMUM_BYTES));
                    case "loadFullMaterial" -> RawJson.fullMaterial(exact((ExactRef) arguments[0], WriterContracts.MAX_PIN_BYTES));
                    default -> throw new AssertionError("archive-only family original refuses: " + method.getName());
                });
    }

    private static byte[] exact(ExactRef reference, int maximum) throws IOException {
        byte[] bytes = Files.readAllBytes(Path.of(reference.path()));
        StrictJson.require(bytes.length == reference.bytes() && bytes.length <= maximum && DriverJson.sha256(bytes).equals(reference.sha256()),
                "actual family96 original length/SHA differs");
        return bytes;
    }
}
