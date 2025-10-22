import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(str(Path(__file__).parent.parent))
from database.connection import get_connection
from utils.logger import setup_logger

load_dotenv()

logger = setup_logger('rag_agent', 'logs/rag_agent.log')


class RAGAgent:

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("RAG Agent инициализирован")

    def search_knowledge(self, query: str, top_k: int = 3) -> str:
        logger.info(f"Поиск знаний для запроса: {query}")

        try:
            query_embedding = self._create_embedding(query)

            emb_str = '[' + ','.join(map(str, query_embedding)) + ']'

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    content,
                    content_type,
                    1 - (embedding <=> %s::vector) as similarity
                FROM knowledge_base
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (emb_str, emb_str, top_k))

            results = cur.fetchall()
            cur.close()
            conn.close()

            if not results:
                return "Релевантная информация не найдена."

            context_parts = ["Найденная информация из базы знаний:\n"]
            for i, row in enumerate(results, 1):
                similarity = row[2] * 100
                context_parts.append(f"{i}. [{row[1]}] (релевантность: {similarity:.1f}%)")
                context_parts.append(row[0])
                context_parts.append("")

            context = "\n".join(context_parts)
            logger.info(f"Найдено {len(results)} релевантных документов")

            return context

        except Exception as e:
            logger.error(f"Ошибка поиска: {str(e)}", exc_info=True)
            return "Ошибка при поиске информации."

    def _create_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
