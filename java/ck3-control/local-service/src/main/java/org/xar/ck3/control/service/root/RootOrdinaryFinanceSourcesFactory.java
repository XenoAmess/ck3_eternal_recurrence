package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceFactory;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinancePolicies;
import org.xar.ck3.control.application.effects.FinanceEvidenceArchive;
import org.xar.ck3.control.application.planning.finance.HireMercenaryAck;
import org.xar.ck3.control.application.planning.finance.MercenaryProcurement;
import org.xar.ck3.control.application.planning.finance.GiftColdReadService;
import org.xar.ck3.control.application.planning.finance.GiftProcessIdentity;
import org.xar.ck3.control.warbudget.OrdinaryWarPriority;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingReducer;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecoveryCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.effects.NativeFinanceEffects;

/** Ordinary finance implementation roles and fixed read definitions, without historical source qualification. */
public final class RootOrdinaryFinanceSourcesFactory {
    private RootOrdinaryFinanceSourcesFactory() { }

    public static FinanceRuntimeInstaller.Sources sources(
            RootOrdinaryRuntimeConfiguration config,
            RootAdditionalDomains.ImplementationMetadata metadata,
            ExactRef actualNativeImplementation) throws IOException {
        
        if (config == null) throw new NullPointerException("config");
        if (metadata == null) throw new NullPointerException("metadata");
        if (actualNativeImplementation == null) throw new NullPointerException("actualNativeImplementation");
        if (actualNativeImplementation.bytes() <= 0) throw new IllegalArgumentException("actualNativeImplementation must have bytes");

        Function<Class<?>, ExactRef> ref = metadata::implementation;

        OrdinaryFinanceFactory.Sources finance = new OrdinaryFinanceFactory.Sources(
            ref.apply(OrdinaryFinancePolicies.class),
            ref.apply(NativeFinanceEffects.class),
            ref.apply(NativeFinanceEffects.class),
            ref.apply(FinanceEvidenceArchive.class)
        );

        List<FinanceRuntimeInstaller.ReadSource> readSources = List.of(
            new FinanceRuntimeInstaller.ReadSource(
                FinanceReadContracts.Query.ROOT,
                new FinanceReadContracts.Registration(
                    actualNativeImplementation,
                    new FinanceReadContracts.Permission(
                        Optional.of("game.command.query-campaign-root-context-v1"),
                        "game.command.query-campaign-root-context-v1",
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                        ReadContract.WireProfile.EXECUTE_STEP
                    )
                )
            ),
            new FinanceRuntimeInstaller.ReadSource(
                FinanceReadContracts.Query.MERCENARIES,
                new FinanceReadContracts.Registration(
                    actualNativeImplementation,
                    new FinanceReadContracts.Permission(
                        Optional.of("game.command.query-player-mercenary-context-v1"),
                        "game.command.query-player-mercenary-context-v1",
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                        ReadContract.WireProfile.EXECUTE_STEP
                    )
                )
            ),
            new FinanceRuntimeInstaller.ReadSource(
                FinanceReadContracts.Query.CASH,
                new FinanceReadContracts.Registration(
                    actualNativeImplementation,
                    new FinanceReadContracts.Permission(
                        Optional.empty(),
                        CashObservationReads.PERMISSION,
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                        ReadContract.WireProfile.EXECUTE_STEP
                    )
                )
            ),
            new FinanceRuntimeInstaller.ReadSource(
                FinanceReadContracts.Query.CONSTRUCTION,
                new FinanceReadContracts.Registration(
                    actualNativeImplementation,
                    new FinanceReadContracts.Permission(
                        Optional.empty(),
                        RootSelectedRegistrationConfiguration.RegistrationFlag.CONSTRUCTION_FORMAL_TRIAL.wire(),
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                        ReadContract.WireProfile.EXECUTE_STEP
                    )
                )
            ),
            new FinanceRuntimeInstaller.ReadSource(
                FinanceReadContracts.Query.FACTION_GIFT,
                new FinanceReadContracts.Registration(
                    actualNativeImplementation,
                    new FinanceReadContracts.Permission(
                        Optional.empty(),
                        RootSelectedRegistrationConfiguration.RegistrationFlag.FACTION_GIFT_QUERY.wire(),
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                        ReadContract.WireProfile.EXECUTE_STEP
                    )
                )
            ),
            new FinanceRuntimeInstaller.ReadSource(
                FinanceReadContracts.Query.FACTION_GIFT_RECEIPT,
                new FinanceReadContracts.Registration(
                    actualNativeImplementation,
                    new FinanceReadContracts.Permission(
                        Optional.empty(),
                        RootSelectedRegistrationConfiguration.RegistrationFlag.FACTION_GIFT_QUERY.wire(),
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                        ReadContract.WireProfile.EXECUTE_STEP
                    )
                )
            )
        );

        FinanceRuntimeInstaller.GiftColdSources giftCold = new FinanceRuntimeInstaller.GiftColdSources(
            new FinanceReadContracts.Registration(
                actualNativeImplementation,
                new FinanceReadContracts.Permission(
                    Optional.empty(),
                    RootSelectedRegistrationConfiguration.RegistrationFlag.FACTION_GIFT_QUERY.wire(),
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                    ReadContract.WireProfile.EXECUTE_STEP
                )
            ),
            ref.apply(GiftColdReadService.class),
            ref.apply(GiftColdRecovery.class),
            ref.apply(GiftColdRecoveryCodec.class),
            ref.apply(CanonicalGiftColdProvider.class),
            ref.apply(GiftProcessIdentity.class)
        );

        return new FinanceRuntimeInstaller.Sources(
            finance,
            ref.apply(FinanceReadContracts.class),
            ref.apply(HireMercenaryAck.class),
            ref.apply(MercenaryDomainSource.class),
            ref.apply(MercenaryProcurement.class),
            ref.apply(OrdinaryWarPriority.class),
            actualNativeImplementation,
            ref.apply(FactionAlertsCodec.class),
            ref.apply(GiftDomainSource.class),
            ref.apply(GiftPendingCodec.class),
            ref.apply(GiftPendingReducer.class),
            readSources,
            // The original SourceProducts compositor replaces these with its actual external body bindings before install.
            List.of(),
            giftCold
        );
    }
}

