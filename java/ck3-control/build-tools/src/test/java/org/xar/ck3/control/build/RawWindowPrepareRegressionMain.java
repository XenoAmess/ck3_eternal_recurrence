package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;
import static org.xar.ck3.control.build.RawWindowPreparation.*;

/** Finite producer regressions for strict helper qualification; persistent JUnit also invokes this entry. */
public final class RawWindowPrepareRegressionMain {
    private RawWindowPrepareRegressionMain() { }
    public static void main(String[] args)throws Exception {
        if(args.length!=1||!Path.of(args[0]).isAbsolute())throw new IllegalArgumentException("one absolute absent regression output directory required");
        run(Path.of(args[0]));System.out.println("PASS_SOFTWARE_PREPARATION_REGRESSIONS_NO_EXE_NO_NATIVE_IDENTITY_QUALIFICATION");
    }
    static void run(Path root)throws Exception {
        Files.createDirectory(root);String machine="software-machine-0001";
        var identity=new SharedSourceFiles.DirectoryIdentity("18446744073709551615","340282366920938463463374607431768211455","132537600000000001");
        var other=new SharedSourceFiles.DirectoryIdentity("1","2","3");
        var evidence=new ControlBuild.FileRef(root.resolve("retained-proof-not-opened.json").toString(),6746,RawWindowLocatorContract.FULL_HASH_ORIGINAL_SHA256);
        var plan=new WindowPlan(WINDOW_PLAN_SCHEMA,machine,Consumer.M5,"software-window",root.resolve("NOT_OPENED-ck3.exe").toString(),evidence,root.toString(),List.of(new Window("metadata",Kind.METADATA,97853184,8184)),new Amounts(0,8184,0),8192,18432,32768,"2099-01-01T00:00:00Z");
        DirectoryPort stable=new DirectoryPort(){public String machineId(){return machine;}public SharedSourceFiles.DirectoryIdentity directory(Path path){return identity;}};
        Path output=root.resolve("request.json");var prepared=prepare(plan,output,stable);
        check(prepared.request().equals(RawWindowCaptureJson.decodeRequest(Files.readAllBytes(output))),"real producer/strict consumer roundtrip");
        check(!Files.exists(Path.of(plan.inputPath()))&&!Files.exists(Path.of(evidence.path())),"prepare unexpectedly needed EXE/proof input");
        expect(IOException.class,()->prepare(plan,output,stable));
        byte[] valid=ControlBuild.strictMapper().writeValueAsBytes(plan);
        check(decodePlan(Mode.WINDOWS,valid).equals(plan),"strict typed plan roundtrip");
        var bad=ControlBuild.strictMapper().readTree(valid);((com.fasterxml.jackson.databind.node.ObjectNode)bad).put("file_identity_api_buffer_cap",8192.0);
        byte[] invalid=ControlBuild.strictMapper().writeValueAsBytes(bad);expect(IOException.class,()->decodePlan(Mode.WINDOWS,invalid));
        String duplicate="{\"schema\":\""+WINDOW_PLAN_SCHEMA+"\","+new String(valid,java.nio.charset.StandardCharsets.UTF_8).substring(1);
        expect(IOException.class,()->decodePlan(Mode.WINDOWS,duplicate.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        AtomicInteger calls=new AtomicInteger();DirectoryPort drift=new DirectoryPort(){public String machineId(){return machine;}public SharedSourceFiles.DirectoryIdentity directory(Path ignored){return calls.incrementAndGet()==1?identity:other;}};
        expect(IOException.class,()->prepare(plan,root.resolve("drift.json"),drift));check(!Files.exists(root.resolve("drift.json")),"identity drift published a request");
        DirectoryPort missing=new DirectoryPort(){public String machineId(){return machine;}public SharedSourceFiles.DirectoryIdentity directory(Path ignored){return null;}};
        expect(NullPointerException.class,()->prepare(plan,root.resolve("no-id.json"),missing));
        var locator=new LocatorPlan(LOCATOR_PLAN_SCHEMA,machine,Consumer.M1,"software-locator",plan.inputPath(),evidence,root.toString(),RawWindowLocatorContract.Locator.M1_MANAGER_QUEUE_TEXT,new RawWindowLocatorContract.Segment(1024,4096,71141888,71141448),new RawWindowLocatorContract.Targets(0x5cc1240L,0x5cc1610L),1048576,256,16384,475136,196608,plan.reviewAtUtc());
        var located=prepare(locator,root.resolve("locator.json"),stable);check(located.request().equals(RawWindowCaptureJson.decodeRequest(encode(located.request()))),"closed locator strict consumer roundtrip");
        var admission=new Admission(ADMISSION_SCHEMA,machine,Consumer.M5,"/root/budget_fast_lane",CaptureScope.BOUNDED_READ_ONLY_FILE_WINDOWS,prepared.encodedRequest(),evidence,plan.reviewAtUtc());
        check(admission.equals(RawWindowCaptureJson.decode(RawWindowCaptureJson.encode(admission),Admission.class,65536)),"existing issuer contract roundtrip");
    }
    private interface Checked {void run()throws Exception;}
    private static void expect(Class<? extends Throwable> type,Checked work)throws Exception {
        try{work.run();}catch(Throwable actual){if(type.isInstance(actual))return;throw new AssertionError("unexpected rejection type",actual);}throw new AssertionError("expected "+type.getName());
    }
    private static void check(boolean condition,String message){if(!condition)throw new AssertionError(message);}
}
