 

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Conexão com o banco de dados SQLite
conn = sqlite3.connect("proorti.db", check_same_thread=False)
cursor = conn.cursor()

# Criar tabela de produtos
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto TEXT,
    tipo TEXT,
    quantidade INTEGER,
    peso REAL,
    desconto REAL,
    peso_final REAL
)
""")

# Criar tabela de movimentações
cursor.execute("""
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT,
    tipo_movimentacao TEXT,
    produto TEXT,
    tipo TEXT,
    quantidade INTEGER,
    peso_final REAL
)
""")
conn.commit()

st.title("📦 controle de estoque")
st.subheader("hortfruti")
st.write("calculadora para caucular o peso das frutas")

# ✅ CALCULADORA NORMAL
st.subheader("🧮 Calcular e descontar peso")
num1 = st.number_input("primeiro valor", step=1.0, format="%.2f")
num2 = st.number_input("segundo valor", step=1.0, format="%.2f")
operacao = st.selectbox("Operação", ["Somar", "Subtrair", "Multiplicar", "Dividir"])

if st.button("Calcular"):
    if operacao == "Somar":
        resultado = num1 + num2
    elif operacao == "Subtrair":
        resultado = num1 - num2
    elif operacao == "Multiplicar":
        resultado = num1 * num2
    elif operacao == "Dividir":
        resultado = num1 / num2 if num2 != 0 else "Erro: divisão por zero"
    st.success(f"Resultado: {resultado}")

st.markdown("---")

# Lista de produtos
produtos_lista = {
    "a": "tomate", "b": "cebola branca", "c": "cenoura", "d": "melão",
    "e": "manga tommy", "f": "abacate", "g": "beterraba", "h": "goiaba",
    "i": "chuchu", "j": "pepino preto", "l": "pocam", "m": "laranja cutrale",
    "n": "batata lavada", "o": "repolho verde", "p": "coco seco", "q": "limão", "r": "maracujá",
    "s": "pêra", "t": "kiwí", "u": "coco verde", "v": "banana prata", "x": "amendoim",
    "z": "uva verde", "a1": "uva roxa", "b2": "pepino japonês","c3": "mamão papaia","d4": "mamão formosa",
    "e4": "melão redinha","f5": "pêra danjou","g6": "manga palmer","h7": "banana da terra","i8": "repolho roxo",
    "j9": "batata branca","l10": "alho","m11": "manutenção","n12": "gengibre","o13": "ovos","p14": "maçã"
}

# Formulário de entrada
st.subheader("entrada do produto")
st.write("o campo manutenção está destinado ao operador do código fonte.")
produto = st.selectbox("Selecione o produto:", list(produtos_lista.values()))
tipo = st.radio("Tipo de embalagem:", ["Caixa", "Saco"])
quantidade = st.number_input("Quantidade:", min_value=1, value=1)

peso_total_informado = st.number_input("Peso total (kg):", min_value=0.0, step=0.1)

descontar = st.checkbox("Descontar peso?")
desconto = st.number_input("Descontar quantos kg no total?", min_value=0.0, step=0.1) if descontar else 0.0
peso_final = max(peso_total_informado - desconto, 0)

if st.button("Salvar dados"):
    cursor.execute("""
        SELECT id, quantidade, peso, desconto, peso_final
        FROM produtos
        WHERE produto = ? AND tipo = ?
    """, (produto, tipo))
    registro_existente = cursor.fetchone()

    if registro_existente:
        id_existente, qtd_existente, peso_existente, desconto_existente, peso_final_existente = registro_existente
        nova_quantidade = qtd_existente + quantidade
        novo_peso = peso_existente + peso_total_informado
        novo_desconto = desconto_existente + desconto
        novo_peso_final = peso_final_existente + peso_final

        cursor.execute("""
            UPDATE produtos
            SET quantidade = ?, peso = ?, desconto = ?, peso_final = ?
            WHERE id = ?
        """, (nova_quantidade, novo_peso, novo_desconto, novo_peso_final, id_existente))
    else:
        cursor.execute("""
            INSERT INTO produtos (produto, tipo, quantidade, peso, desconto, peso_final)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (produto, tipo, quantidade, peso_total_informado, desconto, peso_final))

    # Registrar entrada no histórico
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO movimentacoes (data_hora, tipo_movimentacao, produto, tipo, quantidade, peso_final)
        VALUES (?, 'Entrada', ?, ?, ?, ?)
    """, (data_hora, produto, tipo, quantidade, peso_final))

    conn.commit()
    st.success(f"{quantidade} {tipo.lower()}(s) de {produto} registrados! Peso final: {peso_final:.2f} kg")

st.markdown("---")

# 📦 Estoque Atual
st.subheader("📦 Estoque Atual")
st.write("os descontos são descontos do peso da embalagem do produto.")
df_produtos = pd.read_sql_query("SELECT * FROM produtos ORDER BY produto", conn)
st.dataframe(df_produtos)

st.markdown("---")

# 📤 Controle de saída
st.subheader("📤 Controle de Saída de Produtos")
cursor.execute("SELECT DISTINCT produto FROM produtos")
produtos_existentes = [p[0] for p in cursor.fetchall()]

if produtos_existentes:
    produto_saida = st.selectbox("Produto que saiu:", produtos_existentes)
    cursor.execute("SELECT DISTINCT tipo FROM produtos WHERE produto = ?", (produto_saida,))
    tipos_existentes = [t[0] for t in cursor.fetchall()]
    tipo_saida = st.selectbox("Tipo de embalagem:", tipos_existentes)
    quantidade_saida = st.number_input("Quantidade que saiu:", min_value=1, value=1)

    if st.button("Registrar saída"):
        cursor.execute("""
            SELECT id, quantidade, peso, peso_final
            FROM produtos
            WHERE produto = ? AND tipo = ?
        """, (produto_saida, tipo_saida))
        registro = cursor.fetchone()

        if registro:
            id_registro, qtd_atual, peso_atual, peso_final_atual = registro
            if quantidade_saida > qtd_atual:
                st.error("❌ Saída maior que estoque disponível!")
            else:
                peso_por_caixa = peso_atual / qtd_atual if qtd_atual > 0 else 0
                peso_final_por_caixa = peso_final_atual / qtd_atual if qtd_atual > 0 else 0
                nova_quantidade = qtd_atual - quantidade_saida
                novo_peso = peso_atual - (peso_por_caixa * quantidade_saida)
                novo_peso_final = peso_final_atual - (peso_final_por_caixa * quantidade_saida)

                cursor.execute("""
                    UPDATE produtos
                    SET quantidade = ?, peso = ?, peso_final = ?
                    WHERE id = ?
                """, (nova_quantidade, novo_peso, novo_peso_final, id_registro))

                # Registrar saída no histórico
                data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO movimentacoes (data_hora, tipo_movimentacao, produto, tipo, quantidade, peso_final)
                    VALUES (?, 'Saída', ?, ?, ?, ?)
                """, (data_hora, produto_saida, tipo_saida, quantidade_saida, peso_final_por_caixa * quantidade_saida))

                conn.commit()
                st.success(f"✅ Saída registrada: {quantidade_saida} {tipo_saida.lower()}(s) de {produto_saida}")
                st.rerun()
        else:
            st.error("❌ Produto não encontrado.")
else:
    st.info("📦 Nenhum produto no estoque.")

st.markdown("---")

# 📜 Histórico de movimentações
st.subheader("📜 Histórico de Movimentações")
df_mov = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data_hora DESC", conn)
st.dataframe(df_mov)