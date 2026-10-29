package org.xar.ck3.control.service.root;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionEffects;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPostcondition;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One installed operation binding dispatches the exact typed original plan to its genuine producer and verifier. */
public final class RootPendingInteractionEffects implements NativeEffectRegistry.Observer,ActionPorts.PreparationPort {
    public static final List<OperationKey> OPERATIONS=List.of(new OperationKey("accept-pending-character-interaction"),new OperationKey("reject-pending-character-interaction"),new OperationKey("acknowledge-pending-character-interaction"));
    public record Sources(ExactRef mux,ExactRef knownEffects,ExactRef eventEffects) {
        public Sources { for(ExactRef ref:List.of(mux,knownEffects,eventEffects))StrictJson.require(ref.bytes()>0,"actual pending preparation/observer/replay sources required"); }
    }
    private enum Branch { KNOWN,SOURCE_REVIEWED }
    private final KnownPendingInteractionEffects known;
    private final NativeEventEffects events;
    private final NativeEventEffects.MaterialQueries material;
    private final NativeEffectEvidence.FrameLoader frames;
    private final Sources sources;
    public RootPendingInteractionEffects(KnownPendingInteractionEffects actualKnown,NativeEventEffects sameEvents,
            NativeEventEffects.MaterialQueries sameMaterial,NativeEffectEvidence.FrameLoader actualFrames,Sources exactSources) {
        known=Objects.requireNonNull(actualKnown);events=Objects.requireNonNull(sameEvents);material=Objects.requireNonNull(sameMaterial);frames=Objects.requireNonNull(actualFrames);sources=Objects.requireNonNull(exactSources);
    }
    private static Branch branch(ActionCommand command) {
        Objects.requireNonNull(command);StrictJson.require(OPERATIONS.contains(command.operation()),"pending mux owns exactly its three installed native reply operations");
        String schema=command.expected().observerSchema();OpportunityJson.Value retained=command.arguments().get("known_pending_plan");
        if(KnownPendingInteractionPostcondition.SCHEMA.equals(schema)) {
            StrictJson.require(retained instanceof OpportunityJson.Obj,"known pending original plan artifact required");return Branch.KNOWN;
        }
        StrictJson.require(NativeEventPostconditionPort.PENDING_SCHEMA.equals(schema)
                &&(retained==null||retained==OpportunityJson.Nil.INSTANCE)
                &&command.arguments().get("unhandled_interaction_fallback") instanceof OpportunityJson.Obj capture
                &&new OpportunityJson.Text("xar.pending-interaction-left-reply/v1").equals(capture.get("schema"))
                &&command.arguments().get("selected_step") instanceof OpportunityJson.Text selected&&selected.value().equals(command.operation().value()),"source-reviewed pending original plan/schema required; unknown schemas cannot borrow a reply producer");
        return Branch.SOURCE_REVIEWED;
    }
    @Override public NativeRequest prepare(ActionCommand command) { return switch(branch(command)) { case KNOWN->known.prepare(command);case SOURCE_REVIEWED->EventActionPreparation.prepare(command); }; }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome outcome) {
        return switch(branch(command)) { case KNOWN->known.observe(command,attempt,outcome);case SOURCE_REVIEWED->events.observe(command,attempt,outcome); };
    }
    public List<NativeEffectRegistry.Binding> bindings() { return OPERATIONS.stream().map(operation->new NativeEffectRegistry.Binding(operation,sources.mux(),this,this)).toList(); }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers() {
        List<NativeRecordedEvidenceVerifier.Binding> originalKnown=KnownPendingInteractionEffects.archivedVerifiers(sources.knownEffects(),frames);
        return OPERATIONS.stream().map(operation->new NativeRecordedEvidenceVerifier.Binding(operation,sources.mux(),(head,receipt,archive)-> {
            if(branch(receipt.command())==Branch.KNOWN)originalKnown.stream().filter(b->b.operation().equals(operation)).findFirst().orElseThrow().verifier().verify(head,receipt,archive);
            else NativeEventEffects.archivedVerifier(operation,sources.eventEffects(),frames,material).verifier().verify(head,receipt,archive);
        })).toList();
    }
}
