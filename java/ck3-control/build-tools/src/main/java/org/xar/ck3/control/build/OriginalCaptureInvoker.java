package org.xar.ck3.control.build;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Objects;

/** Executes only the explicitly selected original main or exact public source() export inside the owned child. */
public final class OriginalCaptureInvoker {
    private OriginalCaptureInvoker() { }

    static void invoke(Class<?> target, String expectedRoot, CompiledOriginalCaptureProfile.InvocationKind kind,
            String[] originalArguments, Path output) throws Exception {
        Objects.requireNonNull(kind);
        var location = target.getProtectionDomain().getCodeSource();
        if (location == null || !Path.of(location.getLocation().toURI()).toRealPath().equals(Path.of(expectedRoot))) {
            throw new IllegalArgumentException("Loaded original entrypoint CodeSource differs from genuine compiler root");
        }
        try {
            if (kind == CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT) {
                var method = target.getMethod("source");
                if (!Modifier.isPublic(method.getModifiers()) || !Modifier.isStatic(method.getModifiers())
                        || method.getReturnType() != String.class || originalArguments.length != 0) {
                    throw new IllegalArgumentException("Exact public static String source() required; no extraction/fallback");
                }
                Object value = method.invoke(null);
                if (!(value instanceof String source) || source.isEmpty() || source.getBytes(StandardCharsets.UTF_8).length > (2 << 20)) {
                    throw new IllegalArgumentException("Finite unchanged original source text required");
                }
                Files.write(output, source.getBytes(StandardCharsets.UTF_8), StandardOpenOption.CREATE_NEW);
            } else {
                var method = target.getMethod("main", String[].class);
                if (!Modifier.isPublic(method.getModifiers()) || !Modifier.isStatic(method.getModifiers())
                        || method.getReturnType() != void.class) throw new IllegalArgumentException("Exact original public static main(String[]) required");
                method.invoke(null, (Object) originalArguments.clone());
            }
        } catch (InvocationTargetException failure) {
            if (failure.getCause() instanceof Exception error) throw error;
            if (failure.getCause() instanceof Error error) throw error;
            throw failure;
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 6) throw new IllegalArgumentException("request path/bytes/sha and genuine proof path/bytes/sha required");
        var requestRef = new ControlBuild.FileRef(args[0], Long.parseLong(args[1]), args[2]);
        var proofRef = new ControlBuild.FileRef(args[3], Long.parseLong(args[4]), args[5]);
        if (requestRef.bytes() < 1 || requestRef.bytes() > (2 << 20) || proofRef.bytes() < 1 || proofRef.bytes() > (4 << 20)) {
            throw new IllegalArgumentException("Finite original request/proof pins required");
        }
        var request = CompiledOriginalCapture.parseRequest(CompiledGoldenCapture.readPinned(requestRef, 2 << 20));
        var recorded = ControlBuild.strictMapper().readValue(CompiledGoldenCapture.readPinned(proofRef, 4 << 20),
                CompiledOriginalCaptureProfile.Proof.class);
        var actual = CompiledOriginalCaptureProfile.validate(request, CompiledOriginalCaptureProfile.Context.CHILD);
        if (!actual.equals(recorded)) throw new IllegalArgumentException("Child admission differs from actual original compiler proof");
        Class<?> target = Class.forName(request.profile().selection().binaryName(), false, OriginalCaptureInvoker.class.getClassLoader());
        invoke(target, actual.inventory().entrypoint().runtimeOrigin(), request.profile().invocation(),
                request.profile().arguments().stream().map(CompiledOriginalCaptureProfile.Argument::value).toArray(String[]::new),
                Path.of(request.outputPath()));
        requestRef.verify(); proofRef.verify();
        if (!actual.equals(CompiledOriginalCaptureProfile.validate(request, CompiledOriginalCaptureProfile.Context.CHILD))) {
            throw new IllegalArgumentException("Original child sources changed after actual invocation");
        }
    }
}
