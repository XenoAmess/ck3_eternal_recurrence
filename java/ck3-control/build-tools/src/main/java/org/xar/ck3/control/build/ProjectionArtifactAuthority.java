package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Single primitive wire authority shared by the existing Owner and Quarkus host. No domain dependency or I/O grant. */
public final class ProjectionArtifactAuthority {
    public static final String SCOPE_SCHEMA = "xar.projection-artifact-input-scope/v1";
    public static final String LEASE_SCHEMA = "xar.projection-artifact-input-lease/v1";
    public static final String CONTEXT_SCHEMA = "xar.projection-artifact-input-context/v1";
    public static final String SOURCE_SCHEMA = "xar.projection-artifact-source-binding/v1";
    public static final String RUNTIME_SCHEMA = "xar.projection-artifact-runtime-binding/v1";
    public static final String INPUT_NAME = "payload.json";
    public static final int METADATA_MAX_BYTES = 65_536;
    public static final int CONTEXT_MAX_BYTES = 262_144;
    public static final int BINDING_MAX_BYTES = 1_048_576;
    public static final long MAX_SAFE_INTEGER = 9_007_199_254_740_991L;
    private static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");
    private static final Set<String> SCOPE_FIELDS = Set.of("schema", "scope_id", "owner_session_id", "machine_id", "owner_process",
            "operation", "input_root", "lease_path", "max_input_bytes", "issued_at_utc", "expires_at_utc",
            "source_snapshot_ref", "producer_artifact_ref", "build_receipt_ref", "runtime_binding_ref", "producer_class");
    private ProjectionArtifactAuthority() { }

    public enum InputOperation {
        MILITARY_COMBAT_ROLES_NORMALIZE;
        public String wire() { return "military-combat-roles-normalize"; }
    }
    public enum Purpose { FULL }
    public record ProcessIdentity(long pid, String creationFiletime, Path executable) {
        public ProcessIdentity {
            require(pid > 0 && pid <= 0xffff_ffffL && creationFiletime != null
                    && creationFiletime.matches("[1-9][0-9]{0,19}")
                    && new BigInteger(creationFiletime).compareTo(UINT64_MAX) <= 0, "exact PID/decimal FILETIME required");
            executable = absolute(executable);
        }
        public static ProcessIdentity from(WindowsJobProcess.ProcessIdentity value) {
            return new ProcessIdentity(value.pid(), value.creationFiletimeDecimal(), Path.of(value.executable()));
        }
    }
    public record Scope(String scopeId, String ownerSessionId, String machineId, ProcessIdentity ownerProcess,
            InputOperation operation, Path inputRoot, Path leasePath, long maxInputBytes,
            Instant issuedAtUtc, Instant expiresAtUtc, ControlBuild.FileRef sourceSnapshotRef, ControlBuild.FileRef producerArtifactRef,
            ControlBuild.FileRef buildReceiptRef, ControlBuild.FileRef runtimeBindingRef, String producerClass) {
        public Scope {
            identifier(scopeId); identifier(ownerSessionId); machine(machineId); Objects.requireNonNull(ownerProcess);
            require(operation == InputOperation.MILITARY_COMBAT_ROLES_NORMALIZE, "closed existing input operation required");
            inputRoot = absolute(inputRoot); leasePath = absolute(leasePath);
            require(!leasePath.startsWith(inputRoot), "Owner lease must be outside input slot");
            require(maxInputBytes > 0 && maxInputBytes <= MAX_SAFE_INTEGER, "finite safe input budget required"); interval(issuedAtUtc, expiresAtUtc);
            for (ControlBuild.FileRef proof : List.of(reference(sourceSnapshotRef), reference(producerArtifactRef), reference(buildReceiptRef), reference(runtimeBindingRef))) {
                require(!Path.of(proof.path()).startsWith(inputRoot), "proof must be outside input slot");
            }
            require(producerClass != null && producerClass.matches("[A-Za-z_$][A-Za-z0-9_$]*(?:\\.[A-Za-z_$][A-Za-z0-9_$]*)+"), "fixed producer class required");
        }
    }
    public record Lease(ControlBuild.FileRef scopeRef, ProcessIdentity hostProcess, Instant issuedAtUtc, Instant expiresAtUtc, Purpose purpose) {
        public Lease {
            reference(scopeRef); Objects.requireNonNull(hostProcess); Objects.requireNonNull(purpose); interval(issuedAtUtc, expiresAtUtc);
            require(scopeRef.bytes() <= METADATA_MAX_BYTES, "finite scope metadata required");
        }
    }
    public record Active(ControlBuild.FileRef scopeRef, ControlBuild.FileRef leaseRef, Scope scope, ProcessIdentity hostProcess) {
        public Active {
            reference(scopeRef); reference(leaseRef); Objects.requireNonNull(scope); Objects.requireNonNull(hostProcess);
            require(scopeRef.bytes() <= METADATA_MAX_BYTES && leaseRef.bytes() <= METADATA_MAX_BYTES, "finite original scope and lease metadata required");
        }
    }
    public record Context(String machineId, Instant observedAtUtc, Optional<Active> artifactInputs) {
        public Context { machine(machineId); Objects.requireNonNull(observedAtUtc); Objects.requireNonNull(artifactInputs); }
    }
    @JsonSerialize(using = ObservedSerializer.class)
    @JsonDeserialize(using = ObservedDeserializer.class)
    public record Observed(Context context, ControlBuild.FileRef responseRef) {
        public Observed { Objects.requireNonNull(context); reference(responseRef); require(responseRef.bytes() <= CONTEXT_MAX_BYTES, "finite original context required"); }
    }
    public record SourceBinding(String machineId, ControlBuild.FileRef buildReceiptRef,
            List<ControlBuild.FileRef> sourceRefs, List<ControlBuild.FileRef> compiledSourceRefs) {
        public SourceBinding { machine(machineId); reference(buildReceiptRef); sourceRefs = refs(sourceRefs); compiledSourceRefs = refs(compiledSourceRefs); }
    }
    public record RuntimeBinding(String machineId, ControlBuild.FileRef buildReceiptRef, String ownerSessionId,
            ProcessIdentity ownerProcess, List<ControlBuild.FileRef> ownerSourceRefs, List<ControlBuild.FileRef> ownerRuntimeRefs) {
        public RuntimeBinding {
            machine(machineId); reference(buildReceiptRef); identifier(ownerSessionId); Objects.requireNonNull(ownerProcess);
            ownerSourceRefs = refs(ownerSourceRefs); ownerRuntimeRefs = refs(ownerRuntimeRefs);
        }
    }

    /** Ordered closure equality; a correct hash of an unrelated JSON document cannot satisfy these equations. */
    public static void requireBindings(Scope scope, ControlBuild.BuildReceipt accepted, SourceBinding source, RuntimeBinding runtime) throws IOException {
        if (!scope.machineId().equals(accepted.machineId()) || !source.machineId().equals(scope.machineId()) || !runtime.machineId().equals(scope.machineId())
                || !source.buildReceiptRef().equals(scope.buildReceiptRef()) || !runtime.buildReceiptRef().equals(scope.buildReceiptRef())
                || !source.sourceRefs().equals(accepted.sourcePins()) || !source.compiledSourceRefs().equals(accepted.compiledSourcePins())
                || !runtime.ownerSessionId().equals(scope.ownerSessionId()) || !runtime.ownerProcess().equals(scope.ownerProcess())
                || !runtime.ownerSourceRefs().equals(ownerSources(accepted)) || !runtime.ownerRuntimeRefs().equals(accepted.producerRuntimePins())
                || !accepted.completeDeployment().contains(scope.producerArtifactRef())) {
            throw new IOException("artifact source/runtime binding differs from the complete accepted build or fixed Owner");
        }
    }
    public static List<ControlBuild.FileRef> ownerSources(ControlBuild.BuildReceipt accepted) throws IOException {
        Path root = absolute(Path.of(accepted.sourceRoot())).resolve("build-tools/src/main/java").normalize();
        List<ControlBuild.FileRef> result = accepted.sourcePins().stream().filter(ref -> Path.of(ref.path()).startsWith(root)).toList();
        for (String name : List.of("ProjectionArtifactAuthority.java", "ProjectionArtifactInputOwner.java", "MapAdmissionServiceOwner.java")) {
            Path expected = root.resolve("org/xar/ck3/control/build").resolve(name);
            if (result.stream().noneMatch(ref -> Path.of(ref.path()).equals(expected))) throw new IOException("qualified original Owner source closure is incomplete");
        }
        return result;
    }
    public static ControlBuild.FileRef reference(ControlBuild.FileRef ref) {
        Objects.requireNonNull(ref); absolute(Path.of(ref.path()));
        require(ref.bytes() > 0 && ref.bytes() <= MAX_SAFE_INTEGER, "nonempty safe original reference required"); return ref;
    }
    public static Path absolute(Path value) {
        Objects.requireNonNull(value); require(value.isAbsolute() && value.equals(value.normalize()), "normalized absolute original path required"); return value;
    }
    public static void identifier(String value) { require(value != null && value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"), "bounded exact identifier required"); }
    public static void machine(String value) { require(value != null && !value.equals("unknown") && value.matches("[a-z0-9][a-z0-9-]{0,63}"), "actual machine required"); }
    public static void interval(Instant issued, Instant expires) { require(issued != null && expires != null && issued.isBefore(expires), "finite ordered interval required"); }

    public static Scope decodeScope(byte[] raw) {
        ObjectNode row = object(parse(raw, METADATA_MAX_BYTES), SCOPE_FIELDS); schema(row, SCOPE_SCHEMA);
        require(InputOperation.MILITARY_COMBAT_ROLES_NORMALIZE.wire().equals(text(row, "operation")), "closed operation required");
        return new Scope(text(row, "scope_id"), text(row, "owner_session_id"), text(row, "machine_id"), process(row.get("owner_process")),
                InputOperation.MILITARY_COMBAT_ROLES_NORMALIZE, Path.of(text(row, "input_root")), Path.of(text(row, "lease_path")), integer(row.get("max_input_bytes"), MAX_SAFE_INTEGER),
                instant(row, "issued_at_utc"), instant(row, "expires_at_utc"), ref(row.get("source_snapshot_ref")), ref(row.get("producer_artifact_ref")),
                ref(row.get("build_receipt_ref")), ref(row.get("runtime_binding_ref")), text(row, "producer_class"));
    }
    public static Lease decodeLease(byte[] raw) {
        ObjectNode row = object(parse(raw, METADATA_MAX_BYTES), Set.of("schema", "scope_ref", "host_process", "issued_at_utc", "expires_at_utc", "purpose")); schema(row, LEASE_SCHEMA);
        require("full".equals(text(row, "purpose")), "full-only lease required");
        return new Lease(ref(row.get("scope_ref")), process(row.get("host_process")), instant(row, "issued_at_utc"), instant(row, "expires_at_utc"), Purpose.FULL);
    }
    public static Context decodeContext(byte[] raw) { return decodeContext(parse(raw, CONTEXT_MAX_BYTES)); }
    public static Context decodeContext(JsonNode node) {
        ObjectNode row = object(node, Set.of("schema", "machine_id", "observed_at_utc", "artifact_inputs")); schema(row, CONTEXT_SCHEMA);
        Optional<Active> active = Optional.empty();
        if (!row.get("artifact_inputs").isNull()) {
            ObjectNode value = object(row.get("artifact_inputs"), Set.of("scope_ref", "lease_ref", "scope", "host_process"));
            active = Optional.of(new Active(ref(value.get("scope_ref")), ref(value.get("lease_ref")), decodeScope(encode(value.get("scope"), METADATA_MAX_BYTES)), process(value.get("host_process"))));
        }
        Context result = new Context(text(row, "machine_id"), instant(row, "observed_at_utc"), active);
        active.ifPresent(value -> require(value.scope().machineId().equals(result.machineId()) && Path.of(value.leaseRef().path()).equals(value.scope().leasePath()), "context scope/machine/lease equation required"));
        return result;
    }
    public static SourceBinding decodeSourceBinding(byte[] raw) {
        ObjectNode row = object(parse(raw, BINDING_MAX_BYTES), Set.of("schema", "machine_id", "build_receipt_ref", "source_refs", "compiled_source_refs")); schema(row, SOURCE_SCHEMA);
        return new SourceBinding(text(row, "machine_id"), ref(row.get("build_receipt_ref")), refList(row.get("source_refs")), refList(row.get("compiled_source_refs")));
    }
    public static RuntimeBinding decodeRuntimeBinding(byte[] raw) {
        ObjectNode row = object(parse(raw, BINDING_MAX_BYTES), Set.of("schema", "machine_id", "build_receipt_ref", "owner_session_id", "owner_process", "owner_source_refs", "owner_runtime_refs")); schema(row, RUNTIME_SCHEMA);
        return new RuntimeBinding(text(row, "machine_id"), ref(row.get("build_receipt_ref")), text(row, "owner_session_id"), process(row.get("owner_process")), refList(row.get("owner_source_refs")), refList(row.get("owner_runtime_refs")));
    }
    public static byte[] encodeScope(Scope value) { return encode(scope(value), METADATA_MAX_BYTES); }
    public static byte[] encodeLease(Lease value) {
        ObjectNode row = row(LEASE_SCHEMA); row.set("scope_ref", ref(value.scopeRef())); row.set("host_process", process(value.hostProcess()));
        row.put("issued_at_utc", value.issuedAtUtc().toString()); row.put("expires_at_utc", value.expiresAtUtc().toString()); row.put("purpose", "full"); return encode(row, METADATA_MAX_BYTES);
    }
    public static byte[] encodeContext(Context value) { return encode(context(value), CONTEXT_MAX_BYTES); }
    public static byte[] encodeSourceBinding(SourceBinding value) {
        ObjectNode row = row(SOURCE_SCHEMA); row.put("machine_id", value.machineId()); row.set("build_receipt_ref", ref(value.buildReceiptRef()));
        refList(row, "source_refs", value.sourceRefs()); refList(row, "compiled_source_refs", value.compiledSourceRefs()); return encode(row, BINDING_MAX_BYTES);
    }
    public static byte[] encodeRuntimeBinding(RuntimeBinding value) {
        ObjectNode row = row(RUNTIME_SCHEMA); row.put("machine_id", value.machineId()); row.set("build_receipt_ref", ref(value.buildReceiptRef()));
        row.put("owner_session_id", value.ownerSessionId()); row.set("owner_process", process(value.ownerProcess()));
        refList(row, "owner_source_refs", value.ownerSourceRefs()); refList(row, "owner_runtime_refs", value.ownerRuntimeRefs()); return encode(row, BINDING_MAX_BYTES);
    }
    public static ObjectNode scope(Scope value) {
        ObjectNode row = row(SCOPE_SCHEMA); row.put("scope_id", value.scopeId()); row.put("owner_session_id", value.ownerSessionId()); row.put("machine_id", value.machineId()); row.set("owner_process", process(value.ownerProcess()));
        row.put("operation", value.operation().wire()); row.put("input_root", value.inputRoot().toString()); row.put("lease_path", value.leasePath().toString()); row.put("max_input_bytes", value.maxInputBytes());
        row.put("issued_at_utc", value.issuedAtUtc().toString()); row.put("expires_at_utc", value.expiresAtUtc().toString()); row.set("source_snapshot_ref", ref(value.sourceSnapshotRef()));
        row.set("producer_artifact_ref", ref(value.producerArtifactRef())); row.set("build_receipt_ref", ref(value.buildReceiptRef())); row.set("runtime_binding_ref", ref(value.runtimeBindingRef())); row.put("producer_class", value.producerClass()); return row;
    }
    public static ObjectNode context(Context value) {
        ObjectNode row = row(CONTEXT_SCHEMA); row.put("machine_id", value.machineId()); row.put("observed_at_utc", value.observedAtUtc().toString()); row.putNull("artifact_inputs");
        value.artifactInputs().ifPresent(active -> {
            ObjectNode bound = row.putObject("artifact_inputs"); bound.set("scope_ref", ref(active.scopeRef())); bound.set("lease_ref", ref(active.leaseRef()));
            bound.set("scope", scope(active.scope())); bound.set("host_process", process(active.hostProcess()));
        }); return row;
    }
    public static final class ObservedSerializer extends JsonSerializer<Observed> {
        @Override public void serialize(Observed value, JsonGenerator generator, SerializerProvider provider) throws IOException {
            ObjectNode row = ControlBuild.strictMapper().createObjectNode(); row.set("context", context(value.context())); row.set("response_ref", ref(value.responseRef())); generator.writeTree(row);
        }
    }
    public static final class ObservedDeserializer extends JsonDeserializer<Observed> {
        @Override public Observed deserialize(JsonParser parser, DeserializationContext context) throws IOException {
            ObjectNode row = object(context.readTree(parser), Set.of("context", "response_ref")); return new Observed(decodeContext(row.get("context")), ref(row.get("response_ref")));
        }
    }
    private static ObjectNode row(String schema) { ObjectNode row = ControlBuild.strictMapper().createObjectNode(); row.put("schema", schema); return row; }
    private static ObjectNode process(ProcessIdentity value) { ObjectNode row = ControlBuild.strictMapper().createObjectNode(); row.put("pid", value.pid()); row.put("creation_filetime", value.creationFiletime()); row.put("executable", value.executable().toString()); return row; }
    private static ProcessIdentity process(JsonNode node) { ObjectNode row = object(node, Set.of("pid", "creation_filetime", "executable")); return new ProcessIdentity(integer(row.get("pid"), 0xffff_ffffL), text(row, "creation_filetime"), Path.of(text(row, "executable"))); }
    private static ObjectNode ref(ControlBuild.FileRef value) { reference(value); ObjectNode row = ControlBuild.strictMapper().createObjectNode(); row.put("path", value.path()); row.put("bytes", value.bytes()); row.put("sha256", value.sha256()); return row; }
    private static ControlBuild.FileRef ref(JsonNode node) { ObjectNode row = object(node, Set.of("path", "bytes", "sha256")); return reference(new ControlBuild.FileRef(text(row, "path"), integer(row.get("bytes"), MAX_SAFE_INTEGER), text(row, "sha256"))); }
    private static void refList(ObjectNode row, String name, List<ControlBuild.FileRef> values) { var array = row.putArray(name); values.forEach(value -> array.add(ref(value))); }
    private static List<ControlBuild.FileRef> refList(JsonNode node) { require(node != null && node.isArray(), "exact reference array required"); List<ControlBuild.FileRef> result = new ArrayList<>(); node.forEach(value -> result.add(ref(value))); return refs(result); }
    private static List<ControlBuild.FileRef> refs(List<ControlBuild.FileRef> values) {
        List<ControlBuild.FileRef> result = List.copyOf(values); require(!result.isEmpty(), "nonempty ordered closure required"); Set<Path> paths = new HashSet<>();
        for (ControlBuild.FileRef ref : result) require(paths.add(Path.of(reference(ref).path())), "duplicate closure path refused"); return result;
    }
    private static JsonNode parse(byte[] raw, int maximum) {
        require(raw != null && raw.length > 0 && raw.length <= maximum, "bounded exact metadata required");
        try { return ControlBuild.strictMapper().readTree(raw); } catch (IOException failure) { throw new IllegalArgumentException("invalid strict metadata JSON", failure); }
    }
    private static byte[] encode(JsonNode value, int maximum) {
        try { byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(value); require(raw.length > 0 && raw.length <= maximum, "bounded exact metadata required"); return raw; }
        catch (IOException failure) { throw new IllegalArgumentException("metadata encoding failed", failure); }
    }
    private static ObjectNode object(JsonNode node, Set<String> fields) {
        require(node != null && node.isObject(), "exact object required"); ObjectNode row = (ObjectNode) node; Set<String> actual = new HashSet<>(); row.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(fields), "exact metadata fields required"); return row;
    }
    private static void schema(ObjectNode row, String expected) { require(expected.equals(text(row, "schema")), "exact versioned schema required"); }
    private static String text(ObjectNode row, String name) { JsonNode value = row.get(name); require(value != null && value.isTextual() && !value.textValue().isBlank(), "exact nonempty text required"); return value.textValue(); }
    private static long integer(JsonNode value, long maximum) { require(value != null && value.isIntegralNumber() && value.canConvertToLong() && value.longValue() > 0 && value.longValue() <= maximum, "exact positive safe integer required"); return value.longValue(); }
    private static Instant instant(ObjectNode row, String name) { String value = text(row, name); require(value.endsWith("Z") || value.endsWith("+00:00"), "UTC instant required"); return Instant.parse(value); }
    private static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}
