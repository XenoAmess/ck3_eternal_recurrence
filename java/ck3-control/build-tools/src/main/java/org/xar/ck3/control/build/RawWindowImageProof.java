package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** Narrow reader for the retained actual M7 full-hash original; never rehashes the image or invents missing identity. */
public final class RawWindowImageProof {
    private RawWindowImageProof() { }
    public record LegacyIdentity(String fileId64Decimal, String fileId128Decimal, String volumeSerial64Decimal,
                                 long size, String creationFiletime, String lastwriteFiletime, String changeFiletime,
                                 int attributes, long links) {
        public LegacyIdentity {
            decimal(fileId64Decimal, 64); decimal(fileId128Decimal, 128); decimal(volumeSerial64Decimal, 64);
            decimal(creationFiletime, 64); decimal(lastwriteFiletime, 64); decimal(changeFiletime, 64);
            nonnegative(size); require(size > 0 && links > 0 && (attributes & 0x400) == 0, "original ordinary-file identity required");
        }
        public boolean matches(SharedSourceFiles.NativeFile actual) {
            return fileId128Decimal.equals(actual.fileIdDecimal()) && volumeSerial64Decimal.equals(actual.volumeSerialDecimal())
                    && creationFiletime.equals(actual.creationFiletimeDecimal()) && lastwriteFiletime.equals(actual.lastWriteFiletimeDecimal())
                    && changeFiletime.equals(actual.changeFiletimeDecimal()) && size == actual.logicalBytes() && links == actual.linkCount()
                    && new BigInteger(fileId64Decimal).equals(new BigInteger(actual.legacyFileIdHex(), 16));
        }
    }
    public record Proof(String machineId, String inputPath, String sha256, LegacyIdentity identity, FileRef original) {
        public Proof {
            machine(machineId); sha(sha256); Objects.requireNonNull(identity); Objects.requireNonNull(original);
            try { spelling(inputPath); } catch (IOException invalid) { throw new IllegalArgumentException("absolute original image spelling required", invalid); }
        }
        public void requireCurrent(String expectedMachine, String input, SharedSourceFiles.NativeFile actual) throws IOException {
            if (!machineId.equals(expectedMachine) || !spelling(inputPath).equals(spelling(input)) || !identity.matches(actual))
                throw new IOException("historical full SHA cannot bind this machine/path/Win32 identity/time/size");
        }
    }
    public static Proof load(FileRef original) throws IOException { return decode(original, RawWindowCaptureJson.exactBytes(original, 65_536)); }
    /** The historical format is a specific explicit branch, not a loose alias-based source parser. */
    public static Proof decode(FileRef original, byte[] raw) throws IOException {
        if (raw.length != original.bytes() || !RawWindowCaptureJson.hash(raw).equals(original.sha256())) throw new IOException("historical full-hash original changed");
        ObjectNode root = RawWindowCaptureJson.object(RawWindowCaptureJson.tree(raw), "schema", "machine_id", "observed_at_utc", "status", "input", "final_path",
                "ancestor_paths_checked_no_reparse", "handle_policy", "before", "after", "sha256", "file_version", "pe", "objdump_version", "spans", "budget", "game_pid", "authority");
        if (!"xar.g2.m7.native-static-window-source/v1".equals(RawWindowCaptureJson.text(root.get("schema")))
                || !"FRESH_SOURCE_MAPPED_STATIC_WINDOWS_ONLY".equals(RawWindowCaptureJson.text(root.get("status")))
                || !"GENERIC_READ + FILE_SHARE_READ only; denied write/delete, same handle held across hash/read/objdump/prepost".equals(RawWindowCaptureJson.text(root.get("handle_policy"))))
            throw new IOException("actual prior full-hash producer contract required; no source-only or inherited fallback");
        LegacyIdentity before = identity(root.get("before")), after = identity(root.get("after"));
        if (!before.equals(after)) throw new IOException("historical full-hash file changed while measured");
        var budget = root.get("budget");
        if (budget == null || !budget.isObject() || RawWindowCaptureJson.integer(budget.get("one_full_sha_stream_bytes")) != before.size())
            throw new IOException("historical whole-image SHA streaming length unavailable");
        String path = RawWindowCaptureJson.text(root.get("input")); String finalPath = RawWindowCaptureJson.text(root.get("final_path"));
        if (!spelling(path).equals(spelling(finalPath)))
            throw new IOException("historical held final path differs from its input");
        return new Proof(RawWindowCaptureJson.text(root.get("machine_id")), path, RawWindowCaptureJson.text(root.get("sha256")), before, original);
    }
    private static LegacyIdentity identity(com.fasterxml.jackson.databind.JsonNode node) throws IOException {
        var row = RawWindowCaptureJson.object(node, "file_id64_decimal", "file_id128_decimal", "volume_serial64_decimal", "size", "creation_filetime",
                "lastwrite_filetime", "change_filetime", "attributes", "links");
        return new LegacyIdentity(RawWindowCaptureJson.text(row.get("file_id64_decimal")), RawWindowCaptureJson.text(row.get("file_id128_decimal")),
                RawWindowCaptureJson.text(row.get("volume_serial64_decimal")), RawWindowCaptureJson.integer(row.get("size")),
                RawWindowCaptureJson.text(row.get("creation_filetime")), RawWindowCaptureJson.text(row.get("lastwrite_filetime")),
                RawWindowCaptureJson.text(row.get("change_filetime")), Math.toIntExact(RawWindowCaptureJson.integer(row.get("attributes"))),
                RawWindowCaptureJson.integer(row.get("links")));
    }
    static String stripExtended(String value) {
        if (value.startsWith("\\\\?\\UNC\\")) return "\\\\" + value.substring(8);
        return value.startsWith("\\\\?\\") ? value.substring(4) : value;
    }
    private static String spelling(String value) throws IOException {
        if (value == null || value.length() > 1024 || value.indexOf('\0') >= 0) throw new IOException("bounded original path required");
        String plain = stripExtended(value).replace('/', '\\');
        if (plain.matches("[A-Za-z]:\\\\.*") || plain.startsWith("\\\\")) return SharedSourceFiles.nativePathValue(plain);
        Path path = Path.of(value);
        if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IOException("absolute normalized original path required"); return path.toString();
    }
    private static void decimal(String value, int bits) {
        require(value != null && value.matches("0|[1-9][0-9]*") && new BigInteger(value).bitLength() <= bits,
                "canonical full-width original native identity required");
    }
}
