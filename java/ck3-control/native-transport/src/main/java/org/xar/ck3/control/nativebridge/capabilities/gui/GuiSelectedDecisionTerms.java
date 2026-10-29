package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Original selected-terms wire validation. This DATA grants no action or financing credit. */
public final class GuiSelectedDecisionTerms {
    private GuiSelectedDecisionTerms() { }
    public sealed interface Checked permits Unavailable, Available { RawJson original(); }
    public record Unavailable(String reason, RawJson original) implements Checked {
        public Unavailable { require(reason!=null&&!reason.isEmpty(),"actual unavailable terms reason required");Objects.requireNonNull(original); }
    }
    public record Quote(List<Long> resources, boolean nativeAffordable) {
        public Quote { resources=List.copyOf(resources);require(resources.size()==10,"actual ten signed resource amounts required"); }
    }
    public record Cooldown(boolean present, int current, Optional<Integer> expiry, boolean active) {
        public Cooldown { Objects.requireNonNull(expiry);require(present==expiry.isPresent()&&active==(present&&current<expiry.orElseThrow()),"actual cooldown consistency required"); }
    }
    public record Available(boolean canConfirm, boolean ordinaryLegalityObserved,
            Optional<String> confirmTooltip, Optional<String> requirementsDescription, Optional<String> costDescription,
            Optional<Quote> resourceQuote, Optional<Cooldown> cooldown, RawJson original) implements Checked {
        public Available { Objects.requireNonNull(confirmTooltip);Objects.requireNonNull(requirementsDescription);Objects.requireNonNull(costDescription);Objects.requireNonNull(resourceQuote);Objects.requireNonNull(cooldown);Objects.requireNonNull(original); }
    }
    private static final List<String> OBSERVED=List.of("requirements_bypass_observed","ordinary_legality_observed",
            "confirm_tooltip_available","requirements_description_available","cost_description_available","resource_quote_available","cooldown_observed");
    private static final List<String> VALUES=List.of("can_confirm","requirements_bypass_raw","ordinary_can_confirm","confirm_tooltip",
            "requirements_description","cost_description","resource_quote","cooldown");

    public static Checked decode(ObjectNode value, GuiModels.Context context, GuiModels.DecisionKey key) {
        Objects.requireNonNull(value);Objects.requireNonNull(context);Objects.requireNonNull(key);
        equal(value,"schema","ck3-selected-decision-terms-v1");yes(value,"read_only");no(value,"action_ready");no(value,"decision_confirm_invoked");
        require(context.build()==GuiModels.Build.CROZIER4,"selected terms must not cross native builds");
        equal(value,"game_version",context.build().version());
        require(text(value,"executable_sha256").equalsIgnoreCase(context.build().sha256()),"selected terms executable differs");
        equal(value,"decision_key",key.value());
        require(integer(value,"played_character_id").equals(context.before().frame().identity().player())
                &&integer(value,"date_raw").equals(context.before().frame().identity().dateRaw()),"selected terms changed actual actor/date");
        BigInteger epoch=integer(value,"capture_epoch");require(epoch.signum()>=0,"actual capture epoch required");
        String adapter=text(value,"context_adapter");
        require(Set.of("actual_empty_named_parameters_only","actual_create_hof_stock_default_parameter_only").contains(adapter),"actual selected parameter adapter required");
        RawJson original=PublicDataJson.encodeFullMaterial(value);
        if(!bool(value,"available")){
            require(adapter.equals("actual_empty_named_parameters_only")&&nil(value.get("stock_default_parameter")),"unavailable selected terms cannot claim stock parameter");
            no(value,"context_verified");for(String field:OBSERVED)no(value,field);
            for(String field:VALUES)require(nil(value.get(field)),"unavailable selected terms leaked "+field);
            return new Unavailable(text(value,"unavailable_reason"),original);
        }
        require(epoch.signum()>0,"positive actual selected terms capture epoch required");yes(value,"context_verified");
        BigInteger count=integer(value,"named_parameter_count");
        if(adapter.equals("actual_empty_named_parameters_only"))
            require(count.signum()==0&&nil(value.get("stock_default_parameter")),"empty selected parameter context differs");
        else {
            require(key.value().equals("create_hof_decision")&&count.equals(BigInteger.ONE),"actual stock-default selected context differs");
            ObjectNode parameter=StrictJson.object(value.get("stock_default_parameter"),Set.of("token_source","canonical_token","key","scope_kind","scope_flags","scope_payload","no_custom_controller"));
            require(parameter.size()==7,"exact actual stock parameter fields required");
            equal(parameter,"token_source","stock_detail_default_token_slot_0x5D4C0D8");
            BigInteger token=integer(parameter,"canonical_token");require(token.signum()>=0&&token.bitLength()<=32&&token.equals(integer(parameter,"key")),"actual stock token differs");
            require(integer(parameter,"scope_kind").equals(BigInteger.valueOf(4))&&integer(parameter,"scope_flags").signum()==0
                    &&integer(parameter,"scope_payload").equals(new BigInteger("4294967295")),"actual stock parameter scope differs");yes(parameter,"no_custom_controller");
        }
        boolean can=bool(value,"can_confirm"),bypass=bool(value,"requirements_bypass_observed");
        BigInteger bypassRaw=null;
        if(bypass){bypassRaw=integer(value,"requirements_bypass_raw");require(bypassRaw.signum()>=0&&bypassRaw.compareTo(BigInteger.valueOf(255))<=0,"actual bypass byte required");}
        else require(nil(value.get("requirements_bypass_raw")),"unobserved bypass must remain null");
        boolean ordinary=bypass&&bypassRaw.signum()==0;
        require(bool(value,"ordinary_legality_observed")==ordinary,"selected terms invented ordinary legality");
        require(ordinary?bool(value,"ordinary_can_confirm")==can:nil(value.get("ordinary_can_confirm")),"ordinary selected gate differs");
        Optional<String> tooltip=description(value,"confirm_tooltip"),requirements=description(value,"requirements_description"),cost=description(value,"cost_description");
        Optional<Quote> quote=Optional.empty();
        if(bool(value,"resource_quote_available")){
            ObjectNode row=StrictJson.object(value.get("resource_quote"),Set.of("raw_scale","resource_vector_raw","native_affordable"));
            require(row.size()==3&&integer(row,"raw_scale").equals(BigInteger.valueOf(100000)),"actual resource quote scale/fields required");
            JsonNode vector=row.get("resource_vector_raw");require(vector!=null&&vector.isArray()&&vector.size()==10,"actual ten-resource quote required");
            List<Long> amounts=new ArrayList<>();for(JsonNode amount:vector)amounts.add(StrictJson.integer(amount,Long.MIN_VALUE,Long.MAX_VALUE));
            quote=Optional.of(new Quote(amounts,bool(row,"native_affordable")));
        }else require(nil(value.get("resource_quote")),"unavailable resource quote must remain null");
        Optional<Cooldown> cooldown=Optional.empty();
        if(bool(value,"cooldown_observed")){
            ObjectNode clock=StrictJson.object(value.get("cooldown"),Set.of("present","current_counter_raw","expiry_raw","active","counter_unit"));
            require(clock.size()==5,"exact native selected cooldown required");equal(clock,"counter_unit","native_decision_clock_counter");
            boolean present=bool(clock,"present"),active=bool(clock,"active");int current=(int)StrictJson.integer(clock.get("current_counter_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE);
            Optional<Integer> expiry=present?Optional.of((int)StrictJson.integer(clock.get("expiry_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)):Optional.empty();
            if(!present)require(nil(clock.get("expiry_raw")),"absent selected cooldown invented expiry");
            cooldown=Optional.of(new Cooldown(present,current,expiry,active));
        }else require(nil(value.get("cooldown")),"unobserved cooldown must remain null");
        return new Available(can,ordinary,tooltip,requirements,cost,quote,cooldown,original);
    }
    private static Optional<String> description(ObjectNode row,String name){
        if(bool(row,name+"_available"))return Optional.of(text(row,name));
        require(nil(row.get(name)),"unavailable selected description must remain null");return Optional.empty();
    }
    private static boolean nil(JsonNode value){return value==null||value.isNull();}
    private static BigInteger integer(ObjectNode row,String name){JsonNode value=row.get(name);require(value!=null&&value.isIntegralNumber(),"actual selected terms integer required: "+name);return value.bigIntegerValue();}
    private static boolean bool(ObjectNode row,String name){JsonNode value=row.get(name);require(value!=null&&value.isBoolean(),"actual selected terms boolean required: "+name);return value.booleanValue();}
    private static String text(ObjectNode row,String name){JsonNode value=row.get(name);require(value!=null&&value.isTextual(),"actual selected terms text required: "+name);return value.textValue();}
    private static void equal(ObjectNode row,String name,String expected){require(text(row,name).equals(expected),"selected terms binding differs: "+name);}
    private static void yes(ObjectNode row,String name){require(bool(row,name),"actual selected terms proof required: "+name);}
    private static void no(ObjectNode row,String name){require(!bool(row,name),"selected terms cannot grant "+name);}
}
