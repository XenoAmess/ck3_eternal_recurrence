package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete fixed creator-chain observation; unknown predicates remain null and never authorize Execute. */
public record CurrentCourtierControlsSource(CurrentCourtierControls.Product product,CurrentCourtierControls.Control control,
        boolean confirmationLayerFound,boolean creatorWindowFound,boolean modalFound,boolean panelFound,
        boolean windowVisible,boolean windowEnabled,Optional<Boolean> nativeDefinitionFound,
        Optional<Boolean> nativeShown,Optional<Boolean> nativeValid,boolean executeAdmissible){
    public CurrentCourtierControlsSource{
        Objects.requireNonNull(product);Objects.requireNonNull(control);Objects.requireNonNull(nativeDefinitionFound);Objects.requireNonNull(nativeShown);Objects.requireNonNull(nativeValid);
        StrictJson.require(confirmationLayerFound,"Missing confirmation layer is Unavailable, never fabricated absence");
        if(!creatorWindowFound)StrictJson.require(!modalFound&&!panelFound&&!windowVisible&&!windowEnabled&&nativeDefinitionFound.isEmpty()&&nativeShown.isEmpty()&&nativeValid.isEmpty()&&!executeAdmissible,"Absent creator cannot carry modal material or unobserved predicates");
        else{
            StrictJson.require(modalFound&&panelFound&&nativeDefinitionFound.isPresent(),"Present complete creator needs actual modal/panel/definition observation");
            if(nativeDefinitionFound.orElseThrow())StrictJson.require(nativeShown.isPresent()&&nativeValid.isPresent(),"Actual definition predicates must be observed bools");
            else StrictJson.require(nativeShown.isEmpty()&&nativeValid.isEmpty(),"Missing native definition cannot invent Shown/Valid");
        }
        if(executeAdmissible)StrictJson.require(creatorWindowFound&&modalFound&&panelFound&&windowVisible&&windowEnabled&&nativeDefinitionFound.orElse(false)&&nativeShown.orElse(false)&&nativeValid.orElse(false),"Execute requires actual complete visible/enabled chain and Native predicates");
    }
    static CurrentCourtierControlsSource decode(JsonNode node)throws IOException{
        var r=StrictJson.object(node,Set.of("schema","product","control","confirmation_layer_found","creator_window_found","modal_found","panel_found","window_visible","window_enabled","native_definition_found","native_shown","native_valid","execute_admissible"));
        if(!NativeWire.text(r.get("schema")).equals(CurrentCourtierControls.SOURCE_SCHEMA))throw new IOException("Exact courtier control source schema required");
        return new CurrentCourtierControlsSource(CurrentCourtierControls.Product.parse(NativeWire.text(r.get("product"))),CurrentCourtierControls.Control.parse(NativeWire.text(r.get("control"))),bool(r,"confirmation_layer_found"),bool(r,"creator_window_found"),bool(r,"modal_found"),bool(r,"panel_found"),bool(r,"window_visible"),bool(r,"window_enabled"),maybeBool(r.get("native_definition_found")),maybeBool(r.get("native_shown")),maybeBool(r.get("native_valid")),bool(r,"execute_admissible"));
    }
    ObjectNode encode(){
        var r=StrictJson.object().put("schema",CurrentCourtierControls.SOURCE_SCHEMA).put("product",product.wire()).put("control",control.wire()).put("confirmation_layer_found",confirmationLayerFound)
                .put("creator_window_found",creatorWindowFound).put("modal_found",modalFound).put("panel_found",panelFound).put("window_visible",windowVisible).put("window_enabled",windowEnabled).put("execute_admissible",executeAdmissible);
        putBool(r,"native_definition_found",nativeDefinitionFound);putBool(r,"native_shown",nativeShown);putBool(r,"native_valid",nativeValid);return r;
    }
    private static Optional<Boolean> maybeBool(JsonNode n)throws IOException{if(n.isNull())return Optional.empty();if(!n.isBoolean())throw new IOException("Actual bool or unobserved null required");return Optional.of(n.booleanValue());}
    private static boolean bool(ObjectNode r,String key)throws IOException{return maybeBool(r.get(key)).orElseThrow(()->new IOException("Actual courtier bool required: "+key));}
    private static void putBool(ObjectNode r,String key,Optional<Boolean> value){if(value.isPresent())r.put(key,value.orElseThrow());else r.putNull(key);}
}
