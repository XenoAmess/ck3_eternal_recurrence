package org.xar.ck3.control.wave2.runtime.clockreader;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.channels.OverlappingFileLockException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.StandardCopyOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.AttemptFingerprint;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.ContentEvidenceRef;
import org.xar.ck3.control.reconciliation.LateOutcome.Evidence;
import org.xar.ck3.control.reconciliation.LateOutcome.Read;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockPinnedFiles.Pin;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockQueueProtocol.Artifact;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockQueueProtocol.Collected;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.OriginalQueueReadPort;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadCommand;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadLedger;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.TimeSource;

/** Concrete fixed-read file transport to the existing original Queue. No MCP/native client is created. */
public final class OriginalQueueFileReader implements OriginalQueueReadPort, AutoCloseable {
    private final Path root;
    private final Pin channelManifest;
    private final Attempt admitted;
    private final ClockCustodyGuard guard;
    private final TimeSource time;
    private final Instant leaseDeadline;
    private final FileChannel clientLockChannel;
    private final FileLock clientLock;
    private boolean closed;

    public OriginalQueueFileReader(Path existingChannelRoot, Pin channelManifest, Attempt admitted,
                                  ClockCustodyGuard guard, TimeSource time) throws IOException {
        Objects.requireNonNull(existingChannelRoot); this.channelManifest = Objects.requireNonNull(channelManifest);
        this.admitted = Objects.requireNonNull(admitted); this.guard = Objects.requireNonNull(guard); this.time = Objects.requireNonNull(time);
        ClockPinnedFiles.require(existingChannelRoot.isAbsolute() && !Files.isSymbolicLink(existingChannelRoot), "admitted absolute channel directory");
        this.root = existingChannelRoot.toRealPath();
        ClockPinnedFiles.require(channelManifest.contentStamp().realPath().equals(root.resolve("CHANNEL.json").toRealPath()),
                "manifest must measure this original channel's actual CHANNEL.json");
        for (String name : List.of("requests", "replies", "originals", "guards", "receipts")) {
            Path directory = root.resolve(name);
            ClockPinnedFiles.require(Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS)
                    && directory.toRealPath().startsWith(root) && !Files.isSymbolicLink(directory), "pre-created admitted channel directories required");
        }
        this.leaseDeadline = ClockQueueProtocol.channel(ClockPinnedFiles.read(channelManifest, ClockQueueProtocol.CONTROL_BYTES), admitted).leaseDeadline();
        guard.verify(admitted);
        FileChannel opened = FileChannel.open(root.resolve("JAVA-READER.lock"), StandardOpenOption.CREATE, StandardOpenOption.WRITE);
        FileLock acquired;
        try {
            acquired = opened.tryLock();
            if (acquired == null) { throw new IOException("another Java client holds original Queue reader custody"); }
        } catch (IOException | OverlappingFileLockException error) {
            opened.close(); throw new IOException("cannot borrow exclusive original Queue reader custody", error);
        }
        this.clientLockChannel = opened; this.clientLock = acquired;
    }
    @Override public synchronized void verifyCustody(Attempt expected) throws IOException {
        ensureOpen();
        ClockPinnedFiles.require(!Files.exists(root.resolve("ACTIVE-READ.json"), LinkOption.NOFOLLOW_LINKS), "outstanding original read retained; collect evidence, never submit a replacement");
        Instant currentLease = ClockQueueProtocol.channel(ClockPinnedFiles.read(channelManifest, ClockQueueProtocol.CONTROL_BYTES), expected).leaseDeadline();
        ClockPinnedFiles.require(currentLease.equals(leaseDeadline) && time.now().utc().isBefore(leaseDeadline), "original channel lease expired or changed");
        guard.verify(expected);
    }
    @Override public synchronized int completedReadCount(Attempt expected) throws IOException {
        ensureOpen(); ClockPinnedFiles.require(AttemptFingerprint.sha256(expected).equals(AttemptFingerprint.sha256(admitted)), "different channel attempt");
        return completed().size();
    }
    @Override public synchronized void verifyCompleteLedger(Attempt expected, ReadLedger supplied) throws IOException {
        ensureOpen(); ClockPinnedFiles.require(AttemptFingerprint.sha256(expected).equals(AttemptFingerprint.sha256(admitted)), "different channel attempt");
        List<Collected> records = completed();
        // The planner reports HISTORY_INCOMPLETE for differing counts, retaining that explicit outcome.
        if (records.size() != supplied.reads().size()) { return; }
        try {
            for (int index = 0; index < records.size(); index++) {
                Collected record = records.get(index);
                byte[] requestRaw = ClockPinnedFiles.readBounded(confined(root.resolve("receipts").resolve("INTENT-" + record.ticket() + ".json")), ClockQueueProtocol.CONTROL_BYTES);
                var command = ClockQueueProtocol.preservedRequest(requestRaw, expected);
                ClockPinnedFiles.require(record.ticket().equals(command.ticket()), "preserved intent ticket differs");
                byte[] rawReply = ClockPinnedFiles.readBounded(confined(root.resolve("replies").resolve(record.ticket() + ".json")), ClockQueueProtocol.CONTROL_BYTES);
                ClockPinnedFiles.require(ClockPinnedFiles.hash(rawReply).equals(record.replySha256()), "preserved reply changed during history verification");
                var reply = ClockQueueProtocol.reply(rawReply, command);
                ClockPinnedFiles.require(record.sequence() == reply.sequence(), "preserved completion sequence differs");
                Evidence evidence = record.evidence(expected, reply.originalRow());
                guardReceipt(reply.guardBefore(), "before", command, reply.sequence()); guardReceipt(reply.guardAfter(), "after", command, reply.sequence());
                Read original = ClockMcpRowDecoder.decode(artifact(reply.originalRow(), 32 * 1024 * 1024), command.kind(), evidence, command.maximumRawReplyBytes());
                ClockPinnedFiles.require(original.equals(supplied.reads().get(index)), "caller history differs from preserved original read facts");
            }
        } catch (ContractViolationException error) { throw new IOException("preserved original read history rejected", error); }
    }
    @Override public synchronized Read read(ReadCommand command) throws IOException, InterruptedException {
        verifyCustody(command.attempt());
        ClockPinnedFiles.require(!command.hardDeadline().isAfter(leaseDeadline), "read cannot extend original channel lease");
        List<Collected> prior = completed(); ClockPinnedFiles.require(prior.size() < 64, "original read count exhausted");
        long previousSequence = prior.isEmpty() ? admitted.original().autoSequence() : prior.get(prior.size() - 1).sequence();
        var before = guard.verify(command.attempt());
        byte[] request = ClockQueueProtocol.request(command); Path active = root.resolve("ACTIVE-READ.json");
        createOnly(active, request); // An exception after this point intentionally leaves unresolved intent in place.
        try {
            publish(root.resolve("requests").resolve(command.ticket() + ".json"), request);
            Path replyPath = root.resolve("replies").resolve(command.ticket() + ".json");
            long began = time.now().elapsedMillis();
            while (!Files.exists(replyPath, LinkOption.NOFOLLOW_LINKS)) {
                var tick = time.now();
                if (tick.elapsedMillis() - began >= command.remainingMillis() || !tick.utc().isBefore(command.hardDeadline())
                        || !tick.utc().isBefore(leaseDeadline)) { throw new IOException("fixed read timeout; original ticket retained: " + command.ticket()); }
                time.waitMillis(Math.min(25, command.remainingMillis() - (tick.elapsedMillis() - began)));
            }
            byte[] rawReply = ClockPinnedFiles.readBounded(confined(replyPath), ClockQueueProtocol.CONTROL_BYTES);
            var reply = ClockQueueProtocol.reply(rawReply, command);
            ClockPinnedFiles.require(reply.sequence() > previousSequence, "owner read sequence repeated or regressed");
            byte[] rawRow = artifact(reply.originalRow(), 32 * 1024 * 1024);
            guardReceipt(reply.guardBefore(), "before", command, reply.sequence());
            guardReceipt(reply.guardAfter(), "after", command, reply.sequence());
            var after = guard.verify(command.attempt()); var received = time.now();
            Evidence evidence = new Evidence(before.scope(), after.scope(), reply.sequence(),
                    new ContentEvidenceRef(reply.originalRow().sha256(), reply.originalRow().bytes(), reply.originalRow().relativePath()),
                    received.elapsedMillis(), received.utc(), after.game().win32UptimeMillis());
            Read decoded = ClockMcpRowDecoder.decode(rawRow, command.kind(), evidence, command.maximumRawReplyBytes());
            Collected receipt = new Collected(AttemptFingerprint.sha256(command.attempt()), command.ticket(), reply.sequence(),
                    ClockPinnedFiles.hash(rawReply), evidence.receivedElapsedMillis(), evidence.observedAt(), evidence.readerWin32UptimeMillis());
            createOnly(root.resolve("receipts").resolve("COMPLETED-" + command.ticket() + ".json"), ClockQueueProtocol.collected(receipt, command.attempt()));
            // Archive the exact original intent with create-only semantics; never delete/rewrite a prior read.
            createOnly(root.resolve("receipts").resolve("INTENT-" + command.ticket() + ".json"), request);
            Files.delete(active);
            return decoded;
        } catch (ContractViolationException error) {
            throw new IOException("fixed read contract rejected; original request and raw response retained: " + command.ticket(), error);
        }
    }
    private List<Collected> completed() throws IOException {
        List<Collected> records = new ArrayList<>();
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(root.resolve("receipts"), "COMPLETED-*.json")) {
            for (Path path : stream) {
                ClockPinnedFiles.require(records.size() < 64, "bounded complete read ledger");
                String name = path.getFileName().toString(); String nameTicket = name.substring("COMPLETED-".length(), name.length() - ".json".length());
                Collected row = completion(nameTicket);
                String ticket = row.ticket();
                ClockPinnedFiles.require(path.getFileName().toString().equals("COMPLETED-" + ticket + ".json"), "ledger ticket mismatch");
                byte[] reply = ClockPinnedFiles.readBounded(confined(root.resolve("replies").resolve(ticket + ".json")), ClockQueueProtocol.CONTROL_BYTES);
                ClockPinnedFiles.require(ClockPinnedFiles.hash(reply).equals(row.replySha256()), "preserved reply changed after collection");
                records.add(row);
            }
        }
        records.sort(Comparator.comparingLong(Collected::sequence)); long previous = admitted.original().autoSequence();
        for (Collected record : records) { ClockPinnedFiles.require(record.sequence() > previous, "duplicate/regressed completed sequence"); previous = record.sequence(); }
        return List.copyOf(records);
    }
    private Collected completion(String ticket) throws IOException {
        ClockPinnedFiles.require(ticket.matches("[0-9a-f]{32}"), "canonical completion ticket");
        try {
            return ClockQueueProtocol.collected(ClockPinnedFiles.readBounded(confined(root.resolve("receipts").resolve("COMPLETED-" + ticket + ".json")),
                    ClockQueueProtocol.CONTROL_BYTES), admitted);
        } catch (ContractViolationException error) { throw new IOException("preserved collected receipt rejected", error); }
    }
    private void guardReceipt(Artifact descriptor, String phase, ReadCommand command, long sequence) throws IOException {
        ClockPinnedFiles.require(descriptor.relativePath().startsWith("guards/"), "original guard observation artifact required");
        JsonNode row = StrictJson.object(StrictJson.parse(artifact(descriptor, 65_536)), Set.of("schema", "phase", "read_sequence", "session_id", "attempt_sha256", "original_guard"));
        ClockPinnedFiles.require("xar.clock-fixed-reader-source-observation/v1".equals(StrictJson.text(row.get("schema")))
                && phase.equals(StrictJson.text(row.get("phase"))) && sequence == StrictJson.integer(row.get("read_sequence"), 1, StrictJson.MAX_SAFE_INTEGER)
                && admitted.scope().sessionId().equals(StrictJson.text(row.get("session_id")))
                && AttemptFingerprint.sha256(command.attempt()).equals(StrictJson.text(row.get("attempt_sha256"))), "original guard observation binding mismatch");
        ClockPinnedFiles.require(row.get("original_guard").isObject() || row.get("original_guard").isNull(), "preserved original guard observation shape");
        // The old observation is preserved, not translated into a qualification bool. Original guard still executes at the Queue.
    }
    private byte[] artifact(Artifact descriptor, int maximumBytes) throws IOException {
        ClockPinnedFiles.require(descriptor.bytes() <= maximumBytes, "artifact exceeds role-specific budget");
        byte[] raw = ClockPinnedFiles.readBounded(confined(root.resolve(descriptor.relativePath())), maximumBytes);
        ClockPinnedFiles.require(raw.length == descriptor.bytes() && ClockPinnedFiles.hash(raw).equals(descriptor.sha256()), "original artifact length/digest changed"); return raw;
    }
    private Path confined(Path path) throws IOException {
        Path normalized = path.toAbsolutePath().normalize();
        ClockPinnedFiles.require(normalized.startsWith(root) && !Files.isSymbolicLink(normalized)
                && normalized.toRealPath().startsWith(root), "artifact escaped original channel root"); return normalized;
    }
    private static void createOnly(Path path, byte[] raw) throws IOException {
        try (FileChannel file = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(raw); while (buffer.hasRemaining()) { file.write(buffer); } file.force(true);
        }
    }
    private static void publish(Path path, byte[] raw) throws IOException {
        Path staging = path.resolveSibling(path.getFileName() + ".publishing");
        createOnly(staging, raw);
        // There is one lock-held Java publisher and a unique ticket. Never expose an incomplete request.
        ClockPinnedFiles.require(!Files.exists(path, LinkOption.NOFOLLOW_LINKS), "request ticket already exists");
        Files.move(staging, path, StandardCopyOption.ATOMIC_MOVE);
    }
    private void ensureOpen() throws IOException { ClockPinnedFiles.require(!closed && clientLock.isValid(), "original Queue client custody closed"); }
    @Override public synchronized void close() throws IOException {
        if (!closed) { closed = true; try { clientLock.release(); } finally { clientLockChannel.close(); } }
    }
}
