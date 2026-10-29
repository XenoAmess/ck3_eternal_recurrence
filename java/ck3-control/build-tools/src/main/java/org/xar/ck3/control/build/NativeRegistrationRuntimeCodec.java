package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.JsonMappingException;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Closed historical-six-field / explicit-manifest-version decoder. No missing/null/empty aliases. */
public final class NativeRegistrationRuntimeCodec extends JsonDeserializer<NativeBridgeDefender.Runtime> {
    private static final Set<String> LEGACY=Set.of("python_base_root","venv_root","python","helper","complete_python_files","complete_helper_sources");
    private static final Set<String> CURRENT=Set.of("schema","python_base_root","venv_root","python","helper","inventory_ref");
    @Override public NativeBridgeDefender.Runtime deserialize(JsonParser parser,DeserializationContext context)throws IOException{
        try{
            JsonNode value=context.readTree(parser);if(value==null||!value.isObject())throw new IOException("typed registration runtime object required");
            var keys=new HashSet<String>();value.fieldNames().forEachRemaining(keys::add);
            if(keys.equals(LEGACY))return new NativeBridgeDefender.HelperRuntime(path(value,"python_base_root"),path(value,"venv_root"),
                    pin(value,"python"),pin(value,"helper"),pins(value.get("complete_python_files")),pins(value.get("complete_helper_sources")));
            if(!keys.equals(CURRENT))throw new IOException("exact legacy-six or explicit-version runtime fields required");
            return new NativeBridgeDefender.ManifestRuntime(text(value,"schema"),path(value,"python_base_root"),path(value,"venv_root"),
                    pin(value,"python"),pin(value,"helper"),pin(value,"inventory_ref"));
        }catch(IllegalArgumentException invalid){throw JsonMappingException.from(parser,"invalid typed registration runtime",invalid);}
        catch(IOException invalid){throw JsonMappingException.from(parser,invalid.getMessage(),invalid);}
    }
    private static Path path(JsonNode value,String name)throws IOException{
        text(value,name);
        return ControlBuild.strictMapper().treeToValue(value.get(name),Path.class);
    }
    private static String text(JsonNode value,String name)throws IOException{
        JsonNode item=value.get(name);if(item==null||!item.isTextual()||item.textValue().isBlank())throw new IOException("exact runtime string required: "+name);
        return item.textValue();
    }
    private static FileRef pin(JsonNode value,String name)throws IOException{
        if(value.get(name)==null||!value.get(name).isObject())throw new IOException("exact runtime FileRef required");
        return ControlBuild.strictMapper().treeToValue(value.get(name),FileRef.class);
    }
    private static List<FileRef> pins(JsonNode value)throws IOException{
        if(value==null||!value.isArray()||value.isEmpty()||value.size()>16000)throw new IOException("finite exact historical runtime pins required");
        var result=new ArrayList<FileRef>();for(JsonNode item:value)result.add(ControlBuild.strictMapper().treeToValue(item,FileRef.class));return List.copyOf(result);
    }
}
