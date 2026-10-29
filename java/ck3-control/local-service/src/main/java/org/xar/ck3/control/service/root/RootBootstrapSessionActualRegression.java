package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootBootstrapProtocol.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.*;

/** Postqualification CI/readback of a real Shared Session run, never a substitute for running it.
 * Missing actual inputs fail. No test fixture, build receipt or capacity authority is manufactured. */
public final class RootBootstrapSessionActualRegression {
    private RootBootstrapSessionActualRegression(){ }
    public static void main(String[] args)throws Exception {
        if(args.length!=7||!args[0].equals("verify"))throw new IOException("verify SESSION_PATH BYTES SHA TERMINAL_PATH BYTES SHA required; actual Shared run must have completed");
        verify(ref(args,1),ref(args,4));
    }
    public static void verify(FileRef requestRef,FileRef terminalRef)throws Exception {
        var request=RootProfileBootstrapSession.read(requestRef,RootProfileBootstrapSession.SESSION_REQUEST_BYTES,RootProfileBootstrapSession.Request.class);
        var terminal=RootProfileBootstrapSession.read(terminalRef,65536,RootProfileBootstrapSession.Terminal.class);
        Path root=Path.of(request.controlRoot());
        if(!Path.of(terminalRef.path()).equals(root.resolve("terminal.json"))
                ||terminal.status()!=RootProfileBootstrapSession.Status.COMPLETE_NO_GAME_ADMISSION
                ||!terminal.sessionRequest().equals(requestRef)||!terminal.machineId().equals(request.machineId())
                ||!terminal.deadline().equals(request.deadline())||terminal.failure()!=null||terminal.actualExit()==null
                ||!terminal.actualExit().commandResult().passed()||!terminal.child().equals(terminal.actualExit().commandResult().identity())
                ||terminal.sessionNonce()==null||!terminal.sessionNonce().matches("[0-9a-f]{64}")
                ||terminal.phases().size()!=request.mode().phases().size())throw new IOException("real completed finite Session/Job required, no skipped or fabricated qualification");
        var origins=RootProfileBootstrapSession.read(FileRef.measure(root.resolve("child-origins.json")),65536,Origin.class);
        if(!origins.request().equals(requestRef)||origins.mode()!=request.mode())throw new IOException("actual child origin evidence belongs to another Session");
        RootBootstrapRuntime.verifyObservation(request.runtime(),request.mode(),origins.classes());
        RootBootstrapRuntime.verifyCarrier(request.runtime(),origins.carrier());
        RootProfileBootstrapSession.verifyChildCompletion(requestRef,request,terminal);
        var progress=new java.util.ArrayList<RootProfileBootstrapSession.Progress>();
        for(int i=0;i<terminal.phases().size();i++){
            var phase=terminal.phases().get(i);String expected=request.mode().phases().get(i);
            if(!phase.phase().equals(expected)||phase.state()!=RootProfileBootstrapSession.PhaseState.CREATED||phase.writeReceipt()==null
                    ||phase.writeReceipt().bytesWritten()<1||!phase.writeReceipt().identity().equals(terminal.child())
                    ||!phase.writeReceipt().sessionNonce().equals(terminal.sessionNonce())
                    ||!Path.of(phase.quote().path()).equals(root.resolve("phase-"+i+"-quote.json")))throw new IOException("missing actual per-phase send/readback evidence");
            var quote=RootProfileBootstrapSession.read(phase.quote(),FRAME_BYTES-1,Quote.class);
            RootProfileBootstrapSession.verifyQuote(request,expected,quote);
            if(phase.createdEvidence()==null||!Path.of(phase.createdEvidence().path()).equals(root.resolve("phase-"+i+"-created.json")))throw new IOException("actual completed frame reference missing");
            phase.createdEvidence().verify();
            var stage=RootBootstrapProtocol.stage(line(Path.of(phase.createdEvidence().path())),request.machineId());
            RootProfileBootstrapSession.verifyStage(quote,stage);
            progress.add(new RootProfileBootstrapSession.Progress(phase.phase(),phase.state(),phase.quote(),phase.writeReceipt(),stage.created()));
            var envelope=RootProfileBootstrapSession.read(FileRef.measure(root.resolve("phase-"+i+"-issuer-quote.json")),65536,IssuerQuote.class);
            var reply=RootProfileBootstrapSession.read(FileRef.measure(root.resolve("phase-"+i+"-issuer-reply.json")),65536,IssuerReply.class);
            if(!reply.original().equals(envelope)||!envelope.quote().equals(phase.quote())||!envelope.child().equals(terminal.child())
                    ||!envelope.sessionNonce().equals(terminal.sessionNonce())||!envelope.phase().equals(expected)
                    ||phase.writeReceipt().bytesWritten()!=RootBootstrapProtocol.bindingLine(reply.binding()).length)throw new IOException("independent issuer correlation differs from actual pipe write");
            reply.binding().verify();
        }
        RootProfileBootstrapSession.verifyFinal(request,progress,line(root.resolve("final-originals.json")));
        System.out.println("ACTUAL_SESSION_READBACK_VERIFIED_NO_GAME_ADMISSION");
    }
    private static byte[] line(Path path)throws IOException {
        var original=SharedSourceFiles.observe(path);if(original.source().bytes()>FRAME_BYTES-1)throw new IOException("bounded actual frame required");
        byte[] bytes=Files.readAllBytes(path);SharedSourceFiles.assertUnchanged(original);byte[] line=java.util.Arrays.copyOf(bytes,bytes.length+1);line[bytes.length]='\n';return line;
    }
    private static FileRef ref(String[] args,int index)throws IOException {
        long bytes=Long.parseLong(args[index+1]);if(!Long.toString(bytes).equals(args[index+1]))throw new IOException("canonical exact byte count required");
        return new FileRef(Path.of(args[index]).toAbsolutePath().normalize().toString(),bytes,args[index+2]);
    }
}
