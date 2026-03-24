import json
import requests
import logging


class LLMService:
    def __init__(self, api_key, model="gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def _call(self, prompt):

        response = requests.post(
            self.url,
            params={"key": self.api_key},
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )

        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logging.error(f"LLM error: {e}")
            return None

    def classify_text_rows(self, df, text_col, sample_size=200, flagged_rows=None):

        df = df.head(sample_size)

        data = [
            {
                "index": int(idx),
                "text": str(row[text_col]),
                "pipeline_flag": flagged_rows.get(int(idx)) if flagged_rows else None,
            }
            for idx, row in df.iterrows()
        ]

        prompt = f"""
    You are a STRICT and FINAL data quality judge.

    You are given:
    - Rows of text
    - Pipeline flags (may be wrong)

    Your job:
    - Validate pipeline flags
    - Add missing bad rows
    - Remove incorrect flags

    BAD rows:
    - spam
    - gibberish
    - irrelevant
    - meaningless
    - templated junk

    IMPORTANT:
    - Be conservative
    - Do NOT over-flag

    RETURN ONLY JSON:

    {{
    "final_flagged_rows": {{
        "index": "reason"
    }}
    }}

    DATA:
    {json.dumps(data, indent=2)}
    """

        response = self._call(prompt)

        if not response:
            return {}

        # 🔥 JSON repair (important)
        try:
            parsed = json.loads(response)
        except:
            try:
                # attempt to extract JSON substring
                start = response.find("{")
                end = response.rfind("}") + 1
                parsed = json.loads(response[start:end])
            except:
                logging.error("Failed to parse LLM response")
                return {}

        return parsed.get("final_flagged_rows", {})
