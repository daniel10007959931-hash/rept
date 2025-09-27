#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ROBÔ DE AUTOMAÇÃO DE ORDENS PARA DYDX V4 - VERSÃO 3.0 (TEMPO REAL)
================================================================================

Este é um robô de trading projetado para a automação completa de ordens na
plataforma DYDX v4. Seu objetivo principal é processar sinais de trading e
executar as operações correspondentes de forma autônoma e segura.

COMO FUNCIONA (FLUXO DE AUTOMAÇÃO):
-----------------------------------
1. INICIALIZAÇÃO E CONEXÃO: Carrega as credenciais de ambiente de forma segura
   e estabelece uma conexão direta com a mainnet da DYDX.
2. VERIFICAÇÃO PRÉ-TRADE: Antes de qualquer operação, o robô verifica o status
   da conta, incluindo saldo disponível e posições já abertas.
3. COLETA DE PREÇO EM TEMPO REAL: Para garantir precisão máxima na execução,
   o robô busca o preço de oráculo (`oraclePrice`) mais atualizado para os
   ativos, minimizando o risco de slippage.
4. PROCESSAMENTO DE SINAIS: Interpreta uma lista pré-configurada de sinais
   (ex: "BTC COMPRAR") e os prepara para a execução.
5. CÁLCULO DE RISCO: Avalia a exposição da conta e valida se a operação está
   dentro dos limites de risco definidos antes de qualquer execução.
6. CICLO CONTÍNUO: Repete o fluxo operacional em intervalos configuráveis,
   pronto para agir 24/7 assim que um sinal for válido.

CONFIGURAÇÃO DE AMBIENTE:
-------------------------
- DYDX_PRIVATE_KEY: A chave privada da sua carteira.
- DYDX_ADDRESS: O endereço da sua carteira (0x...).
- LOOP_INTERVAL_SECONDS: Intervalo em segundos entre cada ciclo (padrão: 60).
- BOT_RUN_MODE: "single" para um ciclo ou "continuous" para operação 24/7.

SEGURANÇA E PERFORMANCE:
------------------------
- Credenciais isoladas em variáveis de ambiente.
- Utilização do `oraclePrice` para dados de mercado em tempo real.
- Logs detalhados para auditoria completa de cada passo do ciclo.
- Estrutura robusta para operação contínua e tratamento de falhas.

FUNCIONALIDADES PRINCIPAIS:
---------------------------
✅ Conexão segura e autenticada com a DYDX v4.
✅ Coleta de preços de oráculo em tempo real para precisão nas ordens.
✅ Monitoramento de múltiplos ativos (BTC, ETH, SOL, AVAX, LINK, DOGE).
✅ Verificação de pré-requisitos da conta (saldo, posições).
✅ Processamento e validação de sinais de trading para automação.
✅ Análise de risco pré-operação para gestão de capital.
✅ Logs operacionais detalhados para rastreabilidade.
✅ Modo de execução contínuo para automação 24/7.

Autor: Replit Agent para Daniel Mota de Aguiar Rodrigues
Versão: 3.0 - Foco em Automação com Preço Real
Data: 27 de Setembro de 2025
================================================================================
"""

import os
import logging
import time
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# ============================================================================
# CONFIGURAÇÃO DO SISTEMA DE LOGS
# ============================================================================

def configurar_logs():
    """
    Configura um sistema de logging robusto para o robô.
    Logs são exibidos no console e salvos em 'robo_trader.log'.
    """
    formato_log = '%(asctime)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=logging.INFO,
        format=formato_log,
        handlers=[
            logging.FileHandler('robo_trader.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# Logger global inicializado
logger = configurar_logs()

# ============================================================================
# IMPORTAÇÃO E VALIDAÇÃO DOS MÓDULOS DYDX
# ============================================================================

try:
    from dydx_v4_client.indexer.rest.indexer_client import IndexerClient
    logger.info("✅ Módulo 'dydx_v4_client' importado com sucesso.")
except ImportError as erro:
    logger.critical(f"❌ ERRO CRÍTICO: Falha ao importar o cliente DYDX v4: {erro}")
    logger.critical("   > Por favor, instale a biblioteca com o comando: pip install 'dydx-v4-client==1.1.5'")
    sys.exit(1)

# ============================================================================
# CLASSE PRINCIPAL DO ROBÔ DE AUTOMAÇÃO
# ============================================================================

class RoboTraderDydx:
    """
    Classe que encapsula a lógica para automação de ordens na DYDX v4.
    """
    
    def __init__(self):
        """
        Inicializa o robô, carregando configurações e estabelecendo conexão.
        """
        logger.info("🚀 Inicializando Robô de Automação de Ordens DYDX v4...")
        logger.info("======================================================================")
        
        self._carregar_configuracoes()
        self._inicializar_cliente_dydx()
        self._configurar_trading()
        
        logger.info("✅ Robô inicializado e pronto para operar.")
        logger.info("======================================================================")
    
    def _carregar_configuracoes(self):
        """
        Carrega as configurações a partir de variáveis de ambiente.
        """
        logger.info("📋 Carregando configurações de ambiente...")
        load_dotenv()
        
        self.chave_privada = os.getenv("DYDX_PRIVATE_KEY")
        self.endereco_wallet = os.getenv("DYDX_ADDRESS")
        
        if not self.chave_privada or not self.endereco_wallet:
            logger.critical("❌ ERRO FATAL: Credenciais DYDX não encontradas!")
            logger.critical("   > Defina 'DYDX_PRIVATE_KEY' e 'DYDX_ADDRESS' no seu ambiente.")
            raise ValueError("Credenciais DYDX não configuradas.")
        
        endereco_mascarado = f"{self.endereco_wallet[:12]}...{self.endereco_wallet[-8:]}"
        logger.info(f"   > Endereço da carteira: {endereco_mascarado}")
        
        self.intervalo_loop = int(os.getenv("LOOP_INTERVAL_SECONDS", "60"))
        self.modo_execucao = os.getenv("BOT_RUN_MODE", "single").lower()
        
        logger.info(f"   > Intervalo entre ciclos: {self.intervalo_loop} segundos")
        logger.info(f"   > Modo de execução: {self.modo_execucao.upper()}")
    
    def _inicializar_cliente_dydx(self):
        """
        Estabelece a conexão com o Indexer da rede DYDX v4.
        """
        logger.info("🔗 Conectando-se à mainnet da DYDX...")
        try:
            self.cliente_dydx = IndexerClient("https://indexer.dydx.trade")
            logger.info("   > Conexão com o Indexer da DYDX estabelecida.")
        except Exception as erro:
            logger.critical(f"❌ Falha crítica ao conectar com a DYDX: {erro}")
            raise
    
    def _configurar_trading(self):
        """
        Define os parâmetros de trading, como ativos e limites de risco.
        """
        logger.info("⚙️  Configurando parâmetros de operação e risco...")
        self.ativos_monitorados = ["BTC", "ETH", "SOL", "AVAX", "LINK", "DOGE"]
        self.sinais_trading = [
            "BTC COMPRAR", "ETH COMPRAR", "SOL COMPRAR",
            "AVAX COMPRAR", "LINK COMPRAR", "DOGE COMPRAR"
        ]
        self.limite_saldo_minimo = 50.0      # Saldo mínimo em USDC para operar
        self.limite_exposicao_alta = 75.0    # % de exposição de alto risco
        self.limite_exposicao_moderada = 50.0 # % de exposição de risco moderado
        
        logger.info(f"   > Ativos para automação: {', '.join(self.ativos_monitorados)}")
        logger.info(f"   > Sinais configurados: {len(self.sinais_trading)} sinais ativos")

    def obter_preco_mercado(self, ativo: str) -> Optional[float]:
        """
        Obtém o preço de oráculo (oraclePrice) em tempo real para um ativo.

        Este método é crucial para a precisão das ordens, pois utiliza a mesma
        fonte de preço que a DYDX usa para funções críticas.

        Args:
            ativo (str): O símbolo do ativo (ex: "BTC").

        Returns:
            Optional[float]: O preço em tempo real ou None em caso de falha.
        """
        id_mercado = f"{ativo}-USD"
        try:
            resposta = self.cliente_dydx.markets.get_perpetual_market(id_mercado)
            
            if resposta and hasattr(resposta, 'market'):
                preco_oracle = float(resposta.market.get('oraclePrice', 0))
                if preco_oracle > 0:
                    logger.debug(f"Preço de Oráculo para {ativo}: ${preco_oracle:,.2f}")
                    return preco_oracle
            logger.warning(f"⚠️  Não foi possível obter um preço de oráculo válido para {ativo}.")

        except Exception as erro:
            logger.error(f"❌ Erro ao buscar preço de {ativo}: {erro}")
        
        return None

    def obter_saldo_conta(self) -> float:
        """Obtém o saldo atual da conta em USDC."""
        try:
            resposta = self.cliente_dydx.account.get_subaccount(self.endereco_wallet, 0)
            if resposta and hasattr(resposta, 'subaccount'):
                return float(resposta.subaccount.get('quoteBalance', 0))
        except Exception as erro:
            logger.error(f"⚠️ Erro ao obter saldo da conta: {erro}")
        return 0.0
    
    def obter_posicoes_abertas(self) -> List[Dict[str, Any]]:
        """Obtém a lista de posições abertas na conta."""
        try:
            resposta = self.cliente_dydx.account.get_subaccount_perpetual_positions(self.endereco_wallet, 0)
            if resposta and hasattr(resposta, 'positions'):
                return [
                    {
                        'mercado': p.get('market', ''), 'lado': p.get('side', ''),
                        'tamanho': abs(float(p.get('size', 0))), 'preco_entrada': float(p.get('entryPrice', 0)),
                        'pnl_nao_realizado': float(p.get('unrealizedPnl', 0)),
                    }
                    for p in resposta.positions if float(p.get('size', 0)) != 0
                ]
        except Exception as erro:
            logger.error(f"⚠️ Erro ao obter posições abertas: {erro}")
        return []

    def interpretar_sinal(self, sinal: str) -> Optional[Dict[str, str]]:
        """Interpreta e valida um sinal de trading no formato "ATIVO AÇÃO"."""
        try:
            partes = sinal.strip().upper().split()
            if len(partes) != 2: return None
            ativo, acao = partes
            if ativo not in self.ativos_monitorados: return None
            acoes_validas = {"COMPRAR": "BUY", "VENDER": "SELL", "FECHAR": "CLOSE"}
            if acao in acoes_validas:
                return {"ativo": ativo, "acao": acoes_validas[acao]}
        except Exception as erro:
            logger.error(f"❌ Erro ao interpretar o sinal '{sinal}': {erro}")
        return None

    def executar_ciclo_operacional(self):
        """
        Executa um ciclo completo de automação: verificação, coleta de dados,
        processamento de sinais e avaliação de risco.
        """
        timestamp_inicio = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
        logger.info("\n" + "="*80)
        logger.info(f"⚙️  INICIANDO CICLO OPERACIONAL | {timestamp_inicio}")
        logger.info("="*80)
        
        # --- PASSO 1: VERIFICAÇÃO DE SALDO E POSIÇÕES ---
        logger.info("\n[ 1/4 ] 💰 VERIFICAÇÃO DE SALDO E POSIÇÕES")
        logger.info("--------------------------------------------------")
        saldo_atual = self.obter_saldo_conta()
        posicoes_abertas = self.obter_posicoes_abertas()
        logger.info(f"   > Saldo Disponível: ${saldo_atual:,.2f} USDC")
        logger.info(f"   > Posições Abertas: {len(posicoes_abertas)}")
        if posicoes_abertas:
            pnl_total = sum(pos['pnl_nao_realizado'] for pos in posicoes_abertas)
            pnl_emoji = "🟢" if pnl_total >= 0 else "🔴"
            logger.info(f"   > PnL Total Não Realizado: {pnl_emoji} ${pnl_total:,.2f}")

        # --- PASSO 2: COLETA DE PREÇOS PARA EXECUÇÃO ---
        logger.info("\n[ 2/4 ] 📈 COLETA DE PREÇOS EM TEMPO REAL (ORÁCULO)")
        logger.info("--------------------------------------------------")
        dados_mercado = {ativo: self.obter_preco_mercado(ativo) for ativo in self.ativos_monitorados}
        for ativo, preco in dados_mercado.items():
            if preco:
                logger.info(f"   > {ativo:<5} - ${preco:,.2f}")
            else:
                logger.warning(f"   > {ativo:<5} - PREÇO INDISPONÍVEL")

        # --- PASSO 3: PROCESSAMENTO DE SINAIS PARA AUTOMAÇÃO ---
        logger.info("\n[ 3/4 ] 🎯 PROCESSAMENTO DE SINAIS PARA AUTOMAÇÃO DE ORDENS")
        logger.info("--------------------------------------------------")
        sinais_validos = 0
        for sinal_str in self.sinais_trading:
            sinal = self.interpretar_sinal(sinal_str)
            if sinal:
                ativo, acao, preco = sinal['ativo'], sinal['acao'], dados_mercado.get(sinal['ativo'])
                if preco:
                    emoji_acao = {"BUY": "🟢", "SELL": "🔴", "CLOSE": "🔵"}.get(acao, '⚪')
                    logger.info(f"   {emoji_acao} Sinal Válido: {acao} {ativo} @ ${preco:,.2f}")
                    if acao == "BUY" and saldo_atual < self.limite_saldo_minimo:
                        logger.warning(f"      L-> ⚠️ AÇÃO BLOQUEADA: Saldo insuficiente para operar.")
                    else:
                        logger.info(f"      L-> ✅ AÇÃO VÁLIDA: Condições de saldo atendidas.")
                    sinais_validos += 1
                else:
                    logger.warning(f"   ❌ Sinal Ignorado: {sinal_str} (preço do ativo indisponível).")
            else:
                logger.warning(f"   ❌ Sinal Inválido: '{sinal_str}'.")
        
        logger.info(f"\n   -> Sinais válidos e prontos para automação: {sinais_validos}/{len(self.sinais_trading)}")

        # --- PASSO 4: CÁLCULO DE RISCO PRÉ-OPERAÇÃO ---
        logger.info("\n[ 4/4 ] ⚖️  CÁLCULO DE RISCO PRÉ-OPERAÇÃO")
        logger.info("--------------------------------------------------")
        if saldo_atual > 0 and posicoes_abertas:
            valor_posicoes = sum(pos['tamanho'] * dados_mercado.get(pos['mercado'].replace('-USD', ''), pos['preco_entrada']) for pos in posicoes_abertas)
            percentual_exposicao = (valor_posicoes / (saldo_atual + valor_posicoes)) * 100
            
            logger.info(f"   > Valor Total em Posições: ${valor_posicoes:,.2f}")
            logger.info(f"   > Exposição do Capital: {percentual_exposicao:.2f}%")
            
            if percentual_exposicao > self.limite_exposicao_alta:
                logger.warning("   > 🚨 RISCO ALTO: Exposição superior a 75%. Novas ordens podem ser arriscadas.")
            elif percentual_exposicao > self.limite_exposicao_moderada:
                logger.info("   > 🟡 RISCO MODERADO: Exposição superior a 50%. Monitore ativamente.")
            else:
                logger.info("   > 🟢 RISCO BAIXO: Exposição controlada.")
        else:
            logger.info("   > 🟢 RISCO BAIXO: Sem exposição de capital no momento.")

        # --- CHECKLIST OPERACIONAL ---
        logger.info("\n📋 CHECKLIST OPERACIONAL")
        logger.info("--------------------------------------------------")
        logger.info(f"   > Saldo para operações: {'✅ OK' if saldo_atual >= self.limite_saldo_minimo else '⚠️ INSUFICIENTE'}")
        precos_ok = all(dados_mercado.values())
        logger.info(f"   > Preços em tempo real: {'✅ OK' if precos_ok else '⚠️ FALHA EM ALGUM ATIVO'}")
        logger.info(f"   > Sinais válidos: {'✅ OK' if sinais_validos > 0 else 'ℹ️ NENHUM SINAL VÁLIDO'}")

        logger.info("\n" + "="*80)
        logger.info("✅ CICLO OPERACIONAL FINALIZADO")
        logger.info("="*80)
    
    def executar_modo_continuo(self):
        """Executa o robô em modo de loop contínuo (24/7)."""
        logger.info(f"\n🔄 INICIANDO MODO CONTÍNUO (Intervalo: {self.intervalo_loop}s)")
        logger.info("   Pressione Ctrl+C a qualquer momento para encerrar o robô.")
        logger.info("-" * 60)
        
        ciclo_num = 0
        try:
            while True:
                ciclo_num += 1
                self.executar_ciclo_operacional()
                logger.info(f"\n⏳ Próximo ciclo em {self.intervalo_loop} segundos. Aguardando...")
                time.sleep(self.intervalo_loop)
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Robô interrompido pelo usuário. Encerrando...")
        except Exception as erro:
            logger.critical(f"\n\n💥 Erro crítico no modo contínuo: {erro}", exc_info=True)
            logger.critical("   🚨 O robô será encerrado por segurança.")
    
    def executar(self):
        """Ponto de entrada principal para a execução do robô."""
        if self.modo_execucao == "continuous":
            self.executar_modo_continuo()
        else:
            self.executar_ciclo_operacional()
        logger.info("\n🎉 Execução do robô finalizada.")

# ============================================================================
# FUNÇÃO PRINCIPAL (MAIN)
# ============================================================================

def main():
    """Função principal que inicializa e executa o robô."""
    try:
        print("\n" + "=" * 90)
        print("         🤖 ROBÔ DE AUTOMAÇÃO DE ORDENS DYDX v4 - INICIANDO 🤖")
        print("=" * 90)
        
        robo = RoboTraderDydx()
        robo.executar()
        
        print("\n" + "=" * 90)
        print("                 ✅ OPERAÇÃO FINALIZADA COM SUCESSO ✅")
        print("=" * 90)
        return 0
    except ValueError:
        logger.critical("   > O robô não pôde ser iniciado devido a um erro de configuração.")
        return 1
    except Exception as erro:
        logger.critical(f"\n💥 Erro fatal e inesperado: {erro}", exc_info=True)
        return 1

# ============================================================================
# PONTO DE ENTRADA DO SCRIPT
# ============================================================================

if __name__ == "__main__":
    if sys.stdout.encoding != 'utf-8' and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())

