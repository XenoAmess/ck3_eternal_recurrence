package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pinned real C++ serializer DATA. The Java index carries provenance, never result generation. */
final class LiteralNavigationCppFrames {
    private static byte[] read(String name)throws IOException {
        try(var in=LiteralNavigationCppFrames.class.getResourceAsStream("/current267-faith-editor/"+name)){
            if(in==null)throw new IOException("Actual C++ navigation fixture missing");return in.readNBytes(65537);
        }
    }
    static byte[] json(String file)throws Exception {
        var index=NativeWire.object(NativeWire.parse(read("java-fixture-index.json")));
        var row=NativeWire.object(NativeWire.object(index.get("files")).get(file));byte[] data=read(file);
        if(data.length!=NativeWire.integer(row.get("bytes"),BigInteger.ONE,BigInteger.valueOf(65536)).intValueExact()
                ||!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data)).equals(NativeWire.text(row.get("sha256"))))throw new IOException("Actual C++ navigation fixture pin differs");return data;
    }
    static NativeWire.CommandResult response(String file)throws Exception {
        var frame=NativeWire.decode(NativeWire.packet(json(file)));
        if(!(frame instanceof NativeWire.CommandResult result))throw new IOException("Actual C++ response required");return result;
    }
    static RawJson result(String file)throws Exception{return new RawJson(response(file).result().token().orElseThrow().value());}
    static CoreFrame.Partial core(String file)throws Exception {
        var node=NativeWire.object(NativeWire.parse(result(file).bytes())).get("core_frame");
        var actual=CoreFrame.decode(new RawJson(StrictJson.canonical(node)));
        if(!(actual instanceof CoreFrame.Partial partial))throw new IOException("Actual fixture nested partial Core required");return partial;
    }
}
