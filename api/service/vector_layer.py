from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from api.configuration.llm_factory import LLMFactory


class RAGManager:
    def __init__(self):
        self.embeddings = LLMFactory.get_embeddings()
        self.vector_store = None

    def ingest_examples(self):
        print("🧠 Ingesting RAG examples into FAISS...")

        examples = [
            {
                "question": "Show me all cancelled orders with their order ID, date, amount and ship city.",
                "sql": """SELECT "order_id", "date", "amount", "ship-city" FROM public."Amazon Sale Report" WHERE LOWER("status") = 'cancelled';"""
            },
            {
                "question": "Give me quantity sold for each product category on Amazon.in sales channel.",
                "sql": """SELECT  "category", SUM("qty") AS total_qty FROM public."Amazon Sale Report" WHERE LOWER("sales_channel_") = 'amazon.in' GROUP BY "category" ORDER BY total_qty DESC;"""
            },
            {
                "question": "Show me the price per unit for each service (Inbound, Outbound, Storage Fee, Customer Return) from both Shiprocket and Increff.",
                "sql": """SELECT 
                            "shiprocket",
                            "unnamed:_1" AS shiprocket_price,
                            "increff" AS increff_price
                        FROM public.cloud_warehouse_compersion_chart
                        WHERE "shiprocket" IN (
                            'Inbound (Fresh Stock and RTO)',
                            'Outbound',
                            'Storage Fee/Cft',
                            'Customer Return with Detailed QC'
                        );"""
            },
            {
                "question": "Fetch only the operations (like Unloading, Validation, QC, GRN) with their descriptions from the Increff/price column.",
                "sql": """SELECT 
                                "shiprocket" AS operation,
                                "increff" AS description
                            FROM public.cloud_warehouse_compersion_chart
                            WHERE "shiprocket" IN ('Inward', 'Validation', 'QC', 'GRN');"""
            },
            {
                "question": "Show all purchases made by the customer REVATHY LOGANATHAN, including style, size, pcs and gross amount.",
                "sql": """SELECT 
                            "date",
                            "customer",
                            "style",
                            "size",
                            "pcs",
                            "gross_amt"
                        FROM public.international_sale_report
                        WHERE "customer" = 'REVATHY LOGANATHAN';"""
            },
            {
                "question": "Get the total quantity (pcs) and total gross amount for the month Jun-21.",
                "sql": """SELECT 
                            "months",
                            SUM("pcs"::numeric) AS total_pcs,
                            SUM("gross_amt"::numeric) AS total_gross_amount
                        FROM public.international_sale_report
                        WHERE "months" = 'Jun-21'
                        GROUP BY "months";"""
            },
            {
                "question": "List all SKUs and their selling rate where the rate is greater than 620.",
                "sql": """SELECT 
                            "sku",
                            "rate",
                            "size",
                            "customer"
                        FROM public.international_sale_report
                        WHERE "rate"::numeric > 620;"""
            },
            {
                "question": "Get all SKUs where the category is Kurta Set.",
                "sql": """SELECT 
                            "sku",
                            "style_id",
                            "catalog",
                            "category",
                            "tp",
                            "final_mrp_old"
                        FROM public.may_2022
                        WHERE "category" = 'Kurta Set';"""
            },
            {
                "question": "Identify best-selling sizes in KURTA category (based on inventory availability).",
                "sql": """SELECT size, SUM(stock) AS total_stock
                            FROM sale_report
                            WHERE category = 'KURTA'
                            GROUP BY size
                            ORDER BY total_stock DESC;"""
            },
            {
                "question": "Identify slow-moving SKUs (stock high, but no sales / low movement last 30 days)",
                "sql": """SELECT "order_id", "date", "amount", "status"
                            FROM public."Amazon Sale Report"
                            WHERE "amount" > 5000 AND LOWER("status") = 'completed';"""
            },
            {
                "question": "provide me daily expense summary from expense_iigf table.",
                "sql": """SELECT
                              NULLIF(trim("expance"), '') AS expense_particular,
                              SUM(NULLIF(regexp_replace("unnamed:_3", '[^0-9.-]', '', 'g'), '')::numeric) AS total_expense
                            FROM public.expense_iigf
                            GROUP BY NULLIF(trim("expance"), '')
                            ORDER BY total_expense DESC;"""
            }

        ]

        docs = []
        for ex in examples:
            page_content = ex["question"]
            metadata = {"sql_query": ex["sql"]}
            docs.append(Document(page_content=page_content, metadata=metadata))

        self.vector_store = FAISS.from_documents(docs, self.embeddings)
        print("RAG Index built.")

    def retrieve_similar_examples(self, user_query: str, k=2):
        if not self.vector_store:
            raise Exception("Vector store not initialized. Run ingest_examples() first.")

        results = self.vector_store.similarity_search(user_query, k=k)

        context_str = ""
        for doc in results:
            context_str += f"User: {doc.page_content}\nSQL: {doc.metadata['sql_query']}\n\n"

        return context_str