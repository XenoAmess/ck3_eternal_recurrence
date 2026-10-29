package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.AdvanceResult;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Source-owned Life-result JSON representation only. Caller must first replay actual Life originals.
 * Known revision and Sentinel generation roles become canonical decimal strings. All other integer roles
 * remain numbers and unsafe unknowns refuse. Immutable DecimalValue tokens, including -0.0, are untouched.
 * Route HORIZON clock reports reuse these exact roles only after a separate source-owned Route proof.
 * This class never creates a result, queries, archives, grants Ready or proves a business/Game day.
 */
public final class RootLifeAdvancePublicResult {
    private static final BigInteger SAFE=BigInteger.valueOf(9007199254740991L);
    private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final List<String> REVISIONS=List.of("starting_revision","starting_native_revision","revision","native_revision");
    private RootLifeAdvancePublicResult() { }
    public static RawJson encode(RawJson originalNumeric) {
        Obj original=parse(originalNumeric);Obj converted=transform(original,true);safe(converted);
        RawJson result=new RawJson(DriverJson.encode(converted));
        require(parse(decode(result)).equals(original),"Life public representation changed original JSON type/content/decimal token");return result;
    }
    public static RawJson decode(RawJson canonicalPublic) {
        Obj value=parse(canonicalPublic);safe(value);
        return new RawJson(DriverJson.encode(transform(value,false)));
    }
    /** Representation of the existing one-day Route HORIZON clock report only. Expected operation is
     * a canonical finite RouteContactSteps literal, not arbitrary caller authority. The owning Route
     * result reader must verify its archived command/proof before calling this pure formatter. */
    public static RawJson encodeClockReport(RawJson originalNumeric,OperationKey expectedStep) {
        Obj original=parseClockReport(originalNumeric,expectedStep);Obj converted=transform(original,true);safe(converted);
        RawJson result=new RawJson(DriverJson.encode(converted));
        require(parseClockReport(decodeClockReport(result,expectedStep),expectedStep).equals(original),
                "Route clock public representation changed original JSON type/content/decimal token");return result;
    }
    public static RawJson decodeClockReport(RawJson canonicalPublic,OperationKey expectedStep) {
        Obj value=parseClockReport(canonicalPublic,expectedStep);safe(value);
        return new RawJson(DriverJson.encode(transform(value,false)));
    }
    private static Obj parseClockReport(RawJson value,OperationKey expectedStep) {
        Objects.requireNonNull(expectedStep);
        String step=expectedStep.value();
        require(step.startsWith(RouteContactSteps.HORIZON)&&RouteContactSteps.supports(step),
                "canonical Route HORIZON operation required for clock report");
        require(RouteContactSteps.parse(step).days()==1,"only one-day Route HORIZON clock report is supported");
        Obj root=parseResult(value);
        require(new Text(step).equals(root.get("step")),"Route clock report crossed expected actual operation");return root;
    }
    private static Obj parseResult(RawJson value) {
        Objects.requireNonNull(value);Obj root=DriverJson.object(value.bytes(),RawJson.MAXIMUM_BYTES);
        require(new Text(AdvanceResult.SCHEMA).equals(root.get("schema")),"exact actual advance-result schema required");
        return root;
    }
    private static Obj parse(RawJson value) {
        Obj root=parseResult(value);
        require(new Text("life-advance").equals(root.get("step"))||new Text("life-advance-one-day").equals(root.get("step")),"exact Life-result step required");
        return root;
    }
    private static Obj transform(Obj original,boolean encode) {
        Obj out=original;for(String field:REVISIONS)out=number(out,field,encode,true);
        for(String clock:List.of("exact_day_native_clock","campaign_deadline_native_clock_v1")) {
            Value value=out.get(clock);if(value==null||value==Nil.INSTANCE)continue;
            Obj row=object(value,clock);row=clock(row,encode);out=out.with(clock,row);
        }
        Value actions=out.get("actions");require(actions instanceof Arr,"original Life actions array required");
        var rows=new ArrayList<Value>();
        for(Value action:((Arr)actions).items()) {
            Obj row=object(action,"original clock child");
            require(row.get("step") instanceof Text step&&AdvancePrimitives.supports(new org.xar.ck3.control.application.action.OperationKey(step.value())),"Life public actions must retain actual finite clock child steps");
            Value result=row.get("result");require(result!=null,"original child result field required");
            rows.add(result==Nil.INSTANCE?row:row.with("result",token(object(result,"original Native clock result"),encode)));
        }
        out=out.with("actions",new Arr(rows));
        Value material=out.get("battle_identity_materialization");if(material!=null&&material!=Nil.INSTANCE) {
            Obj row=object(material,"battle identity materialization");
            for(String field:List.of("starting_revision","starting_native_revision","ending_revision","ending_native_revision"))row=number(row,field,encode,true);
            out=out.with("battle_identity_materialization",row);
        }
        return out;
    }
    private static Obj clock(Obj original,boolean encode) {
        Obj out=original;
        for(String name:List.of("armed","stopped")) {
            Value value=out.get(name);if(value!=null&&value!=Nil.INSTANCE)out=out.with(name,status(object(value,"actual Sentinel status"),encode));
        }
        for(String name:List.of("canceled","early_boundary_cancel")) {
            Value value=out.get(name);if(value!=null&&value!=Nil.INSTANCE)out=out.with(name,token(object(value,"actual cancel result"),encode));
        }
        Value speed=out.get("speed_configuration");if(speed!=null&&speed!=Nil.INSTANCE)out=out.with("speed_configuration",number(object(speed,"actual speed configuration"),"source_native_revision",encode,false));
        return out;
    }
    private static Obj token(Obj original,boolean encode) {
        Value value=original.get("tactical_daily_sentinel");
        return value==null||value==Nil.INSTANCE?original:original.with("tactical_daily_sentinel",status(object(value,"original native Sentinel token"),encode));
    }
    private static Obj status(Obj original,boolean encode) {
        Obj numeric=encode?original:number(original,"generation",false,true);
        SentinelObservation.decode(DriverJson.encode(numeric)); // Exact 20-field original numeric wire, including uint64 generation.
        return encode?number(original,"generation",true,true):numeric;
    }
    private static Obj number(Obj original,String field,boolean encode,boolean required) {
        Value value=original.get(field);if(value==null||value==Nil.INSTANCE) {
            require(!required,"required Life public numeric role absent/null: "+field);return original;
        }
        BigInteger exact;
        if(encode) {require(value instanceof IntegerValue,"exact Life numeric integer required: "+field);exact=((IntegerValue)value).value();}
        else {require(value instanceof Text text&&text.value().matches("0|[1-9][0-9]*")&&text.value().length()<=20,"canonical Life decimal string required: "+field);exact=new BigInteger(((Text)value).value());}
        require(exact.signum()>=0&&exact.compareTo(U64)<=0,"Life uint64 role outside its original numeric domain: "+field);
        return original.with(field,encode?new Text(exact.toString()):new IntegerValue(exact));
    }
    private static void safe(Value value) {
        if(value instanceof IntegerValue integer)require(integer.value().abs().compareTo(SAFE)<=0,"unsafe unknown Life numeric role; owning codec required");
        else if(value instanceof Obj object)object.members().values().forEach(RootLifeAdvancePublicResult::safe);
        else if(value instanceof Arr array)array.items().forEach(RootLifeAdvancePublicResult::safe);
        else if(value instanceof DecimalValue decimal)require(Double.isFinite(Double.parseDouble(decimal.token())),"finite original Life float required");
        // Double is used only for the finite predicate. Output always retains the original DecimalValue token.
    }
}
