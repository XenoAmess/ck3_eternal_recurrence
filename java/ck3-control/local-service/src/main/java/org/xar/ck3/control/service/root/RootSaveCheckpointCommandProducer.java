package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;

/** Prepare the original typed SAVE only. The same Root owns the single dispatch and saved-material boundary. */
public final class RootSaveCheckpointCommandProducer {
    private RootSaveCheckpointCommandProducer(){ }
    public static boolean supports(OperationKey actual){return Objects.requireNonNull(actual).value().equals("save-checkpoint");}

    /** Private live custody for the exact request and its archived pre-SAVE SEM; JSON cannot construct this product. */
    public static final class Prepared {
        private final RootRuntimeContext context;
        private final RootApplicationSession root;
        private final PlanningRequest original;
        private final CheckpointRequest request;
        private final SemanticEvidence semantic;
        private Prepared(RootRuntimeContext context,RootApplicationSession root,PlanningRequest original,
                CheckpointRequest request,SemanticEvidence semantic) {
            this.context=context;this.root=root;this.original=original;this.request=request;this.semantic=semantic;
        }
        public ActionCommand command(){return request.saveCommand();}
        public CheckpointRequest request(){return request;}
        public PlanningRequest original(){return original;}
        public SemanticEvidence semantic(){return semantic;}
        /** Historical retention is not a fresh deadline or replay ticket; the executing Root separately guards its call. */
        public void requireOwner(RootRuntimeContext actualContext,RootApplicationSession actualRoot,Session same)throws IOException {
            StrictJson.require(actualContext==context&&actualRoot==root&&context.actions()==root,
                    "planned checkpoint belongs to another actual Root/context");
            context.writer().requireSession(same);context.core().requireCurrentForAccess(same,root);context.game().verify();
            StrictJson.require(root.writer()==context.writer()&&root.archive()==context.archive()
                    &&root.identity().machineId().equals(original.before().machineId())
                    &&root.identity().game().equals(original.before().game())&&root.identity().sessionId().equals(original.sessionId())
                    &&original.source().equals(context.source())&&semantic.frame().equals(original.before()),
                    "planned checkpoint original writer, source, Game, session or pre-SAVE semantic frame changed");
            requireOriginalCommand(request,original,command().actionId());
            context.semanticVerifier().verify(same,root.identity(),semantic);
        }
    }

    /** The planning callback fully unwinds before the existing factory opens its own original readiness observation. */
    public static Prepared prepare(RootRuntimeContext context,PlanningRequest original,String originalActionId)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(original);StrictJson.text(originalActionId);
        context.requireCurrent(original.deadline());
        if(!(context.actions() instanceof RootApplicationSession root))throw new IOException("actual Root checkpoint owner is not installed");
        return context.withSession(same->{
            context.writer().requireSession(same);context.core().requireCurrentForAccess(same,root);
            StrictJson.require(original.source().equals(context.source())&&original.sessionId().equals(context.game().sessionId())
                    &&original.before().machineId().equals(context.game().machineId())&&original.before().game().equals(context.game().generation()),
                    "checkpoint preparation crossed the actual original Root/source/Game/session");
            SemanticEvidence semantic=context.collector().currentPlanning(same,original,original.deadline(),(sameOriginal,lease)->{
                StrictJson.require(sameOriginal==original&&lease.frame().identity().equals(original.before())
                        &&lease.frame().source().equals(original.source())&&lease.frame().sessionId().equals(original.sessionId())
                        &&lease.semantic().frame().equals(original.before()),"checkpoint preparation replaced its actual complete planning input or SEM");
                return lease.semantic();
            });
            // No public SAVE, dispatch or READ flush occurs inside the frozen planning callback above.
            CheckpointRequest request;
            try {request=prepareOriginalRequest(root.checkpointRequestFactory(),original,originalActionId);}
            catch(InterruptedException interrupted){Thread.currentThread().interrupt();var failure=new InterruptedIOException("actual checkpoint preparation interrupted before dispatch");failure.initCause(interrupted);throw failure;}
            Prepared result=new Prepared(context,root,original,request,semantic);result.requireOwner(context,root,same);return result;
        });
    }

    /** Shared typed factory edge only, not Root/Native/material authority. Software regressions use the real factory and Service. */
    public static CheckpointRequest prepareOriginalRequest(CheckpointRequestFactory actualFactory,PlanningRequest original,
            String originalActionId)throws InterruptedException {
        Objects.requireNonNull(actualFactory);Objects.requireNonNull(original);StrictJson.text(originalActionId);
        CheckpointRequest request=actualFactory.prepare(original.before(),original.source(),original.sessionId(),
                Optional.empty(),original.deadline(),originalActionId);
        requireOriginalCommand(request,original,originalActionId);return request;
    }
    private static void requireOriginalCommand(CheckpointRequest request,PlanningRequest original,String originalActionId) {
        ActionCommand command=Objects.requireNonNull(request).saveCommand();
        StrictJson.require(supports(command.operation())&&command.origin() instanceof CommandOrigin.Gameplay
                &&command.actionId().equals(originalActionId)&&command.before().equals(original.before())
                &&command.source().equals(original.source())&&command.sessionId().equals(original.sessionId())
                &&command.deadline().equals(original.deadline())&&request.baseline().isEmpty(),
                "sole checkpoint factory changed the original planned identity/source/session/deadline or baseline role");
    }
}
