package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeArmyWarWindowEffects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.root.RootReconciliationAuthority;

/** Actual sole writer/transport UNKNOWN -> exact original Attempt/profile binding.
 * Native TOP decoding/replay and employer-only projection use the actual corpus in ArmyWarWindowProducerTest.
 * This finite storage fixture grants no Root physical lease, readiness or live holy-order business result.
 */
final class HolyOrderReconciliationFamilyAdmissionTest {
    @TempDir Path temporary;
    private static final long HOLY_ID=0x81000003L;
    private static final OperationKey HIRE=new OperationKey("hire-holy-order-v1");
    private static final Obj EMPTY=new Obj(Map.of());
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static PlayerHolyOrderContextRead producer(ExactRef source){
        var sources=new PlayerHolyOrderContextRead.Sources(source,source,source,source,source,source,source,source);
        return new PlayerHolyOrderContextRead(new PlanningReadPort(){
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("binding DATA cannot issue a native query");}
        },sources,(original,request)->{throw new AssertionError("descriptor construction grants no live original admission");});
    }
    private static RootReconciliationAuthority.AllowedRead allowed(ReadContract<?> actual){
        return new RootReconciliationAuthority.AllowedRead(actual,EMPTY,RootReconciliationAuthority.QueryKind.HOLY_ORDER_EMPLOYER);
    }
    private static ReadContract<PlayerHolyOrderContextRead.Observation> copy(ReadContract<PlayerHolyOrderContextRead.Observation> actual,
            String id,OperationKey operation,String permission,ReadContract.PermissionMode mode,ReadContract.WireProfile wire){
        return new ReadContract<>(id,operation,actual.requiredCapability(),permission,mode,wire,actual.guardMode(),actual.sourceRef(),actual::prepare,actual::decode,actual::replay);
    }
    @Test void actualCanonicalUnknownRetainsOneHireAndAdmitsOnlyItsOwnIndependentCurrentPlayerProfile() throws Exception {
        var dispatches=new AtomicInteger();
        var preparation=new ActionPorts.PreparationPort(){
            @Override public NativeRequest prepare(ActionCommand command){
                return new NativeRequest(HIRE.value(),Optional.of("game.command.hire-holy-order-v1"),
                        new RawJson(StrictJson.canonical(StrictJson.object().put("holy_order_id",HOLY_ID))));
            }
        };
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(HIRE,"game.command.hire-holy-order-v1",
                (command,attempt,original)->new ActionPorts.Pending("actual employer poststate unavailable",List.of(attempt.guard().nativeEvidence())),
                dispatches::incrementAndGet,Optional.empty(),Optional.empty(),false,Optional.of(preparation));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("canonical"),true,scenario)){
            var template=fixture.command("holy-original");
            ExactRef preflight=fixture.writer.locked(same->fixture.archive.inSession(same,archive->archive.readReferenceOf(fixture.lastNestedRead.get())));
            var call=new ArmyCalls.Hire(PublicMethod.HIRE_HOLY_ORDER_V1,
                    new ArmyCalls.Revision(new ArmyTypes.Present<>(template.before().frame().revision())),new ArmyTypes.HireId(HOLY_ID));
            var arguments=new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.HIRE_HOLY_ORDER_V1,ArmyCallCodec.encode(call),List.of(preflight));
            var expected=NativeArmyWarWindowEffects.expected(template.before(),template.source(),HIRE,arguments.raw());
            var command=new ActionCommand(template.actionId(),template.before(),template.source(),template.sessionId(),HIRE,arguments.encode(),expected,template.claims(),template.deadline());
            var pending=fixture.coordinator.execute(command);assertInstanceOf(ActionState.Unknown.class,pending.state());
            var attempt=ActionTransitions.attempt(pending.state()).orElseThrow();
            var identity=fixture.writer.locked(same->fixture.archive.inSession(same,archive->{
                try {
                var retained=ContinuityActionJournal.receipts(same.head().state(),archive);
                assertTrue(retained.contains(pending));var receipt=archive.receiptReferenceOf(pending);assertEquals(pending,archive.loadReceipt(receipt));
                // Deliberately unqualified Driver DATA; the pure binder cannot turn it into a physical lease.
                var driver=archive.preserveMaterial(raw("{\"role\":\"unqualified-same-driver-data\"}"));
                var evidence=new ReconciliationIdentity.Evidence(attempt.guard().nativeEvidence(),attempt.guard().capabilityEvidence(),
                        archive.preserveMaterial(raw("{\"role\":\"heartbeat-data\"}")),archive.preserveMaterial(raw("{\"role\":\"manifest-data\"}")),
                        driver,archive.preserveMaterial(raw("{\"role\":\"source-data\"}")));
                return ReconciliationIdentity.fromCanonical(pending,command.before(),command.source(),command.sessionId(),attempt.guard().connectionGeneration(),receipt,driver,evidence,Instant.now());
                } catch (java.io.IOException failure) {
                    throw new java.io.UncheckedIOException(failure);
                }
            }));
            var actual=producer(command.source().sourceRef());var profile=actual.reconciliationContract();
            var catalog=new RootReadContractCatalog(List.of(actual.installedRead(command.source().sourceRef()),actual.reconciliationInstalledRead(command.source().sourceRef())),List.of());
            assertTrue(catalog.containsIdentity(profile));assertSame(profile,allowed(profile).contract());
            var query=PlanningReadRequest.newReconciliation(identity,PlayerHolyOrderContextRead.OPERATION,EMPTY,Instant.now().plusSeconds(30));
            PlayerHolyOrderContextRead.requireCanonicalReconciliation(pending,attempt,identity,profile,query);
            var restored=ReconciliationIdentityCodec.decode(ReconciliationIdentityCodec.encode(identity));assertEquals(identity,restored);
            PlayerHolyOrderContextRead.requireCanonicalReconciliation(pending,attempt,restored,profile,
                    PlanningReadRequest.newReconciliation(restored,query.operation(),query.arguments(),query.deadline()));
            assertThrows(IllegalArgumentException.class,()->allowed(actual.contract()));
            assertThrows(IllegalArgumentException.class,()->allowed(copy(profile,PlayerHolyOrderContextRead.CONTRACT_ID,profile.operation(),profile.permissionKey(),profile.permissionMode(),profile.wireProfile())));
            assertThrows(IllegalArgumentException.class,()->allowed(copy(profile,profile.contractId(),new OperationKey("query-war-results-window-v1"),profile.permissionKey(),profile.permissionMode(),profile.wireProfile())));
            assertThrows(IllegalArgumentException.class,()->allowed(copy(profile,profile.contractId(),profile.operation(),"game.command.hire-holy-order-v1",profile.permissionMode(),profile.wireProfile())));
            assertThrows(IllegalArgumentException.class,()->allowed(copy(profile,profile.contractId(),profile.operation(),profile.permissionKey(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,profile.wireProfile())));
            assertThrows(IllegalArgumentException.class,()->allowed(copy(profile,profile.contractId(),profile.operation(),profile.permissionKey(),profile.permissionMode(),ReadContract.WireProfile.EXECUTE_STEP)));
            var noReplay=new ReadContract<PlayerHolyOrderContextRead.Observation>(profile.contractId(),profile.operation(),profile.requiredCapability(),profile.permissionKey(),profile.permissionMode(),profile.wireProfile(),profile.guardMode(),profile.sourceRef(),profile::prepare,profile::decode);
            assertThrows(IllegalArgumentException.class,()->allowed(noReplay));
            var extra=new Obj(Map.of("holy_order_id",new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(BigInteger.valueOf(HOLY_ID))));
            assertThrows(IllegalArgumentException.class,()->new RootReconciliationAuthority.AllowedRead(profile,extra,RootReconciliationAuthority.QueryKind.HOLY_ORDER_EMPLOYER));
            assertThrows(IllegalArgumentException.class,()->PlayerHolyOrderContextRead.requireCanonicalReconciliation(pending,attempt,identity,profile,
                    PlanningReadRequest.newReconciliation(identity,query.operation(),extra,query.deadline())));
            assertThrows(IllegalArgumentException.class,()->PlayerHolyOrderContextRead.requireCanonicalReconciliation(pending,attempt,identity,profile,
                    new PlanningReadRequest(identity.factual(),identity.source(),identity.sessionId(),query.operation(),EMPTY,query.deadline())));
            var otherAttempt=new ActionState.Attempt(attempt.requestId()+"-foreign",attempt.submittedAt(),attempt.guard(),attempt.preparedRequest());
            assertThrows(IllegalArgumentException.class,()->PlayerHolyOrderContextRead.requireCanonicalReconciliation(pending,otherAttempt,identity,profile,query));
            var wrongPrepared=new NativeRequest(HIRE.value(),Optional.of("game.command.hire-holy-order-v1"),raw("{\"holy_order_id\":1}"));
            var driftedAttempt=new ActionState.Attempt(attempt.requestId(),attempt.submittedAt(),attempt.guard(),wrongPrepared);
            var drifted=new ActionReceipt(pending.version(),pending.sequence(),command,pending.bodySha256(),new ActionState.Unknown(Optional.of(driftedAttempt),Optional.empty(),"wrong prepared full ID",List.of()));
            assertThrows(IllegalArgumentException.class,()->PlayerHolyOrderContextRead.requireCanonicalReconciliation(drifted,driftedAttempt,identity,profile,query));
            int nativeReads=fixture.nativeReadWrites();assertEquals(pending,fixture.coordinator.execute(command));
            assertEquals(nativeReads,fixture.nativeReadWrites());assertEquals(1,fixture.nativeActionWrites());assertEquals(1,dispatches.get());
            assertFalse(pending.settled());assertFalse(pending.eligibleAdvance());
        }
    }
}
