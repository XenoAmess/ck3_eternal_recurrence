package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SourceRole.*;
import static org.xar.ck3.control.service.root.RootRuntimeNativeOriginals.Role.*;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy;
import org.xar.ck3.control.application.effects.NativeArmyMoveEffects;
import org.xar.ck3.control.application.effects.NativeArmyOrdinaryEffects;
import org.xar.ck3.control.application.effects.NativeArmyWarWindowEffects;
import org.xar.ck3.control.application.effects.HolyHirePoststate;
import org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation;
import org.xar.ck3.control.application.effects.NativeWarExitEffects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SourceRole;
import org.xar.ck3.control.service.root.RootRuntimeNativeOriginals.Role;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.OriginalKind;

/** Concrete source facts and uninstalled definitions only. No Core, Game, seed, permit or Ready is created.
 * Startup retains responsibility for current bound-original/configuration and actual native-cut qualification.
 */
public final class RootArmySourcesFactory {
    private RootArmySourcesFactory() { }
    /** Ordinary business configuration constructs both actual Army products and shares claim sources with Guardian. */
    public static Products ordinary(ArmyRuntimeInstaller.Sources armySources, ArmyRuntimeInstaller.Configuration armyConfig,
            RootArmyOrdinaryRuntimeInputs.Sources ordinarySources, RootArmyOrdinaryRuntimeInputs.Configuration ordinaryConfig,
            RootOrdinaryClaimRuntime.Sources claimSources) {
        Objects.requireNonNull(armySources);Objects.requireNonNull(armyConfig);Objects.requireNonNull(ordinarySources);
        Objects.requireNonNull(ordinaryConfig);Objects.requireNonNull(claimSources);
        if(armySources.supplementalWar().stockSources().isPresent()!=armyConfig.stock().isPresent())
            throw new IllegalArgumentException("Army supplemental stock sources presence must match configuration presence");
        var armyPrepared=new ArmyRuntimeInstaller.Prepared(armySources,armyConfig);
        var ordinaryPrepared=new RootArmyOrdinaryRuntimeInputs.Prepared(ordinarySources,ordinaryConfig);
        return new Products(armyPrepared,ordinaryPrepared,claimSources);
    }
    public record Products(ArmyRuntimeInstaller.Prepared army,RootArmyOrdinaryRuntimeInputs.Prepared ordinary,
            RootOrdinaryClaimRuntime.Sources ordinaryClaimSources) {
        public Products { Objects.requireNonNull(army);Objects.requireNonNull(ordinary);Objects.requireNonNull(ordinaryClaimSources); }
    }
    public static Products prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,
            RootRuntimeNativeOriginals.Bound originals,ArmyRetreatOrderService.ActionIds sameRetreatIds,
            ArmyOrdinaryActionService.ActionIds sameOrdinaryIds)throws IOException {
        return prepare(inputs,selected,originals,sameRetreatIds,sameOrdinaryIds,Optional.empty());
    }
    public static Products prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,
            RootRuntimeNativeOriginals.Bound originals,ArmyRetreatOrderService.ActionIds sameRetreatIds,
            ArmyOrdinaryActionService.ActionIds sameOrdinaryIds,Optional<RootArmyStockReadRuntime.Configuration> stock)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(originals);
        Objects.requireNonNull(sameRetreatIds);Objects.requireNonNull(sameOrdinaryIds);Objects.requireNonNull(stock);
        StrictJson.require(inputs.application().machineId().equals(originals.configuration().machineId()),"Army original sources belong to another configured machine");
        selected.requireCurrent();
        var sources=armySources(inputs,selected,originals,stock);
        var settings=inputs.configuration().army();
        var army=new ArmyRuntimeInstaller.Prepared(sources,new ArmyRuntimeInstaller.Configuration(
                Duration.ofMillis(settings.commandReadTimeoutMs()),Duration.ofMillis(settings.reconciliationReadTimeoutMs()),sameRetreatIds,stock));
        var ordinary=new RootArmyOrdinaryRuntimeInputs.Prepared(ordinarySources(selected,originals),
                new RootArmyOrdinaryRuntimeInputs.Configuration(Duration.ofMillis(settings.commandReadTimeoutMs()),sameOrdinaryIds));
        var claims=claimSources(selected,originals);
        selected.requireCurrent();return new Products(army,ordinary,claims);
    }
    private static ArmyRuntimeInstaller.Sources armySources(RootRuntimeDefinitions.Inputs input,RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,
            Optional<RootArmyStockReadRuntime.Configuration> stock)throws IOException {
        // These actual shared producer classes belong to the selected deployment closure. Merely
        // constructing a callback or the source record does not qualify a read or automatic action.
        selected.javaSource(LOCAL_SERVICE,RootArmyReadPacketVerifier.class);
        selected.javaSource(APPLICATION,OrdinaryAutomaticSurrenderPolicy.class);
        selected.javaSource(APPLICATION,ArmyOrdinaryActionArguments.class);
        selected.javaSource(APPLICATION,NativeDirectFixedWindowObservation.class);
        var stockRead=new RootArmyStockReadRuntime.Sources(selected.javaSource(LOCAL_SERVICE,RootArmyStockReadRuntime.class),
                selected.javaSource(LOCAL_SERVICE,RootH2743StockPredicateAdmission.class),selected.javaSource(APPLICATION,H2743StockPredicateAdmission.class),
                selected.javaSource(APPLICATION,ArmyWarSupplementalStockCodec.class),selected.javaSource(LOCAL_SERVICE,RootManagedSessionScope.class));
        return new ArmyRuntimeInstaller.Sources(
                new ArmyRuntimeInstaller.ReadSources(nativeSource(input,selected,ARMY_CLOSED_DEFINITION),javaSource(input,selected,ARMY_CLOSED_DECODER,NATIVE_TRANSPORT,ArmyClosedReadCodec.class)),
                new ArmyRuntimeInstaller.ReadSources(nativeSource(input,selected,ARMY_BATTLE_DEFINITION),configuredJava(input,selected,ARMY_BATTLE_DECODER)),
                new ArmyRuntimeInstaller.ReadSources(nativeSource(input,selected,ARMY_ROUTE_DEFINITION),configuredJava(input,selected,ARMY_ROUTE_DECODER)),
                new ArmyRuntimeInstaller.ReadSources(nativeSource(input,selected,ARMY_WINDOW_DEFINITION),javaSource(input,selected,ARMY_WINDOW_DECODER,APPLICATION,ArmyWindowCodec.class)),
                new ArmyRuntimeInstaller.ReadSources(javaSource(input,selected,ARMY_RECONCILIATION_DEFINITION,NATIVE_TRANSPORT,ArmyBattleReconciliationReads.class),
                        configuredJava(input,selected,ARMY_RECONCILIATION_DECODER)),
                new ArmyWarExitTruceReads.Sources(javaSource(input,selected,ARMY_WAR_EXIT_TRUCE_DEFINITION,NATIVE_TRANSPORT,ArmyWarExitTruceReads.class),
                        javaSource(input,selected,ARMY_CLOSED_DECODER,NATIVE_TRANSPORT,ArmyClosedReadCodec.class)),
                new ArmySpecialWarReads.Sources(selected.javaSource(APPLICATION,ArmySpecialWarReads.class),selected.javaSource(APPLICATION,ArmySpecialWarReadCodec.class),
                        original(selected,originals,Role.H2743_PREACTION_TRUCE),original(selected,originals,Role.NATIVE_DISPATCHER),original(selected,originals,Role.WAR_BOUND_LOSS_CANDIDATE)),
                supplementalSources(selected,originals,
                        stock.map(actual->new ArmyWarSupplementalReads.StockSources(stockRead.stockDecoder(),actual.pair(),actual.pins(),actual.input().nativeSourceCheckout()))),
                stockRead,
                javaSource(input,selected,ARMY_DOMAIN,NATIVE_TRANSPORT,ArmyRetreatDomain.class),
                javaSource(input,selected,ARMY_COMPOSITE,NATIVE_TRANSPORT,ArmyRetreatComposite.class),
                new ArmyRuntimeInstaller.ServiceSources(javaSource(input,selected,ARMY_CLOSED_SERVICE,NATIVE_TRANSPORT,ArmyClosedReadService.class),
                        javaSource(input,selected,ARMY_BATTLE_SERVICE,NATIVE_TRANSPORT,ArmyBattleReadService.class),
                        javaSource(input,selected,ARMY_PREVIEW_SERVICE,NATIVE_TRANSPORT,ArmyRetreatService.class),
                        javaSource(input,selected,ARMY_ORDER_SERVICE,NATIVE_TRANSPORT,ArmyRetreatOrderService.class),
                        javaSource(input,selected,ARMY_WINDOW_SERVICE,NATIVE_TRANSPORT,ArmyWindowService.class)),
                input.closure(RootRuntimeDefinitionModel.ClosureRole.ARMY_DOMAIN));
    }
    static ArmyWarSupplementalReads.Sources supplementalSources(RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,
            Optional<ArmyWarSupplementalReads.StockSources> stock)throws IOException {
        // Both native readers are implemented in the same retained ck3_11906.cpp source.
        // Keep their separate provenance fields and qualify the actual original through the shared source authority.
        return new ArmyWarSupplementalReads.Sources(selected.javaSource(APPLICATION,ArmyWarSupplementalReads.class),
                selected.javaSource(APPLICATION,ArmyWarSupplementalReadCodec.class),
                original(selected,originals,Role.ARMY_SUPPLEMENTAL_WAR_NATIVE),original(selected,originals,Role.ARMY_SUPPLEMENTAL_WAR_NATIVE),stock);
    }
    static RootArmyOrdinaryRuntimeInputs.Sources ordinarySources(RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals)throws IOException {
        var actions=new ArmyOrdinaryActionService.Sources(selected.javaSource(NATIVE_TRANSPORT,ArmyOrdinaryActionPreparation.class),
                selected.javaSource(APPLICATION,ArmyOrdinaryActionArguments.class),selected.javaSource(NATIVE_TRANSPORT,ArmyOrdinaryActionService.class));
        var holy=new PlayerHolyOrderContextRead.Sources(original(selected,originals,HOLY_PRODUCER),original(selected,originals,HOLY_COST_NORMALIZER),
                original(selected,originals,HOLY_REINFORCEMENT_NORMALIZER),original(selected,originals,HOLY_MAILBOX),original(selected,originals,HOLY_WIRE),
                original(selected,originals,HOLY_CONTEXT),original(selected,originals,HOLY_REINFORCEMENT),original(selected,originals,HOLY_BUILD4_BINDING));
        var maa=new RegularMaaPrivatePermission.Sources(original(selected,originals,REGULAR_MAA_PRODUCER),original(selected,originals,REGULAR_MAA_MAILBOX),
                original(selected,originals,REGULAR_MAA_CREATE),original(selected,originals,REGULAR_MAA_BUILD4_BINDING));
        return new RootArmyOrdinaryRuntimeInputs.Sources(actions,selected.javaSource(LOCAL_SERVICE,RootArmyOrdinaryRuntimeInputs.class),
                selected.javaSource(APPLICATION,NativeArmyOrdinaryEffects.class),selected.javaSource(APPLICATION,NativeArmyMoveEffects.class),
                selected.javaSource(APPLICATION,NativeWarExitEffects.class),selected.javaSource(APPLICATION,NativeArmyWarWindowEffects.class),
                selected.javaSource(NATIVE_TRANSPORT,PlayerHolyOrderContextRead.class),
                new HolyHirePoststate.Sources(selected.javaSource(APPLICATION,HolyHirePoststate.class),selected.javaSource(LOCAL_SERVICE,RootHolyHirePoststate.class)),holy,maa);
    }
    static RootOrdinaryClaimRuntime.Sources claimSources(RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals)throws IOException {
        var runtime=selected.javaSource(LOCAL_SERVICE,RootOrdinaryClaimRuntime.class);var producer=selected.javaSource(LOCAL_SERVICE,RootOrdinaryClaimOriginals.class);
        var domain=selected.javaSource(APPLICATION,OrdinaryClaimDomain.class);var pure=selected.javaSource(APPLICATION,OrdinaryOnceClaims.class);
        var legacy=original(selected,originals,CLAIM_PRODUCER);var release=original(selected,originals,CLAIM_HOST_RELEASE);
        var constructor=selected.javaSource(LOCAL_SERVICE,RootArmySourcesFactory.class);
        // This fixed producer/reducer closure is independent of the order other Startup helpers consume sources.
        // The complete deployed class/native graph remains separately required by the original source authority.
        return new RootOrdinaryClaimRuntime.Sources(runtime,producer,domain,pure,legacy,release,List.of(runtime,producer,domain,pure,legacy,release,constructor));
    }
    private static ExactRef original(RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Role role)throws IOException {
        return selected.original(originals.configuration().source(role).original(),role.kind());
    }
    private static ExactRef javaSource(RootRuntimeDefinitions.Inputs input,RootRuntimeSelectedSources selected,SourceRole role,Module module,Class<?> actualClass)throws IOException {
        ExactRef actual=selected.javaSource(module,actualClass);
        StrictJson.require(actual.equals(input.source(role)),"configured Army source role differs from its actual class winner: "+role);return actual;
    }
    /** Preserve the existing unique owner's explicit codec target, including shared multi-decoder bundles.
     * This does not guess a new codec class or replace the owning source/cut qualification.
     */
    private static ExactRef configuredJava(RootRuntimeDefinitions.Inputs input,RootRuntimeSelectedSources selected,SourceRole role)throws IOException {
        var pin=input.configuration().sources().stream().filter(row->row.role()==role).findFirst().orElseThrow();
        StrictJson.require(pin.kind()==RootRuntimeDefinitionModel.SourceKind.JAVA,"Army decoder must retain its original Java source kind");
        ExactRef actual=selected.javaTarget(pin.selected().targetRelative());
        StrictJson.require(actual.equals(pin.selected().sourceRef()),"configured Army decoder differs from the original winner");return actual;
    }
    private static ExactRef nativeSource(RootRuntimeDefinitions.Inputs input,RootRuntimeSelectedSources selected,SourceRole role)throws IOException {
        ExactRef source=input.source(role);String filename=Path.of(source.path()).getFileName().toString();
        OriginalKind kind;
        if(filename.endsWith(".cpp"))kind=OriginalKind.NATIVE_CPP;
        else if(filename.endsWith(".hpp"))kind=OriginalKind.NATIVE_HEADER;
        else throw new IOException("configured Army native definition must retain its actual C++/header source: "+role);
        return selected.original(new FileRef(source.path(),source.bytes(),source.sha256()),kind);
    }
}
