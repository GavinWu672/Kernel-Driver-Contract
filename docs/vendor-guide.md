# Kernel Driver Contract — Vendor Integration Guide
# Kernel Driver Contract — 廠商整合指南

> Version: 1.0 — 2026-03-16
> Scope: KMDF-first v1

---

## 1. What This Tool Is (and Is Not)
## 1. 這個工具是什麼（以及不是什麼）

**English**

Kernel Driver Contract is a **pre-merge static pattern checker** for Windows kernel driver source code. It scans `.c`/`.h` files, classifies callback functions by IRQL context, and enforces a set of hard-stop rules that correspond to a subset of Windows Driver Kit (WDK) requirements.

It operates **before** build-time analysis tools (PREfast / Code Analysis) and **before** Static Driver Verifier (SDV). It does not replace Driver Verifier, SDV, or the Windows Hardware Lab Kit (HLK). Its value is catching a well-defined set of violations at the lowest-cost point — before a change is merged.

Passing all checks in this tool does **not** indicate WHQL/WHCP readiness. Driver Verifier runtime checks, SDV rule sets, and HLK certification remain required and are outside this tool's scope.

**中文**

Kernel Driver Contract 是一個針對 Windows kernel driver 原始碼的 **pre-merge 靜態 pattern checker**。它掃描 `.c`/`.h` 檔案，依 IRQL 上下文分類 callback function，並執行一組對應部分 WDK 要求的 hard-stop 規則。

它運行在 build-time 靜態分析工具（PREfast / Code Analysis）**之前**，也在 Static Driver Verifier（SDV）**之前**。它不取代 Driver Verifier、SDV 或 Windows Hardware Lab Kit（HLK）。其價值在於以最低成本——在 merge 之前——攔截一組明確定義的違規。

通過本工具的所有檢查，**不代表** WHQL/WHCP 認證就緒。Driver Verifier runtime 檢查、SDV 規則集與 HLK 認證仍然是必要的，不在本工具的涵蓋範圍內。

---

## 2. Prerequisites
## 2. 前提條件

**English**

- Python 3.10 or later
- Driver source is KMDF-based (`EVT_WDF_*` callbacks). WDM drivers using function-pointer cast registration (`MajorFunction[]`, `PI8042_KEYBOARD_ISR` casts) are a known v1 structural limitation — see Section 5.
- No external dependencies required beyond the Python standard library.

**中文**

- Python 3.10 或更新版本
- Driver 原始碼基於 KMDF（使用 `EVT_WDF_*` callbacks）。使用 function-pointer cast 注冊的 WDM driver（`MajorFunction[]`、`PI8042_KEYBOARD_ISR` cast 等）是已知的 v1 結構性限制——見第 5 節。
- 除 Python 標準函式庫外，不需要外部相依套件。

---

## 3. Running the Tool
## 3. 執行工具

**English**

**Step 1 — Scan source files**

```bash
python scan_source.py path/to/your/driver/ --output-dir out/
```

Produces one `.checks.json` per `.c` file in `out/`. Pass a single file or a directory.

**Step 2 — Run validators**

```bash
python run_validators.py out/
```

**Step 3 — (Optional) Install pre-commit hook**

To block commits automatically on hard-stop violations:

```bash
bash scripts/install-hooks.sh
```

**中文**

**第一步 — 掃描原始碼**

```bash
python scan_source.py path/to/your/driver/ --output-dir out/
```

對 `out/` 下每個 `.c` 檔案產生一個 `.checks.json`。可傳入單一檔案或目錄。

**第二步 — 執行驗證器**

```bash
python run_validators.py out/
```

**第三步 — （選用）安裝 pre-commit hook**

如需在 commit 時自動攔截 hard-stop 違規：

```bash
bash scripts/install-hooks.sh
```

---

## 4. Interpreting Results
## 4. 解讀結果

**English**

Each file produces one of three outcomes:

| Result | Meaning | Recommended action |
|--------|---------|-------------------|
| `PASS` | No violations detected | No action required |
| `ADVISORY` | Potential issue flagged; informational only | Review and document if intentional |
| `HARD-STOP` | Violation of a hard rule | Investigate and fix before merging |

Hard-stop rules enforced:

| Rule ID | What it catches |
|---------|----------------|
| KD-002 | IRQL-unsafe API called in ISR / DPC / dispatch context (e.g. `KeWaitForSingleObject`, `ZwCreateFile`) |
| KD-003 | Wrong pool type for IRQL context (e.g. `ExAllocatePoolWithTag(PagedPool,...)` in DPC) |
| KD-006 | Spinlock acquire–release imbalance within a function |
| KD-007 | Blocking call or `WdfRequestSend` while spinlock held |
| KD-010 | Static analysis diagnostic present in payload |

Advisory rules (do not block merge, but should be reviewed):

| Rule ID | What it checks |
|---------|----------------|
| KD-001 | IRQL-sensitive API usage (informational) |
| KD-004–005 | Pool allocation patterns |
| KD-008 | `PAGED_CODE()` annotation discipline |
| KD-009 | Required IRP major function handler presence |

**中文**

每個檔案的結果為以下三種之一：

| 結果 | 意義 | 建議行動 |
|------|------|----------|
| `PASS` | 未偵測到違規 | 不需要任何動作 |
| `ADVISORY` | 標記潛在問題，僅供參考 | 如為刻意設計，審查並記錄 |
| `HARD-STOP` | 違反 hard rule | 在 merge 前調查並修復 |

Hard-stop 規則：

| Rule ID | 偵測內容 |
|---------|----------|
| KD-002 | 在 ISR / DPC / dispatch context 呼叫 IRQL-unsafe API（如 `KeWaitForSingleObject`、`ZwCreateFile`） |
| KD-003 | IRQL context 與 pool type 不符（如在 DPC 中使用 `ExAllocatePoolWithTag(PagedPool,...)`） |
| KD-006 | 函式內 spinlock acquire–release 不對稱 |
| KD-007 | 持有 spinlock 時呼叫 blocking API 或 `WdfRequestSend` |
| KD-010 | payload 中存在靜態分析診斷訊息 |

Advisory 規則（不阻擋 merge，但應審查）：

| Rule ID | 檢查內容 |
|---------|----------|
| KD-001 | IRQL-sensitive API 使用狀況（僅供參考） |
| KD-004–005 | Pool allocation 模式 |
| KD-008 | `PAGED_CODE()` annotation 紀律 |
| KD-009 | 必要的 IRP major function handler 是否存在 |

---

## 5. Known Limitations
## 5. 已知限制

**English**

**v1 scope: KMDF-first.** The tool is validated against KMDF drivers using `EVT_WDF_*` callback registration. Two structural limitations apply in v1:

**Limitation 1 — WDM function-pointer cast registration (High / accepted)**

Callbacks registered via `MajorFunction[]` array assignment, `PI8042_KEYBOARD_ISR` cast, `PSERVICE_CALLBACK_ROUTINE`, or similar WDM patterns are not detectable by the current header-file registry approach. These functions will be classified as `other` rather than their correct role (`dispatch`, `isr`, `dpc`), causing false negatives — violations in those functions will not be caught.

*Impact on your driver:* If your driver uses WDM function-pointer registration, do not rely on this tool for those callbacks in v1. KMDF `EVT_WDF_*` callbacks are not affected.

**Limitation 2 — Spinlock heuristic false positives in KMDF+NDIS-heritage drivers (Low / accepted)**

In drivers that mix KMDF callbacks with legacy NDIS-style explicit spinlock management, helper functions that are called with a spinlock held (but are not themselves dispatch-level callbacks) may be falsely classified as `dispatch`. This can cause spurious `ADVISORY` results.

*Impact on your driver:* If your driver uses framework-managed queue serialization (standard KMDF pattern), this limitation does not apply. If your driver uses explicit `KeAcquireSpinLock` / `WdfSpinLockAcquire` patterns for NDIS-heritage reasons, you may see false positives on helper functions. These will appear as `ADVISORY`, not `HARD-STOP`.

**中文**

**v1 範圍：KMDF-first。** 本工具針對使用 `EVT_WDF_*` callback 注冊的 KMDF driver 進行驗證。v1 存在兩個結構性限制：

**限制 1 — WDM function-pointer cast 注冊（高嚴重度 / 已接受）**

透過 `MajorFunction[]` 陣列賦值、`PI8042_KEYBOARD_ISR` cast、`PSERVICE_CALLBACK_ROUTINE` 或類似 WDM 模式注冊的 callback，目前的 header-file registry 方法無法偵測。這些函式將被分類為 `other` 而非正確的角色（`dispatch`、`isr`、`dpc`），導致 false negative——這些函式中的違規將不會被攔截。

*對您的 driver 的影響：* 若您的 driver 使用 WDM function-pointer 注冊，v1 請勿依賴本工具對這些 callback 的檢查。KMDF `EVT_WDF_*` callback 不受影響。

**限制 2 — KMDF+NDIS-heritage driver 中的 spinlock heuristic false positive（低嚴重度 / 已接受）**

在混用 KMDF callback 與 legacy NDIS-style 顯式 spinlock 管理的 driver 中，被持有 spinlock 的上下文呼叫的 helper function（本身並非 dispatch-level callback）可能被誤分類為 `dispatch`，導致偽陽性的 `ADVISORY` 結果。

*對您的 driver 的影響：* 若您的 driver 使用 framework-managed queue serialization（標準 KMDF 模式），此限制不適用。若您的 driver 因 NDIS-heritage 原因使用顯式 `KeAcquireSpinLock` / `WdfSpinLockAcquire` 模式，helper function 上可能出現 false positive，表現為 `ADVISORY`（不是 `HARD-STOP`）。

---

## 6. Handling Suspected False Positives
## 6. 處理疑似 False Positive

**English**

If a result looks incorrect, follow these steps before filing an issue:

1. **Check the callback classification.** Open the `.checks.json` for the flagged file. Look at `classified_functions` — confirm the function's role (`isr`, `dpc`, `dispatch`, `other`) matches your expectation.

2. **If the classification is wrong:** This is likely a WDM cast registration (Limitation 1). The function's EVT_WDF_* type declaration is not reachable by the scanner. This is a known v1 structural limitation — document it and exclude it from enforcement scope for that function.

3. **If the classification is correct but the flag looks wrong:** Check whether the function body contains `WdfSpinLockAcquire` / `KeAcquireSpinLock` or calls a function that acquires a spinlock. If yes, this may be a spinlock heuristic FP (Limitation 2). The result will be `ADVISORY`; review whether the usage is intentional.

4. **If neither explanation fits:** Record the function name, file, expected classification, actual classification, and the rule that fired. Report via the project issue tracker.

**中文**

若某個結果看起來不正確，在提交 issue 前請先執行以下步驟：

1. **確認 callback 分類。** 開啟被標記檔案的 `.checks.json`，查看 `classified_functions`——確認該函式的角色（`isr`、`dpc`、`dispatch`、`other`）是否符合預期。

2. **若分類錯誤：** 這很可能是 WDM cast 注冊（限制 1）。scanner 無法找到該函式的 `EVT_WDF_*` 型別宣告。這是已知的 v1 結構性限制——記錄下來，並將該函式排除於強制執行範圍之外。

3. **若分類正確但標記看起來不對：** 確認函式本體是否含有 `WdfSpinLockAcquire` / `KeAcquireSpinLock`，或呼叫了會 acquire spinlock 的函式。若是，這可能是 spinlock heuristic FP（限制 2）。結果將為 `ADVISORY`；審查該用法是否為刻意設計。

4. **若以上解釋均不適用：** 記錄函式名稱、檔案、預期分類、實際分類與觸發的規則，透過專案 issue tracker 回報。

---

## 7. Relationship to WHQL / WHCP
## 7. 與 WHQL / WHCP 的關係

**English**

This tool is a **pre-merge complement** to Microsoft's driver verification stack. It does not substitute for any certification requirement.

| Verification layer | Tool | This tool's role |
|-------------------|------|-----------------|
| Build-time static analysis | WDK PREfast / Code Analysis | Complementary — catches a subset earlier |
| Deep static verification | Static Driver Verifier (SDV) | Complementary — SDV remains required |
| Runtime verification | Driver Verifier (DV) | Not applicable — different layer |
| Certification | HLK / WHCP | Not applicable — certification requires hardware testing and runtime DV |

Passing this tool's checks reduces the probability of DV DDI Compliance failures, but does not guarantee DV or HLK passage.

For the detailed rule-by-rule traceability mapping, see [`docs/microsoft-standards-mapping.md`](microsoft-standards-mapping.md).

**中文**

本工具是 Microsoft driver 驗證工具鏈的 **pre-merge 補充**，不替代任何認證要求。

| 驗證層 | 工具 | 本工具的角色 |
|--------|------|-------------|
| Build-time 靜態分析 | WDK PREfast / Code Analysis | 互補——提前攔截部分問題 |
| 深度靜態驗證 | Static Driver Verifier（SDV） | 互補——SDV 仍為必要 |
| Runtime 驗證 | Driver Verifier（DV） | 不適用——不同層次 |
| 認證 | HLK / WHCP | 不適用——認證需要硬體測試與 runtime DV |

通過本工具的檢查能降低 DV DDI Compliance 失敗的概率，但不保證 DV 或 HLK 通過。

規則對應的詳細 traceability mapping，請參閱 [`docs/microsoft-standards-mapping.md`](microsoft-standards-mapping.md)。
