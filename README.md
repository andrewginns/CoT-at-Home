# CoT at Home

This project provides an OpenAI-compatible API proxy that automatically adds Chain-of-Thought (CoT) reasoning, allowing you transparently add CoT to your use of any models.

```mermaid
flowchart LR
    A1([User Input]) --> CoT --> G1([Call API for Final Answer])

    subgraph CoT["Chain of Thought"]
        direction TB
        B1([FastAPI Receives Request]) --> C1([Modify Input with CoT Prompt])
        C1 --> D1([Call API for Thought Process])
        D1 --> E1([Receive and Analyze Thought Process])
        E1 --> F1([Create Input from Thoughts + User Input])
    end
    
    G1 --> H1([Return Final Answer to User])

    %% Styling
    style A1 fill:#f9f,stroke:#333,stroke-width:2px;
    style B1 fill:#bbf,stroke:#333,stroke-width:2px;
    style C1 fill:#bbf,stroke:#333,stroke-width:2px;
    style D1 fill:#bbf,stroke:#333,stroke-width:2px;
    style E1 fill:#bbf,stroke:#333,stroke-width:2px;
    style F1 fill:#bbf,stroke:#333,stroke-width:2px;
    style G1 fill:#f9f,stroke:#333,stroke-width:2px;
    style H1 fill:#f9f,stroke:#333,stroke-width:2px;

    classDef inputClass fill:#f9f,stroke:#333,stroke-width:2px;
    classDef cotClass fill:#bbf,stroke:#333,stroke-width:2px;
```

## Getting Started

### Prerequisites

Required:
   * An [OpenAI Compatible Endpoint](https://platform.openai.com/docs/api-reference/chat/create)
      * An API key (set in `.env` file as `OPENAI_API_KEY`)
      * Your API base URL (set in `.env` file as `OPENAI_API_BASE`) e.g.:
         * OpenAI: https://api.openai.com/v1
         * Azure: https://models.inference.ai.azure.com
         * VertexAI: https://us-central1-aiplatform.googleapis.com/v1beta1/projects/gcloud_project_id/locations/us-central1/endpoints/openapi

Optional:
   * Docker
      * To run without Docker install the `poetry` environment and run the `cot.py` script
   * Make
      * Only used to simplify Docker build and run


### Setup

1. **Clone the repository:**

   ```bash
   git clone <repository_url>
   cd cot_at_home
   ```

2. Create an .env file:

   ```bash
   echo "OPENAI_API_KEY=<your_openai_api_key>" > .env
   echo "OPENAI_API_BASE=<your_openai_api_base_url>" >> .env
   ```

3. Build and run the Docker image:

   ```bash
   make
   ```
   Starts the container on `localhost:5001`, point your application at this instead of your normal `OPENAI_API_BASE`.
   * Optionally change the port from the default `5001` to your choice
      ```bash
      make PORT=8080
      ```


4. Interact with the API:

   You can use the provided oai.py script or any OpenAI-compatible client to send requests to the API. Make sure to adjust the base_url in your client to http://localhost:5001.


## Makefile Commands

1. make all (default): Builds the Docker image and runs the container

2. make build: Builds the Docker image

3. make run: Runs the container, exposing the API on the specified port

## Notes
The API currently supports the /chat/completions endpoint for chat-based interactions.

The cot.py script acts as a proxy, forwarding requests to the actual OpenAI API while adding CoT reasoning capabilities.

Make sure to set the required environment variables in your .env file.

You can customize the port by modifying the PORT variable in the Makefile.

### Initial Architecture
```mermaid
graph TD
    A1[POST request to localhost] -->|API Call to /chat/completions| B1[FastAPI Endpoint]
    
    B1 -->|Extract user message| C1[Capture User Request]
    C1 -->|Prepare Prompt| D1[Modify 1st Message]
    
    subgraph First API Call
        D1 -->|Send Modified Message| E1[call_actual_openai_endpoint - 1st Call]
        E1 --> F1[Receive Thought Process]
        F1 --> G1[Extract Thought Process]
    end
    
    G1 -->|Prepare Refined Request| H1[Modify 2nd Message]
    
    subgraph Second API Call
        H1 -->|Send Refined Message| E2[call_actual_openai_endpoint - 2nd Call]
        E2 --> F2[Receive Final Answer]
    end

    F2 -->|Return Final Answer| I1[Final Response to User]
    
    F2 -->|If Streaming Enabled| I2[Streaming Response with Tokens]
    
    subgraph Error Handling
        B1 -.-> J1[Try-Except Block for Errors]
    end
```

## Acknowledgements

Thanks to https://github.com/antibitcoin/ReflectionAnyLLM/tree/main for the prompts