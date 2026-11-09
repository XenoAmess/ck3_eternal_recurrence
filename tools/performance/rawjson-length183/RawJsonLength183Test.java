package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.lang.management.ManagementFactory;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** DATA length component only; no Registry.observe, Attempt, Guard, Native receive or issuer. */
public final class RawJsonLength183Test {
    private static final String PACKET_SHA="4084dcb52ed1ecafadf7fbe6fd11998ff2ed2c06fd22ac077025e519044e4e5d";
    private static final String BODY_SHA="3f05b00dbe620b779df9b86986ced9e702885ad2bee0c3dfc91504c26bc3cd19";
    @TempDir(cleanup=org.junit.jupiter.api.io.CleanupMode.NEVER) Path temporary;

    @Test void first32LengthComponentAndThreeDefensiveDataCases()throws Throwable {
        long whole=System.nanoTime();Path root=property("ck3.p183.reportRoot");assertTrue(Files.isDirectory(root));Path output=root.resolve("p183-rawjson-length-component-fixed32.json");assertFalse(Files.exists(output));
        var report=new LinkedHashMap<String,Object>();var rows=new ArrayList<Map<String,Object>>();var functional=new ArrayList<Map<String,Object>>();Throwable primary=null;
        report.put("schema","ck3.p183.rawjson-length-component-first32/v1");report.put("completed",false);report.put("rows",rows);report.put("functional",functional);
        report.put("fixed_plan","ExactP164frame3400700/4084;LEbody3400696/3f05. CommonnewAPIextendedRawJsoninstance. Aoldbytes().length versusBnewbyteLength(),notliteralphysical357A. First8ABBA32/16each;0setupgetter/0extra warmup. After32only3smallpublicDATAcases0/object/UTF8text;no Registry.observe or retention fixture.");
        report.put("frozen_rule","Allfunction/input/classorigin/oldmethodsCodequalificationPASS;allocation8groupsnonworseandatleast6strictlower;targetmeanANDmedian<=A;pairedpercallB-Amedian<=0. ElsePARKwithoutwarmup/resampling/changedinput. Literalcomparisonwithcurrent357notclaimed;allcold/outliers/coarseCPU/outer/heaplimitationskept.");
        report.put("target_scope","Onlyintlength=raw.bytes().length(A)orraw.byteLength()(B),includingbranchanddirectcall. No clonearrayescape/blackhole/identityforcing;legalJITcloneeliminationisallowedandreported,notdefeated. Hashes/rowpost/report/setupoutside targetbutwholecostkept.");
        try {
            long setup=System.nanoTime();Path inputPath=property("ck3.p183.packetInput");long readStart=System.nanoTime();byte[] packet=Files.readAllBytes(inputPath);long readEnd=System.nanoTime();assertEquals(3_400_700,packet.length);assertEquals(PACKET_SHA,sha(packet));assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
            byte[] body=Arrays.copyOfRange(packet,4,packet.length);assertEquals(3_400_696,body.length);assertEquals(BODY_SHA,sha(body));long constructStart=System.nanoTime();RawJson raw=new RawJson(body);long constructEnd=System.nanoTime();
            report.put("input",Map.of("path",inputPath.toString(),"packet_bytes",packet.length,"packet_sha256",PACKET_SHA,"body_bytes",body.length,"body_sha256",BODY_SHA,"source","ExactP164retainedpacket;bodyextractedbyLEframingonly,noJSONreencode/noNativehappeningclaim"));
            report.put("setup_file_read_ns",readEnd-readStart);report.put("setup_RawJson_ctor_ns",constructEnd-constructStart);report.put("setup_RawJson_ctor_calls",1);report.put("setup_getter_or_scalar_calls",0);report.put("RawJson_origin",origin());
            var mx=assertInstanceOf(com.sun.management.ThreadMXBean.class,ManagementFactory.getThreadMXBean());assertTrue(mx.isThreadAllocatedMemorySupported());if(!mx.isThreadAllocatedMemoryEnabled())mx.setThreadAllocatedMemoryEnabled(true);assertTrue(mx.isCurrentThreadCpuTimeSupported());if(!mx.isThreadCpuTimeEnabled())mx.setThreadCpuTimeEnabled(true);long tid=Thread.currentThread().threadId();
            report.put("heap_before32",heap());report.put("setup_ns_before_first_target",System.nanoTime()-setup);
            int aCalls=0,bCalls=0;
            for(int cycle=0;cycle<8;cycle++)for(int slot=0;slot<4;slot++) {
                boolean old=slot==0||slot==3;String side=old?"A":"B";var row=new LinkedHashMap<String,Object>();row.put("index",rows.size());row.put("cycle",cycle);row.put("slot",slot);row.put("side",side);row.put("target_completed",false);row.put("post_passed",false);rows.add(row);long enclosing=System.nanoTime();int length;
                long a0=mx.getThreadAllocatedBytes(tid),c0=mx.getCurrentThreadCpuTime(),w0=System.nanoTime();
                try {if(old){aCalls++;length=raw.bytes().length;}else{bCalls++;length=raw.byteLength();}}
                catch(Throwable failure){row.put("failure",error(failure));throw failure;}
                finally {long w1=System.nanoTime(),c1=mx.getCurrentThreadCpuTime(),a1=mx.getThreadAllocatedBytes(tid);row.put("wall_start_ns",w0);row.put("wall_end_ns",w1);row.put("cpu_start_ns",c0);row.put("cpu_end_ns",c1);row.put("allocated_start_bytes",a0);row.put("allocated_end_bytes",a1);row.put("wall_ns",w1-w0);row.put("cpu_ns",c1-c0);row.put("allocated_bytes",a1-a0);}
                row.put("target_completed",true);row.put("length",length);assertEquals(body.length,length);assertEquals(PACKET_SHA,sha(packet));assertEquals(BODY_SHA,sha(body));row.put("packet_and_body_unchanged",true);row.put("post_passed",true);row.put("heap_after_post",heap());row.put("enclosing_ns",System.nanoTime()-enclosing);
            }
            assertEquals(32,rows.size());assertEquals(16,aCalls);assertEquals(16,bCalls);report.put("heap_after32",heap());long functionsStart=System.nanoTime();
            smallCase("scalar_zero","0",1,functional);smallCase("empty_object","{}",2,functional);smallCase("UTF8_Han_emoji","\"\u6c49\u5b57\ud83d\ude00\"",12,functional);
            assertEquals(3,functional.size());report.put("functional_ns",System.nanoTime()-functionsStart);long diskPost=System.nanoTime();byte[] finalPacket=Files.readAllBytes(inputPath);assertEquals(PACKET_SHA,sha(finalPacket));assertArrayEquals(packet,finalPacket);report.put("final_file_read_and_input_post_ns",System.nanoTime()-diskPost);assertEquals(BODY_SHA,sha(body));
            report.put("counts",Map.of("measured_A_bytes_getter",16,"measured_B_byteLength",16,"setup_getter_or_scalar",0,"extra_warmup",0,"post_small_DATA_rows",3,"post_small_RawJson_ctor",3,"post_small_byteLength",3,"post_small_bytes_getter",6,"Registry_observe_calls",0,"actual_retention_branch116_hit","NOT_HELD"));
            report.put("all_original_inputs_unchanged",true);report.put("completed",true);
        }catch(Throwable failure){primary=failure;report.put("failure",error(failure));throw failure;}
        finally {
            report.put("before_report_ns",System.nanoTime()-whole);report.put("limitations","APIcomponentonly;AiscommonAPIextendednewRawcontaineroldgetterbehavior,notliteral357. ActualoldCode/metadataqualificationexternalmustpass;classorigindoesnotprovewholeC0compilerprofile. NofreshRegistryretention/adopter/Guard/ledger/permissionorvalidNativeframecredit. JITcloneeliminationnotprevented;fixed32neverresampled. PerrowinputSHA/postoutside targetinenclosing/whole. Sharedheap/GCpostsnotpeak/noforcedGC/OOMEorproviderCPUcausalclaim;coarseCPUpercentagesnull. FirsttargetA/rawfactory/JITcoldallkept. before_reportexcludesmaterialization/write/JUnittail;managedactor/preparation/waitseparate. No businessRuntime/Game/P100/GET/HTTP/JFR/SAVE.");
            try{byte[] bytes=new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(report);assertTrue(bytes.length<=262_144,"bounded external report");Files.write(output,bytes,StandardOpenOption.CREATE_NEW);}catch(Throwable write){if(primary!=null)primary.addSuppressed(write);else throw write;}
        }
    }

    private static void smallCase(String label,String text,int expectedLength,List<Map<String,Object>> rows) {
        var row=new LinkedHashMap<String,Object>();row.put("case",label);row.put("DATA_only",true);row.put("passed",false);rows.add(row);byte[] input=text.getBytes(StandardCharsets.UTF_8),expected=input.clone();assertEquals(expectedLength,input.length);RawJson raw=new RawJson(input);input[0]^=1;byte[] first=raw.bytes();assertArrayEquals(expected,first);assertNotSame(input,first);first[0]^=1;byte[] second=raw.bytes();assertArrayEquals(expected,second);assertNotSame(first,second);assertEquals(expectedLength,raw.byteLength());row.put("expected_byte_length",expectedLength);row.put("original_input_sha256",sha(expected));row.put("ctor_input_mutation_preserved_value",true);row.put("getter_mutation_preserved_value",true);row.put("RawJson_ctor_calls",1);row.put("byteLength_calls",1);row.put("bytes_getter_calls",2);row.put("passed",true);
    }

    private static Map<String,Object> origin()throws Exception {
        Path expectedRoot=property("ck3.p183.rawJsonRoot"),actualRoot=Path.of(RawJson.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();assertEquals(expectedRoot,actualRoot);Path file=actualRoot.resolve("org/xar/ck3/control/application/action/RawJson.class");byte[] bytes=Files.readAllBytes(file);String expectedSha=Objects.requireNonNull(System.getProperty("ck3.p183.rawJsonSha256"),"actualclosedRawJsonpinrequired");assertTrue(expectedSha.matches("[0-9a-f]{64}"));assertEquals(expectedSha,sha(bytes));assertEquals(int.class,RawJson.class.getMethod("byteLength").getReturnType());assertEquals(byte[].class,RawJson.class.getMethod("bytes").getReturnType());return Map.of("FQName",RawJson.class.getName(),"root",actualRoot.toString(),"class_path",file.toString(),"bytes",bytes.length,"sha256",sha(bytes),"class_loader",RawJson.class.getClassLoader().getClass().getName(),"A_control","SameAPIextendedcontaineroldgetter;notliteralphysical357");
    }
    private static Path property(String key)throws Exception{return Path.of(Objects.requireNonNull(System.getProperty(key),"explicitqualifiedofflinepathrequired: "+key)).toRealPath();}
    private static String sha(byte[] bytes){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(java.security.NoSuchAlgorithmException unavailable){throw new IllegalStateException(unavailable);}}
    private static Map<String,Object> heap(){long count=0,time=0;for(var gc:ManagementFactory.getGarbageCollectorMXBeans()){count+=gc.getCollectionCount();time+=gc.getCollectionTime();}var heap=ManagementFactory.getMemoryMXBean().getHeapMemoryUsage();return Map.of("used_bytes",heap.getUsed(),"committed_bytes",heap.getCommitted(),"gc_count",count,"gc_time_ms",time,"scope","sharedpostobservation/noforcedGC/notpeak");}
    private static Map<String,Object> error(Throwable failure){var out=new LinkedHashMap<String,Object>();out.put("class",failure.getClass().getName());out.put("message",failure.getMessage());if(failure.getCause()!=null)out.put("cause",error(failure.getCause()));if(failure.getSuppressed().length>0){var suppressed=new ArrayList<Map<String,Object>>();for(var item:failure.getSuppressed())suppressed.add(error(item));out.put("suppressed",suppressed);}return out;}
}
