import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
import io
import json
import urllib.request

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Gerador de Etiquetas - WEN SZO", layout="wide")

st.markdown("""
    <style>
    .css-1d391kg {background-color: #f0f2f6;}
    .stButton>button {background-color: #00579D; color: white; border-radius: 5px;}
    .stButton>button:hover {background-color: #003a6b; color: white;}
    h1, h2, h3 {color: #00579D;}
    </style>
""", unsafe_allow_html=True)

st.title("📦 Gerador de Etiquetas QR Code - Almoxarifado")

# ==========================================
# PASTAS, ARQUIVOS E FONTE (CORREÇÃO NUVEM)
# ==========================================
LOGO_DIR = "logos"
CONFIG_FILE = "configuracoes.json"
FONT_PATH = "Roboto-Regular.ttf"

if not os.path.exists(LOGO_DIR):
    os.makedirs(LOGO_DIR)

# Baixa uma fonte TTF de verdade caso o servidor Linux (Nuvem) não tenha a Arial
if not os.path.exists(FONT_PATH):
    try:
        url_fonte = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf"
        urllib.request.urlretrieve(url_fonte, FONT_PATH)
    except:
        pass # Se falhar, usa a de emergência

def listar_logos():
    return [f for f in os.listdir(LOGO_DIR) if f.endswith(('png', 'jpg', 'jpeg'))]

def mm_para_px(mm):
    return int((mm * 300) / 25.4)

# Função Inteligente de Quebra de Texto
def quebrar_texto(texto, fonte, max_largura, draw):
    if not texto: return ""
    linhas = []
    palavras = texto.split()
    linha_atual = ""
    
    for palavra in palavras:
        teste_linha = f"{linha_atual} {palavra}".strip()
        largura_teste = draw.textbbox((0, 0), teste_linha, font=fonte)[2]
        
        if largura_teste <= max_largura:
            linha_atual = teste_linha
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra
            
    if linha_atual:
        linhas.append(linha_atual)
        
    return "\n".join(linhas)

# ==========================================
# SISTEMA DE SALVAR PADRÕES (JSON)
# ==========================================
def carregar_json():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_json(dados):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

configs_salvas = carregar_json()
logos_disponiveis = ["Nenhum"] + listar_logos()

valores_padrao = {
    'largura_mm': 60, 'altura_mm': 30, 'cor_texto': '#000000', 
    'tamanho_fonte': 35, 'tamanho_fonte_extra': 20, 
    'cols_por_linha_a4': 5, 'mostrar_borda': True, 
    'logo_superior': 'Nenhum', 'logo_inferior': 'Nenhum',
    'pos_x_texto_mm': 2, 'pos_y_texto_mm': 5, 
    'pos_x_extra_mm': 2, 'pos_y_extra_mm': 15,
    'tamanho_qr_mm': 20, 'pos_x_qr_mm': 10, 'pos_y_qr_mm': 25, 
    'largura_logo_sup_mm': 15, 'pos_x_sup_mm': 42, 'pos_y_sup_mm': 2,
    'largura_logo_inf_mm': 10, 'pos_x_inf_mm': 45, 'pos_y_inf_mm': 20, 
    'margem_pagina_x_mm': 10, 'margem_pagina_y_mm': 10, 'margem_x_mm': 2, 'margem_y_mm': 2
}

for key, val in valores_padrao.items():
    if key not in st.session_state:
        st.session_state[key] = val

st.sidebar.header("💾 Meus Padrões Salvos")

if configs_salvas:
    opcao_carregar = st.sidebar.selectbox("Selecionar um padrão salvo:", ["-- Escolha --"] + list(configs_salvas.keys()))
    if st.sidebar.button("⬇️ Carregar Padrão Selecionado"):
        if opcao_carregar != "-- Escolha --":
            padrao = configs_salvas[opcao_carregar]
            for k, v in padrao.items():
                if k in ['logo_superior', 'logo_inferior'] and v not in logos_disponiveis:
                    st.session_state[k] = "Nenhum"
                else:
                    st.session_state[k] = v
            st.rerun()

with st.sidebar.expander("➕ Salvar Configuração Atual"):
    nome_novo_padrao = st.text_input("Nome do Padrão (Ex: Padrão Z1 60x30)")
    if st.button("💾 Salvar Padrão"):
        if nome_novo_padrao:
            configs_salvas[nome_novo_padrao] = {k: st.session_state[k] for k in valores_padrao.keys()}
            salvar_json(configs_salvas)
            st.success(f"Padrão '{nome_novo_padrao}' salvo com sucesso!")
            st.rerun()
        else:
            st.error("Digite um nome para o padrão.")

# ==========================================
# BARRA LATERAL - CONTROLES
# ==========================================
st.sidebar.markdown("---")
st.sidebar.header("📏 Tamanho Físico (1 Etiqueta)")
largura_mm = st.sidebar.number_input("Largura (mm)", 10, 210, key="largura_mm")
altura_mm = st.sidebar.number_input("Altura (mm)", 10, 297, key="altura_mm")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configurações Visuais")
mostrar_borda = st.sidebar.checkbox("Imprimir linha de borda", key="mostrar_borda")
cor_texto = st.sidebar.color_picker("Cor do Texto", key="cor_texto")
tamanho_fonte = st.sidebar.slider("Tamanho Fonte Principal (QR)", 10, 100, key="tamanho_fonte")
tamanho_fonte_extra = st.sidebar.slider("Tamanho Fonte Texto Extra", 5, 100, key="tamanho_fonte_extra")

st.sidebar.markdown("---")
st.sidebar.header("🖼️ Logotipos")
novo_logo = st.sidebar.file_uploader("Upload de Novo Logo", type=['png', 'jpg', 'jpeg'])
if novo_logo is not None:
    caminho_salvar = os.path.join(LOGO_DIR, novo_logo.name)
    with open(caminho_salvar, "wb") as f:
        f.write(novo_logo.getbuffer())
    st.sidebar.success("Logo salvo! Atualize a página.")

logo_superior = st.sidebar.selectbox("Logo Superior", logos_disponiveis, key="logo_superior")
logo_inferior = st.sidebar.selectbox("Logo Inferior", logos_disponiveis, key="logo_inferior")

with st.sidebar.expander("📍 Posições e Tamanhos (Ajuste Fino)"):
    st.write("**Texto Principal (Igual ao QR Code)**")
    pos_x_texto_mm = st.number_input("Posição X (Texto Principal)", 0, 200, key="pos_x_texto_mm")
    pos_y_texto_mm = st.number_input("Posição Y (Texto Principal)", 0, 200, key="pos_y_texto_mm")
    
    st.write("**Texto Extra (Descrição Visual)**")
    pos_x_extra_mm = st.number_input("Posição X (Texto Extra)", 0, 200, key="pos_x_extra_mm")
    pos_y_extra_mm = st.number_input("Posição Y (Texto Extra)", 0, 200, key="pos_y_extra_mm")

    st.write("**QR Code**")
    tamanho_qr_mm = st.number_input("Tamanho QR (mm)", 5, 100, key="tamanho_qr_mm")
    pos_x_qr_mm = st.number_input("Posição X (QR)", 0, 200, key="pos_x_qr_mm")
    pos_y_qr_mm = st.number_input("Posição Y (QR)", 0, 200, key="pos_y_qr_mm")
    
    st.write("**Logo Superior**")
    largura_logo_sup_mm = st.number_input("Largura Logo Sup", 1, 100, key="largura_logo_sup_mm")
    pos_x_sup_mm = st.number_input("Posição X Logo Sup", 0, 200, key="pos_x_sup_mm")
    pos_y_sup_mm = st.number_input("Posição Y Logo Sup", 0, 200, key="pos_y_sup_mm")

    st.write("**Logo Inferior**")
    largura_logo_inf_mm = st.number_input("Largura Logo Inf", 1, 100, key="largura_logo_inf_mm")
    pos_x_inf_mm = st.number_input("Posição X Logo Inf", 0, 200, key="pos_x_inf_mm")
    pos_y_inf_mm = st.number_input("Posição Y Logo Inf", 0, 200, key="pos_y_inf_mm")

st.sidebar.markdown("---")
st.sidebar.header("📄 Margens da Folha A4")
cols_por_linha_a4 = st.sidebar.slider("Etiquetas por Linha", 1, 10, key="cols_por_linha_a4")
margem_pagina_x_mm = st.sidebar.number_input("Esquerda do Papel (mm)", 0, 100, key="margem_pagina_x_mm")
margem_pagina_y_mm = st.sidebar.number_input("Superior do Papel (mm)", 0, 100, key="margem_pagina_y_mm")
margem_x_mm = st.sidebar.slider("Espaço Horizontal (mm)", 0, 50, key="margem_x_mm")
margem_y_mm = st.sidebar.slider("Espaço Vertical (mm)", 0, 50, key="margem_y_mm")

# ==========================================
# ÁREA PRINCIPAL
# ==========================================
st.write("### 📍 Dados da Etiqueta")
st.info("💡 **Dica:** Copie duas colunas do Excel e cole abaixo. O sistema coloca a Coluna 1 no QR Code e a Coluna 2 como Texto Extra.")

enderecos_input = st.text_area("Cole os dados aqui:", "P-05 ; BUCHA VALVULA 16X40\nP-06 ; PARAFUSO SEXTAVADO INOX M24\nP-07 ; FLANGE DE VEDACAO DN150")

dados_etiquetas = []
for linha in enderecos_input.split('\n'):
    linha = linha.strip()
    if not linha: continue
    
    if "\t" in linha:
        partes = linha.split("\t", 1)
        dados_etiquetas.append({"qr": partes[0].strip(), "extra": partes[1].strip()})
    elif ";" in linha:
        partes = linha.split(";", 1)
        dados_etiquetas.append({"qr": partes[0].strip(), "extra": partes[1].strip()})
    else:
        dados_etiquetas.append({"qr": linha, "extra": ""})

def criar_etiqueta_imagem(dados):
    larg_px, alt_px = mm_para_px(largura_mm), mm_para_px(altura_mm)
    img = Image.new('RGB', (larg_px, alt_px), color='white')
    draw = ImageDraw.Draw(img)
    
    if mostrar_borda:
        draw.rectangle([(0, 0), (larg_px-1, alt_px-1)], outline="black", width=1)
    
    # A MÁGICA DA FONTE NA NUVEM ESTÁ AQUI
    try: 
        if os.path.exists(FONT_PATH):
            fonte_princ = ImageFont.truetype(FONT_PATH, tamanho_fonte)
            fonte_extra = ImageFont.truetype(FONT_PATH, tamanho_fonte_extra)
        else:
            fonte_princ = ImageFont.truetype("arial.ttf", tamanho_fonte)
            fonte_extra = ImageFont.truetype("arial.ttf", tamanho_fonte_extra)
    except: 
        fonte_princ = ImageFont.load_default()
        fonte_extra = ImageFont.load_default()
    
    # Desenha o texto principal
    draw.text((mm_para_px(pos_x_texto_mm), mm_para_px(pos_y_texto_mm)), dados["qr"], fill=cor_texto, font=fonte_princ)
    
    # Desenha o texto extra (com quebra de linha inteligente)
    if dados["extra"]:
        pos_x_extra_px = mm_para_px(pos_x_extra_mm)
        pos_y_extra_px = mm_para_px(pos_y_extra_mm)
        margem_seguranca_direita_px = mm_para_px(2) 
        largura_maxima_permitida = larg_px - pos_x_extra_px - margem_seguranca_direita_px
        
        texto_formatado = quebrar_texto(dados["extra"], fonte_extra, largura_maxima_permitida, draw)
        draw.text((pos_x_extra_px, pos_y_extra_px), texto_formatado, fill=cor_texto, font=fonte_extra, spacing=4)
    
    # QR Code
    qr_px = mm_para_px(tamanho_qr_mm)
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(dados["qr"])
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").resize((qr_px, qr_px))
    img.paste(img_qr, (mm_para_px(pos_x_qr_mm), mm_para_px(pos_y_qr_mm)))
    
    # Logos
    if logo_superior != "Nenhum" and logo_superior in logos_disponiveis:
        l_img = Image.open(os.path.join(LOGO_DIR, logo_superior)).convert("RGBA")
        l_px = mm_para_px(largura_logo_sup_mm)
        l_img = l_img.resize((l_px, int(l_img.height * (l_px/l_img.width))), Image.Resampling.LANCZOS)
        img.paste(l_img, (mm_para_px(pos_x_sup_mm), mm_para_px(pos_y_sup_mm)), l_img)
        
    if logo_inferior != "Nenhum" and logo_inferior in logos_disponiveis:
        l_img = Image.open(os.path.join(LOGO_DIR, logo_inferior)).convert("RGBA")
        l_px = mm_para_px(largura_logo_inf_mm)
        l_img = l_img.resize((l_px, int(l_img.height * (l_px/l_img.width))), Image.Resampling.LANCZOS)
        img.paste(l_img, (mm_para_px(pos_x_inf_mm), mm_para_px(pos_y_inf_mm)), l_img)
        
    return img

st.write("### 👁️ Pré-visualização")
if dados_etiquetas: 
    qtd_prev = min(len(dados_etiquetas), 2)
    cols_prev = st.columns(qtd_prev)
    for i in range(qtd_prev):
        with cols_prev[i]:
            st.image(criar_etiqueta_imagem(dados_etiquetas[i]), caption=f"Etiqueta {i+1}: {largura_mm}mm x {altura_mm}mm")

st.write("### 🖨️ Exportar para Impressão")
col1, col2 = st.columns(2)

with col1:
    if st.button("📄 Baixar PDF (Folha A4)"):
        if not dados_etiquetas: 
            st.error("Insira dados para gerar as etiquetas!")
        else:
            A4_LARGURA_PX, A4_ALTURA_PX = 2480, 3508
            paginas_pdf = []
            folha = Image.new('RGB', (A4_LARGURA_PX, A4_ALTURA_PX), 'white')
            x_atual, y_atual = mm_para_px(margem_pagina_x_mm), mm_para_px(margem_pagina_y_mm)
            etiquetas_na_linha = 0
            
            for dados in dados_etiquetas:
                etq = criar_etiqueta_imagem(dados)
                if x_atual + etq.width > (A4_LARGURA_PX - mm_para_px(margem_pagina_x_mm)) or etiquetas_na_linha >= cols_por_linha_a4:
                    x_atual = mm_para_px(margem_pagina_x_mm)
                    y_atual += etq.height + mm_para_px(margem_y_mm)
                    etiquetas_na_linha = 0
                if y_atual + etq.height > (A4_ALTURA_PX - mm_para_px(margem_pagina_y_mm)):
                    paginas_pdf.append(folha)
                    folha = Image.new('RGB', (A4_LARGURA_PX, A4_ALTURA_PX), 'white')
                    x_atual, y_atual = mm_para_px(margem_pagina_x_mm), mm_para_px(margem_pagina_y_mm)
                    etiquetas_na_linha = 0
                    
                folha.paste(etq, (x_atual, y_atual))
                x_atual += etq.width + mm_para_px(margem_x_mm)
                etiquetas_na_linha += 1
                
            paginas_pdf.append(folha)
            pdf_bytes = io.BytesIO()
            paginas_pdf[0].save(pdf_bytes, format='PDF', resolution=300.0, save_all=True, append_images=paginas_pdf[1:])
            pdf_bytes.seek(0)
            st.download_button("📥 Baixar PDF A4", data=pdf_bytes, file_name="etiquetas_A4.pdf", mime="application/pdf")

with col2:
    if st.button("🖨️ Baixar PDF (Etiquetas Individuais)"):
        if not dados_etiquetas: 
            st.error("Insira dados para gerar as etiquetas!")
        else:
            pags = []
            for dados in dados_etiquetas:
                pags.append(criar_etiqueta_imagem(dados))
                
            pdf_bytes = io.BytesIO()
            pags[0].save(pdf_bytes, format='PDF', resolution=300.0, save_all=True, append_images=pags[1:])
            pdf_bytes.seek(0)
            st.download_button("📥 Baixar PDF Individual (Zebra)", data=pdf_bytes, file_name="etiquetas_individuais.pdf", mime="application/pdf")
