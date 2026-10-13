# AgriSense Admin Dashboard

This branch is a static GitHub Pages deployment for the AgriSense admin dashboard.

Before deploying, edit `config.js` and set `API_BASE_URL` to the HTTPS URL of the
separately deployed API from the `backend` branch. Add this GitHub Pages origin to
the backend `CORS_ORIGINS` value. Do not add API keys, backend `.env` files, or
agricultural knowledge data to this branch.
