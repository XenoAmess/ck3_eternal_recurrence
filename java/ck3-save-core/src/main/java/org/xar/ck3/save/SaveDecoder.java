package org.xar.ck3.save;

import java.io.ByteArrayOutputStream;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Objects;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.save.SaveContracts.*;

/** One bounded decoder process per selection, with original exit and full-stream validation. */
public final class SaveDecoder {
    private SaveDecoder() { }
    @FunctionalInterface public interface Launcher { Process start(Path decoder, Path save) throws IOException; }
    public static Process launch(Path executable, Path input) throws IOException {
        return new ProcessBuilder(executable.toString(), "melt", input.toString(), "-c", "--format", "ck3", "--unknown-key", "error").start();
    }
    public static Decoded inspect(Pin save, Pin decoder, Selection selection) throws IOException {
        return inspect(save, decoder, selection, DecoderLimits.standard(), SaveDecoder::launch);
    }
    public static Decoded inspect(Pin savePin, Pin decoderPin, Selection selection, DecoderLimits limits, Launcher launcher) throws IOException {
        Objects.requireNonNull(selection); Objects.requireNonNull(limits); Objects.requireNonNull(launcher);
        Path save = Path.of(savePin.path()).toRealPath(); Path decoder = Path.of(decoderPin.path()).toRealPath();
        FilePins.verify(decoder, decoderPin);
        BasicFileAttributes before = Files.readAttributes(save, BasicFileAttributes.class);
        // This is a Java shared read lock and identity recheck, not a Win32 deny-write qualification.
        try (FileChannel channel = FileChannel.open(save, StandardOpenOption.READ); FileLock lock = channel.lock(0, Long.MAX_VALUE, true)) {
            if (!lock.isValid()) throw new IOException("save read lock unavailable");
            FilePins.verify(save, savePin);
            Process process = launcher.start(decoder, save);
            ByteArrayOutputStream diagnostic = new ByteArrayOutputStream();
            AtomicBoolean overflow = new AtomicBoolean(); AtomicReference<IOException> drainFailure = new AtomicReference<>();
            Thread drain = new Thread(() -> drain(process.getErrorStream(), diagnostic, overflow, drainFailure, limits.maxStderrBytes()), "ck3-save-decoder-stderr");
            drain.setDaemon(true); drain.start();
            var watchdog = Executors.newSingleThreadScheduledExecutor(); AtomicBoolean timedOut = new AtomicBoolean();
            var deadline = watchdog.schedule(() -> { timedOut.set(true); process.destroyForcibly(); }, limits.timeout().toMillis(), TimeUnit.MILLISECONDS);
            MessageDigest digest = FilePins.digest();
            try (LimitedInput bytes = new LimitedInput(new DigestInputStream(process.getInputStream(), digest), limits.maxStreamBytes())) {
                SaveContracts.Projection projection = new SaveStream(new InputStreamReader(bytes,
                        StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)), selection).read();
                int code = process.waitFor(); drain.join(10000);
                if (timedOut.get() || drain.isAlive() || drainFailure.get() != null || overflow.get()) throw new IOException("decoder timeout or incomplete stderr");
                String stderr = diagnostic.toString(StandardCharsets.UTF_8);
                if (code != 0) throw new IOException("Rakaly exit " + code + ": " + stderr);
                FilePins.verify(save, savePin); FilePins.verify(decoder, decoderPin);
                BasicFileAttributes after = Files.readAttributes(save, BasicFileAttributes.class);
                if (before.size() != after.size() || !before.lastModifiedTime().equals(after.lastModifiedTime()) || !Objects.equals(before.fileKey(), after.fileKey())) throw new IOException("save physical identity or timestamp changed during inspection");
                return new Decoded(savePin, decoderPin, code, stderr, HexFormat.of().formatHex(digest.digest()), Long.toString(bytes.count), projection, true);
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IOException("offline decoder interrupted", interrupted);
            } finally {
                deadline.cancel(false); watchdog.shutdownNow();
                if (process.isAlive()) {
                    process.destroyForcibly();
                    try { if (!process.waitFor(10, TimeUnit.SECONDS)) throw new IOException("decoder process did not terminate"); }
                    catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException("decoder cleanup interrupted", interrupted); }
                }
                try { drain.join(10000); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException("stderr cleanup interrupted", interrupted); }
                if (drain.isAlive()) throw new IOException("decoder stderr reader did not terminate");
            }
        }
    }
    private static void drain(InputStream stream, ByteArrayOutputStream output, AtomicBoolean overflow, AtomicReference<IOException> failure, int limit) {
        try (stream) {
            byte[] buffer = new byte[8192]; int read;
            while ((read = stream.read(buffer)) != -1) {
                int remaining = limit - output.size();
                output.write(buffer, 0, Math.min(remaining, read)); if (read > remaining) overflow.set(true);
            }
        } catch (IOException error) { failure.set(error); }
    }
    private static final class LimitedInput extends FilterInputStream {
        private final long limit;
        private long count;
        private LimitedInput(InputStream input, long limit) { super(input); this.limit = limit; }
        @Override public int read() throws IOException { int value = in.read(); if (value >= 0) add(1); return value; }
        @Override public int read(byte[] buffer, int offset, int length) throws IOException { int read = in.read(buffer, offset, length); if (read > 0) add(read); return read; }
        private void add(int amount) throws IOException { count += amount; if (count > limit) throw new IOException("melt stream byte cap exceeded"); }
    }
}
