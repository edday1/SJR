# Define a timestamp function
timestamp() {
  date +"%T" # current time
}

# for each pubsub subscription seek it to now which acks all existing messages.
for sub in "sub_controller_start" "sub_pipeline_start" "sub_pipeline_end" "sub_downloader_start" "sub_downloader_end" "sub_annotator_start" "sub_annotator_end" "sub_error"
do
    export NOW=$(timestamp)
    gcloud pubsub subscriptions seek $sub --time=${NOW}
done