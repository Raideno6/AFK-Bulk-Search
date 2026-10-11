# AFK TCG Searcher

## Run locally

Start the FastAPI backend in one terminal from the repository root:

```powershell
python "React App\Backend\main.py"
```

Then start the frontend in a second terminal:

```powershell
Set-Location "React App\frontend"
npm run dev
```

The Vite development server proxies `/search` and `/api/data` to the backend at `http://127.0.0.1:8000`. On backend startup, the server loads the compressed card price dataset once into a shared lookup used by all searches. The page checks that the shared data is ready when it loads, and the `SEARCH` button sends the text box contents as JSON in the `text` field. Keep the backend terminal running while using the page.
