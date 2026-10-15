# Normal exit with source-bound unrelated mod GUI

The actual More Tenets Slots R0016 host passed effective-source projection and
then failed before CK3 launch: `normal-exit private V1 does not support enabled
mod GUI files`. The existing inventory verifier intentionally rejected every
`.gui` file. The two religion windows did not change the pause menu; the shared
zero-GUI scope blocked their otherwise unrelated source inventory.

The scope now permits GUI mods whose source is independent of the existing
normal-exit presentation chain. The six existing `STOCK_GUI_PATHS` remain fully
byte-bound and protected against mod path replacement. The three native fixed
roots are `timeline_widget`, `ingame_pausemenu`, and
`ingame_resign_confirmation`. The narrow GUI source reader follows their stock
global type/template references, including transitive references and all
providers of a duplicate stock declaration. Dependency files are pinned in the
optional `stock_gui_dependencies` inventory field; the verifier independently
recomputes the closure and checks its exact order, paths, bytes and hashes.
Legacy inventories for mods without GUI retain their existing shape.

A mod GUI remains unsupported if it replaces a protected/dependency file,
declares a global type/template used by the exit chain, redefines a fixed exit
root, or refers to `OnPauseMenu`, `PauseMenu.*` or
`ResignConfirmationWindow.*`. Merely instantiating `button_standard` inside an
unrelated window does not redefine that global type. Comments and quoted text
do not masquerade as declarations. Descriptor archive/replace-path refusal,
complete enabled-mod inventory, executable/settings/profile pins and actual
native fixed-target census/dispatch checks remain independent.

On the installed exact CK3 1.20.0.4 source, the three roots reach **99** protected
type/template symbols and **12** additional GUI source files. The actual MTS
`window_faith.gui` and `window_rite_creation.gui` have no prohibited overlap.
The closure read took about 1.37 seconds on this machine; this is a terminal
source check, not a recurring gameplay observation. The product source is not
copied into the framework. Synthetic fixtures verify allowed unrelated GUI,
global type and transitive template overrides, fixed-root/callback/path
conflicts, changed dependency bytes, and refusal of GUI inventory without its
dependency sources. Old complete-inventory checks remain covered.

[`ck3_mod_acceptance_host_preflight.py`](../../tools/ck3_mod_acceptance_host_preflight.py)
closes the missing offline admission step. Given the selected runtime and a
real frozen host argv, it derives a separate diagnostic userdir from explicitly
inventoried prepared inputs, verifies those bytes, and calls the actual selected
wrapper. The wrapper performs its actual checked-source projection, parser,
`public_profile.create_profile`, inventory builder and verifier. Only the
underlying host `main` is replaced with a stop callback, after module definition
loading; no game/session/pipe entry executes. A PASS requires the actual static
profile receipt to report verified sources. The original run profile is not
modified and the diagnostic profile has no launch authority.

Use one fresh output directory, for example:

```text
python tools/ck3_mod_acceptance_host_preflight.py --runtime <selected-runtime.json> --frozen-argv <actual-frozen-argv.json> --output <new-diagnostic-directory>
```

The merged successor must include this verifier and its helper in the selected
source root/index, the updated inventory builder and its host/config/import
pins, as well as the actual DLL and host feature selection. Updating only an
external builder would leave the runtime Driver using the old refusal. R0015,
R0016 and their frozen inputs remain intact. Static GUI/profile qualification
does not prove visible windows, native query business results, orderly process
exit or product acceptance; those still require the controlled live run.

Ownership: generic source compatibility, builder, preflight and fixtures belong
to `ck3_eternal_recurrence`; MTS mechanisms and actual product acceptance belong
to `ck3_mod_more_tenant_slots`. `open_kaishek` script semantics are not applicable
to the GUI type/template reference analysis; it does not execute CK3 scripts.
