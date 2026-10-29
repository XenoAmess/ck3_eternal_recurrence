package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Predicate;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionIds;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec;
import org.xar.ck3.control.application.driver.DriverActionHistoryState;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;


import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.CheckpointPublicCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/**
 * The original execute_step facade, with source-owned typed step products. Read products keep their
 * actual READ result; action products prepare through their installed owner and submit once through
 * Root's coordinator. A canonical receipt is never substituted for the driver's public result.
 */
public final class RootPublicStepExecution {
    private RootPublicStepExecution() { }

    @FunctionalInterface public interface OwnerGuard {
        void requireContext(RootRuntimeContext identical)throws IOException;
    }
    @FunctionalInterface public interface ReadWork {
        RawJson read(PlanningRequest original,Complete frame,Known known,Session same,
                PublicPlanningCodec.ExecuteRequest caller,OutcomeArchive archive)throws IOException;
    }
    @FunctionalInterface public interface ActionPreparation {
        ActionCommand prepare(PlanningRequest original,Complete frame,Known known,Session same,
                PublicPlanningCodec.ExecuteRequest caller)throws IOException;
    }
    @FunctionalInterface public interface ActionResult {
        RawJson present(ActionReceipt actual,OutcomeArchive archive,Session same,
                PublicPlanningCodec.ExecuteRequest caller)throws IOException;
    }
    /** Terminal/restore paths retain their actual typed Core routes, without an ordinary-frame fiction. */
    @FunctionalInterface public interface LifecycleWork {
        RawJson execute(RootApplicationSession root,RootInstalledCatalog installed,PublicPlanningCodec.ExecuteRequest caller,
                Instant deadline)throws IOException,InterruptedException;
    }
    public sealed interface Product permits Read,Action,Lifecycle,OwnedAction {
        String id();Predicate<OperationKey> selector();OwnerGuard owner();List<ExactRef> sources();
        default boolean matches(OperationKey step){return selector().test(Objects.requireNonNull(step));}
        default void requireContext(RootRuntimeContext context)throws IOException{owner().requireContext(context);}
    }
    public enum ReadValidation { CENTRAL_BEFORE,OWNER_ORDERED }
    public record Read(String id,Predicate<OperationKey> selector,OwnerGuard owner,ReadWork work,
            List<ExactRef> sources,ReadValidation validation) implements Product {
        public Read {sources=check(id,selector,owner,sources);Objects.requireNonNull(work);Objects.requireNonNull(validation);}
        public Read(String id,Predicate<OperationKey> selector,OwnerGuard owner,ReadWork work,List<ExactRef> sources) {
            this(id,selector,owner,work,sources,ReadValidation.CENTRAL_BEFORE);
        }
    }
    public enum ActionValidation { CENTRAL_BEFORE,OWNER_ORDERED }
    public record Action(String id,Predicate<OperationKey> selector,OwnerGuard owner,ActionPreparation preparation,
            ActionResult result,List<ExactRef> sources,ActionValidation validation) implements Product {
        public Action {sources=check(id,selector,owner,sources);Objects.requireNonNull(preparation);Objects.requireNonNull(result);Objects.requireNonNull(validation);}
        public Action(String id,Predicate<OperationKey> selector,OwnerGuard owner,ActionPreparation preparation,ActionResult result,List<ExactRef> sources) {
            this(id,selector,owner,preparation,result,sources,ActionValidation.CENTRAL_BEFORE);
        }
    }
    public record Lifecycle(String id,Predicate<OperationKey> selector,OwnerGuard owner,LifecycleWork work,
            List<ExactRef> sources) implements Product {
        public Lifecycle {sources=check(id,selector,owner,sources);Objects.requireNonNull(work);}
    }
    /** Original stateful/conditional routes use their typed Root decision/control API, including
     * canonical UNKNOWN retention. This callback grants no new native preparation or retry power. */
    public record OwnedAction(String id,Predicate<OperationKey> selector,OwnerGuard owner,LifecycleWork work,
            List<ExactRef> sources) implements Product {
        public OwnedAction {sources=check(id,selector,owner,sources);Objects.requireNonNull(work);}
    }
    /** Immutable actual installed roster. Source availability is distinct from a successful Game effect. */
    public static final class Catalog {
        private final RootRuntimeContext context;private final List<Product> products;
        private RootPublicStepFailureOriginals failures;
        public Catalog(RootRuntimeContext actual,List<Product> actualProducts) {
            context=Objects.requireNonNull(actual);products=List.copyOf(actualProducts);
            StrictJson.require(!products.isEmpty()&&products.size()<=1024,"nonempty finite actual public step products required");
            var ids=new HashSet<String>();
            for(Product product:products)StrictJson.require(ids.add(product.id()),"duplicate installed public step product: "+product.id());
        }
        public RootRuntimeContext context(){return context;}
        public List<Product> products(){return products;}
        synchronized RootPublicStepFailureOriginals failureSource(RootInstalledCatalog actual)throws IOException {
            StrictJson.require(actual.context()==context&&actual.publicSteps()==this,"failure issuer must use this identical installed catalog");
            if(failures==null)failures=new RootPublicStepFailureOriginals(actual);return failures;
        }
        public Product require(PublicPlanningCodec.ExecuteRequest caller)throws IOException {
            Objects.requireNonNull(caller);requireGenericFacade(caller.step());
            Product selected=select(products,caller);
            selected.requireContext(context);return selected;
        }
    }

    /** One public decision recipe; it grants no reservation, preparation or replay permission. */
    public static String actionId(PlanningRequest original,PublicPlanningCodec.ExecuteRequest caller) {
        Objects.requireNonNull(original);Objects.requireNonNull(caller);caller.requireCurrent(original);
        return ActionIds.forDecision(original.sessionId(),original.before(),
                "public-execute-step:"+ActionCodec.sha256(PublicPlanningCodec.encodeExecute(caller).bytes()));
    }
    @FunctionalInterface public interface OriginalProjection {
        RawJson project(PublicPlanningCodec.ExecuteRequest caller,RawJson originalNumeric)throws IOException;
    }
    public record LegacyOriginal(DriverActionHistoryCodec.Recording recording,Optional<RawJson> result,
            Optional<String> error,ExactRef originalSource) {
        public LegacyOriginal {Objects.requireNonNull(recording);Objects.requireNonNull(result);Objects.requireNonNull(error);Objects.requireNonNull(originalSource);}
    }
    /** Read-only canonical ACTION publication replay. A source-shaped artifact alone is insufficient. */
    public static LegacyOriginal requireLegacyOriginal(ActionReceipt actual,OutcomeArchive archive,Session same,
            PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(archive);Objects.requireNonNull(same);Objects.requireNonNull(caller);
        StrictJson.require(actual.command().operation().equals(caller.step()),"public original result crossed the caller's step");
        var committed=DriverActionHistoryState.findCommittedCoverage(same,actual,archive)
                .orElseThrow(()->new IOException("actual completed action has no original canonical history publication"));
        var source=DriverActionHistoryCodec.decode(archive.loadMaterial(committed.originalSource()));
        DriverActionHistoryCodec.requireCanonicalMembership(same,actual,source,archive);
        DriverActionHistoryCodec.requireSource(actual,source,archive);
        if(!(source.material() instanceof DriverActionHistoryCodec.Legacy legacy))
            throw new IOException("this original interface needs its actual source-owned result formatter, not a legacy result alias");
        Optional<RawJson> result=legacy.result().map(archive::loadMaterial);
        return new LegacyOriginal(legacy.recording(),result,legacy.error(),committed.originalSource());
    }
    /** The owner supplies its exact numeric-role encoder; no recursive name-based uint64 conversion. */
    public static RawJson legacyResult(ActionReceipt actual,OutcomeArchive archive,Session same,
            PublicPlanningCodec.ExecuteRequest caller,OriginalProjection projection)throws IOException {
        LegacyOriginal original=requireLegacyOriginal(actual,archive,same,caller);
        if(original.recording()==DriverActionHistoryCodec.Recording.RAISED)throwRecorded(original);
        return object(Objects.requireNonNull(projection).project(caller,original.result().orElseThrow()));
    }
    private static void throwRecorded(LegacyOriginal original)throws IOException {
        String error=original.error().orElseThrow();int delimiter=error.indexOf(": ");
        if(delimiter>0) {
            String exactClass=error.substring(0,delimiter),message=error.substring(delimiter+2);
            for(var kind:PublicServiceFailure.Kind.values())if(kind.pythonClassName().equals(exactClass))
                throw new PublicServiceFailure(kind,message,Optional.of(original.originalSource()));
        }
        // This preserves the archived exception as a cause; the shared MCP boundary must explicitly
        // admit any additional original class before it can claim exact public fault parity.
        throw new IOException("unmapped original public exception: "+error);
    }

    /** Pure selection only. Context/source qualification occurs on the actual installed Catalog. */
    static Product select(List<Product> products,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        requireGenericFacade(caller.step());
        List<Product> matches=products.stream().filter(product->product.matches(caller.step())).toList();
        if(matches.isEmpty()) {
            if(caller.h2743())throw new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                    "H2743 native read-only reader unavailable",Optional.empty());
            throw new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,
                    "no installed typed original producer for step "+caller.step().value(),Optional.empty());
        }
        if(matches.size()!=1)throw new IOException("ambiguous installed original step producers: "+caller.step().value());
        Product selected=matches.getFirst();
        if(caller.h2743()&&!(selected instanceof Read))
            throw new IOException("H2743 is an original before-frame READ; no action product may replace it");
        return selected;
    }

    public static RawJson execute(RootApplicationSession root,RootInstalledCatalog installed,
            PublicPlanningCodec.ExecuteRequest caller,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(root);Objects.requireNonNull(installed);Objects.requireNonNull(caller);Objects.requireNonNull(deadline);
        // These original Service-level rejections never enter NativeHeadlessGameplayDriver.execute_step.
        requireGenericFacade(caller.step());
        Catalog catalog=installed.publicSteps();RootRuntimeContext context=installed.context();
        StrictJson.require(catalog.context()==context&&context.actions()==root&&root.writer()==context.writer()
                &&root.archive()==context.archive(),"public step must use its identical installed physical Root/coordinator/writer");
        Product product;
        try {product=catalog.require(caller);}
        catch(PublicServiceFailure noProduct) {
            if(noProduct.kind()!=PublicServiceFailure.Kind.UNSUPPORTED_STEP
                    ||!DriverPublicExecuteFailureRowProducer.fixedUnsupportedHire(caller.step().value()))throw noProduct;
            var failures=catalog.failureSource(installed);context.readHistoryPublisher().bindPublicExecuteFailureSource(failures);context.readHistoryPublisher().bindEarlyExecuteFailureSource(failures);
            try(var originalCall=failures.enter(root,Optional.empty(),caller,deadline)) {
                return failures.executeUnsupportedHire();
            }
        }
        var failures=catalog.failureSource(installed);context.readHistoryPublisher().bindPublicExecuteFailureSource(failures);context.readHistoryPublisher().bindEarlyExecuteFailureSource(failures);
        try(var originalCall=failures.enter(root,Optional.of(product),caller,deadline)) {
        if(product instanceof Lifecycle lifecycle) {
            lifecycle.requireContext(context);
            // The actual typed Core lifecycle route owns its transition lock and can retire this
            // physical Root on RESTORE. The old Root must not be re-entered after that transition.
            RawJson result=object(lifecycle.work().execute(root,installed,caller,deadline));
            return result;
        }
        if(product instanceof OwnedAction owned) {
            return root.withPublicSuppliedAction(deadline,()->{
                owned.requireContext(context);
                RawJson result=object(owned.work().execute(root,installed,caller,deadline));
                owned.requireContext(context);return result;
            });
        }
        if(product instanceof Read)return failures.executeRead();
        return failures.executeAction();
        }
    }
    /** Dedicated exact restore entry. Core owns the original SavedMaterial/private attempt, including
     * query-only continuation of a retired UNKNOWN. Resolving an ordinary current Root first is wrong. */
    public static RawJson executeRetainedRestore(RootPublicHandlerProductsFactory.Context context,
            PublicPlanningCodec.ExecuteRequest caller,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(context);Objects.requireNonNull(deadline);
        return CheckpointPublicCodec.restore(context.restoreCheckpointPublic(retainedRestoreRequest(caller),deadline));
    }
    static RootCheckpointPublicCalls.Request retainedRestoreRequest(PublicPlanningCodec.ExecuteRequest caller) {
        Objects.requireNonNull(caller);
        StrictJson.require(caller.step().value().equals("restore-checkpoint")&&!caller.h2743()
                &&!(caller.expectedH2743Frame() instanceof PublicPlanningCodec.FrameValue),
                "only the original restore-checkpoint caller may enter the retained Core restore route");
        return RootLifecyclePublicStepProducts.checkpointRequest(caller);
    }

    private static RawJson object(RawJson value) {
        Objects.requireNonNull(value);value.objectFieldNames();return value;
    }
    public static void requireGenericFacade(OperationKey step) {
        if(step.value().equals("center-map-on-landed-title-v1"))
            throw new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,
                    "title-map navigation requires its typed MCP facade",Optional.empty());
        if(step.value().equals("navigate-ingame-ui-v1")||step.value().equals("query-ingame-ui-window-v1"))
            throw new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,
                    "ingame UI requires its explicit typed MCP facade",Optional.empty());
    }
    private static List<ExactRef> check(String id,Predicate<OperationKey> selector,OwnerGuard owner,List<ExactRef> sources) {
        StrictJson.text(id);Objects.requireNonNull(selector);Objects.requireNonNull(owner);sources=List.copyOf(sources);
        StrictJson.require(!sources.isEmpty()&&sources.size()<=org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.MAX_PRODUCER_SOURCES
                &&sources.stream().allMatch(ref->ref.bytes()>0),"finite actual step producer metadata required");
        return List.copyOf(new java.util.LinkedHashSet<>(sources));
    }
}
