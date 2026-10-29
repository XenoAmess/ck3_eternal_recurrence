package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubBusinessStateRead;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootAubRuntimeFactory;
import org.xar.ck3.control.service.root.RootApplicationSession;
import org.xar.ck3.control.service.root.RootSessionAccess;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Four original AUB public methods. The current Game is resolved once per call; Root alone submits. */
public final class RootMcpAubOperations {
    @FunctionalInterface public interface Resolver { RootAubRuntimeFactory.Runtime requireCurrent(RootApplicationSession actualCurrent)throws IOException; }
    public record Query(RootMcpAubReads.Revision revision) { public Query { Objects.requireNonNull(revision); } }
    public record Selection(RootMcpAubReads.Revision revision,Select mutation) { public Selection { Objects.requireNonNull(revision);Objects.requireNonNull(mutation); } }
    public record Confirmation(RootMcpAubReads.Revision revision,Confirm mutation) { public Confirmation { Objects.requireNonNull(revision);Objects.requireNonNull(mutation); } }
    private final RootSessionAccess sessions;private final Resolver resolver;private final Clock clock;private final Duration timeout;
    public RootMcpAubOperations(RootSessionAccess sessions,Resolver resolver,Clock clock,Duration timeout) {
        this.sessions=Objects.requireNonNull(sessions);this.resolver=Objects.requireNonNull(resolver);this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        McpJson.require(!timeout.isZero()&&!timeout.isNegative()&&timeout.compareTo(Duration.ofMinutes(2))<=0,"finite positive AUB public timeout required");
    }
    public RawJson business(Query request)throws InterruptedException {
        try{return sessions.withCurrent(root->{var current=Objects.requireNonNull(resolver.requireCurrent(root));current.requireOwner(root);
            var read=root.readCurrent(current.registration().business().contract(),request.revision().expected(),empty(),clock.instant().plus(timeout));
            if(read instanceof PlanningReadResult.Known<AubBusinessStateRead.State> known)return AubBusinessStateRead.normalizedForPublic(known.value());
            throw new IOException("actual original AUB business observation unavailable");});}
        catch(IOException unavailable){throw new UncheckedIOException("actual Root AUB business observation unavailable",unavailable);}
    }
    public RawJson options(Query request)throws InterruptedException {
        try{return sessions.withCurrent(root->{var current=Objects.requireNonNull(resolver.requireCurrent(root));current.requireOwner(root);
            var read=root.readCurrent(current.registration().options(),request.revision().expected(),empty(),clock.instant().plus(timeout));
            if(read instanceof PlanningReadResult.Known<Options> known)return AubOperations.publicOptions(known.value());
            throw new IOException("actual original AUB policy observation unavailable");});}
        catch(IOException unavailable){throw new UncheckedIOException("actual Root AUB policy observation unavailable",unavailable);}
    }
    public RawJson select(Selection request)throws InterruptedException {return mutate(request.revision(),request.mutation());}
    public RawJson confirm(Confirmation request)throws InterruptedException {return mutate(request.revision(),request.mutation());}
    private RawJson mutate(RootMcpAubReads.Revision revision,Mutation mutation)throws InterruptedException {
        var deadline=clock.instant().plus(timeout);
        try{return sessions.withCurrent(root->{var current=Objects.requireNonNull(resolver.requireCurrent(root));current.requireOwner(root);
            return root.executePublicAction(deadline,(frame,known,same)->current.prepare(same,frame,mutation,revision.expected(),deadline),
                    (actual,scoped,same)->current.result(actual,scoped));});}
        catch(IOException unavailable){throw new UncheckedIOException("original Root AUB action unavailable; an existing intent must never be resubmitted",unavailable);}
    }
    /** The sole total public catalog installs exactly this four-member family, replacing the older business-only binding. */
    public List<McpExecutableDirectory.DirectBinding<?,?>> actualMethods(ExactRef actualThisSource) {
        return List.of(
                new McpExecutableDirectory.DirectBinding<>("ck3_query_aub_business_state_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Query.class,RawJson.class,this::business,call->query(call.arguments()),CallResult::fromBusinessJson,target("business",actualThisSource)),
                new McpExecutableDirectory.DirectBinding<>("ck3_query_aub_policy_options_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Query.class,RawJson.class,this::options,call->query(call.arguments()),CallResult::fromBusinessJson,target("options",actualThisSource)),
                new McpExecutableDirectory.DirectBinding<>("ck3_select_aub_policy_option_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Selection.class,RawJson.class,this::select,call->selection(call.arguments()),CallResult::fromBusinessJson,target("select",actualThisSource)),
                new McpExecutableDirectory.DirectBinding<>("ck3_confirm_aub_policy_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Confirmation.class,RawJson.class,this::confirm,call->confirmation(call.arguments()),CallResult::fromBusinessJson,target("confirm",actualThisSource)));
    }
    private static PublicRoutes.Target target(String method,ExactRef source){return new PublicRoutes.Target(RootMcpAubOperations.class.getName(),method,source);}
    public static Query query(Arguments args){ObjectNode row=fields(args,Set.of("expected_revision"),Set.of());return new Query(revision(row));}
    public static Selection selection(Arguments args){ObjectNode row=fields(args,Set.of("expected_revision","expected_selected_key","desired_key"),Set.of("expected_selected_key","desired_key"));return new Selection(revision(row),new Select(key(row,"expected_selected_key"),key(row,"desired_key")));}
    public static Confirmation confirmation(Arguments args){ObjectNode row=fields(args,Set.of("expected_revision","expected_selected_key"),Set.of("expected_selected_key"));return new Confirmation(revision(row),new Confirm(key(row,"expected_selected_key")));}
    private static ObjectNode fields(Arguments args,Set<String> allowed,Set<String> required){ObjectNode row=McpJson.object(McpJson.parse(args.objectOrEmpty().bytes()));McpJson.publicNumbers(row);McpJson.fields(row,allowed,required);return row;}
    private static PolicyKey key(ObjectNode row,String key){var value=row.get(key);McpJson.require(value!=null&&value.isTextual(),"exact AUB semantic policy key required");return PolicyKey.parse(value.textValue());}
    private static RootMcpAubReads.Revision revision(ObjectNode row){return RootMcpAubReads.revision(row);}

    private static OpportunityJson.Obj empty(){return new OpportunityJson.Obj(java.util.Map.of());}
}
