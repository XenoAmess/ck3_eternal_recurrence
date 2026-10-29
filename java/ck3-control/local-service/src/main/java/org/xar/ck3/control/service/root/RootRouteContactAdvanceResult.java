package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;

/** Representation of the owning complete Route report, after archived replay and canonical
 * history membership. Clock fields are encoded by their sole Life/Battle owners. Only the
 * original contact-refresh revision roles are added here; no result or business fact is minted. */
public final class RootRouteContactAdvanceResult {
    private static final int MAXIMUM_REVISION_DIGITS=4300;
    private static final List<String> REFRESH_REVISIONS=List.of("from_revision","from_native_revision","to_revision","to_native_revision");
    private static final Set<String> REFRESH_FIELDS=Set.of("attempted","ack_status","from_snapshot_id","from_revision",
            "from_native_revision","to_snapshot_id","to_revision","to_native_revision","date_raw");
    private RootRouteContactAdvanceResult() { }

    public static RawJson encode(RawJson numeric,OperationKey actualStep) {
        Obj original=parse(numeric,actualStep);Obj contact=contact(original,true);
        RawJson prepared=new RawJson(DriverJson.encode(contact));
        RawJson result=RouteContactSteps.parse(actualStep.value()).days()==1
                ?RootLifeAdvancePublicResult.encodeClockReport(prepared,actualStep)
                :RootBattleAdvancePublicResult.encodeClockReport(prepared,actualStep);
        require(DriverJson.object(decode(result,actualStep).bytes(),RawJson.MAXIMUM_BYTES).equals(original),
                "Route public projection changed an original JSON value, role or decimal token");
        return result;
    }
    public static RawJson decode(RawJson canonical,OperationKey actualStep) {
        parse(canonical,actualStep);
        RawJson clock=RouteContactSteps.parse(actualStep.value()).days()==1
                ?RootLifeAdvancePublicResult.decodeClockReport(canonical,actualStep)
                :RootBattleAdvancePublicResult.decodeClockReport(canonical,actualStep);
        return new RawJson(DriverJson.encode(contact(parse(clock,actualStep),false)));
    }
    private static Obj parse(RawJson actual,OperationKey step) {
        Objects.requireNonNull(actual);Objects.requireNonNull(step);
        var requested=RouteContactSteps.parse(step.value());
        Obj root=DriverJson.object(actual.bytes(),RawJson.MAXIMUM_BYTES);
        require(new Text(step.value()).equals(root.get("step")),"Route report must preserve the exact original parsed caller step");
        require(integer(root.get("requested_horizon_days"),"requested_horizon_days").intValueExact()==requested.days(),
                "Route report horizon differs from its original literal");
        if(requested.days()>1){
            require(new Text("frozen_current_routes").equals(root.get("route_contact_window_context_basis"))
                    &&root.get("route_contact_window") instanceof Obj,"Route window report must retain its actual frozen-route projection");
        }
        return root;
    }
    private static Obj contact(Obj root,boolean encode) {
        Value raw=root.get("contact_refresh");
        if(raw==null)return root; // No refresh branch and an explicit null are different.
        Obj refresh=object(raw,"contact_refresh");
        require(refresh.members().keySet().equals(REFRESH_FIELDS),"complete original same-date contact refresh fields required");
        require(refresh.get("attempted") instanceof Bool,"contact_refresh attempted must retain its actual boolean");
        Obj converted=refresh;
        for(String field:REFRESH_REVISIONS){
            Value value=refresh.get(field);
            require(value!=null,"missing contact refresh revision is not null: "+field);
            if(value==Nil.INSTANCE)continue;
            if(encode){
                require(value instanceof IntegerValue,"original contact refresh revision must be an integer");
                var exact=((IntegerValue)value).value();
                require(exact.signum()>=0&&exact.toString().length()<=MAXIMUM_REVISION_DIGITS,
                        "contact refresh revision exceeds its original nonnegative snapshot integer domain");
                converted=converted.with(field,new Text(exact.toString()));
            }else{
                require(value instanceof Text,"public contact refresh revision must be a canonical decimal string");
                String exact=((Text)value).value();
                require(exact.length()<=MAXIMUM_REVISION_DIGITS&&exact.matches("0|[1-9][0-9]*"),
                        "canonical contact refresh snapshot revision required");
                converted=converted.with(field,new IntegerValue(new java.math.BigInteger(exact)));
            }
        }
        return root.with("contact_refresh",converted);
    }
}

