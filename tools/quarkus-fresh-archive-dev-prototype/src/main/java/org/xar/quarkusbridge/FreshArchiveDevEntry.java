package org.xar.quarkusbridge;

import io.quarkus.bootstrap.app.AdditionalDependency;
import io.quarkus.bootstrap.app.CuratedApplication;
import io.quarkus.bootstrap.app.QuarkusBootstrap;
import io.quarkus.deployment.dev.DevModeContext;
import java.io.Closeable;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.function.BiConsumer;

/** Runs after the original model bootstrap, before the actual application's augmentation/start. */
public final class FreshArchiveDevEntry implements BiConsumer<CuratedApplication, Map<String, Object>>, Closeable {
    static final String OUTPUT = "xar.dev.fresh.output";
    static final String ENTRY_PATH = "xar.dev.fresh.entry.path";
    private Closeable session;
    private boolean accepted;
    private boolean closed;

    @Override
    public void accept(CuratedApplication original, Map<String, Object> params) {
        if (accepted || closed) throw new IllegalStateException("fresh entry can be accepted only once");
        accepted = true;
        CuratedApplication unstarted = null;
        try {
            if (!(params.get(DevModeContext.class.getName()) instanceof DevModeContext context)
                    || context.isTest() || context.getMode() != QuarkusBootstrap.Mode.DEV)
                throw new IllegalArgumentException("actual local DevModeContext is required");
            Path output = actualPath(context, OUTPUT, true);
            Path ownJar = actualPath(context, ENTRY_PATH, false);
            QuarkusBootstrap.Builder builder = original.getQuarkusBootstrap().clonedBuilder()
                    .setExistingModel(original.getApplicationModel())
                    .setDependencyInfoProvider(original.getQuarkusBootstrap().getDependencyInfoProvider())
                    .addAdditionalApplicationArchive(new AdditionalDependency(output, true, true))
                    .addAdditionalDeploymentArchive(ownJar);
            unstarted = builder.build().bootstrap();
            Object prepared = unstarted.runInAugmentClassLoader(PreparedDevSession.class.getName(), params);
            if (!(prepared instanceof Runnable starter) || !(prepared instanceof Closeable closeable)
                    || prepared.getClass().getClassLoader() != unstarted.getOrCreateAugmentClassLoader())
                throw new IllegalStateException("prepared session must be defined in the replacement augmentation loader");
            // Preparation performs no application startup. Custody is acquired before calling run().
            session = closeable;
            unstarted = null;
            starter.run();
        } catch (Throwable failure) {
            // Before session custody, the owned replacement has not started an application.
            if (unstarted != null) {
                try { unstarted.close(); }
                catch (Throwable cleanup) { failure.addSuppressed(cleanup); }
            }
            if (failure instanceof Error error) throw error;
            if (failure instanceof RuntimeException runtime) throw runtime;
            throw new IllegalStateException("fresh entry initialization failed", failure);
        }
    }

    private static Path actualPath(DevModeContext context, String name, boolean directory) throws IOException {
        String value = context.getBuildSystemProperties().get(name);
        if (value == null) throw new IllegalArgumentException("missing owned entry path: " + name);
        Path requested = Path.of(value);
        if (!requested.isAbsolute()) throw new IllegalArgumentException("entry path must be absolute: " + name);
        Path actual = requested.toRealPath();
        if (directory ? !Files.isDirectory(actual) : (!Files.isRegularFile(actual) && !Files.isDirectory(actual)))
            throw new IllegalArgumentException("entry path has wrong kind: " + name);
        return actual;
    }

    @Override
    public void close() throws IOException {
        if (closed) return;
        closed = true;
        if (session != null) session.close();
        // DevModeMain owns and closes original; IsolatedDevModeMain owns the replacement.
    }
}
