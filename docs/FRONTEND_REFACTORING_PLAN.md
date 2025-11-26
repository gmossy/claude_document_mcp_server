# Frontend Refactoring Implementation Plan

## Critical Changes to Implement

### 1. Remove `loadAllDocuments()` Function
- **Location:** Lines 52-115
- **Action:** Delete entire function
- **Impact:** Eliminates loading all documents into memory

### 2. Remove `allDocuments` State
- **Location:** Line 28
- **Action:** Remove `const [allDocuments, setAllDocuments] = useState([]);`
- **Impact:** Reduces memory usage

### 3. Update `loadDocuments()` Function
- **Location:** Lines 117-343
- **Changes:**
  - Remove call to `loadAllDocuments()` (line 323)
  - Remove `setAllDocuments()` calls (line 187)
  - For search: Limit to pageSize instead of 1000, use server-side pagination
  - Apply minimal client-side filtering only on current page results (not all documents)

### 4. Update Statistics Calculation
- **Location:** Lines 665-707
- **Changes:**
  - Remove dependency on `allDocuments`
  - Calculate from current `documents` array only
  - Or fetch counts from API if available

### 5. Implement Proper Debouncing
- **Location:** Lines 345-360
- **Changes:**
  - Use AbortController to cancel in-flight requests
  - Use debounce utility function
  - Proper cleanup

### 6. Add Memoization
- **Add useMemo for:**
  - `formatDocument()` results
  - `displayDocuments` calculation
  - Statistics calculations
- **Add useCallback for:**
  - Event handlers
  - `loadDocuments` function

### 7. Use Utility Functions
- Replace error extraction code with `extractErrorMessage()` utility
- Use `debounce()` utility function

## Implementation Order

1. ✅ Create utility functions (DONE)
2. Remove `loadAllDocuments()` and `allDocuments` state
3. Refactor `loadDocuments()` to use server-side filtering
4. Update statistics to not depend on `allDocuments`
5. Implement proper debouncing with AbortController
6. Add memoization hooks
7. Replace error handling with utility function

