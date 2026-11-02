# Saving tailored resumes to Google Drive (optional)

When `google_drive_folder_url` is set, the coordinator uploads each day's tailored resumes
(.pdf + .docx) to that folder, in a subfolder `Tailored_Resumes_<YYYY-MM-DD>`, so you can open them
from your phone. Leave it empty to skip this; the resumes are still emailed to you as attachments.

Create a folder in Drive (for example "Job Hunt"), open it, and copy the URL from the address bar.

## How the agent uploads

1. **Stage** the files from your Mac into its workspace with `device_stage_files`.
2. **Open Drive** in Chrome through Claude in Chrome, check the signed-in Google account is yours,
   and open (or create once) the dated subfolder.
3. **Upload**: it adds a temporary `<input type=file>` to the page, puts the staged files in it
   (`file_upload`), and on its `change` event dispatches `dragenter`, `dragover`, `drop` with those
   files on the file list. Drive handles it like a normal drag-and-drop.
4. **Verify**: reload, check each file name appears exactly once, remove the input, close the tab.

## Guardrails

- Only creates folders and uploads files inside your configured folder. Never deletes, moves,
  renames or shares anything, and never changes sharing settings.
- Never uploads files containing passwords, ID numbers or salary slips.
- Skips a file that's already there.
- If Chrome is closed or Google is signed out, it skips the upload, keeps the email attachments,
  and logs "Drive upload skipped" on the board.

## Why not the Drive API?

It reuses your own signed-in browser session, so there's no OAuth app to register and no token to
store anywhere.
