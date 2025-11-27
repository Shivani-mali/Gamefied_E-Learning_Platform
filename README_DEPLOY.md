Deployment instructions

This file explains how to deploy this Flask app to a free host (Render or Railway) and how to set the `MONGODB_URI` environment variable to point to either a local MongoDB or MongoDB Atlas.

1) Prepare repository
- From your project folder (`D:\Mini_Project`) run:

```bash
git init
git add .
git commit -m "Prepare app for deployment"
```

- Create a GitHub repo and add it as `origin` (replace URL):

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

2) Ensure `requirements.txt` includes these (already updated):
- Flask
- pymongo
- Werkzeug
- gunicorn
- python-dotenv

3) Render.com (quick deploy)
- Sign in at https://render.com and click `New` → `Web Service`.
- Connect your GitHub account and select the repository.
- Set the build command (Render detects Python automatically). Start command: `gunicorn app:app`
- Add environment variables in the Render dashboard → `Environment`:
  - `MONGODB_URI` = your MongoDB connection string (Atlas or other)
- Click `Create Web Service` and wait for deploy.

4) Railway.app (quick deploy)
- Sign in at https://railway.app, create a new project and choose `Deploy from GitHub`.
- Connect the repo, then add an `Environment Variable` named `MONGODB_URI` with your connection string.
- Start the deployment and note the public URL.

5) Local testing using `.env` (optional)
- Create a `.env` with:
```
MONGODB_URI=mongodb://localhost:27017/?directConnection=true
```
- Install python-dotenv (already in `requirements.txt`). You can load `.env` yourself, or run via your shell and start the app.

6) Post-deploy checks
- Visit your deployed URL: `https://<your-service>.onrender.com` or Railway URL.
- Use MongoDB Compass (Atlas or local) to verify the `users` collection in the database contains the created users.

If you'd like, I can:
- Create the Git commit for you and show the exact `git` commands to run locally.
- Walk through the Render deployment UI step-by-step.
