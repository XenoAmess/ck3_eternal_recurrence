package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;

/** Descriptor DATA is not a private Current or an installed query permit; the actual Root refusal is tested separately. */
final class PendingCloseReconciliationAdmissionTest {
    private static RawJson raw() { return new RawJson("{}".getBytes(StandardCharsets.UTF_8)); }
    private static ReadContract<RawJson> descriptor() {
        var operation = new OperationKey(NativeTimelineBlocker12004.QUERY_STEP);
        var source = new ExactRef(Path.of("software-pending-close-descriptor").toAbsolutePath().toString(), 1, "0".repeat(64));
        return new ReadContract<>(RootPendingUiCloseReconciliation.CONTRACT, operation, Optional.empty(),
                "allow_private_current_timeline_blocker_query", ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.RECONCILIATION_OBSERVATION, source,
                (request, id) -> new NativeRequest(operation.value(), Optional.empty(), raw()),
                receipt -> receipt.original().originalResultToken().orElseThrow(),
                receipt -> receipt.original().originalResultToken().orElseThrow());
    }
    private static RootReconciliationAuthority.AllowedRead allowed(ReadContract<?> actual) {
        return new RootReconciliationAuthority.AllowedRead(actual, new OpportunityJson.Obj(Map.of()),
                RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE);
    }
    private static ReadContract<RawJson> copy(ReadContract<?> original, String id, OperationKey operation,
            Optional<String> capability, String permission, ReadContract.PermissionMode mode,
            ReadContract.WireProfile wire, ReadContract.GuardMode guard, boolean replay) {
        if (!replay) return new ReadContract<>(id, operation, capability, permission, mode, wire, guard, original.sourceRef(),
                (request, requestId) -> original.prepare(request, requestId), receipt -> raw());
        return new ReadContract<>(id, operation, capability, permission, mode, wire, guard, original.sourceRef(),
                (request, requestId) -> original.prepare(request, requestId), receipt -> raw(), receipt -> raw());
    }
    @Test void exactPureDescriptorIsDataUntilTheCanonicalPendingAndM3BinderAdmitIt() {
        var actual = descriptor();
        RootPendingUiCloseReconciliation.requireProfile(actual);
        assertSame(actual, allowed(actual).contract());
        assertEquals(RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE, allowed(actual).kind());
    }
    @Test void closeTimelineCannotBorrowOrdinaryTerminalAdvertisedOrAnotherPrivateReadProfile() {
        var c = descriptor();
        List<Supplier<ReadContract<?>>> invalid = List.of(
                () -> copy(c, c.contractId()+"/other", c.operation(), c.requiredCapability(), c.permissionKey(), c.permissionMode(), c.wireProfile(), c.guardMode(), true),
                () -> copy(c, c.contractId(), new OperationKey(NativeTimelineBlocker12004.CLOSE_STEP), c.requiredCapability(), c.permissionKey(), c.permissionMode(), c.wireProfile(), c.guardMode(), true),
                () -> copy(c, c.contractId(), c.operation(), Optional.of("game.command.foreign-query"), c.permissionKey(), c.permissionMode(), c.wireProfile(), c.guardMode(), true),
                () -> copy(c, c.contractId(), c.operation(), c.requiredCapability(), "allow_private_other_query", c.permissionMode(), c.wireProfile(), c.guardMode(), true),
                () -> copy(c, c.contractId(), c.operation(), c.requiredCapability(), c.permissionKey(), ReadContract.PermissionMode.ADVERTISED_CAPABILITY, c.wireProfile(), c.guardMode(), true),
                () -> copy(c, c.contractId(), c.operation(), c.requiredCapability(), c.permissionKey(), c.permissionMode(), ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS, c.guardMode(), true),
                () -> copy(c, c.contractId(), c.operation(), c.requiredCapability(), c.permissionKey(), c.permissionMode(), c.wireProfile(), ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, true),
                () -> copy(c, c.contractId(), c.operation(), c.requiredCapability(), c.permissionKey(), c.permissionMode(), c.wireProfile(), ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION, true),
                () -> copy(c, c.contractId(), c.operation(), c.requiredCapability(), c.permissionKey(), c.permissionMode(), c.wireProfile(), c.guardMode(), false));
        for (var candidate : invalid) assertThrows(IllegalArgumentException.class, () -> allowed(candidate.get()));
    }
}
