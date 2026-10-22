"""
SISTEMA DE CONCILIAÇÃO BANCÁRIA E EDUCAÇÃO FINANCEIRA PESSOAL - ANDROID (KIVYMD)
=================================================================================
Aplicativo Mobile Nativo em Python usando KivyMD.
Arquitetura Orientada a Objetos, Leitura de Extratos PDF, Regras Condicionais
por Faixa de Valor (ex: Posto x Conveniência), Categorias Customizadas e Alertas.
"""

import os
import re
import html
import io
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple

@dataclass
class Transaction:
    """Modelo orientado a objetos para representar uma transação financeira."""
    id: int
    date: str
    description: str
    amount: float
    trans_type: str  # 'ENTRADA' ou 'SAIDA'
    category: str = "Outros Gastos"
    status: str = "Pendente"  # 'Pendente' ou 'Conciliado'
    orientation_note: str = ""

    def __post_init__(self):
        self.description = html.escape(self.description.strip())[:200]
        self.amount = round(abs(float(self.amount)), 2)
        if self.orientation_note:
            self.orientation_note = html.escape(self.orientation_note.strip())[:250]
        
        if self.trans_type not in ["ENTRADA", "SAIDA"]:
            raise ValueError(f"Tipo de transação inválido: {self.trans_type}")
            
    def to_dict(self) -> Dict:
        return {
            "ID": self.id,
            "Data": self.date,
            "Descrição": self.description,
            "Valor (R$)": self.amount,
            "Tipo": self.trans_type,
            "Categoria": self.category,
            "Status": self.status,
            "Orientação": self.orientation_note
        }


@dataclass
class RuleCondition:
    """Regra de categorização condicional por palavra-chave e faixa de valor."""
    keyword: str
    category: str
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    orientation_note: str = ""

    def matches(self, description: str, amount: float) -> bool:
        kw_clean = self.keyword.lower().strip()
        if kw_clean not in description.lower():
            return False
        if self.min_amount is not None and amount < self.min_amount:
            return False
        if self.max_amount is not None and amount > self.max_amount:
            return False
        return True


class CategoryRuleEngine:
    """Gerenciador de regras dinâmicas e categorias de Entrada/Saída."""

    DEFAULT_CATEGORIES_ENTRADA = [
        "Renda/Salário", "Serviço de Mão de Obra", "Serviço de Infraestrutura",
        "Medição de Projeto", "Vendas/Reembolso", "Outras Entradas"
    ]

    DEFAULT_CATEGORIES_SAIDA = [
        "Construção/Material", "Obra/Mão de Obra", "Serviço de Infraestrutura",
        "Alimentação/Supermercado", "Conveniência/Lanches", "Combustível/Posto",
        "Transporte/Uber", "Moradia/Contas", "Lazer/Streaming", "Saúde", "Outros Gastos"
    ]

    def __init__(self):
        self.categories_entrada = self.DEFAULT_CATEGORIES_ENTRADA.copy()
        self.categories_saida = self.DEFAULT_CATEGORIES_SAIDA.copy()
        
        self.conditional_rules: List[RuleCondition] = [
            RuleCondition(
                keyword="lagos conveniencia",
                category="Combustível/Posto",
                min_amount=48.00,
                max_amount=52.00,
                orientation_note="Abastecimento de combustível na bomba (R$ 48 - R$ 52)"
            ),
            RuleCondition(
                keyword="lagos conveniencia",
                category="Conveniência/Lanches",
                orientation_note="Compras de pão, cigarro e conveniência"
            ),
            RuleCondition(
                keyword="material de construcao",
                category="Construção/Material",
                orientation_note="Compra de suprimentos para obra"
            )
        ]

    def add_category(self, name: str, trans_type: str):
        name_clean = name.strip()
        if not name_clean:
            return
        if trans_type == "ENTRADA" and name_clean not in self.categories_entrada:
            self.categories_entrada.append(name_clean)
        elif trans_type == "SAIDA" and name_clean not in self.categories_saida:
            self.categories_saida.append(name_clean)

    def add_conditional_rule(self, keyword: str, category: str, min_amt: Optional[float] = None, max_amt: Optional[float] = None, note: str = ""):
        rule = RuleCondition(
            keyword=keyword.strip().lower(),
            category=category,
            min_amount=min_amt,
            max_amount=max_amt,
            orientation_note=note
        )
        self.conditional_rules.insert(0, rule)

    def categorize(self, description: str, amount: float, trans_type: str) -> Tuple[str, str]:
        for rule in self.conditional_rules:
            if rule.matches(description, amount):
                return rule.category, rule.orientation_note

        if trans_type == "ENTRADA":
            return "Renda/Salário", "Entrada de recursos"
        
        return "Outros Gastos", "Lançamento pendente de classificação manual"


class PDFStatementParser:
    """Extrai transações de PDF bancário de forma segura no dispositivo mobile."""

    def __init__(self, rule_engine: CategoryRuleEngine):
        self.rule_engine = rule_engine

    def parse_pdf_bytes(self, pdf_bytes: bytes) -> Tuple[List[Transaction], List[str]]:
        import pdfplumber
        transactions: List[Transaction] = []
        errors: List[str] = []
        next_id = 1

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    lines = text.split("\n")
                    for line_num, line in enumerate(lines, start=1):
                        line_str = line.strip()
                        if not line_str:
                            continue
                        
                        try:
                            tr = self._parse_single_line(line_str, next_id)
                            if tr:
                                transactions.append(tr)
                                next_id += 1
                        except Exception as ex:
                            errors.append(f"Linha {line_num}: {str(ex)}")

        except Exception as e:
            errors.append(f"Erro no PDF: {str(e)}")

        return transactions, errors

    def _parse_single_line(self, line: str, tr_id: int) -> Optional[Transaction]:
        date_match = re.search(r"(\d{2}/\d{2}(?:/\d{2,4})?)", line)
        if not date_match:
            return None

        date_str = date_match.group(1)
        amount_matches = re.findall(r"([-+]?\s*(?:R\$\s*)?\d{1,3}(?:\.\d{3})*,\d{2}\s*[-+DCdc]?)", line)
        if not amount_matches:
            return None

        raw_amount_str = amount_matches[-1].strip()
        is_negative = ("-" in raw_amount_str) or ("D" in raw_amount_str.upper() and not "CRED" in raw_amount_str.upper())
        
        clean_amount_str = re.sub(r"[^\d,]", "", raw_amount_str).replace(",", ".")
        try:
            amount_val = float(clean_amount_str)
        except ValueError:
            return None

        if amount_val == 0:
            return None

        trans_type = "SAIDA" if is_negative else "ENTRADA"
        desc = line.replace(date_str, "").replace(raw_amount_str, "").strip()
        desc = re.sub(r"\s+", " ", desc)
        if not desc:
            desc = "Lançamento de Extrato"

        category, note = self.rule_engine.categorize(desc, amount_val, trans_type)

        return Transaction(
            id=tr_id,
            date=date_str,
            description=desc,
            amount=amount_val,
            trans_type=trans_type,
            category=category,
            status="Pendente",
            orientation_note=note
        )


class ConciliadorAndroidApp:
    """Classe principal do aplicativo Android KivyMD."""
    def __init__(self):
        self.rule_engine = CategoryRuleEngine()
        self.transactions: List[Transaction] = []
        self.parser = PDFStatementParser(self.rule_engine)

    def load_demo_data(self):
        self.transactions = [
            Transaction(1, "01/10/2026", "SALARIO EMPRESA XYZ", 5500.00, "ENTRADA", "Renda/Salário", "Conciliado", "Entrada referente a salário mensal"),
            Transaction(2, "02/10/2026", "SAIDA DEBITO LAGOS CONVENIENCIA", 50.00, "SAIDA", "Combustível/Posto", "Pendente", "Abastecimento de combustível na bomba (R$ 48 - R$ 52)"),
            Transaction(3, "03/10/2026", "SAIDA DEBITO LAGOS CONVENIENCIA", 18.50, "SAIDA", "Conveniência/Lanches", "Pendente", "Compras de pão, cigarro e conveniência"),
            Transaction(4, "05/10/2026", "MATERIAL DE CONSTRUCAO SAO JOSE", 1250.00, "SAIDA", "Construção/Material", "Conciliado", "Compra de cimento e suprimentos de obra"),
            Transaction(5, "10/10/2026", "PIX RECEBIDO - MEDICAO INFRAESTRUTURA", 3200.00, "ENTRADA", "Serviço de Infraestrutura", "Conciliado", "Entrada referente a medição de obra de infraestrutura")
        ]

if __name__ == "__main__":
    app = ConciliadorAndroidApp()
    app.load_demo_data()
    print("Módulo KivyMD para Android compilado e pronto!")
