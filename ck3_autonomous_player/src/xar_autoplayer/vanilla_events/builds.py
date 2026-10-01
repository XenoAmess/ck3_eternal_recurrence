"""Build identities for the historical registry and its reviewed migration."""

from typing import Final

CURRENT_CK3_BUILD: Final = "1.20.0.3"
CURRENT_CK3_EXE_SHA256: Final = (
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
)
SUPPORTED_CK3_EXE_SHA256: Final = {
    "1.19.0.6": "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
    "1.20.0.2": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
    CURRENT_CK3_BUILD: CURRENT_CK3_EXE_SHA256,
}
MIGRATED_CK3_BUILDS: Final = frozenset({"1.20.0.2", "1.20.0.3"})
NONWAR_MIGRATION_DEFERRED_EVENT_KEYS: Final = frozenset({
    "fervor.1002", "court_chaplain_task.0313", "great_holy_war.0011",
})


def event_context_build(context: object, *, default: str = "1.19.0.6") -> str:
    """Use the published exact native backend identity or an explicit build.

    Old replay contexts predate build metadata and retain their legacy default.
    A current serializer publishes its backend identity in provenance, so the
    formal planner does not need a machine-specific configuration switch.
    """
    if not isinstance(context, dict):
        return default
    if isinstance(context.get("ck3_build"), str):
        return context["ck3_build"]
    provenance = context.get("provenance")
    if isinstance(provenance, dict):
        if isinstance(provenance.get("ck3_build"), str):
            return provenance["ck3_build"]
        backend = provenance.get("backend_id")
        for build in SUPPORTED_CK3_EXE_SHA256:
            if backend == f"ck3-{build}-native-event-window-v1":
                return build
    return default
