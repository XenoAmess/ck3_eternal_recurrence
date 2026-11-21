package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1PublicCodec;

/** Reads pinned actual C++ serializer outputs. Replay envelopes and fault mutations remain labelled Java DATA. */
final class FrontendMenuCppFrames {
    private FrontendMenuCppFrames() { }
    record Entry(String name,String kind,byte[] json) { }
    static byte[] resource(String name)throws IOException {
        if(!name.matches("[A-Za-z0-9_.-]+\\.json"))throw new IOException("bounded direct fixture filename required");
        try(var in=FrontendMenuCppFrames.class.getResourceAsStream("/current267-frontend-menu/"+name)){
            if(in==null)throw new IOException("Pinned genuine frontend C++ frame missing: "+name);return in.readAllBytes();
        }
    }
    static List<Entry> entries()throws Exception {
        var index=StrictJson.object(StrictJson.parse(resource("actual-cpp-pins.json")),Set.of("schema","files"),Set.of());
        if(!StrictJson.text(index.get("schema")).equals("actual-cpp-current-menu-pins/v1")||!index.get("files").isArray())throw new IOException("actual producer fixture index required");
        var result=new ArrayList<Entry>();
        for(var value:index.get("files")) {
            var row=StrictJson.object(value,Set.of("name","kind","sha256"),Set.of());String name=StrictJson.text(row.get("name"));byte[] original=resource(name);
            if(!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)).equals(StrictJson.text(row.get("sha256"))))throw new IOException("Actual C++ original fixture SHA drift: "+name);
            String kind=StrictJson.text(row.get("kind"));if(!kind.equals("request")&&!kind.equals("result"))throw new IOException("actual wire fixture kind required");
            result.add(new Entry(name,kind,original));
        }
        if(result.isEmpty())throw new IOException("genuine C++ producer outputs required, never a skipped software lane");return List.copyOf(result);
    }
    static NativeWire.CommandResult response(FrontendMenuFrameV1.Action action,FrontendMenuFrameV1.Status status)throws Exception {
        for(var entry:entries())if(entry.kind().equals("result")){
            if(!(NativeWire.decode(NativeWire.packet(entry.json())) instanceof NativeWire.CommandResult r))throw new IOException("actual C++ command_result required");
            var frame=FrontendMenuFrameV1PublicCodec.decodePacket(new RawJson(r.payload().value()),r.requestId());if(frame.action()==action&&frame.status()==status)return r;
        }
        throw new IOException("Actual C++ menu result absent: "+action+"/"+status);
    }
    static byte[] request(FrontendMenuFrameV1.Action action)throws Exception {
        for(var entry:entries())if(entry.kind().equals("request")&&FrontendMenuFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(entry.json())).action()==action)return NativeWire.packet(entry.json());
        throw new IOException("Actual C++ menu request absent: "+action);
    }
    static RawJson result(FrontendMenuFrameV1.Action action,FrontendMenuFrameV1.Status status)throws Exception {return new RawJson(response(action,status).result().token().orElseThrow().value());}
    static FrontendMenuFrameV1 available()throws Exception{return FrontendMenuFrameV1.decode(result(FrontendMenuFrameV1.Action.QUERY_MENU,FrontendMenuFrameV1.Status.AVAILABLE));}
}
