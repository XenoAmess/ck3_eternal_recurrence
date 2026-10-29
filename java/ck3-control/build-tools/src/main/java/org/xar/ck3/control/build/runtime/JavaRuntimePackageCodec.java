package org.xar.ck3.control.build.runtime;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Manifest;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;

/** One strict UTF-8/record codec for the package producer and both runtime consumers. */
public final class JavaRuntimePackageCodec {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private JavaRuntimePackageCodec() { }
    public static byte[] encodeRequest(Request value) throws IOException { return encode(value); }
    public static byte[] encodeManifest(Manifest value) throws IOException { return encode(value); }
    public static Request decodeRequest(byte[] raw) throws IOException { return decode(raw, Request.class); }
    public static Manifest decodeManifest(byte[] raw) throws IOException { return decode(raw, Manifest.class); }
    public static Request readRequest(FileRef file) throws IOException { return decodeRequest(read(file)); }
    public static Manifest readManifest(FileRef file) throws IOException { return decodeManifest(read(file)); }
    static byte[] read(FileRef reference) throws IOException {
        if (reference.bytes() < 1 || reference.bytes() > JavaRuntimePackageModel.MAX_METADATA_BYTES) throw new IOException("package metadata byte limit exceeded");
        var before = SharedSourceFiles.observe(Path.of(reference.path()));
        if (!before.source().equals(reference)) throw new IOException("metadata exact source differs");
        byte[] raw = Files.readAllBytes(Path.of(reference.path()));
        if (raw.length != reference.bytes()) throw new IOException("metadata size changed");
        SharedSourceFiles.assertUnchanged(before); return raw;
    }
    static byte[] encode(Object value) throws IOException {
        byte[] raw = JSON.writeValueAsBytes(value);
        if (raw.length == 0 || raw.length > JavaRuntimePackageModel.MAX_METADATA_BYTES) throw new IOException("package metadata byte limit exceeded");
        return raw;
    }
    static <T> T decode(byte[] raw, Class<T> type) throws IOException {
        if (raw == null || raw.length == 0 || raw.length > JavaRuntimePackageModel.MAX_METADATA_BYTES) throw new IOException("bounded package metadata required");
        final String text;
        try { text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString(); }
        catch (CharacterCodingException malformed) { throw new IOException("strict UTF-8 package metadata required", malformed); }
        return JSON.readValue(text, type);
    }
    static String digest(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
