package org.xar.ck3.control.continuity.writer;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Relocates naturally produced ROOT96 DATA; no source qualification, lease, Game or lineage is constructed. */
final class PortableRoot96Fixture {
    private static final int MAXIMUM=ContinuityJson.DOMAIN_MAX_BYTES;
    private PortableRoot96Fixture() { }
    static ExactRef materialize(Path temporary)throws IOException {
        ObjectNode bundle;
        try(var original=PortableRoot96Fixture.class.getResourceAsStream("/familyroot96/original-root-template.json.gz")) {
            if(original==null)throw new IOException("required ROOT96 fixture resource absent");
            try(var gzip=new GZIPInputStream(original)) {
                byte[] raw=gzip.readNBytes(MAXIMUM+1);if(raw.length>MAXIMUM)throw new IOException("bounded ROOT96 fixture required");
                bundle=ContinuityJson.parseObject(raw,MAXIMUM);
            }
        }
        StrictJson.require("xar.family-root96-software-fixture/v1".equals(bundle.path("schema").textValue()),"exact ROOT96 fixture schema required");
        Path root=Files.createTempDirectory(temporary,"family-root96-software-").toAbsolutePath().normalize();
        return new Materializer(root,(ObjectNode)bundle.get("files")).reference(bundle.path("root_receipt").textValue());
    }
    private static final class Materializer {
        private final Path root;private final ObjectNode templates;
        private final Map<String,byte[]> bytes=new HashMap<>();private final Map<String,ExactRef> refs=new HashMap<>();
        private final Set<String> active=new HashSet<>();
        Materializer(Path root,ObjectNode templates){this.root=root;this.templates=templates;}
        ExactRef reference(String key)throws IOException {
            if(refs.containsKey(key))return refs.get(key);
            StrictJson.require(active.add(key),"cyclic family ROOT96 fixture dependency: "+key);
            try {
                var template=templates.get(key);StrictJson.require(template instanceof ObjectNode,"missing family ROOT96 fixture dependency: "+key);
                String format=StrictJson.text(template.get("format"));JsonNode value=transform(template.get("value"));
                byte[] raw=DriverJson.encodeNode(value);
                if(format.equals("driver"))raw=DriverStateSnapshot.decodeComplete(raw).encode();
                else if(format.equals("framed"))raw=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
                else StrictJson.require(format.equals("full-json"),"unknown family ROOT96 fixture format");
                Path path=root.resolve(key+".bin");Files.write(path,raw);bytes.put(key,raw);
                var reference=new ExactRef(path.toString(),raw.length,DriverJson.sha256(raw));refs.put(key,reference);return reference;
            }finally{active.remove(key);}
        }
        private JsonNode transform(JsonNode value)throws IOException {
            if(value.isObject()) {
                if(value.size()==1) {
                    if(value.has("$decimal"))return new org.xar.ck3.control.contracts.DecimalTokenNode(StrictJson.text(value.get("$decimal")));
                    if(value.has("$ref"))return reference(StrictJson.text(value.get("$ref"))).toJson();
                    if(value.has("$hash"))return StrictJson.object().put("v",reference(StrictJson.text(value.get("$hash"))).sha256()).get("v");
                    if(value.has("$length")) {String key=StrictJson.text(value.get("$length"));reference(key);return StrictJson.object().put("v",bytes.get(key).length).get("v");}
                    if(value.has("$path")) {
                        Path path=root.resolve(StrictJson.text(value.get("$path"))).normalize();StrictJson.require(path.startsWith(root),"family ROOT96 fixture path escaped its root");
                        return StrictJson.object().put("v",path.toString()).get("v");
                    }
                }
                var result=StrictJson.object();var fields=value.fieldNames();
                while(fields.hasNext()){String field=fields.next();result.set(field,transform(value.get(field)));}return result;
            }
            if(value.isArray()){var result=StrictJson.object().putArray("v");for(var child:value)result.add(transform(child));return result;}
            return value.deepCopy();
        }
    }
}
