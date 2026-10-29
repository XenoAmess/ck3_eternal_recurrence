package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPublicNumbers.Domain.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyObservations.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.BiFunction;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.military.monthlycaller.ArmyMonthlyCaller;

/** Complete typed Monthly/Regiment family installation; the loss-allocation stage has its separate single producer. */
public final class ArmyStrengthsMonthly {
    private ArmyStrengthsMonthly(){}
    public static void install(ArmyStrengthsFamilies.Registry registry,ArmyStrengthsPipeline pipeline,ExactRef actualJavaBundleSource){
        Objects.requireNonNull(registry);Objects.requireNonNull(pipeline);Objects.requireNonNull(actualJavaBundleSource);
        add(registry,Key.NATIVE_OWNER_RECALL_INPUTS_V1,ArmyStrengthsRecallCodec.Recall.class,(n,c)->ArmyStrengthsRecallCodec.decode(n),ArmyStrengthsRecallCodec::encode,
                List.of(rule("/owners_in_stored_order/*/native_activity_context_v1/matched_contexts_in_native_order/*/government_flags_40_raw",UNSIGNED_64),rule("/owners_in_stored_order/*/native_activity_context_v1/owner_prefix_inputs/government_flags_40_raw",UNSIGNED_64)),actualJavaBundleSource);
        add(registry,Key.NATIVE_MAA_RECRUITMENT_INPUTS_V1,MaaRecruitment.class,(n,c)->ArmyStrengthsMonthlyCodec.decodeMaa(n),ArmyStrengthsMonthlyCodec::encodeMaa,List.of(rule("/types_in_native_order/*/regular_personal_quote/resources_raw/*",SIGNED_64)),actualJavaBundleSource);
        add(registry,Key.OWNED_REGIMENTS_V1,OwnedRegiments.class,(n,c)->ArmyStrengthsMonthlyCodec.decodeOwned(n),ArmyStrengthsMonthlyCodec::encodeOwned,List.of(),actualJavaBundleSource);
        add(registry,Key.MONTHLY_CALLER_EFFECT_INPUTS_V1,ArmyMonthlyCaller.Input.class,(n,c)->ArmyMonthlyCaller.decodeInputs(n),ArmyMonthlyCaller::encodeInputs,List.of(rule("/current_date_storage_raw64",SIGNED_64)),actualJavaBundleSource);
        add(registry,Key.MONTHLY_FIRST_REMOVAL_CLEANUP_INPUTS_V1,FirstRemoval.class,(n,c)->ArmyStrengthsMonthlyCodec.decodeCleanup(n),ArmyStrengthsMonthlyCodec::encodeCleanup,List.of(),actualJavaBundleSource);
        add(registry,Key.MONTHLY_CURRENT_HELPER_DOMAIN_INPUTS_V1,HelperDomain.class,(n,c)->decodeHelperDomain(n),ArmyStrengthsMonthly::encodeHelperDomain,List.of(rule("/rows/*/domain_value_48_raw64",SIGNED_64)),actualJavaBundleSource);
        add(registry,Key.MONTHLY_CURRENT_HELPER_POINT_STORE_INPUTS_V1,HelperPointStore.class,(n,c)->decodeHelperPointStore(n),ArmyStrengthsMonthly::encodeHelperPointStore,List.of(),actualJavaBundleSource);
        add(registry,Key.CURRENT_MONTH_FIRST_REFILL_CALL_INPUTS_V1,MonthFirst.class,(n,c)->ArmyStrengthsMonthlyCodec.decodeMonthFirst(n),ArmyStrengthsMonthlyCodec::encodeMonthFirst,List.of(),actualJavaBundleSource);
        add(registry,Key.ACTUAL_LOSS_WRITER_OBSERVATIONS_V1,WriterFamily.class,(n,c)->ArmyStrengthsMonthlyObservationCodec.decodeWriter(n,currentRegimentIds(c)),ArmyStrengthsMonthlyObservationCodec::encodeWriter,writerRules(),actualJavaBundleSource);
        add(registry,Key.BATTLE_CASUALTY_OBSERVATIONS_V1,CasualtyFamily.class,(n,c)->ArmyStrengthsMonthlyObservationCodec.decodeCasualty(n),ArmyStrengthsMonthlyObservationCodec::encodeCasualty,casualtyRules(),actualJavaBundleSource);
    }
    private static List<Integer> currentRegimentIds(ArmyStrengths.RowContext context){
        if(context.regiments() instanceof Present<List<ArmyStrengths.Regiment>> p)return p.value().stream().map(ArmyStrengths.Regiment::armyRegimentId).toList();
        require(context.regiments() instanceof Missing<?>,"original absent regiment census is Missing, never an invented null/list");return List.of();
    }
    private static <T> void add(ArmyStrengthsFamilies.Registry registry,Key key,Class<T> type,BiFunction<JsonNode,ArmyStrengths.RowContext,T> decoder,Function<T,JsonNode> encoder,List<ArmyStrengthsPublicNumbers.Rule> rules,ExactRef source){
        Function<Field<T>,RawJson> nativeEncoder=field->new RawJson(ArmyJson.bytes(encoder.apply(field instanceof Present<T> p?p.value():null)));
        registry.register(key,type,(input,context)->{
            if(input instanceof Missing<?>)return key.defaultNullWhenMissing()?new NullValue<>():new Missing<>();
            if(input instanceof NullValue<?>)return new NullValue<>();
            T actual=decoder.apply(ArmyStrengthsCodec.parseValue(ArmyStrengthsCodec.present(input)),context);
            return actual==null?new NullValue<>():new Present<>(actual);
        },nativeEncoder,field->ArmyStrengthsPublicNumbers.encode(nativeEncoder.apply(field),rules),source);
    }
    public static HelperDomain decodeHelperDomain(JsonNode raw){return ArmyStrengthsMonthlyCodec.decodeDomain(raw);}
    public static JsonNode encodeHelperDomain(HelperDomain value){return ArmyStrengthsMonthlyCodec.encodeDomain(value);}
    public static HelperPointStore decodeHelperPointStore(JsonNode raw){return ArmyStrengthsMonthlyCodec.decodePoint(raw);}
    public static JsonNode encodeHelperPointStore(HelperPointStore value){return ArmyStrengthsMonthlyCodec.encodePoint(value);}
    private static ArmyStrengthsPublicNumbers.Rule rule(String path,ArmyStrengthsPublicNumbers.Domain domain){return new ArmyStrengthsPublicNumbers.Rule(path,domain);}
    private static List<ArmyStrengthsPublicNumbers.Rule> writerRules(){
        var out=new ArrayList<ArmyStrengthsPublicNumbers.Rule>();
        for(String key:List.of("oldest_available_sequence","latest_sequence","overwritten_events","unattributed_capture_failures","event_count","unbound_county_primary_direct_diagnostics_overwritten_v2"))out.add(rule("/"+key,UNSIGNED_64));
        for(WriterU64 key:WriterU64.values())out.add(rule("/events/*/"+key.wire(),UNSIGNED_64));
        for(WriterI64 key:WriterI64.values())out.add(rule("/events/*/"+key.wire(),SIGNED_64));
        out.add(rule("/events/*/request_raw",SIGNED_64));out.add(rule("/events/*/caller_return_rva",UNSIGNED_64));
        String supply="/events/*/supply_parent_context_v1/";
        for(String key:List.of("invocation_token","parent_invocation_token","callback_caller_return_rva","callback_entry_rva"))out.add(rule(supply+"invocation/"+key,UNSIGNED_64));
        out.add(rule(supply+"passed_date_raw64",UNSIGNED_64));out.add(rule(supply+"stock_at_writer_entry_raw",SIGNED_64));
        String residual="/events/*/residual_parent_context_v1/";
        for(String key:List.of("invocation_token","parent_invocation_token","allocator_caller_return_rva"))out.add(rule(residual+key,UNSIGNED_64));
        String primary="/events/*/county_primary_owner_at_writer_v1/";
        for(PrimaryU64 key:PrimaryU64.values())out.add(rule(primary+key.wire(),UNSIGNED_64));
        for(String event:List.of("phase_entry_event","writer_event","phase_prefix_roster_event"))tokenRules(out,primary+event+"/");
        directRules(out,"/events/*/county_primary_direct_owner_at_writer_v2/");
        directRules(out,"/unbound_county_primary_direct_diagnostics_v2/*/ownership/");return List.copyOf(out);
    }
    private static void tokenRules(List<ArmyStrengthsPublicNumbers.Rule> out,String path){out.add(rule(path+"clock_identity",UNSIGNED_64));out.add(rule(path+"sequence",UNSIGNED_64));}
    private static void directRules(List<ArmyStrengthsPublicNumbers.Rule> out,String path){for(DirectU64 key:DirectU64.values())out.add(rule(path+key.wire(),UNSIGNED_64));out.add(rule(path+"observed_date_raw64",UNSIGNED_64));tokenRules(out,path+"writer_event/");for(AssociationU64 key:AssociationU64.values())out.add(rule(path+"physical_associations/*/"+key.wire(),UNSIGNED_64));}
    private static List<ArmyStrengthsPublicNumbers.Rule> casualtyRules(){var out=new ArrayList<ArmyStrengthsPublicNumbers.Rule>();for(String key:List.of("oldest_available_sequence","latest_sequence","overwritten_events","event_count"))out.add(rule("/"+key,UNSIGNED_64));for(CasualtyU64 key:CasualtyU64.values())out.add(rule("/events/*/"+key.wire(),UNSIGNED_64));for(CasualtyI64 key:CasualtyI64.values())out.add(rule("/events/*/"+key.wire(),SIGNED_64));return List.copyOf(out);}
}
