package org.xar.ck3.control.build;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** Actual Win32 raw-file port. Identity decoding remains exclusively SharedSourceFiles. */
final class RawWindowNativeIo implements RawWindowCollector.Ports {
    interface ReadApi extends StdCallLibrary {
        boolean SetFilePointerEx(HANDLE file, long distance, LongByReference newPosition, int method);
        boolean ReadFile(HANDLE file, Pointer output, int requested, IntByReference returned, Pointer overlapped);
        int GetFinalPathNameByHandleW(HANDLE file, char[] output, int capacity, int flags);
    }
    private static final class Api { private static final ReadApi VALUE = Native.load("kernel32", ReadApi.class, W32APIOptions.UNICODE_OPTIONS); }
    private final NamedInput request;
    private final Path input, root;
    private HANDLE source, heldDirectory;
    private FileChannel journal;
    private long journalBytes, apiCharge;
    private boolean poisoned;
    /** Internal I/O settings only; no Admission, read scope or machine qualification is minted here. */
    record NamedInput(String inputPath, String outputRoot, SharedSourceFiles.DirectoryIdentity outputRootIdentity,
                      long fileIdentityApiBufferCap, int journalMaximumBytes, int bodyMaximumBytes) {
        NamedInput {
            absolute(inputPath); absolute(outputRoot); java.util.Objects.requireNonNull(outputRootIdentity);
            require(fileIdentityApiBufferCap > 0 && fileIdentityApiBufferCap <= MAX_OUTPUT_BYTES,
                    "bounded identity API buffer settings required");
            require(journalMaximumBytes > 0 && journalMaximumBytes <= MAX_OUTPUT_BYTES
                    && bodyMaximumBytes > 0 && bodyMaximumBytes <= MAX_OUTPUT_BYTES,
                    "bounded durable output settings required");
        }
    }
    RawWindowNativeIo(CaptureRequest request) {
        this(new NamedInput(request.inputPath(), request.outputRoot(), request.outputRootIdentity(),
                request.fileIdentityApiBufferCap(), request.journalMaximumBytes(), request.bodyMaximumBytes()));
    }
    private RawWindowNativeIo(NamedInput request) {
        this.request = java.util.Objects.requireNonNull(request);
        input = Path.of(request.inputPath()); root = Path.of(request.outputRoot());
    }
    static RawWindowNativeIo namedFrontend(NamedInput request) { return new RawWindowNativeIo(request); }

    @Override public String machineId() { return WindowsJobProcess.currentMachineId(); }
    @Override public void startJournal(Started started) throws IOException {
        startMetadataJournal(RawWindowCaptureJson.encode(started));
    }
    /** A closed caller supplies its own typed event; the shared sink accepts one strict bounded object line. */
    void startMetadataJournal(byte[] exactOneLineJson) throws IOException {
        byte[] first;
        try { first = metadataLine(exactOneLineJson); }
        catch (IOException | RuntimeException failure) { poisoned = true; throw failure; }
        if (poisoned) throw new IOException("durable fallback poisoned before open");
        if (journal != null || heldDirectory != null) throw new IOException("one fresh capture journal required");
        charge(140 + ancestors(root));
        if (!SharedSourceFiles.nativeDirectory(root).equals(request.outputRootIdentity())) throw new IOException("output root native identity differs");
        heldDirectory = valid(Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(root), 0x81, 3, null, 3, 0x02200000, null));
        charge(140);
        // This public helper is the C23 addition and delegates the existing decoder with directory=true.
        if (!identity(SharedSourceFiles.nativeHeldDirectory(heldDirectory)).equals(request.outputRootIdentity())) throw new IOException("held output directory differs");
        journal = FileChannel.open(child("fallback.jsonl"), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        appendMetadata(first);
    }
    @Override public void append(Event event) throws IOException { appendMetadata(RawWindowCaptureJson.encode(event)); }
    void appendMetadata(byte[] exactOneLineJson) throws IOException {
        if (journal == null || poisoned) throw new IOException("durable fallback unavailable; no further native input");
        try {
            byte[] encoded = metadataLine(exactOneLineJson);
            if (journalBytes + encoded.length + 1 > request.journalMaximumBytes())
                throw new IOException("bounded fallback event/budget exceeded before further input");
            ByteBuffer bytes = ByteBuffer.allocate(encoded.length + 1).put(encoded).put((byte) '\n'); bytes.flip();
            while (bytes.hasRemaining()) {
                int written = journal.write(bytes); if (written <= 0) throw new IOException("fallback write made no progress"); journalBytes += written;
            }
            journal.force(true);
        } catch (IOException | RuntimeException failure) { poisoned = true; throw failure; }
    }
    private static byte[] metadataLine(byte[] original) throws IOException {
        if (original == null || original.length == 0 || original.length > 4095)
            throw new IOException("one bounded nonempty metadata object line required");
        byte[] encoded = Arrays.copyOf(original, original.length);
        for (byte value : encoded) if (value == 10 || value == 13)
            throw new IOException("raw metadata CR/LF is forbidden");
        java.nio.charset.StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(ByteBuffer.wrap(encoded));
        var mapper = ControlBuild.strictMapper();
        try (var parser = mapper.getFactory().createParser(encoded)) {
            var object = mapper.readTree(parser);
            if (object == null || !object.isObject() || parser.nextToken() != null)
                throw new IOException("one complete metadata JSON object required");
        }
        return encoded;
    }
    @Override public void openInput() throws IOException {
        if (journal == null || poisoned || source != null) throw new IOException("one forced fallback before the held input open required");
        charge(ancestors(input)); SharedSourceFiles.plainAncestors(input);
        source = valid(Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(input), 0x80000000, 1, null, 3, 0x00200000, null));
    }
    @Override public FileProbe held() throws IOException {
        if (source == null) throw new IOException("actual source handle absent");
        charge(140 + 2052); SharedSourceFiles.NativeFile actual = SharedSourceFiles.nativeHeldFile(source);
        char[] output = new char[1024]; int count = Api.VALUE.GetFinalPathNameByHandleW(source, output, output.length, 0);
        if (count <= 0 || count >= output.length) throw nativeError("actual held final path");
        return new FileProbe(ProbeStatus.OBSERVED, actual, new String(output, 0, count), "");
    }
    @Override public FileProbe path() throws IOException {
        charge(140 + ancestors(input));
        // This branch reports actual reopened path metadata, with explicit null for an unqueried final path.
        return new FileProbe(ProbeStatus.OBSERVED, SharedSourceFiles.nativeFile(input), null, "");
    }
    @Override public DirectoryProbe directory() throws IOException {
        if (heldDirectory == null) throw new IOException("actual retained output directory absent");
        charge(280 + ancestors(root));
        SharedSourceFiles.DirectoryIdentity held = identity(SharedSourceFiles.nativeHeldDirectory(heldDirectory));
        SharedSourceFiles.DirectoryIdentity path = SharedSourceFiles.nativeDirectory(root);
        if (!held.equals(path)) throw new IOException("held/path output directory drift");
        return new DirectoryProbe(ProbeStatus.OBSERVED, path, "");
    }
    @Override public ReadResult read(ReadRange window) throws IOException {
        if (source == null || journal == null || poisoned) throw new IOException("held source and durable fallback required");
        LongByReference position = new LongByReference();
        if (!Api.VALUE.SetFilePointerEx(source, window.fileOffset(), position, 0) || position.getValue() != window.fileOffset())
            return new ReadResult(ReadStatus.NATIVE_ERROR, new byte[0], Native.getLastError(), "exact finite seek failed; ReadFile not called");
        try (Memory memory = new Memory(window.length())) {
            memory.clear(); IntByReference returned = new IntByReference();
            boolean success = Api.VALUE.ReadFile(source, memory, window.length(), returned, Pointer.NULL);
            int error = success ? 0 : Native.getLastError(), count = returned.getValue();
            if (count < 0 || count > window.length()) return new ReadResult(ReadStatus.OUTCOME_UNKNOWN, null, error, "Win32 returned an invalid bounded count");
            byte[] actual = memory.getByteArray(0, count);
            return new ReadResult(success ? (count == window.length() ? ReadStatus.COMPLETE : ReadStatus.SHORT_READ) : ReadStatus.NATIVE_ERROR,
                    actual, error, success ? "" : "ReadFile returned false; reported partial bytes retained");
        }
    }
    @Override public RawArtifact preserveRaw(int index, byte[] actual) throws IOException {
        String name = String.format(java.util.Locale.ROOT, "window-%03d.raw", index); Path destination = child(name);
        createNew(destination, actual);
        if (!Arrays.equals(actual, Files.readAllBytes(destination))) throw new IOException("new raw window readback differs");
        return new RawArtifact(OutputStatus.CREATED_VERIFIED, name, (long) actual.length, RawWindowCaptureJson.hash(actual), "");
    }
    @Override public void publishBody(byte[] complete) throws IOException {
        if (complete.length > request.bodyMaximumBytes()) throw new IOException("complete body exceeds reserved maximum");
        Path destination = child("capture.json"); createNew(destination, complete);
        if (!Arrays.equals(complete, Files.readAllBytes(destination))) throw new IOException("complete body readback differs");
    }
    @Override public long fileIdentityApiBufferChargeUpper() { return apiCharge; }
    @Override public CloseStatus closeInput() {
        if (source == null) return CloseStatus.NOT_OPENED;
        if (!Kernel32.INSTANCE.CloseHandle(source)) return CloseStatus.FAILED; source = null; return CloseStatus.CLOSED;
    }
    @Override public void close() throws IOException {
        IOException failure = null;
        if (source != null) { if (!Kernel32.INSTANCE.CloseHandle(source)) failure = nativeError("source cleanup close"); else source = null; }
        if (heldDirectory != null) { if (!Kernel32.INSTANCE.CloseHandle(heldDirectory)) failure = nativeError("directory cleanup close"); else heldDirectory = null; }
        if (journal != null) { try { journal.close(); } catch (IOException error) { failure = error; } journal = null; }
        if (failure != null) throw failure;
    }
    private Path child(String name) throws IOException {
        Path path = root.resolve(name);
        if (!path.getParent().equals(root) || Files.exists(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("new exact output child already exists"); return path;
    }
    private static void createNew(Path path, byte[] complete) throws IOException {
        try (FileChannel output = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(complete);
            while (buffer.hasRemaining()) { if (output.write(buffer) <= 0) throw new IOException("new output write made no progress"); }
            output.force(true);
        }
    }
    private void charge(long upper) throws IOException {
        long next = Math.addExact(apiCharge, upper);
        if (next > request.fileIdentityApiBufferCap()) throw new IOException("finite file-identity API buffer upper budget exhausted before probe"); apiCharge = next;
    }
    private static long ancestors(Path path) { long result = 0; for (Path p = path; p != null; p = p.getParent()) result += 4; return result; }
    private static SharedSourceFiles.DirectoryIdentity identity(SharedSourceFiles.NativeFile value) {
        return new SharedSourceFiles.DirectoryIdentity(value.volumeSerialDecimal(), value.fileIdDecimal(), value.creationFiletimeDecimal());
    }
    private static HANDLE valid(HANDLE value) throws IOException {
        if (value == null || WinBase.INVALID_HANDLE_VALUE.equals(value)) throw nativeError("open native capture resource"); return value;
    }
    private static IOException nativeError(String operation) { return new IOException(operation + " Win32=" + Native.getLastError()); }
}

