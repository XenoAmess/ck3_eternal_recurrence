package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusQueries;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.root.RootReconciliationAuthority;

/** Strict family boundary over the actual native profile producer; constructing these data grants no live scope. */
final class ChildFocusReconciliationFamilyAdmissionTest {
    @TempDir Path temporary;
    private static final Obj ARGUMENTS = new Obj(Map.of());

    private ExactRef source(String name) throws Exception {
        Path path = temporary.resolve(name); byte[] bytes = ("finite software source " + name).getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(path, bytes); return new ExactRef(path.toAbsolutePath().toString(), bytes.length, ActionCodec.sha256(bytes));
    }
    private ReadContract<Obj> actualProfile() throws Exception {
        var ordinary = ChildEducationFocusQueries.contracts(source("native-source"), (request, pending) -> {
            throw new AssertionError("family-boundary regression cannot acquire ordinary admission");
        }).receipt();
        return ChildEducationFocusQueries.reconciliationReceipt(ordinary, source("profile-factory"),
                new ChildEducationFocusQueries.CanonicalAdmission() {
                    @Override public void verifyCurrent(PlanningReadRequest request, ChildEducationFocus.Pending pending) {
                        throw new AssertionError("constructing a contract or AllowedRead cannot acquire a current canonical scope");
                    }
                    @Override public void verifyOriginal(PlanningReadReceipt receipt, ChildEducationFocus.Pending pending) {
                        throw new AssertionError("no archive receipt was supplied to this family-boundary regression");
                    }
                });
    }
    private static ReadContract<Obj> copy(ReadContract<Obj> original, String contractId, OperationKey operation,
            Optional<String> capability, String permission, ReadContract.PermissionMode permissionMode,
            ReadContract.WireProfile wire, ReadContract.GuardMode guard) {
        return new ReadContract<>(contractId, operation, capability, permission, permissionMode, wire, guard, original.sourceRef(),
                original::prepare, original::decode, original::replay);
    }
    private static RootReconciliationAuthority.AllowedRead allowed(ReadContract<Obj> contract) {
        return new RootReconciliationAuthority.AllowedRead(contract, ARGUMENTS,
                RootReconciliationAuthority.QueryKind.CHILD_EDUCATION_FOCUS_RECEIPT);
    }

    @Test void independentNativeReceiptProfileIsTheOnlyChildFocusFamilyDescriptor() throws Exception {
        var actual = actualProfile();
        assertSame(actual, allowed(actual).contract(), "data preserves the identical actual native producer contract");
        assertTrue(actual.hasPureReplay());
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(actual, ChildEducationFocusQueries.RECEIPT_CONTRACT,
                actual.operation(), actual.requiredCapability(), actual.permissionKey(), actual.permissionMode(), actual.wireProfile(), actual.guardMode())));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(actual, actual.contractId(),
                new OperationKey(ChildEducationFocus.QUERY_STEP), actual.requiredCapability(), actual.permissionKey(),
                actual.permissionMode(), actual.wireProfile(), actual.guardMode())));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(actual, actual.contractId(), actual.operation(),
                actual.requiredCapability(), "another-private-family", actual.permissionMode(), actual.wireProfile(), actual.guardMode())));
        var missingReplay = new ReadContract<Obj>(actual.contractId(), actual.operation(), actual.requiredCapability(), actual.permissionKey(),
                actual.permissionMode(), actual.wireProfile(), actual.guardMode(), actual.sourceRef(), actual::prepare, actual::decode);
        assertThrows(IllegalArgumentException.class, () -> allowed(missingReplay));
    }

    @Test void ordinaryGuardAdvertisedCapabilityAndDifferentWireCannotBorrowFocusReceiptReconciliation() throws Exception {
        var actual = actualProfile();
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(actual, actual.contractId(), actual.operation(),
                actual.requiredCapability(), actual.permissionKey(), actual.permissionMode(), actual.wireProfile(), ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP)));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(actual, actual.contractId(), actual.operation(),
                Optional.of("game.command." + ChildEducationFocus.RECEIPT_STEP), "game.command." + ChildEducationFocus.RECEIPT_STEP,
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, actual.wireProfile(), actual.guardMode())));
        assertThrows(IllegalArgumentException.class, () -> allowed(copy(actual, actual.contractId(), actual.operation(),
                actual.requiredCapability(), actual.permissionKey(), actual.permissionMode(), ReadContract.WireProfile.G2_PRIVATE_QUERY, actual.guardMode())));
    }
}
