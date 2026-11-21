package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;

/** Exact genuine C++ DATA originals. Index is a source pin projection, not a second producer. */
final class CurrentSuccessionCppFrames {
    private static byte[] read(String file)throws IOException {
        try(var in=CurrentSuccessionCppFrames.class.getResourceAsStream("/current267-succession/"+file)) {
            if(in==null)throw new IOException("Genuine C++ succession fixture absent");var b=in.readNBytes(65537);if(b.length==0||b.length>65536)throw new IOException("Bounded actual fixture required");return b;
        }
    }
    static byte[] envelope(String name)throws Exception {
        var index=NativeWire.object(NativeWire.parse(read("java-fixture-index.json")));var row=NativeWire.object(NativeWire.object(index.get("files")).get(name));var b=read(NativeWire.text(row.get("file")));
        if(b.length!=NativeWire.integer(row.get("bytes"),BigInteger.ONE,BigInteger.valueOf(65536)).intValueExact()||!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)).equals(NativeWire.text(row.get("sha256"))))throw new IOException("Actual C++ fixture pin differs");return b;
    }
    static NativeWire.CommandResult response(String name)throws Exception {
        var r=NativeWire.decode(NativeWire.packet(envelope(name)));if(!(r instanceof NativeWire.CommandResult result))throw new IOException("Actual command result required");return result;
    }
    static byte[] result(String name)throws Exception{return response(name).result().token().orElseThrow().value();}
    static CurrentSuccessionLifecycleResult frame(String name)throws Exception{return CurrentSuccessionLifecycleResult.decode(new org.xar.ck3.control.application.action.RawJson(result(name)));}
}
