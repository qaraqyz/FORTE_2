import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

load_dotenv()

logger = setup_logger('sql_agent', 'logs/sql_agent.log')


class SQLAgent:
    def __init__(self):
        self.model = os.getenv("SQL_MODEL", "gpt-4o")
        self.temperature = float(os.getenv("SQL_TEMPERATURE", "0.0"))

        prompt_path = Path(__file__).parent / "prompts" / "sql_picker_ai.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_sql(self, query_description: str) -> str:
        logger.info(f"Генерация sql для запроса: {query_description}")
        logger.info(f"Использование OpenAI модели: {self.model}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": query_description}
                ],
                temperature=self.temperature
            )
            sql_query = response.choices[0].message.content.strip()

            sql_query = self._clean_sql(sql_query)

            logger.info(f"SQL успешно сгенерирован: {sql_query[:200]}...")

            return sql_query

        except Exception as e:
            logger.error(f"Ошибка генерации SQL: {str(e)}", exc_info=True)
            raise Exception(f"Ошибка генерации SQL: {str(e)}")

    def _clean_sql(self, sql: str) -> str:
        if sql.startswith("```sql"):
            sql = sql.replace("```sql", "").replace("```", "").strip()
        elif sql.startswith("```"):
            sql = sql.replace("```", "").strip()

        return sql
