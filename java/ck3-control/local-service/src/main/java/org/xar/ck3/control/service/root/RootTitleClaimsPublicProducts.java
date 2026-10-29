package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;

/** Original Service routes, registered before Core and resolved against the same installed per-Game product. */
public final class RootTitleClaimsPublicProducts {
    private RootTitleClaimsPublicProducts() { }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        var binder=context.source(RootTitleClaimsPublicProducts.class);
        var selector=context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,InteractionTitleSelectorReads.class);
        var decoder=context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,InteractionReads.class);
        var codec=context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,TitleClaimsPublicCodec.class);
        var runtime=context.source(RootTitleClaimsRuntime.class);
        register(registry,binder,new Handler(context,selector,decoder,codec,runtime)::read);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,OperatorPlayerSwitch.class);context.source(RootSetPlayedCharacterRuntime.class);
        context.source(RootPlayedCharacterPublicContract.class);
        registerOperator(registry,binder,new OperatorHandler(context,selector,decoder,codec,runtime)::execute);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }
    @FunctionalInterface interface CurrentRead {RawJson read(TitleClaimsPublicCodec.Request request)throws InterruptedException;}
    @FunctionalInterface interface CurrentOperator {RawJson execute(OperatorPlayerSwitch.Request request)throws InterruptedException;}
    /** Final invocation port is supplied by the identical mandatory operator Prepared, never by a generic action callback. */
    static void registerOperator(PublicBindings registry,ExactRef source,CurrentOperator current) {
        registry.register(PublicMethod.SET_PLAYER_CHARACTER_V1,OperatorPlayerSwitch.Request.class,RawJson.class,
                request->RootPlayedCharacterPublicContract.requireResult(request,current.execute(request)),
                arguments->OperatorPlayerSwitch.decode(required(arguments)),value->value,
                new PublicRoutes.Target(OperatorHandler.class.getName(),"execute",source),PublicRoutes.Status.IMPLEMENTED,
                "actual exact-build operator source, canonical settlement, independent played-character after and persisted same-run identity");
    }
    /** The software regression replaces only the last call port, leaving the actual original route/codec binding intact. */
    static void register(PublicBindings registry,ExactRef source,CurrentRead current) {
        register(registry,source,current,PublicMethod.QUERY_TITLE_OWN_LAWS_V1,InteractionTitleSelectorReads.Kind.LAWS);
        register(registry,source,current,PublicMethod.QUERY_PLAYER_CLAIMS_V1,InteractionTitleSelectorReads.Kind.CLAIMS);
        register(registry,source,current,PublicMethod.QUERY_TITLE_HOLDER_V1,InteractionTitleSelectorReads.Kind.HOLDER);
        register(registry,source,current,PublicMethod.QUERY_CURRENT_TITLE_APPOINTMENT_V1,InteractionTitleSelectorReads.Kind.APPOINTMENT);
    }
    private static void register(PublicBindings registry,ExactRef source,CurrentRead current,PublicMethod method,InteractionTitleSelectorReads.Kind kind) {
        registry.register(method,TitleClaimsPublicCodec.Request.class,RawJson.class,current::read,
            arguments->TitleClaimsPublicCodec.decode(kind,required(arguments)),value->value,
            new PublicRoutes.Target(Handler.class.getName(),"read",source),PublicRoutes.Status.IMPLEMENTED,
            "same installed arbitrary-selector native read, paused-map source/revision guard and retained original decoder");
    }
    private record Handler(RootPublicHandlerProductsFactory.Context context,ExactRef selector,ExactRef decoder,ExactRef codec,ExactRef runtime) {
        private RawJson read(TitleClaimsPublicCodec.Request request)throws InterruptedException {
            var deadline=context.clock().instant().plus(context.observationTimeout());
            try{return context.withCurrent(root->{
                var installed=context.installed(root);var actual=installed.additionalDomains().driverRegistry().titleClaims();
                actual.requireContext(installed.context());actual.requireOwner(root);actual.requireSources(selector,decoder,codec,runtime);
                return root.executePublicDecision(deadline,(frame,known,same)->new RootApplicationSession.RetainPublicResult<RawJson>(actual.read(same,frame,request,deadline)),
                    (receipt,archive,same)->{throw new IOException("read-only title selector cannot select an action result");});
            });}catch(IOException unavailable){throw new UncheckedIOException("actual title selector unavailable",unavailable);}
        }
    }
    private record OperatorHandler(RootPublicHandlerProductsFactory.Context context,ExactRef selector,ExactRef decoder,ExactRef codec,ExactRef runtime) {
        private RawJson execute(OperatorPlayerSwitch.Request request)throws InterruptedException {
            var deadline=context.clock().instant().plus(context.actionTimeout());
            try{return context.withCurrent(root->{
                var installed=context.installed(root);var actual=installed.additionalDomains().driverRegistry().titleClaims();
                actual.requireContext(installed.context());actual.requireOwner(root);actual.requireSources(selector,decoder,codec,runtime);
                return actual.operatorSwitch().execute(root,request,deadline);
            });}catch(IOException unavailable){throw new UncheckedIOException("actual explicit operator switch unavailable; unknown original action must only reconcile",unavailable);}
        }
    }
    private static RawJson required(PublicBindings.Arguments arguments){if(arguments instanceof PublicBindings.Value value)return value.original();throw new IllegalArgumentException("original title query arguments must be a present non-null object");}
}
