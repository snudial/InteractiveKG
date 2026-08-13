# InteractiveKG: Transparent and User-Controllable Knowledge Graph Reasoning

> InteractiveKG is a visual analytics system that externalizes LLM-generated
> reasoning as persistent, editable knowledge graphs, enabling users to inspect,
> correct, and iteratively refine the reasoning process.

**Information Visualization, 2026**

[Paper](https://doi.org/10.1177/14738716261435574) · [Citation](#citation)

## Overview

Large Language Models (LLMs) are increasingly used to support complex reasoning tasks, yet their fluent textual explanations often obscure underlying assumptions and intermediate reasoning steps, making it difficult for users to verify correctness or confidently rely on the results. InteractiveKG addresses this gap by externalizing LLM-generated reasoning as persistent, editable knowledge graphs, enabling users to inspect, correct, and iteratively refine reasoning by directly manipulating nodes and edges, adjusting abstraction levels, and accessing contextual explanations within a unified human-in-the-loop workflow.

## Key Features

### 1. Visual Externalization of LLM Reasoning
- Transforms LLM-generated reasoning into interactive knowledge graphs
- Presents entities, relations, and inferred connections as node-link diagrams
- Enables users to examine the structure of reasoning processes beyond linear text

### 2. Interactive Graph Refinement
- Direct manipulation of nodes and edges for correction and refinement
- Support for adding, modifying, and removing graph elements
- Persistent storage of user edits in Neo4j database
- Edits directly influence subsequent model outputs

### 3. Hierarchical Abstraction
- Scalable abstraction mechanisms for graph sensemaking
- Community-based hierarchical abstraction using the Leiden algorithm, with
  LLM-generated semantic names for each community
- Four fixed abstraction levels for transitioning from detailed to global views
- Community View and Detailed View for complementary exploration

### 4. Context-Aware Node Explanation
- On-demand semantic and reasoning explanations for individual nodes
- Contextual interpretations based on local graph structure
- Integration with graph editing workflows for informed modifications

### 5. Dual Reasoning Modes
Both modes ground every LLM call in the current, user-inspected graph state; they differ
only in their write policy:
- **Intelligent Solving Mode**: uses the existing graph as context and may write newly
  extracted entities and relations back to the shared graph state
- **Internal Retrieval Mode**: read-only — generates responses based solely on the
  existing knowledge graph, so every claim can be traced back to a user-inspected structure

## Installation and Setup

### Step 1: Clone the Repository

```bash
git clone git@github.com:snudial/InteractiveKG.git
cd InteractiveKG/InteractiveKG
```

### Step 1b: Clone Knowledge Graph of Thoughts (optional, for the KGOT reasoning modes)

The Intelligent Solving / Internal Retrieval modes delegate to the external
[Knowledge Graph of Thoughts](https://github.com/spcl/knowledge-graph-of-thoughts) project,
which is not bundled with this repository. Clone it next to this repository (or anywhere,
and point `KGOT_PROJECT_ROOT` at it):

```bash
git clone https://github.com/spcl/knowledge-graph-of-thoughts.git
export KGOT_PROJECT_ROOT=/path/to/knowledge-graph-of-thoughts   # optional if cloned next to this repo
```

Without it, the rest of the system (graph editing, hierarchical abstraction, node
explanations) still works; only the KGOT reasoning endpoints are disabled.

### Step 2: Set Up Neo4j Database

#### Option A: Using Docker (Recommended)

```bash
# Start Neo4j using Docker Compose
docker-compose up -d neo4j
```

This will start Neo4j on:
- HTTP: `http://localhost:7474`
- Bolt: `bolt://localhost:7687`
- Default credentials: `neo4j/password123`

#### Option B: Using Local Neo4j Installation

If you have Neo4j installed locally, ensure it's running and update the connection settings in the backend environment variables.

### Step 3: Set Up Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a Python virtual environment (using Python 3.10 or 3.11):
```bash
# Using Python 3.10 (recommended)
python3.10 -m venv .venv310

# Or using Python 3.11
python3.11 -m venv .venv311
```

3. Activate the virtual environment:
```bash
# For Python 3.10
source .venv310/bin/activate

# For Python 3.11
source .venv311/bin/activate
```

4. Upgrade pip and install dependencies:
```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

5. Configure environment variables (optional):
Create a `.env` file in the `backend` directory:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
LLM_PROVIDER=openai_gpt4o_mini
LLM_MODEL_NAME=gpt-4o-mini-2024-07-18
LLM_API_KEY=your-api-key-here
# Optional: path to your knowledge-graph-of-thoughts checkout
# (defaults to a sibling directory of this repository)
KGOT_PROJECT_ROOT=/path/to/knowledge-graph-of-thoughts
```

### Step 4: Set Up Frontend

1. Navigate to the frontend directory:
```bash
cd ../frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure the backend URL (optional):

The frontend talks to the backend at `http://localhost:8000` by default. To point it
elsewhere, create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=http://your-backend-host:8000
```

## Running the Application

### Start Backend Server

1. Navigate to the backend directory:
```bash
cd backend
```

2. Activate the virtual environment:
```bash
source .venv310/bin/activate  # or .venv311 for Python 3.11
```

3. Start the FastAPI server:
```bash
# With hot-reload disabled (recommended for production-like testing)
DEBUG=false API_PORT=8000 python main.py

# Or with hot-reload enabled (for development)
python main.py
```

The backend will be available at `http://localhost:8000`

### Start Frontend Development Server

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Start the Next.js development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Quick Start Script

Alternatively, you can use the provided startup script:

```bash
bash start_chatbot_system.sh
```

**Note**: The script may need to be modified to use the correct Python version and virtual environment path.

## Access Points

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Neo4j Browser**: http://localhost:7474 (if using Docker)

## Usage Guide

### 1. Graph Visualization Operations

- **Zoom**: Mouse wheel
- **Pan**: Drag blank areas
- **Select**: Click on nodes or relationships
- **Edit**: Double-click nodes to open editing panel
- **Context Menu**: Right-click on nodes or relationships

### 2. Interactive Graph Editing

- **Create Node**: Use the toolbar to add new nodes
- **Create Relationship**: Select two nodes and specify their relationship
- **Insert Node**: Add a node along an existing relationship
- **Edit Properties**: Select elements and edit in the side panel
- **Delete**: Select elements and use delete button
- **Save**: Changes are automatically persisted to Neo4j

### 3. Hierarchical Abstraction

- Use the Hierarchical Analysis panel to adjust abstraction levels
- Switch between Community View (global overview) and Detailed View (all nodes)
- Drill down into communities for focused inspection

### 4. Node Explanations

- Double-click any node to view contextual explanations
- Explanations are generated based on the node's local graph context
- Use explanations to understand semantic meaning before editing

### 5. Reasoning Modes

- **Intelligent Solving**: Query the system to dynamically construct knowledge graphs
- **Internal Retrieval**: Generate responses based on existing knowledge graphs only

## Project Structure

```
InteractiveKG/                 # Repository root
└── InteractiveKG/             # Application
    ├── frontend/              # Next.js frontend application
    │   └── src/
    │       ├── app/           # Next.js app router pages
    │       ├── components/    # Graph, UI, and upload components
    │       ├── hooks/         # React hooks (e.g. highlight system)
    │       ├── lib/           # Backend API clients (api.ts, chatbot-api.ts)
    │       ├── styles/        # Global styles
    │       └── types/         # Shared TypeScript types
    ├── backend/               # FastAPI backend application
    │   ├── app/
    │   │   ├── api/           # KGOT and chatbot route handlers
    │   │   ├── config/        # LLM and cleanup configuration
    │   │   ├── database/      # Neo4j connection
    │   │   ├── models/        # Pydantic models
    │   │   ├── routers/       # Graph CRUD/analysis routes
    │   │   └── services/      # Graph, abstraction, KGOT, chatbot services
    │   ├── sample_data/       # Bundled study datasets
    │   ├── tests/             # Smoke tests (python -m pytest tests/)
    │   ├── main.py            # Application entry point
    │   └── requirements.txt   # Python dependencies
    ├── docker-compose.yml     # Docker configuration for Neo4j
    └── start_chatbot_system.sh  # Startup script

knowledge-graph-of-thoughts/   # External dependency, cloned separately (see Step 1b)
```

## Citation

If you use this system in your research, please cite:

> Kim, M., Zhao, Y., Ju, J., Seo, J., & Park, H. (2026). InteractiveKG: Transparent and
> user-controllable knowledge graph reasoning. *Information Visualization*, 25(3), 310–332.
> https://doi.org/10.1177/14738716261435574

```bibtex
@article{kim2026interactivekg,
  title   = {InteractiveKG: Transparent and user-controllable knowledge graph reasoning},
  author  = {Kim, Minchan and Zhao, Yanjie and Ju, Jaeseong and Seo, Jaeeun and Park, Hyunwoo},
  journal = {Information Visualization},
  volume  = {25},
  number  = {3},
  pages   = {310--332},
  year    = {2026},
  doi     = {10.1177/14738716261435574},
  url     = {https://doi.org/10.1177/14738716261435574}
}
```

## Contact and Support

For issues, questions, or contributions, please refer to the project repository or contact the development team.
