import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import calendar

# 1. Configuração inicial da página
st.set_page_config(page_title="Meu RPG da Vida Real", page_icon="👑", layout="centered")

# ==========================================
# 🛠️ [Backend: Funções do Banco de Dados]
# ==========================================
def query_db(sql_query, params=()):
    conn = sqlite3.connect("rpg-database.db")
    df = pd.read_sql_query(sql_query, conn, params=params)
    conn.close()
    return df

# app.py 상단의 init_log_table_safety 함수를 이 완벽한 버전으로 교체합니다.
def init_log_table_safety():
    conn = sqlite3.connect("rpg-database.db")
    cursor = conn.cursor()
    
    # 1. 퀘스트 마스터 테이블 자동 생성 (★클라우드 서버를 위한 핵심 추가분)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS master_quest_db (
        quest_id TEXT PRIMARY KEY,
        quest_name TEXT,
        difficulty TEXT,
        reward_xp INTEGER,
        reward_gold INTEGER,
        frequency INTEGER,
        status TEXT
    )
    """)
    
    # 2. 초기 퀘스트 데이터 주입 (포르투갈어 버전으로 세련되게 반영!)
    cursor.executemany("""
    INSERT OR IGNORE INTO master_quest_db VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Q2606-01', 'Alongamento matinal', 'E', 10, 5, 8, 'Active'),
        ('Q2606-02', 'Ler 3 páginas de um livro', 'N', 30, 15, 8, 'Active'),
        ('Q2606-03', 'Análise tática de futebol', 'H', 50, 25, 3, 'Active'),
        ('Q2606-04', 'Relatório de personal trainer', 'H', 50, 25, 11, 'Active')
    ])
    
    # 3. 기존 갓생 로그 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quest_history_log (
        log_date TEXT PRIMARY KEY,
        day_of_week TEXT,
        completed_ids TEXT,
        total_xp INTEGER,
        total_gold INTEGER
    )
    """)
    
    # 4. 상점 메뉴판 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reward_menu (
        reward_item TEXT PRIMARY KEY,
        price_gold INTEGER
    )
    """)
    
    # 5. 보상 구매 영수증 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reward_shop_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_date TEXT,
        reward_item TEXT,
        spent_gold INTEGER
    )
    """)
    
    # 상점 메뉴 초기 데이터 주입
    cursor.executemany("""
    INSERT OR IGNORE INTO reward_menu VALUES (?, ?)
    """, [
        ('Comer Frango Frito 🍗', 500),
        ('1 Hora de YouTube 📱', 100),
        ('Assistir a um Filme na Netflix 🎬', 200),
        ('Ticket para Dormir até Tarde ⏰', 300)
    ])
    
    conn.commit()
    conn.close()

# 안전장치 가동!
init_log_table_safety()


# ==========================================
# 📊 [Cálculo de Dados: Status Atual em Tempo Real]
# ==========================================
try:
    # Soma de XP e Ouro das missões concluídas
    stats_df = query_db("SELECT SUM(total_xp) as attr_xp, SUM(total_gold) as attr_gold FROM quest_history_log")
    total_accumulated_xp = int(stats_df['attr_xp'].iloc[0]) if pd.notna(stats_df['attr_xp'].iloc[0]) else 0
    total_earned_gold = int(stats_df['attr_gold'].iloc[0]) if pd.notna(stats_df['attr_gold'].iloc[0]) else 0
    
    # Soma de Ouro gasto na loja
    shop_df = query_db("SELECT SUM(spent_gold) as attr_spent FROM reward_shop_log")
    total_spent_gold = int(shop_df['attr_spent'].iloc[0]) if pd.notna(shop_df['attr_spent'].iloc[0]) else 0
    
    # Cálculo do saldo de Ouro restante
    current_remaining_gold = total_earned_gold - total_spent_gold

except Exception:
    total_accumulated_xp = 0
    total_earned_gold = 0
    current_remaining_gold = 0

# Definição de Nível e Título com base no XP acumulado
if total_accumulated_xp >= 5000:
    current_level, character_title = 5, "Transcedente da Produtividade 🌌"
elif total_accumulated_xp >= 2500:
    current_level, character_title = 4, "Mestre dos Hábitos ⚡"
elif total_accumulated_xp >= 1200:
    current_level, character_title = 3, "Líder da Rotina ⚔️"
elif total_accumulated_xp >= 500:
    current_level, character_title = 2, "Praticante Dedicado 跑"
else:
    current_level, character_title = 1, "Iniciante da Vida Saudável 🌱"


# ==========================================
# 🖥️ [Frontend UI: Interface em Português]
# ==========================================
st.title("👑 Meu Painel de RPG Pessoal")

# --- A. Seção de Status do Personagem ---
st.write("---")
st.subheader("👤 Status do Personagem (Character Dashboard)")

status_col1, status_col2, status_col3 = st.columns(3)
with status_col1:
    st.metric("Nível Atual", f"LV. {current_level}")
with status_col2:
    st.metric("XP Acumulado", f"{total_accumulated_xp} XP")
with status_col3:
    st.metric("Ouro Disponível", f"{current_remaining_gold} G")

st.markdown(f"**Seu Título Honorário Atual:** `{character_title}`")


# --- B. Seção do Painel de Controle ---
st.write("---")
st.subheader("⚙️ Painel de Controle (Control Panel)")

# Tradução do calendário interativo para o padrão local
selected_date = st.date_input("Selecione uma data", datetime.now())

# Verificação do dia da semana e início/fim do mês
day_of_week = selected_date.weekday() 
numbers_weekday = 1 if day_of_week == 6 else day_of_week + 2
day_of_month = selected_date.day
_, last_day = calendar.monthrange(selected_date.year, selected_date.month)

is_month_first = (day_of_month == 1)
is_month_last = (day_of_month == last_day)


# --- C. Seção de Missões do Dia ---
st.write("---")
st.subheader("🎯 Missões de Hoje")

sql_filter = """
SELECT quest_id, quest_name, reward_xp, reward_gold 
FROM master_quest_db 
WHERE status = 'Active' AND (
    frequency = 8 OR 
    frequency = ? OR 
    (? = 1 AND frequency = 10) OR 
    (? = 1 AND frequency = 11)
)
"""

today_quests = query_db(sql_filter, (numbers_weekday, is_month_first, is_month_last))

completed_ids = []
total_xp = 0
total_gold = 0

if not today_quests.empty:
    for index, row in today_quests.iterrows():
        is_done = st.checkbox(f"[{row['quest_id']}] {row['quest_name']} (+{row['reward_xp']} XP / +{row['reward_gold']} G)")
        if is_done:
            completed_ids.append(row['quest_id'])
            total_xp += row['reward_xp']
            total_gold += row['reward_gold']
else:
    st.info("Nenhuma missão agendada para hoje. Aproveite para descansar!")


# --- D. Seção de Resumo do Dia ---
st.write("---")
st.subheader("📝 Resumo do Dia (Daily Summary)")

st.code(f"Missões Concluídas: {', '.join(completed_ids) if completed_ids else 'Nenhuma'}\n"
        f"Total de XP de Hoje: {total_xp} XP\n"
        f"Total de Ouro de Hoje: {total_gold} Gold", language="text")

if st.button("💾 Salvar Resultados de Hoje no Banco de Dados"):
    if not completed_ids:
        st.warning("⚠️ Você não selecionou nenhuma missão concluída! Conclua pelo menos uma tarefa antes de salvar.")
    else:
        try:
            conn = sqlite3.connect("rpg-database.db")
            cursor = conn.cursor()
            
            weekday_names = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
            current_day_name = weekday_names[selected_date.weekday()]
            
            sql_insert = """
            INSERT OR REPLACE INTO quest_history_log (log_date, day_of_week, completed_ids, total_xp, total_gold)
            VALUES (?, ?, ?, ?, ?)
            """
            
            formatted_date = selected_date.strftime("%Y-%m-%d")
            cursor.execute(sql_insert, (
                formatted_date,
                current_day_name,
                ", ".join(completed_ids),
                total_xp,
                total_gold
            ))
            
            conn.commit()
            conn.close()
            
            st.balloons() # Efeito de balões para comemorar
            st.success(f"🎉 Resultados do dia [{formatted_date}] salvos com sucesso no SQLite!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar no banco de dados: {e}")


# --- E. Seção da Loja de Recompensas ---
st.write("---")
st.subheader("🛒 Loja de Recompensas Real (Reward Shop)")

menu_df = query_db("SELECT reward_item, price_gold FROM reward_menu")
item_list = menu_df['reward_item'].tolist()

if item_list:
    selected_item = st.selectbox("Escolha sua recompensa:", item_list)
    item_price = int(menu_df[menu_df['reward_item'] == selected_item]['price_gold'].iloc[0])
    st.info(f"💰 O preço de '{selected_item}' é **{item_price} Gold**. (Saldo atual: {current_remaining_gold} G)")
    
    if st.button("💳 Usar Ouro (Comprar Recompensa)"):
        if current_remaining_gold < item_price:
            st.error("❌ Ouro insuficiente! Conclua mais missões diárias para acumular riqueza.")
        else:
            try:
                conn = sqlite3.connect("rpg-database.db")
                cursor = conn.cursor()
                
                purchase_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                INSERT INTO reward_shop_log (purchase_date, reward_item, spent_gold)
                VALUES (?, ?, ?)
                """, (purchase_date_str, selected_item, item_price))
                
                conn.commit()
                conn.close()
                
                st.snow() # Efeito de neve para compras
                st.success(f"🎉 Você comprou '{selected_item}' com sucesso! Aproveite sua recompensa!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao usar a loja: {e}")
else:
    st.error("Nenhum produto registrado na loja.")