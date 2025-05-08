import math
def calcular_muro_gravidade(h, crista, b_mon, b_jus, gamma_concreto, gamma_solo, phi, c, pressao_adm, sobrecarga_mon, nivel_agua=0, fs_coesao=4, fs_atrito=2, k0=0.5, base_max=None, gamma_agua=10):
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
    sobrecarga_mon: sobrecarga no solo a montante (kN/m²)
    """

    b_total = b_mon + b_jus

    # 1. Cálculos geométricos e de peso
    area_muro = 0.5 * (b_total - crista) * h + crista * h
    volume_concreto = area_muro
    peso_muro = volume_concreto * gamma_concreto
    peso_solo = 0.5 * (b_mon - crista) * h * gamma_solo
    
    print(peso_muro)

    # 2. Cálculo dos empuxos
    h_sobrecarga = sobrecarga_mon/gamma_solo
    h_total = h + h_sobrecarga
    e0 = 0.5 * gamma_solo * (h_total**2 - h_sobrecarga**2) * k0  # Empuxo em repouso
    e0_agua = 0.5 * gamma_agua * nivel_agua**2
    empuxo_total = e0 + e0_agua

    print(empuxo_total)

    # 3. Verificação ao Deslizamento
    fs_deslizamento = c * b_total / (empuxo_total * fs_coesao) + (peso_muro + peso_solo)*math.tan(math.radians(phi)) / (empuxo_total * fs_atrito)

    print(fs_deslizamento)

    fs_deslizamento_ok = fs_deslizamento >= 1.0  # Valor mínimo recomendado pela NBR 11682 <- Já está incorporado no cálculo

    # 4. Verificação ao Tombamento
    braco_estabilizante_pt = (crista**2 + (b_total * crista) + b_total**2) / (3 * (b_total + crista)) # Em relação ao ponto de tombamento
    terra_estabilizante_pt = (b_mon - crista)*2/3 + crista    # Em relação ao ponto de tombamento
    braco_tombamento_pt = h/3
    fs_tombamento = (peso_muro*braco_estabilizante_pt + peso_solo*terra_estabilizante_pt) / (empuxo_total*braco_tombamento_pt)
    fs_tombamento_ok = fs_tombamento >= 1.5  # Valor para caso de carregamento normal ELETROBRAS 2003

    momento_estabilizante = peso_muro*braco_estabilizante_pt + peso_solo*terra_estabilizante_pt
    momento_tombamento = empuxo_total*braco_tombamento_pt

    print(braco_estabilizante_pt)

    print(momento_estabilizante, momento_tombamento)

    # 5. Verificação de Tensões na Base
    x_cg = b_total/2
    y_cg = h/3 * (2*crista + b_total)/(crista + b_total)
    braco_estabilizante_cg = braco_estabilizante_pt - x_cg # Em relação ao centro da base
    terra_estabilizante_cg = ((b_mon - crista)*2/3 + crista) - x_cg    # Em relação ao centro da base
    braco_tombamento = h/3

    excentricidade = (b_total)/2 - ((peso_muro*braco_estabilizante_cg + peso_solo*terra_estabilizante_cg) - e0*braco_tombamento)/(peso_muro + peso_solo)
    momento_inercia = (1/6)*b_total**2
    peso_total = peso_muro + peso_solo
    momento_total = peso_muro*braco_estabilizante_cg + peso_solo*terra_estabilizante_cg - e0*braco_tombamento
    tensao_max = peso_total/b_total + abs(momento_total/momento_inercia)
    tensao_min = peso_total/b_total - abs(momento_total/momento_inercia)

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
    base_teorica_pressao = b_total * (tensao_max / pressao_adm) if pressao_adm > 0 else b_total
    
    # Base teórica para satisfazer fator de segurança contra tombamento
    base_teorica_tombamento = b_total * (1.5 / fs_tombamento) if fs_tombamento > 0 else b_total * 1.5
    
    # Base teórica para satisfazer fator de segurança contra deslizamento
    base_teorica_deslizamento = b_total * (1.0 / fs_deslizamento) if fs_deslizamento > 0 else b_total
    
    # Base teórica necessária é o maior valor dentre os três critérios
    base_teorica = max(base_teorica_pressao, base_teorica_tombamento, base_teorica_deslizamento)
    
    # Verificação se a base teórica é menor que a base máxima permitida
    base_atual_ok = base_teorica <= b_total
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


print(calcular_muro_gravidade(h=5, crista=0.7, b_mon=0, b_jus=2.5, gamma_concreto=22, gamma_solo=16, phi=30, c=0, pressao_adm=200, sobrecarga_mon=4, nivel_agua=0, fs_coesao=4, fs_atrito=1.5, k0=0.33, base_max=None, gamma_agua=10))