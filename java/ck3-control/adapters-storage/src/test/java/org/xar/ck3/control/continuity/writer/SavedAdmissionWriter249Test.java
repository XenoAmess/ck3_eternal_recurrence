package org.xar.ck3.control.continuity.writer;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Pure routing boundary only. Data constructors supply no file, Admission or submit authority. */
class SavedAdmissionWriter249Test {
    @Test void malformedSavedAdmissionCannotUseEqualStateAsAValidationBypass() throws Exception {
        ContinuityState before = freshData();
        Request detached = request(SavedContinuityBootstrap.KIND);
        assertThrows(ContractViolationException.class, () -> validate(before, before, detached));
    }

    @Test void unrelatedUnchangedReductionStillUsesItsExistingWriterFieldGuards() throws Exception {
        ContinuityState before = freshData();
        // This private pure check is separate from the actual fixed Authority, which is not invoked here.
        // A successful no-change field check grants no action, lifecycle receipt or initialization.
        assertDoesNotThrow(() -> validate(before, before, request(ACTION_LIFECYCLE_KIND)));
        assertEquals(ContinuityState.Status.AWAITING_INITIAL_ENTRY, before.status());
        assertTrue(before.initializedOrigin().isEmpty());
    }

    private static ContinuityState freshData() {
        return FreshContinuityGenesis.initial(new FreshContinuityGenesis.Plan("writer-boundary-fixture249", 2, 10_958),
                new ExactRef("C:/writer-boundary-fixture249/plan.json", 1, "a".repeat(64)));
    }
    private static Request request(String kind) {
        return new Request(kind, ContinuityJson.canonical(StrictJson.object()
                .put("evidence_id", "writer-boundary-fixture249").put("source", "pure-contract-data")), List.of());
    }
    private static void validate(ContinuityState before, ContinuityState after, Request request) throws Exception {
        Method method = ContinuityWriter.class.getDeclaredMethod("validateReduction", ContinuityState.class, ContinuityState.class, Request.class);
        method.setAccessible(true);
        try { method.invoke(null, before, after, request); }
        catch (InvocationTargetException wrapped) {
            if (wrapped.getCause() instanceof RuntimeException failure) throw failure;
            if (wrapped.getCause() instanceof Error failure) throw failure;
            throw wrapped;
        }
    }
}
