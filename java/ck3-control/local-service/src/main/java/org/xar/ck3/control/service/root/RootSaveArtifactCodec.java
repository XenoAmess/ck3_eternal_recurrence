package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.Arguments;
import static org.xar.ck3.control.service.root.RootSaveArtifactInspector.*;

/** One original public response contract, with exact missing/null/boolean/integer semantics. */
public final class RootSaveArtifactCodec {
    private RootSaveArtifactCodec() { }
    public record Request() { }
    private static final Set<String> RESPONSE = Set.of("schema", "profile_dir", "save_root", "artifact_count", "artifacts", "path_argument_accepted", "read_only");
    private static final Set<String> ZIP = Set.of("name", "relative_path", "bytes", "sha256", "format", "integrity_scope", "integrity_ok", "zip_valid", "bad_member", "has_gamestate", "member_count", "members_truncated", "members");
    private static final Set<String> OTHER = Set.of("name", "relative_path", "bytes", "sha256", "format", "integrity_scope", "integrity_ok", "raw_header_valid", "raw_header_kind", "zip_valid", "bad_member", "has_gamestate", "format_probe_error");
    private static final Set<String> MEMBER = Set.of("name", "bytes", "compressed_bytes", "crc32", "compression", "flags");
    public static Request decodeRequest(Arguments arguments) {
        ObjectNode object = object(parse(arguments.objectOrEmpty())); fields(object, Set.of()); return new Request();
    }
    public static RawJson encode(Response response) {
        ObjectNode result = StrictJson.object(); result.put("schema", SCHEMA);
        result.put("profile_dir", response.profileDirectory().toString()); result.put("save_root", response.saveRoot().toString());
        result.put("artifact_count", response.artifacts().size()); result.put("path_argument_accepted", false); result.put("read_only", true);
        var rows = result.putArray("artifacts");
        for (Artifact artifact : response.artifacts()) {
            ObjectNode row = rows.addObject(); FileFacts file = artifact.file();
            row.put("name", file.name()); row.put("relative_path", file.relativePath()); row.put("bytes", file.bytes()); row.put("sha256", file.sha256());
            if (artifact instanceof ZipArtifact zip) {
                row.put("format", "zip-ck3"); row.put("integrity_scope", "zip-crc"); row.put("integrity_ok", zip.integrityOk());
                row.put("zip_valid", zip.zipValid()); row.put("bad_member", zip.badMember()); row.put("has_gamestate", zip.hasGamestate());
                row.put("member_count", zip.memberCount()); row.put("members_truncated", zip.membersTruncated()); var members = row.putArray("members");
                for (Member member : zip.members()) {
                    ObjectNode item = members.addObject(); item.put("name", member.name()); item.put("bytes", member.bytes());
                    item.put("compressed_bytes", member.compressedBytes()); item.put("crc32", member.crc32());
                    item.put("compression", member.compression()); item.put("flags", member.flags());
                }
            } else if (artifact instanceof OtherArtifact other) {
                row.put("format", other.rawHeader() == null ? "unknown" : "raw-ck3");
                row.put("integrity_scope", other.rawHeader() == null ? "none" : "header-only"); row.putNull("integrity_ok");
                row.put("raw_header_valid", other.rawHeader() != null);
                row.put("raw_header_kind", other.rawHeader() == null ? null : other.rawHeader().name().toLowerCase(java.util.Locale.ROOT));
                row.put("zip_valid", false); row.putNull("bad_member"); row.putNull("has_gamestate"); row.put("format_probe_error", other.formatProbeError());
            }
        }
        try { return new RawJson(ControlBuild.strictMapper().writeValueAsBytes(result)); }
        catch (IOException invalid) { throw new IllegalArgumentException("invalid bounded save artifact response", invalid); }
    }
    public static Response decode(RawJson original) {
        ObjectNode row = object(parse(original)); fields(row, RESPONSE); require(SCHEMA.equals(text(row, "schema")), "exact save artifacts version required");
        require(!bool(row, "path_argument_accepted") && bool(row, "read_only"), "pathless read-only save inspection required");
        JsonNode values = row.get("artifacts"); require(values.isArray(), "artifact array required"); var artifacts = new ArrayList<Artifact>();
        for (JsonNode value : values) {
            ObjectNode artifact = object(value); String format = text(artifact, "format");
            if (format.equals("zip-ck3")) {
                fields(artifact, ZIP); require(text(artifact, "integrity_scope").equals("zip-crc"), "full ZIP integrity scope required");
                int count = (int) number(artifact, "member_count", Integer.MAX_VALUE); JsonNode rawMembers = artifact.get("members");
                require(rawMembers.isArray(), "ZIP member array required"); var members = new ArrayList<Member>();
                for (JsonNode raw : rawMembers) {
                    ObjectNode member = object(raw); fields(member, MEMBER);
                    members.add(new Member(text(member, "name"), number(member, "bytes", StrictJson.MAX_SAFE_INTEGER),
                            number(member, "compressed_bytes", StrictJson.MAX_SAFE_INTEGER), text(member, "crc32"),
                            (int) number(member, "compression", 65535), (int) number(member, "flags", 65535)));
                }
                ZipArtifact zip = new ZipArtifact(file(artifact), bool(artifact, "zip_valid"), nullable(artifact, "bad_member"),
                        bool(artifact, "has_gamestate"), count, members);
                require(bool(artifact, "integrity_ok") == zip.integrityOk() && bool(artifact, "members_truncated") == zip.membersTruncated(),
                        "ZIP derived integrity/truncation fields differ"); artifacts.add(zip);
            } else {
                fields(artifact, OTHER); require(format.equals("raw-ck3") || format.equals("unknown"), "finite save format required");
                require(artifact.get("integrity_ok").isNull() && artifact.get("bad_member").isNull() && artifact.get("has_gamestate").isNull()
                        && !bool(artifact, "zip_valid"), "non-ZIP integrity remains explicit null, never true");
                String kind = nullable(artifact, "raw_header_kind"); RawHeader header = kind == null ? null : switch (kind) {
                    case "text" -> RawHeader.TEXT; case "binary" -> RawHeader.BINARY; default -> throw new IllegalArgumentException("unknown raw SAVE header kind");
                };
                require(bool(artifact, "raw_header_valid") == (header != null) && format.equals(header == null ? "unknown" : "raw-ck3")
                        && text(artifact, "integrity_scope").equals(header == null ? "none" : "header-only"), "raw SAVE header-only contract differs");
                artifacts.add(new OtherArtifact(file(artifact), header, text(artifact, "format_probe_error")));
            }
        }
        require(number(row, "artifact_count", MAX_SAVE_ARTIFACTS) == artifacts.size(), "artifact count differs from actual rows");
        return new Response(Path.of(text(row, "profile_dir")), Path.of(text(row, "save_root")), artifacts);
    }
    private static FileFacts file(ObjectNode row) {
        return new FileFacts(text(row, "name"), text(row, "relative_path"), number(row, "bytes", StrictJson.MAX_SAFE_INTEGER), text(row, "sha256"));
    }
    private static JsonNode parse(RawJson raw) {
        try { return ControlBuild.strictMapper().readTree(raw.bytes()); }
        catch (IOException invalid) { throw new IllegalArgumentException("invalid original save artifact JSON", invalid); }
    }
    private static ObjectNode object(JsonNode value) { require(value instanceof ObjectNode, "exact JSON object required"); return (ObjectNode) value; }
    private static void fields(ObjectNode row, Set<String> expected) {
        var actual = new java.util.HashSet<String>(); row.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(expected), "missing or unknown save artifact contract field");
    }
    private static String text(ObjectNode row, String name) { JsonNode value = row.get(name); require(value != null && value.isTextual(), "exact string required: " + name); return value.textValue(); }
    private static String nullable(ObjectNode row, String name) { JsonNode value = row.get(name); require(value != null, "explicit nullable field required"); return value.isNull() ? null : text(row, name); }
    private static boolean bool(ObjectNode row, String name) { JsonNode value = row.get(name); require(value != null && value.isBoolean(), "exact JSON boolean required: " + name); return value.booleanValue(); }
    private static long number(ObjectNode row, String name, long max) { return StrictJson.integer(row.get(name), 0, max); }
    private static void require(boolean condition, String message) { StrictJson.require(condition, message); }
}
