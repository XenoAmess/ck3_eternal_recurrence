package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;

/** One source-bound assembly of every Army-strength input family and service projection stage. */
public final class ArmyStrengthsInstallation {
    private ArmyStrengthsInstallation() { }
    public record Sources(ArmyStrengthsNativeFields.Sources nativeFields,
            ArmyStrengthsExistingFamilies.Sources existingFamilies, ExactRef baselineStages,
            ExactRef baselinePublicRules, ExactRef refill, ExactRef assault, ExactRef phases,
            ExactRef supply, ExactRef monthly, ExactRef movement, ExactRef managers,
            ExactRef detachment, ExactRef detachmentData, ExactRef lossAllocation) {
        public Sources {
            Objects.requireNonNull(nativeFields); Objects.requireNonNull(existingFamilies);
            Objects.requireNonNull(baselineStages); Objects.requireNonNull(baselinePublicRules);
            Objects.requireNonNull(refill); Objects.requireNonNull(assault); Objects.requireNonNull(phases);
            Objects.requireNonNull(supply); Objects.requireNonNull(monthly); Objects.requireNonNull(movement);
            Objects.requireNonNull(managers); Objects.requireNonNull(detachment);
            Objects.requireNonNull(detachmentData); Objects.requireNonNull(lossAllocation);
        }
        public List<ExactRef> sourceRefs() {
            List<ExactRef> sources = new ArrayList<>(List.of(nativeFields.nativeFields(), nativeFields.currentMovement(),
                    nativeFields.armyUpdateClock(), baselineStages, baselinePublicRules, refill, assault, phases,
                    supply, monthly, movement, managers, detachment, detachmentData, lossAllocation));
            sources.addAll(List.of(existingFamilies.monthlyLoss(), existingFamilies.dailyQueue(), existingFamilies.countyEntry(),
                    existingFamilies.sourceNextFrame(), existingFamilies.fleetTick(), existingFamilies.supplyDispatch(),
                    existingFamilies.futureSupply(), existingFamilies.combatRoles()));
            return List.copyOf(sources);
        }
    }
    /** Both objects are already frozen and enforce the complete closed enum inventory on every production call. */
    public record Installed(ArmyStrengthsFamilies.Registry families, ArmyStrengthsPipeline pipeline, Sources sources) {
        public Installed {
            Objects.requireNonNull(families); Objects.requireNonNull(pipeline); Objects.requireNonNull(sources);
            families.requireCompleteRich(); pipeline.requireComplete();
        }
    }
    public static Installed install(Sources sources) {
        Objects.requireNonNull(sources);
        var families = new ArmyStrengthsFamilies.Registry();
        var pipeline = new ArmyStrengthsPipeline();
        ArmyStrengthsNativeFields.install(families, sources.nativeFields());
        ArmyStrengthsExistingFamilies.install(families, sources.existingFamilies());
        ArmyStrengthsStages.install(pipeline, sources.baselineStages());
        ArmyStrengthsRefill.install(families, pipeline, sources.refill());
        ArmyStrengthsAssaultInstaller.install(families, pipeline, sources.assault());
        ArmyStrengthsPhases.install(families, pipeline, sources.phases());
        ArmyStrengthsSupply.install(families, pipeline, sources.supply());
        ArmyStrengthsMonthly.install(families, pipeline, sources.monthly());
        ArmyStrengthsMovement.install(families, pipeline, sources.movement());
        ArmyStrengthsManagers.install(families, pipeline, sources.managers());
        ArmyStrengthsDetachment.install(families, pipeline, sources.detachment());
        ArmyDetachmentDataProjection.install(pipeline, sources.detachmentData());
        ArmyStrengthsLossAllocation.install(families, pipeline, sources.lossAllocation());
        families.freeze(); pipeline.freeze();
        return new Installed(families, pipeline, sources);
    }
}

