package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** The same request-aware preparation, live observer and cold verifier enter the sole Root catalog. */
public final class GuardianOutgoingInstaller {
    private final OrdinaryInitiationPreparation preparation;
    private final GuardianOutgoingEffects effects;
    private final GuardianReconciliationQueries reconciliation;
    private final List<RootExecutableBindings.ActionBinding> actions;
    private final List<NativeRecordedEvidenceVerifier.Binding> archived;
    public GuardianOutgoingInstaller(Supplier<NativeGameTransport> actualCurrentTransport,Supplier<HeldDriverObservationPort> actualCurrentHeld,
            Build actualQualifiedBuild,PlanningReadPort soleReads,ReadContract<OrdinaryContext> actualRegisteredQuery,
            OrdinaryClaimDomain actualClaims,ActionPorts.OutcomeArchive sameArchive,NativeEffectEvidence.FrameLoader actualFrames,
            Supplier<ContinuityStorePort.Session> actualSession,ExactRef actualEffectsSource,ExactRef actualDecoderSource,
            GuardianReconciliationQueries actualReconciliation) {
        Objects.requireNonNull(actualSession); Objects.requireNonNull(actualEffectsSource); Objects.requireNonNull(actualDecoderSource);
        var projection=new RootInteractionContextProjection(actualQualifiedBuild);
        var frames=OrdinaryInitiationPreparation.heldFrames(actualCurrentHeld,projection,sameArchive,actualFrames);
        reconciliation=Objects.requireNonNull(actualReconciliation);reconciliation.requireOrdinary(actualRegisteredQuery);
        effects=new GuardianOutgoingEffects(soleReads,actualRegisteredQuery,actualClaims,actualFrames,reconciliation);
        preparation=new OrdinaryInitiationPreparation(actualCurrentTransport,soleReads,actualRegisteredQuery,frames,actualClaims,sameArchive,effects);
        var operation=new OperationKey(OrdinaryInteractionCodec.INITIATE_STEP);
        var binding=new NativeEffectRegistry.Binding(operation,actualEffectsSource,preparation,
                (command,attempt,dispatch)->preparation.observeProjected(Objects.requireNonNull(actualSession.get()),command,attempt,dispatch));
        actions=List.of(new RootExecutableBindings.ActionBinding(binding,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of(OrdinaryInteractionCodec.INITIATE_CAPABILITY),actualDecoderSource));
        archived=List.of(effects.archivedVerifier(actualEffectsSource,actualSession));
    }
    public OrdinaryInitiationPreparation preparation() { return preparation; }
    public GuardianOutgoingEffects effects() { return effects; }
    public GuardianReconciliationQueries reconciliationQueries() { return reconciliation; }
    public List<ReadContract<?>> reads() { return List.of(reconciliation.contract()); }
    public List<RootExecutableBindings.ActionBinding> actions() { return actions; }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers() { return archived; }
}

