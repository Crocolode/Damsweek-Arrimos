# Importando bibliotecas necessárias
import math
import numpy as np
import subprocess
import sys
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
import plotly.graph_objects as go
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Função para instalar pré-requisitos
def verificar_instalar_requisitos():
    """
    Verifica se os pacotes necessários estão instalados e os instala se necessário
    """
    requisitos = ['plotly', 'numpy']
    
    def instalar_pacote(pacote):
        print(f"Instalando {pacote}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
            print(f"{pacote} instalado com sucesso!")
            return True
        except subprocess.CalledProcessError:
            print(f"Erro ao instalar {pacote}. Por favor, instale manualmente usando: pip install {pacote}")
            return False

    todos_instalados = True
    for req in requisitos:
        try:
            __import__(req)
            print(f"{req} já está instalado.")
        except ImportError:
            print(f"{req} não encontrado.")
            if not instalar_pacote(req):
                todos_instalados = False
    
    if not todos_instalados:
        print("\nAlguns pacotes não puderam ser instalados. Por favor, instale-os manualmente.")
        sys.exit(1)
    
    print("\nTodos os requisitos estão instalados!")
    return True

def dimensionar_muro_arrimo_flexao(h, b, d, gamma_solo_sat, gamma_solo_sub, phi, fck, fyk, ka, h_agua=0):
    print("=== Dimensionamento de Muro de Arrimo à Flexão ===")
    
    # Cálculo do empuxo passivo (Teoria de Rankine)
    ep = 0.5 * gamma_solo_sat * h**2 * ka  # Empuxo passivo total
    
    # Empuxo de água (caso haja água)
    e_agua = 0.5 * 10 * h_agua**2 # Gamma da água = 10 kN/m³ (Eletrobrás, 2003)

    # Empuxo total
    ep_total = ep + e_agua     # Utilizar para armadura de cisalhamento? 
    
    # Momento fletor na base
    momento = ep * h/3 + e_agua * h_agua/3 # kN.m/m 
    
    # Dimensionamento estrutural
    # d = h/12  # Altura útil estimada - Não usei esse na última revisão
    fcd = fck/1.4  # Resistência de cálculo do concreto
    fyd = fyk/1.15  # Resistência de cálculo do aço
    
    # Cálculo da área de aço necessária
    # Realiza cálculo resumido de armadura (armadura simples)

    # print(momento, b , d, fcd)  
    a = (momento * 100 / (0.425 * 100 * (d*100-5)**2 * fcd / 10))
    # print(a)
    # 0.425 * b * d * d * fcd / 10
    x = 1.25*d * (1 - (1 - a)**0.5)
    x_d = x/d
    # print(x/(h-d))

    if x/(h-d) < 0:
        print("Domínio 1: x é negativo.")
    elif 0 <= x/(h-d) <= 0.25:
        print("Domínio 2: x está entre 0 e 0.25.")
    elif 0.25 < x/(h-d) <= 0.45:
        print("Domínio 3: x está entre 0.25 e 0.45.")
    else:
        print("Domínio 4: x é maior que 0.45.")

    # Verificar se kmd está dentro do limite
    if x/(h-d) > 0.45:
        print("ALERTA: Momento muito grande para a seção - Recomendado aumentar a altura útil!")
        return

    as_calc = momento * 1.4 / (((d * 100-5)-0.4 * x) * fyd) * 1000  # Área de aço calculada em cm²
    
    # Área de aço mínima
    as_min = 0.15/100 * b * h * 100  # cm²
    
    # Área de aço final
    as_final = round(max(as_calc, as_min), 2) # Pega o maior entre o mínimo e calculado
    
    # Apresentação dos resultados
    print("\n=== Resultados ===")
    print(f"Empuxo passivo total: {ep:.2f} kN/m")
    print(f"Momento fletor na base: {momento:.2f} kN.m/m")
    print(f"Área de aço necessária: {as_final:.2f} cm²/m")
    
    # Sugestão de armadura
    print("\nSugestão de armadura:")
    diametros = [5, 6.3, 8, 10, 12.5, 16, 20, 25, 32]  # diâmetros disponíveis em mm
    if as_final > 0:  # Verifica se a área de aço final é válida
        for dia_barra in diametros:
            area_barra = math.pi * (dia_barra/10)**2 / 4  # área de uma barra em cm²
            espacamento = area_barra * 100 / as_final
            
            # Aplicar limites (acha espaçamentos entre 5 e 20 cm) mas verificar se atende a área necessária
            espacamento_ajustado = max(5, min(espacamento, 20))
            
            # Verificar se com o espaçamento ajustado a área é suficiente
            if (area_barra * 100 / espacamento_ajustado) >= as_final:
                print(f"Usar φ {dia_barra}mm a cada {espacamento_ajustado:.1f}cm")
                break
    else:
        print("Área de aço necessária é inválida.")
    
    return {
        'dia_barra': dia_barra,
        'espacamento': espacamento_ajustado,
        'as_final': as_final,
        'as_min': as_min,
        'as_calc': as_calc,
        'momento': momento,
        'x_d': x_d,
        'fck': fck
        }

def calcular_peso_terra_montante(h, b_mont, gamma_solo_sat, gamma_solo_sub, beta=0):
    """
    Calcula o peso de terra sobre a laje de montante do muro
    
    Parâmetros:
    h: altura do muro (m)
    b_mont: largura da base a montante (m)
    gamma_solo: peso específico do solo (kN/m³) 
    beta: ângulo de inclinação do terreno (graus)
    
    Retorna:
    peso_terra: peso total do solo sobre a laje (kN/m)
    x_cg: posição do centro de gravidade em relação à face do muro (m)
    volume_aterro: volume de aterro (m³)
    volume_corte: volume de corte (m³)
    """
    # Conversão do ângulo beta para radianos
    beta_rad = math.radians(beta)
    
    # Área do solo retangular sobre a laje
    area_ret = h * b_mont
    
    # Cálculo do volume de corte simplificado
    volume_corte = b_mont * h + (h - 1)**2 / 2 if h > 1 else b_mont * h  # Considerando escavação em 45º
    
    # Cálculo do volume de aterro
    area_tri = 0
    if beta != 0:
        altura_tri = b_mont * math.tan(beta_rad)
        area_tri = b_mont * altura_tri / 2
    
    # Peso total do solo
    peso_terra = area_ret * gamma_solo_sat + volume_corte * gamma_solo_sat
    
    # Cálculo do centro de gravidade
    momento_ret = (b_mont/2) * area_ret * gamma_solo_sat
    momento_corte = (b_mont / 2) * volume_corte * gamma_solo_sat
    x_cg = (momento_ret + momento_corte) / peso_terra
    
    # Cálculo do volume de aterro
    volume_aterro = peso_terra / gamma_solo_sat  # Volume de aterro considerando a área triangular
    
    return peso_terra, x_cg, volume_aterro, volume_corte  # Retornando também os volumes de aterro e corte

def plotar_muro_arrimo(b_jus, b_mon, h, d, as_final, gamma_solo_sat, gamma_solo_sub, tensao_max, pressao_adm, resultados_estabilidade, resultados_dimensionamento):
    """
    Plota o diagrama do muro de arrimo com armadura
    
    Parâmetros:
    b_jus: largura da base a jusante (m)
    b_mon: largura da base a montante (m)
    h: altura total do muro (m)
    d: altura útil (m)
    as_final: área de aço final (cm²)
    gamma_solo_sat: peso específico do solo saturado (kN/m³)
    gamma_solo_sub: peso específico do solo submerso (kN/m³)
    tensao_max: tensão máxima na base (kN/m²)
    pressao_adm: pressão admissível do solo (kN/m²)
    resultados_estabilidade: dicionário com resultados da verificação de estabilidade
    """
    plt.close('all')  # Fecha todas as figuras existentes
    # Extrair dados do dicionário de resultados
    nivel_agua = resultados_estabilidade.get('nivel_agua', 0)
    gamma_agua = resultados_estabilidade.get('gamma_agua', 10)
    sobrecarga_mon = resultados_estabilidade.get('sobrecarga_mon', 0)
    peso_muro = resultados_estabilidade.get('peso_muro', 0)
    peso_solo = resultados_estabilidade.get('peso_solo', 0)
    peso_solo_sat = resultados_estabilidade.get('peso_solo_sat', 0)
    peso_solo_sub = resultados_estabilidade.get('peso_solo_sub', 0)
    peso_agua = resultados_estabilidade.get('peso_agua', 0)
    peso_sobre = resultados_estabilidade.get('peso_sobre', 0)
    e0 = resultados_estabilidade.get('e0', 0)
    e_agua = resultados_estabilidade.get('e_agua', 0)
    braco_e0 = resultados_estabilidade.get('braco_e0', 0)
    mt = resultados_estabilidade.get('mt', 0)
    me = resultados_estabilidade.get('me', 0)
    me_cg = resultados_estabilidade.get('me_cg', 0)
    forca_normal = resultados_estabilidade.get('forca_normal', 0)
    cg_base = resultados_estabilidade.get('cg_base', 0)
    e0_agua = resultados_estabilidade.get('e0_agua', 0) 
    braco_agua_PT = resultados_estabilidade.get('braco_agua_PT', 0)
    e0_solo_sat = resultados_estabilidade.get('e0_solo_sat', 0)
    braco_solo_sat_PT = resultados_estabilidade.get('braco_solo_sat_PT', 0)
    e0_solo_sub = resultados_estabilidade.get('e0_solo_sub', 0)
    braco_solo_sub_PT = resultados_estabilidade.get('braco_solo_sub_PT', 0)
    tensao_max = resultados_estabilidade.get('tensao_max', 0)
    tensao_min = resultados_estabilidade.get('tensao_min', 0)
    x_sobre = resultados_estabilidade.get('x_sobre', 0)
    
    # Ajustar escala dos empuxos para melhor visualização
    empuxo_max = max(e0, e0_agua, e0_solo_sat, e0_solo_sub)
    empuxo_scale = (b_mon + b_jus) / empuxo_max if empuxo_max > 0 else 0.05
    
    # Criar figura com dois subplots lado a lado
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))
    
    # Plotar a seção do muro de arrimo no subplot da esquerda
    ax1.plot([b_jus, b_jus, b_jus - d, b_jus - d, 0], [b_jus, h, h, 0, 0], color='gray', linewidth=2)  # Muro
    ax1.fill_between([0, b_mon+b_jus], 0, d, color='gainsboro', alpha=0.5)  # Área da base
    ax1.fill_between([b_jus - d, b_jus], b_jus, h, color='gainsboro', alpha=0.5)  # Área do muro
    ax1.plot([0, 0, 0, b_mon+b_jus, 0], [d, 0, 0, d, d], color='gainsboro', linewidth=2)  # Contorno da base
    ax1.fill_between([0, 0], b_jus, d, color='gainsboro', alpha=0.5)  # Área do muro
    ax1.fill_between([b_jus, b_mon+b_jus], d, h, color='saddlebrown', alpha=0.5, label='Solo')  # Terra acima da base
    
    # Adicionar solo submerso se houver nível d'água
    if nivel_agua > 0:
        ax1.fill_between([b_jus, b_mon+b_jus], d, nivel_agua, color='lightblue', alpha=0.3, label='Solo Submerso')
        # Adicionar linha do nível d'água
        ax1.plot([b_jus, b_mon+b_jus], [nivel_agua, nivel_agua], 'b--', linewidth=1, label='Nível d\'água')
    
    # Adicionar empuxos
    if nivel_agua > 0:
        # Empuxo do solo saturado
        pontos_empuxo_solo = [
            [b_mon + b_jus, 0],
            [b_mon + b_jus, h],
            [b_mon + b_jus + e0_solo_sat*empuxo_scale, nivel_agua],
            [b_mon + b_jus + e0*empuxo_scale, 0]
        ]
        ax1.add_patch(plt.Polygon(pontos_empuxo_solo, closed=True, fill=True, color='red', alpha=0.2, label='Empuxo do Solo'))
        
        # Empuxo da água
        pontos_empuxo_agua = [
            [b_mon + b_jus + e0_solo_sat*empuxo_scale, nivel_agua],
            [b_mon + b_jus + (e0_solo_sat + e0_solo_sub + e0_agua)*empuxo_scale*2, 0],
            [b_mon + b_jus + e0*empuxo_scale, 0]
        ]
        ax1.add_patch(plt.Polygon(pontos_empuxo_agua, closed=True, fill=True, color='blue', alpha=0.2, label='Empuxo da Água'))

        # Adicionar setas e valores dos empuxos
        ax1.arrow(b_mon + b_jus + e0*empuxo_scale, nivel_agua/3, -e0*empuxo_scale, 0, head_width=0.1, head_length=0.1, fc='blue', ec='blue')
        ax1.text(b_mon + b_jus + e0*empuxo_scale/2, nivel_agua/3 - 0.2, f'Ea = {e0_agua:.1f} kN/m', ha='center', color='blue')
        
        ax1.arrow(b_mon + b_jus + e0*empuxo_scale, braco_e0, -e0*empuxo_scale, 0, head_width=0.1, head_length=0.1, fc='red', ec='red')
        ax1.text(b_mon + b_jus + e0*empuxo_scale/2, braco_e0, f'Es = {e0_solo_sat:.1f} kN/m', ha='center', color='red')

        # Adicionar braços de alavanca verticais
        ax1.annotate('', xy=(b_mon + b_jus + e0*empuxo_scale, braco_e0), xytext=(b_mon + b_jus + e0*empuxo_scale, 0),
                    arrowprops=dict(arrowstyle='<->', color='red', lw=1, ls='--'))
        ax1.text(b_mon + b_jus + e0*empuxo_scale + 0.2, braco_e0/2, f'{braco_e0:.2f} m', ha='center', va='bottom', fontsize=9, color='red')

        ax1.annotate('', xy=(b_mon + b_jus + e0*empuxo_scale - 0.5, nivel_agua/3), xytext=(b_mon + b_jus + e0*empuxo_scale - 0.5, 0),
                    arrowprops=dict(arrowstyle='<->', color='blue', lw=1, ls='--'))
        ax1.text(b_mon + b_jus + e0*empuxo_scale - 0.3, nivel_agua/6, f'{nivel_agua/3:.2f} m', ha='center', va='bottom', fontsize=9, color='blue')

    else:
        # Empuxo do solo (sem água)
        pontos_empuxo = [
            [b_mon, 0],
            [b_mon, h],
            [b_mon + e0*empuxo_scale, 0]
        ]
        ax1.add_patch(plt.Polygon(pontos_empuxo, closed=True, fill=True, color='red', alpha=0.2, label='Empuxo do Solo'))
        
        # Adicionar seta e valor do empuxo
        ax1.arrow(b_mon + e0*empuxo_scale, h/3, -e0*empuxo_scale, 0, head_width=0.1, head_length=0.1, fc='red', ec='red')
        ax1.text(b_mon + e0*empuxo_scale/2, h/3, f'E = {e0:.1f} kN/m', ha='center', color='red')

        # Adicionar braço de alavanca
        ax1.annotate('', xy=(b_mon, braco_e0), xytext=(b_mon + e0*empuxo_scale, braco_e0),
                    arrowprops=dict(arrowstyle='<->', color='red', lw=1, ls='--'))
        ax1.text(b_mon + e0*empuxo_scale/2, braco_e0, f'{braco_e0:.2f} m', ha='center', va='bottom', fontsize=9, color='red')

    # Adicionar cotas
    ax1.text((b_jus + b_mon)/2, -0.2, f'Base: {b_jus + b_mon:.2f} m', ha='center', va='top', fontsize=10)
    ax1.text(-0.2, h/2, f'Altura: {h:.2f} m', ha='right', va='center', fontsize=10, rotation='vertical')
    ax1.text((b_jus + b_mon)/2, d, f'Altura útil: {d:.2f} m', ha='center', va='bottom', fontsize=10)
    ax1.text(b_mon + 0.5, h/2, f'Área de Aço: {as_final:.2f} cm²', ha='left', va='center', fontsize=10, rotation='vertical')

    # Configurar o subplot da esquerda
    ax1.set_xlim(-1, b_mon + b_jus + 1 + e0*empuxo_scale)
    ax1.set_ylim(-0.5, h + 0.5)
    ax1.set_aspect('equal')
    ax1.set_title('Seção do Muro de Arrimo à Flexão')
    ax1.set_xlabel('Base (m)')
    ax1.set_ylabel('Altura (m)')
    ax1.grid(True)
    ax1.legend()

    # Adicionar informação da pressão admissível
    ax1.text(0, -0.5, f"Pressão Admissível: {pressao_adm:.2f} kN/m²", ha='left', va='top', fontsize=10)
    ax1.text(0, -1, f"Tensão Máxima: {tensao_max:.2f} kN/m²", ha='left', va='top', fontsize=10)
    # Desenhar a linha de pressão admissível
    ax1.plot([0, b_mon + b_jus], [-pressao_adm*0.001, -pressao_adm*0.001], 'k--', linewidth=1)
    # Desenhar as tensões na fundação
    ax1.plot([0, b_mon + b_jus], [-tensao_max*0.001, -tensao_min*0.001], 'k--', linewidth=1)

    
    # Adicionar informações sobre a base teórica necessária e a comparação com a base máxima
    b_total = b_jus + b_mon
    if 'base_teorica' in resultados_estabilidade:
        base_teorica = resultados_estabilidade['base_teorica']
        base_ok = resultados_estabilidade.get('base_ok', False)
        base_atual_ok = resultados_estabilidade.get('base_atual_ok', False)
        base_max_ok = resultados_estabilidade.get('base_max_ok', True)
        
        """
        # Mostrar informações sobre a base
        ax1.text(0, -2.4, f"Base Atual: {b_total:.2f} m", ha='left', va='top', fontsize=10)
        ax1.text(0, -3.2, f"Base Teórica Necessária: {base_teorica:.2f} m", ha='left', va='top', fontsize=10)
        
        # Status da base atual
        status_base_atual = "Sim" if base_atual_ok else "Não"
        cor_status_atual = "green" if base_atual_ok else "red"
        ax1.text(0, -4.0, f"Base Atual Suficiente: {status_base_atual}", ha='left', va='top', fontsize=10, color=cor_status_atual)
        
        # Status da base máxima
        status_base_max = "Sim" if base_max_ok else "Não"
        cor_status_max = "green" if base_max_ok else "red"
        ax1.text(0, -4.8, f"Dentro do Limite Máximo: {status_base_max}", ha='left', va='top', fontsize=10, color=cor_status_max)
        
        # Mensagem geral sobre adequação da base
        status_geral = "Sim" if base_ok else "Não"
        cor_status_geral = "green" if base_ok else "red"
        ax1.text(0, -5.6, f"Base Adequada: {status_geral}", ha='left', va='top', fontsize=12, fontweight='bold', color=cor_status_geral)
        
        # Adicionar uma mensagem destacada sobre a adequação da base
        if not base_ok:
            mensagens = []
            if not base_atual_ok:
                mensagens.append(f"Base atual insuficiente (necessário aprox. +{base_teorica - b_total:.2f}m)")
            if not base_max_ok:
                mensagens.append(f"Base teórica excede o limite máximo permitido")
            
            if mensagens:
                plt.figtext(0.5, 0.01, " | ".join(mensagens), 
                          ha='center', fontsize=12, color='red',
                          bbox={"facecolor":"yellow", "alpha":0.5, "pad":5})
        
        """

    # Plotar os quantitativos dos materiais
    volume_concreto = (b_mon + b_jus + h) * d  # Volume em m³
    peso_terra, x_cg, volume_aterro, volume_corte = calcular_peso_terra_montante(h, b_mon, gamma_solo_sat, gamma_solo_sub)
    solo_corte = volume_corte
    solo_aterro = volume_aterro
    solo_carga = volume_aterro - volume_concreto

    # Relatório no subplot da direita
    ax2.axis('off')  # Desativa os eixos
    ax2.set_title('Resumo')

    relatorio = (
        f"Resumo do Quantitativo:\n"
        f"1. Área de Aço: {as_final:.2f} cm²/m\n"
        f"2. Volume de Concreto: {volume_concreto:.2f} m³/m\n"
        f"3. Volume de Solo - Corte: {solo_corte:.2f} m³/m\n"
        f"4. Volume de Solo - Aterro: {solo_aterro:.2f} m³/m\n"
        f"5. Volume de Solo - Carga [+] / Descarga [-]: {solo_carga:.2f} m³/m\n\n"

        f"Relatório de Estabilidade (caso de carregamento normal):\n"
        f"1. Fator de Segurança ao Deslizamento: {resultados_estabilidade['fs_deslizamento_total']:.2f} "
        f"{'(OK)' if resultados_estabilidade['fs_deslizamento_ok'] else '(NÃO OK - RISCO DE DESLIZAMENTO)'}\n"
        f"2. Fator de Segurança ao Tombamento: {abs(resultados_estabilidade['fs_tombamento']):.2f} "
        f"{'(OK)' if abs(resultados_estabilidade['fs_tombamento_ok']) else '(NÃO OK - RISCO DE TOMBAMENTO)'}\n"
        f"3. Tensão Máxima: {resultados_estabilidade['tensao_max']:.2f} kN/m² "
        f"{'(OK)' if resultados_estabilidade['pressao_adm_ok'] else '(NÃO OK - EXCEDE CAPACIDADE DO SOLO)'}\n"
        f"4. Tensão Mínima: {resultados_estabilidade['tensao_min']:.2f} kN/m² "
        f"{'(OK)' if resultados_estabilidade['tensao_min'] > 0 else '(NÃO OK - RISCO DE LEVANTAMENTO)'}\n"
        f"5. Base Teórica Necessária: {base_teorica:.2f} m\n"
        f"6. Base Atual: {b_total:.2f} m\n"
        f"7. Base Adequada: {'Sim' if base_ok else 'Não'}\n\n"

        f"Relatório de Dimensionamento:\n"
        f"1. Diâmetro da Barra: {resultados_dimensionamento['dia_barra']:.2f} mm\n"
        f"2. Espaçamento: {resultados_dimensionamento['espacamento']:.2f} cm\n"
        f"3. Armadura Mínima: {resultados_dimensionamento['as_min']:.2f} cm²\n"
        f"4. Armadura Calculada: {resultados_dimensionamento['as_calc']:.2f} cm²\n"
        f"5. Armadura Final: {resultados_dimensionamento['as_final']:.2f} cm²\n"
        f"6. Momento: {resultados_dimensionamento['momento']:.2f} kN.m\n"
        f"7. x/d: {resultados_dimensionamento['x_d']:.2f}"
        f"8. fck: {resultados_dimensionamento['fck']:.2f} MPa"
    )

    ax2.text(0.05, 0.95, relatorio, fontsize=10, va='top', ha='left', transform=ax2.transAxes)

    # Adicionar mensagem de alerta se necessário
    if not resultados_estabilidade['base_ok']:
        mensagens = []
        if not resultados_estabilidade['base_atual_ok']:
            mensagens.append(f"Base atual insuficiente (necessário aprox. +{resultados_estabilidade['base_teorica'] - (b_jus + b_mon):.2f}m)")
        if not resultados_estabilidade['base_max_ok']:
            mensagens.append(f"Base teórica excede o limite máximo permitido")
        
        if mensagens:
            plt.figtext(0.5, 0.02, " | ".join(mensagens), 
                      ha='center', fontsize=12, color='red',
                      bbox={"facecolor":"yellow", "alpha":0.5, "pad":5})

    # Criar tabela com resumo das cargas, braços e momentos
    dados_tabela = []
    nomes_cargas = []
    
    # Considerando dados da função verificar_estabilidade_flexao
    # Peso do muro
    peso_muro = resultados_estabilidade.get('peso_muro', 0)
    if 'peso_muro' in resultados_estabilidade:
        nomes_cargas.append("Peso do Muro")
        x_muro = resultados_estabilidade.get('x_muro', 0)
        momento_muro_PT = resultados_estabilidade.get('momento_muro_PT', 0)
        braco_muro_PT = resultados_estabilidade.get('braco_muro_PT', 0)
        momento_muro_CG = resultados_estabilidade.get('momento_muro_CG', 0)
        braco_muro_CG = resultados_estabilidade.get('braco_muro_CG', 0)
        dados_tabela.append([f"{peso_muro:.2f}", f"{x_muro:.2f}", f"{momento_muro_PT:.2f}", f"{braco_muro_CG:.2f}", f"{momento_muro_CG:.2f}"])
    
    # Peso do solo
    peso_solo_sat = resultados_estabilidade.get('peso_solo_sat', 0)
    if 'peso_solo_sat' in resultados_estabilidade:
        nomes_cargas.append("Peso do Solo Saturado")
        braco_solo_sat_PT = resultados_estabilidade.get('braco_solo_sat_PT', 0)
        momento_solo_PT = resultados_estabilidade.get('momento_solo_PT', 0)
        braco_solo_sat_CG = resultados_estabilidade.get('braco_solo_sat_CG', 0)
        momento_solo_CG = resultados_estabilidade.get('momento_solo_CG', 0)
        dados_tabela.append([f"{peso_solo_sat:.2f}", f"{braco_solo_sat_PT:.2f}", f"{momento_solo_PT:.2f}", f"{braco_solo_sat_CG:.2f}", f"{momento_solo_CG:.2f}"])
    
    peso_solo_sub = resultados_estabilidade.get('peso_solo_sub', 0)
    if 'peso_solo_sub' in resultados_estabilidade:
        nomes_cargas.append("Peso do Solo Submerso")
        braco_solo_sub_PT = resultados_estabilidade.get('braco_solo_sub_PT', 0)
        momento_solo_sub_PT = resultados_estabilidade.get('momento_solo_sub_PT', 0)
        braco_solo_sub_CG = resultados_estabilidade.get('braco_solo_sub_CG', 0)
        momento_solo_sub_CG = resultados_estabilidade.get('momento_solo_sub_CG', 0)
        dados_tabela.append([f"{peso_solo_sub:.2f}", f"{braco_solo_sub_PT:.2f}", f"{momento_solo_sub_PT:.2f}", f"{braco_solo_sub_CG:.2f}", f"{momento_solo_sub_CG:.2f}"])

    # Empuxo passivo
    ep = resultados_estabilidade.get('ep', 0)
    if 'ep' in resultados_estabilidade:
        nomes_cargas.append("Empuxo")
        braco_ep_PT = resultados_estabilidade.get('braco_ep_PT', 0)
        momento_ep_PT = resultados_estabilidade.get('momento_ep_PT', 0)
        braco_ep_CG = resultados_estabilidade.get('braco_ep_CG', 0)
        momento_ep_CG = resultados_estabilidade.get('momento_ep_CG', 0)
        dados_tabela.append([f"{ep:.2f}", f"{braco_ep_PT:.2f}", f"{momento_ep_PT:.2f}", f"{braco_ep_CG:.2f}", f"{momento_ep_CG:.2f}"])

    # Peso de água
    peso_agua = resultados_estabilidade.get('peso_agua', 0)
    if 'peso_agua' in resultados_estabilidade:
        nomes_cargas.append("Peso de Água")
        braco_agua_PT = resultados_estabilidade.get('braco_agua_PT', 0)
        momento_agua_PT = resultados_estabilidade.get('momento_agua_PT', 0)
        braco_agua_CG = resultados_estabilidade.get('braco_agua_CG', 0)
        momento_agua_CG = resultados_estabilidade.get('momento_agua_CG', 0)
        dados_tabela.append([f"{peso_agua:.2f}", f"{braco_agua_PT:.2f}", f"{momento_agua_PT:.2f}", f"{braco_agua_CG:.2f}", f"{momento_agua_CG:.2f}"])

    # Empuxo de água
    if 'e_agua' in resultados_estabilidade:
        nomes_cargas.append("Empuxo de Água")
        braco_e_agua_PT = resultados_estabilidade.get('braco_e_agua_PT', 0)
        momento_e_agua_PT = resultados_estabilidade.get('momento_e_agua_PT', 0)
        braco_e_agua_CG = resultados_estabilidade.get('braco_e_agua_CG', 0)
        momento_e_agua_CG = resultados_estabilidade.get('momento_e_agua_CG', 0)
        dados_tabela.append([f"{e_agua:.2f}", f"{braco_e_agua_PT:.2f}", f"{momento_e_agua_PT:.2f}", f"{braco_e_agua_CG:.2f}", f"{momento_e_agua_CG:.2f}"])
    
    # Empuxo de sobrecarga do solo
    if 'e_sobre' in resultados_estabilidade:
        nomes_cargas.append("Empuxo de Sobrecarga do Solo")
        braco_e_sobre_CG = resultados_estabilidade.get('braco_e_sobre_CG', 0)
        momento_e_sobre_CG = resultados_estabilidade.get('momento_e_sobre_CG', 0)
        dados_tabela.append([f"{e_sobre:.2f}", f"-", f"-", f"{braco_e_sobre_CG:.2f}", f"{momento_e_sobre_CG:.2f}"])

    # Momento devido a sobrecarga do solo
    if 'momento_sobre' in resultados_estabilidade:
        nomes_cargas.append("Momento sobrecarga do solo")
        braco_sobre_PT = resultados_estabilidade.get('braco_sobre_PT', 0)
        momento_sobre_PT = resultados_estabilidade.get('momento_sobre_PT', 0)
        braco_sobre_CG = resultados_estabilidade.get('braco_sobre_CG', 0)
        momento_sobre_CG = resultados_estabilidade.get('momento_sobre_CG', 0)
        dados_tabela.append([f"{momento_sobre:.2f}", f"{braco_sobre_PT:.2f}", f"{momento_sobre_PT:.2f}", f"{braco_sobre_CG:.2f}", f"{momento_sobre_CG:.2f}"])
    
    # 
    
    # Se não há todos os dados específicos, mostrar os momentos totais
    if not dados_tabela:
        nomes_cargas = ["Momento Estabilizante", "Momento Desestabilizante"]
        me = resultados_estabilidade.get('me', 0)
        mt = resultados_estabilidade.get('mt', 0)
        me_cg = resultados_estabilidade.get('me_cg', 0)
        dados_tabela = [
            [f"{me:.2f}", "-", "-", "-", "-"],
            [f"{mt:.2f}", "-", "-", "-", "-"],
            [f"{me_cg:.2f}", "-", "-", "-", "-"]
        ]
    
    # Criar a tabela
    # Se temos dados suficientes para a tabela
    if dados_tabela:
        tbl = plt.table(
            cellText=dados_tabela,
            rowLabels=nomes_cargas,
            colLabels=["Carga (kN/m)", "Braço PT (m)", "Momento PT (kN.m/m)", "Braço CG (m)", "Momento CG (kN.m/m)"],
            cellLoc='center',
            loc='bottom',
            # bbox=[0.5, -0.3, 0.45, 0.2]  # Posiciona a tabela abaixo do gráfico
        )
        
        # Ajustar tamanho das fontes da tabela
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1, 1.5)

    plt.tight_layout()
    #plt.subplots_adjust(bottom=0.5)  # Ajustar espaço na parte inferior para acomodar a tabela
    plt.show()

def plotar_muro_gravidade(h, d, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, k0, gamma_agua, sobrecarga_mon, calculos_gravidade, base_max, inclinacao="montante"):
    """
    Plota os diagramas detalhados do muro de gravidade com todas as cargas e excentricidades em um único gráfico
    
    Parâmetros:
    h: altura total do muro (m)
    crista: largura da crista (m)
    b_mon: largura da base a montante (m)
    gamma_concreto: peso específico do concreto (kN/m³)
    gamma_solo: peso específico do solo (kN/m³)
    phi: ângulo de atrito interno do solo (graus)
    c: coesão do solo (kN/m²)
    pressao_adm: pressão admissível do solo (kN/m²)
    nivel_agua: nível d'água (m)
    fs_coesao: fator de segurança à coesão
    fs_atrito: fator de segurança ao atrito
    k0: coeficiente de empuxo em repouso
    base_max: base máxima permitida (m) [opcional]
    gamma_agua: peso específico da água (kN/m³)
    sobrecarga_mon: sobrecarga a montante (kN/m²)
    inclinacao: direção da inclinação do muro ("montante" ou "jusante")
    """
    
    # Criar figura com dois subplots lado a lado
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))
    
    # Plotar o muro no subplot da esquerda
    ax1.set_title('Diagrama do Muro de Gravidade')
    
    # Desenhar o muro com base na inclinação escolhida
    if inclinacao == "montante":
        # Inclinação para montante (padrão): face interna inclinada
        pontos_muro = [
            [0, 0],
            [b_mon, 0],
            [b_mon - (b_mon - crista), h],
            [0, h]
        ]
    else:  # jusante
        # Inclinação para jusante: face externa inclinada
        pontos_muro = [
            [0, 0],
            [b_mon, 0],
            [b_mon, h],
            [b_mon - crista, h]
        ]
    ax1.add_patch(plt.Polygon(pontos_muro, closed=True, fill=False, color='black', linewidth=2))
    
    # Variaveis
    peso_solo_sat1 = 0
    peso_solo_sat2 = 0
    peso_solo_sub = 0
    peso_agua = 0
    peso_muro = 0
    peso_total = 0
    braco_solo_sat_PT1 = 0
    braco_solo_sat_PT2 = 0
    braco_solo_sub_PT = 0
    braco_agua_PT = 0
    braco_e0_agua = 0
    braco_e0_solo_sat1 = 0
    braco_e0_solo_sat2 = 0
    braco_e0_solo_sub = 0
    momento_solo_sat1 = 0
    momento_solo_sat2 = 0
    momento_solo_sub = 0
    momento_agua = 0
    momento_muro = 0
    momento_e0_agua = 0
    momento_e0_solo_sat1 = 0
    momento_e0_solo_sat2 = 0
    momento_e0_solo_sub = 0
    e0_agua = 0
    e0_solo_sat1 = 0
    e0_solo_sat2 = 0
    e0_solo_sub = 0
    e0 = 0
    momento_sobrecarga_est_CG = 0
    momento_sobrecarga_dest = 0
    momento_sobrecarga_est_PT = 0
    momento_sobrecarga_dest_PT = 0
    momento_est_total_PT = 0
    momento_dest_total_PT = 0

    # Calcular cargas com base na inclinação
    if inclinacao == "montante":
        # Inclinação para montante (padrão): face interna inclinada
        area_muro = 0.5 * (b_mon - crista) * h + crista * h
        
        # Dividir muro em trechos
        peso_muro_1 = 0.5 * (b_mon - crista) * h * gamma_concreto  # Parte triangular
        braco_muro_PT1 = (b_mon - crista) * 1 / 3 + crista  # CG do trapézio
        
        peso_muro_2 = crista * h * gamma_concreto  # Parte retangular
        braco_muro_PT2 = crista/2  # CG do retângulo
    else:  # jusante
        # Inclinação para jusante: face externa inclinada
        area_muro = 0.5 * (b_mon - crista) * h + crista * h
        
        # Dividir muro em trechos
        peso_muro_1 = 0.5 * (b_mon - crista) * h * gamma_concreto  # Parte triangular
        braco_muro_PT1 = (b_mon - crista) * 2 / 3  # CG do trapézio
        
        peso_muro_2 = crista * h * gamma_concreto  # Parte retangular
        braco_muro_PT2 = (b_mon - crista/2)  # CG do retângulo
    
    peso_muro = peso_muro_1 + peso_muro_2
    braco_muro_PT = (peso_muro_1 * braco_muro_PT1 + peso_muro_2 * braco_muro_PT2) / peso_muro

    x_cg = b_mon/2

    braco_muro_CG1 = braco_muro_PT1 - x_cg
    braco_muro_CG2 = braco_muro_PT2 - x_cg

    # Para o eixo Y:
    braco_muro_y1 = h/2
    braco_muro_y2 = h/3

    braco_muro_y = (peso_muro_1 * braco_muro_y1 + peso_muro_2 * braco_muro_y2) / peso_muro
    
    if nivel_agua > 0:
        intersecao = b_mon - (nivel_agua) * (b_mon - crista) / h

        # Solo saturado
        peso_solo_sat1 = 0.5 * (intersecao - crista) * (h - nivel_agua) * (gamma_solo_sat)
        braco_solo_sat_PT1 = ((intersecao - crista)*2/3 + crista)

        peso_solo_sat2 = (b_mon - intersecao) * (h - nivel_agua) * (gamma_solo_sat)
        braco_solo_sat_PT2 = intersecao + (b_mon - intersecao)/2
                
        peso_solo_sat = peso_solo_sat1 + peso_solo_sat2
        braco_solo_sat_PT = (peso_solo_sat1 * braco_solo_sat_PT1 + peso_solo_sat2 * braco_solo_sat_PT2) / peso_solo_sat
        
        # Solo submerso
        peso_solo_sub = 0.5 * (b_mon - intersecao) * nivel_agua * gamma_solo_sub
        braco_solo_sub_PT = intersecao + (b_mon - intersecao)*2/3

        # Peso da água
        peso_agua = 0.5 * (b_mon - intersecao) * nivel_agua * (gamma_agua)
        braco_agua_PT = intersecao + (b_mon - intersecao)*2/3
        
        # Empuxos
        e0_agua = 0.5 * gamma_agua * nivel_agua**2
        braco_e0_agua = nivel_agua/3
        e0_solo_sat1 = 0.5 * (gamma_solo_sat) * (h-nivel_agua)**2 * k0
        braco_e0_solo_sat1 = nivel_agua + (h-nivel_agua)/3
        e0_solo_sat2 = (gamma_solo_sat) * nivel_agua * (h - nivel_agua) * k0
        braco_e0_solo_sat2 = nivel_agua/2
        e0_solo_sub = 0.5 * (gamma_solo_sub) * nivel_agua**2 * k0
        braco_e0_solo_sub = nivel_agua/3

        e0_solo_sat = e0_solo_sat1 + e0_solo_sat2
        braco_e0_solo_sat = (e0_solo_sat1 * braco_e0_solo_sat1 + e0_solo_sat2 * braco_e0_solo_sat2) / e0_solo_sat

        # Peso total
        peso_total = peso_solo_sat1 + peso_solo_sat2 + peso_solo_sub + peso_agua + peso_muro + sobrecarga_mon*(b_mon - crista)

        # Empuxo total
        e0 = e0_solo_sat + e0_solo_sub + e0_agua
        braco_e0 = (e0_solo_sat * braco_e0_solo_sat + e0_solo_sub * braco_e0_solo_sub + e0_agua * braco_e0_agua) / e0

    else:
        peso_solo_sat1 = 0.5 * (b_mon - crista) * h * (gamma_solo_sat)
        braco_solo_sat_PT1 = (b_mon - crista) * 2 / 3 + crista

        peso_solo_sat = peso_solo_sat1
        braco_solo_sat_PT = braco_solo_sat_PT1

        e0_solo_sat = 0.5 * (gamma_solo_sat) * h**2 * k0
        braco_e0_solo_sat = h/3

        peso_solo_sub = 0
        peso_agua = 0
        e0_agua = 0

        peso_total = peso_solo_sat1 + peso_muro + sobrecarga_mon*(b_mon - crista)
    
        e0 = e0_solo_sat
        braco_e0 = braco_e0_solo_sat
    
    # Cálculo do momento total em relação ao CG e ponto de tombamento
    momento_solo_sat_CG = peso_solo_sat*(braco_solo_sat_PT - x_cg)
    momento_solo_sub_CG = peso_solo_sub*(braco_solo_sub_PT - x_cg)
    momento_agua_CG = peso_agua*(braco_agua_PT - x_cg)
    momento_muro_CG = peso_muro*(braco_muro_PT - x_cg)
    momento_solo_sat_PT = peso_solo_sat*(braco_solo_sat_PT)
    momento_solo_sub_PT = peso_solo_sub*(braco_solo_sub_PT)
    momento_agua_PT = peso_agua*(braco_agua_PT)
    momento_muro_PT = peso_muro*(braco_muro_PT)

    if inclinacao == "montante":
        momento_est_total_PT = momento_solo_sat_PT + momento_solo_sub_PT + momento_agua_PT + momento_muro_PT
    else:
        momento_est_total_PT = momento_muro_PT

    if nivel_agua == 0:
        momento_e0 = -e0*braco_e0
    else:
        momento_e0_agua = e0_agua*braco_e0_agua
        momento_e0_solo_sat = e0_solo_sat*braco_e0_solo_sat
        momento_e0_solo_sub = e0_solo_sub*braco_e0_solo_sub

        # Momentos totais:
        momento_e0 = -(momento_e0_agua + momento_e0_solo_sat + momento_e0_solo_sub)

    momento_est_total_CG = 0
    if braco_solo_sat_PT - x_cg >= 0:
        momento_est_total_CG =+ momento_solo_sat_CG
    if braco_solo_sub_PT - x_cg >= 0:
        momento_est_total_CG =+ momento_solo_sub_CG
    if braco_agua_PT - x_cg >= 0:
        momento_est_total_CG =+ momento_agua_CG
    if braco_muro_PT - x_cg >= 0:
        momento_est_total_CG =+ momento_muro_CG
    
    momento_dest_total_CG = 0
    if braco_muro_PT - x_cg <= 0:
        momento_dest_total_CG =+ momento_muro_CG
    if braco_solo_sat_PT - x_cg <= 0:
        momento_dest_total_CG =+ momento_solo_sat_CG
    if braco_solo_sub_PT - x_cg <= 0:
        momento_dest_total_CG =+ momento_solo_sub_CG
    if braco_agua_PT - x_cg <= 0:
        momento_dest_total_CG =+ momento_agua_CG
    
    if inclinacao == "montante":
        momento_dest_total_CG =+ momento_e0
        momento_dest_total_PT =+ momento_e0
    else:
        momento_dest_total_CG = momento_e0
        momento_dest_total_PT = momento_e0
    
    if sobrecarga_mon > 0:
        if inclinacao == "montante":
            momento_sobrecarga_est_CG = sobrecarga_mon*((b_mon - crista)*((b_mon - crista)/2 + crista) - x_cg)
            momento_sobrecarga_est_PT = sobrecarga_mon*(b_mon - crista)*((b_mon - crista)/2 + crista)
        momento_sobrecarga_dest = -sobrecarga_mon*k0*h**2 * 0.5
        momento_dest_total_CG =+ momento_sobrecarga_dest
        momento_est_total_CG =+ momento_sobrecarga_est_CG
        momento_est_total_PT =+ momento_sobrecarga_est_PT
        momento_dest_total_PT =+ momento_sobrecarga_dest
    
    momento_CG = momento_solo_sat_CG + momento_solo_sub_CG + momento_agua_CG + momento_muro_CG + momento_e0 + momento_sobrecarga_dest

    FST = abs(momento_est_total_PT/momento_dest_total_PT)

    tensao_max = peso_total/b_mon + abs(momento_CG/(b_mon**2/6))
    tensao_min = peso_total/b_mon - abs(momento_CG/(b_mon**2/6))
    
    # Desenhar cargas no subplot da esquerda
    # Peso do muro
    ax1.arrow(braco_muro_PT, braco_muro_y, 0, -0.5, head_width=0.1, head_length=0.1, fc='grey', ec='grey', label='Peso do Muro')
    ax1.text(braco_muro_PT - 0.5, braco_muro_y - 0.25, f'Pm = {peso_muro:.1f} kN/m', ha='center', color='grey')
    ax1.annotate('', xy=(0,  braco_muro_y), xytext=(braco_muro_PT,  braco_muro_y), arrowprops=dict(arrowstyle='<->', color='grey', lw=1.5))
    ax1.text(braco_muro_PT/2, braco_muro_y + 0.2, f'{braco_muro_PT:.2f} m', ha='center', va='top', fontsize=11, color='grey')

    if inclinacao == "montante":
        # Peso do solo - Desenhar polígono de forças
        pontos_solo = [
            [b_mon - (b_mon - crista), h],
            [b_mon, h],
            [b_mon, 0],
        ]
        ax1.add_patch(plt.Polygon(pontos_solo, closed=True, fill=True, color='green', alpha=0.2))

    if inclinacao == "montante":
        if nivel_agua > 0:
            ax1.arrow(braco_solo_sat_PT, nivel_agua + (h - nivel_agua)/2, 0, -0.5, head_width=0.1, head_length=0.1, fc='green', ec='green', label='Peso do Solo Saturado')
            ax1.text(braco_solo_sat_PT, nivel_agua + (h - nivel_agua)/2 + 0.2, f'Psat = {(peso_solo_sat1+peso_solo_sat2):.1f} kN/m', ha='center', color='green')
            ax1.annotate('', xy=(0, h*2/3), xytext=(braco_solo_sat_PT, h*2/3),
                        arrowprops=dict(arrowstyle='<->', color='green', lw=1, ls='--'))
            ax1.text(braco_solo_sat_PT/2, h*2/3+0.12, f'{braco_solo_sat_PT:.2f} m',
                    ha='center', va='bottom', fontsize=9, color='green')

            ax1.arrow(braco_solo_sub_PT,(h - nivel_agua)*2/3, 0, -0.5, head_width=0.1, head_length=0.1, fc='green', ec='green', label='Peso do Solo Submerso')
            ax1.text(braco_solo_sub_PT,(h - nivel_agua)*2/3 + 0.2, f'Psub = {peso_solo_sub:.1f} kN/m', ha='center', color='green')

            ax1.arrow(braco_agua_PT,(h - nivel_agua)/3, 0, -0.5, head_width=0.1, head_length=0.1, fc='blue', ec='blue', label='Peso da Água')
            ax1.text(braco_agua_PT,(h - nivel_agua)/3 + 0.2, f'Pa = {peso_agua:.1f} kN/m', ha='center', color='blue')
        else:
            ax1.arrow(braco_solo_sat_PT, h*2/3, 0, -0.5, head_width=0.1, head_length=0.1, fc='green', ec='green', label='Peso do Solo')
            ax1.text(braco_solo_sat_PT, h*2/3 + 0.2, f'Ps = {peso_solo_sat1:.1f} kN/m', ha='center', color='green')
            # Peso do solo saturado 1
            ax1.annotate('', xy=(0, h*2/3), xytext=(braco_solo_sat_PT, h*2/3),
                        arrowprops=dict(arrowstyle='<->', color='green', lw=1, ls='--'))
            ax1.text(braco_solo_sat_PT/2, h*2/3+0.12, f'{braco_solo_sat_PT:.2f} m',
                    ha='center', va='bottom', fontsize=9, color='green')
    
    # Empuxo do solo
    empuxo_scale = 0.02
    if nivel_agua > 0:
        # Empuxo de com solo parcialmente submerso
                # Empuxo - Diagrama triangular (solo seco)
        pontos_empuxo_solo = [
            [b_mon, 0],
            [b_mon, h],
            [b_mon + e0_solo_sat1*empuxo_scale, nivel_agua],
            [b_mon + e0*empuxo_scale, 0]
        ]

        empuxo_agua = 0.5 * gamma_agua * nivel_agua**2 * k0

        pontos_empuxo_agua = [
            [b_mon + e0_solo_sat1*empuxo_scale, nivel_agua],
            [b_mon + e0_solo_sat1*empuxo_scale + empuxo_agua*empuxo_scale, 0],
            [b_mon + e0*empuxo_scale, 0]
        ]
        ax1.add_patch(plt.Polygon(pontos_empuxo_solo, closed=True, fill=True, color='red', alpha=0.2))

        ax1.add_patch(plt.Polygon(pontos_empuxo_agua, closed=True, fill=True, color='blue', alpha=0.2))

        ax1.arrow(b_mon + e0*empuxo_scale, nivel_agua, -e0*empuxo_scale, 0, head_width=0.1, head_length=0.1, fc='blue', ec='blue', label='Empuxo da Água')
        ax1.text(b_mon + e0*empuxo_scale/2, nivel_agua, f'Ea = {empuxo_agua:.1f} kN/m', ha='center', color='blue')
    else:
        # Empuxo - Diagrama triangular (solo seco)
        pontos_empuxo = [
            [b_mon, 0],
            [b_mon, h],
            [b_mon + e0*empuxo_scale, 0]
        ]
        ax1.add_patch(plt.Polygon(pontos_empuxo, closed=True, fill=True, color='red', alpha=0.2))
        ax1.arrow(b_mon + e0*empuxo_scale, h/3, -e0*empuxo_scale, 0, head_width=0.1, head_length=0.1, fc='red', ec='red', label='Empuxo')
        ax1.text(b_mon + e0*empuxo_scale/2, h/3*1.05, f'E = {e0 + e0_agua:.1f} kN/m', ha='center', color='red')
        ax1.annotate('', xy=(b_mon+1, 0), xytext=(b_mon+1, h/3),
                    arrowprops=dict(arrowstyle='<->', color='red', lw=1, ls='--'))
        ax1.text(b_mon+1.15, h/2/3, f'h = {h/3:.2f} m',
                ha='left', va='center', fontsize=9, color='red', rotation=90)

    
    # Diagrama de tensões na base
    tensao_scale = 0.003

    ax1.plot([0, b_mon], [-tensao_max*tensao_scale, -tensao_min*tensao_scale], 'r-', linewidth=2, label='Tensões na Base')
    ax1.text(-0.05*b_mon, -tensao_max*tensao_scale, f'{tensao_max:.2f} kN/m²', ha='center', color='red')
    ax1.text(1.1*b_mon, -tensao_min*tensao_scale, f'{tensao_min:.2f} kN/m²', ha='center', color='red')

    # Desenhar a pressão admissível
    ax1.plot([0, b_mon], [-pressao_adm*tensao_scale, -pressao_adm*tensao_scale], 'g--', linewidth=2, label=f'Pressão Admissível: {pressao_adm} kN/m²')
    
    # Desenhar o nível de água
    if nivel_agua > 0:
        # Desenhar linha do nível de água
        # Acha a interseção do nível de água com o muro
        intersecao = b_mon - (nivel_agua) * (b_mon - crista) / h

        ax1.plot([intersecao, b_mon], [nivel_agua, nivel_agua], 'b-', linewidth=2, label='Nível d\'água')
        
        # Sombrear área abaixo do nível de água
        pontos_agua = [
            [intersecao, nivel_agua],
            [b_mon, nivel_agua],
            [b_mon, 0],
        ]
        ax1.add_patch(plt.Polygon(pontos_agua, closed=True, fill=True, color='skyblue', alpha=0.3))

        # Desenhar texto indicativo
        ax1.text(b_mon + 0.1, nivel_agua, f'NA = {nivel_agua:.2f}m', ha='left', va='center', color='blue')
            
    # Configurar o subplot na esquerda
    ax1.set_xlim(- 0.5, b_mon + 0.5 + e0*empuxo_scale)
    ax1.set_ylim(-tensao_max*tensao_scale - 0.5, h + 0.5)
    ax1.grid(True)
    ax1.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
    
    # Adicionar cotas (linhas de dimensão) nos eixos x e y
    # Cota da base (x)
    ax1.annotate('', xy=(0, 0.3), xytext=(b_mon, 0.3),
                arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
    ax1.text(b_mon/2, 0.2, f'Base: {b_mon:.2f} m', ha='center', va='top', fontsize=11, color='#34495e')

    # Cota da altura (y)
    ax1.annotate('', xy=(-0.3, 0), xytext=(-0.3, h),
                arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
    ax1.text(-0.35, h/2, f'Altura: {h:.2f} m', ha='right', va='center', fontsize=11, color='#34495e', rotation='vertical')

    if inclinacao == "montante":
        # Cota da crista (x)
        ax1.annotate('', xy=(0, h*1.02), xytext=(crista, h*1.02),
                    arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
        ax1.text(crista/2, h*1.02+0.08, f'Crista: {crista:.2f} m', ha='center', va='bottom', fontsize=11, color='#34495e', rotation='horizontal')
    else:
        # Cota da crista (x)
        ax1.annotate('', xy=(b_mon - crista, h*1.02), xytext=(b_mon, h*1.02),
                    arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
        ax1.text(b_mon - crista/2, h*1.02+0.08, f'Crista: {crista:.2f} m', ha='center', va='bottom', fontsize=11, color='#34495e', rotation='horizontal')

    if nivel_agua > 0 and inclinacao == "montante":
        # Peso do solo submerso
        ax1.annotate('', xy=(0, (h - nivel_agua)*1/2), xytext=(braco_solo_sub_PT, (h - nivel_agua)*1/2),
                    arrowprops=dict(arrowstyle='<->', color='green', lw=1, ls='--'))
        ax1.text(braco_solo_sub_PT/2, (h - nivel_agua)*1/2+0.12, f'{braco_solo_sub_PT-crista:.2f} m',
                ha='center', va='bottom', fontsize=9, color='green')

        # Peso da água
        ax1.annotate('', xy=(0, (h - nivel_agua)/3), xytext=(braco_agua_PT, (h - nivel_agua)/3),
                    arrowprops=dict(arrowstyle='<->', color='blue', lw=1, ls='--'))
        ax1.text(braco_agua_PT/2, (h - nivel_agua)/3+0.12, f'{braco_agua_PT-crista:.2f} m',
                ha='center', va='bottom', fontsize=9, color='blue')


    if sobrecarga_mon > 0:
        # Desenhar sobrecarga a montante (retângulo/linha/seta)
        ax1.plot([crista, b_mon], [h*1.05+0.08, h*1.05+0.08], color='orange', lw=2, solid_capstyle='butt')
        ax1.arrow(crista, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
        ax1.arrow((b_mon-crista)/3+crista, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
        ax1.arrow((b_mon-crista)/3*2+crista, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
        ax1.arrow(b_mon, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
        ax1.text((b_mon-crista)/2+crista, h+0.32, f'q = {sobrecarga_mon:.1f} kN/m²', ha='center', va='bottom', color='orange', fontsize=11, fontweight='bold')

    # Configurar o subplot da direita para o relatório
    ax2.axis('off')  # Desativa os eixos
    ax2.set_title('Relatório de Estabilidade')

    # Criar tabela com resumo das cargas, braços e momentos
    dados_tabela = []
    nomes_cargas = []
    
    # Adicionar dados do peso do muro
    nomes_cargas.append("Peso do Muro")
    dados_tabela.append([f"{peso_muro:.2f}", f"{braco_muro_PT:.2f}", f"{momento_muro_PT:.2f}", f"{braco_muro_PT-x_cg:.2f}", f"{momento_muro_CG:.2f}"])
    
    # Adicionar dados do solo, água e empuxos dependendo do nível de água
    if nivel_agua > 0:
        nomes_cargas.extend(["Solo Sat", "Solo Sub", "Água", "Empuxo Solo Sat", "Empuxo Solo Sub", "Empuxo Água"])
        
        dados_tabela.append([f"{peso_solo_sat:.2f}", f"{braco_solo_sat_PT:.2f}", f"{momento_solo_sat_PT:.2f}",f"{braco_solo_sat_PT-x_cg:.2f}", f"{momento_solo_sat_CG:.2f}"])
        dados_tabela.append([f"{peso_solo_sub:.2f}", f"{braco_solo_sub_PT:.2f}", f"{momento_solo_sub_PT:.2f}",f"{braco_solo_sub_PT-x_cg:.2f}", f"{momento_solo_sub_CG:.2f}"])
        dados_tabela.append([f"{peso_agua:.2f}", f"{braco_agua_PT:.2f}", f"{momento_agua_PT:.2f}",f"{braco_agua_PT-x_cg:.2f}", f"{momento_agua_CG:.2f}"])
        
        dados_tabela.append([f"{e0_solo_sat:.2f}", f"{braco_e0_solo_sat:.2f}", f"--",f"--", f"{-momento_e0_solo_sat:.2f}"])
        dados_tabela.append([f"{e0_solo_sub:.2f}", f"{braco_e0_solo_sub:.2f}", f"--",f"--", f"{-momento_e0_solo_sub:.2f}"])
        dados_tabela.append([f"{e0_agua:.2f}", f"{braco_e0_agua:.2f}", f"--", f"--", f"{-momento_e0_agua:.2f}"])
    else:
        nomes_cargas.extend(["Solo", "Empuxo"])
        dados_tabela.append([f"{peso_solo_sat:.2f}", f"{braco_solo_sat_PT:.2f}", f"{momento_solo_sat_PT:.2f}",f"{braco_solo_sat_PT-x_cg:.2f}", f"{momento_solo_sat_CG:.2f}"])
        dados_tabela.append([f"{e0:.2f}", f"{braco_e0:.2f}", f"--",f"--", f"{-momento_e0:.2f}"])
        
    # Adicionar sobrecarga se existir
    if sobrecarga_mon > 0:
        nomes_cargas.append("Sobrecarga")
        dados_tabela.append([f"{sobrecarga_mon*(b_mon-crista):.2f}", f"{(b_mon-crista)/2+crista:.2f}", f"{sobrecarga_mon*(b_mon-crista)*(b_mon-crista)/2+crista}",f"{(b_mon-crista)/2:.2f}", f"{momento_sobrecarga_est_CG:.2f}"])
    
    # Criar a tabela
    tbl = plt.table(
        cellText=dados_tabela,
        rowLabels=nomes_cargas,
        colLabels=["Carga (kN/m)", "Braço PT (m)", "Momento - PT (kN.m/m)", "Braço CG (m)", "Momento - CG (kN.m/m)"],
        cellLoc='center',
        loc='center',
        bbox=[0.1, 0.1, 0.8, 0.4]  # Posiciona a tabela no centro do subplot direito
    )
    
    # Ajustar tamanho das fontes da tabela
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.5)  # Ajustar a escala da tabela
    
    # Adicionar linhas de totais abaixo da tabela
    ax2.text(0.1, 0.05, f"Momento Estabilizante: {momento_est_total_PT:.2f} kN.m/m", fontsize=10, ha='left')
    ax2.text(0.1, 0.02, f"Momento Desestabilizante: {momento_dest_total_PT:.2f} kN.m/m", fontsize=10, ha='left')
    # ax2.text(0.1, -0.01, f"Momento Resultante: {momento_CG:.2f} kN.m/m", fontsize=10, ha='left', weight='bold')
    ax2.text(0.1, -0.04, f"Peso Total: {peso_total:.2f} kN/m", fontsize=10, ha='left', weight='bold')
    ax2.text(0.1, -0.07, f"FS ao Tombamento: {FST:.2f}", fontsize=10, ha='left', weight='bold')
    
    plt.tight_layout()
    plt.show()

def validar_dados_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua, k0, base_max, gamma_agua, sobrecarga_mon):
    """
    Verifica se os valores inseridos para o muro de gravidade são válidos.
    
    Retorna (valido, mensagem)
    valido: True se todos os valores são válidos, False caso contrário
    mensagem: Mensagem de erro se os valores não forem válidos
    """
    mensagens_erro = []
    
    # Verificar valores positivos
    if h <= 0:
        mensagens_erro.append("A altura deve ser maior que zero")
    if crista <= 0:
        mensagens_erro.append("A largura da crista deve ser maior que zero")
    if b_mon <= 0:
        mensagens_erro.append("A base deve ser maior que zero")
    if gamma_concreto <= 0:
        mensagens_erro.append("O peso específico do concreto deve ser maior que zero")
    if gamma_solo_sat <= 0:
        mensagens_erro.append("O peso específico do solo saturado deve ser maior que zero")
    if gamma_solo_sub <= 0:
        mensagens_erro.append("O peso específico do solo submerso deve ser maior que zero")
    if pressao_adm <= 0:
        mensagens_erro.append("A pressão admissível deve ser maior que zero")
    if phi < 0 or phi > 45:
        mensagens_erro.append("O ângulo de atrito deve estar entre 0 e 45 graus")
    if c < 0:
        mensagens_erro.append("A coesão deve ser maior ou igual a zero")
    if k0 < 0:
        mensagens_erro.append("O coeficiente de empuxo deve ser maior ou igual a zero")
    if base_max <= 0:
        mensagens_erro.append("A base máxima deve ser maior que zero")
    if gamma_agua <= 0:
        mensagens_erro.append("O peso específico da água deve ser maior que zero")
    if sobrecarga_mon < 0:
        mensagens_erro.append("A sobrecarga deve ser maior ou igual a zero")
    if nivel_agua < 0:
        mensagens_erro.append("O nível d'água não pode ser menor que zero")


    # Verificar coerência entre valores
    if crista >= b_mon:
        mensagens_erro.append("A largura da crista deve ser menor que a base")
    if nivel_agua >= h:
        mensagens_erro.append("O nível d'água não pode ser maior que a altura do muro")
    if nivel_agua > h:
        mensagens_erro.append("O nível d'água não pode ser maior que a altura do muro")
    if base_max < b_mon:
        mensagens_erro.append("A base máxima deve ser maior que a base atual")
    if gamma_solo_sat < gamma_solo_sub:
        mensagens_erro.append("O peso específico do solo submerso está maior que o do solo saturado")
    
    # Verificar limites típicos
    if gamma_concreto < 18 or gamma_concreto > 28:
        mensagens_erro.append("O peso específico do concreto está fora do intervalo típico (18-28 kN/m³)")
    if gamma_solo_sat < 8 or gamma_solo_sat > 32:
        mensagens_erro.append("O peso específico do solo está fora do intervalo típico (8-32 kN/m³)")
    if pressao_adm > 1000:
        mensagens_erro.append("A pressão admissível parece muito alta (> 1000 kN/m²)")
    
    # Verificar proporções comuns para muros de gravidade
    if b_mon < 0.4 * h:
        mensagens_erro.append("A base parece muito pequena para a altura do muro (recomenda-se base ≥ 0.4 × altura)")
    if b_mon > 0.8 * h:
        mensagens_erro.append("AVISO: Base muito larga em relação à altura (> 0.8 × altura)")
    
    if len(mensagens_erro) > 0:
        return False, "\n".join(mensagens_erro)
    else:
        return True, "Valores válidos"

def exibir_muro_gravidade_popup():
    try:
        # Obter os valores da interface principal
        h = float(entry_h.get())
        crista = float(entry_crista.get())
        b_mon = float(entry_b_gravidade.get())
        gamma_concreto = float(entry_gamma_concreto.get())
        gamma_solo_sat = float(entry_gamma_solo_sat.get())
        gamma_solo_sub = float(entry_gamma_solo_sub.get())
        phi = float(entry_phi_estabilidade.get())
        c = float(entry_coesao.get())
        pressao_adm = float(entry_pressao_adm.get())
        nivel_agua = float(entry_nivel_agua.get())
        fs_coesao = float(entry_fs_coesao.get())
        fs_atrito = float(entry_fs_atrito.get())
        k0 = float(entry_k0.get())  # Usando Ka como K0 para o muro de gravidade
        base_max = float(entry_base_max.get())
        gamma_agua = float(entry_gamma_agua.get())
        sobrecarga_mon = float(entry_sobrecarga_mon.get())
        inclinacao = var_inclinacao.get()  # Obter a inclinação escolhida pelo usuário
        
        # Validar dados
        valido, mensagem = validar_dados_muro_gravidade(h, crista, b_mon, gamma_concreto, 
                                                      gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua, k0, base_max, gamma_agua, sobrecarga_mon)
        
        if not valido:
            # Verificar se são avisos ou erros críticos
            if "AVISO:" in mensagem:
                resposta = messagebox.askokcancel("Aviso", 
                                                 f"Foram detectados possíveis problemas nos dados:\n\n{mensagem}\n\nDeseja continuar mesmo assim?")
                if not resposta:
                    return
            else:
                messagebox.showerror("Erro nos dados", mensagem)
                return
        
        # Calcular muro de gravidade
        resultado = calcular_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, 
                                           phi, c, pressao_adm, nivel_agua, fs_coesao, 
                                           fs_atrito, k0, gamma_agua, sobrecarga_mon, base_max)
        
        # Verificar se o resultado foi bem-sucedido
        if resultado is None:
            messagebox.showerror("Erro", "Falha ao calcular o muro de gravidade.")
            return
        
        # Plotar o muro
        plotar_muro_gravidade(
            h, 0, crista, b_mon, 
            gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, 
            pressao_adm, nivel_agua, fs_coesao, fs_atrito, k0, gamma_agua, sobrecarga_mon,
            resultado, base_max, inclinacao  # Passando o resultado completo como calculos_gravidade e a inclinação
        )
        
    except ValueError as e:
        messagebox.showerror("Erro", f"Por favor, insira valores válidos: {str(e)}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")


def calcular_quantitativos_muro_gravidade(dados_dimensionamento, dados_verificacao, diametro_barra=10, espacamento_barra=0.20, h=None, crista=None):
    """
    Calcula quantitativos de materiais usando os dados de dimensionamento e verificação
    
    Parâmetros:
    dados_dimensionamento: dicionário retornado por dimensionar_muro_gravidade
    dados_verificacao: dicionário retornado por verificar_estabilidade_muro_gravidade
    diametro_barra: diâmetro das barras de aço (mm)
    espacamento_barra: espaçamento entre barras (m)
    h: altura do muro (m) - necessário para cálculo da armadura
    crista: largura da crista (m) - necessário para cálculo da armadura
    
    Retorna:
    dict com quantitativos detalhados
    """
    if h is None or crista is None:
        raise ValueError("Altura (h) e largura da crista são necessárias para o cálculo de quantitativos")
    
    # Extrair dados básicos
    volume_concreto = dados_dimensionamento['volume_concreto']
    volume_corte = dados_dimensionamento['volume_corte']
    volume_aterro = dados_dimensionamento['volume_aterro']
    volume_descarga = dados_dimensionamento['volume_descarga']
    
    # Cálculo da armadura na crista
    area_barra = math.pi * (diametro_barra/1000)**2 / 4  # m²
    comprimento_barra = 2 + crista  # Comprimento de cada barra - Crista + 2m (+- anc para ambos os lados)
    numero_barras = math.ceil(h / espacamento_barra)
    volume_aco = area_barra * comprimento_barra * numero_barras  # Volume total de aço em m³
    peso_aco = volume_aco * 7850  # kg (densidade do aço)
    
    # Cálculo da área de formas
    # Altura máxima de concretagem = 1.5m, 5 reutilizações
    numero_camadas = math.ceil(h / 1.5)
    comprimento_inclinado = math.sqrt((dados_dimensionamento.get('b_mon', crista) - crista)**2 + h**2)
    area_formas = (h + comprimento_inclinado) * numero_camadas / 5
    
    # Divisão do volume por tipo de concreto
    volume_concreto_25 = volume_concreto * 0.9  # 90% em concreto estrutural
    volume_concreto_6 = volume_concreto * 0.1   # 10% em concreto de regularização
    
    return {
        'volume_concreto': volume_concreto,
        'volume_concreto_25': volume_concreto_25,
        'volume_concreto_6': volume_concreto_6,
        'peso_aco': peso_aco,
        'numero_barras': numero_barras,
        'comprimento_barra': comprimento_barra,
        'volume_corte': volume_corte,
        'volume_aterro': volume_aterro,
        'volume_descarga': volume_descarga,
        'area_formas': area_formas,
        # Incluir também dados de verificação para facilitar o acesso
        'fs_deslizamento': dados_verificacao['fs_deslizamento'],
        'fs_tombamento': dados_verificacao['fs_tombamento'],
        'tensao_max': dados_verificacao['tensao_max'],
        'tensao_min': dados_verificacao['tensao_min'],
        'tensao_ok': dados_verificacao['tensao_ok'],
        'base_teorica': dados_verificacao['base_teorica'],
        'base_atual_ok': dados_verificacao['base_atual_ok'],
        'base_max_ok': dados_verificacao['base_max_ok'],
        'base_ok': dados_verificacao['base_ok']
    }

def gerar_quantitativos_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito,
                                 ka, gamma_agua, sobrecarga_mon, preco_concreto=350, preco_aco=8.5, diametro_barra=10, espacamento_barra=0.20, base_max=0, inclinacao="montante"):
    """
    Gera quantitativos de materiais para o muro de gravidade
    
    Parâmetros:
    h: altura do muro (m)
    crista: largura da crista (m)
    b_mon: largura da base a montante (m)
    gamma_concreto: peso específico do concreto (kN/m³)
    gamma_solo: peso específico do solo (kN/m³)
    phi: ângulo de atrito interno do solo (graus)
    c: coesão do solo (kN/m²)
    pressao_adm: pressão admissível do solo (kN/m²)
    nivel_agua: nível d'água (m)
    fs_coesao: fator de segurança à coesão
    fs_atrito: fator de segurança ao atrito
    ka: coeficiente de empuxo ativo
    preco_concreto: preço do concreto (R$/m³)
    preco_aco: preço do aço (R$/kg)
    diametro_barra: diâmetro das barras de aço (mm)
    espacamento_barra: espaçamento entre barras (m)
    base_max: base máxima permitida (m) [opcional]
    
    Retorna:
    dict com os quantitativos calculados
    """
    if base_max == 0 or base_max == None:
        base_max = b_mon*1.5

    # Cálculos do muro de gravidade
    resultado_gravidade = calcular_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, ka, gamma_agua, sobrecarga_mon, base_max, inclinacao)
    
    # Cálculo do volume de concreto (trapézio)
    volume_concreto = resultado_gravidade['volume_concreto']
    
    # Cálculo da armadura na crista
    area_barra = math.pi * (diametro_barra/1000)**2 / 4  # m²
    comprimento_barra = 2 + crista  # Comprimento de cada barra - Crista + 2m (+- anc para ambos os lados)
    numero_barras = math.ceil(h / espacamento_barra)
    volume_aco = area_barra * comprimento_barra * numero_barras  # Volume total de aço em m³
    peso_aco = volume_aco * 7850  # kg (densidade do aço)
    
    # Pegar os volumes de solo calculados pelo muro de gravidade
    volume_corte = resultado_gravidade['volume_corte']
    volume_aterro = resultado_gravidade['volume_aterro']
    volume_descarga = resultado_gravidade['volume_descarga']
    
    # Cálculo da área de formas
    # Altura máxima de concretagem = 1.5m, 5 reutilizações
    numero_camadas = math.ceil(h / 1.5)
    comprimento_inclinado = math.sqrt((b_mon - crista)**2 + h**2)
    area_formas = (h + comprimento_inclinado) * numero_camadas / 5
    
    # Divisão do volume por tipo de concreto
    volume_concreto_25 = volume_concreto * 0.1  # 90% em concreto mas o muro de gravidade usa 10%
    volume_concreto_6 = volume_concreto * 0.9   # 10% em concreto de regularização
    
    return {
        'volume_concreto': volume_concreto,
        'volume_concreto_25': volume_concreto_25,
        'volume_concreto_6': volume_concreto_6,
        'area_aco': peso_aco,
        'fs_deslizamento': resultado_gravidade['fs_deslizamento'],
        'fs_tombamento': resultado_gravidade['fs_tombamento'],
        'volume_corte': volume_corte,
        'volume_aterro': volume_aterro,
        'volume_descarga': volume_descarga,
        'formas': area_formas,
        'tensao_max': resultado_gravidade['tensao_max'],
        'tensao_min': resultado_gravidade['tensao_min'],
        'pressao_adm_ok': resultado_gravidade['tensao_ok'],
        'base_teorica': resultado_gravidade['base_teorica'],
        'base_atual_ok': resultado_gravidade['base_atual_ok'],
        'base_max_ok': resultado_gravidade['base_max_ok'],
        'base_ok': resultado_gravidade['base_ok']
    }

def mostrar_avisos_iniciais():
    # Criar uma janela popup
    janela_avisos = tk.Toplevel()
    janela_avisos.title("Avisos Importantes")
    janela_avisos.geometry("800x600")
    janela_avisos.resizable(False, False)
    janela_avisos.transient(root)  # Define como modal
    janela_avisos.grab_set()       # Impede interação com a janela principal
    
    # Cabeçalho
    tk.Label(janela_avisos, text="Avisos Importantes", font=("Arial", 14, "bold")).pack(pady=10)
    
    # Área de texto com barra de rolagem
    frame_texto = tk.Frame(janela_avisos)
    frame_texto.pack(fill="both", expand=True, padx=20, pady=10)
    
    scrollbar = tk.Scrollbar(frame_texto)
    scrollbar.pack(side="right", fill="y")
    
    texto_avisos = tk.Text(frame_texto, wrap="word", yscrollcommand=scrollbar.set)
    texto_avisos.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=texto_avisos.yview)
    
    # Conteúdo dos avisos
    avisos = """
    Bem-vindo ao Programa de Dimensionamento de Muros!
    
    AVISOS IMPORTANTES:
    
    1. Este programa é uma ferramenta de auxílio ao pré-dimensionamento e não substitui o julgamento profissional de um engenheiro qualificado.
    
    2. Os cálculos são baseados em métodos simplificados e podem não considerar todas as variáveis presentes de um projeto executivo.
    
    3. A responsabilidade pela verificação dos resultados e sua aplicação em projetos executivos é inteiramente do usuário.
    
    4. Recomenda-se a validação dos resultados através de métodos alternativos e/ou consultoria especializada.
    
    5. O programa não considera planos de ruptura no solo, condições especiais de fundação ou aterro, ou outros fatores específicos que podem ser críticos em determinadas situações.
    
    Ao continuar, você confirma que leu e compreendeu estes avisos.
    """
    
    texto_avisos.insert("1.0", avisos)
    texto_avisos.config(state="disabled")  # Torna o texto não editável
    
    # Botão de confirmação
    def fechar_aviso():
        janela_avisos.destroy()
    
    tk.Button(janela_avisos, text="Concordo e Desejo Continuar", command=fechar_aviso, 
              font=("Arial", 10, "bold")).pack(pady=15)
    
    # Esperar até que a janela seja fechada
    root.wait_window(janela_avisos)

def calcular_altura_util(h):
    """
    Calcula a altura útil como h/12 arredondado de 5 em 5 cm
    """
    d_exato = h / 12
    # Arredonda para o múltiplo de 5 cm mais próximo (0.05m)
    d = round(d_exato * 20) / 20  # Dividir por 20 porque 5cm = 0.05m = 1/20m
    return max(d, 0.05)  # Garantir valor mínimo de 5 cm

# Quando clica no botao calcular chama essa função
def calcular():
    try:
        h = float(entry_h.get())
        b_jus = float(entry_b_jus.get())
        b_mon = float(entry_b_mon.get())
        d = calcular_altura_util(h)
        gamma_solo_sat = float(entry_gamma_solo_sat.get())
        gamma_solo_sub = float(entry_gamma_solo_sub.get())
        phi = float(entry_phi_estabilidade.get())
        fck = float(entry_fck.get())
        fyk = float(entry_fyk.get())

        # Capturar os valores de custo inseridos pelo usuário
        custo_concreto_25_mat = float(entry_concreto_25_mat.get())  # R$/m³
        custo_concreto_6_mat = float(entry_concreto_6_mat.get())  # R$/m³
        custo_aco_ca50_mat = float(entry_aco_ca50_mat.get())  # R$/kg
        custo_forma_mat = float(entry_forma_mat.get())  # R$/m²
        custo_aterro_mat = float(entry_aterro_mat.get())  # R$/m³
        custo_corte_mat = float(entry_corte_mat.get())  # R$/m³
        custo_carga_mat = float(entry_carga_mat.get())  # R$/m³
        custo_descarga_mat = float(entry_descarga_mat.get())  # R$/m³
        custo_forma_mat = float(entry_forma_mat.get())  # R$/m²
        
        custo_concreto_25_mdo = float(entry_concreto_25_mdo.get())  # R$/m³
        custo_concreto_6_mdo = float(entry_concreto_6_mdo.get())  # R$/m³
        custo_aco_ca50_mdo = float(entry_aco_ca50_mdo.get())  # R$/kg
        custo_aterro_mdo = float(entry_aterro_mdo.get())  # R$/m³
        custo_corte_mdo = float(entry_corte_mdo.get())  # R$/m³
        custo_carga_mdo = float(entry_carga_mdo.get())  # R$/m³
        custo_descarga_mdo = float(entry_descarga_mdo.get())  # R$/m³
        custo_forma_mdo = float(entry_forma_mdo.get())  # R$/m²

        custo_concreto_25_tempo = float(entry_concreto_25_tempo.get())  # R$/m³
        custo_concreto_6_tempo = float(entry_concreto_6_tempo.get())  # R$/m³
        custo_aco_ca50_tempo = float(entry_aco_ca50_tempo.get())  # R$/kg
        custo_aterro_tempo = float(entry_aterro_tempo.get())  # R$/m³
        custo_corte_tempo = float(entry_corte_tempo.get())  # R$/m³
        custo_carga_tempo = float(entry_carga_tempo.get())  # R$/m³
        custo_descarga_tempo = float(entry_descarga_tempo.get())  # R$/m³
        custo_forma_tempo = float(entry_forma_tempo.get())  # R$/m²
        

        # Obter os valores dos parâmetros de estabilidade
        gamma_concreto = float(entry_gamma_concreto.get())
        nivel_agua = float(entry_nivel_agua.get())
        ka = float(entry_ka.get())  # Coeficiente de empuxo ativo para muro de flexão
        k0 = float(entry_k0.get())  # Coeficiente de empuxo em repouso para muro de gravidade
        pressao_adm = float(entry_pressao_adm.get())
        sobrecarga_mon = float(entry_sobrecarga_mon.get())
        gamma_agua = float(entry_gamma_agua.get())
        
        # Obter o valor da base máxima permitida
        base_max = float(entry_base_max.get())
        
        c = float(entry_coesao.get())
        phi_estabilidade = float(entry_phi_estabilidade.get())

        # Chamar a função de dimensionamento aqui
        resultados_dimensionamento = dimensionar_muro_arrimo_flexao(h, b_mon, d, gamma_solo_sat, gamma_solo_sub, phi, fck, fyk, ka, nivel_agua)
        dia_barra = resultados_dimensionamento['dia_barra']
        espacamento = resultados_dimensionamento['espacamento']
        as_final = math.pi * (dia_barra/10)**2 / 4 * 100 / espacamento  # área de uma barra em cm²

        peso_corte, _, volume_aterro, volume_corte = calcular_peso_terra_montante(h, b_mon, gamma_solo_sat, gamma_solo_sub)
        volume_corte = peso_corte / gamma_solo_sat

        # Exemplo de resultados gerados
        volume_concreto_25 = (h + b_jus + b_mon) * d - d * d 
        volume_concreto_6 = 0  # Muro de flexão não usa esse concreto
        peso_aco_ca50 = as_final * 7.85 * (h + b_jus + b_mon * 1.4) * 0.7 # Verificar armadura horizontal (esse 1,4 multiplicando) 0.7 é o fator de redução (a seção inteira não é armada pro momento máximo)

        # Calcula o volume de carga e descarga
        volume_carga = max(volume_corte - volume_aterro, 0)
        volume_descarga = max(volume_aterro - volume_corte, 0)

        # Calcula a área de formas
        altura_max_camada = 1.5 # Altura máxima da camada de concretagem
        num_camadas = math.ceil(h / altura_max_camada)
        reutilizacoes_forma = 5 # Quantidade de reutilizações da forma

        if num_camadas > reutilizacoes_forma:
            area_forma = 2 * num_camadas
        else:
            area_forma = 2 * h / reutilizacoes_forma

                # Atualizar os labels com os resultados
        label_concreto_25.config(text=f"{volume_concreto_25:.2f}")
        label_total_concreto_25.config(text=f"{volume_concreto_25 * (custo_concreto_25_mat + custo_concreto_25_mdo):.2f}")

        label_concreto_6.config(text=f"{volume_concreto_6:.2f}")
        label_total_concreto_6.config(text=f"{volume_concreto_6 * (custo_concreto_6_mat + custo_concreto_6_mdo):.2f}")

        label_aco_ca50.config(text=f"{peso_aco_ca50:.2f}")
        label_total_aco_ca50.config(text=f"{peso_aco_ca50 * (custo_aco_ca50_mat + custo_aco_ca50_mdo):.2f}")

        label_aterro.config(text=f"{volume_aterro:.2f}")
        label_total_aterro.config(text=f"{volume_aterro * (custo_aterro_mat + custo_aterro_mdo):.2f}")
        
        label_corte.config(text=f"{volume_corte:.2f}")
        label_total_corte.config(text=f"{volume_corte * (custo_corte_mat + custo_corte_mdo):.2f}")

        label_carga.config(text=f"{volume_carga:.2f}")
        label_total_carga.config(text=f"{volume_carga * (custo_carga_mat + custo_carga_mdo):.2f}")

        label_descarga.config(text=f"{volume_descarga:.2f}")
        label_total_descarga.config(text=f"{volume_descarga * (custo_descarga_mat + custo_descarga_mdo):.2f}")

        label_forma.config(text=f"{area_forma:.2f}")
        label_total_forma.config(text=f"{area_forma * (custo_forma_mat + custo_forma_mdo):.2f}")
        
        # Chamar a função de verificação de estabilidade
        fs_coesao = float(entry_fs_coesao.get())
        fs_atrito = float(entry_fs_atrito.get())

        resultados_estabilidade = verificar_estabilidade_flexao(
            h, d, b_jus, b_mon, gamma_solo_sat, gamma_solo_sub, phi_estabilidade,
            gamma_concreto, nivel_agua, ka, pressao_adm,
            c, fs_coesao, fs_atrito, sobrecarga_mon, base_max
        )
        
        # Exibir os resultados da verificação de estabilidade
        print("Resultados da Verificação de Estabilidade:")
        print(f"Fator de Segurança ao Tombamento: {resultados_estabilidade['fs_tombamento']:.2f}")
        print(f"Tensão Máxima na Base: {resultados_estabilidade['tensao_max']:.2f} kN/m²")
        print(f"Tensão Mínima na Base: {resultados_estabilidade['tensao_min']:.2f} kN/m²")
        print(f"Pressão Admissível OK: {resultados_estabilidade['pressao_adm_ok']}")
        print(f"Fator de Segurança ao Tombamento OK: {resultados_estabilidade['fs_tombamento_ok']}")
        print(f"Fator de Segurança ao Deslizamento OK: {resultados_estabilidade['fs_deslizamento_ok']}")
        print(f"Base Teórica Necessária: {resultados_estabilidade['base_teorica']:.2f} m")
        print(f"Base Atual: {b_jus + b_mon:.2f} m")
        print(f"Base Máxima Permitida: {base_max:.2f} m")
        print(f"Base Atual Suficiente: {resultados_estabilidade['base_atual_ok']}")
        print(f"Base Dentro do Limite Máximo: {resultados_estabilidade['base_max_ok']}")
        
        if resultados_estabilidade['base_ok']:
            print("VERIFICAÇÃO DE BASE: OK - A base atual é adequada para a estabilidade do muro e está dentro do limite máximo permitido.")
        else:
            print("VERIFICAÇÃO DE BASE: NÃO OK")
            if not resultados_estabilidade['base_atual_ok']:
                print("  - A base atual é menor que a base teórica necessária para a estabilidade.")
                print(f"  - Sugestão: Aumentar a base em pelo menos {resultados_estabilidade['base_teorica'] - (b_jus + b_mon):.2f} m.")
            if not resultados_estabilidade['base_max_ok']:
                print("  - A base teórica necessária é maior que a base máxima permitida.")
                print("  - Sugestão: Reconsiderar os parâmetros de projeto ou aumentar a base máxima permitida.")
        
        # Atualizar exibição dos resultados
        entry_fs_coesao.config(text=f"{fs_coesao:.2f}")
        entry_fs_atrito.config(text=f"{fs_atrito:.2f}")

        # Pega os valores para calculo de quantitativos de gravidade
        crista = float(entry_crista.get())
        b_gravidade = float(entry_b_gravidade.get())
        inclinacao = var_inclinacao.get()  # Obter a inclinação escolhida pelo usuário

        quantitativos_gravidade = gerar_quantitativos_gravidade(h, crista, b_gravidade, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, ka, gamma_agua, sobrecarga_mon, base_max, inclinacao)
        resultado_gravidade = calcular_muro_gravidade(h, crista, b_gravidade, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, ka, gamma_agua, sobrecarga_mon, base_max, inclinacao)
        
        # Exibir os resultados da verificação de estabilidade para o muro de gravidade (opcional)
        print("\n==== Resultados do Muro de Gravidade ====")
        print(f"Fator de Segurança ao Deslizamento: {resultado_gravidade['fs_deslizamento']:.2f}")
        print(f"Fator de Segurança ao Tombamento: {resultado_gravidade['fs_tombamento']:.2f}")
        print(f"Tensão Máxima na Base: {resultado_gravidade['tensao_max']:.2f} kN/m²")
        print(f"Tensão Mínima na Base: {resultado_gravidade['tensao_min']:.2f} kN/m²")
        
        # Exibir informações sobre a base teórica para o muro de gravidade
        print(f"Base Teórica Necessária: {resultado_gravidade['base_teorica']:.2f} m")
        print(f"Base Atual: {b_gravidade:.2f} m")
        print(f"Base Máxima Permitida: {base_max:.2f} m")
        print(f"Base Atual Suficiente: {resultado_gravidade['base_atual_ok']}")
        print(f"Base Dentro do Limite Máximo: {resultado_gravidade['base_max_ok']}")
        
        if resultado_gravidade['base_ok']:
            print("VERIFICAÇÃO DE BASE: OK - A base do muro de gravidade é adequada e está dentro do limite máximo permitido.")
        else:
            print("VERIFICAÇÃO DE BASE: NÃO OK")
            if not resultado_gravidade['base_atual_ok']:
                print(f"  - A base atual é menor que a base teórica necessária para a estabilidade.")
                print(f"  - Sugestão: Aumentar a base em pelo menos {resultado_gravidade['base_teorica'] - b_gravidade:.2f} m.")
            if not resultado_gravidade['base_max_ok']:
                print(f"  - A base teórica necessária é maior que a base máxima permitida.")
                print(f"  - Sugestão: Reconsiderar os parâmetros de projeto ou aumentar a base máxima permitida.")

        # Atualizar os labels com os resultados
        label_concreto_25_grav.config(text=f"{quantitativos_gravidade['volume_concreto_25']:.2f}")
        label_total_concreto_25_grav.config(text=f"{quantitativos_gravidade['volume_concreto_25'] * (custo_concreto_25_mat + custo_concreto_25_mdo):.2f}")

        label_concreto_6_grav.config(text=f"{quantitativos_gravidade['volume_concreto_6']:.2f}")
        label_total_concreto_6_grav.config(text=f"{quantitativos_gravidade['volume_concreto_6'] * (custo_concreto_6_mat + custo_concreto_6_mdo):.2f}")

        label_aco_ca50_grav.config(text=f"{quantitativos_gravidade['area_aco']:.2f}")
        label_total_aco_ca50_grav.config(text=f"{quantitativos_gravidade['area_aco'] * (custo_aco_ca50_mat + custo_aco_ca50_mdo):.2f}")

        label_aterro_grav.config(text=f"{quantitativos_gravidade['volume_aterro']:.2f}")
        label_total_aterro_grav.config(text=f"{quantitativos_gravidade['volume_aterro'] * (custo_aterro_mat + custo_aterro_mdo):.2f}")
        
        # Novos cálculos para os custos adicionais
        label_corte_grav.config(text=f"{quantitativos_gravidade['volume_corte']:.2f}")
        label_total_corte_grav.config(text=f"{quantitativos_gravidade['volume_corte'] * (custo_corte_mat + custo_corte_mdo):.2f}")

        label_carga_grav.config(text=f"{quantitativos_gravidade['volume_descarga']:.2f}")
        label_total_carga_grav.config(text=f"{quantitativos_gravidade['volume_descarga'] * (custo_carga_mat + custo_carga_mdo):.2f}")

        label_descarga_grav.config(text=f"{quantitativos_gravidade['volume_descarga']:.2f}")
        label_total_descarga_grav.config(text=f"{quantitativos_gravidade['volume_descarga'] * (custo_descarga_mat + custo_descarga_mdo):.2f}")

        label_forma_grav.config(text=f"{quantitativos_gravidade['formas']:.2f}")
        label_total_forma_grav.config(text=f"{quantitativos_gravidade['formas'] * (custo_forma_mat + custo_forma_mdo):.2f}")

        # Atualiza a soma de todos os metodos
        label_total_total.config(text=f"{volume_concreto_25 * (custo_concreto_25_mat + custo_concreto_25_mdo) + volume_concreto_6 * (custo_concreto_6_mat + custo_concreto_6_mdo) + peso_aco_ca50 * (custo_aco_ca50_mat + custo_aco_ca50_mdo) + volume_aterro * (custo_aterro_mat + custo_aterro_mdo) + volume_corte * (custo_corte_mat + custo_corte_mdo) + volume_carga * (custo_carga_mat + custo_carga_mdo) + volume_descarga * (custo_descarga_mat + custo_descarga_mdo) + area_forma * (custo_forma_mat + custo_forma_mdo):.2f}")

        label_total_total_grav.config(text=f"{quantitativos_gravidade['volume_concreto_25'] * (custo_concreto_25_mat + custo_concreto_25_mdo) + quantitativos_gravidade['volume_concreto_6'] * (custo_concreto_6_mat + custo_concreto_6_mdo) + quantitativos_gravidade['area_aco'] * (custo_aco_ca50_mat + custo_aco_ca50_mdo) + quantitativos_gravidade['volume_aterro'] * (custo_aterro_mat + custo_aterro_mdo) + quantitativos_gravidade['volume_corte'] * (custo_corte_mat + custo_corte_mdo) + quantitativos_gravidade['volume_descarga'] * (custo_carga_mat + custo_carga_mdo) + quantitativos_gravidade['formas'] * (custo_forma_mat + custo_forma_mdo):.2f}")

        # Monta as strings para exibir a estabilidade do muro
        if resultados_estabilidade['fs_tombamento_ok']:
            estavel_flexao = "OK"
        else:
            estavel_flexao = " Verif. FST"

        if resultados_estabilidade['pressao_adm_ok']:
            if estavel_flexao == "OK":
                estavel_flexao = "OK"
        else:
            if estavel_flexao == "OK":
                estavel_flexao = " Verif. Tensão"
            else:
                estavel_flexao = estavel_flexao + ", Verif. Tensão"

        if resultados_estabilidade['fs_deslizamento_ok']:
            if estavel_flexao == "OK":
                estavel_flexao = "OK"
        else:
            if estavel_flexao == "OK":
                estavel_flexao = " Verif. FSD"
            else:
                estavel_flexao = estavel_flexao + ", FSD"

        if resultado_gravidade['fs_deslizamento_ok']:
            estavel_gravidade = "OK"
        else:
            estavel_gravidade = " Verif. FSD"

        if resultado_gravidade['tensao_ok']:
            if estavel_gravidade == "OK":
                estavel_gravidade = "OK"
        else:
            if estavel_gravidade == "OK":
                estavel_gravidade = " Verif. Tensão"
            else:
                estavel_gravidade = estavel_gravidade + ", Tensão"

        if resultado_gravidade['fs_tombamento_ok']:
            if estavel_gravidade == "OK":
                estavel_gravidade = "OK"
        else:
            if estavel_gravidade == "OK":
                estavel_gravidade = " Verif. FST"
            else:
                estavel_gravidade = estavel_gravidade + " Verif. FST"

        estavel_flexao = f"Flexão: {estavel_flexao}"

        estavel_gravidade = f"Gravidade: {estavel_gravidade}"

        # Atualiza a estabilidade do muro
        label_estavel_flexao.config(text=estavel_flexao)
        label_estavel_gravidade.config(text=estavel_gravidade)

        # ===== ATUALIZAR RESUMO DE CUSTOS E TEMPO =====
        # Calcular totais para o resumo
        total_flexao = (volume_concreto_25 * (custo_concreto_25_mat + custo_concreto_25_mdo) + 
                       volume_concreto_6 * (custo_concreto_6_mat + custo_concreto_6_mdo) + 
                       peso_aco_ca50 * (custo_aco_ca50_mat + custo_aco_ca50_mdo) + 
                       volume_aterro * (custo_aterro_mat + custo_aterro_mdo) + 
                       volume_corte * (custo_corte_mat + custo_corte_mdo) + 
                       volume_carga * (custo_carga_mat + custo_carga_mdo) + 
                       volume_descarga * (custo_descarga_mat + custo_descarga_mdo) + 
                       area_forma * (custo_forma_mat + custo_forma_mdo))

        total_gravidade = (quantitativos_gravidade['volume_concreto_25'] * (custo_concreto_25_mat + custo_concreto_25_mdo) + 
                          quantitativos_gravidade['volume_concreto_6'] * (custo_concreto_6_mat + custo_concreto_6_mdo) + 
                          quantitativos_gravidade['area_aco'] * (custo_aco_ca50_mat + custo_aco_ca50_mdo) + 
                          quantitativos_gravidade['volume_aterro'] * (custo_aterro_mat + custo_aterro_mdo) + 
                          quantitativos_gravidade['volume_corte'] * (custo_corte_mat + custo_corte_mdo) + 
                          quantitativos_gravidade['volume_descarga'] * (custo_carga_mat + custo_carga_mdo) + 
                          quantitativos_gravidade['formas'] * (custo_forma_mat + custo_forma_mdo))

        # Calcular tempo total de execução (em horas)
        tempo_flexao = (volume_concreto_25 * custo_concreto_25_tempo + 
                       volume_concreto_6 * custo_concreto_6_tempo + 
                       peso_aco_ca50 * custo_aco_ca50_tempo + 
                       volume_aterro * custo_aterro_tempo + 
                       volume_corte * custo_corte_tempo + 
                       volume_carga * custo_carga_tempo + 
                       volume_descarga * custo_descarga_tempo + 
                       area_forma * custo_forma_tempo)

        tempo_gravidade = (quantitativos_gravidade['volume_concreto_25'] * custo_concreto_25_tempo + 
                          quantitativos_gravidade['volume_concreto_6'] * custo_concreto_6_tempo + 
                          quantitativos_gravidade['area_aco'] * custo_aco_ca50_tempo + 
                          quantitativos_gravidade['volume_aterro'] * custo_aterro_tempo + 
                          quantitativos_gravidade['volume_corte'] * custo_corte_tempo + 
                          quantitativos_gravidade['volume_descarga'] * custo_carga_tempo + 
                          quantitativos_gravidade['formas'] * custo_forma_tempo)

        # Atualizar labels do resumo
        label_custo_total_flexao.config(text=f"R$ {total_flexao:.2f}")
        label_custo_total_gravidade.config(text=f"R$ {total_gravidade:.2f}")
        label_tempo_total_flexao.config(text=f"{tempo_flexao:.1f} h")
        label_tempo_total_gravidade.config(text=f"{tempo_gravidade:.1f} h")
        
        # Cor verde para estável, vermelha para não estável
        cor_flexao = "green" if "OK" in estavel_flexao else "red"
        cor_gravidade = "green" if "OK" in estavel_gravidade else "red"
        
        label_estavel_flexao.config(fg=cor_flexao)
        label_estavel_gravidade.config(fg=cor_gravidade)
        
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira valores válidos.")

def botao_plotar_muro_arrimo():
    try:
        # Validar e obter valores dos campos
        campos = {
            'h': entry_h.get(),
            'b_jus': entry_b_jus.get(),
            'b_mon': entry_b_mon.get(),
            'gamma_solo_sat': entry_gamma_solo_sat.get(),
            'gamma_solo_sub': entry_gamma_solo_sub.get(),
            'phi': entry_phi_estabilidade.get(),
            'fck': entry_fck.get(),
            'fyk': entry_fyk.get(),
            'gamma_concreto': entry_gamma_concreto.get(),
            'ka': entry_ka.get(),
            'pressao_adm': entry_pressao_adm.get(),
            'c': entry_coesao.get(),
            'fs_coesao': entry_fs_coesao.get(),
            'fs_atrito': entry_fs_atrito.get(),
            'base_max': entry_base_max.get(),
            'nivel_agua': entry_nivel_agua.get()
        }

        # Verificar se algum campo está vazio
        campos_vazios = [campo for campo, valor in campos.items() if not valor.strip()]
        if campos_vazios:
            messagebox.showerror("Erro", f"Os seguintes campos estão vazios:\n{', '.join(campos_vazios)}")
            return

        # Converter valores para float
        try:
            h = float(campos['h'])
            b_jus = float(campos['b_jus'])
            b_mon = float(campos['b_mon'])
            d = calcular_altura_util(h)
            gamma_solo_sat = float(campos['gamma_solo_sat'])
            gamma_solo_sub = float(campos['gamma_solo_sub'])
            phi = float(campos['phi'])
            fck = float(campos['fck'])
            fyk = float(campos['fyk'])
            gamma_concreto = float(campos['gamma_concreto'])
            ka = float(campos['ka'])
            pressao_adm = float(campos['pressao_adm'])
            c = float(campos['c'])
            fs_coesao = float(campos['fs_coesao'])
            fs_atrito = float(campos['fs_atrito'])
            base_max = float(campos['base_max'])
            nivel_agua = float(campos['nivel_agua'])
        except ValueError as e:
            messagebox.showerror("Erro", f"Erro ao converter valores numéricos: {str(e)}")
            return

        # Validar valores negativos
        valores_negativos = []
        if h <= 0: valores_negativos.append("Altura do muro")
        if b_jus <= 0: valores_negativos.append("Largura da base a jusante")
        if b_mon <= 0: valores_negativos.append("Largura da base a montante")
        if gamma_solo_sat <= 0: valores_negativos.append("Peso específico do solo saturado")
        if gamma_solo_sub <= 0: valores_negativos.append("Peso específico do solo submerso")
        if phi <= 0: valores_negativos.append("Ângulo de atrito")
        if fck <= 0: valores_negativos.append("Resistência característica do concreto")
        if fyk <= 0: valores_negativos.append("Resistência de escoamento do aço")
        if gamma_concreto <= 0: valores_negativos.append("Peso específico do concreto")
        if ka <= 0: valores_negativos.append("Coeficiente de empuxo ativo")
        if pressao_adm <= 0: valores_negativos.append("Pressão admissível")
        if c < 0: valores_negativos.append("Coesão")
        if fs_coesao <= 0: valores_negativos.append("Fator de segurança à coesão")
        if fs_atrito <= 0: valores_negativos.append("Fator de segurança ao atrito")
        if base_max <= 0: valores_negativos.append("Base máxima")
        if nivel_agua < 0: valores_negativos.append("Nível d'água")

        if valores_negativos:
            messagebox.showerror("Erro", f"Os seguintes valores não podem ser negativos ou zero:\n{', '.join(valores_negativos)}")
            return

        # Chamar a função de dimensionamento
        resultados_dimensionamento = dimensionar_muro_arrimo_flexao(h, b_mon, d, gamma_solo_sat, gamma_solo_sub, phi, fck, fyk, ka, nivel_agua)
        dia_barra = resultados_dimensionamento['dia_barra']
        espacamento = resultados_dimensionamento['espacamento']
        as_final = math.pi * (dia_barra/10)**2 / 4 * 100 / espacamento  # área de uma barra em cm²

        # Verificação de estabilidade
        resultados_estabilidade = verificar_estabilidade_flexao(
            h, d, b_jus, b_mon, gamma_solo_sat, gamma_solo_sub, phi,
            gamma_concreto, nivel_agua, ka, pressao_adm,
            c, fs_coesao, fs_atrito, base_max
        )
        
        # Plotar o muro
        plotar_muro_arrimo(b_jus, b_mon, h, d, as_final, gamma_solo_sat, gamma_solo_sub, 
                         resultados_estabilidade['tensao_max'], pressao_adm, resultados_estabilidade, resultados_dimensionamento)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {str(e)}")

def verificar_estabilidade_flexao(h, d, b_jus, b_mon, gamma_solo_sat, gamma_solo_sub, phi_estabilidade, gamma_concreto, 
                                    nivel_agua, ka, pressao_adm, c, fs_coesao, fs_atrito, sobrecarga_mon, base_max=None):
    """
    Verifica a estabilidade do muro de arrimo considerando momentos em relação ao centro da base
    e a altura do muro, incluindo a coesão do solo.
    
    Parâmetros:
    h: altura do muro (m)
    b_jus: largura da base a jusante (m)
    b_mon: largura da base a montante (m)
    gamma_solo: peso específico do solo (kN/m³)
    phi: ângulo de atrito interno do solo (graus)
    gamma_concreto: peso específico do concreto (kN/m³)
    nivel_agua: nível d'água (m)
    ka: coeficiente de empuxo ativo
    pressao_adm: pressão admissível do solo (kN/m²)
    c: coesão do solo (kN/m²) [opcional, padrão = 0]
    fs_coesao: fator de segurança à coesão
    fs_atrito: fator de segurança ao atrito
    base_max: base máxima permitida (m) [opcional]
    
    Retorna:
    dict com fatores de segurança distintos para coesão e atrito
    """
    # Largura total da base
    b_total = b_jus + b_mon
        
    # Área da seção transversal do muro
    area_muro = ((b_total) * d) + (h * d) - (d * d)
    
    # Peso do muro por metro linear
    peso_muro = area_muro * gamma_concreto
    

    if nivel_agua > 0:
        # Solo saturado
        peso_solo_sat = (b_mon) * (h - nivel_agua) * (gamma_solo_sat)
        braco_solo_sat_PT = ((b_mon)/2 + b_jus)

        # Solo submerso
        peso_solo_sub = (b_mon) * (nivel_agua - d)* gamma_solo_sub
        braco_solo_sub_PT = (b_mon)/2 + b_jus

        # Peso da água
        peso_agua = (b_mon) * (nivel_agua - d)*(10)
        braco_agua_PT = (b_mon)/2 + b_jus
        
        # Empuxos
        e0_agua = 0.5 * 10 * nivel_agua**2
        braco_e0_agua = nivel_agua/3
        e0_solo_sat1 = 0.5 * (gamma_solo_sat) * (h-nivel_agua)**2 * ka
        braco_e0_solo_sat1 = nivel_agua + (h-nivel_agua)/3
        e0_solo_sat2 = (gamma_solo_sat) * nivel_agua * (h - nivel_agua) * ka
        braco_e0_solo_sat2 = nivel_agua/2
        e0_solo_sub = 0.5 * (gamma_solo_sub) * nivel_agua**2 * ka
        braco_e0_solo_sub = nivel_agua/3

        e0_solo_sat = e0_solo_sat1 + e0_solo_sat2
        braco_e0_solo_sat = (e0_solo_sat1 * braco_e0_solo_sat1 + e0_solo_sat2 * braco_e0_solo_sat2) / e0_solo_sat

        # Peso total
        peso_solo = peso_solo_sat + peso_solo_sub
        peso_total = peso_solo + peso_muro + peso_agua + sobrecarga_mon*(b_mon)

        # Empuxo total
        e0 = e0_solo_sat + e0_solo_sub + e0_agua
        braco_e0 = (e0_solo_sat * braco_e0_solo_sat + e0_solo_sub * braco_e0_solo_sub + e0_agua * braco_e0_agua) / e0

    else:
        peso_solo_sat = (b_mon) * h * (gamma_solo_sat)
        braco_solo_sat_PT = ((b_mon)/2 + b_jus)

        e0_solo_sat = 0.5 * (gamma_solo_sat) * h**2 * ka
        braco_e0_solo_sat = h/3

        peso_solo_sub = 0
        peso_agua = 0
        e0_agua = 0

        peso_solo = peso_solo_sat
        peso_total = peso_solo + peso_muro + sobrecarga_mon*(b_mon)
    
        e0 = e0_solo_sat
        braco_e0 = braco_e0_solo_sat

    # Centro de gravidade do muro (coordenada x em relação à extremidade jusante)
    # Componentes:
    # Base (retângulo)
    area_base = b_total * 1 # 1 m de espessura considerada
    cg_base = b_total / 2
 
    # Talão montante (retângulo)
    area_talao = (h - d) * d
    x_talao = b_jus + (d / 2)
    
    # Sobrecarga do solo
    peso_sobre = sobrecarga_mon*(b_mon)
    braco_sobre_PT = (b_mon)/2 + b_jus
    momento_sobre_PT = peso_sobre * braco_sobre_PT
    braco_sobre_CG = braco_sobre_PT - cg_base
    momento_sobre_CG = peso_sobre * braco_sobre_CG

    # Empuxo de sobrecarga do solo
    e_sobre = sobrecarga_mon * ka
    braco_e_sobre_CG = h/2
    momento_e_sobre_CG = e_sobre * braco_e_sobre_CG

    e0 = e0 + e_sobre 

    # CG total
    x_muro = (area_base*cg_base + area_talao*x_talao) / area_muro

    # CG da sobrecarga
    x_sobre = b_jus + (b_mon)/2
    
    # Força normal total na base
    forca_normal = peso_muro + peso_solo + peso_agua + peso_sobre # Colocar aqui a subpressão depois
    
    # Isso permite que o usuário defina fatores de segurança diferentes 
    # para cada componente de resistência, 
    # seguindo as recomendações da NBR 11682/2022 para contenções.

    # Forças resistentes ao deslizamento
    resistencia_coesao = c * b_total
    resistencia_atrito = forca_normal * math.tan(math.radians(phi_estabilidade))
    
    # Fatores de segurança parciais
    fs_deslizamento_total = (resistencia_coesao / (e0 * fs_coesao)) + (resistencia_atrito / (e0 * fs_atrito))
    
    # Momentos em relação ao centro da base (momento estabilizante)
    momento_muro_cg = peso_muro * (x_muro - cg_base)
    momento_solo_sat_cg = peso_solo_sat * (braco_solo_sat_PT - cg_base)
    momento_solo_sub_cg = peso_solo_sub * (braco_solo_sub_PT - cg_base)
    momento_agua_cg = peso_agua * (braco_agua_PT - cg_base)

    # Momentos em relação ao ponto de tombamento (momento estabilizante)
    momento_muro = peso_muro * x_muro
    momento_solo_sat = peso_solo_sat * braco_solo_sat_PT
    momento_solo_sub = peso_solo_sub * braco_solo_sub_PT
    momento_agua = peso_agua * braco_agua_PT

    # Momento estabilizante total no CG da base
    me_cg = momento_muro_cg + momento_solo_sat_cg + momento_solo_sub_cg + momento_agua_cg + momento_sobre_CG
    
    # Momento estabilizante total
    me = momento_muro + momento_solo_sat + momento_solo_sub + momento_agua + momento_sobre_PT

    mt = (e0 - e_sobre) * braco_e0 + e_sobre * braco_e_sobre_CG
    
    # Fator de segurança ao tombamento
    fs_tombamento = me / mt 
    
   # Tensões na base
    tensao_max = forca_normal / b_total + abs(6 * (me_cg - mt) / b_total**2)
    tensao_min = forca_normal / b_total - abs(6 * (me_cg - mt) / b_total**2)
    
    # Verificação da pressão admissível
    pressao_adm_ok = tensao_max <= pressao_adm
    
    # Verificação do fator de segurança ao tombamento
    fs_tombamento_ok = fs_tombamento >= 1.5  # Valor mínimo recomendado pela NBR 11682

    # Verificação do fator de segurança ao deslizamento
    fs_deslizamento_ok = fs_deslizamento_total >= 1.0
    
    # Verificação da base
    base_teorica = math.sqrt(6 * abs(me_cg - mt) / pressao_adm)
    base_atual_ok = b_total >= base_teorica
    base_max_ok = base_teorica <= base_max if base_max is not None else True
    base_ok = base_atual_ok and base_max_ok
    
    return {
        'fs_tombamento': fs_tombamento,
        'nivel_agua': nivel_agua,
        'fs_tombamento_ok': fs_tombamento_ok,
        'tensao_max': tensao_max,
        'tensao_min': tensao_min,
        'pressao_adm_ok': pressao_adm_ok,
        'fs_deslizamento_ok': fs_deslizamento_ok,
        'fs_deslizamento_total': fs_deslizamento_total,
        'base_teorica': base_teorica,
        'base_atual_ok': base_atual_ok,
        'base_max_ok': base_max_ok if base_max is not None else True,
        'base_ok': base_ok,
        'peso_muro': peso_muro,
        'x_muro': x_muro,
        'momento_muro': momento_muro,
        'peso_solo': peso_solo,
        'peso_solo_sat': peso_solo_sat,
        'peso_solo_sub': peso_solo_sub,
        'peso_agua': peso_agua,
        'braco_solo_sat_PT': braco_solo_sat_PT,
        'braco_solo_sub_PT': braco_solo_sub_PT,
        'braco_agua_PT': braco_agua_PT,
        'x_sobre': x_sobre,
        'momento_solo_sat': momento_solo_sat,
        'momento_solo_sub': momento_solo_sub,
        'momento_agua': momento_agua,
        'momento_sobre_PT': momento_sobre_PT,
        'momento_sobre_CG': momento_sobre_CG,
        'momento_e_sobre_CG': momento_e_sobre_CG,
        'e0': e0,
        'e_agua': e0_agua,
        'braco_e0': braco_e0,
        'mt': mt,
        'me': me,
        'me_cg': me_cg,
        'forca_normal': forca_normal,
        'cg_base': cg_base,
        'e0_agua': e0_agua,
        'e0_solo_sat': e0_solo_sat,
        'e0_solo_sub': e0_solo_sub,
    }

def dimensionar_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua=0, fs_coesao=4, fs_atrito=2, k0=0.5, gamma_agua=10, sobrecarga_mon=0, inclinacao="montante"):
    """
    Dimensiona o muro de gravidade calculando cargas, empuxos e parâmetros geométricos básicos
    
    Parâmetros:
    h: altura total do muro (m)
    crista: largura da crista (m)
    b_mon: largura da base a montante (m)
    gamma_concreto: peso específico do concreto (kN/m³)
    gamma_solo_sat: peso específico do solo saturado (kN/m³)
    gamma_solo_sub: peso específico do solo submerso (kN/m³)
    phi: ângulo de atrito interno do solo (graus)
    c: coesão do solo (kN/m²)
    pressao_adm: pressão admissível do solo (kN/m²)
    nivel_agua: nível d'água (m)
    fs_coesao: fator de segurança à coesão
    fs_atrito: fator de segurança ao atrito
    k0: coeficiente de empuxo em repouso
    gamma_agua: peso específico da água (kN/m³)
    sobrecarga_mon: sobrecarga a montante (kN/m²)
    inclinacao: direção da inclinação ("montante" ou "jusante")
    
    Retorna:
    dict com parâmetros calculados para dimensionamento
    """

    # Variaveis
    peso_solo_sat1 = 0
    peso_solo_sat2 = 0
    peso_solo_sub = 0
    peso_solo = 0
    peso_agua = 0
    peso_muro = 0
    peso_total = 0
    braco_solo_sat_PT1 = 0
    braco_solo_sat_PT2 = 0
    braco_solo_sub_PT = 0
    braco_agua_PT = 0
    braco_e0_agua = 0
    braco_e0_solo_sat1 = 0
    braco_e0_solo_sat2 = 0
    braco_e0_solo_sub = 0
    momento_solo_sat1 = 0
    momento_solo_sat2 = 0
    momento_solo_sub = 0
    momento_agua = 0
    momento_muro = 0
    momento_e0_agua = 0
    momento_e0_solo_sat1 = 0
    momento_e0_solo_sat2 = 0
    momento_e0_solo_sub = 0
    e0_agua = 0
    e0_solo_sat1 = 0
    e0_solo_sat2 = 0
    e0_solo_sub = 0
    momento_sobrecarga_est_CG = 0
    momento_sobrecarga_dest = 0


    # Calcular cargas
    area_muro = 0.5 * (b_mon - crista) * h + crista * h
    peso_muro = area_muro * gamma_concreto

    # Dividir muro em trechos
    peso_muro_1 = 0.5 * (b_mon - crista) * h * gamma_concreto
    braco_muro_PT1 = (b_mon - crista) * 1 / 3 + crista
    peso_muro_2 = crista * h * gamma_concreto
    braco_muro_PT2 = crista/2

    peso_muro = peso_muro_1 + peso_muro_2
    
    braco_muro_PT = (peso_muro_1 * braco_muro_PT1 + peso_muro_2 * braco_muro_PT2) / peso_muro

    x_cg = b_mon/2

    braco_muro_CG1 = braco_muro_PT1 - x_cg
    braco_muro_CG2 = braco_muro_PT2 - x_cg

    # Para o eixo Y:
    braco_muro_y1 = h/2
    braco_muro_y2 = h/3

    braco_muro_y = (peso_muro_1 * braco_muro_y1 + peso_muro_2 * braco_muro_y2) / peso_muro
    
    if nivel_agua > 0:
        intersecao = b_mon - (nivel_agua) * (b_mon - crista) / h

        # Solo saturado
        peso_solo_sat1 = 0.5 * (intersecao - crista) * (h - nivel_agua) * (gamma_solo_sat)
        braco_solo_sat_PT1 = ((intersecao - crista)*2/3 + crista)

        peso_solo_sat2 = (b_mon - intersecao) * (h - nivel_agua) * (gamma_solo_sat)
        braco_solo_sat_PT2 = intersecao + (b_mon - intersecao)/2

        peso_solo_sat = peso_solo_sat1 + peso_solo_sat2
        braco_solo_sat_PT = (peso_solo_sat1 * braco_solo_sat_PT1 + peso_solo_sat2 * braco_solo_sat_PT2) / peso_solo_sat
        
        # Solo submerso
        peso_solo_sub = 0.5 * (b_mon - intersecao) * nivel_agua * gamma_solo_sub
        braco_solo_sub_PT = intersecao + (b_mon - intersecao)*2/3

        # Peso da água
        peso_agua = 0.5 * (b_mon - intersecao) * nivel_agua * (gamma_agua)
        braco_agua_PT = intersecao + (b_mon - intersecao)*2/3

        # Empuxos
        e0_agua = 0.5 * gamma_agua * nivel_agua**2
        braco_e0_agua = nivel_agua/3
        e0_solo_sat1 = 0.5 * (gamma_solo_sat) * (h-nivel_agua)**2 * k0
        braco_e0_solo_sat1 = nivel_agua + (h-nivel_agua)/3
        e0_solo_sat2 = (gamma_solo_sat) * nivel_agua * (h - nivel_agua) * k0
        braco_e0_solo_sat2 = nivel_agua/2
        e0_solo_sub = 0.5 * (gamma_solo_sub) * nivel_agua**2 * k0
        braco_e0_solo_sub = nivel_agua/3

        e0_solo_sat = e0_solo_sat1 + e0_solo_sat2
        braco_e0_solo_sat = (e0_solo_sat1 * braco_e0_solo_sat1 + e0_solo_sat2 * braco_e0_solo_sat2) / e0_solo_sat

        # Peso total
        peso_total = peso_solo_sat1 + peso_solo_sat2 + peso_solo_sub + peso_agua + peso_muro + sobrecarga_mon*(b_mon - crista)

        # Empuxo total
        e0 = e0_solo_sat + e0_solo_sub + e0_agua
        braco_e0 = (e0_solo_sat * braco_e0_solo_sat + e0_solo_sub * braco_e0_solo_sub + e0_agua * braco_e0_agua) / e0


    else:
        peso_solo_sat1 = 0.5 * (b_mon - crista) * h * (gamma_solo_sat)
        braco_solo_sat_PT1 = (b_mon - crista) * 2 / 3 + crista

        peso_solo_sat = peso_solo_sat1
        braco_solo_sat_PT = braco_solo_sat_PT1

        e0_solo_sat = 0.5 * (gamma_solo_sat) * h**2 * k0
        braco_e0_solo_sat = h/3

        peso_solo_sub = 0
        peso_agua = 0
        e0_agua = 0

        peso_total = peso_solo_sat1 + peso_muro + sobrecarga_mon*(b_mon - crista)
    
    # Cálculo do momento total em relação ao ponto de tombamento
    momento_solo_sat = peso_solo_sat*(braco_solo_sat_PT - x_cg)
    momento_solo_sub = peso_solo_sub*(braco_solo_sub_PT - x_cg)
    momento_agua = peso_agua*(braco_agua_PT - x_cg)
    momento_muro = peso_muro*(braco_muro_PT - x_cg)

    if nivel_agua == 0:
        momento_e0 = -e0*braco_e0
    else:
        momento_e0_agua = e0_agua*braco_e0_agua
        momento_e0_solo_sat = e0_solo_sat*braco_e0_solo_sat
        momento_e0_solo_sub = e0_solo_sub*braco_e0_solo_sub

        # Momentos totais:
        momento_e0 = -(momento_e0_agua + momento_e0_solo_sat + momento_e0_solo_sub)

    momento_est_total = 0
    if braco_solo_sat_PT - x_cg >= 0:
        momento_est_total =+ momento_solo_sat
    if braco_solo_sub_PT - x_cg >= 0:
        momento_est_total =+ momento_solo_sub
    if braco_agua_PT - x_cg >= 0:
        momento_est_total =+ momento_agua
    if braco_muro_PT - x_cg >= 0:
        momento_est_total =+ momento_muro
    
    momento_dest_total = 0
    if braco_muro_PT - x_cg <= 0:
        momento_dest_total =+ momento_muro
    if braco_solo_sat_PT - x_cg <= 0:
        momento_dest_total =+ momento_solo_sat
    if braco_solo_sub_PT - x_cg <= 0:
        momento_dest_total =+ momento_solo_sub
    if braco_agua_PT - x_cg <= 0:
        momento_dest_total =+ momento_agua
    
    momento_dest_total =+ momento_e0
    
    if sobrecarga_mon > 0:
        momento_sobrecarga_est_CG = sobrecarga_mon*(b_mon - crista)*((b_mon - crista)/2 + crista)
        momento_sobrecarga_dest = sobrecarga_mon*k0*h**2 * 0.5
        momento_dest_total =+ momento_sobrecarga_dest
        momento_est_total =+ momento_sobrecarga_est_CG
    
    momento_CG = momento_est_total - abs(momento_dest_total)
    FST = abs(momento_est_total/momento_dest_total)

    tensao_max = peso_total/b_mon + abs(momento_CG/(b_mon**2/6))
    tensao_min = peso_total/b_mon - abs(momento_CG/(b_mon**2/6))
    

    # 1. Cálculos geométricos e de peso com base na inclinação
    area_muro = 0.5 * (b_mon - crista) * h + crista * h  # Mesma área independente da inclinação
    volume_concreto = area_muro
    peso_muro = volume_concreto * gamma_concreto
    
    if inclinacao == "jusante":
        # Face externa inclinada
        peso_solo = 0.5 * (b_mon - crista) * h * gamma_solo_sat
        sobrecarga_mon_vertical = sobrecarga_mon * (b_mon - crista)
        peso_agua = 0


    """
    h_total = h + h_sc
    e0 = 0.5 * gamma_solo_sub * h**2 * k0  # Empuxo em repouso
    e0_agua = 0.5 * gamma_agua * nivel_agua**2

    empuxo_total = e0 + e0_agua + e0_sc
    """
    
    # 2. Cálculo dos empuxos
    h_sc = sobrecarga_mon * k0  # Altura da sobrecarga
    e0_sc = sobrecarga_mon * h_sc * k0

    # 3. Verificação ao Deslizamento
    fs_deslizamento = c * b_mon / (e0 * fs_coesao) + (peso_total)*math.tan(math.radians(phi)) / (e0 * fs_atrito)
    fs_deslizamento_ok = fs_deslizamento >= 1.0  # Valor mínimo recomendado pela NBR 11682 <- Já está incorporado no cálculo

    # 4. Verificação ao Tombamento
    braco_estabilizante_pt = (b_mon - crista)/3 + crista # Em relação ao ponto de tombamento
    terra_estabilizante_pt = (b_mon - crista)*2/3 + crista    # Em relação ao ponto de tombamento
    braco_tombamento_pt = h/3
    fs_tombamento = FST
    # fs_tombamento = (peso_muro*braco_estabilizante_pt + peso_solo*terra_estabilizante_pt + sobrecarga_mon_vertical*((b_mon - crista)/2+crista)) / ((e0 - e0_sc)*braco_tombamento_pt + e0_sc*h/2)
    fs_tombamento_ok = fs_tombamento >= 1.5  # Valor para caso de carregamento normal ELETROBRAS 2003

    # 5. Verificação de Tensões na Base
    x_cg = b_mon/2
    y_cg = h/3 * (2*crista + b_mon)/(crista + b_mon)
    braco_estabilizante_cg = ((b_mon - crista)/3 + crista) - x_cg # Em relação ao centro da base
    terra_estabilizante_cg = ((b_mon - crista)*2/3 + crista) - x_cg    # Em relação ao centro da base
    braco_tombamento = h/3
    tensao_ok = tensao_max <= pressao_adm and tensao_min >= 0
    
    # 4. Cálculo dos momentos
    momento_inercia = (1/6)*b_mon**2
    peso_total = peso_muro + peso_solo
    momento_empuxos = e0*braco_tombamento + e0_agua*nivel_agua/3 + e0_sc*h/2
    momento_total = peso_muro*braco_estabilizante_cg + peso_solo*terra_estabilizante_cg + sobrecarga_mon*((b_mon - crista)/2+crista) - e0*braco_tombamento
    
    # 5. Cálculo dos volumes de solo
    volume_corte = 1.5 * b_mon * (h - 1)  # Fator 1.5 para inclinação de talude
    volume_aterro = volume_corte - 0.5 * b_mon * h  # Aterro compactado atrás do muro
    volume_descarga = max(volume_corte - volume_aterro, 0)  # Solo excedente
    
    return {
        'area_muro': area_muro,
        'volume_concreto': volume_concreto,
        'peso_muro': peso_muro,
        'peso_solo': peso_solo,
        'peso_agua': peso_agua,
        'empuxo_total': e0,
        'e0': e0,
        'tensao_ok': tensao_ok,
        'e0_agua': e0_agua,
        'e0_sc': e0_sc,
        'x_cg': x_cg,
        'y_cg': y_cg,
        'braco_estabilizante_pt': braco_estabilizante_pt,
        'terra_estabilizante_pt': terra_estabilizante_pt,
        'braco_tombamento_pt': braco_tombamento_pt,
        'braco_estabilizante_cg': braco_estabilizante_cg,
        'terra_estabilizante_cg': terra_estabilizante_cg,
        'braco_tombamento': braco_tombamento,
        'momento_inercia': momento_inercia,
        'peso_total': peso_total,
        'momento_empuxos': momento_empuxos,
        'momento_total': momento_total,
        'volume_corte': volume_corte,
        'volume_aterro': volume_aterro,
        'volume_descarga': volume_descarga,
        'e0_agua': e0_agua,
        'e0_sc': e0_sc,
        'e0': e0,
        'e0_solo_sat1': e0_solo_sat1,
        'e0_solo_sat2': e0_solo_sat2,
        'e0_solo_sub': e0_solo_sub,
        'e0_agua': e0_agua,
        'e0_solo_sat': e0_solo_sat,
        'FST': FST,
        'tensao_max': tensao_max,
        'tensao_min': tensao_min
    }

def verificar_estabilidade_muro_gravidade(dados_dimensionamento, h, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua=0, fs_coesao=4, fs_atrito=2, k0=0.5, base_max=None, gamma_agua=10, sobrecarga_mon=0, inclinacao="montante"):
    """
    Verifica a estabilidade do muro de gravidade usando os dados de dimensionamento
    
    Parâmetros:
    dados_dimensionamento: dicionário retornado pela função dimensionar_muro_gravidade
    [demais parâmetros iguais à função de dimensionamento]
    base_max: base máxima permitida (m) [opcional]
    
    Retorna:
    dict com resultados das verificações de estabilidade
    """
    # Extrair dados do dimensionamento
    peso_muro = dados_dimensionamento['peso_muro']
    peso_solo = dados_dimensionamento['peso_solo']
    empuxo_total = dados_dimensionamento['empuxo_total']
    e0 = dados_dimensionamento['e0']
    e0_sc = dados_dimensionamento['e0_sc']
    braco_estabilizante_pt = dados_dimensionamento['braco_estabilizante_pt']
    terra_estabilizante_pt = dados_dimensionamento['terra_estabilizante_pt']
    braco_tombamento_pt = dados_dimensionamento['braco_tombamento_pt']
    braco_estabilizante_cg = dados_dimensionamento['braco_estabilizante_cg']
    terra_estabilizante_cg = dados_dimensionamento['terra_estabilizante_cg']
    braco_tombamento = dados_dimensionamento['braco_tombamento']
    momento_inercia = dados_dimensionamento['momento_inercia']
    peso_total = dados_dimensionamento['peso_total']
    peso_agua = dados_dimensionamento['peso_agua']
    momento_total = dados_dimensionamento['momento_total']
    
    # 1. Verificação ao Deslizamento
    fs_deslizamento = c * b_mon / (empuxo_total * fs_coesao) + (peso_muro + peso_solo + peso_agua)*math.tan(math.radians(phi)) / (empuxo_total * fs_atrito)
    fs_deslizamento_ok = fs_deslizamento >= 1.0  # Valor mínimo recomendado pela NBR 11682

    # 2. Verificação ao Tombamento
    fs_tombamento = (peso_muro*braco_estabilizante_pt + peso_solo*terra_estabilizante_pt + sobrecarga_mon*((b_mon - crista)/2+crista)) / ((empuxo_total - e0_sc)*braco_tombamento_pt + e0_sc*h/2)
    fs_tombamento_ok = fs_tombamento >= 1.5  # Valor para caso de carregamento normal ELETROBRAS 2003

    # 3. Verificação de Tensões na Base
    tensao_max = peso_total/b_mon + abs(momento_total/momento_inercia)
    tensao_min = peso_total/b_mon - abs(momento_total/momento_inercia)

    # tensao_max = (peso_muro + peso_solo)/b_mon * (1 + 6*excentricidade/b_mon)
    # tensao_min = (peso_muro + peso_solo)/b_mon * (1 - 6*excentricidade/b_mon)
    tensao_ok = tensao_max <= pressao_adm and tensao_min >= 0
    
    # 4. Cálculo da base teórica necessária
    # Considerando os critérios de estabilidade:
    # 1. Tensão máxima <= pressão admissível
    # 2. Fator de segurança contra tombamento >= 1.5
    # 3. Fator de segurança contra deslizamento >= 1.0
    
    # Base teórica para satisfazer pressão admissível
    base_teorica_pressao = b_mon * (tensao_max / pressao_adm) if pressao_adm > 0 else b_mon
    
    # Base teórica para satisfazer fator de segurança contra tombamento
    base_teorica_tombamento = b_mon * (1.5 / fs_tombamento) if fs_tombamento > 0 else b_mon * 1.5
    
    # Base teórica para satisfazer fator de segurança contra deslizamento
    base_teorica_deslizamento = b_mon * (1.0 / fs_deslizamento) if fs_deslizamento > 0 else b_mon
    
    # Base teórica necessária é o maior valor dentre os três critérios
    base_teorica = max(base_teorica_pressao, base_teorica_tombamento, base_teorica_deslizamento)
    
    # 5. Verificação se a base teórica é menor que a base máxima permitida
    base_atual_ok = base_teorica <= b_mon
    base_max_ok = True
    
    # Verificar se a base teórica é menor que a base máxima permitida
    if base_max is not None:
        base_max_ok = base_teorica <= base_max
    
    # A base só está OK se atende ambos os critérios
    base_ok = base_atual_ok and base_max_ok
    
    return {
        'fs_deslizamento': fs_deslizamento,
        'fs_deslizamento_ok': fs_deslizamento_ok,
        'fs_tombamento': fs_tombamento,
        'fs_tombamento_ok': fs_tombamento_ok,
        'tensao_max': tensao_max,
        'tensao_min': tensao_min,
        'tensao_ok': tensao_ok,
        'base_teorica': base_teorica,
        'base_atual_ok': base_atual_ok,
        'base_max_ok': base_max_ok,
        'base_ok': base_ok,
        'base_teorica_pressao': base_teorica_pressao,
        'base_teorica_tombamento': base_teorica_tombamento,
        'base_teorica_deslizamento': base_teorica_deslizamento
    }

def calcular_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua=0, fs_coesao=4, fs_atrito=2, k0=0.5, base_max=None, gamma_agua=10, sobrecarga_mon=0, inclinacao="montante"):
    """
    Função principal que combina dimensionamento e verificação do muro de gravidade
    
    Parâmetros:
    h: altura total do muro (m)
    crista: largura da crista (m)
    b_mon: largura da base a montante (m)
    gamma_concreto: peso específico do concreto (kN/m³)
    gamma_solo_sat: peso específico do solo saturado (kN/m³)
    gamma_solo_sub: peso específico do solo submerso (kN/m³)
    phi: ângulo de atrito interno do solo (graus)
    c: coesão do solo (kN/m²)
    pressao_adm: pressão admissível do solo (kN/m²)
    nivel_agua: nível d'água (m)
    fs_coesao: fator de segurança à coesão
    fs_atrito: fator de segurança ao atrito
    k0: coeficiente de empuxo em repouso
    base_max: base máxima permitida (m) [opcional]
    gamma_agua: peso específico da água (kN/m³)
    sobrecarga_mon: sobrecarga a montante (kN/m²)
    inclinacao: direção da inclinação ("montante" ou "jusante")
    
    Retorna:
    dict com todos os resultados de dimensionamento e verificação
    """
    # Realizar dimensionamento
    dados_dimensionamento = dimensionar_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, k0, gamma_agua, sobrecarga_mon, inclinacao)
    
    # Realizar verificações
    dados_verificacao = verificar_estabilidade_muro_gravidade(dados_dimensionamento, h, crista, b_mon, gamma_concreto, gamma_solo_sat, gamma_solo_sub, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, k0, base_max, gamma_agua, sobrecarga_mon, inclinacao)
    
    # Combinar todos os resultados
    resultado_completo = {
        # Dados de dimensionamento
        'volume_concreto': dados_dimensionamento['volume_concreto'],
        'peso_muro': dados_dimensionamento['peso_muro'],
        'peso_solo': dados_dimensionamento['peso_solo'],
        'volume_corte': dados_dimensionamento['volume_corte'],
        'volume_aterro': dados_dimensionamento['volume_aterro'],
        'volume_descarga': dados_dimensionamento['volume_descarga'],
        
        # Dados de verificação
        'fs_deslizamento': dados_verificacao['fs_deslizamento'],
        'fs_deslizamento_ok': dados_verificacao['fs_deslizamento_ok'],
        'fs_tombamento': dados_verificacao['fs_tombamento'],
        'fs_tombamento_ok': dados_verificacao['fs_tombamento_ok'],
        'tensao_max': dados_verificacao['tensao_max'],
        'tensao_min': dados_verificacao['tensao_min'],
        'tensao_ok': dados_verificacao['tensao_ok'],
        'base_teorica': dados_verificacao['base_teorica'],
        'base_atual_ok': dados_verificacao['base_atual_ok'],
        'base_max_ok': dados_verificacao['base_max_ok'],
        'base_ok': dados_verificacao['base_ok'],
    }
    
    return resultado_completo

def mostrar_avisos_iniciais():
    # Criar uma janela popup
    janela_avisos = tk.Toplevel()
    janela_avisos.title("Avisos Importantes")
    janela_avisos.geometry("500x400")
    janela_avisos.resizable(False, False)
    janela_avisos.transient(root)  # Define como modal
    janela_avisos.grab_set()       # Impede interação com a janela principal
    
    # Cabeçalho
    tk.Label(janela_avisos, text="Avisos Importantes", font=("Arial", 14, "bold")).pack(pady=10)
    
    # Área de texto com barra de rolagem
    frame_texto = tk.Frame(janela_avisos)
    frame_texto.pack(fill="both", expand=True, padx=20, pady=10)
    
    scrollbar = tk.Scrollbar(frame_texto)
    scrollbar.pack(side="right", fill="y")
    
    texto_avisos = tk.Text(frame_texto, wrap="word", yscrollcommand=scrollbar.set)
    texto_avisos.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=texto_avisos.yview)
    
    # Conteúdo dos avisos
    avisos = """
    Bem-vindo ao Programa de Dimensionamento de Muros!
    
    AVISOS IMPORTANTES:
    
    1. Este programa é uma ferramenta de auxílio ao pré-dimensionamento e não substitui o julgamento profissional de um engenheiro qualificado.
    
    2. Os cálculos são baseados em métodos simplificados e podem não considerar todas as variáveis presentes em um projeto real.
    
    3. A responsabilidade pela verificação dos resultados e sua aplicação em projetos reais é inteiramente do usuário.
    
    4. Recomenda-se a validação dos resultados através de métodos alternativos e/ou consultoria especializada.
    
    5. O programa não considera análises sísmicas, condições especiais do solo ou outros fatores específicos que podem ser críticos em determinadas situações.

    6. Os valores de custos foram obtidos através da SINAPI e podem não refletir a realidade do mercado.

    7. Não foi verificado Estado Limite de Serviço.

    8. Adotada armadura superficial de 12,5c15 para muros de gravidade.

    9. A sobrecarga atuante a montante também é considerada como carga estabilizadora.
    
    Ao continuar, você confirma que leu e compreendeu estes avisos.
    """
    
    texto_avisos.insert("1.0", avisos)
    texto_avisos.config(state="disabled")  # Torna o texto não editável
    
    # Botão de confirmação
    def fechar_aviso():
        janela_avisos.destroy()
    
    tk.Button(janela_avisos, text="Concordo e Desejo Continuar", command=fechar_aviso, 
              font=("Arial", 10, "bold")).pack(pady=15)
    
    # Esperar até que a janela seja fechada
    root.wait_window(janela_avisos)

label_info_custos = None

def editar_custos_popup():
    # Função auxiliar para carregar valores atuais
    def obter_valor_atual(campo_global, valor_default):
        try:
            return globals()[campo_global].get() if globals()[campo_global].get() else valor_default
        except:
            return valor_default
    
    # Criar uma nova janela
    janela_custos = tk.Toplevel()
    janela_custos.title("Edição de Custos")
    janela_custos.resizable(False, False)
    janela_custos.transient()  # Define como modal
    janela_custos.grab_set()       # Impede interação com a janela principal

    # Cabeçalho
    tk.Label(janela_custos, text="Custos de Materiais e Mão de Obra", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=4, pady=10)
    
    # Cabeçalhos das colunas
    tk.Label(janela_custos, text="Item", font=("Arial", 10, "bold")).grid(row=1, column=1, padx=10)
    tk.Label(janela_custos, text="Material (R$)", font=("Arial", 10, "bold")).grid(row=1, column=2, padx=10)
    tk.Label(janela_custos, text="Mão de Obra (R$)", font=("Arial", 10, "bold")).grid(row=1, column=3, padx=10)
    tk.Label(janela_custos, text="Tempo (×/h)", font=("Arial", 10, "bold")).grid(row=1, column=4, padx=10)
    
    tk.Label(janela_custos, text="Concreto Estrutural (m³):").grid(row=2, column=1, sticky="w", padx=10, pady=5)
    entry_concreto_25_mat = tk.Entry(janela_custos)
    entry_concreto_25_mat.insert(0, obter_valor_atual("entry_concreto_25_mat", "587.58"))  # SINAPI 99439 - 03/2025
    entry_concreto_25_mat.grid(row=2, column=2, padx=10, pady=5)

    entry_concreto_25_mdo = tk.Entry(janela_custos)
    entry_concreto_25_mdo.insert(0, obter_valor_atual("entry_concreto_25_mdo", "38.17"))  # SINAPI 99439 - 03/2025
    entry_concreto_25_mdo.grid(row=2, column=3, padx=10, pady=5)

    entry_concreto_25_tempo = tk.Entry(janela_custos)
    entry_concreto_25_tempo.insert(0, obter_valor_atual("entry_concreto_25_tempo", "1.302'"))  # SINAPI 99439 - 03/2025
    entry_concreto_25_tempo.grid(row=2, column=4, padx=10, pady=5)
    
    tk.Label(janela_custos, text="Concreto Massa (m³):").grid(row=3, column=1, sticky="w", padx=10, pady=5)
    entry_concreto_6_mat = tk.Entry(janela_custos)
    entry_concreto_6_mat.insert(0, "119.01")  # SINAPI 94974 - 03/2025
    entry_concreto_6_mat.grid(row=3, column=2, padx=10, pady=5)
    
    entry_concreto_6_mdo = tk.Entry(janela_custos)
    entry_concreto_6_mdo.insert(0, "187.12")  # SINAPI 94974 - 03/2025
    entry_concreto_6_mdo.grid(row=3, column=3, padx=10, pady=5)

    entry_concreto_6_tempo = tk.Entry(janela_custos)
    entry_concreto_6_tempo.insert(0, "6.2858")  # SINAPI 94974 - 03/2025
    entry_concreto_6_tempo.grid(row=3, column=4, padx=10, pady=5)
    
    tk.Label(janela_custos, text="Aço CA50 (kg):").grid(row=4, column=1, sticky="w", padx=10, pady=5)
    entry_aco_ca50_mat = tk.Entry(janela_custos)
    entry_aco_ca50_mat.insert(0, "8.31")  # SINAPI 100345 - 03/2025
    entry_aco_ca50_mat.grid(row=4, column=2, padx=10, pady=5)
    
    entry_aco_ca50_mdo = tk.Entry(janela_custos)
    entry_aco_ca50_mdo.insert(0, "1.5")  # SINAPI 100345 - 03/2025
    entry_aco_ca50_mdo.grid(row=4, column=3, padx=10, pady=5)

    entry_aco_ca50_tempo = tk.Entry(janela_custos)
    entry_aco_ca50_tempo.insert(0, "0.0445")  # SINAPI 100345 - 03/2025
    entry_aco_ca50_tempo.grid(row=4, column=4, padx=10, pady=5)

    tk.Label(janela_custos, text="Forma (m²):").grid(row=5, column=1, sticky="w", padx=10, pady=5)
    entry_forma_mat = tk.Entry(janela_custos)
    entry_forma_mat.insert(0, "19.1")  # SINAPI 100341 - 03/2025
    entry_forma_mat.grid(row=5, column=2, padx=10, pady=5)
    
    entry_forma_mdo = tk.Entry(janela_custos)
    entry_forma_mdo.insert(0, "24.58")  # SINAPI 100341 - 03/2025
    entry_forma_mdo.grid(row=5, column=3, padx=10, pady=5)

    entry_forma_tempo = tk.Entry(janela_custos)
    entry_forma_tempo.insert(0, "0.7326")  # SINAPI 100341 - 03/2025
    entry_forma_tempo.grid(row=5, column=4, padx=10, pady=5)

    tk.Label(janela_custos, text="Aterro (m³):").grid(row=6, column=1, sticky="w", padx=10, pady=5)
    entry_aterro_mat = tk.Entry(janela_custos)
    entry_aterro_mat.insert(0, "0")  # Valor default
    entry_aterro_mat.grid(row=6, column=2, padx=10, pady=5)

    entry_aterro_mdo = tk.Entry(janela_custos)
    entry_aterro_mdo.insert(0, "0")  # Valor default
    entry_aterro_mdo.grid(row=6, column=3, padx=10, pady=5)

    entry_aterro_tempo = tk.Entry(janela_custos)
    entry_aterro_tempo.insert(0, "0")  # Valor default
    entry_aterro_tempo.grid(row=6, column=4, padx=10, pady=5)

    tk.Label(janela_custos, text="Corte (m³):").grid(row=7, column=1, sticky="w", padx=10, pady=5)
    entry_corte_mat = tk.Entry(janela_custos)
    entry_corte_mat.insert(0, "0")  # Valor default
    entry_corte_mat.grid(row=7, column=2, padx=10, pady=5)

    entry_corte_mdo = tk.Entry(janela_custos)
    entry_corte_mdo.insert(0, "0")  # Valor default
    entry_corte_mdo.grid(row=7, column=3, padx=10, pady=5)

    entry_corte_tempo = tk.Entry(janela_custos)
    entry_corte_tempo.insert(0, "0")  # Valor default
    entry_corte_tempo.grid(row=7, column=4, padx=10, pady=5)
    
    tk.Label(janela_custos, text="Carga (m³):").grid(row=8, column=1, sticky="w", padx=10, pady=5)
    entry_carga_mat = tk.Entry(janela_custos)
    entry_carga_mat.insert(0, "0")  # Valor default
    entry_carga_mat.grid(row=8, column=2, padx=10, pady=5)

    entry_carga_mdo = tk.Entry(janela_custos)
    entry_carga_mdo.insert(0, "0")  # Valor default
    entry_carga_mdo.grid(row=8, column=3, padx=10, pady=5)

    entry_carga_tempo = tk.Entry(janela_custos)
    entry_carga_tempo.insert(0, "0")  # Valor default
    entry_carga_tempo.grid(row=8, column=4, padx=10, pady=5)
    
    tk.Label(janela_custos, text="Descarga (m³):").grid(row=9, column=1, sticky="w", padx=10, pady=5)
    entry_descarga_mat = tk.Entry(janela_custos)
    entry_descarga_mat.insert(0, "0")  # Valor default
    entry_descarga_mat.grid(row=9, column=2, padx=10, pady=5)

    entry_descarga_mdo = tk.Entry(janela_custos)
    entry_descarga_mdo.insert(0, "0")  # Valor default
    entry_descarga_mdo.grid(row=9, column=3, padx=10, pady=5)

    entry_descarga_tempo = tk.Entry(janela_custos)
    entry_descarga_tempo.insert(0, "0")  # Valor default
    entry_descarga_tempo.grid(row=9, column=4, padx=10, pady=5)

    # Conectar os campos da janela popup com as StringVars para capturar os valores editados
    entry_concreto_25_mat_popup = entry_concreto_25_mat
    entry_concreto_25_mdo_popup = entry_concreto_25_mdo
    entry_concreto_25_tempo_popup = entry_concreto_25_tempo
    entry_concreto_6_mat_popup = entry_concreto_6_mat
    entry_concreto_6_mdo_popup = entry_concreto_6_mdo
    entry_concreto_6_tempo_popup = entry_concreto_6_tempo
    entry_aco_ca50_mat_popup = entry_aco_ca50_mat
    entry_aco_ca50_mdo_popup = entry_aco_ca50_mdo
    entry_aco_ca50_tempo_popup = entry_aco_ca50_tempo
    entry_forma_mat_popup = entry_forma_mat
    entry_forma_mdo_popup = entry_forma_mdo
    entry_forma_tempo_popup = entry_forma_tempo
    entry_aterro_mat_popup = entry_aterro_mat
    entry_aterro_mdo_popup = entry_aterro_mdo
    entry_aterro_tempo_popup = entry_aterro_tempo
    entry_corte_mat_popup = entry_corte_mat
    entry_corte_mdo_popup = entry_corte_mdo
    entry_corte_tempo_popup = entry_corte_tempo
    entry_carga_mat_popup = entry_carga_mat
    entry_carga_mdo_popup = entry_carga_mdo
    entry_carga_tempo_popup = entry_carga_tempo
    entry_descarga_mat_popup = entry_descarga_mat
    entry_descarga_mdo_popup = entry_descarga_mdo
    entry_descarga_tempo_popup = entry_descarga_tempo
    

    # Função para aplicar as alterações
    def aplicar_custos():
        global entry_concreto_25_mat, entry_concreto_25_mdo, entry_concreto_25_tempo
        global entry_concreto_6_mat, entry_concreto_6_mdo, entry_concreto_6_tempo
        global entry_aco_ca50_mat, entry_aco_ca50_mdo, entry_aco_ca50_tempo
        global entry_forma_mat, entry_forma_mdo, entry_forma_tempo
        global entry_aterro_mat, entry_aterro_mdo, entry_aterro_tempo
        global entry_corte_mat, entry_corte_mdo, entry_corte_tempo
        global entry_carga_mat, entry_carga_mdo, entry_carga_tempo
        global entry_descarga_mat, entry_descarga_mdo, entry_descarga_tempo
        
        try:
            # Validar os valores - MATERIAIS (capturar dos campos da janela popup)
            custos_mat = [
                float(entry_concreto_25_mat_popup.get()),
                float(entry_concreto_6_mat_popup.get()),
                float(entry_aco_ca50_mat_popup.get()),
                float(entry_forma_mat_popup.get()),
                float(entry_aterro_mat_popup.get()),
                float(entry_corte_mat_popup.get()),
                float(entry_carga_mat_popup.get()),
                float(entry_descarga_mat_popup.get())
            ]
            
            # Validar os valores - MÃO DE OBRA (capturar dos campos da janela popup)
            custos_mdo = [
                float(entry_concreto_25_mdo_popup.get()),
                float(entry_concreto_6_mdo_popup.get()),
                float(entry_aco_ca50_mdo_popup.get()),
                float(entry_aterro_mdo_popup.get()),
                float(entry_corte_mdo_popup.get()),
                float(entry_carga_mdo_popup.get()),
                float(entry_descarga_mdo_popup.get()),
                float(entry_forma_mdo_popup.get())
            ]

            # Validar os valores - TEMPO (capturar dos campos da janela popup)
            custos_tempo = [
                float(entry_concreto_25_tempo_popup.get()),
                float(entry_concreto_6_tempo_popup.get()),
                float(entry_aco_ca50_tempo_popup.get()),
                float(entry_aterro_tempo_popup.get()),
                float(entry_corte_tempo_popup.get()),
                float(entry_carga_tempo_popup.get()),
                float(entry_descarga_tempo_popup.get()),
                float(entry_forma_tempo_popup.get())
            ]
            
            valores = [custos_mat, custos_mdo, custos_tempo]
            
            # Verificar se os valores são positivos
            if any(custo < 0 for custo in custos_mat + custos_mdo):
                messagebox.showerror("Erro", "Os custos devem ser valores positivos.")
                return
                
            # Atualizar os valores nos campos da interface principal - MATERIAIS
            entry_concreto_25_mat.delete(0, tk.END)
            entry_concreto_25_mat.insert(0, str(custos_mat[0]))
            entry_concreto_25_mdo.delete(0, tk.END)
            entry_concreto_25_mdo.insert(0, str(custos_mdo[0]))
            entry_concreto_25_tempo.delete(0, tk.END)
            entry_concreto_25_tempo.insert(0, str(custos_tempo[0]))
            
            entry_concreto_6_mat.delete(0, tk.END)
            entry_concreto_6_mat.insert(0, str(custos_mat[1]))
            entry_concreto_6_mdo.delete(0, tk.END)
            entry_concreto_6_mdo.insert(0, str(custos_mdo[1]))
            entry_concreto_6_tempo.delete(0, tk.END)
            entry_concreto_6_tempo.insert(0, str(custos_tempo[1]))
            
            entry_aco_ca50_mat.delete(0, tk.END)
            entry_aco_ca50_mat.insert(0, str(custos_mat[2]))
            entry_aco_ca50_mdo.delete(0, tk.END)
            entry_aco_ca50_mdo.insert(0, str(custos_mdo[2]))
            entry_aco_ca50_tempo.delete(0, tk.END)
            entry_aco_ca50_tempo.insert(0, str(custos_tempo[2]))
            
            entry_forma_mat.delete(0, tk.END)
            entry_forma_mat.insert(0, str(custos_mat[3]))
            entry_forma_mdo.delete(0, tk.END)
            entry_forma_mdo.insert(0, str(custos_mdo[3]))
            entry_forma_tempo.delete(0, tk.END)
            entry_forma_tempo.insert(0, str(custos_tempo[3]))
            
            # Corrigir a ordem dos campos de aterro (mat e mdo estavam trocados)
            entry_aterro_mat.delete(0, tk.END)
            entry_aterro_mat.insert(0, str(custos_mat[4]))
            entry_aterro_mdo.delete(0, tk.END)
            entry_aterro_mdo.insert(0, str(custos_mdo[4]))
            entry_aterro_tempo.delete(0, tk.END)
            entry_aterro_tempo.insert(0, str(custos_tempo[4]))
            
            # Corrigir a ordem dos campos de corte (mat e mdo estavam trocados)
            entry_corte_mat.delete(0, tk.END)
            entry_corte_mat.insert(0, str(custos_mat[5]))
            entry_corte_mdo.delete(0, tk.END)
            entry_corte_mdo.insert(0, str(custos_mdo[5]))
            entry_corte_tempo.delete(0, tk.END)
            entry_corte_tempo.insert(0, str(custos_tempo[5]))

            # Corrigir a ordem dos campos de carga (mat e mdo estavam trocados)
            entry_carga_mat.delete(0, tk.END)
            entry_carga_mat.insert(0, str(custos_mat[6]))
            entry_carga_mdo.delete(0, tk.END)
            entry_carga_mdo.insert(0, str(custos_mdo[6]))
            entry_carga_tempo.delete(0, tk.END)
            entry_carga_tempo.insert(0, str(custos_tempo[6]))

            # Corrigir a ordem dos campos de descarga (mat e mdo estavam trocados)
            entry_descarga_mat.delete(0, tk.END)
            entry_descarga_mat.insert(0, str(custos_mat[7]))
            entry_descarga_mdo.delete(0, tk.END)
            entry_descarga_mdo.insert(0, str(custos_mdo[7]))
            entry_descarga_tempo.delete(0, tk.END)
            entry_descarga_tempo.insert(0, str(custos_tempo[7]))
            
            # Atualizar o rótulo do botão de custos
            atualizar_info_custos()
            
            # Fechar a janela
            janela_custos.destroy()
            
            # Se já existem cálculos, atualizar os resultados
            try:
                calcular()
            except:
                pass
                
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira apenas valores numéricos válidos.")
    
    # Botões
    frame_botoes = tk.Frame(janela_custos)
    frame_botoes.grid(row=12, column=0, columnspan=4, pady=20)
    
    btn_aplicar = tk.Button(frame_botoes, text="Aplicar", command=aplicar_custos)
    btn_aplicar.pack(side="left", padx=10)
    
    btn_cancelar = tk.Button(frame_botoes, text="Cancelar", command=janela_custos.destroy)
    btn_cancelar.pack(side="left", padx=10)
    
    # Informações adicionais
    info_texto = (
        "Os custos definidos aqui serão utilizados para calcular\n"
        "o orçamento das diferentes soluções de muro.\n"
        "Certifique-se de utilizar valores atualizados de mercado."
    )
    
    info_label = tk.Label(janela_custos, text=info_texto, justify="left", wraplength=400)
    info_label.grid(row=13, column=0, columnspan=4, padx=10, pady=10)
    
    # Centralizar a janela
    janela_custos.update_idletasks()
    width = janela_custos.winfo_width()
    height = janela_custos.winfo_height()
    x = (janela_custos.winfo_screenwidth() // 2) - (width // 2)
    y = (janela_custos.winfo_screenheight() // 2) - (height // 2)
    janela_custos.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # Iniciar loop da janela
    janela_custos.mainloop()

def atualizar_info_custos():
    """
    Atualiza o rótulo do botão de custos com informações resumidas
    """
    try:
        conc_25 = float(entry_concreto_25_mat.get())+float(entry_concreto_25_mdo.get())
        conc_6 = float(entry_concreto_6_mat.get())+float(entry_concreto_6_mdo.get())
        aco = float(entry_aco_ca50_mat.get())+float(entry_aco_ca50_mdo.get())
        forma = float(entry_forma_mat.get())+float(entry_forma_mdo.get())
        
        # Formato simplificado para interface compacta
        texto = f"Estrut: R${conc_25:.0f} | Aço: R${aco:.0f} | Forma: R${forma:.0f}"
        label_info_custos.config(text=texto)
    except:
        label_info_custos.config(text="Clique para editar") 

# Criar a janela principal
root = tk.Tk()
# Mostrar avisos antes de continuar
mostrar_avisos_iniciais()

root.title("Pré-Dimensionamento de Muro de Arrimo")


# Novos campos de entrada para os parâmetros de estabilidade
tk.Label(root, text="Param. Muro Flexão:", font=("Arial", 12)).grid(row=0, column=2, columnspan=2)

tk.Label(root, text="Largura da base do muro a jusante (m):").grid(row=1, column=2)
entry_b_jus = tk.Entry(root)
entry_b_jus.insert(0, "1")  # Valor default
entry_b_jus.grid(row=1, column=3)

tk.Label(root, text="Largura da base do muro a montante (m):").grid(row=2, column=2)
entry_b_mon = tk.Entry(root)
entry_b_mon.insert(0, "1.6")  # Valor default
entry_b_mon.grid(row=2, column=3)

# Ajustar a posição dos campos seguintes
# tk.Label(root, text="fck do concreto estrutural (MPa):").grid(row=3, column=2)
entry_fck = tk.Entry(root)
entry_fck.insert(0, "25")  # Valor default
entry_fck.grid_remove() # Ocultar o campo
# entry_fck.grid(row=3, column=3)

# ------------------------------------------ NÃO ESQUECER DE COLOCAR A FCK NO RELATÓRIO

# Novos campos de entrada para os parâmetros de estabilidade
tk.Label(root, text="Param. Muro Gravidade:", font=("Arial", 12)).grid(row=5, column=2, columnspan=2)

tk.Label(root, text="Largura da base do muro a montante (m):").grid(row=6, column=2)
entry_b_gravidade = tk.Entry(root)
entry_b_gravidade.insert(0, "2.5")  # Valor default
entry_b_gravidade.grid(row=6, column=3)

tk.Label(root, text="Largura crista (m):").grid(row=7, column=2)
entry_crista = tk.Entry(root)
entry_crista.insert(0, "0.5")  # Valor default
entry_crista.grid(row=7, column=3)

# tk.Label(root, text="fck do concreto massa (MPa):").grid(row=8, column=2)
entry_fck_massa = tk.Entry(root)
entry_fck_massa.insert(0, "6")  # Valor default
entry_fck_massa.grid_remove() # Ocultar o campo
# entry_fck_massa.grid(row=8, column=3)

# Criar os campos de entrada com valores default
tk.Label(root, text="Altura do muro (m):").grid(row=1, column=0)
entry_h = tk.Entry(root)
entry_h.insert(0, "5.0")  # Valor default
entry_h.grid(row=1, column=1)

# tk.Label(root, text="fyk do aço (MPa):").grid(row=4, column=0)
entry_fyk = tk.Entry(root)
entry_fyk.insert(0, "500")  # Valor default
entry_fyk.grid_remove() # Ocultar o campo
# entry_fyk.grid(row=4, column=1)

# Criar os campos de entrada com valores default
tk.Label(root, text="Altura do muro (m):").grid(row=1, column=0)
entry_h = tk.Entry(root)
entry_h.insert(0, "5.0")  # Valor default
entry_h.grid(row=1, column=1)

tk.Label(root, text="Peso específico do solo saturado (kN/m³):").grid(row=2, column=0)
entry_gamma_solo_sat = tk.Entry(root)
entry_gamma_solo_sat.insert(0, "18")  # Valor default
entry_gamma_solo_sat.grid(row=2, column=1)

tk.Label(root, text="Peso específico do solo submerso (kN/m³):").grid(row=3, column=0)
entry_gamma_solo_sub = tk.Entry(root)
entry_gamma_solo_sub.insert(0, "10")  # Valor default
entry_gamma_solo_sub.grid(row=3, column=1)

tk.Label(root, text="Ângulo de atrito do aterro (graus):").grid(row=4, column=0)
entry_phi_aterro = tk.Entry(root)
entry_phi_aterro.insert(0, "30")  # Valor default
entry_phi_aterro.grid(row=4, column=1)

# Criar um frame para o botão e informações de custo
frame_custos = tk.Frame(root)
frame_custos.grid(row=14, column=3, columnspan=2, pady=5, padx=10, sticky="w")

# Botão para editar custos
btn_editar_custos = tk.Button(frame_custos, text="Editar Custos", command=editar_custos_popup)
btn_editar_custos.pack(side=tk.LEFT, padx=5)

# Label para mostrar informações resumidas sobre custos (mais compacto)
label_info_custos = tk.Label(frame_custos, text="Clique para editar", font=("Arial", 9), wraplength=150)
label_info_custos.pack(side=tk.LEFT, padx=5)

# Atualizar as informações de custos ao iniciar
atualizar_info_custos()

# Novos campos de entrada para os parâmetros de estabilidade

tk.Label(root, text="Peso Específico do Concreto (kN/m³):").grid(row=5, column=0)
entry_gamma_concreto = tk.Entry(root)
entry_gamma_concreto.insert(0, "24")  # Valor default
entry_gamma_concreto.grid(row=5, column=1)

tk.Label(root, text="Coeficiente de Empuxo em Repouso (K0):").grid(row=3, column=6)
entry_k0 = tk.Entry(root)
entry_k0.insert(0, "0.67")
entry_k0.grid(row=3, column=7)

tk.Label(root, text="Coeficiente de Empuxo Ativo (Ka):").grid(row=4, column=6)
entry_ka = tk.Entry(root)
entry_ka.insert(0, "0.36")
entry_ka.grid(row=4, column=7)

tk.Label(root, text="Pressão Admissível Fundação (kN/m²):").grid(row=5, column=6)
entry_pressao_adm = tk.Entry(root)
entry_pressao_adm.insert(0, "200")  # Valor default
entry_pressao_adm.grid(row=5, column=7)

tk.Label(root, text="Base Máxima Permitida (m):").grid(row=6, column=0)
entry_base_max = tk.Entry(root)
entry_base_max.insert(0, "3.0")  # Valor default
entry_base_max.grid(row=6, column=1)

tk.Label(root, text="Nível de Água (m):").grid(row=7, column=0)
entry_nivel_agua = tk.Entry(root)
entry_nivel_agua.insert(0, "2.0")  # Valor default
entry_nivel_agua.grid(row=7, column=1)

tk.Label(root, text="Sobrecarga a montante (kN/m²):").grid(row=8, column=0)
entry_sobrecarga_mon = tk.Entry(root)
entry_sobrecarga_mon.insert(0, "0")  # Valor default
entry_sobrecarga_mon.grid(row=8, column=1)

entry_gamma_agua = tk.Entry(root)
entry_gamma_agua.insert(0, "10")  # Valor default
entry_gamma_agua.grid_remove()  # Ocultar o campo

tk.Label(root, text="Coesão do Solo (kN/m²):").grid(row=6, column=6)
entry_coesao = tk.Entry(root)
entry_coesao.insert(0, "10")  # Valor default
entry_coesao.grid(row=6, column=7)

tk.Label(root, text="Ângulo de Atrito (graus):").grid(row=7, column=6)
entry_phi_estabilidade = tk.Entry(root)
entry_phi_estabilidade.insert(0, "30")  # Valor default
entry_phi_estabilidade.grid(row=7, column=7)

# k.Label(root, text="Fator Seg. Coesão:").grid(row=7, column=6)
entry_fs_coesao = tk.Entry(root)
entry_fs_coesao.insert(0, "4")  # Valor default
entry_fs_coesao.grid_remove()  # Ocultar o campo
# entry_fs_coesao.grid(row=7, column=7)

# tk.Label(root, text="Fator Seg. Atrito:").grid(row=8, column=6)
entry_fs_atrito = tk.Entry(root)
entry_fs_atrito.insert(0, "2")  # Valor default
entry_fs_atrito.grid_remove()  # Ocultar o campo
# entry_fs_atrito.grid(row=8, column=7)

# Criar um frame para as opções de inclinação do muro de gravidade
frame_inclinacao = tk.Frame(root)
frame_inclinacao.grid(row=8, column=2, columnspan=2, padx=10, pady=5)

tk.Label(frame_inclinacao, text="Inclinação do Muro de Gravidade:").pack(side=tk.LEFT)
var_inclinacao = tk.StringVar(root)
var_inclinacao.set("montante")  # Valor padrão
option_inclinacao = tk.OptionMenu(frame_inclinacao, var_inclinacao, "montante", "jusante")
option_inclinacao.pack(side=tk.LEFT, padx=5)

# ---------------------------------------------------------------- #
# ------------------- Muro de Flexão ----------------------------- #
# ---------------------------------------------------------------- #

# Botões principais ajustados para a nova interface
btn_calcular = tk.Button(root, text="Calcular", command=calcular, bg="lightblue")
btn_calcular.grid(row=14, column=0, pady=5)

btn_plotar_flexao = tk.Button(root, text="Exibir Muro de Flexão", command=botao_plotar_muro_arrimo)
btn_plotar_flexao.grid(row=14, column=1, pady=5)

btn_gravidade = tk.Button(root, text="Exibir Muro de Gravidade", 
                        command=lambda: exibir_muro_gravidade_popup())
btn_gravidade.grid(row=14, column=2, pady=5)

entry_concreto_25_mat = tk.Entry(root)
entry_concreto_25_mat.insert(0, "587.58")  # SINAPI 99439 - 03/2025
entry_concreto_25_mat.grid(row=2, column=2, padx=10, pady=5)
entry_concreto_25_mat.grid_remove()

entry_concreto_25_mdo = tk.Entry(root)
entry_concreto_25_mdo.insert(0, "38.17")  # SINAPI 99439 - 03/2025
entry_concreto_25_mdo.grid(row=2, column=3, padx=10, pady=5)
entry_concreto_25_mdo.grid_remove()

entry_concreto_25_tempo = tk.Entry(root)
entry_concreto_25_tempo.insert(0, "1.302")  # SINAPI 99439 - 03/2025
entry_concreto_25_tempo.grid(row=2, column=4, padx=10, pady=5)
entry_concreto_25_tempo.grid_remove()

entry_concreto_6_mat = tk.Entry(root)
entry_concreto_6_mat.insert(0, "119.01")  # SINAPI 94974 - 03/2025
entry_concreto_6_mat.grid(row=3, column=2, padx=10, pady=5)
entry_concreto_6_mat.grid_remove()

entry_concreto_6_mdo = tk.Entry(root)
entry_concreto_6_mdo.insert(0, "187.12")  # SINAPI 94974 - 03/2025
entry_concreto_6_mdo.grid(row=3, column=3, padx=10, pady=5)
entry_concreto_6_mdo.grid_remove()

entry_concreto_6_tempo = tk.Entry(root)
entry_concreto_6_tempo.insert(0, "6.2858")  # SINAPI 94974 - 03/2025
entry_concreto_6_tempo.grid(row=3, column=4, padx=10, pady=5)
entry_concreto_6_tempo.grid_remove()

entry_aco_ca50_mat = tk.Entry(root)
entry_aco_ca50_mat.insert(0, "8.31")  # SINAPI 100345 - 03/2025
entry_aco_ca50_mat.grid(row=4, column=2, padx=10, pady=5)
entry_aco_ca50_mat.grid_remove()

entry_aco_ca50_mdo = tk.Entry(root)
entry_aco_ca50_mdo.insert(0, "1.5")  # SINAPI 100345 - 03/2025
entry_aco_ca50_mdo.grid(row=4, column=3, padx=10, pady=5)
entry_aco_ca50_mdo.grid_remove()

entry_aco_ca50_tempo = tk.Entry(root)
entry_aco_ca50_tempo.insert(0, "0.0445")  # SINAPI 100345 - 03/2025
entry_aco_ca50_tempo.grid(row=4, column=4, padx=10, pady=5)
entry_aco_ca50_tempo.grid_remove()

entry_forma_mat = tk.Entry(root)
entry_forma_mat.insert(0, "19.1")  # SINAPI 100341 - 03/2025
entry_forma_mat.grid(row=5, column=2, padx=10, pady=5)
entry_forma_mat.grid_remove()

entry_forma_mdo = tk.Entry(root)
entry_forma_mdo.insert(0, "24.58")  # SINAPI 100341 - 03/2025
entry_forma_mdo.grid(row=5, column=3, padx=10, pady=5)
entry_forma_mdo.grid_remove()

entry_forma_tempo = tk.Entry(root)
entry_forma_tempo.insert(0, "0.7326")  # SINAPI 100341 - 03/2025
entry_forma_tempo.grid(row=5, column=4, padx=10, pady=5)
entry_forma_tempo.grid_remove()

entry_aterro_mat = tk.Entry(root)
entry_aterro_mat.insert(0, "0")  # Valor default
entry_aterro_mat.grid(row=6, column=2, padx=10, pady=5)
entry_aterro_mat.grid_remove()

entry_aterro_mdo = tk.Entry(root)
entry_aterro_mdo.insert(0, "0")  # Valor default
entry_aterro_mdo.grid(row=6, column=3, padx=10, pady=5)
entry_aterro_mdo.grid_remove()

entry_aterro_tempo = tk.Entry(root)
entry_aterro_tempo.insert(0, "0")  # Valor default
entry_aterro_tempo.grid(row=6, column=4, padx=10, pady=5)
entry_aterro_tempo.grid_remove()

entry_corte_mat = tk.Entry(root)
entry_corte_mat.insert(0, "0")  # Valor default
entry_corte_mat.grid(row=7, column=2, padx=10, pady=5)
entry_corte_mat.grid_remove()

entry_corte_mdo = tk.Entry(root)
entry_corte_mdo.insert(0, "0")  # Valor default
entry_corte_mdo.grid(row=7, column=3, padx=10, pady=5)
entry_corte_mdo.grid_remove()

entry_corte_tempo = tk.Entry(root)
entry_corte_tempo.insert(0, "0")  # Valor default
entry_corte_tempo.grid(row=7, column=4, padx=10, pady=5)
entry_corte_tempo.grid_remove()

entry_carga_mat = tk.Entry(root)
entry_carga_mat.insert(0, "0")  # Valor default
entry_carga_mat.grid(row=8, column=2, padx=10, pady=5)
entry_carga_mat.grid_remove()

entry_carga_mdo = tk.Entry(root)
entry_carga_mdo.insert(0, "0")  # Valor default
entry_carga_mdo.grid(row=8, column=3, padx=10, pady=5)
entry_carga_mdo.grid_remove()

entry_carga_tempo = tk.Entry(root)
entry_carga_tempo.insert(0, "0")  # Valor default
entry_carga_tempo.grid(row=8, column=4, padx=10, pady=5)
entry_carga_tempo.grid_remove()

entry_descarga_mat = tk.Entry(root)
entry_descarga_mat.insert(0, "0")  # Valor default
entry_descarga_mat.grid(row=9, column=2, padx=10, pady=5)
entry_descarga_mat.grid_remove()

entry_descarga_mdo = tk.Entry(root)
entry_descarga_mdo.insert(0, "0")  # Valor default
entry_descarga_mdo.grid(row=9, column=3, padx=10, pady=5)
entry_descarga_mdo.grid_remove()

entry_descarga_tempo = tk.Entry(root)
entry_descarga_tempo.insert(0, "0")  # Valor default
entry_descarga_tempo.grid(row=9, column=4, padx=10, pady=5)
entry_descarga_tempo.grid_remove()  

entry_forma_mat.insert(0, "19.1")  # SINAPI 100341 - 03/2025
entry_forma_mat.grid(row=10, column=2, padx=10, pady=5)
entry_forma_mat.grid_remove()

entry_forma_mdo.insert(0, "24.58")  # SINAPI 100341 - 03/2025
entry_forma_mdo.grid(row=10, column=3, padx=10, pady=5)
entry_forma_mdo.grid_remove()

entry_forma_tempo.insert(0, "0.7326")  # SINAPI 100341 - 03/2025
entry_forma_tempo.grid(row=10, column=4, padx=10, pady=5)
entry_forma_tempo.grid_remove()


# ================================================================== #
# ---------------------- RESUMO DE CUSTOS ------------------------- #
# ================================================================== #

# Seção de resumo simplificado
# tk.Label(root, text="Resumo de Custos e Tempo:", font=("Arial", 14, "bold")).grid(row=9, column=0, columnspan=5, pady=(10,0))

# Cabeçalhos das colunas do resumo
tk.Label(root, text="Tipo de Muro:", font=("Arial", 10, "bold")).grid(row=9, column=0, sticky="w", padx=5, pady=(30,5))
tk.Label(root, text="Custo Total:", font=("Arial", 10, "bold")).grid(row=9, column=1, sticky="w", padx=5, pady=(30,5))
tk.Label(root, text="Tempo (h):", font=("Arial", 10, "bold")).grid(row=9, column=2, sticky="w", padx=5, pady=(30,5))
tk.Label(root, text="Estabilidade:", font=("Arial", 10, "bold")).grid(row=9, column=3, sticky="w", padx=5, pady=(30,5))

# Muro de Flexão - Resumo
tk.Label(root, text="Muro de Flexão:", font=("Arial", 12, "bold")).grid(row=10, column=0, sticky="w", padx=5)
label_custo_total_flexao = tk.Label(root, text="R$ 0.00", font=("Arial", 11))
label_custo_total_flexao.grid(row=10, column=1, sticky="w", padx=5)

label_tempo_total_flexao = tk.Label(root, text="0.0 h", font=("Arial", 11))
label_tempo_total_flexao.grid(row=10, column=2, sticky="w", padx=5)

label_estavel_flexao = tk.Label(root, text="Calcular", font=("Arial", 10))
label_estavel_flexao.grid(row=10, column=3, sticky="w", padx=5)

# Muro de Gravidade - Resumo  
tk.Label(root, text="Muro de Gravidade:", font=("Arial", 12, "bold")).grid(row=11, column=0, sticky="w", padx=5)
label_custo_total_gravidade = tk.Label(root, text="R$ 0.00", font=("Arial", 11))
label_custo_total_gravidade.grid(row=11, column=1, sticky="w", padx=5)

label_tempo_total_gravidade = tk.Label(root, text="0.0 h", font=("Arial", 11))
label_tempo_total_gravidade.grid(row=11, column=2, sticky="w", padx=5)

label_estavel_gravidade = tk.Label(root, text="Calcular", font=("Arial", 10))
label_estavel_gravidade.grid(row=11, column=3, sticky="w", padx=5)

# Botão para visualizar quantitativos detalhados
btn_ver_quantitativos = tk.Button(root, text="Ver Quantitativos Detalhados", 
                                  command=lambda: exibir_quantitativos_detalhados())
btn_ver_quantitativos.grid(row=12, column=0, columnspan=3, pady=10)

def exibir_quantitativos_detalhados():
    """
    Exibe uma janela separada com todos os quantitativos detalhados
    """
    # Criar janela de quantitativos
    janela_quant = tk.Toplevel()
    janela_quant.title("Quantitativos Detalhados")
    janela_quant.geometry("1200x700")
    janela_quant.resizable(True, True)
    
    # Cabeçalho
    tk.Label(janela_quant, text="Quantitativos Detalhados dos Muros", 
             font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=8, pady=15)
    
    # Seção Muro de Flexão
    tk.Label(janela_quant, text="MURO DE FLEXÃO", font=("Arial", 14, "bold"), 
             bg="lightblue").grid(row=1, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
    
    # Cabeçalhos Flexão
    tk.Label(janela_quant, text="Item", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=5)
    tk.Label(janela_quant, text="Quantidade", font=("Arial", 10, "bold")).grid(row=2, column=1, padx=5)
    tk.Label(janela_quant, text="Custo (R$)", font=("Arial", 10, "bold")).grid(row=2, column=2, padx=5)
    tk.Label(janela_quant, text="Tempo (h)", font=("Arial", 10, "bold")).grid(row=2, column=3, padx=5)
    
    # Dados Flexão
    row_start = 3
    
    # Calcular tempos individuais para exibição
    try:
        tempo_concreto_25 = float(label_concreto_25.cget("text")) * float(entry_concreto_25_tempo.get())
        tempo_concreto_6 = float(label_concreto_6.cget("text")) * float(entry_concreto_6_tempo.get())
        tempo_aco = float(label_aco_ca50.cget("text")) * float(entry_aco_ca50_tempo.get())
        tempo_aterro = float(label_aterro.cget("text")) * float(entry_aterro_tempo.get())
        tempo_corte = float(label_corte.cget("text")) * float(entry_corte_tempo.get())
        tempo_carga = float(label_carga.cget("text")) * float(entry_carga_tempo.get())
        tempo_descarga = float(label_descarga.cget("text")) * float(entry_descarga_tempo.get())
        tempo_forma = float(label_forma.cget("text")) * float(entry_forma_tempo.get())
    except:
        tempo_concreto_25 = tempo_concreto_6 = tempo_aco = tempo_aterro = 0
        tempo_corte = tempo_carga = tempo_descarga = tempo_forma = 0
    
    items_flexao = [
        ("Concreto Estrutural (m³)", label_concreto_25.cget("text"), label_total_concreto_25.cget("text"), f"{tempo_concreto_25:.1f}"),
        ("Concreto Massa (m³)", label_concreto_6.cget("text"), label_total_concreto_6.cget("text"), f"{tempo_concreto_6:.1f}"),
        ("Aço CA50 (kg)", label_aco_ca50.cget("text"), label_total_aco_ca50.cget("text"), f"{tempo_aco:.1f}"),
        ("Solo - Aterro (m³)", label_aterro.cget("text"), label_total_aterro.cget("text"), f"{tempo_aterro:.1f}"),
        ("Solo - Corte (m³)", label_corte.cget("text"), label_total_corte.cget("text"), f"{tempo_corte:.1f}"),
        ("Solo - Carga (m³)", label_carga.cget("text"), label_total_carga.cget("text"), f"{tempo_carga:.1f}"),
        ("Solo - Descarga (m³)", label_descarga.cget("text"), label_total_descarga.cget("text"), f"{tempo_descarga:.1f}"),
        ("Área de Fôrma (m²)", label_forma.cget("text"), label_total_forma.cget("text"), f"{tempo_forma:.1f}")
    ]
    
    for i, (item, quant, custo, tempo) in enumerate(items_flexao):
        tk.Label(janela_quant, text=item).grid(row=row_start + i, column=0, sticky="w", padx=5)
        tk.Label(janela_quant, text=quant).grid(row=row_start + i, column=1, padx=5)
        tk.Label(janela_quant, text=f"R$ {custo}").grid(row=row_start + i, column=2, padx=5)
        tk.Label(janela_quant, text=f"{tempo} h").grid(row=row_start + i, column=3, padx=5)
    
    # Total Flexão
    tk.Label(janela_quant, text="TOTAL FLEXÃO:", font=("Arial", 11, "bold")).grid(
        row=row_start + len(items_flexao), column=0, sticky="w", padx=5, pady=(10,0))
    tk.Label(janela_quant, text=f"R$ {label_total_total.cget('text')}", 
             font=("Arial", 11, "bold")).grid(
        row=row_start + len(items_flexao), column=2, padx=5, pady=(10,0))
    tk.Label(janela_quant, text=f"{label_tempo_total_flexao.cget('text')}", 
             font=("Arial", 11, "bold")).grid(
        row=row_start + len(items_flexao), column=3, padx=5, pady=(10,0))
    
    # Seção Muro de Gravidade
    tk.Label(janela_quant, text="MURO DE GRAVIDADE", font=("Arial", 14, "bold"), 
             bg="lightgreen").grid(row=1, column=4, columnspan=4, sticky="ew", padx=5, pady=5)
    
    # Cabeçalhos Gravidade
    tk.Label(janela_quant, text="Item", font=("Arial", 10, "bold")).grid(row=2, column=4, padx=5)
    tk.Label(janela_quant, text="Quantidade", font=("Arial", 10, "bold")).grid(row=2, column=5, padx=5)
    tk.Label(janela_quant, text="Custo (R$)", font=("Arial", 10, "bold")).grid(row=2, column=6, padx=5)
    tk.Label(janela_quant, text="Tempo (h)", font=("Arial", 10, "bold")).grid(row=2, column=7, padx=5)
    
    # Dados Gravidade
    # Calcular tempos individuais para gravidade
    try:
        tempo_concreto_25_grav = float(label_concreto_25_grav.cget("text")) * float(entry_concreto_25_tempo.get())
        tempo_concreto_6_grav = float(label_concreto_6_grav.cget("text")) * float(entry_concreto_6_tempo.get())
        tempo_aco_grav = float(label_aco_ca50_grav.cget("text")) * float(entry_aco_ca50_tempo.get())
        tempo_aterro_grav = float(label_aterro_grav.cget("text")) * float(entry_aterro_tempo.get())
        tempo_corte_grav = float(label_corte_grav.cget("text")) * float(entry_corte_tempo.get())
        tempo_carga_grav = float(label_carga_grav.cget("text")) * float(entry_carga_tempo.get())
        tempo_descarga_grav = float(label_descarga_grav.cget("text")) * float(entry_descarga_tempo.get())
        tempo_forma_grav = float(label_forma_grav.cget("text")) * float(entry_forma_tempo.get())
    except:
        tempo_concreto_25_grav = tempo_concreto_6_grav = tempo_aco_grav = tempo_aterro_grav = 0
        tempo_corte_grav = tempo_carga_grav = tempo_descarga_grav = tempo_forma_grav = 0
    
    items_gravidade = [
        ("Concreto Estrutural (m³)", label_concreto_25_grav.cget("text"), label_total_concreto_25_grav.cget("text"), f"{tempo_concreto_25_grav:.1f}"),
        ("Concreto Massa (m³)", label_concreto_6_grav.cget("text"), label_total_concreto_6_grav.cget("text"), f"{tempo_concreto_6_grav:.1f}"),
        ("Aço CA50 (kg)", label_aco_ca50_grav.cget("text"), label_total_aco_ca50_grav.cget("text"), f"{tempo_aco_grav:.1f}"),
        ("Solo - Aterro (m³)", label_aterro_grav.cget("text"), label_total_aterro_grav.cget("text"), f"{tempo_aterro_grav:.1f}"),
        ("Solo - Corte (m³)", label_corte_grav.cget("text"), label_total_corte_grav.cget("text"), f"{tempo_corte_grav:.1f}"),
        ("Solo - Carga (m³)", label_carga_grav.cget("text"), label_total_carga_grav.cget("text"), f"{tempo_carga_grav:.1f}"),
        ("Solo - Descarga (m³)", label_descarga_grav.cget("text"), label_total_descarga_grav.cget("text"), f"{tempo_descarga_grav:.1f}"),
        ("Área de Fôrma (m²)", label_forma_grav.cget("text"), label_total_forma_grav.cget("text"), f"{tempo_forma_grav:.1f}")
    ]
    
    for i, (item, quant, custo, tempo) in enumerate(items_gravidade):
        tk.Label(janela_quant, text=item).grid(row=row_start + i, column=4, sticky="w", padx=5)
        tk.Label(janela_quant, text=quant).grid(row=row_start + i, column=5, padx=5)
        tk.Label(janela_quant, text=f"R$ {custo}").grid(row=row_start + i, column=6, padx=5)
        tk.Label(janela_quant, text=f"{tempo} h").grid(row=row_start + i, column=7, padx=5)
    
    # Total Gravidade
    tk.Label(janela_quant, text="TOTAL GRAVIDADE:", font=("Arial", 11, "bold")).grid(
        row=row_start + len(items_gravidade), column=4, sticky="w", padx=5, pady=(10,0))
    tk.Label(janela_quant, text=f"R$ {label_total_total_grav.cget('text')}", 
             font=("Arial", 11, "bold")).grid(
        row=row_start + len(items_gravidade), column=6, padx=5, pady=(10,0))
    tk.Label(janela_quant, text=f"{label_tempo_total_gravidade.cget('text')}", 
             font=("Arial", 11, "bold")).grid(
        row=row_start + len(items_gravidade), column=7, padx=5, pady=(10,0))
    
    # Informações sobre estabilidade
    tk.Label(janela_quant, text="VERIFICAÇÃO DE ESTABILIDADE", font=("Arial", 12, "bold")).grid(
        row=row_start + len(items_flexao) + 3, column=0, columnspan=8, pady=15)
    
    tk.Label(janela_quant, text=f"Flexão: {label_estavel_flexao.cget('text')}", 
             font=("Arial", 10)).grid(row=row_start + len(items_flexao) + 4, column=0, columnspan=4, padx=5)
    tk.Label(janela_quant, text=f"Gravidade: {label_estavel_gravidade.cget('text')}", 
             font=("Arial", 10)).grid(row=row_start + len(items_flexao) + 4, column=4, columnspan=4, padx=5)
    
    # Botão para fechar
    btn_fechar = tk.Button(janela_quant, text="Fechar", command=janela_quant.destroy)
    btn_fechar.grid(row=row_start + len(items_flexao) + 6, column=0, columnspan=8, pady=20)

# ================================================================== #
# ------------- LABELS OCULTOS PARA CÁLCULOS INTERNOS ------------- #
# ================================================================== #

# Manter os labels originais ocultos para cálculos internos
label_concreto_25 = tk.Label(root, text="0.00")
label_concreto_25.grid_remove()
label_total_concreto_25 = tk.Label(root, text="0.00")
label_total_concreto_25.grid_remove()

label_concreto_6 = tk.Label(root, text="0.00")
label_concreto_6.grid_remove()
label_total_concreto_6 = tk.Label(root, text="0.00")
label_total_concreto_6.grid_remove()

label_aco_ca50 = tk.Label(root, text="0.00")
label_aco_ca50.grid_remove()
label_total_aco_ca50 = tk.Label(root, text="0.00")
label_total_aco_ca50.grid_remove()

label_aterro = tk.Label(root, text="0.00")
label_aterro.grid_remove()
label_total_aterro = tk.Label(root, text="0.00")
label_total_aterro.grid_remove()

label_corte = tk.Label(root, text="0.00")
label_corte.grid_remove()
label_total_corte = tk.Label(root, text="0.00")
label_total_corte.grid_remove()

label_carga = tk.Label(root, text="0.00")
label_carga.grid_remove()
label_total_carga = tk.Label(root, text="0.00")
label_total_carga.grid_remove()

label_descarga = tk.Label(root, text="0.00")
label_descarga.grid_remove()
label_total_descarga = tk.Label(root, text="0.00")
label_total_descarga.grid_remove()

label_forma = tk.Label(root, text="0.00")
label_forma.grid_remove()
label_total_forma = tk.Label(root, text="0.00")
label_total_forma.grid_remove()

label_tempo_total = tk.Label(root, text="0.00")
label_tempo_total.grid_remove()
label_total_total = tk.Label(root, text="0.00")
label_total_total.grid_remove()

# Labels ocultos do muro de gravidade
label_concreto_25_grav = tk.Label(root, text="0.00")
label_concreto_25_grav.grid_remove()
label_total_concreto_25_grav = tk.Label(root, text="0.00")
label_total_concreto_25_grav.grid_remove()

label_concreto_6_grav = tk.Label(root, text="0.00")
label_concreto_6_grav.grid_remove()
label_total_concreto_6_grav = tk.Label(root, text="0.00")
label_total_concreto_6_grav.grid_remove()

label_aco_ca50_grav = tk.Label(root, text="0.00")
label_aco_ca50_grav.grid_remove()
label_total_aco_ca50_grav = tk.Label(root, text="0.00")
label_total_aco_ca50_grav.grid_remove()

label_aterro_grav = tk.Label(root, text="0.00")
label_aterro_grav.grid_remove()
label_total_aterro_grav = tk.Label(root, text="0.00")
label_total_aterro_grav.grid_remove()

label_corte_grav = tk.Label(root, text="0.00")
label_corte_grav.grid_remove()
label_total_corte_grav = tk.Label(root, text="0.00")
label_total_corte_grav.grid_remove()

label_carga_grav = tk.Label(root, text="0.00")
label_carga_grav.grid_remove()
label_total_carga_grav = tk.Label(root, text="0.00")
label_total_carga_grav.grid_remove()

label_descarga_grav = tk.Label(root, text="0.00")
label_descarga_grav.grid_remove()
label_total_descarga_grav = tk.Label(root, text="0.00")
label_total_descarga_grav.grid_remove()

label_forma_grav = tk.Label(root, text="0.00")
label_forma_grav.grid_remove()
label_total_forma_grav = tk.Label(root, text="0.00")
label_total_forma_grav.grid_remove()

label_total_total_grav = tk.Label(root, text="0.00")
label_total_total_grav.grid_remove()


# Campos ocultos para armazenar os valores de custo
entry_custo_concreto_25 = tk.Entry(root)
entry_custo_concreto_25.insert(0, "300")  # Valor default
entry_custo_concreto_25.grid_remove()  # Ocultar o campo

entry_custo_concreto_6 = tk.Entry(root)
entry_custo_concreto_6.insert(0, "200")  # Valor default
entry_custo_concreto_6.grid_remove()  # Ocultar o campo

entry_custo_aco_ca50 = tk.Entry(root)
entry_custo_aco_ca50.insert(0, "5")  # Valor default
entry_custo_aco_ca50.grid_remove()  # Ocultar o campo

entry_custo_aterro = tk.Entry(root)
entry_custo_aterro.insert(0, "50")  # Valor default
entry_custo_aterro.grid_remove()  # Ocultar o campo

entry_custo_corte = tk.Entry(root)
entry_custo_corte.insert(0, "50")  # Valor default
entry_custo_corte.grid_remove()  # Ocultar o campo

entry_custo_carga = tk.Entry(root)
entry_custo_carga.insert(0, "50")  # Valor default
entry_custo_carga.grid_remove()  # Ocultar o campo

entry_custo_descarga = tk.Entry(root)
entry_custo_descarga.insert(0, "50")  # Valor default
entry_custo_descarga.grid_remove()  # Ocultar o campo

entry_custo_forma = tk.Entry(root)
entry_custo_forma.insert(0, "20")  # Valor default
entry_custo_forma.grid_remove()  # Ocultar o campo

# Iniciar a interface
root.mainloop()

# Atualizar as informações de custos ao iniciar
atualizar_info_custos()
