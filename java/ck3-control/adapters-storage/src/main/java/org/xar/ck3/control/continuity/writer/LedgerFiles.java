package org.xar.ck3.control.continuity.writer;

import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.WString;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.win32.StdCallLibrary;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Optional;
import java.util.UUID;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.WindowsFileIdentity;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Bounded, identity-bearing reads plus same-volume write-through Win32 rename. */
final class LedgerFiles {
    private LedgerFiles() { }
    interface MoveApi extends StdCallLibrary { boolean MoveFileExW(WString existing, WString destination, int flags); }
    private static final class Api { static final MoveApi VALUE = Native.load("kernel32", MoveApi.class); }
    record Document(Pin pin, byte[] bytes) {
        Document { bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    /** Actual full first read/hash plus same-thread OS custody; never a Pin-only cache. */
    static final class LeasedDocument implements AutoCloseable {
        private final IdentityBearingFileAttributes.ReadOnlyLease lease;
        private final Document document;
        private LeasedDocument(IdentityBearingFileAttributes.ReadOnlyLease lease, Document document) {
            this.lease = lease; this.document = document;
        }
        /** Captured acquisition DATA, usable to decode the first commit before final pair qualification. */
        Document original() { return document; }
        Document read() throws IOException {
            BasicFileAttributes actual = lease.verifyCurrent();
            WindowsFileIdentity key = (WindowsFileIdentity) actual.fileKey();
            FileIdentity identity = new FileIdentity(key.volumeSerialDecimal(), key.fileIdDecimal(), key.creationFiletimeDecimal(),
                    actual.lastModifiedTime().toInstant().toString(), actual.size());
            if (!document.pin().identity().equals(identity)) throw new IOException("leased original full identity drift");
            return document;
        }
        @Override public void close() throws IOException { lease.close(); }
        long retainedBytes() { return document.bytes.length; }
    }
    static LeasedDocument lease(Path path, int maximum) throws IOException {
        IdentityBearingFileAttributes.ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(path, maximum);
        try {
            var observed = lease.originalRead();
            BasicFileAttributes after = observed.attributes();
            WindowsFileIdentity key = (WindowsFileIdentity) after.fileKey();
            FileIdentity identity = new FileIdentity(key.volumeSerialDecimal(), key.fileIdDecimal(), key.creationFiletimeDecimal(),
                    after.lastModifiedTime().toInstant().toString(), after.size());
            byte[] raw = observed.bytes();
            Document document = new Document(new Pin(new ExactRef(path.toAbsolutePath().normalize().toString(), raw.length, sha(raw)), identity), raw);
            lease.releaseOriginalBytes();
            return new LeasedDocument(lease, document);
        } catch (IOException | RuntimeException | Error failure) {
            try { lease.close(); } catch (IOException closing) { failure.addSuppressed(closing); }
            throw failure;
        }
    }
    static LeasedDocument lease(ExactRef expected, int maximum) throws IOException {
        LeasedDocument lease = lease(Path.of(expected.path()), maximum);
        try {
            Document actual = lease.original();
            if (actual.pin().reference().bytes() != expected.bytes() || !actual.pin().reference().sha256().equals(expected.sha256())
                    || !Path.of(expected.path()).toAbsolutePath().normalize().equals(Path.of(actual.pin().reference().path())))
                throw new IOException("leased original bytes/SHA/path changed");
            return new LeasedDocument(lease.lease, new Document(new Pin(expected, actual.pin().identity()), actual.bytes));
        } catch (IOException | RuntimeException | Error failure) {
            try { lease.close(); } catch (IOException closing) { failure.addSuppressed(closing); }
            throw failure;
        }
    }

    static FileIdentity identity(Path path) throws IOException {
        if (!Platform.isWindows()) throw new IOException("native Windows file identity required");
        Path absolute = path.toAbsolutePath().normalize();
        BasicFileAttributes value = IdentityBearingFileAttributes.read(absolute);
        if (!value.isRegularFile() || value.isSymbolicLink() || !(value.fileKey() instanceof WindowsFileIdentity key)) {
            throw new IOException("ordinary identity-bearing ledger file required");
        }
        return new FileIdentity(key.volumeSerialDecimal(), key.fileIdDecimal(), key.creationFiletimeDecimal(),
                value.lastModifiedTime().toInstant().toString(), value.size());
    }
    static Document read(Path path, int limit) throws IOException {
        var observed = IdentityBearingFileAttributes.readBoundedWindows(path, limit);
        BasicFileAttributes after = observed.attributes();
        WindowsFileIdentity key = (WindowsFileIdentity) after.fileKey();
        FileIdentity identity = new FileIdentity(key.volumeSerialDecimal(), key.fileIdDecimal(), key.creationFiletimeDecimal(),
                after.lastModifiedTime().toInstant().toString(), after.size());
        byte[] raw = observed.bytes();
        return new Document(new Pin(new ExactRef(path.toAbsolutePath().normalize().toString(), raw.length, sha(raw)), identity), raw);
    }
    static Document exact(ExactRef expected, int maximum) throws IOException {
        Document actual = read(Path.of(expected.path()), maximum);
        if (actual.pin().reference().bytes() != expected.bytes() || !actual.pin().reference().sha256().equals(expected.sha256())
                || !Path.of(expected.path()).toAbsolutePath().normalize().equals(Path.of(actual.pin().reference().path())))
            throw new IOException("named source bytes/SHA/path changed: path=" + expected.path()
                    + ", expected_bytes=" + expected.bytes() + ", actual_bytes=" + actual.pin().reference().bytes()
                    + ", expected_sha256=" + expected.sha256() + ", actual_sha256=" + actual.pin().reference().sha256());
        return new Document(new Pin(expected, actual.pin().identity()), actual.bytes);
    }
    static Optional<Document> optional(Path path) throws IOException {
        return optional(path, ContinuityJson.DOCUMENT_MAX_BYTES);
    }
    static Optional<Document> optional(Path path, int maximum) throws IOException {
        try { return Optional.of(read(path, maximum)); }
        catch (NoSuchFileException absent) { return Optional.empty(); }
    }
    static void verify(Pin original) throws IOException {
        if (original.reference().bytes() > MAX_PIN_BYTES) throw new IOException("source pin exceeds explicit native artifact bound");
        Document again = exact(original.reference(), MAX_PIN_BYTES);
        if (!again.pin().equals(original)) throw new IOException("source content/identity changed after preparation");
    }
    static void requireAbsent(Path path) throws IOException {
        if (Files.exists(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("expected absent ledger path appeared: " + path);
        // Access denied must never be interpreted as absence.
        try { Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS); }
        catch (NoSuchFileException expected) { return; }
        throw new IOException("ledger absence not established: " + path);
    }
    /** One fully quoted physical atomic operation; its pending path is fixed before admission. */
    record AtomicWrite(Path target,Path temporary,byte[] bytes,boolean replace) {
        AtomicWrite { bytes=bytes.clone(); }
        @Override public byte[] bytes(){return bytes.clone();}
        java.util.List<StorageWriteGuard.Mutation> mutations(){
            return java.util.List.of(new StorageWriteGuard.FileCreate(temporary,bytes.length),
                    new StorageWriteGuard.FileRename(temporary,target,replace));
        }
    }
    static AtomicWrite prepareAtomic(Path target,byte[] canonical,boolean replace)throws IOException {
        return prepareAtomic(target,canonical,replace,ContinuityJson.DOCUMENT_MAX_BYTES);
    }
    static AtomicWrite prepareAtomic(Path target,byte[] canonical,boolean replace,int maximum)throws IOException {
        if(maximum<=0||maximum>ContinuityJson.LEDGER_MAX_BYTES)throw new IOException("invalid ledger maximum");
        target=target.toAbsolutePath().normalize();
        byte[] raw=Arrays.copyOf(canonical,canonical.length+1);raw[raw.length-1]='\n';
        if(raw.length>maximum)throw new IOException("original writer output cap");
        Path temp=target.resolveSibling(target.getFileName()+"."+UUID.randomUUID().toString().replace("-","")+".pending");
        return new AtomicWrite(target,temp,raw,replace);
    }
    static StorageWriteGuard.WritePlan plan(Path originalLock,java.util.List<AtomicWrite> writes) {
        return new StorageWriteGuard.WritePlan(originalLock,writes.stream().flatMap(write->write.mutations().stream()).toList());
    }
    static void atomic(StorageWriteGuard storage,Path originalLock,Path target,byte[] canonical,boolean replace)throws IOException {
        atomic(storage,originalLock,prepareAtomic(target,canonical,replace));
    }
    static void atomic(StorageWriteGuard storage,Path originalLock,AtomicWrite write)throws IOException {
        java.util.Objects.requireNonNull(storage);WindowsLedgerLock.requireHeld(originalLock);
        if(!Platform.isWindows())throw new IOException("qualified Windows rename required");
        if(!write.replace())requireAbsent(write.target());
        storage.write(plan(originalLock,java.util.List.of(write)),()->{
            byte[] raw=write.bytes();
            storage.write(new StorageWriteGuard.WritePlan(originalLock,java.util.List.of(
                    new StorageWriteGuard.FileCreate(write.temporary(),raw.length))),()->{
                try(FileChannel channel=FileChannel.open(write.temporary(),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
                    ByteBuffer buffer=ByteBuffer.wrap(raw);while(buffer.hasRemaining())channel.write(buffer);channel.force(true);
                }
                return null;
            });
            // No COPY_ALLOWED: same-volume commit. The guard owns exact native accounting.
            storage.write(new StorageWriteGuard.WritePlan(originalLock,java.util.List.of(
                    new StorageWriteGuard.FileRename(write.temporary(),write.target(),write.replace()))),()->{
                if(!Api.VALUE.MoveFileExW(new WString(winPath(write.temporary())),new WString(winPath(write.target())),
                        8|(write.replace()?1:0)))throw new IOException("ledger atomic rename Win32="+Native.getLastError());
                return null;
            });
            Document persisted=read(write.target(),write.bytes().length);
            if(!Arrays.equals(raw,persisted.bytes()))throw new IOException("ledger committed readback differs");
            return null;
        });
        // A failed physical operation retains its original pending file and UNKNOWN reservation.
        // Neither deletion nor a guessed release may bypass the same storage scope.
    }
    /** The archive uses the same guarded, same-volume no-replace rename primitive. */
    static void moveCreateNew(StorageWriteGuard storage,Path originalLock,Path staging,Path target)throws IOException {
        java.util.Objects.requireNonNull(storage);WindowsLedgerLock.requireHeld(originalLock);
        if(!Platform.isWindows())throw new IOException("Windows same-volume rename required");
        var mutation=new StorageWriteGuard.FileRename(staging.toAbsolutePath().normalize(),target.toAbsolutePath().normalize(),false);
        storage.write(new StorageWriteGuard.WritePlan(originalLock,java.util.List.of(mutation)),()->{
            if(!Api.VALUE.MoveFileExW(new WString(winPath(staging)),new WString(winPath(target)),8))
                throw new IOException("immutable archive rename Win32="+Native.getLastError());
            return null;
        });
    }
    static String winPath(Path path) {
        String value = path.toAbsolutePath().normalize().toString();
        if (value.startsWith("\\\\?\\")) return value;
        return value.startsWith("\\\\") ? "\\\\?\\UNC\\" + value.substring(2) : "\\\\?\\" + value;
    }
    static String sha(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    static void moveCreateNewNoForce(StorageWriteGuard storage,Path originalLock,Path staging,Path target)throws IOException {
        java.util.Objects.requireNonNull(storage);WindowsLedgerLock.requireHeld(originalLock);
        if(!Platform.isWindows())throw new IOException("Windows same-volume rename required");
        var mutation=new StorageWriteGuard.FileRename(staging.toAbsolutePath().normalize(),target.toAbsolutePath().normalize(),false);
        storage.write(new StorageWriteGuard.WritePlan(originalLock,java.util.List.of(mutation)),()->{
            if(!Api.VALUE.MoveFileExW(new WString(winPath(staging)),new WString(winPath(target)),0))
                throw new IOException("immutable archive rename Win32="+Native.getLastError());
            return null;
        });
    }
}
