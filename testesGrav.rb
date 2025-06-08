def testar_muro_gravidade():
    """
    Função para testar os cálculos do muro de gravidade com exemplos calculados manualmente
    """
    # Teste 1: Muro simples sem água
    h = 3.0  # altura
    crista = 0.3  # largura da crista
    b_mon = 1.5  # largura da base
    gamma_concreto = 24  # peso específico do concreto
    gamma_solo_sat = 18  # peso específico do solo saturado
    gamma_solo_sub = 10  # peso específico do solo submerso
    phi = 30  # ângulo de atrito
    c = 10  # coesão
    pressao_adm = 200  # pressão admissível
    nivel_agua = 0  # nível d'água
    fs_coesao = 4  # fator de segurança à coesão
    fs_atrito = 2  # fator de segurança ao atrito
    k0 = 0.5  # coeficiente de empuxo em repouso
    gamma_agua = 10  # peso específico da água
    sobrecarga_mon = 0  # sobrecarga a montante
    inclinacao = "montante"  # inclinação do muro

    # Cálculos manuais esperados:
    # Peso do muro:
    peso_muro_1 = 0.5 * (b_mon - crista) * h * gamma_concreto  # Parte triangular
    peso_muro_2 = crista * h * gamma_concreto  # Parte retangular
    peso_muro_esperado = peso_muro_1 + peso_muro_2

    # Empuxo do solo:
    e0_solo_esperado = 0.5 * gamma_solo_sat * h**2 * k0

    # Teste 2: Muro com água
    h2 = 4.0
    nivel_agua2 = 2.0
    b_mon2 = 2.0
    crista2 = 0.4

    # Cálculos manuais esperados com água:
    # Empuxo da água:
    e0_agua_esperado = 0.5 * gamma_agua * nivel_agua2**2

    # Empuxo do solo saturado:
    e0_solo_sat_esperado = 0.5 * gamma_solo_sat * (h2-nivel_agua2)**2 * k0

    # Empuxo do solo submerso:
    e0_solo_sub_esperado = 0.5 * gamma_solo_sub * nivel_agua2**2 * k0

    print("Teste 1 - Muro sem água:")
    print(f"Peso do muro esperado: {peso_muro_esperado:.2f} kN/m")
    print(f"Empuxo do solo esperado: {e0_solo_esperado:.2f} kN/m")
    print("\nTeste 2 - Muro com água:")
    print(f"Empuxo da água esperado: {e0_agua_esperado:.2f} kN/m")
    print(f"Empuxo do solo saturado esperado: {e0_solo_sat_esperado:.2f} kN/m")
    print(f"Empuxo do solo submerso esperado: {e0_solo_sub_esperado:.2f} kN/m")

def testar_muro_flexao():
    """
    Função para testar os cálculos do muro de flexão com exemplos calculados manualmente
    """
    # Teste 1: Muro simples
    h = 3.0  # altura
    d = 0.3  # espessura
    gamma_concreto = 24  # peso específico do concreto
    gamma_solo = 18  # peso específico do solo
    phi = 30  # ângulo de atrito
    c = 10  # coesão
    ka = 0.33  # coeficiente de empuxo ativo

    # Cálculos manuais esperados:
    # Peso do muro:
    peso_muro_esperado = h * d * gamma_concreto

    # Empuxo ativo:
    e0_esperado = 0.5 * gamma_solo * h**2 * ka

    # Momento fletor:
    momento_esperado = e0_esperado * h/3

    print("\nTeste Muro de Flexão:")
    print(f"Peso do muro esperado: {peso_muro_esperado:.2f} kN/m")
    print(f"Empuxo ativo esperado: {e0_esperado:.2f} kN/m")
    print(f"Momento fletor esperado: {momento_esperado:.2f} kN.m/m")

# Executar os testes
if __name__ == "__main__":
    testar_muro_gravidade()
    testar_muro_flexao()
