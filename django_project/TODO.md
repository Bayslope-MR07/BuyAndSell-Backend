# TODO: Fix Blank Embedded Excel Files in upload_excel View

## Completed Tasks
- [x] Update `is_valid_excel` function to improve logging (changed log to show number of non-empty cells instead of last cell value)
- [x] Modify `save_embedded_to_seller` function to only save Excel files that contain actual data (added check using `_excel_has_data` before saving)
- [x] Test the upload process with a sample Excel file (Bay_Portfolio analysis_Marc.xlsx) - verified improved logging and successful saving of embedded files with data
- [x] Check logs for improved debugging information (now shows number of non-empty cells)
- [x] Verify that valid embedded files are still saved correctly (PDF and Excel with 1004 cells saved successfully)

## Completed Tasks
- [x] Modified `save_embedded_to_seller` to resave extracted embedded Excel files using openpyxl (to ensure proper format and data preservation)
- [x] Test the upload process with multiple Excel files - confirmed that embedded Excel files with 240 and 1004 non-empty cells are resaved successfully and accessible in UI (HTTP 200 for media files)
- [x] Maintain functionality for PDF and other embedded files
- [x] Verify embedded files are visible and downloadable in the UI
- [x] Confirm the fix preserves the original data in embedded Excel files by resaving in standard format
