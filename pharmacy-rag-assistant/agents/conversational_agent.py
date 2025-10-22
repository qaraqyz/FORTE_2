import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Добавляем родительскую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from agents.sql_agent import SQLAgent
from agents.rag_agent import RAGAgent
from tools.sql_executor import execute_safe_sql
from tools.visualizer import create_visualization
from utils.logger import setup_logger

load_dotenv()

# Настройка логирования
logger = setup_logger('conversational_agent', 'logs/conversational_agent.log')


class ConversationalAgent:
    def __init__(self):
        self.model = os.getenv("CONVERSATIONAL_MODEL", "gpt-4o")
        self.temperature = float(os.getenv("CONVERSATIONAL_TEMPERATURE", "0.5"))

        # Загружаем промпт (базовый шаблон)
        prompt_path = Path(__file__).parent / "prompts" / "basic_ai.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.system_prompt_template = f.read()

        # Инициализируем OpenAI клиента
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Инициализируем агентов
        self.sql_agent = SQLAgent()
        self.rag_agent = RAGAgent()

        # История диалога
        self.conversation_history = []

        # Определяем инструменты
        self.tools = self._define_tools()

    def _format_system_prompt(self) -> str:
        if self.conversation_history:
            formatted_history = []
            for msg in self.conversation_history:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "user":
                    formatted_history.append(f"USER: {content}")
                elif role == "assistant":
                    formatted_history.append(f"AI: {content}")

            history_text = "\n".join(formatted_history)

        return self.system_prompt_template.replace("{{messages}}", history_text)

    def _define_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_sql",
                    "description": "Генерирует SQL запрос на основе описания на естественном языке",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_description": {
                                "type": "string",
                                "description": "Описание запроса на естественном языке"
                            }
                        },
                        "required": ["query_description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_sql",
                    "description": "Выполняет SQL запрос в базе данных",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {
                                "type": "string",
                                "description": "SQL запрос для выполнения"
                            }
                        },
                        "required": ["sql_query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_visualization",
                    "description": "Создает график на основе данных",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "string",
                                "description": "Данные для визуализации в формате JSON"
                            },
                            "chart_type": {
                                "type": "string",
                                "enum": ["bar", "line", "pie", "scatter"],
                                "description": "Тип графика"
                            },
                            "title": {
                                "type": "string",
                                "description": "Заголовок графика"
                            },
                            "x_column": {
                                "type": "string",
                                "description": "Название колонки для оси X"
                            },
                            "y_column": {
                                "type": "string",
                                "description": "Название колонки для оси Y"
                            }
                        },
                        "required": ["data", "chart_type", "title", "x_column", "y_column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge",
                    "description": "Ищет релевантную информацию в базе знаний используя векторный поиск (RAG). Используй когда нужна общая информация о продуктах, регионах, категориях или аптеках.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Запрос для поиска в базе знаний"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def _execute_tool(self, tool_name: str, tool_args: Dict) -> Any:
        logger.info(f"Вызов инструмента: {tool_name}, аргументы: {tool_args}")

        try:
            if tool_name == "generate_sql":
                sql = self.sql_agent.generate_sql(tool_args["query_description"])
                logger.info(f"SQL сгенерирован: {sql}")
                return {"sql": sql, "status": "success"}

            elif tool_name == "execute_sql":
                logger.info(f"Выполнение SQL: {tool_args['sql_query']}")
                results = execute_safe_sql(tool_args["sql_query"])
                logger.info(f"Получено {len(results)} строк результата")
                return {"data": results, "row_count": len(results), "status": "success"}

            elif tool_name == "create_visualization":
                # Парсим данные из JSON строки
                data = json.loads(tool_args["data"]) if isinstance(tool_args["data"], str) else tool_args["data"]

                logger.info(f"Создание визуализации: {tool_args['chart_type']}, записей: {len(data)}")
                fig = create_visualization(
                    data=data,
                    chart_type=tool_args["chart_type"],
                    title=tool_args["title"],
                    x_column=tool_args["x_column"],
                    y_column=tool_args["y_column"]
                )
                logger.info("Визуализация создана успешно")
                return {"figure": fig, "status": "success"}

            elif tool_name == "search_knowledge":
                logger.info(f"Поиск в базе знаний: {tool_args['query']}")
                context = self.rag_agent.search_knowledge(tool_args["query"])
                logger.info("Поиск завершен")
                return {"context": context, "status": "success"}

            else:
                logger.error(f"Неизвестный инструмент: {tool_name}")
                return {"error": f"Неизвестный инструмент: {tool_name}", "status": "error"}

        except Exception as e:
            logger.error(f"Ошибка выполнения инструмента {tool_name}: {str(e)}", exc_info=True)
            return {"error": str(e), "status": "error"}

    def chat(self, user_message: str) -> Dict[str, Any]:
        logger.info(f"Получено сообщение от пользователя: {user_message}")

        # Добавляем сообщение в историю
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            result = self._chat_openai()
            logger.info(f"Ответ сгенерирован успешно, визуализаций: {len(result.get('figures', []))}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {str(e)}", exc_info=True)
            return {
                "response": f"Произошла ошибка: {str(e)}",
                "figures": []
            }

    def _chat_openai(self) -> Dict[str, Any]:
        logger.info(f"Отправка запроса в OpenAI, модель: {self.model}")

        formatted_prompt = self._format_system_prompt()
        messages = [{"role": "system", "content": formatted_prompt}] + self.conversation_history

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            temperature=self.temperature
        )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls

        logger.info(f"Получен ответ от AI, tool_calls: {len(tool_calls) if tool_calls else 0}")

        figures = []
        if tool_calls:
            # Конвертируем assistant_message в словарь для истории
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            })

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                result = self._execute_tool(tool_name, tool_args)

                if tool_name == "generate_sql" and "sql" in result and result["status"] == "success":
                    logger.info("Автоматически выполняем сгенерированный sql...")
                    sql_query = result["sql"]

                    try:
                        exec_result = execute_safe_sql(sql_query)
                        logger.info(f"sql выполнен успешно, получено {len(exec_result)} строк")

                        result["executed"] = True
                        result["data"] = exec_result
                        result["row_count"] = len(exec_result)
                    except Exception as e:
                        logger.error(f"Ошибка выполнения sql: {str(e)}")
                        result["executed"] = False
                        result["error"] = str(e)

                if "figure" in result:
                    figures.append(result["figure"])

                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False, default=str)
                })

            updated_prompt = self._format_system_prompt()
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": updated_prompt}] + self.conversation_history,
                temperature=self.temperature
            )

            final_message = final_response.choices[0].message.content
        else:
            final_message = assistant_message.content

        self.conversation_history.append({"role": "assistant", "content": final_message})

        return {
            "response": final_message,
            "figures": figures
        }

    def clear_history(self):
        self.conversation_history = []
