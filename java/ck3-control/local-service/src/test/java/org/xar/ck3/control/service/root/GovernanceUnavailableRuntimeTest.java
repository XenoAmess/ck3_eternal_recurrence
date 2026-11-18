package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** No Game or fabricated Root: real software fixture writer/archive and existing production DATA/policy constructors only. */
final class GovernanceUnavailableRuntimeTest {
    @TempDir Path temporary;
    private ExactRef source()throws IOException {
        var path=temporary.resolve("source-data.txt");if(!Files.exists(path))Files.writeString(path,"availability DATA fixture, not a qualified Native producer");
        var file=FileRef.measure(path);return new ExactRef(file.path(),file.bytes(),file.sha256());
    }
    private static ActionWriterIntegrationFixture softwareFixture(Path root)throws IOException {
        var build=ExactCk3Build.CK3_12004;
        var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario(build.executableSha256(),"ck3-1.20.0.4-msvc-x64",
                reviewed->List.of(),request->{throw new AssertionError("no additional software Native READ");},Optional.of(build.version()),Set.of());
        var actual=new ActionWriterIntegrationFixture(root,false,reads);
        try {actual.preserveInitialObservationData();return actual;}
        catch(IOException|RuntimeException failure){try{actual.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}throw failure;}
    }
    private GovernanceRuntimeInstaller.Sources sources(ExactRef ref){
        return new GovernanceRuntimeInstaller.Sources(new GovernanceActionBindings.Sources(ref,ref,ref),ref,ref,ref,ref,ref,ref,ref,List.of(ref),Optional.empty());
    }
    private static PlanningReadPort forbiddenReads(AtomicInteger calls){return new PlanningReadPort(){
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> definition,PlanningReadRequest request){calls.incrementAndGet();throw new AssertionError("unqualified Native read");}
        @Override public <T>PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> definition,PlanningReadRequest request){calls.incrementAndGet();throw new AssertionError("unqualified held Native read");}
    };}
    @Test void recognizedFlorinPreservesRealHistoryRegistrationsButPublicGateRejectsBeforeAnyCallerWork()throws Exception {
        var build=ExactCk3Build.CK3_1210;var ref=source();
        var config=new GovernanceRuntimeInstaller.Config(build.version(),build.executableSha256(),"availability-test",Set.of(),1,3);
        var prepared=GovernanceRuntimeInstaller.prepare(temporary.resolve("original.lock"),sources(ref),config,Clock.systemUTC());
        assertFalse(prepared.nativeQualified());assertEquals(Set.of(DomainBodies.Slot.COUNCIL_CONTINUATION),prepared.domainRegistrations().stream().map(DomainBodies.Registration::slot).collect(Collectors.toSet()));
        var calls=new AtomicInteger();
        assertTrue(prepared.privatePermissions((actual,hello,frame,request)->{calls.incrementAndGet();throw new AssertionError("no qualification");}).isEmpty());
        var failure=assertThrows(PublicServiceFailure.class,()->{GovernanceRuntimeInstaller.requirePublicAvailable(build.version(),build.executableSha256());calls.incrementAndGet();});
        assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.kind());assertEquals(0,calls.get());
        assertThrows(IllegalArgumentException.class,()->GovernanceRuntimeInstaller.requirePublicAvailable("1.21.0.0",build.executableSha256()));
        assertThrows(IllegalArgumentException.class,()->GovernanceRuntimeInstaller.requirePublicAvailable(build.version(),"0".repeat(64)));
    }
    @Test void absentNativeContractsStillReadTheGenuineHeldWriterWithoutInventingClearBodies()throws Exception {
        try(var actual=softwareFixture(temporary.resolve("real-writer"))){
            var request=actual.ready().request();var calls=new AtomicInteger();int nativeReads=actual.nativeReadWrites(),nativeActions=actual.nativeActionWrites();
            var retained=new AtomicReference<GovernanceCollector>();
            actual.writer.locked(same->{
                var head=same.head();var original=same.persistedHead();
                var scope=new GovernanceBorrowedSession(same,actual.writer.originalLockPath(),actual.writer::requireSession);
                var states=new GovernanceStateSupplier(scope,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),
                        expected->new GovernanceObservationSupplier.Unavailable<>("no retained Crown retry proof"));
                var collector=GovernanceOrdinaryRuntimeInstaller.unavailableCollector(forbiddenReads(calls),actual.archive,states,scope);retained.set(collector);
                var durable=assertInstanceOf(GovernanceObservationSupplier.Known.class,collector.durable(request));
                var body=assertInstanceOf(GovernanceObservationSupplier.Durable.class,durable.value());
                assertTrue(body.cadence().isEmpty());assertTrue(body.opening().isEmpty());assertTrue(body.council().isEmpty());assertTrue(body.crown().isEmpty());
                assertEquals(List.of(original),durable.originals());
                assertInstanceOf(GovernanceObservationSupplier.Unavailable.class,collector.lifestyle(request,"wealth_focus",false));
                assertInstanceOf(GovernanceObservationSupplier.Unavailable.class,collector.openingComparison(request));
                assertInstanceOf(GovernanceObservationSupplier.Unavailable.class,collector.coreCouncil(request));
                assertInstanceOf(GovernanceObservationSupplier.Unavailable.class,collector.councilRoot(request));
                assertInstanceOf(GovernanceObservationSupplier.Unavailable.class,collector.crown(request));
                assertEquals(head,same.head());assertEquals(original,same.persistedHead());return null;
            });
            assertThrows(ContractViolationException.class,()->retained.get().durable(request),"the released real writer Session cannot be retained as authority");
            assertEquals(0,calls.get());assertEquals(nativeReads,actual.nativeReadWrites());assertEquals(nativeActions,actual.nativeActionWrites());

        }
    }
    @Test void theFiveConcretePoliciesAndCoreCouncilKeepMissingProducerRejectionWithoutFillingTheOtherStages()throws Exception {
        var implementation=source();
        try(var actual=softwareFixture(temporary.resolve("policies"))){
            var request=actual.ready().request();int readsBefore=actual.nativeReadWrites(),actionsBefore=actual.nativeActionWrites();
            var calls=new AtomicInteger();
            actual.writer.locked(same->{
                var head=same.head();var canonical=same.persistedHead();var lock=actual.writer.originalLockPath();
                var scope=new GovernanceBorrowedSession(same,lock,actual.writer::requireSession);
                var states=new GovernanceStateSupplier(scope,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),
                        expected->new GovernanceObservationSupplier.Unavailable<>("no original Crown proof"));
                var collector=GovernanceOrdinaryRuntimeInstaller.unavailableCollector(forbiddenReads(calls),actual.archive,states,scope);
                // Genuine canonical writer/ActionJournal source. The fixed software frame comes from actual.ready above; no role is minted.
                var stateSource=new CanonicalFinanceStateSource(lock,actual.writer,actual.journal,held->request.before(),held->Optional.empty(),List.of());
                var financeState=new FinanceStatePort(stateSource,stateSource.owningReaders());
                var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(implementation,
                        new FinanceReadContracts.Permission(Optional.of("software.uninstalled."+query.name()),"software.uninstalled."+query.name(),
                                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP)));
                var finance=new OrdinaryFinanceCollector(definitions,forbiddenReads(calls),financeState,()->same);
                var feastInputs=new FeastObservationCollector(finance,collector,actual.archive,(query,current,arguments)->{
                    calls.incrementAndGet();throw new AssertionError("missing governance state must not query Activity");
                },scope);
                assertInstanceOf(GovernanceObservationSupplier.Unavailable.class,feastInputs.state(request));
                var feast=new OrdinaryFeastPolicy(implementation,feastInputs,(operation,current,arguments)->{
                    calls.incrementAndGet();throw new AssertionError("unavailable Feast cannot construct an effect");
                });
                var council=new GovernancePolicies.Council(collector,implementation);
                var policies=GovernanceOrdinaryRuntimeInstaller.ordinaryPolicies(collector,implementation,council,feast);
                assertEquals(Set.of(PlanningStage.OPENING_LIFESTYLE_FOCUS,PlanningStage.LIFESTYLE,PlanningStage.COUNCIL,
                        PlanningStage.CROWN_AUTHORITY,PlanningStage.FEAST),policies.stream().map(OrdinaryPolicy::stage).collect(Collectors.toSet()));
                assertSame(council,policies.get(2));assertSame(feast,policies.get(4));
                var blocked=assertInstanceOf(OrdinaryPolicy.Stop.class,council.evaluateCoreCouncil(request,OrdinaryPolicy.Draft.empty()));
                assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,blocked.stopReason());
                var domain=new RootDomainInstallation("genuine-governance-policies",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                        List.of(),List.of(),List.of(),List.of(),Set.of(),policies,List.of(),List.of(),List.of(),List.of());
                assertEquals(PlanningStage.values().length-5,RootRuntimePipeline.missing(List.of(domain)).size());
                assertThrows(IllegalArgumentException.class,()->RootRuntimePipeline.assemble(List.of(domain)));
                assertThrows(IllegalArgumentException.class,()->RootRuntimePipeline.missing(List.of(domain,domain)));
                assertEquals(head,same.head());assertEquals(canonical,same.persistedHead());return null;
            });
            assertEquals(0,calls.get());assertEquals(readsBefore,actual.nativeReadWrites());assertEquals(actionsBefore,actual.nativeActionWrites());
        }
    }
}
