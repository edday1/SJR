import time
import subprocess

bash_script = """
timestamp() {
  date +"%T" # current time
}

for sub in "sub_controller_start" "sub_pipeline_start" "sub_pipeline_end" "sub_downloader_start" "sub_downloader_end" "sub_annotator_start" "sub_annotator_end" "sub_error"
do
    export NOW=$(timestamp)
    gcloud pubsub subscriptions seek $sub --time=${NOW}
done
"""

while True:
    subprocess.run(bash_script, shell=True)
    time.sleep(60)  # 1 minute