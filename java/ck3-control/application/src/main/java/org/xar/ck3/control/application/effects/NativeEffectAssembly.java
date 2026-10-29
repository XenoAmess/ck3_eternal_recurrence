package org.xar.ck3.control.application.effects;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatPostReadCollector;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatPreflightVerifier;

/** Installed by the single application composition root, after its exact read contracts and real domain preparers. */
public final class NativeEffectAssembly {
    private NativeEffectAssembly() { }
    public record DefinitionSources(ExactRef warExitJava, ExactRef armyMoveJava, ExactRef constructionJava, ExactRef governanceJava) {
        public DefinitionSources { for (ExactRef ref : List.of(warExitJava, armyMoveJava, constructionJava, governanceJava)) StrictJson.require(ref.bytes() > 0, "exact installed verifier source required"); }
    }
    public record Reads(ReadContract<NativeConstructionEffects.World> construction, NativeGovernanceEffects.Contracts governance) {
        public Reads { Objects.requireNonNull(construction); Objects.requireNonNull(governance); }
        /** Install these identical objects in PlanningReadCoordinator; recreating equal objects does not register them. */
        public List<ReadContract<?>> all() {
            ArrayList<ReadContract<?>> all = new ArrayList<>(); all.add(construction); all.addAll(governance.all()); return List.copyOf(all);
        }
    }
    public static Reads reads(ExactRef actualConstructionQuerySource, ExactRef actualLifestyleQuerySource,
            ExactRef actualCouncilQuerySource, ExactRef actualCrownQuerySource) {
        return new Reads(NativeConstructionEffects.readContract(actualConstructionQuerySource),
                NativeGovernanceEffects.readContracts(actualLifestyleQuerySource, actualCouncilQuerySource, actualCrownQuerySource));
    }
    public static NativeEffectRegistry install(HeldDriverObservationPort held, ActionPorts.OutcomeArchive sameWriterArchive, PlanningReadPort sameEndpointReads, Reads installedReads,
            Map<OperationKey, ActionPorts.PreparationPort> sourceQualifiedPreparers, List<NativeEffectRegistry.Binding> existingEventSaveClock,
            DefinitionSources sources, NativeGovernanceEffects.SessionPort governanceSessions,
            NativeEffectRegistry.Observer privateCouncil, NativeGovernanceEffects.PreparationEvidencePort governancePreflight,
            ArmyRetreatPreflightVerifier retreatPreflight, ArmyRetreatPostReadCollector retreatPost,
            NativeWarExitEffects.TruceReadPort truceReads, NativeEffectEvidence.FrameLoader actualFrames, int retainedHistoryLimit) {
        Objects.requireNonNull(sources); var snapshots = new NativeEffectSnapshots(held, sameWriterArchive, Objects.requireNonNull(actualFrames));
        var war = new NativeWarExitEffects(snapshots, Objects.requireNonNull(truceReads)); var army = new NativeArmyMoveEffects(snapshots,
                Objects.requireNonNull(retreatPreflight), Objects.requireNonNull(retreatPost));
        var construction = new NativeConstructionEffects(snapshots, sameEndpointReads, installedReads.construction());
        var governance = new NativeGovernanceEffects(snapshots, sameEndpointReads, installedReads.governance(),
                Objects.requireNonNull(governanceSessions), Objects.requireNonNull(privateCouncil), Objects.requireNonNull(governancePreflight));
        List<NativeEffectRegistry.Binding> bindings = new ArrayList<>(List.copyOf(existingEventSaveClock));
        for (var entry : Map.copyOf(sourceQualifiedPreparers).entrySet()) {
            OperationKey operation = entry.getKey(); NativeEffectRegistry.Observer observer; ExactRef source;
            if (NativeGovernanceEffects.kind(operation).isPresent()) { observer = governance; source = sources.governanceJava(); }
            else if (operation.value().equals("g2_player_world_building_action_private_v1")) { observer = construction; source = sources.constructionJava(); }
            else if (isWarExit(operation)) { observer = war; source = sources.warExitJava(); }
            else if (isArmyMove(operation)) { observer = army; source = sources.armyMoveJava(); }
            else throw new UnsupportedOperationException("no real registered after-state verifier for " + operation.value());
            // Parsing a name selects a verifier only after Root supplies an exact registered preparation entry.
            // A capability or prefix by itself never makes an operation submit-ready.
            bindings.add(new NativeEffectRegistry.Binding(operation, source, entry.getValue(), observer));
        }
        return new NativeEffectRegistry(bindings, retainedHistoryLimit);
    }
    public static List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers(NativeEffectRegistry installed,
            NativeEffectEvidence.FrameLoader actualFrames, Reads actualReads, DefinitionSources sources,
            List<NativeRecordedEvidenceVerifier.Binding> actualEventSaveClockAndOtherDomains,
            NativeGovernanceEffects.PreparationEvidencePort governancePreflight, ArmyRetreatPreflightVerifier retreatPreflight,
            ArmyRetreatPostReadCollector retreatPost, NativeWarExitEffects.TruceReadPort truceReads) {
        Objects.requireNonNull(retreatPost); Objects.requireNonNull(truceReads);
        var result = new ArrayList<>(List.copyOf(actualEventSaveClockAndOtherDomains));
        var existing = result.stream().map(NativeRecordedEvidenceVerifier.Binding::operation).collect(java.util.stream.Collectors.toSet());
        for (var binding : installed.installed()) {
            var operation = binding.operation(); if (existing.contains(operation)) continue;
            if (operation.value().equals("private-assign-councillor-v1"))
                throw new UnsupportedOperationException("the exact private Council continuation archived verifier must be installed by Root");
            else if (NativeGovernanceEffects.kind(operation).isPresent()) result.add(NativeGovernanceEffects.archivedVerifier(operation, sources.governanceJava(), actualFrames, actualReads.governance(), governancePreflight));
            else if (operation.value().equals("g2_player_world_building_action_private_v1")) result.add(NativeConstructionEffects.archivedVerifier(operation, sources.constructionJava(), actualFrames, actualReads.construction()));
            else if (isWarExit(operation)) result.add(NativeWarExitEffects.archivedVerifier(operation, sources.warExitJava(), actualFrames, truceReads));
            else if (isArmyMove(operation)) result.add(NativeArmyMoveEffects.archivedVerifier(operation, sources.armyMoveJava(), actualFrames, retreatPreflight, retreatPost));
            else throw new UnsupportedOperationException("installed action lacks a real archived domain revalidator: " + operation.value());
        }
        return List.copyOf(result);
    }
    private static boolean isWarExit(OperationKey operation) {
        try { NativeWarExitEffects.warId(operation);return true; }
        catch(IllegalArgumentException|ArithmeticException invalid) {return false;}
    }
    private static boolean isArmyMove(OperationKey operation) {
        if (!operation.value().matches("move-army-(?:0|[1-9][0-9]{0,9})-to-[1-9][0-9]{0,9}")) return false;
        NativeArmyMoveEffects.parse(operation); return true;
    }
}
