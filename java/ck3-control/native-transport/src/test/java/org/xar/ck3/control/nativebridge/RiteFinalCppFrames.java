package org.xar.ck3.control.nativebridge;
import java.io.IOException;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1;
final class RiteFinalCppFrames {
    private RiteFinalCppFrames(){}
    static byte[] json(String file)throws IOException{try(var in=RiteFinalCppFrames.class.getResourceAsStream("/current267-rite-final-confirm/"+file)){if(in==null)throw new IOException("Pinned genuine final C++ frame missing: "+file);return in.readAllBytes();}}
    static NativeWire.CommandResult response(String file)throws IOException{if(!(NativeWire.decode(NativeWire.packet(json(file))) instanceof NativeWire.CommandResult r))throw new IOException("Actual C++ command_result required");return r;}
    static RawJson result(String file)throws IOException{return new RawJson(response(file).result().token().orElseThrow().value());}
    static RiteDoctrineFrameV1 frame(String file)throws IOException{return RiteDoctrineFrameV1.decode(result(file));}
}
