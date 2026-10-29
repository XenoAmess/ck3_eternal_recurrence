package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.ritecreation.RiteCreationCodec;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.RootApplicationSession;
import org.xar.ck3.control.service.root.RootSessionAccess;
import org.xar.ck3.control.service.root.RootRiteCreationRuntimeFactory;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.need;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** The original three conditional methods resolve the same installed per-Game Rite runtime once. */
public final class RootMcpRiteCreation {
    @FunctionalInterface public interface Resolver{RootRiteCreationRuntimeFactory.Runtime requireCurrent(RootApplicationSession actual)throws IOException;}
    @FunctionalInterface public interface CurrentPublic{RootMcpRiteCreation require()throws IOException;}
    @FunctionalInterface private interface EndpointCall{RawJson invoke(RootMcpRiteCreation actual)throws InterruptedException;}
    private final RootSessionAccess sessions;private final Resolver resolver;private final Clock clock;private final Duration timeout;
    public RootMcpRiteCreation(RootSessionAccess sessions,Resolver resolver,Clock clock,Duration timeout){this.sessions=Objects.requireNonNull(sessions);this.resolver=Objects.requireNonNull(resolver);this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);need(!timeout.isNegative()&&!timeout.isZero()&&timeout.compareTo(Duration.ofMinutes(2))<=0,"finite positive Rite public deadline required");}
    public RawJson query(Query request)throws InterruptedException{
        var deadline=clock.instant().plus(timeout);
        try{return sessions.withCurrent(root->{var current=resolver.requireCurrent(root);current.requireOwner(root);return root.withPublicObservation(deadline,(frame,known,same)->current.query(same,frame,request,deadline));});}
        catch(IOException unavailable){throw new UncheckedIOException("actual original Rite preview unavailable",unavailable);}
    }
    public RawJson execute(Execute request)throws InterruptedException{
        var deadline=clock.instant().plus(timeout);
        try{return sessions.withCurrent(root->{var current=resolver.requireCurrent(root);current.requireOwner(root);return root.executePublicDecision(deadline,(frame,known,same)->current.prepare(same,frame,request,deadline),(actual,archive,same)->current.result(same,actual,archive));});}
        catch(IOException unavailable){throw new UncheckedIOException("original Rite action unavailable; an existing UNKNOWN is never replayed",unavailable);}
    }
    public RawJson collect(Collect request)throws InterruptedException{
        // Root needs a finite positive owner-lock deadline even when the original polling timeout is zero.
        var deadline=clock.instant().plus(timeout);var pollDeadline=clock.instant().plus(request.timeout());
        try{return sessions.withCurrent(root->{var current=resolver.requireCurrent(root);current.requireOwner(root);return root.withPublicStandaloneRead(deadline,same->current.collect(same,request,pollDeadline));});}
        catch(IOException unavailable){throw new UncheckedIOException("original Rite retained result unavailable; collect never submits",unavailable);}
    }
    public List<McpExecutableDirectory.DirectBinding<?,?>> actualMethods(ExactRef actualThisSource){return suppliedMethods(actualThisSource,()->this);}
    public static List<McpExecutableDirectory.DirectBinding<?,?>> suppliedMethods(ExactRef actualThisSource,CurrentPublic current){
        Objects.requireNonNull(current);return List.of(
            new McpExecutableDirectory.DirectBinding<>("ck3_query_player_rite_creation_action_context_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Query.class,RawJson.class,request->supplied(current,endpoint->endpoint.query(request)),call->RiteCreationCodec.query(call.arguments().objectOrEmpty()),CallResult::fromBusinessJson,target("query",actualThisSource)),
            new McpExecutableDirectory.DirectBinding<>("ck3_execute_player_rite_creation_action_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Execute.class,RawJson.class,request->supplied(current,endpoint->endpoint.execute(request)),call->RiteCreationCodec.execute(call.arguments().objectOrEmpty()),CallResult::fromBusinessJson,target("execute",actualThisSource)),
            new McpExecutableDirectory.DirectBinding<>("ck3_collect_player_rite_creation_action_result_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Collect.class,RawJson.class,request->supplied(current,endpoint->endpoint.collect(request)),call->RiteCreationCodec.collect(call.arguments().objectOrEmpty()),CallResult::fromBusinessJson,target("collect",actualThisSource)));
    }
    private static RawJson supplied(CurrentPublic current,EndpointCall call)throws InterruptedException{try{return call.invoke(Objects.requireNonNull(current.require()));}catch(IOException unavailable){throw new UncheckedIOException("actual current Rite public services unavailable",unavailable);}}
    private static PublicRoutes.Target target(String method,ExactRef source){return new PublicRoutes.Target(RootMcpRiteCreation.class.getName(),method,source);}
}
