package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact real C++ serializer originals. Index is a source-pin projection, never a Native result producer. */
final class CurrentCheckpointCppFrames {
    private static byte[] read(String file)throws IOException {
        String root=System.getProperty("xar.current267.checkpoint.goldenRoot");
        if(root!=null){Path p=Path.of(root);if(!p.isAbsolute())throw new IOException("Absolute actual C++ fixture root required");return Files.readAllBytes(p.resolve(file));}
        try(var in=CurrentCheckpointCppFrames.class.getResourceAsStream("/current267-core-checkpoint/"+file)){
            if(in==null)throw new IOException("Actual C++ fixture missing: "+file);return in.readNBytes(65537);
        }
    }
    static byte[] envelope(String logical)throws Exception {
        var index=NativeWire.object(NativeWire.parse(read("java-fixture-index.json")));
        var entry=NativeWire.object(NativeWire.object(index.get("files")).get(logical));
        byte[] raw=read(NativeWire.text(entry.get("file")));
        if(raw.length!=NativeWire.integer(entry.get("bytes"),BigInteger.ONE,BigInteger.valueOf(65536)).intValueExact()
                ||!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(NativeWire.text(entry.get("sha256"))))throw new IOException("Actual C++ fixture pin differs");
        return raw;
    }
    static NativeWire.CommandResult response(String logical)throws Exception {
        var frame=NativeWire.decode(NativeWire.packet(envelope(logical)));
        if(!(frame instanceof NativeWire.CommandResult result))throw new IOException("Actual C++ command result envelope required");return result;
    }
    static byte[] result(String logical)throws Exception{return response(logical).result().token().orElseThrow().value();}
    static CoreFrame.Partial core(String logical)throws Exception {
        var request=NativeWire.decodeExecuteRequest(NativeWire.packet(envelope(logical)));
        var claim=NativeWire.object(NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).get("core_checkpoint_save"));
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,new CoreFrame.Prefix(i(claim.get("date_raw")),i(claim.get("speed")),claim.get("paused").booleanValue(),
                i(claim.get("local_player_id")),claim.get("map_ready").booleanValue(),claim.get("has_played_character").booleanValue(),i(claim.get("played_character_id")),claim.get("played_character_alive").booleanValue()));
    }
    private static int i(com.fasterxml.jackson.databind.JsonNode node)throws IOException{return NativeWire.integer(node,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
}
