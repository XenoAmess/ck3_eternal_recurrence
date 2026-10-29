package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeArmyOrdinaryEffects;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Real registered postqueries on Root's currently held writer Session. No writer or Native action is created. */
public final class NativeArmyOrdinaryReads implements NativeArmyOrdinaryEffects.IndependentReadPort {
    private final ArmyWarReads wars;
    private final ArmyClosedReadContracts closed;
    private final RootReadContractCatalog catalog;
    private final PlanningReadPort reads;
    private final Supplier<Session> borrowed;
    public NativeArmyOrdinaryReads(ArmyWarReads actualWars,ArmyClosedReadContracts actualClosed,
            RootReadContractCatalog installedCatalog,PlanningReadPort actualRootReads,Supplier<Session> currentlyBorrowed) {
        wars=Objects.requireNonNull(actualWars);closed=Objects.requireNonNull(actualClosed);catalog=Objects.requireNonNull(installedCatalog);
        reads=Objects.requireNonNull(actualRootReads);borrowed=Objects.requireNonNull(currentlyBorrowed);
    }
    @Override public Optional<PlanningReadReceipt> read(NativeArmyOrdinaryEffects.Query query,ActionCommand command,ActionState.Attempt attempt,Complete actualFrame) {
        StrictJson.require(actualFrame.source().equals(command.source()) && actualFrame.sessionId().equals(command.sessionId())
                && actualFrame.identity().game().equals(command.before().game()),"Army postquery changed actual command Game/source/session");
        Session session=Objects.requireNonNull(borrowed.get(),"currently held original writer Session required");
        var revision=new ArmyCalls.Revision(new ArmyTypes.Present<>(actualFrame.identity().frame().revision()));
        var deadline=ActionObservationWindow.deadline(command);
        if(query.kind()==NativeArmyOrdinaryEffects.ReadKind.OCCUPATION) {
            var call=new ArmyCalls.War(PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1,revision,BigInteger.valueOf(query.warId()));
            var selection=new ArmyWarReads.Selection(call,new ArmyRetreatFrames.Current(actualFrame,deadline),Optional.empty());
            var result=wars.read(session,catalog,selection);
            if(result instanceof PlanningReadResult.Known<ArmyWarReadCodec.Observation> known)return Optional.of(known.receipt());
            return Optional.empty();
        }
        var context=new ArmyTypes.Context(actualFrame.identity(),actualFrame.source(),actualFrame.sessionId(),deadline);
        var call=new ArmyCalls.Frame(PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1,revision);
        var selection=new ArmyClosedReadContracts.Selection(call,context);var contract=closed.issue(catalog,selection);
        var result=reads.read(session,contract,closed.request(selection));
        if(result instanceof PlanningReadResult.Known<ArmyClosedReads.Observation> known)return Optional.of(known.receipt());
        return Optional.empty();
    }
}
