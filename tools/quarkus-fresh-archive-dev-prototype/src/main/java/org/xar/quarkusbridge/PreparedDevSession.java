package org.xar.quarkusbridge;

import io.quarkus.bootstrap.app.CuratedApplication;
import io.quarkus.deployment.dev.IsolatedDevModeMain;
import java.io.Closeable;
import java.util.Map;
import java.util.function.BiConsumer;

/** A preparation barrier: accept stores inputs; run alone starts the original dev lifecycle. */
public final class PreparedDevSession implements BiConsumer<CuratedApplication, Map<String, Object>>, Runnable, Closeable {
    private CuratedApplication application;
    private Map<String, Object> params;
    private IsolatedDevModeMain delegate;
    private boolean started;
    private boolean startFailed;
    private boolean closed;

    @Override
    public void accept(CuratedApplication replacement, Map<String, Object> actualParams) {
        if (application != null || closed) throw new IllegalStateException("session can be prepared only once");
        application = replacement;
        params = actualParams;
        delegate = new IsolatedDevModeMain();
    }

    @Override
    public void run() {
        if (application == null || started || closed) throw new IllegalStateException("session must be prepared and unstarted");
        started = true;
        ClassLoader old = Thread.currentThread().getContextClassLoader();
        try {
            // Ensure TCCL matches the loader that defined the delegate and its service interfaces
            Thread.currentThread().setContextClassLoader(application.getOrCreateAugmentClassLoader());
            delegate.accept(application, params);
        } catch (RuntimeException | Error failure) {
            startFailed = true;
            // Preserve the vendor startup failure. Its Exception cleanup is in accept(); no forced second close.
            throw failure;
        } finally {
            Thread.currentThread().setContextClassLoader(old);
        }
    }

    @Override
    public void close() {
        if (closed) return;
        closed = true;
        if (!started) application.close();
        else if (!startFailed) delegate.close();
        // A startup Error before vendor cleanup remains UNKNOWN; this prototype is not production-adopted.
    }
}
