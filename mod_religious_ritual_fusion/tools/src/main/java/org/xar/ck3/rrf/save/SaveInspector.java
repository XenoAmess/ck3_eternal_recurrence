package org.xar.ck3.rrf.save;

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
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.rrf.Json;
import org.xar.ck3.rrf.ReleaseBuilder;
import org.xar.ck3.rrf.save.SaveContracts.Pin;
import org.xar.ck3.rrf.save.SaveContracts.Report;
import org.xar.ck3.rrf.save.SaveContracts.Request;
import org.xar.ck3.rrf.save.SaveContracts.StreamEvidence;

/** Offline Rakaly stdout oracle. No temp melt, copied save, game process, or business mutation. */
public final class SaveInspector {
    private SaveInspector() { }
    public record Receipt(Pin report, int selectedScopes, boolean gameStarted) { }
    public static void main(String[] args) { System.exit(run(args)); }
    public static int run(String[] args) {
        try {
            if (args.length != 4 || !args[0].equals("--inputs") || !args[2].equals("--output")) throw new IllegalArgumentException("inspect-save requires --inputs request.json --output unused-report.json");
            Path inputs = Path.of(args[1]); Path output = Path.of(args[3]).toAbsolutePath().normalize();
            if (Files.size(inputs) > 65536 || Files.exists(output)) throw new IllegalArgumentException("bounded request and unused output required");
            Request request = Json.read(Files.readAllBytes(inputs), Request.class);
            Report report = inspect(request); byte[] bytes = Json.write(report);
            if (bytes.length > 1024 * 1024) throw new IOException("report exceeds one MiB output budget");
            Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
            System.out.println(new String(Json.write(new Receipt(pin(output), report.scopes().size(), false)), StandardCharsets.UTF_8));
            return 0;
        } catch (IOException | IllegalArgumentException error) { System.err.println("RRF SAVE INSPECTION FAILED: " + error.getMessage()); return 1; }
    }
    public static Report inspect(Request request) throws IOException {
        return inspect(request, (decoder, save) -> new ProcessBuilder(decoder.toString(), "melt", save.toString(), "-c", "--format", "ck3", "--unknown-key", "error").start());
    }
    @FunctionalInterface interface DecoderLauncher { Process start(Path decoder, Path save) throws IOException; }
    static Report inspect(Request request, DecoderLauncher launcher) throws IOException {
        Path save = Path.of(request.save().path()).toRealPath(); Path decoder = Path.of(request.decoder().path()).toRealPath();
        verifyPin(decoder, request.decoder()); BasicFileAttributes before = Files.readAttributes(save, BasicFileAttributes.class);
        try (FileChannel channel = FileChannel.open(save, StandardOpenOption.READ); FileLock lock = channel.lock(0, Long.MAX_VALUE, true)) {
            if (!lock.isValid()) throw new IOException("save read lock unavailable");
            verifyPin(save, request.save());
            Process process = launcher.start(decoder, save);
            ByteArrayOutputStream diagnostic = new ByteArrayOutputStream(); AtomicBoolean overflow = new AtomicBoolean(); AtomicReference<IOException> drainFailure = new AtomicReference<>();
            Thread drain = new Thread(() -> drain(process.getErrorStream(), diagnostic, overflow, drainFailure), "rrf-offline-decoder-stderr"); drain.setDaemon(true); drain.start();
            var watchdog = Executors.newSingleThreadScheduledExecutor(); AtomicBoolean timedOut = new AtomicBoolean();
            var deadline = watchdog.schedule(() -> { timedOut.set(true); process.destroyForcibly(); }, 120, TimeUnit.SECONDS);
            MessageDigest digest = digest();
            try (LimitedInput bytes = new LimitedInput(new DigestInputStream(process.getInputStream(), digest), 512L * 1024 * 1024)) {
                SaveStream.Projection projection = new SaveStream(new InputStreamReader(bytes, StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)), request).read();
                int code = process.waitFor(); drain.join(10000);
                if (timedOut.get() || drain.isAlive() || drainFailure.get() != null || overflow.get()) throw new IOException("decoder timeout or incomplete stderr");
                String stderr = diagnostic.toString(StandardCharsets.UTF_8);
                if (code != 0) throw new IOException("Rakaly exit " + code + ": " + stderr);
                verifyPin(save, request.save()); verifyPin(decoder, request.decoder());
                BasicFileAttributes after = Files.readAttributes(save, BasicFileAttributes.class);
                if (before.size() != after.size() || !before.lastModifiedTime().equals(after.lastModifiedTime()) || !java.util.Objects.equals(before.fileKey(), after.fileKey())) throw new IOException("save physical identity or timestamp changed during inspection");
                return new Report("rrf-save-inspection-v1", request.machineId(), Instant.now().toString(), request, code, stderr,
                        new StreamEvidence(HexFormat.of().formatHex(digest.digest()), Long.toString(bytes.count()), Long.toString(projection.tokens()), Integer.toString(projection.selectedTokenBytes()), projection.rootKeys(), projection.rootScalars()),
                        projection.inventories(), projection.scopes(), producerPins(Path.of(request.repository())), true, false);
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IOException("offline decoder interrupted", interrupted);
            } finally {
                deadline.cancel(false); watchdog.shutdownNow();
                if (process.isAlive()) { process.destroyForcibly(); try { process.waitFor(10, TimeUnit.SECONDS); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); } }
                try { drain.join(10000); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
            }
        }
    }
    private static List<Pin> producerPins(Path repository) throws IOException {
        Path java = repository.resolve("mod_religious_ritual_fusion/tools/src/main/java/org/xar/ck3/rrf"); List<Pin> pins = new ArrayList<>();
        for (String source : List.of("save/SaveContracts.java", "save/SaveStream.java", "save/SaveInspector.java", "Command.java", "Clausewitz.java", "Contracts.java", "Json.java", "ReleaseBuilder.java")) pins.add(pin(java.resolve(source)));
        return List.copyOf(pins);
    }
    private static void drain(InputStream stream, ByteArrayOutputStream output, AtomicBoolean overflow, AtomicReference<IOException> failure) {
        try (stream) { byte[] buffer = new byte[8192]; int read; while ((read = stream.read(buffer)) != -1) { int remaining = 65536 - output.size(); output.write(buffer, 0, Math.min(remaining, read)); if (read > remaining) overflow.set(true); } }
        catch (IOException error) { failure.set(error); }
    }
    public static Pin pin(Path path) throws IOException { Path real = path.toRealPath(); return new Pin(real.toString(), Files.size(real), hash(real)); }
    private static void verifyPin(Path path, Pin expected) throws IOException {
        if (!Files.isRegularFile(path) || Files.size(path) != expected.bytes() || !hash(path).equals(expected.sha256())) throw new IOException("input pin mismatch: " + path);
    }
    private static String hash(Path path) throws IOException {
        MessageDigest digest = digest(); try (InputStream stream = Files.newInputStream(path)) { byte[] buffer = new byte[65536]; int read; while ((read = stream.read(buffer)) != -1) digest.update(buffer, 0, read); }
        return HexFormat.of().formatHex(digest.digest());
    }
    private static MessageDigest digest() { try { return MessageDigest.getInstance("SHA-256"); } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); } }
    private static final class LimitedInput extends FilterInputStream {
        private final long limit; private long count;
        LimitedInput(InputStream stream, long limit) { super(stream); this.limit = limit; }
        long count() { return count; }
        @Override public int read() throws IOException { int value = in.read(); if (value >= 0) add(1); return value; }
        @Override public int read(byte[] buffer, int offset, int length) throws IOException { int read = in.read(buffer, offset, length); if (read > 0) add(read); return read; }
        private void add(int amount) throws IOException { count += amount; if (count > limit) throw new IOException("melt stream byte cap exceeded"); }
    }
}
