package org.xar.ck3.control.build.runtime;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Explicit source DATA for the Root entry. No pair, Started or Game capability is manufactured here. */
public record RootStartupInvocation(FileRef startup, Optional<FileRef> savedRequest) {
    public static final String SCHEMA="xar.java-root-startup-invocation/v1";
    public RootStartupInvocation {
        Objects.requireNonNull(startup); Objects.requireNonNull(savedRequest);
        for(FileRef ref:savedRequest.isPresent()?List.of(startup,savedRequest.orElseThrow()):List.of(startup)) {
            JavaRuntimePackageModel.absolute(ref.path());
            if(ref.bytes()<1||ref.bytes()>1024*1024)throw new IllegalArgumentException("bounded exact Root startup input required");
        }
        if(savedRequest.isPresent()&&startup.path().equals(savedRequest.orElseThrow().path()))throw new IllegalArgumentException("startup and Saved request are distinct original inputs");
    }
    public List<FileRef> sources(){return savedRequest.isPresent()?List.of(startup,savedRequest.orElseThrow()):List.of(startup);}
    /** The sole positional contract matches RootSavedNativeCoordinator.arguments: exact3 or exact6. */
    public List<String> arguments() {
        var result=new ArrayList<String>();for(FileRef source:sources())result.addAll(List.of(source.path(),Long.toString(source.bytes()),source.sha256()));
        return List.copyOf(result);
    }
    public byte[] encode()throws IOException {
        var mapper=ControlBuild.strictMapper();ObjectNode node=mapper.createObjectNode();node.put("schema",SCHEMA);
        node.set("startup",mapper.valueToTree(startup));
        if(savedRequest.isPresent())node.set("saved_request",mapper.valueToTree(savedRequest.orElseThrow()));else node.putNull("saved_request");
        return mapper.writeValueAsBytes(node);
    }
    public static RootStartupInvocation decode(byte[] raw)throws IOException {
        if(raw.length<1||raw.length>65536)throw new IOException("bounded exact Root invocation JSON required");
        var mapper=ControlBuild.strictMapper();JsonNode node=mapper.readTree(raw);fields(node,Set.of("schema","startup","saved_request"));
        if(!node.get("schema").isTextual()||!SCHEMA.equals(node.get("schema").textValue()))throw new IOException("Root invocation schema differs");
        return new RootStartupInvocation(ref(node.get("startup")),node.get("saved_request").isNull()?Optional.empty():Optional.of(ref(node.get("saved_request"))));
    }
    private static FileRef ref(JsonNode node)throws IOException {
        fields(node,Set.of("path","bytes","sha256"));
        if(!node.get("path").isTextual()||!node.get("sha256").isTextual()||!node.get("bytes").isIntegralNumber()||!node.get("bytes").canConvertToLong())throw new IOException("exact file path/integer bytes/SHA types required");
        return new FileRef(node.get("path").textValue(),node.get("bytes").longValue(),node.get("sha256").textValue());
    }
    private static void fields(JsonNode node,Set<String> expected)throws IOException {
        if(node==null||!node.isObject())throw new IOException("exact Root invocation object required");
        var names=new java.util.HashSet<String>();node.fieldNames().forEachRemaining(names::add);
        if(!names.equals(expected))throw new IOException("Root invocation missing or unknown fields");
    }
}
