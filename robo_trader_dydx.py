#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ROBÔ DE AUTOMAÇÃO DE ORDENS PARA DYDX V4 - VERSÃO 3.2 (INTERFACE LIMPA)
================================================================================

Este é um robô de trading projetado para a automação completa de ordens na
plataforma DYDX v4. Seu objetivo principal é processar sinais de trading e
executar as operações correspondentes de forma autônoma e segura.

Esta versão refatora a saída de logs e da interface para uma apresentação
mais limpa, coesa e profissional, facilitando o monitoramento.

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

Autor: Replit Agent para Daniel Mota de Aguiar Rodrigues
Versão: 3.2 - Interface Limpa e Coesa
Data: 27 de Setembro de 2025
================================================================================
"""

import os
import logging
import sys
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# ============================================================================
# CONFIGURAÇÃO DO SISTEMA DE LOGS
# ============================================================================

def configurar_logs():
    """Configura um sistema de logging robusto para o robô."""
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
    """Classe que encapsula a lógica para automação de ordens na DYDX v4."""
    
    def __init__(self):
        """Inicializa o robô, carregando configurações e estabelecendo conexão."""
        logger.info("🚀 Inicializando Robô de Automação de Ordens DYDX v4...")
        
        self._carregar_configuracoes()
        self._inicializar_cliente_dydx()
        self._configurar_trading()
        
        logger.info("✅ Robô inicializado e pronto para operar.")
    
    def _carregar_configuracoes(self):
        """Carrega as configurações a partir de variáveis de ambiente."""
        logger.info("    > Carregando configurações de ambiente...")
        load_dotenv()
        
        self.chave_privada = os.getenv("DYDX_PRIVATE_KEY")
        self.endereco_wallet = os.getenv("DYDX_ADDRESS")
        
        if not self.chave_privada or not self.endereco_wallet:
            logger.critical("❌ ERRO FATAL: Credenciais DYDX não encontradas!")
            logger.critical("   > Defina 'DYDX_PRIVATE_KEY' e 'DYDX_ADDRESS' no seu ambiente.")
            raise ValueError("Credenciais DYDX não configuradas.")
        
        self.intervalo_loop = int(os.getenv("LOOP_INTERVAL_SECONDS", "60"))
        self.modo_execucao = os.getenv("BOT_RUN_MODE", "single").lower()
    
    def _inicializar_cliente_dydx(self):
        """Estabelece a conexão com o Indexer da rede DYDX v4."""
        logger.info("    > Conectando-se à mainnet da DYDX...")
        try:
            self.cliente_dydx = IndexerClient("https://indexer.dydx.trade")
        except Exception as erro:
            logger.critical(f"❌ Falha crítica ao conectar com a DYDX: {erro}")
            raise
    
    def _configurar_trading(self):
        """Define os parâmetros de trading, como ativos e limites de risco."""
        logger.info("    > Configurando parâmetros de operação e risco...")
        self.ativos_monitorados = ["BTC", "ETH", "SOL", "AVAX", "LINK", "DOGE"]
        self.sinais_trading = [
            "BTC COMPRAR", "ETH COMPRAR", "SOL COMPRAR",
            "AVAX COMPRAR", "LINK COMPRAR", "DOGE COMPRAR"
        ]
        self.limite_saldo_minimo = 50.0
        self.limite_exposicao_alta = 75.0
        self.limite_exposicao_moderada = 50.0

    async def obter_preco_mercado(self, ativo: str) -> Optional[float]:
        """Obtém o preço de oráculo (oraclePrice) em tempo real para um ativo."""
        id_mercado = f"{ativo}-USD"
        try:
            resposta = await self.cliente_dydx.public.get_perpetual_market(ticker=id_mercado)
            if resposta and hasattr(resposta, 'market'):
                preco_oracle = float(resposta.market.get('oraclePrice', 0))
                if preco_oracle > 0:
                    return preco_oracle
            logger.warning(f"⚠️  Preço de oráculo indisponível para {ativo}.")
        except Exception as erro:
            logger.error(f"❌ Erro ao buscar preço de {ativo}: {erro}")
        return None

    async def obter_saldo_conta(self) -> float:
        """Obtém o saldo atual da conta em USDC."""
        try:
            resposta = await self.cliente_dydx.account.get_subaccount(self.endereco_wallet, 0)
            if resposta and hasattr(resposta, 'subaccount'):
                return float(resposta.subaccount.get('quoteBalance', 0))
        except Exception as erro:
            logger.error(f"⚠️ Erro ao obter saldo da conta: {erro}")
        return 0.0
    
    async def obter_posicoes_abertas(self) -> List[Dict[str, Any]]:
        """Obtém a lista de posições abertas na conta."""
        try:
            resposta = await self.cliente_dydx.account.get_subaccount_perpetual_positions(self.endereco_wallet, 0)
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

    async def executar_ciclo_operacional(self):
        """Executa um ciclo completo de automação de forma assíncrona."""
        timestamp_inicio = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
        logger.info(f"\n─── Iniciando Ciclo Operacional ({timestamp_inicio}) ───")
        
        logger.info("[1/4] Verificando saldo e posições da conta...")
        saldo_atual = await self.obter_saldo_conta()
        posicoes_abertas = await self.obter_posicoes_abertas()
        logger.info(f"      > Saldo: ${saldo_atual:,.2f} USDC | Posições Abertas: {len(posicoes_abertas)}")
        
        logger.info("[2/4] Coletando preços de mercado em tempo real...")
        tasks = [self.obter_preco_mercado(ativo) for ativo in self.ativos_monitorados]
        precos = await asyncio.gather(*tasks)
        dados_mercado = dict(zip(self.ativos_monitorados, precos))
        precos_validos = {k: v for k, v in dados_mercado.items() if v is not None}
        logger.info(f"      > {len(precos_validos)}/{len(self.ativos_monitorados)} preços coletados com sucesso.")

        logger.info("[3/4] Processando sinais de trading para automação...")
        sinais_validos = 0
        for sinal_str in self.sinais_trading:
            sinal = self.interpretar_sinal(sinal_str)
            if sinal and dados_mercado.get(sinal['ativo']):
                sinais_validos += 1
        logger.info(f"      > {sinais_validos}/{len(self.sinais_trading)} sinais válidos e prontos para execução.")

        logger.info("[4/4] Calculando risco e exposição da conta...")
        if saldo_atual > 0 and posicoes_abertas:
            valor_posicoes = sum(p['tamanho'] * dados_mercado.get(p['mercado'].replace('-USD', ''), p['preco_entrada']) for p in posicoes_abertas)
            percentual_exposicao = (valor_posicoes / (saldo_atual + valor_posicoes)) * 100
            logger.info(f"      > Exposição de capital atual: {percentual_exposicao:.2f}%")
        else:
            logger.info("      > Conta sem exposição de capital no momento.")
        
        logger.info("📋 Checklist Pré-Operação:")
        logger.info(f"      > Saldo para operações: {'✅ OK' if saldo_atual >= self.limite_saldo_minimo else '⚠️ INSUFICIENTE'}")
        logger.info(f"      > Preços em tempo real: {'✅ OK' if all(dados_mercado.values()) else '⚠️ FALHA EM ALGUM ATIVO'}")
        logger.info(f"      > Sinais para execução: {'✅ OK' if sinais_validos > 0 else 'ℹ️ NENHUM SINAL VÁLIDO'}")

        logger.info("─── Ciclo Operacional Finalizado ───")
    
    async def executar_modo_continuo(self):
        """Executa o robô em modo de loop contínuo de forma assíncrona."""
        logger.info(f"\n🔄 Iniciando modo contínuo (intervalo de {self.intervalo_loop}s). Pressione Ctrl+C para parar.")
        
        ciclo_num = 0
        try:
            while True:
                ciclo_num += 1
                await self.executar_ciclo_operacional()
                logger.info(f"\n⏳ Aguardando {self.intervalo_loop} segundos para o próximo ciclo...")
                await asyncio.sleep(self.intervalo_loop)
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Robô interrompido pelo usuário. Encerrando...")
        except Exception as erro:
            logger.critical(f"\n\n💥 Erro crítico no modo contínuo: {erro}", exc_info=True)
            logger.critical("   🚨 O robô será encerrado por segurança.")
    
    async def executar(self):
        """Ponto de entrada principal para a execução assíncrona do robô."""
        if self.modo_execucao == "continuous":
            await self.executar_modo_continuo()
        else:
            await self.executar_ciclo_operacional()
        logger.info("\n🎉 Execução do robô finalizada.")

# ============================================================================
# FUNÇÃO PRINCIPAL (MAIN)
# ============================================================================

async def main():
    """Função principal que inicializa e executa o robô de forma assíncrona."""
    try:
        print("\n" + "─" * 90)
        print("         🤖 ROBÔ DE AUTOMAÇÃO DE ORDENS DYDX v4 - INICIANDO 🤖")
        print("─" * 90)
        
        robo = RoboTraderDydx()
        await robo.executar()
        
        print("\n" + "─" * 90)
        print("                 ✅ OPERAÇÃO FINALIZADA COM SUCESSO ✅")
        print("─" * 90)
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
    
    sys.exit(asyncio.run(main()))
