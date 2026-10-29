package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.time.Instant;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** The sole SAVE service is constructed by Core.stage and bound into this earlier frozen inventory once. */
public final class RootSaveRuntime {
    public static final OperationKey OPERATION=new OperationKey("save-checkpoint");
    public record Sources(ExactRef preparation,ExactRef poststate,ExactRef archivedReplay) {
        public Sources {for(ExactRef ref:List.of(preparation,poststate,archivedReplay))
            StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"actual SAVE preparation, poststate and archive sources required");}
    }
    private final RootRuntimeContext context;
    private final Sources sources;
    private final RootDomainInstallation installation;
    private final RootExecutableBindings.ActionBinding action;
    private CheckpointService checkpoints;
    private CanonicalSaveReceiptVerifier verifier;
    private NativeRecordedEvidenceVerifier.Binding originalReplay;
    public RootSaveRuntime(RootRuntimeContext context,Sources sources) {
        this.context=Objects.requireNonNull(context);this.sources=Objects.requireNonNull(sources);
        var effect=NativeEffectRegistry.Binding.existing(OPERATION,sources.preparation(),this::prepare,this::observe);
        action=new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("game.command.save-checkpoint"),sources.poststate());
        var archived=new NativeRecordedEvidenceVerifier.Binding(OPERATION,sources.archivedReplay(),this::replay);
        installation=new RootDomainInstallation("canonical-physical-save",List.of(),List.of(),List.of(),List.of(action),List.of(),
                List.of(archived),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),
                List.of(),List.of(),List.of());
    }
    public RootDomainInstallation installation(){return installation;}
    public RootExecutableBindings.ActionBinding action(){return action;}
    /** The public adapter uses the same current Root and its already bound physical checkpoint service. */
    public RootCheckpointPublicCalls.SaveCall publicSave(RootApplicationSession root,
            RootCheckpointPublicCalls.Request request,Instant deadline)throws IOException,InterruptedException {
        requirePublicOwner(root,deadline);Objects.requireNonNull(request);
        return root.saveCheckpointPublic(request,deadline);
    }
    public RootCheckpointPublicCalls.RestoreCall publicRestore(RootApplicationSession root,
            RootCheckpointPublicCalls.Request request,Instant deadline)throws IOException,InterruptedException {
        requirePublicOwner(root,deadline);Objects.requireNonNull(request);
        return root.restoreCheckpointPublic(request,deadline);
    }
    private void requirePublicOwner(RootApplicationSession root,Instant deadline)throws IOException {
        Objects.requireNonNull(root);Objects.requireNonNull(deadline);context.requireCurrent(deadline);
        if(root.isRetired()||context.core().sessionAccess().current()!=root||context.actions()!=root
                ||root.driver()!=context.adopted()||root.writer()!=context.writer()||root.archive()!=context.archive()
                ||root.checkpoints()!=actualService()||!root.identity().game().equals(context.game().generation())
                ||!root.identity().machineId().equals(context.game().machineId())
                ||!root.identity().sessionId().equals(context.game().sessionId()))
            throw new IOException("public checkpoint call requires this exact admitted Root/Driver/Game/checkpoint service");
    }
    public synchronized void bind(RootApplicationAssembly.Staged actual)throws IOException {
        Objects.requireNonNull(actual);
        StrictJson.require(checkpoints==null&&verifier==null&&actual.driver()==context.adopted()
                &&actual.planningReads()==context.reads(),"SAVE must bind this exact once-created physical Game stage");
        context.game().verify();
        context.game().launchPlan().sources().requireLoadedClass(RootSaveRuntime.class);
        context.game().launchPlan().sources().requireLoadedClass(CheckpointService.class);
        context.game().launchPlan().sources().requireLoadedClass(CanonicalSaveReceiptVerifier.class);
        checkpoints=actual.checkpoints();verifier=actual.saveReceiptVerifier();
        originalReplay=verifier.archivedBinding(sources.archivedReplay(),context::borrowedSession);
    }
    private synchronized CheckpointService actualService() {
        StrictJson.require(checkpoints!=null&&verifier!=null,"actual stage SAVE service and canonical verifier are not yet bound");
        return checkpoints;
    }
    private NativeRequest prepare(ActionCommand command) {
        actualService();requireCommand(command,true);
        return new NativeRequest(OPERATION.value(),Optional.of("game.command.save-checkpoint"),new RawJson(new byte[]{'{','}'}));
    }
    private ActionPorts.PostconditionResult observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        requireCommand(command,true);
        return actualService().observe(command,attempt,dispatch);
    }
    private void replay(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ActionReceipt actual,
            ActionPorts.OutcomeArchive archive) {
        actualService();requireCommand(actual.command(),false);NativeRecordedEvidenceVerifier.Binding original;
        synchronized(this){original=originalReplay;}
        original.verifier().verify(head,actual,archive);
    }
    private void requireCommand(ActionCommand command,boolean current) {
        Objects.requireNonNull(command);
        StrictJson.require(command.operation().equals(OPERATION)&&command.origin() instanceof CommandOrigin.Gameplay
                &&command.arguments().members().isEmpty()
                &&command.expected().observerSchema().equals(CheckpointRequestFactory.OBSERVER_SCHEMA),
                "SAVE must retain the actual shared request producer, Game/session/source and observer");
        if(current)StrictJson.require(command.origin().game().equals(context.game().generation())
                &&command.sessionId().equals(context.game().sessionId())&&command.source().equals(context.source()),
                "live SAVE cannot borrow another physical Game or source");
        List<ExpectedValue> expected=List.of(
                new ExpectedInteger(new FieldKey("date_raw"),command.before().frame().identity().dateRaw()),
                new ExpectedInteger(new FieldKey("played_character_id"),command.before().frame().identity().player()),
                new ExpectedBoolean(new FieldKey("checkpoint_pair_verified"),true));
        StrictJson.require(command.expected().values().equals(expected),"SAVE exact original postcondition differs");
    }
}

