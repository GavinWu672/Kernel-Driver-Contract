/*
 * KD-007 COMPLIANT: DPC routine uses only non-blocking operations.
 *
 * Queues work to a work item for any operation that requires
 * lower IRQL (file I/O, waits, pageable memory).
 */

#include <ntddk.h>

typedef struct _DPC_WORK_ITEM {
    PIO_WORKITEM WorkItem;
    ULONG        Argument;
} DPC_WORK_ITEM, *PDPC_WORK_ITEM;

IO_WORKITEM_ROUTINE SafeWorkItemCallback;

VOID SafeWorkItemCallback(
    _In_     PDEVICE_OBJECT DeviceObject,
    _In_opt_ PVOID          Context
)
{
    PDPC_WORK_ITEM ctx = (PDPC_WORK_ITEM)Context;
    UNREFERENCED_PARAMETER(DeviceObject);
    /* Runs at PASSIVE_LEVEL — blocking / pageable ops are safe here */
    if (ctx) {
        IoFreeWorkItem(ctx->WorkItem);
        ExFreePoolWithTag(ctx, 'kwI ');
    }
}

VOID SafeDpcRoutine(
    _In_     PKDPC  Dpc,
    _In_opt_ PVOID  DeferredContext,
    _In_opt_ PVOID  SystemArgument1,
    _In_opt_ PVOID  SystemArgument2
)
{
    PDEVICE_OBJECT  devObj = (PDEVICE_OBJECT)DeferredContext;
    PDPC_WORK_ITEM  ctx;

    UNREFERENCED_PARAMETER(Dpc);
    UNREFERENCED_PARAMETER(SystemArgument1);
    UNREFERENCED_PARAMETER(SystemArgument2);

    /* Compliant: allocate non-paged, queue work item, return immediately */
    ctx = (PDPC_WORK_ITEM)ExAllocatePool2(
        POOL_FLAG_NON_PAGED, sizeof(DPC_WORK_ITEM), 'kwI ');
    if (!ctx) return;

    ctx->WorkItem = IoAllocateWorkItem(devObj);
    if (!ctx->WorkItem) {
        ExFreePoolWithTag(ctx, 'kwI ');
        return;
    }
    IoQueueWorkItem(ctx->WorkItem, SafeWorkItemCallback, DelayedWorkQueue, ctx);
}
