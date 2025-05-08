# testes
import math

def verificar_estabilidade_flexao(h, d, b_jus, b_mon, gamma_solo, phi_estabilidade, gamma_concreto, nivel_agua, coef_empuxo, pressao_adm, c, fs_coesao, fs_atrito, base_max=None):
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
    coef_empuxo: coeficiente de empuxo ativo (K)
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
    
    # Cálculo do empuxo ativo
    ka = coef_empuxo  # Coeficiente de empuxo ativo
    ea = 0.5 * gamma_solo * h**2 * ka  # Empuxo ativo total
    
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
    fs_deslizamento_total = (resistencia_coesao / (ea * fs_coesao)) + (resistencia_atrito / (ea * fs_atrito))
    
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
    braco_ea = h / 3  # Ponto de aplicação do empuxo ativo em y = h/3 a partir da base
    mt = ea * braco_ea
    
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
    fs_deslizamento_ok = fs_deslizamento_total >= 1.0  # Valor mínimo recomendado pela NBR 11682 <- Já está incorporado no cálculo
    
    # Cálculo da base teórica necessária
    # Considerando os critérios de estabilidade:
    # 1. Tensão máxima <= pressão admissível
    # 2. Fator de segurança contra tombamento >= 1.5
    # 3. Fator de segurança contra deslizamento >= 1.0
    
    # Base teórica para satisfazer pressão admissível
    # Aproximação: a tensão máxima é inversamente proporcional à largura da base
    base_teorica_pressao = b_total * (tensao_max / pressao_adm) if pressao_adm > 0 else b_total
    
    # Base teórica para satisfazer fator de segurança contra tombamento
    base_teorica_tombamento = b_total * (1.5 / fs_tombamento) if fs_tombamento > 0 else b_total * 1.5
    
    # Base teórica para satisfazer fator de segurança contra deslizamento
    base_teorica_deslizamento = b_total * (1.0 / fs_deslizamento_total) if fs_deslizamento_total > 0 else b_total
    
    # Base teórica necessária é o maior valor dentre os três critérios
    base_teorica = max(base_teorica_pressao, base_teorica_tombamento, base_teorica_deslizamento)
    
    # Verificação se a base teórica é menor que a base máxima permitida
    base_ok = True
    base_atual_ok = True
    
    # Verificar se a base atual é suficiente
    base_atual_ok = base_teorica <= b_total
    
    # Verificar se a base teórica é menor que a base máxima permitida
    if base_max is not None:
        base_max_ok = base_teorica <= base_max
        # A base só está OK se atende ambos os critérios
        base_ok = base_atual_ok and base_max_ok
    else:
        base_ok = base_atual_ok
    
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

print(verificar_estabilidade_flexao(3, 0.25, 0.8, 1.3, 18, 32, 25, 0, 0.307, 200, 0, 4, 2, 3))
