package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact real C++ serializer originals. The index is a source pin projection, not another producer. */
final class CurrentDjcQueryCppFrames {
    private static byte[] read(String file)throws IOException {
        try(var in=CurrentDjcQueryCppFrames.class.getResourceAsStream("/current267-djc-query/"+file)) {
            if(in==null)throw new IOException("Actual C++ fixture missing: "+file);
            byte[] raw=in.readNBytes(65537);if(raw.length==0||raw.length>65536)throw new IOException("Bounded actual C++ fixture required");return raw;
        }
    }
    static byte[] envelope(String logical)throws Exception {
        var index=NativeWire.object(NativeWire.parse(read("java-fixture-index.json")));
        var entry=NativeWire.object(NativeWire.object(index.get("files")).get(logical));
        byte[] raw=read(NativeWire.text(entry.get("file")));
        if(raw.length!=NativeWire.integer(entry.get("bytes"),BigInteger.ONE,BigInteger.valueOf(65536)).intValueExact()
                ||!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(NativeWire.text(entry.get("sha256"))))
            throw new IOException("Actual C++ fixture pin differs");
        return raw;
    }
    static NativeWire.CommandResult response(String logical)throws Exception {
        var frame=NativeWire.decode(NativeWire.packet(envelope(logical)));
        if(!(frame instanceof NativeWire.CommandResult result))throw new IOException("Actual C++ command result required");return result;
    }
    static byte[] result(String logical)throws Exception{return response(logical).result().token().orElseThrow().value();}
    static CoreFrame.Partial core()throws Exception {
        var request=NativeWire.decodeExecuteRequest(NativeWire.packet(envelope("request")));
        var c=NativeWire.object(NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).get("djc_war_query"));
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,new CoreFrame.Prefix(i(c.get("date_raw")),i(c.get("speed")),c.get("paused").booleanValue(),
                i(c.get("local_player_id")),c.get("map_ready").booleanValue(),c.get("has_played_character").booleanValue(),i(c.get("played_character_id")),c.get("played_character_alive").booleanValue()));
    }
    private static int i(com.fasterxml.jackson.databind.JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
}
