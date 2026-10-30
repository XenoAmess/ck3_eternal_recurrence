import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/** Real child0/7/timeout qualification; only the test's own child JVM may be terminated. */
public final class OriginalCommandRecorderTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    private static int checks;
    private OriginalCommandRecorderTest() { }
    private static void yes(boolean value){checks++;if(!value)throw new AssertionError("recorder contract");}
    @FunctionalInterface private interface Checked {void run()throws Exception;}
    private static void reject(Checked call)throws Exception {
        checks++;try{call.run();throw new AssertionError("recorder accepted invalid input");}
        catch(IllegalArgumentException expected){ }
    }
    public static void main(String[] args)throws Exception {
        if(args.length==2&&args[0].equals("--child")){
            System.out.println("original child "+args[1]);System.err.println("original stderr "+args[1]);
            if(args[1].equals("sleep"))Thread.sleep(10000);else System.exit(Integer.parseInt(args[1]));return;
        }
        if(args.length!=3)throw new IllegalArgumentException("actual base own unique-leaf");
        Path base=Path.of(args[0]),own=Path.of(args[1]).resolve(args[2]);Files.createDirectory(own);
        Path runtime=base.resolve("resume-product-a20/runtime-a20/retest-source99-a01"),repo=base.resolve("main12");
        String machine="desktop-3fevhd2-1c74096080",head="0c97cc92a1f502ce7121b45f761914788078b4ff";
        for(String child:List.of("0","7","sleep")){
            String label="RECORDER-"+child;
            var config=new OriginalCommandRecorder.Config(machine,head,repo,runtime,own,label,
                    List.of("java","-XX:-UsePerfData","-cp",System.getProperty("java.class.path"),"OriginalCommandRecorderTest","--child",child),child.equals("sleep")?1:30);
            ObjectNode wire=OriginalCommandRecorder.encode(config);yes(OriginalCommandRecorder.decode(wire).equals(config));
            Path request=own.resolve(label+".request.json");Files.write(request,JSON.writeValueAsBytes(wire));
            int exit=OriginalCommandRecorder.execute(request);
            yes(exit==(child.equals("sleep")?124:Integer.parseInt(child)));
            JsonNode wait=JSON.readTree(Files.readAllBytes(own.resolve(label+".original-wait.actual.json")));
            yes(wait.path("actual_original_popen_wait").booleanValue());
            yes(wait.path("timed_out").booleanValue()==child.equals("sleep"));
            if(!child.equals("sleep"))yes(wait.path("exit_code").intValue()==Integer.parseInt(child));
            yes(wait.path("schema").textValue().equals("xar.resume-original-command-wait.v1"));
            yes(Files.readString(own.resolve(label+".stdout.log")).contains("original child "+child));
            reject(()->OriginalCommandRecorder.execute(request));
            for(String raw:List.of("true","1.0","\"1\"","0","1201")){
                ObjectNode bad=wire.deepCopy();bad.set("timeout_seconds",JSON.readTree(raw));
                reject(()->OriginalCommandRecorder.decode(bad));
            }
        }
        var invalid=new OriginalCommandRecorder.Config(machine,head,repo,runtime,own,"INVALID-DELEGATED",
                List.of("java","-version"),null);
        Path request=own.resolve("INVALID-DELEGATED.request.json");Files.write(request,JSON.writeValueAsBytes(OriginalCommandRecorder.encode(invalid)));
        reject(()->OriginalCommandRecorder.execute(request));yes(!Files.exists(own.resolve("INVALID-DELEGATED.started.json")));
        System.out.println("ORIGINAL_RECORDER_OK checks="+checks+" child0/7/timeout actual waits; repeats and wrong timeouts rejected; no real service terminated; no Game");
    }
}
