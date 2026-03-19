# Kernel Driver Fact Intake Worksheet

## Stage 1 - Locate Core Artifacts

- [ ] project file found
- [ ] dispatch routine source found
- [ ] PnP / power state source found
- [ ] allocation or pool wrapper source found
- [ ] cleanup / IRP completion source found
- [ ] verifier / SDV / WDK evidence source found

## Stage 2 - Promote Human-Mandatory Facts First

| Fact | Value | Source |
| --- | --- | --- |
| DRIVER_TYPE | pending | pending |
| TARGET_OS | pending | pending |
| WDK_VERSION | pending | pending |
| PNP_MODEL | pending | pending |
| POWER_MANAGED | pending | pending |
| IRQL_MAX | pending | pending |
| INTERRUPT_MODEL | pending | pending |
| DMA_MODEL | pending | pending |
| CONFIG_SPACE_ACCESS_LEVEL | pending | pending |
| PAGED_CODE_ALLOWED | pending | pending |
| POOL_TYPE | pending | pending |
| VERIFIER_ENABLED | pending | pending |
| SDV_AVAILABLE | pending | pending |

## Stage 3 - Produce AI-Verifiable Fact Summary

| Fact | Value | Source |
| --- | --- | --- |
| IO_BUFFERING_MODEL | pending | pending |
| IOCTL_SURFACE_PRESENT | pending | pending |
| DEVICE_NAMING_MODEL | pending | pending |
| SECURITY_DESCRIPTOR_MODEL | pending | pending |
| REMOVE_LOCK_USED | pending | pending |
| LOCKING_PRIMITIVES | pending | pending |
| IRP_COMPLETION_MODEL | pending | pending |
| CLEANUP_PATTERN | pending | pending |

## Completion Check

Before calling the contract repo "connected to a real driver repo", confirm:

- [ ] `SOURCE_INVENTORY.md` contains concrete artifact paths
- [ ] human-mandatory facts are resolved or explicitly blocked
- [ ] AI-verifiable facts are surfaced with source locations instead of hidden assumptions
- [ ] `KERNEL_DRIVER_CHECKLIST.md` has updated confirmed fields
- [ ] unresolved facts remain explicitly unresolved rather than guessed