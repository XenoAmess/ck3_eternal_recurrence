package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;
import org.xar.ck3.control.planning.optionalcadence.CadenceJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Closed23 DATA and explicit ordinary policy ports, with no Root/writer/Native authority. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.lifestyle.progress.inputs",matches=".+")
final class OptionalGovernancePrivateSourceTest {
    private static com.fasterxml.jackson.databind.JsonNode index() throws Exception {
        return StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.lifestyle.progress.inputs"))));
    }
    private static byte[] original(String key) throws Exception {
        var ref=ExactRef.fromJson(index().get(key));var raw=Files.readAllBytes(Path.of(ref.path()));
        assertEquals(ref.bytes(),raw.length);assertEquals(ref.sha256(),ActionCodec.sha256(raw));return raw;
    }
    private record Fixture(PlanningRequest request,OrdinaryPolicy.Draft previous,ExactRef reference,OpeningReadProfile.Bindings definitions,CadenceModels.State cadence,Obj council,Obj crown) { }
    private static Fixture fixture() throws Exception {
        // Reuse only the test's pure actual-current DATA preparation; no production private installation is opened.
        var helper=Class.forName("org.xar.ck3.control.application.planning.governance.ReadOnlyLifestyleProgressTest");
        var build=helper.getDeclaredMethod("fixture");build.setAccessible(true);Object actual=build.invoke(null);
        var type=actual.getClass();Object[] fields=new Object[4];String[] names={"request","previous","query","reference"};
        for(int i=0;i<names.length;i++){var method=type.getDeclaredMethod(names[i]);method.setAccessible(true);fields[i]=method.invoke(actual);}
        var request=(PlanningRequest)fields[0];var before=(OrdinaryPolicy.Draft)fields[1];var query=(Obj)fields[2];
        var previous=new OrdinaryPolicy.Draft(before.policy(),before.phase(),before.reason(),before.kind(),before.command(),before.purpose(),before.domain(),
                before.detail().with("lifestyle_readonly_progress",query));
        var dll=ExactRef.fromJson(index().get("actual_dll"));
        var profile=OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,dll).orElseThrow();
        return new Fixture(request,previous,(ExactRef)fields[3],new OpeningReadProfile.Bindings(profile,dll),
                CadenceJson.readState(original("actual_cadence"),request.before().frame().episodeRunId()),
                (Obj)parse(original("actual_council")),(Obj)parse(original("actual_crown")));
    }
    private static DomainState domain(Fixture f,PlanningStage stage,DomainStatus status) {
        return new DomainState(status,Optional.empty(),status==DomainStatus.PENDING?Optional.of(new Obj(Map.of("status",new Text("pending")))):Optional.empty(),
                stage==PlanningStage.COUNCIL?f.council():f.crown());
    }
    private static GovernanceObservationSupplier observed(Fixture f,DomainStatus status,CadenceModels.State cadence,AtomicInteger nativeQueries) {
        return (GovernanceObservationSupplier)Proxy.newProxyInstance(GovernanceObservationSupplier.class.getClassLoader(),new Class<?>[]{GovernanceObservationSupplier.class},(proxy,method,args)->{
            if(method.getName().equals("durable"))return new Known<>(new Durable(f.request().before(),f.request().sessionId(),Optional.of(cadence),Optional.empty(),
                    Optional.of(domain(f,PlanningStage.COUNCIL,status)),Optional.of(domain(f,PlanningStage.CROWN_AUTHORITY,status))),List.of(f.reference()));
            if(method.getName().equals("crownRetryDue"))return new Unavailable<>("no independently qualified due override in this software fixture");
            nativeQueries.incrementAndGet();throw new AssertionError("unexpected private query: "+method.getName());
        });
    }
    private static OrdinaryPolicy original(Fixture f,PlanningStage stage,AtomicInteger calls,RuntimeException failure) {
        return new OrdinaryPolicy() {
            public PlanningStage stage(){return stage;}public ExactRef implementationSource(){return f.reference();}
            public Decision evaluate(PlanningRequest request,Draft previous){calls.incrementAndGet();if(failure!=null)throw failure;return new Keep("original policy retained");}
        };
    }
    @Test void absentSelectedPrivateSourcesOnlyAnnotateAndNeverQueryOrPublishCadence() throws Exception {
        var f=fixture();var nativeQueries=new AtomicInteger();var observed=observed(f,DomainStatus.KNOWN_CLEAR,f.cadence(),nativeQueries);
        for(var stage:List.of(PlanningStage.COUNCIL,PlanningStage.CROWN_AUTHORITY)) {
            var calls=new AtomicInteger();var original=original(f,stage,calls,null);
            var selected=GovernanceOrdinaryRuntimeInstaller.selectedOptionalSource(original,observed,false,Optional.of(f.definitions()));
            var result=(OrdinaryPolicy.Replace)selected.evaluate(f.request(),f.previous());var plan=result.draft();
            assertEquals(f.previous().policy(),plan.policy());assertEquals(f.previous().phase(),plan.phase());assertEquals(f.previous().reason(),plan.reason());
            assertEquals(f.previous().kind(),plan.kind());assertEquals(f.previous().command(),plan.command());assertEquals(f.previous().purpose(),plan.purpose());assertEquals(f.previous().domain(),plan.domain());
            var unavailable=object(plan.detail().get(stage==PlanningStage.COUNCIL?"council_selected_private_source":"crown_selected_private_source"),"unavailable");
            assertEquals(new Text("unavailable"),unavailable.get("status"));
            for(String key:List.of("private_source_installed","query_performed","review_complete","cadence_published","action_authority"))assertEquals(new Bool(false),unavailable.get(key));
            assertEquals(f.previous().detail().members().size()+1,plan.detail().members().size());assertEquals(0,calls.get());assertEquals(original.implementationSource(),selected.implementationSource());
        }
        assertEquals(0,nativeQueries.get());
    }
    @Test void installedPrivateSourceKeepsTheIdenticalOriginalObjectAndItsOriginalFailure() throws Exception {
        var f=fixture();var calls=new AtomicInteger();var failure=new IllegalStateException("original source error");
        var unused=(GovernanceObservationSupplier)Proxy.newProxyInstance(GovernanceObservationSupplier.class.getClassLoader(),new Class<?>[]{GovernanceObservationSupplier.class},
                (proxy,method,args)->{throw new AssertionError("source-present selection must not touch new ports");});
        var original=original(f,PlanningStage.COUNCIL,calls,failure);
        var selected=GovernanceOrdinaryRuntimeInstaller.selectedOptionalSource(original,unused,true,Optional.of(f.definitions()));
        assertSame(original,selected);assertSame(failure,assertThrows(IllegalStateException.class,()->selected.evaluate(f.request(),f.previous())));assertEquals(1,calls.get());
        assertSame(original,GovernanceOrdinaryRuntimeInstaller.selectedOptionalSource(original,unused,false,Optional.empty()));
        var other=original(f,PlanningStage.LIFESTYLE,new AtomicInteger(),null);
        assertSame(other,GovernanceOrdinaryRuntimeInstaller.selectedOptionalSource(other,unused,false,Optional.of(f.definitions())));
    }
    @Test void pendingUnknownDeferredAndUnqualifiedMarkersKeepTheirOriginalStrictPaths() throws Exception {
        var f=fixture();var nativeQueries=new AtomicInteger();
        for(var status:List.of(DomainStatus.PENDING,DomainStatus.UNKNOWN))for(var stage:List.of(PlanningStage.COUNCIL,PlanningStage.CROWN_AUTHORITY)) {
            var observed=observed(f,status,f.cadence(),nativeQueries);
            OrdinaryPolicy original=stage==PlanningStage.COUNCIL?new GovernancePolicies.Council(observed,f.reference()):new GovernancePolicies.Crown(observed,f.reference());
            var selected=GovernanceOrdinaryRuntimeInstaller.selectedOptionalSource(original,observed,false,Optional.of(f.definitions()));
            assertInstanceOf(OrdinaryPolicy.Wait.class,selected.evaluate(f.request(),f.previous()));
        }
        for(var stage:List.of(PlanningStage.COUNCIL,PlanningStage.CROWN_AUTHORITY)) {
            var kind=stage==PlanningStage.COUNCIL?CadenceModels.Domain.COUNCIL:CadenceModels.Domain.CROWN;
            var later=f.cadence().with(kind,new CadenceModels.Row(0,Optional.of(f.request().before().frame().identity().dateRaw().add(BigInteger.ONE)),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty()));
            var observed=observed(f,DomainStatus.KNOWN_CLEAR,later,nativeQueries);
            OrdinaryPolicy original=stage==PlanningStage.COUNCIL?new GovernancePolicies.Council(observed,f.reference()):new GovernancePolicies.Crown(observed,f.reference());
            assertInstanceOf(OrdinaryPolicy.Keep.class,GovernanceOrdinaryRuntimeInstaller.selectedOptionalSource(original,observed,false,Optional.of(f.definitions())).evaluate(f.request(),f.previous()));
        }
        var observed=observed(f,DomainStatus.KNOWN_CLEAR,f.cadence(),nativeQueries);var calls=new AtomicInteger();
        var original=original(f,PlanningStage.COUNCIL,calls,null);var selected=GovernanceOrdinaryRuntimeInstaller.selectedOptionalSource(original,observed,false,Optional.of(f.definitions()));
        Obj query=object(f.previous().detail().get("lifestyle_readonly_progress"),"query");
        Obj snapshot=object(query.get("snapshot"),"snapshot");
        for(Obj invalid:List.of(new Obj(Map.of()),query.with("snapshot",snapshot.with("native_revision",new IntegerValue(BigInteger.valueOf(999)))),
                query.with("snapshot",snapshot.with("current_lifestyle_progress",object(snapshot.get("current_lifestyle_progress"),"progress").with("unspent_perk_points",new IntegerValue(BigInteger.ONE)))))) {
            var plan=new OrdinaryPolicy.Draft(f.previous().policy(),f.previous().phase(),f.previous().reason(),f.previous().kind(),f.previous().command(),f.previous().purpose(),f.previous().domain(),f.previous().detail().with("lifestyle_readonly_progress",invalid));
            assertInstanceOf(OrdinaryPolicy.Keep.class,selected.evaluate(f.request(),plan));
        }
        assertEquals(3,calls.get());assertEquals(0,nativeQueries.get());
    }
}
