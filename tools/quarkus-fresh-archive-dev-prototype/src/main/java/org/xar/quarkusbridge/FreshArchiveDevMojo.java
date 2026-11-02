package org.xar.quarkusbridge;

import io.quarkus.bootstrap.app.QuarkusBootstrap;
import io.quarkus.deployment.dev.DevModeCommandLineBuilder;
import io.quarkus.maven.DevMojo;
import io.quarkus.maven.dependency.ArtifactKey;
import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.Path;

/** Descriptor-injected application-owned subclass; the vendor plugin JAR is never rewritten. */
public final class FreshArchiveDevMojo extends DevMojo {
    // The owned plugin descriptor, not annotations on the vendor superclass, binds this field.
    private String freshArchiveOutput;

    @Override
    protected void modifyDevModeContext(DevModeCommandLineBuilder builder) {
        super.modifyDevModeContext(builder);
        final Path output;
        final Path ownJar;
        try {
            if (freshArchiveOutput == null || freshArchiveOutput.isBlank())
                throw new IllegalArgumentException("xar.dev.fresh.output is required");
            Path requested = Path.of(freshArchiveOutput);
            if (!requested.isAbsolute()) throw new IllegalArgumentException("fresh output must be absolute");
            output = requested.toRealPath();
            if (!Files.isDirectory(output)) throw new IllegalArgumentException("fresh output must be an existing directory");
            ownJar = Path.of(FreshArchiveDevMojo.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
            if (!Files.isRegularFile(ownJar) && !Files.isDirectory(ownJar))
                throw new IllegalArgumentException("entry must be an existing plugin JAR or reactor classes directory");
        } catch (IOException | URISyntaxException failure) {
            throw new IllegalArgumentException("fresh dev paths could not be resolved", failure);
        }
        builder.classpathEntry(ArtifactKey.of("org.xar.research", "fresh-dev-entry", "", "jar"), ownJar.toFile());
        builder.entryPointCustomizer(context -> {
            if (context.isTest() || context.getMode() != QuarkusBootstrap.Mode.DEV
                    || context.getAlternateEntryPoint() != null)
                throw new IllegalStateException("fresh dev entry requires plain local dev without another alternate entry");
            context.getBuildSystemProperties().put(FreshArchiveDevEntry.OUTPUT, output.toString());
            context.getBuildSystemProperties().put(FreshArchiveDevEntry.ENTRY_PATH, ownJar.toString());
            context.setAlternateEntryPoint(FreshArchiveDevEntry.class.getName());
        });
    }
}
