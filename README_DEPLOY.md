Deployment instructions

This file explains how to deploy this Flask app to a free host (Render or Railway) and how to set the database connection string.

Important: the app accepts either `MONGO_URI` or `MONGODB_URI`. Use one of them (they are equivalent here).

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

2) Ensure `requirements.txt` includes these (already updated and pinned):
- Flask==3.1.2
- pymongo==4.15.4
- Werkzeug==3.1.3
- gunicorn==23.0.0
- python-dotenv==1.2.1

3) Render.com (quick deploy)
- Sign in at https://render.com and click `New` → `Web Service`.
- Connect your GitHub account and select the repository.
- Set the build command (Render detects Python automatically). Start command: `gunicorn app:app`
- Add environment variables in the Render dashboard → `Environment`:
  - `MONGO_URI` (or `MONGODB_URI`) = your MongoDB connection string (Atlas or other)
  - `SECRET_KEY` = any long random string
- Click `Create Web Service` and wait for deploy.

4) Railway.app (quick deploy)
- Sign in at https://railway.app, create a new project and choose `Deploy from GitHub`.
- Connect the repo, then add environment variables:
  - `MONGO_URI` (or `MONGODB_URI`) with your connection string.
  - `SECRET_KEY` with a long random string.
- Start the deployment and note the public URL.

5) Local testing using `.env` (optional)
- Create a `.env` with:
```
MONGO_URI=mongodb://localhost:27017/?directConnection=true
SECRET_KEY=replace-with-a-random-string
```
- Install python-dotenv (already in `requirements.txt`). You can load `.env` yourself, or run via your shell and start the app.

6) Post-deploy checks
- Visit your deployed URL: `https://<your-service>.onrender.com` or Railway URL.
- Use MongoDB Compass (Atlas or local) to verify the `users` collection in the database contains the created users.

If you'd like, I can:
- Create the Git commit for you and show the exact `git` commands to run locally.
- Walk through the Render deployment UI step-by-step.
