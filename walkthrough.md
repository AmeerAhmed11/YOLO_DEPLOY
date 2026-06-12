# Lightning AI Deployment Walkthrough

The deployment files are now ready! I've set everything up in a new directory so it won't conflict with your previous GCP deployment.

## What Was Created

All files are located in `c:\Users\Ameer\YOLO_Deploy\lightning_deploy`:

1. `requirements.txt`: Contains all the dependencies (`litserve`, `ultralytics`, `tensorrt`).
2. `server.py`: The LitServe API code. It uses the `ultralytics` library which has native support for TensorRT, meaning it will automatically handle loading the `.engine` file and running inference on the GPU with full hardware acceleration.
3. `deploy.sh`: A simple script containing the `lightning deploy` command.
4. `best.engine`: I've copied your TensorRT model file into this directory.

## Next Steps

> [!IMPORTANT]
> The `lightning` CLI tool is specifically designed to be run from inside **Lightning AI Studio** or an environment where you are logged in to Lightning AI. 

To deploy this, you should:

### 1. Upload to Lightning AI Studio
If you aren't already working in a Lightning Studio that is synced to this folder, upload the entire `lightning_deploy` folder to your Studio environment in your web browser.

### 2. Test Locally in Studio (Optional)
Before deploying to the cloud, it's good practice to ensure everything loads correctly in the studio environment.
Open a terminal in your Studio and run:
```bash
cd lightning_deploy
pip install -r requirements.txt
python server.py
```
This will start the LitServe API locally within the studio (typically on port 8000). You can verify it starts without errors.

### 3. Deploy to Lightning Cloud
Once you are ready to deploy the serverless endpoint, run:
```bash
bash deploy.sh
```
*(Or simply run `lightning deploy server.py --cloud`)*

This command will package the app and give you a public URL that you can use to send requests to your YOLO model running on Lightning's GPUs!
