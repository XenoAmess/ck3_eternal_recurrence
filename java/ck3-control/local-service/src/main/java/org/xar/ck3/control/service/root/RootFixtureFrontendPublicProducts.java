package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.FrontendFixturePolicy;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.FixtureStartSubmission;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;

/** Only the explicit frozen policy selects its original public tool. Its result remains a pending ACK. */
public final class RootFixtureFrontendPublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private final PreparedFixture fixture;
    private RootFixtureFrontendPublicProducts(RootPublicHandlerProductsFactory.Context context,PreparedFixture fixture) {
        this.context=Objects.requireNonNull(context);this.fixture=Objects.requireNonNull(fixture);
    }
    public record Request(FrontendFixturePolicy.Kind kind) {
        public Request { Objects.requireNonNull(kind); }
    }
    public static void install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        var frozen=context.definitions().frontend().originalDriverImport().frozenProfile();
        var selected=frozen.fixture();
        if(selected.isEmpty())return;
        var fixture=selected.orElseThrow();fixture.verifySources();
        ExactRef source=context.source(RootFixtureFrontendPublicProducts.class);
        context.source(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,FixtureStartSubmission.class);
        var kind=fixture.policy().kind();
        PublicMethod method=PublicMethod.valueOf(fixture.policy().publicTool().substring(4).toUpperCase(java.util.Locale.ROOT));
        var actual=new RootFixtureFrontendPublicProducts(context,fixture);
        registry.register(method,Request.class,FixtureStartSubmission.class,actual::invoke,
                arguments->decode(kind,arguments),value->new RawJson(StrictJson.canonical(value.toJson(),1<<20)),
                new PublicRoutes.Target(RootFixtureFrontendPublicProducts.class.getName(),"invoke",source),PublicRoutes.Status.DELEGATED,
                "explicit original policy, same Root writer/coordinator, one exclusive claim; Start ACK retains verification pending");
    }
    public FixtureStartSubmission invoke(Request request)throws InterruptedException {
        StrictJson.require(request.kind()==fixture.policy().kind(),"fixture request differs from its only configured public tool");
        try {
            fixture.verifySources();
            var deadline=context.clock().instant().plus(context.observationTimeout());
            return context.withFrontend(deadline,(installed,menu,lease)->{
                var runtime=installed.frontend();
                StrictJson.require(runtime.fixture().orElseThrow()==fixture,"public fixture route crossed the identical frozen producer");
                var submitted=runtime.submitFixture(menu,lease,deadline);
                StrictJson.require(submitted.submission().kind()==fixture.policy().kind()&&!submitted.submission().postconditionVerified()
                        &&!submitted.submission().fixtureTargetIdentityProven(),"Start submission must preserve pending business qualification");
                return submitted.submission();
            });
        }catch(IOException unavailable){throw new UncheckedIOException("original fixture submission unavailable; retain its exclusive claim and reconcile without replay",unavailable);}
    }
    public static Request decode(FrontendFixturePolicy.Kind kind,PublicBindings.Arguments arguments) {
        Objects.requireNonNull(kind);Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Missing)return new Request(kind);
        StrictJson.require(arguments instanceof PublicBindings.Value,"explicit null fixture arguments are unavailable");
        StrictJson.object(StrictJson.parse(((PublicBindings.Value)arguments).original().bytes(),65536),Set.of());
        return new Request(kind);
    }
}
