package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete actual catalogue and configuration observation. Public rows are DATA, never write authority. */
public record CurrentCourtierChoicesSource(CurrentCourtierControls.Product product,CurrentCourtierChoices.Catalog catalog,
        boolean confirmationLayerFound,boolean creatorWindowFound,boolean modalFound,boolean panelFound,
        boolean windowVisible,boolean windowEnabled,boolean modelAvailable,boolean completeModel,Optional<Integer> catalogCount,
        List<Row> rows,Optional<CurrentCourtierConfigurationSource.Configuration> configuration){
    public record Row(String choiceToken,String key,boolean nativeShown,boolean nativeValid,boolean selected,boolean executeAdmissible){
        public Row{CurrentCourtierChoices.token(choiceToken);CurrentCourtierChoices.exactKey(key);if(executeAdmissible)StrictJson.require(nativeShown&&nativeValid,"Actual row predicate admission required");}
        static Row decode(JsonNode n)throws IOException{var r=StrictJson.object(n,Set.of("choice_token","key","native_shown","native_valid","selected","execute_admissible"));return new Row(NativeWire.text(r.get("choice_token")),NativeWire.text(r.get("key")),bool(r,"native_shown"),bool(r,"native_valid"),bool(r,"selected"),bool(r,"execute_admissible"));}
        ObjectNode encode(){return StrictJson.object().put("choice_token",choiceToken).put("key",key).put("native_shown",nativeShown).put("native_valid",nativeValid).put("selected",selected).put("execute_admissible",executeAdmissible);}
    }
    public CurrentCourtierChoicesSource{
        Objects.requireNonNull(product);Objects.requireNonNull(catalog);Objects.requireNonNull(catalogCount);Objects.requireNonNull(configuration);rows=List.copyOf(rows);
        StrictJson.require(confirmationLayerFound,"Absent confirmation is Unavailable, never invented complete absence");
        if(!creatorWindowFound)StrictJson.require(!modalFound&&!panelFound&&!windowVisible&&!windowEnabled&&!modelAvailable&&!completeModel&&catalogCount.isEmpty()&&rows.isEmpty()&&configuration.isEmpty(),"Absent creator requires null count/configuration and no catalogue rows or predicates");
        else StrictJson.require(modalFound&&panelFound&&modelAvailable&&completeModel&&catalogCount.isPresent()&&catalogCount.orElseThrow()==rows.size()&&configuration.isPresent(),"Present catalogue must be complete actual chain/model/configuration; partial or unbound is Unavailable");
        StrictJson.require(rows.size()<=2048,"Actual bounded catalogue limit exceeded");
        var keys=new HashSet<String>();var tokens=new HashSet<String>();
        for(var row:rows){
            StrictJson.require(keys.add(row.key())&&tokens.add(row.choiceToken()),"Actual keys and opaque tokens must each be unique");
            if(row.executeAdmissible())StrictJson.require(creatorWindowFound&&windowVisible&&windowEnabled&&modelAvailable&&completeModel&&configuration.orElseThrow().complete(),"Actual row admission requires complete visible enabled source and all ten numeric observations");
        }
    }
    static CurrentCourtierChoicesSource decode(JsonNode n)throws IOException{
        var r=StrictJson.object(n,Set.of("schema","product","catalog","confirmation_layer_found","creator_window_found","modal_found","panel_found","window_visible","window_enabled","model_available","complete_model","catalog_count","rows","configuration"));
        if(!NativeWire.text(r.get("schema")).equals(CurrentCourtierChoices.SOURCE_SCHEMA))throw new IOException("Exact current choices source schema required");
        Optional<Integer> count=r.get("catalog_count").isNull()?Optional.empty():Optional.of(NativeWire.integer(r.get("catalog_count"),BigInteger.ZERO,BigInteger.valueOf(2048)).intValueExact());
        if(!r.get("rows").isArray()||r.get("rows").size()>2048)throw new IOException("Bounded actual catalogue rows array required");
        var rows=new ArrayList<Row>();for(var row:r.get("rows"))rows.add(Row.decode(row));
        var configuration=r.get("configuration").isNull()?Optional.<CurrentCourtierConfigurationSource.Configuration>empty():Optional.of(CurrentCourtierConfigurationSource.Configuration.decode(r.get("configuration")));
        return new CurrentCourtierChoicesSource(CurrentCourtierControls.Product.parse(NativeWire.text(r.get("product"))),CurrentCourtierChoices.Catalog.parse(NativeWire.text(r.get("catalog"))),bool(r,"confirmation_layer_found"),bool(r,"creator_window_found"),bool(r,"modal_found"),bool(r,"panel_found"),bool(r,"window_visible"),bool(r,"window_enabled"),bool(r,"model_available"),bool(r,"complete_model"),count,rows,configuration);
    }
    ObjectNode encode(){
        var r=StrictJson.object().put("schema",CurrentCourtierChoices.SOURCE_SCHEMA).put("product",product.wire()).put("catalog",catalog.wire()).put("confirmation_layer_found",confirmationLayerFound).put("creator_window_found",creatorWindowFound).put("modal_found",modalFound).put("panel_found",panelFound).put("window_visible",windowVisible).put("window_enabled",windowEnabled).put("model_available",modelAvailable).put("complete_model",completeModel);
        if(catalogCount.isPresent())r.put("catalog_count",catalogCount.orElseThrow());else r.putNull("catalog_count");
        var array=r.putArray("rows");for(var row:rows)array.add(row.encode());if(configuration.isPresent())r.set("configuration",configuration.orElseThrow().encode());else r.putNull("configuration");return r;
    }
    private static boolean bool(ObjectNode r,String key)throws IOException{var n=r.get(key);if(n==null||!n.isBoolean())throw new IOException("Actual catalogue bool required: "+key);return n.booleanValue();}
}
