package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.LifecycleExpectedPostcondition.Operation;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.mcp.CheckpointPublicCodec;
import org.xar.ck3.control.service.mcp.LifecyclePublicCodec;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Original five execute_step lifecycle routes; every mutation remains owned by its actual Root/Core service. */
public final class RootLifecyclePublicStepProducts {
    private RootLifecyclePublicStepProducts() { }
    enum Step {
        SAVE("save-checkpoint"),RESTORE("restore-checkpoint"),DEATH("death-terminal"),
        NEXT("start-next-episode"),CONTINUE("continue-as-reconciled-successor");
        private final OperationKey key;
        Step(String original){key=new OperationKey(original);}
        OperationKey key(){return key;}
    }
    /** Typed protocol seam only. It supplies no Root, source, lifecycle parent or submission authority. */
    @FunctionalInterface interface Call {
        RawJson execute(Step step,RootApplicationSession root,RootInstalledCatalog installed,
                PublicPlanningCodec.ExecuteRequest caller,Instant deadline)throws IOException,InterruptedException;
    }
    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);var context=actual.context();
        var sources=new ArrayList<ExactRef>();
        for(Class<?> type:List.of(RootLifecyclePublicStepProducts.class,RootApplicationSession.class,
                RootSessionAccess.class,RootCheckpointPublicCalls.class,CheckpointPublicCodec.class,
                RootLifecycleRuntimeFactory.class,LifecyclePublicCodec.class))
            sources.add(actual.publicStepSource(Module.LOCAL_SERVICE,type));
        sources.add(actual.publicStepSource(Module.APPLICATION,org.xar.ck3.control.application.session.SessionController.class));
        sources.add(actual.publicStepSource(Module.APPLICATION,org.xar.ck3.control.application.driver.LifecyclePublicResultCodec.class));
        RootPublicStepExecution.OwnerGuard owner=identical->{
            if(identical!=context||actual.context()!=context)
                throw new IOException("lifecycle EXECUTE product belongs to another installed physical Root context");
            actual.remainingDomains().lifecycle().requireContext(context);
        };
        return bind(owner,List.copyOf(sources),(step,root,installed,caller,deadline)->{
            if(installed!=actual||context.actions()!=root||root.writer()!=context.writer()||root.archive()!=context.archive())
                throw new IOException("lifecycle EXECUTE lost its identical actual Root/Core/writer/archive");
            return switch(step){
                case SAVE -> CheckpointPublicCodec.save(root.saveCheckpointPublic(checkpointRequest(caller),deadline));
                // The Core's dedicated private retained route also handles old retired UNKNOWN attempts.
                // Never first ask for ordinary Ready, a new current snapshot, or an ordinary ActionCommand.
                case RESTORE -> CheckpointPublicCodec.restore(context.core().sessionAccess().restoreCheckpointPublic(checkpointRequest(caller),deadline));
                case DEATH,NEXT,CONTINUE -> {
                    var operation=operation(step);
                    yield root.executePublicLifecycle(actual.remainingDomains().lifecycle(),operation,expected(caller),deadline,
                            (receipt,archive,same)->LifecyclePublicCodec.presentStep(operation,receipt,archive));
                }
            };
        });
    }
    static List<RootPublicStepExecution.Product> bind(RootPublicStepExecution.OwnerGuard owner,
            List<ExactRef> sources,Call actual){
        Objects.requireNonNull(owner);sources=List.copyOf(sources);Objects.requireNonNull(actual);
        var result=new ArrayList<RootPublicStepExecution.Product>();
        for(var step:Step.values())result.add(new RootPublicStepExecution.Lifecycle("original-lifecycle:"+step.key().value(),
                step.key()::equals,owner,(root,installed,caller,deadline)->{
                    Objects.requireNonNull(caller);Objects.requireNonNull(deadline);
                    if(!step.key().equals(caller.step())||caller.h2743())
                        throw new IOException("original lifecycle EXECUTE selector changed before its typed owner call");
                    return Objects.requireNonNull(actual.execute(step,root,installed,caller,deadline));
                },sources));
        return List.copyOf(result);
    }
    static RootCheckpointPublicCalls.Request checkpointRequest(PublicPlanningCodec.ExecuteRequest caller){
        Objects.requireNonNull(caller);
        RootCheckpointPublicCalls.RevisionField revision=switch(caller.expectedRevision()){
            case PublicPlanningCodec.RevisionMissing ignored -> new RootCheckpointPublicCalls.MissingRevision();
            case PublicPlanningCodec.RevisionNull ignored -> new RootCheckpointPublicCalls.NullRevision();
            case PublicPlanningCodec.RevisionValue exact -> new RootCheckpointPublicCalls.ExactRevision(exact.value());
        };
        return new RootCheckpointPublicCalls.Request(revision);
    }
    static Optional<java.math.BigInteger> expected(PublicPlanningCodec.ExecuteRequest caller){
        Objects.requireNonNull(caller);return caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue exact
                ?Optional.of(exact.value()):Optional.empty();
    }
    private static Operation operation(Step step){
        return switch(step){case DEATH->Operation.DEATH_TERMINAL;case NEXT->Operation.START_NEXT_EPISODE;
            case CONTINUE->Operation.CONTINUE_SUCCESSOR;default->throw new IllegalArgumentException("checkpoint has its dedicated Root service");};
    }
}
