PVOID AllocateBuffer(SIZE_T Length) {
    UNREFERENCED_PARAMETER(Length);
    return ExAllocatePool2(POOL_FLAG_NON_PAGED, Length, 'buf2');
}
