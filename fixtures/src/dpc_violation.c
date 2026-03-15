/*
 * KD-007 VIOLATION: Blocking API called inside a DPC routine.
 *
 * DPC routines (KDEFERRED_ROUTINE) run at DISPATCH_LEVEL.
 * KeWaitForSingleObject is a synchronous wait that requires <= APC_LEVEL.
 * Calling it here will bugcheck with IRQL_NOT_LESS_OR_EQUAL.
 */

#include <ntddk.h>

KEVENT g_CompletionEvent;

VOID BadDpcRoutine(
    _In_     PKDPC  Dpc,
    _In_opt_ PVOID  DeferredContext,
    _In_opt_ PVOID  SystemArgument1,
    _In_opt_ PVOID  SystemArgument2
)
{
    UNREFERENCED_PARAMETER(Dpc);
    UNREFERENCED_PARAMETER(DeferredContext);
    UNREFERENCED_PARAMETER(SystemArgument1);
    UNREFERENCED_PARAMETER(SystemArgument2);

    /* VIOLATION: blocking wait inside KDEFERRED_ROUTINE (DISPATCH_LEVEL) */
    KeWaitForSingleObject(&g_CompletionEvent, Executive, KernelMode, FALSE, NULL);
}
