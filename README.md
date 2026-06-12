# 🚀 The Ultimate Beginner's Guide: Deploying Your YOLO AI Model

Welcome! If you have **zero programming experience**, you are in the right place. 
This guide will hold your hand step-by-step to take your AI model (`best.engine`) and turn it into a live, beautiful website on the internet using Google Cloud.

## 🛠️ What You Need First (The "Ingredients")

Before we start, we need to make sure your computer is ready. You need 3 things:

1. **A Google Cloud Account**: You need an account at [Google Cloud](https://cloud.google.com/). Make sure you have a project created (your project ID is `n8n11-470807`) and that you have added a credit card (billing enabled).
2. **Google Cloud CLI (`gcloud`)**: This is a tool that lets your computer talk to Google. [Download and install it here](https://cloud.google.com/sdk/docs/install).
3. **Docker Desktop**: This is a tool that packages your app into a secure "box" so it can be uploaded. [Download Docker Desktop here](https://www.docker.com/products/docker-desktop/) and make sure it is open and running on your computer.

---

## 🚦 Step 1: Log in to Google from your computer

Open your computer's command line tool (search for **PowerShell** on Windows, or **Terminal** on Mac). Type this exact command, then press Enter:

```bash
gcloud auth login
```

A browser window will pop up. Log in with your Google account and click "Allow". Your computer is now securely connected to Google Cloud!

Next, tell Google which project we are working on:
```bash
gcloud config set project n8n11-470807
```

---

## 📦 Step 2: Put the AI Model on the Internet

Right now, your AI model (`best.engine`) is just sitting on your computer. We need to upload it to a powerful Google server (called Vertex AI). 

Don't worry, we wrote an automated script that does all the heavy lifting for you!

1. Make sure your `best.engine` file is inside the `YOLO_Deploy` folder.
2. In your terminal, navigate to the deployment folder:
   ```bash
   cd c:\Users\Ameer\YOLO_Deploy\deploy
   ```
3. Run our magical setup script:
   ```bash
   ./setup_gcp.sh
   ```
   *(Note: If you are using Windows PowerShell and the above command doesn't work, run the Python version instead by typing: `python deploy_vertex.py`)*

⏳ **Wait 10 to 15 minutes.** Go grab a coffee! Google is building a secure home for your AI and spinning up a powerful graphics card (GPU) to run it.

When it finishes, you will see a message at the bottom saying **Endpoint ID:** followed by a long text (it looks like `projects/123.../locations/us-central1/endpoints/456...`). 

📝 **Copy that entire Endpoint ID and save it in a notepad! You need it for the next step.**

---

## 🌐 Step 3: Launch Your Website

Now that the AI is alive on Google, we need to launch the beautiful website (the "Frontend") so people can upload pictures and videos to it.

1. Still in your terminal, tell your computer your Endpoint ID from the previous step. Run this command (replace the placeholder with your actual Endpoint ID):
   
   **For Mac/Linux/Git Bash:**
   ```bash
   export VERTEX_ENDPOINT_ID="projects/47162042628/locations/us-central1/endpoints/55758983423590400"
   ```
   **For Windows PowerShell:**
   ```powershell
   $env:VERTEX_ENDPOINT_ID="projects/47162042628/locations/us-central1/endpoints/55758983423590400"
   ```

2. Run the website launcher script:
   ```bash
   ./deploy_cloudrun.sh
   ```

⏳ **Wait about 2 minutes.** 
When it finishes, it will print out a public website URL (it will look something like `https://yolo-frontend-xxxxx-uc.a.run.app`). 

🎉 **Congratulations!** Click that link. Your AI object detection website is now live on the internet for anyone to use!

---

## 💰 Important Note About Money & Speed

We configured your AI to be **Scale-to-Zero**. 
What does this mean? 
- If nobody is using your website, the powerful GPU turns off. **You pay $0 when it sleeps.**
- When you open the website and click "Run Inference" for the very first time after it has been sleeping, the GPU has to "wake up". **This wake-up process takes about 5 to 10 minutes.** Don't panic if it's spinning for a long time on the first try!
- After it wakes up, any new pictures you upload will process instantly (in milliseconds).

---

## 🚨 Troubleshooting (If things go wrong)

**Error: "Docker is not running"**
Make sure Docker Desktop is open. You should see a little whale icon in your system tray (bottom right of your screen).

**Error: "Permission Denied"**
Make sure you ran `gcloud auth login` and used the correct Google account that owns the `n8n11-470807` project.

**Error: "Command not found" for ./setup_gcp.sh**
Windows sometimes struggles with `.sh` files. If this happens, just make sure Python is installed and run `python deploy_vertex.py` instead.
