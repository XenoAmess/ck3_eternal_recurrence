package org.xar.ck3.control.platform;

import java.io.IOException;
import java.time.Instant;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.contracts.GameLifecycle;

/** Original held Game resource monitor. Startup timeouts never become a running Game lifetime. */
final class GameWatchdog {
    /** The production session and software resource regression use the same scheduled monitor. */
    interface Target {
        String sessionId();
        GameLifecycle.TerminalKind inspect()throws IOException;
        void stop(GameLifecycle.TerminalKind reason)throws IOException,InterruptedException;
    }
    private final ScheduledExecutorService timer;
    GameWatchdog(ManagedGameSession session){
        this(new Target(){
            @Override public String sessionId(){return session.sessionId();}
            @Override public GameLifecycle.TerminalKind inspect()throws IOException{return session.watchdogCheck();}
            @Override public void stop(GameLifecycle.TerminalKind reason)throws IOException,InterruptedException{
                session.stop(session.generation(),Instant.now().plusSeconds(25),false,reason);
            }
        });
    }
    GameWatchdog(Target target){
        java.util.Objects.requireNonNull(target);
        timer=Executors.newSingleThreadScheduledExecutor(task->{Thread t=new Thread(task,"xar-original-game-watchdog-"+target.sessionId());t.setDaemon(true);return t;});
        timer.scheduleWithFixedDelay(()->{
            GameLifecycle.TerminalKind reason=null;
            try{reason=target.inspect();}catch(IOException|RuntimeException drift){
                System.err.println("Java Game watchdog observation unavailable; no owner STOP requested: "+drift);
                return;
            }
            if(reason!=null){
                try{target.stop(reason);}
                catch(IOException failed){System.err.println("Java Game watchdog cleanup UNKNOWN; original unsafe marker retained: "+failed);}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();}
                finally{timer.shutdown();}
            }
        },100,1000,TimeUnit.MILLISECONDS);
    }
    void cancel(){timer.shutdown();}
}
