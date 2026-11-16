package org.xar.ck3.control.service.root;

import com.sun.tools.attach.VirtualMachine;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;

/** One explicit standard-JDK Attach operation; this command has no Game or business-worker path. */
public final class RootAwaitingOwnerStorageHandoffCommand {
    private RootAwaitingOwnerStorageHandoffCommand() { }
    public static void main(String[] args)throws Exception {
        if(args.length==6&&args[0].equals("rehearsal-grant")) {
            RootAwaitingOwnerStorageHandoffAgent.writeRehearsalGrant(Path.of(args[1]),Path.of(args[2]),Path.of(args[3]),Path.of(args[4]),Path.of(args[5]));
            return;
        }
        if(args.length!=7)throw new IOException("pid agent.jar jarBytes jarSHA grantFile grantBytes grantSHA required");
        if(!args[0].matches("[1-9][0-9]{0,9}")||args[0].equals(Long.toString(ProcessHandle.current().pid())))
            throw new IOException("distinct explicit target JVM required");
        Path jar=exact(args[1],args[2],args[3],2<<20),grant=exact(args[4],args[5],args[6],65536);
        if(jar.toString().contains("|")||grant.toString().contains("|"))throw new IOException("literal source paths required");
        VirtualMachine target=VirtualMachine.attach(args[0]);
        try {
            target.loadAgent(jar.toString(),grant+"|"+args[5]+"|"+args[6]);
        }finally{target.detach();}
    }
    private static Path exact(String path,String bytes,String hash,int maximum)throws Exception {
        Path result=Path.of(path);
        if(!result.isAbsolute()||!result.normalize().equals(result)||Files.isSymbolicLink(result)
                ||!Files.isRegularFile(result,LinkOption.NOFOLLOW_LINKS)||!bytes.matches("[1-9][0-9]{0,7}")
                ||!hash.matches("[0-9a-f]{64}"))throw new IOException("bounded exact plain source required");
        byte[] raw;try(InputStream input=Files.newInputStream(result)){raw=input.readNBytes(maximum+1);}
        if(raw.length>maximum||raw.length!=Integer.parseInt(bytes)
                ||!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(hash))
            throw new IOException("exact administrative source differs");
        return result;
    }
}
