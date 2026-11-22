package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Narrow archived Save DATA verification. This never reconstructs a CoreReceived or an old permit. */
final class SupermanHealthBaselineReceipt {
    final ExactRef progress,owner;
    final FileWitness source,archive;
    final CoreFrame.Prefix saved;
    final JsonNode oldSession;
    final Instant acknowledgedAt;
    private SupermanHealthBaselineReceipt(ExactRef progress,ExactRef owner,FileWitness source,FileWitness archive,
            CoreFrame.Prefix saved,JsonNode oldSession,Instant acknowledgedAt) {
        this.progress=progress;this.owner=owner;this.source=source;this.archive=archive;
        this.saved=saved;this.oldSession=oldSession.deepCopy();this.acknowledgedAt=acknowledgedAt;
    }
    static SupermanHealthBaselineReceipt load(ExactRef progress,ExactRef owner,FileWitness source,FileWitness archive)throws IOException {
        try {
            Path home=Path.of(progress.path()).toAbsolutePath().normalize().getParent();
            var row=NativeWire.object(NativeWire.parse(read(progress,4*1024*1024)));
            text(row,"schema","xar.native-owner-current-superman-health/v1");
            text(row,"mode","current_superman_health_baseline_save_and_begin");
            require(ExactRef.fromJson(row.get("owner_descriptor")).equals(owner),"Baseline belongs to a different actual owner");read(owner,1024*1024);
            integer(row,"save_calls",1);integer(row,"choose_calls",0);integer(row,"read_calls",2);
            bool(row,"baseline_physical_material_observed",true);bool(row,"query_available",false);bool(row,"known_choice_dispatched",false);
            var checkpoint=NativeWire.object(row.get("baseline_checkpoint"));integer(checkpoint,"save_calls",1);
            text(checkpoint,"save_dispatch_class","AckReceived");text(checkpoint,"native_checkpoint_status","submitted");
            bool(checkpoint,"changed_physical_material_observed",true);bool(checkpoint,"archive_is_copy_not_another_SAVE",true);
            require(witness(checkpoint.get("checkpoint_source")).equals(source)&&witness(checkpoint.get("checkpoint_immutable_archive")).equals(archive),"Actual archived baseline witnesses differ");
            verifyPair(source,archive);
            var originals=NativeWire.object(row.get("originals"));
            require(!originals.has("superman_health_choice_intent")&&!originals.has("superman_health_choice_original_result")&&!row.has("choose_result"),"A prior Begin attempt cannot acquire another intent");
            var failed=NativeWire.object(originals.get("core_dispatch"));text(failed,"class","Unknown");
            text(failed,"failure_kind","FRAME_BUDGET_EXHAUSTED");text(failed,"failure_stage","RESPONSE_WAIT");
            var failedRequest=NativeWire.decodeExecuteRequest(material(failed.get("outbound"),home));
            require(failedRequest.step().equals(CoreFrame.STEP)&&NativeWire.object(NativeWire.parse(failedRequest.normalizedAdditionalFields().value())).isEmpty(),"Only the original readonly Core frame-budget failure is recoverable");
            var savedOriginals=NativeWire.object(originals.get("baseline_checkpoint"));
            var core=ack(savedOriginals.get("core_dispatch"),home,CoreFrame.STEP);
            var decoded=CoreFrame.decode(new RawJson(core.result));require(decoded instanceof CoreFrame.Partial,"Original Save Core unavailable");
            var actual=(CoreFrame.Partial)decoded;
            var save=ack(savedOriginals.get("save_dispatch"),home,CurrentCoreCheckpointSave.STEP);
            var submitted=CurrentCoreCheckpointSaveResult.decode(new RawJson(save.result));
            require(submitted.accepted()&&submitted.effectAttempted()&&submitted.submission().orElseThrow().dateRaw()==actual.prefix().dateRaw(),"Original Save was not accepted on its actual Core date");
            text(checkpoint,"save_request_id",save.request.requestId());
            require(StrictJson.integer(checkpoint.get("source_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)==actual.prefix().dateRaw(),"Original Save date differs from physical baseline");
            require(core.custody.get("session").equals(save.custody.get("session"))&&core.custody.get("custody_epoch").equals(save.custody.get("custody_epoch")),"Original Core/Save crossed session or custody");
            require(order(core.custody,"response_received").compareTo(order(save.custody,"write_entered"))<0,"Original Save did not follow its Core ACK");
            var fields=NativeWire.object(NativeWire.parse(save.request.normalizedAdditionalFields().value()));
            var deadline=fields.remove("core_control_deadline_unix_ms");require(deadline!=null&&deadline.isIntegralNumber(),"Original Save deadline absent");
            require(fields.equals(NativeWire.parse(CurrentCoreCheckpointSave.request(actual).additionalFields().bytes())),"Original Save claim differs from its complete actual Core");
            Instant originalDeadline=Instant.parse(StrictJson.text(checkpoint.get("save_deadline_utc")));
            require(deadline.longValue()==originalDeadline.toEpochMilli()&&!time(save.custody,"response_received").isAfter(originalDeadline),"Original Save ACK escaped its unchanged deadline");
            return new SupermanHealthBaselineReceipt(progress,owner,source,archive,actual.prefix(),save.custody.get("session"),time(save.custody,"response_received"));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid original health baseline recovery material",invalid);}
    }
    void verifyCurrent(NativeObservationPort.TransportSession session,CoreFrame.Prefix fresh,Instant actualCoreWrite)throws IOException {
        require(saved.equals(fresh),"Fresh actual Core differs from the complete original saved actor/date/pause state");
        require(StrictJson.text(oldSession.get("machine_id")).equals(session.machineId())&&StrictJson.text(oldSession.get("session_id")).equals(session.sessionId())
                &&GameGeneration.fromJson(oldSession.get("game")).equals(session.game()),"Baseline recovery crossed actual owner session/Game");
        require(new BigInteger(StrictJson.text(oldSession.get("connection_generation"))).compareTo(session.connectionGeneration())<0,"Recovery requires an independent later actual connection");
        require(actualCoreWrite.isAfter(acknowledgedAt),"New actual Core must follow the original Save ACK");
        read(progress,4*1024*1024);read(owner,1024*1024);verifyPair(source,archive);
    }
    static void verifyPair(FileWitness source,FileWitness archive)throws IOException {
        require(source.reference().bytes()>0&&source.reference().bytes()<=1L<<30&&source.reference().bytes()==archive.reference().bytes()
                &&source.reference().sha256().equals(archive.reference().sha256())&&!source.identity().fileId().equals(archive.identity().fileId())
                &&!Path.of(source.reference().path()).toAbsolutePath().normalize().equals(Path.of(archive.reference().path()).toAbsolutePath().normalize())
                &&Path.of(source.reference().path()).getFileName().toString().equals(CurrentCoreCheckpointSave.FILENAME),"Independent original fixed checkpoint/archive pair required");
        var files=new NativeCheckpointFiles();files.verify(source);files.verify(archive);
    }
    private record Archived(NativeWire.ExecuteRequest request,byte[] result,JsonNode custody) { }
    private static Archived ack(JsonNode data,Path home,String step)throws IOException {
        var row=NativeWire.object(data);text(row,"class","AckReceived");bool(row,"native_ok",true);
        byte[] packet=material(row.get("ack_packet"),home),request=material(row.get("outbound"),home),token=material(row.get("result_token"),home);
        var outgoing=NativeWire.decodeExecuteRequest(request);require(outgoing.step().equals(step)&&outgoing.expectedRevision().equals(java.util.Optional.of(BigInteger.ZERO))&&outgoing.expectedSnapshotRevision().isEmpty(),"Original archive request profile changed");
        text(row,"request_id",outgoing.requestId());var frame=NativeWire.decode(packet);require(frame instanceof NativeWire.CommandResult,"Original ACK is not command_result");var result=(NativeWire.CommandResult)frame;
        require(result.nativeOk()&&result.requestId().equals(outgoing.requestId())&&result.result().presence()==NativeWire.Presence.VALUE
                &&Arrays.equals(result.result().token().orElseThrow().value(),token),"Original accepted ACK/token identity differs");
        require(Arrays.equals(material(row.get("ack_payload"),home),result.payload().value()),"Original ACK payload differs");
        var custody=NativeWire.object(NativeWire.parse(material(row.get("custody_material"),home)));
        require(custody.equals(row.get("actual_custody")),"Archived endpoint custody differs from progress");text(custody,"request_id",outgoing.requestId());
        identity(custody.get("original_request"),request);identity(custody.get("original_response"),packet);
        require(order(custody,"write_entered").compareTo(order(custody,"write_completed"))<0&&order(custody,"write_completed").compareTo(order(custody,"response_received"))<0
                &&!time(custody,"write_completed").isBefore(time(custody,"write_entered"))&&!time(custody,"response_received").isBefore(time(custody,"write_completed")),"Original archived endpoint chronology regressed");
        return new Archived(outgoing,token,custody);
    }
    private static byte[] material(JsonNode value,Path home)throws IOException {
        var ref=ExactRef.fromJson(value.get("reference"));require(Path.of(ref.path()).toAbsolutePath().normalize().startsWith(home),"Original material escaped its exact progress directory");return read(ref,1024*1024);
    }
    private static byte[] read(ExactRef ref,int maximum)throws IOException {
        Path path=Path.of(ref.path());require(path.isAbsolute()&&ref.bytes()>0&&ref.bytes()<=maximum&&!Files.isSymbolicLink(path)&&Files.size(path)==ref.bytes(),"Bounded exact original file required");
        byte[] raw=Files.readAllBytes(path);require(raw.length==ref.bytes()&&ActionCodec.sha256(raw).equals(ref.sha256()),"Original file bytes/SHA changed");return raw;
    }
    private static FileWitness witness(JsonNode row){return new FileWitness(ExactRef.fromJson(row.get("reference")),FileStatIdentity.fromJson(row.get("identity"),FileStatIdentity.SCHEMA));}
    private static void identity(JsonNode row,byte[] bytes)throws IOException {require(StrictJson.integer(row.get("bytes"),1,1024*1024)==bytes.length&&StrictJson.text(row.get("sha256")).equals(ActionCodec.sha256(bytes)),"Archived packet bytes/SHA differ from endpoint custody");}
    private static BigInteger order(JsonNode row,String event){return new BigInteger(StrictJson.text(row.get(event).get("order")));}
    private static Instant time(JsonNode row,String event){return Instant.parse(StrictJson.text(row.get(event).get("observed_at_utc")));}
    private static void text(JsonNode row,String key,String expected)throws IOException {require(StrictJson.text(row.get(key)).equals(expected),"Original baseline field differs: "+key);}
    private static void integer(JsonNode row,String key,long expected)throws IOException {require(StrictJson.integer(row.get(key),0,Long.MAX_VALUE)==expected,"Original baseline count differs: "+key);}
    private static void bool(JsonNode row,String key,boolean expected)throws IOException {require(row.has(key)&&row.get(key).isBoolean()&&row.get(key).booleanValue()==expected,"Original baseline boolean differs: "+key);}
    private static void require(boolean condition,String reason)throws IOException {if(!condition)throw new IOException(reason);}
}
