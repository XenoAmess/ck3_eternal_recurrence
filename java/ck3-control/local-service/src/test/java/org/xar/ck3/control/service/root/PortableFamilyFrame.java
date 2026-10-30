package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Four relocated retained inputs; production assembly only, without a Root context, lease or Native transport. */
final class PortableFamilyFrame {
    private static final int MAXIMUM=ContinuityJson.DOMAIN_MAX_BYTES;
    record Loaded(DriverObservationAssembler.Complete frame,ExactRef semantic,byte[] originalSemantic) {
        Loaded {originalSemantic=originalSemantic.clone();}
        @Override public byte[] originalSemantic(){return originalSemantic.clone();}
    }
    private PortableFamilyFrame() { }

    static Loaded materialize(Path temporary)throws IOException {
        ObjectNode bundle;
        try(var original=PortableFamilyFrame.class.getResourceAsStream("/familybridge/complete94-template.json.gz")) {
            if(original==null)throw new IOException("required family bridge software fixture absent");
            try(var gzip=new GZIPInputStream(original)) {
                byte[] bytes=gzip.readNBytes(MAXIMUM+1);
                if(bytes.length>MAXIMUM)throw new IOException("family bridge fixture exceeds its finite bound");
                bundle=ContinuityJson.parseObject(bytes,MAXIMUM);
            }
        }
        StrictJson.require("xar.family-bridge-software-fixture/v1".equals(bundle.path("schema").textValue()),"exact family fixture schema required");
        Path root=Files.createTempDirectory(temporary,"family-software-").toAbsolutePath().normalize();
        var materializer=new Materializer(root,(ObjectNode)bundle.get("files"));var roots=bundle.get("roots");
        return load(materializer.reference(roots.path("native").textValue()),materializer.reference(roots.path("facts").textValue()),
                materializer.reference(roots.path("semantic").textValue()));
    }

    static Loaded load(ExactRef nativePacket,ExactRef facts,ExactRef semantic) {
        var archive=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(PortableFamilyFrame.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->switch(method.getName()) {
                    case "loadNativeFrame"->exact((ExactRef)args[0]);
                    case "loadFullMaterial"->RawJson.fullMaterial(exact((ExactRef)args[0]));
                    default->throw new AssertionError("software family archive refuses operation: "+method.getName());
                });
        var frame=new DriverFrameEvidenceLoader(new DriverObservationAssembler()).load(new NativeEffectEvidence.FrameBasis(nativePacket,facts),archive);
        return new Loaded(frame,semantic,exact(semantic));
    }
    private static byte[] exact(ExactRef reference) {
        try {
            byte[] bytes=Files.readAllBytes(Path.of(reference.path()));
            StrictJson.require(bytes.length==reference.bytes()&&DriverJson.sha256(bytes).equals(reference.sha256()),"family software input changed");
            return bytes;
        }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
    }

    private static final class Materializer {
        private final Path root;private final ObjectNode templates;
        private final Map<String,byte[]> bytes=new HashMap<>();private final Map<String,ExactRef> refs=new HashMap<>();
        private final Set<String> active=new HashSet<>();
        Materializer(Path root,ObjectNode templates){this.root=root;this.templates=templates;}
        ExactRef reference(String key)throws IOException {
            if(refs.containsKey(key))return refs.get(key);
            StrictJson.require(active.add(key),"cyclic family fixture dependency: "+key);
            try {
                var template=templates.get(key);StrictJson.require(template instanceof ObjectNode,"missing family fixture dependency: "+key);
                String format=StrictJson.text(template.get("format"));JsonNode value=transform(template.get("value"));
                byte[] raw=ContinuityJson.canonical(value,MAXIMUM);
                if(format.equals("driver"))raw=DriverStateSnapshot.decodeComplete(raw).encode();
                else if(format.equals("framed"))raw=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
                else StrictJson.require(format.equals("json"),"unknown family fixture format");
                Path path=root.resolve(key+".bin");Files.write(path,raw);bytes.put(key,raw);
                var reference=new ExactRef(path.toString(),raw.length,DriverJson.sha256(raw));refs.put(key,reference);return reference;
            }finally{active.remove(key);}
        }
        private JsonNode transform(JsonNode value)throws IOException {
            if(value.isObject()) {
                if(value.size()==1) {
                    if(value.has("$ref"))return reference(StrictJson.text(value.get("$ref"))).toJson();
                    if(value.has("$hash"))return StrictJson.object().put("v",reference(StrictJson.text(value.get("$hash"))).sha256()).get("v");
                    if(value.has("$length")) {String key=StrictJson.text(value.get("$length"));reference(key);return StrictJson.object().put("v",bytes.get(key).length).get("v");}
                    if(value.has("$path")) {
                        Path path=root.resolve(StrictJson.text(value.get("$path"))).normalize();StrictJson.require(path.startsWith(root),"family fixture path escaped its root");
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
