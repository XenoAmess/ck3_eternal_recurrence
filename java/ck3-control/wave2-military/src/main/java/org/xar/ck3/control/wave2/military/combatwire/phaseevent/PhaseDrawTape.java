package org.xar.ck3.control.wave2.military.combatwire.phaseevent;

import static org.xar.ck3.control.wave2.military.combatwire.phaseevent.PhaseJson.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;

/** Explicit draw tape. Native candidate selection deliberately retains signed-int32 overflow semantics. */
final class PhaseDrawTape {
    final List<Integer> draws; int position; final ArrayNode records=arr();
    PhaseDrawTape(List<Integer> draws){this.draws=List.copyOf(draws);for(Integer draw:this.draws)require(draw!=null&&draw>=0,"draw must be nonnegative 31-bit integer");}
    static int nativeWeight(long raw){long quotient=raw/100000,remainder=raw%100000;if(raw>0&&remainder!=0)quotient++;return (int)quotient;}
    ArrayNode weights(List<Long> values){ArrayNode out=arr();values.forEach(out::add);return out;}
    int next(String purpose){require(position<draws.size(),"draw tape exhausted while selecting "+purpose);return draws.get(position++);}
    int take(String purpose,List<Long> weights){BigInteger total=BigInteger.ZERO;for(long weight:weights)if(weight>0)total=total.add(BigInteger.valueOf(weight));if(total.signum()==0)return -1;int draw=next(purpose);BigInteger remainder=new java.math.BigDecimal(Math.scalb((double)draw,-31)*total.doubleValue()).toBigInteger();int selected=-1;for(int i=0;i<weights.size();i++){long weight=weights.get(i);if(weight<=0)continue;if(remainder.compareTo(BigInteger.valueOf(weight))<0){selected=i;break;}remainder=remainder.subtract(BigInteger.valueOf(weight));}require(selected>=0,"weighted choice failed");ObjectNode record=obj().put("ordinal",position-1).put("purpose",purpose).put("random31",draw).put("selected_index",selected);record.set("weights_source_order",weights(weights));records.add(record);return selected;}
    int takeNative(String purpose,List<Long> weights){if(weights.isEmpty())return -1;int total=0;ArrayNode intWeights=arr();for(long weight:weights){int converted=nativeWeight(weight);total+=converted;intWeights.add(converted);}int draw=next(purpose),selected=0;Integer remainder=null;String mode;if(total>0){int left=draw%total;for(int i=0;i<weights.size();i++){left-=nativeWeight(weights.get(i));if(left<0){selected=i;break;}}remainder=left;mode="positive_total_weighted";}else{selected=draw%weights.size();mode="nonpositive_total_uniform";}ObjectNode record=obj().put("ordinal",position-1).put("purpose",purpose).put("random31",draw).put("total_int32",total).put("selection_mode",mode).put("selected_index",selected);record.set("weights_raw_compacted_order",weights(weights));record.set("weights_int32_compacted_order",intWeights);if(remainder==null)record.putNull("terminal_remainder_int32");else record.put("terminal_remainder_int32",remainder);records.add(record);return selected;}
    ObjectNode toJson(){ObjectNode out=obj().put("consumed_count",position).put("remaining_count",draws.size()-position);ArrayNode provided=out.putArray("provided");draws.forEach(provided::add);out.set("records",records.deepCopy());return out;}
}
