package org.xar.ck3.control.service.mcp;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;

/** Protocol adapter port installed by the existing Root assembly, using its actual typed application routes. */
public interface PublicMcpDirectory {
    enum Scope { COMPLETE_MIGRATION, SOFTWARE_ONLY }
    Scope scope();
    List<ToolDescriptor> tools();
    CallResult invoke(ToolCall call) throws ToolFailure, RpcFailure;
    List<ResourceDescriptor> resources();
    ResourceResult read(ResourceCall call) throws ToolFailure, RpcFailure;

    enum Presence { MISSING, NULL, VALUE }
    record Arguments(Presence presence, Optional<RawJson> original) {
        public Arguments {
            Objects.requireNonNull(presence); Objects.requireNonNull(original);
            McpJson.require((presence == Presence.MISSING) == original.isEmpty(), "argument presence/token mismatch");
            if (presence == Presence.NULL) McpJson.require(McpJson.parse(original.orElseThrow().bytes()).isNull(), "null arguments token required");
            if (presence == Presence.VALUE) McpJson.object(McpJson.parse(original.orElseThrow().bytes()));
        }
        /** Only a route whose original contract permits absent/null arguments may deliberately use this default. */
        public RawJson objectOrEmpty() {
            return presence == Presence.VALUE ? original.orElseThrow() : new RawJson(McpJson.utf8("{}"));
        }
    }
    record ToolDescriptor(String name, RawJson original) {
        public ToolDescriptor {
            Objects.requireNonNull(original); McpJson.toolName(name);
            var row = McpJson.object(McpJson.parse(original.bytes()));
            McpJson.require(name.equals(McpJson.text(row.get("name"))), "descriptor/name mismatch");
            var schema = McpJson.object(row.get("inputSchema"));
            McpJson.require("object".equals(McpJson.text(schema.get("type"))), "actual object input schema required");
            if (row.hasNonNull("outputSchema")) McpJson.object(row.get("outputSchema"));
            if (row.hasNonNull("annotations")) McpJson.object(row.get("annotations"));
            McpSchema.supported(schema);
            if (row.hasNonNull("outputSchema")) McpSchema.supported(McpJson.object(row.get("outputSchema")));
        }
        public void validateArguments(Arguments arguments) {
            // The original SDK uses absent/null arguments as {}, while the typed decoder still sees their presence.
            McpJson.publicNumbers(McpJson.parse(arguments.objectOrEmpty().bytes()));
            McpSchema.validate(McpJson.object(McpJson.parse(original.bytes())).get("inputSchema"),
                    McpJson.parse(arguments.objectOrEmpty().bytes()));
        }
        public void validateResult(CallResult result) {
            var descriptor = McpJson.object(McpJson.parse(original.bytes()));
            var response = McpJson.object(McpJson.parseResult(result.bytes()));
            if (response.path("isError").asBoolean(false) || !descriptor.hasNonNull("outputSchema")) return;
            McpJson.require(response.has("structuredContent"), "declared output schema requires structuredContent");
            McpSchema.validate(descriptor.get("outputSchema"), response.get("structuredContent"));
        }
    }
    record ToolCall(String name, Arguments arguments, Optional<RawJson> meta, McpCancellation cancellation) {
        public ToolCall {
            McpJson.toolName(name); Objects.requireNonNull(arguments); Objects.requireNonNull(meta); Objects.requireNonNull(cancellation);
            meta.ifPresent(value -> McpJson.object(McpJson.parse(value.bytes())));
        }
    }
    /** The complete result envelope has a different bound from the 64 MiB native/body token. */
    final class CallResult {
        private final byte[] original;
        public CallResult(byte[] original) { this.original = Objects.requireNonNull(original).clone(); McpJson.validateResult(this.original); }
        public static CallResult fromRaw(RawJson original) { return new CallResult(original.bytes()); }
        /** Original MCPServer dict-result conversion: indented text and the same structured JSON value. */
        public static CallResult fromBusinessJson(RawJson original) {
            McpJson.object(McpJson.parseResult(original.bytes()));
            return new CallResult(McpJson.join(McpJson.utf8("{\"content\":[{\"type\":\"text\",\"text\":"),
                    McpJson.quote(McpJson.prettyOriginal(original.bytes())), McpJson.utf8("}],\"structuredContent\":"), original.bytes(),
                    McpJson.utf8(",\"isError\":false,\"resultType\":\"complete\"}")));
        }
        public byte[] bytes() { return original.clone(); }
    }
    record ResourceDescriptor(String uri, RawJson original) {
        public ResourceDescriptor {
            McpJson.resourceUri(uri); Objects.requireNonNull(original);
            var row = McpJson.object(McpJson.parse(original.bytes()));
            McpJson.require(uri.equals(McpJson.text(row.get("uri"))), "resource descriptor/URI mismatch");
            McpJson.text(row.get("name"));
            if (row.hasNonNull("mimeType")) McpJson.text(row.get("mimeType"));
        }
    }
    record ResourceCall(String uri, Optional<RawJson> meta, McpCancellation cancellation) {
        public ResourceCall { McpJson.resourceUri(uri); Objects.requireNonNull(meta); Objects.requireNonNull(cancellation);
            meta.ifPresent(value -> McpJson.object(McpJson.parse(value.bytes()))); }
    }
    final class ResourceResult {
        private final byte[] original;
        public ResourceResult(byte[] original) {
            this.original = Objects.requireNonNull(original).clone();
            var row = McpJson.object(McpJson.parseResult(this.original));
            McpJson.publicNumbers(row);
            McpJson.fields(row, java.util.Set.of("contents", "_meta", "resultType", "ttlMs", "cacheScope"), java.util.Set.of("contents"));
            McpJson.require(row.get("contents").isArray(), "resource contents array required");
            for (var item : row.get("contents")) McpJson.resourceContents(item);
            if (row.has("resultType")) McpJson.require("complete".equals(McpJson.text(row.get("resultType"))), "complete resource result required");
            if (row.hasNonNull("_meta")) McpJson.object(row.get("_meta"));
            if (row.has("ttlMs")) McpJson.require(row.get("ttlMs").isIntegralNumber() && row.get("ttlMs").bigIntegerValue().signum() >= 0, "exact nonnegative resource ttlMs required");
            if (row.has("cacheScope")) McpJson.require(java.util.Set.of("private", "public").contains(McpJson.text(row.get("cacheScope"))), "known resource cache scope required");
        }
        public static ResourceResult fromBusinessJson(String uri, RawJson business) {
            McpJson.resourceUri(uri);
            McpJson.publicNumbers(McpJson.parseResult(business.bytes()));
            return new ResourceResult(McpJson.join(McpJson.utf8("{\"contents\":[{\"uri\":"), McpJson.quote(uri),
                    McpJson.utf8(",\"mimeType\":\"text/plain\",\"text\":"),
                    McpJson.quote(McpJson.prettyOriginal(business.bytes())), McpJson.utf8("}]}")));
        }
        public byte[] bytes() { return original.clone(); }
    }
    final class ToolFailure extends Exception {
        public ToolFailure(String message) { super(Objects.requireNonNull(message)); }
        public ToolFailure(String message, Throwable cause) { super(Objects.requireNonNull(message), cause); }
    }
    final class RpcFailure extends Exception {
        private final int code;
        private final Optional<RawJson> data;
        public RpcFailure(int code, String message, Optional<RawJson> data) { super(Objects.requireNonNull(message)); this.code = code; this.data = Objects.requireNonNull(data); }
        public int code() { return code; }
        public Optional<RawJson> data() { return data; }
    }
}
