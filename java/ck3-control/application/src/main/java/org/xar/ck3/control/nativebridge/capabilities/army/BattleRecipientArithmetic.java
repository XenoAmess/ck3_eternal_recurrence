package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Pure current recipient arithmetic. It neither mutates its input nor touches native caches. */
public final class BattleRecipientArithmetic {
    public record Result(BigInteger valueQ64, Boolean applicable, boolean calculationReady) { }
    private record LinkedValue(BigInteger value, Boolean found) { }
    private record FamilyValue(BigInteger key, int keyId, int kind, long value) { }
    private record KeyId(BigInteger key, int keyId) { }
    private record Threshold(int priority, long value) { }
    private record Link(BigInteger object, boolean valid) { }
    private static final BigInteger MASK64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final BigInteger MASK32=BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    private static final BigInteger TWO=BigInteger.valueOf(2), FOUR=BigInteger.valueOf(4);
    private static final BigInteger GDBO=BigInteger.valueOf(0x4744624fL);
    private static final long Q=100000L, MUL_BOUND=3037000499L;
    private BattleRecipientArithmetic() { }

    /** Input has already passed BattleRecipientInputsCodec's exact native JSON boundary. */
    public static Result absent(ObjectNode normalized) {
        ObjectNode raw=normalized==null?JsonNodeFactory.instance.objectNode():normalized;
        Demand demand=new Demand();
        Boolean carrier=booleanValue(raw.get("carrier_present"));
        if(Boolean.TRUE.equals(carrier))return new Result(null,false,false);
        if(!Boolean.FALSE.equals(carrier))return new Result(null,null,false);
        BigInteger cache=demand.integer(raw.get("associated_cache_440"));
        if(cache==null||cache.intValue()==0)return new Result(null,true,false);

        JsonNode mapping=raw.get("cached_map_430");
        Integer count=demand.count(mapping);
        LinkedHashMap<BigInteger,Long> assignments=new LinkedHashMap<>();
        JsonNode traits=raw.get("trait_ids");
        Integer traitCount=count!=null&&count>0?demand.count(traits):null;
        if(count!=null&&count>0) {
            JsonNode entries=get(mapping,"entries");
            int observed=observedExtent(entries,count);
            for(int index=0;index<observed;index++) {
                JsonNode value=demand.item(entries,index);
                if(!(value instanceof ObjectNode row)){demand.gap();continue;}
                BigInteger key=demand.word(row.get("key_object"));
                BigInteger trait=demand.integer(row.get("trait_id_u32"));
                Boolean admitted=traitCount!=null&&trait!=null
                        ?contains(demand,traits,traitCount,trait.and(MASK32),false):null;
                if(!Boolean.TRUE.equals(admitted)||key==null)continue;
                Long assigned=demand.q64(row.get("value_q64"));
                JsonNode members=raw.get("membership_ids");
                Integer memberCount=demand.count(members);
                if(!initialized(demand,raw.get("membership_header_guard_raw")))memberCount=null;
                Boolean matched=null;
                if(memberCount!=null&&memberCount==0)matched=false;
                else if(memberCount!=null) {
                    LinkedValue linked=linkedValue(demand,raw.get("cached_map_458"),key);
                    if(BigInteger.ZERO.equals(linked.value()))matched=false;
                    else if(linked.value()!=null)matched=contains(demand,members,memberCount,linked.value(),true);
                }
                if(Boolean.TRUE.equals(matched)) {
                    Long multiplier=demand.q64(raw.get("member_multiplier_q64"));
                    assigned=assigned!=null&&multiplier!=null?fixedMultiply(assigned,multiplier,false):null;
                } else if(matched==null)assigned=null;
                assignments.put(key,assigned);
            }
            if(observed<count)demand.gap();
        }
        Long base;
        if("inline_context_5d67b90".equals(textValue(raw.get("aggregate_context_selection")))
                &&!initialized(demand,raw.get("aggregate_context_guard_raw")))base=null;
        else base=aggregate25d(demand,raw.get("aggregate_properties"));
        boolean sumComplete=!demand.missing;
        Long lower=demand.q64(raw.get("clamp_lower_q64"));
        Long upper=demand.q64(raw.get("clamp_upper_q64"));
        Long summed=sumComplete?base:null;
        for(Long assignment:assignments.values())summed=summed!=null&&assignment!=null?summed+assignment:null;
        Long result=summed!=null&&lower!=null&&upper!=null?(summed<lower?lower:Math.min(summed,upper)):null;
        boolean ready=!demand.missing&&count!=null&&result!=null;
        return new Result(ready?BigInteger.valueOf(result):null,true,ready);
    }

    /** Source-identical family reduction, temporary maps, and the shared cached downstream calculation. */
    public static Result uncached(ObjectNode normalized) {
        ObjectNode raw=normalized==null?JsonNodeFactory.instance.objectNode():normalized;
        Demand demand=new Demand();
        Boolean carrier=booleanValue(raw.get("carrier_present"));
        if(Boolean.TRUE.equals(carrier))return new Result(null,false,false);
        if(!Boolean.FALSE.equals(carrier))return new Result(null,null,false);
        BigInteger cache=demand.integer(raw.get("associated_cache_440"));
        if(cache!=null&&cache.intValue()!=0)return new Result(null,false,false);
        Reducer reducer=new Reducer(demand,raw);
        LinkedHashMap<BigInteger,BigInteger> positive=new LinkedHashMap<>(),negative=new LinkedHashMap<>();
        LinkedHashMap<BigInteger,ObjectNode> objects=new LinkedHashMap<>();
        for(FamilyValue pair:family(demand,raw,raw.get("seed_family")))reducer.offer(pair,1);
        JsonNode contexts=raw.get("active_context");
        Integer contextCount=null;
        for(String name:List.of("active_objects","removed_objects")) {
            boolean active=name.equals("active_objects");
            JsonNode vector=raw.get(name);Integer count=demand.count(vector);
            if(count==null)continue;
            if(count<0){demand.gap();continue;}
            JsonNode entries=get(vector,"entries");int observed=observedExtent(entries,count);
            for(int index=0;index<observed;index++) {
                JsonNode value=demand.item(entries,index);
                if(!(value instanceof ObjectNode row)){demand.gap();continue;}
                BigInteger pointer=demand.word(row.get("object"));
                if(pointer==null)continue;
                objects.put(pointer,row);
                List<FamilyValue> pairs=family(demand,raw,row.get("intrinsic_family"));
                if(pairs.isEmpty())continue;
                Long multiplier=null;int priority=2;
                if(active) {
                    if(contextCount==null)contextCount=demand.count(contexts);
                    ObjectNode matched=null;
                    int extent=contextCount==null?0:Math.max(contextCount,0);
                    JsonNode contextEntries=get(contexts,"entries");
                    int contextObserved=observedExtent(contextEntries,extent);
                    for(int ci=0;ci<contextObserved;ci++) {
                        JsonNode cv=demand.item(contextEntries,ci);
                        if(!(cv instanceof ObjectNode cr)){demand.gap();continue;}
                        BigInteger cp=demand.word(cr.get("object"));
                        if(pointer.equals(cp)){matched=cr;break;}
                    }
                    if(matched==null&&contextObserved<extent)demand.gap();
                    if(matched==null)continue;
                    BigInteger flag=demand.integer(matched.get("flag_u8"));
                    if(flag==null)continue;
                    priority=FOUR.equals(flag)?0:3;
                    multiplier=demand.q64(raw.get(FOUR.equals(flag)?"active_flag4_multiplier_q64":"active_other_multiplier_q64"));
                }
                for(FamilyValue pair:pairs) {
                    long q=pair.value();
                    if(active){if(multiplier==null)continue;q=fixedMultiply(q,multiplier,true);}
                    if(reducer.offer(new FamilyValue(pair.key(),pair.keyId(),pair.kind(),q),priority))
                        (active?positive:negative).put(pair.key(),pointer);
                }
            }
            if(observed<count)demand.gap();
        }
        LinkedHashMap<BigInteger,Entry> materialized=new LinkedHashMap<>();
        for(int kind:List.of(2,1))for(Entry row:reducer.group(kind))materialized.put(row.key,row);
        ArrayNode map430=JsonNodeFactory.instance.arrayNode(),map458=JsonNodeFactory.instance.arrayNode();
        for(Entry row:materialized.values()) {
            ObjectNode item=map430.addObject();item.put("bucket_index",map430.size()-1);item.put("key_object",row.key);
            item.put("trait_id_u32",Integer.toUnsignedLong(row.keyId));item.put("value_q64",row.kind==2?-row.value:row.value);
            Link p=linked(demand,raw,objects,positive,row.key,"positive");
            Link n=p.valid()?linked(demand,raw,objects,negative,row.key,"negative"):new Link(negative.get(row.key),false);
            if(p.valid()&&n.valid()) {
                Entry current=first(reducer.group(row.kind),row.key);
                if(current!=null&&current.priority==2) {
                    BigInteger pointer=demand.word(raw.get("positive_fallback_object"));
                    BigInteger magic=demand.integer(raw.get("positive_fallback_magic_u32"));
                    p=new Link(pointer,GDBO.equals(magic));
                }
            }
            if(p.valid()&&p.object()!=null){ObjectNode link=map458.addObject();link.put("bucket_index",map458.size()-1);link.put("key_object",row.key);link.put("value_u64",p.object());}
        }
        ObjectNode derived;
        if(raw.get("downstream_inputs") instanceof ObjectNode input)derived=input.deepCopy();
        else{demand.gap();derived=JsonNodeFactory.instance.objectNode();}
        derived.put("carrier_present",false);derived.put("associated_cache_440",1);
        ObjectNode c430=derived.putObject("cached_map_430");c430.put("count",map430.size());c430.set("entries",map430);
        ObjectNode c458=derived.putObject("cached_map_458");c458.put("count",map458.size());c458.set("entries",map458);
        Result downstream=absent(derived);
        boolean ready=!demand.missing&&downstream.calculationReady();
        return new Result(ready?downstream.valueQ64():null,true,ready);
    }

    /** battle_trait_numeric_inputs_12003.native_fixed_mul_q_12003: divide signed minimum. */
    public static long cachedFixedMultiplyQ64(long a,long b){return fixedMultiply(a,b,false);}
    /** battle_person_uncached_recipient_12003.native_uncached_fixed_mul_q_12003: divide signed maximum. */
    public static long uncachedFixedMultiplyQ64(long a,long b){return fixedMultiply(a,b,true);}
    /** The source kernels differ in which signed operand is divided in the decomposed branch. */
    private static long fixedMultiply(long a,long b,boolean divideMaximum) {
        if(a>=-MUL_BOUND&&a<=MUL_BOUND&&b>=-MUL_BOUND&&b<=MUL_BOUND)return (a*b)/Q;
        long lo=Math.min(a,b),hi=Math.max(a,b),divided=divideMaximum?hi:lo,other=divideMaximum?lo:hi;
        long quotient=divided/Q;
        long remainder=divided-quotient*Q;
        return quotient*other+(remainder*other)/Q;
    }

    private static final class Demand {
        private boolean missing;
        void gap(){missing=true;}
        BigInteger integer(JsonNode n){if(n!=null&&n.isIntegralNumber())return n.bigIntegerValue();gap();return null;}
        Long q64(JsonNode n){BigInteger value=integer(n);return value==null?null:value.longValue();}
        BigInteger word(JsonNode n) {
            if(n!=null&&n.isTextual()) {
                String token=n.textValue();
                if(token.startsWith("0x")||token.startsWith("0X"))try{return new BigInteger(token.substring(2),16).and(MASK64);}catch(NumberFormatException ignored){/* Demand below records the unavailable operand. */}
            }
            BigInteger value=integer(n);return value==null?null:value.and(MASK64);
        }
        Integer count(JsonNode row){if(!(row instanceof ObjectNode)){gap();return null;}BigInteger n=integer(row.get("count"));return n==null?null:n.intValue();}
        JsonNode item(JsonNode rows,int index){if(rows instanceof ArrayNode a&&index>=0&&index<a.size())return a.get(index);gap();return null;}
    }
    private static int observedExtent(JsonNode rows,int count){return rows instanceof ArrayNode a?Math.min(Math.max(count,0),a.size()):0;}
    private static JsonNode get(JsonNode row,String name){return row instanceof ObjectNode?row.get(name):null;}
    private static Boolean booleanValue(JsonNode value){return value!=null&&value.isBoolean()?value.booleanValue():null;}
    private static String textValue(JsonNode value){return value!=null&&value.isTextual()?value.textValue():null;}
    private static boolean initialized(Demand demand,JsonNode raw){BigInteger value=demand.integer(raw);if(value==null)return false;int guard=value.intValue();if(guard==0||guard==-1){demand.gap();return false;}return true;}
    private static Long aggregate25d(Demand demand,JsonNode container) {
        Integer count=demand.count(container);if(count==null)return null;if(count==0)return 0L;if(count<0){demand.gap();return null;}
        JsonNode keys=get(container,"keys_u16");int offset=0,remaining=count;
        while(remaining>0){int half=remaining>>1,index=offset+half;BigInteger key=demand.integer(demand.item(keys,index));if(key==null)return null;if(key.and(BigInteger.valueOf(65535)).intValue()<0x25d)offset+=remaining-half;remaining=half;}
        if(offset==count)return 0L;BigInteger key=demand.integer(demand.item(keys,offset));if(key==null)return null;if(key.and(BigInteger.valueOf(65535)).intValue()>0x25d)return 0L;
        return demand.q64(demand.item(get(container,"values_q64"),offset));
    }
    private static Boolean contains(Demand demand,JsonNode row,int count,BigInteger key,boolean fullWord) {
        if(count<0){demand.gap();return null;}JsonNode values=get(row,fullWord?"values_u64":"values_u32");boolean missing=false;int observed=observedExtent(values,count);
        for(int index=0;index<observed;index++){JsonNode raw=demand.item(values,index);BigInteger value=fullWord?demand.word(raw):demand.integer(raw);if(value==null)missing=true;else if((fullWord?value:value.and(MASK32)).equals(key))return true;}
        if(observed<count){demand.gap();missing=true;}return missing?null:false;
    }
    private static LinkedValue linkedValue(Demand demand,JsonNode mapping,BigInteger key) {
        Integer count=demand.count(mapping);if(count==null)return new LinkedValue(null,null);if(count<=0)return new LinkedValue(BigInteger.ZERO,false);
        JsonNode entries=get(mapping,"entries");boolean missing=false;int observed=observedExtent(entries,count);
        for(int index=0;index<observed;index++){JsonNode value=demand.item(entries,index);if(!(value instanceof ObjectNode row)){demand.gap();missing=true;continue;}BigInteger rowKey=demand.word(row.get("key_object"));if(rowKey==null)missing=true;else if(rowKey.equals(key))return new LinkedValue(demand.word(row.get("value_u64")),true);}
        if(observed<count){demand.gap();missing=true;}return missing?new LinkedValue(null,null):new LinkedValue(BigInteger.ZERO,false);
    }
    private static List<FamilyValue> family(Demand demand,ObjectNode raw,JsonNode value) {
        if(!(value instanceof ObjectNode input)){demand.gap();return List.of();}
        List<FamilyValue> rows=new ArrayList<>();
        for(int kind:List.of(1,2)) {
            JsonNode vector=input.get(kind==1?"first":"second");Integer count=demand.count(vector);if(count==null)continue;if(count<0){demand.gap();continue;}
            JsonNode records=get(vector,"records");int observed=observedExtent(records,count);
            for(int index=0;index<observed;index++){JsonNode entry=demand.item(records,index);if(!(entry instanceof ObjectNode row)){demand.gap();continue;}BigInteger marker=demand.integer(row.get("marker_u8"));if(marker==null)continue;BigInteger key=demand.word(TWO.equals(marker)?row.get("key_object"):raw.get("fallback_key_object"));BigInteger id=demand.integer(TWO.equals(marker)?row.get("key_id_i32"):raw.get("fallback_key_id_i32"));Long q=demand.q64(row.get("value_q64"));if(key!=null&&id!=null&&q!=null)rows.add(new FamilyValue(key,id.intValue(),kind,q));}
            if(observed<count)demand.gap();
        }
        List<KeyId> keys=new ArrayList<>();for(FamilyValue row:rows)keys.add(new KeyId(row.key(),row.keyId()));keys.sort(Comparator.comparingInt(KeyId::keyId));
        List<KeyId> unique=new ArrayList<>();for(KeyId key:keys)if(unique.isEmpty()||!unique.getLast().key().equals(key.key()))unique.add(key);
        List<FamilyValue> out=new ArrayList<>();for(KeyId key:unique){int selectedKind=0;long selected=0;for(FamilyValue row:rows)if(row.key().equals(key.key())&&row.value()>selected){selectedKind=row.kind();selected=row.value();}out.add(new FamilyValue(key.key(),key.keyId(),selectedKind,selected));}return List.copyOf(out);
    }
    private static Link linked(Demand demand,ObjectNode raw,Map<BigInteger,ObjectNode> objects,Map<BigInteger,BigInteger> table,BigInteger key,String prefix) {
        BigInteger pointer=table.get(key),magic;
        if(pointer==null){pointer=demand.word(raw.get(prefix+"_fallback_object"));magic=demand.integer(raw.get(prefix+"_fallback_magic_u32"));}
        else magic=demand.integer(objects.get(pointer).get("magic_u32"));
        return new Link(pointer,GDBO.equals(magic));
    }
    private static final class Entry {
        final BigInteger key;final int keyId,kind;long value;int priority;
        Entry(FamilyValue v,int priority){key=v.key();keyId=v.keyId();kind=v.kind();value=v.value();this.priority=priority;}
    }
    private static Entry first(List<Entry> rows,BigInteger key){for(Entry row:rows)if(row.key.equals(key))return row;return null;}
    private static final class Reducer {
        private final Demand demand;private final ObjectNode raw;
        private final List<Entry> negative=new ArrayList<>(),positive=new ArrayList<>(),seeds=new ArrayList<>();
        private Threshold negativeThreshold=new Threshold(4,0),positiveThreshold=new Threshold(4,0);
        Reducer(Demand demand,ObjectNode raw){this.demand=demand;this.raw=raw;}
        List<Entry> group(int kind){return kind==2?negative:positive;}
        void sort(int kind){group(kind).sort((a,b)->{int c=Integer.compare(a.priority,b.priority);if(c==0)c=Long.compare(b.value,a.value);return c==0?Integer.compare(b.keyId,a.keyId):c;});}
        void remove(int kind,BigInteger key){group(kind).removeIf(r->r.key.equals(key));sort(kind);}
        void append(Entry candidate){Entry seed=first(seeds,candidate.key);long value=candidate.value;if(seed!=null&&seed.kind==candidate.kind){Long boost=demand.q64(raw.get("seed_boost_multiplier_q64"));if(boost!=null)value+=fixedMultiply(seed.value,boost,true);}Entry row=new Entry(new FamilyValue(candidate.key,candidate.keyId,candidate.kind,value),candidate.priority);group(candidate.kind).add(row);sort(candidate.kind);}
        boolean offer(FamilyValue v,int priority) {
            int kind=v.kind();if(kind==0)return false;Entry candidate=new Entry(v,priority);if(priority==1)seeds.add(candidate);
            Entry existing=first(negative,v.key());if(existing==null)existing=first(positive,v.key());BigInteger cap=demand.integer(raw.get("cap_i32"));if(cap==null)return false;
            List<Entry> rows=group(kind);boolean room=rows.size()<cap.intValue();
            if(existing!=null&&existing.priority==1&&priority!=1&&(room||kind==existing.kind)){remove(existing.kind,v.key());append(candidate);return true;}
            Threshold threshold=kind==2?negativeThreshold:positiveThreshold;if(threshold.priority()<priority||threshold.priority()==priority&&threshold.value()>=v.value())return false;
            Entry worst=!room&&!rows.isEmpty()?rows.getLast():null;
            if(worst!=null&&(worst.priority<priority||worst.priority==priority&&worst.value>=v.value())) {
                if(worst.priority!=priority||worst.value!=v.value()||worst.key.equals(v.key()))return false;
                int index=0;while(index<rows.size()){Entry row=rows.get(index);if(row.priority==priority&&row.value==v.value()){rows.set(index,rows.getLast());rows.removeLast();}else index++;}sort(kind);Threshold next=new Threshold(priority,v.value());if(kind==2)negativeThreshold=next;else positiveThreshold=next;return false;
            }
            if(existing!=null){if(existing.priority<priority||existing.priority==priority&&existing.value>=v.value())return false;if(existing.kind==kind){existing.value=v.value();existing.priority=priority;sort(kind);return true;}remove(existing.kind,v.key());}
            if(worst!=null)remove(kind,worst.key);append(candidate);return true;
        }
    }
}
