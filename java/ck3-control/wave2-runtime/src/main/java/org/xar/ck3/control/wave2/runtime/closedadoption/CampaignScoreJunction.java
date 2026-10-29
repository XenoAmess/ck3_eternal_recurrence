package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.WString;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Java filesystem producer. It grants no Prepared, SDK, ledger or restoration authority.
 * The owning retained Root scope must consume its attempt under the original writer lock first.
 * Failed/unknown creation leaves its evidence and is never retried or cleaned up here. */
public final class CampaignScoreJunction {
    public static final String ROOT_RESULT_STATUS = "VERIFIED_JAVA_JUNCTION";
    public static final String PREPARED_SCHEMA = "xar.java-campaign-score-junction-prepared/v1";
    private static final int MOUNT_POINT_TAG = 0xa0000003;
    private static final int GET_REPARSE_POINT = 0x000900a8;
    private static final int SET_REPARSE_POINT = 0x000900a4;
    private static final int DIRECTORY = 0x10, REPARSE = 0x400;
    private static final int BACKUP_SEMANTICS = 0x02000000, OPEN_REPARSE_POINT = 0x00200000;
    private static final int MAX_ANCHOR = 16_384;
    private CampaignScoreJunction() { }

    /** Shared six-field wire; identity strings never pass through floating point or JSON numbers. */
    public record Binding(Path path, Path target, String fileId, String device, ExactRef anchor) {
        public Binding {
            normalized(path); normalized(target); Objects.requireNonNull(anchor);
            uint64(fileId, false); uint64(device, true);
            StrictJson.require(anchor.bytes() > 0 && anchor.bytes() <= MAX_ANCHOR
                    && Path.of(anchor.path()).equals(target.resolve("CAMPAIGN-ANCHOR.json")),
                    "exact bounded campaign-score anchor");
        }
        public static Binding decode(JsonNode value) {
            var row = StrictJson.object(value, Set.of("path", "exact_target", "must_verify_same_FileID",
                    "target_file_id", "target_device", "anchor_ref"));
            trueValue(row.get("must_verify_same_FileID"), "same FileID verification is mandatory");
            return new Binding(CampaignScoreJunction.path(row, "path"), CampaignScoreJunction.path(row, "exact_target"), text(row, "target_file_id"),
                    text(row, "target_device"), ExactRef.fromJson(row.get("anchor_ref")));
        }
        public ObjectNode toJson() {
            var row = StrictJson.object(); row.put("path", path.toString()); row.put("exact_target", target.toString());
            row.put("must_verify_same_FileID", true); row.put("target_file_id", fileId); row.put("target_device", device);
            row.set("anchor_ref", anchor.toJson()); return row;
        }
    }
    /** Native FILE_ID_INFO plus FILE_BASIC_INFO creation time, all exact decimal strings. */
    public record NativeIdentity(String fileId, String device, String creationFiletime) {
        public NativeIdentity { uint64(fileId, false); uint64(device, true); uint64(creationFiletime, false); }
        public ObjectNode toJson() {
            var row = StrictJson.object(); row.put("file_id", fileId); row.put("device", device);
            row.put("creation_filetime", creationFiletime); return row;
        }
        public static NativeIdentity decode(JsonNode value) {
            var row = StrictJson.object(value, Set.of("file_id", "device", "creation_filetime"));
            return new NativeIdentity(text(row, "file_id"), text(row, "device"), text(row, "creation_filetime"));
        }
    }
    /** Serializable evidence only. Reconstructing this record cannot construct actual Prepared. */
    public record PreparedReceipt(String machineId, Instant observedAt, Binding binding,
            NativeIdentity targetIdentity, NativeIdentity junctionIdentity) {
        public PreparedReceipt {
            StrictJson.text(machineId); Objects.requireNonNull(observedAt); Objects.requireNonNull(binding);
            Objects.requireNonNull(targetIdentity); Objects.requireNonNull(junctionIdentity);
            StrictJson.require(binding.fileId().equals(targetIdentity.fileId()) && binding.device().equals(targetIdentity.device())
                    && !targetIdentity.equals(junctionIdentity), "actual distinct junction and qualified target identities");
        }
        public ObjectNode toJson() {
            var row = StrictJson.object(); row.put("schema", PREPARED_SCHEMA);
            row.put("machine_id", machineId); row.put("observed_at_utc", observedAt.toString());
            row.put("status", "CREATED_AND_VERIFIED"); row.set("campaign_score_junction", binding.toJson());
            row.set("target_identity", targetIdentity.toJson()); row.set("junction_identity", junctionIdentity.toJson());
            row.put("copied_files", 0); row.put("ordinary_cycle_credit", 0); row.put("game_day_credit", 0);
            row.put("original_actions_replayed", false); return row;
        }
        public static PreparedReceipt decode(byte[] raw) {
            var row = StrictJson.object(StrictJson.parse(raw, MAX_ANCHOR), Set.of("schema", "machine_id", "observed_at_utc",
                    "status", "campaign_score_junction", "target_identity", "junction_identity", "copied_files",
                    "ordinary_cycle_credit", "game_day_credit", "original_actions_replayed"));
            equal(row, "schema", PREPARED_SCHEMA); equal(row, "status", "CREATED_AND_VERIFIED");
            for (String key : List.of("copied_files", "ordinary_cycle_credit", "game_day_credit")) StrictJson.integer(row.get(key), 0, 0);
            falseValue(row.get("original_actions_replayed"), "junction never replays actions");
            return new PreparedReceipt(text(row, "machine_id"), Instant.parse(text(row, "observed_at_utc")),
                    Binding.decode(row.get("campaign_score_junction")), NativeIdentity.decode(row.get("target_identity")),
                    NativeIdentity.decode(row.get("junction_identity")));
        }
    }
    private record Source(String machineId, Path target, long founder, long start, long endpoint) {
        static Source decode(byte[] basisBytes) {
            JsonNode basis = StrictJson.parse(basisBytes, 65_536);
            equal(basis, "schema", "xar.current-saved-basis/v1");
            JsonNode refs = object(basis.get("refs")), checkpoint = object(basis.get("checkpoint"));
            Path driver = Path.of(ExactRef.fromJson(refs.get("driver")).path());
            Path save = Path.of(ExactRef.fromJson(refs.get("save")).path());
            normalized(driver); normalized(save);
            StrictJson.require(driver.getParent() != null && driver.getParent().getParent() != null
                    && driver.getParent().getParent().getParent() != null && save.getParent() != null,
                    "complete absolute shared-state path ancestry required");
            Path state = driver.getParent().getParent();
            StrictJson.require(driver.equals(state.resolve("native-session").resolve("driver-state.json"))
                    && save.equals(path(checkpoint, "path"))
                    && save.getParent().equals(state.resolve("profile").resolve("save games")),
                    "Driver and checkpoint derive the same qualified shared state root");
            JsonNode origin = object(basis.get("origin")), goal = object(basis.get("campaign_goal_anchor"));
            return new Source(text(basis, "machine_id"), state.getParent().resolve("campaign-score"),
                    number(goal, "origin_character_id", 1), number(origin, "start_date_raw", 0), number(origin, "target_date_raw", 0));
        }
    }
    /** Non-serializable actual outcome, available only to this package's concrete Root scope. */
    static final class Prepared {
        private final PreparedReceipt receipt;
        private final Path runtime;
        private final Source source;
        private final SharedSourceFiles.Witness anchor;
        private final NativeIdentity runtimeIdentity;
        private final Instant deadline;
        private final Runnable guard;
        private Prepared(PreparedReceipt receipt, Path runtime, Source source, SharedSourceFiles.Witness anchor,
                NativeIdentity runtimeIdentity, Instant deadline, Runnable guard) {
            this.receipt = receipt; this.runtime = runtime; this.source = source; this.anchor = anchor;
            this.runtimeIdentity = runtimeIdentity; this.deadline = deadline; this.guard = guard;
        }
        PreparedReceipt receipt() { return receipt; }
        byte[] bytes() { return StrictJson.canonical(receipt.toJson()); }
        void requireCurrent() throws IOException {
            guard(source, deadline, guard); requireSource(receipt.binding(), source, runtime);
            SharedSourceFiles.assertUnchanged(anchor);
            StrictJson.require(runtimeIdentity.equals(observeDirectory(runtime)), "same actual runtime directory");
            Physical now = verifyPhysical(receipt.binding());
            StrictJson.require(now.target().equals(receipt.targetIdentity()) && now.junction().equals(receipt.junctionIdentity()),
                    "same actual junction, target and exact creation FILETIMEs");
            guard(source, deadline, guard);
        }
    }
    static Prepared prepare(Binding binding, byte[] qualifiedBasis, Path runtime, Instant deadline, Runnable finiteGuard)
            throws IOException {
        Objects.requireNonNull(binding); normalized(runtime); Objects.requireNonNull(deadline); Objects.requireNonNull(finiteGuard);
        Source source = Source.decode(qualifiedBasis); guard(source, deadline, finiteGuard);
        SharedSourceFiles.Witness anchor = requireSource(binding, source, runtime);
        if (Files.exists(binding.path(), LinkOption.NOFOLLOW_LINKS)) throw new IOException("create-only junction child already exists");
        if (!"NTFS".equalsIgnoreCase(Files.getFileStore(runtime).type())
                || !"NTFS".equalsIgnoreCase(Files.getFileStore(binding.target()).type()))
            throw new IOException("this uint64 directory contract requires actual NTFS directories");
        NativeIdentity rootIdentity;
        try (DirectoryHandle root = open(runtime, true, false, false);
                DirectoryHandle target = open(binding.target(), true, false, false)) {
            rootIdentity = root.ordinaryIdentity(); NativeIdentity expected = target.ordinaryIdentity();
            requireExpected(binding, expected); guard(source, deadline, finiteGuard);
            // Win32 creates only the already selected exact child. No shell, subprocess, overwrite or rollback.
            if (!Api.VALUE.CreateDirectoryW(new WString(nativePath(binding.path())), null)) throw win32("junction child create");
            try (DirectoryHandle link = open(binding.path(), true, true, false)) {
                NativeIdentity created = link.ordinaryIdentity();
                try (Memory buffer = mountPoint(binding.target())) {
                    if (!Api.VALUE.DeviceIoControl(link.handle, SET_REPARSE_POINT, buffer, Math.toIntExact(buffer.size()),
                            null, 0, new IntByReference(), null)) throw win32("junction set reparse point; attempt is consumed");
                }
                StrictJson.require(created.equals(link.identity()), "same created directory after setting junction");
                root.ordinaryIdentity(); requireExpected(binding, target.ordinaryIdentity());
                if (!rootIdentity.equals(root.identity()) || !expected.equals(target.identity()))
                    throw new IOException("runtime or target directory changed during junction creation");
            }
        }
        Physical physical = verifyPhysical(binding); SharedSourceFiles.assertUnchanged(anchor);
        Prepared result = new Prepared(new PreparedReceipt(source.machineId(), Instant.now(), binding,
                physical.target(), physical.junction()), runtime, source, anchor, rootIdentity, deadline, finiteGuard);
        result.requireCurrent(); return result;
    }
    private static SharedSourceFiles.Witness requireSource(Binding binding, Source source, Path runtime) throws IOException {
        SharedSourceFiles.plainAncestors(runtime); SharedSourceFiles.plainAncestors(binding.target());
        StrictJson.require(binding.path().equals(runtime.resolve("campaign-score")) && binding.path().getParent().equals(runtime)
                && binding.target().equals(source.target()), "exact campaign-score child and shared source target");
        NativeIdentity before = observeDirectory(binding.target()); requireExpected(binding, before);
        SharedSourceFiles.Witness witness = SharedSourceFiles.observe(Path.of(binding.anchor().path()));
        StrictJson.require(witness.source().bytes() == binding.anchor().bytes() && witness.source().sha256().equals(binding.anchor().sha256()),
                "exact original campaign anchor content");
        byte[] raw;
        try (var input = Files.newInputStream(Path.of(binding.anchor().path()))) { raw = input.readNBytes(MAX_ANCHOR + 1); }
        SharedSourceFiles.assertUnchanged(witness);
        StrictJson.require(raw.length == binding.anchor().bytes()
                && org.xar.ck3.control.recovery.RecoveryEvidence.sha256(raw).equals(binding.anchor().sha256()),
                "complete bounded exact original anchor bytes");
        JsonNode anchor = object(StrictJson.parse(raw, MAX_ANCHOR));
        equal(anchor, "schema", "xar.ck3.campaign-score-fixed-anchor/v1"); equal(anchor, "machine_id", source.machineId());
        equal(anchor, "campaign_id", "robert-first30-v20261019");
        StrictJson.require(number(anchor, "founder_character_id", 1) == source.founder()
                && number(anchor, "start_date_raw", 0) == source.start()
                && number(anchor, "endpoint_date_raw", 0) == source.endpoint(), "fixed campaign founder and calendar endpoints");
        trueValue(anchor.get("fixed_across_ruler_and_sdk_changes"), "fixed campaign anchor across ruler/SDK changes");
        StrictJson.integer(anchor.get("old_campaign_inputs_copied"), 0, 0); Instant.parse(text(anchor, "observed_at_utc"));
        StrictJson.require(before.equals(observeDirectory(binding.target())), "target stable while anchor is validated");
        return witness;
    }
    private record Physical(NativeIdentity target, NativeIdentity junction) { }
    private static Physical verifyPhysical(Binding binding) throws IOException {
        SharedSourceFiles.plainAncestors(binding.path().getParent()); SharedSourceFiles.plainAncestors(binding.target());
        try (DirectoryHandle target = open(binding.target(), true, false, false);
                DirectoryHandle link = open(binding.path(), true, false, true);
                DirectoryHandle followed = open(binding.path(), false, false, false)) {
            NativeIdentity targetIdentity = target.ordinaryIdentity(), linkIdentity = link.identity();
            requireExpected(binding, targetIdentity); link.requireMountPoint(binding.target());
            StrictJson.require(targetIdentity.equals(followed.ordinaryIdentity()) && target.finalPath().equals(followed.finalPath()),
                    "real junction resolves to the exact same target file identity and path");
            link.requireMountPoint(binding.target());
            StrictJson.require(linkIdentity.equals(link.identity()) && targetIdentity.equals(target.ordinaryIdentity()),
                    "junction and target stay stable during physical validation");
            return new Physical(targetIdentity, linkIdentity);
        }
    }
    static NativeIdentity observeDirectory(Path path) throws IOException {
        SharedSourceFiles.plainAncestors(path);
        try (DirectoryHandle directory = open(path, true, false, false)) { return directory.ordinaryIdentity(); }
    }
    private static void requireExpected(Binding binding, NativeIdentity actual) {
        StrictJson.require(binding.fileId().equals(actual.fileId()) && binding.device().equals(actual.device()),
                "qualified target FileID and volume decimal strings");
    }
    private static void guard(Source source, Instant deadline, Runnable finiteGuard) throws IOException {
        if (!com.sun.jna.Platform.isWindows() || !source.machineId().equals(WindowsJobProcess.currentMachineId())
                || !Instant.now().isBefore(deadline)) throw new IOException("current same-machine finite Java junction scope required");
        try { finiteGuard.run(); } catch (RuntimeException failure) { throw new IOException("owning Root junction guard failed", failure); }
    }
    public interface FileApi extends StdCallLibrary {
        HANDLE CreateFileW(WString name, int access, int share, Pointer security, int disposition, int flags, HANDLE template);
        boolean CreateDirectoryW(WString path, Pointer security);
        boolean CloseHandle(HANDLE handle);
        boolean GetFileInformationByHandleEx(HANDLE handle, int kind, Pointer data, int bytes);
        boolean DeviceIoControl(HANDLE handle, int code, Pointer input, int inputBytes, Pointer output,
                int outputBytes, IntByReference returned, Pointer overlapped);
        int GetFinalPathNameByHandleW(HANDLE handle, char[] path, int characters, int flags);
    }
    private static final class Api { private static final FileApi VALUE = Native.load("kernel32", FileApi.class); }
    private static final class DirectoryHandle implements AutoCloseable {
        private final HANDLE handle;
        private DirectoryHandle(HANDLE handle) { this.handle = handle; }
        NativeIdentity ordinaryIdentity() throws IOException {
            int attributes = attributes();
            if ((attributes & DIRECTORY) == 0 || (attributes & REPARSE) != 0) throw new IOException("ordinary non-reparse directory required");
            return identity();
        }
        int attributes() throws IOException {
            try (Memory basic = new Memory(40)) {
                if (!Api.VALUE.GetFileInformationByHandleEx(handle, 0, basic, 40)) throw win32("directory basic metadata");
                return basic.getInt(32);
            }
        }
        NativeIdentity identity() throws IOException {
            try (Memory id = new Memory(24); Memory basic = new Memory(40); Memory standard = new Memory(24)) {
                if (!Api.VALUE.GetFileInformationByHandleEx(handle, 18, id, 24)
                        || !Api.VALUE.GetFileInformationByHandleEx(handle, 0, basic, 40)
                        || !Api.VALUE.GetFileInformationByHandleEx(handle, 1, standard, 24)) throw win32("directory native identity");
                if (standard.getByte(20) != 0 || standard.getByte(21) == 0) throw new IOException("live directory metadata required");
                byte[] little = id.getByteArray(8, 16), big = new byte[16];
                for (int index = 0; index < big.length; index++) big[index] = little[15 - index];
                return new NativeIdentity(new BigInteger(1, big).toString(), Long.toUnsignedString(id.getLong(0)),
                        Long.toUnsignedString(basic.getLong(0)));
            }
        }
        void requireMountPoint(Path target) throws IOException {
            if ((attributes() & (DIRECTORY | REPARSE)) != (DIRECTORY | REPARSE)) throw new IOException("real directory reparse point required");
            try (Memory buffer = new Memory(16_384)) {
                IntByReference returned = new IntByReference();
                if (!Api.VALUE.DeviceIoControl(handle, GET_REPARSE_POINT, null, 0, buffer, 16_384, returned, null))
                    throw win32("junction reparse readback");
                int length = returned.getValue();
                if (length < 16 || length > 16_384 || buffer.getInt(0) != MOUNT_POINT_TAG
                        || Short.toUnsignedInt(buffer.getShort(4)) + 8 != length) throw new IOException("bounded MOUNT_POINT reparse tag required");
                String substitute = reparseName(buffer, length, 8), display = reparseName(buffer, length, 12);
                if (!substitute.equalsIgnoreCase("\\??\\" + target) || !display.equalsIgnoreCase(target.toString()))
                    throw new IOException("junction reparse payload targets another path");
            }
        }
        Path finalPath() throws IOException {
            char[] chars = new char[32_768]; int length = Api.VALUE.GetFinalPathNameByHandleW(handle, chars, chars.length, 0);
            if (length <= 0 || length >= chars.length) throw win32("directory final path");
            String path = new String(chars, 0, length);
            if (!path.startsWith("\\\\?\\")) throw new IOException("local final Win32 path required");
            return Path.of(path.substring(4)).normalize();
        }
        @Override public void close() throws IOException { if (!Api.VALUE.CloseHandle(handle)) throw win32("directory handle close"); }
    }
    private static DirectoryHandle open(Path path, boolean noFollow, boolean write, boolean allowReparse) throws IOException {
        normalized(path);
        HANDLE handle = Api.VALUE.CreateFileW(new WString(nativePath(path)), write ? 0x40000080 : 0x80,
                3, null, 3, BACKUP_SEMANTICS | (noFollow ? OPEN_REPARSE_POINT : 0), null);
        if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw win32("directory handle open");
        DirectoryHandle result = new DirectoryHandle(handle);
        try {
            result.identity(); if (!allowReparse) result.ordinaryIdentity(); return result;
        } catch (IOException | RuntimeException failure) {
            try { result.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
            throw failure;
        }
    }
    private static Memory mountPoint(Path target) throws IOException {
        byte[] substitute = ("\\??\\" + target).getBytes(StandardCharsets.UTF_16LE);
        byte[] display = target.toString().getBytes(StandardCharsets.UTF_16LE);
        int bytes = Math.addExact(20, Math.addExact(substitute.length, display.length));
        if (bytes > 16_384) throw new IOException("bounded junction reparse payload required");
        Memory buffer = new Memory(bytes); buffer.clear(); buffer.setInt(0, MOUNT_POINT_TAG); buffer.setShort(4, (short)(bytes - 8));
        buffer.setShort(8, (short)0); buffer.setShort(10, (short)substitute.length);
        buffer.setShort(12, (short)(substitute.length + 2)); buffer.setShort(14, (short)display.length);
        buffer.write(16, substitute, 0, substitute.length); buffer.write(18L + substitute.length, display, 0, display.length); return buffer;
    }
    private static String reparseName(Memory buffer, int totalBytes, int descriptor) throws IOException {
        int offset = Short.toUnsignedInt(buffer.getShort(descriptor)), bytes = Short.toUnsignedInt(buffer.getShort(descriptor + 2));
        if ((offset & 1) != 0 || (bytes & 1) != 0 || bytes == 0 || 16L + offset + bytes + 2 > totalBytes
                || buffer.getShort(16L + offset + bytes) != 0) throw new IOException("bounded terminated UTF16 reparse name required");
        return new String(buffer.getByteArray(16L + offset, bytes), StandardCharsets.UTF_16LE);
    }
    private static String nativePath(Path path) {
        normalized(path); String value = path.toString();
        StrictJson.require(value.length() >= 3 && value.charAt(1) == ':' && value.charAt(2) == '\\', "local absolute drive path required");
        return "\\\\?\\" + value;
    }
    private static void normalized(Path path) {
        StrictJson.require(path != null && path.isAbsolute() && path.normalize().equals(path), "absolute normalized directory path required");
    }
    private static void uint64(String value, boolean zeroAllowed) {
        StrictJson.require(value != null && value.matches(zeroAllowed ? "0|[1-9][0-9]*" : "[1-9][0-9]*")
                && value.length() <= 20 && new BigInteger(value).bitLength() <= 64, "canonical uint64 identity decimal string required");
    }
    private static JsonNode object(JsonNode value) { StrictJson.require(value != null && value.isObject(), "required object"); return value; }
    private static long number(JsonNode row, String field, long minimum) { return StrictJson.integer(row.get(field), minimum, StrictJson.MAX_SAFE_INTEGER); }
    private static Path path(JsonNode row, String field) { Path result = Path.of(text(row, field)); normalized(result); return result; }
    private static String text(JsonNode row, String field) { return StrictJson.text(row.get(field)); }
    private static void equal(JsonNode row, String field, String expected) { StrictJson.require(expected.equals(text(row, field)), "exact " + field); }
    private static void trueValue(JsonNode value, String message) { StrictJson.require(value != null && value.isBoolean() && value.booleanValue(), message); }
    private static void falseValue(JsonNode value, String message) { StrictJson.require(value != null && value.isBoolean() && !value.booleanValue(), message); }
    private static IOException win32(String operation) { return new IOException(operation + " Win32=" + Native.getLastError()); }
}
