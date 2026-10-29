package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;

/** Source-bound signed low32 bucket calculation and demand-dependent provider selection. */
final class BattleProviderBucketCodec {
    private static final String BUCKET="provider_bucket_11f8", FALLBACK="native_fallback_5d1e0b0";
    private static final List<String> SELECTED=List.of("selected_definition_identity","selected_magic_raw","admitted","property_identity","property_block");
    private BattleProviderBucketCodec() { }
    static JsonNode normalize(JsonNode input,String field) {
        if(nil(input))return NullNode.instance;
        ObjectNode raw=exact(input,field,Set.of("status","ready","character_id","provider_present","provider_identity","carrier_present","key_2f8_raw",
                "denominator_5c68ce8_raw","bucket_index_raw","provider_count_1204_raw","provider_array_present","selection","selected_definition_identity",
                "selected_magic_raw","admitted","property_identity","property_block","reason"));
        Availability availability=availability(raw,field);ObjectNode out=object();availabilityFields(out,availability,"reason");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));
        out.set("property_block",properties(raw.get("property_block"),field+".property_block"));
        for(String key:List.of("provider_present","carrier_present","provider_array_present","admitted"))out.set(key,bool(raw.get(key),field+"."+key,true));
        for(String key:List.of("provider_identity","selected_definition_identity","property_identity","selection"))out.set(key,text(raw.get(key),field+"."+key,true,true));
        for(String key:List.of("key_2f8_raw","denominator_5c68ce8_raw","bucket_index_raw","provider_count_1204_raw"))out.set(key,number(raw.get(key),field+"."+key,32,false,true));
        out.set("selected_magic_raw",number(raw.get("selected_magic_raw"),field+".selected_magic_raw",32,true,true));
        String selection=string(out.get("selection"));require(selection==null || selection.equals(BUCKET)||selection.equals(FALLBACK),field,"invalid selection");
        Boolean provider=booleanValue(out,"provider_present"),carrier=booleanValue(out,"carrier_present");
        BigInteger key=integer(out,"key_2f8_raw"),denominator=integer(out,"denominator_5c68ce8_raw"),index=integer(out,"bucket_index_raw");
        if(!Boolean.TRUE.equals(provider)) {
            absent(out,field,List.of("provider_identity","carrier_present","key_2f8_raw","denominator_5c68ce8_raw","bucket_index_raw","provider_count_1204_raw","provider_array_present","selection"));absent(out,field,SELECTED);
        } else {
            require(!nil(out.get("provider_identity")),field,"loaded provider lacks actual identity");
            if(!Boolean.TRUE.equals(carrier))absent(out,field,List.of("key_2f8_raw","denominator_5c68ce8_raw"));
            else if(key==null)absent(out,field,List.of("denominator_5c68ce8_raw"));
            BigInteger expected=Boolean.FALSE.equals(carrier)?BigInteger.ZERO:null;
            if(Boolean.TRUE.equals(carrier)&&key!=null&&denominator!=null)expected=BigInteger.valueOf(scratchFactor(key.intValueExact(),denominator.intValueExact()));
            require(Objects.equals(index,expected),field,"bucket index differs from consumed signed low32 result");
        }
        BigInteger count=integer(out,"provider_count_1204_raw");String expectedSelection=null;
        if(index==null)absent(out,field,List.of("provider_count_1204_raw","provider_array_present"));
        else if(index.signum()<0){absent(out,field,List.of("provider_count_1204_raw","provider_array_present"));expectedSelection=FALLBACK;}
        else if(count==null)absent(out,field,List.of("provider_array_present"));
        else if(index.compareTo(count)>=0){absent(out,field,List.of("provider_array_present"));expectedSelection=FALLBACK;}
        else expectedSelection=BUCKET;
        require(Objects.equals(selection,expectedSelection),field,"selection differs from signed bucket/count gates");
        if(expectedSelection==null || (BUCKET.equals(expectedSelection)&&!trueValue(out,"provider_array_present")))absent(out,field,SELECTED);
        if(nil(out.get("selected_definition_identity")))absent(out,field,List.of("selected_magic_raw","admitted","property_identity","property_block"));
        BigInteger magic=integer(out,"selected_magic_raw");Boolean admitted=magic==null?null:magic.equals(BigInteger.valueOf(0x4744624fL));
        require(Objects.equals(booleanValue(out,"admitted"),admitted),field,"admission differs from selected definition magic");
        if(!Boolean.TRUE.equals(admitted))absent(out,field,List.of("property_identity","property_block"));
        boolean complete=Boolean.TRUE.equals(provider)&&index!=null&&expectedSelection!=null&&!nil(out.get("selected_definition_identity"))&&admitted!=null
                &&(!admitted || (!nil(out.get("property_identity"))&&propertiesReady(out.get("property_block"))&&nil(out.get("property_block").get("reason"))))&&availability.reason()==null;
        require(availability.ready()==complete,field,"readiness differs from consumed provider operands");return out;
    }
    private static void absent(ObjectNode out,String field,List<String> keys) { for(String key:keys)require(nil(out.get(key)),field,"undemanded native operand: "+key); }
    /** Exact native .3 arithmetic: signed64 intermediates intentionally wrap, division truncates toward zero. */
    static int scratchFactor(int numerator,int denominator) {
        long value=(long)numerator*100000L,divisor=(long)denominator*100000L;
        if(divisor==0)return (int)(0xffffffffL/100000L);
        long scaled;
        if(value>=-92233720368547L&&value<=92233720368547L)scaled=(value*100000L)/divisor;
        else if(Math.abs(divisor)>=10000000000L)scaled=value/(divisor/100000L);
        else {
            long quotient=value/100000L,integral=quotient*100000L,remainder=value-integral;
            long integralQuotient=integral/divisor,integralRemainder=integral-integralQuotient*divisor;
            scaled=(remainder*100000L)/divisor+(integralRemainder*100000L)/divisor+integralQuotient*100000L;
        }
        return (int)(scaled/100000L);
    }
}
