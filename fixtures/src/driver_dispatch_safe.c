NTSTATUS DriverDispatch(_In_ PDEVICE_OBJECT DeviceObject, _Inout_ PIRP Irp) {
    UNREFERENCED_PARAMETER(DeviceObject);
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return STATUS_SUCCESS;
}
