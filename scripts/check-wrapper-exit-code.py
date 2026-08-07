#!/usr/bin/env python3
"""check-wrapper-exit-code.py <skill_root>

Falha quando um wrapper de skill LANCA um processo filho e JOGA FORA o
resultado — nem captura o retorno, nem usa check=True.

Por que isso e um defeito e nao um detalhe de estilo: o wrapper e o que o bot
executa. Se ele descarta o returncode do filho, sai 0 mesmo com a skill
quebrada, e a falha chega ao agente como sucesso. Foi exatamente isso em
agosto/2026 em cinco skills da org (crypto-assets-analytics, crypto-divergence-rsi,
funding-rate-monitor, squeeze-monitor, daily-briefing): analise sem dado nenhum
reportada como execucao bem-sucedida, por meses, sem sinal em log nem em alerta.

O checker usa AST, nao regex: a pergunta "o resultado foi descartado?" e
estrutural (o `Call` e filho direto de um `Expr`), e regex sobre codigo produz
falso-positivo — a org ja pagou por detector fragil duas vezes (#100, #113).

Formas ACEITAS (nao acusa):
    result = subprocess.run(...)          # capturado: da pra inspecionar/propagar
    subprocess.run(..., check=True)       # levanta sozinho se falhar
    return subprocess.run(...)            # quem chamou decide
    sys.exit(subprocess.run(...).returncode)
    subprocess.run(...)  # exit-code-ok: <motivo>   <- escape hatch consciente

Forma ACUSADA:
    subprocess.run([...], check=False)    # resultado no lixo, exit code perdido
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

# So estas descartam a falha em silencio: devolvem o returncode e seguem.
LANCADORES = {"run", "call"}

# Estas levantam CalledProcessError sozinhas — a checagem esta no NOME, nao num
# kwarg `check=True`. Nunca sao violacao. (Sem isso o checker acusaria o
# skill-delta-neutral-nado-kraken, que esta correto.)
SEMPRE_CHECADOS = {"check_call", "check_output"}

# `Popen` fica DE FORA de proposito: lancamento assincrono e outro padrao —
# descartar o objeto pode ser intencional. Um checker barulhento e pior que
# um estreito, e a org ja tem historico de detector em falso-positivo.

MARCADOR_OPTOUT = "exit-code-ok"

# Convencao de nome de wrapper na org. O `entry` do skill.json entra tambem,
# quando aponta para .py — e o arquivo que o bot de fato executa.
NOMES_DE_WRAPPER = {"run.py", "run_skill.py", "wrapper.py", "entrypoint.py"}

IGNORAR_DIRS = {".venv", "venv", "node_modules", ".git", "__pycache__", ".skill-ci"}


def alvos(root: Path) -> list[Path]:
    """Wrappers a conferir: o `entry` do skill.json (se .py) + convencao de nome."""
    encontrados: list[Path] = []

    skill_json = root / "skill.json"
    if skill_json.is_file():
        try:
            entry = json.loads(skill_json.read_text(encoding="utf-8")).get("entry", "")
        except (json.JSONDecodeError, OSError):
            entry = ""  # check-structure ja reprova skill.json invalido
        if isinstance(entry, str) and entry.endswith(".py"):
            caminho = root / entry
            if caminho.is_file():
                encontrados.append(caminho)

    for caminho in root.rglob("*.py"):
        if any(parte in IGNORAR_DIRS for parte in caminho.parts):
            continue
        if caminho.name in NOMES_DE_WRAPPER:
            encontrados.append(caminho)

    # dedup preservando ordem
    vistos, unicos = set(), []
    for c in encontrados:
        chave = c.resolve()
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(c)
    return unicos


def nomes_importados_de_subprocess(arvore: ast.Module) -> set[str]:
    """Pega `from subprocess import run, call` — chamada fica sem o prefixo."""
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom) and no.module == "subprocess":
            for alias in no.names:
                if alias.name in LANCADORES:
                    nomes.add(alias.asname or alias.name)
    return nomes


def e_lancamento_direto(no: ast.AST, importados: set[str]) -> bool:
    if not isinstance(no, ast.Call):
        return False
    alvo = no.func
    # subprocess.run(...)
    if isinstance(alvo, ast.Attribute) and alvo.attr in LANCADORES:
        return isinstance(alvo.value, ast.Name) and alvo.value.id == "subprocess"
    # run(...) importado direto
    return isinstance(alvo, ast.Name) and alvo.id in importados


def _corpo_sem_aninhadas(fn: ast.AST):
    """Nos da funcao, sem descer em funcoes aninhadas (evita atribuir a return
    de uma closure ao escopo de fora)."""
    for filho in ast.iter_child_nodes(fn):
        if isinstance(filho, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        yield filho
        yield from _corpo_sem_aninhadas(filho)


def helpers_que_lancam(arvore: ast.Module, importados: set[str]) -> set[str]:
    """Funcoes locais que DEVOLVEM um lancamento.

    Sem isso o checker tem ponto cego: uma indirecao de uma linha
    (`def roda(...): return subprocess.run(...)`) esconde o defeito. Foi o caso
    real do crypto-divergence-rsi, que passaria batido.
    """
    nomes: set[str] = set()
    for fn in ast.walk(arvore):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        corpo = list(_corpo_sem_aninhadas(fn))
        lancadas: set[str] = {
            t.id
            for no in corpo
            if isinstance(no, ast.Assign) and e_lancamento_direto(no.value, importados)
            for t in no.targets
            if isinstance(t, ast.Name)
        }
        for no in corpo:
            if not isinstance(no, ast.Return) or no.value is None:
                continue
            devolve_direto = e_lancamento_direto(no.value, importados)
            devolve_variavel = isinstance(no.value, ast.Name) and no.value.id in lancadas
            if devolve_direto or devolve_variavel:
                nomes.add(fn.name)
                break
    return nomes


def e_lancamento(no: ast.AST, importados: set[str], helpers: set[str]) -> bool:
    if e_lancamento_direto(no, importados):
        return True
    return (
        isinstance(no, ast.Call)
        and isinstance(no.func, ast.Name)
        and no.func.id in helpers
    )


def tem_check_true(no: ast.Call) -> bool:
    for kw in no.keywords:
        if kw.arg == "check" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return True
    return False


def analisar(caminho: Path, raiz: Path) -> tuple[int, list[str]]:
    fonte = caminho.read_text(encoding="utf-8", errors="replace")
    try:
        arvore = ast.parse(fonte, filename=str(caminho))
    except SyntaxError as e:
        # check-syntax.sh e quem reporta erro de sintaxe; aqui so nao da veredito.
        return 0, [f"::warning file={caminho}::nao foi possivel parsear ({e}); "
                   f"propagacao de exit code NAO verificada neste arquivo"]

    linhas = fonte.splitlines()
    importados = nomes_importados_de_subprocess(arvore)
    helpers = helpers_que_lancam(arvore, importados)
    conferidas, problemas = 0, []

    for no in ast.walk(arvore):
        # Resultado descartado == o Call e o corpo de um Expr statement.
        if not isinstance(no, ast.Expr) or not e_lancamento(no.value, importados, helpers):
            continue
        chamada = no.value
        conferidas += 1

        if tem_check_true(chamada):
            continue

        span = linhas[no.lineno - 1: (no.end_lineno or no.lineno)]
        if any(MARCADOR_OPTOUT in linha for linha in span):
            continue

        rel = caminho.relative_to(raiz).as_posix()
        problemas.append(
            f"::error file={rel},line={no.lineno}::Exit code descartado: o resultado "
            f"desta chamada nao e capturado nem ha check=True, entao a falha do "
            f"processo filho some. Capture o resultado e propague "
            f"(sys.exit(result.returncode)), use check=True, ou marque a linha com "
            f"'# {MARCADOR_OPTOUT}: <motivo>' se descartar for intencional."
        )

    return conferidas, problemas


# Cada fixture e (nome, codigo, deve_acusar). Um checker que para de detectar
# em silencio devolve o problema original — por isso ele se testa.
FIXTURES = [
    ("descartado", "import subprocess\nsubprocess.run(['x'])\n", True),
    ("descartado_check_false",
     "import subprocess\nsubprocess.run(['x'], check=False)\n", True),
    ("subprocess_call_descartado", "import subprocess\nsubprocess.call(['x'])\n", True),
    ("via_helper_de_uma_linha",
     "import subprocess\n"
     "def roda(a):\n    return subprocess.run(a)\n"
     "roda(['x'])\n", True),
    ("via_helper_com_variavel",
     "import subprocess\n"
     "def roda(a):\n    r = subprocess.run(a)\n    return r\n"
     "roda(['x'])\n", True),
    ("import_direto",
     "from subprocess import run\nrun(['x'])\n", True),
    ("capturado", "import subprocess\nr = subprocess.run(['x'])\n", False),
    ("check_true", "import subprocess\nsubprocess.run(['x'], check=True)\n", False),
    ("check_call_levanta_sozinho",
     "import subprocess\nsubprocess.check_call(['x'])\n", False),
    ("check_output_levanta_sozinho",
     "import subprocess\nsubprocess.check_output(['x'])\n", False),
    ("propagado_direto",
     "import subprocess, sys\nsys.exit(subprocess.run(['x']).returncode)\n", False),
    ("return_repassa_ao_chamador",
     "import subprocess\ndef roda(a):\n    return subprocess.run(a)\n", False),
    ("popen_fora_de_escopo", "import subprocess\nsubprocess.Popen(['x'])\n", False),
    ("optout_marcado",
     "import subprocess\nsubprocess.run(['x'])  # exit-code-ok: fire-and-forget\n", False),
    ("helper_aninhado_nao_contamina",
     "import subprocess\n"
     "def externa():\n    def interna():\n        return subprocess.run(['x'])\n"
     "    return 1\n"
     "externa()\n", False),
]


def self_test() -> int:
    import tempfile

    falhas = []
    for nome, codigo, deve_acusar in FIXTURES:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "run.py").write_text(codigo, encoding="utf-8")
            _, problemas = analisar(raiz / "run.py", raiz)
            acusou = any("::error" in p for p in problemas)
            if acusou != deve_acusar:
                esperado = "acusar" if deve_acusar else "aceitar"
                falhas.append(f"  {nome}: esperava {esperado}, fez o oposto")
            print(f"  [{'ok' if acusou == deve_acusar else 'FALHA'}] {nome}")

    if falhas:
        print("::error::self-test do checker falhou:")
        print("\n".join(falhas))
        return 1
    print(f"self-test: {len(FIXTURES)}/{len(FIXTURES)} fixtures OK")
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        return self_test()

    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    arquivos = alvos(raiz)

    if not arquivos:
        print("Wrapper exit code: nenhum wrapper Python encontrado (skill.json.entry "
              "nao e .py e nao ha run.py/run_skill.py) — nada a conferir.")
        return 0

    total, todos = 0, []
    for caminho in arquivos:
        conferidas, problemas = analisar(caminho, raiz)
        total += conferidas
        todos.extend(problemas)
        rel = caminho.relative_to(raiz).as_posix()
        status = "FALHA" if any("::error" in p for p in problemas) else "ok"
        print(f"  [{status}] {rel} — {conferidas} lancamento(s) sem captura do resultado")

    for problema in todos:
        print(problema)

    erros = [p for p in todos if "::error" in p]
    if erros:
        print(f"::error::{len(erros)} chamada(s) descartando exit code. "
              "Wrapper que engole falha do filho faz o bot tratar erro como sucesso.")
        return 1

    print(f"Wrapper exit code: OK — {len(arquivos)} arquivo(s) conferido(s); "
          f"{total} lancamento(s) sem captura, todos com check=True ou marcados "
          f"'{MARCADOR_OPTOUT}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
