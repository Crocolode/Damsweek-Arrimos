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

def dimensionar_muro_arrimo_flexao(h, b, d, gamma_solo, phi, fck, fyk, ka, h_agua=0):
    print("=== Dimensionamento de Muro de Arrimo à Flexão ===")
    
    # Cálculo do empuxo passivo (Teoria de Rankine)
    ep = 0.5 * gamma_solo * h**2 * ka  # Empuxo passivo total
    
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
    
    return dia_barra, espacamento

def calcular_peso_terra_montante(h, b_mont, gamma_solo, beta=0):
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
    peso_terra = area_ret * gamma_solo + volume_corte * gamma_solo
    
    # Cálculo do centro de gravidade
    momento_ret = (b_mont/2) * area_ret * gamma_solo
    momento_corte = (b_mont / 2) * volume_corte * gamma_solo
    x_cg = (momento_ret + momento_corte) / peso_terra
    
    # Cálculo do volume de aterro
    volume_aterro = peso_terra / gamma_solo  # Volume de aterro considerando a área triangular
    
    return peso_terra, x_cg, volume_aterro, volume_corte  # Retornando também os volumes de aterro e corte

def plotar_muro_arrimo(b_jus, b_mon, h, d, as_final, gamma_solo, tensao_max, pressao_adm, resultados_estabilidade):
    plt.close('all')  # Fecha todas as figuras existentes
    
    # Criar figura com dois subplots lado a lado
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))
    
    # Plotar a seção do muro de arrimo no subplot da esquerda
    ax1.plot([0, 0, d, d, 0], [0, h, h, 0, 0], color='gray', linewidth=2)  # Muro
    ax1.fill_between([0, b_mon], 0, d, color='gainsboro', alpha=0.5)  # Área do muro
    ax1.plot([0, 0, -b_jus, b_mon, 0], [d, 0, 0, d, d], color='gainsboro', linewidth=2)  # Contorno da base
    ax1.fill_between([0, -b_jus], 0, d, color='gainsboro', alpha=0.5)  # Base do muro
    ax1.fill_between([d, b_mon], d, h, color='saddlebrown', alpha=0.5, label='Solo')  # Terra acima da base
    ax1.fill_between([b_mon, b_mon + 1], d, h, color='saddlebrown', alpha=0.5)  # Terra à direita do muro

    # Adicionar cotas
    ax1.text((b_jus + b_mon)/2, -0.2, f'Base: {b_jus + b_mon:.2f} m', ha='center', va='top', fontsize=10)
    ax1.text(-0.2, h/2, f'Altura: {h:.2f} m', ha='right', va='center', fontsize=10, rotation='vertical')
    ax1.text((b_jus + b_mon)/2, d, f'Altura útil: {d:.2f} m', ha='center', va='bottom', fontsize=10)
    ax1.text(b_mon + 0.5, h/2, f'Área de Aço: {as_final:.2f} cm²', ha='left', va='center', fontsize=10, rotation='vertical')

    # Configurar o subplot da esquerda
    ax1.set_xlim(-b_jus - 0.5, b_mon + 1)
    ax1.set_ylim(-0.5, h + 0.5)
    ax1.set_aspect('equal')
    ax1.set_title('Seção do Muro de Arrimo à Flexão')
    ax1.set_xlabel('Base (m)')
    ax1.set_ylabel('Altura (m)')
    ax1.grid(True)
    ax1.legend()

    # Adicionar informação da pressão admissível
    ax1.text(0, -0.8, f"Pressão Admissível: {pressao_adm:.2f} kN/m²", ha='left', va='top', fontsize=10)
    ax1.text(0, -1.6, f"Tensão Máxima: {tensao_max:.2f} kN/m²", ha='left', va='top', fontsize=10)
    
    # Adicionar informações sobre a base teórica necessária e a comparação com a base máxima
    b_total = b_jus + b_mon
    if 'base_teorica' in resultados_estabilidade:
        base_teorica = resultados_estabilidade['base_teorica']
        base_ok = resultados_estabilidade.get('base_ok', False)
        base_atual_ok = resultados_estabilidade.get('base_atual_ok', False)
        base_max_ok = resultados_estabilidade.get('base_max_ok', True)
        
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

    # Plotar os quantitativos dos materiais
    volume_concreto = (b_mon + b_jus + h) * d  # Volume em m³
    peso_terra, x_cg, volume_aterro, volume_corte = calcular_peso_terra_montante(h, b_mon, gamma_solo)
    solo_corte = volume_corte
    solo_aterro = volume_aterro
    solo_carga = volume_aterro - volume_concreto

    # Relatório no subplot da direita
    ax2.axis('off')  # Desativa os eixos
    ax2.set_title('Relatório de Estabilidade')

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
        f"7. Base Adequada: {'Sim' if base_ok else 'Não'}"
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

    plt.tight_layout()
    plt.show()

def plotar_muro_gravidade(h, d, crista, b_mon, gamma_concreto, gamma_solo, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, k0, gamma_agua, sobrecarga_mon, calculos_gravidade):
    """
    Plota o muro de gravidade com as dimensões especificadas e um relatório de verificação
    
    Parâmetros:
    h: altura do muro (m)
    d: espessura na base (m) - não usado neste caso
    crista: largura da crista (m)
    b_mon: largura total da base (m)
    gamma_concreto: peso específico do concreto (kN/m³)
    gamma_solo: peso específico do solo (kN/m³)
    phi: ângulo de atrito interno do solo (graus)
    c: coesão do solo (kN/m²)
    pressao_adm: pressão admissível do solo (kN/m²)
    nivel_agua: nível d'água (m)
    fs_coesao: fator de segurança à coesão
    fs_atrito: fator de segurança ao atrito
    k0: coeficiente de empuxo em repouso
    calculos_gravidade: dicionário com os resultados dos cálculos
    
    Retorna:
    Figure: objeto figura do matplotlib
    """
    # Criar a figura e eixos
    plt.close('all')  # Fecha todas as figuras existentes
    fig, axs = plt.subplots(1, 2, figsize=(14, 8))
    
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
    """
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title('Diagrama do Muro de Gravidade')
    
    # Desenhar o muro
    pontos_muro = [
        [0, 0],
        [b_mon, 0],
        [b_mon - (b_mon - crista), h],
        [0, h]
    ]
    ax.add_patch(plt.Polygon(pontos_muro, closed=True, fill=False, color='black', linewidth=2))
    
    # Calcular cargas
    area_muro = 0.5 * (b_mon - crista) * h + crista * h
    peso_muro = area_muro * gamma_concreto
    peso_solo = 0.5 * (b_mon - crista) * h * (gamma_solo - gamma_agua)
    e0 = 0.5 * (gamma_solo - gamma_agua) * h**2 * k0
    e0_agua = 0.5 * gamma_agua * h**2
    
    # Calcular tensões e momentos
    x_cg = b_mon/2
    y_cg = h/3 * (2*crista + b_mon)/(crista + b_mon)
    braco_estabilizante_cg = ((b_mon - crista)/3 + crista)
    terra_estabilizante_cg = ((b_mon - crista)*2/3 + crista)
    braco_tombamento = h/3
    
    momento_total = peso_muro*braco_estabilizante_cg + peso_solo*terra_estabilizante_cg - (e0 + e0_agua)*braco_tombamento
    peso_total = peso_muro + peso_solo
    
    tensao_max = peso_total/b_mon + abs(momento_total/(b_mon**2/6))
    tensao_min = peso_total/b_mon - abs(momento_total/(b_mon**2/6))
    
    # Desenhar cargas
    # Peso do muro
    ax.arrow(braco_estabilizante_cg, y_cg, 0, -0.5, head_width=0.1, head_length=0.1, fc='blue', ec='blue', label='Peso do Muro')
    ax.text(braco_estabilizante_cg, y_cg + 0.5, f'Pm = {peso_muro:.1f} kN/m', ha='center', color='blue')
    
    # Peso do solo - Desenhar polígono de forças
    pontos_solo = [
        [b_mon - (b_mon - crista), h],
        [b_mon, h],
        [b_mon, 0],
    ]
    ax.add_patch(plt.Polygon(pontos_solo, closed=True, fill=True, color='green', alpha=0.2))

    # CG do solo
    x_cg_solo = b_mon - (b_mon - crista)/3
    y_cg_solo = 2*h/3

    ax.arrow(x_cg_solo, y_cg_solo, 0, -0.5, head_width=0.1, head_length=0.1, fc='green', ec='green', label='Peso do Solo')
    ax.text(x_cg_solo, y_cg_solo + 0.2, f'Ps = {peso_solo:.1f} kN/m', ha='center', color='green')
    
    # Empuxo - Diagrama triangular
    empuxo_scale = 0.02
    pontos_empuxo = [
        [b_mon, 0],
        [b_mon, h],
        [b_mon + e0*empuxo_scale, 0]
    ]
    ax.add_patch(plt.Polygon(pontos_empuxo, closed=True, fill=True, color='red', alpha=0.2))
    ax.arrow(b_mon + e0*empuxo_scale, h/3, -e0*empuxo_scale, 0, head_width=0.1, head_length=0.1, fc='red', ec='red', label='Empuxo')
    ax.text(b_mon + e0*empuxo_scale/2, h/3, f'E = {e0 + e0_agua:.1f} kN/m', ha='center', color='red')
    
    # Diagrama de tensões na base
    tensao_scale = 0.003


    ax.plot([0, b_mon], [-tensao_max*tensao_scale, -tensao_min*tensao_scale], 'r-', linewidth=2, label='Tensões na Base')
    ax.plot([0, b_mon], [-pressao_adm*tensao_scale, -pressao_adm*tensao_scale], 'g--', linewidth=2, label=f'Pressão Admissível: {pressao_adm} kN/m²')
    
    # Configurar o gráfico
    ax.set_xlim(- 0.5, b_mon + 0.5 + e0*empuxo_scale)
    ax.set_ylim(-tensao_max*tensao_scale - 0.5, h + 0.5)
    ax.grid(True)
    ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
    
    # Adicionar cotas (linhas de dimensão) nos eixos x e y
    # Cota da base (x)
    ax.annotate('', xy=(0, 0.3), xytext=(b_mon, 0.3),
                arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
    ax.text(b_mon/2, 0.2, f'Base: {b_mon:.2f} m', ha='center', va='top', fontsize=11, color='#34495e')

    # Cota da altura (y)
    ax.annotate('', xy=(-0.3, 0), xytext=(-0.3, h),
                arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
    ax.text(-0.35, h/2, f'Altura: {h:.2f} m', ha='right', va='center', fontsize=11, color='#34495e', rotation='vertical')

    # Cota da crista (x)
    ax.annotate('', xy=(0, h*1.02), xytext=(crista, h*1.02),
                arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
    ax.text(crista/2, h*1.02+0.08, f'Crista: {crista:.2f} m', ha='center', va='bottom', fontsize=11, color='#34495e', rotation='horizontal')

    # Peso do muro (cota do braço)
    ax.annotate('', xy=(0, y_cg), xytext=(braco_estabilizante_cg, y_cg),
                arrowprops=dict(arrowstyle='<->', color='blue', lw=1, ls='--'))
    ax.text(braco_estabilizante_cg/2, y_cg+0.15, f'{braco_estabilizante_cg:.2f} m',
            ha='center', va='bottom', fontsize=9, color='blue')

    # Peso do solo (cota do braço)
    ax.annotate('', xy=(0, y_cg_solo), xytext=(x_cg_solo, y_cg_solo),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1, ls='--'))
    ax.text(x_cg_solo/2, y_cg_solo+0.12, f'{x_cg_solo-crista:.2f} m',
            ha='center', va='bottom', fontsize=9, color='green')

    # Empuxo (altura do muro)
    ax.annotate('', xy=(b_mon+e0*empuxo_scale+0.15, 0), xytext=(b_mon+e0*empuxo_scale+0.15, h/3),
                arrowprops=dict(arrowstyle='<->', color='red', lw=1, ls='--'))
    ax.text(b_mon+e0*empuxo_scale+0.18, h/2/3, f'h = {h/3:.2f} m',
            ha='left', va='center', fontsize=9, color='red', rotation=90)

    # Desenhar sobrecarga a montante (retângulo/linha/seta)
    ax.plot([crista, b_mon], [h*1.05+0.08, h*1.05+0.08], color='orange', lw=2, solid_capstyle='butt')
    ax.arrow(crista, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
    ax.arrow((b_mon-crista)/3+crista, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
    ax.arrow((b_mon-crista)/3*2+crista, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
    ax.arrow(b_mon, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
    ax.text((b_mon-crista)/2+crista, h+0.32, f'q = {sobrecarga_mon:.1f} kN/m²', ha='center', va='bottom', color='orange', fontsize=11, fontweight='bold')

    # Gera quantitativos
    quantitativos = gerar_quantitativos_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, k0, gamma_agua, sobrecarga_mon, base_max)
    

    # Segundo subplot (relatório)
    ax = axs[1]
    ax.set_title('Quantitativos dos Materiais')
    ax.set_ylabel('Quantidade')
    ax.set_ylim(-1, len(quantitativos))  # Define o limite do eixo y para garantir que todos os textos sejam visíveis
    
    # Relatório de Estabilidade
    relatorio = (
        f"Resumo do Quantitativo:\n"
        f"1. Área de Aço: {quantitativos['area_aco']:.2f} kg/m\n"
        f"2. Volume de Concreto: {quantitativos['volume_concreto']:.2f} m³/m\n"
        f"3. Volume de Solo - Corte: {quantitativos['volume_corte']:.2f} m³/m\n"
        f"4. Volume de Solo - Aterro: {quantitativos['volume_aterro']:.2f} m³/m\n"
        f"5. Volume de Solo - Carga [+] / Descarga [-]: {quantitativos['volume_descarga']:.2f} m³/m\n"

        f"Relatório de Estabilidade (caso de carregamento normal):\n"
        f"1. Fator de Segurança ao Deslizamento: {calculos_gravidade['fs_deslizamento']:.2f} {'(OK)' if calculos_gravidade['fs_deslizamento'] >= 1.0 else '(NÃO OK)'}\n"
        f"2. Fator de Segurança ao Tombamento: {calculos_gravidade['fs_tombamento']:.2f} {'(OK)' if calculos_gravidade['fs_tombamento'] >= 1.5 else '(NÃO OK)'}\n"
        f"3. Tensão Máxima: {calculos_gravidade['tensao_max']:.2f} kN/m² {'(OK)' if calculos_gravidade['tensao_ok'] else '(NÃO OK)'}\n"
        f"4. Tensão Mínima: {calculos_gravidade['tensao_min']:.2f} kN/m² {'(OK)' if calculos_gravidade['tensao_min'] > 0 else '(NÃO OK)'}\n"
    )
    
    # Adicionar informações sobre a base teórica e máxima, se disponíveis
    if 'base_teorica' in calculos_gravidade:
        base_teorica = calculos_gravidade['base_teorica']
        base_atual_ok = calculos_gravidade.get('base_atual_ok', False)
        base_max_ok = calculos_gravidade.get('base_max_ok', True)
        base_ok = calculos_gravidade.get('base_ok', False)
        
        relatorio += (
            f"\nVerificação da Base:\n"
            f"5. Base Atual: {b_mon:.2f} m\n"
            f"6. Base Teórica Aproximada: {base_teorica:.2f} m {'(OK)' if base_atual_ok else '(NÃO OK)'}\n"
        )
        
        if 'base_max_ok' in calculos_gravidade:
            base_max = calculos_gravidade.get('base_max', 'N/A')
            if isinstance(base_max, (int, float)):
                status_max = "(OK)" if base_max_ok else "(NÃO OK)"
                relatorio += f"7. Base Máxima Permitida: {base_max:.2f} m {status_max}\n"
            
        relatorio += f"8. Base Adequada: {'Sim' if base_ok else 'Não'}\n"
        
        # Adicionar sugestões se houver problemas
        if not base_ok:
            relatorio += "\nSugestões:\n"
            if not base_atual_ok:
                relatorio += f"- Aumente a base em pelo menos {base_teorica - b_mon:.2f} m para garantir a estabilidade.\n"
            if not base_max_ok:
                relatorio += f"- Reconsidere os parâmetros do projeto, pois a base necessária excede o limite máximo permitido.\n"
    
    ax.text(0.1, 0.5, relatorio, fontsize=12, va='center', ha='left')
    ax.axis('off')  # Remover os eixos para o texto
    
    # Adicionar uma mensagem destacada sobre a adequação da base
    if 'base_ok' in calculos_gravidade and not calculos_gravidade['base_ok']:
        mensagens = []
        if 'base_atual_ok' in calculos_gravidade and not calculos_gravidade['base_atual_ok']:
            mensagens.append(f"Base atual insuficiente (necessário +{calculos_gravidade['base_teorica'] - b_mon:.2f}m)")
        if 'base_max_ok' in calculos_gravidade and not calculos_gravidade['base_max_ok']:
            mensagens.append(f"Base teórica excede o limite máximo permitido")
        
        if mensagens:
            plt.figtext(0.5, 0.01, " | ".join(mensagens), 
                      ha='center', fontsize=12, color='red',
                      bbox={"facecolor":"yellow", "alpha":0.5, "pad":5})
    
    plt.tight_layout()
    plt.show()

def validar_dados_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo, phi, c, pressao_adm, nivel_agua):
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
    if gamma_solo <= 0:
        mensagens_erro.append("O peso específico do solo deve ser maior que zero")
    if pressao_adm <= 0:
        mensagens_erro.append("A pressão admissível deve ser maior que zero")
    if phi < 0 or phi > 45:
        mensagens_erro.append("O ângulo de atrito deve estar entre 0 e 45 graus")
    if c < 0:
        mensagens_erro.append("A coesão deve ser maior ou igual a zero")
    
    # Verificar coerência entre valores
    if crista >= b_mon:
        mensagens_erro.append("A largura da crista deve ser menor que a base")
    if nivel_agua >= h:
        mensagens_erro.append("O nível d'água não pode ser maior que a altura do muro")
    
    # Verificar limites típicos
    if gamma_concreto < 18 or gamma_concreto > 28:
        mensagens_erro.append("O peso específico do concreto está fora do intervalo típico (18-28 kN/m³)")
    if gamma_solo < 14 or gamma_solo > 22:
        mensagens_erro.append("O peso específico do solo está fora do intervalo típico (14-22 kN/m³)")
    if pressao_adm > 500:
        mensagens_erro.append("A pressão admissível parece muito alta (> 500 kN/m²)")
    
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
        gamma_solo = float(entry_gamma_solo.get())
        phi = float(entry_phi_estabilidade.get())
        c = float(entry_coesao.get())
        pressao_adm = float(entry_pressao_adm.get())
        nivel_agua = float(entry_nivel_agua.get())
        fs_coesao = float(entry_fs_coesao.get())
        fs_atrito = float(entry_fs_atrito.get())
        k0 = float(entry_k0.get())  # Usando Ka como K0 para o muro de gravidade
        base_max = float(entry_base_max.get()) if entry_base_max.get() else None
        gamma_agua = float(entry_gamma_agua.get())
        sobrecarga_mon = float(entry_sobrecarga_mon.get())
        
        # Validar dados
        valido, mensagem = validar_dados_muro_gravidade(h, crista, b_mon, gamma_concreto, 
                                                      gamma_solo, phi, c, pressao_adm, nivel_agua)
        
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
        resultado = calcular_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo, 
                                           phi, c, pressao_adm, nivel_agua, fs_coesao, 
                                           fs_atrito, k0, gamma_agua, sobrecarga_mon, base_max)
        
        # Verificar se o resultado foi bem-sucedido
        if resultado is None:
            messagebox.showerror("Erro", "Falha ao calcular o muro de gravidade.")
            return
        
        # Plotar o muro
        plotar_muro_gravidade(
            h, 0, crista, b_mon, 
            gamma_concreto, gamma_solo, phi, c, 
            pressao_adm, nivel_agua, fs_coesao, fs_atrito, k0, gamma_agua, sobrecarga_mon,
            resultado  # Passando o resultado completo como calculos_gravidade
        )
        
    except ValueError as e:
        messagebox.showerror("Erro", f"Por favor, insira valores válidos: {str(e)}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")



def plotar_diagramas_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, k0, base_max=None, gamma_agua=10, sobrecarga_mon=0):
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
    """
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title('Diagrama do Muro de Gravidade')
    
    # Desenhar o muro
    pontos_muro = [
        [0, 0],
        [b_mon, 0],
        [b_mon - (b_mon - crista), h],
        [0, h]
    ]
    ax.add_patch(plt.Polygon(pontos_muro, closed=True, fill=False, color='black', linewidth=2))
    
    # Calcular cargas
    area_muro = 0.5 * (b_mon - crista) * h + crista * h
    peso_muro = area_muro * gamma_concreto
    peso_solo = 0.5 * (b_mon - crista) * h * (gamma_solo - gamma_agua)
    e0 = 0.5 * (gamma_solo - gamma_agua) * h**2 * k0
    e0_agua = 0.5 * gamma_agua * h**2
    
    # Calcular tensões e momentos
    x_cg = b_mon/2
    y_cg = h/3 * (2*crista + b_mon)/(crista + b_mon)
    braco_estabilizante_cg = ((b_mon - crista)/3 + crista)
    terra_estabilizante_cg = ((b_mon - crista)*2/3 + crista)
    braco_tombamento = h/3
    
    momento_total = peso_muro*braco_estabilizante_cg + peso_solo*terra_estabilizante_cg - (e0 + e0_agua)*braco_tombamento
    peso_total = peso_muro + peso_solo
    
    tensao_max = peso_total/b_mon + abs(momento_total/(b_mon**2/6))
    tensao_min = peso_total/b_mon - abs(momento_total/(b_mon**2/6))
    
    # Desenhar cargas
    # Peso do muro
    ax.arrow(braco_estabilizante_cg, y_cg, 0, -0.5, head_width=0.1, head_length=0.1, fc='blue', ec='blue', label='Peso do Muro')
    ax.text(braco_estabilizante_cg, y_cg + 0.5, f'Pm = {peso_muro:.1f} kN/m', ha='center', color='blue')
    
    # Peso do solo - Desenhar polígono de forças
    pontos_solo = [
        [b_mon - (b_mon - crista), h],
        [b_mon, h],
        [b_mon, 0],
    ]
    ax.add_patch(plt.Polygon(pontos_solo, closed=True, fill=True, color='green', alpha=0.2))

    # CG do solo
    x_cg_solo = b_mon - (b_mon - crista)/3
    y_cg_solo = 2*h/3

    ax.arrow(x_cg_solo, y_cg_solo, 0, -0.5, head_width=0.1, head_length=0.1, fc='green', ec='green', label='Peso do Solo')
    ax.text(x_cg_solo, y_cg_solo + 0.2, f'Ps = {peso_solo:.1f} kN/m', ha='center', color='green')
    
    # Empuxo - Diagrama triangular
    empuxo_scale = 0.02
    pontos_empuxo = [
        [b_mon, 0],
        [b_mon, h],
        [b_mon + e0*empuxo_scale, 0]
    ]
    ax.add_patch(plt.Polygon(pontos_empuxo, closed=True, fill=True, color='red', alpha=0.2))
    ax.arrow(b_mon + e0*empuxo_scale, h/3, -e0*empuxo_scale, 0, head_width=0.1, head_length=0.1, fc='red', ec='red', label='Empuxo')
    ax.text(b_mon + e0*empuxo_scale/2, h/3, f'E = {e0 + e0_agua:.1f} kN/m', ha='center', color='red')
    
    # Diagrama de tensões na base
    tensao_scale = 0.003


    ax.plot([0, b_mon], [-tensao_max*tensao_scale, -tensao_min*tensao_scale], 'r-', linewidth=2, label='Tensões na Base')
    ax.plot([0, b_mon], [-pressao_adm*tensao_scale, -pressao_adm*tensao_scale], 'g--', linewidth=2, label=f'Pressão Admissível: {pressao_adm} kN/m²')
    
    # Configurar o gráfico
    ax.set_xlim(- 0.5, b_mon + 0.5 + e0*empuxo_scale)
    ax.set_ylim(-tensao_max*tensao_scale - 0.5, h + 0.5)
    ax.grid(True)
    ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
    
    # Adicionar cotas (linhas de dimensão) nos eixos x e y
    # Cota da base (x)
    ax.annotate('', xy=(0, 0.3), xytext=(b_mon, 0.3),
                arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
    ax.text(b_mon/2, 0.2, f'Base: {b_mon:.2f} m', ha='center', va='top', fontsize=11, color='#34495e')

    # Cota da altura (y)
    ax.annotate('', xy=(-0.3, 0), xytext=(-0.3, h),
                arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
    ax.text(-0.35, h/2, f'Altura: {h:.2f} m', ha='right', va='center', fontsize=11, color='#34495e', rotation='vertical')

    # Cota da crista (x)
    ax.annotate('', xy=(0, h*1.02), xytext=(crista, h*1.02),
                arrowprops=dict(arrowstyle='<->', color='#34495e', lw=1.5))
    ax.text(crista/2, h*1.02+0.08, f'Crista: {crista:.2f} m', ha='center', va='bottom', fontsize=11, color='#34495e', rotation='horizontal')

    # Peso do muro (cota do braço)
    ax.annotate('', xy=(0, y_cg), xytext=(braco_estabilizante_cg, y_cg),
                arrowprops=dict(arrowstyle='<->', color='blue', lw=1, ls='--'))
    ax.text(braco_estabilizante_cg/2, y_cg+0.15, f'{braco_estabilizante_cg:.2f} m',
            ha='center', va='bottom', fontsize=9, color='blue')

    # Peso do solo (cota do braço)
    ax.annotate('', xy=(0, y_cg_solo), xytext=(x_cg_solo, y_cg_solo),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1, ls='--'))
    ax.text(x_cg_solo/2, y_cg_solo+0.12, f'{x_cg_solo-crista:.2f} m',
            ha='center', va='bottom', fontsize=9, color='green')

    # Empuxo (altura do muro)
    ax.annotate('', xy=(b_mon+e0*empuxo_scale+0.15, 0), xytext=(b_mon+e0*empuxo_scale+0.15, h/3),
                arrowprops=dict(arrowstyle='<->', color='red', lw=1, ls='--'))
    ax.text(b_mon+e0*empuxo_scale+0.18, h/2/3, f'h = {h/3:.2f} m',
            ha='left', va='center', fontsize=9, color='red', rotation=90)

    # Desenhar sobrecarga a montante (retângulo/linha/seta)
    ax.plot([crista, b_mon], [h*1.05+0.08, h*1.05+0.08], color='orange', lw=2, solid_capstyle='butt')
    ax.arrow(crista, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
    ax.arrow((b_mon-crista)/3+crista, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
    ax.arrow((b_mon-crista)/3*2+crista, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
    ax.arrow(b_mon, h*1.05+0.08, 0, -0.05*h, head_width=h*0.01, head_length=0.08, fc='orange', ec='orange')
    ax.text((b_mon-crista)/2+crista, h+0.32, f'q = {sobrecarga_mon:.1f} kN/m²', ha='center', va='bottom', color='orange', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.show()

def exibir_diagramas_gravidade_popup():
    try:
        # Obter os valores da interface principal
        h = float(entry_h.get())
        crista = float(entry_crista.get())
        b_mon = float(entry_b_gravidade.get())
        gamma_concreto = float(entry_gamma_concreto.get())
        gamma_solo = float(entry_gamma_solo.get())
        phi = float(entry_phi_estabilidade.get())
        c = float(entry_coesao.get())
        pressao_adm = float(entry_pressao_adm.get())
        nivel_agua = float(entry_nivel_agua.get())
        fs_coesao = float(entry_fs_coesao.get())
        fs_atrito = float(entry_fs_atrito.get())
        k0 = float(entry_k0.get())
        base_max = float(entry_base_max.get()) if entry_base_max.get() else None
        
        # Plotar os diagramas
        plotar_diagramas_gravidade(
            h, crista, b_mon, gamma_concreto, gamma_solo,
            phi, c, pressao_adm, nivel_agua, fs_coesao,
            fs_atrito, k0, base_max
        )
        
    except ValueError as e:
        messagebox.showerror("Erro", f"Por favor, insira valores válidos: {str(e)}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")

def gerar_quantitativos_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, ka, gamma_agua, sobrecarga_mon,
                                 preco_concreto=350, preco_aco=8.5, diametro_barra=10, espacamento_barra=0.20, base_max=None):
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
    # Cálculos do muro de gravidade
    resultado_gravidade = calcular_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, ka, gamma_agua, sobrecarga_mon, base_max)
    
    # Cálculo do volume de concreto (trapézio)
    volume_concreto = resultado_gravidade['volume_concreto']
    
    # Cálculo da armadura na crista
    area_barra = math.pi * (diametro_barra/1000)**2 / 4  # m²
    comprimento_barra = 2 + crista  # Comprimento de cada barra - Crista + 2m (+- anc para ambos os lados)
    numero_barras = math.ceil(h / espacamento_barra)
    volume_aco = area_barra * comprimento_barra * numero_barras  # Volume total de aço em m³
    peso_aco = volume_aco * 7850  # kg/m (densidade do aço)
    
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
    volume_concreto_25 = volume_concreto * 0.9  # 90% em concreto estrutural
    volume_concreto_6 = volume_concreto * 0.1   # 10% em concreto de regularização
    
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
        gamma_solo = float(entry_gamma_solo.get())
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
        ka = float(entry_ka.get())  # Coeficiente de empuxo passivo para muro de flexão
        k0 = float(entry_k0.get())  # Coeficiente de empuxo ativo para muro de gravidade
        pressao_adm = float(entry_pressao_adm.get())
        sobrecarga_mon = float(entry_sobrecarga_mon.get())
        gamma_agua = float(entry_gamma_agua.get())
        
        # Obter o valor da base máxima permitida
        base_max = float(entry_base_max.get())
        
        c = float(entry_coesao.get())
        phi_estabilidade = float(entry_phi_estabilidade.get())

        # Chamar a função de dimensionamento aqui
        dia_barra, espacamento = dimensionar_muro_arrimo_flexao(h, b_mon, d, gamma_solo, phi, fck, fyk, ka, nivel_agua)
        as_final = math.pi * (dia_barra/10)**2 / 4 * 100 / espacamento  # área de uma barra em cm²

        peso_corte, _, volume_aterro, volume_corte = calcular_peso_terra_montante(h, b_mon, gamma_solo)
        volume_corte = peso_corte / gamma_solo

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
            h, d, b_jus, b_mon, gamma_solo, phi_estabilidade,
            gamma_concreto, nivel_agua, ka, pressao_adm,
            c, fs_coesao, fs_atrito, base_max
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

        quantitativos_gravidade = gerar_quantitativos_gravidade(h, crista, b_gravidade, gamma_concreto, gamma_solo, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, ka, gamma_agua, sobrecarga_mon, base_max)
        resultado_gravidade = calcular_muro_gravidade(h, crista, b_gravidade, gamma_concreto, gamma_solo, phi, c, pressao_adm, nivel_agua, fs_coesao, fs_atrito, ka, gamma_agua, sobrecarga_mon, base_max)
        
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
        
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira valores válidos.")

def botao_plotar_muro_arrimo():
    try:
        h = float(entry_h.get())
        b_jus = float(entry_b_jus.get())
        b_mon = float(entry_b_mon.get())
        d = calcular_altura_util(h)
        gamma_solo = float(entry_gamma_solo.get())
        phi = float(entry_phi_estabilidade.get())
        fck = float(entry_fck.get())
        fyk = float(entry_fyk.get())
        gamma_concreto = float(entry_gamma_concreto.get())
        ka = float(entry_ka.get())  # Coeficiente de empuxo passivo
        pressao_adm = float(entry_pressao_adm.get())
        c = float(entry_coesao.get())
        fs_coesao = float(entry_fs_coesao.get())
        fs_atrito = float(entry_fs_atrito.get())
        base_max = float(entry_base_max.get())
        nivel_agua = float(entry_nivel_agua.get())

        # Chamar a função de dimensionamento
        dia_barra, espacamento = dimensionar_muro_arrimo_flexao(h, b_mon, d, gamma_solo, phi, fck, fyk, ka, nivel_agua)
        as_final = math.pi * (dia_barra/10)**2 / 4 * 100 / espacamento  # área de uma barra em cm²

        # Verificação de estabilidade
        resultados_estabilidade = verificar_estabilidade_flexao(
            h, d, b_jus, b_mon, gamma_solo, phi,
            gamma_concreto, nivel_agua, ka, pressao_adm,
            c, fs_coesao, fs_atrito, base_max
        )
        
        # Plotar o muro
        plotar_muro_arrimo(b_jus, b_mon, h, d, as_final, gamma_solo, 
                         resultados_estabilidade['tensao_max'], pressao_adm, resultados_estabilidade)
        
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira valores válidos.")

def verificar_estabilidade_flexao(h, d, b_jus, b_mon, gamma_solo, phi_estabilidade, gamma_concreto, nivel_agua, ka, pressao_adm, c, fs_coesao, fs_atrito, base_max=None):
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
    
    # Cálculo do empuxo passivo
    ep = 0.5 * gamma_solo * h**2 * ka  # Empuxo passivo total
    
    e_agua = 0.5 * 10 * nivel_agua**2 * ka # Empuxo de água 10 kN/m³

    # Área da seção transversal do muro
    area_muro = ((b_total) * d) + (h * d) - (d * d)
    
    # Peso do muro por metro linear
    peso_muro = area_muro * gamma_concreto
    
    # Centro de gravidade do muro (coordenada x em relação à extremidade jusante)
    # Componentes:
    # Base (retângulo)
    area_base = b_total * 1 # 1 m de espessura considerada
    cg_base = b_total / 2
 
    # Talão montante (retângulo)
    area_talao = (h - d) * d
    x_talao = b_jus + (d / 2)
    
    # CG total
    x_muro = (area_base*cg_base + area_talao*x_talao) / area_muro
    
    # Cálculo do peso do solo
    # Volume de solo sobre o talão
    volume_solo = (b_mon) * (h - d)
    peso_solo = volume_solo * gamma_solo
    x_solo = b_jus + d + (b_mon / 2)
    
    # Força normal total na base
    forca_normal = peso_muro + peso_solo # Colocar aqui a subpressão depois
    
    # Isso permite que o usuário defina fatores de segurança diferentes 
    # para cada componente de resistência, 
    # seguindo as recomendações da NBR 11682/2022 para contenções.

    # Forças resistentes ao deslizamento
    resistencia_coesao = c * b_total
    resistencia_atrito = forca_normal * math.tan(math.radians(phi_estabilidade))
    
    # Fatores de segurança parciais
    fs_deslizamento_total = (resistencia_coesao / (ep * fs_coesao)) + (resistencia_atrito / (ep * fs_atrito))
    
    # Momentos em relação ao centro da base (momento estabilizante)
    momento_muro_cg = peso_muro * (x_muro - cg_base)
    momento_solo_cg = peso_solo * (x_solo - cg_base)

    # Momentos em relação ao ponto de tombamento (momento estabilizante)
    momento_muro = peso_muro * x_muro
    momento_solo = peso_solo * x_solo
    # Momento estabilizante total no CG da base
    me_cg = momento_muro_cg + momento_solo_cg
    
    # Momento estabilizante total
    me = momento_muro + momento_solo

    # Momento do empuxo em relação ao centro (momento de tombamento)
    braco_ep = h / 3  # Ponto de aplicação do empuxo passivo em y = h/3 a partir da base
    mt = ep * braco_ep
    
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
        'fs_tombamento_ok': fs_tombamento_ok,
        'tensao_max': tensao_max,
        'tensao_min': tensao_min,
        'pressao_adm_ok': pressao_adm_ok,
        'fs_deslizamento_ok': fs_deslizamento_ok,
        'fs_deslizamento_total': fs_deslizamento_total,
        'base_teorica': base_teorica,
        'base_atual_ok': base_atual_ok,
        'base_max_ok': base_max_ok if base_max is not None else True,
        'base_ok': base_ok
    }

def calcular_muro_gravidade(h, crista, b_mon, gamma_concreto, gamma_solo, phi, c, pressao_adm, nivel_agua=0, fs_coesao=4, fs_atrito=2, k0=0.5, base_max=None, gamma_agua=10, sobrecarga_mon=0   ):
    """
    Calcula quantitativos para muros de gravidade (seção trapezoidal)
    
    Parâmetros:
    h: altura total do muro (m)
    crista: largura da base a jusante (m)
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
    """
    # 1. Cálculos geométricos e de peso
    area_muro = 0.5 * (b_mon - crista) * h + crista * h
    volume_concreto = area_muro
    peso_muro = volume_concreto * gamma_concreto
    gamma_solo_sub = gamma_solo - gamma_agua
    peso_solo = 0.5 * (b_mon - crista) * h * gamma_solo_sub
    
    # 2. Cálculo dos empuxos
    e0 = 0.5 * gamma_solo_sub * h**2 * k0  # Empuxo em repouso
    e0_agua = 0.5 * gamma_agua * h**2
    empuxo_total = e0 + e0_agua
    
    # 3. Verificação ao Deslizamento
    fs_deslizamento = c * b_mon / (empuxo_total * fs_coesao) + (peso_muro + peso_solo)*math.tan(math.radians(phi)) / (empuxo_total * fs_atrito)
    fs_deslizamento_ok = fs_deslizamento >= 1.0  # Valor mínimo recomendado pela NBR 11682 <- Já está incorporado no cálculo

    # 4. Verificação ao Tombamento
    braco_estabilizante_pt = (b_mon - crista)/3 + crista # Em relação ao ponto de tombamento
    terra_estabilizante_pt = (b_mon - crista)*2/3 + crista    # Em relação ao ponto de tombamento
    braco_tombamento_pt = h/3
    fs_tombamento = (peso_muro*braco_estabilizante_pt + peso_solo*terra_estabilizante_pt) / (empuxo_total*braco_tombamento_pt)
    fs_tombamento_ok = fs_tombamento >= 1.5  # Valor para caso de carregamento normal ELETROBRAS 2003

    # 5. Verificação de Tensões na Base
    x_cg = b_mon/2
    y_cg = h/3 * (2*crista + b_mon)/(crista + b_mon)
    braco_estabilizante_cg = ((b_mon - crista)/3 + crista) - x_cg # Em relação ao centro da base
    terra_estabilizante_cg = ((b_mon - crista)*2/3 + crista) - x_cg    # Em relação ao centro da base
    braco_tombamento = h/3

    excentricidade = (b_mon)/2 - ((peso_muro*braco_estabilizante_cg + peso_solo*terra_estabilizante_cg) - e0*braco_tombamento)/(peso_muro + peso_solo)
    momento_inercia = (1/6)*b_mon**2
    peso_total = peso_muro + peso_solo
    momento_total = peso_muro*braco_estabilizante_cg + peso_solo*terra_estabilizante_cg - e0*braco_tombamento
    tensao_max = peso_total/b_mon + abs(momento_total/momento_inercia)
    tensao_min = peso_total/b_mon - abs(momento_total/momento_inercia)

    # tensao_max = (peso_muro + peso_solo)/b_mon * (1 + 6*excentricidade/b_mon)
    # tensao_min = (peso_muro + peso_solo)/b_mon * (1 - 6*excentricidade/b_mon)
    tensao_ok = tensao_max <= pressao_adm and tensao_min >= 0
    
    # Cálculo da base teórica necessária
    # Considerando os critérios de estabilidade:
    # 1. Tensão máxima <= pressão admissível
    # 2. Fator de segurança contra tombamento >= 1.5
    # 3. Fator de segurança contra deslizamento >= 1.0
    
    # Base teórica para satisfazer pressão admissível
    # Aproximação: a tensão máxima é inversamente proporcional à largura da base
    base_teorica_pressao = b_mon * (tensao_max / pressao_adm) if pressao_adm > 0 else b_mon
    
    # Base teórica para satisfazer fator de segurança contra tombamento
    base_teorica_tombamento = b_mon * (1.5 / fs_tombamento) if fs_tombamento > 0 else b_mon * 1.5
    
    # Base teórica para satisfazer fator de segurança contra deslizamento
    base_teorica_deslizamento = b_mon * (1.0 / fs_deslizamento) if fs_deslizamento > 0 else b_mon
    
    # Base teórica necessária é o maior valor dentre os três critérios
    base_teorica = max(base_teorica_pressao, base_teorica_tombamento, base_teorica_deslizamento)
    
    # Verificação se a base teórica é menor que a base máxima permitida
    base_atual_ok = base_teorica <= b_mon
    base_max_ok = True
    
    # Verificar se a base teórica é menor que a base máxima permitida
    if base_max is not None:
        base_max_ok = base_teorica <= base_max
    
    # A base só está OK se atende ambos os critérios
    base_ok = base_atual_ok and base_max_ok
    
    # Cálculo dos volumes de solo
    volume_corte = 1.5 * b_mon * (h - 1)  # Fator 1.5 para inclinação de talude
    volume_aterro = volume_corte - 0.5 * b_mon * h  # Aterro compactado atrás do muro
    volume_descarga = max(volume_corte - volume_aterro, 0)  # Solo excedente
    
    return {
        'fs_deslizamento': fs_deslizamento,
        'fs_deslizamento_ok': fs_deslizamento_ok,
        'fs_tombamento': fs_tombamento,
        'fs_tombamento_ok': fs_tombamento_ok,
        'tensao_max': tensao_max,
        'tensao_min': tensao_min,
        'tensao_ok': tensao_ok,
        'peso_muro': peso_muro,
        'peso_solo': peso_solo,
        'base_teorica': base_teorica,
        'base_atual_ok': base_atual_ok,
        'base_max_ok': base_max_ok,
        'base_ok': base_ok,
        'volume_concreto': volume_concreto,
        'volume_corte': volume_corte,
        'volume_aterro': volume_aterro,
        'volume_descarga': volume_descarga
    }

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

# Variáveis globais para armazenar os custos
entry_concreto_25_mat = None
entry_concreto_6_mat = None
entry_aco_ca50_mat = None
entry_forma_mat = None
entry_aterro_mat = None
entry_corte_mat = None
entry_carga_mat = None
entry_descarga_mat = None

entry_concreto_25_mdo = None
entry_concreto_6_mdo = None
entry_aco_ca50_mdo = None
entry_aterro_mdo = None
entry_corte_mdo = None
entry_carga_mdo = None
entry_descarga_mdo = None
entry_forma_mdo = None

entry_concreto_25_tempo = None
entry_concreto_6_tempo = None
entry_aco_ca50_tempo = None
entry_aterro_tempo = None
entry_corte_tempo = None
entry_carga_tempo = None
entry_descarga_tempo = None
entry_forma_tempo = None

label_info_custos = None

def editar_custos_popup():
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
    entry_concreto_25_mat.insert(0, "250")  # Valor default
    entry_concreto_25_mat.grid(row=2, column=2, padx=10, pady=5)

    entry_concreto_25_mdo = tk.Entry(janela_custos)
    entry_concreto_25_mdo.insert(0, "50")  # Valor default
    entry_concreto_25_mdo.grid(row=2, column=3, padx=10, pady=5)

    entry_concreto_25_tempo = tk.Entry(janela_custos)
    entry_concreto_25_tempo.insert(0, "1")  # Valor default
    entry_concreto_25_tempo.grid(row=2, column=4, padx=10, pady=5)
    
    tk.Label(janela_custos, text="Concreto Massa (m³):").grid(row=3, column=1, sticky="w", padx=10, pady=5)
    entry_concreto_6_mat = tk.Entry(janela_custos)
    entry_concreto_6_mat.insert(0, "150")  # Valor default
    entry_concreto_6_mat.grid(row=3, column=2, padx=10, pady=5)
    
    entry_concreto_6_mdo = tk.Entry(janela_custos)
    entry_concreto_6_mdo.insert(0, "50")  # Valor default
    entry_concreto_6_mdo.grid(row=3, column=3, padx=10, pady=5)

    entry_concreto_6_tempo = tk.Entry(janela_custos)
    entry_concreto_6_tempo.insert(0, "1")  # Valor default
    entry_concreto_6_tempo.grid(row=3, column=4, padx=10, pady=5)
    
    tk.Label(janela_custos, text="Aço CA50 (kg):").grid(row=4, column=1, sticky="w", padx=10, pady=5)
    entry_aco_ca50_mat = tk.Entry(janela_custos)
    entry_aco_ca50_mat.insert(0, "8")  # Valor default
    entry_aco_ca50_mat.grid(row=4, column=2, padx=10, pady=5)
    
    entry_aco_ca50_mdo = tk.Entry(janela_custos)
    entry_aco_ca50_mdo.insert(0, "2")  # Valor default
    entry_aco_ca50_mdo.grid(row=4, column=3, padx=10, pady=5)

    entry_aco_ca50_tempo = tk.Entry(janela_custos)
    entry_aco_ca50_tempo.insert(0, "1")  # Valor default
    entry_aco_ca50_tempo.grid(row=4, column=4, padx=10, pady=5)

    tk.Label(janela_custos, text="Forma (m²):").grid(row=5, column=1, sticky="w", padx=10, pady=5)
    entry_forma_mat = tk.Entry(janela_custos)
    entry_forma_mat.insert(0, "15")  # Valor default
    entry_forma_mat.grid(row=5, column=2, padx=10, pady=5)
    
    entry_forma_mdo = tk.Entry(janela_custos)
    entry_forma_mdo.insert(0, "5")  # Valor default
    entry_forma_mdo.grid(row=5, column=3, padx=10, pady=5)

    entry_forma_tempo = tk.Entry(janela_custos)
    entry_forma_tempo.insert(0, "1")  # Valor default
    entry_forma_tempo.grid(row=5, column=4, padx=10, pady=5)

    tk.Label(janela_custos, text="Aterro (m³):").grid(row=6, column=1, sticky="w", padx=10, pady=5)
    entry_aterro_mat = tk.Entry(janela_custos)
    entry_aterro_mat.insert(0, "50")  # Valor default
    entry_aterro_mat.grid(row=6, column=2, padx=10, pady=5)

    entry_aterro_mdo = tk.Entry(janela_custos)
    entry_aterro_mdo.insert(0, "50")  # Valor default
    entry_aterro_mdo.grid(row=6, column=3, padx=10, pady=5)

    entry_aterro_tempo = tk.Entry(janela_custos)
    entry_aterro_tempo.insert(0, "1")  # Valor default
    entry_aterro_tempo.grid(row=6, column=4, padx=10, pady=5)

    tk.Label(janela_custos, text="Corte (m³):").grid(row=7, column=1, sticky="w", padx=10, pady=5)
    entry_corte_mat = tk.Entry(janela_custos)
    entry_corte_mat.insert(0, "50")  # Valor default
    entry_corte_mat.grid(row=7, column=2, padx=10, pady=5)

    entry_corte_mdo = tk.Entry(janela_custos)
    entry_corte_mdo.insert(0, "50")  # Valor default
    entry_corte_mdo.grid(row=7, column=3, padx=10, pady=5)

    entry_corte_tempo = tk.Entry(janela_custos)
    entry_corte_tempo.insert(0, "1")  # Valor default
    entry_corte_tempo.grid(row=7, column=4, padx=10, pady=5)
    
    tk.Label(janela_custos, text="Carga (m³):").grid(row=8, column=1, sticky="w", padx=10, pady=5)
    entry_carga_mat = tk.Entry(janela_custos)
    entry_carga_mat.insert(0, "50")  # Valor default
    entry_carga_mat.grid(row=8, column=2, padx=10, pady=5)

    entry_carga_mdo = tk.Entry(janela_custos)
    entry_carga_mdo.insert(0, "50")  # Valor default
    entry_carga_mdo.grid(row=8, column=3, padx=10, pady=5)

    entry_carga_tempo = tk.Entry(janela_custos)
    entry_carga_tempo.insert(0, "1")  # Valor default
    entry_carga_tempo.grid(row=8, column=4, padx=10, pady=5)
    
    tk.Label(janela_custos, text="Descarga (m³):").grid(row=9, column=1, sticky="w", padx=10, pady=5)
    entry_descarga_mat = tk.Entry(janela_custos)
    entry_descarga_mat.insert(0, "50")  # Valor default
    entry_descarga_mat.grid(row=9, column=2, padx=10, pady=5)

    entry_descarga_mdo = tk.Entry(janela_custos)
    entry_descarga_mdo.insert(0, "50")  # Valor default
    entry_descarga_mdo.grid(row=9, column=3, padx=10, pady=5)

    entry_descarga_tempo = tk.Entry(janela_custos)
    entry_descarga_tempo.insert(0, "1")  # Valor default
    entry_descarga_tempo.grid(row=9, column=4, padx=10, pady=5)

    tk.Label(janela_custos, text="Forma (m²):").grid(row=10, column=1, sticky="w", padx=10, pady=5)
    entry_forma_mat = tk.Entry(janela_custos)
    entry_forma_mat.insert(0, "15")  # Valor default
    entry_forma_mat.grid(row=10, column=2, padx=10, pady=5)

    entry_forma_mdo = tk.Entry(janela_custos)
    entry_forma_mdo.insert(0, "5")  # Valor default
    entry_forma_mdo.grid(row=10, column=3, padx=10, pady=5)

    entry_forma_tempo = tk.Entry(janela_custos)
    entry_forma_tempo.insert(0, "1")  # Valor default
    entry_forma_tempo.grid(row=10, column=4, padx=10, pady=5)
        
    # Variáveis para armazenar os valores atuais - MATERIAIS
    valor_concreto_25_mat = tk.StringVar(value=entry_concreto_25_mat.get())
    valor_concreto_6_mat = tk.StringVar(value=entry_concreto_6_mat.get())
    valor_aco_ca50_mat = tk.StringVar(value=entry_aco_ca50_mat.get())
    valor_forma_mat = tk.StringVar(value=entry_forma_mat.get())
    valor_aterro_mat = tk.StringVar(value=entry_aterro_mat.get())
    valor_corte_mat = tk.StringVar(value=entry_corte_mat.get())
    valor_carga_mat = tk.StringVar(value=entry_carga_mat.get())
    valor_descarga_mat = tk.StringVar(value=entry_descarga_mat.get())
    
    # Variáveis para armazenar os valores atuais - MÃO DE OBRA
    valor_concreto_25_mdo = tk.StringVar(value=entry_concreto_25_mdo.get())
    valor_concreto_6_mdo = tk.StringVar(value=entry_concreto_6_mdo.get())
    valor_aco_ca50_mdo = tk.StringVar(value=entry_aco_ca50_mdo.get())
    valor_aterro_mdo = tk.StringVar(value=entry_aterro_mdo.get())
    valor_corte_mdo = tk.StringVar(value=entry_corte_mdo.get())
    valor_carga_mdo = tk.StringVar(value=entry_carga_mdo.get())
    valor_descarga_mdo = tk.StringVar(value=entry_descarga_mdo.get())
    valor_forma_mdo = tk.StringVar(value=entry_forma_mdo.get())

    # Variáveis para armazenar os valores atuais - TEMPO
    valor_concreto_25_tempo = tk.StringVar(value=entry_concreto_25_tempo.get())
    valor_concreto_6_tempo = tk.StringVar(value=entry_concreto_6_tempo.get())
    valor_aco_ca50_tempo = tk.StringVar(value=entry_aco_ca50_tempo.get())
    valor_aterro_tempo = tk.StringVar(value=entry_aterro_tempo.get())
    valor_corte_tempo = tk.StringVar(value=entry_corte_tempo.get())
    valor_carga_tempo = tk.StringVar(value=entry_carga_tempo.get())
    valor_descarga_tempo = tk.StringVar(value=entry_descarga_tempo.get())
    valor_forma_tempo = tk.StringVar(value=entry_forma_tempo.get())
    

    # Função para aplicar as alterações
    def aplicar_custos():
        try:
            # Validar os valores - MATERIAIS
            custos_mat = [
                float(valor_concreto_25_mat.get()),
                float(valor_concreto_6_mat.get()),
                float(valor_aco_ca50_mat.get()),
                float(valor_forma_mat.get()),
                float(valor_aterro_mat.get()),
                float(valor_corte_mat.get()),
                float(valor_carga_mat.get()),
                float(valor_descarga_mat.get())
            ]
            
            # Validar os valores - MÃO DE OBRA
            custos_mdo = [
                float(valor_concreto_25_mdo.get()),
                float(valor_concreto_6_mdo.get()),
                float(valor_aco_ca50_mdo.get()),
                float(valor_aterro_mdo.get()),
                float(valor_corte_mdo.get()),
                float(valor_carga_mdo.get()),
                float(valor_descarga_mdo.get()),
                float(valor_forma_mdo.get())
            ]

            # Validar os valores - TEMPO
            custos_tempo = [
                float(valor_concreto_25_tempo.get()),
                float(valor_concreto_6_tempo.get()),
                float(valor_aco_ca50_tempo.get()),
                float(valor_aterro_tempo.get()),
                float(valor_corte_tempo.get()),
                float(valor_carga_tempo.get()),
                float(valor_descarga_tempo.get()),
                float(valor_forma_tempo.get())
            ]
            
            valores = [custos_mat, custos_mdo, custos_tempo]
            
            # Verificar se os valores são positivos
            if any(custo < 0 for custo in custos_mat + custos_mdo):
                messagebox.showerror("Erro", "Os custos devem ser valores positivos.")
                return
                
            # Atualizar os valores nos campos da interface principal - MATERIAIS
            entry_concreto_25_mat.delete(0, tk.END)
            entry_concreto_25_mat.insert(0, str(valores[0][0]))
            entry_concreto_25_mdo.delete(0, tk.END)
            entry_concreto_25_mdo.insert(0, str(valores[0][1]))
            
            entry_concreto_6_mat.delete(0, tk.END)
            entry_concreto_6_mat.insert(0, str(valores[1][0]))
            entry_concreto_6_mdo.delete(0, tk.END)
            entry_concreto_6_mdo.insert(0, str(valores[1][1]))
            
            entry_aco_ca50_mat.delete(0, tk.END)
            entry_aco_ca50_mat.insert(0, str(valores[2][0]))
            entry_aco_ca50_mdo.delete(0, tk.END)
            entry_aco_ca50_mdo.insert(0, str(valores[2][1]))
            
            entry_forma_mat.delete(0, tk.END)
            entry_forma_mat.insert(0, str(valores[3][0]))
            entry_forma_mdo.delete(0, tk.END)
            entry_forma_mdo.insert(0, str(valores[3][1]))
            
            entry_aterro_mdo.delete(0, tk.END)
            entry_aterro_mdo.insert(0, str(valores[4][1]))
            entry_aterro_mat.delete(0, tk.END)
            entry_aterro_mat.insert(0, str(valores[4][0]))
            
            entry_corte_mdo.delete(0, tk.END)
            entry_corte_mdo.insert(0, str(valores[5][1]))
            entry_corte_mat.delete(0, tk.END)
            entry_corte_mat.insert(0, str(valores[5][0]))

            entry_carga_mdo.delete(0, tk.END)
            entry_carga_mdo.insert(0, str(valores[6][1]))
            entry_carga_mat.delete(0, tk.END)
            entry_carga_mat.insert(0, str(valores[6][0]))

            entry_descarga_mdo.delete(0, tk.END)
            entry_descarga_mdo.insert(0, str(valores[7][1]))
            entry_descarga_mat.delete(0, tk.END)
            entry_descarga_mat.insert(0, str(valores[7][0]))
            
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
        aterro = float(entry_aterro_mdo.get())
        corte = float(entry_corte_mdo.get())
        carga = float(entry_carga_mdo.get())
        descarga = float(entry_descarga_mdo.get())
        forma = float(entry_forma_mat.get())+float(entry_forma_mdo.get())
        
        texto = (
            f"Concreto Estrutural: R${conc_25:.2f}/m³\n"
            f"Concreto Massa: R${conc_6:.2f}/m³\n"
            f"Aço: R${aco:.2f}/kg\n"
            f"Aterro: R${aterro:.2f}/m³\n"
            f"Corte: R${corte:.2f}/m³\n"
            f"Carga: R${carga:.2f}/m³\n"
            f"Descarga: R${descarga:.2f}/m³\n"
            f"Forma: R${forma:.2f}/m²"
        )
        label_info_custos.config(text=texto)
    except:
        label_info_custos.config(text="Clique para editar custos") 

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
entry_gamma_solo = tk.Entry(root)
entry_gamma_solo.insert(0, "18")  # Valor default
entry_gamma_solo.grid(row=2, column=1)

tk.Label(root, text="Peso específico do solo submerso (kN/m³):").grid(row=3, column=0)
entry_gamma_solo_sub = tk.Entry(root)
entry_gamma_solo_sub.insert(0, "10")  # Valor default
entry_gamma_solo_sub.grid(row=3, column=1)

tk.Label(root, text="Ângulo de atrito do aterro (graus):").grid(row=4, column=0)
entry_phi_aterro = tk.Entry(root)
entry_phi_aterro.insert(0, "30")  # Valor default
entry_phi_aterro.grid(row=4, column=1)

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



# Criar um frame para o botão e informações de custo
frame_custos = tk.Frame(root)
frame_custos.grid(row=21, column=2, pady=10, padx=10, sticky="nw")

# Botão para editar custos
btn_editar_custos = tk.Button(frame_custos, text="Editar Custos de Materiais", command=editar_custos_popup)
btn_editar_custos.pack(pady=5)

# Label para mostrar informações resumidas sobre custos
label_info_custos = tk.Label(frame_custos, text="Clique para editar custos", wraplength=200)
label_info_custos.pack(pady=5)

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
entry_nivel_agua.insert(0, "0")  # Valor default
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
entry_coesao.insert(0, "100")  # Valor default
entry_coesao.grid(row=6, column=7)

tk.Label(root, text="Ângulo de Atrito (graus):").grid(row=7, column=6)
entry_phi_estabilidade = tk.Entry(root)
entry_phi_estabilidade.insert(0, "30")  # Valor default
entry_phi_estabilidade.grid(row=7, column=7)


# Novo campo para fator de segurança de coesão
# k.Label(root, text="Fator Seg. Coesão:").grid(row=7, column=6)
entry_fs_coesao = tk.Entry(root)
entry_fs_coesao.insert(0, "4")  # Valor default
entry_fs_coesao.grid_remove()  # Ocultar o campo
# entry_fs_coesao.grid(row=7, column=7)


# Novo campo para fator de segurança de atrito
# tk.Label(root, text="Fator Seg. Atrito:").grid(row=8, column=6)
entry_fs_atrito = tk.Entry(root)
entry_fs_atrito.insert(0, "2")  # Valor default
entry_fs_atrito.grid_remove()  # Ocultar o campo
# entry_fs_atrito.grid(row=8, column=7)


# ---------------------------------------------------------------- #
# ------------------- Muro de Flexão ----------------------------- #
# ---------------------------------------------------------------- #

# Botão para calcular
btn_calcular = tk.Button(root, text="Calcular", command=calcular)
btn_calcular.grid(row=21, column=0)

btn_calcular = tk.Button(root, text="Exibir muro de flexão", command=botao_plotar_muro_arrimo)
btn_calcular.grid(row=21, column=1)

# Adicione este botão na interface gráfica
btn_gravidade = tk.Button(root, text="Exibir Muro de Gravidade", 
                        command=lambda: exibir_muro_gravidade_popup())
btn_gravidade.grid(row=21, column=4, padx=10, pady=5)

# Adicionar o botão na interface principal
btn_diagramas_gravidade = tk.Button(root, text="Exibir Diagramas Detalhados", 
                         command=exibir_diagramas_gravidade_popup)
btn_diagramas_gravidade.grid(row=21, column=3, padx=10, pady=5)

# Labels para exibir os quantitativos gerados
tk.Label(root, text="Quantitativos Gerados:", font=("Arial", 12)).grid(row=9, column=0)
tk.Label(root, text="Flexão - Quant.:", font=("Arial", 10)).grid(row=9, column=1)
tk.Label(root, text="Total (R$):", font=("Arial", 12)).grid(row=9, column=2)

# Campos de texto não editáveis para os quantitativos
tk.Label(root, text="Concreto Estrutural (m³):").grid(row=10, column=0)
label_concreto_25 = tk.Label(root, text="0.00")  # Valor padrão
label_concreto_25.grid(row=10, column=1)

label_total_concreto_25 = tk.Label(root, text="0.00")  # Valor padrão
label_total_concreto_25.grid(row=10, column=2)

tk.Label(root, text="Concreto Massa (m³):").grid(row=11, column=0)
label_concreto_6 = tk.Label(root, text="0.00")  # Valor padrão
label_concreto_6.grid(row=11, column=1)

label_total_concreto_6 = tk.Label(root, text="0.00")  # Valor padrão
label_total_concreto_6.grid(row=11, column=2)

tk.Label(root, text="Aço CA50 (kg):").grid(row=12, column=0)
label_aco_ca50 = tk.Label(root, text="0.00")  # Valor padrão
label_aco_ca50.grid(row=12, column=1)

label_total_aco_ca50 = tk.Label(root, text="0.00")  # Valor padrão
label_total_aco_ca50.grid(row=12, column=2)

tk.Label(root, text="Solo - Aterro (m³):").grid(row=13, column=0)
label_aterro = tk.Label(root, text="0.00")  # Valor padrão
label_aterro.grid(row=13, column=1)

label_total_aterro = tk.Label(root, text="0.00")  # Valor padrão
label_total_aterro.grid(row=13, column=2)

# Labels para os novos custos
tk.Label(root, text="Solo - Corte (m³):").grid(row=14, column=0)
label_corte = tk.Label(root, text="0.00")  # Valor padrão
label_corte.grid(row=14, column=1)

label_total_corte = tk.Label(root, text="0.00")  # Valor padrão
label_total_corte.grid(row=14, column=2)

tk.Label(root, text="Solo - Carga (m³):").grid(row=15, column=0)
label_carga = tk.Label(root, text="0.00")  # Valor padrão
label_carga.grid(row=15, column=1)

label_total_carga = tk.Label(root, text="0.00")  # Valor padrão
label_total_carga.grid(row=15, column=2)

tk.Label(root, text="Solo - Descarga (m³):").grid(row=16, column=0)
label_descarga = tk.Label(root, text="0.00")  # Valor padrão
label_descarga.grid(row=16, column=1)

label_total_descarga = tk.Label(root, text="0.00")  # Valor padrão
label_total_descarga.grid(row=16, column=2)

tk.Label(root, text="Área de fôrma:").grid(row=17, column=0)
label_forma = tk.Label(root, text="0.00")  # Valor padrão
label_forma.grid(row=17, column=1)

label_total_forma = tk.Label(root, text="0.00")  # Valor padrão
label_total_forma.grid(row=17, column=2)

tk.Label(root, text="Tempo Total:").grid(row=18, column=0)
label_tempo_total = tk.Label(root, text="0.00")  # Valor padrão
label_tempo_total.grid(row=18, column=1)

tk.Label(root, text="Soma (R$):").grid(row=19, column=0)
label_total_total = tk.Label(root, text="0.00")  # Valor padrão
label_total_total.grid(row=19, column=2)

tk.Label(root, text="Estável?").grid(row=20, column=0)
label_estavel_flexao = tk.Label(root, text="Calcular")  # Valor padrão
label_estavel_flexao.grid(row=20, column=2)

label_estavel_gravidade = tk.Label(root, text="Calcular")  # Valor padrão
label_estavel_gravidade.grid(row=20, column=4)


# ---------------------------------------------------------------- #
# ------------------ Muro de Gravidade --------------------------- #
# ---------------------------------------------------------------- #

# Seção Muro de Gravidade (colunas 3-4)
tk.Label(root, text="Gravidade - Quant.:", font=("Arial", 10)).grid(row=9, column=3)

# Cabeçalhos
tk.Label(root, text="Total (R$):", font=("Arial", 12)).grid(row=9, column=4)

# ---------------------------------------------------------------- #
# ------------------------- INTERFACE ---------------------------- #
# ---------------------------------------------------------------- #

# Campos de texto não editáveis para os quantitativos
label_concreto_25_grav = tk.Label(root, text="0.00")  # Valor padrão
label_concreto_25_grav.grid(row=10, column=3)

label_total_concreto_25_grav = tk.Label(root, text="0.00")  # Valor padrão
label_total_concreto_25_grav.grid(row=10, column=4)

label_concreto_6_grav = tk.Label(root, text="0.00")  # Valor padrão
label_concreto_6_grav.grid(row=11, column=3)

label_total_concreto_6_grav = tk.Label(root, text="0.00")  # Valor padrão
label_total_concreto_6_grav.grid(row=11, column=4)

label_aco_ca50_grav = tk.Label(root, text="0.00")  # Valor padrão
label_aco_ca50_grav.grid(row=12, column=3)

label_total_aco_ca50_grav = tk.Label(root, text="0.00")  # Valor padrão
label_total_aco_ca50_grav.grid(row=12, column=4)


label_aterro_grav = tk.Label(root, text="0.00")  # Valor padrão
label_aterro_grav.grid(row=13, column=3)

label_total_aterro_grav = tk.Label(root, text="0.00")  # Valor padrão
label_total_aterro_grav.grid(row=13, column=4)

label_corte_grav = tk.Label(root, text="0.00")  # Valor padrão
label_corte_grav.grid(row=14, column=3)

label_total_corte_grav = tk.Label(root, text="0.00")  # Valor padrão
label_total_corte_grav.grid(row=14, column=4)

label_carga_grav = tk.Label(root, text="0.00")  # Valor padrão
label_carga_grav.grid(row=15, column=3)

label_total_carga_grav = tk.Label(root, text="0.00")  # Valor padrão
label_total_carga_grav.grid(row=15, column=4)

label_descarga_grav = tk.Label(root, text="0.00")  # Valor padrão
label_descarga_grav.grid(row=16, column=3)

label_total_descarga_grav = tk.Label(root, text="0.00")  # Valor padrão
label_total_descarga_grav.grid(row=16, column=4)

label_forma_grav = tk.Label(root, text="0.00")  # Valor padrão
label_forma_grav.grid(row=17, column=3)

label_total_forma_grav = tk.Label(root, text="0.00")  # Valor padrão
label_total_forma_grav.grid(row=17, column=4)

label_total_total_grav = tk.Label(root, text="0.00")  # Valor padrão
label_total_total_grav.grid(row=18, column=4)


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