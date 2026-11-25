import os
import shutil
from html import escape
from io import BytesIO
import requests
from PIL import Image, ImageOps
from ascii_magic import AsciiArt
import time

pasta_imagens = "imagens"
extensoes_aceitas = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
imagem_carregada = None
largura_escolhida = None
caracteres_escolhidos = None
rodando = True
tempo_execucao = time.time()

def pegar_nome_aleatorio():
    endpoint = "https://random-word-api.herokuapp.com/word?lang=pt-br&diff=1"
    resposta = requests.get(endpoint)
    resposta.raise_for_status()
    return resposta.json()[0] or "abacate"

def ler_inteiro(texto):
    try:
        return int(input(texto))
    except ValueError:
        return None

def obter_largura():
    if largura_escolhida:
        return largura_escolhida
    return max(40, shutil.get_terminal_size((100, 30)).columns - 1)

def parametros_arte():
    return {
        "columns": obter_largura(),
        "char": caracteres_escolhidos,
    }

def preparar_imagem():
    return imagem_carregada.convert("RGB")

def criar_arte():
    return AsciiArt.from_pillow_image(preparar_imagem())

def gerar_html_colorido(texto_arte):
    linhas = texto_arte.split("\n")
    while linhas and not linhas[-1].strip():
        linhas.pop()
    largura = max(len(linha) for linha in linhas)
    img = preparar_imagem().resize((largura, len(linhas)), Image.BOX)
    pixels = img.load()

    def fechar(trecho, cor):
        trecho = escape(trecho)
        if cor:
            return f'<span style="color:{cor}">{trecho}</span>'
        return trecho

    saida = []
    for y, linha in enumerate(linhas):
        linha = linha.ljust(largura)
        partes = []
        cor_atual = None
        buffer = ""
        for x, caractere in enumerate(linha):
            if caractere == " ":
                buffer += caractere
                continue
            r, g, b = pixels[x, y]
            cor = f"#{round(r * 15 / 255):x}{round(g * 15 / 255):x}{round(b * 15 / 255):x}"
            if cor != cor_atual:
                if buffer:
                    partes.append(fechar(buffer, cor_atual))
                buffer = ""
                cor_atual = cor
            buffer += caractere
        if buffer:
            partes.append(fechar(buffer, cor_atual))
        saida.append("".join(partes))

    return '<pre style="font-family:monospace;line-height:1">' + "\n".join(saida) + "</pre>"

def carregar_imagem():
    global imagem_carregada
    opcao = ler_inteiro("1- Carregar imagem on-line\n2- Mostrar opções na pasta imagens\n> ")
    if opcao == 1:
        link = input("Insira o link da imagem: ").strip()
        try:
            resposta = requests.get(link, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            resposta.raise_for_status()
            imagem_carregada = Image.open(BytesIO(resposta.content)).convert("RGB")
            print("O endpoint carregou a imagem!")
        except (requests.RequestException, OSError) as erro:
            print(f"Erro: {erro}")

    elif opcao == 2:
        os.makedirs(pasta_imagens, exist_ok=True)
        arquivos = [f for f in sorted(os.listdir(pasta_imagens)) if f.lower().endswith(extensoes_aceitas)]
        if not arquivos:
            print(f"não foi achado nenhuma imagem na pasta '{pasta_imagens}'.")
            return

        for i, nome in enumerate(arquivos, start=1):
            print(f"{i}- {nome}")
        escolha = ler_inteiro("Escolha o número da imagem: ")
        if escolha is None or not 1 <= escolha <= len(arquivos):
            print("Inválido.")
            return

        caminho = os.path.join(pasta_imagens, arquivos[escolha - 1])
        try:
            imagem_carregada = Image.open(caminho).convert("RGB")
            print("Imagem carregada com sucesso!")
        except OSError as erro:
            print(f"Erro ao abrir a imagem: {erro}")

    else:
        print("Erro ao escolher a opção.")

def salvar_imagem():
    if imagem_carregada is None:
        print("Nenhuma imagem carregada ainda!")
        return

    formato = ler_inteiro("1- Salvar como .txt\n2- Salvar como .md (preto e branco)\n3- Salvar como .md colorido\n")
    if formato not in (1, 2, 3):
        print("Opção inválida.")
        return

    os.makedirs(pasta_imagens, exist_ok=True)
    nome = input("Nome do arquivo: ").strip() or pegar_nome_aleatorio()
    extensao = ".txt" if formato == 1 else ".md"
    caminho = os.path.join(pasta_imagens, nome + extensao)
    arte = criar_arte()

    texto = arte.to_ascii(monochrome=True, **parametros_arte())
    if formato == 3:
        texto = f"# {nome}\n\n{gerar_html_colorido(texto)}\n"
    elif formato == 2:
        texto = f"# {nome}\n\n```\n{texto}\n```\n"
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    print(f"Foi salvo na pasta de imagens {caminho}")

def inverter():
    global imagem_carregada
    if imagem_carregada is None:
        print("Nenhuma imagem carregada.")
        return
    opcao = ler_inteiro("1- Inverter horizontalmente\n2- Inverter verticalmente\n")
    if opcao == 1:
        imagem_carregada = ImageOps.mirror(imagem_carregada)
        print("Imagem invertida horizontalmente!")
    elif opcao == 2:
        imagem_carregada = ImageOps.flip(imagem_carregada)
        print("Imagem invertida verticalmente!")
    else:
        print("Opção inválida.")
        return
    mostrar_ascii()

def gerar_ansi_colorido(texto_arte):
    linhas = texto_arte.split("\n")
    while linhas and not linhas[-1].strip():
        linhas.pop()
    largura = max(len(linha) for linha in linhas)
    img = preparar_imagem().resize((largura, len(linhas)), Image.BOX)
    pixels = img.load()

    saida = []
    for y, linha in enumerate(linhas):
        partes = []
        cor_atual = None
        for x, caractere in enumerate(linha):
            if caractere == " ":
                partes.append(caractere)
                continue
            cor = pixels[x, y]
            if cor != cor_atual:
                partes.append(f"\x1b[38;2;{cor[0]};{cor[1]};{cor[2]}m")
                cor_atual = cor
            partes.append(caractere)
        partes.append("\x1b[0m")
        saida.append("".join(partes))

    return "\n".join(saida)

def mostrar_ascii():
    arte = criar_arte()
    texto = arte.to_ascii(monochrome=True, **parametros_arte())
    print(gerar_ansi_colorido(texto))

def colorido():
    if imagem_carregada is None:
        print("Nenhuma imagem carregada...")
        return
    mostrar_ascii()

def ajustar_largura():
    global largura_escolhida
    print(f"Largura atual: {obter_largura()} colunas")
    valor = ler_inteiro("Nova largura (40 a 300, ou 0 para automática): ")
    if valor == 0:
        largura_escolhida = None
        print("Foi setado como automático")
    elif valor is not None and 40 <= valor <= 300:
        largura_escolhida = valor
        print(f"Largura definida para {valor} colunas.")
    else:
        print("Valor inválido.")

def escolher_caracteres():
    global caracteres_escolhidos
    opcao = ler_inteiro(
        "1- Padrão\n2- Detalhado ( .:-=+*#%@)\n3- Blocos ( ░▒▓█)\n4- Personalizado\n"
    )
    if opcao == 1:
        caracteres_escolhidos = None
        print("padrão da biblioteca")
    elif opcao == 2:
        caracteres_escolhidos = " .:-=+*#%@"
        print("caracteres melhorados")
    elif opcao == 3:
        caracteres_escolhidos = " ░▒▓█"
        print("caracteres em blocos")
    elif opcao == 4:
        digitados = input("digite os caracteres do mais claro ao mais escuro: ")
        if digitados:
            caracteres_escolhidos = digitados
            print("Foi atualizado!.")
        else:
            print("Nada foi digitado...")
    else:
        print("Opção inválida.")

def sair():
    global rodando
    rodando = False

while rodando:
    print("---\n1- Carregar imagem\n2- Salvar imagem\n3- Inverter\n4- Mostrar colorido""\n5- Ajustar largura\n6- Escolher caracteres\n7- Sair\n---")
    print("ps : sempre bom dar um zoom no terminal")
    opcao = ler_inteiro("Selecione uma opção: ")
    match opcao:
        case 1:
            carregar_imagem()
        case 2:
            salvar_imagem()
        case 3:
            inverter()
        case 4:
            colorido()
        case 5:
            ajustar_largura()
        case 6:
            escolher_caracteres()
        case 7:
            sair()
        case _:
            print("Opção inválida.")

print("Até!")
print(f"O programa rodou por {time.time() - tempo_execucao}")