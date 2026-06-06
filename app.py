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
    
    # A. Tabela de missões master
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
    
    # B. Tabela de histórico de missões (로그 테이블)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quest_history_log (
        log_date TEXT PRIMARY KEY,
        day_of_week TEXT,
        completed_ids TEXT,
        total_xp INTEGER,
        total_gold INTEGER
    )
    """)
    
    # C. Tabela do menu de recompensas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reward_menu (
        reward_item TEXT PRIMARY KEY,
        price_gold INTEGER
    )
    """)
    
    # D. Tabela de histórico de compras
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reward_shop_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_date TEXT,
        reward_item TEXT,
        spent_gold INTEGER
    )
    """)
    
    # 🌟 [신설] E. Tabela de Configuração de Níveis (레벨 메커니즘 지하실 설정 테이블)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS level_config (
        level INTEGER PRIMARY KEY,
        required_xp INTEGER,
        title TEXT
    )
    """)
    
    # F. Dados iniciais das missões (최초 1회 샘플 주입)
    cursor.executemany("""
    INSERT OR IGNORE INTO master_quest_db VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Q2606-01', 'Alongamento matinal', 'E', 10, 5, 8, 'Active'),
        ('Q2606-02', 'Ler 3 páginas de um livro', 'N', 30, 15, 8, 'Active'),
        ('Q2606-03', 'Análise tática de futebol', 'H', 50, 25, 3, 'Active'),
        ('Q2606-04', 'Relatório de personal trainer', 'H', 50, 25, 11, 'Active')
    ])
    
    # G. Dados iniciais da loja
    cursor.executemany("""
    INSERT OR IGNORE INTO reward_menu VALUES (?, ?)
    """, [
        ('Comer Frango Frito 🍗', 500),
        ('1 Hora de YouTube 📱', 100),
        ('Assistir a um Filme na Netflix 🎬', 200),
        ('Ticket para Dormir até Tarde ⏰', 300)
    ])
    
    # 📊 H. 데이터베이스 기반 레벨 1~100 자동 규칙 대량 주입 (100만 XP 만렙 리밸런싱 패치)
    # 루프를 돌며 과학적으로 설계된 100개 레벨 스펙트럼을 테이블에 밀어 넣습니다.
    level_rules = []
    for lv in range(1, 101):
        if lv == 1: required = 0
        elif lv <= 10: required = (lv - 1) * 500
        elif lv <= 30: required = 5000 + (lv - 10) * 1200
        elif lv <= 60: required = 29000 + (lv - 30) * 5000
        elif lv <= 90: required = 179000 + (lv - 60) * 18000
        else: required = 719000 + (lv - 90) * 31200
        
        # 칭호 매핑 바인딩
        if lv == 100: title = "Deus da Alta Performance 🌌"
        elif lv >= 96: title = "Iluminado da Rotina 🧘"
        elif lv >= 91: title = "Ser de Luz Disciplinado ☀️"
        elif lv >= 81: title = "Soberano dos Hábitos 🌟"
        elif lv >= 71: title = "Lenda da Produtividade 📜"
        elif lv >= 61: title = "Conquistador Imparável ⛰️"
        elif lv >= 51: title = "Grande Mestre de Si Mesmo 👑"
        elif lv >= 41: title = "Vanguardista da Mente 🔮"
        elif lv >= 31: title = "Dominador do Tempo ⏳"
        elif lv >= 26: title = "Mestre do Auto-Controle 🧠"
        elif lv >= 21: title = "Comandante da Rotina 🎖️"
        elif lv >= 16: title = "Especialista em Foco 🎯"
        elif lv >= 11: title = "Arquiteto do Hábito 📐"
        elif lv >= 10: title = "Desbravador do Foco 🏔️"
        elif lv >= 9: title = "Caçador de Metas 🏹"
        elif lv >= 8: title = "Guerreiro da Constância 🛡️"
        elif lv >= 7: title = "Construidor de Disciplina 🏗️"
        elif lv >= 6: title = "Explorador de Rotinas 🧭"
        elif lv >= 5: title = "Transcendente da Produtividade 🌌"
        elif lv >= 4: title = "Mestre dos Hábitos ⚡"
        elif lv >= 3: title = "Líder da Rotina ⚔️"
        elif lv >= 2: title = "Praticante Dedicado 🏃"
        else: title = "Iniciante da Vida Saudável 🌱"
        
        level_rules.append((lv, required, title))
        
    cursor.executemany("INSERT OR IGNORE INTO level_config VALUES (?, ?, ?)", level_rules)
    
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

# 🧠 🤖 [핵심 진화: SQL 기반 실시간 레벨 매핑 로직]
# 내 누적 경험치보다 요구량이 낮거나 같은 레벨 중 가장 높은 레벨을 지하실에서 단 한 줄로 서치해 옵니다!
try:
    lvl_query = "SELECT level, title FROM level_config WHERE required_xp <= ? ORDER BY level DESC LIMIT 1"
    lvl_df = query_db(lvl_query, (total_accumulated_xp,))
    current_level = int(lvl_df['level'].iloc[0])
    character_title = str(lvl_df['title'].iloc[0])
except Exception:
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
        st.info("Nenhuma missão ativa agendada para hoje. Aproveite para descansar!")

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
# ⚙️ TAB 2: 퀘스트 관리자 영역
# ------------------------------------------
with tab_manage:
    st.subheader("🛠️ Painel do Administrador (퀘스트 관리자 관제탑)")
    
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
        
        st.info(f"🆔 **Código Gerado Automatically:** `{auto_generated_id}`")
        
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

    # 🔄 2. 기존 퀘스트 수정 양식
    else:
        st.markdown("### 🔄 Modificar Missão Existente (기존 퀘스트 정보 변경)")
        quest_options = all_quests['quest_id'].tolist()
        
        if quest_options:
            target_id = st.selectbox("Selecione o Código da Missão:", quest_options)
            
            selected_quest_data = all_quests[all_quests['quest_id'] == target_id].iloc[0]
            current_title = selected_quest_data['quest_name']
            current_status = selected_quest_data['status']
            current_diff = selected_quest_data['difficulty']
            
            st.warning(f"Modificando: **{current_title}**")
            
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                idx_status = ["Active", "Inactive"].index(current_status)
                new_status = st.selectbox("Novo Status (새 상태):", ["Active", "Inactive"], index=idx_status)
            with col_u2:
                idx_diff = ["E", "N", "H"].index(current_diff)
                new_diff = st.selectbox("Nova Dificuldade (새 난이도):", ["E", "N", "H"], index=idx_diff)
            
            updated_xp, updated_gold = diff_rewards[new_diff]
            st.write(f"📊 *Se salvar, as recompensas mudarão para:* **+{updated_xp} XP** / **+{updated_gold} Gold**")
            
            if st.button("💾 Atualizar Missão no Banco de Dados (변경사항 저장)"):
                try:
                    run_db_command("""
                        UPDATE master_quest_db 
                        SET status = ?, difficulty = ?, reward_xp = ?, reward_gold = ? 
                        WHERE quest_id = ?
                    """, (new_status, new_diff, updated_xp, updated_gold, target_id))
                    
                    st.success(f"⚙️ Missão [{target_id}] atualizada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar missão: {e}")
        else:
            st.info("Nenhuma missão cadastrada no sistema.")