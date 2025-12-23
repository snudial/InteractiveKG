import json
import uuid
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from ..models.chatbot_models import (
    ChatbotState, ChatMessage, ChatbotRole, TestScenario, TestPhase,
    ChatbotRequest, ChatbotResponse
)
logger = logging.getLogger(__name__)
class ChatbotService:
    def __init__(self):
        self.sessions: Dict[str, ChatbotState] = {}

        self.sample_data_dir = Path(__file__).parent.parent.parent / "sample_data"

        self.phase_descriptions = {

            TestPhase.CASE1_INTRO: "Case 1: LLM Text Response vs InteractiveKG - Select a domain to explore",
            TestPhase.CASE1_LLM_RESPONSE: "Step 1: Review the LLM text response and evaluate its trustworthiness",
            TestPhase.CASE1_EXPLORE_GRAPH: "Step 2: Explore the knowledge graph using Hierarchical Abstraction",
            TestPhase.CASE1_IDENTIFY_ERRORS: "Step 3: Identify unexpected nodes/relationships using Why Function",
            TestPhase.CASE1_EDIT_CORRECT: "Step 4: Edit and correct the knowledge graph using Property Panel",
            TestPhase.CASE1_REQUERY_COMPARE: "Step 5: Re-query and compare results using Internal Retrieve",

            TestPhase.CASE2_INTRO: "Case 2: LLM Text Response vs InteractiveKG - Select a domain to verify",
            TestPhase.CASE2_LLM_RESPONSE: "Step 1: Review the LLM text response with correct data",
            TestPhase.CASE2_EXPLORE_GRAPH: "Step 2: Explore and verify the knowledge graph",
            TestPhase.CASE2_IDENTIFY_ERRORS: "Step 3: Identify unexpected nodes/relationships using Why Function",
            TestPhase.CASE2_EDIT_CORRECT: "Step 4: Edit and correct the knowledge graph using Property Panel",
            TestPhase.CASE2_REQUERY_COMPARE: "Step 5: Re-query and compare results using Internal Retrieve"
        }

    def create_session(self) -> str:

        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ChatbotState(
            session_id=session_id,
            current_phase=TestPhase.CASE1_INTRO
        )
        logger.info(f"Created new Chatbot session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[ChatbotState]:

        return self.sessions.get(session_id)

    async def process_message(self, request: ChatbotRequest) -> ChatbotResponse:

        try:
            session = self.get_session(request.session_id)
            if not session:
                return ChatbotResponse(
                    session_id=request.session_id,
                    message="Session not found, please restart.",
                    current_phase=TestPhase.CASE1_INTRO,
                    current_scenario=None,
                    success=False,
                    error="Session not found"
                )


            user_message = ChatMessage(
                role=ChatbotRole.USER,
                content=request.message,
                timestamp=datetime.now().isoformat()
            )
            session.messages.append(user_message)


            response_content = await self._generate_response(session, request.message)



            assistant_message = ChatMessage(
                role=ChatbotRole.ASSISTANT,
                content=response_content,
                timestamp=datetime.now().isoformat()
            )
            session.messages.append(assistant_message)


            ui_instructions = self._generate_ui_instructions(session)

            advance_button = self.get_phase_advance_button(session)

            data_source_selection_buttons = self.get_data_source_selection_buttons(session)
            return ChatbotResponse(
                session_id=request.session_id,
                message=response_content,
                current_phase=session.current_phase,
                current_scenario=session.current_scenario,
                ui_instructions=ui_instructions,
                advance_button=advance_button,
                data_source_selection_buttons=data_source_selection_buttons,
                success=True
            )

        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return ChatbotResponse(
                session_id=request.session_id,
                message="Sorry, an error occurred while processing your message. Please try again later.",
                current_phase=TestPhase.CASE1_INTRO,
                current_scenario=None,
                success=False,
                error=str(e)
            )

    async def _generate_response(self, session: ChatbotState, user_message: str) -> str:

        return self._get_phase_specific_guidance(session.current_phase)

    def _get_phase_specific_guidance(self, phase: TestPhase) -> str:

        guidance_texts = {
            TestPhase.CASE1_LLM_RESPONSE: """Welcome to Case 1! In this scenario, you'll compare a traditional LLM text response with the InteractiveKG visualization system.
**Please select a domain** from the options below to begin exploring. Each domain contains a knowledge graph with intentional errors that you'll help identify and correct.
Please read the LLM's text response carefully and evaluate its trustworthiness from a data-accuracy perspective.
**Your task:**
- Read the AI-generated response
- Consider whether the information seems credible
- Think about potential errors or inaccuracies
The response may contain errors. In the next step, you'll use the InteractiveKG system to explore the underlying knowledge graph and identify these issues.""",
            TestPhase.CASE1_EXPLORE_GRAPH: """Now let's explore the knowledge graph using the **Hierarchical Abstraction** feature (highlighted on the left).
**How to use it:**
- Use the abstraction slider to adjust the level of detail
- Higher levels show community views (grouped nodes)
- Lower levels show individual nodes and relationships
- Click on community nodes to see detailed sub-graphs
Use the **Why Function** (highlighted on the right) to identify unexpected nodes or relationships.
**How to use it:**
- Click on any node to see its properties
- Click the "Why" button to understand the reasoning
- Look for nodes or relationships that seem incorrect
- The explanation will help you understand why the node is positioned where it is
Use the **Property Panel** (highlighted on the right) to correct the errors you identified.
**You can:**
- Edit node properties (name, type, attributes)
- Edit relationship properties (type, weight)
- Delete incorrect nodes or relationships
- Add missing information if needed
Now use the **Internal Retrieve** feature (highlighted at the bottom) to get a new answer based on your corrected graph.
**How to use it:**
- Click the "Internal Retrieve" tab
- Enter the same question again
- Click "Retrieve" to get a new answer""",
            TestPhase.CASE2_LLM_RESPONSE: """Welcome to Case 2! This time, you'll explore a scenario with correct data.
**Please select a domain** from the options below. Each domain contains a knowledge graph with accurate information that you'll verify using the InteractiveKG system.
Please read the LLM's text response carefully and evaluate its trustworthiness.
**Your task:**
- Read the AI-generated response
- Consider whether the information seems credible
- Think about how you might verify this information
In the next step, you'll use the InteractiveKG system to explore and verify the knowledge graph.""",
            TestPhase.CASE2_EXPLORE_GRAPH: """Use the features you learned in Case 1 to explore and verify the knowledge graph:
**Available features:**
- **Hierarchical Abstraction** (left panel): Adjust abstraction levels
- **Why Function** (right panel): Understand node reasoning
- **Property Panel** (right panel): View node/relationship details""",
            TestPhase.CASE2_IDENTIFY_ERRORS: """Now that you've explored the graph, let's identify any unexpected nodes or relationships.
**How to use the Why Function:**
- Double-click on any node to see why it's positioned in a certain community
- The explanation panel (right side) will show the reasoning
- Look for nodes that seem out of place or relationships that don't make sense
**Your task:**
- Identify at least one node or relationship that seems unexpected
- Use the Why function to understand the reasoning
- Think about whether the positioning makes sense
Once you've identified unexpected elements, you can proceed to edit them.""",
            TestPhase.CASE1_EDIT_CORRECT: """After identifying problem nodes/relationships, you can now edit the knowledge graph to impact LLM reasoning.
**How to edit:**
- Double-click on a node or relationship to open the Property Panel
- Modify properties, labels, or relationships
- Save your changes
**Your task:**
- Make corrections to the nodes/relationships you identified
- Consider how these changes might improve the LLM's reasoning
- Save your edits
Once you've made your corrections, you can proceed to re-query the system.""",
            TestPhase.CASE1_RETRIEVE_AFTER_EDIT: """Great work! You've corrected the knowledge graph.
Now use the **Internal Retrieve** feature (highlighted at the bottom) to get a new answer based on your corrected graph.
**How to use it:**
- Click the "Internal Retrieve" tab
- Enter the same question again
- Click "Retrieve" to get a new answer"""
        }
        return guidance_texts.get(phase, f"Welcome to {self.phase_descriptions.get(phase, 'this phase')}. Please follow the instructions to proceed.")
    def _generate_ui_instructions(self, session: ChatbotState) -> Dict[str, Any]:

        ui_instructions = {}


        if session.current_phase == TestPhase.CASE1_LLM_RESPONSE:
            ui_instructions = {
                "highlight_panel": "llm_response_panel"
            }
        elif session.current_phase == TestPhase.CASE1_EXPLORE_GRAPH:
            ui_instructions = {
                "highlight_panel": "hierarchical_abstraction_panel"
            }
        elif session.current_phase == TestPhase.CASE1_IDENTIFY_ERRORS:
            ui_instructions = {
                "highlight_panel": "graph_visualization"
            }
        elif session.current_phase == TestPhase.CASE1_EDIT_CORRECT:
            ui_instructions = {
                "highlight_panel": "property_panel"
            }
        elif session.current_phase == TestPhase.CASE1_REQUERY_COMPARE:
            ui_instructions = {
                "highlight_panel": "kgot_panel",
                "highlight_tab": "retrieve"
            }

        elif session.current_phase == TestPhase.CASE2_LLM_RESPONSE:
            ui_instructions = {
                "highlight_panel": "llm_response_panel"
            }
        elif session.current_phase == TestPhase.CASE2_EXPLORE_GRAPH:
            ui_instructions = {
                "highlight_panel": "hierarchical_abstraction_panel"
            }
        elif session.current_phase == TestPhase.CASE2_IDENTIFY_ERRORS:
            ui_instructions = {
                "highlight_panel": "graph_visualization"
            }
        elif session.current_phase == TestPhase.CASE2_EDIT_CORRECT:
            ui_instructions = {
                "highlight_panel": "property_panel"
            }
        elif session.current_phase == TestPhase.CASE2_REQUERY_COMPARE:
            ui_instructions = {
                "highlight_panel": "kgot_panel",
                "highlight_tab": "retrieve"
            }
        return ui_instructions

    def advance_phase(self, session_id: str, target_phase: Optional[TestPhase] = None) -> bool:

        session = self.get_session(session_id)
        if not session:
            return False

        if target_phase:
            session.current_phase = target_phase
        else:

            phase_order = list(TestPhase)
            current_index = phase_order.index(session.current_phase)
            if current_index < len(phase_order) - 1:
                session.current_phase = phase_order[current_index + 1]

        logger.info(f"Session {session_id} advanced to phase: {session.current_phase}")
        return True

    def get_progress_percentage(self, session: ChatbotState) -> float:

        phase_weights = {

            TestPhase.CASE1_INTRO: 0.05,
            TestPhase.CASE1_LLM_RESPONSE: 0.15,
            TestPhase.CASE1_EXPLORE_GRAPH: 0.25,
            TestPhase.CASE1_IDENTIFY_ERRORS: 0.35,
            TestPhase.CASE1_EDIT_CORRECT: 0.45,
            TestPhase.CASE1_REQUERY_COMPARE: 0.50,

            TestPhase.CASE2_INTRO: 0.55,
            TestPhase.CASE2_LLM_RESPONSE: 0.65,
            TestPhase.CASE2_EXPLORE_GRAPH: 0.75,
            TestPhase.CASE2_IDENTIFY_ERRORS: 0.85,
            TestPhase.CASE2_EDIT_CORRECT: 0.95,
            TestPhase.CASE2_REQUERY_COMPARE: 1.0
        }
        return phase_weights.get(session.current_phase, 0.0)
    def get_phase_advance_button(self, session: ChatbotState) -> Optional[Dict[str, Any]]:

        if not session:
            return None

        button_configs = {


            TestPhase.CASE1_LLM_RESPONSE: {
                "label": "Explore Knowledge Graph",
                "description": "I've reviewed the LLM response",
                "target_phase": "case1_explore_graph",
                "variant": "primary"
            },
            TestPhase.CASE1_EXPLORE_GRAPH: {
                "label": "Identify Errors",
                "description": "I've explored the graph structure",
                "target_phase": "case1_identify_errors",
                "variant": "primary"
            },
            TestPhase.CASE1_IDENTIFY_ERRORS: {
                "label": "Edit and Correct",
                "description": "I've identified suspicious nodes/relationships",
                "target_phase": "case1_edit_correct",
                "variant": "warning"
            },
            TestPhase.CASE1_EDIT_CORRECT: {
                "label": "Re-query and Compare",
                "description": "I've made corrections to the graph",
                "target_phase": "case1_requery_compare",
                "variant": "success"
            },
            TestPhase.CASE1_REQUERY_COMPARE: {
                "label": "Complete Case 1",
                "description": "I've compared the results",
                "target_phase": "case2_intro",
                "variant": "success"
            },


            TestPhase.CASE2_LLM_RESPONSE: {
                "label": "Explore Knowledge Graph",
                "description": "I've reviewed the LLM response",
                "target_phase": "case2_explore_graph",
                "variant": "primary"
            },
            TestPhase.CASE2_EXPLORE_GRAPH: {
                "label": "Identify Errors",
                "description": "I've explored the graph structure",
                "target_phase": "case2_identify_errors",
                "variant": "primary"
            },
            TestPhase.CASE2_IDENTIFY_ERRORS: {
                "label": "Edit and Correct",
                "description": "I've identified suspicious nodes/relationships",
                "target_phase": "case2_edit_correct",
                "variant": "warning"
            },
            TestPhase.CASE2_EDIT_CORRECT: {
                "label": "Re-query and Compare",
                "description": "I've made corrections to the graph",
                "target_phase": "case2_requery_compare",
                "variant": "success"
            },
            TestPhase.CASE2_REQUERY_COMPARE: {
                "label": "Complete Study",
                "description": "I've compared the results",
                "target_phase": None,
                "variant": "success"
            }
        }
        return button_configs.get(session.current_phase)
    def get_data_source_selection_buttons(self, session: ChatbotState) -> Optional[List[Dict[str, Any]]]:

        if not session or session.current_phase not in [TestPhase.CASE1_INTRO, TestPhase.CASE2_INTRO]:
            return None

        case_prefix = "case1" if session.current_phase == TestPhase.CASE1_INTRO else "case2"

        domain_buttons = [
            {
                "id": f"{case_prefix}_nlp",
                "label": "🧠 NLP",
                "domain": "nlp",
                "file": f"{case_prefix}_nlp.json",
                "title": "Natural Language Processing",
                "description": "Explore NLP models and architectures",
                "variant": "primary"
            },
            {
                "id": f"{case_prefix}_medical",
                "label": "🏥 Medical",
                "domain": "medical",
                "file": f"{case_prefix}_medical.json",
                "title": "Medical Knowledge",
                "description": "Explore medical concepts and treatments",
                "variant": "primary"
            },
            {
                "id": f"{case_prefix}_math",
                "label": "📐 Math",
                "domain": "math",
                "file": f"{case_prefix}_math.json",
                "title": "Mathematical Concepts",
                "description": "Explore mathematical definitions and properties",
                "variant": "primary"
            },
            {
                "id": f"{case_prefix}_business",
                "label": "💼 Business",
                "domain": "business",
                "file": f"{case_prefix}_business.json",
                "title": "Business Framework (TMF)",
                "description": "Explore business process frameworks",
                "variant": "primary"
            },
            {
                "id": f"{case_prefix}_common",
                "label": "📖 Stories",
                "domain": "common",
                "file": f"{case_prefix}_common.json",
                "title": "Common Knowledge",
                "description": "Explore everyday concepts and stories",
                "variant": "primary"
            }
        ]
        return domain_buttons

chatbot_service = ChatbotService()