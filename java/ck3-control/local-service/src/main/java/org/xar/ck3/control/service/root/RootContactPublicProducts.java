package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeObservation;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeFailure;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;

/** Pre-Core registration; execution resolves the identical current Root/catalog and performs one held actual observation. */
public final class RootContactPublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private RootContactPublicProducts(RootPublicHandlerProductsFactory.Context actual){context=Objects.requireNonNull(actual);}
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry) {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        try {
            var implementation=context.source(RootContactPublicProducts.class);
            context.source(RootContactRuntime.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ContactScopeReads.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ContactScopePublicCodec.class);
            context.source(RootRuntimeSelectedSources.Module.APPLICATION,ContactScopeObservation.class);
            context.source(RootRuntimeSelectedSources.Module.APPLICATION,ContactScopeFailure.class);
            var actual=new RootContactPublicProducts(context);
            register(registry,implementation,actual::projected,actual::actual);
            return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
        }catch(IOException unavailable) {
            return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of(
                    new RootRuntimePublicCatalog.DefinitionGap("query_projected_contact_scope_v1","actual selected Contact READ source closure unavailable: "+unavailable.getMessage()),
                    new RootRuntimePublicCatalog.DefinitionGap("query_actual_contact_scope","actual selected Contact READ source closure unavailable: "+unavailable.getMessage())));
        }
    }
    /** The identical typed registry producer is exercised without inventing a private pre-Core Context in tests. */
    static void register(PublicBindings registry,ExactRef implementation,
            PublicRoutes.Handler<ContactScopePublicCodec.ProjectedRequest,ContactScopePublicCodec.Response> projected,
            PublicRoutes.Handler<ContactScopePublicCodec.ActualRequest,ContactScopePublicCodec.Response> actual) {
        registry.register(PublicMethod.QUERY_PROJECTED_CONTACT_SCOPE_V1,ContactScopePublicCodec.ProjectedRequest.class,ContactScopePublicCodec.Response.class,
                projected,ContactScopePublicCodec::projected,ContactScopePublicCodec::encode,
                new PublicRoutes.Target(RootContactPublicProducts.class.getName(),"projected",implementation),PublicRoutes.Status.IMPLEMENTED,
                "actual same-frame application-main hypothetical arrival READ; no future arrival or combat permission");
        registry.register(PublicMethod.QUERY_ACTUAL_CONTACT_SCOPE,ContactScopePublicCodec.ActualRequest.class,ContactScopePublicCodec.Response.class,
                actual,ContactScopePublicCodec::actual,ContactScopePublicCodec::encode,
                new PublicRoutes.Target(RootContactPublicProducts.class.getName(),"actual",implementation),PublicRoutes.Status.IMPLEMENTED,
                "actual same-frame current-Province application-main READ; unavailable Native results remain unavailable");
    }
    public ContactScopePublicCodec.Response projected(ContactScopePublicCodec.ProjectedRequest request)throws InterruptedException {
        Objects.requireNonNull(request);Instant deadline=context.clock().instant().plus(context.observationTimeout());
        try {
            return context.withCurrent(root->{
                RootContactRuntime runtime=context.installed(root).contactScopes();
                return root.withPublicObservation(deadline,(frame,known,same)->{
                    var query=new ContactScopeObservation.Projected(request.query());
                    ContactScopeFailure.requireExpectedRevision(query,request.expectedRevision().value(),frame.identity().frame().revision());
                    return capture(query,runtime.reads().collect(same,runtime.context().readCatalog(),ContactScopeReads.Selection.current(query,frame,deadline)));
                });
            });
        }catch(IOException unavailable){throw ContactScopeFailure.fromIo(new ContactScopeObservation.Projected(request.query()),unavailable);}
    }
    public ContactScopePublicCodec.Response actual(ContactScopePublicCodec.ActualRequest request)throws InterruptedException {
        Objects.requireNonNull(request);Instant deadline=context.clock().instant().plus(context.observationTimeout());
        try {
            return context.withCurrent(root->{
                RootContactRuntime runtime=context.installed(root).contactScopes();
                return root.withPublicObservation(deadline,(frame,known,same)->{
                    var query=new ContactScopeObservation.Actual(request.query());
                    ContactScopePublicCodec.expected(request).ifPresent(expected->ContactScopeFailure.requireExpectedRevision(query,expected,frame.identity().frame().revision()));
                    return capture(query,runtime.reads().collect(same,runtime.context().readCatalog(),ContactScopeReads.Selection.current(query,frame,deadline)));
                });
            });
        }catch(IOException unavailable){throw ContactScopeFailure.fromIo(new ContactScopeObservation.Actual(request.query()),unavailable);}
    }
    /** The same actual collector path used by both public methods; failures retain their original typed DATA. */
    static ContactScopePublicCodec.Response capture(ContactScopeObservation.Query query,PlanningReadResult<ContactScopeObservation> actual) {
        Objects.requireNonNull(query);Objects.requireNonNull(actual);
        if(actual instanceof PlanningReadResult.Unavailable<ContactScopeObservation> unavailable)
            throw ContactScopeFailure.from(query,unavailable);
        return ContactScopePublicCodec.capture(query,actual);
    }

}
