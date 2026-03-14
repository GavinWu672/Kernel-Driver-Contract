# Kernel Driver Fact Intake Worksheet

## Stage 1 - Locate Core Artifacts

- [ ] project file found
- [ ] dispatch routine source found
- [ ] allocation or pool wrapper source found
- [ ] cleanup / IRP completion source found
- [ ] verifier / SDV / WDK evidence source found

## Stage 2 - Promote High-Risk Facts First

| Fact | Value | Source |
| --- | --- | --- |
| DRIVER_TYPE | pending | pending |
| TARGET_OS | pending | pending |
| IRQL_MAX | pending | pending |
| PAGED_CODE_ALLOWED | pending | pending |
| POOL_TYPE | pending | pending |
| CLEANUP_PATTERN | pending | pending |
| VERIFIER_ENABLED | pending | pending |

## Stage 3 - Promote Review-Shaping Facts

| Fact | Value | Source |
| --- | --- | --- |
| SDV_AVAILABLE | pending | pending |
| WDK_VERSION | pending | pending |
| LOCKING_PRIMITIVES | pending | pending |
| IRP_COMPLETION_MODEL | pending | pending |

## Completion Check

Before calling the contract repo "connected to a real driver repo", confirm:

- [ ] `SOURCE_INVENTORY.md` contains concrete artifact paths
- [ ] `KERNEL_DRIVER_CHECKLIST.md` has updated confirmed fields
- [ ] unresolved facts remain explicitly unresolved rather than guessed
