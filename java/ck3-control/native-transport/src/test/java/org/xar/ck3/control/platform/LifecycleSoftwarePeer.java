package org.xar.ck3.control.platform;

import com.sun.jna.platform.win32.Kernel32;

/** Fixed ordinary software process; never emits Native frames or creates a CK3 surrogate. */
public final class LifecycleSoftwarePeer {
    private LifecycleSoftwarePeer(){ }
    public static void main(String[] args)throws InterruptedException{
        if(args.length==0)throw new IllegalArgumentException("fixed software mode required");
        if(args[0].equals("environment")){
            if(args.length!=3)throw new IllegalArgumentException("fixed environment inputs required");
            for(String key:java.util.List.of("SystemRoot","WINDIR","Path","USERPROFILE","APPDATA","LOCALAPPDATA"))
                requireEnvironment(System.getenv(key)!=null&&!System.getenv(key).isBlank(),key);
            requireEnvironment(args[1].equals(System.getenv("TEMP")),"TEMP");
            requireEnvironment(args[1].equals(System.getenv("TMP")),"TMP");
            requireEnvironment("native-headless".equals(System.getenv("XAR_CK3_BRIDGE_MODE")),"XAR_CK3_BRIDGE_MODE");
            requireEnvironment(args[2].equals(System.getenv("XAR_CK3_BRIDGE_PIPE")),"XAR_CK3_BRIDGE_PIPE");
            System.out.println("ENVIRONMENT_OK");return;
        }
        if(args.length!=1)throw new IllegalArgumentException("fixed software mode required");
        switch(args[0]){
            case "exit259" -> Kernel32.INSTANCE.ExitProcess(259);
            case "exit0" -> { }
            case "wait" -> Thread.sleep(10000);
            case "job-memory-overflow" -> {
                try(var unexpected=new com.sun.jna.Memory(128L<<20)){
                    throw new IllegalStateException("native allocation unexpectedly exceeded the actual Job limit: " + unexpected.size());
                }catch(OutOfMemoryError actual){
                    System.out.println("JOB_MEMORY_ALLOCATION_REJECTED");System.out.flush();
                    Thread.sleep(10000);
                }
            }
            default -> throw new IllegalArgumentException("unknown software mode");
        }
    }
    private static void requireEnvironment(boolean valid,String key){
        if(!valid)throw new IllegalStateException("environment mismatch: "+key);
    }
}
