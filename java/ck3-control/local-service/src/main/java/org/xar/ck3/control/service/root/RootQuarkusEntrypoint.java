package org.xar.ck3.control.service.root;

import java.util.Objects;
import io.quarkus.runtime.annotations.QuarkusMain;

/** Build-selected entry: each actual application retains its original Quarkus/CDI lifetime. */
@QuarkusMain(name="root-entry")
public final class RootQuarkusEntrypoint {
    private RootQuarkusEntrypoint(){ }
    public enum Application { PUBLIC_HOST,ROOT_STARTUP }
    public static Application select(String[] arguments) {
        Objects.requireNonNull(arguments);
        if(arguments.length==3||arguments.length==6) {
            RootSavedNativeCoordinator.arguments(arguments);
            return Application.ROOT_STARTUP;
        }
        // The actual public host accepts zero arguments and itself returns 64 for unsupported counts, including four.
        return Application.PUBLIC_HOST;
    }
    public static void main(String... arguments) {
        switch(select(arguments)) {
            case PUBLIC_HOST->org.xar.ck3.control.service.mcp.RootApplicationMain.main(arguments);
            case ROOT_STARTUP->RootApplicationMain.main(arguments);
        }
    }
}
