NTSTATUS DriverDispatch(_In_ PDEVICE_OBJECT DeviceObject, _Inout_ PIRP Irp) {
    UNREFERENCED_PARAMETER(DeviceObject);
    KeWaitForSingleObject(&g_Event, Executive, KernelMode, FALSE, NULL);
    return STATUS_SUCCESS;
}
