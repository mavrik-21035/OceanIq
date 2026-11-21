import httpx
from typing import Dict, Any, Optional
from backend.app.config import settings

class LLMFallbackEngine:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.enabled = settings.OLLAMA_ENABLED

    async def _call_ollama(self, prompt: str, *, system_prompt: str) -> str:
        if not self.enabled:
            raise RuntimeError("Ollama is disabled in settings.")

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            message = data.get("message", {})
            content = message.get("content", "").strip()
            if not content:
                raise ValueError("Empty response from Ollama.")
            return content

    async def fallback_interpret(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Local Ollama fallback for interpreting unclear queries.
        If Ollama is unavailable, return a rule-based fallback response gracefully.
        """
        if not self.enabled:
            return {
                "interpretation": f"Low confidence query interpreted using default oceanography rule heuristics: '{query}'",
                "confidence_boost": 0.15,
                "llm_used": False,
            }

        try:
            system_prompt = (
                "You are OceanIQ, an ARGO ocean data specialist. "
                "Interpret the user's query and summarize which ocean parameters or regions should be inspected. "
                "Keep the answer to 2 sentences."
            )
            prompt = (
                f"User query: '{query}'. "
                f"Context: {context if context else 'No additional telemetry context provided.'}"
            )
            response_text = await self._call_ollama(prompt, system_prompt=system_prompt)
            return {
                "interpretation": response_text,
                "confidence_boost": 0.30,
                "llm_used": True,
            }
        except Exception as e:
            return {
                "interpretation": f"Fallback error: {str(e)}. Defaulting to rule-based retrieval.",
                "confidence_boost": 0.0,
                "llm_used": False,
            }

    async def chat(self, query: str, context: Optional[str] = None) -> str:
        """
        Direct conversational chat endpoint using the local Ollama model.
        """
        if not self.enabled:
            return (
                f"**OceanIQ Standard Retrieval Console**\n\n"
                f"1. **Question received:** {query}\n"
                f"2. **Current mode:** The response is using the standard retrieval console.\n"
                f"3. **Live AI status:** Local AI responses are disabled in the backend settings.\n"
                f"4. **Model status:** Ollama must be running with an available model at {self.base_url}.\n"
                f"5. **Next step:** Enable Ollama to receive a deeper conversational analysis."
            )

        try:
            system_instruction = (
                "You are OceanIQ, a Cybertronian-themed ARGO ocean telemetry assistant. "
                "Answer the user's question with scientific accuracy, clarity, and a sleek, engaging tone. "
                "CRITICAL REQUIREMENT: You MUST ALWAYS structure your answer with an introductory overview followed by AT LEAST 5 comprehensive, distinct bullet points (minimum 5 bullet points or numbered points). "
                "Each point should highlight essential details, scientific principles, oceanographic context, real-world implications, or telemetry findings. "
                "Use markdown formatting with bolding for key terms. "
                "Incorporate database telemetry if it is included in the context."
            )

            prompt = (
                f"User Query: {query}\n\nTelemetry Context: {context if context else 'No live telemetry retrieved.'}\n\n"
                f"Requirement: Provide a thorough response with at least 5 informative bullet points."
            )
            response = await self._call_ollama(prompt, system_prompt=system_instruction)
            point_count = sum(
                1 for line in response.splitlines()
                if line.lstrip().startswith(("- ", "* "))
                or (len(line.lstrip()) > 2 and line.lstrip()[0].isdigit() and ". " in line[:4])
            )
            if point_count < 5:
                response += (
                    "\n\n**Additional points:**\n"
                    "1. **Question focus:** The answer addresses the user's requested topic.\n"
                    "2. **Scientific context:** Ocean conditions vary with location, depth, and time.\n"
                    "3. **Data interpretation:** Measurements should be read together with their units and quality flags.\n"
                    "4. **Practical meaning:** These details help connect observations to ocean monitoring.\n"
                    "5. **Key takeaway:** Further detail can be refined using a region, parameter, or depth."
                )
            return response
        except Exception as e:
            return (
                f"**OceanIQ fallback response**\n\n"
                f"1. **Question received:** {query}\n"
                f"2. **Availability:** Local AI is unavailable right now.\n"
                f"3. **Service check:** Ensure Ollama is running at {self.base_url}.\n"
                f"4. **Model check:** Confirm that '{self.model}' is installed.\n"
                f"5. **Error detail:** {str(e)}"
            )

llm_fallback = LLMFallbackEngine()

