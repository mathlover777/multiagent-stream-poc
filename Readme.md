## Demo

Check out the demo video below:


https://github.com/user-attachments/assets/a77bc953-1145-43d6-8e0f-d8726122cfff



# Multi-agent Chat Streaming with tool use with FastAPI

This repository extends the [OpenAI Cookbook example](https://cookbook.openai.com/examples/orchestrating_agents) by adding streaming functionality. It also demonstrates how to expose the chat system via FastAPI, enabling seamless Server-Sent Events (SSE) integration for clients.

## Features

- **Streaming Chat Responses**: Provides real-time updates for chat messages.
- **Extendable Architecture**: Includes an abstract base class for easy customization.
- **MongoDB Integration**: Offers an implementation to store message history in MongoDB.
- **FastAPI Ready**: Simple to build additional features like authentication.

## Getting Started

### Prerequisites

1. **Environment Variables**:
   - Define the required environment variables in a `.env.dev` file. Ensure they are correctly configured for your setup.
2. **MongoDB**:
   - Use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) for a free instance or any MongoDB server for message storage. You can use any other memory also, but then you need to extend the code accordingly. I have described this in Architecture.

### Running the Application
-  Set up the `.env.dev` file with necessary variables (e.g., database credentials, API keys, etc
- Build the application with Docker
```bash
docker compose --env-file .env.dev --profile fastapi_chat build
```
- Start the application with Docker
```bash
docker compose --env-file .env.dev --profile fastapi_chat up
```
## Architecture
#### `chat_streamer.py`

The `BaseMultiAgentChatStreamer` class is the core component of this implementation. It handles:

-   **Chat Streaming**: Real-time message updates.
-   **Agent Transfers**: Orchestration between agents.
-   **Tool Calls**: Interaction with external tools.

This abstract class defines the following methods:

-   `get_message_history`: Fetches the chat history for a session.
-   `append_messages`: Appends new messages to the chat history.

You must implement these methods according to your storage requirements. For simplicity, an in-memory implementation is also possible.

#### `ChatStreamMongoMemory`

The `ChatStreamMongoMemory` class provides an implementation using MongoDB for storage. This leverages MongoDB to:

-   Store chat history persistently.
-   Enable robust message retrieval and updates.

To use this, configure your MongoDB connection in the environment variables.

## Customization

This project is designed for easy extension:

-   **Authentication**: You can add an authentication layer directly in FastAPI.
-   **Storage**: Replace the MongoDB implementation with any other storage solution (e.g., Redis, PostgreSQL, or in-memory storage).
-   **Agent Customization**: Extend the `BaseMultiAgentChatStreamer` to fit your specific use case.
## Notes

-   The repository assumes basic familiarity with Docker, FastAPI, and MongoDB.
-   MongoDB Atlas provides an excellent free-tier service for quick setup and scaling.
