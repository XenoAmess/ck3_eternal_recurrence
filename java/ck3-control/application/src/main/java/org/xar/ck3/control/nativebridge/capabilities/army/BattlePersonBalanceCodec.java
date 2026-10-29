package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;

/** Source-minimum 2BCA620 classifier and equality-before-fallback provider path. */
final class BattlePersonBalanceCodec {
    private BattlePersonBalanceCodec() { }
    static JsonNode normalize(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;
        ObjectNode out=start(raw,field,"character_id","balance_source","classifier","provider_selection");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));
        String name=field+".balance_source";ObjectNode in=shape(raw.get("balance_source"),name,"component_present","balance_raw_q64","numeric_balance_q64","reason"),balance=object();
        bools(in,balance,name,"component_present");nums(in,balance,name,64,false,"balance_raw_q64","numeric_balance_q64");texts(in,balance,name,"reason");
        Boolean present=booleanValue(balance.get("component_present"));BigInteger value=Boolean.TRUE.equals(present)?integer(balance.get("balance_raw_q64")):Boolean.FALSE.equals(present)?BigInteger.ZERO:null;
        require(Boolean.TRUE.equals(present)||nil(balance.get("balance_raw_q64")),name,"absent/unknown component contains undemanded raw balance");same(balance.get("numeric_balance_q64"),value,name,"numeric balance differs from actual component/known absence");out.set("balance_source",balance);
        name=field+".classifier";JsonNode classifierRaw=raw.get("classifier");ObjectNode classifier=start(classifierRaw,name,"selection","index_raw_i32");texts(classifierRaw,classifier,name,"selection");nums(classifierRaw,classifier,name,32,false,"index_raw_i32");
        String selected=value==null?null:value.signum()>=0?"nonnegative_balance_minus_one":"negative_balance_income_unobserved";BigInteger index=value!=null&&value.signum()>=0?BigInteger.ONE.negate():null;
        same(classifier.get("selection"),selected,name,"minimum balance classification differs");same(classifier.get("index_raw_i32"),index,name,"minimum balance index differs");
        require(!"negative_balance_income_unobserved".equals(selected)||is(classifier.get("reason"),"negative_balance_income_2bca4e0"),name,"negative balance must retain actual income gap");
        require(classifier.get("ready").booleanValue()==(BigInteger.ONE.negate().equals(index)&&nil(balance.get("reason"))&&nil(classifier.get("reason"))),name,"classifier readiness differs");out.set("classifier",classifier);
        name=field+".provider_selection";JsonNode providerRaw=raw.get("provider_selection");ObjectNode provider=start(providerRaw,name,"provider_loaded","count_raw","selection","definition_identity","definition_magic_u32","admitted","pc");
        bools(providerRaw,provider,name,"provider_loaded","admitted");nums(providerRaw,provider,name,32,false,"count_raw");nums(providerRaw,provider,name,32,true,"definition_magic_u32");texts(providerRaw,provider,name,"selection","definition_identity");provider.set("pc",pc(providerRaw.get("pc"),name+".pc"));
        String selection=null;
        if(index==null) {
            for(String key:new String[]{"count_raw","selection","definition_identity","definition_magic_u32","admitted"})require(nil(provider.get(key)),name,"unavailable classifier contains downstream provider operands");
            require(absentPc(provider.get("pc")),name,"unavailable classifier contains selected PC");
        } else if(Boolean.TRUE.equals(booleanValue(provider.get("provider_loaded")))) {
            BigInteger count=integer(provider.get("count_raw"));if(count!=null)selection=index.equals(count)?"provider_1690_equality_sentinel":"global_fallback_5d1e0b0";
        } else require(nil(provider.get("count_raw")),name,"unloaded provider contains count");
        same(provider.get("selection"),selection,name,"provider equality-before-fallback differs");
        Boolean admitted=selection!=null&&!nil(provider.get("definition_magic_u32"))?eq(provider.get("definition_magic_u32"),0x4744624fL):null;
        same(provider.get("admitted"),admitted,name,"provider Definition magic admission differs");require(Boolean.TRUE.equals(admitted)||absentPc(provider.get("pc")),name,"nonadmitted provider contains PC40");
        boolean complete=classifier.get("ready").booleanValue()&&Boolean.TRUE.equals(booleanValue(provider.get("provider_loaded")))&&selection!=null&&!nil(provider.get("definition_identity"))&&admitted!=null&&(!admitted||pcReady(provider.get("pc")));
        ready(provider,complete,name);out.set("provider_selection",provider);
        require(out.get("ready").booleanValue()==(classifier.get("ready").booleanValue()&&provider.get("ready").booleanValue()),field,"whole-source readiness differs from classifier/provider");return out;
    }
}
