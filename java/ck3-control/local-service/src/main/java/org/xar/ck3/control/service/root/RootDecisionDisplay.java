package org.xar.ck3.control.service.root;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.EventQueue;
import java.awt.Font;
import java.awt.GraphicsEnvironment;
import java.awt.Rectangle;
import java.awt.Toolkit;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicReference;
import javax.swing.BorderFactory;
import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.WindowConstants;
import org.xar.ck3.control.application.presentation.DecisionDisplay;
import org.xar.ck3.control.application.presentation.DecisionDisplayText;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/**
 * Passive, in-process audience window for the actual Root. No Game/desktop input,
 * native bridge, file writer, new process or former overlay renderer is involved.
 */
public final class RootDecisionDisplay implements AutoCloseable {
    private static final long UPDATE_TIMEOUT_MILLIS = 2000;
    public record UiStatus(long publication, Optional<String> configuredHeadless, Optional<Boolean> headless,
            boolean showing, boolean focusable, boolean autoRequestFocus, boolean alwaysOnTop,
            boolean componentTextUpdated, boolean screenDrawVerified, Optional<String> unavailable) {
        public UiStatus {
            StrictJson.safe(publication, 0); Objects.requireNonNull(configuredHeadless); Objects.requireNonNull(headless); Objects.requireNonNull(unavailable);
            StrictJson.require(!screenDrawVerified, "a Java widget update cannot prove OS composition or recorded draw");
        }
    }
    private final DecisionDisplay feed;
    private final AtomicReference<UiStatus> status = new AtomicReference<>(new UiStatus(0,
            Optional.ofNullable(System.getProperty("java.awt.headless")), Optional.empty(), false, false, false, false, false, false, Optional.empty()));
    private volatile boolean closed;
    private volatile IOException renderUnavailable;
    private volatile JFrame window; // Mutation is confined to the EDT; close may inspect the reference.
    private Content content; // Accessed only by the EDT.
    private long renderedPublication;
    private String lastReportedFailure;

    public RootDecisionDisplay(Clock clock) {
        feed = new DecisionDisplay(Objects.requireNonNull(clock), this::render, failure -> {
            UiStatus prior = status.get();
            status.set(new UiStatus(failure.publication(), prior.configuredHeadless(), prior.headless(), prior.showing(),
                    prior.focusable(), prior.autoRequestFocus(), prior.alwaysOnTop(), false, false, Optional.of(failure.reason())));
            // Bounded, separate diagnostic; stdout remains the existing strict Root protocol.
            if (!failure.reason().equals(lastReportedFailure)) {
                lastReportedFailure = failure.reason();
                System.err.println("JAVA_DECISION_DISPLAY_UNAVAILABLE: " + failure.reason());
            }
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

    private void render(DecisionDisplay.Snapshot actual) throws IOException {
        if (closed) throw new IOException("actual Root decision viewer has closed");
        if (renderUnavailable != null) throw renderUnavailable;
        final boolean headless;
        try { headless = GraphicsEnvironment.isHeadless(); }
        catch (java.awt.AWTError unavailable) {
            renderUnavailable = new IOException("actual JVM graphics environment unavailable", unavailable);
            throw renderUnavailable;
        }
        Optional<String> property = Optional.ofNullable(System.getProperty("java.awt.headless"));
        if (headless) {
            status.set(new UiStatus(actual.publication(), property, Optional.of(true), false, false, false, false, false, false,
                    Optional.of("actual JVM graphics environment is headless")));
            renderUnavailable = new IOException("actual JVM graphics environment is headless; decision window unavailable");
            throw renderUnavailable;
        }
        String text = DecisionDisplayText.render(actual);
        try { onEdt(() -> {
            if (closed) throw new IOException("actual Root decision viewer has closed");
            if (renderUnavailable != null) throw renderUnavailable;
            if (actual.publication() < renderedPublication) throw new IOException("stale audience update cannot replace a later actual observation");
            if (window == null) createWindow();
            if (!window.isDisplayable()) throw new IOException("decision viewer was closed; it is not automatically reopened");
            content.showText(text);
            if (!window.isShowing()) throw new IOException("decision viewer is not showing");
            content.text.paintImmediately(content.text.getVisibleRect());
            Toolkit.getDefaultToolkit().sync();
            renderedPublication = actual.publication();
            status.set(new UiStatus(actual.publication(), property, Optional.of(false), window.isShowing(), window.getFocusableWindowState(),
                    window.isAutoRequestFocus(), window.isAlwaysOnTop(), content.text.getText().equals(text), false, Optional.empty()));
        }); } catch (IOException failure) {
            renderUnavailable = failure; // Do not repeatedly stall native execution on the same unavailable EDT.
            throw failure;
        }
    }
    private void createWindow() throws IOException {
        if (!EventQueue.isDispatchThread()) throw new IOException("decision window must be constructed on the existing JVM EDT");
        JFrame actual = new JFrame(DecisionDisplayText.TITLE);
        window = actual;
        try {
        actual.setAutoRequestFocus(false);
        actual.setFocusableWindowState(false);
        actual.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        actual.setLayout(new BorderLayout());
        content = new Content();
        actual.add(content, BorderLayout.CENTER);
        // A normal decorated, opaque text viewer. It shares no old overlay code, window class or style.
        actual.setAlwaysOnTop(true);
        var devices = GraphicsEnvironment.getLocalGraphicsEnvironment().getScreenDevices();
        var selected = devices[devices.length - 1].getDefaultConfiguration();
        Rectangle bounds = selected.getBounds();
        var insets = Toolkit.getDefaultToolkit().getScreenInsets(selected);
        int availableWidth = Math.max(240, bounds.width - insets.left - insets.right);
        int availableHeight = Math.max(240, bounds.height - insets.top - insets.bottom);
        int width = Math.min(460, availableWidth);
        int height = Math.min(700, availableHeight);
        actual.setBounds(bounds.x + bounds.width - insets.right - width, bounds.y + insets.top, width, height);
        actual.setVisible(true); // No requestFocus, toFront, Game HWND access, or activation operation.
        if (actual.getFocusableWindowState() || actual.isAutoRequestFocus())
            throw new IOException("passive decision window focus policy was not retained");
        } catch (IOException | RuntimeException | java.awt.AWTError failure) {
            actual.dispose();
            throw failure;
        }
    }
    /** Lightweight production component also exercised in headless tests; it makes no screen-draw claim. */
    static final class Content extends JScrollPane {
        private static final long serialVersionUID = 1L;
        final JTextArea text = new JTextArea();
        Content() {
            text.setEditable(false);
            text.setFocusable(false);
            text.setLineWrap(true);
            text.setWrapStyleWord(true);
            text.setFont(new Font(Font.DIALOG, Font.PLAIN, 20));
            text.setBackground(new Color(250, 249, 245));
            text.setForeground(new Color(28, 30, 32));
            text.setBorder(BorderFactory.createEmptyBorder(14, 14, 14, 14));
            setViewportView(text);
            setBorder(BorderFactory.createEmptyBorder());
        }
        void showText(String actual) {
            if (!EventQueue.isDispatchThread()) throw new IllegalStateException("actual decision component requires the EDT");
            text.setText(Objects.requireNonNull(actual));
            text.setCaretPosition(0);
            if (!text.getText().equals(actual)) throw new IllegalStateException("actual decision component text differs");
        }
    }
    @FunctionalInterface private interface UiWork { void run() throws IOException; }
    private static void onEdt(UiWork work) throws IOException {
        if (EventQueue.isDispatchThread()) { work.run(); return; }
        var completed = new CompletableFuture<Void>();
        EventQueue.invokeLater(() -> {
            try { work.run(); completed.complete(null); }
            catch (IOException | RuntimeException | java.awt.AWTError failure) { completed.completeExceptionally(failure); }
        });
        try { completed.get(UPDATE_TIMEOUT_MILLIS, TimeUnit.MILLISECONDS); }
        catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new InterruptedIOException("decision component update interrupted");
        } catch (TimeoutException timeout) {
            throw new IOException("decision component update deadline expired; no screen-draw proof", timeout);
        } catch (ExecutionException failed) {
            if (failed.getCause() instanceof IOException io) throw io;
            throw new IOException("actual decision component update failed", failed.getCause());
        }
    }
    @Override public void close() throws IOException {
        closed = true;
        if (window == null) return;
        onEdt(() -> {
            window.dispose();
            UiStatus prior = status.get();
            status.set(new UiStatus(prior.publication(), prior.configuredHeadless(), prior.headless(), false, false, false,
                    prior.alwaysOnTop(), prior.componentTextUpdated(), false, Optional.of("Root viewer closed")));
        });
    }
}

