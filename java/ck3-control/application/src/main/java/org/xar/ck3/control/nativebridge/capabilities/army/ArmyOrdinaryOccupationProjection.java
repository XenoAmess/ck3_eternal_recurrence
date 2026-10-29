package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeArmyOrdinaryEffects;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Thin typed projection of M0's sole complete original occupation decoder; no parallel JSON normalizer. */
public final class ArmyOrdinaryOccupationProjection implements NativeArmyOrdinaryEffects.OccupationDecoder {
    @Override public List<ArmyAssaultSelection.Holding> holdings(Complete actualFrame,PlanningReadReceipt original,ActionPorts.OutcomeArchive archive) {
        NativeRecordedEvidenceVerifier.requireRead(original,archive);
        var call=ArmyCallCodec.decode(PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1,
                new RawJson(DriverJson.encode(original.request().arguments())));
        StrictJson.require(call instanceof ArmyCalls.War,"occupation original request must retain its typed war arguments");
        var context=new ArmyTypes.Context(actualFrame.identity(),actualFrame.source(),actualFrame.sessionId(),original.request().deadline());
        var observation=ArmyWarReadCodec.decode(new ArmyWarReadCodec.Scope(call,context,actualFrame.semantic(),Optional.empty()),original);
        StrictJson.require(observation instanceof ArmyWarReadCodec.Occupation,"original occupation read decoded another domain");
        return from((ArmyWarReadCodec.Occupation)observation);
    }
    public static List<ArmyAssaultSelection.Holding> from(ArmyWarReadCodec.Occupation observation) {
        var value=observation.value();
        if(!value.available() || !value.collectionComplete())return List.of();
        return value.holdings().stream().map(holding->new ArmyAssaultSelection.Holding(value.requestedWar(),holding.province(),
                holding.siegeObservable(),holding.siege().map(siege->{
                    var assault=siege.assault();
                    // assaultObservable is the discriminator; no flag below is usable when the subdomain is absent.
                    return new ArmyAssaultSelection.Siege(siege.id(),assault.isPresent(),
                            assault.map(ArmyWarOccupationCodec.Assault::inProgress).orElse(false),
                            assault.map(ArmyWarOccupationCodec.Assault::canStart).orElse(false),
                            assault.map(ArmyWarOccupationCodec.Assault::canStop).orElse(false),siege.playerBesieging());
                }))).toList();
    }
}
