package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyHeirLegality;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyRootBinding;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/** Reuses the relocated ROOT96 originals; leaf arguments are software-produced DATA. */
final class FamilyRootArgumentsPortableRegressionTest {
    @TempDir Path temporary;

    @Test void retainedRootProducerArgumentsRoundTripThroughTypedLeafDecoder() throws Exception {
        var actual = actual();
        var basis = FamilyRootBinding.fromOriginal(actual.root(), actual.context());
        var arguments = arguments(actual, basis);
        var reads = new AtomicInteger();
        FamilyRootBinding.Originals originals = reference -> {
            assertEquals(actual.root().originalReceipt(), reference);
            reads.incrementAndGet();
            return actual.root();
        };

        assertEquals(basis, FamilyRootBinding.decodeArguments(leaf(actual, arguments), actual.context(), originals));
        assertEquals(1, reads.get());
        assertEquals(arguments, DriverJson.object(DriverJson.encode(arguments), RawJson.MAXIMUM_BYTES));
        assertEquals(actual.context(), basis.binding().context());
        assertEquals(BigInteger.valueOf(21), actual.context().before().frame().identity().nativeRevision());
        assertEquals(BigInteger.valueOf(22), actual.context().before().frame().revision());
    }

    @Test void typedBindingRejectsChangedValuesTypesArraysAndExtraFields() throws Exception {
        var actual = actual();
        var basis = FamilyRootBinding.fromOriginal(actual.root(), actual.context());
        var arguments = arguments(actual, basis);
        var binding = OpportunityJson.object(arguments.get("root_binding"), "retained root binding");
        FamilyRootBinding.Originals originals = reference -> {
            assertEquals(actual.root().originalReceipt(), reference);
            return actual.root();
        };

        reject(actual, arguments, binding.with("root_query_sequence",
                new IntegerValue(basis.binding().rootQuerySequence().add(BigInteger.ONE))), originals);
        reject(actual, arguments, binding.with("observed_first_heir_character_id",
                new IntegerValue(BigInteger.valueOf(basis.binding().observedFirstHeir().orElseThrow()).add(BigInteger.ONE))), originals);
        for (Value replacement : List.of(new Bool(true), new Text(basis.binding().rootQuerySequence().toString()),
                new Arr(List.of(new IntegerValue(BigInteger.ONE), new IntegerValue(BigInteger.TWO))),
                new Arr(List.of(new IntegerValue(BigInteger.TWO), new IntegerValue(BigInteger.ONE))))) {
            reject(actual, arguments, binding.with("root_query_sequence", replacement), originals);
        }
        reject(actual, arguments, binding.with("original_root_receipt", new Arr(List.of())), originals);
        // This closed three-field binding has no legal array field, in either order.
        reject(actual, arguments, binding.with("extra", new Arr(List.of(new IntegerValue(BigInteger.ONE), new IntegerValue(BigInteger.TWO)))), originals);
        reject(actual, arguments, binding.with("extra", new Arr(List.of(new IntegerValue(BigInteger.TWO), new IntegerValue(BigInteger.ONE)))), originals);
    }

    private FamilyRootPortableRegressionTest.Actual actual() throws Exception {
        var fixture = new FamilyRootPortableRegressionTest();
        fixture.temporary = temporary;
        return fixture.actual();
    }

    private static Obj arguments(FamilyRootPortableRegressionTest.Actual actual, FamilyRootBinding.Basis basis) {
        return FamilyRootBinding.arguments(basis,
                new Obj(Map.of("expected_native_revision", new IntegerValue(actual.context().revision()))));
    }

    private static PlanningReadRequest leaf(FamilyRootPortableRegressionTest.Actual actual, Obj arguments) {
        var context = actual.context();
        return new PlanningReadRequest(context.before(), context.source(), context.sessionId(),
                new OperationKey(FamilyHeirLegality.STEP), arguments, context.deadline());
    }

    private static void reject(FamilyRootPortableRegressionTest.Actual actual, Obj arguments, Obj binding,
                               FamilyRootBinding.Originals originals) {
        assertThrows(IllegalArgumentException.class, () -> FamilyRootBinding.decodeArguments(
                leaf(actual, arguments.with("root_binding", binding)), actual.context(), originals));
    }
}
