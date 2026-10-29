package org.xar.ck3.control.application.session;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Freezes the actual complete state authority; no default history, rollback,
 * restoration, succession or goal state is synthesized by the loop.
 */
public final class FrozenDriverSnapshotSupplier implements DriverCheckpointStore.SnapshotSupplier {
    public interface StateAuthority {
        /** Actual state/history lease covers freeze, physical write/readback and CAS; every exception releases it. */
        <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) throws IOException;
    }
    private final StateAuthority authority;
    public FrozenDriverSnapshotSupplier(StateAuthority authority) { this.authority = Objects.requireNonNull(authority); }
    @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) throws IOException {
        Objects.requireNonNull(work);
        return authority.withFrozen((frozen, publisher) -> {
            Objects.requireNonNull(frozen); Objects.requireNonNull(publisher);
            if (frozen instanceof DriverStateSnapshot.Complete complete) DriverStateSnapshot.decodeComplete(complete.encode());
            return work.run(frozen, (expected, published) -> {
                StrictJson.require(expected == frozen, "checkpoint publication did not use the exact frozen state lease");
                validatePublication(expected, published);
                publisher.publish(expected, published);
            });
        });
    }
    private static void validatePublication(DriverStateSnapshot.Complete expected, DriverStateSnapshot.Complete published) {
        StrictJson.require(expected.session().equals(published.session()), "checkpoint publication changed Driver session");
        StrictJson.require(published.commandHistory().size() == expected.commandHistory().size() + 1,
                "checkpoint must append exactly one SAVE row to the complete original history");
        for (int index = 0; index < expected.commandHistory().size(); index++)
            StrictJson.require(Arrays.equals(expected.commandHistory().get(index).originalRow().json(), published.commandHistory().get(index).originalRow().json()), "checkpoint changed an existing Driver history row");
        StrictJson.require(same(expected.managedRestoreTransaction(), published.managedRestoreTransaction())
                && same(expected.successionExpectation(), published.successionExpectation())
                && same(expected.successionLifecycle(), published.successionLifecycle())
                && same(expected.campaignGoal(), published.campaignGoal()), "checkpoint dropped or changed complete original business state");
        StrictJson.require(published.rollbackWarFailures() instanceof DriverStateSnapshot.Value reset
                && StrictJson.parse(reset.json()).isArray() && StrictJson.parse(reset.json()).isEmpty(),
                "a confirmed SAVE must reset rollback_war_failures to the exact JSON empty array");
        StrictJson.require(published.rollbackWarFailure() instanceof DriverStateSnapshot.NullValue,
                "a confirmed SAVE must reset the singular rollback_war_failure advisory to JSON null");
    }
    private static boolean same(DriverStateSnapshot.Slot left, DriverStateSnapshot.Slot right) {
        return left instanceof DriverStateSnapshot.Value a && right instanceof DriverStateSnapshot.Value b
                ? Arrays.equals(a.json(), b.json()) : left.equals(right);
    }
}
