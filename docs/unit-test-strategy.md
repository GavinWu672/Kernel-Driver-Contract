# Unit Test Strategy for Kernel Driver Functions

## Purpose

This document defines the canonical approach for writing user-mode unit tests against Windows kernel driver functions. It exists to prevent a common failure mode: AI agents attempting to stub WDK headers (`ntddk.h`, `wdf.h`, `wdm.h`) for user-mode compilation, which produces an unbounded chain of missing type and symbol errors.

It also defines how to review a partial logic-extraction test so the team does not mistake "the compilable 60%" for full driver-path verification.

## Decision Tree

Before writing any test, apply this decision tree to the target function:

```
1. Does the target function call a kernel API through a function pointer
   or struct interface (e.g., BUS_INTERFACE_STANDARD.GetBusData,
   a driver-internal callback table)?

   YES -> Use seam substitution (see Approach A).
         No WDK headers needed.

2. Does the target function contain pure logic with no kernel API calls
   (e.g., arithmetic, bit manipulation, state machine transitions)?

   YES -> Extract into a separate .c file and compile directly.
         No WDK headers needed.

3. Does the target function call WDF or WDM APIs directly, not through
   a pointer (e.g., WdfDeviceCreate, ExAllocatePool2)?

   YES -> This function is NOT user-mode testable as written.
         Do NOT attempt to stub WDK headers.
         Correct responses:
           a) Test via Driver Verifier + VM integration test.
           b) Refactor: wrap the WDF calls in a thin function-pointer
              layer, then use Approach A.
```

## Approach A - Seam Substitution (Preferred)

Use when a function pointer or interface struct already exists on the call path.

### Structure

```
Tests/
  test_<function>.c    -> minimal struct definitions + test cases
  stub_<seam>.c        -> fake implementation of the seam interface
  (no driver .c files included in this compilation unit)
  (no kmstubs/ directory)
```

### Minimal type definitions

Define only the fields that the target function actually touches. Use opaque pointers (`void*` or `typedef struct _FOO* PFOO`) for any type the test does not inspect.

```c
/* test_Adapter_GetPciConfig.c */
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <stdint.h>

typedef long     NTSTATUS;
typedef uint32_t ULONG;
#define STATUS_SUCCESS      0L
#define STATUS_UNSUCCESSFUL 0xC0000001L
#define NT_SUCCESS(s)       ((NTSTATUS)(s) >= 0)

/* Seam interface -> only the fields the function uses */
typedef ULONG (*PFN_GET_BUS_DATA)(void*, ULONG, void*, ULONG, ULONG);
typedef struct { PFN_GET_BUS_DATA GetBusData; void *Context; } BUS_INTERFACE_STANDARD;

/* Minimal driver struct -> only fields touched by the target function */
typedef struct { void *pBusIfStd; } CHIP_REF;
typedef struct { int GlDevEnum; } CHIP_FAMILY;
typedef struct {
    CHIP_REF    Ref;
    CHIP_FAMILY Family;
    uint32_t    PciConfigBuf[64];
} CHIP_DATA;
typedef struct { CHIP_DATA ChipData; } FDO_DEVICE_EXTENSION;

/* Global side-effects the function writes -> defined here for the test */
ULONG gConfig = 0, gConfig2 = 0, gConfig3 = 0, gConfig4 = 0, gConfig5 = 0;

#define CHIP_ADD_CFG_REG_LOG(a, b, c, d)  /* empty -> logging not under test */
```

### Seam stub

```c
/* stub_pci.c */
#include <stdint.h>
#include <string.h>

static uint32_t g_fake_cfg[64];

ULONG FakePciGetBusData(void *ctx, ULONG type,
                         void *buf, ULONG offset, ULONG len) {
    (void)ctx; (void)type;
    if (offset + len > sizeof(g_fake_cfg)) return 0;
    memcpy(buf, (uint8_t *)g_fake_cfg + offset, len);
    return len;
}

void FakePci_SetConfigWord(unsigned index, uint32_t value) {
    g_fake_cfg[index] = value;
}
```

### Build command

```cmd
cl.exe test_Adapter_GetPciConfig.c stub_pci.c /W4 /Fe:test.exe
```

No `/I` pointing to any WDK directory. No `kmstubs/`. One command, any MSVC.

## Approach B - Logic Extraction

Use when the target function mixes pure logic with kernel API calls.

Extract the pure logic into a new file that includes no kernel headers:

```c
/* pci_devid_classify.c -> no kernel header */
#include "pci_devid_classify.h"

int ClassifyPciDeviceId(unsigned long devId) {
    switch (devId) {
    case 0x9755: return GL_DEV_GL9755A;
    case 0x9750: return GL_DEV_GL9750A;
    default:     return GL_DEV_NONE;
    }
}
```

The original driver function calls `ClassifyPciDeviceId()`. The test compiles only `pci_devid_classify.c` and the test file -> no driver source, no WDK headers.

## Reviewer Checklist for Partial Logic Extraction

Use this checklist when a test only covers a helper extracted from a larger driver function.

### 1. Extraction Boundary

Ask:

- Does the extracted helper have a single, explicit responsibility?
- Is it clearly described as pure logic, not driver-path orchestration?
- Did the refactor isolate logic, or merely cut away the hard-to-compile lines?

Red flag:

- The extracted helper still conceptually depends on device state, IRQL, hardware lifetime, or WDK ownership rules, but those dependencies are no longer visible in the test.

### 2. Driver-State Dependency Check

Ask:

- Does the extracted code depend on PnP state, power state, interrupt connection, DMA ownership, or remove-path validity?
- Would the result change if the device were stopped, surprise-removed, or powered down?
- Is any omitted variable actually a lifecycle fact rather than an incidental type definition?

If yes:

- the helper is not pure enough for standalone user-mode testing
- review against `KSTATE-*` rules is still required
- integration or verifier-based evidence is still needed

### 3. Semantic Completeness Check

Ask:

- Did the extracted helper preserve the real decision core of the original function?
- Are default cases, error cases, unknown-device paths, and fallback behavior included?
- Were any guard conditions, preconditions, or side-effect ordering rules left behind in the driver-facing wrapper?

Red flag:

- The unit test passes because the difficult branches were excluded, not because the original behavior was preserved.

### 4. Wrapper Residual Risk Check

Ask what remains in the original function after extraction.

Acceptable residual wrapper:

- reading kernel or bus data
- marshalling inputs into the pure helper
- applying the helper result back into driver-owned state
- logging or tracing not central to decision correctness

High-risk residual wrapper:

- error-path branching
- resource ownership changes
- cleanup or unwind behavior
- state gating based on PnP, power, interrupt, or DMA state
- security or namespace decisions

If high-risk logic remains outside the helper, the unit test covers only a slice of correctness.

### 5. Verification Coverage Check

Require explicit statement of what the unit test does not prove.

The review should answer:

- Which exact behavior is now covered by the user-mode test?
- Which behavior is still uncovered because it depends on WDK, OS callbacks, IRQL, or device lifecycle?
- What other evidence is expected: code review, SDV, Driver Verifier, VM integration test, or manual lifecycle review?

### 6. Minimum Acceptable Review Summary

A good review note for a partial extraction should look like this:

- extracted helper scope: only `device_id -> config profile` mapping
- not covered: PCI config access, adapter state ownership, remove-path teardown, interrupt or power-state behavior
- residual wrapper risk: low / medium / high, with reason
- preserved semantics: default and unknown-device cases still match the original switch logic
- remaining required evidence: Driver Verifier / SDV / lifecycle review / integration test

## What a Prohibited Approach Looks Like

The following pattern violates KD-011 and must not be used:

```
Tests/
  kmstubs/
    ntddk.h      -> synthetic stub of a WDK header    (PROHIBITED)
    wdf.h        -> synthetic stub of a WDK header    (PROHIBITED)
    wdm.h        -> synthetic stub of a WDK header    (PROHIBITED)
    ...
  build_tests.cmd  /I kmstubs                         (PROHIBITED)
```

This approach fails because WDK headers have hundreds of interdependent type declarations with kernel-mode ordering constraints that cannot be reproduced in user mode. Each synthetic stub that resolves one error reveals the next dependency in the chain without converging.

## Testability Classification

| Function characteristic | Testable in user mode? | Approach |
|---|---|---|
| Calls kernel API via function pointer / interface struct | Yes | A -> seam substitution |
| Contains pure logic (no kernel calls) | Yes | B -> extract and test directly |
| Calls WDF/WDM APIs directly | No | Driver Verifier + VM integration test |
| Entry point called by PnP / power manager | No | Driver Verifier + VM integration test |
| Extracted helper still depends on lifecycle facts | Not sufficient by itself | Unit test plus lifecycle review and stronger evidence |

## Relationship to KD-010 and KD-011

- **KD-010** (static-analysis-clean): governs Driver Verifier, SDV, and WDK PREfast. These tools operate in the WDK build environment and are the correct tools for verifying WDF API usage correctness.

- **KD-011** (unit-test-boundary): governs user-mode unit tests. These tests verify business logic and error-path coverage that static analysis cannot easily check.

The two layers are complementary and do not substitute for each other.