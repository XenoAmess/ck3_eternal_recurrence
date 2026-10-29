package org.xar.ck3.control.service.root;
import java.io.IOException;
import java.util.*;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration;
import org.xar.ck3.control.service.root.RootRuntimeSourceProducts;
import org.xar.ck3.control.service.root.RootAdditionalDomains;
import org.xar.ck3.control.service.root.RootRuntimePreparedSources;
import org.xar.ck3.control.service.root.RootPublicArmyActionIds;
import org.xar.ck3.control.service.root.RootArmyStockReadRuntime;
import org.xar.ck3.control.service.root.RootH2743StockPredicateAdmission;
import org.xar.ck3.control.service.root.RootManagedSessionScope;
import org.xar.ck3.control.service.root.RootOrdinaryClaimRuntime;
import org.xar.ck3.control.service.root.RootOrdinaryClaimOriginals;
import org.xar.ck3.control.service.root.RootHolyHirePoststate;
import org.xar.ck3.control.service.root.RootMilitaryControlStepRuntime;
import org.xar.ck3.control.service.root.RootMilitaryControlPublicStepProducts;
import org.xar.ck3.control.service.root.RootArmyStructuralStepRuntime;
import org.xar.ck3.control.service.root.RootPublicPauseRuntime;
import org.xar.ck3.control.service.root.RootPublicPauseStepProducts;
import org.xar.ck3.control.service.root.RootPublicPausePublicResult;
import org.xar.ck3.control.service.root.RootPublicPauseArchiveClassifier;
import org.xar.ck3.control.service.root.OrdinaryMilitaryInstaller;
import org.xar.ck3.control.service.root.ArmyAdditionalReadInstaller;
import org.xar.ck3.control.service.root.RootArmyDeclarationDiagnostics;
import org.xar.ck3.control.application.planning.military.CommanderBindings;
import org.xar.ck3.control.application.planning.military.OrdinaryActiveRetreatPolicy;
import org.xar.ck3.control.application.planning.military.CommanderQualityPolicy;
import org.xar.ck3.control.application.planning.military.SafeWarRendezvousPolicy;
import org.xar.ck3.control.application.planning.military.GeneralBattleForecastPolicy;
import org.xar.ck3.control.application.planning.military.CommanderObservationCollector;
import org.xar.ck3.control.application.planning.military.CommanderAssignmentPostcondition;
import org.xar.ck3.control.application.planning.military.CommanderArchivedVerifier;
import org.xar.ck3.control.application.planning.military.CommanderReconciliationCollector;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.application.advance.GenericPublicPauseRecovery;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyClosedReadCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyClosedOriginalResultCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyClosedReadContracts;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyClosedReadService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyBattleReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyBattleReadService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyBattleReconciliationReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRouteReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowQueryFailure;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatDomain;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatComposite;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatOrderService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatFrames;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatPostReadCollector;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarExitTruceReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmySpecialWarReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmySpecialWarReadCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReadCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalStockCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionPreparation;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionService;
import org.xar.ck3.control.nativebridge.capabilities.army.RegularMaaPrivatePermission;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStructuralActions;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStructuralActionCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStructuralEffects;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyDeclarationDiagnostics;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarReadCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyForecastReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyPlanningReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyReinforcementReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyReinforcementCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyAdditionalReadService;
import org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlActions;
import org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlContract;
import org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryReceiverProof;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.application.effects.NativeArmyMoveEffects;
import org.xar.ck3.control.application.effects.NativeArmyOrdinaryEffects;
import org.xar.ck3.control.application.effects.NativeArmyWarWindowEffects;
import org.xar.ck3.control.application.effects.NativeWarExitEffects;
import org.xar.ck3.control.application.effects.HolyHirePoststate;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.time.Duration;
public final class RootOrdinaryArmySourcesFactory {
public static RootRuntimeSourceProducts.ArmyConfiguration army(RootOrdinaryRuntimeConfiguration config, RootRuntimeSourceProducts.OrdinaryRuntimePorts ports, RootAdditionalDomains.ImplementationMetadata metadata, ExactRef actualNativeDLL) throws IOException {
    Objects.requireNonNull(config);
    Objects.requireNonNull(ports);
    Objects.requireNonNull(metadata);
    Objects.requireNonNull(actualNativeDLL);
    Function<Class<?>, ExactRef> m = metadata::implementation;
    var timeout = config.operationTimeout();
    var sharedActionIds = new RootPublicArmyActionIds(ports.core(), config.authorityId());

    var closureSet = new LinkedHashSet<ExactRef>();
    closureSet.add(m.apply(ArmyRetreatDomain.class));
    closureSet.add(m.apply(ArmyRetreatComposite.class));
    closureSet.add(m.apply(ArmyRetreatService.class));
    closureSet.add(m.apply(ArmyRetreatOrderService.class));
    closureSet.add(m.apply(ArmyRetreatFrames.class));
    closureSet.add(m.apply(ArmyRetreatPostReadCollector.class));
    closureSet.add(m.apply(ArmyClosedReadCodec.class));
    closureSet.add(m.apply(ArmyClosedOriginalResultCodec.class));
    closureSet.add(m.apply(ArmyClosedReadContracts.class));
    closureSet.add(m.apply(ArmyClosedReadService.class));
    closureSet.add(m.apply(ArmyBattleReads.class));
    closureSet.add(m.apply(ArmyBattleReadService.class));
    closureSet.add(m.apply(ArmyBattleReconciliationReads.class));
    closureSet.add(m.apply(ArmyRouteReads.class));
    closureSet.add(m.apply(ArmyWindowReads.class));
    closureSet.add(m.apply(ArmyWindowService.class));
    closureSet.add(m.apply(ArmyWindowCodec.class));
    closureSet.add(m.apply(ArmyWindowAttempts.class));
    closureSet.add(m.apply(ArmyWindowQueryFailure.class));
    closureSet.add(m.apply(NativeArmyMoveEffects.class));
    closureSet.add(actualNativeDLL);
    var closure = List.copyOf(closureSet);

    var stockRead = new RootArmyStockReadRuntime.Sources(
        m.apply(RootArmyStockReadRuntime.class),
        m.apply(RootH2743StockPredicateAdmission.class),
        m.apply(H2743StockPredicateAdmission.class),
        m.apply(ArmyWarSupplementalStockCodec.class),
        m.apply(RootManagedSessionScope.class)
    );

    var armySources = new ArmyRuntimeInstaller.Sources(
        new ArmyRuntimeInstaller.ReadSources(actualNativeDLL, m.apply(ArmyClosedReadCodec.class)),
        new ArmyRuntimeInstaller.ReadSources(actualNativeDLL, m.apply(ArmyBattleReads.class)),
        new ArmyRuntimeInstaller.ReadSources(actualNativeDLL, m.apply(ArmyRouteReads.class)),
        new ArmyRuntimeInstaller.ReadSources(actualNativeDLL, m.apply(ArmyWindowCodec.class)),
        new ArmyRuntimeInstaller.ReadSources(m.apply(ArmyBattleReconciliationReads.class), m.apply(ArmyBattleReconciliationReads.class)),
        new ArmyWarExitTruceReads.Sources(m.apply(ArmyWarExitTruceReads.class), m.apply(ArmyClosedReadCodec.class)),
        new ArmySpecialWarReads.Sources(m.apply(ArmySpecialWarReads.class), m.apply(ArmySpecialWarReadCodec.class), actualNativeDLL, actualNativeDLL, actualNativeDLL),
        new ArmyWarSupplementalReads.Sources(m.apply(ArmyWarSupplementalReads.class), m.apply(ArmyWarSupplementalReadCodec.class), actualNativeDLL, actualNativeDLL, Optional.empty()),
        stockRead,
        m.apply(ArmyRetreatDomain.class),
        m.apply(ArmyRetreatComposite.class),
        new ArmyRuntimeInstaller.ServiceSources(m.apply(ArmyClosedReadService.class), m.apply(ArmyBattleReadService.class), m.apply(ArmyRetreatService.class), m.apply(ArmyRetreatOrderService.class), m.apply(ArmyWindowService.class)),
        closure
    );

    var armyConfig = new ArmyRuntimeInstaller.Configuration(timeout, timeout, sharedActionIds, Optional.empty());

    var ordinarySources = new RootArmyOrdinaryRuntimeInputs.Sources(
        new ArmyOrdinaryActionService.Sources(m.apply(ArmyOrdinaryActionPreparation.class), m.apply(ArmyOrdinaryActionArguments.class), m.apply(ArmyOrdinaryActionService.class)),
        m.apply(RootArmyOrdinaryRuntimeInputs.class),
        m.apply(NativeArmyOrdinaryEffects.class),
        m.apply(NativeArmyMoveEffects.class),
        m.apply(NativeWarExitEffects.class),
        m.apply(NativeArmyWarWindowEffects.class),
        m.apply(PlayerHolyOrderContextRead.class),
        new HolyHirePoststate.Sources(m.apply(HolyHirePoststate.class), m.apply(RootHolyHirePoststate.class)),
        new PlayerHolyOrderContextRead.Sources(actualNativeDLL, actualNativeDLL, actualNativeDLL, actualNativeDLL, actualNativeDLL, actualNativeDLL, actualNativeDLL, actualNativeDLL),
        new RegularMaaPrivatePermission.Sources(actualNativeDLL, actualNativeDLL, actualNativeDLL, actualNativeDLL)
    );

    var ordinaryConfig = new RootArmyOrdinaryRuntimeInputs.Configuration(timeout, sharedActionIds);

    var claimRuntime = m.apply(RootOrdinaryClaimRuntime.class);
    var claimProducer = m.apply(RootOrdinaryClaimOriginals.class);
    var claimDomain = m.apply(OrdinaryClaimDomain.class);
    var claimPure = m.apply(OrdinaryOnceClaims.class);
    var claimLegacy = actualNativeDLL;
    var claimRelease = actualNativeDLL;
    var claimConstructor = m.apply(RootArmySourcesFactory.class);
    var claims = new RootOrdinaryClaimRuntime.Sources(claimRuntime, claimProducer, claimDomain, claimPure, claimLegacy, claimRelease, List.copyOf(new LinkedHashSet<>(List.of(claimRuntime, claimProducer, claimDomain, claimPure, claimLegacy, claimRelease, claimConstructor))));

    return new RootRuntimeSourceProducts.ArmyConfiguration(armySources, armyConfig, ordinarySources, ordinaryConfig, claims);
  }
public static RootRuntimePreparedSources.MilitaryConfiguration military(RootOrdinaryRuntimeConfiguration config, RootRuntimeSourceProducts.OrdinaryRuntimePorts ports, RootAdditionalDomains.ImplementationMetadata metadata, ExactRef actualNativeDLL) throws IOException {
    Objects.requireNonNull(config);
    Objects.requireNonNull(ports);
    Objects.requireNonNull(metadata);
    Objects.requireNonNull(actualNativeDLL);
    Function<Class<?>, ExactRef> m = metadata::implementation;
    var timeout = config.operationTimeout();

    var controls = new RootMilitaryControlStepRuntime.Sources(
        m.apply(MilitaryControlActions.class),
        m.apply(MilitaryControlContract.class),
        List.copyOf(new LinkedHashSet<>(List.of(
            m.apply(MilitaryControlActions.class),
            m.apply(MilitaryControlContract.class),
            m.apply(MilitaryReceiverProof.class),
            m.apply(RootMilitaryControlStepRuntime.class),
            m.apply(RootMilitaryControlPublicStepProducts.class)
        )))
    );

    var structural = new RootArmyStructuralStepRuntime.Sources(
        m.apply(ArmyStructuralActions.class),
        m.apply(ArmyStructuralActionCodec.class),
        m.apply(ArmyStructuralEffects.class),
        m.apply(RootArmyStructuralStepRuntime.class)
    );

    var commander = new CommanderBindings.Sources(
        m.apply(CommanderObservationCollector.class),
        m.apply(CommanderObservationCollector.class),
        m.apply(CommanderAssignmentPostcondition.class),
        m.apply(CommanderAssignmentPostcondition.class),
        m.apply(CommanderArchivedVerifier.class),
        m.apply(CommanderReconciliationCollector.class)
    );

    var ordinary = new OrdinaryMilitaryInstaller.Sources(
        m.apply(OrdinaryActiveRetreatPolicy.class),
        m.apply(CommanderQualityPolicy.class),
        m.apply(SafeWarRendezvousPolicy.class),
        m.apply(GeneralBattleForecastPolicy.class),
        commander,
        m.apply(ArmyForecastReads.class),
        m.apply(ArmyForecastReads.class),
        m.apply(ArmyPlanningReads.class),
        m.apply(ArmyPlanningReads.class),
        m.apply(ArmyWarReads.class),
        m.apply(ArmyWarReadCodec.class)
    );

    var additional = new ArmyAdditionalReadInstaller.Sources(
        m.apply(ArmyReinforcementReads.class),
        m.apply(ArmyReinforcementCodec.class),
        m.apply(ArmyAdditionalReadService.class)
    );

    var diagnostics = new RootArmyDeclarationDiagnostics.Sources(
        m.apply(RootArmyDeclarationDiagnostics.class),
        m.apply(ArmyDeclarationDiagnostics.class),
        m.apply(ArmyWarReads.class)
    );

    var publicPause = new RootPublicPauseRuntime.Sources(
        m.apply(RootPublicPauseRuntime.class),
        m.apply(RootPublicPauseStepProducts.class),
        m.apply(GenericPublicPauseRecovery.class),
        List.copyOf(new LinkedHashSet<>(List.of(
            m.apply(RootPublicPauseRuntime.class),
            m.apply(RootPublicPauseStepProducts.class),
            m.apply(GenericPublicPauseRecovery.class),
            m.apply(RootPublicPausePublicResult.class),
            m.apply(RootPublicPauseArchiveClassifier.class),
            m.apply(ControlSequenceObservation.class)
        )))
    );

    return new RootRuntimePreparedSources.MilitaryConfiguration(
        ordinary,
        additional,
        diagnostics,
        timeout,
        controls,
        structural,
        timeout,
        publicPause
    );
  }
}
