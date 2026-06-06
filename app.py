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

def run_db_command(sql_command, params=()):
    conn = sqlite3.connect("rpg-database.db")
    cursor = conn.cursor()
    cursor.execute(sql_command, params)
    conn.commit()
    conn.close()

def init_log_table_safety():
    conn = sqlite3.connect("rpg-database.db")
    cursor = conn.cursor()
    
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
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quest_history_log (
        log_date TEXT PRIMARY KEY,
        day_of_week TEXT,
        completed_ids TEXT,
        total_xp INTEGER,
        total_gold INTEGER
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reward_menu (
        reward_item TEXT PRIMARY KEY,
        price_gold INTEGER
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reward_shop_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_date TEXT,
        reward_item TEXT,
        spent_gold INTEGER
    )
    """)
    
    cursor.executemany("""
    INSERT OR IGNORE INTO master_quest_db VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Q2606-01', 'Alongamento matinal', 'E', 10, 5, 8, 'Active'),
        ('Q2606-02', 'Ler 3 páginas de um livro', 'N', 30, 15, 8, 'Active'),
        ('Q2606-03', 'Análise tática de futebol', 'H', 50, 25, 3, 'Active'),
        ('Q2606-04', 'Relatório de personal trainer', 'H', 50, 25, 11, 'Active')
    ])
    
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

init_log_table_safety()


# ==========================================
# 📊 [Cálculo de Dados: Status Atual]
# ==========================================
try:
    stats_df = query_db("SELECT SUM(total_xp) as attr_xp, SUM(total_gold) as attr_gold FROM quest_history_log")
    total_accumulated_xp = int(stats_df['attr_xp'].iloc[0]) if pd.notna(stats_df['attr_xp'].iloc[0]) else 0
    total_earned_gold = int(stats_df['attr_gold'].iloc[0]) if pd.notna(stats_df['attr_gold'].iloc[0]) else 0
    
    shop_df = query_db("SELECT SUM(spent_gold) as attr_spent FROM reward_shop_log")
    total_spent_gold = int(shop_df['attr_spent'].iloc[0]) if pd.notna(shop_df['attr_spent'].iloc[0]) else 0
    
    current_remaining_gold = total_earned_gold - total_spent_gold
except Exception:
    total_accumulated_xp, total_earned_gold, current_remaining_gold = 0, 0, 0

if total_accumulated_xp >= 5000:
    current_level, character_title = 5, "Transcendente da Produtividade 🌌"
elif total_accumulated_xp >= 2500:
    current_level, character_title = 4, "Mestre dos Hábitos ⚡"
elif total_accumulated_xp >= 1200:
    current_level, character_title = 3, "Líder da Rotina ⚔️"
elif total_accumulated_xp >= 500:
    current_level, character_title = 2, "Praticante Dedicado 🏃"
else:
    current_level, character_title = 1, "Iniciante da Vida Saudável 🌱"


# ==========================================
# 🖥️ [Frontend UI: Abas de Navegação]
# ==========================================
st.title("👑 Painel de RPG Pessoal")

tab_play, tab_manage = st.tabs(["🎮 Jogar (플레이)", "⚙️ Gerenciador de Missões (퀘스트 관리)"])

# ------------------------------------------
# 🎮 TAB 1: 플레이 대시보드 영역
# ------------------------------------------
with tab_play:
    st.subheader("👤 Status do Personagem")
    status_col1, status_col2, status_col3 = st.columns(3)
    with status_col1:
        st.metric("Nível Atual", f"LV. {current_level}")
    with status_col2:
        st.metric("XP Acumulado", f"{total_accumulated_xp} XP")
    with status_col3:
        st.metric("Ouro Disponível", f"{current_remaining_gold} G")
    st.markdown(f"**Seu Título Honorário Atual:** `{character_title}`")

    st.write("---")
    st.subheader("⚙️ Painel de Controle")
    selected_date = st.date_input("Selecione uma data", datetime.now(), key="play_date")

    day_of_week = selected_date.weekday() 
    numbers_weekday = 1 if day_of_week == 6 else day_of_week + 2
    day_of_month = selected_date.day
    _, last_day = calendar.monthrange(selected_date.year, selected_date.month)

    is_month_first = (day_of_month == 1)
    is_month_last = (day_of_month == last_day)

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
            is_done = st.checkbox(f"[{row['quest_id']}] {row['quest_name']} (+{row['reward_xp']} XP / +{row['reward_gold']} G)", key=f"q_{row['quest_id']}")
            if is_done:
                completed_ids.append(row['quest_id'])
                total_xp += row['reward_xp']
                total_gold += row['reward_gold']
    else:
        st.info("Nenhuma missão activa agendada para hoje. Aproveite para descansar!")

    st.write("---")
    st.subheader("📝 Resumo do Dia")
    st.code(f"Missões Concluídas: {', '.join(completed_ids) if completed_ids else 'Nenhuma'}\n"
            f"Total de XP de Hoje: {total_xp} XP\n"
            f"Total de Ouro de Hoje: {total_gold} Gold", language="text")

    if st.button("💾 Salvar Resultados de Hoje", key="btn_save_daily"):
        if not completed_ids:
            st.warning("⚠️ Você não selecionou nenhuma missão concluída!")
        else:
            try:
                weekday_names = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
                current_day_name = weekday_names[selected_date.weekday()]
                
                sql_insert = """
                INSERT OR REPLACE INTO quest_history_log (log_date, day_of_week, completed_ids, total_xp, total_gold)
                VALUES (?, ?, ?, ?, ?)
                """
                formatted_date = selected_date.strftime("%Y-%m-%d")
                run_db_command(sql_insert, (formatted_date, current_day_name, ", ".join(completed_ids), total_xp, total_gold))
                
                st.balloons()
                st.success(f"🎉 Resultados do dia [{formatted_date}] salvos com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")

    st.write("---")
    st.subheader("🛒 Loja de Recompensas Real")
    menu_df = query_db("SELECT reward_item, price_gold FROM reward_menu")
    item_list = menu_df['reward_item'].tolist()

    if item_list:
        selected_item = st.selectbox("Escolha sua recompensa:", item_list, key="shop_select")
        item_price = int(menu_df[menu_df['reward_item'] == selected_item]['price_gold'].iloc[0])
        st.info(f"💰 Preço: {item_price} Gold. (Saldo: {current_remaining_gold} G)")
        
        if st.button("💳 Usar Ouro (Comprar Recompensa)", key="btn_buy_reward"):
            if current_remaining_gold < item_price:
                st.error("❌ Ouro insuficiente!")
            else:
                try:
                    purchase_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    run_db_command("INSERT INTO reward_shop_log (purchase_date, reward_item, spent_gold) VALUES (?, ?, ?)", 
                                   (purchase_date_str, selected_item, item_price))
                    st.snow()
                    st.success(f"🎉 Você comprou '{selected_item}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao usar a loja: {e}")


# ------------------------------------------
# ⚙️ TAB 2: 퀘스트 관리자 영역 (★난이도 수정 기능 추가 탑재)
# ------------------------------------------
with tab_manage:
    st.subheader("🛠️ Painel do Administrador (퀘스트 관리자 관제탑)")
    
    # 난이도 규칙 사전 정의 (E: Easy, N: Normal, H: Hard)
    diff_rewards = {"E": (10, 5), "N": (30, 15), "H": (50, 25)}
    
    all_quests = query_db("""
        SELECT quest_id, quest_name, difficulty, reward_xp, reward_gold, frequency, status 
        FROM master_quest_db
        ORDER BY status ASC, quest_id DESC
    """)
    
    def style_inactive_rows(row):
        if row['status'] == 'Inactive':
            return ['color: #A0A0A0; font-style: italic;'] * len(row)
        return [''] * len(row)
    
    st.markdown("### 📜 Lista de Todas as Missões (현재 등록된 전체 퀘스트)")
    styled_df = all_quests.style.apply(style_inactive_rows, axis=1)
    st.dataframe(styled_df, use_container_width=True)
    
    st.write("---")
    
    manage_action = st.radio("Selecione uma ação (작업 선택):", ["➕ Adicionar Nova Missão (퀘스트 추가)", "🔄 Modificar Missão (퀘스트 수정 및 활성/비활성)"], horizontal=True)
    
    # ➕ 1. 새로운 퀘스트 추가 양식
    if "➕" in manage_action:
        st.markdown("### ➕ Criar Nova Missão (새 퀘스트 만들기)")
        
        today_str = datetime.now().strftime("%y%m%d")
        id_prefix = f"Q{today_str}-"
        
        try:
            count_df = query_db("SELECT COUNT(*) as cnt FROM master_quest_db WHERE quest_id LIKE ?", (f"{id_prefix}%",))
            today_count = int(count_df['cnt'].iloc[0])
        except Exception:
            today_count = 0
            
        next_sequence = today_count + 1
        auto_generated_id = f"{id_prefix}{next_sequence:02d}"
        
        st.info(f"🆔 **Código Gerado Automaticamente:** `{auto_generated_id}`")
        
        new_name = st.text_input("Nome da Missão (퀘스트 내용)", placeholder="Fazer academia por 1 hora")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            new_diff = st.selectbox("Dificuldade (난이도)", ["E", "N", "H"])
        with col_m2:
            new_freq = st.selectbox("Frequência (반복 요일 선택)", [
                ("Diário (매일)", 8),
                ("Domingo (일요일)", 1), ("Segunda (월요일)", 2), ("Terça (화요일)", 3),
                ("Quarta (수요일)", 4), ("Quinta (목요일)", 5), ("Sexta (금요일)", 6), ("Sábado (토요일)", 7),
                ("Início do Mês (월초)", 10), ("Fim do Mês (월말)", 11)
            ], format_func=lambda x: x[0])
            
        xp_reward, gold_reward = diff_rewards[new_diff]
        st.write(f"💡 *Esta dificuldade concederá automaticamente:* **+{xp_reward} XP** / **+{gold_reward} Gold**")
        
        if st.button("🚀 Registrar Nova Missão (데이터베이스에 추가)"):
            if not new_name:
                st.error("❌ O nome da missão é obrigatório!")
            else:
                try:
                    run_db_command("""
                    INSERT INTO master_quest_db (quest_id, quest_name, difficulty, reward_xp, reward_gold, frequency, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'Active')
                    """, (auto_generated_id, new_name, new_diff, xp_reward, gold_reward, new_freq[1]))
                    st.success(f"🎉 Missão [{auto_generated_id}] registrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro no banco de dados: {e}")

    # 🔄 2. 기존 퀘스트 수정 양식 (★상태 + 난이도 동시 수정 엔진 업그레이드)
    else:
        st.markdown("### 🔄 Modificar MissãoExistente (기존 퀘스트 정보 변경)")
        quest_options = all_quests['quest_id'].tolist()
        
        if quest_options:
            target_id = st.selectbox("Selecione o Código da Missão:", quest_options)
            
            # 선택된 퀘스트의 현재 데이터 추출
            selected_quest_data = all_quests[all_quests['quest_id'] == target_id].iloc[0]
            current_title = selected_quest_data['quest_name']
            current_status = selected_quest_data['status']
            current_diff = selected_quest_data['difficulty']
            
            st.warning(f"Modificando: **{current_title}**")
            
            # 수정 레이아웃 구성 (상태와 난이도를 나란히 배치)