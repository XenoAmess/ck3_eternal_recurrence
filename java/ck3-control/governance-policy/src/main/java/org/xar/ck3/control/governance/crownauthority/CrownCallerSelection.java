package org.xar.ck3.control.governance.crownauthority;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.*;

/** Explicit caller choice checked against its native quote. This pure material grants no source, writer or submit authority. */
public final class CrownCallerSelection {
    private CrownCallerSelection() { }
    public record Selection(String lawKey,List<CurrencyAmount> quotedCosts) {
        public Selection { Objects.requireNonNull(lawKey);quotedCosts=List.copyOf(quotedCosts); }
    }
    public static Selection select(Readback original,String lawKey) {
        Objects.requireNonNull(original);StrictJson.require(original.available()&&original.paused()&&original.readOnly()&&!original.advertised()
                &&original.groupKey().equals("crown_authority"),"private crown-law submit lacks its observed paused source");
        var selected=original.candidates().stream().filter(row->row.lawKey().equals(lawKey)).toList();
        StrictJson.require(selected.size()==1&&!selected.getFirst().active()&&selected.getFirst().canEnact(),"selected crown law lacks the native final can-enact result");
        // Final CanEnact is the engine verdict, including native overrides. No planner upgrade choice or component gate is added.
        var seen=new java.util.HashSet<Currency>();var costs=new ArrayList<CurrencyAmount>();
        for(var cost:selected.getFirst().costs()) {
            StrictJson.require(seen.add(cost.currency())&&cost.costRaw().signum()>=0&&cost.costRaw().compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"invalid actual native currency cost");
            costs.add(new CurrencyAmount(cost.currency(),cost.costRaw()));
        }
        return new Selection(lawKey,costs);
    }
    /** Only supplied limits survive. Native rejection for an insufficient or omitted limit remains native business behavior. */
    public static List<CurrencyAmount> limits(ObjectNode budgets) {
        Objects.requireNonNull(budgets);var result=new ArrayList<CurrencyAmount>();
        for(var entry:budgets.properties()) {
            var currency=Currency.fromWire(entry.getKey());var value=StrictJson.integer(entry.getValue(),BigInteger.ZERO,BigInteger.valueOf(Long.MAX_VALUE));
            result.add(new CurrencyAmount(currency,value));
        }
        return List.copyOf(result);
    }
    public static boolean isCaller(ObjectNode arguments) {
        if(!arguments.has("caller_budgets"))return false;
        StrictJson.object(arguments,Set.of("readback","law_key","caller_budgets","caller_request_id"));return true;
    }
    public static List<CurrencyAmount> quotedCosts(ObjectNode arguments,Readback readback) {
        return isCaller(arguments)?select(readback,StrictJson.text(arguments.get("law_key"))).quotedCosts():CrownAuthorityPolicy.choose(readback).budgetsRaw();
    }
    public static Choice callerChoice(Readback readback,ObjectNode arguments) {
        var selected=select(readback,StrictJson.text(arguments.get("law_key")));var limits=limits((ObjectNode)arguments.get("caller_budgets"));
        var costs=new java.util.EnumMap<Currency,BigInteger>(Currency.class);selected.quotedCosts().forEach(value->costs.put(value.currency(),value.amountRaw()));
        var balances=new java.util.EnumMap<Currency,BigInteger>(Currency.class);readback.resources().forEach(value->balances.put(value.currency(),value.amountRaw()));
        var post=new ArrayList<CurrencyAmount>();for(var amount:limits)post.add(new CurrencyAmount(amount.currency(),balances.get(amount.currency()).subtract(costs.getOrDefault(amount.currency(),BigInteger.ZERO))));
        return new Choice(Status.READY,"explicit_public_caller_native_final_law_and_limits",readback.activeLawKey(),selected.lawKey(),limits,post);
    }
}
