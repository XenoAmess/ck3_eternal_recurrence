package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.root.RootReconciliationAuthority;

/** Actual ordinary producer -> independent guardian profile -> strict Root descriptor; data grants no canonical scope. */
final class GuardianReconciliationFamilyAdmissionTest {
    @TempDir Path temporary;
    private static final Obj ARGUMENTS = new Obj(Map.of());

    private ExactRef source(String name) throws Exception {
        Path path = temporary.resolve(name); byte[] bytes = ("finite software source " + name).getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(path, bytes); return new ExactRef(path.toAbsolutePath().toString(), bytes.length, ActionCodec.sha256(bytes));
    }
    /** Test construction reuses the actual installed ordinary-query producer, without issuing any Native request. */
    static ReadContract<OrdinaryContext> profile(ExactRef nativeSource, ExactRef profileSource) {
        return factory(nativeSource,profileSource,new GuardianReconciliationQueries.CanonicalAdmission() {
            @Override public void verifyCurrent(PlanningReadRequest request) { throw new AssertionError("AllowedRead data grants no current admission"); }
            @Override public void verifyOriginal(PlanningReadReceipt receipt) { throw new AssertionError("no actual guardian receipt was supplied"); }
        }).contract();
    }
    static GuardianReconciliationQueries factory(ExactRef nativeSource, ExactRef profileSource,
            GuardianReconciliationQueries.CanonicalAdmission admission) {
        var sources = new InteractionCapabilities.Sources(nativeSource,nativeSource,nativeSource,nativeSource,nativeSource,
                nativeSource,nativeSource,nativeSource,nativeSource,nativeSource);
        var ordinary = new InteractionCapabilities.Installation(sources,
                new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()), new InteractionCapabilities.RootHeirSource() {
                    @Override public PlanningReadResult<HeirSubject> read(Context context) { throw new AssertionError("guardian boundary cannot query first heir"); }
                    @Override public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same, Context context) {
                        throw new AssertionError("guardian boundary cannot query first heir");
                    }
                }).ordinaryQuery();
        return new GuardianReconciliationQueries(ordinary,Build.CROZIER4,profileSource,admission);
    }
    private static ReadContract<OrdinaryContext> copy(ReadContract<OrdinaryContext> original,String contractId,OperationKey operation,
            Optional<String> capability,String permission,ReadContract.PermissionMode mode,ReadContract.WireProfile wire) {
        return new ReadContract<>(contractId,operation,capability,permission,mode,wire,original.guardMode(),original.sourceRef(),
                original::prepare,original::decode,original::replay);
    }
    private static RootReconciliationAuthority.AllowedRead allowed(ReadContract<OrdinaryContext> actual) {
        return new RootReconciliationAuthority.AllowedRead(actual,ARGUMENTS,RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION);
    }

    @Test void onlyTheExactGuardianIndependentProfileOperationAndAdvertisedPermissionAreAdmittedAsData() throws Exception {
        var actual=profile(source("native"),source("profile"));assertSame(actual,allowed(actual).contract());
        assertThrows(IllegalArgumentException.class,()->allowed(copy(actual,"interactions:ordinary-query",actual.operation(),
                actual.requiredCapability(),actual.permissionKey(),actual.permissionMode(),actual.wireProfile())));
        assertThrows(IllegalArgumentException.class,()->allowed(copy(actual,actual.contractId(),new OperationKey("query-arrange-marriage-choices"),
                actual.requiredCapability(),actual.permissionKey(),actual.permissionMode(),actual.wireProfile())));
        assertThrows(IllegalArgumentException.class,()->allowed(copy(actual,actual.contractId(),actual.operation(),
                Optional.of("game.command.other-query"),actual.permissionKey(),actual.permissionMode(),actual.wireProfile())));
        assertThrows(IllegalArgumentException.class,()->allowed(copy(actual,actual.contractId(),actual.operation(),
                actual.requiredCapability(),"game.command.other-query",actual.permissionMode(),actual.wireProfile())));
    }

    @Test void guardianDescriptorCannotBorrowPrivatePermissionDifferentWireOrMissingPureReplay() throws Exception {
        var actual=profile(source("native"),source("profile"));
        assertThrows(IllegalArgumentException.class,()->allowed(copy(actual,actual.contractId(),actual.operation(),Optional.empty(),
                actual.permissionKey(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,actual.wireProfile())));
        assertThrows(IllegalArgumentException.class,()->allowed(copy(actual,actual.contractId(),actual.operation(),actual.requiredCapability(),
                actual.permissionKey(),actual.permissionMode(),ReadContract.WireProfile.G2_PRIVATE_QUERY)));
        var missingReplay=new ReadContract<OrdinaryContext>(actual.contractId(),actual.operation(),actual.requiredCapability(),actual.permissionKey(),
                actual.permissionMode(),actual.wireProfile(),actual.guardMode(),actual.sourceRef(),actual::prepare,actual::decode);
        assertThrows(IllegalArgumentException.class,()->allowed(missingReplay));
    }
}
