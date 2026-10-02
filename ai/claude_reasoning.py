"""
Claude AI Reasoning - Explainable diagnosis with confidence scores
Integrates vision + environmental sensor context
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anthropic
from config.settings import CLAUDE_API_KEY

class ClaudeReasoning:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        
    def diagnose(self, image_base64, sensor_context, crop_name):
        """
        Get AI diagnosis with explanation
        Returns: {diagnosis, reasoning, confidence, treatment}
        """
        prompt = f"""You are an expert agricultural pathologist analyzing a {crop_name} plant.

Environmental Context:
- Temperature: {sensor_context.get('temperature_c')}°C
- Humidity: {sensor_context.get('humidity_pct')}%
- Soil Moisture 1: {sensor_context.get('soil1_raw')} (raw ADC)
- Soil Moisture 2: {sensor_context.get('soil2_raw')} (raw ADC)
- Light: {sensor_context.get('lux')} lux

Analyze the image and provide:
1. Diagnosis (disease name or "healthy")
2. Reasoning (what symptoms you observe)
3. Confidence (0.0 to 1.0)
4. Recommended treatment (if diseased)

Respond in JSON format:
{{"diagnosis": "...", "reasoning": "...", "confidence": 0.0, "treatment": "..."}}
"""
        
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }}
                ]
            }]
        )
        
        # Parse response (simplified - add proper JSON parsing)
        response_text = message.content[0].text
        print(f"[AI] Claude response: {response_text}")
        
        # TODO: Parse JSON properly
        return {
            "diagnosis": "unknown",
            "reasoning": response_text,
            "confidence": 0.5,
            "treatment": "manual inspection"
        }
