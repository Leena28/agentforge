from dataclasses import dataclass

from app.config.settings import get_settings
from app.core.logging import logger


@dataclass(slots=True)
class LLMResult:
    text: str
    tokens: int
    cost_usd: float


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def complete(
        self,
        *,
        system: str,
        prompt: str,
        fallback: str,
        model: str | None = None,
        temperature: float | None = None,
    ) -> LLMResult:
        if not self.settings.enable_llm:
            return self._fallback(fallback)

        actual_model = model or self.settings.llm_model
        actual_temperature = temperature or self.settings.llm_temperature

        try:
            from litellm import acompletion

            response = await acompletion(
                model=actual_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=actual_temperature,
                timeout=self.settings.llm_timeout_seconds,
                api_key=self.settings.openai_api_key,
            )
            text = response.choices[0].message.content or fallback
            usage = getattr(response, "usage", None)
            tokens = int(
                getattr(usage, "total_tokens", 0)
                or max(len(text.split()) * 1.3, 1)
            )
            cost_usd = self._estimate_cost(actual_model, tokens)
            return LLMResult(
                text=text.strip(),
                tokens=tokens,
                cost_usd=cost_usd,
            )
        except Exception as exc:
            logger.warning(
                "llm_fallback",
                error=str(exc),
                model=actual_model,
            )
            return self._fallback(fallback)

    def _estimate_cost(self, model: str, tokens: int) -> float:
        cost_per_1k = {
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.000150,
            "gpt-4-turbo": 0.010,
        }
        for key, rate in cost_per_1k.items():
            if key in model:
                return round((tokens / 1000) * rate, 6)
        return 0.0

    @staticmethod
    def _fallback(text: str) -> LLMResult:
        return LLMResult(
            text=text,
            tokens=max(int(len(text.split()) * 1.3), 1),
            cost_usd=0.0,
        )