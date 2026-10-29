package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.PublicEventResolution;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeActiveEvent;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowCodec;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowService;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;

/** Pre-Core supplied registration. Each call resolves the actual committed current Root and installed event runtime. */
public final class RootEventWindowPublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private RootEventWindowPublicProducts(RootPublicHandlerProductsFactory.Context context) { this.context=Objects.requireNonNull(context); }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,
            PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        ExactRef source=context.source(RootEventWindowPublicProducts.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,EventWindowService.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,EventWindowCodec.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,PublicEventResolution.class);
        context.source(RootRuntimeSelectedSources.Module.CONTRACTS,NativeActiveEvent.class);
        context.source(EventRuntimeInstaller.class);context.source(EventResolutionPublicCodec.class);context.source(EventResolutionPublicResponse.class);
        var actual=new RootEventWindowPublicProducts(context);
        register(registry,actual::query_current_event_window_context_v1,source);
        registerResolver(registry,actual::resolve_active_event,source);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }
    public EventWindowService.Response query_current_event_window_context_v1(EventWindowService.Query query)throws InterruptedException {
        Objects.requireNonNull(query);
        try { return context.withCurrent(root->context.installed(root).remainingDomains().events().eventWindow()
                .query_current_event_window_context_v1(query)); }
        catch(IOException unavailable) { throw new UncheckedIOException("actual current-Root installed event-window query unavailable",unavailable); }
    }
    /** Choice and preparation share the actual collector lease. Root alone dispatches after its freeze unwinds. */
    public EventResolutionPublicResponse.Payload resolve_active_event(EventResolutionPublicCodec.Request request)throws InterruptedException {
        Objects.requireNonNull(request);
        try {
            return context.withCurrent(root->{
                EventRuntimeInstaller sameEvents=context.installed(root).remainingDomains().events();
                return root.executePublicPlanningAction(context.clock().instant().plus(context.actionTimeout()),(actual,frame,driver,same)->{
                    requireOriginalRequest(request,actual,frame);
                    return sameEvents.preparePublicResolution(actual,request.expectedInstance());
                },(receipt,scopedArchive,same)->EventResolutionPublicResponse.capture(receipt,scopedArchive,
                        sameEvents.publicSelectionResult(receipt)));
            });
        } catch(IOException unavailable) {
            throw new UncheckedIOException("public event resolution did not produce a presentable original result; retain its actual outcome and do not resend",unavailable);
        }
    }
    static void requireOriginalRequest(EventResolutionPublicCodec.Request request,PlanningRequest actual,Complete frame) {
        Objects.requireNonNull(request);Objects.requireNonNull(actual);Objects.requireNonNull(frame);
        StrictJson.require(actual.before().equals(frame.identity())&&actual.source().equals(frame.source())&&actual.sessionId().equals(frame.sessionId()),
                "public resolution must retain the actual Root planning frame/source/session");
        request.expectedPublicRevision().ifPresent(expected->StrictJson.require(expected.equals(actual.before().frame().revision()),
                "public event expected_revision differs from the actual planning scope; no option was submitted"));
    }
    /** Same original query service/codec boundary retained from source05. */
    static PublicBindings.TypedBinding<EventWindowService.Query,EventWindowService.Response> register(PublicBindings registry,
            PublicRoutes.Handler<EventWindowService.Query,EventWindowService.Response> current,ExactRef actualSource) {
        Objects.requireNonNull(registry);Objects.requireNonNull(current);Objects.requireNonNull(actualSource);
        return registry.register(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1,EventWindowService.Query.class,EventWindowService.Response.class,
                current,EventWindowService::decode,EventWindowService::encode,
                new PublicRoutes.Target(RootEventWindowPublicProducts.class.getName(),"query_current_event_window_context_v1",actualSource),
                PublicRoutes.Status.DELEGATED,"same actual current Root installed EventWindowService and collector contract; complete native presentation and lossy indicators only");
    }
    static PublicBindings.TypedBinding<EventResolutionPublicCodec.Request,EventResolutionPublicResponse.Payload> registerResolver(PublicBindings registry,
            PublicRoutes.Handler<EventResolutionPublicCodec.Request,EventResolutionPublicResponse.Payload> current,ExactRef actualSource) {
        Objects.requireNonNull(registry);Objects.requireNonNull(current);Objects.requireNonNull(actualSource);
        return registry.register(PublicMethod.RESOLVE_ACTIVE_EVENT,EventResolutionPublicCodec.Request.class,EventResolutionPublicResponse.Payload.class,
                current,EventResolutionPublicCodec::decode,EventResolutionPublicResponse.Payload::original,
                new PublicRoutes.Target(RootEventWindowPublicProducts.class.getName(),"resolve_active_event",actualSource),PublicRoutes.Status.DELEGATED,
                "same actual Root event strategy/read/preparation, dedicated known policy and original best-enabled selection where applicable; unfamiliar first displayed native choice, canonical receipt and separate actual window advancement");
    }
}
