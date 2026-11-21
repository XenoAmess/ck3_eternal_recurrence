package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.DateAdvanceFrameV1PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pinned actual C++ serializer DATA. Envelope/operation rewrites in replay tests are explicitly Java DATA. */
final class CurrentDateCppFrames {
    private CurrentDateCppFrames(){}
    static byte[] bytes(String name)throws IOException {
        try(var in=CurrentDateCppFrames.class.getResourceAsStream("/current267-date-advance/"+name+".json")) {
            if(in==null)throw new IOException("Actual current date producer resource missing: "+name);
            return in.readAllBytes();
        }
    }
    static NativeWire.CommandResult response(String name)throws IOException {
        if(!(NativeWire.decode(NativeWire.packet(bytes(name))) instanceof NativeWire.CommandResult result))throw new IOException("Original C++ result required");
        return result;
    }
    static CoreFrame.Partial core()throws IOException {
        return DateAdvanceFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(bytes("request-advance-v1"))).expectedCore();
    }
    static String text(String name)throws IOException{return new String(bytes(name),StandardCharsets.UTF_8);}
    static RawJson result(String name)throws IOException{return new RawJson(response(name).result().token().orElseThrow().value());}
}
