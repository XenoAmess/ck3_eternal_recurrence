package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.application.planning.military.RouteOriginExposurePolicy;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual same-frame Root query for complete directly held county capitals; no caller-authored target list. */
public final class MilitaryHeldCapitals implements RouteOriginExposurePolicy.HeldCapitalPort {
    private final RootRuntimeContext context;
    public MilitaryHeldCapitals(RootRuntimeContext actual){context=Objects.requireNonNull(actual);}
    @Override public Optional<RouteOriginExposurePolicy.HeldCapitals> collect(PlanningRequest request) {
        try{return context.withSession(same->{
            context.requireCurrent(request.deadline());
            var read=context.finance().collector().query(same,FinanceReadContracts.Query.ROOT,request);
            if(!(read instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> known))return Optional.empty();
            var packet=known.value();var original=packet.receipt().request();
            StrictJson.require(original.before().equals(request.before())&&original.source().equals(request.source())&&original.sessionId().equals(request.sessionId())
                    &&original.operation().equals(FinanceReadContracts.Query.ROOT.operation()),"held capitals crossed their actual complete original read binding");
            Obj root=OpportunityJson.object(packet.result().get("campaign_root_context"),"actual complete Root context");
            if(!new Text("available").equals(root.get("status")))return Optional.empty();
            StrictJson.require(new IntegerValue(request.before().frame().identity().player()).equals(root.get("player_character_id"))
                    &&new IntegerValue(request.before().frame().identity().nativeRevision()).equals(root.get("snapshot_revision"))
                    &&new IntegerValue(request.before().frame().identity().dateRaw()).equals(root.get("date_raw")),"held capitals changed actor/native frame");
            List<Obj> rows=OpportunityJson.array(root.get("held_title_partition"),"complete native held partition").stream().map(value->OpportunityJson.object(value,"native held title")).toList();
            var result=new java.util.ArrayList<Integer>();
            for(Obj row:rows) {
                Obj title=OpportunityJson.object(row.get("title"),"actual native held title");
                if(!new IntegerValue(java.math.BigInteger.TWO).equals(title.get("tier_raw")))continue;
                // Landless noble-family county titles deliberately have no physical Province.
                if(new Text("landless_noble_family_no_province").equals(row.get("capital_province_kind")))continue;
                int capital=OpportunityJson.integer(row.get("capital_province_id"),"actual native county capital").intValueExact();
                StrictJson.require(capital>0,"native county capital must remain positive");result.add(capital);
            }
            return Optional.of(new RouteOriginExposurePolicy.HeldCapitals(request.before(),result.stream().distinct().sorted().toList()));
        });}catch(IOException|IllegalArgumentException|IllegalStateException unavailable){return Optional.empty();}
    }
}
