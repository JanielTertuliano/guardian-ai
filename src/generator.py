import pandas as pd
import random
import os
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('pt_BR')
random.seed(42)

def generate_guardian_dataset(num_transactions=1000):
    os.makedirs("data", exist_ok=True)
    num_customers = int(num_transactions * 0.3)
    countries = ['BR', 'US', 'GB', 'KY', 'CH', 'PA', 'SG', 'DE']
    
    customers_data = []
    for _ in range(num_customers):
        customer_id = f"CLI-{fake.unique.random_int(min=10000, max=99999)}"
        tipo_pessoa = random.choice(['PF', 'PJ'])
        customers_data.append({
            "id_cliente": customer_id,
            "nome": fake.name() if tipo_pessoa == 'PF' else fake.company(),
            "tipo_pessoa": tipo_pessoa,
            "faturamento_anual_estrangeiro_usd": round(random.uniform(50000, 15000000), 2),
            "score_credito_interno": random.randint(300, 1000),
            "status_PEP": 1 if random.random() < 0.05 else 0,
            "pais_origem_principal": random.choice(['BR', 'US', 'GB', 'DE'])
        })
    df_customers = pd.DataFrame(customers_data)

    transactions_data = []
    base_time = datetime(2026, 1, 1)
    for i in range(num_transactions):
        tx_id = f"TX-{100000 + i}"
        customer = df_customers.sample(1).iloc[0]
        pais_destino = random.choice(countries)
        if customer['status_PEP'] == 1 or pais_destino in ['KY', 'PA']:
            valor_usd = round(random.uniform(500000, 4000000), 2)
            natureza = random.choice(['Aporte de Capital', 'Serviços de Consultoria'])
        else:
            valor_usd = round(random.uniform(1000, 250000), 2)
            natureza = random.choice(['Importação de Software', 'Aporte de Capital', 'Manutenção de Residentes', 'Turismo', 'Serviços de Consultoria'])
            
        tx_time = base_time + timedelta(days=random.randint(0, 150), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        transactions_data.append({
            "id_transacao": tx_id,
            "id_cliente": customer['id_cliente'],
            "moeda_origem": "BRL",
            "moeda_destino": random.choice(['USD', 'EUR', 'GBP', 'BRL']) if pais_destino != 'BR' else 'BRL',
            "valor_moeda_estrangeira_usd": valor_usd,
            "valor_brl": round(valor_usd * 5.2, 2),
            "pais_destino": pais_destino,
            "natureza_operacao": natureza,
            "data_hora": tx_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    df_transactions = pd.DataFrame(transactions_data)

    logs_data = []
    analistas = ['Ana Silva', 'Carlos Souza', 'Mariana Costa']
    for _, tx in df_transactions.iterrows():
        customer = df_customers[df_customers['id_cliente'] == tx['id_cliente']].iloc[0]
        is_suspicious = (tx['pais_destino'] in ['KY', 'PA'] or customer['status_PEP'] == 1 or tx['valor_moeda_estrangeira_usd'] > 1000000)
        if is_suspicious or random.random() < 0.02:
            status = random.choice(['Aprovado', 'Bloqueado', 'Sob Análise'])
            justificativas = {
                'Aprovado': "Documentação de suporte de origem de fundos validada conforme contrato.",
                'Bloqueado': "Transação destinada a paraíso fiscal sem justificativa econômica clara.",
                'Sob Análise': "Aguardando envio de invoice detalhada."
            }
            logs_data.append({
                "id_alerta": f"ALERT-{fake.unique.random_int(min=10000, max=99999)}",
                "id_transacao": tx['id_transacao'],
                "analista_responsavel": random.choice(analistas),
                "status_revisao": status,
                "justificativa_anterior": justificativas[status]
            })
    df_logs = pd.DataFrame(logs_data)
    
    df_customers.to_csv("data/customers.csv", index=False)
    df_transactions.to_csv("data/transactions.csv", index=False)
    df_logs.to_csv("data/compliance_logs.csv", index=False)
    print("Dataset estruturado gerado com sucesso na pasta data/!")

if __name__ == "__main__":
    generate_guardian_dataset()
