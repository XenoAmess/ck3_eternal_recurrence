package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual creator configuration and fixed-setting observation. Signed raw values have no invented scale. */
public record CurrentCourtierConfigurationSource(CurrentCourtierControls.Product product,CurrentCourtierConfiguration.Setting setting,
        boolean confirmationLayerFound,boolean creatorWindowFound,boolean modalFound,boolean panelFound,
        boolean windowVisible,boolean windowEnabled,Optional<Boolean> nativeDefinitionFound,
        Optional<Boolean> nativeShown,Optional<Boolean> nativeValid,boolean executeAdmissible,
        Optional<Configuration> configuration,boolean numericComplete){
    public record Configuration(Optional<Long> age,Optional<Long> female,Optional<Long> diplomacy,Optional<Long> martial,
            Optional<Long> stewardship,Optional<Long> intrigue,Optional<Long> learning,Optional<Long> prowess,
            Optional<Long> sameHouse,Optional<Long> cost){
        public Configuration{
            for(var value:List.of(age,female,diplomacy,martial,stewardship,intrigue,learning,prowess,sameHouse,cost))Objects.requireNonNull(value);
        }
        public boolean complete(){return List.of(age,female,diplomacy,martial,stewardship,intrigue,learning,prowess,sameHouse,cost).stream().allMatch(Optional::isPresent);}
        static Configuration decode(JsonNode node)throws IOException{
            var r=StrictJson.object(node,Set.of("age","female","diplomacy","martial","stewardship","intrigue","learning","prowess","same_house","cost"));
            return new Configuration(raw(r,"age"),raw(r,"female"),raw(r,"diplomacy"),raw(r,"martial"),raw(r,"stewardship"),raw(r,"intrigue"),raw(r,"learning"),raw(r,"prowess"),raw(r,"same_house"),raw(r,"cost"));
        }
        ObjectNode encode(){
            var r=StrictJson.object();putRaw(r,"age",age);putRaw(r,"female",female);putRaw(r,"diplomacy",diplomacy);putRaw(r,"martial",martial);putRaw(r,"stewardship",stewardship);putRaw(r,"intrigue",intrigue);putRaw(r,"learning",learning);putRaw(r,"prowess",prowess);putRaw(r,"same_house",sameHouse);putRaw(r,"cost",cost);return r;
        }
        private static Optional<Long> raw(ObjectNode r,String key)throws IOException{
            JsonNode n=r.get(key);if(n.isNull())return Optional.empty();String s=NativeWire.text(n);
            if(!s.matches("0|-?[1-9][0-9]{0,18}"))throw new IOException("Canonical signed64 raw string or null required: "+key);
            try{return Optional.of(Long.parseLong(s));}catch(NumberFormatException invalid){throw new IOException("Raw signed64 value outside native range: "+key,invalid);}
        }
        private static void putRaw(ObjectNode r,String key,Optional<Long> v){if(v.isPresent())r.put(key,Long.toString(v.orElseThrow()));else r.putNull(key);}
    }
    public CurrentCourtierConfigurationSource{
        Objects.requireNonNull(product);Objects.requireNonNull(setting);Objects.requireNonNull(nativeDefinitionFound);Objects.requireNonNull(nativeShown);Objects.requireNonNull(nativeValid);Objects.requireNonNull(configuration);
        StrictJson.require(confirmationLayerFound,"Missing confirmation layer is Unavailable, never fabricated absence");
        if(!creatorWindowFound)StrictJson.require(!modalFound&&!panelFound&&!windowVisible&&!windowEnabled&&nativeDefinitionFound.isEmpty()&&nativeShown.isEmpty()&&nativeValid.isEmpty()&&!executeAdmissible&&configuration.isEmpty()&&!numericComplete,"Absent creator cannot carry configuration or unobserved predicates");
        else{
            StrictJson.require(modalFound&&panelFound&&nativeDefinitionFound.isPresent()&&configuration.isPresent(),"Present complete creator needs actual modal/panel/definition and configuration observation");
            if(nativeDefinitionFound.orElseThrow())StrictJson.require(nativeShown.isPresent()&&nativeValid.isPresent(),"Actual definition predicates must be observed bools");
            else StrictJson.require(nativeShown.isEmpty()&&nativeValid.isEmpty(),"Missing native definition cannot invent Shown/Valid");
        }
        StrictJson.require(numericComplete==configuration.map(Configuration::complete).orElse(false),"numeric_complete must reflect all ten observed native raw values");
        if(executeAdmissible)StrictJson.require(creatorWindowFound&&modalFound&&panelFound&&windowVisible&&windowEnabled&&nativeDefinitionFound.orElse(false)&&nativeShown.orElse(false)&&nativeValid.orElse(false)&&numericComplete,"Execute requires actual complete chain, native predicates and numeric snapshot");
    }
    static CurrentCourtierConfigurationSource decode(JsonNode node)throws IOException{
        var r=StrictJson.object(node,Set.of("schema","product","setting","confirmation_layer_found","creator_window_found","modal_found","panel_found","window_visible","window_enabled","native_definition_found","native_shown","native_valid","execute_admissible","configuration","numeric_complete"));
        if(!NativeWire.text(r.get("schema")).equals(CurrentCourtierConfiguration.SOURCE_SCHEMA))throw new IOException("Exact courtier configuration source schema required");
        Optional<Configuration> actual=r.get("configuration").isNull()?Optional.empty():Optional.of(Configuration.decode(r.get("configuration")));
        return new CurrentCourtierConfigurationSource(CurrentCourtierControls.Product.parse(NativeWire.text(r.get("product"))),CurrentCourtierConfiguration.Setting.parse(NativeWire.text(r.get("setting"))),bool(r,"confirmation_layer_found"),bool(r,"creator_window_found"),bool(r,"modal_found"),bool(r,"panel_found"),bool(r,"window_visible"),bool(r,"window_enabled"),maybeBool(r.get("native_definition_found")),maybeBool(r.get("native_shown")),maybeBool(r.get("native_valid")),bool(r,"execute_admissible"),actual,bool(r,"numeric_complete"));
    }
    ObjectNode encode(){
        var r=StrictJson.object().put("schema",CurrentCourtierConfiguration.SOURCE_SCHEMA).put("product",product.wire()).put("setting",setting.wire()).put("confirmation_layer_found",confirmationLayerFound)
                .put("creator_window_found",creatorWindowFound).put("modal_found",modalFound).put("panel_found",panelFound).put("window_visible",windowVisible).put("window_enabled",windowEnabled).put("execute_admissible",executeAdmissible).put("numeric_complete",numericComplete);
        putBool(r,"native_definition_found",nativeDefinitionFound);putBool(r,"native_shown",nativeShown);putBool(r,"native_valid",nativeValid);if(configuration.isPresent())r.set("configuration",configuration.orElseThrow().encode());else r.putNull("configuration");return r;
    }
    private static Optional<Boolean> maybeBool(JsonNode n)throws IOException{if(n.isNull())return Optional.empty();if(!n.isBoolean())throw new IOException("Actual bool or unobserved null required");return Optional.of(n.booleanValue());}
    private static boolean bool(ObjectNode r,String key)throws IOException{return maybeBool(r.get(key)).orElseThrow(()->new IOException("Actual courtier bool required: "+key));}
    private static void putBool(ObjectNode r,String key,Optional<Boolean> value){if(value.isPresent())r.put(key,value.orElseThrow());else r.putNull(key);}
}
