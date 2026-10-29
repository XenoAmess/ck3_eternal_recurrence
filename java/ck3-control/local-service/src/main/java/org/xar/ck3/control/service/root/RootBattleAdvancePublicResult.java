package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceResultCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Pure representation of a separately verified original Route-window clock report. No read or authority. */
public final class RootBattleAdvancePublicResult {
    private static final BigInteger SAFE=BigInteger.valueOf(9007199254740991L);
    private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private RootBattleAdvancePublicResult() { }
    public static RawJson encodeClockReport(RawJson originalNumeric,OperationKey expectedStep) {
        Obj original=parse(originalNumeric,expectedStep);Obj converted=transform(original,true);safe(converted);
        RawJson result=new RawJson(DriverJson.encode(converted));
        require(parse(decodeClockReport(result,expectedStep),expectedStep).equals(original),
                "Battle public conversion changed original JSON type/content/decimal token");return result;
    }
    public static RawJson decodeClockReport(RawJson canonicalPublic,OperationKey expectedStep) {
        Obj original=parse(canonicalPublic,expectedStep);safe(original);
        return new RawJson(DriverJson.encode(transform(original,false)));
    }
    private static Obj parse(RawJson value,OperationKey expected) {
        Objects.requireNonNull(value);Objects.requireNonNull(expected);
        require(RouteContactSteps.supports(expected.value())&&RouteContactSteps.parse(expected.value()).days()>1,
                "canonical multi-day Route-window operation required");
        Obj root=DriverJson.object(value.bytes(),RawJson.MAXIMUM_BYTES);
        require(new Text(BattleAdvanceResultCodec.SCHEMA).equals(root.get("schema"))
                &&new Text(expected.value()).equals(root.get("step")),"exact actual Battle clock schema/operation required");
        return root;
    }
    private static Obj transform(Obj original,boolean encode) {
        Obj out=number(number(original,"revision",encode,true),"native_revision",encode,true);
        for(String field:List.of("armed_tactical_daily_sentinel","tactical_daily_sentinel")) {
            Value value=out.get(field);require(value!=null,"actual sentinel slot must retain null versus missing");
            if(value!=Nil.INSTANCE)out=out.with(field,status(object(value,field),encode));
        }
        Value decision=out.get("player_decision_boundary");
        if(decision!=null&&decision!=Nil.INSTANCE)out=out.with("player_decision_boundary",
                number(number(object(decision,"actual boundary"),"revision",encode,true),"native_revision",encode,true));
        Value actions=out.get("actions");require(actions instanceof Arr,"actual original clock children required");
        var rows=new ArrayList<Value>();
        for(Value value:((Arr)actions).items()) {
            Obj row=object(value,"actual clock child");
            require(row.get("step") instanceof Text step&&AdvancePrimitives.supports(new OperationKey(step.value())),
                    "actual finite clock child operation required");
            row=number(row,"ledger_sequence",encode,true);
            Value token=row.get("result");
            if(token!=null&&token!=Nil.INSTANCE) {
                Obj result=object(token,"actual native clock result");Value sentinel=result.get("tactical_daily_sentinel");
                if(sentinel!=null&&sentinel!=Nil.INSTANCE)result=result.with("tactical_daily_sentinel",status(object(sentinel,"original sentinel"),encode));
                result=number(result,"source_native_revision",encode,false);row=row.with("result",result);
            }
            rows.add(row);
        }
        return out.with("actions",new Arr(rows));
    }
    private static Obj status(Obj original,boolean encode) {
        Obj numeric=encode?original:number(original,"generation",false,true);
        SentinelObservation.decode(DriverJson.encode(numeric));
        return encode?number(original,"generation",true,true):numeric;
    }
    private static Obj number(Obj original,String field,boolean encode,boolean required) {
        Value value=original.get(field);
        if(value==null||value==Nil.INSTANCE){require(!required,"actual numeric role absent/null: "+field);return original;}
        BigInteger exact;
        if(encode){require(value instanceof IntegerValue,"exact original numeric integer required: "+field);exact=((IntegerValue)value).value();}
        else{require(value instanceof Text text&&text.value().matches("0|[1-9][0-9]*")&&text.value().length()<=(field.equals("generation")||field.equals("ledger_sequence")?20:4300),
                "canonical public decimal required: "+field);exact=new BigInteger(((Text)value).value());}
        require(exact.signum()>=0&&exact.toString().length()<=4300,"original nonnegative revision integer domain differs: "+field);
        if(field.equals("generation"))require(exact.compareTo(U64)<=0,"Sentinel uint64 generation out of range");
        if(field.equals("ledger_sequence"))require(exact.signum()>0&&exact.compareTo(SAFE)<=0,"actual canonical receipt sequence out of range");
        return original.with(field,encode?new Text(exact.toString()):new IntegerValue(exact));
    }
    private static void safe(Value value) {
        if(value instanceof IntegerValue integer)require(integer.value().abs().compareTo(SAFE)<=0,"unsafe unknown Battle integer role requires owning codec");
        else if(value instanceof Obj object)object.members().values().forEach(RootBattleAdvancePublicResult::safe);
        else if(value instanceof Arr array)array.items().forEach(RootBattleAdvancePublicResult::safe);
        else if(value instanceof DecimalValue decimal)require(Double.isFinite(Double.parseDouble(decimal.token())),"finite original Battle decimal required");
    }
}
