package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import java.util.HexFormat;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.presentation.DecisionDisplay;
import org.xar.ck3.control.application.presentation.DecisionDisplayText;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/**
 * Headless file-publisher for the actual Root decision display.
 * No AWT/Swing/EDT, no desktop window, no UI. Writes text and binding JSON to stateRoot.
 */
public final class RootDecisionDisplay implements AutoCloseable {
    private static final String TEXT_FILE = "decision-display/current.txt";
    private static final String BINDING_FILE = "decision-display/current.binding.json";
    private static final int MAX_TEXT_BYTES = 32 * 1024;
    private static final int MAX_MANIFEST_BYTES = 16 * 1024;

    public record UiStatus(long publication, Optional<String> configuredHeadless, Optional<Boolean> headless,
            boolean showing, boolean focusable, boolean autoRequestFocus, boolean alwaysOnTop,
            boolean componentTextUpdated, boolean screenDrawVerified, Optional<String> unavailable) {
        public UiStatus {
            StrictJson.safe(publication, 0);
            Objects.requireNonNull(configuredHeadless);
            Objects.requireNonNull(headless);
            Objects.requireNonNull(unavailable);
            StrictJson.require(!screenDrawVerified, "a Java widget update cannot prove OS composition or recorded draw");
        }
    }

    private final Clock clock;
    private final Path stateRoot;
    private final DecisionDisplay feed;
    private final AtomicReference<UiStatus> status;
    private volatile boolean closed;
    private long lastPublishedPublication;

    public RootDecisionDisplay(Clock clock, Path stateRoot) {
        this.clock = Objects.requireNonNull(clock);
        this.stateRoot = Objects.requireNonNull(stateRoot);
        if (!this.stateRoot.isAbsolute() || !this.stateRoot.equals(this.stateRoot.normalize())) {
            throw new IllegalArgumentException("stateRoot must be absolute and normalized");
        }
        this.lastPublishedPublication = 0;
        this.closed = false;
        this.status = new AtomicReference<>(new UiStatus(0,
                Optional.ofNullable(System.getProperty("java.awt.headless")),
                Optional.empty(), false, false, false, false, false, false, Optional.empty()));
        this.feed = new DecisionDisplay(this.clock, this::render, failure -> {
            UiStatus prior = this.status.get();
            this.status.set(new UiStatus(failure.publication(), prior.configuredHeadless(), prior.headless(), prior.showing(),
                    prior.focusable(), prior.autoRequestFocus(), prior.alwaysOnTop(), false, false, Optional.of(failure.reason())));
        });
    }

    public DecisionDisplay feed() { return feed; }
    public UiStatus status() { return status.get(); }

    /** Actual selected source graph must cover the new renderer and the complete typed producer/consumer. */
    public static void requireSources(NativeLaunchPlan plan) throws IOException {
        for (Class<?> unit : List.of(RootDecisionDisplay.class, DecisionDisplay.class, DecisionDisplayText.class))
            requireSource(plan, unit);
    }
    private static void requireSource(NativeLaunchPlan plan, Class<?> unit) throws IOException {
        plan.sources().requireLoadedClass(unit);
        for (Class<?> nested : unit.getDeclaredClasses()) requireSource(plan, nested);
    }

    private synchronized void render(DecisionDisplay.Snapshot actual) throws IOException {
        if (closed) throw new IOException("actual Root decision viewer has closed");
        if (actual.publication() <= lastPublishedPublication) {
            // Stale or duplicate snapshot; do not overwrite newer text.
            return;
        }
        if (actual.current().isEmpty()) {
            // No card to publish yet; do not advance successful publication counter.
            return;
        }

        DecisionDisplay.Card current = actual.current().orElseThrow();

        // 1. Render Text
        String text = DecisionDisplayText.render(actual);
        byte[] textBytes = text.getBytes(StandardCharsets.UTF_8);
        if (textBytes.length > MAX_TEXT_BYTES) throw new IOException("decision text exceeds 32KiB");

        // 2. Build Manifest
        ObjectNode manifest = StrictJson.object();
        manifest.put("schema", "xar.java-root-decision-text/v1");
        manifest.put("status", "TEXT_PUBLISHED");
        manifest.put("publication", actual.publication());
        manifest.put("written_at_utc", clock.instant().toString());
        manifest.put("machine_id", current.context().origin().machineId());
        manifest.put("session_id", current.context().sessionId());
        manifest.set("game", current.context().origin().game().toJson());

        // Publisher Info
        var process = ProcessHandle.current();
        var info = process.info();
        if (info.command().isEmpty() || info.startInstant().isEmpty()) {
             throw new IOException("actual process identity unavailable");
        }
        ObjectNode publisher = manifest.putObject("publisher");
        publisher.put("pid", process.pid());
        publisher.put("start_instant_utc", info.startInstant().get().toString());
        publisher.put("executable", info.command().get());

        // File Paths and Hashes
        Path textPath = stateRoot.resolve(TEXT_FILE);
        Path bindingPath = stateRoot.resolve(BINDING_FILE);

        manifest.put("decision_text_file", textPath.toString());
        manifest.put("text_bytes", textBytes.length);
        manifest.put("text_sha256", sha256Hex(textBytes));

        manifest.put("creates_desktop_window", false);
        manifest.put("OBS_draw_ack", false);
        manifest.put("screen_draw_verified", false);

        byte[] manifestBytes = StrictJson.canonical(manifest, MAX_MANIFEST_BYTES);
        if (manifestBytes.length > MAX_MANIFEST_BYTES) throw new IOException("decision manifest exceeds 16KiB");

        // 3. Atomic Write
        writeAtomic(textPath, textBytes);
        writeAtomic(bindingPath, manifestBytes);

        lastPublishedPublication = actual.publication();
        UiStatus prior = status.get();
        status.set(new UiStatus(actual.publication(), prior.configuredHeadless(), prior.headless(), false, false, false, false, false, false, Optional.empty()));
    }

    private void writeAtomic(Path target, byte[] content) throws IOException {
        Path parent = target.getParent();
        if (!Files.exists(parent)) Files.createDirectories(parent);

        Path temp = Files.createTempFile(parent, "decision-display-", ".tmp");
        try {
            Files.write(temp, content);
            Files.move(temp, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            try { Files.deleteIfExists(temp); } catch (Exception ignored) {}
            throw e;
        }
    }

    private static String sha256Hex(byte[] data) throws IOException {
        try {
            var digest = MessageDigest.getInstance("SHA-256");
            digest.update(data);
            return HexFormat.of().formatHex(digest.digest());
        } catch (NoSuchAlgorithmException e) {
            throw new IOException("SHA-256 algorithm unavailable", e);
        }
    }

    @Override public synchronized void close() throws IOException {
        closed = true;
        UiStatus prior = status.get();
        status.set(new UiStatus(prior.publication(), prior.configuredHeadless(), prior.headless(), false, false, false, false, false, false, Optional.of("Root viewer closed")));
    }
}