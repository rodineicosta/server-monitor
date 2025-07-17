#!/bin/bash
# Função para obter o diretório raiz do projeto
# Deve ser usado por todos os scripts para manter consistência

get_project_dir() {
    # Se executado diretamente da raiz
    if [ -f "monitor.sh" ] && [ -d "configs" ]; then
        echo "$(pwd)"
        return
    fi

    # Se executado de dentro de scripts/
    if [ -f "../monitor.sh" ] && [ -d "../configs" ]; then
        echo "$(cd .. && pwd)"
        return
    fi

    # Tentar encontrar pela estrutura de diretórios
    current_dir="$(pwd)"
    while [ "$current_dir" != "/" ]; do
        if [ -f "$current_dir/monitor.sh" ] && [ -d "$current_dir/configs" ]; then
            echo "$current_dir"
            return
        fi
        current_dir="$(dirname "$current_dir")"
    done

    echo "❌ Erro: Não foi possível encontrar o diretório do projeto!" >&2
    exit 1
}

# Função para configurar o ambiente do projeto
setup_project_env() {
    PROJECT_DIR="$(get_project_dir)"
    export PROJECT_DIR
    cd "$PROJECT_DIR"

    # Verificar se arquivos essenciais existem
    if [ ! -f "monitor.sh" ]; then
        echo "❌ Erro: monitor.sh não encontrado em $PROJECT_DIR" >&2
        exit 1
    fi

    if [ ! -d "configs" ]; then
        echo "❌ Erro: diretório configs não encontrado em $PROJECT_DIR" >&2
        exit 1
    fi
}
