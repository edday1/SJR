%%{
init: {
    'theme': 'base',
    'themeVariables': {
        'background': '#fff',
        'primaryColor': '#BB2528',
        'primaryTextColor': '#fff',
        'primaryBorderColor': '#7C0000',
        'lineColor': '#F8B229',
        'secondaryColor': '#006100',
        'tertiaryColor': '#fff'
    }
}
}%%
sequenceDiagram
    participant Hogarth
    participant Gateway
    participant Endpoints
    participant Controller
    participant Downloader
    participant GCS
    participant Annotator
    participant Output
    %% Setup
    Hogarth ->> Gateway: annotation_request
    Gateway ->> Endpoints: annotation_request
    Endpoints -->> Gateway: 201 success
    Gateway -->> Hogarth: 201 success

    %% Annotator initialise
    Endpoints ->> Controller: annotator_start
    Note over Endpoints, Controller: PubSub
    Controller ->> Downloader: downloader_start
    Note over Controller, Downloader: PubSub
    Note right of Downloader: Download the image
    Downloader ->> Hogarth: Request image download
    Hogarth -->> Downloader: Success download
    Note right of Downloader: Store the image
    Downloader ->> GCS: Store image data
    Downloader ->> Controller: downloader_end
    Note over Downloader, Controller: PubSub

    %% Execute Annotator
    Controller ->> Annotator: Annotator_start
    Note over Controller, Annotator: PubSub
    Annotator ->> GCS: Load image
    GCS -->> Annotator: Success
    Note right of Annotator: annotationJob
    Annotator ->> GCS: Store annotations
    Annotator ->> Output: Annotator_end
    Note over Annotator, Output: PubSub
    Output ->> Output: Construct response
    Output ->> Hogarth: POST results
